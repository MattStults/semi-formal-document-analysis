#!/usr/bin/env python3
"""phase_1/translate.py — ask a model for an ASP module for one clause.

    THE ONE QUESTION THIS ANSWERS:  can a model produce a logic module for a
    specification clause in the form `03_pipeline.md` stage 1 describes?

Stage 1 has never been run. Every downstream stage assumes its output. This is
the harness that finds out whether anything can enter the pipeline at all.

⛔ IT VALIDATES NOTHING ABOUT THE TRANSLATION.  It does not compile the ASP, does
not link it, does not check the headers, does not read the module back. Stage 2
is those checks and it is deliberately not built yet: we want to see raw output
before deciding what to check. A clean run here means "a model returned a fenced
block", never "the translation is right".

WHAT IT DOES FAIL ON, loudly, because a harness whose "pass" is
indistinguishable from "did not run" is broken by design:

    no API key · cost over the gate · a truncated completion · an empty
    response · a response with no fenced block · zero clauses selected ·
    a prompt file that is missing or empty

Everything that varies lives in `config.json` and `prompt/*.md`, so the model,
the API, the clause selection and the translation rules can each be worked on
without touching this file.

    python3 translate.py --self-test              # no network, no cost
    python3 translate.py                          # DRY RUN: prompt + cost, sends nothing
    python3 translate.py --clause m0255 --show-prompt
    python3 translate.py --section definitions --kinds definitional
    python3 translate.py --live                   # needs authorisation

Exit codes:  0 clean · 1 a clause failed · 2 usage/config error
"""

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graveyard as gy                                        # noqa: E402
import schema                                                  # noqa: E402
import version                                                 # noqa: E402

#: The concept dictionary is its OWN artifact, joinable across clauses and
#: across runs — never comments inside the logic files.
CONCEPT_TABLE = "concepts.json"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "config.json")


# ==========================================================================
# 1.  Errors — one class per failure the harness must not swallow
# ==========================================================================

class Phase1Error(RuntimeError):
    """Base. Every failure below is a refusal to proceed, never a warning."""


class ConfigError(Phase1Error):
    """Config is missing a key, or names a file that is absent or empty."""


class CorpusError(Phase1Error):
    """Corpus missing, or the selection matched no clauses."""


class ProviderError(Phase1Error):
    """No key, the API errored, or the completion was truncated."""


class ResponseParseError(Phase1Error):
    """A response arrived that is not the object the schema demanded."""


class CostGateError(Phase1Error):
    """Estimated spend is over the ceiling, or the provider has no prices."""


# ==========================================================================
# 2.  Config
# ==========================================================================

#: Every relative path in a config is resolved against the DIRECTORY OF THAT
#: CONFIG, not against phase_1/. It is a module global rather than a parameter
#: because `rel()` is called from a dozen places and threading a base through
#: all of them would put the path convention in twelve signatures instead of
#: one. `load_config` is the only writer.
#:
#: ⚠️ It is deliberately NOT stored in the config dict: `inputs_fingerprint`
#: hashes that dict, and an absolute path in it would make the dry-run sha
#: machine-dependent.
_BASE = HERE


def load_config(path):
    global _BASE
    if not os.path.exists(path):
        raise ConfigError(f"no config at {path}")
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    for key in ("corpus", "select", "prompt", "model", "output", "cost"):
        if key not in cfg:
            raise ConfigError(f"config is missing the `{key}` block")
    _BASE = os.path.dirname(os.path.abspath(path))
    return cfg


def rel(path):
    """Resolve a config path against the config's own directory.

    It used to resolve against phase_1/ unconditionally, which made
    `--config` anywhere else silently read phase_1's prompts and corpus.
    """
    return path if os.path.isabs(path) else os.path.normpath(
        os.path.join(_BASE, path))


# ==========================================================================
# 3.  Corpus and selection
# ==========================================================================

def load_corpus(cfg):
    c = cfg["corpus"]
    path = rel(c["path"])
    if not os.path.exists(path):
        raise CorpusError(f"corpus not found: {path}")
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    rows = blob[c["records_key"]] if isinstance(blob, dict) else blob
    if not rows:
        raise CorpusError(f"corpus {path} holds zero records")
    return rows


def select(rows, cfg, args):
    """clause_ids beats section_id beats kinds. Empty selection RAISES."""
    c, s = cfg["corpus"], dict(cfg["select"])
    if args.clause:
        s["clause_ids"] = args.clause
    if args.section is not None:
        s["section_id"] = args.section
    if args.kinds is not None:
        s["kinds"] = args.kinds
    if args.limit is not None:
        s["limit"] = args.limit

    idk, seck, kindk = c["id_key"], c["section_key"], c["kind_key"]

    if s.get("clause_ids"):
        want = list(s["clause_ids"])
        by_id = {r[idk]: r for r in rows}
        missing = [w for w in want if w not in by_id]
        if missing:
            raise CorpusError(
                f"no such clause id: {', '.join(missing)} "
                f"(a typo must not silently translate the wrong clause)")
        out = [by_id[w] for w in want]
    elif s.get("section_id"):
        out = [r for r in rows if r.get(seck) == s["section_id"]]
        if not out:
            secs = sorted({r.get(seck) for r in rows if r.get(seck)})
            raise CorpusError(
                f"no clause has section_id {s['section_id']!r}. "
                f"{len(secs)} sections exist, e.g. {', '.join(secs[:6])}")
        if s.get("kinds"):
            out = [r for r in out if r.get(kindk) in s["kinds"]]
    elif s.get("kinds"):
        out = [r for r in rows if r.get(kindk) in s["kinds"]]
    else:
        raise CorpusError(
            "selection is empty: set clause_ids, section_id or kinds. "
            "Translating the whole corpus is not something to do by accident")

    if not out:
        raise CorpusError(
            f"selection matched no clauses (kinds={s.get('kinds')})")

    # `if s.get("limit")` treated 0 as "no limit", so `--limit 0` — the
    # obvious way to ask for a no-op — quietly selected the ENTIRE selection
    # and, with --live, would have paid for it.
    if s.get("limit") is not None:
        n = int(s["limit"])
        if n <= 0:
            raise CorpusError(
                f"select.limit is {n}: that selects nothing, and 0 used to be "
                f"read as 'no limit' — the opposite of what it says. Omit "
                f"limit to translate the whole selection")
        out = out[:n]
    return out


# ==========================================================================
# 4.  Cross-references, from the document's own markdown anchors
# ==========================================================================

ANCHOR = re.compile(r"\]\(#([a-zA-Z0-9_\-]+)\)")


def cross_references(row, rows, cfg):
    """Clauses of the sections this clause's own text points at.

    ⚠️ A LOWER BOUND. Only ~13% of clauses carry anchors; a clause with none is
    not thereby dependency-free. `03_pipeline.md` records this as an open
    question — a model may be needed to find the rest.
    """
    xc = cfg["cross_references"]
    if not xc.get("enabled"):
        return [], []
    seck, kindk = cfg["corpus"]["section_key"], cfg["corpus"]["kind_key"]
    idk, textk = cfg["corpus"]["id_key"], cfg["corpus"]["text_key"]
    targets = sorted(set(ANCHOR.findall(row[textk])))
    found, unresolved = [], []
    for t in targets:
        hits = [r for r in rows
                if r.get(seck) == t and r[idk] != row[idk]
                and r.get(kindk) in xc["include_kinds"]]
        if not hits:
            unresolved.append(t)
            continue
        found.extend(hits[: int(xc["max_clauses_per_target"])])
    return found, unresolved


def render_cross_references(found, unresolved, cfg):
    if not found and not unresolved:
        return ""
    idk, textk = cfg["corpus"]["id_key"], cfg["corpus"]["text_key"]
    out = ["\nCROSS-REFERENCED CLAUSES — the text of every clause this one points at.",
           "Use these to know what the names mean. Do NOT translate them here.\n"]
    for r in found:
        out.append(f"  [{r[idk]}] {r[textk]}\n")
    if unresolved:
        out.append("  ⚠️ referenced but not resolvable in the corpus: "
                   + ", ".join(unresolved) + "\n")
    return "\n".join(out)


# ==========================================================================
# 5.  Prompt assembly — fixed block first, varying block last
# ==========================================================================

def check_no_orphan_prompts(cfg):
    """A prompt file on disk that is never sent is silently doing nothing.

    The directories scanned are DERIVED from the file list itself. This used
    to `listdir(rel("prompt"))` whatever the config said, so a config living
    anywhere else scanned phase_1/prompt and reported its four files as
    orphans — which made `--config elsewhere` impossible, and, worse, made
    that ConfigError pre-empt every other prompt guard (see `check()` in the
    self-test).
    """
    sent = {rel(f) for f in cfg["prompt"]["system_files"]}
    sent |= {rel(f) for f in (cfg["prompt"].get("unused_files") or [])}
    if not sent:
        raise ConfigError(
            "prompt.system_files is empty — the run would send a system "
            "prompt with no instructions in it and look entirely normal")
    on_disk = set()
    for d in sorted({os.path.dirname(p) for p in sent}):
        if not os.path.isdir(d):
            raise ConfigError(
                f"prompt directory not found: {d} (named by prompt."
                f"system_files/unused_files). A config that points at a "
                f"directory which is not there must refuse, not traceback")
        on_disk |= {os.path.join(d, f) for f in os.listdir(d)
                    if f.endswith(".md")}
    orphans = sorted(on_disk - sent)
    if orphans:
        raise ConfigError(
            f"prompt file(s) on disk but never sent: "
            f"{', '.join(os.path.basename(o) for o in orphans)}. "
            f"Add to prompt.system_files, or to prompt.unused_files to say "
            f"the omission is deliberate. A prompt file that exists and does "
            f"nothing looks exactly like one that is working.")


FORCING_MODES = ("json_schema", "json_object", "none")


def validate_format_forcing(cfg):
    """Reject an unknown `model.format_forcing` BEFORE anything is sent.

    It used to be validated inside `_body()` — that is past the cost gate,
    inside the per-clause `except Phase1Error`, and reached once per clause.
    A one-character config typo therefore reported as N clause failures and
    exit 1 ("a clause failed") instead of one config error and exit 2.
    """
    mode = cfg["model"].get("format_forcing", "json_schema")
    if mode not in FORCING_MODES:
        raise ConfigError(
            f"model.format_forcing={mode!r} is not one of "
            f"{' | '.join(FORCING_MODES)}")
    return mode


def sha16(blob):
    """First 16 hex of a sha256. Short enough to read, long enough to pin."""
    import hashlib
    if isinstance(blob, str):
        blob = blob.encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def config_sha(cfg):
    return sha16(json.dumps(cfg, sort_keys=True))


def inputs_fingerprint(cfg):
    """sha of everything that changes what would be sent.

    A dry-run artifact on disk is a claim about what the harness WOULD send.
    Config and prompt files move constantly; the artifact does not follow. A
    stale one is worse than none — it reads as authoritative and describes a
    configuration that no longer exists. This is what lets the self-test say so.
    """
    import hashlib
    h = hashlib.sha256()
    h.update(json.dumps(cfg, sort_keys=True).encode())
    for f in sorted(cfg["prompt"]["system_files"]):
        h.update(open(rel(f), "rb").read())
    return h.hexdigest()[:16]


def write_dry_run_artifact(cfg, args):
    """Regenerate dryrun.txt. Deterministic apart from the sha.

    (It said "dryrun.txt + selftest.txt" and only ever wrote the first;
    selftest.txt is produced by redirecting `--self-test`.)
    """
    import contextlib
    import io
    fp = inputs_fingerprint(cfg)
    out = [f"# phase_1/translate.py — DRY RUN artifact",
           f"# inputs-sha: {fp}   (config.json + every prompt file)",
           f"# Regenerate with: translate.py --write-artifact",
           f"# Nothing was sent. This is the complete prompt that WOULD be sent.",
           ""]

    class _A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = False
        show_prompt = 0
    for title, over in (
            ("default config", {}),
            ("--section definitions --kinds definitional --limit 4",
             {"section": "definitions", "kinds": ["definitional"], "limit": 4}),
            ("--clause m0255 --show-prompt 1",
             {"clause": ["m0255"], "show_prompt": 1})):
        a = type("A", (_A,), dict(over))()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run(cfg, a)
        out += [f"{'#' * 12} {title} {'#' * 12}", buf.getvalue()]

    path = rel("dryrun.txt")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print(f"wrote {path} (inputs-sha {fp})")
    return 0


def build_system(cfg):
    """The cacheable prefix: identical for every clause in a run."""
    check_no_orphan_prompts(cfg)
    parts = []
    for f in cfg["prompt"]["system_files"]:
        p = rel(f)
        if not os.path.exists(p):
            raise ConfigError(f"prompt file not found: {p}")
        txt = open(p, encoding="utf-8").read().strip()
        if not txt:
            raise ConfigError(
                f"prompt file is empty: {p} — an empty rules file would send a "
                f"prompt with no instructions and the run would look normal")
        parts.append(txt)
    return "\n\n---\n\n".join(parts)


