# DISPOSITION — adversarial review of the L1/L2 licensing experiments
(2026-08-25. The question put to review: would passing L1/L2 as registered
actually support answering Q-A (complete representability for
separation under full retranslation) and Q-B (extension to novel
behaviours)? Clean-context Opus reviewer's full report:
L1L2_ADVERSARIAL_REVIEW.md (36 findings F1-F36, amendments A1-A20).
VERDICT: DOES-NOT-LICENSE — ACCEPTED after CoVe. L1/L2 as registered
in RETRANS_REVIEW_DISPOSITION.md are WITHDRAWN as licensing
experiments; they survive only as raw material for the amended
package below. No retranslation campaign is fundable on them.)

## CoVe results (driver re-derivations; the review is accepted only
## where these confirm or the claim is structural)
CONFIRMED exactly:
- truth_all() n/base-rates: helpfulness 477/0.560, harm-avoidance
  291/0.443, over-under-caution 285/0.540.
- coverage_translated.json translated_nodes = 183 (of 773): L1's
  "half the spec's nodes" do not exist in translated form — L1 as
  written presupposes the campaign it is meant to license (F32).
- query_class_corpus.json contains adria: 11 — every behaviour with
  adjudicated truth is IN the coding corpus; NO out-of-corpus panel
  truth exists anywhere in the repo (F29). Q-B is untestable by any
  currently registered experiment.
- panel-v5: 589 model-spec passages x 9 behaviours on disk, pinned,
  externally authored, unexploited (F30).
- Red gates live on disk: block-1 STOP RULE (GEN_BLOCK1_SCORED, prec
  0.40) and metric0: FAIL x3 (panel_run1/REGISTERED_RESULT) — L1/L2
  said nothing about them (F33).
- ua_truth_sealed.json: 38 nodes, single-use marker present (F35).
- undefined_harmfulness_catch_all exists in qc_canonical_values;
  agentic_action_footprint and integrity_of_human_oversight each fire
  once across the 100 coded definitions — L2's stress dimensions are
  singletons and its coverage clause is elastic (F10-F15 substance).
CORRECTED against the reviewer (findings survive, numbers replaced):
- panel-v5 majority(>=2) positive rates are 0.008-0.114 (driver
  re-derivation; e.g. helpfulness 0.085, third-party-harm 0.098,
  over-under-caution 0.071), not the reviewer's 0.012/0.044/0.007.
  The F28 incompatibility with the node ledger (0.443-0.560) is
  5-50x either way; the three-ledgers/truth-shopping finding stands.
- The reviewer's significance claims for the 1-NN results (p=0.0015,
  p=0.0097) are WRONG: one-sided binomial gives p=0.154 (18/25 vs
  0.60) and p=0.157 (19/27 vs 0.59). The 1-NN results are not even
  significantly above baseline — which STRENGTHENS the underlying
  base-rate conclusion but the "pre-satisfied" finding is restated
  as: L1's clause on a point-estimate reading is already met by
  numbers indistinguishable from noise (erratum #21, 4th recurrence).
- Corpus sparrow count is 23, not 24 (trivial).

## Dispositions
- ACCEPT F17+F18+F19 as the replacement design (the reviewer's A1-A12
  dependency chain), with the A13-A20 addendum amendments. Key parts:
  F18 reliability gate first (fresh uniform 60-node draw, two blind
  seats, alpha >= 0.67 floor, ~$0) — at 23/39 today this alone may
  kill the campaign cheaply; F17 blind-readout ablation (Arm T raw
  text ceiling / Arm R signature-only / Arm N seeded permuted null;
  MCC(R) >= MCC(T)-0.05 AND above 99th null percentile, per
  behaviour, worst-behaviour headline, ceiling = panel-internal
  agreement) — the direct Q-A construct, unpassable by fingerprinting
  or noise; F19 scaling pre-flight (60-node end-to-end, extrapolate
  cost/reliability to 773).
- ACCEPT A14 as the load-bearing amendment for Q-B: >= 3 genuinely
  out-of-corpus behaviours (no-sycophancy and undermine-oversight
  INELIGIBLE — in-corpus) x ~80-node uniform fully-ruled fresh draws,
  definitions verbatim-lifted, chosen by a schema-blind seat, hashed
  pre-annotation. Nothing substitutes for this.
- ACCEPT A16 (score on single-process uniform fresh-draw partitions,
  ~537 rulings, never the assembled truth_all() ledger — composition
  bias F31), A13 (name ledger/unit/threshold; no re-scoring against a
  second ledger without new registration), A15 (panel-v5 replication
  tier gated on a committed passage->node join audit, class-aware
  metrics only), A17 (L1 restructured as staged pre-flight), A18
  (L1/L2-successor results VOID unless the block-1 STOP RULE and
  metric0 FAILs are cleared or superseded by signed ruling; decision
  memo enumerates every red gate), A19 (UA seal off-limits, enforced
  by a registered test), A20 (every registration states compute
  cost as well as $).
- ACCEPT the false-negative protections F20-F27 (readout family with
  frontier-judge arm decisive; MCC/F1 primary; ceiling-relative
  scoring; both split types reported; behaviour-shaped pre-screen;
  seat parity checks before reading results; one-run-per-registration).
- NOTE the reviewer's F17 cost paragraph inherits the pre-C1 premise
  (its $ arithmetic is about API spend; panel/judge seats are
  subscription-side subagents at no API cost). Per C1/A20 the F17
  registration must carry a token estimate; the ~550 short judge calls are seat calls,
  and tier routing (certified cheap tier + frontier parity subsample)
  follows the project's standing pattern.

## Standing state after this disposition
- Q-A: answerable by F18 -> F17 (+A3-A7), using truth already on
  disk. Q-B: answerable ONLY after the A14 out-of-corpus truth
  purchase. Funding rule adopted verbatim: fund only on F18 pass AND
  F17 pass AND a scaling estimate inside budget.
- Nothing in this disposition is a finding that the ontology is
  inadequate; the reviewer's own caveat (preserved from 0041's
  disposition) still holds. The finding is that no experiment yet
  registered could tell us.
