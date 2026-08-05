# REGENERATION NOTE — measure/ artifacts re-derived on the post-S2/S3 tree (2026-08-04)

Recorded by the session coordinator (Qwen Code), per Matt Stults's decision (2) "regenerate".

## Why

Two `measure/` outputs carried by the P1 worktree were captured at an INTERMEDIATE
development point — before `DEGENERATE_QUOTE_FLOOR` was recalibrated 25 → 14 and before
`content_empty` was finalized — so they did not reproduce from the final code:

* `delta_v1_v2nomix.json` — the worktree copy had **12 entries** (a floor=25 capture,
  retaining floor-backstop refusals at normalized lengths 14–24). The final code (floor=14)
  yields exactly **6** locators, matching `prediction.draft.json` ("EXACTLY SIX locators
  change, none reference-grade").
* `join_map_v1.json` — its `empty_meta_candidates` field held the 7-item pre-finalization
  regex fallback `[m0002, m0032, m0393, m0398, m0496, m0535, m0539]`. The final
  `content_empty` predicate pins `[m0393, m0398, m0535, m0539]` (membership pinned by
  `test_content_empty_membership_is_pinned`).

The FINAL CODE was always correct (it matches the authoritative `prediction.draft.json`);
only these two recorded artifacts were stale. Regeneration restores the project invariant
that the committed record reproduces from the committed code.

## What was done

1. The two stale originals were preserved verbatim under `superseded_floor25/`
   (`superseded_floor25/delta_v1_v2nomix.json`, `superseded_floor25/join_map_v1.json`).
2. `diagnose_delta.py` and `baseline_join_map.py --mode v1` were re-run against the
   post-S2/S3 tree, regenerating `delta_v1_v2nomix.json` and `join_map_v1.json` in place.
3. Verified post-regeneration:
   * delta = **6 locators**, none reference-grade — the four empty-meta self-maps
     (`#be_thorough_but_efficient>¶2/¶6`, `#express_uncertainty>¶2/¶7`) +
     `#ignore_untrusted_data>¶2` (structural refusal + restriction) +
     `#protect_privileged_information>¶14` (structural refusal).
   * `empty_meta_candidates` = `[m0393, m0398, m0535, m0539]`.
   * v1 fan-out = `{0:7, 1:579, 2:1, 6:1, 28:1}`; v2_nomix fan-out = `{0:13, 1:575, 6:1}`.
   * v1 core locator mappings byte-identical to the superseded copy (only the
     `empty_meta_candidates` field differed).

## What was NOT touched (historical provenance)

The `red_transcript*.txt`, `green_transcript.txt`, and `full_suite_green.txt` files are
TDD red-green transcripts captured as the test-first record; they are preserved unchanged
and are NOT regenerated. `join_map_v2_nomix.json` already reproduced byte-identically and
was left as-is. The segmentation cycle's `join_map_v2.json` was not part of this action.
