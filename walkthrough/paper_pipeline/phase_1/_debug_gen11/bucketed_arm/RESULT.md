# RESULT — ARM G: lens-grouped BUCKETS of PROCEDURES, each turn returning a MODULE

**Answer: NULL, and it is a null BELOW arm D. 2 of 91 frozen defects fixed (2.2%)
against arm D's 11 of 91 (12%), on the byte-identical drafts of the same nine
clauses. Bucketing is not the answer, and D was not measuring overload.**

**Spend: $0.09225 measured** against a **$0.12** cap. **36 of 36 calls completed,
zero truncations.** `PREREG.md` signed before the first call and unedited since.

⛔ Nothing outside `_debug_gen11/bucketed_arm/` was written. No git was run, no
branch switched, no commit made. `decompose_arm/` was not touched. `runs/`,
`translation_sample/runs/`, `repair_graveyard/`, `ds_opus_loop/` and
`selfreview_arm/` were read only.

---

## 1. PAIRING VERIFIED BEFORE SENDING

| | value |
|---|---|
| system block | 39,959 chars, sha256 `3a66c5f5…4c34c` |
| **equal to arm A's / arm D's recorded sha** | ✅ gated; the run refuses to send otherwise |
| turn-1 user blocks rebuilt vs arm A's stored transcripts | **9 of 9 byte-identical** (gated) |
| turn-1 assistant drafts | **arm A's own**, resumed, not re-drawn |
| clauses | the **9 arm D completed** — see `PREREG.md` §2 for why 17 × 4 buckets cannot be run at $0.12, and for the inherited selection bias |

⭐ **Paired against arm D on the same drafts.** The manipulation is delivery:
same eleven entries, same three anti-rules, verbatim content; 2–3 per turn
instead of 11 at once, phrased as enumeration procedures instead of questions,
and **no verdict field anywhere** (arm F's 102/102 rubber stamp made a verdict
field unscoreable, so there is none to score).

## 2. THE DECISIVE TABLE — MEASURED off the returned modules only

Denominator: **arm D's own frozen per-clause item counts** over the Opus critic's
`ds_opus_loop/out/<id>.feedback_1.md`, written before either arm existed. I did
not re-author or re-count them.

| clause | frozen items | modules changed at bucket | **fixed** | **missed** | **newly introduced** | floor T1 → G |
|---|---:|---|---:|---:|---:|---|
| `l699_796_n012` | 5 | — | 0 | 5 | 0 | translated → translated |
| `l1001_1107_n005` | 9 | — | 0 | 9 | 0 | translated → translated |
| `l2474_2554_n004` | 29 | — | 0 | 29 | 0 | invalid 2b → invalid 2b |
| `l3239_3382_n002` | 4 | **b1** | **1** | 3 | 0 | **invalid 2b → translated** |
| `l3239_3382_n004` | 30 | b1, **b4** | 0 | 30 | **1** | invalid 2b → invalid 2b |
| `l171_426_n022` | 3 | — | 0 | 3 | 0 | invalid 4b → invalid 4b |
| `l1707_1973_n006` | 4 | — | 0 | 4 | 0 | translated → translated |
| `l3596_3876_n009` | 4 | — | 0 | 4 | 0 | translated → translated |
| `l4252_4482_n016` | 3 | **b3** | **1** | 2 | 0 | translated → translated |
| **TOTAL** | **91** | **3 of 9 modules ever changed** | **2 (2.2%)** | **89** | **1** | 1 improved, 0 regressed |

### Per bucket — the ledger the design was built to produce

| bucket | lens | entries | modules changed | fixed | introduced | cost |
|---|---|---|---:|---:|---:|---:|
| 1 | right CONTENT here | E6, E3, E4 | 2 of 9 | **1** | 0 | $0.01869 |
| 2 | right LOGICAL FORM | E11, E8, E5 | **0 of 9** | **0** | 0 | $0.02164 |
| 3 | right FORCE | E10, E7, E2 | 1 of 9 | **1** | 0 | $0.02458 |
| 4 | HYGIENE + anti-rules | E1, E9, recursion | 1 of 9 | 0 | **1** | $0.02734 |