def build_user(row, rows, cfg):
    c = cfg["corpus"]
    found, unresolved = cross_references(row, rows, cfg)
    body = cfg["prompt"]["user_template"].format(
        corpus_description=c.get("description", "a specification document"),
        id=row[c["id_key"]],
        locator=row.get("locator", ""),
        kind=row.get(c["kind_key"], ""),
        text=row[c["text_key"]],
        cross_references=render_cross_references(found, unresolved, cfg),
    )
    return body, found, unresolved


# ==========================================================================
# 6.  Provider
# ==========================================================================

class Provider:
    def __init__(self, name, kind, model, base_url, api_key_env,
                 temperature, max_tokens, price_per_mtok, native=None):
        self.name, self.kind, self.model = name, kind, model
        self.base_url, self.api_key_env = base_url, api_key_env
        self.temperature, self.max_tokens = temperature, max_tokens
        self.price_per_mtok = price_per_mtok
        self.native = native


#: The keys that say WHICH ENDPOINT IS CALLED, as opposed to how. `--provider`
#: clears every one of them from the inline block, because leaving any single
#: one behind is how a run gets relabelled without being rerouted.
_IDENTITY_KEYS = ("model", "base_url", "api_key_env", "kind", "price_per_mtok")


def resolve_provider(cfg, args):
    """Resolve the provider actually called. `--provider` REROUTES.

    ⚠️ It did not. Every field was `m.get(k) or row.get(k)`, and this config
    defines model/base_url/api_key_env inline, so `--provider luna` changed
    the display name and nothing else: the call still went to together.ai
    with together's key while `run.json` and the usage row both said `luna`.
    Spend was attributed to a provider that was never contacted. `--provider`
    now selects the providers.json row outright, or refuses.
    """
    m = dict(cfg["model"])
    forced = getattr(args, "provider", None)
    if forced:
        m["provider_name"] = forced
        for k in _IDENTITY_KEYS:
            m.pop(k, None)
    if args.model:
        m["model"] = args.model
    if args.max_tokens:
        m["max_tokens"] = args.max_tokens

    native, row = None, {}
    pj = rel(m["providers_json"]) if m.get("providers_json") else None
    inline = bool(m.get("model") and m.get("base_url"))

    if forced and not (pj and os.path.exists(pj)):
        raise ConfigError(
            f"--provider {forced!r} names a row in providers.json, but "
            f"model.providers_json is unset or missing ({pj}). Set the model "
            f"inline in a config and drop --provider, or point "
            f"model.providers_json at a real file")

    if pj and os.path.exists(pj):
        sys.path.insert(0, os.path.dirname(pj))
        rows = json.load(open(pj, encoding="utf-8"))
        hits = [r for r in rows if r["name"] == m["provider_name"]]
        if hits:
            row = hits[0]
            try:
                import providers as _p                        # noqa: WPS433
                native = _p.ProviderConfig(
                    **{**row,
                       "temperature": m.get("temperature",
                                            row.get("temperature")),
                       "max_tokens": m.get("max_tokens",
                                           row.get("max_tokens"))})
            except Exception:                 # fall back to the local client
                native = None
        elif forced:
            names = ", ".join(r["name"] for r in rows)
            raise ConfigError(
                f"--provider {forced!r} is not a row in {pj}. It is not "
                f"enough to fall back to the inline model: that would print "
                f"{forced!r}, log {forced!r}, and call somebody else. "
                f"Available rows: {names}")
        elif not inline:
            names = ", ".join(r["name"] for r in rows)
            raise ConfigError(
                f"provider {m['provider_name']!r} is not in {pj} and this "
                f"config does not define it inline (needs BOTH `model` and "
                f"`base_url`). Available rows: {names}")
    elif not inline:
        raise ConfigError(
            f"no providers.json at {pj} and no inline `model` + `base_url` — "
            f"nothing identifies which model to call")

    return Provider(
        name=m.get("provider_name") or "inline",
        kind=m.get("kind") or row.get("kind", "openai-compatible"),
        model=m.get("model") or row.get("model"),
        base_url=m.get("base_url") or row.get("base_url"),
        api_key_env=m.get("api_key_env") or row.get("api_key_env"),
        temperature=m.get("temperature", row.get("temperature", 0.2)),
        max_tokens=m.get("max_tokens", row.get("max_tokens", 8192)),
        price_per_mtok=m.get("price_per_mtok") or row.get("price_per_mtok"),
        native=native,
    )


def _resolve_key(prov):
    """Env, then the provider's own reader, then the repo's shell-rc fallback.

    Keys live in ~/.zshrc by project convention and this process runs under
    bash, so the env is usually empty. `providers._parse_shell_export` is the
    established lookup; an INLINE provider has no `native` to ask, so it is
    called directly rather than being reimplemented here.
    """
    if prov.api_key_env and os.environ.get(prov.api_key_env):
        return os.environ[prov.api_key_env]
    if prov.native is not None and hasattr(prov.native, "key"):
        try:
            if (k := prov.native.key()):
                return k
        except Exception:                                     # noqa: BLE001
            pass
    if prov.api_key_env:
        try:
            import providers as _p                            # noqa: WPS433
            for rc in ("~/.zshrc", "~/.bashrc", "~/.bash_profile"):
                if (k := _p._parse_shell_export(rc, prov.api_key_env)):
                    return k
        except Exception:                                     # noqa: BLE001
            pass
    raise ProviderError(
        f"no key for ${prov.api_key_env}: not in the environment and not an "
        f"`export {prov.api_key_env}=` line in ~/.zshrc, ~/.bashrc or "
        f"~/.bash_profile. Refusing to build a live client.")


class Client:
    """The local client, because format forcing is not optional here.

    ⚠️ WHY THIS DOES NOT USE `providers.LiveClient`.  `03_pipeline.md` stage 1
    requires format-forced output. `semi-formal-experiment/providers.py` has no
    `response_format`, no `json_schema` and no tool-use path — verified — so it
    cannot send a strict schema at all. Rather than change a module the wider
    repo's 2,156 tests depend on, phase_1 builds its own request.

    What is deliberately NOT forked: the spend ledger. Usage is appended
    through `providers._append_usage` when that module is importable — in the
    shape that function actually reads (see `response_envelope`), which is not
    what this client used to hand it.
    """

    def __init__(self, prov, cfg):
        self.p = prov
        self.cfg = cfg
        self.forcing = validate_format_forcing(cfg)
        if prov.kind != "openai-compatible":
            raise ProviderError(
                f"this client speaks openai-compatible only, not {prov.kind}")
        self.key = _resolve_key(prov)
        #: Everything this client has spent, in dollars, from measured tokens.
        #: Read at the end of a run to say out loud what `spend.py` cannot see.
        self.spent_usd = 0.0
        self.calls = 0

    def _body(self, system, user):
        p = self.p
        body = {"model": p.model, "temperature": p.temperature,
                "max_tokens": p.max_tokens,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        # `format_forcing` is validated in __init__ (and again in run(), before
        # the cost gate); by here an unknown value is impossible.
        if self.forcing == "json_schema":
            body["response_format"] = schema.response_format(
                self.cfg["model"].get("json_schema_strict", True))
        elif self.forcing == "json_object":
            body["response_format"] = {"type": "json_object"}
        return body

    def _body_messages(self, system, messages):
        """The same request, with a whole transcript instead of one user turn.

        Built from `_body` so the two entry points cannot drift: a repair
        attempt sent with a different response_format or max_tokens is quietly
        a different call from the one being repaired.
        """
        body = self._body(system, "")
        body["messages"] = [{"role": "system", "content": system}] + [
            dict(m) for m in messages]
        return body

    def complete_messages(self, system, messages):
        return self._send(self._body_messages(system, messages))

    def complete(self, system, user):
        return self._retrying(lambda: self._send(self._body(system, user)))

    def _retrying(self, send):
        """Opt-in truncation resampling (`model.resample_truncation`: extra
        draws, default 0 = the documented raise-loudly behavior). Ground:
        the graph driver measured truncation as a per-draw stochastic event
        on this provider -- the same dispatch truncated twice and completed
        clean on a later draw. A resample is a fresh draw of the SAME
        request; nothing half-finished is ever kept."""
        extra = int(self.cfg.get("model", {}).get("resample_truncation", 0))
        for i in range(extra + 1):
            try:
                return send()
            except ProviderError as exc:
                if "TRUNCATED" in str(exc) and i < extra:
                    continue
                raise

    def _send(self, body):
        import urllib.error
        import urllib.request
        url = self.p.base_url.rstrip("/") + "/chat/completions"
        req = urllib.request.Request(
            url, json.dumps(body).encode(),
            {"Authorization": f"Bearer {self.key}",
             "Content-Type": "application/json",
             "User-Agent": "walkthrough-phase1/0.1"})
        try:
            with urllib.request.urlopen(
                    req, timeout=int(os.environ.get(
                        "PHASE1_HTTP_TIMEOUT", "600"))) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:500]
            hint = ""
            if self.forcing == "json_schema" and (
                    "response_format" in detail or "json_schema" in detail
                    or exc.code == 400):
                hint = ("\n   ⇒ this provider may not support strict "
                        "json_schema. Try model.format_forcing=\"json_object\" "
                        "— but record that the shape is then NOT guaranteed at "
                        "generation, which is a departure from stage 1.")
            raise ProviderError(f"HTTP {exc.code}: {detail}{hint}") from exc
        except Exception as exc:
            raise ProviderError(str(exc)) from exc

        full = response_envelope(self.p, data)
        # Log BEFORE the truncation/emptiness guards: a truncated or empty
        # completion is billed exactly like a good one, and the guards raise.
        self._log_usage(full)
        env = _check_envelope(full)
        env["cost_usd"] = (full.get("usage") or {}).get("cost_usd") or 0.0
        return env

    def _log_usage(self, env):
        """Append one measured call, in the shape `_append_usage` reads.

        ⚠️ WHAT WAS WRONG. This passed `{"provider", "model", "usage": <the
        raw together.ai dict>}`. `providers._append_usage` builds its row from
        `finish_reason`, `truncated`, `text`, `reasoning` and `**usage`, so
        every row this harness wrote carried `finish_reason: null`,
        `truncated: null`, `content_chars: 0`, and together's cached-token
        count still nested inside `prompt_tokens_details` where `spend.py`
        never looks. `response_envelope` now produces the normalized shape.
        """
        self.calls += 1
        self.spent_usd += (env.get("usage") or {}).get("cost_usd") or 0.0
        log = self.cfg["model"].get("usage_log", "DEFAULT")
        if not log:
            print("  ⚠️ model.usage_log is off — this call is in NO ledger")
            return
        try:
            import providers as _p                            # noqa: WPS433
            _p._append_usage(log, env)                        # noqa: SLF001
        except Exception as exc:                              # noqa: BLE001
            print(f"  ⚠️ usage not logged to the ledger ({exc}) — "
                  f"spend.py will under-count this run")


def normalize_usage(raw):
    """together.ai's usage dict -> the repo's convention, exactly.

    Prefers `providers._usage`, so this harness cannot drift from the module
    that defines the convention; the fallback below is the same arithmetic and
    exists only so the self-test runs when providers.py is not importable.

    `prompt_tokens` is the TOTAL including cached; the cached part is carried
    alongside it, because `spend.py` subtracts and never adds.
    """
    try:
        import providers as _p                                # noqa: WPS433
        return dict(_p._usage("openai-compatible", raw or {}))  # noqa: SLF001
    except Exception:                                         # noqa: BLE001
        raw = raw or {}
        prompt = raw.get("prompt_tokens", raw.get("input_tokens"))
        details = raw.get("prompt_tokens_details") or {}
        read = raw.get("cached_tokens", details.get("cached_tokens")) or 0
        completion = raw.get("completion_tokens", raw.get("output_tokens"))
        return {"prompt_tokens": prompt, "completion_tokens": completion,
                "reasoning_tokens": (raw.get("completion_tokens_details")
                                     or {}).get("reasoning_tokens"),
                "cached_input_tokens": read, "cache_write_tokens": 0,
                "uncached_input_tokens": (None if prompt is None
                                          else max(prompt - read, 0))}


def measured_cost(prov, usage):
    """Dollars for one call, from measured tokens and the config's own price.

    Cached input is billed at the FULL input rate. together.ai charges less
    for it, but `config.json` records the cached rate as deliberately NOT
    claimed: overstating spend under a hard cap is survivable and
    understating it is not.
    """
    if not prov.price_per_mtok:
        return None
    pin, pout = prov.price_per_mtok
    return ((usage.get("prompt_tokens") or 0) / 1e6 * pin
            + (usage.get("completion_tokens") or 0) / 1e6 * pout)


