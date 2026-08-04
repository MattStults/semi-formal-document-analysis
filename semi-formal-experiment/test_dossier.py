"""Tests for dossier.py — one flip → one self-contained case file (Unit 2).

What is being pinned, and why each pin exists:

  * SELF-CONTAINEDNESS — the Haiku-operability contract is "dossier in →
    verdict out, no repo exploration required". So every field an adjudicator
    needs (behaviour definition, full clause text, atoms, deterministic
    read-back, explain() on both sides, scores/thresholds, what changed) must
    be present and non-empty on a real constructed flip. A dossier missing
    any of these silently reintroduces repo access as a dependency.
  * DETERMINISM — same two snapshots → byte-identical dossier files and index,
    matching Unit 1's contract (sorted keys, PRECISION-rounded numbers, no
    wall clock). A nondeterministic dossier makes the case bank undiffable.
  * BOTH DIRECTIONS — newly-predicted AND no-longer-predicted flips each get
    a dossier; a generator that only covers one direction hides regressions.
  * STALE-INPUT REFUSAL — a snapshot records the sha of every input; if a
    file on disk no longer matches, the dossier would pair yesterday's scores
    with today's clause text. That must FAIL LOUDLY, never dossier silently
    against the wrong artifacts.
  * VALIDATE — the verdict file is checked with check_taxonomy.py discipline:
    full coverage, no dupes, no unknown ids, closed verdict set, non-empty
    document_reason, honest summary. Each violation class is pinned
    separately so weakening one check fails one named test.

All fixtures are synthetic and tiny; the flip is forced by swapping the
behaviour-atoms file between the two snapshots (query atoms move from the
"help" family to the harm atom), which flips clauses in BOTH directions with
the label-free threshold recomputed on each side.
"""
from __future__ import annotations

import json
import os

import pytest

import dossier
import snapshot


# ------------------------------------------------------------- fixtures

def _write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)
    return str(path)


HU = {"name": "helping_user", "kind": "act", "gloss": "model helps the user"}
UT = {"name": "user_task", "kind": "situation", "gloss": "user has a task"}
AR = {"name": "assist_request", "kind": "act", "gloss": "a request is assisted"}
TP = {"name": "third_party_harm", "kind": "situation",
      "gloss": "someone outside the conversation is harmed"}


@pytest.fixture
def env(tmp_path):
    """Two snapshots over the same corpus whose diff flips in BOTH directions.

    Snapshot `a` queries the help-family atoms → predicts {c1, c6}.
    Snapshot `b` queries the harm atom → predicts {c2}.
    So the diff has newly_predicted [c2] and no_longer_predicted [c1, c6],
    with the config-sha diff naming `behaviour_atoms` as what changed.
    Verified against Unit 1 directly before these tests were written.
    """
    clauses = _write(tmp_path / "clauses.json", {"clauses": [
        {"id": "c1", "quote": "models must always help the user accomplish tasks",
         "section_path": ["help"], "locator": "L1", "kind": "norm"},
        {"id": "c2", "quote": "avoid causing harm to third parties in the world",
         "section_path": ["harm"], "locator": "L2", "kind": "norm"},
        {"id": "c3", "quote": "the weather in paris is mild during spring season",
         "section_path": ["misc"], "locator": "L3", "kind": "meta"},
        {"id": "c4", "quote": "helpful assistance benefits the user greatly indeed",
         "section_path": ["help"], "locator": "L4", "kind": "norm"},
        {"id": "c5", "quote": "pastry recipes require butter flour and sugar",
         "section_path": ["misc"], "locator": "L5", "kind": "meta"},
        {"id": "c6", "quote": "assist users helpfully with their many requests",
         "section_path": ["help"], "locator": "L6", "kind": "norm"},
    ]})
    ann = _write(tmp_path / "ann.json", {"clauses": [
        {"clause_id": "c1", "atoms": [HU, UT]},
        {"clause_id": "c4", "atoms": [HU, AR]},
        {"clause_id": "c6", "atoms": [HU, UT, AR]},
        {"clause_id": "c2", "atoms": [TP]},
    ]})
    atoms_a = _write(tmp_path / "atoms_a.json",
                     {"beh-help": {"atoms": [HU, UT, AR]}})
    atoms_b = _write(tmp_path / "atoms_b.json",
                     {"beh-help": {"atoms": [TP]}})
    queries = _write(tmp_path / "queries.json", {"behaviours": [
        {"slug": "beh-help", "name": "Helpfulness",
         "definition": "the model helps the user accomplish tasks"},
    ]})

    snap_dir = str(tmp_path / "snaps")
    for tag, atoms in (("a", atoms_a), ("b", atoms_b)):
        snap = snapshot.build_snapshot(
            tag, annotations_path=ann, atoms_path=atoms,
            clauses_path=clauses, queries_path=queries)
        snapshot.write_snapshot(snap, out_dir=snap_dir)
    return {"tmp": tmp_path, "snap_dir": snap_dir, "inputs_dir": str(tmp_path),
            "clauses": clauses, "ann": ann, "atoms_a": atoms_a,
            "atoms_b": atoms_b, "queries": queries}


