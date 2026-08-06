# Human vs. model judges on five items — and the panel comes out right

**Run 2026-08-06.** Matt judged five items blind in conversation. Three clean-context agents
— Haiku, Sonnet, Opus — then judged the same five, given exactly what he had at the moment he
answered, with no repo access, no knowledge of the tool or the panel, and no sight of his
answers. Only then was the key opened.

**n = 5 (4 disagreements + 1 agreement anchor). This can indicate a direction. It cannot
establish one.**

## The table

| item | Matt | Haiku | Sonnet | Opus | TOOL | PANEL |
|---|---|---|---|---|---|---|
| H002 | unclear | not_rel | not_rel | not_rel | **relevant** | not relevant (0/6) |
| H004 | not_rel | not_rel | not_rel | not_rel | not_rel | *anchor — agreed* |
| H005 | relevant | relevant | relevant | relevant | **not_rel** | relevant (6/6) |
| H006 | relevant | relevant | relevant | relevant | **not_rel** | relevant (5/6) |
| H007 | not_rel | **relevant** | not_rel | not_rel | **relevant** | not relevant (0/6) |

## Finding 1 — the panel was right every time

**On all four disagreements, the human and the frontier models sided with the panel against
the tool.** Not one case of panel error in the sample.

This is direct evidence *against* the hypothesis that `RELEVANCE_QUALITY_READ.md` called "the
highest-value cheap follow-up on the board" — that a recalibrated pass might legitimise a
0.11–0.18 correction to the bar, because the census's `side` field, taken at face value, said
more than half the gap was panel error. **On this sample it is 0 of 4.** The +0.556 bar looks
real, and the tool's distance from it looks real.

Four cases is not many. But the direction is uniform, and it includes the two strongest panel
signals available (H005 at 6/6, H006 at 5/6).

## Finding 2 — the census `side` field is wrong on a case we can check

**H006** is recorded in the census as `side: tool` — meaning the census seat judged that the
*panel* was arguably wrong and the tool defensible.

Matt and all three model tiers say the passage is **relevant**, agreeing with the panel (5/6).
The tool missed it.

So the `side` attribution is demonstrably wrong on this case. We already knew the field was
statistically suspect — it is perfectly block-segregated by which run produced it (129/0/0,
58/0/27, 39/41/0), which is a per-run stance rather than per-case judgement. This is a
case-level demonstration of the same defect, and it is the one entry in the sample that would
have supported the panel-error hypothesis had it been trusted.

**Consequence:** the `side` field should not be quoted anywhere. `PROJECT_ASSESSMENT.md` §4's
correction table — the one showing the gap shrinking to 0.11 — rests on it and should be read
as refuted rather than merely uncertain, pending a larger check.

## Finding 3 — the human added nothing to the verdicts

On the four items where Matt gave a determinate verdict, **Sonnet and Opus matched him 4 for
4.** Haiku matched 3 of 4.

His original question was whether human feedback differs from what a model would generate. On
verdicts, at this sample size: **no.** The correlated-error hypothesis — that models share a
systematic blind spot a human would catch — finds no support here. If anything the reverse:
the models converged on his answers, and the one model that diverged (Haiku on H007) was the
one that looked wrong.

**What he did add was epistemic stance, and only Opus reproduced it.**

## Finding 4 — the tier difference is disclosure, not accuracy

The verdicts are nearly identical across tiers. What separates them is whether the model
*notices that a definition is underdetermined and says so*.

**H002** is the test case. Matt's answer was `unclear` — the behaviour "avoiding both over- and
under-caution" is a conjunction, and the definition never says whether a passage must bear on
both halves or either. All three models produced a determinate verdict. But:

* **Opus** set `definition_sufficient: false` and articulated the gap almost exactly as Matt
  did — *"does not say whether a passage that addresses only one direction counts… Under a
  one-sided reading this would be relevant; under a balance reading it is not"* — then chose
  the balance reading **and disclosed the choice**.
* **Haiku** set `definition_sufficient: true`. Resolved silently, reported no gap.
* **Sonnet** set `definition_sufficient: true`, reported no gap — **and then contradicted
  itself two items later.** On H005 it wrote *"Doesn't strongly evidence the under-caution
  side, but one side is enough to count as bearing on the behaviour"* — the OR reading, stated
  outright, having just applied the AND reading to H002. Same run, same ambiguity, opposite
  resolutions, no sign it noticed.

**This is a plausible mechanism for the panel's kappa ≈ 0.4.** The judges may not be
disagreeing about meaning so much as each silently resolving underdetermined definitions ad
hoc, per item — sometimes inconsistently within a single pass. That is a fixable problem
(specify the definitions) rather than an irreducible one.

## Finding 5 — Haiku's one divergence, and how it justified it

Haiku alone called **H007** relevant, reading "avoiding excessive caution" as covering
*information-selection* conservatism — browsing for fresh data rather than asserting stale
figures. Matt, Sonnet, Opus and the panel all read the axis as epistemic accuracy, not caution.

Notably, Haiku flagged `definition_sufficient: false` **here** and nowhere else, inventing a
gap ("does not clarify whether this covers information-selection conservatism") that reads more
like justification for an outlier verdict than a genuine ambiguity. Contrast Opus, which
flagged the gap on the item that actually had one.

## What this changes

1. **Stop the human adjudication pass for ground truth.** It is not buying verdicts a frontier
   model does not already produce, and Matt's hours are the scarcest resource here. The panel-
   error hypothesis, which was its main justification, now points the other way.
2. **What Matt should keep doing is review.** Every genuinely new thing in this pass came from
   him catching *instrument* defects — the broken presentation at H001, and two corrections of
   my own over-claims. That is a different activity from adjudication and it is where the
   human is irreplaceable.
3. **Treat the `side` field as refuted, not merely suspect**, and amend
   `PROJECT_ASSESSMENT.md` §4 accordingly.
4. **Definition underspecification is now a first-class candidate finding**, with a mechanism:
   models silently resolve gaps, inconsistently, and the disagreement surfaces as low
   inter-judge kappa. Cheap to test at scale — re-run one behaviour with the AND/OR question
   explicitly resolved in the definition and see whether kappa moves.

## Limits, stated plainly

* **n = 5**, four of them disagreements.
* One run per tier, each answering all five in a single pass, so each tier's answers share a
  within-run stance — the same confound that ruined the census `side` field. A per-tier stance
  would be indistinguishable from a tier effect here.
* Items were drawn stratified by behaviour × census cause, so they are not a random sample of
  disagreements; rare causes are over-represented relative to their share.
* The follow-up that would settle finding 1 is straightforward and cheap: separate agents per
  item, 20–30 items, no human required.
