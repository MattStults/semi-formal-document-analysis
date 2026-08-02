"""Tests for section.py — the section quotient.

`section.py` must be provably label-free (contract §5 invariant 9). It is NOT
in `test_no_reference_leak.QUERY_MODULES` (that list is frozen and owned
elsewhere), so this file runs the SAME two guards against it, importing the
guard machinery from that file so the two can never drift apart: if `FORBIDDEN`
grows a token, `section.py` is checked against it here on the next run.

The panel-facing measurement lives behind `__main__`, exactly as in
`test_structural.py`:

    .venv/bin/python test_section.py            # the section-channel report

Running the tests never touches the panel; running the module does.
"""
from __future__ import annotations

import importlib
import json
import os
import re

import pytest

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
                                "n_clauses": 3, "clauses": ["c1"]},
        "ask_followup_question": {"kind": "act", "gloss": "asking a follow-up",
                                  "n_clauses": 3, "clauses": ["c2"]},
        "assume_intent": {"kind": "act", "gloss": "guessing",
                          "n_clauses": 2, "clauses": ["c3"]},
        "end_user": {"kind": "entity", "gloss": "the person talking",
                     "n_clauses": 2, "clauses": ["c1"]},
        "helpfulness": {"kind": "value", "gloss": "being useful",
                        "n_clauses": 2, "clauses": ["c4"]},
    }


@pytest.fixture
def clauses():
    """Four sections, each pinning one thing the election has to get right.

    `Ambiguity`  3 clauses, 2 carry the query's act atom — a MAJORITY, elected.
    `Style`      3 clauses, exactly 1 fires. Conduct-bearing, so ONLY the
                 majority rule can keep it out: it is the fixture that makes
                 the difference between "a majority" and "any hit" visible.
    `Glossary`   BOTH clauses fire, so the firing fraction is 1.0 and only the
                 CONDUCT GATE can keep it out — it is definitional/meta, it
                 states no conduct and shows no worked example.
    `Values`     1 clause, nothing fires.
    """
    return [
        {"id": "c1", "quote": "Ask the user what they meant when the request is unclear.",
         "section_path": ["Ambiguity"], "kind": "conditional", "line": 1,
         "locator": "spec > Ambiguity > 1"},
        {"id": "c2", "quote": "A follow-up question is appropriate when something is unclear.",
         "section_path": ["Ambiguity"], "kind": "example", "line": 2,
         "locator": "spec > Ambiguity > 2"},
        {"id": "c3", "quote": "Background on ambiguity.",
         "section_path": ["Ambiguity"], "kind": "meta", "line": 3,
         "locator": "spec > Ambiguity > 3"},
        {"id": "c4", "quote": "Be useful.", "section_path": ["Values"],
         "kind": "conditional", "line": 4, "locator": "spec > Values > 1"},
        {"id": "g1", "quote": "Clarify means asking what was meant.",
         "section_path": ["Glossary"], "kind": "definitional", "line": 5,
         "locator": "spec > Glossary > 1"},
        {"id": "g2", "quote": "Follow-up means asking a further question.",
         "section_path": ["Glossary"], "kind": "meta", "line": 6,
         "locator": "spec > Glossary > 2"},
        {"id": "s1", "quote": "Ask the user what they meant before answering.",
         "section_path": ["Style"], "kind": "conditional", "line": 7,
         "locator": "spec > Style > 1"},
        {"id": "s2", "quote": "Keep answers short.", "section_path": ["Style"],
         "kind": "example", "line": 8, "locator": "spec > Style > 2"},
        {"id": "s3", "quote": "Style notes follow.", "section_path": ["Style"],
         "kind": "meta", "line": 9, "locator": "spec > Style > 3"},
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
        "c2": [at("clarify_user_intent", "c2", "A follow-up question")],
        "c3": [],
        "c4": [at("helpfulness", "c4", "Be useful")],
        "g1": [at("clarify_user_intent", "g1", "asking what was meant")],
        "g2": [at("clarify_user_intent", "g2", "asking a further question")],
        "s1": [at("clarify_user_intent", "s1", "Ask the user what they meant")],
        "s2": [],
        "s3": [],
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
def index(clauses, annotations, onto):
    return S.StructuralIndex(clauses, annotations, onto)


@pytest.fixture
def quotient(index):
    return SEC.SectionQuotient(index)


# ------------------------------------------------ guard 1: no label access

def test_section_module_never_names_the_reference():
    """STATIC guard, sharing `FORBIDDEN` with `test_no_reference_leak` so the
    two cannot drift. `section.py` is not in that file's frozen QUERY_MODULES
    list, which is exactly why this test exists rather than being assumed."""
    src = GUARD._source("section")
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in GUARD.FORBIDDEN if tok in src]
    assert not hits, (
        f"section.py references the panel at query time: {hits}. The panel is "
        "a measuring instrument, not an input (contract §5 invariant 9).")


