"""Tests for delta.py and baseline_conflicts.py (Agent C).

All fixtures are synthetic conflicts.json documents in the frozen §3 shape.
No network call happens anywhere in this file, and one test enforces that.
"""
import json
import urllib.request

import pytest

import baseline_conflicts as bc
import delta


def doc(source, run_id, pairs, model="m"):
    return {"source": source, "model": model, "run_id": run_id,
            "conflicts": [{"pair": sorted(p),
                           "witness": {"ctx": [] if source == "baseline"
                                       else [f"ctx_{p[0]}"]},
                           "witness_prose": f"situation for {p[0]}+{p[1]}",
                           "note": "collide"} for p in pairs]}


A, B, C, D, E = "fa_a", "fa_b", "fa_c", "fa_d", "fa_e"


# ---------------------------------------------------------------- pair sets

def test_pair_set_normalizes_to_sorted_tuples():
    d = doc("tool", "r1", [[B, A]])
    assert delta.pair_set(d) == {(A, B)}


def test_pairs_compare_as_sets_regardless_of_order():
    t = doc("tool", "r1", [[A, B]])
    b = doc("baseline", "r1", [[B, A]])
    bk = delta.buckets(delta.pair_set(t), delta.pair_set(b))
    assert bk["both"] == [[A, B]]
    assert bk["tool_only"] == [] and bk["baseline_only"] == []


# ------------------------------------------------------------------ buckets

def test_three_buckets():
    t = doc("tool", "t1", [[A, B], [A, C], [C, D]])
    b = doc("baseline", "b1", [[A, B], [B, D], [D, E]])
    bk = delta.buckets(delta.pair_set(t), delta.pair_set(b))
    assert bk["both"] == [[A, B]]
    assert bk["tool_only"] == [[A, C], [C, D]]
    assert bk["baseline_only"] == [[B, D], [D, E]]


def test_buckets_partition_the_union():
    t = doc("tool", "t1", [[A, B], [A, C]])
    b = doc("baseline", "b1", [[A, B], [B, C]])
    bk = delta.buckets(delta.pair_set(t), delta.pair_set(b))
    n = sum(len(v) for v in bk.values())
    assert n == len(delta.pair_set(t) | delta.pair_set(b)) == 3


# ------------------------------------------------------------------ jaccard

def test_jaccard_identical_is_one():
    s = {(A, B), (A, C)}
    assert delta.jaccard(s, set(s)) == 1.0


def test_jaccard_disjoint_is_zero():
    assert delta.jaccard({(A, B)}, {(C, D)}) == 0.0


def test_jaccard_partial_hand_computed():
    # {AB,AC,AD} vs {AB,AC,BC}: intersection 2, union 4 -> 0.5
    x = {(A, B), (A, C), (A, D)}
    y = {(A, B), (A, C), (B, C)}
    assert delta.jaccard(x, y) == pytest.approx(0.5)


def test_jaccard_two_empty_sets_is_one():
    assert delta.jaccard(set(), set()) == 1.0


def test_jaccard_empty_vs_nonempty_is_zero():
    assert delta.jaccard(set(), {(A, B)}) == 0.0


# ----------------------------------------------------------- self-agreement

def test_self_agreement_three_identical_runs_is_one():
    runs = [doc("baseline", f"r{i}", [[A, B], [C, D]]) for i in range(3)]
    assert delta.self_agreement(runs) == 1.0


def test_self_agreement_three_disjoint_runs_is_zero():
    runs = [doc("baseline", "r1", [[A, B]]),
            doc("baseline", "r2", [[C, D]]),
            doc("baseline", "r3", [[A, C]])]
    assert delta.self_agreement(runs) == 0.0


def test_self_agreement_hand_computed_over_three_runs():
    # r1={AB,AC} r2={AB} r3={AB,AC,AD}
    # J(1,2)=1/2, J(1,3)=2/3, J(2,3)=1/3  -> mean = 0.5
    runs = [doc("baseline", "r1", [[A, B], [A, C]]),
            doc("baseline", "r2", [[A, B]]),
            doc("baseline", "r3", [[A, B], [A, C], [A, D]])]
    assert delta.self_agreement(runs) == pytest.approx(
        (0.5 + 2 / 3 + 1 / 3) / 3)


