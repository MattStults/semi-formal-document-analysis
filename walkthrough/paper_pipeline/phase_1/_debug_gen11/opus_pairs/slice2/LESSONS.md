# LESSONS — slice 2 candidate REVIEW_LIST entries

⛔ **`REVIEW_LIST.md` was NOT edited.** Five slices ran in parallel; the fold is a single
coordinated step afterwards, and concurrent edits would corrupt the file. This is the
proposal, deduped **within** the slice only.

Every entry below is **a question a later reader can apply mechanically**, per
`PROCEDURE.md`'s fold rule ("reject descriptions"). Each carries:

* **MEASURED** (seen on a real module of this slice) vs **INFERRED** (reasoned to, not seen
  to fail);
* which clause taught it;
* whether it **duplicates an existing entry**, named;
* ⭐ **MECHANICALLY CHECKABLE** — could a few lines of Python decide it from the module JSON
  plus the span text alone? *Every high-value class this project has found was checkable in
  a few lines nobody had written, so this tag is the one that predicts value.*

The slice proposes **8** entries and explicitly **withholds 11 more** as duplicates or
addenda — those are listed at the bottom, because a rejected lesson is a real datum about
whether the list is working.

⚠️ The list is already at 14 entries against a soft cap of 20. **These 8 cannot all be
added.** My own ranking, for the folder: L-1, L-2 and L-3 are the ones I would spend the
headroom on; L-4 through L-6 are amendments to existing entries and cost no slot; L-7 and
L-8 are the weakest and I would hold them.

---

## ⭐ L-1 — Does one act functor take arguments of DIFFERENT SORTS across its asserts?

**Ask:** for each act functor appearing in more than one `asserts` entry, collect the body
literals that bind the act's variable. **If two asserts bind that variable through literals
with no predicate in common, the module is using one act over incompatible sorts, and at most
one of the rules can ever fire against a given situation fact.**

MEASURED on `l1001_1107_n002`: `respect(X)` is asserted three times — `X` bound by
`creator(X)`, by `work_of(X, C)`, and by `intellectual_property_right_of(X, C)`. A person, a
work, and a legal right, as the same argument of the same act. It is *faithful* — the span
really does coordinate three objects under one verb — and it is still failure mode #3 (rules
that can never fire), because the query side supplies one sort per variable.

⭐ **MECHANICALLY CHECKABLE — yes, and it is `sweep.py` check Q, already written.**

**Duplicates:** none. No existing entry asks it; neither the drafter's four-turn review nor
its independent critic reached it. **This is the entry the cross-clause sweep produced that
nothing else in the apparatus produced**, which is the main argument for adding it.

⚠️ Not repaired on the module. The remedy is a schema-level question (does the act want an
index, `respect(X, Sort)`?) and is above a translator's pay grade. Recorded as an open UNSURE
in `out/l1001_1107_n002.notes.md`.

---

## ⭐ L-2 — Is any borrowed `NEEDS` gloss marked `textual` and cited to your own node?

**Ask:** for each `concepts` entry whose `name` is one of the span's `NEEDS` names, is
`licence == "textual"` with `cites` equal to this node's id? **If so, you have cited your own
span as the source of content it does not state — the manufactured citation `00_task.md`
calls "the single worst failure available here."** The honest form is `assumed`, `cites:
null`, with an inference naming the NEEDS block.

MEASURED on `l1001_1107_n008` and `l1001_1107_n013`; independently avoided on
`l1001_1107_n002`, `l1108_1367_n005` and `l1108_1367_n010`. **Every one of the five modules
scored `translated`, `repair_needed: False`, zero breaches, before and after repair** — the
defect and its fix are byte-indistinguishable in every deterministic instrument the pipeline
runs.

⭐ **MECHANICALLY CHECKABLE — yes, with zero false positives, and it is `sweep.py` check O.**
The NEEDS names are parseable straight out of the span; the licence and cites are fields.

**Duplicates:** none. Closest is `PROVISIONAL.md` ground 2, which reasons this way for
`ESTABLISHES` but is a ruling file, not a translator check, and says nothing about `NEEDS`.

⚠️ **This entry is a WORKAROUND, not a fix.** The prompt actively teaches the defect —
`node_worked_example.md` lines 47–49 and 230–232, against `00_task.md`'s own definition of
`textual`. See `PROMPT_FINDINGS.md` PF-B. **If PF-B is repaired, this entry should be
retired**, and the fold should record that dependency so it does not outlive its cause.

---

## ⭐ L-3 — Does a `textual` conclusion rest on an `assumed` fact?

**Ask:** for every `asserts` / `ontology` entry with a `body`, look up the licence of every
name the body references. `00_task.md`: *"A conclusion inherits the weakest licence in its
derivation."* **A `textual` head over an `assumed` body literal is mis-marked, and the whole
point of the licence field — "change one asserted fact and the answer disappears" — is lost.**

