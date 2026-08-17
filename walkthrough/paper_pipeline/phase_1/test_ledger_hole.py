"""THE LEDGER HOLE and TRUNCATION-AS-AN-OUTCOME (fixed 2026-08-16).

Two defects, both MEASURED on live arms, both observability-only:

  1. A provider call that RAISES has already spent. `Client._log_usage` runs
     BEFORE `_check_envelope` precisely because a truncated completion is
     billed exactly like a good one — but every caller wrote its turn record
     only on the success path, so a billed raise left no record. Measured three
     times: 36% of arm D's spend; $0.01612 of arm E's $0.08335; $0.09066 of arm
     F's $0.15999 — 57% of that arm's spend bought nothing, across 21
     billed-then-raised truncations. The under-report is CORRELATED with the
     outcome: the calls that raise are the long reasoners, i.e. the hard
     clauses, so the arm that looked cheapest was losing the most.

  2. Truncation was invisible. Arm F lost 10 of 17 and 11 of 17 critic calls to
     the cap and delivered 5 and 6 modules; the three clauses where the
     measured harm was worst truncated in BOTH cells — the most informative
     cells are exactly the missing ones.

WHAT IS ASSERTED HERE: a billed raise carries its envelope out (`exc.billed`),
`translate.billed_record` turns it into a complete record, unknown spend is
reported as UNKNOWN and never as zero, the run tag makes a ledger row
attributable without a timestamp join, and the historical holes in arms E and F
are reconstructible from the artifacts still on disk.

⛔ WHAT IS DELIBERATELY NOT ASSERTED: that anything retries, or that any cap
changes. An arm's `max_tokens` is a pre-registered variable; the harness's job
is to make the loss visible and countable and let the caller decide.

Everything here is offline: no network, no key, no spend.
"""
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "_debug_gen11" / "ds_opus_loop"))

import translate as T                                          # noqa: E402

GEN11 = HERE / "_debug_gen11"
LEDGER = (HERE / ".." / ".." / ".." / "semi-formal-experiment"
          / "usage.jsonl").resolve()
DS_MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
MIN_PROMPT_TOKENS = 9000


# ==========================================================================
#  helpers — a real translate.Client with a fake key and no network
# ==========================================================================

def _prov(**over):
    kw = dict(name="test", kind="openai-compatible", model="m",
              base_url="https://example.invalid", api_key_env="FAKE_KEY_ENV",
              temperature=0.0, max_tokens=100, price_per_mtok=[1.0, 2.0])
    kw.update(over)
    return T.Provider(**kw)


def _client(monkeypatch):
    monkeypatch.setenv("FAKE_KEY_ENV", "not-a-real-key")
    # usage_log falsy => `_log_usage` writes to NO ledger. A test that appends
    # to the real usage.jsonl would corrupt the spend record it is defending.
    return T.Client(_prov(), {"model": {"usage_log": ""}})


def _payload(text, finish, prompt=1000, completion=100):
    return {"choices": [{"message": {"content": text},
                         "finish_reason": finish}],
            "usage": {"prompt_tokens": prompt, "completion_tokens": completion}}


def _wire(monkeypatch, payload):
    """Make the next `_send` return `payload` without touching the network."""
    import urllib.request

    class _Resp:
        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **k: _Resp())


@pytest.fixture(autouse=True)
def _no_run_tag_leak():
    """The run tag is process state; a test that sets it must not colour the
    next test's rows."""
    before = T._RUN_TAG
    yield
    T._RUN_TAG = before


# ==========================================================================
#  1 — a call that spends and then raises hands its envelope to the caller
# ==========================================================================

