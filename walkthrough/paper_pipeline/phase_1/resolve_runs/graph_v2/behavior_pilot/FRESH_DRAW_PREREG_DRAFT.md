# FRESH-DRAW RE-REGISTRATION — arm-3 instrument, post-fix certification (DRAFT for the project owner's signature)

Date drafted: 2026-08-19. Purpose: certify the project owner's gate ("the 3 behaviors all match
perfectly or have valid explanations") with an honest number from the FIXED instrument on
nodes it has never been tuned or adjudicated against. This is the measurement the next
behavior/document is gated on.

## Instrument (FROZEN at signature)
relevance_by_act.py + arm_ab.py + assert_protects.json (frontier-labeled, audited keys
locked) + behaviors_canonical_v9.json + modules_contract_v11.json + act_bridges +
situation reversal, at the repo state of the signing commit. LLM-free query path.
Permit-inheritance REJECTED (ruling in PROTECTS_LAYER_RECORD.md) — the strict wall is
what is being measured. No change of any kind after signature; scored ONCE.

## Draw (deterministic; executable only after signature)
Per behavior: from the never-adjudicated pool (762 corpus modules minus that behavior's
existing truth set; pools measured 605/608/637), draw a STRATIFIED sample with seed
20260819: 40 currently-ENGAGED + 40 currently-NOT-engaged nodes (random within stratum;
harm's engaged pool is 49, so its engaged stratum is 40 of 49). Stratification is
declared here, so the headline metrics are the per-stratum rates, never a pooled
"accuracy" (the pool engagement rates — help 62%, harm 8%, caution 64% — make pooled
accuracy incomparable across behaviors and inflatable; rejected by name).

ERROR-BUDGET RATIONALE (amendment, 2026-08-19, pre-signature): sampling error dominates
(±8 pts at n=25) over per-ruling noise (est. ±2–4 pts), so tokens buy nodes, not
instances. Alternatives rejected by name: 25+25 with 3-instance panels (spends 3x/node
suppressing the second-smallest error term); 3-Opus panels with Fable escalation on
splits (symmetric and budget-efficient, but unanimous-but-wrong shared-bias nodes are
invisible to the trigger and an n=20 audit detects only gross tier bias; retained as the
budget FALLBACK, tradeoffs stated, if Fable budget forces it mid-run).

## Truth protocol
Each sampled node ruled by ONE blind Fable instance (node span + behavior description
ONLY — no instrument output, no engagement state, no design docs). Additionally a SEEDED
RANDOM 20% of nodes per behavior (seed 20260819, drawn with the sample) get a 3-instance
panel; the panel ruling supersedes the single ruling on those nodes, and the observed
single-vs-panel overturn rate is the measured per-ruling noise. Estimated cost: ~336
rulings within a registered capacity allocation, $0 API. EXECUTION IS BATCHED per the
project owner (2026-08-19): run behavior 1, capacity checked, then go/hold on behaviors 2–3. A hold is
not a protocol violation: each behavior's result is complete on its own; unscored
behaviors stay unscored (no partial peeking).

## Registered predictions (derived from full-truth measurements of the fixed instrument;
margin: 1 node = 2.5 pts at n=40 per stratum, prediction band = point ± 3 nodes = ±7.5 pts (bands below kept as drafted, ±8, the conservative direction))
| behavior | engaged-stratum precision | not-engaged-stratum decline-correctness |
|---|---|---|
| helpfulness | 0.82 (band 0.74–0.90) | 0.73 (band 0.65–0.81) |
| harm-avoidance | 0.87 (band 0.79–0.95) | 0.67 (band 0.59–0.75) |
| caution | 0.74 (band 0.66–0.82) | 0.72 (band 0.64–0.80) |

KNOWN-DEFECT CONSISTENCY (disclosed; the predictions above already price these in):
harm's decline-correctness is the LOWEST prediction because the E1-structural residue
(protects-wall FNs incl. the 4 named permit nodes' class) lives in the not-engaged
stratum; caution's precision is lowest because its FP 28 class (E6 defensible +
structural act-typing) is undispatched by design.

## Falsifiers (any one fires -> the gate is NOT certified; report and stop)
F1: any behavior's engaged-stratum precision below its band floor.
F2: any behavior's decline-correctness below its band floor.
F3: panel 3-0 unanimous relevant on >=3 nodes in one behavior's not-engaged stratum that
    share a single new (not E1–E7-classed) failure locus — an unknown defect class.
F4: >30% of 3-instance panels split 2-1 in any behavior (truth tier too noisy to certify).
F5: single-vs-panel overturn rate >10% on the 20% subsample in any behavior -> single
    rulings are not certification-grade; all remaining nodes escalate to panels before
    any cell is scored (cost rises, protocol holds).

## Success criterion (pre-declared)
All six cells within or above band, no falsifier fired -> gate certified; next behavior
unblocked. Above-band results are checked for leak signature (per ITERATION_LOOP
perimeter) before being celebrated.

## Errata rule
Registered numbers are never edited; corrections append.

Signature: SIGNED 2026-08-19 (project owner). sha256 of this file at the moment of
signing (this line and below excluded from the hash, per the arm-3 convention):
28a30a27aca7b572cf4fa432a4d44699abd23c91e48e874f6da37b209f8fc5b4
Budget tripwire agreed at signing: helpfulness runs as 3 agent-waves; if wave 1 consumes
a disproportionate share of registered capacity, STOP (the project owner's hard line) and
fall back to the Opus-escalation design for remaining behaviors.