MEASURED, but ⚠️ **not on a module of this slice — on the PROMPT.** All five modules pass
(`sweep.py` check B, zero hits). `node_worked_example.md` lines 184–201, the model heading
node, marks `guideline_authority(R) :- rule_under_heading(R, …)` as `textual` while the
`rule_under_heading` concept it derives through is `assumed`. Verified by the coordinator
against the file, not taken from an agent's report. Taught by `l1108_1367_n010`, whose span
is a heading of exactly that shape and which followed the RULE rather than the EXAMPLE.

⭐ **MECHANICALLY CHECKABLE — yes, ~10 lines, and it is `sweep.py` check B.**

**Duplicates:** none — and this is the class the previous loop NAMED, called *"mechanically
checkable; nothing checks it"*, and left in 12 of 17 clauses. ⭐ **This slice upgrades that
finding: it is not merely unchecked, it is TAUGHT**, in the model answer, on the corpus's
largest node class (`authority_convention.md` puts the section-authority edge class at ~47%
of all golden-vs-ds3 edge divergence). See `PROMPT_FINDINGS.md` PF-C.

---

## L-4 — AMENDMENT TO N10: a binder relation is unanchored BY NECESSITY, and the remedy is `assumed`, not deletion

**Ask (added to N10):** if a coined name has no substring in the narrowed span, is it a
**binder** — a relation the span *uses* without *naming* (a reply to the request it answers, a
rule to the heading it sits under, information to the person it concerns)? If so, the remedy
is `assumed` with the inference named, **never deletion**: an ontology entry with an unbound
variable and no body makes the solver reject the whole file.

MEASURED on three clauses. `responds_to/2` (`l1001_1107_n013`), `rule_under_heading/2`
(`l1108_1367_n010`), `information_about/2` (`l1001_1107_n008`) — all three unanchored, all
three necessary, all three correctly disposed as `assumed`. **N10 as written supplies the
diagnosis and no remedy**, and applied literally it deletes the binder.

⭐ **MECHANICALLY CHECKABLE — the flag is (`sweep.py` check D); the binder/not-binder call is
not.** But the useful mechanical half is the pair rule: *unanchored coined name AND licence
`textual`* is the defect; *unanchored AND `assumed` with an inference* is correct.

**Duplicates: YES — this is an addendum to N10 and must be folded INTO it, not added.**
Costs no slot.

---

## L-5 — AMENDMENT TO P3: is a `claims` entry about the DOCUMENT, or about your own encoding?

**Ask:** does the claim describe what the clause says, or what the module did? A claim of the
second kind ("the span attaches no trigger, no exception and no defeater") cannot be checked
against the span by anyone, and P3's "encoded nowhere is the fingerprint" test misfires on it
in both directions.

MEASURED on `l1001_1107_n002` (2 of its 5 claims), surfaced by `sweep.py` check K and
adjudicated as a screen artifact of a real ambiguity, not as dropped content.
`30_failure_modes.md` #11 genuinely does send unencodable structural statements to `claims`,
so both kinds legitimately live in one field — which is exactly why they need distinguishing
before P3 is applied.

⭐ **MECHANICALLY CHECKABLE — partly.** The word-overlap screen (check K) finds the
candidates; the about-document/about-encoding split is a reading.

**Duplicates: YES — fold into P3 as a precondition.** Costs no slot.

---

## L-6 — AMENDMENT TO N8: the `NEEDS` block gives no ARITY, so whatever you write is invention

**Ask (added to N8):** for each borrowed name, does anything in your module or the span
constrain its **arity**? If the module never uses the predicate, nothing does — so say in the
gloss what you took the arguments to be, not only their order.

MEASURED on `l1001_1107_n008` (`privacy_context_dependence/2`) and `l1108_1367_n010`
(`authority_levels_hierarchy/2`): both invented an arity, neither used the predicate, both
were N8-compliant on ORDER. **N8 is silent about arity, and an arity mismatch is the coarser
failure** — a `/1` provider and a `/2` consumer never link at all, where an order inversion at
least links.

⭐ **MECHANICALLY CHECKABLE — yes** (`sweep.py` check P: borrowed name, arity ≥ 2, absent from
every body).

**Duplicates: YES — an addendum to N8.** Costs no slot.

---

## L-7 — Does a coordinated infinitive series under ONE modal produce one assert per conjunct?

**Ask:** count the conjuncts in a `should X, Y, and Z` series in the narrowed span; count the
distinct act functors in `asserts`. **Fewer functors than conjuncts means content was
collapsed.**

MEASURED on `l1108_1367_n005` (the de-escalation guidance: three aims, three obliges kept).
It did not fail here — it is the failure this clause is historically famous for, and the entry
exists to keep it from failing.

⭐ **MECHANICALLY CHECKABLE — yes, in the weak form.**

