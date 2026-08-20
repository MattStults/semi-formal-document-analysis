# Terminality proofs — class-A nodes

Scope: the six nodes classified **A** ("measured-terminal") in
`convergence/bucket0_reclassification.json`. One section per node.

## Formal setting (fixed for every proof below)

Engagement is `E(n,b) = f(V(n), D(b))`, where

- `V(n) = (Acts, Governs, Protects, Contexts, Actors, Purposes)` is the annotation
  vector of node `n` over finite vocabularies,
- `D(b)` is the behaviour descriptor for behaviour `b` over the same vocabularies,
- `f` is a fixed set-intersection rule (plus the wall/bridge derivations), identical
  for all nodes.

A **configuration** is a choice of the vocabularies, of `D(b)`, and of the wall/bridge
derivations. A configuration **separates** `n` from a set `T` iff it flips `E(n,b)` to
the panel-required verdict while leaving `E(t,b)` correct for every `t ∈ T`.

**Class-A theorem schema.** For a target node `n` with required verdict `v(n)`:

- **(P1)** `E(n,b)` under the current configuration opposes `v(n)`, and the same
  configuration produces the *correct* verdict for a named set `T` of nodes whose
  verdict is the opposite of `v(n)` — i.e. `n` and `T` are decided by the same
  features in the same direction, so any local move on those features moves both.
- **(P2)** Every admissible configuration measured to separate `n` from `T` was
  measured, and each is recorded with its cost.
- **(P3)** The separations not covered by (P2) require vocabulary extensions that the
  campaign record classifies as recall-negative or memorization-grade.
- **(C)** `n` is terminal **relative to the measured configuration space**.

**Relativity clause (applies to every conclusion below, without exception).** "Terminal"
is *not* "unsolvable". `CONVERGENCE_CAMPAIGN.md` §"ON THE NATURE OF THE TERMINAL SET"
explicitly **retracts** the earlier "no gradient" claim: the measure-refine loop *is*
empirical gradient ascent, several steps of it succeeded (subtype splits, wall
derivations, bridge retargets), and "the terminal set is where the climbable gradient,
**as measured so far**, is exhausted — future ideas re-open it, and the census + 9f
receipts define exactly what a successful idea must achieve." These proofs therefore
state a *lower bound on what a successful climb must achieve*, not an impossibility.

**Standing census fact (bears on P1 for all six).** In
`convergence/satisfiability_census.json` all six class-A nodes are recorded
`"status": "SEPARABLE"` with `"colliding_correct_nodes": []`. So **none** of the six is
terminal in sense (i) of the campaign doc (provably UNSAT / vector-identical to a
correct opposite-verdict node). All six can only be terminal in sense (ii): *separable
only by configurations measured to be recall-negative or memorization-grade.*
Consequently, wherever a reclassification note says "same signature", that phrase must
be read as **same decision-relevant features under the current `D(b)`**, not as
vector identity — the census refutes vector identity for these six. Each P1 below is
stated in the weaker, census-consistent form.

---

## 1. `avoiding-over-and-under-caution::l2821_3040_n025`

