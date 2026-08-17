# RESULT — ARM G, task decomposition

**Answer: decomposition MOVES defects by layer, unevenly, exactly as the hypothesis
predicts — and it breaks the join between the layers it separates.**

The class no instruction has ever moved — a borrowed gloss stamped `licence: textual`,
**18 of 18 names in both prior arms** — fell to **1 of 18**. The vacuous-body and
polarity classes fell too. And the schema floor **collapsed**: 10 of 13 modules
invalid against 5 of 13 for the unaided baseline, because **13 of 31 assertions came
out with no body at all**, against **0 of 25** unaided.

⚠️ **n = 13 of the 17 clauses.** The arm was stopped by its budget, not finished. Four
clauses (`l1707_1973_n022`, `l2474_2554_n004`, `l2821_3040_n017`, `l3239_3382_n004`)
have no final module. Every number below is **paired on the 13 that completed** — arms
A and B rescored on the same 13, never on their published 17.

⚠️ **Cost, said plainly and before the defect numbers.** Arm G cost **2.25× the unaided
baseline per clause on the calls that produced something, and 3.7× all-in** — because
**39% of the arm's spend bought nothing at all.** See §5. A reader who cares about
defects per dollar should read §5 before §3.

**Pre-registration:** `PREREG.md`, signed before the first call, with two amendments
recorded in §6. **Spend $0.10875** of a $0.115 self-cap and the brief's $0.120 ceiling:
**53 recorded calls + 26 wasted calls = 79 sends.**

---

## 1. THE SPLIT

| stage | system block | asks for |
|---|---|---|
| 1 ENUMERATE | `promptsG/s1_enumerate.md`, 2.3 KB | the span in prose. **No predicates, no logic, no JSON.** |
| 2 DEONTIC | `promptsG/s2_deontic.md`, 2.4 KB | status / act / body / read-back / closure, and five questions about them |
| 3 DECLARE | `promptsG/s3_declare.md`, 3.0 KB | ontology vs requires vs inputs, arity, glosses, **licences** |
| 4 ASSEMBLE | **the production system block, byte-identical**, 39,959 c, sha256 `3a66c5f5…4c34c` | the JSON object |

User turn 1 is `translate.build_user`'s production user block, unmodified — same span
bytes, same NEEDS/PROVIDES/CITATION instructions. Stages 2–4 append their stage prompt
as a further user turn on one transcript. A sha256 gate refuses to send stage 4 unless
the assembled block still equals production's; it printed the match before every send.

**The stage prompts are QUESTIONS, not review-list entries.** 8.2 KB total across four
stages against arm B's 13.5 KB in one, and **no stage prompt contains a clause id, any
span text, or any example drawn from these 17 clauses.**

⛔ **Entry 5 was excluded and replaced.** Entry 5 is measured to manufacture vacuous
bodied rules. Arm G ships no instruction to prefer bodied rules. Stage 3 Q1 asks the
**exclusion test** instead — *name a thing of the head variable's kind that your body
excludes; if you cannot, you have not defined the class* — and offers two honest routes
(`concepts` only, or `inputs`), requiring the model to pick one by name. §4 records what
that did, and it is not what I predicted.

---

## 2. THE MEASUREMENT IS MECHANICAL

`layers.py`. Every detector reads only the emitted JSON and the node's own user block.
No adjudicator judgement enters any cell of the table below. The reason is on the
record: `list_in_prompt_insample/RESULT.md` §10 states that the single adjudicator on
these 17 clauses is contaminated **toward** finding the historical defect, and I am that
adjudicator's successor with all the same reading behind me.

**Calibrated before the arm was priced, on data already on disk**: the detectors
reproduce arm A's published floor rate (7/17), arm B's (6/17), and all four rows of arm
B's published entry-5 harm table verbatim — `no_moral_ambiguity(S) :- scenario(S)`,
`repeats_user_prompt(R) :- response(R)` ×3, `natural_uncertainty_expression(A) :-
assistant_definition(A)`, `honest_and_forthright(A) :- assistant_conduct(A)`.

