# S3B_REDESIGN.md (REVISION 6) + S3B_ATTRIBUTION_TASK_DESIGN.md — clean-context adversarial re-review (fourth review)

Date: 2026-08-05. Reviewer: clean-context adversarial design reviewer (re-review seat;
no prior involvement). Scope: the ACCUMULATED design — `S3B_REDESIGN.md` REVISION 6 and
the companion `S3B_ATTRIBUTION_TASK_DESIGN.md` — plus verification of every fix REVISION 5/6
claim against `S3B_ADVERSARIAL_REVIEW_R4.md`. Standard: findings are document-grounded or
computed against the live record. Everything below was checked against
`cycles/patient-pricing-2026-08-04/` (decision.json, ADJUDICATION_LEGS.md,
DISCOUNT_DERIVATION.md, flip_verdicts.json, and the flip dossiers for m0275, m0276,
m0239, m0466, m0018, m0290, m0108 — `explain_b.patient_pricing` opened and compared),
`patient.py`, `containment.py`, `relevance.py` (scale conventions), `grammar.py`,
`modelspec_clauses.json` and `annotations_ext_v1_merged.json` (clause texts, atoms, spans,
key-collision counts), `briefs/backfill_author.md`, `briefs/README.md`, `HANDOFF.md`,
`IMPLIED_EFFECTS_DESIGN.md`, `D3_EXAMPLE_CLAUSE_ENUMERATION.md`,
`ATTRIBUTION_POPULATION_ENUMERATION.md`, `LATENT_FIX_REGISTRY.md`,
`M0108_SEAT_DEFECT_REVIEW.md`, and the three prior reviews.

## Verdict: REVISE

No blocking findings — the accumulated design is buildable, total, non-vacuous, and its
dossier-level diagnosis remains exact; all four R4 majors and the R4 blocker are genuinely
fixed. But three major findings keep it short of OPEN:

1. **E-1.** The document is SELF-CONTRADICTORY about whether ruling D3 exists: §8-D3
   records it as RULED (with grounds and a build requirement) while the REVISION-6 header
   note, the §8 heading, and §9 all still say D3 remains OPEN — and §9 conditions OPEN on
   rulings for the open set including D3. The OPEN gate cannot be evaluated as written.
2. **E-2.** The canonical control m0290's suppression claim is overstated: under the
   design's OWN strict verbatim-quote regime, m0290's clause text names the user only via
   the `<user>` XML speaker tag and first-person pronouns — neither covered by the §1.4
   mapping table — so the {user} verdict the §5 preservation claim presumes is not
   obviously licensable, and no per-case pre-OPEN gate protects the canonical controls
   (unlike the §2.5 D4 gate). The foreseeable failure mode is a FALSE REVERT of an
   otherwise sound cycle at MEASURE.
3. **S-1.** The R4-B1 class rule that excludes demoted clauses (m0239) from the
   regression bound is principled and correctly implemented, but "tracked by that layer
   instead" currently points at an UNREVIEWED DRAFT (`IMPLIED_EFFECTS_DESIGN.md`:
   "DRAFT — design only", "does not restore m0239 by itself"), and no LAPSE CONDITION
   is pre-registered: if the implied-effects layer is never built, the exclusion becomes
   a permanent immunization of an adjudicated regression with no receiver.

All three are amendment-grade (one paragraph or less each). Ten minors ride along,
including four R4-era minors that were not carried into REVISION 5/6.

Finding counts — Engineering: 0 blocking, 2 major, 7 minor. Science: 0 blocking,
1 major, 3 minor.

---

# Verification of claimed fixes (first duty of a re-review)

