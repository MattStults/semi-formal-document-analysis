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

## Metrics (all three reported; the equivalence claim is metric 1)

1. **Equivalence (primary):** seat-vs-truth agreement (Jaccard over
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

* Prediction: metric 1 holds on >= 2 of 3 behaviors. (Prior grounds: on the
  2026-08-16 partial corpus, the adjudicator sided with the seat on 15/20
  disputed engagements.)
* Falsifier: metric 1 fails on >= 2 of 3 behaviors, OR precision < 0.6 on
  any behavior — either result is reported as "not panel-equivalent" with
  no post-hoc rescue. The D5 matching fix is frozen BEFORE scoring; no
  matching parameter may be tuned against these numbers.
* The n=1-style caveat is standing: three behaviors is the panel's own
  limit, and the conclusion is scoped to them.

## What this deliberately does not measure

ASP fidelity (SEMANTIC_AUDIT.md owns that), contradiction detection (needs
the D4 concrete instances), and the panel's own correctness — the panel is
an instrument being compared, not a bar being assumed.
