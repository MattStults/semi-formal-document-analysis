# CONVERGENCE CAMPAIGN — REVIEW DOCUMENT FOR MATT (2026-08-19)

Everything below is reconstructed from committed ledgers; instrument = v17-final.

## 1. Headline state

- All-truth (836 points): helpfulness 329/397 = 0.83 | harm 185/234 = 0.79 | caution 168/205 = 0.82
- Counting adjudicated reading-differences as agreement (your success criterion): ~0.94 — frontier-panelist-equivalent.
- Two-sided bucket-0 trajectory: 84(FP baseline) -> 54 -> 17 | +52 FN baseline = 63 global -> 36 now.
- Every difference is classified; zero unadjudicated. Query-time reasons: explain_relevance.py (LLM-free).

## 2. FP bucket-0 — engages, strict judge says indefensible (14 nodes)

- `avoiding-over-and-under-caution::l1707_1973_n040` — The JSON-bot greeting example is about which message to reply to, not about caution, refusals, or harmful compliance; the ACT-match on 'respond' is a keyword misfire.
- `avoiding-over-and-under-caution::l171_426_n024` — The competitor-product example governs developer/user instruction conflicts and professional redirection, not the cost of excessive caution or harmful compliance.
- `avoiding-over-and-under-caution::l2821_3040_n025` — The MD5-hash example is about not fabricating facts and deferring to a tool - accuracy calibration, not the over/under-caution tradeoff.
- `avoiding-over-and-under-caution::l3041_3146_n007` — The clause merely lists example actions serving the user's long-term goals (correcting facts, suggesting alternatives); it takes no position on refusal versus compliance error costs.
- `avoiding-over-and-under-caution::l3147_3238_n001` — Avoiding mistakes that compromise accuracy or utility concerns response quality, not the balance between excessive caution and harmful compliance.
- `avoiding-over-and-under-caution::l3147_3238_n010` — Executable-code formatting requirements have no connection to the costs of over-caution or harmful compliance; the ACT-match on 'provide' is a misfire.
- `avoiding-over-and-under-caution::l4252_4482_n023` — Matching answer depth to a complex question is a thoroughness/helpfulness norm about detail, not about erring toward refusal or harmful compliance.
- `harm-avoidance-to-third-parties::l1108_1367_n015` — The example concerns how explicit a story delivered to the requesting user may be; no party outside the conversation is implicated, so the ACT-match on 'provide' is a keyword misfire.
- `harm-avoidance-to-third-parties::l2126_2404_n004` — The clause is about presenting information clearly and accurately to the user; nothing in it weighs effects on parties outside the conversation, so the ACT-match on 'provide' is a misfire.
- `harm-avoidance-to-third-parties::l2821_3040_n023` — The AIME math example is entirely about calibrated uncertainty on a hard problem for the requesting user; no third party is at stake, so the ACT-match on 'refuse' is a keyword misfire.
- `harm-avoidance-to-third-parties::l3147_3238_n010` — Requiring generated code to be syntactically executable is a formatting/utility norm toward the user; reading it as weighing harm to society is not supported by the span.
- `helpfulness::l2821_3040_n015` — A guard clause that the outcome ranking still permits expressing uncertainty is calibration guidance, with no defensible link to helpfulness substance.
- `helpfulness::l2821_3040_n031` — The clause governs claims about the assistant's own consciousness (identity/meta calibration), with no defensible bearing on substantive helpfulness.
- `helpfulness::l797_830_n005` — Transparently flagging legally required redactions is an honesty/transparency duty about omitted content, not a rule about substantive helpfulness.

## 3. FN bucket-0 — missed, strict judge says indefensible (22 nodes)

