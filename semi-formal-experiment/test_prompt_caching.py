"""Prompt caching in the provider layer — asserted on the REQUEST PAYLOAD.

Every test here builds the body that WOULD be sent and inspects it. Nothing
in this file may make a network call: a live call to `sol` costs real money
against a hard budget, and the whole point of the layer under test is to make
that call cheaper, not to make more of them.

Three mutants this file exists to catch:

  1. caching silently disabled — the constant prefix stops being marked
     (anthropic) or the routing key stops being sent (openai);
  2. the prefix is not actually stable — variable content leaks into the
     region the provider is asked to cache, so every call is a cache MISS
     billed at the WRITE premium, i.e. worse than no caching at all;
  3. a provider with no prompt cache silently pretends to have one.

The usage half (which tokens came from cache, and therefore what the call
cost) is asserted here at the envelope level and in `test_spend_logging.py`
at the money level.
"""
from __future__ import annotations

import io
import json
import urllib.request

import pytest

import providers


# --------------------------------------------------------------------------
# helpers

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _openai(**kw):
    kw.setdefault("base_url", "https://api.openai.com/v1")
    return providers.ProviderConfig(
        name="oa", kind="openai-compatible", model="gpt-test",
        api_key_env="TEST_KEY_ENV", **kw)


def _anthropic(**kw):
    return providers.ProviderConfig(
        name="an", kind="anthropic", model="claude-test",
        api_key_env="TEST_KEY_ENV", **kw)


def _third_party(**kw):
    kw.setdefault("base_url", "https://api.together.xyz/v1")
    return providers.ProviderConfig(
        name="tp", kind="openai-compatible", model="some/oss-20b",
        api_key_env="TEST_KEY_ENV", **kw)


#: A realistic shape for this repo: a constant system prompt, then a constant
#: 361-atom vocabulary block, then the one clause that varies per call.
SYSTEM = "You annotate clauses.\n" * 40
VOCAB = "===== KNOWN ATOMS =====\n" + ("atom_%04d :: gloss\n" % 0) * 200


def _user(clause):
    return VOCAB + "===== CLAUSES =====\n" + clause


# --------------------------------------------------------------------------
# 1. which providers have a prompt cache at all — declared, never guessed

def test_openai_hosted_models_use_automatic_prefix_caching():
    assert _openai().cache_mode() == providers.CACHE_AUTOMATIC


def test_anthropic_requires_explicit_cache_control():
    assert _anthropic().cache_mode() == providers.CACHE_EXPLICIT


def test_an_unsupported_provider_is_explicitly_none_not_silently_on():
    """Together/DeepInfra-hosted OSS endpoints are OpenAI-COMPATIBLE, which is
    not the same as OpenAI-hosted. Assuming they cache would make the budget
    projection too cheap for a run we then cannot pay for."""
    assert _third_party().cache_mode() == providers.CACHE_NONE


def test_the_cache_mode_can_be_declared_in_config_and_wins():
    assert _third_party(prompt_cache="automatic").cache_mode() == \
        providers.CACHE_AUTOMATIC


def test_shipped_providers_json_declares_a_mode_for_every_frontier_model():
    by_name = {p.name: p for p in
               providers.ProviderConfig.load_all(providers.PROVIDERS_PATH)}
    assert by_name["sol"].cache_mode() == providers.CACHE_AUTOMATIC
    assert by_name["luna"].cache_mode() == providers.CACHE_AUTOMATIC
    assert by_name["fable"].cache_mode() == providers.CACHE_EXPLICIT
    assert by_name["together-cheap"].cache_mode() == providers.CACHE_NONE


# --------------------------------------------------------------------------
# 2. the cacheable region — the thing that has to be byte-stable

def test_the_cacheable_region_is_identical_across_two_different_calls():
    """THE load-bearing property. If this drifts by one byte the provider
    treats every call as a fresh prefix: no read discount, and on a provider
    that charges a write premium it costs MORE than not caching."""
    p = _openai()
    a = providers.cacheable_region(p, SYSTEM, _user("clause A"), VOCAB)
    b = providers.cacheable_region(p, SYSTEM, _user("clause B"), VOCAB)
    assert a == b
    assert a  # and it is not the empty string


def test_the_cacheable_region_actually_contains_the_constant_prefix():
    p = _openai()
    region = providers.cacheable_region(p, SYSTEM, _user("clause A"), VOCAB)
    assert SYSTEM in region and VOCAB in region


