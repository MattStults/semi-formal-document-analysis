# Result — does a negative example teach the shape it warns against? ⚠️ UNDERPOWERED, NOT SUPPORTED

36 live calls, **$0.0539**. Predictions frozen in `PREREG_negative_example_artifact.md`, committed
at `ac859d3` before the first call of either run. Raws: `RESULT_negative_example_artifact_raw/`
(directory `A` is arm **B**, directory `B` is arm **C** — `eval.py` names arms by position).

## The arms

| | wrong-form JSON shown | prohibition stated | correct-form JSON shown | system block |
|---|---|---|---|---|
| A (no #6, from run 1) | — | — | — | 32,129 |
| **B** (#6 as committed) | ✅ | ✅ | ✅ | 33,431 |
| **C** (#6, prose only) | ⛔ | ✅ | ✅ | 33,395 |

B and C differ by **36 chars, 0.1%** — the five lines quoted in the pre-registration — so a
difference between them cannot be prompt length. That is the confound the A-vs-B comparison cannot
clear.

## The result

`raw_empty_gloss_rate`, 6 clauses × 3 repeats:

| | per repeat | mean (sd) | pooled concepts |
|---|---|---|---|
| A (no #6) | 0.042, 0.200, 0.140 | 0.127 (0.080) | 14 / 102 = 0.137 |
| **B** (artifact) | 0.154, 0.132, 0.244 | **0.177** (0.060) | 20 / 109 = 0.183 |
| **C** (prose only) | 0.176, 0.000, 0.273 | **0.150** (0.138) | 15 / 93 = 0.161 |

**B − C = +0.027, noise band 0.198.** Pooled, 0.183 vs 0.161, Fisher **p = 0.75**.

⇒ Pre-registered prediction 4 fires: **A, B and C all sit inside one noise band of each other, so
this run says nothing about either hypothesis and is reported as underpowered.** It is not
"H_imitation is false" and it is certainly not "H_instruction is confirmed".

Prediction 1 (H_imitation: B > C outside the band) is **not supported**. Prediction 3's falsifier —
`B − C ≤ 0` — did not technically fire (the delta is +0.027, the direction H_imitation predicts),
but a delta at one seventh of its own noise band is not evidence and will not be reported as a
trend. ⛔ Per the pre-registration, no fourth arm is being added to chase it.

## Arm B replicated

Worth recording on its own: arm B scored 0.180 (run 1) and 0.183 (run 2) on pooled concepts, on the
same clauses in two separate invocations. The arm is stable; it is the *difference* between arms
that this design cannot resolve at 3 repeats.

## Unregistered, and outside the noise band

`error_findings_per_clause`: B **0.944** → C **2.556**, delta +1.611 against a band of 0.778.
`first_attempt_clean_rate` (0.556) and `unbuildable_rate` (0.444) are **identical** between the
arms, so this is more findings per failing module, not more failing modules. Deleting the wrong-form
artifact while keeping the prose may cost mechanical validity.

⚠️ **Not pre-registered, one run, and the metric is a count of findings whose band is wide in every
other comparison here.** It is a reason to run this arm again, not a reason to believe it.

## What this leaves standing

The hypothesis — **a negative example may teach the shape it warns against, which would bear on all
six bad examples** — is neither supported nor refuted. It remains open, and
`RESULT_bad_example_6_rerun.md` records the one post-hoc observation that would motivate testing it
properly: arm B's excess empty glosses are concentrated on a single definitional clause where arm B
also emits *more* named concepts than either arm without the artifact.

The design is right and cheap; what it needs is power. 12 rule-positive clauses × 6 repeats × 2
arms is 144 calls, ≈ $0.21, and would put the B-vs-C band near 0.06 instead of 0.20. Nothing in
this run should be read as a result before that is done.
