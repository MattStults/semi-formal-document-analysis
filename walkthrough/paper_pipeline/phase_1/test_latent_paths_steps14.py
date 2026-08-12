"""Latent code-path audit, steps 1-4 (2026-08-12): tests for FAILURE-HANDLING
branches no prior test executed — repair exhaustion on non-JSON, truncation
guards and resampling, per-clause provider-error rows, cost-gate refusals,
xclingo transport failures, seat prompt refusals — plus PINS of two genuine
bugs found by the audit. Bug pins assert the CURRENT (wrong) behavior on
purpose, so the fix will flip a named test rather than land silently.

  BUG 1 (translate.py:729-730 vs translate.py:776-781): `response_envelope`
  flags finish_reason "max_output_tokens" as truncated, but `_check_envelope`
  raises only on ("length", "max_tokens"). The same reply is refused by the
  batch collector (`dispatch_core._classify` trusts the envelope flag) and
  ACCEPTED as complete by the serial/live guard — two validators, one datum,
  opposite verdicts. A cut-off reply then surfaces one stage later as a JSON
  parse error blamed on "the provider ignored response_format".

  BUG 2 (dispatch_core.py:463-464): "HTTP 402" is in `_TRANSIENT_MARKS`, so a
  payment-required / credit-limit-exceeded error — a condition retries cannot
  cure — is retried 6 times with 30+60+90+120+150+180 = 630s of sleeps per
  dispatch, per worker. This is also why test_translate_exec.py's two F2 pin
  tests (which raise "HTTP 402: Credit limit exceeded" and expect a fast
  per-clause error row) now hang ~10.5 minutes each instead of finishing in
  seconds — the ladder change was never reconciled with the pins.

Everything here is offline: no network, no key, no spend.
"""
import copy
import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
GRAPH_V2 = HERE / "resolve_runs" / "graph_v2"
sys.path.insert(0, str(GRAPH_V2))

import fixtures                      # noqa: E402
import translate as T                # noqa: E402
import readback_r3 as R3             # noqa: E402
import seats                         # noqa: E402

module_json = fixtures.module_json


def _prov(**over):
    kw = dict(name="test", kind="openai-compatible", model="m",
              base_url="https://example.invalid", api_key_env="FAKE_KEY_ENV",
              temperature=0.0, max_tokens=100,
              price_per_mtok=[1.0, 2.0])
    kw.update(over)
    return T.Provider(**kw)


def _client(monkeypatch, cfg_model=None):
    """A real translate.Client with a fake key and no network."""
    monkeypatch.setenv("FAKE_KEY_ENV", "not-a-real-key")
    cfg = {"model": dict(cfg_model or {})}
    return T.Client(_prov(), cfg)


# ==========================================================================
#  1.  the truncation / emptiness guards (translate._check_envelope)
# ==========================================================================

def test_check_envelope_refuses_finish_reason_length():
    env = {"text": "half a module", "finish_reason": "length", "usage": {}}
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        T._check_envelope(env)


def test_check_envelope_refuses_an_empty_or_whitespace_reply():
    for text in (None, "", "   \n\t"):
        with pytest.raises(T.ProviderError, match="empty response"):
            T._check_envelope({"text": text, "finish_reason": "stop",
                               "usage": {}})


def test_check_envelope_passes_the_documented_null_finish_reason():
    """The recorded caveat: together returns finish_reason null, so the guard
    cannot fire there — the reply passes and truncation surfaces later as a
    parse error. Pinned so the caveat stays recorded in the suite, not only
    in --self-test (which pytest never runs)."""
    out = T._check_envelope({"text": "x", "finish_reason": None,
                             "usage": {"prompt_tokens": 3,
                                       "completion_tokens": 5}})
    assert out == {"text": "x", "in": 3, "out": 5}


