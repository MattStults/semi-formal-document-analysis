# S4_ADVERSARIAL_REVIEW — clean-context adversarial design review of SECTION_PRIOR_DESIGN.md (2026-08-05)

Artifact: `SECTION_PRIOR_DESIGN.md` (the S4 section-prior evidence gate, design only).
Reviewer: clean-context adversarial design reviewer (no prior context; everything re-derived
from disk). Dimensions: **engineering excellence** and **science**. Method: every code claim
in the design was checked against the tree (`relevance.py`, `containment.py`, `snapshot.py`,
`dossier.py`, `cycle.py`, `audit_disagreements.py`, `test_quality_floor.py`), every number
was re-computed from the on-disk artifacts (`snapshots/patient-backfill-2026-08-04.json`,
`snapshots/join-integrity-v2-2026-08-04.json`, `cycles/CYCLE_LOG.jsonl`,
`audit_dossiers/ext_v1_merged__audit_v1/`, `thresholds_frozen.json`), and the governing
docs were read (`HANDOFF.md` top section + S4 rulings, `CYCLE_DESIGN.md` incl. BINDING
AMENDMENTS and PRE-BUILT CYCLES, `ITERATION_LOOP.md` policy, `REPRODUCIBILITY.md`,
`PORTFOLIO_REVIEW.md`, `OUTSTANDING_WORK.md`).

---

## VERDICT: **REVISE**

One blocking finding (the decision-critical regression bound is not pre-registered), four
majors, five minors. The design is close: its mechanism description, its census statistics,
and its flip enumeration all reproduce exactly under independent recomputation (see
"Verified correct" below) — the blocking item is a pre-registration gap, not a mechanism
defect, and the majors are spec completions, not redesigns. A positive review would be
wrong: the blocking item sits on the exact tripwire that caught the program's only defect
so far (S3), and leaving it to operator choice at PREDICT time is the one thing this
process exists to prevent.

**Finding counts**

| dimension            | blocking | major | minor |
|----------------------|:--------:|:-----:|:-----:|
| Engineering excellence | 0      | 3     | 3     |
| Science                | 1      | 1     | 2     |
| **total**            | **1**    | **4** | **5** |

---

## Verified correct (so the findings below are not read as blanket doubt)

Re-computed independently, all reproduce exactly:

1. **Code citations.** `relevance.py` `Weights.section = 0.45` / `section_top_k = 3` at
   lines 491–492; `channel_scores` section step at 703–711 (`local` at 704, `sec[path]`
   at 706–709, assignment at 711); membership map at 570–574; smoothed idf at 562–565.
   The design's mechanism reading (pure propagation: every member gets
   `0.45 × mean(top-3 locals)`, unconditional) is exactly right, and since
   `containment.ContainmentIndex.channel_scores` delegates to
   `super().channel_scores(...)` (containment.py), implementing the gate in
   `relevance.py` does cover the shipped overlay-on path.
2. **The flip enumeration.** Applying A1 offline to
   `snapshots/patient-backfill-2026-08-04.json` (channels as recorded): **30 flips =
   13 avoiding-over-and-under-caution + 13 harm-avoidance-to-third-parties +
   4 helpfulness; 0 newly_predicted; every flipped-out clause has atom channel exactly
   0.0**; helpfulness flips exactly m0379/m0381/m0382/m0389. Identical result against
   `snapshots/join-integrity-v2-2026-08-04.json` (behaviours byte-identical to the
   post-S2 snapshot — config inputs, weights, scores, predictions all equal).
3. **Census statistics.** `verdicts_merged.json`: 294 cases, 30 `fp_section_prior`,
   split 18 caution / 12 harm / 0 helpfulness, side 26 panel / 4 tool; dossiers:
   24/30 `atom_channel_zero`; section channel-share 0.428–0.956, median 0.892;
   worked example m0587 = atom 0.0 / lex 0.0819 / section 0.5803 / share 0.876,
   zero matched atoms, zero subsumption matches. All as the design states. The
   checkpoint forecast is mechanically grounded: 26/30 census cases carry clause ids
   inside the A1 flip set.