def test_self_agreement_single_run_is_none():
    assert delta.self_agreement([doc("tool", "r1", [[A, B]])]) is None


def test_self_agreement_two_runs_is_single_jaccard():
    runs = [doc("tool", "r1", [[A, B], [A, C]]),
            doc("tool", "r2", [[A, B], [A, D]])]
    assert delta.self_agreement(runs) == pytest.approx(1 / 3)


# ----------------------------------------------------------------- coverage

def test_coverage_over_42_and_reason_tally():
    ex = {"rules": [{"id": f"r{i}"} for i in range(21)],
          "unencoded": [{"focus_id": "fa_x", "reason": "no act atom"},
                        {"focus_id": "fa_y", "reason": "no act atom"},
                        {"focus_id": "fa_z", "reason": "definitional"}]}
    cov = delta.coverage(ex)
    assert cov["rules_emitted"] == 21
    assert cov["denominator"] == 42
    assert cov["coverage"] == pytest.approx(0.5)
    assert cov["unencoded_count"] == 3
    assert cov["unencoded_reasons"] == {"no act atom": 2, "definitional": 1}


def test_coverage_deduplicates_rule_ids():
    ex = {"rules": [{"id": "r1"}, {"id": "r1"}, {"id": "r2"}], "unencoded": []}
    assert delta.coverage(ex)["rules_emitted"] == 2


# ------------------------------------------------------------- compute / io

def test_compute_blob_has_every_section5_metric(tmp_path):
    tool = [doc("tool", "t1", [[A, B], [A, C]]),
            doc("tool", "t2", [[A, B], [A, D]])]
    base = [doc("baseline", "b1", [[A, B]]),
            doc("baseline", "b2", [[A, B], [B, C]]),
            doc("baseline", "b3", [[A, B]])]
    m = delta.compute(tool, base,
                      extraction={"rules": [{"id": "r"}], "unencoded": []})
    for k in ("C_tool", "C_baseline", "tool_self_agreement",
              "baseline_self_agreement", "bucket_sizes", "coverage"):
        assert k in m
    assert m["C_tool"] == 3 and m["C_baseline"] == 2
    assert m["bucket_sizes"]["both"] == 1
    md = delta.to_markdown(m)
    assert "C_tool" in md and "baseline_self_agreement" in md


def test_compute_accepts_paths(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps(doc("tool", "t1", [[A, B]])))
    m = delta.compute([str(p)], [doc("baseline", "b1", [[A, B]])])
    assert m["bucket_sizes"]["both"] == 1


def test_index_by_pair_keeps_witnesses_from_every_run():
    tool = [doc("tool", "t1", [[A, B]]), doc("tool", "t2", [[A, B]])]
    idx = delta.index_by_pair(tool)
    recs = idx[(A, B)]
    assert len(recs) == 2
    assert {r["run_id"] for r in recs} == {"t1", "t2"}
    assert recs[0]["witness"]["ctx"] == ["ctx_fa_a"]


# -------------------------------------------------- baseline_conflicts.py

def test_baseline_prompt_covers_all_62_focus_areas():
    rows = bc.load_focus_areas()
    assert len(rows) == 62
    system, user = bc.build_prompt(rows)
    for r in rows:
        assert f"[{bc.prefix_id(r['focus_id'])}]" in user
        assert r["text"] in user
    assert "which provisions in this section can conflict, and in what " \
           "situation?" in user.lower()


def test_baseline_prompt_does_not_suppress_specificity_conflicts():
    """General rule vs. carved-out exception is the characteristic real
    conflict in a defeasible spec; the prompt must not tell the baseline to
    skip it. The 'state the concrete situation' discriminator does the
    anti-padding work instead."""
    _, user = bc.build_prompt(bc.load_focus_areas())
    assert "more specific" not in user
    assert "thematically related" in user and "restates another provision" in user
    assert "state the concrete situation in which they pull apart" in user


