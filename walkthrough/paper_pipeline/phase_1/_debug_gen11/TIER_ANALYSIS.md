# TIER_ANALYSIS.md — what distinguishes the retry tiers, and what would move the mass to attempt 1

Orthogonal cut to `SUMMARY.md` / `class_*.md`, which analyse **mechanisms**. This file asks
a different question: **given the tier distribution, what separates a clause that lands on
attempt 1 from one that needs two, or five?** Where the two cuts touch, this file cites the
mechanism file by name rather than renaming it.

**Zero API spend on the translation harness.** Every number below is re-analysis of bytes on
disk. The two live experiments (§6, §7) were run with local **Haiku** subagents, which cost
no project budget. Nothing under `runs/`, `translation_sample/runs/` or `repair_graveyard/`
was written to.

Reads and honours: `_debug_gen11/README.md` (evidence rules), `SUMMARY.md`, the `class_*.md`
files, and **`ANALYSIS_REVIEW_verdict.md`** — DC-1, DC-5 and DC-7 are addressed head-on in
§4.3, §5.3 and §5.4 respectively.

---

## 0. Population and the generation label

Every `run.json` under `resolve_runs/graph_v2/translation_sample/runs/` was read: **319
clause-translation observations** across 13 runs with results (2 run dirs hold no `run.json`).
Prompt generation is `sha256(prompt_system.txt)[:16]`, so no two generations are ever pooled.

| system_sha | runs | obs | max_attempts | schema_sha | first-try |
|---|---|---|---|---|---|
| `2926e21351af71c6` | 08-10 20:35, 20:55 | 30 | 3 | `6a54b599` | **10%** |
| `e9a6c4a2826d45e8` | 08-10 21:24 | 15 | 3 | `6a54b599` | 33% |
| `88aea33ea822e44d` | 08-10 21:30 | 15 | 3 | `6a54b599` | 40% |
| `ab3cb9446df97d3a` | 08-10 21:44, 21:55 | 30 | 3 / 5 | `6a54b599` | 40% |
| **`5ff9daf7fe58845f` (gen 11)** | 08-10 22:54, 23:41; 08-12 09:03, 13:33; 08-14 16:34, 17:33; 08-15 07:00 | **229** | 5 | `c2d4b3e9` → `30ef9db2` | **43%** |

> ⚠️ **The system sha is not a complete generation label.** Inside `5ff9daf7fe58845f` the
> `schema_sha` changes (`c2d4b3e9` → `30ef9db2`) and `max_tokens` drops 16384 → 4096 at 08-14.
> The **checker** therefore moved inside "gen 11". Where a claim could plausibly turn on that,
> this file reports it twice: once on the full gen-11 pool, once on the **08-14 pair** (the
> 100 clauses of `OUTCOME_TABLE.md`, one `schema_sha`, one draw per clause, complete runs).
>
> ⚠️ **08-15 caveat carried forward** from `SUMMARY.md` §1 and `TRANSLATION_REPAIR_CENSUS.md`
> §9: `20260815-070038` was in flight when the mechanism analysis was written. Its numbers
> here are a **snapshot** and **must not be pinned into any test**.

---

## 1. The tier table

Pooled (all 319 obs): 1 → 39% · 2 → 20% · 3 → 22% · 4 → 1% · 5 → 17%. That matches the
commissioning figure. But the pooled 3-tier is inflated by the three-attempt generations, where
"3" *is* exhaustion. On the 5-attempt generations the shape is the one that matters:

| tier | gen-11 pool (n=228) | 08-14 pair (n=100) | what the tier IS |
|---|---|---|---|
| 1 | 98 — **43%** | 47 — **47%** | clean first pass |
| 2 | 54 — 24% | 20 — 20% | one repair round, then done |
| 3 | 26 — 11% | 10 — 10% | two rounds |
| 4 | 4 — 2% | 2 — 2% | three rounds |
| 5 | 46 — 20% | 21 — 21% | exhausted; **44 of 46 produced no module** |