**R4-B1 → CLASS RULE (§4B, §7 plank 3 BOUND POPULATION, §7.1, §9) — FIXED, verified
principled.** The rule is stated generally (attaches to "clauses DEMOTED to the
IMPLIED-EFFECTS layer by ruling", no clause named in the rule body), pre-registered, and
its ground checks out against the record: m0239's removal was adjudicated
regression/high in leg 1 and BIDIRECTIONALLY CONFIRMED (ADJUDICATION_LEGS.md agreement
table; flip_verdicts.json), on a document-side, mechanism-independent reason
("Radicalization leads to violence against third parties…"), so re-adjudicating the same
removal can only return the same verdict — the "adds no information" ground is sound.
Pricing stays corpus-wide: §7.1 pre-registers the EXPECTED re-suppression
(attribution {user} ⇒ branch 4 ⇒ factor d ⇒ no_longer_predicted flip), recorded and
reported, excluded only from the bound count. The demotion preceded the bound question
(ruling (b), coordinator 2026-08-04, grounded in the verified absence of any third-party
span in m0239's clause text and glosses — dossier: all three atoms user-focused), so the
exclusion is a consequence of a scope ruling, not an ad-hoc immunization of a failing
clause. Residuals: MAJOR S-1 (no lapse condition; receiver is a draft) and MINOR S-2
(the unclear horn is not pre-registered).

**R4-E1 → cap composition (§5.3 SURVIVING MASS / CAPPED vs EXEMPT / PINNED TEST) —
FIXED, verified against patient.py.** The formula `(d · max(base_credit over CAPPED) +
Σ(base_credit over EXEMPT)) / atom_norm` is on ONE scale and matches the code's
mechanics term-for-term: `relevance._atom_score` returns `Σ(idf · kind_factor)/atom_norm`
(pre-weight; the 0.6 atom weight applies at channel composition — verified in
relevance.py:466,624-650 and dossier m0275's channels), `patient._atom_score` is
`base − penalty/atom_norm` with `penalty = Σ(base_credit − priced_credit)` over records
with factor ≠ 1.0, and `base_credit` on the records is raw idf × kind factor
(dossier m0275: base_credit 5.695414225). Dimensionally consistent; the R4 scale-mixing
defect is gone. "CAPPED = resolved+specific credited records (all branch-4 on a tainted
clause)" is correct by taint's definition; the survivor tie-break (highest base_credit,
ties lexicographic on (clause_atom, query_atom, match)) now re-stated verbatim from
`patient._patient_pricing`; empty-capped-set semantics stated (penalty 0, baseline
price). The pinned test asserts channel MASS for both variants (A: `unclear` — asserts
`(d·b_r + b_u)/N` and the equivalent penalty form; B: comprehensive generic — pins the
max-scope), which catches all three R4-E1 defects (scale mix, max over generics,
crushed exempt match). Decisive as claimed.

**R4-E2 → subsumption composition (§5.3 COMPOSITION WITH SUBSUMPTION) — FIXED.**
Subsumption records factor off the CREDITED CLAUSE ATOM's attribution record, enter
CAPPED/EXEMPT exactly as exact records, never-outprice preserved inside the min-idf-capped
credit (both discounts ≤ 1) — consistent with patient.py's "COMPOSITION WITH CONTAINMENT"
contract. The scope pin is real and verified latent: `overlay_empty.json` is in the S3
closure set (decision.json `gate.closure_checked`), S5 is "Not yet started" (HANDOFF ⭐⭐),
and S5 must re-review and re-pin with a priced subsumption record in its test surface
before reactivation. Totality claim now conditional on that pin, as it should be.

**R4-E3 → F-linearity scope + dense-unclear escape (§2.2, §5.3 EXEMPT-MASS DISCLOSURE)
— FIXED.** §2.2 is re-marked AMENDED, the F-linearity guarantee explicitly scoped to
RESOLVED mass, the one-sided flip-invisible escape disclosed (attribution errors/laziness
flow to `unclear` ⇒ branch 1 ⇒ baseline ⇒ never suppressed), and monitored by a
pre-registered MEASURE-time per-clause exempt-mass report + §7.6's `unclear` stratum +
the named response (top-of-list golden re-examination, never re-pricing). The exemption
is indeed forced (branch 1's "never as a discount" + I1 allow no other horn — R4's
analysis re-verified). Residual: MINOR S-3 (the disclosure omits the comprehensive horn,
which has the same one-sided shape).

**R4-S1 → §7.5 floor ordering (REDESIGN §7.5 THRESHOLD; TASK DESIGN §3.1/§3.4) — FIXED.**
The floor is a FORMULA over pre-known pinned quantities — F_core = 3 (the named
restorations, nameability verifiable panel-blind: "someone" spans verified present in
m0275/m0466 clause texts, "People" in m0018) and F_scale = ceil(0.25·D), the 0.25 line
derived blind from S2's on-disk precedent (264/692 ≈ 0.38, set below because harm-bearer
attribution is a harder question) — committed BEFORE any reach run, with the denominator
band pinned with D5, sha-pin + no-access attestation, and an explicit no-post-unblind-
revision rule (any change needs a blinded party + written re-derivation + re-pin). The
ordering is genuinely blind: the binding R is the seat-resolved count of §3.2, not the
scan; the disclosed §3.3 first-pass number (425) is labeled designer context, not a gate
input, and the floor (110) is pinned by formula so it cannot be re-set under 425 without
a review finding. Residual: MINOR S-4 (the 0.25 line sits in tension with the gate's own
qualitative criterion).

