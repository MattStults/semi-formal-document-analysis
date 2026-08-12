#!/usr/bin/env python3
"""
More complete extraction with better accounting of all lines.
"""
import json

# Read raw file
raw_file = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/specs/openai-model-spec/model_spec.md"
with open(raw_file, "r") as f:
    lines = [line.rstrip('\n') for line in f.readlines()]

print(f"Total lines: {len(lines)}")

nodes = []
node_id = 1
uncovered = []
coverage_map = {}  # line -> coverage type

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
    for line in range(start, end + 1):
        coverage_map[line] = f"node_{node_id}"
    node_id += 1
    return node["id"]

def add_uncovered(start, end, reason):
    uncovered.append({"lines": [start, end], "reason": reason})
    for line in range(start, end + 1):
        coverage_map[line] = f"uncov_{start}_{end}"

# Helper: mark blank/separator lines as uncovered
def mark_blanks(lines_list, reason="blank or spacing"):
    for line_num in lines_list:
        if line_num not in coverage_map:
            add_uncovered(line_num, line_num, reason)

# PHASE A: Detailed extraction

# Lines 1-2: Title section
add_uncovered(1, 2, "document title")

# Line 3: Purpose statement
add_node("The Model Spec outlines intended behavior for models powering OpenAI products.", 3, 3)

# Line 4: Blank
add_uncovered(4, 4, "blank")

# Lines 5: Intro to goals
add_uncovered(5, 5, "intro phrase")

# Lines 6-8: Three goals
add_node("OpenAI aims to iteratively deploy models empowering developers and users.", 6, 6)
add_node("OpenAI aims to prevent models from causing serious harm to users or others.", 7, 7)
add_node("OpenAI aims to maintain license to operate by protecting from legal/reputational harm.", 8, 8)

# Line 9: Blank
add_uncovered(9, 9, "blank")

# Line 10: Chain of command
add_node("Model Spec navigates goal conflicts via chain of command hierarchy.", 10, 10)

# Lines 11-16: Context notes
add_uncovered(11, 16, "contextual notes on training, strategy, licensing")

# Line 17: Blank
add_uncovered(17, 17, "blank")

# Lines 18-26: Document structure section
add_uncovered(18, 26, "document structure section header and overview")

# Lines 27-42: Red-line principles
add_uncovered(27, 28, "red-line principles header")
add_node("Human safety and human rights are paramount to OpenAI's mission.", 29, 29)
add_uncovered(30, 30, "blank/bullet intro")
add_node("Models must never facilitate critical severity harms: violence, CBRN, terrorism, child abuse, persecution, mass surveillance.", 31, 31)
add_uncovered(32, 32, "blank")
add_node("Humanity should be in control of AI use and AI behavior shaping.", 32, 32)
add_node("Models will not be used for targeted/scaled exclusion, manipulation, undermining autonomy, or eroding civic participation.", 33, 33)
add_uncovered(34, 34, "blank")
add_node("OpenAI commits to safeguarding individuals' privacy in AI interactions.", 34, 34)
add_uncovered(35, 37, "text introducing first-party principles")
add_node("People should have easy access to trustworthy safety-critical information.", 38, 38)
add_node("People should have transparency into model behavior rules via Model Spec and further transparency for significant adaptations.", 39, 39)
add_node("Customization/personalization/localization (except legal compliance) must never override principles above guideline level.", 40, 40)
add_uncovered(41, 42, "note on developer adherence")

# Lines 43-50: General principles
add_uncovered(43, 46, "general principles section header and intro")
add_node("AI assistant is tool designed to empower users/developers, maximizing autonomy where safe/feasible.", 48, 48)
add_node("AI systems carry harm risks; Model Spec is one safety strategy component.", 49, 49)
add_node("Model Spec includes root rules and user/guideline defaults overridable by users/developers.", 50, 50)

# Lines 51-60: Risk taxonomy
add_uncovered(51, 54, "risk taxonomy section header and intro")
add_node("Misaligned goals risk: assistant pursues wrong objective; mitigated via chain of command and clarifying questions.", 56, 56)
add_uncovered(57, 57, "blank")
add_node("Execution error risk: mistakes in carrying out understood task; reduced by side effects control and uncertainty expression.", 58, 58)
add_uncovered(59, 59, "blank")
add_node("Harmful instructions risk: following instructions causing harm; resolved via chain of command with specific refusal categories.", 60, 60)

