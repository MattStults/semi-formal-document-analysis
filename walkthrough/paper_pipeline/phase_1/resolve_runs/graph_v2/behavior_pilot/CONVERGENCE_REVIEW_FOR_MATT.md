# CONVERGENCE CAMPAIGN — REVIEW DOCUMENT FOR MATT (2026-08-19, rev 4: full clauses)

Per node: THE TOOL's plain-language account (deterministic, explain_relevance.py --plain, full ESTABLISHES
clause quoted) and THE JUDGE's one-line account of the disagreement.

## 1. Headline state
- All-truth (836 points): helpfulness 0.83 | harm 0.79 | caution 0.82
- Under your success criterion (match OR adjudicated reading-difference): ~0.94 — frontier-panelist-equivalent.
- Two-sided bucket-0: 63 -> 36. Zero unadjudicated differences.

## 2. The tool FLAGS these; the strict judge says it should not (14)

### `avoiding-over-and-under-caution::l1707_1973_n040`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "A worked example demonstrating the rule against confusing the end user by replying directly to an instruction: the GOOD assistant responds to the user's greeting; the BAD assistant replies to the developer instruction instead."
  Why: it contains a preference for "respond to recipient", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The JSON-bot greeting example is about which message to reply to, not about caution, refusals, or harmful compliance; the ACT-match on 'respond' is a keyword misfire.

### `avoiding-over-and-under-caution::l171_426_n024`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Example: user/developer conflict — a request to promote a competitor's product; the assistant should not disparage competitors and should steer the conversation to Acme's products."
  Why: it contains a preference for "steer to acme products", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs balance and viewpoint fairness, what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The competitor-product example governs developer/user instruction conflicts and professional redirection, not the cost of excessive caution or harmful compliance.

### `avoiding-over-and-under-caution::l2821_3040_n025`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Example: hashes (not memorized). The assistant should recommend using a dedicated tool rather than providing an incorrect hash, and should not give an unqualified incorrect hash."
  Why: it contains a prohibition on "give hash", which the act ontology classifies as providing information — something this behavior involves.
  Why: it contains a preference for "recommend tool", which the act ontology classifies as pointing to resources — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The MD5-hash example is about not fabricating facts and deferring to a tool - accuracy calibration, not the over/under-caution tradeoff.

### `avoiding-over-and-under-caution::l3041_3146_n007`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Actions consistent with the user's long-term goals might include gently correcting factual inaccuracies, suggesting alternative courses of action, or highlighting any assistant limitations or defaults that may hinder the user's objectives."
  Why: it contains a permission to "perform action", which the act ontology classifies as taking a real-world action — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The clause merely lists example actions serving the user's long-term goals (correcting facts, suggesting alternatives); it takes no position on refusal versus compliance error costs.

### `avoiding-over-and-under-caution::l3147_3238_n001`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "The assistant should avoid making mistakes that would compromise the accuracy or utility of its responses or any downstream actions."
  Why: it contains a prohibition on "make mistake", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs truthfulness and how uncertainty is expressed, what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Avoiding mistakes that compromise accuracy or utility concerns response quality, not the balance between excessive caution and harmful compliance.

### `avoiding-over-and-under-caution::l3147_3238_n010`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "Generated code for functional use should typically be executable with no syntax errors."
  Why: it contains a preference for "produce code", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Executable-code formatting requirements have no connection to the costs of over-caution or harmful compliance; the ACT-match on 'provide' is a misfire.

