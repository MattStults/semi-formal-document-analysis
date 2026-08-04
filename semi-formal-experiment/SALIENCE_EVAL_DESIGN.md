# SALIENCE_EVAL_DESIGN — rank-position evaluation against the expert anchors (2026-08-04)

The first and only human-expert relevance signal in this project is
`expert_salience.json`: four anchors from a domain expert reviewing the
published coverage product. The expert's diagnosis is SALIENCE FLATTENING —
the panel over-flags, treating many related passages as equally relevant and
failing to distinguish THE core passage. This document specifies the one
instrument those anchors legitimately support: a rank-position check on the
tool's ranked output. It is deliberately small, because the anchors are
n≈4 and irreplaceable.

## What this is NOT

- Not a benchmark. No MCC, no CI, no headline. Four anecdotes from one
  expert cannot carry a quantitative claim and will not be asked to.
- Not a tuning target. `expert_salience.json` usage_rules are binding:
  nothing may be fitted to these anchors — no threshold, weight, prompt,
  operator, or presentation choice may be selected by reading results
  against them. They are the only human-expert gold the project has;
  burning them as tuning targets destroys the one instrument class the
  project lacks. This is invariant 9 applied to a 4-row gold.
- Not a relevance eval. The panel measures relevant/not; this measures
  whether the RANKING puts the core passage above its related neighbours —
  the axis the panel (a binary instrument) cannot see and the expert says
  is the failure mode.

## The metric

For each anchor with a pinned core passage:

1. **Join** the expert passage to a clause mechanically: normalized
   quote-containment of `expert_core_passage_starts` (plus
   `expert_core_passage_contains` where present) against clause quotes,
   using the `inventory.match_passage` normalization. The join is
   pre-registered per anchor BEFORE any ranked output is consulted. A
   failed join is reported as `unjoined` — never silently dropped, never
   hand-patched after seeing ranks.
2. **Rank** = position of that clause in the shipped ranking surface for
   the anchor's behaviour on the anchor's spec, restricted to that
   behaviour's predicted (hit) set. **RULING [amended per PORTFOLIO_REVIEW
   addendum ruling 2]: THE shipped ranking surface is `relevance.rank` —
   the PatientIndex-lineage normalized ranking the snapshots record.**
   section.py's ELECTION_SCORE is panel-fitted (declared bias 0.039);
   consulting it at generalization would thread a fitted constant through
   the frozen-label-free claim — **section.py stays diagnostic**, never the
   quoted surface. The surface designation is FROZEN in the G1 freeze
   artifact BEFORE any consultation; the result artifact still names the
   surface it consulted, and it must match the frozen designation.
3. **Report** per anchor: raw rank, hit-set size, top-1 indicator, top-5
   indicator. Aggregate: top-1 rate and top-5 rate over the joined,
   pinned anchors (n ≤ 3). Raw ranks are the primary readout; the rates
   are a summary, not a statistic.

Anchor 2 (how-to-approach-tradeoffs) has `expert_core_passage_starts:
null` — the expert's claim is ordinal ("the initial strongest expression
should outrank the others") with no pinned target. It enters no rate. It
is evaluated qualitatively: print the behaviour's top-5 with locators and
record whether the document-order-first strong expression leads. That
verdict is prose, labelled as prose.

## When each anchor can run — prerequisites, verified per anchor

| # | behaviour / spec | prerequisites | earliest legal consultation |
|---|---|---|---|
| 1 | proportionate-risk-mitigation / anthropic | constitution clause annotations (do not exist — HANDOFF "blocked on spend"); PRM query atoms; constitution is sealed TEST | **final pre-registered battery only** |
| 2 | how-to-approach-tradeoffs / anthropic | same constitution artifacts; no pinned passage → qualitative only | **final battery only** |
| 3 | avoiding-over-and-under-caution / anthropic | behaviour atoms exist (DEV behaviour) but the anchor is constitution-side, and the constitution is sealed TEST | **final battery only** |
| 4 | proportionate-risk-mitigation / openai | model-spec annotations exist (`annotations_b8.json`); PRM behaviour atoms do NOT — they are produced label-free by the frozen-pipeline generalization phase (ITERATION_LOOP amendment 2026-08-04) | **generalization-phase evaluation, once** |

So the schedule is: anchor 4 at the declared generalization evaluation,
anchors 1–3 at the final battery, and NOTHING before either. There is no
"quick peek to sanity-check the metric" — a peek is a consultation.

## Protection rules (binding)

1. **Evaluation-only.** Per usage_rules. Any artifact (weights, thresholds,
   overlays, prompts, presentation logic) whose selection post-dates an
   anchor consultation must record that it could not have been influenced
   by it, or the consultation taints it.
2. **Consultation is logged like checkpoint census.** Each run appends
   `{date, anchors_consulted, ranking_surface, config shas, results}` to a
   consultation log; every later document quoting an anchor result names
   the consultation entry. `anchor_consulted: true` is the analog of
   `census_consulted: true` in CYCLE_DESIGN amendment 1.
3. **Pre-register before consulting.** The joined clause ids, the ranking
   surface, and the reporting bands (below) are frozen in writing before
   the ranked lists are generated.
4. **No iteration between consultations.** Two scheduled consultations
   exist (generalization phase: anchor 4; final battery: anchors 1–3).
   Adding a third requires a written justification logged in advance.

## Reading the result — honest bands, pre-registered

- Core in **top-1**: consistent with expert salience; the ranking layer
  does distinguish the core passage even though the binary layer flattens.
- Core in **top-5**: weakly consistent; the presentation layer could
  surface it with a short "core candidates" strip.
- Core **below rank 20** (or unjoined): salience flattening is confirmed
  at the ranking layer too; a core/related distinction cannot be built on
  the current score.
These are directional readings of ≤4 anecdotes. The result artifact must
carry the sentence: "n≈4 human anchors from one expert; directional
evidence only; no rate quoted here is a statistic."

## What it informs — the product surface

The endorsed use case (interest groups checking whether and how their
topics are covered) survives salience flattening; the expert's complaint
is presentation: many-related-few-core. This eval decides whether the tool
can honestly offer a **core-vs-related presentation** — a distinguished
top slot per behaviour — or whether the product must present an unranked
relevant set and say so. It is a product decision input, not a model
quality claim. Cross-reference: all four expert core passages are
weighting/deliberation prose, which is exactly the content the SELECT
stance gap (STANCE_GAP_DESIGN.md) says no atom expresses — so this eval is
also the cheapest evidence on whether stance-blindness costs salience.

## Open discrepancy — RESOLVED

[Amended per PORTFOLIO_REVIEW addendum ruling 1.] The review ruled "two"
was a miscount: `expert_salience.json` carries THREE anthropic-side anchors
(two pinned, one qualitative/unpinned), all sealed with the constitution,
plus one openai-side anchor consumed once at the generalization
evaluation. ITERATION_LOOP.md §5 has been amended accordingly; this
document's treatment (all three anthropic anchors sealed) stands.
