# Readback smoke test on graph-node modules (2026-08-12)

First run of the step-4 readback stages over graph-node translations, per the
gap map in `STEPS34_READINESS.md`. Three modules from the merged node corpus
(27 modules across `translation_sample/runs/`, newest-run-wins; the three
richest by asserts+requires): `l1_170_n016`, `l1368_1541_n011`,
`l1799_1973_n013`. Harness scripts (not committed): scratchpad
`smoke_readback.py` (free stages) and `smoke_seat.py` (dry-run + one live
call). Total spend: **$0.0004** (two seat calls at ~$0.0002; cap was $0.05).

## Stage outcomes

### 1. probe.probe_clause (stage 3, free) — WORKED, nothing synthesized

All three modules: `outcome=passed`, full discrimination coverage, no caps
hit.

| module | signature | ground atoms | coherent | covering | notes |
|---|---|---|---|---|---|
| l1_170_n016 | 4 preds | 4 | 16/16 | 5 | 4/4 rules covered |
| l1368_1541_n011 | 5 preds | 2 | 4/4 | 3 | 1/1 rule covered; 3× requires-unsatisfied (note) |
| l1799_1973_n013 | 7 preds | 5 | 32/32 | 7 | 3/3 rules covered; 2× requires-unsatisfied (note) |

* Link scope per module came from `link_nodes.requires_resolution` — **empty
  for all three** (every `requires` dangles in-corpus), so the Q-22 path
  (unsatisfied `requires` joins the situation signature) carried the load and
  worked: the dangling names were enumerated and the `requires-unsatisfied`
  note fired, severity `note`, exactly as designed.
* The merged concept table (`link_nodes.merged_concepts`, 121 rows) plugs
  straight into `probe_clause(…, concepts=rows)` — the row shape
  (`concept: name/arity`, `gloss`) is what probe already reads. No adapter.
* The gap-3 fear (no stage-3 artifact can exist for nodes) is dissolved for
  covered modules: `ProbeReport.covering` materializes on demand, free.

### 2. readback_r3.render_r3 (stage 4b-R3, free) — WORKED, nothing synthesized

Called as `render_r3(mod, rep.covering, extra_gloss=gloss_from_rows(merged),
link_texts=[])`, `mod` rebuilt via `schema.validate(node_json)` (the stored
node `.json` validates unchanged — `outcome`/`abstain_reason` keys included).

| module | outcome | derivations | error classes |
|---|---|---|---|
| l1_170_n016 | `rendered` | 4 of 5 | none (4× note `readback-act-literal`) |
| l1368_1541_n011 | `rendered` | 1 of 3 | none (1× note `readback-act-literal`) |
| l1799_1973_n013 | `readback-ungloss` | 1 of 7 | 2× ERROR `readback-ungloss` |

* xclingo ran clean; trees parsed; leaves glossed from the merged table.
  Layer-1 fraction 0.00 everywhere (all layer-2 fluent) — fine.
* The n013 block is a **real translation defect surfaced correctly, not an
  integration failure**: the module declares inputs `instruction_from_level/2`
  and `higher_than/2` with no concept rows anywhere (its own `concepts` list
  omits them), so the derivation leaves have no written meaning. Stage 2
  evidently does not require inputs to be glossed; R3 is the first stage that
  refuses. Working as designed.
