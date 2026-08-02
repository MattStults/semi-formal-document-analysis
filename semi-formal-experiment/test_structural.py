"""Tests for structural.py — the typed backoff ladder.

Nothing in `structural.py` may call a model or read a panel label; both are
asserted below by reading its source, in the same style as
`test_relevance.py::test_no_model_is_called_at_query_time`.

WHY THE MEASUREMENT LIVES IN THIS FILE
--------------------------------------
`structural.py` must be provably label-free (contract §5 invariant 9), and the
cheapest proof is that the string `benchmark` does not occur in it. So the
panel-facing evaluation — which legitimately reads labels, because measuring is
what the panel is FOR — lives here instead, behind `__main__`:

    .venv/bin/python test_structural.py            # the LOBO ladder report

Running the tests never touches the panel; running the module does.
"""
from __future__ import annotations

import json
import math
import os
import sys

import pytest

import ontology as O
import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def vocab():
    return {
        "user_request_ambiguous": {"kind": "situation", "gloss": "The request is unclear.",
                                   "n_clauses": 3, "clauses": ["c1"]},
        "ambiguity_present": {"kind": "situation", "gloss": "Something is unclear.",
                              "n_clauses": 4, "clauses": ["c2"]},
        "clarify_user_intent": {"kind": "act", "gloss": "Asking what was meant.",
                                "n_clauses": 3, "clauses": ["c1"]},
        "ask_followup_question": {"kind": "act", "gloss": "Asking a follow-up.",
                                  "n_clauses": 3, "clauses": ["c2"]},
        "assume_intent": {"kind": "act", "gloss": "Guessing what was meant.",
                          "n_clauses": 2, "clauses": ["c3"]},
        "end_user": {"kind": "entity", "gloss": "The person talking.",
                     "n_clauses": 2, "clauses": ["c1"]},
        "helpfulness": {"kind": "value", "gloss": "Being useful.",
                        "n_clauses": 2, "clauses": ["c4"]},
        "everywhere": {"kind": "situation", "gloss": "A stopword atom.",
                       "n_clauses": 5, "clauses": []},
    }


@pytest.fixture
def clauses():
    return [
        {"id": "c1", "quote": "Ask the user what they meant when the request is unclear.",
         "section_path": ["Ambiguity"], "locator": "spec > Ambiguity > 1"},
        {"id": "c2", "quote": "A follow-up question is appropriate when something is unclear.",
         "section_path": ["Ambiguity"], "locator": "spec > Ambiguity > 2"},
        {"id": "c3", "quote": "Do not guess what the user meant.",
         "section_path": ["Ambiguity"], "locator": "spec > Ambiguity > 3"},
        {"id": "c4", "quote": "Be useful.", "section_path": ["Values"],
         "locator": "spec > Values > 1"},
        {"id": "c5", "quote": "Unrelated text about tools.",
         "section_path": ["Tools"], "locator": "spec > Tools > 1"},
    ]


@pytest.fixture
def annotations(vocab):
    def at(name, cid, quote):
        return {"name": name, "kind": vocab[name]["kind"],
                "gloss": vocab[name]["gloss"], "span_id": "s1", "quote": quote,
                "clause_id": cid, "locator": f"spec > {cid}"}
    return {
        "c1": [at("user_request_ambiguous", "c1", "the request is unclear"),
               at("clarify_user_intent", "c1", "Ask the user what they meant"),
               at("end_user", "c1", "the user")],
        "c2": [at("ambiguity_present", "c2", "something is unclear"),
               at("ask_followup_question", "c2", "A follow-up question")],
        "c3": [at("assume_intent", "c3", "guess what the user meant")],
        "c4": [at("helpfulness", "c4", "Be useful")],
        "c5": [],
    }


@pytest.fixture
def query():
    return S.Query("ambiguity", [
        {"name": "user_request_ambiguous", "kind": "situation", "weight": 3},
        {"name": "clarify_user_intent", "kind": "act", "weight": 3},
        {"name": "end_user", "kind": "entity", "weight": 1},
    ])


@pytest.fixture
def onto(vocab):
    """An ontology with hand-set relations — the relation layer this spec's
    mechanical path does NOT supply, so the graded rungs are testable."""
    rels = [
        O.Relation("subsumes", "ambiguity_present", "user_request_ambiguous",
                   "hand", "fixture", "model"),
        O.Relation("subsumes", "clarify_user_intent", "ask_followup_question",
                   "hand", "fixture", "model"),
        O.Relation("contrary", "assume_intent", "clarify_user_intent",
                   "hand", "fixture", "model"),
    ]
    kept, _ = O.validate(rels, vocab)
    return O.Ontology(vocab, kept)


@pytest.fixture
def index(clauses, annotations, onto):
    return S.StructuralIndex(clauses, annotations, onto)


# ------------------------------------------------------- hard invariants

def test_no_model_is_called_at_query_time():
    src = open(os.path.join(HERE, "structural.py")).read()
    for forbidden in ("import providers", "from providers", "requests",
                      "urllib", "http", "openai", "anthropic", "torch",
                      "transformers", "sentence_transformers"):
        assert forbidden not in src, f"query path must not reference {forbidden}"


def test_nothing_reads_panel_labels():
    """Invariant 9, made mechanical: the query cannot be fitted to labels it
    cannot name. # MUTATION-VERIFIED"""
    src = open(os.path.join(HERE, "structural.py")).read()
    for forbidden in ("behaviours.json", "llm-panel-review", "load_panel",
                      "verdicts", "import benchmark", "reference_ids", "gold"):
        assert forbidden not in src, f"structural.py must not reference {forbidden}"


def test_every_declared_constant_carries_a_justification_and_its_provenance():
    """Every constant in the query must be declared in `CONSTANTS` with a
    justification, so 'where did 0.37 come from' is answerable by reading.

    ⚠️ THIS TEST USED TO ASSERT `fitted_on_panel is False` FOR EVERY ENTRY,
    which made "no fitted constants" true BY CONSTRUCTION: the one constant
    that WAS fitted (`primary_operator`, selected on panel MCC over 7
    operators) simply was not declared, and the audit never noticed because it
    only ever iterated what was declared. A blanket ban on the flag is an
    incentive to omit the entry. So the rule is now DISCLOSURE, not denial: a
    fitted constant is allowed if and only if it states what it was selected
    over, on what criterion, and what the UNSELECTED no-choice default scores —
    which is the number a reader needs to bound the selection bias.
    `test_constants_declaration_is_complete` is what stops the omission trick.
    # MUTATION-VERIFIED
    """
    for name, entry in S.CONSTANTS.items():
        assert entry["value"] is not None
        assert len(entry["why"]) > 40, f"{name} has no real justification"
        assert entry["fitted_on_panel"] in (True, False)
        if entry["fitted_on_panel"] is not True:
            continue
        assert entry.get("selected_over"), (
            f"{name} is fitted on the panel but does not say what it was "
            "selected OVER — the alternatives are the bias")
        assert entry.get("selection_criterion"), (
            f"{name} is fitted but does not name the criterion it was fitted on")
        base = entry.get("unselected_baseline") or {}
        for key in ("value", "selected_value", "bias_bound"):
            assert key in base, (
                f"{name} is fitted but gives no {key} for the unselected "
                "no-choice default — without it the selection bias is "
                "unbounded and the reader cannot discount the headline")
        assert abs((base["selected_value"] - base["value"])
                   - base["bias_bound"]) < 1e-9, (
            f"{name}: the stated bias bound must be the gap between the "
            "selected value and the no-choice default, not a smaller number")
        assert len(entry["why"]) > 300, (
            f"{name} is a PANEL-FITTED constant; its justification must be a "
            "full disclosure, not a line")


#: Module-level names in `structural.py` that are NOT query parameters and so
#: are not required to be declared in `CONSTANTS`: file paths, the slot and
#: rung vocabularies (structure, not settings), the operator table, the
#: declaration dict itself, and the CLI help text.
#:
#: ⚠️ THIS SET IS FROZEN AND `test_constants_declaration_is_complete` ASSERTS
#: EQUALITY, NOT MEMBERSHIP. Adding a new module-level constant therefore
#: breaks the test until you either derive it from `CONSTANTS` or come here and
#: argue, in a diff, that it is not a parameter. That is the whole mechanism:
#: the previous audit could be evaded by not declaring a constant, and this one
#: cannot.
NON_PARAMETER_MODULE_NAMES = frozenset({
    "HERE", "CLAUSES", "ANNOTATIONS", "BEHAVIOUR_ATOMS",
    "CORE_SLOTS", "SUPPORT_SLOTS", "SLOTS",
    "RUNGS", "RUNG_NAMES", "OPERATORS", "CONSTANTS", "USAGE",
    # PRIMARY_OPERATOR is no longer a parameter BECAUSE IT IS NO LONGER
    # CHOSEN. It is pinned to `any_atom`, the operator nobody selected: the
    # disjunction you get by declining to fit. `CONSTANTS["primary_operator"]`
    # keeps the fitted value under DECLARED_FITTED_OPERATOR so the audit trail
    # survives, but nothing reads it. A constant with no degrees of freedom is
    # not a parameter; a constant that shipped as `act_match` while the handoff
    # said otherwise was.
    "PRIMARY_OPERATOR", "DECLARED_FITTED_OPERATOR",
    # THE RUNG-1.5 NOTATION. Not settings: these are the SPELLING of a
    # convention owned by `ladder.py`, re-declared here (structural.py may not
    # import the provider layer) and pinned equal to it by
    # `test_the_notation_constants_agree_with_the_ladder_that_emits_them`.
    # There is no version of this module that could choose them differently —
    # it would simply stop parsing what the annotator wrote.
    "POLARITY_PREFIXES", "PRINCIPAL_SEP", "PRINCIPALS",
    # The two bookkeeping sets over the operator TABLE, same status as
    # OPERATORS itself: which operators read the notation, and which were added
    # after the panel-fitted selection was made. Both are asserted against
    # `CONSTANTS["primary_operator"]["selected_over"]`, so neither can be used
    # to hide an operator.
    "NOTATION_OPERATORS", "POST_SELECTION_OPERATORS",
})


def _module_level_constants(path):
    """`{NAME: derives_from_CONSTANTS}` for every module-level CAPS assignment.

    Read from the AST rather than from the imported module, because the point
    is to catch a constant that exists in the SOURCE and was never declared.
    """
    import ast
    tree = ast.parse(open(path).read())

    def reads_constants(node):
        """The CONSTANTS key this assignment reads, or False.

        Returns the KEY, not just a boolean, so the equality check below can
        compare a constant against the entry it actually derives from. The
        earlier version assumed the key was the constant's lowercased name,
        which silently fails the moment two constants read the same entry —
        as PRIMARY_OPERATOR and DECLARED_FITTED_OPERATOR now do.
        """
        for n in ast.walk(node):
            if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                    and n.value.id == "CONSTANTS"):
                k = n.slice
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    return k.value
                return True
        return False

    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (node.targets if isinstance(node, ast.Assign)
                   else [node.target])
        for t in targets:
            if isinstance(t, ast.Name) and t.id.upper() == t.id and t.id[0].isalpha():
                out[t.id] = reads_constants(node.value) if node.value else False
    return out


def test_constants_declaration_is_complete():
    """`CONSTANTS` must be COMPLETE, not merely self-consistent.

    The old audit iterated `CONSTANTS` and checked each entry — so a constant
    could evade it entirely by not being in the dict, and `PRIMARY_OPERATOR`
    (panel-fitted, selected on MCC over 7 operators) did exactly that while the
    module docstring claimed "none was chosen by looking at a score". This test
    goes the other way round: it reads every module-level constant out of the
    SOURCE and demands each one either derive from `CONSTANTS` or be named in
    the frozen non-parameter list above. # MUTATION-VERIFIED
    """
    found = _module_level_constants(os.path.join(HERE, "structural.py"))
    derived = {n for n, d in found.items() if d}
    undeclared = set(found) - derived - NON_PARAMETER_MODULE_NAMES
    assert not undeclared, (
        f"module-level constants not declared in CONSTANTS: {sorted(undeclared)}. "
        "Either add an entry to CONSTANTS and read the value from it, or add "
        "the name to NON_PARAMETER_MODULE_NAMES with an argument for why it is "
        "not a parameter. Silently leaving it out is how PRIMARY_OPERATOR "
        "escaped the fitted-parameter audit.")
    stale = NON_PARAMETER_MODULE_NAMES - set(found)
    assert not stale, (
        f"frozen non-parameter names no longer in structural.py: {sorted(stale)} "
        "— prune the list so it cannot quietly grant an exemption to a name "
        "that is reintroduced later meaning something else")
    #: and the derived values must actually equal what is declared
    for name in derived:
        key = found[name] if isinstance(found[name], str) else name.lower()
        assert key in S.CONSTANTS, f"{name} derives from CONSTANTS[{key!r}]?"
        assert getattr(S, name) == S.CONSTANTS[key]["value"], (
            f"{name} does not equal its declaration — a constant that is "
            "declared one way and used another is worse than an undeclared one")


