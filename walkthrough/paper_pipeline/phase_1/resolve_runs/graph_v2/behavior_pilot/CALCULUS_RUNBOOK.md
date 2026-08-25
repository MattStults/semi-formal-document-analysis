# CALCULUS RUNBOOK v1 — agent-facing: take a failure batch through the loop
(2026-08-24. EXECUTION-DERIVED: rewritten from ITERATION_NOTES.md
0001-0014 after three live iterations on how-to-approach-tradeoffs, per
the execution-derived-docs rule. v0's draft-from-design text is in git
history; every change here traces to a notes entry. Test: test_runbook.py.)

PRECONDITIONS (verify, do not assume):
  P0 clean tree, everything pushed. P1 you have read ERROR_CALCULUS.md
  (router R1-R5, amendments A1-A13). P2 the batch is a committed list of
  (behaviour, node) mismatches with their truth provenance. P3 REFILTER
  the batch against the CURRENT module before routing — a miss list
  scored against an older contract may contain already-fixed nodes
  (notes 0012: 3 of 23 were).

STEP 1 — TRIAGE (deterministic, $0):
  .venv/bin/python route.py <slug> <node>      # per mismatch -> class, move, trace
  GENERALIZATION-VENUE slugs (notes 0001): bare route.py KeyErrors —
  truth lives outside truth_all's fmap. Use the iteration1_triage.py
  pattern: derived single-module contract + frozen venue truth injected
  read-only + ctx truth_tier from committed ruling files; keep the
  census REAL, never ctx-asserted. probe.py takes --contract/--truth
  for the same venue.
  Batch rule (A5): group by class; INVENTORY-level moves (I1 builds, I3
  mints) sequence BEFORE dependent C-D deltas. Emit the routed queue as
  a committed artifact before any move executes. Census caveat (notes
  0001): SEPARABLE relative to a thin venue ledger is weak — say the
  ledger size in the artifact.

STEP 2 — MOVES, cheapest first, per the A10 capability router:
  R1 FIRST, ALWAYS, and once more before choosing between candidates:
    single-wave truth on engaged misses overturned at 3/9 in iteration 1
    (notes 0003); when delta candidates differ only on single-tier
    nodes, escalate THOSE nodes before deciding (notes 0004 — the
    choice becomes a truth fact, not driver judgment). Escalation may be
    DEFERRED only when every route lands in a suspension (no move to
    pay for; notes ITER4_MISS_TRIAGE) — then it is REQUIRED before any
    future fix attempt.
  VENUE (A10 Q3, notes 0006/0013): the cheapest CERTIFIED tier + seeded
    ~20% spot-check + tripwire. Certificates are brief-local AND
    task-class-local: parity measured on consensus items does NOT cover
    the dispute/boundary class (tripwire fired 4/9 there, notes 0014) —
    measure the dispute class separately or keep escalation resolution
    at the trusted tier. A fired tripwire is mechanical: quarantine or
    re-run, never silently accept.
  C-D deltas: candidates via decl-search/discriminator analysis; screen
    EVERY candidate with probe.py (charter + reason-drift + extensional
    fingerprint vs HYPOTHESIS_LEDGER.jsonl — a known fingerprint is the
    same route by another name: REFUSE). Class card REQUIRED (family,
    general form, predicted non-motivating members) before L2.
  I3 mints: mined-frontier candidates only; blind criteria; ONE coin per
    inventory version for zero-collider cases (A8). BEFORE the P3
    signature, MEASURE the criteria (notes 0011-0012): blind
    multi-seat calibration on ledger-known cases, families hidden,
    thresholds pre-stated (stability + separation) — the signature
    ratifies a measured brief, scoped to its measured coverage. A mint's
    consumption mechanisms are SEPARATE downstream config moves, each
    validated individually (notes 0013 erratum: never bundle them into
    one adoption decision or escalate their selection to a human — V4
    flip content decides mechanically; the wall died this way while the
    channel lived).
  Rulings/adjudications: LINEAGE_SEAT_INSTRUCTION.md VERBATIM, wave
    form, fresh seats on the certified venue; panels per registered
    samplers; prompts ONLY from committed packet files.

