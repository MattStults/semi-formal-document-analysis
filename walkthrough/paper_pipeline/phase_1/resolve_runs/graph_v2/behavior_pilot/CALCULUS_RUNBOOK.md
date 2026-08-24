# CALCULUS RUNBOOK v0 — agent-facing: take a failure batch through the loop
(2026-08-24. DRAFT-FROM-DESIGN: this v0 is written before the first live
driven iteration; per the execution-derived-docs rule it will be REWRITTEN
from the trace of iteration 1 — expect errata. Test: test_runbook.py.)

PRECONDITIONS (verify, do not assume):
  P0 clean tree, everything pushed. P1 you have read ERROR_CALCULUS.md
  (router R1-R5, amendments A1-A13). P2 the batch is a committed list of
  (behaviour, node) mismatches with their truth provenance.

STEP 1 — TRIAGE (deterministic, $0):
  .venv/bin/python route.py <slug> <node>      # per mismatch -> class, move, trace
  Batch rule (A5): group by class; INVENTORY-level moves (I1 builds, I3
  mints) sequence BEFORE dependent C-D deltas. Emit the routed queue as a
  committed artifact before any move executes.

STEP 2 — MOVES, cheapest first, per the A10 capability router:
  C-D deltas: candidates via decl-search/discriminator analysis; screen
    EVERY candidate with probe.py (charter + reason-drift + extensional
    fingerprint vs HYPOTHESIS_LEDGER.jsonl — a known fingerprint is the
    same route by another name: REFUSE). Class card REQUIRED (family,
    general form, predicted non-motivating members) before L2.
  I2 annotation: two-seat lane on the pinned brief; certificate check first.
  I3 mints: mined-frontier candidates only; blind criteria; ONE coin per
    inventory version for zero-collider cases (A8).
  Rulings/adjudications: LINEAGE_SEAT_INSTRUCTION.md VERBATIM, wave form,
    fresh Fable subagents; panels per registered samplers.

STEP 3 — VALIDATE (V1-V5, all before adoption):
  probe.py arithmetic on the FULL ledger; reason-drift: DEGRADED = break,
  SUBSTITUTED = design review (criticality filtering is BLOCKED pending
  its brief-pinning); held-out class-card members must move; new flips
  blind-adjudicated (wave seat); REGISTER the predicted fresh-draw
  movement in a committed file BEFORE step 4.

STEP 4 — REALIZE: fresh confirmation wave from the unruled pool (seeded,
  committed pre-dispatch), lineage seats, score vs the registered
  prediction. Below prediction -> REVERT with ledger record.

STEP 5 — RECORD: traces (trace_check.py-certifiable) with evidence
  pointers; verdicts carrying enumeration scopes; SUSPENDED-OPEN for every
  non-certificated exhaustion; commit + push each step's artifacts before
  the next step starts.

STOP CONDITIONS (halt and surface, do not improvise): any spec gap (a
state with no applicable rule), any checker failure, any floor that a
change would lower, any needed judgment lacking a pinned brief, /usage
crossing the registered cap.
