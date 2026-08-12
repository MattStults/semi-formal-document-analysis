# Adversarial review: BATCH_DESIGN.md (batch execution)

Reviewer: clean-context adversarial design review, 2026-08-11.
Inputs read: `BATCH_DESIGN.md`; `recurse_driver.py` in full (Driver.call/build,
GraphClient, autofixes, health, resume, cost estimate); `translate.py`
Provider/Client/`_body_messages`/`_check_envelope`/`_log_usage`/
`response_envelope` (~400–770) and `run()` + `repair_loop` (~1084–1340,
2420–2500).

Verdict: **the ready-queue ruling is sound as a scheduling policy, but the
design is not buildable as written.** It prices the queue and skips the two
things the queue must plug into: an inversion of the driver's blocking
recursive control flow, and a submit-side story for money (ceiling,
double-pay on crash, per-request state). The "~1 day" estimate and the
"one shared BatchQueue, built once" claim both rest on the parts that were
not designed. Findings ranked by severity.

---

## F1 (CRITICAL) — The driver's control flow cannot host a ready queue without a rewrite the design does not mention

**Defect.** `Driver.build` is a recursive function; `unwind` is a *stack
frame* blocked on its children's return values, and every model call goes
through `Driver.call`, which is fully blocking: it holds the repair
transcript, the accumulating `errs`, the `_restarted` flag, and the
truncation heuristic as local variables across up to `max_repairs` serial
round-trips (`recurse_driver.py:636–685`), calling
`self.client.complete(...)` directly inside `self._complete`'s retry loop.
A ready queue ("the queue may mix attempt-1 requests with round-3 repairs
in a single batch job") requires every one of those locals to become
persisted per-dispatch state — dispatch identity, validator closure, schema,
repair round, transcript, restart flag — and requires `build()` to become an
explicit dependency graph (an unwind is "ready when children are all done",
which no call stack can express while its siblings run).

The design instead says:

> "The per-node artifact/resume model is untouched: a batch result is just
> N replies written through the same validate -> autofix -> write path."

and its build plan says:

> "2. Driver `--batch` mode: frontier loop above (est. ~1 day of work incl.
> pins...)"

— where "the frontier loop above" is the **strict-BFS layer design that the
same document retires** ("'frontier' retired", "Rejected by name: ... (c)
strict BFS layers"). The build plan was never updated after the ruling: the
document rejects a design by name and then instructs the builder to build it.

**Why it matters.** The validate/autofix path is *not* the seam; it is three
lines inside `call()`. The seam is `call()` itself, and everything the design
prices as "unchanged code" is entangled with the blocking loop. An
implementer following the doc will either (a) build the rejected BFS loop, or
(b) discover mid-build that the ready queue needs a scheduler + per-dispatch
state machine that nobody designed, and improvise it on an implementation
tier — exactly what the repo's working rules forbid for design work.

**Minimal fix.** Add a section that designs the state machine explicitly:
a `Pending` record per dispatch (kind D/L/U, wdir, lo/hi, seeds/children
refs, schema name, repair_round, transcript, restarted flag), a dependency
table replacing `build()`'s recursion (children-of and unwind-waits-on), and
the rule for which `call()` branches map to re-enqueue vs. abort (see F5).
Then re-estimate; correct the build plan to reference the ready queue, not
the retired frontier loop.

**Confidence: high** (pure code reading; no provider behavior assumed).

---

## F2 (CRITICAL) — Duplicate submission on resume: a submitted-but-uncollected batch is invisible, and is paid twice

**Defect.** The resume model is "each tree node's artifacts ... are the
state; a re-run skips finished directories" (`recurse_driver.py:30–33`;
`divide`/`leaf`/`unwind` each start with `if os.path.exists(art): return`).
Artifacts are written only **after** a validated reply. A batch job commits
spend at **submit** time. So: process submits a 27-request leaf batch, dies
(crash, sleep/wake, Ctrl-C) before collection → no artifact exists for any of
the 27 → resume re-enqueues all 27 and submits a second job. The first job's
results are sitting on the provider, already billed, and nothing in the
design ever looks for them. The doc's failure section does not exist; the
words "resume", "crash", "job id" do not appear in the batch-specific text.