⚠️ **ONT-1 is an over-inclusive proxy**: it flags any bodied ontology rule all of whose
body atoms are unary over head variables, which catches a genuine three-condition
definition as well as the real defect. It is applied identically to all three arms, so
the comparison is sound and the level is inflated. Every hit is in `layer_scores.json`.

---

## 3. ⭐ THE LAYER TABLE — the measurement this arm uniquely buys

Paired, same 13 clauses, same detectors, one variable.

| layer | detector | **A** unaided | **B** list-in-prompt | **G** decomposed |
|---|---|---:|---:|---:|
| DECL | ⭐ **borrowed-gloss licence** (clauses) | 12 / 12 | 12 / 12 | **1 / 12** |
| DECL | ⭐ **borrowed-gloss licence** (NEEDS names) | **18 / 18** | **18 / 18** | **1 / 18** |
| DECL | NEEDS misfiled | 1 | 1 | **0** |
| DECL | undeclared body name | 1 | 1 | 1 |
| ONT | vacuous / type-only body | 3 | 6 | **1** |
| ONT | coextensive heads | 3 | 3 | **1** |
| ONT | unlinked singleton | 0 | 0 | 0 |
| DEO | `prefer` polarity | 1 | 2 | **0** |
| DEO | shared-body `oblige` (disjunction) | 1 | 1 | **0** |
| DEO | ⛔ **bodiless `oblige` ×2+** | 0 | 0 | **4** |
| CITE | foreign citation | 0 | 0 | 0 |
| — | ⛔ **floor `!= translated`** | 5 | 4 | **10** |
| — | ⛔ **total schema breaches** | 14 | 16 | **21** |

### ⭐⭐ The headline: the licence class moved, and only decomposition has moved it

A node's NEEDS block hands the module a gloss *another node established*. Both prior arms
stamped every single one `licence: textual` — which, under this node's own CITATION
instruction (*"must cite EXACTLY this node's id"*), can only cite the node that did not
establish it. `00_task.md` calls a manufactured citation *"the single worst failure
available here."* Arm B's out-of-sample result called this its largest fresh class;
the in-sample result recorded it as **identical in both arms, unchanged, named by no
entry in a 13.5 KB list.**

**18 of 18 → 1 of 18**, on one question asked at the right moment:

> *(a) which licence are you putting on its `concepts` entry? (b) if `textual`, write
> out the clause id you are citing, and then write out the sentence in the narrowing
> that says it. (c) if you cannot complete (b), say so, and say which licence you are
> using instead.*

The stage-3 transcripts show the reasoning working, not being obeyed. On
`l2126_2404_n016` the model wrote: *"(a) `assumed` for both. (b) Cannot cite
`l2126_2404_n016`; the narrowing never mentions 'assistant' or 'user authority'. (c)
Using `assumed`"* — and the final object carries `assistant_definition` and
`user_authority` as `assumed`, each with a named inference, while the names the module
genuinely coined stayed `textual`. **The model discriminated.**

⚠️ **And this is the arm's cleanest CONFOUND, which I state rather than bury.** That
question is new. It was not in the 20-entry list, so this result is at least partly *"a
question nobody had asked yet works"* rather than *"decomposition works"*. What
decomposition contributes is that the question is **answerable at stage 3** — the model
has already committed, in stage 1 q6, to whether the narrowing establishes the concept,
so stage 3 is checking its own earlier prose rather than re-reading the span while also
holding the schema. A single-call arm can carry the same sentence; whether it would
survive alongside the other 39 KB is **untested, and is the obvious next arm** — a
one-call control with only the licence question appended. It costs ~$0.04 and it would
separate the two explanations. It was not run.

### The other layers moved in the predicted direction, and modestly

