# S4_ADVERSARIAL_REVIEW_R2 — clean-context adversarial design review (round 2) of SECTION_PRIOR_DESIGN.md

**Date:** 2026-08-05
**Artifact:** `semi-formal-experiment/SECTION_PRIOR_DESIGN.md` (the S4 section-prior evidence gate, design only, post-revision commit 1dc202e)
**Prior rounds:** `S4_ADVERSARIAL_REVIEW.md` (REVISE: 1 blocking, 4 majors, 5 minors) → revision → `S4_TIER2_VERIFICATION.md` (all 10 credited FIXED-CORRECT)
**Reviewer:** clean-context adversarial design reviewer (Tier 1, dispatched 2026-08-05 by the coordinator session; model: Opus 5). Every code citation was re-checked against the tree; every number was recomputed from artifacts on disk. No network calls, no repo writes.

---

## VERDICT: **REVISE**

Not a redesign — the mechanism is real, the enumeration reproduces exactly, and eight of the ten prior findings are genuinely fixed. But three things must change before OPEN, two of them created or left standing *by the revision itself*:

1. The design asserts the driver **enforces revert** on the `max_regressions` bound. It does not, and `CYCLE_DESIGN.md` says so explicitly. This is the load-bearing sentence of the fix to the blocking finding.
2. The specified gate-off construction parameter **cannot reach the shipped scorer** with the declared `files_to_change`. The cycle as manifested is not buildable, and the driver's closure check would not catch the undeclared edit.
3. The document-side arithmetic offered as *grounds* for `max_regressions: 0` is unsound — the census set and the flip set overlap in only 24 of 30 cells.

`S4_TIER2_VERIFICATION.md` credited (1) and (3) as FIXED-CORRECT while quoting the design's own claims back at it; it explicitly limited itself to "design-doc verification only — no code reads." That was the wrong scope for a fix whose entire content is a claim about what `cycle.py` does. Stated plainly, as instructed: **the Tier-2 pass credits a fix that does not hold as written.**

### Finding counts (new findings only)

| dimension | blocking | major | minor |
|---|:-:|:-:|:-:|
| Engineering excellence | 0 | 2 | 6 |
| Science | 0 | 1 | 3 |
| **total** | **0** | **3** | **9** |

No blocking finding. The three majors are each a paragraph or a manifest-line fix; none touches Rule A1 itself.

---

## Part A — Independent verification of the prior review's ten findings

I did not defer to `S4_TIER2_VERIFICATION.md`. Each ruling below is re-derived.

| finding | my ruling | note |
|---|---|---|
| **SCI-B1** (blocking) — bound not pre-registered | **FIXED, but the fix carries two defects** | The integer is pinned (`max_regressions: 0`) with a named decision rule, in §3, so PREDICT freezes it — that part is correct and sufficient. But the *mechanism claim* is false (new finding **E1**) and the *stated grounds* are unsound (new finding **S1**). |
| **ENG-M1** — enable/disable vehicle | **FIXED-CORRECT in text; FIX-CREATED-A-NEW-PROBLEM in the build** | "Unconditional once merged" is chosen and stated, the opt-in reading is rejected by name, and the DISPATCH-ONLY reachability departure is disclosed honestly. But the chosen vehicle is not executable with the declared file set — new finding **E2**. |
| **ENG-M2** — false `A2 ⇒ A1` lemma | **FIXED-CORRECT** | Verified against the baseline: m0587 atom `0.0`, lex `0.081882`, ungated section `0.580279` → A1 gives 0, A2 gives `0.0819`. Rules are incomparable, exactly as now stated. |
| **ENG-M3** — quality floors | **FIXED-CORRECT** | I re-measured on the exact test path. Ungated `0.2826 / 0.3502 / 0.2007`, gated `0.2474 / 0.3782 / 0.2626` — the design's table is exact to four places. Proposed floors 0.20/0.33/0.21 satisfy the `<= 0.065` ceiling test (gaps 0.047/0.048/0.053), and `test_mispaired_artifacts_do_not_clear_the_floors` still passes under the gate (mispaired gated mean `0.1636 < 0.25`; caution `0.1484` and helpfulness `0.0053` both trip). One residual: **E6**. |
| **SCI-M1** — corpus-max renormalization | **FIXED-CORRECT** | Condition verified: corpus-max clause has atom > 0 on every extant baseline; enumeration is now defined on the normalized surface, conditionality is explicit, and a violating future baseline is correctly routed to re-pin rather than falsification. One factual slip: **E8**. |
| **ENG-m1** — manifest gaps | **PARTIALLY FIXED / FIX-CREATED-A-NEW-PROBLEM** | `config.overlay` pinned ✓; `depends_on` correctly re-described as prose ✓ — but `census: deferred_to_checkpoint`, *in the same sentence*, is the identical not-a-schema-key error and was not corrected (**E4**). And adding `conftest.py` to `files_to_change` introduces an IMPLEMENT-gate trap (**E5**). |
| **ENG-m2** — census config identity | **FIXED-CORRECT** | Deferral with a named owner, which the prior review permitted. F13 → S8 and Group 0c both exist in `PORTFOLIO_REVIEW.md:62,74`. The gap is real and correctly described: `audit_dossiers/ext_v1_merged__audit_v1/index.jsonl` carries no config header at all today. |
| **ENG-m3** — two-axis dispatch | **FIXED-INCOMPLETE** | The sentence is there, but it is conditioned on a landing order the design never fixes, and the pricing axis already has **three** live rungs today, not one — **E3**. |
| **SCI-m1** — principle wording | **FIXED-CORRECT** | Counts verified exactly on the baseline: 506/510 (caution), 530/533 (harm), 442/451 (helpfulness) gated clauses carry lex > 0. |
| **SCI-m2** — unlock cliff | **FIXED-CORRECT** | Stopword floor confirmed at `relevance.py:553–555` (`0.0 if n in self.atom_stopwords`), so stopword atoms cannot unlock. The incentive is named for S6/S7 and S8 is named as the first observing instrument. |

