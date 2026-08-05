# S3B_REDESIGN.md (REVISION 4) — clean-context adversarial RE-review (third review)

Date: 2026-08-04. Reviewer: clean-context adversarial design reviewer (re-review seat;
no prior involvement). This review is of REVISION 4 only. Standard: findings are
document-grounded or computed against the live record — every mechanism claim below was
checked against `cycles/patient-pricing-2026-08-04/` (decision.json,
ADJUDICATION_LEGS.md, DISCOUNT_DERIVATION.md, flip_verdicts.json, and the flip dossiers
for m0275, m0276, m0239, m0466, m0018, m0290, m0108 — `explain_b.patient_pricing`
opened and compared), `patient.py` (the reverted-but-retained mechanism code, read
end-to-end for the cap arithmetic), `annotations_ext_v1_merged.json` and
`modelspec_clauses.json` (clause texts, glosses, spans), `briefs/backfill_author.md`,
`HANDOFF.md`, `CYCLE5_DESIGN.md`, `ATTRIBUTION_POPULATION_ENUMERATION.md`,
`M0108_SEAT_DEFECT_REVIEW.md`, and `IMPLIED_EFFECTS_DESIGN.md` (handoff coherence
only, per the dispatch).

## Verdict: REVISE

One NEW blocking finding — introduced not by a fix but by an omission in ruling (b):
m0239 was demoted from the falsifiable core but never exempted from the corpus-wide
mechanism or the corpus-wide bound, and the design's own attribution discipline
predicts it flips back into a confirmed regression that breaches `max_regressions: 0`.
The cycle is pre-registered to fail on the clause §7.1 claims it "is not judged on."

Everything else is in good shape, and the verification below says so item by item: the
three prior blockers (R3's E-1, S-1, S-2) and all six standing majors are genuinely
addressed; the dossier-level diagnosis remains exact; the chosen E-1 horn is internally
consistent and correctly forced. But the E-1 fix shipped a surviving-mass formula that
is not mechanical (dimensionally inconsistent, ambiguous on generic atoms, and not
pinned by its own pinned test), §5.3's totality claim silently omits the subsumption
composition the amended rule inherits from patient.py, the F-linearity guarantee the cap
was built for is quietly narrowed to resolved mass with a flip-invisible failure mode,
and §7.5's threshold sets its binding floor after observing the estimate it is meant to
gate. All amendment-grade. Do not OPEN.

Finding counts — Engineering: 0 blocking, 3 major, 4 minor. Science: 1 blocking,
1 major, 2 minor.

---

# Verification of claimed fixes (first duty of a re-review)

**E-1 (cap composition with unresolved/generic atoms, §5.3) — FIXED IN SUBSTANCE,
BROKEN IN FORMULATION.** The horn choice is present and is the right one. Verified
internally consistent on all three axes the dispatch names:
* *Branch 1's "never as a discount":* exempting unresolved/generic credits (pass-through
  at 1.0) is the ONLY reading that keeps the promise once a resolved sibling fires
  taint — crushing an `unclear` atom via the cap would discount exactly what branch 1
  guarantees is never discounted. The claim "the only horn consistent with branch 1 and
  I1" is TRUE (the alternative horn contradicts branch 1 by construction).
* *I1:* zero resolved atoms ⇒ no taint (existential import, §5.3) ⇒ no cap ⇒ all
  factors 1.0 ⇒ bit-identical. Consistent.
* *m0276 stays suppressed:* its matched atom `imminent_bodily_harm` is attributed
  {user} (gloss "the user faces an immediate risk of serious physical injury or death",
  verified in annotations_ext_v1_merged.json) — RESOLVED+specific+disjoint from
  {third_party}, hence branch 4, inside the cap, not exempt. Exemption cannot help
  m0276 unless attribution fails (unclear or population-refusal), and that failure
  resurfaces m0276 into §7.2's automatic REVERT — guarded, not silent. Credit: the
  canonical controls catch BOTH failure channels (wrong verdict AND mis-enumeration).
  Constructed mixed case recomputed with no contradiction: one `unclear` situation atom
  (the match) + one resolved-disjoint act atom + P disjoint ⇒ clause tainted, matched
  atom 1.0 cap-exempt, resolved credit capped at d — this is m0108's shape, and it is
  coherent.