ONT fell (3→1, 3→1), DEO-1 and DEO-2 went to zero. **Entry 5's manufactured harm did
not recur**: the exclusion test fires on the vacuous case rather than creating it, which
is what it was designed for. But see §4 — the ONT gain is not free.

---

## 4. ⛔ THE HARM, AND IT IS THE ARM'S SECOND RESULT

**The floor collapsed. 10 of 13 modules are invalid, against 5 of 13 unaided.**
Every arm-G breach is one shape:

```
'answer_straightforwardly(A)' carries the variable 'A' but the body never mentions it,
so nothing binds it. The solver refuses the WHOLE FILE for an unsafe variable
```

Mechanically:

| | A unaided | G decomposed |
|---|---:|---:|
| `asserts` entries, 13 clauses | 25 | 31 |
| ⛔ **of those, with NO body at all** | **0** | **13** |
| mean `ontology` entries per module | 1.2 | **0.3** |
| mean `inputs` entries per module | 3.0 | **1.4** |

⭐ **The mechanism, stated so it is checkable.** Stage 2 settles *which act, which
status, which condition* while stage 3 settles *where the condition's predicates live*.
Stage 3's exclusion test does its job and deletes the vacuous ontology rules — `ontology`
drops from 1.2 entries per module to 0.3. **Nothing replaces them.** `inputs` falls too,
so the body predicates have no home at all, and at assembly the model resolves the
inconsistency by **dropping the body** rather than by dropping the assertion. The
condition the span attached is gone, and the module now states an unconditional duty.

**That is a conclusion-changing defect and it is worse than the one it replaced.** A
vacuous body derives the discriminating condition of every case; a *missing* body states
the duty of every case AND makes the file unsolvable. Arm G traded a wrong answer for a
non-answer.

⚠️ **This is decomposition's own failure, not an instruction's.** Separating the deontic
layer from the declaration layer is precisely what removed the pressure that keeps a
body grounded: in one pass, writing `body: response(R), repeats_prompt(R, P)` and
declaring `repeats_prompt/2` are the same thought. Split across two calls, the first
half survives and the second half is renegotiated.

### Pre-registered harms, scored

* **H-G1 — did not fire as written, and a sibling fired instead.** I named the
  `inputs` route as the danger: a document-side relation pushed into `inputs` where no
  situation supplies it. `inputs` **fell** (3.0 → 1.4). The harm went the other way —
  content left `ontology` and arrived nowhere. **The specific prediction was wrong; the
  general one (stage 3 Q1 would manufacture something) was right.**
* ⛔ **H-G2 — FIRES.** Threshold was floor failures above 11 of 17, i.e. 8.4 of 13.
  **Measured 10 of 13.** Decomposition crowds out the format.
* **H-G3 — did not fire.** No clause invented ontology machinery to satisfy the
  exclusion test; the movement was in the opposite direction.

### ⚠️ One detector was split AFTER the scores were read, and it is recorded as such

The original DEO-2 grouped `oblige` assertions on the normalised body string, so several
with **no** body landed in one group and scored as the disjunction defect. Arm G's four
DEO-2 hits were inspected and found to be all-bodiless, so DEO-2 was restricted to a
shared **non-empty** body and DEO-2b was added. **This was not pre-registered and cannot
be scored as a prediction.** G-3 is therefore reported against both definitions: 0 of 13
on the pre-registered definition, and 4 of 13 if bodiless groups count. The split is
argued in `layers.py:deo_bodiless_oblige`, and it moves the result AGAINST arm G.

---

## 5. ⚠️ THE COST, WITHOUT THE DEFECT NUMBER IN FRONT OF IT

| | arm A unaided | **arm G** |
|---|---:|---:|
| calls per clause | 1 | **4** |
| $ per clause, calls that produced a module | $0.00225 | **$0.00506 — 2.25×** |
| ⛔ $ per clause, **all-in** | $0.00225 | **$0.00837 — 3.72×** |
| ⛔ spend that bought nothing | — | **$0.04294, 39%** |
| recorded / wasted calls | 17 / 0 | **53 / 26** |

