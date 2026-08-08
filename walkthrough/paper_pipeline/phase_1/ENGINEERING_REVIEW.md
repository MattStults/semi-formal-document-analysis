# Adversarial engineering review — `phase_1`, `link.py`, and today's repair loop

**Reviewed 2026-08-07 ~15:50–16:20.** Nothing was spent; no `--live`; no git. Files were read
from the working tree and mutation-tested in a **copy** under a scratchpad — the repo tree was
never written to except for this file.

⚠️ **Moving target.** `translate.py` changed under me mid-review (a `close()` helper appeared in
`repair_loop` at 15:53). Everything below is against these bytes:

```
translate.py 1e4879e142626fde1bbec3cab68cea03      checks.py  f1c30df421b8a8e4bdd909840ba95b20
schema.py    35ca9510cc7ca70b506150735aa9ee4e      link.py    34650bbb0f30e47cc83da94f1a0ab8f0
```

Baseline confirmed before attacking: `pytest walkthrough/ -q` → **209 passed** (task brief said
207; two more have landed since). `translate.py --self-test` → **53/53**. `mutate_schema.py` →
**0 survivors, exit 0**.

Every finding below was **run**, not inferred, unless it says otherwise. Repro scripts are in the
scratchpad; each finding states the inputs and the wrong output.

---

## F1 ⭐ `run()` writes an **unrepaired** module out as `status: "translated"`, exit 0

`translate.py:1074` — `if out.module is None:` is the *only* failure branch after `repair_loop`.

`repair_loop` does its job: on exhaustion it returns `status="unrepaired"` with the surviving
findings. But it also returns `module=` the last *constructible* module. Whenever the surviving
findings are **link**-origin (`beats-cycle`, `rule-shape`, `closure-conflict`, `clingo-error`,
`concept-not-in-table`) rather than schema-origin, `mod` is non-`None`, so `run()` takes the
success path, and line 1108 `rec.update(..., status=obj.outcome, ...)` overwrites `out.status`
with the module's own `"translated"`.

**Concrete case.** Clause `m0091`, `repair.max_attempts=2`. Attempt 1 = `test_repair.BROKEN`
(schema breach → repair fires). Attempt 2 = the same module with two `beats` entries forming a
cycle (`m0037 beats m0053`, `m0053 beats m0037`) — schema-valid, and `checks.run_checks` returns
`outcome="invalid"` with `('beats-cycle', 'error', 'the beats relation is cyclic … a
defeat-based encoding returns a confident answer on a cyclic superiority')`.

Observed output:

```
  ↻ m0091: repaired on attempt 2
  ✓ m0091: 1 asserts, 2 beats, … closure {'produce': 'cepa'}
1 translated, 0 abstained, 0 failed.
EXIT 0
run.json: status="translated"  attempts=2  flags=[]   (no `surviving_findings` key)
m0091.lp and m0091.json written to disk
```

The correct output is `status="unrepaired"`, `failures += 1`, exit 1, and no `.lp`.
`STEP_stage2_and_repair.md` §5 and its TDD item 5 say exactly this: *"exhaustion is
`status: "unrepaired"` — recorded, never an exception, **never a silent pass**."* It is a silent
pass, at the `run()` boundary.

**Why no test caught it:** `test_exhausting_max_attempts_is_RECORDED_not_raised_and_not_passed`
exercises `repair_loop` in isolation, and its fixture (`BROKEN`) fails at *schema* level, so
`module` is always `None` and the run-level branch is never reached.
`test_a_live_run_WIRES_the_loop_and_records_what_it_did` is the only run-level test and it scripts
a *successful* repair.

---

## F2 ⭐ A `ProviderError` during a repair attempt aborts the **whole run** and loses the record of the clause already paid for

`translate.py:1032-1040` wraps `client.complete` in `except Phase1Error`. The `repair_loop` call
at 1065 sits **inside the `except ResponseParseError` handler**, outside that guard. A
`ProviderError` from `complete_messages` (HTTP 500, empty response, truncation) propagates out of
the per-clause loop, out of `run()`, and is caught by `main()`'s `except Phase1Error` → exit 2.

