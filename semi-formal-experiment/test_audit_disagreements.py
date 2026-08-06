"""Tests for audit_disagreements.py — the disagreement-audit instrument.

RED-FIRST: written against a stub module; every test below failed for the
named reason (missing attribute / missing behaviour) before implementation.

Groups:
  1. computed discriminators on constructed fixtures (head convention,
     stem-family adjacency, join-fanout degenerate flag, atom_channel_zero,
     exact-name intersection, distance-to-cut, channel shares);
  2. dossier generation on a constructed mini-corpus: byte determinism,
     index coverage, unmapped-FN handling, per-dossier facts;
  3. validator violation classes, including the dossier-consistency rules;
  4. anti-cheat: the module is in test_no_reference_leak.FORBIDDEN, so no
     query module can ever import it.
"""
from __future__ import annotations

import json
import os

import pytest

import audit_disagreements as AD

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------- 1. discriminators

def test_taxonomy_is_closed_and_documented():
    """Every cause carries a definition and a mechanical signature; the set
    is exactly the pre-registered thirteen."""
    expected = {
        "fn_family_absent_from_vocabulary", "fn_family_unselected",
        "fn_names_cannot_meet", "fn_kind_or_patient_discount", "fn_threshold",
        "fp_promiscuous_atom", "fp_section_prior", "fp_lexical_only",
        "fp_join_artifact", "fp_threshold_drift",
        "boundary_dispute_tool_defensible", "boundary_dispute_panel_defensible",
        "unexplained_escalate",
    }
    assert set(AD.CAUSE_TAXONOMY) == expected
    for name, spec in AD.CAUSE_TAXONOMY.items():
        assert spec["definition"].strip(), name
        assert spec["signature"].strip(), name
        assert spec["kind"] in ("FN", "FP", "either"), name


def test_head_convention_matches_head_induction_probe():
    """Right-headed compounds: last token, singularized, AFTER stripping the
    grammar notation — head_induction_probe.py's convention over stem_of."""
    assert AD.head_of("targeted_political_manipulation") == "manipulation"
    assert AD.head_of("psychological_manipulation") == "manipulation"
    # polarity prefix stripped by grammar.stem_of before heading
    assert AD.head_of("mustnot_manipulate_political_views") == "view"
    # principal chain stripped too
    assert AD.head_of("mustnot_disclose_reasoning__model_user") == "reasoning"
    # _singular: trailing s dropped, ss kept
    assert AD.head_of("third_parties_society_worlds") == "world"
    assert AD.head_of("data_access") == "access"


def test_stem_family_adjacency_finds_the_m0216_family():
    q = [{"name": "psychological_manipulation", "kind": "act", "gloss": "g"}]
    c = [{"name": "targeted_political_manipulation", "kind": "act",
          "gloss": "g", "role": ""}]
    adj = AD.stem_family_adjacency(q, c)
    assert adj == [{"query_atom": "psychological_manipulation",
                    "clause_atom": "targeted_political_manipulation",
                    "shared_head": "manipulation"}]


def test_stem_family_adjacency_excludes_exact_matches_and_orphans():
    q = [{"name": "human_safety", "kind": "value", "gloss": "g"},
         {"name": "data_access", "kind": "act", "gloss": "g"}]
    c = [{"name": "human_safety", "kind": "value", "gloss": "g"},   # exact
         {"name": "political_content", "kind": "entity", "gloss": "g"}]
    # exact matches belong to exact_name_intersection, never to adjacency;
    # atoms with no shared head produce nothing.
    assert AD.stem_family_adjacency(q, c) == []


def test_join_fanout_degenerate_flag():
    ok = AD.join_fanout(3, "a normal passage quote")
    assert ok == {"n_mapped_clauses": 3, "degenerate": False,
                  "quote_len": len("a normal passage quote")}
    bad = AD.join_fanout(28, '!!! meta "Commentary"')
    assert bad["degenerate"] is True and bad["n_mapped_clauses"] == 28
    assert bad["quote_len"] == len('!!! meta "Commentary"')
    # boundary: exactly 5 is NOT degenerate; 6 is
    assert AD.join_fanout(5, "q")["degenerate"] is False
    assert AD.join_fanout(6, "q")["degenerate"] is True


