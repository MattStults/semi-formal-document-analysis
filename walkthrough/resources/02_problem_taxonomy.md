# Enumerating the problem space — what exists, and how to get coverage we can defend

Checked 2026-08-07. Answers two questions: are there resources for the list, and is there a way to
argue the list is complete rather than merely long.

---

## Part 1 — Two established taxonomies, and they cover different halves

### Document-side defects — Basili & Weiss

Six types, long-established in requirements inspection:

| type | meaning |
|---|---|
| **missing / omission** | required content absent |
| **incorrect fact** | states something untrue |
| **inconsistent information** | two parts conflict |
| **ambiguous** | admits more than one reading |
| **extraneous information** | present but not required |
| **miscellaneous** | the honest residual |

⭐ These are defects **in the source document**, not in our translation. That distinction is
load-bearing: a clause that is genuinely ambiguous has no single correct translation, so it is not
a bug to fix — it is a reading to *enumerate*. That is precisely what `interp/1` and R4's
alternative-readings machinery exist for. Mixing document-side and translation-side problems in
one list is the first thing that will make the taxonomy incoherent.

### Ambiguity, decomposed — Berry & Kamsties (2004)

Their top level is **vagueness · generality · linguistic · software-engineering** ambiguity, with
linguistic further split:

| kind | occurs when |
|---|---|
| **lexical** | a word has several meanings (homonymy, polysemy) |
| **syntactic** | one word sequence admits more than one grammatical structure |
| **semantic** | a sentence has more than one reading in context, with no lexical or syntactic ambiguity |
| **pragmatic** | a sentence means different things depending on the context of utterance |
| **language error** | the text is simply wrong |

And two neighbours they treat separately:
- **vagueness** — borderline cases, truth value indeterminate ("excessive hedging", "reasonable")
- **generality** — overly broad, requires further specification to be precise

⚠️ **Vagueness and generality are the ones that will bite us most**, because a normative spec is
full of them by design — *"avoid excessive hedging"*, *"seemingly legitimate research purposes"* —
and neither is an error. They are the clause telling you a judgement call lives here.

---

## Part 2 — Two ways to argue coverage

### A. Faceted decomposition: coverage by construction

You cannot prove a list of naturally-occurring problems is complete. You *can* define orthogonal
dimensions and take the cross-product, which makes the cells exhaustive **relative to the
dimensions** and makes empty cells informative rather than invisible.

⚠️ **The facets must be genuinely disjoint or the claim fails.** An earlier draft used a five-way
"where" axis including *linkage*. That does not work: linkage is not a place a defect can live, it
is a property of two translations considered together, so "a needed link was not made" and
"missing cross-reference" are the same event counted twice. A cross-product over overlapping
facets double-counts, and coverage-by-construction is exactly the claim that double-counting
destroys.

**The two facets, disjoint:**

**ARTIFACT** — which object contains the defect: source document · translation · probe set · check suite
**DIRECTION** — omission (something absent) · commission (something added) · distortion (something changed)

4 × 3 = **12 cells**. Linkage failures land as translation omissions (failed to reference) or
translation distortions (referenced the wrong thing), which is where they belong.

#### The grid, with current occupancy

| | omission | commission | distortion |
|---|---|---|---|
| **source document** | — | — | — |
| **translation** | missing cross-reference · hollow stub | fabricated constant · dead constraint | negation-hides-the-reason · false convergence |
| **probe set** | branch not covered | — | — |
| **check suite** | judge passes a fabrication | — | — |

**6 of 12 occupied.** Reading the empty cells:

- ⭐ **The whole source-document row is empty**, and it maps exactly onto Basili & Weiss:
  *omission* = "missing", *commission* = "incorrect fact", *distortion* = "inconsistent
  information". The spec asserting something false, or contradicting itself, is a real category
  with no instance yet — and it is what the parked **provision × provision** capability was aimed
  at. Empty here means *unexamined*, not *absent*.
- **probe set × commission** — a probe asserting an impossible situation — *has* occurred (a case
  claiming material was both newly supplied and a transformation of user content). It belongs in
  the grid; it is listed below rather than in the cell only because it was caught before being
  recorded as an example.
- **check suite × commission / distortion** — a check that fires on correct input, or reports the
  wrong reason. Both are real risks for a check suite this young and neither has been looked for.

#### Evidence the classifier works

Not the grid — this is the observed set, each labelled with the cell it lands in. Its job is to
show the two facets actually partition real cases:

| problem | cell |
|---|---|
| fabricated policy constant | translation × commission |
| dead constraint (unfireable rule) | translation × commission |
| missing cross-reference | translation × omission |
| hollow stub (name imported, content not) | translation × omission |
| negation-as-failure states a wrong reason | translation × distortion |
| false convergence (one name, two meanings) | translation × distortion |
| divergent predicate names across clauses | translation × distortion |
| probe set misses a branch | probe set × omission |
| incoherent probe (contradictory premises) | probe set × commission |
| judge passes a fabricated entity | check suite × omission |
| clause is vague by design | source document × **not an error** — a reading to enumerate |

⚠️ **The last row is not a cell.** Document-side ambiguity, vagueness and generality are not
defects in any of the twelve senses; they are the document declining to decide. They belong to
the `interp/1` alternative-readings machinery, not to this grid. Keeping them out is what stops
the taxonomy from treating "the spec left this open" as a bug to be fixed.