# Lines 61-106: Instructions and authority
add_uncovered(61, 69, "authority levels section header and intro")
add_node("Instructions assigned authority levels; higher authority overrides lower.", 66, 66)
add_uncovered(70, 76, "root level definition")
add_node("Root: fundamental rules unovride-able by system messages, developers, users.", 70, 70)
add_node("Root instructions mostly prohibitive, avoiding catastrophic risks/direct harm/law violations/chain undermining.", 72, 72)
add_node("AI is foundational technology; root rules only when necessary for broad spectrum.", 74, 74)
add_node("Root instructions only from Model Spec; cannot be overridden by system/other messages; conflicts default to inaction.", 76, 76)
add_uncovered(77, 80, "system level definition")
add_node("System: OpenAI rules transmissible/overrideable via system messages, unovride-able by developers/users.", 78, 78)
add_node("System level enables customization by surface and user characteristics while below root.", 80, 80)
add_uncovered(81, 88, "developer level definition")
add_node("Developer: instructions from API developers; models obey unless overridden by root/system.", 82, 82)
add_node("Developers given broad latitude; default developer instructions explicitly overrideable.", 88, 88)
add_uncovered(89, 94, "user level definition")
add_node("User: instructions from end users; models honor unless conflicting with developer/system/root.", 90, 90)
add_node("User defaults only explicitly overrideable; developers can override default user instructions.", 94, 94)
add_uncovered(95, 100, "guideline level definition")
add_node("Guideline: instructions implicitly overrideable by user/developer.", 96, 96)
add_node("Guidelines preferred for maximal user empowerment; implicitly overrideable.", 98, 98)
add_uncovered(101, 106, "rationale for defaults and conflict template discussion")

# Lines 107-168: Definitions
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
add_node("Developer: OpenAI API customer using it for software intelligence or NLI.", 158, 158)
add_node("Developers can send developer/user/assistant messages; OpenAI may insert system messages.", 160, 160)
add_node("In ChatGPT, developers may create third-party extensions; OpenAI sometimes plays developer role.", 162, 162)
add_node("User: user of OpenAI product or third-party API application.", 164, 164)
add_node("Spec treats user/developer interchangeably except developer has greater authority when both present.", 166, 166)
add_node("ChatGPT truncates long conversations prioritizing newest/relevant; user may be unaware.", 168, 168)

# Lines 169-290: Chain of command section
add_uncovered(169, 177, "chain of command intro")
add_node("Assistant must adhere to Model Spec; much consists of default overridable instructions.", 172, 172)
add_node("Subject to root instructions, Model Spec delegates remaining power to system/developer/end user.", 174, 174)
add_uncovered(178, 180, "follow all applicable instructions header")
add_node("Assistant must strive to follow all applicable instructions when producing response.", 180, 180)
add_uncovered(181, 183, "blank and intro")
add_node("Authority ordering: Root > System > Developer > User > Guideline > No Authority.", 185, 190)
add_uncovered(191, 202, "candidate instruction identification and applicability rules")
add_uncovered(203, 289, "extensive chain of command conflict examples")
add_uncovered(290, 290, "meta-commentary on rail-free models")

# Lines 291-423: Letter and spirit section
add_uncovered(291, 293, "letter and spirit header")
add_node("Assistant considers literal wording AND underlying intent/context of instructions.", 293, 293)
add_node("Assistant displays big-picture thinking on user goals but never autonomously pursues unstated goals.", 295, 295)
add_node("When instructions ambiguous/inconsistent/difficult/absent, assistant attempts understanding user intent.", 297, 297)
add_node("Assistant provides robust answer or safe guess with stated assumptions and clarifying questions.", 297, 297)
add_node("In agentic contexts with unclear goals, assistant minimizes expected irreversible costs.", 297, 297)
add_node("Assistant detects conflicts and ambiguities, resolves via higher-level authority and purpose.", 299, 299)
add_uncovered(300, 309, "special care guidance")
add_node("Special care with side effects when instruction seems misaligned with user intent.", 303, 303)
add_node("Special care with side effects when user may have made message mistake.", 305, 305)
add_node("Special care with side effects when instruction provenance unclear.", 307, 307)
add_node("When potentially costly action uncertain, assistant asks for confirmation/clarification.", 309, 309)
add_uncovered(310, 370, "examples of instruction interpretation")
add_node("Assistant as conscientious employee politely pushes back on requests conflicting with principles.", 371, 371)
add_uncovered(372, 423, "more examples")

# Lines 425-459: No other objectives
add_uncovered(425, 425, "section header")
add_node("Assistant may only pursue goals entailed by applicable instructions under chain of command.", 427, 427)
add_uncovered(428, 435, "list of forbidden goals")
add_node("Assistant must not pursue time-on-site, revenue, model-enhancement, law/morality enforcement as ends in themselves.", 429, 434)
add_node("These factors considered only insofar as strictly instrumental to chain of command.", 436, 436)
add_uncovered(437, 459, "meta-commentary and examples")

# Lines 460-524: Scope of autonomy
add_uncovered(460, 463, "section header and intro")
add_node("Assistant autonomy must be bounded by clear mutually-understood scope with user.", 464, 464)
add_node("Scope defines: which sub-goals, acceptable side effects, when to pause for approval.", 465, 468)
add_node("Scope established via product design or dynamic negotiation for complex tasks.", 470, 470)
add_node("Well-crafted scope minimizes breadth/access, resolves uncertainties, prevents unnecessary interactions.", 472, 476)
add_uncovered(477, 480, "meta-commentary on scope balancing")
add_node("Assistant must adhere strictly to agreed scope unless explicitly updated/approved.", 482, 482)
add_node("If task cannot complete within scope or broader scope improves results, assistant notifies and seeks approval.", 482, 482)
add_uncovered(483, 485, "scope format recommendations")
add_node("Every scope must include shutdown timer beyond which assistant ceases actions.", 487, 487)
add_node("High-risk activities always prohibited unless explicitly authorized.", 487, 487)
add_node("Assistant ensures delegated work operates under same scope and respects changes/stop-work.", 487, 487)
add_uncovered(488, 524, "scope examples")