STEP 3 — VALIDATE (V1-V5, all before adoption):
  probe.py arithmetic on the FULL ledger; reason-drift: DEGRADED =
  break, SUBSTITUTED = design review (criticality filtering BLOCKED
  pending its brief-pinning); held-out class-card members must move;
  new flips blind-adjudicated (standing panel-tier truth discharges
  this on the record — no seat re-spent); V1 is NEVER sufficient: per-
  flip content kills regardless of charter sign (the codified
  radicalization rule; a 24-fixes/12-breaks move died on 8 relevant
  disengagements, notes 0013). REGISTER the predicted fresh-draw
  movement in a committed file BEFORE step 4, AND — BINDING, notes
  0009 — the primary metric MUST have registered COVERAGE of the
  move's extension: gains/losses sampled in the draw, or a registered
  full-extension census/probe. A zero-coverage registration is
  invalid-by-construction (iteration 2 fired a revert off a draw that
  sampled 0/16 of the move; the void-for-coverage ruling and one-shot
  re-measurement cost a day). After computing a draw, CHECK it samples
  the move's classes; if not, register a seeded probe in the same
  pre-dispatch commit (notes 0007).

STEP 4 — REALIZE: fresh confirmation wave from the frozen-prereg draw
  machinery (seeded, committed pre-dispatch), certified-venue seats +
  Fable spot-checks, score with a scorer COMMITTED BEFORE RULINGS
  against the registered prediction. Below the registered line ->
  REVERT with ledger record — unless the measurement itself fails a
  RESULT-BLIND validity criterion (coverage), in which case halt and
  surface; the remedy is re-adjudicating the SAME frozen samples at a
  higher tier, both verdict directions, thresholds fixed pre-dispatch,
  one shot — NEVER a new draw (notes 0010). Sequence venue decisions
  before scoring (score only after the seat set is fixed — removes the
  optional-stopping question, notes 0005).

STEP 5 — RECORD: traces (trace_check.py-certifiable) with evidence
  pointers; verdicts carrying enumeration scopes; SUSPENDED-OPEN for
  every non-certificated exhaustion, each with a NAMED RE-ENTRY;
  opposing UNANIMOUS panels on identical text = DEFENSIBLE-BY-
  CONTRADICTION, no seat spent, excluded from top-line error (Matt's
  ruling, notes 0011); commit + push each step's artifacts before the
  next step starts. The loop's healthy terminal is the QUIESCENT FIXED
  POINT: every open mismatch in a recorded suspension awaiting
  inventory growth, design capacity, or budget — say it that way.

STEP 5b — NOTES (binding): append a dated entry to ITERATION_NOTES.md at
  EVERY step — surprises, doc errors, next-agent-must-know items. An
  iteration whose learning is not in that file did not record its
  learning; this runbook is rewritten FROM that file, never from memory.
  HANDOFF = a fresh session booting CLAUDE.md -> HANDOFF_CURRENT.md ->
  this runbook -> ITERATION_NOTES.md. No compaction ritual, no handoff
  prompt: if a departing instance holds uncommitted context, THAT is
  the bug — commit it here before ending.

BUDGET DISCIPLINE (notes 0002/0008/0013): the agent cannot read /usage —
ask the human to paste it before EVERY Fable dispatch. When a standing
budget cap and a standing venue ruling conflict, that is a conflict
between two HUMAN rulings: surface the CONSTRAINT STRUCTURE (which
rulings collide, what the machine's default is — usually suspend until
the resource resets), never a design menu. Certified-Opus seats do not
bill the Fable bar; measured costs: ~30-80k raw per seat, spot-checks
~30k.

TRUTH ECONOMICS (Matt's ruling, 2026-08-24, notes 0019 — supersedes the
fresh-rulings-per-attempt inertia): TRUTH IS APPEND-ONLY AND MEMOIZED.
(a) A dispatch rules ONLY nodes with no standing panel-tier truth — a
draw's already-ruled nodes are lookups, never re-buys. (b) Rule at
PANEL TIER the FIRST time (certified venue): single-wave truth cannot
be memoized (0.846 self-agreement) and buying it first just prepays an
upgrade. (c) Acquire truth ENGAGED-SET-FIRST per behaviour — precision
becomes exact and noise-free at ~12 off-bar seats; the decline side
fills memoized-incrementally with twin-class propagation (~15-20%
saved). (d) Once coverage is complete, every realization/validation is
a $0 lookup — the noise apparatus (coverage rules, probes,
re-measures) applies only while coverage is partial.

STOP CONDITIONS (halt and surface, do not improvise): any spec gap (a
state with no applicable rule), any checker failure, any floor that a
change would lower, any needed judgment lacking a pinned brief, any
fired tripwire, any measurement failing its coverage criterion, /usage
crossing the registered cap, and any conflict between standing human
rulings.
