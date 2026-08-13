#!/usr/bin/env python3
"""Shared execution core for the graph-build driver.

BATCH_DESIGN.md "Post-review resolution": one shared core (DispatchState +
Scheduler + in-flight manifest) with pluggable executors -- `serial` is the
reference re-expression of Driver.call/Driver.build, `concurrent` a bounded
live worker pool, `batch` the Batch-API submit/poll/collect loop, engaged by
the `batch_min_pending` ready-queue threshold with a starvation fallback to
live. recurse_driver's own serial path stays untouched; this module must
reproduce its semantics exactly (pinned by test_dispatch_core.py's
prompt-byte and artifact-byte equivalence tests).

Review findings implemented here (batch_design_review.md):
  F1  DispatchState persists everything Driver.call held in locals
      (transcript, repair round, restart flag, per-dispatch spend);
      Scheduler is the explicit dependency table Driver.build's call
      stack could not express.
  F2  InFlightManifest: atomic per-job records, swept BEFORE any enqueue on
      resume, so a killed process never double-pays a submitted batch and
      recovered results reach the ledger at collection.
  F3  Worst-case spend gate at batch submit (full input rate, full
      max_tokens out, no cache credit -- the ledger doctrine).
  F4  response_format is built PER REQUEST in the batch path; the mutable
      client-global reply_schema is never used to build a batch body.
  F5  Batch results are classified by DATA SHAPE (ok / http_error /
      truncated / missing-from-output), never by exception-string matching;
      non-ok items requeue as live, successes are written to disk before a
      poison request stops the run.
"""
import json
import os
import re
import subprocess
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))

import recurse_driver as R  # noqa: E402  (validators, schemas, prompts)

T = R.T

PENDING, DONE, FAILED = "pending", "done", "failed"


def _safe_id(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s) or "root"


# ---------------------------------------------------------------- DispatchState
class DispatchState:
    """One dispatch's lifecycle: draw -> validate/autofix -> repair-round-k ->
    done|failed. Replaces Driver.call's local variables (review F1) so any
    executor -- including one holding eight dispatches in flight or a batch
    collector reading a results file -- can step it.

    Step interface:
      next_request() -> message array (role/content dicts) or None
      feed(envelope) -> state transition on a successful completion
      feed_failure(kind, detail) -> state transition on a transport failure
                                    delivered as DATA (review F5)

    Every threshold, message and ordering below mirrors Driver.call verbatim;
    a deliberate difference would break the equivalence pins.
    """

    def __init__(self, key, kind, wdir, user, validate, schema, cfg, out,
                 tally=None, on_success=None):
        self.key, self.kind, self.wdir = key, kind, wdir
        self.user, self.validate, self.schema = user, validate, schema
        self.cfg, self.out, self.tally = cfg, out, tally
        self.on_success = on_success
        # Driver.call's exact defaults -- per-dispatch budget is Matt's
        # 2026-08-11 ruling; the repair count is cfg `max_repairs`.
        self.budget = cfg.get("per_dispatch_usd", 0.30)
        self.max_repairs = cfg.get("max_repairs", 2)
        self.out_cap = cfg.get("model", {}).get("max_tokens", 16384)
        # a list user is a pre-seeded transcript (transcript_continuity's
        # [D-user, D-reply, U-user] reconstruction) -- Driver.call's own
        # `list(user) if isinstance(user, list)` branch (delta review D1)
        self.transcript = (list(user) if isinstance(user, list)
                           else [{"role": "user", "content": user}])
        self.repair_round = 0
        self.restarted = False          # one fresh restart, like call()'s flag
        self.on_dense = None            # dense leaf -> division morph (below)
        self.spent = 0.0
        self.status = PENDING
        self.result = None
        self.error = None
        self.errs = []

    # -- step interface ----------------------------------------------------
    def next_request(self):
        if self.status != PENDING:
            return None
        return list(self.transcript)

    def can_restart(self):
        """Fresh-restart is legal only from a laden repair transcript, once
        (Driver.call: the transcript inflates the reasoning burn; a fresh
        draw completes where the laden one cannot)."""
        return self.repair_round >= 1 and not self.restarted

    def feed(self, env):
        # measured cost rides in the envelope (live: _send's cost_usd; batch:
        # response_envelope's usage.cost_usd); the budget is checked between
        # draws exactly as Driver.call's _over() does
        cost = (env.get("cost_usd")
                or (env.get("usage") or {}).get("cost_usd") or 0.0)
        self.spent += cost
        if self.tally:
            self.tally(env)
        # (Driver.call checks _over() BEFORE _tally on the first draw and
        # after it on repairs; the core always tallies first. Cache-counter
        # cosmetics only -- accepted by name, dispatch_core_review.md R9.4.)
        if self.spent > self.budget:
            return self._fail(self._budget_msg())
        obj, errs = self._attempt(env)
        if not errs:
            self.result, self.status = obj, DONE
            return
        text = env.get("text", "")
        # oversize short-circuit: first draw only, same threshold as call().
        # D6 stage 1 wired live (ds5 2026-08-12: a COMPLETE 123-node dup-loop
        # reply -- 108 repeats of one establishes on a 177-line span -- was
        # mislabeled "truncated" and hard-failed the build). A MALFUNCTION
        # resamples fresh once; only a DENSE span is unfixable at this cap.
        if self.repair_round == 0 and len(text) > self.out_cap * 3:
            self._bury(text, errs)
            if (R.classify_cap_overflow(text) == "malfunction"
                    and not self.restarted):
                self.restarted = True   # once, sharing feed_failure's flag
                self.spent = 0.0        # budget re-bases, as feed_failure
                return                  # transcript still fresh: resample
            if self.on_dense is not None:
                # Matt's ruling 2026-08-12: MORPH into the division dispatch
                # for the same span -- the normal recursion absorbs a dense
                # leaf (and a post-resample malfunction: dividing shrinks
                # the span that triggered it). Rejected by name: the D6
                # stages 2-3 mechanical boundary bisect. A None replacement
                # means the cached division was routed instead (review
                # finding 1): retire this state quietly as DONE-no-op.
                repl = self.on_dense()
                if repl is None:
                    self.on_success = lambda _g: None
                    self.result, self.status = None, DONE
                    return
                self._morph(repl)
                return
            return self._fail(
                "oversize first draw (dense span, or malfunction resample "
                "already spent) at max_tokens; reduce leaf_max_lines "
                "or raise model.max_tokens rather than retrying")
        if self.repair_round >= 1:
            self._bury(text, [f"repair round {self.repair_round}"]
                       + [str(e) for e in errs])
            # a repair reply byte-identical to the previous one means the
            # transcript adds no information (ds5 2026-08-12: unwind c3_c1
            # repeated one 3,127-byte reply r1..r3, an unfixable loop);
            # fresh restart, once
            if (len(self.transcript) >= 2
                    and text == self.transcript[-2].get("content")
                    and self.can_restart()):
                self.transcript = (list(self.user)
                                   if isinstance(self.user, list)
                                   else [{"role": "user",
                                          "content": self.user}])
                self.repair_round, self.errs = 0, []
                self.restarted = True
                self.spent = 0.0
                return
        if self.repair_round >= self.max_repairs:
            return self._fail(
                f"call failed after {self.max_repairs} repair "
                "round(s): " + "; ".join(str(e) for e in errs[:5]))
        # ACCUMULATING repair transcript, byte-identical to Driver.call's
        self.transcript.append({"role": "assistant", "content": text})
        self.transcript.append({"role": "user", "content":
                                ("Your reply failed mechanical checks:\n- "
                                 + "\n- ".join(str(e) for e in errs)
                                 + "\nReturn the corrected COMPLETE JSON "
                                   "object and nothing else.")})
        self.repair_round += 1
        self.errs = errs

    def bill(self, cost):
        """Measured billed spend from a draw that RAISED in transport
        (review R1). Driver.call's _over() reads `client.spent_usd`, which
        translate.py's `_send` increments via `_log_usage` BEFORE the
        truncation/emptiness guards raise -- so every TRUNCATED or empty
        draw is billed and counted against the per-dispatch budget. The
        executor calls this with the measured `spent_usd` delta of a failed
        attempt so the state's budget sees exactly the same money."""
        if not cost:
            return
        self.spent += cost
        if self.status == PENDING and self.spent > self.budget:
            self._fail(self._budget_msg())

    def _budget_msg(self):
        return (f"dispatch exceeded its spend budget "
                f"(${self.spent:.2f} > ${self.budget:.2f} per_dispatch_usd). "
                f"Repeated expensive draws mean this dispatch needs a "
                f"DIAGNOSIS, not more retries -- see health.jsonl and "
                f"the failed/ dir")

    def _morph(self, other):
        """Become `other` (the division dispatch for this span) in place --
        the executor holds a reference to THIS object, so the replacement
        must happen by mutation. Fresh dispatch semantics: repair state,
        restart flag and spent all reset."""
        for a in ("key", "kind", "wdir", "user", "validate", "schema",
                  "on_success"):
            setattr(self, a, getattr(other, a))
        self.transcript = list(other.transcript)
        self.repair_round, self.errs = 0, []
        self.restarted = False
        self.spent = 0.0
        self.on_dense = None

    def feed_failure(self, kind, detail):
        """Transport failure as data (review F5). `truncated` from a laden
        repair transcript restarts the dispatch fresh (once); anything else
        is terminal for this state -- bounded retries live in the executor."""
        if kind == "truncated" and self.can_restart():
            self.transcript = (list(self.user)
                               if isinstance(self.user, list)
                               else [{"role": "user", "content": self.user}])
            self.repair_round, self.errs = 0, []
            self.restarted = True
            self.spent = 0.0   # call()'s recursive restart re-bases spent0
            return
        self._fail(detail)

    # -- internals ---------------------------------------------------------
    def _attempt(self, env):
        # mirror of Driver._attempt (review F12: any exception is repairable)
        try:
            obj = R.parse_json_reply(env["text"])
            return obj, self.validate(obj)
        except Exception as exc:            # noqa: BLE001
            return None, [f"reply failed to parse/validate: {exc!r:.200}"]

    def _bury(self, text, errs):
        # Driver._bury plus the dispatch key in the filename: a batch
        # collector burying N failures in one loop would collide on
        # millisecond stamps alone (review F5's _bury note). The filename
        # divergence from Driver's bare-milliseconds stamp is deliberate --
        # accepted by name, dispatch_core_review.md R9.5.
        d = os.path.join(self.out, "failed")
        os.makedirs(d, exist_ok=True)
        stamp = (f"{int(time.time() * 1000)}_{_safe_id(self.key)}"
                 f"_r{self.repair_round}")
        R.write_json(os.path.join(d, stamp + ".json"),
                     {"errors": [str(e) for e in errs],
                      "reply": text, "user_head": self.user[:2000]})

    def _fail(self, msg):
        self.status, self.error = FAILED, msg

    def custom_id(self):
        """Deterministic provider custom_id (review F2): derived from the
        dispatch identity so a manifest sweep can route recovered results
        with no in-memory state."""
        return f"{_safe_id(self.key)}-r{self.repair_round}"


