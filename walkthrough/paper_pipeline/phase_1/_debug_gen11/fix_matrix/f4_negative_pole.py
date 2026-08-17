#!/usr/bin/env python3
"""F4 — a negative pole for `status`. PROPOSAL ONLY, plus a live blast radius.

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/fix_matrix/f4_negative_pole.py

⛔ THIS FILE APPLIES NOTHING. `schema.py` is guard-watched. What it does is
(a) state the minimal change as text and (b) ENUMERATE, by grepping the tree
rather than by memory, every consumer that would have to change with it — the
part of a schema proposal that is actually hard, and the part whose absence
makes a proposal unreviewable.

────────────────────────────────────────────────────────────────────────────
THE PROBLEM, MEASURED
────────────────────────────────────────────────────────────────────────────
`schema.py:50  STATUSES = ("forbid", "permit", "oblige", "prefer")` has no
negative pole. For a clause that says "avoid X", "minimise X", or marks X as a
BAD example, there is no correct single-act encoding, and the translator
reliably picks the one that INVERTS the meaning: `prefer` on the act the
document says to avoid.

  * 6 of 7 CONTRADICTION verdicts in `flip_classify/verdicts.json` are this.
  * 5 of 26 reference-set edits are `inverted-modality`; all 5 are this shape.
  * `checks.polarity_findings` is deliberately NOT disclosable to the repair
    loop for exactly this reason: told "these two fields disagree", a model
    with no negative pole can only delete the entry or rewrite the read-back,
    and the second is strictly worse than the defect.

────────────────────────────────────────────────────────────────────────────
THE MINIMAL CHANGE — and the alternative rejected BY NAME
────────────────────────────────────────────────────────────────────────────
PROPOSED:  add `"disprefer"` to `STATUSES` and to `Assertion.status`'s Literal.
           Semantics: the mirror of `prefer`. `asserts(C, disprefer, A) :- B`
           compiles to a soft constraint against A under B, at the same weight
           `prefer` gives for it.

REJECTED — A SIGN FIELD ON `prefer` (`prefer` + `polarity: -1`).
  Rejected on three grounds, recorded here so it is not re-proposed:
  1. It reintroduces the same two-field redundancy the polarity check lives
     on, in a place where the two fields are NOT independently authored — the
     model would write status and sign in one breath — so it buys the
     ambiguity without buying the evidence.
  2. Every consumer below must branch on the sign anyway, so the blast radius
     is identical; nothing is saved.
  3. `render_lp` would emit `prefer` with a sign the ASP program has to
     re-interpret, meaning the compiled artifact no longer reads as the norm.
     A status name is read by humans in the .lp file; a sign is not.

REJECTED — A COMPARATIVE TWO-ACT FORM (`prefer A over B`).
  It is the right long-run shape for GOOD/BAD worked examples and it does NOT
  cover the plain case ("repeating the user's prompt is to be avoided" has no
  B), so it cannot replace the pole. It is an addition for later, not this.

────────────────────────────────────────────────────────────────────────────
⛔ THE ANTI-RULE THIS CHANGE MUST NOT BREAK
────────────────────────────────────────────────────────────────────────────
Shipping `disprefer` makes `checks.polarity_findings` promotable to a
disclosable stage-2 finding (a correct encoding finally exists, so the repair
loop has a legal move). ⛔ IT MUST NOT ALSO MAKE `read_back` DERIVED. The
check's whole evidentiary content is that `status` and `read_back` are written
INDEPENDENTLY. If a later change renders the read-back from the status "now
that the statuses are complete", the corpus ships silently-wrong statuses with
agreeing prose and nothing can ever see it again. MEASURED: golden items GS11
and GS12 flip both fields together and every polarity detector scores 0/2 on
them — that is a preview of the whole corpus under a rendered read-back.
Same rule, stated in full, at the top of `detectors.py`.

────────────────────────────────────────────────────────────────────────────
WHAT F4 IS WORTH — MEASURED, and it is NOT additive with F1
────────────────────────────────────────────────────────────────────────────
F4 PREVENTS the class F1 DETECTS. `detectors.f4_reach` is deliberately the
same extension as `f1_regex`, and the matrix shows both at 5/5 on P-REF and
2/4 on P-GOLD. So they are REDUNDANT ON DETECTION and complementary on
lifecycle: F4 removes the defect at write time, F1 catches what F4 fails to
prevent. Shipping F4 does not let F1 be deleted — F1 is F4's own regression
test — but it does mean F1's detection count should be expected to FALL, and a
falling F1 count after F4 is the success signal, not a regression.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.dirname(os.path.dirname(HERE))

#: Every consumer that must change, WITH the reason. The grep below proves each
#: one still exists at the stated place; a row that stops matching is a stale
#: proposal and the script says so rather than printing a tidy table.
CONSUMERS = [
    ("schema.py", r"^STATUSES = ",
     "the tuple itself — add the pole"),
    ("schema.py", r'status: Literal\["forbid"',
     "Assertion.status Literal must gain it or pydantic rejects every module"),
    ("schema.py", r"def render_lp",
     "emits asserts(C, STATUS, ACT) :- BODY. Must emit `disprefer` and the "
     "ASP layer must give it a soft constraint AGAINST the act, mirroring "
     "prefer's weight. ⚠️ Until the solver side exists, a disprefer compiles "
     "to nothing and the module is silently weaker than the document"),
    ("schema.py", r"class ReadBack|_readback_ok",
     "the read-back template/validator: a disprefer read-back must be "
     "PERMITTED to say 'dispreferred'. It must NOT be generated from the "
     "status — see the anti-rule above"),
    ("checks.py", r"_DISFAVOURED|polarity_mismatches",
     "the polarity check's own subject. After F4 it must fire on `prefer` + "
     "disfavouring read-back AND on `disprefer` + favouring read-back — the "
     "mirror case, which does not exist today and will the day the pole does"),
    ("checks.py", r"POLARITY_CHECK_ID|stage4-detector",
     "origin must change from `stage4-detector` to `schema` IN THE SAME "
     "COMMIT that adds the pole, which is what makes it disclosable to the "
     "repair loop. `checks.polarity_findings`' docstring states this "
     "precondition explicitly"),
    ("readback.py", r"prefer",
     "the read-back renderer's status vocabulary"),
    ("readback_r3.py", r"a\.status|asserts\(",
     "the r3 read-back renderer — the one the seats are shown"),
    ("seats.py", r"prefer",
     "⛔ FOUR SEAT BRIEFS. 4a restates the assertion, 4b judges the rendered "
     "sentence, 4c asks about licensing, 4d enumerates from the span. Each "
     "brief's status vocabulary is written out longhand and each must gain "
     "the pole, or a `disprefer` module reads to a seat as malformed. NOT "
     "EDITED HERE: seats.py is owned by the seat-fix agent"),
    ("translate_autofix.py", r"prefer",
     "autofix must not 'repair' a disprefer into a prefer"),
    ("concept_map_probe.py", r"prefer",
     "status vocabulary in the concept-map probe"),
    ("prompt/10_output_format.md", r"prefer",
     "⛔ GUARD-WATCHED. The output format is the SSOT the schema is tested "
     "against (`test_ssot_prompt_schema.py`); the pole must be documented "
     "here or the prompt and the schema disagree and that test fails"),
    ("prompt/00_task.md", r"prefer",
     "⛔ GUARD-WATCHED. The task description's status list"),
    ("prompt/20_worked_example.md", r"prefer|status",
     "⛔ GUARD-WATCHED. The worked example teaches the statuses by "
     "demonstration; a pole with no example is a pole the model will not use"),
    ("test_ssot_prompt_schema.py", r"schema|prompt",
     "asserts prompt and schema agree — fails the moment one side changes"),
    ("test_schema.py", r'status="',
     "status round-trip tests"),
    ("test_readback.py", r"prefer", "read-back rendering tests"),
    ("test_readback_r3.py", r"oblige|asserts\(", "r3 read-back rendering tests"),
    ("test_checks.py", r'polarity|status="', "polarity-check tests"),
    ("test_seats.py", r'polarity|status="', "seat-brief tests"),
]

#: Consumers named in the brief that the grep must CONFIRM or DENY, rather than
#: being quietly dropped. `link.py` and "behaviour matching" are in the brief's
#: list; if they do not exist in phase_1 that is itself the finding.
#: The brief names `link.py` and "behaviour matching" as consumers. NEITHER
#: EXISTS UNDER THOSE NAMES in phase_1 — measured below. The real files are
#: `resolve_runs/graph_v2/link_nodes.py` and
#: `resolve_runs/graph_v2/behavior_pilot/behavior_match.py`, and whether they
#: touch `status` at all is checked rather than assumed.
BRIEF_CLAIMS = ["resolve_runs/graph_v2/link_nodes.py",
                "resolve_runs/graph_v2/behavior_pilot/behavior_match.py"]


def main():
    print(__doc__)
    print("=" * 78)
    print("BLAST RADIUS — grepped now, not remembered")
    print("=" * 78)
    missing = []
    for path, pat, why in CONSUMERS:
        full = os.path.join(PHASE1, path)
        if not os.path.exists(full):
            print(f"\n⚠️ ABSENT  {path}  — proposal row is stale")
            missing.append(path)
            continue
        rx = re.compile(pat)
        hits = [i for i, line in enumerate(
            open(full, encoding="utf-8", errors="replace"), 1)
            if rx.search(line)]
        mark = "  " if hits else "⚠️"
        print(f"\n{mark} {path}   ({len(hits)} matching lines"
              + (f", first at :{hits[0]}" if hits else ", NONE — stale row")
              + ")")
        for chunk in _wrap(why, 72):
            print("     " + chunk)
        if not hits:
            missing.append(path)

    print("\n" + "=" * 78)
    print("CLAIMS IN THE BRIEF, CHECKED")
    print("=" * 78)
    for name in BRIEF_CLAIMS:
        full = os.path.join(PHASE1, name)
        if not os.path.exists(full):
            print(f"\n  {name}: ⛔ FILE DOES NOT EXIST")
            continue
        hits = [(i, ln.strip()[:90]) for i, ln in enumerate(
            open(full, encoding="utf-8", errors="replace"), 1)
            if re.search(r"\bstatus\b|\bprefer\b|\boblige\b|\bforbid\b",
                         ln)]
        print(f"\n  {name}: {len(hits)} line(s) touching a status word")
        for i, ln in hits[:5]:
            print(f"     :{i}  {ln}")
        if not hits:
            print("     ⇒ NOT a consumer of `status`. The brief lists it as "
                  "one; on this measurement it is not, and the proposal "
                  "should not carry it.")

    print("\n" + "=" * 78)
    if missing:
        print(f"⚠️ {len(missing)} proposal row(s) did not match. FIX THE "
              f"PROPOSAL before circulating it: {missing}")
        return 1
    print("every enumerated consumer confirmed present.")
    return 0


def _wrap(text, w):
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
