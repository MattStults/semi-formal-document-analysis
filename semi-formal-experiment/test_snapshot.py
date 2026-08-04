"""Tests for snapshot.py — the freeze/diff/flip-list core of the iteration loop.

What is being pinned, and why each pin exists:

  * DETERMINISM — the whole point of a snapshot is that "same inputs →
    byte-identical file". A wall-clock timestamp or unsorted dict would make
    every diff dirty and every flip list noisy; two builds over the same
    inputs must serialize to the same bytes.
  * FLIP LISTS — diff is exercised on HAND-CONSTRUCTED snapshot dicts where we
    know exactly which clause flips and which channel moved, so the test fails
    if diff ever reports the wrong direction, the wrong scores, or the wrong
    largest-moving channel. A diff tested only on real artifacts would pass
    on any output shaped like a diff.
  * THRESHOLD RECORDED **AND** HONORED — the recorded threshold must be the
    label-free rule (`threshold.PREFERRED`) applied to this query's own
    positive scores, the predicted set must be exactly {score > 0 and
    score >= threshold} over the recorded scores, and both must agree with
    what `relevance.predict()` (default, label-free) returns. Recording one
    number and thresholding on another is how a snapshot silently lies.
  * CONFIG-SHA CHANGE DETECTION — an input file edit must surface in the diff
    as a named changed sha plus a vocabulary-level change, so "what changed"
    is never reconstructed from memory.
  * NO-OP MESSAGE — identical configs + identical scores must SAY "no-op",
    not print empty lists that read the same as "diff ran on the wrong pair".

All fixtures here are synthetic and tiny; nothing reads the real artifacts,
so these tests run in milliseconds and cannot be confounded by artifact drift.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

import snapshot
import relevance
import threshold as threshold_rules


# ------------------------------------------------------------- fixtures

def _write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)
    return str(path)


@pytest.fixture
def fixture_paths(tmp_path):
    """A tiny synthetic corpus where the signal is fully understood.

    c1/c4/c6 share the behaviour's atom and its vocabulary; c2 is about a
    different topic with its own atom; c3/c5 are noise. One behaviour,
    `beh-help`, whose single query atom appears on c1/c4/c6.
    """
    clauses = _write(tmp_path / "clauses.json", {"clauses": [
        {"id": "c1", "quote": "models must always help the user accomplish tasks",
         "section_path": ["help"], "locator": "L1"},
        {"id": "c2", "quote": "avoid causing harm to third parties in the world",
         "section_path": ["harm"], "locator": "L2"},
        {"id": "c3", "quote": "the weather in paris is mild during spring season",
         "section_path": ["misc"], "locator": "L3"},
        {"id": "c4", "quote": "helpful assistance benefits the user greatly indeed",
         "section_path": ["help"], "locator": "L4"},
        {"id": "c5", "quote": "pastry recipes require butter flour and sugar",
         "section_path": ["misc"], "locator": "L5"},
        {"id": "c6", "quote": "assist users helpfully with their many requests",
         "section_path": ["help"], "locator": "L6"},
    ]})
    annotations = _write(tmp_path / "ann.json", {"clauses": [
        {"clause_id": "c1", "atoms": [
            {"name": "helping_user", "kind": "act", "gloss": "model helps the user"},
            {"name": "user_task", "kind": "situation", "gloss": "user has a task"}]},
        {"clause_id": "c4", "atoms": [
            {"name": "helping_user", "kind": "act", "gloss": "model helps the user"},
            {"name": "assist_request", "kind": "act", "gloss": "a request is assisted"}]},
        {"clause_id": "c6", "atoms": [
            {"name": "helping_user", "kind": "act", "gloss": "model helps the user"},
            {"name": "user_task", "kind": "situation", "gloss": "user has a task"},
            {"name": "assist_request", "kind": "act", "gloss": "a request is assisted"}]},
        {"clause_id": "c2", "atoms": [
            {"name": "third_party_harm", "kind": "situation",
             "gloss": "someone outside the conversation is harmed"}]},
    ]})
    # THREE query atoms on purpose: relevance iterates the query-atom SET, so
    # a single-atom query cannot expose hash-seed-dependent summation order —
    # the cross-process determinism test below needs a set worth permuting.
    atoms = _write(tmp_path / "atoms.json", {
        "beh-help": {"atoms": [
            {"name": "helping_user", "kind": "act",
             "gloss": "model helps the user"},
            {"name": "user_task", "kind": "situation",
             "gloss": "user has a task"},
            {"name": "assist_request", "kind": "act",
             "gloss": "a request is assisted"}]},
    })
    queries = _write(tmp_path / "queries.json", {"behaviours": [
        {"slug": "beh-help", "name": "Helpfulness",
         "definition": "the model helps the user accomplish tasks"},
    ]})
    return {"clauses": clauses, "annotations": annotations,
            "atoms": atoms, "queries": queries}


def _build(paths, tag="t"):
    return snapshot.build_snapshot(
        tag,
        annotations_path=paths["annotations"],
        atoms_path=paths["atoms"],
        clauses_path=paths["clauses"],
        queries_path=paths["queries"])


# ----------------------------------------------------------- determinism

def test_snapshot_bytes_identical_across_builds(fixture_paths):
    """Two independent builds over the same inputs → the same bytes.

    Serialization goes through snapshot.snapshot_bytes, the exact bytes the
    CLI writes, so a timestamp / unsorted key / set-ordering leak anywhere in
    the pipeline fails here.
    """
    a = snapshot.snapshot_bytes(_build(fixture_paths, tag="same"))
    b = snapshot.snapshot_bytes(_build(fixture_paths, tag="same"))
    assert a == b


def test_snapshot_write_roundtrip_is_byte_identical(fixture_paths, tmp_path):
    """Writing the same snapshot twice produces byte-identical files."""
    snap = _build(fixture_paths, tag="rt")
    p1 = snapshot.write_snapshot(snap, out_dir=str(tmp_path / "one"))
    p2 = snapshot.write_snapshot(snap, out_dir=str(tmp_path / "two"))
    assert open(p1, "rb").read() == open(p2, "rb").read()
    # and the round-trip loads back to the same object
    assert snapshot.load_snapshot(p1) == snap


def test_snapshot_bytes_identical_across_processes(tmp_path):
    """Byte-identity must hold ACROSS processes, not just within one.

    The in-process test above cannot catch hash-seed nondeterminism: within a
    process every build shares one str-hash seed, so set iteration order — and
    therefore float summation order in the scorer's atom channel — repeats.
    Across processes the seed changes and the last ulp of the sums moves,
    which showed up as real byte diffs between two builds of the SAME real
    baseline. The tiny synthetic fixture does not carry enough query atoms to
    permute, so this test runs over the REAL artifacts — the configuration
    that demonstrably failed — with two different seeds pinned explicitly so
    the failure is reproducible, not probabilistic.
    """
    import subprocess
    here = os.path.dirname(snapshot.__file__)
    ann = os.path.join(here, "annotations_b8.json")
    atoms = os.path.join(here, "behavior_atoms_b8.json")
    if not (os.path.exists(ann) and os.path.exists(atoms)):
        pytest.skip("real artifacts not present")
    outs = []
    for seed, sub in (("1", "one"), ("2", "two")):
        outdir = str(tmp_path / sub)
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run(
            [sys.executable, os.path.join(here, "snapshot.py"),
             "snapshot", "--tag", "x",
             "--annotations", ann, "--atoms", atoms, "--dir", outdir],
            env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        outs.append(open(os.path.join(outdir, "x.json"), "rb").read())
    assert outs[0] == outs[1], (
        "snapshot bytes differ across processes — hash-seed-dependent float "
        "summation order is leaking into the recorded numbers")


# ------------------------------------------------------------ flip lists

def _hand_snapshot(tag, predicted, scores, threshold, channels,
                   shas=None, weights=None, df=None):
    """A minimal snapshot dict for one behaviour, fully under test control."""
    shas = shas or {"annotations": "A", "behaviour_atoms": "B",
                    "clauses": "C", "queries": "Q"}
    df = {"helping_user": 3} if df is None else df
    return {
        "tag": tag,
        "config": {
            "inputs": {k: {"path": k, "sha256": v} for k, v in shas.items()},
            "weights": weights or {"lex": 1.0, "atom": 0.6},
            "threshold_rule": "otsu",
        },
        "vocabulary": {"atom_count": len(df), "df": df,
                       "df_sha256": "D" + str(sorted(df.items()))},
        "behaviours": {
            "beh-x": {
                "threshold": threshold,
                "predicted": sorted(predicted),
                "scores": scores,
                "raw": dict(scores),
                "channels": channels,
            },
        },
    }


def test_diff_flip_lists_scores_and_moving_channel():
    """A constructed flip in each direction, with a KNOWN moving channel.

    c2 flips IN (0.2 → 0.8; the atom channel moved +0.5, most of any channel).
    c3 flips OUT (0.6 → 0.1; the lex channel moved −0.5, most of any channel).
    c1 stays predicted in both and must appear in neither list.
    """
    ch_a = {"c1": {"lex": 1.0, "atom": 0.6, "kind": 0.0, "section": 0.2},
            "c2": {"lex": 0.2, "atom": 0.0, "kind": 0.0, "section": 0.0},
            "c3": {"lex": 0.55, "atom": 0.0, "kind": 0.0, "section": 0.05}}
    ch_b = {"c1": {"lex": 1.0, "atom": 0.6, "kind": 0.0, "section": 0.2},
            "c2": {"lex": 0.25, "atom": 0.5, "kind": 0.0, "section": 0.05},
            "c3": {"lex": 0.05, "atom": 0.0, "kind": 0.0, "section": 0.05}}
    a = _hand_snapshot("a", predicted=["c1", "c3"],
                       scores={"c1": 1.0, "c2": 0.2, "c3": 0.6},
                       threshold=0.5, channels=ch_a)
    b = _hand_snapshot("b", predicted=["c1", "c2"],
                       scores={"c1": 1.0, "c2": 0.8, "c3": 0.1},
                       threshold=0.5, channels=ch_b,
                       shas={"annotations": "A2", "behaviour_atoms": "B",
                             "clauses": "C", "queries": "Q"})
    d = snapshot.diff_snapshots(a, b)

    beh = d["behaviours"]["beh-x"]
    newly = {f["clause_id"]: f for f in beh["newly_predicted"]}
    gone = {f["clause_id"]: f for f in beh["no_longer_predicted"]}

    assert set(newly) == {"c2"}
    assert set(gone) == {"c3"}

    assert newly["c2"]["score_a"] == pytest.approx(0.2)
    assert newly["c2"]["score_b"] == pytest.approx(0.8)
    assert newly["c2"]["threshold_a"] == pytest.approx(0.5)
    assert newly["c2"]["threshold_b"] == pytest.approx(0.5)
    assert newly["c2"]["top_channel"] == "atom"          # +0.5, the largest move

    assert gone["c3"]["score_a"] == pytest.approx(0.6)
    assert gone["c3"]["score_b"] == pytest.approx(0.1)
    assert gone["c3"]["top_channel"] == "lex"            # −0.5, the largest move

    # a clause predicted in both never appears as a flip
    assert "c1" not in newly and "c1" not in gone


# ------------------------------------------------------------- flip causes

def test_flip_cause_threshold_drift_when_score_identical_and_cut_moved():
    """The review's real case class: a clause whose score is IDENTICAL in both
    snapshots (at PRECISION) but sits between the two thresholds flipped only
    because the cut moved. Its cause must be tagged `threshold_drift`, so the
    adjudicator gets the threshold question, never the clause question
    (ITERATION_LOOP.md policy §3)."""
    ch = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0},
          "c2": {"lex": 0.6, "atom": 0.0, "kind": 0.0, "section": 0.0}}
    a = _hand_snapshot("a", predicted=["c1"],
                       scores={"c1": 1.0, "c2": 0.6},
                       threshold=0.7, channels=ch)
    b = _hand_snapshot("b", predicted=["c1", "c2"],
                       scores={"c1": 1.0, "c2": 0.6},
                       threshold=0.5, channels=ch)
    d = snapshot.diff_snapshots(a, b)
    newly = {f["clause_id"]: f for f in
             d["behaviours"]["beh-x"]["newly_predicted"]}
    assert set(newly) == {"c2"}
    assert newly["c2"]["cause"] == "threshold_drift"


def test_flip_cause_match_change_when_score_moved_and_cut_did_not():
    ch_a = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0},
            "c2": {"lex": 0.2, "atom": 0.0, "kind": 0.0, "section": 0.0}}
    ch_b = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0},
            "c2": {"lex": 0.2, "atom": 0.6, "kind": 0.0, "section": 0.0}}
    a = _hand_snapshot("a", predicted=["c1"],
                       scores={"c1": 1.0, "c2": 0.2},
                       threshold=0.5, channels=ch_a)
    b = _hand_snapshot("b", predicted=["c1", "c2"],
                       scores={"c1": 1.0, "c2": 0.8},
                       threshold=0.5, channels=ch_b)
    d = snapshot.diff_snapshots(a, b)
    newly = {f["clause_id"]: f for f in
             d["behaviours"]["beh-x"]["newly_predicted"]}
    assert newly["c2"]["cause"] == "match_change"


def test_flip_cause_both_when_score_and_cut_both_moved():
    ch_a = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0},
            "c2": {"lex": 0.2, "atom": 0.0, "kind": 0.0, "section": 0.0}}
    ch_b = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0},
            "c2": {"lex": 0.2, "atom": 0.6, "kind": 0.0, "section": 0.0}}
    a = _hand_snapshot("a", predicted=["c1"],
                       scores={"c1": 1.0, "c2": 0.2},
                       threshold=0.5, channels=ch_a)
    b = _hand_snapshot("b", predicted=["c1", "c2"],
                       scores={"c1": 1.0, "c2": 0.8},
                       threshold=0.6, channels=ch_b)
    d = snapshot.diff_snapshots(a, b)
    newly = {f["clause_id"]: f for f in
             d["behaviours"]["beh-x"]["newly_predicted"]}
    assert newly["c2"]["cause"] == "both"


# ------------------------------------------------- threshold recorded/honored

def test_threshold_recorded_and_honored(fixture_paths):
    """The recorded threshold is the label-free rule over the recorded scores,
    the predicted set is exactly the recorded scores cut at it, and both agree
    with relevance.predict()'s own label-free default."""
    snap = _build(fixture_paths)
    beh = snap["behaviours"]["beh-help"]

    # recorded == the preferred label-free rule applied to this query's own
    # positive scores (exactly predict()'s derivation)
    positives = [s for s in beh["scores"].values() if s > 0]
    expected_t = threshold_rules.apply_rule(threshold_rules.PREFERRED, positives)
    assert beh["threshold"] == pytest.approx(expected_t)
    assert snap["config"]["threshold_rule"] == threshold_rules.PREFERRED

    # honored: the predicted set is the recorded scores cut at the recorded
    # threshold — no other numbers involved
    expected_set = {cid for cid, s in beh["scores"].items()
                    if s > 0 and s >= beh["threshold"]}
    assert set(beh["predicted"]) == expected_set

    # and end-to-end: identical to what the scorer itself predicts label-free
    idx = relevance.RelevanceIndex.from_files(
        clauses_path=fixture_paths["clauses"],
        annotations_path=fixture_paths["annotations"])
    b = relevance.behaviour_from_panel(
        {"slug": "beh-help", "name": "Helpfulness",
         "definition": "the model helps the user accomplish tasks"},
        relevance.load_behaviour_atoms(fixture_paths["atoms"]))
    assert set(beh["predicted"]) == idx.predict(b)


