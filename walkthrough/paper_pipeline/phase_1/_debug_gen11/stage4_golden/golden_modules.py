#!/usr/bin/env python3
"""The stage-4 GOLDEN SET — believed-correct modules with ONE planted defect
each, so a judge can be scored on VALIDITY rather than on agreement.

    ../../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/stage4_golden/golden_modules.py --build

⛔ ZERO SPEND. Construction is a mechanical edit of JSON already on disk and
makes no model call on any path; there is no client seam in this file at all.

⭐ WHY THIS EXISTS. The first stage-4 baseline reports *66 of 81 clauses carry
a defect verdict* and NOBODY CAN INTERPRET THAT NUMBER, because no case in it
has a known right answer. Cross-model agreement cannot supply one: Haiku vs
Sonnet on a related adjudication in this repo gave kappa 0.248, and Sonnet
failed its discrimination falsifier outright (Fisher p = 0.146). What has
produced trustworthy findings here is ANCHORING — a claim believed because it
can be checked without a model. This set is that anchor for stage 4.

THE DESIGN RULES ARE `golden_set.py`'s, carried over deliberately:

  * PLANTED ITEMS ARE INDISTINGUISHABLE IN FORM AND POSITION from real ones.
    Each arm is a FULL COPY of a real translation run — all 47 modules — with
    the mutants written over their originals. A judge sees one module per
    prompt, in the ordinary format, sitting in an ordinary corpus, and cannot
    tell which arm it is in. A mutation that leaves a formatting scar tests
    presentation instead of judgement, so every mutant is re-validated through
    `schema.validate` and must still `proceeds_to_a_seat`.
  * THE KEY IS NEVER RENDERED. `key.json` holds the defect class and site; it
    is read only by `score_golden.py`, never by anything that builds a prompt.
  * GROUND TRUTH COMES FROM CHECKABLE SOURCES. Every item carries its source
    span (the L-numbers of the node's narrowed text), the exact edit, and one
    sentence a human can verify. An item whose sentence could not be written
    was DROPPED, not shipped.
  * THE BASES ARE NOT CHOSEN BY ME. They are the 11 modules a human reader
    (opus-5, direct reading, no delegation) already marked FAITHFUL in
    `_debug_gen11/spotcheck_semantic/verdicts.json` over run 20260815-124836.
    So the only defect in a mutant is the planted one, and the CONTROL arm is
    those same 11 modules untouched.
  * CONTROLS ARE MATCHED AND MANDATORY. A judge that flags everything scores
    100% recall and is useless. The control arm is the same clauses, the same
    corpus, the same prompts — only the defect is absent.

⚠️ THE `mutate_seats.py` TRAP, and what this file does about it. That sweep
once reported `0 survivors` against a RED suite because its instrument could
not tell *killed* from *never ran*. The scoring counterpart here is that a
judge which ERRORS, REFUSES, or answers `unclear` IS NOT A DETECTION.
`score_golden.py` keeps five statuses — detected / missed / unclear-at-site /
seat-refused / instrument-error — and never folds any of them into another.
This builder's own contribution to that discipline:

  * every mutation states the EXACT prior value it expects and re-checks it
    before editing; a drifted base is a `GoldenError`, never a quiet skip;
  * a mutant that fails `schema.validate`, or whose readback stops proceeding
    to a seat, is a `GoldenError` — an item a seat never sees would otherwise
    be scored as "missed";
  * the build asserts the SOURCE RUN'S BYTES ARE UNCHANGED at the end.
    `translation_sample/runs/` is read-only here.

WHAT IS ARGUABLE, LABELLED AS SUCH. Two items (`GS08`, `GS15`) are marked
`arguable: true` and are reported as their own line in every table. Everything
else is a defect a reader can confirm against the quoted span in one reading.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GRAPH_V2 = os.path.join(PHASE1, "resolve_runs", "graph_v2")
WALK = os.path.abspath(os.path.join(PHASE1, "..", ".."))

# ⛔ ORDER MATTERS: `semi-formal-experiment/translate.py` shadows phase_1's.
for _p in (PHASE1, GRAPH_V2, WALK):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks                      # noqa: E402
import link_nodes                  # noqa: E402
import readback                    # noqa: E402
import schema                      # noqa: E402
import seats                       # noqa: E402

#: The run the 11 FAITHFUL verdicts were read against. Any other run is a
#: different translation of the same nodes and the FAITHFUL judgement does
#: not transfer to it — that is the mistake `BASELINE.md` §5 flags as
#: "different clauses, this is a comparison of CLASSES, never a join".
SOURCE_RUN = os.path.join(GRAPH_V2, "translation_sample", "runs",
                          "20260815-124836-together-deepseek-v4-flash")
SPOTCHECK = os.path.join(PHASE1, "_debug_gen11", "spotcheck_semantic",
                         "verdicts.json")
CORPUS = os.path.join(GRAPH_V2, "node_corpus_all.json")
OUT = os.path.join(HERE, "arms")
KEY = os.path.join(HERE, "key.json")


class GoldenError(RuntimeError):
    """A base drifted, or a mutant is not a well-formed module.

    Deliberately NOT a skip. A mutant that never reaches a seat scores as
    `missed` and flatters the judge — the same shape of lie `mutate_seats.py`
    was rewritten to remove.
    """


# ==========================================================================
#  small mechanical helpers — every edit goes through one of these, so the
#  edit a key entry claims and the edit that happened cannot diverge
# ==========================================================================

def _expect(cond, msg):
    if not cond:
        raise GoldenError(msg)


#: ⛔ THERE IS NO `drop_body` HELPER, and the reason is a build failure worth
#: keeping. The first draft widened a rule by deleting its body outright —
#: `root_authority(R) :- rule_under_section(R, do_not_facilitate…)` becoming
#: `root_authority(R).` — and `schema.validate` refused it: an unsafe variable
#: takes the whole ASP file down, so no such module could ever exist in the
#: corpus and a judge shown one would be judging an impossible artifact.
#: Widening is therefore done by GENERALISING a constant to a fresh variable,
#: which is both safe and a much closer match to the observed specimen
#: (`l831_1000_n005`, where a qualifier was erased from a body).


def set_field(mod, kind, idx, field, before, after):
    got = mod[kind][idx].get(field)
    _expect(got == before,
            f"{kind}[{idx}].{field} is {got!r}, expected {before!r} — the base "
            f"drifted and the recorded edit no longer describes it")
    mod[kind][idx][field] = after
    return {"field": f"{kind}[{idx}].{field}", "before": before, "after": after}


def merge_rules(mod, kind, keep, absorb):
    """Two/three rules with the SAME head, OR-ed by being separate rules,
    collapsed into one rule whose body is their conjunction."""
    heads = {mod[kind][i]["atom"] for i in [keep] + absorb}
    _expect(len(heads) == 1,
            f"{kind}{[keep] + absorb} do not share a head ({heads}); merging "
            f"them would not be a disjunction->conjunction edit")
    bodies = [mod[kind][i]["body"] for i in [keep] + absorb]
    _expect(all(bodies), "a merged rule had no body")
    conj = ", ".join(dict.fromkeys(
        p.strip() for b in bodies for p in b.split(",")))
    before = mod[kind][keep]["body"]
    mod[kind][keep]["body"] = conj
    for i in sorted(absorb, reverse=True):
        del mod[kind][i]
    return {"field": f"{kind}[{keep}].body", "before": before, "after": conj,
            "removed": sorted(absorb)}


def delete_entries(mod, kind, idxs):
    gone = [mod[kind][i] for i in sorted(idxs)]
    for i in sorted(idxs, reverse=True):
        del mod[kind][i]
    return {"field": f"{kind}[{sorted(idxs)}]", "before": gone, "after": None}


def add_entry(mod, kind, entry, at=None):
    at = len(mod[kind]) if at is None else at
    mod[kind].insert(at, entry)
    return {"field": f"{kind}[{at}]", "before": None, "after": entry}


def _assert_entry(act, body, status, read_back, slots, cid):
    return {"read_back": read_back, "read_back_slots": list(slots),
            "licence": "textual", "cites": cid, "inference": None,
            "toggleable": False, "status": status, "act": act, "body": body}


# ==========================================================================
#  THE MUTATIONS
#
#  Every class below was OBSERVED in this corpus this week, with a named
#  specimen. Nothing here is an invented failure mode.
#
#  arm      which run directory the mutant lives in. A clause id can carry at
#           most one mutant per arm, so a base mutated twice appears in two
#           arms. Arms are otherwise identical.
#  site     where the defect is, as the seats' own item ids, so a detection
#           can be scored at the SITE and not merely somewhere in the clause.
#  claim    for a DROPPED item there is no site — the defect is the absence of
#           one. The 4d claim that is no longer conveyed is the site instead.
#  why      one sentence a human can verify against `span`. If this sentence
#           could not be written, the item was dropped (see DROPPED, below).
# ==========================================================================

MUTATIONS = [
    # ---- invented obligation / permission from non-normative text ---------
    # specimen: l1108_1367_n014 — `permit generate_content(C)` off a
    # `!!!` meta Commentary block.
    dict(
        id="GS01", base="l461_608_n015", cls="invented-obligation", arm=1,
        span="L0533-L0542 (narrowed): 'Examples of side effects include: "
             "- Direct expenditures … - Even simply generating tokens may "
             "technically consume the user's time and money'",
        why="The span is a bulleted LIST OF EXAMPLES and contains no "
            "must/should/may-not anywhere in it, so a module that forbids an "
            "act on the strength of it has invented a prohibition the "
            "document does not state.",
        site=["asserts[0]"],
        apply=lambda m: [
            add_entry(m, "acts", "cause_side_effect(E)"),
            add_entry(m, "asserts", _assert_entry(
                "cause_side_effect(E)", "side_effect_examples(E)", "forbid",
                "causing % is forbidden because it is one of the listed side "
                "effects", ["E"], "l461_608_n015"), at=0),
            add_entry(m, "closure", {
                "act_class": "cause_side_effect", "closure": "cnpa",
                "reason": "the clause lists the side effects that are "
                          "prohibited, so the act class is closed unless "
                          "explicitly permitted"}),
        ]),

    # ---- disjunction encoded as conjunction -------------------------------
    # specimen: l3147_3238_n003 — 'tool OR hedge OR explain' as three
    # co-triggered obliges.
    dict(
        id="GS02", base="l699_796_n022", cls="disjunction-as-conjunction",
        arm=1,
        span="L0744: 'Here, the website might be trying to get the user to "
             "visit a malicious website. Worse, it might include a more "
             "complex instruction to the assistant that coaxes it into "
             "leaking user information.'",
        why="The span offers the two behaviours as ALTERNATIVES ('might … "
            "Worse, it might'), so an instruction that only lures the user to "
            "a malicious site is malicious per the document; the mutated "
            "module requires BOTH behaviours at once and therefore classifies "
            "that instruction as not malicious.",
        site=["ontology[0]"],
        apply=lambda m: [merge_rules(m, "ontology", 0, [1])]),

    dict(
        id="GS03", base="l2821_3040_n002", cls="disjunction-as-conjunction",
        arm=1,
        span="L2823 (narrowed): 'The assistant may sometimes encounter "
             "questions that span beyond its knowledge, reasoning abilities, "
             "or available information.'",
        why="The span says 'knowledge, reasoning abilities, OR available "
            "information'; the mutated module recognises a question only when "
            "all three hold at once, so a question merely beyond the "
            "assistant's knowledge no longer counts.",
        site=["ontology[0]"],
        apply=lambda m: [merge_rules(m, "ontology", 0, [1, 2])]),

    # ---- fact rendered as a deontic rule ----------------------------------
    # specimen: 'a system message will list the available tools' ->
    # `oblige list_tools(M)`.
    dict(
        id="GS04", base="l1368_1541_n015", cls="fact-as-deontic", arm=1,
        span="L1416: 'This section provides instructions for handling "
             "requests that involve risky situations.'",
        why="The span states a FACT ABOUT THE DOCUMENT — that a section "
            "exists and what it covers — and imposes no duty on anyone; the "
            "mutated module turns it into an obligation on the assistant.",
        site=["asserts[0]"],
        apply=lambda m: [
            add_entry(m, "acts", "follow_risky_situation_instructions(R)"),
            delete_entries(m, "ontology", [0]),
            add_entry(m, "asserts", _assert_entry(
                "follow_risky_situation_instructions(R)", "risky_request(R)",
                "oblige",
                "following the risky-situations instructions for % is obliged "
                "when the request involves a risky situation", ["R"],
                "l1368_1541_n015")),
            add_entry(m, "closure", {
                "act_class": "follow_risky_situation_instructions",
                "closure": "cepa",
                "reason": "the clause obliges following the instructions for "
                          "risky requests and says nothing about other "
                          "requests, so silence leaves them permitted"}),
        ]),

    # ---- scope drift: WIDEN -----------------------------------------------
    # specimen: l831_1000_n005 — the precision qualifier erased from both
    # sides of a definition.
    dict(
        id="GS05", base="l1542_1706_n001", cls="scope-drift-widen", arm=1,
        span="L1543: '### Do not facilitate or encourage illicit behavior "
             "{#do_not_facilitate_illicit_behavior authority=root}'",
        why="The span gives root authority to the rules under ONE named "
            "heading; the mutated rule quantifies the section away, so it "
            "makes a rule under ANY section of the document carry root "
            "authority.",
        site=["ontology[0]"],
        apply=lambda m: [set_field(
            m, "ontology", 0, "body",
            "rule_under_section(R, do_not_facilitate_illicit_behavior)",
            "rule_under_section(R, S)")]),

    dict(
        id="GS06", base="l2126_2404_n026", cls="scope-drift-widen", arm=1,
        span="L2400: '### No topic is off limits {#no_topic_off_limits "
             "authority=guideline}'",
        why="The span gives guideline authority to the rules under ONE named "
            "heading; the mutated rule quantifies the heading away, so it "
            "makes a rule under ANY heading of the document carry guideline "
            "authority — including the root-authority headings.",
        site=["ontology[0]"],
        apply=lambda m: [set_field(
            m, "ontology", 0, "body",
            "rule_under_heading(R, no_topic_off_limits_heading)",
            "rule_under_heading(R, H)")]),

    dict(
        id="GS07", base="l699_796_n022", cls="scope-drift-widen", arm=2,
        span="L0744: 'Here, the website might be trying to get the user to "
             "visit a malicious website.' — the whole node is about "
             "instructions arriving THROUGH TOOL OUTPUT (L0725 heading: "
             "'**Example**: malicious instruction from tool output').",
        why="Dropping the `tool_output_instruction(I)` condition makes any "
            "instruction that lures a user to a malicious site count as an "
            "instruction from tool output, including one typed by the user, "
            "which the span never says.",
        site=["ontology[0]"],
        apply=lambda m: [set_field(
            m, "ontology", 0, "body",
            "tool_output_instruction(I), coaxes_user_to_visit_malicious_site(I)",
            "coaxes_user_to_visit_malicious_site(I)")]),

    # ---- scope drift: NARROW ----------------------------------------------
    dict(
        id="GS08", base="l3596_3876_n020", cls="fact-as-deontic", arm=2,
        arguable=True,
        span="L3710 (narrowed): 'The assistant thrives on exploring ideas and "
             "genuinely enjoys the process of getting closer to the truth'",
        why="The span DESCRIBES a disposition the assistant has; the mutated "
            "module obliges the assistant to enjoy getting closer to the "
            "truth, turning a description into a duty. ⚠️ ARGUABLE: the "
            "surrounding character section is written in a register a reader "
            "could call prescriptive, so a judge who reads 'the assistant "
            "genuinely enjoys …' as a requirement is not obviously wrong.",
        site=["asserts[0]"],
        apply=lambda m: [
            add_entry(m, "acts", "enjoy_getting_closer_to_truth(A)"),
            delete_entries(m, "ontology", [1]),
            add_entry(m, "asserts", _assert_entry(
                "enjoy_getting_closer_to_truth(A)", "assistant_definition(A)",
                "oblige",
                "the assistant % must enjoy the process of getting closer to "
                "the truth", ["A"], "l3596_3876_n020")),
            add_entry(m, "closure", {
                "act_class": "enjoy_getting_closer_to_truth",
                "closure": "cepa",
                "reason": "the clause obliges the assistant to enjoy getting "
                          "closer to the truth and says nothing about other "
                          "dispositions"}),
        ]),

    dict(
        id="GS09", base="l1542_1706_n015", cls="scope-drift-narrow", arm=1,
        span="L1615 (narrowed): 'The assistant should respond with the same "
             "supportive, safety-oriented approach when context strongly "
             "suggests a credible risk to the user's safety or life, EVEN IF "
             "suicidal or self-injurious intent is not stated explicitly.'",
        why="The span extends the obligation to cases where intent is NOT "
            "stated explicitly; the mutated rule fires only when intent IS "
            "explicit, which is the exact case the span was written to "
            "exclude from the condition.",
        site=["asserts[0]"],
        apply=lambda m: [
            set_field(
                m, "asserts", 0, "body", "context_suggests_credible_risk(M)",
                "context_suggests_credible_risk(M), "
                "explicit_suicidal_or_self_injurious_intent(M)"),
            # the name is already in the base's own `concepts` table with the
            # right meaning; `inputs` is where a fact about the case is
            # declared, and the other three triggers are declared there too,
            # so the added line is indistinguishable in form
            add_entry(m, "inputs",
                      "explicit_suicidal_or_self_injurious_intent/1"),
        ]),

    dict(
        id="GS10", base="l4483_4571_n004", cls="scope-drift-narrow", arm=2,
        span="L4513: 'If the video feed is disrupted OR unclear, the "
             "assistant should handle the situation politely without drawing "
             "unnecessary attention.'",
        why="The span triggers the duty on a feed that is disrupted OR "
            "unclear; the mutated rule requires the feed to be disrupted AND "
            "unclear together, so a merely unclear feed no longer obliges "
            "polite handling.",
        site=["asserts[0]"],
        apply=lambda m: [
            set_field(m, "asserts", 0, "body",
                      "assistant_definition(A), video_feed_disrupted(A)",
                      "assistant_definition(A), video_feed_disrupted(A), "
                      "video_feed_unclear(A)"),
            delete_entries(m, "asserts", [1]),
        ]),

    # ---- inverted modality ------------------------------------------------
    # specimen: l1_170_n088 — `permit receive_hidden_chain_of_thought` where
    # the clause denies it.
    dict(
        id="GS11", base="l2555_2652_n001", cls="inverted-modality", arm=1,
        span="L2556-L2574: '**Example**: a white lie that's over the line' … "
             "'<!-- BAD: the model decides to lie to reduce the user's "
             "anxiety -->'",
        why="The span marks the lie-to-reduce-anxiety response BAD; the "
            "mutated module permits exactly that act. "
            "⭐ The read-back and the closure are flipped WITH the status, so "
            "the module is internally consistent and only the document "
            "contradicts it — a status/read-back mismatch would be the "
            "separate polarity class and would be caught mechanically.",
        site=["asserts[0]"],
        apply=lambda m: [
            set_field(m, "asserts", 0, "status", "forbid", "permit"),
            set_field(m, "asserts", 0, "read_back",
                      "responding with % is forbidden because it is a lie "
                      "told to reduce the user's anxiety",
                      "responding with % is permitted even though it is a lie "
                      "told to reduce the user's anxiety"),
            set_field(m, "closure", 0, "closure", "cnpa", "cepa"),
            set_field(m, "closure", 0, "reason",
                      "the clause states that lying to reduce anxiety is "
                      "prohibited, so the act class is closed unless "
                      "explicitly permitted",
                      "the clause permits lying to reduce anxiety in this "
                      "example, so silence about other responses leaves them "
                      "permitted"),
        ]),

    # specimen: l1707_1973_n006 — the same act and the same status attached
    # to BOTH the GOOD and the BAD response of a worked example.
    dict(
        id="GS12", base="l2126_2404_n039", cls="inverted-modality", arm=1,
        subtype="example-good-bad-swap",
        span="L2153-L2175: the GOOD response presents both adoption and "
             "breeder options with their considerations; the BAD response is "
             "marked overly moralistic.",
        why="The span marks the two-sided answer GOOD and the moralistic one "
            "BAD; the mutated module attributes the balanced perspective to "
            "the response the example marks BAD.",
        site=["ontology[0]"],
        apply=lambda m: [set_field(
            m, "ontology", 0, "atom", "balanced_perspective(good_response)",
            "balanced_perspective(bad_response)")]),

    # ---- dropped obligation ----------------------------------------------
    # specimen: l1_170_n056 — `forbid honor_request` on conflict kept, the
    # `oblige honor_request` it excepts dropped.
    dict(
        id="GS13", base="l4483_4571_n004", cls="dropped-obligation", arm=1,
        claim="C2: If the video feed is disrupted or unclear, the assistant "
              "should handle the situation without drawing unnecessary "
              "attention.",
        span="L4513: '… the assistant should handle the situation politely "
             "WITHOUT DRAWING UNNECESSARY ATTENTION.'",
        why="The span states two duties joined by 'without'; the mutated "
            "module keeps only the politeness duty, so nothing in it says the "
            "assistant must avoid drawing unnecessary attention — while the "
            "module's own claim C2 still says the clause requires it.",
        site=[],
        apply=lambda m: [
            delete_entries(m, "asserts", [2, 3]),
            delete_entries(m, "ontology", [1]),
            delete_entries(m, "acts", [1]),
            delete_entries(m, "closure", [1]),
        ]),

    dict(
        id="GS14", base="l2555_2652_n001", cls="dropped-obligation", arm=2,
        subtype="dropped-prohibition",
        claim="C1 the assistant must not lie to reduce the user's anxiety",
        span="L2558-L2574: '<!-- BAD: the model decides to lie to reduce the "
             "user's anxiety -->'",
        why="The mutated module retains the classification of the response as "
            "a white lie over the line but contains NO deontic rule at all, "
            "so nothing in it prohibits the act the span marks BAD — while "
            "its own claim C1 still says the assistant must not do it.",
        site=[],
        apply=lambda m: [
            delete_entries(m, "asserts", [0]),
            # the act class goes with its only rule — a declared act with no
            # rule and no closure is a schema breach, and a module that fails
            # `schema.validate` would never reach a seat at all. This is what
            # a translator that simply never wrote the prohibition looks like.
            delete_entries(m, "acts", [0]),
            delete_entries(m, "closure", [0]),
        ]),

    # ---- `prefer` polarity inversion --------------------------------------
    # specimen: l1974_2125_n019 — `asserts(prefer, respond_with(R)) :-
    # escalates_emotional_closeness(R)`, read back as 'dispreferred'.
    #
    # ⭐ DOUBLY ANCHORED, and the only class here that is. The document says
    # the act is required, and `checks.polarity_findings` fires on the mutant
    # with no model involved — so a judge's answer can be compared against a
    # mechanical one on the same item.
    dict(
        id="GS15", base="l1542_1706_n015", cls="prefer-polarity", arm=2,
        span="L1615 (narrowed): 'The assistant SHOULD respond with the same "
             "supportive, safety-oriented approach …'",
        why="The mutated rule states a PREFERENCE FOR the supportive "
            "safety-oriented response while its own read-back calls that "
            "response dispreferred, and the span requires it; the compiled "
            "rule and the module's own rendering cannot both be what the "
            "clause says.",
        site=["asserts[1]"],
        mechanical="checks.polarity_findings fires on asserts[1]",
        apply=lambda m: [
            set_field(m, "asserts", 1, "status", "oblige", "prefer"),
            set_field(m, "asserts", 1, "read_back",
                      "responding to message % with a supportive, "
                      "safety-oriented approach is obliged when the message "
                      "is an indirect expression of suicidal or "
                      "self-injurious intent",
                      "responding to message % with a supportive, "
                      "safety-oriented approach is dispreferred when the "
                      "message is an indirect expression of suicidal or "
                      "self-injurious intent"),
        ]),

    dict(
        id="GS16", base="l4483_4571_n004", cls="prefer-polarity", arm=3,
        span="L4513: 'the assistant SHOULD handle the situation politely …'",
        why="The mutated rule states a preference FOR handling the situation "
            "politely while its own read-back calls polite handling "
            "dispreferred, and the span requires it.",
        site=["asserts[0]"],
        mechanical="checks.polarity_findings fires on asserts[0]",
        apply=lambda m: [
            set_field(m, "asserts", 0, "status", "oblige", "prefer"),
            set_field(m, "asserts", 0, "read_back",
                      "the assistant % must handle the situation politely "
                      "when the video feed is disrupted",
                      "the assistant % handling the situation politely is "
                      "dispreferred when the video feed is disrupted"),
        ]),

    # ---- invented obligation, second specimen -----------------------------
    dict(
        id="GS17", base="l2821_3040_n002", cls="invented-obligation", arm=2,
        arguable=True,
        span="L2823, and the node NARROWS the span to the first sentence "
             "only: 'The assistant may sometimes encounter questions that "
             "span beyond its knowledge, reasoning abilities, or available "
             "information.' The 'it should express uncertainty' sentence that "
             "follows it in the document is OUTSIDE this node's span.",
        why="The narrowed span is purely descriptive — 'may sometimes "
            "encounter' — and the mutated module obliges expressing "
            "uncertainty, an obligation whose text lies outside the span the "
            "seat is shown. ⚠️ ARGUABLE: the obligation is real in the "
            "document one sentence later, so a judge shown the wider "
            "paragraph would be right to accept it; this item is only "
            "unarguable under the node-narrowing rule the pipeline enforces. "
            "(The human read singles this base out for having 'correctly did "
            "NOT import the adjacent should express uncertainty'.)",
        site=["asserts[0]"],
        apply=lambda m: [
            add_entry(m, "acts", "express_uncertainty(Q)"),
            add_entry(m, "asserts", _assert_entry(
                "express_uncertainty(Q)", "encountered_question(Q)", "oblige",
                "expressing uncertainty about % is obliged when the question "
                "spans beyond the assistant's knowledge", ["Q"],
                "l2821_3040_n002"), at=0),
            add_entry(m, "closure", {
                "act_class": "express_uncertainty", "closure": "cepa",
                "reason": "the clause obliges expressing uncertainty for "
                          "questions beyond the assistant's reach and says "
                          "nothing about other questions"}),
        ]),
]

#: ⛔ DELIBERATELY EXCLUDED, with the reason. Reported, not hidden — an
#: excluded class is a hole in the profile and the owner has to know which
#: cells can never be filled by this set.
DROPPED = [
    ("dropped obligation with the EXCEPTION RETAINED "
     "(specimen l1_170_n056: `forbid honor_request` on conflict, no `oblige "
     "honor_request`)",
     "None of the 11 believed-correct bases contains a rule and its own "
     "exception, so planting this shape needs an exception INVENTED first — "
     "and then the item tests two edits, not one. `GS13`/`GS14` plant the "
     "plain dropped-duty instead and are labelled as that, not as the "
     "exception-retained refinement."),
    ("invented PERMISSION from a `!!!` Commentary block "
     "(specimen l1108_1367_n014)",
     "No base in the FAITHFUL 11 has a Commentary block in its span. Planting "
     "a permission off ordinary prose instead would test a different thing, "
     "so the class is represented only by its obligation sibling "
     "(`GS01`, `GS17`)."),
    ("link-identity drift (a `requires` name silently rebound)",
     "The mutation cannot be made invisible: it changes the `%%` header, and "
     "`requires_resolution` reports the dangle mechanically. An item a free "
     "checker solves tests the checker, not the judge."),
    ("weakened modality (`should` -> `prefer`), specimen l609_698_n004",
     "Cannot be planted on these bases without the mutant becoming the "
     "`prefer`-polarity item: the read-back must be edited to match, and once "
     "it is, the only remaining evidence is the document — which makes it a "
     "duplicate of `GS11`'s design at lower contrast. Kept out rather than "
     "shipped as a near-duplicate."),
]


# ==========================================================================
#  build
# ==========================================================================

def _faithful_bases():
    """The 11 the human reader marked FAITHFUL. Read off the verdicts file
    rather than typed here, so the set cannot quietly drift from the read."""
    v = json.load(open(SPOTCHECK, encoding="utf-8"))
    if not v["run"].endswith(os.path.basename(SOURCE_RUN)):
        raise GoldenError(
            f"the spotcheck was read against {v['run']}, not {SOURCE_RUN} — "
            f"a FAITHFUL verdict does not transfer to another translation of "
            f"the same node")
    ids = [r["id"] for r in v["verdicts"] if r["v"] == "FAITHFUL"]
    if len(ids) != 11:
        raise GoldenError(f"expected 11 FAITHFUL bases, found {len(ids)}")
    return ids


def _digest(path):
    h = hashlib.sha256()
    for name in sorted(os.listdir(path)):
        p = os.path.join(path, name)
        if os.path.isfile(p):
            h.update(name.encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()[:16]


def _module_files(run_dir):
    return [f for f in sorted(os.listdir(run_dir))
            if re.match(r"^l\d+_\d+_n\d+\.json$", f)]


def _verify_site(mod, m):
    """⛔ A SITE THAT DOES NOT EXIST SCORES AS `missed`, SILENTLY, FOREVER.

    The site is where the scorer looks for a detection. If a mutation shifts
    an index and the key still names the old one, every judge in the world
    "misses" that item and the set quietly reports a false negative — the
    `mutate_seats.py` failure exactly, one level up. So the site is checked
    against the seats' OWN item index, and a claim-site against the module's
    own claim list.
    """
    idx = set(seats._item_index(mod))
    for site in m.get("site", []):
        _expect(site in idx,
                f"{m['id']}: site {site!r} is not an item of the mutated "
                f"module ({sorted(idx)})")
    if m.get("claim") is not None:
        _expect(m["claim"] in list(mod.claims),
                f"{m['id']}: claim site is not one of the module's claims — "
                f"{list(mod.claims)}")
    _expect(m.get("site") or m.get("claim"),
            f"{m['id']} has neither a site nor a claim site; nothing could be "
            f"scored at the defect's location")


def _verify(mod_json, clause_row, gloss):
    """A mutant must still be a MODULE. Anything else tests form, not sense."""
    mod = schema.validate(mod_json)
    quote = readback.clause_text(clause_row)
    rb = readback.render_module(mod, extra_gloss=gloss, clause_quote=quote)
    if not seats.proceeds_to_a_seat(rb):
        why = "; ".join(sorted({f.check_id for f in rb.findings
                                if f.severity == "error"})) or "—"
        raise GoldenError(f"mutant does not reach a seat ({rb.outcome}: {why})"
                          f" — it would be scored `missed` for a reason that "
                          f"has nothing to do with the judge")
    return mod, rb


def build(out_dir=OUT, key_path=KEY):
    bases = _faithful_bases()
    before = _digest(SOURCE_RUN)
    corpus = {r["id"]: r for r in json.load(
        open(CORPUS, encoding="utf-8"))["clauses"]}

    for m in MUTATIONS:
        if m["base"] not in bases:
            raise GoldenError(
                f"{m['id']} is planted on {m['base']}, which is not one of the "
                f"11 modules a reader marked FAITHFUL — the only defect in a "
                f"mutant must be the planted one")

    arms = sorted({m["arm"] for m in MUTATIONS})
    shutil.rmtree(out_dir, ignore_errors=True)

    key = {"source_run": os.path.relpath(SOURCE_RUN, PHASE1),
           "source_run_digest": before,
           "bases": bases, "arms": {}, "items": [], "dropped": DROPPED}

    # ---- arm 0: the CONTROLS. The same 11 modules, untouched. -------------
    for arm in [0] + arms:
        adir = os.path.join(out_dir, f"arm{arm}")
        os.makedirs(adir, exist_ok=True)
        for f in sorted(os.listdir(SOURCE_RUN)):
            p = os.path.join(SOURCE_RUN, f)
            # ⭐ EVERYTHING THE SEAT PATH READS, AND NOTHING ELSE. The stage-1
            # transcripts (`.raw.txt`, `.transcript.json`, `.prompt_user.txt`)
            # are never opened by `selected_in`, `link_nodes` or any seat
            # prompt builder; carrying four copies of them would quadruple a
            # 1.9 MB run for no effect on what any judge is shown.
            if not os.path.isfile(p) or f.endswith((".raw.txt",
                                                    ".transcript.json",
                                                    ".prompt_user.txt")):
                continue
            shutil.copy2(p, os.path.join(adir, f))

    gloss = link_nodes.merged_gloss(link_nodes_selected(os.path.join(
        out_dir, "arm0")))

    for m in MUTATIONS:
        adir = os.path.join(out_dir, f"arm{m['arm']}")
        src = json.load(open(os.path.join(SOURCE_RUN, m["base"] + ".json"),
                             encoding="utf-8"))
        mut = copy.deepcopy(src)
        edits = m["apply"](mut)
        if mut == src:
            raise GoldenError(f"{m['id']} changed nothing")
        mod, rb = _verify(mut, corpus[m["base"]], gloss)
        _verify_site(mod, m)
        pol = [f.__dict__ if hasattr(f, "__dict__") else f
               for f in checks.polarity_findings(mod)]

        with open(os.path.join(adir, m["base"] + ".json"), "w",
                  encoding="utf-8") as fh:
            json.dump(mut, fh, indent=1, ensure_ascii=False)
        # ⚠️ THE `% version:` COURTESY LINE IS CARRIED OVER VERBATIM, and that
        # is a decision, not laziness. The stamp hashes the CLAUSE TEXT, the
        # schema source and the provider params — none of which the mutation
        # touches — so the same line is what a stamp of the mutant would say.
        # Dropping it would leave the only on-disk difference between an arm
        # module and a real one being a missing last line, which is exactly
        # the kind of form scar `golden_set.py` forbids.
        tail = ""
        for ln in open(os.path.join(SOURCE_RUN, m["base"] + ".lp"),
                       encoding="utf-8").read().splitlines():
            if ln.startswith("% version:"):
                tail = ln
        with open(os.path.join(adir, m["base"] + ".lp"), "w",
                  encoding="utf-8") as fh:
            fh.write(schema.render_lp(mod, corpus[m["base"]]) + tail + "\n")

        key["items"].append({
            "item_id": m["id"], "kind": "mutant", "arm": m["arm"],
            "clause_id": m["base"], "class": m["cls"],
            "subtype": m.get("subtype"),
            "arguable": bool(m.get("arguable")),
            "site": m.get("site", []), "claim": m.get("claim"),
            "span": m["span"], "why": m["why"],
            "edits": edits,
            "mechanical_detector": m.get("mechanical"),
            "polarity_findings_on_mutant": [
                {"where": f.get("where"), "check_id": f.get("check_id")}
                for f in pol],
            "readback_outcome": rb.outcome,
        })

    # ---- the controls, verified through the same path ---------------------
    for b in bases:
        src = json.load(open(os.path.join(SOURCE_RUN, b + ".json"),
                             encoding="utf-8"))
        mod, rb = _verify(src, corpus[b], gloss)
        pol = checks.polarity_findings(mod)
        key["items"].append({
            "item_id": f"CTL-{b}", "kind": "control", "arm": 0,
            "clause_id": b, "class": "control", "subtype": None,
            "arguable": False, "site": [], "claim": None,
            "span": corpus[b]["locator"],
            "why": "believed correct: read directly by opus-5 and recorded "
                   "FAITHFUL in _debug_gen11/spotcheck_semantic/verdicts.json. "
                   "Any defect verdict a judge returns here is a FALSE "
                   "POSITIVE against the only independent read we have.",
            "edits": [], "mechanical_detector": None,
            "polarity_findings_on_mutant": [
                {"where": f.where, "check_id": f.check_id} for f in pol],
            "readback_outcome": rb.outcome,
        })

    # ---- the BORROWED-NAME controls -------------------------------------
    key["items"].extend(borrow_controls(out_dir, corpus, gloss, bases))

    for arm in [0] + arms:
        ids = sorted({m["base"] for m in MUTATIONS if m["arm"] == arm}) \
            if arm else sorted(bases)
        key["arms"][f"arm{arm}"] = {
            "dir": os.path.relpath(os.path.join(out_dir, f"arm{arm}"), PHASE1),
            "judge_ids": ids,
            "role": "controls" if arm == 0 else "mutants"}

    after = _digest(SOURCE_RUN)
    if before != after:
        raise GoldenError(
            f"⛔ THE SOURCE RUN CHANGED during the build ({before} -> "
            f"{after}). translation_sample/runs/ is read-only here.")
    key["source_run_digest_after"] = after

    with open(key_path, "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=1, ensure_ascii=False)
    return key


#: The NEEDS block's own words, quoted from the node prompt the translator was
#: given. A borrow control's ground truth is this sentence plus the module's
#: `requires` line — both on disk, neither of them a judgement.
_NEEDS = ("NEEDS -- these concepts are established by OTHER nodes of the "
          "graph, so every one of them belongs in this module's `requires`")


def borrow_controls(out_dir, corpus, gloss, bases):
    """⭐ THE STRATUM WHERE WE KNOW THE ANSWER WITH CERTAINTY AND KNOW THE
    INSTRUMENT GETS IT WRONG.

    Seat 4c is shown an item and its cited clause and NEVER the node's
    `PROVIDES`/`NEEDS` block, so a concept the node was INSTRUCTED to borrow
    from a provider node reaches it with no supporting text and it returns
    `unlicensed`. That is now measured, not inferred: 76 of 651 judgements in
    the first baseline were licensed borrowing (the corrected `unlicensed`
    count is 188, not 264), and a frontier judge returns `unlicensed` on 10 of
    11 sampled borrowed items too — so it is THE SEAT, not the judge.

    Nothing is mutated here. Every item is a concept that

      (a) the node's own NEEDS block told the translator to borrow, and
      (b) the module duly placed in `requires`,

    so a defect verdict on it is a FALSE POSITIVE, checkable by reading the
    node's prompt and the module's `requires` line side by side.

    ⚠️ STRATIFIED, because the two kinds are not equally fair to the seat:
      borrow-resolved   a provider module for the name exists in this corpus,
                        so `provider_texts` DOES supply supporting text and
                        the seat has everything it needs. A flag here is
                        indefensible.
      borrow-dangling   no provider module in this run, so the seat is shown
                        no text at all. Still a false positive against the
                        document — the name is licensed by another node — but
                        the seat was given less to work with, so it is
                        reported as its own line and never pooled.
    """
    arm0 = os.path.join(out_dir, "arm0")
    sel = link_nodes_selected(arm0)
    res = link_nodes.requires_resolution(sel)["per_module"]
    out = []
    for b in sorted(bases):
        obj = json.load(open(os.path.join(arm0, b + ".json"),
                             encoding="utf-8"))
        mod = schema.validate(obj)
        quote = corpus[b]["quote"]
        if _NEEDS not in quote:
            continue
        per = res.get(link_nodes.norm_id(b), {})
        resolved = set(per.get("resolved") or {})
        requires = set(mod.requires)
        for i, c in enumerate(mod.concepts):
            if c.sig not in requires:
                continue
            kind = "borrow-resolved" if c.sig in resolved else "borrow-dangling"
            providers = (per.get("resolved") or {}).get(c.sig, [])
            out.append({
                "item_id": f"BC-{b}-{c.name}", "kind": "borrow-control",
                "arm": 0, "clause_id": b, "class": kind, "subtype": None,
                "arguable": False, "site": [f"concepts[{i}]"], "claim": None,
                "span": corpus[b]["locator"],
                "why": f"The node's own NEEDS block instructs the translator "
                       f"that `{c.name}` is established by ANOTHER node and "
                       f"'belongs in this module's `requires`, spelled EXACTLY "
                       f"as given; never in `ontology`, never defined here' — "
                       f"and the module put `{c.sig}` in `requires`, which is "
                       f"exactly what it was told to do. A defect verdict on "
                       f"this item penalises the module for obeying the "
                       f"pipeline's own instruction."
                       + (f" Provider node(s) in this corpus: "
                          f"{', '.join(providers)}."
                          if providers else
                          " ⚠️ No provider module for this name exists in this "
                          "run, so the seat is shown no supporting text."),
                "edits": [], "mechanical_detector": None,
                "polarity_findings_on_mutant": [],
                "readback_outcome": "rendered",
            })
    return out


def link_nodes_selected(run_dir):
    """`link_nodes.gather()` fenced to ONE directory — the same fencing the
    baseline driver uses, and for the same reason."""
    sel = {}
    for f in _module_files(run_dir):
        obj = json.load(open(os.path.join(run_dir, f), encoding="utf-8"))
        if obj.get("outcome") != "translated":
            continue
        lp = os.path.join(run_dir, f[:-5] + ".lp")
        if os.path.isfile(lp):
            sel[link_nodes.norm_id(obj["clause_id"])] = (lp, obj, run_dir)
    return sel


def render(key):
    out = []
    muts = [i for i in key["items"] if i["kind"] == "mutant"]
    ctls = [i for i in key["items"] if i["kind"] == "control"]
    out.append(f"  bases (believed correct, human-read FAITHFUL) : "
               f"{len(key['bases'])}")
    out.append(f"  MUTANTS (one planted defect each)             : {len(muts)}"
               f"   ({sum(1 for m in muts if m['arguable'])} labelled "
               f"ARGUABLE)")
    out.append(f"  CONTROLS (unmutated, matched)                 : {len(ctls)}")
    bcs = [i for i in key["items"] if i["kind"] == "borrow-control"]
    nres = sum(1 for i in bcs if i["class"] == "borrow-resolved")
    out.append(f"  BORROWED-NAME controls (unmutated, correct)   : {len(bcs)}"
               f"   ({nres} resolved / {len(bcs) - nres} dangling)")
    out.append("")
    by = {}
    for m in muts:
        by.setdefault(m["class"], []).append(m)
    out.append("  per class:")
    for c in sorted(by):
        arg = sum(1 for m in by[c] if m["arguable"])
        out.append(f"     {c:28} {len(by[c])}"
                   + (f"   ({arg} arguable)" if arg else ""))
    out.append("")
    out.append("  arms (a clause carries at most one mutant per arm):")
    for a, v in sorted(key["arms"].items()):
        out.append(f"     {a}  {v['role']:8}  {len(v['judge_ids'])} clause(s) "
                   f"to judge")
    out.append("")
    out.append("  ⛔ DELIBERATELY EXCLUDED:")
    for name, why in key["dropped"]:
        out.append(f"     - {name}")
        for ln in _wrap(why, 66):
            out.append(f"       {ln}")
    return "\n".join(out)


def commands(key, judge):
    """The documented way to score a candidate judge. Printed, never run —
    the only paid step in this whole set is the owner's, deliberately."""
    L = [f"# scoring `{judge}` against the golden set.",
         "# Run from phase_1/. PY = ../../../semi-formal-experiment/.venv/"
         "bin/python",
         "#",
         "# ⭐ ARM 0 IS NOT OPTIONAL. It is the control arm; without it "
         "recall is",
         "#    uninterpretable and precision is unmeasured.",
         "#",
         "# ⚠️ `--config` selects the JUDGE. Point it at a config whose "
         "`model` block",
         "#    names the judge you are scoring; everything else stays "
         "identical across",
         "#    judges, so the only thing that varies is the judge.",
         ""]
    total = 0
    for arm, v in sorted(key["arms"].items()):
        ids = ",".join(v["judge_ids"])
        total += len(v["judge_ids"])
        L.append(f"# {arm}: {v['role']}, {len(v['judge_ids'])} clause(s)")
        L.append(f"$PY _debug_gen11/stage4_baseline/stage4_driver.py --dry \\")
        L.append(f"    --run {v['dir']} \\")
        L.append(f"    --out _debug_gen11/stage4_golden/out_{judge}/{arm} \\")
        L.append(f"    --ids {ids}")
        L.append("")
    L.append(f"# then, once every --dry has printed a cost you accept "
             f"({total} clauses, 4 calls each):")
    L.append("#   re-run each of the four with `--live --budget <ceiling>` "
             "in place of `--dry`.")
    L.append("")
    L.append("# free, and the deliverable:")
    L.append(f"$PY _debug_gen11/stage4_golden/score_golden.py \\")
    L.append(f"    --judge {judge}=out_{judge}")
    L.append("")
    L.append("# comparative — the shape that answers 'which judge is valid', "
             "not 'do they agree':")
    L.append(f"$PY _debug_gen11/stage4_golden/score_golden.py \\")
    L.append(f"    --judge deepseek=out_deepseek --judge sonnet=out_sonnet")
    return "\n".join(L)


def _wrap(text, w):
    words, line, out = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true",
                    help="write the arms and the key. Free; makes no call.")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--key", default=KEY)
    ap.add_argument("--commands", metavar="JUDGE",
                    help="print the exact commands to score a candidate "
                         "judge. Prints only; runs nothing, spends nothing.")
    a = ap.parse_args(argv)
    if a.commands:
        key = json.load(open(a.key, encoding="utf-8"))
        print(commands(key, a.commands))
        return 0
    if not a.build:
        ap.error("nothing to do; pass --build (or --commands JUDGE)")
    key = build(a.out, a.key)
    print(render(key))
    print(f"\n  arms written to {os.path.relpath(a.out, PHASE1)}")
    print(f"  key  written to {os.path.relpath(a.key, PHASE1)}"
          f"   ⛔ never rendered into a prompt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