# -------------------------------------------------------------------- Scheduler
class Scheduler:
    """The tree as an explicit dependency table (review F1): children-of and
    unwind-waits-on, replacing Driver.build's call stack. The ready list is a
    LIFO stack and children are entered in reverse, so a SerialExecutor visits
    dispatches in exactly Driver.build's DFS order -- which is what lets the
    order-consuming MockClient and mock_replies.json be reused unchanged
    (review F9's constraint, met by preserving order rather than re-keying).

    Artifact/resume semantics are inviolable: every phase checks its
    division.json / graph.json before a dispatch is ever created.
    """

    def __init__(self, driver):
        self.drv = driver
        self.ready = []                 # stack of ready DispatchState
        self.root_result = None
        self.lock = threading.Lock()    # held by concurrent executors around
        #                                 pop/complete (scheduler mutation)

    # -- executor surface --------------------------------------------------
    def start(self, lo, hi, seeds, wdir):
        self._enter(lo, hi, seeds, wdir, 0, parent=None)

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
        """A finished dispatch commits its artifact and may make parents or
        children ready. on_success raises on application failure (unwind),
        matching Driver's behavior."""
        state.on_success(state.result)

    # -- dependency table --------------------------------------------------
    def _enter(self, lo, hi, seeds, wdir, depth, parent):
        if depth > R.DEPTH_MAX:
            raise T.Phase1Error(
                f"depth {depth} exceeds DEPTH_MAX at {lo}-{hi}; the divisions "
                f"leading here are cached -- delete {wdir} to re-divide")
        task = {"lo": lo, "hi": hi, "seeds": seeds, "wdir": wdir,
                "depth": depth, "parent": parent}
        if (hi - lo + 1) <= self.drv.leaf_max:
            self._want_leaf(task)
        else:
            self._want_division(task)

    def _key(self, kind, task):
        rel = os.path.relpath(task["wdir"], self.drv.out)
        return f"{kind}:{'' if rel == '.' else rel}"

    def _division_state(self, task):
        """The division DispatchState for `task` -- built here so a dense
        leaf can MORPH into it (Matt's ruling 2026-08-12: a dense leaf
        re-enters the normal division path, no bespoke bisect)."""
        art = os.path.join(task["wdir"], "division.json")
        lo, hi, seeds = task["lo"], task["hi"], task["seeds"]
        # extra / _fix / validator: SHARED with Driver.divide (delta review
        # D1/D7 -- the third copy of the D-extra string lived here)
        extra = R.divide_extra()

        def _fix(o):
            if isinstance(o, dict):
                o["_span_lo"], o["_span_hi"] = lo, hi
            return R.autofix_division(o, seeds)

        st = DispatchState(
            self._key("D", task), "D", task["wdir"],
            self.drv.dispatch_block("D", lo, hi, seeds, extra),
            lambda o: R.validate_division(_fix(o), lo, hi, seeds),
            ("division", R.DIVISION_SCHEMA), self.drv.cfg, self.drv.out,
            tally=self.drv._tally)

        def done(d):
            os.makedirs(task["wdir"], exist_ok=True)
            R.write_json(art, d)
            self._division_done(task, d)
        st.on_success = done
        return st

    def _want_division(self, task):
        art = os.path.join(task["wdir"], "division.json")
        if os.path.exists(art):
            self._division_done(task, json.load(open(art)))
            return
        self.ready.append(self._division_state(task))

    def _division_done(self, task, d):
        if d.get("decision") == "leaf":
            if task.get("dense"):
                # a dense-morphed task answered decision="leaf": redrawing
                # the leaf would overflow the same cap forever
                raise T.Phase1Error(
                    f"dense span {task['lo']}-{task['hi']} was re-dispatched "
                    f"as Phase D and the model answered decision='leaf'; "
                    f"reduce leaf_max_lines for this region")
            self._want_leaf(task)
            return
        task["division"] = d
        kids = d["children"]
        task["child_graphs"] = [None] * len(kids)
        task["pending"] = len(kids)
        # reverse entry: the LIFO ready stack then pops c1 first (DFS parity
        # with Driver.build, which the equivalence pins depend on)
        for i, c in reversed(list(enumerate(kids, 1))):
            clo, chi = c["span"]
            self._enter(clo, chi, d.get("seed_vocabulary", []),
                        os.path.join(task["wdir"], f"c{i}"),
                        task["depth"] + 1, parent=(task, i - 1))

    def _want_leaf(self, task):
        art = os.path.join(task["wdir"], "graph.json")
        if os.path.exists(art):
            self._task_done(task, json.load(open(art)))
            return
        lo, hi, wdir = task["lo"], task["hi"], task["wdir"]
        # extra / schema / derive: SHARED with Driver.leaf (delta review D1:
        # this path ignored derive_uncovered -- ds2 validation semantics on
        # a ds3 build)
        extra, schema, derive = R.leaf_dispatch(lo, hi, self.drv.cfg)
        st = DispatchState(
            self._key("L", task), "L", wdir,
            self.drv.dispatch_block("L", lo, hi, task["seeds"], extra),
            lambda o: R.validate_leaf(o, lo, hi, self.drv.lines,
                                      derive_uncovered=derive),
            schema, self.drv.cfg, self.drv.out,
            tally=self.drv._tally)

        def done(g):
            os.makedirs(wdir, exist_ok=True)
            R.write_json(art, g)
            self.drv._health(g, lo, hi, "leaf", wdir)
            self._task_done(task, g)
        st.on_success = done

        def dense():
            # Matt's ruling 2026-08-12: the dense leaf re-enters the normal
            # division path (Driver.build's fallback, core-side).
            # ⛔ CACHE FIRST (pre-ds6 review finding 1): a resumed run whose
            # dense subtree already divided must honor the stored
            # division.json -- redrawing it re-pays a call and can silently
            # re-span children whose graph.json artifacts belong to the OLD
            # division. None tells feed() to retire this state quietly; the
            # cached division routes through _division_done as always.
            task["dense"] = True
            print(f"    (dense leaf {lo}-{hi}: recursing via Phase D)")
            dart = os.path.join(task["wdir"], "division.json")
            if os.path.exists(dart):
                self._division_done(task, json.load(open(dart)))
                return None
            return self._division_state(task)
        st.on_dense = dense
        self.ready.append(st)

    def _task_done(self, task, g):
        parent = task["parent"]
        if parent is None:
            self.root_result = g
            return
        ptask, slot = parent
        ptask["child_graphs"][slot] = g
        ptask["pending"] -= 1
        if ptask["pending"] == 0:
            self._want_unwind(ptask)

    def _want_unwind(self, task):
        art = os.path.join(task["wdir"], "graph.json")
        if os.path.exists(art):
            self._task_done(task, json.load(open(art)))
            return
        lo, hi, wdir = task["lo"], task["hi"], task["wdir"]
        division, children = task["division"], task["child_graphs"]
        # mechanics + prompt: verbatim from Driver.unwind
        (nodes, uncovered, provides, dangling, dup,
         user) = R.unwind_inputs(division, children, lo, hi,
                                 self.drv.cfg)
        # continuity + grammar caps: SHARED with Driver.unwind (delta review
        # D1: this path sent a bare U string and the uncapped static schema
        # while serial sent the [D-user, D-reply, U-user] transcript and
        # unwind_schema's protocol-derived maxItems)
        if self.drv.cfg.get("transcript_continuity"):
            user = R.continuity_transcript(self.drv, division, lo, hi,
                                           task["seeds"], user)
        st = DispatchState(
            self._key("U", task), "U", wdir, user,
            lambda o: R.apply_decisions(
                json.loads(json.dumps(nodes)),
                R.autofix_unwind_merges(o, nodes, provides, lo, hi,
                                        self.drv.lines),
                provides, lo, hi, self.drv.lines)[1],
            R.unwind_schema(len(dangling), len(nodes),
                            **R.enum_pools(self.drv.cfg, nodes, provides,
                                           dangling)),
            self.drv.cfg, self.drv.out, tally=self.drv._tally)

        def done(dec):
            log, errs = R.apply_decisions(nodes, dec, provides, lo, hi,
                                          self.drv.lines)
            if errs:
                raise T.Phase1Error("unwind decision application failed: "
                                    + "; ".join(errs[:5]))
            g = {"nodes": nodes, "uncovered": uncovered,
                 "judgment_calls": dec.get("judgment_calls", []),
                 "cross_link_report": dec.get("cross_link_report", []),
                 "unwind_log": log, "brief_sha": self.drv.brief_sha}
            if dec.get("_dropped_merges"):
                g["dropped_merges"] = dec["_dropped_merges"]
            os.makedirs(wdir, exist_ok=True)
            R.write_json(art, g)
            self.drv._health(g, lo, hi, "unwind", wdir,
                             promises=R.broken_promises(division, children))
            self._task_done(task, g)
        st.on_success = done
        self.ready.append(st)


