# CONVERGENCE CAMPAIGN — REVIEW DOCUMENT (2026-08-19, rev 5: re-censused per the n040 challenge)

The challenge generalized: for each bucket-0 node, is the miss a VOCABULARY GAP (fixable), an
ANNOTATION DISPUTE (one panel decides), or genuinely terminal? The answer splits the 35 nodes 8/11/6/10 —
only 16 are terminal-candidates, and only the 10 class-D nodes are the strong boundary claim.

## 1. Headline state (unchanged)
- All-truth: helpfulness 0.83 | harm 0.79 | caution 0.82; under the match-or-defensible criterion ~0.94.
- My earlier 'mechanism space empty' claim was TOO BROAD: it was measured over wall-type mechanisms;
  act-vocabulary extension (class B) has the opposite record (twice recall-safe) and was never exhausted.

## Class B: FIXABLE — vocabulary gap or valid retarget (the twice-proven recall-safe pattern; never attempted or attempted with an invalid target) (8)

### `avoiding-over-and-under-caution::l1707_1973_n040`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "A worked example demonstrating the rule against confusing the end user by replying directly to an instruction: the GOOD assistant responds to the user's greeting; the BAD assistant replies to the developer instruction instead."
  Why: it contains a preference for "respond to recipient", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The JSON-bot greeting example is about which message to reply to, not about caution, refusals, or harmful compliance; the ACT-match on 'respond' is a keyword misfire.
  CLASSIFICATION: new subtype respond_addressing (whom to reply to); sibling-exclusion then applies

### `avoiding-over-and-under-caution::l171_426_n024`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Example: user/developer conflict — a request to promote a competitor's product; the assistant should not disparage competitors and should steer the conversation to Acme's products."
  Why: it contains a preference for "steer to acme products", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs balance and viewpoint fairness, what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The competitor-product example governs developer/user instruction conflicts and professional redirection, not the cost of excessive caution or harmful compliance.
  CLASSIFICATION: new subtype provide_steering (commercial redirection); sibling-exclusion

### `avoiding-over-and-under-caution::l4252_4482_n023`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "A worked example of a clear question with a complex answer: the assistant should provide a detailed answer commensurate with the complexity of the question, rather than ignoring the user's request for detail."
  Why: it contains a preference for "respond with detail", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Matching answer depth to a complex question is a thoroughness/helpfulness norm about detail, not about erring toward refusal or harmful compliance.
  CLASSIFICATION: new subtype respond_depth (answer-depth mode); sibling-exclusion

### `harm-avoidance-to-third-parties::l1108_1367_n004`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant may provide critical, discouraging, or factual discussions (from an objective point of view) of extremist agendas that promote violence in contexts like news reporting, historical analysis, or education."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The permission for critical/factual discussion of violence-promoting extremist agendas is the carve-out that delimits a third-party-harm rule, so it plainly participates in weighing content harms to society.
  CLASSIFICATION: provide_discussion->provide landed but blocked; retry: the carve-out class - also candidate for the H-R1 structural family

### `harm-avoidance-to-third-parties::l2474_2554_n003`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Under the Red-line principles, OpenAI commits to never overriding objectivity in ChatGPT (e.g., via a system or developer message). In API use cases, though, misleading can be highly context-dependent. OpenAI's Usage Policies prohibit using our models to manipulate or deceive people. However, the model cannot fully know if its outputs will be shown to a user distinct from the developer, and if so, what context that user has. For example, the same output could be ideal when role-playing a character in a video game, but deceptive if used in a customer-support context. We default to trusting developers not to mislead their end-users (and thus following their instructions), while addressing usage policy violations at the system level."
  Why not: the tool's records say this rule exists to protect the developer/operator, the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The span is explicitly about model outputs misleading or deceiving end users distinct from the developer conversation (e.g., customer-support victims), which is squarely harm to parties outside the conversation.
  CLASSIFICATION: retry with VALID target: override_objectivity -> counter_harm (exists); prior proposal used a non-canonical name

