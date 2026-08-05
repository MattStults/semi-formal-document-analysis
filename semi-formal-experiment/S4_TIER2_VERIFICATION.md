# S4_TIER2_VERIFICATION — tier-2 verification pass over the revised SECTION_PRIOR_DESIGN.md (2026-08-05)

Scope: verify that EACH finding in `S4_ADVERSARIAL_REVIEW.md` (verdict REVISE: 1 blocking,
4 majors, 5 minors) is correctly fixed in the revision of `SECTION_PRIOR_DESIGN.md`, plus a
light internal-consistency check. Design-doc verification only — no code changes, no git, no
test runs. The only file reads beyond the two documents were three cross-reference existence
checks (`PORTFOLIO_REVIEW.md` F13 / Group 0c; `test_quality_floor.py` floor constants).

---

## Per-finding verdicts

### SCI-B1 (BLOCKING) — regression bound not pre-registered — **FIXED-CORRECT**
§3 now pins `max_regressions: 0` as an integer, on document-side grounds, with an unambiguous
named decision rule: any flip adjudicated `regression` → cycle REVERTS (driver-enforced; the
old "revert OR referral" disjunction is deleted, referral is the sequel); `unclear` flip-outs
with the m0587 atom-gap pattern route to the named F13 vocab follow-up batch. The §2
arithmetic is stated exactly as the review prescribed: only atom-gap clauses could license a
regression, bounded by the census's tool-sided count (4 of 30); bounds ≥ 5 ungrounded under
every reading, bounds 1–4 would pre-license substitution on the banned clause class, so the
tripwire is 0 — pre-registered from principle + census arithmetic, not fitted. The bound is
stated in §3 so PREDICT freezes it, and §6's PREDICT line carries it into prediction.json.
F13 exists in PORTFOLIO_REVIEW.md (checkpoint census = S8), so the referral target is real.

