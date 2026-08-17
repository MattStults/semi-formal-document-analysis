# LESSONS — slice 1 candidate `REVIEW_LIST.md` entries

⛔ **`REVIEW_LIST.md` was NOT edited.** Five slices ran in parallel; the fold is one
coordinated step afterwards. These are candidates only.

Every entry below is **a question a later reader can apply mechanically**, not a description
— per the fold rules, *"Watch out for scope drift" is not an entry; "does each body widen
past the span's qualifier?" is.*

Each carries: **MEASURED vs INFERRED** · **which clause taught it** · **whether it duplicates
an existing entry, by name** · ⭐ **whether it is MECHANICALLY CHECKABLE** — every high-value
class we have found was checkable in a few lines of Python that nobody had written.

---

## L1 — Is this borrowed name ALSO a `PROVIDES` name? That decides its licence.

**Ask:** for each `concepts` entry whose name is in the node's `NEEDS` block — is that name
*also* in `PROVIDES`? If **yes**, the node owns it and a `textual` licence can be right. If
**no**, the meaning came from the contract and not from the cited text, and `textual` is a
manufactured citation unless a substring of the NARROWED span supports the gloss.

* **MEASURED.** Four modules, one borrowed name (`root_authority`), a **2–2 licence split**
  that no per-clause pass could see. Taught by the SWEEP over `l1001_1107_n001`,
  `l1001_1107_n007`, `l1001_1107_n012`, `l1108_1367_n004`; three of the four critics raised
  the field independently and none could resolve it from one module.
* **Duplicates?** No existing entry. Adjacent to **N8** (borrowed relations, argument order)
  and to **anti-rule 2** (`requires-unprovided` fires on every correct module) — this is the
  *licence* face of the same borrowed-name problem and merging it into either would lose the
  discriminator, which is the whole content.
* ⭐ **MECHANICALLY CHECKABLE — yes, and it is the highest-value one here.** `name in NEEDS
  and name not in PROVIDES and licence == "textual"` is one predicate. It fires on
  `l1001_1107_n012` and correctly clears `l1001_1107_n001`.
* ⚠️ Depends on `PROMPT_FINDINGS.md` **PF2**: the production prompt teaches `textual` by
  worked example. Do not fold this entry until the owner rules, or the list will contradict
  the prompt and translators will be charged for obeying it.

## L2 — An inert ontology head is only a defect when the node did not `PROVIDE` it.

**Ask:** is any predicate an `ontology` HEAD that appears in no `asserts` body and no other
`ontology` body? If it is a `PROVIDES` name, that is **correct and expected** — the module's
deliverable is exactly a derivable predicate for other nodes. If it is a name you coined,
it is a class the module can never use, and the content that motivated it reaches no verdict.

* **MEASURED.** The naive form fires on **4 of 5** slice-1 modules, including two where the
  inert head IS the deliverable (`root_authority` on `l1001_1107_n001`,
  `privacy_context_dependence` on `l1001_1107_n007`). With the `PROVIDES` qualifier it fires
  on exactly the two the critics reached by reading — `not_private_information`
  (`l1001_1107_n012`) and `specific_circumstance` (`l1108_1367_n009`) — and on no others.
* **Duplicates?** ⭐ **This is the correct narrowing of P9**, whose original form was already
  corrected once for firing on every correct node module. Fold it INTO P9 as a second
  sentence rather than adding a row; P9's own history is the argument.
* ⭐ **MECHANICALLY CHECKABLE — yes.** `heads - (assert_bodies ∪ ontology_bodies ∪
  forbid_body.banned)`, minus `PROVIDES`. It is implemented in `sweep.py` S4.
