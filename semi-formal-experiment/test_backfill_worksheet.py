"""Tests for backfill_worksheet.py — the PATIENT-BACKFILL worksheet
producer + verdict validator (the chain_audit_worksheet.py sibling).

House pattern: written RED-FIRST against a stub module; registered in
conftest._OPTIONAL; every closed vocabulary asserted (the golden-author
self-check lesson), not just names; the FORBIDDEN-token scan is exercised
on the worksheet, the verdict file, the module's own CLI/field names AND
the seat brief (briefs/backfill_author.md must be silent on scoring
machinery — it is written from the annotation conventions alone).
"""
from __future__ import annotations

import json
import os

import pytest

import backfill_worksheet as bw
import grammar

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ fixture

CLAUSES = {
    "clauses": [
        {"id": "c001", "quote": "The assistant must warn the user before "
                                "deleting user files."},
        {"id": "c002", "quote": "Avoid purple prose."},
        {"id": "c003", "quote": "The operator may restrict topics."},
    ]
}

ATOMS = [
    # chain-free polarity-marked act -> PRIMARY stratum candidate
    {"clause_id": "c001", "name": "must_warn_before_deletion",
     "kind": "act", "gloss": "warn the user first", "quote": "must warn",
     "span_id": "s1", "locator": "L1"},
    # chain-free unmarked act -> secondary stratum candidate
    {"clause_id": "c002", "name": "avoid_purple_prose",
     "kind": "act", "gloss": "style guidance", "quote": "Avoid purple",
     "span_id": "s2", "locator": "L2"},
    # already chained act -> NOT a candidate
    {"clause_id": "c001", "name": "must_delete_files__model_user",
     "kind": "act", "gloss": "the act itself", "quote": "deleting",
     "span_id": "s3", "locator": "L3"},
    # non-act kinds -> NOT candidates
    {"clause_id": "c002", "name": "purple_prose", "kind": "entity",
     "gloss": "the style", "quote": "purple prose", "span_id": "s4",
     "locator": "L4"},
    {"clause_id": "c003", "name": "topic_restriction_active",
     "kind": "situation", "gloss": "a restriction", "quote": "restrict",
     "span_id": "s5", "locator": "L5"},
    # second primary candidate, non-model actor licensable
    {"clause_id": "c003", "name": "may_restrict_topics",
     "kind": "act", "gloss": "operator restricts", "quote": "may restrict",
     "span_id": "s6", "locator": "L6"},
]


@pytest.fixture()
def built(tmp_path):
    ann = tmp_path / "ann.json"
    cls = tmp_path / "clauses.json"
    out = tmp_path / "backfill"
    ann.write_text(json.dumps({"atoms": ATOMS}))
    cls.write_text(json.dumps(CLAUSES))
    ws_path = bw.build(str(ann), str(cls), str(out))
    return str(ann), str(cls), str(out), ws_path


def _worksheet(ws_path):
    with open(ws_path) as f:
        return json.load(f)


def _write_verdict_file(out, ws_path, records):
    payload = {"worksheet_sha256": bw.sha256_file(ws_path),
               "records": records}
    vpath = os.path.join(out, bw.VERDICT_FILE_NAME)
    with open(vpath, "w") as f:
        json.dump(payload, f)
    return vpath


def _clean_records():
    return [
        {"clause_id": "c001", "name": "must_warn_before_deletion",
         "verdict": "chain_licensed", "corrected_chain": ["model", "user"],
         "license_quote": "The assistant must warn the user",
         "reason": "clause names the assistant acting and the user warned"},
        {"clause_id": "c002", "name": "avoid_purple_prose",
         "verdict": "no_chain_licensed", "corrected_chain": None,
         "license_quote": None,
         "reason": "no party named by the clause"},
        {"clause_id": "c003", "name": "may_restrict_topics",
         "verdict": "unclear", "corrected_chain": None,
         "license_quote": None,
         "reason": "actor named but no patient; leaving undetermined"},
    ]


# -------------------------------------------------------------- enumeration

def test_build_enumerates_exactly_the_chainfree_act_instances(built):
    _, _, _, ws_path = built
    rows = _worksheet(ws_path)["instances"]
    keys = {(r["clause_id"], r["name"]) for r in rows}
    assert keys == {("c001", "must_warn_before_deletion"),
                    ("c002", "avoid_purple_prose"),
                    ("c003", "may_restrict_topics")}
    # chained instances and non-act kinds are excluded
    assert ("c001", "must_delete_files__model_user") not in keys
    assert all(r["kind"] == "act" for r in rows)
    assert all(not grammar.parse_name(r["name"])["principals"]
               for r in rows)


