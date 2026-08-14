"""Pins for the 2026-08-14 post-build additions: item 14 (golden-flag
deterministic quality checks in post_build_checks) and item 15 (fixup.py,
the mechanical fixup-round applier). Offline throughout."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import recurse_driver as R      # noqa: E402
import fixup                    # noqa: E402

TOY = os.path.join(HERE, "toy_doc.md")


def _replies():
    return json.load(open(os.path.join(HERE, "mock_replies.json")))


def _toy_root_graph(tmp_path):
    """A real toy build, its graph promoted to root_graph.json (main()'s
    own layout for post_build_checks)."""
    out = tmp_path / "run"
    out.mkdir()
    lines = R.load_doc(TOY)
    g = R.Driver({"leaf_max_lines": 15}, R.MockClient(_replies()), lines,
                 str(out)).build(1, len(lines), [], str(out))
    R.write_json(os.path.join(str(out), "root_graph.json"), g)
    return str(out), g


# ================================================ item 14: golden-flag checks
def test_edge_similarity_report_buckets_token_jaccard(tmp_path):
    g = {"nodes": [
        {"id": "n1", "provides": [{"name": "a", "prose":
                                   "the assistant must follow the chain"}],
         "needs": []},
        {"id": "n2", "provides": [],
         "needs": [{"name": "a", "prose":
                    "the assistant must follow the chain"},     # sim 1.0
                   {"name": "a", "prose": "zebra quagga xylophone"},  # 0.0
                   {"name": "dangling_x", "prose": "no provider"}]}]}
    out = os.path.join(str(tmp_path), "edge_similarity.json")
    rep = R.edge_similarity_report(g, out)
    assert rep["total_edges"] == 2, "danglings must not count as edges"
    assert rep["buckets"] == {"lt_0.10": 1, "0.10_0.25": 0, "gte_0.25": 1}
    assert rep["low_sim_edges"][0]["needer"] == "n2"
    assert json.load(open(out)) == rep


def test_post_build_checks_golden_flag_runs_the_instruments(tmp_path,
                                                            capsys):
    """THE FLAG (item 14): with a golden set, post_build_checks must ALSO
    produce compare_vs_golden.json, the repair census, and
    edge_similarity.json -- and stay silent about them when unset."""
    out, g = _toy_root_graph(tmp_path)
    golden = os.path.join(out, "golden.json")
    R.write_json(golden, g)                      # self-compare: a stub golden
    R.post_build_checks(out, golden=golden, doc_path=TOY)
    text = capsys.readouterr().out
    assert os.path.exists(os.path.join(out, "compare_vs_golden.json"))
    assert os.path.exists(os.path.join(out, "edge_similarity.json"))
    assert os.path.exists(os.path.join(out, "postbuild_repair_census.txt"))
    assert "compare_vs_golden" in text and "edge_similarity" in text
    # self-compare sanity: a graph against itself aligns perfectly
    rep = json.load(open(os.path.join(out, "compare_vs_golden.json")))
    assert rep["alignment"]["counts"]["a"]["misaligned"] == 0


def test_post_build_checks_without_golden_is_unchanged(tmp_path, capsys):
    out, _g = _toy_root_graph(tmp_path)
    R.post_build_checks(out)
    text = capsys.readouterr().out
    assert "compare_vs_golden" not in text
    assert not os.path.exists(os.path.join(out, "compare_vs_golden.json"))
    assert not os.path.exists(os.path.join(out, "edge_similarity.json"))


# ======================================================= item 15: fixup.py
def _verdict(kind, verdict, detail, idx=0):
    return {"idx": idx, "kind": kind, "verdict": verdict,
            "risk": 1.0, "detail": detail, "grounds": "g"}


def _fixup_run(tmp_path, verdicts):
    run = tmp_path / "run"
    run.mkdir()
    g = {"nodes": [
        {"id": "L1-4_n01", "establishes": "x",
         "needs": [{"name": "root_authority", "prose": "p"}],
         "provides": []},
        {"id": "L5-9_n02", "establishes": "y", "needs": [],
         "provides": [{"name": "root_authority", "prose": "q"}]}]}
    R.write_json(os.path.join(str(run), "root_graph.json"), g)
    R.write_json(os.path.join(str(run), "frontier_verdicts.json"),
                 {"run": str(run), "verdicts": verdicts})
    return str(run)


def test_rejected_rename_is_reverted_in_the_fixed_graph(tmp_path):
    """THE MECHANICAL CASE: a frontier-rejected seat rename restores the
    original dangling name -- in root_graph.fixed.json, NEVER in place."""
    run = _fixup_run(tmp_path, [_verdict(
        "seat_accepted_rename", "reject",
        {"needer": "L1-4_n01", "name": "house_rules",
         "rename_to": "root_authority"})])
    res = fixup.apply_fixups(run)
    assert res["reverted"] and res["reverted"][0]["reverted_needs"] == 1
    fixed = json.load(open(os.path.join(run, "root_graph.fixed.json")))
    assert fixed["nodes"][0]["needs"][0]["name"] == "house_rules"
    assert any("fixup" in a for a in fixed.get("driver_autofixes", []))
    # the original artifact is untouched
    orig = json.load(open(os.path.join(run, "root_graph.json")))
    assert orig["nodes"][0]["needs"][0]["name"] == "root_authority"
    # the fixup report reached health
    health = [json.loads(l) for l in open(os.path.join(run,
                                                       "health.jsonl"))]
    assert health[-1]["artifact"] == "fixup"
    assert health[-1]["renames_reverted"] == 1


def test_upholds_are_confirmed_and_dropped_merge_is_a_noop(tmp_path):
    run = _fixup_run(tmp_path, [
        _verdict("seat_accepted_rename", "uphold",
                 {"needer": "L1-4_n01", "name": "house_rules",
                  "rename_to": "root_authority"}),
        _verdict("dropped_merge", "uphold", {"survivor": "a", "retired":
                                             "b"}, idx=1)])
    res = fixup.apply_fixups(run)
    assert len(res["confirmed"]) == 2 and not res["queue"]
    fixed = json.load(open(os.path.join(run, "root_graph.fixed.json")))
    assert fixed["nodes"][0]["needs"][0]["name"] == "root_authority", \
        "an upheld rename must not be touched"


def test_non_mechanical_rejections_are_queued_not_applied(tmp_path):
    """Code never makes content decisions: modal drift and broken promises
    (and merge application) land on fixup_queue.json with a reason each."""
    run = _fixup_run(tmp_path, [
        _verdict("modal_drift", "reject", {"id": "L1-4_n01"}),
        _verdict("broken_promise", "reject", {"unwind": "root",
                                              "name": "c"}, idx=1),
        _verdict("dropped_merge", "reject", {"survivor": "a"}, idx=2),
        _verdict("low_sim_edge", "no_verdict", {"needer": "n"}, idx=3)])
    res = fixup.apply_fixups(run)
    assert not res["reverted"] and not res["confirmed"]
    q = json.load(open(os.path.join(run, "fixup_queue.json")))
    assert q["total"] == 4
    assert all(it["reason"] for it in q["items"])
    assert "regeneration" in q["items"][0]["reason"]
    # nothing about the graph changed
    fixed = json.load(open(os.path.join(run, "root_graph.fixed.json")))
    orig = json.load(open(os.path.join(run, "root_graph.json")))
    assert fixed["nodes"] == orig["nodes"]


def test_near_miss_round_trip_routes_by_the_recorded_decision(tmp_path):
    """Review item 2, end to end: a dangling_near_miss judged
    same_concept by the frontier arrives as `reject` (the recorded
    NON-rename is wrong) and must land on the queue as a proposed NEW
    rename -- never auto-applied; different_concept arrives as `uphold`
    and confirms the honest dangling. Verdicts produced by
    frontier_review's own batch parser, not hand-written."""
    import frontier_review as FR
    ok, bad = FR.vocab_for("dangling_near_miss")
    assert (ok, bad) == ("different_concept", "same_concept")
    run = _fixup_run(tmp_path, [
        dict(_verdict("dangling_near_miss", "x",
                      {"needer": "L1-4_n01", "name": "missing_concept"}),
             **FR.parse_verdict(json.dumps({"verdict": "same_concept",
                                            "grounds": "same referent"}),
                                ok, bad)),
        dict(_verdict("dangling_near_miss", "x",
                      {"needer": "L1-4_n01", "name": "other_concept"},
                      idx=1),
             **FR.parse_verdict(json.dumps({"verdict": "different_concept",
                                            "grounds": "distinct"}),
                                ok, bad))])
    res = fixup.apply_fixups(run)
    assert len(res["confirmed"]) == 1
    assert res["confirmed"][0]["detail"]["name"] == "other_concept"
    assert len(res["queue"]) == 1
    q = res["queue"][0]
    assert q["detail"]["name"] == "missing_concept"
    assert "NEW rename" in q["reason"] and "never auto-apply" in q["reason"]
    # nothing was written into the graph either way
    fixed = json.load(open(os.path.join(run, "root_graph.fixed.json")))
    orig = json.load(open(os.path.join(run, "root_graph.json")))
    assert fixed["nodes"] == orig["nodes"]


