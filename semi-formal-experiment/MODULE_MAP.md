# Module map — what is live, what is parked, what is history

Generated from the import graph (not from memory) on 2026-08-01, then hand-annotated.
**Partially refreshed 2026-08-02** after a drift review found it predated panel v2 and
described the query modules as they no longer are. Rows corrected below carry a ⚠️.
**Refreshed 2026-08-04** for the iteration-loop arc: §1b (loop modules), §1c (loop
data + directories), an updated §8 preferred-artifact table, and briefs/ in §10.
Read `HANDOFF.md` first for state and results; this file answers "what is all this code
and which of it matters to me?"
**Accuracy pass 2026-08-04**: stale counts, the containment pricing ladder, the anchor
count and the snapshot/cycle enumerations corrected; §0 added.

---

## 0. Running things (read this first)

Every command in this file assumes you are **in `semi-formal-experiment/`**, invoking the
repo venv by path — no `source`, no `cd` mid-command. Module imports and default artifact
paths are script-anchored, so a module invoked by absolute path from elsewhere does still
run; what breaks outside this directory is (a) the bare `.venv/bin/python` prefix, which
only resolves here, (b) the bare `pytest -q` form, which from the repo root would try to
collect `engine/`'s vendored suites, and (c) every relative argument in these docs
(`cycles/<name>/…`, `snapshots/<tag>.json`, `--dir`/`--out-dir` values). Just run from here.

```
.venv/bin/python -m pytest -q                        # the suite (see §9 for the count)
.venv/bin/python cycle.py status --cycle NAME        # where a cycle stands
.venv/bin/python cycle.py next   --cycle NAME        # advance one phase
```

- **`--cycle NAME` is effectively required.** It is technically optional and falls back to
  "the single open cycle", but that fallback refuses whenever 0 or ≥2 cycles are open — and
  ≥2 is the normal state here (the parallel-safe P-track cycles run alongside the spine).
  Omitting it today gets you `REFUSED: 2 open cycles (…) — pass --cycle NAME.` Always pass it.
- Dependencies are `pytest` and `clingo` (the ASP path in §4); `weight_diag.py` alone wants
  `numpy` + `scikit-learn` and imports them lazily, so the suite runs without them. Provider
  calls use stdlib `urllib` — there is no SDK to install and **no `requirements.txt`**.
- The venv at `semi-formal-experiment/.venv` is the one the suite is run under.

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
| `containment.py` | Unit 4: licensed `child ⊑ parent` overlay (`containment.json`) over the atom matcher. **PRICING_VERSION is `"1.2"`** — see the ladder below | **query module OUTRIGHT** — scanned |
| `patient.py` | patient-aware match pricing, `PRICING_VERSION = "2.0"`, defined ON TOP of 1.2. **Built and REVERTED** (cycle `patient-pricing-2026-08-04`) — in the tree, tested, not in the shipped path | **query module** — scanned |

**The pricing ladder, corrected 2026-08-04** (an earlier revision of this file stopped at
"1.1, the shippable config after cycles 1–3" — that has been false since S1 shipped):