Required verdict (census): `not_relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"accuracy-coupled with the l2821 trio (n003/n016/n030): same
signature, opposite verdicts, one section — the irreducible core, WITH ablation receipt
(fix costs 5 TPs for 2 FPs; 2 of the 5 rerouted to C after breadth review, leaving
3-for-2 still net-negative)."*

**(P1)** The instrument engages `n025` for `caution` (a bucket-0 FP: campaign doc lists
"hash-honesty (l2821_3040_n025/n023)" in the terminal-11), while the required verdict is
`not_relevant`. The same accuracy-side features of `D(caution)` produce the **correct**
`relevant` verdict for
`T = {l2821_3040_n003, l2821_3040_n016, l2821_3040_n030}` —
the "l2821 trio", same section, opposite verdicts. *Cited evidence:* the ablation
receipt in the reclassification note for this node.

**(P2)** The one admissible separating configuration that was measured:

- **Remove `accuracy_calibration` from `D(caution)`** — fixes `{l2821_3040_n025,
  l3147_3238_n010}` (2 FPs), loses `{l2126_2404_n017, l3147_3238_n003,
  l2821_3040_n003, l2821_3040_n016, l2821_3040_n030}` (5 TPs). Receipt: the ablation
  receipt quoted in the reclassification note.
- **Breadth correction to that receipt** (`_breadth_review`, 2026-08-19): 2 of the 5
  losses — `l2126_2404_n017` (asserts |1,|2 under-labelled: `governs += tone_manner`
  defensible) and `l3147_3238_n003` (|0 arguably `substance_usefulness`) — were found
  **under-labelled** and rerouted to class-C panels (queued in `class_C_panel_queue`).
  Net measured trade after correction: **3 TPs lost for 2 FPs fixed — still
  net-negative.**

**(P3)** Separations other than the ablation would require a finer cut inside the
accuracy vocabulary that keeps the trio engaged while dropping `n025`.
`CONVERGENCE_CAMPAIGN.md` records that class of move as measured-negative three
independent ways: **global purpose filter**, **subtype granularity**, and
**quality-scoped purpose conjunction** ("measured and rejected (fixes 3, costs 24
TPs)"), "completing a three-measurement pattern … in which every finer distinction
trades recall ~1:1"; and specifically "three refinements of the accuracy/register
clusters each traded recall ~1:1". The separating feature is characterised as
"expressible in free-text purpose/failure_mode nuance but lies BELOW the finest
vocabulary granularity that remains recall-stable".

**(C)** `l2821_3040_n025` is **terminal relative to the measured configuration space**.
A successful climb must exhibit a configuration that flips `n025` to `not_relevant`
while keeping all of `l2821_3040_n003/n016/n030` engaged — i.e. beat the recorded
3-for-2 trade — without a memorization-grade extension. (Relativity clause applies.)

*Note (not a gap, a caveat):* two of the receipt's five losses are now **contested**
labels pending class-C panels; if those panels rule the broader labels correct, the
receipt's arithmetic is unchanged (it already assumes them rerouted), but the coupled
set `T` would grow back to 5 and the trade would worsen, strengthening (C).

---

## 2. `avoiding-over-and-under-caution::l3041_3146_n007`

Required verdict (census): `not_relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"clause takes no deontic position on the refusal/compliance
axis; no local feature separates example-lists from operative permissions without recall
cost."*

**(P1)** The instrument engages `n007` for `caution` (campaign doc terminal-11:
"long-term-goals (l3041_3146_n007)"), required verdict `not_relevant`.
**PREMISE GAP: no named set `T` of correctly-handled opposite-verdict nodes is
recorded for this node.** The reclassification note asserts a *type* of collision
("example-lists vs operative permissions") but names no member node and cites no
ledger/receipt. Missing measurement: the enumeration of the correctly-engaged
operative-permission nodes that share `n007`'s decision path — i.e. the coupled-node
list that the `_breadth_review` contract requires before an A-classification.

**(P2)** **PREMISE GAP: no configuration is named and no cost is recorded for this
node.** The note's clause "without recall cost" is an assertion, not a receipt: no
ablation, no fix/loss sets, no TP/FP counts. Missing measurement: at minimum one
named candidate move (e.g. an `example_list` vs `operative_permission` context or
deontic-force feature added to `V`, or an exclusion in `D(caution)`) swept and measured
on all truth per the 9d "measured on all truth before adoption" discipline.

**(P3)** The general form of the required move — introducing a deontic-force/illocutionary
distinction that the current vocabularies do not carry — falls inside the class the
campaign measured three ways (global purpose filter, subtype granularity, scoped
conjunction; "every finer distinction trades recall ~1:1"), and matches the campaign's
characterisation of the residue as separable only "in free-text purpose/failure_mode
nuance … BELOW the finest vocabulary granularity that remains recall-stable". This
supports P3 **generically**; it does not supply the node-specific receipt missing in P2.

