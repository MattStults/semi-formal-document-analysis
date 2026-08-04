# Join integrity — locator-restricted joining and degenerate-quote refusal (design, 2026-08-04)

Status: DESIGN — not implemented. Companion documents: SEGMENTATION_GAPS_DESIGN.md
(the join's zero-match side), TOOLING_BATCH_DESIGN.md (the batch this ships with).
Origin: DISAGREEMENT_REPORT_ext_v1.md case 2 and the census's two
`fp_join_artifact` verdicts. The component under change is the one whose own
banner says it GATES EVERY METRIC.

## 1. The defect, stated mechanically

`inventory.match_passage` (inventory.py, the quote-containment join) matches a
panel passage to every clause whose `quote`/`marked_span` contains, or is
contained by, the passage's normalized quote — in either direction, over the
whole clause corpus. It uses no locator information. Passage-level scoring then
takes the max tool score over all mapped clauses (`diagnose_disagreement.passage_map`,
and `benchmark.score_tool`'s any-clause-hit passage recall).

Measured consequence (2026-08-04, true 589-locator universe vs
`modelspec_clauses.json`): fan-out distribution is 1 clause for 579 locators,
2 for one, **6 for one** (`#definitions > ¶5`, a quote beginning
"`role`: specifies the source of each message…"), and **28 for one** —
`#ignore_untrusted_data > ¶2`, whose recorded quote is the 21-character string
`!!! meta "Commentary"`, which is a substring of every one of the 28 commentary
clauses in the document. That one passage inherited m0168's 1.907 score (an
intellectual-freedom commentary in a different section) while the commentary it
actually denotes scored 0.085; the panel scored it 0/0/0; the survey booked it
as a maximal false positive in two behaviours. The census attributed exactly
these two rows to `fp_join_artifact` (`audit_disagreements.FANOUT_DEGENERATE = 5`).

The tool never claimed the passage was relevant. The join manufactured the
disagreement. Any historical number that flowed through a fan-out passage is
polluted in the same way.

## 2. The fix — two independent guards

### 2a. Locator-restricted candidate set

Every panel passage carries a locator of the form
`model-spec@2025-12-18 > #<section_anchor> > ¶<n>`. Every clause row from
`modelspec_clauses.json` carries `section_id`, and the two vocabularies are the
same namespace: the clause rows under `#ignore_untrusted_data` all have
`section_id == "ignore_untrusted_data"` (78 distinct section ids; verified
against live data). `benchmark._clause_rows` already passes `section_id`
through untouched.

Contract: when the passage locator yields a section anchor AND the clause rows
carry `section_id`, the join restricts candidates to clauses of that section
BEFORE quote containment. When either side lacks the key (the focus-area rows
of `modelspec_focus_areas.json` carry `section_path` but no `section_id`; a
foreign clause file may carry neither), the join falls back to the full corpus
and the caller receives a per-passage `restricted: false` fact — the fallback
is disclosed, never silent. No fuzzy anchor matching: the anchor either equals
a `section_id` string or restriction does not apply.

Restriction is sufficient for the 6-fan-out case (all six candidates collapse
to the definitions section and containment then discriminates) and shrinks the
28-fan-out case to the two commentary clauses of `#ignore_untrusted_data`
(m0178, m0187) — still ambiguous, which is why guard 2b exists.

### 2b. Degenerate-quote refusal

A quote below a specificity floor must never fan out; it must be refused,
loudly. Contract:

* Floor: normalized quote (after `inventory._norm`) shorter than 25 characters,
  OR the post-restriction candidate set still exceeds 1 while the quote is a
  proper substring of every candidate (i.e., the quote cannot discriminate
  among them).
* On refusal the join returns no clauses and a machine-readable flag
  (`degenerate_quote_refused`) that `benchmark.map_reference` records as a NEW
  stratum alongside the existing four (`STRATA`), so the accounting identity
  "strata sum equals unmatched" is preserved and the refusal is visible in
  every downstream report. `score_tool` counts a refused reference passage as
  an unmatched false negative in `full` scoring — the honest cost — and the
  census books it under a signature analogous to the current
  `unexplained_escalate`-for-unmapped rule, never under a tool-vs-panel cause.
* Calibration fact: 71 of the 863 published passages have raw quotes under 40
  characters, but only the one header-only quote is under 25 normalized — the
  floor is set to catch the pathological class, not short-but-real sentences.
  If implementation finds a second sub-floor quote that IS discriminating, the
  floor moves down, not the refusal semantics.

Versioning: the join gains a recorded `join_version` (v1 = today's behavior,
v2 = restricted + refusal) surfaced in snapshot/census config identity, the
PRICING_VERSION pattern, so the old behavior stays reachable and CYCLE_DESIGN
amendment F9 (reconstruction compatibility) is satisfied.

## 3. Falsifiable predictions (pre-registered for the fix cycle, checkable with zero panel contact)

1. Under v2 on the true universe, exactly two locators change their mapped
   set: `#ignore_untrusted_data > ¶2` (28 → refused) and `#definitions > ¶5`
   (6 → 1). Every other locator's mapped clause set is byte-identical.
2. No reference-grade passage (panel score ≥ 5) changes its mapped set —
   restriction never removes a correct mapping, because 847 of 849 matched
   passages already map to exactly one clause and that clause is in-section.
3. Clause-level snapshots do not flip at all (the join is downstream of the
   scorer); only passage-level and census numbers move.

Any failure of 1–3 halts the cycle: it means restriction is removing real
matches, which is a different and worse defect than the one being fixed.

## 4. CRITICAL — the re-measurement protocol

This join gates every historical passage-level metric. The fix therefore
obliges re-measurement, and re-measurement obliges disclosure. Protocol:

1. **Scope of affected published numbers.** (a) The README results table —
   tool +0.309 (audited selection, dev), +0.28 (first shipped config), bag
   control +0.19 — all flow through `map_reference`/`score_tool`. The panel
   bar +0.555 is passage-set-only (`panel_agreement` never joins to clauses)
   and CANNOT change; if re-measurement moves it, the harness is broken. (b)
   The 294-case census: the two `fp_join_artifact` rows, and any dossier whose
   `max_clause` was inherited across a fan-out. (c) The survey counts in
   DISAGREEMENT_REPORT_ext_v1.md (279 disagreements; 452 under b8). (d) Golds
   derived from passage-clause pairs, which the report already notes were
   polluted mechanically.
2. **Configs re-scored.** Exactly two: **b8**
   (`annotations_b8.json` + `behavior_atoms_b8.json`) and **audit_v1**
   (`annotations_ext_v1_merged.json` + `behavior_atoms_audit_v1.json`,
   the census configuration, with the containment overlay and frozen
   thresholds it shipped with once the census tooling grows the `--overlay`
   flag — see TOOLING_BATCH_DESIGN.md item 1). Each is scored under join v1
   and join v2 in the same run, producing a per-number delta table
   (old → new, with the join_version of each column in the header). No other
   historical config is re-run; they are marked superseded-by-provenance.
3. **Disclosure.** README's results section gains one sentence per changed
   headline number stating the old value, the new value, and "join v2
   (locator-restricted; see JOIN_INTEGRITY_DESIGN.md)". HANDOFF.md gets a
   dated entry in its correction ledger — same register as the existing
   retraction entries. DISAGREEMENT_REPORT_ext_v1.md is NOT rewritten; it gets
   a dated addendum, because it is a historical record of what was observed
   under v1 and its case 2 is the justification for v2.
4. **Prediction discipline.** The expected direction (tool FP count drops by
   the two manufactured rows; dev MCC moves slightly toward the tool) is
   written down BEFORE the re-score, in the cycle's prediction artifact, and
   the observed deltas are published whether or not they flatter the tool.
   A delta larger than the fan-out passages can account for is a halt
   condition, not a bonus.

## 5. Label-hygiene position

The fix is document-side and mechanical. Its inputs are the passage's locator
(a citation of document structure), the clause's `section_id` (produced by
`segment_modelspec.py` from the document alone), and quote text. No panel
verdict, judge rating, or gold value participates in the join's decision.
The DISCOVERY route ran through panel-reading instruments
(DISAGREEMENT_REPORT_ext_v1, the census) — which is exactly what invariant 9
permits: labels direct attention; they do not supply parameters. Nothing in
this design tunes a weight, a threshold, a vocabulary, or a query.

Correspondingly: **re-measurement is measurement, not fitting.** Re-scored
numbers are published as corrected measurements with the disclosure above.
The keep/revert decision for the fix itself rides a standard cycle — shape
`code`, mechanism-level predictions from §3 checked at MEASURE with zero
panel contact, census deferred to checkpoint per amendment F1 — and the keep
justification cites §3's document-side predictions, never the direction the
re-measured MCC moved.