| version | what it added | status |
|---|---|---|
| (none) | no `pricing_version` key in a snapshot → reconstructs through the untouched legacy `relevance.RelevanceIndex` (overlay-less path) | dispatch target only |
| 1.0 | one credit per atom (a matching, not a product), kind factor + min-idf cap, never-outprice invariant, required budget, one-child-family rejection | superseded |
| 1.1 | + unanimous-child kind inheritance. Shippable after containment cycles 1–3 | superseded |
| **1.2** | the **decoration-blind join** (spine cycle S1, `decoration-blind-join-2026-08-04`, KEEP): match key, atom df/idf and lexical atom-text all read the DECHAINED name (polarity kept, principal chain stripped); chains survive as pricing metadata on `self.chains`. Identity on chain-free names, so pre-1.2 snapshots stay reconstructible | **CURRENT — this is what `containment.py` sets** |
| 2.0 | patient-aware pricing (`patient.py`, spine cycle S3, `patient-pricing-2026-08-04`) | **BUILT AND REVERTED** — the frozen prediction pre-registered `max_regressions = 0`; the blinded seat returned 5 regressions over 18 flips, 4 confirmed bidirectionally by a split-blind frontier leg (m0239, m0275, m0466, m0018). The bound fired; the module stays in the tree, out of the shipped path |
| `cycle.py` | the cycle DRIVER: state machine OPEN → PREDICT → IMPLEMENT → MEASURE → ADJUDICATE → DECIDE → CLOSE over typed artifacts in `cycles/<name>/`; census only in the CHECKPOINT shape, `census: deferred_to_checkpoint` otherwise. Has now run **five** cycles end-to-end (`cycles/CYCLE_LOG.jsonl`: 4 KEEP + 1 REVERT — the bound fired on patient-pricing). CLOSE also drafts `commit_message.txt` + `staging_list.txt`; it never commits | **FORBIDDEN token** (`import cycle`, `cycles/`) — it orchestrates panel-reading census tooling; the fence is disclosure to the driver, never to query time |
| `audit_disagreements.py` | the disagreement-census instrument: one dossier per tool-vs-panel disagreement + closed cause taxonomy + validator. Produced the 294-case census in `audit_dossiers/ext_v1_merged__audit_v1/` (headerless — it predates item 0c and is NOT backfilled; see §11). Item 0c: every run now writes a `config_identity` header as index.jsonl's first line — input shas, overlay/thresholds as explicit nulls when absent, `threshold_rule`, and the pinned join (`join_version` + `mixed_variants`, F12: join identity is CENSUS identity). `--overlay`/`--thresholds`/`--join-version`/`--mixed-variants` on `dossiers`; `validate` refuses a headerless dir | **FORBIDDEN token — PANEL-READING BY DESIGN**, like `diagnose_disagreement`; seat brief `briefs/disagreement_autopsy.md` |
| `select_audit.py` | the SELECT-step instrument: vocabulary sweep (sufficient direction) + query read-back (faithful direction). **v2 contract**: seats score 0–3, only score 3 actionable, budget overflow = measured miscalibration (binary v1 sweeps returned 32–47% in-scope — unusable). Its v2 findings produced `behavior_atoms_audit_v1.json` mechanically | diagnostic-only, **panel-free** |
| `cut_stability.py` | the cut-stability diagnostic that the containment cycles' m0422 escalation demanded: perturbs recorded score distributions label-free and reports cut movement bands + the near-cut bystander census → `cut_stability_results.json`. Its verdict (class is structural) motivated the frozen cut | label-free, reads snapshots only |
| `chain_audit_worksheet.py` | builds/validates the principal-chain audit (`chain_audit/worksheet.json` / `verdicts.json`): every chained atom with its agent-first reading + licensing clause text; closed verdict vocabulary. Fed the chain-repair cycle (97 correct / 11 agent_missing / 1 unlicensed) | document-side, deterministic |
| `grammar.py` | the atom notation: `parse_name` / `stem_of` / `format_name` / `describe` — polarity prefixes, AGENT-FIRST principal chains, roles. Imported by containment (edge licensing) and the query side | panel-blind, scanned |
| `threshold.py` (update) | unchanged as the rule library; the OPERATING POINT is now frozen per behaviour in `thresholds_frozen.json` (cycle `versioned-cut-2026-08-04`) — `snapshot.py --thresholds` consumes it; omitting the flag keeps the old rule-derived behavior reachable (F9 version dispatch) |

## 1c. Iteration-loop data + directories (added 2026-08-04)

