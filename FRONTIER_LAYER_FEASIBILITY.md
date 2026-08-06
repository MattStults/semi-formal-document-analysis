# Is a behaviour-general representation even possible? — the study to run before designing one

**Status: ANALYSIS PLAN, for approval. No design, no build, no spend.** Written 2026-08-05.

`PROJECT_ASSESSMENT.md` Option D argues for a frontier pass that maps the document once and
then answers arbitrary behaviour questions cheaply. `FRONTIER_LAYER_EXPERIMENT.md` says how to
*stage* that. **Neither establishes that it is possible**, and that is the prior question.

This document does three things: states the question precisely, sets out what we already know
from 294 catalogued failures, and specifies a cheap study that would answer it before anyone
designs a schema.

---

## 1. The question, stated precisely

We want a representation `R(passage)` and a query encoder `Q(behaviour)` such that

> relevance(passage, behaviour) is computable from `R(passage)` and `Q(behaviour)` alone —
> without re-reading the passage.

`R` is built **once**, expensively, without knowing which behaviours will be asked. Everything
after is cheap.

**It fails in exactly one way:** for some behaviour X, deciding relevance needs information from
the passage that `R` did not capture. So the feasibility question is:

> **Is the union, over all plausible behaviours, of "information needed to decide relevance"
> finite, small, and enumerable in advance?**

If yes, one well-designed pass carries it and the approach works. If the union keeps growing as
you add behaviours, no fixed schema suffices and the honest answer is to call a frontier model
per query.

---

## 2. This is a question about documents, not about models

Worth stating, because it changes who can answer it and how cheaply.

A normative passage has a bounded grammar: someone acts, on someone, under conditions, with
some force (must / should / may), toward some value, with exceptions. That is close to a
frame-semantic or deontic decomposition, and it is finite *per frame type*.

**The project has already tried this.** The current ontology has typed atoms —
situation / act / entity / value — carrying deontic force, principal chains, and
condition/exception roles. That representation captures **45% of the distance** from keyword
matching to a frontier panel. So the question is not "can a structured representation work at
all" — it demonstrably does part of the job. The question is sharper:

> Is the remaining 55% made of **missing slots** (finite, addable) or of something **no fixed
> schema can hold**?

Two candidate sources of "no fixed schema can hold":