The 4-tier is a rounding artefact (n=4 pooled). The real distribution is **trimodal**:
land immediately (43%), land after one round (24%), or die (20%). Tier 5 is not "tier 4 plus
one" — it is a **different regime**: 96% of it ends with no module, and the mechanism analysis
already shows 40% of its rounds return byte-identical bytes
(`class_repair-fixed-point.md`, safe-to-act-on per the review).

---

## 2. Tier is mostly NOT a stable property of the clause

This is the finding that reframes the commissioning question, and it is measured, not inferred.

**Same clause, byte-identical `user_sha`, byte-identical `system_sha`, independent draw.**
Within gen 11 there are 34 such repeated cells (180 distinct `(clause, user_sha)` pairs over
228 observations).

* Median **within-cell spread in attempt count is 3**; the spread is ≥2 in **24 of 34** cells.
* Of the 20 cells drawn exactly twice: first-try in **both** draws — **0**; in exactly one —
  **10**; in neither — **10**. **50% discordance.** (This cell set is enriched for hard clauses
  — re-runs target stale/failed clauses — which is why "both" is empty. It bounds the *stability*
  of the label, not the base rate.)
* The clean like-for-like: the **19 clauses that burned all 5 attempts and produced nothing in
  `20260814-173322`** were re-drawn in `20260815-070038` under identical `system_sha`,
  `schema_sha`, `provenance_hash` and per-clause `user_sha`:

  | 08-14 attempts | → 08-15 attempts | n |
  |---|---|---|
  | 5 (dead) | **1** | **9** |
  | 5 (dead) | 2 | 3 |
  | 5 (dead) | 3 | 2 |
  | 5 (dead) | 4 | 1 |
  | 5 (dead) | 5 | 4 |

  **9 of 19 clauses that had just failed five consecutive times passed on attempt 1 of a fresh
  draw (47%).** Snapshot — not pinnable.

**Consequence for the 80% target.** A per-clause first-try rate of 43% with this much
draw-to-draw variance means no static feature can explain most of the gap: a large part of the
tier assignment is resampling noise, and the deterministic features below explain the rest.
This corroborates and extends the review's SAFE-TO-ACT-ON item on the fresh-draw counterfactual
(08-14: $0.1780 / 95 calls / 0 modules vs 08-15: $0.0780 / 45 calls / 14 modules), and it is
the same phenomenon `class_repair-fixed-point.md` sees from the cost side.

---

## 3. Features that were tested

Per clause: span line-count and character length; graph `needs` and `provides` counts;
speech-act type of the span (blind-classified, §5.4); presence of a `[node narrows this span
to: …]` narrowing; distinct predicate count in the produced module; output token/char count;
list-item / heading / glossary / prose shape; plus features the data suggested — the
**attempt-1 draft's own shape** (`requires`, `inputs`, `ontology`, bodies) and the
**arity-mismatch** marker the review identified (DC-5).

Two of them turned out not to exist as variables in this population and are reported as such:
**no clause in any run has a source span the graph stores as a list item, heading or glossary
entry in a separable form** — the graph's `spans[].quote` has already stripped list markers, so
"list item vs prose" is not measurable from the artifacts and is **not reported as a null
result**; it is unmeasured. `provides ≥ 1` covers only 39 of 213 observations and separates
nothing (p = 1.0).

---

## 4. What separates the tiers

Fisher exact, two-sided. Population: gen-11 observations whose **attempt-1** response was a
translation attempt (not an abstention), N = 213. Wilson 95% intervals.

### 4.1 The features that DO separate

| feature (measured on the attempt-1 draft unless noted) | with | without | p |
|---|---|---|---|
| **≥1 ontology entry carrying a `body` AND zero `inputs` declared** | **15%** [8–27] (n=59) | **49%** [41–57] (n=154) | **<0.0001** |
| `requires` lists ≥2 borrowed names | 22% [15–32] (n=86) | 51% [43–60] (n=127) | **<0.0001** |
| ≥1 ontology entry carrying a `body` | 31% [23–39] (n=131) | 54% [43–64] (n=82) | **0.0009** |
| **graph node has ≥2 `needs`** *(exogenous — known before the call)* | 24% [15–36] (n=59) | 45% [38–53] (n=154) | **0.0046** |
| declares zero `inputs` | 26% [18–37] (n=80) | 47% [39–56] (n=133) | 0.0024 |
| **a declared name used at a WRONG ARITY (DC-5)** *(all 5 gens, N=315)* | **0%** [0–26] (n=11) | 41% [35–46] (n=304) | **0.0041** |

