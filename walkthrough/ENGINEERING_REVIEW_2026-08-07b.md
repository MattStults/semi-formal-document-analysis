# Engineering review — stage 3 / stage 4, 2026-08-07 (second pass)

Clean-context adversarial review of `f775bc2`, `491cadb`, `3759e55`, `0d930b4`
(plus `710f60f`, `472d225` in range). **REVIEW ONLY — no code, test or document
outside this file was changed.** Every mutation made to verify a guard was
restored and the restore confirmed with `git status`.

Baseline observed: `pytest walkthrough/ -q` → **468 passed**.
Environment: `semi-formal-experiment/.venv/bin/python`, clingo 5.8.0 present.

**Verdict: not clean.** Twelve findings, two of them high severity. F1 is a
totality violation of the exact kind stage 4 exists to prevent — content
silently dropped with all five RB checks green. F2 is a brand-new test that
passes when the thing it tests never ran, written in the same commit that fixed
that shape in `link.py`.

---

## CONFIRMED findings, by severity

### F1 · HIGH — `_parse_body` silently discards everything after the first statement; a body can lose half its conditions with RB1–RB5 all green

`readback.py:152-168` (`_parse_body`), reachable from `render_body`,
`render_items` and `count_not`.

`schema._check_body` (`schema.py:132-160`) rejects only a **trailing** full stop.
An interior one validates:

```
$ semi-formal-experiment/.venv/bin/python -c "import sys; \
  sys.path.insert(0,'walkthrough/paper_pipeline/phase_1'); import schema; \
  schema._check_body('adult(P). N > 5, N != 9','T'); print('ACCEPTED')"
ACCEPTED
```

`_parse_body` wraps the body as `h_readback_head :- {body}.`, so clingo parses
**two statements**, and the loop `for st in stmts: if st.ast_type == Rule:
return list(st.body)` returns the **first** one and drops the rest. Reproduction:

```
ontology[0]  body   = 'adult(P). N > 5, N != 9'
ontology[0]  render = '«the request may proceed» holds of «P», «N» when
                       «the person is over eighteen»'
outcome  = rendered
checks   = {'RB1': True, 'RB2': True, 'RB3': True, 'RB4': None, 'RB5': True}
findings = []
```

Two conditions of the rule are gone from the sentence the four seats read, and
nothing fires. The backstops do not reach it:

* **RB2** scans `_PRED_IN_BODY` (`name(`) only, so a dropped *comparison* or
  arithmetic conjunct is invisible to it. (A dropped *predicate* conjunct is
  caught, by RB2 or by `readback-ungloss` — that is why this is not caught more
  often.)
* **RB3** calls `count_not`, which uses the same broken `_parse_body`, so `want`
  and `got` are computed from the same truncated parse and always agree.

This is not "no template" degrading to layer 1 — the module docstring's ⛔
promise. It is content deleted with a layer-2 "fluent" stamp on it. Under
`DEBUGGING_TIPS.md` §3-adjacent reasoning it is also the exact shape §2's
"silent under-rendering: 4b would pass the weaker sentence" note names.

**Fix direction:** `_parse_body` should count the statements it got and fall
back to layer 1 (or raise) on more than one; `_check_body` should reject any `.`
outside a quoted string, not just a trailing one. Do both — either alone leaves
the other reachable.

Confidence: high (ran it).

---

### F2 · HIGH — the positive control that justifies withdrawing the anonymous-variable restriction passes when clingo never ran

`test_schema.py:172-193`,
`test_an_anonymous_variable_in_a_BODY_is_accepted_and_clingo_loads_it`.

Its own docstring: *"A restriction is only withdrawn honestly if something proves
the newly permitted case works end to end… So this renders the module and runs
clingo over it."* It does not verify clingo ran:

```python
r = subprocess.run([str(VENV_PY), "-m", "clingo", str(lp), "--outf=3"], ...)
errs = [ln for ln in (r.stdout + r.stderr).splitlines() if "error" in ln.lower()]
assert not errs
```

`r.returncode` is never read, and a missing module prints a message containing no
`error`:

```
$ /usr/bin/python3 -m clingo --version 2>&1
/Library/Developer/CommandLineTools/usr/bin/python3: No module named clingo
$ ... | grep -ci error
0
```

Demonstrated by pointing `test_schema.VENV_PY` at a clingo-less interpreter and
calling the test function directly:

```
test_an_anonymous_variable_in_a_BODY_...: PASSED with an interpreter that HAS NO CLINGO
```