def test_no_model_is_called_at_query_time():
    src = GUARD._source("section")
    for tok in ("providers", "urllib", "requests", "openai", "anthropic",
                "http", "socket"):
        assert tok not in src, f"section.py names {tok!r} — querying is offline"


def test_section_queries_open_only_declared_artifacts():
    """DYNAMIC guard. Import UNDER the spy (so an import-time
    `_GOLD = json.load(...)` is visible) and drive every query entry point.

    A module exposing no drivable query surface FAILS rather than skips — a
    skip is not a guard, which is how the previous version of the sibling file
    let a leak through.
    """
    if not (os.path.exists(ANNOTATIONS) and os.path.exists(BEHAVIOUR_ATOMS)):
        pytest.skip("real artifacts not present")
    opened, restore = GUARD._spy_all_open_paths()
    driven = []
    try:
        mod = importlib.reload(importlib.import_module("section"))
        idx = S.StructuralIndex.from_files()
        q = list(mod.load_queries(BEHAVIOUR_ATOMS).values())[0]
        sq = mod.SectionQuotient(idx)
        for meth in ("predict", "rank", "match", "sweep", "election_score",
                     "elect", "diagnostics"):
            fn = getattr(sq, meth, None)
            if fn is None:
                continue
            r = fn(q)
            list(r) if hasattr(r, "__iter__") else r
            driven.append(meth)
    finally:
        restore()
    assert driven, "section.py exposes no drivable query surface, so it is UNGUARDED"
    unexpected = [p for p in opened if p.endswith(".json")
                  and os.path.basename(p) not in GUARD.ALLOWED_ARTIFACTS]
    assert not unexpected, (
        f"section.py opened UNDECLARED artifacts {sorted(set(unexpected))} "
        f"while driving {driven}")


# ------------------------------------------------ the quotient is structural

def test_the_partition_is_the_documents_own_section_path(quotient):
    assert quotient.sections[("Ambiguity",)] == ("c1", "c2", "c3")
    assert quotient.sections[("Values",)] == ("c4",)
    assert quotient.sections[("Glossary",)] == ("g1", "g2")
    assert quotient.sections[("Style",)] == ("s1", "s2", "s3")
    assert quotient.section_of("c2") == ("Ambiguity",)


def test_rank_is_constant_within_a_section(quotient, query):
    """THE DEFINING PROPERTY of a quotient operation: the section is the unit,
    so two clauses of one section cannot be separated by this channel. A
    per-clause smoothing term (what `relevance.py` ships) does not have this
    property — that is the difference between structure and smoothing."""
    r = dict(quotient.rank(query))
    for path, cids in quotient.sections.items():
        vals = {round(r[c], 12) for c in cids}
        assert len(vals) == 1, f"{path} is not scored as one block: {vals}"


def test_section_structure_is_load_bearing(clauses, annotations, onto, query):
    """A mutant that FLATTENS `section_path` to a constant must change the
    answer. If it does not, the module is not using the hierarchy at all and
    every number attributed to the section channel is attributable to
    something else."""
    real = SEC.SectionQuotient(S.StructuralIndex(clauses, annotations, onto))
    flat = [dict(c, section_path=["THE DOCUMENT"]) for c in clauses]
    flattened = SEC.SectionQuotient(S.StructuralIndex(flat, annotations, onto))
    assert real.rank(query) != flattened.rank(query)
    assert real.predict(query) != flattened.predict(query)


