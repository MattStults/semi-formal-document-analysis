# Run 1 assessment (design tier: Fable, 2026-08-20)

## Prove-out verdict: PASSED, with the right kind of failures
1. INTEGRATION DEMONSTRATED: proposal deltas are mergeable module fragments and
   the predicted fixes/breaks were computed by actually mutating v18 and
   re-running RBA.relevance — the discrete charter arithmetic, not the soft fit.
   An agent can consume a proposal with zero interpretation.
2. IT REDISCOVERS OUR FAILURE MODES FROM DATA: caution protects_concern
   "+society" predicted 4 fixes / 79 breaks with a mechanism_note that the slot
   is fail-open-when-empty so the first value flips the whole wall — that is
   family-1's measured flood (harm+user, 36 FPs) found automatically. The
   discrete-rule prediction step is what catches it; the soft model alone would
   not have.
3. NET-POSITIVE HYPOTHESES SURFACED that manual search never tried: help
   purpose_concern "+empowerment" (stability 1.00, +7/3) and caution
   purpose_concern "+harm-prevention" (0.83, +2/0). Both are 9b-justifiable in
   principle (document-ends vocabulary was mined a priori). Status: HYPOTHESES —
   pending blind justification, break adjudication, fresh-pool cert.

## Spec gaps (mine, to fix in PROMPT.md before run 2)
- No context-x-quality interaction features -> governs_conditional unreachable;
  no party features -> party_concern unreachable. Add both families.
- Instrument-vs-model log-loss comparison is biased by the defensible mask
  (masked rows are mostly instrument mismatches); run 2 should report the
  comparison on ALL rows with defensible rows scored as correct-either-way.
- The act-encoding ambiguity the seat resolved (documented in build.py) should
  be fixed in the spec text as the seat read it.

## Honest limits confirmed
- Caution fit is weak (CV 0.42): 205 points is small; stability selection did
  its job filtering to 3 proposals.
- Everything is label-derived; the outputs are attention pointers. The real
  test of the WHOLE idea remains: do fitted proposals survive blind
  justification and fresh draws? That is a post-reset question.

# Run 2 assessment (design tier: Fable, 2026-08-20)
ANSWER TO THE CARVING QUESTION: interaction carvings of existing atoms buy
almost nothing (386 survived screening, zero governs-x-context stable). The
true carving queue is 3 nodes, byte-identical to opposite-verdict colliders
across all 543 columns: help::l797_830_n011, harm::l831_1000_n001,
harm::l831_1000_n011. CONVERGENT VALIDATION: these are exactly the nodes behind
the two DEFERRED act-refinement atoms from split mining
(provide:forbid.form_equivalence, exhibit:illustrate) — L1 residuals and the
Opus miner, blind to each other, agree on both the nodes and the fix family.
Run 3 is therefore NOT an open search: it is minting those two subtypes through
the standard pipeline (blind criteria already written in
split_mining_candidates.json -> two-seat annotation -> regression ->
adjudication).
Of the 40 unresolved: 33 have no collider (separable = declaration-space work;
the run-1/2 purpose_concern proposals cover 11 of these), 4 separated by
existing base columns, 3 = the carving queue.
MAINTENANCE ITEM (queued): satisfiability_census.vector() predates the adopted
definition_* lanes and context_atoms_consensus — census now under-reports
separability relative to the real instrument; update before it is next used as
evidence.
FAIR-COMPARISON SANITY: instrument beats fitted model on all three behaviors
(0.955/0.953/0.946 vs 0.897/0.936/0.781) — the optimizer is a proposer, not a
better instrument, exactly as designed.