def _explain(atom=0.0, lex=0.1, section=0.2, matched=()):
    ch = {"lex": lex, "atom": atom, "kind": 0.0, "section": section}
    raw = sum(ch.values())
    return {"channels": ch,
            "channel_share": {k: (v / raw if raw else 0.0)
                              for k, v in ch.items()},
            "matched_atoms": list(matched)}


def test_discriminators_atom_channel_zero_and_intersection():
    q = [{"name": "psychological_manipulation", "kind": "act", "gloss": "g"}]
    c = [{"name": "targeted_political_manipulation", "kind": "act",
          "gloss": "g", "role": "consequent"}]
    d = AD.discriminators(q, c, _explain(atom=0.0), n_mapped=1,
                          quote="quote", cut=0.4, max_norm=0.164)
    assert d["atom_channel_zero"] is True
    assert d["exact_name_intersection"] == []
    assert d["stem_family_adjacency"][0]["shared_head"] == "manipulation"
    assert d["distance_to_cut"] == pytest.approx(0.164 - 0.4)
    assert d["join_fanout"]["n_mapped_clauses"] == 1
    assert d["channel_shares"]["atom"] == 0.0


def test_discriminators_exact_match_side():
    q = [{"name": "human_safety", "kind": "value", "gloss": "g"}]
    c = [{"name": "human_safety", "kind": "value", "gloss": "g", "role": ""}]
    d = AD.discriminators(q, c, _explain(atom=0.9), n_mapped=2,
                          quote="q", cut=0.3, max_norm=0.8)
    assert d["atom_channel_zero"] is False
    assert d["exact_name_intersection"] == ["human_safety"]
    assert d["stem_family_adjacency"] == []
    assert d["distance_to_cut"] == pytest.approx(0.5)


# ------------------------------------- 2. dossier generation, mini-corpus

_JUDGES = ("ja", "jb", "jc")


def _mini_world():
    """Constructed corpus with one guaranteed FN, two guaranteed FPs (one via
    a degenerate 7-clause join), and one unmapped FN."""
    import relevance as R

    def row(cid, quote):
        return {"id": cid, "quote": quote, "marked_span": None,
                "locator": f"spec > {cid}", "section_path": ["S", cid[:2]]}

    clauses = [row("c_top", "Safety commentary marker: the assistant must "
                            "protect human safety from harm."),
               row("c_zero", "Zzz qqq unrelatedwords.")]
    for i in range(6):
        clauses.append(row(f"c_fan{i}",
                           f"Another commentary marker note number {i}."))

    ann = {"c_top": [{"name": "human_safety", "kind": "value",
                      "gloss": "protection of people from harm",
                      "role": "consequent"}]}
    idx = R.RelevanceIndex(clauses, ann)

    qatoms = [{"name": "human_safety", "kind": "value",
               "gloss": "protection of people from harm"},
              {"name": "psychological_manipulation", "kind": "act",
               "gloss": "manipulating people"}]
    beh = R.Behaviour(slug="harm", name="harm",
                      definition="avoid safety harms to third parties",
                      atoms=qatoms)

    def passage(pid, quote, score):
        per = {_JUDGES[0]: min(score, 2),
               _JUDGES[1]: min(max(score - 2, 0), 2),
               _JUDGES[2]: min(max(score - 4, 0), 2)}
        return {"id": pid, "quote": quote, "score": score, "verdicts": per}

    panel = {"harm": {"slug": "harm", "coverage": {"openai": {"passages": [
        passage("#sec ¶1", clauses[1]["quote"], 6),          # FN -> c_zero
        passage("#sec ¶2", clauses[0]["quote"], 1),          # FP -> c_top
        passage("#meta ¶1", "commentary marker", 0),         # FP, fanout 7
        passage("#gone ¶1", "text absent from every clause", 6),  # unmapped FN
    ]}}}}
    return idx, {"harm": beh}, panel, clauses, {k: list(v) for k, v in ann.items()}


