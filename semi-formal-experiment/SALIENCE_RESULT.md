# NULL — speech-act salience does not move the ranking axis

> ⛔ **DO NOT QUOTE THIS RESULT — 2026-08-06, Matt.** This is a **NON-MEASUREMENT**, not a null.
> `benchmark.passage_scores` calls `dict(ranked)`, which discards order. R4's mechanism class is
> order-only. The instrument therefore cannot detect this lever **by construction, before any data
> is read** — the position lift used to produce a number was the measuring agent's own construction,
> not the frozen design's. The pre-registration's outcome table does NOT apply: "both null" presumes
> the metrics could have seen the effect, and they could not.
>
> The one durable finding here is the instrument defect itself, plus the fresh baseline reproducing
> the transcribed `0.7427` to four decimals. Everything else is pending a valid instrument.


**Pre-registered measurement of `PREREG_salience_ranking.md`, run 2026-08-06.** Generator:
`salience_result.py` (deterministic, seeded, `$0`, no provider calls — two consecutive runs are
byte-identical). Nothing below was chosen after seeing a number; the lever ran at its DEFAULT
config, once.

**Verdict: NULL.** AUC delta **−0.0004**, behaviour-clustered paired 95% CI **[−0.0016, +0.0008]**.
Top-k precision moves nothing at k=1 and k=3 and its k=5 CI touches zero. Both halves of the frozen
gate fail. Per the pre-registration's outcome table, this is the **"both null"** row: *two
independent levers now fail on ranking; R4's premise is bounded and should not be built on without
a new argument.*

---

## 1. The pre-registered numbers, first and verbatim

### Metric 1 — AUC, behaviour-clustered (the headline)

| arm | mean AUC over behaviours |
|---|---|
| baseline — `section.SectionQuotient.rank`, re-scored in this run | **0.7418** |
| lever — `salience.Index` at DEFAULT precedence / DEFAULT tier order | **0.7414** |
| **delta (lever − baseline)** | **−0.0004** |
| behaviour-clustered paired 95% CI (20,000 resamples, seed 20260806) | **[−0.0016, +0.0008]** |

**Gate arithmetic (both required; either alone is a NULL):**

- (a) `delta −0.0004 > 0.0228`? → **NO.** The delta is ~57× *under* the grid-inclusive operative bar
  and on the wrong side of zero.
- (b) paired CI excludes zero? → **NO.** [−0.0016, +0.0008] straddles zero.

⇒ **NULL.** Not "regresses": the negative delta is far inside the floor, not beyond it.

Per behaviour (baseline → lever, delta). 4 of 9 move up, 5 move down; the largest single move is
0.0030 — an eighth of the bar:

| behaviour | baseline | lever | delta |
|---|---|---|---|
| animal-welfare-impacts | 0.7181 | 0.7157 | −0.0024 |
| avoiding-over-and-under-caution | 0.7116 | 0.7119 | +0.0002 |
| harm-avoidance-to-third-parties | 0.7927 | 0.7910 | −0.0017 |
| harmlessness-to-the-user | 0.7374 | 0.7343 | −0.0030 |
| helpfulness | 0.7573 | 0.7592 | +0.0019 |
| how-to-approach-tradeoffs | 0.6207 | 0.6211 | +0.0005 |
| objectivity-on-contested-questions | 0.7990 | 0.8016 | +0.0026 |
| proportionate-risk-mitigation | 0.7905 | 0.7882 | −0.0023 |
| user-autonomy | 0.7489 | 0.7495 | +0.0006 |

### Metric 2 — top-k precision (the axis the endorsed use case cares about)

Reported **with** the AUC, per the pre-registration; either alone is a protocol violation.

| k | baseline | lever | delta | behaviour-clustered 95% CI | gate |
|---|---|---|---|---|---|
| 1 | 0.9333 | 0.9333 | +0.0000 | [+0.0000, +0.0000] | NULL |
| 3 | 0.8198 | 0.8198 | +0.0000 | [+0.0000, +0.0000] | NULL |
| 5 | 0.7926 | 0.8044 | **+0.0119** | [+0.0000, +0.0296] | NULL |

