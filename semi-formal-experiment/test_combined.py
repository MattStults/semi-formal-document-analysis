"""Tests for combined.py — the two structural components as ONE query.

`combined.py` must be provably label-free (contract §5 invariant 9). It is NOT
in `test_no_reference_leak.QUERY_MODULES` — that file is owned elsewhere and
`combined` has to be added to it — so this file runs the SAME two guards here,
importing the guard machinery from that file so the two can never drift: if
`FORBIDDEN` grows a token, `combined.py` is checked against it on the next run.

The load-bearing tests are the ones asserting that the composition genuinely
uses BOTH components. Each has a mutant beside it: an index whose section
partition has been FLATTENED, and a query whose typed core has been EMPTIED.
A composition that had quietly degenerated to one component would still pass
every other test in this file, which is exactly why those two exist.

The panel-facing measurement lives in scratchpad and behind `--report`;
running these tests never touches the panel.
"""
from __future__ import annotations

import importlib
import os
import re

import pytest

import combined as CB
import ontology as O
import section as SEC
import structural as S
import test_no_reference_leak as GUARD

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def vocab():
    return {
        "user_request_ambiguous": {"kind": "situation", "gloss": "unclear request",
                                   "n_clauses": 3, "clauses": ["c1"]},
        "clarify_user_intent": {"kind": "act", "gloss": "asking what was meant",
                                "n_clauses": 6, "clauses": ["c1"]},
        "assume_intent": {"kind": "act", "gloss": "guessing",
                          "n_clauses": 1, "clauses": ["a3"]},
        "end_user": {"kind": "entity", "gloss": "the person talking",
                     "n_clauses": 1, "clauses": ["c1"]},
        "helpfulness": {"kind": "value", "gloss": "being useful",
                        "n_clauses": 1, "clauses": ["c4"]},
    }


@pytest.fixture
def clauses():
    """Five sections, each pinning one thing the composition has to get right.

    `Ambiguity`  3 clauses, 2 fire and one of those reaches the TOP RUNG
                 (`c1` fills situation AND act). Elected by the primary. `a3`
                 carries NO atoms at all, so it is the clause per-clause
                 matching provably cannot reach and the closure must. Its id
                 sorts BEFORE the others on purpose: within a section the
                 section channel is constant and falls back on clause id, so
                 `a3` first / `c1` first is exactly the difference the typed
                 tiebreak makes, and a test asserting `c1 < c2 < c3` would have
                 agreed with a rank that ignored the typed evidence entirely.
    `Tone`       3 clauses, 2 fire — a majority — but on the act slot only, so
                 no firing clause reaches the top rung. Elected by V1 and
                 REFUSED by the primary, and the third clause carries no atoms,
                 so the two answers actually differ. It is the fixture that
                 makes the rung gate visible.
    `Style`      3 clauses, exactly 1 fires. Only the MAJORITY rule keeps it
                 out.
    `Glossary`   both clauses fire (fraction 1.0) but the section is
                 definitional/meta. Only the CONDUCT GATE keeps it out — and
                 its clauses must still be predicted, by the typed core, since
                 the closure may never veto.
    `Values`     1 clause, nothing fires.
    """
    def c(cid, quote, path, kind, line):
        return {"id": cid, "quote": quote, "section_path": [path],
                "kind": kind, "line": line, "locator": f"spec > {path} > {line}"}
    return [
        c("c1", "Ask the user what they meant when the request is unclear.",
          "Ambiguity", "conditional", 1),
        c("c2", "A follow-up question is appropriate.", "Ambiguity", "example", 2),
        c("a3", "Worked example of the above.", "Ambiguity", "example", 3),
        c("t1", "Ask what was meant, politely.", "Tone", "conditional", 4),
        c("t2", "Ask what was meant, briefly.", "Tone", "example", 5),
        c("t3", "Notes on tone.", "Tone", "meta", 12),
        c("s1", "Ask the user what they meant before answering.",
          "Style", "conditional", 6),
        c("s2", "Keep answers short.", "Style", "example", 7),
        c("s3", "Style notes follow.", "Style", "meta", 8),
        c("g1", "Clarify means asking what was meant.",
          "Glossary", "definitional", 9),
        c("g2", "Follow-up means asking what was meant.", "Glossary", "meta", 10),
        c("c4", "Be useful.", "Values", "conditional", 11),
    ]