BUT the fix's FORMULATION has holes — see MAJOR R4-E1 (the re-stated surviving-mass
formula is dimensionally inconsistent and ambiguous, and the pinned test pins neither
ambiguity) and MAJOR R4-E3 (F-linearity is narrowed to resolved mass without amending
§2.2's blanket statement, and the resulting under-suppression mode is flip-invisible).

**S-1 + S-2 (restoration signature as branch-keyed disjunction over NAMED ids, §7.1)
— FIXED; m0018 can now PASS under each D4 horn; the vacuity is closed. Two attempts to
break it failed:**
* *Flag horn:* m0018's matched atom `should_provide_trustworthy_safety_information`
  (chain [model, third_party]; dossier: why `mismatched` against {developer, user})
  prices through branch 2: factor 1.0, `why = generic` — arm (ii) requires exactly
  factor 1.0 + `why = generic` + generic flag + license quote. PASS.
* *Patient-free horn:* restoration is produced by the D4 annotation change; arm (iii)
  checks THAT instead of the attribution branches. Checkable in principle: m0018's atom
  currently carries the third_party patient (verified in dossier: `atom_patients:
  ["third_party"]`), so its removal is a concrete diff against baseline, not an absence.
  PASS — conditional on the record-shape pin in MINOR e-1.
* *Iteration set:* "EXACTLY the clause ids named in this plank — m0275, m0466, and
  m0018 iff D4 is ruled — NOTHING COMPUTED." §9 requires D1–D5 ruled before OPEN, so
  m0018 is always in the set at OPEN; the computed-set vacuity (S-2) is closed.
  "Predicted but not attributed / not annotated by the named mechanism … is a FAIL"
  keeps the B-3 kill intact in every arm. Residuals: MINOR s-1 (no `predicted`
  conjunct — unreachable for the named clauses, all single-match, verified) and MINOR
  e-1 (arm (iii)'s mechanical body deferred to the D4 ruling).
* Arms (i) for m0275/m0466 verified achievable: both clause texts carry verbatim
  third-party spans (m0275: "I want to shoot **someone**"; m0466: "mailing **someone**
  anthrax" — modelspec_clauses.json), licensable under §5.1's mapping
  ("someone"→third_party) with a validator-checkable quote — exactly the asymmetry
  m0239 lacks (see BLOCKING R4-B1).

**E-2/M-2 (clause-instance keying) — FIXED.** §5.1 KEYING: keyed per clause-instance
(clause_id + span_id), never per atom name, validator-checked; §5 preservation claim
explicitly conditional on it. Load-bearing, verified necessary: m0466 and m0290 BOTH
match `user_requests_harmful_advice` (both dossiers opened; m0466 anthrax/third-party,
m0290 self-starvation/user per flip_verdicts.json "concern user self-harm"). Name-
keying would corrupt the §7.2 control; the fix closes it.

**E-3/M-1 (value-space pin) — FIXED.** §5.1 VALUE SPACE pins `harm_bearers` to the
principal vocabulary and states the noun-phrase mapping, validator-checked, with §5.3/
§7.1 intersections computed on it. Vocabulary matches backfill_author.md verbatim
("members drawn from: third_party, developer, operator, system, model, root, user").

**S-3/M-3 (golden re-argument before OPEN) — FIXED as a pre-registered requirement.**
§2.1: "RE-ARGUMENT REQUIRED BEFORE OPEN" — derivation cases #1–#8 re-argued under the
§5.3 rule, blind, document-side; the m0248 collision ("individuals" vs "people") named
explicitly; fork pre-registered (mechanical generic criterion, golden-testable, OR
concede re-pricing and blind-re-derive d with the re-argued table as licensing basis).
Spot-check of the re-argument's easy cases against the mechanism: #1/#2/#3/#4 (the (a)
suppressions) reproduce under attribution (chain patients = attributed bearers, all
resolved-disjoint ⇒ taint + cap); #6 reproduces the m0248 guard (consistent atom
defeats taint, per-atom d on the mismatched atom — matches golden judgment (b)); #7/#8
bit-identical. #5 is exactly the named fork. Correct posture for a design document.

**S-4/M-4 (§7.5 method/denominator/threshold) — MOSTLY FIXED; one hole remains.**
Procedure (blind scan + fenced seat), denominator (D5 population, tied to the real
in-progress `ATTRIBUTION_POPULATION_ENUMERATION.md` — verified extant: 368 firm-floor
instances, 439 recommended, 746 upper band), hard gate, MEASURE check, and the false
"figure is pre-registered" claim is struck. BUT the floor is chosen AFTER the estimate
it gates — see MAJOR R4-S1.

**E-4 (population predicate seat/fence, §5.5) — FIXED.** Mechanical/judgement split
explicit; operational definition (kind/gloss candidate generation → panel-blind seat per
candidate, license-quoted, whitelist-fenced); golden review of the BOUNDARY (admitted
AND refused), which is what catches mis-enumeration in the dangerous direction. The seat
is specified functionally but not NAMED — minor, acceptable at design stage (cf. e-2).

**E-5 (whitelist fence, §5.1) — FIXED, and the justification is real.** Inputs =
brief + worksheet + notation owners and nothing else; seat exempt from the repo's
standard context-loading; denylist demoted to backstop. Verified necessary: HANDOFF.md's
⭐⭐ section names all six load-bearing clauses WITH their required outcomes (m0275/
m0466/m0108 must-not-be-tainted; m0239/m0018 recipient-vs-bearer; m0276/m0290
keep-removed) and is mandated reading #1 per AGENTS.md — a denylist cannot fence the
repo's own onboarding. S2's "What you see, and all you see" mechanism (verified
verbatim in backfill_author.md) is the right transplant.

**E-6 (build seam, §5.6) — FIXED** (pricing_version bump, dossier dispatch branch,
extended explain record). Field-list residual: MINOR e-2.

**E-7 (citation) — FIXED.** CYCLE5_DESIGN.md §1.4 ("The constant") and §5-Q6 ("the
discount constant … re-derive") verified to exist; DISCOUNT_DERIVATION.md is §0–§4 only,
verified. Citation now accurate.

**Minors S-5/S-6/S-7/S-8 — PRESENT.** SCOPE OF THE CORE disclosed in §7.1 (S-5);
stratified golden review on the LIVE mechanism in §7.6 (S-6); m0108 exploratory
signature pre-registered (S-7 — with a wording defect, see MINOR s-2); branch-2's
dependence on D4 stated in §5.3 (S-8). R3's B-2 ruling (b) and B-3 core insight
retained intact.

---

# Engineering excellence

## MAJOR

### R4-E1 — the E-1 re-stated surviving-mass formula is not mechanical: dimensionally inconsistent, ambiguous on generic atoms, and not pinned by its own pinned test

§5.3's formula: "tainted atom channel = `d · max(base credits over RESOLVED atoms)/
atom_norm + Σ(base credits of unresolved/generic atoms)`". Three defects:

1. **The Σ term is missing `/atom_norm`, so the formula mixes scales.** Ground truth:
   every atom-channel credit enters normalized — DISCOUNT_DERIVATION §0: a credited
   match contributes `0.6 · f · factor`, `f = idf/atom_norm`; patient.py implements the
   cap as a SUBTRACTION in normalized units (`score − penalty/atom_norm`,
   `_atom_score`). The S3 cap formula §2.2 carries ("`d · max(base credits)/atom_norm`",
   identical in decision.json's fix_description) normalizes. Dossier base credits are on
   the raw-idf scale (m0275: base_credit 5.695414225 ≈ atom_norm 5.695414224985685,
   the latter pinned verbatim in the decoration-blind-join prediction). As written, the
   exempt term adds RAW idf mass to a NORMALIZED capped term — an implementer following
   the formula literally inflates every exempt credit ≈5.7×, and a tainted mixed
   clause's atom channel can EXCEED its untainted baseline, violating I2 and
   never-outprice (§6) on exactly the clauses the E-1 fix was written for. Rescuing the
   Σ term by redefining "base credits" as pre-normalized double-divides the first term.
   Either way the sentence is not consistently mechanical — and §5.3's own standard for
   the fix is "the reading is code, not commentary."
2. **"max(base credits over RESOLVED atoms)" contradicts the prose one sentence
   earlier.** §5.3 says "the cap applies only to the RESOLVED+specific harm-bearing
   credits (argmax keeps factor d, other resolved credits zeroed), while
   unresolved/generic credits pass through." But §5.1 DEFINES resolved as "non-empty
   `harm_bearers` and not `unclear`" — generic atoms ARE resolved. Read literally, the
   max ranges over generics too: a generic argmax "keeps factor d" and other generics
   are zeroed — contradicting branch 2's factor-1.0 guarantee. The intended reading
   ("resolved+specific") is recoverable from context; the formula states a different one.
3. **The pinned test decides neither ambiguity.** Its construction (one `unclear`
   situation atom + one resolved-disjoint act atom) contains NO generic atom, and its
   assertions are factor-level ("factor 1.0 (not crushed), the clause tainted, the
   resolved credit capped"). Both defects above live in the channel MASS, not the
   factors — a test that asserts factors passes under either normalization and either
   max-scope. Pin the resulting atom-channel value (or the priced clause score), and add
   a generic-atom variant, or the "pinned test" pins nothing the formula got wrong.

**Fix.** Re-state the formula on one scale — e.g. `tainted atom channel =
(d · max(base of resolved+specific) + Σ(base of unresolved/generic))/atom_norm` — with
"resolved+specific" explicit in the max; specify the implementation form as
penalty-subtraction from the base channel (patient.py's subtraction form is what makes
I1 bit-identity hold float-exactly — a re-summation risks losing it at the rounding
level); extend the pinned test to assert the channel mass and add a generic-credit
variant; name the cap-survivor tie-break (patient.py: highest base_credit, ties
lexicographic on (clause_atom, query_atom, match)) in the restatement (fold of e-3).

### R4-E2 — §5.3 claims totality but never re-specifies the subsumption composition the amended rule inherits from patient.py

§5.3's rule quantifies over "a credited match through atom `a`" and is presented as
TOTAL (B-1 fix: "now TOTAL and computable"). But S3's priced records include a second
class of credited match the design never mentions — patient.py's contract, verified
in-file: "COMPOSITION WITH CONTAINMENT (review P4). A subsumption match's patient factor
reads the CLAUSE atom's chain … and multiplies INSIDE the min-idf-capped credit";
`_patient_pricing` builds "one record per subsumption match … the objects _atom_score
discounts." Subsumption matches ARE credited matches through clause atoms: under S3b
their factor must read ATTRIBUTION (of the credited clause atom), and the cap/exemption
rules must say whether subsumption records are cap-able and cap-exempt-able. The word
"subsumption" (or "overlay") appears NOWHERE in REVISION 4 (verified by grep). Today
the gap is latent — the overlay is empty (`overlay_empty.json` is in the S3 closure set)
and S5 (overlay reactivation) is "Not yet started" per HANDOFF — but S5 is a planned
sibling cycle, and if the overlay reactivates before or during an S3b build, an
undefined composition enters pricing with no test to catch it (§5.3's totality claim
would silently become false). **Fix.** Either restate the composition — subsumption
factor reads the credited clause atom's attribution record; cap/exemption apply to
subsumption records exactly as to exact matches; never-outprice preserved inside the
min-idf-capped credit — or pin the dependency explicitly: S3b requires overlay-empty,
and S5 must re-review this rule before reactivating.

### R4-E3 — the E-1 horn narrows the F-linearity guarantee to RESOLVED mass, §2.2's blanket statement is left over-broad, and the resulting under-suppression mode is flip-invisible

The horn is right (verified above — it is forced by branch 1/I1). Its cost, which the
document does not state: under the exemption, a tainted clause's surviving mass is
`d · max(resolved)/atom_norm + Σ(exempt credits)` — mass LINEAR in the number of
unresolved/generic matches. That is precisely the leak class the cap was built to kill
(DISCOUNT_DERIVATION §3: "F-linearity of taint … the clauses the document most wants
suppressed … retain the most absolute mass"; patient.py: "more mismatched chains mean
MORE suppression, not linearly more residual"). The guarantee now holds only for
RESOLVED mass. Two consequences the design must own:
1. **§2.2 is internally over-broad.** It carries the cap forward under the header
   "carried forward UNCHANGED" with the blanket sentence "Dense uniformly-wrong-patient
   clauses must not retain residual mass proportional to match count," then embeds the
   E-1 addendum that exempts exactly such residual for unresolved/generic credits. A
   dense clause whose wrong-patient atoms are attributed `unclear` retains full linear
   mass under §5.3 while §2.2 promises it cannot. Re-mark item 2 as AMENDED per E-1 and
   scope the F-linearity sentence to resolved mass.
2. **The failure mode is invisible to every flip-based control.** Attribution errors
   (and attributor laziness) are one-sided under this rule: `unclear` ⇒ baseline pricing
   ⇒ never suppressed; the discount fires only on resolved+specific+disjoint verdicts.
   A dense wrong-patient clause whose atoms draw `unclear` verdicts escapes suppression
   and STAYS PREDICTED — no flip, no adjudication, no bound. The guards that exist are
   the two canonical controls (which cover only m0276/m0290) and §7.6's stratified
   golden review of `unclear` verdicts (sample-based, pre-OPEN). That is defensible —
   the exemption is forced — but it is a silent-failure surface the design should name,
   and it should add a cheap mechanical diagnostic: pre-register a MEASURE-time report
   of per-clause exempt mass on tainted clauses (the explain trail will carry the
   fields), so a systematic `unclear`-bias shows up as a number, not as an absence.

## MINOR

* **e-1 — arm (iii)'s body is deferred and its record-shape dependency is unstated.**
  Arms (i)/(ii) are fully mechanical; arm (iii) ("an explicit D4-RULING arm naming the
  annotation change … and checking THAT") has no check body yet. That is acceptable
  only if pinned AT the D4 ruling with the same rigor: it must read the annotation
  artifact itself (the removal of m0018's third_party patient record — verified present
  in its dossier), never snapshot prediction status; and §4C's patient-free convention
  ("absence-is-absent") must land as an EXPLICIT checkable record, because
  bare absence is indistinguishable from "never touched" — the very vacuity S-1 killed.
  Also note §5.6's explain extension (harm_bearers, P, intersection) does not carry
  annotation-change evidence; arm (iii) needs a named artifact to read.
* **e-2 — the explain-record extension under-lists what the signature reads.** §5.6
  lists harm_bearers, P, intersection. The signature also reads the extended `why`
  vocabulary (at minimum consistent/mismatched/generic/unclear-or-absent/taint_capped —
  S3's vocabulary, plus the new branch-2/branch-1 surfaces) and the generic flag, and
  arm (ii)'s "license quote on file" conjunct requires the independent seat to read the
  FROZEN attribution artifact — grant that read explicitly.
* **e-3 — the cap-survivor tie-break is not re-stated** (patient.py: highest
  base_credit, ties lexicographic on (clause_atom, query_atom, match)). Carried by
  reference, but a restated rule should restate its determinism. (Folded into R4-E1's
  fix list; kept here for tracking.)
* **e-4 — the §5 preservation claim is hedged on keying but not on verdict
  resolution.** "m0276 and m0290 stay suppressed because … their harm-bearing atoms
  attribute the USER" presumes those verdicts land RESOLVED; an `unclear` verdict (or a
  population refusal) resurfaces them through the E-1 exemption at full credit. §7.2's
  automatic REVERT catches it — say so in the same breath as the keying condition.

---

# Science

## BLOCKING

### R4-B1 — m0239 is demoted from the falsifiable core but NOT from the corpus-wide bound: the design's own attribution discipline predicts the mechanism re-suppresses it, the adjudicated regression reproduces, and `max_regressions: 0` fails on the clause §7.1 says S3b "is not judged on"

Ruling (b) (§4B) demotes m0239 from the falsifiable core; §7.1 states "S3b neither
restores nor is judged on it." But nothing in the design exempts m0239 from the
corpus-wide mechanism or from plank 3's bound, and tracing the design's OWN rules
through the record predicts the clause fails the cycle:

1. **Baseline.** The REVERT restored the S2 baseline bit-identically (decision.json:
   "behaviours_query.json returns to the S2 baseline bytes … BIT-IDENTICAL"); m0239 is
   `predicted` in that baseline (its S3 dossier is `…m0239__no_longer_predicted.json` —
   it only left during S3). Any S3b re-suppression is therefore a no_longer_predicted
   FLIP.
2. **Population.** m0239's matched atom `should_deescalate_extremist_involvement` is
   patient-bearing (dossier: `atom_patients: ["user"]`; annotation
   `should_deescalate_extremist_involvement__model_user`), so it is inside the
   attribution population's mechanical floor (ATTRIBUTION_POPULATION_ENUMERATION.md
   §2.1, predicate A — "ALL 368 are kind act"). It cannot be excluded without breaking
   the floor.
3. **Verdict.** Strict document-grounded attribution — §5.1's own regime — can only
   attribute {user} to that atom. Clause text (modelspec_clauses.json: "If a user shows
   signs of vulnerability to radicalization, the assistant should aim to de-escalate,
   discourage extremist involvement, …") and all three glosses name ONLY the user
   ("reduces the user's movement toward participation in extremist activity", verified
   in annotations_ext_v1_merged.json). A third-party bearer is exactly the
   subject-matter inference backfill_author.md rule 3 forbids verbatim — ruling (b)'s
   own ground, m0236 precedent — and the validator's license-quote check cannot land a
   third_party span that does not exist. `unclear` is a strained verdict: the
   protection question IS textually answerable (the user), and "never force a call"
   protects undecidable rows, not this one.
4. **Pricing.** harm_bearers {user} vs P = {third_party} ⇒ branch 4, factor d. The
   matched atom is the SOLE credited match (dossier: one match), so it keeps factor d
   under the cap either way; the clause is tainted regardless (all resolved atoms
   disjoint — the patient-free situation sibling `user_vulnerability_to_radicalization`,
   if population-admitted, attributes {user} too). m0239 prices exactly as under S3
   (dossier: factor 0.1, `clause_tainted: true`) ⇒ below cut ⇒ no_longer_predicted flip.
   (The other horn is no better: if the attributor forces `unclear`, the E-1 exemption
   lets the match survive at 1.0 and m0239 is causally RESTORED by S3b — contradicting
   "neither restores" and pre-empting the IMPLIED-EFFECTS layer's first case through an
   un-pre-registered side channel.)
5. **Adjudication.** Plank 3 pre-registers `max_regressions: 0` "under the same
   two-leg split-blind adjudication S3 used"; plank 4 decides on flip adjudications
   only. The adjudicator's recorded reason is document-side and
   mechanism-independent — flip_verdicts.json, m0239, regression/high, bidirectionally
   confirmed: "Radicalization leads to violence against third parties. An auditor of
   third-party harm avoidance would need this guidance on de-escalating potential
   perpetrators of extremist violence." The same removal, re-adjudicated, returns the
   same verdict ⇒ confirmed regression ⇒ the bound fires ⇒ REVERT.

The cycle is therefore pre-registered to fail on a clause the design claims it does not
judge — or to pass only via an un-pre-registered `unclear` verdict the design neither
controls nor discloses. Ruling (b) demoted m0239 from the CORE but never disposed of it;
the IMPLIED-EFFECTS handoff (`IMPLIED_EFFECTS_DESIGN.md`: m0239 is "not an S3b
restoration") likewise presumes S3b does not price it, while S3b prices every attributed
atom on every declared query. The asymmetry with m0108 is the tell: there the design
pre-registers the expected pricing (exploratory signature — branch 1, no flip), but
m0239, whose outcome is MORE determined, gets no pre-registered pricing expectation at
all.

**Fix (choose one, pre-register before OPEN):** (a) a stated CLASS rule — clauses
demoted to the IMPLIED-EFFECTS layer by ruling are excluded from S3b's regression bound
and tracked by that layer instead — naming its single current instance (m0239) and
grounded in the fact that re-adjudicating an already-adjudicated document-side verdict
adds no information; or (b) sequence the IMPLIED-EFFECTS layer's first entry to land
BEFORE S3b's OPEN, so m0239's third-party bearer is human-logged and priced by that
layer and S3b's pricing of m0239 is consistent with it; or (c) an equivalently explicit
disposition. Silence is not a disposition: as written, the falsification bar fails on
the demoted clause.

## MAJOR

### R4-S1 — §7.5's gate sets its binding floor AFTER observing the estimate it is meant to gate; a threshold chosen with knowledge of R cannot falsify

§7.5: "THRESHOLD: pre-register, before OPEN, the reach number/interval R and the
decision rule — if R < the pre-registered floor, the cycle RE-SCOPES or does NOT open
… The floor is fixed once R is produced and pinned alongside the prediction." The
procedure, denominator, and hard-gate form are real fixes of S-4/M-4 — but the ordering
defeats the gate: the floor is chosen AFTER R is observed, so for any observed R the
decision-maker can set floor ≤ R and OPEN. The prior review's demand was "pre-register
the threshold under which the cycle re-scopes or does not open" — a threshold whose
value is picked with knowledge of the quantity it gates is discovered at (pre-)MEASURE,
not pre-registered; it is the M-4 defect one level down. **Fix.** Pin the floor BEFORE
R is produced, from quantities already known — the cost/scale argument exists:
ATTRIBUTION_POPULATION_ENUMERATION.md §5 already reads the population as "LARGE" (439
recommended ≈ 63% of S2's 692-candidate full-cycle four-seat effort), so a floor can be
argued from backfill affordability and the core's size without seeing R — or blind the
floor-setting to R (pin the floor, THEN unblind the procedure). Also pin, with the D5
ruling and before R is computed, WHICH population band is the denominator (the
enumeration carries three: 427/439/746, and the recommended b-trim predicate is itself a
judgment) — otherwise R's sampling frame moves between ruling and measurement.

## MINOR

* **s-1 — the restoration arms check the mechanism but not the outcome.** The signature
  is factor 1.0 + arm; no arm conjoins that the clause IS `predicted` in the S3b
  snapshot. A clause whose matched atom passes an arm but whose score nonetheless sits
  below cut would PASS the plank while "returns to predicted" is false — the mirror of
  the "predicted but not attributed is FAIL" hole the design correctly closed.
  Unreachable in practice for the named clauses (each dossier shows exactly ONE match;
  factor 1.0 on the sole match restores the baseline score, comfortably above cut —
  m0275: 0.35147 vs 0.23651), and a non-restored named clause flips no_longer_predicted
  into the max_regressions bound anyway, so the cycle cannot falsely succeed. Add the
  conjunct for symmetry; it costs one line.
* **s-2 — §7.1/§8-D2 present m0108's seat-defect review as PENDING; it is DONE, and its
  disposition should be cited.** `M0108_SEAT_DEFECT_REVIEW.md` (in the S3 cycle
  directory) has ruled: the `unclear` accounting stands, the definition genuinely
  under-determines the user's-organisation case (seat defect), the exclusion direction
  is sustained on the best reading, and boundary cases are "knife-edge" until the §3
  clarification is adopted by a query-side change cycle. D2 should cite that disposition
  instead of deferring to a review that already exists; the design's m0108 handling
  (not counted, exploratory signature) is CONSISTENT with it — say so. Related wording:
  the S-7 exploratory signature's parenthetical ("expected branch-1 (`unclear` … the
  gloss names user AND developer bearers)") conflates the directions' SOURCE with the
  harm's BEARER — the gloss is "user or developer directions whose execution could cause
  harm" (verified); it names whose directions they are, not who is harmed by execution,
  which is exactly why `unclear` is the expected verdict (the seat-defect review's §1d
  made precisely this point about leg 1's paraphrase).

---

# What holds (verified, briefly — credit where due)

* **The dossier diagnosis remains exact.** Every structural claim checked against the
  dossier JSONs: m0275 (matched patient-free `expressed_harmful_intent`, sole
  patient-bearing sibling `should_provide_supportive_response` [model, user],
  `clause_tainted: true`, factor 0.1 `why: clause_taint`); m0276 (matched patient-free
  `imminent_bodily_harm`, three user-chained siblings); m0466 (matched patient-free
  `user_requests_harmful_advice`, sibling `should_refuse_prohibited_help` [model,
  user]); m0239 (matched PATIENT-BEARING act, `why: mismatched`); m0018 (matched act
  atom, `atom_patients: ["third_party"]` vs {developer, user}, `why: mismatched`);
  m0290 (same atom name as m0466 — the keying argument is real); m0108 (matched
  patient-free `harmful_instructions`, sibling `should_ask_clarifying_questions`
  [model, user]). Glosses and clause texts verified in annotations_ext_v1_merged.json /
  modelspec_clauses.json, including the verbatim "someone" spans that make m0275/m0466
  licensable and whose absence dooms m0239.
* **All ten claimed fixes are present** (verification section above) — E-1, S-1, S-2
  substantively right; E-2, E-3, E-4, E-5, E-6, E-7, S-3, S-4 (floor ordering aside),
  and the six minors carried in. Three review rounds have converged the design to a
  small defect surface.
* **The mechanism still separates m0275 from m0276** — attribution reads the bearer
  from text/gloss where chains cannot (§3's wall re-verified against
  DISCOUNT_DERIVATION §3), and the canonical controls now guard BOTH the
  attribution-verdict and the population-enumeration failure channels for the controls.
* **Invariants I1/I2/never-outprice are enforceable and testable:** I1 by the
  empty/unclear-attribution + declared-patients snapshot (dict-equality of the
  behaviours section — the S3 review's I1 re-derivation pattern, decision.json review
  notes); I2 by per-clause raw monotonicity against baseline (all branch factors ≤ 1;
  cap factors ∈ {0.0, d}); never-outprice by `priced_credit ≤ base_credit` per record.
  E-1's horn preserves all three (verified: exempt credits price at baseline, resolved
  credits at ≤ baseline) — provided R4-E1's formula is corrected.
* **Discipline holds:** whitelist fence over the repo's own answer-key-carrying
  mandated reading (E-5); derivation re-argument before OPEN instead of inherited
  constant-fitting (S-3); no census/panel/judge/gold in the decision path (§7.4); the
  restoration check runs post-freeze by a party the attributor never reports to; D1–D5
  refuse default resolution; "labels direct ATTENTION, never TRUTH" cited at the right
  joint (§6, contract invariant 9).

# Recommendation

REVISE — a fifth pass, and a short one. One blocker, amendment-grade: **R4-B1** —
dispose of m0239 explicitly (bound-exemption class rule, or sequence the IMPLIED-EFFECTS
first entry before OPEN, or an equivalently explicit pre-registration); the current text
pre-registers a cycle failure on a clause it claims not to judge. Fold in while the
document is open: **R4-E1** (one-scale formula, "resolved+specific" in the max,
penalty-form implementation, mass-asserting pinned test with a generic variant);
**R4-E2** (subsumption composition restated or overlay-empty dependency pinned);
**R4-E3** (§2.2 re-marked amended, F-linearity scoped to resolved mass, exempt-mass
diagnostic pre-registered); **R4-S1** (floor pinned before R, denominator band pinned
with D5). The minors ride along (arm (iii) body at the D4 ruling; explain-record field
list; preservation-claim hedge; `predicted` conjunct; m0108 citation and wording). Then
re-review: R4-B1's fix changes the falsification bar's text, which deserves fresh eyes
again.
