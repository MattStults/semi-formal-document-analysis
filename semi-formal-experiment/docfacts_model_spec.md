<!-- DOCUMENT FACTS for the OpenAI Model Spec (modelspec_clauses.json).

     Spliced into annotate_prompt.md by annotate.load_template at the
     {{DOCFACTS:<key>}} markers; everything outside a BEGIN/END pair is a
     comment and is never sent. This is the default docfacts file, and the
     composed default prompt is pinned byte-identical to the pre-split
     2026-08-03 prompt (test_annotate.py: PRE_SPLIT_*_SHA) — every block
     below is VERBATIM the text that was moved out of annotate_prompt.md,
     so do not reflow it.

     Facts recorded here, with their source: the Model Spec's chain of
     command names root and system as distinct authority levels (Model Spec
     "Levels of authority"); `platform` was the level's name in the
     2024-05-08 version, renamed to `root` in the 2025 revisions. -->

<!-- DOCFACTS:situation_example BEGIN -->
"the
              operator's instruction conflicts with a root rule",
<!-- DOCFACTS:situation_example END -->

<!-- DOCFACTS:principals BEGIN -->
   `root` and `system` are DIFFERENT levels and the difference is what can
   override them. `root` rules come only from this document and cannot be
   overridden by a system message, a developer or a user. `system` rules are
   set by the same author but CAN be carried or overridden through a system
   message, so they vary by serving surface and by user; they still outrank
   developer and user. If a clause says "root or system", it named two levels,
   not one. There is no `platform` — that was this document's old name for
   `root`, from a version in which it ranked equal to `system`.
<!-- DOCFACTS:principals END -->