def _build(env, **kw):
    return dossier.build_dossiers("a", "b", snap_dir=env["snap_dir"],
                                  inputs_dir=env["inputs_dir"], **kw)


# ---------------------------------------------------------- both directions

def test_both_flip_directions_get_dossiers(env):
    """Every flip in the diff — in EITHER direction — yields exactly one
    dossier, and the fixture's known flip set is reproduced."""
    ds = _build(env)
    by_dir = {}
    for d in ds:
        by_dir.setdefault(d["direction"], set()).add(d["clause"]["id"])
    assert by_dir.get("newly_predicted") == {"c2"}
    assert by_dir.get("no_longer_predicted") == {"c1", "c6"}
    assert len(ds) == 3
    assert len({d["flip_id"] for d in ds}) == 3


def test_behaviour_filter(env):
    """--behaviour restricts to that slug; an unknown slug yields nothing."""
    assert len(_build(env, behaviour="beh-help")) == 3
    assert _build(env, behaviour="no-such-behaviour") == []


# ------------------------------------------------------- self-containedness

def test_dossier_is_self_contained(env):
    """Every field an adjudicator needs, present and non-empty, with NO
    panel fields — no gold, no judges, no panel score."""
    ds = _build(env)
    newly = next(d for d in ds if d["direction"] == "newly_predicted")

    for d in ds:
        # identity
        assert d["flip_id"]
        assert d["tag_a"] == "a" and d["tag_b"] == "b"
        assert d["direction"] in ("newly_predicted", "no_longer_predicted")
        # behaviour: slug + definition + query atom names ON BOTH SIDES
        beh = d["behaviour"]
        assert beh["slug"] == "beh-help"
        assert beh["name"] and beh["definition"]
        assert beh["query_atoms_a"] == sorted(
            a["name"] for a in (HU, UT, AR))
        assert beh["query_atoms_b"] == ["third_party_harm"]
        # clause: id, FULL text, section path
        cl = d["clause"]
        assert cl["id"] and cl["text"] and cl["section_path"]
        assert cl["locator"]
        # the clause's atoms: name/kind/gloss/quote each present as keys
        for a in d["clause"]["atoms"]:
            assert set(a) >= {"name", "kind", "gloss", "quote"}
        # deterministic read-back rendering
        assert "THE INDEX RECORDS" in d["rendering"]
        # explain() under BOTH configurations
        for side in ("explain_a", "explain_b"):
            ex = d[side]
            assert ex["clause_id"] == cl["id"]
            assert "channels" in ex and "score" in ex
            assert set(ex["channels"]) == {"lex", "atom", "kind", "section"}
        # score/threshold before and after, and the moving channel
        for k in ("score_a", "score_b", "threshold_a", "threshold_b"):
            assert isinstance(d[k], (int, float))
        assert d["top_channel"] in ("lex", "atom", "kind", "section")
        # what changed between the configs (the Unit 1 config-sha diff)
        assert d["what_changed"]["inputs_changed"] == ["behaviour_atoms"]
        # PANEL-FREE: none of the case-file panel fields may appear
        assert "panel" not in d and "gold" not in d

    # content spot-checks on the known flip
    assert newly["clause"]["id"] == "c2"
    assert newly["clause"]["text"] == \
        "avoid causing harm to third parties in the world"
    assert newly["clause"]["section_path"] == ["harm"]
    atom_names = {a["name"] for a in newly["clause"]["atoms"]}
    assert "third_party_harm" in atom_names
    assert newly["score_b"] > newly["score_a"]


# ------------------------------------------------------------- determinism

def test_dossiers_byte_identical_across_writes(env, tmp_path):
    """Two independent generation passes → byte-identical dossier files AND
    byte-identical index, matching Unit 1's determinism contract."""
    out1 = str(tmp_path / "out1")
    out2 = str(tmp_path / "out2")
    p1 = dossier.write_dossiers(_build(env), out1)
    p2 = dossier.write_dossiers(_build(env), out2)
    assert [os.path.basename(p) for p in p1] == \
        [os.path.basename(p) for p in p2]
    for a, b in zip(sorted(p1), sorted(p2)):
        assert open(a, "rb").read() == open(b, "rb").read()
    idx1 = open(os.path.join(out1, "index.jsonl"), "rb").read()
    idx2 = open(os.path.join(out2, "index.jsonl"), "rb").read()
    assert idx1 == idx2 and idx1