k=1 and k=3 are **exactly** unchanged — not "small", identical. k=5 is the only positive signal
anywhere in this run: +0.0119, half the operative bar, with a CI whose lower bound is 0.0000 and
therefore does **not** exclude zero. It fails both halves of the gate. ⛔ It is recorded because the
pre-registration requires the metric, **not** as a partial success. The pre-registration's "AUC
null, top-k moves" row is **not** reached.

### Sort order used (R4 guard 2 — a result whose order is not named is not reportable)

```
tier_order:      ['base', 'salience']
kind_precedence: ['conditional', 'definitional', 'holistic', 'example', 'meta']
tie_break:       document_order
baseline:        section.SectionQuotient.rank
```

These are `salience.DEFAULT_TIER_ORDER` and `salience.DEFAULT_KIND_PRECEDENCE` unmodified. **No
other configuration was run, at any point, on any metric.**

### ⭐ R4 guard 1 — the returned SET is identical (checked mechanically)

45 (behaviour × atom-draw) pairs checked; **0 violations**. On every pair the lever returned the
same clause ids *and* the same scores as the baseline, differing only in order. No blocking defect.

### The lever was not inert

A null against a lever that never moved would be a different claim, so movement was measured:
**78.6%** of clause positions and **77.1%** of passage ranks change between the two arms (mean over
behaviour × draw). The lever reorders most of the list and the metrics do not notice.

---

## 2. Run identity

- panel: `panel_v2.load_panel()`, spec `openai`, 9 behaviours — the same panel as
  `auc_noise_floor.py`.
- gold: pair-gold, both held-out judges at verdict ≥ 1 (`benchmark.pair_targets`), golds with an
  empty or full positive class dropped — **the same gold rule as `auc_noise_floor.py`**, so the
  floor is commensurable. No deviation was needed.
- clauses `modelspec_clauses.json` (593), annotations `annotations_b8.json` (587 for this spec).
- atom draws: the 5 `behavior_atoms_v2_draw{0..4}.json` (`benchmark.ATOM_DRAWS_V2`) — the draws that
  cover the 9-behaviour ranking panel, matching the "mean over 5 draws" the transcribed constant
  claims.
- aggregation: AUC per (behaviour, draw, held-out judge) cell → mean over that behaviour's cells →
  mean over behaviours. 135 cells.
- **resampling unit: the BEHAVIOUR**, never the passage (`HANDOFF.md:1128-1138`). Passages are never
  resampled; both arms always see the identical behaviour resample, so the interval is paired.

---

## 3. ⛔ The instrument problem, and the lift this measurement had to choose

This is the largest interpretive call in the run and it is not in the pre-registration, so it is
stated plainly.

`salience.Index.rank` is **order-only**: it returns the baseline's `(clause_id, score)` pairs
permuted, with no score touched (that is R4 guard 1, and it is verified above). The shipped AUC path
is `benchmark.passage_scores(dict(ranked), joins)` — it takes `dict(...)` of those pairs and
**discards the order**. So under the harness as shipped:

| arm | mean AUC via `benchmark.passage_scores` |
|---|---|
| baseline | 0.7427 |
| lever | 0.7427 |
| delta | **+0.000000** |

That zero is **arithmetic, not evidence**: it would hold for every panel, every gold and every
aggregation, before any data is read. Reporting it as the result would be reporting that
`dict()` loses order.

The pre-registered AUC above therefore uses a **position lift**: each arm's own returned order is
turned into a strict descending score (best-ranked clause highest), lifted to passages by the same
MAX rule `passage_scores` uses, with join-nothing passages at 0.0 and still in the denominator, then
scored by the same `benchmark.auc`. Both arms get identical treatment; the only difference between
them is the order their ranker returned. This is the only lift under which an order-only lever is
visible at all.

⚠️ **This choice is load-bearing and was made by the measurement, not by the frozen design.** A
reader who rejects it is left with the score-lift delta of exactly 0.0 — which is also a null, so
the verdict does not turn on it, but the *magnitude* −0.0004 does.