def response_envelope(prov, data):
    """An openai-compatible payload -> the envelope `_append_usage` reads.

    The extra keys ride INSIDE `usage` on purpose: `_append_usage` splats that
    dict into the row and drops everything else, so `cost_usd` and the price
    only reach the ledger from there.
    """
    ch = (data.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
    finish = ch.get("finish_reason")
    usage = normalize_usage(data.get("usage"))
    usage["cost_usd"] = measured_cost(prov, usage)
    usage["price_per_mtok"] = prov.price_per_mtok
    #: `spend.py:prices()` builds its table from providers.json alone, and
    #: this provider is defined inline in the walkthrough config, so
    #: `cost_of()` returns None for this row and `total()` skips it. The row
    #: therefore carries the arithmetic itself, and `spend_invisibility_
    #: warning()` says out loud how much the ledger will not add up.
    usage["priced_by"] = "walkthrough/paper_pipeline/phase_1/config.json"
    return {"text": msg.get("content") or "", "finish_reason": finish,
            "reasoning": reasoning, "usage": usage,
            "provider": prov.name, "model": prov.model,
            "truncated": str(finish or "").lower() in
                         ("length", "max_tokens", "max_output_tokens")}


def spend_invisibility_warning(prov, total_usd, calls):
    """What this run cost that `spend.py` will not add to its total.

    Fixing this properly means a row in `semi-formal-experiment/providers.json`
    or a price lookup in `spend.py` — both outside walkthrough/, both owned by
    the wider repo. Until one of them happens the honest move is to shout the
    number rather than let a silent undercount accumulate under a hard cap.
    """
    pin, pout = (prov.price_per_mtok or [None, None])
    return (
        "\n" + "!" * 72 + "\n"
        f"!! SPEND NOT VISIBLE TO spend.py: ${total_usd:.4f} over {calls} "
        f"call(s).\n"
        f"!! The rows ARE in usage.jsonl, with real token counts and a "
        f"cost_usd field.\n"
        f"!! But spend.py:prices() builds its price table from "
        f"providers.json only,\n"
        f"!! and {prov.name}/{prov.model} is defined inline in this "
        f"harness's config.\n"
        f"!! cost_of() returns None for these rows, so total() SKIPS them "
        f"and the\n"
        f"!! hard cap is that much closer than it reports.\n"
        f"!! To close it, add to semi-formal-experiment/providers.json:\n"
        f'!!     {{"name": "{prov.name}", "kind": "{prov.kind}", '
        f'"model": "{prov.model}",\n'
        f'!!      "base_url": "{prov.base_url}", "api_key_env": '
        f'"{prov.api_key_env}",\n'
        f'!!      "price_per_mtok": [{pin}, {pout}]}}\n'
        + "!" * 72)


def _check_envelope(env):
    """Truncation and emptiness are refusals, not degraded results.

    ⚠️ The truncation guard keys off `finish_reason`, and together.ai returns
    it as null on this model — verified across three live calls, see the
    `finish_reason: null` rows in usage.jsonl. So the guard CANNOT fire here.
    A cut-off completion instead surfaces one stage later, as a JSON parse
    error out of `parse_module`: still loud, still a refusal, but reported as
    "the provider ignored response_format" when the real cause was length.
    The self-test pins the null case so this stays recorded rather than
    rediscovered.
    """
    finish = (env.get("finish_reason") or "").lower()
    if finish in ("length", "max_tokens"):
        raise ProviderError(
            "completion was TRUNCATED (finish_reason=length). A cut-off module "
            "can be syntactically fine and semantically half a clause. Raise "
            "--max-tokens rather than keeping this.")
    text = env.get("text")
    if text is None or not str(text).strip():
        raise ProviderError("empty response")
    u = env.get("usage") or {}
    return {"text": text,
            "in": u.get("prompt_tokens") or u.get("input_tokens") or 0,
            "out": u.get("completion_tokens") or u.get("output_tokens") or 0}


def make_client(prov, cfg):
    return Client(prov, cfg)


# ==========================================================================
# 7.  Cost gate — worst case, before anything is sent
# ==========================================================================

#: Characters allowed for ONE repair turn's user block — the error log
#: `render_error_log` produces, which `repair_loop` appends to the transcript
#: and every later attempt re-sends.
#:
#: ⛔ THIS DIMENSION WAS INVISIBLE. `estimate_cost` priced the prior completions
#: and the `system + user` block; the repair-turn USER blocks appeared in
#: neither the estimate nor `test_cost_and_summary._hand_priced_worst_case`, so
#: the test could not see whether they were covered — a review can only check
#: an estimate against what its floor knows about. Naming the budget makes the
#: coverage a CHECKED relation (`_check_repair_log_budget` below) instead of
#: unmeasured slack.
#:
#: `[RAN] 2026-08-07`, over every `surviving_findings` list in `runs/*/run.json`:
#: the largest error log's findings total **1,062 characters** (m0036, 8
#: findings). 8,000 is ~7.5× that, and still two orders of magnitude below the
#: surplus that has to absorb it.
REPAIR_LOG_CHAR_BUDGET = 8_000


def _check_repair_log_budget(system, users, cpt):
    """The deliberate `(system+user)` over-charge must cover the error logs.

    ⭐ The coverage is exact and provable, which is why it is asserted rather
    than assumed. Writing T for `max_attempts`:

        true worst = T·(sys+user) + max_tokens·T(T-1)/2 + errlog·T(T-1)/2
        estimate   = T(T+1)/2·(sys+user) + max_tokens·T(T-1)/2

    so the estimate's surplus over the true worst case is exactly
    `T(T-1)/2 · (sys+user)` — the SAME coefficient the error-log term carries.
    The estimate therefore covers the error logs for every T iff
    `errlog <= sys + user`. That is a one-line condition, so check it.
    """
    for u in users:
        room = (len(system) + len(u)) / cpt
        need = REPAIR_LOG_CHAR_BUDGET / cpt
        if need > room:
            raise CostGateError(
                f"the repair-turn error log is budgeted at "
                f"{REPAIR_LOG_CHAR_BUDGET} chars but the surplus that absorbs "
                f"it is only {len(system) + len(u)} chars of system+user. The "
                f"estimate would be BELOW the true worst case — the one "
                f"direction it is not allowed to be. Price the error log "
                f"explicitly rather than raising this budget.")


def estimate_cost(system, users, prov, cfg, max_attempts=1):
    cpt = float(cfg["cost"]["chars_per_token"])
    # With repair, one clause is up to `max_attempts` calls, and each carries
    # the transcript so far — so input grows too. Triangular in the attempt
    # count, not linear. Over-estimating is survivable; under-estimating is how
    # a hard cap gets passed.
    #
    # ⛔ THE TRANSCRIPT CONTAINS THE PRIOR COMPLETIONS, AND THEY WERE NOT
    # BILLED. The prose above and `config.json`'s comment both said this
    # estimate was conservative "because each repair turn resends the
    # transcript" — while pricing only `system + user`. Attempt k also resends
    # every earlier completion, worth up to `max_tokens` each (16,384: about
    # 12× the user block). At the shipped `max_attempts: 3` the printed worst
    # case was 12.7 % BELOW the true worst case; at 5, 21.4 % below. That is
    # the one direction the design says must never be wrong, on a project with
    # a hard ledger cap.
    #
    # Worst case, attempt k: `system + user + (k-1) * max_tokens`. Summed over
    # k = 1..T that is `T*(system+user) + max_tokens*T*(T-1)/2`.
    #
    # ⚠️ The `system + user` block is kept at the OLD triangular T(T+1)/2
    # rather than the exact T. It over-charges — the loop resends an error log,
    # not the full user block — and that is deliberate: an estimate is allowed
    # to be high and is not allowed to be low. Do NOT net the two errors off
    # against each other; that is how the anti-conservative half got in.
    #
    # ⚠️ And the repair turns' own USER blocks — the error logs — are carried by
    # that same surplus rather than by a term of their own. That is a claim
    # about magnitudes, so it is CHECKED, not asserted in a comment: see
    # `_check_repair_log_budget`, which is where the third term of the true
    # worst case is written down.
    turns = max(1, int(max_attempts))
    if turns > 1:
        _check_repair_log_budget(system, users, cpt)
    growth = turns * (turns + 1) / 2
    resent = turns * (turns - 1) / 2          # completions carried forward
    in_tok = (sum((len(system) + len(u)) / cpt for u in users) * growth
              + prov.max_tokens * len(users) * resent)
    out_tok = prov.max_tokens * len(users) * turns
    if not prov.price_per_mtok:
        raise CostGateError(
            f"provider {prov.name} has no price_per_mtok. An unpriced provider "
            f"counts as OVER budget, never as free.")
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (out_tok / 1e6) * pout, int(in_tok), int(out_tok)


def cost_gate(est, cfg):
    cap = float(cfg["cost"]["max_cost_usd"])
    if est > cap:
        raise CostGateError(
            f"estimated ${est:.4f} exceeds the ceiling ${cap:.2f}. Nothing sent. "
            f"Narrow the selection or raise cost.max_cost_usd deliberately.")


# ==========================================================================
# 8.  Response handling — write the raw bytes BEFORE parsing anything
# ==========================================================================

_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.S)
#: ⛔ NOT `_FENCE`. That one tolerates a BARE fence on purpose, because some
#: providers wrap a JSON response without annotating it — correct for reading a
#: RESPONSE, wrong for reading a PROMPT FILE, which legitimately contains other
#: languages. The self-test below reused `_FENCE` on `20_worked_example.md`, so
#: adding one bare-fenced ASP block made `json.loads` raise before a single
#: check ran: `--self-test` died outright while `pytest` stayed green, because
#: the self-test is not in the suite. Two jobs, two patterns.
_JSON_FENCE = re.compile(r"```json\s*\n(.*?)```", re.S)


def parse_module(text, clause_id=None, known_clause_ids=None):
    """Text -> the validated module object. Raises on anything else.

    A fenced block is tolerated on the way in (some providers wrap JSON even
    under forcing) but nothing else is guessed at: if it does not parse as an
    object, that is a refusal, not a degraded result.

    `clause_id` and `known_clause_ids` are passed straight to
    `schema.validate`, and `run()` always supplies both. They are what
    enforces "the module did not rename itself" and "it did not cite a clause
    that does not exist" — a run that omits them loses both guarantees with
    no visible difference in its output.
    """
    raw = text.strip()
    if raw.startswith("```"):
        hit = _FENCE.search(raw)
        if hit:
            raw = hit.group(1).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResponseParseError(
            f"response is not JSON ({exc}). Under format forcing this should "
            f"be impossible — suspect the provider ignored response_format, "
            f"or that the completion was cut off (this provider returns "
            f"finish_reason: null, so the truncation guard cannot fire)") \
            from exc
    try:
        return schema.validate(obj, clause_id=clause_id,
                               known_clause_ids=known_clause_ids)
    except schema.ModuleValidationError as exc:
        raise ResponseParseError(str(exc)) from exc


# ==========================================================================
# 8b.  The run directory — a complete transcript, and never a second run's
# ==========================================================================

def resolve_outdir(cfg, prov):
    """The directory this run writes to. It must not already hold a run.

    `output.run_name` plus `makedirs(exist_ok=True)` wrote a second run's
    artifacts over the first. The raw responses of a run that cost money are
    the one thing in this pipeline that cannot be regenerated, so a collision
    is a refusal — not a warning, and not a silent merge.
    """
    base = rel(cfg["output"]["dir"])
    name = cfg["output"].get("run_name")
    if name:
        outdir = os.path.join(base, name)
        if os.path.isdir(outdir) and os.listdir(outdir):
            raise ConfigError(
                f"output directory {outdir} already holds "
                f"{len(os.listdir(outdir))} file(s) from an earlier run. "
                f"Raw responses that were paid for are not regenerable, so "
                f"this refuses rather than overwriting. Clear "
                f"output.run_name to get a timestamped directory, or move "
                f"the old run aside")
        return outdir
    stamp = time.strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(base, f"{stamp}-{prov.name}")
    n = 2
    while os.path.isdir(outdir) and os.listdir(outdir):
        outdir = os.path.join(base, f"{stamp}-{prov.name}-{n}")
        n += 1
    return outdir


def response_format_payload(cfg):
    """Exactly what goes in the request's `response_format`, or None."""
    mode = validate_format_forcing(cfg)
    if mode == "json_schema":
        return schema.response_format(cfg["model"].get("json_schema_strict",
                                                       True))
    if mode == "json_object":
        return {"type": "json_object"}
    return None


