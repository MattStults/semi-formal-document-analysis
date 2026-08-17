# PREREG — the IN-SAMPLE ceiling test for the list-in-the-translator's-prompt

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md`, marked as such.

---

## 1. THE QUESTION

Arm B (`../list_in_prompt/RESULT.md`) put the evidence-ordered review list into
the **translator's** system prompt and drew 15 clauses the list had never seen.
Result: **0 of 15 defect-free** (baseline 0 of 15), **14 of 15 carrying a
conclusion-changing defect**, and **87% of those defects corresponding to an
entry the translator had been given.** A clean out-of-sample null.

This arm asks the **ceiling** question. Run the *same* prompt on the *same
clauses the list was measured on*, where for each clause an entry exists that
names that clause's own historical defect — in eight cases quoting an artifact
of that clause's own draft **verbatim**.

* **If in-sample also fails**, the format is insufficient. The defects are not
  reachable by instruction at any level of specificity, and the argument moves
  to the **schema** and the **graph**.
* **If in-sample succeeds substantially**, the list works but does not
  generalise — it encodes *these clauses* rather than the failure classes, which
  explains arm B's null and justifies retiring most of it.

## 2. THE DESIGN, AND WHY IT IS PAIRED

**The prompt is not rebuilt.** `config_insample.json` points `system_files` at
`../list_in_prompt/promptsB/` — the exact files arm B sent, read-only and
untouched — and `run_insample.py:prompt_shas` **refuses to send** unless the
assembled system block's sha256 still equals arm B's
`045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917`.
⛔ Re-tuning the prompt after seeing arm B's null would make this arm
unattributable. Verified `--dry` before this file was signed: **53,426 chars,
sha matches.**

**Turn 1 only, no feedback, 17 calls in parallel** — protocol identical to arm
B, so the two arms differ in the clause set and in nothing else. DeepSeek has no
cross-call memory, so re-drawing a clause the loop already drew is clean. Each
clause's unaided turn-1 draft under the **production** prompt, and its full
adjudication, are on disk in `../ds_opus_loop/out/<id>.turns.md`. So this is a
**genuine paired comparison** — same clause, same model, one variable, the
list — which arm B, on a historical control of *different* clauses, could not be.

### The clause set: all 17, and why

The 15-clause loop **plus** the two proof clauses `l1_170_n056` and
`l3147_3238_n003`.

**Grounds.** (i) `ORDERING.md` defines the list's evidence population as
**17**, so "in-sample" is a property defined over 17. (ii) The two proof clauses
carry the *most literal* in-sample relation in the whole set: entry 15's worked
example **is** `l3147_3238_n003`'s span verbatim (*"use a tool …, hedge …, or
explain"*) and entry 2's **is** `l1_170_n056`'s (*"should honor … unless it
conflicts"*). Dropping them would remove the two sharpest cases the arm has.
(iii) Worst case prices at **$0.0526**, inside the cap.

⛔ **Rejected by name: the 15 loop clauses only.** It would have matched arm B's
`n` exactly, and that is its only merit; it buys comparability of a denominator
at the cost of the two clauses whose defects the prompt quotes word for word,
which is the measurement.

## 3. ⚠️ THE IN-SAMPLE PREMISE, CORRECTED BEFORE IT IS TESTED

The brief for this arm states that these 15 clauses "are the ones every entry
was written from." **Checked against `../translate_opus/REVIEW_LIST.md`, that is
not exactly true, and the correction is recorded here rather than discovered
later.** Ten of the twenty entries name a *different*, earlier wave as their
provenance — `l831_1000_n005` (P5, N3, N4, N5, N6), `l461_608_n015` (N1),
`l1108_1367_n014` (N2), `l2405_2473_n001` (N9, N10), `l1974_2125_n019` (P1).
None of those five clauses is in this draw.

**The relation that IS true, and the one this arm tests:** these 17 are the
clauses the list was **measured, ranked and corrected on**. Every cell of
`ORDERING.md` is a count over them; all four corrections folded into the arm-B
text (R33, R57, R58, R65) were derived from them; and the adjudicator ran every
entry against every one of them, recording per clause which entries caught,
ratified, or missed.

So the operative in-sample relation is defined in two grades, fixed here:

* **GRADE A (8 clauses).** The prompt quotes, **verbatim**, an artifact of that
  clause's own turn-1 draft or its own span — the coined name it emitted, the
  gloss it wrote, or the remedy phrased in its own words. This is the sharpest
  in-sample relation obtainable and it is where the ceiling claim lives.
* **GRADE B (9 clauses).** An entry produced a recorded FINDING on that clause
  during the loop — it named the defect, without quoting the clause's own bytes.

## 4. THE FROZEN PER-CLAUSE TABLE — written before any call

Each row: the clause's **historical turn-1 defect** under the production prompt,
and the **entry now in the translator's prompt** that names it. Arm-B entry
numbers (1–15, plus the tail and anti-rules) with the original P/N code beside
them. `RESULT.md` scores recurrence against **this table**, frozen, not against
a post-hoc reading.

| # | clause | grade | historical turn-1 defect (decisive unless noted) | entry now in the prompt | what the prompt quotes |
|---|---|:--:|---|---|---|
| 1 | `l4252_4482_n016` | **A** | `prefer repeat_user_prompt(R)` + `prefer include_redundant_phrase/idea(R)` — all three asserts state the **opposite** of *"should avoid repeating … minimize redundant phrases"* | **12** (P1) | entry 12's remedy is *"`prefer minimize_redundant_phrases`"* — **this clause's own span** |
| 2 | `l3147_3238_n003` | **A** | three `oblige` on one identical body for an *"or"*; hedging violates the other two | **15** (P4) | *"use a tool …, hedge …, **or** explain"* — this clause's span, verbatim |
| 3 | `l2126_2404_n016` | **A** | three `ontology` heads share ONE identical body → coextensive → module **obliges and forbids the same act** on every instance | **15** mirror (R45), **1** (P8), **3** (N10), **5** (N1) | entry 1 quotes its gloss *"A is a straightforward answer"*; entry 3 quotes its coined `answers_user_question`; entry 5 quotes its `no_moral_ambiguity` |
| 4 | `l3239_3382_n004` | **A** | two **body-less** `ontology` entries assert both of the span's conditions true of everything; `S` unlinked | **1** (P8), **8** (P5), **5** (N1) | entry 1 quotes **both** of its glosses — *"T is a transformation task"*, *"S is an interactive setting"* |
| 5 | `l1368_1541_n019` | **A** | `S` names a *situation* and a *suggestion* in one body → the middle obligation can never fire | **1** (P8), **9** (N8), **2** (N7) | entry 1 quotes its `safety_precaution_suggestion/1` gloss verbatim |
| 6 | `l4252_4482_n005` | **A** | `exaggerated_or_stereotypical(A) :- speak_in_accent(A)` inverts the clause into a **blanket prohibition** on all accents | **3** (N10) ⚠️, **1** (P8) ⚠️, **6** (P3) | entry 3 quotes its fused name `exaggerated_or_stereotypical` as its own worked warning |
| 7 | `l1_170_n056` | **A** | exception **unattached**: `oblige honor_request(R)` unconditional **plus** three `permit refuse_request(R)` | **2** (N7), **3** (N10), **9** (N8) | entry 2 quotes *"should honor … unless it conflicts"*; entry 9 quotes its `authority_levels_hierarchy` |
| 8 | `l3239_3382_n002` | **A** | circular `ontology`: `overstepping(A)` has its own head in its body, so the module's only `forbid` can never fire | **1** (P8) first half | entry 1's head-in-its-own-body test is written from this shape |
| 9 | `l3596_3876_n009` | B | three of five `concepts` glosses restate their own names; they carry the module's entire non-borrowed content | **1** (P8) | — |
| 10 | `l3877_3953_n014` | B | `rule_in_have_conversational_sense/1` in `inputs` → `user_authority/1`, the one thing the node exists to provide, is derived **never** | **5** (N1), **4** (P6) | entry 5's sanctioned pattern `root_authority(section_x)` is the answer this clause needed |
| 11 | `l1001_1107_n005` | B | `rule_under_heading/2` in `inputs` can never unify with a situation fact → the module's one rule cannot fire; `textual` licence on an unstated inference | **5** (N1), **4** (P6), **3** (N10) | — |
| 12 | `l2474_2554_n004` | B | `third_party_interaction(A) :- on_behalf_of_user(A)` **inverts** the span's conjunction; the paragraph now governs every interaction, and `permit lie_by_omission` licenses lying **to the user** | **8** (P5), **14** (N5) → its NAF, **1** (P8) | — |
| 13 | `l2821_3040_n017` | B | manner constraint became an **unconditional** obligation; `default_context/0` glossed from an **excluded** sentence and widened | **8** (P5), **4** (P6), **1** (P8), **3** (N10 + its R58 fix) | entry 14's ⛔ MEASURED-HARM note is this clause's R57 |
| 14 | `l1707_1973_n022` | B | the **vehicle's** exception imported into the **tenor** under a manufactured `textual` citation, via `not policy_explicitly_allows(P)` | **14** (N5), tail N4, **4** (P6), **1** (P8) | — |
| 15 | `l171_426_n022` | B | `higher_level_instruction` hardcoded to **root** authority though the span's *"higher-level"* is relative → module concludes strictly less than the span; gloss states the correct rule, hiding it | **8** (P5) partial, **3** (N10), **4** (P6), **6** (P3) | — |
| 16 | `l1707_1973_n006` | B | three of the span's four behaviours reach **no rule at all**; the consult-a-doctor element appears nowhere | **6** (P3), **11** (N9), **10** (P9), tail P10 | — |
| 17 | `l699_796_n012` | B | *(no defect called decisive)* modality survives on only one of two conjuncts — `serious_side_effects(I)` reads as actuality, not possibility | **7** (P7), **3** (N10), **2** (N7) | — |

⚠️ **Two rows are honest about a weakness in their own favour.** Row 7
(`l1_170_n056`) is on record as **already having failed to reproduce its own
defect on a fresh draw** — the loop's arm-A redraw produced a *different* wrong
answer for the same span. Row 6's decisive defect is on record as **passing**
entries 1 and 3 (R76, R78: a two-step chain and a fused name slip both tests).
Neither row can be scored as a clean win for the list if it changes.

## 5. WHAT COUNTS AS WHAT

Judged over 17 turn-1 drafts, adjudicated span-first by me, floor first.

### THE LIST WORKS IN-SAMPLE — any one of:
* **M1.** ≥ **5 of 17** turn-1 drafts carry **no** defect I would send an edit
  for. Baselines: arm A **0 of 17**, arm B **0 of 15**.
* **M3 (the ceiling metric).** The clause's **own frozen historical defect from
  §4 recurs on ≤ 5 of 17**, *and* the clause does not substitute an equally
  conclusion-changing defect in its place.
* **M5 (the sharpest, and the one I would weight most).** Of the **8 grade-A
  clauses** — where the prompt quotes the clause's own bytes — **≤ 2 reproduce**
  their frozen defect.

### THE LIST FAILS IN-SAMPLE — all three of:
* **M1** ≤ 1 of 17 defect-free, **and**
* **M3** frozen defect recurs on ≥ **11 of 17**, or is replaced by an
  equally conclusion-changing defect, **and**
* **M5** ≥ **5 of 8** grade-A clauses reproduce.

### PARTIAL / AMBIGUOUS
Anything between. Reported as ambiguous, not rounded toward either verdict.

### SECONDARY, reported regardless (all against the **paired** arm-A turn-1)
* **M2** conclusion-changing defect rate. Arm A ≈ 16 of 17; arm B 14 of 15.
* **M4** share of conclusion-changing defects that an entry in the prompt names.
  Arm B measured **87%**. ≤ 25% would be the mechanism claim succeeding.
* **M6** floor-failure rate (`outcome != translated` or breaches > 0). **Arm A
  turn-1, counted from the loop's own records: 7 of 17 = 41%.** Arm B: 8 of 15.
* **M7** the `asserts` / `ontology` mix. Arm B moved `asserts` **−35%** and
  `ontology` **+50%** against a historical control; here it is **paired**, so the
  same measurement is made clause by clause against that clause's own arm-A
  turn-1 module. Three of arm B's conclusion-changing defects landed *in* the
  `ontology` block the list pushed content into; whether that repeats is scored.

### HARM — pre-registered, same three mechanisms as arm B
* **H1 crowding-out / floor.** ≥ **11 of 17** fail the floor (against arm A's
  measured 7 of 17). ⚠️ Arm B's H1 was pre-registered on a *wrong premise* and
  the error is not repeated: the arm-A rate is stated here as measured, 41%.
* **H2 obedience harm (the R57 shape).** ≥ 1 draft carries a defect that is the
  **direct product of correctly obeying an entry**. Scored and reported even if
  everything else improves.
* **H3 invention.** ≥ 3 drafts coin machinery whose only motivation is an entry
  rather than the span.

## 6. PREDICTIONS, ON THE RECORD

* **Q-a.** **M1 = 0 or 1 of 17.** Grounds: arm B measured 0 of 15 out-of-sample,
  and the classes that dominate both records — unlinked body variables, a
  `status` field with no negative pole, coextensive `ontology` heads, licences
  with no rule for borrowed glosses — are places where the model wrote the only
  thing the format allowed. Confidence: **moderate-high**.
* **Q-b.** **M3 recurrence lands in 8–13 of 17.** Confidence: **low-moderate** —
  a fresh draw varies, and row 7 is on record as varying.
* **Q-c.** ⭐ **Row 1 (`l4252_4482_n016`) reproduces its polarity inversion**
  despite entry 12 carrying its span as the remedy. Grounds: arm B reproduced
  entry 12's failure on **two independent out-of-sample clauses**. Confidence:
  **moderate**. Scored explicitly — this is the single sharpest cell in the arm.
* **Q-d.** **Entry 1 (glosses restating names) is violated on ≥ 3 of the 4
  clauses whose own gloss the prompt quotes** (rows 3, 4, 5, 9). Grounds: entry
  1 is ranked #1 by evidence and was nonetheless arm B's **most-violated** entry.
  Confidence: **moderate**.
* **Q-e.** **M7 repeats in the same direction** — `asserts` down, `ontology` up,
  paired. Confidence: **moderate-high** (arm B measured it against a historical
  control; pairing should make it cleaner, not absent).
* **Q-f.** **≥ 2 clauses produce a defect fresh to both arms.** Confidence:
  moderate. Arm B's largest fresh class (a borrowed `NEEDS` gloss self-cited
  `licence: textual`) is nowhere in the 20 entries and is expected to recur here.
* **Q-g.** **H2 does not fire** (it did not in arm B). Confidence: low.

## 7. ⚠️ CONTAMINATION — disclosed, not denied

**I cannot adjudicate these drafts blind, and I will not claim to.** I have read
all 17 historical adjudications in full, and §4 above is my own summary of them.
The brief anticipated this and required it be disclosed. Four things are done
about it, and one thing cannot be:

1. **The historical defect and the entry that names it are FROZEN in §4 before
   any call**, so recurrence is scored against a written prediction rather than
   against whatever I notice afterwards.
2. **Span-first order is preserved.** For each clause I re-read the narrowed
   `SOURCE TEXT` and enumerate what it says before opening the new module — the
   loop's own protocol.
3. **The floor runs first** on every draft (`schema.validate_all`, then
   `checks.run_checks`), and my reading sits on top of it, never instead.
4. ⭐ **The direction of the bias is stated, and it is favourable to a null.**
   Knowing a clause's historical defect biases me **toward** finding it again —
   confirmation, which **inflates** M3 and M5. Therefore a **high** recurrence
   measured under this bias is the **weaker** reading, and a **low** recurrence
   is the **stronger** one. The verdict this arm is most likely to reach
   (recurrence) is the one its bias most favours, and that must be carried into
   how heavily the null is weighed. It is not a reason to soften the null; it is
   a reason not to overstate the *rate*.
5. **What cannot be fixed:** there is one adjudicator, no second reader, and no
   answer key. Novel defects — the ones §4 does not predict — get **less**
   attention than predicted ones by construction. Any claim that a clause's
   defect count *fell* is therefore weaker than a claim that it *did not*.

## 8. PROTOCOL COMMITMENTS

1. **Turn 1 only.** No repair turns. A second turn measures the critic, which
   the loop already measured.
2. ⛔ **No prompt tuning, before or after.** The sha gate enforces the "before";
   the "after" is a commitment: if a second variant is wanted it is
   pre-registered as one, run separately, and **both** are reported.
3. ⛔ **Nothing under `runs/`, `translation_sample/runs/`, `repair_graveyard/`,
   `prompt/`, `schema.py`, `resources/`, `resolve_runs/graph_v2/`, or
   `_debug_gen11/list_in_prompt/` is written by this arm.** Output goes to
   `_debug_gen11/list_in_prompt_insample/` and nowhere else. No git.
4. **n = 17, single-digit cells throughout.** Every per-class count is reported
   as a count, never as a rate that implies precision it does not have.
5. **A null is the more valuable outcome and will not be softened.** If the
   list fails in-sample, that is the strongest available evidence for a schema
   change and it is reported as such, without hedging toward "a better list
   might work."

## 9. SPEND

Hard cap **$0.06**, owner-set, enforced in `run_insample.py:CAP_USD` against the
on-disk ledger before any send. **Priced `--dry` before this file was signed:
17 clauses, worst case $0.0526** (every input token at full rate, every call
billed the full 4,096-token output cap). Arm B's **measured** rate was
$0.00226/call, predicting **≈ $0.038**. Refuse over.

---

**Signed before the first call.** — adjudicator, 2026-08-16
