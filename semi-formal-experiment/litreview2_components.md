# Literature Sweep 2: Component-Level Prior Art (2026-07-30)

*Second deep-research pass, scoped to components we might be missing (first pass: litreview.md). Verification legend: **[V]** = claim checked against fetched abstract/page; **[S]** = existence + venue verified via search only.*

---

## 1. OpenAI Model Spec specifically

### OpenAI, "Introducing Model Spec Evals" + `openai/model_spec_evals` repo (Mar 25, 2026) **[V]**
- https://alignment.openai.com/model-spec-evals/ ; https://github.com/openai/model_spec_evals
- OpenAI's own adherence suite: 596 scenario prompts covering **225 "concrete focus areas"** spanning all policy sections, each prompt targeting one "load-bearing clause" with a per-prompt rubric. Graded by GPT-5 Thinking on a 1–7 scale, 5 samples, median binarized at ≥6; runs on Inspect AI. Explicitly text-only, non-adversarial, "low-resolution" coverage; **no formal parsing of the spec into assertions/atoms** — clause selection and rubric writing are manual+model-assisted prose.
- **Copy/avoid:** Copy their 225 focus-area clause inventory as a free, OpenAI-endorsed segmentation of the Spec to seed and cross-check our atomization; avoid their coverage model (representative examples per clause, no satisfiability/conflict machinery — exactly our gap).

### Guan et al., "Deliberative Alignment," arXiv:2412.16339 **[V]**
- Trains o-series models to quote and reason over safety-spec *text* in CoT before answering; SFT data auto-generated from specs + RL with a spec-aware reward model. Treats the spec as retrievable prose, not structure.
- **Copy:** the "cite the governing clause in reasoning" pattern for provenance strings.

### Jakkli, Rajamanoharan & Nanda, "How Well Do Models Follow Their Constitutions?", arXiv:2605.24229 (May 2026) **[V]**
- Decomposes Anthropic's constitution into **205 atomic tenets** and the OpenAI Model Spec into **197 tenets**, audits via Petri multi-turn adversarial agents + SURF-style rubric search. Violations fall across generations (Sonnet 4: 15.0% → Sonnet 4.6: 2.0%; GPT-4o: 11.7% → GPT-5.2: 3.6%); persistent failures cluster on operator personas, irreversible agentic actions, fabricated quantitative claims. **No solver, no typing, no composability axioms** — tenets are prose rubrics.
- **Copy/avoid:** Closest prior atomization of *both* target specs — obtain their tenet lists as baseline; differentiate explicitly (typed atoms + defeasible semantics + solver queries vs. flat prose tenets).

### Zhang et al., "Many-Tier Instruction Hierarchy in LLM Agents" (ManyIH), arXiv:2604.09443 **[V]**
- Argues the Spec's fixed ~5-level authority ladder is inadequate; ManyIH-Bench (853 tasks, up to 12 conflicting levels); frontier models drop to ~40% accuracy as conflict depth scales.
- **Copy:** authority ordering must be a first-class, *variable-depth* parameter in the ontology — don't hardcode 5 tiers. Benchmark = external validity test for conflict-resolution outputs.

Also **[S]**: OpenAI "Inside our approach to the Model Spec" (403-blocked, read manually); GovAI "Transparency into Model Spec Adherence" (motivation-section material); "Case-Augmented Deliberative Alignment," arXiv:2601.08000.

---

## 2. Controlled-vocabulary / ontology-constrained generation

- **Grammar-Constrained Decoding for logical parsing**, ACL 2025 Industry **[S]** — GCD guarantees syntax; **semantic errors persist** (their own headline caveat). Copy GCD only for DSL surface syntax; our deterministic checker is the layer they name as missing — cite to justify.
- **Flexible/Efficient GCD** arXiv:2502.05111 **[S]**; **Grammar Prompting** arXiv:2305.19234 **[S]** — grammar-in-prompt + post-hoc checker likely sufficient; avoid constrained-decoding engineering unless error rates demand it.
- **OntoLogX** arXiv:2510.01409 **[S]**; **ODKE+** arXiv:2509.04696 **[S]** — validate→targeted-repair-prompt→revalidate loop; "ontology snippet" trick (show the LLM only the vocabulary slice relevant to the clause being translated). Copy both.
- **Vocabulary-extension escalation:** CEUR Vol-4020, PMC11491333 (online clustering extension), NeurOWL arXiv:2607.15776 (HermiT inconsistency explanations re-prompt the LLM) **[S]** — pattern exists but thin. **No published "LLM proposes typed atom → checker rejects → escalation tier decides" protocol for normative specs. Genuinely open — claim explicitly.**

---

## 3. LLM → ASP

- **Ishay, Yang & Lee**, KR 2023, arXiv:2307.07699 **[S]** — canonical NL→clingo pipeline; **predicate-inventory-first prompting dominates one-shot translation** (matches our atoms-then-rules split); residual errors simple, fixable via error-message feedback.
- **Ishay & Lee**, "LLMs as ASP Programmers: Self-Correction...", arXiv:2604.27960 **[V]** — three findings to copy: (1) **ASP stable-model semantics significantly outperforms SMT on defeasible/exception-heavy reasoning** (empirical support for ASP-over-SMT); (2) solver-feedback self-correction is the primary performance driver; (3) *compact* reference guides beat verbose documentation ("context rot") — keep the DSL reference card short.
- **LLASP**, KR 2024 **[S]** — fine-tuned lightweight ASP generator; fallback if API-model error rates force it.
- **PROLEG line**: arXiv:2601.01477, arXiv:2311.04911 **[S]** — expert-in-the-loop validation tiers, "rule + exception-slot" idiom; avoid PROLEG machinery itself.
- **nl2spec** (Cosler et al., CAV 2023, arXiv:2303.04864) **[S]** — **sub-translations**: LLM maps each subformula back to its NL fragment; users edit the sub-translation table, not the formula. Copy wholesale — per-atom provenance doubles as the correction UI.