def test_dispositions_persist_as_rows_on_the_verdicts_artifact(tmp_path):
    """Review item 2 (persistence half): confirmed and reverted rows land
    on frontier_verdicts.json, not just counts in health."""
    run = _fixup_run(tmp_path, [
        _verdict("seat_accepted_rename", "uphold",
                 {"needer": "L1-4_n01", "name": "house_rules",
                  "rename_to": "root_authority"}),
        _verdict("seat_accepted_rename", "reject",
                 {"needer": "L1-4_n01", "name": "house_rules",
                  "rename_to": "root_authority"}, idx=1)])
    fixup.apply_fixups(run)
    fv = json.load(open(os.path.join(run, "frontier_verdicts.json")))
    disp = fv["dispositions"]
    assert [r["idx"] for r in disp["confirmed"]] == [0]
    assert [r["idx"] for r in disp["reverted"]] == [1]
    assert disp["reverted"][0]["reverted_needs"] == 1
    assert disp["queued_nonmechanical"] == 0


def test_ambiguous_revert_target_queues_instead_of_reverting(tmp_path):
    """Adversarial review (INFO, latent): when the needer carries MORE
    THAN ONE need named rename_to, the renamed entry is indistinguishable
    from a genuine pre-existing need -- reverting all of them would
    rename a REAL edge. Ambiguity goes to the queue."""
    run = tmp_path / "run"
    run.mkdir()
    g = {"nodes": [
        {"id": "L1-4_n01", "establishes": "x",
         "needs": [{"name": "root_authority", "prose": "renamed one"},
                   {"name": "root_authority", "prose": "genuine one"}],
         "provides": []}]}
    R.write_json(os.path.join(str(run), "root_graph.json"), g)
    R.write_json(os.path.join(str(run), "frontier_verdicts.json"),
                 {"run": str(run), "verdicts": [_verdict(
                     "seat_accepted_rename", "reject",
                     {"needer": "L1-4_n01", "name": "house_rules",
                      "rename_to": "root_authority"})]})
    res = fixup.apply_fixups(str(run))
    assert not res["reverted"]
    assert "ambiguous" in res["queue"][0]["reason"]
    fixed = json.load(open(os.path.join(str(run),
                                        "root_graph.fixed.json")))
    assert [d["name"] for d in fixed["nodes"][0]["needs"]] \
        == ["root_authority", "root_authority"], "nothing may be renamed"


def test_unrevertable_rename_falls_to_the_queue_with_a_reason(tmp_path):
    run = _fixup_run(tmp_path, [_verdict(
        "seat_accepted_rename", "reject",
        {"needer": "NO_SUCH_NODE", "name": "house_rules",
         "rename_to": "root_authority"})])
    res = fixup.apply_fixups(run)
    assert not res["reverted"]
    assert "not in root graph" in res["queue"][0]["reason"]


def test_cli_requires_a_run_dir(capsys):
    assert fixup.main([]) == 2
    assert "usage" in capsys.readouterr().out
