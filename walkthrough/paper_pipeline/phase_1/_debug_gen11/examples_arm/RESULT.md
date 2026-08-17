# RESULT — arm C: does the same content TRANSFER as WORKED EXAMPLES?

**Answer: PARTLY, and the part that moved is the one no prose ever addressed.**

This is **not a third null and not a transfer.** It is the first arm in the series to move
a measured class, and it moved one by a lot: a borrowed `NEEDS` gloss stamped
`licence: textual, cites: <this node>` — a *manufactured citation*, which `00_task.md` calls
*"the single worst failure available here"* — ran at **15 of 15 clauses in arm A and 15 of
15 in the prose arm, identically**, and in arm C it is **3 of 15**. By glosses, **24 → 3**.
That is scored mechanically from the JSON and carries none of my judgement.

Everything the experiment exists to move still did not move. **0 of 17 defect-free**
(baselines 0/17, 0/17). **15 of 17 carry a conclusion-changing defect** (baselines ≈16/17,
16/17). And **4 of the 5 clauses whose frozen defect was fixed are the demonstration's own
node** — the examples worked where the prompt showed the clause, which is the in-sample
ceiling, not generalisation.

⚠️ **MEASURED at n = 17, single-digit cells throughout.** No rate below is statistically
separated from noise. The claims that need no rate are the ones the verdict rests on.

**Pre-registration:** `PREREG.md`, signed before the first call, with the six harm branches
and the baselines for the mechanical metrics measured and printed **before** signing.
**Spend: $0.03656** measured, 17 live calls, cap $0.08.

---

## 1. THE PROMPTS

| | system block | sha256 |
|---|---:|---|
| **arm A** (production) | 39,959 | `3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c` |
| **arm B / in-sample** (prose list) | 53,426 | `045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917` |
| **arm C** (this arm) | **50,179** | **`b5af1129958a631347c506bfad4fe03f74b0c0cc177fd1b24277727886f68af5`** |

`run_armc.py` refuses to send unless **both** gates hold, and it printed them:

```
system block: 50179c  sha256 b5af1129...f68af5
VERIFIED: first four files == arm A (3a66c5f5...4c34c); whole block == the frozen arm C sha in PREREG.md.
```

The four production files were copied into `promptsC/` and each copy's sha256 checked
against its original (`0463449d`, `92dbd355`, `a0c12943`, `7a88183e` — byte-identical to the
copies arm B sent). `armC == armA + "\n\n---\n\n" + 40_worked_examples.md` was checked as a
string equality. Appended block **10,214 chars** against arm B's 13,466.

⛔ Nothing under `prompt/`, `schema.py`, `resources/`, `runs/`, `translation_sample/runs/`,
`repair_graveyard/` or `resolve_runs/graph_v2/` was written. No git was run. Every byte this
arm produced is under `_debug_gen11/examples_arm/`, except `usage.jsonl`, appended by
`providers._append_usage` as every paid call in this repo does.

### The block: six before/after pairs, and the validation gate they had to pass

`node_worked_example.md` was found stale on five counts and one of its exemplars violated the
file's own contract. So `validate_examples.py` ran every fragment's source module through
`schema.validate_all` + `checks.run_checks` before the block shipped, and grepped the block
for eleven literal fragment strings so a later edit could not drift from the bytes on disk.
**It passed, exit 0** (`VALIDATION.txt`): **all six ✅ exemplars `translated`, 0 breaches,
note-severity findings only**; all eleven fragments present. ⚠️ **It was not sufficient — see
§7, where one of my own exemplars is shown to have shipped a defect the gate cannot see.**

