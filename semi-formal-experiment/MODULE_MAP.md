# Module map — what is live, what is parked, what is history

Generated from the import graph (not from memory) on 2026-08-01, then hand-annotated.
**Partially refreshed 2026-08-02** after a drift review found it predated panel v2 and
described the query modules as they no longer are. Rows corrected below carry a ⚠️.
Read `HANDOFF.md` first for state and results; this file answers "what is all this code
and which of it matters to me?"

**Nothing here is dead code to be deleted on sight.** The repo carries three capabilities
plus the one-off scripts that built the data. Before removing anything, check the
dependency note in §5 — the parked capability is a *dependency of the live one*.

---

## 1. Priority 1 — RELEVANCE (the live product)

behaviour → which spec passages bear on it. This is what the project is for.

| module | loc | role |
|---|---|---|
| `inventory.py` | 214 | locators + `match_passage` quote-containment join. **Gates every metric.** |
| `measure_join.py` | 93 | ⚠️ the recall ceiling. **Do not quote 849/863** — that is the published-universe figure, and the published universe deleted every passage the panel scored 0. Re-run it; never cite the number from this table. |
| `measure_kinds.py` | 61 | relevance signal by clause kind; source of the conditional-only ceiling finding |
| `annotate.py` | 978 | clause → atoms, behaviour-agnostic, all 5 kinds → `annotations.json` |
| `behavior_atoms.py` | 825 | behaviour → atoms, **selected from the clause vocabulary** → `behavior_atoms.json` |
| `relevance.py` | 861 | ⚠️ the BAG scorer — **violates contract invariant 10** (a similarity score, not a structural query). No longer the only option: `benchmark.py --query-module {relevance,structural,section,combined}`. Its threshold constant is retired; `predict()` derives its operating point label-free (Otsu). It is also the ONLY module that consumes glosses lexically, which matters when reading read-back's sufficiency result. |
| `structural.py` | new | ⚠️ the TYPED query, invariant-10 compliant. Zero-parameter operators, `max_hops=0`. **Now has consumers** (`section.py`, `combined.py`, `benchmark.py --query-module`) — the "imported by nothing but its own test" note is obsolete. Ships `PRIMARY_OPERATOR = any_atom`, the *unselected* operator; the panel-fitted `act_match` is recorded but not run (its DiD selection cost is +0.045, 2.8x its declared bound). |
| `ontology.py` | new | relation layer. Mechanical path is a pinned NULL (20 edges/361 atoms; `contrary`+`entails` fire zero times). Annotated pass built, costed, **un-run**. |
| `panel_universe.py` | new | the TRUE 589-passage evaluation universe. Join rate 1.000 on all six cells. **Every pre-existing number was computed on a truncated universe and is wrong in the tool's favour.** |
| `benchmark.py` | 1277 | tool vs panel: MCC primary, floors, refuse-to-headline, per-gold head-to-heads |
| `lexical_control.py` | 160 | the control, implemented as a *weight setting of the same scorer* |

**⚠️ Added 2026-08-02 — these were live but undocumented here:**

| module | role |
|---|---|
| `threshold.py` | 11 label-free operating-point rules; `PREFERRED` = Otsu (zero free parameters). This is what retired `relevance.DEFAULT_THRESHOLD`, an in-sample argmax on the panel it was then scored against. |
| `section.py` | the section quotient. Ships `ELECTION_OPERATOR = any_atom`. Its own docstring used to read "⚠️ THIS LOSES. Measured −0.143 MCC" — that verdict was an artifact of an operator borrowed from `structural.py` and fitted on 3 behaviours. At `any_atom` it is the best single compliant predictor measured. |
| `combined.py` | typed core ∪ elected sections. Moved to `any_atom` before the other two. |
| `panel_v2.py` | the 9-behaviour × 2-spec panel (`../data/panel-coverage.json`, 4,314 citations). **`panel_universe.py` is the 3-behaviour predecessor — do not confuse them.** Several conclusions that held at n=3 invert at n=9. |
| `readback.py` | the panel-free representation harness: deterministic renderer (atoms → English, no model) + faithful/sufficient/discriminable. Answers "does the ontology describe the DOCUMENT", which nothing else here asks. Now covered by the anti-cheat scan. |
| `weight_diag.py` | **DIAGNOSTIC ONLY, fenced.** Supervised transfer probe; reads the panel by design. Its `NOISE = 0.045` is scoped to the 3-behaviour panel and guarded so it cannot outlive that scope. |

**Run order:** `annotate.py --live` → `behavior_atoms.py --live --annotations …` →
`benchmark.py --tool --annotations … --behaviour-atoms …` (add `--ablate` for channels).

## 2. Priority 2 — BEHAVIOUR-VS-DOCUMENT CONFLICT (built, blocked on Matt)

| module | loc | role |
|---|---|---|
| `conflict_output.py` | 1647 | blinded emitter + side-car + validator + judge prompt |
| `make_conflict_sample.py` | 201 | regenerates the sample and side-car reproducibly |
| `conflict_adapter.py` | new | **the tool → `ConflictFinding` adapter. IT EXISTS** — earlier text saying Matt must write one before judging is obsolete. |

**Adapter status: BUILT** (`conflict_adapter.py`). Earlier text here said no tool →
`ConflictFinding` adapter existed and Matt would have to write one before judging — that is
**obsolete**. What remains are Matt's two decisions (human vs model judges; which `conduct`
vignettes) and one honesty caveat preserved in `conflict_adapter.py`: the score it emits is a
**relevance** score, not a violation model, so the panel measures precision over a
relevance-ranked candidate list. See `CONFLICT_PANEL_README.md`.

## 3. Infrastructure (used by everything)