@pytest.fixture
def annotations(vocab):
    def at(name, cid, quote):
        return {"name": name, "kind": vocab[name]["kind"],
                "gloss": vocab[name]["gloss"], "span_id": f"sp_{cid}_{name}",
                "quote": quote, "clause_id": cid,
                "locator": f"spec > {cid}"}
    return {
        "c1": [at("user_request_ambiguous", "c1", "the request is unclear"),
               at("clarify_user_intent", "c1", "Ask the user what they meant"),
               at("end_user", "c1", "the user")],
        "c2": [at("clarify_user_intent", "c2", "A follow-up question")],
        "a3": [],
        "t1": [at("clarify_user_intent", "t1", "Ask what was meant")],
        "t2": [at("clarify_user_intent", "t2", "Ask what was meant")],
        "t3": [],
        "s1": [at("clarify_user_intent", "s1", "Ask the user what they meant")],
        "s2": [],
        "s3": [],
        "g1": [at("clarify_user_intent", "g1", "asking what was meant")],
        "g2": [at("clarify_user_intent", "g2", "asking what was meant")],
        "c4": [at("helpfulness", "c4", "Be useful")],
    }


@pytest.fixture
def onto(vocab):
    return O.Ontology(vocab, [])


@pytest.fixture
def query():
    return S.Query("ambiguity", [
        {"name": "user_request_ambiguous", "kind": "situation", "weight": 3},
        {"name": "clarify_user_intent", "kind": "act", "weight": 3},
        {"name": "end_user", "kind": "entity", "weight": 1},
    ])


@pytest.fixture
def dead_query():
    """A query whose atoms are in no clause. The degenerate case."""
    return S.Query("nothing", [
        {"name": "atom_that_appears_nowhere", "kind": "act", "weight": 3},
        {"name": "another_absent_atom", "kind": "situation", "weight": 3},
    ])


@pytest.fixture
def index(clauses, annotations, onto):
    return S.StructuralIndex(clauses, annotations, onto)


@pytest.fixture
def cx(index):
    return CB.CombinedIndex(index)


# ------------------------------------------------ guard 1: no label access

def test_combined_module_never_names_the_reference():
    """STATIC guard, sharing `FORBIDDEN` with `test_no_reference_leak` so the
    two cannot drift. `combined.py` is not in that file's QUERY_MODULES list,
    which is exactly why this test exists rather than being assumed."""
    src = GUARD._source("combined")
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in GUARD.FORBIDDEN if tok in src]
    assert not hits, (
        f"combined.py references the panel at query time: {hits}. The panel is "
        "a measuring instrument, not an input (contract §5 invariant 9).")


def test_no_model_is_called_at_query_time():
    src = GUARD._source("combined")
    for tok in ("providers", "urllib", "requests", "socket", "http"):
        assert tok not in src, f"combined.py names {tok!r} — querying is offline"