def test_index_file_enumerates_work(env, tmp_path):
    """One line per dossier: flip_id, behaviour, clause id, direction."""
    out = str(tmp_path / "out")
    ds = dossier.build_dossiers("a", "b", snap_dir=env["snap_dir"],
                                inputs_dir=env["inputs_dir"])
    dossier.write_dossiers(ds, out)
    lines = [json.loads(l) for l in
             open(os.path.join(out, "index.jsonl")) if l.strip()]
    assert len(lines) == len(ds)
    for line in lines:
        assert set(line) == {"flip_id", "behaviour", "clause_id", "direction"}
    assert {l["flip_id"] for l in lines} == {d["flip_id"] for d in ds}


# ------------------------------------------------------ stale-input refusal

def test_stale_input_fails_loudly_not_wrong_dossiers(env):
    """If an input file changed on disk since the snapshot (sha mismatch),
    building dossiers must raise — with the file named — rather than pair
    frozen scores with drifted artifacts."""
    edited = json.load(open(env["ann"]))
    edited["clauses"].append({"clause_id": "c5", "atoms": [
        {"name": "novel_pastry_atom", "kind": "entity", "gloss": "a pastry"}]})
    _write(env["tmp"] / "ann.json", edited)   # overwrite IN PLACE
    with pytest.raises(dossier.StaleConfigError) as e:
        _build(env)
    msg = str(e.value)
    assert "ann.json" in msg and "sha" in msg.lower()


def test_zero_flips_needs_no_reconstruction_so_staleness_is_moot(env, tmp_path):
    """⚠️ Found by the chain-repair cycle (2026-08-04): an ARTIFACT-fix cycle
    changes its annotations file BY DEFINITION, so the baseline snapshot's
    recorded sha can never match disk at MEASURE time — and the staleness
    guard fired before the flip count was consulted, blocking even the
    zero-flip case where there is nothing to reconstruct and staleness is
    moot. Order: count flips first; only a non-empty flip set requires
    reconstruction (and may therefore refuse on staleness)."""
    import copy
    a = snapshot.load_snapshot(os.path.join(env["snap_dir"], "a.json"))
    b = copy.deepcopy(a)
    b["tag"] = "b2"
    # a config-identity change with IDENTICAL scores/cuts -> zero flips
    b["config"]["inputs"]["annotations"] = dict(
        b["config"]["inputs"]["annotations"],
        sha256="0" * 64)
    sd = tmp_path / "snaps2"; sd.mkdir()
    for s in (a, b):
        snapshot.write_snapshot(s, out_dir=str(sd))
    # drift the A-side artifact on disk so _side would refuse if reached
    edited = json.load(open(env["ann"]))
    edited["clauses"].append({"clause_id": "c9", "atoms": []})
    _write(env["tmp"] / "ann.json", edited)
    ds = dossier.build_dossiers("a", "b2", snap_dir=str(sd),
                                inputs_dir=str(env["tmp"]))
    assert ds == []   # empty flip set returned, no StaleConfigError


# ------------------------------------------------------------- empty diff

def test_empty_diff_says_so_explicitly(env, tmp_path, capsys):
    """A self-diff (no flips) must produce an EXPLICIT no-flips message and
    an empty index, not silently write nothing."""
    # second tag over identical inputs → no flips
    snap = snapshot.build_snapshot(
        "a2", annotations_path=env["ann"], atoms_path=env["atoms_a"],
        clauses_path=env["clauses"], queries_path=env["queries"])
    snapshot.write_snapshot(snap, out_dir=env["snap_dir"])
    out = str(tmp_path / "out")
    rc = dossier.main(["dossiers", "--a", "a", "--b", "a2",
                       "--snap-dir", env["snap_dir"],
                       "--inputs-dir", env["inputs_dir"],
                       "--out-dir", out])
    assert rc == 0
    assert "no flips" in capsys.readouterr().out.lower()
    idx = os.path.join(out, "index.jsonl")
    assert os.path.exists(idx) and open(idx).read() == ""


# ------------------------------------------------------------- flip causes

def test_dossier_carries_flip_cause(env):
    """Every dossier carries the diff's `cause` tag, from the closed set —
    the adjudicator's question depends on it (ITERATION_LOOP.md policy §3)."""
    for d in _build(env):
        assert d["cause"] in ("match_change", "threshold_drift", "both")


def test_threshold_drift_flip_tagged_and_shown_in_dossier(env, monkeypatch):
    """The review's real case class, end to end: identical inputs, identical
    scores, but the cut moved (here: a simulated code-level threshold change,
    the class format_diff calls 'a code-level change moved the scores'). The
    flips must tag `threshold_drift` and their dossiers must show it."""
    import threshold as threshold_rules
    monkeypatch.setattr(threshold_rules, "apply_rule",
                        lambda rule, xs: 0.0001)
    snap = snapshot.build_snapshot(
        "bdrift", annotations_path=env["ann"], atoms_path=env["atoms_a"],
        clauses_path=env["clauses"], queries_path=env["queries"])
    snapshot.write_snapshot(snap, out_dir=env["snap_dir"])
    monkeypatch.undo()

    ds = dossier.build_dossiers("a", "bdrift", snap_dir=env["snap_dir"],
                                inputs_dir=env["inputs_dir"])
    newly = [d for d in ds if d["direction"] == "newly_predicted"]
    assert newly, "fixture drifted: the lowered cut must admit new clauses"
    for d in newly:
        assert snapshot._r(d["score_a"]) == snapshot._r(d["score_b"])
        assert d["threshold_a"] != d["threshold_b"]
        assert d["cause"] == "threshold_drift"