The top row replicates on the independent 08-14 pair, harder: **10%** [3–25] (n=31) vs **58%**
[45–70] (n=57), p < 0.0001.

Tier profile of the composite, gen-11, a1-translated:

| tier | n | share with body-bearing ontology **and** zero `inputs` | share with `requires` ≥2 | share with graph `needs` ≥2 |
|---|---|---|---|---|
| 1 | 84 | **11%** | 23% | 17% |
| 2 | 53 | 36% | 51% | 36% |
| 3 | 26 | 35% | 62% | 50% |
| 4 | 4 | 50% | 75% | 50% |
| 5 | 46 | 43% | 46% | 24% |

### 4.2 The features that do NOT separate

Reported plainly, because three of them are the ones a reader would expect to work:

| feature | with | without | p |
|---|---|---|---|
| span > 250 chars | 31% (n=35) | 41% (n=178) | 0.35 |
| span line count > 1 | 67% (n=3) | 46% (n=97) | — (n too small; **no finding**) |
| `[node narrows this span to: …]` present | 41% (n=145) | 37% (n=68) | 0.65 |
| attempt-1 declares ≥5 distinct predicates | 34% (n=92) | 44% (n=121) | 0.16 |
| attempt-1 raw output > 3000 chars | 35% (n=91) | 43% (n=122) | 0.32 |
| graph node has ≥1 `provides` | 38% (n=39) | 40% (n=174) | 1.00 |

**Span size, output size, narrowing, and how many predicates the model invents are all null.**
The monotone-looking gradient in raw predicate count (72% at ≤3 → 0% at >10 in the *final*
module) is an artefact of conditioning on the final artifact — dead clauses have no final
module. Measured on the attempt-1 draft, where every observation has a value, it dissolves
(p = 0.16). **Do not report predicate count as a separator.**

### 4.3 What the surviving features mean — and the DC-1 correction

The separating features are not "the clause is hard". They are all one shape: **the attempt-1
draft wrote a derivation rule whose body names have no declared source.**

* `body` present + `inputs` empty = a rule resting on nothing. That is the finding class the
  checker calls `undeclared-body-name` (`schema.py`, the `declared | requires | inputs` set).
* `requires ≥ 2` and graph `needs ≥ 2` = more borrowed names to gloss and to keep straight.

⚠️ **This does NOT resurrect M1's "no legal declaration bucket" claim, which `ANALYSIS_REVIEW_verdict.md`
DC-1 shows is false** — `ontology` accepts a body-less ground atom and the prompt says so in
bold. My data **independently corroborates DC-1**: attempt-1 drafts that use the body-less
ontology route (≥1 ontology entry, none with a body) land first-try at **60%** [36–80] (n=15)
against 38% [31–45] for everything else, and drafts with **no** body-bearing ontology entry at
all land at **54%** vs **31%**. The route works. It is used by only **15 of 213 (7%)** attempt-1
drafts. **The defect is discoverability, exactly as DC-1 says — not a missing bucket.**

---

## 5. Answering four specific questions

### 5.1 Does the number of findings predict the tier? **No.**

| findings in the first repair message | n | resolved in ONE round | went to 5 |
|---|---|---|---|
| 1 | 54 | 41% | 39% |
| 2 | 28 | 36% | 36% |
| 3 | 17 | 47% | 35% |
| 4 | 28 | 43% | 29% |

Flat. **A clause with four defects is no less likely to be fixed in one round than a clause with
one.** Tier is governed by defect *kind*, not defect *count* — which is why the ranked list in
§8 is by class and not by volume.

### 5.2 The 2-attempt tier — the cheapest wins