**The per-dollar criterion, as pre-registered.** G-7 predicted 1.5–2.5×, on the argument
that the 40 KB production block rides on stage 4 alone. **On recorded calls the cost
model held: 2.25×, and the block is 84% of the input.** All-in it did not: **3.72×.**

⛔ **Where the 39% went, and it is a finding about decomposition, not about billing.**
**13 of the 26 wasted calls have the identical signature: `completion_tokens` at the cap,
`content_chars` 0, `reasoning_chars` ≈ 13,600.** The model entered its reasoning channel
on **stage 2** and never left it. Stage 2 is the call that asks it to settle the deontic
layer while holding its own stage-1 prose and answering five questions about what it just
wrote — and on this model that request is unstable. `l1_170_n056` — the 18-word span with
three distinct wrong answers already on record, the clause the Opus loop needed all five
turns for — reproduced it **five times in a row at 3,200 tokens** and cleared only when
the ceiling was doubled. **The hardest clause for the critic loop is the clause that
breaks decomposition's second stage.** Raising the prose ceiling to 6,000 is free when
unused (output is billed as emitted) and was the fix.

**Against the standing comparison.** The Opus-critic loop converged in 2–4 turns, each
turn resending the full 40 KB block, **plus a frontier critic reading every draft against
the span** — a cost this ledger never sees. Arm G is cheaper than that per clause and
needs no critic. But it does not beat the unaided baseline per dollar on any layer where
the unaided baseline was already acceptable, and on the floor it is **3.7× the cost for
twice the invalid rate**. Stated plainly: **if you only care about modules that compile,
arm G is a straight loss.**

---

## 6. PREDICTIONS, SCORED

| | prediction | outcome |
|---|---|---|
| **G-1** | ≥ 1 layer moves by ≥ 5 clauses of 17 (≥ 3.8 of 13) | ✅ **DECL-1 moved 11 clauses** |
| **G-2** | DECL-1 falls to ≤ 5 of 15 clauses | ✅ **1 of 12** — the arm's headline |
| **G-3** | DEO-2 goes to 0 | ✅ **0 of 13** as pre-registered; ⚠️ 4 of 13 under the post-hoc split (§4) |
| **G-4** | ONT flat, within ±3 of arm A | ✅ 3 → 1; entry-5 manufacture did not recur |
| **G-5** | floor lands 5–9 of 17 (3.8–6.9 of 13) | ❌ **REFUTED, 10 of 13** — worse than either prior arm |
| **G-6** | ≥ 2 clauses whose stage-4 object contradicts its own stage-2/3 answer | ⚠️ **NOT SYSTEMATICALLY SCORED.** One clean case (`l2126_2404_n016`: stage 3 placed all six names in `requires`; the final object kept three and coined the rest). The budget stop cut the arm short and a full hand read is the one contaminated instrument here. Reported as unscored, not as met. |
| **G-7** | 1.5–2.5× arm A per clause | ✅ on recorded calls (2.25×); ❌ all-in (3.72×) |

### Amendments to the pre-registration, both after the first call, both recorded

1. **A word cap was added to the three prose stage prompts** after two stage-1 sends
   truncated. `_check_envelope` raises before returning, so **no stage-1 output had been
   seen either time** — the edit was made blind to any result. The prompts are otherwise
   as signed.
2. **A tolerant truncation guard was installed for the PROSE stages only**
   (`run_armg._tolerant_check`). Stage 4 still passes through the unpatched production
   guard. Grounds are in the function's docstring: the production guard's own words are
   about *"a cut-off MODULE"*, and discarding a paid scratch answer removes the record of
   how it was short without recovering the money. **2 truncated prose stages were kept and
   are flagged in the stage records.** This is not a floor being lowered — the floor that
   decides `outcome` and `breaches` ran unmodified on every stage-4 object.
