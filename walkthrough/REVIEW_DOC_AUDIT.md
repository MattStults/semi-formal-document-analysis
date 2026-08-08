# Audit — can the four point-in-time review documents be retired?

**Audited 2026-08-07 (later session).** Nothing was deleted, nothing was edited outside this file.
No `guard.py --accept`, no `--live`, no spend, no push.

**Method.** Every finding was checked against the code and documents **as they stand today**, not
against the reviewing document's own annotation. Where a finding could be reproduced, it was:
mutations were run in a scratchpad copy of the tree, and schema shapes were pushed through
`schema.validate()` directly. The precedent is commit `d3108d5` (`STEP_stage2_and_repair.md` and
`PROPOSAL_atom_slot.md`): a review document is retired only once every finding is fixed or lives in
a document someone maintains, and only after inbound citations are redirected.

**Suite at audit time:** `pytest walkthrough/ -q` → **352 passed** (the brief said 296; `probe.py`
and `test_probe.py` landed from another agent mid-audit — for about ten minutes the suite would not
collect at all, because `test_probe.py` was committed-shaped before `probe.py` existed. It resolved
itself and is not a finding).

---

## Verdict table

| document | FIXED | RECORDED | OPEN | OBSOLETE | verdict |
|---|---|---|---|---|---|
| `phase_1/CONFORMANCE_REVIEW.md` | 6 | 4 | **5** | 1 | ⛔ **KEEP** |
| `phase_1/ENGINEERING_REVIEW.md` | 6 | 2 | **8** | 0 | ⛔ **KEEP** |
| `model/TRANSCRIPTION_REVIEW.md` | 6 | 3 | **3** | 0 | ⚠️ **KEEP** — one edit from retirable |
| `model/REVIEW_FINDINGS.md` | 1 | 0 | **1 §** | ~26 | ⛔ **KEEP** |

**No document is retirable today.** Two of them (`ENGINEERING_REVIEW.md`,
`CONFORMANCE_REVIEW.md`) are the sole written record of live defects, one of which is a
**cost-estimate error in the direction the config comment says must never be wrong**.

---

## Inbound citations, per document

Checked with `grep -rn "<basename>" --include=*.md --include=*.py --include=*.json --include=*.lp
--include=*.sh walkthrough/`.

| document | inbound |
|---|---|
| `CONFORMANCE_REVIEW.md` | **3**, all in `phase_1/STEP_stage4.md` — lines 39 (F4), 80 (F7), 195 (F6/D3 absence). ⚠️ Line 195 is load-bearing: it is how `STEP_stage4.md` justifies not addressing failure mode #5. Deleting the file breaks stage 4's argument. **None in code.** |
| `ENGINEERING_REVIEW.md` | **0.** Nothing anywhere cites it. |
| `TRANSCRIPTION_REVIEW.md` | **1**, `REVIEW_QUEUE.md:27` — and **that line is now stale** (see below). |
| `REVIEW_FINDINGS.md` | **2**, both in `model/RETIRED.md` — line 16 (*"the design record it produced is kept… stays in this directory"*) and line 78 (*"do not revive it from memory; start from `REVIEW_FINDINGS.md`"*). RETIRED.md **instructs** that this file be kept. Deleting it silently voids the one condition RETIRED.md places on reviving the formal model. |

⚠️ **A stale live record found while auditing.** `REVIEW_QUEUE.md` §1 (line 27–29) and §2.2 (line
70–74) both still say the hollow-stub bad example is dropped and §2.2 is open. It is **closed**:
`phase_1/DECISION_bad_worked_examples.md` restored it as bad example #6 in
`prompt/20_worked_example.md` and recorded the *other* drop as deliberate with a named reopen
condition. `REVIEW_QUEUE.md` should be updated whether or not anything is retired.

