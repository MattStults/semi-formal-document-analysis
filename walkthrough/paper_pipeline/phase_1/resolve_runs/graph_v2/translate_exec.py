#!/usr/bin/env python3
"""Opt-in concurrent/batch execution for the phase_1 translation harness.

`translate.py` IS serial mode and stays the reference implementation; this
module refuses to run without an explicit `execution` block in the config:

    {"execution": {"mode": "concurrent", "concurrent_n": 4}}
    {"execution": {"mode": "batch", "batch_min_pending": 8}}

It drives translate.py's OWN per-clause lifecycle through dispatch_core's
executors (BATCH_DESIGN.md "Post-review resolution": one shared core, built
once, serving both pipelines). The dependency structure of translation is a
FLAT table — every clause independent, a clause's round-k depending only on
its own round-(k-1) — so the tree Scheduler is replaced by `FlatScheduler`,
while the executors (ConcurrentExecutor's bounded worker pool, BatchExecutor's
submit/poll/collect loop with the F3 submit gate, F2 manifest and F5 taxonomy)
are reused unchanged.

HOW REUSE IS ACHIEVED — the one design decision in this file. translate.py's
repair semantics live in `repair_loop`, a blocking loop that calls the model
itself; the executors need a steppable state (`next_request()` / `feed(env)`).
Rather than re-derive repair_loop's decisions (abstention handling, shape
flags, per-attempt counts, transcript form — every one an equivalence hazard),
`ClauseState` runs translate.py's own per-clause code on a private thread and
hands it a shim "model" whose complete()/complete_messages() park the message
array for the executor and block until an envelope is fed back. repair_loop —
the serial reference — therefore remains the single implementation of repair
semantics in every mode, and the per-clause artifacts (raw, transcript,
module JSON, .lp, version sidecar, graveyard entry, run.json row) are written
by the same calls translate.run() makes.

The per-clause body below re-expresses the LOOP BODY of translate.run()
(translate.py §9) call-for-call: that body is inline in run(), not a callable,
and translate.py is a watched file this cycle may not modify. Every function
it uses — build_user, estimate_cost, cost_gate, repair_loop, checks.run_checks
(via repair_loop), gy.should_keep/write_entry/check_cap, version.stamp,
schema.render_lp/concept_rows, run_record — is imported, never copied.

Cost/spend contract (deliverable 2):
  - the run-level worst-case gate is translate.py's own `estimate_cost` +
    `cost_gate`, run BEFORE any client exists, exactly as in run();
  - measured ledger rows: live calls ledger inside Client._send as always
    (ConcurrentExecutor serialises `_log_usage` under its ledger lock); batch
    rows are ledgered at collection by BatchExecutor via the same
    `client._log_usage`, one measured row per returned item;
  - the graveyard cap is checked at the same point run() checks it — after
    the gate, before any dispatch state, scheduler or executor exists, so it
    fires BEFORE any spend and before any executor work;
  - `client.max_cost_usd` is set from `cost.max_cost_usd` so BatchExecutor's
    F3 submit gate (worst-case at submit, plus outstanding commitment) binds
    on top of the run-level gate, never instead of it.

Divergences from serial translate.py, accepted by name:
  - a hard transport failure inside an executor that run_one cannot deliver
    back to the clause (i.e. one raised OUTSIDE a pending request) aborts the
    whole run rather than failing one clause; every completed clause's
    artifacts and the flushed run.json survive. Failures raised while a
    request IS pending — the normal case — are delivered as data
    (`feed_failure`) and become the same per-clause error record serial
    produces.
  - the executor transport ladder retries transient failures (including
    TRUNCATED) up to 6 times per draw; serial translate.py raises immediately
    unless `model.resample_truncation` is set. More retries, never fewer
    checks — the conservative direction.
  - `model.resample_truncation` is inert in concurrent mode (dispatch_core
    review R9.1: _body/_send bypasses Client._retrying); the ladder's bounded
    retries cover the same failure class.
  - batch-mode kill-recovery is unsupported: a killed batch run's submitted,
    paid job is abandoned (review F1 — every clause shares one recovery
    identity, so a resumed sweep could mis-route replies across clauses);
    `_TranslateBatch` refuses to start over a non-empty in-flight manifest.
"""
import argparse
import json
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T          # noqa: E402  (the serial reference harness)
import graveyard as gy         # noqa: E402
import schema as S             # noqa: E402
import version                 # noqa: E402
import dispatch_core as dc     # noqa: E402  (shared core -- import, not copy)

