"""Pins for translate_exec.py — the opt-in concurrent/batch execution modes
over the translation harness.

The load-bearing claim is EQUIVALENCE with serial translate.py: the same
fakes, driven through dispatch_core's executors, must produce the same
per-clause artifacts (module JSON, .lp, version sidecar, raw, transcript,
concept table) and the same run.json rows in every deterministic field.
Plus BATCH_DESIGN.md's mixed-round ruling (attempt-1 and round-k repairs
share one batch) and the graveyard cap firing BEFORE any executor work.

No network, no API spend: MockClient serves scripted replies live, and
FakeBatchTransport serves the same script through the batch envelope shape.
"""
import copy
import json
import os
import re
import sys
import threading

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import fixtures                # noqa: E402  (the shared stage-1 fixtures)
import graveyard as gy         # noqa: E402
import translate as T          # noqa: E402
import translate_exec as TE    # noqa: E402
import dispatch_core as dc     # noqa: E402

CIDS = ["m0001", "m0002", "m0003", "m0004", "m0005"]

#: the measured per-call price of the mock's fixed usage (1000 in, 500 out)
#: at config.json's [0.14, 0.28] $/Mtok — so live and batch rows cost the same
CALL_COST = 1000 / 1e6 * 0.14 + 500 / 1e6 * 0.28


# --------------------------------------------------------------------------
#  fakes
# --------------------------------------------------------------------------

_CLAUSE_RE = re.compile(r"clause id: (\S+)")
_CID_ROUND = re.compile(r"^T_(.+)-r(\d+)$")


def good(cid):
    return fixtures.module_json(clause_id=cid)


class MockClient:
    """Scripted replies keyed by clause id and ATTEMPT NUMBER (read off the
    transcript structure, never a call counter, so serial / concurrent /
    batch-with-live-repairs all index the script identically)."""

    def __init__(self, prov, cfg, scripts):
        self.p, self.cfg = prov, cfg
        self.scripts = scripts
        self.spent_usd, self.calls = 0.0, 0
        self.ledger = []
        self.lock = threading.Lock()

    def _serve(self, cid, idx):
        seq = self.scripts[cid]
        text = seq[min(idx, len(seq) - 1)]
        self._log_usage({"text": text,
                         "usage": {"prompt_tokens": 1000,
                                   "completion_tokens": 500,
                                   "cost_usd": CALL_COST}})
        return {"text": text, "in": 1000, "out": 500, "cost_usd": CALL_COST}

    def complete(self, system, user):
        return self._serve(_CLAUSE_RE.search(user).group(1), 0)

    def complete_messages(self, system, messages):
        cid = _CLAUSE_RE.search(messages[0]["content"]).group(1)
        idx = sum(1 for m in messages if m["role"] == "assistant")
        return self._serve(cid, idx)

    def _log_usage(self, env):
        with self.lock:
            self.calls += 1
            self.spent_usd += (env.get("usage") or {}).get("cost_usd") or 0.0
            self.ledger.append(env)


class FakeBatchTransport:
    """The Batch API as data: upload/create/status/content over the same
    scripts, one output row per request, indexed by the round in the
    custom_id."""

    def __init__(self, scripts):
        self.scripts = scripts
        self.files, self.jobs = {}, {}
        self.n = 0
        self.uploaded_payloads = []

    def upload(self, path, name):
        self.n += 1
        fid = f"file-{self.n}"
        self.files[fid] = open(path, encoding="utf-8").read()
        self.uploaded_payloads.append(self.files[fid])
        return fid

    def create(self, file_id):
        self.n += 1
        bid = f"batch-{self.n}"
        rows = []
        for ln in self.files[file_id].strip().splitlines():
            req = json.loads(ln)
            cid, rnd = _CID_ROUND.match(req["custom_id"]).groups()
            seq = self.scripts[cid]
            text = seq[min(int(rnd), len(seq) - 1)]
            rows.append({"custom_id": req["custom_id"], "response": {"body": {
                "choices": [{"message": {"content": text},
                             "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1000,
                          "completion_tokens": 500}}}})
        ofid = f"out-{bid}"
        self.files[ofid] = "\n".join(json.dumps(r) for r in rows)
        self.jobs[bid] = {"id": bid, "status": "COMPLETED",
                          "output_file_id": ofid, "input_file_id": file_id}
        return {"id": bid}

    def status(self, batch_id):
        return self.jobs[batch_id]

    def list_batches(self):
        return list(self.jobs.values())

    def content(self, file_id):
        return self.files[file_id]


# --------------------------------------------------------------------------
#  config / args plumbing
# --------------------------------------------------------------------------

class Args:
    clause = section = kinds = limit = provider = model = max_tokens = None
    live = False
    show_prompt = 0
    only_stale = False
    waivers = None


def _args(**over):
    return type("A", (Args,), over)()


def _corpus(tmp_path):
    rows = [{"id": cid, "quote": f"Clause {cid} text.", "section_id": "sec_a",
             "kind": "definitional", "locator": f"§{i}"}
            for i, cid in enumerate(CIDS, 1)]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"clauses": rows}))
    return str(path)


