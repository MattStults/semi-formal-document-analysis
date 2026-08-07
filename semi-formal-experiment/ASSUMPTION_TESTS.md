# Minimal tests for the §7 assumptions (A-1 … A-9)

Written 2026-08-06 against `HARNESS_REDESIGN.md` §7 / §7b / §3.4a / §0.0a R4-R6.
**Design only — nothing here has been run and nothing here has spent money.**

Every repo fact below was checked against the named file this session. Where a claim is
inferred rather than verified it is marked ⚠️ *inferred*, per `REPO_TRAPS.md`'s standing
lesson.

---

## 0. The three constraints that shaped every design

**⛔ Money.** `spend.py --status`, run this session:

```
gpt-5.6-luna   459 calls  $1.525
gpt-5.6-sol      1 call   $0.241
Kimi-K3          1 call   $0.223
gpt-5.6-terra    1 call   $0.068
TOTAL          463 calls  $2.057  of $8.50 (24%)
```

`spend.BUDGET = 8.50` (`spend.py:23`). Headroom **$6.44**, and §3.4a says it is an
over-estimate (6 `gpt-oss-20b` artifacts were billed with no usage rows). One frontier
document-pass = $11.28 = 1.75× everything left. $6.44 buys ~330 passage-judgments EVER.

⇒ **The recommended test set spends $0.05.** Every headline result in it is deterministic
re-analysis of data already on disk.

**⭐ Prefer running what exists.** §7b is right that this is the rule, but §7b is **wrong on
one of its three entries** — see the correction to §7b at the end. Two of the three big
un-run items turn out to be already-run (`readback.py`) or already-answerable-offline
(the drift and saturation curves), which is why the free tier is so large.

**Resampling unit.** `HANDOFF.md:1183-1188` rules: *"The resampling unit is the BEHAVIOUR,
not the passage. Between-behaviour SD of the `structural − bag` delta is 0.0596,
between-draw SD 0.0172… **'Sign consistent in 5/5 draws' is worthless evidence**."*

⚠️ **That ruling is scoped to contrasts with a behaviour axis, and four of these nine
assumptions have no behaviour axis at all.** A-1, A-2, A-6 and A-9 are properties of the
corpus, the vocabulary, the renderer and the solver respectively; clustering them "on the
behaviour" is a category error. Each test below names its own unit and says why. Applying
the behaviour rule mechanically where it does not apply would be exactly the repo's
historical failure — a test that measures the wrong thing and passes.

**Precondition T-0 (free, build first).** Verified this session: **no behaviour-clustered
statistics exist in the repo.** `grep -n "cluster\|sign_test\|paired_t\|by_behaviour"` over
`benchmark.py` returns nothing; over `combined.py` only prose. Every contrast the repo has
ever reported is a passage bootstrap, which is the construction §2.2's ⛔ correction
disowns. §8's second amendment already names the coefficient-stability bootstrap as a
**precondition**. Build one ~60-line module: cluster bootstrap over a named unit, paired
t over units, sign test over units. $0, ~1 h. Nothing below that quotes an interval should
run before it exists.

---

## A-1 — re-extraction drift is cheap

### 1. The falsifiable question

⛔ **A-1 as written is not falsifiable and should be rewritten before it is tested.** It
asserts `N × p_drift × p_novel × c_human` is *tolerable*. Three of the four terms are
measurable today; `c_human` has **never been measured anywhere in this project** (§3.4a:
*"no repo artifact records minutes-per-item for any adjudication"*), and "tolerable" names
no threshold. A product with an unmeasured term and no bar cannot be falsified.

**Split it:**

- **A-1a (testable now, free).** Across two independent `annotate.py` passes over the same
  document bytes, `p_drift` = fraction of the 593 clauses whose canonical atom-name set
  differs, and `p_novel` = fraction of drifted clauses whose difference introduces a form
  absent from the other pass's whole vocabulary (i.e. requires a fresh human decision
  rather than a re-alignment). **Falsifiable against a bar fixed before measurement.**
- **A-1b (blocked on an instrument).** `c_human` in minutes per novel decision. Not
  measurable until an adjudication pass records per-item timestamps. See T-A6, which
  supplies it at zero marginal cost.

### 2. What already answers part of it

⭐ **Three complete independent annotation passes over the same document are already on
disk.** Verified from each artifact's `provenance` this session:

| artifact | run_id | batch_size | n_batches | clauses w/ atoms | vocab | coined / reused |
|---|---|---:|---:|---:|---:|---|
| `annotations.json` | `s0-d1ea1a5e` | 14 | 47 | 539 | 330 | 330 / 1093 |
| `annotations_b8.json` | `s0-f542bd84` | 8 | 78 | 587 | 361 | 361 / 1268 |
| `annotations_ext_v1.json` | `s0-c24c4c05` | 6 | 102 | 567 | 650 | 590 / 803 |

All three: `model: gpt-5.6-luna`, `seed: 0`, and **identical
`source_sha256: 8c95f02085548b145468ea45b4c9d99ab6f915e097854fa919dd35b34fd077c0`**. 520
clause ids carry atoms in all three.

⇒ §7 proposes measuring this "on ~30 clauses". **The data for 593 clauses × 3 passes is
already paid for.** Nothing needs to be re-run.

⚠️ Two confounds, both disclosable rather than fatal:
- Batch size differs across all three (14 / 8 / 6), so this is drift under a config change,
  not pure re-run drift. It is an **upper bound**, which is the conservative direction.
- `annotations_ext_v1.json` carries a `docfacts` provenance key the other two lack, i.e. a
  different prompt composition. Treat it as a **separate arm**, not a third replicate.

### 3. The minimal test — T-A1

**Procedure.** For each of the two pairings (`annotations.json` ↔ `annotations_b8.json`
primary; `ext_v1` as the prompt-version arm), for every clause:
1. take the atom-name set from each pass;
2. compute the diff **twice** — raw string identity (upper bound on drift) and after
   `containment.dechain_name` canonicalisation (`containment.py:141`, the polarity-preserving
   key; **not** `grammar.stem_of:234`, which §1.2 records merges `must_x` with `mustnot_x`)
   (lower bound);