PENDING, DONE, FAILED = dc.PENDING, dc.DONE, dc.FAILED

#: rec statuses that count as a failure in run()'s summary partition
_SUCCESS_STATUSES = ("translated", "abstained", "abstained_under_repair")


# ==========================================================================
# 1.  Mode selection — this module REFUSES to run serial
# ==========================================================================

def execution_config(cfg):
    """The config's `execution` block, validated. Absent = run translate.py.

    Serial execution deliberately has no route through this module:
    translate.py IS serial mode, and a second serial implementation is a
    second thing to keep equivalent for zero benefit.
    """
    ex = cfg.get("execution")
    if not ex:
        raise T.ConfigError(
            "config has no `execution` block — this module only runs the "
            "opt-in concurrent/batch modes. For serial execution run plain "
            "translate.py (translate.py IS serial mode). To opt in, add "
            '{"execution": {"mode": "concurrent", "concurrent_n": 4}} or '
            '{"execution": {"mode": "batch", "batch_min_pending": 8}}')
    mode = ex.get("mode")
    if mode == "serial":
        raise T.ConfigError(
            'execution.mode is "serial" — run plain translate.py for that; '
            "it is the reference implementation and this module refuses to "
            "shadow it")
    if mode not in ("concurrent", "batch"):
        raise T.ConfigError(
            f"execution.mode={mode!r} is not one of concurrent | batch "
            f"(serial = plain translate.py)")
    return mode, dict(ex)


# ==========================================================================
# 2.  ClauseState — translate.py's per-clause lifecycle as a steppable state
# ==========================================================================

def _norm_env(env):
    """Envelope in either transport shape -> translate.py's live call shape.

    Live executors feed what Client._send returns: {"text","in","out",
    "cost_usd"}. The batch collector feeds {"text","usage"} (dispatch_core
    _collect). The clause body only ever sees the live shape.
    """
    if "in" in env and "out" in env:
        return env
    u = env.get("usage") or {}
    return {"text": env.get("text", ""),
            "in": u.get("prompt_tokens") or 0,
            "out": u.get("completion_tokens") or 0,
            "cost_usd": env.get("cost_usd")
            or u.get("cost_usd") or 0.0}