# ------------------------------------------------------ config-sha detection

def test_config_sha_change_detected_in_diff(fixture_paths, tmp_path):
    """Editing the annotations file changes its sha; the diff must NAME it,
    and the vocabulary diff must show the atom that appeared."""
    a = _build(fixture_paths, tag="a")

    edited = json.load(open(fixture_paths["annotations"]))
    edited["clauses"].append({"clause_id": "c5", "atoms": [
        {"name": "novel_pastry_atom", "kind": "entity", "gloss": "a pastry"}]})
    fixture_paths = dict(fixture_paths,
                         annotations=_write(tmp_path / "ann2.json", edited))
    b = _build(fixture_paths, tag="b")

    d = snapshot.diff_snapshots(a, b)
    assert d["config"]["changed"] == ["annotations"]
    assert "novel_pastry_atom" in d["vocabulary"]["atoms_added"]
    assert d["vocabulary"]["atoms_removed"] == []
    assert not d["noop"]


# ------------------------------------------------------------ no-op message

def test_noop_diff_says_so_explicitly(fixture_paths):
    """Identical configs + identical scores must produce an explicit no-op
    statement, not silently empty lists."""
    a = _build(fixture_paths, tag="a")
    b = _build(fixture_paths, tag="b")   # same inputs, different tag only
    d = snapshot.diff_snapshots(a, b)
    assert d["noop"] is True
    text = snapshot.format_diff(d)
    assert "no-op change" in text


