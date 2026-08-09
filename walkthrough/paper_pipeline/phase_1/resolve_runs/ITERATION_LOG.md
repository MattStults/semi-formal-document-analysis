# Five prompts for one question — what each cost and what it bought

**The question throughout:** can a model tell us where in the document a borrowed predicate's
meaning lives, well enough that a later step can substitute the document's words for our invented
name? This is Invariant 1's **arm C** — *"a lookup the model never sees"* — the arm the design calls
*"the most attractive and the least explored"*, whose only recorded objection is *"requires the
lookup to exist."*

⭐ **The sequence is the finding.** Four of the five moves were caused by a defect in the PROMPT or
in the SCORING KEY, not by the model. Recorded so the next person does not re-derive them.

---

## 1 · Concept map, section-level — $0.0253

*"For every section, what concepts does it need from elsewhere?"* Whole document, 78 sections, two
turns on one accumulating transcript.

**Produced:** 78/78 sections, 165 distinct concepts, 108 resolved to a producing section, 36 honestly
unresolved. Statically checkable and it half-passed — every section id valid, **72 of 108 evidence
phrases verbatim** in the section named.

⛔ **Overlapped the predicates our translator actually coined by 1 of 32.** The map named
document-level nouns; modules name clause-level predicates. Both right, neither the other.

## 2 · Concept map, predicate-level — $0.0166

Pre-registered: *asking for predicates instead of concepts should raise the overlap.*
**Result: 0 of 32, with 268 candidates on the table. Falsifier fired.**

⇒ **Prediction is the wrong direction.** A map cannot guess the names a translator will coin. Its
role is a **resolution target**, not prompt context — arm C, not arm A.

## 3 · Five-solver panel, name-level — free (subagents)

*"Where is each of the 43 real predicates defined?"* Five independent Haiku solvers, ground truth =
6 predicates whose **words appear nowhere** in the document.

| solver | said `document` | calibration |
|---|---|---|
| D | 5 | **6/6** |
| A | 18 | 3/6 |
| B | 20 | 4/6 |
| C | 37 | **0/6** |
| E | 41 | 2/6 |

**Unanimous on 2 of 43 (5%).** correlation(document-count, calibration) = **−0.89**.

⛔ **AND THE SPREAD WAS MY FAULT.** The prompt asked two different questions in adjacent sentences —
*"a section establishes what it MEANS"* (concept) and *"a NAME the document does not use"* (name).
Solvers anchored on different ones and both were following instructions.

⚠️ Worse, **the key was name-level while the pipeline needs concept-level.** All six "coinages" have
their concept in the document. `interactable_entity` is `**Assistant**: the entity that the end user
or developer interacts with`. The solvers I scored as wrong were answering the more useful question.

⇒ **Solver D was not the careful one — it shared my narrower reading.** Recorded because I reported
the opposite before checking.

## 4 · Single solver, concept-level — free

Four verdicts: `defined-here` / `renamed` / `world` / `absent`. Key rebuilt concept-level and
**shrunk from 6 to 4** — `pasted_text` and `delegated_authority_to_webpage` could not be keyed
honestly, so they were reported unscored rather than forced.

⭐ **4/4 on verdict and section.** The framing fixed what five solvers could not agree on.

⚠️ **But two defects survived:**
- **Over-resolution moved rather than vanished** — from `document` into `defined-here`. 29 uses,
  **8 of which fail the prompt's own "uses substantially this name" test** (`capable`, `disallowed`,
  `fulfillable` at 0 of 1 words present in the section cited). `absent`: **0 uses in 43.**
- **The verdict was right more often than the TERM** — 4/4 on verdict, ~1–2 of 4 on
  `document_term`. `interaction_entity` got *"tool"* while its identical twin two lines above got
  *"assistant"*.

### ⭐ The self-report, and why it was worth running

Asked in its own transcript, told not to re-read or revise. `DEBUGGING_TIPS` §6: a proposer, never a
diagnosis. **Both checkable claims held:**

