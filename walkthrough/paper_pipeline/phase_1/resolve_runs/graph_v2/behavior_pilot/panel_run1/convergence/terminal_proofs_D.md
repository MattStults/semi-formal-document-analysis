# Terminality proofs for the class-D nodes

Scope: the 10 nodes classified `"class": "D"` ("structural-projection; annotations
panel-confirmed; the true terminal family") in
`panel_run1/convergence/bucket0_reclassification.json`.

Evidence admitted (the only files read):
- `[B0]` `panel_run1/convergence/bucket0_reclassification.json`
- `[SC]` `panel_run1/convergence/satisfiability_census.json`
- `[CC]` `behavior_pilot/CONVERGENCE_CAMPAIGN.md`

Truth ledgers, ablation receipt files, `recall_fn_census.json`, and the 9f receipts
were NOT readable in this task; wherever a schema premise requires them directly, the
premise is marked **PREMISE GAP** rather than asserted.

## Formal setting (used in every proof below)

The instrument computes engagement `E(n,b) = f(V(n), D(b))`, where
`V(n) = (Acts(n), Governs(n), Protects(n), Contexts(n), Actors(n), Purposes(n))`, each
component a set drawn from a finite vocabulary, `D(b)` is behaviour `b`'s declaration,
and `f` is a fixed set-intersection rule. Because `f` is fixed and reads only `V(n)`
and `D(b)`, two nodes with identical feature vectors are indistinguishable under every
`D`: for all `b`, `V(n) = V(t)` implies `E(n,b) = E(t,b)`. Terminality of `n` therefore
means: no admissible `(D, bridges)` yields the target verdict for `n` while preserving
the verdicts of the nodes `T` it collides with — either because the collision is
vector-identical (`[SC]` status `UNSAT`), or because the only separating components are
ones no admissible `D` can exploit without a *recorded measured* loss.

## Schema-level finding that governs 9 of the 10 proofs

`[SC]` reports, per node, `verdict_needed`, `status`, and `colliding_correct_nodes`.
`[CC]` defines the census reading: terminal-by-census means "provably UNSAT at the
current feature set (satisfiability census: vector-identical to correct opposite-verdict
nodes)" `[CC, "ON THE NATURE OF THE TERMINAL SET"]`.

Census status of the 10 class-D nodes `[SC]`:

| # | node | verdict_needed | status | colliding_correct_nodes |
|---|------|----------------|--------|--------------------------|
| 1 | avoiding-over-and-under-caution::l2126_2404_n016 | relevant | SEPARABLE | (empty) |
| 2 | avoiding-over-and-under-caution::l2126_2404_n023 | relevant | SEPARABLE | (empty) |
| 3 | avoiding-over-and-under-caution::l609_698_n013 | relevant | SEPARABLE | (empty) |
| 4 | harm-avoidance-to-third-parties::l1368_1541_n004 | relevant | SEPARABLE | (empty) |
| 5 | harm-avoidance-to-third-parties::l609_698_n016 | relevant | SEPARABLE | (empty) |
| 6 | harm-avoidance-to-third-parties::l609_698_n018 | relevant | SEPARABLE | (empty) |
| 7 | harm-avoidance-to-third-parties::l831_1000_n011 | relevant | **UNSAT** | `l831_1000_n013` |
| 8 | helpfulness::l2126_2404_n016 | relevant | SEPARABLE | (empty) |
| 9 | helpfulness::l2126_2404_n019 | relevant | SEPARABLE | (empty) |
| 10 | helpfulness::l2126_2404_n045 | relevant | SEPARABLE | (empty) |

Two consequences follow from the admitted evidence alone, and they apply to every
section below:

1. **Nine of the ten class-D nodes are recorded SEPARABLE with an empty collision set.**
   The schema's (P1) requires a non-empty `T = {t1..tk}` whose verdict differs from
   `n`'s; `[SC]` records `colliding_correct_nodes: []` for those nine, so `T` cannot be
   instantiated from the admitted evidence. (P2) requires either `V(n) = V(t_i)` (cited
   to `[SC]` `UNSAT`) or a stated measured loss; `[SC]` records the opposite status for
   those nine. On the admitted evidence the census does not support terminality for
   them; it supports separability.
2. **All ten have `verdict_needed: "relevant"`, i.e. they are FN-side (missed)
   nodes, not precision-side residue.** `[CC]` states the terminal precision-side
   residue explicitly and enumerates it — "bucket 0 FP-side (THE RESEARCH ANSWER
   CANDIDATE): 11 nodes … uncertainty-expression genus permission (l2821_3040_n015 x
   help), unprompted-info (n031), omission-transparency (l797_830_n005),
   explicitness-limits (l1108_1367_n015), objectivity-balance (l2126_2404_n004),
   hash-honesty (l2821_3040_n025/n023), long-term-goals (l3041_3146_n007), code-quality
   (l3147_3238_n010 x2), addressing (l1707_1973_n040)" `[CC, TERMINAL STATE (v16)]`.
   **None of the ten class-D ids appears in that list.** `[CC]` further records "FN
   side: 132, all in classified recall classes (buckets 3/4); FN bucket 0 = 0", and
   opens "PHASE 2: FN-SIDE CONVERGENCE", in which "every FN is fix-or-adjudicated"
   and the boundary claim is deliberately deferred: "the terminal-11 precision residue
   is DEFERRED until FN-side convergence (fixes may re-engage some with new grounds; the
   boundary claim is stated once, over both sides)" `[CC, PHASE 2]`. The admitted
   evidence therefore records the FN side as **not yet declared terminal**.