---

## 4. Interactive concept/definition refinement

- **EvalGen** (Shankar et al., UIST 2024, arXiv:2404.12272) **[S]** — **"criteria drift"**: users need criteria to grade, but grading changes their criteria; stable criteria may not exist a priori. Design consequence: expect users' interpretations to shift as they see solver witnesses → version DSL translations, make re-validation cheap, no one-pass sign-off.
- **Interactive Weak Supervision** (Boecking et al., ICLR 2021, arXiv:2012.06046) **[S]** — machine proposes, human vetoes; per-rule feedback converges in few iterations.
- **Policy Maps** arXiv:2409.18203, **PolicyCraft** CHI 2025 arXiv:2409.15644, **PolicyPad** 2026 **[S]** — HCI line on authoring LLM policies; **case-grounded deliberation**: humans converge on policy wording via concrete cases → pipe solver witnesses into the validation UI, don't show abstract rules alone.
- Also: MetricMate (CHIWORK '25), interactive machine teaching (Ramos et al. 2020).

---

## 5. Norm conflict detection in NorMAS

- **Vasconcelos, Kollingbaum & Norman**, JAAMAS 2009 **[S]** — conflict = non-empty intersection of constrained instantiation sets, via unification + constraint solving; resolution by variable-scope curtailment (a principled repair suggestion to emit alongside witnesses).
- **Santos et al.**, JAAMAS 2017 survey (10.1007/s10458-017-9362-z) **[S]** — direct vs. **indirect** conflicts; indirect conflicts need domain axioms relating distinct actions → our composability axioms play exactly this role; cite to position.
- **Olson et al.**, DDIC, KR 2024, arXiv:2407.04869 **[S]** — defeasible deontic calculus unifying NorMAS resolution strategies; theoretical anchor for defeasible-rule-per-clause; check which common strategy they debunk before hardcoding precedence.
- **Gap confirmed:** no modern grounder/solver over typed scenario spaces with minimal witnesses for an LLM-era spec.

---

## 6. Ontology quality + competency-question automation (2024–2026)

- **Bench4KE** arXiv:2505.24554 (CQ gold standard, 17 projects, 6 systems compared); **RAG CQ generation** arXiv:2409.08820 (generate CQs from the spec text itself); **VSPO** arXiv:2511.07991 (adversarial CQs targeting semantic pitfalls); arXiv:2504.17402, arXiv:2412.13688, **OntoURL** arXiv:2505.11031. All **[S]**.
- **Avoid:** LLM-as-ontology-judge without gold grounding — the field built benchmarks precisely because free-form LLM evaluation is unreliable.

---

## 7. Near-scoops (2025–2026 compositions)

- **Winston, Winston & Just**, "Solver-Aided Verification of Policy Compliance in Tool-Augmented LLM Agents," arXiv:2603.20449 **[V]** — *closest single composition*: LLM-assisted, human-guided NL tool-policies → SMT-LIB, Z3 blocks violating tool calls at runtime. Differentiate: runtime enforcement vs. spec-level static analysis with witnesses; ASP-vs-SMT (2604.27960 = ammunition).
- **Prose2Policy** (Apple, 2025/26) **[S]** — NL access policies → Rego with staged validators (schema → lint → compile → auto-tests). Industrial template for the checker chain.
- **C-Trace**, arXiv:2606.19242 **[V]** — GDPR predicates over agent traces; ≤12% attack success at ≤16% FP under 10% extraction noise, 0% under perfect extraction. **Key number: LLM fact-extraction is the reliability bottleneck of any NL→formal pipeline — budget error analysis there.**
- **Baldwin & Ghanavati**, arXiv:2604.27713 **[V]** — policy docs → KGs; **open LLM-discovered schema matches or exceeds formal ontology** on QA tasks. Caution: fixed vocabulary must earn its keep; our answer = solver queries (LLM-discovered schemas can't support satisfiability/conflict). Say so explicitly.
- **MAC**, arXiv:2603.15968 **[V]** — multi-agent constitutional rule *discovery* (inverse direction); accept/edit/reject agent roles usable for translation-repair stage.
- Also **[S]**: AgentLTL arXiv:2607.02599, LogiSafetyGen arXiv:2601.08196, ARPaCCino arXiv:2507.10584, AgenticRei (gray literature).

---

## Scoop check: verdict

**No direct scoop.** Nothing composes the full pipeline (typed vocabulary + axioms + defeasible ASP rules + deterministic checker + LLM clause/behavior translation + solver conflict/relevance/coverage queries with witnesses + tiered human validation) for a model spec. Three works to cite and pre-empt:

1. **arXiv:2605.24229** — already atomized both target specs (205 + 197 prose tenets); no typing/logic/solver. Must cite; reuse or explicitly improve on the tenet inventory.
2. **arXiv:2603.20449** — LLM-assisted human-guided policy→solver, but runtime SMT enforcement, not static conflict analysis; ASP>SMT on defeasible reasoning per 2604.27960.
3. **OpenAI Model Spec Evals** — official 225-focus-area segmentation + 596 prompts; behavioral only. Best seed data + clearest "what's missing" foil.

Genuinely open sub-components (no published treatment found): (a) escalation protocol for LLM-proposed vocabulary extensions under a deterministic checker; (b) minimal-witness conflict/coverage queries over typed scenario spaces for normative specs; (c) formal treatment of the Model Spec's defeasibility markers ("by default," "unless," root-level overrides) as first-class solver objects.
