# Graph equivalence protocol (pre-registered 2026-08-10)

**Status: DESIGN, frozen before any DeepSeek build has run.** This file
defines how we will decide whether a second graph of the same document
(e.g. the DeepSeek stability rerun) is *equivalent* to the golden graph even
though it will certainly be *different*. Written in advance so the comparison
cannot be tuned to make the answer come out "equivalent". Per repo rules,
this document is never handed to an adjudication seat.

## Why names are excluded from every metric

The 2026-08-10 replay measurements showed ~0% convergence on invented
predicate names across independent runs, while the *concepts* converged. Any
metric that compares `needs`/`provides` names across graphs measures naming
luck, not understanding. All comparison below happens in **line-space** (the
document's own coordinates) and **prose-space** (adjudicated meaning).

## The four measurements

Graphs A (golden) and B (candidate), same document, same line numbering.

### 1. Node alignment (mechanical)

For each line of the document, each graph names an owning node (or
`uncovered`). Build the bipartite overlap graph: node a∈A matches node b∈B
with weight = Jaccard of their owned line-sets. Alignment classes per node:

- **1:1** — a and b own near-identical line sets (Jaccard ≥ 0.8).
- **split/join** — a's lines are covered by 2–3 nodes of B (or vice versa)
  whose union has Jaccard ≥ 0.8 vs a. Granularity difference, not a
  disagreement, PROVIDED class-2 below passes for the group.
- **misaligned** — everything else. Goes to adjudication.

Metric: fraction of document lines whose owner falls in class 1 or 2.

### 2. Claim agreement on aligned mass (seat-adjudicated)

For every 1:1 pair and split/join group: a seat receives the shared span
text + both establishes-sets (graph identity hidden, order randomized) and
answers: do these assert the SAME claims about this text — same obligations,
same strength (modal profile per `sweep_modals.profile`), same conditions?
Verdict: same / differs, with grounds. Mechanical pre-filter: modal-profile
mismatch between the two establishes-sets auto-routes to the seat.

### 3. Edge agreement (mechanical in line-space, residue adjudicated)

Every needs-edge in A is a pair of line-regions (needer span → provider
span), found by resolving the need's name inside A only. An edge is
**matched** in B if B connects nodes overlapping both regions (any of B's
own names). Report edge recall (A-edges matched in B) and precision
(B-edges matched in A). Unmatched edges go to adjudication: is the edge
real in the document (a defect in the graph missing it) or an artifact
(a defect in the graph asserting it)?

### 4. Boundary objects (mechanical)

Uncovered sets equal as line-sets; final danglings equal as *adjudicated
concepts* (by prose, not name — e.g. both graphs must leave the
usage-policies external reference dangling and must NOT leave
chain-of-command dangling).

## The verdict rule

**Equivalent** = every adjudicated disagreement from classes 1–4 is ruled
*benign* (granularity, paraphrase, naming) — i.e. zero standing rulings of
*substantive divergence* (different obligation, missing edge, wrong owner).
Equivalence is a *judgment-backed zero*, not a similarity threshold: we do
NOT pre-set "edge recall ≥ 0.9 = pass", because a single substantive missing
edge (cf. the reverted patient-pricing change) can matter more than ten
benign ones. Similarity numbers are reported as *descriptive statistics*
alongside the verdict.

Seat-load estimate: with ~590 nodes and the observed convergence, expect
~50–150 adjudications per comparison — feasible at small-model seat rates,
subject to seat validation (divergence-from-frontier check on a 10-item
sample first, per the working rule).

## What gets built (not yet built)

`graph_compare.py` — measurements 1, 3, 4 and the modal pre-filter of 2;
emits `compare_report.json` with the adjudication queue. RED check before
first use: feed it graph A vs a mutated copy of A (one merged node, one
deleted edge, one strengthened establishes, one re-covered dangling) and it
must flag exactly those four.
