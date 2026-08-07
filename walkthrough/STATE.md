# State as of 2026-08-07, end of session

Written so the next session can start from the record rather than from a summary. Everything below
is either in a file (cited) or was decided in conversation and is being written down here for the
first time — the latter are marked ⭐ NEW.

---

## Rulings in force

| | |
|---|---|
| **Representation** | Plain clingo + a **superiority relation**. Not deontic operators. Recorded in `resources/03_pipeline.md` open question 1, with evidence in `resources/04_deolingo_assessment.md` |
| **Seat contracts** | Adopt all ten elements. `03_pipeline.md` open question 5 |
| **Ordering / lexicographic grade** | Deferred as `DEFERRED.md` D-1, with the safety check recorded — deferring it changes nothing stage 1 emits |
| **Licence taxonomy** | `textual` / `assumed` / `world`, graded not binary; a conclusion inherits the weakest licence in its derivation. Invariant 2 |
| **Concept identity** | A symbol is a dictionary index; the read-back renders the **definition**, not the label. Invariant 1 — but *when* concepts are fixed is open question 2 |

## ⭐ NEW — decided in conversation, not previously in any file

**1. Contradiction is BEHAVIOUR-versus-DOCUMENT, not document-internal.**
This was misread for most of the session. Consequences:
- both outputs — relevance and contradiction — are blocked on the **same missing query side**
- the earlier claim that "contradiction is nearly free, it needs no query" is **wrong**
- behaviour-vs-document contradiction is **norm versus norm**, which is where deontic logic is
  strongest and where we have no evidence

**2. ⭐ ANSWERED 2026-08-07 — the deontic question is closed.** `contradiction_probe/FINDINGS.md`.

**One encoding of the document, one of the behaviour, two queries off them.** Relevance is a
*projection* of the behaviour file, not extra input. The behaviour representation exists and
**names no clause** — the first time anything here has.

⛔ **The namespace separation is MANDATORY and was not obvious.** The behaviour is norm-shaped, so
putting it in `asserts/3` with the clauses is the simplification a translator reaches for. Adding
one line — `beats(clause, behaviour)` — makes a real conflict **disappear**, satisfiably, with the
acyclicity guard silent. That is compliance aggregation, which the ruling forbids. Needs a type
constraint, 2 lines.

**Deontic operators are NOT needed. Exactly one deontic AXIOM is:** `O(¬a) ≡ F(a)` over act
complements. The corpus states the same prohibition both ways — `m0208` *"must not generate"* /
`m0270` *"should refuse"* — and plain predicates see two unrelated ground terms. The hand-written
substitute is O(n²) and was **wrong on the first attempt**, producing a false positive between a
clause and a behaviour that agree.

**Other required fixes:** act-index both sides (the hypothesis as written derives **zero** conflicts
— a silent type error); `beats/2` → **`beats(Sayer, Winner, Loser)`**, because `m0255` *states* the
override, scores 5/6, and is unreachable without it.

⭐ **CEPA/CNPA is real, clause-local, and flips the verdict.** `m0263` covers harm *"to the user"*
where it could have said "or anyone on camera" — structured silence. The plain form answers "no
contradiction" by absence of a rule, and `closure=open` is **bit-identical** to `closure=cepa`.
Needs a **forced, per-act** closure declaration, enforced in `link.py`.

⭐ **Invariant 2 has no licence class for the behaviour text.** `textual`/`assumed`/`world` are all
defined relative to *the document*. A fourth class is needed or the invariant does not reach the
behaviour side at all.

**Contrary-to-duty is a non-issue:** zero clauses in 593 have a CTD antecedent. The blocker there is
that the norms one would hang off are **comparatives** (*"minimize side effects"*), which have no
violation condition.

⚠️ 17 clauses of 593, one behaviour, hand-encoded. `averts/2` is an inference the behaviour text
does not license and the CEPA/CNPA result rests on it entirely.

