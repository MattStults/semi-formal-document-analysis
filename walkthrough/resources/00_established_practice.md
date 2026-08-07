# Established practice for validating a text → formal translation

Checked 2026-08-07. Six practices with published provenance, each with its canonical example and
what it catches. Ordered by how directly it bears on what we are building.

---

## 1. Isomorphism — keep formal structure in 1:1 correspondence with the text

**Source:** Bench-Capon & Coenen, *Isomorphism and legal knowledge based systems*,
Artificial Intelligence and Law 1, 65–86 (1992).

The knowledge engineer follows the legal source as closely as possible, writing propositions that
paraphrase or reformulate items in the source text, translated literally according to the
straightforward reading an ordinary reader would give. One source item ↔ one representation item.

**The stated motivation is maintenance, not elegance:** legal knowledge must survive legislative
change, and that is only tractable if you can trace which formal item corresponds to which piece
of amended text.

**Practical form:** use an *intermediate representation* that holds the 1:1 correspondence, then
transform it into the executable formalism — rather than writing the executable form directly.

> **Example.** A statutory section with four sub-clauses becomes four addressable rule units, not
> one merged predicate, even when merging would be logically equivalent and shorter.

**Maps to us:** one clause → one `.lp` file, composed by linking rather than merging. Our
low-churn-document north star is the same argument Bench-Capon & Coenen make: the document is
stable but *will* be amended, and correspondence is what makes amendment cheap.

---

## 2. Round-trip paraphrase as a verification mechanism

**Source:** Attempto Controlled English (ACE) and the Attempto Parsing Engine (APE),
University of Zurich. See `attempto.ifi.uzh.ch`, and the APE parser.

APE translates ACE text into a Discourse Representation Structure, and **that translation is
reversible** — the DRS is verbalised back into Core ACE. The paraphrase is shown to the user as
feedback, indicating how the system understood the input; the user rephrases until the paraphrase
matches their intent.

**This is established as a verification mechanism**, not merely an authoring convenience.

> **Example.** An author writes a requirement, sees it verbalised back with a quantifier scoped
> differently than intended, and rewrites the sentence. The mismatch is visible *without* the
> author reading the logic.

⚠️ **Important structural difference from a blind-judge setup.** ACE's paraphrase goes back to the
**author**, who knows the intent and is checking comprehension. Handing the paraphrase to an
independent judge who never saw the source asks a different question — and is the design used by
the autoformalization work in §5.

**Maps to us:** the xclingo verbalisation. Both loops are available and they catch different
things: author-facing catches *misunderstanding*, judge-facing catches *unfaithfulness*.

---

## 3. Vacuity and coverage — the two standard sanity checks

**Sources:** Beer et al. on vacuous satisfaction and interesting witnesses; Kupferman & Vardi,
*Vacuity detection in temporal model checking*, STTT (2003); Kupferman, *Sanity Checks in Formal
Verification*, CONCUR (2006).

The field's own framing: **model checking succeeding is not evidence the specification is right.**
The specification may be satisfied in an unintended, trivial way. The two leading sanity checks
are **vacuity** and **coverage**.

> **Canonical example.** The property *"every request is eventually followed by a grant"* is
> **vacuously satisfied** in any system where requests are never sent. An *interesting witness* is
> a computation that satisfies the property **and contains a request**.

**What it catches:** rules that cannot fire, constraints whose antecedent is unreachable,
properties that hold because their trigger never occurs.

**Maps to us:** a constraint referencing a predicate that nothing derives is textbook vacuity —
and clingo already reports the ingredient (`atom does not occur in any rule head`). Requiring an
*interesting witness* per rule — a case where the rule actually fires — is the standard
strengthening, and it is cheap here.

---

## 4. Accept/reject probe pairs as a faithfulness signal

**Source:** *Verus-SpecGym: An Agentic Environment for Evaluating Specification
Autoformalization* (arXiv 2605.26457).

Uses executable specifications to check whether a generated specification **accepts and rejects
the right concrete cases** — a scalable faithfulness signal that needs **no expert-written
reference specification**.

> **Example.** A generated postcondition is exercised against implementations known to be correct
> (must accept) and implementations known to be buggy (must reject). A specification that accepts
> everything passes the first and fails the second.

**Why the pairing matters:** a specification that is too permissive passes every positive case.
Only the reject set detects over-permissiveness, and it is the failure mode that positive testing
structurally cannot see.

**Also reported there:** specification autoformalization is a *distinct bottleneck* — models that
can write correct code for a problem often fail to write a faithful specification for the same
problem. Do not assume translation quality tracks general capability.