def test_max_output_tokens_truncation_agrees_across_both_validators():
    """FIXED (was BUG 1, steps-1-4 audit 2026-08-12): `response_envelope`
    counts finish_reason "max_output_tokens" as truncated and
    `_check_envelope` used to raise only on "length"/"max_tokens" -- the
    SAME reply was truncated to the batch collector and complete to the
    serial/live guard. The guard now trusts the envelope's own `truncated`
    flag (authority when present), so the two can never disagree again."""
    data = {"choices": [{"message": {"content": "cut off mid-"},
                         "finish_reason": "max_output_tokens"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 100}}
    env = T.response_envelope(_prov(), data)
    assert env["truncated"] is True          # the envelope calls it truncated
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        T._check_envelope(env)               # ... and now so does the guard

    # the batch collector, reading the same envelope shape, refuses it:
    import dispatch_core as dc

    class _Drv:
        cfg, client, brief, out = {}, object(), "", ""
    bx = object.__new__(dc.BatchExecutor)   # no transport, no manifest needed
    bx.prov = _prov()
    bx._req_max = {}
    kind, _ = bx._classify({"custom_id": "x", "response": {"body": data}})
    assert kind == "truncated", (
        "batch and live now agree — delete the BUG pin above and make "
        "_check_envelope refuse max_output_tokens explicitly")


# ==========================================================================
#  2.  truncation resampling (Client._retrying) — and its repair-round hole
# ==========================================================================

def _wire_send(client, script):
    """Replace the HTTP hop: each entry is an envelope dict or an exception."""
    calls = []

    def fake_send(body):
        calls.append(body)
        item = script[min(len(calls) - 1, len(script) - 1)]
        if isinstance(item, Exception):
            raise item
        return item
    client._send = fake_send
    return calls


def test_resample_truncation_redraws_the_same_request(monkeypatch):
    trunc = T.ProviderError("completion was TRUNCATED (finish_reason=length)")
    client = _client(monkeypatch, {"resample_truncation": 2})
    good = {"text": "ok", "in": 1, "out": 1}
    calls = _wire_send(client, [trunc, trunc, good])
    assert client.complete("sys", "user") == good
    assert len(calls) == 3
    # every draw is the SAME request — a resample, not a mutation
    assert calls[0] == calls[1] == calls[2]


def test_resample_truncation_defaults_to_raising_immediately(monkeypatch):
    trunc = T.ProviderError("completion was TRUNCATED (finish_reason=length)")
    client = _client(monkeypatch, {})
    calls = _wire_send(client, [trunc])
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        client.complete("sys", "user")
    assert len(calls) == 1


def test_resample_never_retries_a_non_truncation_error(monkeypatch):
    client = _client(monkeypatch, {"resample_truncation": 5})
    calls = _wire_send(client, [T.ProviderError("HTTP 500: boom")])
    with pytest.raises(T.ProviderError, match="HTTP 500"):
        client.complete("sys", "user")
    assert len(calls) == 1


def test_GAP_repair_rounds_are_never_resampled_even_when_asked(monkeypatch):
    """Recorded gap, pinned: `_retrying` wraps `complete` only
    (translate.py:581-585). A repair-round draw goes through
    `complete_messages`, so a truncated REPAIR reply raises immediately and
    fails the clause even with `model.resample_truncation` set. (The exec
    adapter documents the concurrent-mode version of this as R9.1; the serial
    version is documented nowhere but here.)"""
    trunc = T.ProviderError("completion was TRUNCATED (finish_reason=length)")
    client = _client(monkeypatch, {"resample_truncation": 5})
    calls = _wire_send(client, [trunc, {"text": "never reached"}])
    with pytest.raises(T.ProviderError, match="TRUNCATED"):
        client.complete_messages("sys", [{"role": "user", "content": "u"}])
    assert len(calls) == 1, "a resample here means the gap closed: undocument it"


# ==========================================================================
#  3.  parse_module — the misleading-cause fallback, and the fences
# ==========================================================================

def test_parse_module_refusal_blames_format_forcing_whatever_the_cause():
    """The fallback MESSAGE misdescribes one real cause by design: a length-
    truncated reply (finish_reason null, see the guard caveat) also lands
    here, and the text leads with 'the provider ignored response_format'.
    The message at least names the truncation possibility — pin that both
    halves stay present."""
    with pytest.raises(T.ResponseParseError) as exc:
        T.parse_module("{ this is not json", clause_id="m0001",
                       known_clause_ids={"m0001"})
    msg = str(exc.value)
    assert "ignored response_format" in msg
    assert "cut off" in msg


def test_parse_module_tolerates_json_and_bare_fences():
    raw = module_json(clause_id="m0001")
    for fenced in (f"```json\n{raw}```", f"```\n{raw}```"):
        mod = T.parse_module(fenced, clause_id="m0001",
                             known_clause_ids={"m0001"})
        assert mod.clause_id == "m0001"


def test_parse_module_wraps_schema_refusals_as_parse_errors():
    with pytest.raises(T.ResponseParseError):
        T.parse_module(json.dumps({"clause_id": "m0001"}),
                       clause_id="m0001", known_clause_ids={"m0001"})


# ==========================================================================
#  4.  resolve_outdir — a paid run's directory is never overwritten
# ==========================================================================

def test_resolve_outdir_refuses_a_nonempty_named_run_dir(tmp_path):
    cfg = {"output": {"dir": str(tmp_path), "run_name": "r1"}}
    os.makedirs(tmp_path / "r1")
    (tmp_path / "r1" / "m0001.raw.txt").write_text("paid for")
    with pytest.raises(T.ConfigError, match="already holds"):
        T.resolve_outdir(cfg, _prov())


def test_resolve_outdir_accepts_an_empty_named_run_dir(tmp_path):
    cfg = {"output": {"dir": str(tmp_path), "run_name": "r1"}}
    os.makedirs(tmp_path / "r1")
    assert T.resolve_outdir(cfg, _prov()) == str(tmp_path / "r1")


def test_resolve_outdir_increments_a_colliding_timestamp_dir(tmp_path,
                                                             monkeypatch):
    import time as _time
    monkeypatch.setattr(_time, "strftime", lambda fmt: "20260101-000000")
    cfg = {"output": {"dir": str(tmp_path), "run_name": None}}
    first = tmp_path / "20260101-000000-test"
    os.makedirs(first)
    (first / "run.json").write_text("{}")
    out = T.resolve_outdir(cfg, _prov())
    assert out == str(tmp_path / "20260101-000000-test-2")


# ==========================================================================
#  5.  cost gates
# ==========================================================================

def test_an_unpriced_provider_counts_as_over_budget():
    with pytest.raises(T.CostGateError, match="no price_per_mtok"):
        T.estimate_cost("sys", ["user"], _prov(price_per_mtok=None),
                        {"cost": {"chars_per_token": 3.5}})


def test_cost_gate_refuses_over_the_ceiling():
    with pytest.raises(T.CostGateError, match="exceeds the ceiling"):
        T.cost_gate(1.0, {"cost": {"max_cost_usd": 0.5}})


def test_repair_log_budget_refuses_a_prompt_too_small_to_absorb_it():
    """With max_attempts > 1, the estimate's surplus must cover the 8,000-char
    error-log budget; a tiny system+user cannot, and the gate must refuse
    rather than print an estimate BELOW the true worst case."""
    with pytest.raises(T.CostGateError, match="repair-turn error log"):
        T.estimate_cost("s", ["u"], _prov(),
                        {"cost": {"chars_per_token": 3.5}}, max_attempts=3)


# ==========================================================================
#  6.  repair exhaustion on never-JSON replies, and the error-log fallbacks
# ==========================================================================

class _Scripted:
    def __init__(self, *texts):
        self.texts, self.n = list(texts), 0

    def complete_messages(self, system, messages):
        t = self.texts[min(self.n, len(self.texts) - 1)]
        self.n += 1
        return {"text": t, "in": 1, "out": 1}


def test_a_clause_whose_every_reply_is_non_json_exhausts_as_unrepaired():
    out = T.repair_loop("not json at all", clause={"id": "m0001"},
                        model=_Scripted("still not json", "nor this"),
                        max_attempts=3)
    assert out.status == "unrepaired"
    assert out.module is None
    assert [f.check_id for f in out.findings] == ["not-json"]
    # the transcript ends with what the model LAST said, not our question
    assert out.transcript[-1]["role"] == "assistant"
    assert out.per_attempt == [1, 1, 1]


def test_error_log_with_only_withheld_findings_still_commands_a_fix():
    """The fallback message misdescribes the situation: when every finding is
    withheld (later-stage origin), the log says 'no error-severity findings —
    nothing here is yours to fix' and then closes with 'Fix every one of
    them.' — an instruction over an empty list. Pinned as-is; a reworded
    closing line should flip this deliberately."""
    f = T.RepairFinding("probe-verdict-x", "error", "claims[0]",
                        "situation s1 derived the wrong status",
                        "probe-verdict")
    log = T.render_error_log([("attempt 1", [f])])
    assert "1 finding(s) withheld" in log
    assert "nothing here is yours to fix" in log
    assert log.strip().endswith("Fix every one of them. "
                                "Return the corrected module, complete.")


def test_shape_and_diff_flags_survive_non_json_and_non_dict_replies():
    assert T._shape("not json") == {}
    assert T._shape(json.dumps([1, 2])) == {}
    assert T._diff_flags({}, {"asserts": 1}) == []
    assert T._diff_flags({"asserts": 1}, {}) == []


# ==========================================================================
#  7.  run(): the per-clause provider-error row (translate.py:1254-1260)
# ==========================================================================

def _run_cfg(tmp_path):
    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": ["m0091"], "section_id": None,
                     "kinds": [], "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": "t"}
    cfg["repair"] = {"max_attempts": 2}
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}
    return cfg