# ------------------------------------------------------------ InFlightManifest
class InFlightManifest:
    """Atomic per-job in-flight records (review F2). An entry exists from the
    moment work is committed to the provider until its results are written or
    re-enqueued; a killed process therefore leaves a record, never a paid but
    invisible batch. sweep() SURFACES orphans -- it never deletes them, so
    the caller must reconcile-or-requeue before clear()."""

    def __init__(self, out):
        self.dir = os.path.join(out, "inflight")
        os.makedirs(self.dir, exist_ok=True)

    def sweep(self):
        out = []
        for fn in sorted(os.listdir(self.dir)):
            if fn.endswith(".json"):
                out.append((fn[:-5], json.load(
                    open(os.path.join(self.dir, fn)))))
        return out

    def record(self, name, entry):
        # write_json is tmp+rename (recurse_driver review F13): a kill mid-
        # record never leaves a half manifest that wedges the sweep
        R.write_json(os.path.join(self.dir, name + ".json"), entry)

    def clear(self, name):
        p = os.path.join(self.dir, name + ".json")
        if os.path.exists(p):
            os.remove(p)
        # review R10: the submitted .jsonl input file is disk-only residue
        # once the job's record is cleared; drop it with the record
        # (never touches <name>.recovered -- that file outlives clear() by
        # design, review R3)
        q = os.path.join(self.dir, name + ".jsonl")
        if os.path.exists(q):
            os.remove(q)


