# Module map — what is live, what is parked, what is history

Generated from the import graph (not from memory) on 2026-08-01, then hand-annotated.
**Partially refreshed 2026-08-02** after a drift review found it predated panel v2 and
described the query modules as they no longer are. Rows corrected below carry a ⚠️.
**Refreshed 2026-08-04** for the iteration-loop arc: §1b (loop modules), §1c (loop
data + directories), an updated §8 preferred-artifact table, and briefs/ in §10.
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

## 1b. The iteration loop (added 2026-08-04 — live)

The loop's contract is `ITERATION_LOOP.md`; the orchestrator's is `CYCLE_DESIGN.md`
(with its 2026-08-04 BINDING AMENDMENTS). Classification discipline as elsewhere in
this file: **panel-blind** modules are statically scanned by `test_no_reference_leak.py`
forever; **FORBIDDEN** modules read the panel by design and are themselves tokens in
the anti-cheat list, so no query module can import them (or read their output dirs)
without the fence firing.

| module | role | panel status |
|---|---|---|
| `snapshot.py` | Unit 1: freeze a tool run (per-clause scores, channels, predicted sets, config shas incl. overlay + `--thresholds` artifact) → `snapshots/<tag>.json`; `diff` → flip lists. Deterministic, byte-identical on same inputs | **panel-blind, scanned** (query-adjacent) |
| `dossier.py` | Unit 2: one flip → one self-contained case file (Haiku-operability: dossier in → verdict out, no repo access); `validate` checks verdict files with check_taxonomy discipline; build-time reconstruction self-check fails loudly on drifted inputs | **panel-blind, scanned**; holds NO panel fields |
| `atom_refactor.py` | Unit 3: `usages` / `rename` / `merge` / `rechain` / `split` over every vocabulary surface, dry-run by default, every apply appended + replayable via `vocabulary_migrations.json` | panel-blind |
| `containment.py` | Unit 4: licensed `child ⊑ parent` overlay (`containment.json`) over the atom matcher; PRICING_VERSION 1.1 (one credit per atom, kind factor + min-idf cap, never-outprice invariant, required budget, one-child rejection, unanimous-child kind inheritance). The shippable config after containment cycles 1–3 | **query module OUTRIGHT** — scanned |
| `cycle.py` | the cycle DRIVER: state machine OPEN → PREDICT → IMPLEMENT → MEASURE → ADJUDICATE → DECIDE → CLOSE over typed artifacts in `cycles/<name>/`; census only in the CHECKPOINT shape, `census: deferred_to_checkpoint` otherwise. Ran the versioned-cut and chain-repair cycles end-to-end | **FORBIDDEN token** (`import cycle`, `cycles/`) — it orchestrates panel-reading census tooling; the fence is disclosure to the driver, never to query time |
| `audit_disagreements.py` | the disagreement-census instrument: one dossier per tool-vs-panel disagreement + closed cause taxonomy + validator. Produced the 294-case census in `audit_dossiers/ext_v1_merged__audit_v1/` | **FORBIDDEN token — PANEL-READING BY DESIGN**, like `diagnose_disagreement`; seat brief `briefs/disagreement_autopsy.md` |
| `select_audit.py` | the SELECT-step instrument: vocabulary sweep (sufficient direction) + query read-back (faithful direction). **v2 contract**: seats score 0–3, only score 3 actionable, budget overflow = measured miscalibration (binary v1 sweeps returned 32–47% in-scope — unusable). Its v2 findings produced `behavior_atoms_audit_v1.json` mechanically | diagnostic-only, **panel-free** |
| `cut_stability.py` | the cut-stability diagnostic that the containment cycles' m0422 escalation demanded: perturbs recorded score distributions label-free and reports cut movement bands + the near-cut bystander census → `cut_stability_results.json`. Its verdict (class is structural) motivated the frozen cut | label-free, reads snapshots only |
| `chain_audit_worksheet.py` | builds/validates the principal-chain audit (`chain_audit/worksheet.json` / `verdicts.json`): every chained atom with its agent-first reading + licensing clause text; closed verdict vocabulary. Fed the chain-repair cycle (97 correct / 11 agent_missing / 1 unlicensed) | document-side, deterministic |
| `grammar.py` | the atom notation: `parse_name` / `stem_of` / `format_name` / `describe` — polarity prefixes, AGENT-FIRST principal chains, roles. Imported by containment (edge licensing) and the query side | panel-blind, scanned |
| `threshold.py` (update) | unchanged as the rule library; the OPERATING POINT is now frozen per behaviour in `thresholds_frozen.json` (cycle `versioned-cut-2026-08-04`) — `snapshot.py --thresholds` consumes it; omitting the flag keeps the old rule-derived behavior reachable (F9 version dispatch) |

