"""The exclusion mechanism must REFUSE rather than guess.

An exclusion removes a module from the corpus every downstream stage reads, on
the strength of a verdict recorded about one artifact. If the artifact on disk
is not the one that was judged, dropping it anyway applies a verdict to
something nobody adjudicated -- which is the failure the mechanism exists to
prevent, committed by the mechanism itself. So every precondition gets a test
that it actually stops the read.
"""
import hashlib
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import corpus_exclusions as EX  # noqa: E402
import link_nodes as LN  # noqa: E402

CID = "l1108_1367_n014"
MARKER = ("permit", "generate_content(C)", "exploring_generation(C)")


# ----------------------------------------------------------------- live state

def test_the_live_table_verifies_against_the_bytes():
    """Not a count pin: whatever is in the table must justify itself."""
    excluded = EX.verified()
    assert excluded, "an empty exclusion table is a silent no-op"
    for (run, fname), (cid, _r, _sha, _m, why) in excluded.items():
        assert fname == cid + ".json"
        assert len(why) > 80, f"{cid} is excluded without stated grounds"


def test_the_erotica_gore_permission_is_out_of_the_corpus():
    assert CID not in LN.gather()


def test_the_evidence_is_still_on_disk_untouched():
    """The whole point: the verdict is honoured WITHOUT editing `runs/`."""
    entry = next(e for e in EX.EXCLUSIONS if e[0] == CID)
    p = EX._path(entry)
    assert os.path.isfile(p), "the excluded module's evidence was deleted"
    assert hashlib.sha256(open(p, "rb").read()).hexdigest() == entry[2]
    for ext in (".lp", ".transcript.json", ".raw.txt"):
        assert os.path.isfile(p[:-len(".json")] + ext), (
            f"{ext} sidecar missing -- exclusion must not touch evidence")


def test_the_module_really_did_carry_the_permission():
    """Guards against the table describing a defect the artifact lacks."""
    entry = next(e for e in EX.EXCLUSIONS if e[0] == CID)
    obj = json.load(open(EX._path(entry), encoding="utf-8"))
    status, act, body = MARKER
    assert any(a["status"] == status and a["act"] == act and a["body"] == body
               for a in obj["asserts"])
    assert obj["outcome"] == "translated"


# ------------------------------------------------------- precondition refusal

def _fake(tmp_path, monkeypatch, obj=None, sha=None, run="20260101-000000-x",
          cid=CID, write=True):
    """Plant a one-entry table over a throwaway runs/ tree."""
    rdir = tmp_path / "translation_sample" / "runs" / run
    rdir.mkdir(parents=True)
    obj = obj if obj is not None else {
        "outcome": "translated", "clause_id": cid,
        "asserts": [{"status": MARKER[0], "act": MARKER[1],
                     "body": MARKER[2]}]}
    raw = json.dumps(obj).encode("utf-8")
    if write:
        (rdir / (cid + ".json")).write_bytes(raw)
    monkeypatch.setattr(EX, "HERE", str(tmp_path))
    monkeypatch.setattr(EX, "EXCLUSIONS", [
        (cid, run, sha or hashlib.sha256(raw).hexdigest(), MARKER,
         "grounds recorded elsewhere; this is a test fixture " + "x" * 60)])
    return rdir


def test_a_verified_entry_is_returned(tmp_path, monkeypatch):
    _fake(tmp_path, monkeypatch)
    assert len(EX.verified()) == 1


def test_refuses_when_the_artifact_is_missing(tmp_path, monkeypatch):
    _fake(tmp_path, monkeypatch, write=False)
    with pytest.raises(SystemExit, match="no module at"):
        EX.verified()


def test_refuses_when_the_digest_does_not_match(tmp_path, monkeypatch):
    _fake(tmp_path, monkeypatch, sha="0" * 64)
    with pytest.raises(SystemExit, match="was recorded against"):
        EX.verified()


def test_refuses_when_the_adjudicated_assert_is_gone(tmp_path, monkeypatch):
    _fake(tmp_path, monkeypatch, obj={
        "outcome": "translated", "clause_id": CID,
        "asserts": [{"status": "forbid", "act": "generate_content(C)",
                     "body": "potentially_harmful_use(C)"}]})
    with pytest.raises(SystemExit, match="no longer carries the assert"):
        EX.verified()


def test_refuses_when_the_module_was_never_in_the_corpus(tmp_path, monkeypatch):
    _fake(tmp_path, monkeypatch, obj={
        "outcome": "abstained", "clause_id": CID, "asserts": []})
    with pytest.raises(SystemExit, match="not 'translated'"):
        EX.verified()


def test_refuses_when_a_verified_exclusion_never_applied():
    """version.py reports unused waivers loudly; same reason here."""
    with pytest.raises(SystemExit, match="never applied"):
        EX.assert_all_applied({("r", "f.json"): ()}, set())


def test_an_exclusion_is_keyed_to_one_artifact_not_to_the_clause_id(
        tmp_path, monkeypatch):
    """A LATER run's module for the same node must enter the corpus normally.

    An id-level ban would silently suppress a future CORRECT translation of the
    node, and nothing would report the suppression.
    """
    rdir = _fake(tmp_path, monkeypatch, run="20260101-000000-x")
    later = tmp_path / "translation_sample" / "runs" / "20260202-000000-y"
    later.mkdir(parents=True)
    good = {"outcome": "translated", "clause_id": CID, "asserts": []}
    (later / (CID + ".json")).write_bytes(json.dumps(good).encode())
    (later / (CID + ".lp")).write_text("% ok\n")
    (rdir / (CID + ".lp")).write_text("% bad\n")

    monkeypatch.setattr(LN, "RUNS", str(tmp_path / "translation_sample" / "runs"))
    sel = LN.gather()
    assert CID in sel, "the later, unjudged module was suppressed by id"
    assert sel[CID][2].endswith("20260202-000000-y")
