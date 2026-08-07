"""Tests for `salience.py` — the SPEECH-ACT SALIENCE tier (HARNESS_REDESIGN R4).

⛔ MECHANICAL PROPERTIES ONLY. This file must never compute AUC, MCC or any
panel-facing number, and must never open `verdicts_merged.json`, the panel, or
any gold label. The salience tier is PRE-REGISTERED: its default precedence was
chosen from the speech-act argument in R4, before any result existed. A test
here that tuned the default against an outcome would destroy that.

What is checked:
  * determinism across runs and across fresh construction
  * ORDERING-ONLY — the returned SET (and every score) is identical to the
    baseline `section.SectionQuotient.rank` (R4 guard 1)
  * the final tie-break falls through to DOCUMENT ORDER, not clause id
  * every clause kind is handled; unknown/missing kinds are tiered, not dropped
  * the tier precedence is CONFIGURABLE, with a declared default
  * the label-free guards `test_section.py` runs against `section.py`

`salience.py` is also registered in `test_no_reference_leak.QUERY_MODULES`
(MODULE_MAP §11: registration, not documentation, is what fences a module), so
the static scan and the dynamic open-spy cover it there as well.
"""
from __future__ import annotations

import importlib
import json
import os
import re

import pytest

import ontology as O
import salience as SAL
import section as SEC
import structural as S
import test_no_reference_leak as GUARD

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def vocab():
    return {
        "user_request_ambiguous": {"kind": "situation", "gloss": "unclear request",
                                   "n_clauses": 3, "clauses": ["c1"]},
        "clarify_user_intent": {"kind": "act", "gloss": "asking what was meant",
                                "n_clauses": 3, "clauses": ["c1"]},
        "end_user": {"kind": "entity", "gloss": "the person talking",
                     "n_clauses": 2, "clauses": ["c1"]},
    }


@pytest.fixture
def clauses():
    """Four sections, each pinning one mechanical property.

    `Ambiguity`  one clause of every R4-named speech act, in an order that is
                 NOT the default salience order — so a module that merely
                 preserves document order cannot pass the precedence tests.
    `Order`      two clauses of the SAME kind in one section whose ids sort
                 AGAINST document order — the tie-break fixture.
    `Odd`        a clause whose `kind` is unknown to the default precedence and
                 a clause with no `kind` at all — neither may be dropped.
    `Values`     a lone clause nothing fires on.
    """
    return [
        {"id": "b3", "quote": "Background on ambiguity.",
         "section_path": ["Ambiguity"], "kind": "meta", "line": 1,
         "locator": "spec > Ambiguity > 1"},
        {"id": "b2", "quote": "For example, ask what they meant when unclear.",
         "section_path": ["Ambiguity"], "kind": "example", "line": 2,
         "locator": "spec > Ambiguity > 2"},
        {"id": "b9", "quote": "Ask the user what they meant when the request is unclear.",
         "section_path": ["Ambiguity"], "kind": "conditional", "line": 3,
         "locator": "spec > Ambiguity > 3"},
        {"id": "b4", "quote": "Clarifying means asking what was meant.",
         "section_path": ["Ambiguity"], "kind": "definitional", "line": 4,
         "locator": "spec > Ambiguity > 4"},
        {"id": "b5", "quote": "The assistant asks the user what they meant.",
         "section_path": ["Ambiguity"], "kind": "holistic", "line": 5,
         "locator": "spec > Ambiguity > 5"},
        # ids sort a9 < z1, document order is z1 THEN a9.
        {"id": "z1", "quote": "Ask the user what they meant before answering.",
         "section_path": ["Order"], "kind": "conditional", "line": 6,
         "locator": "spec > Order > 1"},
        {"id": "a9", "quote": "Ask the user what they meant, first.",
         "section_path": ["Order"], "kind": "conditional", "line": 7,
         "locator": "spec > Order > 2"},
        {"id": "o1", "quote": "Ask the user what they meant, in an aside.",
         "section_path": ["Odd"], "kind": "marginalia", "line": 8,
         "locator": "spec > Odd > 1"},
        {"id": "o2", "quote": "Ask the user what they meant, untyped.",
         "section_path": ["Odd"], "line": 9,
         "locator": "spec > Odd > 2"},
        {"id": "v1", "quote": "Be useful.", "section_path": ["Values"],
         "kind": "conditional", "line": 10, "locator": "spec > Values > 1"},
    ]


