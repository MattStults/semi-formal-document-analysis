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

$V version.py                                    # staleness census over runs/, free
$V version.py --rows                             # one line per (run, module)
$V translate.py --only-stale                     # translate only what has gone stale
$V translate.py --only-stale --waivers w.json    # …honouring a signed provenance waiver
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

⚠️ **`translate.py`'s module docstring and its end-of-run banner are STALE and say the opposite of
what the harness does.** Both still date from before stage 2 existed: the docstring opens *"Stage 1
has never been run"* and *"⛔ IT VALIDATES NOTHING ABOUT THE TRANSLATION… Stage 2 is those checks and
it is deliberately not built yet"*, and every run ends by printing *"⛔ NOTHING here has been
validated. No compile, no link, no read-back."* Since stage 2 became the unconditional gate, every
attempt is compiled by clingo, link-checked, rule-shape checked and cycle checked before anything is
written. Believe this file and the code, not those three strings, until they are corrected.
(`translate.py` is not a watched file, so nothing will catch it. Verified still present
2026-08-07: `translate.py:7`, `:10-14`, `:1225`.)

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

⛔ **This paragraph was false for the term it names, and the correction is worth reading.** "Each
repair turn resends the transcript" was the stated reason for the triangular growth, and the
transcript's largest component — the **prior completions**, up to `max_tokens` each, roughly 12× the
user block — was never billed as input on the next attempt. At the shipped `repair.max_attempts: 3`
the printed worst case came out **12.7 % below** the true worst case (7.0 % at 2, 17.5 % at 4,
21.4 % at 5), i.e. anti-conservative, in the one direction `config.json`'s own comment says must
never be wrong. `estimate_cost` now adds `(k−1) × max_tokens` of carried-forward completion to
attempt *k*'s input, and `test_cost_and_summary.py` prices a repair sequence attempt by attempt and
asserts the estimate is never below it.

⚠️ The estimate still **over**-charges the full user block on every repair turn (the loop actually
re-sends only an error log). That is left in deliberately, and the two errors must not be netted off
against each other: high is survivable, low is not.

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
  m0255.version.json         its two version hashes — what it was made from
  m0255.lp                   the rendering of it (with the version as a % comment)
  m0255.transcript.json      every repair turn, ending in what the model last said
  concepts.json              the concept table for the whole run, as data
  run.json                   config + prompt shas, the response_format sent,
                             per-clause status, attempts, findings, licence counts, spend
```

`run.json`'s `status` is one of `translated` · `abstained` · **`abstained_under_repair`** ·
`unrepaired` · `error`. `unrepaired` means the repair loop was exhausted with findings still
standing; those findings are written out beside it as `surviving_findings`.

⭐ **`abstained_under_repair` is a distinct status and this list used to omit it**, which is exactly
how it also went missing from the run summary's arithmetic — for a while a clause the model refused
*after being told twice that it was wrong* was printed as a successful **translation**. A
first-attempt abstention is a real answer; one produced under repair pressure is not, and counted
together a model can abstain its way out of the hard clauses while the rate reads ordinary. The
summary now counts `translated` by name, prints the two abstention kinds separately, and says so
loudly if any status it does not partition on appears — so the next status added is loud rather than
silently absorbed into the most flattering bucket.

`run.json` is rewritten after **every** clause, not at the end, so an interrupt or a network drop
never loses the record of clauses already paid for.

## Artifact versioning — when a module is translated again

Every translated module is stamped with two hashes of the state that produced it, and the stamp is
what decides whether it runs again. `03_pipeline.md` §1 carries the ruling (Matt, 2026-08-08) and
the alternatives rejected; `version.py` carries the implementation and the reasoning per function.
The short form:

| hash | covers | a change means |
|---|---|---|
| `contract_hash` | clause text + `schema.py` | the artifact **may no longer validate** |
| `provenance_hash` | the system prompt + model + `max_tokens`, `format_forcing`, `max_attempts` | it is **not reproducible** from today's inputs, but is still valid |

**Both trigger a re-run**, and they stay separate anyway: a provenance-stale module still compiles
and links — it just cannot be cited as evidence about the current prompt. `version.py` classifies
every stored module as `current` · `provenance-stale` · `contract-stale` · `unstamped` · 
`no-longer-in-corpus`, and when both hashes moved the state is `contract-stale`, because that is the
one a waiver may never excuse.

The stamp is written **beside** the module (`<clause>.version.json`) and mirrored into `run.json`;
the `.lp` gets it as a `%` comment. It is deliberately not a field of the module object: the object
is a contract the *model* satisfies, and provenance is a fact about the run, not a claim the
translation makes about itself.

```bash
$V version.py                     # census over runs/ — free, sends nothing
$V translate.py --only-stale      # translate only the stale part of a selection
```

⛔ `--only-stale` is **off by default** — changing what a bare run translates is a spend change —
and it prints the census, by class and with its denominator, **above** the cost line, so a run that
is about to re-translate 593 clauses says so before it is priced.

**The waiver** (`--waivers path`) is the intention flag: a reviewed file naming clauses whose
*provenance* change does not oblige a re-run, carrying `who`, `date`, `why`, and the exact hash
transition it excuses — so it expires by construction the next time the prompt moves. It enumerates
clause ids (no wildcard), it can never excuse a `contract_hash` change (it refuses the run instead
of silently not applying), it cannot excuse an `unstamped` artifact, it is inert without
`--only-stale`, and a waiver that matched nothing is reported **unused** rather than passed over.

`mutate_version.py` sweeps all of it — the classification, the waiver rules, the two hash functions
and the wiring in `translate.py` — at 34 mutants, 0 survivors.

## Known unpinned edges

These are true today (re-verified 2026-08-07), cheap, and recorded so nobody rediscovers them:

- **`cross_references.max_clauses_per_target` is observed by no test.** Its only occurrence outside
  `config.json` is `translate.py:224`. It changes what is sent and what is billed.
- **`CorpusError("selection matched no clauses (kinds=…)")` misdiagnoses** (`translate.py:180`).
  After the empty-selection branch has already raised, the only way to reach it is a section+kind
  intersection — so it blames `kinds` for an intersection failure. Untested.
- **`resolve_provider` prepends the `providers.json` directory to `sys.path` permanently**
  (`translate.py:449`), ahead of `phase_1/`, and that directory (`semi-formal-experiment/`) contains
  its own `translate.py`. Nothing imports `translate` after that today; it is one filename away from
  a very confusing bug.
- **`self_test`'s `_StubClient` has no `complete_messages`** (`translate.py:1711-1722`). Stage 2 is
  now unconditional, so a stub that ever returns a repairable failure will die with `AttributeError`
  instead of a named refusal. More consequential now than when it was written.
- **The repair default disagrees three ways:** `run()` falls back to `1` (`translate.py:968`),
  `repair_loop`'s signature says `3` (`:2207`), `config.json` ships `3`. The severe half is fixed —
  `max_attempts=1` no longer disables stage 2, because `repair_loop` runs the checks once regardless.
