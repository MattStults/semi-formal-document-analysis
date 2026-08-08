#!/usr/bin/env python3
"""Draw the "introduces a named category" eval set — deterministically, and
BEFORE any outcome is looked at.

⭐ WHY THIS FILE EXISTS. `RESULT_bad_example_6.md` measured a change to bad
worked example #6 ("imports a name without its content") on a clause set drawn
blind, and the control arm scored 0.000 — the set did not exhibit the failure,
so there was nothing to improve and the delta was unreadable. A fix for a
failure can only be measured where the failure can OCCUR. Bad example #6 is
about a concept that names a category and glosses it with its own name, so the
eval set has to hold clauses that INTRODUCE NAMED CATEGORIES.

⛔ THE TRAP THIS AVOIDS. "Pick the clauses where the failure shows up" is
fitting if the picking happens after the run. So the rule is mechanical, it is
written here before any call is made, and the drawn ids are frozen in a
provenance sidecar with the exclusion sets that produced them. A later reader
can re-run this file and get the same six ids.

The rule, in one sentence: a clause is eligible if it is long enough to yield
concepts at all, has never been sent to the model or named in a prompt, and
either **bolds a term** (the document's own way of introducing a defined name)
or **enumerates instances of a category** ("such as", "including", "e.g."
followed by a list).

Usage:
    python3 select_category_clauses.py --salt eval-categories-v1 --n 6 \
        --out heldout_categories.txt
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(HERE)
CORPUS = os.path.join(P1, "..", "..", "..", "semi-formal-experiment",
                      "modelspec_clauses.json")

#: ⭐ THE TWO SIGNALS. Both are the DOCUMENT's own way of introducing a name.
#: S1 — a bolded term. "**Conversation**: valid input to the model is a
#:      **conversation** ..." is the spec defining a category by naming it.
#: S2 — an enumeration of instances. "critical and high severity harms, such as
#:      acts of violence (...), terrorism, child abuse (...)" is the clause bad
#:      example #6 is literally drawn from: a category whose content is the
#:      list, which a lazy translation collapses into one opaque symbol.
#: The comma requirement is what makes S2 mean "a list" rather than a single
#: parenthetical aside — one "e.g." with no list introduces no category.
_BOLD = re.compile(r"\*\*[^*\n]{2,40}\*\*")
_ENUM = re.compile(r"\b(such as|includ(?:ing|es)|e\.g\.|for example)\b",
                   re.IGNORECASE)

#: A clause shorter than this yields one or two concepts at most, and a rate
#: over a denominator of two is the "metric read 0.0000 because it measured
#: NOTHING" failure in `DEBUGGING_TIPS.md` §2.
MIN_CHARS = 200

#: ⛔ EVERY id that carries a worked answer or a previous outcome.
PROMPT_GLOBS = ["prompt/*.md", "eval_arms/prompt_*/*.md"]
SENT_GLOBS = ["runs/*/*.raw.txt", "runs/*/*.transcript.json",
              "eval_arms/*_raw/*/*/*.raw.txt"]
HELDOUT_FILES = ["heldout.txt", "heldout_v2.txt", "heldout_v3.txt",
                 "diagnosis_set.txt"]
_ID = re.compile(r"m[0-9]{4}")


def exclusions():
    """(set, provenance dict). Each source is recorded separately so a reader
    can see which fence caught which id rather than one anonymous blob."""
    out = {}
    ids = set()
    for label, globs in (("named_in_prompt", PROMPT_GLOBS),):
        found = set()
        for g in globs:
            for path in glob.glob(os.path.join(P1, g)):
                with open(path, encoding="utf-8") as fh:
                    found |= set(_ID.findall(fh.read()))
        out[label] = sorted(found)
        ids |= found
    found = set()
    for g in SENT_GLOBS:
        for path in glob.glob(os.path.join(P1, g)):
            base = os.path.basename(path)
            found |= set(_ID.findall(base))
    out["ever_sent_to_the_model"] = sorted(found)
    ids |= found
    found = set()
    for name in HELDOUT_FILES:
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                found |= set(_ID.findall(fh.read()))
    out["previous_eval_sets"] = sorted(found)
    ids |= found
    return ids, out


def signals(text):
    """Which category-introduction signals this clause carries."""
    hits = []
    if _BOLD.search(text):
        hits.append("bold_term")
    m = _ENUM.search(text)
    if m and text[m.end():].count(",") >= 2:
        hits.append("enumerated_instances")
    return hits


def eligible(clauses, excluded):
    out = []
    for c in clauses:
        if c["id"] in excluded:
            continue
        if c.get("kind") not in ("definitional", "conditional"):
            continue
        text = c.get("quote") or ""
        if len(text) < MIN_CHARS:
            continue
        sig = signals(text)
        if not sig:
            continue
        out.append((c["id"], c.get("kind"), sig))
    return out


def rank(cid, salt):
    return hashlib.sha256(f"{salt}:{cid}".encode()).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salt", required=True)
    p.add_argument("--n", type=int, default=6)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    with open(os.path.abspath(CORPUS), encoding="utf-8") as fh:
        clauses = json.load(fh)["clauses"]
    excl, excl_prov = exclusions()
    pool = eligible(clauses, excl)
    if len(pool) < a.n:
        print(f"⛔ pool holds {len(pool)} clauses, fewer than the {a.n} asked "
              f"for. Widening the rule after seeing this is fitting; say so "
              f"in the pre-registration if you do it.", file=sys.stderr)
        return 2
    picked = sorted(pool, key=lambda t: rank(t[0], a.salt))[:a.n]

    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(cid for cid, _, _ in picked) + "\n")
    with open(out + ".provenance.json", "w", encoding="utf-8") as fh:
        json.dump({
            "generated_by": "eval_arms/select_category_clauses.py",
            "salt": a.salt,
            "rule": "kind in {definitional, conditional}; len(quote) >= "
                    f"{MIN_CHARS}; and at least one of: a bolded term, or an "
                    "enumeration marker followed by a list of >= 2 commas",
            "why": "bad worked example #6 is about a concept that names a "
                   "category and glosses it with its own name. A clause that "
                   "introduces no named category cannot exhibit that failure, "
                   "and the first A/B measured the change on a set that did "
                   "not — the control scored 0.000.",
            "ids": [cid for cid, _, _ in picked],
            "picked": [{"id": c, "kind": k, "signals": s} for c, k, s in picked],
            "pool_size": len(pool),
            "corpus_size": len(clauses),
            "excluded_n": len(excl),
            "excluded": excl_prov,
        }, fh, indent=1)
    print(f"✓ {os.path.relpath(out, HERE)} — {a.n} of {len(pool)} eligible "
          f"({len(excl)} ids excluded)")
    for cid, kind, sig in picked:
        print(f"    {cid}  {kind:12s} {','.join(sig)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