## 1c. Iteration-loop data + directories (added 2026-08-04)

| path | what it is |
|---|---|
| `snapshots/` | frozen tool runs: `baseline-2026-08-03`, `containment-v0/v1/v1.1`, `ext-v1`, `baseline-2026-08-04-auditv1`, `versioned-cut-2026-08-04`, `chain-repair-2026-08-04` |
| `cycles/` | ⚠️ FORBIDDEN-fenced dir: per-cycle state (`manifest`, sha-frozen `prediction`, `review_verdict`, `decision`, `state.json`) for the versioned-cut and chain-repair cycles + `CYCLE_LOG.jsonl` (one line per closed cycle) |
| `dossiers/` | containment cycles 1–3: flip dossiers, blinded adjudication verdicts, and the three KEEP `decision.json` records (cycle 3 = the shippable overlay config; the m0422 standing escalation lives there) |
| `audit_dossiers/ext_v1_merged__audit_v1/` | ⚠️ panel-derived: the 294-case census + `verdicts_merged.json` (155 `fp_promiscuous_atom` / 59 `fp_threshold_drift` / 30 `fp_section_prior` / 26 `fn_family_absent_from_vocabulary` / 19 `fn_names_cannot_meet` / 2+2+1 join/unexplained/fn_threshold). Query modules may not read this dir |
| `chain_audit/` | worksheet + verdicts of the principal-chain audit (plus the pre-repair worksheet backup) |
| `select_audit/` | rosters, sweep verdicts and findings, v1 and **v2** (`findings_v2_*.json` — the source of `behavior_atoms_audit_v1.json`) |
| `containment.json` | the licensed overlay edges + required budget (declared readable by scanned modules) |
| `thresholds_frozen.json` | v1 frozen per-behaviour cuts (0.2162/0.2365/0.3131) with label-free provenance chain |
| `cut_stability_results.json` | the diagnostic's artifact: cut-movement bands + bystander ids per behaviour × snapshot |
| `vocabulary_migrations.json` | the replayable migration log every `atom_refactor --apply` appends to |
| `golden_second_author.json` | 6 clauses translated cold by a second panel-blind author — source of the human ceiling 0.29 name / 0.79 span / 0.91 decoration that made `golden.py`'s scoring span-anchored |
| `golden_expansion_a.json`, `golden_constitution.json` | hand-authored, panel-blind golden expansions (structure-rich Model-Spec picks; constitution side) |
| `expert_salience.json` | the first HUMAN-expert relevance signal (salience-flattening finding + 2 core-passage anchors, reserved with the sealed TEST) |

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
| `annotations_ext_v1_merged.json` | large | **PREFERRED (2026-08-04)** — gpt-5.6-luna, 1,442 atoms / 589 clauses / 590-name vocabulary; the first structure-bearing annotation (force, agent-first principal chains post chain-repair, roles). The census configuration |
| `behavior_atoms_audit_v1.json` | small | **PREFERRED (2026-08-04)** — 42/31/37 query atoms for the 3 DEV behaviours; mechanical re-selection from `select_audit/findings_v2_*.json`, no LLM in that step |
| `annotations_ext_v1.json`, `annotations_ext_v1_patch.json`, `patch_clauses_ext_v1.json` | — | inputs the merged artifact was built from; keep for provenance |
| `behavior_atoms_ext_v1.json` | small | superseded by `behavior_atoms_audit_v1.json` (it was the pre-audit selection the DISAGREEMENT_REPORT_ext_v1 survey ran under) |
| `annotations_b8.json` | 1.7 MB | ⚠️ was PREFERRED until 2026-08-04 — 1,629 atoms, 99% coverage, 183/183 example blocks, reuse 0.78. Now the b8 comparison config in JOIN_INTEGRITY_DESIGN's re-measurement protocol |
| `behavior_atoms_b8.json` | small | ⚠️ was PREFERRED — 70 atoms, 100% in-vocabulary, pairs with `annotations_b8` |
| `annotations.json` | 1510 KB | superseded — 1,423 atoms, 91% coverage, 3 truncated batches lost 24 example blocks |
| `behavior_atoms.json` | small | superseded — 65 atoms, pairs with `annotations.json` |
| `constitution_clauses.json` | 311 KB | **live for swappability** — 616 clauses, same schema, loads today |
| `modelspec_focus_areas.json` | 197 KB | **privileged subset** — authority levels + rubric joins; no longer the analysis unit |
| `smoke_atoms.json` | 103 KB | 28-clause smoke output; safe to remove |
| `_extract_raw.json` | 198 KB | intermediate from an early extraction; safe to remove |