def test_the_cacheable_region_excludes_the_variable_tail():
    p = _openai()
    region = providers.cacheable_region(p, SYSTEM, _user("SENTINEL-CLAUSE"),
                                        VOCAB)
    assert "SENTINEL-CLAUSE" not in region


def test_a_declared_prefix_that_is_not_a_prefix_is_rejected_loudly():
    """Passing a `cache_prefix` the user message does not literally start with
    means the caller's mental model of its own prompt is wrong. Silently
    caching something else would be a cache miss on every call, reported as a
    saving."""
    p = _openai()
    with pytest.raises(providers.CachePrefixError):
        providers.build_request_body(p, SYSTEM, _user("c"), cache_prefix="nope")


# --------------------------------------------------------------------------
# 3. the OpenAI-compatible body

def test_openai_body_never_carries_cache_control():
    """`cache_control` is Anthropic's field. Sending it to OpenAI is a 400."""
    body = providers.build_request_body(_openai(), SYSTEM, _user("c"), VOCAB)
    assert "cache_control" not in json.dumps(body)


def test_openai_messages_stay_plain_strings_so_the_prefix_stays_byte_exact():
    body = providers.build_request_body(_openai(), SYSTEM, _user("c"), VOCAB)
    assert body["messages"][0] == {"role": "system", "content": SYSTEM}
    assert body["messages"][1]["content"] == _user("c")


def test_openai_sends_a_prompt_cache_key():
    body = providers.build_request_body(_openai(), SYSTEM, _user("c"), VOCAB)
    assert body.get("prompt_cache_key")


def test_the_prompt_cache_key_is_the_same_for_every_call_sharing_a_prefix():
    """The key is what routes two calls to the same cache. If it varies per
    call the provider is free to shard them apart and the hit rate collapses
    — the exact silent-disable mutant."""
    p = _openai()
    k1 = providers.build_request_body(p, SYSTEM, _user("A"), VOCAB)["prompt_cache_key"]
    k2 = providers.build_request_body(p, SYSTEM, _user("B"), VOCAB)["prompt_cache_key"]
    assert k1 == k2


def test_the_prompt_cache_key_changes_when_the_constant_prefix_changes():
    p = _openai()
    k1 = providers.build_request_body(p, SYSTEM, _user("A"), VOCAB)["prompt_cache_key"]
    k2 = providers.build_request_body(p, SYSTEM + "!", _user("A"), VOCAB)["prompt_cache_key"]
    assert k1 != k2


def test_a_none_cache_provider_sends_no_caching_fields_at_all():
    body = providers.build_request_body(_third_party(), SYSTEM, _user("c"), VOCAB)
    assert "prompt_cache_key" not in body
    assert "cache_control" not in json.dumps(body)


# --------------------------------------------------------------------------
# 4. the Anthropic body — explicit breakpoints

def _blocks(body):
    return body["system"], body["messages"][0]["content"]


def test_anthropic_marks_the_system_prompt_as_cacheable():
    sys_blocks, _ = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM, _user("c"), VOCAB))
    assert sys_blocks[0]["text"] == SYSTEM
    assert sys_blocks[0]["cache_control"] == {"type": "ephemeral"}


def test_anthropic_marks_the_constant_user_prefix_as_cacheable():
    _, user_blocks = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM, _user("c"), VOCAB))
    assert user_blocks[0]["text"] == VOCAB
    assert user_blocks[0]["cache_control"] == {"type": "ephemeral"}


def test_anthropic_leaves_the_variable_tail_unmarked():
    _, user_blocks = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM,
                                     _user("SENTINEL"), VOCAB))
    tail = user_blocks[-1]
    assert "SENTINEL" in tail["text"]
    assert "cache_control" not in tail


def test_anthropic_reassembles_to_exactly_the_original_prompt():
    """A split that drops or duplicates a byte changes what the model sees."""
    user = _user("clause text here")
    _, blocks = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM, user, VOCAB))
    assert "".join(b["text"] for b in blocks) == user


def test_anthropic_never_exceeds_the_four_breakpoint_limit():
    body = providers.build_request_body(_anthropic(), SYSTEM, _user("c"), VOCAB)
    assert json.dumps(body).count('"cache_control"') <= 4


