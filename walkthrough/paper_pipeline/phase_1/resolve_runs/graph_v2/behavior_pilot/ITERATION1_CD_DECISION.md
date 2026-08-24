# ITERATION 1 — C-D DECISION RECORD (how-to-approach-tradeoffs, 2026-08-24)

## The mismatch batch and its route
Queue r2 (ITERATION1_ROUTED_QUEUE_R2.json): 9 engaged-FPs, all panel-tier
after the R1 escalation wave, all C-D (census SEPARABLE both views at the
40-node repair ledger, ITER1_TRADEOFFS_REPAIR_TRUTH.json).

## ADOPTED DELTA (candidate B) — pending V5 realization
```json
{"governs_concern": ["substance_usefulness", "accuracy_calibration",
                     "formatting_style", "objectivity_neutrality"],
 "governs_conditional": {"tone_manner": ["vulnerable_interaction"]}}
```
Applied in iteration1_tradeoffs_contract_r2.json (module otherwise
byte-identical to the F1-repaired generalization build).

## CLASS CARD (V3)
- FAMILY: single-consideration presentation norms.
- GENERAL FORM (grounded in the definition's own boundary clause — "NOT
  this behaviour: the individual values being traded off"): the behaviour
  is the METHOD for arbitrating between competing values/goals. The spec
  expresses arbitration through clauses that govern what a response
  prioritizes substantively (substance_usefulness), its factual
  commitments under competing pressures (accuracy_calibration — e.g. the
  truth-vs-comfort ordering of l2555_2652_n001), composition under
  competing constraints (formatting_style — e.g. transformation-fidelity
  and completeness-vs-length), and neutrality between contested positions
  (objectivity_neutrality). Clauses whose norms govern ONLY tone/manner
  presentation are per-consideration prescriptions, not arbitration —
  EXCEPT in vulnerable_interaction contexts, where the spec's tone
  guidance is itself the resolution of a support-vs-autonomy-vs-safety
  conflict. That exception is TRUTH-GROUNDED, not fitted: the escalation-2
  panel (3-0) confirmed the vulnerable-context tone node l1368_1541_n018
  relevant AFTER the candidate set was on the table.
- PREDICTED NON-MOTIVATING MEMBERS (held-out, verified mechanically): the
  delta disengages 48 corpus nodes, 43 of them unruled (not in any truth
  set, so they could not have motivated the delta). ALL 48 govern only
  tone_manner and/or identity_meta — zero declared-quality nodes lost.
  Sample: l1108_1367_n025, l1707_1973_n024, l1707_1973_n039,
  l1974_2125_n003, l2405_2473_n006, l2474_2554_n007. The card predicts a
  blind seat rules these not_relevant to tradeoffs; the V5 confirmation
  wave tests that prediction on whatever the fresh draw samples.

## VALIDATION STATE
- V1 CHARTER (probe.py on the full repair ledger — for this slug the
  40-node attempt-1+escalation ledger IS the full assembled ledger, caveat
  recorded in notes 0001): fixes 5, breaks 0.
- V2 REASON PRESERVATION: drift 0/0/0 (augmented/substituted/degraded) —
  the wall gates whole-node engagement; surviving nodes keep identical
  derivations.
- V3: this card; held-out members verified to move (all 48 lost are
  card-class members).
- V4 PER-FLIP: the move creates ZERO new FP/FN on the ruled ledger
  (5 fixes, 0 breaks; the 43 unruled disengagements carry no truth and
  are the card's predictions, tested at V5).
- V5: registered prediction in ITERATION1_V5_PREDICTION.json BEFORE the
  confirmation draw's rulings; fresh seeded draw per the signed prereg's
  attempt-N protocol.

## REJECTED ALTERNATIVES (by name, with grounds)
- A (plain wall, tone_manner excluded outright): fix 6 / break 1 — but the
  break is l1368_1541_n018, panel-confirmed relevant 3-0 (escalation-2)
  AFTER this candidate was identified. Deleting panel-certified
  vulnerable-user guidance for a one-fix gain is the radicalization-revert
  error; rejected.
- C (wall also excluding accuracy_calibration): fix 8 / break 2, best
  ledger precision (0.90) — rejected because it deletes l2555_2652_n001
  ("don't lie to reduce anxiety"), a genuine explicit outcome ordering
  (truth > comfort) squarely inside the behaviour, plus l1368. The metric
  said ship it; the flip content said revert-on-arrival.
- B2 (accuracy kept, formatting conditional on user_supplied_material):
  fix 6 / break 1 — breaks l3877_3953_n002, panel-tier relevant (2-1
  overturn in the R1 escalation). Same defect class as A; rejected.
- All four candidates' extensional fingerprints are in
  HYPOTHESIS_LEDGER.jsonl (A9 no-retry closure).

## CONSCIOUS COSTS OF B (recorded, not hidden)
- l4572_4692_n008 (treat_teens_as_adults; tone_manner +
  vulnerable_interaction) REMAINS ENGAGED though the escalation panel
  ruled it not_relevant 3-0: it is declarably indistinguishable from the
  panel-relevant l1368_1541_n018 (same governs+context signature; the
  distinction lives in unconsumed slots). SUSPENDED-OPEN.
- Residual FPs l2821_3040_n030, l3147_3238_n007, l3954_4251_n038:
  verify_terminal (r1 contract, injected repair truth) stamps all three
  TERMINAL-STRUCT(enumerated: protects_concern, governs_concern,
  purpose_concern); KNOWN_UNENUMERATED (arg_sorts, party_concern,
  governs_conditional) structurally blocks any absolute claim ->
  SUSPENDED-OPEN at this inventory (A8), re-enterable when a consumer for
  the distinguishing slots (purposes are the visible separator for
  n030/n038) exists. Their identical-signature colliders: n030 vs TP
  l2555_2652_n001; n038 vs TP l3877_3953_n002; l4572 vs TP l1368_1541_n018.
- KNOWN LIMITATION: this is the corpus's FIRST live governs_conditional
  declaration. SC.census refuses contracts declaring it (Arc1-e guard) and
  verify_terminal lists it KNOWN_UNENUMERATED — census-based routing of
  this module is blocked until vector() learns conditional contexts. The
  ENGINE consumes it (relevance_by_act gov_cond path, present since the
  9a purity migration); only the analysis tooling lags. Queued as the
  standing Arc1-e addendum work item.

## Fix-ledger class (prereg vocabulary)
EXPECTED (module-local): a wall the definition's boundary clause implied
("NOT the individual values being traded off") that the first build did
not declare. Not ALARMING (no vocabulary gap: the qualities existed), not
FATAL. Attempt-2 re-measurement is therefore in-protocol.