| module | loc | role |
|---|---|---|
| `providers.py` | 259 | provider-agnostic client; usage logging is ON by default |
| `spend.py` | 159 | budget accounting + an audit that reconciles artifacts against the log |
| `calibrate.py` | 120 | measures cost per batch per model from real usage |

## 4. Priority 3 — INTRA-DOCUMENT CONFLICT (parked, not discarded)

provision × provision: does the spec contradict itself. Deliberately parked after P1/P2.
**An earlier iteration built this while believing it was building the product** — do not
resume it without an explicit instruction.

`dsl.py` · `checker.py` · `extract_section.py` · `emit_asp.py` · `filter_extraction.py` ·
`baseline_conflicts.py` · `delta.py` · `adjudicate.py` · `run_conflicts.py` ·
`run_chain.py` · `integration_smoke.py` · `sweep.py` · `translate.py` (~6,000 loc)

## 5. ⚠️ The dependency that stops you deleting §4

`annotate.py` and `behavior_atoms.py` **import `extract_section.py`** — they reuse its
proven batching, span-id selection, `parse_response`, and `FailureLog`. `extract_section`
in turn imports `dsl` and `checker`. So the live relevance path depends on three modules
filed under the parked capability. Deleting §4 wholesale breaks §1.

If §4 is ever removed, first lift the shared machinery out of `extract_section.py` into a
neutral module. Do not do this speculatively — it is a real refactor with no user-visible
benefit.

## 6. One-off scripts that produced the data (history — do not re-run casually)

These built the clause files and are kept for provenance and re-derivation.

| module | produced |
|---|---|
| `segment_modelspec.py`, `modelspec_kinds.py` | `modelspec_clauses.json` (593 clauses, 97.35% coverage) |
| `classify_modelspec.py`, `extract_modelspec.py` | `modelspec_focus_areas.json` (259 focus areas) |

### 6b. Loss-taxonomy diagnostics (2026-08-02; panel-free, verified so by review)

Mine `readback_results.json`'s per-clause loss/fabrication phrases. All read only
`readback_results.json` / `hole_corpus.json` — a review grepped them for every panel
token and found zero, so they are deliberately NOT in the anti-cheat `FORBIDDEN` set.
None feeds a query, a prompt, or a threshold; conclusions go through blind two-coder
agreement, never one reading.

| module | produced |
|---|---|
| `prep_hole_corpus.py` | `hole_corpus.json` — 268 `missing` + 95 `unsupported` phrases with clause text, frozen coder input |
| (two panel-blind subagent coders) | `hole_taxonomy_coder_{a,b}.json`, `fabrication_taxonomy_coder_{a,b}.json` |
| `check_taxonomy.py` | independent re-derivation of a coder's coverage/counts (channel-aware) |
| `taxonomy_agreement.py` | chance-corrected partition agreement (ARI/NMI) + cross-tab, any two coder files |
| `hole_rollup.py` | category→grammar-feature rollup; ⚠️ its banner: the mapping is editorial, the counts are not |
| `diagnose_disagreement.py` | ⚠️ PANEL-READING (in FORBIDDEN, unlike the rest of this table): per-case tool-vs-frontier dumps → `case_fn.json`, `case_fp.json`, `DISAGREEMENT_REPORT.md` |

## 7. Superseded — kept only until someone confirms nothing needs them

| module | superseded by | note |
|---|---|---|
| `compare_to_panel.py`, `panel_join_paragraph.py` | `measure_join.py` + `benchmark.py` | earlier paragraph-anchored join attempts |
| `backfill_locators.py` | locators are now correct at source | |
| `atom_provenance.py` | — | **known broken**: keys on `clause_id`, `KeyError`s on a Model Spec extraction |
| `validate_behaviours.py` | `conflict_output.validate` | |

## 8. Data files

| file | size | status |
|---|---|---|
| `modelspec_clauses.json` | 496 KB | **live** — 593 clauses, the analysis unit |
| `annotations_b8.json` | 1.7 MB | **PREFERRED** — 1,629 atoms, **99% coverage, 183/183 example blocks**, 0 truncated, reuse 0.78 |
| `behavior_atoms_b8.json` | small | **PREFERRED** — 70 atoms, 100% in-vocabulary, pairs with `annotations_b8` |
| `annotations.json` | 1510 KB | superseded — 1,423 atoms, 91% coverage, 3 truncated batches lost 24 example blocks |
| `behavior_atoms.json` | small | superseded — 65 atoms, pairs with `annotations.json` |
| `constitution_clauses.json` | 311 KB | **live for swappability** — 616 clauses, same schema, loads today |
| `modelspec_focus_areas.json` | 197 KB | **privileged subset** — authority levels + rubric joins; no longer the analysis unit |
| `smoke_atoms.json` | 103 KB | 28-clause smoke output; safe to remove |
| `_extract_raw.json` | 198 KB | intermediate from an early extraction; safe to remove |

## 9. Reproducing the current numbers

```
.venv/bin/python -m pytest . -q                      # 808 passing
.venv/bin/python measure_join.py                     # join ceiling (re-derive; do not quote a remembered number)
.venv/bin/python measure_kinds.py                    # relevance signal by clause kind
.venv/bin/python spend.py                            # budget + unlogged-spend audit
.venv/bin/python benchmark.py --tool \
    --annotations annotations_b8.json \
    --behaviour-atoms behavior_atoms_b8.json            # the headline table
.venv/bin/python benchmark.py --ablate \
    --annotations annotations_b8.json \
    --behaviour-atoms behavior_atoms_b8.json            # channel contributions
```

`pytest.ini` excludes `external/` (vendored third-party repos whose tests need deps this
project does not install; collecting them fails the run before ours execute).