def test_a_degenerate_section_signal_scores_zero_not_well(clauses, annotations,
                                                          onto, query):
    """One section containing everything carries no information. The channel
    must then be CONSTANT — which is AUC 0.5 and MCC 0 by construction — and
    must say so, rather than quietly scoring every clause 1.0."""
    flat = [dict(c, section_path=["THE DOCUMENT"]) for c in clauses]
    q = SEC.SectionQuotient(S.StructuralIndex(flat, annotations, onto))
    vals = {round(v, 12) for _, v in q.rank(query)}
    assert len(vals) == 1, "a one-section document must produce a constant score"
    d = q.diagnostics(query)
    assert d["degenerate"] is True
    assert d["n_sections"] == 1


def test_the_conduct_gate_excludes_a_section_that_states_no_conduct(quotient,
                                                                   query):
    """EVERY clause of `Glossary` fires, so its firing fraction is 1.0 and the
    election rule alone would elect it. Only the gate keeps it out, and the
    gate is a TYPED test — the section contains no conditional and no worked
    example, so it states no conduct and cannot be the subject of a behaviour
    — not a score cut. Dropping the gate must therefore change the answer."""
    assert ("Glossary",) not in quotient.conduct_bearing
    assert ("Ambiguity",) in quotient.conduct_bearing
    assert quotient.firing_fraction(query)[("Glossary",)] == 1.0
    assert "g1" in quotient.index.predict(query, "act_match")
    assert "g1" not in quotient.predict(query)
    assert "g1" in quotient.predict(query, gate=False), (
        "the fixture no longer isolates the gate: something OTHER than the "
        "conduct gate is excluding Glossary, so this test would pass with the "
        "gate deleted")


def test_the_quotient_decides_and_the_clause_gets_no_second_vote(quotient, query):
    """A clause in a NON-elected section is not predicted even though it
    matches individually, and a clause in an elected section IS predicted even
    though it matches nothing. Both directions are what makes this a quotient
    rather than a bonus term added to a clause score."""
    pred = quotient.predict(query)
    assert "c3" in pred, "c3 carries no atom but sits in an elected section"
    assert "g1" not in pred, "g1 matches but its section was not elected"


def test_election_needs_a_majority_not_a_hit(quotient, query):
    """`Style` is conduct-bearing and exactly 1 of its 3 clauses fires. A
    majority rule excludes it; an any-hit rule would elect it. That is the only
    difference between the two, so `Style` is what makes this test able to fail
    — `Values` (0 of 1) would pass under either rule and proves nothing."""
    elected = quotient.elect(query)
    assert quotient.firing_fraction(query)[("Style",)] == pytest.approx(1 / 3)
    assert ("Style",) in quotient.conduct_bearing
    assert ("Ambiguity",) in elected
    assert ("Style",) not in elected
    assert ("Values",) not in elected


def test_sweep_is_nested_and_emits_the_curve(quotient, query):
    """The ladder is returned as a curve over how many sections are elected.
    Quoting one point without its neighbours is how a threshold gets
    hand-picked, so the curve is the return value."""
    curve = quotient.sweep(query)
    assert len(curve) >= 1
    for (k1, a), (k2, b) in zip(curve, curve[1:]):
        assert k1 < k2
        assert a <= b, "the family must be nested in the number of sections"


def test_determinism(quotient, query):
    assert quotient.rank(query) == quotient.rank(query)
    assert quotient.predict(query) == quotient.predict(query)
    assert quotient.elect(query) == quotient.elect(query)


def test_empty_query_elects_nothing(quotient):
    assert quotient.predict(S.Query("empty", [])) == set()
    assert quotient.elect(S.Query("empty", [])) == set()


def test_explain_names_the_section_and_why_it_was_or_was_not_elected(quotient,
                                                                     query):
    e = quotient.explain(query, "c3")
    assert e["section_path"] == ["Ambiguity"]
    assert e["elected"] is True
    assert e["conduct_bearing"] is True
    assert e["n_clauses"] == 3 and e["n_firing"] == 2
    assert "c1" in e["firing_clauses"] and "c2" in e["firing_clauses"]
    g = quotient.explain(query, "g1")
    assert g["elected"] is False
    assert g["conduct_bearing"] is False
    assert "conduct" in g["why_not"].lower()


# -------------------------------------------------- constants are declared

