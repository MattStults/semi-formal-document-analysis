# FRESH-DRAW RE-REGISTRATION — arm-3 instrument, post-fix certification (DRAFT for Matt's signature)

Date drafted: 2026-08-19. Purpose: certify Matt's gate ("the 3 behaviors all match
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
20260819: 25 currently-ENGAGED + 25 currently-NOT-engaged nodes (random within stratum).
Stratification is declared here, so the headline metrics are the per-stratum rates, never
a pooled "accuracy" (the pool engagement rates — help 62%, harm 8%, caution 64% — make
pooled accuracy incomparable across behaviors and inflatable; rejected by name).

## Truth protocol
Each sampled node ruled by a 3-instance blind Fable panel (variance protocol validated by
the truth-suspect panel: majority rules; 2-1 splits recorded as low-confidence; per-node
grounds quoted from the document). Panels see node span + behavior description ONLY — no
instrument output, no engagement state, no this-document. Estimated cost: ~450 rulings,
~12 Fable subagents, ~0.7M session tokens, $0 API. RUN ONLY on Matt's go (budget).

## Registered predictions (derived from full-truth measurements of the fixed instrument;
margin: 1 node = 4 pts at n=25 per stratum, prediction band = point ± 2 nodes = ±8 pts)
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
F4: >30% of panel rulings are 2-1 splits in any behavior (truth tier too noisy to certify).

## Success criterion (pre-declared)
All six cells within or above band, no falsifier fired -> gate certified; next behavior
unblocked. Above-band results are checked for leak signature (per ITERATION_LOOP
perimeter) before being celebrated.

## Errata rule
Registered numbers are never edited; corrections append.

Signature: (unsigned — sha256 of this file at signing is recorded below by Matt's "sign it")
