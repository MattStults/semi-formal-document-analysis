"""Tests for ontology.py — the relation layer over the atom vocabulary.

Nothing here calls a model or touches the network. The vocabulary fixtures are
hand-written so every expected relation can be read off the fixture itself.

Discipline note: every test in this file was observed FAILING before the code
that satisfies it existed (ModuleNotFoundError first, then per-assertion), and
the ones marked `# MUTATION-VERIFIED` were re-run against a deliberately broken
ontology.py to confirm they fail for their stated reason and not incidentally.
"""
from __future__ import annotations

import json
import os

import pytest

import ontology as O

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ fixtures

@pytest.fixture
def vocab():
    """A miniature vocabulary exercising every mechanical rule.

    ⚠️ READ THIS BEFORE QUOTING ANY TEST IN THIS FILE AS EVIDENCE. This fixture
    is CONSTRUCTED to make each rule fire. It demonstrates that the rules are
    implemented correctly; it says NOTHING about whether they fire on the real
    spec. On `annotations_b8.json` they very nearly do not — see
    `test_mechanical_path_is_a_measured_null_result`, which is the test that
    carries the empirical claim.
    """
    return {
        # a genus/species pair by name-token containment (same kind)
        "harm": {"kind": "situation", "gloss": "Someone is harmed.",
                 "n_clauses": 40, "clauses": []},
        "third_party_harm": {"kind": "situation",
                             "gloss": "Someone outside the conversation is harmed.",
                             "n_clauses": 4, "clauses": []},
        # polarity pair: avoid_X is contrary to X (same kind)
        "topic_censorship": {"kind": "act", "gloss": "Refusing to discuss a topic.",
                             "n_clauses": 3, "clauses": []},
        "avoid_topic_censorship": {"kind": "act",
                                   "gloss": "Not refusing to discuss a topic.",
                                   "n_clauses": 8, "clauses": []},
        # act/situation nominalisation: same vocab_key, different kind
        "refuse_request": {"kind": "act", "gloss": "Declining a user request.",
                           "n_clauses": 9, "clauses": []},
        "request_refused": {"kind": "situation",
                            "gloss": "A user request has been declined.",
                            "n_clauses": 5, "clauses": []},
        # an unrelated atom of a different kind that shares a token with `harm`
        "harm_prevention": {"kind": "value",
                            "gloss": "The goal of preventing harm.",
                            "n_clauses": 12, "clauses": []},
        "user": {"kind": "entity", "gloss": "The person talking to the model.",
                 "n_clauses": 300, "clauses": []},
    }


@pytest.fixture
def onto(vocab):
    return O.Ontology.mechanical(vocab)


def rel_pairs(relations, rel):
    return {(r.a, r.b) for r in relations if r.rel == rel}


# ------------------------------------------------------- invariants (hard)

def test_no_model_is_called_at_query_time():
    """Deriving the ontology may call a model ONCE PER SPEC; answering a query
    never may. The live path must be reachable only through an explicit CLI
    flag, never from the query surface."""
    src = open(os.path.join(HERE, "ontology.py")).read()
    for forbidden in ("import requests", "import torch", "transformers",
                      "sentence_transformers", "import openai", "import anthropic"):
        assert forbidden not in src, f"ontology.py must not reference {forbidden}"
    # providers is imported lazily, inside the live path only
    assert "\nimport providers" not in src and "\nfrom providers" not in src, \
        "providers must be imported lazily inside the --live path"


def test_nothing_reads_panel_labels():
    """Invariant 8: no labelled example may enter the derivation. The panel
    file is the measuring instrument; naming it here at all is the failure."""
    src = open(os.path.join(HERE, "ontology.py")).read()
    for forbidden in ("behaviours.json", "llm-panel-review", "load_panel",
                      "verdicts", "import benchmark"):
        assert forbidden not in src, f"ontology.py must not reference {forbidden}"


def test_derivation_is_behaviour_independent(vocab):
    """Derived ONCE PER SPEC. The API must not even accept a behaviour."""
    import inspect
    for fn in (O.derive_mechanical, O.Ontology.mechanical):
        params = inspect.signature(fn).parameters
        assert not any("behaviour" in p or "panel" in p or "query" in p
                       for p in params), f"{fn.__name__} takes a query-side argument"


