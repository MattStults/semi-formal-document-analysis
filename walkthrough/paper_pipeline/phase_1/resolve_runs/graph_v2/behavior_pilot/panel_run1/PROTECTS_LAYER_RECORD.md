# `protects` annotation layer — accuracy arc and final state (2026-08-19)

The per-assert `protects` layer (TRANSLATION_CONTRACT_V2 §7, the E1 fix) is read by
`relevance_by_act.py`'s wall to gate module engagement on a behavior's declared
`protects_concern`. This file records how the layer's labels were produced and every
measured accuracy number, in order. Registered gate: >=0.85 blind-audit agreement
before any registration leans on the layer.

## Arc (all measurements blind, ground truth = auditor labels, locked in protects_locked.json)

| round | layer | measurement | result |
|---|---|---|---|
| 1 | v1 seat (DeepSeek-V4-Flash, ESTABLISHES-only 500-char input) | blind audit #1: 8 targeted + 25 random nodes, 56 asserts | 43/56 = **0.77 FAIL**; 13 corrections applied; targeted class = missed co-protection |
| 2 | v2 seat (v1 + audit-lesson prompt rules) | pre-registered calibration (protects_calibration_v2.json) | **FAIL 2/4** expected-change: co-protection classes unchanged; no-change drift both directions. NOT broadened. |
| 3 | v3 seat (v2 rules + two-step at_risk/protects elicitation + **input fix**: verbatim SOURCE TEXT now shown — root cause of round 2 was an input defect, the seat never saw the span's examples) | calibration re-run | **PASS 7/7** -> swept 922 unlocked asserts ($0.08) |
| 4 | v3 layer | blind audit #2: 40 asserts, deterministic draw seed 20260819 fixed pre-sweep | 28/40 = **0.70 exact-set FAIL** (functional wall-predicate agreement 34/40 = 0.85, recorded but NOT the registered metric); 12 corrections applied; truth-set checkpoint also *worse* (336 -> 332, harm FP 5 -> 9, over-listing) |
| 5 | **full frontier relabel** (Fable subagents, 20 blind batches, all 889 unlocked asserts; 96 audited keys locked untouched; ~0.9M session tokens, $0 API) | second input defect found & fixed en route: 15 nodes with run-local ids had EMPTY spans in every prior round (both annotator and auditor); spans recovered from each run's prompt_user.txt | layer now frontier-labeled end to end |
| 6 | tier study (identical 40-item packet + brief; only the model varies) | DeepSeek 0.60 exact / 0.82 functional; **Haiku 0.62 exact / 0.78 functional**; Fable = reference | Haiku is NOT better than DeepSeek here — both small tiers plateau ~0.60; the deficit is a tier threshold (stable normative doctrine on boundary cases), not a vendor artifact |

## Final distribution (985 asserts)
user 739 · developer 124 · society 105 · third_party 82 · minor 71 · unspecified 66 (multi-label)

## Truth-set checkpoint under the final layer
helpfulness 127/157 (81%, FP 24 FN 6) · harm 112/154 (73%, **FP 6** FN 36) · caution 92/125 (74%, FP 28 FN 5) · TOTAL 331/436 (76%)

The aggregate is flat across layer versions (336/332/331): the wall's FP<->FN trade, not
annotation noise, dominates. The 4 relevant harm nodes newly blocked under frontier labels
(l1707_1973_n029, l609_698_n016, l699_796_n012, l831_1000_n011) are all PERMITS whose span
protects the user's access/autonomy — the labels are right; the misses are the named
E1-structural residue: "whom an assert protects" != "whether the node bears on the
behavior" for exception-carving permits. OPEN DESIGN QUESTION for Matt (recorded, not
tuned away): should a permit inherit the protects of the forbid it carves an exception
into? The tempting alternative — hand-flipping those 4 labels to make the number go up —
is rejected by name: it would encode the answer to a design question as data.

## Accuracy status of the final layer
By construction the layer matches the tier that produced both audits' ground truth; the
0.85 seat-gate is therefore moot for THIS corpus (there is no cheaper seat to gate). For
the NEXT document, the contract requires: seat choice validated against a frontier blind
audit sample >=0.85 exact-set BEFORE bulk annotation, with the tier-necessity comparison
(round 6) as the evidence for whether a mid-tier seat suffices.

## Tier study conclusion + escalation architecture (2026-08-19, n=40 — pre-registration-grade evidence, not a registered result)
Small-tier failure mode (both models, both directions): (1) the unspecified<->user boundary
on epistemic-quality norms re-decided inconsistently per item; (2) one-party-off
co-protection breadth calls. Rubrics plateau because each new span surfaces a boundary
case the rubric didn't enumerate.

**Escalation-by-disagreement simulation** (trigger: DeepSeek and Haiku disagree on the
label -> escalate to frontier; else keep the agreed cheap label):
- escalation volume 16/40 (40%)
- agreed-cheap-label accuracy vs Fable: 21/24 = 0.88 (above the 0.85 floor)
- simulated hybrid accuracy: 37/40 = 0.93 at ~60% frontier-token savings
DESIGN FOR NEXT DOCUMENT (goes with contract §7): dual cheap seats label everything;
agreement keeps the label, disagreement escalates to a frontier instance; validate the
agreed-label accuracy >=0.85 on a fresh blind frontier sample before trusting the layer.
n=40 caveat: the 0.88 has a wide interval (21/24); the next-document validation sample
must be >=100 asserts before the design is relied on.