### B. ⭐ Mutation: coverage over the *detectable* space, with ground truth for free

**Source:** *MutDafny: A Mutation-Based Approach to Assess Dafny Specifications* (arXiv 2511.15403).

The move that makes this strong: **you cannot reliably enumerate what goes wrong, but you can
enumerate the syntactic transformations of a translation you believe is correct.** Each mutation
is a synthetic defect with known ground truth. Then:

- a mutant is **killed** if some check rejects it;
- the **mutation score** is the fraction killed;
- the score is a defensible coverage number — *"our checks kill 84% of mutants, and here are the
  survivor classes"* — rather than a claim that a hand-written list was complete.

⚠️ **Direction differs from MutDafny and this matters.** MutDafny mutates the *code* and asks
whether the *specification* is sensitive enough to notice. We mutate the *translation* and ask
whether our *check suite* is sensitive enough to notice. Same machinery, inverted roles; do not
import their numbers.

Mutation operators for an ASP translation, drawn from the failures already seen:

| operator | synthesises |
|---|---|
| delete a body literal | over-permissive rule |
| add a body literal | over-restrictive rule |
| swap a predicate for a same-arity sibling | false convergence |
| rename a predicate to a fresh name | divergence / broken link |
| replace a constant with a fresh one | fabricated entity |
| negate a body literal | inverted condition |
| replace a positive reason atom with `not …` | untraceable reason |
| delete a whole rule | omitted claim |
| replace a rule body with an unreachable atom | vacuity |
| collapse a structured term to a bare constant | hollow stub |
| change arity | silent link failure |

⭐ **The survivors are the finding.** A mutant no check kills names a real hole in the check suite,
and it does so without anyone having to imagine that hole in advance. That is the completeness
argument.

⚠️ Note: no ASP-specific mutation-operator set was found in the literature search. The list above
is derived from our own observed failures plus MutDafny's general categories (logical, relational,
quantifier, assertion), so it is a starting point, not a standard.

---

## Part 3 — The one local precedent, and exactly how far it goes

⛔ **The repo has NO approach to validating a formal translation.** The walkthrough on 2026-08-07
was the first attempt at one. Nothing below should be read as "we already solved this."

What exists is a precedent for **taxonomy construction**, not for translation validation.
`audit_disagreements.CAUSE_TAXONOMY` is a closed set of 13 classes, each with a mechanical
signature the validator enforces, built to explain **why the lexical retrieval scorer disagreed
with the panel** — `fp_promiscuous_atom`, `fp_threshold_drift`, `fn_family_absent_from_vocabulary`
and so on. No formal translation appears anywhere in it. It is a post-hoc diagnostic over
retrieval disagreements.

**The one transferable lesson:** declaring the classes *before* measuring turns "did we think of
everything?" into a reportable result. Run over 294 cases it populated 8; five returned nothing,
and those five are data.

⚠️ **And it should not be described as having worked cleanly.** Three known problems, all live:

- Two of the five empty classes are `boundary_dispute_*` — precisely the ones that would have
  evidenced the product's headline claim. Whether they are empty because the phenomenon does not
  occur or because the instrument could not see it is **unresolved**.
- **155 of 294 cases (53%) fell into a single class.** A taxonomy whose mass concentrates that
  hard in one bin is at least a hint that it is too coarse exactly where the phenomenon lives.
- The census's `side` field was **withdrawn** as unreliable.

⇒ Carry the *closed-taxonomy-first* discipline. Carry the warning that **an empty class is
ambiguous** — absent phenomenon or blind instrument, and you cannot tell from the count. Do not
carry any implication that the pattern has been validated on this problem, because it has not been
applied to this problem at all.

## Proposed shape for the jsonl

Each record is one example, with:

- `id`, `clause_id`, `source_text`
- `cell` — the (where, direction) pair from §2A
- `named_type` — the Basili & Weiss or Berry & Kamsties type where one applies
- `origin` — `observed` (hit in real work) or `mutant` (synthesised, with the operator recorded)
- `ground_truth` — what the correct handling is
- `caught_by` — which checks detect it, empty if none
- `notes`

Two populations in one file, distinguished by `origin`. The observed ones are real but sparse and
biased toward what we happened to hit. The mutants are systematic and cover the space. Neither
alone is enough: mutants cannot invent a failure mode absent from the operator list, and observed
cases cannot claim coverage.

---

## Sources

- [Basili & Weiss defect taxonomy — via *Defect Types and Software Inspection Techniques*](https://thescipub.com/pdf/jcssp.2017.470.495.pdf)
- [*Classification of defect types in requirements specifications*](https://www.academia.edu/69763709/Classification_of_defect_types_in_requirements_specifications_Literature_review_proposal_and_assessment)
- [Berry & Kamsties ambiguity taxonomy — via *Identifying and Classifying Ambiguity for Regulatory Requirements*](https://www.cc.gatech.edu/~aianton/assets/2014_re14_ambiguity.pdf)
- [*MutDafny: A Mutation-Based Approach to Assess Dafny Specifications* (arXiv 2511.15403)](https://arxiv.org/pdf/2511.15403)
- [*A Retrieval-Augmented Framework for Detecting and Resolving Pragmatic Ambiguities in NL Requirements* (arXiv 2607.04436)](https://arxiv.org/pdf/2607.04436)
