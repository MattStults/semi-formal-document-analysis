# RESULT — TRIAGE: can cheap pre-critic signals predict frontier-critic yield?

**Zero API spend.** Every number is recomputed from data already on disk.
No git was run, no branch switched, no commit made.

Pre-registration: `PREREG.md` (six predictors, outcome columns tiered, falsifiers fixed,
one signed amendment A1). Code: `build.py`, `analyse.py`. Data: `table.json`, `stats.json`.

---

## THE ANSWER, IN THREE SENTENCES

⛔ **The starred candidate failed.** Cheap-critic *disagreement* — the signal that would
have made triage free and document-independent — **points the wrong way** and is falsified
on its own pre-registered criterion.

⚠️ **One predictor survives, weakly.** A defeasibility-hedge regex on the span holds its
pre-registered sign in-sample **and gets stronger out of sample** (ρ +0.34 → +0.42), and
on the semi-independent 25-clause cohort **all 6 hedged clauses were edited against a 64%
base rate** (one-sided hypergeometric p = 0.045). That is one cell of six.

⛔ **And the headroom is small anyway.** A *perfect oracle* selecting the top 6 of 17
clauses captures only **63.4%** of total frontier-critic output against a **35.3%** random
baseline. Frontier yield is not concentrated, so **no triage instrument on this cohort can
be worth more than a ~1.8× lift**, and the best real predictor reaches at most 1.6× under
a favourable tie-break and 1.1× under an unfavourable one.

**Bottom line: this is a negative result with one weak survivor.** I would not route
production traffic on anything measured here. The recommended next step (§7) is a test,
not a deployment.

---

## 1. INSTRUMENT VALIDATION — my measures reproduce the independent review

Per the amendment, the licence-inheritance class was **recomputed, not copied**
(`build.lic_inherit`, four lines over the module JSON: entries stamped `licence:"textual"`
whose body references a predicate the same module declares `assumed`/`world`).

| class | independent review says | **my independent recompute** | agree |
|---|---|---|---|
| licence inheritance | 32 instances, 12 of 17 modules | **32 instances, 12 of 17** | ✅ exact |
| self-cited borrowed gloss | 20 names, 12 of 17 modules | **20 names, 12 of 17** | ✅ exact |

Both reproduce exactly. The Tier-1 outcome columns are sound, and this is the only claim
in this document that is not limited by n.

*(Minor, recorded: my header-parse counts **24** NEEDS names where the review counts 23
borrowed names. The review counts module `requires` entries; I count node-header NEEDS.
The one-name gap does not touch any statistic below.)*

## 2. AMENDMENT A1, AND WHY IT WAS NOT A FISHING EXPEDITION

The pre-registered outcome `FROZEN` (numbered edit lines in `feedback_1.md`) assumed one
feedback format. The frontier critic uses **three** — numbered list (13 of 17), prose
ordinals (2), and a check report (2) — so the regex returned a silent `0` on four clauses,
including `l1_170_n056`, which is the **highest**-yield clause in the set (4 turns, 8,474
characters of critique). Using it would have inverted the outcome on exactly the clauses
the critic worked hardest on.

`FROZEN` was retired in favour of two format-independent file measurements: `FB_CHARS`
(total frontier-critic output across all rounds for the clause — **literally the bill**)
and `TURNS` (round count). The amendment was written before any correlation was computed,
and **no predictor's predicted direction moves as a result**. Full grounds in `PREREG.md`.

## 3. IS "FRONTIER YIELD" EVEN ONE THING?

Before asking what predicts yield, whether the Tier-1 outcome columns agree:

| pair | Spearman ρ (n=17) |
|---|---|
| `FB_CHARS` ~ `TURNS` | **0.68** |
| `FB_CHARS` ~ `CONV_SELFCITE` | 0.54 |
| `FB_CHARS` ~ `CONV_LICINH` | 0.52 |
| `TURNS` ~ `CONV_LICINH` | 0.45 |
| `CONV_LICINH` ~ `CONV_SELFCITE` | **0.28** |

⚠️ **The *effort* axis (how much the critic wrote, how many rounds) and the *residual
defect* axis (what survived into the converged module) are only loosely coupled, and the
two residual-defect measures barely agree with each other.** A predictor that tracks
effort is not thereby tracking quality. Everything below reports which axis it is on.

## 4. THE PRE-REGISTERED RESULTS

Primary outcome `FB_CHARS`, Tier 1, n=17. Two-sided permutation p, 20,000 draws, no scipy.

