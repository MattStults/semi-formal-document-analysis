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
    (acts, governs, contexts, protects, actors, purposes, plumbing,
     refinements) = _current_vector()
    # acts carry (canonical, arg-sort) — assert status is NOT instrument-
    # visible and must not appear (prereg addendum 2)
    assert acts == frozenset({("refuse", None)})
    # both lanes' governs values are instrument-visible
    assert governs == frozenset({"truthfulness", "substance_usefulness"})
    assert contexts == frozenset({"vulnerable_interaction"})
    # both lanes' protects values are instrument-visible
    assert protects == frozenset({"user", "third_party"})
    assert plumbing == frozenset()
    assert refinements == frozenset()


def test_m2_colliders_addressable_via_refinements():
    """Arc1-b M2 pin (SUBTYPE_MINT_PREREG.md addendum 4): the three collider
    mismatches stay CURRENT-UNSAT (the frozen instrument consumes no
    refinement marks) but separate in the REACHABLE view — the minted
    subtypes are declarable vocabulary, so the rows become
    addressable_by_declaration. Pinned after the registered prediction held
    3/3; subset form, never live counts."""
    rep = SC.census("modules_contract_v18.json")
    pins = {"helpfulness": ["l797_830_n011"],
            "harm-avoidance-to-third-parties": ["l831_1000_n001",
                                                "l831_1000_n011"]}
    for slug, nodes in pins.items():
        for n in nodes:
            r = rep[slug][n]
            assert r["status"] == "UNSAT", f"{slug}::{n} CURRENT changed"
            assert r["status_reachable"] == "SEPARABLE", \
                f"{slug}::{n} not separated in REACHABLE"
            assert r["addressable_by_declaration"] is True


def test_vector_carries_refinement_marks():
    sig, ap, pa, _ = _layers()
    ref = {"n1": frozenset({"exhibit:illustrate"})}
    v = SC.vector("n1", {"n1": []}, {}, sig, ap, pa, None, None, ref)
    assert v[7] == frozenset({"exhibit:illustrate"})
    v2 = SC.vector("n2", {"n2": []}, {}, sig, ap, pa, None, None, ref)
    assert v2[7] == frozenset()


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


# E1 flips from the frozen POSTFIX diff — nodes the definition-lane merge
# separated, as of addendum-3 semantics: CURRENT-separable for the frozen
# instrument, plus one design-space-only separation (UNSAT-current,
# REACHABLE-separable) disclosed per the addendum. Pinned as SUBSET checks.
E1_CURRENT = {
    "avoiding-over-and-under-caution": ["l1_170_n030", "l611_698_n009"],
    "harm-avoidance-to-third-parties": ["l1_170_n038", "l831_1000_n006"],
    "helpfulness": ["l1_170_n030", "l3239_3382_n012", "l3502_3504_n001",
                    "l609_698_n011"],
}
E1_DESIGN_SPACE = {"avoiding-over-and-under-caution": ["l1707_1973_n012"]}

# nodes reclassified SEPARABLE->UNSAT by corrections 2-3 (inert features:
# assert status, none-vs-other sort, contexts slot); pinned UNSAT-current
FALSE_SEPARABLES = {"l3877_3953_n010", "l2126_2404_n023", "l1542_1706_n006"}
COLLIDERS = {"l797_830_n011", "l831_1000_n001", "l831_1000_n011"}


@pytest.mark.skipif(not os.path.exists(PREFIXTURE), reason="pre-fix baseline absent")
def test_real_corpus_semantics_pins():
    """Addendum-3 semantics on modules_contract_v18.json. The old P1 subset
    assertion belongs to the pre-masking semantics (where only refinement
    was possible); masking legitimately adds UNSAT, so the standing
    invariants here are: mismatch-set invariance (P4), every node ever
    reclassified UNSAT stays UNSAT, reachable-separable superset of
    current-separable, and the named pins."""
    pre = json.load(open(PREFIXTURE))["summary"]
    rep = SC.census("modules_contract_v18.json")
    for slug, rows in rep.items():
        pre_unsat = set(pre[slug]["unsat"])
        pre_sep = set(pre[slug]["separable"])
        # P4: mismatch sets invariant (corrections touch vector/grouping only)
        assert set(rows) == pre_unsat | pre_sep, f"{slug}: mismatch set changed"
        post_sep = {n for n, r in rows.items() if r["status"] == "SEPARABLE"}
        # nodes reclassified UNSAT by corrections 2-3 stay UNSAT-current
        for n in FALSE_SEPARABLES & set(rows):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} reclassified back"
        # prefixture UNSAT nodes stay UNSAT, except the E1 definition-lane
        # flips (the only legitimate prefixture-UNSAT -> SEPARABLE path:
        # the definition merge refines classes; masking itself only merges)
        post_unsat = {n for n, r in rows.items() if r["status"] == "UNSAT"}
        assert pre_unsat - set(E1_CURRENT.get(slug, [])) <= post_unsat, \
            f"{slug}: unexpected prefixture-UNSAT flip {pre_unsat - set(E1_CURRENT.get(slug, [])) - post_unsat}"
        # E1 pins: definition-lane separations persist under both semantics
        for n in E1_CURRENT.get(slug, []):
            assert rows[n]["status"] == "SEPARABLE", f"{slug}::{n} lost E1 separation"
        for n in E1_DESIGN_SPACE.get(slug, []):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} design-space node"
            assert rows[n]["status_reachable"] == "SEPARABLE"
            assert rows[n]["addressable_by_declaration"] is True
        # P2: collider control nodes stay UNSAT under CURRENT
        for n in COLLIDERS & set(rows):
            assert rows[n]["status"] == "UNSAT", f"{slug}::{n} flipped without an act change"
        # reachable separability superset of current
        rch_sep = {n for n, r in rows.items() if r["status_reachable"] == "SEPARABLE"}
        assert rch_sep >= post_sep, f"{slug}: reachable lost current-separable nodes"


