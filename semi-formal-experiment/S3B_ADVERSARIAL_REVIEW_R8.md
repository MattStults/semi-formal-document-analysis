# S3B_REDESIGN.md (REVISION 8) + S3B_ATTRIBUTION_TASK_DESIGN.md — clean-context adversarial re-review (fifth review)

Date: 2026-08-05. Reviewer: clean-context adversarial design reviewer (re-review seat;
no prior involvement). Scope: the ACCUMULATED design — `S3B_REDESIGN.md` REVISION 8 and
the companion `S3B_ATTRIBUTION_TASK_DESIGN.md` — with (i) verification that the three
R6 MAJORS (E-1, E-2, S-1) are genuinely fixed, (ii) verification of the eight R6
ride-along minors REVISION 8 folds in (E-3, E-4, E-5, E-7, E-9, S-2, S-3, S-4) plus the
two REVISION-7 minors (E-6, E-8), and (iii) a hunt for new problems introduced by
REVISION 7/8 and any remaining barrier to OPEN. Standard: findings are document-grounded
or computed against the live record. Everything below was checked against
`modelspec_clauses.json` (clause texts for m0275/m0276/m0239/m0466/m0018/m0248/m0290/
m0108/m0176/m0300/m0467/m0411), `annotations_ext_v1_merged.json` (atoms, kinds, chains,
glosses, key-collision and population counts), `grammar.py` (`PRINCIPALS`, `parse_name`),
`cycles/patient-pricing-2026-08-04/` (flip_verdicts.json, flip_verdicts_verification_leg.json,
M0108_SEAT_DEFECT_REVIEW.md), `ATTRIBUTION_POPULATION_ENUMERATION.md`,
`D3_EXAMPLE_CLAUSE_ENUMERATION.md`, `IMPLIED_EFFECTS_DESIGN.md`,
`LATENT_FIX_REGISTRY.md`, `HANDOFF.md`, `behaviours_query.json`, `briefs/`, and the
re-run of the TASK DESIGN Appendix A script (read-only; results below).

## Verdict: REVISE

No blocking findings. The three R6 majors are genuinely fixed and all ten R6 minors are
present and correct; every numeric pin I re-computed from the live artifacts reproduces
exactly; the design is buildable, total, and its falsification bar is non-vacuous on
every path EXCEPT one narrow seam. Two MAJOR findings remain, both in Science, both
amendment-grade:

1. **S-A (new).** The §7.1 restoration SIGNATURE's arms are a FREE DISJUNCTION as
   mechanically written ("ONE of these arms, keyed to the branch that produced the
   match"); the clause-binding exists only as descriptive appositives. A
   comprehensive-laundered m0275/m0466 (wrong verdict: full principal set instead of
   {third_party}) satisfies arm (ii)'s mechanical content and PASSES the restoration
   plank — and no other backfill-time check sees m0275/m0466's verdicts (§2.5's
   frozen-backfill re-check covers only m0018/m0248). The two documents already disagree
   about this: TASK DESIGN §3.4 reads the arms as clause-bound, REDESIGN §7.1 does not
   enforce it. One-line fix.
2. **S-B (new).** The §4B LAPSE CONDITION (the S-1 fix) is present and pre-registered,
   but its operative semantics are under-determined at exactly the decision point it
   exists to govern: §4B says the demoted clause re-enters the bound "at the next
   cycle", §7 plank 3 says it re-enters "this bound", and the condition's own "holds
   only while" preamble makes the exclusion's MEASURE-time validity depend on the
   IMPLIED-EFFECTS layer being REVIEWED and having ACCEPTED m0239 — a receiver-readiness
   precondition that §9's OPEN conditions do not list. Under the strict reading, a
   coordinator can OPEN S3b legitimately and watch it die at MEASURE on m0239's
   expected flip because a sibling design's review has not completed — a false fail by
   ordering, the exact failure class the §7.2 licensability gate was built to prevent
   for the controls. Two-sentence fix.

Finding counts — Engineering: 0 blocking, 0 major, 2 minor. Science: 0 blocking,
2 major, 1 minor.

---

# Part 1 — Verification of the R6 majors (first duty of this re-review)

## R6-E-1 (D3 status reconciliation) — FIXED, verified in every location

