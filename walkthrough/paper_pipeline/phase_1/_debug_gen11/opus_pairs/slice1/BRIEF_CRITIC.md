# CRITIC BRIEF — slice 1, opus pair loop

All paths are under
`/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/`.
Use ABSOLUTE paths in every tool call.

## What you are

You are an INDEPENDENT critic. You have never seen the drafter's reasoning and you must
not go looking for it. You get the span, the prompt contract, and the finished module —
nothing else. **Do NOT read** `out/<id>.notes.md` or `out/<id>.span_enumeration.md`, and do
not read any previous critic's report for this clause unless it is handed to you in this
brief. Self-review anchored on the drafting rationale is a condition already measured as
much weaker; your value is that you are not anchored.

## ⛔ Fenced out — do not read, list, or search these, at any depth

* `_debug_gen11/reference_set/`
* `_debug_gen11/redraw_adjudication/`
* `_debug_gen11/spotcheck_semantic/`

## Read

1. `prompt/00_task.md`
2. `prompt/10_output_format.md`
3. `resolve_runs/graph_v2/node_worked_example.md`
4. `prompt/30_failure_modes.md`
5. the span: `_debug_gen11/opus_pairs/slice1/spans/<CLAUSE_ID>.prompt_user.txt`
6. the module: `_debug_gen11/opus_pairs/slice1/out/<CLAUSE_ID>.json`

## ⭐ Question 1, and it is mandatory — THE FRAME

**Should this clause have been translated at all?**

`00_task.md` says: *"If you cannot translate this clause faithfully — it is a section
heading, it states a goal rather than a condition, **it is an example**, or its content is
not expressible as rules — abstain and give the reason."*

Answer **in words**, explicitly, for this clause. Both answers are real answers:

* "**No — it should have abstained**, because …", or
* "**Yes — this states a norm, because X**", naming the norm and the words that state it.

A measured failure of the previous cohort: a clause whose span is headed `**Example**:` was
translated anyway and the word *abstain* appears **zero times in its entire transcript**.
Auditing the translation while never auditing the frame is the gap this question exists to
close. **A silent answer counts as unasked.** Put your answer at the TOP of your report.

If the module already abstained, audit that too: is the abstention right, or did it decline
a clause that does state a norm?

## Question 2 — is it a good translation?

Work the module against the span and the output contract. The measured failure classes are
in `_debug_gen11/translate_opus/REVIEW_LIST.md` — read it, but you are not limited to it,
and an entry that fires wrongly is itself a finding.

Grade every finding:

* **CONCLUSION-CHANGING** — the module states something the document does not, or fails to
  state something it does, in a way that changes what a situation would be judged.
* **MINOR** — real but does not change a verdict.
* **NOT A DEFECT** — considered and rejected; say so.

## ⭐ Question 3 — is this defect the TRANSLATOR's, or the PROMPT's?

For every fix you decline because the production prompt licenses or requires the thing,
and for every defect you find whose true cause is an instruction in
`00_task.md` / `10_output_format.md` / `node_worked_example.md` / `30_failure_modes.md`,
say so **under a heading `PROMPT FINDING`**, quoting the file and the line that teaches it.
A previous critic rejected a real fix on the grounds that `10_output_format.md` requires it
and "the worked example does exactly this" — and it was probably right about the prompt.
That case must not be filed as a clean module. **A clean module and a prompt defect are two
different verdicts and you must not merge them.**

## ⭐ Question 4 — content deletion

State `len(asserts)`, `len(ontology)`, `len(claims)`, `len(beats)`, `len(closure)` for the
module as you received it. **Any repair you propose that would REDUCE `asserts` must be
justified explicitly, naming which obligation leaves and why the span does not carry it.**
A measured arm deleted two of three obligations while the read-back still recited all
three, and it scored `translated`, `repair_needed=False`, zero breaches.

## ⛔ Known trap — entry shape to distrust

An entry of the shape *"is every entry in `claims` actually encoded — and can the rule that
encodes it ever FIRE?"* has now produced the **identical harmful weakening under two
different critics** on another clause. Its nearest analogues in `REVIEW_LIST.md` are **P3**
and **N1**. If you are about to charge under either, check first whether your fix makes a
rule fire by weakening what it asserts. If it does, that is the trap. **Record the firing
and your judgement of it explicitly** in a section headed `TRAP CHECK`.

## Verdict

End with exactly one line:

`VERDICT: NOTHING CONCLUSION-CHANGING` or `VERDICT: CONCLUSION-CHANGING FINDINGS (n)`

## Output

Write your report to
`_debug_gen11/opus_pairs/slice1/out/<CLAUSE_ID>.critic_<TURN>.md`.
Do not edit the module. Do not edit `REVIEW_LIST.md`. No git.
