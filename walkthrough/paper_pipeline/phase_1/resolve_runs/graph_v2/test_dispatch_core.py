"""Pins for dispatch_core.py (the shared execution core).

The load-bearing claim is EQUIVALENCE: Scheduler+SerialExecutor must be
byte-for-byte the same build as recurse_driver.Driver.build -- prompts,
artifacts, resume. Everything else (concurrency, manifest, batch taxonomy)
is pinned against the review findings it implements (batch_design_review.md
F1-F5)."""
import json
import os
import re
import stat
import sys
import threading
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dispatch_core as DC  # noqa: E402
import recurse_driver as R  # noqa: E402

TOY = os.path.join(HERE, "toy_doc.md")


def _replies():
    return json.load(open(os.path.join(HERE, "mock_replies.json")))


class FakeSched:
    """Duck-typed scheduler surface for executor unit tests."""

    def __init__(self):
        self.completed, self.requeued = [], []

    def complete(self, st):
        self.completed.append(st)

    def requeue(self, st):
        self.requeued.append(st)


def _state(key, out, validate=lambda o: [], cfg=None, user="dispatch",
           wdir=None):
    st = DC.DispatchState(key, key.split(":")[0], wdir or out, user,
                          validate, None, cfg or {}, out)
    st.on_success = lambda obj: None
    return st


# ============================================================ (a) EQUIVALENCE
def test_core_serial_build_is_byte_identical_to_driver_build(tmp_path):
    """The whole point of the shared core (review F1): the reference executor
    IS Driver.build, re-expressed. Same toy doc, same canned replies, same
    artifacts to the byte."""
    lines = R.load_doc(TOY)
    a, b = tmp_path / "driver", tmp_path / "core"
    a.mkdir(), b.mkdir()
    ga = R.Driver({"leaf_max_lines": 15}, R.MockClient(_replies()), lines,
                  str(a)).build(1, len(lines), [], str(a))
    drv = R.Driver({"leaf_max_lines": 15}, R.MockClient(_replies()), lines,
                   str(b))
    gb = DC.run_build(drv, 1, len(lines), [], str(b), "serial")
    # node sets byte-identical, and the whole root artifact too
    assert (json.dumps(ga["nodes"], sort_keys=True)
            == json.dumps(gb["nodes"], sort_keys=True))
    assert (open(a / "graph.json", "rb").read()
            == open(b / "graph.json", "rb").read())
    # the toy semantics the original e2e pins
    assert len(gb["nodes"]) == 10
    provs = {R.nm(p) for n in gb["nodes"] for p in n.get("provides", [])}
    dang = {R.nm(d) for n in gb["nodes"] for d in n.get("needs", [])
            if R.nm(d) not in provs}
    assert dang == {"house_rules"}
    # resume is inviolable: a second core build must not call the model
    class Boom:
        def complete(self, *a):
            raise AssertionError("resume must not re-call the model")
        complete_messages = complete
    drv2 = R.Driver({"leaf_max_lines": 15}, Boom(), lines, str(b))
    g2 = DC.run_build(drv2, 1, len(lines), [], str(b), "serial")
    assert len(g2["nodes"]) == 10


def test_core_serial_sends_the_same_prompt_bytes_as_driver(tmp_path):
    """The core rebuilds the dispatch prompts (extra strings, unwind report)
    rather than calling into Driver's phase methods; this pin is what keeps
    the two from drifting apart."""
    class PromptSpy(R.MockClient):
        def __init__(self, replies, log):
            super().__init__(replies)
            self.log = log

        def complete(self, system, user):
            self.log.append(("c", system, user))
            return R.MockClient.complete(self, system, user)

        def complete_messages(self, system, messages):
            self.log.append(("m", system, json.dumps(messages)))
            return R.MockClient.complete(self, system, "")

    lines = R.load_doc(TOY)
    a, b = tmp_path / "driver", tmp_path / "core"
    a.mkdir(), b.mkdir()
    la, lb = [], []
    R.Driver({"leaf_max_lines": 15}, PromptSpy(_replies(), la), lines,
             str(a)).build(1, len(lines), [], str(a))
    drv = R.Driver({"leaf_max_lines": 15}, PromptSpy(_replies(), lb), lines,
                   str(b))
    DC.run_build(drv, 1, len(lines), [], str(b), "serial")
    assert la == lb, "the core sent different prompt bytes (or a different " \
                     "call order) than Driver.build"


# ============================================================ (b) concurrency
def test_concurrent_executor_overlaps_calls_and_matches_serial(tmp_path):
    """>1 dispatch genuinely in flight (the two toy leaves overlap in
    wall-clock), and the finished graph equals the serial build's. The mock
    is keyed by dispatch identity, not call order -- review F9's constraint
    on any non-serial scheduler."""
    lines = R.load_doc(TOY)
    reps = _replies()
    n = len(lines)
    table = {("D", 1, n): reps[0], ("L", 1, 12): reps[1],
             ("L", 13, n): reps[2], ("U", 1, n): reps[3]}
    log, lock = [], threading.Lock()

    class KeyedMock:
        spent_usd = 0.0

        def complete(self, system, user):
            m = re.search(r"Phase: (\w+)\nSpan: lines (\d+)-(\d+)", user)
            key = (m.group(1), int(m.group(2)), int(m.group(3)))
            with lock:
                log.append(("start", key, time.time()))
            time.sleep(0.2)
            with lock:
                log.append(("end", key, time.time()))
            return {"text": json.dumps(table[key]), "usage": {}}

        def complete_messages(self, system, messages):
            return self.complete(system, messages[0]["content"])

    outc = tmp_path / "conc"
    outc.mkdir()
    drv = R.Driver({"leaf_max_lines": 15}, KeyedMock(), lines, str(outc))
    sched = DC.Scheduler(drv)
    sched.start(1, n, [], str(outc))
    g = DC.ConcurrentExecutor(drv, n=2).run(sched)
    # both leaves were in flight at once
    iv = {}
    for kind, key, t in log:
        iv.setdefault(key, {})[kind] = t
    a, b = iv[("L", 1, 12)], iv[("L", 13, n)]
    assert a["start"] < b["end"] and b["start"] < a["end"], \
        f"leaf calls did not overlap: {iv}"
    # identical result to the serial reference
    outs = tmp_path / "ser"
    outs.mkdir()
    R.Driver({"leaf_max_lines": 15}, R.MockClient(_replies()), lines,
             str(outs)).build(1, n, [], str(outs))
    assert (open(outc / "graph.json", "rb").read()
            == open(outs / "graph.json", "rb").read())
    assert len(g["nodes"]) == 10


