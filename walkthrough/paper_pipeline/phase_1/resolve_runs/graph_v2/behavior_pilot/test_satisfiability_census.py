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
    acts, governs, contexts, protects, actors, purposes, plumbing = _current_vector()
    # acts carry (canonical, arg-sort) — assert status is NOT instrument-
    # visible and must not appear (prereg addendum 2)
    assert acts == frozenset({("refuse", None)})
    # both lanes' governs values are instrument-visible
    assert governs == frozenset({"truthfulness", "substance_usefulness"})
    assert contexts == frozenset({"vulnerable_interaction"})
    # both lanes' protects values are instrument-visible
    assert protects == frozenset({"user", "third_party"})
    assert plumbing == frozenset()


def test_vector_collapses_inert_sort_sentinels():
    # arg_ok fails open identically for missing/"none"/"other"
    sig, ap, pa, _ = _layers()
    corpus = {"n1": [("refuse", "forbid")]}
    br = {"refuse": "refuse"}
    base = SC.vector("n1", corpus, br, sig, ap, pa, None, {})[0]
    for inert in ("none", "other"):
        assert SC.vector("n1", corpus, br, sig, ap, pa, None,
                         {"refuse": inert})[0] == base


def test_vector_purposes_exclude_definitional_keys():
    # lane-scope ruling 2026-08-20: the purpose OR-channel was verdict-gated
    # on the assert lane only; definitional keys (nid|c{i}) never feed it,
    # so their purpose credits are not part of the instrument-visible vector
    purposes = _current_vector()[5]
    assert purposes == frozenset({"harm_prevention"})
    assert "empowerment" not in purposes


def test_vector_actors_include_definitional_keys():
    # the actor wall consumes ALL keys including definitional ones
    actors = _current_vector()[4]
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


def test_vector_carries_functor_arg_sorts():
    # all three v18 modules declare arg_sorts, so arg_ok() is live and the
    # functor's raw sort is instrument-visible (None = fail-open)
    sig, ap, pa, _ = _layers()
    corpus = {"n1": [("refuse", "forbid")]}
    br = {"refuse": "refuse"}
    v = SC.vector("n1", corpus, br, sig, ap, pa, None, {"refuse": "request"})
    assert ("refuse", "request") in v[0]
    v2 = SC.vector("n1", corpus, br, sig, ap, pa, None, {})
    assert ("refuse", None) in v2[0]


def test_status_twins_share_vector_class():
    """Addendum-2 regression: l3877_3953_n009/n010 differ ONLY in assert
    status (oblige vs prefer); relevance() never consumes status, so their
    vectors must be identical — the old status-bearing tuple falsely
    SEPARATED n010."""
    import relevance_by_act as RBA
    sig, ap, pa, ctx = SC.load_layers()
    asorts = RBA.arg_sorts()
    corpus = RBA.corpus_acts(); br = RBA.bridges()
    v9 = SC.vector("l3877_3953_n009", corpus, br, sig, ap, pa, None, asorts)
    v10 = SC.vector("l3877_3953_n010", corpus, br, sig, ap, pa, None, asorts)
    assert v9 == v10


def test_vector_carries_plumbing_flags():
    sig = {"n1|0": {"governs": ["truthfulness"], "contexts": [],
                    "authority_plumbing": True},
           "n1|1": {"governs": ["tone_manner"], "contexts": [],
                    "authority_plumbing": False}}
    v = SC.vector("n1", {"n1": []}, {}, sig, {}, {})
    assert v[6] == frozenset({"0"})


PREFIXTURE = os.path.join(HERE, "panel_run1", "convergence",
                          "satisfiability_census_v18_PREFIXTURE.json")


# E1 flips from the frozen POSTFIX diff — the eight nodes the definition-lane
# merge separated. Pinned as a SUBSET check (never live counts) so future
# legitimate refinements cannot silently un-separate them.
E1_NODES = {
    "avoiding-over-and-under-caution": ["l1_170_n030", "l611_698_n009"],
    "harm-avoidance-to-third-parties": ["l1_170_n038", "l831_1000_n006"],
    "helpfulness": ["l1_170_n030", "l3239_3382_n012", "l3502_3504_n001",
                    "l609_698_n011"],
}


