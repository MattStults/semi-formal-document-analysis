# phase_1 — the stage 1 + stage 2 harness

**The one question:** can a model produce a logic module for a specification clause in the form
`resources/03_pipeline.md` describes — and, when it cannot, can it be told what is wrong and fix it?

```bash
# from anywhere; paths in config.json are relative to this directory
V=../../../semi-formal-experiment/.venv/bin/python

$V translate.py --self-test                      # 53 checks, no network, no cost
$V translate.py                                  # DRY RUN — selection + cost, sends nothing
$V translate.py --clause m0255 --show-prompt     # see exactly what would be sent
$V translate.py --section definitions --kinds definitional --limit 4
$V translate.py --list-models                    # GET /models, free, verifies the model id
$V translate.py --write-artifact                 # regenerate dryrun.txt from the current inputs
$V translate.py --live                           # needs authorisation
```

Exit codes: `0` clean · `1` a clause failed · `2` usage/config error.

## What a run does

One clause at a time, and each clause runs the same three steps:

1. **Ask.** A system block assembled from `prompt/*.md` — byte-identical for every clause in a run,
   so it is the cacheable prefix — plus a user block holding the clause text and the text of every
   clause it cross-references.
2. **Check.** `checks.py` runs every deterministic check there is over the answer: the schema
   contract in `schema.py`, and the link/shape/cycle checks in `walkthrough/link.py`. One call, one
   complete findings list — not one defect per round trip.
3. **Repair.** Any `error`-severity finding sends the answer back, in a single accumulating
   transcript carrying the model's own earlier attempts and every check they failed, with reasons.
   `repair.max_attempts` in `config.json` bounds it; `1` disables repair.

The output is a **JSON object**, not raw ASP. `schema.py` validates it and renders the `.lp`; the
object is the record and the `.lp` is a rendering of it.

## What it checks, and what it still does not

**Checked, deterministically, before a module is ever written:** the schema contract (every field,
every read-back, every licence obligation), that the module did not rename itself, that it cites no
clause id the corpus does not have, that it compiles under clingo, that every referenced predicate
is declared, rule-shape bans, closure declarations, concept-table membership, and that the `beats`
relation is acyclic.

⛔ **None of that judges the translation.** Whether the module for clause `m0091` says what clause
`m0091` says needs a reader, and that is stage 4. A clean run means "the answer satisfies every
mechanical contract we can state", never "the translation is right".

**Two severities, and only one drives repair.** `error` sends the answer back; `note` is reported,
counted, and inert. Some notes are true of a *correct* module — `requires-unprovided` fires on
every well-formed single-clause module, because a `%% requires:` predicate is head-less by design.
A loop driven by notes would not converge on a better translation; it would converge on teaching
the model to move predicates from `requires` into `inputs` until nothing fires. `checks.py`'s
module docstring carries the full ruling.

## The output contract

Each module declares, per fact:

| | |
|---|---|
| **licence** | exactly one of `textual` · `assumed` · `world` |
| `textual` | must carry `cites` naming a real clause id |
| `assumed` | must name the `inference` it rests on |
| `world` | must be marked `toggleable` — a result resting on a world fact must be switchable off |

Validated, not merely requested: `schema.py` raises on a `textual` fact with no citation, on an
`assumed` fact with no named inference, on a `world` fact that is not toggleable, and on a
non-`world` fact that is. The rendered `.lp` carries the licence in a trailing comment on every
line (`[T]` / `[A]` / `[W] toggleable`).

The normative layer uses a **fixed vocabulary** — `asserts/3`, `beats/3`, `defines/3` — so that
independently translated clauses link. Names are invented only in the `ontology` block, and every
one must also appear in `concepts` with a gloss.

## Format forcing

The request carries `response_format: {"type": "json_schema", "json_schema": {...}}`, built from
`schema.json_schema()` — flat, strict, no `$ref`, because several providers do not resolve one.
`model.format_forcing` selects `json_schema` (default) · `json_object` · `none`, and
`model.json_schema_strict` controls the `strict` key. `run.json` records the exact payload sent.

⚠️ A fenced block is still tolerated on the way in — some providers wrap JSON even under forcing —
but nothing else is guessed at. Anything that does not parse as an object is a refusal.

## What it refuses to do

A harness whose "pass" state is indistinguishable from its "did not run" state is broken by design,
and this project has shipped that three times. Every one of these raises and writes no module:

| condition | error |
|---|---|
| a clause id or section id that does not exist | `CorpusError` — a typo must not translate something else |
| nothing selected | `CorpusError` — "translate everything" is not an accident |
| a prompt file missing, or empty | `ConfigError` — a promptless call looks completely normal |
| a `prompt/*.md` that is neither sent nor listed as unused | `ConfigError` — an orphan prompt file is this failure in prompt form; it happened once |
| an unknown provider name | `ConfigError` — must not fall through to a default model |
| no API key | `ProviderError` |
| `finish_reason=length` | `ProviderError` — a truncated module can be syntactically fine and semantically half a clause |
| an empty response | `ProviderError` |
| a response that is not a JSON object, or fails the schema | `ResponseParseError` |
| estimated cost over the ceiling, or an unpriced provider | `CostGateError`, before anything is sent |