| predictor | ρ vs `FB_CHARS` | p | ρ vs `TURNS` | transfer ρ (25) | transfer ρ (20 disjoint) | sign holds? |
|---|---:|---:|---:|---:|---:|---|
| ⭐ **DISAGREE** (n=6) | **−0.154** | 0.76 | **−0.167** | *unavailable* | *unavailable* | ⛔ **wrong way** |
| **BORROWED** | **+0.494** | **0.043** | +0.287 | +0.189 | +0.133 | ✅ but collapses |
| **FLOORDIRTY_T1** | +0.464 | 0.071 | +0.286 | *no variance* | *no variance* | ⛔ **cannot transfer** |
| **PROPLOAD** (N9) | +0.231 | 0.36 | +0.196 | +0.303 | +0.227 | ✅ weak both ways |
| **DISJ** (P4) | +0.144 | 0.60 | −0.115 | **−0.053** | **−0.101** | ⛔ **reverses** |
| **HEDGE** (P7) | +0.342 | 0.19 | +0.195 | **+0.421** | **+0.380** | ✅ **strengthens** |
| *(control)* span_chars | +0.126 | 0.62 | −0.055 | — | — | — |
| *(control)* T1_ENTRIES | +0.337 | 0.18 | **+0.477** | — | — | — |

### Top-6-of-17 capture of total frontier output (the economic question)

Random baseline **35.3%**. Ties broken optimistically / pessimistically — at n=17 with
integer predictors, **the tie-break decides the answer**, which is itself the finding.

| selector | capture (optimistic) | capture (pessimistic) |
|---|---:|---:|
| **oracle (perfect foresight)** | **63.4%** | 63.4% |
| BORROWED | 57.7% | 39.2% |
| HEDGE | 58.9% | 23.1% |
| FLOORDIRTY_T1 | 53.7% | 40.0% |
| T1_ENTRIES *(control)* | 41.5% | 39.4% |
| DISJ | 44.5% | 23.7% |
| PROPLOAD | 31.8% | 31.8% |
| span_chars *(control)* | 26.9% | 26.9% |
| *random* | 35.3% | 35.3% |

⛔ **The oracle ceiling is 63.4%.** The whole available prize is 35.3% → 63.4%. Two
predictors (HEDGE, DISJ) swing by more than 30 points on tie-break alone, which means
their apparent lift is an artefact of how ties are ordered, not a property of the
predictor. **BORROWED and FLOORDIRTY are the only two that beat random under *both*
tie-breaks**, and only barely under the pessimistic one.

## 5. ⭐ THE STARRED CANDIDATE, IN FULL — because n=6 supports nothing else

`DISAGREE` = entries of the eleven-entry review list where arm D (self-review) and arm E
(peer critic) return different PASS/FIX verdicts on the **byte-identical** turn-1 draft.
Tier-1 input: it is a diff. Document-tunedness: **NONE**. This was ranked first before any
number was computed, and it is the one that would have generalized for free.

| clause | DISAGREE | D_FIX | E_FIX | which entries | `FB_CHARS` | `TURNS` | `CONV_LICINH` | IREV |
|---|---:|---:|---:|---|---:|---:|---:|---|
| `l3239_3382_n002` | **0** | 6 | 6 | — | **2582** | **3** | 2 | CORRECT |
| `l1707_1973_n006` | 2 | 0 | 2 | E1, E6 | 2412 | 2 | 3 | DEFECTIVE |
| `l3596_3876_n009` | 1 | 0 | 1 | E1 | 2045 | 1 | 0 | UNSURE |
| `l171_426_n022` | 2 | 4 | 2 | E1, E7 | 1745 | 2 | 2 | CORRECT |
| `l4252_4482_n016` | 1 | 0 | 1 | E10 | 1364 | 2 | 3 | CORRECT |
| `l1001_1107_n005` | 1 | 2 | 3 | E3 | 1043 | 1 | 0 | UNSURE |

**FALSIFIED on the pre-registered criterion, on both limbs.** The falsifier read: "P1 is
falsified if `DISAGREE` has |ρ| < 0.3 against `TURNS`, **or** if it points the wrong way."
Measured ρ = **−0.167** vs `TURNS`, **−0.154** vs `FB_CHARS`: |ρ| < 0.3 *and* wrong way.
Against the Tier-2 verdict, ρ = +0.211, p = 1.0. Nothing here is distinguishable from noise.