**3. The ontology-fit test measures the wrong consistency.** It measures run-to-run agreement on a
single token. Our failure modes are cross-document: do **synonyms converge** (#8), do **homonyms
separate** (#9). Neither is visible in run-to-run agreement.
⇒ The test should assign every eligible token, then check **internal consistency of assignments
across the document** — mechanical detection of candidate inconsistencies (near-identical glosses
on different concepts; one concept spanning contradictory glosses), model adjudication of only
those. **Not rebuilt yet. Do not run it as it stands.**

**4. Research findings adopted** into `03_pipeline.md` Part 4b — a CI job that runs published
queries against the published artifact, DPV's concept record, a named-removal changelog. Plus the
MIREL calibration: **~0.27 concept Jaccard between trained humans**, so our 20% multi-definition
rate is the ordinary rate, not a defect.

---

## Built and working

| | |
|---|---|
| `link.py` | anchor closure, unresolved names, rule-shape. RED-tested |
| `m0255.lp` + `clauses/` + 5 probe cases | one hand-written clause translation, linked, with case E covering the claim the other four could not reach |
| `witness.lp` | witness search, demonstrated |
| `model/` | formal model of the design: constraints, staleness guard, waivers requiring date/who/why, 15 integration tests. **15 findings, 0 blocking, all waived with reasons** |
| `paper_pipeline/` stage 0 | 7 competency questions, 18 executable instances, runs 16-as-declared |
| `paper_pipeline/ontology_fit.py` | 39 self-tests green — ⚠️ but measures the wrong thing, see NEW-3 |
| `deontic_probe/` | 6 relevance encodings, ablations, corpus ceilings |

## Never run

⭐ **Stage 1.** No model has produced a logic module for a clause in this form. The one worked
example was written by hand. Every downstream stage assumes its output.

---

## What the evidence says

**Measured, and it does not depend on anyone's encoding:**
- **57–68%** of what the frontier panel calls *core* is **not a conditional clause** — goals,
  headers, definitions, examples
- modal verbs are worse than useless as a relevance signal: MCC **0.005 / 0.129 / −0.068**; for
  over/under-caution, **10 modal-carrying passages are core and 197 are unanimously irrelevant**
- **12 of 13** condition names in a real extraction run were used exactly once, despite the
  extractor being configured to encourage sharing
- **46 of 228** reused concept names carry more than one definition — which the MIREL calibration
  now says is **normal**
- examples are **36–46%** of core passages, and no encoding consumes the `example(P,Q)` links that
  already exist

**Suggestive, with a stated leak:** the deontic relevance probe wrote its encodings knowing the
panel scores. Treat its successes as suggestive, its failures as the result. Its finding —
**deontic operators propagate relevance, they do not supply it** — rests on an ablation that
returns the empty set from all six encodings when the ontological block is removed.

---

## Open, in the order I would take them

1. ✅ **DONE — one behaviour represented, naming no clause.** `contradiction_probe/behaviour.lp`.
   The six required fixes are listed in NEW-2; none has been implemented. **Implementing them is
   now the top item**, in this order: act-indexing (free) → type constraint (2 lines) →
   `beats/3` → forced closure declaration → the `O(¬a) ≡ F(a)` axiom.
2. **Stage 1, both arms of open question 2** — supply the dictionary at generation, or normalise
   afterwards. Contrary published evidence exists against the first.
3. **Rebuild the ontology-fit test** against internal consistency (NEW-3).
4. **Licences on facts.** Invariant 2 is designed and unimplemented; it blocks the citation
   checker's coverage rule, the weakest-licence output, and eventually the grade.
5. **Example inheritance** — three lines, and examples are 36–46% of core. Probably the highest
   ratio of value to effort anywhere in this list.

## Cost

`spend.py`: **$2.06 of $8.50**. The ontology-fit live run is $0.0325 and is *not* authorised —
and per NEW-3 should not be run until rebuilt.

## Process notes worth carrying

- **A check whose "pass" state is indistinguishable from its "did not run" state is broken by
  design.** Three separate failures this session were that shape; `check.py`'s parse canary and
  `guard.py`'s self-test exist because of them.
- **Every measured claim states its source and its n.** Two of the headline numbers are n=1.
- The `walkthrough/` directory is **allowed to contradict the wider repo**; `03_pipeline.md` is its
  source of truth. See `README.md`.