> ⛔ **This paragraph is itself incomplete — see §6.** Bad example #6 was restored, then measured
> twice and **REMOVED again** (that file's AMENDMENT). `REVIEW_QUEUE.md` §2.2 now records all three
> steps. Left standing above as written, because the correction is the point.

---

# 1 · `paper_pipeline/phase_1/CONFORMANCE_REVIEW.md` (400 lines)

## FIXED — verified against current code

| | finding | evidence today |
|---|---|---|
| F1 | repair transcript's first turn was a 491-byte stub, dropping every cross-reference | `translate.py:1078` passes `first_user=j["user"]`; `translate.py:2176-2180` uses it. Pinned by `test_repair.py:526 test_the_transcripts_first_turn_is_the_prompt_that_was_ACTUALLY_SENT` |
| F2 | stage 2's link checks never ran on a first-time-valid clause | `translate.py:1067-1080` — `repair_loop` is now called **unconditionally**, with the ruling written above it as a comment. Pinned by `test_repair.py:504 test_stage_2_RUNS_on_a_module_that_passes_the_schema` |
| F3 | an unrepaired module was written out as `translated` | `translate.py:1113-1125` tests `out.status not in ("translated","abstained","abstained_under_repair")`; the module's own `outcome` no longer overwrites it (`:1152`). Pinned by `test_repair.py:479` |
| F4 | `concepts` was a fourth declaration site, letting a dead rule pass | `schema.py:636-642` — `known` is now `ontology ∪ requires ∪ inputs`, with a ⛔ comment naming exactly this defect. `fixtures.py:14-19` records `test_link.py`'s wrong `political()` fixture being corrected in the same change |
| F11 | the repair loop's *denial* machinery | re-verified item by item; still correct. `origin` required/positional, `DISCLOSABLE_ORIGINS`, the visible-hole message, terminal abstention |
| F12 | `concepts` required by the wire schema but unexplained by the licence prose | `prompt/10_output_format.md:89` now names `concepts` in the licence obligation |

## RECORDED — still true, captured live

| | finding | where |
|---|---|---|
| F6 | D2 (witness at link scope) absent | `DEFERRED.md:154` names D2 as the link-scope exemplar |
| F6 | D3 (no opaque stubs) absent — failure mode #5 has no check anywhere | `STEP_stage4.md:195` (⛔ *"not addressed and must not appear to be"*), and `DECISION_bad_worked_examples.md` rejects a stage-2 check for it **by name**, with the measurement that the obvious proxy is inverted |
| F7 | Invariant 1's read-back renders the label, not the definition | `STEP_stage4.md:80` — *"`CONFORMANCE_REVIEW.md` F7 said the remedy was absent; verified"*. ⚠️ The live record **cites this file**; retiring it would need that line rewritten |
| F9 | the namespace guard is a three-name blacklist, not a type constraint | `contradiction_probe/FINDINGS.md:23` (*"a type constraint. 2 lines, mandatory"*), `STATE.md:213`, `resources/03_pipeline.md:965` |
| F13 | severity split / arm-B contradiction | the severity ruling is now in `checks.py`'s docstring **and** in `03_pipeline.md`'s typed-repair-guard section; the `DEFERRED.md` D-3 vs `STEP` §1 contradiction was resolved by D-3's withdrawal-by-name |

## OBSOLETE

* F13's three `STEP_stage2_and_repair.md` items — that file was deleted in `d3108d5`.

## ⭐ OPEN — recorded nowhere else

### F5 — `acts` is still not a declaration site, and the error message names three wrong remedies

**Reproduced today.** A module declaring `be_explicit_about_inability(I)` in `acts` and referencing
it in a rule body is rejected:

```
body references `be_explicit_about_inability` but nothing declares it. Put it in this module's
`ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about the case).
```

`schema.py:641-642` builds `known` from `ontology ∪ requires ∪ inputs` and omits `self.acts`
(which is used, separately, at `:601` only to check that `asserts` names a declared act). For an
act-typed predicate the finding is false and all three suggested remedies are wrong, so a repair
loop handed it **cannot converge** — this is what defeated the only repair in the run the review
was written against (`m0091`, `per_attempt: [1, 1]`).

⚠️ Note the F4 fix and this are the same block. Whoever fixes F5 must not re-open F4: an act is a
declaration site because `acts` names a thing the module *governs*; `concepts` is not, because it
says what a name means and never that anything derives it.

> **Draft for `phase_1/DEBUGGING_TIPS.md`, as a new section 11:**
>
> ## 11 ⛔ `acts` is not in the body-declaration set, and the message it produces is wrong
>
> `schema.py`'s D4b-level-1 check builds `known` from `ontology ∪ requires ∪ inputs`. `acts` is
> not in it. So a module that declares `be_explicit_about_inability(I)` in `acts` — correctly —
> and then references it in a rule body is told *"nothing declares it. Put it in this module's
> `ontology`, in `requires` … or in `inputs`."* All three remedies are wrong for an act, and
> following any of them corrupts the module.
>
> **The cost is not a bad message, it is non-convergence.** The finding is `error` severity, so it
> drives repair; the model can only clear it by doing something wrong; the loop exhausts. `m0091`
> was the one `unrepaired` clause of the first live run for exactly this reason, and it burned a
> paid attempt to learn nothing.
>
> ⛔ **The trap:** the neighbouring block was tightened deliberately — `concepts` was REMOVED from
> `known` because a rule resting only on concept declarations can never fire. Do not undo that
> while fixing this. An act is a declaration site because the module *governs* it and declares a
> closure over it; a concept is not, because saying what a name means never says anything derives
> it.

### F10 — a module with no logic at all still validates as `translated`

**Reproduced today.** A module with `acts: []`, `asserts: []`, `ontology: []`, `beats: []`,
`defines: []`, `closure: []` and **one** `concepts` entry validates clean, `outcome == "translated"`.
Its rendered `.lp` is five comment lines and nothing else:

```
%% clause: m0001   section:    kind:
%% acts:
%% concepts: assistant_entity/1   (glosses in the concept table, not here)
%% requires:
%% inputs:
```

Two guards leak together. `schema.py:571-575` accepts `concepts` alone as evidence that something
was translated; and `acts: []` means `governed` is empty, so the **forced** per-act closure
declaration — one of the four things open question 1's CLOSED ruling requires — is owed on nothing.
The attack is *delete the content, keep the declarations*, and it is the mirror of the
`requires`→`inputs` attack the repair guard is typed against. The `shrank` flag fires and changes
no outcome.

> **Draft for `resources/03_pipeline.md`, in the typed-repair-guard section (attack table):**
>
> ⛔ **Attack D — delete the content, keep the declarations.** A module whose only surviving field
> is `concepts` satisfies the "did you translate anything" guard, and a module with `acts: []` owes
> no closure declaration at all, because the forced closure is derived from the acts the module
> governs. Together they make a **contentless module a passing translation**: zero asserts, zero
> ontology facts, zero rules, a `.lp` containing only comments, `status: "translated"`, counted in
> the run's success line. Measured on `m0037`: attempt 1 wrote a whole rule into an `atom` slot,
> the finding was correct, and attempt 2 cleared it by deleting the entry rather than moving the
> conditions into `body`.
>
> This is the same shape as attacks A–C and belongs with them: the guard must be **typed**, not
> sized. The `shrank` flag is not the fix — it fires and sets no outcome. A translated module owes
> at least one of `asserts` / `defines` / `ontology` / `beats`, and a module that governs no act is
> a claim about the clause that should have been an abstention.

### F8a — `world` toggleability is a comment, not an operative property

`schema.py:900-905` renders a `world` fact as the line plus `% [W] toggleable`. The **ontology
block** is switchable (`#const onto = on.`); an individual `world` fact is not. Invariant 2 requires
it *"marked and toggleable"*, and `03_pipeline.md:1097` makes marked-and-toggleable the
deterministic check standing in for the `world` row of the citation checker's denominator — so half
of that check cannot run, because half of the property does not exist. `STEP_stage4.md:452` asserts
the deterministic half *"already exists in `schema.Licensed`"*; `Licensed` enforces that the
**flag** is set, which is the marking, not the switchability.

> **Draft for `DEFERRED.md`, as a new entry D-4:**
>
> ## D-4 — `world` facts are marked toggleable but are not actually switchable
>
> **Deferred 2026-08-07.** Invariant 2 requires a `world` fact to be *"marked and toggleable — a
> result resting on world knowledge is a different claim"*, and `schema.Licensed` enforces the
> mark: `licence: "world"` without `toggleable: true` is rejected, and `toggleable` on a
> non-`world` fact is rejected. **The switch does not exist.** `render_lp` emits the fact
> unconditionally with a trailing `% [W] toggleable` comment; only the whole ontology block is
> switchable, via `#const onto = on.`
>
> **What this blocks, precisely.** `03_pipeline.md`'s citation-checker table gives the `world` row
> as *"is it marked as world knowledge, and is it toggleable?"* — a deterministic check standing in
> for a human seat. Today it can only check the first half. And `DEFERRED.md` D-1's tier 3
> ("licence strength") rests on the same mechanism, with stage-0 finding F4 already showing the
> naive version wrong: *"change that one fact and the match disappears"* was false, because the
> match survived through a second independent world fact. **Toggleability needs minimal supports,
> plural** — which is an argument for building the switch once rather than per-fact.
>
> **Why deferring is safe.** Nothing stage 1 emits changes: a fact declares `world` and carries
> `toggleable: true` whether or not the renderer later gives it its own `#const`. The switch is a
> rendering decision over an existing contract.
>
> ⚠️ **What must not happen** is `STEP_stage4.md:452`'s claim being read as closing it. It says the
> deterministic marked-and-toggleable check already exists in `schema.Licensed`. `Licensed`
> enforces the *flag*. Deleting this entry on the strength of that line would retire a check that
> was never built.

### F8b — weakest-licence inheritance is computed nowhere

