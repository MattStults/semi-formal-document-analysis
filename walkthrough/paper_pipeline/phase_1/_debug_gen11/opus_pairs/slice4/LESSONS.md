# LESSONS — slice 4, candidate `REVIEW_LIST.md` entries

⛔ **`REVIEW_LIST.md` was NOT edited.** Five slices ran in parallel; the fold is a
single coordinated step afterwards.

Each entry below is **a question a later reader can apply mechanically**, not a
description. Every one carries: MEASURED vs INFERRED · which clause taught it ·
whether it duplicates an existing entry (named) · and ⭐ whether it is
MECHANICALLY CHECKABLE — because every high-value class this campaign has found
was checkable in a few lines of Python that nobody had written.

⚠️ `REVIEW_LIST.md` stands at 20 entries against a soft cap of 20. **Most of what
follows should NOT become a 21st entry.** L1 and L3 are checks, not list rows;
L5–L7 belong to the prompt and to `PROMPT_FINDINGS.md`. My recommendation per
entry is stated. A list that grows without bound stops being read, and that is
the measured drift risk the cap exists for.

---

## ⭐ L1 — Does this module's `licence` survive its own body?

**Ask:** for every `asserts` and `ontology` entry marked `licence: "textual"`,
does its body reference a name this module declares `assumed` or `world`? If so,
the conclusion is not textual — `00_task.md` says so in bold: *"A conclusion
inherits the weakest licence in its derivation."*

* **MEASURED.** Taught by `l1001_1107_n004` (twice) and `l2821_3040_n010`. Fires
  on **2 of the 3 translated modules in this slice**, and independently
  recomputes the previous cohort's recorded figure — 12 of 17 modules there.
* **Duplicates nothing in `REVIEW_LIST.md`.** No existing entry mentions licence
  at all. Nearest neighbours are P6 (which is about *scope*, not licence) and
  P9 (declaration hygiene).
* ⭐ **MECHANICALLY CHECKABLE — `sweep.py:C_LICINH`, about fifteen lines.** It was
  written for this run and the class had already been named, measured and left
  unrepaired across a whole previous cohort with no checker in existence.
