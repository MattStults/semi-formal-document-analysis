# Adversarial engineering review: dispatch_core.py (pre-spend gate)

Reviewer: clean-context adversarial review, 2026-08-11.
Subject: `dispatch_core.py` + `test_dispatch_core.py` + the `--exec-mode`
integration in `recurse_driver.py` (main(), lines 916–1006).
Reference semantics: `recurse_driver.py` `Driver.call` (681–749),
`Driver._complete` (647–679), `Driver.build` (885–901);
`translate.py` `Client._send`/`_log_usage`/`response_envelope` (603–730).
Requirements: BATCH_DESIGN.md "Post-review resolution" + "Engagement rule";
batch_design_review.md F1–F5.

Method: line-by-line diff of DispatchState/SerialExecutor against
Driver.call/_complete; probe scripts against the unhappy paths the pin suite
does not reach (probe file:
`/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/probe_review.py`;
all five probes reproduce their findings). Existing suite: 16/16 pass.

**Verdict: do not spend yet.** The happy-path equivalence is genuinely strong
(prompt bytes, artifact bytes, DFS order, resume — all pinned and passing),
and F4/F5's data-shaped taxonomy is correctly built. But the per-dispatch
budget — the one control Matt ruled in *specifically against the overnight
redraw failure* — is blind to billed failed draws in every core executor
(R1), and the batch path has two F2 windows (R2, R3) and an F3 gap (R4) that
each translate directly into double-paid or over-committed dollars under the
hard cap. R1–R4 need fixes (or a signed acceptance) before live money.

---

## R1 (HIGH, semantic parity) — The per-dispatch budget never sees billed failed draws; Driver.call's does

**Defect.** `Driver.call`'s `_over()` measures `client.spent_usd - spent0`
(recurse_driver.py:690–700). `client.spent_usd` is incremented by
`_log_usage`, which `Client._send` calls **before** the truncation/emptiness
guards raise (translate.py:632–634) — so every TRUNCATED or empty draw is
billed *and counted against the dispatch budget*. `DispatchState.feed`
(dispatch_core.py:99–114) instead accumulates `self.spent` only from
envelopes that reach `feed()` — i.e. only successful draws. Every draw that
raises inside `SerialExecutor._ladder` (truncated, empty, or any billed-then-
raised response) is invisible to the budget.

**Concrete failure scenario** (probe P1, reproduced): budget $0.30, draws
cost $0.12 each, sequence TRUNCATED/TRUNCATED/clean. `Driver.call` fails
loudly at $0.36 with the "needs a DIAGNOSIS" message. The core executors
complete the dispatch with `state.spent == 0.12`. This is *exactly* the
overnight failure mode the ruling names ("a single leaf redrawing at
$0.055/draw with only an aggregate ceiling watching") — the redraws in that
incident were truncations, i.e. precisely the draws the core no longer
counts. In `concurrent` mode the ladder retries a truncating dispatch up to
7 draws, all billed, none counted; N workers can do this simultaneously
with only the aggregate ceiling watching. The equivalence tests cannot see
this: MockClient never raises and never bills.

**Minimal fix.** Bill the failure to the state where the executor catches
it: in `SerialExecutor._ladder`, snapshot a per-attempt cost (for clients
exposing `spent_usd`, take the delta across the `_send` call — in
ConcurrentExecutor, capture the delta inside the locked `_log_usage` wrapper
keyed by thread, since the client-global delta is racy) and add it to
`state.spent`, checking the budget between attempts as `call()` does. Same
for `BatchExecutor._collect`'s truncated rows (it ledgers them but never
adds them to `state.spent`). Then add a probe-style test with a
billing-then-raising client.

**Confidence: high** (probe-reproduced). **Severity: 1.**

---

## R2 (HIGH, batch F2) — Kill window between `create()` and the second `record()`: the job exists, the manifest says it doesn't

**Defect.** `_flush` orders: record entry (no batch_id) → `transport.create`
→ record entry (with batch_id) (dispatch_core.py:803–811). A kill after
`create()` returns but before the second `record` — or during the create
round-trip itself, after the provider accepted it — leaves a record with
`input_file_id` but no `batch_id`. `_sweep` (911–917) treats that record as
"uploaded but never created: nothing was committed to run", clears it, and
lets every dispatch re-enqueue. The next flush resubmits all of them: the
orphaned job runs and bills in parallel. This is the exact F2 defect the
manifest exists to prevent, surviving in a narrow window. The comment at
805 ("a kill in the create window still leaves a record to sweep") is true
but the sweep then discards what the record proves.

