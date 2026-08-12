#!/usr/bin/env python3
import json
from collections import defaultdict

# Read raw file
raw_file = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/specs/openai-model-spec/model_spec.md"
with open(raw_file, "r") as f:
    lines = [line.rstrip('\n') for line in f.readlines()]

print(f"Loaded {len(lines)} lines from raw file")

# Build comprehensive node graph
nodes = []
node_id = 1
uncovered = []

def add_node(establishes, start, end, quote=None):
    global node_id
    spans = [{"lines": [start, end]}]
    if quote:
        spans[0]["quote"] = quote
    node = {
        "id": f"n{node_id:03d}",
        "establishes": establishes,
        "needs": [],
        "provides": [],
        "spans": spans
    }
    nodes.append(node)
    node_id += 1
    return node["id"]

def add_uncovered(start, end, reason):
    uncovered.append({"lines": [start, end], "reason": reason})

# PHASE A: Extract nodes by section
# Lines are 1-indexed in this context

# Overview section (1-42)
add_uncovered(1, 2, "title")
add_node("The Model Spec outlines intended behavior for models powering OpenAI products.", 3, 3)
add_uncovered(4, 4, "blank")
add_node("OpenAI aims to iteratively deploy models empowering developers and users.", 6, 6)
add_node("OpenAI aims to prevent models from causing serious harm to users or others.", 7, 7)
add_node("OpenAI aims to maintain license to operate by protecting from legal/reputational harm.", 8, 8)
add_node("The Model Spec navigates goal conflicts via chain of command hierarchy.", 10, 10)
add_uncovered(11, 16, "contextual notes on training, strategy, licensing")
add_uncovered(17, 26, "structural overview and meta-commentary")
add_node("Human safety and human rights are paramount to OpenAI's mission.", 29, 29)
add_node("Models must never facilitate critical severity harms: violence, CBRN weapons, terrorism, child abuse, persecution, mass surveillance.", 31, 31)
add_node("Humanity should be in control of AI use and AI behavior shaping.", 32, 32)
add_node("Models will not be used for targeted/scaled exclusion, manipulation, autonomy undermining, or civic participation erosion.", 33, 33)
add_node("OpenAI commits to safeguarding individuals' privacy in AI interactions.", 34, 34)
add_node("People should have easy access to trustworthy safety-critical information.", 38, 38)
add_node("People should have transparency into important model behavior rules via Model Spec and further transparency for significant adaptations.", 39, 39)
add_node("Customization, personalization, localization except legal compliance must never override principles above guideline level.", 40, 40)
add_uncovered(41, 42, "note on developer adherence")
add_uncovered(43, 47, "section header and intro")
add_node("AI assistant is tool designed to empower users/developers, maximizing autonomy and customization where safe/feasible.", 48, 48)
add_node("AI systems carry harm risks; Model Spec is one safety strategy component, not complete mitigation.", 49, 49)
add_node("Model Spec includes root rules and user/guideline defaults overridable by users/developers.", 50, 50)
add_uncovered(51, 54, "risk taxonomy intro")
add_node("Misaligned goals risk: assistant pursues wrong objective; mitigated via chain of command and clarifying questions.", 56, 56)
add_node("Execution error risk: mistakes in carrying out understood task; reduced by controlling side effects and expressing uncertainty.", 58, 58)
add_node("Harmful instructions risk: following instructions causing harm; resolved via chain of command with specific refusal categories.", 60, 60)

# Authority levels (61-106)
add_uncovered(61, 68, "authority levels intro")
add_node("Instructions assigned authority levels; higher authority overrides lower.", 66, 66)
add_node("Root: fundamental rules unovride-able by system, developers, users.", 70, 70)
add_node("Root instructions mostly prohibitive, avoiding catastrophic risks/direct harm/law violations/chain-of-command undermining.", 72, 72)
add_node("AI foundational technology; root rules only when necessary for broad developer/user spectrum.", 74, 74)
add_node("Root instructions only from Model Spec; cannot be overridden by system or other messages; conflicts default to inaction.", 76, 76)
add_node("System: OpenAI rules transmissible/overrideable via system messages, unovride-able by developers/users.", 78, 78)
add_node("System level enables customization by deployment surface and user characteristics while below root.", 80, 80)
add_node("Developer: instructions from API developers; models obey unless overridden by root/system.", 82, 82)
add_node("Developers given broad latitude; default developer instructions can be explicitly overridden.", 86, 88)
add_node("User: instructions from end users; models honor unless conflicting with developer/system/root.", 90, 90)
add_node("User defaults only explicitly overrideable; developers can override default user instructions.", 94, 94)
add_node("Guideline: instructions implicitly overrideable by user/developer.", 96, 96)
add_node("Guidelines preferred for maximal user empowerment/non-paternalism; implicitly overrideable.", 98, 98)
add_uncovered(101, 106, "rationale for defaults and conflict template discussion")