def test_anthropic_emits_no_empty_text_block_when_the_tail_is_empty():
    """An empty text block is a 400. It happens when the whole user message is
    constant, which is exactly the best case for caching."""
    _, blocks = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM, VOCAB, VOCAB))
    assert all(b["text"] for b in blocks)


def test_anthropic_without_a_declared_prefix_still_caches_the_system_block():
    """The system prompt is constant by construction. A caller that has not
    yet been taught to declare its user-message prefix should not lose that."""
    sys_blocks, _ = _blocks(
        providers.build_request_body(_anthropic(), SYSTEM, _user("c")))
    assert sys_blocks[0]["cache_control"] == {"type": "ephemeral"}


def test_a_none_cache_anthropic_style_provider_sends_no_breakpoints():
    p = _anthropic(prompt_cache="none")
    body = providers.build_request_body(p, SYSTEM, _user("c"), VOCAB)
    assert "cache_control" not in json.dumps(body)


# --------------------------------------------------------------------------
# 5. minimum cacheable prefix — a prefix below it silently does not cache

def test_a_prefix_below_the_provider_minimum_is_reported_as_uncacheable():
    p = _openai()
    assert providers.prefix_caches(p, "tiny") is False


def test_a_prefix_above_the_minimum_is_reported_as_cacheable():
    p = _openai()
    assert providers.prefix_caches(p, SYSTEM + VOCAB) is True


def test_the_minimum_is_configurable_per_provider():
    assert _openai(min_cacheable_tokens=99999).cache_mode() is not None
    assert providers.prefix_caches(
        _openai(min_cacheable_tokens=99999), SYSTEM + VOCAB) is False


# --------------------------------------------------------------------------
# 6. usage normalization — what the call actually cost

def test_openai_cached_tokens_are_read_from_prompt_tokens_details():
    env = providers._envelope("openai-compatible", {
        "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10000, "completion_tokens": 500,
                  "prompt_tokens_details": {"cached_tokens": 9000}}})
    assert env["usage"]["cached_input_tokens"] == 9000


def test_openai_prompt_tokens_are_the_total_and_already_include_cached():
    """OpenAI reports cached tokens as a SUBSET of prompt_tokens. Adding them
    on would overstate the bill; subtracting them from nothing would
    understate it. The envelope must say which convention it uses."""
    env = providers._envelope("openai-compatible", {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 10000, "completion_tokens": 1,
                  "prompt_tokens_details": {"cached_tokens": 9000}}})
    u = env["usage"]
    assert u["prompt_tokens"] == 10000
    assert u["uncached_input_tokens"] == 1000


def test_openai_with_no_cache_details_reports_zero_not_none():
    env = providers._envelope("openai-compatible", {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 2}})
    assert env["usage"]["cached_input_tokens"] == 0
    assert env["usage"]["cache_write_tokens"] == 0


def test_anthropic_prompt_tokens_include_the_cache_fields():
    """Anthropic's `input_tokens` EXCLUDES both cache fields. Logging it as
    the prompt total undercounts a cached call by ~90% of its input — the
    budget would read a cheap run as free."""
    env = providers._envelope("anthropic", {
        "content": [{"type": "text", "text": "hi"}],
        "usage": {"input_tokens": 500, "output_tokens": 100,
                  "cache_creation_input_tokens": 0,
                  "cache_read_input_tokens": 9500}})
    assert env["usage"]["prompt_tokens"] == 10000
    assert env["usage"]["cached_input_tokens"] == 9500
    assert env["usage"]["uncached_input_tokens"] == 500


def test_anthropic_cache_writes_are_recorded_separately_from_reads():
    """A write is billed ABOVE the input rate, a read far below it. Collapsing
    them into one number gets the first call of every run wrong."""
    env = providers._envelope("anthropic", {
        "content": [{"type": "text", "text": "hi"}],
        "usage": {"input_tokens": 500, "output_tokens": 100,
                  "cache_creation_input_tokens": 9500,
                  "cache_read_input_tokens": 0}})
    u = env["usage"]
    assert u["cache_write_tokens"] == 9500
    assert u["cached_input_tokens"] == 0
    assert u["prompt_tokens"] == 10000


def test_a_response_with_no_usage_at_all_does_not_invent_zeros():
    env = providers._envelope("openai-compatible",
                              {"choices": [{"message": {"content": "hi"}}]})
    assert env["usage"]["prompt_tokens"] is None


# --------------------------------------------------------------------------
# 7. end to end through the transport, with a faked socket

