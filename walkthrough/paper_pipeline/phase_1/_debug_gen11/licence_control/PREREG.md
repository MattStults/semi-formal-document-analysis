# PREREG — THE LICENCE CONTROL

**Signed before the first call.** Every threshold below is fixed here and is not
touched afterwards. The baseline table in §3 was computed from data already on disk,
by `measure.py`, before anything was sent.

---

## 1. THE QUESTION THIS ARM ANSWERS

Two arms moved the target class — **a borrowed `NEEDS` gloss stamped `licence: textual,
cites: <this node>`**, which `00_task.md` calls *"the single worst failure available
here."* The examples arm moved it with 6 worked demonstrations; the decomposition arm
moved it with a 4-stage build whose stage 3 asks *"which of these names did another node
establish?"*. **Both arms added the licence question and something else, and both said so
in their own write-ups.** `decompose_arm/RESULT.md` names this control and its price
(~$0.04) and does not run it:

> *"A single-call arm can carry the same sentence; whether it would survive alongside the
> other 39 KB is untested, and is the obvious next arm — a one-call control with only the
> licence question appended. It costs ~$0.04 and it would separate the two explanations.
> It was not run."*

**Exactly one variable is added: the question.** No worked examples, no stages, no review
list, no other check. The system block is the production block, gated byte-identical
(`3a66c5f5…4c34c`, 39,959 chars). The added text lives in the USER block, via
`user_template` in this arm's own config — which is the only place it can live without
disturbing the gated system block.

## 2. THE QUESTION AS SENT — REWRITTEN, NOT REUSED, AND WHY

`decompose_arm/promptsG/s3_declare.md` Q3 could not be pasted in. It is written for a
transcript stage that emits **prose** (`Prose and lists. No JSON yet.`), it demands a
written-out citation and a written-out sentence as its answer, and it refers to a
commitment the model made *"in stage 1"*. This arm has no stage 1 and cannot emit prose:
`format_forcing: json_schema` forces one JSON object. Pasting Q3 would either add a second
variable (a prose channel) or ask for an answer the response format forbids.

So it is **rewritten to preserve Q3's operative core and nothing else** — (i) *which node
established this name*, (ii) the citability test that follows from this node's own
CITATION instruction, (iii) the named fallback when the test fails — with the answer
delivered *in the module's own `licence` field* rather than in prose:

> ONE QUESTION BEFORE YOU WRITE, and answer it in the module rather than in prose: for
> each NEEDS name listed above, which node established it? If you stamp its `concepts`
> entry `licence: textual`, the CITATION instruction permits only this node's id, so you
> must be able to point to a sentence in this node's own SOURCE TEXT above that says what
> that gloss says. If you cannot point to one, use the licence you can defend instead.

**Deliberately excluded, by name.** The three licence definitions (`textual` / `assumed` /
`world`) are NOT restated — `00_task.md` already carries them in the gated system block,
and repeating them would add emphasis as a second variable. Q1 (the exclusion test), Q2
(two heads one body), Q4 (glosses), Q5 (every body name has a source) are all excluded:
Q1 in particular is the instruction `decompose_arm/RESULT.md` §4 identifies as the cause
of the floor collapse, and an arm carrying it could not answer this arm's second question.
**Nothing about bodies, `ontology`, `inputs`, polarity or closure appears in the added
text.**

## 3. BASELINES, computed from disk before any call (`measure.py`, `measure.json`)

One code path — `arms_review/floor.py` + `arms_review/measures.py`, imported not
reimplemented — over every arm, on the review's own denominator (`selfcited` /
`requires_names`).

| arm | n | floor_clean | selfcited/requires | rate | errors | asserts | bodiless |
|---|--:|--:|--:|--:|--:|--:|--:|
| armA_turn1 (unaided) | 17 | 10 | 25/26 | **96.2%** | 18 | 34 | 0 |
| arm_aprime (NULL replicate) | 17 | 11 | 24/29 | **82.8%** | 17 | 34 | 0 |
| list_in_prompt_insample | 17 | 11 | 24/24 | 100% | 19 | 34 | 0 |
| retrieval_arm | 17 | 9 | 24/24 | 100% | 18 | 29 | 0 |
| forced_verdict_arm | 17 | 12 | 24/24 | 100% | 10 | 32 | 0 |
| selfreview_arm | 9 | 7 | 14/14 | 100% | 7 | 15 | 0 |
| **examples_arm** | 17 | 13 | **3/24** | **12.5%** | 10 | 33 | 0 |
| **decompose_arm** | 13 | 3 | **3/21** | **14.3%** | 21 | 31 | **13** |

⚠️ decompose_arm reads 3/21 here, not the 1/18 it published: `layers.py` scored NEEDS
names, `measures.selfcited` scores `requires` names against `concepts`. **This arm is
scored on the second, like every row above it**, because the brief requires the review's
denominator. The published 1/18 is not contradicted; it is a different denominator.

### The noise floor, from the complete null replicate (this is the band to clear)

| metric | armA vs arm_aprime |
|---|---|
| **target class, per clause** | differs at **1 of 17** (`l3239_3382_n002`, 3→2); totals 25/26 vs 24/29 |
| **floor_clean, per clause** | differs at **3 of 17** (both directions) |
| **error count, per clause** | differs at **7 of 17** (0↔6 swings) |

⭐ **The two measures have very different noise.** The target class is near-deterministic
draw to draw; the mechanical floor is not. A pre-registered consequence: **a large target-
class move is interpretable at n=17; a floor move of 1–3 clauses is not.** The brief's
reported "6 of 17" for the null was taken from the null while it was still partial; on the
now-complete 17 the figure is 3 of 17 on `floor_clean` and 7 of 17 on the error count.
Both are reported.

