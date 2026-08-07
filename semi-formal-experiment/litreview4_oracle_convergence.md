# Literature Sweep 4: Oracle-Driven Convergence (2026-08-06)

*Fourth sweep. Sweeps 1–3 covered the **representation** axis (what a correct formalization is,
who else builds spec→ontology pipelines). This one covers the **algorithm** axis: given an
unreliable generator (an LLM call) and a human oracle, what procedure provably anneals an
initially-arbitrary formalization toward the target?*

**Explicitly OUT of scope (ruled out by design, 2026-08-06):** aggregation of unreliable agents
(von Neumann redundancy, majority vote, Dawid–Skene, Snorkel/data programming, debate,
self-consistency). Those buy reliability from *error independence*, and our own measurements
falsify that assumption locally — Haiku/Sonnet/Opus matched the human 4/4 on determinate
verdicts, and DeepSeek-V4-Flash's single divergence reproduced the **tool's** error direction
(`HUMAN_VS_MODEL_JUDGES.md`, this session). We are not building truth from correlated judges.
We are building a verifiable artifact refined by an oracle.

---

## 1. The frame: CEGIS / CEGAR / exact learning

- **CEGIS** (counterexample-guided inductive synthesis; Solar-Lezama). Generator proposes a
  candidate from a hypothesis space; verifier accepts or returns a **counterexample**;
  counterexample joins a permanent constraint set; repeat. **The guarantee does not depend on
  generator quality** — a biased generator changes the rate, not the limit, because each
  counterexample strictly shrinks the surviving hypothesis space. This is the formal content of
  "fine if the initial state is 100% weird DeepSeek logic."
- **CEGAR** (Clarke et al., 2000; 25-year retrospective collection at Springer). Counterexample-
  guided *abstraction refinement*: start coarse, and when a counterexample proves spurious,
  refine the abstraction **at the point that produced it**. This is the algorithm for our
  "long tail of representation" problem — refinement is targeted, not a global redraw.
- **Angluin exact learning / MAT** (1987). Membership + equivalence queries against a Minimally
  Adequate Teacher, provable convergence in polynomial queries. Our human oracle is the MAT.
- **CEGIS Modulo Theories** (Abate et al., CAV 2018) — the SMT-backed variant; relevant if the
  behaviour layer ever needs arithmetic/ordering rather than pure propositional+taxonomic.

### LLM-as-learner inside CEGIS
- **arXiv:2309.16436 — Neuro-Symbolic Reasoning for Planning: CEGIS using LLMs and Satisfiability
  Solving** (IEEE/FMCAD). Canonical placement of the LLM as the *learner* with a solver as the
  *teacher*. Cite as the architectural precedent.
- **arXiv:2605.16142 — Property-Guided LLM Program Synthesis for Planning.** LLM synthesizer +
  property checker; counterexample = failing state + heuristic values of successors. COPY the
  *shape of the counterexample payload* — ours should carry the failing passage, the derivation
  that failed, and the specific missing atom/edge.
- **Guiding Enumerative Program Synthesis with LLMs** (Springer, 10.1007/978-3-031-65630-9_15).
  Builds a **pCFG from the LLM's *incorrect* solutions** to steer an enumerative synthesizer —
  i.e. mines the generator's failures into search bias. Directly applicable to our 40%
  draw-dependent atom periphery.
- **arXiv:2606.11521 — Counterexample Guided Learning in the Large using Reasoning Agents.**
  Learner/teacher over accumulated counterexample sets; reflection + repair loops. Domain is
  regex induction. **No formal convergence claim** — empirical only (38.1%/74.1% vs 3.2%/38.9%
  single-shot). Cite as evidence the loop *works* with LLM learners; do not cite for guarantees.

## 2. ⭐ A named failure mode — prospectively relevant, but NOT our historical one

