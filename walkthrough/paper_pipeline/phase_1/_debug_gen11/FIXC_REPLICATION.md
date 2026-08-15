# FIXC_REPLICATION.md — the randomised replication of TIER_ANALYSIS §6, and what it kills

**Headline: the confound did NOT survive. `TIER_ANALYSIS.md` §6's 5/10 → 10/10 (p = 0.033)
was batch variance, not the instruction.** Under randomisation, with the same model, the
same byte-identical prompts and three draws per cell, arm A scores **20/30** and arm B
scores **22/30** (p = 0.78). The rank-1 falsifier named in `TIER_ANALYSIS.md` §8 —
*"if arm A's pass rate then matches arm B's, the §6 result was batch variance"* — **fired.**

Per the standing instruction that this result gates everything downstream:

* **Fix C is NOT proposed.** No diff was written against `prompt/00_task.md`,
  `prompt/10_output_format.md`, `prompt/20_worked_example.md` or `schema.py`.
  `PROPOSED_prompt_fixC.md` **does not exist and was deliberately not written.**
* **The DC-1 worked example was NOT landed.** `resolve_runs/graph_v2/node_worked_example.md`
  is **unmodified**. Experiment 2 was built to the point of being runnable and then **not
  run**, because the gate says step 2 only proceeds if step 1 holds. Its materials are
  preserved in `fixc_replication/` so the decision can be taken on its own merits rather
  than re-derived.

**Zero API spend.** Every draw is a local Haiku subagent; nothing under `runs/`,
`translation_sample/runs/` or `repair_graveyard/` was written to. The stored prompts were
read only.

---

## 1. What was wrong with the original design

`TIER_ANALYSIS.md` §6 states the defect itself: each arm was run by two subagents of five
clauses each, and **the A/B split coincided exactly with the batch split** — A1 passed
5/5, A2 failed 0/5. Agent-level variation could not be separated from clause-level
difficulty. §6's own mitigation — *"A2's five failures reproduce the stored DeepSeek
findings clause-for-clause"* — is what this replication tests directly, and it does not
hold up (§4).

## 2. Design of the replication

| | |
|---|---|
| cohort | the **10** clauses of the 08-14 pair whose attempt-1 repair message was `borrowed-without-gloss` **and nothing else** — recomputed from the transcripts, reproduces §6's cohort exactly |
| system prompt, arm A | the stored `20260814-173322/prompt_system.txt`, byte-identical, 36,605 chars, `sha256[:16] = 5ff9daf7fe58845f` |
| system prompt, arm B | arm A **+ RULE G** appended (37,711 chars). Exact text: `fixc_replication/RULE_G.txt` |
| user prompt | the stored per-clause `<clause>.prompt_user.txt`, byte-identical, read-only |
| draws | **3 per (clause, arm)** → 30 per arm, **60 observations** |
| **randomisation** | **one task per subagent.** 60 isolated Haiku subagents, each given exactly one system + one user prompt, told to read nothing else, answer once, and not iterate. Task ids were shuffled under a fixed seed (`20260815`) so dispatch order carries no arm information |
| gate | `checks.run_checks(obj, clause_row, corpus_ids, concepts=None, attempt=1)` — **exactly** the call `translate.py:2557` makes at attempt 1, over the 773-id `node_corpus_all.json`. `schema.validate_all` runs inside it |
| endpoint | `outcome == "translated"` — the pipeline's own definition of "clean at attempt 1" |

**Why one task per subagent.** It is the only design under which agent identity cannot
carry arm information at all: every observation has its own fresh context, so there is no
batch to confound with and no cross-clause carryover in either direction. It is stronger
than the "≥3 draws per cell" the falsifier asked for, and it costs nothing extra locally.

**Harness validated before use.** The scorer was run against the stored DeepSeek artifacts
first: every cohort clause's stored attempt-1 draft scores `invalid` /
`['borrowed-without-gloss']`, and its stored final `.json` scores `translated` / `[]`. The
harness reproduces the pipeline's own verdicts on bytes whose verdicts are already on disk.

## 3. Result — EXPERIMENT 1

| arm | clean at attempt 1 | 95% (Wilson) |
|---|---|---|
| **A — stock gen-11 prompt** | **20 / 30 = 67%** | [49–81] |
| **B — stock + RULE G** | **22 / 30 = 73%** | [56–86] |

* **Fisher exact, two-sided: p = 0.779.** Difference **+6.7 pp**, 95% CI **[−16, +30] pp**.
* **Clause-blocked permutation test** (arm labels permuted *within* each clause, which is
  the randomisation actually performed): diff = +0.067, **p = 0.769**. This is the primary
  test — it cannot borrow strength from between-clause differences.
* **The original claimed +50 pp. That is outside the replication's confidence interval.**
  The replication is powered to exclude the reported effect size, and does.

