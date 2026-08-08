# What needs your review before this commits

Written 2026-08-07. Ordered by what blocks what.

---

## 1 ⛔ MECHANICALLY BLOCKING THE COMMIT

The pre-commit hook is installed and `walkthrough/model/guard.py` is red. It blocks any commit
touching a watched file while **any** watched file is unreviewed.

    semi-formal-experiment/.venv/bin/python walkthrough/model/guard.py

**Six watched files. One accepted, five never reviewed.**

| file | state |
|---|---|
| `resources/03_pipeline.md` | ⚠️ **stale again** — you accepted it, then I and an agent both edited it |
| `phase_1/prompt/00_task.md` | never reviewed |
| `phase_1/prompt/10_output_format.md` | never reviewed |
| `phase_1/prompt/20_worked_example.md` | never reviewed |
| `phase_1/prompt/30_failure_modes.md` | never reviewed |
| `phase_1/schema.py` | never reviewed |

Accepting is per file: `guard.py --accept <path>`. There is deliberately no accept-all.

⚠️ **A clean review of the five already ran** (`model/TRANSCRIPTION_REVIEW.md`). Re-audited
2026-08-07 (`REVIEW_DOC_AUDIT.md`): six of its nine findings are fixed, including both it called
highest-cost, and its central decline is explicitly closed in the design. **§2.1 and §2.2 below are
both now RULED and closed.** What is still open from it is **§2.3** — two prompt-set drifts — plus
the design's own internal contradictions, collected in §8. Accepting the five now would certify
files a review has found drifted and nobody has re-read.

⚠️ `resources/03_pipeline.md` and `phase_1/schema.py` were edited again on 2026-08-07 (the §2.1
ruling, and the field-documentation move out of `10_output_format.md`). All three of those files
need re-reading before `--accept`.

---

## 2 DECISIONS ONLY YOU CAN MAKE

### 2.1 ✅ CLOSED 2026-08-07 — Does stage 1 demonstrate a `world`-licensed fact?