def _cfg(tmp_path, run_name, execution=None):
    cfg = copy.deepcopy(T.load_config(T.DEFAULT_CONFIG))
    cfg["corpus"]["path"] = _corpus(tmp_path)
    cfg["output"] = {"dir": str(tmp_path / "runs"), "run_name": run_name}
    cfg["graveyard"]["dir"] = str(tmp_path / f"gy_{run_name}")
    cfg["cost"]["max_cost_usd"] = 5.0
    cfg["model"]["usage_log"] = ""   # tests must not touch the repo ledger
    if execution is not None:
        cfg["execution"] = execution
    else:
        cfg.pop("execution", None)
    return cfg


def _scripts():
    """m0003 fails attempt 1 (not JSON) and repairs on attempt 2; the rest
    translate first try — so the equivalence run exercises the repair round
    in every mode."""
    s = {cid: [good(cid)] for cid in CIDS}
    s["m0003"] = ["this is not JSON at all", good("m0003")]
    return s


def _rundir(cfg):
    return os.path.join(cfg["output"]["dir"], cfg["output"]["run_name"])


def _run_serial(tmp_path, capsys=None):
    cfg = _cfg(tmp_path, "serial")
    client = {}

    def factory(prov, c):
        client["c"] = MockClient(prov, c, _scripts())
        return client["c"]

    code = T.run(cfg, _args(clause=list(CIDS), live=True),
                 client_factory=factory)
    return code, _rundir(cfg), client["c"]


def _run_exec(tmp_path, execution, run_name, transport=None):
    cfg = _cfg(tmp_path, run_name, execution=execution)
    client = {}

    def factory(prov, c):
        client["c"] = MockClient(prov, c, _scripts())
        return client["c"]

    code = TE.run_exec(cfg, _args(clause=list(CIDS), live=True),
                       client_factory=factory, transport=transport)
    return code, _rundir(cfg), client["c"]


def _rows(rundir):
    rj = json.load(open(os.path.join(rundir, "run.json"), encoding="utf-8"))
    return {r["clause_id"]: r for r in rj["results"]}


def _assert_equivalent(a_dir, b_dir):
    """The deterministic parts must be byte-identical: module JSON, .lp,
    version sidecars, raw responses, transcripts, concept table, and every
    run.json row field except the timestamped graveyard entry name."""
    for cid in CIDS:
        for suffix in (".json", ".lp", ".version.json", ".raw.txt",
                       ".transcript.json", ".prompt_user.txt"):
            fa, fb = (os.path.join(d, cid + suffix) for d in (a_dir, b_dir))
            assert os.path.exists(fa), f"serial run lacks {cid}{suffix}"
            assert os.path.exists(fb), f"exec run lacks {cid}{suffix}"
            assert open(fa, "rb").read() == open(fb, "rb").read(), \
                f"{cid}{suffix} differs between serial and exec"
    ca, cb = (open(os.path.join(d, T.CONCEPT_TABLE)).read()
              for d in (a_dir, b_dir))
    assert ca == cb, "concept tables differ"
    ra, rb = _rows(a_dir), _rows(b_dir)
    assert set(ra) == set(rb) == set(CIDS)
    for cid in CIDS:
        a, b = dict(ra[cid]), dict(rb[cid])
        # the graveyard entry NAME carries a wall-clock stamp; the decision
        # to keep is deterministic, so presence must still agree
        assert ("graveyard" in a) == ("graveyard" in b), cid
        a.pop("graveyard", None), b.pop("graveyard", None)
        assert a == b, f"run.json row for {cid} differs: {a} != {b}"


