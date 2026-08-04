"""Tests for cycle.py — the cycle driver, per CYCLE_DESIGN.md INCLUDING the
2026-08-04 BINDING AMENDMENTS:

  * default cycle shape "code" has NO census phase (census deferred to
    checkpoint cycles; the default path never touches audit_disagreements);
  * PREDICT's required targets are mechanism-level (flip count / direction /
    clauses / adjudication expectations), census classes optional and
    checked only in checkpoint cycles (stamped DEV);
  * manifest AND prediction shas freeze at PREDICT; manifest edits only via
    a loud amendment artifact; PREDICT override demotes to exploratory;
    ADJUDICATE and DECIDE are non-overridable;
  * two-sided one-variable check (declared files changed, sha-pinned closure
    of undeclared inputs unchanged);
  * flip budget (>30 halts with the policy §4 split/stratify template);
  * verdict binding via dossier_set_sha echo + snapshot tag immutability.

Unit tests MOCK the heavy tools: every external invocation goes through
`cycle._run`, replaced here by a FakeRun that simulates each tool's on-disk
effect. One integration-ish test drives a full cycle end-to-end on the same
synthetic fixtures with stub seat outputs.

Registered in conftest._OPTIONAL, like every optional test module.
"""
from __future__ import annotations

import json
import os

import pytest

import cycle


# ------------------------------------------------------------------ fixtures

class FakeRun:
    """Stands in for cycle._run: records calls, simulates tool side effects.

    Knobs: pytest_rc (gate tests), diff (the machine diff snapshot.py would
    write), flips (index records dossier.py dossiers would write),
    census_index (index records audit_disagreements dossiers would write),
    validate_rc / audit_validate_rc (the two validators).
    """

    def __init__(self):
        self.calls = []
        self.pytest_rc = 0
        self.diff = None
        self.flips = []
        self.census_index = []
        self.validate_rc = 0
        self.audit_validate_rc = 0

    def _arg(self, argv, flag):
        argv = [str(a) for a in argv]
        return argv[argv.index(flag) + 1] if flag in argv else None

    def __call__(self, argv, cwd=None):
        self.calls.append([str(a) for a in argv])
        s = [str(a) for a in argv]
        if "pytest" in s:
            if self.pytest_rc:
                raise cycle.ToolFailed("gate tests failed", self.pytest_rc)
            return
        script = os.path.basename(s[1]) if len(s) > 1 else ""
        sub = s[2] if len(s) > 2 else ""
        if script == "snapshot.py" and sub == "snapshot":
            tag = self._arg(argv, "--tag")
            d = self._arg(argv, "--dir")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, tag + ".json"), "w") as f:
                json.dump({"tag": tag}, f)
            return
        if script == "snapshot.py" and sub == "diff":
            out = self._arg(argv, "--json")
            with open(out, "w") as f:
                json.dump(self.diff, f, sort_keys=True, indent=1)
                f.write("\n")
            return
        if script == "dossier.py" and sub == "dossiers":
            out_dir = self._arg(argv, "--out-dir")
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "index.jsonl"), "w") as f:
                for rec in self.flips:
                    f.write(json.dumps(rec, sort_keys=True) + "\n")
            return
        if script == "dossier.py" and sub == "validate":
            assert "--verdict-file" in s, \
                "dossier.py's flag is --verdict-file (never harmonize, F9)"
            if self.validate_rc:
                raise cycle.ToolFailed("flip verdicts invalid",
                                       self.validate_rc)
            return
        if script == "audit_disagreements.py" and sub == "dossiers":
            out_root = self._arg(argv, "--out-root")
            tag = "test__test"
            d = os.path.join(out_root, tag)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.jsonl"), "w") as f:
                for rec in self.census_index:
                    f.write(json.dumps(rec, sort_keys=True) + "\n")
            return
        if script == "audit_disagreements.py" and sub == "validate":
            assert "--verdicts" in s, \
                "audit_disagreements' flag is --verdicts (F9)"
            if self.audit_validate_rc:
                raise cycle.ToolFailed("census verdicts invalid",
                                       self.audit_validate_rc)
            return
        raise AssertionError(f"FakeRun: unexpected command {s}")


NOOP_DIFF = {"noop": True, "behaviours": {}}

FLIP_DIFF = {
    "noop": False,
    "behaviours": {
        "beh-a": {"newly_predicted": [{"clause_id": "m1"}],
                  "no_longer_predicted": []},
    },
}

BIG_DIFF = {
    "noop": False,
    "behaviours": {
        "beh-a": {"newly_predicted": [{"clause_id": f"m{i}"}
                                      for i in range(31)],
                  "no_longer_predicted": []},
    },
}

FLIP_INDEX = [{"flip_id": "base__c1__beh-a__m1__newly_predicted",
               "behaviour": "beh-a", "clause_id": "m1",
               "direction": "newly_predicted"}]

CENSUS_INDEX = [
    {"dossier_id": "beh-a__p1", "behaviour": "beh-a", "pid": "p1",
     "kind": "FP", "file": "beh-a__p1.json"},
    {"dossier_id": "beh-b__p2", "behaviour": "beh-b", "pid": "p2",
     "kind": "FN", "file": "beh-b__p2.json"},
]


class Env:
    def __init__(self, root, fake):
        self.root = root
        self.fake = fake
        self.repo = os.path.join(root, "repo")
        self.cycles = os.path.join(root, "cycles")

    def path(self, *parts):
        return os.path.join(self.repo, *parts)


