# CLAUDE.md — read this before acting in this repo

Semi-formal document analysis: a label-free tool that finds which clauses of a model
spec bear on a given behaviour. Most work happens in `semi-formal-experiment/`.

## Read in this order

1. **`semi-formal-experiment/HANDOFF.md`** — its ⭐⭐ top section only. Current state,
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
* **Model tiers:** frontier (Fable/K3/Qwen) for orchestration, design, and adversarial
  review; Opus for executing a written and reviewed plan; Haiku for validated judgment
  seats. Set the model explicitly on every subagent dispatch. Two items must NOT be
  started on an implementation tier: the **S3b redesign** and the **G-freeze artifact**
  (the latter defines a measurement we only get to run once).
* **Environment:** venv at
  `/Users/mattstults/Documents/ai_safety_projects/ai_character_index/semi-formal-experiment/.venv/bin/python`;
  run from `semi-formal-experiment/`. Budget ceiling $8.50, ~$2.15 spent — nearly all
  work here is deterministic re-analysis costing zero API dollars.

## What "done" looks like

A change is done when: predictions were frozen before measurement, every flip was
adjudicated against the document, an independent review passed, the decision is signed
with its grounds, and the cycle log has its line. Not when the score improved.