class ClauseState(dc.DispatchState):
    """One clause's translate/repair lifecycle behind DispatchState's step
    interface. The FLAT dependency table BATCH_DESIGN names: round-k of this
    clause depends only on its own round-(k-1), which is exactly the pending
    transcript the private thread is blocked on.

    The thread runs `ctx.clause_body` — the re-expression of translate.run()'s
    loop body — with `self` as the shim model. status becomes DONE when the
    body returns its run.json record (INCLUDING per-clause failure records:
    serial translate.py tolerates clause failures and so does this), FAILED
    only on an exception the body's own per-clause handler would not have
    caught either.
    """

    kind = "T"

    def __init__(self, ctx, slot, job):
        # deliberately no super().__init__: the base initialises Driver.call's
        # repair machinery, which repair_loop owns here. Only the surface the
        # executors touch is set up.
        self.ctx, self.slot, self.job = ctx, slot, job
        cid = job["row"][ctx.idk]
        self.clause_id = cid
        self.key = f"T:{cid}"
        self.wdir, self.out, self.cfg = ctx.outdir, ctx.outdir, ctx.cfg
        self.schema = None      # response_format comes from translate's own
        #                         config (see _TranslateBatch._request_body)
        self.status, self.error, self.result = PENDING, None, None
        self.repair_round = 0   # round k <=> the k-th repair transcript
        self.budget, self.spent = float("inf"), 0.0
        self.max_repairs = 0
        self._req_ready = threading.Event()
        self._resp_ready = threading.Event()
        self._pending = None
        self._delivery = None
        self._nreq = 0
        self._thread = None

    # -- the shim model surface (what the clause body / repair_loop calls) --
    def complete(self, system, user):
        return self._rpc([{"role": "user", "content": user}])

    def complete_messages(self, system, messages):
        return self._rpc([dict(m) for m in messages])

    def _rpc(self, msgs):
        self._pending = msgs
        self.repair_round = self._nreq   # 0 = attempt 1; k = k-th repair
        self._nreq += 1
        self._resp_ready.clear()
        self._req_ready.set()
        self._resp_ready.wait()
        kind, payload = self._delivery
        self._delivery = None
        if kind == "fail":
            raise T.ProviderError(payload)
        return payload

    # -- the dispatch_core step interface ----------------------------------
    def _ensure_thread(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run_body, daemon=True)
            self._thread.start()

    def _run_body(self):
        try:
            self.result = self.ctx.clause_body(self.job, self)
            self.status = DONE
        except BaseException as exc:              # noqa: BLE001
            self.status = FAILED
            self.error = (f"clause {self.clause_id}: "
                          f"{type(exc).__name__}: {exc}")
        finally:
            self._req_ready.set()   # wake whoever is waiting on this state

    def next_request(self):
        if self.status != PENDING:
            return None
        self._ensure_thread()
        self._req_ready.wait()
        if self.status != PENDING:
            return None
        return list(self._pending)

    def feed(self, env):
        self._deliver(("env", _norm_env(env)))

    def feed_failure(self, kind, detail):
        """A transport failure as data: raised inside the clause body as
        ProviderError, where translate.run()'s own per-clause handler turns
        it into the same error record serial mode writes."""
        self._deliver(("fail", detail))

    def _deliver(self, item):
        self._req_ready.clear()
        self._delivery = item
        self._resp_ready.set()
        # wait until the body posts its next request or finishes, so the
        # executor's status check after feed() is truthful
        self._req_ready.wait()

    def can_restart(self):
        # translate.py has no fresh-restart path; a truncation failure goes
        # to the clause body as data instead
        return False

    def bill(self, cost):
        if cost:
            self.spent += cost


# ==========================================================================
# 3.  FlatScheduler — the flat dependency table
# ==========================================================================

class FlatScheduler:
    """Every clause independent; the only dependency (round-k on round-k-1)
    lives inside each ClauseState. Presents the same executor surface as
    dispatch_core.Scheduler; `root_result` becomes non-None when every clause
    has completed, which is what the executors' run loops terminate on."""

    def __init__(self, ctx, states):
        self.ctx = ctx
        # LIFO ready stack (executors pop from the end): reversed so clause 0
        # is dispatched first, matching serial order
        self.ready = list(reversed(states))
        self.lock = threading.Lock()
        self.pending = len(states)
        self.root_result = None

    def pop_ready(self):
        return self.ready.pop() if self.ready else None

    def drain_ready(self):
        out, self.ready = list(self.ready), []
        return out

    def push_back(self, states):
        self.ready.extend(states)

    def requeue(self, state):
        self.ready.append(state)

    def complete(self, state):
        self.ctx.finish(state.slot, state.result)
        self.pending -= 1
        if self.pending == 0:
            self.root_result = {"clauses": len(self.ctx.results)}


# ==========================================================================
# 4.  Executors — dispatch_core's, with per-clause failure tolerance
# ==========================================================================