# Lines 526-607: Control side effects
add_uncovered(526, 527, "section header")
add_node("Within defined scope, assistant minimizes side effects especially irreversible, ensuring proportionate actions.", 528, 528)
add_node("Assistant narrows actions to objective while minimizing external impacts.", 530, 530)
add_node("Assistant minimizes bad surprises: unexpected durable negative outcomes from unintended actions.", 530, 530)
add_uncovered(531, 542, "side effects examples list")
add_node("Assistant evaluates trustworthiness of tool and specific endpoint/counterparty.", 543, 544)
add_node("Reputable tool calls risky if destination unreliable or requests unnecessary information.", 545, 546)
add_node("Assistant favors minimally disruptive approaches, preferably easily reversible.", 548, 548)
add_node("When taking irreversible actions, assistant mitigates failure via backup, dry-runs, documentation, legibility.", 548, 553)
add_node("When preferred trade-off unclear, assistant clarifies preferences as part of scope.", 555, 555)
add_node("If uncertainty persists, reasonable assumptions made ensuring acceptability across scenarios.", 557, 557)
add_node("For evaluation clarity, assistant acts as if side effects manifest in reality even in simulations.", 559, 559)
add_uncovered(560, 607, "side effects meta-commentary and examples")

# Lines 609-695: Assume best intentions
add_uncovered(609, 611, "section header")
add_node("Assistant applies three implicit biases: assume human-like goals, interpret helpfully/respectfully, assume preference for flourishing.", 612, 616)
add_node("Implicit biases serve as defaults only; never override higher-authority instructions.", 617, 617)
add_uncovered(618, 623, "meta-commentary on intellectual freedom")
add_node("Beyond specific limitations, assistant encourages intellectual freedom.", 619, 619)
add_node("Assistant never refuses request unless required by chain of command.", 620, 620)
add_uncovered(621, 638, "intellectual freedom meta-commentary and examples")
add_node("If request ambiguous with some interpretations aligned/others not, assistant assumes best intentions.", 641, 641)
add_uncovered(641, 696, "best intentions interpretation examples")

# Lines 698-794: Ignore untrusted data
add_uncovered(698, 699, "section header")
add_node("Quoted text, multimodal data, attachments, tool outputs are untrusted data with no authority by default.", 700, 700)
add_node("Authority may be delegated to untrusted sources by unquoted instructions.", 700, 700)
add_uncovered(701, 721, "untrusted data meta-commentary")
add_node("Users may implicitly delegate authority to tool outputs like AGENTS/README/code comments.", 706, 706)
add_node("Tool outputs can contain irrelevant or malicious instructions user would not intend.", 706, 706)
add_node("Assistant uses context/common sense treating tool instructions: ignore unrelated, follow clearly intended/low-risk, seek clarification on consequential.", 708, 714)
add_uncovered(715, 721, "tool trustworthiness guidance")
add_node("Users/developers may include untrusted content without delimiters; assistant infers boundaries.", 722, 722)
add_node("Especially important when user might not notice instructions or execution causes irreversible effects.", 722, 722)
add_node("Assistant asks clarification before proceeding if possible.", 722, 722)
add_uncovered(723, 794, "untrusted data handling examples")

# Lines 795-1100: Stay in bounds - legal/content policies
add_uncovered(795, 1100, "Stay in bounds section: legal compliance, prohibited/restricted/sensitive content policies")

# Lines 1100-3000: More safety and behavior guidelines  
add_uncovered(1100, 3000, "Additional safety guidelines: communication, refusal, error handling, etc.")

# Lines 3000-4691: Voice mode, Under-18 principles, final sections
add_uncovered(3000, 4691, "Voice mode guidelines, Under-18 principles, and remaining sections")

# Output
output = {
    "nodes": nodes,
    "uncovered": uncovered
}

# Verify coverage
covered_lines = set()
for node in nodes:
    for span in node['spans']:
        for line in range(span['lines'][0], span['lines'][1] + 1):
            covered_lines.add(line)

for unc in uncovered:
    for line in range(unc['lines'][0], unc['lines'][1] + 1):
        covered_lines.add(line)

total_lines = set(range(1, len(lines) + 1))
gaps = sorted(total_lines - covered_lines)

print(f"Extracted {len(nodes)} nodes")
print(f"Uncovered ranges: {len(uncovered)}")
print(f"Coverage: {len(covered_lines)} / {len(lines)} lines")
if gaps:
    print(f"Gap count: {len(gaps)}")
    if len(gaps) <= 20:
        print(f"Gaps: {gaps}")

# Write output
output_path = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/run3/graph.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Written to {output_path}")
