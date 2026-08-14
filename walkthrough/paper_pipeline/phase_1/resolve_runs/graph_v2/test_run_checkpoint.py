"""Pins for FIX 4 -- periodic run checkpoints (Matt's directive
2026-08-14: "periodic stops during long runs, more frequent rather than
less").

A long paid run that reports only at the end discovers its defects after
paying for all of them. Every `checkpoint_every` items the run says
where it is -- done/remaining, spend vs ceiling, failures by category,
graveyard open entries -- on stdout AND on the run's health.jsonl; with
`checkpoint_pause` it stops there.

⛔ THE PROPERTY THAT MATTERS IS "NEVER LOSES WORK": the checkpoint lands
BETWEEN items, after the completed item's artifacts and the run index
are written. Both pause pins below assert exactly that, and the
translate pin re-runs the remainder to show the run resumes from what is
on disk.

Offline: the translate pins reuse test_translate_exec's MockClient and
scripts (imported, not copied, so the two files cannot drift); the
promise_repair pins use test_splice_seat's fixture run. $0.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T             # noqa: E402
import translate_exec as TE       # noqa: E402
import graveyard as gy            # noqa: E402
import promise_repair as PR       # noqa: E402
import run_checkpoint as CK       # noqa: E402
import test_translate_exec as TT  # noqa: E402
import test_splice_seat as TS     # noqa: E402


# ==========================================================================
#  the mechanism itself
# ==========================================================================

def test_defaults_are_every_25_and_no_pause():
    """25 items, and NOT paused: a non-interactive run must never wedge
    waiting for a human. The pause is opt-in, the reporting is not."""
    assert CK.checkpoint_config({}) == (25, False)
    assert CK.DEFAULT_EVERY == 25


def test_config_reads_the_stage_section_before_the_root():
    cfg = {"checkpoint_every": 10, "checkpoint_pause": True,
           "promise_repair": {"checkpoint_every": 3}}
    assert CK.checkpoint_config(cfg, "promise_repair") == (3, True)
    assert CK.checkpoint_config(cfg) == (10, True)
    assert CK.checkpoint_config({"checkpoint_every": "x"}) == (25, False)


def test_it_fires_only_on_the_interval_and_can_be_disabled(tmp_path):
    hp = str(tmp_path / "health.jsonl")
    c = CK.Checkpoint(3, False, hp, "unit", total=7, ceiling_usd=0.5)
    fired = [i for i in range(1, 8)
             if c.tick(i, spent_usd=0.01 * i,
                       failures={"error": 1}, graveyard_open=2)]
    assert fired == [3, 6]
    rows = [json.loads(ln) for ln in open(hp)]
    assert [r["completed"] for r in rows] == [3, 6]
    assert [r["remaining"] for r in rows] == [4, 1]
    assert rows[0] == {"artifact": "unit", "kind": "checkpoint",
                       "completed": 3, "remaining": 4, "total": 7,
                       "spent_usd": 0.03, "ceiling_usd": 0.5,
                       "failures": {"error": 1}, "graveyard_open": 2,
                       "paused": False}
    off = CK.Checkpoint(0, False, hp, "unit")
    assert [off.tick(i) for i in range(1, 40)] == [None] * 39


def test_pause_raises_a_resumable_phase1_error(tmp_path):
    hp = str(tmp_path / "health.jsonl")
    c = CK.Checkpoint(2, True, hp, "unit", total=5,
                      resume_hint="rerun with the rest")
    assert c.tick(1) is None
    with pytest.raises(CK.CheckpointPause) as exc:
        c.tick(2)
    assert "2 item(s)" in str(exc.value) and "3 remaining" in str(exc.value)
    assert "rerun with the rest" in str(exc.value)
    assert isinstance(exc.value, T.Phase1Error)
    # ⛔ the record is written BEFORE the raise: a pause is a reported stop
    assert json.loads(open(hp).read().strip())["paused"] is True


# ==========================================================================
#  translate_exec: the translation-facing path
# ==========================================================================

def _scripts_with_a_failure():
    s = dict(TT._scripts())
    s["m0002"] = ["this never becomes JSON"]     # repeats -> status error
    return s


def _run(tmp_path, run_name, clauses, every=None, pause=None,
         scripts=None):
    os.makedirs(str(tmp_path), exist_ok=True)
    cfg = TT._cfg(tmp_path, run_name,
                  execution={"mode": "concurrent", "concurrent_n": 1})
    if every is not None:
        cfg["checkpoint_every"] = every
    if pause is not None:
        cfg["checkpoint_pause"] = pause
    holder = {}

    def factory(prov, c):
        holder["c"] = TT.MockClient(prov, c, scripts or _scripts_with_a_failure())
        return holder["c"]
    code = TE.run_exec(cfg, TT._args(clause=list(clauses), live=True),
                       client_factory=factory)
    return code, TT._rundir(cfg), holder["c"], cfg


def _health(rundir):
    p = os.path.join(rundir, "health.jsonl")
    return [json.loads(ln) for ln in open(p)] if os.path.exists(p) else []


def test_checkpoints_fire_at_the_interval_with_the_right_counts(tmp_path):
    """RED before FIX 4: a 5-clause run reported once, at the end. Now it
    reports at clause 2 and clause 4 -- items done/remaining, spend
    against the ceiling, failures BY CATEGORY, graveyard open entries."""
    code, rundir, client, cfg = _run(tmp_path, "ck", TT.CIDS, every=2)
    assert code == 1, "one clause failed; the run still finishes"
    rows = [r for r in _health(rundir) if r["kind"] == "checkpoint"]
    assert [r["completed"] for r in rows] == [2, 4]
    assert [r["remaining"] for r in rows] == [3, 1]
    assert [r["total"] for r in rows] == [5, 5]
    # m0002 is the failure, and it is booked BY CATEGORY (its repair
    # status), not as an anonymous count
    assert rows[0]["failures"] == {"unrepaired": 1} == rows[1]["failures"]
    assert rows[0]["remaining_clause_ids"] == ["m0003", "m0004", "m0005"]
    # spend so far vs the ceiling, both on the record
    assert rows[0]["ceiling_usd"] == cfg["cost"]["max_cost_usd"]
    assert 0 < rows[0]["spent_usd"] < rows[1]["spent_usd"]
    assert rows[1]["spent_usd"] <= round(client.spent_usd, 6)
    # the graveyard is read LIVE at each checkpoint: m0002's entry is
    # already there at clause 2, m0003's repair adds one by clause 4
    assert rows[0]["graveyard_open"] >= 1
    assert rows[1]["graveyard_open"] >= rows[0]["graveyard_open"]
    assert rows[1]["graveyard_open"] <= len(
        gy.open_entries(cfg["graveyard"]["dir"]))
    assert rows[0]["paused"] is False


def test_the_default_interval_never_fires_on_a_short_run(tmp_path):
    """Default 25 over 5 clauses: no checkpoint, and byte-parity with the
    pinned equivalence run (the mechanism is inert until configured)."""
    code_a, dir_a, _c, _cfg = _run(tmp_path, "plain", TT.CIDS,
                                   scripts=TT._scripts())
    assert code_a == 0
    assert [r for r in _health(dir_a) if r["kind"] == "checkpoint"] == []
    code_b, dir_b, _client = TT._run_serial(tmp_path)
    TT._assert_equivalent(dir_b, dir_a)


def test_a_pause_stops_cleanly_and_the_run_resumes_from_artifacts(tmp_path):
    """⛔ NO WORK LOST: the pause fires after clause 2's artifacts and
    run.json row are written. Exit code 3 says "incomplete", the two
    finished clauses are byte-identical to an unpaused run's, the three
    unstarted ones cost nothing, and re-running them completes the
    corpus."""
    scripts = TT._scripts()
    code, rundir, client, cfg = _run(tmp_path / "p", "paused", TT.CIDS,
                                     every=2, pause=True, scripts=scripts)
    assert code == 3, "a checkpoint pause is not a failure and not a pass"
    done = ["m0001", "m0002"]
    todo = ["m0003", "m0004", "m0005"]
    rows = {r["clause_id"] for r in json.load(
        open(os.path.join(rundir, "run.json")))["results"]}
    assert rows == set(done)
    for cid in done:
        for suffix in (".json", ".lp", ".version.json", ".raw.txt",
                       ".transcript.json"):
            assert os.path.exists(os.path.join(rundir, cid + suffix)), cid
    for cid in todo:
        assert not os.path.exists(os.path.join(rundir, cid + ".json"))
    assert client.calls == 2, "no clause past the pause was paid for"
    hrow = [r for r in _health(rundir) if r["kind"] == "checkpoint"]
    assert len(hrow) == 1 and hrow[0]["paused"] is True
    assert hrow[0]["remaining_clause_ids"] == todo

    # RESUME: the remaining clauses, from the artifacts on disk
    code2, dir2, client2, _c2 = _run(tmp_path / "p", "resumed", todo,
                                     every=2, scripts=scripts)
    assert code2 == 0
    assert {r["clause_id"] for r in json.load(
        open(os.path.join(dir2, "run.json")))["results"]} == set(todo)

    # and the union is byte-identical to one unpaused run of all five
    code3, dir3, _c3, _cfg3 = _run(tmp_path / "whole", "whole", TT.CIDS,
                                   scripts=scripts)
    assert code3 == 0
    for cid, d in [(c, rundir) for c in done] + [(c, dir2) for c in todo]:
        for suffix in (".json", ".lp", ".raw.txt", ".transcript.json"):
            assert (open(os.path.join(d, cid + suffix), "rb").read()
                    == open(os.path.join(dir3, cid + suffix), "rb").read()), \
                f"{cid}{suffix} differs from the unpaused run"


def test_a_batch_pause_routes_every_paid_row_before_stopping(tmp_path):
    """⛔ REVIEW DEFECT 4a, the blocking one. In BATCH mode the whole
    corpus is submitted -- and PAID FOR -- in one job, then collected row
    by row. A CheckpointPause raised out of `sched.complete` inside
    `_collect`'s per-row loop aborted that loop, so every REMAINING row
    of an already-paid batch was never fed, never written, never
    ledgered, and a resumed run re-bought it (at checkpoint_every=25 on
    750 items, ~725 rows). dispatch_core's own R5a doctrine deferred
    CostGateError and poison for exactly this reason and did not know
    about the pause. Now it does: every collected row is routed, THEN
    the pause raises -- before any live rerun can spend more."""
    scripts = TT._scripts()
    cfg = TT._cfg(tmp_path, "batchpause",
                  execution={"mode": "batch", "batch_min_pending": 2,
                             "poll_s": 0})
    cfg["checkpoint_every"], cfg["checkpoint_pause"] = 2, True
    holder = {}

    def factory(prov, c):
        holder["c"] = TT.MockClient(prov, c, scripts)
        return holder["c"]
    code = TE.run_exec(cfg, TT._args(clause=list(TT.CIDS), live=True),
                       client_factory=factory,
                       transport=TT.FakeBatchTransport(scripts))
    rundir = TT._rundir(cfg)
    assert code == 3, "a pause stops the run cleanly"
    # ⛔ EVERY collected row was FED AND LEDGERED -- all five, not the
    # two that preceded the pause. m0003's attempt-1 row is "ok" but
    # incomplete (it needs a repair round), so it is fed and billed and
    # then left for the resume; the other four are finished and written.
    done = ["m0001", "m0002", "m0004", "m0005"]
    for cid in done:
        assert os.path.exists(os.path.join(rundir, cid + ".raw.txt")), \
            f"{cid}'s PAID batch row was discarded by the pause"
    rows = {r["clause_id"] for r in json.load(
        open(os.path.join(rundir, "run.json")))["results"]}
    assert rows == set(done)
    assert holder["c"].calls == len(TT.CIDS), \
        "every clause's batch row must be billed exactly once"
    assert len(holder["c"].ledger) == len(TT.CIDS), \
        "a discarded row is an unledgered row: the spend goes invisible"
    # ⛔ and the pause bought NOTHING more: m0003's repair round, which
    # is a fresh paid draw, is left for the resume
    assert not os.path.exists(os.path.join(rundir, "m0003.json"))
    # the pause still happened, and at the right place
    cks = [r for r in _health(rundir) if r["kind"] == "checkpoint"]
    assert cks and cks[0]["completed"] == 2 and cks[0]["paused"] is True


# ==========================================================================
#  promise_repair honours the same mechanism
# ==========================================================================

def _two_plan_run(tmp_path):
    """The splice-seat fixture run, with a SECOND promise queued so the
    stage has two plans to checkpoint between."""
    run = TS._run(tmp_path)
    d = json.load(open(os.path.join(run, "division.json")))
    second = {"name": "front_desk_duty", "prose": "The front desk duty.",
              "established_around": [3, 4]}
    d["seed_vocabulary"].append(second)
    import recurse_driver as R
    R.write_json(os.path.join(run, "division.json"), d)
    q = json.load(open(os.path.join(run, "fixup_queue.json")))
    q["items"].append({"kind": "broken_promise", "verdict": "reject",
                       "detail": {"unwind": run,
                                  "name": "front_desk_duty"},
                       "reason": "needs regeneration"})
    R.write_json(os.path.join(run, "fixup_queue.json"), q)
    g = json.load(open(os.path.join(run, "root_graph.json")))
    g["nodes"][1]["needs"].append({"name": "front_desk_duty",
                                   "prose": "relies on the desk duty"})
    R.write_json(os.path.join(run, "root_graph.json"), g)
    return run


def _delivers(name):
    return TS._reply(1, 12, provides=[{"name": name,
                                       "prose": f"The {name}."}])


def test_promise_repair_checkpoints_between_plans(tmp_path):
    run = _two_plan_run(tmp_path)
    cfg = TS._cfg(checkpoint_every=1)
    rep = PR.run_repair(run, cfg,
                        TS.SeatClient([_delivers(TS.NAME),
                                       _delivers("front_desk_duty")]),
                        list(TS.ESTABLISHING))
    assert rep["repaired"] == 2 and rep["plans"] == 2
    rows = [json.loads(ln) for ln in
            open(os.path.join(run, "health.jsonl"))]
    cks = [r for r in rows if r["kind"] == "checkpoint"]
    assert [c["completed"] for c in cks] == [1, 2]
    assert [c["remaining"] for c in cks] == [1, 0]
    assert all(c["ceiling_usd"] == 0.25 for c in cks)
    assert cks[0]["failures"] == {"failed": 0, "narration_mismatch": 0,
                                  "rejected_by_splice_seat": 0,
                                  "declined": 0}
    assert rep["checkpoints"] == cks and rep["paused"] is None


def test_a_resumed_paused_repair_does_not_re_pay_for_its_splices(tmp_path):
    """⛔ REVIEW DEFECT 4b: the pause's resume hint was FALSE. prep read
    the ORIGINAL root_graph.json, so the names already spliced into
    root_graph.repaired.json were invisible to `skipped_already_provided`
    -- a resumed run re-drew and RE-PAID every plan and then overwrote
    the partial repaired graph. The rerun now takes the repaired graph as
    its baseline, and says so."""
    run = _two_plan_run(tmp_path)
    first = PR.run_repair(run, TS._cfg(checkpoint_every=1,
                                       checkpoint_pause=True),
                          TS.SeatClient([_delivers(TS.NAME)]),
                          list(TS.ESTABLISHING))
    assert first["repaired"] == 1 and first["paused"]
    assert first["resumed_from"] is None

    # the RESUME: only the unfinished plan may cost anything
    client = TS.SeatClient([_delivers("front_desk_duty")])
    second = PR.run_repair(run, TS._cfg(), client, list(TS.ESTABLISHING))
    assert second["resumed_from"] == "root_graph.repaired.json"
    assert client.calls == 1, \
        "the already-spliced name must not be re-drawn (and re-paid)"
    assert second["repaired"] == 1
    row = next(r for r in second["items"] if r["name"] == TS.NAME)
    assert row["status"] == "skipped_already_provided"
    # and both splices survive in one graph
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert {PR.R.nm(p) for p in fixed["nodes"][0]["provides"]} == \
        {TS.NAME, "front_desk_duty"}
    assert second["paused"] is None


def test_a_completed_run_is_never_a_silent_resume_baseline(tmp_path):
    """The other half of 4b: only a run that RECORDED A PAUSE resumes
    from its own output. A completed run's repaired graph must never
    become the silent base of a second repair -- that would compound
    edits across runs with nothing saying so."""
    run = _two_plan_run(tmp_path)
    PR.run_repair(run, TS._cfg(),
                  TS.SeatClient([_delivers(TS.NAME),
                                 _delivers("front_desk_duty")]),
                  list(TS.ESTABLISHING))
    again = PR.run_repair(run, TS._cfg(),
                          TS.SeatClient([_delivers(TS.NAME),
                                         _delivers("front_desk_duty")]),
                          list(TS.ESTABLISHING))
    assert again["resumed_from"] is None


def test_main_exits_3_on_a_pause(tmp_path, monkeypatch):
    """A paused stage returned 0, so `ds7_repair.sh` (set -e) sailed
    straight past a half-finished repair into the quality battery."""
    run = _two_plan_run(tmp_path)
    calls = {}

    def fake(run_dir, cfg, client, lines):
        calls["cfg"] = cfg
        return {"paused": "paused at checkpoint after 1 item(s)"}
    monkeypatch.setattr(PR, "run_repair", fake)
    monkeypatch.setattr(PR.R, "GraphClient",
                        lambda *a, **k: type("C", (), {})())
    monkeypatch.setattr(PR.R, "load_doc", lambda *a, **k: ["x"])
    assert PR.main([run, "--yes"]) == 3
    fake_ok = lambda *a, **k: {"paused": None}          # noqa: E731
    monkeypatch.setattr(PR, "run_repair", fake_ok)
    assert PR.main([run, "--yes"]) == 0


def test_promise_repair_pause_keeps_the_finished_splice(tmp_path):
    """⛔ NO WORK LOST, stage edition: the pause after plan 1 leaves the
    first splice in root_graph.repaired.json with its report row, and
    the second plan unpaid."""
    run = _two_plan_run(tmp_path)
    cfg = TS._cfg(checkpoint_every=1, checkpoint_pause=True)
    client = TS.SeatClient([_delivers(TS.NAME),
                            _delivers("front_desk_duty")])
    rep = PR.run_repair(run, cfg, client, list(TS.ESTABLISHING))
    assert rep["repaired"] == 1 and rep["plans"] == 2
    assert "paused at checkpoint after 1 item(s)" in rep["paused"]
    assert client.calls == 1, "the second plan must not have been paid for"
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    assert [PR.R.nm(p) for p in fixed["nodes"][0]["provides"]] == [TS.NAME]
    assert [r["status"] for r in rep["items"]] == ["repaired"], \
        "the unattempted plan books no row at all -- it was never tried"
    assert not any(r["name"] == "front_desk_duty" for r in rep["items"])