⭐ **RULED (Matt): option (a) — find and use a real document-side `world` fact. One was found:
`illegal/1`, exemplified by `m0232`.** Seven clauses depend on it (`m0209` · `m0232` · `m0253` ·
`m0270` · `m0271` · `m0524` · `m0586`) and **zero clauses define its extension**. It is not
`textual` (nothing defines it), not `assumed` (a criminal code cannot be inferred from a
behavioural spec), not behaviour-side (the word is in the clause's own text), and genuinely
toggleable (change jurisdiction, change verdict).

⛔ **Rejected by name:** (i) *"record that `world` may have no document-side instances and stop
demonstrating it"* — an instance exists and seven clauses depend on it; (ii) *"drop `world` from
the contract"* — same ground, plus it would foreclose the case before stages 3/4 have run.

⛔ **A claim written here was wrong and is corrected in the design.** The zeros below are real —
31 textual / 8 assumed / 0 world across 18 hand-encoded clauses, and `world_fact_rate` 0.000 over
72 model attempts — but they measure **what translators emitted**, not **what the corpus
requires**. Those are different questions and this entry conflated them. A single-clause translator
reads *illegal* as ordinary vocabulary, so it will systematically **under-produce** `world`
licences; the zero is a fact about the translator's field of view, not about the class.

⚠️ The design's old exemplar, `m0255`'s `protects_third_party`, is still wrong and is now marked as
such: it lives in `behaviour_harm3p.lp:15-16`, so it is **behaviour-side** — an instance of the
fourth licence class Invariant 2 says is still needed. **That gap is UNCHANGED and still open.**

⇒ **Recorded with its grounds in `resources/03_pipeline.md`, Invariant 2** (*"The `world` exemplar
— RULED 2026-08-07"* and the finding that follows it).

⚠️ **Follow-up, deliberately NOT done here:** `prompt/*.md` still demonstrates no `world` fact.
Adding `illegal/1` to the prompt is a prompt change and needs its own held-out measurement — it is
not a documentation edit and must not be slipped in as one.

### 2.2 ✅ CLOSED 2026-08-07 — the two bad worked examples the prompt dropped

⭐ **RULED and recorded in `phase_1/DECISION_bad_worked_examples.md`.** Both halves are decided, and
the second half was then decided **again** on evidence — read all three steps, because the middle one
alone is the version this queue used to carry:

1. **#4, the hollow stub** (*"survives a paraphrase check by construction"*) — **RESTORED** as bad
   example #6, on a measurement: 10 of 133 concepts carry a gloss adding zero words beyond the
   predicate name.
2. **#2 "translates in isolation"** — the drop is **recorded as deliberate**, with grounds (the user
   block now supplies every cross-referenced clause text: 77/77 anchored clauses) and a named reopen
   condition. A stage-2 check for #4 is rejected **by name, twice**, with the measurement showing the
   obvious proxy is inverted.
3. ⚠️ **Bad example #6 was then REMOVED again** — added, measured twice, reverted by its own
   pre-registered falsifier. See that file's **AMENDMENT 2026-08-07**.

⛔ **Read step 3 correctly.** It is a **null result on a weak instrument**, not a refutation: n = 6
clauses, one model, one temperature, and a proxy metric (`empty_gloss_rate`) that scores legitimate
primitives like `system_message` as empty. Every delta was **inside the noise band** — the example
was not shown to make anything worse. The failure mode is **real** (the 10-of-133 measurement, plus
`STEP_stage4.md` finding (5) measuring it independently), and detection still lives at stage-4 seat
4r.

⛔ **This is NOT a blocklist.** Re-proposing it is explicitly allowed on a better instrument,
adequate power (12 rule-positive clauses × 6 repeats, ≈ $0.21 — this ran 6 × 3), a different form
(only one was tried, and neither form was ruled out), or a different model. **What must not happen is
re-adding it without a fresh pre-registration because it reads well.**

### 2.3 Two prompt-set drifts a transcription review found, still open

Both are edits to **watched** files, so neither is a documentation fix: they need a held-out
measurement and a review, like any other prompt change. Both re-verified 2026-08-07.

1. **`00_task.md:35` says "a rule is not a fact… licences are for the facts your module asserts",
   and the schema disagrees.** `10_output_format.md:89` and `schema.Licensed` require a licence on
   `asserts` and `beats`, **both of which carry a `body`** — they are rules. The worked example's
   `beats` entry is a rule carrying `licence: textual`. `00_task.md` is faithful to the design's
   dataclass sketch and inconsistent with the three files beside it, which is what the model reads
   together.
2. **`00_task.md` never states that cross-referenced clause texts will be supplied.** Rule 2 (`:48`)
   hedges — *"If you were shown the cross-referenced text, you may cite it"* — while the design makes
   it one of four GIVEN items and calls it load-bearing. A model told it *might* be shown a
   dependency has a licence to guess when it is.

---

## 3 PROPOSALS AWAITING YOUR REVIEW

| | file | state |
|---|---|---|
| **the graveyard** | `phase_1/PROPOSAL_graveyard.md` | you have read it; you asked for re-review then implement. **Not yet re-reviewed** |
| **stage 3** | `phase_1/STEP_stage3.md` | ⛔ **revision 2's §0 is REFUTED** and not yet reverted — see §4 |
| **stage 4** | `phase_1/STEP_stage4.md` | written by an agent, **not reviewed by me or you** |
| ~~the atom-slot defect~~ | ~~`phase_1/PROPOSAL_atom_slot.md`~~ | **CLOSED 2026-08-07, file deleted.** Fixed by worked example `m0088`: 18→0 on the diagnosis set, 10→0 held-out. Its findings live in `DEBUGGING_TIPS.md` §1 (the demonstration gap, the clause-concentration rule) and §4 (the hypothesis I refuted) |

---

## 4 ⛔ THINGS I GOT WRONG THAT ARE NOT YET FIXED

**`STEP_stage3.md` §0 is wrong and still in the file.** I argued discrimination coverage should be
built first and labelled verdicts deferred. A clean review refuted it on three independent grounds:

- the cost argument was false — labelling is **~$0.26 for all 593 clauses**, against $6.4 remaining
- one of its two data points was wrong — m0217's rule **does** fire, in 1 of 8 situations
- the concession was far too generous — discrimination coverage reports **byte-identically** for a
  correct module and for one whose meaning is inverted (`permit`→`forbid`)

Revision 3 must revert §0, partition §§1–9 by half, fix a test whose fire condition cannot fire on
the bug it names, and add an enumeration cap and a zero-rule refusal. **Not done.**

⭐ **The `read_back` prompt fix did not generalise, and I reported it as if it had.** It went
6 → 0 on the eight clauses it was diagnosed from and recurs **18 times** on six held-out
clauses. Confounded by clause difficulty and not claimed more strongly, but "the cause went to
zero" was a statement about the diagnosis set, not about the prompt. `eval_arms/RESULT_licence_emphasis.md`.

⭐ **I also reported the prompt fixes as "19 → 18, flat".** Wrong twice: the 19 counted three
`requires-unprovided` NOTES that the current log correctly filters, and my clustering used
backtick-only normalisation while `schema.py` interpolates with `{term!r}` — single quotes —
so the dominant cause stayed fragmented and invisible in the rank. Like for like, error-severity
first-attempt findings went **16 → 8**.

⚠️ One review finding I could **not reproduce** (F1: whether a probe case detects the dead C3 claim
at explanation granularity). Recorded as unresolved, not accepted.

---

## 5 FINDINGS ABOUT COMMITTED ARTIFACTS — worth knowing before you sign anything

- ⭐ **`m0255.lp`'s claim C3 is behaviourally inert.** Deleting both its rules changes nothing:
  144→144 models, all five probe cases bit-identical. **Cause found**: a later edit to the same file
  (iteration 3's coherence constraint) subsumes it. Remove that constraint and the counts diverge
  180 vs 192. Recorded in `phase_1/FINDINGS_m0255.md`. **The rules were not deleted.**
- ⭐ **The "5 witnesses" figure cited three times in the design does not reproduce.** The honest
  number is **72**; six projections were tried and none gives 5. The load-bearing half — *zero*
  without the dependency — reproduces exactly. Corrected in all three places.
- **5 of 8 stored modules no longer validate** under the current contract, from two contract changes
  made today. That is the empirical case for artifact versioning (§6).

---

## 6 WHAT IS BUILT AND GREEN

**270 tests** (was 217) · `translate.py --self-test` 53/53 · `link.py --self-test` 19/19 ·
`mutate_schema.py` **45 guards, 0 survivors** · spend **~$0.19** of $8.50.

Since: the graveyard's persistence layer, `eval.py` (an A/B harness that measures its own
noise first and scores the FIRST attempt only), `eval_arms/make_arm.py` (an arm generated as a
verified one-line diff of the live prompt, never a copy), and stage 3 plan revision 3.

Stage 1 and stage 2 run end to end: schema contract, clingo compile, unresolved names, rule shape,
closure, `beats` acyclicity, concept table — then an accumulating repair transcript with typed
gaming guards. The formal model was retired to its staleness guard, which now watches the
transcriptions.

---

## 7 MY RECOMMENDED ORDER WHEN YOU RETURN

1. ~~Rule on §2.1 (`world` facts)~~ — **done 2026-08-07.** Ruling recorded in the design; §2.2 is
   now the only open transcription item.
2. Re-review + implement the graveyard (you have already called this).
3. `STEP_stage3.md` revision 3, re-reviewed, then implement both halves.
4. ~~Retire `STEP_stage2_and_repair.md` into the design~~ — **done 2026-08-07. File deleted.**
   Abstention-as-an-outcome and the typed repair guard went into `resources/03_pipeline.md`; the
   arm-B withdrawal went into `DEFERRED.md` D-3; its stale "fresh conversation" text was dropped.

---

## 8 ⛔ HELD FOR ONE EDIT TO `resources/03_pipeline.md` — do not land these piecemeal

**Collected 2026-08-07 from `REVIEW_DOC_AUDIT.md`.** Every item below has `resources/03_pipeline.md`
as its destination. It is a **watched** file with another change in flight, so they are parked here
rather than applied one at a time. **All four were re-verified against the file on 2026-08-07 and
every line number below is current.** They are the *only* surviving reason to keep
`model/REVIEW_FINDINGS.md` (604 lines) and are half the reason to keep
`model/TRANSCRIPTION_REVIEW.md` — landing them retires documents, which is why they are worth doing
together.

⚠️ **Do them as ONE edit, then re-run `guard.py` and re-review the file.** Four separate edits to a
watched file is four review points.

### 8.1 The document contradicts itself on stage numbers, and the diagram is right

Draft, to be placed **near the top of Part 1** so it is read before the diagrams:

> ### ⚠️ Known internal inconsistencies in this document, 2026-08-07
>
> Recorded rather than silently carried, because two reviews independently stalled on them and a
> third could not check `check(C, Stage, _)` against any single authority.
>
> **The stage numbers in the prose do not match the diagram, and the diagram is right.** Diagram:
> 5 NORMALISE · 6 PARAMETERISE · 7 EXPAND · 8 LINK · 9 MUTATION. Prose that disagrees: *"Stage 7's
> merge"* (`:1052` — the merge is stage 5); *"visible only at stage 9"* (`:1164` — that is LINK,
> stage 8); *"seat 5c"* (`:1061` — the seats are 4a–4d); a heading `### 6 — Divergence` (`:806`)
> where the diagram leaves DIVERGENCE unnumbered and gives 6 to PARAMETERISE; a heading `### 9 and
> 10 — Testing the tests` (`:860`) whose body opens *"**11 — Translate twice**"*.
>
> **The failure-mode count is given as 16 in one place and 17 in every other.** Part 3's diagram node
> reads *"and the 16 error cases"* (`:232`); the stage-1 diagram says *"the 17 known failure modes"*
> (`:394`); Part 1's table has seventeen rows and `phase_1/prompt/30_failure_modes.md` transcribes
> all seventeen. **#17 was added later and that one node was not updated.**
>
> **Part 6's *"⭐ Stage 1 has never been run"* is stale** (`:1139`). It has run: three clauses on
> 2026-08-07, then 36 first attempts across two prompt arms in `phase_1/eval_arms/`. The same
> sentence survives in `phase_1/translate.py`'s module docstring (`:7`) — recorded in
> `phase_1/README.md` under "What a run does".
>
> ⇒ **Until these are corrected, do not derive anything from a stage number stated in prose.** Read
> the diagram, and cite the stage by NAME. A reviewer who cannot resolve "stage 2" against a single
> authority cannot check whether a check is at the right stage, which is how a coverage check ended
> up asserted at a stage that could not build its inputs.