| it said | check |
|---|---|
| *"I pulled 'disallowed content' from elsewhere"* | ✅ a `disallowed_content` section exists; the phrase appears in 3 clauses, none in the section cited |
| *"the document establishes concepts without naming them"* | ✅ **13 of 41 resolutions (32%)** give a `document_term` absent from the section cited |
| *"`absent` was a category I understood abstractly but didn't activate"* | consistent with 0 uses in 43 |
| *"I lost the thread"* on the twin predicates | unverifiable, and it said so |

⇒ **It independently reached the gap I had already been forced into** — I dropped `pasted_text` from
the key because the concept is present with no document noun. Two arrivals at the same structural
point, one mechanical and one introspective, is the strongest signal available here.

## 5 · Term-first, five verdicts — free, running

`document_term` becomes the **primary output**; the verdict falls out of whether one exists. Adds
**`described-not-named`** for the 32% case, requires `document_term` verbatim from the cited
passage, and forces an explicit `considered_absent` on every entry.

⭐ **The key grows to 5 and spans two verdicts** (2 `renamed`, 3 `described-not-named`), so a model
answering everything the same way cannot score. `pasted_text` becomes keyable *because* the new
verdict exists.

---

## What the sequence says, so far

1. ⭐ **Four of five iterations were fixing my instrument, not measuring the model.** The one real
   model-side finding — that over-resolution persists under renaming — only became visible once the
   prompt stopped being ambiguous.
2. ⛔ **A verdict that is never used is not a verdict.** `absent` was unused in 43 under v2, and the
   same shape appeared in v1 under a different name. A category needs forcing, not offering.
3. ⚠️ **Ground truth must match what the pipeline consumes.** My first key tested name-absence; the
   pipeline needs the document's wording. The key was measuring a different question from the one
   worth asking, and it took a spread of 5-to-41 to notice.
4. **Total spend: $0.042.** The panel work was free — subagent tokens are not API spend, which is
   why five solvers was affordable at all.

## 6 · Multi-turn iteration to self-sufficiency, n=5 — free (subagents)

The design Matt specified: turn 1 gather passages for a concept, turn 2 write the most
self-sufficient formal definition those passages support, **and if it is not self-sufficient, go
back for passages on the newly-opened predicates and repeat** — then consolidate across the five
runs. Definitions annotated with the section each rule came from. 8 concepts × 5 runs, bounded at
4 rounds. Scored by `iter_score.py`.

⭐ **This existed to answer the one question experiment 5 could not: single-shot formalization
opened 2–3 new undefined predicates per concept, so does the recursion have a fixed point?**

### It terminates, and the answer is still no

| | `[RAN]` |
|---|---|
| concept-runs that closed | **14 of 40** |
| `conflicts_with_later_same_authority/1` | **3 rounds in all 5 runs, closed in 0 of 5** |
| `interaction_entity/1` | **1 round, closed, 5 of 5** |
| round-to-round transitions | n=48 — **shrank 22 · flat 15 · grew 11** |
| concept-runs ending with MORE open than they started | **5** (worst `[4, 10, 8]`) |

⇒ **The borrow set does not run away, but it does not reliably shrink either.** Nearly a quarter of
all transitions ADD open predicates. Gathering more of the document to close a definition opens
more than it closes often enough that four rounds is not a bound, it is a cutoff.

### ⛔ THE DECISIVE RESULT: consolidation yields nothing

Rules matched on **(head, body-predicate set)** — structure, not text, so paraphrase cannot cost a
match.

| concept | distinct rule shapes | shared by ≥3 of 5 runs |
|---|---|---|
| `conflicts_with_later_same_authority/1` | 23 | **0** |
| `policy_class/2` | 15 | **0** |
| `refusal_style/1` | 8 | **0** |
| `task/1`, `pasted_text/1`, `new_material/1` | 7 each | **0** |
| `interactable_entity/1`, `interaction_entity/1` | 2 each | 1 — and it is a **body-less ground fact** |