def test_a_truncated_call_carries_its_billed_envelope_out(monkeypatch):
    """⛔ THE HOLE ITSELF. Before the fix the exception carried a message and
    nothing else, so the caller had no cost to write and wrote none."""
    c = _client(monkeypatch)
    _wire(monkeypatch, _payload("half a mod", "length", completion=100))
    with pytest.raises(T.ProviderError) as ei:
        c.complete_messages("sys", [{"role": "user", "content": "u"}])
    full = T.billed_envelope(ei.value)
    assert full is not None, "the money is spent; the envelope must come out"
    assert full["usage"]["cost_usd"] > 0
    assert full["truncated"] is True
    assert full["requested_max_tokens"] == 100
    assert full["usage"]["completion_tokens"] == 100
    # and the client keeps it too, for a caller that no longer holds the exc
    assert c.last_billed is full


def test_the_raise_names_the_token_count_at_cut(monkeypatch):
    c = _client(monkeypatch)
    _wire(monkeypatch, _payload("half", "length", completion=100))
    with pytest.raises(T.ProviderError, match="TRUNCATED") as ei:
        c.complete_messages("sys", [{"role": "user", "content": "u"}])
    assert "cut at 100 completion tokens" in str(ei.value)
    assert "cap of 100" in str(ei.value)


def test_the_finish_reason_null_cut_is_also_billed_and_flagged(monkeypatch):
    """together.ai returns finish_reason null on this model — the documented
    caveat. The at-cap backstop must still produce a BILLED, truncated
    record, or the exact case that ate arm F stays invisible."""
    c = _client(monkeypatch)
    _wire(monkeypatch, _payload("half", None, completion=100))
    with pytest.raises(T.ProviderError, match="TRUNCATED") as ei:
        c.complete_messages("sys", [{"role": "user", "content": "u"}])
    rec = T.billed_record(ei.value)
    assert rec["billed"] is True
    assert rec["truncated"] is True
    assert rec["completion_tokens_at_cut"] == 100
    assert rec["cost_usd"] > 0


def test_an_empty_reply_is_billed_too(monkeypatch):
    """Not every billed raise is a truncation. An empty completion is billed
    for its prompt and must land in the ledger the same way."""
    c = _client(monkeypatch)
    _wire(monkeypatch, _payload("   ", "stop", completion=3))
    with pytest.raises(T.ProviderError, match="empty") as ei:
        c.complete_messages("sys", [{"role": "user", "content": "u"}])
    rec = T.billed_record(ei.value)
    assert rec["billed"] is True and rec["cost_usd"] > 0
    assert rec["truncated"] is False


def test_a_transport_failure_reports_UNKNOWN_spend_never_zero(monkeypatch):
    """⚠️ THE ANTI-FLATTERING RULE. No envelope came back, so there are no
    token counts. `cost_usd` is None — a caller totalling money must not be
    able to read this as a free call."""
    c = _client(monkeypatch)
    import urllib.request

    def _boom(*a, **k):
        raise OSError("connection reset")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(T.ProviderError) as ei:
        c.complete_messages("sys", [{"role": "user", "content": "u"}])
    assert T.billed_envelope(ei.value) is None
    rec = T.billed_record(ei.value)
    assert rec["billed"] is False
    assert rec["cost_usd"] is None, "unknown spend is not zero spend"
    assert rec["truncated"] is None


def test_a_clean_call_is_unaffected(monkeypatch):
    """The fix is observability-only: a call that succeeds returns exactly
    what it returned before."""
    c = _client(monkeypatch)
    _wire(monkeypatch, _payload("{}", "stop", completion=10))
    env = c.complete_messages("sys", [{"role": "user", "content": "u"}])
    assert env["text"] == "{}" and env["cost_usd"] > 0
    assert set(env) == {"text", "in", "out", "cost_usd"}


# ==========================================================================
#  2 — the run tag: attribution without a timestamp join
# ==========================================================================

def test_priced_by_is_unchanged_when_no_run_tag_is_set():
    """5,012 rows already carry the bare string. An unconditional suffix would
    make every historical row look like it came from a tagged run."""
    T.set_run_tag(None)
    env = T.response_envelope(_prov(), _payload("x", "stop"))
    assert env["usage"]["priced_by"] == T.PRICED_BY
    assert T.run_tag_of(env["usage"]) is None


