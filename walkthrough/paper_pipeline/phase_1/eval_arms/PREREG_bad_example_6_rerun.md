# Pre-registration — bad worked example #6, re-run. ⭐ FROZEN BEFORE ANY CALL

**Written 2026-08-07, before the first live call of this run.** Supersedes nothing:
`PREREG_bad_example_6.md` and `RESULT_bad_example_6.md` stand as the record of a test that was
invalid. Ruling on the change itself: `DECISION_bad_worked_examples.md`.

⛔ **This document is not seat material and is not eval input.** It pre-registers an expected
outcome.

---

## Why the first test was invalid — and a THIRD reason, which is the important one

`RESULT_bad_example_6.md` lists two: the control arm scored 0.000 (read as "the eval set does not
exhibit the failure"), and arm B's correct-form fragment was malformed JSON. The second is fixed at
`09f9809`. The first is **wrong about its own cause**, and re-counting the run's raw responses —
already on disk, no spend — says so:

| arm A of `RESULT_bad_example_6` | empty glosses | concepts | rate |
|---|---|---|---|
| as `empty_gloss_rate` measured it | 0 | 42 | **0.000** |
| re-counted from `*_raw/A/r*/*.raw.txt` | **8** | 84 | **0.095** |

All eight sat inside modules that failed a schema check. `gloss_metric` reads `o.module`, which is
`None` for those, so it never saw them. **The zero was CENSORING, not absence.** And the censoring
is not neutral between arms: A and B differed in `unbuildable_rate` (0.444 vs 0.333) as well as in
glosses, so the metric compared two differently-sized populations and reported the difference as an
effect.

⇒ Fix 3, and the one that makes the re-run worth paying for: **`glosses_raw`**, a new metric in
`eval.py` that counts the same thing off the raw response text and conditions on nothing but "it
parsed as JSON". `raw_responses_parsed` is printed beside it (`DEBUGGING_TIPS.md` §2). RED-verified:
the five new tests in `test_eval.py` fail against `eval.py` at `09f9809`.

## The eval set — the rule, frozen, with its derivation shown

`eval_arms/select_category_clauses.py`, salt `eval-categories-v1`, n = 6, drawn from 63 eligible of
593 with 34 ids excluded. **A clause is eligible iff** its kind is definitional or conditional, its
quote is ≥ 100 chars, it is in none of the exclusion sets, and it carries at least one of:

* **a run of ≥ 3 consecutive comma-separated segments**, each ≤ 60 chars and ≤ 8 words — the
  document enumerating the members of a category; or
* **a bolded term** — the document naming one outright.

Drawn: **m0491, m0329, m0073, m0068, m0411, m0580**. Excluded: every clause ever sent
(`runs/*/*.raw.txt`, `runs/*/*.transcript.json`, `eval_arms/*_raw/*/*/*.raw.txt`), heldout v1/v2/v3
and the diagnosis set, and every `m####` named in any prompt file or arm. The exclusion sets are
enumerated in `heldout_categories.txt.provenance.json`.

⚠️ **THE RULE WAS DERIVED FROM DATA AND HERE IS THE WHOLE SEARCH.** Six candidates were scored
against the empty glosses in the 24 clauses already on disk. Every one of those 24 is excluded from
the draw, so the drawn set is held out from the derivation — but the rule is fitted to them and
that is not nothing.

| candidate | rule-positive | rule-negative | kept? |
|---|---|---|---|
| marker word ("such as", "e.g.", "including") + 2 commas — **tried first** | 5/103 = 4.9% | 25/390 = 6.4% | ⛔ discarded, does not discriminate |
| bolded term alone | 4/58 = 6.9% | 26/435 = 6.0% | ⛔ discarded |
| backticked term alone | 10/77 = 13.0% | 20/416 = 4.8% | ⛔ only 2 positive clauses |
| **run of ≥ 3 items, or bolded term** | **22/226 = 9.7%** (9 clauses) | 8/267 = 3.0% | ⭐ **KEPT** |
| run of ≥ 3 items alone | 18/168 = 10.7% (5 clauses) | 12/325 = 3.7% | fewer positive clauses |
| run of ≥ 4 items | 18/135 = 13.3% (4 clauses) | 12/358 = 3.4% | highest rate, thinnest support |

The kept rule is **not** the highest-scoring one. It was chosen for the largest positive-clause
count (9), so that the expected incidence does not rest on one or two clauses, and because both
signals are the shape the observed failures actually come off: `file_attachment`, `tool_output`,
`multimodal_data`, `system_message`, `terrorism_act` — one predicate per listed item, glossed by
repeating the item's name.

## ⭐ WHAT INCIDENCE THE CONTROL ARM MUST SHOW, stated before the run

Expected `raw_empty_gloss_rate` in arm A: **≈ 0.10**, from the 9.7% the rule-positive clauses
already on disk produced. Expected `raw_gloss_concepts_scored` ≈ 4–8 per clause, so ≈ 75–140
concepts per arm over 6 clauses × 3 repeats.

⛔ **THE VALIDITY GATE, decided in advance.** If arm A's **raw** empty-gloss count is **0**, or its
`raw_empty_gloss_rate` is below **0.02**, the eval set again does not exhibit the failure and
**this test is invalid — the delta must not be read**, exactly as in `RESULT_bad_example_6.md`.
Reporting "B is worse than A" off a control of zero is the mistake this whole re-run exists to
undo, and doing it twice would be worse than not measuring.

⚠️ If instead `empty_gloss_rate` (censored) reads 0.000 while `raw_empty_gloss_rate` does not, the
test is valid and the censoring diagnosis above is confirmed.

## The arms

Both pinned to commit **`09f9809`**, because other agents are editing `prompt/` and the working
tree moves. Arm A = that commit's four prompt files with `20_worked_example.md` taken from
`de61f02` (the last state before #6). Arm B = that commit's four files as they are.

Verified: the two arms are **byte-identical in `00_task.md`, `10_output_format.md` and
`30_failure_modes.md`**, and differ in `20_worked_example.md` by **+1,302 chars** (system block
32,129 → 33,431, i.e. **+4.05%**). That delta is bad example #6 plus two "five bad" → "six bad"
heading renames, and nothing else.

## Predictions ⭐ FROZEN

1. **`raw_empty_gloss_rate` FALLS in arm B.** This is the original claim of #6, restated on the
   metric that can see the failure. Point prediction: A ≈ 0.10, B < A by more than the noise band
   (sum of the two arms' sd across 3 repeats).
2. **`first_attempt_clean_rate` does not fall and `error_findings_per_clause` does not rise** by
   more than the noise band. #6 teaches a semantic habit; it should not move mechanical validity.
3. **`raw_gloss_concepts_scored` > `gloss_concepts_scored` in BOTH arms**, i.e. the censoring
   reproduces on a fresh clause set rather than being a peculiarity of the last one.
4. ⛔ **FALSIFIER.** If `raw_empty_gloss_rate` does not fall — delta ≥ 0 — bad example #6 did not
   teach what it was added to teach, and the recommendation is **revert**, not keep-because-it-
   reads-well. If it *rises* by more than the noise band, that is a positive result for the
   imitation hypothesis and is pre-registered as such in
   `PREREG_negative_example_artifact.md`.

## What this still cannot settle

* `empty_gloss_rate` is a **proxy** and `DECISION_bad_worked_examples.md` refused it as a check:
  `system_message` → "C is a system message" scores empty and is correct. Legitimate as a rate
  ACROSS arms, never as a verdict on a concept.
* A gloss can gain words and gain no content. Only stage 4 can see that.
* n = 6 clauses, 3 repeats, one model, temperature 0.2. `within_noise` over 3 repeats is a weak
  yardstick and a delta inside it is not evidence of no effect.
* Arm B's system block is 4% longer. Length is not separated from content in this run — it is in
  the B-vs-C run, where the arms differ by 36 chars.
* The eval set's rule is fitted to 24 clauses' worth of prior responses. It predicts *where the
  failure occurs*, not *what fixes it*, so it cannot manufacture a difference between arms — but
  it can make the whole set atypical, and 6 clauses is not a corpus.

## Cost

36 calls, worst-case estimate **$0.2073** against the $0.25 config ceiling. Expected actual ≈ $0.05
at the ~$0.0014/call the last run measured.
