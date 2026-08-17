# DRAFTER BRIEF — slice 1, opus pair loop

All paths below are relative to
`/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/`.
Use ABSOLUTE paths in every tool call.

## What you are

You are the TRANSLATOR. You write one module for one clause. You are given the best
chance possible: the full production prompt contract, your clause's user block, and a
review list of measured failure classes. **The review list is an aid, not a capability
test.**

## ⛔ Fenced out — do not read, list, or search these, at any depth

* `_debug_gen11/reference_set/`
* `_debug_gen11/redraw_adjudication/`
* `_debug_gen11/spotcheck_semantic/`

Also do not read any other clause's finished module in `_debug_gen11/ds_opus_loop/out/`
or `_debug_gen11/translate_opus/out/` — those are other cohorts' answers.

## Read, in this order (this IS the production system prompt, concatenated in this order)

1. `prompt/00_task.md`
2. `prompt/10_output_format.md`
3. `resolve_runs/graph_v2/node_worked_example.md`
4. `prompt/30_failure_modes.md`

Then your clause's user block: `_debug_gen11/opus_pairs/slice1/spans/<CLAUSE_ID>.prompt_user.txt`

Then the review list: `_debug_gen11/translate_opus/REVIEW_LIST.md`

## Procedure

### Step 0 — SPAN ENUMERATION, before you draft anything

Write `_debug_gen11/opus_pairs/slice1/out/<CLAUSE_ID>.span_enumeration.md`:

* enumerate every distinct element of the NARROWED span, E1, E2, … — each with the exact
  substring it comes from;
* **N9: count the finite verbs in the narrowed text, and count the propositions
  `ESTABLISHES` demands.** If those numbers disagree, say so now — a mismatch is a scope
  conflict, and burning repair turns on it is a measured failure mode;
* **N3: diff `ESTABLISHES` against the narrowed span in BOTH directions** — what does
  ESTABLISHES add, and what does it drop?
* ⭐ **THE FRAME QUESTION, answered in words, before you draft:** *should this clause be
  translated at all?* `00_task.md` lists section-heading, states-a-goal, **is an example**,
  and not-expressible-as-rules as abstention triggers. Answer explicitly — "yes, translate,
  because it states the norm X" or "no, abstain, because …". A silent answer counts as
  unasked. If you abstain, the module is still written, with `outcome: "abstained"` (that
  exact string — the schema's `Literal` admits only `translated` and `abstained`) and an
  `abstain_reason`, and every content field forced empty.

### Step 1 — draft SPAN-FIRST

Draft the module from the span and the output contract. Do not consult the review list yet.
Save it as `_debug_gen11/opus_pairs/slice1/out/<CLAUSE_ID>.json`.

### Step 2 — TURN-BASED REVISION, four turns, grouped by lens

The list has 20 entries. An agent handed twenty checks applies none of them properly, so
you take them in four turns of five, grouped by LENS:

| turn | lens | entries |
|---|---|---|
| 1 | **Is the right content here at all?** | P2 · P3 · P6 · N2 · N3 |
| 2 | **Is the logical form right?** | P4 · P5 · P8 · N4 · N6 |
| 3 | **Is the force right?** | P1 · P7 · P10 · N5 · N7 |
| 4 | **Naming, grounding, hygiene, anti-rules** | P9 · N1 · N8 · N10 · the three ANTI-RULES |

⛔ **A TURN THAT CHANGES NOTHING IS THE EXPECTED OUTCOME, NOT A FAILED TURN.** An agent
that believes each turn must justify itself will edit a correct module until it is wrong.
Over-editing a correct module is worse than the overload the turns cure.

**Per entry, per turn, report three things: what you looked for, what you found, and what
you changed — including "nothing", explicitly.** A silent entry is treated as unchecked.

⭐ **Record `len(asserts)` at the start and end of EVERY turn.** A turn that reduces the
`asserts` count must justify the reduction in writing, naming which obligation left and
why the span does not carry it. Content deletion is invisible otherwise: a measured arm
deleted two of three obligations while its read-back still recited all three.

⛔ **Known trap.** A critic entry of the shape *"is every entry in `claims` actually
encoded — and can the rule that encodes it ever FIRE?"* has twice produced an identical
HARMFUL weakening on another clause. Its nearest analogues here are P3 and N1. If applying
either makes a rule fire by weakening what it says, that is the trap — record it and do
not follow it.

### Step 3 — final pass

Re-read your Step-0 span enumeration against the finished module. Anything in the
enumeration that reaches the module nowhere: say so.

## Outputs (write all three)

* `out/<CLAUSE_ID>.json` — the module, valid JSON, no markdown fence.
* `out/<CLAUSE_ID>.span_enumeration.md`
* `out/<CLAUSE_ID>.notes.md` — the turn-by-turn report, the asserts ledger, the frame
  answer, every UNSURE you could not settle.

## Validation

You may run:
`../../../semi-formal-experiment/.venv/bin/python` from the `phase_1/` directory, e.g.

```
/Users/mattstults/.../semi-formal-experiment/.venv/bin/python -c "..."
```

using `schema.validate_all(obj, clause_id)` and `checks.run_checks(...)`. The coordinator
re-derives this independently, so do not report a pass you did not run.

## Discipline

* **No git. No commits. No branch change.** Write ONLY inside
  `_debug_gen11/opus_pairs/slice1/`.
* Do not edit `REVIEW_LIST.md` — five slices run in parallel and the fold is one
  coordinated step afterwards.
* Report unsoftened. Anything you could not settle goes in the notes as UNSURE.
