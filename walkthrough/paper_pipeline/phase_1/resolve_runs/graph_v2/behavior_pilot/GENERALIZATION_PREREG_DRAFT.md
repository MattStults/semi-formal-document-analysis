# GENERALIZATION PRE-REGISTRATION — zero-adaptation runs on six never-consulted behaviours (DRAFT, awaits Matt's signature)

Campaign: 10-hour push (HANDOFF_CURRENT.md campaign section, baseline commit
5cc21627, scope ruling same day: all six, 3+3 sequential, FATAL stop rule).
Status: DRAFT — not frozen until signed. Corrections append, never edit.

## What this measures
Whether a NEW behaviour costs a fixed procedure, not another campaign. The
instrument (modules_contract_v18 + lanes as frozen at run time) was built
around three dev behaviours. Six behaviours it has never seen — never
consulted in any design, tuning, or adjudication decision — are run through
the same procedure, once each, with no adaptation before scoring. The
PRIMARY result is the fix ledger: what repairs are needed AFTER scoring,
classified. The score is secondary.

## Subjects, order, document
Corpus: OpenAI Model Spec graph corpus (link_nodes.gather() at freeze time),
the same corpus as round-4. Behaviours, in fixed order:

Block 1 (probes): 1. harmlessness-to-the-user — adjacent family; the
protects wall must flip from third-parties to the user (the historic S3
failure mode). 2. objectivity-on-contested-questions — maximal-distance
shape; answer-quality class the old census said nothing touched.
3. how-to-approach-tradeoffs — procedural/meta; the behaviour IS the
document's own weighing method.
Block 2 (confirmation; runs ONLY if block 1 transfers cleanly): 4. user-
autonomy. 5. proportionate-risk-mitigation. 6. general-welfare — CAVEAT:
the collaborator's 10th index behaviour ("general welfare, strict reading")
is general-welfare verdicts restricted to what both specs share; on this
single-document corpus it is the plain general-welfare behaviour, and this
prereg records that the comparison-layer statistic for it is computed on the
unrestricted rows (data/panel-v5 has only the unrestricted rows anyway).

Rejected alternatives (by name): run only the two originally chosen
(loses breadth now that v5 panel truth-scarcity is resolved); run all six as
one block (loses the confirmation structure).

## Build phase (before any run)
For each behaviour, an a-priori module built per TRANSLATION_CONTRACT_V2
section 8: acts performed, walls derived from the behaviour definition ALONE,
purpose-channel decision, governs_conditional only via the 9b-declared
context atoms if the definition warrants. Inputs allowed: the behaviour's
definition text (engine/panel + v3w/v5 definitions where they exist), the
contract, the frozen act/context vocabulary. Inputs FORBIDDEN: instrument
outputs on this behaviour, any panel verdict, any truth. Execution tier:
written-spec execution (annotation-class seats); adversarial review per
module; Fable spot-audit queued post-reset (its absence at run time is
recorded, not hidden). Modules are frozen as built — no revision before
scoring.

## Run and truth protocol
- Instrument runs ONCE per behaviour on the frozen corpus. Zero adaptation:
  no wall tweaks, no vocabulary additions, no re-runs after looking.
- Truth: stratified fresh draw, n=40 per behaviour (20 engaged, 20
  not-engaged; if a side has fewer nodes, take the side whole and top up the
  other). Strata are informed by the v5 panel COMPARISON layer only, via two
  pre-declared strata: panel-agree (all three full seats on the same side of
  the >=2-relevant cut) and panel-split (anything else), drawn 50/50 where
  population allows. Determinism: seeded draw script, seed + input shas
  recorded; same seed -> byte-identical sample (tested before use).
- Rulings: blind Fable adjudication post-reset, single rulings + seeded 20%
  three-instance panels (per-ruling noise measurement, falsifier F5 in the
  round-4 lineage). Fable only; no substitution without a fresh parity
  validation, disclosed.

## Registered statistics (computed exactly as written, for each behaviour)
Truth-side: engagement precision = TP/(TP+FP); decline correctness =
TN/(TN+FN); both with the draw's confidence band; defensible-rescue rate
(the match-or-adjudicated-defensible criterion standing used for the dev
behaviours) reported alongside, same definition as round-4.
Comparison-side (v5 panel; COMPARISON ONLY, never truth): (a) instrument vs
panel-relevant (verdict >= 2) agreement on the full model-spec passage set;
(b) same with >= 1; (c) per-seat agreement; (d) instrument precision
decomposed on panel-agree vs panel-split strata. These four, nothing else;
any additional cut is post-hoc and labeled so.

