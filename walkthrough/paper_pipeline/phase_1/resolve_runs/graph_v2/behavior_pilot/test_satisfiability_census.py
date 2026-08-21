"""Tests for satisfiability_census.vector() layer-merge faithfulness (campaign
Arc1-e, 2026-08-21; prereg panel_run1/convergence/CENSUS_VECTOR_FIX_PREREG.md).

The census vector must mirror what relevance_by_act.relevance() actually
consumes: assert layers MERGED with definition_* lanes, including the
lane-scope jurisdiction ruling (purpose credits from definitional keys
nid|c{i} never feed the purpose OR-channel; actor credits from definitional
keys DO feed the actor wall). Context atoms are annotated-but-undeclared
vocabulary: they appear only in the REACHABLE vector, never the CURRENT one.
"""
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
import satisfiability_census as SC


def _layers():
    sig = {
        "n1|0": {"governs": ["truthfulness"], "contexts": ["vulnerable_interaction"],
                 "authority_plumbing": False},
        "n1|c0": {"governs": ["substance_usefulness"], "contexts": [],
                  "authority_plumbing": False},
    }
    ap = {"n1|0": ["user"], "n1|c0": ["third_party"]}
    pa = {"n1|0": {"actor": "assistant", "purpose": ["harm_prevention"]},
          "n1|c0": {"actor": "document", "purpose": ["empowerment"]}}
    ctx = {"n1": {"0": ["user_supplied_material"]}}
    return sig, ap, pa, ctx


def _current_vector():
    sig, ap, pa, ctx = _layers()
    corpus = {"n1": [("refuse", "forbid")]}
    br = {"refuse": "refuse"}
    return SC.vector("n1", corpus, br, sig, ap, pa)


def test_vector_merges_definition_signature_and_protects():
    acts, governs, contexts, protects, actors, purposes = _current_vector()
    assert acts == frozenset({("refuse", "forbid")})
    # both lanes' governs values are instrument-visible
    assert governs == frozenset({"truthfulness", "substance_usefulness"})
    assert contexts == frozenset({"vulnerable_interaction"})
    # both lanes' protects values are instrument-visible
    assert protects == frozenset({"user", "third_party"})


def test_vector_purposes_exclude_definitional_keys():
    # lane-scope ruling 2026-08-20: the purpose OR-channel was verdict-gated
    # on the assert lane only; definitional keys (nid|c{i}) never feed it,
    # so their purpose credits are not part of the instrument-visible vector
    *_, purposes = _current_vector()
    assert purposes == frozenset({"harm_prevention"})
    assert "empowerment" not in purposes


def test_vector_actors_include_definitional_keys():
    # the actor wall consumes ALL keys including definitional ones
    _, _, _, _, actors, _ = _current_vector()
    assert actors == frozenset({"assistant", "document"})


def test_context_atoms_reachable_only():
    sig, ap, pa, ctx = _layers()
    corpus = {"n1": [("refuse", "forbid")]}
    br = {"refuse": "refuse"}
    current = SC.vector("n1", corpus, br, sig, ap, pa)
    reachable = SC.vector("n1", corpus, br, sig, ap, pa, ctx)
    assert "user_supplied_material" not in current[2]
    assert "user_supplied_material" in reachable[2]
    # reachable differs from current ONLY by context atoms
    assert current[0] == reachable[0] and current[1] == reachable[1]
    assert current[3:] == reachable[3:]


PREFIXTURE = os.path.join(HERE, "panel_run1", "convergence",
                          "satisfiability_census_v18_PREFIXTURE.json")


@pytest.mark.skipif(not os.path.exists(PREFIXTURE), reason="pre-fix baseline absent")
def test_real_corpus_monotone_refinement():
    """Prereg P1/P2/P3/P4 on modules_contract_v18.json."""
    pre = json.load(open(PREFIXTURE))["summary"]
    rep = SC.census("modules_contract_v18.json")
    colliders = {"l797_830_n011", "l831_1000_n001", "l831_1000_n011"}
    for slug, rows in rep.items():
        pre_unsat = set(pre[slug]["unsat"])
        pre_sep = set(pre[slug]["separable"])
        # P4: mismatch sets invariant (fix touches vector() only)
        assert set(rows) == pre_unsat | pre_sep, f"{slug}: mismatch set changed"
        post_unsat = {n for n, r in rows.items() if r["status"] == "UNSAT"}
        post_sep = {n for n, r in rows.items() if r["status"] == "SEPARABLE"}
        # P1: monotone refinement
        assert post_unsat <= pre_unsat, f"{slug}: new UNSAT nodes {post_unsat - pre_unsat}"
        assert post_sep >= pre_sep, f"{slug}: lost SEPARABLE nodes {pre_sep - post_sep}"
        # P2: collider control nodes stay UNSAT under CURRENT (their fix
        # family is act-refinement subtypes, not this layer merge)
        for n in colliders & set(rows):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} flipped without an act change"
        # P3: reachable separability superset of current
        rch_sep = {n for n, r in rows.items() if r["status_reachable"] == "SEPARABLE"}
        assert rch_sep >= post_sep, f"{slug}: reachable lost current-separable nodes"
