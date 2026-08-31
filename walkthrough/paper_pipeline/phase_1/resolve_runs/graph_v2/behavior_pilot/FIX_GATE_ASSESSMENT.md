# FIX-GATE ASSESSMENT — "all known fixes done on the current three behaviors"
# (the project owner's gate, 2026-08-18: no new behavior until this holds)

## DONE — each with its verification named

| fix | verification |
|---|---|
| H2 missing act families (protective_response; helpfulness+refuse) | r5–r9 tuning; census re-run |
| H3 bridge errors | FULL 720-bridge audit (3 blind auditors, 50 fixes); fresh-sample accuracy 0.95 |
| H5 wrong-actor | evidence-retag from read_backs; bridges actor-gated |
| H4 actless modules (relevance) | input-relevance channel (the project owner's design), 169/181 reachable; specificity-weighted |
| H4 actless modules (contradiction) | M30 sweep: 2 dropped norms repaired via full ceremony; web-trust conflict demo; 5 correctly assertless |
| Mutation-stage coverage | census-driven scaffold v7/v9 (scope-confirmed x3); 12-module spot-check: residual silence is correctly-conditional; (b) earns keep on tuning (0.77>0.75, declines only wrong engagements) |
| H1 wrong-argument | per-behavior argument declarations wired (v8, tuning-neutral); global walls rejected by measurement |
| T2 seam collisions | repairs 8+9 (35 arity + 133 gloss nodes), drafted→blind-verified→applied→schema-valid; seam layer 0/0/0 |
| Instrument hardening | adversarial review (MATERIAL finding fixed w/ errata; 2 latent hazards hardened; numbers reproduced bit-for-bit) |
| Determinism + LLM-free path | verified (static audit; byte-identical re-runs; suite 2,267 green) |
| Pipeline for next time | TRANSLATION_CONTRACT_V2 + M30 + validators, wired into HANDOFF |

## REMAINING — small, named
1. `l796_1000_n034`: pre-existing schema failure (4 missing borrowed-name
   glosses); its 2 gloss edits held. Mini-ceremony, ~30 min.
2. `applies_to` polymorphism: ruled + gate-encoded; behavior-side use of
   the polymorphic gloss untested.

## THE ONE OPEN QUESTION FOR THE PROJECT OWNER
The corpus gate's MODULE-LEVEL hard queue predates this campaign and is
untouched by it: rebranding_derivation 204, readback_status_conflict 133,
needs_in_requires 66, provides_defined 38, needs_gloss_licence 29,
naf_polarity 12, refusal_inverted 8, exclusivity_unencoded 2. These are
the M-series semantic detectors' standing adjudication queue from the bulk
campaign (the corpus sealed with them as known state; many hits are
flag-for-attention, not proven defects — §11 anti-rules apply). Does
"all known fixes" include adjudicating this queue (a multi-session
campaign of its own), or is the gate satisfied by the arm-3 fix backlog
(everything above) plus the queue's existence being on the record?

## RULING (project owner, 2026-08-19) — detector queue EXCLUDED from this gate
The project owner ruled that the module-level detector queue needs its own
understanding session before any adjudication decision, and that meanwhile a
checkpoint reading of quality without them is worth having. So: the gate's fix scope =
the arm-3 fix backlog above; the fresh-draw re-registration proceeds with
the queue untouched and ON THE RECORD as known state (this section is the
record). The tempting alternative — folding a 500+-hit multi-session
adjudication campaign into the behavior gate — is rejected BY NAME as
scope creep that would block the checkpoint reading without a measured
reason to believe those hits move behavior-level numbers.

## RECOMMENDED NEXT MEASUREMENT (either way)
The fixed instrument differs from the registered one (v9 scaffold,
hardened code, repaired corpus). Its honest number = fresh-draw
re-registration (~50 new adjudicated nodes/behavior, frontier attention
only), which is also the direct measurement of "working very well".