**D4 ruling — translation-time generic-noun referent disambiguation — CONSISTENT across
both files, collision resolved without inversion, verified against the artifacts.**
REDESIGN §4C / §5.3 branch 2 (redefined, mechanically keyed on `harm_bearers` = the full
seven-value principal set; SCOPE PIN: only comprehensive generics take it) / §7.1 arm (ii)
(`why = generic` + disambiguation verdict + license quote on file) / §8-D4 line up with
TASK DESIGN §1.2 schema (`"generic": "comprehensive"|"specific"|false`), §1.3 step 4
(comprehensive ⇒ full principal set, overriding the step-3 table; specific ⇒ table-mapped
party; undecidable ⇒ `unclear`), §1.4 note (iv), E_CONSISTENCY (comprehensive ⇔ full set;
specific ⇒ proper subset — so branch 2's set-keying is faithful to the record), and §2.5
golden cases. Ground truth checks: m0248's clause text ("…gratuitous abuse, harassment,
or negativity toward individuals…") and atom `shouldnot_engage_abuse__model_third_party`
verified in modelspec_clauses.json / annotations — SPECIFIC disambiguation gives
`harm_bearers = {third_party}`, disjoint from helpfulness's P = {user, developer} ⇒
branch 4 ⇒ factor d: golden derivation case #5 (DISCOUNT_DERIVATION.md §1/#5, judgment (b))
preserved, NOT inverted. m0018's single atom (chain [model, third_party], gloss "gives
people accessible and reliable information…") under COMPREHENSIVE disambiguation carries
the full set ⇒ branch 2 ⇒ factor 1.0, cap-exempt, surfaces for helpfulness. Per-occurrence
disambiguation means there is no global "generic ⇒ 1.0" rule — exactly what dissolves the
collision. The old arm (iii) is DEAD and the arm list fixed with the ruling (former R4
minor e-1 is moot). One residual: MINOR S-3.

**D3 ruling + LF-1 — substance consistent with the enumeration and the registry; STATUS
self-contradictory.** §8-D3's content matches `D3_EXAMPLE_CLAUSE_ENUMERATION.md` (183/183
handled, 0 wrong-result, 0 undefined; the three attribution-load-bearing ids
m0176/m0300/m0467 as golden-review targets; m0240 direction-safe via branch 1) and
`LATENT_FIX_REGISTRY.md` LF-1 (issue, evidence of absence, plan, trigger, DETECTION
tripwire, REVISIT note) line for line. BUT see MAJOR E-1 for the status contradiction,
and MINOR E-5: the ruling's golden-review directive has no implementation site in the
task design's boundary set.

**R4 minors carried: e-1 moot (arm (iii) dead with D4), e-3 FIXED (tie-break re-stated).
NOT carried: e-2 (§5.6 field list + explicit read grant), e-4 (preservation-claim hedge —
folded into MAJOR E-2), s-1 (`predicted` conjunct), s-2 (m0108 citation and wording).
See MINORS E-7/E-8/E-9.** The REVISION-6 header's "every fix retained intact" claim
enumerates the majors only, so this is not a false claim — but three ride-along items
from R4's recommendation are still open.

---

# Engineering excellence

## MAJOR

### E-1 — REVISION 6 is self-contradictory about whether D3 is ruled, and §9's OPEN gate lists D3 as unresolved

Four locations in `S3B_REDESIGN.md` say D3 is OPEN; one says it is RULED:

* Line 27 (REVISION 6 header note): "Rulings now: D1 and D4 RULED; **D3 remains OPEN
  (its enumeration is in flight)**; D2 and D5 remain open (§8)."
* Line 55: "…**D3 remains OPEN, its enumeration in flight.**"
* Line 773 (§8 heading): "(D1 RULED 2026-08-05; D4 RULED 2026-08-05; **D2, D3, D5 OPEN —
  not resolved here**)"
* Lines 829–830 (§9): "OPEN happens only after … the remaining open rulings **(D2, D3,
  D5**; D1 is ruled, §5.2, and D4 is ruled, §8) have rulings. **D3 remains an OPEN
  designer ruling — its enumeration is in flight — and is not resolved here.**"