**(C)** Terminality of `l3041_3146_n007` is **asserted but not proved**: with P1 and P2
in gap, the strongest defensible conclusion is that `n007` is *unresolved bucket-0 with a
plausible mechanism*, not measured-terminal. Under the reclassification file's own
`_breadth_review` contract ("an A-classification requires a breadth review of the
coupled nodes' labels first — under-labeled nodes are C, not A"), this node's
class-A status is **not yet earned**. (Relativity clause applies a fortiori.)

---

## 3. `avoiding-over-and-under-caution::l3147_3238_n001`

Required verdict (census): `not_relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"accuracy/utility quality on caution's declared accuracy —
same-signature cluster."*

**(P1)** The instrument engages `n001` for `caution` via `D(caution)`'s declared
accuracy/quality features; required verdict `not_relevant`. The same features correctly
engage the accuracy cluster in this behaviour. **PARTIAL PREMISE GAP: the set `T` is
named only as "the same-signature cluster" and is not enumerated for this node.** The one
enumerated accuracy-side coupling in the record — the `accuracy_calibration` ablation
receipt — lists its fix set as `{l2821_3040_n025, l3147_3238_n010}` and **does not
include `l3147_3238_n001`**, so that receipt cannot be transferred to this node without a
new measurement. Missing measurement: the coupled-node enumeration + breadth review for
`l3147_3238_n001` specifically (which correctly-`relevant` accuracy nodes are decided by
`n001`'s exact feature path).

**(P2)** **PREMISE GAP: no configuration separating `n001` from its cluster was named
and costed.** The `accuracy_calibration` ablation is the nearest recorded measurement but
is a receipt for a *different* fix set; whether it also fixes `n001` is unrecorded.
Missing measurement: re-run of the `accuracy_calibration` ablation (and of any
narrower accuracy-quality carve-out) with `n001` in the reported fix/loss ledger.

**(P3)** Supported generically, as in §1: the campaign records "three refinements of the
accuracy/register clusters each traded recall ~1:1", and the quality-scoped purpose
conjunction — the most targeted accuracy-quality move attempted — was "measured and
rejected (fixes 3, costs 24 TPs)". `n001` is an accuracy-quality node, so this is the
directly governing measured-negative family.

**(C)** `l3147_3238_n001` is terminal **relative to the measured configuration space**
*only on the strength of the cluster-level P3 evidence*; the node-level P1/P2 receipts
are missing. A successful climb must produce an accuracy-quality cut that drops `n001`
while beating the recorded ~1:1 cluster trade and the 3-fix/24-TP-loss scoped-conjunction
result. (Relativity clause applies.)

---

## 4. `helpfulness::l2821_3040_n015`

Required verdict (census): `not_relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"the uncertainty-genus permission: genus-governs-species is
load-bearing; measured cluster."*
Campaign doc terminal-11 entry: *"uncertainty-expression genus permission
(l2821_3040_n015 x help)"*.

**(P1)** The instrument engages `n015` for `helpfulness` because the node's `governs`
label is a **genus** whose species are governed by `D(helpfulness)`; required verdict
`not_relevant`. The note states that genus-governs-species is **load-bearing** — i.e.
the same genus→species inheritance rule correctly engages other nodes, so removing the
rule to fix `n015` would break them. **PARTIAL PREMISE GAP: the set `T` of nodes that the
genus→species rule correctly engages is not enumerated** ("measured cluster" names no
members and cites no ledger line). Missing measurement: the enumeration of the
genus-inheritance-dependent TP set for `helpfulness`.

**(P2)** **PREMISE GAP: no named configuration with a recorded cost.** The obvious
admissible moves — (a) disable genus→species inheritance in `f` for `helpfulness`,
(b) split the uncertainty genus into species subtypes so the permission's species falls
outside `D(helpfulness)` — are both unmeasured for this node in the cited record. The
word "measured" in the note is unaccompanied by fix/loss sets or counts. Missing
measurement: ablation of genus inheritance, and/or an uncertainty-genus subtype split,
each swept on all truth with its TP/FP ledger.

**(P3)** The subtype-split route (b) is squarely inside a family the campaign measured
and rejected: **"subtype granularity"** is one of the three named refinements in the
"three-measurement pattern … in which every finer distinction trades recall ~1:1", and
the campaign doc's own summary of that family is that "each finer cut that would separate
the residue costs more true engagements than it saves, measured three independent ways".
The inheritance-ablation route (a) has no such record. So P3 covers (b) and
**not** (a): **PREMISE GAP: the cost of disabling genus→species inheritance is
unrecorded.**

**(C)** `l2821_3040_n015` is terminal **relative to the measured configuration space**
under the subtype-granularity branch only; the inheritance-ablation branch is open. A
successful climb must either beat the measured subtype-granularity economics
or show that genus→species inheritance can be narrowed with a net-positive
all-truth delta. (Relativity clause applies.)

---

## 5. `helpfulness::l797_830_n005`

Required verdict (census): `not_relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"transparency/accuracy on helpfulness's declared accuracy —
same-signature cluster."*
Campaign doc terminal-11 entry: *"omission-transparency (l797_830_n005)"*.

**(P1)** The instrument engages `n005` for `helpfulness` through `D(helpfulness)`'s
declared accuracy features, which are the same features that correctly engage the
helpfulness accuracy/transparency cluster; required verdict `not_relevant`.
**PARTIAL PREMISE GAP: `T` is named only as "same-signature cluster" and is not
enumerated.** Unlike §1 there is no ablation receipt naming this node's coupled TPs.
Missing measurement: the coupled-node enumeration and label-breadth review for
`l797_830_n005` — required by the file's own `_breadth_review` contract note before an
A-classification.

**(P2)** **PREMISE GAP: no separating configuration is named or costed for this node.**
The recorded accuracy-side ablation (`remove accuracy_calibration from D(caution)`) is
for a **different behaviour** (`caution`) and cannot be cited for `helpfulness`. Missing
measurement: the analogous `D(helpfulness)` accuracy/transparency ablation — or an
omission-vs-commission transparency feature — swept with its fix/loss sets.

**(P3)** Supported generically and by direct family match: the campaign's terminal-class
diagnosis is that the separating feature ("what makes an *omission* transparency norm
bear differently from a stated-accuracy norm") is "expressible in free-text
purpose/failure_mode nuance but lies BELOW the finest vocabulary granularity that
remains recall-stable", and the three measured refinements — global purpose filter,
subtype granularity, quality-scoped purpose conjunction (fixes 3, costs 24 TPs) —
each traded recall ~1:1.

**(C)** `l797_830_n005` is terminal **relative to the measured configuration space** on
cluster-level P3 evidence only; node-level P1/P2 receipts are missing, and under the
`_breadth_review` contract ("under-labeled nodes are C, not A") the A-classification is
provisional pending that review. A successful climb must produce a transparency/omission
distinction in `V` that separates `n005` from the helpfulness accuracy cluster at a
net-positive all-truth delta. (Relativity clause applies.)

---

## 6. `helpfulness::l461_608_n001`

Required verdict (census): `relevant`. Census status: `SEPARABLE`,
`colliding_correct_nodes: []`.
Reclassification note: *"fix exists (does+=act_in_world) but was MEASURED net-negative
(5 indefensible FPs per 1 fix) — terminal by recorded trade."*

Note the polarity: this is the one class-A node whose required verdict is **`relevant`**,
so it is an **FN**, and the separating move is an *addition* to `V(n)` rather than a
subtraction from `D(b)`. `T` is accordingly a set of nodes that must stay
**not-engaged**, and the cost is measured in **new FPs**, not lost TPs.

**(P1)** The instrument fails to engage `n001` for `helpfulness`; required verdict
`relevant`. The single recorded fix (`does += act_in_world`) engages it, but the same
act vocabulary term, applied consistently, also engages a set of nodes whose correct
verdict is `not_relevant` — recorded as **5 indefensible FPs**. "Indefensible" is the
strict-judge category: these are not bucket-2 reading-differences but instrument-wrong
engagements. **PARTIAL PREMISE GAP: the 5 FP node ids are not enumerated in the cited
record.** Missing measurement: the ledger line listing the five nodes by id (the receipt
records the count, not the membership).

**(P2)** The one admissible separating configuration was measured:

- **`does += act_in_world` on `l461_608_n001`** — fixes `{l461_608_n001}` (1 FN),
  costs **5 indefensible FPs**. Recorded verdict: **MEASURED net-negative**.
  Receipt: the class-A note itself ("terminal by recorded trade").

This is the strongest node-level receipt of the six: a named configuration, a recorded
direction, and a recorded cost, with an explicit adoption decision against it.
Residual gap as in P1 (membership of the 5, needed to check whether any are themselves
under-labelled and hence class-C rather than genuine FPs — the same correction that
turned §1's 5-for-2 into 3-for-2).

**(P3)** Any remaining separation must engage `n001` *without* the blunt `act_in_world`
term — i.e. a narrower act subtype that covers `n001`'s act but excludes the five.
That is exactly the **subtype granularity** family, measured and rejected in the
campaign's three-measurement pattern ("every finer distinction trades recall ~1:1").
Alternatively
a node-specific carve-out would be **memorization-grade** and is excluded by the
campaign's own admissibility standard.

**(C)** `l461_608_n001` is **terminal relative to the measured configuration space**,
on the strongest node-level receipt in this set. A successful climb must engage `n001`
at a cost strictly better than 5-indefensible-FPs-per-1-fix, without a memorization-grade
carve-out. (Relativity clause applies.)

---

## Summary table

| # | Node id | Required verdict | Census | P1 | P2 | P3 | Node-level receipt? |
|---|---|---|---|---|---|---|---|
| 1 | `avoiding-over-and-under-caution::l2821_3040_n025` | not_relevant | SEPARABLE | ✔ (`T` = l2821 trio n003/n016/n030) | ✔ (accuracy_calibration ablation, 3-for-2 net-negative) | ✔ | **yes** |
| 2 | `avoiding-over-and-under-caution::l3041_3146_n007` | not_relevant | SEPARABLE | **GAP** | **GAP** | generic only | no |
| 3 | `avoiding-over-and-under-caution::l3147_3238_n001` | not_relevant | SEPARABLE | **PARTIAL GAP** | **GAP** | ✔ (cluster) | no |
| 4 | `helpfulness::l2821_3040_n015` | not_relevant | SEPARABLE | **PARTIAL GAP** | **GAP** | ✔ subtype branch / **GAP** inheritance branch | no |
| 5 | `helpfulness::l797_830_n005` | not_relevant | SEPARABLE | **PARTIAL GAP** | **GAP** | ✔ (cluster) | no |
| 6 | `helpfulness::l461_608_n001` | relevant (FN) | SEPARABLE | **PARTIAL GAP** (5 FPs uncounted by id) | ✔ (`does += act_in_world`, 5 FPs per 1 fix) | ✔ | **yes** |

**Cross-cutting finding.** Only 2 of 6 class-A nodes (§1, §6) carry a node-level named
configuration with a recorded cost. The other four rest on cluster-level P3 evidence
plus an unenumerated `T`. The reclassification file's own contract note is the governing
standard here: *"an A-classification requires a breadth review of the coupled nodes'
labels first — under-labeled nodes are C, not A."* That review is on record for §1 only.
Sections 2–5 are therefore best read as **A-provisional**.

**Cross-cutting finding (census).** All six are `SEPARABLE` with empty
`colliding_correct_nodes`, so **no class-A node is terminal in sense (i)** (UNSAT /
vector-identical). Every class-A conclusion in this document is of sense (ii) —
*separable only by measured-recall-negative or memorization-grade configurations* — and
is therefore relative to the measured configuration space by construction, exactly as
`CONVERGENCE_CAMPAIGN.md` requires after the retraction of the "no gradient" claim.

**Sources cited in this document (the only files read):**
`convergence/bucket0_reclassification.json`, `convergence/satisfiability_census.json`,
`behavior_pilot/CONVERGENCE_CAMPAIGN.md`.
