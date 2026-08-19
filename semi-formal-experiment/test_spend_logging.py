"""Behavioural tests for the spend/transport layer.

This layer had NO tests, and an adversarial review confirmed five separate
mutations survived the whole suite -- including `_append_usage` gutted to a
no-op and `cost_of` ignoring completion tokens (which halves the bill). The
session runs under a hard budget enforced against this number, so "the code
looks right" is not enough: these tests drive the real transport with a faked
socket and assert on what actually lands in the log.

Deliberately NOT introspection tests. An earlier test asserted usage logging
worked by grepping `inspect.getsource` for the string "LiveClient"; it passed
with `_append_usage` gutted. Every test here would fail if the behaviour broke.
"""
from __future__ import annotations

import io
import json
import os
import urllib.error
import urllib.request

import pytest

import providers
import spend


class _Resp(io.BytesIO):
    """Minimal stand-in for the urlopen context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _payload(prompt=100, completion=200, finish="stop", text="hi"):
    return {
        "choices": [{"message": {"content": text}, "finish_reason": finish}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
    }


@pytest.fixture
def cfg():
    return providers.ProviderConfig(
        name="testprov", kind="openai-compatible", model="test-model",
        base_url="https://example.invalid/v1", api_key_env="TEST_KEY_ENV")


@pytest.fixture
def live(cfg, monkeypatch):
    monkeypatch.setenv("TEST_KEY_ENV", "sk-not-a-real-key")
    return providers.LiveClient(cfg)


def _fake_urlopen(payload, seen=None):
    def _open(req, timeout=None):
        if seen is not None:
            seen.append(json.loads(req.data.decode()))
        return _Resp(json.dumps(payload).encode())
    return _open


# ---- the load-bearing claim: a live call lands in the log ----

def test_live_call_appends_one_priced_row(live, monkeypatch, tmp_path):
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(_payload()))
    live.complete_envelope("sys", "usr", usage_log=str(log))

    rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    assert len(rows) == 1
    assert rows[0]["model"] == "test-model"
    assert rows[0]["provider"] == "testprov"
    assert rows[0]["prompt_tokens"] == 100
    assert rows[0]["completion_tokens"] == 200


def test_each_call_appends_its_own_row(live, monkeypatch, tmp_path):
    """Two calls must not collapse into one row -- an undercount is the whole
    failure mode this layer exists to prevent."""
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(_payload()))
    for _ in range(3):
        live.complete_envelope("sys", "usr", usage_log=str(log))
    assert len(log.read_text().strip().splitlines()) == 3


def test_usage_log_none_is_the_only_way_to_opt_out(live, monkeypatch, tmp_path):
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(_payload()))
    live.complete_envelope("sys", "usr", usage_log=None)
    assert not log.exists()


def test_truncation_is_recorded_from_the_real_envelope(live, monkeypatch, tmp_path):
    """Truncation detection lives in providers._envelope. Tests that use a
    FakeClient hand finish_reason through and never exercise it."""
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen",
                        _fake_urlopen(_payload(finish="length")))
    env = live.complete_envelope("sys", "usr", usage_log=str(log))
    assert env["truncated"] is True
    assert json.loads(log.read_text().splitlines()[0])["truncated"] is True


# ---- pricing arithmetic ----

def test_cost_uses_both_input_and_output_tokens():
    """A mutant that ignored completion tokens halved the bill and survived
    the entire suite."""
    px = {"m": (10.0, 100.0)}
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "completion_tokens": 1_000_000}, px)
    assert c == pytest.approx(110.0)


def test_output_tokens_are_priced_at_the_output_rate():
    px = {"m": (0.0, 30.0)}
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "completion_tokens": 1_000_000}, px)
    assert c == pytest.approx(30.0), "output priced at the input rate"


def test_unpriced_rows_are_flagged_not_silently_zero(tmp_path):
    """A row we cannot price must be visible. Counting it as $0.00 is how a
    budget silently overruns."""
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": "no-such-model",
                               "prompt_tokens": 999_999_999,
                               "completion_tokens": 999_999_999}) + "\n")
    t = spend.total(str(log))
    assert t["unpriced"] == 1
    assert t["total"] == 0.0


def test_total_sums_across_models(tmp_path):
    log = tmp_path / "usage.jsonl"
    px = spend.prices()
    model = next(iter(px))
    rows = [{"model": model, "prompt_tokens": 1000, "completion_tokens": 1000}
            for _ in range(4)]
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    t = spend.total(str(log))
    assert t["calls"] == 4
    assert t["total"] == pytest.approx(4 * spend.cost_of(rows[0], px))


def test_malformed_log_lines_do_not_crash_accounting(tmp_path):
    log = tmp_path / "usage.jsonl"
    log.write_text("not json\n\n" + json.dumps(
        {"model": "x", "prompt_tokens": 1, "completion_tokens": 1}) + "\n")
    assert spend.total(str(log))["calls"] == 1


# ---- cached input tokens ----
#
# Enabling prompt caching without teaching this layer about it is worse than
# not enabling it: the budget number stays plausible while being wrong in a
# direction nobody checks. Cached input is billed at a different rate and the
# two providers report it in different fields with OPPOSITE conventions about
# whether it is already inside the prompt total.

CACHED_PX = {"m": {"in": 10.0, "out": 100.0, "cached_in": 1.0,
                   "write_mult": 1.25}}


def test_cached_input_is_billed_at_the_cached_rate_not_the_input_rate():
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "cached_input_tokens": 1_000_000,
                       "completion_tokens": 0}, CACHED_PX)
    assert c == pytest.approx(1.0), "cached tokens billed at the uncached rate"


def test_cached_tokens_are_not_billed_twice():
    """`prompt_tokens` is the TOTAL on both providers after normalization.
    Adding the cached count on top would double-bill the cheapest part of the
    request and make caching look like it cost more."""
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "cached_input_tokens": 900_000,
                       "completion_tokens": 0}, CACHED_PX)
    # 100k uncached @ $10 + 900k cached @ $1
    assert c == pytest.approx(1.0 + 0.9)


def test_a_cache_write_costs_more_than_plain_input():
    """Anthropic bills a cache WRITE above the input rate. The first call of
    every run pays it, so pricing it as a read makes run one look free."""
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "cache_write_tokens": 1_000_000,
                       "completion_tokens": 0}, CACHED_PX)
    assert c == pytest.approx(12.5)


def test_a_row_with_cached_tokens_and_no_cached_price_is_not_discounted():
    """An unknown cached rate must bill at FULL price. Guessing a discount
    understates the bill, and this session runs against a hard cap where an
    understatement is the failure that matters."""
    px = {"m": {"in": 10.0, "out": 100.0, "cached_in": None}}
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "cached_input_tokens": 1_000_000,
                       "completion_tokens": 0}, px)
    assert c == pytest.approx(10.0)


def test_an_unpriced_cache_assumption_is_counted_and_surfaced(tmp_path):
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": "m", "prompt_tokens": 100,
                               "cached_input_tokens": 90,
                               "completion_tokens": 1}) + "\n")
    t = spend.total(str(log), px={"m": {"in": 10.0, "out": 100.0,
                                        "cached_in": None}})
    assert t["cache_price_assumed"] == 1


def test_legacy_two_tuple_prices_still_price_a_row():
    """`prices()` grew a shape. Existing callers pass (in, out) tuples and a
    silent TypeError here would zero the budget, not raise it."""
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "completion_tokens": 1_000_000}, {"m": (10.0, 100.0)})
    assert c == pytest.approx(110.0)


def test_a_two_tuple_price_bills_cached_tokens_at_full_rate():
    c = spend.cost_of({"model": "m", "prompt_tokens": 1_000_000,
                       "cached_input_tokens": 1_000_000,
                       "completion_tokens": 0}, {"m": (10.0, 100.0)})
    assert c == pytest.approx(10.0)


def test_total_reports_cached_and_written_tokens(tmp_path):
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": "m", "prompt_tokens": 1000,
                               "cached_input_tokens": 800,
                               "cache_write_tokens": 100,
                               "completion_tokens": 10}) + "\n")
    t = spend.total(str(log), px=CACHED_PX)
    d = t["by_model"]["m"]
    assert d["cached_in"] == 800 and d["cache_write"] == 100


def test_shipped_prices_carry_a_cached_rate_for_the_frontier_models():
    """Without a cached rate for `sol`, enabling caching changes what the run
    COSTS but not what the tracker THINKS it costs."""
    px = spend.prices()
    for model in ("gpt-5.6-sol", "gpt-5.6-luna"):
        assert px[model]["cached_in"] is not None
        assert px[model]["cached_in"] < px[model]["in"]


def test_the_cached_rate_is_never_above_the_input_rate():
    px = spend.prices()
    for name, p in px.items():
        if p.get("cached_in") is not None:
            assert p["cached_in"] <= p["in"], name


# ---- the cross-provider convention, end to end ----

def _anthropic_cfg():
    return providers.ProviderConfig(
        name="antprov", kind="anthropic", model="claude-test",
        api_key_env="TEST_KEY_ENV")


def test_an_anthropic_cached_call_is_not_undercounted(monkeypatch, tmp_path):
    """Anthropic's `input_tokens` EXCLUDES the cache fields. Logging it as the
    prompt total logged 500 tokens for a 10,000-token request — a 95%
    undercount of real spend, invisible in every report."""
    monkeypatch.setenv("TEST_KEY_ENV", "sk-not-a-real-key")
    client = providers.LiveClient(_anthropic_cfg())
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({
        "content": [{"type": "text", "text": "hi"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 500, "output_tokens": 100,
                  "cache_creation_input_tokens": 0,
                  "cache_read_input_tokens": 9500}}))
    client.complete_envelope("sys", "usr", usage_log=str(log))

    row = json.loads(log.read_text().splitlines()[0])
    assert row["prompt_tokens"] == 10000
    assert row["cached_input_tokens"] == 9500
    # 500 @ $10 + 9500 @ $1 + 100 @ $100
    assert spend.cost_of(dict(row, model="m"), CACHED_PX) == pytest.approx(
        (500 * 10.0 + 9500 * 1.0 + 100 * 100.0) / 1e6)


def test_an_openai_cached_call_is_not_overcounted(monkeypatch, tmp_path):
    """The mirror-image error: OpenAI already includes cached tokens in
    `prompt_tokens`, so a layer that adds them would overstate the bill and
    stop a run that was affordable."""
    monkeypatch.setenv("TEST_KEY_ENV", "sk-not-a-real-key")
    cfg = providers.ProviderConfig(
        name="oa", kind="openai-compatible", model="gpt-test",
        base_url="https://api.openai.com/v1", api_key_env="TEST_KEY_ENV")
    client = providers.LiveClient(cfg)
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen({
        "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10000, "completion_tokens": 100,
                  "prompt_tokens_details": {"cached_tokens": 9500}}}))
    client.complete_envelope("sys", "usr", usage_log=str(log))

    row = json.loads(log.read_text().splitlines()[0])
    assert row["prompt_tokens"] == 10000
    assert spend.cost_of(dict(row, model="m"), CACHED_PX) == pytest.approx(
        (500 * 10.0 + 9500 * 1.0 + 100 * 100.0) / 1e6)


# ---- parameter adaptation ----

def test_adapt_body_rewrites_max_tokens_for_reasoning_models():
    body = {"model": "m", "max_tokens": 4096}
    detail = json.dumps({"error": {"param": "max_tokens"}})
    out = providers._adapt_body(body, detail)
    assert out["max_completion_tokens"] == 4096 and "max_tokens" not in out


def test_adapt_body_ignores_a_complaint_it_cannot_fix():
    assert providers._adapt_body({"model": "m"}, "<html>502</html>") is None


def test_adapt_body_does_not_touch_a_param_the_error_did_not_name():
    """A mutant that always dropped temperature survived the suite. Dropping
    it silently changes sampling, and nothing records that it happened."""
    body = {"model": "m", "temperature": 0.2, "max_tokens": 8}
    out = providers._adapt_body(body, json.dumps({"error": {"param": "max_tokens"}}))
    assert out["temperature"] == 0.2


# ---- G1/G9 (2026-08-15): the gauge must not understate, and the machine
# ceiling must be the live authorization ----
#
# The review measured spend.py reading "$2.072 of $8.50 (24%)" while the
# ledger's own embedded arithmetic said over cap: 2,122 rows carried no price
# entry because the campaign's workhorse provider was defined inline in
# walkthrough/paper_pipeline/phase_1/config.json, and cost_of() priced those
# rows at None and total() SKIPPED them. The pins below construct their rows;
# the real usage.jsonl is evidence and is never edited.

CAMPAIGN_MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
CAMPAIGN_PROVIDER = "together-deepseek-v4-flash"


def test_the_campaign_inline_provider_is_now_priced():
    """The walkthrough's workhorse ran 2,100+ calls that cost_of() priced at
    None. Its list price ($0.14 in / $0.28 out per Mtok, together.ai model
    page fetched 2026-08-07, recorded at the source in phase_1/config.json's
    `_price_per_mtok` comment) belongs in the machine price table."""
    px = spend.prices()
    assert CAMPAIGN_MODEL in px, "the ledger's dominant model has no price"
    assert CAMPAIGN_PROVIDER in px
    assert px[CAMPAIGN_MODEL]["in"] == pytest.approx(0.14)
    assert px[CAMPAIGN_MODEL]["out"] == pytest.approx(0.28)


def test_the_campaign_provider_bills_cached_input_at_full_rate():
    """G1 ruling, conservative direction: the cached-input rate is KNOWN
    ($0.03/Mtok) and deliberately NOT set. The harness's own embedded
    cost_usd bills every input token at the FULL rate — config.json: 'the
    conservative direction and is what a hard [...] ledger cap deserves' —
    and spend.py's recomputation must stay equal to the rows' own arithmetic.
    Rejected alternative, by name: `cached_input_per_mtok: 0.03`."""
    px = spend.prices()
    assert px[CAMPAIGN_MODEL]["cached_in"] is None
    c = spend.cost_of({"model": CAMPAIGN_MODEL, "prompt_tokens": 1_000_000,
                       "cached_input_tokens": 900_000,
                       "completion_tokens": 0}, px)
    assert c == pytest.approx(0.14), "cached tokens were discounted"


def test_a_usage_row_with_no_price_entry_makes_the_total_loud_not_quiet(tmp_path):
    """⭐ THE G1 PIN. A row spend.py cannot price must make the gauge REFUSE
    the total, not print a partial sum in the total's place — that is how
    $9.20 of spend read as 24%."""
    log = tmp_path / "usage.jsonl"
    priced = next(iter(spend.prices()))
    log.write_text("\n".join(json.dumps(r) for r in [
        {"model": priced, "prompt_tokens": 1000, "completion_tokens": 1000},
        {"model": "no-such-provider-anywhere", "prompt_tokens": 5_000_000,
         "completion_tokens": 5_000_000}]) + "\n")
    text = "\n".join(spend.report_lines(str(log)))
    assert not any(l.startswith("TOTAL") for l in text.splitlines()), \
        "a partial sum was printed as the total"
    assert any(l.startswith("PRICED SUBTOTAL") for l in text.splitlines())
    assert "REFUSED" in text
    assert "no-such-provider-anywhere" in text


def test_a_fully_priced_ledger_still_reports_a_total(tmp_path):
    """Paired control: loudness about unpriced rows must not become
    loudness always — a fully priced ledger reports its total normally."""
    log = tmp_path / "usage.jsonl"
    priced = next(iter(spend.prices()))
    log.write_text(json.dumps(
        {"model": priced, "prompt_tokens": 1000, "completion_tokens": 1000})
        + "\n")
    text = "\n".join(spend.report_lines(str(log)))
    assert any(l.startswith("TOTAL") for l in text.splitlines())
    assert "REFUSED" not in text


def test_check_fails_closed_when_any_row_is_unpriced(tmp_path, capsys):
    """The one budget gate must not certify a sum it could not finish:
    unpriced rows present -> non-zero exit, whatever the check amount."""
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": "no-such-provider-anywhere",
                               "prompt_tokens": 10, "completion_tokens": 10})
                   + "\n")
    rc = spend.run_cli(["--check", "1e9"], usage_path=str(log))
    assert rc != 0, "--check certified a ledger it could not finish pricing"
    assert "REFUSED" in capsys.readouterr().out


def test_check_still_passes_a_fully_priced_ledger_under_budget(tmp_path):
    log = tmp_path / "usage.jsonl"
    priced = next(iter(spend.prices()))
    log.write_text(json.dumps(
        {"model": priced, "prompt_tokens": 10, "completion_tokens": 10})
        + "\n")
    assert spend.run_cli(["--check", "1e9"], usage_path=str(log)) == 0


def test_the_machine_ceiling_is_the_live_authorization():
    """G9: ONE ceiling the machine reads. Authorization history: $7.50 ->
    $8.50 (2026-08-02, BUDGET comment) -> $10.00 (Matt, 2026-08-12,
    resolve_runs/graph_v2/EXPERIMENTS.md:1291) -> $20.00 (Matt +$5,
    2026-08-14, EXPERIMENTS.md 'Budget raised to $20.00') -> $25.00 (Matt,
    2026-08-16, D6: 'spend up to $25 if necessary', recorded in the BUDGET
    constant's comment and quoted in AGENTS.md). At the old $8.50 constant
    the gauge printed a percentage against a ceiling the ledger had already
    passed with authorization to be past it."""
    assert spend.BUDGET == pytest.approx(25.00)


def test_batch_caveat_is_printed_when_the_batch_provider_has_rows(tmp_path):
    """Batch-billed rows are NOT identifiable in usage.jsonl: dispatch_core's
    batch collector ledgers them through the same response_envelope as live
    calls (cost_usd at list price, no row field marks the billing path). So
    wherever this provider's rows are priced, the gauge must say the list
    price may overstate. Paired control below."""
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": CAMPAIGN_MODEL, "prompt_tokens": 1000,
                               "completion_tokens": 1000}) + "\n")
    text = "\n".join(spend.report_lines(str(log)))
    assert "batch" in text.lower(), "no batch-billing caveat over batch rows"
    assert "OVERSTATE" in text


def test_batch_caveat_is_absent_for_providers_never_billed_by_batch(tmp_path):
    log = tmp_path / "usage.jsonl"
    log.write_text(json.dumps({"model": "gpt-5.6-luna", "prompt_tokens": 1000,
                               "completion_tokens": 1000}) + "\n")
    assert "batch" not in "\n".join(spend.report_lines(str(log))).lower()


# ---- the InstrumentedClient hole ----

def test_instrumented_client_logs_its_usage(monkeypatch, tmp_path, cfg):
    """extract_section.InstrumentedClient defined _log_usage and never called
    it, so every live extraction run was billed and absent from usage.jsonl.
    Six such runs were already on disk when this was found."""
    import extract_section as ex

    monkeypatch.setenv("TEST_KEY_ENV", "sk-not-a-real-key")
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(providers, "DEFAULT_USAGE_LOG", str(log))
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(_payload()))

    client = ex.InstrumentedClient(cfg)
    client.complete_envelope("sys", "usr")

    rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    assert len(rows) == 1, "live extraction call did not reach the spend log"
    # provider/model must be resolvable or spend.cost_of prices the row at $0
    assert rows[0]["provider"] == "testprov"
    assert rows[0]["model"] == "test-model"
    assert spend.cost_of(rows[0], {"test-model": (1.0, 1.0)}) is not None
