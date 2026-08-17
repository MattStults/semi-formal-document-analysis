# ORDERING — `REVIEW_LIST.md` ranked by EVIDENCE, not by mention count

## Why mention counts are useless here

The loop's protocol required the adjudicator to report on **every** entry on
**every** clause, so raw mentions are a measure of the protocol, not of the
entry. Measured over the 17 `*.turns.md` + `*.lessons.md` files:

| entry | files mentioning it | | entry | files mentioning it |
|---|---|---|---|---|
| P1 | 17 | | N1 | 17 |
| P2 | 17 | | N2 | 17 |
| P3 | 16 | | N3 | 15 |
| P4 | 15 | | N4 | 16 |
| P5 | 17 | | N5 | 15 |
| P6 | 16 | | N6 | 16 |
| P7 | 15 | | N7 | 17 |
| P8 | 16 | | N8 | 17 |
| P9 | 17 | | N9 | 17 |
| P10 | 16 | | N10 | 17 |

Range 15–17 out of 17. **The metric has no variance and cannot order anything.**

## The metric that does order them

Per entry, the number of **DISTINCT CLAUSES on which it produced an actual
FINDING** — a defect charged, a call reversed, or a drafted remedy changed — as
opposed to "checked, nothing". Read off the `FROM-LIST` / `FRESH, and
independently on the list` / `CHECKED and CLEAN` / `Examined and DECLINED`
sections of all 17 clause records.

Two sub-columns, because they are different kinds of value:

* **CAUGHT** — the entry did work the adjudicator did *not* do: missed blind,
  reversed a clean call, or refuted/rewrote a drafted remedy. This is the
  entry's *marginal* value.
* **RATIFIED** — the entry independently named a defect already found blind.
  Real value (it is why a call with no answer key could be signed) but not
  marginal.

⚠️ **MEASURED on 17 clauses, single-digit cells throughout. INFERRED wherever
this note orders two entries whose totals differ by 1.**

Population: the 15-clause loop plus the 2 pilot clauses (`l1_170_n056`,
`l3147_3238_n003`) = **17**.

---

## THE TABLE

| rank | entry | CAUGHT | RATIFIED | total clauses with a finding | recorded FAILURES of the entry |
|---:|---|---:|---:|---:|---|
| 1 | **P8** tautology / gloss restates its name | **7** | 5 | **12** | 1 (R78: a two-step chain passes P8) |
| 2 | **N7** excepted branch is a hole; `cepa` → `unclear` | 3 | 7 | **10** | — (applied beyond its measured case 2×) |
| 3 | **N10** every coined symbol traces to a substring | 4 | 6 | **10** | 3 (R58 ×2: checks the name, not the gloss; R76: fused names pass) |
| 4 | **P6** content sourced outside the narrowing | 3 | 5 | **8** | 1 (R64: false charge on node-header vocabulary) |
| 5 | **N1** bodied rule vs inert ground constant | 3 | 5 | **8** | 2 (passed a body firing on the wrong set, twice) |
| 6 | **P3** claim in `claims`, encoded nowhere | 4 | 3 | **7** | 3 (blind when claims *carry* the error; misses a 2nd fingerprint form; passes a claim encoded by an inert rule — R72) |
| 7 | **P7** defeasibility must be RECORDED | 4 | 3 | **7** | — (but see N5 below: P7+N5 obeyed together produced a defect) |
| 8 | **P5** scope drift, both directions | 1 | 6 | **7** | — |
| 9 | **N8** argument order of an arity ≥ 2 relation | 2 | 2 | **4** | needed widening (R65) to fire at all |
| 10 | **P9** (corrected) coined name declared and unused | 0 | 4 | **4** | 1 (R65: blind to a coined duplicate of a used name). ⭐ Its *corrected* form is the run's single most-used **false-charge preventer** (~8 clauses) |
| 11 | **N3** diff `ESTABLISHES` against the span both ways | 1 | 3 | **4** | **never fired alone** — every hit is co-extensive with P6 and/or N10 |
| 12 | **N9** count the finite verbs before drafting | 1 | 2 | **3** | its motivating payoff (predicting repair exhaustion) **never recurred**: non-convergence in the run was zero |
| 13 | **P1** polarity: does a `prefer` name the act to AVOID? | 1 | 2 | **3** | — |
| 14 | **N5** "without X" must be POSITIVE, never NAF | 0 | 2 | **2** | ⛔ **1 MEASURED HARM (R57): obeyed correctly, it CREATED the clause's decisive defect.** Its asymmetry is polarity-dependent and the entry does not say so |
| 15 | **N2** strip the matrix verb | 1 | 1 | **2** | its remedy was offered and **declined by name** once (R63) as forbidden by N1 + rule 8 |
| 16 | **N4** a qualifier in a list bounds ONE item | 0 | 1 | **1** | ⛔ **2 recorded mis-directions** — would have pushed the wrong way on `l171_426_n022` and reached the right answer for the wrong reason on `l699_796_n012` |
| 17 | **P4** disjunction encoded as conjunction | 0 | 1 | **1** | ⛔ **in-sample only** (its own clause). 2 recorded mis-directions: the P4 reflex points the wrong way under a negative-scope `or` (De Morgan), twice |
| 18 | **P10** both poles of a GOOD/BAD example must differ | 0 | 1 | **1** | ⛔ **in-sample only** (its own calibration clause). No GOOD/BAD pair occurred in the other 16 |
| 19 | **P2** deontic force on a non-norm | 0 | 0 | **0** | ⛔ **0 in 17. And on `l4252_4482_n005` it ENDORSED the decisive defect** (`permit` where the span obliges): P2 confirmed the bearer was the assistant and nothing on the list asked whether the *strength* was right (R77) |
| 20 | **N6** "regardless of X" → `forbid_body` | 0 | 0 | **0** | ⛔ **0 in 17.** Every single mention is inside a "checked, clean" or "did not happen" list |