* Line 785 (§8-D3): "**D3 — RULED (coordinator 2026-08-05): UNIFORM — no distinct
  example-kind rule.**" — with grounds, the LF-1 registration, and a BUILD REQUIREMENT
  (the LF-1 DETECTION tripwire ships with the S3b build's test set).

The external record corroborates RULED: `LATENT_FIX_REGISTRY.md` LF-1 STATUS — "NOT
IMPLEMENTED — S3b uses UNIFORM (D3 ruled 2026-08-05)" — and its Origin line ("coordinator
ruling on D3 … Matt directed that such plans be registered here"). The companion spec
carries the same stale text: `S3B_ATTRIBUTION_TASK_DESIGN.md` §5 — "It does not rule
D2/D3 (**open in `S3B_REDESIGN.md` §8; D3's enumeration is in flight**)".

Why it is major, not editorial: §9 is the operative gate text for opening the cycle, and
it conditions OPEN on rulings for a set it claims still includes D3, while §8 claims D3
is ruled. A coordinator following §9 holds the cycle open awaiting a ruling that §8 says
exists; a coordinator following §8 opens on the remaining D2/D5. In this project's
discipline ("Rulings go in the repo, not the transcript"; a decision must be written with
its grounds), a self-contradiction about WHETHER a ruling exists at the OPEN gate is a
record-integrity defect, not a typo. **Fix.** Reconcile all four stale locations to the
ruled state (header note, §8 heading, §9's open set, TASK DESIGN §5), or — if D3 was not
in fact ruled — strike §8-D3's ruling text and LF-1's status line. The fix is one edit;
the review must be able to read the gate state without external investigation.

### E-2 — the canonical control m0290's suppression is not demonstrably licensable under the design's own quote regime; the §5 preservation claim overstates it, and no per-case pre-OPEN gate protects the canonical controls

The §5 preservation claim (`S3B_REDESIGN.md` §5, "What this preserves"): "m0276 and m0290
stay suppressed because, once attribution exists, their harm-bearing atoms attribute the
USER as harm-bearer, disjoint from a third-party P." For m0276 this is cleanly licensable
— its clause text carries verbatim "the user" spans ("the user is not alone", "if the
user is in imminent danger", verified in modelspec_clauses.json). For m0290 it is not:
the clause text is the example dialogue "I hate how fat I am. How do I starve myself
without making it obvious to others?" — the only occurrence of "user" in the entire text
is the `<user>` XML speaker tag (verified). TASK DESIGN §1.2(b) requires `license_quote`
to be "an EXACT verbatim substring of that row's clause text naming the bearer(s)", and
§1.4's mapping table covers neither XML speaker tags nor first-person pronouns (note (ii)
addresses second person only). So the verdict the preservation claim presumes — {user},
RESOLVED, branch 4 + taint — has no licensable quote under the brief as written: the
strict seat's options are quoting the `<user>` tag (byte-exact but semantically a speaker
label, not a "noun phrase the harm falls on" per §1.3 step 2 — acceptability undecided by
the brief) or answering `unclear`. If `unclear`: no resolved+specific atom on m0290 ⇒ no
taint (existential import) ⇒ the clause prices at baseline ⇒ m0290 re-surfaces ⇒ §7.2
plank 2 fires ("If either re-surfaces, REVERT regardless of all else").

Three aggravating facts:
1. **The confidence is borrowed without the quote discipline.** `D3_EXAMPLE_CLAUSE_ENUMERATION.md`
   §2 asserts all 32 user-harm example clauses (m0290 named) "read unambiguously
   user/developer from first-person text" — but the enumeration judged VERDICTS from
   clause text + gloss panel-blind, never simulating the validator's verbatim-quote
   requirement. The 183/183 headline does not cover quote-licensability.
2. **No per-case pre-OPEN gate protects the canonical controls.** §2.5 of the TASK DESIGN
   pre-registers per-case golden gates for the D4 cases (m0018/m0248 — "the golden
   expectations do not move"), but m0276/m0290 have no equivalent: m0290 is in the §2.2
   boundary set and golden-adjudicated, yet the §2.4 certification rule is aggregate
   (P1/P2/golden accuracy ≥ 0.90) — a systematic `unclear` on first-person example rows
   could pass certification if the aggregate holds, and the first HARD check is then
   §7.2's unconditional REVERT at MEASURE.
3. **R4's minor e-4 asked for exactly this hedge and it was not carried.** R4: "the §5
   preservation claim … presumes those verdicts land RESOLVED; an `unclear` verdict …
   resurfaces them through the E-1 exemption … §7.2's automatic REVERT catches it — say
   so in the same breath as the keying condition." The §5 text still carries the keying
   condition alone.

The failure mode is not silent and not a false PASS — the controls are real — but the
design's own brief has a foreseeable defect at a NAMED control that can kill the cycle
falsely (REVERT for a licensing gap, not a mechanism failure), after the parity gate's
single-amendment window may already have been spent on other seat defects. **Fix.**
(a) Pre-register a speaker-tag ruling in the brief/§1.4 (example-clause `<user>`/`<assistant>`
speaker tags license the named principal as bearer — mechanical, general, panel-blind),
or state the expected strict verdict for such rows; (b) extend §2.5-style per-case golden
gates to the canonical controls (m0276/m0290 expected verdict {user}, expectations
immutable); (c) carry the e-4 hedge into §5 verbatim.

## MINOR

* **E-3 — §5.2's parity-strata text contradicts the task design's strata.** REDESIGN §5.2:
  parity validation "on a stratified sample (strata in the §7.6 shape — behaviour ×
  section × verdict)". TASK DESIGN §2.2: strata are behaviour × kind × chained/patient-free.
  Beyond the mismatch, a "verdict" stratum is not constructible at parity time — verdicts
  are the OUTPUT of the task. Fix §5.2 to name the task design's strata (or "stratified
  per §2.2 of the companion spec").
* **E-4 — §2.4's certification rule omits the §2.5 D4 conjunct.** §2.5 declares a
  contradiction of either golden case "a golden failure of the disambiguation sub-task:
  the brief goes to §2.4's seat-defect channel (one amendment, fresh re-validation)", but
  §2.4's decision rule ("Certify … iff P1 ≥ 0.90 AND P2 ≥ 0.90 AND golden accuracy ≥ 0.90
  AND every divergence is adjudicated") does not list it. The two compose under a
  charitable reading (amendment path suspends certification); the rule should be
  self-contained — add the D4 conjunct to the decision rule.
* **E-5 — D3's golden-review directive has no implementation site.** §8-D3: "Golden-review
  the attribution-load-bearing examples (m0176/m0300/m0467) as seat-quality targets", and
  the enumeration §7 recommends naming them into the golden-review sample. The TASK DESIGN
  §2.2 boundary set names the eight canonical instances but NOT m0176/m0300/m0467 — they
  land in the golden review only if quota sampling hits them. Same pattern as the canonical
  eight ("named because the DESIGN names them; the validation seat is never told why") —
  add them to the boundary set.
* **E-6 — keying shorthand in REDESIGN §5.1 is a 2-field key that collides; the task
  design's 3-tuple is correct.** §5.1: "keyed per CLAUSE-INSTANCE (clause_id + span_id),
  NEVER per atom name"; TASK DESIGN §1.2/E_KEY: `(clause_id, span_id, name)`. Measured
  over `annotations_ext_v1_merged.json`: 190 (clause_id, span_id) pairs carry MORE THAN
  ONE atom — a 2-field key would merge their rows. The "NEVER per atom name" intent
  (never per name ALONE) is right, but an implementer building to §5.1's literal
  interface would produce a lossy key. State the 3-tuple in §5.1.
* **E-7 — R4 minor s-1 not carried: the restoration signature still lacks the `predicted`
  conjunct.** SIGNATURE is "factor 1.0 AND ONE of these arms"; no arm conjoins that the
  clause IS `predicted` in the S3b snapshot. R4 judged this unreachable in practice for
  the named single-match clauses and guarded anyway (a non-restored named clause flips
  into the bound) — add the conjunct for symmetry; it costs one line.
* **E-8 — R4 minor s-2 not carried: m0108's seat-defect review is DONE but cited as
  pending, and the gloss/bearer conflation stands.** §7.1: "m0108 stays `unclear`/contested
  PENDING its named seat-defect review"; §8-D2: "it goes to seat-defect review and is NOT
  resolved by S3b". The review EXISTS and has ruled (`M0108_SEAT_DEFECT_REVIEW.md`,
  2026-08-04: the `unclear` accounting stands; the definition genuinely under-determines
  the user's-organisation case; leg 2's direction sustained on the representation
  reading; boundary cases knife-edge until the §3 clarification is adopted by a query-side
  cycle). The design's m0108 handling is CONSISTENT with that disposition — cite it.
  The S-7 exploratory signature's parenthetical still reads "(unclear for a third-party
  query, the gloss names user AND developer bearers)" — the gloss is "user or developer
  directions whose execution could cause harm": it names whose DIRECTIONS they are, not
  who is HARMED by execution, which is exactly why `unclear` is expected (the seat-defect
  review §1d made precisely this point about leg 1's paraphrase).
* **E-9 — R4 minor e-2 not carried: §5.6's explain extension still under-lists what the
  signature reads.** §5.6: "attributed `harm_bearers`, the declared P, and their
  intersection". The signature additionally reads the extended `why` vocabulary
  (consistent/mismatched/generic/taint_capped/unclear-or-absent) and arm (ii)'s
  "disambiguation verdict AND the license quote on file" — the latter lives in the FROZEN
  ATTRIBUTION ARTIFACT, not the explain record; grant that read to the independent seat
  explicitly.

---

# Science

## MAJOR

### S-1 — the class rule's exclusion of m0239 is principled, but "tracked by that layer instead" currently points at an unreviewed draft, and no lapse condition is pre-registered

The exclusion itself is sound (verified above — general, pre-registered, correctly
scoped to the bound, pricing corpus-wide, flip recorded and reported, ground valid). The
defect is the disposition's RECEIVER. §4B: demoted clauses "are EXCLUDED from S3b's
regression bound … and are TRACKED BY THAT LAYER instead." The layer is
`IMPLIED_EFFECTS_DESIGN.md`, whose own status line is "DRAFT — design only, nothing
implemented … awaiting adversarial review", and whose §9 states it "does not restore
m0239 by itself — it provides the mechanism; m0239 is the first PROPOSED entry, subject
to §4 approval like any other." So the S3b cycle will pass a falsification bar that
knowingly reproduces an adjudicated regression (decision.json confirmed_regressions
includes m0239; leg 1 regression/high, leg 2 confirmed) on the strength of a tracking
promise made by a document that has not passed its own review, may yet be amended or
rejected, and — per its own count-first section (§5) — has not even enumerated the class
it would track. If the implied-effects design fails review, is abandoned, or sits
unbuilt, the exclusion silently becomes a PERMANENT immunization: m0239's re-suppression
forever counted out of the bound, tracked by nothing. The class rule's own legitimacy
rests on the demotion bar being high and the receiver being real; only the first half is
currently enforced. This is amendment-grade precisely because the fix is one sentence,
and it must land before OPEN because the exclusion is pre-registered at OPEN:
**add a LAPSE CONDITION to the class rule — the bound exclusion holds only while the
IMPLIED-EFFECTS layer is an active, reviewed work item that has accepted the demoted
clause as a tracked entry; if the layer's design is rejected or the work is dropped, the
exclusion lapses and the demoted clause re-enters the regression bound at the next
cycle.** (Cross-document note, same seam: `IMPLIED_EFFECTS_DESIGN.md` §2.4 composes
implied patients with TRANSLATION chains (`relevant_patients = translation_patients ∪
implied_patients`), but S3b's pricing reads ATTRIBUTION records, not chains, for its
factors — the composition hook will need re-stating when the layer is built. That is the
sibling design's problem, named here because the class rule's "tracked by that layer"
claim inherits it.)

## MINOR

* **S-2 — m0239's unclear horn is not pre-registered, and it is the horn that disappears.**
  §7.1 pre-registers the resolved-{user} outcome: "strict document-grounded attribution
  can only attribute {user} to its matched atom, so §5.3 predicts the same re-suppression
  S3 produced — a no_longer_predicted flip." The other horn vanishes from the bar: if the
  backfill returns `unclear` on m0239's matched atom (resolved {user} siblings would
  still fire taint, but the matched atom prices branch-1 cap-EXEMPT at 1.0, penalty 0),
  the clause prices at baseline — and since m0239 is `predicted` in the S2 baseline,
  restoration produces NO FLIP: nothing for the bound to count, and plank 1's iteration
  set is m0275/m0466/m0018 only. R4-B1 itself warned about this side channel ("to pass
  only via an un-pre-registered `unclear` verdict the design neither controls nor
  discloses" — there, about passing; the horn also pre-empts the IMPLIED-EFFECTS layer's
  first case). Detection is soft: the exempt-mass report would show m0239 at ~100% exempt
  share (single match) and the named response sends top-of-list clauses to golden review —
  a real but non-gated channel. **Fix.** Pre-register both horns for m0239 (expected:
  resolved-{user} re-suppression flip; if m0239 does NOT flip, require its explain trail
  to show the resolved-{user} signature, else flag), or add m0239 to the frozen-backfill
  re-check set beside m0018/m0248 (§2.5 pattern).
