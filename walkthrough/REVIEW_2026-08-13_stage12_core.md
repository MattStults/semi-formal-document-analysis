# REVIEW — stage-1/stage-2 core (`translate.py`, `schema.py`, `checks.py`, `link.py`) — 2026-08-13

**VERDICT: the core is unusually disciplined — honest tests, negative controls, silent-paths
closed one by one — but it admits a whole class of contentless modules as `translated`
(Attack D, now generalized), its repair-gaming guards are telemetry-only AND have concrete
holes, one committed test in scope is RED, and `link.py` misreads the headers of the repo's
own flagship worked example. Four HIGH/MEDIUM findings are RUN-verified below.**

## Baseline

```
$ cd semi-formal-document-analysis
$ semi-formal-experiment/.venv/bin/python -m pytest walkthrough/test_link.py \
    walkthrough/paper_pipeline/phase_1/ -q -k "not seats and not readback and not mutate"

1 failed, 624 passed, 356 deselected, 1 xfailed in 118.40s
FAILED walkthrough/test_link.py::test_d4b_no_table_and_no_concepts_declared_is_silent
```

The single failure is in scope and is finding §A3. The single xfail is the tracked Q-4
stale-`dryrun.txt` (see prior-findings section). `translate.py --self-test`: **51 passed,
1 failed** — the same tracked dryrun staleness, nothing new. `link.py --self-test` passes
(green via `test_self_test_still_passes` in the baseline).

All repros below ran offline (pytest, `--self-test`, clingo on scratch files, stub models —
zero provider calls). Scratchpad: `/tmp/review_stage12.uUh7rI/`. Every finding is marked
**[RUN]** or **[INFERRED]**.

---

## Findings

### §A1 — HIGH — a whole class of contentless modules validates as `translated` (Attack D, generalized) [RUN]

`schema.py:789-793`, `checks.py:run_checks`, `schema.py:render_lp`.

The "did you translate anything" guard is:

```python
if not (self.asserts or self.defines or self.ontology or self.beats
        or self.concepts):
    errs.append("translated but emitted no assertion, ...")
```

`concepts` is in the disjunction, but concepts **assert nothing by design** and never enter
the `.lp` (only a pointer header; glosses go to the concept table). So the guard is
satisfied by a module that says nothing. Repro (offline, real `schema.py` + `checks.py`):

| shape | `validate_all` | `run_checks` outcome | findings | non-comment `.lp` lines |
|---|---|---|---|---|
| A1 concepts-only (Attack D exactly) | built, 0 breaches | `translated` | 0 | **0** |
| A2 concepts + `acts` + `closure`, no rules | built, 0 breaches | `translated` | 0 | **0** |
| A3 `forbid_body` + concepts only | built, 0 breaches | `translated` | 0 | **0** |
| A5 one `inputs` entry + its mandatory gloss | built, 0 breaches | `translated` | 0 | **0** |
| A4 everything empty (control) | refused | — | "abstention that did not say so" | — |

A2 is worse than the documented attack: the module *governs* `produce` and *declares a
closure over it* — it reads as having settled what silence means — while rendering zero
rules. A3 carries a `%% forbid-body:` declaration that nothing can ever violate.

**The hole generalizes further.** Since the 2026-08-12 ruling every `requires`/`inputs`
borrow must carry a gloss as a `concepts` entry (`schema.py:882` ff.). So **any module
with a non-reserved borrow automatically satisfies the content guard** (A5): declarations
about the interface alone are enough to be "translated". A corpus built this way can count
clauses as done whose `.lp` is comments.

Why it matters: `run()` writes such modules to `runs/` with `status: "translated"`,
extends the concept table, and counts them in the success line. Downstream stages inherit
hollow nodes; the "translated N of 593" number overstates content. This is exactly the
shape REVIEW_QUEUE §8.3 recorded for `m0037`, still open. Confidence: high.

### §A2 — HIGH — the typed repair-gaming guards are non-binding and have three concrete holes [RUN]

`translate.py:2426-2441` (`DECLARATION_FIELDS`/`_diff_flags`), `translate.py:2515-2518`
(flag collection), `translate.py:1336-1342` (`run()` writes flagged modules anyway),
`graveyard.py:108-114`.