* ⚠️ **This is a REPORTING rule, not a repair rule.** Both critics that found their instance
  declined the repair and both were right: the available fixes were to delete the class
  (dropping the span's named circumstances) or to add a `permit` the span does not state.
  **An inert head is a finding to log, never a licence to make something fire.**

## L3 — Does the code close a class the span left open — and does your own gloss say so?

**Ask:** does the narrowed span carry `such as`, `e.g.`, `contexts like`, `including`? Then
find the class it opens. Is that predicate derivable ONLY from the members named in the span?
If yes, the program closes what the document left open. Then read your own `concepts` gloss:
if it says the class is open, **your prose and your code disagree, and the read-back renders
the prose.**

* **MEASURED, on two clauses independently.** `l1108_1367_n004` (`contexts like` →
  `qualifying_discussion_context` closed at 3) and `l1108_1367_n009` (`such as` →
  `sensitive_content` closed at 2; `e.g.` → `specific_circumstance` closed at 4). Two
  separate critics reached it separately, which is what makes it a class.
* **Duplicates?** Partially overlaps **N4** ("a qualifier in a list bounds ONE item") — but
  N4 is about *attachment* of a qualifier and this is about *closure* of an enumeration. Do
  not merge: N4's remedy is to attach correctly, this one's is that there may be no remedy.
* ⭐ **MECHANICALLY CHECKABLE — yes**, both halves: the marker is a substring test, and
  "derivable only from named members" is `head not in inputs ∪ requires` with every rule for
  it bodied.
* **Note the honest outcome:** in both cases there was no clean repair (ASP cannot encode
  "like"; the alternatives were an invented member or a tautological input). The finding is
  the recorded disagreement, and the direction matters — closing a class narrows a
  *permission* safely and narrows a *prohibition* dangerously. On `l1108_1367_n009` the
  closed class `sensitive_content` sits under a **`forbid`**, which is the dangerous side.

## L4 — Did the span carry an exception connective with no counterpart id?

**Ask:** does the narrowed span contain `However`, `unless`, `may only`, `except`, or a
`BAD[#anchor]` tag? Then it stands in a relation to another clause. Was that clause's id
supplied anywhere in your user block? If not, `beats` cannot be filled without guessing —
**say so in the notes, and do not treat the module as complete.**

* **MEASURED.** 3 of 5 slice-1 spans carry the connective; `beats` is empty in **5 of 5**,
  and no module could have done otherwise. Taught by `l1108_1367_n004` (`However` — a
  permission that exists only as a carve-out from a prohibition in the same sentence).
* **Duplicates?** No. **N7** is the closest ("the EXCEPTED branch is a hole, not a rule") but
  N7 is about not over-asserting on the excepted branch; this is about the ordering relation
  being unrecordable. Complementary, both needed.
* ⭐ **MECHANICALLY CHECKABLE — yes**, and cheaply: connective present ∧ `beats == []`.
* ⚠️ Filed also as `PROMPT_FINDINGS.md` **PF4**, because the true fix is upstream: rule 8b
  demands a field the node contract never supplies an id for. As a review-list entry its
  value is that it stops "beats: []" reading as "no relation exists".

## L5 — Does the SOURCE TEXT point at a section the `NEEDS` block never mentions?

**Ask:** grep the node's source text for `](#anchor)`. Is each anchor represented in `NEEDS`?
If not, the document states a dependency your module has no licensed way to record — and
`requires: []` will look like independence.

* **MEASURED.** `l1108_1367_n009` points at `#no_erotica_or_gore` and
  `#transformation_exception`, `NEEDS` is *(none)*, and the module correctly ships
  `requires: []`. Corpus-wide, **131 of 172 anchor occurrences** are absent from their node's
  `NEEDS` block, and `cross_references` cannot resolve any of them (every record's
  `section_id` is the constant `"graph_node"`).
* **Duplicates?** No. Related to failure mode #2, which is prompt text, not a list entry.
* ⭐ **MECHANICALLY CHECKABLE — yes**, and it is the cheapest check in this file.
* **INFERRED on the consequence, MEASURED on the count:** I measured the drop; that a
  dropped anchor changes some downstream verdict is inference, not measurement.
* ⚠️ Mostly a **PROMPT/CORPUS** finding (`PF3`). Include it in the list only as *"say it in
  your notes"*, never as something a translator can repair.

## L6 — A "may only X" states a NECESSARY condition. Did you assert the sufficient one?

**Ask:** for a span of the form *"may only be Ved under C"* — does your module contain a
`permit` whose body is C? If so you have asserted that C **suffices**, which the span does
not say. The span forbids the complement; it does not license the inside.

* **MEASURED**, as a refusal that held: `l1108_1367_n009` recorded the decision in a `META`
  claim and emitted `forbid` only, and its critic independently graded the absent `permit`
  as *"the load-bearing correct choice"* and warned it must not be "fixed" in a later turn.
* **Duplicates?** Strongly adjacent to **N7** ("the EXCEPTED branch is a hole, not a rule")
  and to `00_task.md` rule 6 ("never encode the positive from a negative statement"). ⭐ **My
  recommendation is to MERGE this into N7 as its second measured provenance** rather than
  add a row — the fold rules say merge on the question, and it is the same question with a
  different surface form (`only` instead of `unless`). Keeping both would push the list past
  its cap for no discriminating gain.
* ⭐ **MECHANICALLY CHECKABLE — partially.** `"may only" in narrowed_span and any
  assert.status == "permit"` is a cheap trigger with some false positives; the judgement of
  whether the body IS the carve-out condition is a reading.

## L7 — Is an ontology rule's body a presupposition rather than a discriminator?

**Ask:** for each `ontology` rule, is there any realistic case that satisfies the head's
subject but NOT the body? If the body holds whenever the head's arguments exist, the
predicate is true of everything and classifies nothing.

* **MEASURED, and DECLINED — the entry's value is the decline.** `l1001_1107_n007` emits
  `privacy_context_dependence(I, C) :- occurs_in_context(I, C)`, which derives for every
  (information, context) pair. Its critic found this (F6) and refused to repair it, because
  the document's claim really is universal and narrowing it would be a **P5 weakening**. I
  independently reached the same reading before seeing the report.
* **Duplicates?** Not P8 (no head appears in its own body, and no gloss restates a name). Not
  N1 (the rule is correctly bodied rather than a ground constant). It is a genuinely new
  shape — but see the warning.
* ⭐ **MECHANICALLY CHECKABLE — no**, and that is the point. "Would any case fail this body?"
  needs a reading of the world, not of the file.
* ⛔ **LOWEST-CONFIDENCE ENTRY HERE, and I recommend NOT folding it yet.** It is one clause,
  it is not checkable, and its only measured outcome was a correct decision to change
  nothing. An entry whose sole demonstrated effect is "consider it and leave it alone" is
  exactly the kind that tempts a later reader into over-editing a correct module. Bring it
  back if a second clause produces it.

---

## What the list did NOT need — reported because a null is a datum

Per the checkpoint's *rubber-stamping* test: the five drafters between them reported changes
under **P6, P8 (×3), N3, N6, N7, N10** and explicit no-change findings on the rest. That is
application, not a null — the two agents that reported the most "nothing" (`l1001_1107_n001`,
2 of 20 entries changed anything; `l1001_1107_n007`, 1 of 20) were both checked by hand by
the coordinator against their modules and their nothings are real. **No agent reported
"nothing" on every entry**, so the halt condition did not fire.

⭐ **Novelty signal for the fold:** of the 7 candidates above, **3 (L1, L2, L4) came from the
cross-clause sweep and not from any per-clause pass**, and 2 of those 3 recommend *modifying
an existing entry* (L2 into P9) or are *prompt findings first* (L4). The per-clause loop is
producing fewer genuinely new classes than the sweep is, on the same five clauses. If that
holds in the other slices it is an argument for making the sweep a standing step rather than
a one-off.
