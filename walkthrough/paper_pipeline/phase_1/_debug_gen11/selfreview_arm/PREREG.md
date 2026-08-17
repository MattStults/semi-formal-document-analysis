# PREREG — ARM D: the model applies the review list TO ITS OWN DRAFT, across turns

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md`, marked as such.

---

## 1. THE POSITIVE CONTROL THIS ARM RESTORES

Three arms have now tested `REVIEW_LIST.md` as **static text inside a one-shot
drafting prompt** and all three returned nulls:

| arm | delivery | defect-free turn-1 drafts | defects named by a held entry |
|---|---|---|---|
| **A** (`ds_opus_loop`) | list not shown to the drafter at all | 0 of 17 | — |
| **B** (`list_in_prompt`) | list appended to the system block, 15 unseen clauses | 0 of 15 | 20 of 23 (87%) |
| **C** (`list_in_prompt_insample`) | same system block, the 17 in-sample clauses | 0 of 17 | 35 of 42 (83%) |

⭐ **But the list's CONTENT has a positive control, and it converged 15/15.** In
the `ds_opus_loop`, an Opus critic applied the same entries to DeepSeek's own
drafts, turn by turn, in DeepSeek's own transcript — every clause converged, in
2–4 turns.

So "the list does not work" is not established. What is established is that
**one-shot static delivery** does not work. The untested cell is the one the
positive control differs from arm B in **two** ways at once: the entries were
applied *across turns*, and they were applied *by a stronger reader*. This arm
holds the first constant and flips the second: **DeepSeek applies the list to its
own draft, across turns, with no critic in the room.**

If arm D transfers, the earlier nulls were about *delivery* and a self-review
turn is the cheap fix. If arm D nulls, the earlier nulls were about **the
reader**, and the content works only in a stronger reader's hands — a statement
about the model, not about instruction. Both outcomes are informative and both
are pre-registered below.

## 2. THE MATERIAL — identical to every prior arm, and the turn-1 drafts are REUSED

The same 17 clauses, in the brief's order. ⭐ **Turn 1 is not re-drawn.** Arm A's
17 stored turn-1 drafts (`ds_opus_loop/out/<id>.turn1.raw.json`) are resumed as
the assistant's first message. Grounds:

1. **It makes the comparison PAIRED, not historical.** Arm B and arm C are both
   historical controls on different draws. Arm D vs the Opus loop is the same
   clause, the same model, the *byte-identical draft* — the only difference is
   who reviews it. That is the cleanest contrast this project has been able to
   construct, and it is free.
2. It removes 17 calls from a $0.12 budget, buying a second review round.
3. **VERIFIED before writing this file, not assumed:** the arm-D system block is
   39,959 chars, sha256 `3a66c5f5…4c34c`, **equal to arm A's recorded sha**; the
   four system files are byte-verified copies (`0463449d`, `92dbd355`,
   `a0c12943`, `7a88183e` — the same four arm B copied); and all **17 of 17**
   rebuilt turn-1 user blocks are byte-identical to the ones stored in arm A's
   transcripts. A resumed transcript that differed by one byte would silently
   measure a different prompt.

⚠️ **Cost of reuse, stated:** arm D therefore has **no independent turn-1
sample**. Any turn-1 rate quoted is arm A's, not a fresh draw, and the arm
cannot speak to turn-1 variance.

## 3. THE DESIGN, AND WHY EACH CHOICE WAS MADE

### 3.1 Two calls per review round: IDENTIFY, then REPAIR

Production forces the output format to the module JSON schema
(`format_forcing: "json_schema"`, `additionalProperties: false`, `strict: true`).
A per-entry verdict therefore **cannot** be returned alongside the module: there
is no field for it and an invented field is a hard rejection.

Rejected by name: (i) **putting the verdicts in `claims`** — it corrupts the
artifact and the very field E6 tests; (ii) **dropping the verdict** — it forfeits
the one measurement the brief calls sharpest and no prior arm could make;
(iii) **turning format forcing off for a single combined call** — it changes the
drafting regime and the module regime at once.

Chosen instead: **the round is two messages.**

* **IDENTIFY call** — `format_forcing: "none"`, output is eleven verdict lines
  and *no JSON*. This is the only departure from production, it is confined to a
  message that produces no module, and it is disclosed.
* **REPAIR call** — `format_forcing: "json_schema"`, byte-identical regime to
  production and to arms A/B/C. The module is produced under the production
  contract.

⭐ **This is not a workaround; it is the instrument.** Splitting identification
from repair makes the brief's decisive readout directly observable: a defect the
model marked `FIX` and did not then repair is *identified-and-unrepaired*; a
defect it marked `PASS` is *never-identified*. Those two want different next
instruments and no prior arm could tell them apart.

### 3.2 Eleven entries, not twenty

The coordinator's own procedure holds that more than ten entries at once means
none are applied properly. Arms B and C already show that **coverage is not the
bottleneck** — 83–87% of their defects were named by an entry the model held — so
trading tail coverage for concentration costs little and tests something new.

Kept, and why: **arm-B entries 1–9** are the nine highest-yield entries as
measured on *these very 17 clauses* in `ORDERING.md`. Added back: **entry 12**
(`prefer` has no negative pole), because arm B reproduced its exact failure
verbatim on two independent clauses, so the class is measurably live; and
**entry 15** (`"or"` in the span), because it names the decisive historical
defect of `l3147_3238_n003`, one of these 17 — excluding it would build a
guaranteed miss into the arm's single best-documented case.

Dropped, and why: **entry 10** (0 "caught" in 17 — it never found a real defect,
only ratified); **entry 11** (3 of 17) and **entry 13** (0 findings in 17); the
**three-item low-yield tail** (0, 1, and a twice-misdirecting entry); and
**entry 14**, which is one of the two entries *measured to create* a clause's
decisive defect, and whose live branch is already covered by E7.
⚠️ **Consequence, stated in advance:** arm D does not test the same list surface
as arms B and C. Any arm-D defect that only a dropped entry covers is scored
**separately** and never counted as a self-review failure.

**All three anti-rules are carried in full, in both rounds.** Anti-rule 2
prevented false charges on ~8 of 17 clauses and is the highest-value line in the
file; withholding it would manufacture harm by design. Anti-rules are
prohibitions, not review questions, and do not count against the eleven.

### 3.3 Entry 5 is AMENDED, not excluded

E5 obeyed correctly was measured to convert an inert constant into a **vacuous
bodied rule** — `no_moral_ambiguity(S) :- scenario(S)` takes a clause scoped to
*some* cases and makes it govern *all* of them. It is not excluded, because it is
the 5th-highest-yield entry (8 of 17) and the failure has a one-sentence guard.
The guard added, verbatim in `messages/review_d.md`: **"Before you change
anything here, ask: is there a case this body is FALSE of? If there is not, leave
the atom exactly as it is"** — plus an explicit *never widen what the clause
governs to satisfy E5*. Whether the guard holds is scored under **H2** below.

### 3.4 The review turn does NOT re-paste the span

The narrowed `SOURCE TEXT` is already in the transcript, in the turn-1 user
block, unmodified. Re-pasting it would cost tokens and would differ from the
Opus loop's feedback turns, which never re-pasted it. Instead the review message
opens with the imperative *"Re-read the SOURCE TEXT in my first message"*.

### 3.5 The message style is the measured-effective one

The loop's own style result: **imperative, one-sentence-per-edit feedback was
performed 100+/100+ and 29/29**, while ~3,900-character *prose critiques* scored
**0/3** — and R56 separates the variables, so the operative property is
**per-item mechanical imperativeness**, not brevity. The review message
therefore fixes the reply format to eleven `E<n>: PASS|FIX — <one sentence>`
lines, forbids "N/A"/"unsure"/"partially", and requires each FIX to name the
field and the new value. The repair message is 4 lines: *"Perform every edit you
wrote after FIX, exactly as you wrote them. Change nothing you marked PASS."*

⚠️ **A self-review instruction is not the same thing as a critic's edit list**,
and this is an extrapolation from the closest available evidence, not a
measurement of it.

### 3.6 Rounds

* **Round 1**, all 17 clauses: IDENTIFY + REPAIR = 34 calls.
* **Round 2**, one forced call per clause (`messages/round2_d.md`): *"check
  whether each FIX you wrote is present in the module you just returned; perform
  any that is missing."* This targets exactly the identified-and-unrepaired
  population, which is the failure mode this arm exists to expose.
* ⛔ **Round 2 starts only if** `ledger + 17 × (1.5 × the measured round-1 repair
  mean) ≤ $0.12`. If the per-call gate then refuses mid-round, round 2 is
  reported as **partial**, with the covered clauses listed. If it does not fit,
  round 2 is **not run** and the arm reports one round.
* Max 3 assistant turns per clause (draft, repair, round-2 repair), inside the
  Opus loop's measured 2–4 convergence window.

## 4. THE FROZEN TURN-1 DEFECT INVENTORY

⭐ Scoring uses `ds_opus_loop/out/<id>.feedback_1.md` — the Opus critic's
span-first adjudication of that exact draft — as the turn-1 defect list. It is
**frozen on disk, written before this arm existed, and not by me after seeing
arm D's output.** Each numbered edit that changes something is one item; "leave X
alone" lines are excluded. Total items are counted and published before scoring.

This also *is* the ceiling: the same items, handed to the same model, by a
frontier critic instead of by itself.

## 5. THE BASELINES, stated before looking

| B# | baseline | value | source |
|---|---|---|---|
| **B1** | turn-1 drafts defect-free | **0 of 17** | arm A |
| **B2** | ⭐ **clauses converged after ONE round of feedback** | **6 of 17** | Opus loop (clauses whose final turn is turn 2) |
| **B3** | Opus-critic edits performed | 100+/100+, 29/29, 101/101 with 1 miss | R56/R61/R62 |
| **B4** | defects named by an entry the model held | 87% (B), 83% (C) | arms B, C |
| **B5** | one-shot-static defect-free rate | 0/15, 0/17 | arms B, C |

## 6. THE BRANCHES

Judged over the 17 round-1 REPAIR modules (and the round-2 modules if run),
adjudicated span-first by me, floor first.

### TRANSFER — any one of:
* **T1 (the strong one).** ≥ **3 of 17** modules carry no defect I would have
  sent an edit for. Baseline 0 of 17; ceiling 6 of 17. 3 is half the ceiling and
  is not comfortably one draw of noise against a floor of zero.
* **T2 (the mechanism claim).** ≥ **50%** of the frozen turn-1 items are repaired
  in the round-1 module. Against a ceiling of ~100% when a critic writes them.
* **T3 (the identification claim).** ≥ **50%** of the frozen turn-1 items are
  *correctly named* by a FIX line — even if not repaired. This is transfer of
  the list's **diagnostic** value and would be a real, separable result: it says
  build a self-diagnosis instrument and drive the repair mechanically.

### NULL
* ≤ 1 module defect-free, **and** frozen items repaired < 30%, **and** frozen
  items identified < 30%.
* ⚠️ A null here is **not** a repeat of arms B/C. It would say the content works
  when applied by a stronger reader and not when applied by the drafter — a
  property of the model, not of the instruction.

### MANUFACTURED HARM — scored separately and reported even if everything else improves
* **H1 regression.** ≥ 3 modules acquire a conclusion-changing defect that the
  turn-1 draft did not have.
* **H2 obedience harm (the R57 / E5 shape).** ≥ 1 defect that is the direct
  product of correctly obeying an entry. **E5's amended guard is on trial here**:
  a vacuous bodied rule appearing in a round-1 module is a failure of my
  amendment and is reported as such.
* **H3 floor regression.** ≥ 3 modules whose turn-1 floor was clean
  (`translated` / `repair_needed=False` / 0 breaches) fail the floor after review.
* **H4 false repair from an anti-rule.** ≥ 1 module "repairs" something the
  anti-rules explicitly protect (a schema-forced tautological binder, a
  contract-required `NEEDS` name in `requires`, or a rewritten read-back).

### THE DECISIVE READOUT, whatever the aggregate says
For every frozen turn-1 item, one of four states, published per clause:
**IDENTIFIED+REPAIRED · IDENTIFIED+UNREPAIRED · NOT-IDENTIFIED · N/A (only a
dropped entry covers it)**. Plus, for every FIX line: was it a **real** defect, a
**false charge**, or an **anti-rule violation**. No prior arm can produce this
table and it is the arm's main product.

## 7. PREDICTIONS, on the record

* **P-a.** Headline is **NULL on T1** — fewer than 3 defect-free. Confidence:
  moderate. Grounds: three arms of nulls, and the positive control differs in the
  reader as well as the delivery.
* **P-b.** **T3 separates from T2** — identification exceeds repair by ≥ 15
  points. Grounds: arms B/C measured 83–87% of defects *named* by a held entry,
  which is evidence the model can recognise these classes in text; what it has
  never been shown to do is act on them. **This is the prediction I hold most
  confidently and it is the one that would redirect the programme.**
* **P-c.** The model marks far more PASS than the frozen list justifies —
  median FIX count per clause ≤ 3 against a median frozen-item count I expect
  near 5. Scored as counts.
* **P-d.** **H2 does not fire**: no vacuous bodied rule appears. This scores my
  E5 amendment. Confidence: low-moderate.
* **P-e.** At least one **false charge** and at least one **anti-rule violation**
  appear across the 17. Grounds: anti-rule 2 is the corpus's most common false
  alarm and self-review has no external check on it.
* **P-f.** Round 2 recovers **fewer than half** of the identified-and-unrepaired
  items. Grounds: the loop's freeze result — a model re-reading its own reply
  reproduces it.

## 8. PROTOCOL COMMITMENTS

1. ⛔ **No tuning after seeing results.** `messages/`, `promptsD/` and
   `config_armd.json` are frozen at the first live call. A second variant would
   have to be pre-registered as such and **both** reported.
2. **The floor runs first** on every module — `schema.validate_all` then
   `checks.run_checks` — and my adjudication is on top of it, never instead.
3. **Span-first adjudication**, exactly as the loop and arms B/C did.
4. ⛔ **READ-ONLY** outside `_debug_gen11/selfreview_arm/`. Nothing under
   `prompt/`, `schema.py`, `runs/`, `translation_sample/runs/`,
   `repair_graveyard/`, `resolve_runs/`, or `ds_opus_loop/` is written. No git is
   run, no branch is switched, no commit is made.
5. **n = 17, single-digit cells throughout.** No rate reported is statistically
   separated from noise. Claims that need no rate carry the verdict.
6. **A null is a real result and is reported as one**, undiluted.

## 9. CONTAMINATION, DISCLOSED

I have read `ds_opus_loop/FINDINGS.md` in full, the section headings of
`RECOMMENDATIONS.md`, and arm B's and arm C's `RESULT.md`/`PREREG.md` in full.
I therefore already know: `l3147_3238_n003`'s decisive defect (the disjunction),
`l1_170_n056`'s three recorded wrong answers, and several `R<n>` findings tied to
named clauses. **I cannot adjudicate these 17 clauses blind and I do not claim
to.** Three mitigations, all structural rather than promises:

* The turn-1 defect list is the **frozen `feedback_1.md` files**, written by the
  Opus critic before this arm existed. I score against them; I do not author
  them.
* The FIX-line classification (real / false charge / anti-rule violation) is made
  against the **span**, and the span text is quoted in the result for every
  contested call.
* Entry selection (§3.2) was fixed by `ORDERING.md`'s **measured yield counts**,
  not by my knowledge of which clause needs which entry. E11 is the one entry
  admitted *because* of a known clause defect, and that is stated, not hidden.

## 10. SPEND

Hard cap **$0.12**, owner-set, enforced in `run_armd.py:CAP_USD` and checked
against the on-disk ledger before **every** send, worst-case-priced.

Estimate. Provider `together-deepseek-v4-flash`, $0.14/$0.28 per Mtok,
`max_tokens` 4096. System 39,959c ≈ 9,990 tok. Round 1 = 34 calls.
* IDENTIFY: in ≈ 13.8k tok = $0.0019; out worst 4,096 = $0.0011 → **$0.0031**.
* REPAIR: in ≈ 17.9k tok = $0.0025; out worst 4,096 = $0.0011 → **$0.0037**.
* **Round 1 worst case ≈ $0.116**; measured rates from the loop (~$0.002/call)
  predict **≈ $0.077**.
* Round 2 is gated on §3.6 and will only run out of the measured surplus.

⛔ Over the cap, nothing is sent. **Refuse over.**

---

**Signed before the first call.** — adjudicator, 2026-08-16