**Judgement call — N1 (entry 5) was INCLUDED, repaired, and the repair is stated.** The
in-sample arm measured entry 5 *manufacturing* a defect class: obeyed, it turned harmless
inert constants into **vacuous bodied rules**. ⛔ Shipping its content as a two-way example
(constant ⛔ → bodied rule ✅) was **rejected by name** in `PREREG.md` §3. Example 5 is
instead **three-way** and names the harmful middle option as harmful: ⛔ arity-0 constant,
⛔⛔ `no_moral_ambiguity(S) :- scenario(S)` (the in-sample arm's own output for that node),
✅ arity 1 in **`inputs`** with the act's variable linked. The substantive fix is that the
destination is `inputs`, not `ontology`. **§7 shows the repair worked on its own node and
failed on the two other clauses where the class was live.**

---

## 2. ⭐ THE MECHANICAL READOUTS — no judgement of mine enters these

Baselines measured and printed in `PREREG.md` §5 **before** the first call.

### Example 6 — a borrowed `NEEDS` gloss cited to this node

Counted over the **15 clauses that carry a `NEEDS` name**: a `concepts` entry whose name is
exactly a NEEDS name, `licence: textual`, `cites` equal to this node's own id.

| | arm A t1 | prose arm | **ARM C** |
|---|---:|---:|---:|
| clauses with ≥ 1 | **15 of 15** | **15 of 15** | **3 of 15** |
| glosses | 24 | 24 | **3** |

⭐ **This is the largest movement measured in any of the three arms, and it is the class no
entry in the 20-entry list ever named.** On 12 of 15 clauses the licence became `assumed`
with a named inference; on most of those the gloss also became *the NEEDS block's own
words* rather than a rewrite from memory — a second improvement the metric does not count.

The three residuals are `l1001_1107_n005`, `l1368_1541_n019` and `l1707_1973_n006`, each
with one NEEDS name still self-cited. On two of the three the gloss is nonetheless now the
NEEDS wording; only `l1001_1107_n005` keeps the full historical defect (invented gloss *"the
highest authority level in the document"*, self-cited).

⚠️ **What this win is measured against.** No schema rule fixes the licence of a borrowed
concept. The class is defined by *this project's* adjudication: the converged modules of
record use `assumed` with exactly this inference, and both prior arms charged the self-cited
form as a manufactured citation. So arm C moved a class **against the project's own
standard**, not against a machine check — stated so a reader can discount it if they reject
the standard.

### Example 3 — closure values

| | arm A t1 | prose arm | **ARM C** |
|---|---:|---:|---:|
| clauses with ≥ 1 `cepa` | 14 of 17 | **6 of 17** | 11 of 17 |
| clauses with ≥ 1 `unclear` | 0 of 17 | **8 of 17** | 4 of 17 |

⚠️ **The prose arm beat arm C here**, and `PREREG.md` §5 said in advance that this class
could not separate form from content because prose entry 2 was the in-sample arm's one
measured transfer. It is reported and **not counted toward C4**. What it does show: a single
demonstration is *weaker* than a prose rule at moving a single named field value.

### The harm branches, scored mechanically where possible

| | threshold | measured | |
|---|---|---|---|
| **X1** PROVIDES/coined name demoted to non-`textual` | ≥ 3 clauses | **0 of 5** | ✅ did not fire |
| **X3** negation-as-failure in any body | ≥ 5 of 17 | **4 of 17** (arm A 2, prose 2) | ⚠️ **near miss — see §7** |
| **X5** an example's content token on a foreign clause | ≥ 3 drafts | **0** | ✅ did not fire |
| **X2** `unclear` where the span settles the question | ≥ 3 clauses | **0 of 4** | ✅ did not fire |
| **X4** a span-defined condition deleted into `inputs` | ≥ 3 clauses | **0** | ✅ did not fire |

### Field mix, floor, length — all paired on the same 17

| field, mean per module | arm A | prose | **ARM C** |
|---|---:|---:|---:|
| `asserts` | 2.00 | 2.00 | **1.94** |
| `ontology` | 1.18 | 1.29 | **1.00** |
| `acts` / `concepts` / `inputs` / `requires` / `claims` | 1.53 / 5.47 / 2.88 / 1.53 / 2.71 | 1.82 / 5.76 / 2.88 / 1.41 / 3.00 | 1.71 / 5.65 / 3.18 / 1.41 / 2.71 |

⭐ **The `asserts`/`ontology` mix is a NULL a third time.** Arm B claimed a shift
(`asserts` −35%, `ontology` +50%) against a historical control; pairing refuted it and it was
retracted. Arm C, paired, moves `asserts` by 0.06 and `ontology` by 0.18 entries per module.
**Neither prose nor demonstrations move the field mix on this corpus.**

| | arm A | prose | **ARM C** |
|---|---:|---:|---:|
| floor failures (`outcome != translated` or breaches > 0) | 7 of 17 (41%) | 6 of 17 (35%) | **4 of 17 (24%)** |
| mean raw output | 3,645 | 3,803 | **3,809** |

Floor failures fell to 4 of 17 — the lowest of the three arms, and **not** separable from 7
and 6 at n = 17. **R-f predicted 5–9 and was wrong in the safe direction.** A 26% longer
prompt again produced no longer output.

---

## 3. THE PER-CLAUSE TABLE

`✅` the clause's frozen historical defect did not recur · `⛔` it recurred, verbatim or in
mechanism · `⚠️` it did not recur but an equally conclusion-changing defect took its place.
Frozen defects are the ones fixed in `../list_in_prompt_insample/PREREG.md` §4.

| # | clause | frozen defect | **arm C** | CC | of which an EXAMPLE demonstrates | floor |
|---|---|---|:--:|---:|---|---|
| 1 | `l1001_1107_n005` | `rule_under_heading/2` in `inputs`; the one rule cannot fire | ⛔ **byte-identical** | 3 | ex 5, ex 6 | clean |
| 2 | `l1368_1541_n019` | `S` names two things; middle `oblige` cannot fire | ⛔ **worse** | 1 | ex 5 | clean |
| 3 | `l1707_1973_n006` | three of four behaviours reach no rule | ⚠️ **regression** | 2 | — | 2 br |
| 4 | `l1707_1973_n022` | vehicle's exception imported into the tenor by NAF | ⛔ mechanism | 2 | — | 1 br |
| 5 | `l171_426_n022` | `higher_level_instruction` hardcoded to root | ⛔ mechanism | 2 | — | clean |
| 6 | `l1_170_n056` | exception unattached: `oblige` + three `permit refuse` | ✅ **FIXED** | **0** | — | clean |
| 7 | `l2126_2404_n016` | coextensive `ontology` heads on one body | ✅ **FIXED** | 1 | ex 3 | clean |
| 8 | `l2474_2554_n004` | `third_party_interaction(A) :- on_behalf_of_user(A)` inverts the conjunction | ⛔ **byte-identical** | 3 | — | 4 br |
| 9 | `l2821_3040_n017` | unconditional manner duty; the default deleted | ⛔ **and via ex 5's own harm** | 2 | ex 5 ×2 | clean |
| 10 | `l3147_3238_n003` | three `oblige` on one body for an *"or"* | ⛔ **verbatim** | 2 | ex 3 | clean |
| 11 | `l3239_3382_n002` | `overstepping(A)` head in its own body | ✅ **FIXED** | 2 | ex 5 | 3 br |
| 12 | `l3239_3382_n004` | two body-less `ontology` entries; `S` unlinked | ⚠️ **relocated** | 2 | ex 5 | clean |
| 13 | `l3596_3876_n009` | three glosses restate their own names | ⛔ **one word changed** | 1 | ex 1 | clean |
| 14 | `l3877_3953_n014` | document relation in `inputs`; the node provides nothing | ⛔ isomorphic | 1 | ex 5 | clean |
| 15 | `l4252_4482_n005` | chain inverts the clause into a blanket accent ban | ⚠️ **substituted** | 3 | — | clean |
| 16 | `l4252_4482_n016` | `prefer` on the acts the span says to avoid | ✅ **FIXED** | 1 | — | clean |
| 17 | `l699_796_n012` | modality survives on only one conjunct | ✅ **FIXED** | **0** | — | clean |
| | **TOTAL** | | **5 ✅ / 3 ⚠️ / 9 ⛔** | **28** | **11 of 28 (39%)** | **4 invalid** |

Prose arm, same 17: 2 ✅ / 6 ⚠️ / 9 ⛔.

---

## 4. SCORED AGAINST THE PRE-REGISTRATION

| criterion | "transfer" threshold | measured | |
|---|---|---|---|
| **C1** defect-free turn-1 drafts | ≥ 5 of 17 | **0 of 17** | ❌ |
| **C2** conclusion-changing rate | ≤ 8 of 17 | **15 of 17** | ❌ |
| **C3** CC defects an example demonstrates | ≤ 25% | **39%** (11 of 28) | ❌ **but see the confound** |
| **C4** classes meeting the fall threshold | ≥ 3 of 6 | **2 of 6** by the letter | ❌ **and the letter is doing work — see below** |
| **X1–X5** harm branches | any fires | **none fires** | ✅ |

**NULL was defined as C1 ≤ 1 *and* C2 ≥ 13 *and* C4 < 2 of 6.** C1 and C2 are met; **C4 is
not** — 2 of 6 is not fewer than 2. **So this arm is not a null by its own pre-registration,
and it is not a transfer.** It lands in the band `PREREG.md` §5 called PARTIAL, and it is
reported as such rather than rounded toward either verdict.

### ⚠️ C4, class by class, with the pre-registration's letter applied against my own arm

The threshold was *"falls by at least half AND to ≤ 2"*.

| class | applicable in arm A | arm C | halves? | ≤ 2? | meets |
|---|---:|---:|:--:|:--:|:--:|
| **ex 6** borrowed-gloss licence *(mechanical)* | **15** | **3** | ✅ | ❌ | ⛔ **NO** |
| **ex 1** gloss restates its name *(judgement)* | 4 | 2 | ✅ | ✅ | ✅ |
| **ex 4** "unless" arm as permission *(judgement, n=1)* | 1 | 0 | ✅ | ✅ | ✅ |
| **ex 2** head-in-own-body / outside the narrowing | 3 | 2 | ❌ | ✅ | ❌ |
| **ex 5** condition placement / vacuous body | 5 | 4 + 1 new | ❌ | ❌ | ❌ |
| **ex 3** closure *(excluded from C4 in advance)* | 14 | 11 | ❌ | ❌ | — |

⭐ **The single most important line in this table is that ex 6 FAILS C4 on the `≤ 2` leg
while falling 15 → 3.** I wrote that threshold before seeing anything and I am scoring it as
written. But the honest statement of what happened is: **the one class scored mechanically,
free of my contamination, and untouched by 13.5 KB of prose across two arms, fell by 80% when
shown as one before/after pair.** A reader who thinks `≤ 2` was the wrong second leg should
read C4 as **3 of 6 and a PARTIAL TRANSFER verdict**; a reader who holds me to what I signed
reads 2 of 6. Both readings are in this file and I am not choosing between them.

⚠️ **The other two passing classes are mine to judge and both are weak.** ex 4's applicable
set is **one clause, and it is the example's own node**. ex 1's is four clauses judged by me,
and it "passes" while `l3596_3876_n009` — the clause whose frozen defect *is* ex 1's class —
changed *"the **state** of possessing vast knowledge…"* to *"the **situation** of possessing
vast knowledge…"*, i.e. **one word**, and still restates its own name. That is the in-sample
arm's "minus two characters" finding reproduced against a demonstration instead of a rule.

### ⚠️ C3's 39% is not comparable to 87% and 83% without a correction

Arm B's block named **20** classes; arm C's shows **6**. Fewer classes named means fewer
defects fall inside them, so 39% partly measures *coverage*, not *transfer*. `PREREG.md` §3
named this confound in advance and moved the verdict to C4 for exactly this reason. **The
uncorrected number is reported because it was pre-registered; it should not be read as the
mechanism claim succeeding.**

### Predictions scored

| | prediction | outcome |
|---|---|---|
| **R-a** | C1 = 0 or 1 of 17 | ✅ **0 of 17** |
| **R-b** | C4 succeeds on ex 6 and nothing else | ⚠️ **half right, and the interesting half.** Ex 6 produced by far the largest movement — and misses C4's second leg by one clause. Ex 1 and ex 4 "pass" on judgement and n=1 |
| **R-c** | C3 fails | ✅ 39% > 25%, with the confound above |
| **R-d** | X5 fires | ❌ **REFUTED.** Not one example token crossed to a foreign clause |
| **R-e** | X1 does not fire | ✅ **0 of 5.** The one-line guard in ex 6 held |
| **R-f** | floor failures 5–9 of 17 | ❌ **4 of 17**, wrong in the safe direction |

---

## 5. THE DECISIVE CELLS — no rate needed

### ⭐ `l1_170_n056` and `l2126_2404_n016` and `l3239_3382_n002` — the examples' own nodes

All three are ✅. On `l1_170_n056` the three manufactured `permit refuse_request(R)` entries
are gone and the module is the converged answer's structure: one `oblige`, the exception in
the body, `closure: unclear`. On `l2126_2404_n016` there is **no `ontology` block at all** —
the conditions are arity-1 in `inputs`, `answer_in_scenario(A, S)` links the act's variable,
and the three asserts sit on three *different* acts, so the oblige/forbid collision on one
act is gone. On `l3239_3382_n002` the circular `overstepping(A) :- …, overstepping(A)` is
gone, `overstepping/1` is in `inputs`, and the `forbid` carries `licence: assumed` with the
narrowing inference **verbatim from the example**.

⚠️ **This is the ceiling, not generalisation.** Four of the five fixes are on a node the
prompt shows. The in-sample arm established that quoting a clause's own bytes buys nothing
for *prose*; arm C shows it buys a great deal for a *demonstration*. **That difference is
real and it is the strongest support the owner's hypothesis gets here.** It is also the
narrowest possible support: it does not travel.

### ⛔⛔ `l2821_3040_n017` — example 5's own harm, reproduced against example 5

Example 5's ⛔⛔ arm shows `no_moral_ambiguity(S) :- scenario(S)` and says in the caption that
such a body *"derives the span's discriminating condition of **every** case, so the module
concludes **more** than the span, in the dangerous direction."*

This module emitted, for *"**By default**, the assistant should express uncertainty
naturally"*:

```
natural_uncertainty_expression(A) :- assistant_definition(A).
oblige express_uncertainty_naturally(A) :- assistant_definition(A), natural_uncertainty_expression(A).
```

**Every assistant is a natural uncertainty expression**, so the guard is vacuous and the duty
is unconditional — and *"by default"* is gone for the third arm running. `outcome:
translated`, **0 breaches**. In production this module ships. **The prose entry manufactured
this class; the repaired three-way demonstration did not prevent it.**

### ⛔ `l2474_2554_n004` and `l3147_3238_n003` — byte-identical recurrences the block does not cover

`third_party_interaction(A) :- on_behalf_of_user(A)` is **identical to arm A's**, and it
inverts the span's conjunction so the paragraph governs every interaction. `l3147_3238_n003`
emitted three `oblige` on the identical body `assistant_definition(A),
lacks_sufficient_confidence(A)` for a span reading *"use a tool …, hedge …, **or** explain"* —
**verbatim across all three arms.** Neither class is in arm C's six. That is the cost of
Judgement Call 1 (six examples, not twenty) and it is exactly what the trade predicted.

### ⛔ `l1707_1973_n006` — a REGRESSION, and it is arm C's worst cell

Arm A `forbid respond_with(R)` on the definitive-diagnosis arm. Arm C:

```
prefer respond_with(R) :- good_response(R).   read_back: "…is preferred"
prefer respond_with(R) :- bad_response(R).    read_back: "…is dispreferred"
```

**The same status on the same act for both poles** — the compiled program cannot tell GOOD
from BAD, which is the one thing the example exists to say — plus `status` and `read_back`
disagreeing on the second. The prose list carried both an entry for this (tail P10) and an
entry for polarity (12); **arm C dropped both, and the clause got worse than unaided.** A
narrower block is not a free choice.

---

## 6. WHAT DID *NOT* NEED AN EXAMPLE

⭐ **`l4252_4482_n016` fixed itself.** Its frozen defect — `prefer` on the three acts the
span says to avoid, with read-backs that negate them — was the **sharpest cell in the entire
in-sample arm**: reproduced 3 of 3 against an entry printing the remedy in the clause's own
words. Arm C emitted `forbid repeat_user_prompt(R)`, `forbid use_redundant_phrase(R)`,
`forbid use_redundant_idea(R)`, with bodies linked and read-backs agreeing. **No arm-C
example covers polarity.** ⚠️ It over-corrected: *"generally minimize"* is a gradient and
`forbid` is too strong, which is a new conclusion-changing defect in the strict direction.

⭐ **`l699_796_n012` fixed itself** too — *"could cause serious side effects"* preserves the
modality on both conjuncts — and no example covers modality.

**Two of the five fixes are unattributable to anything in the block.** At n = 17 that is the
right size for run-to-run variation, and it is the reason C4's per-class comparison, not the
fix count, is the metric the verdict rests on.

---

## 7. ⛔ HARM: NO BRANCH FIRED, AND ONE THING HAPPENED THAT NO BRANCH NAMED

All five pre-registered harm branches came back clean. Two near-misses and one finding
against myself:

### ⚠️ X3 near-miss — negation-as-failure doubled, and the block is why

**Measured: 2 of 17 → 2 of 17 → 4 of 17.** X3's threshold was ≥ 5 and it did not fire.
But of arm C's four, **three are decisive defects**: `l1707_1973_n022`
(`not explicit_policy_allowance(P)`, importing the *manual's* policy exception into the
*assistant's* prompts, which the tenor never states), `l2474_2554_n004`
(`not instructed_by_user(A, I)` with an unsafe variable), and `l4252_4482_n005`
(`not exaggerated_portrayal(A), not stereotype(A)`, so silence licenses the caricature).
The fourth is `l1_170_n056`, where it is correct.

⛔ **The only NAF in the block is example 4's ✅ side.** It is the adjudicated answer of
record and `PREREG.md` §5 flagged the risk in advance and did not alter it. **X5 as written
was refuted — no token crossed — but the FORM crossed.** A demonstration teaches a shape, and
a shape does not carry the polarity condition that decides when the shape is safe. That is a
real mechanism, it was not what I pre-registered, and it is the clearest candidate for
demonstration-induced harm in the arm. **INFERRED, not measured:** three defective NAF bodies
against a baseline of one is not separable from noise at n = 17.

### ⛔ A defect in MY OWN exemplar, copied verbatim, that the validation gate could not see

Example 2's ✅ fragment ends:

```json
"status": "forbid", "act": "overstep(A)", "body": "assistant_definition(S), overstepping(A)"
```

`S` is an **unlinked singleton** — it binds nothing and ties the assistant to nothing. It is
in the converged module of record, it passed `schema.validate_all`, it passed
`checks.run_checks` with note-severity findings only, and it passed my eleven-string
fragment check. **`l3239_3382_n002` reproduced it byte-for-byte.**

This is the `node_worked_example.md` failure happening again, to me, one arm after I built a
gate specifically to prevent it: **a demonstration ships whatever its source module contained,
and the floor does not flag an unlinked singleton in an assert body.** The gate as built
verifies that an exemplar is *legal*; it cannot verify that it is *good*. That is a finding
about the gate, not about the model, and it belongs in whatever comes next.

### ⚠️ The other classes ex 5 was meant to reach

Ex 5 fixed its own node and produced a **new** vacuous bodied rule on
`l3239_3382_n002` (`avoid_overstepping(S) :- section(S)` — every section is the
avoid-overstepping section, which vacates this node's only `PROVIDES` obligation) and failed
to prevent one on `l2821_3040_n017`. **Vacuous-body count across the arm: 3.** The in-sample
arm's entry-5 harm was ≥ 4. **Flat.** The repaired demonstration did not make it worse and
did not make it better.

---

## 8. ⚠️ CONTAMINATION, AND WHICH WAY IT CUTS

`PREREG.md` §7 disclosed two biases in advance and both are live. **I did not adjudicate
blind and I do not claim to.** I read all 17 historical adjudications and both prior RESULT
files, and **I chose and wrote the examples**, so I have a stake in their working.

* ⭐ **The mitigation is the one that matters and it held.** The claim the verdict leans on —
  ex 6, 15/15 → 3/15 — is computed from the JSON by a script whose baseline was printed
  before the first call. So is the closure table, the NAF count, the field mix, the floor
  rate and X1/X5. **None of them passes through my reading.** The classes where my judgement
  is the only evidence (ex 1, ex 2, ex 4, ex 5's applicability sets, and the 28 CC counts)
  are marked as such in §4, and each of them is *weaker* than the mechanical ones.
* **Direction of the bias on the fix count.** Knowing each clause's frozen defect biases me
  toward finding it again, so **the 9 recurrences are the number to distrust and I lean on
  them least**; but knowing I wrote the examples biases me toward calling their nodes fixed,
  so **the 5 ✅ are the number to distrust in the other direction.** The two biases point
  opposite ways on the two halves of the same table, which is worth stating and does not
  cancel.
* **What cannot be fixed:** one adjudicator, no second reader, no answer key, n = 17, cells
  of 1–3. **Novel defects got less attention than predicted ones by construction.**

---

## 9. VERDICT

**The owner's hypothesis is partly borne out, on a much narrower footing than it was posed.**

1. ⭐ **Demonstrations moved a class that prose could not.** The borrowed-gloss licence
   failure sat at **15 of 15 in both prior arms**, was named by **none** of the twenty
   entries, and fell to **3 of 15** on one before/after pair. Mechanical, contamination-free,
   and by far the largest movement in the series. **This refutes the strong form of the
   in-sample arm's conclusion** — *"a prompt cannot reach them, not at any level of
   specificity"* — for at least one real class.
2. ⛔ **But it did not move the numbers the experiment exists to move.** 0 of 17 defect-free,
   against 0 and 0. 15 of 17 conclusion-changing, against ≈16 and 16.
3. ⛔ **The fixes are concentrated where the prompt shows the clause.** Four of five ✅ rows
   are the demonstration's own node. Two more clauses fixed themselves with no example at
   all. **On foreign clauses the demonstrations behaved much like the prose did.**
4. ⛔ **Narrowing the block has a measured price.** Two byte-identical recurrences and one
   outright regression (`l1707_1973_n006`, where dropping the polarity and GOOD/BAD entries
   made the clause worse than unaided) all sit in classes the six examples do not cover.
5. ⚠️ **A demonstration teaches a shape, and a shape carries no side conditions.** NAF
   doubled, three of four instances are defects, and the block's only NAF is my ✅ fragment.
   X5 as written was refuted; the mechanism it was pointing at is real and is not token-level.
6. ⛔ **And one of my own exemplars shipped an unlinked singleton that the validation gate
   passed and the model copied verbatim.** A gate that proves an exemplar *legal* does not
   prove it *good*, and `node_worked_example.md`'s history says this is the failure mode that
   recurs.

⭐ **What follows.** The transferable shape is now measured twice and it is the same shape
both times: **a single named field value, decidable without re-reading the span.** Prose
entry 2 moved `cepa`→`unclear`; example 6 moved a licence. Everything else in both arms —
unlinked and vacuous bodies, a `status` field with no negative pole, disjunction-as-
conjunction, a document-side relation with nowhere legal to live, NAF where the schema offers
nothing else — **did not move for prose and did not move for demonstrations.** Those are
places where the model wrote the only thing the format allowed, or a thing the format does
not check. **The argument still moves to the schema and the graph** — but the licence result
says the prompt is not finished as a lever, and the next thing to try is the *smallest
possible* demonstration of a *single field value*, not another block.

⚠️ **What this does NOT show.** It does not show demonstrations beat prose in general: on
closure, the one class both arms addressed, **the prose entry beat the demonstration** (8 of
17 clauses with `unclear` against 4). It does not establish a rate for anything. And it does
not show a larger example block would do better — the one thing measured about size here is
that dropping two classes cost one regression.

⛔ **Nothing in `promptsC/` was tuned, before or after. No second variant was run.** A second
variant would have to be pre-registered as such, and both reported.

---

**Signed.** — adjudicator, 2026-08-16. Spend **$0.03656** of a $0.08 cap, 17 live calls,
reconciled against the per-clause `_armc_cost_usd` records in `out/*.json`.

⛔ **Write audit.** The only file this arm touched outside `_debug_gen11/examples_arm/` is
`usage.jsonl`. Nothing under `runs/`, `translation_sample/runs/`, `repair_graveyard/`,
`prompt/`, `schema.py` or `resolve_runs/graph_v2/` was written; no git was run; no branch was
switched.