@pytest.fixture
def annotations(vocab, clauses):
    def at(name, cid, quote):
        return {"name": name, "kind": vocab[name]["kind"],
                "gloss": vocab[name]["gloss"], "span_id": "s1", "quote": quote,
                "clause_id": cid, "locator": f"spec > {cid}"}
    firing = ("b9", "b2", "b4", "b5", "z1", "a9", "o1", "o2")
    out = {c["id"]: [] for c in clauses}
    for cid in firing:
        out[cid] = [at("user_request_ambiguous", cid, "the request is unclear"),
                    at("clarify_user_intent", cid, "Ask the user what they meant"),
                    at("end_user", cid, "the user")]
    return out


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
def base(clauses, annotations, onto):
    return SEC.SectionQuotient(S.StructuralIndex(clauses, annotations, onto))


@pytest.fixture
def ranker(base):
    return SAL.Index(base)


def _ids(ranking):
    return [cid for cid, _ in ranking]


# ------------------------------------------------- guard: no label access

def test_salience_module_never_names_the_reference():
    """STATIC guard, sharing `FORBIDDEN` with `test_no_reference_leak` so the
    two cannot drift. Registered there too — this is the belt to that braces."""
    src = GUARD._source("salience")
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in GUARD.FORBIDDEN if tok in src]
    assert not hits, (
        f"salience.py references the panel at query time: {hits}. The panel is "
        "a measuring instrument, not an input (contract §5 invariant 9).")


def test_salience_is_registered_in_the_query_module_fence():
    """MODULE_MAP §11: registration is what fences a module. Documentation is
    not a guard; a query module absent from this list is unscanned."""
    assert "salience" in GUARD.QUERY_MODULES, (
        "salience.py answers a query but is not in QUERY_MODULES, so neither "
        "the static scan nor the open-spy covers it.")


def test_no_model_is_called_at_query_time():
    src = GUARD._source("salience")
    for tok in ("providers", "urllib", "requests", "openai", "anthropic",
                "http", "socket"):
        assert tok not in src, f"salience.py names {tok!r} — querying is offline"


# ------------------------------------------------------------ determinism

def test_rank_is_deterministic_within_one_object(ranker, query):
    a, b = ranker.rank(query), ranker.rank(query)
    assert a == b, "two calls on one ranker disagreed — the sort is unstable"


def test_rank_is_deterministic_across_fresh_construction(
        clauses, annotations, onto, query):
    def once():
        q = SEC.SectionQuotient(S.StructuralIndex(clauses, annotations, onto))
        return SAL.Index(q).rank(query)
    assert once() == once(), (
        "two independently built rankers disagreed — the order depends on "
        "something other than the clauses, the query and the precedence.")


def test_rank_does_not_depend_on_input_row_order(
        clauses, annotations, onto, query):
    """Document order is read from the index, so shuffling the ROWS is a real
    reordering of the document and MAY change the order — but re-running on the
    same shuffle must not."""
    shuffled = list(reversed(clauses))
    def once():
        q = SEC.SectionQuotient(S.StructuralIndex(shuffled, annotations, onto))
        return SAL.Index(q).rank(query)
    assert once() == once()


# --------------------------------------------- R4 guard 1: ORDERING ONLY

def test_rank_returns_exactly_the_baseline_set(ranker, base, query):
    """⛔ R4 guard 1. A sort that adds or drops is a hidden filter."""
    assert set(_ids(ranker.rank(query))) == set(_ids(base.rank(query))), (
        "the salience sort changed the SET. Membership is fixed by the "
        "derivation; precedence orders within it (R4 guard 1).")


def test_rank_returns_the_baseline_multiset_not_just_the_set(ranker, base, query):
    assert sorted(_ids(ranker.rank(query))) == sorted(_ids(base.rank(query))), (
        "a clause was duplicated or lost by the sort")


def test_rank_never_changes_a_score(ranker, base, query):
    """Salience is a TIER, never a score (R4). The numbers must come through
    untouched, or the ordering claim is a rescoring claim in disguise."""
    assert dict(ranker.rank(query)) == dict(base.rank(query)), (
        "the salience layer moved a score — it may only reorder")


def test_examples_are_ordered_below_the_rule_but_never_dropped(ranker, base, query):
    """⛔ R4: examples carry 39.1% of relevance-weighted hits. Demoting them out
    of the result set reinstates the conditional-only recall ceiling."""
    got, exp = _ids(ranker.rank(query)), _ids(base.rank(query))
    assert "b2" in got, "the example clause was dropped, not demoted"
    assert got.index("b9") < got.index("b2"), (
        "the rule did not outrank the example it states")
    assert exp.index("b2") < exp.index("b9"), (
        "fixture no longer discriminates: the baseline must put the example "
        "FIRST, or this test passes without a salience layer")


