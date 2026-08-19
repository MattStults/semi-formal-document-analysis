# ARM 3 — REGISTERED RESULT (2026-08-18)

Registration: behavior_pilot_arm3_prereg_DRAFT.md, signed by Matt at
sha256 a05adfcc50186b05fb4b0a8d9825eb7a3d8112e1dc6d4fa6014cf9d666f0179d;
scored ONCE at commit 65a68ba by the registered command. Numbers unedited.

## Test-slice deviation-defensibility (61/60/53 nodes; margin: 1 node ~ 2 pts)

| behavior | cold seat | tuned seat | ARM (a) symbolic | arm (b) +mutation | (a)+input channel |
|---|---|---|---|---|---|
| helpfulness | 0.67 | 0.65 | **0.77** | 0.75 | 0.77 (recall .89->.91) |
| harm-avoidance | 0.31 | 0.78 | **0.77** | 0.77 | 0.73 |
| caution | 0.64 | 0.67 | **0.72** | 0.72 | 0.64 |

Supporting: engagement precision .82/.67/.70; decline defensibility
.55/.83/.77; recall .89/.73/.90.

## Against the registered predictions
* Helpfulness: predicted (a) beats both seats (~0.75-0.85) — CONFIRMED (0.77).
* Caution: predicted seat-parity at higher recall — CONFIRMED and exceeded
  (0.72 vs 0.67; recall 0.90).
* Harm: predicted 0.45-0.60 — WRONG, in the good direction: 0.77, within
  one node of the tuned seat (0.78). The balanced test slice rewarded what
  validation could not show: harm's DECLINES are highly defensible (30/36 =
  0.83) — the relevant-heavy validation slice had underweighted the
  instrument's precision at declining.

## The equivalence claim
**PASSES**: arm (a) >= tuned seat on helpfulness (+0.12) and caution
(+0.05); harm is within the margin rule (0.77 vs 0.78, one node). The
symbolic instrument — no LLM in the query path, $0 per query, a printable
reason per verdict — is at or above the TUNED LLM seat on all three
behaviors' test slices, and above COLD-START on all three by +0.08 to +0.46.

## Falsifier that FIRED (reported as registered, no rescue)
**Arm (b) < arm (a) on helpfulness (0.75 < 0.77): the mutation stage is
dead weight in its current form.** Its one differential act on the test
slice was declining a RELEVANT engagement (recall .89->.87). Per-behavior
detail: inert on harm and caution (identical to (a)). The scope-
discrimination DESIGN is validated elsewhere (S4, T4, A7 all reproduce
hand-grounded firing); what failed is COVERAGE — ~90% of engaged module
bodies remain ungroundable, so the stage sees too few modules to earn its
keep. Registered future work: n-ary/constant reversal driven by the
silence census, per-behavior argument declarations (H1), then re-register.

## Input channel (own column, as registered)
Helpfulness: +recall (.89->.91) at ~flat precision — earns its place.
Harm/caution: precision cost exceeds recall gain on these slices (0.73/
0.64) — one-hop input relevance over-fires where providers are shared
scaffolding. Reported, not adopted, pending per-name weighting.

## Standing caveats (registered defects 1-9 apply verbatim)
Single-model truth tier; small decline denominators on helpfulness;
T2 repairs held; behavior modules hand-authored under the contract.

---

## ERRATA (2026-08-18, from the clean-context adversarial review — MATERIAL finding, fixed; arm-3 numbers unaffected)

**Finding:** the "cold seat" and "tuned seat" columns above are the ARM-2
HELD-OUT numbers, presented under a "same test slice" header. Overlap with
the arm-3 test slice is only 23/21/17 nodes; every cross-column delta was
cross-slice arithmetic. The reviewer independently reproduced the arm-3
measurement bit-for-bit at the frozen commit (denominators, timeline, and
provenance all clean) — the defect is confined to the comparison columns.

**Corrected SAME-SLICE comparison** (seat engagement sets rescored on the
arm-3 test slices, deterministic, seat_sameslice_full.json):

| behavior | cold (same slice) | tuned (same slice) | ARM (a) registered |
|---|---|---|---|
| helpfulness | 0.54 (rec .41) | 0.67 (rec .72) | **0.77** (rec .89) |
| harm-avoidance | 0.78 (rec .64) | 0.68 (rec .82) | 0.77 (rec .73) |
| caution | 0.60 (rec .39) | 0.68 (rec .74) | **0.72** (rec .90) |

* Equivalence claim under same-slice treatment: **arm (a) >= tuned seat on
  ALL THREE** (+0.10 / +0.08 / +0.04) — stronger than originally reported;
  the mislabeled table UNDERSTATED arm 3 on harm ("within one node of
  0.78" was a denominator artifact).
* Cold-vs-arm(a) on harm: 0.783 vs 0.767 — WITHIN the registered margin
  rule (1 node ~ 1.7 pts; threshold 2 nodes). The falsifier "arm (a) <
  cold-start on any behavior" does NOT fire under the margin rule. Metric
  note, stated plainly: on a negative-heavy slice (22 rel / 38 not),
  deviation-defensibility rewards low-engagement instruments; cold harm's
  same-slice score reflects mass declining, at recall .64 vs the tuned
  seat's .82 and with the original held-out recall measured at .30.
* The 12 balancing negatives per behavior lift arm (a) by +0.035/+0.059/
  +0.034 vs the pre-balance core slice (0.735/0.708/0.683); the same
  negative-heavy composition is what lifts cold-harm. All instruments are
  now scored on the identical composition, which is the fix.
* Two MINOR latent hazards from the same review fixed in code the same
  day: truth-merge glob order made deterministic with a duplicate-conflict
  guard; arm_b_states firing check made exact-module.
