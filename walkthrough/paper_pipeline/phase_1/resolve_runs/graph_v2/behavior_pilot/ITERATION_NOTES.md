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

## 0008 — FINAL-BLOCK BUDGET CHECKPOINT (Matt, 2026-08-24)
/usage pasted at 27% Fable; Matt: "Please continue." — explicit
authorization for the final all-Fable block (~2 points: spot-check 3,
wave 40, 3x panel 8, probe 5), expected landing ~29%. This supersedes
the iteration-1 26% halt line for this block only.

## 0009 — ITERATION 2, STEP 4 REALIZATION: STOP CONDITION FIRED, 2026-08-24
Attempt-3 (all-Fable venue as registered): engaged precision 0.40 — P1
(>=0.60) FAILS, registered consequence = REVERT the batch move. NOT
EXECUTED: halt-and-surface, because the move-level evidence contradicts
the estimator, and resolving that conflict binds process (Q5, Matt).
- THE ESTIMATOR CARRIED NO SIGNAL ABOUT THE MOVE: the seeded draw
  sampled 0/16 of the move's gained nodes and the move lost 0 — engaged
  precision was measured on a sample causally disconnected from the
  delta it gates. MY REGISTRATION ERROR: the pre-ruling addendum caught
  exactly this for P3 (added the machinery probe) and did not extend the
  same coverage requirement to P1/P2. RUNBOOK RULE (bind it): a V5
  primary metric MUST have measured coverage of the move's extension
  (gains/losses sampled, or scored on a registered probe), else the
  registration is invalid-by-construction.
- MOVE-LEVEL EVIDENCE, all committed: machinery probe 5/5 relevant
  (blind Fable, the card's thesis in the seat's own grounds); spot-check
  3/3; charter +3/0 on panel-tier truth; V2 clean.
- SEAT NOISE IS REAL AND MEASURED: this wave seat agrees 4/7 with
  standing ledger truth on the draw's known nodes, contradicting TWO
  panel-tier rulings (l3877_3953_n002, l3239_3382_n005). Baseline
  single-wave-vs-panel is 0.846. Corrected estimator (panel-tier truth
  substituted): 0.50 — still sub-line; n=20 draws carry ±~0.2; attempts
  2 (0.75) and 3 (0.40) are compatible with pool precision ~0.55-0.60.
  V5's own text warned it is 'a measurement, not a proof'.
- OPTIONS SURFACED TO MATT (his ruling required): (a) execute the
  registered revert; (b) rule the P1 realization void-for-coverage and
  re-measure under a coverage-valid registration; (c) accept the move on
  probe+charter evidence recording attempt-3 as noise-dominated. No
  branch taken in-repo pending the ruling.

## 0010 — RE-MEASUREMENT FINAL + ITERATION 2 CLOSE, 2026-08-24
Executed exactly per ITER2_VOID_RULING_AND_REMEASURE_PREREG.md; one
shot; numbers FINAL.
- MOVE GATE: STANDS at 0.875 (14/16 of the machinery move's full
  extension panel-relevant — no sampling, no variance, no re-roll).
  The two extension not_relevants are the residual to type later.
- FINAL NUMBERS (raw single-wave vs uniform panel tier):
  attempt-1 transfer 0.40 (frozen) | attempt-2 0.75 raw / 0.70 panel |
  attempt-3 0.40 raw / 0.55 panel. Pooled panel-tier engaged precision
  over both frozen draws: 23/38 = 0.605. The attempt-3 wave seat's
  strictness bias is confirmed (+0.15 at panel tier); the residual
  attempt-2-vs-3 gap is n=20 draw variance over a ~0.6 pool.
- SPOT-CHECK: 2/13 disagreements, tripwire NOT fired; the Opus
  certificate held on a node mix including machinery clauses.
- THE HONEST HEADLINE IS RECALL, NOT PRECISION: 23/40 pooled declined
  nodes are panel-relevant. The module's engaged side sits ~0.6-0.7;
  its DECLINED side leaks a large relevant mass — the provide-class and
  definitional-lane reach limits, now measured, not just characterized.
- TRUTH-INSTABILITY FINDING (do not let dict order hide it):
  l3239_3382_n005 carries two OPPOSING unanimous Fable panels (iter-1
  escalation 3-0 relevant; attempt-3 panel 3-0 not_relevant). The
  scorer's recency precedence currently rules; the node needs a
  panel-of-record with the contradiction in front of it. Same watch on
  l3877_3953_n002 (2-1 R then wave NR).
- FINAL QUEUE handed to future work: 15 panel-tier FPs + 23 panel-tier
  FNs (ITER2_REMEASURE_SCORED.json + this entry); FN mass dominated by
  reach classes (provide-lane, definitional-lane), FP mass by the
  single-consideration family — both already carry SUSPENDED-OPEN
  grounds and named re-entry paths.