`CLAUDE.md` names a clingo-less venv as a **supported** state ("those tests will
show as collection errors, which is a known environment gap"). They will not —
there is no `importorskip`; this one goes green. And this test is the *entire*
positive evidence for removing the `_check_body` guard in `3759e55`.

The irony is load-bearing: `f775bc2` fixed precisely this shape in
`link._check_clingo` and `test_link.py:341-354` writes a whole essay about "a
pass indistinguishable from a did-not-run". The same commit series then
reproduced it in `test_schema.py`.

**Fix direction:** assert `r.returncode == 0` (clingo returns 10/20/30 for
SAT/UNSAT — mirror `link.CLINGO_OK_RC`), or `pytest.importorskip("clingo")` at
module scope, and assert the solver produced output.

Note: the pre-existing `test_the_worked_examples_compile_in_clingo`
(`test_schema.py:115-132`) has the identical defect. Out of today's scope, same
one-line fix.

Confidence: high (ran it).

---

### F3 · MEDIUM-HIGH — `translate.py --self-test` is RED and pytest is green; the pytest wrapper is designed not to see it

```
$ cd walkthrough/paper_pipeline/phase_1 && ../../../semi-formal-experiment/.venv/bin/python translate.py --self-test
  ❌ dryrun.txt matches the current config and prompts (inputs-sha fdef1ecdebb0728c)
       dryrun.txt is missing or STALE (current inputs-sha fdef1ecdebb0728c)
51 passed, 1 failed
EXIT=1
```

The prompt files last changed at `6be3a4a` — the base of today's scope — and
`dryrun.txt` was not regenerated, so the self-test has been red for the whole of
today's work. `pytest walkthrough/` stayed at 468 passed throughout.

`test_prompt_examples.py:193-215` is the wrapper and asserts only that no
`Traceback` appears and that a `\d+ passed` line exists. Its stated reason —
*"Pinning '53 passed' would fail the moment someone legitimately adds a check
(DEBUGGING_TIPS entry 9)"* — is a **false dichotomy**. `assert r.returncode == 0`
or `assert "failed" not in summary` pins no count and violates no anti-pinning
rule. As written, the wrapper closes the "self-test crashed" hole and leaves the
"self-test failed" hole wide open, in the file whose docstring says *"a check
that cannot run must not be reachable from the same state as a check that
passed."*

Partially disclosed — `OPEN_QUESTIONS.md` Q-4 records this and correctly refuses
to regenerate the artifact. Two problems remain:

* Q-4 says *"52 passed / 1 failed"*; it is **51**.
* `REVIEW_QUEUE.md:175`, in a section headed **"WHAT IS BUILT AND GREEN"**, still
  claims `translate.py --self-test 53/53`, `270 tests`, and `mutate_schema.py 45
  guards, 0 survivors`. Measured today: **51 passed / 1 FAILED**, **468 tests**,
  **44 guards**. `REVIEW_QUEUE.md` was edited in today's range (162 lines) and
  this block was not touched. A status section asserting green for a red check is
  worse than no status section.

Confidence: high (ran it).

---

### F4 · MEDIUM — gloss substitution rewrites the inside of quoted string constants

`readback.py:110-124` (`substitute`), regex `_NAME` at `:101`. No string
awareness anywhere. Note that `schema._strip_strings` — the *only* string-aware
helper in the pipeline — was **deleted** in `3759e55` along with the guard that
used it.

```
render_body('p("political_content is bad")', {...})
  -> '«a thing» (of "«content about politics» is bad")'
```

A data constant is rewritten into prose. Worse for the checks: a declared label
occurring inside a string is glossed away, so RB1 can no longer see it — the one
check whose entire job is to notice a surviving label.

Confidence: high (ran it). Impact depends on whether string constants appear in
the corpus; the schema permits them, so this is reachable.

---

### F5 · MEDIUM — a `«` or `»` inside a gloss breaks `_strip`, and makes RB3 fire on a correct rendering

`readback.py:557-568` (`_strip`) is a flat, non-nesting scanner.
`schema._BAD_IN_TEXT = re.compile(r'[\n\r"\\{}]')` does **not** forbid the
substitution markers in a gloss, so a model can emit one.

```
_strip('«a «flag» that has not been set»', '«', '»')  ->  '» that has not been set'
```

The residue leaks into every consumer of `_strip`. Concrete misfire:

```
concept gloss = 'text with a «flag» the user has not seen'
ontology body = 'unread(X)'          # zero `not`
RB3: False
  'ontology[0]: body has 0 `not`, rendering shows 1 negation marker(s)'
```

`_markers` (`:644-655`) exists specifically to prevent this — its docstring is
*"A gloss reading 'text the user has not read carefully' is prose about the
world, not polarity"* — and it fails on the one input that defeats its stripper.
The same residue corrupts RB1's inside-gloss / outside-gloss classification
(`:610`) and `echo_score` (`:684`).

**Fix direction:** add `«»` (and `⟦⟧⟨⟩`) to `_BAD_IN_TEXT`, or escape on
insertion. A tolerant `_strip` is the weaker fix — the markers must stay
unambiguous for RB1 to mean anything.

Confidence: high (ran it).

---

### F6 · MEDIUM — `_CONVERSE`'s strict-inequality entries and `_CMP[Equal]` are unpinned; an aggregate bound can invert silently

`readback.py:78-93`. The comment there says it outright: *"getting this backwards
inverts every aggregate bound silently."* Mutants run against the full suite:

| mutant | result |
|---|---|
| `_CONVERSE[LessThan] -> LessThan` (drop the swap) | **SURVIVED 468** |
| `_CONVERSE[Equal] -> NotEqual` | **SURVIVED 468** |
| `_CMP[Equal] = "different from"` | **SURVIVED 468** |
| `_CONVERSE[LessEqual] -> LessEqual` | killed (`test_count_aggregate_renders_as_a_number_phrase`) |
| drop `_CONVERSE` lookup entirely | killed (same test) |

The `LessEqual` entry is covered only *incidentally*: clingo normalises
`#count{...} >= 3` into a **left** guard `3 <= #count{...}`, so the one aggregate
test happens to exercise it. Nothing exercises `<` / `>`. Under the surviving
mutant:

```
'3 < #count{ X : harmed(X) }'
  correct : 'the number of X such that «a person is harmed» is greater than 3'
  MUTANT  : 'the number of X such that «a person is harmed» is less than 3'
```

**Fix direction:** one parametrised test over all six operators in both guard
positions. Six asserts closes the whole table.

Confidence: high (ran it).

---

### F7 · MEDIUM — `_layer`'s `min` is unpinned; a mixed-layer item could be stamped fully fluent

`readback.py:532`. `min([s.layer ...]) -> max(...)` **SURVIVED 468**.

The behaviour is currently correct — a body of `adult(P), 2 { q(P) } 4` yields
spans `[2, 1]` and the `Rendering` is stamped `layer 1 · asp-with-glosses`. But
no test builds an item whose body mixes the two layers, so the module's own ⭐
property — *"Every rendering records WHICH LAYER produced it… because the two
carry different amounts of trust"* — is unpinned exactly where it matters. Under
`max`, an item containing glossed raw ASP is presented to a seat as fluent
English.

Confidence: high (ran it).

---

### F8 · MEDIUM — `KEYWORDS` makes layer 1 and layer 2 disagree, and guarantees a false RB1 failure for a predicate named `count`/`sum`/`min`/`max`/`true`/`false`

`readback.py:76`. `substitute` consults `KEYWORDS`; `_gloss_slot` (`:216-230`)
does not.

```
substitute('count(X), 3 < Y', {'count': 'the tally'})  ->  'count(X), 3 < Y'
render_body('count(X)',       {'count': 'the tally'})  ->  '«the tally»'
```

Consequences for a module that legitimately declares `count/1` as a concept:
layer-1 spans keep the bare name, RB1 fires on every one of them, and the message
says *"in the renderer's own text — no definition was available to put there"*,
which is **false** (a definition exists; `substitute` refused to use it). RB1's
inside/outside distinction was added precisely so its output would be readable.

The entries are also mostly unnecessary: `_NAME`'s lookbehind is
`(?<![A-Za-z0-9_#])`, so `#count`, `#sum`, `#min`, `#max`, `#true`, `#false` are
already excluded by the `#`. Only bare `not` is load-bearing.

`test_substitute_leaves_keywords_alone` (`test_readback.py:119-123`) pins the
defect rather than the property — it passes a gloss for `count` and asserts it is
*not* used.

Confidence: high (ran it).

---

### F9 · LOW-MEDIUM — `render_items` puts raw ontology arguments inside gloss markers, which also mis-classifies RB1

`readback.py:494` and `:498`.

```
ontology atom 'restricted(new_step)'  ->  '«new_step» is «it falls under…»'
ontology atom 'ok(P,N)'               ->  '«…» holds of «P», «N»'
```

A variable name and a bare constant are dressed in the typography reserved for a
written definition. Because RB1 builds its `outside` scan by stripping `«…»`
(`:610`), a declared label appearing as an ontology argument is reported as:

```
'the label 'known' survives …, inside a gloss — the written definition reuses
 its own predicate's name'
```

when in fact the renderer emitted the bare label itself. That is the *weaker* of
RB1's two diagnoses and, per the comment at `:605-609`, the one a reader is told
to discount. The classification is inverted for this case.

Confidence: high (ran it).

---

### F10 · LOW — `_rb1` mutates its scan by iterating a `set` and doing prefix-blind replacement

`readback.py:601-602`:

```python
for cid in ids:                       # ids is a set
    scan = scan.replace(f"clause {cid}", "clause")
```

`ids` is a `set` of `str`, so iteration order varies with `PYTHONHASHSEED`. If
one clause id is ever a prefix of another (`m001` / `m0012`), replacing the
shorter first corrupts the longer and the finding set becomes hash-order
dependent. Not reachable on today's fixed-width four-digit ids, so this is latent
— but `REPRODUCIBILITY.md` requires determinism and
`test_rendering_is_deterministic` runs both renders in one process, where the
hash seed is constant, so it cannot see this class of defect at all.

**Fix direction:** `for cid in sorted(ids, key=len, reverse=True)`, or use a
regex alternation with word boundaries.

Confidence: medium-high (reasoned from the source; the prefix condition is not
reachable in the current corpus).

---

### F11 · LOW — the cost fix is genuinely conservative, but the repair-turn user blocks are unpriced and the slack covering them is unmeasured

`translate.py:780-812`. I re-derived the worst case independently:

```
attempt k input = system + user + Σ_{i<k}(completion_i + errorlog_i)
true worst  = T·(sys+user) + max_tokens·T(T-1)/2 + Σ errorlog resends
estimate    = T(T+1)/2·(sys+user) + max_tokens·T(T-1)/2
```

The completion term is now correct. The error-log turns are missing from **both**
the estimate and `_hand_priced_worst_case` in the test, so the test cannot see
that dimension. In practice the deliberate over-charge on the `(sys+user)` term
— `T(T-1)/2` surplus copies, ≈29k tokens at the shipped `max_attempts: 3` with a
33.5k-char system block — dominates any plausible error log by two orders of
magnitude, so the estimate **is** ≥ the true worst case for `max_attempts` 1..5.
This is a documentation/robustness gap, not a live under-estimate.

Two smaller notes on the same test:

* `system = "s" * 33614  # the real stage-1 system block` (`:87`) has already
  drifted — the self-test reports the real block at **33,506** chars. Harmless as
  a magnitude fixture; the comment is now false.
* `test_the_completion_carried_forward_is_priced_as_INPUT` and
  `test_one_attempt_bills_no_carried_completion` are a real killer pair — I
  checked that the guard actually rejects "just inflate the estimate". Sound.

Confidence: high on the arithmetic (re-derived and re-ran); the error-log
dominance is an estimate, not a proof.

---

### F12 · LOW (process) — concurrency damage, live during this review

* `walkthrough/paper_pipeline/phase_1/test_seats.py` (44 KB) appeared **untracked**
  mid-review with no `seats.py` beside it. `pytest walkthrough/` goes from
  *468 passed* to `ImportError: No module named 'seats'` → `Interrupted: 1 error
  during collection` — **zero tests run**. It exits non-zero, so it does block
  (correct behaviour), but any measurement taken in that window is void: two of
  my own mutant verdicts were silently corrupted by it and had to be re-run with
  `--ignore`. Anyone reading a test count from today's transcripts should check
  which side of this window it came from.
* `semi-formal-experiment/usage.jsonl` grew by 49 rows during the review.
  `spend.py` reports `!! 311 logged calls had no price entry` and
  `!! UNLOGGED SPEND — openai/gpt-oss-20b: 6 artifact(s)` against the hard $8.50
  cap (total shown: $2.057). Unpriced calls in a ledger whose purpose is a hard
  cap are the same defect class as F11, one layer down.

Confidence: high (observed).

---

## What I checked and found SOUND

Listed so the coverage of this review is auditable.

**Layer-1 totality.** Hand-built attack set, all through `render_body` and again
through `render_module`: 500 conjuncts; 200- and 2000-deep nested function terms;
theory atoms (`&diff{X-Y} <= 3`); `#external`; `#minimize`; classical negation
(`-p(X)`); pooling (`q(X;Y)`); intervals (`p(1..5)`); choice aggregates; nested
aggregate assignment (`X = #sum{...}`); conditional-literal lists; `#false`;
unparseable text (`p(X) )( q(`); empty and whitespace-only bodies; unicode
constants; a body carrying the `«»` markers. **Nothing raised and nothing was
refused.** The only totality defect found is F1, which is a *drop*, not a
refusal. The design claim survives contact.

`test_layer1_is_total_over_every_real_lp_rule_body` is **not vacuous** — it
asserts `bodies` is non-empty first, and `rule_bodies`' textual fallback for
files clingo refuses is a real anti-vacuity measure.

**Mutation sweep, re-run by hand — 15 mutants against `readback.py`.**
Killed (each by exactly one targeted test, which is the good signature):

| mutant | died to |
|---|---|
| drop the `NEG_MARK` loop in `_render_element` | polarity/RB3 tests |
| `substitute` never glosses | substitution tests |
| `checks["RB5"] = True` | `test_rb5_empty_rendered_set_is_an_outcome_not_a_pass` |
| RB2 never fires | `test_rb2_fires_when_the_renderer_drops_a_condition` |
| `_fallback` claims layer 2 | `test_a_construct_with_no_template_falls_back_and_says_so` |
| `_gloss_slot` returns the bare name | ungloss-marker tests |
| `_rb1` `in_gloss = True` | `test_rb1_says_whether_the_label_is_in_the_gloss…` |
| `count_not` returns 0 | RB3 tests |
| `echo_score` returns 0.0 | RB4 tests |
| `_rb1` skips the act-mark strip | `test_rb1_exempts_only_the_marked_act_term` |
| drop `_CONVERSE` lookup | `test_count_aggregate_renders_as_a_number_phrase` |
| `_CONVERSE[LessEqual]` neutered | same |

Survivors are F6 (×3) and F7. **12 of 15 killed** — this is a genuinely strong
pin set, not a decorative sweep. I could not find a way to make the RB1/RB2/RB3
machinery pass vacuously.

**`mutate_schema.py`, re-run:** `44 killed · 0 SURVIVORS · 0 errors (of 44
guards)`, with its own entanglement report (`64 of 65 tests killed by a narrow
mutation are killed by exactly one`). Real. Note **44**, not the 45 claimed in
`REVIEW_QUEUE.md` — consistent with the withdrawn `_check_body` guard, i.e. the
count moved for a legitimate reason and the doc did not (see F3).

**`link.py --self-test`: 19/19.** The new `test_link.py` return-code tests
(`:355-419`) are the best work in this range. `_fake_interpreter` correctly
refuses to be a claim about the host machine; the premise assertion
(`link.CLINGO_ERR.findall(blob) == []`) makes the test self-invalidating if the
text arm ever starts matching; and
`test_d4_every_documented_clingo_exit_code_stays_silent` is a real paired guard
that kills `if True:`. This is the pattern F2 should have copied.

**The `abstained_under_repair` fix.** `run()`'s new partition counts
`translated` by name and prints a named residual for any unpartitioned status.
The tests assert on the **printed line** via `capsys` and carry a positive
control (`test_the_PRINTED_SUMMARY_still_counts_a_real_translation`) that kills
`0 translated` passing everything. Correct, and correctly reasoned in
`DEBUGGING_TIPS.md` §2.

**The schema regrounding.** I confirmed the new ground independently:
`clingo <<< 'q(a). p(_) :- q(X).'` → `error: unsafe variables in:
p(#Anon0):-…;q(X)`, and `p(X) :- q(X,_). q(a,b).` derives `p(a)`. The rejection
in `_check_term` and the withdrawal in `_check_body` are both correct on the
merits. The problem is only F2 — the evidence for the withdrawal is not fenced.

**Anti-rules.** Read `MODULE_MAP.md` §11. None of the twelve findings above
touches any of the six contracts (all six are in `semi-formal-experiment/`; all
findings here are in `walkthrough/`).

**Pinned live values.** Swept the new tests for hard-coded counts and sizes. The
only ones are `len(...) == 1` on a locally-constructed finding list (legitimate)
and the two character-count fixtures in `test_cost_and_summary.py` (F11, cosmetic
— they are magnitudes, not reads of a live artifact). `test_readback.py`'s
real-corpus tests are written as properties with clean skips, as its header
claims. No new instance of DEBUGGING_TIPS §9 found.

---

## Restore verification

```
$ git status --short
 M semi-formal-experiment/usage.jsonl        # not mine — grew during the review, F12
?? walkthrough/paper_pipeline/phase_1/test_seats.py   # not mine — F12
```

`readback.py`, `test_readback.py`, `schema.py`, `test_schema.py`, `translate.py`
and `test_link.py` are all identical to `HEAD`. No API call was made; no money
was spent; `guard.py --accept` was not run; nothing was pushed.