**Borrowed-predicate agreement is 0.00 on all eight concepts.** `conflicts_with_later_same_authority`
accumulated a union of **28** open predicate names across five runs with **not one** shared by all
five. Defined-head agreement is 0.18, and the five names shared by every run are **exactly five of
the eight target names supplied in the prompt** — every name the runs agree on is a name we gave
them. Emergent agreement is **zero**.

### ⚠️ This is not a competence failure, which is what makes it a finding

The runs are individually good: **89% of 205 passages verbatim** in the section named (4 more
verbatim elsewhere, 19 not found), **clingo accepts 106 of 113 (94%)** final rules, and only **1 of
40** claimed closure it did not have. Five careful, document-grounded, individually defensible
definitions that do not overlap.

⇒ **Iterating makes vocabulary convergence WORSE, not better: 0.06 single-shot → 0.00 iterated.**
Each additional round coins more names, and names are the thing that does not converge. The
recursion is real and the fixed point is not reachable by asking harder.

### What it says about Invariant 1

Arm **C** — *"a deterministic lookup the model never sees"* — requires that lookup to exist. This is
the second experiment to find that it can be built **only where the document supplies the name
itself**: convergence tracks `**Term**:` definitions and nothing else. Experiment 5 found this at the
predicate level; experiment 6 finds it survives unbounded iteration.

⛔ **Not a ruling.** Whether that means arm C is dead, or means arm C must be seeded from the
document's own `**Term**:` inventory and refuse everything else, is Matt's call — recorded in
`OPEN_QUESTIONS.md` Q-6.

⚠️ **Two instrument defects found and fixed while scoring this, both of which had already produced a
wrong number:** the verbatim normaliser did not strip `**markdown emphasis**` (76% reported, **88%**
true — `DEBUGGING_TIPS` §17, third time this instrument has been the broken part), and the
open-set agreement table scored a concept 0.00 when four of five runs closed it cleanly, because
Jaccard over empty sets reads as total disagreement. The `runs w/ 0 open` column exists so the
figure can be read at all.

### ⛔ Reading the transcripts changed the conclusion — 62% of it was RENAMING

Matt asked why the non-closing concepts did not close. Reading them found that **the open-set SIZE
metric above cannot distinguish resolving from spinning**, and that most of the runs were spinning.

`task/1`, run 5, all three rounds:

```
round 1   task(G) :- complex_or_multistep(G).
round 2   task(G) :- user_request_for(G).
round 3   task(G) :- requested_goal(G).
```

Three unrelated one-predicate paraphrases, each **replacing** the last rather than defining what the
last opened. Open counts `[2, 2, 1]` — which the size metric reports as **converging**.

⇒ New measure, `B2`: an open predicate is **carried** if the next round still owes it or later
defines it, and **replaced** if it vanishes having never been defined.

| | `[RAN]` n=159 |
|---|---|
| carried — the round engaged with it | **61 (38%)** |
| ⛔ **replaced, never defined** | **98 (62%)** |
| concept-runs that dropped an undefined predicate rather than define it | **27 of 40** |

⭐ **So the headline result is measuring two things at once, and they have different remedies.**

### Three reasons a definition did not close, and only one is about the document

Classifying every open predicate in the transcripts:

**(1) Genuinely underdetermined by the document — the real finding.** The spec says an instruction is
superseded if a later one at the same level *"either contradicts it, overrides it, or otherwise makes
it irrelevant"*. It **names three relations and defines none**. `contradicts/2`, `overrides/2`,
`makes_irrelevant/2` are carried by every run that reaches them and closed by none. ⭐ This is
correct behaviour finding a correct gap, and it is the output worth having.