---

## Part B — New findings

### ENGINEERING

#### E1 (MAJOR) — the driver does **not** enforce revert on `max_regressions`; the design says it does, at the exact point where the blocking finding was supposed to be closed

§3 states:

> "The driver REQUIRES this field as a non-negative integer and **gates keep-vs-revert on it** … Named decision rule, **leaving no judgment call at DECIDE** … revert is **the driver-enforced outcome**".

What the driver actually does:

* `cycle.py:1046–1056` — `_check_predictions_adjudicate` computes `regressions <= pred["max_regressions"]` and **records a dict** `{"kind": "max_regressions", …, "result": "PASS"|"FAIL"}` into `prediction_checks`. It returns `None`; it raises nothing.
* `cycle.py:1383–1390` — `_decide` reads `prediction_check.json`, computes `any_fail`, and the *only* consequence is: `if (any_fail or overrides) and not justification.strip(): raise CycleError`. A signed `decision.json` with `"decision": "keep"` and a non-empty justification passes with a FAILing bound.
* `CYCLE_DESIGN.md`, "The decision rule (policy-critical)": *"a FAILED prediction or an override obliges a written justification; **it never auto-decides**."* This is deliberate policy, not an omission.
* The program's own precedent proves it: `cycles/patient-pricing-2026-08-04/prediction_check.json` = `pass_rate [19, 20]`, the single FAIL being `{"kind": "max_regressions", "expected": 0, "observed": 5}` — and the cycle closed `"decision": "revert"` because a **human-signed** `decision.json` said so, with a 900-word justification. The tripwire fired; the *operator* pulled it.

Why it matters: the blocking finding's whole complaint was "the integer that decides the cycle is chosen by the operator." The revision correctly moved the integer into the design (good). But it then claims the *decision* is mechanical, which removes the one instruction a signer actually needs: **any regression → sign revert.** Under the true mechanism, the pre-registration binds by ceremony, not by code, and that has to be said so the DECIDE signer knows the obligation is theirs.

**Fix (one paragraph, no mechanism change):** replace "gates keep-vs-revert on it" / "driver-enforced outcome" / "leaving no judgment call at DECIDE" with the accurate statement — the driver validates the field, computes the tally, records PASS/FAIL, and refuses an unjustified decision; **the revert is the signer's pre-registered obligation under this design**, exactly as it was for S3. Keep everything else.

#### E2 (MAJOR) — the specified gate-OFF construction parameter cannot reach the shipped scorer, and `files_to_change` is incomplete for it

