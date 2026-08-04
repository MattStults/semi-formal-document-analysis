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

def _fake_dossier_dir(tmp_path, dossiers):
    out = tmp_path / "dossiers"
    out.mkdir(parents=True)
    lines = []
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
