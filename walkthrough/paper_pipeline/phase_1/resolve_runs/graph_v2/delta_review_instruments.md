# Delta review — recent unreviewed instruments (2026-08-11)

Clean-context adversarial review, follow-on to `instruments_review.md`. No API
spend: every number below is a deterministic local probe or static reading.
Model tiers: items 1/4/5 on the strongest available tier (orchestrating
session); items 2/3 dispatched to a clean-context frontier-tier subagent
(opus) with its own probes against the stored graphs.

Scope: (1) `walkthrough/link.py` corpus-scope preamble handling + the pyclingo
diagnostic cap; (2) `resolve_pass.py` + `smoke_authority.py`; (3)
`link_nodes.py` post-rewrite; (4) verification/application of
`translate_exec_review.md`'s fixes; (5) the six failing `test_link.py` tests.

Verdict summary: **(1) instrument sound, one HIGH latent hazard (silent
20-message cap) for future corpora; (2) FINDINGS — a smoke_authority PASS does
NOT certify the convention's intent; (3) FINDINGS — the readiness headline
number is self-contradictory; (4) confirmed ABSENT, now applied and pinned;
(5) five fixed, sixth diagnosed below.**

---

## 1. link.py SHARED_PREAMBLE / dedupe_shared_preamble — sound; the cap is a real hazard

### The dedupe itself and its five tests: clean

* `dedupe_shared_preamble` (link.py:747) strips by exact stripped-line match
  against `SHARED_PREAMBLE` only, keeps the first copy across the set, writes
  copies into numbered subdirs (equal basenames cannot collide), and is
  applied by `collect()` only at `len(paths) > 1` (link.py:883) — the
  single-module byte-identity contract holds and is pinned
  (`test_corpus_single_module_path_is_untouched`).
* The five tests cover the right adversarial surface: link-clean at corpus
  scope, detector-still-fed after dedup (`undeclared_dep/1` surfaces), a
  genuine non-preamble `#const` redefinition still errors, and the
  text-not-import correspondence with `render_lp` is pinned including the
  "no OTHER #const line" direction. No finding.
* Cosmetic only: at corpus scope the `clingo-error` message text quotes paths
  under the `link_corpus_*` tmpdir, not the artifact paths. The `where` field
  carries the real basenames, so nothing is misattributed.
* Edge, accept by name: a single FILE that is itself a hand-concatenated
  corpus (preamble twice in one file) is not deduped (`len(paths) == 1`) and
  errors loudly — the conservative direction.

### The 20-message cap — probe-confirmed, and FULLY silent

