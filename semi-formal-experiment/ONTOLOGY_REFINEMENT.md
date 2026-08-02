# Ontology refinement: a document-grounded optimisation loop

**Status: ⛔ WITHDRAWN — DO NOT BUILD. Failed its drift gate (SEVERE).**

Kept as a record because the *frame* may be reusable; the *decision to run it* was wrong.

**The motivating premise was a logical error.** The design was sold on: "atoms support +0.591,
raw text under a linear model +0.398, judges +0.51-0.55 — a faithful compression should let a
reader of the atoms approach a reader of the text, so the gap means the atoms are lossy."
**Order those numbers: atoms +0.591 > judges +0.51-0.55 > text +0.398.** The atoms are the BEST
reader in the list. There is no gap in that direction, and `HANDOFF.md` had already recorded the
correct reading — and used it to CLOSE the richer-extraction lead.

Four further reasons, any one sufficient:
1. **It predicts its own falsification.** "The vocabulary moves a lot; the panel score moves
   little" is stated as a prediction, and "distortion falls but the panel score does not move"
   is listed as the falsifier. The escape hatch ("if MCC is flat, that is itself the finding")
   makes every outcome a finding — unfalsifiable — and that finding is already established free
   by the 5-draw data.
2. **Under-powered for its single end-measurement.** Noise floor 0.0316-0.037, MDE 0.032-0.045,
   against three prior measurements saying vocabulary change is worth ~0 (5 draws within
   0.006-0.021; the b14->b8 upgrade +0.005 n.s.; 90+ reweighting variants <=0 after selection).
3. **The cost model prices the wrong operation.** $0.28 is the OPEN-vocabulary pass.
   `annotate.py` EVICTS carried vocabulary (`MAX_CARRIED_SITUATION = 80`) precisely because
   re-sending it is expensive; a genuinely closed 361-atom vocabulary needs no-eviction plus
   no-coin enforcement that does not exist. And forcing name agreement across runs was measured
   at **-0.157 MCC** — recorded here as an "open question" while planning to do it ten times.
4. **Its blocking precondition was unmet.** The read-back pilot ran n=5, all one clause kind,
   1 of 4 discrimination conditions — not the pre-registered 125 x 4.