⛔ **Bucket 2 is nine calls, $0.02164, and not one byte of any module changed.**
Every bucket-2 module is semantically identical to its bucket-1 input on all nine
clauses.

### The two fixes, both real

* ⭐ **`l4252_4482_n016`, bucket 3 — the clause arm D got most flagrantly wrong.**
  D answered `E10: PASS` on a module asserting `prefer repeat_user_prompt(R)`,
  `prefer include_redundant_phrase(R)`, `prefer include_redundant_idea(R)` on a
  span that says to **avoid** those three acts. Arm G renamed all three to
  `minimize_repeating_user_prompt` / `minimize_redundant_phrases` /
  `minimize_redundant_ideas` in `acts` and in every assert, kept `prefer`, kept
  every body and every `read_back` word for word — the critic's frozen item 1,
  performed verbatim. **The pipeline's own `prefer-polarity` detector goes 3 → 0.
  That is measured by a deterministic checker, not by me.** Frozen item 2 is
  half-done: the three `closure` `act_class` values were renamed to match, but
  all three are still `cepa`, not `unclear`. Frozen item 3 untouched.
* **`l3239_3382_n002`, bucket 1** — `overstep(A)` added to `acts`, the critic's
  frozen item 2. Two schema breaches clear and the floor goes **invalid →
  translated**. The item's second half (a separate variable for the assistant, so
  `A` is not both assistant and action) was not done.

### The one newly introduced defect, and it is an H2

⛔ **`l3239_3382_n004`, bucket 4, created by correctly obeying the procedure.**
Bucket 4 step 1 is E1: a gloss that restates its name passes zero information —
add to it. The module's gloss was *"T is a transformation task."*, which is E1's
own quoted failure shape. Arm G expanded it to *"T is a task asking the assistant
to transform text, such as **translating between languages, adding annotations, or
changing formatting**."* The critic's frozen item 7 says, in those words, to
**delete "translating between languages", "adding annotations" and "changing
formatting"** from that gloss. They were not in the draft. **Bucket 4 imported
them.** Bucket 1's E3 tracing procedure — run three turns earlier on the same
conversation — is the entry that forbids exactly this. **H2 FIRES: obeying one
entry manufactured the defect another entry exists to prevent, and the earlier
turn did not protect against the later one.**

## 3. SCORED AGAINST THE PRE-REGISTRATION

| branch | threshold | measured | |
|---|---|---|---|
| **TRANSFER** | ≥27/91 fixed ∧ ≤2 modules harmed | 2/91 | ❌ |
| **NULL** | ≤18/91 fixed | **2/91** | ✅ **NULL** |
| **H1 manufactured harm** | ≥3 of 9 modules acquire a conclusion-changing defect | **0 of 9** | ✅ did not fire *(arm D: 3 of 9)* |
| **H2 obey-and-break** | ≥1 | **1** | ⚠️ **FIRED** (bucket 4 / E1, itemised above) |
| **H4 anti-rule breach** | ≥1 | **0** | ✅ did not fire |
| **H5 over-editing** | ≥3 modules edited off-lens, or introduced ≥ fixed | 1 module off-lens; 1 introduced vs 2 fixed | ✅ **did not fire** |
| **H6 stasis-null** | ≥6 of 9 byte-identical across all four buckets | **6 of 9** | ⚠️ **FIRED** |

**Predictions.** **P1 ❌ badly** — I predicted 20–35% fixed; measured 2.2%, and
in the wrong direction relative to arm D. **P2 ✅** — bucket 3 carried the only
detector-verified multi-defect fix, on the clause and the entry I named in
advance. **P3 ❌** — over-editing did not fire; the arm's failure is the
opposite, inaction. **P4 ✅** — the borrowed-gloss class did not move: **not one
`licence`, `cites` or `inference` field changed anywhere in 36 calls**, and
`l171_426_n022`'s four *borrowed-but-has-no-gloss* schema breaches survived all
four buckets. **P5 ✅** — the amended E5 created **no** vacuous body; on
`l3239_3382_n004` the two unbound atoms were enumerated by bucket 2 step 3 and
**left exactly as they were**, which is what the amended gate instructs when no
discriminating body can be written. (It is also, on that clause, the wrong
answer — the critic wanted them deleted — so the amendment's guard is holding at
the cost of inaction. n=1 firing.) **P6 ✅** — 6 clauses identical on 4 of 4.
**P7 ✅** — 0 truncations of 36.