def test_every_declared_constant_carries_a_justification_and_its_provenance():
    for name, c in SEC.CONSTANTS.items():
        assert "value" in c, name
        assert len(c.get("why", "")) > 40, f"{name} has no real justification"
        assert isinstance(c.get("fitted_on_panel"), bool), name
        if c["fitted_on_panel"]:
            assert c.get("selected_over"), f"{name} hides what it beat"
            assert c.get("unselected_baseline"), (
                f"{name} is panel-fitted and does not state the no-choice "
                "baseline, so its selection bias is unbounded")


def test_constants_declaration_is_complete():
    """Every module-level constant must be derived from `CONSTANTS` or named in
    the frozen non-parameter list — otherwise a fitted number can be hidden by
    simply not declaring it, which is how `structural.primary_operator` escaped
    its own audit."""
    src = GUARD._source("section")
    declared = set(SEC.CONSTANTS)
    assigned = set(re.findall(r"^([A-Z][A-Z0-9_]*)\s*=", src, re.M))
    unexplained = assigned - SEC.NON_PARAMETERS - {
        n.upper() for n in declared} - {"CONSTANTS", "NON_PARAMETERS"}
    assert not unexplained, (
        f"module-level constants neither declared in CONSTANTS nor listed in "
        f"NON_PARAMETERS: {sorted(unexplained)}")


# --------------------------------------- the measured result cannot be spun

def test_the_measured_result_is_reported_per_behaviour_with_both_floors():
    """The mean of 9 cells is not the verdict. Every reported figure must carry
    its per-behaviour rows AND both floors, because this channel's sign differs
    by behaviour and by product (ranking vs decision rule)."""
    lines = SEC.result_lines()
    text = "\n".join(lines)
    for slug in ("helpfulness", "harm-avoidance-to-third-parties",
                 "avoiding-over-and-under-caution"):
        assert slug in text, f"{slug} missing from the report"
    assert "0.000" in text and "-0.059" in text, "both floors must be printed"


def test_the_verdict_cannot_claim_a_win_the_interval_does_not_support():
    """The best label-free decision rule beats the per-clause operator by
    +0.029 with a CI spanning zero. A verdict word of 'recovered' or 'beats'
    for the DECISION-RULE result is therefore forbidden by the numbers in
    `MEASURED`, and this test is what stops it being written back in."""
    d = SEC.MEASURED["decision_rule"]
    lo, hi = d["ci"]
    assert lo < 0 < hi, "the recorded CI no longer spans zero — re-derive"
    assert d["verdict"] in ("no effect", "not established"), d["verdict"]
    r = SEC.MEASURED["ranking"]
    assert all(c[0] > 0 for c in r["ci_per_behaviour"].values()), (
        "the ranking CIs are recorded as excluding zero; if that changed the "
        "verdict below must change with it")
    assert r["verdict"] == "established"


def test_the_supervised_ceiling_is_labelled_as_a_diagnostic_not_a_target():
    c = SEC.MEASURED["supervised_ceiling"]
    assert c["label_free"] is False
    assert c["value"] == 0.536
    assert "diagnostic" in c["note"].lower()


# ---------------------------------------------------- real-artifact smoke

@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_real_index_partitions_the_real_spec():
    idx = S.StructuralIndex.from_files()
    q = SEC.SectionQuotient(idx)
    assert len(q.sections) == 78
    assert sum(len(v) for v in q.sections.values()) == len(idx.ids)
    # 11 sections state no conduct at all; they hold 31 of the 593 clauses.
    assert len(q.sections) - len(q.conduct_bearing) == 11
    excluded = sum(len(q.sections[p]) for p in q.sections
                   if p not in q.conduct_bearing)
    assert excluded == 31


@pytest.mark.skipif(not os.path.exists(BEHAVIOUR_ATOMS), reason="artifacts absent")
def test_real_queries_rank_the_real_sections():
    idx = S.StructuralIndex.from_files()
    q = SEC.SectionQuotient(idx)
    queries = SEC.load_queries(BEHAVIOUR_ATOMS)
    assert queries
    for slug, query in queries.items():
        sc = q.election_score(query)
        assert set(sc) == set(q.sections)
        assert all(0.0 <= v <= 1.0 for v in sc.values())
        assert len({round(v, 9) for v in sc.values()}) > 1, slug


# ------------------------------------------------------------------ report

if __name__ == "__main__":   # pragma: no cover
    raise SystemExit(SEC.main(["--report"]))