3. Transport retries (HTTP 503, read stalls) were added for all stages; content failures
   (empty / reasoning loop) are still refused on stage 4. **10 in-process retries** across
   the arm. together.ai returned 503s and multi-minute stalls throughout the window.

---

## 7. WHICH LAYER ARGUES FOR A SCHEMA CHANGE

The brief's question was: *the layer decomposition fails to help is the one that needs a
schema change rather than a process change.* The answer this arm gives is the opposite of
the one it was set up to find, and it is the more useful one.

* ⭐ **The DECL layer does NOT need a schema change.** `schema.py:366` already offers
  `assumed` + `inference`, and the model reached it as soon as it was asked, at the moment
  it could answer. Eighteen self-citations in each of two prior arms looked like a schema
  gap and were an **attention** gap. **The schema-change argument for the borrowed-gloss
  class is withdrawn on this evidence** — pending the one-call control in §3, which could
  still show that the question, not the split, is doing the work.
* ⛔ **The layer that now argues for a schema change is the one this arm BROKE: the join
  between an assertion and its body.** Nothing in the schema requires an `asserts` entry to
  carry a body, and nothing requires the predicates in a body to be reachable. So a module
  can satisfy every field-level rule and still say *"the assistant is obliged to answer
  straightforwardly"* with the span's condition deleted, and the only thing that catches it
  is clingo refusing an unsafe variable — **a syntax error standing in for a semantic one.**
  A schema that made the condition a required, checked relation between `asserts` and the
  declaration fields would have made arm G's 13 bodiless assertions impossible to write,
  and would have caught the vacuous ones in both prior arms by the same rule.

---

## 8. WHAT THIS DOES NOT SHOW

* **n = 13, cells of 0–12, one model, one draw.** No rate here is separated from noise.
  The claims that carry the verdict need no rate: 18/18 → 1/18 on a mechanically counted
  field, and 0/25 → 13/31 bodiless assertions.
* **The DECL result is confounded** with a question no prior arm asked (§3). The control
  is named, costed and not run.
* **Four clauses are missing** and they were not chosen at random — they are the ones the
  workers reached last, after the provider degraded. `l2821_3040_n017` and
  `l3239_3382_n004` carry two of the sharper historical defects, so their absence removes
  two hard cases from arm G and **flatters it**.
* **The floor comparison is the most robust cell here** (mechanical, paired, large
  effect) and it is the one that goes against the arm.
* **Contamination:** I read all 17 historical adjudications and both prior RESULT files
  before writing anything. The layer table is entirely mechanical and carries none of it.
  G-6 is the only judgement-bearing prediction and it is reported as **unscored**.

---

## 9. WRITE AUDIT AND RECONCILIATION

Everything this arm produced is under `_debug_gen11/decompose_arm/`. Nothing under
`runs/`, `translation_sample/runs/`, `repair_graveyard/`, `prompt/`, `schema.py`,
`resolve_runs/graph_v2/`, or any other agent's `_debug_gen11/*_arm/` directory was
written. No git was run. `usage.jsonl` was appended by `providers._append_usage`, as
every paid call in this repo does.

**Reconciled from this arm's own stage records first** (`reconcile.py`): 53 recorded
calls, $0.06580. The wasted calls are then read off the shared ledger rather than kept in
a constant a crash could lose — arm G is the only arm in this window sending a prompt
under 8,000 tokens, and a prose-shaped row whose `content_chars` matches no stage record
is a call that produced nothing: **26 calls, $0.04294.** **Total $0.10875** against a
$0.115 self-cap and the brief's $0.120. The gate refuses at the stage that would cross;
the arm stopped at 13 clauses because it would have.

⚠️ Several agents append to `usage.jsonl` concurrently and its tail contains their rows.
It is used here only as the cross-check the brief asks for, never as the source of the
recorded figure.

**Signed** — adjudicator, arm G.