def _make_env(root, monkeypatch):
    fake = FakeRun()
    env = Env(root, fake)
    os.makedirs(env.repo, exist_ok=True)
    for name, content in (
            ("fix_target.py", "x = 1\n"),
            ("test_gate.py", "def test_ok():\n    assert True\n"),
            ("annotations_test.json", "{}\n"),
            ("behavior_atoms_test.json", "{}\n")):
        with open(env.path(name), "w") as f:
            f.write(content)
    os.makedirs(env.path("snapshots"), exist_ok=True)
    with open(env.path("snapshots", "base.json"), "w") as f:
        f.write("{}\n")
    monkeypatch.setattr(cycle, "REPO", env.repo)
    monkeypatch.setattr(cycle, "CYCLES_ROOT", env.cycles)
    monkeypatch.setattr(cycle, "SNAPSHOT_DIR", env.path("snapshots"))
    monkeypatch.setattr(cycle, "DEV_CENSUS_CELLS", ("beh-a", "beh-b"))
    monkeypatch.setattr(cycle, "_run", fake)
    return env


@pytest.fixture
def env(tmp_path, monkeypatch):
    return _make_env(str(tmp_path), monkeypatch)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True, indent=1)
        f.write("\n")


def read_json(path):
    with open(path) as f:
        return json.load(f)


MANIFEST = {
    "cycle_name": "c1",
    "date": "2026-08-04",
    "shape": "code",
    "census_scope": "dev",
    "fix_description": "fix the widget",
    "document_side_rationale": "the document says so",
    "files_to_change": ["fix_target.py"],
    "gate_tests": ["test_gate.py"],
    "review_required": False,
    "baseline_snapshot_tag": "base",
    "compatibility": {
        "version_key": "widget_version",
        "statement": "old behavior reachable via widget_version=1 recorded "
                     "in snapshot config (PRICING_VERSION pattern)"},
    "config": {"annotations": "annotations_test.json",
               "atoms": "behavior_atoms_test.json"},
}

BASELINE_CENSUS_REL = os.path.join("audit_dossiers", "baseline",
                                   "verdicts_merged.json")

CHECKPOINT_MANIFEST = dict(
    MANIFEST, shape="checkpoint", baseline_census=BASELINE_CENSUS_REL)

PREDICTION = {
    "expected_flip_count": {"min": 1, "max": 5},
    "expected_directions": ["newly_predicted"],
    "expected_clauses": ["m1"],
    "max_regressions": 0,
    "notes": "the fix adds exactly the manipulation-family matches",
}

CENSUS_CLASSES = {"expected_shrink": ["fp_lexical_only"],
                  "must_not_grow": ["fn_threshold"]}


def baseline_census(env, counts):
    """Write the NAMED baseline census artifact the checkpoint manifest
    points at (F2: deltas vs a named artifact, never 'the directory')."""
    recs, i = [], 0
    for cause, n in sorted(counts.items()):
        for _ in range(n):
            recs.append({"dossier_id": f"old__{i}", "cause": cause,
                         "side": "panel", "note": "baseline"})
            i += 1
    write_json(env.path(BASELINE_CENSUS_REL), recs)


def state_of(c):
    return read_json(os.path.join(c.dir, "state.json"))


def write_flip_verdicts(c, records):
    """The bound verdict artifact: echoes the dossier_set_sha (F3)."""
    write_json(os.path.join(c.dir, "flip_verdicts.json"),
               {"dossier_set_sha": state_of(c)["dossier_set_sha"],
                "records": records})


GOOD_FLIP_RECORDS = [{"flip_id": FLIP_INDEX[0]["flip_id"],
                      "verdict": "correct",
                      "document_reason": "clause concerns the behaviour"}]


def write_census_verdicts(c, slug, records):
    write_json(os.path.join(c.dir, "census", f"verdicts_{slug}.json"),
               {"dossier_set_sha": state_of(c)["census_set_sha"],
                "records": records})


def advance_to(env, target, shape="code", review_required=False,
               baseline_counts=None, diff=None, prediction=None):
    """Walk a fresh cycle 'c1' to the named phase using valid operator
    artifacts, returning the Cycle."""
    c = cycle.Cycle("c1")
    manifest = dict(CHECKPOINT_MANIFEST if shape == "checkpoint"
                    else MANIFEST, review_required=review_required)
    if baseline_counts is not None:
        baseline_census(env, baseline_counts)
    if target == "OPEN":
        return c
    write_json(os.path.join(c.dir, "manifest.json"), manifest)
    c.next()                      # OPEN completes
    if target == "PREDICT":
        return c
    pred = dict(prediction if prediction is not None else PREDICTION)
    if shape == "checkpoint":
        pred["census_classes"] = CENSUS_CLASSES
    write_json(os.path.join(c.dir, "prediction.json"), pred)
    c.next()                      # PREDICT completes (freeze)
    if target == "IMPLEMENT":
        return c
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")        # the content diff the gate requires
    if review_required:
        write_json(os.path.join(c.dir, "review_verdict.json"),
                   {"verdict": "proceed", "by": "reviewer", "notes": "ok"})
    c.next()                      # IMPLEMENT completes
    if target == "MEASURE":
        return c
    env.fake.diff = diff if diff is not None else FLIP_DIFF
    env.fake.flips = FLIP_INDEX
    env.fake.census_index = CENSUS_INDEX
    c.next()                      # MEASURE runs (mechanical)
    if target == "ADJUDICATE":
        return c
    c.next()                      # ADJUDICATE halt: writes assignment
    write_flip_verdicts(c, GOOD_FLIP_RECORDS)
    c.next()                      # ADJUDICATE completes
    if target == "CENSUS":
        return c
    if shape == "checkpoint":
        c.next()                  # CENSUS mechanical part + halt
        write_census_verdicts(c, "beh-a",
                              [{"dossier_id": "beh-a__p1",
                                "cause": "fp_lexical_only",
                                "side": "panel", "note": "n"}])
        write_census_verdicts(c, "beh-b",
                              [{"dossier_id": "beh-b__p2",
                                "cause": "fn_threshold",
                                "side": "panel", "note": "n"}])
        c.next()                  # CENSUS completes
    if target == "DECIDE":
        return c
    c.next()                      # DECIDE halt: drafts decision
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    draft.update(decision="keep", signed_by="matt",
                 justification="document-side adjudications support keeping")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    c.next()                      # DECIDE completes
    if target == "CLOSE":
        return c
    c.next()                      # CLOSE appends the log line
    return c