⛔ **Look at the top row.** The clause where the two cheap critics agreed *perfectly*
(`DISAGREE = 0`) is the one with the most frontier turns and the second-most frontier
output. They agreed because **both flagged six of eleven entries** — they agreed that it
was a mess. Disagreement was not the signal; **shared alarm** was.

⚠️ **Post-hoc, therefore a hypothesis and not a result** (`analyse.posthoc`, clearly
fenced in the code): the *volume* variant `D_FIX + E_FIX` gives ρ = **+0.548** against
`TURNS`, sign correct. This was computed after the pre-registered join was read, at n = 6,
and I am not entitled to claim it. It is the single most promising thing in this document
and it is exactly the shape of finding that n = 6 manufactures by accident.

**Why n = 6 and not 17:** arm D completed 9 clauses and arm E 13; only 6 overlap. Arm D
lost 47% of its sample to reasoning truncation at `max_tokens` 4,096.

## 6. THE TWO PREDICTORS THAT DIED ON TRANSFER, AND WHY IT MATTERS

**`DISJ` reverses sign** (+0.144 in-sample → −0.053 / −0.101 on transfer). Pre-registered
as dead. Reported as dead.

⛔ **`FLOORDIRTY_T1` cannot be tested on transfer at all: 0 of 25 reference-cohort drafts
are floor-dirty, against 7 of 17 in the loop cohort.** Zero variance. This is the most
generalization-relevant finding in the document and it is not about documents at all:
**the predictor measures the pipeline generation, not the clause.** The reference run is a
later generation in which the mechanical floor issues had been fixed, so a triage rule keyed
to floor-dirtiness would have looked strong in August and silently become a constant the
moment the floor was repaired. Any instrument built on a defect the pipeline is actively
fixing has a half-life, and this one's expired between two runs three weeks apart.

Note also that arm A′ measured the mechanical floor at **7/17 (41%) under an empty
manipulation** — pre-registered in §3 as the reason to distrust this predictor. It was
right to distrust it.

## 7. THE TIER-2 OUTCOME IS CONFOUNDED — reported because it cuts against a tidy story

The independent review's verdict (10 CORRECT / 3 DEFECTIVE / 4 UNSURE) gave the strongest
correlation of anything measured: `T1_ENTRIES` (module size) ρ = **−0.600**, p = 0.013 —
**bigger modules were judged more correct.**

That is not a quality signal. Sorting by module size, the four smallest-but-one modules are
`l3877_3953_n014` (5 entries), `l1001_1107_n005` (6), `l3596_3876_n009` (9) — **all three
UNSURE** — and all three are section headings or purely descriptive spans. The UNSURE
bucket is not "defective"; it is *the reviewer declining to rule on abstention-trigger
clauses*, which are short and therefore produce small modules.

⚠️ So the Tier-2 binary measures **span type**, not defect, and it recovers by the back door
the `ABSTAIN_TRIGGER` predictor I rejected in pre-registration for having a cell of ~4.
It carries no headline here, exactly as pre-registered. **Any triage instrument validated
against this column would be a heading detector wearing a quality-detector's coat.**

---

# ⭐ RANKED CANDIDATE PREDICTORS

Ranked by **what I would actually trust**, which weights transfer and document-generality
above in-sample ρ, per the brief.

### 1. `HEDGE` — defeasibility marker in the narrowed span — **the only survivor**
* **Evidence.** In-sample ρ +0.342 (p 0.19, not significant). Transfer **+0.421** (25
  clauses) / **+0.380** (20 non-overlapping) — *stronger out of sample*, which is the rare
  and reassuring direction. On the transfer cohort **6 of 6 hedged clauses carried an edit
  vs a 64% base rate, one-sided hypergeometric p = 0.045**. As a filter on the 17: hedged
  clauses are 58.8% of clauses and carry **71.3%** of frontier output and 63.6% of turns.
* **Tier: 1** on both cohorts (span regex vs `diffs.json` edit flag / file measurements).
* **Document-tunedness: LOW–MEDIUM.** English-general modal lexicon ("by default",
  "generally", "unless"). Survives a document swap in *mechanism*; the word list was
  assembled with the Model Spec in view and would want re-derivation from a new document's
  register. **Would survive a swap.**
* **Honest ceiling.** Lift is 71.3/58.8 = **1.21×** as a filter. The transfer cell is
  **6 clauses**. Per my own pre-registration: a cell of six is a hypothesis with a p-value
  attached, not a finding.