### 8.2 The unresolved inline reviewer query at `:437` is still embedded in the design

Part 4 §1's GIVEN table still carries, in the right-hand column of the cross-reference row, an
unanswered query: *"<√Are you confidence the document's own mardown anchors are sufficient to give
every cross reference accurately?…>"* — while the cell beside it asserts the anchors *"give this list
mechanically"*, unqualified, in the **source of truth**. It is **partly answered** and the answer is
not next to it. Draft replacement for the cell (and delete the query column):

> | the text of every clause this one cross-references | ⭐ a clause that modifies rules defined
> elsewhere cannot be translated in isolation. The document's own markdown anchors give this list
> mechanically — ⚠️ **for the 13 % of clauses that carry one.** `[RAN]` 77 clauses of 593 have a
> resolvable anchor and all 77 receive the referenced text; the rest are supplied nothing. Finding
> the unanchored dependencies is an open problem, and a clause that depends on another without an
> anchor still reaches failure mode #2 with nothing to prevent it. Recorded with its measurement in
> `phase_1/DECISION_bad_worked_examples.md`, which drops the "translates in isolation" worked example
> on the strength of the mechanism existing — **not** of the mode being impossible. |

### 8.3 Attack D belongs in the typed-repair-guard attack table

`CONFORMANCE_REVIEW.md` F10, **reproduced 2026-08-07**: a module with `acts: []`, `asserts: []`,
`ontology: []`, `beats: []`, `defines: []`, `closure: []` and **one** `concepts` entry validates
clean and reports `outcome == "translated"`. Its rendered `.lp` is comment lines and two
`%!show_trace` directives — **not one fact, not one rule.**