def test_combined_queries_open_only_declared_artifacts():
    """DYNAMIC guard. Import UNDER the spy — so an import-time
    `_GOLD = json.load(...)` is visible — and drive EVERY query entry point.

    A module exposing no drivable query surface FAILS rather than skips: a skip
    is not a guard, and that is how the sibling file once let a leak through.
    """
    if not (os.path.exists(ANNOTATIONS) and os.path.exists(BEHAVIOUR_ATOMS)):
        pytest.skip("real artifacts not present")
    opened, restore = GUARD._spy_all_open_paths()
    driven = []
    try:
        mod = importlib.reload(importlib.import_module("combined"))
        idx = mod.CombinedIndex.from_files()
        q = list(mod.load_queries(BEHAVIOUR_ATOMS).values())[0]
        cid = idx.index.ids[0]
        for meth in ("predict", "rank", "sweep", "match", "typed_core",
                     "closure", "elected", "elections", "section_order",
                     "top_rung", "diagnostics"):
            r = getattr(idx, meth)(q)
            list(r) if hasattr(r, "__iter__") else r
            driven.append(meth)
        idx.explain(q, cid)
        driven.append("explain")
        for name, _ in mod.VARIANTS:
            idx.variant(q, name)
            driven.append(f"variant:{name}")
    finally:
        restore()
    assert driven, "combined.py exposes no drivable query surface — UNGUARDED"
    assert "explain" in driven and "predict" in driven
    unexpected = [p for p in opened if p.endswith(".json")
                  and os.path.basename(p) not in GUARD.ALLOWED_ARTIFACTS]
    assert not unexpected, (
        f"combined.py opened UNDECLARED artifacts {sorted(set(unexpected))} "
        f"while driving {driven}")


# --------------------------------------------------------------- determinism

def test_predict_and_rank_are_deterministic(cx, query):
    assert cx.predict(query) == cx.predict(query)
    assert cx.rank(query) == cx.rank(query)
    assert cx.sweep(query) == cx.sweep(query)


def test_results_do_not_depend_on_clause_order(clauses, annotations, onto,
                                               query):
    """Two indices over the same clauses in opposite order must agree. Dict
    iteration order is stable in this interpreter, so an order dependence would
    be invisible in a single run and would surface only when the corpus is
    regenerated."""
    a = CB.CombinedIndex(S.StructuralIndex(clauses, annotations, onto))
    b = CB.CombinedIndex(S.StructuralIndex(list(reversed(clauses)),
                                           annotations, onto))
    assert a.predict(query) == b.predict(query)
    assert a.elected(query) == b.elected(query)
    assert [c for c, _ in a.rank(query)] == [c for c, _ in b.rank(query)]


# --------------------------------------------------------- the degenerate case

def test_a_degenerate_query_predicts_nothing(cx, dead_query):
    """A query whose atoms are in no clause must score ~0, not score WELL.

    Predicting the whole corpus is MCC 0 by construction but F1 0.64 at this
    base rate, so "predicts everything" is the failure mode that looks like
    success on the wrong metric. It must predict NOTHING.
    """
    assert cx.predict(dead_query) == set()
    assert cx.typed_core(dead_query) == set()
    assert cx.closure(dead_query) == set()
    assert cx.elected(dead_query) == set()


def test_a_degenerate_query_says_so(cx, dead_query):
    d = cx.diagnostics(dead_query)
    assert d["degenerate_to_section"] is True
    assert d["distinct_section_scores"] == 1, (
        "every section scores the same, so the ranking channel carries no "
        "information — the module must SAY that rather than emit an order")
    assert d["n_predicted"] == 0


def test_a_query_with_no_atoms_at_all_is_empty(cx):
    assert cx.predict(S.Query("empty", [])) == set()


# -------------------------------- the composition uses BOTH components

def test_the_closure_adds_a_clause_the_typed_core_cannot_reach(cx, query):
    """`c3` carries NO annotations. Per-clause matching can never reach it;
    the section closure is the only thing that can. This is the whole point of
    the union, so if this ever stops holding the module has degenerated to
    `structural`."""
    core = cx.typed_core(query)
    pred = cx.predict(query)
    assert "a3" not in core
    assert "a3" in pred
    assert pred - core, "the closure added nothing: this is `structural`, not a composition"


def test_the_typed_core_is_never_vetoed(cx, query):
    """`Glossary` is not conduct-bearing, so it is never elected — but its
    clauses fire on their own atoms and MUST still be predicted. Letting the
    quotient veto them is exactly `section.predict`'s measured -0.143 loss."""
    core = cx.typed_core(query)
    pred = cx.predict(query)
    assert {"g1", "g2"} <= core
    assert ("Glossary",) not in cx.elected(query)
    assert core <= pred, "the closure vetoed a clause carrying its own evidence"


