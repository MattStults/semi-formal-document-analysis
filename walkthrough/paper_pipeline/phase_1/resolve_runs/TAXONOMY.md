# What kinds of linkage are there, and does the test set cover them?

**DRAFT for review. Nothing built from this yet.** The scoring set for `resolve_probe.py` is
currently 43 real predicates with a 6-item key, and that key scores **one direction only** —
correct refusals. It cannot see a false refusal, and it has no case where refusing is *wrong*.

This is the brainstorm before building the rest.

---

## The four ways a lookup fails

Everything below exists to expose one of these. A category that cannot expose any is decoration.

| | failure | what it looks like |
|---|---|---|
| **F1** | **false refusal** | says *"not in the document"* about something the document defines. Silently narrows the corpus |
| **F2** | **false resolution** | names a defining section for something absent. ⛔ **The dangerous one** — it manufactures a citation, and a downstream reader has no way to tell |
| **F3** | **wrong section** | resolves to a section that *mentions* rather than *establishes*. Reads correctly and is wrong |
| **F4** | **arbitrary resolution** | picks one of many plausible sections without flagging that the choice was arbitrary |

---

## KNOWN GOOD — should resolve, to a nameable section

| | kind | grounded candidate | `[RAN]` |
|---|---|---|---|
| **G1** | **explicitly defined term** — the document says `**Term**: …` | `conversation`, `guideline`, `assistant` | **199 such terms exist** |
| **G2** | **snake_case of a document phrase** | `chain_of_command` | both words present, spans 14 sections |
| **G3** | **compound the document uses as a unit** | `restricted_content`, `system_message` | spans 29 / 23 sections |
| **G4** | ⭐ **defined by ENUMERATION, not definition** — the document lists instances and never gives a rule | `critical_high_severity_harm` — six instances, no definition | this is the shape `m0014` actually produced |
| **G5** | **compositional relation** built from document parts | `higher_authority/2` | needs constructing |

⚠️ **G4 is the one I would most expect to break a resolver.** There is no defining phrase to quote,
only a list — so a resolver demanding verbatim evidence may refuse a term the document genuinely
establishes. That is **F1** in its most likely form.

---

## KNOWN BAD — should NOT resolve to any section

⭐ **This splits three ways, and the split was invisible until I measured it.**

| | kind | grounded candidate | `[RAN]` |
|---|---|---|---|
| **B1** | **absent vocabulary** — a word simply is not in the document | `pasted_text` ("pasted" absent), `interactable_entity` ("interactable" absent) | 1 of 2 words present, spans **0** |
| **B2** | ⛔ **ABSENT COMPOUND — both words are document vocabulary, the compound is not** | `policy_class` | **both words present, spanning 9 sections** |
| **B3** | **plausible construction from common words** | `user_trust_level`, `content_severity_tier` | all words present, spanning **73** and **31** sections |
| **B4** | **world knowledge** — real, outside the document | `illegal`, `minor` | 7 clauses use "illegal", **0 define it** |
| **B5** | ⭐ **renameable near-miss** — the document has a *different* term for the same idea | `interactable_entity` vs the document's `assistant` | `m0053` coined it while defining "Assistant" |
| **B6** | **over-bundled** — packs conditions the document never bundles | `conflicts_with_later_same_authority` | real coinage |

⛔ **B2 and B3 are the hard cases and the current key contains only one of them.** A resolver
scanning for word presence will find "policy" and "class" scattered across 9 sections and can
assemble a confident, wrong citation. That is **F2**, and it is exactly the failure that would put a
fabricated citation into a stage-4 seat's dossier.

⚠️ **B5 is the most *useful* answer to get right**, because it is actionable: the remedy is
`rename-to-document-term`, and the claim is checkable. It is also the one where a resolver is most
tempted to resolve — the concept *is* in the document, just under another name.

---

## AMBIGUOUS — resolving to one section is itself an error

| | kind | grounded candidate | `[RAN]` |
|---|---|---|---|
| **A1** | **wide attractor** — the term is everywhere | `assistant`, `user` | **72 of 78 sections each** |
| **A2** | ⭐ **problem #9** — one name, two meanings in different sections | needs identifying | the design measures **46 of 228 reused names (20%)** carrying conflicting definitions |

⇒ A correct answer for A1 either names the *defining* section (`definitions`, for `assistant`) **or**
flags the ambiguity. Naming an arbitrary one of 72 is **F4**, and nothing in the current probe would
catch it.

---

## CONTROL — the fence

| | kind | why |
|---|---|---|
| **C1** | a **behaviour-namespace** name (`b_asserts`-side) | stage 1 is denied the behaviour side. A resolver that happily resolves one is a leak-fence signal, cheap to include |

---

## ⛔ What the current test set covers, and what it does not

| | covered today | by |
|---|---|---|
| G1–G5 | ⚠️ **incidentally** | some of the 43 real predicates are document terms, but **none is keyed**, so a false refusal scores as nothing |
| B1 | ✅ | `pasted_text`, `interactable_entity` |
| B2 | ✅ **one case** | `policy_class` |
| B3 | ⛔ **not at all** | must be constructed |
| B4 | ⛔ not keyed | `illegal` is not among the 43 |
| B5 | ✅ | `interactable_entity` |
| B6 | ✅ | `conflicts_with_later_same_authority` |
| A1, A2 | ⛔ **not at all** | must be constructed |
| C1 | ⛔ not at all | must be constructed |

⇒ **The current key measures F2 in its easiest form and nothing else.** It cannot detect a false
refusal (F1), cannot detect a wrong section (F3), and cannot detect arbitrary resolution (F4).

---

## Proposed shape of a complete set

Three groups, kept separable so a result can be read per group:

1. **the 43 REAL predicates** — the only ones that answer *"can it resolve what our translator
   actually produced?"* Keyed on the 6 known coinages. **Unchanged.**
2. **~15 KNOWN GOOD**, drawn from the 199 explicitly defined terms plus G4's enumeration case.
   Keyed to their defining section. ⭐ This is what makes **F1 and F3** measurable for the first time.
3. **~12 KNOWN BAD**, one or more per B-category, with **B2 and B3 deliberately over-weighted**
   because they are where a confident wrong citation comes from.
4. **~4 AMBIGUOUS + 1 CONTROL**, where the correct answer is *"the defining section"* or an explicit
   ambiguity flag, and any other single section is wrong.

⚠️ **Two design cautions I would want ruled on before building it:**

- **Constructed items must be indistinguishable in form from real ones.** If the fabricated ones
  read differently — longer, odder, more uniform — the model can score well by detecting *which list
  an item came from* rather than by reading the document. They should be interleaved and
  identically formatted, and the run should not say how many are planted.
- ⛔ **The prompt currently warns that some names are coinages.** With a mixed set that warning
  becomes a much stronger hint, and it will inflate refusals — which is precisely what the known-good
  group is there to measure. **Consider running one arm without the warning** to size the effect,
  since the warning's cost is now measurable and was not before.
