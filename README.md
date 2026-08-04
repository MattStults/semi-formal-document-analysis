# Semi-formal document analysis

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
  *.py + test_*.py           tools and their suites (~1,960 tests)
  briefs/                    written contracts for every LLM judgment seat
  golden_*.json              hand-authored translation gold (Model Spec + constitution)
  snapshots/, dossiers/      the iteration loop's frozen states and adjudications
  audit_dossiers/            the disagreement census
  select_audit/              query-selection sweep instrument
  cycle.py, CYCLE_DESIGN.md  the fix-cycle orchestrator (state machine over artifacts)
```

⚠️ **Three different files are named `behaviours.json` and they are NOT
interchangeable** — see the warning in earlier revisions; loading the wrong one produces
a silently de-behaviourised score. Also: `*_dry-run` invocations of the annotation tools
write 0-atom stub artifacts to their default output paths — one such stub once silently
clobbered the shipped `behavior_atoms.json` (restored; guard pending).

## Running it

```bash
python -m venv .venv && .venv/bin/pip install -r semi-formal-experiment/requirements.txt
.venv/bin/python -m pytest semi-formal-experiment -q      # ~1,960 tests
```

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