* The `#const onto = on.` collision never arose here because link scopes were
  empty; a future run with non-empty `link_texts` must dedupe via
  `link.dedupe_shared_preamble` (readiness gap 1's fix) AND strip the link
  modules' own `%!show_trace` directives before handing them to xclingo —
  untested in this smoke.

### 3. seats.judge 4b, live, one call (paid: $0.0004 incl. retry) — RAN,
### reply competent, adjudication REFUSED: live prompt/denominator id mismatch

* Path: `readback.render_module(mod, extra_gloss=merged, clause_quote=…)` →
  `rendered` (6 renderings, echo 0.36, evidential) →
  `seats.denominator_4b` → `seats.build_4b_prompt` → `seats.judge("4b", …)`.
  Module: `l1368_1541_n011`.
* Provider: the stage hardcodes nothing (`seats.py` is offline by design;
  `judge` demands a `client_factory` seam). Factory was built from
  `config_graph_nodes.json` → together-DeepSeek (`DeepSeek-V4-Flash-0731`),
  i.e. the stage's own config. No STOP condition met.
* **Finding (new, live-path): `seats.NotAdjudicated` — the seat cannot name
  the denominator.** `build_4b_prompt` shows the sentences as `0.`, `1.`, …
  and the `_ANSWER` brief says `"item": "..."` with no id list; the
  denominator ids are `concepts[0]`…`asserts[0]`. The seat echoed the
  numbered sentence text as `item`, and `validate_judgements` refused every
  row. Every existing test passes because the mock replies are written with
  the internal ids the live seat is never shown. The reply itself covered all
  6 items exactly once, in order, with reasons — the model is not the
  problem.
* Substance of the (unadjudicated) reply, for the record: items 0–2
  (cross-node concept glosses) `unclear` — the seat rightly notes the
  narrowed node span doesn't define them (that is readiness gap 2 showing up
  as seat behaviour); item 3 `faithful`; items 4–5 `unfaithful` — the seat
  read the gloss "the transformation exception would permit producing M under
  policy P" as contradicting the clause. A real faithfulness question about
  that gloss's polarity, worth a look if this module ever ships.

## What was synthesized (all documented, none touched repo files)

1. **clause_text** — `node_corpus.json`'s `quote` is the packed prompt
   (readiness gap 4); the seat/RB4 text was extracted from its
   `[node narrows this span to: "…"]` bracket.
2. **Seat client factory** — `translate.resolve_provider` + `translate.Client`
   over `config_graph_nodes.json`, with `format_forcing` switched
   `json_schema → json_object` (the config's json_schema is the stage-1
   MODULE schema; forcing it on a seat reply would mangle it) and
   `max_tokens → seats.SEAT_MAX_TOKENS` (4096).
3. **Envelope adapter** — `translate.Client.complete_messages` returns an
   envelope dict; `seats.judge` expects raw text. Three-line wrapper.
4. **sys.path order** — `semi-formal-experiment/` must go LAST:
   its `translate.py` shadows phase_1's (bit once, loudly).

## Integration gaps before full step-4 on nodes, ranked

1. **Seat item-id disclosure (NEW, blocks every live seat).** The live prompts
   never show the seat the ids `validate_judgements` demands. Fix is small
   and mechanical: enumerate prompt items by denominator id (or have the
   brief define `item` as the shown index and map positionally in `judge`).
   Until fixed, all four seats are live-unrunnable against their own
   adjudicator — on any corpus, not just nodes.
2. **Client seam for seats** (syntheses 2–3 above): no stage-owned factory
   exists; a ~15-line blessed factory (json_object forcing, SEAT_MAX_TOKENS,
   envelope→text) is needed somewhere config-driven.
3. **Clause text for nodes** (readiness gap 4, confirmed live): the packed
   `quote` must not reach RB4/seats; the narrowed-span extraction works and
   should be promoted into the node corpus row (or read off `locator`).
4. **Cross-node gloss context for seats** (readiness gap 2, now with live
   evidence): with only the node span as clause text, the seat returns
   `unclear` on every borrowed concept gloss. Cross-reference texts (the
   provider nodes' spans) need to ride along once providers are translated.
5. **Link-scope hygiene for R3** (untested here): shared-preamble dedup plus
   `%!show_trace` stripping when `link_texts` is non-empty.
6. **Inputs without glosses** (translation-side, surfaced by R3): stage 2
   accepts inputs no concept row defines; R3 then blocks (n013). Either
   stage 2 warns, or this stays a known stage-4 refusal class.

## Verdict

**A-few-fixes-away, not architecturally blocked.** The deterministic pipeline
(probe → covering set → R3 with merged-table glosses) runs end-to-end on node
modules today with zero code changes and zero synthesis. The one hard blocker
— seat item-id disclosure — is a prompt/adjudication mismatch in `seats.py`
itself, unrelated to node modules, and is a one-function fix. Everything else
is plumbing already mapped by `STEPS34_READINESS.md`.