def _generate(tmp_path, sub):
    idx, behs, panel, clauses, ann = _mini_world()
    out = str(tmp_path / sub)
    recs = AD.generate_dossiers(idx, behs, panel, clauses, ann, out,
                                config_tag="mini")
    return out, recs


def test_generation_covers_every_disagreement_and_index_agrees(tmp_path):
    out, recs = _generate(tmp_path, "a")
    kinds = sorted(r["kind"] for r in recs)
    assert kinds == ["FN", "FN", "FP", "FP"]
    idx_lines = [json.loads(l) for l in
                 open(os.path.join(out, "index.jsonl"))]
    assert sorted(r["dossier_id"] for r in idx_lines) == \
        sorted(r["dossier_id"] for r in recs)
    for r in idx_lines:
        assert os.path.exists(os.path.join(out, r["file"]))


def test_generation_is_byte_deterministic(tmp_path):
    out1, _ = _generate(tmp_path, "a")
    out2, _ = _generate(tmp_path, "b")
    files1 = sorted(os.listdir(out1))
    assert files1 == sorted(os.listdir(out2))
    for f in files1:
        b1 = open(os.path.join(out1, f), "rb").read()
        b2 = open(os.path.join(out2, f), "rb").read()
        assert b1 == b2, f
    # no wall clock anywhere
    for f in files1:
        assert b"timestamp" not in open(os.path.join(out1, f), "rb").read()


def _dossier_by_pid(out):
    got = {}
    for l in open(os.path.join(out, "index.jsonl")):
        r = json.loads(l)
        d = json.load(open(os.path.join(out, r["file"])))
        got[d["passage"]["id"]] = d
    return got


def test_dossier_facts_fn_fp_and_degenerate_join(tmp_path):
    out, _ = _generate(tmp_path, "a")
    by_pid = _dossier_by_pid(out)

    fn = by_pid["#sec ¶1"]
    assert fn["kind"] == "FN" and fn["passage"]["panel_score"] == 6
    assert set(fn["passage"]["verdicts"]) == set(_JUDGES)
    assert fn["max_clause"]["clause_id"] == "c_zero"
    assert fn["discriminators"]["atom_channel_zero"] is True
    assert fn["discriminators"]["distance_to_cut"] < 0

    fp = by_pid["#sec ¶2"]
    assert fp["kind"] == "FP"
    assert fp["max_clause"]["clause_id"] == "c_top"
    assert fp["discriminators"]["exact_name_intersection"] == ["human_safety"]
    assert fp["discriminators"]["atom_channel_zero"] is False
    assert fp["discriminators"]["distance_to_cut"] >= 0
    # the clause's atoms carry role through to the dossier
    assert fp["max_clause"]["atoms"][0]["role"] == "consequent"
    assert [a["name"] for a in fp["query_atoms"]] == \
        ["human_safety", "psychological_manipulation"]

    fan = by_pid["#meta ¶1"]
    assert fan["kind"] == "FP"
    jf = fan["discriminators"]["join_fanout"]
    assert jf["n_mapped_clauses"] == 7 and jf["degenerate"] is True
    assert jf["quote_len"] == len("commentary marker")
    assert len(fan["mapped_clauses"]) == 7
    assert fan["max_clause"]["clause_id"] == "c_top"


def test_unmapped_fn_dossier_has_null_clause_facts(tmp_path):
    out, _ = _generate(tmp_path, "a")
    d = _dossier_by_pid(out)["#gone ¶1"]
    assert d["kind"] == "FN"
    assert d["mapped_clauses"] == [] and d["max_clause"] is None
    assert d["discriminators"]["join_fanout"]["n_mapped_clauses"] == 0