⚠️ One correction to the review's version: `claims` must be **non-empty** (validation raises
*"translated with no `claims`"*), so the attack carries a claims block it never encodes. That makes
it *worse*, not better — the `.lp` states in a comment what the logic does not say.

Draft:

> ⛔ **Attack D — delete the content, keep the declarations.** A module whose only surviving field is
> `concepts` satisfies the "did you translate anything" guard, and a module with `acts: []` owes no
> closure declaration at all, because the forced closure is derived from the acts the module governs.
> Together they make a **contentless module a passing translation**: zero asserts, zero ontology
> facts, zero rules, a `.lp` containing only comments, `status: "translated"`, counted in the run's
> success line. Measured on `m0037`: attempt 1 wrote a whole rule into an `atom` slot, the finding
> was correct, and attempt 2 cleared it by **deleting the entry** rather than moving the conditions
> into `body`.
>
> This is the same shape as attacks A–C and belongs with them: the guard must be **typed**, not
> sized. The `shrank` flag is not the fix — it fires and sets no outcome. A translated module owes at
> least one of `asserts` / `defines` / `ontology` / `beats`, and a module that governs no act is a
> claim about the clause that should have been an abstention.

⚠️ **8.3 touches `schema.py` as well as the design, and `schema.py` is watched too.** Its two guards
sit immediately beside the F4 fix (`concepts` was deliberately REMOVED from the declaration set). See
§8.4 — fix them together or not at all.

### 8.4 ⛔ `acts` is not a declaration site, and F4 must not be re-opened while fixing it

Recorded in full as `phase_1/DEBUGGING_TIPS.md` §13, with the reproduction. Named here because the
**design** side of it belongs in the same `03_pipeline.md` pass, and because the trap is the sort
that gets walked into by whoever fixes §8.3: `schema.py` builds `known` from
`ontology ∪ requires ∪ inputs`; `concepts` was removed from it **deliberately**, because a rule
resting only on concept declarations can never fire. **The distinction to preserve: an act is a
declaration site because the module governs it and owes a closure over it; a concept is not, because
saying what a name means never says that anything derives it.** Fixing F5 by loosening `known` is how
F4 comes back.