# ------------------------------------------------------- phase inference

def test_fresh_cycle_is_open_and_emits_manifest_template(env):
    c = cycle.Cycle("c1")
    assert c.phase() == "OPEN"
    msg = c.next()
    assert "manifest.template.json" in msg
    tpl = read_json(os.path.join(c.dir, "manifest.template.json"))
    for key in ("cycle_name", "date", "shape", "census_scope",
                "fix_description", "document_side_rationale",
                "files_to_change", "gate_tests", "review_required",
                "baseline_snapshot_tag", "compatibility", "config"):
        assert key in tpl, f"manifest template missing {key}"
    assert tpl["cycle_name"] == "c1"
    assert tpl["shape"] == "code"
    assert c.phase() == "OPEN", "no manifest yet — must not advance"


def test_open_validates_paths_exist(env):
    c = cycle.Cycle("c1")
    bad = dict(MANIFEST, files_to_change=["no_such_file.py"])
    write_json(os.path.join(c.dir, "manifest.json"), bad)
    with pytest.raises(cycle.CycleError, match="no_such_file.py"):
        c.next()
    assert c.phase() == "OPEN"


def test_open_requires_compatibility_for_code_shape(env):
    c = cycle.Cycle("c1")
    bad = dict(MANIFEST, compatibility={})
    write_json(os.path.join(c.dir, "manifest.json"), bad)
    with pytest.raises(cycle.CycleError, match="compatibilit"):
        c.next()


def test_open_pins_census_scope_to_dev(env):
    c = cycle.Cycle("c1")
    bad = dict(MANIFEST, census_scope="held-out")
    write_json(os.path.join(c.dir, "manifest.json"), bad)
    with pytest.raises(cycle.CycleError, match="census_scope"):
        c.next()


def test_open_records_census_deferral_for_code_shape(env):
    c = advance_to(env, "PREDICT")
    assert state_of(c)["census"] == "deferred_to_checkpoint"


@pytest.mark.parametrize("target,phase", [
    ("OPEN", "OPEN"), ("PREDICT", "PREDICT"), ("IMPLEMENT", "IMPLEMENT"),
    ("MEASURE", "MEASURE"), ("ADJUDICATE", "ADJUDICATE"),
    ("DECIDE", "DECIDE"), ("CLOSE", "CLOSE"),
])
def test_phase_inference_from_constructed_dirs(env, target, phase):
    c = advance_to(env, target)
    assert c.phase() == phase
    # a FRESH Cycle object over the same dir infers the same phase from disk
    assert cycle.Cycle("c1").phase() == phase


def test_code_shape_has_no_census_phase_and_never_touches_audit_tooling(env):
    c = advance_to(env, "DONE")
    assert c.phase() == "CLOSED"
    for call in env.fake.calls:
        assert "audit_disagreements.py" not in " ".join(call), \
            "the DEFAULT path must not touch audit_disagreements at all (F1)"


def test_checkpoint_shape_includes_census_phase(env):
    c = advance_to(env, "CENSUS", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2, "fn_threshold": 1})
    assert c.phase() == "CENSUS"


# --------------------------------------------------- predict + freeze

def test_predict_template_is_mechanism_level_for_code_shape(env):
    c = advance_to(env, "PREDICT")
    msg = c.next()
    assert "prediction.template.json" in msg
    tpl = read_json(os.path.join(c.dir, "prediction.template.json"))
    for key in ("expected_flip_count", "expected_directions",
                "expected_clauses", "max_regressions"):
        assert key in tpl, f"prediction template missing {key}"
    assert "_cause_taxonomy" not in tpl, \
        "code-shape template must not touch the census taxonomy (F1)"


def test_predict_template_checkpoint_adds_taxonomy_and_baseline(env):
    import audit_disagreements as AD
    c = advance_to(env, "PREDICT", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 4})
    c.next()
    tpl = read_json(os.path.join(c.dir, "prediction.template.json"))
    for cause in AD.CAUSE_TAXONOMY:
        assert cause in tpl["_cause_taxonomy"]
    assert tpl["_baseline_census_counts"] == {"fp_lexical_only": 4}


def test_prediction_rejects_bad_mechanism_fields(env):
    c = advance_to(env, "PREDICT")
    write_json(os.path.join(c.dir, "prediction.json"),
               dict(PREDICTION, expected_directions=["sideways"]))
    with pytest.raises(cycle.CycleError, match="sideways"):
        c.next()


def test_prediction_freeze_records_both_shas_and_tamper_is_hard_error(env):
    c = advance_to(env, "PREDICT")
    ppath = os.path.join(c.dir, "prediction.json")
    write_json(ppath, PREDICTION)
    c.next()  # freezes
    state = state_of(c)
    frozen = state["frozen_prediction_sha"]
    assert frozen == cycle.sha256_file(ppath)
    assert state["frozen_manifest_sha"] == cycle.sha256_file(
        os.path.join(c.dir, "manifest.json")), \
        "the MANIFEST sha must freeze alongside the prediction (F5)"
    # tamper with the prediction
    write_json(ppath, dict(PREDICTION, notes="edited after the freeze"))
    tampered = cycle.sha256_file(ppath)
    with pytest.raises(cycle.PredictionTampered) as e:
        c.status()
    assert frozen in str(e.value) and tampered in str(e.value), \
        "the tamper error must name BOTH shas"
    with pytest.raises(cycle.PredictionTampered):
        c.next()