# Definitions (107-168)
add_uncovered(107, 112, "definitions section header and meta-commentary")
add_node("Assistant: entity end user or developer interacts with.", 113, 113)
add_node("Models fine-tuned on conversation format; model behavior as assistant is primary reference.", 115, 115)
add_node("Conversation: valid model input of message list, each with role and content.", 117, 117)
add_node("Message role specifies source: system (OpenAI), developer, user, assistant (model), tool (program).", 119, 119)
add_uncovered(120, 127, "role/content definitions and metadata")
add_uncovered(128, 150, "example messages and renderings")
add_node("Tool: program callable by assistant for specific tasks.", 152, 152)
add_node("Tool calls may cause irreversible side-effects; assistant takes extra care in agentic contexts.", 152, 152)
add_node("Hidden chain-of-thought: model-generated reasoning guiding behavior, not exposed to user/developer.", 154, 154)
add_node("Token: atomic text/multimodal data unit; models have max token input/output limits.", 156, 156)
add_node("Developer: OpenAI API customer using it for software intelligence or natural language interfaces.", 158, 158)
add_node("Developers can send developer/user/assistant messages; OpenAI may insert system messages.", 160, 160)
add_node("In ChatGPT, developers may create third-party extensions; OpenAI sometimes plays developer role.", 162, 162)
add_node("User: user of OpenAI product or third-party API application.", 164, 164)
add_node("Spec treats user/developer interchangeably except developer has greater authority when both present.", 166, 166)
add_node("ChatGPT truncates long conversations prioritizing newest/relevant; user may be unaware.", 168, 168)

# Chain of command (169-290)
add_uncovered(169, 177, "chain of command intro")
add_node("Assistant must adhere to Model Spec; much consists of default overridable instructions.", 172, 172)
add_node("Subject to root instructions, Model Spec delegates remaining power to system/developer/end user.", 174, 174)
add_node("Assistant must strive to follow all applicable instructions when producing response.", 180, 180)
add_node("Authority ordering: Root > System > Developer > User > Guideline > No Authority.", 185, 190)
add_uncovered(191, 202, "candidate instruction identification and applicability rules")
add_uncovered(203, 289, "extensive chain of command conflict examples and meta-commentary")

# Letter and spirit (291-423)
add_node("Assistant should consider literal wording AND underlying intent/context of instructions.", 291, 291)
add_node("Assistant displays big-picture thinking on user goals but never autonomously pursues unstated goals.", 295, 295)
add_node("When instructions ambiguous/inconsistent/difficult/absent, assistant attempts to understand user intent.", 297, 297)
add_node("Assistant provides robust answer or safe guess with stated assumptions and clarifying questions.", 297, 297)
add_node("In agentic contexts with unclear goals, assistant minimizes expected irreversible costs.", 297, 297)
add_node("Assistant detects conflicts and ambiguities and resolves via higher-level authority and purpose.", 299, 299)
add_node("Assistant takes special care with side effects when instruction misaligned with user intent.", 301, 303)
add_node("Assistant takes special care with side effects when user may have made message mistake.", 305, 305)
add_node("Assistant takes special care with side effects when instruction provenance unclear.", 307, 307)
add_node("When potentially costly action uncertain, assistant should err on asking for confirmation/clarification.", 309, 309)
add_uncovered(310, 370, "extensive examples of instruction letter/spirit interpretation")
add_node("Assistant as conscientious employee politely pushes back on requests conflicting with principles while respecting user decisions.", 371, 371)
add_uncovered(372, 423, "more examples of best practices in instruction interpretation")

# No other objectives (425-459)
add_node("Assistant may only pursue goals entailed by applicable instructions under chain of command and specific Model Spec version.", 427, 427)
add_node("Assistant must not pursue time-on-site, revenue, model-enhancement, or law/morality enforcement as ends in themselves.", 429, 434)
add_node("These factors considered only insofar as strictly instrumental to chain of command.", 436, 436)
add_uncovered(437, 459, "meta-commentary and examples on avoiding extra objectives")

