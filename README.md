# Semi-formal document analysis

> **Agents and new contributors: start with [`AGENTS.md`](AGENTS.md).** It is the read
> order plus the short list of rules whose violation silently corrupts a result — the
> landmines are not obvious from the code, and several are contracts that *look* like
> bugs. (`CLAUDE.md` is a symlink to it, so Claude Code auto-loads the same content.
> Point any other tool's convention at the same file with a symlink, never a copy.)

Can a **semi-formal ontology** extracted from a model spec answer *"which passages of this
document bear on behaviour X?"* as well as a panel of frontier models — but instantly,
offline, and with an auditable reason for every answer?

Where it stands: **the label-free tool reaches +0.31 MCC against a +0.555 frontier-panel
bar** (dev cells, true universe) — and the more important products turned out to be the
measurement instruments and the iteration process around the tool. See
`semi-formal-experiment/HANDOFF.md` for state, `ITERATION_LOOP.md` for the loop and its
policy, `REPRODUCIBILITY.md` for the process rules, and `CYCLE_DESIGN.md` for the
orchestrator.

## The idea

Read the spec once. Segment it into clauses. Have a cheap model annotate each clause with
typed **atoms** — `situation`, `act`, `entity`, `value`, now carrying deontic force,
principal chains and condition/exception roles. A query then selects atoms for the
*behaviour* and matches structurally. No model call at query time, and every hit traces
back to a licensing span of source text.

## Results, in brief (2026-08-04)

Relevance (9 behaviours judged; 3 frontier dev cells quoted, true 589-passage universe):

| | MCC |
|---|---:|
| frontier judges — the bar | +0.555 |
| the tool, audited selection (dev) | **+0.309** |
| the tool, first shipped config | +0.28 |
| bag-of-words control | +0.19 |

Translation quality, against hand-authored golden sets with a **measured two-author
human ceiling** (names 0.29 / spans 0.79 / structure 0.91):

| axis | extractor | human ceiling |
|---|---:|---:|
| location (span F1) | 0.86 | 0.79 |
| structure (span+force/party/role) | 0.59 | 0.91 |

A 294-case causal census of every tool-vs-panel disagreement (Haiku-run, blind-validated
seats): ~63% matching precision, ~20% threshold calibration, ~15% vocabulary/naming,
~2% plumbing. A human-expert review of the panel product independently found the judges
**over-flag and flatten salience** — the bar itself is imperfect, and the endorsed use
case is ranked first-pass auditing, not judge replacement.

## Layout

```
data/                      panel judgements and behaviour definitions (the instrument)
specs/                     the documents under analysis
engine/                    vendored panel harness
semi-formal-experiment/    everything else:
  *.py + test_*.py           tools and their suites (2,156 tests, 2026-08-04)
  briefs/                    written contracts for every LLM judgment seat
  golden_*.json              hand-authored translation gold (Model Spec + constitution)
  snapshots/, dossiers/      the iteration loop's frozen states and adjudications
  audit_dossiers/            the disagreement census
  select_audit/              query-selection sweep instrument
  cycle.py, CYCLE_DESIGN.md  the fix-cycle orchestrator (state machine over artifacts)
```

⚠️ **Three different files are named `behaviours.json` and they are NOT
interchangeable** — `data/behaviours.json` (the panel roster), `engine/panel/behaviours.json`
(the vendored harness's own copy) and `site/spec-reader-test/data/behaviours.json` (the
reader prototype's). The experiment's query-side definitions are a FOURTH, differently
named file: `semi-formal-experiment/behaviours_query.json`. Loading the wrong one produces
a silently de-behaviourised score. (The earlier text here pointed at "the warning in
earlier revisions", which pointed nowhere.) Also, historically: `*_dry-run` invocations of the annotation tools
wrote 0-atom stub artifacts to their default output paths, and one such stub silently
clobbered the shipped `behavior_atoms.json` (restored). **The guard is no longer pending**
— as of 2026-08-04 (TOOLING_BATCH_DESIGN §4) a dry run writes to `<name>.dryrun.json`, and
no write, dry or live, may overwrite a non-stub artifact without `--force`.

## Running it

**There is no `requirements.txt`** (an earlier revision of this file told you to install
one). The dependency list is short enough to write out, and the venv the suite actually
runs under lives inside `semi-formal-experiment/`, not at the repo root:

```bash
python -m venv semi-formal-experiment/.venv
semi-formal-experiment/.venv/bin/pip install pytest clingo
semi-formal-experiment/.venv/bin/python -m pytest semi-formal-experiment -q
# 2,156 passed, 3 skipped (measured 2026-08-04 — counts drift; the command is the
# source of truth, not this number)
```

`clingo` is only needed for the parked ASP path (`emit_asp.py` and its tests). One
diagnostic module, `weight_diag.py`, additionally wants `numpy` + `scikit-learn` and
imports them lazily, so the suite passes without them. Provider calls go through stdlib
`urllib` — there is no vendor SDK to install. Most tools import each other by bare module
name, so **run them from inside `semi-formal-experiment/`** (pytest is the exception —
it can be pointed at the directory from the repo root, as above).

API keys are read from environment variables named in config; no key is stored here.
Every live run is billed against a hard budget (`spend.py`), preflighted, and logged.

## What this repo is really about

The negative results, the guards, and the process. Highlights of what was true at some
point and is not true now: a silently truncated evaluation universe; an error-rate "win"
that reversed under MCC; a supervised +0.59 "ceiling" that proved separability, not
semantics; a translation score of 0.21 measured against a naming axis where humans
themselves only reach 0.29. Every headline here was overturned at least once — always by
asking what an existing number actually measures — and the machinery that survives is
the part built in response: anti-cheat scans that have caught real planted leaks and
real agent mistakes, sha-frozen prompts and gold standards, blind two-coder protocols,
certified small-model judgment seats, and a cycle orchestrator whose gates exist because
every recorded operator error was an orchestration error.