Per clause (clean draws / total):

| clause | arm A | arm B |
|---|---|---|
| l1_170_n036 | 2/3 | 2/3 |
| l1_170_n046 | 3/3 | 2/3 |
| l1_170_n049 | 2/3 | 2/3 |
| l1_170_n051 | 3/3 | 3/3 |
| l1_170_n056 | 3/3 | 2/3 |
| l1_170_n071 | 3/3 | 3/3 |
| l1_170_n072 | 1/3 | 3/3 |
| l1_170_n075 | 0/3 | 2/3 |
| l1_170_n082 | 1/3 | 1/3 |
| l1_170_n087 | 2/3 | 2/3 |

### 3.1 The test was not vacuous, and that is what makes the null informative

The obvious way to dismiss a null here is "the requirement never fired". It did fire:

* **25 of 30 arm-A draws declared at least one borrowed name** (`requires` + `inputs`),
  mean 2.70 names per draft, so they were exposed to the obligation. Clean-among-exposed
  is 19/25 (A) vs 21/27 (B) — the same null.
* Arm B did write more: mean 3.27 declared names and 3.97 `concepts` entries against arm
  A's 2.70 and 3.23. **RULE G was read and acted on.** It simply did not move the endpoint.

### 3.2 The targeted defect barely occurs — the sharpest limitation of this instrument

| | arm A | arm B | Fisher |
|---|---|---|---|
| draws carrying `borrowed-without-gloss` at attempt 1 | **2 / 30 (7%)** | **0 / 30 (0%)** | p = 0.49 |

RULE G did remove the class where it appeared — but it appeared **twice in thirty draws**.
Under randomisation Haiku essentially does not make the defect that Fix C exists to prevent,
even on the ten clauses selected precisely because DeepSeek made it there. **This corpus
region + Haiku is a weak instrument for Fix C**, and §6's apparent power came from one
subagent that happened to make the mistake five times in a row.

### 3.3 Defect trading, the second falsifier, is visible

`TIER_ANALYSIS.md` §8 rank 1 also lists: *"if a grammar-enforced version raises another
class by more than it removes, it has traded a cheap defect for a lethal one."* Small
numbers, but the sign is there:

| classes seen ONLY in arm A | classes seen ONLY in arm B |
|---|---|
| `borrowed-without-gloss` (2), `act-not-in-acts` (1), `empty-body-not-null` (1) | `asp-body-unparseable` (2), `undeclared-body-name` (1), `readback-slot-arity` (1), `toggleable-licence-mismatch` (1) |

Arm B removed 2 findings of the target class and introduced 5 findings across four other
classes, two of them (`asp-body-unparseable`) in the family that makes clingo refuse the
whole file. **Directional only — do not quote as a measured trade rate.**

## 4. The specific §6 claim that does not reproduce

§6's strongest argument was that arm A's failures were not arbitrary: *"a second, unrelated
model reading the same 36 kB spec makes the identical omission on the identical clauses."*
Splitting this replication by the original batches:

| original batch | originally | arm A here | arm B here |
|---|---|---|---|
| A1: n036, n046, n049, n051, n056 | 5/5 PASS | **13/15 (87%)** | 11/15 (73%) |
| A2: n071, n072, n075, n082, n087 | **0/5 FAIL** | **7/15 (47%)** | 11/15 (73%) |

* The A2 clauses are genuinely somewhat harder (87% vs 47% within arm A) — **there is a
  real clause-difficulty gradient**, and that part of §6's intuition survives.
* But **0/5 is not reproducible**: the same five clauses under the same stock prompt pass
  7 of 15 times. The "identical omission on identical clauses" was one context's run of
  bad luck, amplified by n = 5 with no replication.
* On the A2 subset alone, arm B is +26.7 pp (11/15 vs 7/15), **Fisher p = 0.264, CI
  [−7, +60]** — a direction, not a finding, and it is exactly the subgroup the original
  design selected on, so it is the least trustworthy number in this document. On the A1
  subset arm B is **−13.3 pp** (11/15 vs 13/15, p = 0.651); the two subgroups cancel, which
  is what a null looks like when you slice it.

⚠️ **One disclosure about the draws.** Three tasks (`t054`, `t057`, `t059`) were dispatched
twice — the first attempt hit the 20-subagent concurrency limit and was re-issued, and both
agents eventually ran and wrote to the same file, so the stored answer is the second
agent's. Each stored answer is still exactly one isolated agent's single first response, so
the design is intact, but the *selection* of which of two draws survived was arbitrary
rather than random for those three. Scoring the earlier set instead gives arm B 21/30
(p = 1.00) rather than 22/30 (p = 0.78). **Both readings are null and both exclude the
original's +50 pp**, so nothing in this document turns on it.

## 5. EXPERIMENT 2 — built, staged, and NOT RUN

