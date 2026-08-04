# The SELECT-audit seats: vocabulary sweep and query read-back

Why these seats exist: a behaviour's query atoms are SELECTED from the
document vocabulary by reading the behaviour's definition. Two failure classes
follow. A definition's text does not enumerate its own extension, so selection
can silently miss vocabulary atoms that plainly fall under the concept
(selection-recall failure) — no reconstruction test can catch this, because
you cannot detect the absence of something the source never stated. And
selection can include atoms the definition does not license (over-selection).
One directional test each.

## Seat 1 — the SWEEP (selection-blind)

**Input:** one roster file `select_audit/roster_<slug>.json`: the behaviour's
definition and the FULL document vocabulary (name, kinds, gloss per atom).
You are deliberately NOT shown which atoms the current query selected, and
you must not seek that out.

**Task:** for EVERY atom in the roster, SCORE it 0-3 against the definition.
Judge from the atom's name and gloss against the definition's CONCEPT, not
just its wording: a definition about "harms to third parties" covers any atom
naming a concrete way third parties come to harm, whether or not the
definition uses that word.

The scale — and 3 is a BUDGETED claim, not a vote:

    3  CORE: this atom belongs in a ~25-atom query for this behaviour. If
       forced to pick the few dozen atoms that ARE this behaviour in this
       document, this is one of them. EXPECT ROUGHLY 25-50 THREES ACROSS THE
       WHOLE ROSTER; the validator enforces a budget and REFUSES your file
       if you exceed it — calibrate as you go and revisit early 3s before
       delivering.
    2  RELATED: genuinely about the behaviour, but a query would not need it.
    1  TANGENTIAL: touches the topic; a careful auditor would not use it.
    0  OUT: co-occurrence only (generic process, formatting, other subjects).

The first binary version of this seat failed calibration — three different
runs marked 32-47% of the vocabulary "in scope", burying real findings in
noise. The budget exists so that failure mode is measured and refused rather
than silently produced. When genuinely torn between two scores, take the
lower.

**Output:** a JSON list, one record per roster atom, every atom exactly once:
`[{"name": "<atom>", "score": 0|1|2|3}, ...]`
Validated by `select_audit.py validate --budget <K>` (coverage, duplicates,
unknown names, malformed scores, budget). The validator — not you — diffs
score-3 verdicts against the actual selection; you never see the selection.

## Seat 2 — the QUERY READ-BACK

**Input:** the behaviour definition plus the SELECTED atoms only (names +
glosses), from the behaviour-atom artifact.

**Task:** two lists. (a) OVER-SELECTION: selected atoms whose name+gloss the
definition does not license — asserting them as query content misstates the
behaviour. (b) STATED-CONTENT GAPS: phrases of the definition's own text with
no covering selected atom. Cite the definition phrase for every finding.

**Output:** `{"over_selection": [{"name":..., "why":...}],
"stated_gaps": [{"definition_phrase":..., "why":...}]}`

## What both seats may never see

data/behaviours.json, data/panel-coverage.json, anything with "panel" in the
name, benchmark.py, DISAGREEMENT_REPORT*.md, case_*.json, dossiers/**,
HANDOFF.md, snapshots/**. Verdicts are about the DEFINITION and the
VOCABULARY, never about any judge's opinion. The sweep seat additionally may
not open behavior_atoms*.json (the selection it must stay blind to).

Small-model standard applies: these are atomic judgments; divergence between
a small and large model on the same roster is a defect in this brief.