# ============================================================== (c) manifest
def test_manifest_sweep_surfaces_orphans_without_deleting(tmp_path):
    """Review F2: a submitted-but-uncollected job must survive a process
    death. sweep() SURFACES the orphan; only an explicit clear() (after
    reconcile-or-requeue) removes it."""
    m = DC.InFlightManifest(str(tmp_path))
    entry = {"batch_id": "b1", "requests": {"x-r0": {"wdir": "", "kind": "L",
                                                     "round": 0}}}
    m.record("job-1", entry)
    m2 = DC.InFlightManifest(str(tmp_path))     # a fresh process
    assert m2.sweep() == [("job-1", entry)]
    assert m2.sweep() == [("job-1", entry)], "sweep must not consume orphans"
    m2.clear("job-1")
    assert m2.sweep() == []
    # atomic write: no tmp residue to wedge a later sweep
    assert not any(f.endswith(".tmp") for f in os.listdir(m.dir))


def test_orphaned_batch_is_reconciled_not_resubmitted(tmp_path, fake_curl):
    """Kill-simulation (review F2): a manifest entry with a batch_id and no
    artifacts. On init the executor polls THAT job and routes its results;
    it never POSTs a new batch for the orphan, so the submitted job is not
    paid twice."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    man = DC.InFlightManifest(str(out))
    cid = "L_leafdir-r0"
    man.record("job-orphan", {
        "batch_id": "batch-1", "input_file_id": "file-1",
        "requests": {cid: {"key": "L:leafdir", "kind": "L",
                           "wdir": "leafdir", "round": 0}}})
    (spool / "out-1.jsonl").write_text(json.dumps({
        "custom_id": cid, "response": {"body": {
            "choices": [{"message": {"content": "{\"n\": 1}"},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5}}}}) + "\n")
    ex = DC.BatchExecutor(drv, {"poll_s": 0}, manifest=man)
    rec = ex._sweep()
    assert ("leafdir", "L") in rec and rec[("leafdir", "L")]["text"] == \
        "{\"n\": 1}"
    assert man.sweep() == [], "reconciled orphan must be cleared"
    calls = [json.loads(ln) for ln in open(log)]
    assert not any("POST" in c and any(a.endswith("/batches") for a in c)
                   for c in calls), "the orphan was blindly resubmitted"
    # the recovered result feeds the dispatch instead of a new submission
    st = _state("L:leafdir", str(out), wdir=str(out / "leafdir"))
    sched = FakeSched()
    ex._recovered = rec
    assert ex._feed_recovered(st, sched) is True
    assert st.status == DC.DONE and st.result == {"n": 1}
    assert sched.completed == [st]


# ================================================= (d) call()-parity pins
def test_dispatch_state_budget_parity(tmp_path):
    """Mirror of test_per_dispatch_budget_stops_expensive_redraws through
    DispatchState: measured cost between draws, loud failure at the cap."""
    st = _state("L:x", str(tmp_path), cfg={"per_dispatch_usd": 0.30})
    st.feed({"text": "not json {", "usage": {"cost_usd": 0.31}})
    assert st.status == DC.FAILED and "spend budget" in st.error


def test_dispatch_state_repair_round_parity(tmp_path):
    """Mirror of test_validator_exception_becomes_repairable (review F12):
    a bad-shape reply becomes an ACCUMULATING repair round, not a crash."""
    bad = {"decision": "divide", "children": [{"span": "1-3"}],
           "seed_vocabulary": [], "expected_cross_links": []}
    good = {"decision": "leaf"}
    st = _state("D:x", str(tmp_path),
                validate=lambda o: R.validate_division(o, 1, 3))
    st.feed({"text": json.dumps(bad), "usage": {}})
    assert st.status == DC.PENDING and st.repair_round == 1
    req = st.next_request()
    assert len(req) == 3
    assert "failed mechanical checks" in req[2]["content"]
    st.feed({"text": json.dumps(good), "usage": {}})
    assert st.status == DC.DONE and st.result == good
    # ... and through the reference executor with the real MockClient
    drv = R.Driver({}, R.MockClient([bad, good]), ["a", "b", "c"],
                   str(tmp_path))
    st2 = _state("D:y", str(tmp_path),
                 validate=lambda o: R.validate_division(o, 1, 3))
    DC.SerialExecutor(drv).run_one(st2)
    assert st2.status == DC.DONE and st2.result == good


def test_dispatch_state_repair_exhaustion_matches_call(tmp_path):
    st = _state("L:x", str(tmp_path), cfg={"max_repairs": 2},
                validate=lambda o: ["always wrong"])
    # replies must DIFFER: byte-identical repair replies now trigger the
    # once-only fresh restart instead (ds5 2026-08-12 pin below)
    for t in ('{}', '{ }', '{  }'):          # initial draw + 2 repair rounds
        st.feed({"text": t, "usage": {}})
    assert st.status == DC.FAILED
    assert "call failed after 2 repair round(s)" in st.error
    # failed repair replies are buried as evidence (review F25 lineage),
    # with the dispatch key in the name (batch collision guard, F5 note)
    buried = os.listdir(os.path.join(str(tmp_path), "failed"))
    assert len(buried) == 2 and all("L_x" in f for f in buried)


def test_dispatch_state_oversize_malfunction_resamples_once(tmp_path):
    """D6 stage 1 wired (ds5 2026-08-12): an oversize first draw that the
    classifier calls MALFUNCTION (dup-loop, garbage) gets ONE fresh
    resample; a second oversize malfunction fails loudly. The old behavior
    hard-failed the whole build with a false 'truncated' diagnosis on a
    COMPLETE 123-node dup-loop reply."""
    st = _state("L:x", str(tmp_path), cfg={"model": {"max_tokens": 4}},
                validate=lambda o: ["bad"])
    st.feed({"text": "x" * 50, "usage": {}})           # garbage = malfunction
    assert st.status == DC.PENDING and st.restarted    # one fresh resample
    assert st.repair_round == 0 and st.spent == 0.0
    assert st.next_request() == [{"role": "user", "content": "dispatch"}]
    st.feed({"text": "x" * 50, "usage": {}})           # resample also melts
    assert st.status == DC.FAILED and "oversize first draw" in st.error
    assert os.listdir(os.path.join(str(tmp_path), "failed"))


def test_dispatch_state_oversize_dense_fails_immediately(tmp_path):
    """A genuinely DENSE oversize first draw (distinct ids, non-repeating
    establishes) is unfixable at this cap: no resample, loud failure."""
    node = ('{{"id": "L1-9_n{i:03d}", "establishes": "distinct claim '
            'number {i} about a different obligation"}}')
    dense = "[" + ",".join(node.format(i=i) for i in range(30)) + "]"
    st = _state("L:x", str(tmp_path), cfg={"model": {"max_tokens": 4}},
                validate=lambda o: ["bad"])
    assert len(dense) > 4 * 3
    st.feed({"text": dense, "usage": {}})
    assert st.status == DC.FAILED and "dense span" in st.error
    assert not st.restarted


def test_dispatch_state_identical_repair_reply_restarts_fresh(tmp_path):
    """ds5 2026-08-12: unwind c3_c1 repeated one 3,127-byte reply across
    repair rounds r1..r3 -- the transcript adds no information, so the
    repair budget was an unfixable loop by construction. A repair reply
    byte-identical to the one it was asked to correct triggers the
    existing once-only fresh restart instead of burning rounds."""
    st = _state("U:x", str(tmp_path), cfg={"max_repairs": 4},
                validate=lambda o: ["bad merge"])
    st.feed({"text": '{"a": 1}', "usage": {}})         # r0 -> repair round 1
    assert st.repair_round == 1
    st.feed({"text": '{"a": 1}', "usage": {}})         # identical -> restart
    assert st.status == DC.PENDING and st.restarted
    assert st.repair_round == 0
    assert st.next_request() == [{"role": "user", "content": "dispatch"}]
    st.feed({"text": '{"a": 1}', "usage": {}})         # restart draw fails...
    st.feed({"text": '{"a": 1}', "usage": {}})         # ...identical again:
    st.feed({"text": '{"a": 1}', "usage": {}})         # no second restart,
    st.feed({"text": '{"a": 1}', "usage": {}})         # rounds burn through
    st.feed({"text": '{"a": 1}', "usage": {}})         # all 4 repairs to the
    assert st.status == DC.FAILED                      # max_repairs fail
    assert "call failed after 4 repair round(s)" in st.error


def test_dispatch_state_fresh_restart_once(tmp_path):
    """Mirror of call()'s _restarted path: a laden repair transcript that
    truncates restarts the dispatch fresh exactly once."""
    st = _state("L:x", str(tmp_path), validate=lambda o: ["bad"])
    st.feed({"text": "{}", "usage": {"cost_usd": 0.01}})
    assert st.repair_round == 1 and st.can_restart()
    st.feed_failure("truncated", "completion was TRUNCATED")
    assert st.status == DC.PENDING and st.repair_round == 0
    assert st.restarted and st.spent == 0.0        # budget re-bases, as call()
    assert st.next_request() == [{"role": "user", "content": "dispatch"}]
    st.feed({"text": "{}", "usage": {}})
    st.feed_failure("truncated", "completion was TRUNCATED")   # second time
    assert st.status == DC.FAILED                  # -> give up loudly


def test_serial_executor_ladder_resamples_transients(tmp_path, monkeypatch):
    """Mirror of test_truncated_draw_is_resampled_not_fatal through the
    reference executor's ladder."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)

    class Flaky:
        calls = 0

        def complete(self, system, user):
            Flaky.calls += 1
            if Flaky.calls == 1:
                raise R.T.ProviderError("completion was TRUNCATED "
                                        "(finish_reason=length). ...")
            if Flaky.calls == 2:
                raise R.T.ProviderError("HTTP 503: service unavailable")
            return {"text": json.dumps({"decision": "leaf"}), "usage": {}}
        complete_messages = complete

    drv = R.Driver({}, Flaky(), ["a"], str(tmp_path))
    st = _state("D:x", str(tmp_path))
    DC.SerialExecutor(drv).run_one(st)
    assert st.result == {"decision": "leaf"} and Flaky.calls == 3


