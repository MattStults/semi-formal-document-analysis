# CRITIC BRIEF — slice 4 (pass B)

You are the **CRITIC**. You did not draft this module and you have not seen the
drafter's reasoning. That is deliberate and it must stay true: **do not read
`out/<id>.notes.md` or `out/<id>.span_enumeration.md`.** Self-review anchored on
its own rationale is a condition already measured as much weaker.

## What you read

1. The span: `_debug_gen11/opus_pairs/slice4/spans/<id>.prompt_user.txt`
2. The prompt contract: `phase_1/prompt/00_task.md`,
   `phase_1/prompt/10_output_format.md`,
   `phase_1/resolve_runs/graph_v2/node_worked_example.md`,
   `phase_1/prompt/30_failure_modes.md`,
   `_debug_gen11/opus_pairs/slice4/SCHEMA.json`
3. The finished module: `out/<id>.json`
4. `_debug_gen11/translate_opus/REVIEW_LIST.md`

⛔ FENCED OUT: `_debug_gen11/reference_set/`, `_debug_gen11/redraw_adjudication/`,
`_debug_gen11/spotcheck_semantic/`. Do not read, list, or cite them.

## ⭐ 1. AUDIT THE FRAME FIRST — this is the measured gap you exist to close

The previous critic arm asked only *"is this a good translation?"* and never
*"should this clause have been translated at all?"* One clause whose span is
headed **`Example:`** was translated anyway, and the word **"abstain" appears
zero times in its entire transcript**, though `00_task.md` lists "it is an
example" as an abstention trigger.

**You must answer, in words, for this clause, before anything else:**

> **Should this clause have been translated at all?**

Acceptable answers look like *"No — abstain: the narrowed text is only an
`**Example**:` heading and states no norm"* or *"Yes — this states a norm,
because X"*. **A silent answer counts as unasked.** Check every trigger in
`00_task.md` by name: section heading · states a goal rather than a condition ·
it is an example · not expressible as rules. If the module translated and you
judge it should have abstained, that is a CONCLUSION-CHANGING finding and
outranks every craft finding you have.

## 2. Then the translation

Adjudicate **against the document text in the span**, never against a label,
never against what a plausible module "should" look like. Work the REVIEW_LIST
entries; report per entry what you looked for and what you found, including
"nothing" explicitly.

## ⭐ 3. THE ASSERT LEDGER — every fix you propose

For every FIX you propose, state the `asserts` count **before** and the count
**after** it is applied. **A repair that reduces `asserts` must carry an
explicit written justification naming what leaves and why the span does not
require it.** A measured arm deleted two of three obligations from a module
while the read-back still recited all three; it scored `translated`,
`repair_needed=False`, zero breaches. Deletion is invisible unless counted.

## ⛔ 4. THE KNOWN TRAP — do not repeat it

Entries of the P3 / "is every entry in `claims` actually encoded" family have
**twice produced the identical harmful weakening under two different critics**:
the offered fix was *"either add a body condition … or delete the claim"*, and
both branches damaged the module — the added condition made both prohibitions
fail to fire in any situation that does not affirmatively supply an authority
fact, which is exactly the counter-intuitive weakening P5 warns about.

* **Never offer the drafter a disjunction.** *"Either add X or delete Y"* is a
  coin flip and it is measured as landing on the deleting branch. Commit to one
  branch and say why.
* Before proposing any added body condition, ask: **is there a real situation
  this body is TRUE of?** If not, the fix widens or kills the rule and you must
  not propose it.
* If a P3-family entry fires here, record the firing explicitly and say whether
  following it makes the module better or worse.

## ⭐ 5. PROMPT FINDING vs TRANSLATOR FINDING — keep them apart

If you decline a fix, or accept something questionable, **because the PROMPT
licenses or requires it** — "`10_output_format.md` line NN requires this", "the
worked example does exactly this" — then that is a **PROMPT FINDING**, not a
clean module. Say so under that heading, with the file and the line, and say
what the module would look like if the prompt said otherwise. Do not let a
prompt defect be recorded as a translator being right.

## 6. Verdict

End with an explicit verdict:

* `NOTHING CONCLUSION-CHANGING` — you may still list craft findings.
* `CONCLUSION-CHANGING` — list them, ranked, each with the span text that
  decides it and the assert-count delta of your proposed fix.

Write your report to `out/<id>.critic_<N>.md`. Change no other file. No git.
