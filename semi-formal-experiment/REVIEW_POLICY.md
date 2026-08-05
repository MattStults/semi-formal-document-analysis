# REVIEW POLICY — two-tier review (adopted 2026-08-05 after trialing)

Why this exists: full clean-context adversarial reviews are expensive, and the S3b
revision chain (REVISION 2 → 8) showed diminishing returns — early reviews caught
load-bearing structural defects, later reviews caught ever-smaller issues at the same
high cost. Full reviews remain essential at decision points; intermediate revisions get a
cheaper focused check instead. This policy was trialed on S4 and S3b and proved out.

## Tier 1 — full adversarial review

Open-ended, clean-context hunt for blocking / major / minor problems ("a clean bill of
health is a failed review"). Expensive (~3–4M tokens, 30–50 tool-uses).

Run Tier 1 only at DECISION POINTS:
* before a cycle OPEN (the design is about to be frozen);
* before a BUILD (implementation starts);
* when deciding whether a multi-revision design has CONVERGED.

## Tier 2 — verification pass

Focused check that the SPECIFIC findings from a prior review were correctly fixed, plus a
light internal-consistency check. NOT an open-ended hunt. Cheap (~0.3–0.6M tokens,
9–13 tool-uses — roughly 5–12x cheaper than Tier 1).

Run Tier 2 for INTERMEDIATE REVISIONS — a revision whose scope is fixing findings from a
prior review, with no decision point imminent. The brief must state the findings to verify
and instruct the reviewer NOT to hunt for new issues (note anything blocking it stumbles
on, but the mandate is verifying the fixes).

## The trial that justified this (2026-08-05)

| review | tier | verdict | cost |
|---|---|---|---|
| S4 adversarial review | Tier 1 | REVISE (1 blocking + 4 majors) | ~4.4M tokens |
| S4 REVISION → Tier-2 verification | Tier 2 | READY-FOR-NEXT-STEP (all 10 fixed) | ~0.29M tokens |
| S3b REVISION 8 re-review | Tier 1 | REVISE (0 blocking, 2 majors) | ~3.4M tokens |
| S3b REVISION 9 → Tier-2 verification | Tier 2 | READY-FOR-NEXT-STEP (S-A/S-B fixed) | ~0.61M tokens |

Both Tier-2 passes gave real confidence at ~5–12x lower cost than a full review.

## Known caveats

* The adversarial framing biases toward over-finding — not every finding is equal value.
  Weigh blocking > major > minor; do not treat minor findings as blockers.
* Diminishing returns are real: if successive reviews only surface minors, stop and decide
  whether to proceed with the minors documented, rather than revising again.
* A Tier-2 pass only verifies the fixes it was told to check. Findings left out of scope
  (e.g. minors deferred during a focused revision) stay on the record for the next Tier 1.
* If a Tier-2 pass returns anything other than clean, escalate to a Tier 1 full review.

## When in doubt

If it is unclear whether a review should be Tier 1 or Tier 2, default to Tier 1 when a
decision point is near (OPEN / build / convergence) and Tier 2 otherwise.
