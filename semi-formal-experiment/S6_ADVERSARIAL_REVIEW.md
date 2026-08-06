# S6 ADVERSARIAL REVIEW — `VOCAB_GAPS_DESIGN.md`

**Artifact:** `semi-formal-experiment/VOCAB_GAPS_DESIGN.md` (dated 2026-08-04) — the S6 vocabulary-additions cycle and its S6b re-selection follow-on
**Review date:** 2026-08-05 · clean-context, Tier-1 decision-point · read-only, no `cycle.py` run, no network
**Reviewer standard:** every count recomputed from artifacts on disk; every code citation opened and read.

---

## VERDICT: **REVISE**

Four blocking findings, nine major, seven minor. The design absorbs the PORTFOLIO F8 amendments faithfully and its census arithmetic is exactly right — but it fails on the axis it was warned about. Its central Shape-A/Shape-B gate, the thing that is supposed to stop the census from being laundered into the vocabulary, **cannot be enforced by any mechanism the design specifies**, and a mechanical recomputation puts 14 of the 26 target dossiers on the side the design says it must not touch. Separately, its flip-surface accounting — the honest-flip-surface paragraph added *by* F8 — omits the single heaviest channel in the scorer.

| dimension | BLOCKING | MAJOR | MINOR |
|---|---:|---:|---:|
| ENGINEERING | 2 | 4 | 4 |
| SCIENCE | 2 | 5 | 3 |
| **total** | **4** | **9** | **7** |

---

## SCIENCE — BLOCKING

### B1. The Shape-A / Shape-B gate is unenforceable, and a mechanical reading inverts it for 15 of 26 clauses

§2 draws the load-bearing distinction:

> **Shape A** — the concept is atomized NOWHERE … Fix = add clause-side atoms.
> **Shape B** — the concept exists clause-side but the query cannot meet it … **This design MUST NOT add duplicate atoms for Shape-B concepts; the worksheet validator enforces reuse-first (§3.3).**

Two independent failures.

**(a) The claimed enforcement does not exist.** §3.3's reuse-first rule fires only when `stem_of(name)` equals an existing vocabulary stem. That catches a coined *near-duplicate of a name*. It cannot catch a Shape-B *concept*, because Shape-B-ness is a fact about the relation between a clause's existing atoms and a **behaviour's query vocabulary** — and §3.1 deliberately blinds the seat to exactly that: the worksheet "MUST NOT carry: behaviour names, panel scores, dossier fields." The seat is structurally incapable of applying the distinction, and the validator has no input from which to compute it. The only thing that applies Shape A/B is the designer's §1 family assignment, which is prose, is not reproducible from the artifacts, and is not re-derived at any gate.

**(b) The assignment does not survive recomputation.** Under the live join key — `containment.dechain_name` (strips the principal chain, **preserves polarity**; `containment.py:141`, applied at `:546`, `:579`) — against `annotations_ext_v1_merged.json` and `behavior_atoms_audit_v1.json`:

**14 of the 26 dossiers already carry a clause-side atom whose join key is a member of another DEV behaviour's query vocabulary** — i.e. the concept is coined *and already judged query-worthy somewhere*, so §2's own Shape-B remedy (the `select_audit` sweep, whose rosters carry the full vocabulary) can repair them with **zero annotation edits**:

| clause | dossier behaviour | atom already in another query |
|---|---|---|
| m0170 | helpfulness | `positive_user_intent` (caution) |
| m0322 | caution | `psychological_manipulation` (harm) |
| m0236 | harm | `may_provide_critical_factual_discussion` (caution) |
| m0238 / m0244 / m0245 / m0246 / m0215 / m0207 | harm | `should_redirect_to_applicable_help` (helpfulness) |
| m0198 / m0203 / m0205 / m0255 | harm | `shouldnot_generate_disallowed_content` (caution) |
| m0528 | harm | `neutral_refusal`, `judgmental_refusal`, `offer_safe_alternative` (caution + helpfulness) |

