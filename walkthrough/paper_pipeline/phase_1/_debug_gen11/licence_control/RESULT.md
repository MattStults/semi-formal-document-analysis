# RESULT — THE LICENCE CONTROL

**Answer, on the pre-registered rule: ⛔ NULL on the primary endpoint. Asking the licence
question, alone, in one call, does NOT reach the class. 21 of 26 — 80.8% — inside the
band every non-mover occupies (82.8–100%), nowhere near the two movers (12.5%, 14.3%).**

**Second answer, and it is a clean one: ⭐ the floor cost is SEPARABLE. Zero bodiless
assertions, floor unchanged within noise. The decomposition arm's floor collapse is
decomposition's, not the licence question's.**

**Third, and it is the finding that is neither: ⚠️ the question is not inert.** It cleared
**3 of 15 eligible clauses outright** — and **every other single-call arm, including the
token-identical null replicate, cleared 0 of 15.** The effect is real, directionally
correct, honestly reasoned where it fired, and roughly a quarter of what the movers buy.

**Pre-registration:** `PREREG.md`, signed before the first call, thresholds untouched
afterwards. **Spend $0.03040** of a $0.06 cap, reconciled against `usage.jsonl` at
**zero unattributed rows**. n=17, single-digit cells throughout.

---

## 1. WHAT WAS SENT

One call per clause, turn 1 only, 17 clauses, the same provider / model / temperature as
arms A and A'. **Three gates, all printed before every send:**

* **GATE 1** — system block 39,959 c, sha256 `3a66c5f5…4c34c`. The production block, byte-
  identical. **MEASURED and printed on both sends.**
* **GATE 2** — each of the 17 user blocks equals arm A's user block for that clause with
  **exactly** the 429-char licence question inserted. Checked by *reconstruction* (delete
  the question, require byte equality), not by eyeball, so a template that also dropped
  something could not pass.
* **GATE 3** — worst case of the exact set about to be sent, plus the on-disk ledger,
  against `CAP_USD = 0.06`. Printed $0.0449 for the 17, $0.0027 for the retry.

**The question, as sent** (`config_licence.json:_licence_question`, the whole manipulation):

> ONE QUESTION BEFORE YOU WRITE, and answer it in the module rather than in prose: for each
> NEEDS name listed above, which node established it? If you stamp its `concepts` entry
> `licence: textual`, the CITATION instruction permits only this node's id, so you must be
> able to point to a sentence in this node's own SOURCE TEXT above that says what that
> gloss says. If you cannot point to one, use the licence you can defend instead.