class _Args:
    clause = section = kinds = limit = provider = model = max_tokens = None
    live = True
    show_prompt = 0


def test_a_provider_error_on_attempt_1_is_one_error_row_not_an_abort(
        tmp_path, capsys):
    class _Raises:
        def __init__(self, *a, **k):
            pass

        def complete(self, system, user):
            raise T.ProviderError("HTTP 402: Credit limit exceeded")

    code = T.run(_run_cfg(tmp_path), _Args(), client_factory=_Raises)
    assert code == 1
    rec = json.load(open(tmp_path / "t" / "run.json"))["results"][0]
    assert rec["status"] == "error"
    assert rec["error"] == "ProviderError: HTTP 402: Credit limit exceeded"
    # nothing was paid for, so nothing raw exists — but the user prompt half
    # of the transcript was written BEFORE the call, as documented
    assert not (tmp_path / "t" / "m0091.raw.txt").exists()
    assert (tmp_path / "t" / "m0091.prompt_user.txt").exists()


def test_a_provider_error_mid_repair_is_one_error_row_not_an_abort(tmp_path):
    broken = module_json(asserts=[fixtures.assertion(
        head="looks_professional(D)", body="", licence="direct",
        cites="m9999")])            # cites a clause that does not exist

    class _RaisesOnRepair:
        def __init__(self, *a, **k):
            pass

        def complete(self, system, user):
            return {"text": broken, "in": 1, "out": 1}

        def complete_messages(self, system, messages):
            raise T.ProviderError("HTTP 500: mid-repair drop")

    code = T.run(_run_cfg(tmp_path), _Args(), client_factory=_RaisesOnRepair)
    assert code == 1
    rec = json.load(open(tmp_path / "t" / "run.json"))["results"][0]
    assert rec["status"] == "error"
    assert "HTTP 500: mid-repair drop" in rec["error"]
    # the raw reply that WAS paid for is on disk
    assert (tmp_path / "t" / "m0091.raw.txt").exists()