Nothing below appeals to intuition; each section states only what `[B0]`, `[SC]`, and
`[CC]` record, and marks the rest as gaps.

---

## 1. avoiding-over-and-under-caution::l2126_2404_n016

- **(P1)** Target verdict: `relevant` `[SC: avoiding-over-and-under-caution /
  l2126_2404_n016 / verdict_needed]`. A differing-verdict set `T` is **not** available:
  `colliding_correct_nodes: []` `[SC, same entry]`. Truth ledgers were not readable.
  **PREMISE GAP: (P1) cannot be instantiated — no node `t` with a differing verdict is
  recorded for this node in any admitted file.**
- **(P2)** `[SC]` records `status: "SEPARABLE"`, not `UNSAT`; so `V(n) = V(t_i)` is not
  supported and is in fact contradicted for this node. The alternative branch requires a
  *stated measured loss* on the differing components; `[B0]` gives the classification
  note "panel-confirmed labels; anti-hedging norm bears on caution through its rationale,
  not its beneficiary/quality projections" `[B0]` — a structural description of *why* the
  projection misses, with no measurement attached. `[B0]` records an ablation receipt for
  exactly one node, `l2821_3040_n025` ("WITH ablation receipt (fix costs 5 TPs for 2 FPs
  …)"), which is a class-A node, not this one. **PREMISE GAP: (P2) unsupported — census
  status is SEPARABLE and no ablation receipt or measured loss is recorded for this
  node or for an "anti-hedging/rationale-projection" cluster.**
- **(P3)** Supported: `[B0]` records "panel-confirmed labels" for this node. Label
  correctness of `V(n)` is therefore independently confirmed.
- **(C)** **Not concluded.** With (P1) uninstantiable and (P2) contradicted by `[SC]`,
  no derivation of "no admissible `(D, bridges)` satisfies both `n` and `T`" is
  available. The admitted evidence positively records the opposite disposition
  (`SEPARABLE`, empty collision set), and `[CC, PHASE 2]` records the FN side as still
  under fix-or-adjudicate. The corresponding "every extension recorded recall-negative or
  memorization-grade" clause is also unsupported for this node: `[CC]` names three
  measured refusals — "global purpose filter, subtype granularity, scoped conjunction" —
  as refinements of "the accuracy/register clusters" `[CC, CAMPAIGN RESULT / ON THE
  NATURE OF THE TERMINAL SET]`, not of the anti-hedging rationale cluster.

## 2. avoiding-over-and-under-caution::l2126_2404_n023

- **(P1)** Target verdict `relevant` `[SC: avoiding-over-and-under-caution /
  l2126_2404_n023]`; `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: no
  differing-verdict `T` recorded; (P1) cannot be instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]` — `UNSAT`/vector-identity is contradicted.
  `[B0]` note: "panel-confirmed; engage-rather-than-avoid rationale" — a structural
  account, no measurement. **PREMISE GAP: (P2) unsupported; no ablation receipt for this
  node or its rationale cluster in `[B0]` or `[CC]`.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, for the reasons in §1; and the extension clause is
  unsupported, the three recorded measured refusals `[CC]` attaching to the
  accuracy/register clusters rather than to this one.

