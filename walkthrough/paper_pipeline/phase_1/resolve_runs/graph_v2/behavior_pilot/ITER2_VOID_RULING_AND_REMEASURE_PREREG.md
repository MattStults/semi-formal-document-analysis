# VOID-FOR-COVERAGE RULING + RE-MEASUREMENT PREREG (2026-08-24)

## The ruling (project owner, accepted this session; drafted by the driver)
The attempt-3 P1 realization (ITERATION2_V5_PREDICTION.json /
ITER2_ATTEMPT3_SCORED.json, measured 0.40) is VOID FOR COVERAGE: its
estimator sampled 0 of the batch move's 16 gained nodes and the move
lost 0 nodes, so the number that gated the revert carried no information
about the move it gates. The registration error is the DRIVER'S (the
pre-ruling addendum caught this coverage gap for P3 and did not extend
it to P1/P2 — recorded in notes 0009). Validity here is a RESULT-BLIND
property: the same ruling would void a passing 0.80 measured on the same
zero-coverage draw. The registered revert is NOT executed; the failed
measurement stays in the record unedited.

BINDING RULE forward (runbook rewrite must carry it): a V5 primary
metric is invalid-by-construction unless its measurement has registered
coverage of the move's extension (gains/losses sampled, or a registered
full-extension census/probe).

## The re-measurement design (accepted verbatim; NO NEW DRAWS, ONE SHOT)
Anti-forking commitments: the frozen draws (seeds 20260824, 20260825)
are the only samples, ever; every threshold below is fixed BEFORE any
new ruling exists; single execution; the resulting panel-tier numbers
are FINAL for the blog regardless of direction — a bad number routes
surviving mismatches into the ordinary calculus queue as work items and
never triggers another measurement.

1. MOVE GATE (replaces voided P1): full-extension census. The move's
   extension is exactly 16 nodes. 3 already carry panel-tier truth
   (iter-2 escalation: l1_170_n040 3-0 R, l1_170_n046 3-0 R,
   l699_796_n010 2-1 R). The other 13 get 3-seat panels on the CERTIFIED
   Opus venue. THRESHOLD: the move stands iff panel-tier precision over
   ALL 16 >= 0.60; below, the revert executes immediately. No sample ->
   no variance -> nothing to re-roll. The 5 probe nodes' standing Fable
   rulings (5/5 relevant) become a 5-node Fable-vs-Opus cross-check.
2. UNIFORM PANEL TIER ON THE FROZEN DRAWS: every node of the attempt-2
   and attempt-3 draws (and the extension) lacking standing panel-tier
   truth — 62 nodes total, list = the committed packet — gets a 3-seat
   certified-Opus panel. Standing panel-tier truth is KEPT, never
   re-measured (no truth churn). Both attempts are then rescored at
   uniform panel tier, engaged AND declined sides (escalating both
   verdict directions so re-adjudication cannot inflate precision).
   REPORTING: each attempt's raw single-wave number AND its panel-tier
   number, side by side (the campaign's precedented raw-vs-adjudicated
   format). These are the final numbers.
3. FABLE SPOT-CHECK: seeded 13/62 sample (seed 20260836), one Fable
   seat, packet committed pre-dispatch. TRIPWIRE: >=3/13 disagreements
   with the Opus majorities -> halt-and-surface (no silent acceptance,
   no silent re-run). The 5-node probe overlap adds independent Fable
   coverage of the extension class.

## Registered seeds and artifacts
Panel packet: iter2_remeasure_panel.json (62 items, shuffle 20260835).
Spot-check: iter2_remeasure_spotcheck.json (13 items, seed 20260836).
Standing panel-tier registry frozen in this commit's scratch-derived
sets (40 nodes; recomputed deterministically by the scorer).
Venue: 3 fresh Opus seats (certificate ITER1_OPUS_PARITY_CERTIFICATE),
LINEAGE_SEAT_INSTRUCTION verbatim; 1 Fable spot-check seat.
Scorer: iteration2_score_remeasure.py (committed before rulings).