# ---------------------------------------------------- overlay reconstruction

PM = {"name": "psychological_manipulation", "kind": "act",
      "gloss": "manipulating a mind"}
TPM = {"name": "targeted_political_manipulation", "kind": "act",
       "gloss": "targeted political manipulation of groups"}
# The subsumer as a REAL clause-side atom (kind "act"): since the 2026-08-03
# review fixes, a latent subsumer's credit carries the kind-mismatch discount,
# which on this tiny corpus prices c2 below the Otsu cut. Attesting the parent
# on c2 keeps the fixture's flip (kind agreement verified against a real
# subsumer -> full credit) without weakening the flip assertion below.
MAN = {"name": "manipulation", "kind": "act",
       "gloss": "influence exerted covertly over a person"}


@pytest.fixture
def overlay_env(tmp_path):
    """Snapshot `a` plain, snapshot `b` under a containment overlay whose
    subsumption credit flips c2 in (and, via the recomputed Otsu cut, c1/c5
    out). Verified against Unit 1 directly before these tests were written.
    This is the review's exact case class: an honest overlay snapshot whose
    dossiers, rebuilt through a PLAIN index, silently contradict the frozen
    numbers."""
    clauses = _write(tmp_path / "clauses.json", {"clauses": [
        {"id": "c1", "quote": "models must always help the user accomplish tasks",
         "section_path": ["help"], "locator": "L1", "kind": "norm"},
        {"id": "c2", "quote": "never manipulate the political views of groups",
         "section_path": ["harm"], "locator": "L2", "kind": "norm"},
        {"id": "c3", "quote": "the weather in paris is mild during spring season",
         "section_path": ["misc"], "locator": "L3", "kind": "meta"},
        {"id": "c4", "quote": "pastry recipes require butter flour and sugar",
         "section_path": ["misc"], "locator": "L4", "kind": "meta"},
        {"id": "c5", "quote": "the model helps people with their user tasks",
         "section_path": ["help"], "locator": "L5", "kind": "norm"},
    ]})
    ann = _write(tmp_path / "ann.json", {"clauses": [
        {"clause_id": "c1", "atoms": [HU]},
        {"clause_id": "c2", "atoms": [TPM, MAN]},
        {"clause_id": "c5", "atoms": [HU]},
    ]})
    atoms = _write(tmp_path / "atoms.json",
                   {"beh-manip": {"atoms": [PM, HU]}})
    queries = _write(tmp_path / "queries.json", {"behaviours": [
        {"slug": "beh-manip", "name": "Manipulation avoidance",
         "definition": "the model avoids manipulating people"}]})
    overlay = _write(tmp_path / "ov.json", {
        "artifact": "containment", "version": "v0",
        "budget": {"max_edges": 2, "max_families": 1},
        "edges": [
            {"child": "psychological_manipulation", "parent": "manipulation",
             "license": "shared_head", "note": "t"},
            {"child": "targeted_political_manipulation",
             "parent": "manipulation", "license": "shared_head", "note": "t"}],
        "provenance": {"origin": "test"}})

    snap_dir = str(tmp_path / "snaps")
    a = snapshot.build_snapshot("a", annotations_path=ann, atoms_path=atoms,
                                clauses_path=clauses, queries_path=queries)
    b = snapshot.build_snapshot("b", annotations_path=ann, atoms_path=atoms,
                                clauses_path=clauses, queries_path=queries,
                                overlay_path=overlay)
    snapshot.write_snapshot(a, out_dir=snap_dir)
    snapshot.write_snapshot(b, out_dir=snap_dir)
    d = snapshot.diff_snapshots(a, b)
    flips = d["behaviours"]["beh-manip"]
    assert {f["clause_id"] for f in flips["newly_predicted"]} == {"c2"}, \
        "fixture drifted: the overlay must flip c2 in"
    return {"tmp": tmp_path, "snap_dir": snap_dir,
            "inputs_dir": str(tmp_path)}


def test_overlay_dossier_explain_matches_frozen_scores(overlay_env):
    """An overlay snapshot's dossiers must be rebuilt through the RECORDED
    overlay (ContainmentIndex with the sha-verified edge file), so the
    reconstructed explain score equals the frozen score on every flip — the
    review found a plain-index rebuild silently contradicting score_b on
    every honest overlay dossier."""
    ds = dossier.build_dossiers("a", "b", snap_dir=overlay_env["snap_dir"],
                                inputs_dir=overlay_env["inputs_dir"])
    assert ds, "fixture drifted: expected flips"
    for d in ds:
        for side, key in (("a", "score_a"), ("b", "score_b")):
            ex = d[f"explain_{side}"]
            assert ex, f"missing explain_{side} on {d['flip_id']}"
            assert snapshot._r(ex["score"]) == snapshot._r(d[key]), (
                f"{d['flip_id']} side {side}: reconstructed explain score "
                f"{ex['score']} contradicts frozen {d[key]}")


