# PREREG — list-in-the-translator's-prompt, arm B

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md` marked as such.

---

## THE DESIGN FLAW THIS CORRECTS

In the 15-clause DeepSeek/Opus loop, `REVIEW_LIST.md` was shown **only to the
adjudicator**. Every turn-1 draft came from the byte-identical production system
prompt, so the translator has never seen a single entry. The measured
consequence:

* new mistake classes per clause fell to zero over the last four clauses
  (3,3,2,3,2,3 → 0,1,1,1,0,0,0,0);
* turns-to-converge did **not** fall (3/3/3/3/2/2/2/2/3/4/4/3/2/3/2).

**A better list made the critic better, not the drafts better.** This arm asks
whether it can make the drafts better.

## THE QUESTION

Turn 1 only. Does the production system prompt **plus the evidence-ordered
review list** produce better unaided first drafts than the production system
prompt alone?

---

## THE BASELINE, stated before looking

All three from the 15-clause loop, all on record:

| B# | baseline | value |
|---|---|---|
| **B1** | drafts that passed `translated` / `repair_needed=False` / `0 breaches` **while carrying a conclusion-changing defect** | **11 of 22** (50%) |
| **B2** | turns-to-converge | **2–4, mean ≈ 2.7, never 1** |
| **B3** | turn-1 drafts that were defect-free | **0 of 15** |

⚠️ B1's denominator is 22 *drafts across all turns*, not 15 clauses; the
comparable arm-B figure is over 15 turn-1 drafts only, and is reported as such.

## WHAT COUNTS AS WHAT

Judged over the 15 arm-B turn-1 drafts, adjudicated span-first by me, exactly as
the loop did.

### IMPROVEMENT
Any one of:
* **I1 (the strong one).** ≥ 2 of 15 turn-1 drafts carry **no** defect I would
  have sent an edit for. Baseline is 0 of 15; 2 of 15 is the smallest count that
  is not comfortably one draw of noise at this n.
* **I2.** The **conclusion-changing** defect rate on turn-1 drafts falls to
  **≤ 4 of 15 (27%)**, against a baseline where every turn-1 draft was
  defective and 50% of all drafts hid a conclusion-changer behind a clean floor.
* **I3 (the mechanism claim, and the one that would actually matter).** Of the
  defects that *do* occur, **≤ 25%** correspond to an entry the translator was
  given. That would say the list closed the classes it names and the residue is
  elsewhere.

### NO EFFECT
* 0 or 1 defect-free drafts, **and**
* conclusion-changing defect rate in **5–11 of 15**, **and**
* the mix of defect classes is not visibly different from the loop's.

### HARM — pre-registered because two mechanisms are already measured
* **H1 crowding-out.** ≥ 3 of 15 drafts carry a defect in a class the loop's
  turn-1 drafts got *right* (empty `beats`/`defines`/`forbid_body` where
  correct; declining the `prefer` temptation; not manufacturing an antecedent
  for `kind: conditional`; leaving contract-2 `NEEDS` names alone), or
  ≥ 3 drafts fail the floor outright (`breaches > 0`) where the loop's turn-1
  breach rate was low.
* **H2 obedience harm — the R57 shape.** ≥ 1 draft carries a defect that is the
  **direct product of correctly obeying a list entry**. R57 measured exactly
  this: N5 and P7 were both obeyed and *together produced* the clause's decisive
  defect. This is scored separately and reported even if everything else
  improves, because a prompt that manufactures defects is worse than one that
  fails to prevent them.
* **H3 invention.** ≥ 3 drafts coin machinery (extra `ontology` entries,
  `forbid_body` entries, promoted hedge predicates) whose only motivation is a
  list entry rather than the span. N2's promotion remedy and N6's `forbid_body`
  destination are the two most likely sources.

### THE DECISIVE READOUT, whatever the aggregate says
For every defect found, I record whether **an entry in the prompt explicitly
warned against it**. A defect the prompt names is the strongest available
evidence that the list does not transfer. This is reported per clause and
totalled, and it is the number the verdict turns on.

## PREDICTIONS, on the record

* **P-a.** The headline result is **NO EFFECT** on I1 and I2. Grounds: the list
  is a *critic's* instrument — every entry is phrased as a question to ask of a
  finished object, and 12 of 17 loop clauses record its highest-value action as
  being **on the adjudicator**, not on the draft. Confidence: moderate.
* **P-b.** **I3 fails** — a majority of defects will correspond to a list entry
  the translator was given. Confidence: moderate-high.
* **P-c.** If any single entry transfers, it is **P8** (gloss restates its
  name): purely local, purely syntactic, needs no reading of the span.
  Confidence: low-moderate. Scored explicitly.
* **P-d.** **H2 fires at least once.** Confidence: low. Scored explicitly.
* **P-e.** Mean output length rises (more `claims` prose, more hedging notes)
  without a matching fall in defects. Scored as a token count, MEASURED.

## PROTOCOL COMMITMENTS

1. **Turn 1 only, arm B only.** No repair turns. The 15 calls are independent
   and are issued in parallel; the prompt is fixed, so there is no accumulation.
2. ⛔ **No prompt tuning after seeing results.** If a second variant is wanted
   it is pre-registered as a second variant, run separately, and **both** are
   reported. Nothing in `promptsB/` is edited after the first call.
3. **The floor runs first** on every draft — `schema.validate_all` then
   `checks.run_checks` — and my adjudication is on top of it, never instead.
4. **Span-first adjudication**, exactly as the loop did: read the narrowed
   `SOURCE TEXT` and enumerate what it says before reading the module.
5. **No arm-A re-run.** The comparison is against the loop's recorded turn-1
   results. ⚠️ This is a **historical control, not a paired control** — arm A's
   15 clauses are different clauses. Stated as a limitation, not fixed.
6. **n = 15, single-digit cells.** Every per-class count is reported as such. A
   null is a real result and is reported as one.

## THE CONFOUND I AM ACCEPTING, AND WHY

The clauses are **new** (drawn from the 634 corpus nodes never touched by any
`_debug_gen11` artifact), because the list was derived from the loop's 15 and
testing on those would be in-sample. The cost is that arm B's clauses are not
arm A's clauses, so a difference could be clause difficulty. **Mitigation:** the
draw is strided across the document (15 distinct line-blocks, one node each) and
the per-clause adjudication is reported in full, so a reader can judge
difficulty directly rather than trusting the aggregate.

## SPEND

Hard cap **$0.12**, owner-set for this experiment, enforced in
`run_armb.py:CAP_USD` and checked against the ledger on disk before each send.
Estimate: 15 calls × (≈ 48 KB system + ≈ 2 KB user) input + ≤ 4096 output tokens
at $0.14 / $0.28 per Mtok = **worst case ≈ $0.043**; measured rate from the loop
(~$0.0018 / turn-1 call) predicts **≈ $0.03**. Refuse over.

---

**Signed before the first call.** — adjudicator, 2026-08-16