**Why it matters.** This project runs under a hard budget ceiling ($8.50,
CLAUDE.md) and the driver's whole crash story is "a killed run loses at most
one call." Batch mode silently changes that to "a killed run loses up to one
whole batch of calls," at exactly the wide layers where batching was chosen.
Worse, the orphaned job's spend lands in *no* ledger: `_log_usage` fires at
collection, so the usage.jsonl undercounts real spend — the precise failure
mode `spend_invisibility_warning` exists to shout about.

**Minimal fix.** Extend the artifact-as-state model to the job level: at
submit, atomically write `<out>/batches/<job_id>.json` (via the existing
`write_json` tmp+rename) mapping provider `custom_id` → (wdir, kind,
repair_round), derived deterministically from the dispatch (e.g.
`sha16(wdir + ":" + str(round))`). On startup, **before** enqueueing
anything, sweep `<out>/batches/*.json`, poll each job, collect and route any
finished results through the normal validate/write path, and log their usage
then. Delete/mark the manifest only after every request in it is either
written or re-enqueued. Duplicate-collection is then idempotent because the
per-node `os.path.exists(art)` guard already is.

**Confidence: high** on the defect (it follows from code + design text);
**medium** on fix details (together's batch retrieval semantics not verified
offline — the design already owes Matt a batch-API fact-check per its own
open questions).

---

## F3 (HIGH) — The measured-spend ceiling is enforced per call, after the fact; a batch commits N calls before the first measurement

**Defect.** The ceiling is enforced in `GraphClient._log_usage`
(`recurse_driver.py:550–558`): after **each** live call, measured dollars are
compared to `max_cost_usd` and the run raises, so overshoot is bounded by
one call. In batch mode the whole job is committed at submit; measurement
happens at collection. A leaf-layer batch (~27 dispatches × up to
`max_tokens` out each) can sail past the ceiling by the entire job's cost
before `_log_usage` ever runs. The design never mentions the ceiling.

**Why it matters.** The ceiling exists because estimates were wrong before
(review F10 made it *measured*). Batch mode quietly re-widens the bound from
"one call" to "one batch," at the widest point of the tree, under a repo-wide
hard cap.