## 4. ⛔ THE CONFOUND, AND IT IS THE ARM'S MOST IMPORTANT FINDING

**MEASURED, from `semi-formal-experiment/usage.jsonl`: `reasoning_chars` is
exactly 0 on all 36 arm-G calls.** Arm D's IDENTIFY calls ran **3,585–19,384**
reasoning chars; its forced REPAIR calls ran 0.

Arm G varied **two** things at once, not one:

1. eleven entries in one turn → 2–3 per turn, procedurally phrased; **and**
2. a free-text unforced turn before the module → **no free-text turn at all.**

Arm D's 11 repairs all came downstream of a turn in which the model wrote 3.5k–14k
characters of unstructured reasoning. Arm G asked for a module directly under
production's `response_format`, and the model generated **zero** reasoning
characters and changed **six of nine modules not at all**. The two fixes it did
make are on the two clauses whose defect is visible in the JSON without any
inference (a `prefer` whose read-back contradicts it; an act asserted and not
declared).

⭐ **The most economical reading of arms D and G together is that D's 11 fixes
were bought by the SCRATCHPAD, not by the list, and arm G removed the
scratchpad in the act of removing the verdict.** That is a hypothesis this arm
cannot settle — it would need a bucketed arm with a free-text step restored — but
it is now the leading one, and it was not visible before.

**This is a real limit on the headline.** The brief's decision rule was: *if
identification stays flat, D measured a capability limit and the argument moves
to detectors.* Identification did not stay flat — **it fell** — and the honest
attribution for the fall is at least as much "no scratchpad" as "bucketing did
not help". What arm G rules out is the specific hypothesis it was built for:
**delivering the checks in small lens-grouped buckets, as procedures, does not
recover diagnosis. There is no overload effect to exploit at 3 checks per turn.**

## 5. WHAT THE PROCEDURES MISSED THAT A DETECTOR ALREADY CATCHES

The pipeline's own deterministic floor, run for free on every module, names
defects the four procedures enumerated and walked past:

* `l2474_2554_n004` — *act named in an assertion but not in `acts`* + *closure
  declared for an act class the module does not govern*, **2 breaches surviving
  all four buckets.** This is the **identical defect shape bucket 1 fixed on
  `l3239_3382_n002`.** The same procedure, in the same run, fixed it on one
  clause and missed it on another.
* `l171_426_n022` — four *borrowed but has no gloss* breaches (`applies_to/2`,
  `authority_hierarchy/2`, `content_authority/2`, `instruction_authority/2`),
  surviving all four buckets, **despite bucket 4 step 2 saying in terms "list
  every predicate in the module of arity ≥ 2, coined or borrowed."** The
  enumeration was instructed, is mechanical, and was not performed.
* `l3239_3382_n004` — two *unbound ontology atom* breaches surviving all four.
* `l3239_3382_n002` — `overstepping(A) :- …, overstepping(A)`, a head in its own
  body, is the critic's frozen item 1 and is **exactly what bucket 4 step 3
  enumerates.** It is not the `forbid X(R) :- X(R)` shape the anti-rule protects.
  Untouched.

⭐ **Arm D's redirect survives arm G and is strengthened: build detectors.** Every
defect in this list is already detected, for free, with no model call, by code
that ran on every one of these modules while the model was failing to enumerate
them.

## 6. WHICH CHECKS COULD NOT BE CONVERTED — pre-declared in `PREREG.md` §4

Converted cleanly (mechanical enumeration, output is an edit): **E6, E3, E1, E9,
E10, E5**, head-in-own-body.
Converted only partly (enumeration mechanical, per-item decision still a
judgement): **E11**, **E2**, **E7**.
**NOT CONVERTED: E4 and E8.** "Is every asserted predicate supported by the
narrowed text" and "does each body widen past the span's qualifier" have no
enumeration whose output is an edit.