# REGISTRATION FENCE (repo idiom; round-3 review finding): pinned ground
# truth for the vector's slot inventory and which slots each frozen v18
# behavior consumes. Any change to vector()'s slots (e.g. the Arc1-b
# refinement feature) or to module declarations MUST update this constant
# AND current_mask in the same reviewed commit — the probe fails loud until
# it does. Without the pin the probe re-derives census's own grouping and
# cannot fail (reviewer's mutation proof, round 3).
SLOT_INVENTORY = ("acts", "governs", "contexts", "protects", "actors",
                  "purposes", "plumbing", "refinements")
SLOT_INDEX = {name: i for i, name in enumerate(SLOT_INVENTORY)}
# refinements (Arc1-b mint marks) is dead for every frozen behavior: no
# subtype-conditional declaration exists yet. Same-commit-update rule applies.
DEAD_SLOTS_PINNED = {
    "avoiding-over-and-under-caution": {"contexts", "protects", "purposes",
                                        "refinements"},
    "harm-avoidance-to-third-parties": {"contexts", "refinements"},
    "helpfulness": {"contexts", "purposes", "refinements"},
}


def test_dead_slot_probe():
    """Standing regression (reviewer meta-criterion, prereg addendum 3,
    round-3 correction): independent ground truth for the per-behavior
    masking. (a) current_mask must equal the PINNED dead sets — a mutation
    of current_mask fails here, not silently in census; (b) re-grouping
    under the PINNED sets must reproduce census's CURRENT verdicts; (c) the
    vector's slot inventory is pinned so a new slot forces a reviewed
    update. Guards the per-behavior dead-slot defect class (review rounds
    2-3); the round-2 status/sort-sentinel classes were removed from the
    vector outright rather than masked."""
    import relevance_by_act as RBA
    # (c) slot inventory pin — arity check on a dependency-free vector call
    probe = SC.vector("probe_node", {}, {}, {}, {}, {})
    assert len(probe) == len(SLOT_INVENTORY), (
        "vector arity changed — update SLOT_INVENTORY and DEAD_SLOTS_PINNED "
        "in the same reviewed commit (Arc1-e addendum 3 handshake)")
    mods = json.load(open(os.path.join(HERE, "modules_contract_v18.json")))["modules"]
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    sig, ap, pa, ctx = SC.load_layers()
    asorts = RBA.arg_sorts()
    rep = SC.census("modules_contract_v18.json")
    for slug, m in mods.items():
        pinned_dead = {SLOT_INDEX[s] for s in DEAD_SLOTS_PINNED[slug]}
        # (a) current_mask equals the pinned ground truth
        assert SC.current_mask(m) == pinned_dead, (
            f"{slug}: current_mask {SC.current_mask(m)} != pinned "
            f"{pinned_dead} — update the pin deliberately if declarations "
            "changed")
        # (b) verdicts re-derived under the PINNED mask equal census's
        _, rel = RBA.relevance(m, br, corpus)
        eng = set(rel)
        t = SC.truth_all(slug)
        groups = {}
        keys = {}
        for n in t:
            key = SC.masked(SC.vector(n, corpus, br, sig, ap, pa, None, asorts),
                            pinned_dead)
            keys[n] = key
            groups.setdefault(key, []).append(n)
        for n, r in rep[slug].items():
            twins = [mm for mm in groups[keys[n]]
                     if mm != n and ((t[mm] == "relevant") == (mm in eng))
                     and t[mm] != t[n]]
            derived = "UNSAT" if twins else "SEPARABLE"
            assert derived == r["status"], (
                f"{slug}::{n}: pinned-mask verdict {derived} != census "
                f"{r['status']}")


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