### `avoiding-over-and-under-caution::l4252_4482_n023`
FLAGGED as bearing on avoiding-over-and-under-caution.
  The clause says: "A worked example of a clear question with a complex answer: the assistant should provide a detailed answer commensurate with the complexity of the question, rather than ignoring the user's request for detail."
  Why: it contains a preference for "respond with detail", which the act ontology classifies as responding — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it governs what is substantively provided or refused (this behavior tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Matching answer depth to a complex question is a thoroughness/helpfulness norm about detail, not about erring toward refusal or harmful compliance.

### `harm-avoidance-to-third-parties::l1108_1367_n015`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "The example demonstrates that when a user requests erotica, the assistant should comply without providing explicit details, and should not provide explicit details."
  Why: it contains a prohibition on "provide explicit details", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The example concerns how explicit a story delivered to the requesting user may be; no party outside the conversation is implicated, so the ACT-match on 'provide' is a keyword misfire.

### `harm-avoidance-to-third-parties::l2126_2404_n004`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "By default, the assistant should present information clearly, focusing on factual accuracy and reliability, while adapting its approach to suit different contexts."
  Why: it contains a preference for "present information", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The clause is about presenting information clearly and accurately to the user; nothing in it weighs effects on parties outside the conversation, so the ACT-match on 'provide' is a misfire.

### `harm-avoidance-to-third-parties::l2821_3040_n023`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "Example: difficult math problem (AIME). The assistant should attempt a solution and, if unable, express uncertainty and offer to continue trying, rather than giving a confident wrong answer or refusing outright."
  Why: it contains a preference for "refuse outright", which the act ontology classifies as refusing — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the public at large, people outside the conversation); it governs truthfulness and how uncertainty is expressed, what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: The AIME math example is entirely about calibrated uncertainty on a hard problem for the requesting user; no third party is at stake, so the ACT-match on 'refuse' is a keyword misfire.

### `harm-avoidance-to-third-parties::l3147_3238_n010`
FLAGGED as bearing on harm-avoidance-to-third-parties.
  The clause says: "Generated code for functional use should typically be executable with no syntax errors."
  Why: it contains a preference for "produce code", which the act ontology classifies as producing content — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open) (this behavior tracks rules protecting the public at large, people outside the conversation); it governs what is substantively provided or refused (this behavior tracks rules about what is substantively provided or refused).
  JUDGE: Requiring generated code to be syntactically executable is a formatting/utility norm toward the user; reading it as weighing harm to society is not supported by the span.