**(2) ⚠️ MISSING PIPELINE METADATA, not a document gap.** Run 3 opened `in_spec/1`,
`root_section/1`, `system_section/1`, `developer_section/1`, `user_section/1`, `guideline_section/1`,
`in_section/2` — and quoted the document saying *"Each section of the spec, and message role in the
input conversation, is assigned an authority level."* The document **states** that every section has
an authority level; the corpus does not **carry** it. Seven open predicates that are an artifact gap
on our side and would close as ground facts if a section's authority were a corpus field.

**(3) ⚠️ SITUATION VOCABULARY THE PROMPT FAILED TO FIX — my defect.** `message/1`, `role/2`,
`message_order/2`, `in_message/2`, `message_content/2` are exactly the *"plain facts about the
situation being judged"* the prompt named as primitive. **Run 2 declared them primitive; run 3 left
them open.** Same predicates, same document, opposite classification — because the prompt gave a
**criterion** for primitive and no **list**. The runs disagree about where the bottom of the
formalization is, not about what the document says.

⇒ **A meaningful part of the 0.00 agreement is (2) and (3), which are ours to fix, not the
document's.** What a fair re-run needs: the situation vocabulary supplied as a fixed primitive list,
section authority carried on the corpus, and a driver that **pins the open set** so a round cannot
discharge a predicate by paraphrasing the head. Only what survives that is evidence about the
document.

⛔ **The one thing not rescued by any of that is (1)**, and it is also the thing five runs agreed on.

### ⭐ Do the runs find the SAME SECTIONS? Yes — in round 1, and only in round 1

Matt asked this directly. Sections cited per concept, five runs, same 8 concepts:

| | all-5 | union | agreement | cited by exactly ONE run |
|---|---|---|---|---|
| **single-turn retrieval** (`subset_run1..5`) | 9 | 14 | **0.64** | 3 of 14 (21%) |
| **multi-turn iterative** (`iter_run1..5`) | 7 | 24 | **0.29** | 8 of 24 (33%) |

Single-turn: **5 of 8 concepts unanimous at 1.00**, and 7 of 8 share at least one section. So the
answer to *"do they typically find the same supporting sections"* is **yes** — retrieval was never
the weak link.

⛔ **Multi-turn made it worse, and the by-round split says exactly how:**

| | in all 5 | union | agreement |
|---|---|---|---|
| round 1 alone (8 concepts) | 7 | 9 | **0.78** |
| round 2 alone (4 concepts) | 3 | 10 | 0.30 |
| round 3 alone (1 concept) | **0** | 3 | **0.00** |
| cumulative through 1 / 2 / 3 / 4 | 7 / **7 / 7 / 7** | 9 / 19 / 24 / 24 | 0.78 / 0.37 / 0.29 / 0.29 |

⭐ **The all-5 column never moves after round 1.** Fifteen sections are added across rounds 2–4 and
**not one of them is found by all five runs.** Every section the iteration discovered is a section
some single run found alone.

⇒ **The mechanism, and it is not a retrieval defect.** Round 1 asks all five runs the *same*
question — *"what defines this concept?"* — and they converge on it at 0.78. Rounds 2+ ask *"what
defines the predicates YOU just opened"*, and those predicates agree at **0.00**. The later rounds
are retrieving competently against five different questions. **The loop manufactures the divergence
it then propagates.**

⚠️ **This is the strongest argument yet that the resolution target should be the CONCEPT, not the
predicate** — which is the same shape as experiment 4's 4/4, arrived at from the opposite direction.
Recorded, not ruled: see `OPEN_QUESTIONS.md` Q-6.

## 7 · EXTENSIONAL identity — the concept IS the text it points at

**Matt's proposal, 2026-08-08, and it inverts the whole line of attack.** Stop trying to say what a
borrowed predicate *means*. Let its identity be **the region of the document it is grounded in**.
Names that point at the same text are the same concept; a name is then just a label drawn from the
set and any member will do. Relations fall out of set algebra — containment is specialisation,
intersection a shared component, disjointness independence.