## Success criterion and falsifiers (per behaviour)
- S1 TRANSFER: engagement precision >= 0.70 at the 40-node draw AND fix
  ledger contains no FATAL entry. Basis: below the dev trio's converged
  standing (0.94-0.96 in-sample after a full campaign — not expected cold),
  anchored on the round-2 prediction lineage (0.73-0.89). (A former anchor —
  "Matt's human-panelist baseline 71%" — is STRUCK 2026-08-21: no artifact
  establishes it and its presumed source does not recognize it; the floor
  stands on the prediction lineage alone.)
- F1 FATAL fix-ledger entry (a repair that requires a per-behaviour special
  case in the instrument rather than in the behaviour module) -> behaviour
  fails transfer; if in block 1, STOP RULE fires: blocks stop, results
  reported, no further draws or rulings.
- F2 engagement precision < 0.60 -> procedure-transfer failure for this
  behaviour; reported; block 1 occurrence also fires the stop rule.
- F3 seeded-panel disagreement rate > 20% of panelled rulings -> truth
  noise too high for the band; widen bands or redraw, disclosed, never
  silently.
- Fix-ledger classes: EXPECTED (module-local: a wall/act the definition
  implied but the first build missed), ALARMING (vocabulary gap: a
  distinction the instrument lacks that the definition implies), FATAL
  (per-behaviour special case). The ledger is the primary result; all
  entries land in the record with their class and the rejected quick-fix.

## Re-measurement protocol (attempts budget, added 2026-08-21 at Matt's ruling)
n=40 chosen over n=60 because the binding resource is ATTEMPTS, not band
width: block-1 behaviours may be measured several times as the fix ledger
drives repairs, and fatter draws buy fewer attempts.
- ATTEMPT 1 (zero adaptation) carries the TRANSFER verdict exclusively —
  the generalization claim. Nothing done later can change it.
- ATTEMPT 2+ exists for repairs: if the fix ledger holds EXPECTED entries,
  the repair is module-local; ALARMING entries get design-tier treatment;
  either way the behaviour is re-measured with a fresh seeded draw + fresh
  blind rulings, labeled attempt-N. Attempt-N verdicts measure THE REPAIR,
  never transfer; writeups keep the two claims separate.
- FATAL entries are never repaired in-campaign (the stop rule owns them).
- Budget: ~0.5-0.6M Fable covers the six first attempts; re-measurements
  (~0.1M each) exceeding the fresh bar queue to the following week's bar,
  disclosed.

## Confirmation-block rule
Block 2 runs only if every block-1 behaviour satisfies S1 and no F1/F2
fired. If block 2 shows materially worse transfer than block 1 (any
behaviour below 0.65 precision or any F1), the combined result is reported
as "transfers with degradation" and the blog claim is scoped to match.

## Integration slots (pre-declared, so nothing arrives as a surprise)
- v5 frontier panel (data/panel-v5/, PROVENANCE.md): comparison layer as
  above. Seat composition (sol/fable/deepseek + partials) differs from the
  v3w trio; writeups name the panel they cite.
- Any further frontier data (e.g. the Slack reader-test-coverage.json Matt
  holds, or new aci runs): enters ONLY under the same comparison rule, or
  not at all. Truth path is closed to it by this prereg.
- Round-4 results: independent; this prereg neither reads nor is read by the
  round-4 prereg. Both may be cited together afterward.

## Cost and timing
~0.5-0.6M Fable tokens across six 40-node draws + panels; all post-reset
(Sun 9pm PT Aug 23). Module builds, instrument runs, v5 comparison: Fable-
free and proceed before the reset. Draws are computed and sha-recorded
before any ruling exists.

## Signatures
Drafted by the campaign orchestration seat, 2026-08-21.
Matt: SIGNED 2026-08-21. Rulings incorporated at signature: n=40 on the
attempts-budget rationale (re-measurement protocol clause); the 71% anchor
STRUCK (no artifact establishes it; its presumed source did not recognize it
— Matt later suggested it may have been a manual test he personally ran; if
that artifact surfaces it is restored by appended erratum, not by memory);
third probe = how-to-approach-tradeoffs. FROZEN at this signature;
corrections append only.

## ADDENDUM (2026-08-22, post-signature clarification, append-only)
Stratum granularity operationalization: panel-agree/panel-split are computed
at ANCHOR granularity (the document's {#anchor} principle sections), not
paragraph granularity: node -> anchor by line containment (deterministic,
total coverage); seat verdict per anchor = max over its paragraphs; agree
iff all three full seats land on the same side of the >=2 cut on those
maxima. Reason: paragraph-level indexing validated at only 12/40 against the
independent clause corpus (generators disagree on paragraphization —
mis-stratification risk), while anchor attribution is exact. Strata inform
sampling only; truth is untouched. Implemented in draw_generalization.py
(determinism tested: same seed -> byte-identical artifact).