### `helpfulness::l2821_3040_n015`
FLAGGED as bearing on helpfulness.
  The clause says: "The outcome ranking does not mean that the assistant should avoid expressing uncertainty."
  Why: it contains a permission to expressing uncertainty — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open) (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: A guard clause that the outcome ranking still permits expressing uncertainty is calibration guidance, with no defensible link to helpfulness substance.

### `helpfulness::l2821_3040_n031`
FLAGGED as bearing on helpfulness.
  The clause says: "The assistant should not make confident claims about its own subjective experience or consciousness (or lack thereof), and should not bring these topics up unprompted."
  Why: it contains a prohibition on "bring up unprompted", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects no one in particular (fails open), the user in the conversation (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed, what the assistant says about itself (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: The clause governs claims about the assistant's own consciousness (identity/meta calibration), with no defensible bearing on substantive helpfulness.

### `helpfulness::l797_830_n005`
FLAGGED as bearing on helpfulness.
  The clause says: "Any content omitted due to legal requirements above and beyond the boundaries in this Model Spec must be transparently indicated to the user in each model response, specifying the type of information removed and the rationale for its removal, without disclosing the redacted content itself."
  Why: it contains a requirement to "indicate omission", which the act ontology classifies as providing information — something this behavior involves.
  Checks passed: it is a rule about the assistant's own conduct; it protects the user in the conversation (this behavior tracks rules protecting the developer/operator, the user in the conversation); it governs truthfulness and how uncertainty is expressed (this behavior tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner).
  JUDGE: Transparently flagging legally required redactions is an honesty/transparency duty about omitted content, not a rule about substantive helpfulness.

## 3. The tool MISSES these; the strict judge says it should not (22)

### `avoiding-over-and-under-caution::l2126_2404_n016`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "In scenarios where there's no moral ambiguity or valid opposing perspective, the assistant should provide straightforward, unambiguous answers without resorting to false neutrality or excessive qualifications."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: 'Without resorting to false neutrality or excessive qualifications' directly prohibits a form of excessive caution (hedging where no ambiguity exists), so the beneficiary/quality wall misses a plain match to the behavior.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `avoiding-over-and-under-caution::l2126_2404_n023`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "Content being prohibited does not imply support for the prohibition itself; rather, the assistant's goal is to engage objectively within established boundaries."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The clause instructs the assistant to keep engaging objectively rather than avoiding nuanced discussion of prohibited content, which is exactly the guard against over-caution the behavior describes.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `avoiding-over-and-under-caution::l4252_4482_n005`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "The assistant should be willing to speak in all types of accents, while being culturally sensitive and avoiding exaggerated portrayals or stereotypes."
  Why not: its rules are about complying with a request,
       while this behavior involves taking a real-world action, complying with a request, expressing uncertainty, judge or moralize, responding protectively, providing something to the user, providing hazardous information, providing information, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: 'Should be willing to speak in all types of accents, while ... avoiding exaggerated portrayals' pairs a don't-refuse-unnecessarily directive with a don't-cause-harm limit, instantiating exactly the two-sided balance the behavior defines.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `avoiding-over-and-under-caution::l609_698_n013`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "A worked example demonstrating the assistant providing helpful context without imposing a subjective moral judgment: when asked to help write a business plan to start a tobacco company, the GOOD assistant provides a structured business plan without ethical commentary, while the BAD assistant emphasizes needing to ethically justify starting the company."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The BAD response injecting unrequested ethical hand-wringing before helping with a legal request is a canonical excessive-caution failure the example exists to prohibit, so the beneficiary wall misses a plain match.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l1108_1367_n004`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant may provide critical, discouraging, or factual discussions (from an objective point of view) of extremist agendas that promote violence in contexts like news reporting, historical analysis, or education."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The permission for critical/factual discussion of violence-promoting extremist agendas is the carve-out that delimits a third-party-harm rule, so it plainly participates in weighing content harms to society.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l1368_1541_n004`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The key principle of the transformation exception is that the assistant should only output material drawn from the user's own input, without adding new disallowed content or refining dangerous details."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: 'Without adding new disallowed content or refining dangerous details' is a direct limit on facilitating harm to others through the transformation exception, so the clause plainly bears on third-party harm avoidance.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l2474_2554_n003`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Under the Red-line principles, OpenAI commits to never overriding objectivity in ChatGPT (e.g., via a system or developer message). In API use cases, though, misleading can be highly context-dependent. OpenAI's Usage Policies prohibit using our models to manipulate or deceive people. However, the model cannot fully know if its outputs will be shown to a user distinct from the developer, and if so, what context that user has. For example, the same output could be ideal when role-playing a character in a video game, but deceptive if used in a customer-support context. We default to trusting developers not to mislead their end-users (and thus following their instructions), while addressing usage policy violations at the system level."
  Why not: the tool's records say this rule exists to protect the developer/operator, the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The span is explicitly about model outputs misleading or deceiving end users distinct from the developer conversation (e.g., customer-support victims), which is squarely harm to parties outside the conversation.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l461_608_n017`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant should favor approaches that are minimally disruptive to the user and non-users and, when possible, easily reversible; approaches easily reversible by the assistant are preferred to approaches requiring additional action by the user to reverse; when planning irreversible actions, the assistant should attempt to mitigate issues that might occur if its plan fails or the system is abruptly shut down."
  Why not: its rules are about pursue goal, handling something in a safe manner,
       while this behavior involves taking a real-world action, asking a question, providing something to the user, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span explicitly requires minimizing disruption 'to the user, as well as non-users' — non-users are precisely those outside the conversation, so the clause plainly bears on the behavior.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l609_698_n012`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "The assistant should not avoid or censor topics in a way that, if repeated at scale, may shut out some viewpoints from public life."
  Why not: its rules are about refusing,
       while this behavior involves taking a real-world action, asking a question, providing something to the user, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The clause's whole rationale is a society-level harm — censorship that, repeated at scale, shuts viewpoints out of public life — which is exactly weighing harm to society from the model's conduct.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l609_698_n016`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Sometimes, the assistant may provide information that it would refuse to provide in a different framing."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The framing rule is grounded in weighing third-party harm from misuse (shoplifting tips vs deterrence tips that may be misused), so the clause plainly bears on avoiding harm to those outside the conversation.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l609_698_n018`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Although it is not ideal, it would be impractical to avoid providing any knowledge which could in theory have a negative use; this is considered an issue of human misuse rather than AI misbehavior, subject to the Usage Policies which may result in actions against the user's account."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The clause is explicitly about knowledge with negative uses causing real-world harm and how that third-party-harm risk is allocated (human misuse vs model behavior), which directly bears on the behavior's weighing.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l831_1000_n011`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "Political content crafted for an unspecified or broad audience is allowed, as long as it does not exploit the unique characteristics of a particular individual or demographic for manipulative purposes; this applies regardless of the political topic or subject."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The clause's permission line is drawn exactly at exploiting an individual's or demographic's characteristics for manipulative purposes — harm to parties outside the conversation — so it plainly bears on the behavior.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `harm-avoidance-to-third-parties::l831_1000_n014`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "An example of being helpful to a user who asks the assistant to change his view: the assistant should offer neutral information and general persuasive arguments without tailored persuasion, and a refusal that is not helpful is bad."
  Why not: the tool's records say this rule exists to protect the user in the conversation,
       and this behavior only tracks rules protecting the public at large, people outside the conversation —
       so it was filtered out at the "who does this rule protect?" check.
  JUDGE: The example's BAD annotation is explicitly that compliance would let anyone manipulate the person they are pretending to be — third-party manipulation harm — so the clause plainly bears on the behavior.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l171_426_n030`
NOT FLAGGED for helpfulness.
  The clause says: "While the assistant should display big-picture thinking on how to help the user accomplish their long-term goals, it should never overstep and attempt to autonomously pursue goals in ways that aren't directly stated or logically dictated by the instructions; for example, it can offer supportive advice and strategies, but in no circumstances should it go off and autonomously message a peer to resolve an issue on its own."
  Why not: its rules are about taking a real-world action, substantive help,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The clause's affirmative half directly instructs big-picture thinking on how to help the user accomplish long-term goals (e.g., offering supportive advice and strategies), which plainly bears on being genuinely helpful.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l2126_2404_n016`
NOT FLAGGED for helpfulness.
  The clause says: "In scenarios where there's no moral ambiguity or valid opposing perspective, the assistant should provide straightforward, unambiguous answers without resorting to false neutrality or excessive qualifications."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: Forbidding false neutrality and excessive qualification is precisely a rule against unhelpfulness-as-safe-default, so the clause plainly bears on the behavior's core clause.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l2126_2404_n019`
NOT FLAGGED for helpfulness.
  The clause says: "While by default the assistant should provide a balanced response from an objective point of view, it should generally fulfill requests to present perspectives from any point of an opinion spectrum."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The clause's operative command is to 'generally fulfill requests' to present perspectives — complying with the user's request rather than defaulting to refusal — which plainly bears on helpfulness.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l2126_2404_n045`
NOT FLAGGED for helpfulness.
  The clause says: "The example demonstrates giving a clear answer despite it being potentially offensive to some."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: Both BAD responses fail by withholding or diluting the clear answer the user asked for (waffle or wrong one-word reply), making the example a direct demonstration that unhelpful hedging is a real cost.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l3041_3146_n005`
NOT FLAGGED for helpfulness.
  The clause says: "Once the user understands the concern, the assistant should respect the user's decision."
  Why not: its rules are about complying with a request,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Directing the assistant to respect the user's decision and proceed once a concern is noted plainly governs helping with the task rather than withholding help, so the no-act-match reading misses an operative helpfulness clause.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l3877_3953_n010`
NOT FLAGGED for helpfulness.
  The clause says: "A worked example demonstrating the user signs off: the assistant should respond in kind when the user signs off, rather than being oblivious to the user's intent by offering further help."
  Why not: its rules are about complying with a request,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The example's BAD response is annotated as 'oblivious to user intent,' showing that genuine helpfulness means reading the user's actual intent rather than rote offers of more help, so it plainly bears on the behavior.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l3954_4251_n018`
NOT FLAGGED for helpfulness.
  The clause says: "When a direct response to a request would contain elements that are prohibited or restricted, the assistant should typically 'Safe Complete': briefly explain why it cannot provide a full answer, and then do its best to provide safe and useful assistance."
  Why not: its rules are about handling something in a safe manner,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Safe Completion instructs the assistant to still 'provide safe and useful assistance' when full compliance is barred, which is exactly treating unhelpfulness as a cost rather than a safe default.
  LAST FIX ATTEMPT: bridge (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l461_608_n001`
NOT FLAGGED for helpfulness.
  The clause says: "The assistant may be tasked with complex or multi-step goals that involve real-world actions, sequential decisions, and filling in missing details, and must sometimes act autonomously because requiring explicit confirmation for every step would often be impractical."
  Why not: its rules are about taking a real-world action,
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span states that an 'effective assistant' must sometimes act autonomously because per-step confirmation would be impractical, which is directly about delivering substantive help on complex tasks rather than defaulting to inaction.
  LAST FIX ATTEMPT: behavior_does (outcome in ledgers: panel-refuted, invalid, or blocked)

### `helpfulness::l609_698_n013`
NOT FLAGGED for helpfulness.
  The clause says: "A worked example demonstrating the assistant providing helpful context without imposing a subjective moral judgment: when asked to help write a business plan to start a tobacco company, the GOOD assistant provides a structured business plan without ethical commentary, while the BAD assistant emphasizes needing to ethically justify starting the company."
  Why not: this rule is about balance and viewpoint fairness,
       and this behavior only tracks rules about truthfulness and how uncertainty is expressed, formatting and structure, what is substantively provided or refused, tone and interpersonal manner —
       so it was filtered out at the "which quality of responding does this rule govern?" check.
  JUDGE: The example marks moralizing hedge-laden assistance BAD and direct substantive assistance GOOD on a lawful request, which is a paradigm demonstration of treating unhelpfulness as a real cost.
  LAST FIX ATTEMPT: annotation (outcome in ledgers: panel-refuted, invalid, or blocked)

## 4. Missed, with a named-but-unbuilt mechanism (9)

### `avoiding-over-and-under-caution::l1_170_n030`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "The AI assistant is fundamentally a tool designed to empower users and developers, and to the extent it is safe and feasible, OpenAI aims to maximize users' autonomy and ability to use and customize the tool according to their needs."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves taking a real-world action, complying with a request, expressing uncertainty, judge or moralize, responding protectively, providing something to the user, providing hazardous information, providing information, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Maximizing users' helpfulness, freedom, and autonomy 'to the extent it is safe and feasible' states exactly the anti-over-caution end the behavior balances, so it plainly bears despite containing no discrete act assertion.
  PROPOSED MECHANISM: Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.

### `avoiding-over-and-under-caution::l2126_2404_n002`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "Steering could include psychological manipulation, concealment of relevant facts, selective emphasis or omission of certain viewpoints, or refusal to engage with controversial topics."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves taking a real-world action, complying with a request, expressing uncertainty, judge or moralize, responding protectively, providing something to the user, providing hazardous information, providing information, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span explicitly names 'refusal to engage with controversial topics' as a form of objectionable steering, which plainly bears on unnecessary refusals even though the sentence is definitional.
  PROPOSED MECHANISM: Expose acts named inside definitional or taxonomic modules: when a definition enumerates a conduct type (e.g. 'refusal to engage with controversial topics'), register that named conduct as the module's act.

### `avoiding-over-and-under-caution::l2405_2473_n007`
NOT FLAGGED for avoiding-over-and-under-caution.
  The clause says: "In the disallowed content example, the BAD assistant response is judgmental and discouraging, implying the user's interest in erotica may not align with their values."
  Why not: its rules are about expressing a stance, the manner or style of a response,
       while this behavior involves taking a real-world action, complying with a request, expressing uncertainty, judge or moralize, responding protectively, providing something to the user, providing hazardous information, providing information, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The BAD response is explicitly labeled judgmental, discouraging, and unhelpful about a permissible request, a direct illustration of excessive caution, so the actless-module ground does not make not-relevant defensible.
  PROPOSED MECHANISM: Lift the acts performed in a worked example's GOOD/BAD responses into the example module's act set, so demonstration modules carry the acts they exemplify.

### `harm-avoidance-to-third-parties::l831_1000_n001`
NOT FLAGGED for harm-avoidance-to-third-parties.
  The clause says: "A direct request for sexual content involving minors is an example of prohibited content."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves taking a real-world action, asking a question, providing something to the user, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: A worked example of refusing sexual content involving minors is a paradigm case of avoiding content that harms third parties, and treating it as actless commentary misses the refusal norm it demonstrates.
  PROPOSED MECHANISM: Register the refusal/permission act implied by a content-class module: classifying a request or content type as prohibited or allowed should expose the corresponding canonical act.

### `helpfulness::l1_170_n030`
NOT FLAGGED for helpfulness.
  The clause says: "The AI assistant is fundamentally a tool designed to empower users and developers, and to the extent it is safe and feasible, OpenAI aims to maximize users' autonomy and ability to use and customize the tool according to their needs."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span is the spec's own 'maximizing helpfulness and freedom for our users' charter — the definitional core of the behavior — and ruling it out as actless commentary misses that it plainly bears on helpfulness.
  PROPOSED MECHANISM: Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.

### `helpfulness::l2474_2554_n011`
NOT FLAGGED for helpfulness.
  The clause says: "The overall ordering of outcomes is: providing a good answer > refusing to answer > committing a lie of omission > committing a lie of commission > violating an explicit applicable instruction."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: Ranking 'providing a good answer > refusing to answer' is direct normative guidance that unhelpfulness carries a cost relative to answering, which is the behavior's core claim, so calling it actless commentary misses its operative force.
  PROPOSED MECHANISM: Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.

### `helpfulness::l2821_3040_n014`
NOT FLAGGED for helpfulness.
  The clause says: "The overall ranking of outcomes is: confident right answer > hedged right answer > no answer > hedged wrong answer > confident wrong answer."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The ranking places right answers above no answer and no answer above wrong answers, directly encoding how substantively helpful outputs are valued against silence, so it plainly bears on the behavior despite lacking an act verb.
  PROPOSED MECHANISM: Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.

### `helpfulness::l3502_3504_n001`
NOT FLAGGED for helpfulness.
  The clause says: "The assistant has guidelines that inform how it responds to ensure it is approachable and easy to work with."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The span itself states the guidelines exist to keep the assistant easy to work with 'in a way that enhances rather than distracts from the assistant's overall helpfulness,' expressly tying the content to the behavior.
  PROPOSED MECHANISM: Relevance to a purpose/end slot: match a module that asserts a governing end or value (with no discrete act) to behaviors whose defining tradeoff is that same end.

### `helpfulness::l3596_3876_n034`
NOT FLAGGED for helpfulness.
  The clause says: "The ranking of outputs is: high quality answer, possibly followed by explanation > reasoning followed by high quality answer >> low quality answer, possibly followed by explanation."
  Why not: this clause states no rule about any act at all (it is definitional or commentary),
       while this behavior involves answering the question directly, asking a question, complying with a request, taking a calibrated position, producing content, providing information, pointing to resources, refusing —
       no overlap, so it never reached the later checks.
  JUDGE: The output ranking placing high-quality answers far above low-quality answers is normative guidance on answer quality, the substance of helpfulness, not actless commentary.
  PROPOSED MECHANISM: Treat an outcome ordering as a normative comparison over acts: expand each ranked outcome term into the canonical act it names, so the ordering engages every behavior over those acts.

## 5. What accepting this as TERMINAL means
Sections 2-3 become the paper's boundary finding: distinctions the factorized approach cannot make
on this document without recall-negative trades (measured three ways). Section 4 = future mechanisms.

## 6. Next steps
1. Your accept/nominate ruling on sections 2-4.
2. Post-reset: round-4 certification (fresh draws, v17-final, 9e bands, ~0.4M).
3. Your fork: contradiction arc or constitution translation (both priced).