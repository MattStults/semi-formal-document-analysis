# ARM A′ — the NULL-MANIPULATION REPLICATE

**Signed before any call was sent.** Nothing below was written or amended after
seeing a draft.

## What this arm is

A re-draw of the SAME 17 clauses under the **byte-identical arm A prompt**, same
config, same provider, same model, same temperature (0.2), turn 1 only, issued in
parallel. **The manipulation is the empty manipulation.** Every difference from
arm A is therefore draw-to-draw noise and nothing else.

## Why it exists

Eight arms in this series were each compared against **one** arm A draw. The
series has never had a noise floor. The adversarial review in
`../arms_review/` found that arm F (`forced_verdict_arm`), whose *drafting
prompt* is token-identical to arm A's — its extra schema rides in
`response_format` at zero prompt tokens — nevertheless differs from arm A on the
mechanical floor at **6 of 17 clauses**. Arm F is not a clean null (a
`json_schema` in `response_format` constrains decoding, so generation genuinely
differs), which is exactly why a clean null is needed.

If an unmanipulated re-draw moves a measure by as much as an arm did, that arm's
effect on that measure carries no information.

## Frozen baseline (arm A turn 1, from `../arms_review/measures.json`)

| measure | arm A turn 1 |
|---|---|
| floor-clean clauses | 10 / 17 |
| self-cited borrowed glosses | 25 / 26 `requires` names; 15 / 17 clauses |
| closure verdict mix | `cepa` 25, `cnpa` 4, **`unclear` 0** |

## PRE-REGISTERED PREDICTIONS — what would invalidate what

Let **F(m)** = the number of the 17 clauses on which arm A′ differs from arm A on
measure *m*. F(m) is the noise floor for *m*, from one replicate.

The two headline effects under test, and the exact condition that kills each:

1. **Arm C's borrowed-gloss collapse (25/26 → 3/24 glosses; 15 → 3 clauses).**
   * KILLED if arm A′'s clauses-with-self-cite falls to **≤ 6 / 17** (i.e. the
     null reproduces most of the drop on its own).
   * SERIOUSLY WEAKENED if arm A′ lands in **7–11 / 17** — the effect would then
     be a difference of degree inside a noisy measure, and the reported
     p ≈ 1e-6 (which assumed a fixed 24/24 comparator) would be void.
   * SURVIVES only if arm A′ stays at **≥ 12 / 17**.

2. **Arm B's closure shift (`unclear` 0 → 16).**
   * KILLED if arm A′ produces **≥ 8** `unclear` verdicts unprompted.
   * SERIOUSLY WEAKENED at **3–7**; the McNemar p = 0.031 would be void because
     its discordant-pair count was computed against a comparator assumed stable.
   * SURVIVES only at **≤ 2**.