def test_a_run_tag_reaches_the_ledger_row_and_comes_back_out():
    T.set_run_tag("armF/f2")
    env = T.response_envelope(_prov(), _payload("x", "stop"))
    assert env["usage"]["priced_by"] == f"{T.PRICED_BY}#run=armF/f2"
    assert T.run_tag_of(env["usage"]) == "armF/f2"
    assert T.billed_record(_exc_with(env))["run_tag"] == "armF/f2"


def test_a_truncated_row_is_tagged_too():
    """The rows that MOST need attribution are the ones that raised: they are
    the ones an arm's own records used to miss."""
    T.set_run_tag("armE")
    env = T.response_envelope(_prov(), _payload("x", "length", completion=100))
    assert T.run_tag_of(env["usage"]) == "armE"
    assert env["truncated"] is True


def _exc_with(envelope):
    exc = T.ProviderError("boom")
    exc.billed = envelope
    return exc


# ==========================================================================
#  3 — loop.py: the record is written BEFORE the raise propagates
# ==========================================================================

def _loop():
    # The arm harness under test left the working tree when the critic-loop
    # series was parked (2026-08-16); it lives in full at commit 06e2050
    # (_debug_gen11/ds_opus_loop/loop.py). These tests skip rather than
    # delete so a resurrection of the arm brings its ledger contract back
    # with it — mirroring section 4, which already skips on absent artifacts.
    try:
        import loop
    except ModuleNotFoundError:
        pytest.skip("ds_opus_loop/loop.py parked at 06e2050 — not on disk")
    return loop


def test_loop_writes_a_billed_failure_record_before_the_raise(tmp_path,
                                                              monkeypatch):
    loop = _loop()
    monkeypatch.setattr(loop, "OUT", str(tmp_path))
    monkeypatch.setattr(loop, "CLAUSES", ["c1"])
    st = loop.load_state("c1")
    env = T.response_envelope(_prov(), _payload("half", "length",
                                                completion=100))
    env["requested_max_tokens"] = 100
    loop.record_billed_failure(st, _exc_with(env), turn=1)

    on_disk = loop.load_state("c1")
    assert on_disk["turns"] == [], (
        "a failed turn produced no assistant message: putting it in `turns` "
        "would renumber the transcript and refuse the re-send of turn 1")
    assert len(on_disk["billed_failures"]) == 1
    fail = on_disk["billed_failures"][0]
    assert fail["truncated"] is True and fail["completion_tokens_at_cut"] == 100
    assert loop.ledger_spent() == pytest.approx(env["usage"]["cost_usd"])


def test_loop_ledger_spent_used_to_miss_this_money(tmp_path, monkeypatch):
    """The regression in one line: the OLD total read `turns` alone."""
    loop = _loop()
    monkeypatch.setattr(loop, "OUT", str(tmp_path))
    monkeypatch.setattr(loop, "CLAUSES", ["c1"])
    st = loop.load_state("c1")
    st["turns"].append({"n": 1, "cost_usd": 0.01})
    env = T.response_envelope(_prov(), _payload("half", "length",
                                                completion=100))
    env["requested_max_tokens"] = 100
    loop.record_billed_failure(st, _exc_with(env), turn=2)

    old_way = sum(float(t.get("cost_usd") or 0.0)
                  for t in loop.load_state("c1")["turns"])
    assert old_way == pytest.approx(0.01)
    assert loop.ledger_spent() > old_way, "the hole"
    assert loop.ledger_spent() == pytest.approx(
        0.01 + env["usage"]["cost_usd"])