The DC-1 discoverability experiment was constructed in full and deliberately left unrun,
because step 1 gates it:

* Cohort: the **17** clauses of the 08-14 pair whose attempt-1 defect was
  `undeclared-body-name` and nothing else (recomputed; matches `TIER_ANALYSIS.md` §7).
* Arm A: the stored system prompt. Arm B: the same prompt with the embedded
  `node_worked_example.md` text replaced by a version carrying **one added worked example**
  — node `l1_170_n028`, a glossary-shaped span rendered as **fourteen body-less ground
  `ontology` atoms**, with an enumerated where-does-it-go table (the ENUMERATION precedent
  DC-1 points at). Draft: `fixc_replication/DRAFT_worked_example_section.md`.
* 17 × 2 arms × 2 draws = **68 tasks**, same one-task-per-subagent randomisation.
* Manifest: `fixc_replication/exp2_manifest_NOT_RUN.json`. Builder: `build_exp2.py`.

The draft example **was validated** against `checks.run_checks` on the pinned 15-node
`node_corpus.json` before being staged: `outcome = translated`, zero errors, four notes
(head-less situation inputs, which every good example in the file already produces). It
also satisfies the constraints `test_node_worked_example.py` imposes — its `clause_id` is
one of the 15 sample nodes, the `## The six bad ones` heading is untouched, and it adds a
fifth good module rather than replacing one.

⚠️ **Nothing about experiment 2 is evidence yet.** It is a designed instrument, not a
result, and it inherits the instrument problem §3.2 exposes: before spending anything on
it, check whether Haiku reproduces `undeclared-body-name` on that cohort at a rate that
gives the design any power at all. If it does not, the honest next step is DeepSeek, not
another Haiku pass.

## 6. What this does and does not establish

* ⚠️ **Haiku is a DIFFERENT MODEL from `deepseek-ai/DeepSeek-V4-Flash-0731`. This is
  evidence about the INSTRUCTION as read by one model, not a guarantee for DeepSeek** —
  the same caveat §6 carried, and it cuts both ways here.
* **Established:** §6's reported effect size does not replicate under randomisation and is
  excluded by this experiment's confidence interval. The §6 number must not be quoted, in
  `EXPERIMENTS.md` or anywhere else, as a measured effect of the instruction.
* **Established:** the observational evidence in `TIER_ANALYSIS.md` §5.2 is untouched by
  this. `borrowed-no-gloss` really is 57% of the 2-attempt tier's single repair round and
  26% of all repair rounds **in the DeepSeek corpus**. This replication says nothing about
  those counts; it says the *live A/B that was offered as the fix's evidence* was noise.
* **NOT established:** that Fix C is worthless. The CI admits effects up to +30 pp, and
  §3.2 shows this instrument could not detect a real effect anyway. **The correct next
  measurement is the DeepSeek A/B that `TIER_ANALYSIS.md` §8 rank 1 already names** — and
  it should be run with this replication's randomisation, not the original's batching.
* **NOT established:** anything about DC-1 / rank 2. The worked-example hypothesis rests on
  the review's reading of `schema.py` and on the 60%-vs-38% observational split, neither of
  which passes through §6. Its evidence base is independent and undamaged; only its
  *sequencing behind rank 1* was assumed.

## 7. Falsifiers for THIS document

* **If the reconstructed RULE G is materially weaker than the original's.** §6's artifacts
  lived in a session scratchpad and are gone; `RULE_G.txt` is a reconstruction from §6's
  own description (counted, local, name + arity + gloss, written before `asserts`). **This
  is the single most likely way this replication is unfair to Fix C.** Re-run with the
  original wording if anyone can produce it.
* **If 30 draws per arm is too few.** It is not, for the claim under test: +50 pp is
  excluded. It *is* too few for +10 pp. A replication wanting to detect a small real effect
  needs roughly ten times this.
* **If `concepts=None` is the wrong gate.** It is what `translate.py` passes at attempt 1,
  and the harness reproduces the stored DeepSeek verdicts under it. Passing the corpus-wide
  concept table would add cross-clause link findings the live attempt-1 call never saw.
* **If the cohort is wrong.** It was recomputed from the transcripts with
  `translation_repair_census.classify` and reproduces §6's 10 clauses and §7's 17 exactly.

## 8. Reproduction

Everything is in `_debug_gen11/fixc_replication/`: `cohort.py` (cohort derivation),
`build_exp1.py` / `build_exp2.py` (task construction, fixed seeds), `score.py` (the
pipeline gate), `analyse.py` (Fisher, Wilson, clause-blocked permutation),
`exp1_manifest.json` + `exp1_scored.json` (all 60 observations with their findings),
`RULE_G.txt`, `exp2_manifest_NOT_RUN.json`, `DRAFT_worked_example_section.md`.