def test_predict_is_neither_component_alone(cx, query):
    core, closure = cx.typed_core(query), cx.closure(query)
    pred = cx.predict(query)
    assert pred != core, "the section component contributes nothing"
    assert pred != closure, "the typed component contributes nothing"
    assert pred == core | closure


def test_MUTANT_flattening_the_section_partition_removes_the_contribution(
        clauses, annotations, onto, query):
    """MUTATION CHECK. Put every clause in ONE section. The partition then
    carries no information at all, and the election degenerates: the one block
    is judged as a whole, so it is elected or refused wholesale and the closure
    is everything or nothing. If the real answer did not depend on the
    partition, the mutant would agree with it — and it must not.

    (Measured on this fixture the flat block IS elected, 7 of 11 firing, so the
    mutant predicts the entire corpus. That is the degenerate behaviour, and
    the point is that it is a DIFFERENT answer, not that it is an empty one.)
    """
    flat = [dict(c, section_path=["ALL"]) for c in clauses]
    mutant = CB.CombinedIndex(S.StructuralIndex(flat, annotations, onto))
    real = CB.CombinedIndex(S.StructuralIndex(clauses, annotations, onto))
    assert len(mutant.quotient.sections) == 1
    assert mutant.closure(query) != real.closure(query), (
        "flattening the section partition left the closure unchanged — the "
        "election is not reading the partition")
    assert mutant.predict(query) != real.predict(query), (
        "flattening the section partition changed nothing: the section "
        "component is dead and the module is `structural` under another name")
    assert mutant.diagnostics(query)["distinct_section_scores"] == 1


def test_MUTANT_emptying_the_typed_core_removes_the_answer(cx, query,
                                                           monkeypatch):
    """MUTATION CHECK, the other side. With the typed core forced empty the
    election has no votes, so the answer must collapse to nothing. A module
    that still answered would be running on the section alone."""
    monkeypatch.setattr(CB.CombinedIndex, "typed_core",
                        lambda self, q, operator=CB.TYPED_OPERATOR: set())
    assert cx.predict(query) == set()
    assert cx.elected(query) == set()


def test_the_rung_gate_is_load_bearing(cx, query):
    """`Tone` fires on BOTH its clauses but on the act slot only, so no firing
    clause reaches `act_and_situation`. V1 elects it; the primary refuses it.
    The gate's whole content is that difference, and the difference is measured
    (it LOSES -0.018 — see `MEASURED`), which is only meaningful if it is real."""
    gated = cx.elected(query, rung_gate=True)
    ungated = cx.elected(query, rung_gate=False)
    assert ("Tone",) in ungated
    assert ("Tone",) not in gated
    assert gated < ungated
    assert cx.variant(query, "P") < cx.variant(query, "V1")


def test_the_conduct_gate_and_the_majority_rule_are_both_live(cx, query):
    """Asserted WITHOUT the rung gate. `Glossary` has no top-rung clause
    either, so under the primary its refusal is over-determined and a dead
    conduct gate would be invisible — which is exactly what a mutation run
    showed before this test was written this way."""
    el = cx.elections(query, rung_gate=False)
    assert el[("Glossary",)].majority and not el[("Glossary",)].conduct_bearing
    assert not el[("Glossary",)].elected, "the conduct gate is not being applied"
    assert el[("Style",)].conduct_bearing and not el[("Style",)].majority
    assert not el[("Style",)].elected, "the majority rule is not being applied"
    assert el[("Ambiguity",)].elected
    assert cx.elections(query)[("Ambiguity",)].elected


# ------------------------------------------------------------- the ranking