The design assigns **9 of these 14** to Shape A (families 1, 2, 6, 9 → "add clause-side atoms"). Symmetrically, 6 clauses the design books to Shape B (m0015, m0030, m0096, m0202, m0253, m0303) carry no atom present in *any* query — they are the genuine Shape-A cases. **15 of 26 are classified against the direction the artifacts support.** m0528 is the sharpest case: it is a *harm* dossier, and `neutral_refusal` / `judgmental_refusal` sit in the caution query already. The design books it to families 1 *and* 9, both Shape A. Adding `judgmental_refusal` to m0528 is precisely the duplicate §2 forbids.

*Honest caveat on my criterion:* "present in another behaviour's query" is a **lower bound** on Shape B, not a full test — it does not detect a concept coined in the vocabulary but selected into no query. That makes the finding conservative: the true Shape-B count is ≥14.

**(c) The order of operations is backwards.** §6 runs S6 (additions) first and S6b (re-selection) last. For these 14 the cheap, zero-annotation, zero-new-vocabulary fix is never given the chance to show it was sufficient; instead new atoms land first and their flips are attributed to the additions. Running **S6b before S6** is a free negative control that costs nothing but ordering, and would shrink the additions worklist to the clauses that actually need it.

**Fix:** compute the Shape-A/Shape-B partition mechanically, from the artifacts, as a committed script whose output is frozen at OPEN (the F3 precedent: "ship the enumerator as a committed script; freeze its output; nothing admits until then"). Run S6b first. Restrict S6's frozen clause list to the computed Shape-A residue.

### B2 → see ENGINEERING (the lexical channel)

Listed there; it is also a falsifiability failure, since §5.2's prediction is stated over a channel the additions do not confine themselves to.

### B3. The design's "predictions" are not in the PREDICT schema's vocabulary, and `max_regressions` is absent entirely

`cycle.py` freezes a typed prediction. Its required fields, verified: `expected_flip_count {min,max}` (`:769-785`), `expected_directions` (`:1032`), `expected_clauses` (`:1038`), and — validated at `:794-796` (`"max_regressions must be a non-negative int"`) and consumed with a **hard subscript** at `:1052` and `:1054` — `max_regressions`.

The word `max_regressions` **does not appear anywhere in `VOCAB_GAPS_DESIGN.md`**. Neither does `expected_flip_count`, `expected_directions`, or `expected_clauses`. What the design offers instead:

- §5.2 "additions can only raise span recall on m0242" — a golden-span statement, not a flip target;
- §5.3 "at least the Shape-A families … yield score-3 verdicts" — checked in S6b, not S6, and unfalsifiable given B1;
- §5.5 "≥ the Shape-A subset (≈14 dossiers) resolved at checkpoint" — a **census-class** target, deferred to S8.

So the cycle that is the highest fitting risk on the board arrives with **no document-side, mechanism-level, pre-registered bound of the kind that produced this program's one revert**. The S3 revert happened because `max_regressions: 0` was frozen and 5 regressions landed. S6 as designed has no such number.

To this design's credit — and I checked, because a prior review caught a false claim of exactly this shape — **the design does not falsely claim `cycle.py` enforces revert.** It doesn't mention the mechanism at all. For the record, verified: `_check_predictions_adjudicate` (`cycle.py:1046-1058`) only *records* `PASS`/`FAIL`; `_decide` (`:1380-1392`) refuses an unjustified decision when `any_fail or state["overrides"]`, and `DECISION_VALUES` is otherwise unconstrained. The revert is the signer's obligation, not the driver's.

