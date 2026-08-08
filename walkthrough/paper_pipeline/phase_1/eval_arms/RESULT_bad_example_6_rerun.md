# Result — bad worked example #6, re-run. ⛔ PREDICTION FALSIFIED AGAIN, and this time the test is VALID

36 live calls, **$0.0536**. Predictions frozen in `PREREG_bad_example_6_rerun.md`, committed at
`ac859d3` before the first call. Raws: `RESULT_bad_example_6_rerun_raw/`.

## ⭐ FIRST: the validity gate, which is what the last run failed

The pre-registration said the test is invalid unless the control arm's **raw** empty-gloss rate
clears 0.02, and named ≈ 0.10 as the expected value.

| arm A (no #6), per repeat | r1 | r2 | r3 | mean |
|---|---|---|---|---|
| `raw_empty_gloss_rate` | 0.042 | 0.200 | 0.140 | **0.127** |
| `raw_gloss_concepts_scored` | 4.0 | 5.8 | 7.2 | 5.7 |

**14 empty glosses in 102 concepts, in every repeat, on 4 of the 6 clauses.** The gate is cleared
and the predicted incidence (0.10) was close. ⇒ **The eval set exhibits the failure in the control
arm, and the delta below is readable.** That was the whole point of the selection rule.

The censoring diagnosed in the pre-registration also reproduced, in both arms
(prediction 3, HELD): `raw_gloss_concepts_scored` 5.7 vs `gloss_concepts_scored` 3.9 in arm A, 6.2
vs 5.1 in arm B. The censored metric would have shown arm A at 0.084 — not zero this time, but
still a third of the concepts unseen, and unseen at a rate that differs between arms.

## The registered prediction failed

Prediction 1: `raw_empty_gloss_rate` **falls** in arm B.

| | A (no #6) | B (with #6) | B − A | noise band |
|---|---|---|---|---|
| `raw_empty_gloss_rate` per repeat | 0.042, 0.200, 0.140 | 0.121, 0.103, 0.265 | | |
| mean (sd) | **0.127** (0.080) | **0.163** (0.089) | **+0.036** | 0.169 · within noise |
| `empty_gloss_rate` (censored) | 0.046, 0.125, 0.080 → 0.084 | 0.129, 0.143, 0.277 → 0.183 | +0.099 | 0.121 · within noise |
| pooled concepts | 14 / 102 = 0.137 | 20 / 111 = 0.180 | Fisher p = 0.51 | |

⛔ **It did not fall. It rose**, on both the raw and the censored metric, and the pre-registered
falsifier says that means bad example #6 did not teach what it was added to teach.

**And it rose again in the independent second run.** Arm B was re-run against arm C the same day
with the same clauses (`RESULT_negative_example_artifact.md`): 20 / 109 = **0.183**, against 0.180
in run 1. Pooled over 6 repeats, arm B is **40 / 220 = 0.182** against arm A's 14 / 102 = 0.137
(Fisher p = 0.34). Two independent runs put arm B above the control by about the same amount.

⚠️ **Every one of those differences is inside the noise band, and none is significant.** The claim
here is not "#6 makes it worse". It is the weaker and pre-registered one: **#6 does not make it
better, and the point estimate moves the wrong way in both runs.**

## The regression check PASSED (prediction 2, HELD)

| | A | B | delta | band |
|---|---|---|---|---|
| `first_attempt_clean_rate` | 0.611 | **0.722** | +0.111 | 0.385 |
| `error_findings_per_clause` | 1.500 | **1.111** | −0.389 | 1.937 |
| `unbuildable_rate` | 0.333 | 0.278 | −0.056 | 0.359 |

Adding #6 does not damage mechanical validity — same as last time, and this is what Matt asked the
first run to check.

## The arms

Pinned to `09f9809`. `00_task.md`, `10_output_format.md`, `30_failure_modes.md` **byte-identical**;
`20_worked_example.md` differs by **+1,302 chars** (system block 32,129 → 33,431, +4.05%), which is
#6 plus the two heading renames and nothing else. Eval set: m0491, m0329, m0073, m0068, m0411,
m0580 (`heldout_categories.txt`, salt `eval-categories-v1`, 34 ids excluded).

## ⭐ RECOMMENDATION: REVERT bad worked example #6 — and this is a recommendation, not an act

`prompt/20_worked_example.md` has not been touched. The revert decision is Matt's.

**Grounds.** #6 was added to reduce empty glosses. On a control arm that demonstrably produces
them (13.7% of concepts, all three repeats, 4 of 6 clauses), adding it **did not reduce them in
either of two independent runs**, and the point estimate moved the wrong way in both. The
pre-registered falsifier for exactly this outcome says revert rather than keep because it reads
well. The regression check gives no reason to keep it either: nothing else improved outside noise.

**The honest counter-case, stated because it is real.** Every delta is inside the noise band; n is
6 clauses and one model; and the prompt-length confound (+4%) is not separated in this run. A
defender of #6 can say the measurement is too weak to condemn it. What the measurement will not
support is the claim that #6 helps — that claim has now been tested twice and failed twice, once
invalidly and once validly.

**What would change the recommendation:** a run at 6+ repeats on 12+ rule-positive clauses, where
the arms are length-matched the way B and C are, showing `raw_empty_gloss_rate` falling outside the
band. That costs roughly $0.20 and has not been run.

## Unregistered observation — do not treat as a finding

Arm B's excess is **almost entirely one clause**, m0073: 2/23 empty in arm A, 11/33 and 12/44 in
arm B's two runs, 2/22 in arm C. The other five clauses are flat (arm B minus arm A off m0073,
Fisher p = 0.53). Arm B also writes *more* concepts on that clause (33 and 44, against 23), and the
extra ones are `developer_message` → "message M is a developer message", `api_application` → "X is
an API application" — one predicate per named item, glossed by repeating the item.

⛔ **This is a cut chosen after seeing the data, on one clause, and its p of 0.054 is what a
post-hoc single-clause cut produces when there is nothing there.** `DEBUGGING_TIPS.md` §3 is
explicit that this is the shape fitting takes. It is recorded as a hypothesis for anyone who runs
this again with more clauses — *#6 makes the model decompose a definitional clause into more named
categories, and the extra names arrive without content* — and as nothing more.