## 9. Reproducing the current numbers

⚠️ 2026-08-04: the commands below still run but quote the b8 config; the preferred
config is `annotations_ext_v1_merged.json` + `behavior_atoms_audit_v1.json` (+ frozen
thresholds via `snapshot.py --thresholds thresholds_frozen.json`). The suite is now
~1,960 tests. Loop equivalents: `python3 snapshot.py <tag>` / `python3 snapshot.py diff
a b`, `python3 cycle.py status|next`, `python3 audit_disagreements.py dossiers`
(panel-reading — audit seat only).

```
.venv/bin/python -m pytest . -q                      # 808 passing (2026-08-01 count)
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

## 10. briefs/ — the judgment-seat contracts (added 2026-08-04)

REPRODUCIBILITY.md's sandwich rule: every LLM/human judgment seat runs under a
versioned brief in the repo, between a deterministic producer and a mechanical
validator. Seats are Haiku-operable by default (a small/frontier divergence is
diagnosed as a seat defect first); three ⚠️ seats are explicitly frontier/human.

| brief | seat | producer → validator |
|---|---|---|
| `flip_adjudicator.md` | dossier → verdict, the loop's document-side adjudication | `dossier.py` → `dossier.py validate` |
| `disagreement_autopsy.md` | ⚠️ the ONE panel-seeing seat (disclosure, not blindness): cause attribution over census dossiers | `audit_disagreements.py dossiers` → `validate` |
| `select_audit.md` | vocabulary sweep + query read-back (v2: 0–3 scoring) | `select_audit.py` both sides |
| `blind_coder.md` | two-coder open coding over the frozen loss corpus | `prep_hole_corpus.py` → `check_taxonomy.py`/`taxonomy_agreement.py` |
| `golden_author.md` | panel-blind hand-author of golden translations | — → `golden.load` sha-freeze + `test_golden.py` |
| `golden_review.md` | ⚠️ frontier/human: golden-set audit (catches the author) | — |
| `change_reviewer.md` | ⚠️ frontier/careful: the cycle IMPLEMENT-gate review (freeze shas, declared-diff-only, tests bind incl. a mutant, fence scan) | `cycle.py` writes the assignment → `review_verdict.json` |
| `decision_signer.md` | ⚠️ careful/authorized: the cycle DECIDE seat — document-side adjudications decide, census numbers inform | `cycle.py` drafts → signed `decision.json` |