**Fix:** state `max_regressions` with a **document-side** defence. The defensible value here is **0**, on the same grounds as S3: an addition that removes a clause an auditor needs is a regression the mechanism cannot justify, and additions are supposed to be monotone in coverage. Add `expected_flip_count`, `expected_directions` (both, per §2b's own admission), and `expected_clauses`.

### B4 → see ENGINEERING (no annotation cycle shape)

---

## ENGINEERING — BLOCKING

### B2. The flip-surface accounting omits the lexical channel — the heaviest channel in the scorer

§2(b), the paragraph F8 required in order to state the flip surface "honestly", names exactly three propagation mechanisms: atom df/idf, section top-k means, corpus-max normalizer. Verified all three are real (`relevance.py:546-556`, `:703-711`, `:772-783`).

It omits a fourth, and it is the largest. `relevance.py:558`:

```python
docs = {cid: _counts(f"{c.get('quote', '')} {_atom_text(self._atoms[cid])}")
        for cid, c in zip(self.ids, self.clauses)}
```

with `_atom_text` (`:298-299`) = `" ".join(f"{a['name']} {a['gloss']}" for a in atoms)`. **Atom names and their free-text glosses are part of the lexical document.** From those `docs` come the corpus-wide lexical `idf` (`:561-565`), the per-clause `vectors` (`:566`), and the Rocchio pseudo-relevance query expansion (`_query_vector`, `:600-622`, `expansion_docs=12`, `expansion_terms=25`) which re-derives *every behaviour's* expanded query vocabulary from those vectors.

Measured on the live artifact:

```
mean tokens from clause QUOTE     : 41.0
mean tokens from ATOM name+gloss  : 23.6   → 36.5% of the lexical document
mean atoms/clause (corpus)        : 2.43
mean atoms/clause (the 26 targets): 2.65
```

And `Weights.lex = 1.0` (`relevance.py:465`) against `atom = 0.6` and `section = 0.45` — **lex is the heaviest channel.** §3.3's per-clause cap of 4 additions would let a target clause go from 2.65 atoms to 6.65, roughly **tripling** its atom-text mass in a channel that is already 36.5% atom-derived and weighted 1.0.

Three consequences the design does not see:

1. The additions move the target clauses' `lex` scores directly — so §5.2's prediction ("additions can only raise span recall") is stated over a surface the change does not confine itself to.
2. New gloss tokens change the **corpus-wide** lexical `idf`, shifting `lex` on unrelated clauses sharing those stems.
3. Changed clause vectors can change which 12 clauses form the Rocchio pseudo-relevance set, altering the expanded query vector for **every** behaviour.

Worst of all, the design places **no constraint on gloss content**. §3.3 constrains `name` (grammar round-trip), `kind` (four-way), `quote` (verbatim substring — a genuinely good fence), and `reuse`. `gloss` is free prose from a small-model seat, and it is the field with the most direct line into the heaviest channel. §3.4's gloss review covers **coined atoms only** — a `reuse: true` proposal ships a new, unreviewed gloss straight into `lex`.

**Fix:** name the lexical/expansion channel in §2(b); constrain `gloss` in §3.3 (length bound, and — the clean option — require the gloss to be drawn from or bounded by the licensed `quote` span, since the quote is already in `docs`); extend §3.4 gloss review to reuses.

*What I checked and did **not** find:* a colleague analysis flagged `self._atom_norm = max(self.atom_idf.values())` (`:556`, consumed `:648` and `containment.py:587`) as a fourth global normalizer that additions would move. **It is inert.** Computed: `_atom_norm = 5.695414…` = exactly `log(1 + 593/2)`, the df=1 value, and **397 of 688 atoms already sit at df=1**. A new df=1 atom cannot raise it; no plausible df increase can lower it. I am not raising this as a finding.

### B4. No cycle shape exists for what S6 is, and `shape: code` will refuse this manifest

`CYCLE_DESIGN.md` § Scope: "v1 supports one cycle shape: a code/matching fix. Extension points marked for **annotation-cycle and selection-cycle variants**." Verified in the driver: `cycle.py:604-607` rejects any shape not in `PHASES_BY_SHAPE` with the message `"(EXTENSION POINT (v2): annotation/selection shapes)"`, and `:102` marks the same hole. **S6 is the annotation cycle and S6b is the selection cycle** — neither shape exists.

Forced into `shape: code`, `_open` imposes (`:618-630`):

```python
if shape == "code":
    if not m["files_to_change"]: problems.append(...)
    compat = m.get("compatibility") or {}
    if not (str(compat.get("version_key","")).strip()
            and str(compat.get("statement","")).strip()):
        problems.append("compatibility.version_key / compatibility.statement required … (amendment F9)")
```

The design supplies neither, and never mentions F9. This is not fatal — the precedent exists and works: `cycles/chain-repair-2026-08-04` and `cycles/patient-backfill-2026-08-04` both used `version_key: "annotations"` with an artifact-identity statement, exactly the pattern S6 needs. But the design must say so, because the F9 answer is non-obvious for an artifact-content change and the operator will hit the refusal cold.

Note also `:661`: `closure = set(m["gate_tests"]) | {cfg["annotations"], cfg["atoms"]}`, minus `files_to_change`. The annotations artifact is **closure-pinned by default** — S6 must declare it in `files_to_change` or the IMPLEMENT gate refuses on a changed closure input. Unstated.

**Credit where due:** §4's `add` migration entry, shape `{"artifacts": {<path>: {sha_before, sha_after, n_added}}}`, is **exactly** the shape `dossier._migration_span` (`dossier.py:98-124`) requires to license reconstruction of a sha-mismatched input (`e["artifacts"][rel]["sha_before"]` chaining to `sha_after`, ending at the disk sha). Combined with `_git_bytes_matching` (`:127`, now repaired), **pre-S6 snapshots do reconstruct** and the `containment-v0` disaster does not recur. The design got the hard part right; it just never states that this is the F9 answer.

**Fix:** declare `shape: code`, `compatibility.version_key: "annotations"` with the chain-repair-pattern statement, `files_to_change` including the annotations artifact + `vocabulary_migrations.json` + `atom_refactor.py`, and note the §4 replay contract *as* the F9 reconstruction argument.

---

## SCIENCE — MAJOR

### M1. The S4 unlock cliff is not inherited, and every atom S6 adds is by construction the exact key that opens it

`SECTION_PRIOR_DESIGN.md:424-439`, added by S4's own adversarial review, names an incentive **explicitly for S6 to inherit**:

> A1 keys the full 0.45 propagation on EXACTLY-zero atom evidence: any nonzero atom credit, however weak, unlocks the entire section prior. The cheapest gaming route is blocked by construction — stopword atoms are floored to idf 0.0 … but **a rare atom with small positive idf can**. … the INCENTIVE it creates is named here for S6/S7 to inherit: **vocabulary additions can buy section credit for a clause one ε-match at a time.**

Every atom S6 coins is, by construction, df=1 — i.e. carries the **maximum** atom idf (5.6954, verified above), not a small one. S4 lands *before* S6 in the spine. S6 is therefore the first cycle able to hand a gated clause its entire 0.45 section prior for one new atom — and `VOCAB_GAPS_DESIGN.md` mentions neither S4, nor the gate, nor the unlock, nor any negative control against it. S4's own text notes the unlock side **generates no flips** ("unchanged scores are never adjudicated"), so S6's flip adjudication is structurally blind to it.

**Fix:** inherit the disclosure by name; pre-register the count of currently-gated clauses among the frozen list and report post-add how many unlocked, as a reported (not gating) mechanism number.

### M2. The proposal step is fenced only for the seat, and there is a re-run channel

The seat is well fenced (blind to behaviour, no panel numbers, verbatim-quote license). But §1 of this very design **pre-names the target atoms** — `hateful_content`, `protected_group`, `extremist_content`, `user_provided_content`, `content_transformation_request` — all read off the census. And §3.3 provides a re-run channel: "per-clause addition cap of 4 — a seat proposing more is miscalibrated; **refuse the file, re-run the seat**."

A coordinator who has read §1 knows which names the census wants, and holds a documented lever to re-run the seat. Nothing in the design forbids re-running after inspecting content, bounds the number of re-runs, or requires the re-run to be recorded. That is a live fitting channel — precisely the shape of the disclosed `Weights` violation (`relevance.py:434-464`: *"TWO constants were selected by reading results off the panel … Disclosure is not compliance"*).

**Fix:** re-run is licensed **only** by a mechanical validator failure, the failure reason is recorded, re-runs are capped and logged, and — the cheap strong version — the seat runs **once** with over-budget files truncated by the validator's own rule rather than re-solicited.

### M3. The fallback trigger is unmeasurable — the verdict schema has no channel for it

§2(b): "Fallback trigger, **falsifiable**: if the seat pass finds ≥3 clauses whose EXISTING atoms it flags as wrong (not merely incomplete), those clauses escalate to option (a)."

§3.3's verdict schema is additions-only: `{name, kind, gloss, quote, reuse}`. There is **no field in which a seat can flag an existing atom as wrong**, and §3.2's brief instructs the seat only to "List every concept this clause's text asserts that has no covering atom." The trigger can never fire. A falsifiable-labelled condition that is mechanically unreachable is worse than none.

### M5. The "≈14 Shape-A dossiers" success criterion is not well-defined

§2 defines Shape A as "families 1, 2, 4, **6 in part**, **9 in part**". "In part" is never resolved. Computed: families 1∪2∪4∪6∪9 = exactly **14** clauses — but reaching 14 requires taking families 6 and 9 *whole* (contradicting "in part") **and** including m0253/m0255, which §2 simultaneously books to Shape B (family 3/4 overlap) and forbids adding atoms for. The only arithmetic that yields the pre-stated target counts two clauses the design says it must not fix. Combined with B1, §5.5's success criterion is not falsifiable as written.

### M7. The cost line is materially incomplete against a budget flagged as the program's main risk

§6: "$0 until step 3; steps 3+8 are small-model seat runs; nothing touches the panel at any step."

Uncosted: (i) §3.4's gloss review, a separate blinded seat; (ii) **S6b's sweep**, which per `select_audit.build_rosters` scores the **FULL vocabulary — 688 atoms — against each behaviour definition**, the largest single seat run in the portfolio; (iii) per-family S6 cycles, each carrying its own full flip adjudication (§5.4), multiplying against `PORTFOLIO_REVIEW` F11's aggregate budget of ~90–130 adjudications across the whole 8–10-cycle spine. `AGENTS.md` records an $8.50 ceiling with ~$2.15 used, and `HANDOFF.md` names budget as "the main risk". Step 8 in §6 is the *flip adjudication*, not the gloss review — the design's own numbering conceals two of the three seat costs.

---

## ENGINEERING — MAJOR

### M4. Three of the 26 frozen clauses belong to no family, so per-family batching drops them

§1 claims the 26 dossiers "cluster into nine families." Recomputed from §1's own membership lists: the nine families name **23 distinct clauses**. **m0215, m0270, m0273 appear in no family.** Since §5.4 and §6.6 batch the work *per family* ("Apply as one migration entry per family batch"; ">30 flips ⇒ split the batch by family"), these three have no batch and would silently fall out of a worklist §3.1 declares frozen and coverage-checked. (Their atoms — `user_requests_prohibited_content`, `user_requests_illicit_help`, `should_refuse_prohibited_help`, `should_redirect_to_applicable_help` — are, tellingly, the cleanest Shape-B/re-selection cases in the set; see B1.)

### M6. The baseline is never resolved, and the standing rule is not stated

`HANDOFF.md` ruling 2 is explicit and general: *"baseline = latest closed-KEEP spine snapshot, always read from the cycle log, never named statically in a design doc"* — a rule written **because** `SECTION_PRIOR_DESIGN.md` named one statically and went stale. `VOCAB_GAPS_DESIGN.md` names no baseline at all and does not state the rule; §5.4 says only "against its own baseline" and §5.3 "measured against the additions' keep snapshot."

Verified from `cycles/CYCLE_LOG.jsonl`, the latest closed-KEEP is `join-integrity-v2-2026-08-04` — but S4 and S5 land before S6, so any baseline named today is wrong by construction. **The design must state the rule, not a tag.**

### M8. Registration is omitted — `AGENTS.md`: "Registration, not documentation, fences a module. Same diff, every time."

The design creates `vocab_gap_worksheet.py` and (implicitly) `test_vocab_gap_worksheet.py`, and never mentions `conftest._OPTIONAL`. The precedent is directly adjacent: `"test_backfill_worksheet.py": "backfill_worksheet"` is registered there. A companion concern for S6b: `select_audit.py` sits in `conftest._OPTIONAL` but **not** in `test_no_reference_leak.QUERY_MODULES`. That is defensible while it is "DIAGNOSTIC-ONLY" (its module docstring); S6b makes its output **decision-bearing on the query itself**, which is the QUERY_MODULES trigger.

### M9. The gloss review has no brief — transcript-only procedure, which `REPRODUCIBILITY.md` classes as a review finding

§3.4: "Every COINED atom … gets a blinded gloss review **under the `briefs/golden_review.md` pattern**." A *pattern* is not a brief. `REPRODUCIBILITY.md` sandwich-rule leg 4 requires "An instruction file IN THE REPO", and the same document lists three violations of this exact class as resolved debt. Compounding: `briefs/golden_review.md` is, per `REPRODUCIBILITY.md` §2, "explicitly a human/frontier-model seat", while §6 costs everything as "small-model seat runs" — a tier mismatch on the **only content fence** standing between a seat's free-text gloss and the heaviest scoring channel (B2). And reuses skip this review entirely while still shipping a gloss.

---

## MINOR

- **m1 (ENG).** §1 renders atom names with principal chains silently stripped. m0242's only atom is `mustnot_generate_disallowed_content__model_third_party`, not `mustnot_generate_disallowed_content`; m0015's is `mustnot_facilitate_human_disempowerment__model_third_party`. Imprecise in exactly the dimension §3.3 legislates about (the no-coined-chains rule).
- **m2 (ENG).** §1 family 2: m0236 "carries only generic disallowed-content atoms." It carries three: `mustnot_generate_disallowed_content`, `sensitive_content_appropriate_context`, `may_provide_critical_factual_discussion` — the last of which is in the caution query.
- **m3 (ENG).** The stopword mechanism is **dead**: `atom_stopword_frac = 0.25` × 593 clauses = cutoff **148.25**, live max `atom_df` = **17** (688 distinct atoms). Zero atoms are ever stopworded — an 8.7× margin, which no plausible S6 addition narrows. Worth stating because S4's SCI-m2 mitigation leans on the stopword floor. Note the `Weights` docstring's own self-description of this (`relevance.py:456-463`) cites **stale b8 numbers** (361 names, max df 43); the live headline artifact is 688 / 17.
- **m4 (ENG).** `select_audit.py:36` defaults `BEHAVIOUR_ATOMS = "behavior_atoms_ext_v1.json"`, a superseded artifact — every cycle manifest on disk uses `behavior_atoms_audit_v1.json`. S6b must pass it explicitly or inherit the wrong roster.
- **m5 (SCI).** `D5_WORKED_EXAMPLES.md` books ~30 FP cases ("no party at all — the clause is about answer quality") to "query-atom curation / structural role (**S6, S6b**)". This design's scope is the 26-dossier FN class only and does not acknowledge the ~30. Unowned work. (D5 postdates this design by a day; a scope note resolves it.)
- **m6 (ENG).** §2(b) says the worksheet carries "the CURRENT full vocabulary index for reuse"; §3.1 says each row carries clause id, text, existing atoms "**and nothing else**." Contradictory, and material — reuse-first is unimplementable without the index.
- **m7 (SCI).** §4's "m0236 (split: held_out)" is correct as a *golden-clause* label, but the m0236 **dossier's cell** (harm-avoidance-to-third-parties) is DEV. Both splits are live and a careless reader will conflate them; state the distinction.

---

## WHAT HOLDS — verified correct

Recomputed independently from disk, not taken on the design's word:

1. **The census arithmetic is exact.** `audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json` holds 294 dossiers; **exactly 26** carry `cause == "fn_family_absent_from_vocabulary"`; their clause set matches §0's 26-clause list with **empty set difference in both directions**; the mapping is strictly **1:1** (no clause repeats across behaviours). Full cause distribution: `fp_promiscuous_atom` 155, `fp_threshold_drift` 59, `fp_section_prior` 30, **`fn_family_absent_from_vocabulary` 26**, `fn_names_cannot_meet` 19, `fp_join_artifact` 2, `unexplained_escalate` 2, `fn_threshold` 1 = 294.
2. **The golden claim is exact.** Of the 26, exactly two are golden entries: **m0242 (dev)** and **m0236 (held_out)** — verbatim as §4 states. All 26 dossiers live in DEV cells; no held-out cell is touched.
3. **The F8 amendments are absorbed faithfully, not cosmetically.** S6/S6b split into separate cycles with S6b baselined on S6's keep; the coined-chain ban with a correct rationale (chain-authoring is the backfill's fenced job); the flip surface restated over the whole corpus with "**Flips can land on clauses the batch never touched**" — three of the four propagation mechanisms verified real.
4. **Binding amendment F1 is honoured.** §5.5 reads the FN class "at checkpoints only … never steered on per-batch." The census stays out of the per-cycle path.
5. **The `add` migration entry is correctly shaped for reconstruction.** Its `{"artifacts": {path: {sha_before, sha_after}}}` form is exactly what `dossier._migration_span` (`dossier.py:98-124`) needs to license a sha-mismatched input, so **pre-S6 snapshots reconstruct** and the `containment-v0` in-place-edit failure does not recur. The idempotency rule ("already present under the same (clause_id, name, kind) is a replay error, not a silent skip") is the right call.
6. **The verbatim-quote span license is the right instrument** — mechanically checked, enforced not promised, and the one fence in the design that genuinely converts "licensed by the document" from a claim into a validator.
7. **Seat blinding is correctly specified:** no behaviour names, no panel scores, no dossier fields, no census cause strings; the seat never learns why a clause was selected.
8. **§2(a)'s rejection of re-annotation is sound and correctly reasoned** — the prompt-hint leak, the unbounded adds+drops+renames flip surface, and the migration-log's inability to express wholesale replacement are all real and correctly identified.
9. **No false claim about `cycle.py` enforcing revert.** Verified `:1046-1058` (records PASS/FAIL only) and `:1380-1392` (refuses an unjustified decision; does not decide). The design makes no claim here.
10. **`_atom_norm` is not a hazard.** Verified saturated at the df=1 idf with 397 atoms already there; additions cannot move it. The design's omission of it is harmless.