Gen-11, 54 clauses whose whole repair history is one round. What that one round said:

| class of the single repair round | n | share |
|---|---|---|
| **`borrowed-no-gloss` alone** | **25** | **46%** |
| `undeclared-body-name` alone | 9 | 17% |
| `borrowed-no-gloss` + `undeclared-body-name` | 5 | 9% |
| everything else (11 classes, ≤2 each) | 15 | 28% |

**57% of the 2-attempt tier's single repair round mentions `borrowed-no-gloss`** — a borrowed
predicate name declared in `requires`/`inputs` with no `concepts` gloss. That is **M2**
(`class_borrowed-gloss-split.md`), and the mechanism analysis's verdict on it stands: expensive,
nearly harmless (kill rate 1/24), graph-stage-preventable, and **the review lists M2's mechanism
and its graph-stage verdict as SAFE TO ACT ON AS WRITTEN**.

Share of **all** repair rounds this class represents:

| population | rounds mentioning it | rounds where it is the ONLY class | finding lines |
|---|---|---|---|
| gen 11 (302 rounds, 711 lines) | 78 — **26%** | 41 — 14% | 145 — **20%** |
| 08-14 pair (130 rounds, 276 lines) | 28 — **22%** | 17 — 13% | 48 — 17% |

So: one defect class, ~a quarter of all repair rounds, ~half of the cheapest tier, and its own
mechanism file says the graph already holds the answer (`root_graph.production.json` stores
`needs[].prose`). **The already-named fix is `TRANSLATION_FIX_PLAN.md` Fix C** (`requires`/`inputs`
entries carry name+arity+gloss). It is ranked #3 there by *kills*; by **first-try leverage in
this corpus region it is the top prompt/grammar candidate**, and §6 tests it live.

### 5.3 DC-5, the arity-blind declaration check — tested as a predictor, as instructed

`schema.py`'s declaration set is built by name only
(`known = declared | {p.split("/")[0] for p in requires + inputs}`), so `inputs: ['conflict/2']`
legalises `conflict(P1,P2,C)`. Computed over every stored attempt-1 draft in all five
generations:

* **11 of 315 attempt-1 drafts** use a declared name at an arity it was not declared at.
* **0 of the 11 landed on attempt 1** (0% [0–26] vs 41% [35–46]); **73% ended `unrepaired`**
  against a 26% base rate. Fisher **p = 0.0041**.
* Scanning every **final** `.json` module in every run finds **0** instances — consistent with
  the review's "four instances corpus-wide", which counts modules on *unrepaired* clauses (those
  never get a `.json`; their last draft lives only in the transcript). Different unit, same
  phenomenon.

**It is the sharpest categorical marker in the whole feature table** — but n = 11, the CI is wide,
and it is a *marker* of a confused draft as much as a cause (the check is blind to it, so it
cannot itself be the reason the draft failed schema). Report as: strong, cheap to detect, small
denominator, and the review's one-line checker change is worth making on its own merits because
it converts a silent link-stage failure into a named schema finding.

### 5.4 DC-7 adjudicated: an outcome-BLIND classification of all 100 spans

Per the coordinator's instruction, this was settled rather than assumed. The 100 `ESTABLISHES`
+ source-quote pairs of the 08-14 pair were written to a shuffled file under opaque 8-hex keys,
with **no outcome, no clause id, no run data**, and classified by a Haiku subagent instructed to
read nothing else. Labels were joined to outcomes only afterwards.

| blind label | n | first-try | abstained | unrepaired |
|---|---|---|---|---|
| ABOUT-THE-DOCUMENT | 59 | **58%** [45–69] | 11 | 9 |
| DEFINITIONAL | 25 | 32% [17–52] | 0 | 6 |
| NORMATIVE | 13 | 31% [13–58] | 0 | 4 |
| EXAMPLE | 3 | 33% | 1 | 0 |

* **NORMATIVE 31% vs NON-NORMATIVE 49%**, p = 0.25 — **not significant, and the sign is the
  opposite of a routing rationale**: normative spans are, if anything, slightly *harder*.