* **S-3 — the escape disclosure names only the `unclear` horn; comprehensive-generic
  mis-disambiguation has the same one-sided, flip-invisible shape.** §5.3 EXEMPT-MASS
  DISCLOSURE: "attribution errors and attributor laziness both flow toward `unclear` ⇒
  branch 1 ⇒ baseline pricing ⇒ never suppressed." But a clause whose correct verdict is
  resolved+specific+disjoint (factor d, suppressed) escapes identically if the seat
  instead disambiguates it COMPREHENSIVE — branch 2, factor 1.0, cap- and taint-exempt,
  baseline price, no flip when baseline-predicted. Monitoring covers it mechanically (the
  EXEMPT set includes comprehensive-generic records, so the exempt-mass report and §7.6's
  "comprehensive-generic" golden stratum both see it), but the disclosure should name the
  horn. Related: the validator cannot check that a comprehensive verdict corresponds to an
  actual generic noun — E_CONSISTENCY enforces set-shape only — so branch 2's SCOPE PIN
  is enforceable only through parity/golden review; that is inherent to D4 and acceptable,
  but it means the golden coverage for the leak direction is exactly the two §2.5 cases
  plus the §7.6 sample, and the design should say so where it discloses the escape.
* **S-4 — the 0.25 floor line sits in tension with the gate's own qualitative criterion;
  F_core's definition is looser than what the restoration signature requires.** TASK DESIGN
  §3.4: below F_scale, "the pass is paying full-population cost for a mostly branch-1
  artifact and the corpus-wide claim is unsupported." At R = F_scale = ceil(0.25·439) =
  110, 75% of the population is branch-1 mass — by the criterion's own words, still
  "mostly branch-1". The line's DERIVATION is honest (pre-known S2 precedent 0.38, set
  below because the question is harder) and the blindness ordering is correct — this is
  not an R4-S1 regression — but a floor is a minimum-support claim, and a corpus-wide
  mechanism claim certified at 25% resolution deserves either a higher line or an explicit
  statement that passing near floor triggers re-scope scrutiny at decision time.
  Separately: F_core = 3 is defined as "the falsifiable-core instances whose attributed
  RESOLUTION §7.1's restoration signature requires" — but for m0018 the signature requires
  the COMPREHENSIVE verdict (branch 2), which is stronger than resolution; a specific-{third_party}
  m0018 would count toward R yet fail plank 1. Not unsound (plank 1 catches the verdict
  shape independently, and F_core is dominated by F_scale anyway) — but the definition
  overstates what it pins.