# =============================================== (e) batch executor + taxonomy
FAKE_CURL = '''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
open(os.environ["FAKE_CURL_LOG"], "a").write(json.dumps(args) + "\\n")
url = next(a for a in args if a.startswith("http"))
spool = os.environ["FAKE_CURL_SPOOL"]
def emit(o):
    sys.stdout.write(o if isinstance(o, str) else json.dumps(o))
if url.endswith("/files/upload"):
    src = next(a for a in args if a.startswith("file=@"))[6:]
    open(os.path.join(spool, "input.jsonl"), "w").write(open(src).read())
    emit({"id": "file-1"})
elif url.endswith("/batches"):
    if "POST" in args:
        emit({"id": "batch-1", "status": "VALIDATING"})
    elif os.path.exists(os.path.join(spool, "batch_list_fail")):
        sys.stderr.write("WAF 403 intermittent")
        sys.exit(7)
    else:
        p = os.path.join(spool, "batch_list.json")
        emit(open(p).read() if os.path.exists(p) else {"jobs": []})
elif "/batches/" in url:
    emit({"id": url.rsplit("/", 1)[1], "status": "COMPLETED",
          "output_file_id": "out-1"})
elif "/files/" in url and url.endswith("/content"):
    fid = url.split("/files/")[1].split("/")[0]
    p = os.path.join(spool, fid + ".jsonl")
    if os.path.exists(p):
        emit(open(p).read())
    else:
        # taxonomy fixture rows derived from the submitted JSONL:
        # row 0 ok, row 1 error object, row 2 truncated, row 3 OMITTED
        reqs = [json.loads(l) for l in open(os.path.join(spool,
                                                         "input.jsonl"))]
        rows = []
        for i, r in enumerate(reqs):
            cid = r["custom_id"]
            if i == 0:
                rows.append({"custom_id": cid, "response": {"body": {
                    "choices": [{"message": {"content":
                                             json.dumps({"ok": 1})},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10,
                              "completion_tokens": 5}}}})
            elif i == 1:
                rows.append({"custom_id": cid,
                             "error": {"message": "internal error"}})
            elif i == 2:
                rows.append({"custom_id": cid, "response": {"body": {
                    "choices": [{"message": {"content": "{\\"trunc"},
                                 "finish_reason": "length"}],
                    "usage": {}}}})
        emit("\\n".join(json.dumps(r) for r in rows))
'''


@pytest.fixture
def fake_curl(tmp_path, monkeypatch):
    """A `curl` stub on PATH: the transport's WAF-driven curl dependency is
    exactly what makes the batch path testable for $0."""
    bindir = tmp_path / "fakebin"
    spool = tmp_path / "spool"
    bindir.mkdir(), spool.mkdir()
    stub = bindir / "curl"
    stub.write_text(FAKE_CURL)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "curl_log.jsonl"
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CURL_LOG", str(log))
    monkeypatch.setenv("FAKE_CURL_SPOOL", str(spool))
    return log, spool


def _batch_driver(out):
    cfg = {"model": {"model": "mock-model",
                     "base_url": "http://fake.local/v1",
                     "api_key_env": "X", "max_tokens": 64,
                     "temperature": 0.0},
           "price_per_mtok": [0.14, 0.28]}

    class Dummy:
        spent_usd = 0.0
    return R.Driver(cfg, Dummy(), ["a"], out)


