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
