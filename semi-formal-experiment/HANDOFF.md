# HANDOFF — spec ontology spike (2026-08-01)

> ## ⛔ READ FIRST — EVERY PREVIOUSLY PUBLISHED NUMBER IN THIS FILE IS WRONG
>
> The panel did **not** score a candidate list. `engine/panel/whole_doc.py` put the
> **entire spec in one prompt as 589 numbered passages** and required a verdict for every
> one. `build_site_data.py:40 keeps_citation()` then **dropped every passage scoring 0** —
> **212 / 256 / 436** per behaviour (36% / 43% / 74%). Those passages are gold-negative
> **and correctly predicted negative by every judge**, so deleting them stripped
> true-negative credit the judges had earned.
>
> | mean over 3 behaviours × 3 pair-golds | published | **TRUE 589** |
> |---|---:|---:|
> | tool @0.18 (in-sample) | +0.274 | **+0.320** |
> | judges (mean of 3) | +0.394 | **+0.555** |
> | **tool → judge gap** | 0.119 | **0.236** |
>
> **The gap was understated by ~2×.** Reconstructed by `panel_universe.py`, join rate
> **1.000** on all six (behaviour × spec) cells.
>
> Four claims repeated throughout this project are ARTIFACTS of that deletion:
> * **"MCC is robust to true negatives, so it is safe here."** False as applied — the true
>   negatives had been deleted upstream.
> * **"`sol` is degenerate / near chance."** It is a *low-threshold* judge:
>   helpfulness MCC **−0.027 → +0.308**.
> * **"over/under-caution is UNUSABLE for a headline."** On the true universe it is the
>   **strongest** behaviour by AUC (0.90). `kimi-k2` MCC is **+0.552**.
> * **The selection-effect caveat** (`unliftable_frac` 22% / 14% / 56%) described the broken
>   universe; on the true one it is **2% / 1% / 2%**.
>
> **Judges beat the tool 9 of 9 cells** at the judge's own false-positive rate. On
> helpfulness the judge gets TPR 0.76–0.79 at FPR ≈0.06 where the tool gets **0.13**.
>
> Anything below quoting 377/333/153, 863 passages, 0.764/0.780/0.500, +0.274, +0.187, or
> the over/under refusal is a published-universe number and must be re-derived.


Read this first. Contract: `mattstults.github.io/_drafts/2026-07-31-spec-ontology-tdd.md`.
Deferred full-system design: `...-full-system-DEFERRED.md`.

## Where we are in one paragraph

The **scope problem is solved**: full-document segmentation gives 593 clauses at 97.35%
character coverage (was 18.7% under focus areas), and the panel join now reaches
**849/863 (98.4%)**, 313/313 example blocks, 110/112 high-consensus. 1113 tests pass. Spend
**$1.520 of $7.50** (`spend.py`, plus 6 unlogged `gpt-oss-20b` artifacts, so a floor).
The conflict-delta spike (priority 3) is built and validated end-to-end on cheap models.
**The current work is priority 1, relevance** — see the architecture finding below, which
is the thing most likely to be re-derived expensively by a future agent.

**⇒ FOR CURRENT STATE AND THE ACTIVE PLAN, READ `LADDER_PLAN.md`.** It is the agreed plan
of record (2026-08-02), including the amendments a drift review forced on it the same day.
Short version: read-back ran at full pre-registered scale and found the atoms are an
adequate INDEX and a poor REPRESENTATION — 91 of 125 clauses are identifiable from their
atoms among nine same-section neighbours while a reader of those atoms would not know what
the clause requires (discriminable 0.89 at a 0.944 ceiling; faithful 0.46; sufficient
0.16). Segmentation accounts for only ~2.6% of that loss (Wilson 0.8-10.2%), so it is an
assignment/vocabulary/grammar problem. The ladder is the attribution experiment.

## The finding that shapes the architecture

`extract_section.py` encodes only `conditional` clauses, because a deontic rule needs a
trigger and an act. That is correct for conflict and **fatal for relevance**: measured with
`measure_kinds.py`, example blocks carry 39.1% of high-consensus panel hits versus 38.2%
for conditionals. **A conditional-only relevance tool caps at 38% recall.** So relevance
annotates all 593 clauses across all five kinds; rule extraction stays on the 188
conditionals. Two tiers over one clause set, not one tier.

## The two invariants that are easiest to violate and hardest to detect

1. **Annotation is behavior-agnostic; querying is offline.** No behavior text in the
   annotation prompt, no model call at query time. Either violation silently turns the
   tool into "ask a model per query" — the baseline we are trying to beat — while the
   metrics still look fine.
2. **Never quote a matched-subset score alone.** Passages that join to no clause are
   invisible, not wrong. Always report matched-subset *and* full-reference, strata beneath.

## The bar, pinned (do not re-derive — it cost real effort)

Reproduced to three decimals from `behaviours.json`, so this is the definition:

- `role` free text gives three levels per judge: **core=2, related=1, not relevant=0**;
  the published `score` is their sum. Verified 377/377, 333/333, 153/153. A parser that
  doesn't reproduce `score` exactly is wrong.
- A judge predicts relevant at **core OR related (≥1)**, not core-only.
- **Gold for judge *j* = both other judges relevant.** Not "either" — that variant gives
  0.544/0.689/0.640 and matches nothing.