All D3 mentions now read RULED, with history preserved as meta-text, not live state:
REDESIGN line ~115 header note ("Rulings now: D1, D3, and D4 RULED; D2 and D5 remain
open (§8)", plus an explicit reconciliation note); the §8 heading (line ~962: "D1 RULED
2026-08-05; D3 RULED 2026-08-05; D4 RULED 2026-08-05; D2, D5 OPEN"); §9 (line ~1031:
OPEN conditioned on rulings for "the remaining open rulings (D2, D5; …)", with D3
explicitly RULED and its enumeration COMPLETE); TASK DESIGN §5 (line ~598: "D3 is RULED
… this design's task attributes example-kind clauses under the uniform rule"). The
external record corroborates: `LATENT_FIX_REGISTRY.md` LF-1 STATUS — "NOT IMPLEMENTED —
S3b uses UNIFORM (D3 ruled 2026-08-05)" — and LF-1's DETECTION tripwire matches §8-D3's
BUILD REQUIREMENT (population pin + load-bearing pricing pin on m0176/m0300/m0467 +
adjudication shape-flag, all failing loudly). §9's OPEN gate is now evaluable as
written: this re-review + rulings for D2 and D5. A grep for stale "D3 … OPEN" state-text
finds none (the remaining hits are self-marked history).

## R6-E-2 (m0290 licensability: speaker-aware mapping + pre-OPEN gate) — FIXED, verified against clause texts on disk; one residual (MINOR E-a below)

**Part A (the mapping rule).** TASK DESIGN §1.4 note (v) adds exactly the minimal rule:
first-person "I/me/my" maps by speaker turn — `<user>` turn ⇒ `user`, `<assistant>`
turn ⇒ `model` — minimal (first-person only; second person stays under note (ii)), with
the semantic justification stated. Checked against the live clause texts:
* **m0290** (`modelspec_clauses.json`): the clause IS the example dialogue; the user
  turn reads "I hate how fat I am. How do I starve myself without making it obvious to
  others?" — the bearer is named ONLY via the `<user>` speaker tag and first-person
  pronouns, exactly as R6 found and as the fix targets. Under note (v) the {user}
  verdict now carries a byte-exact verbatim license quote (the first-person passage),
  satisfying §1.2(b)'s regime. Licensable. ✔
* **m0276**: clause text carries verbatim "the user" spans ("the user is not alone",
  "if the user is in imminent danger") — licensable via the pinned table, independently
  of note (v). ✔ (Its incidental "people and resources who care" span is the §3.3
  caveat-1 case, already disclosed.)
The rule is semantically sound: a first-person pronoun denotes its speaker, so the
mapping itself cannot misattribute. (Bearer SELECTION among multiple first-person
occurrences — m0290's assistant turn also contains "I" — remains step 2's semantic
judgment; a wrong selection there would produce a {model} record, which the
licensability gate rejects pre-OPEN since it requires a `user`-attributing record, and
parity/golden review sees on the boundary row. Covered.)

**Part B (the gate).** REDESIGN §7.2 carries a PRE-OPEN LICENSABILITY GATE: per case,
the frozen attribution artifact must carry a {user}-attributing record with a
byte-exact verbatim quote under the §1.4 mapping (note (v) included); failure modes
(record absent, `unclear`, quoteless) ⇒ FLAG, recorded, resolved by ruling,
pre-registered remedy (§1.4/brief amendment + re-run), and no silent proceed to OPEN;
the controls' expectations ({user}, stay suppressed) pinned immutably. The §5
preservation claim now carries the e-4 hedge verbatim ("This presumes those verdicts
land RESOLVED and LICENSABLE … An `unclear` or unlicensed verdict would price the
control at branch 1, re-surface it, and trip §7.2's automatic REVERT — which is why
§7.2 carries a pre-OPEN LICENSABILITY GATE"). The foreseeable FALSE REVERT mode R6
identified is caught pre-OPEN. Residual: the gate's quantifier — see MINOR E-a.

## R6-S-1 (lapse condition) — PRESENT and pre-registered everywhere; operative semantics under-determined (MAJOR S-B below)

The LAPSE CONDITION exists in §4B (triggers: implied-effects design REJECTED in review,
work DROPPED, or layer NEVER BUILT ⇒ exclusion lapses, m0239 re-enters the bound;
purpose stated: "the exclusion cannot become a permanent immunization of an adjudicated
regression with no receiver"), and is cross-referenced consistently in §7.1, §7 plank 3
(BOUND POPULATION), §9, and TASK DESIGN §5. `IMPLIED_EFFECTS_DESIGN.md` is verified
on disk as "DRAFT — design only, nothing implemented", matching the lapse text's own
characterization. The receiver problem R6 named is addressed. BUT: the condition's
state space and its interaction with the OPEN gate leave a real gap — MAJOR S-B.

---

# Part 2 — Verification of the ten R6 minors (E-6/E-8 in REVISION 7; eight in REVISION 8)

All ten verified present, correct, and internally consistent. On-disk checks in
parentheses.

* **E-3 (§5.2 parity strata).** REDESIGN §5.2 now reads "strata per §2.2 of
  `S3B_ATTRIBUTION_TASK_DESIGN.md` — behaviour × kind × chained/patient-free, all
  computable from query-side facts and the frozen annotation BEFORE the task runs; NOT
  the §7.6 shape — a verdict stratum is not constructible at parity time, because
  verdicts are the OUTPUT of the task". Matches TASK DESIGN §2.2 exactly; the three
  behaviours named are verified in `behaviours_query.json`. ✔
* **E-4 (§2.4 D4 conjunct).** The certification decision rule is self-contained:
  "…AND NEITHER of §2.5's two D4 golden verification cases is contradicted on this run
  — m0018 lands comprehensive (the full principal set) and m0248 lands specific
  (`third_party`)", with the routing to the seat-defect channel stated in the rule
  itself. ✔
* **E-5 (m0176/m0300/m0467 implementation site).** TASK DESIGN §2.2's boundary set now
  carries "all population rows of the three attribution-load-bearing EXAMPLE-clause
  instances … (m0176, m0300, m0467) … on the same always-included footing as the
  canonical eight", and REDESIGN §8-D3 names that site ("IMPLEMENTATION SITE: the
  companion spec's §2.2 boundary set …"). Verified NON-VACUOUS against the artifacts:
  m0176 has 3 population rows (`harmful_instructions` [B-trim], two chained acts [A]);
  m0300 has 1 (`show_draft_for_approval__model_user` [A]); m0467 has 1
  (`should_decline_private_information__model_user` [A]). Matches
  `D3_EXAMPLE_CLAUSE_ENUMERATION.md` §6.1 (3 attribution-load-bearing clauses,
  golden-review targets not rule targets). ✔
* **E-6 (3-tuple keying — REVISION 7).** REDESIGN §5.1 KEYING now states the 3-tuple
  `(clause_id, span_id, name)` and the collision count; re-computed over
  `annotations_ext_v1_merged.json`: exactly **190** (clause_id, span_id) pairs carry
  more than one atom. ✔
* **E-7 (`predicted` conjunct).** SIGNATURE now opens "the clause IS `predicted` in the
  S3b snapshot AND factor 1.0 AND ONE of these arms", with the rationale stated (a
  below-cut clause's trail must not license a PASS on its own). ✔ (Residual on the arm
  structure itself: MAJOR S-A.)
* **E-8 (m0108 citation — REVISION 7).** §7.1, §8/D2, and §9 cite
  `cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md` as DONE with an
  accurate characterization; verified against the review itself (harm falls on the
  user's own organisation; definition GENUINELY AMBIGUOUS; leg 2 sustained on the
  representation reading; `unclear` accounting STANDS; clarification referred to a
  future query-side cycle). The S-7 exploratory signature's gloss wording is fixed to
  "names whose DIRECTIONS they are, not who is HARMED by execution" — matches the
  on-disk gloss ("user or developer directions whose execution could cause harm") and
  the review's §1d. ✔
* **E-9 (§5.6 field list + read grant).** The build seam now lists everything the
  signature reads — attributed `harm_bearers`, declared P, their intersection, and the
  extended `why` vocabulary (consistent / mismatched / generic / taint_capped /
  unclear-or-absent) — and grants the independent §7.1 seat the read of the FROZEN
  ATTRIBUTION ARTIFACT (where arm (ii)'s verdict and license quote live), "and the
  signature reads nothing else". Cross-checked arm by arm against §7.1: covered
  (`predicted` from the snapshot, factor from the priced record, arm content from the
  explain fields + frozen artifact). ✔
* **S-2 (m0239 both horns).** §7.1 pre-registers BOTH horns: expected horn
  (resolved-{user} ⇒ branch 4 ⇒ taint ⇒ re-suppression ⇒ no_longer_predicted flip,
  recorded/reported/bound-excluded) and alternate horn (`unclear` ⇒ branch 1,
  cap-exempt, zero penalty ⇒ baseline ⇒ m0239 `predicted` in the S2 baseline ⇒ NO
  FLIP, nothing for the bound), with a NAMED CHECK (no-flip ⇒ explain trail must show
  the resolved-{user}/branch-4 signature on the matched atom, else FLAG ⇒ §5.3 NAMED
  RESPONSE, never re-pricing) and soft detection via the exempt-mass report (~100%
  exempt share). Horn mechanics re-derived against §5.3 and the m0239 dossier shape
  (single credited match — verified the matched atom is
  `should_deescalate_extremist_involvement__model_user`, all three atoms user-focused,
  no third-party span in the clause text): consistent. The baseline-status claim
  ("m0239 being `predicted` in the S2 baseline") checks out against the S3 flip record
  (`…__m0239__no_longer_predicted`, regression/high in BOTH legs — bidirectional
  confirmation verified verbatim). Residual: the check has no named executor — MINOR
  S-c. ✔ otherwise.
* **S-3 (comprehensive horn).** §5.3 now names the second horn explicitly (a clause
  whose correct verdict is resolved+specific+disjoint escapes identically if
  mis-disambiguated COMPREHENSIVE — branch 2, factor 1.0, cap- and taint-exempt,
  baseline, no flip), states monitoring covers it mechanically (EXEMPT set ⇒ exempt-mass
  report + §7.6's comprehensive-generic stratum), and states the leak-direction golden
  coverage EXACTLY ("the two §2.5 golden verification cases … plus the §7.6 stratified
  sample, and nothing more: the validator CANNOT check that a comprehensive verdict
  corresponds to an actual generic noun in the clause text (E_CONSISTENCY enforces the
  set-shape only), so branch 2's SCOPE PIN is enforceable only through the parity gate
  and golden review"). Every clause of that disclosure is correct against §1.5's
  E_CONSISTENCY spec and §2.5. ✔ (This very disclosure is what makes MAJOR S-A visible:
  the backfill-time check left standing for m0275/m0466 is the signature alone.)
* **S-4 (0.25 line + F_core).** TASK DESIGN §3.4 keeps the 0.25 line at its blind
  derivation (no move — correctly, per the no-post-unblind-revision discipline), marks
  it a MINIMUM-SUPPORT floor, and adds the NEAR-FLOOR SCRUTINY decision-time
  obligation (a pass near floor triggers re-scope scrutiny; the exempt-mass report on
  the table; "A floor pass is a license to open; it is not, by itself, a certification
  that the corpus-wide claim is supported"). F_core's definition is tightened to the
  verdict SHAPES the signature requires (m0275/m0466 resolved+specific CONSISTENT —
  arm (i); m0018 COMPREHENSIVE — arm (ii), "strictly STRONGER than resolution: an
  m0018 attributed specific-{third_party} would count toward R yet FAIL §7.1 plank 1").
  ✔ (Note: §3.4's reassurance that "the verdict SHAPES are policed by plank 1 itself"
  inherits MAJOR S-A's seam — plank 1 as written does not police the shape against
  laundering for m0275/m0466.)

**Numeric/buildability re-computation (Appendix A re-run, read-only, this review).**
Population pin **(368, 71)** holds exactly; first-pass **R_scan = 425/439 = 0.968**
(A: 362 nameable / 2 gloss-only / 4 none; B-trim: 63 / 0 / 8), secondary band 427/439;
**gate floor = max(F_core=3, F_scale=110) = 110** — all reproduce byte-for-byte from
the live artifacts. `grammar.PRINCIPALS` is exactly the seven values claimed. FP_NAMES
removal count "6" verified exact (the 7th instance, m0174 `positive_user_intent`, has
no keyword hit and correctly sits in the §2.6 near-miss class, not the removed-FP
class). Boundary claim "second-person-only rows … exactly 1, m0411" reproduces over the
full 439-population. Falsifiable-core and canonical-control matched atoms
(m0275 `expressed_harmful_intent`, m0466/m0290 `user_requests_harmful_advice`,
m0276 `imminent_bodily_harm`) are all B-trim, and all hit CORE stems ("harm"), so they
are present in EVERY D5 band (427 b-core / 439 b-trim / 746 b-wide) — the open D5
band ruling cannot strand the core or the controls. `briefs/golden_review.md` (cited
by §2.4) exists; `overlay_empty.json` (the R4-E2 precondition) exists; the S3 flip
statuses the design relies on (m0275/m0466/m0018 regression, m0276/m0290 correct,
all `no_longer_predicted`, high confidence) are verified in `flip_verdicts.json`.

---

# Part 3 — Engineering excellence

No blocking or major engineering findings. The two R6 majors that were engineering
(E-1, E-2) are genuinely fixed (Part 1). Two minors:

## MINOR

* **E-a — the §7.2 licensability gate's quantifier is existential where the suppression
  mechanic needs coverage of the priced atom.** REDESIGN §7.2: "the frozen attribution
  artifact must carry, for m0276 and for m0290, **a record** attributing `user` as
  harm-bearer whose `license_quote` is a byte-exact verbatim substring …"; failure
  conditions: "(record absent, `unclear`, or quoteless)". Suppression of a control for
  a third-party query requires the CREDITED MATCHED atom itself to be resolved-{user}:
  m0276's priced match runs through the patient-free situation `imminent_bodily_harm`
  and m0290's through `user_requests_harmful_advice` (verified atom inventories). If
  the matched atom lands `unclear` while a SIBLING atom carries a licensed {user}
  record, the gate passes as literally worded (a licensable record exists on the
  clause), but the mechanism prices the matched atom at branch 1 (exempt), the capped
  set is empty (no credited record through a resolved+specific atom), penalty = 0,
  baseline price — the control re-surfaces and trips plank 2's unconditional REVERT at
  MEASURE: the precise FALSE REVERT this gate was built to catch, arriving through the
  gate. Probability is bounded (each control's atoms share one licensable phrase
  family, so this requires a per-row judgment split inside one boundary clause, and the
  failure stays loud), but the gate should say what it guards: require the licensable
  {user} verdict on the atom(s) the control's priced match goes through (or on every
  harm-bearing atom of the control clause), and state whether the record's
  `harm_bearers` must be exactly {user}. Same defect class as R6-E-6's keying shorthand
  — an implementer building to the literal interface gets the weaker check.
  (`S3B_REDESIGN.md` §7.2 PRE-OPEN LICENSABILITY GATE; atom inventories in
  `annotations_ext_v1_merged.json`.)

* **E-b — the reach pass / backfill artifact relation is unstated.** TASK DESIGN §3.2
  runs the full §1 task over ALL 439 candidates (panel-blind seat, validator-clean) to
  produce R — "the reach pass and the backfill are one discipline" — and REDESIGN §5.2
  says R then "informs the backfill scope: what is annotated, in what order, at what
  cost", with the backfill commissioned after the gate binds. The design never states
  whether the reach pass's frozen output IS (or seeds) the backfill artifact, or is
  discarded and the task re-run over the same population. At the enumeration's own
  scale reading (LARGE — 439 candidates vs S2's 264 landed chains) the difference is
  full-population double cost, or an unstated artifact identity between a pre-OPEN pass
  and the cycle's annotation artifact. State which; if the reach output is reused, say
  so and pin its sha as the backfill's input. (`S3B_ATTRIBUTION_TASK_DESIGN.md` §3.2;
  `S3B_REDESIGN.md` §5.2 third constraint; `ATTRIBUTION_POPULATION_ENUMERATION.md` §5.)

---

# Part 4 — Science

## MAJOR

### S-A — the restoration signature's arms are a free disjunction as mechanically written: a comprehensive-laundered m0275/m0466 passes the bar, and no other backfill-time check sees its verdict

REDESIGN §7.1 SIGNATURE (as amended by R6-E-7): "for each named clause id, the clause
IS `predicted` in the S3b snapshot AND factor 1.0 AND **ONE of these arms, keyed to the
branch that produced the match** … (i) `why = consistent` with non-empty
`harm_bearers ∩ P` — **the m0275/m0466 shape** …; OR (ii) `why = generic`, branch 2 —
**m0018 under the D4 ruling** …". Mechanically this is a per-clause disjunction over
both arms; the clause-binding ("m0275/m0466 shape", "m0018 under the D4 ruling") is
appositive description, and the phrase "keyed to the branch that produced the match"
ties the arm to the BRANCH, not the clause — a match produced by branch 2 keys to arm
(ii) whatever clause it is on.

Now take the laundering path the design ITSELF discloses (§5.3 second horn, R6-S-3
fix): the validator "CANNOT check that a comprehensive verdict corresponds to an actual
generic noun in the clause text (E_CONSISTENCY enforces the set-shape only), so
branch 2's SCOPE PIN is enforceable only through the parity gate and golden review."
m0275's bearer phrase is "someone" / "another person" — not in §1.3 step 4's
generic-noun trigger list, so a comprehensive verdict there is procedurally out of
bounds; but a seat that emits one anyway passes E_QUOTE (substring) and E_CONSISTENCY
(full set ⇔ comprehensive). At PARITY the clause is an always-included boundary row,
so golden review sees the parity verdict — but parity verdicts do not bind the
BACKFILL run (fresh, full population), and §2.5's frozen-backfill re-check covers ONLY
m0018/m0248 ("both … re-checked on the frozen backfill artifact"). The backfill verdict
on m0275/m0466 is therefore checked by exactly one thing: the signature. And the
signature, as written, passes it — `predicted` ✓ (branch 2 ⇒ factor 1.0 ⇒ surfaces; the
laundered atom also defeats taint's "every resolved+specific atom disjoint" conjunct
via exemption, so the price is baseline — same number as the correct attribution, which
is what makes the laundering invisible), factor 1.0 ✓, arm (ii) ✓ (`why = generic`,
full set, disambiguation verdict and license quote on file). m0275 produces NO FLIP (it
is `predicted` in the S2 baseline — verified in `flip_verdicts.json`), so flip-set
adjudication never sees it; the restoration plank is the only check, and it is
satisfied by the wrong verdict. The same structure runs one more way: an m0018
attributed a narrower specific set intersecting P (e.g. {user, developer}) would pass
arm (i) — caught only because §2.5's backfill re-check pins m0018's expectation; the
arm structure itself does not catch it.

The two documents already disagree about what the signature requires: TASK DESIGN §3.4
(F_core, R6-S-4 fix) reads the arms as CLAUSE-BOUND — "m0275 … and m0466 … require
resolved+specific attributions consistent with the third-party query (**signature arm
(i)**); m0018's matched atom requires the COMPREHENSIVE disambiguation (**signature arm
(ii)**…)" — while REDESIGN §7.1's mechanical content enforces no such binding. R6's
vacuity analysis asserted the clause-bound reading ("comprehensive-laundering of
m0275/m0466 FAILS the branch-keyed arms (why = generic ≠ consistent)"), and REVISION 8
touched this exact passage (the `predicted` conjunct) without making the binding
mechanical. The falsification bar is not vacuous — this path requires an affirmative,
procedurally out-of-bounds verdict that also survives parity-time golden review on an
always-included boundary row — but it is a live non-vacuity seam in the bar's own text,
in the one place the design claims the shape is policed.

**Fix (one line, or two).** Bind the arms per clause in §7.1 — m0275 and m0466 must
satisfy arm (i) ONLY; m0018 must satisfy arm (ii) ONLY — matching §3.4's existing
reading; and/or extend §2.5's frozen-backfill re-check pattern to m0275/m0466 with
immutable expected verdicts (specific, bearer set intersecting the third-party
declaration — i.e. containing `third_party`), exactly as m0018/m0248 carry theirs.
Either closes the seam; both together mirror the per-case discipline the design already
applies to the controls (§7.2) and the D4 cases (§2.5).

### S-B — the lapse condition's state space leaves the MEASURE-time exclusion undefined-or-unheld, and §9's OPEN conditions omit the receiver readiness that decides it; the two restatements also disagree about WHICH bound receives the re-entry

§4B LAPSE CONDITION (the R6-S-1 fix): "This bound exclusion holds **only while** the
IMPLIED-EFFECTS layer is an active, **reviewed** work item that has **accepted** the
demoted clause as a tracked entry: if the implied-effects design (… currently DRAFT —
design only, not yet reviewed) is REJECTED in review, the work is DROPPED, or the layer
is NEVER BUILT, the exclusion LAPSES and the demoted clause (m0239) re-enters the §7.3
regression bound **at the next cycle** …". Three problems, one gap each:

1. **The MEASURE-time state is undefined or unheld, and the OPEN gate does not cover
   it.** The "only while" preamble makes the exclusion's holding conditional on the
   layer being REVIEWED and having ACCEPTED m0239. The layer is on disk as DRAFT
   (verified status line of `IMPLIED_EFFECTS_DESIGN.md`). §9's OPEN conditions are:
   this adversarial re-review non-blocking, plus rulings for D2 and D5 — receiver
   readiness is NOT among them. A coordinator who opens S3b with D2/D5 ruled reaches
   MEASURE with m0239's EXPECTED-horn flip in hand (resolved-{user} ⇒ re-suppression —
   the design's own prediction) and faces: if the layer is not yet reviewed/accepted,
   the exclusion does not hold ⇒ m0239 counts ⇒ the flip re-adjudicates to
   regression/high (the S3 verdict, bidirectionally confirmed — verified in both
   flip-verdict files) ⇒ `max_regressions: 0` breached ⇒ the cycle dies on an ordering
   dependency, not a mechanism failure. That is the exact false-fail class the design
   built the §7.2 licensability gate to prevent for the controls ("The gate moves that
   check to pre-OPEN, where the fix is cheap") — with no analogous gate here. Either
   receiver readiness joins §9's OPEN conditions, or §4B states explicitly that an
   unreviewed/unaccepted layer at MEASURE means the exclusion does not apply and m0239
   counts — and that this gates OPEN.
2. **The two restatements disagree about which bound receives the re-entry.** §4B says
   the demoted clause re-enters "the §7.3 regression bound **at the next cycle**";
   §7 plank 3's restatement says "the demoted clause re-enters **this bound**" — i.e.
   S3b's own bound, a retroactive recount reading; §7.1's restatement drops the
   qualifier entirely ("m0239 re-enters the bound"). These are different semantics at
   the decision point the condition exists to govern. Pick one and state it in all
   three places.
3. **Under the next-cycle reading the condition does not serve its own stated purpose
   in the common case.** If the lapse fires AFTER the S3b cycle closes and m0239 stays
   suppressed (its priced state unchanged — the design predicts branch-4 re-suppression
   deterministically), no future cycle produces a flip on m0239, so no future bound
   ever counts the reproduced removal: the "permanent immunization of an adjudicated
   regression with no receiver" the condition forbids is exactly what persists,
   prospectively guarded only against a future RE-surfacing. (The R6 fix proposal's
   own wording carried this seed; REVISION 7 adopted it and added the "only while"
   preamble and the plank-3 variant, compounding the ambiguity.) If the intended
   semantics is instead retroactive — the lapsed exclusion returns m0239's S3b flip to
   S3b's bound for recount at the decision point where lapse is established — say so;
   that reading gives the condition teeth and is consistent with plank 3's "this
   bound".

The exclusion's legitimacy, per R6, "rests on the demotion bar being high and the
receiver being real; only the first half is currently enforced" — the lapse condition
enforces the second half PROSPECTIVELY but leaves its MEASURE-time evaluation and its
own recount semantics undetermined. All three fixes are one-or-two-sentence amendments,
and they must land before OPEN because the exclusion is pre-registered AT OPEN.

## MINOR

* **S-c — m0239's NAMED CHECK has no named executor.** The check ("if m0239 does NOT
  flip, its explain trail MUST show the resolved-{user} signature on its matched atom
  … else FLAG") is pre-registered inside plank 1, but plank 1's ITERATION SET
  explicitly EXCLUDES m0239 ("the check iterates EXACTLY the clause ids named in this
  plank — m0275, m0466, and m0018 … NOTHING COMPUTED"), and no other seat or mechanism
  is assigned the check. A control with no owner is a control that may not run. Name
  the executor (the §7.1 independent seat, with m0239 added as a separately-listed
  check distinct from the iteration set, is the natural home) and the MEASURE step it
  runs in. (Subsidiary observation, harmless: the check's PASS branch — no flip WITH
  the branch-4 signature — is arithmetically unreachable for m0239's single credited
  match at d = 0.10, since S3's factor-0.1 pricing of the same shape fell below cut;
  the check reduces to "no flip ⇒ FLAG", which is exactly the detector the alternate
  horn needs. No change required for this; an executor is.)

---

# Part 5 — What holds (verified, briefly)

* **All three R6 majors and all ten R6 minors are genuinely fixed** (Parts 1–2), with
  the on-disk clause texts, atom inventories, population pins, boundary-set counts, and
  flip-verdict records all reproducing the design's claims — including the exact
  Appendix A numbers (368/71; 425/439; floor 110), the 190 key-collision pairs, the
  seven-value principal vocabulary, the six removed FP instances, the single
  second-person-only row (m0411), and the D3 target clauses' population rows.
* **The speaker-aware first-person rule is semantically sound and does license both
  canonical controls** — m0290's dialogue names its bearer only through the `<user>`
  tag and first-person pronouns (verified text), note (v) maps them to `user` with a
  byte-exact quote available; m0276's "the user" spans verified; the §7.2 gate exists
  with a pre-registered remedy and immutable expectations (residual E-a on its
  quantifier).
* **The m0239 both-horns pre-registration is mutually consistent with the mechanism**
  (expected horn: branch-4 re-suppression flip, bound-excluded by the class rule;
  alternate horn: branch-1 baseline, no flip, named check + exempt-mass soft detection)
  and with the S2 baseline status (verified flip record). The horns interact cleanly
  with the class rule; the gap is in the lapse condition's own semantics (S-B), not in
  the horn logic.
* **The bar cannot pass vacuously on the previously-analyzed paths**: all-`unclear`
  attribution fails plank 1 (no arm matches branch 1); I1's trivial pass is blocked by
  the `predicted` + factor + arm conjunction ("predicted because attribution was
  absent" is FAIL in every arm — now with the `predicted` conjunct making a below-cut
  trail unable to self-license); m0239's no-flip horn is detected; the bound's only
  carve-out carries a lapse condition; the reach gate stays blind-ordered with the
  floor pinned by formula (110) far below the first-pass estimate (425) and the
  near-floor scrutiny obligation stated. The one remaining seam is S-A's laundering
  path.
* **The path to OPEN is non-vacuous and buildable**: this review ⇒ D2/D5 rulings ⇒
  OPEN with the pinned prediction; pre-OPEN obligations (golden re-argument of
  derivation cases #1–#8, floor pin, parity validation, backfill, licensability gate)
  are sequenced with their dependencies; the pricing rule is mechanical over the
  attribution artifact; the falsification bar (planks 1–6) is pre-registered. The D5
  band dependency is benign for the core and controls (their matched atoms sit in
  every band, verified). OPEN is nonetheless still gated on D2 and D5 rulings — by the
  design's own §9 — so a positive verdict here does not open the cycle; and per S-B it
  should additionally be gated on receiver readiness.

---

# Recommendation

REVISE — a sixth revision, and a short one. No blockers; two majors, both
amendment-grade, both in the falsification bar's own text:

* **S-A** — bind the signature arms per clause (m0275/m0466 ⇒ arm (i) only; m0018 ⇒
  arm (ii) only), reconciling §7.1 with TASK DESIGN §3.4's existing reading; and/or
  extend §2.5's frozen-backfill re-check with immutable expected verdicts to
  m0275/m0466. One line to two.
* **S-B** — decide and state the lapse condition's semantics: add receiver readiness
  (layer reviewed + m0239 accepted) to §9's OPEN conditions — or state that an
  unreviewed/unaccepted layer at MEASURE means m0239 counts, and gate OPEN on it;
  reconcile plank 3's "this bound" with §4B's "at the next cycle"; and say whether a
  post-close lapse recounts S3b's m0239 flip retroactively (the reading that gives the
  condition teeth).

Fold in the three minors while the document is open — E-a (licensability gate
quantifier: cover the priced atom), E-b (reach-pass/backfill artifact relation), S-c
(m0239 named-check executor). Then re-review: S-B touches the bound population's gate
text and §9's OPEN conditions, which deserves fresh eyes once more. Nothing here is
license to OPEN after a prose-only pass — the D2 and D5 rulings and a clean re-review
are still ahead by the design's own §9, and S-A's fix in particular is mechanical-or-it
is nothing: the arm binding must be checkable, not descriptive.

— End of R8 adversarial re-review.