# ==========================================================================
#  refusal: this module never runs serial
# ==========================================================================

def test_refuses_to_run_without_an_execution_block(tmp_path):
    cfg = _cfg(tmp_path, "noexec")
    with pytest.raises(T.ConfigError, match="translate.py IS serial mode"):
        TE.run_exec(cfg, _args(clause=list(CIDS), live=True))


def test_refuses_an_explicit_serial_mode(tmp_path):
    cfg = _cfg(tmp_path, "serialmode", execution={"mode": "serial"})
    with pytest.raises(T.ConfigError, match="run plain translate.py"):
        TE.run_exec(cfg, _args(clause=list(CIDS), live=True))


def test_refuses_an_unknown_mode(tmp_path):
    cfg = _cfg(tmp_path, "badmode", execution={"mode": "warp"})
    with pytest.raises(T.ConfigError, match="concurrent | batch"):
        TE.run_exec(cfg, _args(clause=list(CIDS), live=True))


# ==========================================================================
#  (a) 5-clause equivalence: concurrent == serial on the same fakes
# ==========================================================================

def test_concurrent_mode_matches_serial_translate_on_the_same_fakes(tmp_path):
    code_a, dir_a, client_a = _run_serial(tmp_path)
    code_b, dir_b, client_b = _run_exec(
        tmp_path, {"mode": "concurrent", "concurrent_n": 3}, "conc")
    assert code_a == code_b == 0
    _assert_equivalent(dir_a, dir_b)
    # the spend ledger is identical: same number of measured rows, same money
    assert client_a.calls == client_b.calls == len(CIDS) + 1  # one repair
    assert client_a.spent_usd == pytest.approx(client_b.spent_usd)
    assert client_a.spent_usd == pytest.approx(client_a.calls * CALL_COST)
    # run.json's spend block carries the measured total in both
    for d in (dir_a, dir_b):
        rj = json.load(open(os.path.join(d, "run.json")))
        assert rj["spend"]["usd"] == pytest.approx(
            round(client_a.calls * CALL_COST, 6))
        assert rj["spend"]["calls"] == client_a.calls


def test_batch_mode_matches_serial_translate_on_the_same_fakes(tmp_path):
    """The whole 5-clause corpus as one batch job (min_pending=2 < 5), the
    failed clause's repair running through the ready queue again. Ledger
    rows arrive at collection via the same client._log_usage."""
    code_a, dir_a, client_a = _run_serial(tmp_path)
    ft = FakeBatchTransport(_scripts())
    code_b, dir_b, client_b = _run_exec(
        tmp_path, {"mode": "batch", "batch_min_pending": 2, "poll_s": 0},
        "batch", transport=ft)
    assert code_a == code_b == 0
    _assert_equivalent(dir_a, dir_b)
    assert client_a.calls == client_b.calls
    assert client_a.spent_usd == pytest.approx(client_b.spent_usd)
    # no submitted-but-uncollected job left behind
    inflight = os.path.join(dir_b, "inflight")
    assert not [f for f in os.listdir(inflight) if f.endswith(".json")]


# ==========================================================================
#  (b) mixed-round batching: attempt-1 and round-k share one flush
# ==========================================================================