def test_primary_stratum_is_polarity_marked_and_ordered_first(built):
    _, _, _, ws_path = built
    ws = _worksheet(ws_path)
    rows = ws["instances"]
    strata = [r["stratum"] for r in rows]
    assert set(strata) <= set(bw.STRATA)
    # every polarity-marked row precedes every unmarked row
    first_unmarked = strata.index("unmarked")
    assert all(s == "polarity_marked" for s in strata[:first_unmarked])
    assert all(s == "unmarked" for s in strata[first_unmarked:])
    # deterministic (clause_id, name) order within each stratum
    for stratum in bw.STRATA:
        sub = [(r["clause_id"], r["name"]) for r in rows
               if r["stratum"] == stratum]
        assert sub == sorted(sub)
    s = ws["summary"]
    assert s["total_instances"] == 3
    assert s["by_stratum"]["polarity_marked"]["instances"] == 2
    assert s["by_stratum"]["unmarked"]["instances"] == 1


def test_rows_carry_clause_text_and_a_closed_field_set(built):
    _, _, _, ws_path = built
    ws = _worksheet(ws_path)
    for r in ws["instances"]:
        assert set(r) == set(bw.ROW_FIELDS)
        assert r["clause_text"]
        assert r["gloss"] is not None
    # the licensing rules ride in the worksheet header, verbatim
    rules = "\n".join(ws["licensing_rules"])
    assert "A chain is written ONLY where the clause names both an actor" \
        in rules
    assert "Do not infer an affected party from the subject matter" in rules
    assert "who acts first" in rules


def test_build_is_deterministic(built, tmp_path):
    ann, cls, _, ws_path = built
    out2 = tmp_path / "again"
    ws2 = bw.build(ann, cls, str(out2))
    assert open(ws_path, "rb").read() == open(ws2, "rb").read()


def test_build_refuses_an_invented_kind(tmp_path):
    # golden-author lesson: assert every closed vocabulary, not just names
    bad = dict(ATOMS[0])
    bad["kind"] = "behavior"     # the recorded calibration failure word
    ann = tmp_path / "ann.json"
    cls = tmp_path / "clauses.json"
    ann.write_text(json.dumps({"atoms": [bad]}))
    cls.write_text(json.dumps(CLAUSES))
    with pytest.raises(bw.WorksheetError):
        bw.build(str(ann), str(cls), str(tmp_path / "o"))


def test_real_artifact_counts_match_the_registered_scope():
    """The registered scope is pinned by the FROZEN worksheet enumeration
    (the cycle artifact), not by the live annotation artifact: the live
    artifact loses chain-free candidates exactly as licensed verdicts land
    (the backfill's whole point), so a live-count pin would break on the
    cycle's own change — the stale-census-pin failure mode this repo has
    now hit twice (test_dechain's n==109; this test's original 692). The
    live artifact is instead checked for COHERENCE: every chain-free act
    candidate it still carries must lie inside the frozen scope."""
    ws_path = os.path.join(HERE, "cycles", "patient-backfill-2026-08-04",
                           "backfill", "worksheet.json")
    if not os.path.exists(ws_path):
        pytest.skip("frozen backfill worksheet not present")
    ws = json.load(open(ws_path))
    s = ws["summary"]
    assert s["total_instances"] == 692
    assert s["distinct_clauses"] == 462
    assert s["by_stratum"]["polarity_marked"] == {"instances": 505,
                                                  "distinct_clauses": 347}
    assert s["by_stratum"]["unmarked"] == {"instances": 187,
                                           "distinct_clauses": 148}
    frozen_keys = {(r["clause_id"], r["name"]) for r in ws["instances"]}
    assert len(frozen_keys) == 692
    ann = os.path.join(HERE, "annotations_ext_v1_merged.json")
    live = {(a["clause_id"], a["name"])
            for a in bw.candidates(json.load(open(ann)))}
    assert live <= frozen_keys


# --------------------------------------------------------------- validator

def test_clean_verdict_file_validates(built):
    _, _, out, ws_path = built
    vpath = _write_verdict_file(out, ws_path, _clean_records())
    assert bw.validate(ws_path, vpath) == []


def test_coverage_missing_and_duplicate_and_unknown(built):
    _, _, out, ws_path = built
    recs = _clean_records()
    vpath = _write_verdict_file(out, ws_path, recs[:2])
    assert any("no verdict" in e for e in bw.validate(ws_path, vpath))
    vpath = _write_verdict_file(out, ws_path, recs + [recs[0]])
    assert any("2 verdicts" in e for e in bw.validate(ws_path, vpath))
    stray = dict(recs[0], clause_id="c999")
    vpath = _write_verdict_file(out, ws_path, recs + [stray])
    assert any("not a worksheet instance" in e
               for e in bw.validate(ws_path, vpath))


def test_verdict_vocabulary_is_closed_and_includes_no_chain_licensed(built):
    _, _, out, ws_path = built
    assert set(bw.VERDICT_VOCAB) == {"chain_licensed", "no_chain_licensed",
                                     "unclear"}
    recs = _clean_records()
    recs[0]["verdict"] = "correct"      # chain-audit vocab, not this seat's
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("closed vocabulary" in e for e in bw.validate(ws_path, vpath))