⭐ **The measurements favour this over anything tried in §1–6.** It builds identity out of section
retrieval, the *only* signal that survived repetition (0.78 across five runs, 5 of 8 concepts
unanimous), and discards predicate vocabulary, which never did (0.06 → 0.00). It is also **statically
checkable**, which no definition ever was: a span is in the document or it is not.

### ⛔ But the stored data cannot test it — the extension encodes the CLAUSE, not the concept

`extension_id.py` over `solver_v4.json`, 41 predicates with locatable verbatim excerpts:

| character-Jaccard band | pairs | **share a borrowing clause** |
|---|---|---|
| 1.00 | 5 | **5 (100%)** |
| 0.8+ | 1 | 1 (100%) |
| 0.5+ | 8 | 8 (100%) |
| any overlap at all | 31 | 26 (84%) |
| **baseline, all 820 pairs** | | **104 (13%)** |

⇒ **Similarity is measuring provenance.** The resolver was told which clause wanted each predicate,
so it cited that clause's home passage — **the same passage for every predicate that clause
borrows.** `includes_malicious_instructions` and `not_read_carefully` score **1.00** because both are
`m0105`'s, not because they mean the same thing.

Two more results that indict the instrument rather than the idea:

- ⛔ **`interactable_entity/1` and `interaction_entity/1` have no locatable extension at all.**
  `m0053`'s twins are the exact defect Q-6 names, and the method is **silent** on them.
- ⚠️ **The only genuine cross-clause synonym pair — `transformation_of_user_content` (`m0255`) and
  `translation_of_user_content` (`m0150`) — merges at SECTION granularity and separates at SPAN
  granularity.** The granularity that removes the confound also destroys the signal.
- The 29 "cross-clause" section-level merges are a single `m0091 × m0079` cross-product: two clauses
  that share a section.

⚠️ **Two instrument defects found and fixed here too**, both of which had already produced output I
was about to read: any-overlap identity is dominated by how much text a model chose to quote (one
long excerpt overlaps everything), and union-find takes the *transitive closure* of overlap, so
A–B and B–C chained unrelated names into one 8-member blob. Together they manufactured a containment
table whose 16 pairs had the **same right-hand side 15 times**. Replaced with character-Jaccard and
no chaining.

### ⭐ PRE-REGISTERED: the clause-blind retrieval experiment

The confound has one cause — the resolver knew the borrowing clause. Remove it: hand the model the
whole document and a **shuffled list of predicate names with no clause id, no section of origin, and
no grouping**, and ask where each is grounded. The extension then cannot encode provenance.

⭐ **The confound becomes the control.** Predicates borrowed by the SAME clause that are plainly
different conditions are a ready-made negative key — nothing about clause-blind retrieval should put
them on the same text.

**Written before the run, per `REPRODUCIBILITY.md`'s sandwich rule:**

| | prediction | what it decides |
|---|---|---|
| P1 | same-clause pairs drop from **100%** of the high-similarity band toward the **13%** baseline | if it stays high, extension identity is provenance and the idea fails on this corpus |
| P2 | `interactable_entity/1` and `interaction_entity/1` land on **overlapping text** | the case the whole proposal is for |
| P3 | `transformation_of_user_content/1` and `translation_of_user_content/1` land on overlapping text **despite different clauses** | cross-clause synonymy is detectable at all |
| P4 | `unnecessary_request/1` and `unreliable_destination/1` (both `m0150`, different conditions) **separate** | the negative control; if these still merge, granularity is too coarse regardless of the confound |
| P5 | the 6 known coinages resolve to **no span** | a name with no grounding must get an empty extension, not a guessed one |

⛔ **P1 and P4 are the falsifiers.** Either alone sinks the extensional design as stated; P2/P3
failing would mean it works but not for the case that motivated it.

### The clause-blind run, n=3 — stable, and it does not do the job it was for

