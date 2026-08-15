# SUMMARY.md — gen-11 translation post-mortem

Scope: every costly outcome of `20260814-163457-together-deepseek-v4-flash` (12 clauses)
and `20260814-173322-together-deepseek-v4-flash` (88 clauses). Prompt generation 11
(`system_sha 5ff9daf7fe58845f`), identical `schema_sha` and provider params across both.
**Zero API spend.** Full per-clause data in `OUTCOME_TABLE.md`; reconciliation with the
earlier census, fix plan and review in `PRIOR_WORK_MAP.md`.

---

## 1. Outcome totals

| | |
|---|---|
| clauses | **100** |
| paid calls (transcript turns, all matched 1:1 to `usage.jsonl`) | **230** |
| repair rounds | **130 (57% of calls)** |
| recorded spend | **$0.4051**, of which repair **$0.2415 (60%)** |
| **translated** | **69** — 36 first-pass, 33 after 1-4 repair rounds |
| **unrepaired** (5 attempts, no module) | **19** |
| **abstained** | **11** + 1 `abstained_under_repair` |
| **modules produced** | **69 / 100** |
| repair rounds returning byte-identical bytes | **52 / 130 (40%), $0.1026** |

> ⚠️ **Standing caveat on the 08-15 comparison.** `20260815-070038-together-deepseek-v4-flash`
> was **still in flight** while this analysis was written (its `run.json`, `health.jsonl`
> and `inflight/` are live, and graveyard entries were still appearing). Its outcomes are a
> **snapshot**, they will change, and **no count from it may be pinned into a test** — per
> `TRANSLATION_REPAIR_CENSUS.md` §9 and `AGENTS.md`. Nothing under `runs/` or
> `repair_graveyard/` was written to by this analysis. Its 08-14 numbers, by contrast, are
> from two completed runs and are stable.

Attempts: 1 → 47 · 2 → 20 · 3 → 10 · 4 → 2 · 5 → 21.
The 21 five-attempt clauses are 21% of clauses and **65% of repair rounds**.

---

## 2. The two rankings, which disagree

They disagree by design and the disagreement is the actionable part.

### By paid cost

| # | mechanism | rounds | $ | share of repair $ |
|---|---|---|---|---|
| 1 | **M1** invented descriptive predicate has no legal declaration bucket | 81 | **0.1196** | 50% |
| 2 | **M2** borrowed name declared in one list, glossed in another | 29 | 0.0435 | 18% |
| 3 | **M5** cross-module identity drift / upstream loss (link stage) | 15 | 0.0226 | 9% |
| 4 | **M4** `ontology` used as a declaration list (unsafe variable) | 14 | 0.0221 | 9% |
| 5 | **M3** tautological predicate — gloss can only restate the name | 11 | 0.0159 | 7% |
| 6 | **M6** `read_back_slots` read as "this rule's variables" | 5 | 0.0085 | 4% |
| 7 | **M7** honest invention penalised (`assumed`, no named inference) | 3 | 0.0058 | 2% |
| — | residue (M8 abstention-with-content, M9 gloss punctuation / textual-no-citation) | 3 | 0.0035 | 1% |

### By modules lost

| # | mechanism | modules lost | kill rate (lost ÷ clauses touched) |
|---|---|---|---|
| 1 | **M1** | **12 of 19** | 12/30 = **40%** |
| 2 | **M5** | **3** | 3/4 = **75%** |
| 3 | **M3** | **2** | 2/5 = **40%** |
| 4 | **M4** | 1 | 1/8 = 13% |
| 4 | **M2** | 1 | 1/24 = **4%** |
| — | M6, M7, residue | 0 | 0% |

### Why the two rankings differ, and the two ways that difference has misled before

* **M2 is expensive and almost harmless** (18% of spend, 4% kill rate). Optimising the
  cost table alone would put M2 second in the queue; it is fifth by the thing that
  matters.
* **M5 is cheap and lethal** (9% of spend, 75% kill rate) and, worse, two of its three
  losses are *downstream of M1 losses* — `n047` needs a concept `n043` never exported,
  `n087` needs one `n065` never exported. **Losses compound; rounds do not.** A
  cost-ranked plan cannot see that.
* **M3 is tiny by every count except the one that matters**: 5 clauses, 2 dead modules,
  and one of them (`l171_426_n005`) is a chain-of-command obligation whose module was
  otherwise complete and was lost to a single gloss.

**A third ranking exists and beats both: cost that is recoverable without any design
work.** `class_repair-fixed-point.md` — 40% of repair rounds returned byte-identical
modules, $0.1026 (42% of repair spend), and 96% of those rounds sit on chains that never
converged. That is larger than M2+M5+M4+M3+M6+M7 combined and needs no schema change, no
prompt change, no `contract_hash` bump and no model call to validate.

---

## 3. Graph-stage-preventable, per mechanism

The question the fix pass asked: could a **graph-stage** decision — classifying what kind
of thing a span is, or fixing what the graph publishes about it — have prevented this,
or is it genuinely translation-stage?

