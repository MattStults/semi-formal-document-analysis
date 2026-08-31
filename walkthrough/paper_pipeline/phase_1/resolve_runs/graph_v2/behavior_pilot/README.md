# behavior_pilot/ — index

Arc 2's working directory: the translated-corpus instrument, its truth ledgers,
and the research record. ~350 files, most of them generated artifacts. This
index separates the two.

## Read in this order

1. `HANDOFF_CURRENT.md` — state in one ⭐⭐ block (the rest is archive).
2. `ITERATION_NOTES.md` — the append-only ledger, entries 0000–0043. The
   primary artifact: every step, erratum, and withdrawal, written at the time.
3. `RETRANS_REVIEW_DISPOSITION.md`, `L1L2_ADVERSARIAL_REVIEW.md`,
   `L1L2_REVIEW_DISPOSITION.md` — the reviews that withdrew the headline
   claims, with independent re-derivations of each decisive finding.
4. `ERROR_CALCULUS.md` + `CALCULUS_RUNBOOK.md` — the repair state machine and
   its execution-derived, docs-tested runbook.

## Human-authored documents

**Framework:** `ERROR_CALCULUS.md`, `CALCULUS_RUNBOOK.md`, `calculus_diagram.md`,
`LINEAGE_SEAT_INSTRUCTION.md` (the verbatim adjudication-seat brief),
`TRANSLATION_CONTRACT_V2.md`, `node_behavior_contract.md`, `ROSETTA.md`.

**Pre-registrations** (frozen before measurement): `ROUND4_PREREG.md` (+
scaffold), `FRESH_DRAW_PREREG_DRAFT.md` (+ rounds 2–3),
`GENERALIZATION_PREREG_DRAFT.md`, `PREREG_panel_equivalence.md`,
`behavior_pilot_arm3_prereg_DRAFT.md`, `MINT_ARBITRATES_PREREG_DRAFT.md`,
`ITER2_VOID_RULING_AND_REMEASURE_PREREG.md`, `BLOCK2_TRANSFER_PREDICTIONS.md`,
`GENERALIZATION_FAMILY_PREDICTIONS.md`.

**Decisions and reviews:** the three disposition/review files above, plus
`ITERATION1_CD_DECISION.md`, `ITERATION2_CD_DECISION.md`,
`CONVERGENCE_REVIEW.md`, `CAMPAIGN_REVIEW_BRIEF.md`, `FIX_GATE_ASSESSMENT.md`,
`UA_PLAN_REVIEW_DISPOSITION.md`, `DEFENSIBILITY_BATCH_PROTOCOL.md`,
`R4_HELP_FAILURE_HYPOTHESES.md`.

**Design and studies:** `DESIGN.md`, `9B_DESIGN_ROUND.md`,
`CHEAP_TIER_DRIVER_DESIGN.md`, `CONVERGENCE_CAMPAIGN.md`,
`QUERY_CLASS_STUDY_SPEC.md`, `NORM_FRAME_THEORY_MAP.md`,
`ONTOLOGY_CONTRACT_DRAFT.md`, `BEHAVIOR_MODULE_SPEC.md`,
`GENERALIZATION_BUILD_SPEC.md`, `BEHAVIOR_TRANSLATION_FAILURES.md`,
`BEHAVIOR_CHECKLIST.md`, `CONCRETE_INSTANCES.md`, `PILOT_SUBSET.md`,
`ACT_BRIDGE_SPOTCHECK.md`.

## Code

`relevance_by_act.py` (the instrument), `satisfiability_census.py` (truth
assembly + census), `behavior_match.py`, `arm_ab.py`, plus the three test files
(`test_behavior_match.py`, `test_satisfiability_census.py`, `test_runbook.py` —
run with the arc-1 venv python, ~30 s).

## Generated artifacts (do not hand-edit)

- `behaviors_canonical_v*.json`, `modules_contract_v*.json` — versioned
  instrument inputs; the highest version is live, earlier versions are history.
- `qc_*.json` — query-class study outputs (corpus, codings, schema, censuses).
- `panel_run1/` — panel adjudications, fresh draws, convergence artifacts, and
  the retranslation integration test (`fresh_draw4/`).
- `act_*.json`, `assert_*.json`, `atoms_*.json`, `arb_marks_*.json` —
  translation layers consumed by the instrument.
- `*_RESULT.json`, `*_SCORED.json`, `*.log` — run outputs, kept as evidence.

Truth files (`ua_truth_visible.json`, `ua_truth_sealed.json`, fresh-draw
results) are adjudicated ledgers: append-only, never regenerated.
`ua_truth_sealed.json` is single-use and must not enter any visible-truth path.
