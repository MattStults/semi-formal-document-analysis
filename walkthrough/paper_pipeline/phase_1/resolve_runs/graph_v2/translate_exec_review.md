# Adversarial review — translate_exec.py + test_translate_exec.py

Clean-context review before live spend. 2026-08-11. No API spend: all evidence is
static reading plus deterministic probes (`/tmp/probe_translate_exec.py`, mock
clients only). Suite baseline: 8/8 pass. Serial reference: `translate.run()`
(translate.py §9); executors: `dispatch_core.py`.

Verdict: **no stopper for a live concurrent run; one finding (F1) should be
ruled on before a live BATCH run**, because a mid-batch kill currently abandons
paid work and the recovery machinery that claims otherwise would mis-route
replies across clauses if it ever engaged.

---

## F1 — batch crash-recovery is inert, and wrong if ever reached  (HIGH, batch mode only)

Every `ClauseState` presents the same recovery identity to dispatch_core's F2
machinery: `wdir = ctx.outdir` and `kind = "T"`, so
`os.path.relpath(state.wdir, drv.out)` is `"."` for all clauses.
Probe P3: 5 states → **1** distinct `(wdir, kind)` key `('.', 'T')`.

Consequences inside `dispatch_core.BatchExecutor` (all keyed on that tuple):

* `_sweep()` recovered dict keeps only ONE clause's paid reply per run
  (`recovered[('.', 'T')] = env` overwrites), and `_feed_recovered()` hands the
  surviving reply to **whichever clause is popped first** — a cross-clause
  mis-delivery that would be written out as that clause's translation.
* `_live_only` (unreconcilable-orphan guard) would force every clause live, not
  the orphaned ones.
* `_artifact_path()` computes `<outdir>/./graph.json` for kind "T" (probe P3:
  never exists), so the R5b "written-and-ledgered" witness always fails and
  every recovered row would be **re-ledgered** (usage.jsonl double count).

Why nothing has burned yet: the path is unreachable. `prepare()` runs
`os.makedirs(outdir)` (no `exist_ok`) and `T.resolve_outdir` refuses a non-empty
run dir, so a killed batch run can never be re-entered in the same outdir — the
inflight record and the submitted, **paid** batch job are simply abandoned; a
fresh run pays again. So today's real behaviour is "kill mid-batch = lose the
money", with the F2 manifest as dead weight.

Minimal fix (pick one, record the ruling either way):

1. **Honest refusal** (smallest): in `_TranslateBatch.__init__`, raise
   `T.Phase1Error` if `manifest.sweep()` is non-empty, and add one line to the
   translate_exec docstring: batch-mode kill-recovery is unsupported; a killed
   batch run's submitted job is abandoned. Removes the mis-routing hazard by
   construction.
2. **Real identity** (if resume is ever wanted): give each state a distinct
   recovery identity — e.g. `self.wdir = os.path.join(ctx.outdir, cid)` in
   `ClauseState.__init__` (translate_exec.py:170) so relpath is the clause id,
   plus an `_artifact_path` override in `_TranslateBatch` returning
   `os.path.join(self.drv.out, meta["wdir"] + ".json")` — and a resume entry
   point that tolerates an existing outdir. That is a design change; per the
   working rules it needs a design-tier pass, not an implementation-tier patch.

Test gap: no test kills a process mid-batch or exercises `_sweep` with
translation states (the caller's attack 4 — confirmed).

## F2 — fed-failure error records diverge from serial  (MEDIUM, confirmed)

`_TolerantRunOne.run_one` (translate_exec.py:310) builds the failure detail as
`f"{type(exc).__name__}: {exc}"`; `ClauseState._rpc` re-raises it as
`T.ProviderError(payload)`, and `clause_body`'s handler prefixes the type name
again. Measured (probes P2/P4 vs serial reference run):

* serial run.json: `'ProviderError: HTTP 402: Credit limit exceeded'`
* exec run.json:   `'ProviderError: ProviderError: HTTP 402: Credit limit exceeded'`

A real run.json row field differs between modes, i.e. the module's load-bearing
equivalence claim is broken on the error path — undetected because the
equivalence fakes never raise (attack 4, confirmed).

Minimal fix: pass `str(exc)` as the detail in `_TolerantRunOne.run_one`
(one-line, translate_exec.py:310). Residual, accept by name: a `Phase1Error`
subclass other than `ProviderError` (e.g. `CostGateError`) still gets recorded
as `ProviderError: ...` in exec mode because the shim re-raises under one type;
serial preserves the subclass name.

Test fix: add an equivalence case whose client raises `ProviderError` on one
clause (attempt-1 and mid-repair variants) and pin serial vs exec run.json rows.

## F3 — abort path leaks the pending clause's parked thread  (LOW, confirmed)

A non-`Phase1Error` escaping `run_one` (raw transport bug, `response_envelope`
KeyError on an error-shaped 200, …) aborts the run — the documented, accepted
divergence, and serial `run()` would abort on the same exception too, so the
abort itself is equivalent. Probe P1 confirms: no deadlock, completed clauses'
artifacts survive, `run.json` is flushed by `execute()`'s `finally`. But the
failing clause's body thread is left parked forever on `_resp_ready.wait()`
(P1: 1 leaked daemon thread). Harmless for the CLI (process exits); real for
pytest / any embedding (threads accumulate; the body holds no locks while
parked, so no corruption).

Minimal fix: in `_TolerantRunOne.run_one` catch `Exception` instead of
`T.Phase1Error`; deliver `feed_failure` if PENDING as now, then **re-raise when
the exception was not a Phase1Error** (preserving serial-equivalent abort
semantics) — the delivery unparks the thread and lets the body write its error
rec before the abort. ~4 lines at translate_exec.py:305-312.

## F4 — NOTE (requested): the ds3 HTTPError meltdown class, checked here

The live graph-build kill (runs/ds3_log.txt) was `urllib HTTPError 402` →
wrapped by `translate.Client._send` (translate.py:627) into
`ProviderError("HTTP 402: ...")` → not in `_TRANSIENT_MARKS` (dispatch_core.py:457,
only "HTTP 5") → escaped `_ladder` → `ConcurrentExecutor.worker` caught it,
set `stop`, and `run` re-raised (dispatch_core.py:661/701), killing the build.

**translate_exec does NOT inherit this failure mode for that error class.**
`_TolerantRunOne` converts any `Phase1Error` raised while a request is pending
into the clause's own error record; probes P2 (attempt-1) and P4 (mid-repair —
a path no test exercises) both show: exit code 1, failing clause recorded as
`status="error"`, the other 4 clauses translated, 0.2s wall time (no transient
retries wasted on a 402), no deadlock, no leaked threads. What translate_exec
DOES share is the abort on non-`Phase1Error` exceptions (F3), which is
serial-equivalent and accepted by name in its docstring.