def test_the_summary_says_the_truncation_out_loud(tmp_path, monkeypatch):
    loop = _loop()
    monkeypatch.setattr(loop, "OUT", str(tmp_path))
    monkeypatch.setattr(loop, "CLAUSES", ["c1"])
    st = loop.load_state("c1")
    st["turns"].append({"n": 1, "cost_usd": 0.01})
    env = T.response_envelope(_prov(), _payload("half", "length",
                                                completion=100))
    env["requested_max_tokens"] = 100
    loop.record_billed_failure(st, _exc_with(env), turn=2)

    out = loop.truncation_summary()
    assert "TRUNCATED AT THE CAP 1" in out
    assert "100 completion tokens" in out
    assert "cap 100" in out
    assert "NOT retried" in out, (
        "the ruling against a silent retry / a silently raised cap is part of "
        "what the summary has to say")


def test_an_unpriced_failure_is_counted_but_not_totalled(tmp_path,
                                                         monkeypatch):
    loop = _loop()
    monkeypatch.setattr(loop, "OUT", str(tmp_path))
    monkeypatch.setattr(loop, "CLAUSES", ["c1"])
    st = loop.load_state("c1")
    loop.record_billed_failure(st, T.ProviderError("connection reset"), turn=1)
    assert len(loop.unpriced_calls()) == 1
    assert loop.ledger_spent() == 0.0
    assert "spend UNKNOWN, not zero" in loop.truncation_summary()


def test_a_prefix_record_is_still_counted_as_a_cut_and_flagged_as_a_floor():
    """The arms already on disk were written by the OLD code: no `truncated`
    field, no cost, only the error string. The summary must still SHOW those
    21 cuts — and must say out loud that the dollar share it prints for them
    is a floor, not the loss."""
    loop = _loop()
    legacy = [{"phase": "critic", "cost_usd": 0.0,
               "error": "ProviderError('completion was TRUNCATED ...')"},
              {"phase": "repair", "cost_usd": 0.01}]
    out = loop.summarize_truncation(legacy, "armF/f1")
    assert "TRUNCATED AT THE CAP 1" in out
    assert "PREDATE the fix" in out and "FLOOR" in out


# ==========================================================================
#  4 — ⭐ THE RECONCILIATION. The historical holes, replayed against the
#      artifacts still on disk. Nothing here pins a count of a live
#      artifact: the ledger window is read from each arm's own frozen
#      `_ledger_start.json`, and every assertion is a RELATION between the
#      arm's records and the ledger, not a constant.
# ==========================================================================

def _start_lines():
    """Every arm's frozen ledger start line, in order."""
    import glob
    out = []
    for p in glob.glob(str(GEN11 / "**" / "_ledger_start.json"),
                       recursive=True):
        try:
            out.append(json.load(open(p))["first_new_line"])
        except Exception:                                     # noqa: BLE001
            continue
    return sorted(set(out))


def _ledger_window(start, end):
    with open(LEDGER, encoding="utf-8") as fh:
        return [json.loads(ln) for i, ln in enumerate(fh, 1)
                if start <= i < end and ln.strip()]


def _arm(records_glob, start_file):
    """⚠️ THIS FUNCTION IS THE ARGUMENT FOR THE RUN TAG.

    An arm's rows can only be found by (a) its frozen start line, (b) the NEXT
    arm's start line as an upper bound, and (c) a prompt-size heuristic. Arm
    E's own `reconcile.py` had no upper bound and was right only because no
    later arm existed when it ran; the same script run today sweeps up all 21
    of arm F's truncations. `translate.set_run_tag` removes every step of this:
    a tagged row says which arm bought it.
    """
    import glob
    if not LEDGER.exists() or not os.path.exists(start_file):
        pytest.skip("arm artifacts not on disk")
    start = json.load(open(start_file))["first_new_line"]
    later = [s for s in _start_lines() if s > start]
    end = min(later) if later else 1 << 60
    rows = [r for r in _ledger_window(start, end)
            if r.get("model") == DS_MODEL
            and (r.get("prompt_tokens") or 0) >= MIN_PROMPT_TOKENS]
    calls = [c for p in glob.glob(records_glob)
             for c in json.load(open(p, encoding="utf-8"))["calls"]]
    if not calls or not rows:
        pytest.skip("arm artifacts not on disk")
    return rows, calls