* **The review's DC-7 conclusion is confirmed and strengthened.** My blind pass makes 87 of 100
  non-normative (the review read ~32 of 36 first-pass successes that way); we differ on the exact
  count but agree completely on the consequence. A router that diverted non-normative spans would
  divert **ABOUT-THE-DOCUMENT, the single easiest bucket at 58% first-try** — it would throw away
  the cheapest successes. **Do not build span-type routing on this evidence.**
* The one span-type split that survives is a **different** one: **ABOUT-THE-DOCUMENT 58% vs
  everything else 32%, p = 0.015**. Documented as an observation; it is not a lever, because you
  cannot make a definitional span into a document-description span.

---

## 6. EXPERIMENT 1 — does a one-paragraph instruction kill `borrowed-no-gloss`?

**Design.** Cohort: the 10 clauses of the 08-14 pair whose attempt-1 repair message contained
`borrowed-no-gloss` and nothing else. Each was given the **byte-identical stored system prompt**
(`20260814-173322/prompt_system.txt`, 36,605 chars, `sha 5ff9daf7fe58845f`) and its **byte-identical
stored user prompt** (`<clause>.prompt_user.txt`). Arm A = that prompt verbatim. Arm B = that
prompt plus one added block, "RULE G": *every name in `requires` or `inputs` is borrowed and MUST
also get a `concepts` entry with name, arity and a one-sentence gloss; write them before `asserts`;
count them.* Each arm was run by local **Haiku** subagents, one first answer per clause, no
iteration, no validator access. Outputs were then validated through `schema.validate_all(obj,
clause_id=…, known_clause_ids=…)` exactly as `translate.py` does, against the 773-id corpus.

**Result.**

| arm | clean at attempt 1 | Fisher |
|---|---|---|
| A — stock gen-11 prompt | **5 / 10** | |
| B — stock + RULE G | **10 / 10** | **p = 0.033** |

Paired, and this is where the honest reading lives:

| clause | arm A | arm B |
|---|---|---|
| n036, n046, n049, n051, n056 | PASS (5/5) | PASS (5/5) |
| **n071, n072, n075, n082, n087** | **FAIL (0/5)** | **PASS (5/5)** |

**The effect is carried entirely by the second five clauses** (0/5 → 5/5, Fisher p = 0.0079); on
the first five, Haiku under the stock prompt did **not** reproduce the defect DeepSeek made, so
those clauses are uninformative about the fix. The five failures were the *same* finding the
stored DeepSeek run got on the *same* clauses:
`` `message_role_definition/2` is borrowed but has no gloss `` (n071, n072),
`` `conversation_definition/2` is borrowed but has no gloss `` (n075),
`` `tool_definition/1` … `` (n082), `` `assistant_definition/1` … `` (n087). Arm B produced zero
findings of any class on all ten.

**The test was not vacuous.** Every one of the 20 modules declared at least one borrowed name
(`requires` 1–2 in all cases), so every module was exposed to the requirement. The arm-A failures
wrote a `concepts` list that glossed *something else* and left the borrowed name bare; arm B's
counted formulation closed exactly that gap.

**What this is and is not evidence for.**

* ⚠️ **Haiku is a DIFFERENT MODEL from `deepseek-ai/DeepSeek-V4-Flash-0731`. This is evidence
  about the INSTRUCTION, not a guarantee for DeepSeek.**
* What it does establish: a second, unrelated model reading the same 36 kB spec makes the
  *identical* omission on the *identical* clauses. The defect is a property of **how the
  requirement is stated**, not of one provider's quirks. The requirement is *already in the
  prompt* (`10_output_format.md` states it with a ⭐) — which is precisely Fix C's diagnosis: it
  is **a join between two lists**, invisible from where the model is standing when it writes
  `inputs` last. Restating it as a counted, local obligation closed it 5/5 where it fired.