@pytest.mark.skipif(not os.path.exists(PREFIXTURE), reason="pre-fix baseline absent")
def test_real_corpus_monotone_refinement():
    """Prereg P1/P2/P3/P4 on modules_contract_v18.json, with the addendum-2
    correction: the prefixture's lone false SEPARABLE (l3877_3953_n010,
    status over-refinement) is excluded from the monotone comparison and
    pinned UNSAT in both views."""
    pre = json.load(open(PREFIXTURE))["summary"]
    rep = SC.census("modules_contract_v18.json")
    colliders = {"l797_830_n011", "l831_1000_n001", "l831_1000_n011"}
    # addendum-2 corrected false SEPARABLEs (inert status / none-vs-other
    # sort distinctions the instrument never consumes)
    corrected = {"l3877_3953_n010", "l2126_2404_n023"}
    for slug, rows in rep.items():
        pre_unsat = set(pre[slug]["unsat"])
        pre_sep = set(pre[slug]["separable"])
        # P4: mismatch sets invariant (fix touches vector() only)
        assert set(rows) == pre_unsat | pre_sep, f"{slug}: mismatch set changed"
        post_unsat = {n for n, r in rows.items() if r["status"] == "UNSAT"}
        post_sep = {n for n, r in rows.items() if r["status"] == "SEPARABLE"}
        # P1 (corrected, addendum 2): monotone refinement modulo the two
        # reclassified false SEPARABLEs
        assert post_unsat <= pre_unsat | corrected, \
            f"{slug}: new UNSAT nodes {post_unsat - pre_unsat - corrected}"
        assert post_sep >= pre_sep - corrected, \
            f"{slug}: lost SEPARABLE nodes {pre_sep - post_sep - corrected}"
        # E1 subset pin: the definition-lane separations persist
        for n in E1_NODES.get(slug, []):
            assert rows[n]["status"] == "SEPARABLE", f"{slug}::{n} lost E1 separation"
        # P2: collider control nodes stay UNSAT under CURRENT (their fix
        # family is act-refinement subtypes, not this layer merge)
        for n in colliders & set(rows):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} flipped without an act change"
        # P3: reachable separability superset of current
        rch_sep = {n for n, r in rows.items() if r["status_reachable"] == "SEPARABLE"}
        assert rch_sep >= post_sep, f"{slug}: reachable lost current-separable nodes"
        # addendum-2 pin: the corrected false SEPARABLEs are UNSAT in both views
        for n in corrected & set(rows):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} not reclassified"
            assert rows[n]["status_reachable"] == "UNSAT", f"{slug}::{n} reachable"


def test_load_layers_merges_definition_lanes():
    """The fix lives in load_layers(); fixture tests bypass it, so pin the
    merge against the REAL files (subset checks, not live counts)."""
    sig, ap, pa, ctx = SC.load_layers()
    # definitional keys (|c{i}) are present in all three merged layers
    assert any(k.split("|")[1].startswith("c") for k in sig)
    assert any(k.split("|")[1].startswith("c") for k in ap)
    assert any(k.split("|")[1].startswith("c") for k in pa)
    # and the assert-level keys survived the merge
    assert any(not k.split("|")[1].startswith("c") for k in sig)
    # context-atom consensus credits loaded (reachable view input)
    assert ctx, "context_atoms_consensus credits missing"


def test_guards_fire_on_undeclarable_channels(tmp_path):
    for channel in ("party_concern", "governs_conditional"):
        mf = tmp_path / f"mods_{channel}.json"
        mf.write_text(json.dumps({"modules": {"some-behaviour": {channel: ["x"]}}}))
        with pytest.raises(NotImplementedError):
            SC.census(str(mf))