The guards (`shrank`, `declaration-edit`) are **telemetry only**: a flagged module still
exits `repair_loop` as `status="translated"` and `run()` writes `{cid}.json`/`{cid}.lp`
into the corpus; `test_repair.py::test_a_repair_that_moves_a_predicate_from_requires_to_
inputs_is_FLAGGED` itself asserts `out.status == "translated"`. The cost has already been
paid once: `graveyard.py`'s docstring records *"One clause converged, was flagged `shrank`,
and was garbage: it cleared its finding by deleting the offending entry and the run
recorded it as a success."*

Worse, even the telemetry has holes. Repro with a stub model (no provider calls),
attempt 1 → scripted attempt 2, real `repair_loop` + real `checks.run_checks`:

| scenario | result |
|---|---|
| S1 m0037 shape: finding cleared by deleting the ontology entry + dependent assert | `status=translated attempts=2 flags=['shrank']` — flagged but accepted |
| S2 finding cleared by deleting the defective `concepts` entry | `status=translated attempts=2 flags=[]` — **invisible** |
| S3c genuine fix **plus** silent deletion of `requires`+gloss, masked by adding one filler ontology fact | `status=translated attempts=2 flags=[]` — **invisible** |
| `_diff_flags({}, anything)` (unparseable attempt 1) | `[]` — **no baseline, no flags ever** |

Root causes: `concepts` is in neither `TRANSLATION_FIELDS` nor `DECLARATION_FIELDS`, so
deleting concept rows is untracked (S2); `declaration-edit` fires only when `decl and not
trans` (`translate.py:2439-2440`), so growing any translation field masks any declaration
deletion (S3c — demonstrated with counts asserts 1→2, requires 1→0, concepts 2→1 →
`flags=[]`); `_shape` returns `{}` for an unparseable first attempt and `_diff_flags`
returns `[]` against an empty side, so a garbage attempt 1 erases the baseline.

Why it matters: the documented attack family ("deleting content instead of fixing") converges
to corpus artifacts; the guards exist, are tested, and bind nothing. Confidence: high.

### §A3 — MEDIUM — baseline is RED in scope: `test_d4b_no_table_and_no_concepts_declared_is_silent` fails on the committed tree [RUN]

`walkthrough/test_link.py:825-838`, `walkthrough/paper_pipeline/phase_1/fixtures.py:173-194`.

The test renders the default `fixtures.m0255_module()` and asserts no
`concept-table-absent` finding, on the stated premise *"module_dict: concepts=[]"*. Since
the 2026-08-12 inputs-gloss ruling, `m0255_module()` declares **two** concepts (glosses for
its borrowed `new_material/1` and `disallowed/1` — verified by rendering:
`%% concepts: new_material/1, disallowed/1`). The rendered module therefore *does* declare
concepts and `concept-table-absent` correctly fires; the test's premise is stale:

```
assert not by_id(link.collect([p]), "concept-table-absent")
AssertionError: assert not [Finding(check_id='concept-table-absent', ...)]
```