def test_manifest_tamper_is_hard_error_amendment_is_the_loud_path(env):
    c = advance_to(env, "IMPLEMENT")
    mpath = os.path.join(c.dir, "manifest.json")
    old_sha = cycle.sha256_file(mpath)
    write_json(mpath, dict(MANIFEST, fix_description="quietly changed"))
    new_sha = cycle.sha256_file(mpath)
    with pytest.raises(cycle.ManifestTampered) as e:
        c.status()
    assert old_sha in str(e.value) and new_sha in str(e.value)
    # the LOUD path: a manifest amendment artifact naming both shas
    write_json(os.path.join(c.dir, "manifest_amendments.json"),
               [{"reason": "clarified the fix description",
                 "old_sha": old_sha, "new_sha": new_sha}])
    out = c.status()
    assert "AMEND" in out.upper()
    assert "clarified the fix description" in out


# ----------------------------------------------------- implement gate

def test_implement_refuses_failing_gate_tests(env):
    c = advance_to(env, "IMPLEMENT")
    env.fake.pytest_rc = 1
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    with pytest.raises(cycle.ToolFailed) as e:
        c.next()
    assert e.value.code == 1, "the gate's real exit code must propagate"
    assert c.phase() == "IMPLEMENT"


def test_implement_refuses_unchanged_file(env):
    c = advance_to(env, "IMPLEMENT")
    msg = c.next()  # gate tests pass but fix_target.py is untouched
    assert "fix_target.py" in msg
    assert c.phase() == "IMPLEMENT"


def test_implement_refuses_changed_undeclared_input(env):
    c = advance_to(env, "IMPLEMENT")
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    with open(env.path("annotations_test.json"), "w") as f:
        f.write('{"drifted": true}\n')  # undeclared input changed (F5)
    with pytest.raises(cycle.CycleError, match="annotations_test.json"):
        c.next()
    assert c.phase() == "IMPLEMENT"


def test_implement_refuses_missing_review(env):
    c = advance_to(env, "IMPLEMENT", review_required=True)
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    msg = c.next()
    assert "review_verdict.json" in msg
    assert c.phase() == "IMPLEMENT"


def test_implement_refuses_blocked_review(env):
    c = advance_to(env, "IMPLEMENT", review_required=True)
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    write_json(os.path.join(c.dir, "review_verdict.json"),
               {"verdict": "blocked", "by": "reviewer",
                "notes": "the fix regresses the frobnicator"})
    msg = c.next()
    assert "frobnicator" in msg, "a blocked review must surface its notes"
    assert c.phase() == "IMPLEMENT"


def test_implement_advances_when_all_gates_pass(env):
    c = advance_to(env, "IMPLEMENT", review_required=True)
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    write_json(os.path.join(c.dir, "review_verdict.json"),
               {"verdict": "proceed", "by": "reviewer", "notes": "ok"})
    c.next()
    assert c.phase() == "MEASURE"
    assert any("pytest" in call for call in
               [" ".join(x) for x in env.fake.calls]), "gate tests never ran"


# ------------------------------------------------------------ override

def test_override_requires_reason(env):
    c = advance_to(env, "IMPLEMENT")
    with pytest.raises(cycle.CycleError, match="reason"):
        c.next(override="IMPLEMENT", reason="")


def test_override_recorded_and_echoed_by_status(env):
    c = advance_to(env, "IMPLEMENT")
    c.next(override="IMPLEMENT", reason="hotfix, gates run manually")
    assert c.phase() == "MEASURE"
    assert state_of(c)["overrides"] == [
        {"phase": "IMPLEMENT", "reason": "hotfix, gates run manually"}]
    out = c.status()
    assert "OVERRID" in out.upper()
    assert "hotfix, gates run manually" in out


def test_override_must_name_the_current_phase(env):
    c = advance_to(env, "IMPLEMENT")
    with pytest.raises(cycle.CycleError, match="IMPLEMENT"):
        c.next(override="DECIDE", reason="skipping ahead")


def test_adjudicate_and_decide_are_non_overridable(env):
    c = advance_to(env, "ADJUDICATE")
    with pytest.raises(cycle.CycleError, match="non-overridable|cannot"):
        c.next(override="ADJUDICATE", reason="in a hurry")
    c.next()
    write_flip_verdicts(c, GOOD_FLIP_RECORDS)
    c.next()
    assert c.phase() == "DECIDE"
    with pytest.raises(cycle.CycleError, match="non-overridable|cannot"):
        c.next(override="DECIDE", reason="in a hurry")


def test_override_predict_demotes_to_exploratory_and_close_refuses_keep(env):
    c = advance_to(env, "PREDICT")
    msg = c.next(override="PREDICT", reason="exploratory poke at the scorer")
    assert "exploratory" in msg.lower()
    assert state_of(c)["exploratory"] is True
    # walk on to DECIDE
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    c.next()                      # IMPLEMENT
    env.fake.diff = FLIP_DIFF
    env.fake.flips = FLIP_INDEX
    c.next()                      # MEASURE
    c.next()                      # ADJUDICATE halt
    write_flip_verdicts(c, GOOD_FLIP_RECORDS)
    c.next()                      # ADJUDICATE completes
    c.next()                      # DECIDE halt: drafts
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    draft.update(decision="keep", signed_by="matt",
                 justification="looks good")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    with pytest.raises(cycle.CycleError, match="(?i)exploratory"):
        c.next()
    draft.update(decision="revert")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    c.next()
    assert c.phase() == "CLOSE"