* ⛔ **DO NOT ADD THIS TO THE REVIEW LIST YET.** The prompt teaches the opposite
  (`PROMPT_FINDINGS.md` PF-4: `00_task.md`'s lattice vs its own *"a rule is not a
  fact"*, with every shipped worked module stamping `textual` on bodied rules).
  An entry that fires on work the demonstration mandates is exactly the shape
  that took a seat to 48/86 on known-good modules and forced the P9 correction.
  **Fix the prompt, then add the entry — or add it as an anti-rule saying the
  opposite.** Either way, run the checker on the corpus first: it is free.

## ⭐ L2 — Does EVERY assert body depend on a borrowed `NEEDS` predicate?

**Ask:** intersect each assert's body functors with the node's `NEEDS` names. If
*every* assert is gated on a borrowed name, the module fires on **no situation at
all** until another node's module is linked in. Then ask the deciding question:
**is that gate stated in the span, or is it an unforced narrowing?**

* **MEASURED.** Taught by `l3954_4251_n030`, whose three asserts all carry
  `markdown_latex_formatting_rule(E)`. Swept back over the previous 17-clause
  cohort, where it fires on two more modules — so not one clause's quirk.
* ⭐ **Why this is worth a row even though the `l3954_4251_n030` verdict was
  CLEAN:** it is the **same shape as the measured E6 harm** (*"add a body
  condition referencing `lower_level_content` to both asserts"* → both
  prohibitions stopped firing in any situation not affirmatively supplying an
  authority fact) — **reached with no repair step at all.** The entire E6 record
  frames that defect as something a critic introduces. It can be present in the
  first draft, and nothing on the list looks for it.
* **Partly duplicates P5's ⚠️ counter-intuitive half** (*"a body added to encode
  'regardless of context' WEAKENS the rule"*). Per the fold rule *merge on the
  QUESTION*: this is a **different question** — P5 asks whether a body is wider
  or narrower than a qualifier; this asks whether the module is inert without a
  provider. **Recommend merging as an addendum under P5** rather than a new row,
  keeping both clause provenances.
* ⭐ **MECHANICALLY CHECKABLE — `sweep.py:C_BORROWED_GATE`, about ten lines.**

## L3 — Is the coined name in the body a re-lexicalisation of the head?

**Ask:** for every rule, compare the `concepts` gloss of the head with the gloss
of each body conjunct. If two glosses say the same thing in different words, the
rule derives a conclusion from a synonym of itself, and the "extra" conjunct is a
gate no situation supplies.

* **MEASURED, and it is the ONE conclusion-changing finding of the slice.**
  `l2821_3040_n010` bodied `outdated_information_cause(I)` on
  `outdated_information(I)` — glossed *"what the model knows bearing on I is no
  longer current"* against *"the information the model actually has bearing on I
  has been overtaken by events"*. The module's only promised output was
  effectively underivable, and it validated clean with zero breaches.
* **Extends P8 without duplicating it.** P8 asks *"does a gloss restate the
  PREDICATE NAME?"*; this asks *"do two glosses in one rule restate EACH
  OTHER?"* — the same failure one step out, and P8's form misses it entirely
  because neither gloss restates its own name. **Recommend folding into P8** as
  a second sentence, per *merge on the question*.
* ⭐ **MECHANICALLY CHECKABLE, and NOT YET WRITTEN.** Gloss-pair similarity within
  a single rule is a few lines of token overlap. My `C_TAUTOLOGICAL_GLOSS` does
  not do this — it only compares a gloss to its own name. **This is the highest-value
  unwritten check I am handing over.** It found the only defect in the slice that
  changed what a module concludes, and it found it by a human reading a colon.

## ⭐ L4 — The assert ledger must count MORE than `asserts`

**Ask, of every repair:** the before/after count of `asserts` **and** `ontology`,
`claims`, `concepts`, `inputs`, `acts`, `requires`. Any list that falls needs the
written justification, naming what leaves and why the span does not require it.

* **MEASURED on `l2821_3040_n010`.** Its critic's fix is `asserts` **0 → 0** —
  a perfectly clean ledger under the `asserts`-only rule — while `concepts` fell
  6 → 5 and `inputs` 3 → 2. On a **definitional** module the whole content lives
  in `ontology`/`concepts`, and an `asserts`-only ledger is structurally blind to
  it. This slice has two modules with zero asserts by design.
* **Duplicates nothing.** It is a correction to the gap-3 *instrument*, not a
  translation lesson — it belongs in the brief and in `PROCEDURE.md`, not in
  `REVIEW_LIST.md`.
* ⭐ **MECHANICALLY CHECKABLE** and trivial: diff the length of every list field
  across two versions of the module JSON. The measured harm this instrument
  exists to catch — *two of three obligations deleted while the read-back still
  recited all three* — would have been caught by the `asserts` count. The
  `l2821_3040_n010` shape would not.

## L5 — Does the narrowing leave anything but a label?

**Ask, before drafting:** if `[node narrows this span to: "…"]` is present, does
the narrowed string contain a **matrix finite verb**? A narrowing that resolves
to `**Example**: <gerund phrase>` contains no proposition, and any content the
module encodes must then be coming from `ESTABLISHES` or from printed text
outside the narrowing.

* **MEASURED on `l831_1000_n014`** — narrowed to eleven words with zero matrix
  finite verbs, while three normative propositions were demanded by
  `ESTABLISHES` and printed in the block below.
* ⭐ **AND IT GENERALISES, WHICH IS THE POINT.** Its critic checked three sibling
  nodes and found the same shape. Extended over the whole node corpus (command in
  `SWEEP.md` §4): **roughly one node in eleven is narrowed to a bare
  `**Example**:` caption**, and nodes carrying such a caption anywhere are roughly
  a quarter of the corpus. Under the standing narrowing ruling every one of those
  must abstain, and **the document's worked examples enter the corpus through no
  module at all.**
* **Sharpens N9 and P6 rather than duplicating them.** N9 counts finite verbs
  against `ESTABLISHES` propositions; this asks specifically whether the count is
  **zero**, which is the degenerate case N9's remedy ("resolve the conflict")
  cannot resolve — there is nothing to resolve toward.
* ⛔ **This is NOT a translator lesson.** It is a defect in the graph's
  **narrowing** step and no review-list entry can fix it. **Recommend: escalate,
  do not fold.** Filed in `PROMPT_FINDINGS.md`.
* ⭐ **MECHANICALLY CHECKABLE — four lines of regex over `node_corpus_all.json`**,
  and nobody had written them.

## L6 — Is the frame answer PRESENT, in words?

**Ask of every transcript:** does the string "abstain" appear, with a reason, in
an explicit answer to *"should this clause have been translated at all?"* — and
is each of `00_task.md`'s four triggers named?

* **MEASURED, in both directions.** The gap: one previous clause headed
  `Example:` was translated with **zero occurrences of "abstain" in its entire
  transcript**. The repair: making the question mandatory produced explicit
  answers on 5 of 5 here, **two of them abstentions**, and the two critics who
  translated an `**Example**:` node both wrote down that the trigger fires and
  said what overrides it.
* ⭐ **The strongest evidence is what the forcing SURFACED, not the abstention
  rate:** three independent critics, on three different clauses, each traced the
  translate-anyway answer to the same prompt contradiction and cited the same two
  files with the same line numbers. That contradiction is invisible unless the
  question is asked out loud.
* **Duplicates nothing** — the review list has no frame entry at all; every one
  of its twenty entries presupposes that translation is the right move.
* ⭐ **MECHANICALLY CHECKABLE, in the cheapest possible way**: grep the transcript
  for "abstain", and match the span against the trigger patterns
  (`sweep.py:C_ABSTAIN_FRAME`). Over the previous 17-clause cohort that check
  finds triggers textually present in three spans, **every one `translated`**.
* **Recommend: not a `REVIEW_LIST` row — a mandatory PRE-STEP in `PROCEDURE.md`**,
  before the turns. A frame question inside a list of craft checks will be worked
  as a craft check.

## L7 — When a fix is declined because the PROMPT licenses it, is it FILED as a prompt finding?

**Ask of every declined fix:** did the reason contain "the worked example does
this" or "line NN requires it"? Then it is a PROMPT FINDING and must not be
recorded as a clean module.

* **MEASURED, and the yield was large.** All five critics were required to
  separate these, and they returned prompt findings on 5 of 5 clauses —
  including on both abstentions and on the module with no findings at all. Under
  the previous arm these would have been banked as "clean".
* **Duplicates nothing** in `REVIEW_LIST.md`; it is a reporting rule.
* **Recommend: into `PROCEDURE.md` and the critic brief**, not the review list.
* Not mechanically checkable in itself — but the *disagreements it surfaces* are
  (L1, L5).

---

## ⛔ The E6 trap — did it fire, and what happened

The standing warning: entry **E6** (*"is every entry in `claims` actually
encoded"*, the P3 family) has produced the identical harmful weakening under two
different critics on `l171_426_n022`, via the fix *"either add a body condition …
or delete C3."*

**Recorded plainly: the P3 family fired on this slice, and produced no harm.**

| clause | did P3/E6 fire? | what happened |
|---|---|---|
| `l1001_1107_n004` | no | drafter and critic each stated the branch they did **not** take, unprompted. Critic: *"because P3 does not fire, I propose no added body condition and no deleted claim, and there is no disjunction for me to be tempted by."* |
| `l2821_3040_n010` | **yes, on its face** — `asserts` is empty, so every claim is "encoded nowhere" | drafter took **neither** harmful branch: no claim deleted, no gate added; C1–C4 are encoded in `ontology` and C5 records the absence of a norm deliberately. |
| `l3954_4251_n030` | no — claims map 1:1 | recorded explicitly that the trap therefore never arises. |
| both abstentions | vacuous | an empty abstention cannot masquerade as an enforced module. |

⭐ **What I think prevented it, offered as a hypothesis and not as a result:** the
critic brief forbade offering the drafter a disjunction and required committing
to one branch with a reason. **Zero "either … or" fixes were issued across five
critics.** The measured harmful arm ran at 11 of 39 FIX lines containing that
shape. n = 5 clauses cannot distinguish the ban working from the clauses being
easier, and I am not claiming it does.

⭐⭐ **And the direction reversed once, which is the more interesting datum.** The
single conclusion-changing fix of the slice REMOVES a body condition. Its critic
applied the trap question in the removal direction — *"is there a real situation
the current body is true of?"* — answered **no**, and said so: *"This edit removes
a body condition; it is the opposite direction from the measured harm."* **The
trap question is symmetric and the E6 record only ever states it one way.** That
is a candidate amendment to the E6 entry itself, and it is the one change to the
list I would push for.

---

## What I did NOT learn

* **Nothing about whether the pair beats a single pass.** There is no
  single-pass arm here and I did not construct one.
* **Nothing about model tier.** Every drafter and critic was the same tier.
* **Nothing about the abstention rate as a quality signal.** Two of five
  abstained; both rest on an **unratified** `PROVISIONAL.md` ruling, and if the
  owner rules the other way at least one becomes a two-assert module. The rate
  measures the ruling, not the translator.

---

## ⭐⭐ L8 — Does P3 fire on a module that correctly has NO asserts?

**Added after the turn-2 critic on `l2821_3040_n010`. This is the highest-value
list finding of the slice, because it is a defect in the list itself.**

**Ask of P3 before applying it:** does this module take the ontology route — zero
`asserts` by design, with its content in `ontology`? If so, **P3 as written fires
on every one of them**, because it says *"check every entry in `claims` against
the asserts"* and there are no asserts. Its literal remedy is then to **invent a
deontic entry the span does not support.**

* **MEASURED**, on `l2821_3040_n010`, by a reader that was fenced from the
  drafter's reasoning and from turn 1's. Two of this slice's five modules have
  zero asserts by design; a third (`l1001_1107_n004`) does not, so this is not an
  artefact of one clause.
* ⛔ **This is the P9 failure, exactly, on a second entry.** P9's correction
  records that its original form *"fires on every CORRECT node module"* and that
  this is *"how seat 4c reached 48/86 on known-good modules"*. **P3 has the same
  shape and has not been corrected.** An entry that fires on correct work does
  not merely waste attention — it pressures the translator toward the invented
  obligation, which is the worst failure the task has.
* ⭐ **And it compounds the known E6 trap.** E6/P3 is already on record as a
  measured defect generator whose harmful branch is *"add a body condition … or
  delete the claim"*. On a zero-assert module the entry fires **unconditionally**,
  so the trap is armed on every ontology-route clause in the corpus rather than
  on the occasional clause with a real claims/asserts gap.
* **Recommended repair, committed to one branch:** narrow P3 to *"check every
  entry in `claims` against the asserts **and the ontology**"*. The critic
  proposed exactly this wording independently. Same repair shape as P9's, same
  grounds, and it costs the list nothing.
* ⭐ **MECHANICALLY CHECKABLE, and the check already exists:**
  `sweep.py:C_CLAIMS_UNENCODED` searches `asserts` **and** `ontology` — it does
  not fire on this module, and it did not fire on the two abstentions. So the
  checker is already correct and it is the prose entry that is wrong. That
  divergence is itself the evidence.

⛔ **Do not fold L8 as a new row.** It is a **correction to an existing entry**,
and per the fold rules a correction is recorded on the entry it corrects, the way
P9's was — with the ⛔ marker, the reason, and the clause that taught it.

## L9 — process: is a slow agent dead, or slow?

**Ask before reporting a result missing:** did I stop on the completion signal,
or on my own poll loop giving up?

* **MEASURED on this slice, against me.** I closed the run reporting
  `l2821_3040_n010`'s turn-2 critic as never returned and its clause as owed a
  second reader. It returned ~1.6 hours after dispatch, under heavy subagent-pool
  contention from four sibling slices, with a clean independent deletion audit.
  Had that report been folded as written, the record would have carried a
  false gap and the strongest corroboration in the slice would have been lost.
* **Not a translation lesson** — it belongs in `PROCEDURE.md` alongside the
  checkpoint mechanics. Under parallel slices, wall-clock variance is large
  enough that "did not return within my patience" and "did not return" are
  different claims and must be written differently.
* ⭐ **MECHANICALLY CHECKABLE, trivially:** before closing, assert that every
  dispatched agent has either a completion notification or a written artifact,
  and name any that has neither. A dispatch ledger is the same four lines as the
  critic ledger.