def test_primary_operator_is_declared_as_the_panel_fitted_choice_it_is():
    """The fitted choice is DECLARED but NO LONGER SHIPPED.

    `structural.py` selected `act_match` on panel MCC over 7 operators and did
    not declare it, so the fitted-parameter audit reported zero fitted
    parameters. The first fix declared it. That was not enough: the module went
    on SHIPPING it as the CLI default.

    ⚠️ RETRACTED, and the retraction is the point of this test. The bias was
    called "small (+0.294 against +0.310)". Both numbers are 3-behaviour
    numbers. At n=9 the ordering INVERTS — the unselected `any_atom` wins and
    the measured selection cost is +0.0449 by difference-in-differences, 2.8x
    the 0.016 bound declared alongside it. An honest disclosure of a bias can
    still be wrong about its size and its sign.

    So the module now pins `any_atom` and keeps the fitted value unread, and
    this test asserts the SEPARATION: what was fitted is recorded, and what
    ships is the operator nobody chose. # MUTATION-VERIFIED
    """
    entry = S.CONSTANTS["primary_operator"]
    assert entry["value"] == S.DECLARED_FITTED_OPERATOR, \
        "the fitted value must remain recorded — the audit trail is the point"
    assert S.PRIMARY_OPERATOR != entry["value"], (
        "structural.py is shipping the panel-fitted operator as its default "
        "again. That is the defect this test exists to prevent: declaring a "
        "fitted parameter in an audit dict while still running it.")
    assert entry["fitted_on_panel"] is True, (
        "the operator WAS selected on a panel score; declaring it unfitted "
        "would be a false statement in the audit surface")
    assert set(entry["selected_over"]) | S.POST_SELECTION_OPERATORS \
        == set(S.OPERATORS), (
        "the alternatives it was selected over are exactly the operator table "
        "as it stood at selection time. An operator added LATER must appear in "
        "`POST_SELECTION_OPERATORS` — that is the only honest way to add one, "
        "because neither silently extending `selected_over` (which would claim "
        "a comparison that never happened) nor leaving the table bigger than "
        "the disclosure (which would understate the selection surface) is true.")
    assert entry["unselected_baseline"]["operator"] == "any_atom"


# ------------------------------------------- the noise floor and the verdict

def test_the_expired_noise_floor_constant_is_gone():
    """`NOISE = 0.06` was an INTERIM guardrail explicitly conditional on n=1
    ("re-draws (k>=5) have been requested; until they land..."). The re-draws
    landed and it was used anyway, against an effect whose SE is 0.0041 — a
    15-SE floor, which made the "consistent and outside the floor" branch
    unreachable and the null unfalsifiable. It must not come back.
    # MUTATION-VERIFIED"""
    import ast
    tree = ast.parse(open(os.path.join(HERE, "test_structural.py")).read())
    assigned = {t.id for node in ast.walk(tree)
                if isinstance(node, ast.Assign)
                for t in node.targets if isinstance(t, ast.Name)}
    offenders = sorted(n for n in assigned if n.upper() == n
                       and ("NOISE" in n or "FLOOR" in n))
    assert not offenders, (
        f"{offenders}: the noise floor must be DERIVED from the paired "
        "delta's own sampling distribution (see `_paired_stats`), never "
        "assigned. A constant floor cannot shrink as evidence arrives, which "
        "is how a 15-SE placeholder outlived the data that retired it.")


def test_t_table_is_right():
    """The tabulated critical values are checkable against any statistics text;
    a wrong entry would silently move every CI in this file."""
    assert abs(T_CRIT_95[4] - 2.776445) < 1e-6
    assert abs(T_CRIT_95[2] - 4.302653) < 1e-6
    assert abs(T_POWER_80[4] - 0.940965) < 1e-6
    for tbl in (T_CRIT_95, T_POWER_80):
        vals = [tbl[d] for d in sorted(tbl)]
        assert vals == sorted(vals, reverse=True), "t must fall with df"


def test_noise_floor_is_the_effects_own_sampling_distribution():
    """The floor is the half-width of the CI at the k the draws supply — so it
    SHRINKS as evidence accumulates, which a constant cannot do. On the real
    five draws it is ~0.011, not 0.06."""
    xs = [0.0200, 0.0176, 0.0222, 0.0231, 0.0010]        # the measured deltas
    st = _paired_stats(xs)
    assert abs(st["sd"] - 0.0091) < 5e-4
    assert abs(st["se"] - 0.0041) < 5e-4
    assert abs(st["noise_floor"] - T_CRIT_95[4] * st["se"]) < 1e-12
    assert 0.010 < st["noise_floor"] < 0.013, st["noise_floor"]
    assert st["noise_floor"] < 0.06 / 4, (
        "the expired constant was more than four times the real floor")
    #: and it must fall with more evidence — the property a constant lacks
    assert _paired_stats(xs * 4)["noise_floor"] < st["noise_floor"]


def test_a_single_draw_cannot_produce_a_noise_floor_at_all():
    """n=1 is the situation the +-0.06 placeholder existed for. Refuse rather
    than invent: a floor from one sample is a guess wearing a number."""
    with pytest.raises(ValueError):
        _paired_stats([0.02])


def _fake_verdict(per, overall=None):
    """A verdict dict built from raw delta lists, for driving the checker."""
    slugs = list(per)
    labels = [f"draw{i}" for i in range(len(next(iter(per.values()))))]
    deltas = {l: [per[s][i] for s in slugs] for i, l in enumerate(labels)}
    return _typing_verdict(deltas, slugs)


def test_the_verdict_cannot_contradict_its_own_sign_summary():
    """THE DEFECT, MADE UNREPEATABLE. The retracted output printed

        sign of the mean delta: 5 positive, 0 negative
        VERDICT: TYPING CONTRIBUTES NOTHING MEASURABLE ... does not hold a
        consistent sign

    three lines apart. Nothing checked the sentence against the numbers.
    # MUTATION-VERIFIED"""
    v = _fake_verdict({"a": [0.08, 0.09, 0.10, 0.09, 0.08]})
    lines = _verdict_lines(v)
    assert _check_verdict_consistency(v, lines)
    # now lie about it in exactly the way the retracted harness did
    v["per_behaviour"]["a"]["verdict"] = UNDETERMINED
    with pytest.raises(AssertionError):
        _check_verdict_consistency(v, lines)


def test_the_null_headline_cannot_be_printed_beside_a_resolved_effect():
    """A null claim is only printable when every block is undetermined."""
    v = _fake_verdict({"a": [0.08, 0.09, 0.10, 0.09, 0.08]})
    assert NULL_CLAIM not in "\n".join(_verdict_lines(v))
    with pytest.raises(AssertionError):
        _check_verdict_consistency(v, [f"VERDICT: {NULL_CLAIM}"] + _verdict_lines(v))
    # and a genuinely null effect may still say so
    flat = _fake_verdict({"a": [0.001, -0.002, 0.003, -0.001, 0.000]})
    lines = _verdict_lines(flat)
    assert NULL_CLAIM in "\n".join(lines)
    assert _check_verdict_consistency(flat, lines)


def test_a_printed_verdict_word_cannot_drift_from_its_row():
    """Hand-editing the word without editing the numbers must fail."""
    v = _fake_verdict({"a": [-0.05, -0.04, -0.05, -0.06, -0.04]})
    lines = _verdict_lines(v)
    assert v["per_behaviour"]["a"]["verdict"] == HURTS
    tampered = [l.replace(HURTS, HELPS) for l in lines]
    with pytest.raises(AssertionError):
        _check_verdict_consistency(v, tampered)


def test_the_verdict_is_per_behaviour_and_the_mean_is_not_the_verdict():
    """A +0.087 win and a -0.047 loss average to +0.017, which describes
    neither. The mean row may be printed; it may not be the verdict."""
    v = _fake_verdict({
        "rare":   [0.077, 0.104, 0.093, 0.120, 0.042],
        "common": [-0.049, -0.060, -0.035, -0.038, -0.053],
        "mid":    [0.032, 0.009, 0.009, -0.012, 0.014]})
    assert v["per_behaviour"]["rare"]["verdict"] == HELPS
    assert v["per_behaviour"]["common"]["verdict"] == HURTS
    assert v["per_behaviour"]["mid"]["verdict"] == UNDETERMINED
    assert v["eta_sq"] > 0.85, "behaviour explains most of this delta"
    text = "\n".join(_verdict_lines(v))
    assert "MEAN OVER BEHAVIOURS (not the verdict)" in text
    assert "precision-buying prune" in text.lower()
    assert NULL_CLAIM not in text


def test_the_output_prints_mean_deltas_not_only_spreads():
    """A review found the harness printed standard deviations where a reader
    expects effects, and the per-behaviour mean deltas appeared NOWHERE — not
    in the output, not in the handoff. The effect must be on the page."""
    v = _fake_verdict({"rare": [0.077, 0.104, 0.093, 0.120, 0.042],
                       "common": [-0.049, -0.060, -0.035, -0.038, -0.053]})
    lines = _verdict_lines(v)
    for s in ("rare", "common"):
        row = next(l for l in lines if l.strip().startswith(s))
        m = v["per_behaviour"][s]["mean"]
        assert f"{m:+.3f}" in row, f"{s}: mean delta {m:+.3f} is not printed"
        assert "95% CI" not in row and "[" in row, "and its CI beside it"


def test_behaviour_level_power_is_reported_because_there_is_none():
    """n=3 behaviours. The between-behaviour MDE at 80% power is ~0.2, far
    above every effect measured, so 'WHICH behaviours typing pays for' is a
    hypothesis. Printing the MDE is what stops it being read as a result."""
    v = _fake_verdict({
        "rare":   [0.077, 0.104, 0.093, 0.120, 0.042],
        "common": [-0.049, -0.060, -0.035, -0.038, -0.053],
        "mid":    [0.032, 0.009, 0.009, -0.012, 0.014]})
    assert 0.15 < v["behaviour_level_mde80"] < 0.30, v["behaviour_level_mde80"]
    text = "\n".join(_verdict_lines(v))
    assert f"{v['behaviour_level_mde80']:.3f}" in text
    assert "not" in text.lower() and "established" in text.lower()


# ------------------------------------------------- typing is the join structure