- Fable spend this block: spot-check seat only (~33k); everything else
  Opus. The campaign's Fable discipline held: paste-before-dispatch at
  every Fable seat, tripwires never silently passed.

## 0011 — MATT RULING: DEFENSIBLE-BY-CONTRADICTION, 2026-08-24
Matt's ruling on the n005 flag: opposing UNANIMOUS panels on identical
text/brief = the node is defensible either way and must not hit the
top-line — score it match-or-defensible, the campaign's standing metric
shape. MECHANIZED AS A ZERO-COST RULE: the contradiction IS the
defensibility certificate (no seat, no panel-of-record needed — that
queued item is closed by this ruling). Qualification bar: two full
panels, both unanimous, opposed. l3239_3382_n005 qualifies;
l3877_3953_n002 (2-1 panel vs wave) does NOT and stays contested.
Applied append-only to ITER2_REMEASURE_SCORED.json: pooled
match-or-defensible engaged = 24/38 = 0.632; registered final numbers
untouched. RUNBOOK RULE CANDIDATE: check every truth supersession for
the opposing-unanimous pattern before letting recency precedence decide.

## 0012 — ITERATION 3 OPENED: TRIAGE + MINT DESIGN, 2026-08-24
- Queue refiltered against the CURRENT module first (lesson: never route
  a stale miss list) — 3 FNs already resolved by the kept iter-2 move;
  n005 out as defensible-by-contradiction; final 14 FP + 20 FN, all
  panel-tier (R1 free).