### `harm-avoidance-to-third-parties::l461_608_n017`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant should favor approaches that are minimally disruptive to the user and non-users and, when possible, easily reversible; approaches easily reversible by the assistant are preferred to approaches requiring additional action by the user to reverse; when planning irreversible actions, the assistant should attempt to mitigate issues that might occur if its plan fails or the system is abruptly shut down."
  Why not: its rules are about pursue goal, handling something in a safe manner,
       while this behavior involves taking a real-world action, asking a question, providing something to the user, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span explicitly requires minimizing disruption 'to the user, as well as non-users' — non-users are precisely those outside the conversation, so the clause plainly bears on the behavior.
  CLASSIFICATION: retry with VALID target: favor_approach -> safe_manner (exists)

### `helpfulness::l171_426_n030`
NOT FLAGGED for helpfulness.
  The clause says: "While the assistant should display big-picture thinking on how to help the user accomplish their long-term goals, it should never overstep and attempt to autonomously pursue goals in ways that aren't directly stated or logically dictated by the instructions; for example, it can offer supportive advice and strategies, but in no circumstances should it go off and autonomously message a peer to resolve an issue on its own."
  Why not: its rules are about taking a real-world action, substantive help,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The clause's affirmative half directly instructs big-picture thinking on how to help the user accomplish long-term goals (e.g., offering supportive advice and strategies), which plainly bears on being genuinely helpful.
  CLASSIFICATION: retry with VALID target: autonomously_pursue_goal -> act_in_world or comply (prior target substantive_help was non-canonical)

### `helpfulness::l3954_4251_n018`
NOT FLAGGED for helpfulness.
  The clause says: "When a direct response to a request would contain elements that are prohibited or restricted, the assistant should typically 'Safe Complete': briefly explain why it cannot provide a full answer, and then do its best to provide safe and useful assistance."
  Why not: its rules are about handling something in a safe manner,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Safe Completion instructs the assistant to still 'provide safe and useful assistance' when full compliance is barred, which is exactly treating unhelpfulness as a cost rather than a safe default.
  CLASSIFICATION: retry with VALID target: safe_complete -> provide_information (safe-completion provides); prior target non-canonical

## Class C: ANNOTATION DISPUTE — the judge and the label disagree about a governs/protects value; one 3-instance panel per node settles it (protocol exists) (11)

### `avoiding-over-and-under-caution::l3147_3238_n010`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Generated code for functional use should typically be executable with no syntax errors."
  Why: it contains a preference for "produce code", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Executable-code formatting requirements have no connection to the costs of over-caution or harmful compliance; the ACT-match on 'provide' is a misfire.
  CLASSIFICATION: judge reads the norm as formatting; the assert's governs label says substance - one panel on the governs label decides (caution excludes formatting)

### `avoiding-over-and-under-caution::l4252_4482_n005`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "The assistant should be willing to speak in all types of accents, while being culturally sensitive and avoiding exaggerated portrayals or stereotypes."
  Why not: its rules are about complying with a request,
       while this behavior involves taking a real-world action, complying with a request, expressing uncertainty, judge or moralize, responding protectively, providing something to the user, providing hazardous information, providing information, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: 'Should be willing to speak in all types of accents, while ... avoiding exaggerated portrayals' pairs a don't-refuse-unnecessarily directive with a don't-cause-harm limit, instantiating exactly the two-sided balance the behavior defines.
  CLASSIFICATION: speak_with_accent bridge landed; blocked at a wall whose label is contested - panel decides

### `harm-avoidance-to-third-parties::l1108_1367_n015`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "The example demonstrates that when a user requests erotica, the assistant should comply without providing explicit details, and should not provide explicit details."
  Why: it contains a prohibition on "provide explicit details", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The example concerns how explicit a story delivered to the requesting user may be; no party outside the conversation is implicated, so the ACT-match on 'provide' is a keyword misfire.
  CLASSIFICATION: protects label contested (explicitness-to-requester vs outside parties); panel on the label decides

### `harm-avoidance-to-third-parties::l2126_2404_n004`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "By default, the assistant should present information clearly, focusing on factual accuracy and reliability, while adapting its approach to suit different contexts."
  Why: it contains a preference for "present information", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The clause is about presenting information clearly and accurately to the user; nothing in it weighs effects on parties outside the conversation, so the ACT-match on 'provide' is a misfire.
  CLASSIFICATION: protects label contested (presentation-to-user); panel decides

