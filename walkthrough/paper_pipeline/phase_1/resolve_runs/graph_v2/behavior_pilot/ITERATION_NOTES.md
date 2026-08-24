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