# ---------------------------------------------------- the lexicographic order

def test_salience_never_crosses_a_higher_baseline_score(ranker, base, query):
    """Default tier order puts salience LAST (§0.0 tier 4): it refines the
    baseline's ties and may never lift a clause over a better-scoring one."""
    scores = dict(base.rank(query))
    got = _ids(ranker.rank(query))
    for i in range(len(got) - 1):
        assert scores[got[i]] >= scores[got[i + 1]], (
            f"{got[i+1]} (score {scores[got[i+1]]}) was placed after "
            f"{got[i]} (score {scores[got[i]]}) — salience overrode the "
            "baseline tier under the default precedence")


def test_default_precedence_orders_the_named_speech_acts(ranker, query):
    """R4 names it: rule-stating > illustrating > commentary."""
    got = _ids(ranker.rank(query))
    pos = {cid: got.index(cid) for cid in ("b9", "b4", "b5", "b2", "b3")}
    assert pos["b9"] < pos["b2"] < pos["b3"], (
        "conditional > example > meta is the ruling's own ordering")
    assert pos["b4"] < pos["b2"], "definitional is rule-stating (R4), not illustration"
    assert pos["b5"] < pos["b2"], "holistic states a standing rule, not an illustration"
    assert pos["b9"] < pos["b4"] < pos["b5"], (
        "the declared default orders the rule-stating band "
        "conditional > definitional > holistic")


# ------------------------------------------------------------- tie-break

def test_final_tie_break_is_document_order_not_clause_id(ranker, base, query):
    """The zero-parameter tie-break (§0.0). `z1` precedes `a9` in the document
    and follows it alphabetically; the baseline sorts by id, so a module that
    inherits the baseline's tail order fails here."""
    got = _ids(ranker.rank(query))
    assert got.index("z1") < got.index("a9"), (
        "equal baseline score and equal kind resolved by clause id, not by "
        "document order — the final tie-break is document order")
    assert _ids(base.rank(query)).index("a9") < _ids(base.rank(query)).index("z1"), (
        "fixture no longer discriminates: the baseline must disagree here")


def test_document_order_follows_the_index_not_the_id(clauses, annotations, onto,
                                                     query):
    def order(rows):
        q = SEC.SectionQuotient(S.StructuralIndex(rows, annotations, onto))
        got = _ids(SAL.Index(q).rank(query))
        return got.index("z1") < got.index("a9")
    assert order(clauses) and not order(list(reversed(clauses))), (
        "reversing the document did not reverse the tie-break — document "
        "order is being read from something other than the document "
        "(clause id, most likely)")


# ------------------------------------------------------- every kind handled

def test_every_declared_kind_has_a_distinct_tier():
    prec = SAL.DEFAULT_KIND_PRECEDENCE
    assert len(set(prec)) == len(prec), "a kind appears twice in the default"
    tiers = [SAL.kind_tier(k, prec) for k in prec]
    assert tiers == sorted(tiers) and len(set(tiers)) == len(prec)


def test_default_precedence_covers_every_kind_in_the_corpus():
    """The corpus's five kinds must all be named, or a real clause falls into
    the unknown bucket silently."""
    if not os.path.exists(CLAUSES):
        pytest.skip("modelspec_clauses.json not present")
    with open(CLAUSES) as fh:
        rows = json.load(fh)
    rows = rows.get("clauses", rows) if isinstance(rows, dict) else rows
    kinds = {(r.get("kind") or "") for r in rows}
    missing = kinds - set(SAL.DEFAULT_KIND_PRECEDENCE)
    assert not missing, (
        f"kinds {sorted(missing)} are in the document but not in the declared "
        "default precedence — they would land in the unknown tier unnoticed")


def test_unknown_and_missing_kinds_are_tiered_never_dropped(ranker, base, query):
    got = _ids(ranker.rank(query))
    assert "o1" in got and "o2" in got, (
        "a clause with an unrecognised or absent `kind` was dropped — "
        "salience orders, it never drops (R4)")
    assert SAL.kind_tier("marginalia") == SAL.kind_tier("") == \
        len(SAL.DEFAULT_KIND_PRECEDENCE), (
        "unknown kinds must share one declared trailing tier")


