"""Targeted tests for shape_partition.py — the mechanical Shape-A/Shape-B
enumerator.

DISCIPLINE. No test pins an exact count of a live artifact (the anti-rule
that has bitten this repo twice). Live assertions are SUBSET checks against
a small frozen expectation; exact counts are asserted only over synthetic
fixtures this file owns.
"""
from __future__ import annotations

import json
import os
import re

import pytest

import containment
import grammar
import shape_partition as sp

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------ the join key

def test_join_key_is_dechain_not_stem():
    """The join key must strip the principal chain and KEEP polarity.

    `grammar.stem_of` strips polarity too and would merge `must_x` with
    `mustnot_x` (containment.py:141). A sibling design made exactly this
    error; this test is the record that the two functions differ and that
    this module chose the polarity-preserving one.
    """
    name = "mustnot_generate_disallowed_content__model_third_party"
    assert sp.join_key(name) == "mustnot_generate_disallowed_content"
    assert sp.stem_key(name) == "generate_disallowed_content"
    assert sp.join_key(name) == containment.dechain_name(name)
    assert sp.stem_key(name) == grammar.stem_of(name)
    # the merge the wrong key would perform
    assert sp.stem_key("must_x") == sp.stem_key("mustnot_x")
    assert sp.join_key("must_x") != sp.join_key("mustnot_x")
    # identity on a chain-free, polarity-free name
    assert sp.join_key("psychological_manipulation") == \
        "psychological_manipulation"


# ------------------------------------------------- classification, in vitro

def _index(queries):
    return sp.query_index_from_mapping(queries)


def test_classify_is_shape_b_when_an_atom_is_in_some_query():
    idx = _index({"beh_one": ["positive_user_intent"], "beh_two": ["other"]})
    rec = sp.classify("cX", [{"name": "positive_user_intent",
                              "kind": "situation"},
                             {"name": "unrelated_thing", "kind": "value"}],
                      idx)
    assert rec["shape"] == "shape_b"
    hit = [a for a in rec["atoms"] if a["name"] == "positive_user_intent"][0]
    assert hit["in_queries"] == ["beh_one"]
    assert rec["divergent_under_stem_of"] is False


def test_classify_is_shape_a_when_no_atom_is_in_any_query():
    idx = _index({"beh_one": ["something_else"]})
    rec = sp.classify("cX", [{"name": "human_control_of_ai", "kind": "value"}],
                      idx)
    assert rec["shape"] == "shape_a"
    assert rec["atoms"][0]["in_queries"] == []
    assert rec["atoms"][0]["polarity_variants"] == []


def test_classify_reaches_through_a_principal_chain():
    """A chained clause-side atom must join to the un-chained query name."""
    idx = _index({"beh_one": ["should_redirect_to_applicable_help"]})
    rec = sp.classify(
        "cX", [{"name": "should_redirect_to_applicable_help__model_user",
                "kind": "act"}], idx)
    assert rec["shape"] == "shape_b"
    assert rec["atoms"][0]["join_key"] == "should_redirect_to_applicable_help"


def test_polarity_variant_is_its_own_state_and_is_not_shape_b():
    """THE THIRD STATE. Same stem, different polarity/modality: the query
    cannot meet the atom, so it is NOT shape_b — but it is the one place
    where the wrong join key would have said it was."""
    idx = _index({"beh_one": ["shouldnot_generate_disallowed_content"]})
    rec = sp.classify(
        "cX", [{"name": "mustnot_generate_disallowed_content__model_third_party",
                "kind": "act"}], idx)
    assert rec["shape"] == "shape_a_polarity_variant"
    assert rec["atoms"][0]["in_queries"] == []
    assert rec["atoms"][0]["polarity_variants"] == [
        {"behaviour": "beh_one",
         "query_atom": "shouldnot_generate_disallowed_content"}]
    assert rec["divergent_under_stem_of"] is True
    assert rec["shape_under_stem_key"] == "shape_b"


def test_classification_never_reads_a_panel_value():
    """`classify` takes atoms and a query index and nothing else — no
    census record, no dossier, no behaviour of origin. A panel value has no
    argument to arrive through."""
    import inspect
    params = list(inspect.signature(sp.classify).parameters)
    assert params == ["clause_id", "atoms", "index"]
    idx = _index({"beh_one": ["a"]})
    rec = sp.classify("cX", [{"name": "a", "kind": "act"}], idx)
    assert set(rec) == set(sp.CLAUSE_FIELDS)
    for atom in rec["atoms"]:
        assert set(atom) == set(sp.ATOM_FIELDS)


def test_shape_vocabulary_is_closed_and_an_unknown_shape_is_refused():
    assert sp.SHAPES == ("shape_a", "shape_a_polarity_variant", "shape_b")
    art = {"clauses": [{"clause_id": "cX", "shape": "shape_c", "reason": "r",
                        "n_atoms": 0, "atoms": [],
                        "divergent_under_stem_of": False,
                        "shape_under_stem_key": "shape_a"}]}
    errs = sp.check_payload(art["clauses"])
    assert any("outside the closed set" in e for e in errs)