* **Frame diversity** — the document may contain passage *types* whose slots differ
  fundamentally. Party-protection rules ("don't harm X") and answer-quality standards ("be
  clear, be accurate") are not the same shape, and a schema built for one may not express the
  other. We have direct evidence this is live: roughly 30 catalogued failures are
  answer-quality passages where "who is affected" has no answer, because the passage is not
  about parties at all.
* **Document indeterminacy** — cases the document genuinely does not settle. Two competent
  reviewers split on whether a user's own employer is a "third party". **No representation of a
  document can settle what the document leaves open.** This residue is irreducible in
  principle — but it is not fatal, because the right move is for `R` to carry *the ambiguity
  plus a recorded ruling*, which is exactly what the interpretation layer does. It converts an
  unanswerable question into an answered-and-revocable one.

---

## 3. What 294 catalogued failures already suggest

We have an unusual asset: every tool-vs-panel disagreement on three behaviours, classified by
cause. That is a partial answer to the saturation question already, and it is mildly
encouraging.

* **294 disagreements collapse into 8 cause classes.** Not 294 idiosyncratic problems.
* **The largest class (155) decomposes into ~4 sub-causes**, each of which maps to a nameable
  missing slot: who is affected, what is implied but unsaid, what kind of obligation this is,
  and a threshold/calibration residue that is not a representation problem at all.
* **The four walls we hit over months map to four slots**, not four hundred.

**But this evidence is weak in a specific way, and the weakness is the whole reason to run a
study.** All 294 cases come from **three** behaviours, and the slots were discovered by
*failing* on those three. A taxonomy fitted to three behaviours tells you almost nothing about
the fourth. The saturation curve has three points on it.

---

## 4. The study: slot saturation

**The question it answers:** does the set of required slots close, or keep growing with each new
behaviour?

**Method.** For a sample of catalogued disagreements, a reviewer answers one question per case:

> *What information about this passage, recorded in advance and without knowing the behaviour,
> would have been sufficient to decide this case correctly?*

The answer is a **slot** — named, defined, and reusable — or one of three terminal verdicts:

| verdict | meaning |
|---|---|
| **new slot** | a dimension not yet in the inventory. Record it. |
| **existing slot** | already in the inventory; the representation just didn't capture it here. |
| **indeterminate** | the document does not settle it. Goes to the ruling channel, not the schema. |
| **not a representation problem** | threshold calibration, matching mechanics, panel error. Out of scope. |

**Then plot the curve: new slots discovered against cases examined, ordered by behaviour.**

* Curve flattens within a behaviour, and flattens *further* on each new behaviour →
  **feasible.** The union is small and mostly behaviour-independent.
* Curve flattens within a behaviour but jumps at each new behaviour → **the tail is
  per-behaviour.** Fixed schema won't generalize; this is the finding that kills Option D.
* Curve never flattens → the residue is idiosyncratic; use a frontier model per query.

**The discipline that makes it honest:** run behaviour-by-behaviour and **freeze the slot
inventory before starting each new behaviour**, recording it with a sha. The jump at each
boundary is the measurement. If slots are added while reading a behaviour and then
retro-fitted, the curve is meaningless — the same failure mode as fixing freely in stage 2 of
the experiment design.

**Cost.** This is *reading and classifying*, not annotating a corpus. A sample of 60–100 cases
across three behaviours is enough to see a curve. It can be done by a human, or by a frontier
seat with a written brief and human spot-checks — the second is cheaper and is the same
seat-plus-golden-review pattern already used here. **Order $5–20, or a few hours of reading.**

**Extending the curve past three behaviours is the expensive part**, because it needs
disagreement data on behaviours we have not judged. That is exactly what the held-out set is
for — and it is why the study should run on the three dev behaviours *first*: if the curve
already fails to flatten across three, we have the answer without spending a one-shot resource.

---

## 5. What the layer design must then specify (only if the study says feasible)

Recording these now so the study is designed to inform them:

1. **The frame inventory.** How many passage *types*, and the slot set for each. The study's
   "new slot" answers cluster into this.
2. **Per-slot capture contract.** For each slot: a closed vocabulary or a stated open one, a
   required verbatim license quote, and a fixed decision procedure. `S3B_ATTRIBUTION_TASK_DESIGN.md`
   is the worked template — one slot, done to this standard, including the parity gate.
3. **The query encoder.** The under-examined half. `R` is useless without a principled way to
   turn "avoiding over- and under-caution" into a query over slots — and that behaviour is
   *not* obviously a slot query, which is a warning worth taking seriously. **If `Q` requires
   bespoke work per behaviour, the per-behaviour cost has simply moved from scoring to query
   construction and Option D's economics collapse.** The study should record, per case, whether
   the needed slot is queryable from the behaviour's own definition text.
4. **The indeterminacy channel.** Ambiguities carried as recorded rulings with reasoning,
   revocable — the interpretation layer, already designed.
5. **The open slot.** A free-text "what else is salient here" field, whose contents are the
   first place to look when the schema fails.

---

## 6. What we can reuse

* **`S3B_ATTRIBUTION_TASK_DESIGN.md`** — one slot specified to production standard: closed
  vocabulary, verbatim license quote, fixed ordered procedure, blinded seat, cheap-model /
  frontier parity gate with pre-registered thresholds, golden review over the boundary. This is
  the per-slot template; it does not need reinventing.
* **`INTERPRETATION_LAYER_DESIGN.md`** — the ruling channel: approver, date, reasoning,
  revocation, provenance in the answer trail.
* **The census method** — the instrument that produced the classified failures this study reads.
* **The cycle ceremony** — for whatever ships.

---

## 7. What would make me say "don't build this"

Stated now, so it is not rationalized later:

* The slot curve **jumps at each behaviour boundary**. That is the per-behaviour tail, and it
  means the representation is not general.
* A large fraction of cases come back **"not queryable from the behaviour definition"** — `Q`
  needs bespoke work per behaviour, so the cost merely moved.
* **Frame diversity is high** — many passage types with disjoint slot sets — which multiplies
  the schema and the annotation cost without bounding either.

---

## 8. Recommended next step

Run §4 on the three dev behaviours, freezing the inventory at each boundary. It costs tens of
dollars and a few hours, spends **no** one-shot resource, and returns one of three answers:
*feasible and small*, *feasible but per-behaviour*, or *not feasible*.

That is a better first purchase than a schema — and if the curve is flat, the schema largely
writes itself from the slot inventory the study produces.