# ------------------------------------------------------------------- executors
_TRANSIENT_MARKS = ("TRUNCATED", "timed out", "HTTP 5", "Connection",
                    "unavailable", "urlopen error", "Errno", "HTTP 402", "HTTP 429",)

#: sentinel snapshot: "read the per-thread billed accumulator" (R1 concurrent)
_TLS_BILLED = object()


class SerialExecutor:
    """The reference executor: Driver.call's transport ladder around
    DispatchState, one dispatch at a time, DFS order via the scheduler.
    Production `serial` mode does NOT run through this class (recurse_driver's
    own path is untouched); this is the equivalence baseline and the live
    fallback the batch executor requeues into."""

    def __init__(self, driver):
        self.drv, self.client = driver, driver.client

    def run(self, sched):
        while sched.root_result is None:
            state = sched.pop_ready()
            if state is None:
                raise T.Phase1Error("scheduler stalled: no ready dispatch "
                                    "and no root result")
            self.run_one(state)
            if state.status != DONE:
                raise T.Phase1Error(state.error)
            sched.complete(state)
        return sched.root_result

    def run_one(self, state):
        """Draw/repair loop for one dispatch, to DONE or FAILED."""
        while True:
            req = state.next_request()
            if req is None:
                return
            try:
                env = self._ladder(state, req)
            except T.ProviderError as exc:
                # laden-repair-transcript truncation -> one fresh restart
                # (Driver.call's _restarted path, verbatim semantics)
                if "TRUNCATED" in str(exc) and state.can_restart():
                    print("    (repair transcript truncating; restarting "
                          "dispatch fresh)")
                    state.feed_failure("truncated", str(exc))
                    continue
                raise
            state.feed(env)
            if state.status == FAILED:
                return

    def _ladder(self, state, req):
        """Driver._complete verbatim: schema-rejection downgrade plus up to 6
        bounded transient retries with backoff. One deliberate addition
        (review R1): every attempt's MEASURED billed spend -- including a
        draw that raises after billing, exactly what Driver.call's _over()
        sees via the client.spent_usd delta -- is billed to the state, and a
        budget already blown stops the ladder instead of paying more
        retries. Driver.call would pay for the retries and only fail after
        the next successful draw; stopping earlier is the cheaper direction
        and is the R1 ruling's whole point."""
        for attempt in range(7):
            snap = self._spend_snapshot()
            try:
                return self._send(state, req)
            except Exception as exc:        # noqa: BLE001
                # R1: a billed-then-raised draw (TRUNCATED, empty) is real
                # money; _log_usage ran before the guard raised.
                state.bill(self._spend_since(snap))
                detail = str(exc)
                if (state.schema
                        and not getattr(self.client, "_schema_rejected", True)
                        and ("response_format" in detail
                             or "json_schema" in detail)):
                    self.client._schema_rejected = True
                    continue
                if state.status == FAILED:
                    # budget blown by billed failed draws: fail loudly with
                    # the budget diagnosis, not another paid retry
                    raise T.Phase1Error(state.error)
                transient = any(m in detail for m in _TRANSIENT_MARKS)
                # HTTP 402 rides a SHORT ladder (steps-1-4 audit 2026-08-12,
                # BUG 2): as a full transient it burned 630s of backoff on a
                # terminal credit exhaustion. It stays retryable at all --
                # rejected alternative, by name: terminal 402 -- because
                # together.ai 402s flapped for ~minutes after mid-campaign
                # credit top-ups; two retries (~90s) ride out a flap and
                # fail fast on real exhaustion.
                if "HTTP 402" in detail and attempt >= 2:
                    transient = False
                if transient and attempt < 6:
                    wait = min(30 * (attempt + 1), 180)
                    print(f"    (transient [{detail[:50]}], retry "
                          f"{attempt + 1}/6 in {wait}s)")
                    time.sleep(wait)
                    continue
                raise

    # R1 measurement surface: the serial executor owns the whole client, so
    # the client-global spent_usd delta IS the attempt's billed cost.
    def _spend_snapshot(self):
        return getattr(self.client, "spent_usd", None)

    def _spend_since(self, snap):
        if snap is None:
            return 0.0
        return max(getattr(self.client, "spent_usd", 0.0) - snap, 0.0)

    def _phase_cap(self, state):
        """Driver.call's per-phase output cap lookup, keyed on the schema
        name (delta review D1: the caps never engaged in ANY core mode --
        division 8K / leaf 24K / unwind 8K existed only on the untouched
        serial path)."""
        if not state.schema:
            return None
        return self.drv.cfg.get("phase_max_tokens",
                                self.drv.PHASE_MAX_TOKENS).get(
                                    state.schema[0])

    def _send(self, state, req):
        # Driver.call's contract: set reply_schema + max_tokens_override
        # when the client has the slots, complete() for the first draw,
        # complete_messages() for repairs (and for a continuity transcript)
        if hasattr(self.client, "reply_schema"):
            self.client.reply_schema = state.schema
        if state.schema and hasattr(self.client, "max_tokens_override"):
            self.client.max_tokens_override = self._phase_cap(state)
        if len(req) == 1:
            return self.client.complete(self.drv.brief, req[0]["content"])
        return self.client.complete_messages(self.drv.brief, req)


