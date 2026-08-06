# S5 ADVERSARIAL REVIEW — `CONTAINMENT_WIDENING_DESIGN.md` (the overlay-reactivation cycle S5)

**Artifact:** `semi-formal-experiment/CONTAINMENT_WIDENING_DESIGN.md` (dated 2026-08-04; S5 is specified in §0.5, with §4/§5/§7 supplying the machinery it inherits)
**Review date:** 2026-08-05 · Tier 1, clean context, decision point = cycle OPEN
**Reviewer method:** every code citation re-derived from the tree; every number recomputed from artifacts on disk; the S5 snapshot actually built and diffed in a scratch directory (read-only w.r.t. the repo; `cycle.py` never run; no network calls)

## VERDICT: **REVISE**

**4 BLOCKING · 8 MAJOR · 5 MINOR**

The design's *procedure* is largely sound and its most-attacked parts (the frozen order, the dead-53 handling, the min-idf cap) hold up. But S5 as written cannot be opened as a cycle, and — measured — it cannot be falsified either: **turning the licensed edges on produces exactly zero flips on the current corpus.** A cycle whose keep/revert "cites the flip adjudications only" and which has no flips is a rubber stamp, and it is the gate every widening cycle depends on.

> ⚠️ **Disclosure that must ride into the cycle record.** This review measured S5's outcome before OPEN. The temporal guarantee is therefore already gone, exactly as `CYCLE_DESIGN.md` § PRE-BUILT CYCLES describes it: *"this is already gone and no procedure restores it. Do not construct a ritual that appears to restore it."* S5's prediction notes **and** its decision justification must state that the flip count was known before the prediction was frozen. Without that line, an honest zero-flip pre-registration would read to a later reader as a blind prediction that came true.

---

# ENGINEERING

## BLOCKING

### ENG-B1 — S5 is not expressible as a cycle: it changes no file, and the one file it points at is closure-**pinned**

§0.5 defines S5 as "turn the existing v1.1 edges ON … snapshot → diff". Mechanically that is a change to the *manifest's own* `config.overlay` value — from `overlay_empty.json` to `containment.json`. The driver has no shape for that:

* `PHASES_BY_SHAPE` (`cycle.py:97-103`) offers only `code` and `checkpoint`. S5 is not a checkpoint (census deferred).
* For `shape: code`, OPEN refuses an empty `files_to_change` (`cycle.py:623-625`: *"a code fix cycle changes something"*) and refuses a missing `compatibility.version_key`/`statement` (`:626-631`). The design supplies neither.
* Worse, `config.overlay` is added to the **closure pin** at OPEN (`cycle.py:661-668`: `closure = gate_tests ∪ {annotations, atoms} ∪ {overlay, thresholds} ∪ CLOSURE_DEFAULTS`, minus `files_to_change`). So `containment.json` must **not** change. And if it is instead declared in `files_to_change` to satisfy the non-empty rule, the IMPLEMENT gate refuses because it is byte-identical to its OPEN sha (`cycle.py:661-667` in `_implement`: *"the fix has not been implemented"*).

There is no path through the driver as designed. The fix is available and cheap (see the change list), but the design must name it; today it would halt an operator at OPEN.

### ENG-B2 — §4's expected-effect statement is incomplete **by construction**: it is atom-channel only, and the scorer propagates through the section channel

§4 defines the pre-registration as the diff of `subsumption_matches`, and §4's falsification rule says any newly-predicted clause without a predicted record "is a bug investigation that blocks the KEEP decision" (escape hatches: threshold-drift tag, `section_gate_reactivation`).

Computed on S5's own configuration (baseline `join-integrity-v2-2026-08-04` → overlay `containment.json`):

| | count |
|---|---|
| clauses whose score changes | **24** (all `harm-avoidance-to-third-parties`) |
| clauses carrying a subsumption record | **8** — m0216, m0217, m0218, m0220, m0221, m0222, m0322, m0355 |
| clauses changed with **no** subsumption record | **16** — m0219, m0321, m0323, m0354, m0356–m0367 |

The 16 are pure **section-channel spillover**. Per-channel deltas: the 8 record-carrying clauses move `{section: +0.0797/+0.0266, atom: +0.1771}`; the other 16 move `{section: +0.0266/+0.0797}` and nothing else. The mechanism is `relevance.py:703-711` — `section = 0.45 × mean(top-3 local scores in the clause's section)` — so **every** atom-channel gain lifts every co-sectional clause. An atom-channel-only prediction can never cover them.

