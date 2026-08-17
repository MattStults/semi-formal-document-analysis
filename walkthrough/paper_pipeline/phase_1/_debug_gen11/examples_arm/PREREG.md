# PREREG — arm C: the same content as WORKED EXAMPLES

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after the
first response arrives; corrections go in `RESULT.md`, marked as such.

---

## 1. THE HYPOTHESIS AND WHY IT DESERVES A THIRD SHOT

Two arms have failed.

* **Arm B, out-of-sample** (`../list_in_prompt/RESULT.md`): 0 of 15 defect-free, 14 of 15
  conclusion-changing, **87%** of CC defects named by an entry the translator held.
* **In-sample** (`../list_in_prompt_insample/RESULT.md`): 0 of 17 defect-free, 16 of 17
  conclusion-changing, **83%** named — on the clauses the list was measured on, where the
  prompt quotes the clause's own bytes. Specificity bought nothing. On one clause the
  **only** change between arms was deleting the two characters the entry's own sentence
  quotes.

The owner's hypothesis is that the failing variable is **form, not content**: the review
list is twenty prose rules and zero demonstrations, and this project has measured, in this
very prompt, that a model **disregards prose passages while following a concrete
demonstration** (`../routing_criterion/`). Arm C converts the highest-evidence content into
before/after demonstrations and changes nothing else.

## 2. THE DESIGN — one variable, paired, same 17

**Same 17 clauses** as the in-sample arm, so arm C is paired against **two** baselines on
identical material: arm A's unaided turn-1 drafts (`../ds_opus_loop/out/<id>.turn1.raw.json`)
and the in-sample prose arm (`../list_in_prompt_insample/out/<id>.json`).

**Same placement, same protocol.** The block is appended last, in the exact slot arm B gave
`40_review_list.md`. Turn 1 only, no feedback, 17 calls in parallel, same model, same
temperature.

| | system block | sha256 |
|---|---:|---|
| **arm A** (production) | 39,959 | `3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c` |
| **arm B / in-sample** (prose list) | 53,426 | `045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917` |
| **arm C** (this arm, demonstrations) | **50,179** | **`b5af1129958a631347c506bfad4fe03f74b0c0cc177fd1b24277727886f68af5`** |

**VERIFIED before signing:** the four production files were copied into `promptsC/`, each
copy's sha256 checked against its original (`0463449d`, `92dbd355`, `a0c12943`, `7a88183e` —
byte-identical to arm B's copies), and the first four assemble to **39,959 chars, sha256
`3a66c5f5…`**, i.e. arm A exactly. `armC == armA + "\n\n---\n\n" + 40_worked_examples.md`
was checked as a string equality. Appended block: **10,214 chars** (arm B's was 13,466).

⛔ Nothing under `prompt/`, `schema.py`, `resources/`, `runs/`, `translation_sample/runs/`,
`repair_graveyard/` or `resolve_runs/graph_v2/` is written by this arm.

## 3. WHAT IS IN THE BLOCK, AND THE FOUR JUDGEMENT CALLS

Six before/after pairs. Every ⛔ fragment is a verbatim slice of a real turn-1 draft on
disk; every ✅ fragment is a verbatim slice of that same module after it converged.

| # | class demonstrated | prose entry it replaces | node |
|---|---|---|---|
| 1 | a gloss that re-spaces its own name | **1 (P8)**, rank 1 | `l1368_1541_n019` |
| 2 | head in its own body + content outside the narrowing | **1b (P8), 4 (P6)**, ranks 1 & 4; the traceability family (**3 / N10**, rank 3) | `l3239_3382_n002` |
| 3 | a `cepa` closure deciding what the span left open | **2 (N7)**, rank 2 | `l1368_1541_n019` |
| 4 | an "unless" arm is a hole, not a permission | **2 (N7)**, rank 2 | `l1_170_n056` |
| 5 | where a condition about the CASE lives | **5 (N1)**, rank 5 — **repaired, see below** | `l2126_2404_n016` |
| 6 | a borrowed `NEEDS` gloss is not yours to cite | ⭐ **NO ENTRY NAMES THIS** | `l1707_1973_n022` |

**Call 1 — six examples, not twenty.** The prompt is already 39,959 chars and the 13.5 KB
prose list failed twice. `ORDERING.md` measures five entries carrying 48 of 82 findings;
those five are covered by examples 1–5. Fewer and sharper is the version of the hypothesis
worth testing: if a demonstration works at all it should work at six.

**Call 2 — the examples REPLACE the prose; no review-list text is included.** Grounds: with
both in the prompt the format variable is unidentifiable, and prose has been measured at
0/17 twice, so it can only muddy. ⚠️ **The cost is stated, not hidden:** arm C's block is
narrower in coverage than arm B's, so an arm-C-vs-arm-B difference confounds FORM with
BREADTH. **Mitigation, fixed here:** the verdict turns on the **per-class** comparison in
§5 (C4), where arm A, the prose arm and arm C are compared on the *same six classes* — that
comparison is breadth-free.

**Call 3 — N1 (entry 5) is INCLUDED, but only in a repaired form, and the repair is stated.**
The in-sample arm measured entry 5 *manufacturing* a defect class: obeyed, it turned
harmless inert constants into **vacuous bodied rules** (`no_moral_ambiguity(S) :- scenario(S)`
makes a clause scoped to *"scenarios where there's no moral ambiguity"* govern **all**
scenarios). Entry 5's prose cannot stop this because its headline instruction *is* "prefer
the bodied rule over a coined constant."

⛔ **Rejected by name: shipping entry 5's content as a two-way example** (inert constant ⛔ →
bodied rule ✅). That is precisely the demonstration that manufactures the harm, and a wrong
demonstration is more harmful than wrong prose because demonstrations are what the model
follows.