§6(b)/(c) specify: the index carries "one explicit construction parameter (gate on/off) whose DEFAULT is on", and the absent-key dispatch rung rebuilds the ungated scorer "by **passing the gate-OFF parameter EXPLICITLY**". `files_to_change` = `relevance.py`, `snapshot.py`, `dossier.py`, `conftest.py`, `test_quality_floor.py`, tests. **`containment.py` and `patient.py` are not declared.**

But the dispatch ladder does not construct `RelevanceIndex` on the path that matters:

* `dossier.py:346–364` `_index_for` dispatches `pricing_version == "2.0"` → `patient.PatientIndex.from_files`; overlay present → `containment.ContainmentIndex.from_files`; else → `relevance.RelevanceIndex.from_files`.
* The entire keep lineage — including the baseline the log resolves to (`join-integrity-v2-2026-08-04`, `pricing_version: "1.2"`, `overlay: overlay_empty.json`) — takes the **ContainmentIndex** rung.
* `containment.py:452–458`: `ContainmentIndex.from_files(cls, clauses_path, annotations_path, weights=None, *, edges=())` → `cls(base.clauses, base.annotations, weights, edges=edges)`. `containment.py:350`: `__init__(self, clauses, annotations=None, weights=None, *, edges=())`. **No `**kwargs`, no pass-through.** Same for `patient.py:189,229`.

So a kw-only `gate` parameter added to `relevance.RelevanceIndex.__init__` is simply unreachable through the only constructors the ladder calls. The absent-key branch would silently fall through to the merged default — which §6(c) itself names as the exact failure to avoid ("the absent-key branch must not fall through to the merged default").

Worse for the record: this would *not* halt. `CLOSURE_DEFAULTS` (`cycle.py:120–121`) is only the three data artifacts, and the closure is `gate_tests ∪ config inputs ∪ CLOSURE_DEFAULTS − files_to_change`. `containment.py` is in neither set, so editing it undeclared passes the two-sided one-variable check silently and leaves a manifest that misstates the diff.

**Fix — pick one and write it into §6:**
* (a) declare `containment.py` (and `patient.py`, once S3b's rung exists) in `files_to_change` and thread the parameter; or
* (b) change (c)'s wording from "construction parameter" to a **post-construction assignment in `dossier.py`** (`idx.<gate> = False` on the absent-key branch) — buildable with the declared set, since `dossier.py` is declared; or
* (c) make the gate a `relevance.Weights` field — it then flows through all three `from_files(..., weights=...)` signatures untouched, and surfaces automatically in snapshot `config.weights` and `diff_snapshots`'s `weights_changed`, at the cost of putting the switch on the swept surface (which §2's parameter-free argument may not want).

Option (b) is the smallest change and preserves the design's intent.

#### E3 (MINOR, borderline major) — the two-axis obligation is written for a future that has already arrived

§6(c): "whichever of S3b and S4 lands SECOND must extend EVERY rung of the first axis with the other." Two problems:

1. The pricing axis has **three live rungs today**, not one: `"2.0"` → PatientIndex, overlay → ContainmentIndex, absent → legacy — and snapshots exist on all three (`patient-pricing-2026-08-04` = 2.0; `join-integrity-v2` / `patient-backfill` / `decoration-blind-join` = 1.2; `versioned-cut` / `chain-repair` / `baseline-*` = absent). S4 must extend all three **whether or not it lands second**; the conditional wording implies otherwise.
2. `HANDOFF.md` ⭐⭐⭐ already fixes the order — *"NEXT STEP: run the S3b build …, then S4 — SEQUENCED (dispatch-ladder composition), not parallel"* — so S4 lands second, and this design's §5 ordering note ("this cycle does not wait for S3b") does not say so. The obligation is therefore S4's, concretely, and should be stated as such rather than as a rule about hypothetical orderings.

**Fix:** one sentence — "S4 extends all three existing pricing rungs with the gate branch; per HANDOFF ⭐⭐⭐ S4 lands after S3b, so it also extends S3b's new rung."

#### E4 (MINOR) — `census: deferred_to_checkpoint` is not a manifest key either

§6 lists it as a manifest field, in the same sentence in which `depends_on` was correctly demoted to prose. It is not in `manifest_template` (`cycle.py:227–244`) or `REQUIRED_MANIFEST_KEYS` (`:247–250`), and **no manifest on disk carries it** (checked all six in `cycles/*/manifest.json`; only `patient-pricing` carries an extra key, `depends_on`, the tolerated-noise case the design already names). The driver sets it itself: `cycle.py:672–673`, `if shape == "code": state["census"] = "deferred_to_checkpoint"`. Same correction, one clause later.

