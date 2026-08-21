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

## ADDENDUM 1 (2026-08-21, frozen before the extension runs)
Post-first-implementation channel audit found TWO more live instrument-visible
feature families the merged vector still omitted:
(a) ARGUMENT SORTS — all three v18 modules declare arg_sorts, so arg_ok()
    filters engagements by each functor's sort (act_arg_sorts.json);
(b) AUTHORITY_PLUMBING — 71 merged keys are plumbing-flagged; the all-plumbing
    exclusion in signature_ok() is instrument-visible.
party_concern is declared by NO v18 module (party_ok inert); rather than
encode a dead channel, census() must FAIL LOUD if any module ever declares
it, since the vector would then be unfaithful.
Extension, registered before running: acts entries gain the functor's raw
argument sort (None = unspecified/fail-open, matching arg_ok); a plumbing-key
feature lists flagged key suffixes per node. P1-P4 re-asserted against the
same frozen prefixture (further refinement can only shrink UNSAT further);
P2 collider controls unchanged (act-refinement subtypes are still absent).

## ADDENDUM 2 — adversarial review finding ALARMING-1 (2026-08-21, correction)
The clean-context adversarial review (verdict: BLOCKED, scope-limited) found
that the acts tuple carried the assert STATUS, which relevance() never
consumes — engagement is gated by verb_hit/arg_ok/party_ok/walls only; status
rides into rel[cid] as reason text. Over-fine vectors shrink collision
classes, producing false SEPARABLEs. The review's scan found ONE instance
(helpfulness::l3877_3953_n010 vs its status-twin l3877_3953_n009, both
bridging to comply); an exhaustive pre/post-correction census diff then found
exactly ONE MORE that the scan's method could not see — it searched for
status twins INSIDE old collision classes, but removing status and collapsing
none/other sorts can merge classes that were previously apart:
avoiding-over-and-under-caution::l2126_2404_n023 (engage_objectively/oblige,
sort "other") vs l2126_2404_n010 (avoid_subjective_terms/prefer, sort None)
— both functors bridge to respond, both sorts fail open identically in
arg_ok, layers identical. Corrected set is therefore TWO false SEPARABLEs,
both reclassified UNSAT in both views; the diff verified no other verdict
changed (2 of 124 rows, both directions checked). decl_search_proto/
declaration_proposals.json already exhibits the n010 coupling (a proposal
with n010 in fixed_nodes, n009 in broken_nodes). Both defects predate this
fix (they are SEPARABLE in the PREFIXTURE too), so the frozen baseline
carried them; this addendum is the erratum, appended per the corrections
rule.
Corrections applied: (1) status removed from the acts tuple; (2) functor
sorts none/other/missing collapsed to one sentinel (arg_ok fails open
identically for all three; reviewer verified zero current impact); (3)
governs_conditional gains the same fail-loud guard as party_concern
(declared by no v18 module; the flattened contexts slot cannot express its
per-key pairing); (4) remaining latent representation gaps (per-key
actor-purpose conjunction, all-plumbing key-count, fail-open asymmetry —
all verified zero-instance by the reviewer) go to LATENT_FIX_REGISTRY.md per
repo custom, not into code; (5) the docstring's "EXACTLY" softened to the
sufficiency scope (frozen v18 inventory).
P1 CORRECTED: UNSAT_after ⊆ UNSAT_before ∪ {l3877_3953_n010,
l2126_2404_n023}, with both pinned UNSAT in both views. Expected counts
after correction: help UNSAT 8->9 current, 6->7 reachable; caution 1->2 in
both views; harm unchanged (7 current, 5 reachable). 9b must consume only
the corrected census output.