- **The judge panels differ per behaviour**: helpfulness = Sol/Kimi-K3/Fable 5;
  harm-avoidance = Sol/Kimi-K3/**Opus 4.8**; over/under-caution = Sol/Fable 5/**Kimi-K2.6**.
  Hardcoding one panel yields 0.000 for the other two and looks like a modelling failure.

Reference implementation: `scratchpad/pin_the_bar.py`.

Do **not** use consensus `score ≥5` as gold: it implies every judge rated ≥1, so gold is a
subset of every judge's positive set and **every judge scores recall 1.0 by construction** —
there is no bar at all on that basis.

## The floors — see the banner; the table that was here is superseded

It was published-universe. Use `panel_universe.py`. Floor A = 0.000 (chance, MCC's
definitional zero); floor B = −0.059 (chance minus the coverage gap), per behaviour
+0.029 over/under / −0.161 harm-avoidance / −0.043 helpfulness.

### Use MCC as the primary metric
F1 is what makes the floor unquotable (all-positive scores 0.44–0.64). **MCC is 0 by
construction** for that predictor, and judge ranking is unchanged under it (helpfulness: kimi
0.659, fable 0.648, **sol −0.027** = chance, which F1's 0.240 precision hides).

## Two protocol defects to state with any number

1. **Mean-of-3 vs max-of-1.** Judges are scored on one gold and the bar takes the max; the
   tool is scored on all three and takes the mean. Scoring the best judge's own predictions
   under the tool protocol gives 0.871/0.884/0.833, not 0.764/0.780/0.500. Report **three
   like-for-like head-to-heads**; if one number is needed, compare to judges' **mean LOO**
   (0.636/0.697/0.419).
2. **Selection effect shields the tool, not the judges.** Score 0 never appears, so only
   372/326/**151** of 593 clauses are reachable. F1 ignores true negatives, so truncation
   changes no judge's score while the tool's out-of-list false positives vanish. Predict-all
   inflation, visible vs whole-spec: **+0.147 / +0.228 / +0.429**.

## Settled — do not re-open

- **Judges saw full example blocks, not captions.** `cite.py:147-148` attaches the fenced
  dialogue to its `**Example**:` caption *before* judging; `build_site_data.py:50-57` stores
  only the caption as `quote` because fenced content "renders as code the matcher cannot
  see". The caption is a display anchor. Label unit and prediction unit agree.
- **The clause→passage lift buys no free recall**: clauses-per-passage is `{0:14, 1:847,
  2:2}`, mean 1.002, max 2.
- **Short-quote false joins don't fire**: only 9 of 851 joins rest on a quote under 40 chars.
- **`role` ↔ `verdicts` agree exactly**: 4008 verdict lines, 1336 passages, zero mismatches.


## THE STRUCTURAL RESULT — the earlier NULL WAS WRONG. Retracted.

An earlier version of this section said "typing contributes nothing measurable on this data"
and called the operator "a coarse topic filter, not concept-level ontological work."
**Both statements are retracted.** Three independent errors, each sufficient on its own:

### 1. The noise floor was an expired constant
`NOISE = 0.06` was an **interim guardrail explicitly conditional on n=1** — its own source
says *"until the re-draws land, no difference under about ±0.06 should be read as real."*
The re-draws landed; the constant was used anyway. The precondition that justified it was the
thing that had been removed.

| noise floor for this contrast | value |
|---|---|
| asserted | ±0.060 — from `act_match` vs **bag@LOBO**, a different and far noisier contrast |
| passage bootstrap (act vs any) | ±0.034 |
| **draw-level SE of the design as run** | **±0.0041** |

`act_match ⊆ any_atom` by construction, so the pair is nested and correlated; its true band is
much tighter. **0.060 / 0.0041 ≈ 15 SE applied to a 4.1 SE effect.**

### 2. By the project's own unit of replication, the effect is SIGNIFICANT
Draw as unit, n=5: **mean +0.0168, sd 0.0091, se 0.0041, t(4) = +4.13, p ≈ 0.014,
95% CI [+0.0055, +0.0281] — excludes zero.** MDE at 80% power = 0.0151; the observed effect
exceeds it. The design was never underpowered for the mean — **a significant result was
overridden by an obsolete constant.**

### 3. The published test never tested typing — it confounded typing with SET SIZE
Kind is a strict function of name (361 names, 0 with more than one kind), so `act_match` is
exactly a name-subset filter — verified: it yields the **identical** prediction set to
`any_atom` on the act-only subquery in all 15 cells. So `act_match` vs `any_atom` compares
**prune vs no-prune**, never controlling for set size.

The missing control — replace the act subset with a **random same-sized subset of the query's
own atoms**, 500 draws per cell:

| control | act wins | mean Δ |
|---|---|---|
| size-matched random subset | **15 / 15 cells** | **+0.091** (sign test p = 3e-5) |
| df-matched subset | 14 / 15 cells | +0.066 |

**Typing survives every control.** Including on harm-avoidance, where its published "loss" is
a set-size artifact.

### MEASURED: typing's sign differs by behaviour. HYPOTHESISED: base rate explains it.

Keep these apart. What is **measured** is the per-behaviour sign, reproducible 5/5 across
independent draws, plus the size-matched control (act wins 15/15, mean +0.091). What is a
**hypothesis** is that *base rate* is the explanatory variable: with n=3 behaviours, base rate
is perfectly confounded with behaviour identity, and atom count, topic breadth or clause
density would fit those three points equally well. The F-test below shows behaviours DIFFER —
it does not show base rate is why. "Crosses zero near ~0.15" is an interpolation between three
points, not a fitted threshold.

| behaviour | mean Δ | t(4) | 95% CI | gold prevalence |
|---|---:|---:|---|---:|
| over/under-caution | **+0.087** | +6.57 | [+0.050, +0.124] | 0.068 |
| helpfulness | +0.011 | +1.50 | [−0.009, +0.030] | 0.182 |
| harm-avoidance | **−0.047** | −10.35 | [−0.060, −0.035] | 0.236 |

**Behaviour explains 90.3% of the variance, F(2,12) = 55.6.** `act_match` roughly halves the
prediction set: it buys precision by pruning recall, which pays when the target is rare and
loses when it is common. The three prevalences order perfectly against the three deltas. This
is falsifiable on a fourth behaviour — Δ should decline with base rate and cross zero near
~0.15.

### The "coarse topic filter" claim is also refuted
The 12–16 atom common core is the **more common** atoms (median df 9.5/7.0/10.5 vs remainder
7.0/6.0/8.0) — the opposite of IDF weighting. A same-sized highest-information subset
**collapses** (+0.042 / +0.186 / +0.004 vs the core's +0.342 / +0.368 / +0.231). Random
same-sized subsets span sd 0.048–0.091; the five draws span sd 0.024–0.032. **Draws agree
because independent samples keep selecting the same semantically central atoms** — that is
evidence of a *stable extraction*, and it was read as evidence of a *vacuous operator*.

### What is genuinely unresolved
**Which** behaviours typing pays for. n=3 behaviours; the behaviour-level MDE is 0.206 — no
power at all. Adding 3–5 behaviours spanning prevalence 0.05–0.30 is a few cents and would
confirm or destroy the prevalence model.

**The ontology-pass gate at +0.310 ± 0.021 is suspended** — it was defending a null that does
not exist.



## ⛔ THE DIAGNOSIS WAS WRONG. IT IS THE QUERY MECHANISM. DO NOT BUY ANNOTATION.

An earlier reading said the ceiling was **representation capacity** — "~2.75 atoms per clause
cannot carry what relevance depends on" — and a frontier re-annotation was scoped to test it.
**Refuted, twice, from data already on disk.**

### The supervised ceiling is ABOVE the judge bar
True 589 universe, 9 cells, 5-fold OOF, threshold chosen on training folds only:

| features (all already on disk) | ceiling | 95% CI |
|---|---:|---|
| text (passage tf-idf) | +0.398 | [+0.321, +0.442] |
| atoms | +0.435 | [+0.419, +0.525] |
| **section identity ALONE** | **+0.536** | [+0.478, +0.578] |
| **atoms + section** | **+0.591** | [+0.534, +0.630] |
| text + atoms + section | +0.606 | [+0.535, +0.637] |
| judges (mean) | +0.555 | [+0.516, +0.593] |
| judges (best per behaviour) | +0.654 | — |

Permutation control: −0.0015 ± 0.011. No leakage.

### Where the retracted +0.258 came from
Three compounding faults, all mine: a **fixed 0.5 cut** on a 4–27% base rate (two of nine
cells scored exactly +0.000 — the classifier predicted nothing, which is calibration, not
capacity); a hand-rolled full-batch GD that underfits by +0.11 against liblinear on identical
features; and **`section_path` absent from the feature matrix entirely**. Also: numpy and
sklearn ARE available under system `python3` — the "no sklearn" premise was false.

### Representation capacity is refuted as an information claim
The atom index partitions the 589 passages into **534 distinct equivalence classes**, so the
maximum MCC any function of the atom set can reach is **+0.972**. Act-atoms alone bound at
+0.743; section alone at +0.657. All above the judge bar.

### Richer extraction has no headroom, and the arm was already run FREE — twice
Text-only (+0.398) is **BELOW** the atom index (+0.435): raw text contains everything any
annotator could extract. And `annotations.json` → `annotations_b8.json` was a real +9%
coverage / +14% atoms / +9% vocabulary upgrade, same model and prompt. Paired over 10 CV
seeds: **+0.0054, sd 0.035, t(9)=0.49, CI [−0.019, +0.030], n.s.**

### The paid contrast is unattributable AND underpowered
Those two same-model runs share **78 of 330/361 atom names — 21% vocabulary overlap**. The
vocabulary is a per-run DRAW, not a property of the model, so "model competence" is
inseparable from "different draw". Forcing shared names costs −0.157. And MDE(80%) is
**0.032–0.045** while the best estimate of the paid effect is **+0.005 — one sixth of it**.
**The decision rule cannot fire in either direction.**

### What the deficit actually is
| | MCC |
|---|---:|
| shipped tool, held-out (LOBO) threshold | +0.206 |
| shipped tool, oracle threshold (generous) | +0.396 |
| supervised over the SAME offline features | **+0.591** |
| judges (mean / best) | +0.555 / +0.654 |

The whole recoverable gap sits between the unsupervised scorer and a supervised readout of
**identical** features. That is the **query/scoring mechanism**. Two pieces, both free, both
already named in this file:

1. **Nested/held-out threshold selection** — LOBO→oracle is worth **+0.19**, the single
   largest gap in the project. Costs $0.
2. **The section channel** — section identity alone supervised is +0.536, while the shipped
   channel's AUC is 0.522/0.633/0.623 (near chance on helpfulness) at weight 0.45. Worth
   **+0.16 on top of atoms**, offline.

### Honest target
Never the mean of 9. The supervised ceiling LOSES to the strong judges on helpfulness
(+0.50 vs fable +0.70) and wins only where a judge is degenerate. Report **per-behaviour best
judge, per cell** (0.706 / 0.705 / 0.552, mean +0.654).


## ⛔ BOTH LABEL-FREE LEADS ARE NOW CLOSED. Read before proposing more scorer work.

The supervised ceiling (+0.591) sits above the mean judge (+0.555); the label-free tool sits
at **+0.278**. That gap was attributed to two recoverable items. **Both have now been
measured and both are dead ends** — by proof, not by failure to try.

### Lead 1 — threshold calibration (+0.19). Recovered 40%, then hits a structural wall.
11 label-free rules, pre-registered preference (Otsu, zero free parameters). Otsu recovers
**+0.073 of +0.181 (40%)**, CI excludes zero, beats LOBO in 9/9 cells, stable across all 5
atom draws (+0.268 ± 0.007). But **no rule reaches oracle, and none can**: the three
behaviours' score distributions are nearly identical (mean 0.16–0.19, sd 0.14–0.18) while
their optimal cuts differ by **0.40**. A distribution-shape rule structurally cannot produce
that spread. Eight of eleven rules land in a narrow +0.25–0.32 band.

*(`relevance.predict` now derives its cut label-free by default, retiring
`DEFAULT_THRESHOLD = 0.18` — an in-sample argmax on the scoring panel, i.e. a live invariant-9
violation that shipped for most of this session.)*

### Lead 2 — the section channel (+0.16). NOT RECOVERABLE LABEL-FREE.

| | MCC |
|---|---:|
| oracle section election, then distribute | **+0.641** |
| supervised section-only (78 params/cell) | +0.536 |
| supervised, TRANSFERRED from the other 2 behaviours | +0.334 |
| best label-free section ranking at an **oracle** cut | +0.408 |
| best label-free ranking at any parameter-free cut | +0.18 … +0.34 |

The pre-registered design **lost** (+0.177 vs +0.310 per-clause baseline, CI
[−0.211, −0.079]); the best of 16 variants (+0.335) has a CI spanning zero.

**The mechanism is the finding.** The only behaviour-specific label-free signal available is
the atom index, and aggregating it to section level **adds no information** — it re-uses the
same clause matches. Firing fraction, evidence mass, section-level atom-profile joins, the
rung ladder as elector, the section tree, `kind` composition, adjacency and heading-word
overlap all re-derive the same evidence.

And the decisive part: **~60% of the supervised +0.536 is a generic "which sections are
substantive" prior** that only reaches parity with the clause operator even when handed the
other behaviours' labels — while **the remaining ~40% encodes which sections THOSE JUDGES
treated as relevant. That is a property of the judges, not of the document.** No
document-grounded method can access it, at any budget.

### What this implies about the project's central question
Inter-judge Jaccard is 0.16–0.62 and gold is the intersection of two judges. So part of every
judge's score is **shared idiosyncrasy that no content-grounded function can reach**. The
+0.278 → +0.591 gap should no longer be assumed recoverable: a measurable share of it is
judge-specific by construction.

### What DID work — the rebuild wins as a RANKING channel
Passage AUC, paired bootstrap, all CIs excluding zero:

| behaviour | shipped | rebuilt | Δ |
|---|---:|---:|---:|
| helpfulness | 0.561 | **0.673** | +0.111 |
| harm-avoidance | 0.695 | **0.781** | +0.086 |
| over/under-caution | 0.840 | **0.867** | +0.027 |

Two caveats recorded in `section.py`: the previously-quoted shipped AUCs (0.522/0.633/0.623)
**do not reproduce** — on the corrected universe with the current loader they are
0.561/0.695/0.840, and the deltas above are against the re-measured figures; and
`election_score` is a **panel-fitted** choice of 3 (declared, no-choice baseline 0.671/0.742/
0.864, bias bound 0.039 AUC).


## THE 9-BEHAVIOUR PANEL — power, NOT a bar

`ai_character_index/data/panel-coverage.json` — **9 behaviours x 2 specs = 18 cells**,
2,632 openai + 1,682 anthropic citations. Verified: **locator join is 100%** on both sides
(589 model-spec / 374 constitution universes via `panel_universe.spec_passages`).

Behaviours: animal-welfare-impacts, harmlessness-to-the-user, helpfulness,
objectivity-on-contested-questions, avoiding-over-and-under-caution,
proportionate-risk-mitigation, harm-avoidance-to-third-parties, how-to-approach-tradeoffs,
user-autonomy.

**This fixes the binding statistical constraint.** n=3 behaviours gave a behaviour-level MDE of
0.209 — every "which behaviours does this help" claim in this project has been unmeasurable,
including the base-rate story that had to be demoted to a hypothesis. 9 behaviours settles it.

### ⚠️ Three things not to get wrong

1. **IT IS A WEAKER PANEL. NEVER QUOTE ITS AGREEMENT AS "THE BAR."** Judges are
   **gpt-mini, haiku, qwen-small** — small models. The goal is "quality equal to or better than
   asking the FRONTIER models", so `behaviours.json` (sol/kimi/fable/opus/kimi-k2) remains THE
   BAR. Use this panel for **generalisation and power**, and label it by its roster wherever it
   appears.
2. **THE UNIVERSE IS TRUNCATED, WORSE THAN BEFORE.** Score distribution is
   `{2:1309, 3:1145, 4:741, 5:583, 6:536}` — **no 0 AND no 1**, where `behaviours.json` at
   least kept score 1. Reconstruct via `panel_universe` and restore absent passages as
   all-zero. **Score-1 passages are IRRECOVERABLE** — real "tangentially related" judgements
   now indistinguishable from "not related". State that limitation with any number.
   Mistaking a truncated universe for the judged set is the error that made every headline in
   this project wrong, in the tool's favour, for most of a day.
3. `verdicts` is a **JSON object (a real dict)**; `role` is JSON `null`. An earlier note here
   said `verdicts` was a string repr — that was wrong, an artifact of a pretty-printer calling
   `str()` on it. `panel_v2.parse_verdicts` accepts both shapes and uses `ast.literal_eval`,
   never `eval`, for the string path. Verdict scale is
   **2 = relevant, 1 = tangentially related, 0 = not related** (confirmed by Matt), matching
   the existing panel's core/related/not-relevant.

### Wired: `panel_v2.py` (+ `benchmark.py --panel-v2`)
100% join reproduced; universe restored (6,867 recovered rows, all-zero, tested); duplicate,
unjoinable, and judge-missing rows all RAISE. Re-derived noise floor **0.0288** (18 cells,
1000 resamples) — the old 0.045 is refused *by name* in code and test.

**⚠️ THE SCORE-1 TRUNCATION INFLATES THE JUDGES BY ~+0.089 MCC.** Gold is untouched (a
pair-gold needs two judges at >=1, so score >=2), so the whole effect lands on the *judges'
predicted sets*: their lone "tangentially related" calls vanish, taking their false positives
with them. Applying the export's `score >= 2` rule to the frontier panel moves judge LOO
**+0.631 -> +0.720**, with 7.5-29.7% of passages changing class. **So the small-model judge
column on panel v2 over-states its own panel by ~+0.09, and the tool-vs-judge gap it reports
is conservative IN THE JUDGE'S FAVOUR.** Irreparable from this file; only a re-export from
`experiments/panel-judges/runlog-v2.jsonl` fixes it.

**Quotes are re-derived for every row.** The export's published rows carry RAW passage text
(`**bold**`, inline fences) while recovered rows would carry the publisher's cleaned quote —
1,027/2,632 openai and 306/1,682 anthropic differ. Mixing them would have biased the clause
join **along the gold axis**, since "published" means some judge saw relevance. Tested.

A second independent demonstration of the truncation defect: on the export's own citation list
the small-model judges score **-0.221** mean MCC (base rate near 1) versus +0.525 on the true
universe — a delta of 0.746.

`check_bar_provenance` is now a standing guard: any document quoting a bar off these
behaviours must name the roster and say "small-model panel", or it raises.

### Blocked on spend
- **Constitution clause annotations do not exist** — `annotations_b8.json` is 587 clauses, all
  `m*`, zero `c*`. So the anthropic side cannot run the ontology tier even once atoms exist.
  `annotate.py --clauses constitution_clauses.json --live` is ~47 requests; `annotate.py`
  prints no estimate, so cost is **unverified** (~$0.1-0.2 by scaling). Needs its own costing.


## ⭐ THE CENTRAL QUESTION IS ANSWERED: the signal is a DOCUMENT property, not judge idiosyncrasy

The +0.20 between our label-free query and a supervised readout of **identical features** was
the last open question. It is now decomposed, and **replicated across two panels, two judge
tiers, and 3 -> 9 behaviours.**

### The transfer test (and why one test was not enough)
"Does it transfer?" is under-specified: a behaviour-specific but perfectly document-grounded
signal ALSO fails leave-one-behaviour-out. So the decisive arm is **cross-judge** — train on
judge *j*'s own positives, evaluate against gold[j] = the other two judges' intersection, a
label source **disjoint** from the evaluation label.

| arm (atoms+section, fold-wise) | MCC | 95% CI |
|---|---:|---|
| in-cell | +0.583 | [+0.520, +0.659] |
| **cross-judge (disjoint label source)** | **+0.404** | [+0.348, +0.458] |
| LOBO (other behaviours) | +0.241 | [+0.196, +0.281] |

**69% of the supervised ceiling survives being learned from a judge who did not write the
gold.** Decomposition: behaviour-agnostic document prior **41%**; behaviour-specific but
judge-generic **28%**; single-judge label noise 18%; **judge IDENTITY <= 12%** (upper bound).

Replicated on the 9-behaviour panel (27 cells): in-cell +0.644, cross-judge +0.437 —
**68% vs 69%**, to one point, across two judge tiers. All 9 behaviours in +0.29…+0.54, none
degenerate. Honest range: **judge identity 12–22%, document+behaviour signal 68–69%.**

*A memorisation control earned its keep*: fitted on all rows instead of fold-wise, cross-judge
reads +0.511 and tracks the training judge's own MCC at **r = 0.962** — the model reciting the
judge it was trained on. Run without holding out rows, this test says "transfers beautifully"
from an artifact.

### But the label-free derivation does not exist in anything the corpus supplies
- The learned weighting is **ANTI-correlated with our IDF in 8/9 cells** (rho −0.00 to −0.50).
  Positively-weighted atoms have HIGHER df (5.9–9.7) than negatively-weighted (3.3–4.0).
- **It is not a function of anything we compute.** Coefficient regressed on log clause-df, log
  passage-df, gloss length, clause count and kind: **R² = 0.039 [0.029, 0.054]**. It encodes
  atom **identity**.
- 3–11 of every 19–28 query atoms earn a **negative** weight — which our query cannot express.
- **54 label-free re-weighting variants** (18 weightings x 3 normalisations): best gain
  **+0.016**. The 13 corpus-statistic variants span 0.023 MCC, half the noise floor. Eight
  behaviour-agnostic passage priors all LOSE (−0.098 to −0.318). No monotone df transform works
  — the weighting is anti-IDF but *not* pro-df.

### Gap attribution (+0.278 -> +0.583)
calibration **+0.118** · per-atom re-weighting **+0.141** (label-free reachable: **+0.009**) ·
section block **+0.118** · lex+section drop −0.039 · supervised's own calibration cost −0.034.

### ~~THE ONE LEAD LEFT~~ — WITHDRAWN, it was a fitting vector

This proposed raising the annotation salience field's rank fidelity, **"with rho against the
learned coefficients as a cheap OFFLINE progress metric"**. Those coefficients are an L2
logistic fit to panel labels. **Iterating an annotation prompt until that correlation rises IS
fitting to the panel** — invariant 9, reached one level of indirection out. The disclaimer
attached to it guarded the fitted *weight*, not the *selection criterion*.

This is the same shape as the retracted "a genuine result being left on the table", which a
funded experiment had already been designed to execute before it was caught. Recorded here
because the recurring failure mode of this project is a fitting-shaped sentence surviving in
prose until it becomes the plan of record.

**And the observation itself is noise — the lead is dead twice over.**
* rho = +0.17 is **not distinguishable from zero**: per-cell z-scores +0.20 to +1.45, none
  reaching 1.96. The "9/9 cells" is really **3 independent units** (cells within a behaviour
  share atoms and golds overlapping J = 0.56-0.76): sign test **p = 0.125**.
* The field is near-degenerate — harm-avoidance salience is `{2: 17, 3: 6}`, **two distinct
  values over 23 atoms**.
* **To clear the 0.045 noise floor you would need rho ~ 0.42 — 2.5x an effect that is
  currently unmeasurable.** The entire lever caps at **+0.088** at PERFECT rank fidelity, and
  at **+0.026** under transfer, i.e. inside noise.
* **rho is falsified as a progress metric by our own data**: IDF has rho -0.30 and is the
  shipped baseline; the declared salience has rho +0.17 and scored **-0.013**; a synthetic
  vector at rho +0.17 scores **+0.023**. Two weightings with identical rho differ by 0.036
  MCC — 80% of the noise floor — because rho ignores tie structure.

Do not revive this without a document-derived metric AND an effect size that clears noise.



## ⛔ `act_match` DOES NOT TRANSFER — structural's +0.310 was a 3-behaviour number

`structural.PRIMARY_OPERATOR = "act_match"` was selected on panel MCC over 7 operators using
the **3-behaviour** frontier panel, declared `fitted_on_panel: True` with a **0.016 bias
bound**. Measured on **9 behaviours** (openai, 5 draws):

| | 3 behaviours | **9 behaviours** |
|---|---:|---:|
| `act_match` (the fitted choice) | +0.310 | **+0.246** |
| `any_atom` (the NO-CHOICE baseline) | +0.294 | **+0.274** |
| bag scorer (`relevance`, label-free) | +0.277 | +0.284 |

**The fitted operator LOSES to the unselected one on 9 behaviours** (S0 − S = +0.027; inside
the composition P@any − P = **+0.039** [+0.019, +0.058], every draw). And `act_match` at
+0.246 **loses to the bag scorer**. The declared 0.016 bias bound **understates the cost by
more than 2x**.

This is the clearest instance yet of the project's recurring failure: a choice made by reading
panel results on n=3 behaviours, declared honestly, and still wrong once n=9 was available.
**Anything quoted from `structural.py` at +0.310 is a 3-behaviour figure and must not be
carried forward.**

## The combination: helps on the DECISION side, null on RANKING

`combined.py` — typed core (never vetoed) UNION rung-elected section closure. Pre-registration
in the docstring predates every number.

| variant | mean MCC (9 beh, 5 draws) |
|---|---:|
| **V1@any** typed core ∪ majority-elected sections, no rung gate | **+0.316** |
| bag scorer | +0.284 |
| typed core alone (`any_atom`) | +0.274 |
| PRE-REGISTERED PRIMARY (with the rung gate) | +0.259 |
| `act_match` alone | +0.246 |
| section alone (elect & distribute) | +0.198 |
| intersection | +0.145 |

- **V1@any − typed core = +0.042** [+0.030, +0.055], every draw — clears both noise floors.
- **V1@any − bag = +0.032** [+0.017, +0.047] — clears the optimistic 0.0295, **NOT** the
  re-derived 0.035. **Parity-to-marginal, not a clean win.**
- **The rung gate — the one operator the agent invented — LOSES to its own no-choice
  baseline** (−0.018, every draw). Reported rather than dropped.
- **Size-matched randomisation control**: replacing the ~29 closure clauses with a random
  same-sized non-core set scores **+0.243**, BELOW the unextended core's +0.274, while the
  elected sections give +0.316. **The gain is the partition, not the extra prediction mass.**
- **Ranking is a flat null**: combined AUC 0.7425 vs `section.rank` 0.7427 (structural alone
  0.6475). The typed within-section tiebreak buys nothing; the ranking result stays entirely
  `section.py`'s.

`section.py`'s earlier null was a null about the section **deciding alone** — never about the
section **extending** a typed core. This is the first measurement that separates the two.

## ⚠️ The noise floor is 0.035–0.037, not 0.0295
Re-derived at 2000 resamples on this panel for four predictors: 0.0350–0.0357. **0.0295 is
the optimistic end.** State verdicts so they hold at 0.037.


## ⛔ THE CONTRACT-COMPLIANT MODULE IS WORSE THAN THE ONE IT REPLACES

> **⛔⛔ THIS SECTION IS RETRACTED. Read the retraction 84 lines below
> ("RETRACTED: 'THE COMPLIANT MODULE IS WORSE'. It was an `act_match`
> artifact.") BEFORE you act on anything here.** The finding was an artifact of
> an operator borrowed from another module and selected on 3 behaviours. At the
> shipped `any_atom` the compliant module is *not* worse. The section is kept
> because the measurement discipline in it is sound and worth reading — but a
> reader who stops at this heading leaves with the opposite of the conclusion,
> which is exactly what happened for three cycles.

Two agents measured this independently and agree to three decimals. 9 behaviours, openai,
589-passage universe, 5 atom draws, label-free, MCC:

| predictor | mean | invariant 10 |
|---|---:|---|
| **`combined.py` V1@any** (typed core ∪ elected sections) | **+0.316** | COMPLIANT |
| `relevance.py` (bag scorer) | **+0.284** | **VIOLATING** |
| typed core alone (`any_atom`) | +0.274 | compliant |
| `structural.py` (`act_match`) | +0.246 | compliant |
| `section.py` | +0.198 | compliant |
| lexical control | +0.185 | — |
| FLOOR B / FLOOR A | −0.035 / 0.000 | |
| small-model judges | +0.514 | (inflated ~+0.09) |

- `structural − relevance` = **−0.0378** [−0.0596, −0.0164], sign consistent in **5/5 draws**.
  Structural wins 3 of 9 cells and loses badly on animal-welfare (+0.133 vs +0.217) and
  how-to-approach-tradeoffs (+0.058 vs +0.188).
- `section − control` = +0.0132, **CI spans zero** — the section quotient's DECISION rule buys
  nothing over bag-of-words.
- `structural − control` = +0.0613 [+0.0335, +0.0892] — structural does earn its ontology over
  the lexical baseline, just **less than the bag scorer does**.

**So the module the contract calls "scheduled for replacement" is the best SINGLE module.**
The compliant modules' case rests on invariant-10 compliance, zero fitted parameters, and a
better `explain()` — **not on the number.** Say that plainly wherever they are proposed.

### The one compliant thing that does beat it
`combined.py` V1@any at **+0.316** vs the bag's +0.284 — but the delta is **+0.032** against a
re-derived noise floor of **0.0316–0.037** (the two agents derived 0.0316 at 1000 resamples /
9 cells and 0.0350–0.0357 at 2000 resamples). **Borderline: it clears one estimate of the
floor and not the other.** Do not call it a win.

### Noise floor: 0.0316–0.037, NOT 0.0295
The 0.0295 quoted earlier is the optimistic end. State verdicts so they hold at 0.037.


## ⭐ THE DECISION FOR MATT — everything else in this file is input to it

Every fact below is measured and recorded elsewhere in this document. No page previously put
them together as a choice, so here it is.

| | MCC |
|---|---:|
| frontier-judge bar (**the stated goal**) | **+0.555 mean / +0.654 best-per-cell** |
| best COMPLIANT config (`combined` V1@any) | +0.316 |
| best VIOLATING config (`relevance` bag) | +0.284 |
| lexical control | +0.185 |
| chance | 0.000 |

### Invariant 10 is NOT the constraint — invariant 9 is
Invariant 10 (structural query, not a similarity score) has a measured cost of **at most
±0.03**, and on the best available configuration the cost is **NEGATIVE** — the compliant
composition is ahead of the bag scorer. The distance to the goal is **0.24–0.34**. So the
structural requirement accounts for **under a tenth** of the shortfall; dropping it would buy
a rounding error and forfeit the auditability that is half the stated value proposition.
**Keep invariant 10.**

The binding constraint is **invariant 9 — no labelled examples**. A supervised readout of
IDENTICAL offline features reaches **+0.591**, above the judge mean. Both label-free routes to
that number are now closed BY PROOF, not by failure to try:
* threshold calibration — the three behaviours' score distributions are near-identical while
  their optimal cuts differ by 0.40, so no distribution-shape rule can produce that spread;
* the section channel — ~40% of its supervised advantage encodes which sections THOSE JUDGES
  treated as relevant, which no document-grounded method can access;
* 90+ label-free re-weighting variants across five families — best gain +0.018, and **<= 0
  after correcting for selection**.

### The question
> **Is a fast, auditable, fully-explainable tool at ~55–60% of frontier-judge agreement the
> product — or does the goal need restating?**

The "MUCH faster iteration and better explainability/auditability" half of the value
proposition is **delivered and defensible today**: annotate once (~$0.28), query offline and
instantly, with `explain()` tracing behaviour -> atom -> span -> clause -> locator.

The "quality equivalent to or higher than just asking the frontier models" half is, on current
evidence, **not reachable under the contract as written**.

Do not let an agent resolve this by continuing to iterate. It is a scope decision, not a
measurement.


## ⛔⛔ RETRACTED: "THE COMPLIANT MODULE IS WORSE". It was an `act_match` artifact.

Independently recomputed from raw artifacts (every recorded number reproduced to 4 dp — the
numbers are honest; the INFERENCE was not).

### 1. The headline traced to ONE fitted parameter we already knew not to trust
Operator sweep, 7 operators x 3 module families. `any_atom` — the declared NO-CHOICE default —
ranks **1/7 on the held-out 6 behaviours for all three families**. `act_match` ranks 3/7.

| contrast (behaviour-level, n=9) | delta | p | sign |
|---|---:|---:|---:|
| `structural@act_match − bag` | −0.038 | **0.121** | 3/9 |
| `core@any_atom − bag` | −0.011 | 0.49 | — |
| **`section@any_atom − bag`** | **+0.023** | 0.061 | 7/9 |
| **`section@any_atom − control`** | **+0.122** | **0.0005** | **9/9** |

**At the no-choice operator the compliant modules are level with or AHEAD of the bag scorer.**
`section.py`'s own docstring warning "THIS LOSES, measured −0.143" is an artifact of the
operator it inherited. The project applied the `act_match` lesson to `structural.py`'s headline
and **not** to `section.py`'s, `combined.py`'s primary, or the invariant-10 conclusion.

### 2. The noise floor is MIS-SPECIFIED — delete it
`benchmark.noise_floor` scores ONE predictor on TWO INDEPENDENT passage resamples. Its
half-width is exactly `1.96*sqrt(2)*SE` — an **unpaired** null. Every contrast it gates is
**paired** (same resample, clauses, golds, joins). Measured: the floor is **2.1x to 6.5x the
paired SE**. It would reject a true, perfectly-measured effect of 0.03 forever, at any sample
size. Not conservatism — a mis-specified test.

### 3. The resampling unit is the BEHAVIOUR, not the passage
Between-behaviour SD of the `structural − bag` delta is **0.0596**; between-draw SD **0.0172**.
Behaviour variance dominates ~12x in variance and the passage-unit CIs ignore it entirely.
**"Sign consistent in 5/5 draws" is worthless evidence** — the draws are correlated re-queries
of the same 9 behaviours. Report behaviour-clustered CIs, a paired t, and a sign test.

### 4. `combined` does NOT beat the bag at n=9, and the typed core adds nothing
`combined − bag` = +0.032, **t=2.02, p=0.078, 7/9** — fails at the behaviour level. Fragile:
`harm-avoidance` alone contributes +0.144 while the other eight average +0.018; **drop it and
the delta halves to +0.018.**
`combined − section@any` = **+0.0084, p=0.60** — the typed core adds nothing measurable on top
of the section module at its no-choice operator.

### 5. RETRACTED: "the gain is the partition, not the extra prediction mass"
The size-matched control reproduces exactly (+0.2431) but **cannot come out any other way** —
sd across 200 randomisations is 0.0021, P(random >= core) = 0.000. The decisive control was
never run: random **whole sections**, size-matched, score **+0.2406** — no better than random
clauses. **The partition is INERT.** The gain is the *election ranking*, computed from the same
typed atoms already in the core. That is a claim about aggregation, not ontological structure,
and it materially changes what the thesis rests on.

### 6. `act_match`'s selection cost, isolated by difference-in-differences
gap on the 3 selection behaviours −0.0025; on the 6 held-out +0.0424; **DiD = +0.0449, cluster
CI [+0.0172, +0.0717], excludes zero — 2.8x the declared 0.016 bound.**

### 7. ⚠️ `combined.MEASURED` and `section.MEASURED` ARE HAND-TRANSCRIBED CONSTANTS
No generator exists in the repo. Every variant mean, all 11 bootstrap contrasts, the size
control and the AUCs live in a literal dict, and the test suite checks only **internal
consistency of the literals** (e.g. asserting one hardcoded number is smaller than another).
**A green suite is not evidence that any of them is what the pipeline computes.** They were all
independently verified correct — but "two agents agree to three decimals" is weak if both read
the same dict, and nothing would catch drift.

### THE HONEST HEADLINE IS A NULL, AND IT IS STILL INTERESTING
No compliant configuration separates from the bag scorer at n=9 (best p=0.061). The defensible
claim is:

> **A zero-parameter structural query reaches PARITY with a fitted bag scorer and beats
> bag-of-words by +0.12 (p=0.0005, 9/9 behaviours).**

**Ship `section@any_atom`, not `combined`** — it is the most transfer-stable predictor measured
(frontier-3 +0.3085 vs held-out-6 +0.3066, a shift of 0.002, against `act_match`'s 0.088).

**n=9 is the binding constraint on every remaining question.** More passages buy nothing; more
behaviours buy everything.

## The loop being tested

Tool vs. a frontier LLM answering the **same question**. Adjudicate deltas only; each
delta → named artifact → fix → full recompute → regression check. **The document is ground
truth; the LLM is a lead generator, never an oracle.** For relevance the reference already
exists on disk (`behaviours.json`); the bar is the **best single judge**
on the TRUE universe (see banner). The published-universe bar 0.764/0.780/0.500 is
superseded and must not be quoted.

## Module state — all green, 1113 tests (2026-08-02)

| module | owner | state |
|---|---|---|
| `modelspec_clauses.json` | — | **593 clauses**, 97.35% char coverage, 100% verbatim, 0 duplicate locators, 259/259 focus markers preserved as a privileged subset |
| `measure_join.py` | me | the recall ceiling: 849/863 overall, 110/112 at score ≥5, 313/313 example blocks. **Gates every benchmark number** |
| `measure_kinds.py` | me | relevance signal by clause kind; source of the 38% ceiling finding above |
| `annotate.py` | agent | done — 1,629 atoms, 99% coverage, reuse 0.78 (`annotations_b8.json`) |
| `relevance.py`, `benchmark.py` | agent | done — offline scorer + MCC-primary benchmark; CLI runs the tool, `explain()` wired |
| `behavior_atoms.py` | agent | done — 70 query atoms, 100% selected from the clause vocabulary |
| `conflict_output.py` | agent | instrument done (blinded + negatives + rubric + validator); **no tool adapter** |
| `inventory.py` | A | unique locators `... > L200 [fa_la9s]`; `match_passage()` quote-containment join now normalizes whitespace, `[^xxxx]` footnotes, markdown emphasis, **and both link renderings** — all four required, dropping any one silently lowers every metric. `SPEC_MD` points at the shared `../specs/openai-model-spec/` tree |
| `emit_asp.py` | A | `--skip-invalid` with cascade + `provenance` block; provenance facts proven inert |
| `extract_section.py` | B | batched (default 14), span-id selection, act-enum closed across batches, `conflict_capable` diagnostic, truncation as its own failure class |
| `baseline_conflicts.py`, `delta.py`, `adjudicate.py` | C / chain agent | k=3 baseline, 3-bucket delta, worksheet with encoding-status block |
| `providers.py` | me | `complete_envelope()` → `{text, finish_reason, reasoning, usage, truncated}`; usage logging; auto-adapts unsupported params |
| `calibrate.py` | me | measures cost per batch per model from real usage |

## Key numbers (all measured, not estimated)

**Cost — measured tokens × looked-up rates. Use `luna` for everything until a final
measurement run.**

| model | $/Mtok in–out | $/batch | whole doc (13 batches) | k=2 |
|---|---|---|---|---|
| **luna** (gpt-5.6-luna) | 0.20 / 1.20 | **$0.0088** | **$0.11** | **$0.23** |
| terra (gpt-5.6-terra) | 2 / 12 | $0.068 | $0.88 | $1.76 |
| kimi (Kimi-K3) | 3 / 15 | $0.223 | $2.89 | $5.79 |
| sol (gpt-5.6-sol) | 5 / 30 | $0.241 | $3.14 | $6.28 |

**`luna` is 27× cheaper than sol, had the LOWEST reasoning overhead of the four (39%),
parsed cleanly, and was fastest (35s vs sol's 82s).** It is gpt-5.6-family, so its failure
modes should resemble sol's — a much better iteration tier than a different-family
mid-tier model. Prices are in `providers.json` and `calibrate.py` reads them.

**First comparison table** (both sides `gpt-oss-20b`, chain-of-command only):
`|C_tool|`=0, `|C_baseline|`=6, coverage 0.524 effective / 0.571 claimed,
`baseline_self_agreement`=0.244 over k=3. **Degenerate** — tool's zero is structural
(0 `incompat`, no act both obliged and forbidden), settled before the solver runs.

**Panel join — SOLVED.** Against focus areas it was **70.3% zero-match** (example blocks
100% zero, core judgments 40.6% zero). Against `modelspec_clauses.json` with the fixed
normalizer, via `measure_join.py`:

| stratum | matched | total | |
|---|---|---|---|
| all | 849 | 863 | 98.4% |
| score ≥5 | 110 | 112 | 98.2% |
| score ==6 | 58 | 60 | 96.7% |
| example blocks | 313 | 313 | 100% |

The 14 remaining misses are **not paraphrase and not version skew** — our spec copy is
byte-identical to `../specs/openai-model-spec/model_spec.md` (sha256 `8c95f020…`). The
panel's own renderer rewrote `[text](url)` inconsistently, sometimes *within a single
passage*, so no one normalization variant matches. A real but small ~1.6% reference-side
ceiling.

## THE OPEN PROBLEM — SOLVED, kept for the reasoning

OpenAI's focus areas are a **test index, not a document index**: 225 of 259 carry rubric
prompts. They covered **50,855 of 271,474 chars (~19%)**, contained **zero markers inside
the 183 example blocks**, and skipped whole sections including `levels_of_authority` (which
*defines the authority lattice we use*).

So focus areas are the right unit for the **rule layer** and the wrong unit for the
**coverage/lookup layer**. Fixed by our own full segmentation → `modelspec_clauses.json`
(593 clauses, 97.35%), with focus areas retained as a privileged subset carrying authority
+ rubric joins. `measure_kinds.py` then showed the split has to go further than expected:
rules on the 188 conditionals, **annotations over all 593 including examples**.

## ~~THE RESULT (2026-08-01, first version)~~ — DELETED, IT WAS ALL BUG ARTIFACT

This section held an F1 table, a "MCC near chance" claim, and a channel ablation ending in an instruction to delete a channel. **Every number in it came from the broken loader and was ranked on F1.** The numbers and the instruction have been REMOVED rather than quoted-and-annotated, because a reviewer found the annotated version still being followed and `grep` still returned the instruction. Under the repaired loader and MCC ranking that ablation row is *vacuous* anyway — it is bit-identical to `full`.

Two general lessons, both earned the expensive way:
- **A superseded number left in a doc is an instruction, not a footnote.** Delete it.
- Do not rank channels on F1 here: the all-relevant point is inside the sweep, so F1 rewards
  rescaling the score distribution rather than discrimination.

## Update — full-coverage artifact (use these, not the originals)

`annotations_b8.json` (batch-size 8): **1,629 atoms, 99% coverage, 183/183 example blocks,
0 truncated, 0 call failures**, reuse 0.78. Paired with `behavior_atoms_b8.json` (70 atoms,
100% in-vocabulary). Example blocks carry 39% of the relevance signal and were the biggest
hole — the original run lost 24 of them.

### ⚠️ Every ablation number recorded before 2026-08-01 12:18 is void

`benchmark._clause_rows` dropped `section_path`, collapsing all 593 clauses into one section
and turning the section channel (0.45 of the weight) into a constant. **The blast radius is
every prior ablation and every prior threshold derivation.** Do not compare across that fix.

### ~~Current headline~~ — DELETED (published universe, superseded)

This block carried a table headed **"QUOTE THIS +0.187"**. Every number in it was computed on
the truncated 377/333/153 universe. It is deleted rather than annotated, because this file's
own lesson is that *a superseded number left in a doc is an instruction, not a footnote* — and
a reviewer found the previous annotated-but-retained version still being quoted. Use
`panel_universe.py` and re-derive. On the true universe: tool @0.18 +0.320, judges +0.555.

### ⚠️ The `section_path` fix was a CALIBRATION fix, not a recovery

Best MCC **over the sweep** moved only **+0.2637 → +0.2743 (Δ +0.011)**. The bug moved where
the good operating point sits on the threshold axis (0.36 → 0.18); it did not change how well
the method discriminates. An earlier version of this file narrated it as "MCC near chance →
50-83% of a judge". That was a threshold artifact. With n=3 behaviours whose optima are
0.18 / 0.18 / 0.58, one constant cannot be tuned honestly — **nested selection is the fix and
is not implemented.**

### Ablation — ranked on MCC (F1 ranking was itself the bug)

| variant | mean MCC |
|---|---|
| _FLOOR (all-relevant)_ | _−0.036_ |
| full | **+0.339** |
| −lex | +0.338 |
| −section | +0.317 |
| −atom | +0.264 |
| lex only | +0.272 |

**The atom channel is the largest single contributor (+0.075); lexical contributes +0.001.**
Under F1 ranking the atom channel looked marginal (+0.018, CI [−0.004, +0.053], n.s.) — but
ranking channels on F1 rewards rescaling the score distribution rather than discrimination,
which is the same pathology as the threshold bug. MCC ranking is the honest view.

**The section channel's value is UNKNOWN — do not delete it, and do not claim it helps.**
An earlier version said "the section prior is harmful, dropping it is the next free win";
that was measured under the broken loader. A later version over-corrected to "dropping it
costs 0.022 MCC". Both overstate: the paired bootstrap gives **+0.0217, 95% CI
[-0.0118, +0.0557]** — it spans zero, and `-section` is actually *better* than full on
helpfulness (+0.242 vs +0.215). The honest statement is that we cannot yet tell.

### (deleted) "the section signal is unexploited"

This section said a supervised section predictor reaches AUC 0.795 where the shipped channel
reaches 0.522, and closed *"a genuine result being left on the table."* The contract retracts
that exact phrasing as **"an instruction to go fit it — exactly the drift invariants 9 and 10
exist to prevent."** It is deleted here rather than annotated, because a reviewer found this
very sentence was what the next funded experiment had been designed to execute.


## In flight

Two clean-context reviews: (a) is the proposed **oracle-atom ceiling experiment**
scientifically legitimate, and (b) **could the poor results be caused by bugs** rather than by
the method. Do not draw conclusions about the approach until (b) reports.

See `MODULE_MAP.md` for what every module is and which capability it serves.

## Next actions, in order

~~1. Make the tool runnable.~~ DONE — `relevance.py <slug>` runs the real tool;
   `--baseline` is now an explicit opt-in and is labelled in the output.
~~2. Wire `explain()`.~~ DONE — reachable via `--explain <clause_id>`, 6 tests, verified over
   150 explanations: channels sum to the raw score, every cited span is a substring of its own
   clause.
~~3. Print the floor in the ablation table.~~ DONE — and `ablate` now ranks on MCC, not F1.
4. ~~Build the tool → `ConflictFinding` adapter.~~ **DONE** — `conflict_adapter.py`. `ConflictFinding` is constructed by hand
   only in `make_conflict_sample.py` ("not a tool run"); nothing generates a panel from a real
   tool run. Priority 2 is blocked on THIS, not only on Matt's two decisions. Also unfixed:
   the sample ships 1:2 negatives while the README states and argues for 1:1, and every
   negative carries `adjacent: False` — a tell to any human reader.
5. **Nested/held-out threshold selection.** Every lift currently quoted is a
   hindsight-threshold number.
6. Only then consider a frontier run, and only to *measure*, not to iterate.

### Deleted from this list, deliberately — do not reinstate

*"Reframe the tool as a high-precision lead generator reporting P@k."* It rested on
"harm-avoidance P@20 = 0.896 is the only place any method beat chance", which is **now false**
(MCC +0.358 beats chance). It was proposed after one weak measurement, retracted in
conversation, and then survived in writing here for several hours — which is precisely how a
retracted reframe becomes the plan of record. The goal is unchanged: **match or beat a
frontier model on relevance.**

## Things that will bite you

- **`incompat` is the only channel for indirect conflicts** and the cheap model produced
  zero. If a frontier model also under-produces it, `|C_tool|` collapses regardless of
  coverage. B added a pairwise-pass requirement and an `incompat_declined` record; verify it
  actually fires.
- **Coverage is gameable by decomposition** — the extractor split one provision into 8 rules
  differing only in condition, inflating coverage without adding conflict surface.
- **`jaccard({},{}) == 1.0`** meant all-empty runs reported *perfect* self-agreement. Fixed
  (`None` when every run empty) but the class of bug — a metric that reads best when the
  system fails worst — is worth re-checking elsewhere.
- **The join normalizer needs all four transforms**: whitespace runs, `[^xxxx]` footnote
  markers (25 mid-sentence), markdown emphasis, and *both* renderings of a markdown link.
  Emphasis stripping alone is worth 313 passages — every example caption is `**Example**:`
  in source and `Example:` in the panel, so no example block can match without it. Dropping
  any one transform silently lowers every downstream metric. `test_inventory.py` guards this.
- **Relevance must not be scoped to conditional clauses.** Example blocks carry 39.1% of
  high-consensus panel hits vs 38.2% for conditionals; conditional-only caps recall at 38%.
  Re-derive with `measure_kinds.py` if you doubt it.
- **`atom_provenance.py` keys on `clause_id`** and defaults to the constitution pilot; it
  will `KeyError` on a Model Spec `extraction.json` (`focus_id` naming split). Unfixed.
- **`gpt-5.6-*` models reject `max_tokens`**, require `max_completion_tokens`. Handled by
  auto-adaptation in `providers.py`, but don't reintroduce it elsewhere.
- Reasoning is billed as completion tokens and **scales with the budget you give it** —
  `gpt-oss-20b` produced 71,964 chars of reasoning and zero content at 16k max_tokens.

## Instrument findings that shape the design

Blind two-rater experiment (`audit_*.json`): the **directed** span question ("which span
licenses this gloss, does it assert more?") has precision 1.00 and found 3 uncatalogued
defects. The **global** question ("does the document draw this distinction?") failed on a
known coined atom *with full document access*. **Always show the full clause, never a
truncated span.** Dominant defect class is provenance — real distinction, wrong citation.