* ⚠️ **Batch confound, stated rather than hidden.** Each arm was run by two subagents of five
  clauses each, and the A/B split coincides exactly with the batch split — A1 passed all five,
  A2 failed all five. Agent-level variation therefore **cannot** be separated from clause-level
  difficulty in this design. The mitigating evidence is that arm B's two batches both scored 5/5,
  and that A2's five failures reproduce the stored DeepSeek findings clause-for-clause rather
  than being arbitrary. **A clean replication should randomise clauses across subagents and run
  ≥3 draws per cell.** Do not quote 5/10 → 10/10 as a measured effect size; quote it as a
  directional result on n=5 informative clauses.
* Cross-clause carryover within a subagent context is possible but symmetric across arms.

---

## 7. EXPERIMENT 2 — not run, and why

The obvious companion — testing whether a worked example of the **body-less ontology ground atom**
raises first-try on the `undeclared-body-name` cohort (17 clauses in the 08-14 pair) — was
**deliberately not run in this pass.** DC-1 has just re-scoped that remedy from "widen `inputs`"
to "make the existing route discoverable via a worked example", and this repo's standing rule is
that **the worked example is itself the artifact under test** (`DECISION_bad_worked_examples.md`,
`test_prompt_examples.py`). Writing one inside an analysis pass, on a hypothesis one day old,
would test a strawman. It is the single highest-value experiment left; §8 rank 2 states its
design and its falsifier.

---

## 8. Ranked list — changes most likely to move first-try rate

Reach = measured share of gen-11 clause-observations the change touches (N = 228 unless stated).
Ceilings come from the counterfactual "if class X never fired at attempt 1, every clause whose
attempt-1 defect set was a subset of X becomes first-try".

| # | change | already named as | reach | measured effect | falsifier |
|---|---|---|---|---|---|
| **1** | **Make the borrowed-name gloss a local, counted obligation** — grammar-enforced (`Borrowed` object carrying name+arity+gloss) or, as a zero-risk interim, the RULE G paragraph | **Fix C**, `TRANSLATION_FIX_PLAN.md`; mechanism **M2** / `class_borrowed-gloss-split.md` | **12%** of clauses have this as their *sole* attempt-1 defect; the class appears in **26% of all repair rounds** and **57% of the 2-attempt tier** | first-try 43% → **55%** on the counterfactual; live Haiku A/B (§6): **10/10 vs 5/10** overall, **5/5 vs 0/5** on the clauses where the defect actually fired (p=0.008), with a batch confound stated in §6 | Replicate §6 with clauses randomised across subagents and ≥3 draws per cell — **if arm A's pass rate then matches arm B's, the §6 result was batch variance, not the instruction.** Then run the same A/B against DeepSeek. **If arm B still emits `borrowed-no-gloss` on ≥3 of 10, the fix does not transfer and rank 1 is wrong.** Also: if a grammar-enforced version raises `gloss-restates-name` (M3) by more than it removes M2, it has traded a cheap defect for a lethal one |
| **2** | **A worked example showing the body-less ontology ground atom** — make the existing legal route discoverable | **DC-1**'s own recommendation; the residue of `class_no-legal-bucket.md` after M1 collapses | `undeclared-body-name` is the sole attempt-1 defect on **15%** of clauses and appears in **46% of all repair rounds** (the largest single class). The composite predictor (body-bearing ontology + zero `inputs`) covers **28%** of attempt-1 drafts at **15%** first-try | drafts already using the route: **60%** first-try (n=15) vs 38%; drafts with no body-bearing ontology at all: **54%** vs **31%** (p=0.0009). Counterfactual ceiling with Fix C: **75%** | Add the example, re-run the 17-clause `undeclared-body-name` cohort. **If body-less ontology usage does not rise above the 7% baseline, the example did not teach the route.** If usage rises but first-try does not, the route was never the blocker. ⚠️ n=15 on the 60% figure — treat as direction |
| **3** | **Spend the repair budget on fresh draws instead of repair rounds** for clauses that fail twice | `class_repair-fixed-point.md` (SAFE TO ACT ON per the review); the fresh-draw counterfactual | **20%** of clauses reach tier 5; they burn **65%** of repair spend and 96% of them yield nothing | **9 of 19** five-attempt losses passed on **attempt 1** of a byte-identical re-draw. Cost: 08-14 $0.1780/95 calls/0 modules vs 08-15 $0.0780/45 calls/14 modules | Re-draw the 4 clauses that failed in **both** 08-14 and 08-15 (`n056`, `n058`, `n078`, `n084`). **If a third independent draw also fails all four, those are genuinely hard clauses and the resampling story does not cover them.** ⚠️ 08-15 is a snapshot; do not pin |
| **4** | **Make the declaration check arity-aware** (one line: report "declared at /2 but used at /3") | **DC-5**, `ANALYSIS_REVIEW_verdict.md` | **3.5%** of attempt-1 drafts (11/315) | **0/11 first-try**, 73% unrepaired vs 26% base, p=0.0041 | Ship the check, re-run. **If the newly-named finding is repaired in one round on ≥half of the 11, it was a real silent defect; if the clauses still die, arity mismatch was a symptom and the change buys diagnosis, not yield.** ⚠️ n=11 |
| **5** | **Route by graph `needs ≥ 2`** — the only *exogenous* separator found: give those clauses a longer prompt, a stronger model, or the graph's stored `needs[].prose` pre-filled | new; complements M2's graph-stage verdict | **26%** of clauses (59/228) | 24% [15–36] first-try vs 45% [38–53], p=0.0046 | Pre-fill `concepts` from `needs[].prose` for the `needs≥2` set and re-run. **If their first-try rate does not close at least half the gap to 45%, the count is a proxy for something else (topic, region) and not a lever.** |
| — | **NOT recommended: span-type / normativity routing** | **DC-7** | would divert 87% of clauses | normative vs non-normative **31% vs 49%, p=0.25** — wrong sign, not significant; ABOUT-THE-DOCUMENT is the *easiest* bucket | — |
| — | **NOT recommended: gating on span length, output length, narrowing, or predicate count** | — | — | all p > 0.15 (§4.2) | — |

