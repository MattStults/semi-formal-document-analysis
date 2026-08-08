# Result — bad worked example #6. ⛔ PREDICTION FALSIFIED, and the test is not yet valid

36 live calls, ~$0.05. Prediction frozen in `PREREG_bad_example_6.md` before any call.

## The registered prediction failed

| | A (no #6) | B (with #6) |
|---|---|---|
| `empty_gloss_rate` | **0.000, 0.000, 0.000** | 0.00, 0.04, **0.25** |
| `empty_glosses_per_clause` | 0.000 | 0.333 |

Predicted: it falls. It **rose**. My pre-registered falsifier says that means revert rather than
keep because it reads well.

⚠️ **But the test is not valid, for two reasons, and both are my fault.** I am not reverting on an
invalid test any more than I would keep on one.

## Why the test is invalid

**1. The control arm had ZERO incidence — there was nothing to improve.** Arm A's rate is 0.000
across all three repeats. The 7.5% baseline that motivated this came from a *different* clause set.
So this eval set does not exhibit the failure, and measuring a fix where the defect does not occur
is the licence-metric mistake again (`RESULT_licence_emphasis.md`), in a new costume. ⇒ The eval set
must be chosen for clauses that introduce named categories, not drawn blind.

**2. Arm B's "correct form" example was malformed JSON.** The `gloss` string in the corrected
fragment was written across two source lines. So the model was shown a **well-formed example of the
wrong way** and a **broken example of the right way**. Fixed after the run; the measurement predates
the fix.

## ⭐ The hypothesis this raises, which is worth more than the original question

**A negative example may teach the thing it warns against.** Bad example #6 shows
`{"name": "terrorism_act", "gloss": "an act of terrorism"}` as a concrete artifact. Arm B produced
empty glosses where arm A produced none. That is consistent with imitation of the shown shape
regardless of its "bad" label — and if it holds, it bears on all six bad examples, not just this one.

⚠️ **Consistent with, not evidence for.** n is tiny, the delta is within noise, and confound 2 is
live. This is a hypothesis to test, not a finding.

## The regression check — which is what Matt actually asked for — PASSED

| | A | B |
|---|---|---|
| `unbuildable_rate` | 0.444 | **0.333** (larger than noise, better) |
| `error_findings_per_clause` | 1.333 | 1.278 |
| `first_attempt_clean_rate` | 0.500 | 0.556 |

Adding #6 did not damage mechanical validity.

## What to do

1. Re-run with the malformed fragment fixed, on a clause set **selected for clauses that introduce
   named categories** — pre-register that selection rule so it is not fitted after the fact.
2. If `empty_gloss_rate` still does not fall, revert #6 and record that negative examples of this
   shape do not teach.
