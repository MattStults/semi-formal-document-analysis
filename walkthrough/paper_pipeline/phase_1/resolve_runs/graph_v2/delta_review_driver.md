# Clean-context adversarial review — UNREVIEWED DELTA (recurse_driver.py + dispatch_core.py)

Date: 2026-08-11. Reviewer: clean-context agent (Fable tier). Scope: ONLY the delta since
driver_layer_review.md / dispatch_core_review.md, per EXPERIMENTS.md from "MATT'S
ARCHITECTURE RESTORED" onward: transcript continuity, the new autofixes (provides_side_child
0 drops, F5-as-drop), per-phase caps + max_tokens_override, unwind grammar caps, the
reply-size contract, unwind_inputs single-sourcing, run_resolution_pass + its prompt,
authority convention in leaf_extra, transient ladder extensions (402/429), fingerprint
subset loosening. Method: full read of both files against the prior reviews' covered
state, the 78-test suite (all green, 96s), and seven executable probes
(`scratchpad/delta_probes.py` — every CERTAIN finding below shows probe output).
No API spend.

**Headline: the delta was applied to the serial Driver but only PARTIALLY to
dispatch_core — and batch is now the DEFAULT execution mode.** The restored architecture
whose absence explained ds2's edge-recall 0.32 does not exist on the path the next build
will take.

---

## D1. dispatch_core silently drops four delta behaviors the serial path has — CERTAIN, rank 1

**Defect.** Scheduler/executors were not updated when the delta landed in the Driver:

- `_want_unwind` (dispatch_core.py:350–384) builds a plain-string unwind user prompt —
  **no transcript_continuity reconstruction** (Driver.unwind:1133–1147 has it) — and pins
  the uncapped `("unwind_decisions", R.UNWIND_SCHEMA)` instead of
  `unwind_schema(len(dangling), len(nodes))` — **no unwind grammar caps**.
- `_want_leaf` (317–337) calls `R.validate_leaf(o, lo, hi, lines)` without
  `derive_uncovered` and uses bare `R.leaf_extra` — **derive_uncovered=true is ignored**:
  the model is never told not to emit `uncovered`, LEAF_SCHEMA (requiring `uncovered`) is
  used, ds2 validation semantics apply. (The leaf grammar cap `R.leaf_schema` IS wired —
  the delta is half-applied.)
- `SerialExecutor._send` (524–531) sets `reply_schema` but never `max_tokens_override`;
  `BatchExecutor._request_body` (867–885) uses `self.prov.max_tokens` (32768). **The
  per-phase output caps (division 8K / leaf 24K / unwind 8K) never engage in ANY core
  mode.** driver_config.json's own `_max_tokens` note ("every phase call carries its own
  cap") is false off-serial, and the head-to-head entry's "the size contract + per-phase
  caps held" is unsupported — the caps were not applied in either mode measured.

Probe P2 (ds3 cfg, mock replies, serial Driver vs `run_build(..., "serial")`): driver leaf
prompt carries the derive addendum, core's does not; driver unwind is
`[user, assistant, user]` messages, core's is a single string. The equivalence pins cannot
see this: test_dispatch_core.py contains zero references to transcript_continuity /
derive_uncovered / unwind_schema — the pinned cfg has every ds3 flag off.

**Consequence.** driver_config.json now ships `execution.mode: "batch"` +
`transcript_continuity: true` + `derive_uncovered: true`. The next build inherits the
resolution pass and authority convention (those are shared) but silently runs WITHOUT
continuity, without derived uncovered, without unwind caps, without phase caps — the exact
"design substitution" failure mode the RESTORED entry records, reintroduced by default.

**Minimal fix.** Single-source the dispatch construction the way `unwind_inputs` and
`leaf_extra` already do: factor Driver.divide/leaf/unwind's (extra, schema, validate,
user) construction into module functions both paths call; minimally — `_want_leaf`
mirrors the derive branch, `_want_unwind` calls `unwind_schema` and reconstructs the
continuity transcript (DispatchState.user already accepts what `next_request` returns —
seed the transcript with the three-message list), `_send`/`_request_body` apply
`PHASE_MAX_TOKENS`. Then pin: one equivalence test with all ds3 flags ON.

## D2. `_TRANSIENT_MARKS` missing comma: "Errno" and "HTTP 402" are dead — CERTAIN, rank 2

