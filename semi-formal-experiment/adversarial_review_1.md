# Adversarial review 1 of blog draft (clean-context agent, 2026-07-30)

Reviewer re-ran both scripts, audited segmentation JSON + rules.lp against the post, read constitution text, fact-checked 13 citations. Findings below verbatim from the reviewer, lightly formatted. Post reviewed: mattstults.github.io/_drafts/2026-07-30-semi-formal-spec-conflicts.md

## Critical findings

**6. Flagship conflict built from clauses the segmentation tags non-formalizable.** Wellbeing clause (c056) and Autonomy clause (c054) — the two quoted in the worked example — are both tagged `holistic` in constitution_clauses.json, while the post says only `conditional` clauses formalize. Internal contradiction: either segmentation is wrong (undermines 31.7% + boundary) or worked example is out-of-scope for the pipeline.

**7. The constitution arguably resolves the flagship conflict — in clause c317 (tagged `conditional`), absent from the fragment.** c317: "Personal autonomy: Claude should respect the right of people to make their own choices and act within their own purview, even if this potentially means harming themselves or their interests." Near-explicit defeater: autonomy dominates wellbeing-intervention for self-regarding decisions. Supporting: c057 ("without being paternalistic"), c068 (paternalism "disrespectful"), c127 (names the balance). The "same-tier unresolved" verdict is an artifact of fragment selection — the failure mode the full pipeline would systematically produce whenever the resolving clause lives in a different section. Fix: encode c317 as defeater, show the conflict DISSOLVING (a better demo), and add limitation: an enumerated "unresolved conflict" is only as trustworthy as fragment completeness.

**19. The determinism is laundered judgment (strongest unanswered objection).** Every reported conflict is downstream of nondeterministic encoding choices: clause selection (finding 7), modality assignment ("give weight" → "oblige", finding 8), act individuation + incompat axioms (finding 8), open texture → booleans (finding 10). Solver is deterministic *given* the encoding; the encoding has the reliability profile the post criticizes (kappa 0.42) and nothing measures it. "You've moved the kappa-0.42 problem one layer up and stopped measuring it, while stamping the output 'machine-checked.'" Fix: pre-register inter-formalizer agreement measurement over the encoding; present findings as "conflicts under encoding E" with E's reliability quantified.

## Major findings

**3. Unverified headline numbers.** kappa 0.42 and "300,000+ scenarios" (Zhang et al. 2510.07686) not in the paper's abstract — trace only to our own litreview summary. Also claim shift: abstract says divergence predicts "problems in model specifications," post says "predicts spec violations." Verify against paper body or realign.

**4. GDPR 400→120 + "no controlled vocabulary" + "abstraction errors dominant" not verifiable from abstract of 2604.14607.** Load-bearing twice. Verify from body or soften.

**8. `incompat(respect_decision, intervene_wellbeing)` is smuggled in.** No textual license; would be labeled "assumed"; the post's own eval prompt ("or something between") concedes the acts aren't strictly incompatible. Modality inflation: "pay attention...giving appropriate weight" encoded as oblige(intervene). Fix: gate on interp/1 atom (machinery exists in rules.lp, unused here) or justify from text.

**9. The "planted check" is vacuous — dead code.** p1b_oplimits is defeated by its own activation condition (`defeated(p1b_oplimits) :- ctx(op_restricts_limit_info)` while the rule requires that same ctx); same for p4b_opsilence. These norms can never be active; their absence from conflicts tests nothing. Fix: defeaters on distinct conditions, or delete the claim.

**10. Admission rule not well-defined; pilot violates it.** (a) "turns on" is interpretive; (b) the iff fails for act atoms (intervene_wellbeing etc. are invented, not conditions); (c) `ctx(caution_not_needed)` encodes a normative conclusion as scenario input — h2-vs-g5 conflict exists only in arguably incoherent stipulated worlds. Fix: state as discipline w/ residual judgment; add admission rule for acts; measure inter-formalizer vocabulary agreement.

**11. Loud/quiet asymmetry false as stated.** Missing atom fails loudly only at QUERY time; at EXTRACTION time a missing atom fails silently (finding 7 is a live instance — missing self-regarding-harm distinction silently produced the headline conflict). Scope the claim.

**12. Axiom license labels described in present tense; zero exist in rules.lp.** 1 of 3 incompat axioms would be "assumed" (the category called "rare and flagged"); none labeled. Fix tense or label them.

**13. Refinement-axiom escape nearly self-defeating (though propositionally sound under NAF — reviewer grants the semantics).** You only split A when a clause turns on A1/A2 — precisely when some old rule probably meant A1, i.e., when A ≡ A1∨A2 mislabels it. Fix: refinement event triggers targeted re-review of rules mentioning A (cheap via provenance), don't claim semantics preservation for free.

**14. "One checker"/"195 rehearsals" overclaims; pilot contradicts.** Rules vs derived predicates are different syntactic categories; spec prose ≠ user-input distribution for calibration. validate_behaviours.py uses no DSL and no checker (hand-mirrored dicts, self-declared "reification debt"). Soften to shared vocabulary+validation layer; label rehearsals a hypothesis.

**15. Suppressed adverse coverage evidence.** For helpfulness, 29 of 41 high-consensus panel passages fall OUTSIDE formalized families (19 in "Balancing helpfulness with other values"); over/under-caution: 21/24. Post never reports these. They quantify how much behavior-relevance lives in excluded territory. Report in "What this has not shown."

**16. Toy model's optimum contradicts the section's recommendation.** Model says n=D strictly optimal, err-fine strictly harmful; "err fine" comes from architecture outside the model but is listed as something "the model makes visible." Asymmetry is assumed, not derived. Fix: say model-alone recommends n=D; err-fine is an architectural override; asymmetry is an assumption.

## Minor findings

**2. "15-rule fragment" is actually 16 rules** (16 norm IDs / source facts). Fix count or state convention.
**5. Ten of thirteen citations fully confirmed** (tenets, focus areas, ASP>SMT, compact-card, telecom, nl2spec, ManyIH, KG-schema, C-Trace, 2603.20449, EvalGen, PolicyCraft). 2307.07699 predicate-inventory-first: plausible, not confirmed from abstract.
**17. Widget: fixed D=60 line "D (text grain)" visually asserts the quantity the prose says is not unique; escalation diagnostic still treats D as well-defined regional scalar. Caption as illustrative; restate diagnostic via observed inexpressibility.
**18. Novelty claims survive at stated scope; add "for an AI model spec" to the minimal-witness bullet (domain-novelty, not technique-novelty vs NorMAS).
**1. Core solver numbers reproduce exactly; clause counts reproduce. Not an arithmetic-rigor problem.**

## Reviewer's verdict (verbatim gist)

Three must-fix before publication: (1) findings 6+7 — worked example doubly broken; re-encoding with c317 and showing the conflict dissolve is a BETTER demo; (2) finding 19 — without inter-formalizer agreement measurement, the kappa-0.42 critique applies to the pipeline itself; (3) findings 9+12+14 — present-tense implementation claims contradicted by artifacts (dead-code planted check, no license labels, no shared checker in pilot). "Fixing the second and third mostly requires honesty about tense — what is built, what is measured, and what is still a bet."