def stale_filter(jobs, cfg, args, prov, system, idk, text_key):
    """`--only-stale`: keep only the jobs whose stored artifact has moved.

    ⛔ IT REPORTS BEFORE IT DECIDES. The census is printed here, above the cost
    estimate and the gate, because the failure this feature could produce is a
    staleness tool that quietly re-runs 593 clauses. The counts, by class, with
    their denominator, are on screen before anything is priced.

    Returns (jobs, report) — `report` is what goes into `run.json`.
    """
    # ⚠️ VALIDATED FIRST, before any work and before any output. A malformed
    # waiver file is a refusal, and a refusal that arrives underneath a census
    # reads as a comment on the census.
    waivers = load_waivers_for(args)

    runs_root = rel(cfg["output"]["dir"])
    model, temperature, params = version.model_params(cfg, prov)
    schema_src = version.schema_source()
    current = {}
    for j in jobs:
        current[j["row"][idk]] = version.stamp(
            j["row"].get(text_key, ""), schema_src, system, model,
            temperature, params)

    rows = version.survey(runs_root, current)
    # A clause with no artifact anywhere has never been translated: it is not
    # "current", and it is not a stale artifact either — it is work.
    best = version.best_per_clause(rows)
    states = {}
    for j in jobs:
        cid = j["row"][idk]
        states[cid] = best.get(cid) or {
            "run": None, "clause_id": cid, "state": version.UNSTAMPED,
            "differing": ["contract_hash", "provenance_hash"],
            "stored": None, "current": current[cid]}

    counts = version.census(list(states.values()))
    print(version.format_census(counts, total=len(jobs), label="selected"))

    waived, honoured, unused = version.apply_waivers(states, waivers)
    if waivers:
        print(version.format_waivers(honoured, unused))

    keep = [j for j in jobs
            if states[j["row"][idk]]["state"] in version.STALE
            and j["row"][idk] not in waived]
    print(f"only-stale  : translating {len(keep)} of {len(jobs)} selected "
          f"clause(s); {len(jobs) - len(keep)} left as they are")
    report = {
        "enabled": True,
        "census": counts,
        "waivers_file": getattr(args, "waivers", None),
        "selected": sorted(j["row"][idk] for j in keep),
        "skipped": sorted(set(j["row"][idk] for j in jobs)
                          - set(j["row"][idk] for j in keep)),
        "states": {k: v["state"] for k, v in sorted(states.items())},
    }
    return keep, report, honoured


def load_waivers_for(args):
    """⛔ A waiver file is INERT without `--only-stale`.

    Nothing is being skipped in an ordinary run, so a waiver file lying around
    must not quietly change what gets translated. It is read here, inside the
    only-stale path, and nowhere else.
    """
    path = getattr(args, "waivers", None)
    return version.load_waivers(path) if path else []


def run_record(cfg, prov, system, results, user_shas=None, spend=None,
               version_block=None):
    """The contents of run.json.

    ⚠️ It used to record `system_sha_len`: the LENGTH of the system prompt.
    Two different prompts of equal length were indistinguishable, and run.json
    is the only provenance a run carries. It now records real shas of the
    prompt, of the config and of every user block, plus the model id and the
    exact `response_format` sent.
    """
    return {
        "config": cfg,
        "provider": prov.name,
        "model": prov.model,
        "base_url": prov.base_url,
        "config_sha": config_sha(cfg),
        "system_sha": sha16(system),
        "inputs_sha": inputs_fingerprint(cfg),
        "user_sha": dict(user_shas or {}),
        "response_format": response_format_payload(cfg),
        "spend": spend or {},
        # ⭐ The run-level half of the version stamp. The per-clause half is on
        # each result and in the `<id>.version.json` sidecar; this says what
        # every clause in the run shared — which prompt, which model, which
        # schema source — so a run can be compared to today's inputs without
        # opening a single module.
        **(version_block or {}),
        "results": results,
    }


# ==========================================================================
# 9.  Run
# ==========================================================================

