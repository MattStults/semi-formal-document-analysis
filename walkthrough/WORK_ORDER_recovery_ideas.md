# Work order — generate and validate ideas for recovering translation failures

You are being asked for IDEAS THAT SURVIVE MEASUREMENT. Three appealing
conclusions died this week the moment someone tested them properly, so the
bar here is evidence, not plausibility. A well-argued idea with a null
result is a success and should be reported as one; an untested idea that
sounds right is worth nothing to this project.

## The problem

Full-corpus translation (773 graph nodes, DeepSeek-V4-Flash) measured over
~100 clauses: **69 translated, 19 unrepaired, 12 abstained** — a 19% hard
failure rate, projecting ~146 lost modules of 773. First-try rate is ~43%.
A lost module takes its concepts and edges with it, so coverage — not spend
— is what matters (the whole corpus costs ~$4).

## What is already SETTLED — do not re-derive, do not contradict without evidence

Read `walkthrough/paper_pipeline/phase_1/_debug_gen11/` in full: `SUMMARY.md`,
`OUTCOME_TABLE.md`, the seven `class_*.md` files, `ANALYSIS_REVIEW_verdict.md`,
`CHAIN_ANALYSIS.md`, `TIER_ANALYSIS.md`, `FIXC_REPLICATION.md`.

**Established:**
* Freezing is MOTION, not difficulty: chains whose every reply differs end
  translated 98% (63/64); chains repeating any earlier reply, 9% (3/32).
  Nothing about the defect predicts the outcome.
* A fresh draw beats the repair loop: 14 of 19 lost clauses recovered on one
  byte-identical re-draw ($0.078/45 calls vs $0.178/95 calls for nothing).
* First-try is governed by defect KIND, not volume: defect count is null
  (1 finding resolves 41% of the time, 4 findings 43%); span length, line
  count, narrowing, output length and predicate count are all null.
* The only EXOGENOUS separator known before spending: graph `needs` >= 2
  (24% first-try vs 45%).
* Arity mismatch is 0/11 first-try and 73% unrepaired.

**Refuted — do not build on these:**
* "There is no legal declaration bucket for invented descriptive predicates"
  — FALSE. `ontology` accepts a body-less ground atom, `schema.py` declares
  by NAME ALONE, `prompt/10_output_format.md` says so in bold, and 33 of 173
  ontology entries across translated modules already do it, all first-pass.
  The real residual is DISCOVERABILITY: only 7% of drafts use that route,
  and those that do land first-try at 60% vs 38%.
* Graph-stage span-type routing (normative vs about-the-document) — dead,
  adjudicated twice, once with an outcome-BLIND classification: normative
  31% vs non-normative 49%, p=0.25, and the WRONG SIGN.
* Fix C's counted-gloss rule — its evidence died under randomisation
  (67% vs 73%, p=0.78). The idea is not disproven; the evidence for it is.

**Already built, do not duplicate:** the restart-on-repeat chain policy
(`translate.py` repair loop) and the arity-aware declaration check
(`checks.py`). Both are committed and pinned.

## What to do

Generate candidate interventions for (a) recovering the ~19% that never
translate and (b) raising the ~43% first-try rate, then TEST them. Ideas may
target the prompt, the worked example, the grammar/format forcing, the
checker, the repair message, the corpus packing, or the order/segmentation
of work — anywhere except the two already-built fixes.

Rank your own candidates before testing, and say what each would cost.

## The experimental protocol — this part is not optional

The protocol below is what killed the last three false positives.

1. **Check the instrument FIRST.** Before A/B-ing a fix for defect X, verify
   the model under test actually produces defect X on your cohort at a rate
   that could show a difference. Fix C's replication was undermined because
   Haiku made the target mistake on only 2 of 30 stock draws — a null there
   measures the instrument, not the fix.
2. **Isolate the arm from the agent.** Use ONE Haiku subagent per task
   (Agent tool, `model: haiku`), never batching an arm into a subagent —
   that exact confound produced a spurious 5/10-vs-10/10, p=0.033 which
   became 20/30-vs-22/30, p=0.78 when decorrelated.
3. **Use the real inputs.** Byte-identical stored `prompt_system.txt` and
   `*.prompt_user.txt` from `resolve_runs/graph_v2/translation_sample/runs/`
   (read-only), and validate through the exact call `translate.py:2557`
   makes (`schema.validate` + `checks.run_checks`) — not a proxy.
4. **Pre-register the falsifier** before you look at results, and report the
   CI, not just the p-value. Report effects that fail your falsifier as
   nulls, plainly.
5. **Multiple draws per cell.** Tier is NOT a stable property of a clause:
   median within-cell attempt spread is 3, and of 20 twice-drawn cells 10
   disagree on first-try. A single draw per cell measures noise.
6. **Haiku is not DeepSeek.** Every result is evidence about the
   INSTRUCTION, not a guarantee for the production model. Say so, and name
   which findings would need a DeepSeek A/B before they could be trusted
   (that spend needs the owner's authorisation — do not spend).

## Fences

* ZERO project API spend. Haiku subagents only.
* NEVER modify: anything under any `runs/`, `translation_sample/runs/`, or
  `repair_graveyard/` directory; `translate.py`; `checks.py`;
  `translate_exec.py`; `dispatch_core.py`; `recurse_driver.py`.
* GUARD-WATCHED, propose diffs only, never apply: `prompt/00_task.md`,
  `prompt/10_output_format.md`, `prompt/20_worked_example.md`, `schema.py`.
* `node_worked_example.md` is NOT watched and may be edited — but only with
  a measured result behind the change.
* Work in your own worktree/branch. Do not push to `walkthrough-prototype`.

## Deliverable

`_debug_gen11/RECOVERY_IDEAS.md`: every candidate with its rationale, its
predicted mechanism, the experiment run, the effect size with CI, the
falsifier and whether it fired, and a verdict — VALIDATED / NULL /
UNTESTABLE-WITH-THIS-INSTRUMENT. Plus a ranked shortlist of what deserves a
DeepSeek A/B and what it would cost.

Report back: which ideas survived, which died, and the single experiment you
would run next if given production budget.
