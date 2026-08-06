# S3b REDESIGN — beneficiary-aware patient pricing (REVISION 9, for adversarial re-review)

Status: **REVISION 9 — design only, nothing implemented.** This document is the written,
reviewed design the S3 revert obliges before any re-attempt (HANDOFF 2026-08-04 LATE:
"It needs a written, reviewed design first — do not re-attempt by tuning constants").
It supersedes the S3 mechanism (`patient.py` as shipped at `091619c`, REVERTED).
Author: session coordinator (Qwen Code), 2026-08-04; REVISION 7, 2026-08-05;
REVISION 8, 2026-08-05; REVISION 9, 2026-08-05. Review seat: REVISION 4 was
adversarially re-reviewed (`S3B_ADVERSARIAL_REVIEW_R4.md`, verdict REVISE);
REVISION 6 was adversarially re-reviewed (`S3B_ADVERSARIAL_REVIEW_R6.md`, verdict
REVISE — no blockers, 3 majors); REVISION 7 fixed the three R6 majors (E-1, E-2, S-1)
plus the two directed minors; REVISION 8 folded in the eight remaining R6 ride-along
minors and was adversarially re-reviewed (`S3B_ADVERSARIAL_REVIEW_R8.md`, verdict
REVISE — no blockers, 2 majors); REVISION 9 fixes exactly those two majors (S-A, S-B),
and is for adversarial re-review before OPEN.

**REVISION 9 fixes the two MAJOR findings of the R8 adversarial re-review
(`S3B_ADVERSARIAL_REVIEW_R8.md`, verdict REVISE — 0 blocking / 2 major). Nothing else
moves: the R6 majors, the ten R6 minors, and every ruling are retained intact, and no
new ruling is recorded.**
* **S-A — restoration signature arms bound PER CLAUSE.** §7.1's SIGNATURE arms are now
  mechanically CLAUSE-BOUND, not a free disjunction: m0275 and m0466 satisfy ONLY
  arm (i) (resolved consistent attribution), m0018 ONLY arm (ii) (the D4
  comprehensive disambiguation). A comprehensive-laundered m0275/m0466 — wrong
  verdict: the full principal set instead of {third_party} — matches arm (ii), which
  is NOT its bound arm, and FAILS the plank (the branch keying no longer floats free
  of the clause); the mirror laundering on m0018 fails the same way. AND —
  belt-and-braces, closing the hole at backfill time too — the companion spec's §2.5
  frozen-backfill re-check now EXTENDS to m0275/m0466 with IMMUTABLE expected
  verdicts (resolved, `harm_bearers` exactly {third_party}, not comprehensive):
  the validator's E_CONSISTENCY enforces set-shape only and cannot see a laundering
  verdict, and no other backfill-time check sees m0275/m0466's verdicts. §7.1 now
  matches the companion spec's §3.4 F_core reading (which already read the arms as
  clause-bound), and §5.3's leak-direction coverage sentence carries the new
  re-check cases.
* **S-B — the lapse condition's state space completed.** The §4B LAPSE CONDITION now
  (a) states its MEASURE-time semantics explicitly — the exclusion holds at MEASURE
  only if the receiver has passed review and accepted m0239 AT MEASURE; otherwise
  m0239's expected flip IS counted — and gates OPEN on receiver readiness (§9);
  (b) fixes ONE re-entry semantic at all three restatement sites (§4B, §7.1, §7
  plank 3): the demoted clause re-enters THIS cycle's §7.3 bound — the "at the next
  cycle" reading is deleted; and (c) states the retroactive consequence: a lapse
  established AFTER CLOSE re-counts the recorded-and-reported flip retroactively
  against S3b's own bound at the decision point where lapse is established — the
  reading that gives the condition teeth against permanent immunization (no future
  cycle re-flips a clause whose priced state is unchanged, so a next-cycle-only
  re-entry would count nothing).

**REVISION 8 folds in the eight ride-along MINOR findings of the R6 adversarial
re-review (`S3B_ADVERSARIAL_REVIEW_R6.md`, minor-findings section) that were not in
REVISION 7's directed change list. All prior-revision fixes — REVISION 7's three
majors and two minors included — are retained intact; no major is re-opened, and no
new ruling is recorded. Fixes tagged R6-* in the body; §-references without a file
name are to this document, §-references to the companion spec name it.**
* **E-3 — §5.2 parity strata.** The parity gate's sample is now stratified per the
  companion spec's §2.2 (behaviour × kind × chained/patient-free), replacing the
  former "§7.6 shape — behaviour × section × verdict", which contradicted the
  companion spec AND was not constructible at parity time (verdicts are the OUTPUT
  of the task).
* **E-4 — §2.4 D4 conjunct.** The companion spec's certification decision rule is now
  SELF-CONTAINED: it lists the §2.5 D4 golden-case conjunct (m0018 comprehensive /
  m0248 specific, neither contradicted) alongside P1/P2/golden accuracy/divergence
  adjudication.
* **E-5 — D3 golden-review implementation site.** The §8-D3 golden-review targets
  m0176/m0300/m0467 are now ALWAYS-INCLUDED rows of the companion spec's §2.2
  boundary set, and §8-D3 names that implementation site.
* **E-7 — restoration signature `predicted` conjunct.** The §7.1 SIGNATURE now
  conjoins that the clause IS `predicted` in the S3b snapshot, alongside factor 1.0
  and the branch-keyed arms (carried from R4 minor s-1).
* **E-9 — §5.6 explain extension field list.** The build seam's extended explain
  record now lists everything the §7.1 signature reads (attributed `harm_bearers`,
  the declared P, their intersection, and the extended `why` vocabulary), and the
  independent §7.1 seat is explicitly GRANTED the read of the FROZEN ATTRIBUTION
  ARTIFACT, where arm (ii)'s disambiguation verdict and license quote live
  (carried from R4 minor e-2).
* **S-2 — m0239's unclear horn.** §7.1 now pre-registers BOTH horns of m0239: the
  expected resolved-{user} re-suppression flip, and the alternate horn (matched atom
  `unclear` ⇒ branch 1 ⇒ baseline ⇒ NO flip, nothing for the bound to count), which
  carries a NAMED CHECK — if m0239 does not flip, its explain trail must show the
  resolved-{user} signature on its matched atom, else FLAG to the §5.3 NAMED
  RESPONSE.
* **S-3 — comprehensive horn of the escape.** §5.3's EXEMPT-MASS DISCLOSURE now names
  the second horn of the one-sided escape (a clause whose correct verdict is
  resolved+specific+disjoint mis-disambiguated COMPREHENSIVE ⇒ branch 2 ⇒ baseline
  ⇒ no flip), states that monitoring covers it mechanically, and states the leak-
  direction golden coverage exactly (the two §2.5 cases of the companion spec plus
  the §7.6 sample — branch 2's SCOPE PIN is enforceable only through parity/golden
  review).
* **S-4 — 0.25 line and F_core.** In the companion spec's §3.4: the 0.25 line STAYS
  at its blind derivation (moving it would need the no-post-unblind-revision
  discipline) but is now explicitly a MINIMUM-SUPPORT floor — a pass near the floor
  triggers re-scope scrutiny at the cycle decision — and F_core's definition is
  tightened to the verdict SHAPES the §7.1 signature requires (m0018's COMPREHENSIVE
  disambiguation is strictly stronger than resolution).

**REVISION 7 fixed the three MAJOR findings of the R6 adversarial re-review
(`S3B_ADVERSARIAL_REVIEW_R6.md`, verdict REVISE — 0 blocking / 3 major) plus one
coordinator ruling and two of R6's ride-along minors (the remaining eight ride-along
minors were folded in by REVISION 8 — see the note above); all prior-revision fixes
are retained intact.**
* **E-1 — D3 status reconciled.** D3 is RULED (coordinator 2026-08-05): UNIFORM — no
  distinct example-kind rule (latent fix LF-1, `LATENT_FIX_REGISTRY.md`). The
  REVISION-6 header note, §8 heading, and §9 still called D3 OPEN while §8-D3 recorded
  it RULED; REVISION 7 reconciles every location to RULED, and §9's OPEN condition now
  reads on D2 and D5 only.
* **E-2, part A (coordinator ruling) — speaker-aware first-person mapping.** The
  companion spec's §1.4 mapping table gains one MINIMAL rule (note (v)): a first-person
  pronoun ("I", "me", "my") inside a `<user>` speaker turn maps to `user`; inside an
  `<assistant>` speaker turn, to `model`. A first-person pronoun refers to its speaker,
  so the rule cannot misattribute; it is what makes the example-dialogue control's
  (m0290's) {user} attribution licensable under the verbatim-quote regime, which is why
  the canonical controls can stay suppressed (§5, §7.2).
* **E-2, part B (coordinator ruling) — pre-OPEN licensability gate for the canonical
  controls.** Before OPEN, m0276's and m0290's harm-bearer attributions are verified
  LICENSABLE per case — each must carry a verbatim `license_quote` under the companion
  spec's §1.4 mapping (now speaker-aware); a control whose attribution is not
  licensable is FLAGGED, never silently proceeded on (§7.2). This guards against the
  foreseeable FALSE REVERT at MEASURE — the cycle killed by a licensing gap, not a
  mechanism failure.
* **S-1 — lapse condition on the demoted-clause exclusion.** The §4B CLASS RULE's
  exclusion of demoted clauses (m0239) from the regression bound now carries a
  pre-registered LAPSE CONDITION: if the IMPLIED-EFFECTS layer is rejected, dropped, or
  never built, the exclusion lapses and the demoted clause re-enters the bound — the
  exclusion cannot become a permanent immunization of an adjudicated regression with no
  receiver (§4B, §7.1, §7 plank 3).
* **Minors.** (i) The m0108 seat-defect review is cited as DONE
  (`cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`, 2026-08-04: the
  harm m0108 guards falls on the user's own organisation, not third parties; a genuine
  definition-ambiguity flagged; the `unclear` accounting stands) — §7.1, §8/D2, §9.
  (ii) §5.1's keying is the 3-tuple `(clause_id, span_id, name)`, matching the
  companion spec's schema; the former 2-field `(clause_id, span_id)` shorthand was
  ambiguous (190 such pairs in the frozen translation carry more than one atom).

**REVISION 6 recorded the coordinator's D4 ruling: generic nouns ("people",
"individuals") carry multiple meanings and are disambiguated at TRANSLATION/ATTRIBUTION
time — NOT via a pricing-time generic flag** (§4C, §5.3, §7.1, §8/D4). The attribution
fixes each OCCURRENCE's referent. A COMPREHENSIVE generic — m0018's "people", the
beneficiaries of a universal provision — is attributed `harm_bearers` = the FULL
principal set, which intersects every non-empty declared P, so the clause surfaces for
ANY matching query; §5.3 branch 2 is REDEFINED as this comprehensive-generic case
(factor 1.0, cap-exempt — the branch is KEPT and its cap-exemption logic preserved, now
grounded in the disambiguation). A SPECIFIC generic — m0248's "individuals", the
targets of a harm — is attributed the specific party and prices by branches 3/4: for a
helpfulness query (P = {user, developer}) it draws factor d, exactly golden derivation
case #5. Because the disambiguation is per-occurrence, there is no global
"generic ⇒ factor 1.0" rule — that is how the ruling resolves the m0248 golden
collision (§2.1, §4C). **All REVISION 5 fixes — RULING 1 (R4-B1), RULING 2 (D1),
R4-E1, R4-E2, R4-E3, R4-S1 — and every REVISION 4 and REVISION 3 fix named below are
retained intact; this revision changes only what D4 governs.** Rulings now: D1, D3, and
D4 RULED; D5 RULED 2026-08-05 (b-trim/439, §8); D2 remains open (§8). (At REVISION 6 this note, the §8 heading, and §9
still called D3 OPEN while §8-D3 recorded it RULED; REVISION 7 reconciled every
location to RULED — D3 UNIFORM, no distinct example-kind rule, latent fix LF-1; see the
REVISION 7 note above, R6-E-1.)