def test_rank_preserves_the_section_order_and_breaks_ties_by_typed_evidence(
        cx, query, index):
    """ACROSS sections the order must be `section.rank`'s order — the channel
    measured to beat the shipped smoothing term must not be disturbed. WITHIN a
    section, where that channel is constant by construction, the typed ladder
    must decide."""
    quotient = SEC.SectionQuotient(index)
    sect = {p: s for p, s in quotient.election_score(query).items()}
    order = [p for p, _ in cx.section_order(query)]
    assert order == sorted(sect, key=lambda p: (-sect[p], p))

    ranked = [c for c, _ in cx.rank(query)]
    seen = [cx.quotient.section_of(c) for c in ranked]
    # every section's clauses are contiguous: the section is the outer key
    assert len(seen) == len(ranked)
    first = {}
    for i, p in enumerate(seen):
        first.setdefault(p, i)
    assert seen == sorted(seen, key=lambda p: first[p])

    # Inside `Ambiguity` the section channel is CONSTANT, so only the typed
    # ladder can order these. `a3` carries no atoms and sorts FIRST by id, so
    # this assertion fails the moment the tiebreak stops consulting the typed
    # evidence — which is the whole content of the secondary claim.
    assert ranked.index("c1") < ranked.index("c2") < ranked.index("a3")


def test_rank_scores_are_bounded_and_total(cx, query):
    r = cx.rank(query)
    assert len(r) == len(cx.index.ids)
    assert all(0.0 <= v <= 1.0 for _, v in r)
    assert r == sorted(r, key=lambda kv: (-kv[1], kv[0]))


def test_rank_is_not_the_structural_rank(cx, query, index):
    """If the two agreed, the section component would not be in the ranking."""
    assert [c for c, _ in cx.rank(query)] != [c for c, _ in index.rank(query)]


# --------------------------------------------------------------- the sweep

def test_sweep_is_nested_and_starts_at_the_typed_core(cx, query):
    sw = cx.sweep(query)
    assert sw[0] == (0, cx.typed_core(query))
    for (_, a), (_, b) in zip(sw, sw[1:]):
        assert a <= b, "the sweep is not nested in k"
    assert sw[-1][1] == set(cx.index.ids)


# -------------------------------------------------------------- the variants

def test_every_named_variant_is_reachable(cx, query):
    for name, _ in CB.VARIANTS:
        assert isinstance(cx.variant(query, name), set)


def test_an_unknown_variant_raises(cx, query):
    with pytest.raises(ValueError):
        cx.variant(query, "V99")


def test_the_baseline_variants_are_the_components_verbatim(cx, query, index):
    """S, S0 and Q must be the components themselves, not re-implementations —
    a baseline that drifts from the thing it is a baseline for is worse than no
    baseline."""
    assert cx.variant(query, "S") == index.predict(query, S.PRIMARY_OPERATOR)
    assert cx.variant(query, "S0") == index.predict(query, "any_atom")
    assert cx.variant(query, "Q") == SEC.SectionQuotient(index).predict(query)


# -------------------------------------------------------------- explain()

def test_explain_returns_the_full_typed_path_and_names_the_component(cx, query):
    e = cx.explain(query, "c1")
    assert e["contributed_by"] == "both"
    assert e["predicted"] is True
    assert e["typed"]["rung"] == "act_and_situation"
    ev = e["typed"]["evidence"]
    assert ev, "no typed evidence in the explanation"
    assert all(x["span"] and x["locator"] and x["clause_atom"] for x in ev), (
        "a hit must bottom out in a quotation at a locator, not in a number")
    assert e["section"]["elected"] is True
    assert e["section"]["n_top_rung_firing"] >= 1
    assert e["why"]["composition"]


def test_explain_names_the_closure_when_the_clause_has_no_evidence_of_its_own(
        cx, query):
    e = cx.explain(query, "a3")
    assert e["contributed_by"] == "section_closure"
    assert e["typed"]["evidence"] == []
    assert "section was elected" in e["why"]["section_closure"]


