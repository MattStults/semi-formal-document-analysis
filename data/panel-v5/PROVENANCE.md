# panel-v5 — frontier-LLM panel bench (collaborator data, ingested 2026-08-21)

## Source (pinned, will not drift)
Repository: github.com/AndresCotton/ai-character-index
Commit: ef08e676dc206f83d2da548b082084aa5c806bfa
Extracted via `git show` from the local clone of that repo; every file here was
verified byte-identical to the pinned commit's blob (git hash-object equality).
Shared by the collaborator (Andres) 2026-08-21 with the description: "the v5 panel
bench — the frontier-LLM panel scoring every passage of both specs against each
behaviour of the index."

## Files
- runlog-v5.jsonl — 31,293 rows, one JSON object per line:
  {behaviour, spec, model, locator, verdict, + parsed/relevant/rubric/via}.
  9 behaviour slugs; specs = model-spec (17,081 rows) + constitution (14,212).
  A 10th behaviour ("General welfare impacts, strict reading") has no rows of its
  own: it is DEFINED as the general-welfare verdicts restricted to what both specs
  share (collaborator's note).
- rubric-v5.txt — the rubric prompt the judges ran under. Verdict semantics:
  3 = DEFINING, 2 = CORE, 1 = ADJACENT, 0 = neither.
- behaviour-definitions-v5.json — what each behaviour slug was defined as for the
  judges (engine/panel/behaviours.json at the pinned commit).
- panel-config-v5.json — full seat/model configuration at the pinned commit.
- report-v5.html — the collaborator's rendered analysis (open locally).

## Seats ("model" column tags)
sol = gpt-5.6-sol, fable = claude-fable-5, deepseek = DeepSeek-V3.2 — FULL seats
(8,667 rows each; all 9 behaviours x both specs). glm = glm-5.2, deepseek-v4 =
deepseek-v4-pro-0813 (2,085 rows each), qwen38-max = qwen3.8-max (1,122 rows) —
PARTIAL seats.

## Measured coverage for the campaign's generalization behaviours
harmlessness-to-user: 2,889 rows (963 passages x 3 full seats).
objectivity: 2,889 rows (963 passages x 3 full seats).

## USAGE RULE (campaign mandate, Matt 2026-08-21)
This data enters the campaign ONLY as a pre-declared COMPARISON layer — panel
agreement statistics reported alongside adjudicated results. It NEVER serves as
truth: truth remains blind Fable adjudication per the fresh-draw protocol
(labels direct ATTENTION, never TRUTH). The generalization pre-registration must
name the exact comparison statistics before this file is read against any
instrument output. Note the seat composition differs from the v3w frontier trio
(sol/fable/kimi): any writeup citing "frontier panel" must say which panel.

## Not ingested
reader-test-coverage.json (Slack link, same message) sits behind the Constellation
Slack sign-in and could not be fetched by the agent; Matt holds it. Its name
suggests a reader-test artifact, not panel verdicts — ingest separately if needed.
