# S3 OPEN-phase recomputation (CYCLE5_DESIGN §2, mandatory before PREDICT) — 2026-08-04

Operator record. Computed on the S2 keep baseline
(`snapshots/patient-backfill-2026-08-04.json`, pricing_version 1.2) with the
merged, 1.2-reconciled `patient.py`, scored EXACTLY as `snapshot.build_snapshot`
will score at MEASURE (summed channels → corpus-max normalize → PRECISION
rounding → frozen cuts from `thresholds_frozen.json`; predict = s > 0 and
s ≥ cut). Declared patients as per the design: harm → {third_party},
helpfulness → {user, developer}, caution → {} (disabled). Sanity: PatientIndex
with NO patients reproduces the baseline snapshot's recorded scores and
predicted sets EXACTLY, all three behaviours.

## ⛔ HALT: the d-plateau is BROKEN on the post-backfill population

The design's own §1.4/§5-Q6 condition fires: the flip set is NOT flat over
d ∈ {0.1, 0.25, 0.4}, so "hand-set with stated reasoning" is no longer
licensed — per the design, the constant "must be re-argued from golden-set
patient-contrast cases before build." PREDICT is NOT frozen; no prediction.json
is written; IMPLEMENT is untouched. **The designer must rule before this cycle
advances.**

Flip sets per d (vs the S2 baseline predicted sets; newly / no_longer):

- **d = 0.10** (18 flips): harm newly {m0015, m0215, m0265, m0266, m0268,
  m0269}; harm no_longer {m0108, m0111, m0194, m0239, m0275, m0276, m0290,
  m0355, m0466, m0575}; helpfulness no_longer {m0018, m0463}; caution 0.
- **d = 0.25** (17 flips): harm newly {m0015, m0215, m0265, m0266, m0268,
  m0269, m0577}; harm no_longer {m0108, m0111, m0194, m0239, m0275, m0276,
  m0290, m0466}; helpfulness no_longer {m0018, m0463}; caution 0.
- **d = 0.40** (12 flips): harm newly {m0015, m0265, m0266, m0268, m0269,
  m0577}; harm no_longer {m0194, m0239, m0275, m0290, m0466}; helpfulness
  no_longer {m0018}; caution 0.

d-sensitive members: m0577, m0215 (newly side); m0108, m0111, m0276, m0355,
m0575, m0463 (no_longer side). The pre-repair plateau was a small-population
fact; 368 length-≥2 chains dissolved it.

## The recomputed pin at d = 0.25 (for the designer's ruling, NOT frozen)

- **TOTAL 17 flips** — under the F4b budget (30), so the pre-registered
  stratified-sampling protocol would NOT trigger at this count (it remains
  pre-registered in the manifest path via flip_budget_plan.json should MEASURE
  disagree).
- **newly_predicted on RAW scores: 0** — the computed fact holds; every
  raw score moved down or held (I2 verified on the full population). All 7
  newly_predicted flips are normalized-side artifacts of the falling
  normalizer → `normalizer_drift` class per amended I2 (raw m0015/m0215
  unchanged; m0265/66/68/69/m0577 raw DOWN yet normalized UP because the
  argmax fell further).
- **Normalizer movement, disclosed:** harm corpus-max 2.4964 → 1.9593
  (−21.5%; the argmax clause is taint-discounted), so every untouched harm
  clause's normalized score rises ~27%. helpfulness and caution normalizers
  unmoved.
- **no_longer_predicted: 10** — harm {m0108, m0111, m0194, m0239, m0275,
  **m0276** (the defining case, flips out as designed), m0290, m0466},
  helpfulness {m0018, m0463}. All match_change (raw fell through the frozen
  cut).
- **Hard bound HOLDS:** no_longer_predicted ⊆ the uniformly-mismatch-attested
  predicted set (+ section-mates) on both behaviours. That set, recomputed:
  harm n=33 {m0108, m0111, m0175, m0176, m0194, m0214, m0220, m0221, m0222,
  m0239, m0260, m0263, m0264, m0275, m0276, m0290, m0355, m0466, m0575,
  m0578, m0579, m0580, m0581, m0582, m0583, m0584, m0585, m0586, m0587,
  m0588, m0590, m0591, m0593}; helpfulness n=2 {m0018, m0463}. (The old
  16-clause census-era set is a strict subset of the harm set minus m0589,
  which is no longer predicted at baseline.)
- **helpfulness is no longer zero-flip** — the design's "current-artifact
  luck" pin has expired as predicted: S2 chains naming model/system/
  third_party landed on helpfulness clauses; m0018 and m0463 flip out.
- **The under-18 story is INVERTED vs the pre-repair pin:** the 11
  fp_section_prior under-18 flips are GONE — under-18 clauses sit inside the
  taint set but SURVIVE the frozen cut because the normalizer fell with them;
  m0577 (under-18) flips IN at d=0.25 by normalizer drift. The pre-registered
  "the under-18 boundary IS the cycle" adjudication framing no longer
  describes the computed flip mass.
- **Census composition (DEV, attention-direction only, disclosed):**
  no_longer side: 6 × fp_promiscuous_atom (m0108, m0111, m0276, m0290,
  m0018, m0463) + 4 not-in-census; newly side: 2 × fn_family_absent_from_
  vocabulary (m0015, m0215 — normalizer drift ADMITS two census FNs) + 5
  not-in-census. The cycle now moves 6 members of its nominal 155-case class
  (was 1/155 pre-backfill).
- **m0221/m0222 (ever-adjudicated-correct):** inside the taint set — priced
  ×d forever — but do NOT flip at any tested d (they survive the cut). The
  review's standing concern is a price change without a flip at current cuts.

## What the designer must rule on before PREDICT can freeze

1. **The constant (blocking, the design's own condition):** re-argue d from
   golden-set patient-contrast cases, or amend §1.4's licensing basis. The
   flip set is d-sensitive at exactly the members listed above.
2. **The prediction content:** §2's pre-registered numbers (12 flips, 11
   under-18, helpfulness 0) are pre-backfill facts and do not survive; the
   recomputed pin above is the candidate replacement but freezing it is the
   designer's call, including the adjudication framing (the flip mass now
   rides normalizer drift + chain-of-command/stay-in-bounds mismatches, not
   the under-18 boundary).
3. **Normalizer-drift adjudication surface:** 7/17 flips are normalizer
   artifacts by construction; confirm they are dossiered as threshold-class
   (amended I2) and whether the newly-admitted census FNs (m0015, m0215)
   change the keep-criteria framing.

## State at halt

- Cycle patient-pricing-2026-08-04: OPEN complete (manifest validated;
  files_to_change baseline shas + undeclared-input closure recorded in
  state.json). PREDICT: HALTED, prediction.template.json emitted by the
  driver, prediction.json deliberately NOT written.
- The worktree merge is complete on main's working tree (uncommitted, riding
  this cycle's CLOSE per house discipline): patient.py + validate_query.py +
  test_patient.py + test_validate_query.py new; conftest.py + 
  test_no_reference_leak.py registrations; patient.py hand-reconciled to the
  1.2 chain-metadata seam (details in the manifest's MERGE RECONCILIATION
  paragraph). Full suite 2117 passed / 3 skipped; FORBIDDEN scan green.
- IMPLEMENT untouched: no patients declared in behaviours_query.json, no
  snapshot/dossier wiring — the working tree scores bit-identically to the
  S2 baseline (verified above).
