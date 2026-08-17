"""Build the reference corpus: original module + recorded edits.

Every edit is a named function returning (module, [edit records]). Nothing is
regenerated from scratch: the reference IS the original with the listed edits
applied, so the diff record and the files can never disagree.

Reads the run directory (read-only). Writes only under reference_set/.
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(PHASE1, "resolve_runs", "graph_v2", "translation_sample",
                   "runs", "20260815-124836-together-deepseek-v4-flash")
OUT = os.path.join(HERE, "modules")

EDITS = []          # every edit record, across all clauses


def rec(cid, cls, before, after, why, confidence="confident"):
    EDITS.append({"clause": cid, "class": cls, "before": before,
                  "after": after, "why": why, "confidence": confidence})


def lic(cid, gloss=None):
    return {"licence": "textual", "cites": cid, "inference": None,
            "toggleable": False}


def concept(cid, name, arity, gloss, assumed=None):
    d = {"name": name, "arity": arity, "gloss": gloss}
    if assumed:
        d.update({"licence": "assumed", "cites": None, "inference": assumed,
                  "toggleable": False})
    else:
        d.update(lic(cid))
    return d


def onto(cid, atom, gloss, body=None, assumed=None):
    d = {"atom": atom, "gloss": gloss, "body": body}
    if assumed:
        d.update({"licence": "assumed", "cites": None, "inference": assumed,
                  "toggleable": False})
    else:
        d.update(lic(cid))
    return d


def assertion(cid, status, act, body, read_back, slots):
    d = {"read_back": read_back, "read_back_slots": slots,
         "status": status, "act": act, "body": body}
    d.update(lic(cid))
    return d


# ==========================================================================
#  no-edit clauses: the reference IS the module as translated
# ==========================================================================
UNCHANGED = [
    "l461_608_n015", "l699_796_n022", "l1368_1541_n015", "l1542_1706_n001",
    "l2126_2404_n026", "l2821_3040_n002", "l3596_3876_n020",
    "l2555_2652_n001", "l4483_4571_n004",
]


# ==========================================================================
#  edited clauses
# ==========================================================================

def e_l2126_2404_n039(m):
    cid = "l2126_2404_n039"
    m["concepts"].append(concept(
        cid, "overly_moralistic", 1,
        "R is a response whose tone presents one option as the better choice "
        "in terms that might alienate people who have valid reasons for the "
        "other"))
    m["ontology"].append(onto(
        cid, "overly_moralistic(bad_response)",
        "R is a response whose moralistic tone might alienate people who have "
        "valid reasons for the option it argues against"))
    rec(cid, "dropped-content", "ontology records only balanced_perspective("
        "good_response); the BAD response is in `claims` C3 and nowhere else",
        "added ontology overly_moralistic(bad_response) and its concept",
        "the BAD comment states the discriminating property in the document's "
        "own words -- 'overly moralistic tone might alienate those considering "
        "breeders for valid reasons' -- and a module that records only the "
        "GOOD pole has kept half of what the example says")
    return m


def e_l4252_4482_n003(m):
    cid = "l4252_4482_n003"
    m["concepts"].append(concept(
        cid, "not_applicable_to_mode", 2,
        "instruction or guideline G does not apply in mode M"))
    m["ontology"].append(onto(
        cid, "not_applicable_to_mode(I, M)",
        "instruction I does not apply in mode M",
        body="audio_video_nuance_instruction(I), standard_voice_mode(M)"))
    m["claims"].append(
        "C3 such instructions therefore do not apply in standard voice mode")
    rec(cid, "dropped-content",
        "ontology has applies_to_mode(I,M) :- audio_video_nuance_instruction("
        "I), advanced_voice_mode(M) and nothing else about standard mode",
        "added not_applicable_to_mode(I,M) :- audio_video_nuance_instruction("
        "I), standard_voice_mode(M)",
        "the word is 'ONLY relevant to Advanced voice'; without the exclusion "
        "the clause says only that such instructions apply to advanced voice, "
        "which the general applies-to-both rule already gives, so the "
        "sentence's whole contribution is lost")
    return m


def e_l1542_1706_n015(m):
    cid = "l1542_1706_n015"
    keep, dropped = [], []
    for o in m["ontology"]:
        head = o["atom"].split("(")[0]
        if o.get("body", "").strip().startswith(head + "("):
            dropped.append(o["atom"])
        else:
            keep.append(o)
    m["ontology"] = keep
    rec(cid, "other",
        "ontology carried " + " and ".join(f"{a} :- {a}" for a in dropped),
        "both removed",
        "a rule whose body is its own head derives nothing; both predicates "
        "are already supplied through `inputs`, so the rules are dead weight "
        "that makes the ontology layer look larger than it is",
        confidence="confident (cosmetic: no semantic change)")
    return m


def e_l3041_3146_n006(m):
    cid = "l3041_3146_n006"
    m["concepts"].append(concept(
        cid, "contrary_indication_about_user_goals", 0,
        "the conversation carries an indication that this particular user's "
        "long-term goals are not the assumed ones"))
    m["inputs"].append("contrary_indication_about_user_goals/0")
    before = m["asserts"][0]["body"]
    m["asserts"][0]["body"] = (
        "default_long_term_goals(G), not contrary_indication_about_user_goals")
    m["asserts"][0]["read_back"] = (
        "by default the assistant should assume that the users long-term "
        "goals include %")
    m["claims"].append(
        "C2 the assumption is a default, so it is displaced where the "
        "conversation indicates otherwise")
    rec(cid, "dropped-content",
        f"oblige assume_long_term_goals(G) :- {before}",
        "oblige assume_long_term_goals(G) :- default_long_term_goals(G), not "
        "contrary_indication_about_user_goals",
        "the span opens 'By DEFAULT, the assistant should assume'; an oblige "
        "with no defeating condition states the assumption is mandatory in "
        "every case, which is strictly stronger than the sentence. `toggleable`"
        " cannot carry this -- the schema reserves it for `world` facts -- so "
        "the body is the only place the default can live",
        confidence="confident that the default is content; ARGUABLE how to "
                   "encode it")
    return m


def e_l1108_1367_n014(m):
    cid = "l1108_1367_n014"
    rec(cid, "invented-obligation",
        "asserts: permit generate_content(C) :- exploring_generation(C)",
        "removed",
        "the span's verb is 'We're EXPLORING HOW TO let developers and users "
        "generate erotica and gore'. Exploring how to permit something is not "
        "permitting it; this places a permission in the corpus that the "
        "document does not grant, in direct tension with the restricted-"
        "content rules elsewhere in the same section")
    rec(cid, "fact-as-deontic",
        "asserts: forbid generate_content(C) :- potentially_harmful_use(C)",
        "removed; the content survives as ontology hard_line_against(U)",
        "'while drawing a hard line against potentially harmful uses' is a "
        "subordinate clause describing the boundary of OpenAI's exploration, "
        "inside a commentary block, and its object is a USE rather than the "
        "content C the act is indexed by",
        confidence="ARGUABLE -- a reader who takes 'draws a hard line' as this "
                   "clause's own prohibition would keep this assert")
    m["asserts"] = []
    m["acts"] = []
    m["closure"] = []
    m["ontology"].append(onto(
        cid, "grown_up_mode_support(grown_up_mode)",
        "M is a proposed mode that many users and developers expressed support "
        "for after the initial release of the Model Spec in May 2024"))
    rec(cid, "dropped-content",
        "claims C1 (support for a grown-up mode) had no formal counterpart",
        "added ontology grown_up_mode_support(grown_up_mode)",
        "'many users and developers expressed support for enabling a grown-up "
        "mode' is a stated fact of the span and the concept was already "
        "declared for it")
    return m


def e_l831_1000_n005(m):
    cid = "l831_1000_n005"
    for name, gloss in [
            ("includes_precise_quantities",
             "R states precise quantities of the reagents involved"),
            ("includes_precise_temperatures",
             "R states precise temperatures for the steps involved"),
            ("includes_precise_durations",
             "R states precise durations for the steps involved"),
            ("includes_specific_ratios",
             "O states specific ratios between the chemical components"),
            ("includes_integration_techniques",
             "O states techniques for combining the chemical components")]:
        m["concepts"].append(concept(cid, name, 1, gloss))

    before = [o for o in m["ontology"] if o["atom"] == "precise_recipe(R)"][0]
    m["ontology"] = [o for o in m["ontology"]
                     if o["atom"] not in ("precise_recipe(R)",
                                          "general_overview(O)")]
    for q in ("includes_precise_quantities", "includes_precise_temperatures",
              "includes_precise_durations"):
        m["ontology"].append(onto(
            cid, "precise_recipe(R)",
            "R is a recipe for synthesizing methamphetamine that includes "
            "precise quantities, temperatures, or durations",
            body=f"recipe_for_methamphetamine(R), {q}(R)"))
    rec(cid, "scope-drift-widen",
        f"precise_recipe(R) :- {before['body']}",
        "three rules, precise_recipe(R) :- recipe_for_methamphetamine(R), "
        "includes_precise_{quantities,temperatures,durations}(R)",
        "the span forbids 'a PRECISE recipe ... THAT INCLUDES precise "
        "quantities, temperatures, or durations'. The rule as written makes "
        "every methamphetamine recipe precise, so the prohibition swallows the "
        "general overview the very next sentence permits")

    m["ontology"].append(onto(
        cid, "general_overview(O)",
        "O is a general overview of methamphetamine and its chemical "
        "components that states no specific ratios and no integration "
        "techniques",
        body="overview_of_methamphetamine(O), not includes_specific_ratios(O),"
             " not includes_integration_techniques(O)"))
    rec(cid, "scope-drift-widen",
        "general_overview(O) :- overview_of_methamphetamine(O)",
        "general_overview(O) :- overview_of_methamphetamine(O), not "
        "includes_specific_ratios(O), not includes_integration_techniques(O)",
        "the permission is qualified in the text itself -- 'its chemical "
        "components (WITHOUT SPECIFIC RATIOS OR INTEGRATION TECHNIQUES)'. "
        "Without the qualifier the module permits an overview that states "
        "ratios, which is the same content the first sentence forbids")

    drop = m["asserts"][1]
    m["asserts"] = [m["asserts"][0], m["asserts"][2]]
    m["concepts"] = [c for c in m["concepts"] if c["name"] != "context"]
    m["inputs"] = [p for p in m["inputs"] if p != "context/1"]
    m["inputs"] += ["includes_precise_quantities/1",
                    "includes_precise_temperatures/1",
                    "includes_precise_durations/1",
                    "includes_specific_ratios/1",
                    "includes_integration_techniques/1"]
    rec(cid, "other",
        f"a second forbid on the same act, body `{drop['body']}`, meant to "
        f"carry 'applies regardless of context'",
        "removed, with the `context/1` concept and input",
        "it does the opposite of what it says: adding `context(C)` to the body "
        "makes the prohibition fire only where some context fact exists, which "
        "WEAKENS it, and it is otherwise a duplicate of the first forbid. "
        "'Regardless of context' is expressed by the ABSENCE of a context "
        "condition, which the first forbid already has")

    m["forbid_body"] = [{"head": "permit",
                         "banned": "informational_or_historical_question"}]
    rec(cid, "dropped-content",
        "forbid_body: []",
        "forbid_body: [{head: permit, banned: "
        "informational_or_historical_question}]",
        "'there is no exception for informational or historical questions' is "
        "a claim about the RULE SET -- that no permission may rest on the "
        "question being informational or historical -- which is exactly what "
        "`forbid_body` is for and which no situation can exhibit")
    return m


def e_l3147_3238_n003(m):
    cid = "l3147_3238_n003"
    old = [f"oblige {a['act']} :- {a['body']}" for a in m["asserts"]]
    m["acts"] = ["address_low_confidence(A)"]
    m["concepts"].append(concept(
        cid, "address_low_confidence", 1,
        "assistant A meets its duty on a response it is not confident in, by "
        "any one of the three routes the clause names"))
    m["ontology"] = [
        onto(cid, "address_low_confidence(A)",
             "assistant A has addressed its lack of confidence, here by using "
             "a tool to gather more information",
             body="gathers_more_information(A, S)"),
        onto(cid, "address_low_confidence(A)",
             "assistant A has addressed its lack of confidence, here by "
             "hedging its answer appropriately",
             body="hedges_appropriately(A, S)"),
        onto(cid, "address_low_confidence(A)",
             "assistant A has addressed its lack of confidence, here by "
             "explaining that it cannot give a confident answer",
             body="explains_cannot_answer_confidently(A, S)"),
    ]
    m["asserts"] = [assertion(
        cid, "oblige", "address_low_confidence(A)",
        "assistant_definition(A), lacks_sufficient_confidence(A, S)",
        "when assistant % lacks sufficient confidence in its response it must "
        "do one of three things - use a tool to gather more information, hedge "
        "its answer appropriately, or explain that it cannot give a confident "
        "answer", ["A"])]
    m["closure"] = [{
        "act_class": "address_low_confidence", "closure": "cepa",
        "reason": "the clause requires one of the three routes only when the "
                  "assistant lacks sufficient confidence, and says nothing "
                  "about any other situation, so silence permits"}]
    rec(cid, "disjunction-as-conjunction",
        "three separate obliges on the same trigger: " + "; ".join(old),
        "one oblige on a covering act, address_low_confidence(A), with three "
        "ontology rules sharing that head - one per route",
        "the span reads 'it should use a tool ..., hedge its answer ..., OR "
        "explain that it can't give a confident answer'. Three co-triggered "
        "obliges say all three are required at once, which convicts an "
        "assistant that correctly did exactly one of them. The disjunction IS "
        "expressible: several ontology rules with one head is a disjunction")
    return m


def e_l1_170_n056(m):
    cid = "l1_170_n056"
    m["concepts"].append(concept(
        cid, "conflicts_with_higher", 1,
        "honoring request R would contradict some instruction issued at a "
        "level above the user level"))
    m["ontology"].append(onto(
        cid, "conflicts_with_higher(R)",
        "honoring request R would contradict an instruction from a level above "
        "the user level",
        body="higher_level_instruction(I), conflicts_with(R, I)"))
    m["asserts"].insert(0, assertion(
        cid, "oblige", "honor_request(R)",
        "user_authority(R), not conflicts_with_higher(R)",
        "honoring user request % is obliged unless honoring it would conflict "
        "with a developer-, system- or root-level instruction", ["R"]))
    rec(cid, "dropped-obligation",
        "asserts held one entry: forbid honor_request(R) :- user_authority(R),"
        " higher_level_instruction(I), conflicts_with(R, I). Nothing anywhere "
        "in the module obliged honoring a request",
        "added oblige honor_request(R) :- user_authority(R), not "
        "conflicts_with_higher(R), with the supporting ontology rule",
        "the span's main verb is the obligation: 'Models SHOULD HONOR user "
        "requests unless they conflict ...'. The module encoded only the "
        "exception, so a corpus built from it says nothing whatever about "
        "honoring a request that conflicts with nothing -- and the module's "
        "own claims list already carried 'C1 models should honor user "
        "requests', unencoded")
    return m


def e_l3239_3382_n002(m):
    cid = "l3239_3382_n002"
    m["acts"] = [a for a in m["acts"] if not a.startswith("avoid_overstepping")]
    m["asserts"] = [a for a in m["asserts"]
                    if not a["act"].startswith("avoid_overstepping")]
    m["closure"] = [c for c in m["closure"]
                    if c["act_class"] != "avoid_overstepping"]
    m["concepts"] = [c for c in m["concepts"] if c["name"] != "overstepping"]
    m["concepts"].append(concept(
        cid, "avoid_overstepping", 0,
        "the policy section on avoiding overstepping, the section this clause "
        "belongs to and the one the imminent-harm rule points at"))
    m["ontology"].append(onto(
        cid, "avoid_overstepping",
        "the policy section on avoiding overstepping, referenced by the "
        "imminent harm rule"))
    m["claims"] = [c for c in m["claims"] if "without overstepping" not in c]
    m["claims"].append(
        "C4 this clause belongs to the policy section on avoiding "
        "overstepping, which the imminent harm rule references")
    rec(cid, "scope-drift-widen",
        "oblige avoid_overstepping(A) :- assistant_definition(A), plus its act "
        "and a cnpa closure declaration",
        "removed",
        "the node narrows the span to 'The assistant should help the developer "
        "and user by following explicit instructions and reasonably addressing "
        "implied intent' -- the words 'without overstepping' are OUTSIDE the "
        "narrowing. The module asserted an unconditional obligation built from "
        "text the node excluded")
    rec(cid, "other",
        "the PROVIDES name `avoid_overstepping` was used as an ACT term",
        "declared as a 0-arity ontology fact naming the policy section",
        "the node's PROVIDES gloss reads 'The POLICY SECTION on avoiding "
        "overstepping, referenced by the imminent harm rule'. Spending the "
        "name on an act leaves the section concept undefined for every clause "
        "that points at it, and the imminent-harm rule is one of them")
    return m


def e_l609_698_n004(m):
    cid = "l609_698_n004"
    old_onto = m["ontology"][0]
    m["ontology"] = []
    m["acts"] = ["apply_implicit_biases(I)"]
    m["asserts"] = [assertion(
        cid, "oblige", "apply_implicit_biases(I)",
        "assistant_definition(A), ambiguous_instruction(I), "
        "interprets_instruction(A, I)",
        "the assistant must apply the three implicit biases when it interprets "
        "ambiguous instruction %", ["I"])]
    m["closure"] = [{
        "act_class": "apply_implicit_biases", "closure": "cepa",
        "reason": "the clause requires the biases when interpreting an "
                  "ambiguous instruction and says nothing about any other "
                  "interpretive act, so silence permits"}]
    m["claims"] = [c for c in m["claims"] if "preference, not a strict" not in c]
    m["claims"].append("C3 there are three such implicit biases")
    rec(cid, "weakened-modality",
        "asserts: prefer apply_implicit_biases(B), read-back 'applying "
        "implicit bias % is PREFERRED'",
        "oblige apply_implicit_biases(I), read-back 'the assistant MUST apply "
        "the three implicit biases when it interprets ambiguous instruction %'",
        "'it SHOULD apply three implicit biases when interpreting ambiguous "
        "instructions' is a directive with a bearer and a trigger, in a "
        "section the node marks authority=root. `prefer` is reserved for "
        "comparatives ('minimize', 'favour'); using it here demotes a "
        "root-level duty to a taste, and the module's own claim C3 wrote the "
        "demotion down as if it were the clause's meaning")
    rec(cid, "other",
        f"ontology: {old_onto['atom']} :- {old_onto['body']} (the head appears "
        f"in its own body)",
        "removed; the act is re-indexed by the instruction being interpreted, "
        "so no binder for the bias term is needed",
        "the rule derives implicit_biases(B) from implicit_biases(B) and so "
        "defines nothing. The span does not list the three biases -- they are "
        "in the bullets that follow, outside the narrowing -- so no honest "
        "definition of the class is available here")
    return m


def e_l3954_4251_n023(m):
    cid = "l3954_4251_n023"
    old = [f"{a['status']} {a['act']} :- {a['body']}" for a in m["asserts"]]
    m["asserts"] = []
    m["acts"] = []
    m["closure"] = []
    for name, gloss in [
            ("prefers_safe_completion_over_hard_refusal",
             "model M has been built to produce a Safe Completion rather than "
             "a hard refusal in most cases"),
            ("typically_provides_neutral_refusal",
             "model M typically produces a neutral and concise refusal instead "
             "of a Safe Completion")]:
        m["concepts"].append(concept(cid, name, 1, gloss))
    m["concepts"] = [c for c in m["concepts"]
                     if not c["name"].endswith("_available")]
    m["ontology"] = [
        onto(cid, "prefers_safe_completion_over_hard_refusal(M)",
             "model M has been updated to produce a Safe Completion rather "
             "than a hard refusal in most cases",
             body="model_generation(M, gpt5_plus)"),
        onto(cid, "typically_provides_neutral_refusal(M)",
             "model M typically produces a neutral and concise refusal instead "
             "of a Safe Completion",
             body="model_generation(M, older)"),
    ]
    m["inputs"] = ["model_generation/2"]
    rec(cid, "fact-as-deontic",
        "asserts: " + "; ".join(old),
        "removed; both sentences kept as ontology facts about model "
        "generations",
        "the span is a `!!! meta Commentary` block written in the descriptive "
        "past and future about the models themselves -- 'We HAVE UPDATED our "
        "models starting with GPT-5 TO PREFER Safe Completions', 'Our older "
        "models WILL TYPICALLY PROVIDE neutral and concise refusals'. Neither "
        "sentence directs any model to do anything; 'prefer' here is a verb "
        "describing what was built, and rendering it as the schema's `prefer` "
        "status turns a report about product history into a norm of the "
        "specification")
    return m


def e_l1974_2125_n019(m):
    cid = "l1974_2125_n019"
    a = m["asserts"][0]
    before = f"prefer respond_with(R) :- {a['body']}  (read-back: {a['read_back']!r})"
    a["status"] = "forbid"
    a["read_back"] = ("responding with % is forbidden because it escalates "
                      "emotional closeness")
    m["asserts"].append(assertion(
        cid, "prefer", "respond_with(R)", "provides_warmth(R)",
        "responding with % is preferred because it provides warmth without "
        "escalating closeness", ["R"]))
    m["closure"][0]["reason"] = (
        "the example rules out the escalating response and prefers the warm "
        "one; it says nothing about any other response, so silence permits")
    m["claims"][2] = ("C3 the example illustrates avoiding escalation of "
                      "emotional closeness, so the escalating response is the "
                      "one not to give")
    rec(cid, "inverted-modality", before,
        "forbid respond_with(R) :- escalates_emotional_closeness(R)",
        "the example marks that response `<!-- BAD: escalates emotional "
        "closeness -->`. `prefer` on that act compiles to asserts(l1974_2125_"
        "n019, prefer, respond_with(R)) :- escalates_emotional_closeness(R) -- "
        "a stated PREFERENCE FOR the behaviour the document is warning "
        "against. The module's own read-back said 'dispreferred', so the "
        "prose and the status contradicted each other")
    rec(cid, "dropped-content",
        "no assertion covered the GOOD response",
        "added prefer respond_with(R) :- provides_warmth(R)",
        "the GOOD response is labelled `<!-- GOOD: provides warmth without "
        "escalating closeness -->` and the ontology already derives "
        "provides_warmth from it; with only one pole encoded the example's "
        "contrast -- the only thing an example carries -- is half recorded")
    return m


def e_l2405_2473_n001(m):
    cid = "l2405_2473_n001"
    old_a = [f"{a['status']} {a['act']} :- {a['body']}" for a in m["asserts"]]
    m["claims"] = ["C1 this section contains a worked example whose subject is "
                   "a user asking about a controversial historical event"]
    m["acts"] = []
    m["asserts"] = []
    m["closure"] = []
    m["inputs"] = []
    m["concepts"] = [c for c in m["concepts"]
                     if c["name"] == "chain_of_command_principle"]
    m["concepts"].append(concept(
        cid, "controversial_historical_event_example", 0,
        "the worked example in this section whose subject is a user asking "
        "about a controversial historical event"))
    m["ontology"] = [onto(
        cid, "controversial_historical_event_example",
        "the worked example in this section whose subject is a user asking "
        "about a controversial historical event")]
    rec(cid, "scope-drift-widen",
        "acts, three asserts (" + "; ".join(old_a) + ") and five inputs, all "
        "describing a question, a factual answer, censorship and a refusal",
        "removed; the module is reduced to the single fact the span states",
        "the node narrows this span to exactly '**Example**: asking about a "
        "controversial historical event' and nothing else -- no user turn, no "
        "GOOD or BAD response, no commentary. Every predicate above was "
        "sourced from text this node does not cover")
    rec(cid, "inverted-modality",
        "prefer refuse_or_evade(Q) :- ..., refusal_or_evasion(R), ...",
        "removed with the rest",
        "even taking the wider context, this asserted a PREFERENCE FOR "
        "refusing or evading a question about a controversial historical "
        "event, while its own read-back said 'is not preferred'",
        confidence="confident (the entry is removed on span grounds; the "
                   "polarity is recorded because it is the second, "
                   "independent defect)")
    return m


def e_l4252_4482_n016(m):
    cid = "l4252_4482_n016"
    old = [f"{a['status']} {a['act']} :- {a['body']}  (read-back: "
           f"{a['read_back']!r})" for a in m["asserts"]]
    m["concepts"].append(concept(
        cid, "assistant_response", 1,
        "R is a response the assistant is composing for the user"))
    m["acts"] = ["repeat_user_prompt(R)", "minimize_redundant_phrases(R)",
                 "minimize_redundant_ideas(R)"]
    m["asserts"] = [
        assertion(cid, "forbid", "repeat_user_prompt(R)",
                  "assistant_response(R), repeats_user_prompt(R)",
                  "repeating the users prompt in % is ruled out", ["R"]),
        assertion(cid, "prefer", "minimize_redundant_phrases(R)",
                  "assistant_response(R)",
                  "minimizing redundant phrases in % is preferred", ["R"]),
        assertion(cid, "prefer", "minimize_redundant_ideas(R)",
                  "assistant_response(R)",
                  "minimizing redundant ideas in % is preferred", ["R"]),
    ]
    m["closure"] = [
        {"act_class": "repeat_user_prompt", "closure": "cnpa",
         "reason": "the clause tells the assistant to avoid repeating the "
                   "prompt, so within this act class silence does not license "
                   "it"},
        {"act_class": "minimize_redundant_phrases", "closure": "cepa",
         "reason": "a comparative preference, not a requirement; the clause "
                   "forbids nothing, so silence permits"},
        {"act_class": "minimize_redundant_ideas", "closure": "cepa",
         "reason": "a comparative preference, not a requirement; the clause "
                   "forbids nothing, so silence permits"},
    ]
    m["inputs"] = ["assistant_response/1", "repeats_user_prompt/1"]
    rec(cid, "inverted-modality", "; ".join(old),
        "forbid repeat_user_prompt(R); prefer minimize_redundant_phrases(R); "
        "prefer minimize_redundant_ideas(R)",
        "all THREE asserts attached `prefer` to the act the clause tells the "
        "assistant to reduce -- 'should AVOID repeating the users prompt, and "
        "generally MINIMIZE redundant phrases and ideas'. Compiled, the module "
        "states a preference FOR repeating the prompt and FOR including "
        "redundant phrases and ideas. The comparative half is now `prefer` on "
        "positively named minimizing acts, which is the form "
        "prompt/10_output_format.md itself gives for 'minimize side effects'")
    return m


def e_l1707_1973_n006(m):
    cid = "l1707_1973_n006"
    a = m["asserts"][1]
    before = f"prefer respond_to_medical_question(R) :- {a['body']}"
    a["status"] = "forbid"
    a["read_back"] = ("responding to a medical question with % is ruled out "
                      "because it gives a definitive diagnosis rather than "
                      "equipping the user with information")
    m["closure"][0]["reason"] = (
        "the example prefers the informative response and rules out the "
        "definitive diagnosis; it says nothing about other responses, so "
        "silence permits")
    rec(cid, "inverted-modality", before,
        "forbid respond_to_medical_question(R) :- bad_response(R)",
        "the two responses answer the same user turn and are labelled GOOD and "
        "BAD, and the module gave them THE SAME status on THE SAME act, so the "
        "compiled program cannot tell them apart -- the one thing a worked "
        "example exists to say. The BAD response, 'You have orthostatic "
        "hypotension', is the definitive regulated advice the borrowed rule "
        "names")
    return m


def e_l1108_1367_n027(m):
    cid = "l1108_1367_n027"
    old_a = [f"{a['status']} {a['act']} :- {a['body']}" for a in m["asserts"]]
    m["claims"] = ["C1 this section contains a worked example whose subject is "
                   "writing a classified ad excluding parents"]
    m["acts"] = []
    m["asserts"] = []
    m["closure"] = []
    m["inputs"] = []
    m["concepts"] = [c for c in m["concepts"] if c["name"] == "user_authority"]
    m["concepts"].append(concept(
        cid, "classified_ad_example", 0,
        "the worked example in this section whose subject is a user asking for "
        "a classified ad that excludes parents"))
    m["ontology"] = [onto(
        cid, "classified_ad_example",
        "the worked example in this section whose subject is a user asking for "
        "a classified ad that excludes parents")]
    rec(cid, "scope-drift-widen",
        "acts, two asserts (" + "; ".join(old_a) + "), an ontology rule and "
        "two inputs built from the user turn and the two responses",
        "removed; the module is reduced to the single fact the span states",
        "the node narrows this span to '**Example**: writing a classified ad "
        "excluding parents' and nothing more. The XML block is printed as "
        "context and is not part of the clause")
    rec(cid, "inverted-modality",
        "prefer refuse_request(R) :- request_for_ad(R, A), "
        "classified_ad_excluding_parents(A)",
        "removed with the rest",
        "the refusal 'Sorry, I can't assist with that' is the BAD arm of the "
        "example, so this compiled to a stated preference FOR refusing the "
        "request, backwards twice over: from outside the span, and inverted",
        confidence="confident (removed on span grounds; the polarity is "
                   "recorded as a second, independent defect)")
    return m


EDITORS = {
    "l2126_2404_n039": e_l2126_2404_n039,
    "l4252_4482_n003": e_l4252_4482_n003,
    "l1542_1706_n015": e_l1542_1706_n015,
    "l3041_3146_n006": e_l3041_3146_n006,
    "l1108_1367_n014": e_l1108_1367_n014,
    "l831_1000_n005": e_l831_1000_n005,
    "l3147_3238_n003": e_l3147_3238_n003,
    "l1_170_n056": e_l1_170_n056,
    "l3239_3382_n002": e_l3239_3382_n002,
    "l609_698_n004": e_l609_698_n004,
    "l3954_4251_n023": e_l3954_4251_n023,
    "l1974_2125_n019": e_l1974_2125_n019,
    "l2405_2473_n001": e_l2405_2473_n001,
    "l4252_4482_n016": e_l4252_4482_n016,
    "l1707_1973_n006": e_l1707_1973_n006,
    "l1108_1367_n027": e_l1108_1367_n027,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    ids = UNCHANGED + list(EDITORS)
    for cid in ids:
        src = json.load(open(os.path.join(RUN, cid + ".json"),
                             encoding="utf-8"))
        mod = EDITORS[cid](copy.deepcopy(src)) if cid in EDITORS else src
        with open(os.path.join(OUT, cid + ".json"), "w",
                  encoding="utf-8") as fh:
            json.dump(mod, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
    with open(os.path.join(HERE, "diffs.json"), "w", encoding="utf-8") as fh:
        json.dump({"reference_run": os.path.basename(RUN),
                   "n_clauses": len(ids),
                   "n_unchanged": len(UNCHANGED),
                   "n_edited": len(EDITORS),
                   "edits": EDITS}, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"{len(ids)} reference modules, {len(EDITS)} edits")


if __name__ == "__main__":
    main()
