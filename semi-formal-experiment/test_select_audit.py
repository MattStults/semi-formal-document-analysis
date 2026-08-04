"""Tests for select_audit.py — the SELECT step's roster/validator instrument.

Pays down the declared test debt (module docstring, 2026-08-03) and pins the
v2 CALIBRATION contract: the 2026-08-03 sweeps returned 32-47%% of the whole
vocabulary as in-scope — binary self-calibrated judgment is the failure mode —
so v2 moves calibration into the tool: the seat SCORES each atom 0-3, the
brief defines 3 as "would belong in the query", and the VALIDATOR enforces a
budget on score-3 verdicts. An over-budget verdict file is a measured seat
miscalibration, reported loudly, never silently truncated.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import select_audit as SA


@pytest.fixture
def env(tmp_path):
    ann = {"atoms": [
        {"clause_id": "c1", "name": "alpha_act", "kind": "act", "gloss": "a"},
        {"clause_id": "c2", "name": "alpha_act", "kind": "act", "gloss": "a"},
        {"clause_id": "c2", "name": "beta_topic", "kind": "entity", "gloss": "b"},
        {"clause_id": "c3", "name": "gamma_value", "kind": "value", "gloss": "c"},
    ]}
    q = {"behaviours": [{"slug": "beh-x", "name": "X", "definition": "about x"}]}
    ba = {"beh-x": {"atoms": [{"name": "alpha_act", "kind": "act",
                               "gloss": "a"}]}}
    a = tmp_path / "ann.json"; a.write_text(json.dumps(ann))
    qp = tmp_path / "q.json"; qp.write_text(json.dumps(q))
    bp = tmp_path / "ba.json"; bp.write_text(json.dumps(ba))
    out = tmp_path / "audit"
    return {"ann": str(a), "q": str(qp), "ba": str(bp), "out": str(out),
            "tmp": tmp_path}


def _verdicts(path, rows):
    p = str(path)
    with open(p, "w") as f:
        json.dump(rows, f)
    return p


def test_rosters_cover_the_vocabulary_once_each(env):
    paths = SA.build_rosters(env["ann"], env["q"], env["out"])
    assert len(paths) == 1
    r = json.load(open(paths[0]))
    names = [a["name"] for a in r["atoms"]]
    assert sorted(names) == ["alpha_act", "beta_topic", "gamma_value"]
    assert len(set(names)) == len(names)
    assert r["definition"] == "about x"


def test_rosters_are_deterministic(env):
    p1 = SA.build_rosters(env["ann"], env["q"], env["out"])[0]
    b1 = open(p1, "rb").read()
    p2 = SA.build_rosters(env["ann"], env["q"], env["out"])[0]
    assert open(p2, "rb").read() == b1


def test_roster_never_contains_the_selection(env):
    """The sweep seat is selection-blind; the roster must not leak it."""
    p = SA.build_rosters(env["ann"], env["q"], env["out"])[0]
    assert "selected" not in open(p).read()


# ----------------------------------------------------- validator, v1 classes

def _roster(env):
    return SA.build_rosters(env["ann"], env["q"], env["out"])[0]


def _ok_rows(score_alpha=3, score_beta=0, score_gamma=0):
    return [{"name": "alpha_act", "score": score_alpha},
            {"name": "beta_topic", "score": score_beta},
            {"name": "gamma_value", "score": score_gamma}]


def test_validator_clean_and_diffs_against_selection(env):
    r = _roster(env)
    v = _verdicts(env["tmp"] / "v.json", _ok_rows(3, 3, 0))
    f = SA.validate_sweep(r, v, atoms_path=env["ba"])
    assert f is not None
    assert f["in_scope_unselected"] == ["beta_topic"]
    assert f["selected_marked_out_of_scope"] == []


def test_validator_rejects_duplicates(env):
    v = _verdicts(env["tmp"] / "v.json", _ok_rows() + [
        {"name": "alpha_act", "score": 0}])
    assert SA.validate_sweep(_roster(env), v, atoms_path=env["ba"]) is None


def test_validator_rejects_missing_and_unknown(env):
    v = _verdicts(env["tmp"] / "v.json", [
        {"name": "alpha_act", "score": 3},
        {"name": "NOT_IN_ROSTER", "score": 0},
        {"name": "gamma_value", "score": 0}])
    assert SA.validate_sweep(_roster(env), v, atoms_path=env["ba"]) is None


def test_validator_rejects_malformed_scores(env):
    for bad in ("yes", 7, None, True):
        v = _verdicts(env["tmp"] / "v.json", [
            {"name": "alpha_act", "score": bad},
            {"name": "beta_topic", "score": 0},
            {"name": "gamma_value", "score": 0}])
        assert SA.validate_sweep(_roster(env), v, atoms_path=env["ba"]) is None


# ----------------------------------------------------- v2: budgeted scoring

def test_worklist_is_score3_only(env):
    """Scores 1-2 (related/tangential) are reported as strata, never as the
    actionable worklist — that is the calibration lesson in code."""
    v = _verdicts(env["tmp"] / "v.json", _ok_rows(3, 2, 1))
    f = SA.validate_sweep(_roster(env), v, atoms_path=env["ba"])
    assert f["in_scope_unselected"] == []          # beta scored 2, not 3
    assert f["strata"] == {"3": 1, "2": 1, "1": 1, "0": 0}


def test_over_budget_is_reported_not_truncated(env):
    """A seat that marks more score-3 atoms than the budget is MISCALIBRATED;
    the validator must say so and refuse the worklist rather than silently
    keep an arbitrary subset."""
    v = _verdicts(env["tmp"] / "v.json", _ok_rows(3, 3, 3))
    f = SA.validate_sweep(_roster(env), v, atoms_path=env["ba"], budget=2)
    assert f is not None
    assert f["over_budget"] is True
    assert f["in_scope_unselected"] == []          # refused, not truncated
    assert f["n_score3"] == 3 and f["budget"] == 2


def test_within_budget_passes_with_worklist(env):
    v = _verdicts(env["tmp"] / "v.json", _ok_rows(3, 3, 0))
    f = SA.validate_sweep(_roster(env), v, atoms_path=env["ba"], budget=2)
    assert f["over_budget"] is False
    assert f["in_scope_unselected"] == ["beta_topic"]


def test_legacy_boolean_verdicts_still_validate(env):
    """The three 2026-08-03 sweep files use {"in_scope": bool}; they must
    remain loadable (bool maps to score 3/0) so the recorded run stays
    reproducible."""
    v = _verdicts(env["tmp"] / "v.json", [
        {"name": "alpha_act", "in_scope": True},
        {"name": "beta_topic", "in_scope": False},
        {"name": "gamma_value", "in_scope": False}])
    f = SA.validate_sweep(_roster(env), v, atoms_path=env["ba"])
    assert f is not None and f["in_scope_unselected"] == []