On S5 this is inert (nothing flips). On the widening cycles, where flips are the point, §4 as written will book legitimate second-order effects as "unexplained flips" and block KEEPs. §4's F7 amendment anticipates exactly one section interaction (un-gating an atom-zero clause) and misses the ordinary one.

### ENG-B3 — §5.3's patient-composition contract is **false** under pricing 1.2, and S5 is the cycle that makes it false in practice

§5.3 states: *"licensed children are chain-free by construction, so every subsumption match is patient-FREE on the clause-atom side … a chained clause atom remains unreachable via the overlay."*

That was true at v1.1. Pricing 1.2 (S1, `containment.py:350-378`) dechains **every clause atom before the base index is built**, so a chained clause atom whose dechained form is a licensed child matches through the overlay normally. Demonstrated on one of S5's own 8 records:

```
clause m0355 carries only:  psychological_manipulation__developer_user  (kind: act)
idx.chains['m0355'] = {'psychological_manipulation': [['developer','user']]}
subsumption record:  query targeted_political_manipulation → clause_atom
                     psychological_manipulation, subsumer manipulation, credit 1.6812
```

The clause atom is chained; the overlay reaches it. Since this contract is what S3b's beneficiary-aware pricing is meant to compose against, freezing it as written propagates a false premise into the redesign that the program's only revert was called on.

### ENG-B4 — the design's factual state block is stale on load-bearing facts (§0, §0.5, §5.3)

Re-derived from disk:

| design claim | tree |
|---|---|
| "PRICING_VERSION 1.1" (§0) | `containment.PRICING_VERSION = "1.2"` (`containment.py:125`) — S5's snapshot will record 1.2, not 1.1 |
| "turn the existing **v1.1** edges ON" (§0.5) | measured: the built snapshot records `pricing_version: "1.2"` |
| "three KEEP cycles logged" (§0) | `cycles/CYCLE_LOG.jsonl` holds **6** closed cycles — 5 keep, **1 revert** |
| "the entire keep lineage … measured overlay-OFF" (§0.5) | **4 of 6** driver-era snapshots record `overlay: overlay_empty.json`. Only the *frozen cuts* are genuinely overlay-null (`thresholds_frozen.json` provenance: `"overlay": null`) |
| "once cycle 5 lands … the first admission cycle after cycle 5 lands" (§5.3) | cycle 5 (`patient-pricing-2026-08-04`) **REVERTED**; §5.3's entire premise is counterfactual |

Individually these are staleness; together they mean the document does not know which machine it is turning on. It is blocking because §0.5 is the whole S5 specification and two of its five substantive clauses are wrong.

## MAJOR

### ENG-M1 — the baseline is named statically, and misdescribed