**Minimal fix.** A submit-side gate in `BatchQueue.flush`: worst-case-price
the job with the same arithmetic as `measured_cost` (full input rate, full
`max_tokens` out, no cache credit — the codebase's stated doctrine:
"overstating spend under a hard cap is survivable and understating it is
not"), and refuse to submit if `spent_usd + worst_case > max_cost_usd`;
optionally split the flush to fit. Keep the existing post-collection check
as the backstop.

**Confidence: high.**

---

## F4 (HIGH) — Per-request client state: `reply_schema` and the `_schema_rejected` latch do not survive batching

**Defect.** The design says batch replies flow through "the same
validate -> autofix -> write path ... untouched" and batch_client is "same
Provider/key/ledger plumbing." But request *construction* is stateful:
`Driver.call` does `self.client.reply_schema = schema` (line 637–638) and
`GraphClient._body` reads that mutable instance attribute; a batch job mixes
division, leaf, unwind, and repair requests, each needing a different
`response_format`, so the one-slot client state is structurally wrong — the
body builder must take the schema as an argument per request. Second, the
json_schema→json_object downgrade is a *client-global latch* flipped inside
`_complete`'s exception handler when the endpoint rejects `response_format`
(lines 616–621, mirroring translate.py's HTTPError hint at ~601–611). In
batch mode that rejection arrives per-request, as **data in the results
file**, after the whole job ran: every schema-bearing request in the job has
already failed, and the exception-string trigger (`"response_format" in
detail`) never fires because nothing raised.

**Why it matters.** Best case, one wasted batch job of N rejected requests
(paid or not depending on provider error-billing — unverified); worst case,
the latch never flips and every round re-fails identically — a systemic
poison batch (see F5) that the retry logic misreads as N independent
failures.

**Minimal fix.** (1) Thread `(name, schema)` through per-request body
construction (`_body(system, user, schema=...)`) instead of client state.
(2) Decide schema support **once, live, before the first batch**: the very
first call of any run is the root division and runs live anyway under the
starvation fallback — let it set `_schema_rejected` for the run. (3) In the
collector, recognize the response_format-rejection error shape as
"downgrade and re-enqueue," not as a repair or transient.

**Confidence: high** on the state problem (code); **medium** on how
together's batch surfaces per-request 400s.

---

## F5 (HIGH) — Failure taxonomy is missing: partial results, job-level death, and poison requests all fall through exception-string logic that only exists for live HTTP

**Defect.** Every recovery in the current stack is keyed off **raised
exceptions and substring matches**: `_complete` retries on `"TRUNCATED"`,
`"HTTP 5"`, `"timed out"`, `"Connection"`, etc. (lines 622–634);
`_check_envelope` raises on truncation/emptiness; `call()`'s repair loop
catches `T.ProviderError` for the fresh-restart path. Batch results arrive
as a results file where a request's failure is a **data row** (error object,
missing output), and a job can also fail/expire *as a whole*. None of the
existing triggers fire on data. The design's only words on failure are
"collect; validate/autofix each reply (unchanged code)" — which presumes
every request produced a reply.

Unspecified, and each needs a named answer:
- **Per-request transient error in a batch** → re-enqueue with the same
  bounded count as `_complete`'s 6, or the bound silently disappears.
- **Per-request truncation** → the live path's rules (resample twice; on a
  laden repair transcript, restart the dispatch fresh, once —
  `_restarted`) must map to re-enqueue rules, or the 2026-08-10 truncation
  findings are un-learned.
- **Job-level failure/expiry** → re-submit all, with a *job* retry cap, else
  an outage loops forever at batch granularity.
- **Poison request** (fails validation every round): live semantics are
  "raise `Phase1Error`, abort the build, artifacts keep resume cheap." In a
  batch, the poison's failure surfaces alongside N−1 successes. The design
  must state the order: **write every success to disk first, then stop** —
  and say whether independent subtrees keep running. Silence here means the
  implementer chooses, on an implementation tier.

**Minimal fix.** A one-page failure table in the design: {per-request
transient, per-request truncation, per-request schema-rejection (F4),
per-request validation failure → repair round, job failure, poison after
`max_repairs`} × {action, bound, who logs usage, what lands in `failed/`
(`_bury`)}. Note `_bury`'s millisecond-timestamp filenames
(`recurse_driver.py:597–600`) collide when a collector buries a batch of
failures in one loop — add the custom_id to the name.

**Confidence: high** (design omission is on its face; live-path semantics
from code).

---

## F6 (MEDIUM) — Cache economics: the discount claim is not netted against losing the prefix cache, and one stated cache property becomes false

**Defect.** The design's economic case is "prices at a discount" (~50%,
listed as an open question). It never mentions the prefix cache, yet the
driver's cost story leans on it by name: the system prompt is
"byte-identical on every call, so the provider's prefix cache covers it"
(`recurse_driver.py:14–17`), the run reports its hit rate, and
`repair_loop`'s docstring asserts "its PREFIX never changes, so every call
after the first is a cache hit" (`translate.py:2424–2426`). Whether batch
workers share the live prefix cache — or whether requests inside one job can
even hit each other's freshly-written prefixes — is provider-specific and
unverified; the sequential-call cache pattern (call N warms call N+1) is
exactly what batching destroys. If batch requests miss the cache, the real
bill gains full-rate input on the multi-KB brief × every request, offsetting
an unknown fraction of the 50% output+input discount; for transcript-heavy
repair rounds the offset is largest.