# ------------------------------------------------- measure / budget

def test_measure_runs_snapshot_diff_dossiers(env):
    c = advance_to(env, "MEASURE")
    env.fake.diff = FLIP_DIFF
    env.fake.flips = FLIP_INDEX
    c.next()
    joined = [" ".join(x) for x in env.fake.calls]
    assert any("snapshot.py snapshot" in j and "--tag c1" in j
               for j in joined)
    assert any("snapshot.py diff" in j for j in joined)
    assert any("dossier.py dossiers" in j for j in joined)
    assert os.path.exists(os.path.join(c.dir, "diff.json"))
    assert c.phase() == "ADJUDICATE"
    assert "dossier_set_sha" in state_of(c), \
        "MEASURE must record the dossier-set identity (F3)"


def test_measure_refuses_snapshot_tag_reuse_with_different_content(env):
    c = advance_to(env, "MEASURE")
    with open(env.path("snapshots", "c1.json"), "w") as f:
        f.write('{"tag": "c1", "different": "bytes"}\n')
    env.fake.diff = FLIP_DIFF
    with pytest.raises(cycle.CycleError, match="c1"):
        c.next()
    assert c.phase() == "MEASURE"
    assert read_json(env.path("snapshots", "c1.json"))["different"] == \
        "bytes", "the existing snapshot must never be overwritten"


def test_measure_flip_budget_halts_over_30(env):
    c = advance_to(env, "MEASURE")
    env.fake.diff = BIG_DIFF
    env.fake.flips = FLIP_INDEX
    msg = c.next()
    assert "31" in msg
    assert "split" in msg.lower() and "strat" in msg.lower(), \
        "the budget halt must offer the policy §4 choices"
    assert c.phase() == "MEASURE"
    # the pre-registered plan unblocks it
    write_json(os.path.join(c.dir, "flip_budget_plan.json"),
               {"resolution": "stratified_sample",
                "rationale": "pre-registered strata: behaviour x direction "
                             "x cause"})
    c.next()
    assert c.phase() == "ADJUDICATE"


def test_measure_noop_short_circuits_to_decide(env):
    c = advance_to(env, "MEASURE")
    env.fake.diff = NOOP_DIFF
    msg = c.next()
    assert "no-op" in msg.lower() or "no effect" in msg.lower()
    assert c.phase() == "DECIDE"
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    assert draft["noop"] is True
    assert draft["decision"] == ""
    assert "ADJUDICATE" in state_of(c)["skipped"]


# --------------------------------------------------------- adjudicate

def test_adjudicate_writes_assignment_with_set_sha_and_halts(env):
    c = advance_to(env, "ADJUDICATE")
    msg = c.next()
    assert "flip_verdicts.json" in msg
    apath = os.path.join(c.dir, "assignments", "flips.md")
    assert os.path.exists(apath)
    text = open(apath).read()
    assert "briefs/flip_adjudicator.md" in text
    assert "flip_dossiers" in text
    assert state_of(c)["dossier_set_sha"] in text, \
        "the assignment must carry the dossier_set_sha the verdicts echo"
    assert c.phase() == "ADJUDICATE"


def test_adjudicate_requires_sha_echo(env):
    c = advance_to(env, "ADJUDICATE")
    c.next()
    # a bare list (no echo) is refused
    write_json(os.path.join(c.dir, "flip_verdicts.json"), GOOD_FLIP_RECORDS)
    with pytest.raises(cycle.CycleError, match="dossier_set_sha"):
        c.next()
    # a wrong echo is refused naming both shas
    write_json(os.path.join(c.dir, "flip_verdicts.json"),
               {"dossier_set_sha": "0" * 64, "records": GOOD_FLIP_RECORDS})
    with pytest.raises(cycle.CycleError) as e:
        c.next()
    assert "0" * 64 in str(e.value)
    assert state_of(c)["dossier_set_sha"] in str(e.value)
    # the correct echo advances
    write_flip_verdicts(c, GOOD_FLIP_RECORDS)
    c.next()
    assert c.phase() == "DECIDE"


def test_adjudicate_records_reused_from(env):
    c = advance_to(env, "ADJUDICATE")
    c.next()
    write_json(os.path.join(c.dir, "flip_verdicts.json"),
               {"dossier_set_sha": state_of(c)["dossier_set_sha"],
                "reused_from": "cycles/c0/flip_verdicts.json",
                "records": GOOD_FLIP_RECORDS})
    c.next()
    assert state_of(c)["flip_verdicts_reused_from"] == \
        "cycles/c0/flip_verdicts.json"


def test_adjudicate_completes_only_when_verdicts_validate(env):
    c = advance_to(env, "ADJUDICATE")
    c.next()  # writes assignment
    write_flip_verdicts(c, GOOD_FLIP_RECORDS)
    env.fake.validate_rc = 1
    with pytest.raises(cycle.ToolFailed):
        c.next()
    assert c.phase() == "ADJUDICATE"
    env.fake.validate_rc = 0
    c.next()
    assert c.phase() == "DECIDE"
    assert any("dossier.py validate" in " ".join(x) for x in env.fake.calls)


# ------------------------------------------- mechanism prediction check

def test_prediction_check_mechanism_all_pass(env):
    c = advance_to(env, "DECIDE")
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    by_kind = {}
    for rec in check["checks"]:
        by_kind.setdefault(rec["kind"], []).append(rec)
    assert by_kind["flip_count"][0]["observed"] == 1
    assert by_kind["flip_count"][0]["result"] == "PASS"
    assert by_kind["directions"][0]["result"] == "PASS"
    assert by_kind["expected_clause"][0]["clause"] == "m1"
    assert by_kind["expected_clause"][0]["result"] == "PASS"
    assert by_kind["max_regressions"][0]["observed"] == 0
    assert by_kind["max_regressions"][0]["result"] == "PASS"
    assert check["pass_rate"] == [4, 4]