✅ **The repair, stated so it is checkable.** Example 5 is a **three-way** demonstration and
names the harmful middle option as harmful: ⛔ the arity-0 constant (inert — concludes
less), ⛔⛔ the bodied typing rule that the in-sample arm actually emitted (concludes more,
in the dangerous direction), ✅ the converged answer — **arity 1, declared in `inputs` as a
fact the situation supplies, with the act's variable linked to the scenario via
`answer_in_scenario/2`.** The substantive fix is that the destination is `inputs`, not
`ontology`; entry 5's prose says the opposite in its headline and says the true thing only
in its last sentence. All three fragments are on disk (the ⛔⛔ one is the in-sample arm's own
output for this node).

**Call 4 — the borrowed-gloss licence failure IS included (example 6), though no entry names
it.** Measured mechanically before signing: **15 of the 15 clauses that carry a `NEEDS` name
give at least one borrowed gloss `licence: textual, cites: <this node>` — in arm A's turn-1
drafts AND in the prose arm, identically.** `00_task.md` calls a manufactured citation *"the
single worst failure available here"*. It is the largest measured class, it is at 100% in
both arms, and nothing has ever been tried on it. It is therefore the cleanest available
test of the hypothesis on fresh ground and the sharpest mechanical readout in the arm. ⚠️ It
also carries an over-application risk, pre-registered as **X1** below.

## 4. THE VALIDATION GATE — the one place this project has been burned

`node_worked_example.md` was found stale on five counts and one of its exemplars **violated
the file's own contract**. `validate_examples.py` therefore runs every fragment's source
module through `schema.validate_all` + `checks.run_checks` before the block ships, and
greps the block for the literal fragment strings so a later edit cannot drift from the bytes
on disk.

**RUN AND PASSED before signing** (`VALIDATION.txt`, exit 0):

| ex | node | ✅ side | ⛔ side |
|---|---|---|---|
| 1 | `l1368_1541_n019` | `translated`, **0 breaches** | `invalid`, 1 |
| 2 | `l3239_3382_n002` | `translated`, **0 breaches** | `invalid`, 2 |
| 3 | `l1368_1541_n019` | `translated`, **0 breaches** | `invalid`, 1 |
| 4 | `l1_170_n056` | `translated`, **0 breaches** | `invalid`, 5 |
| 5 | `l2126_2404_n016` | `translated`, **0 breaches** | `translated`, **0** · ⛔⛔ `invalid`, 3 |
| 6 | `l1707_1973_n022` | `translated`, **0 breaches** | `translated`, **0** |

**All six ✅ exemplars pass the floor with zero breaches**, `outcome == translated`, and only
`note`-severity findings. All eleven literal fragments were found in the block.
⚠️ **Stated honestly:** where a ⛔ module is `invalid`, that is usually for a reason **other**
than the defect being demonstrated (ex 2's breaches are an undeclared act, not the circular
rule). Examples 5 and 6 are the ones whose ⛔ side passes the floor **clean** — those are the
defects no deterministic check can reach, which is why they are in the block.