def test_explain_says_why_a_clause_was_not_predicted(cx, query):
    e = cx.explain(query, "c4")
    assert e["contributed_by"] == "neither"
    assert e["predicted"] is False
    assert e["why"]["section_closure"]
    e2 = cx.explain(query, "g1")
    assert e2["contributed_by"] == "typed_core"
    assert "conduct-bearing" in e2["why"]["section_closure"]


def test_explain_delegates_verbatim_to_both_components(cx, query, index):
    """The composition must not be able to narrate a story its components do
    not tell."""
    e = cx.explain(query, "c1")
    assert e["typed"] == index.explain(query, "c1")
    assert e["section_component"] == SEC.SectionQuotient(index).explain(query, "c1")


# ------------------------------------------------------------- the constants

def test_every_constant_is_declared_and_justified():
    for name, spec in CB.CONSTANTS.items():
        assert spec.get("why"), f"{name} has no justification"
        assert len(spec["why"]) > 80, f"{name}'s justification is a stub"
        assert "fitted_on_panel" in spec, f"{name} does not disclose provenance"


def test_a_panel_fitted_constant_discloses_its_unselected_baseline():
    """A fitted constant that does not name what it was selected OVER cannot be
    audited. `structural.PRIMARY_OPERATOR` escaped exactly this way."""
    for name, spec in CB.CONSTANTS.items():
        if not spec["fitted_on_panel"]:
            continue
        assert spec.get("selected_over"), f"{name}: no candidate set"
        assert spec.get("selection_criterion"), f"{name}: no criterion"
        assert spec.get("unselected_baseline"), f"{name}: no baseline"


def test_the_constants_dict_is_complete():
    """Every module-level constant is either derived from `CONSTANTS` or named
    in `NON_PARAMETERS`, so a fitted number cannot hide by not being declared."""
    import types
    derived = {"TYPED_OPERATOR", "ELECTION_MAJORITY", "CONDUCT_KINDS",
               "ELECTION_RUNG", "COMPOSITION", "CONSTANTS", "NON_PARAMETERS"}
    undeclared = [n for n in dir(CB)
                  if n.isupper() and n not in derived
                  and n not in CB.NON_PARAMETERS
                  and not isinstance(getattr(CB, n), types.ModuleType)]
    assert not undeclared, (
        f"undeclared module-level constants: {undeclared}. Add them to "
        "CONSTANTS with a justification or to NON_PARAMETERS.")


def test_inherited_constants_still_agree_with_their_source():
    """A silent edit upstream must not leave a stale disclosure here."""
    assert CB.CONSTANTS["typed_operator"]["value"] == S.PRIMARY_OPERATOR
    assert CB.CONSTANTS["election_majority"]["value"] == SEC.ELECTION_MAJORITY
    assert CB.CONSTANTS["conduct_kinds"]["value"] == SEC.CONDUCT_KINDS
    assert CB.CONSTANTS["election_rung"]["value"] == S.RUNG_NAMES[0]
    assert (CB.CONSTANTS["typed_operator"]["unselected_baseline"]
            == S.CONSTANTS["primary_operator"]["unselected_baseline"])


def test_no_new_numeric_constant_was_invented():
    """The module's claim is that it introduces no number of its own. Every
    declared value is inherited or a name from an existing ladder."""
    for name, spec in CB.CONSTANTS.items():
        v = spec["value"]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            assert spec.get("inherited_from"), (
                f"{name} is a bare number that was not inherited — declare "
                "where it came from or do not introduce it")


# ---------------------------------------------------------- the measured result

def test_the_expired_noise_floor_is_not_reintroduced():
    """0.045 was derived on the 3-behaviour, 9-cell panel and does not transfer.
    It may be NAMED in prose as refused; it may not be a value."""
    assert CB.MEASURED["noise_floor"]["value"] != 0.045
    src = GUARD._source("combined")
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"#.*", "", src)
    code = "\n".join(l for l in src.splitlines() if '"' not in l and "'" not in l)
    assert "0.045" not in code, (
        "the expired 0.045 noise floor is refused BY NAME; this panel's floor "
        "was re-derived")


