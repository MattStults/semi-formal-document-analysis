"""Pins for the 2026-08-14 routing-gap fix set (EXPERIMENTS.md: "routing-gap
audit COMPLETE" F1-F10 + the IDENTICAL-RETRY SEAM GUARD design + the ds7
RESIDUALS (a) coinage-variant widening).

Every guard here was proven RED by feeding it the defect it catches: each
test's docstring names the pre-fix behavior the assertion would have seen.
No network, no spend -- transports and clients are stubs throughout."""
import json
import os
import sys
import threading
import time
import urllib.request

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import graveyard as gy          # noqa: E402
import translate as T           # noqa: E402
import translate_exec as TE     # noqa: E402
import dispatch_core as DC      # noqa: E402
import recurse_driver as R      # noqa: E402
import rename_seat as RS        # noqa: E402


# --------------------------------------------------------------- helpers
def _client(monkeypatch, **model_cfg):
    monkeypatch.setenv("FAKE_KEY", "k")
    prov = T.Provider("stub", "openai-compatible", "m", "http://fake/v1",
                      "FAKE_KEY", 0.0, 64, None)
    cfg = {"model": dict({"format_forcing": "json_object",
                          "usage_log": ""}, **model_cfg)}
    return T.Client(prov, cfg)


class _FakeResp:
    def __init__(self, payload):
        self._p = json.dumps(payload).encode()

    def read(self, *a):
        return self._p

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ok_payload(text='{"ok": 1}', finish="stop", out_toks=5):
    return {"choices": [{"message": {"content": text},
                         "finish_reason": finish}],
            "usage": {"prompt_tokens": 10, "completion_tokens": out_toks}}


class FakeSched:
    def __init__(self):
        self.completed, self.requeued = [], []
        self.lock = threading.Lock()

    def complete(self, st):
        self.completed.append(st)

    def requeue(self, st):
        self.requeued.append(st)


def _state(key, out, validate=lambda o: [], cfg=None, user="dispatch",
           schema=None, wdir=None):
    st = DC.DispatchState(key, key.split(":")[0], wdir or out, user,
                          validate, schema, cfg or {}, out)
    st.on_success = lambda obj: None
    return st


def _driver(out, client=None, cfg=None):
    class Dummy:
        spent_usd = 0.0
    return R.Driver(cfg or {}, client or Dummy(), ["a"], out)


# =================================================== 1. identical-retry guard
def test_seam_guard_varies_a_resend_of_a_failed_body(tmp_path, monkeypatch):
    """THE DEFECT: a body that failed at transport was re-sent
    byte-identically (the ds7 truncation lock-in). The guard must make the
    second send's bytes differ, via the marker on the FINAL user message,
    with the prefix unchanged (cache economics)."""
    c = _client(monkeypatch)
    sent, fail = [], [True]

    def fake_urlopen(req, timeout=None):
        sent.append(req.data)
        if fail[0]:
            fail[0] = False
            raise OSError("connection reset")
        return _FakeResp(_ok_payload())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    body = c._body("sys", "hello clause")
    with pytest.raises(T.ProviderError):
        c._send(json.loads(json.dumps(body)))
    env = c._send(json.loads(json.dumps(body)))
    assert env["text"] == '{"ok": 1}'
    assert len(sent) == 2
    assert sent[0] != sent[1], "identical failed retry left the client " \
                               "byte-identical (the lock-in defect)"
    assert b"[transport retry 1: prior identical attempt failed]" in sent[1]
    assert b"[transport retry" not in sent[0]
    # prefix unchanged: everything up to the final user content is identical
    head = sent[0].split(b"hello clause")[0] + b"hello clause"
    assert sent[1].startswith(head)
    p0, p1 = json.loads(sent[0]), json.loads(sent[1])
    assert p1["messages"][-1]["content"] == (
        p0["messages"][-1]["content"]
        + "\n[transport retry 1: prior identical attempt failed]")
    assert {k: v for k, v in p1.items() if k != "messages"} \
        == {k: v for k, v in p0.items() if k != "messages"}
    # telemetry: the trigger was counted on the client
    assert c.retry_variations == 1
    # a NOVEL body is never varied
    c._send(c._body("sys", "a different clause"))
    assert b"[transport retry" not in sent[-1]
    assert c.retry_variations == 1