def test_a_panel_field_in_the_classification_payload_is_refused():
    """The classification payload is banned-key scanned: a census or panel
    field smuggled into a clause record must be a refusal, not a shrug."""
    rows = [{"clause_id": "cX", "shape": "shape_a", "reason": "r",
             "n_atoms": 0, "atoms": [], "divergent_under_stem_of": False,
             "shape_under_stem_key": "shape_a", "panel_score": 5}]
    errs = sp.check_payload(rows)
    assert any("panel" in e for e in errs)


# ------------------------------------------------------- the live partition

@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("sp") / "shape_partition.json"
    sp.build(out_path=str(out))
    with open(out) as f:
        return str(out), json.load(f)


#: FROZEN expectation. Not a count of a live artifact — a subset the live
#: partition must contain, chosen because each is load-bearing:
#:   m0170/m0528 — atoms already in another behaviour's query (shape_b);
#:   m0015/m0030 — no atom in any query (shape_a);
#:   m0242/m0253 — the two stem/polarity collisions.
FROZEN_SHAPE_B = {"m0170", "m0528", "m0246"}
FROZEN_SHAPE_A = {"m0015", "m0030"}
FROZEN_POLARITY_VARIANT = {"m0242", "m0253"}


def test_live_partition_contains_the_frozen_subset(built):
    _, art = built
    by_shape = {}
    for row in art["clauses"]:
        by_shape.setdefault(row["shape"], set()).add(row["clause_id"])
    assert FROZEN_SHAPE_B <= by_shape.get("shape_b", set())
    assert FROZEN_SHAPE_A <= by_shape.get("shape_a", set())
    assert FROZEN_POLARITY_VARIANT <= \
        by_shape.get("shape_a_polarity_variant", set())


def test_every_target_clause_is_classified_exactly_once(built):
    _, art = built
    ids = [row["clause_id"] for row in art["clauses"]]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(art["selection"]["clause_ids"])
    assert ids == sorted(ids)


def test_provenance_shas_match_the_files_on_disk(built):
    _, art = built
    assert art["inputs"]
    for rec in art["inputs"]:
        # repo-relative, so the frozen artifact is the same bytes in every
        # checkout — an absolute path would make the sha machine-specific
        assert not os.path.isabs(rec["path"]), rec["path"]
        assert rec["sha256"] == sp.sha256_file(sp.abspath(rec["path"]))
    assert not os.path.isabs(art["selection"]["census_dir"])
    assert art["join_key"]["function"] == "containment.dechain_name"
    assert art["join_key"]["rejected"] == "grammar.stem_of"


def test_selection_discloses_that_it_is_panel_derived(built):
    _, art = built
    sel = art["selection"]
    assert sel["cause"] == "fn_family_absent_from_vocabulary"
    assert "attention" in sel["label_hygiene"].lower()
    # the census contributes IDS ONLY
    assert set(sel) <= set(sp.SELECTION_FIELDS)


def test_build_is_deterministic_and_carries_no_clock(built, tmp_path):
    path, art = built
    again = tmp_path / "again.json"
    sp.build(out_path=str(again))
    assert open(path, "rb").read() == open(again, "rb").read()
    raw = open(path).read()
    for token in ("timestamp", "generated_at", "date", "wall_clock"):
        assert token not in raw
    # no ISO date and no epoch-looking integer anywhere in the artifact
    assert not re.search(r"\b\d{4}-\d{2}-\d{2}\b", raw)
    assert not re.search(r"\b1[6-9]\d{8}\b", raw)


def test_validate_accepts_the_freshly_built_artifact(built):
    path, _ = built
    assert sp.validate(path) == []


def test_validate_refuses_a_hand_edited_shape(built, tmp_path):
    path, art = built
    tampered = json.loads(json.dumps(art))
    row = [r for r in tampered["clauses"] if r["shape"] == "shape_b"][0]
    row["shape"] = "shape_a"
    bad = tmp_path / "tampered.json"
    with open(bad, "w") as f:
        json.dump(tampered, f, sort_keys=True, indent=1)
    errs = sp.validate(str(bad))
    assert any("does not match the recomputed" in e for e in errs)


def test_validate_refuses_a_drifted_input_sha(built, tmp_path):
    path, art = built
    tampered = json.loads(json.dumps(art))
    tampered["inputs"][0]["sha256"] = "0" * 64
    bad = tmp_path / "drifted.json"
    with open(bad, "w") as f:
        json.dump(tampered, f, sort_keys=True, indent=1)
    errs = sp.validate(str(bad))
    assert any("sha256 mismatch" in e for e in errs)


def test_cli_build_then_validate_round_trips(tmp_path, capsys):
    out = tmp_path / "cli.json"
    assert sp.main(["build", "--out", str(out)]) == 0
    capsys.readouterr()
    assert sp.main(["validate", "--path", str(out)]) == 0
    assert "CLEAN" in capsys.readouterr().out