---

## THE SHORTEST PATH TO READY-FOR-OPEN

1. **Compute the Shape-A/Shape-B partition mechanically** as a committed script; freeze its output at OPEN; restrict S6's clause list to the computed Shape-A residue. **Run S6b before S6** as the zero-annotation control. *(B1, M4, M5)*
2. **Name the lexical/expansion channel** in §2(b), and **constrain `gloss`** in §3.3 — bounded by the licensed quote span — with §3.4 gloss review extended to reuses. *(B2, M9)*
3. **Write the PREDICT block:** `max_regressions: 0` defended from document-side grounds (the S3 precedent), plus `expected_flip_count`, `expected_directions` (both), `expected_clauses`. *(B3)*
4. **Add the manifest section:** `shape: code`, `compatibility.version_key: "annotations"` with the chain-repair statement, `files_to_change` (annotations artifact, `vocabulary_migrations.json`, `atom_refactor.py`), and note §4's replay contract *as* the F9 argument. State the baseline rule ("latest closed-KEEP spine snapshot, read from `cycles/CYCLE_LOG.jsonl`"), never a tag. *(B4, M6)*
5. **Inherit S4's unlock-cliff disclosure by name**, with a pre-registered count of currently-gated clauses among the frozen list, reported post-add. *(M1)*
6. **Close the two seat channels:** re-runs licensed only by mechanical validator failure, capped and recorded; and give the seat a schema field for "existing atom is wrong" so §2(b)'s fallback trigger can actually fire. *(M2, M3)*
7. **Write `briefs/vocab_gap_seat.md` and `briefs/vocab_gap_gloss_review.md`** as repo artifacts with declared model tiers; register `test_vocab_gap_worksheet.py` in `conftest._OPTIONAL`; re-cost §6 to include gloss review, the 688-atom S6b sweep, and per-family adjudications against the $8.50 ceiling. *(M7, M8, M9)*
8. Fix the minors: chain-accurate atom renderings in §1, the §2(b)/§3.1 worksheet-contents contradiction, the `select_audit` default artifact, the DEV-cell vs golden-split note, and a scope line on D5 §6's ~30 unowned FP cases.

---

*Reviewed against `AGENTS.md`, `HANDOFF.md` ⭐⭐⭐/⭐⭐, `CYCLE_DESIGN.md` (BINDING AMENDMENTS / PRE-BUILT CYCLES / CEREMONY MECHANICS), `ITERATION_LOOP.md`, `REPRODUCIBILITY.md`, `MODULE_MAP.md`, `PORTFOLIO_REVIEW.md`, `SECTION_PRIOR_DESIGN.md`, `D5_WORKED_EXAMPLES.md`, and the live tree (`relevance.py`, `containment.py`, `snapshot.py`, `dossier.py`, `cycle.py`, `atom_refactor.py`, `select_audit.py`, `test_no_reference_leak.py`, `conftest.py`). No repo file was modified; `cycle.py` was not run; no network or paid calls were made.*