def test_seam_guard_covers_billed_then_raised_truncation(tmp_path,
                                                         monkeypatch):
    """THE MOTIVATING INCIDENT: a TRUNCATED draw raises AFTER transport
    succeeded (the envelope guard), and the ladder used to redraw the same
    bytes. The failed-hash set must include guard-raised sends too."""
    c = _client(monkeypatch)
    sent = []

    def fake_urlopen(req, timeout=None):
        sent.append(req.data)
        return _FakeResp(_ok_payload(text='{"cut', finish="length"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    body = c._body("sys", "hello")
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        c._send(json.loads(json.dumps(body)))
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        c._send(json.loads(json.dumps(body)))
    assert sent[0] != sent[1]
    assert b"[transport retry 1: prior identical attempt failed]" in sent[1]


def test_seam_guard_marks_only_the_last_user_message(tmp_path,
                                                     monkeypatch):
    """Review item 8: the marker lands ONLY on the last USER turn -- a
    laden repair transcript's assistant turns are never mutated, and a
    body with no user message at all is re-sent unchanged."""
    c = _client(monkeypatch)
    sent, fail = [], [True]

    def fake_urlopen(req, timeout=None):
        sent.append(req.data)
        if fail[0]:
            fail[0] = False
            raise OSError("boom")
        return _FakeResp(_ok_payload())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    body = c._body_messages("sys", [
        {"role": "user", "content": "first ask"},
        {"role": "assistant", "content": "half an answer"},
        {"role": "user", "content": "repair ask"}])
    with pytest.raises(T.ProviderError):
        c._send(json.loads(json.dumps(body)))
    c._send(json.loads(json.dumps(body)))
    p1 = json.loads(sent[1])
    msgs = [m for m in p1["messages"] if m["role"] != "system"]
    assert msgs[0]["content"] == "first ask"
    assert msgs[1]["content"] == "half an answer", \
        "an assistant turn was mutated"
    assert msgs[2]["content"].endswith(
        "\n[transport retry 1: prior identical attempt failed]")
    # no user message anywhere: the body goes out unchanged, unvaried
    c2 = _client(monkeypatch)
    weird = {"model": "m", "max_tokens": 8, "messages": [
        {"role": "system", "content": "s"},
        {"role": "assistant", "content": "a"}]}
    fail[0] = True
    with pytest.raises(T.ProviderError):
        c2._send(json.loads(json.dumps(weird)))
    c2._send(json.loads(json.dumps(weird)))
    assert sent[-1] == sent[-2], \
        "a userless body must be re-sent unchanged, never mutated"
    assert c2.retry_variations == 0


# ============================================ 2. F1 truncation short ladder
def test_core_ladder_caps_truncated_retries_at_two(tmp_path, monkeypatch):
    """THE DEFECT (F1): TRUNCATED rode the FULL transient ladder -- six
    byte-identical redraws. It now gets variation + two tries (like the
    402 short ladder), then raises to the restart paths."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)

    class AlwaysTrunc:
        calls = 0

        def complete(self, system, user):
            AlwaysTrunc.calls += 1
            raise T.ProviderError("completion was TRUNCATED "
                                  "(finish_reason=length). ...")
        complete_messages = complete

    drv = _driver(str(tmp_path), AlwaysTrunc())
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        DC.SerialExecutor(drv).run_one(_state("D:x", str(tmp_path)))
    assert AlwaysTrunc.calls == 3, \
        "TRUNCATED must stop after 2 retries, not ride the full ladder"


def test_driver_ladder_caps_truncated_retries_at_two(tmp_path, monkeypatch):
    """Same pin through recurse_driver.Driver._complete (the untouched
    serial path's own ladder)."""
    monkeypatch.setattr(R.time, "sleep", lambda s: None)
    calls = []

    def method():
        calls.append(1)
        raise T.ProviderError("completion was TRUNCATED ...")

    drv = _driver(str(tmp_path))
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        drv._complete(method)
    assert len(calls) == 3


# ==================================================== 3. F2 translation gate
def test_translate_client_log_usage_enforces_the_ceiling(monkeypatch):
    """THE DEFECT (F2): translate_exec set max_cost_usd on a client that
    never checked it -- the measured ceiling was UNENFORCED in translation
    concurrent/batch. Client._log_usage must bill, then raise, exactly as
    GraphClient does."""
    c = _client(monkeypatch)
    c.max_cost_usd = 1.0
    c._log_usage({"usage": {"cost_usd": 0.4}})       # under: no raise
    with pytest.raises(T.CostGateError, match="max_cost_usd"):
        c._log_usage({"usage": {"cost_usd": 5.0}})
    # billed BEFORE the raise: the ledger never under-counts a gated call
    assert c.spent_usd == pytest.approx(5.4)


def test_tolerant_executor_propagates_the_cost_gate():
    """translate_exec assumption re-checked: the per-clause tolerance must
    NOT swallow CostGateError (tolerating it would bill one more call per
    remaining clause)."""
    delivered = []

    class Boom:
        def run_one(self, state):
            raise T.CostGateError("measured spend exceeds the run ceiling")

    class Tol(TE._TolerantRunOne, Boom):
        pass

    class St:
        status = TE.PENDING

        def feed_failure(self, kind, detail):
            delivered.append((kind, detail))
            self.status = TE.DONE

    with pytest.raises(T.CostGateError):
        Tol().run_one(St())
    assert delivered, "the clause thread must still be unwound"


# ============================================= 4. F3 seat terminal transport
def test_seat_raises_on_terminal_transport(monkeypatch):
    """THE DEFECT (F3): rename_seat.judge absorbed 402/401/403 and key
    failures into fail-closed different_concept -- a mid-finale credit
    exhaustion would grind 600 descend calls into silent all-rejections."""
    monkeypatch.setattr(time, "sleep", lambda s: None)
    for msg in ("HTTP 402: credit exhausted", "HTTP 401: bad key",
                "HTTP 403: forbidden",
                "no key for $TOGETHER_API_KEY: not in the environment"):
        def complete(system, user, _m=msg):
            raise T.ProviderError(_m)
        with pytest.raises(T.ProviderError):
            RS.judge(complete, "prompt")


def test_seat_still_fails_closed_on_genuine_transients(monkeypatch):
    """The other direction: a 503/timeout after bounded retries stays
    fail-closed (an outage-lost rename is an honest dangling), and
    CostGateError still propagates by name."""
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def flaky(system, user):
        raise T.ProviderError("HTTP 503: service unavailable")
    v = RS.judge(flaky, "prompt")
    assert v["verdict"] == "different_concept"
    assert "fail-closed" in v["grounds"]

    def gated(system, user):
        raise T.CostGateError("ceiling")
    with pytest.raises(T.CostGateError):
        RS.judge(gated, "prompt")


# ========================================== 5. F4 finish_reason-null backstop
def test_check_envelope_catches_null_finish_at_the_cap(monkeypatch):
    """THE DEFECT (F4): together returns finish_reason null on this model,
    so a live reply cut at the cap sailed past the truncation guard and
    failed a stage later as a parse error. completion_tokens >= the
    requested cap IS truncation, whatever finish_reason says."""
    env = {"text": '{"nodes": [', "finish_reason": None, "truncated": False,
           "usage": {"completion_tokens": 64}, "requested_max_tokens": 64}
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        T._check_envelope(env)
    # below the cap, a null finish_reason stays the documented pass
    ok = T._check_envelope({"text": '{"nodes": []}', "finish_reason": None,
                            "usage": {"completion_tokens": 10},
                            "requested_max_tokens": 64})
    assert ok["text"] == '{"nodes": []}'


def test_send_stamps_the_requested_cap_into_the_envelope(monkeypatch):
    """The backstop only has the cap because _send passes it: a null-finish
    reply at exactly max_tokens must raise TRUNCATED out of _send."""
    c = _client(monkeypatch)

    def fake_urlopen(req, timeout=None):
        return _FakeResp(_ok_payload(text='{"cut', finish=None,
                                     out_toks=json.loads(req.data)
                                     ["max_tokens"]))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        c._send(c._body("sys", "hello"))


# ================================================== 6. F5 engaged-cap oversize
def test_state_oversize_threshold_uses_the_engaged_phase_cap(tmp_path,
                                                             monkeypatch):
    """THE DEFECT (F5): the oversize threshold read model.max_tokens
    (32768) while phase caps bounded replies far below it -- the D6
    dense/malfunction machinery was dead code. A leaf-schema state with
    the phase cap engaged must consult the classifier on a reply oversized
    AT THE PHASE CAP."""
    consulted = []
    monkeypatch.setattr(R, "classify_cap_overflow",
                        lambda text: consulted.append(len(text))
                        or "malfunction")
    st = _state("L:x", str(tmp_path), validate=lambda o: ["bad"],
                cfg={"model": {"max_tokens": 32768}},
                schema=("leaf_graph", {"type": "object"}))
    assert st.out_cap == 24576, "leaf phase cap must be the engaged cap"
    big = "x" * (24576 * 3 + 10)          # oversize at the PHASE cap,
    st.feed({"text": big, "usage": {}})   # well under 32768*3
    assert consulted, "the dense/malfunction classifier was never " \
                      "consulted (dead code at engaged caps)"
    assert st.restarted and st.status == DC.PENDING, \
        "a malfunction must resample fresh once"


def test_driver_call_oversize_threshold_uses_the_engaged_phase_cap(
        tmp_path, monkeypatch):
    """Same pin through Driver.call (the untouched serial path)."""
    consulted = []
    monkeypatch.setattr(R, "classify_cap_overflow",
                        lambda text: consulted.append(len(text))
                        or "malfunction")
    big = "x" * (24576 * 3 + 10)

    class BigMock:
        spent_usd = 0.0

        def complete(self, system, user):
            return {"text": big, "usage": {}}
        complete_messages = complete

    drv = _driver(str(tmp_path), BigMock(),
                  cfg={"model": {"max_tokens": 32768}})
    with pytest.raises(T.Phase1Error, match="oversize first draw"):
        drv.call("user", lambda o: ["bad"],
                 schema=("leaf_graph", {"type": "object"}))
    assert len(consulted) == 2, \
        "classifier consulted on the draw AND the spent resample"


# ================================================= 7. F6 empty reply is a draw
def test_empty_reply_is_transient_with_the_short_cap(tmp_path, monkeypatch):
    """THE DEFECT (F6): an empty live reply aborted the build immediately
    while batch mode reran it. Both ladders now treat it like truncation:
    variation + two tries, then raise."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)
    monkeypatch.setattr(R.time, "sleep", lambda s: None)

    class Empty:
        calls = 0

        def complete(self, system, user):
            Empty.calls += 1
            raise T.ProviderError("empty response")
        complete_messages = complete

    drv = _driver(str(tmp_path), Empty())
    with pytest.raises(T.ProviderError, match="empty response"):
        DC.SerialExecutor(drv).run_one(_state("D:x", str(tmp_path)))
    assert Empty.calls == 3, "empty reply must retry (not abort) and " \
                             "stop at the short cap (not ride the ladder)"
    # recovery: one empty draw, then a clean one -- the build continues
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise T.ProviderError("empty response")
        return {"text": "{}", "usage": {}}
    assert _driver(str(tmp_path))._complete(flaky) == {"text": "{}",
                                                       "usage": {}}
    assert len(calls) == 2


# =========================================== 8. F8 statusless poll backstop
class _NoStatusTransport:
    def __init__(self):
        self.polls = 0

    def status(self, bid):
        self.polls += 1
        return {"error": {"message": "internal"}}


def test_poll_and_collect_raises_after_three_statusless_polls(tmp_path):
    """THE DEFECT (F8): a status reply with no recognizable status field
    ({"error": ...}) polled forever as not-yet-terminal."""
    ex = DC.BatchExecutor(_driver(str(tmp_path)), {"poll_s": 0},
                          transport=_NoStatusTransport())
    jobs = [{"name": "j1", "batch_id": "b1", "worst": 0.0, "states": {}}]
    sched = FakeSched()
    jobs = ex._poll_and_collect(jobs, sched)
    jobs = ex._poll_and_collect(jobs, sched)
    with pytest.raises(T.ProviderError, match="no status field"):
        ex._poll_and_collect(jobs, sched)
    assert ex._transport.polls == 3


def test_sweep_wait_loop_raises_after_three_statusless_polls(tmp_path):
    """Same backstop in _sweep's orphan wait loop."""
    out = tmp_path / "run"
    out.mkdir()
    man = DC.InFlightManifest(str(out))
    man.record("job-1", {"batch_id": "b1", "input_file_id": "f1",
                         "requests": {}})
    ex = DC.BatchExecutor(_driver(str(out)), {"poll_s": 0},
                          transport=_NoStatusTransport(),
                          manifest=man)
    with pytest.raises(T.ProviderError, match="no status field"):
        ex._sweep()


# ======================================= 9. F9 cost-gate type preservation
def test_ladder_preserves_cost_gate_type_over_budget_diagnosis(tmp_path,
                                                               monkeypatch):
    """THE DEFECT (F9): when the run ceiling and the per-dispatch budget
    blew on the same billed draw, the ladder re-raised the budget's
    Phase1Error -- laundering the CostGateError into a per-dispatch
    diagnosis. The ceiling outranks."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)

    class Gated:
        spent_usd = 0.0

        def complete(self, system, user):
            Gated.spent_usd += 10.0       # billed, THEN the gate raised
            raise T.CostGateError(
                "measured spend $10.00 exceeds the run ceiling")
        complete_messages = complete

    drv = _driver(str(tmp_path), Gated())
    st = _state("D:x", str(tmp_path), cfg={"per_dispatch_usd": 0.001})
    with pytest.raises(T.CostGateError, match="run ceiling"):
        DC.SerialExecutor(drv).run_one(st)


# ============================================== 10. F10 GraveyardError exits
def test_translate_main_catches_graveyard_error(monkeypatch, capsys):
    """THE DEFECT (F10): gy.GraveyardError is a bare RuntimeError (it
    cannot subclass Phase1Error -- import direction), so a cap refusal
    escaped main() as a traceback instead of a usage-error exit 2."""
    monkeypatch.setattr(T, "load_config", lambda p: (_ for _ in ()).throw(
        gy.GraveyardError("graveyard cap reached: 12 unexamined entries")))
    assert T.main([]) == 2
    assert "GraveyardError" in capsys.readouterr().err


def test_translate_exec_main_catches_graveyard_error(monkeypatch, capsys):
    monkeypatch.setattr(T, "load_config", lambda p: (_ for _ in ()).throw(
        gy.GraveyardError("graveyard cap reached")))
    assert TE.main([]) == 2
    assert "GraveyardError" in capsys.readouterr().out


# ================================== 11. F7 _req_max survives a process death
class _RecordingTransport:
    def __init__(self, rows_fn):
        self.rows_fn = rows_fn
        self.calls = []

    def upload(self, path, name):
        self.calls.append("upload")
        self.jsonl = open(path).read()
        return "file-1"

    def create(self, fid):
        self.calls.append("create")
        return {"id": "batch-1"}

    def status(self, bid):
        self.calls.append("status")
        return {"id": bid, "status": "COMPLETED", "output_file_id": "of-1"}

    def content(self, fid):
        return "\n".join(json.dumps(r) for r in self.rows_fn())


def test_flush_persists_req_max_and_sweep_rebuilds_it(tmp_path):
    """THE DEFECT (F7, deterministic half): _req_max lived only in memory,
    so a resumed sweep's _classify lost the completion-at-cap truncation
    backstop -- a truncated null-finish row recovered as 'ok'."""
    out = tmp_path / "run"
    out.mkdir()
    rows = []
    tr = _RecordingTransport(lambda: rows)
    ex = DC.BatchExecutor(_driver(str(out),
                                  cfg={"model": {"max_tokens": 32768},
                                       "price_per_mtok": [0.14, 0.28]}),
                          {"poll_s": 0}, transport=tr)
    st = _state("L:t0", str(out), schema=("leaf_graph", {"type": "object"}),
                wdir=os.path.join(str(out), "leafdir"))
    jobs = ex._flush([st], FakeSched())
    cid = st.custom_id()
    # the requested phase cap is PERSISTED in the manifest entry
    entry = dict(ex.manifest.sweep())[jobs[0]["name"]]
    assert entry["requests"][cid]["max_tokens"] == 24576
    # a fresh process (the kill): null finish_reason, completion AT the cap
    rows.append({"custom_id": cid, "response": {"body": {
        "choices": [{"message": {"content": '{"nodes": []}'},
                     "finish_reason": None}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 24576}}}})
    ex2 = DC.BatchExecutor(_driver(str(out),
                                   cfg={"model": {"max_tokens": 32768},
                                        "price_per_mtok": [0.14, 0.28]}),
                           {"poll_s": 0}, transport=tr,
                           manifest=DC.InFlightManifest(str(out)))
    recovered = ex2._sweep()
    assert (ex2._req_max or {}).get(cid) == 24576, \
        "_req_max must be rebuilt from the persisted manifest"
    assert recovered == {}, \
        "a truncated-at-cap row must NOT recover as ok on resume"


# =================================== 11b. review item 4: gate mid-collection
class _GatedLedgerClient:
    """_log_usage bills, then raises the F2 ceiling -- every call."""

    def __init__(self):
        self.spent_usd, self.envs = 0.0, []

    def _log_usage(self, env):
        self.envs.append(env)
        self.spent_usd += (env.get("usage") or {}).get("cost_usd") or 0.0
        raise T.CostGateError("measured spend exceeds the run ceiling")


def _ok_row(cid, text='{"ok": 1}'):
    return {"custom_id": cid, "response": {"body": {
        "choices": [{"message": {"content": text},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}}}}


def test_collect_defers_the_cost_gate_until_rows_are_routed(tmp_path):
    """Review item 4 (THE DEFECT: F2 made _log_usage raise, and a raise at
    _collect's ledger site would drop every later paid row unfed): the
    gate is DEFERRED -- all collected rows feed and complete first, the
    live reruns never start, then the CostGateError raises."""
    out = tmp_path / "run"
    out.mkdir()
    drv = _driver(str(out), _GatedLedgerClient())
    ex = DC.BatchExecutor(drv, {"poll_s": 0},
                          transport=_NoStatusTransport())
    reruns = []
    ex._run_live = lambda st, sched: reruns.append(st)
    sched = FakeSched()
    sts = [_state(f"L:t{i}", str(out), user=f"user {i}",
                  wdir=os.path.join(str(out), f"t{i}")) for i in range(3)]
    job = {"name": "j1", "batch_id": "b1", "worst": 0.0,
           "states": {st.custom_id(): st for st in sts}}
    rows = [_ok_row(sts[0].custom_id()),
            _ok_row(sts[1].custom_id())]      # sts[2] missing -> rerun
    with pytest.raises(T.CostGateError, match="run ceiling"):
        ex._collect(job, rows, sched)
    assert sts[0].status == DC.DONE and sts[1].status == DC.DONE, \
        "paid rows in hand must still be fed"
    assert sched.completed == [sts[0], sts[1]]
    assert len(drv.client.envs) == 2, "both rows reached the ledger"
    assert reruns == [], "the ceiling must stop the run BEFORE live reruns"


def test_sweep_defers_the_gate_until_recovered_rows_persist(tmp_path):
    """Item 4's _sweep half: the gate raises only AFTER _persist_recovered
    and the record clear -- the paid rows are spooled to disk and a resume
    cannot re-ledger them (no double-ledger)."""

    class Completed(_NoStatusTransport):
        def status(self, bid):
            return {"id": bid, "status": "COMPLETED",
                    "output_file_id": "of-1"}

        def content(self, fid):
            return json.dumps(_ok_row("L_leafdir-r0"))

    out = tmp_path / "run"
    out.mkdir()
    man = DC.InFlightManifest(str(out))
    man.record("job-1", {"batch_id": "b1", "input_file_id": "f1",
                         "requests": {"L_leafdir-r0": {
                             "key": "L:leafdir", "kind": "L",
                             "wdir": "leafdir", "round": 0}}})
    drv = _driver(str(out), _GatedLedgerClient())
    ex = DC.BatchExecutor(drv, {"poll_s": 0}, transport=Completed(),
                          manifest=man)
    with pytest.raises(T.CostGateError, match="run ceiling"):
        ex._sweep()
    assert len(drv.client.envs) == 1
    spool = [f for f in os.listdir(man.dir) if f.endswith(".recovered")]
    assert spool, "the paid row must be spooled BEFORE the gate raises"
    assert not [f for f in os.listdir(man.dir) if f.endswith(".json")], \
        "the record must be cleared so a resume cannot re-ledger"
    # the resume: a fresh executor loads the spool with ZERO ledger calls
    drv2 = _driver(str(out), _GatedLedgerClient())
    ex2 = DC.BatchExecutor(drv2, {"poll_s": 0}, transport=Completed(),
                           manifest=DC.InFlightManifest(str(out)))
    recovered = ex2._sweep()
    assert ("leafdir", "L") in recovered
    assert drv2.client.envs == [], "resume double-ledgered a spooled row"


# ============================================ 12. coinage variants (item 13)
_DS7_VARIANTS = ("ask_clarifying_questions_section_guideline_authority",
                 "respect_creators_section_user_authority",
                 "x_section_authority",
                 "section_authority")


def test_authority_coinage_pattern_catches_ds7_variants():
    """THE DEFECT (ds7 RESIDUALS (a)): the literal 'section_authority'
    substring check missed variant coinages of the
    'X_section_<level>_authority' shape. One shared pattern; the five
    canonical names and the hierarchy never match."""
    for name in _DS7_VARIANTS:
        assert R.is_authority_coinage(name), name
    for name in ("root_authority", "system_authority",
                 "developer_authority", "user_authority",
                 "guideline_authority", "authority_levels_hierarchy"):
        assert not R.is_authority_coinage(name), name
    assert not R.is_authority_coinage("sectional_authority_notes")
    assert not R.is_authority_coinage(None)


def test_validate_leaf_rejects_variant_coinages():
    g = {"nodes": [{"id": "L1-4_n01", "establishes": "x",
                    "needs": [{"name": _DS7_VARIANTS[0], "prose": "p"}],
                    "provides": [], "spans": [{"lines": [1, 2]}]}]}
    errs = R.validate_leaf(g, 1, 4, ["a", "b", "c", "d"])
    assert any("authority coinage" in e for e in errs), errs


def test_autofix_canonicalizes_variant_coinages():
    lines = ["# section", "authority=guideline", "text a", "text b"]
    g = {"nodes": [{"id": "L3-4_n01", "establishes": "x", "needs": [],
                    "provides": [{"name": _DS7_VARIANTS[0], "prose": "p"}],
                    "spans": [{"lines": [3, 4]}]}]}
    R.autofix_authority_coinages(g, lines)
    assert g["nodes"][0]["provides"][0]["name"] == "guideline_authority"
    assert g.get("driver_autofixes"), "the rename must be recorded"