def _replay(rows, calls):
    """What the FIXED code would have written for this arm.

    The raised calls on disk are the billed-then-raised ones; the truncated
    ledger rows are the envelopes they were billed for. Pair them and run the
    real `translate.billed_record` over the pairing — this is the fix applied
    to the historical events, not a re-derivation of them.
    """
    raised = [c for c in calls if c.get("error")]
    cut_rows = [r for r in rows if r.get("truncated")]
    assert len(raised) == len(cut_rows), (
        "every raise in these arms was a cap cut, and every cap cut raised")
    out = []
    for row in cut_rows:
        env = {"text": "", "finish_reason": row.get("finish_reason"),
               "truncated": bool(row.get("truncated")),
               "requested_max_tokens": row.get("completion_tokens"),
               "usage": {k: v for k, v in row.items()
                         if k not in ("provider", "model", "ts",
                                      "finish_reason", "truncated")}}
        out.append(T.billed_record(_exc_with(env)))
    return raised, out


@pytest.mark.parametrize("arm,glob_pat,start", [
    ("E", "ds_critic_arm/out/*.arme.json", "ds_critic_arm/out/_ledger_start.json"),
    ("F", "ds_critic_format_arm/out_*/*.armf.json",
     "ds_critic_format_arm/_ledger_start.json"),
])
def test_the_historical_hole_is_exactly_what_the_fix_now_records(arm, glob_pat,
                                                                 start):
    """⭐ THE PIN. recorded(old) + replayed(billed failures) == the ledger.

    Arm E: $0.06723 recorded + $0.01612 lost = $0.08335 billed.
    Arm F: $0.06933 recorded + $0.09066 lost = $0.15999 billed — 57%.
    The numbers are in the docstring for the reader; the ASSERTION is the
    identity, so a future arm with different traffic still passes.
    """
    rows, calls = _arm(str(GEN11 / glob_pat), str(GEN11 / start))
    raised, replayed = _replay(rows, calls)

    billed = sum(float(r.get("cost_usd") or 0.0) for r in rows)
    recorded_old = sum(float(c.get("cost_usd") or 0.0) for c in calls)
    recovered = sum(float(r["cost_usd"]) for r in replayed)

    assert recovered > 0, "there was a hole"
    assert recorded_old + recovered == pytest.approx(billed, abs=1e-9), (
        f"arm {arm}: the fix must close the hole exactly, not approximately")
    assert all(r["billed"] and r["truncated"] for r in replayed)
    assert all(r["completion_tokens_at_cut"] == r["requested_max_tokens"]
               for r in replayed), "a cap cut sits ON the cap"
    assert len(replayed) == len(raised)


def test_the_arms_currently_on_disk_are_the_uncorrected_ones():
    """⚠️ A GUARD ON THE PIN ABOVE, not on the arms. Those records were written
    by the OLD code, so `cost_usd` is 0.0 on every raise. If a re-run ever
    rewrites them with the fix in place, the identity above becomes
    `billed + billed == billed` and would fail loudly rather than silently
    reconcile — this test says which world we are in.
    """
    import glob
    ps = glob.glob(str(GEN11 / "ds_critic_format_arm/out_*/*.armf.json"))
    if not ps:
        pytest.skip("arm F artifacts not on disk")
    raised = [c for p in ps
              for c in json.load(open(p, encoding="utf-8"))["calls"]
              if c.get("error")]
    assert raised, "arm F truncated 21 of its 34 critic calls"
    old_shape = [c for c in raised if float(c.get("cost_usd") or 0.0) == 0.0]
    new_shape = [c for c in raised if c.get("billed") is not None]
    assert bool(old_shape) != bool(new_shape), (
        "records are either all pre-fix or all post-fix; a mix means an arm "
        "was half re-run and its spend figure is not a measurement of "
        "anything")