Fix locations for the graph-build side (dispatch_core, out of this review's
change scope): (a) the abort itself is arguably correct there — graph
dispatches are dependency-bearing, artifact-resume covered the restart, and a
402 will fail every subsequent call anyway; (b) the cheap conservative
improvement is extending `_TRANSIENT_MARKS` (dispatch_core.py:457) with
`"HTTP 429"` so rate-limit blips retry with backoff instead of aborting a
multi-hour build (in translate_exec a 429 currently becomes a permanent
per-clause error with no retry — fewer retries than the ladder gives 5xx, the
non-conservative direction).

## F5 — remaining verified-clean surfaces (attacks 1–3)

* **Shim handshake**: deadlock-free by construction — `_run_body`'s `finally`
  sets `_req_ready`, so `_deliver`/`next_request` can never wait on a dead
  body; `feed_failure` during attempt-1 and mid-repair both terminate (P2/P4).
  A genuinely hung `checks.run_checks` hangs the run, but hangs serial
  identically — equivalent, not a defect.
* **run_checks crash on one clause**: body thread catches `BaseException` →
  state FAILED → whole run aborts after completed clauses' artifacts and a
  flushed run.json — same as serial, where the uncaught non-Phase1Error aborts
  `run()` (its `finally: flush()` also runs). Equivalent.
* **run.json / concept-table races**: every write is under `ctx.io_lock`
  (RLock; `finish` → `flush` re-entry safe); slot-ordered lists keep serial row
  order. Graveyard entries embed the clause id in the dir name and each clause
  runs once per run, so no cross-thread collision; `check_cap` runs once
  pre-executor, same point as serial (pinned by test).
* **Ledger under batch**: one `_log_usage` per collected item (ok AND billed
  truncated/error rows), `ConcurrentExecutor` wraps `_log_usage` under its
  ledger lock with the idempotence guard; no in-run duplicate path found.
  Resume-path duplicates are exactly F1's re-ledger hazard — unreachable today.
* **Measured-ceiling note**: `client.max_cost_usd` set in `prepare()` feeds
  only the F3 batch submit gate; translate's `Client._log_usage` (unlike
  `GraphClient`) never enforces it on measured spend mid-run. Live concurrent
  spend is bounded by the up-front worst-case `cost_gate` alone — same bound
  serial runs under; fine, but worth knowing it is the only bound.

## Ranked fix list

| # | Finding | Fix | Where | Size |
|---|---------|-----|-------|------|
| 1 | F1 batch recovery inert/mis-routing | refuse non-empty sweep + document (or design-tier identity fix) | `_TranslateBatch.__init__` (translate_exec.py:327) | ~5 lines |
| 2 | F2 doubled error prefix breaks row equivalence | pass `str(exc)` as detail | translate_exec.py:310 | 1 line |
| 3 | F3 leaked parked thread on abort | catch `Exception`, deliver, re-raise non-Phase1 | translate_exec.py:305-312 | ~4 lines |
| 4 | F4 429 non-transient | add `"HTTP 429"` to `_TRANSIENT_MARKS` | dispatch_core.py:457 | 1 token |
| 5 | F5/attack-4 blind spot | raising-client equivalence test (attempt-1 + mid-repair) pinning serial vs exec rows | test_translate_exec.py | ~40 lines |

Probes: `/tmp/probe_translate_exec.py` (P1 abort/leak, P2 402-attempt-1,
P4 402-mid-repair, P3 recovery-identity collision). All deterministic, $0.
