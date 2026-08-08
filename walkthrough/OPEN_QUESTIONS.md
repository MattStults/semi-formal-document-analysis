# Questions waiting on Matt

**Maintained by the autonomous run. Everything here BLOCKED work; everything else continued.**
Newest first. Each entry says what is blocked, what I did instead, and what a decision costs.

⚠️ **Nothing here was decided unilaterally.** Where a design question arose I recorded it and
worked around it. Where a design ruling already existed I followed it, even where I would have
chosen differently — that is the standing instruction.

---

## Q-10 ⭐ THE LABELLED HALF FOUND A LIVE TRANSLATION DEFECT THE DETERMINISTIC HALF SCORED CLEAN

**This is the result that justifies building the `[L]` half at all, and it needs your adjudication.**

`m0150`: the deterministic half scores it **`passed`, |R| = 5, coverage 5/5** — a clean sheet. The
seat labels situations S5 and S9 `must-be-silent`. The module asserts `prefer make_tool_call` in
both, **because its rules never require a tool call to be under consideration**.

⇒ The rule fires in situations the clause does not speak to. `[D]` cannot see this **by
construction** — mutation coverage asks whether deleting a rule changes an outcome, and this rule
does change outcomes; it changes them in the wrong situations.

⛔ **`CLAUDE.md` requires every flip to be adjudicated against the document, with label values
nowhere in the room. I have not done that** — it is a judgement about what clause m0150 says, which
is yours. The seat's reason and the situations are in `RESULT_stage3_labelled_live.md`.

⚠️ One caveat that cuts the other way: the seat's errors on `m0217` all run in **one direction** —
over-reaching past the clause's trigger. If that is the seat's bias rather than the module's defect,
S5/S9 could be the same over-reach. That is exactly why this needs a human and not me.

---

## Q-11 · `render_situation` is defective at k = 1, and it cost the run its only forbid-side module

With a single fact line the seat reads the fact **as the situation id**, `adjudicate` refuses, and
`m0014` returned 6 refusals from 6 calls. The guard behaved correctly — a refusal, not a partial
pass — but the rendering is wrong, and the run therefore has **no forbid-side / `cnpa` coverage at
all**.

**Not fixed:** the fix changes what the seat is shown, which `STEP_stage3.md` §5 specifies row by
row. That is a design edit.

---

## Q-12 · The label set has no answer for `oblige` or `prefer`

Four of twelve mismatches are this artefact, not disagreement. The three-valued set
(`must-forbid` / `must-permit` / `must-be-silent`) covers the forbid/permit axis; the closed status
set is **four** values. A seat with no way to say "the clause requires this" must answer with one of
the three it has.

**What a decision costs:** either a fourth and fifth label (changing §5's brief and every stored
labelling), or an explicit ruling that `oblige`/`prefer` rules are out of scope for stage 3 and
excluded from the denominator by name.

---

## Q-13 · The seat is NOT validated, and the standing ruling names the test that would do it

`CLAUDE.md`: *"the adjudication seat is proven at small-model/frontier parity, and divergence from a
frontier model on the same brief is a seat defect, not a model failure."*

That test has **not been run**. There was no ground truth in this run, so "working" currently means
only *"did not exhibit the failure §9 named"*. The actual validation is a frontier model on the
identical brief over the identical 23 cells — **≈ $0.20**.

**I did not run it:** it is the validation the ruling requires, and Q-10's adjudication depends on
knowing whether the seat over-reaches. Say the word and it is twenty minutes.

---

## Q-6 ⛔ HALF THE CORPUS CANNOT REACH ANY STAGE-4 SEAT — the biggest finding today

**Blocked:** running stage 4 on most of what we have.

`[RAN]` Of the 14 stored modules that validate against today's schema, the renderer returns
`readback-ungloss` on **7** — they are blocked from every seat. 14 distinct symbols have no written
meaning: `interactable_entity`, `interaction_entity` (both `m0053`, exactly as `STEP_stage4.md`
§2.3 predicted), plus `task`, `disallowed`, `pasted_text`, `policy_class` and others. **Almost all
are `requires`/`inputs` predicates that no clause in the corpus defines.**

`STEP_stage4.md` §2.3 says a missing gloss is an ERROR and the clause reaches no seat. That ruling
was written expecting it to fire on `defines.term`. It fires on half the corpus.

**Three readings, and I am not choosing between them:**
1. The renderer is right and the corpus is not ready — a symbol with no written meaning genuinely
   cannot have its meaning rendered, and Invariant 1 says so.
2. `requires` predicates are defined *elsewhere*, so demanding a local gloss is the wrong test at
   single-module scope — that is D-3's link-scope question wearing a stage-4 costume.
3. The threshold is right but the corpus needs a gloss-supplying pass first.

**What I did instead:** built and tested everything, and left the 7 blocked rather than relaxing the
check to make the number look better. **Lowering a floor to make a run pass is the one thing
`CLAUDE.md` forbids outright.**

---

## Q-7 · `STEP_stage4.md` §2.3's `act/1` template cannot be implemented as written

