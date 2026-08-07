# Pre-registration — does speech-act salience move the ranking axis?

**Frozen 2026-08-06, before any result exists.** Written while the noise floor and the ranker are
being built by separate agents, each explicitly forbidden from computing the outcome. Neither the
threshold nor the direction below was chosen with knowledge of a result.

## The claim under test

R4 (`HARNESS_REDESIGN.md` §0.0a) rules that a clause's **speech act** — rule-stating vs
illustrating vs commentary — can order the core passage above equally-licensed peers. The data
already exists: `kind` on all 593 clauses (conditional 188, example 183, definitional 84, meta 72,
holistic 66). Nothing currently consumes it for per-clause salience.

## Baselines, already recorded — not re-derived for this test

| ranker | AUC | source |
|---|---|---|
| `section.rank` — best single compliant ranker | 0.7427 | `combined.py` MEASURED `auc_mean` |
| `structural` alone | 0.6475 | same |
| combined, typed within-section tiebreak | 0.7425 | `HANDOFF.md:1050` — **a flat null** |

⭐ That last row is why this test is fair rather than fishing: **a ranking lever has already been
tried and returned nothing.** Speech act is a different signal on the same axis. Either outcome is
informative, which is the point of registering before looking.

## ⛔ The measurement problem this pre-registration exists to prevent

**AUC is a whole-curve measure. The expert's complaint is about the top of the list.**

`expert_salience.json` records the failure as *"SALIENCE FLATTENING: it over-flags, treating many
related passages as equally relevant, and fails to distinguish THE core passage"*, with the anchor
*"should be many related + ~one core"*. A change that correctly promotes one clause into the top
few can leave AUC — which integrates over every threshold — essentially unmoved.

So a null on AUC alone would be **uninterpretable**: it cannot distinguish "the lever does nothing"
from "the metric cannot see what the lever does." Registering only AUC would have set up a
measurement that reports failure regardless.

⇒ **Two metrics, both frozen here, with different jobs:**

| metric | job | comparable to a recorded baseline? |
|---|---|---|
| **AUC**, behaviour-clustered | comparability with 0.7427 / 0.7425 | yes — this is the reportable number |
| **top-k precision** (k = 1, 3, 5) | the axis the endorsed use case actually cares about | no recorded baseline; must be computed for the baseline ranker in the same run |

Reporting AUC without top-k, or top-k without AUC, is a protocol violation.

## ⛔ AMENDMENT 2026-08-06 — the comparator changes, before any result exists

The derived floor's own distrust item 4: `combined.MEASURED` is **hand-transcribed with no
generator**, so it cannot be confirmed that 0.7427 was produced by the gold rule and aggregation
this test would use. Comparing a freshly-computed AUC against a transcribed constant of unverifiable
provenance is not a comparison.

⇒ **The comparator is the baseline ranker re-scored in the SAME run, same gold rule, same
aggregation.** The recorded 0.7427 / 0.7425 become a sanity reference — if the fresh baseline lands
far from 0.7427, that is itself a finding about the transcribed constants and must be reported.

⇒ **And clearing the floor is necessary, not sufficient.** Distrust item 2: the floor is *unpaired*,
which `HANDOFF.md:1175-1180` records as running 2.1–6.5× the paired SE. Distrust item 1: a
label-free null cannot manufacture between-behaviour heterogeneity, so the floor reads as *"below
this is certainly noise"*, never *"above this is certainly signal"*.

**The gate is therefore BOTH:** delta > 0.0228 (grid-inclusive operative bar) **AND** a
behaviour-clustered paired CI excluding zero. Either alone is a null.

## Decision rule — fixed before the floor is derived

The AUC noise floor is being derived independently and does not exist yet. The rule is therefore
stated as a function of it, so it cannot be chosen to fit:

- **Moves** — the AUC delta exceeds the **upper end** of the derived noise-floor range, behaviour-clustered.
- **Null** — the delta falls inside the range.
- **Regresses** — the delta is negative beyond the range.

⭐ The floor's **upper** end, not its lower. `REPO_TRAPS.md` #2 records the cost of the opposite
choice: quoting half a range let `+0.0317` be called "clears" when it straddles.

**Resampling unit: the BEHAVIOUR, not the passage** (`HANDOFF.md:1128-1138` — behaviour SD 0.0596 is
~12× draw SD 0.0172; passage-level CIs are far too tight and a prior finding was retracted over
exactly this). A result that is significant only under passage resampling is a null.

## What each outcome licenses

| outcome | what may be claimed |
|---|---|
| AUC moves | speech-act salience is the first lever to beat the ranking null. R4's mechanism is supported. |
| AUC null, top-k moves | the lever works on the axis the use case cares about and AUC cannot see it. R4 supported; **AUC is the wrong headline metric for this product** and should be replaced. |
| both null | two independent levers now fail on ranking. R4's premise is bounded; do not build on it without a new argument. |
| regresses | R4 is wrong as stated. Revisit §0.0's grade. |

## Constraints on the run

- **Label-free and compliant.** No labelled example enters the ranker; comparability with 0.7427
  requires it, and invariant 9's replacement (R5) licenses fitting only under capacity bounds that
  this test does not use.
- **Ordering only, never dropping.** R4 guard 1: the returned SET must be identical to the
  baseline's. Asserted mechanically in the ranker's own tests, and re-checked at measurement.
- **$0.** Deterministic re-analysis of data on disk. No provider calls.
- **The precedence order used must be recorded with the number** (R4 guard 2). A result whose sort
  order is not named is not reportable.

## Known limits, stated now rather than discovered later

- ⛔ **AMENDED 2026-08-06, before any result:** `expert_salience.json` has 4 anchors but only
  **3 usable** — `how-to-approach-tradeoffs` carries `expert_core_passage_starts: null` — and the
  3 span only **2 behaviours**. They are n=1 expert, secondhand, no protocol: a qualitative
  check, never the decision rule. Amended loudly rather than silently because this file is frozen.
- `kind` was assigned by an earlier annotation pass, not by this experiment; its own accuracy is
  unmeasured. A null could be a `kind`-quality failure rather than a speech-act failure, and this
  test cannot separate those.
- No `illustrates` edge exists (H-5). This tests the free half of R4 only.