def test_the_verdict_matches_the_recorded_intervals():
    """The prose may not upgrade a number it does not have. Asserted against
    `MEASURED`, so an edit that improves the wording without re-deriving the
    measurement fails here."""
    m = CB.MEASURED
    floor = m["noise_floor"]["value"]
    win = m["contrasts"]["V1@any-S0"]
    assert win["delta"] > floor and win["ci"][0] > 0 and win["all_draws_exclude_zero"]
    assert "COMBINING HELPS" in m["verdict"]

    prim = m["contrasts"]["P-S"]
    assert prim["delta"] < floor
    assert "immaterial" in m["verdict"]

    gate = m["contrasts"]["P@any-V1@any"]
    assert gate["delta"] < 0 and gate["ci"][1] < 0
    assert "rung gate" in m["verdict"] and "LOSS" in m["verdict"]

    rk = m["ranking"]
    assert abs(rk["auc_mean"]["combined"] - rk["auc_mean"]["section"]) < 0.005
    assert rk["verdict"] == "no effect" and "flat null" in m["verdict"]

    vs_bag = m["contrasts"]["V1@any-B"]
    assert vs_bag["delta"] > floor
    assert "NOT a clean win" in m["verdict"], (
        "+0.032 does not clear the re-derived 0.035 floor; the verdict may not "
        "call it a win")


def test_every_variant_in_the_family_is_reported():
    """A losing variant may not be dropped from the table."""
    for name, _ in CB.VARIANTS:
        assert name in CB.MEASURED["variants"], f"{name} is not reported"


def test_result_lines_print_both_floors_and_the_losers():
    txt = "\n".join(CB.result_lines())
    assert "FLOOR A" in txt and "FLOOR B" in txt
    assert "noise floor" in txt
    for name in ("V2", "V4", "Q"):
        assert f"\n{name} " in txt or f"\n{name:<8}"[:len(name) + 1] in txt
    assert "VERDICT" in txt
    for slug in CB.MEASURED["floors"]["B_per_behaviour"]:
        assert slug in txt, "the per-behaviour rows are not printed"


def test_the_size_matched_control_is_recorded_and_passes():
    """The +0.042 must not be the extra prediction mass. A random extension of
    identical size has to do WORSE than the unextended core, and the number has
    to be in the module rather than in a scratchpad."""
    sc = CB.MEASURED["size_control"]
    assert sc["random_same_sized_extension"] < sc["typed_core_alone"]
    assert sc["elected_sections"] > sc["typed_core_alone"]


if __name__ == "__main__":
    print("\n".join(CB.result_lines()))


def test_election_globals_are_the_audited_values_not_literals():
    """The CONSTANTS audit read the DICT; the election logic reads the module
    GLOBALS. A reviewer replaced the global's read with a hard-coded literal
    (`ELECTION_MAJORITY = 0.4`) and flipped `>` to `>=`: the mean moved +0.0175
    with 1073 tests green and the disclosure still reading "never tuned".

    The audit could not see it because it never compared the two directions.
    """
    import combined as C
    assert C.ELECTION_MAJORITY == C.CONSTANTS["election_majority"]["value"], (
        "ELECTION_MAJORITY has been decoupled from its audited value — a tuned "
        "knob can now ship with a clean audit trail")
    assert C.ELECTION_RUNG == C.CONSTANTS["election_rung"]["value"]
    # the definitional majority: strictly more than half, never tuned
    assert C.ELECTION_MAJORITY == 0.5


def test_the_majority_rule_is_strict():
    """`>` -> `>=` alone moves the mean +0.0175 and no test saw it. A section
    where exactly half the clauses fire is NOT a majority."""
    import inspect, combined as C
    src = inspect.getsource(C.CombinedIndex.elections) + \
        inspect.getsource(C.CombinedIndex.elected)
    assert ">= ELECTION_MAJORITY" not in src and ">=ELECTION_MAJORITY" not in src, (
        "the majority test is non-strict; exactly-half now counts as a majority")