# --------------------------------------------------------- 3. the validator

def _fake_dossier_dir(tmp_path, dossiers, header=True):
    out = tmp_path / "dossiers"
    out.mkdir(parents=True)
    lines = []
    if header:
        # every census dir carries a config-identity header (F2 / item 0c)
        lines.append(json.dumps(
            {"record": "config_identity", "config_tag": "fake",
             "inputs": {"annotations": None, "behaviour_atoms": None,
                        "overlay": None, "thresholds": None},
             "threshold_rule": "otsu", "join_version": None},
            sort_keys=True))
    for d in dossiers:
        fname = d["dossier_id"] + ".json"
        json.dump(d, open(out / fname, "w"))
        lines.append(json.dumps({"dossier_id": d["dossier_id"],
                                 "kind": d["kind"], "file": fname}))
    (out / "index.jsonl").write_text("\n".join(lines) + "\n")
    return str(out)


def _dossier(did, kind, *, fanout=1, degenerate=False, atom_zero=True,
             inter=(), adj=(), dist=-0.3,
             shares=(0.5, 0.0, 0.5)):   # (lex, atom, section)
    lex, atom, section = shares
    return {"dossier_id": did, "kind": kind,
            "discriminators": {
                "atom_channel_zero": atom_zero,
                "exact_name_intersection": list(inter),
                "stem_family_adjacency": list(adj),
                "join_fanout": {"n_mapped_clauses": fanout,
                                "degenerate": degenerate, "quote_len": 10},
                "distance_to_cut": dist,
                "channel_shares": {"lex": lex, "atom": atom,
                                   "kind": 0.0, "section": section}}}


_ADJ = [{"query_atom": "a_x", "clause_atom": "b_x", "shared_head": "x"}]


def _verdict(did, cause, side="panel", note="n", **kw):
    return {"dossier_id": did, "cause": cause, "side": side, "note": note, **kw}


def test_validator_accepts_a_clean_file(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [
        _dossier("d1", "FN", adj=_ADJ),
        _dossier("d2", "FP", fanout=9, degenerate=True, atom_zero=False,
                 inter=["human_safety"], dist=0.05),
    ])
    rep = AD.validate([
        _verdict("d1", "fn_names_cannot_meet"),
        _verdict("d2", "fp_join_artifact", side="panel"),
    ], dd)
    assert rep["ok"] is True and rep["violations"] == []


@pytest.mark.parametrize("verdicts,needle", [
    # coverage: missing dossier
    ([_verdict("d1", "fn_names_cannot_meet")], "missing"),
    # coverage: duplicate
    ([_verdict("d1", "fn_names_cannot_meet"),
      _verdict("d1", "fn_names_cannot_meet"),
      _verdict("d2", "fp_promiscuous_atom")], "duplicate"),
    # coverage: unknown id
    ([_verdict("d1", "fn_names_cannot_meet"),
      _verdict("d2", "fp_promiscuous_atom"),
      _verdict("dX", "unexplained_escalate")], "unknown"),
    # closed cause vocabulary
    ([_verdict("d1", "fn_bad_cause"),
      _verdict("d2", "fp_promiscuous_atom")], "cause"),
    # closed side vocabulary
    ([_verdict("d1", "fn_names_cannot_meet", side="referee"),
      _verdict("d2", "fp_promiscuous_atom")], "side"),
    # kind mismatch: fp_ cause on an FN dossier
    ([_verdict("d1", "fp_lexical_only"),
      _verdict("d2", "fp_promiscuous_atom")], "FN"),
])
def test_validator_violation_classes(tmp_path, verdicts, needle):
    dd = _fake_dossier_dir(tmp_path, [
        _dossier("d1", "FN", adj=_ADJ),
        _dossier("d2", "FP", atom_zero=False, inter=["human_safety"]),
    ])
    rep = AD.validate(verdicts, dd)
    assert rep["ok"] is False
    assert any(needle in v for v in rep["violations"]), rep["violations"]


