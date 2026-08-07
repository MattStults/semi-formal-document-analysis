# Scratch — an ontology phase: what survives contact with the evidence

**Throwaway. Delete once picked and tested.**

Rewritten 2026-08-07 after three things landed that the previous draft was written without:

1. **LKIF-Core is unmaintained and does not load.** Content frozen since 2008; every `owl:imports`
   404s (`05_practice_from_ontology_projects.md` §1.2, §1.3, verified).
2. **The MIREL calibration** — ~0.27 concept-vocabulary Jaccard between *trained human annotators*
   (§4.2, n=3 pairs, computed off the raw data). Our 20% multi-definition rate is the ordinary rate.
3. **The ontology-fit test as built measures the wrong consistency** — run-to-run agreement on one
   token, while our failure modes are cross-document (`STATE.md` NEW-3).

The previous draft's proposal was: **produce the concept vocabulary first, by specialising an
existing ontology, before extraction.** ⛔ **Three parts of that sentence do not survive.** What is
left is smaller, is worth having, and is decided by one test that costs about $0.18.

---

## 1 ⛔ "Specialising an existing ontology" is not a thing anyone has done and kept doing

The previous draft's premise was *"reuse is the field's stated norm — the OBO Foundry aligns to an
upper ontology and reuses external classes; starting from nothing is the deviation."*

That is true of OBO. It is **not true of the field we are actually in**, and the evidence is now
direct rather than assumed:

| | | source |
|---|---|---|
| LKIF-Core forks with a sustained line of work (≥3 commits, >1 day) | **0 of 48** | 05 §1.1, `gh api`, verified |
| LKIF terms reused by DAOnt — the one funded, peer-reviewed, 2026 LKIF specialisation | **4 of ~283**, copied locally, **no `owl:imports` at all** | 05 §2.1, verified |
| surveyed legal-ontology repos alive | **1 of 9** (DPV) | 05 §9 |
| surveyed repos with a test suite | **0 of 9** | 05 §9 |

⇒ The one professional team doing exactly our move in 2026 did not specialise LKIF. They MIREOT'd
four class names into their own file. That is the practice, and the reason is §1.2: **you cannot
import a 404.**

⭐ **So the honest description of what is on offer is not "specialise an ontology". It is: borrow a
frozen list of ~21 class names as a type layer, and vendor it.** That is a much smaller claim, it is
what `ontology_fit.py` already does, and it should be said in those words so nobody later cites this
directory as having reused a maintained upper ontology.

⚠️ Being frozen is not purely a cost. A vocabulary that cannot change upstream cannot break our
identifiers either, and 2008 content with 167 citations is a stable thing to point at. The cost is
that no defect in it will ever be fixed, and two of the fixes people have attempted (`tourtiere`,
`wadie999`) **rewrite every class IRI**, so their `Action` and ours are different classes to a
reasoner (05 §1.2). Vendor, do not fork, do not point at anyone else's fork.

---

## 2 ⛔ It should not go before extraction

