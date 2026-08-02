# Literature Sweep 3: Autoformalization into Ontologies (2026-07-31)

*Third sweep, scoped to LLM pipelines turning normative/policy prose into typed vocabulary + relations + axioms (an ontology), not flat rule lists or math theorem-proving. Verified against fetched abstracts. Complements litreview.md + litreview2_components.md.*

---

## 1. De Jure — arXiv:2604.02276 (NEW, must-cite)
**Iterative LLM Self-Refinement for Structured Extraction of Regulatory Rules.** Four stages: Normalization (raw→structured Markdown) → Semantic Decomposition (LLM→typed structured rule units) → Evaluation (3 LLM-judge panels, 19 dimensions) → Iterative Repair (regenerate low-scoring extractions within budget, **fix upstream metadata/definitions BEFORE rules**). Rule schema: identifiers, descriptive fields, a **9-field statement decomposition** (action, action_object, method, conditions, constraints, exceptions, penalties, purpose, verbatim span), role targets, section refs. NOT an OWL ontology — a deontic frame/typed record. Results: monotonic improvement over 3 iterations; 73.8%/84.0% human preference vs prior at single/deep retrieval; generalizes to finance, healthcare, **EU AI Act (Reg 2024/1689)** at 4.71/5 no tuning; **Non-Hallucination = uniform 5.00** (attributed to schema constraint). COPY: the "repair upstream vocabulary before rules" ordering = our atoms→axioms→rules; the LLM-judge dimension battery (Non-Hallucination, Fidelity-to-Source, Consistency, Actionability). CAVEAT: their no-hallucination is judge-measured on own schema, not solver-verified — our checker+solver is the upgrade to position against.

## 2. Towards a Common Framework for Autoformalization — arXiv:2509.09810 (NEW, cite as framing)
Unifying framework across 4 domains: math/theorem-proving (Lean/Isabelle), logical inference (FOL/LTL, **ASP/Prolog**), planning (PDDL), **KR (OWL/RDF/Situation+Event Calculus)** — both our targets (ASP + ontology) are first-class members. Framework = 4 primitives: informal language Li; formal language Lf (grammar/formation rules); **semantic equivalence criterion E**; **validation criterion V** (computable approximation of E). Our project instantiates ⟨Li=Model Spec prose, Lf=typed atoms+ASP, E=intended-behavior equivalence, V=solver conflict/coverage queries⟩. Use to argue ontology-targeted autoformalization is not fringe (reviewers equate autoformalization with Lean).

## 3. LLM ontology learning from normative text (2025-2026)
- **Ontology Generation using LLMs — arXiv:2503.05388** (Gangemi/Blomqvist/Nuzzolese et al.). Two prompt techniques: **Memoryless CQbyCQ** + **Ontogenia** (metacognitive prompting + Ontology Design Patterns) generate **OWL directly from user stories + competency questions**. 10 ontologies/100 CQs; o1-preview+Ontogenia meets engineer quality, beats novices. COPY: CQ-driven loop makes our Model-Spec ontology requirements-driven — write CQs ("can the assistant reveal system-prompt contents if the user asks?") that BOTH drive vocabulary AND double as solver coverage queries.
- **OntoLearner arXiv:2607.01977** (tooling scaffold); **RELRaE arXiv:2507.03829** (extract→refine→evaluate for relations); **VSPO arXiv:2511.07991** (CQs to validate semantic pitfalls).

## 4. Spec/constitution/policy → ontology or KG (BULLSEYE) — NO SCOOP
- **KG Representations for LLM-Based Policy Compliance Reasoning — arXiv:2604.27713** (Baldwin & Ghanavati). KG of compliance policies (EU AI Act, **OWASP LLM Top 10, NIST AI**, OPP-115); entity-relation extraction; compliance-QA over triples. NEAREST "AI-governance policy→graph" but NO typed vocab+axioms, NO defeasible/solver conflict analysis. MUST-CITE contrast. (Also the earlier-found "open LLM-discovered schema matches formal ontology on QA" caution comes from this line.)
- **Stress-Testing Model Specs arXiv:2510.07686** — confirmed purely empirical/inductive; finds Spec conflicts BEHAVIORALLY (divergence across 12 LLMs), never formalizes. The COMPLEMENT of us: they sample, we deduce.
- **Horner arXiv:2506.08899** (known) — legal→DDL w/ superiority relation = the conflict-resolution semantics we want; gap = apply to model spec + ontology front-end + coverage queries.

## 5. Neuro-symbolic propose→check→repair for ontologies
- **arXiv:2504.07640** — canonical loop: LLM output checked vs OWL ontology w/ **HermiT**; on inconsistency, **contradiction explanation fed back as refined prompt**. = our "escalation under a checker" verified. COPY repair-from-explanation; our deterministic+ASP checker is a cleaner/more decidable substrate than HermiT/OWL-DL.
- **arXiv:2604.00555** (ontology→OWL axioms, HermiT over agent output); **arXiv:2507.09751** (Sound+Complete Neurosymbolic Reasoning w/ LLM-grounded interpretations — cite if making checker correctness claims).

## 6. Faithfulness eval of ontology autoformalization
- **Ontology Learning: Axiom Identification benchmark — arXiv:2512.05594** (NEW, must-cite). Benchmarks LLM extraction of subClassOf/disjointWith/equivalence axioms vs ground truth, **separating legitimate from hallucinated axioms**. Most direct hallucinated-axiom-rate measurement. COPY the axiom-level precision/recall + hallucination framing for evaluating OUR composability axioms.
- **Do LLMs Game Formalization? — arXiv:2604.19459** — measures faithful vs "gamed" autoformalization; concrete failure taxonomy incl. **hallucinated axioms "such as survival obligations or harm assumptions introduced without grounding in source text."** Adopt as checker targets.
- **Text2KGBench** — faithfulness = Ontology Conformance (only predefined relations) + entity-existence-in-source. = our two-part checker enforcement (vocab-closure + source-groundedness).
- **DeFAb arXiv:2606.18557** — verifiable defeasible-abduction benchmark, for validating the defeasible-ASP layer.

---

## Bottom line
**(a) No scoop** of "spec/policy → queryable ontology with conflict analysis." Closest: 2604.27713 (policy→KG, compliance-QA, no defeasible solving), 2510.07686 (behavioral conflict-finding, no formalization), 2506.08899 (legal→DDL, not a spec, no ontology front-end). Our combination — typed atoms + composability axioms + defeasible ASP + deterministic checker + solver conflict/coverage on the OpenAI Model Spec — unoccupied. Position: deductively formalize what 2510.07686 finds empirically; add the ontology+coverage layer the policy→KG and legal→DDL lines each lack.

**(b) Three new must-cite:** 2604.02276 (De Jure — regulation→typed rule units, self-refine loop, EU-AI-Act validation), 2604.27713 (policy→KG contrast), 2512.05594 (hallucinated-axiom faithfulness metric). Runners-up: 2503.05388 (Ontogenia/CQbyCQ→coverage queries), 2504.07640 (reasoner-checked explanation-driven repair).

## Also confirmed this session (local artifact inspection)
OpenAI Model Spec is a STRUCTURED TAXONOMY, not a queryable ontology: 259 focus-area IDs `[^xxxx]` in model_spec.md, containment hierarchy (focus→section→5 top-level: chain_of_command/stay_in_bounds/style/seek_truth/best_work), 21 section anchors; eval dataset maps 596 prompts→225 focus IDs w/ rubrics. No typed entities/relations/axioms/logical semantics. = GIFT (adopt their 259 focus IDs as our clause layer + 596 prompts as behavioral cross-check), not a scoop.