def test_consistency_fp_join_artifact_requires_fanout_over_5(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [_dossier("d2", "FP", fanout=3,
                                               atom_zero=False)])
    rep = AD.validate([_verdict("d2", "fp_join_artifact")], dd)
    assert rep["ok"] is False
    assert any("join_fanout" in v for v in rep["violations"])


def test_consistency_fn_family_unselected_needs_adjacency_or_sweep(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [_dossier("d1", "FN", adj=())])
    rep = AD.validate([_verdict("d1", "fn_family_unselected")], dd)
    assert rep["ok"] is False
    assert any("fn_family_unselected" in v for v in rep["violations"])
    # sweep-core evidence in the verdict satisfies the rule
    rep2 = AD.validate([_verdict("d1", "fn_family_unselected",
                                 sweep_core_evidence=["manipulation_family"])],
                       dd)
    assert rep2["ok"] is True
    # and adjacency alone satisfies it too
    dd2 = _fake_dossier_dir(tmp_path / "x", [_dossier("d1", "FN", adj=_ADJ)])
    rep3 = AD.validate([_verdict("d1", "fn_family_unselected")], dd2)
    assert rep3["ok"] is True


def test_consistency_fn_names_cannot_meet_needs_dead_atom_channel(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [
        _dossier("d1", "FN", atom_zero=False, inter=["human_safety"])])
    rep = AD.validate([_verdict("d1", "fn_names_cannot_meet")], dd)
    assert rep["ok"] is False


def test_consistency_family_absent_excludes_adjacency(tmp_path):
    # adjacency nonempty means a family member IS in the vocabulary
    dd = _fake_dossier_dir(tmp_path, [_dossier("d1", "FN", adj=_ADJ)])
    rep = AD.validate([_verdict("d1", "fn_family_absent_from_vocabulary")], dd)
    assert rep["ok"] is False


def test_consistency_threshold_causes_need_near_cut(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [
        _dossier("d1", "FN", dist=-0.5, adj=_ADJ),
        _dossier("d2", "FP", dist=0.6, atom_zero=False, inter=["x"])])
    rep = AD.validate([_verdict("d1", "fn_threshold"),
                       _verdict("d2", "fp_threshold_drift")], dd)
    assert rep["ok"] is False
    assert sum("distance_to_cut" in v for v in rep["violations"]) == 2


def test_consistency_section_prior_and_lexical_only(tmp_path):
    # lex-dominant dossier: section_prior refused, lexical_only fine
    dd = _fake_dossier_dir(tmp_path, [
        _dossier("d2", "FP", shares=(0.8, 0.0, 0.2))])
    assert AD.validate([_verdict("d2", "fp_section_prior")], dd)["ok"] is False
    assert AD.validate([_verdict("d2", "fp_lexical_only")], dd)["ok"] is True
    # section-dominant: the reverse
    dd2 = _fake_dossier_dir(tmp_path / "x", [
        _dossier("d2", "FP", shares=(0.2, 0.0, 0.8))])
    assert AD.validate([_verdict("d2", "fp_section_prior")], dd2)["ok"] is True
    assert AD.validate([_verdict("d2", "fp_lexical_only")], dd2)["ok"] is False


def test_consistency_boundary_side_and_escalation_note(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [_dossier("d1", "FN", adj=_ADJ),
                                      _dossier("d2", "FP", atom_zero=False)])
    rep = AD.validate([
        _verdict("d1", "boundary_dispute_tool_defensible", side="panel"),
        _verdict("d2", "unexplained_escalate", note=""),
    ], dd)
    assert rep["ok"] is False
    assert any("side" in v for v in rep["violations"])
    assert any("note" in v for v in rep["violations"])