| path | what it is |
|---|---|
| `snapshots/` | frozen tool runs, **one `<tag>.json` per snapshot tag**; tags are either a config name (`baseline-2026-08-03`, `containment-v0` / `-v1-pricing` / `-v1.1-kindinherit`, `ext-v1`, `baseline-2026-08-04-auditv1`) or a cycle name (`<cycle>.json`, written by that cycle's snapshot_build). **Enumerate with `ls snapshots/`** — the previous hand-list here undercounted (11 files on disk at 2026-08-04). `snapshot.write_snapshot` refuses a differing rewrite of an existing tag without `--force` |
| `cycles/` | ⚠️ FORBIDDEN-fenced dir: **one directory per cycle**, named `<slug>-<date>`, holding that cycle's typed artifacts (`manifest.json`, sha-frozen `prediction.json`, `review_verdict.json`, `decision.json`, `state.json`, `flip_dossiers/` + `flip_verdicts.json`, and from S1 on `commit_message.txt` + `staging_list.txt`) — plus `CYCLE_LOG.jsonl`, **one line per CLOSED cycle**. `ls cycles/` and `cycles/CYCLE_LOG.jsonl` are the source of truth; do not maintain a list here. At 2026-08-04: 7 cycle dirs, 5 of them closed (versioned-cut, chain-repair, decoration-blind-join, patient-backfill, patient-pricing), 2 open (join-integrity-v2, segmentation-variants) |
| `dossiers/` | `dossier.py`'s default output root, `<tag_a>__<tag_b>/` per set — in practice the **pre-driver** containment cycles 1–3: flip dossiers, blinded adjudication verdicts, and the three KEEP `decision.json` records (cycle 3 = the last pre-driver shippable overlay config; the m0422 standing escalation lives there). Driver-era cycles write to `cycles/<name>/flip_dossiers/` instead |
| `drift_standing/` | the drift-standing seat pass: 61 stripped near-cut dossiers under `dossiers/`, two blinded leg verdict files (+ reruns) and a tiebreak, `assignments/`, and `DISCLOSURE.md` (the once-per-rule-family casebank consultation rule). Reporting only — changes no number, no predicted set, no threshold |
| `audit_dossiers/ext_v1_merged__audit_v1/` | ⚠️ panel-derived: the 294-case census + `verdicts_merged.json` (155 `fp_promiscuous_atom` / 59 `fp_threshold_drift` / 30 `fp_section_prior` / 26 `fn_family_absent_from_vocabulary` / 19 `fn_names_cannot_meet` / 2+2+1 join/unexplained/fn_threshold). Query modules may not read this dir |
| `chain_audit/` | worksheet + verdicts of the principal-chain audit (plus the pre-repair worksheet backup) |
| `select_audit/` | rosters, sweep verdicts and findings, v1 and **v2** (`findings_v2_*.json` — the source of `behavior_atoms_audit_v1.json`) |
| `containment.json` | the licensed overlay edges + required budget (declared readable by scanned modules) |
| `thresholds_frozen.json` | v1 frozen per-behaviour cuts (0.2162/0.2365/0.3131) with label-free provenance chain |
| `cut_stability_results.json` | the diagnostic's artifact: cut-movement bands + bystander ids per behaviour × snapshot |
| `vocabulary_migrations.json` | the replayable migration log every `atom_refactor --apply` appends to |
| `golden_second_author.json` | 6 clauses translated cold by a second panel-blind author — source of the human ceiling 0.29 name / 0.79 span / 0.91 decoration that made `golden.py`'s scoring span-anchored |
| `golden_expansion_a.json`, `golden_constitution.json` | hand-authored, panel-blind golden expansions (structure-rich Model-Spec picks; constitution side) |
| `expert_salience.json` | the first HUMAN-expert relevance signal: the salience-flattening finding + **4 core-passage anchors — THREE anthropic-side (two pinned by `expert_core_passage_starts`, one qualitative/unpinned) plus ONE openai-side**. "Two anchors" was a miscount (PORTFOLIO_REVIEW addendum ruling 1); corrected here 2026-08-04. The three anthropic anchors are sealed with the constitution TEST; the openai anchor is consumed EXACTLY ONCE, at the generalization evaluation. Nothing may be fitted to any of them |

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
**2,156 passed / 3 skipped (measured 2026-08-04)**. Loop equivalents:
`python3 snapshot.py <tag>` / `python3 snapshot.py diff a b`,
`python3 cycle.py status|next --cycle NAME`, `python3 audit_disagreements.py dossiers`
(panel-reading — audit seat only). The S8 checkpoint census pins its whole
configuration on that entry point rather than inheriting any of it:
`audit_disagreements.py dossiers --overlay <edges.json> --thresholds thresholds_frozen.json
--join-version 2` (add `--mixed-variants` only to opt into the unmeasured per-link variant
set) — every one of those choices lands in the run's `config_identity` header.

⚠️ **Test counts drift, and every count written into a doc goes stale within days** — this
one has already been wrong twice (a "808 passing" line frozen at 2026-08-01 and a "~1,960"
line frozen at 2026-08-02 both survived into 2026-08-04). **The command is the source of
truth, not any number in this file.** If you need the count, run it; if you write it down,
date it.

```
.venv/bin/python -m pytest . -q                      # 2,156 passed / 3 skipped (2026-08-04)
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
| `backfill_author.md` | ⚠️ frontier/careful: does the CLAUSE TEXT license a principal chain this atom instance left off, and which? | `backfill_worksheet.py build --dir` → `validate --dir` |
| `drift_standing.md` | the STANDING contents of the frozen cut — near-cut clauses where nothing flipped; two independent blinded legs, reporting only | `drift_dossiers.py dossiers` → `validate` |

**Validator invocations, explicitly** (never written down before; the flag spellings differ
ON PURPOSE — CYCLE_DESIGN.md F9, pinned by `test_dossier.py::
test_the_two_validators_keep_their_distinct_flag_spellings`, and hardcoded in `cycle.py`):

```
.venv/bin/python dossier.py validate --dir cycles/<name>/flip_dossiers \
                                     --verdict-file cycles/<name>/flip_verdicts.json
.venv/bin/python audit_disagreements.py validate --verdicts <file> --dossier-dir <dir>
.venv/bin/python drift_dossiers.py     validate --verdicts <file> --dossier-dir <dir>
.venv/bin/python backfill_worksheet.py validate --dir <dir>
```

The panel-blind flip seat is singular (`--verdict-file`) because the plural `--verdicts` is
a FORBIDDEN token — it names per-judge panel labels. Do not "harmonize" them.

## 11. ⚠️ Anti-rules — things that look like bugs and are not (added 2026-08-04)

Every entry below is a change a competent agent would make in good faith, and every
one breaks a contract. They are enforced by tests; this section is the only prose
statement of *why*. Check here before "cleaning up" anything in this list.

| Looks wrong | Actually required | Enforced | What the "fix" would break |
|---|---|---|---|
| `containment.load_edges` skips the one-child-family check when no vocabulary is passed | The skip is deliberate | `test_containment.py:732-733` | Running it unconditionally makes already-frozen overlay snapshots unreconstructable |
| Empty-overlay equivalence asserted at recorded PRECISION, not bit-identity | Precision is the contract | `test_containment.py:145-147` | Tightening to `==` fails on float summation order (hash-seed dependent) |
| The verdict loader accepts a bare list, `{"records": …}`, *and* any single list-valued key | The tolerance is a contract; genuine ambiguity must refuse | `test_dossier.py:540-548`, `:565-569` | "Standardizing on one shape" orphans every historical verdict file |
| `dossier.py --verdict-file` vs `audit_disagreements.py --verdicts` | Must stay divergent | `test_dossier.py:583-598`, `CYCLE_DESIGN` F9 | Plural `--verdicts` is a FORBIDDEN token (it names per-judge panel labels) |
| Patient pricing's monotone-downward invariant (I2) is asserted on RAW scores only | Normalized scores MAY rise — the corpus-max normalizer moves | `test_patient.py:290`, `:314`, `:326` | Asserting it on `rank()` writes a false-by-design test; "fixing" the normalizer silently changes every ranking number. Raw-untouched flips that crossed a cut are `normalizer_drift`, a threshold class, never `match_change` |
| `--mixed-variants` under `--join-version 1` raises instead of being ignored, and the census header records `mixed_variants` as an explicit `null`/bool rather than omitting it | The census RECORDS the join it ran; a silently-ignored flag would make that record false. The mixed per-link variant set is v2-only and opt-in (`inventory.match_passage_v2` default flipped to False in `68b036d`) | `test_audit_disagreements.py` (`mixed_variants_is_opt_in_and_v2_only`), `test_join_v2.py` (`map_reference_threads_the_variant_set_choice`) | "Accepting the flag anywhere" ships a census whose header names a variant set it never used — the same class of defect as the 2026-08-03 plain-index rebuild of an overlay config |
| The 294-case census under `audit_dossiers/ext_v1_merged__audit_v1/` has no config-identity header and none is added | It predates item 0c and is a measurement OF RECORD; a header written now would be a reconstruction asserted as provenance | (nothing regenerates it) | Backfilling one fabricates the identity of a run nobody observed. `validate` refusing that directory is the honest outcome: re-census under current tooling, never retrofit |
| Degenerate inputs return refusals or floor values, never flattering ones | `jaccard(∅,∅) == 0.0`; a cut predicting everything or nothing is `DEGENERATE_CUT` and is never selected; an empty sweep must not report perfect F1 | `test_threshold.py:140-142`, `:157-205`; `test_benchmark.py:642` | "Vacuous agreement is total agreement" reasoning produces flattering numbers from empty sets |

### Registration is what fences a module — not this table

Adding a module to §1b documents it; it does not fence it. In the SAME diff:

* a new **query-side** module must be appended to `test_no_reference_leak.QUERY_MODULES`,
  and it needs a drivable surface — a scan that skips is not a guard
  (`test_no_reference_leak.py:43-81`, `:591-594`);
* a new **panel-reading** module must be added to `FORBIDDEN`, or it becomes a
  laundering path for every module permitted to import it
  (`test_unsupported_ablation.py:60-65` and siblings);
* a new **test** module goes in `conftest._OPTIONAL`.

All three registrations belong in the cycle's declared diff.