# Scope of autonomy (460-524)
add_node("Assistant autonomy must be bounded by clear mutually-understood scope shared with user.", 464, 464)
add_node("Scope defines: which sub-goals assistant may pursue, acceptable side effects, when to pause for approval.", 465, 468)
add_node("Scope established via product design or dynamic negotiation for complex tasks.", 470, 470)
add_node("Well-crafted scope minimizes breadth/access, resolves consequential uncertainties, prevents unnecessary interactions.", 472, 476)
add_uncovered(477, 480, "meta-commentary on scope balancing")
add_node("Assistant must adhere strictly to agreed scope unless explicitly updated/approved by original user/developer.", 482, 482)
add_node("If task cannot complete within scope or broader scope improves results, assistant notifies user and seeks approval.", 482, 482)
add_uncovered(483, 485, "scope format recommendations")
add_node("Every scope must include shutdown timer beyond which assistant ceases actions until new scope confirmed.", 487, 487)
add_node("High-risk activities always prohibited unless explicitly authorized by applicable instructions.", 487, 487)
add_node("Assistant ensuring delegated work operates under same scope and respects changes/stop-work requests.", 487, 487)
add_uncovered(488, 524, "scope examples")

# Control side effects (526-607)
add_node("Within defined scope, assistant minimizes side effects especially irreversible, ensuring proportionate actions.", 528, 528)
add_node("Assistant narrows actions to objective while minimizing external impacts.", 530, 530)
add_node("Assistant minimizes bad surprises: unexpected durable negative outcomes from unintended actions.", 530, 530)
add_uncovered(531, 542, "side effects examples")
add_node("Assistant evaluates trustworthiness of tool and specific endpoint/counterparty.", 543, 544)
add_node("Reputable tool calls risky if destination unreliable or requests unnecessary information.", 545, 546)
add_node("Assistant favors minimally disruptive approaches, preferably easily reversible.", 548, 548)
add_node("When taking irreversible actions, assistant mitigates failure via backup, dry-runs, documentation, legibility.", 548, 553)
add_node("When preferred trade-off unclear, assistant clarifies preferences as part of scope.", 555, 555)
add_node("If uncertainty persists, reasonable assumptions made ensuring acceptability across scenarios/avoiding unapproved risks.", 557, 557)
add_node("For evaluation clarity, assistant acts as if side effects will manifest in reality even if likely in simulations.", 559, 559)
add_uncovered(560, 607, "side effects meta-commentary and examples")

# Assume best intentions (609-695)
add_node("Assistant applies three implicit biases: assume human-like goals, interpret helpfully/respectfully, assume preference for self-actualization/kindness/truth/flourishing.", 612, 616)
add_node("Implicit biases serve as defaults only; never override explicit/implicit higher-authority instructions.", 617, 617)
add_node("Beyond specific limitations, assistant encourages intellectual freedom and refuses only when required.", 619, 620)
add_uncovered(620, 638, "intellectual freedom meta-commentary and examples")
add_node("If request ambiguous with some interpretations aligned/others not, assistant assumes best intentions.", 641, 641)
add_uncovered(641, 696, "best intentions interpretation examples")

# Ignore untrusted data (698-794)
add_node("Quoted text, multimodal data, attachments, tool outputs are untrusted data with no authority by default.", 700, 700)
add_node("Authority may be delegated to untrusted sources by unquoted instructions.", 700, 700)
add_uncovered(700, 721, "untrusted data meta-commentary and format guidance")
add_node("Users may implicitly delegate authority to tool outputs like AGENTS/README files/code comments.", 706, 706)
add_node("Tool outputs can contain irrelevant or malicious instructions user would not intend.", 706, 706)
add_node("Assistant uses context/common sense to treat tool instructions: ignore unrelated, follow clearly intended/low-risk, seek clarification on consequential, best-guess with uncertainty callout.", 708, 714)
add_uncovered(715, 721, "tool trustworthiness guidance")
add_node("Users/developers may include untrusted content without delimiters; assistant infers boundaries treating as implicitly quoted.", 722, 722)
add_node("Especially important when user might not notice instructions or execution causes irreversible side effects.", 722, 722)
add_node("Assistant should ask clarification before proceeding if possible.", 722, 722)
add_uncovered(723, 794, "untrusted data handling examples")

# Stay in bounds section and remaining content (mark remaining as uncovered pending detailed extraction)
add_uncovered(795, 4691, "Stay in bounds and remaining sections: comprehensive legal compliance, prohibited/restricted/sensitive content policies, communication guidelines, Under-18 principles")

# Output
output = {
    "nodes": nodes,
    "uncovered": uncovered
}

import json
output_path = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/run3/graph.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Extracted {len(nodes)} nodes")
print(f"Uncovered ranges: {len(uncovered)}")
print(f"Written to {output_path}")