### 2. `BORROWED` — count of NEEDS names in the node header
* **Evidence.** Best in-sample: ρ **+0.494**, p **0.043** vs `FB_CHARS`; top-6 capture
  57.7% (optimistic) vs 35.3% random. **But transfer collapses to +0.189 / +0.133.** Sign
  holds; effect does not.
* **Tier: 1.** Header parse.
* **Document-tunedness: LOW** in mechanism (the NEEDS block exists for any decomposed
  document; every borrowed name is one manufactured-citation opportunity, and the only
  CORRECT module in the set — `l2474_2554_n004` — has an empty NEEDS block). **But** the
  decomposer is measured 82% document-tuned, so the *distribution* of NEEDS counts is a
  property of this decomposition, not of documents in general. **Would survive a swap in
  mechanism, not in calibration.**
* **Honest ceiling.** The shrinkage from 0.49 to 0.13 across cohorts is what selection on
  17 points looks like. Treat 0.49 as the artefact and 0.13 as the estimate.

### 3. `PROPLOAD` — propositional load of the span (REVIEW_LIST N9)
* **Evidence.** ρ +0.231 in-sample, +0.303 / +0.227 on transfer. Sign holds everywhere,
  significant nowhere. Top-6 capture **31.8% — below the 35.3% random baseline.**
* **Tier: 1.** **Document-tunedness: MEDIUM** (modal lexicon; Model Spec register is
  unusually modal-dense).
* **Honest ceiling.** Consistent and useless. Its consistency is the only interesting thing
  about it; it is the one predictor whose weak effect is the same size in both cohorts,
  which is what a real-but-tiny effect looks like.

### 4. ⛔ `FLOORDIRTY_T1` — unaided draft fails the mechanical checks — **DEAD**
* ρ +0.464 in-sample (p 0.071), and **untestable on transfer: 0/25 variance.** Measures the
  pipeline generation, not the clause. **Document-tunedness: NONE** — and it makes no
  difference, because the axis it varies on is *time*, not *document*. Do not build on it.

### 5. ⛔ `DISJ` — disjunction marker — **DEAD**
* Reverses sign on transfer (+0.144 → −0.101). Pre-registered as dead; reported as dead.
  Document-tunedness LOW, which does not save it.

### 6. ⛔ `DISAGREE` — cheap-critic disagreement — **FALSIFIED, and it was the best idea**
* Wrong sign on both primary outcomes at n=6. **Document-tunedness: NONE** — it remains the
  most *valuable* hypothesis in the space and the cheapest to test properly, which is why
  §8 recommends testing its corrected form rather than abandoning the family. What died is
  *disagreement*; what the data gestures at (post-hoc, n=6) is *shared alarm volume*.

---

# ⭐ THE ONE CHEAPEST TESTABLE RULE I WOULD RUN NEXT

**Not the hedge filter.** The hedge filter is the best *result* I have, but it is not the
best *next experiment*: it rests on a cell of six, its ceiling is a 1.21× lift, and testing
it properly needs fresh frontier adjudications, which are the expensive thing.

**The rule to test: `CHEAP_ALARM` — escalate a clause to the frontier critic when the
combined FIX volume of two cheap critic passes exceeds a threshold.**

> Run the cheap critic **twice** on the same draft (self-review pass + peer-vantage pass).
> Score the clause by the **number of review-list entries flagged FIX by either pass**.
> Escalate the top k% to the frontier critic; accept the cheap critic's repairs on the rest.

**Why this one.**
* It is the **corrected form of the falsified starred candidate.** The data killed
  *disagreement* and pointed at *volume* (post-hoc ρ +0.548 vs `TURNS` at n=6). Testing
  the thing the data pointed at, having declared it post-hoc, is the honest next move.
* **Document-tunedness: NONE.** No span features, no lexicon, no schema knowledge, no
  Model Spec phrasing. It transfers to a second document for free — the property the brief
  asked me to weight above in-sample accuracy, and the only candidate that has it.
* It needs **no new frontier calls to reach n=17**, because arms D and E already exist and
  the outcome columns are already on disk. The gap is only that D covered 9 clauses and E
  covered 13, overlapping on 6.

**The cheapest decisive test:** complete arms D and E to all 17 clauses — **8 arm-D calls
and 4 arm-E calls**, at arm D's and E's own `max_tokens` 7,168 (arm D's 4,096 caused the
47% truncation loss that produced the n=6 hole in the first place). Then re-run
`analyse.py` unchanged against outcome columns that already exist.