| mechanism | verdict | reasoning |
|---|---|---|
| **M1** | **Graph-stage for the volume, translation-stage for the residue** | 16 of the 19 unrepaired and **all 12 abstentions** are non-normative spans (glossary, about-the-document, applicability, example). A graph-stage speech-act decision would stop sending meta text to a translator whose only output shape is a rule — and abstention already costs 1 call and works. **But** 4 unrepaired are genuine obligations (`n047`, `n052`, `n056`, `l171_426_n005`), and ~20 non-normative spans translated first-pass, so span type alone neither predicts failure nor covers it. The residual — *no legal list holds a descriptive property of a defined term* — is a schema/adapter defect and survives perfect routing. |
| **M2** | **Graph-stage, cheaply** | 70% of the findings name a predicate the graph itself supplied, and `root_graph.production.json` already stores `needs[].prose` — which is exactly the gloss the checker demands. The graph holds the answer and the pipeline retypes it through the model. |
| **M3** | **Translation-stage (arguably check-stage)** | All five offending predicates were model-invented, not graph-supplied, and two of the five clauses are ordinary obligations. The open question is whether the check is well-posed for spans whose whole content is the term. |
| **M4** | **Translation-stage** | The illegal state is `OntologyFact.body: Optional[str]`. Graph-stage routing would remove most of *this slice's* volume (7 of 8 clauses are non-normative), but the earlier census measured this as the #1 class in normative corpus regions, so the graph route does not generalise. |
| **M5** | **Split: graph-stage + scheduling + not-a-defect** | Arity is not part of a graph concept's identity (`{"name", "prose"}`, no arity) — graph-stage, and 3 of 146 borrowed names already disagree. Provider-before-consumer ordering is scheduling. `requires-unprovided` at partial corpus is **expressly not a defect** (standing ruling in the cleared graveyard `VERDICT.md` files). |
| **M6** | **Translation-stage** | A field name and its neighbours. The graph has no bearing. |
| **M7** | **Graph-stage (low confidence, n=3)** | Triggered where the node's `establishes` claims more than its span supports, so `textual` is unavailable and `assumed` is honest. The check is well-posed; the merge decision was the graph's. |
| **X (fixed point)** | **Neither — loop design** | Orthogonal to all of the above; lands independently. |

**Short answer for the fix pass: M1 (volume), M2, M5 (identity) and M7 are graph-stage-
preventable. M3, M4 and M6 are translation-stage. M1's residue and the whole of X are
neither.**

---

## 4. Defect trading — the 57% claim, re-tested on this run's data

The review measured defect trading at **57% of post-first rounds (71/124)** with a masking
test (97 genuinely new vs 5 latent). Re-measured on these 100 clauses, the answer depends
entirely on the unit, and the difference is worth recording because it is easy to quote
the wrong one:

| unit of measurement | result |
|---|---|
| post-first **rounds** introducing a new `check_id` | 4 / 96 — **4%** |
| post-first **rounds** introducing a new finding *class* (message shape) | 19 / 96 — **20%** |
| post-first **rounds** introducing a new class *or a new predicate name* | 23 / 96 — **24%** |
| **clauses** with ≥2 repair rounds that ever traded | 17 / 33 — **51.5%** |

**The 57% figure replicates as a per-clause rate (51.5% here), not as a per-round rate
(20-24% here).** Both documents that quote it describe it as "the share of post-first
rounds", which on this data would be 20%. The phenomenon is real either way — the
mechanism is visible clause by clause (`l1_170_n039`: unsafe-variable → bind the variable
→ the binder is undeclared; `l1_170_n016`: M1 → M4 → M1; `l1_170_n053`: M1 → M4 → M1 →
M2) — but **the number should be restated with its unit before it is used to rank
anything.**

The complementary half is this run's own finding: post-first rounds that do *not* trade a
defect largely do nothing at all — 40% return byte-identical bytes.

---

## 5. Residue, and what is deliberately not a class

* **M8 — abstention with content** (`l171_426_n003`, 1 round, $0.0001). The model
  abstained but left `claims`, `concepts` and `requires` populated and gave no reason:
  *"an abstention with no reason is a skip in disguise"*. One instance; recorded, not
  elevated.
* **M9 — gloss punctuation** (`l1_170_n077`: *"gloss contains a quote, brace, backslash or
  newline"*) and **textual licence with no citation** (`l1_170_n083`). Two rounds. The
  second is the mirror of M7 and is discussed there.
* **`requires-unprovided` at partial corpus is NOT a defect.** The standing ruling is in
  `repair_graveyard/_cleared_*/VERDICT.md` and is honoured throughout this analysis.
  `customer_of_openai_api/1` in `n087` is the exception — a name no node in the graph
  provides — and is a real under-export.
* **The graveyard added no unique evidence**, consistent with the census review's finding
  that its transcripts are byte-identical copies of the run transcripts. Its value here
  was the written rulings in the `_cleared_*` `VERDICT.md` files, not its data.

---

## 6. What this run says that the earlier work could not

1. **Four finding classes here have no entry in the census taxonomy** —
   `gloss-restates-name`, `assumed-no-inference`, `concept-declared`, `situation-input` —
   and would land in its `OTHER:` bucket. Two of them killed modules. See
   `PRIOR_WORK_MAP.md`.
2. **The class ranking is corpus-region-dependent.** `unsafe-variable` was #1 by cost in
   the census's gen-11 population and is #4 here; `act-not-in-acts`, `closure-missing`,
   `closure-ungoverned`, `citation-not-in-corpus` and `clause-id-mismatch` — five of the
   census's top nine — **fired zero times** in these 100 clauses, because the document's
   overview and definitions sections govern almost no acts. Fixes A, B and E target
   classes that do not exist in this region.
3. **The dominant class here (M1: 50% of spend, 63% of losses) is the one class the fix
   plan explicitly declined to fix**, and the one candidate that addresses it (F) is
   re-scoped by this evidence — see `PRIOR_WORK_MAP.md` §4.
4. **A byte-identical retry recovers most losses.** 14 of 19 unrepaired clauses translated
   in `20260815-070038` under identical prompts, for 45 calls against the 95 the repair
   loop spent producing nothing.
