# REVIEW 2026-08-13 — graph_v2 campaign (pre-ds7 slice, deep adversarial pass)

**Verdict: PASS WITH CORRECTIONS.** The five claims marked FIXED in the
pre-ds7 review all hold under repro. The three deferred/accepted items are
correctly scoped LOW with bounded blast radius, and — important for an
unattended cost-gated run — every identified corruption path fails LOUD and
overstates (never understates) spend. No launch-blocking defect was found
(ds7 is already running on frozen commit 0a6d541; nothing below invalidates
the run). The new findings are in the *acceptance instrumentation*: the risk
queue double-counts root-unwind verdicts, the "hard" descend call cap is
per-dangling, and two honesty surfaces (spend banner, check exit codes) are
inert. Those matter for how ds7's pre-registered numbers get read, not for
whether the graph is trustworthy.

## Baseline

```
cd /Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis
semi-formal-experiment/.venv/bin/python -m pytest \
    walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/ -q
→ 140 passed in 100.62s   (2026-08-13, commit 8614f44)
```

Code reviewed at HEAD 8614f44; ds7 runs from 0a6d541. `git diff --name-only
0a6d541..HEAD` touches NO pipeline code (only EXPERIMENTS.md, ds7_status.sh,
the tier_spot probe, run artifacts, and the ledger), so this review covers
exactly the code ds7 is executing.

Evidence discipline: every finding below is marked RUN-verified (repro
executed from a `mktemp -d` scratchpad; scripts kept there) or INFERRED
(code citation only). No API/embedding/seat calls were made; all run
artifacts were read read-only. ds7 (pid 2216) was confirmed alive and
progressing via read-only inspection only.

---

## §1 Re-verification of the 9 prior dispositions

### 1. (HIGH, FIXED) CostGateError out of the seat loop + descend call cap — **CONFIRMED, with one correction (see F2)**

- `rename_seat.judge` retry loop re-raises the gate by class name:
  `rename_seat.py:116` `if type(exc).__name__ == "CostGateError": raise`.
  RUN: a `complete` raising `T.CostGateError` propagated after exactly ONE
  attempt (no re-bill); a generic error still retries 3× then fail-closes
  `different_concept`.
- Both seat call sites (`adjudicate_resolutions`, `greedy_rename_descend`)
  let it propagate: RUN — gate raised inside `adjudicate_resolutions`
  propagated out (the run stops loudly). The measured-spend gate fires
  inside `GraphClient._log_usage` (recurse_driver.py:1185) AFTER
  `super()._log_usage` appends to the ledger — ledger-before-raise ✓.
- Cap: `recurse_driver.py:1792` `budget_calls = …descend_max_calls, 600`;
  capped danglings recorded with `capped: True` and their ranked candidates
  (RUN-verified). **Correction:** the cap is checked once per DANGLING
  (line 1798), before the inner candidate loop, so a single dangling can
  spend up to 5 calls past the cap. RUN: cap=2 → 5 seat calls made. See F2.

### 2. (HIGH, FIXED) descend dedupe on (needer, name) — **CONFIRMED**

- `recurse_driver.py:1752-1764` dedupes the dangling list on
  `(node id, name)`. RUN: a node with TWO same-named dangling needs
  produced ONE seat-confirmed resolution; both entries renamed; no crash.