### ENG-M1 (MAJOR) — gate enable/disable vehicle unspecified — **FIXED-CORRECT**
§6 states the vehicle plainly: the gate is UNCONDITIONAL once merged (the review's reading 1)
— no CLI flag, no manifest key, no `_measure` seam, `cycle.py` NOT in files_to_change; the
opt-in reading is rejected by name with its consequence (would measure a NO-OP). The
absent-key dispatch branch passes the gate-OFF parameter explicitly. The "exactly the
pricing_version pattern" claim is corrected in a dedicated "Reachability" block: pattern
HOLDS (own identity key, absent-is-defined-value, dispatch rung, diff surfacing), does NOT
hold at the builder (bare `snapshot.py` can never rebuild a pre-gate snapshot byte-for-byte;
reachability is dispatch-only), and the manifest compatibility statement names the
reachability mode DISPATCH-ONLY — exactly what the review asked for.

### ENG-M2 (MAJOR) — false "A2 ⇒ A1" lemma — **FIXED-CORRECT**
§2 Rule A2 now states the rules are INCOMPARABLE, with the m0587 counterexample computed
(atom 0.0, lex 0.0819, ungated section 0.5803 → A1 gives 0.0, A2 gives min(0.5803, 0.0819)
= 0.0819) and the converse direction stated (A2 throttles the amplify case A1 preserves).
A2's rejection rests on the independent cap-constant ground, and the text says the
correction removes a false lemma, not a reason.

### ENG-M3 (MAJOR) — standing quality floors undisclosed — **FIXED-CORRECT**
§5 adds a full pre-registration: the floors are a `conftest.REQUIRED` guard measuring the
very scorer A1 modifies (`predict` MCC, b8 pairing, re-derived Otsu), and under the
unconditional gate they measure the gated scorer. The table reproduces the review's verified
numbers verbatim (caution +0.2826 → +0.2474, margin 0.017; harm +0.3502 → +0.3782, margin
0.078; helpfulness +0.2007 → +0.2626, margin 0.113). Treatment pre-registered: re-derive
all three floors AND the mean floor in the SAME COMMIT, ≈ 0.05 below the gated measurements
(caution ≈ 0.20, harm ≈ 0.33, helpfulness ≈ 0.21, mean ≈ 0.25 — arithmetic consistent:
each is gated MCC − 0.05; mean of gated MCCs = 0.2961), numbers pinned in the cycle record,
mandatory ⚠️ rationale comment, and the caution DROP framed as calibration, not relaxation.
The Otsu move (helpfulness 0.2318 → 0.0569) is disclosed. Goes one step beyond the review,
correctly: `MEAN_FLOOR = 0.23` exists in test_quality_floor.py and also measures the gated
scorer, so it is included; the STRUCTURAL floors are rightly left alone (they measure
`StructuralIndex`, which A1 does not modify). `test_quality_floor.py` is in files_to_change.

### SCI-M1 (MAJOR) — subset/enumeration claims elide corpus-max renormalization — **FIXED-CORRECT**
§3 defines the flip set on the NORMALIZED surface ("clauses with atom == 0 whose normalized
total minus their section credit's normalized contribution falls below the frozen cut"),
states the raw-space shorthand coincides only because the denominator is unchanged, and pins
the corpus-max condition as an explicit OPEN-time check: predictions are CONDITIONAL on every
behaviour's corpus-max clause having atom > 0 (verified on extant baselines m0527/m0592/
m0438, stated as an empirical envelope fact, not mechanism necessity); a future violating
baseline is a scoping trigger that voids and re-pins, not a falsification. The zero-new-flip
prediction is re-worded to fire "WITH the corpus-max check passing". §6's gate tests carry
the precondition into the OPEN enumeration.

### ENG-m1 (MINOR) — manifest spec gaps — **FIXED-CORRECT**
`config.overlay = overlay_empty.json` pinned explicitly with the confound rationale;
`depends_on` re-described as descriptive prose, not a manifest key, with the frozen-cut
dependency correctly assigned to `config.thresholds`; `conftest.py` added to files_to_change
with the same-diff registration-fence citation.

### ENG-m2 (MINOR) — census config identity not plumbed — **FIXED-CORRECT**
Takes the review's second permitted option: deferral with a named owner. The gap is stated
plainly (items (a)–(d) do NOT reach census identity), the reason given (this cycle runs no
census, so the plumbing would be unexercised), and the obligation is specced for S8: the
checkpoint census header must record `section_gate_version` whenever the scoring scorer had
the gate enabled (post-merge: always), tracked as Group 0c ("census --overlay/headers",
before S8). Both referents (F13/S8, Group 0c) exist in PORTFOLIO_REVIEW.md.

### ENG-m3 (MINOR) — two-axis dispatch-ladder composition — **FIXED-CORRECT**
§6(c) carries the obligation in the exact form the review suggested: whichever of S3b and S4
lands SECOND must extend EVERY rung of the first axis with the other (each pricing rung gains
the gate branch, absent key ⇒ ungated variant), else a snapshot carrying both keys is
dispatch-ambiguous.

### SCI-m1 (MINOR) — principle worded broader than its rule — **FIXED-CORRECT**
Principle narrowed to "the section prior may amplify a clause's own ATOM evidence, never
substitute for it", with an inline bracket citing the lexical-self-evidence counts
(506/510, 530/533, 442/451) and the Lead-2 / Rule-D grounds for atom-only
operationalization — both remedies the review offered, applied together.

### SCI-m2 (MINOR) — binary-cliff unlock incentive — **FIXED-CORRECT**
§5 adds "The unlock cliff, named for the cycles that inherit it": the stopword-floor blocking
is retained, the incentive is named verbatim ("vocabulary additions can buy section credit
for a clause one ε-match at a time"), the unlock side's invisibility in this cycle's
measurement is stated, S6/S7 are named as inheritors, and the checkpoint census (S8) is
named as the first instrument that can observe the unlock side, with the pattern to read.

---

## Light internal-consistency check

The fixes cohere; no blocking contradictions found:

1. **SCI-B1 vs §2 wording.** §2 still says "reverting on a PATTERN of [regressions] is the
   designed outcome" while §3 pins revert on ANY single regression (max_regressions 0).
   Not a contradiction: §3 explicitly subordinates the qualitative form ("survives only as
   orientation … the decision reads the bound, not the expectation").
2. **ENG-M1 vs ENG-M3.** The floor pre-registration is explicitly conditioned on the chosen
   vehicle ("Under the unconditional gate (§6) they measure the GATED scorer") — the two
   fixes reference each other correctly.
3. **ENG-M3 vs §3 frozen-cut precondition.** Potential conflict resolved by explicit
   scoping: the frozen-cut precondition governs the snapshot/flip surface, not the floor
   test's standing measurement path (where a re-derived cut is the defined semantics).
   Consistent with the closing "neither may re-derive it", which governs the frozen
   threshold artifact, not the floor test's internal Otsu.
4. **SCI-M1 vs §6 gate tests.** The corpus-max precondition is carried into the OPEN
   enumeration and the gate-test list consistently.
5. **files_to_change vs the vehicle choices.** Coherent: `cycle.py` absent (unconditional
   gate needs no `_measure` seam), `audit_disagreements.py` absent (census identity deferred
   to S8), `conftest.py` present (registration fence), `test_quality_floor.py` present
   (same-commit floor re-derivation).
6. **Cross-references resolve.** F13 and Group 0c exist in PORTFOLIO_REVIEW.md; `MEAN_FLOOR`
   exists in test_quality_floor.py; the ENG-M3 numbers match the review's independently
   recomputed table verbatim.
7. **Non-substantive observations (not concerns):** a few line citations shifted by 1–4
   lines relative to the review's (stopword floor 552–555 vs 553–557; `_measure` 927–942
   vs 911–934; smoothed idf 563–565 vs 562–565). The review verified the substance of each
   claim; the shifts do not alter any fix.

---

## Overall assessment

**READY-FOR-NEXT-STEP.** All ten findings (1 blocking, 4 majors, 5 minors) are fixed;
none is FIXED-WITH-CONCERN or NOT-FIXED. The blocking SCI-B1 tripwire is pre-registered on
document-side grounds with the arithmetic stated; the majors are resolved at the exact sites
the review named; the minors are fixed or deferred through the review's own permitted
deferral route with named owners. The revision header's claim ("blocking finding and all
four majors resolved inline, each marked at the change site; minors fixed or explicitly
deferred with a named owner") is accurate. The design should open per the review's
recommendation ("REVISE, then build").