It renders `produce(M)` as *"producing the material"*. But `[RAN]` **no module in the corpus
declares a concept for its own act functor**, nothing in the schema glosses an act, and turning
`produce` into "producing" plus reading `M` as "the material" needs knowledge no artifact carries.

**What was done instead:** the act renders as itself inside `⟨act produce(M)⟩` with a
`readback-act-literal` note, and only that marked span is exempt from RB1. Without the exemption
RB1 fires whenever an act functor is also a declared input.

**What a decision costs:** doing it properly needs a **new schema field** (an act gloss). That is a
contract change, so it was not made. Cheap to add if you want it.

---

## Q-8 · Two prompt sites still teach the disproved `_` ground

`prompt/00_task.md:70-71` and `prompt/30_failure_modes.md:20` both tell the model *"the explanation
tooling cannot process `_`"*. That ground is now disproved and the schema gate is gone.

⚠️ **Consequence, stated plainly: until these are edited the model still will not write `_`, so the
schema change alone buys nothing at the prompt level.**

**Not edited, deliberately.** Both are watched transcriptions; the failure-mode list is a numbered
transcription of `03_pipeline.md` Part 1 whose count `translate.py --self-test` asserts, it is
mirrored in three `eval_arms/` copies, and `DEBUGGING_TIPS.md` §10 requires a held-out measurement
and a review for any prompt change. Removing a schema *gate* is what "no restrictions" means
mechanically; changing what we *teach* is a prompt change with its own process.

---

## Q-9 · RB1 as specified fires on ordinary English inside glosses

`[RAN]` RB1 ("no predicate label survives into the English") fired on 9 of 14 modules, 34 findings —
but **18 of the 34 are single-word predicate names like `task`, `user`, `instruction`, `assistant`
occurring as ordinary English inside a gloss**, not as a leaked label.

The renderer now distinguishes renderer-emitted from gloss-internal in each finding, because
collapsing them would point every repair at the renderer when the majority are about the gloss.
Whether gloss-internal occurrences should be a finding at all is a design question.

---

## Q-1 · Stage 5+ have no design at all

**Blocked:** anything past stage 4. `03_pipeline.md` describes stages 1–9, but only 1–4 have STEP
documents. Stages 5–9 have no plan, no failing example, and no cost model.

**What I did instead:** wrote *initial* designs for the next undesigned components as drafts marked
`DRAFT — NOT REVIEWED`, following the STEP format (a passing example, a failing example, evidence
produced, cost). They are proposals for you to review, not decisions.

**What a decision costs:** reading one STEP draft is ~15 minutes. Implementing against an
unreviewed design risks the thing this project already paid for twice — building a check that
measures the wrong thing and reports success.

---

## Q-2 · The `[L]` half of stage 3 has never been run against a real model

**Status: UNBLOCKED — you authorised the spend before going AFK ("Feel free to spend on the [L]
run"), so I am running it.** Recorded here because the RESULT may need your ruling.

`STEP_stage3.md` §9 says two measurements must exist before any coverage number is believed:
- the **`silent`-rate**. A rate near zero on a corpus where most clauses govern one act is a **seat
  defect**, to be investigated as one — not a conclusion about the translations.
- the **`k` histogram**, from which `probe.max_signature` must be re-set. It is currently 10, from a
  cost model, and nobody has measured the real distribution.

**What needs you afterwards:** if the `silent`-rate comes back near zero, §9 says that is a brief
defect. Rewriting a seat brief is a design change, so I will report and not act.

---

## Q-3 · Stage 4's four seats need spend, and the amount is not yet estimable

**Blocked:** running stage 4 end to end.

Four review seats per clause, over a corpus of 593. The renderer is being built now; until it
exists I cannot count the items each seat must read, so I cannot price it. The project cap is
$8.50 with roughly $2.5 used.

**What I did instead:** everything up to the seats — renderer, the five deterministic RB checks,
and the seat prompts exercised against stubs.

**What a decision costs:** an authorisation and a ceiling. I will produce a measured estimate from
the renderer's real output before asking, so the number will be evidence rather than a guess.

---

## Q-4 · `dryrun.txt` is stale and is the one failing self-test check

`translate.py --self-test` reports 52 passed / 1 failed. The failure predates today.

**I have deliberately NOT regenerated it.** Regenerating bakes the current prompt into the
artifact, which would turn a visible red into an invisible green while changing what the artifact
attests. That is the shape this project keeps being bitten by.

**What a decision costs:** one word. Either "regenerate it" (and it goes green, attesting today's
prompt) or "leave it" (and it stays red and honest until the prompt settles).

---

## Q-5 · `STATE.md` is a deletion candidate with live inbound citations

It duplicates `REVIEW_QUEUE.md` and the phase_1 README and has drifted from both — it claimed
stage 2 was "under review, nothing built" until I corrected it today. But `STEP_stage3.md` and
`STEP_stage4.md` both cite it, and one live finding (weakest-licence inheritance being stated in
two places and computed nowhere) has **`STATE.md` as its only record**.

**What I did instead:** left it, corrected its false claim, and marked it a deletion candidate in
the file itself.

**What a decision costs:** "delete it" means first moving that one finding somewhere live. I can do
that unprompted if you want it gone — say so and it is a ten-minute job.
