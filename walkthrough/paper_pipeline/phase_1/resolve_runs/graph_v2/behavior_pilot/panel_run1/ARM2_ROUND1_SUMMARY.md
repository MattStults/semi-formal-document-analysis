# Arm 2 (tuned) — round 1 summary, 2026-08-18

Protocol per PREREG §"Second arm": Fable-signal tuning on the tuning half
only; held-out half scored by FRESH adjudicators; layer-3 beam widened for
tuned arms (TOP_K 24); probe over unretrieved held-out nodes folded in.
Numbers are HELD-OUT-HALF only, cold-start vs tuned on identical truth.

| behavior | metric | cold-start | tuned r1 |
|---|---|---|---|
| harm-avoidance-to-third-parties | deviation defensibility | 0.31 | **0.72** |
|  | engagement defensibility | 0.53 | 0.84 |
|  | decline defensibility | 0.14 | 0.57 |
|  | recall of truth-relevant | 0.30 | 0.70 |
| avoiding-over-and-under-caution | deviation defensibility | 0.64 | 0.67 |
|  | engagement defensibility | 0.80 | 0.79 |
|  | decline defensibility | 0.00 | 0.50 |
|  | recall of truth-relevant | 0.73 | 0.68 |
| helpfulness | — | (cold 0.66 full-set) | not yet tuned |

Reading: tuning moves most where cold-start was worst (harm-avoidance,
+0.41) and little where cold-start was already decent (caution, +0.03).
Harm-avoidance's residual is retrieval reach (probe engaged 16/35
unretrieved held-out nodes) — layer-3, general. Caution's residual is small
and mixed (a little recall traded for decline defensibility).

First BEHAVIOR MODULE (caution): branch structure mirrors the definition;
per-branch coverage of relevant nodes reached: over_caution 38,
under_caution 33 — both branches covered, the interpretive fact a bag of
atoms cannot report.

Gate status (second document): one round on the worst behavior cleared the
panel's own defensibility level on the held-out set. Not yet enough to
call the gate — helpfulness untuned, caution flat, all n small — but the
direction is what the gate needs.
