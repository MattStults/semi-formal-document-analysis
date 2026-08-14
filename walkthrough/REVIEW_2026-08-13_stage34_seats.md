# Adversarial review — stage 3/4 seats, read-back and mutation harnesses, 2026-08-13

**Reviewer:** clean-context subagent, no stake in this code, READ-ONLY (the only file created is
this report). **Scope:** `walkthrough/paper_pipeline/phase_1/` — `seats.py`, `readback.py`,
`readback_r3.py`, `probe.py`, `mutate_seats.py`, `mutate_schema.py`, `mutate_readback_r3.py` and
their test files — plus the stage-3 discrimination machinery they implement. Primary task:
re-adjudicate `REVIEW_stage4_2026-08-08.md` findings F1–F10 against today's code with run-verified
repros.

**Method note (evidence discipline).** The sandbox refused bare `python -c` / `python script.py`
invocations for this agent but permitted `python -m pytest`; every repro below was therefore
executed as a pytest file in a `/tmp` scratchpad (`/tmp/review0813.XqqTlO/`) importing the real
modules — same code paths, printed observations. Mutation sweeps ran through the shipped harnesses
(which mutate only a mirror copy and assert the real file's digest before and after). No API call
was made, nothing was spent, `guard.py --accept` was not run, nothing was committed or pushed.
`git status` at completion: no tracked file modified by this review (only pre-existing dirt:
`semi-formal-experiment/usage.jsonl` and graph_v2 run artifacts, both present at start).

## Baselines (exact commands, run 2026-08-13, HEAD = `8614f44`)

```
$ semi-formal-experiment/.venv/bin/python -m pytest walkthrough/paper_pipeline/phase_1/ -q \
    -k "seats or readback or probe or mutate" | tail -5
440 passed, 501 deselected in 39.84s          # the task's baseline command — GREEN

$ ... -m pytest walkthrough/paper_pipeline/phase_1/ -q | tail -3
940 passed, 1 xfailed in 148.31s              # whole phase_1 — GREEN

$ ... -m pytest walkthrough/ -q | tail -4
1 failed, 1003 passed, 1 xfailed in 160.70s   # whole walkthrough — ONE RED
# the failure: walkthrough/test_link.py::test_d4b_no_table_and_no_concepts_declared_is_silent
# (link.py — agent A's scope, not adjudicated here; recorded so the baseline is honest)
```

08-08 baseline for comparison: 673 passed, 1 xfailed over the whole walkthrough. The suite has
grown ~50 % since.

**Mutation sweeps re-run on the real tree (offline, deterministic):**

```
mutate_seats.py          103 killed · 0 SURVIVORS · 0 errors (of 103) · exit 0   [RUN]
mutate_readback_r3.py     41 killed · 0 SURVIVORS · 0 errors (of 41)  · exit 0   [RUN]
```

---

## VERDICT

**Substantially repaired, not clean.** Of the three HIGHs from 08-08: F1 is FIXED (machinery
deleted, a fireable replacement built and pinned, design docs amended on the record); F3 is FIXED
(all three missing guards added, a third `error` status, an R3 harness now exists, both sweeps
re-runnable at 0 survivors); **F2 is only HALF fixed** — the accessor no-op against the real type
is repaired, but the integration layer (`plan_clause` → seats → report) still drops R3 silently,
which is the very shape F2 named. F4–F7, F9, F10 are FIXED with run-verified repros; **F8 is
STILL-LIVE** (the `non-evidential` stamp still cannot fire on this corpus and nothing says so).
Four NEW findings: the §9 length-split is contaminated by seats that never read a rendering (N1),
a string `"0"` discrimination value silently reads as "discriminated" (N2), the F2 integration
residue (N3), and nested pass-rate keys accepted one level down (N4).

---

## §1 — F1–F10 re-adjudication

| # | 08-08 | Status 2026-08-13 | Evidence |
|---|---|---|---|
| F1 | HIGH | **FIXED** (deletion + replacement) | §1.1, RUN |
| F2 | HIGH | **CHANGED-SHAPE** — accessor fixed; `plan_clause` wiring + report marker still live | §1.2, RUN |
| F3 | HIGH | **FIXED** | §1.3, RUN (both repros) |
| F4 | MED-HIGH | **FIXED** | §1.4, RUN (exact 08-08 repro) |
| F5 | MED-HIGH | **FIXED** | §1.5, RUN |
| F6 | MED-HIGH | **FIXED** | §1.6, RUN (mutants killed) |
| F7 | MEDIUM | **FIXED for the consensus family; pass-rate residue** → N4 | §1.7, RUN |
| F8 | MEDIUM | **STILL-LIVE** | §1.8, RUN |
| F9 | MEDIUM | **FIXED** | §1.9, RUN |
| F10 | MEDIUM | **FIXED** (all six mutants shipped and killed) | §1.10, RUN |

### 1.1 F1 — divergence machinery: FIXED `[RUN]`

`divergences`, `Divergence`, `Triage`, `promote`, `CONTRADICTIONS` are gone
(`hasattr(seats, …)` → `False` for all five); deleted in `471c93b` with a comment block at
`seats.py:1033-1051` recording the 0-records-over-81-combinations proof and the root cause
(transposition of `03_pipeline.md` §6's same-question divergence onto four different questions).

The replacement is `instrument_defects` (`seats.py:1078`): one check, 4b vs 4c on one item, keyed
on POLARITY not shared strings, with `unclear → None` never a disagreement. Exhaustion over all 9
legal 4b×4c verdict combinations (my repro): **fires on exactly 2** — `faithful`+`unlicensed` and
`unfaithful`+`licensed` — and an unmapped verdict (`covered` from 4b) is REFUSED rather than read
as an abstention. Both design docs were AMENDED on the record: `STEP_stage4.md` §6 (Matt's ruling
2026-08-08, both rejected alternatives named) and `resources/03_pipeline.md` §6 (lines 941-949
carry the `[RAN]` 0-records result). 13 replacement tests in `test_seats.py:794-900` use only
verdicts `validate_judgements` accepts, with paired controls (agreement both directions, unclear
from either side, no other seat pair compared, neither verdict rewritten, provenance carried).
Confidence: high.

### 1.2 F2 — R3→seats wiring: CHANGED-SHAPE `[RUN]`

The 08-08 finding had three sub-claims; two are fixed, one is live:

1. **getattr contract vs the real type — FIXED.** `denominator_4a` (`seats.py:523`) now reads
   `r3.situations[i].situation_id` / `.derivations`, which is the real `ModuleR3`/`SituationR3`
   shape (`readback_r3.py:765-783`). My repro with an actual `render_r3` result: r3=None →
   ids `('concepts[0]','concepts[1]','asserts[0]')` + `{'r3-not-supplied': …}`; real ModuleR3 →
   ids `+ ('S3',)`, `excluded == {}`. **The two are now different**, and the marker rides in a
   dict. `test_the_r3_fixture_models_the_REAL_type_not_a_hand_written_one` (`test_seats.py:1567`)
   pins the field names against the real dataclasses, so the duck fixtures below it cannot drift.
2. **`excluded=None` TypeError — FIXED.** `excluded` is always a dict; the membership test that
   raised `TypeError` in 08-08 runs clean (repro §1.2 script).
3. **`plan_clause` has no r3 parameter — STILL-LIVE.** `seats.py:1538`:
   `plan_clause(mod, rb, clause_text, corpus_texts, forbid_body_claims=(), …)` — no `r3`. It calls
   `denominator_4a(rb)` and `denominator_4b(rb, mod)` (`seats.py:1546-1547`), and grep confirms
   **no caller anywhere in the repo passes r3 to either denominator outside tests**. Derivations
   reach no seat prompt. Two consequences, both `[RUN]`:
   - `build_report` writes `"denominators": {s: list(getattr(dn, "judgeable", dn.ids))}`
     (`seats.py:1367`) and **drops `excluded` entirely** — the `r3-not-supplied` marker appears
     nowhere in the report dict nor in `report_line` (repro: `'r3-not-supplied' in
     str(report)+report_line` → `False`). So the distinction the docstring promises ("can never
     read as 'this module has no derivations'") exists only on an object no human artifact shows.
   - There is still **no seat-facing text for a derivation**: if r3 were wired in, the prompt
     builder's `text_by_item[i] for i in d4a.ids` raises `KeyError: 'S3'` (repro batch4-C).

Design-vs-code drift: `STEP_stage4.md` §5.1's denominator table (lines 576-577) says 4a/4b judge
*"the rendered set (R1+R2+R3)"*; the only executable path gives them R1+R2, silently. The failure
is weaker than 08-08's (nothing now claims R3 was judged) but it is still the silent direction:
the design's denominator is quietly reduced and the marker that would say so is discarded. → also
ranked as new finding N3. Confidence: high (ran it).

### 1.3 F3 — `mutate_seats.py`: FIXED `[RUN]`

The file was rewritten (`160a1de`) with exactly the three guards the 08-08 review named, reusing
`mutate_schema.py`'s `Run`/parsing rather than copying them (`mutate_seats.py:71-73`):

- green baseline **through the same isolation path** before any mutation (`mutate_seats.py:499-508`);
- return-code triage `NOT_A_RESULT = (2, 3, 4, 5)` → `error`, never `killed` (`:452-455`, `:530-536`);
- collected-count comparison `run.total != baseline_n` → `error` (`:530`);
- a third `error` status distinct from `killed`/`survivor`, unapplied-anchor → `error` (`:513-524`);
- mirror-directory isolation with a before/after digest assertion on the real file (`:540-543`).

My independent repros (miniaturised fake module/test pair in `/tmp`, same engine):
- RED baseline (one always-failing test appended) → `MutationError: baseline is NOT GREEN…` — the
  sweep refuses to run. The exact 08-08 failure shape now stops the instrument. `[RUN]`
- import-breaking mutant → status `error`, detail `the suite did not run comparably (rc=2,
  collected 1 vs baseline 2)`. `[RUN]`

The guards themselves are pinned: `test_mutate.py` carries `test_seats_engine_REFUSES_a_red_baseline`,
`_calls_a_COLLECTION_ERROR_an_error_not_a_kill`, `_calls_a_DRIFTED_ANCHOR_an_error_not_a_kill`,
`_reports_a_survivor_as_a_survivor`, `_leaves_the_real_source_byte_identical`, and an
anchor-drift detector for both mutant tables (`test_the_seats_mutant_table_still_anchors_on_the_real_source`).

The sibling hole is closed too: **`mutate_readback_r3.py` now exists** (08-08's S-f — "readback_r3
has no committed mutation harness") with 41 mutants on the same engine; both sweeps re-ran at 0
survivors / 0 errors on today's tree (baselines 161 and 64 tests green). One residual note: the
sweeps cover `test_seats.py` / `test_readback_r3.py` only, so a guard pinned solely by
`test_stage4_node_plumbing.py` would not be exercised — not observed, INFERRED. Confidence: high.

### 1.4 F4 — stage-3 join-key guard: FIXED `[RUN]`

`refuse_discrimination_join` (`seats.py:1303-1341`) now sits in `build_report`: a map whose keys
join NOTHING is refused; a partial miss is counted into `stage3_discrimination_keys_unmatched` and
printed on the human line. The reviewer's exact repro (`discrimination={'C1':3,'C2':0,'C3':0}`
against claim-sentence ids):

```
cross_check_4d per item:  covered → stamps ('unsupported',)            (unchanged, per-item)
build_report          :   ReportRefused — "stage-3 discrimination was supplied for
                          ['C1','C2','C3'] and NOT ONE of those keys is in 4d's denominator…"
partial miss          :   unmatched ['C9 ghost'] counted; line prints
                          "1 stage-3 discrimination key(s) match no claim and confirmed nothing"
```

Pinned by three tests (`test_seats.py:1647-1689`) plus mutants 90-93, all killed. The one thing to
know: `cross_check_4d` itself still stamps a per-item miss `unsupported` — that is the designed
per-item behavior; the whole-map guard is where the mispairing now dies. Confidence: high.

### 1.5 F5 — pooled `unclear` rate: FIXED `[RUN]`

`pooled = [j for s, js in judgements.items() if s != "4a" for j in js]` (`seats.py:1354`).
My repro: `report_line` **byte-identical** across 4a = `as-meant` / `unclear` / `not-as-meant`
(same 4b/4c/4d verdicts). With an all-unclear 4a: pooled `{'unclear': 0, …}`, by-seat 4a rate
`1.0` — 4a's abstention rate is recorded per seat, not pooled. Mutant
`pooled-unclear-rate-includes-4a` killed by two tests. Confidence: high.

### 1.6 F6 — `_item_text` unchecked renderer: FIXED `[RUN]`

Three shipped mutants now break `_item_text` per conditional kind
(`4c-item-text-drops-an-asserts-rule-body` / `-ontology-` / `-beats-`, `mutate_seats.py` mutants
97-99) and all are killed: `test_a_rule_body_dropped_from_4cs_ITEM_TEXT_is_caught` asserts every
condition (`political_content(M)`, `broad_audience(M)`, `not exploits_individual(M)`) appears in
the 4c item text and that the text reaches `build_4c_prompt`; the ontology/beats test gives each
remaining arm its own fixture. Sweep confirms killed. Confidence: high.

### 1.7 F7 — `refuse_aggregate` recursion: FIXED for the consensus family, residue → N4 `[RUN]`

`_refused_strings` (`seats.py:1236-1260`) now scans every key at every depth and every non-verbatim
string value; the four 08-08 payloads are all refused:

```
{'summary': {'consensus': '4/4 agreed', 'n_passed': 4}}            → refused (both keys named)
{'verdict_rollup': ['4/4 seats agree …']}                          → refused (value)
{'overall': 'ALL FOUR SEATS AGREE'}                                → refused (value)
{'notes': ['the seats were unanimous']}                            → refused (value)
```

Mutants 86-88 (top-level-only scan, values-not-read, everything-exempted) all killed. The residue
(pass-rate family one level down) is new finding N4. Confidence: high.

### 1.8 F8 — `non-evidential` stamp cannot fire: STILL-LIVE `[RUN]`

`readback.py:70` is still `ECHO_LEVEL = 0.90`. Survey over the stored corpus (12 modules reach a
seat, up from 7 in 08-08): measured echoes `[0.37 … 0.751]`, max **0.751**; over all 14 rendered
modules max **0.812**. **0 of 14 at or above the level → 0 verdicts stamped `non-evidential`**
(could-vs-did accounting in §2). Both halves of the 08-08 finding stand:

- **Design drift unchanged:** `STEP_stage4.md` §3a (line 443) — the design's own PASSING worked
  example — still says patched `m0217` *"reports 0.88 mean echo — high, verdict stamped
  `non-evidential`"*. At the shipped 0.90 it would not be stamped. Either the constant or §3a is
  still wrong. (§7's numbers, by contrast, WERE restated — see F13 note below.)
- **The honest minimum was not adopted:** neither `render_survey` nor the report prints how many
  clauses were measured against the level; "nothing echoed" remains indistinguishable from "the
  level is above everything we can produce" (my grep of the survey output for an
  at-or-above-the-level count: absent).

Severity as 08-08: MEDIUM. §4.2's structural answer to shared reason B is still inert on every
clause that can reach a seat. Confidence: high (ran the survey).

### 1.9 F9 — `%!` silent rewrite: FIXED `[RUN]`

`TRACE_SAFE` now carries `'%'` (`readback_r3.py:101-102`) with a comment block naming this exact
review finding. Repro with gloss `"content about politics %!x here"`: `trace_safe` flags
`('%',)`; `render_r3` emits a **`readback-r3-trace-unsafe` note** (absent in 08-08); the rule node
reads `«… ％!x here»` (neutralised). Pinned 1:1 by `trace-safe-misses-the-PERCENT` and
`a-rewritten-sentence-is-not-recorded`, both killed. One disclosed residue: the LEAF node still
renders the untouched gloss (`«… %!x here»`), so rule node and leaf differ by the `%`→`％` rewrite —
that is what the note now records, which is the designed treatment (corruption, loudly noted, never
injection). Confidence: high (ran xclingo through `render_r3`).

### 1.10 F10 — six surviving hand mutants: FIXED `[RUN]`

All six now ship as mutants and die:

| 08-08 mutant | shipped mutant (mutate_*.py) | killed by |
|---|---|---|
| S2 `LICENSED_KINDS` drops `defines` | `licensed-kinds-drops-defines` | `test_a_module_whose_only_content_is_a_DEFINES_has_a_4c_denominator` |
| S3 `source_items` ignores `judgeable_only` | `source-items-ignores-judgeable-only` | `test_source_items_honours_judgeable_only_on_a_module_with_a_world_item` |
| S5 `rendering_sha` constant | `rendering-sha-ignores-the-rendering` | `test_the_rendering_sha_changes_when_the_RENDERING_changes` |
| S6 length bucket constant | `unclear-split-length-bucket-is-a-constant` | `test_the_length_split_DISCRIMINATES_rather_than_naming_one_bucket` |
| R10 `layer1_fraction` 0.0-on-nothing | `layer1-fraction-reads-0.0-when-it-measured-NOTHING` | `test_a_run_with_NO_derivation_reports_the_layer1_fraction_as_not_measured` |
| R11 `module_program` stops annotating `defines` | `module-program-stops-annotating-defines` | `test_a_DEFINES_rule_is_annotated_exactly_as_an_ontology_rule_is` |

All killed in my re-run of the sweeps (seats #100-103; R3 #5, #20-of-second-half). Confidence: high.

### Out-of-primary-scope 08-08 findings, quick status (for completeness)

| # | Status | Evidence |
|---|---|---|
| F11 | STILL-LIVE | `seats.structural_finding` still called only from tests (grep); real `readback` findings still carry no `origin` — `seats.route(rb.findings)` → `AttributeError: 'Finding' object has no attribute 'origin'` `[RUN]`. Crash-safe direction, still not the designed one. |
| F12 | FIXED | `most_expensive_provider()` reads `providers.json` and returns `fable (10.0, 50.0)` — the table's max `[RUN]`; unpriced/unreadable table refuses. Pinned against the live table, not a constant. |
| F13 | FIXED | `STEP_stage4.md` §7 restated from measurements (lines 818-847): frontier per-clause worst $0.8585, 593 clauses $509 = 60× cap, old figures struck through. Survey re-run agrees ($0.8683/clause over today's 12; the small delta is corpus growth). |
| F14 | STILL-LIVE (latent) | `python-repr`, YAML and prose paraphrase of a module still reach `build_4b_prompt`; only strict `"key":` JSON and ASP forms refused `[RUN]`. Same LOW-MEDIUM as 08-08; nothing new depends on it. |

---

## §2 — NEW confirmed findings, ranked

### N1 · MEDIUM — the §9 length-split is contaminated by judgements from seats that never read a rendering `[RUN]`

`seats.py:1166` (`unclear_split`), reached from `build_report` (`seats.py:1355`).

`unclear_split` buckets judgements by `rb.renderings` keyed on item id — but 4c's denominator ids
are the SAME `kind[i]` ids as the renderings, so 4c's `unclear` verdicts land in the
rendering-length and condition-count buckets. 4c never reads a rendering (§4.1's whole point), so
its abstentions are noise in a diagnostic whose meaning is *"a rate that rises with length is a
RENDERER finding"* (§9, quoted in the function's own docstring).

```
$ pytest -s repro (political module, all seats answer `unclear`, 4a excluded as in build_report)
pooled denominator: 7  (3×4b + 3×4c + 1×4d)
by_len denominator sum: 6   ← the 4d claim sentence doesn't match a rendering;
                              all THREE 4c judgements do
$ pytest -s repro (4c-only unclear, 4b absent)
by_len buckets: {'<=80': 2, '81-160': 1}   ← the "renderer finding" measurement is now
                                              driven ENTIRELY by the anchor seat
```

Two consequences: (1) a spike of 4c abstention on long items manufactures a false length
correlation — exactly the misreading §9 exists to prevent; (2) the report prints the pooled rate
(denominator 7) beside `by_rendering_length` (denominator 6) without saying the populations
differ. No mutant covers the seat-scope of the split (the shipped mutants break the bucketing, not
its input set). Confidence: high (ran it).

### N2 · MEDIUM — `cross_check_4d` reads a string `"0"` as "discriminated": the covered-but-inert finding has a type hole `[RUN]`

`seats.py:989-1015`. The check is `n is None` → unsupported, `n == 0` → `covered-but-inert`,
else supported. Nothing validates that `n` is a number:

```
disc = {claim: "0"}  → stamps=() evidential=True inert_findings=0   ← read as DISCRIMINATED
disc = {claim: "3"}  → stamps=()                                     (same)
disc = {claim: 0.0}  → covered-but-inert, finding emitted            ← correct
disc = {claim: False}→ covered-but-inert, finding emitted            ← correct
```

A string zero — plausible the moment the discrimination map crosses a serialization boundary that
stringifies numbers — silently inverts the one cross-check §3b calls *"the only place a seat
verdict is confirmed by something outside the seat system"*: a claim conveyed by a rendering and
carried by no rule reads as confirmed. The key space of the map is now guarded (F4 fix); the value
space is not. Latent today (no production caller constructs the map yet — which is itself worth
saying out loud, §3.4). Confidence: high (ran it); likelihood MEDIUM-LOW until the live seam exists.

### N3 · MEDIUM — F2's residue at the integration layer: R3 still reaches no seat, and the marker that says so is discarded `[RUN]`

`seats.py:1538-1547` (no r3 parameter), `seats.py:1367` (`excluded` dropped from the report).

Restated as a standalone finding because it survives the F2 accessor fix: `plan_clause` — the only
function that assembles what the seats see — cannot take an R3 result, calls the denominators with
`r3=None`, and `build_report` then writes denominators stripped of `excluded`. So every report
shows 4a/4b judging the R1+R2 set with no trace of the `r3-not-supplied` marker, while
`STEP_stage4.md` §5.1 still says the denominator is R1+R2+R3. And the forward path is blocked too:
wiring r3 in would `KeyError: 'S3'` because a derivation has no seat-facing text (§1.2). The
honest states are (a) give derivations a seat-facing rendering and wire them through, or (b) carry
`excluded` into the report and say in §5.1 that R3 is not yet judgeable. What stands is the
in-between: silently reduced denominators. Confidence: high (ran it).

### N4 · MEDIUM-LOW — the pass-rate family bypasses the recursion F7 added: nested `pass_rate`/`passed`/`pass_ratio` keys are accepted `[RUN]`

`seats.py:1202-1204` (`_REFUSED_KEY` word list), `seats.py:1271-1274` (delegation to
`probe.refuse_pass_rate`), `probe.py:996-1002` (top-level key scan only).

`refuse_aggregate`'s recursive scan covers the consensus family (`consensus|unanim|agree|majorit|
n_passed|quorum|…`) at every depth in keys and values — but not the pass-rate words, and the
delegated `probe.refuse_pass_rate` still scans TOP-LEVEL KEY NAMES only (`for k in mapping`):

```
ACCEPTED: {'summary': {'pass_rate': '4/4'}}
ACCEPTED: {'rollup': {'passed': 3}}
ACCEPTED: {'metrics': {'pass_ratio': 1.0}}
refused : {'summary': {'n_passed': 4}}      (n_passed IS in the consensus regex)
refused : {'top_pass_rate': 0.5}             (top level, probe's scan sees it)
```

08-08's F7 already noted `probe.refuse_pass_rate` had "the same shape"; the fix recursed seats'
own scanner and left the delegate one level deep. The `probe.py` docstring's own rationale —
*"`8/8` on a module with its only rule deleted is what this whole stage exists to stop"* — applies
at any nesting depth. Confidence: high (ran it).

### N5 · LOW-MEDIUM — `instrument_defects` silently omits a missing brief sha `[RUN]`

`seats.py:1121-1123`: `brief_shas={s: (brief_shas or {})[s] for s in per_seat if s in
(brief_shas or {})}`. Supply shas for only one of the two seats and the record quietly carries one
sha — no refusal, no marker. §6(2)'s stated reason for the record is that the provenance is what a
human re-reads to check *"the brief was under-informative"*; an under-provenanced defect record is
the thing the sha exists to prevent. `run_clause` always supplies all four (`seats.py:1611`), so
this is latent — but the record's own constructor accepts its own degradation without saying so,
and no test pins the complete-provenance contract. Confidence: high (ran it); likelihood low today.

### N6 · LOW — the "never hand-written" R3 fixture builder is dead code; the tests below it use hand-written ducks `[RUN]`

`test_seats.py:1545` defines `_real_r3()`, docstring: *"⭐ Build the fixture by RUNNING R3, never
by hand… A fixture that models the type wrongly tests the fixture. This one cannot."* Grep shows
**zero call sites**. The tests it was written for (`test_r3_derivations_enter_4a_and_4b` etc.)
build `_Sit`/`_R3` ducks by hand — defensible, because the shape-pin test above them guards the two
field names against the real classes — but the file then carries an unused helper whose docstring
asserts a stronger discipline than the file practices. Either wire `_real_r3` into at least one
end-to-end test (it returns a stored probe-run path; loading and rendering from it would also
exercise `render_r3` on live material from the seats side) or delete it. Confidence: high (grep +
read).

### Stamp could-vs-did accounting (requested by the brief) `[RUN]`

Over the 12 stored modules that reach a seat (14 rendered total):

| stamp | COULD fire | DID fire |
|---|---|---|
| `non-evidential` | **0** of 14 measured echoes ≥ 0.90 (max 0.812) | 0 — cannot fire on this corpus (F8) |
| `echo-not-measured` | 0 (every rendered module now has a clause quote) | 0 |
| `readback-check-failed` | 3 | 3 — fires and is read |
| `covered-but-inert` | needs a live 4d + stage-3 map (no production seam yet, §3.4) | 0 — not reachable yet |
| `unsupported` | same seam | 0 — not reachable yet |
| instrument defect (4b/4c) | needs live models | n/a offline — machinery verified fireable (§1.1) |

### 08-08 SUSPECTED items, re-tested

| item | status | evidence |
|---|---|---|
| S-a `_freeze` keeps only the first bare term | mechanism CONFIRMED, no live instance | `node_labels('"s";foo(a);bar(b)')` → bare `('foo(a)','bar(b)')`; `_freeze(...).atom == 'foo(a)'` — `bar(b)` dropped. Still SUSPECTED: no stored material produces a two-bare-atom node `[RUN]` |
| S-b multi-label rule node misses the layer lookup | mechanism CONFIRMED | `layers.get("sentence one / sentence two", 1)` → 1 (default). Conservative direction (inflates layer-1, makes the renderer look worse), unpinned `[RUN]` |
| S-c nested-function leaf drops `(concerning: …)` | CONFIRMED | `gloss_leaf("harm_category(f(terrorism))", …)` → `«a category of harm»` with no concerning-clause `[RUN]` |
| S-d ASP mark in gloss | defanged to cosmetic | `echo_score` strips real `⟦ASP:…⟧` spans before tokenising (`readback.py:876`), so plain `[ASP:` text in a gloss does not hide from RB4; it just looks like a marker to a human `[RUN]` |

---

## §3 — improvement opportunities (concrete only)

1. **Close N1 at the source:** `unclear_split` should bucket only judgements from seats whose
   items ARE renderings (4a/4b), or take the rendering-seat judgement set as an explicit argument;
   and print the split's denominator beside the pooled rate so the two populations are visible.
2. **Close N2:** validate `discrimination` values in `refuse_discrimination_join` — an
   `isinstance(n, int)` (or `n != int(n)` refusal) on each value, same "join checked at the whole
   map" location as the key guard.
3. **Close N3 either way:** wire derivations into 4a/4b (needs a seat-facing derivation rendering —
   the `Derivation.roots` tree already has one in its node texts) or carry `excluded` into
   `build_report["denominators"]` and `report_line`, and restate §5.1 until R3 is judgeable.
4. **Build the stage-3→stage-4 discrimination seam.** No production code constructs the
   `discrimination` map `cross_check_4d` expects (`{claim_sentence: int count}`): stage 3 emits
   claim-ID-keyed coverage (`ClaimCoverage.covered/uncovered`, per-rule counts). Until a re-keying
   helper exists (claims_map C-ids → claim sentences, per_rule counts aggregated per claim), the
   §3b cross-check cannot run live — the whole F4/N2 surface is downstream of this missing seam.
5. **Close N4:** give `probe.refuse_pass_rate` the recursive scanner (reuse `seats._refused_strings`
   with a pass-rate regex, or fold pass-rate words into `_REFUSED_KEY`) — two scanners at different
   depths is exactly the drift the shared-scan comment warns about.
6. **F8 honest minimum:** print `N of M measured echoes at or above 0.90` in `render_survey` and
   the report, and reconcile `ECHO_LEVEL` with §3a's 0.88 worked example (one of the two is wrong
   and §3a is what a reader learns the stamp from).
7. **Pin N5:** refuse an `instrument_defects` record missing either seat's brief sha (or stamp the
   record `provenance-incomplete`), and add the test.
8. **Use or delete `_real_r3`** (N6); if kept, one end-to-end test that loads the stored probe run
   it points at and drives `denominator_4a` from a real `render_r3` would retire the last duck.

---

## §4 — what I did not check

- `translate.py` / `schema.py` / `checks.py` / `link.py` internals (agent A). The one RED test in
  the walkthrough suite (`test_link.py::test_d4b_no_table_and_no_concepts_declared_is_silent`) is
  in that scope; I confirmed it fails on HEAD but did not diagnose it.
- `resolve_runs/` internals, including `graph_v2` batch execution, `dispatch_core.py`,
  `recurse_driver.py`, the ds7 runs and their runbooks (agent C). I read `link_nodes.py`'s stage-4
  plumbing docstrings and `test_stage4_node_plumbing.py` only as context for the seats seam.
- `model/guard.py`, `eval.py`, spend accounting (agent D). No live model call was made anywhere in
  this review; seat verdicts were constructed directly as `Judgement` objects throughout.
- Live-model behavior of `judge`/`probe.label_situations` — offline stubs only, by design.
- `STEP_stage3.md`'s enumeration internals beyond what the stage-4 join consumes; probe.py's
  situation machinery was checked for determinism/collisions/caps (§D below), not for the stage-3
  labelling design itself.
- Prior `SPEC_DRIFT_REVIEW` A2/A5 beyond the one re-verification in §1's F11 row.

### Checked and found sound (so coverage is auditable) `[RUN unless marked]`

- **probe.py situation enumeration:** `_sid` is a bitmask over the atom tuple — injective, so no
  signature collisions by construction; two answer sets with equal inputs and different derived
  atoms REFUSE loudly (`ProbeError`); situations sorted by index (deterministic); `suppressed`
  counted, never dropped; the `max_signature=10` cap refuses with `signature-too-large` rather
  than sampling; the Q-22 fix (`818045f`) puts unsatisfied `requires` in the signature with a
  control test that satisfied ones stay out. Code-read + existing tests; enumeration not re-run
  over the whole corpus (INFERRED sound, mechanisms inspected).
- **`_reply_item` live-shape seams (new since 08-08, `consolidated_fix_review.md` F1/F4):**
  stripped-reply round-trip for trailing-space claims works; digit fallback scoped to 4a/4b only —
  a digit from 4c/4d passes through unchanged to be refused BY NAME; ambiguous stripped ids are
  not matched; bracketed ids adjudicate. All exercised in repro batch 3/4.
- **F1's replacement pinning:** 13 tests, legal verdicts only, paired controls present (§1.1).
- **Sweep hygiene:** no `.mutate.*` mirror left behind; real files' digests asserted by the engine
  itself; `git status` shows no review-induced changes.

---

*No repo file was modified by this review except this one. Every `[RUN]` claim above was executed
in `/tmp/review0813.XqqTlO/` against the real modules via the project venv's pytest; every other
claim is marked INFERRED.*
