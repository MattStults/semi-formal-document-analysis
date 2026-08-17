# Pilot subset — frozen 2026-08-16

Machine-readable form: `pilot_subset.json`. Produced by `coverage_translated.py`
(concentration of the pilot behaviors' frontier clause sets over the CURRENTLY
translated corpus) crossed with `corpus_gate_report.json` (the one defect
definition). Frontier labels direct attention, never truth; no matching code
reads any of these files.

## The re-measure that made the freeze possible

`pilot_behaviors.json`'s honest finding — "only ONE behavior concentrates >2x
in the translated spans" — was measured against the pinned 15-node sample. At
203 translated modules (183 with geometry in `node_corpus_all.json`; the other
20 are old-segmentation ids, excluded) the baseline span share is 29.0% and the
five originally selected behaviors all sit at or near lift 1.0 or better:

| behavior | lift | frontier clauses covered |
|---|---|---|
| how-to-approach-tradeoffs | 1.88 | 61/112 |
| animal-welfare-impacts | 1.51 | 33/86 |
| proportionate-risk-mitigation | 1.07 | 45/166 |
| harm-avoidance-to-third-parties | 1.00 | 33/133 |
| harmlessness-to-the-user | 0.97 | 53/196 |

**Decision: keep the original 5 selected behaviors** (DESIGN.md open question 1
resolves to "accept the 5" — the coverage that motivated narrowing to 3 was an
artifact of the 15-node sample). Retrieval recall against frontier clause sets
is still bounded by span coverage (27–54% per behavior); per DESIGN.md, score it
per-region so it does not read as a matcher failure. Largest gap regions:
`l2126_2404`, `l2821_3040`, `l4572_4692`, `l1368_1541` — translating those is
the highest-value corpus growth if the pilot's bound binds.

## Subset state at freeze (107 nodes)

* **15 hard-clean** as drafted.
* **85 licence-fix only** — every hard hit is the manufactured-citation class
  (`needs_gloss_licence`), mechanically correctable under
  `DECISION_licence_textual.md`: borrowed NEEDS gloss `textual`→`assumed` with
  the inference naming the NEEDS contract. Field-only; no redraw.
* **7 need real edits** (see `pilot_subset.json` `.status.needs_redraw`):
  6 × `provides_defined` (the promised predicate is never derivable — the
  root_authority shape at the provider end), 1 × `needs_in_requires` (two
  NEEDS names dropped from `requires`). These are redrawn under the corrected
  prompt, not hand-patched — the defect is in the module's reading of its
  contract, not in a field value.

Known bound accepted at freeze: the cross-module seam (14 shared names with
arity disagreements, 3 section-local gloss splits, concentrated in the
authority vocabulary) is NOT resolved by this subset work. The seam needs an
identity contract per shared name — arity, argument sort, one global gloss —
which is its own design step. The pilot runs with the seam as-is and the gate
report on the record; link-time silence caused by an arity mismatch is a known,
named phenomenon, not a surprise.