## 3. avoiding-over-and-under-caution::l609_698_n013

- **(P1)** Target verdict `relevant` `[SC: avoiding-over-and-under-caution /
  l609_698_n013]`; `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be
  instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed labels; the
  moralizing-BAD example bears via rationale". **PREMISE GAP: (P2) unsupported — no
  vector identity, no recorded measured loss.**
- **(P3)** Supported: "panel-confirmed labels" `[B0]`.
- **(C)** **Not concluded.** Note additionally that `[SC]` records a *separate*
  `helpfulness / l609_698_n013` entry, also `relevant`/`SEPARABLE` — neither carries a
  collision set, so no cross-behaviour `T` is available either.

## 4. harm-avoidance-to-third-parties::l1368_1541_n004

- **(P1)** Target verdict `relevant` `[SC: harm-avoidance-to-third-parties /
  l1368_1541_n004]`; `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be
  instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed;
  no-new-disallowed-content limit bears via rationale". **PREMISE GAP: (P2)
  unsupported.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, per §1.

## 5. harm-avoidance-to-third-parties::l609_698_n016 (the H-R1 "permit")

- **(P1)** Target verdict `relevant` `[SC: harm-avoidance-to-third-parties /
  l609_698_n016]`; `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be
  instantiated — the census records no colliding correct node for the permit.**
- **(P2)** `status: "SEPARABLE"` `[SC]` — vector identity is contradicted. `[B0]` note:
  "THE permit: three Fable readings confirm protects=user; relevance flows through
  exception structure - the named terminal family". "Relevance flows through exception
  structure" is a structural claim about the projection, with no measured loss attached
  in any admitted file. **PREMISE GAP: (P2) unsupported.**
- **(P3)** Supported, and the strongest of the ten: "three Fable readings confirm
  protects=user" `[B0]` is an explicit independent confirmation of a `V(n)` component.
- **(C)** **Not concluded.** No extension attempt for the exception-structure cluster is
  recorded recall-negative or memorization-grade in `[B0]`, `[SC]`, or `[CC]`; and
  `[CC, ON THE NATURE OF THE TERMINAL SET]` states that "the search space of alternative
  atomizations is HARD, not hopeless" and that "future ideas re-open it", so the
  admitted evidence does not close the extension clause for this node.

## 6. harm-avoidance-to-third-parties::l609_698_n018

- **(P1)** Target verdict `relevant` `[SC: harm-avoidance-to-third-parties /
  l609_698_n018]`; `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be
  instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed; dual-use
  rationale". **PREMISE GAP: (P2) unsupported.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, per §1.

## 7. harm-avoidance-to-third-parties::l831_1000_n011 — the one census-supported node

- **(P1)** Target verdict for `n` is `relevant` `[SC: harm-avoidance-to-third-parties /
  l831_1000_n011 / verdict_needed]`, and the census records exactly one colliding
  correct node, `T = {l831_1000_n013}` `[SC, same entry / colliding_correct_nodes]`. By
  the census's own definition — terminal-by-census means "vector-identical to correct
  opposite-verdict nodes" `[CC, ON THE NATURE OF THE TERMINAL SET]` — a member of
  `colliding_correct_nodes` is a *correct* node carrying the *opposite* verdict.
  (P1) is supported at this remove; the truth ledger itself was not readable, so the
  verdict of `l831_1000_n013` is taken from the census's construction rather than read
  directly. *Minor citation gap: ledger not directly inspected.*
- **(P2)** Supported: `status: "UNSAT"` `[SC]`, which by `[CC]`'s definition is exactly
  the statement `V(n) = V(l831_1000_n013)` under the current feature set. Since `f` is a
  fixed function of `(V(n), D(b))`, `V(n) = V(t)` gives `E(n,b) = E(t,b)` for every
  declaration `D(b)`; no choice of `D` or of bridges (which act by determining which
  vocabulary items enter the vectors and the declaration, not by distinguishing equal
  vectors) can assign the two nodes different engagements.
- **(P3)** Supported: `[B0]` records "panel-confirmed; manipulation-limit rationale" for
  this node, independently confirming the labels constituting `V(n)`.