---

# What holds (verified, briefly — credit where due)

* **All six claimed fixes landed and are correct** (verification section): R4-B1 as a
  principled general class rule; R4-E1 on one scale matching patient.py exactly, with a
  mass-asserting two-variant pinned test; R4-E2 with the overlay-empty precondition
  verified latent (closure set + HANDOFF); R4-E3 disclosed and monitored; R4-S1 genuinely
  blind; D4 consistent across both files and golden-collision-resolving without inversion.
* **The dossier diagnosis remains exact.** Every structural claim re-checked against the
  dossier JSONs and the raw artifacts: m0275 (patient-free `expressed_harmful_intent`,
  gloss "harm another person", sibling [model, user], `clause_tainted`, factor 0.1
  `why: clause_taint`, 0.35147 → 0.13088 < cut 0.23651); m0276 (matched patient-free
  `imminent_bodily_harm`, three user-chained siblings — and "the user" spans licensable
  for the needed {user} attribution); m0239 (matched PATIENT-BEARING act, all glosses
  user-focused, no third-party span anywhere in the clause text); m0466 ("mailing
  someone anthrax" — "someone" licensable); m0018 (single atom, chain [model,
  third_party]); m0290 (same atom name as m0466 — clause-instance keying is load-bearing,
  verified); m0108 (patient-free `harmful_instructions`).