def test_reconstruction_mismatch_raises_loudly(overlay_env):
    """A hand-edited snapshot must be self-exposing: if a frozen score cannot
    be reproduced by the recorded configuration, building dossiers raises —
    naming clause, side, and both numbers — instead of shipping a
    self-contradictory case file."""
    path = os.path.join(overlay_env["snap_dir"], "b.json")
    snap = json.load(open(path))
    beh = snap["behaviours"]["beh-manip"]
    beh["scores"]["c2"] = 0.987654321  # tampered; stays predicted
    with open(path, "wb") as f:
        f.write(snapshot.snapshot_bytes(snap))
    with pytest.raises(dossier.ReconstructionMismatch) as e:
        dossier.build_dossiers("a", "b", snap_dir=overlay_env["snap_dir"],
                               inputs_dir=overlay_env["inputs_dir"])
    msg = str(e.value)
    assert "c2" in msg and "b" in msg
    assert "0.987654321" in msg


# ------------------------------------------------------------------ CLI

def test_cli_dossiers_end_to_end(env, tmp_path, capsys):
    """The dossiers subcommand writes one JSON per flip plus the index."""
    out = str(tmp_path / "out")
    rc = dossier.main(["dossiers", "--a", "a", "--b", "b",
                       "--snap-dir", env["snap_dir"],
                       "--inputs-dir", env["inputs_dir"],
                       "--out-dir", out])
    assert rc == 0
    files = sorted(os.listdir(out))
    assert "index.jsonl" in files
    dossier_files = [f for f in files if f != "index.jsonl"]
    assert len(dossier_files) == 3
    loaded = json.load(open(os.path.join(out, dossier_files[0])))
    assert "flip_id" in loaded and "rendering" in loaded


# --------------------------------------------------------------- validate

def _verdict(fid, value="correct", reason="the clause plainly concerns "
             "third-party harm, the behaviour's subject matter"):
    return {"flip_id": fid, "verdict": value, "document_reason": reason,
            "confidence": "high"}


@pytest.fixture
def adjudication_env(env, tmp_path):
    out = str(tmp_path / "dossier_out")
    ds = dossier.build_dossiers("a", "b", snap_dir=env["snap_dir"],
                                inputs_dir=env["inputs_dir"])
    dossier.write_dossiers(ds, out)
    return {"dir": out, "flip_ids": sorted(d["flip_id"] for d in ds),
            "tmp": tmp_path}


def test_validate_happy_path(adjudication_env, capsys):
    """A complete, well-formed verdict file validates clean."""
    e = adjudication_env
    vfile = _write(e["tmp"] / "v.json",
                   [_verdict(f) for f in e["flip_ids"]])
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is True
    assert summary["adjudicated"] == len(e["flip_ids"])
    assert "clean" in capsys.readouterr().out


def test_validate_catches_missing_flip(adjudication_env):
    e = adjudication_env
    vfile = _write(e["tmp"] / "v.json",
                   [_verdict(f) for f in e["flip_ids"][1:]])
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is False
    assert e["flip_ids"][0] in summary["never_adjudicated"]


def test_validate_catches_duplicate(adjudication_env):
    e = adjudication_env
    records = [_verdict(f) for f in e["flip_ids"]]
    records.append(_verdict(e["flip_ids"][0], value="regression"))
    vfile = _write(e["tmp"] / "v.json", records)
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is False
    assert e["flip_ids"][0] in summary["duplicated"]


def test_validate_catches_unknown_id(adjudication_env):
    e = adjudication_env
    records = [_verdict(f) for f in e["flip_ids"]] + [_verdict("bogus__id")]
    vfile = _write(e["tmp"] / "v.json", records)
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is False
    assert "bogus__id" in summary["unknown"]


def test_validate_catches_bad_verdict_value(adjudication_env):
    e = adjudication_env
    records = [_verdict(f) for f in e["flip_ids"]]
    records[0] = _verdict(e["flip_ids"][0], value="looks-fine-to-me")
    vfile = _write(e["tmp"] / "v.json", records)
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is False
    assert e["flip_ids"][0] in summary["bad_verdict"]


def test_validate_catches_empty_reason(adjudication_env):
    e = adjudication_env
    records = [_verdict(f) for f in e["flip_ids"]]
    records[0] = _verdict(e["flip_ids"][0], reason="   ")
    vfile = _write(e["tmp"] / "v.json", records)
    ok, summary = dossier.validate(e["dir"], vfile)
    assert ok is False
    assert e["flip_ids"][0] in summary["empty_reason"]


