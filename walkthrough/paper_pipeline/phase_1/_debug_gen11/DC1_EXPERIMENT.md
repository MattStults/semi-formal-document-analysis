# DC1_EXPERIMENT.md — the instrument check that stops the DC-1 A/B before it is run

**Headline: the gate FAILED. Verdict UNTESTABLE-WITH-THIS-INSTRUMENT.** Across 51
isolated stock-prompt Haiku draws on the 17-clause `undeclared-body-name` cohort, the
target defect appears **3 times (5.9%, Wilson 95% [2.0, 15.9])** and on only **2 of the
17 clauses**. The pre-registered gate required ≥15% with a Wilson lower bound ≥8%. **No
A/B was run. `node_worked_example.md` is unmodified. Nothing was landed.**

This is the same failure mode `FIXC_REPLICATION.md` §3.2 exposed for Fix C (2/30 = 7%) —
found this time *before* spending 102 draws on an experiment that could not have detected
its own effect.

**Zero API spend.** Every draw is a local Haiku subagent. `runs/`,
`translation_sample/runs/` and `repair_graveyard/` were read only.

---

## 1. Pre-registration

`fixc_replication/PREREG_dc1.txt`, written and committed to disk **before the first draw
was dispatched**. It fixes the gate threshold, the primary and secondary endpoints, four
falsifiers, the landing rule, and the design of the confound test. Nothing below was
chosen after seeing a number.

## 2. Instrument check — design

| | |
|---|---|
| cohort | the **17** clauses of the 08-14 pair whose attempt-1 defect set was exactly `{undeclared-body-name}`. Recomputed with `cohort.py` / `translation_repair_census.classify`; reproduces `TIER_ANALYSIS.md` §7 exactly |
| system prompt | the stored `20260814-173322/prompt_system.txt`, byte-identical, 36,605 chars, `sha256[:16] = 5ff9daf7fe58845f` (asserted in the builder) |
| user prompt | the stored per-clause `<clause>.prompt_user.txt`, byte-identical, read-only |
| draws | **3 per clause = 51**, **one isolated Haiku subagent per draw**, told to answer once and read nothing else. Task ids shuffled under seed `20260822` so dispatch order carries no clause information |
| gate call | `checks.run_checks(obj, clause_row, corpus_ids, concepts=None, attempt=1)` over the 773-id `node_corpus_all.json` — **exactly** the call `translate.py:2557` makes at attempt 1. `schema.validate_all` runs inside it. Not a proxy |

**Harness validated before use, on bytes whose verdict is already on disk.** Every one of
the 17 stored DeepSeek attempt-1 drafts scores `invalid` with `undeclared-body-name`
present — **17 of 17**. The scorer reproduces the pipeline's own verdicts.

**Operational check.** All 51 answers parsed as JSON; zero `not-json`. The measured rate
is not an artifact of malformed output.

## 3. Result — the gate

| | value |
|---|---|
| `undeclared-body-name` at attempt 1 | **3 / 51 = 5.9%**, Wilson 95% **[2.0, 15.9]** |
| clauses on which the class ever fired | **2 of 17** (`n023` 1/3, `n032` 2/3) |
| **GATE** (pre-registered ≥15% and Wilson-lo ≥8%) | **FAIL** |

Both conditions fail, and not marginally: the point estimate is below the threshold and
the *upper* confidence bound only just reaches it.

### 3.1 Attempt-1 outcomes, all 51 stock draws

| outcome | n |
|---|---|
| `translated` (clean) | 25 (49.0%, [35.9, 62.3]) |
| **`abstained`** | **17 (33.3%, [22.0, 47.0])** |
| `invalid` | 9 |

### 3.2 A second, independent reason this instrument cannot test DC-1

**Haiku abstains on a third of the cohort.** DeepSeek produced a module on all 17 of
these clauses and hit `undeclared-body-name` on all 17; Haiku declines to translate 17 of
51 draws. An abstaining draw never enters the region where the defect can occur, so the
worked example has nothing to act on. Restricting to the 34 non-abstaining draws does not
rescue the design: **3/34 = 8.8%, [3.0, 23.0]** — still under the gate.

This is worse than a low rate. It means arm B could "improve" the endpoint by shifting
draws between *abstain* and *translate* without touching the mechanism DC-1 is about.

### 3.3 Defect classes present at attempt 1 (stock, all 51 draws)

| class | n |
|---|---|
| `undeclared-body-name` | 3 |
| `OTHER:schema-breach` | 3 |
| `unsafe-variable` | 1 |
| `borrowed-without-gloss` | 1 |
| `asp-body-unparseable` | 1 |

Nine error-class instances across 51 draws. The 17 abstentions carry no error class.
**The cohort's defining defect is not what Haiku does on this cohort.**