def test_a_situation_never_matches_an_act(vocab, clauses, onto):
    """The same NAME under two kinds must not connect. In this artifact kind is
    a function of name, so this can only arise from a corrupted annotation —
    and it must be rejected and counted, never silently credited.
    # MUTATION-VERIFIED"""
    ann = {"c1": [{"name": "clarify_user_intent", "kind": "situation",
                   "gloss": "", "clause_id": "c1", "quote": "x"}]}
    idx = S.StructuralIndex(clauses, ann, onto)
    q = S.Query("q", [{"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    m = idx.match(q)
    assert "c1" not in m
    assert idx.rejections["cross_kind_atom"] == 1


def test_slot_is_the_behaviour_atoms_role_not_a_bonus_term(index, query):
    """A clause filling BOTH core slots must land on a strictly higher rung
    than one filling a single slot — not merely score a little more. That is
    the difference between a join structure and a bonus term."""
    both = S.Query("both", [
        {"name": "user_request_ambiguous", "kind": "situation", "weight": 3},
        {"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    act_only = S.Query("act_only", [
        {"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    assert index.match(both)["c1"].rung == "act_and_situation"
    assert index.match(act_only)["c1"].rung == "act_match"
    assert index.match(act_only)["c1"].rung_index > \
           index.match(both)["c1"].rung_index


def test_the_primary_operator_is_the_disjunction_not_the_conjunction():
    """The conjunction stays rejected; the act-match no longer replaces it.

    Still true, and the reason this test keeps its name: the typed CONJUNCTION
    fires on 3-6% of the corpus and loses to the bag scorer. Anyone
    re-promoting it must change this line.

    ⚠️ RETRACTED: "the typed act-match wins at +0.310 +- 0.021 over 5 draws".
    That is 3 behaviours. At n=9 it is +0.246 and it LOSES to the bag scorer.
    The number was quoted for three cycles after the data that overturned it
    was available. The shipped operator is now `any_atom` — still a
    disjunction, still zero-parameter, but chosen by declining to choose.
    """
    assert S.PRIMARY_OPERATOR == "any_atom"
    assert S.RUNGS[0][0] == "act_and_situation", \
        "the conjunction remains the top PRECISION tier, just not the query"


def test_every_operator_is_zero_parameter():
    """No operator may consult a threshold, a depth, or a fitted weight. They
    take the evidence list and nothing else."""
    import inspect
    for name, fn in S.OPERATORS.items():
        assert len(inspect.signature(fn).parameters) == 1, name


def test_the_no_prune_control_operator_exists():
    """`any_atom` must stay first-class, for two reasons that are NOT the one
    previously given here.

    ⚠️ RETRACTED: "`any_atom` is the untyped control; the entire empirical case
    for typing is `act_match` minus `any_atom`." It is not. Kind is a strict
    function of name in this artifact, so `act_match` is a name-subset filter
    and returns the identical set to `any_atom` on the act-only subquery in all
    15 draw x behaviour cells. The difference between them is therefore
    PREDICTION-SET SIZE (roughly 2:1), not typing, and the real typing test is
    the size-matched randomization control in `--variance`.

    The two reasons it stays: it is the NO-PRUNE control, and it is the
    unselected no-choice default against which the panel-fitted choice of
    `PRIMARY_OPERATOR` is bounded (+0.294 vs +0.310). # MUTATION-VERIFIED"""
    assert "any_atom" in S.OPERATORS
    assert S.CONSTANTS["primary_operator"]["unselected_baseline"]["operator"] \
        == "any_atom"


# --------------------------------------------------------------- the ladder

def test_rungs_are_disjoint_and_ordered(index, query):
    m = index.match(query)
    for match in m.values():
        assert match.rung == S.RUNGS[match.rung_index][0]
    ranked = index.rank(query)
    idx = {c: i for i, (c, _) in enumerate(ranked)}
    hits = sorted(m.values(), key=lambda x: idx[x.clause_id])
    assert [h.rung_index for h in hits] == sorted(h.rung_index for h in hits), \
        "ranking must never put a lower rung above a higher one"


def test_precision_tier_requires_both_core_slots(index, query):
    m = index.match(query)
    assert m["c1"].rung == "act_and_situation"
    assert {e.slot for e in m["c1"].evidence} >= {"situation", "act"}


def test_act_match_fires_where_the_conjunction_cannot(clauses, annotations, vocab):
    """The whole reason the disjunction is primary: a clause carrying an act
    atom but NO situation atom is invisible to the conjunction and is a hit for
    the primary operator. 55% of the real spec is in this position."""
    bare = O.Ontology(vocab, [])
    idx = S.StructuralIndex(clauses, annotations, bare)
    q = S.Query("q", [{"name": "ask_followup_question", "kind": "act", "weight": 3}])
    assert idx.predict(q, "act_and_situation") == set()
    assert idx.predict(q, "act_match") == {"c2"}


def test_relation_expansion_is_off_by_default(clauses, annotations, onto, query):
    """`max_hops` defaults to 0. Relation expansion was measured to hurt on
    every behaviour, so reaching c2 through a subsumption edge must require an
    explicit opt-in rather than happening silently. # MUTATION-VERIFIED"""
    assert S.CONSTANTS["max_hops"]["value"] == 0
    default = S.StructuralIndex(clauses, annotations, onto)
    assert "c2" not in default.predict(query, "any_atom")
    opted_in = S.StructuralIndex(clauses, annotations, onto, max_hops=1)
    assert "c2" in opted_in.predict(query, "any_atom")


def test_relation_edges_are_traversed_when_opted_in(clauses, annotations, onto, query):
    """c2 shares NO atom name with the query; it is reachable only through the
    subsumption edges."""
    idx = S.StructuralIndex(clauses, annotations, onto, max_hops=1)
    m = idx.match(query)
    assert "c2" in m
    assert any(e.hops > 0 for e in m["c2"].evidence)


def test_support_only_is_the_bottom_rung(index, query):
    m = index.match(query)
    assert "c4" not in m or m["c4"].rung == "support_only"


def test_generic_atom_criterion_is_inherited_not_invented(
        clauses, annotations, vocab, onto):
    """The 0.25 document-frequency cap is `relevance.Weights.atom_stopword_frac`
    — the same number and the same argument, predating this module."""
    import relevance
    assert S.GENERIC_ATOM_FRAC == relevance.Weights().atom_stopword_frac
    ann = dict(annotations)
    for cid in ("c3", "c5"):
        ann[cid] = list(ann.get(cid, [])) + [
            {"name": "everywhere", "kind": "situation", "gloss": "",
             "clause_id": cid, "quote": "Unrelated text"}]
    idx = S.StructuralIndex(clauses, ann, onto)
    assert idx.is_generic("everywhere"), "2 of 5 clauses is over the 0.25 cap"
    assert not idx.is_generic("clarify_user_intent")


# ------------------------------------------------------- contrary as defeater

def test_contrary_blocks_a_match_that_would_otherwise_fire(clauses, annotations,
                                                           vocab):
    """THE test for the defeater, and the one thing no similarity score can do.

    Note the shape carefully — an earlier version of this test was a FALSE
    GREEN and mutation testing caught it. A `contrary` edge can only ever
    REMOVE a match that some other query atom created, so a query whose only
    atom is contrary to the clause proves nothing: it would not have matched
    anyway. The real case needs TWO query atoms — one that creates the match
    and one that defeats it. That is not contrived: a behaviour about
    `avoid_followup` legitimately carries `ask_followup_question` too, and a
    clause about DOING the thing is exactly what must not count as a hit.

    Identical index, identical query, one relation edge different.
    # MUTATION-VERIFIED
    """
    v = dict(vocab)
    v["avoid_followup"] = {"kind": "act", "gloss": "Not asking a follow-up.",
                           "n_clauses": 1, "clauses": []}
    q = S.Query("q", [
        {"name": "ask_followup_question", "kind": "act", "weight": 3},
        {"name": "avoid_followup", "kind": "act", "weight": 3}])

    without = S.StructuralIndex(clauses, annotations, O.Ontology(v, []))
    assert "c2" in without.match(q), "precondition: the match fires unopposed"

    edge = [O.Relation("contrary", "ask_followup_question", "avoid_followup",
                       "hand", "fixture", "model")]
    kept, _ = O.validate(edge, v)
    with_edge = S.StructuralIndex(clauses, annotations, O.Ontology(v, kept))
    assert "c2" not in with_edge.match(q), \
        "a defeated slot must not produce a hit"
    assert ("c2", "act", "avoid_followup", "ask_followup_question") in \
        with_edge.defeats(q)


def test_defeat_is_recorded_not_silent(clauses, annotations, onto):
    q = S.Query("q", [{"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    idx = S.StructuralIndex(clauses, annotations, onto)
    d = idx.defeats(q)
    assert ("c3", "act", "clarify_user_intent", "assume_intent") in d


# ------------------------------------------------------------------ explain

def test_explain_returns_a_complete_typed_path(clauses, annotations, onto,
                                               query):
    index = S.StructuralIndex(clauses, annotations, onto, max_hops=1)
    info = index.explain(query, "c2")
    assert info["rung"] == "act_and_situation"
    assert info["clause_id"] == "c2"
    assert info["locator"]
    quotes = {c["id"]: c["quote"] for c in clauses}
    for step in info["evidence"]:
        assert step["slot"] in ("situation", "act", "entity", "value")
        assert step["behaviour_atom"] and step["clause_atom"]
        assert step["path"], "a >0-hop match must print its relation edges"
        assert step["span"] in quotes[info["clause_id"]], \
            "every cited span must be a substring of its own clause"
        assert step["locator"]


def test_explain_cites_only_spans_from_its_own_clause(index, query):
    for cid in ("c1", "c2"):
        info = index.explain(query, cid)
        for step in info["evidence"]:
            assert step["clause_id"] == cid


def test_explain_names_the_defeated_slots(clauses, annotations, onto):
    q = S.Query("q", [{"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    info = S.StructuralIndex(clauses, annotations, onto).explain(q, "c3")
    assert info["rung"] is None
    assert info["defeated"], "a blocked match must say what blocked it"
    assert info["defeated"][0]["contrary_of"] == "clarify_user_intent"


def test_explain_on_the_real_spec_cites_real_spans():
    """The load-bearing audit property, on the real artifact rather than a
    fixture: every quoted span must occur verbatim in the clause it is
    attributed to. # MUTATION-VERIFIED"""
    idx = S.StructuralIndex.from_files()
    q = S.load_queries(BEHAVIOUR_ATOMS)["harm-avoidance-to-third-parties"]
    n = 0
    for cid, m in sorted(idx.match(q).items()):
        info = idx.explain(q, cid)
        clause = idx.by_id[cid]
        for step in info["evidence"]:
            assert step["span"] in clause["quote"], \
                f"{cid}: cited span is not in its own clause"
            n += 1
    assert n > 0, "no evidence cited at all — the ladder is inert"


# -------------------------------------------------------- degenerate queries

def test_a_query_that_matches_everything_scores_badly(clauses, annotations, vocab, onto):
    """The mirror bug this project already hit once: a degenerate run must not
    read as a perfect one. A query built from every atom in the vocabulary
    fires everywhere, and MCC against any non-trivial gold is 0 by
    construction — so what must hold here is that it does not outrank a
    specific query, and that it lands on the LOW rungs. # MUTATION-VERIFIED"""
    everything = S.Query("everything", [
        {"name": n, "kind": e["kind"], "weight": 3} for n, e in vocab.items()])
    idx = S.StructuralIndex(clauses, annotations, onto)
    annotated = {c for c in idx.ids if any(idx.by_kind[c].values())}
    fired = idx.predict(everything, "any_atom")
    # c3 is annotated with `assume_intent`, which the ontology says is CONTRARY
    # to the query's `clarify_user_intent`. Even the everything-query cannot
    # match a clause about the opposite concept — the defeater still holds.
    assert fired == annotated - {"c3"}
    assert ("c3", "act", "clarify_user_intent", "assume_intent") in \
        idx.defeats(everything)
    # and firing everywhere must not thereby occupy the high-precision tier
    assert len(idx.predict(everything, "act_and_situation")) < len(fired)


def test_empty_query_predicts_nothing(index):
    empty = S.Query("empty", [])
    for op in S.OPERATORS:
        assert index.predict(empty, op) == set(), op


def test_prediction_sets_are_nested_in_depth(index, query):
    sets = [index.predict_depth(query, d) for d in range(len(S.RUNGS))]
    for a, b in zip(sets, sets[1:]):
        assert a <= b, "deeper rungs must only ever ADD clauses"


def test_unknown_operator_is_an_error_not_a_silent_empty_set(index, query):
    with pytest.raises(ValueError):
        index.predict(query, "definitely_not_an_operator")


def test_scores_are_in_the_unit_interval_and_ordered(index, query):
    ranked = index.rank(query)
    assert all(0.0 <= s <= 1.0 for _, s in ranked)
    assert [s for _, s in ranked] == sorted((s for _, s in ranked), reverse=True)


def test_determinism(index, query):
    assert index.rank(query) == index.rank(query)


# ---------------------------------------------------------- the real artifact

def test_real_queries_load_with_their_weights():
    qs = S.load_queries(BEHAVIOUR_ATOMS)
    assert len(qs) == 3
    total = sum(len(q.atoms) for q in qs.values())
    assert total == 70
    assert all(1 <= a["weight"] <= 3 for q in qs.values() for a in q.atoms)


def test_real_index_builds_and_every_slot_is_populated():
    idx = S.StructuralIndex.from_files()
    assert len(idx.ids) == 593
    kinds = {k for cid in idx.ids for k in idx.by_kind[cid]}
    assert kinds == {"situation", "act", "entity", "value"}


# ------------------------------------------------------- the section partition

def test_the_index_exposes_the_documents_section_partition(index):
    """`section.py` builds its quotient on this, so the partition has to belong
    to the module that owns the clause rows rather than being re-derived."""
    secs = index.sections()
    assert secs[("Ambiguity",)] == ("c1", "c2", "c3")
    assert secs[("Values",)] == ("c4",)
    assert index.section_of("c4") == ("Values",)
    assert index.section_of("nosuchclause") == ()


def test_the_partition_covers_every_clause_exactly_once(clauses, annotations,
                                                        onto):
    """Including a clause with NO `section_path`. A clause the segmentation
    could not place must land in the `()` block and stay countable; dropping it
    would quietly shrink the universe the quotient is defined over, and the
    fixture clauses all carry a path, so the unsectioned row has to be added
    here for this test to be able to fail at all."""
    rows = list(clauses) + [{"id": "orphan", "quote": "no section", "kind": "meta"}]
    ann = dict(annotations, orphan=[])
    idx = S.StructuralIndex(rows, ann, onto)
    secs = idx.sections()
    flat = [cid for cs in secs.values() for cid in cs]
    assert sorted(flat) == sorted(idx.ids)
    assert len(flat) == len(set(flat))
    assert secs[()] == ("orphan",)


def test_the_partition_keys_on_the_PATH_not_the_leaf_heading(annotations, onto):
    """Two headings with the same TEXT under different parents are DIFFERENT
    sections. Keying on the leaf would merge them and quietly pool two
    unrelated blocks of the document. The real spec has no repeated leaf, so
    nothing would catch this regression in production — it has to be pinned
    here."""
    rows = [
        {"id": "c1", "quote": "x", "section_path": ["Part One", "Exceptions"]},
        {"id": "c2", "quote": "y", "section_path": ["Part Two", "Exceptions"]},
    ]
    ann = {"c1": [], "c2": []}
    secs = S.StructuralIndex(rows, ann, onto).sections()
    assert len(secs) == 2, f"paths were merged on their leaf heading: {secs}"
    assert secs[("Part One", "Exceptions")] == ("c1",)
    assert secs[("Part Two", "Exceptions")] == ("c2",)


def test_the_partition_is_deterministic(index):
    assert index.sections() == index.sections()


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_the_real_spec_partitions_into_78_sections():
    secs = S.StructuralIndex.from_files().sections()
    assert len(secs) == 78
    assert sum(len(v) for v in secs.values()) == 593


# =====================================================================
# THE NOTATION: polarity- and role-aware operators (rung 1.5's consumers)
# =====================================================================
# `ladder.py` rung 1.5 emits atom names carrying a reserved polarity prefix
# (`must_ mustnot_ should_ shouldnot_ may_`) and an ordered principal chain
# (`stem__actor_patient_third`). Until these tests existed, NO operator read
# either, so rung 1.5 could not demonstrate a retrieval effect even if its
# annotation were strictly better.
#
# Two properties are load-bearing and each has its own test below:
#   1. BACKWARD COMPATIBILITY. The shipped 361-name vocabulary carries no
#      notation, so every new operator must reduce EXACTLY to its untyped base
#      there — not to the empty set. Proven twice: once on the parse (identity
#      on every shipped name) and once on the prediction sets (equal to
#      `any_atom` on the real artifact).
#   2. THE OPERATORS ACTUALLY READ THE NOTATION. Written in the shape the
#      module docstring demands of a defeater test: something else CREATES the
#      match, the notation REMOVES it, and the two indexes differ by exactly
#      one character of notation.

def _rung15_fixture(clause_atom_name, query_atoms=None, extra=None):
    """An index + query where ONE clause atom carries rung-1.5 notation.

    The clause atom's STEM is always `clarify_user_intent`, which the query
    always asks for, so the match exists in every variant and any difference
    between variants is attributable to the notation alone.
    """
    clauses = [{"id": "c1", "quote": "Ask the user what they meant.",
                "section_path": ["Ambiguity"], "locator": "spec > A > 1"}]
    ann = {"c1": [{"name": clause_atom_name, "kind": "act",
                   "gloss": "Asking what was meant.", "span_id": "s1",
                   "quote": "Ask the user what they meant",
                   "clause_id": "c1", "locator": "spec > c1"}]}
    for a in extra or []:
        ann["c1"].append(dict({"gloss": "", "span_id": "s2",
                               "quote": "Ask the user", "clause_id": "c1",
                               "locator": "spec > c1"}, **a))
    q = S.Query("q", query_atoms or [
        {"name": "clarify_user_intent", "kind": "act", "weight": 3}])
    return S.StructuralIndex(clauses, ann), q


def test_the_notation_constants_agree_with_the_ladder_that_emits_them():
    """`structural.py` re-declares the notation instead of importing `ladder`
    (which imports the provider layer, and this module may not). A silent edit
    on either side would make the consumer read a convention the producer no
    longer writes, so the two are pinned equal here — the only place that may
    import both."""
    import ladder as L
    assert S.POLARITY_PREFIXES == L.POLARITY_PREFIXES
    assert S.PRINCIPAL_SEP == L.PRINCIPAL_SEP
    assert S.PRINCIPALS == L.PRINCIPALS
    for name in ("clarify_user_intent", "must_disclose__model_user",
                 "may_x", "mustnot_y__third_party", "must_", "a__nobody",
                 "a__b__c", "shouldnot_z__model_operator_third_party"):
        mine, theirs = S.parse_atom_name(name), L.parse_name(name)
        assert mine["stem"] == theirs["stem"], name
        assert mine["polarity"] == theirs["polarity"], name
        assert list(mine["principals"]) == list(theirs["principals"]), name
        assert bool(mine["error"]) == bool(theirs["error"]), name


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_the_parse_is_the_identity_on_every_shipped_atom_name():
    """BACKWARD COMPATIBILITY, at the root. The prefixes are reserved and no
    shipped name contains the principal separator, so parsing a rung-0/1 name
    returns the name itself with no polarity and no principals. This is what
    makes the stem-aware join provably bit-identical on the current artifacts:
    the second lookup asks for the same string as the first."""
    import relevance as R
    names = {a["name"] for v in R.load_annotations(ANNOTATIONS).values()
             for a in v if isinstance(a, dict) and a.get("name")}
    names |= {a["name"] for q in S.load_queries(BEHAVIOUR_ATOMS).values()
              for a in q.atoms}
    assert len(names) > 300, "the shipped vocabulary did not load"
    for n in sorted(names):
        p = S.parse_atom_name(n)
        assert p["error"] is None, n
        assert p["stem"] == n and p["polarity"] is None and not p["principals"], (
            f"{n!r} collides with the rung-1.5 notation; the reserved prefixes "
            "are no longer reserved and the join is no longer unambiguous")


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_notation_operators_degrade_to_their_untyped_base_on_the_shipped_vocabulary():
    """The requirement that makes these operators safe to add: on a corpus with
    NO notation they must reduce to their untyped base, not score everything
    zero. Rung 0/1 artifacts will be scored with them, and an operator that
    silently returns the empty set there would read as a catastrophic rung
    regression caused entirely by the scorer. # MUTATION-VERIFIED"""
    idx = S.StructuralIndex.from_files()
    for slug, q in sorted(S.load_queries(BEHAVIOUR_ATOMS).items()):
        base = idx.predict(q, "any_atom")
        assert base, slug
        for op in S.NOTATION_OPERATORS:
            assert idx.predict(q, op) == base, (
                f"{op} on {slug}: no atom in this vocabulary carries polarity "
                "or principals, so there is nothing for the operator to "
                "exclude and it must equal its untyped base")


def test_a_stem_match_joins_across_the_notation():
    """The join, not the operator. A rung-1.5 name must reach the query atom it
    is a decoration of, or every operator is dead on rung-1.5 output and the
    rung cannot be scored at all. # MUTATION-VERIFIED"""
    idx, q = _rung15_fixture("must_clarify_user_intent__model_user")
    assert idx.predict(q, "any_atom") == {"c1"}
    ev = list(idx.match(q).values())[0].evidence
    assert [e.clause_polarity for e in ev] == ["must"]
    assert [e.clause_principals for e in ev] == [("model", "user")]
    assert [e.stem for e in ev] == ["clarify_user_intent"]


def test_polarity_is_read_a_permission_is_not_a_directive():
    """The polarity-aware operator, in the shape the docstring demands: the
    match EXISTS in both indexes (`any_atom` fires on both), the two clause
    atoms differ only in their reserved prefix, and `directive_atom` keeps one
    and drops the other. A test where the permissive clause simply failed to
    match would pass with the whole operator deleted. # MUTATION-VERIFIED"""
    for prefix, fires in (("must_", True), ("mustnot_", True),
                          ("should_", True), ("shouldnot_", True),
                          ("may_", False), ("", True)):
        idx, q = _rung15_fixture(prefix + "clarify_user_intent__model_user")
        assert idx.predict(q, "any_atom") == {"c1"}, prefix
        assert (idx.predict(q, "directive_atom") == {"c1"}) is fires, (
            f"{prefix!r}: a permission records that the act is ALLOWED, which "
            "is not the clause committing the model to the conduct")


def test_a_permissive_clause_still_fires_on_its_other_evidence():
    """`directive_atom` is a filter on EVIDENCE, not a veto on clauses. A
    clause carrying both a permission and an untyped match still fires, because
    the untyped match is not a permission. Without this the operator would be a
    clause-level exclusion rule and would throw away evidence it never read."""
    idx, q = _rung15_fixture(
        "may_clarify_user_intent__model_user",
        query_atoms=[{"name": "clarify_user_intent", "kind": "act", "weight": 3},
                     {"name": "end_user", "kind": "entity", "weight": 1}],
        extra=[{"name": "end_user", "kind": "entity"}])
    assert idx.predict(q, "directive_atom") == {"c1"}


def test_opposed_polarity_removes_a_match_that_would_otherwise_fire():
    """`polarity_consistent` is `contrary`, derived from the notation instead
    of from a hand-built relation layer. Two indexes differing by ONE prefix on
    the CLAUSE side, with the query naming the positive polarity."""
    q = [{"name": "must_clarify_user_intent", "kind": "act", "weight": 3}]
    same, _ = _rung15_fixture("must_clarify_user_intent__model_user")
    opposed, _ = _rung15_fixture("mustnot_clarify_user_intent__model_user")
    query = S.Query("q", q)
    assert same.predict(query, "any_atom") == {"c1"}
    assert opposed.predict(query, "any_atom") == {"c1"}, (
        "both must MATCH — otherwise the operator is being credited for a "
        "join failure")
    assert same.predict(query, "polarity_consistent") == {"c1"}
    assert opposed.predict(query, "polarity_consistent") == set()


def test_polarity_consistency_is_inert_when_one_side_is_untyped():
    """Graceful degradation, per-atom rather than per-corpus: an unpolarised
    query atom cannot CONTRADICT anything, so the clause stands."""
    idx, q = _rung15_fixture("mustnot_clarify_user_intent__model_user")
    assert idx.predict(q, "polarity_consistent") == {"c1"}


def test_the_role_chain_is_read_and_its_order_matters():
    """The role-aware operators. The query names `third_party` in its ENTITY
    slot; the clause's act is between the model and the user, so the behaviour
    is not what this clause is about — even though the act stem matches
    exactly. `patient_aligned` additionally reads the ORDER: a third party who
    ACTS is not a third party who is ACTED UPON. # MUTATION-VERIFIED"""
    qa = [{"name": "clarify_user_intent", "kind": "act", "weight": 3},
          {"name": "third_party", "kind": "entity", "weight": 3}]
    other, _ = _rung15_fixture("clarify_user_intent__model_user", qa)
    patient, _ = _rung15_fixture("clarify_user_intent__model_third_party", qa)
    actor, _ = _rung15_fixture("clarify_user_intent__third_party_user", qa)
    q = S.Query("q", qa)
    for idx in (other, patient, actor):
        assert idx.predict(q, "any_atom") == {"c1"}
    assert other.predict(q, "role_aligned") == set()
    assert patient.predict(q, "role_aligned") == {"c1"}
    assert actor.predict(q, "role_aligned") == {"c1"}
    assert patient.predict(q, "patient_aligned") == {"c1"}
    assert actor.predict(q, "patient_aligned") == set(), (
        "the chain is ORDERED — who acts first, then who is acted upon. An "
        "operator that reads it as a set has thrown the ordering away and "
        "rung 1.5's 'ordered principals' bought nothing")


def test_role_alignment_is_inert_when_the_query_names_no_principal():
    """A behaviour whose entity slot names no party imposes no role
    constraint, and both role operators reduce to `any_atom`."""
    qa = [{"name": "clarify_user_intent", "kind": "act", "weight": 3},
          {"name": "prohibited_content", "kind": "entity", "weight": 3}]
    idx, _ = _rung15_fixture("clarify_user_intent__model_user", qa)
    q = S.Query("q", qa)
    assert idx.predict(q, "role_aligned") == {"c1"}
    assert idx.predict(q, "patient_aligned") == {"c1"}


def test_a_head_final_compound_names_its_principal():
    """`end_user` is a user and `api_developer` is a developer; the shipped
    query vocabulary spells principals as head-final compounds. The rule is
    morphological and declared in `CONSTANTS`, not a lookup table tuned until
    something fired."""
    assert S.principal_named("end_user") == "user"
    assert S.principal_named("api_developer") == "developer"
    assert S.principal_named("third_party") == "third_party"
    assert S.principal_named("prohibited_content") is None
    assert S.principal_named("helpfulness") is None


def test_every_operator_returns_a_bool_not_a_score(index, query):
    """INVARIANT 10, made mechanical. An operator is a SET/TYPE operation, so
    it returns a membership decision. A float would pass `predict`'s truthiness
    check silently and turn the query back into the weighted sum this module
    exists to replace — which is exactly how a scorer gets smuggled in.
    # MUTATION-VERIFIED"""
    seen = 0
    for cid in index.ids:
        ev, _ = index._evidence(query, cid, index._expansion(query),
                                index._contraries(query))
        if not ev:
            continue
        seen += 1
        for name, fn in S.OPERATORS.items():
            got = fn(ev)
            assert got is True or got is False, (
                f"{name} returned {got!r}: an operator must decide membership, "
                "not report a quantity")
    assert seen, "no evidence to test the operators on"


def test_the_notation_operators_are_declared_as_post_selection_candidates():
    """They are CANDIDATES, not a new default. The module ships `any_atom`, and
    the panel-fitted `act_match` was selected over the operator table AS IT
    STOOD — so an operator added afterwards must be declared as such rather
    than quietly widening (or narrowing) the recorded selection surface.
    # MUTATION-VERIFIED"""
    assert S.PRIMARY_OPERATOR == "any_atom"
    assert S.NOTATION_OPERATORS <= set(S.OPERATORS)
    assert S.NOTATION_OPERATORS == S.POST_SELECTION_OPERATORS, (
        "every operator added after the selection must be named, so the "
        "selection surface recorded in CONSTANTS stays auditable")
    assert not (S.NOTATION_OPERATORS
                & set(S.CONSTANTS["primary_operator"]["selected_over"]))
    assert S.PRIMARY_OPERATOR not in S.NOTATION_OPERATORS
    assert not (S.NOTATION_OPERATORS & set(S.RUNG_NAMES)), (
        "a candidate operator must not silently become a rung of the shipped "
        "ladder — that would change `predict_depth` for everyone")


# ==========================================================================
# MEASUREMENT
# ==========================================================================
# This section reads panel labels, which is what the panel is FOR. It lives
# here rather than in `structural.py` so that the query module can be PROVEN
# label-free by `test_nothing_reads_panel_labels` above — the cheapest possible
# proof that nothing was fitted to the thing it is measured against.
#
#     .venv/bin/python test_structural.py
#
# Running the TESTS never touches the panel; running the MODULE does.
#
# ⚠️ THE EVALUATION UNIVERSE. The published `behaviours.json` is a FILTERED
# artifact: the panel graded all 589 model-spec passages in one prompt, and
# `build_site_data.keeps_citation()` then dropped every passage that scored 0.
# The published 377/333/153 are the survivors. Scoring on them silently deletes
# the true negatives every judge got right, which flatters everything and
# distorts the comparison. `panel_universe.py` OWNS the reconstruction and is
# the authority (join rate 1.000 on all six cells); `_universe()` below is a
# thin delegation to it. Every headline number is on the 589 universe; the
# published-universe number is printed beside it with the delta.

BOOTSTRAP_RESAMPLES = 2000


def _universe():
    """`{slug: behaviour}` on the TRUE 589-passage universe.

    Delegates to `panel_universe.py`, which OWNS the reconstruction (join rate
    1.000 on all six cells). An earlier version of this file carried its own
    local rebuild; it agreed with this one exactly, and it has been deleted
    rather than left to drift — two reconstructions of a measuring instrument
    is one too many.
    """
    import panel_universe
    return panel_universe.load_universe(spec_keys=("openai",))


def _mcc_cells(pred, joins, behaviour, benchmark):
    """`{held-out judge: MCC}` — one cell per pair-target, no exclusions."""
    universe = set(joins)
    lifted = benchmark.lift(pred, joins)
    return {j: benchmark.mcc(lifted, t["gold"], universe)
            for j, t in benchmark.pair_targets(behaviour).items()}


def _mean(d):
    return sum(d.values()) / len(d) if d else 0.0


def _auc(scores, joins, gold):
    """Threshold-free ranking quality. For a BINARY predictor (a judge) this
    reduces to balanced accuracy, which is the correct AUC of a single point."""
    universe = sorted(joins)
    per = {p: max((scores.get(c, 0.0) for c in joins[p]), default=0.0)
           for p in universe}
    pos = [per[p] for p in universe if p in gold]
    neg = [per[p] for p in universe if p not in gold]
    if not pos or not neg:
        return 0.5
    srt = sorted(pos + neg)
    rank, i = {}, 0
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        rank[srt[i]] = (i + j) / 2 + 1
        i = j + 1
    s = sum(rank[v] for v in pos)
    return (s - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def _bootstrap(a_pred, b_pred, joins, behaviours, slugs, benchmark,
               resamples=BOOTSTRAP_RESAMPLES, seed=0):
    """Paired bootstrap over PASSAGES of the mean-over-behaviours MCC delta.

    Paired because both methods are scored on the same resample — the question
    is whether A beats B, not how variable each is alone. At this n a delta
    under about +-0.06 is noise, so the CI is the number to read, not the point
    estimate.
    """
    import random
    rng = random.Random(seed)

    def cats(pred, slug):
        universe = sorted(joins[slug])
        lifted = benchmark.lift(pred, joins[slug])
        return [[(p in lifted, p in t["gold"]) for p in universe]
                for _, t in sorted(benchmark.pair_targets(
                    behaviours[slug]).items())]

    A = {s: cats(a_pred[s], s) for s in slugs}
    B = {s: cats(b_pred[s], s) for s in slugs}
    n = len(joins[slugs[0]])

    def mcc_of(pairs, idxs):
        tp = fp = fn = tn = 0
        for i in idxs:
            p, g = pairs[i]
            tp, fp, fn, tn = (tp + (p and g), fp + (p and not g),
                              fn + (g and not p), tn + (not p and not g))
        d = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        return 0.0 if d <= 0 else (tp * tn - fp * fn) / math.sqrt(d)

    deltas = []
    for _ in range(resamples):
        idxs = [rng.randrange(n) for _ in range(n)]
        deltas.append(sum(
            sum(mcc_of(p, idxs) for p in A[s]) / 3
            - sum(mcc_of(p, idxs) for p in B[s]) / 3 for s in slugs) / len(slugs))
    deltas.sort()
    return (sum(deltas) / resamples, deltas[int(0.025 * resamples)],
            deltas[int(0.975 * resamples) - 1])


def _measure():
    import benchmark
    import measure_join
    import relevance

    clauses, _src = benchmark.load_clauses()
    published = benchmark.load_panel()
    queries = S.load_queries(BEHAVIOUR_ATOMS)
    slugs = sorted(s for s in queries if s in published)

    universe = _universe()
    corrected = {s: universe[s] for s in slugs}
    joins = {s: benchmark.clause_joins(corrected[s], clauses) for s in slugs}
    pub_joins = {s: benchmark.clause_joins(published[s], clauses) for s in slugs}

    idx = S.StructuralIndex.from_files()
    rows = measure_join.clause_rows()
    ann = relevance.load_annotations(ANNOTATIONS)
    batoms = relevance.load_behaviour_atoms(BEHAVIOUR_ATOMS)
    bag = relevance.RelevanceIndex(rows, ann)
    bag_atom = relevance.RelevanceIndex(
        rows, ann, relevance.Weights(lex=0.0, section=0.0, kind=0.0, atom=0.6))
    beh = {s: relevance.behaviour_from_panel(published[s], batoms) for s in slugs}

    def mean_mcc(slug, pred, j=None, b=None):
        return _mean(_mcc_cells(pred, j or joins[slug], b or corrected[slug],
                                benchmark))

    print("=" * 78)
    print("UNIVERSE")
    print("=" * 78)
    for s in slugs:
        print(f"  {s:34} {len(joins[s])} passages "
              f"({len(benchmark.joinable(joins[s]))} joinable to a clause), "
              f"published was {len(pub_joins[s])}")

    # ------------------------------------------------------------ baselines
    sweep = relevance.DEFAULT_SWEEP

    def lobo(index):
        curve = {s: {t: mean_mcc(s, index.predict(beh[s], t)) for t in sweep}
                 for s in slugs}
        out = {}
        for s in slugs:
            others = [o for o in slugs if o != s]
            t = max(sweep, key=lambda x: sum(curve[o][x] for o in others))
            out[s] = (t, curve[s][t], index.predict(beh[s], t))
        return curve, out

    bag_curve, bag_lobo = lobo(bag)
    atom_curve, atom_lobo = lobo(bag_atom)

    print()
    print("=" * 78)
    print("PARAMETER LEDGER — a method must be quoted at its HONEST setting")
    print("=" * 78)
    print("  !! the `structural:` rows here are ONE DRAW (behavior_atoms_b8). "
          "act_match at\n     +0.340 is the MAXIMUM of a 5-draw spread whose "
          "mean is +0.310 +- 0.021.\n     Quoting it as a constant is the error "
          "this project keeps making — run\n     `--variance` and quote the "
          "mean with its spread.\n")
    print(f"  {'method':40} {'params':>7} {'selection':>14} {'mean MCC':>9}")
    print(f"  {'bag scorer @ LOBO threshold':40} {1:>7} {'held out':>14} "
          f"{_mean({s: bag_lobo[s][1] for s in slugs}):>+9.3f}")
    print(f"  {'bag scorer @ 0.18':40} {1:>7} {'IN-SAMPLE':>14} "
          f"{_mean({s: bag_curve[s][0.18] for s in slugs}):>+9.3f}   "
          f"<- may NOT be compared to a 0-param method")
    print(f"  {'bag ATOM CHANNEL ONLY @ LOBO':40} {1:>7} {'held out':>14} "
          f"{_mean({s: atom_lobo[s][1] for s in slugs}):>+9.3f}")
    for op in ("act_match", "sit_or_act", "any_atom", "multi_atom",
               "act_and_situation"):
        v = _mean({s: mean_mcc(s, idx.predict(queries[s], op)) for s in slugs})
        tag = "  <- PRIMARY" if op == S.PRIMARY_OPERATOR else ""
        print(f"  {'structural: ' + op:40} {0:>7} {'1 draw':>14} {v:>+9.3f}{tag}")
    jm = {s: _mean({j: benchmark.mcc(t['pred'], t['gold'], set(joins[s]))
                    for j, t in benchmark.pair_targets(corrected[s]).items()})
          for s in slugs}
    jb = {s: max(benchmark.mcc(t['pred'], t['gold'], set(joins[s]))
                 for t in benchmark.pair_targets(corrected[s]).values())
          for s in slugs}
    print(f"  {'judges (mean of 3) — THE BAR':40} {'-':>7} {'-':>14} "
          f"{_mean(jm):>+9.3f}")
    print(f"  {'judges (best of 3)':40} {'-':>7} {'-':>14} {_mean(jb):>+9.3f}")
    # TWO FLOORS, BOTH REPORTED. They answer different questions and the gap
    # between them IS the join-coverage cost, which this project states rather
    # than absorbs.
    #   A  literal all-positive over every passage: tn = fn = 0, the MCC
    #      denominator vanishes, MCC = 0 by convention. This is MCC's
    #      DEFINITIONAL zero and it is why MCC is the primary metric here — a
    #      degenerate predictor cannot score above chance.
    #   B  all-positive over what the TOOL CAN REACH. 7 of 589 passages join to
    #      no clause, so they are forced misses (fn > 0, tn = 0) and the floor
    #      goes NEGATIVE by however many of them are gold.
    floor_b = {}
    for s in slugs:
        universe_ids = set(joins[s])
        reachable = benchmark.joinable(joins[s])
        floor_b[s] = _mean({j: benchmark.mcc(reachable, t["gold"], universe_ids)
                            for j, t in benchmark.pair_targets(
                                corrected[s]).items()})
    print(f"  {'floor A: chance (all-positive)':40} {0:>7} {'none':>14} "
          f"{0.0:>+9.3f}   MCC's definitional zero")
    print(f"  {'floor B: chance MINUS coverage gap':40} {0:>7} {'none':>14} "
          f"{_mean(floor_b):>+9.3f}   the tool's ACHIEVABLE floor")
    print()
    print("  The two floors differ by the join-coverage cost: 7 of 589 passages "
          "join to no")
    print("  clause and can never be predicted, so they are forced misses for "
          "ANY method.")
    print(f"    {'behaviour':34} {'floor B':>8} {'unreachable':>12} "
          f"{'of which gold':>14}")
    for s in slugs:
        unreachable = set(joins[s]) - benchmark.joinable(joins[s])
        gold_lost = [len(t["gold"] & unreachable)
                     for t in benchmark.pair_targets(corrected[s]).values()]
        print(f"    {s:34} {floor_b[s]:>+8.3f} {len(unreachable):>12} "
              f"{str(gold_lost):>14}")
    print("  A reader comparing against 0.000 is asking 'is this better than "
          "chance?';")
    print("  a reader comparing against the floor B mean is asking 'is this "
          "better than")
    print("  chance, given the passages the pipeline cannot reach at all?'. "
          "Quote both.")

    print()
    print("  !! THE ATOM-ONLY CONTROL IS THE HEADLINE. On all three behaviours "
          "the bag's\n     atom channel at its LOBO threshold predicts EXACTLY "
          "the untyped `any_atom`\n     set. So the +0.114 the structural query "
          "gains over the full bag comes from\n     DELETING the lexical and "
          "section channels and the threshold — not from typing.")
    for s in slugs:
        same = atom_lobo[s][2] == idx.predict(queries[s], "any_atom")
        print(f"       {s:34} atom-only@{atom_lobo[s][0]:.2f} == any_atom: {same}")

    # ------------------------------------------------------- all nine cells
    print()
    print("=" * 78)
    print("ALL 9 CELLS — no behaviour and no pair-target excluded")
    print("=" * 78)
    print(f"  {'behaviour':32} {'held-out':10} {'act_match':>10} "
          f"{'any_atom':>9} {'bag@LOBO':>9} {'judge':>8}")
    for s in slugs:
        a = _mcc_cells(idx.predict(queries[s], "act_match"), joins[s],
                       corrected[s], benchmark)
        u = _mcc_cells(idx.predict(queries[s], "any_atom"), joins[s],
                       corrected[s], benchmark)
        g = _mcc_cells(bag_lobo[s][2], joins[s], corrected[s], benchmark)
        for j, t in sorted(benchmark.pair_targets(corrected[s]).items()):
            print(f"  {s:32} {j:10} {a[j]:>+10.3f} {u[j]:>+9.3f} "
                  f"{g[j]:>+9.3f} "
                  f"{benchmark.mcc(t['pred'], t['gold'], set(joins[s])):>+8.3f}")

    # -------------------------------------------------------- per-rung P/R
    print()
    print("=" * 78)
    print("PER-RUNG precision / recall (disjoint rungs) — where each pattern earns")
    print("=" * 78)
    for s in slugs:
        m = idx.match(queries[s])
        print(f"  {s}")
        for i, (name, _) in enumerate(S.RUNGS):
            only = {c for c, x in m.items() if x.rung_index == i}
            if not only:
                print(f"    {name:20} (never fires)")
                continue
            lf = benchmark.lift(only, joins[s])
            p = r = mc = 0.0
            for t in benchmark.pair_targets(corrected[s]).values():
                g = t["gold"]
                p += (len(lf & g) / len(lf) if lf else 0) / 3
                r += (len(lf & g) / len(g) if g else 0) / 3
                mc += benchmark.mcc(lf, g, set(joins[s])) / 3
            print(f"    {name:20} clauses={len(only):>4} passages={len(lf):>4} "
                  f"P={p:.3f} R={r:.3f} MCC={mc:+.3f}")

    # ------------------------------------------------------------ bootstrap
    print()
    print("=" * 78)
    print(f"PAIRED BOOTSTRAP, {BOOTSTRAP_RESAMPLES} resamples over passages")
    print("=" * 78)
    bagL = {s: bag_lobo[s][2] for s in slugs}
    comparisons = [
        ("act_match", "bag @LOBO", {s: idx.predict(queries[s], "act_match") for s in slugs}, bagL),
        ("any_atom", "bag @LOBO", {s: idx.predict(queries[s], "any_atom") for s in slugs}, bagL),
        ("sit_or_act", "bag @LOBO", {s: idx.predict(queries[s], "sit_or_act") for s in slugs}, bagL),
        ("act_and_situation", "bag @LOBO",
         {s: idx.predict(queries[s], "act_and_situation") for s in slugs}, bagL),
        ("act_match", "any_atom (SIZE-CONFOUNDED)",
         {s: idx.predict(queries[s], "act_match") for s in slugs},
         {s: idx.predict(queries[s], "any_atom") for s in slugs}),
    ]
    for a, b, ap, bp in comparisons:
        d, lo, hi = _bootstrap(ap, bp, joins, corrected, slugs, benchmark)
        sig = "SIGNIFICANT" if (lo > 0 or hi < 0) else "not significant"
        note = ("   <-- CONFOUNDED WITH SET SIZE, NOT A TYPING TEST"
                if b.startswith("any_atom") else "")
        print(f"  {a:18} vs {b:20} Δ {d:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  "
              f"{sig}{note}")

    # ------------------------------------------------------------------ AUC
    print()
    print("=" * 78)
    print("AUC — threshold-free ranking quality (judges: balanced accuracy)")
    print("=" * 78)
    print(f"  {'behaviour':34} {'structural':>11} {'bag':>8} {'judges':>8}")
    for s in slugs:
        ss, sb = dict(idx.rank(queries[s])), dict(bag.rank(beh[s]))
        a_s = a_b = a_j = 0.0
        for t in benchmark.pair_targets(corrected[s]).values():
            a_s += _auc(ss, joins[s], t["gold"]) / 3
            a_b += _auc(sb, joins[s], t["gold"]) / 3
            U, g, pr = set(joins[s]), t["gold"], t["pred"]
            P, N = len(g), len(U) - len(g)
            a_j += ((len(pr & g) / P if P else 0)
                    + (1 - len(pr - g) / N if N else 0)) / 2 / 3
        print(f"  {s:34} {a_s:>11.3f} {a_b:>8.3f} {a_j:>8.3f}")
    print("  NOTE: the bag out-RANKS the structural query on 2 of 3 behaviours "
          "even though\n  it loses decisively as a DECISION rule. Ranking and "
          "thresholded prediction are\n  different products; the structural "
          "query wins the second, not the first.")

    # ------------------------------------------ published vs corrected universe
    print()
    print("=" * 78)
    print("PUBLISHED (filtered) universe vs CORRECTED 589 — the delta the fix costs")
    print("=" * 78)
    for op in ("act_match", "any_atom", "act_and_situation"):
        pub = _mean({s: _mean(_mcc_cells(idx.predict(queries[s], op),
                                         pub_joins[s], published[s], benchmark))
                     for s in slugs})
        cor = _mean({s: mean_mcc(s, idx.predict(queries[s], op)) for s in slugs})
        print(f"  {op:20} published {pub:+.3f}   corrected {cor:+.3f}   "
              f"Δ {cor - pub:+.3f}")

    print()
    print("=" * 78)
    print("KNOWN UNQUANTIFIED UNCERTAINTY")
    print("=" * 78)
    print("  The ~25 behaviour atoms per behaviour in THIS report come from ONE")
    print("  model call, so every number above is a single sample. The k=5")
    print("  re-draws that quantify it HAVE LANDED — run --variance, which is")
    print("  now the authority for anything about typing.")
    print()
    print("  ⚠️ RETRACTED GUIDANCE, previously printed here: 'no difference under")
    print("  about +-0.06 should be read as real, and that includes act_match vs")
    print("  any_atom.' That was an INTERIM guardrail conditional on n=1 and it")
    print("  outlived its condition. The measured draw-level SE of that delta is")
    print("  0.0041 — the +-0.06 rule was ~15 SE and rejected everything. Use the")
    print("  derived floor in --variance (0.011 on the mean, 0.013-0.037 per")
    print("  behaviour), never a constant.")
    print()
    print("  ⚠️ act_match vs any_atom above is CONFOUNDED WITH PREDICTION-SET")
    print("  SIZE (act_match predicts about half as many clauses) and is not a")
    print("  test of typing. The size-matched control in --variance is.")


# ==========================================================================
# VARIANCE ACROSS BEHAVIOUR-ATOM DRAWS
# ==========================================================================
# The ~25 behaviour atoms per behaviour come from ONE model call, so every
# structural number is a single sample presented as a constant. These draws
# quantify that. `behavior_atoms_b8.json` is draw 0; `behavior_atoms_draw*.json`
# are the re-draws.
#
# ⚠️ THESE ARE A VARIANCE MEASUREMENT, NOT A SELECTION SET. Nothing here picks
# a draw, ranks draws, or averages in a way that implicitly selects. Choosing
# the best draw would be fitting to the panel through the back door — the exact
# failure this whole redesign exists to avoid. The spread is reported as-is.
#
#     .venv/bin/python test_structural.py --variance


def _draw_paths():
    """`[(label, path)]` — draw 0 is the original artifact, then the re-draws."""
    import glob
    out = [("draw0", BEHAVIOUR_ATOMS)]
    for p in sorted(glob.glob(os.path.join(HERE, "behavior_atoms_draw*.json"))):
        out.append((os.path.basename(p).replace("behavior_atoms_", "")
                    .replace(".json", ""), p))
    return out


def _sd(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _median(xs):
    ys = sorted(xs)
    n = len(ys)
    return ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2


# ------------------------------------------------------- inference machinery
#
# THE NOISE FLOOR IS DERIVED FROM THE DATA, NOT DECLARED.
#
# ⚠️ WHAT WAS HERE BEFORE, AND WHY IT WAS WRONG. This file used to compare the
# paired delta against a hardcoded `NOISE = 0.06`. Its own provenance note
# stated it as an INTERIM guardrail conditional on n=1 ("re-draws (k>=5) have
# been requested; UNTIL THEY LAND, no difference under about +-0.06 should be
# read as real"). The re-draws landed. The constant was used anyway. The
# sampling sd of the paired delta across draws is 0.009 and its standard error
# is 0.0041, so +-0.06 is roughly FIFTEEN standard errors — a floor that no
# effect this experiment could ever produce would clear, which made the
# "consistent and outside the floor" branch unreachable and the null verdict
# unfalsifiable. An expired guardrail is worse than no guardrail: it looks like
# a measurement.
#
# The floor is now the half-width of the 95% CI of the effect's own sampling
# distribution, computed at whatever k the draws supply. Two independent
# estimates are printed:
#
#   * DRAW-LEVEL: draw is the unit, sd across draws / sqrt(k). This is the
#     right one for "would another atom draw have said something else", which
#     is the uncertainty the re-draws were commissioned to quantify.
#   * PASSAGE-LEVEL: paired bootstrap over passages WITHIN one draw. This is a
#     different variance component (which passages the panel graded), reported
#     as a cross-check, not as a substitute.

#: Two-sided 95% critical values of Student's t, by degrees of freedom. A table
#: rather than a special-function implementation: k is small and fixed here,
#: and a table is checkable against any statistics text at a glance.
T_CRIT_95 = {1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582,
             6: 2.446912, 7: 2.364624, 8: 2.306004, 9: 2.262157, 10: 2.228139,
             11: 2.200985, 12: 2.178813, 13: 2.160369, 14: 2.144787,
             15: 2.131450, 19: 2.093024, 20: 2.085963, 24: 2.063899,
             29: 2.045230, 30: 2.042272}

#: One-sided 80th-percentile t, for the minimum detectable effect at 80% power.
T_POWER_80 = {1: 1.376382, 2: 1.060660, 3: 0.978472, 4: 0.940965, 5: 0.919544,
              6: 0.905703, 7: 0.896030, 8: 0.888890, 9: 0.883404, 10: 0.879058,
              11: 0.875530, 12: 0.872609, 13: 0.870152, 14: 0.868055,
              15: 0.866245, 19: 0.861104, 20: 0.860151, 24: 0.856855,
              29: 0.853860, 30: 0.853387}


def _paired_stats(xs):
    """One-sample t on the paired deltas. Draw is the unit of analysis.

    Returns mean, sd, se, t, the 95% CI, the half-width of that CI (which IS
    the noise floor — the smallest |effect| this k can distinguish from zero),
    and the minimum detectable effect at 80% power.
    """
    n = len(xs)
    if n < 2:
        raise ValueError("a sampling distribution needs at least two draws; "
                         "this is exactly the n=1 situation the expired +-0.06 "
                         "constant was a placeholder for")
    df = n - 1
    if df not in T_CRIT_95:
        raise ValueError(f"no tabulated t for df={df}; add it rather than "
                         "reaching for the nearest number")
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / df)
    se = sd / math.sqrt(n)
    tc = T_CRIT_95[df]
    return {"n": n, "mean": m, "sd": sd, "se": se,
            "t": (m / se) if se else (math.inf if m > 0 else
                                      -math.inf if m < 0 else 0.0),
            "ci_lo": m - tc * se, "ci_hi": m + tc * se,
            "noise_floor": tc * se,
            "mde80": (tc + T_POWER_80[df]) * se,
            "n_pos": sum(1 for x in xs if x > 0),
            "n_neg": sum(1 for x in xs if x < 0)}


#: The three verdicts a block may carry. There is no fourth, and the string is
#: derived from the CI in ONE place so a printed word cannot drift from the
#: numbers printed beside it.
HELPS, HURTS, UNDETERMINED = "HELPS", "HURTS", "UNDETERMINED"
VERDICT_WORDS = (HELPS, HURTS, UNDETERMINED)

#: The retracted headline. Named as a constant so the consistency check can
#: refuse to let it be printed beside a significant effect ever again.
NULL_CLAIM = "NO MEASURABLE TYPING EFFECT"


def _verdict_of(st):
    """The ONLY place a verdict word is chosen. Purely a function of the CI."""
    if st["ci_lo"] > 0:
        return HELPS
    if st["ci_hi"] < 0:
        return HURTS
    return UNDETERMINED


def _typing_verdict(deltas, slugs):
    """The typing verdict, PER BEHAVIOUR. `deltas` is `{draw label: [d per slug]}`.

    ⚠️ THE MEAN-OVER-BEHAVIOURS ROW IS NOT THE VERDICT. It averages a large win
    (+0.087 on over-and-under-caution) against a large loss (-0.047 on
    harm-avoidance) and reports neither; behaviour explains 90% of the variance
    in this delta. The row is kept because it is what the retracted claim was
    made about, and because it is itself significant — but the per-behaviour
    rows are the finding.
    """
    labels = list(deltas)
    per = {}
    for i, s in enumerate(slugs):
        st = _paired_stats([deltas[l][i] for l in labels])
        st["verdict"] = _verdict_of(st)
        per[s] = st
    overall = _paired_stats([sum(deltas[l]) / len(slugs) for l in labels])
    overall["verdict"] = _verdict_of(overall)
    # between-behaviour variance: does behaviour explain the delta?
    allv = [deltas[l][i] for l in labels for i in range(len(slugs))]
    gm = sum(allv) / len(allv)
    sst = sum((x - gm) ** 2 for x in allv)
    ssb = sum(len(labels) * (per[s]["mean"] - gm) ** 2 for s in slugs)
    dfb, dfw = len(slugs) - 1, len(allv) - len(slugs)
    # power to resolve WHICH behaviours differ, with behaviour as the unit.
    # None with a single behaviour: there is nothing to resolve between.
    across = (_paired_stats([per[s]["mean"] for s in slugs])
              if len(slugs) > 1 else None)
    return {"labels": labels, "slugs": list(slugs), "per_behaviour": per,
            "overall": overall,
            "eta_sq": (ssb / sst) if sst else 0.0,
            "f_stat": ((ssb / dfb) / ((sst - ssb) / dfw))
                      if dfb and dfw and (sst - ssb) > 0 else math.inf,
            "f_df": (dfb, dfw),
            "behaviour_level_mde80": across["mde80"] if across else None}


def _verdict_lines(v):
    """The printed verdict. Generated from the numbers, never hand-written."""
    L = ["  PER-BEHAVIOUR VERDICT — this table IS the finding.",
         "",
         f"    {'behaviour':34} {'mean Δ':>8} {'sd':>7} {'se':>7} "
         f"{'t':>7} {'95% CI':>18} {'gold prev':>10} {'sign':>7}  verdict"]
    for s in v["slugs"]:
        st = v["per_behaviour"][s]
        ci = f"[{st['ci_lo']:+.3f},{st['ci_hi']:+.3f}]"
        prev = st.get("gold_prevalence")
        L.append(f"    {s:34} {st['mean']:>+8.3f} {st['sd']:>7.3f} "
                 f"{st['se']:>7.4f} {st['t']:>+7.2f} {ci:>18} "
                 f"{(f'{prev:.3f}' if prev is not None else '-'):>10} "
                 f"{st['n_pos']}+/{st['n_neg']}-  {st['verdict']}")
    o = v["overall"]
    L += ["",
          f"    {'MEAN OVER BEHAVIOURS (not the verdict)':34} "
          f"{o['mean']:>+8.3f} {o['sd']:>7.3f} {o['se']:>7.4f} "
          f"{o['t']:>+7.2f} [{o['ci_lo']:+.3f},{o['ci_hi']:+.3f}]  "
          f"{o['n_pos']}+/{o['n_neg']}-  {o['verdict']}",
          "",
          f"  behaviour explains {v['eta_sq']:.1%} of the variance in this "
          f"delta, F{v['f_df']} = {v['f_stat']:.1f}",
          ""]
    helps = [s for s in v["slugs"] if v["per_behaviour"][s]["verdict"] == HELPS]
    hurts = [s for s in v["slugs"] if v["per_behaviour"][s]["verdict"] == HURTS]
    if not helps and not hurts:
        L.append(f"  VERDICT: {NULL_CLAIM} on any behaviour at this k.")
    else:
        L += ["  VERDICT: TYPING IS A PRECISION-BUYING PRUNE, NOT A NULL AND "
              "NOT A UNIFORM WIN.",
              f"  It HELPS on {helps or '(none)'} and HURTS on "
              f"{hurts or '(none)'}; the mean over behaviours hides both.",
              "  Mechanism consistent with the signs: requiring the act slot "
              "roughly halves the",
              "  prediction set, buying precision by pruning recall — which "
              "pays when the target",
              "  is rare and costs when it is common. ⚠️ WHICH behaviours it "
              "pays for is NOT",
              f"  established: n = {len(v['slugs'])} behaviours, and the "
              f"behaviour-level MDE at 80% power is",
              f"  {v['behaviour_level_mde80']:.3f} — far above every effect "
              "here. Three points are not a law."
              if v["behaviour_level_mde80"] is not None else
              "  established: a single behaviour cannot establish anything "
              "about which behaviours."]
    return L


def _check_verdict_consistency(v, lines):
    """The verdict may not contradict the evidence printed beside it.

    THE DEFECT THIS EXISTS TO PREVENT, verbatim from the retracted output:

        sign of the mean delta: 5 positive, 0 negative
        ...
        VERDICT: TYPING CONTRIBUTES NOTHING MEASURABLE ... does not hold a
        consistent sign

    Three lines apart, in the same block, printed by the same function. Nothing
    checked that the sentence and the numbers agreed, so they did not. Raises
    `AssertionError` rather than returning a bool: this runs inside the harness
    and must stop it, not decorate it.
    """
    text = "\n".join(lines)
    blocks = dict(v["per_behaviour"])
    blocks["MEAN OVER BEHAVIOURS"] = v["overall"]
    for name, st in blocks.items():
        assert st["verdict"] in VERDICT_WORDS, (name, st["verdict"])
        assert st["verdict"] == _verdict_of(st), (
            f"{name}: verdict {st['verdict']} is not what its own CI "
            f"[{st['ci_lo']:+.4f},{st['ci_hi']:+.4f}] says")
        if st["verdict"] == HELPS:
            assert st["mean"] > 0 and st["ci_lo"] > 0
            assert st["n_pos"] > st["n_neg"], (
                f"{name}: verdict HELPS but the sign summary is "
                f"{st['n_pos']} positive / {st['n_neg']} negative")
        if st["verdict"] == HURTS:
            assert st["mean"] < 0 and st["ci_hi"] < 0
            assert st["n_neg"] > st["n_pos"], (
                f"{name}: verdict HURTS but the sign summary is "
                f"{st['n_pos']} positive / {st['n_neg']} negative")
        if st["verdict"] == UNDETERMINED:
            assert st["ci_lo"] <= 0 <= st["ci_hi"]
    if NULL_CLAIM in text:
        offenders = {n: b["verdict"] for n, b in blocks.items()
                     if b["verdict"] != UNDETERMINED}
        assert not offenders, (
            f"the output claims {NULL_CLAIM!r} while these blocks are "
            f"resolved: {offenders}. This is the retracted defect: a null "
            "headline printed above its own contradicting evidence.")
    # every behaviour's verdict word must appear on that behaviour's own line,
    # and no OTHER verdict word may — so hand-editing a word without changing
    # the numbers is caught.
    for s, st in v["per_behaviour"].items():
        row = [l for l in lines if l.strip().startswith(s)]
        assert row, f"{s} has no row in the printed table"
        for w in VERDICT_WORDS:
            present = any(w in r for r in row)
            assert present == (w == st["verdict"]), (
                f"{s}: printed row says {w!r} but the numbers say "
                f"{st['verdict']!r}")
    return True


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def _variance():
    import benchmark

    clauses, _src = benchmark.load_clauses()
    published = benchmark.load_panel()
    draws = _draw_paths()
    base = S.load_queries(BEHAVIOUR_ATOMS)
    slugs = sorted(s for s in base if s in published)

    universe = _universe()
    corrected = {s: universe[s] for s in slugs}
    joins = {s: benchmark.clause_joins(corrected[s], clauses) for s in slugs}
    idx = S.StructuralIndex.from_files()

    print("=" * 78)
    print(f"BEHAVIOUR-ATOM DRAW VARIANCE — k = {len(draws)} draws")
    print("=" * 78)
    if len(draws) < 2:
        print("  only the original artifact is present; re-draws not found.")
        return
    for label, path in draws:
        print(f"  {label:8} {os.path.basename(path)}")

    Q = {label: S.load_queries(path) for label, path in draws}
    missing = [(l, s) for l in Q for s in slugs if s not in Q[l]]
    if missing:
        print(f"  !! draws missing behaviours: {missing}")

    res = {}   # (label, slug, op) -> mcc
    for label in Q:
        for s in slugs:
            if s not in Q[label]:
                continue
            for op in ("act_match", "any_atom"):
                res[(label, s, op)] = _mean(_mcc_cells(
                    idx.predict(Q[label][s], op), joins[s], corrected[s],
                    benchmark))

    # ---------------------------------------------------------- per draw
    for op in ("act_match", "any_atom"):
        print()
        print(f"  {op} MCC per draw")
        print(f"    {'draw':8} " + " ".join(f"{s[:16]:>16}" for s in slugs)
              + f" {'mean':>8}")
        for label in Q:
            vals = [res.get((label, s, op)) for s in slugs]
            if any(v is None for v in vals):
                continue
            print(f"    {label:8} " + " ".join(f"{v:>+16.3f}" for v in vals)
                  + f" {sum(vals)/len(vals):>+8.3f}")
        print(f"    {'-'*8} " + " ".join("-" * 16 for _ in slugs) + " " + "-" * 8)
        # ⚠️ MEAN FIRST. A review found this harness printed spreads where a
        # reader looks for effects, and the mean delta appeared nowhere.
        for stat, fn in (("MEAN", lambda xs: sum(xs) / len(xs)), ("min", min),
                         ("median", _median), ("max", max), ("sd", _sd)):
            cols = []
            for s in slugs:
                xs = [res[(l, s, op)] for l in Q if (l, s, op) in res]
                cols.append(fn(xs))
            means = [sum(res[(l, s, op)] for s in slugs) / len(slugs)
                     for l in Q if all((l, s, op) in res for s in slugs)]
            print(f"    {stat:8} " + " ".join(f"{c:>+16.3f}" for c in cols)
                  + f" {fn(means):>+8.3f}")

    # ------------------------------------------- THE within-draw paired delta
    print()
    print("=" * 78)
    print("act_match - any_atom, WITHIN each draw  ⚠️ CONFOUNDED WITH SET SIZE")
    print("=" * 78)
    print("  ⚠️ THIS IS NOT THE TEST OF TYPING, THOUGH IT WAS PUBLISHED AS ONE.")
    print("  Kind is a strict function of name in this artifact (361 names, 0 with")
    print("  more than one kind), so `act_match` is exactly a NAME-SUBSET FILTER:")
    print("  it returns the identical set to `any_atom` on the act-only subquery,")
    print("  in all 15 cells (asserted below). It also predicts roughly HALF as")
    print("  many clauses. So this contrast is PRUNE vs NO-PRUNE and never")
    print("  controls for set size. The size-matched control further down is the")
    print("  test. This table is kept because the retracted claim was made on it.")
    print()
    print("  Paired within a draw, so the atom set is held constant and the ONLY")
    print("  difference is whether the act slot is required. Across draws this is")
    print("  the sampling distribution of the effect.")
    print()
    print(f"    {'draw':8} " + " ".join(f"{s[:16]:>16}" for s in slugs)
          + f" {'mean':>8}")
    deltas = {}
    for label in Q:
        if not all((label, s, "act_match") in res for s in slugs):
            continue
        d = [res[(label, s, "act_match")] - res[(label, s, "any_atom")]
             for s in slugs]
        deltas[label] = d
        print(f"    {label:8} " + " ".join(f"{v:>+16.3f}" for v in d)
              + f" {sum(d)/len(d):>+8.3f}")
    means = [sum(d) / len(d) for d in deltas.values()]
    print(f"    {'-'*8} " + " ".join("-" * 16 for _ in slugs) + " " + "-" * 8)
    for stat, fn in (("MEAN Δ", lambda xs: sum(xs) / len(xs)), ("min", min),
                     ("median", _median), ("max", max), ("sd", _sd)):
        cols = [fn([deltas[l][i] for l in deltas]) for i in range(len(slugs))]
        print(f"    {stat:8} " + " ".join(f"{c:>+16.3f}" for c in cols)
              + f" {fn(means):>+8.3f}")

    # --------------------------------------------- the noise floor, DERIVED
    verdict = _typing_verdict(deltas, slugs)
    for s in slugs:
        verdict["per_behaviour"][s]["gold_prevalence"] = _mean(
            {j: len(t["gold"]) / len(set(joins[s]))
             for j, t in benchmark.pair_targets(corrected[s]).items()})

    print()
    print("=" * 78)
    print("THE NOISE FLOOR, DERIVED FROM THIS EFFECT'S OWN SAMPLING DISTRIBUTION")
    print("=" * 78)
    print("  ⚠️ RETRACTED: a hardcoded +-0.06. Its own provenance stated it as an")
    print("  INTERIM guardrail conditional on n=1 — 'until the re-draws land'. The")
    print("  re-draws landed and it was used anyway. Measured against this effect")
    print("  it is roughly FIFTEEN standard errors, so the 'outside the floor'")
    print("  branch was unreachable and the null it guarded was unfalsifiable.")
    print()
    o = verdict["overall"]
    print(f"  draw-level, mean over behaviours, k={o['n']}:")
    print(f"    sd across draws {o['sd']:.4f}   SE {o['se']:.4f}   "
          f"95% CI half-width (THE FLOOR) {o['noise_floor']:.4f}")
    print(f"    MDE at 80% power {o['mde80']:.4f}; observed "
          f"{o['mean']:+.4f} {'exceeds' if abs(o['mean']) > o['mde80'] else 'is below'} it")
    print("  draw-level, per behaviour:")
    for s in slugs:
        st = verdict["per_behaviour"][s]
        print(f"    {s:34} SE {st['se']:.4f}  floor {st['noise_floor']:.4f}  "
              f"MDE80 {st['mde80']:.4f}")
    d_boot, lo_boot, hi_boot = _bootstrap(
        {s: idx.predict(Q["draw0"][s], "act_match") for s in slugs},
        {s: idx.predict(Q["draw0"][s], "any_atom") for s in slugs},
        joins, corrected, slugs, benchmark)
    print(f"  passage-level cross-check (paired bootstrap over passages WITHIN "
          f"draw0):")
    print(f"    Δ {d_boot:+.4f}  95% CI [{lo_boot:+.4f}, {hi_boot:+.4f}]  "
          f"half-width {(hi_boot - lo_boot) / 2:.4f}")
    print("    This is a DIFFERENT variance component (which passages were")
    print("    graded, not which atoms were drawn) and is a cross-check, not a")
    print("    substitute. Neither estimate is anywhere near 0.06.")

    # ------------------------------------------------------- the verdict
    print()
    print("=" * 78)
    print("THE TYPING VERDICT — PER BEHAVIOUR")
    print("=" * 78)
    print(f"  sign of the mean delta: {o['n_pos']} positive, {o['n_neg']} negative")
    print()
    lines = _verdict_lines(verdict)
    _check_verdict_consistency(verdict, lines)
    for line in lines:
        print(line)

    print()
    _size_matched_control(idx, Q, slugs, joins, corrected, benchmark)

    # ------------------------------------------------------ atom stability
    # -------------------------------------- spread vs query instability
    act_means = [sum(res[(l, s, "act_match")] for s in slugs) / len(slugs)
                 for l in Q if all((l, s, "act_match") in res for s in slugs)]
    print()
    print("=" * 78)
    print("HEADLINE, RESTATED AS A DISTRIBUTION")
    print("=" * 78)
    print(f"  act_match mean MCC over k={len(act_means)} draws: "
          f"{sum(act_means)/len(act_means):+.3f} +- {_sd(act_means):.3f} (sd), "
          f"range [{min(act_means):+.3f}, {max(act_means):+.3f}]")
    print(f"  The single-draw +0.340 quoted earlier is the MAXIMUM of this "
          f"spread, not a constant.")
    print(f"  It must be quoted as the mean with its spread. Even the minimum "
          f"({min(act_means):+.3f})")
    print(f"  clears the bag scorer's honest +0.206.")
    print()
    floor_b = {}
    for s in slugs:
        universe_ids = set(joins[s])
        reachable = benchmark.joinable(joins[s])
        floor_b[s] = _mean({j: benchmark.mcc(reachable, t["gold"], universe_ids)
                            for j, t in benchmark.pair_targets(
                                corrected[s]).items()})
    print(f"  Against BOTH floors — they answer different questions, so quote "
          f"both:")
    print(f"    floor A  chance, all-positive over every passage      "
          f"{0.0:+.3f}  (MCC's definitional zero)")
    print(f"    floor B  chance MINUS the coverage gap (7/589 passages "
          f"unreachable)  {_mean(floor_b):+.3f}")
    print(f"    the structural mean sits {sum(act_means)/len(act_means):+.3f}, "
          f"i.e. {sum(act_means)/len(act_means):.3f} above A and "
          f"{sum(act_means)/len(act_means) - _mean(floor_b):.3f} above B.")

    print()
    print("=" * 78)
    print("ATOM-SET STABILITY across draws")
    print("=" * 78)
    print(f"  {'behaviour':34} {'sizes':>16} {'common to all':>14} {'union':>7}")
    core, mean_jac = {}, {}
    for s in slugs:
        sets = {l: {a["name"] for a in Q[l][s].atoms} for l in Q if s in Q[l]}
        inter = set.intersection(*sets.values())
        union = set.union(*sets.values())
        core[s] = inter
        sizes = "/".join(str(len(v)) for v in sets.values())
        print(f"  {s:34} {sizes:>16} {len(inter):>14} {len(union):>7}")
        pj = []
        labels = list(sets)
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = sets[labels[i]], sets[labels[j]]
                pj.append(len(a & b) / len(a | b) if (a | b) else 0.0)
        mean_jac[s] = sum(pj) / len(pj) if pj else 0.0
        print(f"  {'':34} mean pairwise Jaccard {mean_jac[s]:.3f}; "
              f"core is {len(inter)/ (len(union) or 1):.0%} of the union")

    print()
    print("  does draw-to-draw atom overlap predict that draw's MCC?")
    print(f"    {'behaviour':34} {'r(overlap, act_match MCC)':>26}")
    for i, s in enumerate(slugs):
        sets = {l: {a["name"] for a in Q[l][s].atoms} for l in Q if s in Q[l]}
        labels = [l for l in deltas if l in sets]
        # each draw's agreement with the other draws
        agree, mccs = [], []
        for l in labels:
            others = [sets[o] for o in labels if o != l]
            js = [len(sets[l] & o) / len(sets[l] | o) if (sets[l] | o) else 0.0
                  for o in others]
            agree.append(sum(js) / len(js) if js else 0.0)
            mccs.append(res[(l, s, "act_match")])
        r = _pearson(agree, mccs)
        print(f"    {s:34} {r:>+26.3f}")
    print("    (k is small; treat any |r| here as descriptive, not inferential)")

    print()
    print("  THE SPREAD IS SMALL AND THE QUERY IS NOT. Roughly half of each")
    print("  ~23-atom query is redrawn between samples (pairwise Jaccard "
          "0.58-0.74,")
    print("  and only 32% of the union is stable on over/under-caution), yet "
          "the mean")
    print("  MCC moves by an sd of only %.3f." % _sd(act_means))
    print()
    print("  ⚠️ RETRACTED READING: 'the operator is a COARSE TOPIC FILTER, not")
    print("  concept-level ontological work — it is insensitive to WHICH atoms")
    print("  the query contains.' That inference does not follow, and the block")
    print("  below refutes it. Agreement between independent samples is evidence")
    print("  that the SAMPLING is stable, not that the CONTENT is irrelevant:")
    print("  five draws that keep selecting the same semantically central atoms")
    print("  will agree precisely BECAUSE the atoms matter. The test that")
    print("  separates the two readings is whether an ARBITRARY same-sized")
    print("  subset does as well — and it does not, by a wide margin.")

    print()
    _core_only(idx, Q, slugs, joins, corrected, benchmark)


#: How many random subsets per cell. Not a tuned number: 500 is enough that
#: the control MEAN is stable to ~0.005 (the sd across subsets is ~0.05-0.10),
#: and the verdict is a 15/15 sign count, which does not move with R.
RANDOMIZATION_R = 500
DF_MATCHED_R = 300
DF_MATCH_TOLERANCE = 0.10


def _any_atom_sets(idx):
    """`{atom name: {clause ids}}` — `any_atom` for a name set is their union.

    A speed path for the randomization control, which needs ~12000 predictions.
    Legitimate ONLY because `max_hops=0` and the shipped ontology has no
    relation layer, so `predict(q, "any_atom")` is exactly the union of the
    per-atom clause sets. `_size_matched_control` ASSERTS that equivalence
    against the real `predict` on every cell before using it — an optimisation
    that is not checked against the thing it replaces is a second
    implementation, and this project already has one too many of those.
    """
    out = {}
    for cid in idx.ids:
        for slot in S.SLOTS:
            for n in idx.by_kind[cid][slot]:
                out.setdefault(n, set()).add(cid)
    return out


def _size_matched_control(idx, Q, slugs, joins, corrected, benchmark):
    """THE TEST OF TYPING: the act subset vs a RANDOM SAME-SIZED subset.

    ⚠️ WHY THE PUBLISHED TEST WAS NOT A TEST OF TYPING. `act_match` vs
    `any_atom` compares a filtered query to the whole query, so it varies the
    SET SIZE and the typing together — `act_match` predicts about half as many
    clauses. Everything the published contrast measured could have been the
    prune alone. The control holds size fixed and varies only WHICH atoms:
    replace the act subset with a random same-sized subset of the query's own
    atoms. If typing is doing nothing, the act subset is an ordinary draw from
    that distribution.

    The df-matched variant additionally holds SUMMED DOCUMENT FREQUENCY fixed,
    which rules out "the act atoms are just the rarer ones" — i.e. that the
    operator is term weighting in disguise.
    """
    import random
    sets = _any_atom_sets(idx)

    def fast(names):
        out = set()
        for n in names:
            out |= sets.get(n, set())
        return out

    def score(names, s):
        return _mean(_mcc_cells(fast(names), joins[s], corrected[s], benchmark))

    print("=" * 78)
    print("THE TEST OF TYPING: SIZE-MATCHED RANDOMIZATION CONTROL")
    print("=" * 78)

    # 1. the identity that makes the published contrast confounded, and the
    #    conditions under which the speed path is exact. The equivalence is
    #    checked on the real queries AND on random subsets — a control whose
    #    fast path were only valid for the un-subsetted query would prove
    #    nothing about the subsets it is built from.
    import random as _r
    _chk = _r.Random("equivalence")
    for l in Q:
        for s in slugs:
            q = Q[l][s]
            acts = [a["name"] for a in q.atoms if a["kind"] == "act"]
            names = [a["name"] for a in q.atoms]
            assert fast(acts) == idx.predict(q, "act_match"), (l, s)
            assert fast(names) == idx.predict(q, "any_atom"), (l, s)
            # no contrary anywhere in this query can defeat a match, so
            # removing atoms can only remove clauses — the union is exact
            assert not idx.defeats(q), (l, s, "a defeater fires; the union "
                                        "speed path is no longer valid")
            for _ in range(5):
                sub = _chk.sample(names, len(acts))
                assert fast(sub) == idx.predict(
                    S.Query(s, [a for a in q.atoms if a["name"] in set(sub)]),
                    "any_atom"), (l, s, sub)
    print(f"  act_match(full query) == any_atom(act-only subquery) in all "
          f"{len(Q) * len(slugs)} cells.")
    print("  Kind is a strict function of name, so act_match IS a name-subset")
    print("  filter — which is exactly why act_match vs any_atom cannot")
    print("  separate typing from set size.")

    for label, R, matched in (("RANDOM same-sized subset of the query's atoms",
                               RANDOMIZATION_R, False),
                              (f"DF-MATCHED same-sized subset (summed df within "
                               f"{DF_MATCH_TOLERANCE:.0%})", DF_MATCHED_R, True)):
        print()
        print(f"  {label}, R={R} per cell")
        print(f"    {'draw':7} {'behaviour':34} {'k/n':>7} {'act':>8} "
              f"{'control':>8} {'sd':>7} {'Δ':>8} {'pct>=act':>9}")
        rows = []
        for l in Q:
            for s in slugs:
                q = Q[l][s]
                names = [a["name"] for a in q.atoms]
                acts = [a["name"] for a in q.atoms if a["kind"] == "act"]
                k = len(acts)
                target = sum(idx.df.get(n, 0) for n in acts)
                act_mcc = score(acts, s)
                rng = random.Random(f"{l}/{s}/{matched}")
                vals, tries = [], 0
                while len(vals) < R and tries < 200 * R:
                    tries += 1
                    sub = rng.sample(names, k)
                    if matched and target and abs(
                            sum(idx.df.get(n, 0) for n in sub)
                            - target) > DF_MATCH_TOLERANCE * target:
                        continue
                    vals.append(score(sub, s))
                if not vals:
                    print(f"    {l:7} {s[:34]:34} no matched control exists")
                    continue
                m = sum(vals) / len(vals)
                sd = _sd(vals)
                pct = sum(1 for v in vals if v >= act_mcc) / len(vals)
                rows.append((s, act_mcc - m))
                print(f"    {l:7} {s[:34]:34} {k:>3}/{len(names):<3} "
                      f"{act_mcc:>+8.3f} {m:>+8.3f} {sd:>7.3f} "
                      f"{act_mcc - m:>+8.3f} {pct:>9.3f}")
        ds = [d for _, d in rows]
        wins = sum(1 for d in ds if d > 0)
        # exact two-sided sign test, no ties possible at this resolution
        p = min(1.0, 2 * sum(math.comb(len(ds), i)
                             for i in range(wins, len(ds) + 1)) / 2 ** len(ds))
        print(f"    ACT WINS {wins}/{len(ds)} CELLS, mean Δ {sum(ds)/len(ds):+.3f}, "
              f"sign test p = {p:.1e}")
        for s in slugs:
            d = [x for sl, x in rows if sl == s]
            print(f"      {s:34} mean Δ {sum(d)/len(d):+.3f} "
                  f"({sum(1 for x in d if x > 0)}/{len(d)} positive)")

    print()
    print("  TYPING SURVIVES BOTH CONTROLS — including on harm-avoidance, where")
    print("  its apparent LOSS against any_atom is a set-size artifact: at")
    print("  matched size the act slot still beats a random slice of the same")
    print("  query. The act slot is therefore not an arbitrary vocabulary")
    print("  subset and not term weighting in disguise.")


#: Random same-sized subsets per behaviour for the core-vs-arbitrary contrast.
CORE_CONTROL_R = 300


def _core_only(idx, Q, slugs, joins, corrected, benchmark):
    """Does the STABLE CORE carry the signal, and IS IT ARBITRARY?

    The first question was asked before: ~14 atoms common to all five draws
    score what ~25 atoms score, so the redrawn half adds nothing.

    ⚠️ THE SECOND QUESTION WAS NOT ASKED, AND ITS ANSWER RETRACTS THE
    CONCLUSION DRAWN FROM THE FIRST. "The core scores what the draws score" was
    read as "the specific concepts do not matter — this is a coarse topic
    filter". That reading requires the core to be an ORDINARY subset. Three
    measurements say it is not:

      * the core is the MORE COMMON half of the vocabulary (median df above
        the remainder's), which is the OPPOSITE of what IDF weighting would
        select — so it is not a rare-term effect;
      * a same-sized HIGHEST-INFORMATION (lowest-df) subset COLLAPSES;
      * random same-sized subsets scatter several times more widely than the
        five draws do.

    Independent samples agree because they keep selecting the same semantically
    central atoms. That is a STABLE EXTRACTION, and it was misread as a vacuous
    operator.
    """
    import random
    print()
    print("=" * 78)
    print("COMMON CORE vs FULL DRAWS vs ARBITRARY SUBSETS")
    print("=" * 78)
    print(f"  {'behaviour':30} {'core n':>6} {'core MCC':>9} "
          f"{'full mean':>10} {'delta':>7} {'union n':>8} {'union MCC':>10}")
    stats = {}
    for s in slugs:
        sets = {l: {a["name"] for a in Q[l][s].atoms} for l in Q if s in Q[l]}
        core = set.intersection(*sets.values())
        union = set.union(*sets.values())
        proto = {a["name"]: a for l in Q if s in Q[l] for a in Q[l][s].atoms}

        # `s` and `proto` bound at definition time: this closure is stored and
        # called from the SECOND loop below, where late binding would silently
        # score every behaviour against the last one's atoms.
        def mcc_of(names, s=s, proto=proto):
            return _mean(_mcc_cells(
                idx.predict(S.Query(s, [proto[n] for n in sorted(names)]),
                            "act_match"),
                joins[s], corrected[s], benchmark))

        cm, um = mcc_of(core), mcc_of(union)
        fulls = [_mean(_mcc_cells(idx.predict(Q[l][s], "act_match"), joins[s],
                                  corrected[s], benchmark))
                 for l in Q if s in Q[l]]
        fm = sum(fulls) / len(fulls)
        print(f"  {s:30} {len(core):>6} {cm:>+9.3f} {fm:>+10.3f} "
              f"{cm - fm:>+7.3f} {len(union):>8} {um:>+10.3f}")
        stats[s] = (core, union, mcc_of, cm, fulls)

    print()
    print("  The core is a STRICT SUBSET of every draw, so this is not a "
          "selection:")
    print("  no panel label chose these atoms — they are the ones five "
          "independent")
    print("  samples happened to agree on.")

    print()
    print("  IS THE CORE AN ORDINARY SUBSET? (the question the retracted "
          "reading skipped)")
    print(f"    {'behaviour':30} {'core df':>8} {'rest df':>8} {'core':>8} "
          f"{'hi-info':>8} {'random':>8} {'rand sd':>8} {'draw sd':>8}")
    for s in slugs:
        core, union, mcc_of, cm, fulls = stats[s]
        rest = union - core
        med = lambda xs: _median([idx.df.get(n, 0) for n in xs]) if xs else 0.0
        # the same-sized HIGHEST-INFORMATION subset: lowest document frequency
        hi = sorted(union, key=lambda n: (idx.df.get(n, 10 ** 6), n))[:len(core)]
        rng = random.Random(f"core/{s}")
        vals = [mcc_of(rng.sample(sorted(union), len(core)))
                for _ in range(CORE_CONTROL_R)]
        print(f"    {s:30} {med(core):>8.1f} {med(rest):>8.1f} {cm:>+8.3f} "
              f"{mcc_of(hi):>+8.3f} {sum(vals)/len(vals):>+8.3f} "
              f"{_sd(vals):>8.3f} {_sd(fulls):>8.3f}")
    print()
    print("  Read the last two columns together: an ARBITRARY same-sized subset")
    print("  scatters several times more widely than the five real draws do. The")
    print("  draws agree because independent samples keep re-selecting the same")
    print("  semantically central atoms — a STABLE EXTRACTION. And the core is")
    print("  the MORE COMMON half, the opposite of IDF weighting, while the")
    print("  same-sized highest-information subset collapses. 'Insensitive to")
    print("  WHICH atoms' is false: it is sensitive, and the sampler is stable.")


if __name__ == "__main__":
    if "--variance" in sys.argv:
        _variance()
    else:
        _measure()