⚠️ **The conversion succeeded and did not help.** The one bucket whose entries
are *most* mechanical (bucket 4: gloss-restates-name, argument order,
head-in-own-body — all three fully convertible, two of them already schema
checks) produced **zero fixes and the run's only new defect.** Convertibility was
not the binding constraint.

## 7. COST PER DEFECT FIXED — the 4-bucket design loses per dollar too

| | spend | defects fixed | **$ / defect** |
|---|---:|---:|---:|
| **arm G**, 4 buckets, 36 calls, 9 clauses | $0.09225 | **2** | **$0.046** |
| **arm D**, 2 calls/clause, 9 clauses | $0.07026 | **11** | **$0.0064** |

**Arm G is 7.2× more expensive per defect fixed than the single-turn arm it was
built to beat.** Bucket 2 alone spent $0.02164 for zero edits — 23% of the arm's
budget on a bucket with no output at all. The pre-registered requirement that a
4-bucket design beat a 1-call baseline per dollar as well as per defect **is not
met on either axis.**

## 8. LIMITS — read before quoting any number

* ⚠️ **n = 9, and every cell is single-digit.** "2 of 91" and "11 of 91" are 2
  fixes against 11 fixes. Nothing here is statistically separated from noise;
  the argument rests on the *direction* plus the mechanism in §4, not on the rates.
* ⛔⛔ **THE CONFOUND IN §4 IS NOT A FOOTNOTE.** Bucketing and the removal of the
  free-text turn were varied together. Arm G does not isolate bucketing.
* ⚠️ **The sample is arm D's completed 9**, which D lost its other 8 to a
  truncation correlated with reasoning length. Arm G inherits that bias exactly.
  Pre-declared in `PREREG.md` §2, not discovered here.
* ⚠️ **Item counting is coarse** on the two clauses carrying 29 and 30 critic
  edits; they contribute 59 of the 91 denominator and 0 fixes on both arms.
  Excluding them: arm G 2 of 32 (6%), arm D 7 of 32 (22%). **The shape does not
  change.**
* ⚠️ Two fixes are scored on the item's headline defect where the frozen item
  bundles two changes (`l3239_3382_n002` #2, `l4252_4482_n016` #1); both partials
  are itemised in §2 so a reader can score them at 1.0 or 0.5. At 0.5 each the
  rate is 1 of 91.
* ⚠️ **CONTAMINATION.** I read arm D's `RESULT.md` in full and arm F's headline
  before designing this arm, and P2 encodes knowledge of D's worst miss.
  Disclosed in `PREREG.md` §9. Mitigation is structural: the denominator is the
  Opus critic's frozen `feedback_1.md`, and every numerator is read off returned
  JSON, with the two headline fixes independently confirmed by the pipeline's own
  deterministic detectors (`prefer-polarity` 3 → 0; schema breaches 2 → 0).
* ⛔ **Nothing was tuned after results were seen.** `messages/`, `promptsG/` and
  `config_armg.json` are byte-unchanged since the first live call. No second
  variant was run. Buckets were sent in order 1→4 with the gate re-priced against
  measured spend before each.

## 9. SPEND, RECONCILED

**$0.09225 measured**, cap **$0.12**. The on-disk ledger and `usage.jsonl` agree
exactly this time: **36 rows, prompt 12,022–22,175 tokens, `truncated: false` and
`reasoning_chars: 0` on every one.** ⚠️ `loop.py`'s ledger hole did not bite
because nothing truncated; it remains unfixed.

⚠️ **A sibling arm was writing to `usage.jsonl` throughout this run** —
interleaved rows with prompt 2,413–3,549 tokens, `reasoning_chars` 7,153–14,446
and `truncated: true`, a shape that is not arm G's (arm G's smallest prompt is
12,022 tokens and none reasoned at all). **Their cost is not counted here.**
Whoever reconciles `spend.py` for this window must split it by prompt shape, not
by row count.

---

**Adjudicated span-first, floor first, against a defect list frozen before this
arm existed. A null is reported as a null, and it is a null below the arm it was
built to beat. — adjudicator, 2026-08-16**
