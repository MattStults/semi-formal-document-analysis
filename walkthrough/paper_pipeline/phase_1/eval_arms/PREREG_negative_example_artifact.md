# Pre-registration — does a negative example TEACH THE SHAPE IT WARNS AGAINST?

**Written 2026-08-07, before any call of either run.** Frozen at the same moment as
`PREREG_bad_example_6_rerun.md`, deliberately: designing this arm after seeing the re-run's numbers
would be choosing the follow-up that the numbers reward.

⛔ Not seat material, not eval input.

---

## The hypothesis

`prompt/20_worked_example.md` warns against six failures by **showing each one as a JSON artifact**.
Bad example #6 shows

```json
{ "name": "terrorism_act", "arity": 1, "gloss": "an act of terrorism" }
```

under the heading "imports a name without its content". `RESULT_bad_example_6.md` found arm B
(with #6) producing empty glosses where arm A produced none — consistent with the model **imitating
the concrete artifact regardless of its label**, the way `DEBUGGING_TIPS.md` §1 found an example
outranking the prose that contradicted it.

⚠️ That prior reading is now known to be censored (see the re-run prereg), so the motivating
observation may evaporate. The hypothesis is worth testing anyway, and **it bears on all six bad
examples, not on #6** — if a shown artifact teaches its own shape, every "here is the wrong way"
block in this prompt is a demonstration with a warning label on it.

## The discriminating arm

**Arm C** = arm B with the **wrong-form artifact deleted** and its prohibition stated in prose. The
**correct**-form artifact stays, identically, in both. Nothing else changes anywhere.

| | wrong-form JSON shown | prohibition stated | correct-form JSON shown |
|---|---|---|---|
| **A** (no #6) | — | — | — |
| **B** (#6 as committed) | ✅ | ✅ | ✅ |
| **C** (#6, prose only) | ⛔ | ✅ | ✅ |

⭐ **Length is controlled.** C's system block is **36 chars shorter** than B's — 33,395 vs 33,431,
a 0.1% difference, against the 1,302-char (4%) gap between A and B. So a B-vs-C difference cannot
be "arm B's prompt is longer", which is a live confound in the A-vs-B comparison and is why that
comparison alone cannot answer this.

Both arms pinned to `09f9809`; verified byte-identical in `00_task.md`, `10_output_format.md`,
`30_failure_modes.md`, and differing in `20_worked_example.md` only, in the five lines quoted above.

## Predictions ⭐ FROZEN

Measured on `raw_empty_gloss_rate` (uncensored — see the re-run prereg), same 6 clauses, 3 repeats.

1. **H_imitation:** the artifact is what teaches ⇒ **B > C**, by more than the noise band, and C ≤ A.
2. **H_instruction:** the prose prohibition is what teaches ⇒ **B ≈ C**, both ≤ A.
3. ⛔ **FALSIFIER for H_imitation:** if `B − C ≤ 0`, the shown artifact is not what produced the
   empty glosses and H_imitation is **not supported**. It is then not to be rescued by re-cutting
   the metric or by adding a fourth arm; it is written up as unsupported.
4. If **A, B and C are all within one noise band of each other**, this run says nothing about
   either hypothesis and must be reported as underpowered, not as "no effect".

## ⭐ The arms actually tried, so the search is visible

`PROPOSAL_graveyard.md` requires that a search be visible rather than reported by its winner. The
complete list of arms built for these two runs:

| arm | what it is | run? |
|---|---|---|
| A `prompt_head` | `09f9809` minus #6 | ✅ run 1 |
| B `prompt_head_plus6` | `09f9809` as committed | ✅ runs 1 and 2 |
| C `prompt_head_plus6_prose` | B, wrong-form artifact deleted, prose kept | ✅ run 2 |

No other arm was built, and **no arm will be added after seeing these results** without a new
pre-registration saying so and saying why. If a further arm is ever wanted, the obvious one is
"#6 with the wrong-form artifact and NO prose prohibition", which would separate label from
artifact completely; it is not being run now, because two runs is the budget and a third arm chosen
after the fact is the thing this section exists to prevent.

## Cost

Run 2 is 36 calls, arms B and C, same worst-case estimate as run 1 (~$0.21) against the $0.25
ceiling; expected actual ≈ $0.05. Combined expected actual for both runs ≈ $0.10 against a $0.25
task ceiling and an $8.50 project cap.
