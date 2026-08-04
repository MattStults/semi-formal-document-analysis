# Segmentation gaps — the unmapped passages and the empty-meta clauses (design, 2026-08-04)

Status: DESIGN — not implemented. Companion: JOIN_INTEGRITY_DESIGN.md (the
join's fan-out side; this document is its zero-match side),
TOOLING_BATCH_DESIGN.md. Origin: the census's two `unexplained_escalate`
verdicts, both with the note "Unmapped passage: join_fanout = 0
(segmentation-coverage gap)": `helpfulness__…letter_and_spirit_3` and
`harm-avoidance-to-third-parties__…restricted_content_1`.

## 1. Count first — the enumeration procedure is the design's first deliverable

Nothing is repaired until the gap population is enumerated mechanically.
The procedure, runnable today with existing modules and no panel-verdict
contact beyond passage identity:

For every panel passage in the TRUE universe (589 unique locators for the
model spec via `benchmark.load_true_panel`), compute
`inventory.match_passage(quote, clauses)` against `modelspec_clauses.json`.
Every passage joining to ZERO clauses is a gap candidate. Classify each with
`benchmark.map_reference`'s existing strata: `example_block`,
`not_verbatim_in_source`, `verbatim_but_unsegmented`, `unknown`. Report
count, locator, quote length, stratum, and per-behaviour panel score. The
enumeration is deterministic and belongs next to the join as a standing
check, not a one-off script.

**Measured result (2026-08-04, run during this design):** 7 unique locators
join to zero clauses — `#follow_all_applicable_instructions > ¶13`,
`#letter_and_spirit > ¶2`, `#letter_and_spirit > ¶3`,
`#ignore_untrusted_data > ¶13`, `#disallowed_content > ¶2`,
`#restricted_content > ¶1`, `#avoid_errors > ¶3` (21 behaviour-rows across
the three behaviours). **All seven classify `not_verbatim_in_source`** —
none is `verbatim_but_unsegmented`. Exactly two are reference-grade
(score ≥ 5) in some behaviour: `#letter_and_spirit > ¶3` (helpfulness, 6/6)
and `#restricted_content > ¶1` (harm-avoidance, 6/6) — precisely the
census's two escalations. So the scale question is answered: the population
is 7 locators, of which 2 currently cost reference recall, and the
worst-case "2–6 cases" prior was right in magnitude.

**Falsifiable bound:** if a future enumeration returns more than 12 locators,
or ANY member of the `verbatim_but_unsegmented` stratum, the theory in §2 is
wrong and repair stops pending re-diagnosis.

## 2. Diagnosis: these are transcription-variant misses, not missing segments

`modelspec_segmentation_summary.md` records 97.35% character coverage with 0
unaccounted characters, and independently found that its 14 published-set
join misses "are all panel transcription artifacts": the panel's renderer
rewrote markdown links inconsistently — sometimes to the link text, sometimes
to the target, occasionally both ways within one passage.
`inventory._variants` already matches on either rendering, but only
uniformly per passage; a passage mixing renderings across two links defeats
both variants. The seven zero-match quotes are long (135–865 chars), all
fail the verbatim-in-source check under every uniform variant, and all sit
in link-dense paragraphs. The document is fully segmented; the citation text
is what drifted.

## 3. Repair options, in preference order

1. **Normalizer extension (preferred, code-side).** Extend the variant set to
   choose each link's rendering independently, bounded (refuse and fall back
   to current behavior beyond, say, 8 variants per passage, to keep the join
   linear in practice). Acceptance: the seven locators map, each to exactly
   one clause, and no already-matched passage changes its mapped set —
   pre-registered as the cycle's mechanism-level prediction. This touches
   `inventory.py` only and composes with join v2 (locator restriction narrows
   the candidate set first, making the variant explosion harmless).
2. **Segment additions via the runbook's segmentation step (only if option 1
   leaves a residue).** Any repair that adds or splits clauses goes through
   `segment_modelspec.py` regeneration per NEW_DOCUMENT_RUNBOOK.md, and every
   added clause quote MUST be an exact verbatim substring of the source
   (`segment_modelspec` verification re-run, 100% or refuse). It is FORBIDDEN
   to author a clause whose text is adjusted toward the panel's rendering to
   make a join succeed — the source document is the only licensor of clause
   text. A clause-count change re-freezes `modelspec_clauses.json`'s sha and
   therefore trips every snapshot input pin; see ceremony, §5.
3. **Leave unmapped, accounted (the floor option).** The strata already charge
   unmapped reference passages as false negatives in `full` scoring; keeping
   them visible is honest and cheap. This remains the treatment for any case
   options 1–2 cannot repair without violating the verbatim rule.

## 4. The four empty-meta clauses

`modelspec_clauses.json` contains four content-free pseudo-heading clauses:
m0393 (`**When to express uncertainty**`), m0398 (`**Types of uncertainty**`),
m0535 (`Favoring longer responses:`), m0539 (`Favoring shorter responses:`) —
structural headings written as body paragraphs, kind `meta`, which "consume a
¶ but carry no content and never anchor anything" (segmentation summary).
They are the clause-side mirror of the degenerate-quote problem: a short
heading-like string that containment could bind to spuriously. Design: mark
them with a `content_empty: true` field at segmentation time and have the v2
join skip them as candidates (a passage whose quote is exactly such a heading
is refused under the degenerate floor anyway). They are NOT deleted and NOT
renumbered — ¶ arithmetic against the panel must stay stable. Acceptance:
join results over the current universe are unchanged by the skip (predicted
delta: zero — nothing currently maps to them; that prediction is itself the
regression test).

## 5. Ceremony fit

* Option 1 is a standard `code`-shape cycle: OPEN with document-side
  rationale (transcription variance, §2), PREDICT the exact seven locators
  that become mapped and zero clause-level flips, MEASURE/ADJUDICATE with no
  panel contact, census deferred to checkpoint. Its effect on reference
  recall (2 passages leave the structurally-impossible FN pool) is disclosed
  in the same re-measurement pass as JOIN_INTEGRITY_DESIGN §4 — one
  disclosure event, not two.
* Option 2, if ever needed, is an artifact-shape change: `modelspec_clauses.json`
  regenerates, its sha changes, and old snapshots become reconstructable only
  via the recorded input sha (amendment F9 / TOOLING_BATCH_DESIGN item 3).
  It requires its own cycle with the verbatim gate as a non-overridable test.
* The census keeps its rule that unmapped dossiers admit only
  `unexplained_escalate`; after repair, that verdict class should go to zero
  for these two ids, which is a checkable checkpoint prediction.