- ROUTE: C-I(I3) unified mint. Contrast analysis supports ONE
  distinction serving BOTH directions: FN spans carry
  ordering/exception/bounded-permission structure ("never refuse
  unless…", "allowed as long as not…"), FP spans are single
  prescriptions. Drafted as MINT_ARBITRATES_PREREG_DRAFT.md — per-assert
  ARBITRATES mark, consumed as an act-channel wall (precision) + an
  additive channel (recall). The hard boundary (concessive single norms,
  "comply even if long") is ruled NO in the brief with the panel-tier
  case that forces it.
- AWAITING MATT'S P3 SIGNATURE — the annotation lanes do not run
  without it (A10 Q4/Q5). Post-signature pipeline is Opus-dominant
  (two-seat corpus lane + certified-Opus escalations); Fable only for
  spot-checks and the attempt-4 headline wave.
- Convergence note for the writeup: l831_1000_n011 sits in BOTH this
  queue and split mining's deferred provide:forbid.form_equivalence
  list — the third time two blind-to-each-other methods named the same
  fix family.

## 0013 — RULING AMENDMENT + MACHINE-PRESCRIBED VENUE, 2026-08-24
Matt: "Let's ignore my 'final run' message for now" — the
final-iteration-on-Fable overlay is rescinded (for now). With it gone,
A10 Q3's prescription stands unopposed: attempt-4 runs on the CHEAPEST
CERTIFIED TIER (Opus, lineage-brief certificate) + seeded Fable
spot-checks + tripwire. Remaining Fable this week: two spot-check seats
(~0.6 pt from the 30% mark). DRIVER ERRATUM banked for the runbook
(with 0009's): when surfacing a halt, name the CONSTRAINT STRUCTURE
(which standing rulings conflict), never a design menu — two of the
three "options" I offered were not mine to offer.

## 0014 — ITERATION 3 CLOSE, 2026-08-24
Attempt-4 (certified-Opus venue per A10 Q3, coverage-valid registration):
ENGAGED PRECISION 0.85 (P1 pass; P2 exceeded on the HIGH side), DECLINE
0.70 (P4 pass; was 0.35-0.50 panel-tier), P3 move gate 10/14 extension
nodes relevant — the arbitrates_channel adoption REALIZED AND KEPT.
Wave spot-check 1/8 (certificate held again). Attempt series:
0.40 transfer -> 0.70 -> 0.55 -> 0.85/0.895.
- TRIPWIRE WORKED AS DESIGNED (blog material): the dispute-class
  spot-check fired (4/9) — the Opus certificate measurably does NOT
  cover the boundary-item annotation sliver, exactly the population
  2-seat disagreement selects for. Response was mechanical: quarantine
  the 43 dispute resolutions (assembly's own rule), marks 283->260,
  engagement 393->384; the only measured affected node was a fresh FP,
  so the quarantine RAISED the adjusted precision to 0.895 and P3 holds
  at 10/12. Lesson for certificates: measure parity ON THE DISPUTE
  CLASS separately before letting a cheap tier resolve escalations —
  consensus items and boundary items are different tasks.
- OPEN AT CLOSE: 43 suspended dispute marks (Fable-tier resolvable,
  ~0.5pt, next bar); the 8-node relevant-by-example FN class (second
  concept, future mint); the single-consideration FP family (unchanged,
  SUSPENDED-OPEN); C-V definitional-lane pair; runbook rewrite from
  notes 0001-0014 now carrying FOUR banked errata.
- Fable spend this block: 2 spot-check seats (~64k raw, ~0.6pt from
  30%). Everything else Opus.

## 0015 — QUIESCENCE + RUNBOOK v1, 2026-08-24
Following the machine's own prescription (Matt: "continue to follow the
state machine"):
- STEP-1 triage of attempt-4 misses: 9/9 into standing states, no new
  mechanism -> the tradeoffs loop is at its QUIESCENT FIXED POINT at
  inventory k (ITER4_MISS_TRIAGE.json). Escalations deferred per A5
  (nothing to pay for), required before any future fix.
- CALCULUS_RUNBOOK v1 rewritten FROM notes 0001-0014 (execution-derived;
  docs-tests 5/5). Carries: gen-venue truth-injection pattern, refilter-
  before-routing, escalate-before-choosing, certificates are task-class-
  local, measure-criteria-before-signing, consumption mechanisms
  validated individually, the binding V5 coverage rule, same-samples-
  higher-tier re-measurement, defensible-by-contradiction, quiescent-
  fixed-point language, constraint-structure-not-menus, tripwires never
  silently passed.
- REMAINING MAINTENANCE (queued, named): census/vector extension for
  party_concern, governs_conditional, machinery_concern, arbitrates_*
  (the Arc1-e build — design-tier, needed before census-based routing
  of the r4 module); trace-audit extension over iterations 2-3; the
  Fable-tier dispute re-resolution (~0.5pt, next bar).

## 0016 — ITEMS 1+2 COMPLETE (census extension + frozen transfer predictions), 2026-08-24
- Arc1-e MAINTENANCE BUILD landed: vector() 8->12 slots (append-only;
  pinned indices untouched), current_mask consumes every DECLARABLE_MOVES
  channel, guards lifted-with-reasons-discharged, registration fence
  updated same-commit, guard test rewritten to the structural form (every
  registry channel must map to a live-when-declared slot — new channels
  now fail loud here too). 43 tests green. FIRST census over a
  new-channel contract (r4): runs; 35 mismatches, incl. 1 UNSAT-both
  (future R5 datum). Census-routability of user-autonomy (party_concern)
  unblocked as a side effect.
- BLOCK2_TRANSFER_PREDICTIONS.md FROZEN before any block-2 ruling:
  user-autonomy (single-consideration FPs + machinery FNs; existing
  channels; 0 mints; 0.55-0.75), proportionate-risk (HEADLINE: the
  tradeoffs ARB mint transfers as a zero-annotation arbitrates_channel
  declaration — calibration IS arbitration; 0.60-0.80), general-welfare
  (C-V: does still carries ASP-literal names, the F1 class unrepaired in
  this module — checkable from the contract file alone; measure-after-
  repair, not before). Per-clause scoring rule frozen with them.
- STATUS: measuring any block-2 behaviour awaits Matt's signed prereg
  amendment (the F2 stop rule) + behaviour pick + budget envelope.

## 0017 — PREDICTION FALSIFIED AT $0 + D-RULINGS EXECUTED, 2026-08-24
Matt: D1 approved (ADDENDUM 5 signed), D2 user-autonomy, D3 run now
(2pt), D5' question resolved by FALSIFICATION: general-welfare has no
C-V defect — behavior_acts() regex-extracts canonical heads from the
ASP-literal form; the F1 class was bespoke NAMES, not ASP SYNTAX.
Prediction 3 clause (a) scored FAILED pre-measurement, correction
appended, modest v2 re-prediction recorded. RUNBOOK ERRATUM #13: verify
contract-level predictions against the engine before freezing (the
check was one line and I skipped it). This is the per-clause scoring
rule doing its job — a methodology hit taken in public before a single
seat was spent on it.

## 0018 — USER-AUTONOMY ATTEMPT-1 (PROVISIONAL) + ERRATUM #14, 2026-08-24
Venue executed as amended; all seats machine-checked. PROVISIONAL result:
engaged precision 0.60 (WITHIN the frozen 0.55-0.75 band — prediction
clause (c) holds provisionally), decline 0.55, panel splits 3/10.
- TRIPWIRE FIRED (3/8 wave spot-check) AND IT IS RIGHT: the Opus parity
  certificate was measured on the TRADEOFFS brief; I deployed it on the
  user-autonomy brief without re-measurement. ERRATUM #14 (runbook):
  parity certificates are BEHAVIOUR-BRIEF-LOCAL — a new behaviour's
  venue needs its own (cheap: the panel rows are the free key). The
  spot-check architecture caught the stretch at a cost of one seat.
- Scoring stands PROVISIONAL pending post-reset Fable verification:
  (a) brief-local parity vs the 10 panel-tier rows, (b) re-verification
  of the 3 disputed rulings, (c) the deferred 43-dispute re-resolution.
  ~1-1.5pt next bar, none of it urgent.
- Q1 DATA POINT: this fresh run produced one new erratum — the process
  layer is STILL amending (errata series 4,4,4,2*,1 — trending down,
  not yet zero; *0013/0009 counted to their iterations). The automation
  decision correctly waits.
- Budget: envelope respected — spot-check dispatched (~32.4 est.),
  dispute ride-along deferred at the 32% paste per the halt line.

## 0019 — TRUTH ECONOMICS RULING (Matt) + ERRATUM #15, 2026-08-24
Matt caught the overlap/tier waste: attempts re-ruled ruled nodes
(~30-40 node-rulings of pure overlap waste) and, worse, bought
single-wave truth first then paid to upgrade it (escalations, the
62-node re-measure). RULING: memoize-at-panel-tier, dispatch only
unruled nodes, engaged-set-first acquisition — identical total rulings
to bulk up-front but deferred, abandonment-safe, and rerun potential
preserved; runs get monotonically cheaper and end at $0 lookups.
Runbook amended (TRUTH ECONOMICS block). ERRATUM #15: the prereg's
fresh-rulings-per-attempt clause was justified for attempt-1 transfer
only; carrying it into repair attempts was inertia.
- EXECUTION PLAN (post-reset, TONIGHT 9pm PT): (i) brief-local Fable
  parity key for user-autonomy (~0.5pt — 1 seat over ~20 nodes incl.
  the 10 Opus panel rows; the erratum-#14 tripwire makes certifying
  BEFORE the 150-node Opus purchase mandatory, not optional);
  (ii) if certified: Opus panel-tier purchase of the remaining ~150
  engaged nodes (off-bar) + Fable spot-check (~0.5pt) -> exact UA
  precision, then the repair arc on lookups; (iii) if parity fails:
  surface — the UA venue economics change and Matt decides;
  (iv) 43-dispute re-resolution rides the first Fable seat.

## 0020 — ADVERSARIAL REVIEW OF THE PLAN: BLOCKING, LARGELY UPHELD, 2026-08-24
Clean-context Opus review returned 8 findings; CoVe verified every
factual claim before disposition (all checked out — incl. the exact
split-node names and the cap arithmetic). 5 accepted, 2 partial, 1
sub-claim rejected with the existing mechanism cited
(UA_PLAN_REVIEW_DISPOSITION.md). The big catches: my parity-key design
was UNSOUND (single Fable seat as key — the exact single-wave noise the
memoization rule itself names); the held-out seal requirement (tuning
against a fully visible key is Goodhart bait the anti-cheat perimeter
already names); the clause-(a)/(c) scoring holes; the moving-boundary
correction. Plan v2 committed; BLOCKED pending Matt's fresh envelope
(~2.5-3 pt — the sound key design costs more than the unsound one).
Q1 note: the review+CoVe cycle added 4 process rules in one pass —
the errata series is NOT converged; manual driving remains correct.

## 0021 — ENVELOPE + PLAN-V2 DISPATCH, 2026-08-24
Matt: "ok do it" at 33% for the ~2.5-3pt plan-v2 -> registered envelope
3pt, halt-and-surface ~36%. Dispatching: 3 Fable key seats (24 nodes),
3 Opus seats (the 14 key nodes lacking Opus majorities), 1 fresh Fable
dispute seat (43 ARB items). Spot-check seat follows the Opus purchase;
0.5pt reserve held for one tripwire response.

## 0022 — UA GATE: NOT CERTIFIED (one node shy, one direction), 2026-08-24
19/24 vs gate 20/24; not-side 0.74 vs 0.75. All 5 disagreements are
Opus-relevant-vs-Fable-not (both tripwire nodes among them) — the
divergence is a REAL brief-local permissiveness bias, not noise (Fable
panel splits 1/24). Measured conditional reliability: Opus NOT_RELEVANT
verdicts 14/14 vs the key; Opus RELEVANT verdicts 5/10 — an asymmetric-
certificate candidate (per-verdict-class certification, an A10 Q3
extension needing its own registered gate if adopted). F5 rescoring
executed once as registered: attempt-1 corrected = 0.45/0.80 -> clause
(c) FAILED low; clause (a) directionally supported. 24 Fable-panel
rulings memoized as trusted truth. HALTED per plan-v2 branch 3 —
venue-economics options to Matt: (a) asymmetric certificate + Fable
escalation of Opus-relevants (~2.5pt, mostly next bar), (b) full Fable
engaged set (~4-5pt), (c) park UA at the honest attempt-1 record.
Fable spent this block so far: 3 key seats ~1.3pt (-> ~34.3 est.).

## 0023 — DISPUTE QUARANTINE CLOSED + BLOCK WRAP, 2026-08-24
Trusted-tier resolution of the 43 ARB disputes: 9 yes / 34 no — the
Opus boundary-class permissiveness bias measured a SECOND time,
independently, same direction as the UA gate failure. Marks final r3 =
269; tradeoffs r4 engagement 384->386 (both truth-carrying changes
consistent: l699_796_n010 relevant+engages; l1_170_n042 relevant but
still act/wall-blocked — stays in the FN reach class). CONVERGENT
FINDING FOR THE CERTIFICATE DOCTRINE: two independent measurements now
show Opus over-marking/over-including on BOUNDARY items specifically —
per-task-class AND per-brief certification is not optional caution, it
is the measured shape of the capability gap.
BLOCK LEDGER: 4 Fable seats spent (~1.7pt: 3 key + 1 dispute) ->
~34.7% est.; reserve intact; envelope 36 respected. HALTED on the UA
venue-economics decision (options in notes 0022 / the halt report).

## 0024 — OPTION (a) EXECUTED: UA TRUTH LEDGER v1 + BLOCK CLOSE, 2026-08-24
- ASYMMETRIC CERTIFICATE VALIDATED IN USE: negative spot-check 10/10
  (tripwire clear) -> 74 Opus negatives memoized as trusted truth at
  ~zero Fable. Escalation batch 1: Fable downgrades 10/24 Opus-relevants
  — the Opus permissiveness on this brief measured a THIRD independent
  time (gate 5/10, dispute class 9-vs-23, now 14/24).
- LEDGER: 122/175 relevant-side+key nodes ruled (98 visible + 24
  sealed); 53 escalations PENDING next bar (~1.8-2pt).
- HONEST EARLY PROJECTION (disclosed-partial, firms up with the 53):
  visible engaged precision-so-far 13/83 = 0.16, and even projecting
  batch-1's 58% escalation-confirm rate onto the pending nodes the
  engaged precision lands ~0.25-0.30 — the user-autonomy module
  OVER-ENGAGES far more than any sample suggested (attempt-1 said
  0.60; corrected said 0.45; the exhaustive ledger is heading to
  ~0.3). Prediction clause (a) (FP-dominant) is being confirmed
  emphatically; the band in clause (c) was optimistic by 2x. THE
  MEMOIZED-EXHAUSTIVE ARCHITECTURE JUST EARNED ITS KEEP: no n=20
  sample was ever going to reveal a 0.3-precision module reliably.
- BUDGET DISCLOSURE: escalation seats ran ~41k vs the ~33k estimate ->
  est ~36.4%, ~0.4pt past the 36 line. The overshoot is mine (batch
  sized on stale per-seat costs); logged, not hidden. NO further Fable
  this bar.
- NEXT BAR QUEUE: 53 escalations (completes the visible+sealed engaged
  truth) -> exact precision -> FP-population triage -> repair arc on
  lookups -> single seal-scored confirmation -> prediction §1 final
  scoring + the Q1 errata datum.

## 0025 — ERRATUM #16 (stale reset belief) + CONTINUE RULING, 2026-08-24
Matt: there is NO upcoming 9pm reset — the Sunday-9pm reset in my notes
was LAST week's (Aug 23, already passed); I carried it forward as a
stale belief through several plans. ERRATUM #16: budget scheduling must
use dates, not remembered anchors; the bar's actual reset schedule is
Matt's to state. RULING: continue now — remaining 53 escalations
(~2pt, est landing ~38.5%). EXPECTATIONS RECALIBRATION recorded: raw
zero-adaptation transfer is weak (UA exhaustive ~0.3 vs the 0.55-0.75
band — second optimistic band; mechanism: protects(user) walls fail
open nearly everywhere for comply/respond heads); the failure SHAPE
was predicted exactly; the program's value claim is cheap verified
repair (0.3-0.8 -> 0.85+ in ~2 iterations at 2-4pt), not first-shot
transfer.

## 0026 — UA ENGAGED-SET TRUTH COMPLETE: EXACT PRECISION 0.262, 2026-08-24
All 77 escalations done (batch2: 27 confirmed / 26 downgraded — Fable
downgraded 36/77 Opus-relevants overall, the permissiveness now
measured at scale). THE NUMBER: visible engaged precision is EXACTLY
32/122 = 0.262 (seal: 38 nodes untouched, single-use). The sample
series that pointed here: 0.60 (n=20 wave) -> 0.45 (corrected) ->
0.262 (exhaustive). NO SAMPLE WAS CLOSE. Prediction §1 standing:
clause (a) FP-dominant CONFIRMED emphatically (90 FPs vs 3 sampled
FNs); clause (c) band FAILED by >2x (already scored); clause (b)
scores at repair time. The module engages 160 nodes to find ~40
relevant — the repair arc's task is now a fully-enumerated,
truth-complete FP population of 90 visible nodes, routable at $0.
Escalation seat costs ran ~60k each (note: 53-node packets; the
per-seat overhead model needs the node-count term — see the batch1
sizing miss, notes 0024). Budget: est ~40.4% (2pt authorized -> ~38.5
est; actuals nearly 60k/seat -> overshoot ~1.9pt vs estimate across
the batch — DISCLOSED; the cost-estimation erratum is now twice
repeated: #17, fix the model before the next sizing).
NEXT ($0 until the confirmation): FP triage -> repair arc on lookups ->
seal confirmation -> prediction final scoring + Q1 errata count.

## 0027 — V5-AS-TRUTH MEASURED (Matt's question), 2026-08-24
Answered with data: the shelf panel projects to node level at 0.50-0.75
agreement (granularity smearing) — unusable as truth, the prereg's
closure now measured-correct. ERRATUM #18: measure shelf data sources'
certificate-ability BEFORE the dominant spend, not after the question.
Artifact: V5_TRUTH_TIER_MEASUREMENT.json.

## 0028 — RECURRENCE ANALYSIS: SECTIONS NOT STATEMENTS, 2026-08-24
Matt's question answered with counts (PROBLEM_NODE_RECURRENCE.json):
zero retranslations ever; 7/138 statement-recurrers (contested +
suspended-by-design); the mass is sectional (style/formatting +
objectivity + authority-machinery). KEY DESIGN CONSEQUENCE: the same
style-section nodes FP across BOTH behaviours measured -> the missing
concept is corpus-level, and the UA mint should be designed as the
GENERAL single-consideration-vs-cross-consideration layer (ARB was the
behaviour-flavored first cut) so one mint amortizes across all
behaviours — the concrete mechanism by which the concept-per-behaviour
cost curve could actually bend.

## 0029 — DIMENSION-ACCRETION QUESTION (Matt) + THE TRACKED METRIC, 2026-08-24
Matt's architectural critique, recorded at full strength: ~1 new
dimension per behaviour extrapolates to an untranslatable schema — the
a-priori-translation goal dies of dimension obesity; the alternative is
direct frontier relevance with translation kept for audit only.
COMPETING HYPOTHESIS (falsifiable): mints are completing the FIXED
argument structure of a norm (ARB = internal structure; machinery =
standing; locus = operative object; joining action/actor/beneficiary/
quality/condition/force) — slot inventory bounded ~10-12, after which
behaviours consume existing slots with new VALUES (cheap).
TRACKED METRIC: slots-vs-values per behaviour. Current curve: tradeoffs
+2 slots (ARB, machinery); UA +1 projected (locus); PREDICTIONS ALREADY
IN PLACE: proportionate-risk = 0 slots (pure ARB reuse, frozen);
general-welfare = 0 slots (protects VALUE growth: animal/AI welfare).
KILL-CRITERION (registered): if behaviours 3 AND 4 each require a
genuinely new SLOT (not values), the frame hypothesis is dead — stop
minting, re-architect around direct frontier relevance.

## 0030 — THEORY GROUNDING (Matt's directive), 2026-08-24
"Find the existing theory instead of finding dimensions one by one" —
NORM_FRAME_THEORY_MAP.md drafted: every empirically-minted slot maps
onto the canonical inventories (von Wright's six norm elements; Hohfeld
correlatives; Searle constitutive/regulative — which PREDICTED the
machinery finding; defeasible deontic logic = ARB). Four a-priori gaps
no miss has forced yet (full Hohfeld relation-typing; inter-norm
priority as a RELATION; constitutive flag at translation time; deontic
vs epistemic modality). Proposal: derive the next document's schema
from the completed frame; kill-criterion upgraded to
zero-slots-outside-the-theory-frame. DRAFT-FROM-MODEL-KNOWLEDGE:
requires a literature-verification pass before anything binds.

## 0031 — THEORY REVIEW + SPOT-CHECK: BOTH LANDED, MUTUALLY CONFIRMING, 2026-08-24
The web-verified adversarial review found: one doctrinal error (Hohfeld
privilege/claim-right conflation), one unsupported attribution (locus as
von Wright content-object), one wrong equivalence (ARB=defeasibility),
category mixing (components/relations/types/attributes flattened into
peer slots), a near-unfalsifiable kill-criterion, and the wrong
comparanda (validate vs LegalRuleML/ODRL, not 1963). The blind
spot-check then CONFIRMED the two testable charges from data:
defeasibility 0.38 stability (relation-as-property fails), machinery=
constitutive 1/5. And the decisive separation result: NO canon form
field carves behaviour relevance (best 0.70 vs 0.59 base) — norm FORM
annotates cheaply and stably (7/8 fields 0.87-0.97, straight into the
next document's schema) but relevance lives on the CONTENT side
(target/locus), whose proper homes are ODRL target + frame semantics.
Map corrected append-only (C1-C7). NET for Matt's directional question:
the theory gives us the form layer a priori and free; it does NOT hand
us the relevance-carrying dimensions — those remain to be designed, now
against engineered standards instead of minted from misses.

## 0032 — AFK ENVELOPE (Matt, 2026-08-25), AUTONOMOUS DRIVE
Matt AFK: "drive this as far as you can, using less capable models to
the extent you can; try not to spend more than 5% of my fable budget
for the week." REGISTERED: incremental Fable cap 5pt; PLAN USES 0 Fable
seats (query-class study = Opus/Sonnet/Haiku per spec; UA R3
enumeration, validation, and the SEAL confirmation are all $0 — the
seal's truth was pre-bought). A mint, if the R3 space exhausts, gets
designed + calibrated on Opus and PARKS at the P3 signature for Matt.
No /usage pastes available -> no Fable dispatch at all this block
(strictly safer than the cap).

## 0033 — UA ARC (AFK block): MOVE-1 ADOPTED; TARGET MINT CALIBRATED AND HELD, 2026-08-25
- R3 enumeration (64 compounds, $0): admissible optimum = governs wall
  {substance, tone, objectivity}: 18/90 fixes, 0 breaks, 0 new FPs.
  ADOPTED (UA_REPAIR_MOVE1.json, ua_contract_r2.json). Seal UNTOUCHED.
- OPERATIVE_TARGET mint calibration (3 Opus seats, thresholds
  pre-stated): STABILITY 0.98 mean pairwise, ZERO 3-way splits — the
  most stable layer ever measured here. FP-side separation PASSES
  (0.20 <= 0.30). TP-side coverage FAILS the gate: 0.67 vs >=0.70 —
  5/15 UA TPs are relevant via other targets (incl. machinery-class
  and assistant-output-with-deference-content), so a PURE WALL is
  inadmissible (would break 5 TPs). HELD FOR MATT with the honest
  numbers: the concept is real and crisp; the consumption design needs
  a second disjunct (e.g. wall scoped to a sub-channel, or
  target-OR-machinery composite). The calibration-before-signature
  discipline did its job: a gate miss surfaced BEFORE any corpus
  annotation was bought.
- Tradeoffs cross-check (descriptive): the enum classifies the
  cross-behaviour recurrers as assistant_output — consistent with the
  amortization hypothesis.

## 0034 — AFK BLOCK CLOSE, 2026-08-25
Full block ran at ZERO Fable (envelope was 5pt). State at close, all
parked honestly:
- UA ARC: move-1 adopted (18/0/0); OPERATIVE_TARGET mint calibrated
  (stability 0.98 — best ever; FP-side passes; TP-side 0.67 vs 0.70
  gate -> pure wall inadmissible) -> HELD at Matt's signature with the
  second-disjunct design question. Seal untouched. 72 residual FPs.
- QUERY-CLASS STUDY: 100-def corpus built (exemplary Opus coordinator
  run); v1 vocabulary tripwired (my spec defect — under-determination,
  Opus-vs-Opus 0.47); v2 fix raised calibration to 0.87 and bulk pairs
  to 0.78 but the INDEPENDENT spot-check tripwired again at full-pattern
  granularity (0.36 vs 0.20). Halted without publishing a bound.
  MEASURED: verb 1.00, primary-place 0.93/0.75, full pattern 0.78/0.64
  — the reliable resolution is primary x verb; secondaries are the
  noise. DESCRIPTIVE (non-binding): 9 primary places observed over 100
  definitions, dominated by governed_quality (29), object_sphere (16),
  act (13) — shape-consistent with the bounded-frame hypothesis.
  DECISION PARKED: accept coarse bound / brief v3 / accept-with-noise.
- Tier data: no cheap tier certifies definition-coding (Sonnet 0.13,
  Haiku 0.00 at v1) — the first measured negative for the down-tier
  program on a design-adjacent task.
- Errata: #19 (my coding vocabulary under-specified — same lesson as
  the mint-criteria discipline: MEASURE the brief before scaling, which
  the phased design did, catching it at 15 items not 100).

## 0035 — COMPOSITIONAL-SUFFICIENCY PROBE + PROGRAM VERDICT, 2026-08-25
Matt asked whether the build-our-own-ontology idea failed. $0 probe:
best compact principled DNF over ALL existing layers on UA truth =
OR(gov_substance, gov_tone, head_comply): 23 fixes / 1 break — beats
the adopted wall (18/0) but leaves ~65/90 FPs untouched; the engine's
conjunctive-gate weakness was NOT the main bottleneck for UA.
VERDICT (recorded): layers succeed as annotation (stable, signal-
bearing); the instrument succeeded once (tradeoffs 0.85); the PROGRAM
is unproven at scale — cost curve unbent, one concept per behaviour so
far. DECISIVE PENDING EXPERIMENTS (both cheap, both designed):
corpus-wide OPERATIVE_TARGET (blocked on Matt's mint decision) and the
frozen prop-risk ARB-transfer test. Both land -> program stands; both
miss -> content doesn't compile and the instrument's role shrinks to
form-layer + audit over direct frontier relevance.

## 0036 — REPRESENTATION PROBES: THE INFORMATION FLOOR, 2026-08-25
Three $0 probes (Matt's optimization/latent questions):
- L1 over the FULL symbolic feature space (48 features, all sparsity
  levels): CV ceiling 0.76 vs 0.74 base — the annotations do not
  contain UA relevance; the guessed-library probe's conclusion was
  right for the right reason. (Convex fit; no initialization issue —
  features are deterministic indicators of committed layers.)
- TF-IDF text features (uni+bigram): CV 0.74 = base. Surface lexical
  content doesn't carry it either.
- Pairwise behaviour phi: 0.04-0.29 (help x caution 0.55 the sole
  exception) — behaviours are near-ORTHOGONAL dichotomies. Matt's
  log2(n) low-rank hypothesis has measured evidence AGAINST it; ~1
  load-bearing dimension per behaviour is geometry, not pathology.
SYNTHESIS (the session's clearest statement of what minting IS):
a mint = frontier judgment used as a feature extractor for ONE named,
blind-reproducible, auditable bit per node. The concept lives in deep
semantics (seats judge it at 0.9+; no shallow space reaches base+0.02);
embeddings would separate but collapse the instrument into direct-ask-
in-vector-form. THE COST FLOOR: ~one frontier-extracted dimension per
orthogonal behaviour + validation; everything around the floor (form
layer, truth memoization, validation-by-lookup, Opus extraction at
0.98) is what the program has successfully cheapened. Rank test proper
still blocked on cross-behaviour truth overlap (4 common nodes) — an
argument for ruling a common node panel across behaviours if the
low-rank question ever needs settling.

## 0037 — ERRATUM #20: CLOSED-VOCABULARY CIRCULARITY (Matt's suspicion, upheld), 2026-08-25
Matt flagged the too-tidy "last dimension defined just as you asked."
Upheld on inspection, two mechanisms: (a) ENDOGENEITY — his questions
caused this week's analyses; the tidy picture is authorship, not
coincidence; (b) CIRCULARITY — the query-class study's 10-place coding
vocabulary was written by the designer WITH knowledge of the built
layers; forced-choice coding into it structurally CANNOT discover an
out-of-vocabulary place (shoehorning presents as coder disagreement —
some of the tripwire noise may be exactly that). Therefore "100
definitions need no new places" bounds the query class RELATIVE TO the
designer's vocabulary only. RULE: saturation studies with closed
vocabularies measure vocabulary coverage, never space completeness;
unknown-dimension detection needs open coding or external falsifiers.
The claims that survive: TARGET's blind calibration (predates the
study), and the three EXTERNAL tests (TARGET at scale, prop-risk
transfer, next-document misses) — which do not share the designer's
vocabulary and can falsify what internal analyses cannot.

## 0038 — QUERY-CLASS ARC CLOSED: THE MEASURED BOUND, 2026-08-25
Matt's arc (open coding -> place-blind schema -> annotate -> separate)
completed end-to-end, all Opus, $0 Fable:
- DISCOVERY WORKED where my closed vocabulary could not: 24 emergent
  dimensions, 9 with no counterpart in my ten places (evaluation_unit
  and subject_matter_class the load-bearing two, dual-coder evidenced;
  our instrument is measurably utterance-locked).
- The vacuousness trap was caught (free-text values = fingerprints,
  zero reuse) and fixed by canonicalization (105 values, 46% merger,
  seat-independent 115/115).
- FINAL: separability 94/100 both seats identically; all 6 collisions
  are cross-source SAME-CONSTRUCT duplicates (the census doubling as
  corpus dedup); zero different-construct collisions. THE BOUND:
  24 dimensions x 105 values addresses the sampled character-spec
  query class completely, ~1.2 handles/definition.
- Errata this arc: designer-vocabulary smuggling caught THREE times
  (Matt twice, the vacuousness check once) — the standing rule: schema
  derivation, annotation, and canonicalization must each be blind to
  the layer above; comparison to prior vocabularies happens only at
  analysis, as a finding.
STANDING FOR MATT: the new-dimension candidates' implications for the
INSTRUMENT (evaluation_unit especially — trajectory-class behaviours
are outside the node-relevance design entirely); the UA mint decision;
the prop-risk test. Fable spent this AFK drive: 0.