Worse: `results.append(rec)` for the in-flight clause happens *after* the repair block, so the
`finally: flush()` writes a `run.json` with **zero results** — for a clause whose attempt-1 call
was already billed.

**Concrete case.** Select `m0091, m0037, m0053`; stub `complete` returns `BROKEN`,
`complete_messages` raises `ProviderError("HTTP 500: upstream hiccup")`:

```
writing to …/t
ESCAPED: ProviderError HTTP 500: upstream hiccup
run.json → clauses recorded: []   of 3 selected
```

The identical error on attempt 1 is a per-clause `status="error"` and the run continues. This is
the priority-1 shape verbatim: the tested path (attempt 1) and the executed path (attempt ≥2)
differ, and the difference is only visible live.

---

## F3 ⭐ Stage 2 never runs on a module that passes the schema — `link.py`'s half of stage 2 is unreachable in a live run

`run()` decides whether to check by whether `parse_module` **raises**. `parse_module` calls
`schema.validate` only. So `checks.run_checks` — and with it every `link.py` check: D1a compile,
D5 rule-shape, #17 beats-cycle, closure declarations, the concept table — is reachable **only
through the repair path**, i.e. only for modules that already failed the schema.

**Concrete case.** Same cyclic-`beats` module as F1, returned on **attempt 1**:

```
  ✓ m0091: 1 asserts, 2 beats, … 1 out-tokens
1 translated, 0 abstained, 0 failed.
run.json: status="translated"  attempts=1   (no flags, no findings, no transcript.json)
```

A module with a cyclic superiority relation — the failure `03_pipeline.md` calls problem #17 and
which `link.py` has a dedicated DFS for — is written out clean. The better a module is, the less
it is checked.

Corollary: with `repair.max_attempts: 1` (the documented way to disable repair, and `run()`'s
default when the `repair` block is absent — `cfg.get("repair") or {}`, line 937), `checks.py` is
**never called at all** in a live run.

---

## F4 ⭐ The "worst case" cost estimate is an **under**-estimate as soon as repair runs

`estimate_cost` (line 778) grows *input* triangularly in `max_attempts` but only over
`len(system) + len(user)`. It never bills the **previous completion** as input on the next call —
and that completion is worth up to `max_tokens = 16384`, ~12× the user block.

Measured against the shipped config (`m0091`, `max_tokens=16384`, `[0.14, 0.28]`/Mtok):

| `max_attempts` | printed "cost (worst)" | true worst case | under by |
|---|---|---|---|
| 2 (**shipped**) | $0.012555 | $0.013560 | **8.0 %** |
| 3 | $0.020522 | $0.023706 | 15.5 % |
| 4 | $0.029616 | $0.036153 | 22.1 % |
| 5 | $0.039836 | $0.050901 | 27.8 % |

(true worst = system + user for attempt 1; then per attempt *k*: system + the short clause turn +
(k−1)×`max_tokens` of prior completions + error logs; output = `max_tokens` × attempts.)

The config comment says *"Deliberately the full max_tokens, i.e. the worst case … Overstating an
estimate is survivable; understating is how a hard cap gets passed."* The estimate is on the wrong
side of its own stated rule. The gate is small in absolute terms ($0.25/run) so nothing has burned
yet, but the direction is the one the design says must never be wrong.

Two related notes: (a) `cost.max_cost_usd` is **per invocation**, and nothing anywhere compares a
run against the remaining $8.50 — combined with the documented `spend.py` invisibility, repeated
runs accumulate unmetered; (b) the sign of the error is partly masked because the estimate
*over*-charges the full user block on every repair turn while the loop only re-sends a 491-char
clause turn (see F5) — two errors in opposite directions, neither intended.

---

## F5 ⭐ The repair transcript's first user turn is **not what was sent** — repair loses every cross-reference

`repair_loop` (line ~2109) synthesises its own opening turn:

```python
transcript = [{"role": "user",
               "content": f"CLAUSE {clause.get('id')}\n{clause.get('quote','')}"}]
```

The call it is repairing used `build_user()`: the template plus **the full text of every
cross-referenced clause**.

Measured for `m0091`:

```
attempt-1 USER block : 5,324 chars, 8 cross-referenced clauses
repair turn-1 USER   :   491 chars
  contains "CROSS-REFERENCED"          : False
  contains "Write the module for clause": False
  identical to what was actually sent  : False
```