§0.5 says S5 diffs "against the overlay-OFF baseline". `HANDOFF.md` ruling 2 is explicit: *"baseline = latest closed-KEEP spine snapshot, always read from the cycle log, never named statically in a design doc."* Taken literally, "overlay-OFF" points at `baseline-2026-08-04-auditv1` (overlay null, no `pricing_version`, and a **different** annotations sha) — a three-variable diff. **Mitigating, verified:** the two live candidates are score-identical (`snapshot.py diff patient-backfill-2026-08-04 → join-integrity-v2-2026-08-04` = *"no-op change"*), so the numbers do not move; but `manifest.baseline_snapshot_tag` still needs the right string, resolved from `CYCLE_LOG.jsonl`. (Residual ambiguity the design should settle: the last closed KEEP is P1's `join-integrity-v2`, which is not a *spine* snapshot.)

### ENG-M2 — no quality floor or leak ceiling covers the overlay path at all

`test_quality_floor.py` measures `relevance.RelevanceIndex` (`:111`), `structural.StructuralIndex` (`:125`), `section.SectionQuotient` and `combined.CombinedIndex` (`:316`) — all on `annotations_b8.json` + `behavior_atoms_b8.json` (`:61-63`). `containment` appears nowhere in the file. So the module carrying the *leak ceiling* argument (`CEILING_BAND = 0.075`, `:306`, the guard that caught a planted leak in `structural.predict`) does not watch the scoring path S5 switches on. The design declares no `gate_tests` at all. Pre-existing, but S5 is precisely the cycle that makes the unguarded path live.

### ENG-M3 — the ≥2-children license is never enforced on the configuration S5 scores

`containment.load_edges(path)` runs `_check_family_support` only when a `vocabulary` is passed (`containment.py:328-329`). `snapshot.py:184` and `:190` call it **without one**; so do `dossier.py:354/361` and (on the in-flight branch) `index_builder._apply_overlay`. The only place the check binds the real artifact is `test_containment.py:777-793`, against `_b8_vocabulary()` — the *superseded* corpus. I verified by hand that the current corpus passes (clause-side df: `psychological_manipulation` 1 raw / 2 dechained, `targeted_political_manipulation` 6; latent `manipulation` df = 8), so there is no live defect — but nothing checks it, and every family §3 admits inherits the gap.

### ENG-M4 — S5's measurement is not invariant to S4, which has not closed

§4 assumes the section evidence gate "landed at S4". `CYCLE_LOG.jsonl` has no S4 line. S4 changes the **section channel** — the channel carrying 16 of S5's 24 score deltas (ENG-B2). Running S5 before S4 is defensible, but the design must say which order it assumes and re-derive the expected effect if the order changes.

## MINOR

* **ENG-m1 — `depends_on` is not a manifest schema field.** §0.5 and §7.0 present it as a checkable manifest key. It is in neither `manifest_template` (`cycle.py:227-244`) nor `REQUIRED_MANIFEST_KEYS` (`:247-250`), and nothing validates it. The identical error was found and corrected in `SECTION_PRIOR_DESIGN` (S4 review ENG-m1). Same correction needed here.
* **ENG-m2 — §3.1 edits `containment.json` in place**, contradicting `REPRODUCIBILITY.md`'s versioned-filename corollary — a rule learned *from this exact file* ("the containment overlay was edited in place … `containment-v0` … is permanently un-dossierable"). Severity reduced because the A-side git reconstruction now exists.
* **ENG-m3 — the standing cut-stability gate is not applied to S5.** `ITERATION_LOOP.md` escalation (a): *"a cut-stability diagnostic gates any overlay widening."* The design imposes it on §7's widening cycles; S5 falls outside §7. Low impact: with `thresholds_frozen.json` asserted the cuts cannot move — verified.
* **ENG-m4 — "the audit_v1 configuration"** names only the atoms artifact; the annotations are `annotations_ext_v1_merged.json`. Name both, by sha.
* **ENG-m5 — the `index_builder.py` seam survives, with one ordering hazard.** The overlay axis dispatches on the resolved overlay path and still calls `containment.load_edges(paths["overlay"])` — S5's config-flip works identically. **But** that branch adds `verify_reconstruction.py` + `reconstruction_baseline.json`, which pins *every published snapshot's* replay at exact float equality. S5 publishes a new tag; whichever lands second must extend that baseline.

---

# SCIENCE

## BLOCKING

### SCI-B1 — the falsification bar is empty: S5 produces **zero flips**, measured

I built S5's snapshot (`snapshot.py snapshot --overlay containment.json --thresholds thresholds_frozen.json`) and diffed it against `join-integrity-v2-2026-08-04`:

```
# diff join-integrity-v2-2026-08-04 -> s5probe
inputs changed: overlay
avoiding-over-and-under-caution  (95 -> 95)   no flips
harm-avoidance-to-third-parties  (73 -> 73)   no flips
helpfulness                     (146 -> 146)  no flips
```

All 8 clauses that gain subsumption credit were **already** in the predicted set. The nearest non-predicted clause, m0357, sits at 0.1937 against a cut of 0.2365 — a 0.043 gap it does not close. The result is robust: forcing full-credit kind inheritance (2.5× the credit, see SCI-M1) still yields **0 flips**.

Consequences, each verified by running the machinery:

1. The diff is **not** a no-op (`diff_snapshots` requires identical config *and* identical scores; `snapshot.py:428-435`), so the driver does **not** short-circuit — it proceeds to ADJUDICATE with an empty dossier set.
2. `dossier.py dossiers` writes *"no flips … (empty index.jsonl written)"*; `dossier.py validate` against `{"records": []}` returns **`VERDICT clean`**, exit 0.
3. `_check_predictions_adjudicate` (`cycle.py:1046-1056`) then reads `regressions = 0` and records **PASS**.

So S5 can close KEEP with a clean validator, a passing prediction, and **zero adjudications** — while §0.5 says "keep/revert cites the flip adjudications only". There are none to cite. The gate every widening cycle waits on is, as designed, unfalsifiable.

This does not mean S5 is worthless — it means its real content is mechanism-level (8 priced records, 24 changed scores, a latent parent at df 8 / idf 4.203) and the design pre-registers none of it.

### SCI-B2 — no pre-registration is specified, including the one field the driver requires

`prediction.json` REQUIRES `max_regressions` (a non-negative int, `cycle.py:794-796`), checked at ADJUDICATE (`:1051-1055`). §0.5 specifies **no** prediction targets whatsoever. The design cannot be frozen at OPEN without an operator inventing them at the halt — the transcript-only procedure `REPRODUCIBILITY.md` classes as a review finding.

For the record: the design makes **no** false claim that `cycle.py` enforces revert on a bound. Verified `:1046-1056` records PASS/FAIL only, and `:1383-1392` merely refuses an *unjustified* decision. The revert remains the DECIDE signer's obligation. But a bound that is never stated cannot bind anyone.

## MAJOR

### SCI-M1 — kind inheritance, the feature the third containment cycle was KEPT for, is **inert** on the current corpus, and the design never notices

`_unanimous_child_kind` (`containment.py:426-449`) requires every licensed child to be attested under exactly one non-empty kind, all agreeing. Recomputed:

| corpus | `psychological_manipulation` | `targeted_political_manipulation` | inherited kind |
|---|---|---|---|
| `annotations_b8.json` | act ×2 | act ×6 | **`{'act'}`** — inheritance fires |
| `annotations_ext_v1_merged.json` (S5's corpus) | act ×2 | **situation ×6** | **`frozenset()`** — blocked |

The re-annotation reclassified one child from `act` to `situation`, so `manipulation` inherits nothing and **every** subsumption match pays the mismatch discount (credit 4.2030 × 0.4 = **1.6812**, confirmed on all 8 records). §5.1 asserts the mechanism and §2.2 makes a kind-inheritance statement mandatory for every *future* family — but S5, which reactivates the only existing one, gets no such statement. Whether `targeted_political_manipulation` is a situation or an act is a genuine document-side question on which the overlay's pricing turns, and it is exactly the sort of thing S5 could adjudicate instead of nothing.

### SCI-M2 — the flip-budget calibration in §3.1 is refuted on the current corpus

§3.1 grounds "one family per cycle" in *"the cycle-1 experience (7 flips for a 2-edge family)"*. Cycle 1 measured 7 flips over the **b8** corpus. The same 2 edges on the current corpus give **0**. The conclusion (one family per cycle) is still the conservative choice and I would keep it — but its stated grounds are false, and the design should not carry a refuted number into the freeze.

### SCI-M3 — fireability is a poor proxy for falsifiability, and §6's stopping rule inherits the flaw

§1.2 makes "fireability" — new (query_atom, clause) pairs — the primary sort, justified as *"the size of the family's testable claim."* S5 is the counter-example: **8 fireable pairs, 0 flips, 0 adjudications, nothing learned.** §6's stopping rule 1 is denominated in the same unit ("< 2 new pairs each"), so the procedure can keep admitting families that connect pairs while never producing a single adjudicable flip — burning cycles and budget on unfalsifiable admissions and then halting on a criterion that never noticed. What needs adding is a *flip-capable* screen — does the family's credit move any clause across its frozen cut — before a family consumes a cycle.

### SCI-M4 — could this be fitted to labels? Mostly no, with one honest residual

The label-free discipline holds where it is hardest: the order is a pure function of document- and query-side artifacts (§1.2), the "admit the family that moves MCC most" temptation is rejected **by name**, the census is confined to declared checkpoints and can only *stop* widening (§6.3), and `containment.json`'s provenance block records that the manipulation family was label-*directed* and label-*independent* in content. The residual: §0's evidence base is a census read (19 dossiers), and §1.2's tertiary tiebreak plus §3.4's ceiling (8 families / 32 edges) are operator choices with no document-side derivation. Neither is a scoring-path literal, so `REPRODUCIBILITY.md`'s new-constant rule does not bite — but they should be labelled as governance choices rather than derived quantities.

## MINOR

* **SCI-m1 — §2.4's worked example is directionally right but should be re-derived.** The claim that a fully admitted `information` family "addresses at most ~4 of its 9 census cases" rests on which adjacent atoms are principal-chained. Under pricing 1.2 the clause side is **dechained before matching**, so the chain-based unreachability argument no longer holds as §2.4 states it (same root cause as ENG-B3). The conclusion may survive on polarity grounds (polarity is *not* stripped) but the reasoning as written is stale.
* **SCI-m2 — §0.5's "census deferred to checkpoint"** is correct and matches amendment F1 and the driver's own default (`cycle.py:672-673`). No finding; noted because the design states it as a choice when it is the driver's behaviour for `shape: code`.

---

# WHAT HOLDS (verified, not assumed)

* **The edge set is the one the design thinks it is.** `containment.load_edges('containment.json')` accepts exactly 2 edges under the shipped `shared_head` license: `psychological_manipulation → manipulation` and `targeted_political_manipulation → manipulation`. One latent family; `manipulation` is not itself a vocabulary atom (latent path). Both children are present in the current clause vocabulary. §0's `{max_edges: 4, max_families: 2}`, "2 edges, 1 family (manipulation)" — all confirmed byte-for-byte.
* **The census numbers reproduce exactly.** `verdicts_merged.json` (294 records): `fn_names_cannot_meet` = **19** ✓, `fp_promiscuous_atom` = **155** ✓. All nine dossier names §0 attributes to the `information` head appear in that class.
* **The F3 handling is right.** Declaring the 53 dead rather than "to be reconciled", shipping the enumerator as a committed sha-pinned script, and freezing its output before anything admits, is the correct shape — as is recording the singular/plural license limitation instead of picking the flattering count.
* **§2.3's floor check matches the code.** `cutoff = weights.atom_stopword_frac × n_docs` = 0.25 × 589 = 147.25, and `subsumer_idf = 0.0 if df > cutoff` (`containment.py:392-402`). A floored parent genuinely cannot contribute.
* **§5.2's pricing claims match the code.** `min(idf(subsumer), idf(clause_atom)) × kind_factor` with the never-outprice cap is `_best_subsumption` (`containment.py:513`) verbatim; the one-credit-per-query-atom and one-credit-per-clause-atom matching rules are `_subsumption_matches` (`:522-565`).
* **The F9 reconstruction story is intact.** S5 changes no scoring code, so every pre-S5 snapshot rebuilds through the recorded `overlay`/`pricing_version` dispatch exactly as before. The `overlay` key is already the natural `compatibility.version_key` for S5.
* **The mechanism is total on the zero-flip path** — run end to end: non-noop diff → empty `index.jsonl` → `dossier.py validate` clean, exit 0. That it *also* lets a cycle close on no evidence is SCI-B1, not a totality defect.
* **No new sweepable numeric constant enters a scoring path.**
* **No false enforcement claim** about `cycle.py`.

---

# SHORTEST PATH TO READY-FOR-OPEN

1. **Make S5 openable, in writing.** Specify `shape: code`; `files_to_change: ["test_containment.py"]` — adding the pin that `containment.json` loads under the **current** vocabulary, which is a real change, closes ENG-M3, and is a *stronger* pin; `gate_tests: ["test_containment.py", "test_snapshot.py", "test_no_reference_leak.py"]`; `compatibility: {version_key: "overlay", statement: "…the old behaviour remains reachable by pointing config.overlay at overlay_empty.json; no scoring code changes, so every pre-S5 snapshot reconstructs unchanged"}`; and `baseline_snapshot_tag` resolved from `cycles/CYCLE_LOG.jsonl`. Demote `depends_on` to prose.
2. **Pre-register S5 honestly, at mechanism level.** `expected_flip_count: {min: 0, max: 0}`, `expected_directions: []` (the driver explicitly licenses this — `cycle.py:777-786`), `max_regressions: 0`, plus a *mechanism* pre-registration the cycle can actually fail: **8 subsumption records on exactly {m0216, m0217, m0218, m0220, m0221, m0222, m0322, m0355}, all `harm-avoidance-to-third-parties`, each priced 1.6812 at `kind_factor 0.4`; latent `manipulation` at df 8 / idf 4.2030; 24 clauses changing score, of which 16 change through the section channel only.** Carry the built-before-OPEN disclosure into both the prediction notes and the decision justification.
3. **Fix §4's expected-effect statement** to be two-part: the atom-channel subsumption diff **plus** the induced section-channel delta over each affected section's members. Add `section_spillover` alongside `section_gate_reactivation` as a permitted, adjudicable flip tag.
4. **Rewrite §5.3.** Under pricing 1.2 a chained clause atom **is** reachable via the overlay (proven on m0355); state the real composition contract for S3b rather than the v1.1-era one.
5. **Refresh §0/§0.5/§5.3 against the tree:** PRICING_VERSION 1.2; 6 closed cycles (5 keep, 1 revert); "overlay-OFF" true of the frozen cuts only; cycle 5 **reverted**, so §5.3 becomes conditional on S3b. Drop or re-ground the "7 flips for a 2-edge family" calibration.
6. **Add a flip-capability screen to §2 and a kind statement to S5.** Before a family consumes a cycle, compute whether its credit moves any clause across its frozen cut; a family that cannot is recorded `inert` and skipped. And give S5 the §2.2 kind-inheritance statement its successors are required to produce — which would surface, pre-registered, that inheritance is currently **blocked** by the act/situation split on `targeted_political_manipulation`.

Items 1–4 are the blocking set. Item 5 is bookkeeping but touches the only paragraph that defines S5. Item 6 is what would turn S5 from a rubber stamp into a cycle worth running.