**REVISION 5 applied the coordinator's two rulings on the R4 re-review and fixed its
four major findings** (`S3B_ADVERSARIAL_REVIEW_R4.md`, verdict REVISE — 1 new blocking /
4 major / 6 minor; the three prior blockers and all ten R3-era fixes verified present).
**RULING 1 (R4-B1, option (a)):** a pre-registered CLASS RULE — clauses demoted to the
IMPLIED-EFFECTS layer by ruling are excluded from S3b's regression bound (plank 3,
`max_regressions`) and are tracked by that layer instead; m0239 named as the single
current instance; grounded in "re-adjudicating an already-adjudicated document-side
verdict adds no information" (§4B, §7.1, §7.3). **RULING 2 (D1, option (a)):** delivery
is the ANNOTATION-SIDE BACKFILL — the attribution task designed to be mechanical enough
for a capable-but-cheap seat (closed output vocabulary, verbatim license_quote, fixed
decision procedure, error-recovery loop), the cheap seat gated on a pre-registered parity
validation against a frontier model before the backfill runs, and §7.5's reach R
informing the backfill scope; substance in the companion spec
`S3B_ATTRIBUTION_TASK_DESIGN.md` (§5.2). **MAJOR FIXES: R4-E1** — the mixed-clause
surviving-mass formula re-stated on ONE scale aligned with patient.py's mechanics
(penalty-subtraction form), the capped mass and the exempt set defined exactly, and the
pinned test re-stated to pin the FORMULA — both terms — plus a generic-atom variant, not
just the factors (§5.3). **R4-E2** — subsumption-priced records take the same attribution
factors, cap, and exemption; overlay-empty pinned as a build precondition with an S5
re-review check pre-registered for overlay reactivation (§5.3). **R4-E3** — §2.2
re-marked AMENDED and its F-linearity guarantee scoped to RESOLVED mass; the
dense-`unclear` escape mode disclosed as the cost of the forced horn and monitored by a
pre-registered MEASURE-time exempt-mass report (§2.2, §5.3). **R4-S1** — the §7.5 floor
is committed BLIND, before the reach estimate is seen, and the denominator band is pinned
with the D5 ruling (§7.5). **At REVISION 5, D3 and D4 remained OPEN designer rulings, and
that revision resolved nothing that was not ruled — D4 has since been RULED (REVISION 6
note above); D3 has since been RULED UNIFORM (§8/D3; the stale "D3 remains OPEN" text
carried at REVISION 6 was reconciled in REVISION 7, R6-E-1).** All REVISION-4 fixes are
retained intact — the
E-1 horn choice, the S-1/S-2 restoration disjunction, E-2/M-2 keying, E-3/M-1 value
space, S-3/M-3 derivation re-argument, S-4/M-4 gate structure, E-4 population seat, E-5
whitelist fence, E-6 seam, E-7 citation — as are REVISION 3's (B-1 atom-level totality,
B-2 ruling (b), B-3 core insight).

Governing constraint: work that needs a frontier session and must NOT be started
otherwise (model-dispatch memory; HANDOFF). This design is written to be *attacked*,
not executed, in the current session.

---

## 0. Scope and method

This redesign prices the same census class S3 targeted — `fp_promiscuous_atom`
(155 cases, 53% of the 294-case census) — but fixes the PROVENANCE defect that
reverted S3. It does **not** touch the discount arithmetic, the taint cap, or the
derivation pattern; those passed and are carried forward unchanged (§2). Every claim
below is grounded in the S3 cycle record: `decision.json` (justification, findings
i–iii), `ADJUDICATION_LEGS.md`, `flip_verdicts.json`, `flip_verdicts_verification_leg.json`,
`DISCOUNT_DERIVATION.md`, and the flip dossiers under `flip_dossiers/`.

The falsification bar for S3b is pre-registered in §7.

---

## 1. What S3 proved — the three findings, restated as design inputs

From `decision.json` (REVERT, 2026-08-04; 4 confirmed regressions + 1 contested at
the strict two-leg count; `max_regressions: 0` bound breached):

* **Finding (i) — CLAUSE TAINT INHERITANCE.** Patient-free atoms are discounted
  through a *sibling* user-directed remedial act in the same clause. In example
  passages the model's remedial act is almost always addressed to the user, so any
  example whose harm falls on a third party but whose modelled response speaks to the
  user is tainted regardless of who is harmed. Confirmed regressions of this shape:
  **m0275, m0466**; contested **m0108** (same shape, split-blind divergence).
* **Finding (ii) — RECIPIENT ≠ HARM-BEARER.** Protective acts UPON the user FOR
  others' benefit fire the mismatch rule against needed clauses. Confirmed regression:
  **m0239** (de-escalating a user's radicalization protects third parties). Generic-noun
  variant: **m0018** ("People should have easy access…" annotated `third_party`, but
  "people" comprehends the users/developers a helpfulness query declares).
* **Finding (iii) — WHAT WORKED (must be preserved).** Patient-saturated wrong-patient
  clauses were correctly removed — **m0276** (self-harm, the canonical census false
  positive) and **m0290** (eating-disorder self-starvation), both adjudicated `correct`
  exactly as pre-registered. The golden-derived `d = 0.10` and the taint cap behaved
  exactly as `DISCOUNT_DERIVATION.md` derived them.

**The defect is patient PROVENANCE, not the discount arithmetic** (decision.json).
The pricing layer reads chains that record who an act is *addressed to* and treats
that as who the clause *protects*. S3b must price on the harm-bearer/beneficiary.

---

## 2. What is carried forward UNCHANGED (the review-stable core)

These passed S3 and are NOT reopened; a reviewer who believes one of them is wrong
should raise it as a blocking finding, not assume a silent re-litigation:

1. **`d = 0.10`**, the derived module constant (`DISCOUNT_DERIVATION.md`, frozen,
   sha-pinned). NOT a tuning target. If S3b's mechanism change breaks the d-plateau,
   the remedy is the one CYCLE5_DESIGN §1.4/§5-Q6 prescribes (citation corrected per
   R3/E-7 — it is NOT a section of DISCOUNT_DERIVATION.md, which has §0–§4 only):
   **re-derive blind** from golden patient-contrast cases — never re-tie-break after
   seeing which clause crosses (ruled explicitly at the m0355 knife-edge).
   **RE-ARGUMENT REQUIRED BEFORE OPEN (S-3/M-3, R3 re-review).** The derivation that
   LICENSED 0.10 priced its eight golden cases under CHAIN-based taint; S3b re-prices
   them under attribution semantics. Before OPEN, re-argue derivation cases #1–#8 under
   the §5.3 rule (blind, document-side, the same seat pattern). The known collision is
   case #5 (m0248, "abuse, harassment, or negativity toward **individuals**", golden
   judgment (b) = factor d): §4C's generic test ("comprehends all principals") would flag
   "individuals" generic ⇒ factor 1.0, inverting golden judgment #5. Resolve by EITHER a
   mechanical generic criterion that separates m0018's "people" from m0248's "individuals"
   (pre-registered, golden-testable), OR concede §5.3 re-prices derivation cases and
   pre-register blind re-derivation of d under the amended rule as the OPEN remedy — with
   the re-argued golden table, not an inherited constant, as the licensing basis.
   **DISPOSITION (REVISION 6, D4 RULED):** the collision is resolved at TRANSLATION
   time — the first horn, realized as per-occurrence generic-noun referent
   disambiguation (§4C): m0248's "individuals" disambiguates SPECIFIC (the targets of
   the harm ⇒ factor d preserved, golden judgment #5 intact), m0018's "people"
   disambiguates COMPREHENSIVE (§5.3 branch 2). The separation is golden-testable —
   m0018 and m0248 are the pre-registered golden verification cases
   (`S3B_ATTRIBUTION_TASK_DESIGN.md` §2.5). The re-argument of cases #1–#8 under the
   §5.3 rule still runs before OPEN.
2. **The taint cap** (F-linearity fix) — **statement AMENDED (E-1, R3; re-stated R4-E1,
   scoped R4-E3); the mechanism itself carried forward.** Under clause taint the
   surviving RESOLVED mass is ONE discounted credit (`d · max(base credits over
   resolved+specific credited matches)/atom_norm`), never `d · Σ`. **F-LINEARITY SCOPE
   (R4-E3): the guarantee is scoped to RESOLVED mass** — dense uniformly-wrong-patient
   clauses must not retain RESOLVED residual mass proportional to match count. The cap
   itself is not implicated in any of the four regressions. **Mixed-clause composition
   (E-1, R3; horn re-stated R4-E1):** when a tainted clause also carries
   unresolved/comprehensive-generic atoms, the cap applies only to the RESOLVED+specific
   credited matches — unresolved/comprehensive-generic credits are cap-exempt and pass
   through at factor 1.0, all on one normalized scale (§5.3, SURVIVING MASS). Under the
   exemption, a tainted clause's EXEMPT mass IS linear in the number of exempt matches:
   that horn is forced
   (branch 1's "never as a discount" promise and I1 allow no other), and the
   dense-`unclear` escape it opens — a clause whose wrong-patient atoms all draw
   `unclear` verdicts stays predicted, no flip, no adjudication — is disclosed and
   monitored, not denied: a pre-registered MEASURE-time per-clause exempt-mass report
   plus §7.6's stratified golden review of `unclear` verdicts (§5.3, EXEMPT-MASS
   DISCLOSURE). The complete total rule — capped mass, exempt set, one-scale formula,
   penalty form, survivor tie-break, subsumption composition — is stated in §5.3.
3. **The derivation pattern** (`DISCOUNT_DERIVATION.md`): outcome-blind, golden-contrast
   constant derivation. Reused verbatim if a re-derivation fires.
4. **Opt-in, bit-identity invariants** (I1/I2): no declared patients ⇒ bit-identical to
   ContainmentIndex; all factors ≤ 1, raw scores monotone downward; never default-on;
   declarations licensed panel-blind by the behaviour's own prose, never by a panel number.
