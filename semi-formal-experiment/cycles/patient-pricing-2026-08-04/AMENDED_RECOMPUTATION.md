# S3 recomputation under the AMENDED mechanism (taint cap, d = 0.10) — 2026-08-04

Operator record, after the designer's three rulings (mechanism amendment per
DISCOUNT_DERIVATION.md §4; d = 0.10; normalizer-drift flips adjudicated
per-flip). Amendment applied and RED-first verified — see
MECHANISM_AMENDMENT.md (old->new shas). Full suite post-amendment: 2120
passed / 3 skipped. Scoring identical to snapshot.build_snapshot's MEASURE
path; baseline = snapshots/patient-backfill-2026-08-04.json; sanity
(no-patients bit-identity to the baseline snapshot): EXACT, all behaviours.

## ⛔ HALT: the amended-mechanism plateau check is ALSO not flip-set-identical

Ruling (2)'s stop condition fires, so PREDICT is NOT frozen. The facts, for
the designer:

- Flip sets at d = 0.08 and d = 0.10 are IDENTICAL (18 flips).
- d = 0.12 differs by EXACTLY ONE membership: m0355 (harm, "Do not lie"
  section) stays predicted instead of flipping out. No other clause moves
  anywhere in {0.08, 0.10, 0.11, 0.12}.
- The crossing sits INSIDE the derivation's licensed degenerate interval
  [0.10, 0.11]: m0355 normalized-vs-frozen-cut margin is
  d=0.08: −0.0080 | d=0.10: −0.0015 | d=0.11: +0.0018 | d=0.12: +0.0051
  (harm cut 0.2365). So even 0.10 vs 0.11 differ by this one clause.
- Character of the residual: this is NOT the F-linearity knife-edge the
  derivation repaired (that came from dense-clause mass and is gone — the
  rest of the set is flat across the whole range). It is a single near-cut
  clause whose normalized score passes within ±0.005 of the frozen cut —
  the m0422 near-cut bystander class (cut granularity), now expressed
  through d. m0355's sole recorded chain is
  psychological_manipulation__developer_user (patients {user} — mismatched
  with P = {third_party}), so the clause is legitimately tainted/capped;
  the d-sensitivity is purely that its capped residual passes within
  ±0.005 of the frozen cut as d moves.

## The candidate pin at d = 0.10 (NOT frozen — awaiting the ruling)

TOTAL 18 flips (≤ 30: per-flip adjudication, no stratified sampling):

- caution: 0 / 0 (patients [] — pricing disabled; bit-identity).
- harm-avoidance-to-third-parties: newly_predicted 6 {m0015, m0215, m0265,
  m0266, m0268, m0269}; no_longer_predicted 10 {m0108, m0111, m0194, m0239,
  m0275, m0276, m0290, m0355, m0466, m0575}.
- helpfulness: newly_predicted 0; no_longer_predicted 2 {m0018, m0463}.

Mechanism classes (raw-score facts, drift rule per amended I2):
- newly_predicted on RAW scores: 0 (I2 held population-wide). All 6 newly
  flips are normalizer-side: m0015/m0215 raw byte-unchanged, m0265/66/68/69
  raw DOWN yet normalized UP (harm corpus-max fell 2.4964 → 1.9593, −21.5%,
  argmax taint-capped). Per ruling (3): adjudicated per-flip, dossiers
  naming normalizer_drift as mechanism (S1 m0207 precedent).
- All 12 no_longer_predicted flips: match_change (raw fell through the
  frozen cut; the taint cap deepens suppression vs the old d·sum — e.g.
  m0290 raw 0.7237 → 0.1779).
- Hard bound HOLDS: no_longer_predicted ⊆ uniformly-mismatch-attested
  predicted set (+ section-mates); harm taint set n=33, helpfulness n=2
  (identical membership to OPEN_RECOMPUTATION.md's).
- m0276 (the defining case) flips out. m0575 (under-18 header clause) now
  flips out under the cap (margin −0.026, d-stable); the under-18 leaf
  clauses (m0577+ / m0579–m0593) remain predicted at every tested d.
- Census composition (DEV, attention-direction): no_longer side 6 ×
  fp_promiscuous_atom (m0108, m0111, m0276, m0290, m0018, m0463) + m0355,
  m0575, m0194, m0239, m0275, m0466 not-in-census; newly side 2 ×
  fn_family_absent_from_vocabulary (m0015, m0215) + 4 not-in-census.

## What the designer must rule to unfreeze PREDICT

The residual instability is ONE clause (m0355) crossing within the licensed
interval's own width. Options visible from here (operator lists, does not
choose): (i) freeze at d = 0.10 with m0355 IN the predicted flip set and its
knife-edge margin disclosed in the prediction notes; (ii) treat the ±0.005
near-cut band as the m0422 class and pre-register m0355's direction as
undetermined-at-freeze (a two-valued prediction the driver's exact-set check
may not support — would need a range/notes framing); (iii) re-derive the
tie-break inside [0.10, 0.11] to clear the crossing. The rest of the 18-flip
set is flat across {0.08 … 0.12} and freezes cleanly under any option.

## State at halt

Cycle phase: PREDICT (prediction.json deliberately not written; template on
disk). IMPLEMENT untouched (no patients declared; no snapshot/dossier
wiring; working tree still scores bit-identically to the S2 baseline with no
patients). Mechanism amendment COMPLETE and green: patient.py taint cap +
d=0.10 + derivation-sha pin; suite 2120/3 skipped; FORBIDDEN scan intact.