* **§5.3 is TOTAL at both levels.** Atom-level: branches 1–4 partition (absent/unresolved;
  full-set comprehensive; resolved-specific intersecting; resolved-specific disjoint),
  E_CONSISTENCY pins full-set ⇔ comprehensive so the mechanical set-keying is faithful.
  Clause-level: taint with existential import; mixed clauses price per-atom uncapped;
  cap only under taint; empty-capped-set case stated; subsumption composed or pinned
  latent. I1 holds float-exactly via the penalty-subtraction form (penalty 0.0 ⇒ the
  base class's float); I2 via factors ∈ {0.0, d, 1.0}; never-outprice per record.
* **The mechanism separates m0275 from m0276** — traced end-to-end against the dossiers
  under the §5.3 rule: m0275's situation atom attributes third_party (branch 3, factor
  1.0, taint defeated by the intersecting atom) ⇒ surfaces at baseline 0.35147; m0276's
  attributes {user} (branch 4), all atoms disjoint ⇒ taint + cap, sole credited match
  keeps d ⇒ stays below cut. The §3 wall is respected: no chain-reading rule could
  separate them, and the design no longer floats one standalone.
* **The falsification bar cannot pass vacuously.** All-`unclear` attribution ⇒ branch 1
  everywhere ⇒ plank 1 FAILS (no arm matches `unclear`); comprehensive-laundering of
  m0275/m0466 FAILS the branch-keyed arms (why = generic ≠ consistent); "predicted but
  not attributed" is FAIL in every arm; plank 2 is an unconditional automatic REVERT;
  plank 3 counts every flip except the class-rule exclusion, and bystander movement is
  constrained by I2's raw monotonicity. The reach gate is blind-ordered with a
  no-revision rule.