**Defect.** dispatch_core.py:426–427: `("… "urlopen error", "Errno" "HTTP 402",
"HTTP 429",)` — adjacent-string concatenation yields the single mark `"ErrnoHTTP 402"`.
Probe P1: `'HTTP 402 Payment Required'` → transient=False; `'[Errno 8] nodename'` →
transient=False. The delta ADDED 402/429 to Driver._complete (recurse_driver.py:936–943,
correct there); the port to the core's ladder broke 402 AND regressed the pre-existing
Errno mark. In concurrent/batch-live mode a laptop sleep/wake or a credit-propagation 402
aborts the run where serial retries it. HTTP 429 survived (own tuple element).

**Minimal fix.** Add the comma; better, replace the tuple with a shared
`R.is_transient(detail)` used by both ladders so the two lists cannot drift again. Pin
with a tuple-content or classification test.

## D3. run_resolution_pass applies structure_nodes/merges UNVALIDATED into the final graph — CERTAIN, rank 3

**Defect.** Both the validate lambda and the real apply call
`apply_decisions(nodes, dec, provides)` with `lo=hi=lines=None`
(recurse_driver.py:1351–1356). `apply_decisions` skips leaf-grade structure-node
validation when `lines is None` but the append loop still runs. Probe P6: a hallucinated
`L900-999_ghost` node (span outside the document, fabricated quote) sails through
validate, is appended, and lands in the returned root graph. The pass's prompt says
`"structure_nodes": []` but `unwind_schema` grants up to 8, and merges up to
`n_nodes//2` — a merge here also runs with no unwind context. Secondary: the real apply's
`errs` are discarded (deterministically empty today because validate ran the same call on
a deep copy — but silent by construction, one refactor from a masked failure).
Post-hoc graph_check would flag the bad span, but as an adjudication candidate, not a
refusal — the artifact is already written.

**Minimal fix.** The pass's ONLY job is resolutions: in `run_resolution_pass`, use a
schema with `structure_nodes`/`merges` `maxItems: 0` and error in the validate lambda if
either is non-empty; assert `not errs` after the real apply.

## D4. F5-as-drop: semantics SOUND, but the guard is bypassable by a duplicated provides name — CERTAIN, rank 4