# ==========================================================================
#  8.  selection guards (translate.select)
# ==========================================================================

def _rows():
    return [{"id": "m0001", "section_id": "s1", "kind": "definitional"},
            {"id": "m0002", "section_id": "s2", "kind": "conditional"}]


def _sel_args(**over):
    class A:
        clause = section = kinds = limit = None
    for k, v in over.items():
        setattr(A, k, v)
    return A()


_SEL_CFG = {"corpus": {"id_key": "id", "section_key": "section_id",
                       "kind_key": "kind"},
            "select": {}}


def test_select_refuses_an_unknown_section_and_names_the_real_ones():
    with pytest.raises(T.CorpusError, match="s1"):
        T.select(_rows(), _SEL_CFG, _sel_args(section="nope"))


def test_select_refuses_kinds_matching_nothing():
    with pytest.raises(T.CorpusError, match="matched no clauses"):
        T.select(_rows(), _SEL_CFG, _sel_args(kinds=["holistic"]))


def test_select_refuses_limit_zero_rather_than_reading_it_as_no_limit():
    with pytest.raises(T.CorpusError, match="selects nothing"):
        T.select(_rows(), _SEL_CFG,
                 _sel_args(kinds=["definitional"], limit=0))


def test_select_refuses_an_empty_selection_outright():
    with pytest.raises(T.CorpusError, match="selection is empty"):
        T.select(_rows(), _SEL_CFG, _sel_args())


# ==========================================================================
#  9.  usage normalisation fallback (providers.py not importable)
# ==========================================================================

def test_normalize_usage_fallback_reads_togethers_nested_cached_tokens(
        monkeypatch):
    monkeypatch.setitem(sys.modules, "providers", None)  # import -> refuses
    u = T.normalize_usage({"prompt_tokens": 100, "completion_tokens": 40,
                           "prompt_tokens_details": {"cached_tokens": 60},
                           "completion_tokens_details":
                               {"reasoning_tokens": 7}})
    assert u["prompt_tokens"] == 100          # TOTAL, including cached
    assert u["cached_input_tokens"] == 60
    assert u["uncached_input_tokens"] == 40   # subtracted, never negative
    assert u["reasoning_tokens"] == 7
    empty = T.normalize_usage(None)
    assert empty["prompt_tokens"] is None
    assert empty["uncached_input_tokens"] is None