def test_prediction_check_mechanism_failures(env):
    bad_pred = {
        "expected_flip_count": {"min": 2, "max": 5},   # only 1 flip: FAIL
        "expected_directions": ["no_longer_predicted"],  # wrong dir: FAIL
        "expected_clauses": ["m9"],                    # never flipped: FAIL
        "max_regressions": 0,                          # 1 regression: FAIL
        "notes": "",
    }
    c = advance_to(env, "ADJUDICATE", prediction=bad_pred)
    c.next()
    write_flip_verdicts(c, [{"flip_id": FLIP_INDEX[0]["flip_id"],
                             "verdict": "regression",
                             "document_reason": "clause is off-topic"}])
    c.next()
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    assert check["pass_rate"] == [0, 4]
    assert all(rec["result"] == "FAIL" for rec in check["checks"])


# ------------------------------------------------- checkpoint census

def test_census_missing_baseline_halts_with_instructions(env):
    c = advance_to(env, "CENSUS", shape="checkpoint")
    # no baseline_counts were written: the named artifact does not exist
    msg = c.next()
    assert "verdicts_merged.json" in msg
    assert "audit_disagreements" in msg, \
        "the halt must say HOW to generate the baseline"
    assert c.phase() == "CENSUS"


def test_census_scope_pin_refuses_held_out_cells(env):
    c = advance_to(env, "CENSUS", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2})
    env.fake.census_index = CENSUS_INDEX + [
        {"dossier_id": "held__p9", "behaviour": "held-out-cell", "pid": "p9",
         "kind": "FN", "file": "held__p9.json"}]
    with pytest.raises(cycle.CycleError, match="held-out-cell"):
        c.next()
    assert c.phase() == "CENSUS"


def test_census_assignments_merge_validate_and_dev_stamp(env):
    c = advance_to(env, "CENSUS", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2, "fn_threshold": 1})
    msg = c.next()  # mechanical: audit dossiers + assignments, halts
    for slug in ("beh-a", "beh-b"):
        apath = os.path.join(c.dir, "assignments", f"census_{slug}.md")
        assert os.path.exists(apath), f"missing seat assignment for {slug}"
        text = open(apath).read()
        assert "briefs/disagreement_autopsy.md" in text
        assert f"verdicts_{slug}.json" in text
    assert "verdicts_beh-a.json" in msg
    write_census_verdicts(c, "beh-a",
                          [{"dossier_id": "beh-a__p1",
                            "cause": "fp_lexical_only",
                            "side": "panel", "note": "n"}])
    write_census_verdicts(c, "beh-b",
                          [{"dossier_id": "beh-b__p2",
                            "cause": "fn_threshold",
                            "side": "panel", "note": "n"}])
    c.next()
    assert c.phase() == "DECIDE"
    merged = read_json(os.path.join(c.dir, "census", "verdicts_merged.json"))
    assert [m["dossier_id"] for m in merged] == ["beh-a__p1", "beh-b__p2"]
    assert any("audit_disagreements.py validate" in " ".join(x)
               for x in env.fake.calls)
    delta = read_json(os.path.join(c.dir, "census_delta.json"))
    assert delta["stamp"] == "DEV"
    assert delta["baseline_census"] == BASELINE_CENSUS_REL
    assert delta["by_cause"]["fp_lexical_only"]["delta"] == -1
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    assert check["stamp"] == "DEV", \
        "census-derived numbers must be stamped DEV"
    by_class = {r.get("class"): r for r in check["checks"] if "class" in r}
    # baseline 2 -> new 1: strictly decreased, PASS
    assert by_class["fp_lexical_only"]["result"] == "PASS"
    # baseline 1 -> new 1: not grown, PASS
    assert by_class["fn_threshold"]["result"] == "PASS"


def test_census_class_check_shrink_strict_and_grow_fails(env):
    # baseline: fp_lexical_only 1, fn_threshold 1
    # new:      fp_lexical_only 1 (NOT strictly decreased: FAIL),
    #           fn_threshold 2   (grew: FAIL)
    c = advance_to(env, "CENSUS", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 1, "fn_threshold": 1})
    env.fake.census_index = CENSUS_INDEX + [
        {"dossier_id": "beh-b__p3", "behaviour": "beh-b", "pid": "p3",
         "kind": "FN", "file": "beh-b__p3.json"}]
    c.next()
    write_census_verdicts(c, "beh-a",
                          [{"dossier_id": "beh-a__p1",
                            "cause": "fp_lexical_only",
                            "side": "panel", "note": "n"}])
    write_census_verdicts(c, "beh-b",
                          [{"dossier_id": "beh-b__p2",
                            "cause": "fn_threshold",
                            "side": "panel", "note": "n"},
                           {"dossier_id": "beh-b__p3",
                            "cause": "fn_threshold",
                            "side": "panel", "note": "n"}])
    c.next()
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    by_class = {r.get("class"): r for r in check["checks"] if "class" in r}
    assert by_class["fp_lexical_only"]["result"] == "FAIL", \
        "expected_shrink must be STRICTLY decreased"
    assert by_class["fn_threshold"]["result"] == "FAIL", "must_not_grow grew"


# ------------------------------------------------------------- decide

def test_decide_drafts_computed_fields(env):
    c = advance_to(env, "DECIDE")
    msg = c.next()
    assert "decision.json" in msg
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    assert draft["cycle"] == "c1"
    assert draft["flip_tallies"] == {"correct": 1}
    assert draft["prediction_check"]["pass_rate"] == [4, 4]
    assert draft["overrides"] == []
    assert draft["census"] == "deferred_to_checkpoint"
    assert draft["decision"] == "" and draft["signed_by"] == ""