def test_real_change_is_not_reported_noop():
    """The no-op flag must be False the moment any score differs, even with
    identical config shas (e.g. a code change under the same inputs)."""
    ch = {"c1": {"lex": 1.0, "atom": 0.0, "kind": 0.0, "section": 0.0}}
    a = _hand_snapshot("a", ["c1"], {"c1": 1.0}, 0.5, ch)
    b = _hand_snapshot("b", ["c1"], {"c1": 0.9}, 0.5,
                       {"c1": {"lex": 0.9, "atom": 0.0, "kind": 0.0,
                               "section": 0.0}})
    d = snapshot.diff_snapshots(a, b)
    assert d["noop"] is False
    assert "no-op change" not in snapshot.format_diff(d)


def test_threshold_only_change_is_not_reported_noop():
    """⚠️ Found by the 2026-08-03 fix build, confirmed live on the real
    baseline: identical configs + identical scores + a MOVED CUT produced 34
    flips and `noop: True`, so format_diff printed "no-op change" and stopped —
    hiding exactly the threshold_drift class the cause-tagging exists to make
    adjudicable. A no-op must also require identical thresholds and predicted
    sets."""
    ch = {"c1": {"lex": 0.6, "atom": 0.0, "kind": 0.0, "section": 0.0}}
    a = _hand_snapshot("a", [], {"c1": 0.6}, 0.7, ch)
    b = _hand_snapshot("b", ["c1"], {"c1": 0.6}, 0.5, ch)
    d = snapshot.diff_snapshots(a, b)
    assert d["noop"] is False, (
        "identical scores with a moved cut flipped c1 yet reported no-op")
    assert "no-op change" not in snapshot.format_diff(d)
    flips = d["behaviours"]["beh-x"]["newly_predicted"]
    assert [f["clause_id"] for f in flips] == ["c1"]
    assert flips[0]["cause"] == "threshold_drift"


