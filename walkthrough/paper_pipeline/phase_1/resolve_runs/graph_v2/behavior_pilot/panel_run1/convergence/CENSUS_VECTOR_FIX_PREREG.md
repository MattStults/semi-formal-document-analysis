# CENSUS vector() MERGE-FIX — pre-registered expectations (2026-08-21)

Campaign item Arc1-e (HANDOFF_CURRENT.md campaign start c7069143+). Frozen
BEFORE the fix; corrections append, never edit.

## The defect
`satisfiability_census.vector()` builds each node's feature vector from the
assert-level layers only (assert_signature/protects/purpose_actor). The real
instrument (relevance_by_act.relevance) has since merged the definition_*
lanes into all three layers (keys nid|c{i}), and a corpus-wide context-atom
consensus layer exists (undeclared; feeds no engagement yet). So the census
under-reports separability relative to the real instrument (RUN1_ASSESSMENT
run-2 maintenance item) and cannot see the reachable context-atom vocabulary.

## The fix (scope-faithful, two views)
- CURRENT vector: merged assert+definition layers, mirroring relevance()
  EXACTLY, including its jurisdiction rules: purpose credits from
  definitional keys (nid|c{i}) are EXCLUDED (the purpose OR-channel was
  verdict-gated on the assert lane only; lane-scope ruling 2026-08-20), while
  ACTOR credits from definitional keys ARE included (actor wall consumes all
  keys). Acts slot unchanged — corpus_acts() already performs example- and
  definition-act lifting, which vector() reads.
- REACHABLE vector: CURRENT plus consensus context-atom credits as context
  features — the forward view for the 9b declaration-design round
  (inventory-relative terminality, 9g: context atoms are annotated but
  undeclared vocabulary).

## Pre-fix baseline (frozen artifact: satisfiability_census_v18_PREFIXTURE.json)
Contract modules_contract_v18.json, old vector():
- caution: 31 mismatches -> UNSAT 3, SEPARABLE 28
- harm:    44 mismatches -> UNSAT 9, SEPARABLE 35
- help:    65 mismatches -> UNSAT 12, SEPARABLE 53
Collider nodes all UNSAT pre-fix: harm l831_1000_n001, l831_1000_n011;
help l797_830_n011.

## Registered predictions (falsifiable)
- P1 MONOTONE REFINEMENT: per behavior, UNSAT_current(after) is a SUBSET of
  UNSAT(before) and SEPARABLE(after) a SUPERSET. Adding features refines
  vectors; it cannot create new collisions. Any violation -> the merge
  deviates from relevance()'s actual semantics; stop and diagnose.
- P2 CONTROL: the 3 collider nodes remain UNSAT under CURRENT after the fix.
  Their registered fix family is act-refinement subtypes (Arc1-b) — an
  ACT-vocabulary change this layer merge does not contain. If any flips
  SEPARABLE here, the vector is seeing a feature relevance() does not.
- P3 REACHABLE >= CURRENT: per behavior, every CURRENT-separable mismatch is
  REACHABLE-separable.
- P4 MISMATCH INVARIANCE: the mismatch sets themselves are byte-identical
  before/after (the fix touches vector() only; engagement and truth come
  from the same v18 instrument in both runs).
- E1 EXPECTATION (directional, not a gate): at least one pre-fix UNSAT node
  becomes CURRENT-separable via definition-lane features. If NONE do, the
  fix is disclosed as inert-on-UNSAT (still required for faithfulness — the
  vector must mirror the instrument whatever the outcome; inertness here is
  reported exactly as S5's zero-effect was).

## Validation artifacts
- test_satisfiability_census.py: fixture tests of the merge semantics (incl.
  the purpose-exclusion and actor-inclusion jurisdiction rules, context atoms
  reachable-only) + the P1/P3/P4 real-corpus property tests against the
  frozen prefixture.
- Post-fix diff report: satisfiability_census_v18_POSTFIX_DIFF.json.