**REWRITTEN, not reused, and the grounds are in PREREG §2.** `decompose_arm/promptsG/
s3_declare.md` Q3 is written for a stage that emits prose (*"Prose and lists. No JSON
yet."*), demands a written-out citation as its answer, and refers back to a commitment made
*"in stage 1"*. This arm has no stage 1 and cannot emit prose — `format_forcing:
json_schema` forces one JSON object. Pasting Q3 would have added a prose channel as a
second variable. The rewrite keeps Q3's three operative moves — *which node established
it*, the citability test, the named fallback — and delivers the answer in the module's own
`licence` field. **Excluded by name:** Q1 (the exclusion test — the instruction
`decompose_arm/RESULT.md` §4 blames for the floor collapse, and an arm carrying it could
not answer this arm's second question), Q2, Q4, Q5, and the three licence definitions,
which the gated system block already carries and restating would have added as emphasis.

## 2. THE MEASUREMENT IS MECHANICAL

`measure.py` imports `arms_review/floor.py` and `arms_review/measures.py` and calls them —
it does not reimplement them. **No span is read anywhere in this arm.** The target class is
`measures.selfcited` unmodified, on the review's own denominator. Every arm in the table
below is scored by that one code path, and it reproduces the review's published counts
(armA 25/26, examples 3/24, forced verdict 24/24) exactly.

⚠️ `decompose_arm` reads **3/21** here, not the **1/18** it published: `layers.py` scored
NEEDS names, `measures.selfcited` scores `requires` names against `concepts`. Different
denominator, not a contradiction. This arm is scored on the second, like every other row.

## 3. ⭐ THE TABLE

| arm | n | floor_clean | **selfcited/requires** | **rate** | errors | asserts | **bodiless** | ont | inp |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| armA_turn1 (unaided) | 17 | 10 | 25/26 | 96.2% | 18 | 34 | 0 | 20 | 49 |
| arm_aprime (**NULL replicate**) | 17 | 11 | 24/29 | 82.8% | 17 | 34 | 0 | 17 | 51 |
| list_in_prompt_insample | 17 | 11 | 24/24 | 100% | 19 | 34 | 0 | 22 | 49 |
| retrieval_arm | 17 | 9 | 24/24 | 100% | 18 | 29 | 0 | 17 | 51 |
| forced_verdict_arm | 17 | 12 | 24/24 | 100% | 10 | 32 | 0 | 16 | 56 |
| **⭐ licence_control** | **17** | **9** | **21/26** | **80.8%** | **14** | **36** | **0** | **15** | **51** |
| examples_arm | 17 | 13 | 3/24 | 12.5% | 10 | 33 | 0 | 17 | 54 |
| decompose_arm | 13 | 3 | 3/21 | 14.3% | 21 | 31 | **13** | 4 | 18 |

Outcome mix: 9 `translated` / 8 `invalid` (armA 10/7, null 11/6). Errors are 13 schema
breaches + 1 `clingo-error`; polarity mismatches **0** in every arm; arity mismatches 0.
Closure mix `cepa` 20 / `cnpa` 9 (armA 25/4, null 16/8).

### 3.1 The pre-registered rule, applied

**Primary endpoint — rate ≥ 65% ⇒ the effect belongs to the demonstration or the
decomposition.** Measured **80.8%**. The rule fires. The 26–64% "partial" band is empty and
was not entered.

⚠️ **The denominator did not collapse — H-2 does not fire.** `requires_names` = **26**,
identical to armA's 26 (null 29). The model did not evade the question by dropping NEEDS
names; it kept them and mostly kept stamping them `textual`.

### 3.2 ⚠️ The effect is small but it is NOT zero, and this is the honest middle

The continuous rate hides where the movement is. Clauses **fully cleared** — armA had ≥1
self-cite, the arm has none:

| arm | clauses cleared / eligible |
|---|---|
| armA_turn1 | 0 / 15 |
| list_in_prompt_insample | **0 / 15** |
| retrieval_arm | **0 / 15** |
| forced_verdict_arm | **0 / 15** |
| **arm_aprime (null replicate)** | **0 / 15** |
| selfreview / bucketed | 0 / 8, 0 / 8 |
| **⭐ licence_control** | **3 / 15** — `l171_426_n022`, `l1_170_n056`, `l4252_4482_n005` |
| armA_CONVERGED (gold, after repair) | 3 / 15 |
| decompose_arm | 9 / 12 |
| examples_arm | 12 / 15 |

**Five of six single-call interventions — including a 20-entry prose list, a filtered
retrieval list, required check fields, and a token-identical null draw — cleared exactly
zero clauses. This one cleared three.** That is outside the null band on this reading
(null-vs-A differs at 1 of 17 on the target class; this arm differs at 4 of 17, three of
them clearances and one a regression, `l3239_3382_n002` 3→4).

⭐ **And where it fired, it fired for the right reason.** The licence mix on `requires`
names is the sharpest cut in the arm — every non-mover is 100% `textual` with **zero**
`assumed`:

| arm | `requires`-name licences |
|---|---|
| armA_turn1 | textual 25, assumed 0 |
| arm_aprime (null) | textual 24, assumed 0 |
| forced_verdict_arm | textual 24, assumed 0 |
| **licence_control** | **textual 21, assumed 5** |
| examples_arm | textual 3, assumed 21 |
| decompose_arm | textual 3, assumed 15, world 3 |

All five re-licensed entries carry an `inference`, and the inferences are correct:

```
l1_170_n056   user_authority/1  assumed  "the node's NEEDS contract supplies this meaning;
                                          the source text itself only says 'user request'…"
l171_426_n022 root_authority/1  assumed  "the node's NEEDS block supplies this concept;
                                          the source text does not define it"
```

**The model is not failing to understand the question. On 3 of 15 clauses it answers it
correctly and completely; on the other 12 it does not act on it at all.** That is a
compliance failure at 39 KB of competing instruction, not a comprehension failure — which
is exactly the hypothesis `decompose_arm/RESULT.md` floated (*"whether it would survive
alongside the other 39 KB is untested"*). **It survives on a fifth of the clauses.**

## 4. ⭐ THE SECOND QUESTION — the floor cost is SEPARABLE, cleanly

Pre-registered rule: **bodiless asserts ≤ 1 AND floor_clean ≥ 9 of 17 ⇒ SEPARABLE.**

| | armA | null A' | **licence_control** | decompose (×17/13) |
|---|--:|--:|--:|--:|
| `asserts` | 34 | 34 | **36** | 31 (≈40) |
| ⛔ **of those, NO body at all** | 0 | 0 | **0** | **13 (≈17)** |
| floor_clean | 10 | 11 | **9** | 3 (≈3.9) |
| error findings | 18 | 17 | **14** | 21 |
| schema breaches | 18 | 17 | **13** | 21 |

**Zero bodiless assertions. `asserts` went UP (36 vs 34), not down. Errors and breaches
went DOWN.** `floor_clean` = 9 meets the threshold at its boundary, one below armA's 10 and
two below the null's 11 — and the measured null-vs-A noise on `floor_clean` is **3 of 17**,
so a 1–2 clause difference is not interpretable at this n and is not interpreted here.

⭐ **This is the arm's most transferable result.** The decomposition arm bought the target
class and paid 10-of-13 invalid for it, via 13 of 31 bodiless assertions. **The licence
question is not what charged that price.** The bill belongs to stage 3's exclusion test
knocking out `ontology` entries with nothing replacing them — a mechanism this arm
deliberately did not carry, and correspondingly did not reproduce.

⚠️ **One directional caution, under-powered and stated as such.** `ontology` entries fall
15 vs armA 20 / null 17 — the same *direction* decomposition collapsed in (20 → ~5), at a
tiny fraction of the magnitude, and inside the arm-to-arm spread (forced verdict 16,
retrieval 17, examples 17). **INFERRED, not measured, and n=17: no claim is made on it.**
It is flagged because if this question is ever scaled up, that is the column to watch.

### Pre-registered harms, scored

* **H-1 over-correction — DOES NOT FIRE.** Non-`requires` concepts stamped `assumed`: 26,
  against armA 31 and the null 24. Names the module genuinely coined were not pushed off
  `textual`. The discrimination is targeted.
* **H-2 denominator collapse — DOES NOT FIRE.** `requires_names` 26 = armA's 26, far above
  the 20 floor the prereg set for declaring the endpoint confounded.
* **H-3 recency degradation — DOES NOT FIRE on asserts** (36 vs 34) **or inputs** (51 vs
  49/51). See the `ontology` caution above, which is the one column that leans.

## 5. SPEND, RECONCILED AGAINST THE LEDGER

**$0.03040 of a $0.06 cap** — 18 sends: 17 recorded + 1 that raised. Estimate was $0.030;
worst case gated at $0.0449.

⚠️ **The measured hole did not fire this time, and that is a measurement, not an
assumption.** `_log_usage` runs before `_check_envelope`, so a truncated or empty
completion is billed while writing no arm record. `l1368_1541_n019` raised
**`ProviderError HTTP 503 service_unavailable`** on the first pass. `reconcile.py` over the
stamped ledger window found **16 rows for 16 records, $0.028486 = $0.028486, zero
unattributed** — a 503 is refused upstream of generation and is not billed. The clause was
re-sent under the prereg's §8 retry clause (the only retry in the arm, named here), and the
final reconciliation is **17 rows / 17 records / $0.030404 / zero unattributed / zero
truncated.** `out/` and the ledger agree to the cent; the ledger figure remains the figure
of record.

⚠️ **Attribution is weaker than arm A-prime's and is recorded as weaker.** A' separated its
rows from a concurrent arm by prompt size; that was unavailable here, since A' sends the
same 39,959-char block to the same model. The first matcher keyed on
`(prompt_tokens, completion_tokens, cost_usd)` and matched **0 of 16** — because
`complete_messages` returns `cost_usd` but no usage dict, so every record on disk (this
arm's and `arm_aprime/out/`'s alike) carries `"usage": null`. The matcher is therefore a
**multiset match on `cost_usd` inside a line-stamped window**, which cannot tell this arm's
row from another arm's row of identical cost. The zero residue is the guard, not the match.
`arm_aprime` was **complete and idle** (all 17 modules on disk) before this arm sent.

## 6. ⭐ WHAT THIS BUYS THE SERIES

1. **The two movers' confound is now half-resolved, in the direction neither arm guessed.**
   Asking is **not sufficient** — it recovers ~20% of the class where demonstration and
   decomposition recover ~85%. Both movers' write-ups treated "maybe it's just the asking"
   as the deflationary explanation of their result. **It is not the explanation.** Their
   mechanisms are doing most of the work.
2. **But asking is not nothing, and it is the only cheap thing that has ever moved this
   class.** 3 of 15 clauses cleared, against 0 of 15 for four other single-call
   interventions and for a token-identical null draw, at **$0.030 and 429 characters**.
3. **The floor cost is decomposition's alone.** Anyone tempted to reject the licence
   question because arm G's floor collapsed should not: **0 bodiless assertions, 36
   asserts, 14 errors — better than unaided on two of those three.**
4. ⭐ **The obvious next arm, and this one has a measured reason behind it rather than a
   hunch:** the question is understood and correctly answered where it is answered, and
   ignored elsewhere. That is a salience problem, not a content problem. **The examples arm
   is the same question made unignorable by demonstration** — which now looks like the
   mechanism, and is testable: 6 demonstrations vs 1 demonstration vs the bare question,
   same call, same block. The bare-question end of that ladder is now measured and costs
   $0.030.

## 7. LIMITS, stated plainly

* **n = 17, single-digit cells.** "3 of 15 cleared" is three clauses. It clears the
  measured null band on the target class (1 of 17 draw-to-draw) but it is three clauses.
* **One draw.** No second sample of this arm; the null replicate is the only noise estimate
  and it is a replicate of arm A, not of this arm.
* **One model, one provider, one temperature** (DeepSeek-V4-Flash-0731, 0.2). Nothing here
  claims cross-model behaviour.
* **The wording is one wording.** A null on one phrasing of "ask about licences" is not a
  null on the intervention class. It is a null on this sentence, in this position, in this
  block — which is precisely what the two movers left unmeasured, and is now measured.