### 3.4 Baseline route uptake

Draws containing ≥1 body-less ground `ontology` atom: **4/51 = 7.8%, [3.1, 18.5]** —
consistent with the ~7% baseline `TIER_ANALYSIS.md` §8 rank 2 names. Had the gate passed,
this is the number arm B's uptake would have been measured against. It is recorded here so
a future DeepSeek run has a Haiku comparison point, **not** as evidence about DeepSeek.

## 4. The 60%-vs-38% confound — addressed, not inherited

DC-1's supporting statistic is correlational, and the obvious confound is that the model
may choose the ontology route on *easier* clauses. I tested it rather than repeating it.

**First, the observational figure reproduces** on the 100 attempt-1 drafts of the 08-14
pair (this run's scorer, same gate): drafts with ≥1 body-less ground ontology atom are
**6/10 = 60%** first-try against **36%** overall and 33% for the rest. (`TIER_ANALYSIS.md`
says n=15; by this definition it is n=10. The rate matches; the denominator does not, so
the underlying definition differs slightly and the figure should be quoted with its
definition attached.)

**Second, it does not survive clause blocking.** The 51 stock draws give three draws of
each clause, so route choice varies *within* clause. Permuting the route indicator within
each clause block:

| test | estimate | p |
|---|---|---|
| marginal (ignores clause, the form DC-1 cites) | route-users 3/4 = 75% vs non-users 22/47 = 47% | Fisher 0.35 |
| **clause-blocked permutation (route varies within clause)** | **+0.282** | **1.00** |

Only **3 of 17 clauses** are discordant on route choice, so the blocked test has almost no
information — p = 1.00 means *"indistinguishable from chance"*, not *"no effect"*.

**Ruling: the 60/38 split is not evidence that the ontology route causes first-try
success, and must not be cited as support for DC-1.** Route choice and outcome remain two
free model choices on the same call — the same objection `ANALYSIS_REVIEW_verdict.md` DC-2
raised against the "controlled pair", applied to DC-1's own supporting statistic. The
causal question is exactly what the A/B was built to answer, and the A/B could not be run.

## 5. What was NOT done, and why

Per the standing gate — *step 2 proceeds only if step 1 holds*:

* **No A/B was run.** The 102-task arm-A/arm-B design is built and remains unrun.
* **`resolve_runs/graph_v2/node_worked_example.md` is UNMODIFIED.** It is not
  guard-watched and I was permitted to edit it; the pre-registered landing rule says
  nothing lands on a null, and this is weaker than a null — it is an untestable.
* **No diff was written** against `prompt/00_task.md`, `prompt/10_output_format.md`,
  `prompt/20_worked_example.md` or `schema.py`. Confirmed by `git status`.

### 5.1 The draft worked example WAS re-validated, and it passes

Independently re-checked (not taken on trust from `FIXC_REPLICATION.md` §5):

* `DRAFT_worked_example_section.md` contains one module, `l1_170_n028`, which **is** one
  of the 15 pinned `node_corpus.json` sample nodes.
* `checks.run_checks(..., attempt=1)`: **`outcome = translated`, 0 errors, 4 notes** — all
  four head-less situation-input/concept notes that every good example in the file already
  produces.
* `schema.validate_all` returns a module; `render_lp` is non-empty.
* **16 ontology entries, 14 of them body-less ground atoms** — it does demonstrate the
  route it claims to.
* Spliced into `node_worked_example.md` before `## The six bad ones`, it adds a **fifth**
  good module rather than replacing one, and leaves the heading intact — the constraints
  `test_node_worked_example.py` imposes.

The artifact is sound. **The instrument, not the artifact, is what failed.** Materials are
preserved at `fixc_replication/{old,new}_worked_example.md` so the DeepSeek run can use
byte-identical arm-B bytes.

## 6. Verdict

> **DC-1 is UNTESTABLE WITH THIS INSTRUMENT.**

Haiku, on the corpus region and the exact cohort selected because DeepSeek made this
mistake there, reproduces `undeclared-body-name` at 5.9% and abstains a third of the time.
No experiment powered on 51 draws per arm can resolve the removal of a 5.9% class, and the
primary endpoint (attempt-1 clean rate) can move by at most that 5.9% — far inside the
±14pp the design's own confidence interval would carry.

This is a **successful outcome of the protocol**, not a failure of it: the cost of finding
out was 51 free draws instead of a spurious result with a pre-registered p-value attached
to it.

**What is NOT established:** that the worked example is worthless. This says nothing about
whether it works — only that this instrument cannot see. **What IS established:** the
Haiku A/B named as DC-1's next step should not be run, and the 60/38 statistic offered in
its support does not survive clause blocking.

## 7. The measurement that WOULD settle DC-1, and what it costs

**A randomised DeepSeek A/B**, with this document's randomisation (one call per task, ≥3
draws per clause per arm, arms interleaved, clause order shuffled) — never the original's
batching. `deepseek-ai/DeepSeek-V4-Flash-0731`, $0.14 / $0.28 per Mtok.