5. **The canonical removals** m0276 and m0290: any S3b mechanism that re-surfaces either
   of these has failed its own reason to exist.

---

## 3. The load-bearing structural fact (why chains alone cannot fix this)

The grammar's principal chains are **agent-first**: `..__model_user` reads "the MODEL
acts, upon the USER" (grammar.describe). A chain of length ≥ 2 records
`[agent, recipient]` — WHO ACTS, UPON WHOM. It does **not** record the party the
harm or the protection ultimately *falls on*.

The defining contrast, from the m0275 dossier (`explain_b.patient_pricing`):

| | m0276 (self-harm) — KEEP removed | m0275 ("I want to shoot someone") — RESTORE |
|---|---|---|
| matched atom for a third-party query | patient-free `imminent_bodily_harm` / user-chained self-harm atoms | patient-free **situation** `expressed_harmful_intent`, gloss *"the user expresses an intention to harm another person"* |
| patient-bearing siblings | `mustnot_enable_self_harm`, `should_provide_supportive_response`, `must_advise_immediate_help` — all **user**, all self-harm | `should_provide_supportive_response__model_user` — **user**, the remedial act |
| harm actually falls on | the **user** (self-harm is definitionally harm to the speaker) | a **third party** ("another person") |
| third-party query should | **suppress** (clause protects the user, not third parties) | **surface** (the situation IS third-party harm; the remedy addresses the user but protects others) |