# ---------------------------------------------------------------- overlay

def _overlay_file(tmp_path, name="cont.json"):
    """A minimal VALID containment overlay for the synthetic fixture."""
    path = str(tmp_path / name)
    with open(path, "w") as f:
        json.dump({"artifact": "containment", "version": "v0",
                   "budget": {"max_edges": 1, "max_families": 1},
                   "edges": [{"child": "assist_request", "parent": "request",
                              "license": "shared_head", "note": "test edge"}],
                   "provenance": {"origin": "test"}}, f)
    return path


def test_overlay_sha_recorded_and_null_when_absent(fixture_paths, tmp_path):
    """Config identity must carry the overlay: the file's sha when one is
    passed, an explicit null when not — so old and new snapshots diff cleanly
    and the diff NAMES `overlay` as the changed input."""
    pytest.importorskip("containment")
    import hashlib
    plain = _build(fixture_paths, tag="plain")
    assert plain["config"]["inputs"]["overlay"] is None

    ov = _overlay_file(tmp_path)
    snap = snapshot.build_snapshot(
        "with-overlay",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        overlay_path=ov)
    rec = snap["config"]["inputs"]["overlay"]
    assert rec["path"] == os.path.basename(ov)
    assert rec["sha256"] == hashlib.sha256(open(ov, "rb").read()).hexdigest()

    d = snapshot.diff_snapshots(plain, snap)
    assert "overlay" in d["config"]["changed"]


def test_pricing_version_recorded_iff_overlay_active(fixture_paths, tmp_path):
    """When an overlay is active the scoring rules are containment.py's, so
    the config identity must carry containment.PRICING_VERSION under
    `pricing_version` — and the key must be ABSENT when no overlay is (the
    base scorer's rules are not containment's to version)."""
    containment = pytest.importorskip("containment")
    plain = _build(fixture_paths, tag="plain")
    assert "pricing_version" not in plain["config"]

    ov = _overlay_file(tmp_path)
    snap = snapshot.build_snapshot(
        "with-overlay",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        overlay_path=ov)
    assert snap["config"]["pricing_version"] == containment.PRICING_VERSION