def test_consistency_unmapped_dossier_only_escalates(tmp_path):
    dd = _fake_dossier_dir(tmp_path, [_dossier("d1", "FN", fanout=0)])
    rep = AD.validate([_verdict("d1", "fn_threshold")], dd)
    assert rep["ok"] is False
    assert any("unmapped" in v for v in rep["violations"])
    rep2 = AD.validate([_verdict("d1", "unexplained_escalate",
                                 note="segmentation gap")], dd)
    assert rep2["ok"] is True


# ------------------------------------------------------------ 4. anti-cheat

def test_module_is_in_the_forbidden_set():
    """audit_disagreements holds panel verdicts and tool scores side by side
    — the same launderable pairing as diagnose_disagreement — so the static
    anti-cheat scan must refuse any query module that names it."""
    import test_no_reference_leak as guard
    assert "audit_disagreements" in guard.FORBIDDEN


# ------------------- 5. config identity header + overlay/thresholds (0c)

def _tmp_input(tmp_path, name, obj):
    p = tmp_path / name
    json.dump(obj, open(p, "w"))
    return str(p)


def test_config_identity_header_shape_and_nulls(tmp_path):
    """The header carries FULL config identity in snapshot.py's exact key
    shape: input shas, explicit nulls for absent overlay/thresholds, the
    threshold rule, a join_version placeholder (F12: join_version belongs
    to CENSUS identity), and pricing_version only when an overlay is
    active."""
    import threshold as T
    ann = _tmp_input(tmp_path, "annotations_x.json", {"clauses": []})
    atoms = _tmp_input(tmp_path, "behavior_atoms_y.json", {})
    ident = AD.config_identity(ann, atoms)
    assert ident["record"] == "config_identity"
    assert ident["config_tag"] == "x__y"
    ins = ident["inputs"]
    assert set(ins) == {"annotations", "behaviour_atoms", "overlay",
                        "thresholds"}
    for key in ("annotations", "behaviour_atoms"):
        assert set(ins[key]) == {"path", "sha256"}
        assert len(ins[key]["sha256"]) == 64
    assert ins["overlay"] is None and ins["thresholds"] is None
    assert ident["threshold_rule"] == T.PREFERRED
    assert ident["join_version"] is None
    assert "pricing_version" not in ident

    ov = _tmp_input(tmp_path, "ov.json", {"edges": []})
    thr = _tmp_input(tmp_path, "thr.json", {"thresholds": {}})
    import containment
    ident2 = AD.config_identity(ann, atoms, overlay_path=ov,
                                thresholds_path=thr)
    assert ident2["inputs"]["overlay"]["path"] == "ov.json"
    assert ident2["inputs"]["thresholds"]["path"] == "thr.json"
    assert ident2["pricing_version"] == containment.PRICING_VERSION


def test_generate_writes_header_first_and_stays_deterministic(tmp_path):
    idx, behs, panel, clauses, ann = _mini_world()
    header = {"record": "config_identity", "config_tag": "mini",
              "inputs": {"annotations": None, "behaviour_atoms": None,
                         "overlay": None, "thresholds": None},
              "threshold_rule": "otsu", "join_version": None}
    for sub in ("a", "b"):
        AD.generate_dossiers(idx, behs, panel, clauses, ann,
                             str(tmp_path / sub), config_tag="mini",
                             header=header)
    ia = open(tmp_path / "a" / "index.jsonl", "rb").read()
    ib = open(tmp_path / "b" / "index.jsonl", "rb").read()
    assert ia == ib
    first = json.loads(ia.decode().splitlines()[0])
    assert first["record"] == "config_identity"