## 5. WHAT COUNTS AS WHAT — three branches, all pre-specified

Judged over 17 turn-1 drafts, floor first, then span-first adjudication by me.

### ⭐ TRANSFER — any one of:
* **C1.** ≥ **5 of 17** turn-1 drafts carry **no** defect I would send an edit for.
  Baselines: arm A **0 of 17**, prose arm **0 of 17**. (Same threshold the in-sample arm
  used for M1, kept for comparability.)
* **C2.** Conclusion-changing defect rate ≤ **8 of 17**. Baselines: arm A ≈ 16 of 17, prose
  arm **16 of 17**.
* **C3 (the mechanism claim).** Of the CC defects that occur, ≤ **25%** are ones an arm-C
  example demonstrates. Baselines: **87%** (arm B), **83%** (prose, in-sample).
* **C4 (the breadth-free one, and the one I weight most).** Per demonstrated class, counted
  over the clauses where the class is applicable: the count **falls by at least half AND to
  ≤ 2**, on **≥ 3 of the 6 classes**. Two of the six are scored **mechanically, with the
  baseline measured before signing**:

  | class | arm A t1 | prose arm | arm C |
  |---|---:|---:|---|
  | **ex 6** — ≥1 borrowed `NEEDS` gloss `textual`/self-cited (of 15 clauses with a NEEDS name) | **15 of 15** | **15 of 15** | *(to be measured)* |
  | **ex 3** — ≥1 `cepa` closure | **14 of 17** | 6 of 17 | *(to be measured)* |
  | **ex 3** — ≥1 `unclear` closure | **0 of 17** | 8 of 17 | *(to be measured)* |

  ⚠️ The prose arm already moved the `cepa`/`unclear` numbers (entry 2 was its one measured
  transfer). So **ex 3 cannot separate form from content** and is reported but not counted
  toward C4. **Ex 6 can**: it is at 15/15 in both baselines and no prose ever addressed it.

### NULL — all three:
* **C1** ≤ 1 of 17 defect-free, **and**
* **C2** CC rate ≥ 13 of 17, **and**
* **C4** fewer than 2 of the 6 classes meet their fall threshold.

### ⛔ MANUFACTURED — the third branch, live because it already fired once
A demonstration is followed more literally than a rule, so the arm can *create* defects. Any
of these fires the branch, and it is reported **even if C1–C4 all succeed**, exactly as H2
was in the in-sample arm.