- The residual variant (the MODEL emitting the same (needer, name) twice)
  does not crash either, but via a different mechanism than the disposition
  implies: it is caught by VALIDATION (`apply_decisions` runs on a deep
  copy inside every call's validate lambda at all three sites), so it costs
  a repair round, not a build-end crash. RUN: duplicate proposals →
  `"resolution matched no needs entry"` error from `apply_decisions`.
  Caveat: `adjudicate_resolutions` itself does not dedupe (see F3).

### 3. (MED, FIXED) authority canonicalization reads upward — **CONFIRMED**

- `autofix_authority_coinages` (recurse_driver.py:387-420):
  `for ln in range(min(start, len(lines)), 0, -1)` — scans UP from the
  span's first line; `start = min(first line of each span)`.
- RUN: span [2,4] starting in a `authority=root` section and running over
  an in-span `authority=user` heading canonicalized to `root_authority`
  (the upward label), not the in-span one. No label at/above → autofix
  leaves it and `validate_leaf` errors FORBIDDEN (honest, RUN-verified).
- Live confirmation: ds7's own health.jsonl rows show the autofix firing
  ~50× so far (e.g. `use_preset_voice_section_authority -> system_authority`),
  enforcement working mid-run. Pinned test also present
  (`test_authority_coinages_autofix_to_the_spans_own_label`).

### 4. (MED, GUARDED) rename_seat + concurrent executor refuses at startup — **CONFIRMED**

- Guard: recurse_driver.py:1632-1640 raises `Phase1Error` when
  `mode == "concurrent" and cfg.get("rename_seat")`, before any spend.
- The race it guards is real: seat calls set the one-slot
  `client.reply_schema` outside `ConcurrentExecutor._body_lock`. Batch mode
  (ds7's mode) is safe: BatchExecutor is single-threaded for
  collection/live-rerun/adjudication, and batch bodies build
  `response_format` per request from `state.schema` (dispatch_core.py:1005
  `_request_body`), never from the client slot.

### 5. (MED, FIXED) gate passes recorded + queue walks the run tree — **CONFIRMED, with a double-count bug (see F1)**

- Gate passes: `adjudicate_resolutions` appends
  `{"verdict": "gate_pass", …}` to the record (recurse_driver.py:~1882).
  RUN: a ≥0.25-sim proposal recorded one `gate_pass` verdict, zero seat
  calls. The pre-registered "every applied rename carries a verdict or gate
  pass ON THE ARTIFACT" is now verifiable from artifacts.
- Tree walk: `risk_queue.py:36-40` globs `run_dir/**/graph.json`. RUN: an
  interior unwind verdict reached the queue. **But** the glob also matches
  the root unwind artifact `run_dir/graph.json`, and the root unwind's
  verdicts are ALSO in `root_graph.json` (the root unwind writes them via
  `g.update(meta)` and main() later writes the same object as
  root_graph.json) — RUN: the same verdict appears TWICE in the queue. See
  F1. Note the ds6 smoke (437 items) could not have caught this: ds6
  predates tranche 2, so no graph in that run carried any verdicts.

### 6. (MED-LOW, PART-FIXED) embedding spend unledgered — blast radius assessed

- Temp file is unlinked in `finally` (recurse_driver.py:1717) ✓ code-read.
- `_embed_texts` bills via raw curl to together's embeddings endpoint,
  outside `usage.jsonl`. Blast radius: one call per resolution pass that
  reaches descend; batched ≤64 texts/call at e5-large pricing ≈ $0.001/run
  (the recorded figure checks out: ds7's ~100-200 danglings = 2-4 embedding
  calls of ≤64+provider texts). Direction: UNDERCOUNT of ~$0.001 — tiny,
  disclosed. One correction to the record: embeddings are NOT "the one
  unledgered path" — the probe scripts (modal_adjudicate.py,
  canon_embed_probe.py, brief_sweep.py, tier_spot.py, sla_probe.py) all
  bill via direct curl too (see F9).

### 7. (LOW, ACCEPTED BY NAME) verdict cache keys on (prose, candidate) — blast radius assessed

- Cache lives only in `greedy_rename_descend` (`seen_verdicts`,
  recurse_driver.py:1788, key at :1805); `adjudicate_resolutions` has NO
  cache at all (RUN: two identical below-gate proposals cost 2 seat calls).
- Blast radius of the needer-blind key: two danglings with BYTE-IDENTICAL
  need prose share one verdict, and the second's recorded grounds cite the
  FIRST needer's passage. Post-authority-restructure ds7 makes this more
  likely, not less: canonical `root_authority`-style needs with templated
  prose recur across sections. Wrong-accept probability on a reused verdict
  ≈ the brief's measured FA (~0.12); wrong-reject leaves an honest
  dangling. Economy side is real (one seat call per template family).
  Severity stays LOW; reviewer-facing grounds-misattribution noted.

### 8. (LOW, FIXED) risk_queue cleanup + wiring — **CONFIRMED**

- Wired: `post_build_checks` (recurse_driver.py:1987, jobs list at ~2008)
  runs `risk_queue.py <run_dir>` on every build; RUN (synthetic run dir):
  builds offline, exit 0, prints counts.
- `.get` guards throughout; modal input is the run-local
  `modal_adjudication.json` (risk_queue.py:79) — ds6 ids cannot transfer.
  Residual gaps: interior `dropped_merges` never reach the queue (F1b) and
  `broken_promise` items are not deduped across resume rebuilds (F6).

### 9. (LOW, DEFERRED BY NAME) batch resume double-ledger + missing `_req_max` backstop — **CONFIRMED as described; blast radius bounded and safe-direction**

- 9a double-ledger RUN-verified: a killed-with-manifest sweep ledgers an
  orphan row; a resume sweep ledgers the SAME paid row again (artifact never
  written for non-ok rows, so the R5b artifact-witness skip cannot fire).
  Window = between `_log_usage` and `manifest.clear` in `_sweep`
  (dispatch_core.py:1318-1335). Blast radius: per crash-in-window, ≤ one
  job's non-ok/unwritten rows double-counted (a few cents at ds7 prices).
  Direction: OVERSTATE → the run ceiling trips early, never late. Safe.
- 9b RUN-verified: at sweep time `_req_max` is still the class default None
  (populated only in `_flush`), so `_classify` cannot apply the
  completion-tokens≥cap truncation backstop; a row at the cap with
  finish_reason=null classifies "ok". Blast radius ≈ nil in practice:
  truncated text is mid-JSON, so `parse_json_reply` fails and the normal
  repair path owns it (one extra round, mislabeled cause). The dangerous
  variant (truncated-but-parses) requires the cut to land exactly on a
  JSON boundary — measure zero.

---

## §2 New confirmed findings (ranked by how badly a wrong answer would mislead)

### F1 (MED) risk_queue double-counts root-unwind verdicts; interior dropped_merges never queued — RUN-verified

`risk_queue.py:36-40`: `verdicts = list(g.get("rename_seat_verdicts", []))`
(from root_graph.json) then adds every `**/graph.json`'s verdicts. Python's
recursive glob `run_dir/**/graph.json` MATCHES `run_dir/graph.json` (the
root unwind artifact — RUN-verified: glob returned both `graph.json` and
`c1/graph.json`). The root unwind's verdicts live in BOTH files, so every
root-level accepted rename enters the frontier queue twice.
Repro (synthetic run dir): verdicts {root-unwind, resolution-pass} in
root_graph.json + same root-unwind verdict in graph.json + one interior
verdict → queue contained `unwind L1-100` **2×**, `unwind L1-50` 1×,
`resolution pass` 1×.
Why it matters: ds7's acceptance expects the queue "dominated by
seat_accepted_rename + dangling_near_miss" — root-unwind renames will be
systematically inflated, and the frontier pass (runbook step 4, ~$1.80
budgeted on queue length) pays K3 to review the same item twice. Any
"every applied rename has a verdict" count built from the queue inherits the
inflation. (Fix direction: skip `run_dir/graph.json` in the walk, or dedupe
on (needer, name, rename_to, where).)
Companion gap (INFERRED): `dropped_merges` is read only from the ROOT graph
(risk_queue.py:69); interior unwinds' dropped merges — the actual ds6
merge-loop class — never reach the queue.

### F2 (MED-LOW) the descend "hard call cap" is checked per-dangling, overshoots up to 4 calls — RUN-verified

`greedy_rename_descend` checks `calls_made >= budget_calls` only at the top
of each dangling (recurse_driver.py:1798), then walks up to 5 candidates
with a seat call each (calls_made += 1 at :1809). RUN with
`descend_max_calls=2`: 5 seat calls made, 2 danglings correctly recorded
`capped`. So the cap is a per-dangling gate: worst-case overshoot 4 calls
(~$0.002 at Flash prices), and the TRUE hard cap is the run ceiling in
`GraphClient._log_usage`. No silent stranding — capped danglings keep their
ranked candidates — but the disposition's "HARD call cap" wording
overstates the mechanism. No test covers `descend_max_calls` at all.

### F3 (MED-LOW) adjudicate_resolutions has no verdict cache or dedupe — RUN-verified

Each gated proposal costs a fresh seat call even when (need prose,
candidate) is byte-identical to one already judged in the same pass (RUN:
2 identical proposals → 2 seat calls, 2 verdict records). The
`seen_verdicts` economy exists only in `greedy_rename_descend`. Model-emitted
duplicates are caught earlier by validation (so no double-apply), but
template-shaped danglings — exactly what the authority restructure produces
— will re-bill the seat per occurrence at every unwind level. Bounded (≤
dangling count per pass × $0.0004), but the economy was already measured
worth building for descend; the choke point itself lacks it.

### F4 (MED-LOW) the spend-invisibility banner is computed and discarded — code citation

`main()` ends with a bare expression statement
(recurse_driver.py:1659-1661):
`T.spend_invisibility_warning(client.p, client.spent_usd, client.calls)` —
`print` is missing and the function RETURNS its banner (translate.py:733
`return (...)`). ds7 will finish without the 72-exclamation visibility
warning ever reaching the log. The ledger rows exist, so this is
console-honesty only — but the function's contract ("the honest move is to
shout the number") is silently unmet on the campaign's largest run.

### F5 (MED-LOW) post-build check failures do not surface in the exit code — code citation

`post_build_checks` records each instrument's returncode as an `OK `/`!! `
console flag (recurse_driver.py:2023) and `main()` exits 0 regardless. An
unattended ds7 whose `graph_check` or `risk_queue` step fails still
"completes" — acceptance depends on a human reading
`postbuild_*.txt`. Combined with F11 (empty log until flush), the failure
surface for a check is the file itself and nothing else.

### F6 (LOW) broken_promise queue items can duplicate across resume rebuilds — INFERRED

`health.jsonl` is append-only (`_health` appends per build); a killed run
that rebuilds an interior unwind re-logs the same broken promises, and
`risk_queue.py:90-95` emits one item per row with no dedupe on
(unwind, name). ds6's queue already shows 55 broken_promise items after
five external kills — likely inflated. Review-noise class only.

### F7 (LOW) greedy-descend SKIP leaves no per-dangling record — INFERRED

On embedding failure the stage records ONE global `driver_autofixes` line
("greedy descend SKIPPED") and returns (recurse_driver.py:1706-1709): no
`descend_near_misses`, no seat rejections. The pre-registered expectation
"every residual dangling must … carry a seat rejection / near-miss record"
is then unverifiable per-dangling for the whole run (only the global note
proves the mode). Absence-over-wrong is preserved (danglings stay), but the
per-item evidence the acceptance criterion names does not exist in this
mode.

### F8 (MINOR) resume fingerprint omits behavior flags — INFERRED

`run_meta.json` fingerprints only brief/doc/model/leaf_max
(recurse_driver.py:1600-1603); `derive_uncovered`, `rename_seat`,
`greedy_rename_descend`, `enum_decisions`, `execution.mode` can change
between resumes without refusal. Mostly benign (artifacts are validated
outputs; the post-build stages rerun uncached), and the cost-ceiling
resume semantics are intentional — recorded so the next config flip is a
conscious choice, not a silent one.

### F9 (MINOR, record correction) "embedding calls are the one unledgered path" is inaccurate — code citation

Five probe scripts bill via direct curl, outside usage.jsonl:
modal_adjudicate.py:44, canon_embed_probe.py (canon+embed), brief_sweep.py:45,
tier_spot.py, sla_probe.py. Each is tiny (fractions of a cent; the 31-call
modal adjudication ≈ $0.001), but the handoff snapshot's uniqueness claim
is false, and modal_adjudicate.py also unlinks its temp file OUTSIDE a
finally (`os.unlink(name)` after subprocess.run — a timeout leaks it;
finding-6 class).

### F10 (MINOR) modal-drift wiring into the ds7 queue requires a manual adaptation step — INFERRED

`risk_queue.py:79` reads `<run>/modal_adjudication.json`; the only producer
is `modal_adjudicate.py`, hardcoded to `runs/ds6` and writing
`modal_adjudication_ds6.json` in the SCRIPT dir. Runbook step 3 owns the
adaptation; until it runs, ds7's queue silently has zero modal_drift items
and nothing says so. The expectation "modal drift verdicts reach the queue"
is one manual edit away from mechanically wired.

### Minor notes

| # | note | class |
|---|------|-------|
| N1 | ds7_log.txt is 0 bytes after ~2h (stdout fully buffered when redirected without `python -u`); runbook "check the log" is blind mid-run — artifact/health growth is the real signal | operational |
| N2 | `type(exc).__name__ == "CostGateError"` name-matching in rename_seat.py:116 is fragile to a rename/subclass; works today | robustness |
| N3 | `adjudicate_resolutions` gate lookup `need_prose.get((needer, name))` uses first-prose on duplicate same-name needs of one node (setdefault) — degenerate input, harmless | edge |
| N4 | `risk_queue.json` written non-atomically (`json.dump(open(path,"w"))`); regenerable, last stage | hygiene |
| N5 | `root_graph.pre_resolution.json` backup is written every pass incl. resume (variable still named `shutil_path`, recurse_driver.py:1972) — leftover name, correct behavior | cosmetic |
| N6 | seat calls on a killed-and-resumed unwind are re-paid (verdicts are in-memory only): "resume lossless" is true for artifacts and batch rows, not for adjudication work already spent | record precision |

---

## §3 Pre-registered expectations — checkability audit

| expectation | mechanically checkable from artifacts? | checker |
|---|---|---|
| zero mid-run interventions | YES, but no script | `git diff --name-only <launch-commit>..HEAD -- <pipeline paths>` — verified empty for pipeline code right now; needs pinning as a step |
| cost $0.20–0.40 | YES (agent D's ledger) | sum usage.jsonl rows provider=`graph-build` + the disclosed ~$0.001 unledgered embedding; no script in this dir |
| zero `section_authority` coinages | YES, trivial | grep root_graph names; enforcement already runs at leaf time. No pinned script |
| mismatched edges ≤ 7% | PARTIAL — **metric not pinned** | low-sim count is computable (risk_queue's `sim`), but the DENOMINATOR is nowhere defined: ds5 measures 82/934 resolved edges = 8.8% vs 82/1100 all needs = 7.5% (RUN). The record's "ds5's best ≤7%" matches neither cleanly — an acceptance reader must improvise, which is exactly the reinterpretation the census process forbids |
| danglings 20–80 | YES | graph_check prints `dangling (no provider): N` into postbuild_graph_check.txt; RUN on ds5 reproduces 166 (matches the record's ds5 figure) |
| every residual dangling external-by-design or carrying rejection/near-miss | PARTIAL | near-misses + seat verdicts are on artifacts; but (a) F7: embedding-skip mode records nothing per-dangling; (b) danglings the model never proposed carry no record at all — "external-by-design" is a prose judgment with no artifact |
| every applied rename carries verdict or ≥0.25 gate pass | YES in principle, no script | verdicts on artifacts (RUN: gate_pass recorded; seat verdicts recorded incl. `where`); cross-referencing applied renames (unwind_log "resolved …" lines across the tree) against verdict proposals is ~20 lines nobody has written. F1's double-count corrupts any queue-based count |
| buried failures ≤ 17, two categories ~0 | YES | repair_census.py runs/ds7 — offline, writes the run's census; RUN on ds5/ds6 reproduces 25/17 exactly |
| boundary objects (chain_of_command not dangling; no wrong-wiring) | HALF | chain_of_command: grep-able from graph_check's dangling list. "no wrong-wiring of external references": no mechanical signal — frontier review only |

**Net: 4 of 9 fully mechanical today, 3 partial, 2 need a script or a
judgment.** The dangerous one is the ≤7% band with an unpinned denominator.

---

## §4 Improvement opportunities (leverage-ranked)

1. **One acceptance script for the frozen bands** (~50 lines, offline).
   Input: run dir + launch commit. Output: each §3 row computed with the
   denominator PINNED in code, plus the intervention certificate via git.
   This converts the runbook's "read the log and compare" step — the place
   post-hoc reinterpretation can creep in — into a single deterministic
   artifact. Highest leverage: every later run inherits it for free.
2. **Fix the queue double-count** (F1): skip `run_dir/graph.json` in the
   walk (root_graph.json already carries those verdicts) or dedupe on
   (needer, name, rename_to, where); also gather `dropped_merges` from the
   tree, not just the root. One-line each; makes the frontier budget honest.
3. **Per-call cap check** (F2): move `if calls_made >= budget_calls` into
   the candidate loop (record the rest of the current dangling as capped).
   Trivial; makes the "hard cap" claim literally true.
4. **Print the banner, propagate the checks** (F4/F5): `print(…)` the
   spend warning; have `post_build_checks` return/exit non-zero (or print a
   terminal "N checks FAILED" summary an unattended log can't miss).
5. **Verdict cache in adjudicate_resolutions** (F3): same (prose, candidate)
   key descend already uses — template danglings then cost one seat call per
   family per pass, and the recorded economy becomes measurable.
6. **Launch with `python -u`** (N1) or flush at each health row, so the
   runbook's log-tail step works mid-run.
7. **Persist the verdict cache per run** (tiny disk file, key-on-argv like
   the probes): a crash in the finale currently re-pays every seat call on
   resume (N6). Also makes finding-9-style windows cheaper.

---

## §5 What I did not check

- Other agents' slices, beyond interfaces: `seats.py`/readback/mutate_*
  (B), `translate.py` internals beyond Client/ledger/envelope contracts (A),
  `model/guard.py`/`eval.py`/spend ledger internals (D — I verified only
  that this slice's rows reach `_append_usage`).
- `dispatch_core` ConcurrentExecutor under live load (read-only analysis;
  the seat+concurrent guard makes it unreachable in ds7's config).
- Statistical validity of the golden labels underlying brief_sweep's
  adopted-brief numbers (label noise is acknowledged in the record; the
  FA audit method is sound but n=5).
- graph_compare/parity/tooling outside the rename-risk-leaf-merge-batch
  scope; the `run1..run5`/`hh_*` probe trees.
- ds7's live behavior beyond read-only liveness (pid alive, 43 artifacts
  written, authority autofix firing in health.jsonl, log empty by N1).
- Whether together's batch API can return a row whose JSON is complete
  despite completion_tokens ≥ cap (9b worst case; assumed measure-zero).