**Estimated cost: ≈ $0.05, and no frontier spend at all.**
Grounded in measured per-call spend, not list prices: arm E measured **$0.08335 for 13
clauses × 2 calls** = $0.0032/call; arm A′ measured $0.029952 for 17 calls = $0.0018/call.
12 calls × ~$0.0035 (7,168-token ceiling) ≈ **$0.042**, worst case **$0.06**. Against
`spend.py:BUDGET`, this is negligible.

⚠️ **A cost note that changes the economics of this entire question.** The "frontier
critic" in `ds_opus_loop` is **a model in the harness's own context, not a metered API
call** (`loop.py` docstring; `usage.jsonl` contains no frontier rows — its 5,114 rows are
DeepSeek, GPT and Kimi). The frontier critic's price is therefore **agent attention**, not
dollars: 17 clauses consumed **33 adjudicated turns and 50,541 characters of written
critique**. So the triage instrument's payoff is denominated in frontier-agent turns, and
`TURNS` is the right target. This should be stated in any writeup that quotes a price.

**PRE-REGISTERED FALSIFIER** (fixed now, before the 12 calls):

> `CHEAP_ALARM` is falsified if, at n = 17, the union FIX count has **Spearman ρ < +0.30
> against `TURNS`**, or **ρ < +0.30 against `FB_CHARS`**, or if its **top-6 capture of total
> `FB_CHARS` fails to exceed 35.3% under BOTH tie-breaks**. Any of the three ends it.
> Direction is fixed at **positive**; a negative ρ of any magnitude is a failure, not a
> discovery. The n=6 value (ρ +0.548) is **not** carried forward as evidence and does not
> lower the bar — the 11 clauses being added are the test.

Falsification is a real outcome here: 6 of the 17 points are already in hand and only 11
are new, so the estimate can move a long way, and the pre-registered floor of +0.30 is
above what three of the six surviving predictors achieved.

---

# ⛔ WHAT n = 17 CANNOT SETTLE

Stated plainly, and not softened.

1. **n = 17 cannot separate any two predictors here.** ρ of 0.49 and ρ of 0.23 at n = 17
   have overlapping intervals. The ranking above is a ranking of *my confidence*, driven by
   transfer behaviour and document-generality, **not** a ranking the data establishes.

2. **n = 17 with 6 candidate predictors overfits by default, and I did not run the analysis
   that would have hidden it.** No multivariate fit, no tuned threshold, no predictor
   combination, no cross-validation-selected cutoff — pre-registered in `PREREG.md` §6 and
   held. Any of them would have produced a much better-looking number and no information.

3. **The starred cell is n = 6.** Six clauses, single-digit everything. Both the
   falsification of `DISAGREE` and the post-hoc promise of `CHEAP_ALARM` rest on it. Six
   points cannot distinguish "wrong hypothesis" from "right hypothesis, wrong operational
   form" from "noise" — which is precisely why §8 proposes spending $0.05 to get to 17
   rather than writing a conclusion.

4. **Selection was not blind on the 17.** Declared in `PREREG.md` §0: I had read the
   independent review's verdicts and both arms' per-clause tables before pre-registering.
   Only the 25-clause reference cohort is honestly out-of-sample, and **it is the only place
   my in-sample winner was tested and found to collapse** (BORROWED 0.49 → 0.13). Treat
   every in-sample number as an upper bound with a human prior applied.

5. **The transfer cohort is only semi-independent.** 5 of its 25 clauses are also among the
   17. The disjoint-20 column is reported alongside every transfer figure and moves the
   conclusions not at all — but 20 clauses is still 20 clauses.

6. **The two axes of "yield" are not the same thing** (§3: `CONV_LICINH` ~ `CONV_SELFCITE`
   ρ = 0.28). A rule that routes on effort may route away from the clauses whose *defects
   survive*, which is the failure that would matter most and which this design cannot see.

7. **The Tier-2 column cannot referee any of this** (§7). It measures span type. Four of
   its seven NOT-CORRECT clauses are the reviewer's UNSURE, and the reviewer retracted three
   findings after seeing the critic's turns. One blind reader is worth having and is not
   worth a threshold.

8. **What no amount of this data can settle:** whether escalating the top k% *preserves the
   normative content* the cheap critic's repairs delete. The measured harm — arm E's 5 of 13
   modules acquiring a conclusion-changing defect, and E6 generating the same defect in two
   independent arms — is a harm of the **repair** step, and a triage rule that routes
   *review* attention does not touch it. **A perfect triage instrument would still ship the
   deletions on the un-escalated 100−k%.** That is a different experiment and it is the more
   important one.