**Duplicates: PARTIALLY — strengthens P3 and amends N9.** P3 is a *self-consistency* check and
passes trivially on a module whose `claims` already collapsed the three aims; this is anchored
on the span's grammar. ⚠️ **N9's finite-verb count reads 2 on this span against 6
propositions**, so N9 alone does not detect the collapse. Recommended disposal: **widen N9's
counting question from finite verbs to conjuncts under a shared modal**, rather than add a
row.

---

## L-8 — In a GOOD/BAD example span, does the module encode the DELTA between the arms?

**Ask:** if the span has a `<comparison>` block, does the module contain a body literal that
one arm satisfies and the other fails? **Encoding only the GOOD arm's content passes P10 and
is still blind to what the example exists to say.**

MEASURED on `l1001_1107_n013`: the span has one GOOD arm and **two** BAD arms, and the GOOD
arm shares its most salient property — declining to share the private details — with the
`BAD[#chain_of_command]` bare refusal. A module bodied only on that shared property satisfies
P10's "do the two arms differ in status or act" and discriminates nothing.

⭐ **MECHANICALLY CHECKABLE — partly** (presence of a comparison block and of a
non-shared body literal; which property is shared is a reading).

**Duplicates: PARTIALLY — P10 covers the two-arm case and this is the ≥3-arm generalisation.**
Recommended disposal: **amend P10** to read "differ in `status`, in act, **or in a body
literal the other arm fails**", rather than add a row.

⚠️ **Conditional on PF-A.** If the owner rules that example spans are abstained on, this
entry and P10 both become dead letters. Fold in that order.

---

# WITHHELD — proposed by a drafter, not carried forward

A rejected lesson is evidence about whether the list is working (`PROCEDURE.md`,
checkpoint B). 11 were proposed across the five clauses and are not promoted:

| lesson | clause | why withheld |
|---|---|---|
| a redundant TYPE literal in a body silently narrows an unconditional obligation | n002 | Real and mechanically checkable, and the drafter's own turn-4 caught it. **Held only for cap reasons** — it is my first pick if a slot frees. Restates P5's narrowing direction with a new trigger. |
| *while / as / alongside* is concurrent, not concessive — N6 mis-fires on it | n002 | Addendum to N6, not an entry. ⚠️ **Records a THIRD N6 misfire and a NEW shape**: additive (an invented priority rule) rather than weakening. |
| an abstract ACT term is fine; an abstract ONTOLOGY predicate is the hollow stub | n002 | Sharpens `00_task.md` rule 5 / failure mode #5. Belongs in the output-contract reading, which `PROCEDURE.md` says is not a lesson. |
| verb count and proposition count may legitimately differ under a coordinated object | n002 | Addendum to N9; merged into L-7's amendment. |
| *"should be able to"* is a permission, not an obligation | n008 | Real, MEASURED, checkable. P1 does this job for `prefer` and nothing does it for the `oblige`/`permit` pair — but it is a **modal-vocabulary** lesson and the list has no such row; a single row would end up unbounded. Held. |
| an affirmatively-stated exception arm is not the hole N7 describes | n008 | Addendum to N7. ⚠️ Load-bearing: applied literally, N7 would have taken that module 1 → 0 asserts and silently restored the prohibition the span carves out of. |
| an EMPTY `ESTABLISHES`/span diff is a distinct result and must be recorded | n008 | Process lesson, not a defect check. Belongs in `PROCEDURE.md`. |
| a permission carve-out with no `forbid` should not close `cepa` | n008 | INFERRED, not measured. Held for evidence. |
| N10 must be applied INSIDE glosses, not only to coined names | n008 | ⭐ Found by the independent critic and missed by the drafter — the single clearest demonstration that the blind second pass earns its cost. Folded into L-4's scope. |
| whose VOICE is the finite verb in? | n013 | Refines N9. ⚠️ Strong: that span has ~20 finite verbs and **2** in the document's own voice. Merge as a second sentence of N9. |
| does a `concepts` entry exist for every `forbid_body` name? | n013 | INFERRED, and it is a schema-contract question, not a reading question. |

**Novelty reading for the checkpoint.** 19 lessons proposed across 5 clauses; **3 promoted as
new rows** (L-1, L-2, L-3), 5 disposed as amendments to existing entries, 11 withheld. That
is a novelty rate of **3/19 ≈ 16%**, against fold 1's 56% at the same point. ⭐ **Falling is
the signal the procedure says we want** — the list has absorbed the recurring classes, and
what remains are amendments. ⚠️ Read with the caveat that this is a different slice of the
corpus and a differently-shaped pass, so it is not a clean like-for-like against fold 1.

**And the honest counter-reading:** all three promoted entries are **licence- and
sort-related**, i.e. they live in the join between the module and the span that no
deterministic check inspects. That is not "the list has converged". It is "the list has
converged on the reading of spans, and a whole family of defects sits in a place the list
was never pointed at."