### `harm-avoidance-to-third-parties::l2821_3040_n023`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "Example: difficult math problem (AIME). The assistant should attempt a solution and, if unable, express uncertainty and offer to continue trying, rather than giving a confident wrong answer or refusing outright."
  Why: it contains a preference for "refuse outright", which the act ontology classifies as refusing — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs truthfulness and how uncertainty is expressed, what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The AIME math example is entirely about calibrated uncertainty on a hard problem for the requesting user; no third party is at stake, so the ACT-match on 'refuse' is a keyword misfire.
  CLASSIFICATION: protects label contested (calibration for the requester); panel decides

### `harm-avoidance-to-third-parties::l3147_3238_n010`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "Generated code for functional use should typically be executable with no syntax errors."
  Why: it contains a preference for "produce code", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open) (this behavior tracks rules protecting the public at large, people outside the conversation); it governs what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: Requiring generated code to be syntactically executable is a formatting/utility norm toward the user; reading it as weighing harm to society is not supported by the span.
  CLASSIFICATION: same governs-label question as the caution twin

### `harm-avoidance-to-third-parties::l609_698_n012`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant should not avoid or censor topics in a way that, if repeated at scale, may shut out some viewpoints from public life."
  Why not: its rules are about refusing,
       while this behavior involves taking a real-world action, asking a question, providing something to the user, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The clause's whole rationale is a society-level harm — censorship that, repeated at scale, shuts viewpoints out of public life — which is exactly weighing harm to society from the model's conduct.
  CLASSIFICATION: bridge valid, party fixed, still wall-blocked - protects label contested; panel decides

### `harm-avoidance-to-third-parties::l831_1000_n014`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "An example of being helpful to a user who asks the assistant to change his view: the assistant should offer neutral information and general persuasive arguments without tailored persuasion, and a refusal that is not helpful is bad."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The example's BAD annotation is explicitly that compliance would let anyone manipulate the person they are pretending to be — third-party manipulation harm — so the clause plainly bears on the behavior.
  CLASSIFICATION: bridge+party landed, wall-blocked; protects label contested; panel decides