# ----------------------------------------------------- mechanical relations

def test_name_token_containment_yields_subsumption(onto):
    """`harm` is broader than `third_party_harm`: fewer modifiers, same kind."""
    assert ("harm", "third_party_harm") in rel_pairs(onto.relations, "subsumes")
    assert ("third_party_harm", "harm") not in rel_pairs(onto.relations, "subsumes")


def test_polarity_prefix_yields_contrary_not_subsumption(onto):
    """`avoid_topic_censorship` must NOT subsume `topic_censorship` merely
    because its token set is a superset — the extra token is a negation."""
    contrary = rel_pairs(onto.relations, "contrary")
    assert {"topic_censorship", "avoid_topic_censorship"} in [
        set(p) for p in contrary]
    subs = rel_pairs(onto.relations, "subsumes")
    assert ("topic_censorship", "avoid_topic_censorship") not in subs


def test_nominalisation_bridges_act_to_situation(onto):
    """`refuse_request` (act) and `request_refused` (situation) share a
    vocab_key. That is an ENTAILMENT across kinds, never a same_as merge."""
    ent = rel_pairs(onto.relations, "entails")
    assert ("refuse_request", "request_refused") in ent
    assert not any({r.a, r.b} == {"refuse_request", "request_refused"}
                   for r in onto.relations if r.rel == "same_as")


def test_cross_kind_subsumption_is_rejected_and_counted(vocab):
    """A situation may not subsume a value however containing its tokens are.
    # MUTATION-VERIFIED"""
    rels = [O.Relation("subsumes", "harm", "harm_prevention", "model", "", "model")]
    kept, rej = O.validate(rels, vocab)
    assert kept == []
    assert rej["cross_kind_subsumes"] == 1


def test_unknown_atom_is_rejected_and_counted(vocab):
    """Nothing may be invented: both endpoints must already be vocabulary.
    # MUTATION-VERIFIED"""
    rels = [O.Relation("subsumes", "harm", "not_an_atom", "model", "", "model"),
            O.Relation("subsumes", "also_fake", "harm", "model", "", "model")]
    kept, rej = O.validate(rels, vocab)
    assert kept == []
    assert rej["unknown_atom"] == 2


def test_subsumption_is_acyclic(vocab):
    """# MUTATION-VERIFIED"""
    rels = [O.Relation("subsumes", "harm", "third_party_harm", "x", "", "model"),
            O.Relation("subsumes", "third_party_harm", "harm", "x", "", "model")]
    kept, rej = O.validate(rels, vocab)
    assert len(kept) == 1
    assert rej["cycle"] == 1
    assert O.Ontology(vocab, kept).is_acyclic("subsumes")


def test_real_vocabulary_subsumption_is_acyclic():
    o = O.Ontology.from_annotations(os.path.join(HERE, "annotations_b8.json"))
    assert o.is_acyclic("subsumes")
    assert o.is_acyclic("entails")


def test_self_loops_rejected(vocab):
    rels = [O.Relation("subsumes", "harm", "harm", "x", "", "model")]
    kept, rej = O.validate(rels, vocab)
    assert kept == [] and rej["self_loop"] == 1


def test_contrary_beats_subsumes_on_the_same_pair(vocab):
    """A pair cannot be both a genus/species pair and mutually exclusive.
    Contrary wins because a false contrary only costs recall, while a false
    subsumption manufactures matches."""
    rels = [O.Relation("subsumes", "harm", "third_party_harm", "x", "", "mech"),
            O.Relation("contrary", "harm", "third_party_harm", "y", "", "model")]
    kept, rej = O.validate(rels, vocab)
    assert rel_pairs(kept, "subsumes") == set()
    assert rej["contradictory_pair"] == 1


def test_every_relation_carries_its_evidence(onto):
    for r in onto.relations:
        assert r.via, "relation with no rule name is unauditable"
        assert r.source in ("mechanical", "model", "both")
        assert r.a in onto.vocab and r.b in onto.vocab


# ------------------------------------------------------------ reachability