### The anti-rules, scored on a different axis

They exist to **prevent false charges**, so a finding count is the wrong metric.

| anti-rule | findings | false charges prevented | note |
|---|---:|---:|---|
| A2 `requires-unprovided` fires on every correct module | 0 | **~8 clauses** | the single highest-value item in the file by this measure; with corrected-P9 it is what keeps contract-2 `NEEDS` names from being "fixed" |
| A3 never rewrite the read-back to agree with `status` | **3 (2 of them decisive)** | — | ⭐ **inverted a drafted remedy twice** (`l699_796_n012` F3, `l2821_3040_n017` F9). R33: its stated scope (`status` only) is too narrow — its mechanism covers *any* independently-written pair |
| A1 `forbid X(R) :- X(R)` is schema-forced | 0 | 2 | |

---

## WHAT THIS TABLE IS, AS A RESULT IN ITS OWN RIGHT

1. ⭐ **The list's mass is in five entries.** P8, N7, N10, P6, N1 account for
   **48 of the 82** clause-findings and **20 of the 27** CAUGHT. A translator
   that only ever ran those five would get most of the measured value.

2. ⛔ **Five entries are retirement candidates on this evidence.**
   * **N6** and **P2** — 0 findings in 17 clauses. P2 is worse than idle: it
     actively *endorsed* the decisive defect on one clause.
   * **P10** and **P4** — 1 finding each, both **on the clause the entry was
     written from**. Zero out-of-sample yield, and P4 has two recorded
     mis-directions.
   * **N4** — 1 finding, 2 mis-directions. It has never charged a defect that
     was not already charged by something else.

3. ⛔ **N5 is the one entry MEASURED to cause harm when obeyed** (R57). It is
   kept in arm B only with its polarity condition attached; shipping its
   unconditioned form into a *drafting* prompt would be shipping a known defect.

4. **P8 is the surprise.** It is the shortest entry in the file, it asks about a
   field (`gloss`) that changes no conclusion, and it is the top scorer by both
   sub-metrics. **INFERRED explanation** (not measured): it is the only entry
   whose test is purely local and syntactic — it needs no reading of the span at
   all — which is exactly the kind of check a blind adjudicator skips and a
   drafter could in principle run mechanically. If any entry transfers to the
   translator, the prior says it is this one.

5. **N3 is redundant, not wrong.** 4 findings, all co-extensive with P6/N10. It
   is kept (it is cheap, and it states the *both directions* half that P6 does
   not) but it should never be counted as independent evidence.
