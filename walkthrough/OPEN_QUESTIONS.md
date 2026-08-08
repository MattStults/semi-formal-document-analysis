# Questions waiting on Matt

**Maintained by the autonomous run. Everything here BLOCKED work; everything else continued.**
Newest first. Each entry says what is blocked, what I did instead, and what a decision costs.

## ⛔ ONE ACTION NEEDED BEFORE ANY FURTHER COMMIT TOUCHING A WATCHED FILE

```
semi-formal-experiment/.venv/bin/python walkthrough/model/guard.py --accept paper_pipeline/phase_1/schema.py
```

`schema.py` moved twice after you accepted it, both times to **restore or complete a guard**, and
both on evidence: the anonymous-variable rejection (`b7c663e` — xclingo dies on `_` in a body, so my
earlier withdrawal was wrong) and the internal-full-stop rejection (`f8f83ed` — a body carrying a
second statement was having two thirds of itself silently dropped). Nothing was relaxed.

---

⚠️ **Nothing here was decided unilaterally.** Where a design question arose I recorded it and
worked around it. Where a design ruling already existed I followed it, even where I would have
chosen differently — that is the standing instruction.

---

## Q-20 ✅ RULED — artifact versioning and the re-run strategy

**Matt, 2026-08-08:** *"It should probably trigger a re-run. If there's an intention flag that would
make sense for a partial re-run we could respect that."*

⛔ **This was under-tracked and that is my failure, not a design gap.** The two hash functions have
existed since the graveyard landed, but `[RAN]` they are called **only when writing a graveyard
entry** — metadata on a FAILURE record. Zero occurrences across every `run.json` and `m*.json`.
Nothing compared a stored hash to a current one; nothing selected clauses for re-translation. The
strategy did not exist, and it appeared nowhere in this file despite 19 other entries being here.

**The ruling, now being implemented:**

| hash | covers | on a change |
|---|---|---|
| `contract_hash` | clause text + schema source | the artifact **may no longer validate** ⇒ re-translate, not optional |
| `provenance_hash` | prompt + model + params | ⭐ **also re-runs**, per this ruling |

⚠️ **The two stay separate even though both now re-run**, because they answer different questions: a
module whose `provenance_hash` moved is still **valid** and still links — it simply cannot be cited
as evidence about the current prompt. Collapsing them marks the whole corpus stale on every prompt
edit, which makes iteration impossible. `graveyard.py`'s docstring already carries that argument.

**Rejected by name** (to be written into `03_pipeline.md` with the ruling): *"one hash for
everything"*, and *"a provenance change only relabels, never re-runs"* — the latter considered and
rejected by Matt today.

**The intention flag is the part to watch.** It is the mechanism by which someone makes 593 stale
modules not-stale with one word, so it is being designed to be hard to use carelessly, to leave a
record, and to be **incapable of excusing a `contract_hash` change**.

---

## Q-19 ⛔ §6's DIVERGENCE MACHINERY CAN NEVER FIRE — and the design, not the code, is why

`[RAN]` **0 divergence records over all 81 legal verdict combinations.** Every seat's verdict
vocabulary is disjoint from every other's:

| seat | verdicts |
|---|---|
| 4a | `as-meant` · `not-as-meant` · `unclear` |
| 4b | `faithful` · `unfaithful` · `unclear` |
| 4c | `licensed` · `unlicensed` · `unclear` |
| 4d | `covered` · `not-conveyed` · `unclear` |

…and **every pair in `CONTRADICTIONS` sits inside a single seat's vocabulary.** So `seat-divergence`,
the brief shas, `promote`, `Triage` and `report_line`'s NOT-ADJUDICATED branch are all unreachable,
and the five tests pinning §6 build judgements `validate_judgements` refuses.

⚠️ **The code implements the design literally.** §6 says *"when two seats reach opposite verdicts on
one item"* — and its own worked example is *"only `faithful` vs `unfaithful`"*, **both 4b's**. The
design describes a cross-seat mechanism using a within-seat pair.

**The question is what "opposite" means across seats**, and it is genuinely yours:
1. **Shared vocabulary** — seats answer the same question, so verdicts are comparable. Changes every
   seat brief.
2. **A tension table** — `4b: faithful` against `4c: unlicensed` is not literally opposite but is in
   tension. Needs the pairs enumerated and justified.
3. **§6 applies only within a seat** — two labellings of one item by one brief. Cheapest, and much
   weaker than §6 reads.

