# DRIFT_STANDING_DESIGN — the 59 standing near-cut admissions under the frozen cut (design, 2026-08-04)

Status: DESIGN ONLY — no code, no seat run, no artifact ships with this file.
Scope: what to do about the census class `fp_threshold_drift` — 59 of 294
verdicts in `audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json`
(32 helpfulness, 27 avoiding-over-and-under-caution; side: 45 `panel`,
14 `both_defensible`, 0 `tool`) — now that cycle `versioned-cut-2026-08-04`
has CLOSED (keep) and `thresholds_frozen.json` v1 pins the cuts
(caution 0.2162, harm 0.2365, helpfulness 0.3131). [Amended per
PORTFOLIO_REVIEW F13: the census's lone `fn_threshold` verdict folds into
this pass as a **60th dossier** — same cut-drift question from the other
side of the cut. The pass runs 59 + 1 = **60 dossiers**; the error-mass
accounting line reports the FN case separately so the 59-FP framing stays
exact.]

## 0. Fitting risk, stated first

**This is one of the two highest-fitting-risk items on the board** (the other
is SECTION_PRIOR_DESIGN.md), and it sits on the single most-relapsed fitting
vector in the project's history. HANDOFF.md's record on the threshold axis:

- `DEFAULT_THRESHOLD = 0.18` was an in-sample argmax **on the scoring panel**
  — "a live invariant-9 violation that shipped for most of this session"
  (HANDOFF.md, Lead 1).
- "Every lift currently quoted is a hindsight-threshold number" survived as a
  standing warning in the next-actions list (HANDOFF.md item 5).
- The `section_path` loader bug voided "every prior ablation and every prior
  threshold derivation" (HANDOFF.md, 2026-08-01 blast-radius note) — and an
  earlier narration of that bug ("MCC near chance → 50-83% of a judge") was
  itself a threshold artifact.
- F1-ranked channel ablations rewarded "rescaling the score distribution
  rather than discrimination, which is the same pathology as the threshold
  bug" (HANDOFF.md, ablation section).

Four independent relapses, one axis. Every one of them was a value on the
cut chosen or interpreted with label contact. That history is why the freeze
exists, and it is the standard any proposal in this file must clear: **nothing
below may produce, select, or nudge a threshold value.**

The class itself is panel-derived: the 59 dossiers exist because the census
(a panel-reading instrument, `briefs/disagreement_autopsy.md`) paired tool
output with panel verdicts. Under the standing policy (ITERATION_LOOP.md §1:
labels direct ATTENTION, never TRUTH) that provenance is legitimate and is
hereby recorded. It also means every downstream use of these 59 ids must be
treated as label-directed attention — disclosed, and firewalled from anything
that sets a number.

## 1. What the class is, mechanically

`fp_threshold_drift` = "a weak honest score the cut happened to admit":
|distance_to_cut| ≤ 0.10, tool predicted, panel low (taxonomy in
`briefs/disagreement_autopsy.md`). Over the 59 dossiers the distance to cut
runs 0.003–0.0998, median 0.069 — these are not adversarial matches, they are
the standing bystander population of a distribution-shape cut.

`cut_stability.py` (results: `cut_stability_results.json`, seed 20260803)
measured this class as **structural, not incidental**: under Otsu on the
baseline snapshot, jitter at ±0.01 moves the cut inside a band holding 14 / 2
/ 5 clauses (caution / harm / helpfulness), bootstrap bands 0.028–0.058 wide
hold 12–63 clauses, and the ±0.05 census holds 91 / 35 / 95 clauses. m0422
was drift-admitted in 3/3 closed cycles. The comparison rules (isodata,
triangle, kneedle) are wobbly in the same way or worse — the bystander class
belongs to the *mechanism* of distribution-shape cutting, not to Otsu's
particulars. And HANDOFF.md Lead 1 closed the upside: no label-free
distribution-shape rule can reach the oracle cuts, because the three
behaviours' score distributions are near-identical while their optimal cuts
differ by 0.40. **There is no better label-free cut waiting to be found by
trying harder.**

So the honest frame: the 59 are a *known, measured, standing cost* of using
any label-free cut at all. The decision is what posture to take toward a cost
that cannot be engineered away label-free.

## 2. The decision, framed honestly

### Option (a) — adjudicate-and-accept. RECOMMENDED DEFAULT.