def test_decide_requires_justification_after_override(env):
    c = advance_to(env, "IMPLEMENT")
    c.next(override="IMPLEMENT", reason="gates run by hand")
    env.fake.diff = NOOP_DIFF
    c.next()  # MEASURE, no-op -> DECIDE
    c.next()  # drafts
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    draft.update(decision="keep", signed_by="matt", justification="")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    with pytest.raises(cycle.CycleError, match="justification"):
        c.next()
    draft["justification"] = "override was a controlled manual gate run"
    write_json(os.path.join(c.dir, "decision.json"), draft)
    c.next()
    assert c.phase() == "CLOSE"


def test_decide_requires_justification_on_failed_prediction(env):
    c = advance_to(env, "DECIDE",
                   prediction=dict(PREDICTION,
                                   expected_flip_count={"min": 2, "max": 5}))
    c.next()  # drafts (flip_count FAILed: 1 flip < min 2)
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    draft.update(decision="keep", signed_by="matt", justification="")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    with pytest.raises(cycle.CycleError, match="justification"):
        c.next()


def test_decide_rejects_bad_decision_value(env):
    c = advance_to(env, "DECIDE")
    c.next()
    draft = read_json(os.path.join(c.dir, "decision.draft.json"))
    draft.update(decision="maybe", signed_by="matt")
    write_json(os.path.join(c.dir, "decision.json"), draft)
    with pytest.raises(cycle.CycleError, match="maybe"):
        c.next()


# -------------------------------------------------------------- close

def test_close_appends_exactly_one_log_line(env):
    c = advance_to(env, "CLOSE")
    c.next()
    log = os.path.join(env.cycles, "CYCLE_LOG.jsonl")
    lines = [l for l in open(log) if l.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["cycle"] == "c1"
    assert rec["date"] == "2026-08-04"
    assert rec["decision"] == "keep"
    assert rec["prediction_pass_rate"] == [4, 4]
    assert rec["census_consulted"] is False
    assert c.phase() == "CLOSED"
    # closing again must not double-append
    msg = c.next()
    assert "closed" in msg.lower()
    lines = [l for l in open(log) if l.strip()]
    assert len(lines) == 1


def test_close_checkpoint_logs_census_consulted(env):
    c = advance_to(env, "DONE", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2, "fn_threshold": 1})
    log = os.path.join(env.cycles, "CYCLE_LOG.jsonl")
    rec = json.loads([l for l in open(log) if l.strip()][0])
    assert rec["census_consulted"] is True


# -------------------------------------------------------- determinism

def test_determinism_same_inputs_byte_identical_artifacts(tmp_path,
                                                          monkeypatch):
    outs = []
    for sub in ("one", "two"):
        root = os.path.join(str(tmp_path), sub)
        env = _make_env(root, monkeypatch)
        c = cycle.Cycle("c1")
        c.next()  # manifest template
        write_json(os.path.join(c.dir, "manifest.json"), MANIFEST)
        c.next()  # OPEN
        c.next()  # prediction template
        write_json(os.path.join(c.dir, "prediction.json"), PREDICTION)
        c.next()  # PREDICT freeze
        grab = {}
        for rel in ("state.json", "manifest.template.json",
                    "prediction.template.json"):
            with open(os.path.join(c.dir, rel), "rb") as f:
                grab[rel] = f.read()
        outs.append(grab)
    assert outs[0] == outs[1], \
        "same inputs must yield byte-identical artifacts"


# ----------------- first-customer fixes (versioned-cut-2026-08-04 findings)

ZERO_FLIP_PREDICTION = {
    "expected_flip_count": {"min": 0, "max": 0},
    "expected_directions": [],
    "expected_clauses": [],
    "max_regressions": 0,
    "notes": "honest zero-flip prediction: no direction can occur",
}


def test_predict_accepts_empty_directions_iff_zero_flip_max(env):
    """Recorded refusal (versioned-cut-2026-08-04 prediction.json FIELD
    NOTE): a deliberate no-op predicts zero flips, so NO direction can occur
    — the honest direction target is the empty list. The driver refused it
    ('expected_directions must be a non-empty list'), forcing a vacuous
    full-direction fill. Empty must be legal iff expected_flip_count.max ==
    0."""
    c = advance_to(env, "PREDICT")
    write_json(os.path.join(c.dir, "prediction.json"), ZERO_FLIP_PREDICTION)
    c.next()   # must FREEZE, not refuse
    assert "frozen_prediction_sha" in state_of(c)


def test_predict_still_requires_directions_when_flips_possible(env):
    """The guard the fix must NOT loosen: with max > 0 flips predicted, an
    empty direction list is still an unfalsifiable hole — refused."""
    c = advance_to(env, "PREDICT")
    write_json(os.path.join(c.dir, "prediction.json"),
               dict(PREDICTION, expected_directions=[]))
    with pytest.raises(cycle.CycleError, match="expected_directions"):
        c.next()


def test_noop_records_vacuous_prediction_targets(env):
    """First-customer finding (the max_regressions gap): the no-op
    short-circuit skips ADJUDICATE, so the frozen max_regressions target
    silently vanished from prediction_check.json. Every frozen target absent
    from the check must be recorded as PASS_VACUOUS with a reason — never
    dropped."""
    c = advance_to(env, "MEASURE")
    env.fake.diff = NOOP_DIFF
    c.next()
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    by_kind = {r["kind"]: r for r in check["checks"]}
    assert "max_regressions" in by_kind, \
        "the frozen max_regressions target was silently dropped on no-op"
    rec = by_kind["max_regressions"]
    assert rec["result"] == "PASS_VACUOUS"
    assert str(rec.get("reason", "")).strip(), \
        "a vacuous pass must say WHY it is vacuous"
    # PREDICTION targets 1-5 flips and clause m1: both genuinely FAIL on a
    # no-op; directions PASSes; max_regressions passes vacuously.
    assert check["pass_rate"] == [2, 4], \
        "PASS_VACUOUS must count as a pass, and real FAILs must remain FAILs"


