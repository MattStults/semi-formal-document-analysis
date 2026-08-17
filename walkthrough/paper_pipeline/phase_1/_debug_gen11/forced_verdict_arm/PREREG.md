# PREREG — ARM F, structural coercion: the review list as REQUIRED OUTPUT FIELDS

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md`, marked as such.

---

## 1. THE QUESTION, AND WHY IT IS NOT THE ONE THE OTHER ARMS ASKED

Three arms have shipped the review list as **prose** and returned nulls:

| arm | population | defect-free turn-1 | CC defects named by a held entry |
|---|---|---|---|
| arm B | 15 new clauses | **0 of 15** | **87%** |
| in-sample | **these 17** | **0 of 17** | **83%** |

Both nulls have the same blind spot, and both said so: **nothing in the reply is
about the entries**, so neither can tell whether the model *read an entry and
ignored it* or *never engaged it at all*.

Arm F changes the **mechanism, not the text**. The production pipeline already
guarantees the reply's shape at generation — `model.format_forcing:
json_schema`, which `03_pipeline.md` stage 1 calls *"guaranteed at generation
rather than checked afterwards"*. Arm F **extends that shape**: a required
`checks` array, one element per entry, each demanding a quotation from the
module, a verdict, and an action. Producing a well-formed module now *requires*
answering every check.

⭐ **THE MEASUREMENT THIS ARM UNIQUELY BUYS.** The model's verdicts are on the
record, so "what it said it checked" can be compared against "what it actually
did". Three cells no prior arm could see, reported per clause:

* **DECLARED-AND-DID** — `applies_and_handled`, and the module bears it out.
* ⭐ **FALSE CLEAN** — `does_not_apply` or `applies_and_handled`, **and the
  defect is present anyway**. A clean verdict *written down* over a live defect.
* **DECLARED-AND-SHIPPED** — `applies_and_not_handled`: the model named its own
  defect in writing and returned it regardless. Honest, and still a defect.

## 2. WHAT IS HELD FIXED, AND THE ONE VARIABLE

* **The system block is PRODUCTION.** `run_armf.py` rebuilds the block from
  `resolve_runs/graph_v2/config_corpus_all.json` and **refuses to send unless
  the two sha256s are equal**. Measured before signing: both
  `3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c`, 39,959
  chars. A second gate refuses if the block ever equals arm B's `04560828…`.
* **Arm F ships no list prose at all.** `40_review_list.md` sits in
  `promptsB/` unsent and is declared in `prompt.unused_files`, so the prompt
  orphan guard makes its absence a *checked fact*.
* So: **arm A → arm B** is *the entries, as prose in the system block*;
  **arm A → arm F** is *the entries, as required fields of the reply*. One
  variable each way, same 17 clauses, same model, same temperature, turn 1 only,
  no feedback, issued in parallel.
* ⛔ `schema.py` is guard-watched and is **not edited, not patched, not
  shadowed**. `arm_f_schema.request_json_schema` **deep-copies**
  `schema.response_format(strict)` and appends one property, mirroring
  `json_schema()`'s own `required == list(properties)` rule. Verified before
  signing: every production property is byte-identical in the copy; the
  production object is unchanged after deriving. Wire schema 14,432c → 21,964c.
* **The extra key is STRIPPED before the real floor runs.** `strip()` removes
  exactly one top-level key and rebinds every other value **by identity**.
  `strip_proof()` records, per clause: `keys_removed == ["checks"]`, no keys
  added, every surviving field `is`-identical to the parsed original, and every
  surviving field byte-equal under `json.dumps(sort_keys=True)`. The floor —
  the **real** `schema.validate_all` then the **real** `checks.run_checks` — is
  run on the stripped object and on nothing else.

## 3. WHICH ENTRIES, AND WHY — the judgement calls, stated

**Six of the shipped twenty.** `ORDERING.md` ranks the list by distinct clauses
on which each entry produced an actual finding, counted over **these same 17**.
Five entries carry **48 of the 82** findings and **20 of the 27 CAUGHT**: P8,
N7, N10, P6, N1 — shipped list entries 1–5. Those are **C1–C5**.

**C6 is shipped entry 12 (P1), rank 13 with 3 findings — included against its
rank, for a reason specific to this arm.** `l4252_4482_n016` is the sharpest
MEASURED *"held the entry and ignored it"* cell in the programme: the in-sample
arm shipped entry 12 with **this clause's own span as the remedy**, and the
model returned all three inverted `prefer`s. Forcing a verdict on exactly that
clause is the highest-information single cell available for the coercion
hypothesis, and it is bought for one extra check.

**The other fourteen are excluded.** Twenty forced verdicts is a ritual, not a
review, and the tail is where the measured *mis-directions* live: N6 and P2
found nothing in 17 clauses (P2 *endorsed* a decisive defect once); P4, P10 and
N4 fired only on their own clauses, N4 and P4 with recorded mis-directions.
Coercing a verdict from an entry that has never found anything buys nothing and
spends output tokens the evidenced checks would otherwise get.

### ⛔ SHIPPED ENTRY 5 IS NOT SHIPPED AS WRITTEN — what was changed

Entry 5 (N1) is the one entry MEASURED to **manufacture** a defect class.
`list_in_prompt_insample/RESULT.md` §7: obeyed correctly on four clauses it
converted a **harmless inert constant** into a **vacuous bodied rule** —
`no_moral_ambiguity(S) :- scenario(S)` makes a clause scoped to *"scenarios
where there's no moral ambiguity"* govern **all** scenarios.

**Excluding it was considered and rejected by name.** The harm is exactly the
kind a *forced field* can be built to block, and dropping the entry would drop
this arm's only test of whether structure repairs an instruction prose could
not. **C5 is rewritten in two ways:**

1. **The headline is inverted.** The shipped text leads with *"prefer the bodied
   rule over a coined constant"* and buries the document-atom exception in its
   last sentence. C5 leads with the **asymmetry of harm** — inert concludes
   *less* than the span, vacuous concludes *more*, in the dangerous direction —
   and makes the conversion **conditional** on carrying the span's own
   discriminating condition into the body.
2. ⭐ **The fix is itself structural, which is the arm's thesis.**
   `excluded_case` is a required field, mandatory on C5: *name one concrete
   situation that satisfies the body's type predicate but NOT the head.*
   `scenario(S)` admits no such case, so the vacuous rule cannot be written and
   its verdict truthfully filled in at the same time.

⚠️ This is a **deliberate departure from a strict replication**: C5's text is
not the shipped entry 5, and any C5 result is a result about the rewrite, not
about the shipped entry. Stated here so it cannot be read the other way later.

### Field order — `evidence` before `verdict`, `checks` after the module

Both placements are decisions and both plausibly matter.

* **Inside each check, `evidence` precedes `verdict`.** A verdict emitted first
  can be produced without consulting the object; a quotation cannot.
  `ORDERING.md`'s own INFERRED reading of why the top entries scored is that
  they *"could only be answered by looking at the finished text"* — so the field
  that forces the look is emitted first.
* **`checks` is appended LAST, after `forbid_body`.** A structured decoder emits
  properties in schema order. Placed **first**, the verdicts would be a *plan* —
  a prediction about a module not yet written, i.e. exactly the "intentions"
  the prose already failed to convert into behaviour, and unfalsifiable against
  the object. Placed **last**, every verdict is about bytes already committed,
  so *"it said clean and the defect is there"* becomes a checkable statement,
  and the arm's headline measurement exists at all. ⚠️ **The cost is accepted
  and named: last placement is also the placement most exposed to
  rubber-stamping.** That is the measurement, not a flaw in it.

## 4. THE BASELINES, stated before looking

All MEASURED, all on the **same 17 clauses**.

| B# | baseline | arm A (unaided) | in-sample (list as prose) |
|---|---|---|---|
| B1 | turn-1 drafts defect-free | **0 of 17** | **0 of 17** |
| B2 | conclusion-changing defect | ~16 of 17 | **16 of 17** |
| B3 | floor failure (`outcome != translated` or breaches > 0) | **7 of 17** | 6 of 17 |
| B4 | CC defects named by an entry the model held | — | **83%** (35 of 42) |
| B5 | mean raw output chars | **3,645** | 3,803 |
| B6 | frozen §4 defect recurred | (by construction) | **9 of 17**, +6 equal substitutes |

**B7, frozen here and computed before the run.** Of the 17 clauses, the frozen
`list_in_prompt_insample/PREREG.md` §4 table names a **coerced** entry
(arm-B numbering 1, 2, 3, 4, 5 or 12 = C1–C6) for **14**. The three it does not
are `l3147_3238_n003` (entry 15), `l1707_1973_n006` (entries 6/11/10/tail) and —
partially — nothing else. Of those 14, the in-sample arm reproduced the frozen
defect **verbatim or in mechanism on 8**.

## 5. WHAT COUNTS AS WHAT

Judged over 17 turn-1 drafts, floor first, adjudicated span-first by me.

### ⭐ TRANSFER — structural coercion succeeds where prose failed. Any one of:

* **F1.** ≥ **5 of 17** drafts carry no defect I would send an edit for. Same
  bar the in-sample arm set (M1), deliberately not re-tuned. Baselines 0 and 0.
* **F2 (the targeted claim).** Of the **14** B7 clauses, ≤ **3** carry a defect
  in the coerced C1–C6 class named for them. Baseline: in-sample **8 of 14**.
* **F3 (the mechanism claim).** The **FALSE CLEAN** count is ≤ **20%** of the
  ruled cells *and* F1 or F2 also holds. Coercion that works looks like honest
  clean verdicts over clean modules; a low false-clean rate with a high defect
  rate is a **different** result (see §7 R-c) and is not scored as transfer.

### NULL — all three of:

* ≤ 1 draft defect-free, **and**
* ≥ **6 of 14** B7 clauses carry their coerced-class defect, **and**
* the array is a ratification: ≥ **70%** of ruled cells are
  `applies_and_handled` while the defect rate does not fall.

⚠️ **A null here is more informative than the prose nulls and will not be
softened.** A model that writes *"does not apply"* next to a defect it then
commits is a **different failure** from one that never considered the check, and
this arm can tell them apart for the first time.

### PARTIAL / AMBIGUOUS
Anything between, reported as ambiguous and not rounded toward either verdict.

### ⛔ MANUFACTURED HARM — pre-registered, four shapes, reported even if
everything else improves

* **H-F1 VACUITY (the entry-5 shape).** ≥ 1 draft carries a vacuous bodied rule
  (`X(S) :- <type>(S)` with no discriminating condition). Baseline: in-sample
  measured **4 clauses**. ⭐ Scored jointly with the module's own
  `excluded_case`: a vacuous body shipped with a **fabricated** excluded case is
  a specific, nameable failure of the structural fix, and is reported as such.
* **H-F2 CROWD-OUT.** The module degrades because output budget went to
  `checks`: ≥ **10 of 17** fail the floor (arm A: 7), **or** any truncation,
  **or** mean module size (raw minus the `checks` block) falls > 20% below arm
  A's 3,645c.
* **H-F3 COERCED INVENTION.** ≥ 3 drafts coin machinery whose only motivation is
  a check rather than the span. (In-sample H3 fired at 4.)
* **H-F4 VERDICT-SERVING DAMAGE — new, and specific to this arm.** ≥ 1 draft
  changes a thing arm A got RIGHT in order to make a verdict sayable — the
  archetype being rewriting a correct `read_back` to agree with a wrong `status`
  so C6 can be ruled `applies_and_handled`. This is the failure mode a forced
  field has that prose does not, and it is why it is pre-registered.

### SHAPE, measured not assumed
`strict` honouring is UNVERIFIED for this model. Per clause: `checks` present,
length 6, `entry_id`s exactly C1–C6 in order, `verdict`s in the enum, and the
strip proof. Reported as counts.

## 6. ⚠️ CONTAMINATION — disclosed, not denied

I have read all 17 historical adjudications, `ORDERING.md`, and the in-sample
`RESULT.md` in full. I cannot adjudicate these drafts blind and do not claim to.

1. **Direction of the old bias, and it favours the null.** Knowing each clause's
   historical defect biases me *toward* finding it again — confirmation, which
   **inflates** F2's recurrence count. A **high** recurrence measured under this
   bias is therefore the **weaker** reading; a **low** one is the stronger. That
   is a reason not to overstate the *rate*, never a reason to soften the null.
2. ⭐ **A NEW bias specific to this arm, and the protocol that fences it.** The
   model's own verdicts would steer my adjudication toward the classes it names
   and away from the ones it does not. **PROTOCOL COMMITMENT: for each clause I
   read the narrowed SOURCE TEXT and enumerate it, then read the STRIPPED module
   and write that clause's defect list — and only then open `armf_checks`.** The
   run record stores `module` and `armf_checks` as separate keys precisely so
   this is mechanically possible. Verdict-versus-reality scoring happens against
   a defect list already written.
3. **The floor runs first** on every draft and my reading sits on top of it,
   never instead.
4. **What cannot be fixed:** one adjudicator, no second reader, no answer key.
   Novel defects get less attention than predicted ones by construction, so any
   claim that a clause's defect count *fell* is weaker than a claim that it
   *did not*.

## 7. PREDICTIONS, ON THE RECORD

* **R-a.** **F1 = 0 or 1 of 17.** Confidence **moderate-high**. Grounds: both
  prose arms measured 0, and the dominant classes — unlinked body variables, a
  `status` field with no negative pole, coextensive `ontology` heads, borrowed
  glosses self-cited `textual` — are places the model wrote the only thing the
  format allowed. A verdict field adds no expressive option.
* **R-b.** **The array comes back overwhelmingly clean:** ≥ 80% of ruled cells
  `applies_and_handled` or `does_not_apply`, and ≤ 10 cells across all 17
  clauses are `applies_and_not_handled`. Confidence **moderate-high**.
* ⭐ **R-c. THE FALSE-CLEAN COUNT IS LARGE: ≥ 15 of the ~102 cells are a written
  clean verdict over a defect I adjudicate present.** Confidence **moderate**.
  Grounds: 83–87% of conclusion-changing defects were already named by held
  entries in both prose arms; if the defect rate holds and the verdicts read
  clean, false cleans are arithmetically forced. **This is the arm's headline
  number and it is predicted before it is measured.**
* **R-d.** `l4252_4482_n016` reproduces its three inverted `prefer`s **and**
  rules C6 `applies_and_handled` or `does_not_apply`. Confidence
  **moderate-low** — the single sharpest cell, and I would be genuinely
  surprised either way. Scored explicitly.
* **R-e.** If any check transfers it is **C1** (glosses), because its test is
  purely local and syntactic and needs no reading of the span — `ORDERING.md`'s
  own INFERRED explanation of why P8 tops the table. Prediction: ≥ 2 clauses
  show a gloss materially better than arm A's. Confidence **low-moderate**.
* **R-f.** **H-F1 fires 0 or 1 times** — the C5 rewrite holds. Confidence
  **low**. ⭐ And if it fires, at least one `excluded_case` will be
  **fabricated** rather than the honest `NONE`. Scored explicitly.
* **R-g.** Mean raw output rises ≥ 25% over arm A's 3,645c. MEASURED, not a
  judgement.
* **R-h.** ≥ 1 clause breaks the shape contract (`checks` missing, wrong length,
  wrong ids, or an enum violated). Confidence **low**; `strict` honouring is
  unverified for this model and this is the first test of it under an extended
  schema.

## 8. PROTOCOL COMMITMENTS

1. **Turn 1 only, arm F only.** No repair turns; a second turn measures the
   critic, which the loop already measured.
2. ⛔ **No schema tuning after seeing results.** If a second variant is wanted it
   is pre-registered as one, run separately, and **both** are reported.
3. ⛔ **Nothing under `runs/`, `translation_sample/runs/`, `repair_graveyard/`,
   `prompt/`, `schema.py`, `resolve_runs/`, or any other `_debug_gen11` arm
   directory (`examples_arm`, `selfreview_arm`, `retrieval_arm`,
   `list_in_prompt*`, `ds_opus_loop`) is written.** Everything this arm produces
   is under `_debug_gen11/forced_verdict_arm/`. **No git is run.** The branch is
   `d3-worked-example` and is not switched.
4. **n = 17, single-digit cells throughout.** Every per-class count is reported
   as a count, never as a rate implying precision it does not have.
5. **MEASURED vs INFERRED is marked on every claim.**

## 9. SPEND

Hard cap **$0.10**, owner-set, enforced in `run_armf.py:CAP_USD` against the
on-disk ledger before any send. **Priced `--dry` before this file was signed:**
17 clauses, worst case **$0.0577** — every input token at full rate, the 21,964c
wire schema billed as input, every call billed the full 4,096-token output cap.
The in-sample arm's MEASURED rate was $0.00225/call; arm F's replies are longer
by the `checks` block, so the expectation is **≈ $0.04**. Refuse over.

⚠️ Several agents are appending to `semi-formal-experiment/usage.jsonl`
concurrently. Spend is reconciled from **this arm's own turn records**
(`out/<id>.json:_arm_f_cost_usd`); the shared ledger is a cross-check that may
contain other arms' rows and is never the source.

---

**Signed before the first call.** — adjudicator, 2026-08-16
