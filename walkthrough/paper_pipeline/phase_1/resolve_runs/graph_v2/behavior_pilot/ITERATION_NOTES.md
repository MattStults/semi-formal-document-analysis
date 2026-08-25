# ITERATION NOTES — append-only learning ledger for the calculus loop
(Convention, binding via CALCULUS_RUNBOOK step 5b: EVERY step of every
iteration appends a dated entry here — what surprised, what the docs got
wrong, what the next agent must know. This file is the SOURCE for runbook
rewrites; learning that is not an artifact here does not exist.)

## 0000 — SEED: tacit operational knowledge from the 2026-08-24 sessions
(committed so no handoff depends on any instance's memory)
- SUBAGENT REGISTRY loads at session start only: a new .claude/agents/*.md
  needs a session restart. The lean ruling-seat agent exists (Read-only
  tools); wave seats currently run as "claude"-type agents because they
  must read packet files.
- WAVE SEAT ECONOMICS: one lineage-brief wave seat rules 40 nodes for
  ~35-70k raw tokens; cache reads bill 0.10x. The whole dev-table day ran
  in ~3 points of a weekly Fable bar. Registered budget: bar hard-caps at
  12% (7% baseline + 5 experiment points, Matt 2026-08-24).
- SEAT FAILURE MODES seen live: ultra-short fragment passages push seats
  into document-completion (fix: the anti-completion fence line, pinned in
  E3/round4_pilot.py FENCE); one seat fabricated-from-memory dispatch was
  voided (rule: prompts ONLY from committed packet files, never retyped).
- Haiku JSON output can be malformed in grounds strings — parse verdicts
  with the lenient regex (see parity scoring scripts), never bare
  json.load, and say "must be VALID JSON; escape internal quotes" in
  briefs.
- HEREDOC PATCHING: python string-replace patches MUST assert-and-WRITE in
  the same script (one patch printed diagnostics and never wrote — caught
  by a later NameError); prefer literal strings grepped from the file over
  remembered escapes (a ▸ vs \\u25b8 mismatch silently no-opped a patch
  batch and the commit shipped without the widget changes).
- COMMIT DISCIPLINE FAILURES to not repeat: two commits today shipped with
  a red/unverified state (docs-test red; widget patch unapplied) because
  commit preceded verification — run the check, THEN commit.
- fresh_draw4/ is the round-4-era rulings home; result files named
  {HELP,HARM,CAUTION}_R4_RESULT.json feed truth_all's fmap. The
  defensibility overlay in ruling_packets/defensibility_rulings.json is
  highest-precedence truth.
- probe.py appends to HYPOTHESIS_LEDGER.jsonl keyed (post-A9) by
  extensional fingerprint; verify_terminal verdicts now carry enumeration
  scopes; ENUMERATED vs KNOWN_UNENUMERATED lives in verify_terminal.
- The Opus coordinator pattern works (dispatch batches, checkpoint the
  output file after EVERY batch with complete:false/true) — always include
  the checkpoint instruction; the first coordinator ran end-write-only
  until amended mid-flight.
- /usage cannot be read by the agent: ask Matt to paste it at checkpoints.

## 0001 — ITERATION 1, STEP 1 (TRIAGE), 2026-08-24
Batch: the 12 indefensible engaged-FPs of how-to-approach-tradeoffs
(GEN_BLOCK1_SCORED.json), attempt-2 repair under the signed gen prereg.
- RUNBOOK ERRATUM (first command, first failure): STEP 1's
  `route.py <slug> <node>` KeyErrors for generalization slugs —
  SC.truth_all's fmap only knows the three round-4 behaviours. The
  §9-precedented fix (route_validate.py case e) is route()'s ctx
  port-record mechanism. iteration1_triage.py goes one better: it keeps
  the census REAL by (a) projecting the tradeoffs module into a derived
  single-module contract (iteration1_tradeoffs_contract.json — same
  wrapper schema as v19, byte-identical module dict) and (b) injecting
  the FROZEN attempt-1 verdicts into SC.truth_all for this slug only
  (read-only consumption; the transfer claim is untouched). Only
  truth_tier is ctx-supplied, from the committed gen ruling files.
- TIER SPLIT: 3 of 12 FPs are panel-tier (l3596_3876_n037 3-0,
  l3954_4251_n008 3-0, l3954_4251_n038 2-1) -> route C-D directly.
  9 are wave-single -> router stops OPEN(P1): R1 prescribes 3-seat
  panel escalation BEFORE any move (A5 ordering: premises first).
- CENSUS CAVEAT (next agent must know): all 12 are SEPARABLE in both
  views, but the certificate is relative to the 40-node attempt-1 truth
  set, not the 640-node ledger — separability is cheap at n=40. V1
  charter arithmetic for any delta must run on this same 40-node ledger
  (it is the only truth these nodes have); the real test is V5's fresh
  draw, exactly as the prereg's attempt-2 protocol demands.
- Census mismatch count 15 = 12 FPs + the 3 not_engaged_FNs (FNs are
  NOT in this batch; they stay unrouted).
- Prereg alignment: the predictions file blamed a meta/procedural
  no-walls mechanism; a walls-style C-D delta would classify the fix
  ledger entry EXPECTED (module-local), keeping attempt-2 in-protocol.

## 0002 — BUDGET RULING (Matt, 2026-08-24, transcript->artifact)
The 12% weekly-bar cap registered in the SEED entry was already crossed
before iteration 1 spent anything: Matt pasted /usage = 23% Fable at the
step-1 checkpoint. STOP CONDITION fired and was surfaced, not improvised
past. Matt's ruling: ITERATION 1 MAY SPEND UP TO 3 POINTS — next hard
halt at 26% — and should ideally land the COMPLETE fix arc (escalation,
moves, V1-V5, confirmation wave) inside that envelope. This supersedes
the 12% registration for this exercise only. Checkpoint discipline
unchanged: ask Matt to paste /usage at every checkpoint; 26% is a
halt-and-surface line, not a soft target.
- BUDGET PLAN registered against SEED wave economics (40-node seat
  ~35-70k raw, cache reads 0.10x): R1 escalation 3 seats x 9 nodes
  ~0.5-1 pt; V4 per-flip adjudication ~0.5 pt; STEP-4 fresh
  confirmation wave ~1-1.5 pt. Orchestration stays lean; every wave is
  preceded by a /usage checkpoint.

## 0003 — ITERATION 1, STEP 2a (R1 ESCALATION), 2026-08-24
3 fresh Fable seats, LINEAGE_SEAT_INSTRUCTION verbatim, packet =
committed 9-node subset of the attempt-1 lineage wave packet. Raw seat
spend ~98k tokens (32.8/33.1/32.1k). Machine-checked: 3x9 rulings, all
nodes present, all verdicts valid.
- RESULT: 3 OVERTURNS -> C-T dissolved (l2126_2404_n034 3-0,
  l3239_3382_n005 3-0, l3877_3953_n002 2-1 SPLIT); 6 stand, now
  panel-tier. Artifact: fresh_draw4/ITER1_TRADEOFFS_ESCALATION_RESULT
  .json — supersedes single-wave entries FOR REPAIR ROUTING ONLY; the
  attempt-1 transfer claim (0.40, F2) stays frozen.
- A5 PREMISES-FIRST, CONCRETELY VINDICATED (blog-post material): the
  natural pre-escalation delta was a governs_concern wall excluding
  formatting_style/objectivity_neutrality — and two of the three
  overturned nodes are EXACTLY formatting_style/objectivity_neutrality
  carriers (l3877_3953_n002, l2126_2404_n034). A delta designed before
  the premise check would have validated against wrong truth and been
  reverted at V5. The 25%-of-batch overturn rate also says single-wave
  FP truth on a THIN engaged draw is noisy — future batches should
  expect R1 escalation to dissolve a nontrivial fraction.
- Queue r2 (ITERATION1_ROUTED_QUEUE_R2.json): 9 nodes, all panel-tier,
  all C-D SEPARABLE-both-views. iteration1_triage.py now overlays the
  escalation result (repair-ledger truth = frozen attempt-1 verdicts +
  panel supersessions) and emits the r2 queue when the result file
  exists.
- Discriminator snapshot AT UPDATED TRUTH: remaining-FP governs =
  tone_manner x6, accuracy_calibration x2, formatting_style x1; but TPs
  now carry tone_manner, formatting_style, accuracy_calibration too —
  NO single governs wall separates. The C-D candidate must come from
  finer structure (functor/arg-sort/purpose/context combinations);
  class card required before anything L2.

## 0004 — ITERATION 1, STEPS 2b-3 (C-D MOVE + V1-V4) and STEP-4 PREP, 2026-08-24
- ESCALATION-2 (~82k raw, 3 seats, 1 node): before choosing between delta
  candidates, the single-wave TP the leading census-expressible candidate
  would break (l1368_1541_n018) was panel-escalated: 3-0 RELEVANT. This is
  the iteration's second premises-before-moves win — the candidate choice
  became a truth fact instead of a driver judgment. PATTERN FOR THE RUNBOOK:
  when candidates differ only on nodes with single-tier truth, escalate
  those nodes BEFORE deciding.
- ADOPTED (pending V5): candidate B = governs_concern wall + the corpus's
  FIRST live governs_conditional (tone_manner:[vulnerable_interaction]).
  V1 5/0, V2 drift 0/0/0, V3 held-out 48/48 (all lost nodes tone_manner/
  identity_meta-only), V4 zero new ruled flips. Full grounds + rejected
  candidates by name: ITERATION1_CD_DECISION.md. TOOLING CONSEQUENCE the
  next agent must know: SC.census REFUSES contracts declaring
  governs_conditional (Arc1-e guard) and verify_terminal lists it
  KNOWN_UNENUMERATED — census-based routing of the repaired module is
  blocked until vector() learns conditional contexts. The engine itself
  consumes it fine.
- probe.py extended with --contract/--truth (defaults untouched) — the
  same gen-venue gap as route.py, same fix pattern. 4 candidates
  fingerprinted into HYPOTHESIS_LEDGER.jsonl.
- 4 residuals SUSPENDED-OPEN at this inventory (n030/n007/n038/l4572),
  verify_terminal scoped TERMINAL-STRUCT(enumerated: protects, governs,
  purpose); the visible separator (purposes slot) has NO consuming gate —
  a future I1 consumer build re-enters them.
- RUNBOOK ERRATUM (STEP 4): nothing documents how attempt-1 wave items
  were built from ctx packets. Reverse-engineered: ESTABLISHES paragraph +
  SOURCE TEXT section, ALL-CAPS-header segmentation, blank-line
  normalization — verified byte-identical on all 40 attempt-1 items before
  use (11 packets carry GRAPH NODE preambles and PROVIDES/NEEDS middle
  sections that must be dropped). Builder lives in the STEP-4 pre-dispatch
  commit; fold into ruling_packets.py at the runbook rewrite.
- V5 prediction registered (ITERATION1_V5_PREDICTION.json) BEFORE any
  attempt-2 ruling: P1 revert line >= 0.55 venue-matched, point 0.65±0.10,
  P3 mechanism (fixed class cannot recur), P4 decline >= 0.80. Draw seed
  20260824; pools 231/531; 5 ruled-ledger overlaps (fresh rulings anyway).

## 0005 — ITERATION 1, STEPS 4-5 (REALIZATION + CLOSE), 2026-08-24
Confirmation venue as registered: 1 wave seat (40 nodes, ~55k raw) +
3 panel seats (8 pre-registered rows, ~93k raw). Wave rulings were
committed and the venue decision (dispatch panels vs wave-only) was made
on budget alone BEFORE any scoring — keep that sequencing; it removes the
optional-stopping question entirely. Scorer was committed before rulings
existed. Result (ITER1_ATTEMPT2_SCORED.json):
- ENGAGED PRECISION 0.75 (attempt-1: 0.40). P1 PASS (>=0.55), P2 within
  band (point was 0.65), P3 PASS (zero fixed-class recurrence among the 5
  fresh engaged-FPs), panel split 1/8. Also clears S1's 0.70 bar at the
  repair venue — reported as exactly that, never as a transfer claim.
- VERDICT: candidate B KEPT. The V5 keep/revert line was P1, and P1 passed.
- P4 FAILED (decline_correctness 0.60 vs predicted >=0.80) and the failure
  is a PREDICTION-CALIBRATION error, not a repair defect, shown three
  ways: (i) all 8 fresh FNs were un-engaged BEFORE the repair too (the
  wall created none of them — they are pre-existing act-channel misses:
  substance/identity/objectivity clauses the does=[respond,comply] lanes
  never reached); (ii) zero of the 48 walled nodes were ruled relevant
  anywhere in the fresh draw; (iii) the one walled node the declined draw
  sampled (l3954_4251_n012, a fixed FP) was freshly, blindly re-ruled
  not_relevant — the fix confirmed on unseen truth. LESSON FOR THE
  RUNBOOK: predict decline_correctness from the POST-REPAIR pool
  composition, not by carrying over the prior attempt's figure — the
  attempt-1 0.85 was one draw of a different pool; single-wave FN noise
  on decline sides is real (this is the mirror of the 3/9 FP overturn
  rate found at R1).
- NEW MISMATCH QUEUE SEEDED (iteration 2): 5 engaged-FPs (l2821_3040_n029,
  l3147_3238_n009, l3596_3876_n028, l3954_4251_n038 AGAIN — the standing
  SUSPENDED-OPEN residual, drawn and re-confirmed FP at panel tier
  3-0 not_relevant, its wave+panel unanimous, l3954_4251_n040)
  + 8 not-engaged-FNs (list in scored file). Truth tier: wave-single
  except panel rows. These route through the calculus next iteration;
  the FN class (act-channel reach) is C-I-shaped, not C-D — the wall
  cannot cause or cure it.
- Budget actual: 10 seats total this iteration, ~430k raw subagent tokens;
  bar 23% -> 25% at last paste before panels (~1 pt to appear); Matt's
  26% halt line respected by measuring (paste) before each dispatch.

## 0006 — POST-CLOSE: PATH AUDIT + OPUS PARITY CERTIFICATE, 2026-08-24
Matt's rulings this block: (a) NO new monotonicity metric — the blog's
progress claim rests on the machine's existing artifacts (registered V5
predictions + charter records); (b) cut cost via the machine's own A10 Q3
mechanism; (c) THE FINAL ITERATION'S CONFIRMATION WAVE STAYS ON FABLE.
- PATH AUDIT ($0, committed: ITER1_TRACE_AUDIT.json): all 12 iteration-1
  traces replayed from recorded artifacts and clingo-certified legal
  (12/12, 0 violations); Theorem-2 port census: at most one P1 per
  resolution. Findings F-a1 (SUSPENDED_OPEN is not a terminal in the v1
  calculus.lp — suspensions are ledger states until encoded) and F-a2
  (validated deltas do not consume R3 budget) recorded.
- OPUS PARITY CERTIFICATE GRANTED (ITER1_OPUS_PARITY_CERTIFICATE.json;
  prereg gates committed BEFORE dispatch; zero Fable): 3 Opus seats on
  the 23-node panel-tier key -> majority 0.913, mean single 0.884
  (ABOVE Fable's own 0.846 single-wave baseline on the same key),
  per-class 8/9 + 13/14. Scope: lineage ruling seat, THIS brief,
  tradeoffs venue; re-measures on brief change; does NOT touch the 0.38
  flip-adjudication doctrine. Deployment: Opus waves + seeded 20% Fable
  spot-checks + >1-disagreement tripwire; final iteration all-Fable.
- REVISED COST PICTURE for iterations 2-3: Fable only for spot-checks,
  tripwires, and the final confirmation wave — ~1-1.5 points total
  instead of 4-6. Opus seat cost measured ~39k raw per 23-node seat.
- NOTE ON THE 2 PARITY DISAGREEMENTS (both contested-history nodes):
  l171_426_n018 (Opus 3-0 relevant vs key) and l2126_2404_n034 (Opus 2-1
  vs key relevant). Neither blocks the certificate; both are worth a
  future panel-of-record look if they ever matter to a decision.

## 0007 — ITERATION 2, STEPS 1-4-PREP, 2026-08-24
- ESCALATION ON THE CERTIFIED OPUS VENUE: 0/11 overturns (vs attempt-1's
  3/9 single-wave) — attempt-2's wave was accurate; all 13 misses real.
  Fable spot-check (seeded 3/11) held for the /usage checkpoint;
  tripwire >1 disagreement voids the Opus wave.
- FN MECHANISM (the finding of the iteration): the 8 FNs decompose into
  (a) override-headed chain-of-command clauses the does-lane missed
  (F1-era rendering used follow_chain_of_command->comply; the corpus
  heads to canonical override); (b) the spec's instruction-hierarchy
  DEFINITIONS — all-authority_plumbing, document-actor — structurally
  excluded by GLOBAL walls no declaration could exempt: a behaviour whose
  subject matter IS the machinery could not say so. Resolved by a new
  typed gate machinery_concern:[acts] (I1 build; engine + registry +
  handshake test one commit; inert unless declared; 43 tests green);
  (c) a provide-headed trio whose fix (+139 engagements even arg_sorts-
  walled) was rejected by name as the attempt-1-shaped precision bomb;
  (d) two definitional-lane nodes with no act credits (C-V lane named).
- DRAW LUCK IS REAL (next agent must know): the attempt-3 seeded draw
  sampled ZERO of the 16 gained nodes (p~0.26) — P3 would have been
  vacuously true. Fixed PRE-RULING by a registered addendum: seeded
  5-node machinery probe, separate rulings file, P3 scores on the probe
  only. RUNBOOK RULE CANDIDATE: after computing a confirmation draw,
  CHECK it samples the move's gain/fix classes; if not, register a
  seeded probe in the same pre-dispatch commit.
- Iteration 2 is the FINAL in-scope iteration (post-move queue is
  entirely fixed-or-suspended), so its confirmation venue is ALL-FABLE
  per Matt's ruling: 1 wave (40) + 3 panels (8) + 1 probe seat (5) +
  the pending 3-node spot-check.