def test_cli_validate_exit_codes(adjudication_env):
    """The validate subcommand exits 0 clean, nonzero on any violation."""
    e = adjudication_env
    good = _write(e["tmp"] / "good.json",
                  [_verdict(f) for f in e["flip_ids"]])
    bad = _write(e["tmp"] / "bad.json",
                 [_verdict(f) for f in e["flip_ids"][1:]])
    assert dossier.main(["validate", "--dir", e["dir"],
                         "--verdict-file", good]) == 0
    assert dossier.main(["validate", "--dir", e["dir"],
                         "--verdict-file", bad]) != 0


# ----------------------- verdict-loader tolerance, PINNED (TOOLING item 5)

def test_verdict_loader_accepted_shapes_pinned(tmp_path):
    """The loader's tolerance is a CONTRACT, not an accident: a bare list,
    the conventional single-key dict, and a single-list-valued key of ANY
    name all load to the same records. A well-meaning cleanup that narrows
    this orphans every historical adjudication artifact — this test is the
    tripwire."""
    records = [{"flip_id": "f1", "verdict": "correct", "document_reason": "r"}]
    for i, shape in enumerate((
            records,                                # bare list
            {"records": records},                   # the driver's spelling
            {"anything_at_all": records},           # any single list key
            {"note": "prose", "items": records},    # non-list keys ignored
    )):
        p = _write(tmp_path / f"shape{i}.json", shape)
        assert dossier._load_verdict_records(p) == records, f"shape {i}"


def test_verdict_loader_no_list_anywhere_yields_no_records(tmp_path):
    """A dict with no list under any key loads as ZERO records (pinned
    current behavior) — validate then reports every dossier
    never-adjudicated rather than guessing at a shape."""
    p = _write(tmp_path / "nolist.json", {"note": "prose", "n": 3})
    assert dossier._load_verdict_records(p) == []


def test_verdict_loader_refuses_two_candidate_lists(tmp_path):
    """AMBIGUITY MUST REFUSE, NOT GUESS (TOOLING item 5): a dict holding TWO
    list-valued keys has no principled winner; silently taking the first
    sorted key could validate the wrong record set as clean."""
    p = _write(tmp_path / "two.json", {
        "alpha": [{"flip_id": "f1"}], "beta": [{"flip_id": "f2"}]})
    with pytest.raises(ValueError) as e:
        dossier._load_verdict_records(p)
    msg = str(e.value)
    assert "alpha" in msg and "beta" in msg, \
        "the refusal must name the competing keys"


def test_the_two_validators_keep_their_distinct_flag_spellings(capsys):
    """Amendment F9 hardcodes that the two validators keep their DIFFERING
    flags — dossier.py's is --verdict-file, audit_disagreements' is
    --verdicts — because cycle.py invokes both by exact spelling. Pinned by
    argparse introspection: harmonizing either breaks the driver."""
    import audit_disagreements

    with pytest.raises(SystemExit) as e:
        dossier.main(["validate", "--help"])
    assert e.value.code == 0
    dossier_help = capsys.readouterr().out
    assert "--verdict-file" in dossier_help
    assert "--verdicts " not in dossier_help and \
        "--verdicts\n" not in dossier_help

    import sys as _sys
    old = _sys.argv
    try:
        _sys.argv = ["audit_disagreements.py", "validate", "--help"]
        with pytest.raises(SystemExit) as e2:
            audit_disagreements.main()
        assert e2.value.code == 0
    finally:
        _sys.argv = old
    audit_help = capsys.readouterr().out
    assert "--verdicts" in audit_help
    assert "--verdict-file" not in audit_help


# ---------------- A-side reconstruction from a logged migration (item 3)

import hashlib as _hashlib
import subprocess as _subprocess


def _sha(path):
    return _hashlib.sha256(open(path, "rb").read()).hexdigest()


def _git(env, *args):
    return _subprocess.run(
        ["git", "-C", str(env["tmp"]), "-c", "user.email=t@t",
         "-c", "user.name=t"] + list(args),
        capture_output=True, text=True, check=True)


def _apply_logged_rename(env, sha_after_override=None):
    """Rewrite helping_user -> assisting_user in ann.json IN PLACE and log
    it in vocabulary_migrations.json exactly as atom_refactor logs one
    (per-artifact sha_before/sha_after chain). Returns (old_sha, new_sha)."""
    old_sha = _sha(env["ann"])
    raw = open(env["ann"]).read()
    edited = raw.replace("helping_user", "assisting_user")
    assert edited != raw, "fixture drifted: the rename must change bytes"
    with open(env["ann"], "w") as f:
        f.write(edited)
    new_sha = _sha(env["ann"])
    log = {"artifact": "vocabulary_migrations", "version": 1,
           "migrations": [{
               "op": "rename", "old": "helping_user",
               "new": "assisting_user", "date": "2026-08-04",
               "reason": "test: reconstruction fixture",
               "artifacts": {"ann.json": {
                   "sha_before": old_sha,
                   "sha_after": (sha_after_override or new_sha),
                   "n_rewritten": 3}}}]}
    _write(env["tmp"] / "vocabulary_migrations.json", log)
    return old_sha, new_sha