def test_attempt1_and_round2_flush_as_one_batch_and_both_resolve(tmp_path):
    """BATCH_DESIGN.md's ruling made concrete: the ready queue holds clause
    A's attempt-1 request and clause B's round-2 (first-repair) transcript;
    one flush, one job, both resolve. Per-clause repair transcripts are
    self-contained, so nothing about correctness depends on what shared the
    batch."""
    scripts = {"m0001": [good("m0001")],
               "m0002": ["still not JSON", good("m0002")]}
    cfg = _cfg(tmp_path, "mixed",
               execution={"mode": "batch", "batch_min_pending": 2,
                          "poll_s": 0})
    holder = {}

    def factory(prov, c):
        holder["c"] = MockClient(prov, c, scripts)
        return holder["c"]

    ctx = TE.prepare(cfg, _args(clause=["m0001", "m0002"], live=True),
                     client_factory=factory)
    states = [TE.ClauseState(ctx, i, j) for i, j in enumerate(ctx.jobs)]
    a, b = states

    # advance B through its (failed) first attempt so its round-2 repair
    # transcript is what sits in the queue
    req = b.next_request()
    assert [m["role"] for m in req] == ["user"]
    b.feed({"text": "still not JSON", "in": 1000, "out": 500,
            "cost_usd": CALL_COST})
    assert b.status == dc.PENDING and b.repair_round == 1
    req2 = b.next_request()
    assert [m["role"] for m in req2] == ["user", "assistant", "user"]

    ft = FakeBatchTransport(scripts)
    sched = TE.FlatScheduler(ctx, states)
    driver = TE._Driver(ctx.cfg, ctx.client, ctx.system, ctx.outdir)
    ex = TE.build_executor("batch", driver,
                           {"batch_min_pending": 2, "poll_s": 0},
                           transport=ft)
    ex.run(sched)

    # ONE batch job, holding A's attempt-1 AND B's round-2 repair
    assert len(ft.uploaded_payloads) == 1, \
        f"expected one flush, got {len(ft.uploaded_payloads)}"
    cids = [json.loads(ln)["custom_id"]
            for ln in ft.uploaded_payloads[0].strip().splitlines()]
    assert sorted(cids) == ["T_m0001-r0", "T_m0002-r1"]

    rows = _rows(ctx.outdir)
    assert rows["m0001"]["status"] == "translated"
    assert rows["m0001"]["attempts"] == 1
    assert rows["m0002"]["status"] == "translated"
    assert rows["m0002"]["attempts"] == 2
    for cid in ("m0001", "m0002"):
        assert os.path.exists(os.path.join(ctx.outdir, cid + ".json"))


# ==========================================================================
#  (c) the graveyard cap fires before any executor work
# ==========================================================================

def test_graveyard_cap_fires_before_any_executor_work(tmp_path):
    cfg = _cfg(tmp_path, "capped",
               execution={"mode": "concurrent", "concurrent_n": 3})
    cfg["graveyard"]["cap"] = 1
    # one OPEN entry (a directory with no VERDICT.md) puts the pile at cap
    os.makedirs(os.path.join(cfg["graveyard"]["dir"], "m9999-20260101-000000"))
    holder = {}

    def factory(prov, c):
        holder["c"] = MockClient(prov, c, _scripts())
        return holder["c"]

    with pytest.raises(gy.GraveyardError, match="graveyard cap reached"):
        TE.run_exec(cfg, _args(clause=list(CIDS), live=True),
                    client_factory=factory)
    # the client existed but was never called: zero spend, zero ledger rows
    assert holder["c"].calls == 0
    assert holder["c"].spent_usd == 0.0
    # and no clause ever started: no raw response anywhere in the run dir
    rundir = _rundir(cfg)
    assert not [f for f in os.listdir(rundir) if f.endswith(".raw.txt")]


# ==========================================================================
#  (d) review F1/F2/F3 pins — the error-path fixes stay fixed
# ==========================================================================

class RaisingClient(MockClient):
    """A MockClient whose script entries may be exceptions: those are RAISED
    from the serve call (the equivalence fakes never raised — review F5
    attack-4 blind spot)."""

    def _serve(self, cid, idx):
        seq = self.scripts[cid]
        item = seq[min(idx, len(seq) - 1)]
        if isinstance(item, Exception):
            raise item
        return super()._serve(cid, idx)


def _run_pair_with_raising(tmp_path, scripts_fn):
    """Serial and concurrent runs on the same raising script; returns the two
    run.json row dicts and the two exit codes."""
    cfg_a = _cfg(tmp_path, "serial_err")
    cfg_b = _cfg(tmp_path, "conc_err",
                 execution={"mode": "concurrent", "concurrent_n": 3})
    dirs, codes = [], []
    for cfg, runner in ((cfg_a, T.run), (cfg_b, TE.run_exec)):
        def factory(prov, c):
            return RaisingClient(prov, c, scripts_fn())
        codes.append(runner(cfg, _args(clause=list(CIDS), live=True),
                            client_factory=factory))
        dirs.append(_rundir(cfg))
    return codes, [_rows(d) for d in dirs]