**What is safe:** the *ledger and ceiling* are unaffected — `measured_cost`
deliberately bills cached input at the full rate (`translate.py:675–687`),
so estimates and the F3 gate already assume zero cache. The exposure is the
real-dollar claim motivating the whole build, and the two docstrings that
would become false.

**Minimal fix.** Add to the open questions (the design already has the right
slot): "does together's batch tier hit the prefix cache — measure the
`cached_input_tokens` field on a small pilot batch before committing to
batch-by-default"; make the engagement decision conditional on the *net*
number. Update the two cache docstrings when batch mode lands.

**Confidence: high** that it's unexamined; **medium** on the magnitude
(depends on unverified provider behavior — which is the point).

---

## F7 (MEDIUM) — The health-checkpoint benefit was a property of strict BFS, which the design then rejected; the claim survives the ruling it lost

**Defect.** The layer section claims:

> "Health telemetry gains a natural checkpoint: score the whole layer before
> paying for the next (the golden-free bands would have caught tonight's
> degenerate leaf one layer early, before its unwind consumed it)."

The engagement section then rejects strict BFS by name. Under the ready
queue there is **no** point where the run holds still between a leaf's
collection and its dependents' submission: a degenerate leaf's siblings may
already be done, so its unwind becomes ready at the same collection tick and
can ride the very next flush. `_health` only *prints* warnings
(`recurse_driver.py:725–747`); nothing gates on them. The claimed benefit
quietly evaporated when the layer design did, and the doc still advertises
it.

**Minimal fix.** Either retract the sentence, or make it true cheaply: a
flush-time hold — a dispatch whose input artifact carries a health warning
(density band, zero-needs) is not enqueued until acknowledged (flag or
`--force`), i.e. the check moves from "print at collection" to "gate at
enqueue of dependents." That is small, and it is the actual lesson of the
969-duplicate night.

**Confidence: high.**

---

## F8 (MEDIUM) — "One shared BatchQueue ... built ONCE" is real only for the transport 20%; both pipelines need their own resumable state machine, and translate's is misdescribed

**Defect.** The genuinely shareable piece is item 1 of the build plan:
submit/poll/fetch + envelope normalization + ledger routing. That is the
easy part. What the "built ONCE" sentence glosses over:

- **translate.py's loop is clause-structured, not round-structured.** The
  design says "the run loop is already round-structured" — it is not:
  `run()` iterates clauses serially and each clause runs its *entire*
  multi-attempt `repair_loop` to completion inside the iteration
  (`translate.py:1219–1330`). Round-batching requires hoisting
  `repair_loop`'s per-clause locals (`transcript`, `per_attempt`, `flags`,
  `prev_shape`, `res`) into per-clause state that survives between batch
  rounds — the same state-machine surgery as F1, done a second time on a
  different body of code.
- **Different everything around the seam:** config keys
  (`repair.max_attempts` vs `max_repairs`), success taxonomy
  (translated/abstained/abstained_under_repair/unrepaired + graveyard
  sampling + shape-diff flags vs. validated-or-raise), artifact discipline
  (translate writes prompt_user/raw/transcript per clause and `flush()`es
  run.json after **every** clause for crash-safety — a batched collector
  must preserve that ordering guarantee), and resume (the driver resumes
  from artifacts; translate has no mid-run resume at all, so F2's manifest
  is load-bearing for one pipeline and novel machinery for the other).

**Why it matters.** The claim sets the effort estimate and invites building
the shared component first and "wiring it in" on an implementation tier —
where the wiring is the design-hard part.

**Minimal fix.** Restate honestly: shared = transport + envelope + manifest
format; per-pipeline = a scheduler each (driver: dependency graph over the
tree; translate: rounds over surviving clauses). Estimate each separately.

**Confidence: high** (all from code structure).

---