class ConcurrentExecutor(SerialExecutor):
    """Bounded live concurrency: a threading semaphore of N whole-dispatch
    workers (each worker runs the full draw/repair loop -- review F1's state
    machine is what makes >1 of these coexist). The in-flight manifest covers
    the killed-with-N-live-calls resume blind spot F2 names for this mode."""

    def __init__(self, driver, n=4, manifest=None):
        super().__init__(driver)
        self.n = max(int(n), 1)
        self.manifest = manifest or InFlightManifest(driver.out)
        # F4's state problem, live-concurrency edition: reply_schema is a
        # one-slot client global. The body is built under a short lock with
        # the slot set, and the HTTP round-trip runs outside it.
        self._body_lock = threading.Lock()
        self._ledger_lock = threading.Lock()
        self._tls = threading.local()
        if hasattr(self.client, "_log_usage"):
            orig = self.client._log_usage
            # idempotence guard (review R9.3): building two executors on one
            # client must not stack a wrapper on a wrapper
            if not getattr(orig, "_dc_locked", False):
                def _locked(env, _o=orig, _l=self._ledger_lock, _s=self):
                    # R1 concurrent: the client-global spent_usd delta is
                    # racy across N workers, so the per-attempt billed cost
                    # is captured HERE, inside the lock, into the calling
                    # thread's accumulator (_log_usage runs on the worker
                    # thread that made the call).
                    with _l:
                        before = getattr(_s.client, "spent_usd", None)
                        r = _o(env)
                        if before is not None and getattr(
                                _s._tls, "billed", None) is not None:
                            _s._tls.billed += max(
                                getattr(_s.client, "spent_usd", 0.0)
                                - before, 0.0)
                    return r
                _locked._dc_locked = True
                self.client._log_usage = _locked   # instance attr shadows

    def _spend_snapshot(self):
        # R1 concurrent: measure via the locked _log_usage wrapper's
        # per-thread accumulator, never the racy client-global delta
        if getattr(self.client, "_log_usage", None) is not None:
            self._tls.billed = 0.0
            return _TLS_BILLED
        return super()._spend_snapshot()

    def _spend_since(self, snap):
        if snap is _TLS_BILLED:
            billed, self._tls.billed = getattr(self._tls, "billed", 0.0), None
            return billed
        return super()._spend_since(snap)

    def _send(self, state, req):
        c = self.client
        if hasattr(c, "_body") and hasattr(c, "_send"):
            # NOTE (review R9.1, recorded): calling _body/_send directly
            # bypasses Client._retrying, so model.resample_truncation extra
            # draws are inert in concurrent mode; the ladder's bounded
            # transient retries cover the same failure class.
            with self._body_lock:
                c.reply_schema = state.schema
                if state.schema and hasattr(c, "max_tokens_override"):
                    # D1: per-phase caps engage in concurrent mode too;
                    # _body reads the slot inside this same lock
                    c.max_tokens_override = self._phase_cap(state)
                if len(req) == 1:
                    body = c._body(self.drv.brief, req[0]["content"])
                else:
                    body = c._body_messages(self.drv.brief, req)
            return c._send(body)
        if hasattr(c, "reply_schema"):
            # review R9.2: the serial fallback would mutate the client-global
            # reply_schema slot from N threads with no lock. No current
            # client has the slot without _body/_send; refuse rather than
            # race if one ever does.
            raise T.Phase1Error(
                "concurrent executor: client exposes reply_schema but not "
                "_body/_send; the unlocked serial fallback would race the "
                "schema slot across workers (dispatch_core_review R9.2)")
        return super()._send(state, req)

    def run(self, sched):
        # orphans from a killed run are informational here: live calls leave
        # no provider-side result, and artifact-resume already covers them
        for name, entry in self.manifest.sweep():
            print(f"  (stale in-flight record {name}: {entry.get('key')} -- "
                  f"artifact-resume covers it)")
            self.manifest.clear(name)
        sem = threading.Semaphore(self.n)
        errors, threads = [], []
        stop = threading.Event()

        def worker(state):
            try:
                mname = _safe_id(state.key)
                self.manifest.record(mname, {
                    "key": state.key, "kind": state.kind,
                    "wdir": os.path.relpath(state.wdir, self.drv.out),
                    "round": state.repair_round})
                self.run_one(state)
                if state.status != DONE:
                    raise T.Phase1Error(state.error)
                with sched.lock:
                    sched.complete(state)
                self.manifest.clear(mname)
            except Exception as exc:        # noqa: BLE001
                errors.append(exc)
                stop.set()
            finally:
                sem.release()

        while True:
            with sched.lock:
                if stop.is_set() or sched.root_result is not None:
                    break
                state = sched.pop_ready()
            if state is None:
                if any(t.is_alive() for t in threads):
                    time.sleep(0.01)
                    continue
                break
            sem.acquire()
            # review R6: a worker may have hit a fatal error while the main
            # loop was blocked on the semaphore; starting one more paid
            # dispatch after the run has decided to abort is money the F5
            # story does not cover. Re-check, push the state back, stop.
            if stop.is_set():
                sem.release()
                with sched.lock:
                    sched.requeue(state)
                break
            t = threading.Thread(target=worker, args=(state,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        if errors:
            # F5's poison ordering: workers that finished have already
            # written their artifacts; only then does the run stop
            raise errors[0]
        if sched.root_result is None:
            raise T.Phase1Error("scheduler stalled: no ready dispatch "
                                "and no root result")
        return sched.root_result


class CurlTransport:
    """Batch-endpoint transport via curl subprocess. Ground: together's WAF
    intermittently 403s stdlib urllib on files/upload and /v1/batches while
    accepting curl, and the multipart upload only ever worked through curl's
    canonical encoding (EXPERIMENTS.md 'BATCH SLA PROBE RESULT'; re-checked
    2026-08-11 with a $0 GET: both passed that day, curl kept for the
    recorded intermittency and for the upload). curl resolves via PATH, which
    is also what lets the tests substitute a stub."""

    def __init__(self, base_url, api_key):
        self.base = base_url.rstrip("/")
        self.key = api_key

    def _run(self, args):
        r = subprocess.run(["curl", "-sS", *args],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise T.ProviderError(f"curl failed: {r.stderr[:300]}")
        return r.stdout

    def _json(self, args):
        out = self._run(args)
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            raise T.ProviderError(f"batch endpoint returned non-JSON: "
                                  f"{out[:200]!r}") from exc

    def upload(self, path, name):
        j = self._json(["-X", "POST", f"{self.base}/files/upload",
                        "-H", f"Authorization: Bearer {self.key}",
                        "-F", "purpose=batch-api",
                        "-F", f"file_name={name}",
                        "-F", f"file=@{path}"])
        fid = j.get("id") or j.get("file_id") or (j.get("data") or {}).get("id")
        if not fid:
            raise T.ProviderError(f"upload returned no file id: "
                                  f"{json.dumps(j)[:200]}")
        return fid

    def create(self, file_id):
        j = self._json(["-X", "POST", f"{self.base}/batches",
                        "-H", f"Authorization: Bearer {self.key}",
                        "-H", "Content-Type: application/json",
                        "-d", json.dumps({"input_file_id": file_id,
                                          "endpoint": "/v1/chat/completions"})])
        return j.get("job") or j

    def status(self, batch_id):
        j = self._json([f"{self.base}/batches/{batch_id}",
                        "-H", f"Authorization: Bearer {self.key}"])
        return j.get("job") or j

    def list_batches(self):
        """All jobs visible to this key (review R2): the reconciliation
        source for a manifest record killed inside the create round-trip."""
        j = self._json([f"{self.base}/batches",
                        "-H", f"Authorization: Bearer {self.key}"])
        if isinstance(j, list):
            return j
        return j.get("jobs") or j.get("data") or []

    def content(self, file_id):
        return self._run([f"{self.base}/files/{file_id}/content",
                          "-H", f"Authorization: Bearer {self.key}"])


class BatchExecutor:
    """Batch-API executor: JSONL build with per-request bodies (F4),
    worst-case spend gate at submit (F3), atomic per-job manifest swept
    before any enqueue (F2), and a data-shaped per-item failure taxonomy
    (F5). Engagement per BATCH_DESIGN's ruling: a flush fires when the ready
    queue holds >= batch_min_pending; when nothing is in flight and the
    queue is smaller, the queued items run LIVE (starvation fallback -- the
    tail and top of a tree never wait on a threshold they cannot reach)."""

    #: F5 failure table, per collected item:
    #:   ok            -> feed; success writes its artifact, a validation
    #:                    failure advances the repair round and re-enters the
    #:                    ready queue (repair rounds batch too)
    #:   http_error    -> requeue as LIVE (the live ladder's bounded retries
    #:                    replace exception-string matching)
    #:   truncated     -> requeue as LIVE (a truncation is a bad DRAW; the
    #:                    fresh live draw is the resample)
    #:   missing       -> custom_id absent from the output file: requeue LIVE
    #: Job-level death (FAILED/EXPIRED/CANCELLED) reruns the whole job LIVE,
    #: never as another batch -- that bounds job retries by construction.
    #: A poison request (repairs exhausted) stops the run only AFTER every
    #: success in its job has been written to disk.

    def __init__(self, driver, exec_cfg=None, transport=None, manifest=None):
        exec_cfg = exec_cfg or {}
        self.drv, self.client = driver, driver.client
        self.min_pending = int(exec_cfg.get("batch_min_pending", 8))
        self.poll_s = float(exec_cfg.get("poll_s", 20))
        self.manifest = manifest or InFlightManifest(driver.out)
        self._transport = transport
        self.live = SerialExecutor(driver)
        cfg = driver.cfg
        p = getattr(self.client, "p", None)
        # envelope normalisation needs a Provider-shaped price/model carrier
        # even under a mock client
        self.prov = p or T.Provider(
            name="graph-batch", kind="openai-compatible",
            model=cfg.get("model", {}).get("model", "mock"),
            base_url=cfg.get("model", {}).get("base_url", ""),
            api_key_env=cfg.get("model", {}).get("api_key_env", ""),
            temperature=cfg.get("model", {}).get("temperature", 0.0),
            max_tokens=cfg.get("model", {}).get("max_tokens", 16384),
            price_per_mtok=cfg.get("price_per_mtok"))
        self._recovered = {}
        # review R4: worst-case dollars committed to submitted-but-uncollected
        # jobs; the submit gate must count ALL in-flight commitment, not just
        # the flush in hand
        self.outstanding_worst = 0.0
        # review R10: same-millisecond flushes must not overwrite each
        # other's manifest entry
        self._job_seq = 0
        # review R2: dispatches whose orphaned record could not be reconciled
        # with the provider (list_batches unavailable) -- they run LIVE, never
        # as another batch, and their record stays until it reconciles
        self._live_only = set()

    @property
    def transport(self):
        if self._transport is None:
            self._transport = CurlTransport(self.prov.base_url,
                                            getattr(self.client, "key", ""))
        return self._transport

    def _rpc(self, fn, *args):
        """Bounded retry around read-only transport calls (review R7): the
        curl transport exists BECAUSE of an intermittent WAF, so one flaky
        poll must not abort a run the manifest would have to rescue. Writes
        (upload/create) are NOT retried here -- a blind create retry could
        double-submit. No per-job wall-clock cap is taken (review R7 marks
        it optional); an EXPIRED-less provider hang still polls forever."""
        for attempt in range(4):
            try:
                return fn(*args)
            except T.ProviderError as exc:
                if attempt >= 3:
                    raise
                wait = min(5 * (attempt + 1), 20)
                print(f"    (batch transport transient [{str(exc)[:50]}], "
                      f"retry {attempt + 1}/3 in {wait}s)")
                time.sleep(wait)

    # -- top loop ----------------------------------------------------------
    def run(self, sched):
        self._recovered = self._sweep()   # F2: BEFORE any enqueue
        jobs = []
        while True:
            ready = []
            for st in sched.drain_ready():
                if self._feed_recovered(st, sched):
                    continue
                if (os.path.relpath(st.wdir, self.drv.out),
                        st.kind) in self._live_only:
                    # review R2: an unreconcilable orphan record may still
                    # have a live provider job for this dispatch; batching
                    # it again could double-pay, so it runs live only
                    self._run_live(st, sched)
                    continue
                ready.append(st)
            if sched.root_result is not None and not ready and not jobs:
                # review R3: recovered-result spool files are only consumed
                # once the whole run has finished cleanly
                for fn in os.listdir(self.manifest.dir):
                    if fn.endswith(".recovered"):
                        os.remove(os.path.join(self.manifest.dir, fn))
                break
            if len(ready) >= self.min_pending:
                jobs.extend(self._flush(ready, sched))
            elif ready and not jobs:
                # starvation fallback: run live, immediately
                for st in ready:
                    self._run_live(st, sched)
                continue
            elif ready:
                sched.push_back(ready)    # sub-threshold but work in flight:
                #                           the returning job may grow the set
            if jobs:
                jobs = self._poll_and_collect(jobs, sched)
            elif sched.root_result is None and not sched.ready:
                raise T.Phase1Error("batch scheduler stalled: nothing ready, "
                                    "nothing in flight, no root result")
        return sched.root_result

    # -- submit ------------------------------------------------------------
    def _request_body(self, state):
        """Per-request body (review F4): the response_format is computed HERE,
        from the state's own schema -- the client-global reply_schema slot is
        never involved in the batch path."""
        cap = self.live._phase_cap(state)   # D1: per-phase caps engage in
        #                                     batch bodies too, exactly as
        #                                     GraphClient._body's override
        body = {"model": self.prov.model,
                "temperature": self.prov.temperature,
                "max_tokens": cap or self.prov.max_tokens,
                "messages": [{"role": "system", "content": self.drv.brief}]
                + state.next_request()}
        if state.schema and not getattr(self.client, "_schema_rejected",
                                        False):
            name, sch = state.schema
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": name, "strict": False,
                                "schema": sch}}
        else:
            body["response_format"] = {"type": "json_object"}
        return body

    def _worst_case_usd(self, body):
        # F3 arithmetic per the ledger doctrine: full input rate on every
        # byte, full max_tokens out, no cache credit
        if not self.prov.price_per_mtok:
            return 0.0
        pin, pout = self.prov.price_per_mtok
        in_toks = len(json.dumps(body)) / 3.5   # chars/token, config.json's
        return (in_toks / 1e6 * pin
                + self.prov.max_tokens / 1e6 * pout)

    def _flush(self, states, sched):
        """Submit ready states as one batch job; returns the job list (0 or
        1 jobs). States the F3 gate cannot afford as a batch run LIVE, where
        the per-call measured ceiling is the backstop."""
        ceiling = getattr(self.client, "max_cost_usd", None)
        spent = getattr(self.client, "spent_usd", 0.0)
        rows, gated = [], []
        worst = 0.0
        for st in states:
            body = self._request_body(st)
            if self._req_max is None:
                self._req_max = {}
            self._req_max[st.custom_id()] = body.get("max_tokens")
            w = self._worst_case_usd(body)
            # F3: refuse at SUBMIT what the per-call check would only catch
            # at collection; the flush is split to fit rather than aborted.
            # review R4: `outstanding_worst` is the worst case already
            # committed to every submitted-but-uncollected job -- without it
            # two interleaved flushes each fit the ceiling alone while their
            # sum overcommits the run.
            if (ceiling is not None
                    and spent + self.outstanding_worst + worst + w > ceiling):
                gated.append(st)
                continue
            worst += w
            rows.append((st, body))
        if gated:
            print(f"  (batch submit gate: {len(gated)} request(s) exceed the "
                  f"worst-case ceiling as a batch; running them live)")
        if not rows:
            for st in gated:
                self._run_live(st, sched)
            return []
        # review R10: a custom_id collision would silently drop a state from
        # the job dict and end in a scheduler stall; unreachable with c{i}
        # components today, asserted so a refactor cannot make it silent
        cids = [st.custom_id() for st, _ in rows]
        if len(set(cids)) != len(cids):
            raise T.Phase1Error(
                "batch flush: duplicate custom_id after _safe_id collapse: "
                + ", ".join(sorted(c for c in cids if cids.count(c) > 1)))
        self._job_seq += 1   # R10: same-ms flushes must not share a name
        name = f"job-{int(time.time() * 1000)}-{self._job_seq}-{len(rows)}"
        jpath = os.path.join(self.manifest.dir, name + ".jsonl")
        with open(jpath, "w") as f:
            for st, body in rows:
                f.write(json.dumps({"custom_id": st.custom_id(),
                                    "body": body}) + "\n")
        entry = {"requests": {st.custom_id(): {
                     "key": st.key, "kind": st.kind,
                     "wdir": os.path.relpath(st.wdir, self.drv.out),
                     "round": st.repair_round} for st, _ in rows}}
        file_id = self.transport.upload(jpath, name + ".jsonl")
        # F2 ordering: the manifest entry exists BEFORE the job does, so a
        # kill in the create window still leaves a record to sweep. The
        # record carries the input_file_id from this moment on: a kill
        # DURING or right after create() leaves an indeterminate record
        # that _sweep reconciles against the provider (review R2) instead
        # of clearing as never-created.
        entry["input_file_id"] = file_id
        self.manifest.record(name, entry)
        job = self.transport.create(file_id)
        # submitted-flag update: only now is the job known to exist by id
        entry["batch_id"] = job.get("id")
        entry["submitted"] = True
        self.manifest.record(name, entry)
        self.outstanding_worst += worst   # review R4: committed until collect
        for st in gated:
            self._run_live(st, sched)
        return [{"name": name, "batch_id": entry["batch_id"],
                 "worst": worst,
                 "states": {st.custom_id(): st for st, _ in rows}}]

    # -- collect -----------------------------------------------------------
    def _poll_and_collect(self, jobs, sched):
        remaining, progressed = [], False
        for job in jobs:
            j = self._rpc(self.transport.status, job["batch_id"])
            status = str(j.get("status") or "").upper()
            if status == "COMPLETED":
                rows = self._rows(j.get("output_file_id"))
                # R4: the job's committed worst-case is released BEFORE
                # collect -- from here on its cost is measured, not worst-case
                self.outstanding_worst = max(
                    self.outstanding_worst - job.get("worst", 0.0), 0.0)
                self._collect(job, rows, sched)
                self.manifest.clear(job["name"])
                progressed = True
            elif status in ("FAILED", "EXPIRED", "CANCELLED"):
                # F5 job-level death: rerun LIVE, never batch-resubmit
                print(f"  (batch job {job['batch_id']} {status}; rerunning "
                      f"{len(job['states'])} request(s) live)")
                self.outstanding_worst = max(
                    self.outstanding_worst - job.get("worst", 0.0), 0.0)
                self.manifest.clear(job["name"])
                for st in job["states"].values():
                    self._run_live(st, sched)
                progressed = True
            else:
                remaining.append(job)
        if remaining and not progressed:
            time.sleep(self.poll_s)
        return remaining

    def _rows(self, output_file_id):
        if not output_file_id:
            return []
        blob = self._rpc(self.transport.content, output_file_id)
        rows = []
        for ln in blob.strip().splitlines():
            if ln.strip():
                rows.append(json.loads(ln))
        return rows

    _req_max = None    # custom_id -> requested max_tokens, set at flush

    def _classify(self, row):
        """F5: taxonomy from data shape alone -- a batch failure is a row (or
        a hole), and the live path's exception-substring triggers never fire
        on rows. Returns (kind, env_or_None)."""
        if row is None:
            return "missing", None
        resp = row.get("response") if isinstance(row, dict) else None
        body = resp.get("body") if isinstance(resp, dict) else None
        if isinstance(body, dict) and body.get("choices"):
            env = T.response_envelope(self.prov, body)
            # data-shape truncation backstop (ds4 live, 2026-08-11): together
            # returns finish_reason null on this model in some rows (the
            # harness's own documented caveat), so the envelope flag alone
            # let a truncated division parse as {"children": []} and poison
            # the run. completion_tokens >= the requested cap IS truncation,
            # whatever finish_reason says.
            req_max = (self._req_max or {}).get(row.get("custom_id"))
            out_toks = (env.get("usage") or {}).get("completion_tokens") or 0
            if env.get("truncated") or (req_max and out_toks >= req_max):
                return "truncated", env
            if not str(env.get("text") or "").strip():
                return "http_error", env    # empty completion: refusal-shaped
            return "ok", env
        return "http_error", None

    def _collect(self, job, rows, sched):
        """Two passes (review R5a): every collected 'ok' row is fed -- its
        artifact written, its usage ledgered -- BEFORE any live rerun can
        raise. The old interleaving discarded collected, paid, unwritten
        rows whenever a rerun earlier in dict order aborted the loop."""
        by_id = {r.get("custom_id"): r for r in rows}
        taxonomy, poison, reruns = {}, [], []
        for cid, state in job["states"].items():
            kind, env = self._classify(by_id.get(cid))
            taxonomy[cid] = kind
            if kind == "ok":
                # usage reaches the ledger at collection (F2's fix): the
                # ceiling backstop and spend visibility both live there
                if hasattr(self.client, "_log_usage"):
                    self.client._log_usage(env)
                state.feed({"text": env["text"], "usage": env["usage"]})
                if state.status == DONE:
                    sched.complete(state)
                elif state.status == PENDING:
                    sched.requeue(state)    # repair round batches too
                else:
                    poison.append(state)
            else:
                if env is not None:
                    if hasattr(self.client, "_log_usage"):
                        self.client._log_usage(env)  # truncated is billed too
                    # review R1: a billed truncated row counts against the
                    # dispatch budget, exactly like a billed live truncation
                    state.bill((env.get("usage") or {}).get("cost_usd")
                               or 0.0)
                if state.status == FAILED:   # budget blown by billed rows
                    poison.append(state)
                else:
                    reruns.append(state)
        if poison:
            # F5 poison ordering: every success above already wrote its
            # artifact; resume stays cheap. Raising BEFORE the live reruns
            # spends nothing more on a run that has decided to stop -- the
            # manifest entry survives, so the rerun states re-enqueue on
            # resume (review R5).
            raise T.Phase1Error(poison[0].error)
        for state in reruns:
            self._run_live(state, sched)
        return taxonomy

    def _run_live(self, state, sched):
        self.live.run_one(state)
        if state.status != DONE:
            raise T.Phase1Error(state.error)
        sched.complete(state)

    # -- resume (F2) -------------------------------------------------------
    def _artifact_path(self, meta):
        art = "division.json" if meta.get("kind") == "D" else "graph.json"
        return os.path.join(self.drv.out, meta.get("wdir") or "", art)

    def _persist_recovered(self, name, items):
        """review R3: recovered envelopes reach DISK before the manifest
        entry is cleared -- a crash anywhere after clear() (the rest of the
        sweep loop can block for minutes on a second orphan's poll) must not
        lose paid results. The `.recovered` suffix is deliberately not
        `.json`, so manifest.sweep() never mistakes the spool for a job."""
        if items:
            R.write_json(os.path.join(self.manifest.dir, name + ".recovered"),
                         items)

    def _adopt_batch_id(self, name, entry):
        """review R2: a record with an input_file_id but no batch_id is
        INDETERMINATE -- the kill may have landed after the provider accepted
        create() but before the second record(). Ask the provider; never
        clear a record the create round-trip might have made real."""
        fid = entry.get("input_file_id")
        try:
            jobs = self._rpc(self.transport.list_batches)
        except T.ProviderError as exc:
            # the endpoint cannot answer: keep the record and refuse to
            # resubmit these dispatches as a batch -- they run live, and a
            # later sweep reconciles (and ledgers) the job if it exists
            print(f"  (in-flight record {name}: create window indeterminate "
                  f"and batch listing unavailable [{str(exc)[:60]}]; keeping "
                  f"the record, its dispatches will run LIVE only)")
            for meta in entry.get("requests", {}).values():
                self._live_only.add((meta.get("wdir"), meta.get("kind")))
            return None
        match = next((j for j in jobs
                      if j.get("input_file_id") == fid), None)
        if match is None:
            # a positive listing with no job for this file: the create never
            # took; nothing was committed to run
            print(f"  (in-flight record {name}: provider has no job for "
                  f"{fid}; clearing -- dispatches will re-enqueue)")
            self.manifest.clear(name)
            return None
        bid = match.get("id")
        print(f"  (in-flight record {name}: adopted live job {bid} for "
              f"{fid} from the create kill window)")
        entry["batch_id"] = bid
        self.manifest.record(name, entry)
        return bid

    def _sweep(self):
        """Reconcile orphaned submissions BEFORE anything is enqueued: a
        submitted-but-uncollected job is money already committed, so its
        results are fetched and routed -- never blindly resubmitted."""
        recovered = {}
        # review R3: a prior sweep may have persisted recovered results and
        # crashed before they were fed; load the spool first
        for fn in sorted(os.listdir(self.manifest.dir)):
            if fn.endswith(".recovered"):
                for it in json.load(open(os.path.join(self.manifest.dir,
                                                      fn))):
                    recovered[(it["wdir"], it["kind"])] = it["env"]
        for name, entry in self.manifest.sweep():
            bid = entry.get("batch_id")
            reqs = entry.get("requests", {})
            if not bid and not entry.get("input_file_id"):
                # never uploaded: nothing was committed to run; the
                # dispatches re-enqueue naturally through artifact-resume
                print(f"  (in-flight record {name} has no batch id; "
                      f"clearing -- dispatches will re-enqueue)")
                self.manifest.clear(name)
                continue
            if not bid:
                bid = self._adopt_batch_id(name, entry)
                if bid is None:
                    continue
            j = self._rpc(self.transport.status, bid)
            status = str(j.get("status") or "").upper()
            while status not in ("COMPLETED", "FAILED", "EXPIRED",
                                 "CANCELLED"):
                time.sleep(max(self.poll_s, 0.1))   # R7: never busy-spin
                j = self._rpc(self.transport.status, bid)
                status = str(j.get("status") or "").upper()
            if status == "COMPLETED":
                by_id = {r.get("custom_id"): r
                         for r in self._rows(j.get("output_file_id"))}
                n, items = 0, []
                for cid, meta in reqs.items():
                    if os.path.exists(self._artifact_path(meta)):
                        # review R5b: the artifact is the witness that this
                        # row was written AND ledgered before a crash;
                        # ledgering it again would double-count usage.jsonl
                        continue
                    kind, env = self._classify(by_id.get(cid))
                    if env is not None and hasattr(self.client,
                                                   "_log_usage"):
                        # paid at submit, ledgered now (F2); review R8:
                        # billed truncated/error rows reach the ledger too,
                        # not only the "ok" ones
                        self.client._log_usage(env)
                    if kind == "ok":
                        key = (meta.get("wdir"), meta.get("kind"))
                        recovered[key] = env
                        items.append({"wdir": key[0], "kind": key[1],
                                      "env": env})
                        n += 1
                # R3 ordering: results to disk BEFORE the record is cleared
                self._persist_recovered(name, items)
                print(f"  (recovered {n}/{len(reqs)} result(s) from orphaned "
                      f"batch {bid}; the rest re-enqueue)")
            else:
                print(f"  (orphaned batch {bid} ended {status}; its "
                      f"dispatches re-enqueue)")
            self.manifest.clear(name)
        return recovered

    def _feed_recovered(self, state, sched):
        """Route a recovered orphan result to its dispatch instead of
        resubmitting (F2). Matched on (wdir, kind): the dispatch identity
        that survives a process death."""
        key = (os.path.relpath(state.wdir, self.drv.out), state.kind)
        env = self._recovered.pop(key, None)
        if env is None:
            return False
        state.feed({"text": env["text"], "usage": env["usage"]})
        if state.status == DONE:
            sched.complete(state)
        elif state.status == PENDING:
            sched.requeue(state)   # recovered reply failed validation:
            #                        normal repair path takes over
        else:
            raise T.Phase1Error(state.error)
        return True


# ------------------------------------------------------------------- selection
def build_executor(mode, driver, exec_cfg=None):
    exec_cfg = exec_cfg or {}
    if mode == "serial":
        return SerialExecutor(driver)
    if mode == "concurrent":
        return ConcurrentExecutor(driver, n=exec_cfg.get("concurrent_n", 4))
    if mode == "batch":
        return BatchExecutor(driver, exec_cfg)
    raise T.Phase1Error(f"unknown execution mode {mode!r} "
                        f"(execution.mode: serial|concurrent|batch)")


def run_build(driver, lo, hi, seeds, out, mode):
    """Entry point for recurse_driver --exec-mode: same arguments, same
    artifacts, same root graph as Driver.build."""
    exec_cfg = driver.cfg.get("execution", {})
    sched = Scheduler(driver)
    ex = build_executor(mode, driver, exec_cfg)
    sched.start(lo, hi, seeds, out)
    return ex.run(sched)