def test_license_quote_must_be_a_substring_of_the_clause_text(built):
    _, _, out, ws_path = built
    recs = _clean_records()
    recs[0]["license_quote"] = "warns the user politely"   # not verbatim
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("substring" in e for e in bw.validate(ws_path, vpath))
    recs = _clean_records()
    recs[0]["license_quote"] = ""
    vpath = _write_verdict_file(out, ws_path, recs)
    assert bw.validate(ws_path, vpath)


def test_corrected_chain_rules(built):
    _, _, out, ws_path = built
    # length-1 addition refused outright
    recs = _clean_records()
    recs[0]["corrected_chain"] = ["user"]
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("length" in e for e in bw.validate(ws_path, vpath))
    # bare model chain refused (subsumed by the length rule, named anyway)
    recs = _clean_records()
    recs[0]["corrected_chain"] = ["model"]
    vpath = _write_verdict_file(out, ws_path, recs)
    assert bw.validate(ws_path, vpath)
    # non-principal member refused
    recs = _clean_records()
    recs[0]["corrected_chain"] = ["model", "customer"]
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("non-principal" in e for e in bw.validate(ws_path, vpath))
    # chain_licensed with a null chain refused
    recs = _clean_records()
    recs[0]["corrected_chain"] = None
    vpath = _write_verdict_file(out, ws_path, recs)
    assert bw.validate(ws_path, vpath)
    # the formatted decorated name must parse and round-trip
    recs = _clean_records()
    name = grammar.format_name("warn_before_deletion", "must",
                               recs[0]["corrected_chain"])
    assert not grammar.parse_name(name)["error"]


def test_no_chain_and_unclear_require_null_chain_and_quote(built):
    _, _, out, ws_path = built
    recs = _clean_records()
    recs[1]["corrected_chain"] = ["model", "user"]
    vpath = _write_verdict_file(out, ws_path, recs)
    assert bw.validate(ws_path, vpath)
    recs = _clean_records()
    recs[2]["license_quote"] = "The operator may restrict topics."
    vpath = _write_verdict_file(out, ws_path, recs)
    assert bw.validate(ws_path, vpath)


def test_reason_required_and_bounded(built):
    _, _, out, ws_path = built
    recs = _clean_records()
    recs[0]["reason"] = ""
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("reason" in e for e in bw.validate(ws_path, vpath))
    recs = _clean_records()
    recs[0]["reason"] = "word " * 30
    vpath = _write_verdict_file(out, ws_path, recs)
    assert any("25 words" in e for e in bw.validate(ws_path, vpath))


def test_verdict_file_binds_to_the_worksheet_sha(built):
    _, _, out, ws_path = built
    vpath = os.path.join(out, bw.VERDICT_FILE_NAME)
    with open(vpath, "w") as f:
        json.dump({"worksheet_sha256": "0" * 64,
                   "records": _clean_records()}, f)
    assert any("worksheet_sha256" in e for e in bw.validate(ws_path, vpath))


def test_stem_and_polarity_are_immutable_under_the_seat(built):
    # decoration only: the validated correction is always
    # format_name(original stem, original polarity, corrected_chain) — the
    # validator exposes the derivation so nothing else can move.
    _, _, out, ws_path = built
    row = _worksheet(ws_path)["instances"][0]
    corrected = bw.corrected_name(row, ["model", "user"])
    p = grammar.parse_name(corrected)
    assert p["stem"] == row["stem"]
    assert p["polarity"] == row["polarity"]
    assert p["principals"] == ["model", "user"]


# ------------------------------------------------------- token-scan fences

def test_forbidden_tokens_are_read_live_from_the_guard():
    toks = bw.forbidden_tokens()
    assert "load_panel" in toks and "panel_universe" in toks
    assert len(toks) >= 30


def test_worksheet_and_verdict_file_pass_the_token_scan(built):
    _, _, out, ws_path = built
    vpath = _write_verdict_file(out, ws_path, _clean_records())
    assert bw.scan_file(ws_path) == []
    assert bw.scan_file(vpath) == []


def test_module_cli_and_field_names_carry_no_forbidden_token():
    toks = bw.forbidden_tokens()
    names = list(bw.ROW_FIELDS) + list(bw.VERDICT_FIELDS) \
        + list(bw.CLI_MODES) + [bw.VERDICT_FILE_NAME, bw.WORKSHEET_NAME]
    for n in names:
        hits = [t for t in toks if t in n]
        assert not hits, (n, hits)


def test_the_seat_brief_exists_and_is_silent_on_scoring_machinery():
    """F10i fence, mechanical: the seat brief is written from the annotation
    conventions alone. It may not mention pricing, discounts, any design
    document, or anything panel-side."""
    brief = os.path.join(HERE, "briefs", "backfill_author.md")
    assert os.path.exists(brief)
    hits = bw.scan_brief(brief)
    assert hits == [], hits


def test_brief_scan_catches_a_planted_mention(tmp_path):
    p = tmp_path / "brief.md"
    p.write_text("Chains will later discount pricing for matches.")
    hits = bw.scan_brief(str(p))
    assert any("pricing" in h for h in hits)
    assert any("discount" in h for h in hits)