**Attack result (the dispatch's F5 question).** The promotion from error to autofix-drop
is correct: a dropped self-satisfy leaves the need DANGLING and visible (escalates upward,
re-enters the dedicated resolution pass, leaves a `DROPPED self-satisfying` line in
unwind_log), so nothing is encoded by absence — versus 4 paid repair rounds that bought
nothing. The genuine-mis-model case (needer wrongly contains both definition and use, so
every pass re-proposes self-satisfaction) stays visible as a persistent dangling; it is a
granularity smell readable only in unwind_log, worth a health counter, not an error.

**But the guard itself has a hole.** `provides.get(newname) == [n["id"]]`
(recurse_driver.py:571) is a LIST equality. Probe P3: a node providing `target` TWICE
(nothing forbids duplicate provides names within a node) gives `provides["target"] ==
[id, id] != [id]` — the self-satisfying resolution APPLIES and the need is resolved
against its own node, exactly what F5 exists to stop.

**Minimal fix.** `if set(provides.get(newname, [])) == {n["id"]}`. Pin with the
duplicate-provides case.

## D5. Continuity's reconstructed transcript replays driver log-lines as the model's own words — CERTAIN, rank 5

**Attack result (the dispatch's fidelity question).** The reconstructed assistant turn is
`json.dumps(stored)` where `stored` strips only `_`-prefixed keys
(recurse_driver.py:1143–1146). Probe P4: after a gap autofix, the replayed "assistant"
reply contains post-autofix spans `[[1,20],[21,40]]` where the model actually said
`[[1,15],[21,40]]`, PLUS the key `"driver_autofixes": ["gap closed: child ending 15
extended to 20"]` — driver telemetry presented as the assistant's own prior output.

Ruling on the span half: replaying the POST-autofix division is the defensible choice —
the children were built on the fixed spans, and replaying the raw reply would make the
divider's "own" division contradict the U-report it must now reconcile — but that choice
is currently transcript-only reasoning; write it into the code comment as a decision with
the rejected alternative (raw-reply replay) named. The `driver_autofixes` leak has a
behavioral edge: the model sees an unfamiliar key in its "own" JSON (teaching it to emit
one, and showing repair-machinery text mid-conversation). Repair rounds are also
collapsed to one clean exchange — same fidelity class, same justification, should be in
the same recorded ruling.

**Minimal fix.** `stored.pop("driver_autofixes", None)` alongside the `_`-key strip; one
comment recording the post-autofix-replay ruling. (Seeds reconstruction checked: same
`seeds` object flows to divide and unwind in build(); dispatch_block is deterministic —
byte-identity holds, probe-verified via the prefix.)

## D6. Caps interaction: the grammar admits leaves the token cap cannot express — HIGH (arithmetic probe), rank 6

**Defect (bounded, loud).** Probe P5 on live ds3 artifacts: mean node ≈556 chars, so a
300-line leaf's grammar allowance (maxItems 210 = 0.7/line) is ~33K tokens against
`PHASE_MAX_TOKENS["leaf_graph"] = 24576`. The cap binds at density ~0.52/line — INSIDE
the band the density ceiling's own comment blesses for "legitimately list-like" regions
(>0.35, ≤0.7). Such a leaf truncates on every draw; the ladder resamples 6 times (same
cap, same result — paid each time up to the dispatch budget) and the terminal diagnostic
says "reduce leaf_max_lines or **raise model.max_tokens**" — which `max_tokens_override`
makes INERT for this phase; the operator's documented remedy does nothing. Not observed
in ds3 (modal spans are smaller), but constructible from a 300-line dense-list span.

**Minimal fix.** (a) The diagnostic must name `cfg phase_max_tokens` (and say
model.max_tokens is overridden per phase); (b) floor the leaf cap on its own grammar:
`max(24576, maxItems * ~110 toks)`, or derive one from the other so the two ceilings
cannot disagree. Also detect cap-truncation before paying 6 identical resamples (the
ladder knows the cap it sent).

## D7. Minor (LOW, ranked last)

- **Fingerprint subset loosening: safe as written, but the delta's own flags never
  entered the fingerprint** (probe P7). Comparing only `meta`'s keys still refuses on any
  differing value and on a missing key; only EXTRA stored keys are ignored — the loosening
  itself is the right shape. The gap: `transcript_continuity` / `derive_uncovered` /
  `rename_candidates` / `phase_max_tokens` change call semantics but not
  `run_meta.json`, so a ds2 tree resumes under ds3 flags into a mixed-semantics build.
  The mid-ds2 `derive_uncovered` flip was a deliberate, logged instance of exactly this —
  so either add the flags to the fingerprint now, or record the acceptance by name.
- **The Phase-D extra string now exists in THREE copies** (Driver.divide,
  Driver.unwind's continuity reconstruction, Scheduler._want_division). Drift between the
  first two silently breaks the reconstructed transcript's byte-identity — no error, just
  a cache-missing, subtly diverged replay. This file's own `leaf_extra` docstring records
  the three-copies lesson. Hoist to one `divide_extra()`.
- **EXPERIMENTS.md head-to-head accuracy**: "the size contract + per-phase caps held"
  overstates — per D1 the caps were never applied in either measured mode; the runs
  simply never needed them. One-clause correction when D1 is fixed.
- `unwind_schema`'s `cross_link_report` cap (`n_dangling + 10, min 20`) can undercut a
  division with many expected_cross_links and few danglings; the report is advisory and
  unvalidated, so worst case is silent report truncation. Note or key it off
  `len(division["expected_cross_links"])`.

**Not findings (attacks that failed):** provides_side_child-0 drops — both variants
correctly encode provided-elsewhere by absence; the dropped entry is quarantined via
`_dropped` and stripped in validate_division before persistence, autofix-logged, and the
dangling still escalates (no information lost). Reply-size contract is prose-only
pressure with the grammar caps as the actual bound — consistent. `unwind_inputs`
single-sourcing is real (smoke and driver share it; checked both callers).
`run_resolution_pass`'s provides index vs in-place mutation: resolutions don't touch
`provides`, validate runs on a deep copy, real apply is deterministic-identical — the
mutation-order attack finds nothing (the injection hole is D3, not ordering). Backup
ordering (pre_resolution written before apply) correct. `bill()`/budget parity for the
new 402/429 retries correct in serial; the core's ladder bills failed draws per R1 as
documented.

---

## Suggested order

D2 is a one-character fix — do it first. D1 is the substantive one and should block the
next live build (the default mode currently discards the campaign's headline change);
its fix is mostly deletion-by-sharing. D3 and D4 are three-line guards with pins. D5 is
a one-line pop plus a recorded ruling. D6 is a diagnostic correction now, a cap
derivation when convenient. D7 items are each one honest sentence or one hoist.

Suite after review: 78/78 green (nothing here regressed by reading); probes:
`scratchpad/delta_probes.py`, all seven reproduce.