4. **The log-read rule works, including the revert case.** `cycles/CYCLE_LOG.jsonl`:
   the reverted `patient-pricing-2026-08-04` line carries `"decision": "revert"` and
   is skipped; the last keep line resolves to `join-integrity-v2-2026-08-04`, whose
   snapshot exists and is score-identical to the post-S2 baseline (so the baseline
   moving with the log is harmless today; `OUTSTANDING_WORK.md` D1 independently names
   "currently join-integrity-v2"). The deleted stale "cycle-4 config if cycle 5
   reverts" fallback is gone from the design, and no static baseline name remains.
5. **Driver claims.** `_open` does refuse a shape:code manifest with empty
   `compatibility.version_key`/`statement` (cycle.py:622–630); `FLIP_BUDGET = 30` with
   a strict `>` halt (cycle.py:113, 981) — 30 is at the line, not over it;
   `snapshot.assert_frozen_thresholds` exists and the baseline passes it
   (`threshold_source == "frozen_artifact"` on all three behaviours, cuts equal to
   `thresholds_frozen.json` v1); the dossier reconstruction self-check
   (`ReconstructionMismatch`) would catch a dispatch rung that fails to reproduce.
6. **Rule D's rejection rationale holds empirically.** lex is near-universally nonzero:
   only 1–2% of clauses have lex == 0 per behaviour on the baseline (4/593, 3/593,
   9/593), so a lex gate would indeed fire almost never.

---

# Engineering excellence

## ENG-M1 (MAJOR) — the gate's enable/disable vehicle is unspecified, and the "exactly on the pricing_version pattern" claim does not hold for reachability

The F9 spec (§6, items (a)–(d)) says snapshot.py records `section_gate_version`
"whenever the index that scored had the gate enabled" — implying the index has an
enabled and a disabled state — but nothing in the declared change set can express that
state at snapshot BUILD time:

* `cycle.py::_measure` (lines 911–934) threads exactly `annotations`, `atoms`,
  `overlay`, `thresholds` from the manifest config into the `snapshot.py` command;
  there is no seam for a gate flag, and **`cycle.py` is not in files_to_change** (§6).
* `snapshot.build_snapshot`'s signature has `overlay_path` / `thresholds_path` and
  nothing else scoring-relevant; the manifest config schema (cycle.py
  `manifest_template`) has `annotations/atoms/overlay/thresholds` only.

There are therefore two readings, and the design commits to neither:

1. **Gate unconditional once merged.** Buildable with the declared files (the measure
   snapshot is gated automatically; dossier.py's `_index_for` needs an explicit
   gate-off parameter for the absent-key branch). But then builder-level reachability
   of pre-gate scoring is GONE — bare `snapshot.py` can never again reproduce a
   pre-gate snapshot byte-for-byte — which is a real departure from the pattern §6
   claims to follow "exactly": `pricing_version`'s old behavior stayed reachable AT
   THE BUILDER by omitting `--overlay` (S1 manifest compatibility statement;
   snapshot.py:257–284), and `thresholds`' by omitting `--thresholds` (versioned-cut
   manifest). Reachability would exist only in the reconstruction dispatch — defensible
   under F9's letter ("so the baseline side reconstructs"), but §6 must say so plainly,
   and the manifest's compatibility statement must name dispatch-only reachability.
2. **Gate opt-in.** Needs a new CLI flag + manifest config key + `_measure` plumbing —
   i.e. `cycle.py` in files_to_change, which the design does not declare. Under this
   reading the cycle as specified measures a NO-OP (the measure snapshot scores ungated).

Fix: pick one, state it in §6, and (if reading 2) add `cycle.py` to files_to_change.
Either way, correct "specified exactly on the pricing_version pattern" to name the
respect in which the pattern holds (config-identity key + dispatch rung + diff
surfacing) and the respect in which it does not (builder-side reachability).

## ENG-M2 (MAJOR) — §2's "A2 ⇒ A1" is false; the two rules are incomparable