### Does this reach 80%?

Counterfactual ladder on gen-11 (baseline 43%; 08-14 pair in brackets, baseline 47%):

| classes removed at attempt 1 | first-try | reach |
|---|---|---|
| `borrowed-no-gloss` (rank 1) | **55%** [57%] | 12% |
| + `undeclared-body-name` (rank 2) | **75%** [81%] | 32% |
| + unsafe-variable | **82%** [85%] | 39% |
| + read-back slots | 86% [89%] | 43% |
| every classified attempt-1 defect | 92% [—] | — |

**Two classes get to ~75–81%. Three get past 80%.** The commissioning target is reachable
without touching the corpus, the graph, or the model — but only if ranks 1 and 2 both land, and
rank 2's remedy is a worked example that has not been written or tested yet.

⚠️ **The ladder is an upper bound, not a forecast.** It assumes a fix removes its class without
introducing another, and the mechanism analysis measured defect trading at **51.5% of clauses with
≥2 repair rounds** (`SUMMARY.md` §4 — and note the review's DC-8 restores the census's 57%
per-round figure and re-reads the difference as a *population* effect, ~2.7× weaker trading in
this corpus region). Half of every removed defect may reappear as a different one. Treat 75% as
the honest expectation for ranks 1+2 and re-measure rather than assume.

---

## 9. Reproduction

All figures come from re-reading `run.json`, `*.transcript.json`, `*.prompt_user.txt`,
`*.json` and `prompt_system.txt` under `resolve_runs/graph_v2/translation_sample/runs/`, plus
`resolve_runs/graph_v2/runs/ds7/root_graph.production.json` and
`resolve_runs/graph_v2/node_corpus_all.json`. Finding classes are assigned by message shape (the
method `translation_repair_census.py` uses), extended with the six classes that fire only outside
the L1-170 region. Experiment 1's artifacts (both system prompts, the 10 user prompts, 20 model
outputs, validator results) are in the session scratchpad; the validator call is
`schema.validate_all(obj, clause_id=<id>, known_clause_ids=<773 corpus ids>)`.
