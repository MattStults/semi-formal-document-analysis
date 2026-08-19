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