§2 candidates: "Rule A2 ... Strictly stronger than A1 (A2 ⇒ A1 since local ≥ atom ≥ 0
and a zero-local clause caps at 0)". This is wrong. A2 caps section credit at
`local[cid] = lex + atom + kind` (kind weight is 0.0 — relevance.py:490), so an
atom-zero clause with positive lex keeps positive section credit under A2. Verified on
the design's own worked example from the baseline snapshot: m0587 has atom 0.0, lex
0.0819, ungated section 0.5803 — A2 gives min(0.5803, 0.0819) = **0.0819 > 0**, where
A1 gives 0. So A2 does NOT imply A1, and A1 does not imply A2 either (A2 throttles the
amplify case A1 preserves) — the rules are incomparable, not "strictly stronger".
A2's rejection stands on the design's other stated ground (the cap constant smuggles a
shape choice), so the recommendation is unaffected — but a false mathematical lemma in
the section that argues the recommendation must be corrected; this is the document whose
whole function is precision.

## ENG-M3 (MAJOR) — the standing panel-derived quality floors measure the very scorer A1 modifies; the design never mentions them

`test_quality_floor.py` is a `conftest.REQUIRED` guard (ITERATION_LOOP.md anti-cheat
perimeter) and measures `relevance.RelevanceIndex.predict` MCC per behaviour against
the true panel on the b8 pairing, with floors helpfulness 0.15 / harm 0.30 / caution
0.23 and a "raise-in-the-same-commit, never lower" rule (test_quality_floor.py
docstring + FLOORS). If the gate lands (under ENG-M1 reading 1, unconditionally), this
measurement changes. Pre-computed here with the exact test path (`predict` semantics,
Otsu cut re-derived, true universe; the ungated numbers reproduce the file's own
docstring values exactly):

| behaviour | MCC ungated | MCC gated | floor | margin after |
|---|---:|---:|---:|---:|
| avoiding-over-and-under-caution | +0.2826 | +0.2474 | 0.23 | **0.017** |
| harm-avoidance-to-third-parties | +0.3502 | +0.3782 | 0.30 | 0.078 |
| helpfulness | +0.2007 | +0.2626 | 0.15 | 0.113 |

All three floors stay green, so this does not block the build — but the suite is
REQUIRED, the caution margin tightens ~4×, and two floors drift far below the measured
value ("a guard that had quietly gone slack" is the exact pathology the floor test's
own history records). The design must pre-register the floor treatment: re-derive the
floors in the same commit with the measurement (the floor file's own rule for a genuine
change), with the numbers pinned in the cycle record. Note also the Otsu cuts on this
path move substantially under the gate (helpfulness 0.2318 → 0.0569) — the m0422
drift dynamic the design itself warns about (§3 hard precondition) is live on every
path that re-derives its cut; the floors are such a path.

## ENG-m1 (MINOR) — manifest spec gaps: `config.overlay` omitted; `depends_on` is not a schema field; conftest registration not declared

* §6 specifies the manifest's `depends_on`, `census`, `census_scope`, compatibility
  block — but not `config.overlay`. The entire keep lineage is overlay-ON
  (`overlay_empty.json`, pricing_version 1.2; S1's manifest carries both `overlay` and
  `thresholds` in config). Omitting it from the measure snapshot makes
  `diff_snapshots` surface "overlay" in `config.changed` and confounds the diff with a
  scorer swap (ContainmentIndex → legacy). Loud, not silent — but the design should
  pin `config.overlay = overlay_empty.json` explicitly next to the thresholds
  requirement it already states.
* `depends_on` appears in no manifest template and no validation (cycle.py
  `manifest_template` / `REQUIRED_MANIFEST_KEYS`); an extra key is tolerated noise.
  The frozen-cut dependency is really carried by `config.thresholds` — say that.
* files_to_change says "tests (any NEW test file registered in `conftest._OPTIONAL`)"
  — the registration fence requires `conftest.py` itself in the same diff
  (ITERATION_LOOP.md anti-cheat perimeter; AGENTS.md "same diff, every time"), so
  `conftest.py` belongs in files_to_change.

## ENG-m2 (MINOR) — the version-key plumbing is narrower than the pattern it cites: census config identity is not covered