* **X1 — licence over-demotion (ex 6's mirror).** ≥ **3** clauses mark a `PROVIDES` name, or
  a name coined from the narrowed text, as `licence: assumed` where the narrowed text does
  state it. Measured baseline to compare against will be computed the same way on arm A.
* **X2 — closure under-commitment (ex 3's mirror).** ≥ **3** clauses write `unclear` on an
  act class where the span does settle the question.
* **X3 — negation-as-failure proliferation (ex 4's risk).** ⚠️ Example 4's ✅ side contains
  `not overridden_by_higher_instruction(R)`; it is the adjudicated answer and was not
  altered, but NAF is forbidden by production rule 4 in other positions. **Measured baseline,
  before signing: 2 of 17 arm-A turn-1 drafts contain NAF in any body; 2 of 17 in the prose
  arm.** X3 fires at ≥ **5 of 17**.
* **X4 — condition-definition deletion (ex 5's mirror).** ≥ **3** clauses move a condition
  the span itself *defines* out of `ontology` into `inputs`, deleting the module's own
  definition. This is the exact inverse of the entry-5 harm and is the risk the repair
  creates.
* **X5 — surface imitation.** ≥ **3** drafts reproduce a content token from an example
  (`overridden_by_higher_instruction`, `answer_in_scenario`, `no_moral_ambiguity`,
  `overstepping`, `root_authority` where not a NEEDS name) on a clause whose span names
  nothing of the kind.

### SECONDARY, reported regardless
* Floor-failure rate (`outcome != translated` or breaches > 0). **Arm A: 7 of 17 (41%).
  Prose arm: 6 of 17 (35%).**
* The `asserts`/`ontology` mix. **Measured paired before signing: arm A 2.00 / 1.18; prose
  arm 2.00 / 1.29.** Arm B's claimed shift (2.0→1.3, 1.2→1.8) **did not survive pairing and
  was retracted**; arm C's figures are reported against the paired numbers only.
* Mean raw output chars. Arm A 3,645; prose arm 3,803.

## 6. PREDICTIONS, ON THE RECORD

* **R-a.** **C1 fails: 0 or 1 of 17 defect-free.** Grounds: the dominant classes in both
  prior arms are structural (unlinked or vacuous bodies, a `status` field with no negative
  pole, NAF where the schema offers nothing else, a document-side relation with nowhere legal
  to live) and a demonstration does not add a destination the format lacks. Confidence:
  moderate-high.
* **R-b.** **C4 succeeds on example 6 and on nothing else.** Grounds: ex 6 is a single named
  field value, decidable without re-reading the span — the shape the in-sample arm identified
  as the only transferable one (entry 2 moved `cepa`→`unclear` mechanically). Ex 1 (gloss) is
  equally local and the in-sample arm violated it on the clause it quotes, so I do not predict
  it. Confidence: moderate. **This is the prediction the arm turns on.**
* **R-c.** **C3 fails** — a majority of CC defects will be ones an example demonstrates.
  Confidence: moderate. If C3 *succeeds* while C1 fails, that is the informative middle
  result: the demonstrated classes closed and the residue is elsewhere.
* **R-d.** **X5 fires.** A demonstration supplies vocabulary, and the in-sample arm showed
  the model will copy a quoted artifact almost verbatim. Confidence: low-moderate. Scored
  explicitly.
* **R-e.** **X1 does not fire** (the ⚠️ guard line in ex 6 restricts it to borrowed NEEDS
  names). Confidence: low. Scored explicitly, because if it *does* fire, ex 6's mechanical
  win in R-b is bought with a manufactured defect and the arm is a net harm.
* **R-f.** Floor-failure rate lands in 5–9 of 17, i.e. a NULL against arm A's 7. Confidence:
  moderate.

## 7. ⚠️ CONTAMINATION — disclosed in advance, not softened

**I do not adjudicate blind and I do not claim to.** I read all 17 historical adjudications
and both prior RESULT files while building the block, and I chose the examples. Two specific
biases follow and I carry them:

1. **Toward finding the historical defect.** Knowing each clause's frozen defect biases me
   toward seeing it again. Any claim that a defect count *fell* is therefore weaker than a
   claim that it did not.
2. ⭐ **Toward finding my own examples to have worked.** I built the block; I have a stake in
   it. **Mitigation, fixed here:** the two classes I weight most (C4's ex 6, and the closure
   counts) are scored **mechanically from the JSON**, with baselines already measured and
   printed in §5 above — no reading by me enters them. Where a judgement of mine is the only
   evidence, it is marked as such and the verdict does not rest on it.
3. **What cannot be fixed:** one adjudicator, no second reader, no answer key. n = 17,
   single-digit cells throughout. No rate here will be statistically separated from noise.

## 8. ⛔ PROTOCOL COMMITMENTS

1. **Turn 1 only, arm C only.** 17 independent calls in parallel; the prompt is fixed.
2. ⛔ **No tuning after seeing results.** Nothing in `promptsC/` is edited after the first
   call. A second variant must be pre-registered as a second variant, run separately, and
   **both** reported.
3. **The floor runs first** on every draft — `schema.validate_all` then `checks.run_checks` —
   and my adjudication sits on top of it, never instead of it.
4. **The sha gate.** `run_armc.py` refuses to send unless the assembled system block's sha256
   equals `b5af1129…8af5` and the first four files still assemble to arm A's `3a66c5f5…`.
5. **A third consecutive null is a valuable and decisive result** and will be reported as
   one, undiluted. It would mean the defects are unreachable by instruction **in any form**,
   and the argument moves to the schema and the graph.

## 9. SPEND

Hard cap **$0.08**, owner-set, enforced in `run_armc.py:CAP_USD` against the on-disk ledger
before any send. Estimate: 17 calls × (50,179 char system + ~2–4 KB user) at 4 chars/token,
worst-case 4,096 output tokens, $0.14 / $0.28 per Mtok → **worst case ≈ $0.052**. The prose
arm's measured rate on the same 17 clauses with a longer prompt was **$0.03826**, so the
expected figure is **≈ $0.036**. Refuse over.

---

**Signed before the first call.** — adjudicator, 2026-08-16