Both clauses have the SAME chain shape: a patient-free harm-describing atom plus a
user-directed act atom. The only thing that separates "suppress" (m0276) from "surface"
(m0275) is **who the harm falls on** — and that lives in the situation atom's *gloss*
("harm another person" vs "self-harm"), which is text, not machine-readable chain
metadata. **No value of `d`, and no rule over chains as currently recorded, can
separate them.** This is the same wall the derivation hit on its (a)/(b) separator
(`DISCOUNT_DERIVATION.md` §3: "that information lives in the clause TEXT … not in the
chain metadata the pricing reads").

**Consequence:** S3b needs the pricing to read the **harm-bearer / beneficiary**, which
must be *attributed* — either by annotation or by a panel-blind seat at index time. It
cannot be recovered from the existing chain field alone.

---

## 4. The three sub-defects, and the mechanism each needs

The four confirmed regressions (+contested m0108) are not one defect but three, and a
redesign that fixes only one will still breach the bound. Each is stated with its
evidence and its candidate fixes.

### 4A. Taint inheritance onto a matched patient-free situation atom (m0275, m0466, m0108)

**Evidence.** m0275: the matched atom is the patient-free situation
`expressed_harmful_intent`; the clause's only patient-bearing chain is the sibling
remedial act `should_provide_supportive_response` → user. Since that single chain is
mismatched with `third_party`, the clause is "uniformly mismatch-attested", so the
patient-free situation match is discounted to `factor 0.1` via `why: clause_taint`
(atom channel 0.6 → 0.06; score 0.351 → 0.131 < cut 0.2365). m0466 is the same shape
(anthrax request; taint from the model-upon-user refusal act, which does not bear on
who would be harmed by the requested advice). Contested m0108 is the same shape
(compromised-instruction example; the only match is the patient-free situation atom
`harmful_instructions`).

**The error.** Clause-level taint propagates from a *remedial act's* recipient to a
*harm-describing situation atom* that is itself the query's match. The situation atom
correctly names the harm and its bearer; it is discounted because of who the model's
response is addressed to.

**Candidate fixes.**
* **A-structural (no re-annotation) — WITHDRAWN as an independent fix (B2).** As first
  drafted this read: do not let clause taint discount a MATCHED patient-free `situation`
  atom when every patient-bearing atom on the clause is a model-agent `act`. Verified
  against the dossiers, that rule CANNOT work alone: m0275 (must surface) and m0276 (must
  stay suppressed) are structurally identical under it — each is a matched patient-free
  situation (`expressed_harmful_intent` / `imminent_bodily_harm`) plus a sibling
  user-directed model-act. The rule would protect BOTH, resurfacing m0276 — the automatic
  REVERT of §7.2. The separator is the harm-bearer in the gloss (§3's wall), which only
  attribution reads. A-structural is retained ONLY as an attribution-gated component of
  §5.3/§5.4; if any version is ever floated standalone it needs STRATIFIED controls (the
  S2 golden-review pattern over affected clauses), not just m0276/m0290 (N3).
* **A-attribution (principled).** Price the situation atom on its ATTRIBUTED harm-bearer
  (§5). If the attributed harm-bearer ∈ P, factor 1.0 regardless of sibling acts. This
  fixes A, B, and C with one mechanism, but requires the attribution step.

### 4B. Recipient ≠ harm-bearer on a protective/remeial act (m0239)

**Evidence.** m0239: "If a user shows signs of vulnerability to radicalization, the
assistant should aim to de-escalate…". The act `should_deescalate_extremist_involvement`
is directed at the user, but the harm averted (extremist violence) falls on third
parties. Adjudication (leg 1, regression, high): "Radicalization leads to violence
against third parties. An auditor of third-party harm avoidance would need this
guidance on de-escalating potential perpetrators." decision.json: "dropping it on the
ground that the model's act is addressed to the user mistakes the recipient of the
intervention for the bearer of the harm."

**The error.** The chain's recipient (the user being de-escalated) is read as the party
the clause protects. The clause actually protects *potential victims* — third parties.

**Candidate fixes and SCOPE RULING (b, coordinator 2026-08-04).** A-structural does NOT
cover this (the act atom IS patient-bearing and genuinely mismatches `third_party`). And —
verified against the m0239 dossier — STRICT document-grounded attribution cannot cover it
either: the matched atom is `should_deescalate_extremist_involvement` and every gloss is
user-focused ("the user shows signs of being susceptible to extremist recruitment…",
"reduces the user's movement toward participation in extremist activity"); no span of the
clause names a third party, and the third-party beneficiary is supplied only by inference
("radicalization leads to violence against third parties" — the adjudicator's own words).
§5.1 requires a verbatim, document-grounded `license_quote`, and
`briefs/backfill_author.md` rule 3 explicitly FORBIDS inferring an affected party from the
subject matter (precedent: m0236's `__model_third_party` chain was removed on exactly that
ground). **RULING (b): m0239 is DEMOTED from S3b's falsifiable core.** This is not a
failure of strict attribution; it is outside what document-grounded attribution can reach
by construction. m0239 becomes the canonical first member of the separate IMPLIED-EFFECTS
layer (`IMPLIED_EFFECTS_DESIGN.md`) — a human-approved, provenance-logged judgement,
droppable and deterministic once logged — rather than something S3b's strict mechanism
restores. S3b's core is therefore m0275 + m0466 + m0018 (D4 is now RULED —
comprehensive-generic disambiguation, §4C); see §7.1.

**CLASS RULE (R4-B1 fix; coordinator ruling 2026-08-05, option (a) — pre-registered).**
Clauses DEMOTED to the IMPLIED-EFFECTS layer by ruling are EXCLUDED from S3b's regression
bound (§7 plank 3, `max_regressions`) and are tracked by that layer instead. This is a
GENERAL class rule, not an ad-hoc clause exclusion: it attaches to the act of
demotion-by-ruling, so any future clause demoted the same way is excluded the same way,
and no clause is named in the rule itself. It does NOT immunize pricing — S3b's mechanism
is corpus-wide and still prices a demoted clause like any other attributed clause; what
is excluded is counting its flip against the bound. GROUND: re-adjudicating an
already-adjudicated document-side verdict adds no information. A demotion is ruled
precisely because strict document-grounded attribution cannot reach the clause, so S3b's
mechanism re-suppresses it predictably; the removal's adjudication is document-side and
mechanism-independent, and counting the reproduced removal against `max_regressions`
would measure the ruling, not the mechanism. m0239 is the rule's single current
instance: its removal was adjudicated in S3 as a regression (`flip_verdicts.json`,
regression/high) and BIDIRECTIONALLY CONFIRMED ("Radicalization leads to violence against
third parties…"), so a re-adjudication of the same removal can only return the same
verdict; its disposition is the IMPLIED-EFFECTS layer (this §4B; §7.1; §7.3), which
tracks it from here.

**LAPSE CONDITION (R6-S-1; pre-registered with the class rule; STATE SPACE COMPLETED
R8-S-B).** This bound exclusion holds only while the IMPLIED-EFFECTS layer is an
active, reviewed work item that has accepted the demoted clause as a tracked entry
(the RECEIVER READINESS condition).
**MEASURE-TIME SEMANTICS (stated explicitly, R8-S-B).** The exclusion holds at
MEASURE only if receiver readiness holds AT MEASURE — the receiver has passed review
AND accepted m0239 as a tracked entry; otherwise (the implied-effects design
(`IMPLIED_EFFECTS_DESIGN.md`, currently DRAFT — design only, not yet reviewed) is
still unreviewed at MEASURE, or has not accepted m0239) the exclusion does NOT apply
and the demoted clause's expected flip IS counted against the §7.3 bound like any
other flip. Because the exclusion is pre-registered AT OPEN, OPEN is gated on
receiver readiness (§9): a coordinator must not open S3b on the D2/D5 rulings alone
while the receiver is still unreviewed — that would let the cycle die at MEASURE on
a sibling design's review ordering, the exact false-fail class the §7.2 licensability
gate prevents for the controls. Receiver readiness regressing BETWEEN OPEN and
MEASURE (review rejects the design, acceptance withdrawn) remains governed by the
MEASURE-time statement above.
**LAPSE — ONE re-entry semantic, stated here and restated identically at §7.1 and
§7 plank 3 (R8-S-B).** If the implied-effects design is REJECTED in review, the work
is DROPPED, or the layer is NEVER BUILT, the exclusion LAPSES and the demoted clause
(m0239) re-enters THIS cycle's §7.3 regression bound — never "the next cycle's":
no future cycle re-flips a clause whose priced state is unchanged (the design
predicts branch-4 re-suppression deterministically), so a next-cycle-only re-entry
would count nothing and immunize permanently — exactly what this condition forbids.
Concretely: lapse established BEFORE MEASURE ⇒ the flip is counted at MEASURE; lapse
established AFTER the cycle's CLOSE ⇒ the flip S3b recorded and reported but did not
count (if the expected horn obtained, §7.1) is RE-COUNTED RETROACTIVELY against this
bound at the decision point where lapse is established — recorded in the repo's
decision record (the implied-effects review outcome, or a coordinator ruling noting
drop/never-built; rulings go in the repo, not the transcript). The re-adjudication
verdict is already settled (regression/high, bidirectionally confirmed in S3), so the
retroactive re-count breaches `max_regressions: 0`, and the cycle's closure is
revised to reflect the breach: the removal stands PRICED (S3b's mechanism still
produces it) but is no longer bound-excluded, and the receiver-less removal is an
explicit open item, never silently absorbed. The exclusion cannot become a permanent
immunization of an adjudicated regression with no receiver.

### 4C. Generic-noun patients over-scope (m0018) — D4 RULED 2026-08-05

**Evidence.** m0018: "People should have easy access to trustworthy safety-critical
information…" is annotated `third_party` (the generic noun "People"), but a helpfulness
query declares `[user, developer]`. Adjudication (regression, high): "This is a core
statement of what helpfulness means." decision.json: "'people' as written comprehends
the users and developers the model works with rather than excluding them."

**The error, restated under D4.** Generic nouns ("people", "individuals", "everyone")
carry MULTIPLE meanings, and the pre-ruling candidate fixes located the decision at the
wrong time: the meaning is fixed at TRANSLATION/ATTRIBUTION, not by a pricing-time
generic flag. The same word differentiates into distinct referents (think `people_broad`
vs `people_narrow`); the attribution determines each OCCURRENCE's referent, and the
pricing reads only the attributed `harm_bearers`:
* **m0018 — COMPREHENSIVE generic.** "People should have easy access…" states a
  universal provision; "people" here is the BENEFICIARY CLASS of that provision and
  comprehends every principal. Disambiguation: `harm_bearers` = the FULL principal set
  (all seven values of `grammar.py`'s `PRINCIPALS`). That set intersects every non-empty
  declared P, so the clause surfaces for ANY matching query — helpfulness's
  `[user, developer]` included — at factor 1.0 (§5.3 branch 2, redefined as the
  comprehensive-generic case; cap-exempt).
* **m0248 — SPECIFIC generic.** "…gratuitous abuse, harassment, or negativity toward
  individuals" names the TARGETS of a harm; "individuals" here is a specific party named
  by a generic noun. Disambiguation: `harm_bearers` = the specific party
  (`third_party`). For a helpfulness query (P = {user, developer}) the bearers are
  disjoint from P ⇒ factor d (§5.3 branch 4) — golden derivation case #5 preserved
  exactly (§2.1).
**The disambiguation is per-OCCURRENCE** — the same noun may resolve differently in
different clauses — so there is no global "generic ⇒ factor 1.0" rule, and that is what
resolves the m0248 golden collision without re-deriving d. m0248-style SPECIFIC
generics never take branch 2; they price via branches 3/4 by their specific
`harm_bearers`. The attribution's disambiguation sub-task, and m0018/m0248 as GOLDEN
VERIFICATION CASES, are specified in `S3B_ATTRIBUTION_TASK_DESIGN.md` (§1.3 step 4,
§2.5).

**Candidate fixes (as drafted pre-ruling — dispositions marked).**
* **C-generic flag — SUPERSEDED by D4.** Would have attributed, per patient-bearing
  atom, whether its patient was GENERIC (comprehends all principals) or SPECIFIC, with
  the flag read at PRICING time. The ruling replaces the pricing-time flag with the
  referent disambiguation above: the comprehensive/specific decision is made ONCE, at
  translation/attribution, and lands in `harm_bearers` itself; pricing reads bearers,
  never a flag.
* **CONVENTION ruling (generic-noun clauses patient-FREE, absence-is-absent) — REJECTED
  by D4.** Would have been cheaper but lost the "People" signal, needed an annotation
  ruling, and could not distinguish m0018's universal provision from m0248's specific
  harm-targets — the distinction the collision turns on.

---

## 5. The recommended mechanism: beneficiary-aware attribution

**Recommendation (to be confirmed or overturned by review): price on the attributed
HARM-BEARER / BENEFICIARY, not the chain's grammatical recipient.** Concretely:

1. **Attribution artifact.** For each patient-bearing atom (and each patient-free
   harm-describing atom, e.g. situation atoms), a **panel-blind, document-grounded**
   attribution records `harm_bearers` — the party/parties the harm or the protection
   ultimately falls on — plus, where the bearer is named by a generic noun, the referent
   DISAMBIGUATION that fixed that set (COMPREHENSIVE ⇒ the full principal set; SPECIFIC
   ⇒ the specific party — §4C/D4) and a short verbatim `license_quote`, exactly in the
   spirit of S2's validator-checked backfill. The
   attribution reads clause text + gloss + the golden chain convention only; it never
   opens a panel artifact, a judge rating, or a gold value (same fence as S3).
   **KEYING (E-2/M-2, R3; 3-tuple stated per R6-E-6): attribution is keyed per
   CLAUSE-INSTANCE — the 3-tuple `(clause_id, span_id, name)`, exactly the schema of
   `S3B_ATTRIBUTION_TASK_DESIGN.md` §1.2/E_KEY — NEVER per atom name ALONE** — the same
   atom name carries different harm-bearers in different clauses
   (`user_requests_harmful_advice` is third-party harm in m0466 but user self-harm in
   m0290, a §7.2 automatic-REVERT control), so name-only keying is self-contradictory
   and the error would land on m0290. NOR is the key the 2-field pair
   `(clause_id, span_id)`: measured over the frozen translation
   (`annotations_ext_v1_merged.json`), 190 such pairs carry MORE THAN ONE atom, so a
   2-field key would merge distinct rows into one. Validator-checked like S2's license
   quotes. The §5 preservation claim below is conditional on this keying.
   **VALUE SPACE (E-3/M-1, R3): `harm_bearers` is pinned to the existing principal
   vocabulary** (`backfill_author.md`: third_party, developer, operator, system, model,
   root, user); the noun-phrase→principal mapping ("another person"→third_party,
   "someone"→third_party, "the user"→user) is stated in the attribution brief and
   validator-checked. §5.3 and §7.1 compute intersections on this vocabulary, so a correct
   attribution cannot silently fail an intersection by recording free text. A
   COMPREHENSIVE-generic disambiguation (§4C/D4) records the FULL set — all seven
   values; §5.3 branch 2 keys on exactly that set, so the disambiguation is a pure
   bearer-set decision with no free text anywhere.
   **BLINDNESS FENCE (B1 fix, coordinator review).** The fence ALSO excludes the answer
   key this document and the S3 cycle record constitute: the attribution seat must not
   read `S3B_REDESIGN.md`, the S3 cycle directory (`flip_verdicts*.json`,
   `flip_dossiers/`, `decision.json`, `ADJUDICATION_LEGS.md`), or the census — any of
   which name the outcomes the attributor is supposed to derive independently, colliding
   with §6's "attribution MUST NOT be fit to flip outcomes." Concretely: the attribution
   BRIEF is written standalone (S2's `briefs/backfill_author.md` precedent — it never
   mentioned pricing), is FORBIDDEN-token scanned like every query module, and the §7.1
   restore-check is run by a party the attributor never reports to, AFTER attribution is
   frozen. An attributor that can see the expected flips is transcribing, not attributing.
   RESIDUAL FENCE PATHS (adversarial review M-5): the exclusion ALSO covers this cycle's
   own prediction/decision artifacts (`prediction*.json`, `decision*.json`, and the
   restore-signature outputs of §7.1) and the rechain-repair channel (a rechain migration
   is a license to change chains, never to smuggle in an attribution); and the
   FORBIDDEN-token scan is necessary-but-not-sufficient — the standalone-brief requirement
   is the primary fence, the scan a backstop, never the guard itself.
   **WHITELIST, NOT DENYLIST (E-5, R3).** A denylist cannot work here: `HANDOFF.md` is
   this repo's mandated reading #1 for every agent (AGENTS.md) and it names all six
   load-bearing clauses WITH their required outcomes. The fence is therefore a WHITELIST,
   exactly S2's `backfill_author.md` mechanism ("What you see, and all you see"): the
   attribution seat's inputs are the brief + the attribution worksheet + the notation
   owners (grammar.py / annotate_prompt.md) and NOTHING ELSE; the seat is EXEMPT from the
   repo's standard context-loading (the AGENTS.md/HANDOFF reading order) for the duration
   of the pass; the denylist above is the backstop, not the fence.
2. **Delivery — RULED (D1, coordinator 2026-08-05, option (a)): the ANNOTATION-SIDE
   BACKFILL.** Extend the chain convention so harm-bearer is a first-class annotated
   field, shipped as a targeted backfill cycle (validator-checked, license-quoted,
   golden-reviewed) — the proven S2 machinery. Pricing stays fully mechanical (reads
   attributed harm-bearers). The index-side seat (former option (b)) is CLOSED by this
   ruling. The ruling carries three constraints:
   * **Mechanical task design.** The attribution task is designed to be mechanical
     enough for a capable-but-cheap model seat (candidate: DeepSeek V4 Flash).
     "Mechanical" here is a CLOSED list, and a task is mechanical iff it satisfies all
     four: (i) a CLOSED OUTPUT VOCABULARY — `harm_bearers` values drawn from the
     principal vocabulary only, plus the `unclear` sentinel (§5.1 VALUE SPACE);
     (ii) a VERBATIM `license_quote` for every non-`unclear` verdict; (iii) a FIXED
     DECISION PROCEDURE named in the attribution brief (no per-row improvisation); and
     (iv) an ERROR-RECOVERY LOOP — a mechanically malformed entry (a `license_quote`
     that does not verbatim-match the clause text, a reference that does not resolve,
     a value outside the closed vocabulary) produces an error and the model gets a
     chance to retry. The task's substance lives in the companion spec
     `S3B_ATTRIBUTION_TASK_DESIGN.md` (being written separately); this document fixes
     only the interface the pricing reads.
   * **Pre-registered parity gate.** The cheap seat is not trusted on design claims:
     BEFORE the backfill runs, a parity validation of the cheap model against a
     FRONTIER model on a stratified sample is pre-registered (strata per §2.2 of
     `S3B_ATTRIBUTION_TASK_DESIGN.md` — behaviour × kind × chained/patient-free, all
     computable from query-side facts and the frozen annotation BEFORE the task runs;
     NOT the §7.6 shape — a verdict stratum is not constructible at parity time,
     because verdicts are the OUTPUT of the task — R6-E-3), and the cheap seat is
     certified ONLY if parity clears the pre-registered threshold. Parity below
     threshold ⇒ the backfill runs on the frontier seat, or the task design is
     amended and re-gated.
   * **Scope informed by the reach R.** §7.5's strict-attribution reach R — together
     with the D5 denominator-band pin — informs the backfill scope: what is annotated,
     in what order, at what cost. The §7.5 floor gate binds before the backfill is
     commissioned.
3. **Pricing rule, amended (B-1 fix, adversarial review — now TOTAL and computable).**
   First, the MECHANICAL DEFINITIONS the rule quantifies over (both were missing, and the
   rule is unbuildable without them):
   * An atom is **harm-bearing** iff it carries an attribution record whose
     `harm_bearers` set is NON-EMPTY. An `unclear` or empty record is NOT harm-bearing.
     The attribution artifact is the SOLE source of harm-bearers, so this predicate is a
     pure read of it — no chains, no kinds, no glosses.
   * An attribution record is **resolved** iff `harm_bearers` is non-empty and not the
     sentinel `unclear`.
   For a query with declared patients P, the factor for a credited match through atom `a`
   is the FIRST matching branch, in this order (precedence is part of the rule):
   1. **Attribution absent or UNRESOLVED** (no record, empty `harm_bearers`, or
      `unclear`): factor 1.0 from this layer, and `a` is EXCLUDED from the clause-taint
      quantifier below. This is the only reading consistent with I1 — an atom the
      attribution does not resolve prices exactly as it does today, never as a discount.
      `unclear` is a first-class legal attribution verdict (S2's
      `briefs/backfill_author.md`: "never force a call"), so this branch is a foreseeable
      input, not an edge case.
   2. **Comprehensive generic (D4 RULED 2026-08-05 — branch REDEFINED, not removed)**:
      `a` is resolved and its attribution disambiguated a generic-noun bearer
      COMPREHENSIVE — mechanically: `harm_bearers(a)` = the FULL principal set (all
      seven values; §4C): factor 1.0; excluded from the taint quantifier; cap-EXEMPT
      (EXEMPT set below). GROUNDING: a comprehensive generic is the beneficiary class of
      a universal provision (m0018's "people"), so its bearer set intersects every
      non-empty declared P — the atom is consistent with every query and surfaces for
      any matching query, helpfulness's `[user, developer]` included. The branch is
      grounded in the attribution's disambiguation verdict (recorded with its license
      quote, §5.1), NOT in a pricing-time flag; it is KEPT deliberately because it is
      what carries the cap-exemption logic for comprehensive-generic credits on mixed
      clauses (E-1 horn below). **SCOPE PIN: only COMPREHENSIVE generics take this
      branch.** An m0248-style SPECIFIC generic — a generic noun disambiguated to the
      targets of a harm — carries the SPECIFIC party as `harm_bearers` and falls through
      to branches 3/4, pricing like any resolved+specific atom (factor d for a
      helpfulness query; golden derivation case #5 preserved). The dependence on D4 is
      resolved, not left implicit: D4's REVISION-5 FLAG horn is superseded by the
      disambiguation, and its patient-free horn was rejected (§4C), so branch 2 is live.
   3. **Consistent**: `a` is resolved+specific and `harm_bearers(a) ∩ P ≠ ∅`: factor 1.0.
   4. **Mismatched**: `a` is resolved+specific and `harm_bearers(a) ∩ P = ∅`: factor d.
      (In branches 3–4, "specific" = resolved and not comprehensive-generic: branch 2's
      precedence has already caught every comprehensive disambiguation.)
   **Clause taint (EXISTENTIAL IMPORT — restores S3's precondition in attributed terms).**
   The clause is tainted iff it has AT LEAST ONE resolved+specific harm-bearing atom with
   `harm_bearers ∩ P = ∅`, AND every resolved+specific harm-bearing atom on it is disjoint
   from P. A clause with ZERO resolved harm-bearers is NOT tainted — this is what I1
   requires and what REVISION 2's vacuous reading violated (it made "every harm-bearing
   atom disjoint" true when none existed). This re-expresses DISCOUNT_DERIVATION §0's
   taint precondition ("≥1 patient-bearing chain, none consistent") over attributed
   harm-bearers.
   **Cap composition on MIXED clauses (E-1, R3 — the horn chosen; formula re-stated
   R4-E1).** When a tainted clause also carries unresolved (branch-1) or
   comprehensive-generic (branch-2) atom credits, those credits are EXEMPT from the cap;
   the cap applies only to the RESOLVED+specific credits. This is the only horn
   consistent with branch 1's
   "never as a discount" promise and I1 — crushing an `unclear` atom via a resolved
   sibling's taint would discount exactly what branch 1 guarantees is never discounted.
   **THE CAPPED MASS vs THE EXEMPT SET, EXACTLY.** The unit is the CREDITED RECORD —
   one per credited match, exact or subsumption (COMPOSITION WITH SUBSUMPTION below),
   carrying its `base_credit` on the RAW-IDF scale patient.py's records carry
   (idf × kind factor for exact matches; the min-idf-capped containment credit for
   subsumption matches). On a TAINTED clause:
   * CAPPED = every credited record whose clause atom is RESOLVED+specific. By taint's
     definition these are all branch-4 (mismatched), factor d pre-cap. The SURVIVOR —
     highest `base_credit` among capped records, ties lexicographic on (clause_atom,
     query_atom, match); patient.py's tie-break re-stated — keeps factor d; every other
     capped record is zeroed (factor 0.0, `why: taint_capped`).
   * EXEMPT = every credited record whose clause atom is UNRESOLVED (branch 1: no
     record, empty `harm_bearers`, or `unclear`) or COMPREHENSIVE-GENERIC (branch 2:
     `harm_bearers` = the full principal set): factor 1.0, untouched by the cap.
   (Taint itself quantifies over resolved+specific harm-bearing ATOMS, credited or not;
   the cap quantifies over credited RECORDS through resolved+specific atoms.)
   **SURVIVING MASS — one scale (R4-E1 re-statement; supersedes the REVISION-4 formula,
   which mixed a normalized first term with a raw-idf Σ term and thereby inflated exempt
   credits ≈atom_norm-fold, breaking never-outprice on exactly the clauses the E-1 fix
   was written for).** All base credits below are raw-idf; normalization happens ONCE:
   `tainted atom channel = (d · max(base_credit over CAPPED records)
                            + Σ(base_credit over EXEMPT records)) / atom_norm`
   An empty capped set contributes nothing to the first term: taint's existential import
   is over the clause's resolved+specific ATOMS, and the query may credit only exempt
   matches on a tainted clause (then the penalty below is zero and the clause prices at
   baseline — branch 1's promise extended from atoms to matches). IMPLEMENTATION FORM
   (the shipped form): penalty-subtraction from the base channel, patient.py's
   `_atom_score` shape — `priced = base_channel − penalty/atom_norm`, `penalty =
   Σ(base_credit − priced_credit)` over records with factor ≠ 1.0, so exempt records
   contribute zero penalty. The subtraction form, not a re-summation, because it is what
   makes I1's bit-identity hold float-exactly (no discounted records ⇒ penalty 0.0 ⇒
   the base class's float, bit for bit). Never-outprice holds: exempt credits price at
   baseline, capped credits at ≤ baseline, so the tainted channel ≤ the baseline
   channel.
   **PINNED TEST (pre-registered; re-stated R4-E1 to pin the FORMULA — both terms — not
   just the factors).** Constructed mixed clauses with a declared-disjoint P; each
   variant asserts the priced atom-channel MASS, not only per-record factors:
   * VARIANT A (`unclear`): one `unclear` situation atom as the match (base credit b_u)
     + one resolved+specific act atom whose `harm_bearers` are disjoint from P (base
     credit b_r), both credited, clause atom_norm N. Assert: clause tainted; the match
     factor 1.0 and cap-exempt; the resolved record the cap survivor at factor d; atom
     channel == (d · b_r + b_u)/N — both terms, raw scale, normalized once — and ≤ the
     baseline channel (b_r + b_u)/N; equivalently priced == base_channel − (1 − d) ·
     b_r/N.
   * VARIANT B (comprehensive generic): the same shape with the match atom resolved and
     disambiguated COMPREHENSIVE (`harm_bearers` = the full principal set; base credit
     b_g). Assert: the comprehensive-generic record prices at factor 1.0, cap-EXEMPT —
     not d-priced, not zeroed — and atom channel == (d · b_r + b_g)/N. This variant pins
     the max-scope: a max ranging over comprehensive generics (the REVISION-4 formula's
     second defect) would d-price or zero the generic credit and fail the mass
     assertion.
   Variant A is the m0108 shape (S-7). A reading that crushes the `unclear`/
   comprehensive-generic match, mixes scales, or widens the max fails the test — the
   reading is code, not commentary.
   Under taint the (restated) cap applies. A remedial ACT atom whose
   attributed beneficiary ∈ P, or whose attributed harm-bearer is the situation's victim,
   does NOT taint a sibling harm-situation atom. **This is the single rule change that
   fixes 4A** (the 4B shape is covered by the same mechanism but exercised by no
   in-scope clause — §7.1 SCOPE OF THE CORE; m0239 itself is disposed of by ruling (b)
   and the §4B CLASS RULE). Golden review of the attribution MUST cover the
   `unclear`/empty verdicts, not only the positive ones (PORTFOLIO_REVIEW F10's fence
   pattern: golden review covered `no_chain` verdicts for exactly this reason).
   **COMPOSITION WITH SUBSUMPTION (R4-E2 fix — totality made explicit).** patient.py's
   contract prices a second class of credited match: subsumption matches — "a
   subsumption match's patient factor reads the CLAUSE atom's chain … and multiplies
   INSIDE the min-idf-capped credit"; `_patient_pricing` builds one record per
   subsumption match, and those records are the objects the cap discounts. Under S3b
   subsumption-priced records take the SAME rule as exact matches: a subsumption record
   is a credited match THROUGH its clause atom, so its factor reads the ATTRIBUTION
   RECORD of that credited clause atom (never the subsumer's), and it enters the capped
   mass or the exempt set exactly as an exact record would (base credit = the
   min-idf-capped containment credit), with never-outprice preserved inside the
   min-idf-capped credit (both discounts ≤ 1). SCOPE PIN: today this composition is
   LATENT — the overlay is empty (`overlay_empty.json`, in the S3 closure set) and S5
   (overlay reactivation) is "Not yet started" (HANDOFF) — so S3b requires
   OVERLAY-EMPTY as a build precondition, and S5 MUST re-review and re-pin this rule,
   with a priced subsumption record in its test surface, BEFORE reactivating the
   overlay. The totality claim of the pricing rule is conditional on that pin.
   **EXEMPT-MASS DISCLOSURE AND MONITORING (R4-E3 fix — the cost of the forced horn,
   owned).** Under the exemption a tainted clause's surviving mass is linear in its
   number of EXEMPT matches — exactly the leak shape the cap was built to kill
   (DISCOUNT_DERIVATION §3's F-linearity; patient.py: "more mismatched chains mean
   more suppression, not linearly more residual"). The F-linearity guarantee therefore
   holds for RESOLVED mass only, and §2.2 is scoped accordingly. The escape mode this
   opens is one-sided and flip-invisible: attribution errors and attributor laziness
   both flow toward `unclear` ⇒ branch 1 ⇒ baseline pricing ⇒ never suppressed (the
   discount fires only on resolved+specific+disjoint verdicts), so a dense
   wrong-patient clause whose atoms draw `unclear` verdicts escapes suppression and
   STAYS PREDICTED — no flip, no adjudication, invisible to every flip-based control.
   The exemption is nonetheless FORCED (branch 1 and I1 allow no other horn), so the
   design's answer is monitored disclosure, not a mass bound that would re-break
   branch 1.
   **A SECOND HORN OF THE SAME ESCAPE (R6-S-3 — named, not absorbed).** The one-sided,
   flip-invisible shape is not unique to `unclear`: a clause whose CORRECT verdict is
   resolved+specific+disjoint (factor d, suppressed) escapes IDENTICALLY if the seat
   instead disambiguates a generic-noun bearer COMPREHENSIVE — branch 2, factor 1.0,
   cap- and taint-exempt, baseline price, and no flip when baseline-predicted.
   Monitoring covers this horn mechanically: the EXEMPT set includes comprehensive-
   generic records, so the pre-registered exempt-mass report below and §7.6's
   comprehensive-generic golden stratum both see it. But golden coverage in the leak
   direction is exactly the two §2.5 golden verification cases of
   `S3B_ATTRIBUTION_TASK_DESIGN.md` (m0018/m0248), plus §2.5's FROZEN-BACKFILL
   RE-CHECK CASES for the falsifiable-core clauses m0275/m0466 (R8-S-A — immutable
   expected verdicts: resolved, `harm_bearers` exactly {third_party}, not
   comprehensive), plus the §7.6 stratified sample, and nothing more corpus-wide:
   the validator CANNOT check that a comprehensive verdict corresponds to an actual
   generic noun in the clause text (E_CONSISTENCY enforces the set-shape only), so
   branch 2's SCOPE PIN is enforceable only through the parity gate, golden review,
   and — for the named falsifiable-core clauses — the §2.5 frozen-backfill re-check.
   That is inherent to D4 and is accepted here, stated where the escape is disclosed.
   * PRE-REGISTERED MEASURE-TIME REPORT: for every tainted clause, per-clause EXEMPT
     MASS (the Σ term of the surviving-mass formula) and the exempt share of surviving
     mass, reported corpus-wide with its maximum — the explain trail already carries
     the fields (patient.py's records carry `base_credit`, `priced_credit`, `factor`
     per credited match; §5.6 extends it). A systematic `unclear` bias shows up as a
     number, not an absence.
   * NAMED RESPONSE: clauses at the top of that list get their `unclear` verdicts
     re-examined by golden review (document-side, the §7.6 machinery) — never by
     re-pricing toward a target.
   The two canonical controls (§7.2) cover only m0276/m0290, and §7.6's stratified
   golden review carries the `unclear` stratum on a sample; this report is the
   corpus-wide third leg.
4. **The cross-sibling guard is ATTRIBUTION-GATED, not an independent step (B2 fix,
   coordinator review).** The first draft offered §4A-A-structural as belt-and-braces
   shippable "before attribution lands," independently justified by m0275/m0466/m0108.
   That is WRONG and is withdrawn. m0276 is suppressed for a third-party query through
   exactly that path — verified against the m0276 dossier: the match runs through the
   patient-free situation `imminent_bodily_harm`, the three patient-bearing siblings are
   user-directed, `clause_tainted` is true, and the matched atom is discounted to 0.1.
   m0275 and m0276 are STRUCTURALLY IDENTICAL under the structural guard (matched
   patient-free situation + sibling user-directed model-act), so no attribution-free rule
   can surface m0275 without also resurfacing m0276 — the automatic REVERT of §7.2. The
   cross-sibling guard therefore ships ONLY inside the attribution mechanism (§5.3), where
   the attributed harm-bearer distinguishes m0275 (third party) from m0276 (user).
5. **The attribution population predicate (E-4, R3).** §8/D5's population — "patient-
   bearing atoms AND patient-free harm-describing atoms" — splits into a MECHANICAL half
   and a JUDGEMENT half, and the split must be explicit because record-presence is price-
   moving (§5.3 branch 1): "patient-bearing" is mechanical (length-≥2 chains); "harm-
   describing" is judgement and is given an OPERATIONAL DEFINITION — candidate generation
   by kind/gloss (e.g. `situation` atoms, or glosses bearing harm/benefit/risk
   vocabulary), then a PANEL-BLIND SEAT decision per candidate, recorded with a license
   quote, fenced exactly like the attribution itself (whitelist, §5.1). Golden review
   covers the BOUNDARY cases — atoms ADMITTED to the population and atoms REFUSED — not
   only the verdicts inside, so a mis-enumeration in the dangerous direction (a harm-
   describing atom left out, silently leaving a wrong-bearer clause un-discounted) is
   caught; the two named controls guard only m0276/m0290 themselves.
6. **The build seam (E-6, R3).** S3b ships the same three seam mechanics S3 did, named
   explicitly: a new `pricing_version` value in snapshot config identity (S3 was 2.0), a
   matching dispatch branch in `dossier.py` reconstruction, and an EXTENDED explain record
   carrying EVERYTHING the §7.1 restoration signature reads — without which the signature
   has nothing mechanical to read. COMPLETE FIELD LIST (R6-E-9): the attributed
   `harm_bearers`, the declared P, their intersection, and the priced record's extended
   `why` value under the §5.3 branches (consistent / mismatched / generic / taint_capped /
   `unclear`-or-absent). Arm (ii)'s disambiguation verdict AND its license quote live in
   the FROZEN ATTRIBUTION ARTIFACT, not the explain record; the independent §7.1 seat is
   GRANTED that read explicitly (explain trail + frozen attribution artifact), and the
   signature reads nothing else. The opt-in bit-identity invariants (§6 I1) ride this
   seam exactly as in S3.

**What this preserves (attribution-dependent AND conditional on clause-instance keying,
§5.1/E-2 — this claim provides no cover for any pre-attribution structural step):**
m0276 and m0290 stay suppressed because, once attribution exists, their harm-bearing
atoms attribute the USER as harm-bearer, disjoint from a third-party P. This presumes
those verdicts land RESOLVED and LICENSABLE: m0276's clause text carries verbatim "the
user" spans, and m0290's example-dialogue text names its bearer only through the
`<user>` speaker tag and first-person pronouns — licensable under the companion spec's
speaker-aware first-person rule (§1.4 note (v)). An `unclear` or unlicensed verdict
would price the control at branch 1, re-surface it, and trip §7.2's automatic REVERT —
which is why §7.2 carries a pre-OPEN LICENSABILITY GATE that verifies each control's
attribution per case before OPEN (R4 e-4 hedge, carried; R6-E-2 fix). d = 0.10 and the
cap are untouched; the opt-in/bit-identity invariants hold (no attribution ⇒ no declared
harm-bearers ⇒ bit-identical).

---

## 6. Invariants pre-registered for S3b

* **I1 bit-identity.** No declared patients, or no attributed harm-bearers, ⇒ bit-for-bit
  ContainmentIndex. Pinned by test, as in S3.
* **I2 monotone-downward on RAW scores.** All factors ≤ 1. Normalized-score bystander
  movement is `normalizer_drift` in the dossier, never `match_change` (S3/F3 convention).
* **No constant re-tuning.** `d` stays 0.10 unless the mechanism change breaks the
  d-plateau, in which case re-derive blind (the CYCLE5_DESIGN §1.4/§5-Q6 remedy; citation
  corrected per R3/E-7, and per §2.1 the golden cases must first be re-argued under the
  attribution rule), never re-tie-break post-hoc. The attribution MUST NOT be fit to flip
  outcomes (contract invariant 9; labels direct ATTENTION, never TRUTH).
* **Panel-blind.** Attribution and any index-side seat are panel-blind, scanned by
  `test_no_reference_leak.py`; declarations licensed by the behaviour's own prose only.
* **Never-outprice.** Any new factor path keeps every credit ≤ the un-discounted credit.

---

## 7. Falsification bar (pre-registered prediction skeleton)

The redesign's cycle must pre-register, at OPEN, a prediction whose falsifiable core is:

1. **Restore the confirmed regressions IN SCOPE (ruling (b), §4B).** m0275 and m0466
   return to `predicted` for harm-avoidance-to-third-parties; m0018 returns for
   helpfulness UNDER the D4 ruling — its generic noun ("people") disambiguates
   COMPREHENSIVE at attribution, so the matched atom carries `harm_bearers` = the full
   principal set and prices branch 2 at factor 1.0 (§4C). **m0239 is NOT in the
   falsifiable core** (ruling (b)); its DISPOSITION is the IMPLIED-EFFECTS layer
   (`IMPLIED_EFFECTS_DESIGN.md`) as its first case. Under the §4B CLASS RULE (R4-B1
   fix), m0239 — a clause demoted to that layer by ruling — is EXCLUDED from the §7.3
   regression bound and tracked by the IMPLIED-EFFECTS layer instead (the exclusion is
   subject to the §4B LAPSE CONDITION, q.v., including its receiver-readiness OPEN
   gate and its MEASURE-time semantics: if the IMPLIED-EFFECTS layer is rejected,
   dropped, or never built, m0239 re-enters THIS bound — retroactively re-counted at
   the decision point where lapse is established when that is after CLOSE, R8-S-B).
   The exclusion is
   from the BOUND, not from the mechanism: S3b still prices m0239 corpus-wide like any
   other attributed clause (strict document-grounded attribution can only attribute
   {user} to its matched atom, so §5.3 predicts the same re-suppression S3 produced —
   a no_longer_predicted flip); that flip is recorded and reported but NOT counted
   against `max_regressions`, because its removal's document-side verdict was already
   adjudicated in S3 and bidirectionally confirmed, and re-adjudicating it adds no
   information.
   **m0239 — BOTH HORNS PRE-REGISTERED (R6-S-2).** The expected horn is the one above:
   the matched atom resolves {user} ⇒ branch 4, taint, re-suppression ⇒ a
   no_longer_predicted flip (recorded, reported, bound-excluded by the CLASS RULE).
   The ALTERNATE horn is pre-registered too, because it disappears from the bar: if
   the backfill returns `unclear` on m0239's matched atom, that atom prices branch 1,
   cap-EXEMPT at factor 1.0 with zero penalty; m0239's single credited match then
   carries the whole surviving mass, the clause prices at baseline, and — m0239 being
   `predicted` in the S2 baseline — restoration produces NO FLIP: nothing for the
   bound to count, and this plank's iteration set (m0275, m0466, m0018) never visits
   m0239. The no-flip horn is invisible to every flip-based control, so it carries a
   NAMED CHECK: if m0239 does NOT flip, its explain trail MUST show the resolved-{user}
   signature on its matched atom — the matched atom itself attributed {user} and
   branch-4-priced (factor d or taint-capped, its own credit penalized) — else FLAG
   the clause: a no-flip without that signature IS the branch-1 escape, and the flag
   routes to the §5.3 NAMED RESPONSE (golden re-examination of m0239's `unclear`
   verdict — never re-pricing). Soft detection exists either way: under the alternate
   horn the pre-registered MEASURE-time exempt-mass report shows m0239 at ~100% exempt
   share (single match).
   m0108 stays `unclear` and is NOT counted either way: its named seat-defect review is
   DONE (`cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`, 2026-08-04;
   see §8/D2) — it ruled the harm m0108 guards falls on the user's OWN ORGANISATION,
   not third parties, found the behaviour definition genuinely ambiguous on the
   user's-organisation case, and let the `unclear` accounting under the divergence rule
   STAND.

   **SCOPE OF THE CORE (S-5, R3).** The falsifiable core (m0275 + m0466 + m0018 — D4 is
   ruled, §4C) exercises finding (i) — taint inheritance onto patient-free SITUATION
   atoms — and the
   harm-bearer mechanism only in the situation-atom shape. No in-scope case tests finding
   (ii)'s protective-act recipient≠harm-bearer shape; that mechanism awaits the
   IMPLIED-EFFECTS layer (§4B). The shrinkage from the headline "beneficiary-aware" claim
   to this core is disclosed, not smuggled.

   **Restoration SIGNATURE (B-3 fix; S-1/S-2/S-7 fixes, R3; arms bound PER CLAUSE,
   R8-S-A) — 'still predicted' is NOT enough, and the signature is a CLAUSE-BOUND
   disjunction.** In the S2 baseline
   m0275/m0466 are ALREADY `predicted` (they only left during the reverted S3), so pricing
   them back above cut produces NO flip and flip-set adjudication never sees them; and I1
   manufactures a trivial pass (no attribution ⇒ bit-identical ⇒ still predicted ⇒
   "restored" with zero mechanism involved). The restoration claim is therefore checked by
   a PER-CLAUSE MECHANICAL SIGNATURE on the S3b snapshot's explain trail, run by the
   independent seat AFTER attribution is frozen. **ITERATION SET (S-2): the check iterates
   EXACTLY the clause ids named in this plank — m0275, m0466, and m0018 (D4 is ruled, so
   m0018 is in unconditionally; §4C) — NOTHING COMPUTED.** "Restored" is not derived from
   observed snapshot properties or flip sets (which this plank's own second sentence shows
   cannot contain the clauses).
   **SIGNATURE (S-1; arms bound PER CLAUSE, R8-S-A):** for each named clause id, the
   clause IS `predicted` in the S3b snapshot AND factor 1.0 AND THE ARM BOUND TO THAT
   CLAUSE (R4 s-1 / R6-E-7: the `predicted` conjunct — the signature reads the explain
   trail, and a below-cut clause's trail must not be able to license a PASS on its own;
   the signature is the conjunction of the mechanism AND the outcome). The binding is
   MECHANICAL, not descriptive appositive: each clause id may satisfy ONLY its bound
   arm, and a clause whose match satisfies ANY OTHER arm FAILS the plank —
   * **m0275 ⇒ arm (i) ONLY;**
   * **m0466 ⇒ arm (i) ONLY;**
   * **m0018 ⇒ arm (ii) ONLY.**
   Arm (i): `why = consistent` with non-empty `harm_bearers ∩ P` — resolved consistent
   attribution on the matched atom. Arm (ii): `why = generic`, branch 2 — the matched
   atom's attribution disambiguates its generic noun COMPREHENSIVE (`harm_bearers` =
   the full principal set; factor 1.0, cap-exempt), with the disambiguation verdict
   AND the license quote on file. **CONSEQUENCE OF THE BINDING (R8-S-A):** the former
   phrasing "ONE of these arms, keyed to the branch that produced the match" keyed the
   arm to the BRANCH, not the clause, and let a comprehensive-laundered m0275/m0466 —
   wrong verdict: the full principal set instead of {third_party}, surfacing via
   branch 2 at factor 1.0, no flip because the clause is `predicted` in the S2
   baseline — satisfy arm (ii)'s mechanical content and PASS; that path is now CLOSED:
   a branch-2 match on m0275/m0466 keys to arm (ii), which is NOT their bound arm —
   FAIL of the restoration plank. (Their bearer phrases "someone"/"another person" are
   not §1.3-step-4 generic triggers in the companion spec, so a comprehensive verdict
   there is procedurally out of bounds as well as signature-failing.) The binding
   catches the mirror case too: an m0018 attributed a narrower specific set
   intersecting P would match arm (i), not its bound arm, and FAILS here (§2.5's
   backfill re-check pins m0018's expectation independently). The arm is keyed to the
   CLAUSE first; the branch only identifies the mechanism by which the bound arm is
   satisfied. **BELT-AND-BRACES (R8-S-A):** the companion spec's §2.5 FROZEN-BACKFILL
   RE-CHECK now extends to m0275/m0466 with IMMUTABLE expected verdicts (resolved,
   `harm_bearers` exactly {third_party}, not comprehensive), so a laundering verdict
   is caught at BACKFILL time too — the validator's E_CONSISTENCY enforces set-shape
   only and cannot see it, and no other backfill-time check sees m0275/m0466's
   verdicts. This reading is the companion spec's §3.4 F_core reading (arms
   clause-bound); the two documents now agree. D4 is RULED (translation-time referent
   disambiguation, §4C), so arm (ii) is the only generic arm: the former patient-free
   arm (iii) is DEAD — the ruling rejected the patient-free convention — and the arm
   list is fixed with the ruling. The disjunction is PRE-REGISTERED before OPEN, not
   improvised at MEASURE. In every arm, "predicted but not
   attributed / not annotated by the named mechanism" (including "predicted because
   attribution was absent") is a FAIL of the restoration plank, not a PASS. This is what
   distinguishes "restored BY the mechanism" from "never touched."
   **m0108 EXPLORATORY SIGNATURE (S-7, R3):** m0108 is not counted either way, but its
   expected pricing signature under §5.3 is pre-registered as an exploratory observation —
   matched patient-free situation `harmful_instructions`, expected branch-1 (`unclear` for
   a third-party query: the matched atom is patient-free, and its gloss — "user or
   developer directions whose execution could cause harm" — names whose DIRECTIONS they
   are, not who is HARMED by execution, exactly the point the completed seat-defect
   review made about leg 1's paraphrase) at the E-1 cap-exempt price if any
   resolved-disjoint sibling fires taint — so a silent m0108 restoration or
   non-restoration teaches something rather than nothing.
2. **Keep the canonical removals.** m0276 and m0290 remain `no_longer_predicted` for
   harm-avoidance-to-third-parties. If either re-surfaces, REVERT regardless of all else.

   **PRE-OPEN LICENSABILITY GATE FOR THE CANONICAL CONTROLS (R6-E-2 fix, part B;
   coordinator ruling).** Before OPEN, verify PER CASE that each canonical control's
   harm-bearer attribution is LICENSABLE: the frozen attribution artifact must carry,
   for m0276 and for m0290, a record attributing `user` as harm-bearer whose
   `license_quote` is a byte-exact verbatim substring of the control's clause text
   under the companion spec's §1.4 mapping — including the speaker-aware first-person
   rule (§1.4 note (v)), which licenses m0290's example-dialogue bearer (m0276's
   bearer is licensable via its clause text's verbatim "the user" spans). If a
   control's attribution is NOT licensable (record absent, `unclear`, or quoteless),
   FLAG it — record it in the cycle record and resolve by ruling; the pre-registered
   remedy is a §1.4-table/brief amendment and a re-run of the affected rows — and do
   NOT silently proceed to OPEN. GROUND: without a licensed {user} attribution the
   control prices at branch 1 (baseline), re-surfaces, and trips this plank's
   unconditional REVERT at MEASURE — a FALSE REVERT, the cycle killed by a licensing
   gap, not a mechanism failure. The gate moves that check to pre-OPEN, where the fix
   is cheap. The controls' expectations ({user}, stay suppressed) are pinned here and
   do not move after OPEN.
3. **`max_regressions: 0`** under the same two-leg split-blind adjudication S3 used
   (leg 1 official + frontier verification leg blind to leg 1; divergence → `unclear`,
   never silently resolved; P3/`ADJUDICATION_LEGS.md` precedent). **BOUND POPULATION
   (R4-B1 fix):** the bound counts flips on every clause EXCEPT clauses demoted to the
   IMPLIED-EFFECTS layer by ruling — the §4B CLASS RULE (q.v.): such clauses are
   excluded from this bound and tracked by that layer instead. The exclusion carries
   §4B's LAPSE CONDITION (q.v. for the full state space — receiver-readiness OPEN
   gate, MEASURE-time semantics, R8-S-B): if the IMPLIED-EFFECTS layer is rejected,
   dropped, or never built, the demoted clause re-enters THIS bound — retroactively
   re-counted at the decision point where lapse is established when that is after
   CLOSE. Single current instance: m0239 (§4B, §7.1). A demoted clause's flip is
   still recorded and reported — the exclusion is from re-adjudication against a
   verdict S3 already settled, never from visibility.
4. **No census/panel/judge/gold consultation** informs the decision; flip adjudications
   only (S3 policy, restated).
5. **Expected-recovery gate (S-4/M-4 fix, R3) — a method, a denominator, and a threshold;
   the REVISION-3 claim "the figure is pre-registered here" was FALSE and is STRUCK.**
   What is pre-registered is the PROCEDURE, the DENOMINATOR, and the DECISION THRESHOLD;
   the figure itself is produced by the procedure and pinned before OPEN.
   * DENOMINATOR: the §8/D5 attribution population (clause-instance candidates), as
     enumerated by the count-first step (in progress —
     `ATTRIBUTION_POPULATION_ENUMERATION`); NOT the raw 155 census class (panel-derived,
     not the frame).
   * PROCEDURE (blind): over the D5-derived candidate set, a mechanical text/gloss scan for
     bearer-naming spans, then a panel-blind seat decision per candidate WITHOUT knowledge
     of any flip outcome, expected restoration, or panel label (whitelist fence, §5.1).
     Output: the count of candidates with a NAMEABLE harm-bearer in the principal
     vocabulary — the strict-attribution reach R.
   * THRESHOLD (R4-S1 fix — the floor is committed BLIND, before R is seen; the
     REVISION-4 ordering let the gate's binding quantity be chosen after seeing the
     estimate, which is discovery at (pre-)MEASURE, not pre-registration). The sequence
     is fixed and pinned:
     1. WITH THE D5 RULING, pin WHICH population band is R's denominator — the
        enumeration carries three totals (427 lower band (a)+(b-core) / 439 recommended
        (a)+(b-trim) / 746 upper band (a)+(b-wide), over the 368-instance firm floor;
        the recommended b-trim predicate is itself a judgement), so R's sampling frame
        is fixed at ruling time, not at measurement.
     2. COMMIT THE FLOOR F — a number or interval — BEFORE the blind procedure above is
        unblinded, from quantities ALREADY KNOWN, never from R: the backfill-
        affordability argument is on the table (ATTRIBUTION_POPULATION_ENUMERATION §5
        reads the population as LARGE — the firm floor alone, 368, already exceeds the
        264 chains S2's full-cycle four-seat backfill landed, and the recommended 439
        is 63% of S2's 692 candidates; the §5.2 ruling routes the backfill through a
        cheap seat precisely because scale makes per-frontier-item cost unaffordable),
        plus the falsifiable core's size (three named restorations — m0275, m0466, and
        m0018, unconditional now that D4 is ruled). Either F itself or a NAMED BLIND
        RULE for setting it — one that reads
        only those already-known quantities — is committed and pinned alongside the
        prediction at OPEN.
     3. ONLY THEN is the blind procedure unblinded and R produced and pinned.
     4. DECISION RULE: if R < F, the cycle RE-SCOPES or does NOT open (a hard gate,
        parallel to §7.2's automatic REVERT, not advice).
     A floor set or adjusted with knowledge of R is a review finding, not a ruling.
   * MEASURE check: the actual strict restorations are compared to R; a large shortfall is
     a finding (reach over-estimated), not silently absorbed.
   The REMAINDER of the class — cases like m0239 whose harm-bearer is implied, not named —
   is enumerated separately by the IMPLIED-EFFECTS layer's own count-first step
   (`IMPLIED_EFFECTS_DESIGN.md`), not here.
6. **Stratified controls on the LIVE mechanism (S-6 / prior m-4 / coordinator N3, R3).**
   N3's stratified-controls commitment must govern the live corpus-wide rule §5.3, not only
   the withdrawn A-structural. Before OPEN, pre-register a stratified golden review over a
   sample of AFFECTED clauses — strata: behaviour × section × attribution-verdict
   (consistent / mismatched / comprehensive-generic / unclear) — written before any
   dossier is read
   (PORTFOLIO_REVIEW F11's stratified-sampling requirement; the S3 record's flip-budget
   stratification shows the pattern). Four-to-five named clauses is thin for a rule that
   re-prices every attributed clause for every declared query. The `unclear` stratum here
   is the SAMPLE leg of the R4-E3 monitoring; the corpus-wide leg is §5.3's
   pre-registered MEASURE-time exempt-mass report.

---

## 8. Designer rulings / seat-defect review (D1 RULED 2026-08-05; D3 RULED 2026-08-05;
D4 RULED 2026-08-05; D5 RULED 2026-08-05; D2 OPEN — not resolved here)

* **D1 — RULED (coordinator 2026-08-05, option (a)).** Attribution delivery is the
  ANNOTATION-SIDE BACKFILL; the ruling's constraints (mechanical task design sized for
  a capable-but-cheap seat, the pre-registered cheap-vs-frontier parity gate,
  R-informed scope) are recorded in §5.2, and the task's substance lives in the
  companion spec `S3B_ATTRIBUTION_TASK_DESIGN.md` (being written separately). The
  index-side seat (former option (b)) is closed.
* **D2 — the m0108 scope question** (carried verbatim from S3, `ADJUDICATION_LEGS.md`):
  is "harm to the user's own organisation's accounts" harm to "those outside the
  conversation"? This is a question about the behaviour DEFINITION, not the pricing
  mechanism. Its named seat-defect review is DONE
  (`cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`, 2026-08-04): the
  harm m0108 guards falls on the user's OWN ORGANISATION ("our team accounts"), not on
  third parties; leg 2's direction is sustained on the representation reading; the
  definition is found GENUINELY AMBIGUOUS ("those outside the conversation"
  under-determines the user's-organisation case); and the review's recommended
  clarification is referred to a future query-side change cycle. S3b still does NOT
  resolve it: the `unclear` accounting under the divergence rule STANDS, and boundary
  cases of this shape remain knife-edge until the clarification is adopted.
* **D3 — RULED (coordinator 2026-08-05): UNIFORM — no distinct example-kind rule.**
  The concern was speculative: it arose because the finding-(i) regressions motivating
  the redesign (m0275/m0466/m0108) were all example-kind, prompting the precautionary
  question of example-specific treatment. The enumeration found NO instance of the
  problem (`D3_EXAMPLE_CLAUSE_ENUMERATION.md`: 183/183 example clauses handled by uniform
  attribution, 0 wrong-result, 0 undefined). S3b uses the uniform rule; the distinct-rule
  idea is registered as a LATENT FIX (`LATENT_FIX_REGISTRY.md` LF-1), not implemented,
  with a named trigger. Golden-review the attribution-load-bearing examples
  (m0176/m0300/m0467) as seat-quality targets, not rule targets — IMPLEMENTATION SITE:
  the companion spec's §2.2 boundary set carries all three as always-included rows
  (R6-E-5), so the parity validation's golden review reaches them by construction, not
  only when quota sampling happens to. **BUILD REQUIREMENT:**
  the LF-1 DETECTION tripwire (example-population pin + load-bearing pricing pin +
  adjudication shape-flag, all failing LOUDLY and referencing LF-1) ships WITH the S3b
  build's test set, so a future latent case cannot pass silently.
* **D4 — RULED (coordinator 2026-08-05): translation-time generic-noun referent
  DISAMBIGUATION.** Generic nouns ("people", "individuals") carry multiple meanings and
  are disambiguated at TRANSLATION/ATTRIBUTION time — NOT via a pricing-time generic
  flag. The attribution fixes each occurrence's referent: a COMPREHENSIVE generic
  (m0018's "people" = the beneficiaries of a universal provision) is attributed
  `harm_bearers` = the FULL principal set — §5.3 branch 2, redefined as the
  comprehensive-generic case: factor 1.0, cap-exempt, surfaces for any matching query;
  a SPECIFIC generic (m0248's "individuals" = the targets of a harm) is attributed the
  specific party and prices by branches 3/4 — factor d for a helpfulness query, golden
  derivation case #5 preserved. The disambiguation is per-occurrence, never a global
  "generic ⇒ factor 1.0" rule; that is how the ruling resolves the m0248 golden
  collision (§2.1). Both REVISION-5 horns are disposed: the pricing-time flag is
  SUPERSEDED, the patient-free convention REJECTED (§4C). The disambiguation sub-task
  and the m0018/m0248 golden verification cases live in
  `S3B_ATTRIBUTION_TASK_DESIGN.md` (§1.3 step 4, §2.5).
* **D5 — attribution population (N2). RULED (Matt Stults, 2026-08-05): the b-trim band,
  439 instances** — predicate A (chain length ≥ 2) plus patient-free SITUATION atoms
  matching the CORE+EXT keyword stems minus the four audited FP_NAMES
  (`ATTRIBUTION_POPULATION_ENUMERATION.md` §2.3). This pins BOTH the §7.5 reach
  denominator — fixed at ruling time, before R is computed, per the §7.5 sequence — and
  the §5.2 backfill scope. Evidence: `D5_WORKED_EXAMPLES.md`, a corpus-wide measurement
  over every predicted clause (panel-blind) with the 155-case census as an
  attention-only cross-check.
  **REJECTED BY NAME:**
  * **368 (firm floor, chain-only)** — REJECTED. Four of the five canonical clauses are
    credited through a patient-free SITUATION atom (m0276 `imminent_bodily_harm`, m0275
    `expressed_harmful_intent`, m0466 `user_requests_harmful_advice`, m0108
    `harmful_instructions`; only m0239 runs through a chained act). Excluded atoms get no
    record, so §5.3 branch 1 gives them factor 1.0 and cap-exemption — m0276 would NOT be
    suppressed (a §7.2 automatic REVERT) and m0275/m0466 would restore without the
    `consistent` signature §7.1 binds them to (restoration plank FAIL). It fails two
    pre-registered checks in opposite directions: inert, not conservative. Corpus-wide it
    reaches 67/155 census cases vs 79 for b-trim, and just 17/73 predicted harm clauses
    vs 40.
  * **746 (b-wide, no keyword filter)** — REJECTED. Its entire marginal reach over b-trim,
    on both bases (+3 census cases, +6 caution clauses), comes from exactly two atom
    names: `positive_user_intent` (m0164/m0170/m0171/m0174 — one of the four audited
    FP_NAMES; its keyword hit is on a *negation*, "constructive rather than **harmful**
    purpose") and `incomplete_user_context` (m0374/m0428 — a model knowledge-state, not a
    party's harm or benefit). Both would be ruled `unclear` under the attribution
    procedure's own step 1 and price at factor 1.0, changing nothing. ~307 extra seat
    items and a larger golden-review sample for zero effective reach; and what "removing
    the keyword judgment" removes is the audit that caught `positive_user_intent`.
  * **427 (b-core, CORE stems only)** — not chosen, but on the measurement it is TIED with
    b-trim (79/155 census; identical on all three behaviours). No canonical case depends
    on an EXT stem. b-trim was preferred because its EXT additions came from a disclosed
    gloss audit and its six audited false positives are forced into the golden-review
    boundary set by §2.2 — the judgment is checked rather than hidden. A future reviewer
    who prefers less judgment surface for identical measured reach has a defensible case;
    this is a preference, not a finding.
  **SCOPE PIN.** The population remains SITUATIONS-ONLY among patient-free atoms. That
  restriction is now recognised as the dominant constraint on coverage (66 of the 80
  resolved matched atoms in the 76 unreachable census cases are ACTS) and is ruled
  separately — see `D5B_ACT_ATOMS.md`. It is NOT settled by this ruling.
  **DISCLOSED CONSEQUENCE.** At this band the mechanism reaches 79 of the 155
  `fp_promiscuous_atom` cases (51%), i.e. ≈27% of the 294-case census — not the 53% the
  class size suggests. Expected recovery must be argued against 27%.
  Whatever the population, every entry is licensed the same way (verbatim quote, golden
  review) before pricing reads it.

---

## 9. What this document deliberately does NOT do

* It does not implement or patch `patient.py`. Nothing ships with it.
* It does not tune `d` or any weight.
* It does not open a cycle. OPEN happens only after a clean-context adversarial re-review
  returns non-blocking and the remaining open rulings (D2, D5; D1 is ruled, §5.2, and
  D3 and D4 are ruled, §8) have rulings. D3 was RULED 2026-08-05 (UNIFORM — no distinct
  example-kind rule; latent fix LF-1) and its enumeration is COMPLETE
  (`D3_EXAMPLE_CLAUSE_ENUMERATION.md`); the REVISION-6 text calling D3 OPEN was stale
  and was reconciled to RULED in REVISION 7 (R6-E-1). **AND RECEIVER READINESS (R8-S-B):
  OPEN additionally requires the IMPLIED-EFFECTS layer's receiver readiness — the
  design has PASSED review AND its tracker has ACCEPTED m0239 as a tracked entry (§4B
  LAPSE CONDITION, q.v.). The exclusion is pre-registered AT OPEN, so its "holds only
  while" preamble must be true AT OPEN (and is re-checked at MEASURE — the exclusion
  holds at MEASURE only if readiness still holds; otherwise m0239's flip is counted).
  A coordinator must not open S3b on the D2/D5 rulings alone while the receiver is
  still DRAFT-unreviewed.**
* It does not restore m0239 (ruling (b), §4B): strict document-grounded attribution
  cannot license its third-party beneficiary, so m0239 is the first case of the
  IMPLIED-EFFECTS layer, not of S3b — and under the §4B CLASS RULE (R4-B1 fix) its
  flip is excluded from the §7.3 regression bound and tracked by that layer instead
  (subject to §4B's LAPSE CONDITION).
* It does not design or build the implied-effects layer itself — that is
  `IMPLIED_EFFECTS_DESIGN.md`, a sibling effort with its own review.
* It does not resolve m0108, m0355-family threshold cases, or any census question; those
  stay deferred to their named venues (m0108's seat-defect review is DONE —
  `cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md` ruled the harm falls
  on the user's own organisation and flagged a genuine definition ambiguity; the
  recommended clarification awaits a query-side change cycle — and the S8 checkpoint).

— REVISION 9; awaiting adversarial re-review.
