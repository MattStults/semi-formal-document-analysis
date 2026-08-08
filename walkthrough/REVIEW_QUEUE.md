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

⚠️ **A clean review of the five already ran** (`model/TRANSCRIPTION_REVIEW.md`). It found six items.
Four are fixed. **§2.1 is now RULED and closed; §2.2 remains open.** Accepting the five now would
certify files a review just found drifted.

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

### 2.2 The other open transcription item

Two of the design's five bad worked examples were swapped out for act-indexing and missing-sayer
cases. Dropped: *"translates in isolation"* and the hollow stub the design calls *"survives a
paraphrase check by construction."* Restore, or record the swap as deliberate.

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