def test_log_usage_shouts_when_the_ledger_is_off(monkeypatch, capsys):
    client = _client(monkeypatch, {"usage_log": ""})
    client._log_usage({"usage": {"cost_usd": 0.01}})
    assert "in NO ledger" in capsys.readouterr().out
    assert client.calls == 1 and client.spent_usd == 0.01


# ==========================================================================
#  10.  BUG 2 — dispatch_core retries a payment-required error as transient
# ==========================================================================

def test_http_402_rides_a_short_ladder_then_fails(monkeypatch):
    """FIXED (was BUG 2, steps-1-4 audit 2026-08-12): 402 as a full
    transient burned 630s of backoff on terminal credit exhaustion. It
    stays retryable AT ALL -- rejected alternative, by name: terminal 402 --
    because together.ai 402s flapped for ~minutes after mid-campaign credit
    top-ups; two retries (~90s) ride out a flap and fail fast on real
    exhaustion."""
    import dispatch_core as dc

    sleeps = []
    monkeypatch.setattr(dc.time, "sleep", sleeps.append)

    sends = []

    class _BrokeClient:
        def complete(self, system, user):
            sends.append(user)
            raise T.ProviderError("HTTP 402: Credit limit exceeded")

    class _Drv:
        client = _BrokeClient()
        brief, out, cfg = "brief", "", {}

    class _State:
        schema = None
        status = dc.PENDING
        error = None

        def bill(self, cost):
            pass

    ex = dc.SerialExecutor(_Drv())
    with pytest.raises(T.ProviderError, match="HTTP 402"):
        ex._ladder(_State(), [{"role": "user", "content": "u"}])
    assert len(sends) == 3, "exactly two retries for a credit flap"
    assert sleeps == [30, 60], "~90s rides out propagation, then fail fast"


def test_a_genuinely_terminal_error_is_not_retried(monkeypatch):
    """Contrast case: HTTP 400 is not in the marks and fails on send #1."""
    import dispatch_core as dc

    monkeypatch.setattr(dc.time, "sleep",
                        lambda s: pytest.fail("slept on a terminal error"))
    sends = []

    class _BrokeClient:
        def complete(self, system, user):
            sends.append(user)
            raise T.ProviderError("HTTP 400: bad request")

    class _Drv:
        client = _BrokeClient()
        brief, out, cfg = "brief", "", {}

    class _State:
        schema = None
        status = dc.PENDING
        error = None

        def bill(self, cost):
            pass

    with pytest.raises(T.ProviderError, match="HTTP 400"):
        dc.SerialExecutor(_Drv())._ladder(
            _State(), [{"role": "user", "content": "u"}])
    assert len(sends) == 1


# ==========================================================================
#  11.  readback_r3: the xclingo transport failures R3 must refuse on
# ==========================================================================

def test_run_xclingo_refuses_when_the_binary_is_missing():
    with pytest.raises(R3.R3Error, match="could not be executed"):
        R3.run_xclingo("a.", xclingo=["/nonexistent/xclingo-not-here"])


def test_run_xclingo_refuses_on_timeout():
    slow = [sys.executable, "-c", "import time; time.sleep(5)"]
    with pytest.raises(R3.R3Error, match="did not finish within"):
        R3.run_xclingo("a.", xclingo=slow, timeout=0.2)


def test_run_xclingo_refuses_a_clean_exit_with_no_completion_marker():
    """Detector 3: exit 0, empty stdout — a crash-shaped success that must
    never be read as 'ran and found nothing'."""
    silent = [sys.executable, "-c", "pass"]
    with pytest.raises(R3.R3Error, match="no completion marker"):
        R3.run_xclingo("a.", xclingo=silent)


# ==========================================================================
#  12.  seats: the id/entry pairing refusals
# ==========================================================================

def test_entry_lines_refuses_an_id_count_that_mismatches_the_entries():
    with pytest.raises(seats.SeatRefused, match="one-to-one"):
        seats._entry_lines(["a", "b"], ids=("only-one",), seat="4b")


def test_4a_and_4b_refuse_a_vacuous_pass_with_no_renderings():
    with pytest.raises(seats.SeatRefused, match="vacuous pass"):
        seats.build_4a_prompt("clause", "{}", renderings=())
    with pytest.raises(seats.SeatRefused, match="vacuous pass"):
        seats.build_4b_prompt("clause", renderings=())