def test_pricing_version_change_shows_in_snapshot_sha(fixture_paths, tmp_path,
                                                      monkeypatch):
    """A scoring-rule version bump under IDENTICAL inputs must change the
    snapshot bytes — otherwise a pricing change produces a diff that cannot
    name its own cause."""
    containment = pytest.importorskip("containment")
    import hashlib
    ov = _overlay_file(tmp_path)
    kw = dict(annotations_path=fixture_paths["annotations"],
              atoms_path=fixture_paths["atoms"],
              clauses_path=fixture_paths["clauses"],
              queries_path=fixture_paths["queries"],
              overlay_path=ov)
    before = snapshot.build_snapshot("v", **kw)
    monkeypatch.setattr(containment, "PRICING_VERSION", "test-bump")
    after = snapshot.build_snapshot("v", **kw)
    assert after["config"]["pricing_version"] == "test-bump"
    ba = snapshot.snapshot_bytes(before)
    bb = snapshot.snapshot_bytes(after)
    assert (hashlib.sha256(ba).hexdigest()
            != hashlib.sha256(bb).hexdigest())


def test_snapshot_deterministic_with_overlay_on(fixture_paths, tmp_path):
    """Two builds under the same overlay serialize to the same bytes — the
    determinism contract survives the ContainmentIndex path."""
    pytest.importorskip("containment")
    ov = _overlay_file(tmp_path)
    kw = dict(annotations_path=fixture_paths["annotations"],
              atoms_path=fixture_paths["atoms"],
              clauses_path=fixture_paths["clauses"],
              queries_path=fixture_paths["queries"],
              overlay_path=ov)
    a = snapshot.snapshot_bytes(snapshot.build_snapshot("same", **kw))
    b = snapshot.snapshot_bytes(snapshot.build_snapshot("same", **kw))
    assert a == b


def test_cli_overlay_flag(fixture_paths, tmp_path, capsys):
    """`snapshot --overlay PATH` builds through the overlay and records it."""
    pytest.importorskip("containment")
    ov = _overlay_file(tmp_path)
    outdir = str(tmp_path / "snaps")
    snapshot.main(["snapshot", "--tag", "ov",
                   "--annotations", fixture_paths["annotations"],
                   "--atoms", fixture_paths["atoms"],
                   "--clauses", fixture_paths["clauses"],
                   "--queries", fixture_paths["queries"],
                   "--dir", outdir, "--overlay", ov])
    snap = snapshot.load_snapshot(os.path.join(outdir, "ov.json"))
    assert snap["config"]["inputs"]["overlay"]["path"] == os.path.basename(ov)


# ------------------------------------------------------- frozen thresholds

def _thresholds_file(tmp_path, thresholds, name="thr.json"):
    """A minimal frozen-thresholds artifact (the versioned-cut fix)."""
    path = str(tmp_path / name)
    with open(path, "w") as f:
        json.dump({"artifact": "thresholds_frozen",
                   "provenance": "test: label-free frozen cuts",
                   "thresholds": thresholds}, f)
    return path


def test_frozen_threshold_artifact_honored(fixture_paths, tmp_path):
    """When a frozen-thresholds artifact names this behaviour, the recorded
    threshold must BE the artifact's value (not the rule's), the predicted set
    must be the recorded scores cut at that value under predict()'s decision
    rule (score > 0 and score >= cut), and the behaviour must record that its
    cut came from the artifact — so a frozen cut can never silently revert to
    the drifting rule (the m0422 threshold_drift escalation)."""
    thr = _thresholds_file(tmp_path, {"beh-help": 0.9})
    snap = snapshot.build_snapshot(
        "frozen",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        thresholds_path=thr)
    beh = snap["behaviours"]["beh-help"]
    assert beh["threshold"] == pytest.approx(0.9)
    # the artifact value must actually DIFFER from the rule's, or this test
    # could pass with the flag ignored
    positives = [s for s in beh["scores"].values() if s > 0]
    rule_t = threshold_rules.apply_rule(threshold_rules.PREFERRED, positives)
    assert beh["threshold"] != pytest.approx(rule_t)
    # honored: predicted is exactly the recorded scores cut at the frozen value
    expected_set = {cid for cid, s in beh["scores"].items()
                    if s > 0 and s >= beh["threshold"]}
    assert set(beh["predicted"]) == expected_set
    assert beh["threshold_source"] == "frozen_artifact"


def test_thresholds_sha_recorded_and_null_when_absent(fixture_paths, tmp_path):
    """Config identity must carry the frozen-thresholds artifact: the file's
    sha under `thresholds` when passed, an explicit null when not (the overlay
    pattern, amendment F9's version dispatch) — so frozen-cut and rule-cut
    snapshots diff cleanly and the diff NAMES `thresholds` as the changed
    input."""
    import hashlib
    plain = _build(fixture_paths, tag="plain")
    assert plain["config"]["inputs"]["thresholds"] is None

    thr = _thresholds_file(tmp_path, {"beh-help": 0.9})
    snap = snapshot.build_snapshot(
        "with-thresholds",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        thresholds_path=thr)
    rec = snap["config"]["inputs"]["thresholds"]
    assert rec["path"] == os.path.basename(thr)
    assert rec["sha256"] == hashlib.sha256(open(thr, "rb").read()).hexdigest()

    d = snapshot.diff_snapshots(plain, snap)
    assert "thresholds" in d["config"]["changed"]