def test_logged_migration_reconstructs_from_git_history(env):
    """TOOLING item 3 + F12: after an artifact cycle rewrote the
    annotations in place (sha logged in vocabulary_migrations.json), the
    baseline side must reconstruct its recorded input from git history —
    sha-verified — instead of refusing forever. The dossier records
    reconstruction provenance; the build stays byte-deterministic."""
    _git(env, "init", "-q")
    _git(env, "add", "ann.json")
    _git(env, "commit", "-qm", "pre-change ann")
    old_sha, _ = _apply_logged_rename(env)

    ds = _build(env)
    assert len(ds) == 3, "the fixture's flip set must survive reconstruction"
    for d in ds:
        rec = d["reconstruction"]
        for side in ("a", "b"):     # BOTH snapshots recorded the old sha
            r = rec[side]["annotations"]
            assert r["source"] == "git_history"
            assert r["recorded_sha256"] == old_sha
            assert r["migrations_spanned"] == [
                {"op": "rename", "old": "helping_user",
                 "new": "assisting_user", "date": "2026-08-04"}]
    # determinism: a second build serializes byte-identically
    again = _build(env)
    assert [snapshot.snapshot_bytes(d) for d in ds] == \
        [snapshot.snapshot_bytes(d) for d in again]


def test_prechange_copy_is_the_nongit_fallback(env):
    """No git history: a cycle's pre_change/ copy (captured at MEASURE) is
    the fallback source, still sha-verified."""
    original = open(env["ann"], "rb").read()
    _apply_logged_rename(env)
    pc = env["tmp"] / "cycles" / "prior" / "pre_change"
    os.makedirs(pc)
    with open(pc / "ann.json", "wb") as f:
        f.write(original)
    ds = _build(env)
    assert len(ds) == 3
    assert ds[0]["reconstruction"]["a"]["annotations"]["source"] \
        == "pre_change_copy"


def test_unlogged_mutation_still_refuses(env):
    """Reconstruction never launders corruption: a sha absent from the
    migration chain remains a hard StaleConfigError even with the log
    present."""
    _apply_logged_rename(env, sha_after_override="f" * 64)  # chain broken
    with pytest.raises(dossier.StaleConfigError):
        _build(env)


def test_missing_sources_error_names_both(env):
    """A LOGGED migration whose pre-change bytes exist in neither git
    history nor any pre_change copy gets a DISTINCT refusal naming both
    searched sources."""
    _apply_logged_rename(env)          # no git repo, no pre_change copy
    with pytest.raises(dossier.StaleConfigError) as e:
        _build(env)
    msg = str(e.value)
    assert "git history" in msg and "pre_change" in msg, msg


# ---------------- F9 dispatch ladder + normalizer_drift (S3 patient cycle)

def _empty_overlay_file(tmp_path):
    p = str(tmp_path / "overlay_empty_t.json")
    with open(p, "w") as f:
        json.dump({"artifact": "containment", "version": "v0",
                   "budget": {"max_edges": 0, "max_families": 0},
                   "edges": [], "provenance": {"origin": "test"}}, f)
    return p


def test_index_dispatch_ladder_absent_12_and_20(env, tmp_path):
    """THE F9 LADDER (F6: absent is a DEFINED dispatch value = legacy):
    _index_for routes a config with pricing_version '2.0' through
    patient.PatientIndex carrying exactly the RECORDED declared patients;
    an overlay without '2.0' through ContainmentIndex; and neither through
    the legacy relevance.RelevanceIndex — never a KeyError."""
    import relevance
    containment = pytest.importorskip("containment")
    patient = pytest.importorskip("patient")
    paths = {"clauses": env["clauses"], "annotations": env["ann"]}
    # absent => legacy, exactly
    legacy = dossier._index_for({"config": {}}, paths)
    assert type(legacy) is relevance.RelevanceIndex
    # overlay without a version => the 1.2 containment class
    ov = _empty_overlay_file(tmp_path)
    p2 = dict(paths, overlay=ov)
    mid = dossier._index_for({"config": {"pricing_version": "1.2"}}, p2)
    assert type(mid) is containment.ContainmentIndex
    # 2.0 => PatientIndex with the RECORDED patients (not the live file's)
    snap = {"config": {"pricing_version": "2.0",
                       "query_patients": {"beh-help": ["user"]}}}
    top = dossier._index_for(snap, p2)
    assert type(top) is patient.PatientIndex
    assert top.query_patients == {"beh-help": frozenset({"user"})}


