# Change review assignment — cycle join-integrity-v2-2026-08-04

Seat brief: briefs/change_reviewer.md — read it first; it is the seat's
entire instruction. This is a frontier/careful seat: it exists to catch the
implementer's mistakes, so the small-model standard does not apply.

Change under review (from the manifest):

- fix_description: JOIN v2 (parallel-track P1; JOIN_INTEGRITY_DESIGN.md build-as-is per PORTFOLIO_REVIEW, F12 rulings applied): inventory.match_passage_v2 = the quote-containment join behind two independent guards plus the F9 empty-meta skip. (2a) Locator-restricted candidates: the passage locator's section anchor, on exact equality with a clause section_id, restricts candidates to that section BEFORE containment; anywhere the key is absent the join falls back to the full corpus with a disclosed restricted:false fact. (2b) Degenerate-quote refusal: the LOAD-BEARING structural arm refuses a quote that is a proper substring of every one of >1 post-restriction candidates; the backstop floor refuses normalized quotes under DEGENERATE_QUOTE_FLOOR before enumeration. Refusal returns no clauses plus the machine-readable degenerate_quote_refused flag, which benchmark.map_reference records as the NEW fifth stratum (accounting identity strata-sum==unmatched preserved; score_tool books a refused reference passage as an unmatched FN in full scoring). (F9) content_empty is a CODE-SIDE predicate (kind meta AND bold-heading or short trailing-colon pseudo-heading; membership pinned to {m0393,m0398,m0535,m0539}); such clauses are never candidates; modelspec_clauses.json is NOT touched. Versioning: JOIN_VERSION_V1/V2 constants; v1 (match_passage) is untouched and stays the DEFAULT at every existing entry point (map_reference, score_tool, clause_joins, evaluate all gain an explicit join_version parameter and record it in their outputs; per-passage restriction/refusal facts exposed via join_facts / clause_join_facts); audit_disagreements.config_identity gains the join_version seam for CENSUS identity (F12: census identity, NOT snapshot identity — snapshots carry no join key). IMPLEMENTATION DEVIATION, licensed by the design's own calibration rule and requiring reviewer sign-off at OPEN: DEGENERATE_QUOTE_FLOOR recalibrated 25 -> 14 (see design_vs_reality in prediction.draft.json).
- document_side_rationale: The join gates every passage-level metric (its own banner). The 28-fan-out passage #ignore_untrusted_data>¶2 (quote = the 21-char header '!!! meta "Commentary"', a substring of all 28 commentary clauses corpus-wide) manufactured two maximal false positives the census attributed to fp_join_artifact; the fix's inputs are the passage locator (document structure), clause section_id (produced by segment_modelspec.py from the document alone), and quote text — no panel verdict, judge rating, or gold value participates (JOIN_INTEGRITY §5: labels directed attention via the census; they supply no parameter). Re-measurement of historical numbers is NOT run here — it rides the S8 checkpoint census (design §4), which is why v1 stays the default at every entry point: no published number moves silently mid-spine.
- files_to_change: inventory.py, benchmark.py, audit_disagreements.py
- gate_tests: test_join_v2.py, test_benchmark.py, test_inventory.py, test_audit_disagreements.py, test_no_reference_leak.py

Required output: review_verdict.json in this cycle's directory:

    {"verdict": "proceed" | "blocked",
      "by": "<who reviewed — never the implementer>",
      "notes": "<what was verified, or why blocked>"}

All three keys are REQUIRED; verdict is a CLOSED set. The driver re-checks
the frozen manifest/prediction shas, the two-sided one-variable check and
the gate tests mechanically; your seat verifies what the machine cannot
(see the brief: freeze shas, declared-diff-only, tests bind — at least one
mutant — and the fence scan). A "blocked" verdict halts the cycle until
resolved and re-reviewed.