def test_noop_checkpoint_records_vacuous_census_targets(env):
    """Same gap, checkpoint shape: the no-op path skips CENSUS too, so
    frozen census-class targets must surface as PASS_VACUOUS."""
    c = advance_to(env, "MEASURE", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2, "fn_threshold": 1})
    env.fake.diff = NOOP_DIFF
    c.next()
    check = read_json(os.path.join(c.dir, "prediction_check.json"))
    by_class = {r.get("class"): r for r in check["checks"] if "class" in r}
    assert by_class["fp_lexical_only"]["result"] == "PASS_VACUOUS"
    assert by_class["fn_threshold"]["result"] == "PASS_VACUOUS"


def test_open_validates_thresholds_path_exists(env):
    """Manifest config gains optional 'thresholds' (the frozen-thresholds
    artifact); a dangling path must be refused at OPEN like every other
    config path."""
    c = cycle.Cycle("c1")
    bad = dict(MANIFEST, config=dict(MANIFEST["config"],
                                     thresholds="no_such_thresholds.json"))
    write_json(os.path.join(c.dir, "manifest.json"), bad)
    with pytest.raises(cycle.CycleError, match="no_such_thresholds.json"):
        c.next()
    assert c.phase() == "OPEN"


def test_measure_threads_thresholds_like_overlay(env):
    """config.thresholds must thread to the snapshot build exactly like
    overlay: --thresholds on the snapshot command (the sha joins the
    identity via the snapshot's own recording) and the artifact joins the
    sha-pinned undeclared-input closure at OPEN."""
    with open(env.path("thresholds_test.json"), "w") as f:
        f.write('{"thresholds": {}}\n')
    c = cycle.Cycle("c1")
    manifest = dict(MANIFEST, config=dict(MANIFEST["config"],
                                          thresholds="thresholds_test.json"))
    write_json(os.path.join(c.dir, "manifest.json"), manifest)
    c.next()                      # OPEN
    assert "thresholds_test.json" in state_of(c)["closure_shas"], \
        "the thresholds artifact is an undeclared input: it must join the " \
        "pinned closure like overlay"
    write_json(os.path.join(c.dir, "prediction.json"), PREDICTION)
    c.next()                      # PREDICT (freeze)
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    c.next()                      # IMPLEMENT
    env.fake.diff = FLIP_DIFF
    env.fake.flips = FLIP_INDEX
    c.next()                      # MEASURE
    snap_calls = [" ".join(x) for x in env.fake.calls
                  if "snapshot.py" in " ".join(x) and x[2] == "snapshot"]
    assert snap_calls, "no snapshot build ran"
    assert "--thresholds" in snap_calls[0]
    assert "thresholds_test.json" in snap_calls[0]


def test_implement_review_halt_writes_assignment(env):
    """First-customer finding: ADJUDICATE writes its seat assignment but the
    IMPLEMENT review wait-state wrote nothing — the reviewer had no typed
    assignment. The halt must write assignments/review.md with the change
    summary from the manifest (files, rationale, gate tests), the verdict
    schema, and the pointer to briefs/change_reviewer.md."""
    c = advance_to(env, "IMPLEMENT", review_required=True)
    with open(env.path("fix_target.py"), "w") as f:
        f.write("x = 2\n")
    msg = c.next()                # halts waiting for review_verdict.json
    assert "review_verdict.json" in msg
    apath = os.path.join(c.dir, "assignments", "review.md")
    assert os.path.exists(apath), \
        "the review wait-state must write its seat assignment"
    text = open(apath).read()
    assert "briefs/change_reviewer.md" in text
    assert "fix_target.py" in text          # files under review
    assert "test_gate.py" in text           # gate tests
    assert "the document says so" in text   # rationale from the manifest
    assert "review_verdict.json" in text
    assert '"proceed"' in text and '"blocked"' in text  # verdict schema


# ------------------------------------------------------ status output

def test_status_names_phase_and_whats_needed(env, capsys):
    c = advance_to(env, "PREDICT")
    out = c.status()
    assert "PREDICT" in out
    assert "prediction.json" in out
    rc = cycle.main(["status", "--cycle", "c1"])
    assert rc == 0
    assert "PREDICT" in capsys.readouterr().out


# ------------------------------------------- integration-ish full walk

def test_full_cycle_end_to_end_on_synthetic_fixtures(env):
    c = advance_to(env, "DONE")
    assert c.phase() == "CLOSED"
    for rel in ("manifest.json", "prediction.json", "state.json",
                "diff.json", "flip_verdicts.json",
                os.path.join("assignments", "flips.md"),
                "prediction_check.json",
                "decision.draft.json", "decision.json"):
        assert os.path.exists(os.path.join(c.dir, rel)), f"missing {rel}"
    log = os.path.join(env.cycles, "CYCLE_LOG.jsonl")
    assert len([l for l in open(log) if l.strip()]) == 1


def test_full_checkpoint_cycle_end_to_end(env):
    c = advance_to(env, "DONE", shape="checkpoint",
                   baseline_counts={"fp_lexical_only": 2, "fn_threshold": 1})
    assert c.phase() == "CLOSED"
    for rel in (os.path.join("census", "verdicts_merged.json"),
                "census_delta.json", "prediction_check.json"):
        assert os.path.exists(os.path.join(c.dir, rel)), f"missing {rel}"