def test_thresholds_fallback_for_missing_behaviour(fixture_paths, tmp_path):
    """A behaviour ABSENT from the artifact falls back to the derivation rule
    — and the fallback is RECORDED per behaviour, so a partially-covering
    artifact can never silently freeze less than it claims."""
    thr = _thresholds_file(tmp_path, {"some-other-behaviour": 0.5})
    snap = snapshot.build_snapshot(
        "fallback",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        thresholds_path=thr)
    beh = snap["behaviours"]["beh-help"]
    positives = [s for s in beh["scores"].values() if s > 0]
    rule_t = threshold_rules.apply_rule(threshold_rules.PREFERRED, positives)
    assert beh["threshold"] == pytest.approx(rule_t)
    assert beh["threshold_source"] == "rule_fallback"
    expected_set = {cid for cid, s in beh["scores"].items()
                    if s > 0 and s >= beh["threshold"]}
    assert set(beh["predicted"]) == expected_set


def test_snapshot_deterministic_with_thresholds_flag(fixture_paths, tmp_path):
    """Two builds under the same frozen-thresholds artifact serialize to the
    same bytes — the determinism contract survives the new path."""
    thr = _thresholds_file(tmp_path, {"beh-help": 0.9})
    kw = dict(annotations_path=fixture_paths["annotations"],
              atoms_path=fixture_paths["atoms"],
              clauses_path=fixture_paths["clauses"],
              queries_path=fixture_paths["queries"],
              thresholds_path=thr)
    a = snapshot.snapshot_bytes(snapshot.build_snapshot("same", **kw))
    b = snapshot.snapshot_bytes(snapshot.build_snapshot("same", **kw))
    assert a == b


def test_old_behavior_reachable_without_thresholds_flag(fixture_paths):
    """F9 version dispatch: OMITTING the flag must reproduce the old rule-
    derived behavior exactly — recorded threshold == the preferred label-free
    rule over this query's positive scores, and no per-behaviour source key
    (the old snapshot shape is the old shape)."""
    snap = _build(fixture_paths, tag="old-path")
    beh = snap["behaviours"]["beh-help"]
    positives = [s for s in beh["scores"].values() if s > 0]
    rule_t = threshold_rules.apply_rule(threshold_rules.PREFERRED, positives)
    assert beh["threshold"] == pytest.approx(rule_t)
    assert "threshold_source" not in beh


def test_cli_thresholds_flag(fixture_paths, tmp_path):
    """`snapshot --thresholds PATH` builds through the artifact and records
    it in the config identity."""
    thr = _thresholds_file(tmp_path, {"beh-help": 0.9})
    outdir = str(tmp_path / "snaps")
    snapshot.main(["snapshot", "--tag", "thr",
                   "--annotations", fixture_paths["annotations"],
                   "--atoms", fixture_paths["atoms"],
                   "--clauses", fixture_paths["clauses"],
                   "--queries", fixture_paths["queries"],
                   "--dir", outdir, "--thresholds", thr])
    snap = snapshot.load_snapshot(os.path.join(outdir, "thr.json"))
    rec = snap["config"]["inputs"]["thresholds"]
    assert rec["path"] == os.path.basename(thr)
    assert snap["behaviours"]["beh-help"]["threshold"] == pytest.approx(0.9)


def test_noop_prose_acknowledges_null_equal_new_keys(fixture_paths):
    """First-customer finding (versioned-cut-2026-08-04, cosmetic): a no-op
    diff can pair an OLD-shape snapshot (no `thresholds` input key at all)
    with a NEW-shape one (`thresholds`: null) — the config identities are
    null-equal, not byte-identical, yet the prose claimed 'identical
    configuration shas'. It must acknowledge absent==null keys."""
    a = _build(fixture_paths, tag="a")
    b = _build(fixture_paths, tag="b")
    del a["config"]["inputs"]["thresholds"]      # the old shape
    d = snapshot.diff_snapshots(a, b)
    assert d["noop"] is True, \
        "an absent key vs an explicit null is the SAME configuration"
    text = snapshot.format_diff(d)
    assert ("identical configuration (allowing absent==null keys) "
            "and identical scores") in text


# ------------------------------------ frozen-thresholds gate (CYCLE5 item 6)

def test_assert_frozen_thresholds_passes_when_fully_frozen(fixture_paths,
                                                           tmp_path):
    """The gate helper the chain-audit / cycle-5 gate tests call: a snapshot
    whose every behaviour records threshold_source == 'frozen_artifact'
    passes silently."""
    thr = _thresholds_file(tmp_path, {"beh-help": 0.9})
    snap = snapshot.build_snapshot(
        "frozen-ok",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        thresholds_path=thr)
    path = snapshot.write_snapshot(snap, out_dir=str(tmp_path / "snaps"))
    snapshot.assert_frozen_thresholds(path)      # must not raise


def test_assert_frozen_thresholds_raises_on_old_shape(fixture_paths,
                                                      tmp_path):
    """A snapshot built WITHOUT the flag (no threshold_source key) silently
    re-derives every cut — the gate must raise naming the behaviours
    (CYCLE5_REVIEW.md item 6: 'fallback silently re-derives')."""
    snap = _build(fixture_paths, tag="old-shape")
    path = snapshot.write_snapshot(snap, out_dir=str(tmp_path / "snaps"))
    with pytest.raises(AssertionError, match="beh-help"):
        snapshot.assert_frozen_thresholds(path)


