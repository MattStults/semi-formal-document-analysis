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