`03_pipeline.md:199` states it with a ⭐ (*"that is what makes 'change one asserted fact and the
match disappears' visible in the output rather than discovered later"*), and `prompt/00_task.md:31`
tells the model about it as a **note**. No propagation exists in `schema.py`, `link.py` or
`checks.py`; nothing derives a conclusion's licence from its derivation.

⚠️ This is *nearly* recorded: `STATE.md:219` lists it under "Open, in the order I would take them".
But `STATE.md:183-184` **declares itself a deletion candidate** (*"duplicates `REVIEW_QUEUE.md` and
the phase_1 README and has drifted from both"*). A finding whose only live record is in a file
marked for deletion is not recorded. It belongs in `DEFERRED.md`, next to D-1, which already depends
on it.

> **Draft — one paragraph to append to `DEFERRED.md` D-1, under "Open questions to answer when it
> returns":**
>
> - ⭐ **Weakest-licence inheritance is stated and unbuilt, and tier 3 is the thing that needs it.**
>   `03_pipeline.md` Invariant 2: *"A conclusion inherits the weakest licence in its derivation."*
>   `prompt/00_task.md` tells the model so, as a note. **Nothing computes it** — not `schema.py`,
>   not `link.py`, not `checks.py`. Tier 3 ("licence strength: proof uses only `textual` > requires
>   `assumed` > requires `world`") is a statement *about a derivation*, so it cannot be read off the
>   per-fact licences the contract collects; it has to be propagated. Note this is the same
>   propagation the citation checker's licence-dependent denominator needs, so it is one piece of
>   work serving three consumers, not an ordering feature.

### F11-caveat — `per_attempt` counts notes, so a converged clause can read as non-converging

`translate.py:2211` appends `len(found)` where `found` is the **complete** findings list.
`requires-unprovided` is a `note` and fires on every well-formed single-clause module, so a clause
whose only remaining findings are inert notes reports `per_attempt: [1, 1]` — indistinguishable
from `m0091`'s two real errors. `DEBUGGING_TIPS.md` §7 tells a *reader* to filter to errors first;
the recorded field itself still mixes the two, and `per_attempt` is what a convergence measurement
would group on.

> **Draft — one bullet for `DEBUGGING_TIPS.md` §7, appended:**
>
> ⚠️ **`per_attempt` in `run.json` is not an error count.** `repair_loop` records `len(found)` over
> the complete findings list, notes included. A clause whose only surviving findings are
> `requires-unprovided` notes — true of every correct single-clause module — reads as
> `per_attempt: [1, 1]`, byte-identical to a clause with one real error on both attempts. Any
> convergence rate computed off this field is measuring note volume. Filter by severity before
> counting, or read `surviving_findings`, which is only written on the failure path.

---

# 2 · `paper_pipeline/phase_1/ENGINEERING_REVIEW.md` (390 lines)

**Cited by nothing.** It is nonetheless the document carrying the most live, untracked defects.

## FIXED — verified

| | finding | evidence today |
|---|---|---|
| F1 | unrepaired written as `translated` | same fix as CONF F3 |
| F2 | `ProviderError` during repair aborts the whole run and loses a billed clause | `translate.py:1081-1090` — the repair call now sits inside a per-clause `except Phase1Error` that records `status="error"` and continues. Pinned by `test_repair.py:550` |
| F3 | stage 2 unreachable on a schema-valid module | same fix as CONF F2 |
| F5 | transcript first turn | same fix as CONF F1 |
| F6 | `abstained_under_repair` collapsed to `abstained` in `run.json` | `translate.py:1149-1152` writes `status=out.status` with the ruling as a comment. Pinned by `test_repair.py:567`. ⚠️ **Half-fixed — see the OPEN section** |
| F8 | `run()`'s identity guards passed at an untested call site | **Mutation-verified today.** The call site moved (`run()` now passes `corpus_ids=known_ids` into `repair_loop`, which forwards to `run_checks`). Replacing it with `corpus_ids=None` in a scratch copy **kills** `test_repair.py::test_a_live_run_WIRES_the_loop_and_records_what_it_did` and one self-test check. Fenced |
| F9 | `translate.py --self-test` not run by pytest | `test_prompt_examples.py:193 test_translate_self_test_runs_to_completion` runs it in a subprocess. Its docstring records that pytest stayed green at 294 while the self-test was dead |

## RECORDED

* **`guard.py` is RED / the five transcriptions unreviewed** — `REVIEW_QUEUE.md` §1 and
  `DEFERRED.md`'s "Re-reviewing the five newly watched transcriptions" entry, which argues the red
  state is correct and names the one thing that must not happen (`--accept --all`).
* **`run()` passes no corpus-wide concept table** — deferred in `DEFERRED.md` D-3 (level 3). ⚠️
  Partial: D-3 records the check as *incomplete*; ENG's sharper point, that the live wiring makes
  `concept-multi-gloss` **structurally incapable of firing** even though `run()` accumulates
  `_concepts` for exactly that data, is not in D-3. Verified still true: `run()` calls `repair_loop`
  without `concepts=` (`translate.py:1076-1080`), so `run_checks` falls back to the module's own
  rows. One sentence in D-3 closes it.

## ⭐ OPEN — recorded nowhere else

### F4 — the worst-case cost estimate UNDER-estimates, and the README asserts the opposite ⭐⭐

**The most serious item in this audit.** `estimate_cost` (`translate.py:780-795`) grows *input*
triangularly in `max_attempts`, but only over `len(system) + len(user)`. It never bills the
**previous completion** as input on the next call — and that completion is worth up to
`max_tokens = 16384`, roughly 12× the user block.

Recomputed today against the **shipped** config (`max_tokens: 16384`, `[0.14, 0.28]`/Mtok, system
block 33,614 chars, `m0091`'s user block 5,341 chars):

| `max_attempts` | printed "cost (worst)" | true worst case | under by |
|---|---|---|---|
| 2 | $0.013265 | $0.014196 | 7.0 % |
| **3 (shipped today)** | **$0.021943** | **$0.024734** | **12.7 %** |
| 4 | $0.031984 | $0.037566 | 17.5 % |
| 5 | $0.043389 | $0.052692 | 21.4 % |

**It is worse than when the review was written**, because `config.json` now ships
`max_attempts: 3` rather than 2.

⛔ **And it is now asserted as safe in two places.** `config.json:79` — *"Deliberately the full
max_tokens, i.e. the worst case… Overstating an estimate is survivable; understating is how a hard
cap gets passed."* `README.md:159` — *"Cost is estimated worst-case… and triangular in the attempt
count because each repair turn resends the transcript."* The transcript that gets resent contains
the **prior completions**, which is the term that is missing. A reader checking the estimate against
the README is told the error cannot exist.

**Fix:** add `(k-1) * max_tokens` to the input term per attempt `k`. One line.

> **Draft for `phase_1/DEBUGGING_TIPS.md`, as a new section 12:**
>
> ## 12 ⛔ The cost estimate is on the wrong side of its own stated rule
>
> `estimate_cost` grows the *input* term triangularly in `max_attempts` — but only over
> `len(system) + len(user)`. Each repair turn also resends **every prior completion**, worth up to
> `max_tokens` (16,384 — about 12× the user block), and that term is absent. At the shipped
> `max_attempts: 3` the printed worst case is **12.7 % below** the true worst case; at 5 it is
> 21.4 % below.
>
> ⛔ **The trap is that two documents tell you this cannot happen.** `config.json`'s comment says
> *"Overstating an estimate is survivable; understating is how a hard cap gets passed"*, and
> `README.md` explains the triangular growth as *"because each repair turn resends the
> transcript"* — which is the exact term that is missing. The estimate is described by its own
> rationale as conservative while being anti-conservative.
>
> ⚠️ Two errors point in opposite directions and partly mask each other: the estimate
> **over**-charges the full user block on every repair turn, while the loop re-sends only an error
> log. Do not net them off. The gate is small in absolute terms ($0.25/run) so nothing has burned
> yet, but the direction is the one the design says must never be wrong, and this is the project
> with a hard $8.50 ledger.
>
> **The check to run:** price a repair sequence by hand — attempt 1 is `system + user`; attempt *k*
> is `system + user + (k−1)×max_tokens` of prior completions — and diff it against the printed
> number. A test asserting `three > one * 2.5` cannot see this: with `max_tokens=1000` and the
> strings `"sys"`/`"user"`, the **output** term alone gives exactly 3×, so the assertion passes with
> the input term contributing nothing measurable.

### F7 — the `clingo` guard's return-code half is unpinned, and it is the half that catches "clingo never ran" ⭐⭐

**Mutation-verified today.** `link.py:745` — `if errs or r.returncode not in CLINGO_OK_RC:`.
Mutating it to `if errs:` in a scratch copy of the tree:

```
pytest walkthrough/ -q          -> 301 passed   (mutant survives every test)
pytest .../test_link.py -q      ->  34 passed   (includes link.py --self-test in-process)
```

And it matters, reproduced today with `clingo` absent from the interpreter:

```python
link.PY = '/usr/bin/python3'
link._check_clingo(['m0255.lp'])
# stdout+stderr : "…/python3: No module named clingo"
# CLINGO_ERR.findall(blob) -> []      <-- the text half sees NOTHING
# the finding is raised only because returncode == 1
```

So under the mutant, a link check over a program that was **never compiled** returns clean and every
test stays green. That is precisely the "a pass indistinguishable from a did-not-run" shape that
`STATE.md:230`, `README.md:89` and `DEBUGGING_TIPS.md` §8 all name as the project's recurring
failure — sitting unpinned inside the function whose docstring exists to prevent it. `link.py` is
otherwise well pinned: this was the single survivor of a 7-mutation pass then, and it is still the
survivor now.

> **Draft for `phase_1/DEBUGGING_TIPS.md`, appended to §8 ("A check that cannot run must not exit
> like a check that passed"):**
>
> ⛔ **A live instance of exactly this, still unpinned: `link._check_clingo`.** The guard is
> `if errs or r.returncode not in CLINGO_OK_RC:` — two independent detectors, deliberately
> redundant. Only the first is tested. Mutating it to `if errs:` **survives all 352 tests and
> `link.py --self-test`**. And the redundancy is not decorative: with `clingo` missing from the
> interpreter the output is *"No module named clingo"*, `CLINGO_ERR` matches **zero** of it, and the
> finding is raised by the return code alone. Under the mutant, a link check over a program that was
> never compiled reports clean.
>
> ⇒ **When a guard is deliberately redundant, each arm needs its own RED test.** A test that only
> exercises the arm that fires most often converts the redundancy into decoration, and the arm that
> is left is the one covering the environment failure — which is the one you cannot reproduce by
> writing a bad program.

### F10-residue — `translate.py` still tells every reader, and every run, that nothing is validated

`README.md` was rewritten and its six false rows are gone (verified: no "16 checks", no
`no_code_block`, no "deliberately not built yet", no "instruction-following plus a regex"; the
run-directory listing now includes `prompt_system.txt`, `concepts.json`, `<id>.transcript.json`).
Three residues are **in the code** and are now flatly false:

* `translate.py:7` — *"Stage 1 has never been run."*
* `translate.py:10-14` — *"⛔ IT VALIDATES NOTHING ABOUT THE TRANSLATION. It does not compile the
  ASP, does not link it, does not check the headers… Stage 2 is those checks and it is deliberately
  not built yet."*
* `translate.py:1180` — printed on **every** run: `⛔ NOTHING here has been validated. No compile,
  no link, no read-back.`

Since the F2 fix, every attempt goes through `checks.run_checks` → `link.collect`: clingo compile,
unresolved names, rule shape, closure, `beats` acyclicity, concept table. The banner is the last
line a human reads after a run, and it says the opposite of what happened.

⚠️ **This is not cosmetic.** It is the same class as `README.md`'s six rows, and the reason those
mattered: a reader who believes the banner will not look at a finding, and an agent reading the
module docstring will re-derive stage 2 as unbuilt. `translate.py` is not a watched file, so nothing
will catch it.

> **Draft — for `phase_1/README.md`, appended to "What a run does":**
>
> ⚠️ **`translate.py`'s module docstring and its end-of-run banner are STALE and say the opposite of
> what the harness does.** Both still date from before stage 2 existed: the docstring opens *"Stage
> 1 has never been run"* and *"⛔ IT VALIDATES NOTHING ABOUT THE TRANSLATION… Stage 2 is those
> checks and it is deliberately not built yet"*, and every run ends by printing *"⛔ NOTHING here
> has been validated. No compile, no link, no read-back."* Since stage 2 became the unconditional
> gate, every attempt is compiled by clingo, link-checked, rule-shape checked and cycle checked
> before anything is written. Believe this file and the code, not those three strings, until they
> are corrected.

### ⭐ NEW (found in this audit, tracked nowhere) — `abstained_under_repair` is counted as *translated* in the run summary

ENG F6 was fixed in `run.json` and **not** in the summary arithmetic.

`translate.py:1177-1181`:

```python
n_ab = sum(1 for r in results if r.get("status") == "abstained")
print(f"\n{len(results) - failures - n_ab} translated, {n_ab} abstained, {failures} failed.")
```

`abstained_under_repair` is on the success branch (`:1115` admits it, so `failures` is not
incremented) and is not `"abstained"`, so it falls into **`len(results) - failures - n_ab`** — the
**translated** count. A clause the model refused after being told twice it was wrong is printed as a
successful translation.

This is the same defect ENG F6 identified, one line further down, and the test that closed F6
(`test_abstained_UNDER_REPAIR_survives_into_the_record`) asserts only on `run.json`'s `status`
field — it never reads the summary. `README.md:192` compounds it by listing the statuses as
`translated · abstained · unrepaired · error`, omitting `abstained_under_repair` entirely.

The stakes are the ones `checks.py`'s own docstring states: *"a model can abstain its way out of the
hard clauses while the rate, which is the reliability signal the whole mechanism exists for, reads
as though it had judged them."* Here it reads **better** than that — as though it had translated
them.

> **Draft — for `phase_1/DEBUGGING_TIPS.md` §2 ("A metric can read 0.0000 when it measured
> NOTHING"), appended:**
>
> ⛔ **A live instance: the run summary counts `abstained_under_repair` as TRANSLATED.**
> `run()` computes `n_ab` by matching `status == "abstained"` exactly, then prints
> `len(results) - failures - n_ab` as the translated count. `abstained_under_repair` matches
> neither the abstained test nor the failure branch, so it lands in "translated". A clause the model
> declined after two failed attempts is reported as a success, in the one line a human reads.
>
> ⇒ **When a status set grows, every place that partitions on it has to grow with it.** The record
> was fixed (`run.json` carries the distinction, and a test pins it); the *arithmetic over* the
> record was not, and the test asserts on the field rather than on the summary. `README.md`'s
> status list is missing the value too. Grep for every consumer of a status before adding one, and
> pin the derived counts, not just the stored field.

### Smaller OPEN items, all verified still true

| | item | evidence |
|---|---|---|
| a | `cross_references.max_clauses_per_target` is observed by no test | only occurrence outside config is `translate.py:224`. It changes what is sent and what is billed |
| b | the `CorpusError` message misdiagnoses the section+kind case | `translate.py:180` still blames `kinds` when the cause is the intersection with the section filter. Untested |
| c | `resolve_provider` permanently prepends `semi-formal-experiment/` to `sys.path` | `translate.py:449`, ahead of `phase_1/`, and `semi-formal-experiment/translate.py` exists. Latent, one filename away |
| d | `self_test`'s `_StubClient` has no `complete_messages` | `translate.py:1666-1677`. **More consequential now than when written**: `repair_loop` is on the unconditional path, so any self-test stub that ever returns a repairable failure dies with `AttributeError` rather than a named refusal |
| e | three-way disagreement on the repair default | `translate.py:947` falls back to **1**, `repair_loop`'s signature default is **3**, `config.json` ships **3**. The severe half is fixed (max_attempts=1 no longer disables stage 2 — `repair_loop` runs `look()` once regardless), but the defaults still disagree |

> **Draft — for `phase_1/README.md`, as a short "Known unpinned edges" subsection:**
>
> ## Known unpinned edges
>
> These are true today, cheap, and recorded so nobody rediscovers them:
>
> - **`cross_references.max_clauses_per_target` is observed by no test.** It changes what is sent
>   and what is billed; removing it from `translate.py:224` leaves the suite green.
> - **`CorpusError("selection matched no clauses (kinds=…)")` misdiagnoses.** After the section
>   branch has already raised, the only way to reach it is a section+kind intersection — so it
>   blames `kinds` for an intersection failure. Untested.
> - **`resolve_provider` prepends `semi-formal-experiment/` to `sys.path` permanently**, ahead of
>   `phase_1/`, and that directory contains its own `translate.py`. Nothing imports `translate`
>   after that today; it is one filename away from a very confusing bug.
> - **`self_test`'s `_StubClient` has no `complete_messages`.** Stage 2 is now unconditional, so a
>   stub that ever returns a repairable failure will die with `AttributeError` instead of a named
>   refusal.
> - **The repair default disagrees three ways:** `run()` falls back to 1, `repair_loop`'s signature
>   says 3, `config.json` ships 3.

---

# 3 · `model/TRANSCRIPTION_REVIEW.md` (261 lines)

## FIXED — verified

| | finding | evidence today |
|---|---|---|
| A | the design still specified `provides` | `03_pipeline.md:620-623` — *"⛔ `provides` was REMOVED… This paragraph supersedes the `provides` mentions in the stage-1 diagram above"*, with the grounds the review had to find in a code comment |
| B | the stage-1 relation vocabulary was not licensed by the source of truth — the partial decline | `03_pipeline.md:590-618`, *"⭐ The relation vocabulary, written here 2026-08-07"*, opening *"⛔ It was missing from this document while five files implemented it… a clean reviewer could not license `asserts/3`, `defines/3` or the status set from the source of truth, and correctly declined to try."* The four relations, the closed status set, and the `concepts`/`ontology` split are all now in the design. **This was the review's headline finding and its "what I would re-check first"; it is closed** |
| C | `30_failure_modes.md` instructed an output the format cannot carry | line 39 now reads *"you can **partly** prevent"* and adds *"(There is no field for an integrity constraint, so you cannot state the impossibility directly — say it in `claims` instead.)"* |
| D | two of the design's five bad worked examples were dropped | **RULED and closed** by `phase_1/DECISION_bad_worked_examples.md`. #4 "imports a name without its content" was **restored** as bad example #6, on a measurement (10 of 133 concepts have a gloss adding zero words beyond the predicate name); #2 "translates in isolation" is a **recorded deliberate drop**, because the user block now supplies every cross-referenced clause text (77/77 anchored clauses), with an explicit reopen condition. A stage-2 check for #4 is rejected **by name**, twice |
| F | `concepts` missing from `10_output_format.md`'s field table | the field table was replaced by *"Each field is described in the schema itself"* (single source), and `:89` names `concepts` in the licence obligation |
| H | the Part 3 diagram's `FIX` node showed no ORIGIN filter | `03_pipeline.md:246` — the node now reads *"⭐ Only STAGE-2 findings may enter it; stage 3 and 4 findings carry an answer key and are filtered by their ORIGIN"*. This was the review's highest-cost internal contradiction |
| J | `phase_1/README.md`'s conformance table had three false rows | the table is gone; README rewritten |

## RECORDED

* **E — no `world`-licensed fact is demonstrated anywhere in the prompt set.** Verified still true
  (`grep '"world"' prompt/*.md` → nothing). Recorded twice, and well: `03_pipeline.md` Invariant 2's
  *"⚠️ Not yet acted on in the prompt… it is not a documentation edit, and it must not be slipped in
  as one"*, and `REVIEW_QUEUE.md` §2.1's identical follow-up note.
* **G — Invariant 2's fourth licence class.** The design half is recorded and sharpened
  (`03_pipeline.md:190-196`: *"⚠️ The `world` ruling above does not touch this gap… Both remain open
  together"*). Only the review's cheaper alternative — one line in `schema.py` scoping "Three
  licences" to stage 1 — is undone (`schema.py:154` still says *"Three licences"* flatly). Minor.
* **I5 — the concept dictionary is absent from the prompt (arm B by construction).**
  `DEFERRED.md` D-3 and `STATE.md` NEW-6, with the arm-B commitment withdrawn by name in D-3.

## ⭐ OPEN

### H-residue — four self-contradictions still live in `03_pipeline.md`

Shared with `REVIEW_FINDINGS.md` §4; drafted once, below, in §4's entry. Verified today:

* **16 vs 17 failure modes.** `03_pipeline.md:232` — *"and the 16 error cases"*; `:394` — *"the 17
  known failure modes"*; Part 1's table has 17 and `30_failure_modes.md` reproduces all seventeen.
* **Two different things are stage 6.** `:806` `### 6 — Divergence`; `:830` `### 5 and 6 — Why
  normalising and parameterising are different operations`. The diagram numbers PARAMETERISE 6 and
  leaves DIV unnumbered.
* **"9 and 10" contains 9 and 11.** Heading at `:860`; body ten lines down opens *"**11 — Translate
  twice, enumerate the disagreement.**"*
* **Prose stage numbers contradict the diagram.** `:1052` *"Stage 7's merge"* — the merge is
  diagram stage 5 (NORMALISE); diagram 7 is EXPAND (`:270`). `:1164` *"visible only at stage 9"* —
  that is LINK, diagram stage 8 (`:271`); diagram 9 is MUTATION (`:277`). `:1061` refers to *"seat
  5c"* where the seats are 4a–4d.

### H-residue — the unresolved inline reviewer query is still embedded in the design

`03_pipeline.md:437`, inside a table cell in Part 4 §1's GIVEN list:

> *"<√Are you confidence the document's own mardown anchors are sufficient to give every cross
> reference accurately? I would expect to need a model here to find all of the references but I am
> happy if I am wrong. For example, if a section references some rules defined elsewhere, how are
> these provided?>"*

It is **partly answered** and the answer is not next to it: `DECISION_bad_worked_examples.md`
measured that only **13 % of clauses carry a resolvable anchor**, and used that to justify dropping
a bad worked example — while noting *"if a clause depends on another without an anchor, the failure
is still reachable and nothing supplies the text."* The design cell still asserts the anchors *"give
this list mechanically"*, unqualified, and it is the source of truth.

> **Draft — replacement for the `03_pipeline.md:437` table cell:**
>
> | the text of every clause this one cross-references | ⭐ a clause that modifies rules defined
> elsewhere cannot be translated in isolation. The document's own markdown anchors give this list
> mechanically — ⚠️ **for the 13 % of clauses that carry one.** `[RAN]` 77 clauses of 593 have a
> resolvable anchor and all 77 receive the referenced text; the rest are supplied nothing. Finding
> the unanchored dependencies is an open problem, and a clause that depends on another without an
> anchor still reaches failure mode #2 with nothing to prevent it. Recorded with its measurement in
> `phase_1/DECISION_bad_worked_examples.md`, which drops the "translates in isolation" worked
> example on the strength of the mechanism existing — not of the mode being impossible. |

### I1 / I4 — two prompt-set drifts still live

* **I1** — `00_task.md:35-36`: *"**A rule is not a fact.** … Licences are for the facts your module
  asserts."* But `10_output_format.md:89` requires a licence on `asserts` and `beats`, both of which
  carry a `body` — i.e. they *are* rules, and the worked example's `beats` entry is a rule with
  `licence: textual`. `00_task.md` is faithful to the design's dataclass sketch and inconsistent
  with its own sibling files, which is what the model actually reads.
* **I4** — `00_task.md` still never states that cross-referenced clause texts **will be** supplied.
  Rule 2 (`:48`) hedges: *"If you were shown the cross-referenced text, you may cite it."* The
  design makes this one of four GIVEN items and calls it load-bearing.

⚠️ Both are prompt edits, so under the standing rule they need a held-out measurement, not a
documentation pass. That is exactly why they need a live home rather than a review document.

> **Draft — for `REVIEW_QUEUE.md` §2, as a new decision item:**
>
> ### 2.3 Two prompt-set drifts a transcription review found, still open
>
> Both are edits to watched files, so neither is a documentation fix: they need a held-out
> measurement and a review, like any other prompt change.
>
> 1. **`00_task.md:35` says "a rule is not a fact… licences are for the facts your module
>    asserts", and the schema disagrees.** `10_output_format.md:89` and `schema.Licensed` require a
>    licence on `asserts` and `beats`, both of which carry a `body` — they are rules. The worked
>    example's `beats` entry is a rule carrying `licence: textual`. `00_task.md` is faithful to the
>    design's dataclass sketch and inconsistent with the three files beside it, which is what the
>    model reads together.
> 2. **`00_task.md` never states that cross-referenced clause texts will be supplied.** Rule 2
>    hedges — *"If you were shown the cross-referenced text, you may cite it"* — while the design
>    makes it one of four GIVEN items and calls it load-bearing. A model told it *might* be shown a
>    dependency has a licence to guess when it is.

## Recommendation

**KEEP for now — but this one is genuinely close.** Six of its nine findings are fixed, including
both it called highest-cost, and its central decline (B) is explicitly closed in the source of
truth. Its three open items are: the design self-contradictions (shared with `REVIEW_FINDINGS.md`
§4, so retiring both needs the fix once), the inline reviewer query, and the two prompt drifts.

⇒ **If the three drafted paragraphs above land — `REVIEW_QUEUE.md` §2.3, the `03_pipeline.md:437`
cell, and §4's stage-numbering paragraph — this document is retirable**, with one citation to
rewrite (`REVIEW_QUEUE.md:27`, which needs updating regardless because it is stale on finding D).

---

# 4 · `model/REVIEW_FINDINGS.md` (604 lines)

## OBSOLETE — the great majority

`model/RETIRED.md` records that `pipeline.lp`, `rules.lp`, `check.py`, `accepted.json` and the
findings half of `guard.py` were **deleted** on 2026-08-07. Confirmed: `ls walkthrough/model/` shows
only `guard.py`, `watch.json`, `reviewed.json`, `hooks/`, `test_model.py` and the three markdown
files. So:

* **§1** — all nine invented facts (`catches(normalise, p9)`, `check(coverage, s2, …)`, the rest):
  obsolete, about deleted facts.
* **§2** — all ten omissions: obsolete for the same reason. They describe what the model *failed to
  record*; there is no model.
* **§3** — accounting: obsolete.
* **§5.1–5.4** — the rules that would have fired: obsolete as work items. Their *lesson* is carried
  in `RETIRED.md`'s "why it went" and "what would justify bringing it back".
* **§6** — "is extending the model to `phase_1/` worth doing": obsolete as a decision (the model
  itself is gone), and its reasoning is superseded by `RETIRED.md`.
* **§7's code defect** in `check.py`'s `CLASS` dict: obsolete, file deleted.

## FIXED

* **§5.5's second half** — *"the guard protects the model from design drift; it does not protect
  **derived artifacts**"*, with the recommendation to add `prompt/*.md` and `schema.py` to
  `WATCHED`. **Done**: `watch.json` carries them, `RETIRED.md:54-57` calls the widening *"the actual
  finding"*, and `REVIEW_QUEUE.md` §1 lists all six watched files.

## ⭐ OPEN — §4, the seven contradictions inside `03_pipeline.md`

`03_pipeline.md` is live, is the declared source of truth for `walkthrough/`, and **four of §4's
seven items reproduce verbatim today** (enumerated under TRANSCRIPTION_REVIEW's H-residue above,
with current line numbers). Two more are live:

* **§4.7** — the unresolved inline reviewer query at `:437`, drafted above.
* **Part 6's `⭐ Stage 1 has never been run`** (`:1139`). Stage 1 has run many times: three clauses
  on 2026-08-07, then 36 first attempts × 2 arms in `eval_arms/`, plus every worked-example run.
  ⚠️ The identical stale sentence is also `translate.py:7`.

⚠️ **These are the only surviving reason to keep 604 lines**, and they are not recorded anywhere
else. `STATE.md` does not carry them; `REVIEW_QUEUE.md` does not; `DEBUGGING_TIPS.md` does not.

> **Draft — a new subsection for `resources/03_pipeline.md`, placed near the top of Part 1 so it is
> read before the diagrams:**
>
> ### ⚠️ Known internal inconsistencies in this document, 2026-08-07
>
> Recorded rather than silently carried, because two reviews independently stalled on them and a
> third could not check `check(C, Stage, _)` against any single authority.
>
> **The stage numbers in the prose do not match the diagram, and the diagram is right.** Diagram:
> 5 NORMALISE · 6 PARAMETERISE · 7 EXPAND · 8 LINK · 9 MUTATION. Prose that disagrees:
> *"Stage 7's merge"* (the merge is stage 5); *"visible only at stage 9"* for corpus-level
> correctness (that is LINK, stage 8); *"seat 5c"* where the seats are 4a–4d; a heading `### 6 —
> Divergence` where the diagram leaves DIVERGENCE unnumbered and gives 6 to PARAMETERISE; a heading
> `### 9 and 10 — Testing the tests` whose body opens *"**11 — Translate twice**"*.
>
> **The failure-mode count is given as 16 in one place and 17 in every other.** Part 3's diagram
> node reads *"and the 16 error cases"*; the stage-1 diagram says *"the 17 known failure modes"*;
> Part 1's table has seventeen rows and `phase_1/prompt/30_failure_modes.md` transcribes all
> seventeen. **#17 was added later and that one node was not updated.**
>
> **Part 6's *"⭐ Stage 1 has never been run"* is stale.** It has run: three clauses on 2026-08-07,
> then 36 first attempts across two prompt arms in `phase_1/eval_arms/`. The same sentence survives
> in `phase_1/translate.py`'s module docstring.
>
> ⇒ **Until these are corrected, do not derive anything from a stage number stated in prose.** Read
> the diagram, and cite the stage by NAME. A reviewer who cannot resolve "stage 2" against a single
> authority cannot check whether a check is at the right stage, which is how a coverage check ended
> up asserted at a stage that could not build its inputs.

## Recommendation

⛔ **KEEP, and not only for §4.** `RETIRED.md` cites this file **by name, twice**, and the second
citation is a condition on future work: *"⚠️ Do not revive it by writing `pipeline.lp` back from
memory. If items 1–3 hold, start from `REVIEW_FINDINGS.md` — it records what the model got wrong and
how, which is worth more than the model was."* Deleting it would leave `RETIRED.md` pointing at a
missing file and would remove the only account of *how* an unmaintained assertion model manufactures
confidence — which is the argument that keeps it retired.

⇒ If the size is the problem, the honest edit is **not** deletion but a banner at the top saying
what §§1–3 and 5–8 are (a post-mortem of deleted code, kept as the revival precondition) and that §4
is the only part describing something that still exists. That is a five-line change and it costs
nothing that matters.

---

# 5 · ⭐ Still broken, and nobody is tracking it

Ranked by what will produce a wrong artifact or a wrong number soonest. Everything here was
**reproduced during this audit**, not read off a review.

| | what | why it bites | where it is recorded today |
|---|---|---|---|
| **1** | **The cost estimate under-states the worst case by 12.7 % at the shipped `max_attempts: 3`** — the prior completion (up to `max_tokens`, ~12× the user block) is never billed as input on the next attempt | This is the one direction `config.json`'s own comment says must never be wrong, on a project with a hard $8.50 ceiling. **`README.md:159` and `config.json:79` both assert the estimate is conservative**, so a reader checking it is told the error cannot exist | **nowhere** |
| **2** | **`link._check_clingo`'s return-code arm is unpinned.** Mutating `if errs or r.returncode not in CLINGO_OK_RC:` → `if errs:` survives all 352 tests and `link.py --self-test` | With `clingo` absent the text arm matches **zero** output; the finding comes from the return code alone. Under the mutant a program that was never compiled reports clean — the "pass indistinguishable from did-not-run" shape this repo names as its recurring failure, inside the function written to prevent it | **nowhere** |
| **3** | **`abstained_under_repair` is counted as *translated* in the run summary** (`translate.py:1177`) | A clause the model refused after two failed attempts is printed as a success, in the one line a human reads. The test that fixed the same defect one line up asserts on `run.json`, never on the summary. `README.md:192`'s status list omits the value too | **nowhere** |
| **4** | **`acts` is not in the body-declaration set** (`schema.py:641`), so an act used in a rule body raises a false finding naming three wrong remedies | The finding is `error` severity, so it drives repair, and no faithful repair clears it. This is why `m0091` was the first live run's only `unrepaired` clause | CONFORMANCE_REVIEW F5 only |
| **5** | **A module with no logic validates as `translated`** — `concepts` alone satisfies the content guard and `acts: []` owes no closure | Attack "delete the content, keep the declarations", against a repair guard explicitly designed to be typed rather than sized. `shrank` fires and changes nothing | CONFORMANCE_REVIEW F10 only |
| **6** | **`translate.py` tells every run that nothing was validated** (`:7`, `:10-14`, `:1180`) | Stage 2 has run on every attempt since the F2 fix. A reader who believes the banner will not look at a finding; an agent reading the docstring will re-derive stage 2 as unbuilt | ENGINEERING_REVIEW F10 only |
| **7** | **`world` toggleability is a comment, not a switch** (`schema.py:904`) | `03_pipeline.md:1097` makes marked-**and**-toggleable the deterministic check standing in for a human seat; only the marking half can run. `STEP_stage4.md:452` claims it *"already exists in `schema.Licensed`"* — `Licensed` enforces the flag | CONFORMANCE_REVIEW F8 only |
| **8** | **Weakest-licence inheritance is stated in the design and the prompt, and computed nowhere** | It is the mechanism behind *"change one asserted fact and the match disappears"*, and `DEFERRED.md` D-1's tier 3 depends on it | `STATE.md:219` — **a file that declares itself a deletion candidate** |
| **9** | **`per_attempt` counts notes**, so a converged clause reads as non-converging | `requires-unprovided` fires on every correct single-clause module. Any convergence rate off this field measures note volume | partially, `DEBUGGING_TIPS.md` §7 (reader-side only) |
| **10** | **`03_pipeline.md` contradicts itself on stage numbers, on 16-vs-17 failure modes, and still carries an unresolved inline reviewer query at `:437`; Part 6 still says stage 1 has never been run** | It is the declared source of truth. Two reviews stalled on it; one had to decline a whole section | REVIEW_FINDINGS §4 + TRANSCRIPTION_REVIEW H only |
| **11** | **Five smaller unpinned edges** — `max_clauses_per_target` observed by nothing; the `CorpusError` message misdiagnosing section+kind; `sys.path.insert` shadowing `phase_1/` with `semi-formal-experiment/`; `_StubClient` lacking `complete_messages` on a now-unconditional repair path; the repair default disagreeing three ways (1 / 3 / 3) | individually small; (d) is the one that will bite, because stage 2 is no longer optional | ENGINEERING_REVIEW "Lesser items" only |
| **12** | **`REVIEW_QUEUE.md` is stale** — §1 line 27 and §2.2 both still present the bad-worked-example item as open and still name the hollow stub as dropped | It was ruled and closed in `DECISION_bad_worked_examples.md`; the hollow stub is live as bad example #6. `REVIEW_QUEUE.md` is the document Matt reads to decide what to do next | it *is* the live record, and it is wrong |

## ⚠️ One thing to be careful about

Items 4 and 5 both live in `schema.py`'s coherence block, immediately beside the **F4 fix** —
`concepts` was deliberately REMOVED from the declaration set because a rule resting only on concept
declarations can never fire, and `fixtures.py:14-19` records a wrong test fixture that was corrected
in the same change. Fixing F5 by loosening `known` is how F4 comes back. The distinction to preserve:
**an act is a declaration site because the module governs it and owes a closure over it; a concept is
not, because saying what a name means never says that anything derives it.**

---

# 6 · ⭐ LANDED 2026-08-07 (later session) — what happened to each open finding

The drafted paragraphs above are kept **as drafts, verbatim**, because two of them were landed with
corrections and the diff between draft and landed text is the useful record. Every finding was
**re-verified against the code before it was written down**; nothing here was transcribed on the
audit's authority.

| finding | disposition |
|---|---|
| ENG **F7** — `_check_clingo`'s return-code arm unpinned | ⭐ **FIXED, not just recorded.** Two tests added (`test_link.py::test_d4_clingo_that_NEVER_RAN_is_a_failure_even_with_no_error_text` + an `if True:` guard). RED-verified: the `if errs:` mutant fails the first, the `if True:` mutant fails the second. Lesson landed in `DEBUGGING_TIPS.md` §8 |
| ENG **F4** — the cost estimate under-states | ⭐ **FIXED.** 12.7 % at `max_attempts: 3` re-derived independently and matches the table above exactly (7.0 / 12.7 / 17.5 / 21.4 %). `estimate_cost` now bills `(k−1) × max_tokens` of carried-forward completion on attempt *k*. Lesson landed as `DEBUGGING_TIPS.md` **§14** (not §12 — the file had grown), and `README.md`'s false paragraph corrected in place |
| **NEW** — `abstained_under_repair` counted as translated | ⭐ **FIXED.** The summary now counts `translated` by name, prints both abstention kinds, and warns on any status it does not partition on. Pinned on the **printed line** (`test_cost_and_summary.py`). `README.md`'s status list corrected. Lesson landed in `DEBUGGING_TIPS.md` §2 |
| CONF **F11-caveat** — `per_attempt` counts notes | landed in `DEBUGGING_TIPS.md` §7, as drafted. Re-verified |
| CONF **F5** — `acts` not a declaration site | landed as `DEBUGGING_TIPS.md` **§13**. ⚠️ Reproduced, and the audit's recipe is incomplete: it takes four rounds with the validator, each intermediate failure a *different correct* error. The working reproduction is now in the tip |
| CONF **F8a** — `world` toggleability | landed as `DEFERRED.md` **D-4**, as drafted. Re-verified (`schema.py:910` comment; `:972-973` is the only real switch) |
| CONF **F8b** — weakest-licence inheritance | landed as a bullet on `DEFERRED.md` D-1, as drafted. Re-verified: the only two occurrences of the word are the two statements of intent |
| ENG **RECORDED (partial)** — `concept-multi-gloss` cannot fire | one sentence added to `DEFERRED.md` D-3, as the audit recommended. Re-verified |
| ENG **F10-residue** — `translate.py`'s stale docstring/banner | landed in `phase_1/README.md`, as drafted, with current line numbers (`:7`, `:10-14`, `:1225`). ⚠️ **The strings themselves were NOT corrected** — deliberately out of scope; the note is the tracking, and correcting the code is still owed |
| ENG **smaller items a–e** | landed as `phase_1/README.md` "Known unpinned edges". **All five re-verified individually** and all five still true |
| TRANS **I1 / I4** — two prompt drifts | landed as `REVIEW_QUEUE.md` §2.3, as drafted. Both re-verified |
| REVIEW_FINDINGS **§4** + TRANS **H-residue** (stage numbers, 16-vs-17, `:437`, Part 6) and CONF **F10** (Attack D) | ⛔ **NOT LANDED — destination is `resources/03_pipeline.md`, which is watched with another change in flight.** Parked in `REVIEW_QUEUE.md` **§8**, in one clearly-marked section, for a single edit. All four re-verified with current line numbers |
| **§5 item 12** — `REVIEW_QUEUE.md` is stale | fixed: §1's citation and §2.2 both rewritten |

## ⚠️ Two things this audit got wrong, corrected on landing

1. **The bad-worked-example item is closed differently than recorded.** This audit says bad example
   #6 was *restored*. It was restored, then **measured twice and REMOVED again** — see
   `DECISION_bad_worked_examples.md`'s **AMENDMENT**. The result is a **null on a weak instrument**
   (n = 6, one model, deltas inside the noise band), explicitly **not** a blocklist, and the failure
   mode is still real. `REVIEW_QUEUE.md` §2.2 now carries all three steps, because carrying only the
   middle one is how the queue got stale in the first place.
2. **The drafts' section numbers were already taken.** "new section 11" / "new section 12" for
   `DEBUGGING_TIPS.md` collide with the existing §11 and §12; they landed as §13 and §14. A draft
   that pins a position in a live file is the same class of defect as pinning an exact count.

Also corrected: F10's contentless module must carry a **non-empty `claims`** (validation raises
otherwise), so its `.lp` is comments *plus a CLAIMS block asserting things the logic does not say* —
worse than the review's version, not better.

**Suite after landing: 359 passed** (352 before + 7 new). No test was weakened, deleted or xfailed.
No `guard.py --accept`, no `--live`, no spend, no push.

---

## What this audit did not check

* Whether the drafted paragraphs are correct *as design* — they restate verified findings; the
  rulings are Matt's.
* `eval.py`, `eval_arms/`, `STEP_stage3.md`, `STEP_stage4.md`, `test_probe.py`,
  `DECISION_stage3_build.md` and `model/hooks/` were **read only**, per the brief.
* The `--live` behaviour of anything. No API call was made and no money was spent.