class _TolerantRunOne:
    """serial translate.py tolerates per-clause failures; run_one raising a
    Phase1Error while a request is pending is therefore delivered INTO the
    clause instead, where the body's own handler records the error rec."""

    def run_one(self, state):
        try:
            super().run_one(state)
        except Exception as exc:                          # noqa: BLE001
            # review F3: catch Exception, not just Phase1Error, so the
            # clause's parked body thread is always unwound (delivery below)
            # even on the abort path; the non-Phase1Error is then re-raised,
            # preserving serial-equivalent abort semantics.
            if state.status == PENDING:
                # review F2: for Phase1Errors the detail is str(exc) — the
                # body's own handler prefixes the re-raised type name, so a
                # type-name prefix here doubled it vs serial run.json rows.
                # Non-Phase1Errors keep the type name: serial writes no rec
                # for them at all, so there is no row to be equivalent to.
                detail = (str(exc) if isinstance(exc, T.Phase1Error)
                          else f"{type(exc).__name__}: {exc}")
                state.feed_failure("error", detail)
            if (not isinstance(exc, T.Phase1Error)
                    or isinstance(exc, T.CostGateError)
                    or state.status == FAILED):
                # CostGateError by name (routing-gap audit F2): tolerating
                # the ceiling per-clause would bill one more call per
                # remaining clause -- the run stops loudly instead, with
                # every completed clause's artifacts and run.json intact.
                raise


class _TranslateSerialLive(_TolerantRunOne, dc.SerialExecutor):
    """The live rung under batch mode (starvation fallback, F5 reruns)."""


class _TranslateConcurrent(_TolerantRunOne, dc.ConcurrentExecutor):
    """Bounded live worker pool over ClauseStates."""


class _TranslateBatch(dc.BatchExecutor):
    """dispatch_core's batch executor with translate's own response_format
    and the tolerant live rung."""

    def __init__(self, driver, exec_cfg=None, transport=None, manifest=None):
        super().__init__(driver, exec_cfg, transport=transport,
                         manifest=manifest)
        # review F1 (honest refusal): every ClauseState shares one recovery
        # identity (wdir=outdir, kind="T"), so dispatch_core's F2 sweep would
        # keep ONE recovered reply and hand it to whichever clause pops first
        # — a cross-clause mis-delivery. Refuse rather than mis-route.
        orphans = self.manifest.sweep()
        if orphans:
            raise T.Phase1Error(
                f"{len(orphans)} in-flight record(s) in {self.manifest.dir}: "
                "batch-mode kill-recovery is unsupported for translation; a "
                "killed batch run's submitted job is abandoned. Rerun in a "
                "fresh outdir.")
        self.live = _TranslateSerialLive(driver)

    def _request_body(self, state):
        """Per-request body with the EXACT response_format translate.py
        sends (strictness and schema from config), never dispatch_core's
        strict=False rebuild — a batch repair sent with a different
        response_format is quietly a different call from the one being
        repaired (translate.Client._body_messages's own doctrine)."""
        body = super()._request_body(state)
        rf = T.response_format_payload(self.drv.cfg)
        if rf is None:
            body.pop("response_format", None)
        else:
            body["response_format"] = rf
        return body


class _Driver:
    """The duck dispatch_core executors drive: client, brief, out, cfg."""

    def __init__(self, cfg, client, system, outdir):
        self.cfg, self.client = cfg, client
        self.brief, self.out = system, outdir


def build_executor(mode, driver, exec_cfg, transport=None):
    if mode == "concurrent":
        return _TranslateConcurrent(driver,
                                    n=exec_cfg.get("concurrent_n", 4))
    if mode == "batch":
        return _TranslateBatch(driver, exec_cfg, transport=transport)
    raise T.ConfigError(f"unknown execution mode {mode!r}")


# ==========================================================================
# 5.  RunContext — everything translate.run() held in locals
# ==========================================================================

