# Literature Review: Formal Verification of AI Model Specifications for Conflict Detection

*Deep-research report, 2026-07-30. Question: can deontic/defeasible logic + SAT/SMT/ASP machinery find internal conflicts in AI model specs (Claude's Constitution, OpenAI Model Spec) — e.g. around "faithfulness to the user" — and turn them into evals? All key claims verified against fetched abstracts/pages, not just search snippets.*

---

## Thread 1: Stress-testing model specs (the closest prior work)

### Zhang et al. 2025 — "Stress-Testing Model Specs Reveals Character Differences among Language Models"
- **Citation:** Jifan Zhang (Anthropic Fellows), Henry Sleight (Constellation), Andi Peng (Anthropic), John Schulman (Thinking Machines), Esin Durmus (Anthropic). arXiv:2510.07686, Oct 2025. Blog: [alignment.anthropic.com/2025/stress-testing-model-specs](https://alignment.anthropic.com/2025/stress-testing-model-specs/); [arXiv](https://arxiv.org/abs/2510.07686).
- **Method:** Built on a taxonomy of 3,307 fine-grained values extracted from natural Claude traffic ("Values in the Wild" lineage). Generated **300,000+ synthetic scenarios** forcing explicit tradeoffs between pairs of legitimate principles that cannot be simultaneously satisfied (e.g., "social equity" vs. "business effectiveness"; "assume best intentions" vs. safety restrictions). Ran 12 frontier models (Anthropic, OpenAI, Google, xAI). Scored each response on a 0–6 "value spectrum rubric"; **disagreement = std. dev. of value scores across models**.
- **Findings:** >220k scenarios show meaningful cross-model disagreement; >70k show large divergence. High disagreement strongly predicts spec problems: for five OpenAI models judged against the published Model Spec, high-disagreement scenarios show **5–13× higher rates of frequent spec violations** (all models violating their own spec). Documented direct contradictions and interpretive ambiguities; LLM judges applying identical spec criteria only reached **kappa = 0.42**. Found misalignment cases and false-positive refusals in every frontier model.
- **Relevance:** This substantially occupies the "generate conflict scenarios → measure divergence → attribute to spec defects" territory — *behaviorally*. Critically, the method is **entirely LLM-driven** (taxonomy sampling + generation + LLM judging). No formalization, no solver, no exhaustive or provable conflict enumeration, no deontic structure. Conflicts are surfaced statistically (disagreement as a symptom) rather than derived (contradiction as a theorem). That's the seam the proposed project would occupy — but it sets a high bar: any formal pipeline must find conflicts this method misses, or characterize/verify conflicts it can only gesture at.

### Adjacent adherence/conflict evals
- **SpecEval** — Ahmed, Klyman, Zeng, Koyejo, Liang (Stanford). arXiv:2509.02464, NeurIPS 2025. Parses provider specs into behavioral statements (OpenAI 46, Anthropic 49, Google/Sparrow 23), TestMaker LM generates probing prompts, Judge LM scores; audits 16 models from 6 providers for **three-way consistency** (spec ↔ model output ↔ provider's own model as judge). Finds compliance gaps up to ~20%. **Audits adherence to individual statements only; does not analyze intra-spec conflicts.**
- **IHEval** ([arXiv:2502.08745](https://arxiv.org/pdf/2502.08745)) and **"Reasoning Up the Instruction Ladder"** ([arXiv:2511.04694](https://arxiv.org/html/2511.04694v5)): instruction-hierarchy conflict evals (system vs. developer vs. user). All models degrade notably in conflict settings. These formalize *priority between tiers*, not conflicts *among same-tier normative principles*.

---

## Thread 2: SLEEC rules and tooling — the most transferable formal machinery

- **SLEEC framework (Calinescu et al., York/Toronto):** Social, Legal, Ethical, Empathetic, Cultural requirements as a DSL: `when <trigger> then <response> [unless <defeater>] [within <deadline>]` — defeasible rules with temporal constraints, designed for non-technical stakeholders (lawyers, ethicists).
- **SLEECVAL / tock-CSP toolchain:** Getir Yaman, Ribeiro, Burholt, Jones, Cavalcanti, Calinescu, "Specification, validation and verification of SLEEC requirements for autonomous agents," *JSS* 2024 ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0164121224002735)). Translates SLEEC to tock-CSP, uses the FDR refinement checker for conflict and redundancy detection, plus agent-compliance verification.
- **LEGOS-SLEEC (current state of the art):** Kolyakov, Marsso, Feng, Quan, Chechik (U. Toronto), [arXiv:2501.12544](https://arxiv.org/html/2501.12544v1) (tool paper; underlying analysis at ICSE 2024, "Analyzing and Debugging Normative Requirements via Satisfiability Checking"). Translates SLEEC to **FOL\* (first-order logic with relational objects)**, satisfiability checking with **five well-formedness checks: vacuous conflict, situational conflict, redundancy, overly restrictive rules, insufficiency**, minimized diagnostics from UNSAT proofs. Case studies: assistive robots, firefighting drones, healthcare monitors, driver-attentiveness systems (~25 measures each).
- **SLEEC × LLM:** Feng, Marsso et al., "Normative Requirements Operationalization with Large Language Models," RE 2024 ([arXiv:2404.12335](https://arxiv.org/abs/2404.12335)) — LLMs extract semantic relations between rule concepts to help operationalize SLEEC rules. Newer ASM-based work at ABZ 2026 ([Springer](https://link.springer.com/chapter/10.1007/978-3-032-26752-8_9)).
- **Key gap check (verified):** **No SLEEC work applies the machinery to LLM model specs or constitutions.** All targets are cyber-physical/robotic systems with small (~10–30) rule sets. LLMs appear only as extraction aides.
- **Relevance:** Best off-the-shelf substrate: an existing DSL with defeaters, a maintained solver (LEGOS), and exactly the conflict taxonomy needed (situational conflict = "there exists a scenario triggering contradictory obligations" — the SAT witness *is* the eval-scenario skeleton).

---

## Thread 3: LLM autoformalization of normative text

- **Horner, Mateis, Governatori, Ciabattoni, "Toward Robust Legal Text Formalization into Defeasible Deontic Logic using LLMs"** ([arXiv:2506.08899](https://arxiv.org/abs/2506.08899), 2025). Pipeline: segment normative text into atomic snippets → extract deontic rules → coherence checks → refinement stage. Evaluated on the Australian Telecommunications Consumer Protections Code vs. expert-crafted DDL. Guided LLMs "align closely with expert-crafted representations." Governatori is the DDL/SPINdle lineage, so output is solver-ready. Strongest evidence spec-clause → DDL formalization is feasible today.
- **"GDPR Auto-Formalization with AI Agents and Human Verification"** — Nguyen, Fungwacharakorn, Wehnert, Araszkiewicz, Goebel, Satoh et al. ([arXiv:2604.14607](https://arxiv.org/html/2604.14607), 2026). Drafter agent + four verifier agents + human-in-the-loop, targeting "Pythen." Sobering: of 400 samples passing automated verification, humans kept only 120; recurring errors were **abstraction-choice errors invisible to automated checks**. Full autonomy inappropriate; verification-centered pipelines required.
- **"Know Your Limits: On the Faithfulness of LLMs as Solvers and Autoformalizers in Legal Reasoning"** ([arXiv:2606.16118](https://arxiv.org/abs/2606.16118), 2026). Compares pure LLM classification, LLM-simulated formal reasoning, and Z3-grounded reasoning on re-annotated ContractNLI. Accuracy gains from formal structure "do not imply faithful reasoning": documents **scope laundering** (model reports conclusions inconsistent with its own solver), **implicit constraint blindness**, Z3 synthesis failures. Caution: an LLM-formalized spec + solver can still launder the LLM's priors through formal veneer.
- **Inter-formalizer agreement:** No dedicated large study on normative text found. Closest: kappa=0.42 judge agreement (Zhang et al.), low annotator agreement on open-texture identification (AI&Law 2025), and the legal-theoretic point that "there may not be a uniquely correct formalization" ([arXiv:2508.18880](https://arxiv.org/html/2508.18880v2)). **An inter-formalizer agreement study over a model spec would itself be a novel, cheap contribution** — doubling as a per-clause ambiguity detector.

---

## Thread 4: Legal-informatics conflict-detection machinery

- **Defeasible Deontic Logic solvers:** **SPINdle** (Lam & Governatori 2009) — mature propositional defeasible reasoner, scales to millions of facts; **Turnip** — modern CSIRO-lineage DDL, **propositional only**; ASP-based temporal deontic compliance checking (Giordano et al., ICAIL 2013). Model spec clauses are heavily first-order/contextual, so propositional solvers force aggressive grounding — LEGOS's FOL\* or ASP are better fits.
- **LegalRuleML + DAPRECO:** Robaldo, Bartolini, Palmirani et al., "Formalizing GDPR Provisions in Reified I/O Logic: The DAPRECO Knowledge Base," *JLLI* 2020. Largest free LegalRuleML/I-O-logic KB; proof a real messy regulation of comparable scale can be fully hand-formalized — and how labor-intensive (years, expert team).
- **Catala:** Merigoux, Chataing, Protzenko, ICFP 2021 ([arXiv:2103.03198](https://arxiv.org/abs/2103.03198)). Default logic (general rule + exceptions) as core semantics; lawyers pair-programmed with programmers; deployed with French DGFiP. Default-with-exceptions maps well onto model-spec prose ("be helpful, unless...").
- **SMT-based contract consistency:** ContractCheck ([arXiv:2212.03349](https://arxiv.org/pdf/2212.03349)); "Automated Consistency Analysis for Legal Contracts" (*AI&Law* 2025; [arXiv:2504.18422](https://arxiv.org/pdf/2504.18422)): encode clause preconditions/constraints in decidable FOL fragments, SMT + UNSAT cores prove existence of conflicting clauses with diagnostics. The exact "solver finds contradiction, core explains it" loop — applied to share-purchase agreements, never to AI specs.
- **LogiKEy:** Benzmüller, Parent, van der Torre, *AIJ* 2020 ([arXiv:1903.10187](https://arxiv.org/pdf/1903.10187)) — shallow embeddings of multiple deontic logics in Isabelle/HOL, automated consistency checks. Heaviest-duty; best for small, deep formalizations of a few clauses.
- **Deontic temporal logic + Z3 for AI ethics:** Priya T.V. & Shrisha Rao ([arXiv:2501.05765](https://arxiv.org/html/2501.05765v4), 2025): deontic+temporal axioms for fairness/explainability checked with Z3 (COMPAS, loan model). Verifies *system behavior against hand-written principles*; does not formalize any real published AI-company document — that niche is open.

---

## Thread 5: Formalizing constitutions / model specs specifically

- **C3AI** — Kyrychenko, Zhou, Bogucka, Quercia, WWW 2025 ([arXiv:2502.15861](https://arxiv.org/abs/2502.15861)). Selecting/structuring constitutional principles pre-fine-tuning, evaluating adherence after. Humans prefer positively framed, behavior-based principles, but CAI models follow negatively framed ones better. Empirical/psychometric, **no logic**.
- **Anthropic's constitution (Jan 2026)** explicitly acknowledges internal tensions, reasons-over-rules design; commentary ([BISI](https://bisi.org.uk/reports/claudes-claudes-constitution-ai-alignment-ethics-and-the-future-of-model-governance), [aigl.blog](https://www.aigl.blog/claudes-constitution/)) notes enforcement is implicit and principle-to-risk mapping absent. Anthropic-adjacent validation practice = multiple frontier LLM judges on production traffic, disagreement to localize ambiguous sections — statistical, not formal.
- **"The Specification Trap"** — Spizzirri ([arXiv:2512.03048](https://arxiv.org/pdf/2512.03048)): static specs can't resolve genuine value conflicts; comprehensive formalization risks oversimplification. Useful foil: the project doesn't need formalization to *resolve* conflicts, only to *enumerate and localize* them — a weaker, defensible claim.
- **Verified negative result:** ~15 targeted searches found **no published work formalizing the OpenAI Model Spec or Claude's Constitution into any machine-checkable logic**, and no solver-based consistency analysis of either document.

---

## Thread 6: Critiques and the LLM-as-analyst alternative

- **Open texture:** "Identifying open-texture in regulations using LLMs," *AI&Law* 2025 — even human annotators show low agreement on what counts as open-textured. Model specs are *deliberately* open-textured, so any formalization is one interpretation among several (Hart/Bench-Capon line).
- **"Challenges for Generative AI in Legal Reasoning"** ([arXiv:2508.18880](https://arxiv.org/html/2508.18880v2)): general clauses require extra-legal judgment; no uniquely correct formalization; competing formalizations can both be reasonable.
- **Synthesis:** LLM methods find symptoms at scale but can't prove anything or guarantee coverage; formal methods prove and enumerate but only relative to a contestable formalization. **No work closes this loop in either direction for model specs.**

---

## Novelty Assessment

**Already done (don't re-do):**
1. LLM-generated conflict-scenario stress-testing of real model specs at massive scale, divergence-as-defect-detector, documented contradictions (Zhang et al. 2025 — Anthropic-affiliated).
2. Behavioral adherence auditing against parsed spec statements (SpecEval).
3. Solver-based conflict/redundancy detection over defeasible normative rules — but only for robots/CPS (LEGOS-SLEEC) and contracts (ContractCheck).
4. LLM pipelines producing near-expert DDL from real regulatory codes (Horner et al.), with documented failure modes and need for human verification.

**Open gap (verified — nobody has done this):**
**Solver-based, exhaustive, explainable conflict enumeration over a real published model spec.** Concretely: formalize the "faithfulness-to-user" cluster (honesty, helpfulness, autonomy-respect, non-manipulation) of Claude's Constitution and/or the OpenAI Model Spec into a defeasible/deontic formalism (SLEEC DSL + LEGOS, or DDL + SPINdle/Turnip, or ASP), run situational-conflict/redundancy/insufficiency checks, and use SAT witnesses / UNSAT cores as *seeds for behavioral evals*. Every component exists; the composition does not.

**Differentiators vs. Zhang et al. (the bar to clear):**
- *Completeness within a fragment:* solver enumerates **all** conflicting trigger-combinations under the formalization, vs. sampling 300k scenarios and finding symptoms. "These 14 clause-pairs are jointly unsatisfiable under interpretation I" is a claim they cannot make.
- *Explainability:* UNSAT cores name the exact clauses in tension; Zhang et al. attribute post hoc via LLM analysis.
- *Cheap regression checking:* re-run when the spec is revised (Anthropic revised Jan 2026; OpenAI revises repeatedly) — a spec-CI story nobody offers.
- *The formalization-ambiguity study is itself a contribution:* N independent formalizers per clause; divergence quantifies open texture per clause — no such study exists for any AI spec.

**Main risks:**
- Open texture: every discovered "conflict" is conditional on interpretation; critics will say LLM stress-testing already found the important ones. Mitigation: close the loop into behavioral evals (solver witness → concrete scenario → measure model divergence), so the end product is validated the same way Zhang et al.'s is.
- Formalization fidelity: abstraction errors and unfaithful hybrids are the dominant failure mode (GDPR-agents, Know Your Limits); budget for human verification of a small fragment (one value-cluster, ~20–50 rules — LEGOS-SLEEC's demonstrated regime).
- Propositional solvers force lossy grounding; prefer LEGOS's FOL\* or ASP.

**Bottom line:** The behavioral-divergence half is taken (well executed, Anthropic-affiliated). The formal half — deontic/defeasible formalization of a real model spec with solver-certified conflict enumeration, closing the loop into evals and comparing head-to-head against LLM-only stress-testing — is genuinely unoccupied, has all tooling prerequisites published, and has an obvious baseline to compare against.