def test_real_cycle4_keep_snapshot_has_no_pricing_version_key():
    """The F6 pin against the REAL cycle-4 keep snapshot: it predates the
    overlay versioning and carries NO pricing_version key — 'absent' must
    stay a defined legacy dispatch value forever, so this fact is pinned
    where the dispatch test above can be read next to it."""
    real = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "snapshots", "versioned-cut-2026-08-04.json")
    if not os.path.exists(real):
        pytest.skip("real cycle-4 snapshot not present")
    snap = snapshot.load_snapshot(real)
    assert "pricing_version" not in snap["config"]
    assert snap["config"]["inputs"]["overlay"] is None


def test_cycle_declared_change_licenses_reconstruction(env):
    """THE SECOND RECONSTRUCTION LICENSE (S3): a baseline input that drifted
    because a CYCLE's declared diff changed it — the manifest names the file
    in files_to_change and the cycle's state.json open_shas records exactly
    the baseline's sha — is a licensed, recorded provenance, parallel to the
    migration-log license (which only atom_refactor rename/rechain ops can
    produce; a field addition like the S3 patients declarations never can).
    The bytes still come only from git history / a pre_change copy, sha-
    verified; the license never launders an UNRECORDED drift (control arm:
    without the cycle record the build still refuses)."""
    import hashlib
    q = env["queries"]
    with open(q, "rb") as f:
        old_bytes = f.read()
    old_sha = hashlib.sha256(old_bytes).hexdigest()
    # the declared change lands AFTER both snapshots were built
    doc = json.loads(old_bytes)
    doc["behaviours"][0]["patients"] = ["user"]
    with open(q, "w") as f:
        json.dump(doc, f)
    # control: an undeclared drift refuses exactly as before
    with pytest.raises(dossier.StaleConfigError):
        _build(env)
    # the cycle record: manifest declares the file, open_shas pins the
    # baseline sha, pre_change/ holds the recorded bytes (no git repo here)
    cdir = env["tmp"] / "cycles" / "test-cycle"
    os.makedirs(cdir / "pre_change", exist_ok=True)
    _write(cdir / "manifest.json",
           {"cycle_name": "test-cycle",
            "files_to_change": ["queries.json"]})
    with open(cdir / "pre_change" / "queries.json", "wb") as f:
        f.write(old_bytes)
    # second control: the DECLARATION ALONE does not license — the cycle's
    # open_shas must pin EXACTLY the baseline sha (a sha-blind license
    # would let any cycle that ever declared the file launder any drift)
    _write(cdir / "state.json",
           {"open_shas": {"queries.json": "0" * 64}})
    with pytest.raises(dossier.StaleConfigError):
        _build(env)
    _write(cdir / "state.json", {"open_shas": {"queries.json": old_sha}})
    ds = _build(env)
    assert ds, "no dossiers built"
    recs = [d.get("reconstruction") for d in ds if d.get("reconstruction")]
    assert recs, "reconstruction provenance missing from the dossiers"
    for rec in recs:
        # both sides recorded the pre-change queries sha, so both carry it
        for side in rec.values():
            r = side.get("queries") or {}
            assert r.get("source") == "pre_change_copy"
            lic = r.get("license") or {}
            assert lic.get("kind") == "cycle_declared_change"
            assert lic.get("cycle") == "test-cycle"


def test_normalizer_drift_rule_truth_table():
    """The amended-I2 rule (CYCLE5_DESIGN §3 I2/F3): a flip whose RAW score
    did not move in the flip's own direction crossed the cut on the
    NORMALIZED surface only — threshold-class, never match_change."""
    assert dossier._normalizer_drift("newly_predicted", 1.0, 1.0)
    assert dossier._normalizer_drift("newly_predicted", 1.0, 0.9)
    assert not dossier._normalizer_drift("newly_predicted", 1.0, 1.1)
    assert dossier._normalizer_drift("no_longer_predicted", 1.0, 1.0)
    assert dossier._normalizer_drift("no_longer_predicted", 1.0, 1.1)
    assert not dossier._normalizer_drift("no_longer_predicted", 1.0, 0.9)
    assert not dossier._normalizer_drift("newly_predicted", None, 1.0)


def test_normalizer_drift_annotation_lands_in_the_dossier(env, monkeypatch):
    """The dossier wiring is load-bearing: when the rule fires, the dossier
    carries {normalizer_drift: {raw_a, raw_b}} with the SNAPSHOTS' recorded
    raw values; when it does not fire, the key is ABSENT (pre-existing
    dossier bytes stay stable). Both directions pinned via a forced rule."""
    ds = _build(env)
    assert all("normalizer_drift" not in d for d in ds), (
        "fixture flips are genuine query-side match changes — the "
        "annotation must not fire on them")
    monkeypatch.setattr(dossier, "_normalizer_drift",
                        lambda direction, ra, rb: True)
    forced = _build(env)
    for d in forced:
        nd = d.get("normalizer_drift")
        assert nd is not None and set(nd) == {"raw_a", "raw_b"}