def test_batch_executor_failure_taxonomy(tmp_path, fake_curl):
    """Review F5: batch failures are DATA. One job, four requests: ok /
    http_error / truncated / missing-from-output. The ok item completes; the
    three failures requeue as live -- no exception-string matching anywhere
    in the path."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    ex = DC.BatchExecutor(drv, {"batch_min_pending": 4, "poll_s": 0})
    live = []
    ex._run_live = lambda st, sched: live.append(st)
    sched = FakeSched()
    states = [_state(f"L:t{i}", str(out), user=f"user {i}",
                     wdir=os.path.join(str(out), f"t{i}"))
              for i in range(4)]
    jobs = ex._flush(states, sched)
    assert len(jobs) == 1 and jobs[0]["batch_id"] == "batch-1"
    # per-request bodies carried their own response_format (review F4)
    sent = [json.loads(ln) for ln in
            open(os.path.join(spool, "input.jsonl"))]
    assert all("response_format" in r["body"] for r in sent)
    assert [r["custom_id"] for r in sent] == [st.custom_id()
                                              for st in states]
    # the manifest covered the job while it was in flight (review F2)
    assert [n for n, _ in ex.manifest.sweep()] == [jobs[0]["name"]]
    j = ex.transport.status(jobs[0]["batch_id"])
    tax = ex._collect(jobs[0], ex._rows(j["output_file_id"]), sched)
    cids = [st.custom_id() for st in states]
    assert [tax[c] for c in cids] == ["ok", "http_error", "truncated",
                                      "missing"]
    assert states[0].status == DC.DONE and states[0].result == {"ok": 1}
    assert sched.completed == [states[0]]
    assert live == states[1:], "non-ok items must requeue as live"


def test_batch_validation_failure_requeues_as_repair_round(tmp_path,
                                                           fake_curl):
    """An 'ok' row that fails validation is not a transport failure: it
    advances the repair round and re-enters the ready queue (repair rounds
    batch too -- BATCH_DESIGN engagement rule)."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    sched = FakeSched()
    st = _state("L:t0", str(out), validate=lambda o: ["not good enough"])
    jobs = ex._flush([st], sched)
    j = ex.transport.status(jobs[0]["batch_id"])
    ex._collect(jobs[0], ex._rows(j["output_file_id"]), sched)
    assert st.status == DC.PENDING and st.repair_round == 1
    assert sched.requeued == [st]


