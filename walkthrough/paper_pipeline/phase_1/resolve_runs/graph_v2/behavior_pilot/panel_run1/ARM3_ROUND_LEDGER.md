# Arm 3 refinement ledger — validation slice (plateau watch)

Stopping rule (pre-stated): <0.02 gain on all behaviors for two consecutive
rounds, or 4 substantive rounds. Deviation-defensibility, arm (a) / arm (b)
where they differ.

| round | change (tuning/validator-driven only) | help | harm | caution |
|---|---|---|---|---|
| r1 | base generated ontologies | 0.77 | 0.56 | 0.62 |
| r2 | act subtypes; behavior acts narrowed | 0.77 | 0.52 | 0.62 |
| r3 | H2 protective_response; H3 retail; reachability generics+dims | 0.77 | 0.54 | 0.62 |
| r4 | full 720-bridge audit (50 fixes) | 0.77 | 0.56 | 0.57 |
| r5 | census H3 rebridges; v4 does (+refuse to help) | 0.79 / **0.81 (b)** | 0.56 | 0.57 |
| r6 | v4 BUG FIX (protective_response absent from caution's does-block) + caution generic provide restored | 0.79 / **0.81 (b)** | 0.56 | **0.68** / 0.65 (b) |

**FROZEN at r6** (2026-08-18): past the pre-stated 4-round cap. Caution's r6
gain (+0.11) is a bug-fix recovery, not tuning momentum; continuing past the
cap to chase it would be exactly what the cap forbids. Arm (b) verdict at
freeze, honestly mixed: helps helpfulness (+0.02), inert on harm, costs
caution (-0.03, declined one relevant node). Harm remains at its
census-explained H1 ceiling; the structural fix (act-argument scoping) is
future work, out of this registration.

Notes for the record:
* r5 is arm (b)'s first win: mutation stage declined a wrong helpfulness
  engagement (0.79 -> 0.81, recall 0.97).
* harm is pinned at 0.56 = the census-predicted H1 ceiling (wrong-argument
  engagements; the structural fix — act-argument scoping — is designed,
  unbuilt, and out of scope for this registration).
* caution r4–r5 was a self-inflicted REGRESSION, not a plateau: the audit
  moved caution-relevant acts into protective_response while a v4 assembly
  bug left protective_response out of the module does-block arm (a) reads.
  v5 fix: caution tuning 0.44 -> 0.81 (recall 0.96).
* Input-relevance channel (Matt's design) measured on tuning: harm +0.02,
  help recall 0.94->0.97, caution 0. Registered as a distinct reported
  state, not merged into act engagement.
* Corpus-side ceiling recorded: H4 actless (relevance side solved by the
  input channel; contradiction side = M30 sweep, 7 hits, adjudication in
  flight), H5 wrong-actor (actor tagging in flight).