Probe (scratchpad `many.lp`, 30 head-less atoms, this venv's clingo):
`python -m clingo` emitted **exactly 20** "atom does not occur in any rule
head" messages, **no truncation marker of any kind, exit code 0**. There is
nothing in the blob for `collect()` to notice.

Consequences for `collect()` (link.py:894):

* `headless` is truncated at 20 distinct diagnostics at corpus scope.
  `unresolved-reference` errors are computed as `headless − declared`, so an
  **undeclared** head-less atom whose diagnostic falls past message 20 is
  silently never checked — a false "0 unresolved", the exact
  pass-indistinguishable-from-did-not-run shape `_check_clingo`'s docstring
  exists to kill, one layer up from where it was killed.
* **Is today's 0-unresolved trustworthy?** Yes, but only because of the
  out-of-band verification recorded in `STEPS34_READINESS.md` gap 1 (clingo
  API with the cap lifted: 36 unique head-less atoms, every one declared).
  That was a one-time manual check, not a guard in the tool; the tool alone
  cannot currently certify that number.
* **Is the cap a hazard for FUTURE larger corpora? Yes — HIGH, latent.** The
  14-module corpus already produces 36 head-less atoms (>20). The 593-node
  corpus will bury the cap by an order of magnitude, and WHICH names get
  `concept-declared`/`situation-input` notes is already cap-dependent
  (admitted in the readiness doc).

Recommended guard (NOT applied — outside this delta's mandated fix scope, and
it touches a reviewed instrument): in `collect()`, count `NO_HEAD` matches;
when the count equals the cap (20), emit a loud `error`-severity finding
("diagnostics truncated; unresolved-reference analysis is incomplete") — or
drive clingo through its Python API with `message_limit` raised, which the
readiness verification already showed works. Either way the 0-unresolved
claim becomes self-certifying instead of resting on a transcript-era check.

---

## 2. resolve_pass.py + smoke_authority.py — a PASS does not mean the convention's intent

Frontier-tier subagent review, probes reproduced against the real
`recurse/root/graph.json` and `runs/ds3/root_graph.json`. Headline answer to
the caller's question: **yes, the scorer is gameable exactly as feared — it
never looks at an edge.**

* **A-1 (HIGH).** `score()` (smoke_authority.py:97-121) inspects only the
  node's own `needs`/`provides` name strings via a token-set test
  (`canon_entry`, :87-94). It never resolves a name to a provider, never
  checks direction, never reads the `authority=` label being scored.
  Constructions measured at **frac 1.00 → PASS** (above the golden's 0.80):
  wrong authority level on every heading; per-section coinages with numeric
  discriminators (`guideline_authority_3997`, … — digits are token
  separators, so this is ds3's forbidden shape renumbered); one node spanning
  the whole range with `needs: ["authority"]` (1/1). A model that names
  canonically but attaches WRONG edges passes at full marks.
* **A-2 (HIGH).** The convention (`authority_convention.md:25-27`) requires a
  `needs` entry on every labelled heading; `score()` counts needs **OR**
  provides (:112). The golden's own span A scores **0/5 on canon_needs** and
  passes at 0.80 via provides — four unconnected per-section *providers* of
  the same name, structurally the ds3 defect spelled canonically (and a
  multi-provided name `graph_check.py:88` would flag). Since the golden
  PASS / ds3 FAIL asymmetry is the entire justification for live spend, a
  live PASS is not evidence the convention was followed.
* **A-3 (MEDIUM).** `resolve_pass.py:39-44` pre-commits the answer ("~1 in 10
  truly absent") and the run reports 115/119 resolved — v1 with neutral
  framing resolved zero, and nothing separates framing effect from real
  resolution.
* **A-4 (MEDIUM).** 4 of the 10 retained samples rename needs INTO
  `*_section_authority` coinages — the names the convention calls
  uncomparable plumbing; `resolve_pass.py:72` keeps `resolved[:10]` only, so
  the other 105 renames and the mutated graph are unadjudicable after the
  fact.
* **A-5 (MEDIUM).** `danglings_before` (per (needer, name) pair: 119) and
  `danglings_after` (distinct names: 37) are different units — a do-nothing
  run would report a fake 69% improvement. (This run lands at 4 either way;
  the metric, not this number, is broken.)
* **A-6 (MEDIUM).** Post-state is measured against the pre-mutation provider
  index, so a merge that retires a provider leaves its names counted as
  satisfied; `"dropped"` is computed by subtraction and silently absorbs
  merge/structure log lines.
* **A-7 (LOW).** Empty/malformed inputs FAIL, exceptions surface as error
  rows — fail-safe. But `validation_errors` never gates a PASS row, and the
  report has no aggregate verdict field.
* **A-8 (LOW).** `LEVELS` includes `platform` and `none`, which are not among
  the convention's five canonical levels; `none_authority` scores canonical.

Disposition recommendation: before any live spend gated on smoke_authority,
the scorer needs (i) needs-only as the verdict metric (or a ruling that
provides counts, recorded with grounds), (ii) an edge-truth component —
cheapest is: every canonical `needs` must have exactly one provider in-graph
and it must be the hub, which `graph_check.py` machinery can already express.

---

## 3. link_nodes.py post-rewrite — dedupe correct; the headline number contradicts itself

Verified clean first: artifact-dedupe ordering correct (0 mismatches vs
max-run-dir choice), no `norm_id` collisions, no missing `.lp`, no duplicate
concept rows, finding counts internally consistent, report reproduces live.

* **B-1 (HIGH).** `link_nodes.py:98` excludes self-provision from
  `requires_resolution`; `link.py:859-862` includes it. Same JSON therefore
  says 27 dangling pairs AND 23 `requires-unprovided` notes; three sigs
  (`harmful_instruction/1`, `authority_rank/2`, `stay_in_bounds_principles/1`)
  are called dangling for modules that define them themselves, and
  `stay_in_bounds_principles/1` appears as both dangling and the one
  successful resolution. `STEPS34_READINESS.md`'s "requires resolution 1/28"
  is quoted as a readiness number without documenting the unit mismatch.
  Needs a ruling: either self-provision is legitimate (then 27 overstates by
  3 and those modules have an undocumented declaration defect) or it is not
  (then link.py under-reports) — currently the report asserts both.
* **B-2 (MEDIUM).** 54 translated artifacts collapse to 14 modules; the 40
  losers are discarded with no count and no disagreement check — "0
  unresolved" is a property of one draw per node, not of the corpus. Cheapest
  fix: record `n_artifacts_considered` + per-node loser counts.
* **B-3 (MEDIUM).** `main()` always exits 0 and prints a success-shaped line;
  finding classes are encoded by key-presence, so "clean" and "clingo never
  ran" (empty blob → zero unresolved-reference findings next to one
  clingo-error) are indistinguishable to anything gating on the report shape
  or exit code. Today's report exits 0 over a live closure-conflict error.
* **B-4 (LOW).** A run dir with no `concepts.json` is skipped silently; its
  module's concepts then surface as `concept-not-in-table` errors —
  misattributed to the module rather than the missing input. Latent (all 14
  current modules have rows).
* **B-5 (LOW).** No test pins `link_nodes.py` — the only readiness-number
  producer in the directory without a `test_*.py`; B-1 and B-3 are exactly
  what a pin would have caught. Registration rule applies when one is added.

---

## 4. translate_exec_review.md fixes — confirmed ABSENT, now applied and pinned

The coordinator was right: none of F1/F2/F3 had been applied. Verified by
direct read before touching anything (line 310 still double-prefixed; `except
T.Phase1Error` still narrow; no sweep refusal in `_TranslateBatch.__init__`).

Applied per the review's minimal-fix prescriptions (`translate_exec.py`):

* **F2** — `_TolerantRunOne.run_one` now feeds `str(exc)` as the failure
  detail for `Phase1Error`s; the body's own handler adds the (re-raised) type
  name once, so exec run.json rows match serial byte-for-byte on the error
  path. Residual accepted by name, per the review: a `Phase1Error` subclass
  other than `ProviderError` is still recorded as `ProviderError: ...` in
  exec mode.
* **F3** — `run_one` catches `Exception`, delivers the failure into a PENDING
  clause (unparking the body thread, which writes its error rec), then
  re-raises when the exception was not a `Phase1Error` — serial-equivalent
  abort, no leaked parked thread. Non-Phase1 details keep the type-name
  prefix (serial writes no row for them, so there is nothing to be
  equivalent to).
* **F1** — honest-refusal variant: `_TranslateBatch.__init__` raises
  `T.Phase1Error` on a non-empty `manifest.sweep()`, and the module docstring
  now names batch kill-recovery as unsupported (the submitted, paid job of a
  killed batch run is abandoned). The design-tier per-clause-identity
  alternative from the review remains open and is rejected here by name for
  this delta: it is a design change and this pass runs at implementation
  tier.
* F4 (`"HTTP 429"` in `dispatch_core._TRANSIENT_MARKS`) is out of this
  delta's change scope, exactly as the review scoped it; still recommended.

Pins added (`test_translate_exec.py`, +4 tests, closing the review's
attack-4 blind spot — the equivalence fakes never raised):

* `test_provider_error_on_attempt_1_writes_the_serial_error_row` — serial vs
  exec run.json rows equal; error text pinned to the single-prefix form.
* `test_provider_error_mid_repair_writes_the_serial_error_row` — probe-P4
  path (failure on the repair round's request), previously untested; also
  pins the absence of `ProviderError: ProviderError`.
* `test_non_phase1_abort_still_unparks_the_clause_thread` — RuntimeError
  aborts the run, run.json is flushed, and every thread the run started
  terminates.
* `test_batch_mode_refuses_a_nonempty_inflight_manifest` — an orphaned
  in-flight record makes `_TranslateBatch` refuse with the documented
  message.

Suite: `test_translate_exec.py` 12/12 pass (was 8).

---

## 5. The six failing walkthrough/test_link.py tests

Root causes were TWO, not one:

* Four tests (`test_d1_requires_is_not_reported_as_unresolved`,
  `test_d1_unprovided_requires_is_its_own_non_error_status`,
  `test_d1_provided_requires_is_silent`, `test_d5_headers_are_parsed`)
  tripped the Q-22 D4b-level-2 rule: a borrowed `requires` name must carry a
  `concepts` gloss. Fixed by giving each fixture a `policy_class/2` concepts
  entry ("policy P is of kind K" — says something the name does not, per the
  anti-restate check). `test_d5_headers_are_parsed`'s expected concepts
  header now includes `policy_class/2`, which is the contract's intent: the
  borrow's meaning travels in the concept channel.
* `test_d4_a_file_clingo_refuses_is_a_loud_failure` failed for a DIFFERENT
  reason: `Module._coherent` now rejects the unsafe-head-variable shape
  itself, so the defect is no longer schema-renderable. Per the file's own
  fixture doctrine, the fixture is now a real render with the rule line's
  body variables swapped by hand (the byte-minimal hand-edit), with a drift
  guard asserting the rendered rule still has the expected shape.

Result: `test_link.py` 40 passed, 1 failed — exactly the designated one.

### The sixth — `test_d4b_no_table_and_no_concepts_declared_is_silent` (left untouched)

What it needs is a RULING, which is why it is reported rather than fixed. Its
premise — "the m0255 worked example declares no concepts at all" — is now
false: the Q-22 fixture change gave `fixtures.m0255_module` a default
concepts entry (`restricted/1`), so `render(tmp_path, "plain.lp")` renders a
concept-declaring module and `concept-table-absent` fires correctly. Probe:
`schema.validate(fixtures.m0255_module(concepts=[]))` still VALIDATES, so the
mechanical fix is one argument — `render(tmp_path, "plain.lp", concepts=[])`
— restoring a genuinely concept-free fixture. But that silently detaches the
fixture from "the m0255 worked example" its docstring pins it to; the honest
alternatives are (a) `concepts=[]` plus a rewritten docstring that stops
claiming worked-example identity, or (b) accepting that the worked example
now declares a concept and retiring/redesigning the test's guard role around
a different concept-free module. Whoever fixed the other five should not make
that call as a side effect; it belongs to the owner of the Q-22 fixture
change. (The test's subprocess arm — first CLI line mentions the table
without shouting — was not reached and needs re-checking after the ruling.)

---

## Gates at close

* `phase_1` suite, `--ignore=resolve_runs`: **737 passed, 1 xfailed**.
* `walkthrough/test_link.py`: **40 passed, 1 failed** (the designated sixth).
* `graph_v2/test_translate_exec.py`: **12 passed**.