#### E5 (MINOR) — the ENG-m1 fix put `conftest.py` in `files_to_change`, which is a halt if it doesn't change; and a genuinely new test file cannot be declared at OPEN

* IMPLEMENT refuses when any declared file is byte-identical to its OPEN sha (`cycle.py:830–836`). `conftest._OPTIONAL` needs an entry **only if a new test module is added**. `test_relevance.py` is *not* in `_OPTIONAL` (it is collected unconditionally), so gate tests placed there require no `conftest.py` change at all — and the cycle would then halt on its own manifest.
* Conversely, `_open` refuses any `files_to_change`/`gate_tests` path that does not exist (`cycle.py:638–640`), so a brand-new `test_section_gate.py` cannot be declared at OPEN unless it is created (at least as a stub) beforehand.

**Fix:** state the choice — "gate tests land in `test_relevance.py` (existing, not `_OPTIONAL`), so `conftest.py` is **not** in `files_to_change`"; or "a new test file is created pre-OPEN and registered, and `conftest.py` is declared."

#### E6 (MINOR) — the floor re-derivation is pre-registered; the floor file's *stated measurements* are not

The design pre-registers re-deriving `FLOORS` + `MEAN_FLOOR` with a ⚠️ rationale comment. But `test_quality_floor.py` also documents measured values in prose that become false under the gate, and this repo treats a floor file's honesty about its own numbers as load-bearing:

* module-level `FLOORS` comment: "Measured label-free: helpfulness +0.2007, harm-avoidance +0.3502, over/under +0.2826" → becomes `+0.2626 / +0.3782 / +0.2474`.
* `test_mispaired_artifacts_do_not_clear_the_floors` docstring: "helpfulness **+0.0019**, over/under +0.2516, harm-avoidance **+0.3421**", "**the MEAN is the load-bearing guard here** (+0.1985 vs a 0.23 floor)", and the two per-behaviour clearance claims. Recomputed under the gate: **`+0.0053 / +0.1484 / +0.3369`, mean `+0.1636`** — and the guard's coverage *changes character*: caution now trips too (0.1484 < 0.20), where the docstring says it clears. The "honest limit of this guard" note becomes wrong in the tool's favour.

**Fix:** add these four numbers to the same pre-registration line.

#### E7 (MINOR) — the containment interaction is currently vacuous, so its gate test needs a synthetic fixture, and §5 overstates the stakes

§5: "gating on exact names only would silently punish the overlay's adjudicated wins (cycles 1–3). Gate test: a clause scored solely via a containment edge must be un-gated." But the shipped overlay is `overlay_empty.json` — `"edges": []`, `max_edges: 0`, whose own provenance statement says it exists *only* as the vehicle that routes scoring through `ContainmentIndex` so `pricing_version` gets recorded, with "containment.json's licensed edges … dormant (overlay reactivation is cycle S5's job)". No clause in any current baseline carries subsumption credit. The requirement is right and forward-looking, but a builder hunting for such a clause in the live corpus will find none. Say the test is written against a synthetic edge fixture, and that the interaction goes live at S5.

#### E8 (MINOR) — the corpus-max clause ids are not correct for "all extant baselines"

§3 says the condition is "verified on all extant baselines (corpus-max clauses m0527 / m0592 / m0438)". Recomputed per snapshot: caution `m0527` and harm `m0592` hold everywhere, but helpfulness's corpus-max is **`m0384`** on `chain-repair-2026-08-04` and `versioned-cut-2026-08-04`, and `m0438` only on the 1.2 lineage. The *condition* (atom > 0) holds in every case — the claim is safe, the id list is not. Since §6 turns this into an asserted OPEN-time check, the check should be written as "per behaviour, whichever clause is corpus-max", never against pinned ids.

#### E9 (MINOR) — the log-read mechanization silently drops the "spine" qualifier