⛔ **This matters more than its size suggests.** §4.3's whole guard is that *unanimity must not read
as confirmation*, and §6 is the mechanism that makes disagreement visible. If it cannot fire, four
agreeing seats are the only possible outcome — which is the failure §4 is written to prevent.

---

## Q-18 · Stage 0's competency check has 2 unexpected failures — red, and correctly loud

`walkthrough/paper_pipeline/cq_check.py` reports **14 as declared, 2 unexpected, 2 blocked**.
CQ-6.a and CQ-6.b fail against their written-first expectations. Pre-existing, unrelated to today's
work, and outside the stage 1–4 scope I was given — recorded so it is not lost.

⚠️ **A correction worth reading, because two of us got it wrong in the same way.** A subagent
reported *"the tool exits 0 anyway, so stage 0's competency check is red and quiet"*, and I nearly
filed that as a defect. It is false: `[RAN]` `cq_check.py` exits **1**. Both measurements had been
taken through a shell pipe, where `$?` reports `tail`'s status and not the program's.

⇒ The check is red and **loud**. Nothing needs fixing in its signalling; what needs attention is the
two failures themselves, which is a stage-0 question.

⭐ The general lesson is worth more than the finding: **`cmd | tail` silently discards the exit
code**, and this repo's whole discipline is that a check must not be able to look like it passed.
Two independent agents produced the same false "exits 0" claim from that one habit.

---

## Q-16 ✅ RESOLVED — stage 4's R3 layer is built and wired

`STEP_stage4.md` §2.1 specifies **three** rendering layers. `readback.py` produces **R1 and R2
only**. R3 — *"xclingo explanation tree, every leaf replaced by its R1 rendering"* — is absent, so
**no derivation reaches any seat**, and 4a/4b's denominators are smaller than §2.1 describes.

⭐ **DONE 2026-08-08.** `readback_r3.py` (36 tests, 21 mutants / 0 survivors) composes a
`%!trace_rule` mechanically from the module's own glosses, runs xclingo once per derived verdict
atom, and replaces every leaf with its R1 rendering. Wired into 4a and 4b, which §5.1 specifies as
*"the rendered set (R1+R2+R3)"* — so the design answered the "fifth denominator?" question and no
decision was needed.

`[RAN]` **8 of 18 covering-set situations derive a verdict** across the stored modules. The other 10
are excluded **by name** as `no-derivation`, never dropped — dropping them would overstate 4a's
coverage by more than a third.

⚠️ **Two defects it found on live material, both Invariant 1 violations reaching seat-facing text:**
the ablation guard `o` surfaced as an unglossed leaf of every ontology-backed derivation, and a raw
ASP atom (`asserts(m0079,oblige,produce_response)`) reached the rendered sentence because xclingo
joins two labels with `;` and the payload was read as one quoted string.

**Still unsigned:** R3 is not gated on the probe outcome — `m0134`'s probe outcome is `failed` and
R3 renders it anyway. Arguably right, since the derivation is still real evidence, but nobody has
ruled.

⚠️ It is also the reason the anonymous-variable guard matters (see `b7c663e`): R3 is the layer that
xclingo actually drives, so a `_` anywhere in the link set would take the whole tree down.

---

## Q-17 · 4c's independence is compromised by gating, not by design

`plan_clause` refuses a clause whose read-back failed, so **4c never runs for the 7
`readback-ungloss` modules**. §4.1's anchor property is that 4c is independent of the rendering —
and it is provably independent of a *wrong* rendering (a test asserts 4c is never stamped), but not
of a *missing* one.

⇒ The seat designed to be the check on the shared artifact is switched off exactly when that
artifact fails. **Worth a ruling**, and I did not change the gating.

---

## Q-14 · The design contradicts its own grounds for disclosing an `impossible` label

The spec-drift review filed this as a leak (A2, "CODE should change"). **I checked and the reviewer
is wrong about the remedy** — but right that something is inconsistent.

`STEP_stage3.md:331` **explicitly rules**: *"`impossible` is a label the seat may return, and it is
the only label that is not a verdict… which is why it is **disclosable**"*. §8 item 16 is a TDD test
for precisely that behaviour, and `:385` lists the finding text under `probe-structural`.

⇒ **The code follows the design.** I did not change it.