**Concrete failure scenario** (probe P3): manifest entry
`{input_file_id: "file-77", requests: {...}}`, provider has a live job for
file-77. `_sweep` returns `{}`, clears the record, never queries the
provider. A 27-leaf batch killed in this window is paid twice — and the
first job's spend reaches no ledger (the F2 spend-invisibility failure).

**Minimal fix.** A no-batch_id record with an `input_file_id` is
*indeterminate*, not clean: before clearing, ask the provider (list batches
and match on `input_file_id`, or GET the file's jobs if the API supports
it); if a job exists, adopt its id and reconcile as usual. If the endpoint
cannot answer, keep the record and refuse to resubmit those custom_ids as a
batch (run them live with a warning) rather than silently double-paying.
Test: extend the fake curl with a batch-list endpoint and pin the window.

**Confidence: high** on the window (code + probe); **medium** on fix shape
(together's batch-list semantics unverified offline). **Severity: 2.**

---

## R3 (HIGH, batch F2) — `_sweep` clears the manifest before recovered results are fed or written

**Defect.** `_sweep` fetches an orphaned job's results into an in-memory
dict and clears the manifest entry immediately (dispatch_core.py:935, 942).
The recovered envelopes reach disk only later, when `run()`'s drain loop
calls `_feed_recovered` per state. A crash — or any raise — between the
`clear()` and the feed (window includes the *entire remaining sweep loop*,
which can block for minutes in the poll-until-terminal loop at 920–924 on a
second orphan, plus scheduler start-up) loses paid results with no record
left: the next resume finds no manifest and no artifact, and resubmits.
Also, `_feed_recovered`'s `else: raise` (960) aborts the drain mid-list,
discarding every other recovered envelope the same way.

**Minimal fix.** Don't clear on recovery — clear a job's record only after
every request in it is written-or-re-enqueued (the rule
batch_design_review F2 itself states). Cheapest faithful version: persist
recovered envelopes (write each env to `inflight/<name>.recovered.json`
via `write_json`, or feed states directly during sweep since the scheduler
could be started first) and only then `clear(name)`.

**Confidence: high** (code reading; the window is unambiguous).
**Severity: 3.**

---

## R4 (MEDIUM-HIGH, batch F3) — The submit gate ignores worst-case already committed to in-flight jobs

**Defect.** `_flush`'s gate compares `spent + worst + w > ceiling` where
`spent = client.spent_usd` (measured, i.e. *collected*) and `worst` covers
only the current flush (dispatch_core.py:772–785). A previously submitted,
uncollected job's committed worst-case is in neither term. Interleaving is
real: the starvation fallback runs live work while a job is in flight, live
completions grow the ready queue past `min_pending`, and a second `_flush`
fires before the first collects.

**Concrete failure scenario** (probe P4, reproduced): ceiling set so one
2-request flush fits; two flushes both submit; total committed worst-case
~$21.8 against a ~$13.6 ceiling. F3's own words — "refuse at SUBMIT what
the per-call check would only catch at collection" — are met per-job but
not per-run.

**Minimal fix.** Track `self.outstanding_worst` in the executor: add each
submitted job's summed worst-case at submit, subtract at collect/death, and
gate on `spent + outstanding_worst + worst + w > ceiling`. One field, three
lines. Pin with a two-flush test.

**Confidence: high.** **Severity: 4.**

---

## R5 (MEDIUM, batch F5) — Poison ordering is violated by interleaved live reruns; partial-collect crash double-ledgers

**Defect (a).** The module header and the F5 table promise "successes are
written to disk before a poison request stops the run". `_collect`
(868–894) interleaves: non-ok rows call `_run_live` *inside* the loop, and
`_run_live` raises `Phase1Error` when the live rerun exhausts repairs. Every
"ok" row later in `job["states"]` iteration order is then discarded —
collected, paid, unwritten. Probe P2 (reproduced): job of [error-row,
ok-row]; after the abort the ok state is still PENDING, result None. The
manifest entry survives (clear is after `_collect`), so resume *does*
recover the row — but see (b).

**Defect (b).** When `_collect` ledgers some ok rows and then raises, resume
`_sweep` re-ledgers **all** ok rows of that job (932–934), including those
already ledgered and even those whose artifacts were written pre-crash.
Overcount is the survivable direction under the doctrine, but it burns
headroom under the $8.50 cap and corrupts usage.jsonl as a record.

**Minimal fix.** Two passes in `_collect`: (1) feed every "ok" row (writing
artifacts, collecting poison states), (2) then run the non-ok reruns, (3)
then raise for poison. For (b): have `_sweep` skip ledgering rows whose
dispatch artifact already exists (the artifact is the "this was ledgered"
witness), or log the double-count decision by name.

**Confidence: high** (probe (a); code (b)). **Severity: 5.**

---

## R6 (MEDIUM, concurrency) — After a fatal worker error, the dispatcher can still start (and pay for) one more dispatch

**Defect.** `ConcurrentExecutor.run`'s main loop checks `stop` only at the
top, *before* `sem.acquire()` (575–588). Sequence: main pops state S, blocks
on the semaphore; a worker hits a fatal error (`stop.set()`, releases); main
wakes and starts a worker for S anyway — a full draw/repair loop, up to
`per_dispatch_usd` of spend, after the run has already decided to abort.
With the F5 comment claiming "workers that finished have already written
their artifacts; only then does the run stop", the *newly started* dispatch
is outside that story.

**Minimal fix.** Re-check `stop.is_set()` after `sem.acquire()`; if set,
release and break (push S back for resume hygiene). Two lines.

**Confidence: high** (code; timing-dependent so not probe-scripted).
**Severity: 6.**

---

## R7 (LOW-MEDIUM, batch robustness) — No transient tolerance anywhere in the batch transport, whose own docstring documents an intermittent WAF

**Defect.** `CurlTransport` grounds its existence in "together's WAF
intermittently 403s ... while accepting curl" — yet one failed
`status()` poll (curl non-zero, non-JSON body, or a WAF 403 through curl)
raises `ProviderError` straight out of `_poll_and_collect` and aborts the
run. Correctness survives (manifest → resume reconciles; probe not needed),
but the executor built to ride out live-tier flakiness dies on one flaky
poll. Also: `_sweep`'s poll-until-terminal loop (920–924) has no timeout
and busy-spins when `poll_s=0`; `run()`'s poll loop likewise has no job
timeout (an EXPIRED-less hang polls forever).

**Minimal fix.** Wrap `status`/`content` calls in a small bounded retry
(the live ladder's shape: N attempts, backoff); floor `poll_s` at some
epsilon in the sweep loop; optionally a wall-clock cap per job that reruns
its states live (the F5 job-death path already exists to receive them).

**Confidence: high.** **Severity: 7.**

---

## R8 (LOW, ledger consistency) — `_sweep` does not ledger billed non-ok orphan rows; `_collect` does

**Defect.** `_collect` ledgers truncated rows explicitly ("truncated is
billed too", 887–888). `_sweep` ledgers only "ok" rows (930–934); a
truncated or error row recovered from an orphaned job — billed at submit —
reaches no ledger. Probe P5 (reproduced): orphaned job with one truncated
row; zero `_log_usage` calls during sweep. Undercount — the direction the
doctrine forbids.

**Minimal fix.** Mirror `_collect`: in `_sweep`, `_log_usage(env)` whenever
`env is not None`, not only on "ok". One line. **Severity: 8.**

---

## R9 (LOW, parity/latent) — Three small divergences and hazards, for the record

1. **ConcurrentExecutor bypasses `Client._retrying`** (it calls
   `_body`/`_send` directly), so `model.resample_truncation` extra draws are
   silently inert in concurrent mode. The ladder's transient retries mostly
   mask this; note it or route through `_retrying`.
2. **Fallback `_send` race**: for a client with a `reply_schema` slot but no
   `_body`/`_send`, `ConcurrentExecutor._send` falls through to the
   *unlocked* serial path (543), which mutates the client-global slot from N
   threads. No current client fits that shape (GraphClient has both), but
   the hazard is one refactor away — assert or lock the fallback.
3. **`_log_usage` wrapper stacks** if two executors are ever built on one
   client (instance-attr wrap of the previous wrap). Idempotence guard is
   one `getattr` check.
4. **First-draw tally/budget ordering**: Driver checks `_over()` *before*
   `_tally` on the first draw (702–703) and after on repairs; the core
   always tallies first. Affects only cache counters — cosmetic, accepted.
5. **Bury filenames** carry `_<key>_r<n>` where Driver uses bare
   milliseconds — a *documented, deliberate* divergence (batch collision
   guard, F5 note). Accepted.

**Severity: 9.**

---

## R10 (LOW, batch bookkeeping) — Collision spaces that fail as stalls, not corruption

- **custom_id**: `_safe_id(key)-r{round}`. Distinct dispatches collide only
  if `_safe_id` collapses distinct rel-paths (`c1/c2` vs `c1_c2`) — the
  scheduler only ever creates `c{i}` components, so unreachable today; but a
  collision would *silently drop a state* from `job["states"]` (dict build,
  814), ending in a scheduler-stall raise rather than a wrong artifact.
  Cheap insurance: assert uniqueness in `_flush`.
- **Job names**: `job-{ms}-{n}` — two flushes in the same millisecond with
  equal row counts overwrite each other's manifest entry. Upload+create
  round-trips make this near-impossible live; a counter suffix closes it.
- **Manifest dir residue**: submitted `.jsonl` input files are never
  deleted (sweep only matches `.json`, so no wedging — disk-only).

**Severity: 10.**

---

## Test-suite assessment (attack surface 4)

**What holds up.** The two equivalence pins are the real thing: prompt-byte
and artifact-byte comparison against an *independently executed*
`Driver.build`, plus a resume re-run under a client that raises on any call.
The concurrency test proves genuine overlap with wall-clock intervals and
byte-compares the result. The orphan test asserts the negative ("no POST to
/batches") from the transport log, not from its own mocks. No test asserts
purely on its own construction.

**What the suite cannot see (each maps to a finding above):**
- No client that **bills and then raises** — the entire R1 class is
  invisible; MockClient/KeyedMock never raise, never carry cost, and the
  budget test feeds `feed()` directly rather than driving the ladder.
- `test_batch_executor_failure_taxonomy` and the gate test **stub out
  `_run_live`** with a list-appending lambda — precisely the seam where R5's
  ordering violation lives; the stub cannot raise, so the poison-ordering
  claim in the module header is untested.
- The kill-scenario test (`test_orphaned_batch_is_reconciled_not_resubmitted`)
  covers only the batch_id-present record; the R2 window (input_file_id, no
  batch_id, job live) and the R3 clear-before-feed window have no test.
- No two-flush test, so R4's in-flight gate blindness is untested.
- The e2e batch test wires `flush_and_answer` over `_flush` — legitimate as
  a harness, but it means the fake-curl `/files/.../content` taxonomy path
  and the real `_flush` never run together in the same test; fine today,
  worth noting as coupling.

**Suggested additions once R1–R5 are fixed:** a `BilledFlaky` parity test
(Driver.call vs SerialExecutor, same client behavior, same outcome), the
two F2 kill-window tests against the fake curl, a two-flush gate test, and
a `_collect` test where `_run_live` is real and the live client is
unrepairable.

---

## Summary table

| # | Severity | One line | Probe |
|---|----------|----------|-------|
| R1 | High | Per-dispatch budget blind to billed failed draws — the exact overnight failure the ruling targets | P1 |
| R2 | High | create→record kill window: live job cleared as "never created", then double-paid | P3 |
| R3 | High | `_sweep` clears manifest before recovered results are fed/written; crash loses paid results | code |
| R4 | Med-High | Submit gate ignores in-flight jobs' committed worst-case | P4 |
| R5 | Medium | Poison ordering violated by interleaved live reruns; partial-collect crash double-ledgers on resume | P2 |
| R6 | Medium | Concurrent stop race starts one more paid dispatch after a fatal error | code |
| R7 | Low-Med | Zero transient tolerance in the batch transport built *because of* transient WAF failures; unbounded polls | code |
| R8 | Low | `_sweep` skips ledgering billed truncated/error orphan rows | P5 |
| R9 | Low | resample bypass in concurrent; unlocked fallback `_send`; wrapper stacking; two accepted cosmetic divergences | code |
| R10 | Low | custom_id/job-name collision spaces fail as stalls; assert-uniqueness is cheap | code |