def test_baseline_prompt_withholds_the_same_tier_resolution_rule():
    """Telling only the baseline how the Spec resolves same-tier conflicts
    would bias the comparison; whether that rule resolves a tension is an
    adjudication question, not a prompt hint."""
    system, user = bc.build_prompt(bc.load_focus_areas())
    instructions = user.split("=== BEGIN SECTION ===")[0] + system
    for phrase in ("default to inaction", "root-level principles conflict",
                   "same tier", "same-tier"):
        assert phrase not in instructions.lower()


def test_baseline_ids_match_agent_a_inventory_ids():
    import inventory
    a_ids = {r["id"] for r in inventory.load_section()}
    mine = {bc.prefix_id(r["focus_id"]) for r in bc.load_focus_areas()}
    assert mine == a_ids


def test_baseline_prompt_prefixes_digit_initial_ids():
    assert bc.prefix_id("8ep1") == "fa_8ep1"
    assert bc.prefix_id("fa_8ep1") == "fa_8ep1"


def test_parse_response_normalizes_sorts_and_zeroes_ctx():
    text = ('```json\n{"conflicts": [{"pair": ["fa_b", "fa_a"], '
            '"witness_prose": "s", "note": "n"}]}\n```')
    out, errs = bc.parse_response(text, [A, B])
    assert errs == []
    assert out[0]["pair"] == [A, B]
    assert out[0]["witness"] == {"ctx": []}


def test_parse_response_records_junk_instead_of_raising():
    out, errs = bc.parse_response("sorry, I cannot help with that", [A, B])
    assert out == [] and errs and "unparseable" in errs[0]


def test_parse_response_rejects_unknown_ids_and_dupes_and_self_pairs():
    text = json.dumps({"conflicts": [
        {"pair": [A, "fa_zzz"], "witness_prose": "s"},
        {"pair": [A, A], "witness_prose": "s"},
        {"pair": [A, B], "witness_prose": "s"},
        {"pair": [B, A], "witness_prose": "s"},
        {"pair": [A], "witness_prose": "s"}]})
    out, errs = bc.parse_response(text, [A, B])
    assert [c["pair"] for c in out] == [[A, B]]
    assert len(errs) == 4


def test_parse_response_flags_empty_prose_but_keeps_the_pair():
    text = json.dumps({"conflicts": [{"pair": [A, B], "witness_prose": ""}]})
    out, errs = bc.parse_response(text, [A, B])
    assert len(out) == 1 and any("witness_prose" in e for e in errs)


def test_baseline_doc_matches_frozen_shape():
    d = bc.conflicts_doc("m", "baseline-x-r1", [])
    assert set(d) == {"source", "model", "run_id", "conflicts"}
    assert d["source"] == "baseline"