The appeal of putting it first is real: a closed vocabulary constrains the extractor, so free
coinage (#8) and flat sibling lists (#10) never happen. But the appeal does not survive the question
*"a closed vocabulary of what?"*

LKIF supplies ~21 upper classes. Our corpus has **330 distinct concepts** (`annotations.json`,
computed 2026-08-07), and the ones that carry the specification's meaning — *restricted content*,
*the transformation exception* — are coined by the document and will never be LKIF classes. This is
the same wall Invariant 1's arm C hits, and the previous draft already recorded it for general
knowledge graphs. ⭐ It applies to upper ontologies too, and for the same reason.

So "ontology before extraction" can only mean **"the extractor must type each concept as it coins
it."** Three objections, in increasing weight:

- It **fuses two judgements** — *what is this concept* and *what kind of thing is it* — into one
  output, so neither can be checked without the other. Separating them is arm B's independent
  argument, which `03_pipeline.md` open question 2 already endorses.
- It makes placement **unrepeatable**. Ontology changes, closed-set changes and model changes then
  require re-extracting the corpus. As a separate pass it is re-runnable for ~$0.18.
- It is **arm A with extra steps**, and arm A carries the contrary published evidence: supplying a
  model its own accumulated vocabulary *increased* invention (`03_pipeline.md` Invariant 1).

⇒ **Placement is a pass over the concept table, after extraction.** Input: a gloss and its source
sentence. Output: a set of upper classes, or `NOT_IN_LKIF_<surface_form>`.

⚠️ **And the concept name is withheld from the prompt.** Not a detail — see §4. `ontology_fit.py`
currently sends `CONCEPT: {id}` and would have to change.

---

## 3 ⛔ Placement does not address problem #9, and the corpus says so before we spend anything

This is the substantive finding of the rewrite, and it contradicts the previous draft's framing that
closed placement is what replaces naming for identity purposes.

**The measurement that is already on disk.** The corpus carries a hand-rolled four-category type
(`kind ∈ {situation, act, entity, value}`) on every one of the 1,423 atoms. It is a coarse type
layer — exactly the shape of thing a placement produces. So: **how often does a coarse type layer
disagree with itself across occurrences of one name?**

| | | source |
|---|---|---|
| distinct concept names | 330 | `annotations.json`, computed 2026-08-07 |
| names carrying **more than one distinct gloss** (problem #9's population) | **46**, all spanning >1 clause | ditto |
| distinct `(name, gloss)` pairs in the corpus | 385, of which **101** belong to those 46 | ditto |
| names whose **`kind` disagrees** across occurrences | ⭐ **1 of 330** (`condescending_language`) | ditto |

⇒ **A four-way type separates 1 of the 46 known multi-gloss names.** 21 classes are finer than 4, so
this does not settle it — but it moves the burden of proof onto the placement, and it gives the
test a null model that costs nothing.

⚠️ **Caveat, stated because it cuts the other way.** `kind` was assigned per-occurrence by the same
extractor that coined the name, with an accumulator carrying prior names across the run
(`extract_section.py:394-400`). Its stability may therefore be *name-conditioned* rather than
genuine type agreement, which would make 1/330 an understatement of what an independent typing would
find. This is why the test in `STEP_placement_discrimination.md` **withholds the name**.

**Why this is structural, not a tuning problem.** Read the actual multi-gloss cases. The genuine
differences are differences of **scope** — of what falls under the concept — and an upper class is
blind to scope by construction:

| name | its glosses | what differs |
|---|---|---|
| `instruction_prioritization` | "…of multiple instructions." / "…instructions or outcomes." / "…instructions or behavioral rules." | **extension**. All three are the same kind of act. |
| `expand_permissions` | "…access or authorization available to a party or process." / "…systems or data access available to an assistant or process." | **extension**, twice over |
| `default_inaction` | "Taking no action when applicable instructions conflict…" / "…while awaiting a basis for proceeding." | **trigger condition** |

And the differences an upper class *will* see are mostly not sense differences at all — they are
grammatical alternations:

| name | its glosses | what an upper class sees |
|---|---|---|
| `high_risk_activity` | "**An activity** with elevated potential for harm…" / "**Engaging in** an activity with elevated potential for harm…" | a thing vs an act — **a split, and a wrong one** |
| `condescending_language` | "**A response uses** patronizing… language." / "**Using** patronizing… language." | ditto — and this is the 1 of 330 the `kind` layer flagged |
| `content` | "Text, untrusted text, or multimodal data…" / "**The** text, untrusted text, or multimodal data…" | nothing. Correct: it is a leading article. |

⭐ **The predicted shape is anti-correlation**: placement splits paraphrases and misses sense
splits. If that is what the run shows, the ontology phase contributes **nothing** to #9 and its
scope shrinks to §5. This is a falsifiable prediction with named instances, and it is the reason to
run the test rather than argue about it.

---

## 4 ⚠️ The MIREL band is not a threshold, and the built tool uses it as one

`ONTOLOGY_FIT.md`'s verdict table reads **usable** at Jaccard CI lower bound ≥ 0.30 and **marginal**
at ≥ 0.24, taken from `reference.human_pair_jaccard`. The doc already caveats the band as "a low
floor, not a pass mark". ⛔ **That caveat is not strong enough. The two quantities are not the same
kind of number and no boundary should be read off one for the other.**

| | MIREL 0.30 / 0.24 / 0.29 | what `ontology_fit.py` measures |
|---|---|---|
| raters | two **different** trained humans | one model **against itself** |
| answer space | **open** — free-form concept vocabulary over WordNet/YAGO | **closed** — 22 declared labels |
| unit | distinct labels used anywhere in a document | class set per concept, averaged |

An open-vocabulary between-annotator score and a closed-set within-rater score do not share a scale.
A model returning one class per item from a 22-item list would clear 0.30 by consistency alone; two
humans choosing freely from WordNet cannot. ⇒ **Drop the band from the verdict rule.** It survives
as what it actually supports: *free-form naming is not beatable, so replace it* — which is the
argument for a closed task existing at all, not a pass mark for one.

⭐ **What survives from MIREL and should be kept**: the `NOT_IN_<vocab>_<surface_form>` marker
(05 §4.1). A term the vocabulary does not cover is recorded **as unresolvable, carrying its surface
word**, so off-vocabulary coverage is a count rather than an absence. That answers the open question
*"what does it do with a term the document never defines"* — mark it, keep the word, do not mint.

---

## 5 ⭐ What the phase is actually for, stated so it can be argued with

Strip the claims that did not survive and this is what is left. It is smaller than the previous
draft and it is defensible.

```mermaid
flowchart TD
    EX[["extraction output<br/>385 distinct (name, gloss) pairs"]] --> PL

    PL{"PLACE<br/>gloss + source sentence,<br/>name WITHHELD<br/>→ set of upper classes,<br/>or NOT_IN_LKIF_&lt;surface&gt;"}

    PL --> U1["⭐ 1 · MERGE VETO<br/>stage 5 proposes collapsing two names.<br/>Incompatible placements BLOCK it."]
    PL --> U2["2 · a type in the read-back<br/>'follows_chain_of_command, a Norm'<br/>is a visible commitment"]
    PL --> U3["3 · off-vocabulary COUNT<br/>the NOT_IN_LKIF rate is<br/>a coverage number"]

    PL -.->|⛔ NOT this| X["identity / homonym detection<br/>— §3 says it cannot"]

    U1 --> ASYM["⚠️ ONE DIRECTION ONLY<br/>mismatch ⇒ not the same concept.<br/>match ⇒ NO evidence of sameness."]
```

**1 — the merge veto, and it is the only load-bearing use.** Stage 5 (normalise) proposes collapsing
two names into one concept, and its acceptance test is *re-render every affected clause and re-run
the clause↔paraphrase review* — a render and a review **per affected clause, per proposal**
(`03_pipeline.md` §5-and-6). A placement mismatch kills a proposal for free, before any of that.

⚠️ **The inference runs one way and only one way.** Different placements ⇒ different concepts, so do
not merge. Same placement ⇒ **nothing**, because 21 classes over 330 concepts means most pairs
collide. Anyone reading a match as evidence of sameness has reintroduced problem #9 through the
filter meant to guard it.

**2 — a type on the read-back.** Problem #5 is hollow stubs: `follows_chain_of_command` reads
correctly in every explanation because it echoes the document's words. Rendering *"a Norm"* or
*"an Action"* beside it is a commitment a reviewer can disagree with. ⚠️ Small, unmeasured, and it
is a nice-to-have — not a reason to build the phase.

**3 — an off-vocabulary count.** Per §4.

⛔ **And what it is not for:** producing the concept vocabulary (§2), solving #9 (§3), or supplying
the query side. None of the three.

### The standing resolution on `norm`, unchanged and now corroborated

Take the class names, refuse the axioms. `norm` makes `Prohibition` a subclass of `Permission` and
equivalent to `Obligation` (05 §1.6, verified at `norm.ttl:285-297`) — a deontic commitment we ruled
against (`03_pipeline.md` open question 1). ⭐ DAOnt reached the same place independently: it took
`norm:Right` as a bare class with none of the axiomatisation (05 §2.1). Saying a concept *is* a
prohibition does not license inferring what follows from one.

---

## 6 What to do, in order

| | | cost | blocks what |
|---|---|---|---|
| **1** | ⭐ Run `STEP_placement_discrimination.md` — does placement separate senses at all, and does it split paraphrases? | ~$0.18 + ~30 min of human pre-registration | decides whether §5's use 1 exists |
| **2** | Drop the MIREL band from `ontology_fit.py`'s verdict rule (§4) | free | nothing; it is a correctness fix |
| **3** | Rebuild the placement pass to withhold the name and emit `NOT_IN_LKIF_<surface>` (§2, §4) | small | step 1 needs it |
| **—** | ⛔ Do **not** test minting (step 3 of the previous draft's flowchart) | | steps 1–2 must work first |

⚠️ **None of this blocks stage 1.** `03_pipeline.md` Part 6 names running stage 1 on one clause as
the highest-value next step, and it is still true: no model has produced a logic module in this form
and every downstream stage assumes one. The ontology phase feeds stage 5, which does not exist. If
there is one unit of attention, it goes to stage 1.

⇒ **The reason to run step 1 anyway is that it is cheap and it is decisive.** A negative result
deletes a phase from the design before anyone builds against it, which is the outcome this directory
exists to buy.

---

## What the previous draft got right and is retained

- **Placement into a closed set is a different kind of judgement from naming**, and the second is not
  measurable while the first is. §3 narrows *what the measurement buys*; it does not restore naming.
- **Set-valued, not single-label.** `developer` is an `Agent` **and** a `Role`; LKIF is a
  multiple-inheritance ontology (`Person ⊑ Agent`, `Person ⊑ Natural_Object`). Forcing one label
  manufactures disagreement. This correction stands and is a named check in `ontology_fit.py`'s
  self-test.
- **Jaccard, not κ.** Chance-corrected single-label statistics cannot represent a set-valued answer
  and would score `{Agent}` against `{Role}` as total disagreement.
- **A model is a proposer, never the source of a deterministic step.** DeepSeek found the concepts
  by reading and then stated a rule that could not have produced its own examples.
- **The vocabulary-only flag on `norm`** — §5.

## What was withdrawn

| claim | why |
|---|---|
| "reuse is the norm; building from scratch is the deviation" | true of OBO, false of legal ontologies — 0 of 48 forks, 4 of 283 terms (§1) |
| "LKIF-Core … live, not a paper artifact" | content frozen 2008; the Feb 2026 commit was a licence change (05 §1.3) |
| "produce the concept vocabulary first" | the vocabulary that matters is coined by the document (§2) |
| the concept phase addresses #8 and #9 | it vetoes merges in one direction; it does not detect homonyms (§3, §5) |
| "the CLOSED set of ~15" | no structural cut yields it; the set is a declared 21 + `NONE_OF_THESE`, in config |
| the MIREL band as a verdict boundary | category mismatch between the two measures (§4) |