⚠️ **The truncation guard cannot fire on the configured model.** together.ai returns
`finish_reason: null` for it, verified across live calls. A cut-off completion therefore surfaces
one step later as a JSON parse failure — still loud, still a refusal, but reported as "the provider
ignored `response_format`" when the real cause was length. A self-test pins the null case.

The **raw response is written before any parsing**, and the user block is written **before the
call**, so a clause that fails still has both halves of its exchange on disk.

## The four things you can work on independently

| | where |
|---|---|
| **the translation rules** | `prompt/00_task.md` — the rules, the licence obligations, the abstention route |
| **the output format** | `prompt/10_output_format.md` — the fixed vocabulary, the fields, read-backs, closure, abstention |
| **the worked examples** | `prompt/20_worked_example.md` — one good module, one definitional contrast, five bad ones |
| **the failure modes** | `prompt/30_failure_modes.md` — the 17, grouped by whether a single-clause translator can even see them |
| **model / API / selection / cost** | `config.json`, or CLI flags which override individual keys |

Nothing about the provider, the corpus or the prompt is in `translate.py`. `--config` points
somewhere else entirely, and `prompt.system_files` fixes the concatenation order.

## Design notes

**Prompt order is fixed-block-first.** The `prompt/*.md` files are concatenated into the system
block; the clause text and its cross-references go last, per `03_pipeline.md` stage 1. Currently
27,754 chars from 4 files.

**Cross-references come from the document's own markdown anchors** — `[restricted](#restricted_content)`
— matched against `section_id`. ⚠️ **This is a lower bound.** Only ~13% of clauses carry anchors, so
a clause showing "no anchors" is not thereby dependency-free; `03_pipeline.md` records finding the
rest as open. Turn it off with `cross_references.enabled: false` to measure what it is worth.

**Repair prompts carry the real first user block, not a summary of it.** A synthesised stub dropped
the cross-referenced clause texts — which stage 1 calls load-bearing — so repair ran without the
definitions, and the stored transcript was a fiction of the exchange rather than a record of it.

**Findings carry no suggested fix and no expected value.** Stage 1 is denied the expected verdicts;
a `fix=` field would put the answer into the prompt that is supposed to produce it. Every finding
must also name its `origin`, and the rendered repair log admits stage-2 origins only — stages 3 and
4 carry expected answers, and the marker is what keeps them out.

**Two repair pathologies are watched rather than assumed away.** `flags` records `shrank` when a
repair returns fewer translation items than it started with, and `declaration-edit` when a repair
changed only `requires`/`inputs`/`acts`/`closure`/`forbid_body` — the cheap way to clear a finding
is to bend a declaration until the check stops firing. `unclear_closure_rate` records the same risk
for closure: answering `unclear` everywhere is legal, goes green, and restores the silent default
the declaration exists to replace.

**An abstention is terminal, and not argued with.** A model that says it cannot translate the
clause faithfully is not re-prompted — re-prompting produces exactly what abstention prevents.

**Live runs go through `providers.py` `LiveClient`** when it is importable, so usage lands in
`usage.jsonl`. There is a stdlib fallback that needs no repo import.

**Cost is estimated worst-case** — every call billed at the full `max_tokens`, and triangular in the
attempt count because each repair turn resends the transcript — because on a reasoning model the
hidden reasoning is billed as output and dominates. Overstating is survivable; understating is how
a hard cap gets passed. The gate refuses before anything is sent.

⚠️ **This harness's spend is invisible to `spend.py`.** The configured provider is defined inline in
`config.json` rather than in `providers.json`, and `spend.py` prices only from the latter, so these
rows are logged and then dropped from the total. Every run prints the residue rather than swallowing
it, and `run.json` records `visible_to_spend_py: false` with the reason. Repo ledger: **$2.06 of
$8.50**; this directory has spent a further **$0.021** across 17 calls that the ledger does not see.

**Caching is unpriced for this provider.** together.ai lists a cached-input rate for it, but the
estimate bills every input token at the full rate — the conservative direction, which is what a hard
cap deserves.

## Output of a run

One directory per run under `runs/`. A run never writes into an existing directory: the raw
responses of a run that cost money are the one thing that cannot be regenerated.

```
runs/<timestamp>-<provider>/
  prompt_system.txt          the system block, once — identical for every clause
  m0255.prompt_user.txt      written BEFORE the call
  m0255.raw.txt              the complete response, written first, always
  m0255.json                 the validated module object — the record
  m0255.lp                   the rendering of it
  m0255.transcript.json      every repair turn, ending in what the model last said
  concepts.json              the concept table for the whole run, as data
  run.json                   config + prompt shas, the response_format sent,
                             per-clause status, attempts, findings, licence counts, spend
```

`run.json`'s `status` is one of `translated` · `abstained` · `unrepaired` · `error`.
`unrepaired` means the repair loop was exhausted with findings still standing; those findings are
written out beside it as `surviving_findings`.

`run.json` is rewritten after **every** clause, not at the end, so an interrupt or a network drop
never loses the record of clauses already paid for.