def run(cfg, args, client_factory=None):
    """Dry-run or live. `client_factory` exists so the self-test can drive a
    complete run — directory layout, transcript, run.json, exit code — with a
    stub transport and no key, no network and no spend."""
    rows = load_corpus(cfg)
    known_ids = {r[cfg["corpus"]["id_key"]] for r in rows}
    picked = select(rows, cfg, args)
    system = build_system(cfg)
    # Before the cost gate and before the loop: a bad `format_forcing` is a
    # config error and exit 2, not N clause failures and exit 1.
    validate_format_forcing(cfg)
    jobs = []
    for r in picked:
        user, found, unres = build_user(r, rows, cfg)
        jobs.append({"row": r, "user": user,
                     "xrefs": [x[cfg["corpus"]["id_key"]] for x in found],
                     "xrefs_unresolved": unres})

    prov = resolve_provider(cfg, args)
    _max_attempts = int((cfg.get("repair") or {}).get("max_attempts", 1))
    idk = cfg["corpus"]["id_key"]

    # ⛔ BEFORE THE ESTIMATE, NOT INSIDE THE LOOP. Filtering while pricing the
    # whole selection leaves the printed worst case describing calls that were
    # never going to be made, and — worse — leaves the cost GATE refusing runs
    # over clauses nobody was going to send.
    _version_report, _honoured = None, []
    if getattr(args, "only_stale", False):
        jobs, _version_report, _honoured = stale_filter(
            jobs, cfg, args, prov, system, idk, cfg["corpus"]["text_key"])
        if not jobs:
            print("nothing is stale — nothing to translate, nothing sent.")
            return 0

    est, in_tok, out_tok = estimate_cost(
        system, [j["user"] for j in jobs], prov, cfg,
        max_attempts=_max_attempts)

    print(f"provider     : {prov.name}  ({prov.model})")
    print(f"clauses      : {len(jobs)}  "
          f"[{', '.join(j['row'][idk] for j in jobs[:8])}"
          f"{' …' if len(jobs) > 8 else ''}]")
    print(f"system prompt: {len(system):,} chars from "
          f"{len(cfg['prompt']['system_files'])} file(s) — identical every call")
    print(f"cost (worst) : ${est:.4f}   "
          f"(~{in_tok:,} in, {out_tok:,} out at full max_tokens)   "
          f"ceiling ${float(cfg['cost']['max_cost_usd']):.2f}")
    for j in jobs:
        note = f"{len(j['xrefs'])} xref(s)" if j["xrefs"] else "no anchors"
        if j["xrefs_unresolved"]:
            note += f", ⚠️ unresolved: {', '.join(j['xrefs_unresolved'])}"
        print(f"  {j['row'][idk]:>6}  {j['row'].get(cfg['corpus']['kind_key'],''):<12} {note}")

    if args.show_prompt:
        print("\n" + "=" * 72 + "\nSYSTEM\n" + "=" * 72)
        print(system)
        for j in jobs[: args.show_prompt]:
            print("\n" + "=" * 72 + f"\nUSER — {j['row'][idk]}\n" + "=" * 72)
            print(j["user"])

    if not args.live:
        print("\nDRY RUN — nothing was sent. Add --live to spend.")
        return 0

    cost_gate(est, cfg)

    # The client is built BEFORE the directory. `_resolve_key` raising used to
    # leave an empty run directory behind for every attempt that had no key.
    client = (client_factory or make_client)(prov, cfg)

    outdir = resolve_outdir(cfg, prov)
    os.makedirs(outdir)
    print(f"\nwriting to {outdir}")

    # WHAT WAS SENT, written before anything comes back. A run directory that
    # holds only the responses is half a transcript: dryrun.txt is a separate
    # artifact for the default selection, so without these nobody can read a
    # run and see what was actually asked. The system block is identical for
    # every clause in the run, so it is written once.
    with open(os.path.join(outdir, "prompt_system.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(system)

    _gy = cfg.get("graveyard") or {}
    _gy_dir = rel(_gy.get("dir", "repair_graveyard"))
    # ⭐ ONE definition of what this run was made from, used by the graveyard
    # entry, by every module's stamp and by run.json. Computed once so the
    # three cannot drift: a sidecar that disagreed with run.json would make
    # the staleness query answer differently depending on which it read.
    _schema_src = version.schema_source()
    _model, _temp, _params = version.model_params(cfg, prov)
    _prov_hash = gy.provenance_hash(system, _model, _temp, params=_params)
    _version_block = {
        "schema_sha": sha16(_schema_src),
        "provenance_hash": _prov_hash,
        "provenance_params": _params,
        "stamp_version": 1,
        "waivers_honoured": _honoured,
        "only_stale": _version_report,
    }
    if _gy.get("cap"):
        # Refuse to start a run that would only deepen an unexamined pile.
        gy.check_cap(_gy_dir, _gy["cap"])

    results, failures, user_shas, _concepts = [], 0, {}, []

    def flush():
        """run.json AND the concept table, after every clause and on the way out.

        It used to be written only after the loop finished, so any mid-loop
        exception — a keyboard interrupt, a network drop — lost the record of
        every clause already paid for.

        ⚠️ The concept table is written HERE, not at the end. An earlier
        attempt inserted the write at a `run.json` call site that no longer
        existed; the string did not match, the patch silently did nothing, and
        the run produced no table while a self-test check that compared a
        constant to itself reported success.
        """
        with open(os.path.join(outdir, CONCEPT_TABLE), "w",
                  encoding="utf-8") as fh:
            json.dump(_concepts, fh, indent=1)
        with open(os.path.join(outdir, "run.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(run_record(
                cfg, prov, system, results, user_shas,
                {"usd": round(getattr(client, "spent_usd", 0.0), 6),
                 "calls": getattr(client, "calls", 0),
                 "visible_to_spend_py": False,
                 "why": "spend.py prices from providers.json; this provider "
                        "is defined inline in this config"},
                version_block=_version_block),
                fh, indent=1)

    try:
        for j in jobs:
            cid = j["row"][idk]
            rec = {"clause_id": cid, "provider": prov.name,
                   "model": prov.model, "xrefs": j["xrefs"],
                   "xrefs_unresolved": j["xrefs_unresolved"]}
            # The user block is written BEFORE the call, so a clause that
            # fails — exactly when someone needs to see what was sent — still
            # has its half of the transcript on disk.
            with open(os.path.join(outdir, f"{cid}.prompt_user.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(j["user"])
            user_shas[cid] = sha16(j["user"])
            rec["user_sha"] = user_shas[cid]
            _stamp = version.stamp(
                j["row"].get(cfg["corpus"]["text_key"], ""), _schema_src,
                system, _model, _temp, _params)

            try:
                env = client.complete(system, j["user"])
            except Phase1Error as exc:
                rec.update(status="error", error=f"{type(exc).__name__}: {exc}")
                print(f"  ⛔ {cid}: {rec['error']}")
                failures += 1
                results.append(rec)
                flush()
                continue

            # raw first, always — a parse failure must never lose what was
            # paid for
            with open(os.path.join(outdir, f"{cid}.raw.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(env["text"])
            rec.update(tokens_in=env["in"], tokens_out=env["out"],
                       cost_usd=round(env.get("cost_usd") or 0.0, 6))

            # ⭐ STAGE 2 IS THE GATE, ALWAYS — not an exception handler.
            # It used to run only when `parse_module` RAISED, so a module that
            # satisfied the schema was written without ever being compiled,
            # link-checked, rule-shape checked or cycle checked. Two clauses
            # were reported translated having never been near the solver.
            # `repair_loop` runs stage 2 on every attempt including the first,
            # so calling it unconditionally is both the gate and the loop.
            try:
                out = repair_loop(env["text"], clause=j["row"], model=client,
                                  max_attempts=_max_attempts,
                                  corpus_ids=known_ids, system=system,
                                  first_user=j["user"])
            except Phase1Error as exc:
                # A provider error during REPAIR used to escape the per-clause
                # handler and abort the whole run, writing a run.json with zero
                # results for clauses already billed.
                rec.update(status="error", error=f"{type(exc).__name__}: {exc}")
                print(f"  ⛔ {cid}: {rec['error']}")
                failures += 1
                results.append(rec)
                flush()
                continue

            keep, why = gy.should_keep(
                out, _max_attempts, _gy.get("rates") or {},
                clause_id=cid, seed=int(_gy.get("seed", 0)))
            if keep:
                entry = gy.write_entry(
                    _gy_dir, j["row"], out, reason=why,
                    contract_hash=_stamp["contract_hash"],
                    provenance_hash=_stamp["provenance_hash"],
                    extra={"run": os.path.basename(outdir)})
                rec["graveyard"] = os.path.basename(entry)

            rec.update(attempts=out.attempts, per_attempt=out.per_attempt,
                       flags=out.flags, n_findings=len(out.findings),
                       unclear_closure_rate=out.unclear_closure_rate)
            with open(os.path.join(outdir, f"{cid}.transcript.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(out.transcript, fh, indent=1)

            # ⛔ `out.module is not None` is NOT success. A module whose
            # surviving breach is a corpus or link rule still CONSTRUCTS, so
            # testing for None recorded exhaustion as a pass — and the module's
            # own `outcome` field then overwrote the loop's status.
            if out.status not in ("translated", "abstained",
                                  "abstained_under_repair"):
                rec.update(status=out.status,
                           surviving_findings=[
                               f"[{f.check_id}] {f.where}: {f.message}"
                               for f in out.findings])
                print(f"  ⛔ {cid}: {out.status} after {out.attempts} "
                      f"attempt(s), {len(out.findings)} finding(s) standing")
                failures += 1
                results.append(rec)
                flush()
                continue
            obj = out.module
            if out.attempts > 1:
                print(f"  ↻ {cid}: {out.status} on attempt {out.attempts}"
                      + (f"  ⚠️ {', '.join(out.flags)}" if out.flags else ""))

            # the object is the record; the .lp is a rendering of it
            with open(os.path.join(outdir, f"{cid}.json"), "w",
                      encoding="utf-8") as fh:
                fh.write(obj.model_dump_json(indent=1))
            lp = schema.render_lp(obj, j["row"])
            with open(os.path.join(outdir, f"{cid}.lp"), "w",
                      encoding="utf-8") as fh:
                # ⚠️ A `%` COMMENT, appended — not a `%%` header line. `%%` is
                # the module interface and `link.py` parses it; a version
                # there would be a header field nothing declares. The record
                # is the sidecar written below; this line is for a human
                # reading the rendering on its own.
                fh.write(lp + version.lp_comment(_stamp) + "\n")
            # ⭐ THE ARTIFACT CARRIES ITS OWN PROVENANCE. Only on the success
            # path: a stamp beside a clause that failed would make the next
            # `--only-stale` run skip a clause that was never translated.
            version.write_stamp(outdir, cid, _stamp)
            rec.update(_stamp)
            _concepts.extend(schema.concept_rows(obj))

            lic = {}
            for item in (*obj.ontology, *obj.asserts, *obj.beats, *obj.defines):
                lic[item.licence] = lic.get(item.licence, 0) + 1

            rec.update(n_concepts=len(obj.concepts),
                       attempts=rec.get("attempts", 1),
                       # ⛔ The LOOP's status, explicitly. `rec.get("status")`
                       # is empty on this path, so falling back to the module's
                       # own `outcome` silently collapsed
                       # `abstained_under_repair` into `abstained` — losing the
                       # distinction between a real answer and repair pressure.
                       status=out.status,
                       lp_bytes=len(lp),
                       n_claims=len(obj.claims), n_acts=len(obj.acts),
                       n_ontology=len(obj.ontology), n_asserts=len(obj.asserts),
                       n_beats=len(obj.beats), n_defines=len(obj.defines),
                       licences=lic,
                       closure={c.act_class: c.closure for c in obj.closure},
                       acts=list(obj.acts), requires=list(obj.requires),
                       inputs=list(obj.inputs),
                       forbid_body=[f"{f.head} <- {f.banned}"
                                    for f in obj.forbid_body])
            if obj.outcome == "abstained":
                print(f"  ∅ {cid}: abstained — {obj.abstain_reason}")
            else:
                print(f"  ✓ {cid}: {rec['n_asserts']} asserts, "
                      f"{rec['n_beats']} beats, {rec['n_defines']} defines, "
                      f"{rec['n_ontology']} ontology {lic or '{}'}, "
                      f"closure {rec['closure'] or '{}'}, "
                      f"{env['out']:,} out-tokens")
            results.append(rec)
            flush()
    finally:
        flush()

    # ⛔ COUNT `translated` BY NAME, and partition on the WHOLE status set.
    # This used to read `len(results) - failures - n_ab` with `n_ab` matching
    # `status == "abstained"` exactly. `abstained_under_repair` is neither that
    # nor a failure — it is admitted on the success branch above — so it landed
    # in the TRANSLATED count: a clause the model refused after being told
    # twice that it was wrong, printed as a successful translation, in the one
    # line a human reads. The distinction was fixed in `run.json` and NOT in
    # the arithmetic one line below it, because the test that closed it asserts
    # on the stored field and never on this line.
    #
    # ⚠️ Any status this does not name now shows up in `other` and says so,
    # rather than being absorbed into the most flattering bucket. That is the
    # actual lesson: when a status set grows, every place that partitions on it
    # has to grow with it, and a residual is how you find out that it did not.
    n_tr = sum(1 for r in results if r.get("status") == "translated")
    n_ab = sum(1 for r in results if r.get("status") == "abstained")
    n_abr = sum(1 for r in results
                if r.get("status") == "abstained_under_repair")
    print(f"\n{n_tr} translated, {n_ab} abstained, "
          f"{n_abr} abstained under repair, "
          f"{failures} failed. Raw responses kept in {outdir}")
    other = len(results) - n_tr - n_ab - n_abr - failures
    if other:
        print(f"⚠️ {other} of {len(results)} result(s) carry a status this "
              f"summary does not partition on, so the counts above do not add "
              f"up. Statuses seen: "
              f"{sorted({str(r.get('status')) for r in results})}")
    print("⛔ NOTHING here has been validated. No compile, no link, no read-back.")
    spent = getattr(client, "spent_usd", 0.0)
    if spent:
        print(spend_invisibility_warning(prov, spent,
                                         getattr(client, "calls", 0)))
    return 1 if failures else 0


# ==========================================================================
# 10.  Self-test — RED-first, no network, no cost
# ==========================================================================

def self_test():
    """Each check names the condition and the reason it exists to fire on."""
    import contextlib
    import copy
    import io
    import tempfile

    cfg0 = load_config(DEFAULT_CONFIG)
    rows = load_corpus(cfg0)
    ok, bad = 0, 0

    def check(label, reason, fn, want, must_say=None):
        """A check is the TYPE and the MESSAGE, never the type alone.

        ⚠️ Why `must_say` is mandatory. Two checks here — the empty prompt
        file and the missing prompt file — were green for eight days while
        neither branch ever ran: both setups tripped `check_no_orphan_prompts`
        first, which also raises ConfigError. Deleting the guards they were
        written to protect would not have turned either of them red. Comparing
        only the exception type cannot tell a guard from its neighbour.
        """
        nonlocal ok, bad
        if want is not None and not must_say:
            raise AssertionError(
                f"{label}: an expected-exception check must name a substring "
                f"of the message it expects. Type-only checks pass for the "
                f"wrong reason and this suite has been bitten by exactly that")
        try:
            fn()
            got, msg = None, ""
        except Exception as exc:                              # noqa: BLE001
            got, msg = type(exc), str(exc)
        if want is None:
            good, why = got is None, f"expected no exception, got {got}: {msg}"
        elif got is not want:
            good, why = False, f"expected {want.__name__}, got {got}: {msg}"
        else:
            good = must_say.lower() in msg.lower()
            why = (f"raised {want.__name__} but for the WRONG REASON — the "
                   f"message does not contain {must_say!r}: {msg}")
        if good:
            print(f"  ✅ {label}\n       fires on: {reason}")
            ok += 1
        else:
            print(f"  ❌ {label}\n       {why}")
            bad += 1

    def require(label, reason, cond, detail):
        """An assertion that does not abort the remaining checks.

        The trailing block of this suite used bare `assert`s: the first one to
        fail (dryrun.txt being stale) hid every check after it, including the
        wire-schema and rendering checks. A suite that stops at the first
        failure reports one defect and conceals the rest.
        """
        nonlocal ok, bad
        if cond:
            print(f"  ✅ {label}\n       fires on: {reason}")
            ok += 1
        else:
            print(f"  ❌ {label}\n       {detail}")
            bad += 1

    def _ok(fn):
        try:
            fn()
            return True
        except Exception:                                     # noqa: BLE001
            return False

    def _why(fn):
        try:
            fn()
            return "ok"
        except Exception as exc:                              # noqa: BLE001
            return f"{type(exc).__name__}: {exc}"

    class A:                                    # a bare args stand-in
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = False
        show_prompt = 0

    print("phase_1/translate.py --self-test\n")

    check("selection: unknown clause id",
          "a typo must not silently translate a different clause",
          lambda: select(rows, cfg0, type("x", (A,), {"clause": ["m9999"]})()),
          CorpusError, "no such clause id")

    check("selection: unknown section id",
          "a renamed section must not yield an empty run reported as success",
          lambda: select(rows, cfg0, type("x", (A,), {"section": "nope"})()),
          CorpusError, "no clause has section_id")

    def _empty_selection():
        c = copy.deepcopy(cfg0)
        c["select"] = {"clause_ids": [], "section_id": None, "kinds": []}
        select(rows, c, A())
    check("selection: nothing selected",
          "'translate everything' must not happen by accident",
          _empty_selection, CorpusError, "selection is empty")

    check("selection: a real one resolves",
          "the happy path stays green",
          lambda: select(rows, cfg0, type("x", (A,), {"clause": ["m0255"]})()),
          None)

    check("selection: --limit 0 is a refusal, not 'everything'",
          "`if s.get('limit')` made 0 falsy, so --limit 0 silently selected "
          "the whole selection — the opposite of what it says",
          lambda: select(rows, cfg0, type("x", (A,), {"limit": 0})()),
          CorpusError, "limit")

    # ---- prompt assembly -------------------------------------------------
    # Each of these three must reach ITS OWN branch. They are built inside a
    # private directory precisely so the orphan scan (which now derives the
    # directories it scans from the file list) finds nothing else there.

    def _tmp_prompt_dir(files):
        """A config whose prompt files live in a fresh directory of their own."""
        d = tempfile.mkdtemp(prefix="phase1_prompt_")
        c = copy.deepcopy(cfg0)
        for name, body in files.items():
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        c["prompt"]["system_files"] = [os.path.join(d, n) for n in files]
        c["prompt"]["unused_files"] = []
        return c, d

    def _empty_prompt_file():
        c, _ = _tmp_prompt_dir({"00_rules.md": "   \n"})
        build_system(c)
    check("prompt: an empty rules file",
          "an empty instruction file sends a promptless call that looks normal",
          _empty_prompt_file, ConfigError, "prompt file is empty")

    def _missing_prompt_file():
        c, d = _tmp_prompt_dir({"00_rules.md": "real content"})
        c["prompt"]["system_files"] = [os.path.join(d, "does_not_exist.md")]
        c["prompt"]["unused_files"] = [os.path.join(d, "00_rules.md")]
        build_system(c)
    check("prompt: a missing rules file",
          "a renamed prompt file must not silently shrink the instructions",
          _missing_prompt_file, ConfigError, "prompt file not found")

    def _orphan():
        c = copy.deepcopy(cfg0)
        c["prompt"]["system_files"] = ["prompt/00_task.md"]
        c["prompt"]["unused_files"] = []
        build_system(c)
    check("prompt: a file on disk that is never sent",
          "30_failure_modes.md was written and left unwired — the model never "
          "saw the 17 failure modes while the README said it did",
          _orphan, ConfigError, "never sent")

    def _no_prompt_dir():
        c = copy.deepcopy(cfg0)
        c["prompt"]["system_files"] = ["nowhere/00_task.md"]
        c["prompt"]["unused_files"] = []
        build_system(c)
    check("prompt: a config whose prompt directory does not exist",
          "the orphan scan used to listdir phase_1/prompt whatever the config "
          "said, so --config elsewhere was impossible and a wrong path came "
          "back as a bare FileNotFoundError traceback, not exit 2",
          _no_prompt_dir, ConfigError, "prompt directory not found")

    # ---- provider envelope ----------------------------------------------

    check("truncation is a refusal",
          "a cut-off module can be syntactically fine and half a clause",
          lambda: _check_envelope({"text": "x", "finish_reason": "length"}),
          ProviderError, "TRUNCATED")

    check("empty response is a refusal",
          "an empty completion must not be written out as a module",
          lambda: _check_envelope({"text": "  ", "finish_reason": "stop"}),
          ProviderError, "empty response")

    check("a null finish_reason is NOT treated as truncation",
          "this provider returns finish_reason: null on every call, so the "
          "truncation guard cannot fire here at all — a cut-off completion "
          "surfaces one stage later as a JSON parse error. Loud, but "
          "misdiagnosed, and that is recorded rather than papered over",
          lambda: _check_envelope({"text": "{}", "finish_reason": None}), None)

    check("a non-JSON response is a refusal",
          "under forcing this is impossible; if it happens the provider "
          "ignored response_format and nothing downstream can be trusted",
          lambda: parse_module("here is your module, roughly: policy(a)."),
          ResponseParseError, "not JSON")

    # ---- the module contract --------------------------------------------
    # The fixture is built from the REAL classes in schema.py. A hand-written
    # dict drifts silently: the previous one still named `rules`/`facts`/
    # `provides` after the schema was rewritten around `asserts`/`ontology`/
    # `closure`, and every negative check below went green on
    # "Extra inputs are not permitted" instead of the rule it names.

    # The fixture is the m0255 module out of `prompt/20_worked_example.md` —
    # the very example the model is shown. A hand-written dict drifts silently:
    # the previous one still named `rules`/`facts`/`provides` after the schema
    # was rewritten around `asserts`/`ontology`/`closure`, and every negative
    # check below went green on "Extra inputs are not permitted" instead of the
    # rule it names. Reading it out of the prompt also checks something that
    # was never checked: that the shape we TEACH is a shape the contract
    # ACCEPTS. If those two ever part company, the model is being instructed
    # to produce output the harness will reject on every clause.

    _ex_path = rel("prompt/20_worked_example.md")
    # ⛔ FILTER, THEN PARSE. This used to `json.loads` every fenced block and
    # filter afterwards, so ONE illustrative fragment killed the whole
    # self-test before a single check ran — the same shape as the bare-fence
    # bug this line already had once. A partial fragment legitimately uses a
    # `...` placeholder to mean "and the rest of the fields"; it is not a
    # module and is not this check's business.
    #
    # ⚠️ `test_prompt_examples.py` scans the same file and STRIPS `...` before
    # parsing, so the two extractors disagreed and only this one broke. Kept
    # deliberately different: that test asserts every fragment is well-formed,
    # this one only cares about whole modules.
    _ex_blocks = []
    for _b in _JSON_FENCE.findall(open(_ex_path, encoding="utf-8").read()):
        try:
            _ex_blocks.append(json.loads(_b))
        except json.JSONDecodeError:
            continue                      # a fragment, not a module
    _ex_modules = [b for b in _ex_blocks if isinstance(b, dict)
                   and "outcome" in b]
    require(f"the worked example we SHOW the model validates "
            f"({len(_ex_modules)} module(s) in 20_worked_example.md)",
            "a prompt that teaches a shape the contract rejects fails every "
            "clause, and nothing in the harness compared the two",
            len(_ex_modules) >= 2
            and all(_ok(lambda b=b: schema.validate(b)) for b in _ex_modules),
            f"{_ex_path} carries {len(_ex_modules)} full module(s); "
            + "; ".join(_why(lambda b=b: schema.validate(b))
                        for b in _ex_modules))

    GOOD = next((b for b in _ex_modules
                 if b.get("asserts") and b.get("ontology")), _ex_modules[0])

    def mut(**kw):
        import copy as _c
        o = _c.deepcopy(GOOD)
        o.update(kw)
        return o

    def onto(**kw):
        """The example's own first ontology fact, with one field bent.

        ⚠️ Bends the first entry and KEEPS the rest. Truncating the list to one
        made the module fail a different check — a `beats` body referencing an
        ontology predicate that had just been deleted — so the positive control
        ("a licensed world fact is ACCEPTED") failed for an unrelated reason.
        That is the wrong-reason failure this file's `check()` exists to catch,
        occurring in a fixture rather than in a check.
        """
        rest = [dict(f) for f in GOOD["ontology"][1:]]
        base = dict(GOOD["ontology"][0])
        base.update(kw)
        return mut(ontology=[base] + rest)

    def asrt(**kw):
        """The example's own first assertion, with one field bent."""
        a = dict(GOOD["asserts"][0])
        a.update(kw)
        return mut(asserts=[a])

    check("a valid module passes",
          "the happy path stays green",
          lambda: parse_module(json.dumps(GOOD)), None)

    check("licence `textual` with no citation",
          "an uncited textual fact is an invention wearing a citation's clothes",
          lambda: parse_module(json.dumps(
              onto(licence="textual", cites=None, inference=None))),
          ResponseParseError, "licence `textual` with no citation")

    check("licence `assumed` with no named inference",
          "an unnamed inference is an unmarked invention (Invariant 2)",
          lambda: parse_module(json.dumps(
              onto(licence="assumed", cites=None, inference=""))),
          ResponseParseError, "licence `assumed` with no named inference")

    check("licence `world` that is not toggleable",
          "a result resting on world knowledge is a different claim and must "
          "be switchable off",
          lambda: parse_module(json.dumps(
              onto(licence="world", cites=None, toggleable=False))),
          ResponseParseError, "not toggleable")

    check("a licensed `world` fact is ACCEPTED",
          "the graded licence exists so non-textual facts are marked, NOT "
          "banned — rejecting this would re-create the binary rule the design "
          "already recorded as wrong",
          lambda: parse_module(json.dumps(
              onto(atom="protects_third_party(rc)", licence="world",
                   cites=None, toggleable=True))),
          None)

    check("a predicate declared without arity",
          "forbids/2 and forbids/3 must be distinguishable at link time",
          lambda: parse_module(json.dumps(mut(requires=["material"]))),
          ResponseParseError, "name/arity")

    check("a citation to a clause outside the corpus",
          "a manufactured citation creates an invented entity BEHIND a passed "
          "check — the schema alone cannot see it, so run() now hands "
          "validate() the corpus ids",
          lambda: parse_module(json.dumps(GOOD), clause_id="m0255",
                               known_clause_ids={"m0001"}),
          ResponseParseError, "not a clause in this corpus")

    check("a module that renames itself",
          "a module whose clause_id is not the clause it was asked for would "
          "be written to <asked>.json carrying a second identity",
          lambda: parse_module(json.dumps(GOOD), clause_id="m0091",
                               known_clause_ids=None),
          ResponseParseError, "two identities")

    # ⛔ REMOVED 2026-08-07: "an anonymous variable in a rule body" is rejected.
    # It asserted that `_` raises, on the ground that "the explanation tool
    # cannot process it". That ground is now disproved twice -- `[RAN]` clingo
    # accepts `p(X) :- q(X,_).` and derives correctly, and the published
    # ASP2CNL renderer handles `_` explicitly ("hidden terms are simply
    # skipped"). The schema restriction was removed on that evidence; this
    # check pinned the restriction, so it went with it.
    #
    # ⚠️ The self-test caught its own staleness: after the schema change it
    # failed with "raised ResponseParseError but for the WRONG REASON" -- the
    # module now fails an undeclared-name check instead. A check that pins a
    # deliberately-removed rule is not a floor; deleting it is not lowering one.

    check("a rule with no read-back annotation",
          "the read-back is what a reviewer sees INSTEAD of the rule; without "
          "it the rule cannot be checked against the clause at all",
          lambda: parse_module(json.dumps(
              asrt(read_back="  ", read_back_slots=[]))),
          ResponseParseError, "no read-back annotation")

    check("read-back slots that do not match their arguments",
          "the rendered sentence would silently be wrong",
          lambda: parse_module(json.dumps(
              asrt(read_back="producing % is forbidden because %"))),
          ResponseParseError, "slot(s) but")

    check("an act asserted but never declared",
          "the FORCED closure declaration is checked against `acts`; an "
          "undeclared act escapes it",
          lambda: parse_module(json.dumps(asrt(act="interject(user)"))),
          ResponseParseError, "not in `acts`")

    check("an act class with no closure declaration",
          "an absent declaration reads as CEPA silently, and the probe found "
          "that flips the contradiction verdict while open and cepa stay "
          "bit-identical",
          lambda: parse_module(json.dumps(mut(closure=[]))),
          ResponseParseError, "no default-closure declaration")

    check("abstention with no reason",
          "an abstention with no reason is a skip in disguise, and the "
          "abstention RATE is a signal we read",
          lambda: parse_module(json.dumps(mut(
              outcome="abstained", abstain_reason=" "))),
          ResponseParseError, "abstained with no reason")

    check("abstention that still carries content",
          "neither an abstention nor a translation",
          lambda: parse_module(json.dumps(mut(
              outcome="abstained", abstain_reason="it is a heading"))),
          ResponseParseError, "is non-empty")

    check("a translation that emitted nothing",
          "an abstention that did not say so",
          lambda: parse_module(json.dumps(mut(
              asserts=[], concepts=[], ontology=[], defines=[], beats=[]))),
          ResponseParseError, "abstention that did not say so")

    check("a translation with no claims",
          "a clause with four claims tested against one case is mode 12, and "
          "`claims` is how that becomes visible",
          lambda: parse_module(json.dumps(mut(claims=[]))),
          ResponseParseError, "no `claims`")

    # ---- cost, provider selection, output directory ----------------------

    def _unpriced():
        p = Provider("x", "openai-compatible", "m", "u", "K", 0.2, 100, None)
        estimate_cost("s", ["u"], p, cfg0)
    check("an unpriced provider is over budget",
          "unpriced must never be treated as free",
          _unpriced, CostGateError, "no price_per_mtok")

    def _over_gate():
        c = copy.deepcopy(cfg0)
        c["cost"]["max_cost_usd"] = 1e-9
        cost_gate(0.01, c)
    check("cost gate refuses before sending",
          "the ceiling must bind before the first call, not after",
          _over_gate, CostGateError, "exceeds the ceiling")

    def _bad_forcing():
        c = copy.deepcopy(cfg0)
        c["model"]["format_forcing"] = "jsonschema"
        validate_format_forcing(c)
    check("an unknown format_forcing is a CONFIG error",
          "it was only checked while building the first request body — past "
          "the cost gate and inside the per-clause handler — so a typo was "
          "reported as N clause failures and exit 1 instead of exit 2",
          _bad_forcing, ConfigError, "format_forcing")

    def _bad_forcing_in_run():
        c = copy.deepcopy(cfg0)
        c["model"]["format_forcing"] = "jsonschema"
        with contextlib.redirect_stdout(io.StringIO()):
            run(c, type("x", (A,), {"clause": ["m0255"]})())
    check("a bad format_forcing stops the whole run, not one clause",
          "the guard must sit before the loop; if it fires per clause the "
          "exit code says 'a clause failed' about a config typo",
          _bad_forcing_in_run, ConfigError, "format_forcing")

    def _provider_reroutes():
        c = copy.deepcopy(cfg0)
        return resolve_provider(c, type("x", (A,), {"provider": "luna"})())
    check("--provider names a row and the row is USED",
          "it used to be `inline or row`, so --provider luna relabelled the "
          "run while still calling together.ai with together's key — spend "
          "attributed to a provider that was never called",
          _provider_reroutes, None)
    _rp = None
    try:
        _rp = _provider_reroutes()
    except Exception:                                         # noqa: BLE001
        pass
    require("--provider luna reroutes the model, url and key, not the label",
            "a relabelled call bills the wrong provider and the ledger says "
            "so in the wrong row",
            _rp is not None and _rp.model == "gpt-5.6-luna"
            and "openai.com" in (_rp.base_url or "")
            and _rp.api_key_env == "OPENAI_API_KEY"
            and _rp.price_per_mtok == [0.2, 1.2],
            f"--provider luna resolved to {getattr(_rp, 'model', None)!r} at "
            f"{getattr(_rp, 'base_url', None)!r} with "
            f"${getattr(_rp, 'price_per_mtok', None)} — the inline block won")

    def _provider_unknown_but_inline():
        c = copy.deepcopy(cfg0)
        resolve_provider(c, type("x", (A,), {"provider": "no-such-row"})())
    check("--provider with a name providers.json does not carry",
          "silently falling back to the inline model is the mislabelling "
          "defect in its purest form",
          _provider_unknown_but_inline, ConfigError, "not a row in")

    def _unknown_provider():
        c = copy.deepcopy(cfg0)
        c["model"].update(provider_name="not-a-provider", model=None,
                          base_url=None)
        resolve_provider(c, A())
    check("unknown provider name with no inline model",
          "a typo must not fall through to some default model",
          _unknown_provider, ConfigError, "is not in")

    def _inline_provider():
        c = copy.deepcopy(cfg0)
        c["model"]["provider_name"] = "not-in-providers-json"
        return resolve_provider(c, A())
    check("a provider defined INLINE resolves without providers.json",
          "the happy path for a model the wider repo does not carry",
          _inline_provider, None)
    _p = _inline_provider()
    require("the inline provider carries its own model id and prices",
            "an inline provider that silently inherited a providers.json row "
            "would spend at another model's price",
            _p.model == "deepseek-ai/DeepSeek-V4-Flash-0731"
            and _p.price_per_mtok == [0.14, 0.28],
            f"inline provider resolved to {_p.model!r} / {_p.price_per_mtok}")

    def _outdir_collision():
        c = copy.deepcopy(cfg0)
        d = tempfile.mkdtemp(prefix="phase1_runs_")
        c["output"]["dir"] = d
        c["output"]["run_name"] = "fixed"
        os.makedirs(os.path.join(d, "fixed"))
        open(os.path.join(d, "fixed", "m0255.raw.txt"), "w").write("paid for")
        resolve_outdir(c, _p)
        resolve_outdir(c, _p)
    check("a run must not overwrite a previous run's artifacts",
          "output.run_name + makedirs(exist_ok=True) wrote a second run's "
          "files over the first, and the raw responses of a run that cost "
          "money are the one thing that cannot be regenerated",
          _outdir_collision, ConfigError, "already holds")

    # ---- a run directory is a COMPLETE transcript -------------------------
    # Driven end to end through run() with a stub transport: no key, no
    # network, no spend. One clause succeeds and one FAILS, because a failed
    # clause is exactly when someone needs to see what was sent.

    class _StubClient:
        def __init__(self, prov, cfg):
            self.p, self.cfg = prov, cfg
            self.spent_usd, self.calls = 0.0, 0

        def complete(self, system, user):
            self.calls += 1
            if "m0091" in user.split("text:")[0]:
                raise ProviderError("stub: simulated HTTP 500")
            self.spent_usd += 0.00028
            return {"text": json.dumps(GOOD), "in": 1000, "out": 500,
                    "cost_usd": 0.00028}

    _rundir = tempfile.mkdtemp(prefix="phase1_run_")
    _cfg_run = copy.deepcopy(cfg0)
    _cfg_run["output"] = {"dir": _rundir, "run_name": "t"}
    _code, _made = None, []
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            _code = run(_cfg_run,
                        type("x", (A,), {"clause": ["m0255", "m0091"],
                                         "live": True})(),
                        client_factory=_StubClient)
        except Exception:                                     # noqa: BLE001
            pass
    _d = os.path.join(_rundir, "t")
    _made = sorted(os.listdir(_d)) if os.path.isdir(_d) else []
    _rj = (json.load(open(os.path.join(_d, "run.json"), encoding="utf-8"))
           if "run.json" in _made else {})
    _want = ["m0091.prompt_user.txt", "m0255.json", "m0255.lp",
             "m0255.prompt_user.txt", "m0255.raw.txt", "prompt_system.txt",
             CONCEPT_TABLE, "run.json"]
    _ct = (json.load(open(os.path.join(_d, CONCEPT_TABLE), encoding="utf-8"))
           if CONCEPT_TABLE in _made else None)
    require("the concept table is written, as data, by a real run",
            "the concept dictionary is its own artifact. Buried in .lp "
            "comments, every consumer — the read-back, the normaliser, a "
            "human reading the vocabulary — must regex ASP to recover it. "
            "⚠️ An earlier version of THIS check asserted only that a "
            "constant equalled itself, so it passed while the run wrote no "
            "table at all",
            _ct is not None and len(_ct) >= 1
            and set(_ct[0]) == {"concept", "clause_id", "gloss", "licence",
                                "cites", "inference"}
            and all(r["clause_id"] == "m0255" for r in _ct),
            f"{CONCEPT_TABLE} missing or malformed: {_ct!r}")
    require("a run directory holds what was SENT as well as what came back, "
            "for failed clauses too",
            "the directory used to hold only responses. dryrun.txt is a "
            "separate artifact for the default selection, so nobody could "
            "read a run and see what was actually asked — and m0091, the "
            "clause that failed, is the one whose prompt someone will want",
            all(w in _made for w in _want)
            and open(os.path.join(_d, "prompt_system.txt"),
                     encoding="utf-8").read() == build_system(cfg0)
            and set(_rj.get("user_sha") or {}) == {"m0255", "m0091"}
            and _rj.get("response_format", "MISSING") is not None
            and _rj.get("system_sha") == sha16(build_system(cfg0))
            and len(_rj.get("results") or []) == 2
            and _code == 1,
            f"run wrote {_made}, run.json keys "
            f"{sorted(_rj.keys())}, user_sha {sorted(_rj.get('user_sha') or {})}"
            f", exit {_code}")

    class _CrashClient(_StubClient):
        """Second clause raises something run() does NOT catch."""

        def complete(self, system, user):
            if self.calls >= 1:
                raise KeyboardInterrupt("stub: interrupted mid-run")
            return _StubClient.complete(self, system, user)

    _crashdir = tempfile.mkdtemp(prefix="phase1_crash_")
    _cfg_crash = copy.deepcopy(cfg0)
    _cfg_crash["output"] = {"dir": _crashdir, "run_name": "t"}
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            run(_cfg_crash,
                type("x", (A,), {"clause": ["m0255", "m0091"],
                                 "live": True})(),
                client_factory=_CrashClient)
        except KeyboardInterrupt:
            pass
    _cj = os.path.join(_crashdir, "t", "run.json")
    _crj = (json.load(open(_cj, encoding="utf-8"))
            if os.path.exists(_cj) else {})
    require("run.json survives an exception that escapes the loop",
            "it was written only after the loop completed, so an interrupt "
            "or a network drop lost the record of every clause already paid "
            "for — the clauses whose money is already spent",
            len(_crj.get("results") or []) == 1
            and (_crj["results"][0].get("clause_id") == "m0255"),
            f"after an interrupt on clause 2, run.json holds "
            f"{len((_crj.get('results') or []))} result(s)")

    # ---- the ledger row --------------------------------------------------

    _fake = {"choices": [{"message": {"content": "{}"},
                          "finish_reason": None}],
             "usage": {"prompt_tokens": 1000, "completion_tokens": 500,
                       "total_tokens": 1500,
                       "prompt_tokens_details": {"cached_tokens": 400}}}
    _env = None
    try:
        _env = response_envelope(_p, _fake)
    except Exception as exc:                                  # noqa: BLE001
        _env_err = exc
    _u = (_env or {}).get("usage") or {}
    require("the usage row carries real token counts and a cost",
            "the rows appended by this harness carried the RAW together.ai "
            "usage dict: cached_tokens was nested where spend.py never looks, "
            "content_chars was 0, and with no price entry the whole row was "
            "dropped from the total. Live spend was invisible to the cap",
            _u.get("prompt_tokens") == 1000
            and _u.get("completion_tokens") == 500
            and _u.get("cached_input_tokens") == 400
            and _u.get("uncached_input_tokens") == 600
            and abs((_u.get("cost_usd") or 0) - 0.00028) < 1e-9
            and (_env or {}).get("truncated") is False,
            f"envelope usage is {_u!r} (truncated="
            f"{(_env or {}).get('truncated')!r})")

    require("the run prints what spend.py will NOT see",
            "spend.py prices only from providers.json and this provider is "
            "defined inline, so the row is logged and then skipped from the "
            "total. That residue is unfixable from inside walkthrough/ and "
            "must therefore be shouted, not swallowed",
            (lambda w: "0.0028" in w and "spend.py" in w
             and "providers.json" in w)(
                 spend_invisibility_warning(_p, 0.0028, 4)
                 if "spend_invisibility_warning" in globals() else ""),
            "spend_invisibility_warning() does not name the amount, spend.py "
            "and providers.json")

    # ---- provenance ------------------------------------------------------

    _rec = None
    try:
        _rec = run_record(cfg0, _p, "SYSTEM PROMPT", [])
    except Exception:                                         # noqa: BLE001
        pass
    require("run.json records a real sha of the prompt and the config",
            "it recorded `system_sha_len`: two different prompts of equal "
            "length were indistinguishable, and run.json is the only "
            "provenance a run carries",
            isinstance(_rec, dict)
            and "system_sha_len" not in _rec
            and len(_rec.get("system_sha") or "") >= 16
            and len(_rec.get("config_sha") or "") >= 16
            and _rec.get("model") == _p.model
            and _rec["system_sha"] != run_record(
                cfg0, _p, "SYSTEM PROMPU", [])["system_sha"],
            f"run_record produced {sorted((_rec or {}).keys())}")

    # ---- artifacts, schema, rendering ------------------------------------

    art = rel("dryrun.txt")
    fp = inputs_fingerprint(cfg0)
    head = (open(art, encoding="utf-8").read(400)
            if os.path.exists(art) else "")
    require(f"dryrun.txt matches the current config and prompts "
            f"(inputs-sha {fp})",
            "a dry-run artifact that no longer describes what would be sent "
            "reads as authoritative and is wrong",
            f"inputs-sha: {fp}" in head,
            f"dryrun.txt is missing or STALE (current inputs-sha {fp}). "
            f"Regenerate with --write-artifact")

    sch = schema.json_schema()
    require(f"wire schema is flat and strict "
            f"({len(sch['properties'])} properties, no $ref)",
            "several providers do not resolve $ref, and a non-strict schema "
            "lets an invented field through as silent noise",
            "$defs" not in json.dumps(sch) and "$ref" not in json.dumps(sch)
            and sch["additionalProperties"] is False
            and set(sch["required"]) == set(sch["properties"])
            and sch["properties"]["abstain_reason"]["type"] == ["string",
                                                                "null"],
            "the wire schema carries $ref/$defs, is not additionalProperties="
            "false, does not require every property, or renders Optional as "
            "anyOf")

    # (moved: this is now asserted against a COMPLETED RUN, below — the
    # version here compared a constant to itself and could not fail.)

    _clause = {"section_id": "s", "kind": "conditional",
               "quote": "some clause text"}
    ab = parse_module(json.dumps({
        "outcome": "abstained", "clause_id": "m1",
        "abstain_reason": "it is a section heading", "claims": [],
        "acts": [], "concepts": [], "ontology": [], "asserts": [],
        "beats": [], "defines": [], "closure": [], "requires": [],
        "inputs": [], "forbid_body": []}))
    good_lp = schema.render_lp(parse_module(json.dumps(GOOD)), _clause)
    require(".lp renders from the object: interface, read-back, licence, "
            "abstention — and deterministically",
            "the .lp is what a reviewer reads; a missing read-back or licence "
            "marker makes the module unreviewable, and non-determinism makes "
            "two runs incomparable",
            "%% ABSTAIN:" in schema.render_lp(ab, _clause)
            and f"%% requires: {', '.join(GOOD['requires'])}" in good_lp
            and "%% closure: " in good_lp
            and "%!trace_rule" in good_lp
            and "% [T] m0255" in good_lp
            and "#const onto = on." in good_lp
            and schema.render_lp(parse_module(json.dumps(GOOD)),
                                 _clause) == good_lp,
            f"rendered .lp is missing a required element or is not "
            f"deterministic:\n{good_lp}")

    m0255 = [r for r in rows if r["id"] == "m0255"][0]
    found, _unres = cross_references(m0255, rows, cfg0)
    require(f"cross-references resolve off the document's own anchors "
            f"({len({r['id'] for r in found})} clauses for m0255)",
            "a clause that modifies rules defined elsewhere cannot be "
            "translated in isolation",
            bool(found),
            "m0255 cites #restricted_content and #sensitive_content and "
            "neither resolved")

    sys_txt = build_system(cfg0)
    missing_tokens = [f"{tok!r} ({why})" for tok, why in (
        ("abstain", "the abstention route"),
        ("asserts", "the fixed relation schema"),
        ("closure", "the FORCED per-act default closure"),
        ("textual", "the licence taxonomy"),
        ("assumed", "the licence taxonomy"),
        ("world", "the licence taxonomy"),
        ("read_back", "the read-back annotation"),
        ("forbid_body", "rule-set claims"),
        ("Made-up things", "the 17 failure modes"))
        if tok.lower() not in sys_txt.lower()]
    require(f"system prompt assembles from "
            f"{len(cfg0['prompt']['system_files'])} files "
            f"({len(sys_txt):,} chars) and carries the relation schema, the "
            f"three licences, the read-back, the closure, forbid_body, "
            f"abstention and the failure modes",
            "a prompt that lost the licence taxonomy would produce unmarked "
            "inventions and every downstream check would still pass",
            not missing_tokens,
            "the assembled system prompt is missing "
            + ", ".join(missing_tokens))

    print(f"\n{ok} passed, {bad} failed")
    return 1 if bad else 0


# ==========================================================================
# 11.  CLI
# ==========================================================================

def list_models(cfg, args):
    """GET /models — read-only and free. Answers 'is this id real?'.

    Exit 0 when the configured id is there, 2 when it is not: that is a config
    error, and returning 1 said "a clause failed" about a run that sent no
    clauses. The shortlist is derived from the configured model id rather than
    hardcoded to "deepseek", which printed nothing at all against any other
    provider and then reported failure.
    """
    import urllib.error
    import urllib.request
    prov = resolve_provider(cfg, args)
    key = _resolve_key(prov)
    url = prov.base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise ProviderError(
            f"HTTP {exc.code}: {exc.read().decode()[:400]}") from exc
    rows = data.get("data") if isinstance(data, dict) else data
    ids = sorted(str(r.get("id") or r.get("name")) for r in (rows or []))
    want = (prov.model or "").lower()
    # The shortlist: ids sharing the configured model's family — its last path
    # segment's first token, e.g. `deepseek-ai/DeepSeek-V4-Flash` -> "deepseek".
    stem = re.split(r"[-_.:]", want.rsplit("/", 1)[-1])[0]
    hits = [i for i in ids if stem and stem in i.lower()]
    print(f"{len(ids)} model(s) at {url}")
    if hits:
        print(f"\nids matching {stem!r}:")
    else:
        print(f"\nno id matches {stem!r}; showing the first 20 of {len(ids)}:")
        hits = ids[:20]
    for i in hits:
        print(f"   {'-> ' if i.lower() == want else '   '}{i}")
    found = any(i.lower() == want for i in ids)
    print(f"\nconfigured: {prov.model}")
    print("   " + ("FOUND — the id is real"
                   if found
                   else "NOT FOUND — the configured id does not exist here. "
                        "Fix model.model before spending."))
    return 0 if found else 2


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--clause", nargs="+", help="clause ids, e.g. m0255")
    ap.add_argument("--section", help="section_id, e.g. transformation_exception")
    ap.add_argument("--kinds", nargs="+",
                    help="definitional | conditional | holistic | meta")
    ap.add_argument("--limit", type=int,
                    help="keep at most N of the selection. 0 is a refusal, "
                         "not 'no limit'.")
    ap.add_argument("--provider",
                    help="SELECT a row of providers.json — its model, url, "
                         "key and prices REPLACE the config's inline model "
                         "block. Refuses if the name is not a row there; it "
                         "will not relabel a call to somebody else.")
    ap.add_argument("--model", help="override the model id only. The base "
                                    "url, key and prices stay as resolved.")
    ap.add_argument("--max-tokens", type=int, dest="max_tokens")
    ap.add_argument("--show-prompt", nargs="?", const=1, type=int, default=0,
                    metavar="N", help="print the system prompt and N user prompts")
    ap.add_argument("--live", action="store_true",
                    help="actually send. Without this nothing is sent.")
    ap.add_argument("--only-stale", action="store_true", dest="only_stale",
                    help="translate only the clauses of the selection whose "
                         "stored artifact is stale — its clause text or the "
                         "schema source moved (contract-stale), its prompt, "
                         "model or params moved (provenance-stale), or it "
                         "carries no version stamp at all. OFF BY DEFAULT: "
                         "changing what a bare run translates is a spend "
                         "change. The census is printed before the cost gate.")
    ap.add_argument("--waivers", default=None, metavar="PATH",
                    help="a reviewed waiver file naming clauses whose "
                         "PROVENANCE change does not oblige a re-run, the "
                         "exact hash transition it excuses, and who signed "
                         "it. ⛔ It can never excuse a contract change, and it "
                         "is inert without --only-stale.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write-artifact", action="store_true",
                    help="regenerate dryrun.txt from the current config and "
                         "prompt files. Sends nothing.")
    ap.add_argument("--list-models", action="store_true",
                    help="GET /models on the configured provider. Read-only, "
                         "free. Use it to verify the model id before spending.")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    try:
        if args.write_artifact:
            return write_dry_run_artifact(load_config(args.config), args)
        if args.list_models:
            return list_models(load_config(args.config), args)
        return run(load_config(args.config), args)
    except (Phase1Error, version.VersionError) as exc:
        # A refused waiver is a usage error and exits 2. It is NOT "a clause
        # failed" (exit 1): no clause was sent, and the operator has to fix a
        # file before anything can be.
        print(f"⛔ {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


# ==========================================================================
# 12.  The repair loop
# ==========================================================================
#
# A translation that fails a deterministic check is sent back. What the repair
# attempt can SEE is the whole design here, and getting it wrong does not look
# like a failure — it looks like a rising pass rate.
#
# It is ONE ACCUMULATING TRANSCRIPT, in the model's own turn structure:
#
#     system   : the fixed instructions, format, examples, failure modes
#     user     : the clause and its cross-references
#     assistant: the module it produced
#     user     : every check that failed, with its reason
#     assistant: its next module
#     ...
#
# Nothing is dropped once fixed. A log carrying only the LATEST findings lets
# repair oscillate — fix A and break B, fix B and reintroduce A — for the whole
# budget, and the symptom is indistinguishable from a model that cannot do the
# task at all.
#
# ⛔ ONLY STAGE-2 FINDINGS MAY ENTER. Later stages carry probe cases with their
# expected verdicts. A leaked verdict lives in a transcript for the rest of that
# clause's life, not for one call — which is why `origin` is filtered here and
# an excluded finding leaves a VISIBLE hole rather than vanishing.

import dataclasses

# ⭐ `probe-structural` IS ADMITTED; `probe-verdict` NEVER IS, and the split is
# the whole reason stage 3 has two origins. A structural finding — "rule R is in
# no derivation any situation distinguishes", "the module admits a situation the
# clause treats as impossible", "the coherent set is empty" — is derived from the
# module and the solver alone, with no expected verdict anywhere near it, exactly
# as stage 2's are. A `probe-verdict` finding names a situation whose derived
# status disagrees with its LABEL, and for any one situation the module derived
# something specific: naming it IS the answer key. Withholding the label while
# naming the situation is not a partial disclosure, it is the whole disclosure
# with a fig leaf. See `probe.route` — a verdict mismatch discards the transcript
# and re-runs stage 1 from a clean prompt instead.
DISCLOSABLE_ORIGINS = ("schema", "link", "probe-structural")


@dataclasses.dataclass(frozen=True)
class RepairFinding:
    check_id: str
    severity: str
    where: str
    message: str
    origin: str


@dataclasses.dataclass
class RepairOutcome:
    status: str                 # translated | abstained | abstained_under_repair
                                # | unrepaired | invalid
    attempts: int
    module: object = None
    findings: list = dataclasses.field(default_factory=list)
    per_attempt: list = dataclasses.field(default_factory=list)
    flags: list = dataclasses.field(default_factory=list)
    unclear_closure_rate: float = 0.0
    transcript: list = dataclasses.field(default_factory=list)


def render_error_log(attempts):
    """Render ONE attempt's findings as the next user turn.

    ⚠️ Takes a list so a caller CAN pass several, but the loop passes one. The
    accumulation is the TRANSCRIPT — turn 3 holds attempt 1's findings and turn
    5 holds attempt 2's, both still visible. Re-rendering the whole history into
    every turn would duplicate attempt 1 into every later turn and pay for it
    again, while adding nothing the conversation did not already carry.
    """
    out = []
    for label, findings in attempts:
        out.append(f"{label} failed these checks:")
        withheld = notes = 0
        shown = 0
        for f in findings:
            if f.origin not in DISCLOSABLE_ORIGINS:
                withheld += 1
                continue
            # ⛔ NOTES ARE NEVER SHOWN AS FAULTS. A note is true of a CORRECT
            # module — `requires-unprovided` fires on every well-formed
            # single-clause module, because `requires` means another clause
            # defines it and no other clause is linked at this scope. Handed
            # one under "fix every one of them", the only available repair is
            # to move the predicate into `inputs`, which collapses the
            # distinction that makes linking possible. One clause was given
            # eight of them, twice, and never converged.
            if f.severity != "error":
                notes += 1
                continue
            shown += 1
            out.append(f"  - [{f.check_id}] {f.where}: {f.message}")
        if not shown:
            out.append("  (no error-severity findings — nothing here is yours "
                       "to fix)")
        if notes:
            out.append(f"  ({notes} note(s) not shown: they are true of a "
                       f"correct module at this scope and are not faults)")
        if withheld:
            # A visible hole, never a silent omission: a reader must be able to
            # tell a filtered log from a clean one.
            out.append(f"  - ({withheld} finding(s) withheld: they come from a "
                       f"later stage and would disclose an expected answer)")
        out.append("")
    out.append("Fix every one of them. Return the corrected module, complete.")
    return "\n".join(out)


_SHAPE_FIELDS = ("claims", "acts", "concepts", "ontology", "asserts", "beats",
                 "defines", "closure", "requires", "inputs", "forbid_body")


def _shape(raw):
    """The counts a repair must not quietly reduce.

    Read off the RAW object, not the validated model: attempt 1 is usually one
    that failed validation, so it has no model — and comparing every repair
    against an empty shape made the guards fire on nothing.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    return {k: len(raw.get(k) or []) for k in _SHAPE_FIELDS}


#: A change to these is a DECLARATION edit: it alters what the module claims
#: about its own interface rather than what it says about the clause. The cheap
#: way to clear a finding is to bend one of these until the check stops firing.
DECLARATION_FIELDS = ("requires", "inputs", "acts", "closure", "forbid_body")
TRANSLATION_FIELDS = ("asserts", "beats", "defines", "ontology")


def _diff_flags(before, after):
    flags = []
    if not before or not after:
        return flags
    if any(after.get(k, 0) < before.get(k, 0) for k in TRANSLATION_FIELDS
           + ("claims",)):
        flags.append("shrank")
    decl = any(after.get(k) != before.get(k) for k in DECLARATION_FIELDS)
    trans = any(after.get(k) != before.get(k) for k in TRANSLATION_FIELDS)
    if decl and not trans:
        flags.append("declaration-edit")
    return flags


def repair_loop(initial_raw, clause, model, max_attempts=3, corpus_ids=None,
                concepts=None, system="", first_user=None):
    """Attempt 1 is already in hand; call the model for attempts 2..N.

    `model` needs `complete_messages(system, messages)`. The transcript grows by
    two turns per attempt and its PREFIX never changes, so every call after the
    first is a cache hit.
    """
    import checks as _checks
    corpus_ids = corpus_ids if corpus_ids is not None else {clause.get("id")}

    def look(raw, n):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            return None, [RepairFinding("not-json", "error", "<response>",
                                        str(exc), "schema")]
        res = _checks.run_checks(obj, clause, corpus_ids, concepts=concepts,
                                 attempt=n)
        found = [RepairFinding(f.check_id, f.severity, f.where, f.message,
                               f.origin) for f in res.findings]
        return res, found

    # ⚠️ The REAL first prompt, not a summary of it. A synthesised stub dropped
    # the cross-referenced clause texts — which stage 1 calls load-bearing — so
    # repair ran without the definitions AND the stored transcript was a
    # fiction of the exchange rather than a record of it.
    transcript = [{"role": "user",
                   "content": first_user if first_user is not None else
                   f"CLAUSE {clause.get('id')}\n{clause.get('quote', '')}"}]
    per_attempt, flags = [], []
    res, found = look(initial_raw, 1)
    prev_shape = _shape(initial_raw)
    raw = initial_raw

    def close(status, **kw):
        kw.setdefault("findings", found)
        """Every exit path ends the transcript with what the model last said.

        The assistant turn used to be appended only while preparing the NEXT
        prompt, so an exhausted loop stored a transcript ending in our question
        rather than its answer — and a failed clause is the one someone reads.
        """
        if not transcript or transcript[-1]["role"] != "assistant":
            transcript.append({"role": "assistant", "content": raw})
        return RepairOutcome(status=status, per_attempt=per_attempt,
                             flags=flags, transcript=transcript, **kw)

    for n in range(1, max_attempts + 1):
        per_attempt.append(len(found))
        if res is not None and res.outcome == "abstained":
            # A model that says it cannot translate faithfully is not argued
            # with — re-prompting produces exactly what abstention prevents.
            # But an abstention AFTER a failed attempt is a repair-pressure
            # artifact, and counting it with first-attempt abstentions is how a
            # model abstains its way out of the hard clauses.
            return close("abstained" if n == 1 else "abstained_under_repair",
                         attempts=n, module=res.module)
        if res is not None and not res.repair_needed:
            return close("translated", attempts=n, module=res.module,
                         unclear_closure_rate=_unclear_rate(res.module))
        if n == max_attempts:
            break

        transcript.append({"role": "assistant", "content": raw})
        transcript.append({"role": "user",
                           "content": render_error_log([(f"attempt {n}", found)])})
        env = model.complete_messages(system, transcript)
        raw = env["text"]
        res, found = look(raw, n + 1)
        new_shape = _shape(raw)
        for f in _diff_flags(prev_shape, new_shape):
            if f not in flags:
                flags.append(f)
        prev_shape = new_shape or prev_shape

    return close("unrepaired", attempts=max_attempts,
                 module=getattr(res, "module", None), findings=found,
                 unclear_closure_rate=_unclear_rate(
                     getattr(res, "module", None)))


def _unclear_rate(mod):
    """Answering `unclear` everywhere is legal, grows the module, goes green,
    and restores the silent default the declaration exists to replace. Only a
    RATE shows that — no per-attempt diff can."""
    if mod is None or not getattr(mod, "closure", None):
        return 0.0
    return sum(c.closure == "unclear" for c in mod.closure) / len(mod.closure)


# ⚠️ NOTHING may be defined below this line. Under `import` the whole module
# runs and every later definition exists; run as a SCRIPT, `main()` executes
# here and anything after it is never reached. A full test suite passes either
# way, so the only symptom is a NameError on the first real invocation — which
# is what happened, after the first clause had already been paid for.
if __name__ == "__main__":
    raise SystemExit(main())