def test_unknown_kinds_sort_deterministically_among_themselves(ranker, query):
    a, b = _ids(ranker.rank(query)), _ids(ranker.rank(query))
    assert a.index("o1") != a.index("o2") and a == b


def test_tiers_cover_every_clause_of_the_baseline(ranker, base, query):
    tiers = ranker.tiers()
    assert set(tiers) == set(_ids(base.rank(query))), (
        "the tier map and the baseline's clause set disagree — some clause "
        "has no speech-act tier at all")


# -------------------------------------------------------- configurability

def test_precedence_is_configurable(base, query):
    """R4: precedence is a user control, not a fixed policy."""
    flipped = tuple(reversed(SAL.DEFAULT_KIND_PRECEDENCE))
    got = _ids(SAL.Index(base, kind_precedence=flipped).rank(query))
    assert got.index("b3") < got.index("b2") < got.index("b9"), (
        "reversing the declared precedence did not reverse the order — the "
        "precedence argument is not wired to the sort")


def test_a_configured_precedence_still_cannot_change_the_set(base, query):
    flipped = tuple(reversed(SAL.DEFAULT_KIND_PRECEDENCE))
    assert set(_ids(SAL.Index(base, kind_precedence=flipped).rank(query))) == \
        set(_ids(base.rank(query))), "a configured sort changed the set"


def test_tier_order_is_configurable_and_salience_major_is_available(base, query):
    """The PRECEDENCE OF THE TIERS is the other user control R4 names."""
    major = SAL.Index(base, tier_order=("salience", "base"))
    got = _ids(major.rank(query))
    assert set(got) == set(_ids(base.rank(query)))
    assert got.index("b9") < got.index("b2")
    assert got != _ids(SAL.Index(base).rank(query)), (
        "salience-major produced the base-major order — the tier order "
        "argument is not wired to the sort")
    assert [SAL.kind_tier(major.kind_of(c)) for c in got] == \
        sorted(SAL.kind_tier(major.kind_of(c)) for c in got), (
        "under salience-major order the speech-act tier must be the OUTER key")


def test_the_default_is_declared_and_is_base_major(base):
    assert SAL.DEFAULT_TIER_ORDER == ("base", "salience")
    assert SAL.Index(base).tier_order == SAL.DEFAULT_TIER_ORDER
    assert SAL.Index(base).kind_precedence == SAL.DEFAULT_KIND_PRECEDENCE


def test_a_bad_configuration_is_refused_not_silently_ignored(base):
    with pytest.raises(ValueError):
        SAL.Index(base, kind_precedence=("conditional", "conditional"))
    with pytest.raises(ValueError):
        SAL.Index(base, tier_order=("base", "base"))
    with pytest.raises(ValueError):
        SAL.Index(base, tier_order=("base", "nonsense"))


# ------------------------------------------------------------- delegation

def test_predict_is_the_baselines_set_untouched(ranker, base, query):
    """Set and order are computed INDEPENDENTLY (R4 guard 1): the decision
    surface passes straight through."""
    assert ranker.predict(query) == base.predict(query)


def test_explain_names_the_speech_act_and_the_ordering(ranker, query):
    ex = ranker.explain(query, "b2")
    assert ex["kind"] == "example"
    assert ex["salience_tier"] == SAL.kind_tier("example")
    assert ex["sort_order"] == SAL.Index(ranker.base).sort_order()
    assert "document_order" in ex


def test_sort_order_is_reportable(ranker):
    """⛔ R4 guard 2: every reported number names its ordering."""
    so = ranker.sort_order()
    assert so["tier_order"] == list(SAL.DEFAULT_TIER_ORDER)
    assert so["kind_precedence"] == list(SAL.DEFAULT_KIND_PRECEDENCE)
    assert so["tie_break"] == "document_order"


# ------------------------------------------------------------ real corpus

def test_real_corpus_ranks_without_crashing_and_keeps_the_set():
    if not (os.path.exists(ANNOTATIONS) and os.path.exists(BEHAVIOUR_ATOMS)):
        pytest.skip("real artifacts not present")
    idx = S.StructuralIndex.from_files()
    q = list(SEC.load_queries(BEHAVIOUR_ATOMS).values())[0]
    base = SEC.SectionQuotient(idx)
    r = SAL.Index(base)
    got, exp = r.rank(q), base.rank(q)
    assert len(got) == len(exp) == len(idx.ids)
    assert set(_ids(got)) == set(_ids(exp))
    assert dict(got) == dict(exp)
    assert set(r.tiers()) == set(idx.ids), "a real clause has no tier"