§5 quotes the standing rule as "latest closed-KEEP **spine** snapshot" and then mechanizes it as "the LAST line whose `decision` is `keep`". `CYCLE_LOG.jsonl` records `{census_consulted, census_deltas, cycle, date, decision, exploratory, noop, overrides, prediction_pass_rate, shape}` — **no field distinguishes a spine keep from any other keep.** The two rules are not equivalent, and a future off-spine keep (different annotations/atoms/overlay) would be silently selected. Today it resolves correctly (last keep = `join-integrity-v2-2026-08-04`; snapshot present; `pricing_version 1.2`, `overlay_empty`, `thresholds_frozen`, all three `threshold_source: frozen_artifact` at exactly the frozen cuts). The mitigation already exists — §5's re-enumerate-or-re-pin rule — so this is a wording gap, not a hole. Note in passing that `HANDOFF.md` ruling 2 names `patient-backfill-2026-08-04` as "the latest closed-KEEP … in `cycles/CYCLE_LOG.jsonl`", which the log has since superseded; the design's refusal to name a baseline statically is vindicated.

### SCIENCE

#### S1 (MAJOR) — the stated *grounds* for `max_regressions: 0` are unsound: the census set is not the flip set

§3 argues:

> "the ONLY clauses on which a regression could even be licensed are atom-GAP clauses … and their number is bounded by the census's own tool-sided count: **4 of 30** … any bound ≥ 5 is ungrounded under every reading".

The "30" on the left (census `fp_section_prior` cases) and the "30" on the right (A1 flips) are **different sets**. Computed against the log-resolved baseline, behaviour-keyed:

