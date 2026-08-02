"""Provider-agnostic LLM client layer. NO provider is assumed; everything
comes from providers.json. Dry-run is the default — live calls require both
a resolvable API key and an explicit live=True from the caller.

providers.json format:
[
  {"name": "kimi",  "kind": "openai-compatible",
   "base_url": "https://api.moonshot.ai/v1", "model": "kimi-k3",
   "api_key_env": "MOONSHOT_API_KEY"},
  {"name": "qwen",  "kind": "openai-compatible", ...},
  {"name": "anthropic-example", "kind": "anthropic",
   "model": "claude-sonnet-4-6", "api_key_env": "ANTHROPIC_API_KEY"}
]

"openai-compatible" covers most hosted open models (Kimi, Qwen, Llama via
Together/OpenRouter/etc.) — only base_url/model/key differ. The ensemble for
stage 1 is just a list of provider names.

PROMPT CACHING
--------------
Every annotation call in this repo re-sends the same system prompt and the
same 361-atom vocabulary block — ~95% of the request — and the provider will
bill that once instead of 125 times IF the request lets it. The two families
do it differently and the difference is not cosmetic:

  * OpenAI-hosted models cache a stable prompt PREFIX automatically. There is
    no request field that turns it on, so "we did nothing" and "it works" look
    identical from the code. What the code CAN do is (a) keep the prefix
    byte-stable, and (b) send `prompt_cache_key` so calls sharing a prefix are
    routed to the same cache instead of being sharded apart. Cached input is
    reported in `usage.prompt_tokens_details.cached_tokens` and is a SUBSET of
    `prompt_tokens`.

  * Anthropic caches nothing unless the request carries an explicit
    `cache_control` breakpoint at the end of the region to cache. Its usage
    reports `cache_creation_input_tokens` (billed ABOVE the input rate) and
    `cache_read_input_tokens` (billed far below it), and — the trap —
    `input_tokens` EXCLUDES both. Logging `input_tokens` as the prompt total
    undercounts a cached call by most of its input.

  * Everything else (Together, DeepInfra, ...) is OpenAI-COMPATIBLE, which is
    not the same as OpenAI-hosted. Their caching behaviour is not something
    this repo has measured, so it is declared CACHE_NONE: inert and visible,
    never a silent no-op dressed up as a saving.

`_envelope` normalizes all of that to ONE convention, so `spend.py` never has
to know which provider a row came from:

    prompt_tokens        total input, cached and uncached alike
    cached_input_tokens  served from cache      (cheap rate)
    cache_write_tokens   written to cache       (premium rate)
    uncached_input_tokens = prompt - cached - write   (full rate)
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROVIDERS_PATH = os.path.join(HERE, "providers.json")

#: Provider caches a stable prefix on its own; the request carries no
#: cache markers, only a routing key.
CACHE_AUTOMATIC = "automatic"
#: Provider caches only what the request explicitly marks.
CACHE_EXPLICIT = "explicit"
#: No prompt cache we support. Declared, so a cost projection cannot quietly
#: assume a discount that will not arrive.
CACHE_NONE = "none"

#: Hosts whose OpenAI-compatible endpoint is the real OpenAI service and
#: therefore caches prefixes automatically. Membership is a claim about a
#: vendor, so it lives in one named place rather than in an `if` somewhere.
AUTO_CACHE_HOSTS = ("api.openai.com",)

#: Below this many tokens a prefix silently does not cache — no error, just no
#: discount. 1024 for both families today; overridable per provider.
DEFAULT_MIN_CACHEABLE_TOKENS = 1024

#: Only used to decide whether a prefix clears the minimum above. There is no
#: tokenizer in this environment; 4.59 chars/token is the ratio MEASURED on
#: this repo's own logged calls (see ladder.calibrate_chars_per_token). A
#: rough ratio is fine here because the decision is order-of-magnitude.
CHARS_PER_TOKEN = 4.59


class CachePrefixError(ValueError):
    """A caller declared a cacheable prefix its prompt does not start with.

    Raised, never worked around: caching the wrong bytes is not a smaller
    saving, it is a cache MISS on every call — and on a provider that charges
    a write premium it costs more than not caching at all, while the cost
    report shows a discount.
    """


class ProviderConfig:
    def __init__(self, name, kind, model, api_key_env=None,
                 base_url=None, max_tokens=4096, temperature=0.2,
                 api_key_file=None, price_per_mtok=None,
                 prompt_cache=None, cached_input_per_mtok=None,
                 cache_write_multiplier=1.25, prompt_cache_key=None,
                 min_cacheable_tokens=DEFAULT_MIN_CACHEABLE_TOKENS, **extra):
        self.price_per_mtok = price_per_mtok   # [$/Mtok in, $/Mtok out] or None
        self.extra = extra                     # tolerate unknown config keys
        self.name = name
        self.kind = kind                    # openai-compatible | anthropic
        self.model = model
        self.api_key_env = api_key_env
        self.api_key_file = api_key_file    # fallback: file containing only the key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        #: None => infer from kind/host. A string overrides the inference, so
        #: a provider whose behaviour we later measure can be corrected in
        #: config rather than in code.
        self.prompt_cache = prompt_cache
        #: $/Mtok billed for input served from cache. None means UNKNOWN, and
        #: spend.py then bills cached tokens at the FULL input rate and says
        #: so — overstating is survivable, understating is how a hard budget
        #: gets blown.
        self.cached_input_per_mtok = cached_input_per_mtok
        #: Anthropic bills a cache WRITE above the input rate.
        self.cache_write_multiplier = cache_write_multiplier
        self._prompt_cache_key = prompt_cache_key
        self.min_cacheable_tokens = min_cacheable_tokens

    def cache_mode(self):
        """CACHE_AUTOMATIC | CACHE_EXPLICIT | CACHE_NONE."""
        if self.prompt_cache:
            return self.prompt_cache
        if self.kind == "anthropic":
            return CACHE_EXPLICIT
        if self.kind == "openai-compatible":
            host = (self.base_url or "").split("//", 1)[-1].split("/", 1)[0]
            if host.split(":")[0] in AUTO_CACHE_HOSTS:
                return CACHE_AUTOMATIC
        return CACHE_NONE

    def sends_prompt_cache_key(self):
        """`prompt_cache_key` is an OpenAI field. Sending it to an endpoint
        that merely speaks the OpenAI dialect risks a 400, so it is on only
        where automatic caching is claimed — or where config says so."""
        if self._prompt_cache_key is not None:
            return bool(self._prompt_cache_key)
        return self.cache_mode() == CACHE_AUTOMATIC

    @classmethod
    def load_all(cls, path):
        with open(path) as f:
            return [cls(**p) for p in json.load(f)]

    def key(self):
        k = os.environ.get(self.api_key_env) if self.api_key_env else None
        if not k and self.api_key_file:
            path = os.path.expanduser(self.api_key_file)
            if os.path.exists(path):
                with open(path) as f:
                    k = f.read().strip()
        if not k and self.api_key_env:
            k = _parse_shell_export("~/.zshrc", self.api_key_env)
        return k or None


def _parse_shell_export(rc_path, var):
    """Last-resort key lookup: read `export VAR=value` from the user's shell
    rc (keys live in ~/.zshrc per project convention; this process runs under
    bash and doesn't source it). The value is returned in-process only —
    never logged, printed, or written."""
    path = os.path.expanduser(rc_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"export {var}="):
                    val = line.split("=", 1)[1].strip()
                    return val.strip("'\"") or None
    except OSError:
        return None
    return None


# --------------------------------------------------------------------------
# prompt caching — request construction

def cacheable_region(provider, system, user, cache_prefix=None):
    """The exact bytes the provider is being asked to cache for this call.

    Exposed (rather than buried in the body builder) so a caller — or a test —
    can assert the region is IDENTICAL across two calls that differ only in
    their variable tail. That property is the whole mechanism: if it drifts by
    one byte there is no cache hit, and the only visible symptom is a bill.
    """
    _check_prefix(user, cache_prefix)
    return system + (cache_prefix or "")


def _check_prefix(user, cache_prefix):
    if cache_prefix is not None and not user.startswith(cache_prefix):
        raise CachePrefixError(
            "declared cache_prefix is not a prefix of the user message "
            f"(prefix {len(cache_prefix)} chars, user {len(user)} chars); "
            "caching the wrong bytes is a miss on every call, not a smaller "
            "saving")


def prefix_caches(provider, region):
    """Would `region` actually be cached, or is it below the minimum?

    Providers do not error on a too-short prefix; they just silently do not
    cache it. A projection that assumes a discount here would be wrong with no
    signal, so the check is explicit.
    """
    if provider.cache_mode() == CACHE_NONE:
        return False
    return len(region) / CHARS_PER_TOKEN >= provider.min_cacheable_tokens


def cache_key_for(system, cache_prefix=None):
    """Stable routing key for every call sharing this constant prefix.

    Derived from the prefix itself, so two calls share a key exactly when they
    share a prefix — no counter, no timestamp, no uuid, nothing that would
    shard the cache and turn every call into a write.
    """
    h = hashlib.sha256((system + (cache_prefix or "")).encode("utf-8"))
    return "sfx-" + h.hexdigest()[:32]


def build_request_body(provider, system, user, cache_prefix=None):
    """The JSON body this provider would be sent. No network, no key needed.

    Split out of the transport so the caching contract can be verified by
    inspecting what WOULD be sent. Verifying it by sending it would cost money
    on exactly the model the caching exists to make affordable.
    """
    p = provider
    _check_prefix(user, cache_prefix)
    mode = p.cache_mode()

    if p.kind == "openai-compatible":
        # Messages stay plain strings. The prefix is a prefix by construction
        # and any block structure we invented here could only break that.
        body = {"model": p.model, "max_tokens": p.max_tokens,
                "temperature": p.temperature,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        if mode == CACHE_AUTOMATIC and p.sends_prompt_cache_key():
            body["prompt_cache_key"] = cache_key_for(system, cache_prefix)
        return body

    if p.kind == "anthropic":
        body = {"model": p.model, "max_tokens": p.max_tokens,
                "system": [{"type": "text", "text": system}],
                "messages": [{"role": "user",
                              "content": [{"type": "text", "text": user}]}]}
        if mode != CACHE_EXPLICIT:
            return body
        mark = {"type": "ephemeral"}
        body["system"][0]["cache_control"] = mark
        if cache_prefix:
            tail = user[len(cache_prefix):]
            blocks = [{"type": "text", "text": cache_prefix,
                       "cache_control": mark}]
            if tail:                       # an empty text block is a 400
                blocks.append({"type": "text", "text": tail})
            body["messages"][0]["content"] = blocks
        return body

    raise ValueError(f"unknown provider kind {p.kind}")


class DryRunClient:
    """Records prompts instead of calling anything. Returns None so callers
    must handle the no-response path explicitly."""

    def __init__(self, provider: ProviderConfig, log_dir):
        self.provider = provider
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.calls = 0

    def complete(self, system: str, user: str):
        self.calls += 1
        path = os.path.join(
            self.log_dir, f"{self.provider.name}_{self.calls:04d}.prompt.txt")
        with open(path, "w") as f:
            f.write(f"### SYSTEM ({self.provider.name}/{self.provider.model})\n")
            f.write(system + "\n\n### USER\n" + user + "\n")
        return None


class LiveClient:
    """Minimal HTTP client, stdlib only. Instantiating without a key raises."""

    def __init__(self, provider: ProviderConfig):
        self.provider = provider
        if not provider.key():
            raise RuntimeError(
                f"provider {provider.name}: no key in ${provider.api_key_env} — "
                "refusing to construct a live client")

    def complete(self, system: str, user: str):
        """Backward-compatible: returns the assistant text only."""
        return self.complete_envelope(system, user)["text"]

    def complete_envelope(self, system: str, user: str, usage_log="DEFAULT",
                          cache_prefix=None):
        """Full response envelope: {text, finish_reason, reasoning, usage}.

        finish_reason and usage are required to distinguish truncation from a
        parse failure and to price a run from measured tokens rather than from
        an assumed content size — reasoning is billed as completion tokens, and
        on a reasoning model it dominates.

        `cache_prefix` is the leading slice of `user` that is byte-identical on
        every call (this repo's case: the 361-atom vocabulary block). It is
        OPTIONAL and defaults to None so existing two-argument callers keep
        working: on an automatic-cache provider the prefix caches regardless
        and the key still covers the system prompt; on Anthropic, omitting it
        caches the system block only. Declaring it is strictly better.
        """
        p = self.provider
        ua = "semi-formal-experiment/0.1"
        body = build_request_body(p, system, user, cache_prefix)
        if p.kind == "openai-compatible":
            url = p.base_url.rstrip("/") + "/chat/completions"
            headers = {"Authorization": f"Bearer {p.key()}",
                       "Content-Type": "application/json", "User-Agent": ua}
        elif p.kind == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": p.key(), "anthropic-version": "2023-06-01",
                       "Content-Type": "application/json", "User-Agent": ua}
        else:
            raise ValueError(f"unknown provider kind {p.kind}")
        req = urllib.request.Request(
            url, json.dumps(body).encode(), headers=headers)
        for attempt in range(4):
            try:
                req = urllib.request.Request(
                    url, json.dumps(body).encode(), headers=headers)
                with urllib.request.urlopen(req, timeout=600) as resp:
                    data = json.load(resp)
                env = _envelope(p.kind, data)
                env["provider"] = p.name
                env["model"] = p.model
                if usage_log:
                    _append_usage(usage_log, env)
                return env
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode()[:800]
                except Exception:
                    pass
                # Newer reasoning models reject parameters older ones require.
                # Adapt once per offending parameter rather than hardcoding
                # model-name patterns, then retry.
                if e.code == 400 and attempt < 3:
                    adapted = _adapt_body(body, detail)
                    if adapted is not None:
                        body = adapted
                        continue
                if e.code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"{p.name}/{p.model} HTTP {e.code}: {detail}") from e


def _adapt_body(body, detail):
    """Rewrite one unsupported parameter named in a 400 body. Returns the new
    body, or None if the complaint isn't one we know how to fix."""
    try:
        param = (json.loads(detail).get("error") or {}).get("param")
    except Exception:
        param = None
    if param == "max_tokens" and "max_tokens" in body:
        b = dict(body)
        b["max_completion_tokens"] = b.pop("max_tokens")
        return b
    if param == "temperature" and "temperature" in body:
        b = dict(body)          # some reasoning models allow only the default
        b.pop("temperature")
        return b
    if param and param in body:
        b = dict(body)
        b.pop(param)
        return b
    return None


def _usage(kind, u):
    """One token convention for both families — see the module docstring.

    The two providers disagree about what `input_tokens`/`prompt_tokens`
    MEANS, and the disagreement is worth ~90% of a cached call's input:

      OpenAI:    prompt_tokens INCLUDES cached_tokens.
      Anthropic: input_tokens EXCLUDES both cache fields.

    So `prompt_tokens` here is always the TOTAL, and the cached and written
    parts are carried alongside it. `spend.py` subtracts; it never adds.
    """
    if kind == "anthropic":
        write = u.get("cache_creation_input_tokens")
        read = u.get("cache_read_input_tokens")
        raw_in = u.get("input_tokens")
        if raw_in is None and write is None and read is None:
            prompt = None            # no usage at all — do not invent a zero
        else:
            prompt = (raw_in or 0) + (write or 0) + (read or 0)
        write, read = write or 0, read or 0
        completion = u.get("output_tokens")
    else:
        prompt = u.get("prompt_tokens", u.get("input_tokens"))
        details = u.get("prompt_tokens_details") or {}
        read = u.get("cached_tokens", details.get("cached_tokens")) or 0
        write = 0                    # automatic caching bills no write premium
        completion = u.get("completion_tokens", u.get("output_tokens"))
    uncached = None if prompt is None else max(prompt - read - write, 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "reasoning_tokens": (u.get("reasoning_tokens")
                             or (u.get("completion_tokens_details") or {})
                             .get("reasoning_tokens")),
        "cached_input_tokens": read,
        "cache_write_tokens": write,
        "uncached_input_tokens": uncached,
    }


def _envelope(kind, data):
    """Normalize OpenAI-compatible and Anthropic payloads to one shape."""
    if kind == "openai-compatible":
        ch = (data.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
        if not reasoning and isinstance(msg.get("reasoning_details"), list):
            reasoning = "".join(d.get("text", "")
                                for d in msg["reasoning_details"]
                                if isinstance(d, dict))
        text = msg.get("content") or ""
        finish = ch.get("finish_reason")
    else:  # anthropic
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks
                       if isinstance(b, dict) and b.get("type") != "thinking")
        reasoning = "".join(b.get("thinking", "") for b in blocks
                            if isinstance(b, dict) and b.get("type") == "thinking")
        finish = data.get("stop_reason")
    usage = _usage(kind, data.get("usage") or {})
    return {"text": text or "", "finish_reason": finish,
            "reasoning": reasoning or "", "usage": usage,
            "truncated": str(finish or "").lower() in
                         ("length", "max_tokens", "max_output_tokens")}


DEFAULT_USAGE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "usage.jsonl")


def _append_usage(path, env):
    """Append one measured call. `path` may be the sentinel "DEFAULT".

    Logging is on by default and opt-OUT (pass usage_log=None) because a
    missed call is an invisible undercount of real spend, and the session
    operates under a hard budget. An extra row is harmless; a missing one is
    not.
    """
    if path == "DEFAULT":
        path = DEFAULT_USAGE_LOG
    if path is None:
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    row = {"ts": time.time(), "provider": env.get("provider"),
           "model": env.get("model"), "finish_reason": env.get("finish_reason"),
           "truncated": env.get("truncated"),
           "content_chars": len(env.get("text") or ""),
           "reasoning_chars": len(env.get("reasoning") or ""),
           **(env.get("usage") or {})}
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def make_client(provider: ProviderConfig, live: bool, log_dir="prompt_log"):
    if live:
        return LiveClient(provider)
    return DryRunClient(provider, log_dir)