class RunContext:
    def __init__(self, cfg, prov, client, system, outdir, jobs, known_ids,
                 max_attempts, gy_cfg, gy_dir, schema_src, model, temp,
                 params, version_block):
        self.cfg, self.prov, self.client = cfg, prov, client
        self.system, self.outdir = system, outdir
        self.jobs, self.known_ids = jobs, known_ids
        self.max_attempts = max_attempts
        self.gy_cfg, self.gy_dir = gy_cfg, gy_dir
        self.schema_src, self.model, self.temp = schema_src, model, temp
        self.params, self.version_block = params, version_block
        self.idk = cfg["corpus"]["id_key"]
        self.io_lock = threading.RLock()
        self.results = [None] * len(jobs)     # run.json rows, slot-ordered
        self.concepts = [None] * len(jobs)    # concept rows, slot-ordered
        self.user_shas = {}
        self.failures = 0

    # -- run.json / concept table, after every clause (translate's flush) --
    def flush(self):
        with self.io_lock:
            rows = [r for r in self.results if r is not None]
            concepts = [c for cs in self.concepts if cs
                        for c in cs]
            with open(os.path.join(self.outdir, T.CONCEPT_TABLE), "w",
                      encoding="utf-8") as fh:
                json.dump(concepts, fh, indent=1)
            with open(os.path.join(self.outdir, "run.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(T.run_record(
                    self.cfg, self.prov, self.system, rows, self.user_shas,
                    {"usd": round(getattr(self.client, "spent_usd", 0.0), 6),
                     "calls": getattr(self.client, "calls", 0),
                     "visible_to_spend_py": False,
                     "why": "spend.py prices from providers.json; this "
                            "provider is defined inline in this config"},
                    version_block=self.version_block), fh, indent=1)

    def finish(self, slot, rec):
        with self.io_lock:
            self.results[slot] = rec
            if rec.get("status") not in _SUCCESS_STATUSES:
                self.failures += 1
            self.flush()

    # -- the loop body of translate.run(), one clause, shim model ----------
    def clause_body(self, job, shim):
        """Byte-for-byte the artifact writes and record fields of
        translate.run()'s per-clause loop body; `shim` stands where `client`
        stood, so attempt 1 and every repair draw travel through whichever
        executor is running the state."""
        cfg, prov, outdir = self.cfg, self.prov, self.outdir
        cid = job["row"][self.idk]
        rec = {"clause_id": cid, "provider": prov.name,
               "model": prov.model, "xrefs": job["xrefs"],
               "xrefs_unresolved": job["xrefs_unresolved"]}
        with open(os.path.join(outdir, f"{cid}.prompt_user.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(job["user"])
        with self.io_lock:
            self.user_shas[cid] = T.sha16(job["user"])
        rec["user_sha"] = self.user_shas[cid]
        _stamp = version.stamp(
            job["row"].get(cfg["corpus"]["text_key"], ""), self.schema_src,
            self.system, self.model, self.temp, self.params)

        try:
            env = shim.complete(self.system, job["user"])
        except T.Phase1Error as exc:
            rec.update(status="error", error=f"{type(exc).__name__}: {exc}")
            print(f"  ⛔ {cid}: {rec['error']}")
            return rec

        with open(os.path.join(outdir, f"{cid}.raw.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(env["text"])
        rec.update(tokens_in=env["in"], tokens_out=env["out"],
                   cost_usd=round(env.get("cost_usd") or 0.0, 6))

        try:
            out = T.repair_loop(env["text"], clause=job["row"], model=shim,
                                max_attempts=self.max_attempts,
                                corpus_ids=self.known_ids,
                                system=self.system, first_user=job["user"])
        except T.Phase1Error as exc:
            rec.update(status="error", error=f"{type(exc).__name__}: {exc}")
            print(f"  ⛔ {cid}: {rec['error']}")
            return rec

        keep, why = gy.should_keep(
            out, self.max_attempts, self.gy_cfg.get("rates") or {},
            clause_id=cid, seed=int(self.gy_cfg.get("seed", 0)))
        if keep:
            entry = gy.write_entry(
                self.gy_dir, job["row"], out, reason=why,
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

        if out.status not in _SUCCESS_STATUSES:
            rec.update(status=out.status,
                       surviving_findings=[
                           f"[{f.check_id}] {f.where}: {f.message}"
                           for f in out.findings])
            print(f"  ⛔ {cid}: {out.status} after {out.attempts} "
                  f"attempt(s), {len(out.findings)} finding(s) standing")
            return rec
        obj = out.module
        if out.attempts > 1:
            print(f"  ↻ {cid}: {out.status} on attempt {out.attempts}"
                  + (f"  ⚠️ {', '.join(out.flags)}" if out.flags else ""))

        with open(os.path.join(outdir, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(obj.model_dump_json(indent=1))
        lp = S.render_lp(obj, job["row"])
        with open(os.path.join(outdir, f"{cid}.lp"), "w",
                  encoding="utf-8") as fh:
            fh.write(lp + version.lp_comment(_stamp) + "\n")
        version.write_stamp(outdir, cid, _stamp)
        rec.update(_stamp)
        with self.io_lock:
            self.concepts[shim.slot] = S.concept_rows(obj)

        lic = {}
        for item in (*obj.ontology, *obj.asserts, *obj.beats, *obj.defines):
            lic[item.licence] = lic.get(item.licence, 0) + 1

        rec.update(n_concepts=len(obj.concepts),
                   attempts=rec.get("attempts", 1),
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
        return rec


# ==========================================================================
# 6.  The run — translate.run()'s frame around the executor
# ==========================================================================

def prepare(cfg, args, client_factory=None):
    """Everything translate.run() does before its per-clause loop, in the
    same order: selection, prompt build, provider, only-stale filter, cost
    ESTIMATE, dry-run exit, cost GATE, client, run directory, version block,
    graveyard cap — the cap check runs before any dispatch state, scheduler
    or executor exists, so it fires before any spend and before any executor
    work. Returns a RunContext, or an int exit code for the dry-run path."""
    rows = T.load_corpus(cfg)
    known_ids = {r[cfg["corpus"]["id_key"]] for r in rows}
    picked = T.select(rows, cfg, args)
    system = T.build_system(cfg)
    T.validate_format_forcing(cfg)
    jobs = []
    for r in picked:
        user, found, unres = T.build_user(r, rows, cfg)
        jobs.append({"row": r, "user": user,
                     "xrefs": [x[cfg["corpus"]["id_key"]] for x in found],
                     "xrefs_unresolved": unres})

    prov = T.resolve_provider(cfg, args)
    max_attempts = int((cfg.get("repair") or {}).get("max_attempts", 1))
    idk = cfg["corpus"]["id_key"]

    _version_report, _honoured = None, []
    if getattr(args, "only_stale", False):
        jobs, _version_report, _honoured = T.stale_filter(
            jobs, cfg, args, prov, system, idk, cfg["corpus"]["text_key"])
        if not jobs:
            print("nothing is stale — nothing to translate, nothing sent.")
            return 0

    est, in_tok, out_tok = T.estimate_cost(
        system, [j["user"] for j in jobs], prov, cfg,
        max_attempts=max_attempts)

    ex = cfg.get("execution") or {}
    print(f"provider     : {prov.name}  ({prov.model})")
    print(f"execution    : {ex.get('mode')}  "
          f"(concurrent_n={ex.get('concurrent_n')}, "
          f"batch_min_pending={ex.get('batch_min_pending')})")
    print(f"clauses      : {len(jobs)}  "
          f"[{', '.join(j['row'][idk] for j in jobs[:8])}"
          f"{' …' if len(jobs) > 8 else ''}]")
    print(f"cost (worst) : ${est:.4f}   "
          f"(~{in_tok:,} in, {out_tok:,} out at full max_tokens)   "
          f"ceiling ${float(cfg['cost']['max_cost_usd']):.2f}")

    if not getattr(args, "live", False):
        print("\nDRY RUN — nothing was sent. Add --live to spend.")
        return 0

    T.cost_gate(est, cfg)

    client = (client_factory or T.make_client)(prov, cfg)
    # the F3 batch submit gate and the batch collector both read these off
    # the client; translate's own Client carries neither
    if getattr(client, "p", None) is None:
        client.p = prov
    if getattr(client, "max_cost_usd", None) is None:
        client.max_cost_usd = float(cfg["cost"]["max_cost_usd"])

    outdir = T.resolve_outdir(cfg, prov)
    os.makedirs(outdir)
    print(f"\nwriting to {outdir}")
    with open(os.path.join(outdir, "prompt_system.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(system)

    _gy = cfg.get("graveyard") or {}
    _gy_dir = T.rel(_gy.get("dir", "repair_graveyard"))
    _schema_src = version.schema_source()
    _model, _temp, _params = version.model_params(cfg, prov)
    _prov_hash = gy.provenance_hash(system, _model, _temp, params=_params)
    _version_block = {
        "schema_sha": T.sha16(_schema_src),
        "provenance_hash": _prov_hash,
        "provenance_params": _params,
        "stamp_version": 1,
        "waivers_honoured": _honoured,
        "only_stale": _version_report,
    }
    if _gy.get("cap"):
        # BEFORE any dispatch state, executor or spend — run()'s own refusal
        # to deepen an unexamined pile, at the same point in the order
        gy.check_cap(_gy_dir, _gy["cap"])

    return RunContext(cfg, prov, client, system, outdir, jobs, known_ids,
                      max_attempts, _gy, _gy_dir, _schema_src, _model,
                      _temp, _params, _version_block)


def execute(ctx, mode, exec_cfg, transport=None):
    """Build the flat table and drive it through the chosen executor."""
    states = [ClauseState(ctx, i, j) for i, j in enumerate(ctx.jobs)]
    sched = FlatScheduler(ctx, states)
    driver = _Driver(ctx.cfg, ctx.client, ctx.system, ctx.outdir)
    ex = build_executor(mode, driver, exec_cfg, transport=transport)
    try:
        ex.run(sched)
    finally:
        ctx.flush()

    results = [r for r in ctx.results if r is not None]
    n_tr = sum(1 for r in results if r.get("status") == "translated")
    n_ab = sum(1 for r in results if r.get("status") == "abstained")
    n_abr = sum(1 for r in results
                if r.get("status") == "abstained_under_repair")
    print(f"\n{n_tr} translated, {n_ab} abstained, "
          f"{n_abr} abstained under repair, "
          f"{ctx.failures} failed. Raw responses kept in {ctx.outdir}")
    other = len(results) - n_tr - n_ab - n_abr - ctx.failures
    if other:
        print(f"⚠️ {other} of {len(results)} result(s) carry a status this "
              f"summary does not partition on. Statuses seen: "
              f"{sorted({str(r.get('status')) for r in results})}")
    print("⛔ NOTHING here has been validated. "
          "No compile, no link, no read-back.")
    spent = getattr(ctx.client, "spent_usd", 0.0)
    if spent:
        print(T.spend_invisibility_warning(
            ctx.prov, spent, getattr(ctx.client, "calls", 0)))
    return 1 if ctx.failures else 0


def run_exec(cfg, args, client_factory=None, transport=None):
    """Entry point: the same contract as translate.run(), plus the executor.
    `transport` exists so tests (and a future non-together batch endpoint)
    can substitute the Batch API transport; None = dispatch_core's curl
    transport."""
    mode, exec_cfg = execution_config(cfg)
    ctx = prepare(cfg, args, client_factory)
    if isinstance(ctx, int):
        return ctx
    return execute(ctx, mode, exec_cfg, transport=transport)


# ==========================================================================
# 7.  CLI
# ==========================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="opt-in concurrent/batch execution for translate.py "
                    "(serial = run translate.py itself)")
    ap.add_argument("--config", default=T.DEFAULT_CONFIG)
    ap.add_argument("--clause", nargs="*", default=None)
    ap.add_argument("--section", default=None)
    ap.add_argument("--kinds", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", dest="max_tokens", type=int, default=None)
    ap.add_argument("--only-stale", dest="only_stale", action="store_true")
    ap.add_argument("--waivers", default=None)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--show-prompt", dest="show_prompt", type=int, default=0)
    args = ap.parse_args(argv)
    try:
        cfg = T.load_config(args.config)
        return run_exec(cfg, args)
    except (T.Phase1Error, gy.GraveyardError) as exc:
        # gy.GraveyardError by name (routing-gap audit F10): it cannot
        # subclass Phase1Error (import direction), and the cap refusal is
        # a usage error and exit 2, not a traceback.
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
