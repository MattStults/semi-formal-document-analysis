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

## ⚠️ AMENDMENT (2026-08-05, after the first real failure of this policy)

**A Tier-2 pass that verifies a claim ABOUT CODE must read the code. No exceptions.**

What happened: the S4 Tier-2 pass scoped itself to *"design-doc verification only — no code,
no git, no test runs"* and credited two findings as FIXED-CORRECT. A subsequent Tier-1
(`S4_ADVERSARIAL_REVIEW_R2.md`) found that one of them did not hold at all. The design had
claimed the cycle driver **enforces** revert when a regression bound is breached; it does
not — `cycle.py` records a PASS/FAIL check and refuses an *unjustified* decision, and the
revert is the DECIDE signer's obligation. That claim is **entirely** a statement about what
`cycle.py` does, and the pass that "verified" it never opened `cycle.py`.

The failure is structural, not careless: a design-doc-only reader can confirm that a document
now *says* the right-looking thing, which is exactly what a fix looks like from the outside.

Binding rules, from here:

1. **Scope follows the finding, not the tier.** If a finding's content is a claim about code,
   a version, a count, or an artifact on disk, verifying its fix requires reading that thing.
   A Tier-2 brief that forbids it is malformed and must be rejected rather than executed.
2. **A Tier-2 pass must state, per finding, what it actually checked** — file and line, or
   the recomputation — not merely its verdict. "FIXED-CORRECT" with no evidence is not a
   verification.
3. **A Tier-2 pass may not be the last word before a decision point.** Tier 1 still governs
   OPEN, BUILD, and convergence, and a design that changed substantially after its last
   Tier 1 needs another one, however clean its Tier-2 passes were.
4. **A fix that is purely editorial** — wording, cross-references, a deferred minor — remains
   Tier-2 territory. That is what the tier is for, and it is genuinely cheaper.

The cost ratio in the trial table below is real. So is the failure. Keep the tier; keep it
honest about what it can see.

## Known caveats

* The adversarial framing biases toward over-finding — not every finding is equal value.
  Weigh blocking > major > minor; do not treat minor findings as blockers.
* Diminishing returns are real: if successive reviews only surface minors, stop and decide
  whether to proceed with the minors documented, rather than revising again.
* A Tier-2 pass only verifies the fixes it was told to check. Findings left out of scope
  (e.g. minors deferred during a focused revision) stay on the record for the next Tier 1.
* If a Tier-2 pass returns anything other than clean, escalate to a Tier 1 full review.
* **A clean Tier-2 is weak evidence when the findings were about code.** See the amendment
  above — the first two clean Tier-2 passes in this repo were on exactly that kind of
  finding, and one was wrong.

## When in doubt

If it is unclear whether a review should be Tier 1 or Tier 2, default to Tier 1 when a
decision point is near (OPEN / build / convergence) and Tier 2 otherwise.