Against `DOCUMENT_CLEAN.txt` (needs-blocks stripped, corpus assertion in `blind_score.py`).
Grounded 38 / 35 / 38 of 43; ungrounded 5 / 8 / 5. ⭐ **Removing the leak cost 4–8 groundings per
run** — the leaked runs scored 42–43 of 43, which is the fingerprint of a lookup.

⭐ **THE STRONG POSITIVE — extensional identity is STABLE.** 28 names grounded in all three runs;
of their **378 pairs, 368 (97%)** get the same overlap / no-overlap verdict in every run. Set that
beside the intension-based numbers on the same corpus — vocabulary agreement 0.06 single-shot, 0.00
iterated, 0 shared rule shapes for 6 of 8 concepts. **Extension reproduces; intension does not.**

⛔ **AND IT FAILS THE CASE IT EXISTS FOR (P2).** `interactable_entity/1` and `interaction_entity/1`
score **0.00** in both runs that ground them. Read blind, the models resolve them as **opposites**:

| run | `interaction_entity/1` | `interactable_entity/1` |
|---|---|---|
| 2 | `**Assistant**: the entity that the end user or developer interacts with.` | `**User**: a user of a product made by OpenAI` |
| 3 | the `role:` definition | Assistant + Developer + User + Tool |

⚠️ **And run 2's reading is defensible English** — "the entity that interacts" and "the entity that
can be interacted with" *are* different things. `m0053` used both for one idea. ⇒ **Extensional
identity cannot detect that two names were sloppily coined for one concept, because it resolves each
name on its own reading — and the names genuinely read differently.** Detecting the twins requires
the clause context, which is exactly what introduces the confound the blind design removed. That is
a real tension, not a tuning problem.

### ⚠️ Two of the five pre-registered predictions were badly formed. Recorded as such.

**P3 was wrong and the runs are right.** All three put `transformation_of_user_content` and
`translation_of_user_content` on **adjacent, non-overlapping** parts of one sentence:

```
transformation → "transform or analyze content that the user has directly provided"
translation    → "tasks such as translating, paraphrasing, summarizing, classifying, ..."
```

⭐ **That is genus and species, not synonymy** — translation is one item in the list the
transformation rule governs. The models found the right structure; **I predicted a merge and
measured raw overlap, so the correct answer scored 0.00.** This is the ontology signal the proposal
predicted, arriving in the one place I had built no way to see it: **containment and adjacency need
their own measure, distinct from overlap.**

**P5 was flagged flawed before scoring** and behaved as flagged — 4 / 5 / 5 of the six "coinages"
got spans, which under extensional identity is the *right* answer, since all six have their concept
in the document even where the name's words do not.

**P1 became uninterpretable once the leak was removed.** Same-clause share fell from 100% to
**86% / 75% / 50%** against an 11–12% chance rate — but on only **7 / 8 / 2** high-similarity pairs,
and more importantly: with the model blind, predicates from one clause landing on one passage is no
longer a confound, it is **a true fact about the document**. A clause is a sentence, and the
conditions it borrows really are established together. P1 cannot separate "leak" from "truth" and
should not be re-used in this form.

**P4, the surviving falsifier, mostly held:** `unnecessary_request` and `unreliable_destination`
(both `m0150`, plainly different conditions) separated at **0.00 in 2 of 3 runs**, 0.50 in the third.

### ⇒ Where this leaves the proposal

⭐ **Kept:** extension is the only concept-identity signal measured on this corpus that reproduces
across runs (97%), and it is statically checkable. Everything intension-based is at or near zero.

⛔ **Not kept as stated:** it does not merge sloppy twin coinages, and cannot, without the clause
context it was designed to exclude.

⚠️ **Unmeasured and now the obvious next question:** the relations — containment, adjacency, nesting
— which showed up unbidden in P3 and which no instrument here can see. `extension_id.py`'s
containment test exists but was never run against clause-blind data.