def test_assert_frozen_thresholds_raises_on_rule_fallback(fixture_paths,
                                                          tmp_path):
    """A partially-covering artifact leaves some behaviours on
    'rule_fallback' — exactly the drift the freeze exists to stop; the gate
    must raise naming them."""
    thr = _thresholds_file(tmp_path, {"some-other-behaviour": 0.5})
    snap = snapshot.build_snapshot(
        "partial",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"],
        thresholds_path=thr)
    path = snapshot.write_snapshot(snap, out_dir=str(tmp_path / "snaps"))
    with pytest.raises(AssertionError) as e:
        snapshot.assert_frozen_thresholds(path)
    assert "beh-help" in str(e.value)
    assert "rule_fallback" in str(e.value)


# -------------------------------------------------------------------- CLI

def test_cli_snapshot_then_diff(fixture_paths, tmp_path, capsys):
    """The two subcommands work end to end: snapshot writes
    snapshots/<tag>.json under --dir; diff on the two tags prints the no-op
    message and, with --json, writes a machine-readable diff."""
    outdir = str(tmp_path / "snaps")
    common = ["--annotations", fixture_paths["annotations"],
              "--atoms", fixture_paths["atoms"],
              "--clauses", fixture_paths["clauses"],
              "--queries", fixture_paths["queries"],
              "--dir", outdir]
    snapshot.main(["snapshot", "--tag", "one"] + common)
    snapshot.main(["snapshot", "--tag", "two"] + common)
    assert os.path.exists(os.path.join(outdir, "one.json"))
    assert os.path.exists(os.path.join(outdir, "two.json"))

    diff_json = str(tmp_path / "d.json")
    snapshot.main(["diff", "--a", "one", "--b", "two",
                   "--dir", outdir, "--json", diff_json])
    out = capsys.readouterr().out
    assert "no-op change" in out
    machine = json.load(open(diff_json))
    assert machine["noop"] is True


# --------------------------------------------- no-clobber (TOOLING item 2)

def _edit_annotations(fixture_paths):
    """A real input change: add an atom to c5, shifting the vocabulary."""
    edited = json.load(open(fixture_paths["annotations"]))
    edited["clauses"].append({"clause_id": "c5", "atoms": [
        {"name": "pastry_topic", "kind": "entity", "gloss": "a pastry"}]})
    with open(fixture_paths["annotations"], "w") as f:
        json.dump(edited, f)


def test_write_snapshot_refuses_clobber_with_different_bytes(fixture_paths,
                                                             tmp_path):
    """TOOLING_BATCH item 2: write_snapshot itself must refuse to overwrite
    snapshots/<tag>.json with DIFFERENT bytes — a bare CLI call could destroy
    a baseline another cycle's dossiers depend on (only cycle.py's driver
    refused tag reuse before this). The refusal names the tag and both shas;
    the existing file survives byte-identical."""
    outdir = str(tmp_path / "snaps")
    snapshot.write_snapshot(_build(fixture_paths, tag="frozen"),
                            out_dir=outdir)
    frozen_bytes = open(os.path.join(outdir, "frozen.json"), "rb").read()
    import hashlib
    old_sha = hashlib.sha256(frozen_bytes).hexdigest()

    _edit_annotations(fixture_paths)
    changed = _build(fixture_paths, tag="frozen")
    new_sha = hashlib.sha256(snapshot.snapshot_bytes(changed)).hexdigest()
    assert new_sha != old_sha, "fixture drifted: the edit must change bytes"
    with pytest.raises(SystemExit) as e:
        snapshot.write_snapshot(changed, out_dir=outdir)
    msg = str(e.value)
    assert "frozen" in msg
    assert old_sha in msg and new_sha in msg, \
        "the refusal must name BOTH shas"
    assert open(os.path.join(outdir, "frozen.json"), "rb").read() \
        == frozen_bytes, "the existing snapshot must survive untouched"


def test_write_snapshot_identical_rewrite_is_noop_success(fixture_paths,
                                                          tmp_path):
    """Identical bytes: silent no-op success — same path returned, same
    bytes on disk, no refusal."""
    outdir = str(tmp_path / "snaps")
    p1 = snapshot.write_snapshot(_build(fixture_paths, tag="same"),
                                 out_dir=outdir)
    before = open(p1, "rb").read()
    p2 = snapshot.write_snapshot(_build(fixture_paths, tag="same"),
                                 out_dir=outdir)
    assert p1 == p2
    assert open(p2, "rb").read() == before