@pytest.fixture
def live_openai(monkeypatch):
    monkeypatch.setenv("TEST_KEY_ENV", "sk-not-a-real-key")
    return providers.LiveClient(_openai())


def _fake_urlopen(payload, seen=None):
    def _open(req, timeout=None):
        if seen is not None:
            seen.append(json.loads(req.data.decode()))
        return _Resp(json.dumps(payload).encode())
    return _open


def test_the_wire_request_carries_the_caching_fields(live_openai, monkeypatch,
                                                     tmp_path):
    seen = []
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(
        {"choices": [{"message": {"content": "hi"}}],
         "usage": {"prompt_tokens": 1, "completion_tokens": 1}}, seen))
    live_openai.complete_envelope(SYSTEM, _user("c"),
                                  usage_log=str(tmp_path / "u.jsonl"),
                                  cache_prefix=VOCAB)
    assert seen and seen[0].get("prompt_cache_key")


def test_cached_token_counts_reach_the_usage_log(live_openai, monkeypatch,
                                                 tmp_path):
    """`spend.py` prices rows from this file. A field that never lands here
    cannot be billed correctly no matter what the arithmetic does."""
    log = tmp_path / "usage.jsonl"
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(
        {"choices": [{"message": {"content": "hi"}}],
         "usage": {"prompt_tokens": 10000, "completion_tokens": 20,
                   "prompt_tokens_details": {"cached_tokens": 9000}}}))
    live_openai.complete_envelope(SYSTEM, _user("c"), usage_log=str(log),
                                  cache_prefix=VOCAB)
    row = json.loads(log.read_text().splitlines()[0])
    assert row["prompt_tokens"] == 10000
    assert row["cached_input_tokens"] == 9000
    assert row["cache_write_tokens"] == 0


# --------------------------------------------------------------------------
# 8. the cost re-derivation is comparable to the one it replaces
#
# The whole point of `ladder_cost_cached.py` is that its cached number can be
# read against ladder.py's uncached number. That is only true if the two agree
# where they should — i.e. with the discount switched off.

def test_the_cached_cost_model_reproduces_ladders_uncached_number():
    """If these drift, the cached table is not a caching result — it is a
    second, differently-wrong cost model, and the comparison a real spending
    decision rests on is meaningless."""
    ladder = pytest.importorskip("ladder")
    lcc = pytest.importorskip("ladder_cost_cached")
    mine = lcc.build(rungs=("3",), models=("sol",))["sol"]["3"]
    theirs = ladder.estimate_cost(rungs=("3",), models=("sol",),
                                  controls=False)["sol"]["3"]
    assert mine["in_tokens"] == pytest.approx(theirs["in_tokens"])
    assert mine["out_high"] == pytest.approx(theirs["out_tokens_high"])
    assert mine["usd_uncached"] == pytest.approx(theirs["usd"], rel=1e-9)


def test_the_cached_number_is_strictly_below_the_uncached_one():
    lcc = pytest.importorskip("ladder_cost_cached")
    d = lcc.build(rungs=("3",), models=("sol",))["sol"]["3"]
    assert 0 < d["usd"] < d["usd_uncached"]
    assert d["cache_share"] > 0.5, "the constant prefix is most of the request"


def test_the_first_call_of_a_group_is_never_credited_as_a_cache_read():
    """A cache must be written before it can be read. Crediting all N calls
    overstates the saving on exactly the run being approved."""
    lcc = pytest.importorskip("ladder_cost_cached")
    d = lcc.build(rungs=("3",), models=("sol",))["sol"]["3"]
    n_ann = 125
    # tolerance is 1e-3; crediting all N calls instead of N-1 is 1/125 = 8e-3,
    # so the off-by-one-call mutant is still caught.
    assert d["cached_tokens"] == pytest.approx(
        d["prefix_tokens"][0] * (n_ann - 1), rel=1e-3)


def test_the_existing_two_argument_call_still_works(live_openai, monkeypatch,
                                                    tmp_path):
    """annotate.py / readback.py / ladder.py call this with two positional
    arguments and are owned by other agents. Caching must not require them to
    change before it does anything at all."""
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(
        {"choices": [{"message": {"content": "hi"}}],
         "usage": {"prompt_tokens": 1, "completion_tokens": 1}}))
    env = live_openai.complete_envelope(SYSTEM, _user("c"),
                                        usage_log=str(tmp_path / "u.jsonl"))
    assert env["text"] == "hi"