3. **The floor comparisons in general** ("6 of 17 fixed", "9 of 17 reproduced
   their own frozen defect", "5 modules structurally identical to arm A").
   * If F(floor outcome + error-severity count) **≥ 6 / 17**, every one of these
     is at or below the noise floor and none of them is reportable.
   * If F ≥ 3, the "5 structurally identical" claim is uninterpretable, since
     structural identity is a stricter test than the floor and the null will
     already break it more often.

**A high floor is the informative outcome here.** It is what this arm exists to
detect and it will be reported unsoftened.

## PRE-REGISTERED DESIGN DECISIONS (taken before results)

* **ONE replicate, n = 17.** Arm A's turn-1 spend on exactly these 17 clauses is
  **MEASURED at $0.02971** (summed from the `turns[n==1].cost_usd` records in
  `../ds_opus_loop/out/*.transcript.json`). A second replicate would cost the
  same again, i.e. ~$0.059 total, which is **over the $0.05 hard cap**. So the
  second replicate is refused *now*, on arithmetic, not later on results.
  (The brief's ~$0.017 estimate is low; the measured arm A figure is authoritative.)
* **A single replicate bounds the floor LOOSELY and only from below in
  expectation.** F(m) from n=1 is one draw of a binomial-ish count with no
  variance estimate. Every F reported is a point estimate with a Wilson 95%
  interval attached, and no claim of the form "the floor is exactly k" will be made.
* **Retries.** `Client.complete_messages` does NOT route through `_retrying`, so
  `resample_truncation` does not apply (this is arm A's behaviour too, and it is
  preserved). At most **2** whole-clause re-sends are authorised, only for a
  clause whose call RAISED (truncation/transport), never for one whose draft
  merely displeases. Any re-send is disclosed in RESULT.md.
* **No adjudication.** Not one draft is read span-first. Every number comes from
  `../arms_review/floor.py` and `measures.py`, reused unmodified.
* **Structural identity to arm A** is defined mechanically, before results, as
  equality of `json.dumps(module, sort_keys=True)` after dropping nothing. A
  weaker "signature identity" (the sorted multiset of predicate `name/arity` in
  `concepts`, plus the sorted `requires` list, plus the closure verdict list) is
  reported alongside.

## GATES — the run refuses to send unless all hold

1. The four production prompt files assemble to arm A's system block,
   sha256 `3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c`,
   39,959 chars. **Refuse if it does not match.**
2. Every one of the 17 user blocks is **byte-identical** to the user block arm A
   built from its own config (`../../resolve_runs/graph_v2/config_corpus_all.json`),
   verified by rebuilding both and comparing.
3. Worst case of all 17 calls (full `max_tokens` output) plus the on-disk ledger
   must be ≤ **$0.05**. Priced before any send.

## Accounting

`translate.Client._log_usage` runs **before** `_check_envelope`, so a call that
truncates or comes back empty **is billed and logged to `usage.jsonl` but writes
no arm record**. (This hole cost arm D 36% of its recorded spend.) Spend is
therefore reconciled against `semi-formal-experiment/usage.jsonl`, not against
this arm's `out/` records. `../decompose_arm/` is running concurrently and its
rows will be interleaved in that ledger; reconciliation is by timestamp window
and by the arm's own recorded token counts.

---

## AMENDMENT 1 — 2026-08-17, after the first live send, before any measurement

**What happened.** Of the 17 parallel calls, **12 returned and 5 raised
`ProviderError: HTTP 503 Service unavailable`** (ids `owVmiMa-…`, `owVmioy-…`,
`owVmjMr-…`, `owVmkQL-…`, `owVmkuL-…`). Reconciliation against
`usage.jsonl` (lines 5048+) shows **12 billed rows totalling $0.021107, zero
unrecorded, zero truncated** — the 503s raised inside the `HTTPError` branch,
which sits *before* `_log_usage`, so they cost nothing and generated nothing.

**The conflict.** §PRE-REGISTERED DESIGN DECISIONS authorised **at most 2**
whole-clause re-sends. Five clauses need one. Honouring the letter would leave
n = 14 and silently drop 3 clauses from a 17-clause paired comparison.

**What I had seen at the moment of writing this amendment**, stated so the
amendment can be audited: the runner's per-clause floor lines for the 12
returned clauses (outcome / breach count / finding count) — nothing else. No
`measures.py` output, no self-cite counts, no closure verdicts, no draft text.
For the **5 clauses being re-sent I have seen nothing at all**, because nothing
was generated for them.

**Ruling: the 2-re-send limit is raised to 5, for these 5 clause ids only.**
Grounds:

* The limit existed to stop (a) budget overrun and (b) re-rolling a draft whose
  *content* I disliked. Neither is in play. A 503 is a pre-generation transport
  failure: there is no draft to dislike and no result to shop.
* The failure is **provably independent of draft content** — the provider never
  reached generation. Dropping these 5 would not be missing-at-random with
  respect to anything except provider load, but keeping them costs nothing in
  validity and restores the paired n = 17.
* Budget holds: $0.021107 recorded + worst case 5 × $0.00262 = **$0.0342**,
  under the $0.05 cap. The cap is not touched.

**Rejected by name:** *re-send only 2 and report n = 14.* Rejected because the
choice of which 2 would be mine to make after seeing the other 12's floor
outcomes, which is a worse discretion than the one the limit was written to
prevent. **Also rejected: re-send with a longer timeout, more workers, or any
other changed parameter** — the re-send is byte-identical to the original, or
it is not a null replicate.

**If any clause 503s again**, it is reported as missing and n is reduced; there
is no second amendment.

## AMENDMENT 2 — same moment: a cap-gate ordering defect, fixed

`run_aprime.py` priced the worst case of **all 17** clauses even when only a
subset would be sent, so the partial re-send would have been REFUSED at
$0.021107 + $0.0446 > $0.05 despite the true exposure being $0.0342. The gate
now prices **exactly the set it is about to send**, plus the on-disk ledger.
This is strictly *tighter* enforcement, never looser: the figure gated on is the
real worst case of the real send. The full-17 figure is still printed.
