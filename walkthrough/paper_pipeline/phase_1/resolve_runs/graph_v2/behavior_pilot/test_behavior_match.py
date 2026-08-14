"""Offline tests for the behavior-matching skeleton. No network, no spend:
the seat is mocked through the injectable `complete` seam; clingo runs for
real where it is cheap (two small modules, one solve)."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import behavior_match as bm  # noqa: E402

clingo = pytest.importorskip("clingo")


# --------------------------------------------------------------------------
#  Seat discipline
# --------------------------------------------------------------------------

def _atom(name="demo_atom", gloss="a user under 18 interacting"):
    return {"name": name, "kind": "entity", "gloss": gloss,
            "behavior_text": "some behavior text"}


def test_prompt_is_blind_on_names():
    """The seat prompt carries glosses and document text only — never the
    atom's snake_case name, never a node/predicate id (rename_seat's
    measured blindness, kept)."""
    views = bm.node_views()
    atom = _atom(name="secret_atom_name_xyz")
    for node_id, view in views.items():
        prompt = bm.build_prompt(atom, view)
        assert "secret_atom_name_xyz" not in prompt
        assert node_id not in prompt


def test_node_views_omit_predicate_name_blocks():
    """PROVIDES/NEEDS blocks (predicate names) must not leak into the view."""
    views = bm.node_views()
    assert len(views) == 15
    for view in views.values():
        joined = view["establishes"] + view["source_text"]
        assert "PROVIDES" not in joined
        assert "use EXACTLY these names" not in joined
    # a known node's claim survives extraction
    assert "authority hierarchy" in views["l1_170_n028"]["establishes"]
    # and verbatim document text rides along
    assert any(v["source_text"] for v in views.values())


def test_judge_valid_verdict_passes_through():
    v = bm.judge(lambda s, u: {"text": json.dumps(
        {"verdict": "engaged", "grounds": "because"})}, "prompt")
    assert v == {"verdict": "engaged", "grounds": "because"}


def test_judge_fails_closed_on_garbage():
    v = bm.judge(lambda s, u: {"text": "no json here"}, "prompt")
    assert v["verdict"] == "not_engaged"
    assert "fail-closed" in v["grounds"]


def test_judge_fails_closed_on_wrong_enum():
    v = bm.judge(lambda s, u: {"text": json.dumps(
        {"verdict": "same_concept", "grounds": "wrong seat"})}, "prompt")
    assert v["verdict"] == "not_engaged"


def test_judge_fails_closed_after_transport_errors(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    calls = []

    def boom(s, u):
        calls.append(1)
        raise OSError("transport down")
    v = bm.judge(boom, "prompt")
    assert v["verdict"] == "not_engaged"
    assert len(calls) == 3


def test_judge_propagates_cost_gate():
    """The cost gate is not a transient (rename_seat's pre-ds7 finding)."""
    class CostGateError(Exception):
        pass

    def gate(s, u):
        raise CostGateError("ceiling")
    with pytest.raises(CostGateError):
        bm.judge(gate, "prompt")


def test_judge_passes_schema_to_slot():
    got = []
    bm.judge(lambda s, u: {"text": json.dumps(
        {"verdict": "not_engaged", "grounds": ""})}, "p",
        schema_slot=got.append)
    assert got == [bm.SCHEMA]


# --------------------------------------------------------------------------
#  Retrieval
# --------------------------------------------------------------------------

def test_lexical_ranker_prefers_overlap():
    views = {"n_roleplay": {"establishes": "immersive romantic roleplay "
                            "with a U18 user is forbidden",
                            "source_text": ""},
             "n_birthday": {"establishes": "overview-then-detail for "
                            "birthday party planning", "source_text": ""}}
    atom = _atom(gloss="the assistant engages in immersive romantic "
                       "roleplay with the user")
    ranked = bm.rank_candidates([atom], views, top_k=2)
    assert ranked[0][0][1] == "n_roleplay"
    assert ranked[0][0][0] > ranked[0][1][0]


def test_injected_embedding_wins_over_lexical():
    """When an embed callable is injected its geometry decides the ranking,
    even against the lexical evidence."""
    views = {"n_a": {"establishes": "exact copy of the atom gloss words",
                     "source_text": ""},
             "n_b": {"establishes": "zzz unrelated", "source_text": ""}}
    atom = _atom(gloss="exact copy of the atom gloss words")

    def embed(texts):
        # order: candidates (sorted ids: n_a, n_b) then queries
        return [[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]]
    ranked = bm.rank_candidates([atom], views, embed=embed, top_k=2)
    assert ranked[0][0][1] == "n_b"


def test_embed_failure_falls_back_to_lexical():
    """embed returning None (the recurse_driver failure contract) must not
    break retrieval."""
    views = {"n_a": {"establishes": "romantic roleplay", "source_text": ""},
             "n_b": {"establishes": "unrelated", "source_text": ""}}
    atom = _atom(gloss="romantic roleplay")
    ranked = bm.rank_candidates([atom], views, embed=lambda t: None, top_k=1)
    assert ranked[0][0][1] == "n_a"


def test_match_atoms_first_engaged_wins_and_memoises():
    views = {"n_a": {"establishes": "alpha topic", "source_text": ""},
             "n_b": {"establishes": "beta topic", "source_text": ""}}
    atoms = [_atom(gloss="beta topic exactly"),
             _atom(gloss="beta topic exactly")]   # duplicate gloss on purpose
    calls = []

    def complete(system, user):
        calls.append(user)
        verdict = "engaged" if "beta topic" in user else "not_engaged"
        return {"text": json.dumps({"verdict": verdict, "grounds": "g"})}
    out = bm.match_atoms(atoms, complete, views=views, top_k=2)
    assert out["matched_nodes"] == ["n_b"]
    for entry in out["per_atom"]:
        assert entry["matched"] == "n_b"
    # duplicate (gloss, node) pairs are memoised: the second atom pays nothing
    assert out["seat_calls"] == len(calls) <= 2


def test_match_atoms_call_cap_is_a_mechanism():
    views = {"n_a": {"establishes": "alpha", "source_text": ""},
             "n_b": {"establishes": "beta", "source_text": ""}}
    atoms = [_atom(gloss="gloss one"), _atom(gloss="gloss two")]

    def complete(system, user):
        return {"text": json.dumps(
            {"verdict": "not_engaged", "grounds": "g"})}
    out = bm.match_atoms(atoms, complete, views=views, top_k=2,
                         max_seat_calls=1)
    assert out["seat_calls"] == 1
    assert any(e.get("capped") for e in out["per_atom"])
    # capped atoms keep their ranked candidates on the record
    capped = [e for e in out["per_atom"] if e.get("capped")]
    assert all(e["candidates"] for e in capped)


# --------------------------------------------------------------------------
#  Behavior module rendering
# --------------------------------------------------------------------------

def test_render_behavior_module_shape():
    lp = bm.render_behavior_module(
        "b_demo", "a demo behavior", ["user(u1)", "age_under_18(u1)"],
        does=["some_act(a1, u1)"])
    assert lp.startswith("%% behavior: b_demo")
    assert "%% inputs: age_under_18/1, user/1" in lp
    assert "behavior(b_demo)." in lp
    assert "user(u1).   % [B] b_demo" in lp
    assert "does(b_demo, some_act(a1, u1))." in lp


def test_render_behavior_module_refuses_non_asp_id():
    with pytest.raises(ValueError):
        bm.render_behavior_module("B-1", "bad id", ["user(u1)"])


# --------------------------------------------------------------------------
#  clingo relevance query — real clingo, real translated modules on disk
# --------------------------------------------------------------------------

PAIR = ["l797_809_n001", "l4572_4691_n011"]   # requires-resolved pair


def test_relevance_query_fires_and_finds_conflict():
    lp = bm.render_behavior_module(
        "b_t", "U18 romance test", bm.DEMO_FACTS, bm.DEMO_DOES)
    out = bm.relevance_query(PAIR, lp)
    assert out["relevant_modules"] == sorted(
        bm.link_nodes.norm_id(n) for n in PAIR)
    assert out["silent_modules"] == []
    forbids = [a for a in out["asserts_by_module"]["l4572_4691_n011"]
               if a["deontic"] == "forbid"]
    assert any("engage_in_immersive_romantic_roleplay"
               in a["act"] for a in forbids)
    assert out["conflicts"] == [{
        "module": "l4572_4691_n011",
        "forbidden_act_performed":
            "engage_in_immersive_romantic_roleplay(a1,u1)"}]


def test_relevance_query_silent_module_reported():
    """With no situation facts, no rule fires: relevance must report the
    modules as silent, not invent hits."""
    lp = bm.render_behavior_module("b_empty", "no facts", [])
    out = bm.relevance_query(PAIR, lp)
    assert out["relevant_modules"] == []
    assert set(out["silent_modules"]) == set(
        bm.link_nodes.norm_id(n) for n in PAIR)
    assert out["conflicts"] == []


def test_relevance_query_missing_module_is_loud():
    with pytest.raises(bm.QueryError):
        bm.relevance_query(["l9999_9999_n001"], "behavior(b_x).\n")


def test_relevance_query_refuses_broken_program():
    with pytest.raises(bm.QueryError):
        bm.relevance_query(PAIR, "this is not asp §§§\n")


# --------------------------------------------------------------------------
#  End-to-end demo (mock seat, lexical retrieval, real clingo)
# --------------------------------------------------------------------------

def test_run_demo_end_to_end():
    out = bm.run_demo()
    assert out["match"]["matched_nodes"] == [
        "l4572_4691_n011", "l797_809_n001"]
    assert out["query"]["relevant_modules"] == [
        "l4572_4691_n011", "l797_809_n001"]
    assert len(out["query"]["conflicts"]) == 1
    assert ("engage_in_immersive_romantic_roleplay"
            in out["query"]["conflicts"][0]["forbidden_act_performed"])
    # the obligation from the stay-in-bounds provider also fired
    obliges = [a for a in
               out["query"]["asserts_by_module"]["l797_809_n001"]
               if a["deontic"] == "oblige"]
    assert obliges, "refrain_from_full_compliance should be obliged"


# --------------------------------------------------------------------------
#  Pilot selection artifact
# --------------------------------------------------------------------------

def test_pilot_behaviors_artifact():
    path = os.path.join(HERE, "pilot_behaviors.json")
    o = json.load(open(path, encoding="utf-8"))
    assert 3 <= len(o["selected"]) <= 8
    slugs = {b["slug"] for b in o["behaviors"]}
    assert set(o["selected"]) <= slugs
    # every selected behavior clears the recorded floor
    by_slug = {b["slug"]: b for b in o["behaviors"]}
    for s in o["selected"]:
        assert by_slug[s]["max_span_lift"] >= 0.9
    # stats carry the evaluation-only guard in writing
    assert "never truth" in o["_purpose"]


def test_pilot_selection_is_deterministic():
    sys.path.insert(0, HERE)
    import select_pilot_behaviors as spb
    a = spb.analyse()
    b = spb.analyse()
    assert a == b
    on_disk = json.load(open(os.path.join(HERE, "pilot_behaviors.json"),
                             encoding="utf-8"))
    assert on_disk == a