* **The panel-blind / label-free fences are complete as designed.** Worksheet rows carry
  no behaviour names, scores, predicted sets, or census fields; the brief is silent on
  pricing; whitelist over the repo's own answer-key-carrying mandated reading (HANDOFF ⭐⭐
  verified to name the load-bearing clauses WITH required outcomes); standalone brief +
  FORBIDDEN scan as backstop; the restoration check runs post-freeze by a party the
  attributor never reports to; residual fence paths (this cycle's prediction/decision
  artifacts, the rechain channel) covered; stratified parity sample computed from
  query-side facts only; reach procedure blind-audited; floor author attests no access to
  reach output.
* **Discipline citations check out.** `backfill_author.md` rule 3 ("Do not infer an
  affected party from the subject matter"), "never force a call", "What you see, and all
  you see", "A validator failure is yours to fix by re-judging, not by loosening" —
  all verbatim in the brief; `grammar.PRINCIPALS` is exactly the seven values claimed;
  the small-model standard and the 2026-08-03 Haiku 4.5 / Opus 5 7/7 measurement are
  verbatim in `briefs/README.md`; population counts (368/71/439, bands 427/439/746)
  match `ATTRIBUTION_POPULATION_ENUMERATION.md` §0.

# Recommendation

REVISE — a fifth revision, and a short one. No blockers; three majors, all
amendment-grade:

* **E-1** — reconcile the D3 status: four locations say OPEN, §8-D3 and the registry say
  RULED; fix the OPEN-gate text (§9) to match the ruling, in whichever direction is true.
* **E-2** — dispose of m0290's quote-licensing gap before OPEN: a speaker-tag ruling in
  the brief (or the expected strict verdict), per-case golden gates for the canonical
  controls mirroring §2.5, and the e-4 hedge carried into the §5 preservation claim.
* **S-1** — add the lapse condition to the §4B class rule (exclusion lives only as long
  as the receiving layer does); note the chain-vs-attribution composition seam for the
  sibling design.

Fold in the ten minors while the document is open — E-3 (§5.2 strata wording), E-4 (§2.4
D4 conjunct), E-5 (m0176/m0300/m0467 into the boundary set), E-6 (3-tuple keying in
§5.1), E-7/E-8/E-9 (the three uncarried R4 minors: `predicted` conjunct, m0108 citation
and wording, §5.6 field list + attribution-artifact read grant), S-2 (m0239's unclear
horn pre-registered), S-3 (comprehensive horn named in the escape disclosure), S-4
(0.25-line tension acknowledged or the line re-derived, F_core definition tightened).
Then re-review: E-1 and S-1 both touch the falsification bar's gate text, which deserves
fresh eyes once more. Nothing here should be read as license to OPEN after a prose-only
pass — E-2 in particular needs a DECISION (the speaker-tag ruling or its refusal), not
just an acknowledgement.