**Maps to us:** every clause needs both a *must-violate* set and a *must-permit* set. Probe cases
that only test "does it correctly forbid" are half a test.

---

## 5. Independent judges, consensus, and human calibration

**Source:** *Beyond Compilation: Evaluating Faithful Natural-Language-to-Lean Statement
Formalization* (arXiv 2606.31002). Related: *Faithful Autoformalization of Natural Language
Assertions* (arXiv 2607.13303), the Monty framework's conformance score.

Method: compiler verification **plus** semantic faithfulness scoring by *independent LLM judges*,
with **strict consensus reporting** and **human expert calibration**.

**The stated purpose is to expose "compile-valid but meaning-shifted" statements at scale** — the
formalization type-checks and still says something other than the source.

> **Example.** A formal statement that compiles cleanly, uses the right symbols, and quantifies
> over the wrong domain. No structural check catches it; only semantic comparison against the
> source does.

**Maps to us:** structural checks (linking, vacuity) and semantic checks (read-back judging) are
complementary and neither substitutes for the other. Multiple independent judges with consensus,
calibrated against human judgement on a sample, is the established shape — not a single judge.

---

## 6. Bidirectional traceability

**Source:** RTCA DO-178C, *Software Considerations in Airborne Systems and Equipment
Certification*, §5.4 and §6.4.

Requires bidirectional trace links from each requirement down to the implementing code and the
verifying tests, and from each test back up to the requirement it validates. **Depth is scaled to
criticality level**, not applied uniformly: Level D traces system requirements → high-level
requirements → test cases; Levels B and C add high-level → low-level → source.

> **Practical reality.** Teams commonly maintain these in spreadsheets; manual traceability is the
> primary bottleneck, and every requirements change triggers substantial manual reconciliation.
> Traceability gaps found late trigger rework measured in months.

**Maps to us:** per-fact provenance — each formal fact naming the clause that licenses it. The
two lessons worth importing are *bidirectional* (text→formal and formal→text) and *scaled
granularity* (do not pay for per-atom traceability everywhere if per-clause suffices).

---

## Composite: what a validated translation looks like

| check | catches | mechanism | cost |
|---|---|---|---|
| isomorphism | untraceable structure; expensive amendment | one clause, one module, linked | authoring discipline |
| link resolution | missing dependencies | solver's own unresolved-atom report | one solve |
| vacuity + witness | rules that cannot fire | require a firing case per rule | one solve per rule |
| accept probes | under-permissiveness | must-violate cases | per clause |
| **reject probes** | **over-permissiveness** | **must-permit cases** | per clause |
| read-back to author | misunderstanding | verbalise, author rephrases | one call |
| read-back to blind judges | meaning shift | independent judges + consensus | n calls |
| per-fact provenance | imported or unlicensed facts | each fact names its source clause | authoring discipline |

**The two structural findings across all six sources:** *first*, structural validity and semantic
faithfulness are separate problems requiring separate machinery — passing a compiler, a linker or
a solver is explicitly not evidence of meaning. *Second*, the reject/permit half of testing is
where over-permissive formalizations hide, and it is the half most often omitted.

---

## Sources

- [Bench-Capon & Coenen, *Isomorphism and legal knowledge based systems* (1992)](https://link.springer.com/article/10.1007/BF00118479) · [PDF](https://cgi.csc.liv.ac.uk/~tbc/publications/AILawIsomorphism.pdf)
- [Attempto Controlled English — plural ambiguity and paraphrase](https://attempto.ifi.uzh.ch/site/pubs/papers/claw2000.pdf) · [APE parser](https://github.com/Attempto/APE)
- [Kupferman & Vardi, *Vacuity detection in temporal model checking*, STTT](https://link.springer.com/article/10.1007/s100090100062)
- [Kupferman, *Sanity Checks in Formal Verification*, CONCUR 2006](https://www.cs.huji.ac.il/~ornak/publications/concur06b.pdf)
- [*Verus-SpecGym: Evaluating Specification Autoformalization* (arXiv 2605.26457)](https://arxiv.org/abs/2605.26457)
- [*Beyond Compilation: Evaluating Faithful NL-to-Lean Statement Formalization* (arXiv 2606.31002)](https://arxiv.org/pdf/2606.31002)
- [*Faithful Autoformalization of Natural Language Assertions* (arXiv 2607.13303)](https://arxiv.org/abs/2607.13303)
- [DO-178C requirements traceability overview](https://www.parasoft.com/learning-center/do-178c/requirements-traceability/)
