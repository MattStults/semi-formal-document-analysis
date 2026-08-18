# PRE-REGISTRATION — "frontier-panel-equivalent" relevance quality

Drafted 2026-08-16 under Matt's D3 ruling ("draft and hash; scoring waits
for sign-off"). ⛔ **This measurement is scored ONCE, on the full translated
corpus, after the bulk run and the D5 matching fix land. Nothing here may be
scored, peeked at, or partially computed before Matt approves this document.
Editing this file after approval voids the registration.** The sha256 of
this file at registration is committed beside it; verify before scoring.

## The claim under test

The node-matching pipeline (embed-rank + blind small-model seat over
translated node prose) identifies spec material relevant to a behavior at a
quality equivalent to the frontier panel (`data/behaviours.json`, judges
sol / kimi / fable / opus / kimi-k2), as measured against a common truth
tier that is independent of both.

## Truth tier (per D2)

Blind Fable-tier adjudicators, one clean context per behavior, given ONLY
the behavior definition and each node's ESTABLISHES + SOURCE TEXT. Never
shown seat verdicts, panel citations, or queue membership (protocol as run
2026-08-16, `panel_run1/adjudication.json`). Matt spot-checks a sample
afterwards; his spot-check is diagnostic, not part of the score.

## Behaviors and universe

The frontier panel's three behaviors (helpfulness,
harm-avoidance-to-third-parties, avoiding-over-and-under-caution) over
every translated, non-abstained node in `node_corpus_all.json` at scoring
time. The adjudicated node set per behavior: the union of (a) every node
the seat engaged, (b) every panel-warm node (any_ge2), and (c) a random
sample of 15 nodes from neither set (drawn by fixed seed 20260816,
sorted-id order) so both instruments can also be scored on agreed-negative
ground. Every node in the adjudicated set receives a blind ruling.

## Metrics (all reported; the equivalence claim is metric 0)

0. **Defensibility (PRIMARY — Matt's ruling, 2026-08-18):** for every
   deviation the tool makes from the truth tier, is it an ERROR or a
   DEFENSIBLE INTERPRETATION? Two rates per behavior:
   * engagement defensibility = share of tool engagements the truth tier
     rules relevant (both where the panel agreed and where it did not);
   * decline defensibility = share of tool declines on panel-cited nodes the
     truth tier rules NOT relevant (i.e. the tool was right to decline).
   The comparison instrument is the PANEL under the SAME reader:
   panel-citation defensibility = share of the panel's consensus citations
   the truth tier rules relevant. **Equivalence = the tool's deviations are
   defensible at least as often as the panel's are, on the same behavior,
   under the same reader.** Symmetric by construction; no instrument is
   assumed correct.
   Validity control (REQUIRED before the claim is made): a second frontier
   model, blind, re-rules a stratified sample of the disagreement rows; the
   Fable defensibility calls must survive that reader at >= 80% agreement
   or the truth tier is reported as single-model and the claim downgraded.
   Matt's own stratified spot-check (a few clear-relevant, a few
   clear-irrelevant, a few borderline in each direction) is recorded
   alongside as the human calibration.

The following are reported beside metric 0, not as the claim:


1. **Consistency:** seat-vs-truth agreement (Jaccard over
   relevant sets) >= the frontier panel's own **median pairwise
   judge-vs-judge agreement** on the same behavior (benchmark.judge_set /
   jaccard at threshold 1, spec_key openai, computed over the panel's
   passage universe mapped through clause_joins to the same nodes). If the
   pipeline agrees with an independent reader at least as well as the
   panel's judges agree with each other, "panel-equivalent" is earned on
   that behavior.
2. **Recall against truth:** fraction of truth-relevant nodes the seat
   engaged. Reported with the structural coverage ceiling (truth-relevant
   clauses with no translated span) stated beside it.
3. **Precision against truth:** fraction of seat-engaged nodes ruled
   relevant.

## Pre-stated predictions and falsifiers

* Prediction: metric 0 holds on >= 2 of 3 behaviors; metric 1 reported. (Prior grounds: on the
  2026-08-16 partial corpus, the adjudicator sided with the seat on 15/20
  disputed engagements.)
* Falsifier: metric 0 fails on >= 2 of 3 behaviors, OR engagement
  defensibility < 0.6 on any behavior, OR the second-frontier control falls
  below 80% — either result is reported as "not panel-equivalent" with
  no post-hoc rescue. The FROZEN matching layer comprises the D5 fix
  (TOP_K 12, MAX_ATOMS 10) AND the frontier atom decomposition
  (`atoms_frontier_frozen.json`, produced BLIND to panel citations,
  adjudication outcomes, and prior match results — its provenance block
  states the inputs). Nothing in the matching layer may change after this
  registration is signed, and no matching parameter may be tuned against
  these numbers.
* **Q3 ruled (Matt, 2026-08-18): the cold-start matching layer is scored AS
  BLIND-DECOMPOSED.** The known precision and recall errors catalogued in
  `panel_run1/THREEWAY_REPORT.md` (27 scope/structural, 73 seat-miss) are
  counted against the cold-start number by design; the general fixes they
  license (party-scope checklist + seat-brief item, topic/agenda atom
  vocabulary, retrieval brief) are arm-2 material. Rejected by name:
  applying the party-scope fix to the base tool before signing — legitimate
  in principle, but it would make the cold-start number describe a tool
  improved after seeing where it failed.
* The n=1-style caveat is standing: three behaviors is the panel's own
  limit, and the conclusion is scoped to them.

## Second arm (Matt's ruling, 2026-08-17): the TUNED number

Behaviors are query-side artifacts built to be written and iterated freely
— that is the product feature (DESIGN.md stage 4: "feedback refines the
QUERY, never the corpus"). So the report carries TWO numbers per behavior,
answering two different questions:

* **Cold-start (arm 1, above):** what the system delivers on first contact
  — frozen blind atoms, one shot. Fair to compare against the panel, whose
  judges also got one pass.
* **Tuned (arm 2):** what a user reaches by iterating the behavior. The
  atoms/definition for each behavior may be revised freely for up to 3
  rounds. The tuning signal is FABLE ADJUDICATION, not the panel (Matt's
  amendment, 2026-08-17: tuning against panel citations would import the
  panel's measured defects — strict-tier under-citation, the truncated
  universe — into the behavior; the tuned arm must make sense on its own,
  and Fable judgment is the operative truth tier). Discipline: the
  behavior's adjudicated node set is split 50/50 by fixed seed (20260817,
  sorted-id order). The tuner sees verdicts-with-grounds on the TUNING half
  only. Scoring runs on the HELD-OUT half plus any new engagements the
  tuned matcher produces, judged by FRESH adjudicator instances shown
  neither the tuning history nor the tuning half's verdicts. Same
  instrument type, disjoint verdicts and instances — the tuned number
  measures reach, not memorization. The panel appears in arm 2 only as the
  comparison instrument inside metric 0, never as a signal.
* Reported side by side, always both, labeled: the cold-start number is
  the generalization claim, the tuned number is the expressiveness ceiling,
  and the GAP between them is the measured value of the iteration feature
  itself. Reporting the tuned number alone is forbidden by this
  registration.
* Arm-2 falsifier: if tuning cannot bring metric 0 to pass on a behavior
  in 3 rounds, that behavior is reported "not reachable by iteration at
  this corpus", with the round transcripts kept.

## What this deliberately does not measure

ASP fidelity (SEMANTIC_AUDIT.md owns that), contradiction detection (needs
the D4 concrete instances), and the panel's own correctness — the panel is
an instrument being compared, not a bar being assumed.
