"""Targeted tests for drift_dossiers.py — the drift-standing pass's
producer/validator (DRIFT_STANDING_DESIGN.md §3).

Registered in conftest._OPTIONAL. Scope, honestly stated: these cover the
VALIDATOR contract (coverage exactly-once, closed verdict/confidence sets,
non-empty reasons, headerless refusal, unknown/duplicate ids) and the
banned-key fence, over synthetic fixtures — plus the case-list pinning over
the real census file. The full generation path is covered by inline
self-checks at build time (see drift_dossiers.py docstring, TEST DEBT).
"""
from __future__ import annotations

import json
import os

import pytest

import drift_dossiers as D

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- fixtures

def _mini_set(tmp_path, header=True):
    """A 2-dossier synthetic stripped set, schema-shaped like the real one."""
    d = tmp_path / "dossiers"
    d.mkdir()
    lines = []
    if header:
        lines.append({"record": "config_identity", "pass": "drift_standing",
                      "config_tag": "t", "inputs": {}, "threshold_rule": "otsu",
                      "pricing_version": None, "join_version": None})
    for did in ("beh__case_1", "beh__case_2"):
        dossier = {
            "dossier_id": did, "config_tag": "t",
            "behaviour": {"slug": "beh", "name": "B", "definition": "d",
                          "query_atoms": []},
            "clause": {"id": "m0001", "text": "x", "section_path": [],
                       "locator": "L", "kind": "imperative", "atoms": []},
            "rendering": "r",
            "explain": {"channels": {}, "channel_share": {},
                        "matched_atoms": [], "top_lexical_terms": [],
                        "atom_channel_live": True},
            "cut": 0.3, "cut_source": "frozen_artifact",
            "score": {"raw": 1.0, "norm": 0.31}, "distance_to_cut": 0.01,
        }
        (d / f"{did}.json").write_text(json.dumps(dossier, sort_keys=True))
        lines.append({"dossier_id": did, "behaviour": "beh",
                      "file": f"{did}.json"})
    (d / "index.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in lines) + "\n")
    return str(d)


def _verdict(did, verdict="unclear", reason="dry", **kw):
    return {"dossier_id": did, "verdict": verdict,
            "document_reason": reason, **kw}


# ------------------------------------------------------------- validator

def test_clean_full_coverage(tmp_path):
    d = _mini_set(tmp_path)
    rep = D.validate([_verdict("beh__case_1", "admit_defensible", "cites text"),
                      _verdict("beh__case_2", "admit_not_needed", "cites text",
                               confidence="high")], d)
    assert rep["ok"], rep["violations"]
    assert rep["by_verdict"] == {"admit_defensible": 1, "admit_not_needed": 1}


def test_headerless_directory_refused(tmp_path):
    d = _mini_set(tmp_path, header=False)
    rep = D.validate([_verdict("beh__case_1"), _verdict("beh__case_2")], d)
    assert not rep["ok"]
    assert any("config-identity" in e for e in rep["violations"])


@pytest.mark.parametrize("mutate,needle", [
    (lambda v: v[:1], "missing verdict"),                        # coverage
    (lambda v: v + [v[0]], "duplicate"),                         # dupes
    (lambda v: v + [_verdict("beh__nope")], "unknown"),          # unknown id
    (lambda v: [dict(v[0], verdict="correct")] + v[1:],
     "not in the closed set"),                                   # open verdict
    (lambda v: [dict(v[0], document_reason="  ")] + v[1:],
     "non-empty"),                                               # empty reason
    (lambda v: [dict(v[0], confidence="sure")] + v[1:],
     "confidence"),                                              # open conf
])
def test_validator_refuses(tmp_path, mutate, needle):
    d = _mini_set(tmp_path)
    base = [_verdict("beh__case_1"), _verdict("beh__case_2")]
    rep = D.validate(mutate(base), d)
    assert not rep["ok"]
    assert any(needle in e for e in rep["violations"]), rep["violations"]


def test_contaminated_dossier_refused(tmp_path):
    """A panel-side field planted in a dossier fails validation even when
    the verdict file itself is perfect — the fence is checked at read time."""
    d = _mini_set(tmp_path)
    p = os.path.join(d, "beh__case_1.json")
    dossier = json.load(open(p))
    dossier["panel_score"] = 1
    with open(p, "w") as f:
        json.dump(dossier, f)
    rep = D.validate([_verdict("beh__case_1"), _verdict("beh__case_2")], d)
    assert not rep["ok"]
    assert any("banned panel-side" in e for e in rep["violations"])


# ------------------------------------------------------------ fence unit

def test_banned_key_hits_recursive():
    assert D.banned_key_hits({"a": [{"verdicts": []}]}) == ["a[0].verdicts"]
    assert D.banned_key_hits({"panel_anything": 1})  # substring 'panel'
    # values are never scanned — clause text may contain any word
    assert D.banned_key_hits({"text": "the panel said cause and side"}) == []


# ------------------------------------------------------------- case list

def test_case_list_pins_59_plus_1():
    """The design's amended composition, over the real census artifact."""
    if not os.path.exists(D.CENSUS_VERDICTS):
        pytest.skip("census artifacts not present")
    cases = D.case_list()
    assert len(cases) == 60
    from collections import Counter
    assert Counter(c["cause"] for c in cases) == D.EXPECTED_BY_CAUSE
    assert len({c["dossier_id"] for c in cases}) == 60
