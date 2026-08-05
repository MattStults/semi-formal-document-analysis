# S3B Tier-2 verification pass — REVISION 9 fixes for the R8 majors (S-A, S-B)

Date: 2026-08-05. Seat: tier-2 verification (clean context; design-doc verification only —
no code, no git, no test runs). Scope NARROW: verify that the TWO major findings of
`S3B_ADVERSARIAL_REVIEW_R8.md` were correctly fixed in `S3B_REDESIGN.md` REVISION 9 and
`S3B_ATTRIBUTION_TASK_DESIGN.md`, plus a light internal-consistency check. Not an
adversarial hunt; no new issues sought.

## S-A (signature arm-binding) — FIXED-CORRECT

Ground: §7.1's SIGNATURE now binds arms per clause as a mechanical table — "m0275 ⇒
arm (i) ONLY; m0466 ⇒ arm (i) ONLY; m0018 ⇒ arm (ii) ONLY" with the rule "each clause
id may satisfy ONLY its bound arm, and a clause whose match satisfies ANY OTHER arm
FAILS the plank" — so a comprehensive-laundered m0275/m0466 (branch-2, full principal
set, `why = generic`) matches arm (ii), which is not its bound arm, and FAILS the
restoration plank (the mirror m0018 case fails the same way); AND the companion spec's
§2.5 now carries FROZEN-BACKFILL RE-CHECK CASES for m0275/m0466 with IMMUTABLE expected
verdicts (RESOLVED, `harm_bearers` exactly {third_party} — set equality rules out the
comprehensive laundering, any other bearer set, and `unclear`; re-check semantics pin
the matched-atom row of the frozen backfill artifact, and any contradiction routes to
the seat-defect channel with expectations that "do not move"); and §7.1 explicitly
adopts §3.4 F_core's clause-bound reading while §3.4 now records that §7.1 enforces it
mechanically — the two documents agree, both directions cross-referenced (R8-S-A tags
present at every site, plus §5.3's leak-coverage sentence updated).

Checked items:
* Binding table present, mechanical (a conjunction per clause, not a free disjunction);
  the old free-disjunction phrasing survives only as quoted-and-superseded history in
  the CONSEQUENCE OF THE BINDING passage. ✓
* Laundered verdict ⇒ FAIL traced: laundered m0275/m0466 satisfies `predicted` and
  factor 1.0 but not its bound arm (i) (`why = generic ≠ consistent`) ⇒ plank FAIL;
  stated verbatim in §7.1. ✓
* §2.5 re-check cases: immutable, matched-atom-row pinned, backfill-artifact binding
  (where parity verdicts do not bind), failure routing to §2.4's seat-defect channel,
  and an explicit statement that they are NOT added to §2.4's certification decision
  rule (which stays self-contained on the two D4 cases) — the division of roles is
  stated, not contradictory. ✓
* REDESIGN §7.1 ↔ TASK DESIGN §3.4 F_core agreement, both directions. ✓

## S-B (lapse-condition semantics) — FIXED-CORRECT

Ground: all three R8 gaps closed in §4B with matching restatements — (a) MEASURE-time
semantics stated explicitly ("the exclusion holds at MEASURE only if receiver readiness
holds AT MEASURE … otherwise … the demoted clause's expected flip IS counted against
the §7.3 bound") and receiver readiness added to §9's OPEN conditions (OPEN requires
the design PASSED review AND the tracker ACCEPTED m0239; "re-checked at MEASURE");
(b) ONE re-entry semantic at all three sites (§4B, §7.1, §7 plank 3 all now read
"re-enters THIS [cycle's] bound", with 'never "the next cycle\'s"' stated and the
former next-cycle reading deleted — grep confirms no live next-cycle text remains);
(c) post-close retroactivity stated: lapse established AFTER CLOSE re-counts the
recorded-and-reported m0239 flip retroactively against S3b's own bound at the decision
point where lapse is established, breaching `max_regressions: 0` and revising the
cycle's closure — the reading that gives the condition teeth, with the
permanent-immunization argument for it stated inline.

Checked items:
* §4B: receiver-readiness definition, MEASURE-TIME SEMANTICS block, OPEN-gate rationale
  (ordering false-fail class named), and the OPEN→MEASURE regression case covered. ✓
* §9: receiver readiness is a listed OPEN condition alongside the clean re-review and
  the D2/D5 rulings; "A coordinator must not open S3b on the D2/D5 rulings alone while
  the receiver is still DRAFT-unreviewed." ✓
* Three restatement sites reconciled (lines ~440, ~858, ~993 all "THIS bound" +
  retroactive re-count at the lapse decision point). ✓
* Retroactive re-count mechanics concrete: decision record in the repo, closure revised,
  removal stands PRICED but no longer bound-excluded, receiver-less removal an explicit
  open item. ✓

## Light internal-consistency check

The two fixes cohere:
* S-A's belt-and-braces is reflected consistently in three places: REDESIGN §7.1, §5.3's
  leak-coverage sentence (the golden coverage list now includes "§2.5's FROZEN-BACKFILL
  RE-CHECK CASES … m0275/m0466"), and TASK DESIGN §2.5 + the REVISION-9 ALIGNMENT NOTE.
* S-B does not contradict the m0239 two-horns pre-registration: the expected-horn
  parenthetical "(recorded, reported, bound-excluded by the CLASS RULE)" sits in the
  same plank whose preceding paragraph states the full lapse state space (q.v.), and
  OPEN-gating on readiness makes bound-exclusion the expected path; readiness
  regressing OPEN→MEASURE is explicitly assigned to the MEASURE-time statement.
* Cross-file pointers updated both ways: TASK DESIGN status line ("Aligned with
  `S3B_REDESIGN.md` REVISION 9"), §5 pointer (S-B completion noted), REDESIGN header
  note (§3.4 agreement noted). No reference to a nonexistent section found; the
  §2.5 four-case golden-failure routing coexists consistently with the self-contained
  two-D4-case certification rule.
* Numeric pins untouched where untouched: F_core = 3 and floor 110 unchanged (the S-A
  fix alters verdict SHAPES policed, not counts). ✓

Out-of-mandate observations (not verdict items — REVISION 9 scoped itself to the two
majors; R8 had recommended folding its three minors while the document was open):
R8 minors E-a (§7.2 licensability-gate quantifier), E-b (reach-pass/backfill artifact
relation), and S-c (m0239 NAMED CHECK executor) appear carried unchanged — the NAMED
CHECK still names no executor. These remain on the record for the next full review.

## Overall assessment: READY-FOR-NEXT-STEP

Both R8 majors are FIXED-CORRECT with the fixes mechanical (checkable, not descriptive),
pre-registered in the bar's own text, and mutually consistent; no FIXED-WITH-CONCERN or
NOT-FIXED items. Per the design's own §9, this does not open the cycle: the clean
re-review, the D2/D5 rulings, and receiver readiness still stand ahead.

— End of tier-2 verification.
