# QUERY-CLASS SATURATION STUDY — coordinator spec
(2026-08-25. Written by the Fable driver as the one-time spec; an OPUS
coordinator executes it phase by phase. Fable touches only the phase
gates (machine-check scripts) and the final analysis. Zero Fable seats.)

## Purpose
Bound the space of behaviour-shaped capability questions over character
specs: code real behaviour definitions as constraint patterns over the
norm frame's argument places, measure pattern saturation, estimate
richness. Output feeds the content-ontology completeness spec and a
frozen next-document prediction.

## Coding vocabulary (FROZEN — the judgment call is made here)
For each behaviour definition, code:
- places_constrained (1-3 from): subject | act | object_sphere |
  governed_quality | beneficiary | condition | exception_structure |
  authority | character_force | modality
- query_verb (1 of): select | check | order | compare | complete
- pattern = sorted(places) + verb. "New pattern" = unseen pattern string.
Blind rule: coders see ONLY the definition text and this vocabulary,
never other codings, never this spec's purpose section.

## Phases (coordinator: checkpoint your status file after EVERY phase —
## write partial results with complete:false; never end-write-only)
P1 CORPUS (target 60-100 definitions, floor 50): collect behaviour/
  trait/rule definitions with provenance from: the OpenAI Model Spec's
  own section-level behaviour concepts; Anthropic public materials
  (constitution/character posts, usage policy categories); published
  HHH and Sparrow rule lists; public safety-eval taxonomies; and the
  local behaviours-for-adria set (search the repo). Each entry: id,
  definition text (verbatim, 1-4 sentences), source, url-or-path.
  Dedupe near-identical entries. Write query_class_corpus.json.
  GATE-1 (Fable script): n>=50, all entries have all fields, no dupes.
P2 CALIBRATION: seeded 15-definition sample (seed 20260858). Dispatch
  TWO fresh Opus seats coding the sample under the frozen vocabulary
  (blind; packet = vocabulary + definitions only). Write
  qc_calib_opusA/B.json. GATE-2 (Fable script): coverage + value-
  legality + inter-seat agreement (report; no threshold — Opus is the
  reference tier).
P3 PARITY: dispatch TWO Sonnet and TWO Haiku seats on the SAME sample,
  same packet. (Haiku brief line: output must be VALID JSON; escape
  internal quotes.) Write qc_calib_{sonnetA,sonnetB,haikuA,haikuB}.json.
  GATE-3 (Fable script): per-tier consensus vs Opus consensus on
  pattern strings; CERTIFY the cheapest tier with agreement >= 0.80
  (pattern-exact) and >= 0.90 (places-overlap Jaccard). No tier
  certifies -> bulk runs on Opus; say so, don't stretch.
P4 BULK: remaining definitions, 2 seats at the certified tier, plus a
  seeded 15% Opus spot-check (seed 20260859), tripwire >20% pattern
  disagreement on the spot sample -> halt, surface. Write
  qc_bulk_{A,B}.json + qc_spotcheck_opus.json, checkpointing every 25
  definitions.
P5 (Fable, deterministic): consensus assembly, accumulation curve
  bootstrapped over 200 seeded orderings, Chao1 richness estimate + CI,
  the pattern inventory, and the frozen next-document prediction.
  Script: query_class_analysis.py (committed with this spec).

## Coordinator conduct rules
Execute this spec exactly; do not redesign it. Every dispatched seat's
prompt comes from the committed packet files you write, never retyped.
If any phase cannot be completed as specified (source unavailable,
seat failure), record the gap in the status file and continue —
surface, never improvise. Your status file is
qc_study_status.json: {phase, complete, counts, gaps[]} — update it
after every phase AND every 25-item batch within P4.