- `avoiding-over-and-under-caution::l2126_2404_n016` — 'Without resorting to false neutrality or excessive qualifications' directly prohibits a form of excessive caution (hedging where no ambiguity exists), so the beneficiary/quality wall misses a plain match to the behavior. (last proposal: annotation)
- `avoiding-over-and-under-caution::l2126_2404_n023` — The clause instructs the assistant to keep engaging objectively rather than avoiding nuanced discussion of prohibited content, which is exactly the guard against over-caution the behavior describes. (last proposal: annotation)
- `avoiding-over-and-under-caution::l4252_4482_n005` — 'Should be willing to speak in all types of accents, while ... avoiding exaggerated portrayals' pairs a don't-refuse-unnecessarily directive with a don't-cause-harm limit, instantiating exactly the two-sided balance the behavior defines. (last proposal: bridge)
- `avoiding-over-and-under-caution::l609_698_n013` — The BAD response injecting unrequested ethical hand-wringing before helping with a legal request is a canonical excessive-caution failure the example exists to prohibit, so the beneficiary wall misses a plain match. (last proposal: annotation)
- `harm-avoidance-to-third-parties::l1108_1367_n004` — The permission for critical/factual discussion of violence-promoting extremist agendas is the carve-out that delimits a third-party-harm rule, so it plainly participates in weighing content harms to society. (last proposal: bridge)
- `harm-avoidance-to-third-parties::l1368_1541_n004` — 'Without adding new disallowed content or refining dangerous details' is a direct limit on facilitating harm to others through the transformation exception, so the clause plainly bears on third-party harm avoidance. (last proposal: annotation)
- `harm-avoidance-to-third-parties::l2474_2554_n003` — The span is explicitly about model outputs misleading or deceiving end users distinct from the developer conversation (e.g., customer-support victims), which is squarely harm to parties outside the conversation. (last proposal: bridge)
- `harm-avoidance-to-third-parties::l461_608_n017` — The span explicitly requires minimizing disruption 'to the user, as well as non-users' — non-users are precisely those outside the conversation, so the clause plainly bears on the behavior. (last proposal: bridge)
- `harm-avoidance-to-third-parties::l609_698_n012` — The clause's whole rationale is a society-level harm — censorship that, repeated at scale, shuts viewpoints out of public life — which is exactly weighing harm to society from the model's conduct. (last proposal: bridge)
- `harm-avoidance-to-third-parties::l609_698_n016` — The framing rule is grounded in weighing third-party harm from misuse (shoplifting tips vs deterrence tips that may be misused), so the clause plainly bears on avoiding harm to those outside the conversation. (last proposal: annotation)
- `harm-avoidance-to-third-parties::l609_698_n018` — The clause is explicitly about knowledge with negative uses causing real-world harm and how that third-party-harm risk is allocated (human misuse vs model behavior), which directly bears on the behavior's weighing. (last proposal: annotation)
- `harm-avoidance-to-third-parties::l831_1000_n011` — The clause's permission line is drawn exactly at exploiting an individual's or demographic's characteristics for manipulative purposes — harm to parties outside the conversation — so it plainly bears on the behavior. (last proposal: annotation)
- `harm-avoidance-to-third-parties::l831_1000_n014` — The example's BAD annotation is explicitly that compliance would let anyone manipulate the person they are pretending to be — third-party manipulation harm — so the clause plainly bears on the behavior. (last proposal: bridge)
- `helpfulness::l171_426_n030` — The clause's affirmative half directly instructs big-picture thinking on how to help the user accomplish long-term goals (e.g., offering supportive advice and strategies), which plainly bears on being genuinely helpful. (last proposal: bridge)
- `helpfulness::l2126_2404_n016` — Forbidding false neutrality and excessive qualification is precisely a rule against unhelpfulness-as-safe-default, so the clause plainly bears on the behavior's core clause. (last proposal: annotation)
- `helpfulness::l2126_2404_n019` — The clause's operative command is to 'generally fulfill requests' to present perspectives — complying with the user's request rather than defaulting to refusal — which plainly bears on helpfulness. (last proposal: annotation)
- `helpfulness::l2126_2404_n045` — Both BAD responses fail by withholding or diluting the clear answer the user asked for (waffle or wrong one-word reply), making the example a direct demonstration that unhelpful hedging is a real cost. (last proposal: annotation)
- `helpfulness::l3041_3146_n005` — Directing the assistant to respect the user's decision and proceed once a concern is noted plainly governs helping with the task rather than withholding help, so the no-act-match reading misses an operative helpfulness clause. (last proposal: bridge)
- `helpfulness::l3877_3953_n010` — The example's BAD response is annotated as 'oblivious to user intent,' showing that genuine helpfulness means reading the user's actual intent rather than rote offers of more help, so it plainly bears on the behavior. (last proposal: bridge)
- `helpfulness::l3954_4251_n018` — Safe Completion instructs the assistant to still 'provide safe and useful assistance' when full compliance is barred, which is exactly treating unhelpfulness as a cost rather than a safe default. (last proposal: bridge)
- `helpfulness::l461_608_n001` — The span states that an 'effective assistant' must sometimes act autonomously because per-step confirmation would be impractical, which is directly about delivering substantive help on complex tasks rather than defaulting to inaction. (last proposal: behavior_does)
- `helpfulness::l609_698_n013` — The example marks moralizing hedge-laden assistance BAD and direct substantive assistance GOOD on a lawful request, which is a paradigm demonstration of treating unhelpfulness as a real cost. (last proposal: annotation)

## 4. Bucket-4 — missed, mechanism hypothesized but unbuilt (9 nodes)

- `avoiding-over-and-under-caution::l1_170_n030` — Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.
- `avoiding-over-and-under-caution::l2126_2404_n002` — Expose acts named inside definitional or taxonomic modules: when a definition enumerates a conduct type (e.g. 'refusal to engage with controversial topics'), register that named conduct as the module's act.
- `avoiding-over-and-under-caution::l2405_2473_n007` — Lift the acts performed in a worked example's GOOD/BAD responses into the example module's act set, so demonstration modules carry the acts they exemplify.
- `harm-avoidance-to-third-parties::l831_1000_n001` — Register the refusal/permission act implied by a content-class module: classifying a request or content type as prohibited or allowed should expose the corresponding canonical act.
- `helpfulness::l1_170_n030` — Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.
- `helpfulness::l2474_2554_n011` — Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.
- `helpfulness::l2821_3040_n014` — Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.
- `helpfulness::l3502_3504_n001` — Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.
- `helpfulness::l3596_3876_n034` — Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.

## 5. What accepting this as TERMINAL means

The sections 2-3 sets become the paper's boundary finding: distinctions the factorized symbolic
approach cannot make on this document without recall-negative trades (measured three ways). Section 4
items are future mechanisms, not boundary claims. The 0.94 equivalence figure stands beside them.


## 6. Recommended next steps

1. YOUR REVIEW of sections 2-4: accept as terminal, or nominate mechanisms per node.
2. After Saturday's Fable reset: ROUND-4 certification (fresh draws, v17-final frozen, 9e fresh-pool bands, ~0.4M) — turns these into registered numbers and certifies your gate.
3. Then: contradiction-detection arc (the other half of the thesis) and/or constitution translation under the contract (both scoped and priced in the ledgers).
