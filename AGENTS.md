# AGENTS.md — read this before acting in this repo

Semi-formal document analysis: a label-free tool that finds which clauses of a model
spec bear on a given behaviour. Most work happens in `semi-formal-experiment/`.

> **This file is the single canonical brief for every AI agent and every new human
> contributor.** `CLAUDE.md` is a **symlink to this file**, so Claude Code auto-loads
> the same content other tools read from `AGENTS.md`. If your tool looks for a
> different filename (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules`),
> **add another symlink to this file** — never a copy. Two copies drift, and a stale
> agent brief is worse than none. (Windows without symlink support: enable
> `git config core.symlinks true`, or read this file directly.)

## Read in this order

1. **`semi-formal-experiment/HANDOFF.md`** — its top starred section only. Current state,
   what is closed, what is parked, and the standing rulings. Everything below that
   section is history (self-marked, some superseded).
2. **`semi-formal-experiment/CYCLE_DESIGN.md`** — how a change cycle runs. Read the
   BINDING AMENDMENTS, ⚠️ PRE-BUILT CYCLES, and ⚠️ CYCLE CEREMONY MECHANICS.
3. **`semi-formal-experiment/MODULE_MAP.md`** — §0 (how to run anything), §1b (what each
   module is), **§11 (anti-rules — read before "fixing" anything that looks wrong)**.
4. **`semi-formal-experiment/REPRODUCIBILITY.md`** — the sandwich rule, new-constant
   governance, determinism.
5. **`semi-formal-experiment/briefs/<seat>.md`** — before dispatching any judgment seat.

## Things that will silently corrupt a result if you don't know them

* **Never lower a quality floor to make a run pass.** A real gain raises it in the same
  commit, with the measurement. Scoring far *above* a floor is a **leak signature**, not
  a win (`ITERATION_LOOP.md`, anti-cheat perimeter).
* **A cycle's own design document is never seat material.** Design docs pre-register
  expected outcomes; handing one to an adjudication seat destroys the judgment. Same for
  `PORTFOLIO_REVIEW.md`, prior `flip_verdicts*.json`, and the census.
* **Never pin an exact count of a live artifact** in a test (`n == 109`, `692
  candidates`). Pin a frozen input plus a subset check — a cycle that legitimately grows
  the artifact will otherwise fail its own gate. This has bitten twice.
* **Registration, not documentation, fences a module.** New query-side module →
  `test_no_reference_leak.QUERY_MODULES`; new panel-reading module → `FORBIDDEN`; new
  test → `conftest._OPTIONAL`. Same diff, every time.
* **Labels direct ATTENTION, never TRUTH.** A change may be *motivated* by a panel
  disagreement, but it is kept or reverted on its complete flip set, adjudicated against
  the document, with label values nowhere in the room.
* **Check `MODULE_MAP.md` §11 before "cleaning up"** anything that looks like a bug.
  Six known cases are contracts, not defects.

## Working rules

* **The driver never runs git.** `cycle.py` drafts `commit_message.txt` and
  `staging_list.txt` at CLOSE; a human/coordinator stages and commits. Staging usually
  needs more than the list — check `git status` against it.
* **Always pass `--cycle NAME`** to `cycle.py`; a directory holding only drafts counts
  as open, so the bare command gets refused.
* **Every cycle gets a clean-context adversarial review before close, and a positive
  review stops everything until it is fixed.** This has fired twice and was right both
  times.
* **Rulings go in the repo, not the transcript.** A decision that resolves an open
  design question must be written into the cycle record with its grounds, and any
  tempting alternative rejected **by name**. Transcript-only procedure is a review
  finding (`REPRODUCIBILITY.md`).
* **Match the model tier to the work, and say which you used.** Strongest available model
  for orchestration, design, and adversarial review; a mid tier for executing a written
  and reviewed plan; a small model for validated judgment seats — the adjudication seat
  is proven at small-model/frontier parity, and **divergence from a frontier model on the
  same brief is a seat defect, not a model failure**. Set the model explicitly on every
  subagent dispatch rather than inheriting. Design work must not be pushed forward on an
  implementation tier (currently: the S3b redesign, and the G-freeze artifact — which
  defines a measurement that can only be run once).

## Environment

```bash
# from the repo root
python3 -m venv semi-formal-experiment/.venv
semi-formal-experiment/.venv/bin/pip install pytest clingo
cd semi-formal-experiment && .venv/bin/python -m pytest -q      # ~2,270 pass, ~8 min
```

`clingo` is only needed for the ASP-solver tests; everything else runs without it (those
tests will show as collection errors, which is a known environment gap, not a failure).
Run from `semi-formal-experiment/` — several commands take relative path arguments.
Provider calls use stdlib `urllib`, no vendor SDK. `numpy`/`scikit-learn` are imported
lazily by `weight_diag.py` only.

**API spend:** this project has a hard budget ceiling and it is `spend.py:BUDGET` — the ONE
ceiling the machine reads (the authorization history is in the
constant's comment, and `spend.py` reports the current figure — quote the constant, never a
second number). Nearly all work — every cycle, every audit, every number in the
writeups — is deterministic re-analysis of data already on disk and costs nothing. If you
find yourself about to spend, check that the question genuinely needs a new model call.

## What "done" looks like

A change is done when: predictions were frozen before measurement, every flip was
adjudicated against the document, an independent review passed, the decision is signed
with its grounds, and the cycle log has its line. **Not when the score improved.**

If you are new here and want the shortest statement of why the process looks like this:
a change that improved the aggregate metric was reverted because per-flip adjudication
found it had deleted the spec's guidance on de-escalating a user's radicalization. The
metric said ship it. See `cycles/patient-pricing-2026-08-04/decision.json`.
