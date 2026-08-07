"""Mechanical validator for density rewrites of a markdown design document.

The sandwich rule (REPRODUCIBILITY.md): every LLM judgment seat runs under a versioned
brief between a deterministic producer and a mechanical validator. This is the validator
for `briefs/density_editor.md` — a seat that rewrites dense prose for readability and is
FORBIDDEN from changing content.

What "does not change content" means here is deliberately narrow and mechanical. A rewrite
PASSES only if every load-bearing token survives:

  * numbers      — every numeric literal (0.0316, +0.591, 593, 68-69%) must survive.
                   This is the highest-risk class: this repo's history is numbers that were
                   subtly wrong, and 0.0316 vs 0.035 inverts a published verdict.
  * code refs    — every `backticked` span (file paths, identifiers, line refs).
  * quotations   — every *"quoted string"*; these are verbatim citations of other files.
  * markers      — the count of ⛔ ⚠️ ✅ ⭐ must not fall silently.

The rewrite must also achieve its OBJECTIVE: bold spans cut to <= MAX_BOLD_RATIO of the
original, and bold-per-line must not rise. Length may grow up to 5% (a lead sentence per
section is wanted); beyond that it is not an edit. Everything else is free.

Usage:
    python3 check_rewrite.py before.md after.md
    python3 check_rewrite.py --self-test
"""

import re
import sys
import collections

NUM = re.compile(r'[+\-−]?\d+(?:[.,]\d+)*%?')
CODE = re.compile(r'`([^`\n]+)`')
QUOTE = re.compile(r'\*"([^"]{4,})"\*')
MARKERS = ("⛔", "⚠️", "✅", "⭐")

#: A rewrite must cut bold spans to at most this fraction of the original.
#: The document averaged one bold span per two lines, which means bold marked nothing.
MAX_BOLD_RATIO = 0.6


def _nums(s):
    # normalise unicode minus and thousands separators so formatting is free
    return collections.Counter(
        n.replace("−", "-").replace(",", "") for n in NUM.findall(s))


def _codes(s):
    return collections.Counter(CODE.findall(s))


def _quotes(s):
    # whitespace inside a quote is free (rewrapping); the words are not
    return collections.Counter(" ".join(q.split()) for q in QUOTE.findall(s))


def check(before, after):
    """Return (ok, list_of_failures)."""
    fails = []

    for label, fn in (("number", _nums), ("code ref", _codes), ("quotation", _quotes)):
        b, a = fn(before), fn(after)
        missing = b - a
        if missing:
            for tok, n in sorted(missing.items()):
                fails.append(f"{label} dropped ({n}x): {tok[:90]}")

    for m in MARKERS:
        b, a = before.count(m), after.count(m)
        if a < b:
            fails.append(f"marker {m} count fell {b} -> {a}")

    # THE OBJECTIVE. The first run of this seat validated only content-preservation
    # and byte-compression, so every editor compressed by cutting plain prose while
    # keeping the bold — bold-per-line ROSE in all 8 sections (worst: 0.60 -> 1.31).
    # The seat optimised what was measured. Measure the actual goal instead.
    bb, ab = before.count("**") // 2, after.count("**") // 2
    bl = len([l for l in before.split("\n") if l.strip()])
    al = len([l for l in after.split("\n") if l.strip()])
    if bb and ab > bb * MAX_BOLD_RATIO:
        fails.append(f"bold not cut enough: {bb} -> {ab} spans "
                     f"(need <= {int(bb * MAX_BOLD_RATIO)})")
    b_dens, a_dens = bb / max(bl, 1), ab / max(al, 1)
    if a_dens > b_dens:
        fails.append(f"bold DENSITY rose: {b_dens:.2f} -> {a_dens:.2f} per line")

    # Length may grow slightly — a one-line lead sentence per section is wanted —
    # but a rewrite that balloons is not an edit.
    if len(after) > len(before) * 1.05:
        fails.append(f"grew >5%: {len(before)} -> {len(after)} chars")

    return (not fails), fails


def _self_test():
    """RED first: the validator must FAIL a lossy rewrite for the NAMED reason."""
    before = (
        'The **floor** is `0.0316-0.037` per `breadth_filter.py:190`, and the **contrast**\n'
        '+0.0317 **straddles** it. ⛔ See *"the decisive control was never run"* for why.\n'
        'Filler sentence that exists only so a faithful rewrite can be shorter.\n')

    cases = [
        ("drops a number",
         'The floor is `0.0316-0.037` per `breadth_filter.py:190`. ⛔ '
         '*"the decisive control was never run"*.\n',
         "number dropped"),
        # keeps every number and quote; only the backticks are gone, so this
        # isolates the code-ref check rather than tripping the number check
        ("drops a code ref",
         'The floor is 0.0316-0.037 per breadth_filter.py:190; +0.0317 straddles. ⛔ '
         '*"the decisive control was never run"*.\n',
         "code ref dropped"),
        ("drops a quotation",
         'Floor `0.0316-0.037` per `breadth_filter.py:190`; +0.0317 straddles. ⛔\n',
         "quotation dropped"),
        ("drops a marker",
         'Floor `0.0316-0.037` per `breadth_filter.py:190`; +0.0317 straddles it. '
         '*"the decisive control was never run"*.\n',
         "marker"),
        # keeps every bold span, deletes only plain prose: the exact failure the
        # first run of this seat produced in all 8 sections
        ("keeps the bold, cuts the prose",
         'The **floor** is `0.0316-0.037` per `breadth_filter.py:190`, and the **contrast**\n'
         '+0.0317 **straddles** it. ⛔ *"the decisive control was never run"*.\n',
         "bold"),
        ("balloons instead of editing",
         'The **floor** is `0.0316-0.037` per `breadth_filter.py:190`; +0.0317 straddles\n'
         'it. ⛔ *"the decisive control was never run"* explains why this matters, and\n'
         'here is a great deal of additional padding added by an editor who expanded\n'
         'the section instead of tightening it, which is not the job at all, plus more.\n',
         "grew >5%"),
    ]

    print("RED — each lossy rewrite must fail for its named reason:")
    red_ok = True
    for name, after, expect in cases:
        ok, fails = check(before, after)
        hit = (not ok) and any(expect in f for f in fails)
        print(f"  [{'PASS' if hit else 'FAIL'}] {name:22s} -> {fails[0] if fails else 'ACCEPTED (bug!)'}")
        red_ok &= hit

    good = ('Floor `0.0316-0.037` (`breadth_filter.py:190`); +0.0317 **straddles** it. ⛔\n'
            '*"the decisive control was never run"*.\n')
    ok, fails = check(before, good)
    print(f"\nGREEN — a faithful, shorter rewrite must pass:\n  [{'PASS' if ok else 'FAIL'}] {fails}")
    return 0 if (red_ok and ok) else 1


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    if len(argv) != 3:
        print(__doc__)
        return 2
    before, after = (open(p, encoding="utf-8").read() for p in argv[1:3])
    ok, fails = check(before, after)
    if ok:
        print(f"PASS — content preserved, {len(before)} -> {len(after)} chars "
              f"({100 * (1 - len(after) / len(before)):.0f}% shorter)")
        return 0
    print(f"FAIL — {len(fails)} content change(s):")
    for f in fails:
        print("  " + f)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