3. classify each difference as *re-alignment* (the differing name exists somewhere in the
   other pass's `vocabulary`) or *novel* (it does not).

**Denominator: 593 clauses, not 520.** ⛔ Restricting to the intersection silently drops the
worst cases — a clause with atoms in one pass and none in the other (`coverage` records 54
such clauses for `annotations.json` alone) is **maximal** drift. "No atoms" is a valid state
and must be counted.

**Resampling unit: the SECTION.** Not the behaviour (no behaviour axis) and not the clause.
Batches are section-aligned — the `plan` field in every provenance record is a list of
`{request, section, clauses}` — so clauses within a section share a prompt context and their
drift is correlated. A clause-level interval would understate variance. Cluster-bootstrap
over the ~15 sections in `modelspec_clauses.json`.

**Decision rule, fixed before looking.** A-1a survives iff the expected novel-decision count
`593 × p_drift × p_novel ≤ 40` on the **upper-bound (raw string)** diff — 40 being one
adjudication sitting at any plausible rate. Report the number either way; do not move the
bar after seeing it.

### 4. Cost

**$0.** ~2 h to write the differ and the report (shared with T-A2 — one data pull covers both).

### 5. What would falsify it

`p_drift × p_novel > 0.0675` on the 593-clause denominator, i.e. more than 40 fresh human
decisions per re-extraction. Given the bank has no corpus-version binding (G-k), that would
also mean every re-extraction orphans part of the constraint bank.

### 6. Runnable today

**Yes, entirely, with data already paid for.**

### ⚠️ Could this pass while A-1 is false?

**Yes, one way, and it is designed out above.** If drift is measured *only* after
canonicalisation, semantically identical re-coinings collapse and `p_drift` reads low while
a human still has to adjudicate every one of them. That is why the **decision** uses the raw
upper bound and the canonicalised figure is reported as context. A second hazard —
name-identity treating `user_harm` / `harm_to_user` as drift — inflates the number, which
fails safe.

**Residual it cannot reach:** a same-batch-size replicate. If the upper bound lands near the
bar, one more `annotate.py` pass at `batch_size=14` prices at **$0.45** (47 cheap batches,
§3.4a) and settles it. Recommend only if T-A1 is ambiguous.

---

## A-2 — distinct canonical atom forms saturate

### 1. The falsifiable question

Let `F(n)` be distinct canonical atom forms after `n` clauses. Saturation ⇒ the marginal
coining rate declines: Heaps exponent β < 0.75 **and** the last-100-clause coining rate
below 40% of the first-100 rate.

### 2. What already answers part of it

⭐ **The curve is literally in the provenance.** Every artifact's
`provenance.vocabulary.per_batch` is an ordered list of
`{batch, clauses, atoms, coined, reused, aliased, rejected, truncated}` — 47, 78 and 102
points respectively. Headline `reuse_rate` is recorded too: **0.7681** for
`annotations.json`.

**And the three arms already disagree, which is the finding.** Coined/reused: 330/1093
(reuse 0.77) · 361/1268 (0.78) · **590/803 (0.58)**. The extended-prompt arm coins nearly
twice as many forms for fewer reuses and ends at a 650-name vocabulary. ⇒ *"forms saturate"*
is **arm-dependent**, and any answer must name the prompt it holds for.

### 3. The minimal test — T-A2

**Procedure.** Three curves per artifact:
- **observed** `F(n)` in processing order, straight from `per_batch`;
- **permutation control** — recompute `F(n)` over 200 seeded random clause orderings using
  the fixed per-clause atom sets from `by_clause`. This is the **concept-space** curve;
- their divergence is the **pipeline** effect.
Then fit β on both, and report `provenance.carried_atoms_evicted` alongside.

⭐ **Why the permutation control is not optional.** `annotate.py` carries the accumulated
vocabulary into each batch's prompt, and provenance records a `carried_atoms_evicted`
counter. If carried atoms are evicted, late batches **cannot reuse what they cannot see**,
so the observed coining decline may be a context-window property rather than a concept-space
one. Without the control, T-A2 measures the prompt.

**Denominator:** 593 clauses × 3 arms.
**Resampling unit:** the **permutation** (n=200) for the concept-space curve. Across arms
the unit is the **pass**, n=3 ⇒ report three curves, make no significance claim. (§2.6
defect 3 and `REPO_TRAPS.md` #11 both record what n=3 does in this repo.)

**Decision rule.** Saturation holds iff, on the permuted curve, β < 0.75 **and**
last-100 rate < 40% of first-100 rate, in ≥2 of 3 arms.

### 4. Cost

**$0.** ~1 h on top of T-A1's data pull.

### 5. What would falsify it

β ≥ 0.75 or last-decile ≈ first-decile: forms keep arriving at near-constant rate ⇒ no
saturation ⇒ vocabulary build cost is linear in document size and A-8/H-7 are unbounded.

### 6. Runnable today

**Yes.**

### ⚠️ Could this pass while A-2 is false?

**Yes, and the scope limit must ship with the result.** Saturation on *this* document says
nothing about a *new* document. §1.2's own consequence: *"atoms derive from behaviour
definitions, never from documents. A new document contributes no new concepts on arrival;
its unanticipated content is visible only as a miss."* A pass here certifies
**within-document** saturation only. It must never be quoted as "the vocabulary saturates."

---

## A-3 — the extraction seat holds under the small-model standard in clingo notation

### 1. The falsifiable question

On the same brief and the same input batches, a small model and a frontier model produce
clingo-notation extractions that are indistinguishable, blind, at a pre-registered
equivalence margin on (i) validator acceptance rate and (ii) per-clause fact-set agreement.

### 2. What already answers part of it

**Very little, and less than it looks.** `calibration.json` records one batch each for
`sol` / `terra` / `luna` / `kimi`, all `ok: true`, all `parses: true`, none truncated. That
establishes **parseability at n=1 batch on the annotate prompt** — not agreement, and not on
a clingo fact schema.

`CLAUDE.md` states *"the adjudication seat is proven at small-model/frontier parity"* — a
**different seat**. Do not transfer it.

### 3. ⛔ The blocking problem: the seat does not exist

**There is no clingo-notation extraction brief.** `briefs/` has no such entry;
`behavior_atoms_notation_prompt.md` is notation for behaviour atoms, not the fact schema;
and §8's own list carries *"Design the fact schema in clingo (§4's remaining task)"* as
**outstanding**. §7 asks whether a seat holds before that seat has been specified.

⇒ **A-3 is not testable today, and testing it now would measure a brief we have not
written.**

### 4. The cheapest informative substitute, priced so the choice is explicit

Once the schema exists: paired frontier-vs-small extraction on the same batches, blinded.
`sol` = $0.24/batch measured, `luna` = $0.0096/batch.

| n batches | frontier | cheap | total | share of $6.44 |
|---:|---:|---:|---:|---:|
| 3 | $0.72 | $0.03 | **$0.75** | 12% |
| 8 | $1.92 | $0.08 | **$2.00** | 31% |

**Resampling unit: the batch.** At n=3 a sign test's best possible outcome is p = 0.25 —
**unpowered by construction**, and §2.6 defect 3 forbids exactly this shape. n=8 is the
smallest that can reach p < 0.05 on a clean sweep. **Recommendation: do not run at n=3.**
n=8 is affordable but costs a third of everything left; that is Matt's call, not a default.

**Decision rule (for when it runs):** frontier−small fact-set agreement ≥ pre-registered
margin on ≥ 7 of 8 batches (sign test p = 0.035).

### 5. What would falsify it

Small-model agreement below the margin on ≥2 of 8 batches. Per `CLAUDE.md`, that is *"a seat
defect, not a model failure"* — so a failure is a **brief-rewrite trigger**, and the test
should be pre-registered as such.

### 6. Runnable today

**No.** Blocked on §8's fact-schema task.

---

## A-4a — the §4 port reproduces the current scorer

### 1. The falsifiable question

For every (clause, cell) in the frozen benchmark set, the ported implementation returns the
current scorer's raw per-clause score at recorded precision **and** an identical predicted
set.

### 2. What already answers part of it

Nothing — the port does not exist. But the reference machinery does:
`snapshot.py` + `snapshots/` + `dossier.py`'s stale-sha guard, and `test_snapshot.py:125-127,
:170-172` already enforce **cross-process** determinism under a different `PYTHONHASHSEED`
(`REPRODUCIBILITY.md`'s named requirement).

### 3. The minimal test — T-A4a

This is a **unit test, not an experiment**. No sampling, no CI, no resampling unit.

**Denominator:** all 593 clauses × all 18 `--panel-v2` cells = 10,674 comparisons.
**Decision rule:** exact set equality **and** `|Δraw| = 0` at recorded precision. One
mismatch fails.

⛔ **The set check alone would pass while the port is wrong.** Otsu is a data-dependent cut
over the positives-only score distribution (`relevance.py:806-808`, `REPO_TRAPS.md` #8), so
two *different* score vectors routinely yield the *same* predicted set. This is precisely
why §4's gate correction says **raw + sets**. Ship both or the gate is decorative.

### 4. Cost

**$0.** Test runtime is minutes. The harness can and should be written **before** the port,
so the port is developed against a red gate (`feedback-verify-red-before-fix`).

### 5. What would falsify it

Any nonzero raw delta or any set difference.

### 6. Runnable today

**Harness: yes. Test: no** (no port to run it against).

---

## A-4b — is §0.0's lexicographic grade usable output?

### 1. The falsifiable question

Two separable questions were bundled here; only one is a measurement.

- **A-4b-i (measurable, free, today).** Does any candidate default ordering place the
  expert's named core passage first among its behaviour's predicted set?
- **A-4b-ii (not a measurement).** Shown one worked derivation with its grade and interp
  tags, does it settle the §0.0b expert's question? **n=1, and it is an interview.** Run it —
  it is the product question and it is free — but do not schedule it as a test or report it
  as evidence.

### 2. What already answers part of it

R4 (§0.0a) already specifies A-4b-i and calls it *"offline, zero spend, runnable now"*. The
data is `expert_salience.json`, read this session: 4 anchors, dated 2026-08-04, described as
*"the FIRST human-expert relevance signal in this project; everything prior is
model-measuring-model,"* with `usage_rules` forbidding any fitting to them.

⛔ **The effective denominator is 3, not 4.** The `how-to-approach-tradeoffs` anchor has
`expert_core_passage_starts: null` — there is no named core, so it cannot be scored on a
rank-1 criterion. It can only support the weaker *"the initial strongest expression should
outrank the others"* check. §7 should say 3.

R4 also supplies the mechanism: `kind` is on **all 593 clauses** in
`modelspec_clauses.json` (conditional 188 · example 183 · definitional 84 · meta 72 ·
holistic 66), `RelevanceIndex` already consumes it, and R4's ⛔ guard forbids salience from
*dropping* examples (39.1% of relevance-weighted hits).

### 3. The minimal test — T-A4b

**Procedure.** For each of the 3 scorable anchors, take the existing predicted set and
re-order it under each candidate default (kind-salience order; section-election rank;
raw score; and R4's `in_example_block` + section co-membership proxy for the missing
`illustrates` edge). Report the rank of the expert's core passage under each, plus the
guard check that **the set is unchanged** under every ordering (R4 guard 1: a sort that adds
or drops is a hidden filter).

**Denominator:** 3 anchors.
**Resampling unit:** the **anchor**, n=3. No interval is reportable.

**Decision rule — asymmetric, and pre-registered as such.**
⛔ **A positive result here is not reportable.** With 3 anchors and ≥4 candidate orderings,
the chance that *some* ordering wins ≥2/3 by luck is large. Only the **negative** is a
result: if no candidate ordering places any core passage first, R4's premise is wrong and
R4 says so itself.

### 4. Cost

**$0**, ~2 h. A-4b-ii: $0, one conversation.

### 5. What would falsify it

No candidate ordering ranks any expert core passage first — or an ordering that ranks it
first while **changing the set**, which fails R4 guard 1 and is a worse outcome than a miss.

### 6. Runnable today

**Yes** (R4 already declares it so).

---

## A-5 — the reclassification generalizes past one design's reviews

### 1. The falsifiable question

Applying the same closed four-bucket rubric (`INEXPR` / `EXPR-UNVER` / `PROCESS` / `DOC`),
**blind to the S3B tally**, to a different design's adversarial review record yields
`INEXPR` ≤ 10% of occurrences in ≥3 of 4 reviews.

### 2. What already answers part of it

`S3B_FINDING_RECLASSIFICATION.md`, read this session: `INEXPR` **0** · `EXPR-UNVER` 13 ·
`PROCESS` 15 · `DOC` 6 over 34 occurrences, with three corrections applied (BL-4's miscount,
both `INEXPR` rows reclassified per the F2 retraction, S-7 moved to `PROCESS`) and its own
disclosure that *"34 is a subset, not the full record."*

⚠️ **And §0.1's precondition is unmet.** That file states: *"Classified by me, with a stake
in the answer… This classification should be re-run by a clean context before it is used to
authorise or cancel a migration."* §8's outstanding list carries the re-run on the full ~54
occurrences as *"the only genuinely outstanding item."* ⇒ **the baseline arm of A-5 is not
yet trustworthy**, and the clean re-run is a precondition, not a companion.

Untouched review records available as the second arm (line counts verified):
`S4_ADVERSARIAL_REVIEW.md` (317) + `_R2` (216) · `S5_ADVERSARIAL_REVIEW.md` (193) ·
`S6_ADVERSARIAL_REVIEW.md` (244) · `IMPLIED_EFFECTS_ADVERSARIAL_REVIEW.md` (491) ·
`INDEX_BUILDER_REVIEW.md` (290).

### 3. The minimal test — T-A5

**Procedure.** Two independent classifiers under the existing two-coder protocol
(`briefs/blind_coder.md` — reuse it, do not invent a method), each receiving the rubric
definitions plus the review *bodies*, and **not** receiving
`S3B_FINDING_RECLASSIFICATION.md`, `HARNESS_REDESIGN.md`, or any tally. `CLAUDE.md`:
*"A cycle's own design document is never seat material."*

**Denominator:** every finding body in S4 + S4_R2 + S5 + S6 — **counted and frozen before
classification begins** (`CLAUDE.md`: never pin a live count; freeze the input instead).

**Resampling unit: the REVIEW DOCUMENT (n=4).** Not the finding. Findings inside one review
are correlated by construction — S3B's own tally counts recurrences (E-2 = prior M-2, S-3 =
prior M-3, S-4 = prior M-4) as separate occurrences because each cost a review round. Report
per-review `INEXPR` share.

**Decision rule.** A-5 holds iff `INEXPR` ≤ 10% in ≥3 of 4 reviews **and** inter-coder
agreement ≥ 80%. Below 80% the rubric is the defect and the result is void.

### ⚠️ Could this pass while A-5 is false? — YES, and this is the one that needs a control

`INEXPR` is defined as *"was the fix stateable in the representation that existed."*
Adversarial reviewers, as a genre, **name a fix**. So `INEXPR ≈ 0` may be a property of
review-writing rather than of this representation, and the test would pass on any corpus of
reviews about anything.

⛔ **Mandatory positive control:** seed the input with 3 synthetic findings whose fix is
genuinely unstateable in the current representation (candidates are easy — anything needing
a relation the ontology has zero of, e.g. a cross-kind `entails`, or the `illustrates` edge
R4 records as missing, H-5). If the coders do not classify those 3 as `INEXPR`, the
instrument is blind and the null means nothing. **Do not run T-A5 without the control.**

### 4. Cost

**$0** API (agent time only), ~4 h including the control construction.
Precondition: the clean-context S3B re-run (~2 h, $0).

### 5. What would falsify it

Any review with `INEXPR` > 10%, or coder agreement < 80%, or a failed positive control
(which voids rather than falsifies).

### 6. Runnable today

**Yes, after the §8 clean-context S3B re-run and the control.**

---

## A-6 — blind quality judgments correlate with document truth

### 1. The falsifiable question

`readback.py`'s model-judged `faithful` / `sufficient` verdicts agree with a human reading
the same (source clause, render) pair at ≥ 0.80, with a 95% cluster interval excluding 0.70,
and their disagreements are not systematically one-directional.

### 2. What already answers part of it

⛔ **§7b is wrong that `readback.py` is un-run.** It has run, live, and its artifact is on
disk. From `readback_results.json` `provenance`, read this session:

```
model: gpt-5.6-luna   live: true   created: 2026-08-02T10:31:36
n_clauses: 125   per_kind: 25   seed: 20260802   errors: 0
conditions: random_N4, random_N10, section_N4, section_N10
```

Computed from the artifact this session:

| measure | pre-registered | **measured** |
|---|---:|---:|
| FAITHFUL | ~0.90+ | **0.456** |
| SUFFICIENT | ~0.35 | **0.160** |
| identity ceiling (whole corpus) | — | 0.9174 (544 classes / 593) |
| gloss echo rate | — | 0.0034 (2 of 593) |

⭐ **§7 quotes only the sufficiency collapse. The faithfulness miss is the more alarming
number and it is the one that points straight at A-6.** `readback.py`'s design argument is
that the renderer is mechanical and therefore *cannot invent* — yet the judge called 54% of
renders unfaithful. Either the argument is wrong, or the judge is over-calling. **That is
exactly the question A-6 asks, and it is now a concrete, sampled, on-disk question rather
than an abstract worry.**

⇒ Also note the **exposure is half what §7 implies**: `DISCRIMINABLE` has objective ground
truth (`answer_index` is recorded per trial), so it is model-*answered*, not model-*judged*.
A-6's real surface is `faithful` + `sufficient` only.

`REPO_TRAPS.md` #5 is confirmed at source (`readback.py:45`, *"three measures, judged by a
cheap model"*) — the promotion of A-6 to load-bearing is correct.

### 3. The minimal test — T-A6

⭐ **The cheapest high-value test in the set, and it needs no new model call.**

**Procedure.** Every one of the 125 `fidelity_trials` already carries `clause_id`,
`clause_kind`, `section_id`, `source_text`, `render`, and the model's verdict **with its
itemised `unsupported` / `missing` lists**. So the human is *checking specific assertions*,
not redoing the task. Draw 30 trials, stratified 6 per `clause_kind`, seeded, **drawn before
anyone reads them**. Human records: the two booleans, plus agree/disagree on each listed
`unsupported` and `missing` item.

**Denominator:** 30 trials for boolean agreement; separately, the total count of listed
items across those 30 for item-level agreement. **Report both; never pool them** — one
trial can carry 5 items and would silently dominate.

**Resampling unit: the CLAUSE, clustered on SECTION.** Not the behaviour — readback has no
behaviour axis. Section clustering because renders of neighbouring clauses share vocabulary
and section context; `section_id` is on every trial.

**Decision rule.** A-6 survives iff `sufficient` agreement ≥ 0.80 with the 95% cluster
interval excluding 0.70, **and** a sign test on directional disagreement does not reject at
0.05. `sufficient` is the one to gate on: at 0.16 it is a floor-level reading, which is
exactly where a judge artifact hides.

⭐ **Bolt A-1b onto this at zero marginal cost.** `responses.jsonl` already carries a `date`
field; per-item start/end timestamps are one more column. §3.4a: *"the next adjudication
pass should record a start and end timestamp per item… Until it exists, the loop's cost
model is missing its dominant term."* **T-A6 is that pass.** 30 timed items is the first
`c_human` measurement the project has ever had.

### 4. Cost

**$0** API. Human: 30 items, duration unknown — which is the point.

### 5. What would falsify it

Agreement ≤ 0.70, **or** one-directional disagreement (model says "insufficient" where the
human says the render is adequate). The second outcome is the important one: it would mean
0.16 is an **instrument reading of the renderer's terseness**, and the harness's core signal
(§3.1) is measuring its own rendering conventions rather than the ontology.

### 6. Runnable today

**Yes, entirely. Nothing needs to be built or bought.**

### ⚠️ Could this pass while A-6 is false?

**Yes, one way.** A human shown the model's `unsupported`/`missing` lists is **anchored** —
agreeing is the low-effort response, so agreement is biased up. Fix, and it is cheap: on
10 of the 30 items (a pre-registered third, seeded), present the pair **without** the
model's lists and have the human generate their own; compare unanchored agreement to
anchored. If the two differ materially, only the unanchored arm is quotable.

---

## A-7 — oracle self-consistency `p`

### 1. The falsifiable question

Presented the same item twice, separated and re-randomised, the human oracle returns the
same verdict with probability `p`. ExPairT's Theorem 5 guarantees hold for `p > 0.5`.
Falsifiable: the Wilson lower bound on `p` exceeds 0.5.

### 2. What already answers part of it

**Nothing.** `RELATIONAL_TURN_DECISIONS.md` O2: *"we currently assume rather than measure."*
No duplicate items exist.

What *is* on disk (`human_adjudication/`, read this session):
`manifest.json` = seed 20260805, 32 disagreement + 8 anchor items, `reserved_pool_size:
1571`, protocol `HUMAN_ADJUDICATION_PROTOCOL.md`. `responses.jsonl` = **10 rows, of which 6
are items** (H001-H006) and 4 are followups.

⭐ **And the 6 carry a number more urgent than `p`.** Verdicts: `unclear` ·  `unclear` ·
`not_a_valid_item` · `not_relevant` · `relevant` · `relevant`. **Three of six items did not
yield a usable verdict** — H001 is annotated *"PROTOCOL DEFECT, not a judgement… Item
burned"*, H002 *"INTERPRETATION CANDIDATE"*, H003 `not_a_valid_item`. The **item-validity
rate is ~50%**, and it is not what A-7 measures. Any A-7 sample must be sized on *usable*
verdicts, so 20 usable duplicates means drawing ~40 items.

### 3. ⛔ A-7 is mis-priced in §7

§7 calls it *"the cheapest test in the set."* **In dollars, yes — $0. In the currency that
is actually scarce, it is the most expensive thing on this list.** §3.4a: human throughput
is the loop's rate limit and has never been measured, and the project's entire recorded
human-adjudication history is **6 items**. A-7 needs ~40-80 presentations. Rewrite the §7
cell to say *"free in dollars; the largest human-time ask in the set."*

### 4. The minimal test — T-A7

**Take §4e's advice and change the seat first.** Ask *"does behaviour B bear more on passage
X or on passage Y"* rather than *"is X relevant to B."* §4e's four recorded reasons: it is
the form ExPairT's `p` is defined over; it emits **ranking** constraints (C2, and §0.0b's
endorsed axis); it is cheaper per judgment; and it is *"the strongest cheap move available."*
It also sidesteps the H001 protocol defect, since a pairwise comparison is answerable
without the full-document context an absolute-relevance question needed.

**Procedure.** Build 20 pairwise items from the 1,571-item reserved pool via
`build_adjudication_sample.py`. Present each **twice**, with:
1. **≥8 intervening items** between the pair, and where possible **≥1 day**;
2. **X/Y order flipped** on the repeat — without this, position bias reads as consistency;
3. a **recognition check** on the repeat (*"have you seen this item before?"*), analysed as
   a separate stratum;
4. per-item timestamps (same column as T-A6).

**Denominator:** 20 duplicate pairs.
**Resampling unit: the ITEM (n=20).** Wilson interval on `p`.

**Decision rule, with its power stated honestly.** A-7 holds iff the Wilson lower bound on
`p` > 0.5. **At n=20 that requires p̂ ≥ 0.75.** To distinguish `p = 0.65` from `p = 0.5` you
need n ≈ 60, which is 120 presentations and is not affordable in human time. ⇒ Pre-register
that this test can only separate *"clearly usable"* from *"not established."* It cannot
certify `p ∈ (0.5, 0.75)`, and a result in that band must be reported as **inconclusive**,
not as a pass.

### 5. Cost

**$0** API. Human: 40 presentations, ideally across two sittings on different days.

### 6. What would falsify it

Wilson lower bound ≤ 0.5. Consequence: ExPairT's guarantees do not apply, and §0.0's
oracle-facts-only input channel has no foundation. R1's residual (*"if the same oracle under
the same assumptions adjudicates a case both ways, that is oracle inconsistency"*) becomes
the live failure mode.

### 7. Runnable today

**Yes** — the pool, the sampler and the protocol all exist. Only the pairwise prompt is new,
and §4e specifies it.

### ⚠️ Could this pass while A-7 is false? — YES, and this is the most fakeable test here

**A within-session repeat measures short-term memory, not oracle stability.** If Matt
remembers item 3 when it reappears as item 12, `p` inflates toward 1.0 and the test passes
on an oracle that is not stable at all. The three mitigations above (order flip, day
separation, recognition check) are **not optional refinements — without the recognition
check a high `p` is uninterpretable**, because there is no way to tell consistency from
recall. If recognised items show materially higher agreement than unrecognised ones, only
the unrecognised stratum is quotable, and the sample must be enlarged.

---

## A-8 — document-derived vocabulary is achievable at acceptable cost

### 1. The falsifiable question

⛔ **A-8 as written prices the wrong half of its own problem, and its dollar question is not
falsifiable.** §7 says *"cost of one extension pass."*

**What §1.2 already establishes** (verified against the frozen artifact
`vocab_gap/shape_partition.json` as reported in §1.2, and `shape_partition.py` +
`test_shape_partition.py` exist):

| shape | n of 26 | meaning | licensed fix |
|---|---:|---|---|
| `shape_b` | **14** | concept EXISTS clause-side; no query reaches it | **re-selection; adding atoms is FORBIDDEN** |
| `shape_a` | 10 | atomized nowhere | add clause-side atoms |
| `shape_a_polarity_variant` | 2 | where `grammar.stem_of` would have inverted the call | add, with the polarity-safe key |

⇒ **Over half the measured "vocabulary gap" is a query-side selection failure that document
extraction cannot fix by construction.** Pricing an extension pass answers nothing about
those 14. And the extension question itself is unfalsifiable as posed: 12 clauses is ~1
batch, so *"acceptable cost"* is $0.01 cheap / $0.24 frontier, and **nothing plausible would
falsify it**. A test with no falsifier is not a test.

**Rewrite A-8 as:** *(a) what fraction of `shape_b` misses does re-selection from the
existing index recover, and (b) does the `shape_a` extension change any query outcome?* (a)
is free and is the larger half; (b) is the only part that costs money and the only part that
can fail.

### 2. The minimal test — T-A8

**Procedure (part a, the one to run).** For each of the 14 `shape_b` clauses: enumerate the
atoms already recorded on it in `annotations_b8.json`; check whether any is reachable by the
missed behaviour's query under the existing selection rule; and if not, whether **any**
selection from the existing 361-name index would reach it. The third is a **computed
ceiling**, not a fit — it must be derived without consulting whether it improves MCC, or it
becomes a fitting channel (invariant 9).

**Denominator:** 14 clauses.
**Resampling unit:** the **behaviour** the clause was missed for (this is the one assumption
where `HANDOFF.md:1183`'s rule applies directly). n is small ⇒ **report counts, not
intervals**.

**Decision rule.** Report the reachable fraction. That number re-prices H-7 directly: a high
fraction means the "vocabulary gap" is mostly a selection bug and document-derived
vocabulary is not on the critical path; a low fraction means extraction really is the
binding constraint.

**Part (b), only if part (a) returns a low fraction.** One extension pass over the 12
`shape_a` + polarity clauses, ~1 batch, **$0.01 cheap / $0.24 frontier**. ⚠️ Its readout must
not be MCC at n=9 behaviours — that contrast is behaviour-clustered and underpowered (§2.2's
correction). The readout is binary and mechanical: *do the 12 clauses become reachable?*

### 3. Cost

**$0** for part (a), ~2 h. **$0.01-$0.24** for part (b).

### 4. What would falsify it

Part (a): a reachable fraction near zero would mean re-selection cannot recover `shape_b`
misses either, so §1.2's reweighting of A-8 "in the direction that makes them cheaper" is
wrong and the gap is larger than recorded.

### 5. Runnable today

**Yes** for part (a) — `shape_partition.py` is built, tested, and its output frozen.

---

## A-9 — grounding is tractable at corpus scale

### 1. The falsifiable question

⛔ **A-9 is mis-stated in the most dangerous way on this list: "ground the corpus, measure"
names the wrong cost, and a test built on it would pass while the assumption is false.**

Verified at source: `emit_asp.py`'s docstring emits *"a choice rule `{ ctx(A) }.` per
unconstrained context atom"*, and `run_conflicts.brave_conflicts` runs
`clingo.Control(["--enum-mode=brave"])` over **all answer sets**, then `witness()` runs a
**separate `--opt-mode=optN` solve per conflict**. ⇒ The scenario space is `2^|unconstrained
ctx|` by construction. **Grounding can be polynomial while enumeration is exponential** — a
grounding-size measurement would come back green on a program that cannot be solved.

**Restate as a triple, all three pre-registered:** at corpus scale, (i) grounded program
size, (ii) count of answer sets to a complete brave closure, (iii) wall-clock to that
closure plus the per-conflict witness solves — all under declared caps.

### 2. What already answers part of it

- G-f records that **no size/time guard exists** in `emit_asp.py` / `run_conflicts.py` /
  `run_chain.py`. Confirmed — no timeout or model-count cap appears in either.
- ✅ **`clingo 5.8.0` is installed in `.venv`** (verified by import this session). `CLAUDE.md`
  calls it optional; for *this machine* that is stale, though G-i's CI point stands.
- **Corpus scale has never been approached.** `smoke_extraction.json`, read this session:
  **4 atoms, 2 rules, 1 incompat, 0 exclusions, 40 unencoded**. That is ~2 orders of
  magnitude below the target.

### 3. The minimal test — T-A9

**No extraction needed, so no spend.** A synthetic scaling curve.

**Procedure.** Generate extractions parameterised by `(n_rules, n_ctx_atoms, n_defeaters,
n_incompat, exclusion_density)`, calibrated to `smoke_extraction.json`'s ratios and to the
corpus's rule-bearing population — `modelspec_clauses.json` `kind` counts give
**conditional = 188** as the target `n_rules`. Run `emit_asp.py` → `run_conflicts.py` at
`n_rules ∈ {4, 8, 16, 32, 64, 128, 188}`, recording the triple at each point under a hard
per-point timeout.

**Denominator:** the scaling grid.
**Resampling unit: the generated INSTANCE (5 seeded instances per grid point).** Structure
matters more than size here, so report **median and max** — for a guard, the max is the
number that matters.

**Decision rule, pre-registered before the first run.** A-9 holds iff at `n_rules = 188` the
**median** instance completes brave closure in < 60 s within < 2 GB. Both caps fixed in
advance.

⚠️ **Sweep exclusion density, and headline the 0% arm.** A generator that happens to emit
heavily constrained programs finds grounding easy and A-9 passes on a corpus that is
actually loose. `smoke_extraction.json` has `exclusions: 0`, so **0% is the honest default**
and must be the headline arm; higher densities are the optimistic ones.

### 4. Cost

**$0.** ~4 h to build the generator; the runs themselves are bounded — cap each grid point at
120 s, so the whole sweep is under 30 min of local CPU. (Well inside the "no heavy local
compute" rule; nothing here saturates cores for long.)

### 5. What would falsify it

Timeout or memory blowup at any `n ≤ 188` in the median instance.

⭐ **And a falsification here is a design result, not a bug.** It would say the harness needs
`at_most_one` exclusion structure as a **requirement** rather than an option, and that G-f's
guard must be a **refusal** — the same shape as §3.4a's budget rule: *refuse, never
truncate*, because a truncated enumeration silently changes the denominator.

### 6. Runnable today

**Yes.** `clingo` is installed, both entry points exist, nothing is bought.

---

## Extra: T-ONT — the un-run ontology annotated pass (§7b's ⭐ item)

§7b calls this *"the single most on-target un-run experiment in the repo."* It is cheap and
it should run — but **not with the readout §7b implies**.

**What is verified.** `ontology.py`'s annotated path (`run_annotation_pass`, `--live`) is
built, priced at *"~$0.04, once per spec"* in its own docstring, and defaults to a dry run.
`estimate_cost` prices 4 passes over the 361-atom vocabulary. The mechanical baseline is a
pinned null: `contrary_negation` **0** (22 atoms carry `avoid_`, not one has its un-negated
partner in the vocabulary), `entails_nominalisation` **0** (all 361 names have exactly one
kind, so no act/situation pair exists to bridge), `contrary_antonym` 1,
`subsumes_name_tokens` 14 — 20 edges over 361 atoms.

⛔ **But `ontology.main()` prints its own warning, and it must be carried:** *"the annotated
pass below is NOT a justified fix: relation expansion was measured to HURT the query on
every behaviour. See `structural.CONSTANTS['max_hops']`."* Verified at
`structural.py:502-513`: `max_hops = 0`, *"relation expansion was MEASURED TO HURT — one hop
degrades precision on all three behaviours (.348→.309, .850→.631, .433→.367) and passage MCC
from +0.123 to +0.088."* And `structural.py:322` records the gate as **SUSPENDED**: *"+0.340
is DRAW0, the MAXIMUM of a 5-draw spread… re-derive per behaviour with the correct noise
floor before gating anything on it."*

⇒ **Do not read this experiment out as query MCC.** That contrast is behaviour-clustered,
n=9, underpowered, and gated on a suspended number. It would be the repo's canonical mistake
one more time.

**The readout that is actually informative, and it is binary.** Does the annotated pass
produce **non-zero `contrary` edges and non-zero cross-kind `entails` edges that survive
`validate`?** Those are precisely the two relations the mechanical path fired **zero** times,
and `entails` is the only relation licensed to cross kinds — the thing that stops the type
discipline from being a wall. If the annotated pass returns zero of both, the relation layer
is empty on this vocabulary by two independent derivations, and that is a strong, clean,
$0.04 finding for the logic goal. If it returns a useful count, the relation layer is a live
option and *then* an MCC contrast can be designed properly.

**Cost: $0.04** (4 luna calls). **Falsifier:** zero surviving `contrary` and zero surviving
cross-kind `entails`. **Runnable today: yes** — `--live` is the only flag needed.

---

## The ranking

### Tier 1 — run now. $0, offline, all reportable this week.

| # | test | what it buys | cost | time |
|---:|---|---|---:|---|
| 1 | **T-0** clustered-stats helper | precondition for every interval below; a named §8 item | $0 | 1 h |
| 2 | **T-A1** drift / novelty, 3 passes × 593 clauses | the first real `p_drift`/`p_novel`; §7 asked for 30 clauses, we have 593×3 already paid for | $0 | 2 h |
| 3 | **T-A2** saturation curves + permutation control | shares T-A1's data pull; already shows an arm-dependent answer (reuse 0.77/0.78 vs **0.58**) | $0 | 1 h |
| 4 | **T-A9** grounding **and enumeration** scaling | could kill or confirm the clingo commitment **before** anything is built on it; supplies G-f's missing guard | $0 | 4 h |
| 5 | **T-A6** readback judge vs human, 30 items, **timed** | A-6 is the load-bearing one, the data is on disk, and the timing column closes §3.4a's missing human term | $0 | human |
| 6 | **T-A4b-i** R4 salience ranking probe | R4 already declares it runnable now; negative-only | $0 | 2 h |

**Why this order.** T-A1/T-A2/T-A9 are pure re-analysis with no human in the loop, so they
produce reportable numbers on Matt's schedule rather than on his availability. T-A6 needs
him but is the highest-value single item in the set: it is the assumption `REPO_TRAPS.md` #5
promoted to load-bearing, its input is already bought, and it doubles as the project's first
`c_human` measurement. T-A9 is placed high because a falsification there changes the design
rather than a number.

### Tier 2 — run next. $0.05 total.

| # | test | cost |
|---:|---|---:|
| 7 | **T-ONT** ontology annotated pass, binary contrary/entails readout | **$0.04** |
| 8 | **T-A8(a)** `shape_b` re-selection reachability (14 clauses) | $0 |
| 9 | **T-A7** pairwise duplicate consistency, 20×2, order-flipped + recognition check | $0, human |
| 10 | **T-A8(b)** `shape_a` extension, 12 clauses — only if 8 returns low | **$0.01** |

T-A7 sits here rather than Tier 1 only because it is a second human sitting and wants a day's
separation from T-A6 by design. If Matt has appetite for two sessions, promote it — it is the
assumption the whole convergence order rests on.

### Tier 3 — needs a precondition first. $0.

| # | test | precondition |
|---:|---|---|
| 11 | **T-A5** blind reclassification of S4/S5/S6 | §8's clean-context S3B re-run, **and** the 3-finding positive control. Without the control it is not a test. |

### ⛔ Not worth testing yet, with reasons

- **A-3** — the seat does not exist. There is no clingo-notation extraction brief in
  `briefs/`, and §8 still carries *"design the fact schema in clingo"* as outstanding.
  Testing now would measure a brief we have not written. And when it does run, the
  affordable sample (n=8 batches, **$2.00 = 31% of everything left**) is the *minimum*
  powered design — n=3 at $0.75 is unpowered by construction and must not be run as a
  compromise.
- **A-4a** — no port exists. Build the equality harness (raw **and** sets) alongside the
  port so the port is developed against a red gate; it is a unit test, not an experiment,
  and it needs no place in a ranking of measurements.
- **A-4b-ii** — do the interview, it is free and it is the product question, but it is n=1
  and must not be scheduled or reported as a measurement.
- **A-8's dollar half** — nothing plausible falsifies "one 12-clause pass is affordable."
  Not a test. The reachability question replaces it.

### Total cost of the recommended set

**$0.05** — `$0.04` (T-ONT) + `~$0.01` (T-A8b, conditional). Headroom after: **$6.39**,
i.e. the entire frontier budget stays intact for the one thing that will eventually need it
(A-3's paired extraction, or a `PANEL_CHECKPOINT` sample pre-registered once at ~110
passages × 3 judges, which §3.4a shows consumes all of it).

Human cost: **two sittings, ~70 presentations total** (30 timed readback items + 40 pairwise
presentations), and both are instrumented to produce `c_human` as a by-product.

---

## Assumptions that are mis-stated in §7 and should be rewritten before testing

1. **A-1** bundles an unmeasured term with no bar. `c_human` has never been measured and
   "tolerable" names no number. ⇒ Split into **A-1a** (`p_drift`, `p_novel` — free, and the
   data for 593×3 is already on disk, not the 30 clauses §7 asks for) and **A-1b** (`c_human`,
   blocked until an adjudication pass records timestamps).
2. **A-7** is called *"the cheapest test in the set."* True in dollars, **false in the only
   scarce currency**: it needs ~40-80 human presentations against a recorded project history
   of **6 items ever**, and §3.4a names human throughput as the loop's unmeasured rate limit.
   Rewrite to *"free in dollars; the largest human-time ask in the set."* Add that a
   held-back duplicate **without an order flip and a recognition check is a memory test**,
   not a consistency test.
3. **A-8** prices the wrong half and its dollar question has no falsifier. §1.2's own
   frozen `shape_partition` artifact shows **14 of 26** gap cases are `shape_b`, where
   *"adding atoms is forbidden"* — extraction cannot fix them by construction. Rewrite as
   the re-selection reachability question, with the 12-clause extension as a conditional
   second part.
4. **A-9** names grounding when the binding cost is **enumeration**. `emit_asp.py` emits a
   choice rule per unconstrained context atom and `run_conflicts.py` runs
   `--enum-mode=brave` over all answer sets, so the space is `2^n` by construction. As
   written, a test could pass on a program that cannot be solved. Rewrite as the triple
   (grounded size, answer-set count, wall-clock incl. per-conflict witness solves).
5. **A-4b** should say **3 anchors, not 4** — `expert_salience.json`'s
   `how-to-approach-tradeoffs` entry has `expert_core_passage_starts: null` and cannot be
   scored on rank-1.
6. **A-6** should quote **both** readback numbers. §7 cites *"discrimination at ceiling while
   sufficiency collapsed to 0.16."* Computed from `readback_results.json` this session,
   **faithfulness is 0.456 against a pre-registered ~0.90+** — a bigger miss, and the one
   that most directly implicates the judge, since the module's whole design argument is that
   a mechanical renderer *cannot invent*. §7 should also note that `DISCRIMINABLE` has
   objective ground truth (`answer_index` per trial), so A-6's exposure is `faithful` +
   `sufficient` only, not all three measures.

### And one correction to §7b

⛔ **`readback.py` is not un-run.** `readback_results.json` records `live: true`,
`created: 2026-08-02T10:31:36`, `model: gpt-5.6-luna`, 125 clauses, 4 discrimination
conditions, 0 errors. It has run, it is paid for, and its artifact is the input to T-A6.
What is un-run is the **validation of its judge** — which is A-6, and which is free.

Two of §7b's three ⭐ items therefore need re-labelling: `readback.py` from *un-run* to *run,
judge unvalidated*; and `ontology.py`'s annotated pass from *the most on-target un-run
experiment* to *the most on-target un-run experiment, whose readout must not be query MCC* —
because the module's own `main()` warns the annotated pass is **not a justified fix** and
`structural.py:502` records the one-hop degradation that warning refers to.