⚠️ **But `:385`'s stated GROUND is false of it**: *"derived from the module and the solver alone,
with no expected verdict anywhere near them."* An `impossible` label is a **seat output**, not
solver-derived. The ruling may well be right — an `impossible` finding names a situation and no
status — but it is right for a different reason than the one written down.

**What a decision costs:** one sentence in `:385` distinguishing *"carries no expected verdict"*
(true, and the real ground) from *"was not produced by a model"* (false). ⛔ It is a design edit to
a watched file, so I left it.

---

## Q-15 · Review findings I did NOT act on, and why

Both adversarial reviews landed (`SPEC_DRIFT_REVIEW_2026-08-07.md`, `ENGINEERING_REVIEW_2026-08-07b.md`).
Two HIGH findings are **fixed** (the silent content drop, and the anonymous-variable guard I
withdrew on the wrong tool). These remain, each because acting would be a design decision:

- **RB1's act exemption** (`readback.py`) grants a second exception where `STEP_stage4.md:415`
  grants one. 19 of 19 `asserts` renderings show a bare functor. The reviewer's view is "a hole, not
  a limit"; mine is that it cannot be closed without a schema field for an act gloss — which is
  **Q-7**. Same question, two symptoms.
- **RB4 is structurally blind to layer-1 content.** Revision 2 weakened a check while stating it
  amended only §2.3. Latent today at 0/106 layer-1 items, live as soon as any module uses a
  construct with no template.
- **`readback.Finding` has no `origin`**, so `readback-structural` cannot be registered in
  `DISCLOSABLE_ORIGINS` as §5.5 requires "in the same diff". This is the leak perimeter's
  registration rule, and it is currently unsatisfiable for stage 4.
- **§8 requires stage 4 to ship a mutation run at 0 survivors**, but `mutate_schema.py` deletes
  `ast.Raise` nodes and `readback.py` has **none** by design. ⭐ The reviewer's judgement, which I
  share: **do not weaken the bar — write the right instrument.** The reviewer hand-wrote 15 mutants
  and killed 12; the 3 survivors are real gaps.

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

⭐ **ANSWERED 2026-08-08 — `seats.py --cost`, computed from the real rendered artifact, free:**

| | total (7 clauses) | per clause |
|---|---|---|
| **WORST, flash** | **$0.0360** | $0.0051 |
| WORST, frontier | $3.5782 | $0.5112 |
| likely, flash | $0.0063 | $0.0009 |
| likely, frontier | $0.3979 | $0.0568 |

⚠️ **WORST is the number a budget decision uses** — every reply at its 4096-token cap, which is what
dominates the frontier figure. `likely` assumes 40 output tokens per judgement and is an
**assumption**: nothing has run, so no reply length has been measured.

⇒ **On the configured flash model a full stage-4 run over everything that can reach a seat costs
about four cents.** That is inside any reasonable ceiling. On a frontier model it is $3.58, which is
42% of the entire remaining project budget.

⛔ **AT CORPUS SCALE THE FRONTIER NUMBER IS DISQUALIFYING, and the first estimate understated it.**
`STEP_stage4.md` §7 said roughly $25 for 593 clauses. Measured: **$303 worst / $33.7 likely** at the
hard-coded `(5.0, 30.0)` frontier price — and once the code reads the *real* maximum in
`providers.json` (`fable`, `10/50`), **$509 worst / $60.1 likely**. That is **60× the entire $8.50
project cap**, and even the optimistic figure is 7×.

⇒ **A frontier stage-4 pass over the corpus is not affordable and never was.** The flash figure
scales to roughly $3 for 593 clauses, which is. §7 now carries the measured table.

⛔ Only **7 of 19** stored modules reach a seat: 5 fail stage 2, 7 are blocked by `readback-ungloss`
(**Q-6**). The check was not relaxed to raise that number.

---

## Q-4 · `dryrun.txt` is stale and is the one failing self-test check

`translate.py --self-test` reports **51 passed / 1 failed** (this said 52; measured 2026-08-07).
The failure predates today.

⚠️ **It is now VISIBLE from pytest.** `test_prompt_examples.py
::test_translate_self_test_runs_to_completion` asserted only "no Traceback" and "N passed", so
`pytest walkthrough/` read green while the self-test exited 1. It now asserts `returncode == 0`
— which pins no count, so it does not re-create the anti-pinning problem its old comment
claimed — and carries `xfail(strict=True)` naming this question. **Strict matters:** the moment
this is resolved and the self-test goes green, that test XPASSes and FAILS, so the exemption
cannot outlive the ruling.

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