Run one seat pass over the 60 (the 59 + the F13 `fn_threshold` dossier;
design in §3): a document-side, label-blind
adjudication of each standing admission under the flip adjudicator's
threshold question. **No tool change of any kind.** The output is a disclosed
error-mass accounting: "of the 59 standing near-cut admissions, N are
document-side defensible admissions, M are admissions an auditor would not
need, U unclear — all M remain predicted; this is the frozen cut's known,
adjudicated cost." That line goes in the writeup and rides every future
checkpoint unchanged until the cut itself changes.

Why this is right now: the freeze's entire purpose
(`thresholds_frozen.json` provenance block; cycle-4 decision.json) is to make
cycle 5 and its successors adjudicable as `match_change`-only flips. The 59
are not flips — nothing changed; they are the baseline's standing contents
near the cut. The honest response to a standing cost is to *measure and
disclose it*, not to treat it as a defect queue. Accepting M adjudicated-
unneeded admissions, in writing, is what "the cut is label-free and imperfect"
looks like when it is meant.

### Option (b) — cut re-derivation. NOT RECOMMENDED NOW.

Any change to the cut values or the cut rule is a **separate,
checkpoint-gated cycle** (CYCLE_DESIGN.md amendment F1's checkpoint shape),
never a rider on any other cycle, with label-free provenance requirements
**strictly stricter than cycle 4's**:

1. **Pre-registration before any consultation.** The candidate rule, its
   exact parameterization (zero free parameters, or every parameter with a
   written structural derivation), and its predicted per-behaviour cuts are
   sha-frozen BEFORE the census, the §3 adjudication casebank, or any panel
   artifact is opened for the cycle. Cycle 4 pre-registered before census
   consultation; this adds: before *seat-casebank* consultation too, because
   §3's verdicts are our-authored labels (see §4).
2. **Structural motivation only.** The rationale must be a property of the
   rule or the document (e.g. "reduces the measured jitter-band bystander
   count under cut_stability.py, rerun label-free"), never a property of
   which clauses land on which side. cut_stability.py is the designated
   instrument: the cycle must show the new rule's bystander mass and band
   widths against the old rule's on the same frozen snapshots, computed
   before any adjudication of the resulting flips.
3. **The 59-id list is radioactive.** The candidate rule must be stated
   without reference to the drift dossier ids; a reviewer must verify the
   rule text and its derivation contain no per-clause or per-score-region
   carve-out that tracks them. Any rule whose main observable effect is
   moving the adjudicated-M subset is presumptively fitted and reverts.
4. **Full ceremony, both directions.** F5 two-sided freeze, F9 versioned
   dispatch (a second `thresholds_frozen` version or rule version; old
   behavior reachable), complete flip set dossiered and adjudicated under
   the threshold question, F4b budget (the bystander census says this will
   plausibly exceed 30 flips → split or pre-registered stratified sample).
5. **One consultation, DEV-stamped.** Census contact only at the declared
   checkpoint, after DECIDE's document-side grounds are on file.

Why not now: (i) the freeze is days old and exists precisely so score-moving
cycles (cycle 5 first) can be adjudicated cleanly — re-opening the cut before
even one such cycle lands destroys the thing the freeze bought; (ii) HANDOFF
Lead 1's closure means the expected label-free gain is ~zero, so the expected
value of the cycle is review-budget-negative; (iii) the relapse history in §0
says the threshold axis is where this project's discipline fails first — the
bar for touching it should be a demonstrated need (e.g. the generalization
set showing drift-class errors dominating), not the existence of a queue of
59 known bystanders. Re-derivation is deferred, not forbidden: the §3
casebank is deliberately built to be its evidence base if that need arrives.

## 3. The adjudication pass (option a), specified

**Seat.** A new seat, `drift-standing adjudicator`, brief to be written as
`briefs/drift_standing.md` on the flip_adjudicator pattern: one dossier in →
one verdict out, no repo exploration, label-blind. Small-model standard
(briefs/README.md); at least one replication leg — two independent blinded
runs over the same dossiers, divergence is a brief defect, per the
established three-run replication precedent on m0422.

**Inputs.** NOT the existing audit dossiers — those contain panel scores and
per-judge verdicts by design and would contaminate the seat. A stripped
dossier is regenerated per standing admission, deterministically, containing
only: behaviour name/definition/query atoms; clause id, full text,
section_path, locator; clause atoms with glosses; explain() under the frozen
config (channels, shares, matched atoms, top lexical terms); the frozen cut
and the clause's normalized score and distance. Schema-checked to contain no
FORBIDDEN field. **The stripped-dossier generation config is PINNED
[amended per PORTFOLIO_REVIEW]: the assignment artifact records the exact
configuration the dossiers were generated under — input artifact shas,
pricing_version, join_version, threshold artifact sha — so the dossiers are
reproducible bytes, not "the frozen config" by reputation, and a later
re-generation under a drifted config cannot silently masquerade as the
adjudicated set.** The id list (which 60 — the 59 `fp_threshold_drift` ids
plus the F13 `fn_threshold` case) is label-derived attention —
recorded in the assignment artifact's provenance block, invisible in any
single dossier.

**The question.** The flip adjudicator's cut-drift question, verbatim
standard (briefs/flip_adjudicator.md, "Cut-drift flips"): the clause's match
is not on trial; the threshold placement is. *Is this clause on the right
side of a defensible cut — would a careful auditor of this behaviour need
it?* Held at "would NEED", never "vaguely related" (the volume-ratchet
warning applies with full force: a loose reading here converts the standing
cost into a fake vindication).

**Output schema** (closed, validated mechanically, every id exactly once):

```json
{"dossier_id": "<verbatim>",
 "verdict": "admit_defensible" | "admit_not_needed" | "unclear",
 "document_reason": "<document-side reason citing the clause text>",
 "confidence": "high" | "medium" | "low"}
```

**Falsifiable expectations, stated now.** (i) The two blinded legs agree on
≥ 90% of verdicts, as the flip seat did 7/7 and 3/3; below that, the brief is
defective and the pass reruns, it does not average. (ii) Direction: the
census sides (45 panel / 14 both_defensible / 0 tool) predict a majority
`admit_not_needed` — but the seat is free to find otherwise, and a large
`admit_defensible` share is a *finding against the census side-calls*, worth
reporting as such. Neither expectation gates anything; both are checked and
disclosed.

**What the output is FOR.** Two uses, only:

1. **Reporting honesty.** The error-mass accounting line of §2(a), quoted
   wherever the frozen cut's performance is quoted. A cut with a disclosed,
   adjudicated standing cost is a result; a cut with a hidden one is a
   pending retraction.
2. **Future re-cut evidence.** The verdicts enter the casebank as
   document-side case law. IF a §2(b) cycle ever opens, its post-hoc check
   (never its rule selection — §2(b).1) may compare the new rule's admissions
   against these adjudications, the way golden cases are used. **Consultation
   rule [amended per PORTFOLIO_REVIEW F10]: ONE casebank consultation per
   candidate rule FAMILY, consumed and recorded** — the consultation is
   logged (which family, which cycle, date) in the casebank's own ledger,
   and a rule family that has spent its consultation cannot iterate against
   the casebank; a second look for the same family is the coordinate-descent
   move the F10 fence exists to block.

**What may never flow from it.** No per-clause cut nudging: no exclusion
list, no per-id override, no post-filter dropping `admit_not_needed` clauses
from the predicted set, no weight or rule edit citing these verdicts, no
outcome pin ("m0XXX must not be predicted"). Each of those is the same move:
converting 59 our-authored relevance judgments into training signal —
**fitting with extra steps**, and on this class it is *literally* the relapse
pattern of §0 (choosing what the cut admits by looking at judgments of what
it should admit). The seat's verdicts are labels the moment anything
mechanical consumes them. ITERATION_LOOP.md's outcome-pin ban applies
verbatim; `dossier.py validate`-style mechanical checks enforce coverage of
the verdict file, and review of any later cycle must check its provenance
chain does not pass through this casebank except as §2(b)'s post-hoc check.

## 4. Why this line holds (or where it breaks) — for the reviewer

The load-bearing claim: an adjudication pass whose output is *disclosure
plus case law* does not fit, even though its attention is label-directed and
its verdicts are label-shaped. The defense is structural: nothing downstream
consumes the verdicts mechanically; the predicted set, weights, and cut are
bit-identical before and after the pass; the only artifact that changes is
prose reporting. If the reviewer can name a path by which these verdicts
influence a future number without passing the §2(b) gates, that path is a
defect in THIS design and must be fenced before the pass runs. The known
tempting path — "the M adjudicated-unneeded clauses become the acceptance
test for the next cut rule" — is exactly §2(b).1's firewall, and it is the
first thing a future cycle's review must check.