def test_reachability_records_hops_and_path(onto):
    reach = onto.reachable("harm", max_hops=1)
    assert "third_party_harm" in reach
    link = reach["third_party_harm"]
    assert link.hops == 1
    assert link.path and link.path[0].rel == "subsumes"


def test_reachability_is_bounded_by_max_hops(vocab):
    v = dict(vocab)
    v["a1"] = {"kind": "act", "gloss": "", "n_clauses": 1, "clauses": []}
    v["a2"] = {"kind": "act", "gloss": "", "n_clauses": 1, "clauses": []}
    v["a3"] = {"kind": "act", "gloss": "", "n_clauses": 1, "clauses": []}
    rels = [O.Relation("subsumes", "a1", "a2", "x", "", "model"),
            O.Relation("subsumes", "a2", "a3", "x", "", "model")]
    o = O.Ontology(v, rels)
    assert "a3" not in o.reachable("a1", max_hops=1)
    assert "a3" in o.reachable("a1", max_hops=2)


def test_contrary_is_never_traversed_as_a_connection(onto):
    """A path through a contrary edge would connect a concept to its own
    opposite. Contrary is a defeater, not a bridge."""
    reach = onto.reachable("topic_censorship", max_hops=3)
    assert "avoid_topic_censorship" not in reach


def test_contraries_lookup_is_symmetric(onto):
    assert "avoid_topic_censorship" in onto.contraries("topic_censorship")
    assert "topic_censorship" in onto.contraries("avoid_topic_censorship")


# ------------------------------------------------------- artifact round-trip

def test_json_round_trip(onto, tmp_path):
    p = tmp_path / "ontology.json"
    onto.save(str(p))
    back = O.Ontology.load(str(p))
    assert {(r.rel, r.a, r.b) for r in back.relations} == \
           {(r.rel, r.a, r.b) for r in onto.relations}
    assert back.vocab.keys() == onto.vocab.keys()


def test_merge_marks_relations_both_paths_found(vocab):
    m = [O.Relation("subsumes", "harm", "third_party_harm", "name_subset", "", "mechanical")]
    g = [O.Relation("subsumes", "harm", "third_party_harm", "model", "", "model"),
         O.Relation("contrary", "harm", "user", "model", "", "model")]
    merged = O.merge(m, g)
    both = [r for r in merged if r.source == "both"]
    assert len(both) == 1 and both[0].a == "harm"


def test_agreement_reports_overlap(vocab):
    m = [O.Relation("subsumes", "harm", "third_party_harm", "x", "", "mechanical")]
    g = [O.Relation("subsumes", "harm", "third_party_harm", "y", "", "model"),
         O.Relation("subsumes", "harm_prevention", "harm_prevention", "y", "", "model")]
    a = O.agreement(m, g)
    assert a["both"] == 1
    assert a["mechanical_only"] == 0
    assert a["model_only"] == 1


# ------------------------------------------------------------- the live path

def test_dry_run_is_the_default_and_makes_no_call():
    args = O.build_parser().parse_args([])
    assert args.live is False


def test_prompt_only_offers_vocabulary_pairs(vocab):
    system, user = O.render_prompt(sorted(vocab.items()))
    for name in vocab:
        assert name in user
    assert "situation" in system and "subsumes" in system and "contrary" in system


def test_annotation_passes_split_the_relation_space_not_the_vocabulary(vocab):
    """Every pass must see EVERY concept: the pairs worth having are the ones a
    vocabulary split would separate."""
    for name, task in O.PASSES:
        _, user = O.render_prompt(sorted(vocab.items()), task, name)
        assert all(n in user for n in vocab)
        assert name in user


def test_annotation_pass_survives_a_dry_run(vocab):
    """The dry-run client returns None. The whole path — prompt, parse,
    validate — must still execute, so a dry run exercises more than argparse."""
    class Dry:
        def __init__(self):
            self.calls = []

        def complete(self, system, user):
            self.calls.append((system, user))
            return None

    c = Dry()
    rels, rej, per_pass = O.run_annotation_pass(c, vocab)
    assert len(c.calls) == len(O.PASSES)
    assert rels == [] and rej["no_response"] == len(O.PASSES)
    assert set(per_pass) == {n for n, _ in O.PASSES}