CYCLE_DESIGN F2 requires the FULL config identity (input shas, overlay sha,
pricing_version, threshold rule) in census output headers, and
`audit_disagreements.py` (lines 279–311) accordingly records `pricing_version` in
census identity when the overlay scored. The design's (a)–(d) plumb
`section_gate_version` through snapshot identity, `diff_snapshots` surfacing, dossier
dispatch, and the manifest — but not through the census identity. The consequence lands
at S8 (the checkpoint census that checks this cycle's own DEV-stamped class forecast):
its header would omit a scoring-rule version that changed scores. Add
`audit_disagreements.py` to files_to_change or name why S8 carries it.

## ENG-m3 (MINOR) — dispatch-ladder composition across the two version axes is unstated

§6(c) specifies the section axis only (ABSENT ⇒ ungated, PRESENT ⇒ gated). The ladder
it extends (dossier.py `_index_for`) is keyed on `pricing_version` first ("2.0" →
PatientIndex; overlay → ContainmentIndex; else legacy). S3b will land its own
pricing rung (S3B_REDESIGN.md §6: "a new pricing_version value in snapshot config
identity"). Whichever of S3b and S4 lands second must extend EVERY pricing rung with
the gate axis, or a snapshot carrying both keys is dispatch-ambiguous. One sentence in
§6(c) assigning that obligation ("the cycle that lands the second axis extends all
rungs of the first") closes it.

---

# Science

## SCI-B1 (BLOCKING) — the decision-critical regression bound is not pre-registered; "a cluster" is not a number and the driver demands one

Verbatim finding:

> §3 (PREDICT) pins the flip count (30), the directions (no_longer_predicted only),
> the per-behaviour split (13/13/4), and even the four helpfulness clause ids — but it
> leaves the DECISION-CRITICAL bound qualitative: "most flip-outs expected `correct`"
> and "a cluster of `regression` verdicts concentrated on atom-gap clauses (the m0587
> pattern) is the designed failure signal and grounds revert or a vocabulary-cycle
> referral". Meanwhile the driver REQUIRES `max_regressions` as a non-negative integer
> in prediction.json (cycle.py:794–796; template default 0, cycle.py:742), and
> `_check_predictions_adjudicate` (cycle.py:1051–1054) gates on exactly that number.
> The design says "PREDICT: §3 verbatim" — and §3 contains no number. So the integer
> that decides keep-vs-revert is chosen by the operator at PREDICT time, on no
> document-side grounds stated anywhere in the design. This is the one quantity the
> program's history proves is load-bearing: S3's revert was caught by exactly this
> bound (`max_regressions: 0` vs 4 regressions — HANDOFF.md, "The S3 finding";
> ITERATION_LOOP.md cycle-log note). And this design explicitly anticipates
> mechanism-grounded regressions (§2's "against" argument names the m0587 annotation-gap
> cost as "accepted and DISCLOSED", with "a `regression` verdict on such a clause is
> the designed detector") — so the template default 0 is not even clearly the intended
> value, and the "revert OR vocabulary-cycle referral" disjunction is itself an unpinned
> judgment call at decision time. A bound chosen after the mechanism is known and before
> the verdicts are in is a fitted constant wearing a pre-registration's clothes.
>
> Fix, before OPEN: pin the integer (or a named decision rule, e.g. "max_regressions
> = 0; any regression on a clause with a document-side auditor-need adjudication is a
> revert; regressions adjudicated `unclear` route to the named F13 vocab referral")
> WITH its document-side grounds in §3, so PREDICT freezes it. The grounds exist in the
> design's own §2 — the principle says substitution-banned flips are correct removals,
> so the only licensed regressions are atom-GAP clauses, and their count is bounded by
> the census's own tool-sided count (4 of 30) — state that arithmetic, or reject it by
> name, but do not leave the tripwire unset.

## SCI-M1 (MAJOR) — the §3 subset prediction and the enumeration formula elide the corpus-max renormalization; both are conditionally true, stated as unconditionally true

§3: "Scores only decrease; predicted_new ⊆ predicted_old at the frozen cut ... Any such
flip falsifies the design outright", and the flip set is "{clauses with atom == 0 whose
total minus section credit falls below the frozen cut}". But predictions are decided on
the NORMALIZED surface: `rank()` divides every raw score by the corpus raw max
(relevance.py:780–783), and `build_snapshot` records exactly those normalized scores
against the frozen cut (snapshot.py:200–207). A1 monotonically decreases RAW scores,
and normalized scores decrease too ONLY IF the corpus-max clause is not gated — if it
were (atom == 0), the denominator drops and every surviving clause's normalized score
RISES, producing newly_predicted flips with the mechanism working exactly as designed.
Verified the condition holds on every extant baseline (the corpus-max clause has atom >
0 in all three behaviours: m0527, m0592, m0438) — but that is an empirical envelope
fact, not the mechanism necessity §3's wording claims, and "falsifies the design
outright" would misfire on any future baseline (post-vocab, per the design's own F6
scoping) whose top clause is gated. The enumeration formula has the same gap in reverse:
"total minus section credit falls below the frozen cut" compares a raw-space quantity
against a normalized cut; it happens to coincide because the denominator is unchanged
here. Fix: state the condition (corpus-max clause ungated — pin it in the OPEN
enumeration as an explicit check) and define the enumeration on the normalized surface.

## SCI-m1 (MINOR) — the principle is worded broader than the rule it justifies

The principle under test (§2): "the section prior may amplify EVIDENCE, never
substitute for it" — but the rule operationalizes evidence as the ATOM channel only.
On the baseline, 506/510 (caution), 530/533 (harm), 442/451 (helpfulness) of the gated
clauses carry positive lexical self-evidence. The design has the substantive argument
(§2: the atom index is the only behaviour-specific label-free signal — HANDOFF Lead 2;
Rule D: lexical overlap without a shared concept is itself the `fp_lexical_only` failure
class), but the principle as worded reads as if lexical self-evidence is not evidence,
which is a larger claim than the argument makes. Narrow the principle text to
"atom evidence" or cross-reference the Rule D / Lead-2 grounds inline, so the principle
cannot later be quoted against its own operationalization.

## SCI-m2 (MINOR) — the binary cliff creates an unlock incentive the design should name, not just the non-invariance

A1 keys full 0.45 propagation on exactly-zero atom evidence: any nonzero atom credit,
however weak, unlocks the entire section prior. The cheapest version of gaming this is
blocked by construction (stopword atoms are floored to idf 0.0 — relevance.py:553–557 —
so they contribute exactly 0.0 and cannot unlock), verified. But a rare atom with small
positive idf still unlocks everything, the unlock side generates NO flips in this cycle
(unchanged scores are not adjudicated), and the design's F6 scoping discloses the
non-invariance ("S6 atoms can give a gated clause its first nonzero atom credit")
without naming the incentive it creates for future vocabulary cycles to buy section
credit one ε-match at a time. Name it in §5 so the S6/S7 cycles inherit the awareness,
and note that the checkpoint census is the first instrument that can see the unlock
side at all.

---

## Recommendation

**REVISE, then build.** The mechanism is real, the discipline is largely intact, and the
pre-registered envelope reproduces under independent recomputation — this design is
worth the fix list, not a redesign:

1. **(Blocking, SCI-B1)** Pin `max_regressions` — an integer or a named decision rule —
   with document-side grounds, in §3, before OPEN.
2. **(ENG-M1)** Name the gate's enable/disable vehicle; declare `cycle.py` if opt-in,
   or state default-on + dispatch-only reachability and let the compatibility statement
   carry it; correct the "exactly the pricing_version pattern" claim.
3. **(ENG-M2)** Correct the A2⇒A1 lemma (the rules are incomparable; m0587 is the
   counterexample).
4. **(ENG-M3)** Pre-register the quality-floor treatment (measured deltas above;
   same-commit floor re-derivation with the numbers pinned).
5. **(SCI-M1)** State the corpus-max condition and move the enumeration formula to the
   normalized surface.
6. **(Minors)** config.overlay in the manifest spec + conftest.py in files_to_change +
   `depends_on` dropped or re-described (ENG-m1); census-identity plumbing or a named
   S8 owner (ENG-m2); the two-axis dispatch-ladder obligation (ENG-m3); principle
   wording (SCI-m1); name the unlock incentive (SCI-m2).

Nothing here touches the rulings the design already absorbed correctly (baseline from
the log, own F9 key, enumeration intact, seat fence, deferral as a legitimate terminal
state). After the fixes, this cycle should open.