def test_overlay_changes_scores_and_header_identity(tmp_path):
    """The 2026-08-03 dossier lesson: a plain-index rebuild of an overlay
    config silently contradicts frozen scores. With --overlay threaded to
    index construction, the same census inputs produce different
    max-clause pricing / distance_to_cut, and the header identity differs
    (overlay sha + pricing_version)."""
    import containment
    idx, behs, panel, clauses, ann = _mini_world()
    over = containment.ContainmentIndex(
        clauses, {k: list(v) for k, v in ann.items()},
        edges=[("psychological_manipulation", "human_safety")])
    out_plain = str(tmp_path / "plain")
    out_over = str(tmp_path / "over")
    AD.generate_dossiers(idx, behs, panel, clauses, ann, out_plain,
                         config_tag="mini")
    AD.generate_dossiers(over, behs, panel, clauses, ann, out_over,
                         config_tag="mini")

    def by_pid(out):
        got = {}
        for l in open(os.path.join(out, "index.jsonl")):
            r = json.loads(l)
            if "dossier_id" not in r:
                continue
            d = json.load(open(os.path.join(out, r["file"])))
            got[d["passage"]["id"]] = d
        return got

    p, o = by_pid(out_plain), by_pid(out_over)
    fp = "#sec ¶2"    # maps to c_top, where the subsumption credit lands
    assert o[fp]["max_clause"]["raw"] > p[fp]["max_clause"]["raw"], \
        "the overlay's subsumption credit must reprice the max clause"
    assert o[fp]["discriminators"]["distance_to_cut"] != \
        p[fp]["discriminators"]["distance_to_cut"]


def test_frozen_thresholds_cut_source_recorded_per_behaviour(tmp_path):
    """--thresholds mirrors snapshot.py: a behaviour named in the artifact
    takes its cut FROM the artifact (cut_source frozen_artifact); one
    absent falls back to the rule (rule_fallback); without the flag no
    cut_source key appears (old shape preserved)."""
    idx, behs, panel, clauses, ann = _mini_world()
    out0 = str(tmp_path / "none")
    AD.generate_dossiers(idx, behs, panel, clauses, ann, out0,
                         config_tag="mini")
    d0 = json.load(open(os.path.join(out0, "harm__" +
                                     AD._sanitize("#sec ¶2") + ".json")))
    assert "cut_source" not in d0

    out1 = str(tmp_path / "frozen")
    AD.generate_dossiers(idx, behs, panel, clauses, ann, out1,
                         config_tag="mini", frozen_cuts={"harm": 0.123456})
    d1 = json.load(open(os.path.join(out1, "harm__" +
                                     AD._sanitize("#sec ¶2") + ".json")))
    assert d1["cut"] == 0.123456
    assert d1["cut_source"] == "frozen_artifact"

    out2 = str(tmp_path / "fallback")
    AD.generate_dossiers(idx, behs, panel, clauses, ann, out2,
                         config_tag="mini", frozen_cuts={"other-beh": 0.5})
    d2 = json.load(open(os.path.join(out2, "harm__" +
                                     AD._sanitize("#sec ¶2") + ".json")))
    assert d2["cut"] == d0["cut"]
    assert d2["cut_source"] == "rule_fallback"


def test_validate_refuses_a_headerless_census_dir(tmp_path):
    """F2: a census dir whose index.jsonl carries no config-identity header
    cannot prove WHICH configuration it audited — validate refuses."""
    dd = _fake_dossier_dir(tmp_path, [_dossier("d1", "FN", adj=_ADJ)],
                           header=False)
    rep = AD.validate([_verdict("d1", "fn_names_cannot_meet")], dd)
    assert rep["ok"] is False
    assert any("header" in v for v in rep["violations"]), rep["violations"]


def test_cli_dossiers_accepts_overlay_and_thresholds_flags(capsys):
    import sys as _sys
    old = _sys.argv
    try:
        _sys.argv = ["audit_disagreements.py", "dossiers", "--help"]
        with pytest.raises(SystemExit) as e:
            AD.main()
        assert e.value.code == 0
    finally:
        _sys.argv = old
    out = capsys.readouterr().out
    assert "--overlay" in out and "--thresholds" in out


# ------------- 6. pinning the join variant in census identity (0c / F12)