def test_cost_estimate_is_reported_before_any_call(vocab):
    est = O.estimate_cost(vocab, O.PASSES, price_per_mtok=(0.20, 1.20),
                          max_tokens=8000)
    assert est["calls"] == len(O.PASSES)
    assert 0 < est["usd"] < 0.20, "a per-spec pass must be cents, not dollars"


def test_parse_response_keeps_only_in_vocabulary_triples(vocab):
    text = json.dumps({"relations": [
        {"rel": "subsumes", "a": "harm", "b": "third_party_harm"},
        {"rel": "subsumes", "a": "harm", "b": "invented_atom"},
        {"rel": "teleports", "a": "harm", "b": "user"},
    ]})
    rels, rej = O.parse_response(text, vocab)
    assert [(r.rel, r.a, r.b) for r in rels] == [
        ("subsumes", "harm", "third_party_harm")]
    assert rej["unknown_atom"] == 1
    assert rej["bad_relation"] == 1


# --------------------------------------------------------- on the real spec

def test_mechanical_path_is_a_measured_null_result():
    """THE empirical test in this file. The mechanical rules are correct and on
    this vocabulary they find almost nothing, and that is the finding: the
    vocabulary is flat and morphologically parallel, so containment morphology
    has nothing to bite on.

    Pinned exactly, so a future change that quietly makes the null go away has
    to come and edit this number and say why. # MUTATION-VERIFIED
    """
    o = O.Ontology.from_annotations(os.path.join(HERE, "annotations_b8.json"))
    by_rule = O.Counter(r.via for r in o.relations)
    assert len(o.vocab) == O.MECHANICAL_NULL_RESULT["n_atoms"] == 361
    assert len(o.relations) == O.MECHANICAL_NULL_RESULT["n_relations"] == 20
    for rule in ("contrary_negation", "entails_nominalisation", "same_as_key"):
        assert by_rule[rule] == 0, f"{rule} was a null rule; it now fires"
    touched = {n for r in o.relations for n in (r.a, r.b)}
    assert len(touched) / len(o.vocab) < 0.10, \
        "mechanical coverage claim in MECHANICAL_NULL_RESULT is stale"


def test_zero_avoid_atoms_have_an_unnegated_partner():
    """WHY the polarity rule is null, asserted rather than asserted-in-prose:
    22 atoms are `avoid_*` and not one of their base concepts is an atom."""
    o = O.Ontology.from_annotations(os.path.join(HERE, "annotations_b8.json"))
    toks = {n: O.name_tokens(n) for n in o.vocab}
    negated = [n for n in o.vocab if toks[n] & O.NEGATION_TOKENS]
    assert len(negated) >= 20
    partners = [n for n in negated
                if any(toks[m] == toks[n] - O.NEGATION_TOKENS
                       and o.kind(m) == o.kind(n) for m in o.vocab if m != n)]
    assert partners == []


def test_every_atom_has_exactly_one_kind():
    """The gate's finding, pinned: kind is DERIVABLE FROM NAME in this
    artifact. That is why no kind-AGREEMENT operation can add information at
    any weight, and why typing has to be load-bearing through structural ROLE
    instead. `structural.py` is designed around this fact."""
    raw = json.load(open(os.path.join(HERE, "annotations_b8.json")))
    kinds = {}
    for a in raw["atoms"]:
        kinds.setdefault(a["name"], set()).add(a["kind"])
    assert max(len(k) for k in kinds.values()) == 1


def test_real_ontology_is_typed():
    o = O.Ontology.from_annotations(os.path.join(HERE, "annotations_b8.json"))
    assert len(o.vocab) == 361
    for r in o.relations:
        if r.rel in ("subsumes", "same_as", "contrary"):
            assert o.kind(r.a) == o.kind(r.b), \
                f"{r.rel} crosses kinds: {r.a}/{r.b}"


def test_relation_density_is_reported():
    o = O.Ontology.from_annotations(os.path.join(HERE, "annotations_b8.json"))
    s = o.stats()
    assert s["n_atoms"] == 361
    assert set(s["by_relation"]) <= set(O.RELATIONS)
    assert s["connected_fraction"] > 0.0