Sizing (chars/4; arm A system 36,605 chars, arm B 48,770, user mean 2,123, DeepSeek
attempt-1 answer mean 2,424 chars over 88 stored drafts):

| design | calls/arm | total | cost | what it can resolve |
|---|---|---|---|---|
| 3 draws × 17 clauses | 51 | 102 | **$0.18** | target class only, if the drop is near-total |
| 4 draws | 68 | 136 | **$0.24** | 24% → ~5% on the target class |
| **5 draws (powered point)** | **85** | **170** | **~$0.30** | **24% → 8% at 80% power (n≈82/arm by normal approx)** |
| 8 draws | 136 | 272 | **$0.47** | 24% → 10% |
| 10 draws | 170 | 340 | **$0.59** | primary endpoint: ~+15pp on clean rate at 80% power |

The base rate driving the power calculation is DeepSeek's own **24%** — 24 of the 100
attempt-1 drafts in the 08-14 pair carry `undeclared-body-name` (17 with it as the sole
defect). That is 4× the Haiku rate measured here, which is precisely why the instrument
question had to be asked separately for each model.

**Recommendation: the $0.30 five-draw design**, endpoint = the target class; add draws to
$0.59 only if the class rate moves and the clean-rate question becomes live. Against the
recorded ceiling ($8.50, ~$2.15 used) this is affordable, and it is the *only* remaining
route to DC-1 — every free alternative has now been tried.

## 8. Which findings need a DeepSeek A/B before production trust

**Haiku is not `deepseek-ai/DeepSeek-V4-Flash-0731`. Every draw here is evidence about the
INSTRUCTION as read by one model.** Specifically:

| finding | transfers? |
|---|---|
| the 5.9% target rate and the 33% abstention rate | **Haiku-only.** These are properties of this model on this cohort. They justify not running the Haiku A/B; they say nothing about DeepSeek, whose rate is 24% |
| the 7.8% body-less-ontology uptake baseline | **Haiku-only**, and needs re-measuring on DeepSeek before it can serve as arm B's comparison point |
| the clause-blocked null on the 60/38 confound | **partially transfers.** The *reasoning* — route choice and outcome are two free choices on one call — is model-independent and stands. The *measurement* is Haiku's and is weak (3 discordant clauses); it should be recomputed on the DeepSeek draws, where it comes free |
| the draft example's validity | **model-independent.** It is a checker result on fixed bytes |
| **DC-1 itself** | **entirely unmeasured.** No result here supports or refutes it |

## 9. Falsifiers for THIS document

* **If the gate threshold was set too high.** It was pre-registered with its power
  argument, but it is a judgement. The result does not depend on it: at 5.9% with a Wilson
  upper bound of 15.9%, *any* threshold that admits a detectable experiment excludes this.
* **If the abstention rate is a harness artifact** — e.g. the one-shot subagent framing
  ("answer once, do not iterate") pushes Haiku toward abstaining where the live pipeline
  would not. **This is the most likely way this document is unfair to the instrument.**
  Testable for free: re-draw with the abstention instruction emphasised differently and
  compare. I did not do this; it does not change the gate (3/34 among non-abstainers is
  still a fail), but it would change how the 33% is read.
* **If `concepts=None` is the wrong gate.** It is what `translate.py:2557` passes at
  attempt 1, and the harness reproduces the stored DeepSeek verdicts under it.
* **If the cohort is wrong.** Recomputed from the transcripts; reproduces §7's 17 exactly.
* **If 51 draws is too few to establish the rate.** It is enough for the gate — the whole
  confidence interval [2.0, 15.9] sits at or below the threshold.

## 10. Reproduction

In `_debug_gen11/fixc_replication/`: `PREREG_dc1.txt` (pre-registration),
`cohort.py` (cohort), `build_instr.py` (51 tasks, fixed seed), `score.py` (the pipeline
gate), `gate.py` (gate statistic + clause-blocked confound test), `instr/manifest.json`
and `instr/scored.json` (all 51 observations with findings), `instr_gate.txt` (the run
output), `old_worked_example.md` / `new_worked_example.md` (byte-exact arm A/B worked
examples, staged for the DeepSeek run), `DRAFT_worked_example_section.md` (the example
under test), `exp2_manifest_NOT_RUN.json` (the A/B design, still unrun).
