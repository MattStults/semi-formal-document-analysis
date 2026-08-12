# Adversarial review of recurse_driver.py — disposition (2026-08-10)

Clean-context Fable review; 26 findings; every finding verified before action
(per the standing instruction: adversarial reviews over-report, validate first).
Remarkably, none refuted outright — dispositions below.

## FIXED, each with a RED test pin (24-test suite; phase_1 total 761 green)
F1 estimate ignored --leaf-max · F2 estimate not worst-case (now: max_tokens
output, DEPTH_MAX passes, repair-retry doubling; expected + ceiling printed) ·
F3 resume fingerprint (run_meta.json: brief/doc/model/leaf_max; mismatch
refuses) · F4 merges now union needs · F5 structure nodes get leaf-grade
validation · F6 empty-nodes and out-of-span uncovered rejected · F9 cache
tally reads the logged envelope (was dead code) · F10 cost.max_cost_usd
ceiling on measured spend + spend_invisibility_warning · F11 truncation
short-circuits instead of a futile same-cap retry · F12 validator exceptions
become repairable errors, malformed shapes hardened · F13 atomic writes ·
F15 empty child spans rejected · F17 inherited-seed carriage + established_
around provenance checked · F18 cross-sibling id collisions + id-prefix
convention enforced · F19 merge-loss checked BEFORE mutation · F20 no-op
resolutions error · F21 parse tries clean JSON first · F22 depth wedge names
the directory to delete · F25 failed replies buried in <out>/failed/.

## FIXED BY DESIGN CHANGE
F7/F8b: the Phase U prompt now carries compact ALL-node summaries (id,
establishes, provides with prose), so restatements under different names are
findable and renames are judged on prose. Structure-node grounding remains
weaker than the agent design (no span text in U) — quotes are validated
against the document, so fabrication dies in repair; residual: U cannot COIN
a grounded structure node it cannot see text for. Accepted residual, named.

## ACCEPTED, BY NAME, WITH GROUNDS
- F14a (spans ≤ leaf_max skip Phase D): deliberate cost optimization; the
  spec's per-agent Phase D presumed tool-using agents. Amendment recorded in
  the driver docstring. The unbounded-leaf half of F14 remains open: a model
  MAY declare a large span leaf; mitigated by truncation short-circuit and
  the ceiling, not eliminated.
- F8a (same-name needs auto-link): this IS the seed design; residual risk is
  measured (audit stratum B: 93% valid) and belongs to the audit, not the
  driver.
- F19a (merge_loss is a heuristic): documented as such; the audit's node-
  fidelity stratum is the semantic backstop.
- F23 (root_graph.json duplication): cosmetic; kept for consumer convenience.
- F24 (local chars/token constant): recorded; sourced to the same 3.5 value
  as phase_1 config. Consolidation deferred until the two estimators share a
  caller.
- F16 (cross_link_report unchecked): report contents are adjudication-grade
  material, checked by the audit protocol, not mechanically.