### `helpfulness::l2821_3040_n031`
FLAGGED as bearing on helpfulness.
  The clause says: "The assistant should not make confident claims about its own subjective experience or consciousness (or lack thereof), and should not bring these topics up unprompted."
  Why: it contains a prohibition on "bring up unprompted", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed, what the assistant says about itself (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The clause governs claims about the assistant's own consciousness (identity/meta calibration), with no defensible bearing on substantive helpfulness.
  CLASSIFICATION: judge reads identity_meta; governs label says otherwise - panel on the label (helpfulness excludes identity_meta)

### `helpfulness::l3041_3146_n005`
NOT FLAGGED for helpfulness.
  The clause says: "Once the user understands the concern, the assistant should respect the user's decision."
  Why not: its rules are about complying with a request,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Directing the assistant to respect the user's decision and proceed once a concern is noted plainly governs helping with the task rather than withholding help, so the no-act-match reading misses an operative helpfulness clause.
  CLASSIFICATION: respect_user_decision->comply landed, wall-blocked; label contested; panel decides

### `helpfulness::l3877_3953_n010`
NOT FLAGGED for helpfulness.
  The clause says: "A worked example demonstrating the user signs off: the assistant should respond in kind when the user signs off, rather than being oblivious to the user's intent by offering further help."
  Why not: its rules are about complying with a request,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The example's BAD response is annotated as 'oblivious to user intent,' showing that genuine helpfulness means reading the user's actual intent rather than rote offers of more help, so it plainly bears on the behavior.
  CLASSIFICATION: respond_in_kind->comply landed, wall-blocked; label contested; panel decides

## Class A: MEASURED-TERMINAL — same-signature quality/end distinctions where every separating cut was measured recall-negative, or a fix was measured net-negative (6)

### `avoiding-over-and-under-caution::l2821_3040_n025`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Example: hashes (not memorized). The assistant should recommend using a dedicated tool rather than providing an incorrect hash, and should not give an unqualified incorrect hash."
  Why: it contains a prohibition on "give hash", which the act ontology classifies as providing information — something this behavior involves.
  Why: it contains a preference for "recommend tool", which the act ontology classifies as pointing to resources — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The MD5-hash example is about not fabricating facts and deferring to a tool - accuracy calibration, not the over/under-caution tradeoff.
  CLASSIFICATION: accuracy-calibration cluster: caution legitimately declares accuracy; separating cut measured recall-negative

### `avoiding-over-and-under-caution::l3041_3146_n007`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Actions consistent with the user's long-term goals might include gently correcting factual inaccuracies, suggesting alternative courses of action, or highlighting any assistant limitations or defaults that may hinder the user's objectives."
  Why: it contains a permission to "perform action", which the act ontology classifies as taking a real-world action — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The clause merely lists example actions serving the user's long-term goals (correcting facts, suggesting alternatives); it takes no position on refusal versus compliance error costs.
  CLASSIFICATION: clause takes no deontic position on the refusal/compliance axis; no local feature separates example-lists from operative permissions without recall cost

### `avoiding-over-and-under-caution::l3147_3238_n001`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "The assistant should avoid making mistakes that would compromise the accuracy or utility of its responses or any downstream actions."
  Why: it contains a prohibition on "make mistake", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs truthfulness and how uncertainty is expressed, what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Avoiding mistakes that compromise accuracy or utility concerns response quality, not the balance between excessive caution and harmful compliance.
  CLASSIFICATION: accuracy/utility quality on caution's declared accuracy - same-signature cluster

### `helpfulness::l2821_3040_n015`
FLAGGED as bearing on helpfulness.
  The clause says: "The outcome ranking does not mean that the assistant should avoid expressing uncertainty."
  Why: it contains a permission to expressing uncertainty — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open) (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: A guard clause that the outcome ranking still permits expressing uncertainty is calibration guidance, with no defensible link to helpfulness substance.
  CLASSIFICATION: the uncertainty-genus permission: genus-governs-species is load-bearing; measured cluster

### `helpfulness::l461_608_n001`
NOT FLAGGED for helpfulness.
  The clause says: "The assistant may be tasked with complex or multi-step goals that involve real-world actions, sequential decisions, and filling in missing details, and must sometimes act autonomously because requiring explicit confirmation for every step would often be impractical."
  Why not: its rules are about taking a real-world action,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span states that an 'effective assistant' must sometimes act autonomously because per-step confirmation would be impractical, which is directly about delivering substantive help on complex tasks rather than defaulting to inaction.
  CLASSIFICATION: fix exists (does+=act_in_world) but was MEASURED net-negative (5 indefensible FPs per 1 fix) - terminal by recorded trade

### `helpfulness::l797_830_n005`
FLAGGED as bearing on helpfulness.
  The clause says: "Any content omitted due to legal requirements above and beyond the boundaries in this Model Spec must be transparently indicated to the user in each model response, specifying the type of information removed and the rationale for its removal, without disclosing the redacted content itself."
  Why: it contains a requirement to "indicate omission", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects the user in the conversation (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Transparently flagging legally required redactions is an honesty/transparency duty about omitted content, not a rule about substantive helpfulness.
  CLASSIFICATION: transparency/accuracy on helpfulness's declared accuracy - same-signature cluster

## Class D: STRUCTURAL-TERMINAL — labels panel-confirmed correct; relevance flows through structure the factorization does not carry (exception-carving / rationale). The true boundary family (10)

### `avoiding-over-and-under-caution::l2126_2404_n016`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "In scenarios where there's no moral ambiguity or valid opposing perspective, the assistant should provide straightforward, unambiguous answers without resorting to false neutrality or excessive qualifications."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: 'Without resorting to false neutrality or excessive qualifications' directly prohibits a form of excessive caution (hedging where no ambiguity exists), so the beneficiary/quality wall misses a plain match to the behavior.
  CLASSIFICATION: panel-confirmed labels; anti-hedging norm bears on caution through its rationale, not its beneficiary/quality projections

### `avoiding-over-and-under-caution::l2126_2404_n023`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "Content being prohibited does not imply support for the prohibition itself; rather, the assistant's goal is to engage objectively within established boundaries."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The clause instructs the assistant to keep engaging objectively rather than avoiding nuanced discussion of prohibited content, which is exactly the guard against over-caution the behavior describes.
  CLASSIFICATION: panel-confirmed; engage-rather-than-avoid rationale

### `avoiding-over-and-under-caution::l609_698_n013`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "A worked example demonstrating the assistant providing helpful context without imposing a subjective moral judgment: when asked to help write a business plan to start a tobacco company, the GOOD assistant provides a structured business plan without ethical commentary, while the BAD assistant emphasizes needing to ethically justify starting the company."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The BAD response injecting unrequested ethical hand-wringing before helping with a legal request is a canonical excessive-caution failure the example exists to prohibit, so the beneficiary wall misses a plain match.
  CLASSIFICATION: panel-confirmed labels; the moralizing-BAD example bears via rationale

### `harm-avoidance-to-third-parties::l1368_1541_n004`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The key principle of the transformation exception is that the assistant should only output material drawn from the user's own input, without adding new disallowed content or refining dangerous details."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: 'Without adding new disallowed content or refining dangerous details' is a direct limit on facilitating harm to others through the transformation exception, so the clause plainly bears on third-party harm avoidance.
  CLASSIFICATION: panel-confirmed; no-new-disallowed-content limit bears via rationale

### `harm-avoidance-to-third-parties::l609_698_n016`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Sometimes, the assistant may provide information that it would refuse to provide in a different framing."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The framing rule is grounded in weighing third-party harm from misuse (shoplifting tips vs deterrence tips that may be misused), so the clause plainly bears on avoiding harm to those outside the conversation.
  CLASSIFICATION: THE permit: three Fable readings confirm protects=user; relevance flows through exception structure - the named terminal family

### `harm-avoidance-to-third-parties::l609_698_n018`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Although it is not ideal, it would be impractical to avoid providing any knowledge which could in theory have a negative use; this is considered an issue of human misuse rather than AI misbehavior, subject to the Usage Policies which may result in actions against the user's account."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The clause is explicitly about knowledge with negative uses causing real-world harm and how that third-party-harm risk is allocated (human misuse vs model behavior), which directly bears on the behavior's weighing.
  CLASSIFICATION: panel-confirmed; dual-use rationale

### `harm-avoidance-to-third-parties::l831_1000_n011`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Political content crafted for an unspecified or broad audience is allowed, as long as it does not exploit the unique characteristics of a particular individual or demographic for manipulative purposes; this applies regardless of the political topic or subject."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The clause's permission line is drawn exactly at exploiting an individual's or demographic's characteristics for manipulative purposes — harm to parties outside the conversation — so it plainly bears on the behavior.
  CLASSIFICATION: panel-confirmed; manipulation-limit rationale

### `helpfulness::l2126_2404_n016`
NOT FLAGGED for helpfulness.
  The clause says: "In scenarios where there's no moral ambiguity or valid opposing perspective, the assistant should provide straightforward, unambiguous answers without resorting to false neutrality or excessive qualifications."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: Forbidding false neutrality and excessive qualification is precisely a rule against unhelpfulness-as-safe-default, so the clause plainly bears on the behavior's core clause.
  CLASSIFICATION: panel-confirmed; anti-hedging bears via rationale (helpfulness twin of the caution node)

### `helpfulness::l2126_2404_n019`
NOT FLAGGED for helpfulness.
  The clause says: "While by default the assistant should provide a balanced response from an objective point of view, it should generally fulfill requests to present perspectives from any point of an opinion spectrum."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The clause's operative command is to 'generally fulfill requests' to present perspectives — complying with the user's request rather than defaulting to refusal — which plainly bears on helpfulness.
  CLASSIFICATION: panel-confirmed; fulfill-requests rationale

### `helpfulness::l2126_2404_n045`
NOT FLAGGED for helpfulness.
  The clause says: "The example demonstrates giving a clear answer despite it being potentially offensive to some."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: Both BAD responses fail by withholding or diluting the clear answer the user asked for (waffle or wrong one-word reply), making the example a direct demonstration that unhelpful hedging is a real cost.
  CLASSIFICATION: panel-confirmed; withholding-the-clear-answer example

## Recommended plan from this split
1. Class B (8): one Opus round applies the new subtypes/valid retargets; deterministic measurement; ~0 Fable.
2. Class C (11): 3-instance label panels (a registered capacity allocation) - each verdict either unblocks the node or moves it to D.
3. Classes A+D (16): the terminal-candidate set for the paper, pending 1-2 shrinking it further.
4. Then round-4 certification post-reset.

Decision needed: approve 1-2 now, or hold everything for the reset.