def test_config_identity_records_the_variant_set_choice(tmp_path):
    """F12 puts join identity in CENSUS identity; the variant set is the
    other half of that identity. `mixed_variants` is recorded as an
    EXPLICIT value — None when unstated (the legacy shape), the bool
    actually in force otherwise — never a missing key, exactly the way
    snapshot.py records an absent overlay."""
    import inventory
    ann = _tmp_input(tmp_path, "annotations_x.json", {"clauses": []})
    atoms = _tmp_input(tmp_path, "behavior_atoms_y.json", {})

    base = AD.config_identity(ann, atoms)
    assert "mixed_variants" in base, "the key must exist even when unstated"
    assert base["mixed_variants"] is None
    assert base["join_version"] is None

    pinned = AD.config_identity(ann, atoms,
                               join_version=inventory.JOIN_VERSION_V2,
                               mixed_variants=False)
    assert pinned["join_version"] == inventory.JOIN_VERSION_V2
    assert pinned["mixed_variants"] is False

    opted_in = AD.config_identity(ann, atoms,
                                  join_version=inventory.JOIN_VERSION_V2,
                                  mixed_variants=True)
    assert opted_in["mixed_variants"] is True


def test_generate_dossiers_scores_under_the_join_it_names(tmp_path):
    """A recorded join_version that did not drive the join would be a lie in
    the header. The mini world's fan-out FP passage ('commentary marker', a
    proper substring of seven clauses and of nothing else) is exactly what
    v2's structural arm refuses: under v1 it is a dossier, under v2 the
    passage joins to nothing, the disagreement disappears, and every other
    dossier survives. Constructed frozen input; subset checks only."""
    idx, behs, panel, clauses, ann = _mini_world()
    fanout = "harm__" + AD._sanitize("#meta ¶1")
    r1 = AD.generate_dossiers(idx, behs, panel, clauses, ann,
                              str(tmp_path / "v1"), config_tag="mini",
                              join_version=1)
    r2 = AD.generate_dossiers(idx, behs, panel, clauses, ann,
                              str(tmp_path / "v2"), config_tag="mini",
                              join_version=2)
    ids1 = {r["dossier_id"] for r in r1}
    ids2 = {r["dossier_id"] for r in r2}
    assert fanout in ids1, "v1 keeps the degenerate fan-out disagreement"
    assert fanout not in ids2, "v2's structural arm refuses that quote"
    assert ids2 < ids1


def test_mixed_variants_is_opt_in_and_v2_only(tmp_path):
    """The mixed variant set is a v2-only lever (inventory.match_passage_v2,
    default flipped to False in 68b036d). Asking for it under v1 would be a
    silent no-op that the header would then MISreport — refuse instead."""
    idx, behs, panel, clauses, ann = _mini_world()
    with pytest.raises(ValueError) as e:
        AD.generate_dossiers(idx, behs, panel, clauses, ann,
                             str(tmp_path / "bad"), config_tag="mini",
                             join_version=1, mixed_variants=True)
    assert "mixed_variants" in str(e.value)
    assert not os.path.exists(tmp_path / "bad" / "index.jsonl")


def test_cli_pins_the_join_explicitly_and_defaults_to_the_measured_state():
    """S8 must be able to pin its join variant on the entry point rather
    than inherit one. The flags exist, the default is the measured state
    (v1, uniform variants), and both are always explicit values that reach
    the header."""
    import inventory
    ap = AD._parser()
    d = ap.parse_args(["dossiers"])
    assert d.join_version == inventory.JOIN_VERSION_V1
    assert d.mixed_variants is False
    p = ap.parse_args(["dossiers", "--join-version", "2", "--mixed-variants"])
    assert p.join_version == inventory.JOIN_VERSION_V2
    assert p.mixed_variants is True
    with pytest.raises(SystemExit):
        ap.parse_args(["dossiers", "--join-version", "3"])