Three consequences: the repair attempt is asked to fix a translation **without the definitions it
was given** (`config.json` justifies cross-references with *"a clause that modifies rules defined
elsewhere cannot be translated in isolation"*); the stored transcript is a **fiction** — the
assistant turn is presented as a reply to a prompt that was never issued, and it is the artifact a
reviewer reads; and the cache claim in `test_repair.py`'s docstring (*"the message prefix is
byte-identical as it grows"*) holds only *within* the repair sequence — attempt 2's prefix diverges
from attempt 1's right after the system block, so the 8 cross-referenced clauses are paid for again
at full price on… nothing, since they are simply dropped.

`test_the_clause_is_in_the_transcript_exactly_once` currently **locks this in**.

I attacked the prefix invariant itself and could **not** break it: within the loop the transcript
is only ever appended to, `_body_messages` copies the dicts, and the mutation "drop the assistant
turns" is killed by two tests.

---

## F6 `abstained_under_repair` is computed carefully and then thrown away by `run()`

Same overwrite as F1 (`status=obj.outcome`, line 1108). `repair_loop` distinguishes
`"abstained"` from `"abstained_under_repair"` — and `checks.py` devotes a long docstring to why
(*"how a model abstains its way out of the hard clauses"*), with a tri-state `first_attempt`
property built for it.

**Concrete case.** Attempt 1 = `BROKEN`; attempt 2 = a well-formed abstention:

```
  ∅ m0091: abstained — it is a heading
run.json: status="abstained"   attempts=2   flags=['shrank']
summary:  0 translated, 1 abstained, 0 failed
```

`status` is the field any aggregate will group on; the distinction survives only as `attempts=2`,
which is also what a *successful* repair reports. `checks.CheckResult.first_attempt` is currently
dead — nothing reads it.

---

## F7 The `clingo` guard's return-code half is unpinned, and it is the half that catches "clingo never ran"

`link.py:714` — `if errs or r.returncode not in CLINGO_OK_RC:`.

Mutating this to `if errs:` **survives all 187 tests and `link.py --self-test`**. It is the only
survivor of a 7-mutation pass over `link.py`'s checks (the other six — compile-error text,
rule-shape, beats-cycle, closure, unresolved-reference, requires-unprovided — are all killed by
2–4 tests each; `link.py` is otherwise well pinned).

That it matters is not hypothetical. With `clingo` absent from the venv:

```python
link.PY = '/usr/bin/python3'
link._check_clingo(['m0255.lp'])
# blob: "…/python3: No module named clingo"
# CLINGO_ERR.findall(blob)  ->  []          <-- the text half sees nothing
# finding raised only because returncode == 1
```

So under the mutant, a link check over a program that was **never compiled** returns clean, and
every test stays green — the exact "pass indistinguishable from did not run" shape `_check_clingo`'s
own docstring was written to prevent. The redundancy is right; nothing asserts it.

---

## F8 `run()`'s identity guards are enforced at a call site nothing tests

`translate.py:1051` passes `clause_id=cid, known_clause_ids=known_ids` into `parse_module`. The
docstring says these are what enforce *"the module did not rename itself"* and *"it did not cite a
clause that does not exist"*, and *"a run that omits them loses both guarantees with no visible
difference in its output."* That is exactly right — and unfenced.

Deleting both kwargs at the call site leaves **187 pytest tests and all 53 self-test checks
green**. Side by side, same stub returning a module whose `clause_id` is `m0037` while `m0091` was
requested:

```
ORIGINAL : ⛔ m0091: module says clause_id 'm0037' but it was asked to translate 'm0091'.
                    The artifact would carry two identities   (raw kept)
MUTANT   : ✓ m0091: 1 asserts, …
           m0091.json says clause_id = m0037
```

The self-test checks `parse_module`'s *behaviour* when given the arguments; nothing checks that
`run()` gives them. Same for `checks.run_checks`'s `corpus_ids` in the repair path (that one is
passed correctly today, also untested).

---

## F9 `translate.py --self-test` is not run by pytest, so "209 passed" does not cover 53 of the checks