## F9 (MEDIUM) — "the mock client already simulates layers for free" is false: MockClient is call-order-dependent

**Defect.** `MockClient.complete` does `self.replies.pop(0)`
(`recurse_driver.py:561–572`): canned replies are consumed in the exact DFS
order the serial driver makes calls. Any batch scheduler — even one that
collects a job and iterates results in provider order — changes the call
sequence, so the mock hands the root-division reply to a leaf dispatch and
the free end-to-end test fails or, worse, passes by coincidence on small
trees. The design leans on this: "(the mock client already simulates layers
for free)".

**Minimal fix.** Key mock replies by dispatch identity (span + phase — the
same deterministic custom_id F2 needs anyway) instead of order. Small, but
it must be *in* the plan or the pin suite goes red on day one and gets
"fixed" by reordering canned replies to match the scheduler — a test welded
to incidental ordering, the exact anti-pattern the repo's no-pinned-counts
rule exists to prevent.

**Confidence: high.**

---

## F10 (LOW/D) — Alternatives review: what was rejected, and what was never named

- Rejections (a) global `--batch` and (b) depth-trigger: **sound**, for the
  reasons given; (b) genuinely is subsumed by pending-size.
- Rejection (c) strict BFS: **sound as scheduling**, but it silently took
  the health checkpoint with it (F7) — the rejection needed a "what we lose"
  line.
- **Never named, and should have been rejected by name or adopted:**
  *bounded concurrent live calls* (a small worker pool, 3–5 in flight, over
  the existing blocking `call()`). The stated motivation is serial
  per-call grinding plus live-tier degradation; a pool attacks the first
  directly with **none** of F1–F5 (no control-flow inversion — threads keep
  `call()`'s blocking loop intact; ceiling stays per-call; no job manifest;
  no batch failure taxonomy), at the cost of forgoing the discount and not
  dodging live-tier 503s. It may well lose to batch on Matt's actual
  trigger (provider degradation + discount) — but the design's own rule is
  that tempting alternatives get rejected *by name with grounds*, and the
  cheapest one is missing. Relatedly, the open question "batch turnaround
  SLA (minutes vs hours)" is not a footnote: at hours per round, a
  3-repair-round poison-ish node costs most of a day, and the pool
  alternative dominates. The SLA answer should be a *gate* on the build
  order, not a question asked after the build.

**Confidence: high** that the alternative is unnamed; **medium** on which
one wins (depends on the unverified SLA and discount answers).

---

## Summary table

| # | Severity | One line | Fix cost |
|---|----------|----------|----------|
| F1 | Critical | Blocking recursion + `call()` locals can't host the ready queue; build plan still points at the design the doc rejected | design section + honest re-estimate |
| F2 | Critical | Submitted-uncollected batch is invisible to artifact-resume → double pay under a hard cap | job manifest + collect-before-enqueue sweep |
| F3 | High | Spend ceiling enforced post-hoc per call; batch commits N calls first | worst-case submit gate |
| F4 | High | `reply_schema`/`_schema_rejected` are client-global; batch needs per-request bodies and a live schema probe | thread schema per request; probe on root call |
| F5 | High | No failure taxonomy; all recovery today is exception-string matching that data-shaped batch errors never trigger | one-page failure table |
| F6 | Medium | Discount claim not netted against prefix-cache loss; ledger safe, real dollars and two docstrings not | pilot-batch measurement, netted decision |
| F7 | Medium | Health-checkpoint benefit died with strict BFS but is still claimed | enqueue-time health hold, or retract |
| F8 | Medium | "One BatchQueue built once" covers the transport, not the two per-pipeline schedulers; translate loop is clause- not round-structured | honest scope split |
| F9 | Medium | MockClient is call-order-dependent; "simulates layers for free" is false | key mocks by dispatch id |
| F10 | Low/D | Bounded concurrent live calls never rejected by name; SLA open question should gate the build | add the rejection or the pilot |