def test_dry_run_makes_no_network_call_and_logs_k_prompts(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network call attempted in dry run")
    monkeypatch.setattr(urllib.request, "urlopen", boom)

    log = tmp_path / "prompt_log"
    written = bc.run("fable", k=3, live=False, out_dir=str(tmp_path),
                     log_dir=str(log), stamp="TEST")
    assert written == []                       # no conflicts.json without a response
    prompts = sorted(p.name for p in log.iterdir())
    assert len(prompts) == 3
    assert not list(tmp_path.glob("conflicts_*.json"))


def test_unknown_provider_is_rejected(tmp_path):
    with pytest.raises(SystemExit):
        bc.run("no-such-provider", k=1, live=False, out_dir=str(tmp_path),
               log_dir=str(tmp_path / "log"))


# ==========================================================================
# Regressions found running the chain on the first REAL extraction
# (smoke_live2/extraction_openai_gpt-oss-20b_s0-21da64d9.json, gpt-oss-20b:
#  34 atoms / 24 rules / 0 incompat / 0 exclusions, 2 rules invalid).
# Every fixture below is the shape that actually broke, not an invention.
# ==========================================================================

import os

import filter_extraction

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_EXTRACTION = os.path.join(
    HERE, "smoke_live2", "extraction_openai_gpt-oss-20b_s0-21da64d9.json")
REAL_BASELINES = [os.path.join(HERE, "smoke_live2", f"conflicts_baseline_run{i}.json")
                  for i in (1, 2, 3)]

real = pytest.mark.skipif(not os.path.exists(REAL_EXTRACTION),
                          reason="real artifacts not present")


# -- B1: coverage counted rules the emitter then threw away -----------------

def test_coverage_discounts_rejected_rules():
    """A rule that fails validation never reaches the solver, so it is not
    'encoded'. Counting it inflates coverage --- and §6's coverage stop rule
    keys on exactly that number."""
    ext = {"rules": [{"id": "fa_a"}, {"id": "fa_b"}, {"id": "fa_c"}],
           "unencoded": []}
    cov = delta.coverage(ext, rejected_rule_ids=["fa_c"])
    assert cov["rules_claimed"] == 3
    assert cov["rules_emitted"] == 2
    assert cov["rules_rejected"] == 1
    assert cov["coverage"] == pytest.approx(2 / 42)
    assert cov["coverage_claimed"] == pytest.approx(3 / 42)


def test_coverage_without_rejections_is_unchanged():
    ext = {"rules": [{"id": "fa_a"}, {"id": "fa_b"}], "unencoded": []}
    cov = delta.coverage(ext)
    assert cov["rules_emitted"] == 2 and cov["rules_rejected"] == 0
    assert cov["coverage"] == cov["coverage_claimed"] == pytest.approx(2 / 42)


@real
def test_real_extraction_effective_coverage_is_below_claimed():
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    _, rep = filter_extraction.filter_extraction(ext)
    rejected = [r["id"] for r in rep["rejected"] if r["kind"] == "rule"]
    assert set(rejected) == {"fa_ag8e", "fa_a93s"}   # the two known-bad rules
    cov = delta.coverage(ext, rejected_rule_ids=rejected)
    assert cov["rules_claimed"] == 24 and cov["rules_emitted"] == 22
    assert cov["coverage"] < cov["coverage_claimed"]


# -- B2: all-empty runs reported as perfect self-agreement ------------------

def test_self_agreement_is_none_when_every_run_is_empty():
    """Two runs that both found nothing are not evidence of stability --- they
    are no evidence at all. Returning 1.0 would let a pair of truncated,
    failed baseline calls read as a perfectly reproducible comparator."""
    runs = [doc("baseline", "r1", []), doc("baseline", "r2", [])]
    assert delta.self_agreement(runs) is None


def test_self_agreement_still_defined_when_one_run_is_empty():
    runs = [doc("baseline", "r1", [[A, B]]), doc("baseline", "r2", [])]
    assert delta.self_agreement(runs) == 0.0


def test_compute_counts_empty_runs_per_side():
    m = delta.compute([doc("tool", "t1", [])],
                      [doc("baseline", "b1", [[A, B]]),
                       doc("baseline", "b2", []),
                       doc("baseline", "b3", [])])
    assert m["n_tool_empty_runs"] == 1
    assert m["n_baseline_empty_runs"] == 2


def test_compute_flags_a_degenerate_comparison():
    """|C_tool| == 0 makes every bucket vacuous; the table must say so rather
    than let '6 baseline_only' read as a disagreement about conflicts."""
    m = delta.compute([doc("tool", "t1", [])], [doc("baseline", "b1", [[A, B]])])
    assert m["degenerate"] is True
    assert "tool found no conflicts" in m["degenerate_reason"]
    assert "degenerate" in delta.metrics_table(m)


def test_non_degenerate_when_both_sides_have_conflicts():
    m = delta.compute([doc("tool", "t1", [[A, B]])],
                      [doc("baseline", "b1", [[A, C]])])
    assert m["degenerate"] is False


# -- B3: |C_tool| == 0 was unattributed -------------------------------------

def test_conflict_channels_explain_an_empty_tool_side():
    """The emitted program can only produce a conflict two ways: one act both
    obliged and forbidden, or two obligations over an `incompat` pair. With
    neither present, zero conflicts is arithmetic, not a solver result."""
    ext = {"rules": [{"id": "fa_a", "modality": "oblige", "act": "x"},
                     {"id": "fa_b", "modality": "oblige", "act": "y"}],
           "incompat": [], "unencoded": []}
    ch = delta.conflict_channels(ext)
    assert ch["n_incompat"] == 0
    assert ch["acts_both_obliged_and_forbidden"] == []
    assert ch["any_channel_open"] is False


def test_conflict_channels_detect_an_open_direct_channel():
    ext = {"rules": [{"id": "fa_a", "modality": "oblige", "act": "x"},
                     {"id": "fa_b", "modality": "forbid", "act": "x"}],
           "incompat": [], "unencoded": []}
    ch = delta.conflict_channels(ext)
    assert ch["acts_both_obliged_and_forbidden"] == ["x"]
    assert ch["any_channel_open"] is True


def test_conflict_channels_detect_an_open_incompat_channel():
    ext = {"rules": [{"id": "fa_a", "modality": "oblige", "act": "x"},
                     {"id": "fa_b", "modality": "oblige", "act": "y"}],
           "incompat": [{"acts": ["x", "y"], "license": "logical"}],
           "unencoded": []}
    assert delta.conflict_channels(ext)["any_channel_open"] is True


@real
def test_real_extraction_has_no_open_conflict_channel():
    """Documents *why* the first real table is degenerate: gpt-oss-20b emitted
    no incompat pairs at all, and no act it obliged was also forbidden."""
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    ch = delta.conflict_channels(ext)
    assert ch["n_incompat"] == 0
    assert ch["acts_both_obliged_and_forbidden"] == []
    assert ch["any_channel_open"] is False


@real
def test_real_chain_metrics_are_stable():
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    filtered, rep = filter_extraction.filter_extraction(ext)
    base = [delta.load_conflicts(p) for p in REAL_BASELINES]
    tool = {"source": "tool", "model": ext["model"], "run_id": ext["run_id"],
            "conflicts": []}
    m = delta.compute([tool], base, extraction=ext,
                      rejected_rule_ids=[r["id"] for r in rep["rejected"]
                                         if r["kind"] == "rule"])
    assert m["C_tool"] == 0 and m["C_baseline"] == 6
    assert m["bucket_sizes"] == {"tool_only": 0, "baseline_only": 6, "both": 0}
    assert m["tool_self_agreement"] is None          # k=1: undefined, not 1.0
    assert 0 < m["baseline_self_agreement"] < 1
    assert m["degenerate"] is True
    assert m["coverage"]["rules_emitted"] == 22
    assert m["coverage"]["coverage"] == pytest.approx(22 / 42)


# -- filter_extraction agrees with emit_asp's own skip-invalid --------------

@real
def test_filter_agrees_with_emit_asp_skip_invalid():
    """The filter exists only because emit_asp was fail-fast. It must be
    retired, not diverge: this pins the two rejection sets together."""
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    cc = filter_extraction.cross_check(ext)
    assert cc["agree"], (cc["only_filter_extraction"], cc["only_emit_asp"])


@real
def test_filtered_extraction_passes_fail_fast_validation():
    import emit_asp
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    filtered, _ = filter_extraction.filter_extraction(ext)
    emit_asp.validate(filtered)          # must not raise
    with pytest.raises(emit_asp.EmitError):
        emit_asp.validate(ext)           # the unfiltered one still does


def test_filter_defaults_a_missing_exclusions_key_instead_of_aborting():
    """emit_asp treats a missing `exclusions` as a whole-document abort. A run
    that otherwise parsed cleanly should still yield a table, with the
    substitution recorded."""
    ext = {"atoms": [{"name": "a", "kind": "act"}],
           "rules": [{"id": "fa_a", "modality": "oblige", "act": "a", "tier": 1}]}
    filtered, rep = filter_extraction.filter_extraction(ext)
    assert rep["exclusions_defaulted"] is True
    assert filtered["exclusions"] == []