## 4. ⭐ PRE-REGISTERED DECISION RULE — the three outcomes

Primary endpoint: **self-cited borrowed glosses / `requires` names**, this arm's own 17,
`measures.selfcited`, unmodified.

| result | reading |
|---|---|
| **rate ≤ 25%** (≈ ≤ 7 of ~28) | ⭐ **THE EFFECT IS THE ASKING.** The class is reachable by one sentence in one call. Demonstration and decomposition are sufficient but not necessary, and both movers were confounded by the cheaper thing they contained. |
| **rate ≥ 65%** (≈ ≥ 18 of ~28) | **THE EFFECT IS THE DEMONSTRATION OR THE DECOMPOSITION.** Asking, alone, drowns in 39 KB. The two movers share a mechanism neither isolated and the class is reachable only by the heavier interventions. This is the null, and it is a valuable result. |
| **26–64%** | **PARTIAL.** Asking carries some of the effect and the heavier machinery carries the rest. Reported as partial, not rounded to either side. |

The bands are set from the measured distribution, not chosen after: every non-mover sits
at 82.8–100%, both movers at 12.5–14.3%. The gap between 25% and 65% is empty on every arm
measured to date, and a landing inside it is a genuinely new fact.

## 5. ⭐ SECOND ENDPOINT — is the floor cost separable from the gain?

The decomposition arm bought the target class at the price of the floor: **10 of 13
invalid vs 5 of 13 unaided, because 13 of 31 assertions came back with NO BODY.** Whether
the licence question *alone* carries that cost may matter more than the first question.

| result | reading |
|---|---|
| **bodiless asserts ≤ 1 AND floor_clean ≥ 9 of 17** | ⭐ **THE COST IS SEPARABLE.** The floor collapse belongs to decomposition (specifically to stage 3's exclusion test), not to asking about licences. |
| **bodiless asserts ≥ 4 OR floor_clean ≤ 7 of 17** | ⛔ **THE COST IS CARRIED BY THE QUESTION ITSELF.** A gain in the target class is not bankable without it. |
| in between | inconclusive on this endpoint, reported as such |

Thresholds: `floor_clean` 9 is one below the *lower* of armA (10) and the null (11), i.e.
outside the measured 3-of-17 noise band in the harmful direction. `bodiless` 4 of ~34
assertions (12%) is well under decompose's 13 of 31 (42%) and well over the 0 of 34 that
every single-call arm has recorded — **no arm other than decompose_arm has ever produced a
single bodiless assert.**

## 6. HARMS PREDICTED, so they are scored rather than discovered

* **H-1.** The question mentions `concepts` and NEEDS names and nothing else, so the
  likeliest side effect is *over-correction*: names the module genuinely coined getting
  pushed off `textual` too. Detector: `concepts` entries with `licence: assumed`/`world`
  whose names are NOT NEEDS names, compared against armA and the null.
* **H-2.** A `requires` list that shrinks — the model dropping NEEDS names entirely rather
  than re-licensing them, which would deflate the primary endpoint's denominator without
  fixing anything. Detector: `requires_names` total vs armA's 26 / null's 29. **If
  `requires_names` falls below 20, the primary endpoint is reported as CONFOUNDED by
  denominator collapse and the numerator is reported per clause instead.**
* **H-3.** The added ~470 chars land after the span and before "Write the module", i.e. at
  the recency position; a general degradation of the module (fewer `asserts`, fewer
  `ontology`) is possible. Detector: the asserts/ontology/inputs columns.

## 7. SPEND

* Ceiling for this arm: **`CAP_USD = 0.06`**, the brief's hard cap, gated in
  `run_licence.py` on the worst case of the exact set about to be sent.
* MEASURED comparable: arm A' billed **$0.021107 for 12 calls** on the same block and
  model = **$0.00176/call**; arm A's 17 turn-1 calls are measured at **$0.02971**.
  Expected here: **~$0.030**, plus ~120 prompt tokens/call for the added question
  (~$0.0003 total). **Estimate: $0.030. Worst case gated: ~$0.045.**
* ⚠️ `translate.Client._log_usage` runs BEFORE `_check_envelope`: a truncated or empty
  completion **is billed, is logged to `usage.jsonl`, and writes no arm record** (36% of
  one arm's spend went this way). Not patched — arm A and arm A' both ran with it and a
  control that patches it is not running the same harness. `reconcile.py` closes it
  against `usage.jsonl`, and **the ledger figure, never `out/`, is the spend of record.**
* ⚠️ `_debug_gen11/arm_aprime/` may re-run concurrently on the same provider and model,
  and its prompt sizes overlap this arm's, so attribution by prompt size is not available.
  **Attribution is by exact match on the usage dicts this arm records**, over a ledger
  window opened immediately before the send; the residue is reported as UNATTRIBUTED and
  counted against this arm as the conservative bound.

## 8. STOP RULES

* Gate 1 fails (system block ≠ `3a66c5f5…4c34c` / 39,959 c) → **nothing is sent.**
* Gate 2 fails (any user block differs from arm A's by anything other than the single
  added paragraph) → **nothing is sent.**
* Gate 3 fails (worst case + on-disk ledger > $0.06) → **nothing is sent.**
* One send of 17. **No second draw.** A re-send of a clause is permitted only for a call
  that RAISED (and is therefore missing from `out/` while possibly billed), via `--only`,
  and every such retry is named in RESULT.md.