| | |
|---|---|
| A1 flips | 30 |
| census `fp_section_prior` cells | 30 |
| **intersection** | **24** |
| flips outside the census class | **6** |
| census cells that do not flip | 6 (all six atom>0, all panel-sided — the design's own forecast, verified exactly right) |

The 6 flips outside the class:

* `helpfulness/m0379, m0381, m0382, m0389` — census FPs, but classified **`fp_threshold_drift`**, panel-sided, not `fp_section_prior`.
* `caution/m0176` and `harm/m0586` — **not census disagreements at all**, i.e. cells where tool and panel agreed and A1 removes the clause anyway.

So the census's tool-sided count of 4 bounds the tool-sided autopsies *within one census class*; it does not bound the atom-gap population inside the flip set, which contains six cells that class never examined. "Any bound ≥ 5 is ungrounded under every reading" does not follow from the arithmetic offered.

**Severity, weighed honestly:** the *conclusion* is unaffected and is the conservative direction — 0 follows from §2's principle alone ("substitution-banned flips are correct removals; the design licenses none"), and 0 is also the template default. Nothing about the pre-registration changes. But this is the **second false quantitative lemma** in a document whose stated function is precision, and it sits in the paragraph that closes the program's only blocking finding. Prior-round ENG-M2 was rated MAJOR on exactly this reasoning (a false lemma that did not change the recommendation); consistency requires the same rating here.

**Fix:** delete the census-arithmetic step, or restate it correctly — "0 follows from the principle: the design licenses no substitution-mode regression at all. The census's 4 tool-sided autopsies are named as the *class* where a regression is most likely to surface, not as a bound on the flip set, which contains 6 cells the census never classified as `fp_section_prior`."

#### S2 (MINOR) — §3 under-pre-registers: the flip set has an exact, sharper, label-free characterization

Recomputed on the log-resolved baseline: the number of **predicted** clauses with `atom == 0.0` is **13 / 13 / 4** — identical to the flip counts, per behaviour. Every predicted atom-zero clause flips out; none survives. So on this baseline A1 is exactly equivalent, at the frozen cut, to *"do not predict any clause with zero atom evidence."*

That is a strictly stronger, entirely label-free, mechanically checkable pre-registration than "flip-outs only on clauses with atom exactly 0.0" (which permits survivors), and it is free to add. It also sharpens the disclosed cost honestly: the `fn_names_cannot_meet` exposure is exactly co-extensive with the flip set, not a subset of it.

#### S3 (MINOR) — scale disclosure: "touch the mode, not the weight" understates how much of the channel the mode is

§2 rejects Rule C (lower the `section` weight) on the ground that only the *substitution mode* is indefensible. Computed on the baseline, the fraction of total section-channel mass A1 removes:

| behaviour | % of corpus section mass removed | % of predicted-set section mass removed | gated share of corpus |
|---|---:|---:|---:|
| avoiding-over-and-under-caution | 71.9% | 22.8% | 510/593 |
| harm-avoidance-to-third-parties | 75.3% | 27.2% | 533/593 |
| helpfulness | 64.8% | 4.4% | 451/593 |

A1 deletes roughly **two-thirds to three-quarters of all section credit in the corpus**. The Rule-C rejection is still sound — A1 is content-conditioned where a weight change is not, and it leaves the amplify case exactly bit-identical — but a reader should be told that "the mode" is most of the channel, especially given §0's admission that the channel's aggregate value is UNKNOWN (paired bootstrap CI spans zero). Two lines of disclosure; it strengthens rather than weakens the case.

#### S4 (MINOR) — two gaps in the fitting-risk provenance and the DEV forecast

* **Provenance.** §0 discloses that the *class* was named by the census. It does not disclose that the *gate predicate* is the census's own discriminator: `atom_channel_zero` is computed by `audit_disagreements.py:248` — a module whose docstring reads "PANEL-READING, DIAGNOSTIC-ONLY — in the anti-cheat FORBIDDEN set". This is a disclosure gap, not a violation: the census's `fp_section_prior` *signature* is "section is the dominant channel share" (`audit_disagreements.py:131–137`), and A1 deliberately does **not** use that predicate — using it would have required a share threshold, i.e. exactly the swept constant §4 refuses. Choosing atom-zero over the class's own signature is the more principled choice, and saying so out loud is a stronger disclosure than the current silence.
* **Forecast.** §3's dossier-class forecast names `fp_section_prior` (shrink) and `fn_*` (may grow). Per S1, it should also forecast **`fp_threshold_drift` shrinking by up to 4** and **2 tool-panel agreements converting to FNs** — otherwise the S8 checkpoint will show class movement this design did not predict, and the re-narration risk §3 exists to prevent reappears at the checkpoint.

**My judgment on the §0 fitting-risk question, asked directly:** the guards are **adequate, and thin**. What genuinely holds: A1 is parameter-free (there is no literal to sweep, which is the guard that actually bites); B and C are rejected on the correct ground; census contact is deferred to S8 and DEV-stamped; the complete flip set is adjudicated document-side under a seat fenced from this document; and `max_regressions: 0` is the only bound that cannot pre-license the banned class. What remains: the rule *shape* was selected with the census discriminator in view, and the honest characterization of A1 (S2) is a large scorer change — "require atom evidence to predict" — presented as a narrow one. With S2, S3 and S4's disclosures added, the guards are adequate. Without them, the design is fitting-safe in mechanism but under-disclosed in framing, which is how the deleted HANDOFF section got written in the first place.

---

## Part C — What I verified as CORRECT

So the findings above are not read as blanket doubt. All of the following reproduce exactly under independent recomputation:

1. **Every code citation I checked is materially accurate.** `relevance.py:491–492` (`section: float = 0.45`, `section_top_k: int = 3`); the section step at `704` (`local`), `706–709` (`sec[path]`), `711` (assignment); membership map at `568–574`; stopword floor at `553–555`; smoothed idf at `565`; `rank()` normalization at `780–782`. `cycle.py:794–796` (field validation), `1051–1054` (the tally check), `622–630` (`compatibility` refusal for `shape: code`), `FLIP_BUDGET = 30` at `113` with a strict `>` halt at `981`. `snapshot.assert_frozen_thresholds` at `snapshot.py:351`; `diff_snapshots`'s scoring-identity loop at `447`; `dossier.ReconstructionMismatch` at `78`/`461`. `_measure`'s snap_cmd threads exactly `annotations/atoms/overlay/thresholds` — the "no new seam, `cycle.py` not in files_to_change" claim is correct on its own terms. `containment.ContainmentIndex.channel_scores` delegates to `super()`, so a gate in `relevance.py` does cover the shipped path. (Only cosmetic slip: `channel_scores` is defined at line 660, not 694.)
2. **The mechanism reading is exactly right.** The section channel is pure unconditional propagation; `local` is computed before any section credit is assigned, so A1 leaves `sec[path]` untouched and there is genuinely **no second-order propagation**. Independently confirmed.
3. **The 30-flip enumeration, recomputed from scratch.** Against `snapshots/join-integrity-v2-2026-08-04.json` (the snapshot the log-read rule actually resolves to): **13 caution + 13 harm + 4 helpfulness = 30**, `newly_predicted` = **0**, every flipped clause has atom exactly 0.0, helpfulness ids exactly `m0379 / m0381 / m0382 / m0389`. **Identical** against `patient-backfill`, `decoration-blind-join`, `chain-repair` and `versioned-cut`. 30 is *at* the F4b line, and the halt is strict `>`, so the stratified-sampling path does not trigger. HANDOFF ruling 3 is confirmed, not stale.
4. **The corpus-max condition holds** on every baseline (caution `m0527`, harm `m0592`, helpfulness `m0438`/`m0384` — all atom > 0).
5. **Every census statistic.** `verdicts_merged.json`: 294 cases, 30 `fp_section_prior`, 18 caution / 12 harm / 0 helpfulness, side 26 panel / 4 tool. Dossiers: **24/30 `atom_channel_zero`** (and 24/30 still atom-zero when recomputed against the overlay-on baseline, so the figure is not a pre-containment artifact); section channel-share **0.428 – 0.956, median 0.892**; worked example m0587 = atom 0.0 / lex 0.081882 / section 0.580279 / share 0.876341, zero matched atoms, empty `exact_name_intersection`.
6. **The design's own class forecast is exactly right** where it is checkable: the 6 census cases with atom > 0 are precisely the 6 that do not flip, and all 6 are panel-sided. The 4 tool-sided cases are all atom-zero and all flip.
7. **The lexical-self-evidence counts** behind SCI-m1: 506/510, 530/533, 442/451.
8. **The quality-floor table**, reproduced on the exact test path to four decimals, in both directions.
9. **The baseline resolution.** The log's reverted `patient-pricing` line carries `"decision": "revert"` and is correctly skipped; the last keep resolves to a snapshot that exists, passes `assert_frozen_thresholds` on all three behaviours at exactly `thresholds_frozen.json` v1's values, and carries `overlay_empty.json` / `pricing_version 1.2` — i.e. the config the design pins. Every closed cycle publishes a snapshot under its own cycle name, so the "closed cycles publish under their own tag" premise holds for all six.
10. **All cross-references resolve:** `PORTFOLIO_REVIEW.md` F13 (checkpoint census = S8, "m0587 gets a named vocab follow-up") at line 62, Group 0c at line 74; `MEAN_FLOOR` and the `<= 0.065` ceiling test in `test_quality_floor.py`; `test_quality_floor.py` in `conftest.REQUIRED`.
11. **`SECTION_GATE_VERSION = "1.0"` is not a new-constant-governance object** — it is a version string, not a numeric literal in a scoring path (`REPRODUCIBILITY.md`, "A bare literal in a scoring path is a review finding"). A1 introduces no sweepable number. That claim in §2 is true and is the design's strongest guard.
12. **The seat fence, the deferral-as-terminal-state option, and the DEV stamping** are all correctly carried, and the design correctly refuses to name its own baseline.

---

## Recommendation — the shortest list that makes this READY-FOR-OPEN

1. **(E1)** Correct §3's mechanism claim: the driver validates, tallies, records PASS/FAIL and refuses an unjustified decision; **the revert on any `regression` is the DECIDE signer's pre-registered obligation under this design.** Keep `max_regressions: 0` and the named rule exactly as they are.
2. **(E2)** Fix the gate-off reachability: either declare `containment.py` (+`patient.py`) in `files_to_change`, or restate §6(c) as a post-construction assignment inside `dossier.py`. One sentence either way; `files_to_change` freezes at OPEN, so this cannot be deferred.
3. **(S1)** Delete or restate the "4 of 30" arithmetic. The bound stands on the principle; the census step does not survive the set mismatch (24/30 overlap; 6 flips outside the class, 2 of them tool-panel agreements).
4. **(Minors, all one-liners)** E3 extend all three existing pricing rungs and state the fixed S3b→S4 order; E4 drop `census` as a manifest key; E5 resolve the `conftest.py` / new-test-file question; E6 add the four mispaired-guard numbers to the floor pre-registration; E7 say the containment gate test uses a synthetic edge fixture; E8 check corpus-max per behaviour, not by pinned id; E9 note the log has no spine marker; S2 pre-register the sharper "flip set = predicted ∧ atom == 0" characterization; S3 disclose the 65–75% section-mass figure; S4 disclose the predicate's census provenance and add `fp_threshold_drift` to the checkpoint forecast.

After (1)–(3), this cycle should open. Rule A1 itself needs no change: it is parameter-free, its enumeration reproduces exactly against four independent baselines, its cost is disclosed rather than denied, and its tripwire is set at the only defensible value.