**What to do instead** (drift gate's ranking): the $0 fixes below; then constitution annotation
(~$0.15) as the only independent replication available; then read-back as pre-registered
(~$0.05-0.20), which is worth having on its own. Revisit this only if read-back shows large
same-section distortion AND someone can state a lambda derivation and a stopping rule in advance.

---

**Original status: DESIGN, not built.** Blocked on `readback.py` validating that the
renderer measures what it claims.

---

## The problem this solves

We have 361 atoms over 593 clauses, produced by one annotation pass with one prompt. We have
no procedure for making them better. The obvious move — "change an atom" — is hard because an
atom is a *shared* vocabulary item: re-scoping `refuse_request` perturbs all 53 clauses
carrying it, and those clauses may then want different atoms. That cascades.

Every "better atoms" idea in this project so far has reduced to **more atoms**, because
nothing penalised vocabulary growth.

## The frame

The annotation is a lossy **encoder** (clause → atoms). `readback.render` is the **decoder**
(atoms → English). Read-back measures **reconstruction error**.

So "are the atoms good?" becomes *"does this codebook reconstruct the corpus at a given
compression budget?"* — rate–distortion / MDL. That is a studied problem with a standard
algorithm.

It also formalises a tension we identified informally. Reconstruction alone is maximised by
**one unique atom per clause**: perfect fidelity, zero compression, useless — nothing recurs,
so no cross-clause matching is possible. The description-length term penalises exactly that.
The distinctiveness-vs-reuse tradeoff is not a judgment call; it falls out of the objective.

## The objective

    L = distortion + λ · description_length

**distortion** (from `readback.py`, all panel-free):
* *unfaithful* — the render asserts what the clause does not say
* *insufficient* — the clause requires what the render omits
* *indiscriminable* — the render cannot pick its own clause from near-miss distractors
* *incoherent* — clauses sharing an atom do not share the concept it names

**description_length**: vocabulary size, plus assignment cost (atoms per clause). **This term
does not currently exist anywhere in the project and is the reason every previous refinement
idea degenerated into growth.**

`λ` must be set a priori and declared, never tuned on the panel.

## The loop — and why the cascade dissolves

Incremental repair is what makes cascading hard. We are not obliged to repair incrementally:
**a full re-annotation costs $0.28.** So alternate wholesale (Lloyd's algorithm / EM):

* **E-step** — vocabulary fixed, re-assign across all 593 clauses. One annotation pass under a
  CLOSED vocabulary.
* **M-step** — assignments fixed, revise the vocabulary. Mechanical proposals from the
  clause × atom incidence structure.

No propagation logic and no consistency repair: the assignment is simply recomputed. At $0.28
a pass, ~20 iterations costs ~$6 — far more than this alternation usually needs.

## M-step moves

From the ontology-evolution literature (Stojanovic; Noy & Klein, *Ontology evolution is not the
same as schema evolution*) — split and merge affect the concept lattice differently and should
not be treated as inverses.

| move | trigger |
|---|---|
| MERGE a, b | co-occur almost always; neither discriminates without the other |
| SPLIT a | a's clauses are heterogeneous — coherence fails on a's pairs |
| DROP a | never changes any render's discriminability |
| RE-SCOPE a | faithful on some clauses, unfaithful on others |
| ADD | a clause is insufficient and no existing atom covers the gap |

**Formal Concept Analysis** over the clause × atom incidence gives the complete concept
lattice, and it is purely combinatorial — no model call. It identifies which distinctions do
work and which atom sets are redundant, which is exactly the M-step proposal engine.

## ⚠️ THE INVARIANT THAT MAKES OR BREAKS THIS

**The panel is held out. Entirely. It is the test set.**

Every term in `L` is computed from the document — clause text, atoms, renders. Nothing in the
loop may read `behaviours.json`, `panel-coverage.json`, `panel_v2`, `panel_universe` or
`benchmark`. Score against the panel **once, at the end**, and never feed that score back.

If the loop ever optimises against the panel we have (a) violated contract invariant 9 and
(b) destroyed the only instrument we have for judging the result. This project has already had
one lead withdrawn for proposing a panel-fitted progress metric one indirection out; this is
the same hazard with a bigger blast radius, because the loop would run it dozens of times.

Enforce structurally: the refinement module must pass `test_no_reference_leak.py`'s static and
dynamic guards, and the panel score must be computed by a separate process.

## A prediction from data we already have

The five behaviour-atom draws share only **32–53%** of their names yet land within
**0.006–0.021 MCC** of each other. That is a **flat objective surface with many near-equivalent
optima**.

Predictions, recorded before running:
1. The loop converges quickly.
2. The *vocabulary* moves a lot; the *panel score* moves little.
3. Therefore **judge iterations on reconstruction error, not on MCC.**

If MCC is genuinely flat across good vocabularies, **that is itself the finding** — it would
mean the specific vocabulary was never load-bearing, which reframes the whole approach.

## What would falsify this being worth doing

* Read-back shows the renders are already faithful and sufficient → little distortion to
  reduce → the loop has nothing to optimise.
* Distortion falls but the held-out panel score does not move → the objective is not aligned
  with the task, and we should say so rather than keep iterating.
* The M-step proposals are dominated by MERGE with no SPLIT → the vocabulary is already too
  coarse and the compression term is mis-weighted.

## Cost

| | |
|---|---|
| one E-step (full re-annotation, closed vocabulary) | ~$0.28 |
| one distortion evaluation (stratified sample) | ~$0.05 |
| M-step (FCA + mechanical proposals) | $0 |
| **per iteration** | **~$0.33** |
| ~10 iterations | ~$3.30 |

Against $6.17 remaining. Affordable, but it is most of the remaining budget — so read-back must
validate first, and the falsification conditions above must be checked at iteration 1, not 10.

## Open questions for review

1. Is MDL the right objective, or does rate–distortion with an explicit rate constraint fit
   better? λ is a free parameter and we have no principled way to set it.
2. Distortion mixes four measures on different scales. Weighted sum, or lexicographic, or a
   constrained objective (minimise description length subject to distortion ≤ ε)?
3. Alternating optimisation converges to a local optimum. Given the observed flat landscape,
   do restarts or annealing buy anything, or just cost?
4. Is FCA tractable here? The lattice over 593 × 361 can be large in the worst case.
5. The E-step re-annotates under a closed vocabulary. Earlier measurement showed forcing name
   agreement across runs cost **−0.157 MCC**. Does the closed-vocabulary E-step inherit that
   penalty, and does it matter if we are optimising reconstruction rather than MCC?