⛔ **Nothing decided.** `OPEN_QUESTIONS.md` Q-6.

## 8 · ⛔ CORRECTION: the twins never co-occur, and the tension was mis-stated

Matt asked whether we can keep the context needed to tell apart two concepts established in one
passage. Checking the stored modules to answer it overturned a claim this log and `OPEN_QUESTIONS.md`
Q-6 had both been repeating.

**`interactable_entity` and `interaction_entity` are not two names in one module.** They are one
clause translated twice:

```
run 20260807-143853:  defines(m0053, assistant, interaction_entity).
run 20260807-154618:  defines(m0053, assistant, interactable_entity).
```

Same clause, same slot, same `kind: assistant`, and `assistant` glossed identically in both. Only the
coined term differs. ⇒ **Not a concept-identity failure. Run-to-run instability in one field.**

### And it is not confined to that field `[RAN]`

Every clause in the run store translated more than once, comparing the sets of names:

| | agreement across repeat runs of the SAME clause |
|---|---|
| concept names — what a clause **introduces** | **0.30** (11 of 37) |
| ⛔ **borrowed names — what a clause NEEDS** | **0.00** (0 of 22) |

Per clause the borrowed-name agreement is 0.00 for `m0079` (union 8), `m0105` (7), `m0150` (6),
`m0014` (1); the three clauses scoring 1.00 borrow **nothing**, so they are not evidence.

⭐ **Zero of twenty-two borrowed names are coined the same way twice. The twins are not a special
case — every borrowed name is a twin.** `m0053`'s pair is merely the one where both spellings
survived into the corpus and got noticed.

⚠️ Glosses are far more stable than names: of 45 concept glosses seen in more than one run, **only 6
differ, and all 6 are paraphrase** (*"through a system message"* / *"through system messages"*). The
model agrees about the meaning and disagrees about the label, every time.

### ⇒ The answer to Matt's question: the tension is not real, because it is two jobs

**Differentiating** two concepts established in one passage, and **identifying** two names as one
concept, need different information from different sources — and only the first one needs the
document at all.

| job | source | already measured |
|---|---|---|
| tell apart two conditions in one sentence | the DOCUMENT | ✅ clause-blind does it — P4 separated `unnecessary_request`/`unreliable_destination` at 0.00 in 2 of 3 runs, and pairwise verdicts are **97%** stable |
| know that two names are one concept | ⭐ **our own RUN STORE** | mechanical: same clause + same slot ⇒ same concept, **by construction**. No model, no retrieval |

⇒ **The confound never came from having clause context. It came from asking one model, in one pass,
to do both jobs while holding the clause** — at which point provenance is the cheapest way to answer
both, and it did.

**Three designs that keep the context without the confound, in increasing order of what the data
supports:**

- **(a) sibling-blind, clause-visible** — show the using clause but resolve ONE borrowed name at a
  time with the clause's other names hidden. The clause supplies the role; the hiding prevents one
  passage being spread over all siblings. ⚠️ Testable directly: same-clause share of high-similarity
  pairs must stay near the 11–12% chance rate while grounding rises.
- **(b) ground blind, then discriminate with context** — keep round 1 exactly as it is (97% stable),
  then show the model the clause, the sibling names AND their fixed spans, asking only *"must any two
  of these be narrowed so they stop overlapping?"* ⭐ The context cannot manufacture the extension
  because the extension is already fixed before the context is shown.
- **(c) never ask the model to merge at all** — identity comes from the run store, the document is
  only ever asked *where is this grounded*. ⭐ **The design the measurements most support**, because
  it dissolves the tension instead of trading it off.

⛔ **Nothing decided.** But note what (c) implies and Q-6 must now record: with borrowed-name
agreement at **0.00**, the coined name is not carrying information at all, and a pipeline that
resolves names is resolving noise. The stable things are the **clause+slot** (ours, free) and the
**gloss** (0.30–1.00, and its disagreements are paraphrase).