def test_write_snapshot_force_overwrites_and_names_both_shas(fixture_paths,
                                                             tmp_path,
                                                             capsys):
    """--force is the only override (never used by the driver): the
    overwrite happens and BOTH shas are printed to stdout, so a forced
    clobber is always on the record."""
    outdir = str(tmp_path / "snaps")
    common = ["--annotations", fixture_paths["annotations"],
              "--atoms", fixture_paths["atoms"],
              "--clauses", fixture_paths["clauses"],
              "--queries", fixture_paths["queries"],
              "--dir", outdir]
    assert snapshot.main(["snapshot", "--tag", "t"] + common) == 0
    import hashlib
    old_sha = hashlib.sha256(
        open(os.path.join(outdir, "t.json"), "rb").read()).hexdigest()

    _edit_annotations(fixture_paths)
    # without --force the CLI must exit nonzero and leave the file alone
    with pytest.raises(SystemExit):
        snapshot.main(["snapshot", "--tag", "t"] + common)
    assert hashlib.sha256(
        open(os.path.join(outdir, "t.json"), "rb").read()).hexdigest() \
        == old_sha
    capsys.readouterr()
    assert snapshot.main(["snapshot", "--tag", "t", "--force"] + common) == 0
    new_sha = hashlib.sha256(
        open(os.path.join(outdir, "t.json"), "rb").read()).hexdigest()
    assert new_sha != old_sha, "--force must actually overwrite"
    out = capsys.readouterr().out
    assert old_sha in out and new_sha in out, \
        "a forced overwrite must print both shas"


# ------------------- patient pricing v2.0 wiring (patient-pricing cycle, S3)

def _queries_with_patients(tmp_path, patients, name="queries_p.json"):
    """The synthetic query file with a `patients` declaration on beh-help.
    Its definition says 'the model helps the user accomplish tasks', so
    ['user'] is anchor-licensed and ['third_party'] is not."""
    return _write(tmp_path / name, {"behaviours": [
        {"slug": "beh-help", "name": "Helpfulness",
         "definition": "the model helps the user accomplish tasks",
         "patients": patients},
    ]})


def test_patient_declarations_route_scoring_and_config_identity(
        fixture_paths, tmp_path):
    """The v2.0 seam (F9 ladder): overlay + non-empty validated patient
    declarations => the scorer is patient.PatientIndex and the config
    identity records pricing_version '2.0' plus the per-slug declared
    patients. Without the overlay the seam is closed (2.0 requires the 1.2
    join under it): no pricing_version key, no query_patients key."""
    patient = pytest.importorskip("patient")
    ov = _overlay_file(tmp_path)
    q = _queries_with_patients(tmp_path, ["user"])
    snap = snapshot.build_snapshot(
        "with-patients",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=q, overlay_path=ov)
    assert snap["config"]["pricing_version"] == patient.PRICING_VERSION
    assert snap["config"]["pricing_version"] == "2.0"
    assert snap["config"]["query_patients"] == {"beh-help": ["user"]}

    plain = snapshot.build_snapshot(
        "patients-no-overlay",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=q)
    assert "pricing_version" not in plain["config"]
    assert "query_patients" not in plain["config"]


def test_unlicensed_patient_declaration_refuses_snapshot_build(
        fixture_paths, tmp_path):
    """The anchor check runs INSIDE the build (validate_query is the named
    opt-in loader): an unlicensed declaration must refuse the snapshot
    loudly, naming the behaviour — never build with it silently dropped."""
    pytest.importorskip("patient")
    ov = _overlay_file(tmp_path)
    q = _queries_with_patients(tmp_path, ["third_party"])
    with pytest.raises(ValueError, match="beh-help"):
        snapshot.build_snapshot(
            "unlicensed",
            annotations_path=fixture_paths["annotations"],
            atoms_path=fixture_paths["atoms"],
            clauses_path=fixture_paths["clauses"],
            queries_path=q, overlay_path=ov)


def test_empty_patient_declarations_stay_pricing_1_2(fixture_paths, tmp_path):
    """patients [] disables pricing (patient.py I1): the build routes
    through ContainmentIndex, records containment.PRICING_VERSION, records
    NO query_patients key, and every behaviour section is identical to the
    no-declaration build under the same overlay."""
    containment = pytest.importorskip("containment")
    pytest.importorskip("patient")
    ov = _overlay_file(tmp_path)
    q = _queries_with_patients(tmp_path, [])
    snap = snapshot.build_snapshot(
        "empty-patients",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=q, overlay_path=ov)
    assert snap["config"]["pricing_version"] == containment.PRICING_VERSION
    assert "query_patients" not in snap["config"]
    bare = snapshot.build_snapshot(
        "no-declarations",
        annotations_path=fixture_paths["annotations"],
        atoms_path=fixture_paths["atoms"],
        clauses_path=fixture_paths["clauses"],
        queries_path=fixture_paths["queries"], overlay_path=ov)
    assert snap["behaviours"] == bare["behaviours"]


def test_diff_surfaces_pricing_version_and_query_patients_change():
    """THE BLOCKING PRECONDITION (CYCLE5_DESIGN §3 I5; standing cycle-3
    escalation (c)): a pricing_version or declared-patients change under
    identical inputs is THE cause of the diff and must appear in
    config.changed — and such a diff is never a no-op."""
    a = _hand_snapshot("a", ["c1"], {"c1": 0.5}, 0.2,
                       {"c1": {"lex": 0.1, "atom": 0.4}})
    b = _hand_snapshot("b", ["c1"], {"c1": 0.5}, 0.2,
                       {"c1": {"lex": 0.1, "atom": 0.4}})
    b["config"]["pricing_version"] = "2.0"
    b["config"]["query_patients"] = {"beh-x": ["third_party"]}
    d = snapshot.diff_snapshots(a, b)
    assert "pricing_version" in d["config"]["changed"]
    assert "query_patients" in d["config"]["changed"]
    assert d["noop"] is False