def test_batch_submit_gate_refuses_over_ceiling(tmp_path, fake_curl):
    """Review F3: the ceiling is enforced at SUBMIT on worst-case arithmetic
    -- an unaffordable flush never reaches the provider; its dispatches run
    live under the per-call measured backstop."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    drv.client.max_cost_usd = 0.0        # nothing is affordable as a batch
    ex = DC.BatchExecutor(drv, {"batch_min_pending": 2})
    live = []
    ex._run_live = lambda st, sched: live.append(st)
    states = [_state(f"L:t{i}", str(out)) for i in range(2)]
    jobs = ex._flush(states, FakeSched())
    assert jobs == [] and live == states
    assert not os.path.exists(log), "a gated flush still hit the provider"


def test_batch_executor_end_to_end_on_toy_doc(tmp_path, fake_curl):
    """The full loop (sweep -> flush -> poll -> collect -> starvation
    fallback) on the toy tree. min_pending=2: the root division runs LIVE
    (queue of 1 < K, nothing in flight -- the top of the tree never waits),
    the two leaves ship as ONE batch job, and the unwind falls back to live
    again. The finished graph byte-matches the serial reference."""
    log, spool = fake_curl
    lines = R.load_doc(TOY)
    n = len(lines)
    reps = _replies()
    table = {("D", 1, n): reps[0], ("L", 1, 12): reps[1],
             ("L", 13, n): reps[2], ("U", 1, n): reps[3]}

    def reply_for(user):
        m = re.search(r"Phase: (\w+)\nSpan: lines (\d+)-(\d+)", user)
        return table[(m.group(1), int(m.group(2)), int(m.group(3)))]

    class KeyedMock:
        spent_usd = 0.0

        def complete(self, system, user):
            return {"text": json.dumps(reply_for(user)), "usage": {}}

        def complete_messages(self, system, messages):
            return self.complete(system, messages[0]["content"])

    # the batch output file is built from the submitted JSONL by a second
    # stub pass: write it AFTER flush via the spool hook below
    outb = tmp_path / "batch"
    outb.mkdir()
    cfg = {"leaf_max_lines": 15,
           "model": {"model": "mock-model",
                     "base_url": "http://fake.local/v1",
                     "api_key_env": "X", "max_tokens": 16384,
                     "temperature": 0.0},
           "price_per_mtok": [0.14, 0.28]}
    drv = R.Driver(cfg, KeyedMock(), lines, str(outb))
    ex = DC.BatchExecutor(drv, {"batch_min_pending": 2, "poll_s": 0})
    orig_flush = ex._flush

    def flush_and_answer(states, sched):
        jobs = orig_flush(states, sched)
        if jobs:
            rows = []
            for ln in open(os.path.join(spool, "input.jsonl")):
                req = json.loads(ln)
                user = req["body"]["messages"][-1]["content"]
                rows.append({"custom_id": req["custom_id"], "response": {
                    "body": {"choices": [{
                        "message": {"content":
                                    json.dumps(reply_for(user))},
                        "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 3,
                                  "completion_tokens": 3}}}})
            (spool / "out-1.jsonl").write_text(
                "\n".join(json.dumps(r) for r in rows))
        return jobs
    ex._flush = flush_and_answer
    sched = DC.Scheduler(drv)
    sched.start(1, n, [], str(outb))
    g = ex.run(sched)
    assert len(g["nodes"]) == 10
    # exactly one batch job was created (the leaf layer); D and U ran live
    calls = [json.loads(ln) for ln in open(log)]
    creates = [c for c in calls if "POST" in c
               and any(a.endswith("/batches") for a in c)]
    assert len(creates) == 1
    # in-flight manifest is empty after a clean finish (review F2)
    assert ex.manifest.sweep() == []
    outs = tmp_path / "ser"
    outs.mkdir()
    R.Driver({"leaf_max_lines": 15}, R.MockClient(_replies()), lines,
             str(outs)).build(1, n, [], str(outs))
    assert (open(outb / "graph.json", "rb").read()
            == open(outs / "graph.json", "rb").read())


# ==================================== (f) review R1-R10 fixes (2026-08-11)
class _BilledFlaky:
    """Bills BEFORE raising, exactly as translate.Client._send does: its
    _log_usage runs before the truncation/emptiness guards raise, so a
    TRUNCATED draw increments client.spent_usd and then raises."""

    def __init__(self, cost=0.12, failures=2):
        self.spent_usd, self.calls = 0.0, 0
        self.cost, self.failures = cost, failures

    def complete(self, system, user):
        self.calls += 1
        self.spent_usd += self.cost           # billed ...
        if self.calls <= self.failures:       # ... then raised
            raise R.T.ProviderError(
                "completion was TRUNCATED (finish_reason=length)")
        return {"text": json.dumps({"decision": "leaf"}),
                "usage": {"cost_usd": self.cost}}

    def complete_messages(self, system, messages):
        return self.complete(system, messages[0]["content"])


def test_budget_counts_billed_failed_draws_like_driver_call(tmp_path,
                                                            monkeypatch):
    """Review R1 (probe P1's scenario): budget $0.30, draws $0.12,
    TRUNCATED/TRUNCATED/clean. Driver.call fails loudly at $0.36 because
    _over() reads the client.spent_usd delta; the core executor must reach
    the same outcome from the same client behavior."""
    monkeypatch.setattr(R.time, "sleep", lambda s: None)
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)
    cfg = {"per_dispatch_usd": 0.30}
    drv = R.Driver(cfg, _BilledFlaky(), ["a"], str(tmp_path / "a"))
    with pytest.raises(R.T.Phase1Error) as ei:
        drv.call("dispatch", lambda o: [])
    assert "spend budget" in str(ei.value)
    drv2 = R.Driver(cfg, _BilledFlaky(), ["a"], str(tmp_path / "b"))
    st = _state("L:x", str(tmp_path / "b"), cfg=cfg)
    DC.SerialExecutor(drv2).run_one(st)
    assert st.status == DC.FAILED and "spend budget" in st.error
    assert st.spent == pytest.approx(0.36)     # both truncations counted
    assert drv2.client.calls == 3              # same draws as Driver.call


def test_budget_stops_the_ladder_between_billed_attempts(tmp_path,
                                                         monkeypatch):
    """Review R1, the ruling's point: once billed failed draws blow the
    budget, the ladder stops PAYING for retries instead of riding out all
    seven attempts (Driver.call would pay on; stopping is the cheaper
    direction, deliberately)."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)
    client = _BilledFlaky(cost=0.12, failures=7)
    drv = R.Driver({"per_dispatch_usd": 0.20}, client, ["a"], str(tmp_path))
    st = _state("L:x", str(tmp_path), cfg={"per_dispatch_usd": 0.20})
    with pytest.raises(R.T.Phase1Error) as ei:
        DC.SerialExecutor(drv).run_one(st)
    assert "spend budget" in str(ei.value)
    assert client.calls == 2, "the ladder kept paying past the budget"
    assert st.spent == pytest.approx(0.24)


def _ok_row(cid, obj):
    return {"custom_id": cid, "response": {"body": {
        "choices": [{"message": {"content": json.dumps(obj)},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5}}}}


def test_create_kill_window_adopts_live_job(tmp_path, fake_curl):
    """Review R2 kill-simulation (probe P3's window): a record with an
    input_file_id but no batch_id -- killed inside the create round-trip --
    while the provider holds a live job for that file. The sweep must adopt
    and reconcile that job, never clear the record as never-created (which
    resubmits and double-pays). A record whose file has NO provider job is
    genuinely clean and clears."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    man = DC.InFlightManifest(str(out))
    cid = "L_leafdir-r0"
    man.record("job-kill", {           # killed after create() was accepted
        "input_file_id": "file-77",
        "requests": {cid: {"key": "L:leafdir", "kind": "L",
                           "wdir": "leafdir", "round": 0}}})
    man.record("job-kill2", {          # killed before create() was accepted
        "input_file_id": "file-99",
        "requests": {"L_other-r0": {"key": "L:other", "kind": "L",
                                    "wdir": "other", "round": 0}}})
    (spool / "batch_list.json").write_text(json.dumps(
        {"jobs": [{"id": "batch-77", "input_file_id": "file-77",
                   "status": "COMPLETED"}]}))
    (spool / "out-1.jsonl").write_text(
        json.dumps(_ok_row(cid, {"n": 2})) + "\n")
    ex = DC.BatchExecutor(drv, {"poll_s": 0}, manifest=man)
    rec = ex._sweep()
    assert rec[("leafdir", "L")]["text"] == "{\"n\": 2}"
    assert ("other", "L") not in rec           # no job existed: re-enqueues
    assert man.sweep() == [], "reconciled/clean records must both clear"
    calls = [json.loads(ln) for ln in open(log)]
    assert not any("POST" in c and any(a.endswith("/batches") for a in c)
                   for c in calls), "the kill-window job was resubmitted"


def test_create_kill_window_unlistable_keeps_record_and_goes_live(
        tmp_path, fake_curl, monkeypatch):
    """Review R2, the endpoint-cannot-answer arm: if the batch listing is
    unavailable, the indeterminate record is KEPT (it may prove a live paid
    job) and its dispatches are marked live-only -- never resubmitted as a
    batch on a guess."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    man = DC.InFlightManifest(str(out))
    man.record("job-kill", {
        "input_file_id": "file-77",
        "requests": {"L_leafdir-r0": {"key": "L:leafdir", "kind": "L",
                                      "wdir": "leafdir", "round": 0}}})
    (spool / "batch_list_fail").write_text("1")
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0},
                          manifest=man)
    rec = ex._sweep()
    assert rec == {}
    assert [n for n, _ in man.sweep()] == ["job-kill"], \
        "an indeterminate record was cleared while the provider was mute"
    assert ("leafdir", "L") in ex._live_only


