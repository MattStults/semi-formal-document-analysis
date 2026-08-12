# Breadth-first batch execution (design, 2026-08-11)

**Status: DESIGN — not yet built.** Matt's observation: together.ai degrades
under high-volume live traffic (tonight's 503s, timeouts, and stochastic
truncations are consistent with that) but performs well on their Batch API,
which also prices at a discount. The recursion can't submit the whole tree
up front — child dispatches depend on parent divisions — but it CAN go
breadth-first.

## Graph build: BFS layers

The recursion is depth-first only by implementation accident. Layered form:

```
frontier = [root span]
while frontier:
    batch-submit every dispatch in frontier          # one Batch API job
    collect; validate/autofix each reply (unchanged code)
    frontier = all NEW child dispatches (divisions' children)
               + leaves are terminal
unwinds run bottom-up in layers the same way (all unwinds at depth d
depend only on completed depth d+1 artifacts)
```

Properties:
- Layer 1 has 1 call, layer 2 has 2-3, then ~9, then ~27 — the wide layers
  (leaves, the bulk of calls and tokens) are exactly where batch helps.
- Repair rounds batch too: collect all failed replies in a layer, submit
  one batch of repair transcripts, repeat up to max_repairs. Latency per
  round is a batch turnaround, but rounds are few and the wall-clock we
  actually lost tonight was serial per-call grinding.
- The per-node artifact/resume model is untouched: a batch result is just
  N replies written through the same validate -> autofix -> write path.
- Health telemetry gains a natural checkpoint: score the whole layer before
  paying for the next (the golden-free bands would have caught tonight's
  degenerate leaf one layer early, before its unwind consumed it).

## Translation: embarrassingly batchable, transcripts and all

Translation is per-node independent, so attempt-1 for ALL nodes is one
batch. The repair loop's multi-turn transcripts batch by ROUND:

```
round 1: batch(all nodes)                -> validate all
round k: batch(failed nodes' transcripts + findings)  -> validate
```

Each round's requests are self-contained message arrays (the harness
already builds them via _body_messages); nothing about the Batch API
conflicts with multi-turn — only with *interactive* multi-turn, which the
repair loop is not.

## Engagement rule (Matt's rulings, 2026-08-11, superseding the layer design)

Batch is OPTIONAL, and engages on ONE trigger: a ready-queue flush
threshold. The depth trigger is DROPPED (Matt: unnecessary if pending-size
works), and so is strict BFS layering, because it would hold ready work:
child dispatches of a fast parent would wait for slow siblings' parents.

**Ready-queue design** ("frontier" retired -- the queue holds every
dispatch whose inputs exist right now):

- Each dispatch that becomes ready (children of a returned division; a
  leaf span; an unwind whose children are all done; a translation node's
  next attempt) enters one queue.
- `batch.min_pending = K`: when the queue holds >= K requests, flush them
  as one Batch API job.
- Starvation fallback: when nothing is in flight and the queue holds < K,
  run the queued items LIVE -- the tail of a tree and the top of a tree
  never wait on a threshold they cannot reach.

Nothing is ever held waiting for a "complete set"; K only means "enough to
be worth a batch round-trip", and correctness never depends on what shares
a batch.

**Translation folds in tighter than the layer design assumed**: repair
rounds need no global synchronisation, since each node's round-k transcript
is self-contained. The queue may mix attempt-1 requests with round-3
repairs in a single batch job. One shared `BatchQueue` component therefore
serves both pipelines and is built ONCE.

Rejected by name: (a) global --batch switch (batches the serial
top-of-tree for pure latency); (b) depth-based engagement (subsumed by
pending-size, which measures the actual batch benefit); (c) strict BFS
layers (holds ready work on slow siblings).

## What to build (order)

1. `batch_client.py`: submit/poll/fetch for together's Batch API, same
   Provider/key/ledger plumbing, envelope-normalised to the existing
   `{text, usage}` shape so validators and autofixes are untouched.
2. Driver `--batch` mode: frontier loop above (est. ~1 day of work incl.
   pins; the mock client already simulates layers for free).
3. translate.py `--batch` mode: round-batched repair (simpler than the
   driver; the run loop is already round-structured).

## Open questions for Matt

- Batch turnaround SLA on together (minutes vs hours) decides whether
  repair rounds stay batched or fall back to live for small layers.
- Whether the ~50% batch discount applies to this model.

## Post-review resolution (2026-08-11, pending Matt's approval)

The adversarial review (batch_design_review.md) found the ready-queue
design uncomposable with today's Driver (F1: blocking recursion; call()
holds repair state in locals) and named an unconsidered competitor (F10:
bounded concurrent live calls). Matt's rulings: config-selected execution
mode; head-to-head on together.ai; share implementation where possible.

Resolution -- the two modes share MORE than they differ, because F1's
refactor is required by BOTH:
- bounded concurrency also cannot run 8 dispatches through call()'s
  local-variable repair state; and a killed process with 8 in-flight live
  calls has the same resume blind spot F2 names, smaller blast radius.

Shared core (built once):
1. DispatchState: one dispatch's lifecycle (draw -> validate/autofix ->
   repair-round-k -> done|failed), owning its transcript, budget, and
   artifact write. Replaces call()'s locals.
2. Scheduler: computes the ready set from the tree (or clause list) and
   feeds any executor. Health/tripwire checks per completed dispatch.
3. In-flight manifest (atomic, swept on resume): covers F2 for batch AND
   the concurrent-live resume blind spot.

Executors (the only divergence; config `execution.mode`):
- `serial` -- today's behavior, the reference implementation.
- `concurrent` -- semaphore of N live calls (config N).
- `batch` -- submit/poll/collect with worst-case submit gate (F3),
  per-request response_format bodies (F4), and a data-shaped failure
  taxonomy (F5).

Head-to-head: same build, same dispatches, run under `concurrent` vs
`batch` configs; score wall-clock, error rate, cost (incl. prefix-cache
delta, F6), and turnaround variance. Winner may be service- and
model-dependent -- which is WHY the mode is config, not code.

Estimated incremental cost of both-over-either: ~30-40% (the batch
executor + manifest + gate on top of the shared core).