def test_provider_error_on_attempt_1_writes_the_serial_error_row(tmp_path):
    """Review F2: exec mode wrote 'ProviderError: ProviderError: ...' where
    serial wrote 'ProviderError: ...'. Pin exec == serial, byte for byte."""
    def scripts():
        s = {cid: [good(cid)] for cid in CIDS}
        s["m0003"] = [T.ProviderError("HTTP 402: Credit limit exceeded")]
        return s

    codes, (ra, rb) = _run_pair_with_raising(tmp_path, scripts)
    assert codes[0] == codes[1]
    assert ra["m0003"]["status"] == "error"
    assert ra["m0003"]["error"] == \
        "ProviderError: HTTP 402: Credit limit exceeded"
    for cid in CIDS:
        a, b = dict(ra[cid]), dict(rb[cid])
        a.pop("graveyard", None), b.pop("graveyard", None)
        assert a == b, f"run.json row for {cid} differs: {a} != {b}"


def test_provider_error_mid_repair_writes_the_serial_error_row(tmp_path):
    """Review F2, mid-repair variant (probe P4): the failure arrives on the
    repair round's request, a path no prior test exercised."""
    def scripts():
        s = {cid: [good(cid)] for cid in CIDS}
        s["m0003"] = ["still not JSON",
                      T.ProviderError("HTTP 402: Credit limit exceeded")]
        return s

    codes, (ra, rb) = _run_pair_with_raising(tmp_path, scripts)
    assert codes[0] == codes[1]
    assert ra["m0003"]["status"] == "error"
    assert "ProviderError: HTTP 402" in ra["m0003"]["error"]
    assert "ProviderError: ProviderError" not in rb["m0003"]["error"]
    for cid in CIDS:
        a, b = dict(ra[cid]), dict(rb[cid])
        a.pop("graveyard", None), b.pop("graveyard", None)
        assert a == b, f"run.json row for {cid} differs: {a} != {b}"


def test_non_phase1_abort_still_unparks_the_clause_thread(tmp_path):
    """Review F3: a non-Phase1Error escaping run_one aborts the run (the
    accepted divergence) but must not leave the failing clause's body thread
    parked forever on _resp_ready.wait()."""
    import time

    def scripts():
        s = {cid: [good(cid)] for cid in CIDS}
        s["m0003"] = [RuntimeError("raw transport bug")]
        return s

    cfg = _cfg(tmp_path, "abort",
               execution={"mode": "concurrent", "concurrent_n": 3})

    def factory(prov, c):
        return RaisingClient(prov, c, scripts())

    before = set(threading.enumerate())
    with pytest.raises(RuntimeError, match="raw transport bug"):
        TE.run_exec(cfg, _args(clause=list(CIDS), live=True),
                    client_factory=factory)
    # run.json was flushed by execute()'s finally
    assert os.path.exists(os.path.join(_rundir(cfg), "run.json"))
    # every thread the run started terminates: nothing stays parked
    deadline = time.time() + 10
    while time.time() < deadline:
        leaked = [t for t in threading.enumerate()
                  if t not in before and t.is_alive()]
        if not leaked:
            break
        time.sleep(0.05)
    assert not leaked, f"leaked parked thread(s): {leaked}"


def test_batch_mode_refuses_a_nonempty_inflight_manifest(tmp_path):
    """Review F1 (honest refusal): every ClauseState shares one recovery
    identity, so a swept orphan could be fed to the WRONG clause. The batch
    executor must refuse to start over a non-empty in-flight manifest."""
    cfg = _cfg(tmp_path, "zombie")
    out = str(tmp_path / "zombie_out")
    os.makedirs(out)
    dc.InFlightManifest(out).record(
        "job-000000", {"batch_id": "b-dead", "items": []})
    driver = TE._Driver(cfg, None, "system prompt", out)
    with pytest.raises(T.Phase1Error, match="kill-recovery is unsupported"):
        TE._TranslateBatch(driver, {"batch_min_pending": 2, "poll_s": 0})


# ==========================================================================
#  dry run spends nothing and builds nothing
# ==========================================================================

def test_dry_run_sends_nothing(tmp_path, capsys):
    cfg = _cfg(tmp_path, "dry",
               execution={"mode": "concurrent", "concurrent_n": 3})
    holder = {}

    def factory(prov, c):                       # pragma: no cover — must
        holder["c"] = MockClient(prov, c, _scripts())   # never be reached
        return holder["c"]

    code = TE.run_exec(cfg, _args(clause=list(CIDS), live=False),
                       client_factory=factory)
    assert code == 0
    assert "DRY RUN" in capsys.readouterr().out
    assert not holder, "dry run built a client"
    assert not os.path.isdir(_rundir(cfg))
