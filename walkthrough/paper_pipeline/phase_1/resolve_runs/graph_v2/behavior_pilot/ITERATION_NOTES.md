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