> **CORRECTION (2026-08-06, same day).** An earlier draft of this section claimed this failure
> explained our +0.0003 over six cycles. **Checked against `cycles/CYCLE_LOG.jsonl`: it does
> not.** Six cycles recorded five `keep` and one `revert`; the revert (patient-pricing) was a
> deliberate adjudication catch, not a silent regression. No cycle undid a prior cycle's fix.
> Our ceremony — frozen predictions, adjudicated flips, signed decisions, revert available —
> already supplies the monotonicity this section says LLM loops lack.
>
> The two failures share a symptom (loop doesn't improve) and differ in mechanism:
> theirs is *the generator forgets*, ours is *five kept changes each moved ≈0*. The latter is a
> **reachability/expressiveness** ceiling — the reasoning that decides our errors (multi-hop
> subsumption) is not expressible in the searched hypothesis space; see the `AXIOM_KINDS` /
> one-step-closure analysis. This section applies **prospectively** to any future loop with an
> LLM generator proposing vocabularies, and should not be cited for the historical number.

> *"In classical settings the generator is often symbolic or enumerative, so earlier
> counterexamples can be removed from the search space by construction. An LLM breaks that
> assumption. It can read counterexamples and try again, but it does not maintain a symbolic
> version space and can reintroduce an old failure in the next sample."*

**arXiv:2607.03656 — AutoCedar: An Agentic Framework for Verifier-Guided Access Control Policy
Synthesis (MUST-CITE, nearest architectural neighbour).** Natural language → Cedar policy via
generator/verifier/counterexample loop. Its stated contribution is keeping CEGIS discipline —
*every accepted candidate is checked against the full target* — while making explicit what the
LLM does not supply: **monotone elimination of prior failures.**

**COPY (for the future loop, not as a fix to the past):** a growing regression set of adjudicated
cases, checked in full on every candidate vocabulary/behaviour formula. Our cycle ceremony does
this per-cycle by hand; an LLM-generator loop would need it per-sample and automated.
**CAVEAT:** AutoCedar claims no convergence guarantee and has a machine verifier (Cedar's own
analyzer); our faithfulness verifier is the human, which is why §3 matters.

## 3. ⭐ Oracle design: pairwise, not absolute

**arXiv:2511.10855 — ExPairT-LLM: Exact Learning for LLM Code Selection by Pairwise Queries
(AAAI 2026, MUST-CITE).** Extends Angluin exact learning where the oracle is fallible.

Findings that transfer directly to our adjudication seat:
- Membership queries ("is this relevant?") need too many queries per item; equivalence queries
  ("is this formalization right?") are too hard to answer. **Both of our current seat designs are
  the infeasible ones.**
- **Pairwise queries are the tractable substitute**: *pairwise membership* (which of these two
  is more suitable for the task) and *pairwise equivalence* (are these two equivalent; if not,
  return a differentiating input).
- **Tolerates an imperfect oracle**: Theorem 5 gives probabilistic guarantees that the correct
  cluster wins the tournament whenever oracle accuracy **p > 0.5**. This answers the standing
  worry ("I don't know if I can evaluate the same items fairly twice") — the MAT assumption does
  **not** require a perfect human.
- **Differentiating inputs are validated by execution, not by trusting the oracle's word.**

**COPY, and it changes the seat:** stop asking Matt "is passage X relevant to behaviour B."
Ask "does behaviour B bear more on passage X or passage Y," and derive the constraint. Measure
his p on a held-back duplicate rather than assuming it.

## 4. Learning the formal artifact directly (ILP over ASP)

- **ILASP** (Law, Russo, Broda; arXiv:2005.00904 + manual). Learns ASP programs — normal rules,
  choice rules, hard **and weak** constraints — from positive/negative examples of partial answer
  sets, with **optimality guarantees** (shortest hypothesis). We already emit ASP (`emit_asp.py`,
  clingo dependency), so this is a drop-in candidate for *learning* the behaviour layer rather
  than prompting a model to write it. Weak constraints = a native home for the current
  `weight: 3/2/…` fields in `behavior_atoms.json`.
- **arXiv:2606.24245 — AutoSpec: Safety Rule Evolution for LLM Agents via Inductive Logic
  Programming (NEAR NEIGHBOUR).** ILP to evolve *safety rules* for agents. Closest thing to
  "learn the normative formalization from labelled behaviour." Check for scoop on the
  learning-the-rules framing; likely differs in that it governs agent actions, not document
  coverage.
- **arXiv:2606.03269 — Distilling ASP Rules from LLMs for Neurosymbolic VQA.** LLM→ASP rule
  distillation; Kareem et al. 2024 combine LLM + ILASP for commonsense rule induction from few
  examples.
- **arXiv:2510.07069** — inductive learning for possibilistic logic programs (if we ever want
  graded rather than boolean atoms).

## 5. ⭐ Reusable prior work on interpretive ambiguity (take it, don't re-derive it)

*Framing correction (2026-08-06): an earlier draft filed this as a "partial scoop." That is
publication-brain and the wrong question for a tool. The right questions are **what can we use
directly** and **what is the deficit**. Both are answered below.*

- **Statutory Construction and Interpretation for AI — PNAS 2026 / arXiv:2509.01186
  (MUST-CITE; partial scoop of Finding 4).** Formalizes **interpretive ambiguity as constrained
  entropy minimization over a set of reasonable interpreters**, then borrows legal safeguards:
  (a) a **rule refinement pipeline** that revises ambiguous rules to reduce interpretive
  disagreement (≈ agency rulemaking), and (b) prompt-based interpretive constraints (≈ canons of
  statutory construction). Both reduce entropy. Evaluated on 5,000 WildChat scenarios.

  **USE DIRECTLY — three components we do not have and should not rebuild:**
  1. **Entropy over interpreters as a targeting diagnostic.** Localizes *which* definitions are
     underspecified so refinement effort goes where it pays. ⚠️ **Asymmetric validity:** high
     entropy is a valid positive (definitely ambiguous); low entropy is an INVALID negative —
     correlated blind spots yield confident agreement on a shared misreading, which our own
     4-tier convergence demonstrates. Use to prioritize, never to certify.
  2. **The rule-refinement loop** (revise → re-measure → iterate), applicable to our three
     behaviour definitions as-is.
  3. ⭐ **Canons of statutory construction as a fixed interpretive policy.** *Ejusdem generis*,
     *noscitur a sociis*, *expressio unius*, conjunctive/disjunctive list canons. Our H002
     problem — does "avoiding both over- and under-caution" require both halves or either — is a
     textbook instance. Adopting a canon set gives a **public, stable, auditable resolution
     policy applied uniformly**, instead of resolving each ambiguity ad hoc per definition
     (Sonnet resolved AND on H002 and OR on H005 within one run). Strictly better than what we
     had planned, and more defensible under audit.

  **DEFICIT — why it is not sufficient on its own:**
  - Output is **revised prose**. Nothing to ablate, no consistency check, no coverage query, no
    "what would flip this decision."
  - **Different output object.** They improve model behavioural consistency across WildChat
    scenarios; we compute document coverage per section×behaviour. Their pipeline does not
    produce a coverage map, which is the thing our tool exists to emit.
  - Entropy cannot certify (see 1 above); no convergence/retention procedure.

  **Overlap is smaller than first assessed:** their unit is model behaviour on prompts, ours is
  judges scoring passage relevance. Their result strongly *predicts* our Finding 4 rather than
  preempting it. Cite as support and as a source of components; the artifact and the coverage
  output remain ours.
- **arXiv:2605.24247 — Improving Labeling Consistency with Detailed Constitutional Definitions
  and AI-Driven Evaluation.** More detailed constitutional definitions → better labeling
  consistency. Same warning: the "specify the definition, kappa improves" experiment is occupied.
- **arXiv:2603.06974 — Elenchus: Generating Knowledge Bases from Prover–Skeptic Dialogues.**
  Adversarial dialectic as KB construction; relevant alternative to solver-as-teacher.
- **arXiv:2605.11315 — Natural Language based Specification and Verification.** NL specs as a
  practical verification layer; explicitly *not* a substitute for formal contracts.

## 6. ⭐⭐ The hypothesis-representation question — DO NOT BUILD THIS, IT EXISTS

*Added 2026-08-06 after the question "what is the complete set of hypothesis actions, and isn't
this off-the-shelf?" The answer is yes, three times over, and we were about to hand-roll an
edit-type enum badly.*

**The named concept is `language bias` / `mode declarations`.** In ILP you do not enumerate edit
operations; you declare which literals may appear in a learned rule — `#modeh(r, atom)` for heads,
`#modeb(r, atom)` for bodies, with abstracted arguments `var(t)` / `const(t)` for type `t` — and
the learner searches the space that bias defines. ILASP's mode bias *is* the hypothesis-space
specification, and ILASP compiles the induction task into a **meta-level ASP program whose optimal
answer sets are the inductive solutions**. We already depend on clingo; this is clingo.
Ref: *ILP at 30: A New Introduction* (arXiv:2008.07912) for the syntactic/semantic bias taxonomy.

- ⭐ **arXiv:2505.21486 — Hypothesis Generation via LLM-Automated Language Bias for ILP
  (MUST-CITE).** LLM proposes the language bias; ILP searches it. This is precisely the
  "inexpensive hypothesis about formal representation" loop we identified as the bottleneck,
  already built. Read before writing any proposal schema.
- **Belief revision for ASP** (Delgrande, Schaub, Tompits, Woltran; KR 2008 + TPLP). Expansion /
  revision / contraction over logic programs with AGM-style postulates, semantic (SE-model /
  HT-model based) rather than syntactic, **with an encoding that computes the revision of a logic
  program inside the same logic-programming framework** — i.e. in clingo, no new engine.
  This is the principled version of "changes to our DSL."
- **Flouris et al., Ontology Change: Classification and Survey** (Knowledge Engineering Review
  2008) — canonical taxonomy: 11 change tasks, change operators as building blocks, plus
  pattern-based layered operator frameworks. Use instead of a hand-written edit enum.

### ⚠️ Root cause this exposes: our DSL is PROPOSITIONAL, our hypotheses are RELATIONAL

`dsl.Atom` = name + kind + dimension + gloss (no arguments). `dsl.Axiom` ranges over atom *names*.
`emit_asp.py` emits `ctx(atom_name)` — a single predicate over constants. **We own clingo and use
it as a propositional engine.**

A hypothesis like *"has an implied impact on an unnamed party"* needs an argument slot (which
party) and a modality (implied vs. stated). It is not expressible as a propositional atom, so it
must be *encoded in code* — which is why one such hypothesis costs ~8 iterations and days of work
to discover it moves the metric ~0.001. Same ceiling explains the missing `is_a(child, parent)`:
subsumption is relational too. **Two symptoms, one cause.**

Relational form makes it a declaration plus an extractor:

```
#modeb(1, implied_impact(var(party))).      % (a) how the DSL operates
#modeb(1, unnamed(var(party))).
```
plus (b) one cheap per-passage extraction call ("does this passage imply an impact on a party not
named in it? return party type + deciding span"). 589 passages on V4-Flash ≈ **$0.60**, minutes,
then re-run the existing evaluation. Cost of a negative result drops from ~a week to under a
dollar — which is the stated goal.

**COPY:** move the atom layer from propositional constants to typed ASP predicates; express the
hypothesis space as mode declarations rather than a bespoke edit enum; let an LLM propose bias +
do extraction; keep clingo/ILASP as the search and the checker.
**NOT off the shelf:** the text→predicate-instance extraction step (domain-specific; that is the
LLM's job) and the glue to our existing evaluation harness.

## 7. Gaps found (searched, not found)

- **CEGAR applied to ontology/vocabulary refinement with an LLM** — no hits. The refinement
  literature is about *program abstractions*; the ontology literature does propose→check→repair
  (litreview3 §5) but **without** the targeted-refinement-from-spurious-counterexample discipline
  or any monotonicity claim.
- **Convergence guarantees for LLM-assisted ontology/KB refinement with a human oracle** — no
  hits; the ESWC LLM4KGOE 2026 workshop line and the ontology-engineering SLR are qualitative.
- **CEGIS applied to a model spec / AI constitution** — no hits. AutoCedar is access-control
  policy; statutory-construction work is prose refinement without a formal artifact.

---

## Bottom line

**(a) The frame is well-established and we were not using it.** CEGIS/CEGAR/exact-learning give
exactly the property asked for: provable annealing from an arbitrary start, with the generator's
bias affecting rate only. Our loop currently violates its central requirement.

**(b) One prospective requirement, not a retrodiction.** LLM generators supply no version space
(AutoCedar), so any future loop with a model proposing vocabularies must bank counterexamples as
constraints checked on every sample. **This does NOT explain the historical +0.0003** — the cycle
log shows five `keep`, one deliberate `revert`, no silent regressions, i.e. monotonicity already
holds. The historical number is a **reachability** failure: multi-hop subsumption is not
expressible in the searched space, so each kept change could only move ≈0.

**(c) One must-change, with a theorem behind it.** ExPairT-LLM: absolute membership/equivalence
queries are the infeasible ones; **pairwise** queries are tractable and tolerate an oracle with
p > 0.5. Redesign the adjudication seat accordingly, and measure the human's p rather than
assuming it.

**(d) One candidate replacement for the generator.** ILASP learns ASP with optimality guarantees
from exactly the example format we already have. Consider learning the behaviour layer instead of
prompting for it — or at minimum use ILASP as the check on a prompted hypothesis.

**(e) Three components to adopt off the shelf.** From PNAS/arXiv:2509.01186: entropy-over-
interpreters as an ambiguity *targeting* diagnostic (valid as a positive only), the rule-
refinement loop, and — highest value — **canons of statutory construction as a fixed, auditable
interpretive policy** in place of ad-hoc per-definition resolution. Their deficit is that the
output is prose and the output object is behavioural consistency, not document coverage. Taking
their components costs us nothing and removes work we had scheduled.

**(f) Still unoccupied:** counterexample-guided *refinement of a typed vocabulary + defeasible
ASP layer* for a real model spec, with retained constraints and a human MAT. That is the
combination to claim.
