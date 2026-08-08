# Pre-registration — restoring bad worked example #4 ("imports a name without its content")

**Written before any call. Frozen 2026-08-07.** Ruling: `DECISION_bad_worked_examples.md`.

## The change
`prompt/20_worked_example.md` gains bad example **#6**: a concept whose gloss restates its own
name (`terrorism_act` → "an act of terrorism"), the wrong form and the right one. Plus two
heading renames ("five bad" → "six bad"). Arms differ by **1,314 chars**, nothing else.

⚠️ **Both arms are pinned to git HEAD.** Another agent is editing `prompt/10_output_format.md`
right now; taking arm A from the working tree would have measured that edit too.

## Predictions ⭐ FROZEN
1. **`empty_gloss_rate` falls.** The direct target. Baseline: 10 of 133 concepts (7.5%) corpus-wide.
2. **`first_attempt_clean_rate` and `error_findings_per_clause` do NOT get worse.** This is the
   regression check Matt asked for; #6 teaches a *semantic* habit and should not move mechanical
   validity.
3. ⛔ **FALSIFIER:** if `empty_gloss_rate` does not fall, the example did not teach and should be
   reverted rather than kept because it reads well.

## What this cannot settle
- `empty_gloss_rate` is a **proxy**, and `DECISION_bad_worked_examples.md` refused it as a check for
  exactly that reason: `system_message` → "C is a system message" scores empty and is correct.
  Usable as a rate ACROSS arms (the primitives are the same in both), never as a verdict.
- A gloss can gain words and gain no content. This cannot see that; only stage 4 can.
- n = 6 clauses, 3 repeats, one model, temperature 0.2.
- Arm B's system block is 4% longer; length is not separated from content.

## Eval set
Fresh draw, salt `eval-heldout-v3`, 3 conditional + 3 definitional:
m0532, m0195, m0177, m0029, m0077, m0074 — excluding every clause ever sent (including eval raws),
held-out v1 and v2, and every clause id named in any prompt file or arm.