⛔ **A standing finding for the harness, independent of this result:** any future order-only ranking
lever is unmeasurable through `benchmark.py`'s AUC path as currently wired. That is a defect in the
instrument, and R4's whole mechanism class is order-only.

---

## 4. Fresh baseline vs the transcribed 0.7427 (pre-registration amendment)

The amendment forbids comparing against the transcribed constant and requires reporting how far the
fresh baseline lands from it.

| quantity | value | distance from 0.7427 |
|---|---|---|
| transcribed `combined.MEASURED["ranking"]["auc_mean"]["section"]` | 0.7427 | — |
| **fresh baseline, score lift (the shipped path)** | **0.7427** | **+0.0000** |
| fresh baseline, position lift (this run's arm) | 0.7418 | −0.0009 |

⭐ **The transcribed constant reproduces exactly to four decimals** under this panel, this gold rule
and this aggregation. The derived floor's distrust item 4 — "hand-transcribed with no generator, so
it cannot be confirmed it was produced by the gold rule this test uses" — is **discharged for
`section`**: it now has a generator (`salience_result.py`, section 3 of its report) and it agrees.
This does not retroactively validate `structural: 0.6475` or `combined: 0.7425`, which were not
recomputed here.

The gate was nonetheless computed against the **fresh** baseline, as the amendment requires.

---

## 5. SECONDARY — R4's own anchor falsification probe

⛔ **n=3 usable anchors spanning 2 behaviours, n=1 expert, relayed secondhand, no protocol. This is
a qualitative check and NEVER a decision rule.** No gate above reads it. In practice it came out
weaker than n=3:

| anchor | outcome |
|---|---|
| `proportionate-risk-mitigation` / **openai** | ran on a live ranker. Core passage rank among the behaviour's hits: **93, 51, 54, 30, 93** across the 5 draws — **identical under baseline and lever**. Not first, not moved. |
| `proportionate-risk-mitigation` / **anthropic** | ⛔ **DEGENERATE.** The constitution has 0 clause annotations, so the ranker fires on nothing and every clause carries one score (1 distinct score across 593). Its rank 319/374 is a tie-break artifact, not a measurement. |
| `avoiding-over-and-under-caution` / **anthropic** | ⛔ **UNMATCHED.** The relayed quote ("if Claude is being over cautious or over compliant") is not verbatim in the panel, which reads "whether Claude is being overcautious or overcompliant". Nearest candidates are printed by the generator; **the match was deliberately not guessed** — fuzzy-matching the only human-expert gold onto a passage would be a judgment this script has no protocol for. It is on the degenerate `anthropic` side regardless. |
| `how-to-approach-tradeoffs` / anthropic | UNUSABLE — `expert_core_passage_starts: null` (already recorded in the pre-registration's amended limits). |

⇒ **One** anchor is genuinely evaluable, and under the default order the lever does **not** put the
expert's named core passage first — it does not move it at all. R4's falsification test says *"if no
ordering puts it first, R4's premise is wrong and this should revisit."* ⚠️ At n=1 that sentence
cannot be honoured as written. This is a *consistent* signal with the null, not a second
independent one.

Note on the mechanism: the openai core passage joins exactly one clause, `m0139`, whose `kind` is
`conditional` — the **top** tier of the default precedence. The lever promotes it inside its section
and its passage rank still does not change, because its neighbours in that tie group are also
conditionals and the residual order is document order.

---

## 6. Every caveat that applies

1. **The lift is an interpretive call made at measurement time** (§3). The verdict is null under both
   lifts; the magnitude is not.
2. **`kind` accuracy is unmeasured.** It came from an earlier annotation pass. A null could be a
   `kind`-quality failure rather than a speech-act failure, and this test cannot separate those
   (pre-registered limit, restated).
3. **No `illustrates` edge exists (H-5).** This tests the free half of R4 only.
4. **The floor is unpaired and this delta is paired.** `HANDOFF.md:1175-1180`: an unpaired floor runs
   2.1–6.5× the paired SE. That matters for a *near-miss*; it does not rescue this one, whose paired
   CI half-width is 0.0012 and whose point estimate is negative.
5. **The floor carries no between-behaviour heterogeneity** (`auc_noise_floor.py` limitation 2), so
   it reads "below this is certainly noise", never "above this is certainly signal". Used only in
   the direction it supports.
6. **Top-k ties are broken by passage id ascending** — deterministic and identical in both arms, so
   no arm wins on tie-break luck. k=1/k=3 being *exactly* unchanged is a consequence of the top
   passages being separated by the baseline's own score, where an order-only tier applied *inside*
   the baseline's tiers (`tier_order = ("base","salience")`) has no room to act.
7. **9 behaviours is a small clustering unit.** A behaviour-clustered bootstrap on n=9 is coarse; it
   is the pre-registered unit and the alternative (passages) is explicitly forbidden.
8. **Single seed for the bootstrap** (20260806, 20,000 resamples). The interval is far from the
   decision boundary, so seed sensitivity was not explored — and exploring it after seeing a null
   would be a search.
9. **`anthropic` coverage is unavailable to this ranker at all** (0 clause annotations), which is
   why 2 of the 3 "usable" anchors are unevaluable. This is a known input gap
   (`benchmark.build_query_module`'s own warning), not a result.

---

## 7. What was NOT done

- ⛔ **No other `kind_precedence` and no other `tier_order` were run.** Not before the number, not
  after it. There is no sensitivity exploration in this file, because running one after a null and
  reporting the best of it is the exact failure the anti-fitting rule names.
- No labelled example entered either ranker; both arms are label-free and compliant.
- Nothing was fitted to `expert_salience.json`; it was read only for the rank-position check its own
  `usage_rules` licenses.
- No provider calls. `$0`.

---

## Appendix — verbatim generator output

```
============================================================================
PRE-REGISTERED MEASUREMENT — speech-act salience on the ranking axis
============================================================================

panel: panel_v2 / openai — 9 behaviours; clauses modelspec_clauses.json (593); annotations annotations_b8.json (587)
atom draws: ['behavior_atoms_v2_draw0.json', 'behavior_atoms_v2_draw1.json', 'behavior_atoms_v2_draw2.json', 'behavior_atoms_v2_draw3.json', 'behavior_atoms_v2_draw4.json']
gold: pair-gold (both held-out judges at >= 1), per benchmark.pair_targets — the SAME rule as auc_noise_floor.py
cells: AUC per (behaviour, draw, held-out judge); 135 cells total
resampling unit: the BEHAVIOUR (HANDOFF.md:1128-1138)

SORT ORDER (R4 guard 2 — a result whose order is not named is not reportable):
    baseline: section.SectionQuotient.rank
    kind_precedence: ['conditional', 'definitional', 'holistic', 'example', 'meta']
    tie_break: document_order
    tier_order: ['base', 'salience']

----------------------------------------------------------------------------
R4 GUARD 1 — the lever's returned SET vs the baseline's
----------------------------------------------------------------------------
  (behaviour x draw) pairs checked: 45
  set/score violations: 0
  ✅ identical set and identical scores on every behaviour x draw — ordering only.

  DID THE LEVER MOVE ANYTHING? (a null against an inert lever would be a different claim)
    clauses whose position changed:  78.6% (mean over behaviour x draw)
    passages whose rank changed:     77.1%

============================================================================
1. AUC, behaviour-clustered — THE PRE-REGISTERED HEADLINE
============================================================================
  baseline (section.SectionQuotient.rank)  mean AUC = 0.7418
  lever    (salience.Index @ DEFAULT)      mean AUC = 0.7414
  delta (lever - baseline)                 = -0.0004
  behaviour-clustered paired 95% CI        = [-0.0016, +0.0008]  (20000 resamples, seed 20260806)

  GATE ARITHMETIC (both required, either alone is a NULL):
    (a) delta -0.0004 > 0.0228 ?  NO
    (b) paired CI excludes zero ?           NO
  ==> VERDICT: NULL

  per behaviour (baseline -> lever, delta):
    animal-welfare-impacts                0.7181 -> 0.7157  -0.0024
    avoiding-over-and-under-caution       0.7116 -> 0.7119  +0.0002
    harm-avoidance-to-third-parties       0.7927 -> 0.7910  -0.0017
    harmlessness-to-the-user              0.7374 -> 0.7343  -0.0030
    helpfulness                           0.7573 -> 0.7592  +0.0019
    how-to-approach-tradeoffs             0.6207 -> 0.6211  +0.0005
    objectivity-on-contested-questions    0.7990 -> 0.8016  +0.0026
    proportionate-risk-mitigation         0.7905 -> 0.7882  -0.0023
    user-autonomy                         0.7489 -> 0.7495  +0.0006

============================================================================
2. TOP-K PRECISION — the axis the endorsed use case cares about
============================================================================
  (reported WITH the AUC above; either alone is a protocol violation)

     k   baseline    lever      delta      95% CI (behaviour-clustered)   gate
     1   0.9333     0.9333   +0.0000   [+0.0000, +0.0000]              NULL
     3   0.8198     0.8198   +0.0000   [+0.0000, +0.0000]              NULL
     5   0.7926     0.8044   +0.0119   [+0.0000, +0.0296]              NULL

============================================================================
3. THE SHIPPED SCORE LIFT — an instrument fact, not a result
============================================================================
  baseline mean AUC (benchmark.passage_scores) = 0.7427
  lever    mean AUC (benchmark.passage_scores) = 0.7427
  delta = +0.000000
  The shipped path takes dict(ranked) and DISCARDS the order, so an order-only
  lever is invisible to it BY CONSTRUCTION — this 0 is arithmetic, not evidence.

============================================================================
4. FRESH BASELINE vs THE TRANSCRIBED 0.7427 (prereg amendment)
============================================================================
  transcribed `combined.MEASURED['ranking']['auc_mean']['section']` = 0.7427  (hand-transcribed, no generator)
  fresh baseline, score lift (the shipped path)   = 0.7427   (delta +0.0000)
  fresh baseline, position lift (this run's arm)  = 0.7418   (delta -0.0009)
  The comparator for the gate is the FRESH baseline above, never the transcribed
  constant (PREREG amendment 2026-08-06).

============================================================================
5. SECONDARY — R4's own anchor falsification probe
============================================================================
  ⛔ n=3 usable anchors spanning 2 behaviours, n=1 expert, secondhand, no protocol.
  QUALITATIVE ONLY. This is NOT a decision rule and no gate reads it.

  - proportionate-risk-mitigation / anthropic: run
      passage constitution@2026-01-20 > Being broadly ethical > Avoiding harm > The costs and benefits of actions > ¶6
      matched by: exact prefix; hits per draw [374, 374, 374, 374, 374]; clause annotations for this spec: 0; distinct baseline scores: 1
      ⛔ DEGENERATE — the ranker has no annotations for this spec; its order is a tie-break artifact.
      rank of the expert core passage — baseline [319, 319, 319, 319, 319], lever [319, 319, 319, 319, 319]
      lever puts it FIRST in every draw: False
  - how-to-approach-tradeoffs / anthropic: UNUSABLE — expert_core_passage_starts is null
  - avoiding-over-and-under-caution / anthropic: UNMATCHED — the relayed quote is not verbatim in the panel; not resolved here (see _near_misses)
      near miss (23 normalised chars): constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶1
      near miss (21 normalised chars): constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶23
  - proportionate-risk-mitigation / openai: run
      passage model-spec@2025-12-18 > #control_side_effects > ¶1
      matched by: exact prefix; hits per draw [144, 125, 139, 115, 121]; clause annotations for this spec: 587; distinct baseline scores: 51
      rank of the expert core passage — baseline [93, 51, 54, 30, 93], lever [93, 51, 54, 30, 93]
      lever puts it FIRST in every draw: False

============================================================================
HEADLINE: NULL
============================================================================
```