`test_link.py:745` runs `link.py --self-test` in a subprocess. Nothing does the equivalent for
`translate.py`. The only place both self-tests run is `setup_env.sh`, which is not a test gate.

This is why the mutation table below splits: `--limit 0` and the truncation guard survive pytest
and are caught only by the self-test. If someone regresses a self-test-only guard, `pytest
walkthrough/ -q` stays green.

Full result of the 17-mutation pass over `checks.py` + `translate.py` (all `checks.py` mutants
died — 6/6; that file is well covered):

| mutation | pytest | self-test |
|---|---|---|
| cost estimate triangular → linear | **survives** | **survives** |
| `run()` drops `clause_id` / `known_clause_ids` (F8) | **survives** | **survives** |
| `cross_references.max_clauses_per_target` ignored | **survives** | **survives** |
| `if not out: raise CorpusError("selection matched no clauses")` removed | **survives** | **survives** |
| `--limit 0` means "no limit" again | survives | killed |
| truncation guard removed | survives | killed |
| repair log stops filtering by `origin` | killed | — |
| `_diff_flags` / `_unclear_rate` neutered | killed | — |
| assistant turns dropped from the transcript | killed | — |
| `run()` never calls `repair_loop` | killed | — |

Notes on two of the survivors:

* **`growth = turns*(turns+1)/2` → `turns`.**
  `test_the_cost_gate_PRICES_the_repair_attempts` asserts `three > one * 2.5`. With
  `max_tokens=1000` and the strings `"sys"` / `"user"`, the **output** term alone gives exactly
  3×, so the assertion is satisfied without the input term contributing anything measurable. The
  test named for the triangular estimate cannot see the triangular estimate — a
  passes-for-the-wrong-reason of the kind this suite's `check()` helper exists to catch, one file
  over.
* **`max_clauses_per_target`** is a config key that changes what is sent and what is billed, and
  nothing observes it.

---

## F10 `README.md` is factually wrong about the code in six places

| line | says | actually |
|---|---|---|
| 13 | `--self-test  # 16 checks` | 53 |
| 24-27 | "⛔ It validates nothing… no compile, no link check… Stage 2 is those checks and it is **deliberately not built yet**" | `checks.py` exists and runs `link.collect` + `schema.validate_all` — on the repair path only (F3) |
| 78-80 | "This harness implements the initial-answer path only — **no repair loop, no checks**" | both exist |
| 76 | "Ledger: **$2.06** of $8.50" | brief says ~$2.07; unverified either way |
| ~95 | "output part 3 — a licence and a citation on EVERY fact ⛔ **absent**" | `Licensed` is a base class; `licence`/`cites`/`inference`/`toggleable` are enforced, and six self-test checks pin them |
| ~97 | "format-forced … ⛔ **it is instruction-following plus a regex**" | `model.format_forcing: "json_schema"` and `schema.response_format()` are sent in the body |
| 143 | "`status` is one of `translated · abstained · no_code_block · error`" | the statuses written are `translated`, `abstained`, `invalid_module`, `unrepaired`, `error`. `no_code_block` no longer exists |
| 130-140 | run-directory listing | omits `prompt_system.txt`, `<id>.prompt_user.txt`, `concepts.json`, `<id>.transcript.json` |

Same class inside the code: `translate.py`'s module docstring still opens *"⛔ IT VALIDATES
NOTHING ABOUT THE TRANSLATION… does not link it"*, and `run()` prints
`"⛔ NOTHING here has been validated. No compile, no link, no read-back."` on **every** run,
including runs where the repair path did compile and link the module. `STEP_stage2_and_repair.md`
still says "`checks.py` and the repair loop are **NOT built**" (defensible — it is a design doc
under review — but it is also the only written record of the design, and §5's "fresh conversation
= a new `messages` list per attempt, **no assistant turns carried**" is now contradicted by the
implementation; the departure is argued in `test_repair.py`'s docstring but not in the design
record, which `AGENTS.md` would call a transcript-only ruling).

---

## Lesser items

* **`repair_loop`'s default `max_attempts=3` vs `run()`'s fallback of 1** (line 937,
  `cfg.get("repair") or {}` → `.get("max_attempts", 1)`) vs the design's stated default of 3. A
  config missing the `repair` block silently disables both repair *and* — via F3 — all of stage 2.