- **(C)** From (P2) and the fixed-`f` argument: **no admissible configuration
  `(D, bridges)` satisfies both `n` and `T = {l831_1000_n013}`** — engaging `n` engages
  `l831_1000_n013` identically, and by (P1) that flips a correct node. With (P3),
  the collision is not an annotation error. Separation therefore requires extending the
  vocabulary so that `V(n) ≠ V(t)`.
  The schema's final clause — that *every* extension attempted for this cluster is
  recorded recall-negative or memorization-grade — is **PREMISE GAP: partial.** `[CC]`
  records three measured refusals, "global purpose filter, subtype granularity, scoped
  conjunction", forming "a three-measurement pattern … in which every finer distinction
  trades recall ~1:1" `[CC, CAMPAIGN RESULT]`, and attributes the measured local minima
  to "three refinements of the accuracy/register clusters" `[CC, ON THE NATURE OF THE
  TERMINAL SET]`. No extension attempt is recorded specifically for the
  manipulation-limit cluster to which `[B0]` assigns this node. The terminality of
  `n` against the *current* feature set is proved; the exhaustion of extensions for
  *this* cluster is not recorded in the admitted files.

## 8. helpfulness::l2126_2404_n016

- **(P1)** Target verdict `relevant` `[SC: helpfulness / l2126_2404_n016]`;
  `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed; anti-hedging
  bears via rationale (helpfulness twin of the caution node)". Both twins (§1 and this
  section) are recorded SEPARABLE with empty collision sets, so the twinning does not
  supply a `T` either. **PREMISE GAP: (P2) unsupported.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, per §1.

## 9. helpfulness::l2126_2404_n019

- **(P1)** Target verdict `relevant` `[SC: helpfulness / l2126_2404_n019]`;
  `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be instantiated.**
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed;
  fulfill-requests rationale". **PREMISE GAP: (P2) unsupported.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, per §1.

## 10. helpfulness::l2126_2404_n045

- **(P1)** Target verdict `relevant` `[SC: helpfulness / l2126_2404_n045]`;
  `colliding_correct_nodes: []` `[SC]`. **PREMISE GAP: (P1) cannot be instantiated.**
  (`[SC]` also carries a distinct `harm-avoidance-to-third-parties / l2126_2404_n045`
  entry, likewise `relevant`/`SEPARABLE` with an empty collision set; the class-D
  classification in `[B0]` is on the helpfulness node.)
- **(P2)** `status: "SEPARABLE"` `[SC]`. `[B0]` note: "panel-confirmed;
  withholding-the-clear-answer example". **PREMISE GAP: (P2) unsupported.**
- **(P3)** Supported: "panel-confirmed" `[B0]`.
- **(C)** **Not concluded**, per §1.

---

## Summary of the evidentiary position

- **1 of 10** class-D nodes (`harm-avoidance-to-third-parties::l831_1000_n011`) has
  (P1), (P2), (P3) supported by the admitted evidence and yields the terminality
  conclusion against the current feature set; its only residual gap is the "every
  extension attempted for this cluster" clause of (C).
- **9 of 10** have (P3) supported and (P1)/(P2) unsupported: `[SC]` records them
  `SEPARABLE` with empty `colliding_correct_nodes`, which is the census's *negation* of
  the vector-identity premise, not merely silence about it.
- All 10 are `verdict_needed: relevant`, i.e. FN-side; `[CC]` records the FN side as
  "all in classified recall classes (buckets 3/4); FN bucket 0 = 0" and opens PHASE 2
  FN-side convergence with the boundary claim explicitly deferred. None of the 10
  appears in `[CC]`'s enumerated terminal precision-side residue of 11.
- The class-D note in `[B0]` describes these as "structural-projection (annotations
  panel-confirmed; the true terminal family)". On the admitted evidence, the
  *panel-confirmation* half of that description is supported for all 10; the *terminal*
  half is supported for 1 and is contradicted by the census for the other 9. The
  structural claims ("bears via rationale, not its beneficiary/quality projections",
  "relevance flows through exception structure") are accounts of the projection, and no
  measured loss or ablation receipt is recorded for any of these clusters in the
  admitted files — `[B0]` attaches an ablation receipt to `l2821_3040_n025` (class A)
  only, and `[CC]`'s three measured refusals are attributed to the accuracy/register
  clusters.

What would close the gaps: the truth ledgers (to instantiate `T` directly, in case the
census's collision computation is scoped more narrowly than the ledger's), the 9f
receipts, and any per-cluster ablation measurement for the rationale-projection,
exception-structure, dual-use, and anti-hedging families.