def test_sweep_persists_recovered_results_before_clearing(tmp_path,
                                                          fake_curl):
    """Review R3 kill-simulation: at the moment the manifest entry is
    cleared, the recovered envelopes must already be on disk -- and a fresh
    process (crash between clear and feed) must recover them from the
    spool instead of resubmitting paid work."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    man = DC.InFlightManifest(str(out))
    cid = "L_leafdir-r0"
    man.record("job-orphan", {
        "batch_id": "batch-1", "input_file_id": "file-1",
        "requests": {cid: {"key": "L:leafdir", "kind": "L",
                           "wdir": "leafdir", "round": 0}}})
    (spool / "out-1.jsonl").write_text(
        json.dumps(_ok_row(cid, {"n": 3})) + "\n")
    orig_clear = man.clear

    def checking_clear(name, _o=orig_clear):
        assert os.path.exists(os.path.join(man.dir, name + ".recovered")), \
            "manifest cleared before recovered results reached disk (R3)"
        _o(name)
    man.clear = checking_clear
    ex = DC.BatchExecutor(drv, {"poll_s": 0}, manifest=man)
    rec = ex._sweep()
    assert rec[("leafdir", "L")]["text"] == "{\"n\": 3}"
    # crash-after-clear simulation: a brand-new process still has the result
    ex2 = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0},
                           manifest=DC.InFlightManifest(str(out)))
    rec2 = ex2._sweep()
    assert rec2[("leafdir", "L")]["text"] == "{\"n\": 3}"


def test_submit_gate_counts_worst_case_of_all_inflight_jobs(tmp_path,
                                                            fake_curl):
    """Review R4 (probe P4's scenario): two flushes that each fit the
    ceiling alone must NOT both submit when their combined worst-case
    overcommits it -- and collecting the first job releases its commitment
    so later flushes can proceed."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    ex = DC.BatchExecutor(drv, {"poll_s": 0})
    w = ex._worst_case_usd(ex._request_body(_state("L:p", str(out))))
    assert w > 0
    drv.client.max_cost_usd = 2.5 * w
    live = []
    ex._run_live = lambda st, sched: live.append(st)
    sched = FakeSched()
    first = [_state(f"L:a{i}", str(out)) for i in range(2)]
    jobs1 = ex._flush(first, sched)
    assert len(jobs1) == 1 and ex.outstanding_worst == pytest.approx(2 * w)
    second = [_state(f"L:b{i}", str(out)) for i in range(2)]
    jobs2 = ex._flush(second, sched)
    assert jobs2 == [] and live == second, \
        "the second flush ignored the in-flight job's committed worst-case"
    calls = [json.loads(ln) for ln in open(log)]
    creates = [c for c in calls if "POST" in c
               and any(a.endswith("/batches") for a in c)]
    assert len(creates) == 1
    # collection releases the commitment
    live.clear()
    assert ex._poll_and_collect(jobs1, sched) == []
    assert ex.outstanding_worst == pytest.approx(0.0)
    jobs3 = ex._flush([_state("L:c0", str(out))], sched)
    assert len(jobs3) == 1, "collected worst-case was never released"


def test_collect_persists_ok_rows_before_live_rerun_can_raise(tmp_path,
                                                              fake_curl):
    """Review R5a (probe P2's scenario): a job whose non-ok row reruns live
    and dies must NOT discard collected, paid ok rows later in iteration
    order -- every ok row is fed (artifact written, completion committed)
    before any rerun runs."""
    log, spool = fake_curl

    class Unrepairable:
        spent_usd = 0.0

        def complete(self, *a):
            raise R.T.ProviderError("HTTP 400: permanently poisoned")
        complete_messages = complete

    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    drv.client = Unrepairable()
    ex = DC.BatchExecutor(drv, {"poll_s": 0})
    sched = FakeSched()
    s_ok = _state("L:t0", str(out))
    s_err = _state("L:t1", str(out))
    jobs = ex._flush([s_ok, s_err], sched)   # fixture: row 0 ok, row 1 error
    job = jobs[0]
    # iterate the error state FIRST -- the old interleaving died here
    job["states"] = dict(reversed(list(job["states"].items())))
    j = ex.transport.status(job["batch_id"])
    with pytest.raises(R.T.ProviderError):
        ex._collect(job, ex._rows(j["output_file_id"]), sched)
    assert s_ok.status == DC.DONE and s_ok.result == {"ok": 1}
    assert sched.completed == [s_ok], \
        "a collected, paid ok row was discarded by the interleaved rerun"


def test_poison_stops_run_after_successes_and_before_rerun_spend(
        tmp_path, fake_curl):
    """Review R5 poison ordering, pinned end to end: successes are committed
    first, the poison Phase1Error fires before any live rerun spends money
    on a run that has decided to stop, and the manifest entry survives so
    the rerun states re-enqueue on resume."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    live = []
    ex._run_live = lambda st, sched: live.append(st)
    sched = FakeSched()
    poison = _state("L:p", str(out), validate=lambda o: ["never right"],
                    cfg={"max_repairs": 0})
    ok = _state("L:ok", str(out))
    err = _state("L:err", str(out))
    jobs = ex._flush([poison, ok, err], sched)
    (spool / "out-1.jsonl").write_text(
        json.dumps(_ok_row(poison.custom_id(), {"x": 1})) + "\n"
        + json.dumps(_ok_row(ok.custom_id(), {"x": 2})) + "\n")
    job = jobs[0]
    j = ex.transport.status(job["batch_id"])
    with pytest.raises(R.T.Phase1Error) as ei:
        ex._collect(job, ex._rows(j["output_file_id"]), sched)
    assert "call failed after 0 repair round(s)" in str(ei.value)
    assert ok.status == DC.DONE and sched.completed == [ok]
    assert live == [], "live rerun spend after the poison abort decision"
    assert [n for n, _ in ex.manifest.sweep()] == [job["name"]], \
        "manifest must survive the poison abort so resume covers the rest"


def test_sweep_ledgers_billed_non_ok_rows_and_skips_written(tmp_path,
                                                            fake_curl):
    """Review R8 (probe P5) + R5b: a truncated orphan row -- billed at
    submit -- must reach the ledger during sweep; an ok row whose artifact
    already exists was ledgered before the crash and must NOT be ledgered
    again."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()

    class LedgerSpy:
        spent_usd = 0.0

        def __init__(self):
            self.rows = []

        def _log_usage(self, env):
            self.rows.append(env)

    drv = _batch_driver(str(out))
    drv.client = LedgerSpy()
    man = DC.InFlightManifest(str(out))
    man.record("job-o", {"batch_id": "batch-1", "requests": {
        "L_a-r0": {"key": "L:a", "kind": "L", "wdir": "a", "round": 0},
        "L_b-r0": {"key": "L:b", "kind": "L", "wdir": "b", "round": 0}}})
    trunc = {"custom_id": "L_a-r0", "response": {"body": {
        "choices": [{"message": {"content": "{\"tr"},
                     "finish_reason": "length"}],
        "usage": {"prompt_tokens": 9, "completion_tokens": 9}}}}
    (spool / "out-1.jsonl").write_text(
        json.dumps(trunc) + "\n"
        + json.dumps(_ok_row("L_b-r0", {"done": 1})) + "\n")
    os.makedirs(out / "b")
    R.write_json(str(out / "b" / "graph.json"), {"done": 1})  # pre-crash
    ex = DC.BatchExecutor(drv, {"poll_s": 0}, manifest=man)
    rec = ex._sweep()
    assert len(drv.client.rows) == 1, \
        "billed truncated orphan row missed the ledger (R8) or the " \
        "already-written row was double-ledgered (R5b)"
    assert drv.client.rows[0]["truncated"] is True
    assert rec == {}       # truncated is no result; written row re-resumes


def test_flaky_status_poll_is_retried_not_fatal(tmp_path, fake_curl,
                                                monkeypatch):
    """Review R7: the transport exists BECAUSE of an intermittent WAF; one
    flaky status poll must be retried, not abort the run."""
    monkeypatch.setattr(DC.time, "sleep", lambda s: None)
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    ex._run_live = lambda st, sched: None
    sched = FakeSched()
    jobs = ex._flush([_state("L:t0", str(out))], sched)
    real = ex.transport

    class Flaky:
        n = 0

        def status(self, bid):
            Flaky.n += 1
            if Flaky.n == 1:
                raise R.T.ProviderError(
                    "batch endpoint returned non-JSON: '<html>WAF</html>'")
            return real.status(bid)

        def content(self, fid):
            return real.content(fid)
    ex._transport = Flaky()
    assert ex._poll_and_collect(jobs, sched) == []
    assert Flaky.n == 2, "the flaky poll was not retried"


def test_flush_refuses_custom_id_collision(tmp_path, fake_curl):
    """Review R10: two rel-paths that _safe_id collapses to one custom_id
    would silently drop a state from the job and stall the scheduler; the
    flush must refuse loudly instead."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    s1 = _state("L:c1/c2", str(out))
    s2 = _state("L:c1_c2", str(out))
    with pytest.raises(R.T.Phase1Error, match="custom_id"):
        ex._flush([s1, s2], FakeSched())


# ==================== (g) delta_review_driver.md D1/D3/D4 (2026-08-11)
DS3_FLAGS = {"leaf_max_lines": 15, "transcript_continuity": True,
             "derive_uncovered": True, "rename_candidates": True}


class _PromptSpy(R.MockClient):
    """Logs every outbound prompt (and the full message transcript) plus the
    schema name / schema bytes / per-phase output cap the call carried --
    the review's blind spot was that every equivalence pin ran flags-off."""
    reply_schema = None
    max_tokens_override = None
    _schema_rejected = False

    def __init__(self, replies, log):
        super().__init__(replies)
        self.log = log

    def _meta(self):
        return (self.reply_schema and self.reply_schema[0],
                json.dumps(self.reply_schema and self.reply_schema[1],
                           sort_keys=True),
                self.max_tokens_override)

    def complete(self, system, user):
        self.log.append(("c", system, user) + self._meta())
        return R.MockClient.complete(self, system, user)

    def complete_messages(self, system, messages):
        self.log.append(("m", system, json.dumps(messages)) + self._meta())
        return R.MockClient.complete(self, system, "")


def test_core_serial_matches_driver_with_all_ds3_flags_on(tmp_path):
    """delta_review_driver.md D1, the headline pin: with EVERY ds3 flag on
    (transcript_continuity + derive_uncovered + rename_candidates), the
    core must send the same prompt/transcript bytes, the same schema (the
    derived leaf variant, the dangling/node-capped unwind grammar), the
    same per-phase output caps, in the same order as Driver.build -- and
    land byte-identical artifacts. Before the fix the core sent a bare
    unwind string, the ds2 leaf dispatch, the uncapped static unwind
    schema, and no phase caps."""
    lines = R.load_doc(TOY)
    n = len(lines)
    a, b = tmp_path / "driver", tmp_path / "core"
    a.mkdir(), b.mkdir()
    la, lb = [], []
    ga = R.Driver(dict(DS3_FLAGS), _PromptSpy(_replies(), la), lines,
                  str(a)).build(1, n, [], str(a))
    drv = R.Driver(dict(DS3_FLAGS), _PromptSpy(_replies(), lb), lines,
                   str(b))
    gb = DC.run_build(drv, 1, n, [], str(b), "serial")
    assert la == lb, "flags-on core build diverged from Driver.build " \
                     "(prompt bytes, schema, phase cap, or call order)"
    assert (open(a / "graph.json", "rb").read()
            == open(b / "graph.json", "rb").read())
    assert (json.dumps(ga, sort_keys=True) == json.dumps(gb, sort_keys=True))
    # the flags were genuinely EXERCISED, not vacuously equal:
    # continuity -- the unwind went out as [D-user, D-reply, U-user]
    tri = [json.loads(e[2]) for e in lb if e[0] == "m"]
    tri = [m for m in tri if len(m) == 3]
    assert tri, "no unwind carried the divider transcript"
    assert tri[0][0]["content"].startswith("YOUR DISPATCH\nPhase: D")
    assert json.loads(tri[0][1]["content"])["decision"] == "divide"
    assert "Phase: U" in tri[0][2]["content"]
    # derive_uncovered -- leaf prompts carry the derive addendum and the
    # derived schema (no `uncovered` required)
    leaves = [e for e in lb if e[3] == "leaf_graph_derived"]
    assert leaves and all("do NOT emit `uncovered`" in e[2] for e in leaves)
    assert all("uncovered" not in json.loads(e[4])["required"]
               for e in leaves)
    # unwind grammar caps -- the capped schema, not the static one
    unwinds = [e for e in lb if e[3] == "unwind_decisions"]
    assert unwinds
    assert all("maxItems" in json.loads(e[4])["properties"]["resolutions"]
               for e in unwinds)
    # per-phase output caps engaged on every call
    caps = R.Driver.PHASE_MAX_TOKENS
    for e in lb:
        assert e[5] == caps.get(e[3]) and e[5] is not None, \
            f"phase cap missing on a {e[3]} call: {e[5]}"


def test_batch_request_bodies_honor_per_phase_caps(tmp_path):
    """delta review D1, batch half: _request_body must carry the per-phase
    output cap (division 8K / leaf 24K / unwind 8K), not the provider-wide
    max_tokens -- driver_config's '_max_tokens' note was false off-serial."""
    out = tmp_path / "run"
    out.mkdir()
    drv = _batch_driver(str(out))
    ex = DC.BatchExecutor(drv, {"poll_s": 0})
    st = _state("L:x", str(out))
    st.schema = ("leaf_graph", {"type": "object"})
    assert (ex._request_body(st)["max_tokens"]
            == R.Driver.PHASE_MAX_TOKENS["leaf_graph"])
    st.schema = ("unwind_decisions", {"type": "object"})
    assert (ex._request_body(st)["max_tokens"]
            == R.Driver.PHASE_MAX_TOKENS["unwind_decisions"])
    # cfg phase_max_tokens overrides, exactly as Driver.call
    drv.cfg["phase_max_tokens"] = {"unwind_decisions": 123}
    assert ex._request_body(st)["max_tokens"] == 123
    # no schema -> provider max_tokens (the pre-existing behavior)
    st.schema = None
    assert ex._request_body(st)["max_tokens"] == 64


def test_resolution_pass_strips_ghost_structure_nodes_and_merges(tmp_path,
                                                                 capsys):
    """delta review D3 (probe P6): run_resolution_pass applied
    structure_nodes/merges UNVALIDATED (lo=hi=lines=None skips leaf-grade
    checks but still appends) -- a hallucinated ghost node with a span
    outside the document landed in the final graph. The pass admits
    resolutions ONLY: ghosts are stripped with a log line, the grammar caps
    both shapes at 0, and the resolutions still apply."""
    g = {"nodes": [
        {"id": "a", "establishes": "provider", "needs": [],
         "provides": [{"name": "real_name", "prose": "the concept"}],
         "spans": [{"lines": [1, 1]}]},
        {"id": "b", "establishes": "needer",
         "needs": [{"name": "other_name", "prose": "the concept"}],
         "provides": [], "spans": [{"lines": [2, 2]}]}]}
    reply = {"resolutions": [{"needer": "b", "name": "other_name",
                              "rename_to": "real_name"}],
             "merges": [{"survivor": "a", "retired": "b"}],
             "structure_nodes": [
                 {"id": "L900-999_ghost", "establishes": "fabricated",
                  "needs": [], "provides": [],
                  "spans": [{"lines": [900, 999],
                             "quote": "text that exists nowhere"}]}],
             "judgment_calls": []}
    drv = R.Driver({}, R.MockClient([reply]), ["x", "y"], str(tmp_path))
    g2 = R.run_resolution_pass(drv, g, str(tmp_path))
    ids = [n["id"] for n in g2["nodes"]]
    assert "L900-999_ghost" not in ids, "ghost node reached the final graph"
    assert ids == ["a", "b"], "a merge was applied by the resolution pass"
    assert g2["nodes"][1]["needs"][0]["name"] == "real_name"
    assert any("resolutions ONLY" in x
               for x in g2.get("driver_autofixes", []))
    assert "resolutions ONLY" in capsys.readouterr().out
    # and the pass's grammar refuses both shapes outright
    name, sch = R.resolution_schema(3, 10)
    assert sch["properties"]["structure_nodes"]["maxItems"] == 0
    assert sch["properties"]["merges"]["maxItems"] == 0
    assert name == "unwind_decisions", \
        "renaming the schema would drop the pass's per-phase output cap"


def test_self_satisfy_guard_holds_for_duplicated_provides_name():
    """delta review D4 (probe P3): a node providing the target name TWICE
    gave provides[name] == [id, id] != [id], bypassing the F5 list-equality
    guard -- the need resolved against its own node. The guard must compare
    as SETS: the resolution drops, the need stays dangling and escalates."""
    nodes = [{"id": "a", "establishes": "x",
              "needs": [{"name": "alias", "prose": "p"}],
              "provides": [{"name": "target", "prose": "p"},
                           {"name": "target", "prose": "p again"}],
              "spans": [{"lines": [1, 1]}]}]
    provides = {"target": ["a", "a"]}
    log, errs = R.apply_decisions(nodes, {"resolutions": [
        {"needer": "a", "name": "alias", "rename_to": "target"}]}, provides)
    assert errs == []
    assert any("DROPPED self-satisfying" in x for x in log)
    assert nodes[0]["needs"][0]["name"] == "alias", \
        "the need was resolved against its own node (F5 bypass)"
    # the legitimate case is untouched: a DIFFERENT node providing the name
    nodes2 = [dict(nodes[0], needs=[{"name": "alias", "prose": "p"}]),
              {"id": "z", "establishes": "y", "needs": [],
               "provides": [{"name": "target", "prose": "p"}],
               "spans": [{"lines": [2, 2]}]}]
    log2, errs2 = R.apply_decisions(nodes2, {"resolutions": [
        {"needer": "a", "name": "alias", "rename_to": "target"}]},
        {"target": ["a", "a", "z"]})
    assert errs2 == [] and any(x.startswith("resolved") for x in log2)


# ------------------------------------------------------------ mode selection
def test_executor_selection_from_config():
    class D:
        pass
    drv = D()
    drv.client, drv.out, drv.cfg = None, ".", {}
    assert isinstance(DC.build_executor("serial", drv), DC.SerialExecutor)
    with pytest.raises(R.T.Phase1Error):
        DC.build_executor("warp", drv)


def test_batch_truncation_backstop_fires_on_null_finish_reason():
    """ds4 live 2026-08-11: finish_reason null + completion_tokens at the
    requested cap must classify as truncated, never ok."""
    import dispatch_core as DC
    ex = DC.BatchExecutor.__new__(DC.BatchExecutor)
    ex.prov = type("P", (), {"price_per_mtok": [0.14, 0.28],
                             "model": "m", "name": "p"})()
    ex._req_max = {"job-x": 8192}
    row = {"custom_id": "job-x", "response": {"body": {
        "choices": [{"message": {"content": '{"decision": "divide", '
                                            '"children": ['},
                     "finish_reason": None}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8192}}}}
    kind, env = ex._classify(row)
    assert kind == "truncated", kind


# ------- latent-branch pins (coverage measurement, 2026-08-12) -------------
# After ds5 failed twice inside guard branches no test had ever executed,
# branch coverage was run over the guard stack; these pin the highest-value
# remaining failure-handling paths.

def test_batch_job_level_failure_reruns_live(tmp_path, fake_curl):
    """F5 job-level death: a batch whose STATUS is FAILED/EXPIRED/CANCELLED
    reruns every request live -- never a blind batch resubmit. The worst-case
    ceiling rolls back and the manifest record clears."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    live = []
    ex._run_live = lambda st, sched: live.append(st)
    sched = FakeSched()
    states = [_state(f"L:t{i}", str(out), user=f"user {i}",
                     wdir=os.path.join(str(out), f"t{i}"))
              for i in range(2)]
    jobs = ex._flush(states, sched)
    assert len(jobs) == 1
    ex._rpc = lambda fn, *a: {"status": "FAILED"}
    remaining = ex._poll_and_collect(jobs, sched)
    assert remaining == []
    assert live == states, "a dead batch's requests must rerun live"
    assert ex.outstanding_worst == 0.0
    assert [n for n, _ in ex.manifest.sweep()] == []


def test_feed_recovered_invalid_reply_requeues_for_repair(tmp_path,
                                                          fake_curl):
    """A recovered orphan reply that fails validation is NOT a transport
    failure: it advances the repair round and requeues -- the normal repair
    path takes over from the recovered draw."""
    log, spool = fake_curl
    out = tmp_path / "run"
    out.mkdir()
    ex = DC.BatchExecutor(_batch_driver(str(out)), {"poll_s": 0})
    sched = FakeSched()
    st = _state("L:t0", str(out), validate=lambda o: ["not good enough"],
                wdir=os.path.join(str(out), "t0"))
    key = (os.path.relpath(st.wdir, ex.drv.out), st.kind)
    ex._recovered = {key: {"text": "{}", "usage": {}}}
    assert ex._feed_recovered(st, sched)
    assert st.status == DC.PENDING and st.repair_round == 1
    assert sched.requeued == [st]
    assert sched.completed == []