* **`run()` never passes a corpus-wide concept table.** `repair_loop` calls `run_checks` with
  `concepts=None`, so `_link_findings` falls back to *the module's own rows*. The cross-clause
  check `concept-multi-gloss` is therefore computed against a single module and is structurally
  incapable of firing in a live run, even though `run()` accumulates `_concepts` for exactly that
  data. (Documented as deferred in `DEFERRED.md` D-3; recording that the live wiring makes it
  inert, not merely incomplete.)
* **`resolve_provider` does `sys.path.insert(0, os.path.dirname(pj))`** (line 447), permanently
  prepending `semi-formal-experiment/` *ahead of* `phase_1/` for the rest of the process — and
  `semi-formal-experiment/translate.py` exists. Nothing imports `translate` after that today
  (in script mode phase_1's own file is `__main__`), and `repair_loop`'s deferred
  `import checks` is safe because the repo has `checker.py`, not `checks.py`. Latent, one filename
  away from a very confusing bug.
* **`self_test`'s `_StubClient` has no `complete_messages`.** The self-test's end-to-end run
  therefore cannot exercise the repair path at all; if its stub ever returned a repairable
  failure the self-test would die with `AttributeError`, not a named refusal.
* **`rec["flags"]` / `rec["per_attempt"]` exist only on the repair path**, so a `run.json`
  aggregate must treat "absent" and "none" as the same thing.
* **The `if not out: raise CorpusError(f"selection matched no clauses (kinds={s.get('kinds')})")`
  message misdiagnoses** the section+kind case, which is the only way to reach it after the
  section branch has already raised: it blames `kinds` when the cause is the intersection.
  Untested (survives both suites).
* **`model/guard.py` is currently RED** — `schema.py` and all four `prompt/*.md` have **no review
  point at all** (`⛔ NEVER REVIEWED — 5 watched file(s)`, exit 1) while today's work proceeded on
  top of them. The hook is installed (`.git/hooks/pre-commit` → `model/hooks/pre-commit`), so a
  commit touching them will block; flagging it because the guard's own docstring records that
  being red and unread for two hours is the failure it exists to prevent.

---

## What I attacked and could not break

* **`checks.py`** — 6/6 mutations killed (severity ruling, abstention terminality, link-finding
  pass-through, the `concepts=None` default, `Finding.origin`, `Finding.severity`). The
  `origin` filter in `render_error_log` is killed too. The stage-3 leak defence is solid.
* **`link.py`** — 6/7 mutations killed by 2–4 tests each (F7 is the single survivor).
* **`mutate_schema.py`** — I tried to make it lie by pointing it at `link.py`. It refused
  (`‼ REQUIRED guards did not resolve to exactly one raise site … Refusing to run: a short run
  reports fewer holes than exist`) rather than reporting "no survivors". Its own run on
  `schema.py` is honest: 45 guards, 0 survivors, 63 of 64 narrow mutations killed 1:1.
* **The repair transcript's growth invariant** — append-only, dicts copied at the boundary,
  system block byte-identical across calls. Only its *first turn* is wrong (F5).
* **Abstention terminates** — confirmed at attempt 1 (`len(model.calls) == 0`) and end-to-end
  through `run()`.
* **The cost gate itself** — no path reaches `client.complete*` without `cost_gate(est, cfg)`
  having run; `--write-artifact` and `--list-models` send nothing billable; every call routes
  through `_send` → `_log_usage`, including repair calls, so usage is recorded. The defect is the
  *estimate* (F4), not the gate.
* **The `__main__`-guard regression** — `test_nothing_is_defined_below_the_main_guard` is a real
  pin; the mutation "move a def below the guard" is a source-text assertion that would catch it.
  Nothing below line 2168 but the guard.

---

## Suggested order

F1, F2, F3 are one afternoon and they are the ones that will produce a wrong artifact on the next
live run. F1 and F6 are the same two-line overwrite. F5 changes what the model sees, so it should
land before any measurement of repair effectiveness — a repair rate measured today is a repair
rate *without cross-references*. F4 is cheap: add `(k-1) * max_tokens` to the input term.
