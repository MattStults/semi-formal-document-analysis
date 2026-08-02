# Semi-formal document analysis

Can a **semi-formal ontology** extracted from a model spec answer *"which passages of this
document bear on behaviour X?"* as well as a panel of frontier models — but instantly,
offline, and with an auditable reason for every answer?

Short answer so far: **it gets about halfway, and the binding constraint turned out not to
be the ontology.** See `semi-formal-experiment/HANDOFF.md` for state and results, and
`semi-formal-experiment/LADDER_PLAN.md` for the current plan and its amendments.

## The idea

Read the spec once. Segment it into clauses. Have a cheap model annotate each clause with
typed **atoms** — `situation`, `act`, `entity`, `value`. A query then annotates the
*behaviour* from the same vocabulary and matches structurally. No model call at query
time, and every hit traces back to a licensing span of source text.

## Results, in one table

Matthews correlation, 9 behaviours, true 589-passage universe:

| | MCC |
|---|---:|
| frontier judges — the bar | +0.555 |
| best query | +0.28 – 0.32 |
| bag-of-words control | +0.19 |
| chance | 0.00 |

## Layout

```
data/                      panel judgements and behaviour definitions
  behaviours.json            THE BAR — the panel WITH citations (377/333/153)
  behaviour-definitions.json 11-entry label/definition file
  panel-coverage.json        9 behaviours x 2 specs, small-model panel
specs/                     the documents under analysis (OpenAI Model Spec,
                           Anthropic constitution)
engine/                    vendored panel harness the reconstruction depends on
site/spec-reader-test/     behaviour metadata for panel v2
semi-formal-experiment/    all code, tests and result artifacts
```

⚠️ **Three different files are named `behaviours.json` and they are NOT
interchangeable.** `data/behaviours.json` is the panel with citations;
`data/behaviour-definitions.json` is the 11-entry definition file;
`site/spec-reader-test/data/behaviours.json` is panel-v2 metadata. Loading the wrong one
produces empty queries and a silently de-behaviourised score rather than an error.

## Running it

```bash
python -m venv .venv && .venv/bin/pip install -r semi-formal-experiment/requirements.txt
.venv/bin/python -m pytest semi-formal-experiment -q      # 1446 passed, 3 skipped
```

API keys are read from environment variables named in `data/panel-config.json`. No key is
ever stored in this repo. Every live run is billed against a hard budget tracked by
`semi-formal-experiment/spend.py`; `--dry-run` and `preflight()` exist so nothing spends by
accident.

## What this repo is really about

More of the value here is in the **negative results and the guards** than in the headline.
A partial list of things that were true at some point and are not true now:

- The evaluation universe was silently truncated — every published number was ~2× too
  generous — until `panel_universe.py` reconstructed it.
- A query operator selected on 3 behaviours *lost* at 9, at nearly 3× its declared
  selection-bias bound. It shipped as the default for three cycles anyway.
- A planted reference leak scored far *better* than the honest tool while 1,000+ tests
  stayed green. Twice.
- An elaborate six-rung experiment was designed, built and then withdrawn once it was
  costed and powered properly.

Hence: `test_no_reference_leak.py` (static + dynamic anti-cheat), `test_quality_floor.py`
(floors *and* a leak ceiling), pre-registered predictions recorded before runs, and a
standing rule that any spend-touching code gets an independent clean-context review before
its first paid launch.

## Provenance

Extracted from a shared research repo (`ai_character_index`). The panel judgements,
specs, and the vendored `engine/` harness originate there and in `ai_character_index-mvp`;
this repo carries copies so it runs standalone. Absolute paths into those checkouts have
been rewritten to repo-relative ones — the suite passes identically before and after, which
is what verifies the move.