Fails in isolation too; both files were last touched in the same commit (`3d856a8`), so the
red shipped with the fixture change. The property the test pins ("a module declaring no
concepts must not acquire the warning — a warning on every run is how the old `no %%
provides:` message became invisible") is now only held by `link.py --self-test` check (i4),
not by a green pytest pin. Confidence: high.

### §A4 — MEDIUM — `link.py` cannot read the worked example's `%% requires` header: 3 false ERRORs on `m0255.lp`, and those dependencies can never be tracked [RUN]

`walkthrough/link.py:138-141` (`HDR`), `walkthrough/m0255.lp:4`.

`m0255.lp` writes `%% requires (from other clauses): policy_class/2, scope/2,
out_of_scope/2`. `HDR` requires the colon to follow the key with only whitespace between
(`(inputs|requires|...)[^\S\n]*:`), so prose between the key and the colon makes the whole
header invisible. Running the tool on the repo's only worked example:

```
$ link.py m0255.lp
  ⛔ 3 UNRESOLVED REFERENCE(S) — used in a body, defined nowhere, and not declared:
      `out_of_scope/2` ... declared neither in `%% inputs:` nor in `%% requires:` ...
      `policy_class/2` ...
      `scope/2` ...
```

The file *does* declare all three — as requirements. Consequences: (a) false ERRORs at
single-file scope on the flagship artifact; (b) `requires-unprovided` (the status designed
for exactly this) can never fire for them, so the three-way diagnosis of `03_pipeline.md`
Part 4 §2 is corrupted for any hand-written file using the prose form; (c) the regression
test (`test_regression_m0255_worked_example_stays_green`) only covers the 4-file link,
where `clauses/*.lp` happen to provide the predicates, hiding the parse hole. Generated
modules are unaffected (`render_lp` emits bare `%% requires:`). Confidence: high.

### §A5 — MEDIUM — `%% forbid-body:` declarations are silently inert under two ordinary header shapes; a violating rule then passes with zero findings [RUN]

`walkthrough/link.py:118` (`FORBID` regex), `walkthrough/link.py:489-528`
(`_check_rule_shape`).

`FORBID = r"^%%\s*forbid-body\s*:\s*(\w+)\s*<-\s*(\w+)\s*$"`. Two shapes drop the
declaration without trace, and with the banned predicate properly declared as an input the
violating rule then produces **no findings at all**:

```
L1c: %% forbid-body: Permit <- Purpose   +   asserts(t1, permit, produce(M)) :- purpose(M).
     findings: [('situation-input', 'note')]          <- NO rule-shape
L2c: %% forbid-body: permit <- purpose   % author note   + the same violating rule
     findings: [('situation-input', 'note')]          <- NO rule-shape
```

Capitalised names never match the lowercase derived set (statuses and head predicates are
lowercase); the `$` anchor rejects any trailing comment. Both are things a hand-written
`.lp` plausibly carries — `m0255.lp` itself is the intended consumer of this check
(`test_d2_forbid_body_fires_on_a_relation_head` says so). Generated modules are protected
by `ForbidBody`'s lowercase validation, so this bites exactly the hand-written link glue
the rule-shape check exists for. A forbid-body claim is "checked by inspecting the program
rather than by running it" (`schema.py:ForbidBody`); an inert declaration makes it *look*
enforced while enforcing nothing — the dead-rule failure mode the declaration was invented
to prevent. Confidence: high.

### §A6 — MEDIUM/LOW — a module may declare `requires: X` and provide X itself; no check ever sees the false promise [RUN]

`schema.py:866` (`known` includes ontology ∪ requires ∪ inputs), `link.py`
`defined_predicates()` / `requires-unprovided`.

A module with `requires=["restricted/1"]` **and** an ontology fact `restricted(csam)`
passes `validate_all` with 0 breaches and `run_checks` as `translated` with 0 findings.
`requires` means *another clause* must define it; here the module satisfies its own
requirement, and because `defined_predicates` counts the self-providing head,
`requires-unprovided` stays silent at every scope, forever. The interface lies: corpus
readers conclude a dependency exists and is met elsewhere. Plausible as live model output
(the schema actively allows both declarations together). Confidence: high.

### §A7 — LOW — duplicate `%%` headers: last one silently wins; earlier declarations vanish and re-surface as false unresolved-reference ERRORs [RUN]

`walkthrough/link.py:373-388` (`header()`): `for key, val in HDR.findall(...)` assigns
`out[key] = {...}`, overwriting. Repro: a hand-written file with `%% inputs:
declared_first/1` then `%% inputs: declared_second/1`, body using `declared_first(M)` →
`unresolved-reference` ERROR on `declared_first/1`, which the file plainly declared.
Generated modules emit one header per key; hand-written link sets don't have that
guarantee. Wrong-reason error rather than silent pass — noisy, not invisible. Confidence:
high.

### §A8 — MEDIUM/LOW — `concept-not-in-table` is structurally unfireable in the stage-2 repair loop [INFERRED]

`checks.py:251-254` (`_link_findings` defaults `concepts` to `schema.concept_rows(mod)`).

`run_checks` always supplies the module's own concept rows, so every signature in the
module's `%% concepts:` pointer always has a table row, and `concept-not-in-table` can
never fire during repair — it only becomes reachable when someone links files from
different runs against a merged/foreign table (and `link.py:_check_concepts` itself warns
that is a real usage). By design (the default exists to prevent the 7-of-7 false-flood),
but the consequence is not stated anywhere near the check: **stage 2 cannot detect a
dangling concept pointer at all**; the first moment it can be detected is corpus link time,
by a different component. Noting it so the asymmetry is a decision and not a surprise.
Confidence: high (the code path is total; marked INFERRED only because corpus-link
behaviour is agent C's scope).

### §A9 — LOW — all-`unclear` closure is telemetry-only, as documented [RUN, confirming design]

`translate.py:2526-2531`. `_unclear_rate` measures the legal-but-hollow strategy of
answering `unclear` on every act class (restoring the silent default the declaration
exists to replace). It is recorded in `run.json` and nothing consumes it. This is the
documented posture and the rate is the right shape of detector — listed only so §A1/§A2's
recommendations can be checked against it: a corpus can be 100% `translated`, 0 flags, and
100% unclear-closure, and every dashboard line reads green. Confidence: high.

---

## Prior findings — re-verification

| prior finding | status here | evidence |
|---|---|---|
| **Attack D** (REVIEW_QUEUE §8.3): concepts-only module validates `translated`, renders comments-only `.lp` | **STILL OPEN**, and generalized | §A1, runs A1–A5. The partial content guard at `schema.py:789` *includes* `concepts` in the disjunction, so the documented fix ("owes at least one of asserts/defines/ontology/beats") was not applied. The borrow-gloss rule additionally makes the guard satisfiable by any module with a borrow. |
| DEBUGGING_TIPS §13 / REVIEW_QUEUE §8.4: `acts` absent from the body-declaration set `known` | **STILL OPEN** | [RUN] a module declaring `be_explicit_about_inability(I)` in `acts` and referencing it in another assertion's body is refused: *"body references `be_explicit_about_inability` but nothing declares it"* with three remedies, all wrong for an act (`schema.py:861-866` — `known = declared | requires | inputs`, no acts). This is the documented `m0091` non-convergence trap. Not re-proposing the rejected fix (loosening `known` to include `concepts` would re-open F4); the §8.4 distinction (acts = declaration site, concepts ≠) is intact in current code. |
| `concepts` deliberately excluded from `known` (F4) | intact | `schema.py:861-866`, verified while reproducing §13; `test_a_concept_does_NOT_declare_the_predicate_for_the_undeclared_check` pins it. |
| Q-4: stale `dryrun.txt` red tracked as `xfail(strict)` | as expected | baseline: `1 xfailed` (`test_prompt_examples.py:193`); `translate.py --self-test`: 51 passed / 1 failed on the same artifact. Not re-reported. |
| `m0255` C3 rules behaviourally inert (`FINDINGS_m0255.md`) | known; confirmed out of link.py's reach | `link.py` is static: `_check_rule_shape` reads only `%% forbid-body:` declarations and rule text; behavioural inertness needs the probe stage. The file's own `lifted <- purpose` declaration IS parsed and exercised (relation-form reading pinned by `test_d2_forbid_body_fires_on_a_relation_head`, green). |
| `m0255` stage-1 output CONTAMINATED (worked example in prompt) | known | no contaminated artifact was used as a fixture here; all repros were freshly constructed modules. |

---

## Minor notes

| # | note | status |
|---|---|---|
| M1 | `run_checks(lp_path=...)` has no production caller; a stale path would check a different file than `mod` describes. Dead-ish parameter; keep or delete, but nobody is exposed today. | INFERRED (grep: only `checks.py` itself) |
| M2 | corpus-scope `unresolved-reference` / `situation-input` / `concept-declared` attribute `where` to **all** linked files, not the one using the atom (`link.py:921` ff.). Imprecise at multi-module scope. | INFERRED |
| M3 | table-row-without-header-pointer is unchecked: `concept-not-in-table` compares header → table only. A `concepts.json` row whose module lost its pointer (cross-run merge) is invisible. | INFERRED |
| M4 | `_check_closure` reads only the `%% acts:` header; act inventories carried as `act/1` facts (`contradiction_probe/doc.lp`) are invisible to it — stated in the code's own LIMIT note, correctly not fixed. | as documented |
| M5 | `_check_beats_cycle` reads ground `beats` FACTS only; a beats RULE with variable winner/loser escapes — stated LIMIT in the code. Lower bound by design. | as documented |
| M6 | `link.py --self-test`'s `_module()` is a hand-written duck of `render_lp`'s shape (zero-dependency by design). I diffed it against `render_lp` output: header shapes currently agree (closure line, concepts parenthetical, empty `%% requires:`). Drift risk is real and unpinned by any test — the pytest side renders real modules, but nothing compares the self-test duck to `render_lp` byte-for-byte. | INFERRED |
| M7 | negative results worth recording: a headless atom used **only under `not`** IS still reported by clingo and caught as `unresolved-reference` [RUN]; a malformed `%% concepts: foo /1` header drops the sig from the pointer but the table still declares it, so usage surfaces as a `concept-declared` note, not silence [RUN]. | RUN |
| M8 | `HDR`'s alternation matches `closure` but the if-chain has no branch for it (CLOSURE_HDR handles it separately) — a harmless dead arm in the regex loop. | INFERRED |

---

## Improvement opportunities (concrete)

1. **Close the hollow-module class with one mechanical check.** Drop `concepts` from the
   content-guard disjunction at `schema.py:789` (the REVIEW_QUEUE §8.3 wording: a
   translated module owes at least one of asserts/defines/ontology/beats), AND add a
   stage-2 rendering check: if the rendered `.lp` has zero non-comment statements, that is
   an error finding ("rendered nothing"). The second catches the whole class — including
   any future field that renders nothing — without reasoning about fields. Pair each with
   the attack shapes in §A1 as the failing fixtures (they are ready-made).
2. **Make the gaming guards bind, or quarantine their output.** Minimal: when
   `out.flags` is non-empty, `run()` writes the module to a quarantine side-directory and
   the run summary counts it separately (needs a waiver-style flag to admit it), instead of
   `{cid}.lp` entering the corpus as `translated`. `graveyard.py` already preserves the
   flagged cases for inspection; the missing step is only keeping them out of the corpus.
3. **Plug the three `_diff_flags` holes** (all cheap): add `concepts` to the tracked sets;
   split the `decl and not trans` condition so declaration edits are flagged INDEPENDENTLY
   of translation edits (S3c); record an explicit `no-baseline` flag when
   `_shape(attempt 1)` is empty, so an unparseable first attempt is visible rather than
   silently unguardable.
4. **Header hygiene in `link.py`:** (a) accept prose between key and colon, or emit a loud
   `unrecognized-header` note for any `%%` line that parses under no branch — §A4's false
   ERRORs and §A7's silent overwrite both become visible; (b) strip trailing `%` comments
   before matching `FORBID`, lowercase the captured names, and emit a note when a
   `%% forbid-body:` line is present but unreadable (§A5). A declaration that cannot be
   parsed must never be silent — that is the exact failure mode the check exists to kill.
5. **Add a self-provided-`requires` note** (§A6): when a module declaring `requires: X`
   also defines X itself, report "declares another clause must define X, and defines X
   itself" — one set intersection in `_coherent`.
6. **Corpus observability for the next campaign:** persist `n_rendered_statements`
   (non-comment lines) per module in `run.json` beside the existing `n_asserts`/`n_ontology`
   counters, and print the run-level `unclear_closure_rate` mean in the summary line. Both
   make §A1/§A9-class hollowing measurable without re-rendering 593 files.
7. **Fix §A3** by constructing the concepts-free module explicitly
   (`_no_auto_gloss=True`, no borrows) so the silence property has a green pin again; the
   test's own docstring already names the property worth keeping.

---

## What I did not check

- **Prompt quality** (`prompt/*.md`) — treated as data only, per scope; whether the worked
  example teaches the hollow shapes of §A1 needs held-out measurement.
- **Other agents' scopes**: `seats.py`, `readback*.py`, `probe*.py`, `mutate_*.py` (B),
  `resolve_runs/` (C), `guard.py`/`eval*.py`/spend accounting (D). Read only for
  interfaces. Note for agent C: `resolve_runs/graph_v2/translate_exec.py` is a SECOND copy
  of the repair loop; whatever is ruled for §A2's guards should be applied there too.
- The 356 deselected tests (seats/readback/mutate); the full suite was deliberately not
  run.
- Live provider behaviour (e.g. the recorded `finish_reason: null` claim) — taken as
  documented; no API calls made.
- `version.py` staleness machinery beyond its seam with `run()`; `model/`,
  `deontic_probe/`, `contradiction_probe/`.
- Whether `config_arm_*.json` variants change any of the above (eval-arm configs; D's
  scope).

*Reviewer: adversarial engineering-excellence pass, stage-1/stage-2 core. Evidence
discipline per `README.md`: every RUN above is reproducible from the scratchpad scripts in
`/tmp/review_stage12.uUh7rI/` (`attack_schema.py`, repair scenarios S1–S3c, link batteries
L1c/L2c/L3/L6/L7b) using the project venv, offline.*
