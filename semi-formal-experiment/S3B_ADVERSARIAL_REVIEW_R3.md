# S3B_REDESIGN.md (REVISION 3) — clean-context adversarial RE-review

Date: 2026-08-04. Reviewer: clean-context adversarial design reviewer (re-review seat;
no prior involvement). This review is of REVISION 3 only. Standard: findings are
document-grounded or computed against the live record — every mechanism claim below was
checked against `cycles/patient-pricing-2026-08-04/` (decision.json, ADJUDICATION_LEGS.md,
DISCOUNT_DERIVATION.md, flip_verdicts.json, and the flip dossiers for m0275, m0276, m0239,
m0466, m0018, m0290, m0108 — `explain_b.patient_pricing` opened and compared), plus
`briefs/backfill_author.md`, `HANDOFF.md`, `CYCLE5_DESIGN.md`, and
`IMPLIED_EFFECTS_DESIGN.md` (handoff coherence only, per the dispatch).

## Verdict: REVISE

Two blocking findings — both NEW, both introduced by the revision's own fixes. The three
prior blockers are genuinely addressed (verified, not taken on faith — see "Verification
of claimed fixes"), the dossier-level diagnosis remains exact, and ruling (b) is
scientifically honest. But fixing B-1's atom-level totality created an undefined
clause-level composition on exactly the mixed clauses the mechanism will meet, and the
B-3 restoration signature — written for the m0275/m0466 shape — cannot be passed by
m0018 under ANY horn of the D4 ruling that §7.1 conditions it on. One of the three core
restorations is pre-registered to fail its own check. Additionally, four of the six prior
majors (M-1, M-2, M-3, M-4) were not carried into REVISION 3 and two of them are now
load-bearing for the new machinery. None of this indicts the mechanism — attribution
DOES separate m0275 from m0276, verified against the dossiers — but the spec is not yet
buildable and the falsification bar is not yet internally consistent. Do not OPEN.

Finding counts: Engineering — 1 blocking, 4 major, 2 minor. Science — 1 blocking,
3 major, 4 minor.

---

## Verification of claimed fixes (first duty of a re-review)

**B-1 (§5.3 totality / vacuous taint) — FIXED at the atom level, broken at the clause
level.** The mechanical definitions are present and genuinely mechanical (pure reads of
the attribution artifact: "harm-bearing iff record with non-empty `harm_bearers`",
"resolved iff non-empty and not `unclear`" — §5.3). Empty/`unclear` attribution lands in
branch 1 with factor 1.0 and quantifier exclusion; `unclear` is correctly treated as a
first-class foreseeable verdict (backfill_author.md: "never force a call"). Taint has
existential import and correctly re-expresses DISCOUNT_DERIVATION §0's precondition
("≥1 patient-bearing chain, none consistent" — verified verbatim in the derivation);
branch precedence is stated. BUT the fix created a new composition gap: see BLOCKING E-1.

**B-2 (m0239) — FIXED, and ruling (b) is honest.** Verified against the m0239 dossier:
the matched atom is the PATIENT-BEARING act `should_deescalate_extremist_involvement`
(chain `[model, user]`, `why: mismatched`, factor 0.1), and neither the clause text nor
any of the three glosses names a third party ("the user shows signs of being susceptible
to extremist recruitment…", "reduces the user's movement toward participation in
extremist activity", "explains that extremist ideologies are harmful and broadly
discredited"). §5.1's document-grounded regime (verbatim `license_quote`, clause text +
gloss + golden convention only) cannot license a third-party bearer here, and
backfill_author.md rule 3 FORBIDS the needed inference verbatim ("Do not infer an
affected party from the subject matter: a clause forbidding an act does not thereby name
whoever that act would harm"; m0236 precedent). The demotion is stated in §4B, restated
in §7.1 (core = m0275 + m0466 + m0018-conditional-on-D4), and in §9. The handoff to
`IMPLIED_EFFECTS_DESIGN.md` is coherent: m0239 is named there as the first case (§1),
with count-first sizing (§5) and the explicit coupling "S3b sizes the strict-attribution
reach, this sizes the implied remainder." The scope reduction is disclosed, grounded, and
routed — not smuggled (but see S-5 for its cost).

**B-3 (vacuous restoration) — FIXED in its core insight, with a new contradiction and a
residual ambiguity.** The I1-manufactured trivial pass is closed: "Predicted but not
attributed (including 'predicted because attribution was absent') is a FAIL of the
restoration plank, not a PASS" (§7.1). The signature (non-empty `harm_bearers ∩ P`,
factor 1.0, `why = consistent`) is mechanical given the explain trail, and independent
post-freeze checking is pre-registered. BUT the signature as written cannot be satisfied
by m0018 (BLOCKING S-1), and the iteration set "each in-scope restored clause" admits a
vacuous computed-set reading (MAJOR S-2).

**Prior majors.** M-5 (fence residual paths) — FIXED: §5.1's RESIDUAL FENCE PATHS closes
all three named holes (S3b's own prediction/decision artifacts + restore-signature
outputs; rechain-repair channel; token scan demoted to backstop). M-6 (§7.1 record) —
FIXED: m0018 is D4-conditional in §7.1, and the counts match decision.json
(`confirmed_regressions = [m0239, m0275, m0466, m0018]`, contested m0108). M-1, M-2,
M-3, M-4 — NOT addressed in REVISION 3 (verified by grep: no value-space pin, no keying
statement, zero mentions of m0248 or derivation cases #5/#6, no figure/method/threshold
in §7.5). All four are carried forward below, two at higher severity because the new
machinery now rests on them.

**Prior minors.** m-1 (1/155 arithmetic) — fixed: §7.5 now matches CYCLE5_DESIGN §0
("this cycle moves exactly 1 of the 155 clauses in its nominal class", "a 1/155 fix"),
and the m0290 substantive point is preserved in §1. m-2, m-3, m-4, m-5 — unaddressed;
carried below.

---

# Engineering excellence

## BLOCKING

### E-1 — §5.3 is total per-atom but UNDEFINED at the clause level: the taint cap's composition with branch-1/branch-2 atoms on mixed clauses has two contradictory readings

The B-1 fix makes every atom-level input land in exactly one branch. It does not make
the RULE total, because pricing is not only per-atom: clause taint + the carried-forward
cap (§2.2: "the surviving atom mass is ONE discounted credit (`d · max(base
credits)/atom_norm`)") is clause-level, and §5.3's only statement of the interaction is
"Under taint the existing cap applies unchanged."

Construct the case — it is foreseeable by the design's OWN stipulations:
* Clause C has a matched patient-free situation atom `a` whose attribution is `unclear`
  (branch 1: factor 1.0, excluded from the taint quantifier) and one patient-bearing
  act atom `b` resolved+specific with `harm_bearers = {user}`.
* Query declares P = {third_party}.
* Taint check: the resolved+specific harm-bearing atoms are {`b`}; `b ∩ P = ∅`; all
  resolved+specific atoms disjoint ⇒ the clause IS tainted (existential import
  satisfied).
* Then what is the price of the match through `a`?

Reading A — the cap replaces the atom channel, "unchanged" as in S3 (DISCOUNT_DERIVATION
§0 states of the S3 rule: "Under taint, **patient-free atoms on the clause are discounted
too**"; decision.json fix_description: "tainted atom channel = d * max(base
credits)/atom_norm"): the channel becomes `d · max(base)/atom_norm`, and `a`'s credit is
crushed to the discount despite branch 1. This CONTRADICTS branch 1's own prose — "an
atom the attribution does not resolve prices exactly as it does today, never as a
discount" — and contradicts the I1 rationale branch 1 invokes.
Reading B — branch-1/branch-2 credits are exempt from the cap and survive at full value
alongside the one discounted credit: that is NOT "the existing cap unchanged" but new cap
semantics the document never states, and "the surviving atom mass is ONE discounted
credit" is then false as a description of surviving mass.

The readings produce different suppression/surface outcomes (Reading A: channel
`0.1 · max/norm`; Reading B: full `a` credit + `0.1 · b` credit). This is the "clause
with a mix" case, and it is not exotic: `unclear` is declared a first-class legal verdict
that golden review must cover (§5.3), partial resolution of a clause's atoms is the
normal state of any large attribution pass (D5 concedes the population may exceed S2's
692-candidate effort), and the contested m0108 is exactly this shape (matched
patient-free situation `harmful_instructions`, gloss "user or developer directions whose
execution could cause harm", `why: clause_taint` in its dossier — one `unclear` verdict
on the situation atom plus any resolved-disjoint sibling lands the case). The same gap
applies to branch-2 (generic) atoms coexisting with a taint-firing resolved-disjoint atom.

B-1 demanded "every foreseeable input lands in exactly one branch with no undefined
cases." Atom-level: done. Clause-level: the fix created the gap it was meant to close.
**Fix:** state, as a fifth rule sentence, whether unresolved/generic atom credits are
inside or outside the capped mass when the clause is tainted by resolved siblings — and
whichever horn is chosen, reconcile it with branch 1's "never as a discount" promise and
re-state the cap's surviving-mass formula for the mixed case. Pre-register a pinned test
on a constructed mixed clause (one `unclear` situation atom + one resolved-disjoint act
atom + P disjoint) so the reading is code, not commentary.

## MAJOR

### E-2 — attribution keying granularity is STILL unspecified, and the design's own §5 preservation claim is false under the other reading (prior M-2, now load-bearing)

§5.3 reads `harm_bearers(a)` for "a credited match through atom `a`", and §5.1 never
states whether records are keyed per clause-instance (clause_id + span) or per atom
NAME. The dossiers prove this is not hypothetical: `user_requests_harmful_advice` is the
matched atom in BOTH m0466 (anthrax — "mailing **someone** anthrax"; must be attributed
third-party to restore) and m0290 (eating-disorder self-starvation — flip_verdicts.json:
"concern user self-harm"; must stay user-attributed to keep the §7.2 control suppressed).
Under name-keying, one record serves both clauses; whichever bearer wins, the other clause
is mispriced — and the error lands on m0290, one of the two automatic-REVERT controls.
The §5 preservation claim ("m0276 and m0290 stay suppressed because … their harm-bearing
atoms attribute the USER as harm-bearer") is true only under instance keying, which the
document never pins. The prior review asked for exactly this sentence plus a validator
check; it is still absent (verified by grep for key/span/clause_id/instance in
S3B_REDESIGN.md).
**Fix:** state in §5.1 that attribution is keyed per clause-instance (clause_id +
span_id), validator-checked like S2's license quotes, and make the §5 preservation claim
explicitly conditional on it.

### E-3 — the `harm_bearers` value space and the text→principal mapping are STILL unpinned, and two mechanical checks now depend on them (prior M-1)

§5.3's branches and the §7.1 restoration signature both compute `harm_bearers(a) ∩ P`,
where P lives in the declared-principal vocabulary ({third_party}, {user, developer}, …).
§5.1 never pins `harm_bearers` to a vocabulary or gives the mapping from clause noun
phrases ("another person", "someone", "the user") to principals. If the attribution
records free text, every intersection in the mechanism is syntactic and can silently miss
— the entire restoration turns on m0275's "harm **another person**" (gloss of
`expressed_harmful_intent`, verified in dossier) landing as `third_party` and m0466's
"mailing **someone** anthrax" (clause text) landing the same. The project already owns a
principal set (backfill_author.md: "members drawn from: third_party, developer, operator,
system, model, root, user"). Without the pin, a correct attribution can fail the
restoration signature, and the "mechanical definitions" of §5.3 are mechanical only after
an unstated normalization.
**Fix:** pin `harm_bearers` to the existing principal vocabulary, put the noun-phrase→
principal mapping rule in the attribution brief, validator-check it, and state that the
§7.1 intersection is computed on that vocabulary.

### E-4 — the D5 population predicate ("patient-free harm-describing atoms") is a judgement that directly sets prices, and it has no operational definition, no seat, and no fence (prior m-2, raised)

§5.3 branch 1 prices an atom with NO attribution record at factor 1.0, quantifier-
excluded; a record can move the same atom to branch 4 (factor d). Record-presence is
therefore price-moving, and record-presence is decided by the D5 population predicate:
"patient-bearing AND patient-free harm-describing atoms" (§8-D5). "Patient-bearing" is
mechanical (length-≥2 chains); "harm-describing" is JUDGEMENT with no operational
definition, no named seat, and no fence statement — yet D5's enumeration determines,
clause by clause, which atoms CAN be suppressed at all. Mis-enumeration in the dangerous
direction (a harm-describing atom left out) silently leaves a wrong-bearer clause
un-discounted; the two named controls catch only m0276/m0290 themselves. §5.3's claim
that its predicates are "pure reads of [the attribution artifact]" inherits this hole:
the read is pure, but the artifact's DOMAIN is judgement-laden and unfenced.
**Fix:** give "harm-describing" an operational definition (e.g., gloss/kind-based
candidate generation + a panel-blind seat decision, recorded with license quotes), name
the seat, fence it like the attribution itself, and pre-register golden review of the
boundary cases (atoms admitted and atoms refused), not just the verdicts inside.

### E-5 — the blindness fence is a DENYLIST over named artifacts; the repo's own mandated reading carries the answer key and is not excluded

§5.1's fence names what the attribution seat must NOT read: S3B_REDESIGN.md, the S3 cycle
directory, the census, S3b's own prediction/decision artifacts, the restore-signature
outputs, the rechain channel. This is a denylist, and it misses the repo-level documents
that carry the key. `HANDOFF.md` — which AGENTS.md makes mandated reading #1 for every
agent in this repo — names all six load-bearing clauses WITH their required outcomes:
"m0275 'I want to shoot someone', m0466 anthrax…" (must not be tainted), "De-escalating
the user's radicalization protects third parties (m0239); … (m0018)" (the recipient-vs-
bearer defect), and "What worked and must be preserved … m0276 self-harm, m0290
eating-disorder". An attributor dispatched under this repo's standard reading order sees
the answer key before seeing a single clause. The design correctly demoted the token scan
to a backstop (M-5 fix), but then left the primary fence as "the brief is standalone" —
an intent, not a mechanism. S2 already owns the mechanism: backfill_author.md's
"What you see, and all you see" WHITELIST (row + grammar.py + annotate_prompt.md "and
nothing else").
**Fix:** state that the attribution seat's inputs are whitelisted exactly as S2's were
(brief + worksheet + notation owners, nothing else), that the seat is exempt from the
repo's standard context-loading for the duration of the pass, and that the denylist is
the backstop, not the fence.

## MINOR

### E-6 — the build seam is unstated: pricing_version bump, snapshot/dossier dispatch branch, and the explain-schema extension the signature needs

S3 shipped pricing_version 2.0 in snapshot config identity, a 2.0 branch in dossier
dispatch, and `patient_pricing` in the explain trail (decision.json fix_description;
dossiers' `explain_b.patient_pricing`). S3b needs all three again — a new version value,
a new dispatch branch, and (new) an explain record that carries the attributed
`harm_bearers`, P, and their intersection, without which the §7.1 signature has nothing
mechanical to read. §2 says the "derivation pattern" and "opt-in, bit-identity
invariants" carry forward but never names the seam mechanics. Implementable by analogy,
but a design that pre-registers a mechanical check on the explain trail should state that
the trail carries the fields the check reads.

### E-7 — §2.1 misattributes the re-derivation remedy

"the remedy is the derivation's own §1.4/Q6" — §1.4/Q6 is CYCLE5_DESIGN's, not
DISCOUNT_DERIVATION.md's (OPEN_RECOMPUTATION.md: "The design's own §1.4/§5-Q6 condition
fires"; DISCOUNT_DERIVATION.md has sections §0–§4 and no Q6). Citation only; the remedy
itself is correctly stated.

---

# Science

## BLOCKING

### S-1 — the restoration signature contradicts §7.1 for m0018: under EVERY horn of D4, a correctly-working mechanism FAILS its own pre-registered check

§7.1 pre-registers: "m0018 returns for helpfulness CONDITIONAL on the D4 generic-noun
ruling." The B-3 signature requires, for each in-scope restored clause, "non-empty
`harm_bearers ∩ P`, factor 1.0, and `why = consistent` — not `clause_taint`, not
branch-1 absent/unresolved." Now take D4's horns (§8: "Attribute `generic` and keep the
patient (§4C), or rule generic-noun clauses patient-free?"):

* **Flag horn.** m0018's matched atom `should_provide_trustworthy_safety_information`
  (chain `[model, third_party]`, dossier: `why: mismatched` against P = {user,
  developer}) is resolved and flagged `generic` (§4C: "people" comprehends all
  principals). It prices through BRANCH 2: factor 1.0, `why = generic` — not
  `consistent`. And its bearer does not intersect P in the first place: the generic flag
  exists precisely because the bearer ("people") is NOT a principal-vocabulary member
  whose intersection with {user, developer} is non-empty. The signature's first conjunct
  is false by construction. FAIL.
* **Patient-free horn.** Generic-noun clauses are annotated patient-free; the atom
  carries no chain-patient. Either it still gets an attribution record (then it is
  generic/branch-2 again — FAIL as above) or it gets no record (branch 1: `why =
  absent/unresolved` — which the signature EXPLICITLY lists as FAIL: "'Predicted but not
  attributed' … is a FAIL of the restoration plank"). Under this horn m0018's restoration
  is produced by the D4 ANNOTATION ruling, not by the attribution mechanism — and the
  signature, correctly suspicious of branch 1, fails it for exactly that reason. FAIL.

So one of the three named core restorations can only fail the check that exists to
certify it. At MEASURE this forces a choice between two corruptions: mark the plank
failed although the mechanism did precisely what §4C designed, or improvise an acceptance
condition for `why = generic` after seeing the outcome — the "silently loosening at build
time" disease this review process exists to catch. The signature was written for the
m0275/m0466 shape (consistent attribution on a situation atom) and never reconciled with
the §7.1 scope it serves.
**Fix:** restate the signature as a branch-keyed DISJUNCTION — for each NAMED clause id
(m0275, m0466, and m0018 if D4 is ruled): factor 1.0 AND (`why = consistent` with
non-empty `harm_bearers ∩ P`, OR `why = generic` with the atom's `generic` flag set and
a license quote on file, OR — if D4 rules patient-free — an explicit D4-ruling arm that
names the annotation change as the restoration mechanism and checks it instead). State
which arms exist once D4 is ruled; pre-register the disjunction before OPEN, not at
MEASURE.

## MAJOR

### S-2 — the signature's iteration set admits the very vacuity B-3 was meant to kill

"for each in-scope restored clause, the matched atom's pricing explanation MUST show…" —
"restored" is not defined as an input to the check. If an implementer computes the set
("clauses that were restored" = clauses satisfying some observed property in the S3b
snapshot, or — worse — newly_predicted flips, which this set cannot contain by §7.1's own
second sentence: "pricing them back above cut produces NO flip"), the check iterates an
empty or self-selecting set and passes vacuously. The named list (m0275, m0466, +m0018
per D4) exists two lines above in the same plank; the check must iterate THAT list.
**Fix:** one sentence — "the check iterates the clause ids named in plank 1, nothing
computed."

### S-3 — d = 0.10 is carried "UNCHANGED" but its licensing derivation is never re-argued under the new rule, and the generic flag INVERTS golden judgment #5 as written (prior M-3)

§2.1 carries d = 0.10 forward as review-stable "UNCHANGED … NOT a tuning target," with
blind re-derivation as the remedy "if S3b's mechanism change breaks the d-plateau." But
the derivation that LICENSED 0.10 (DISCOUNT_DERIVATION.md §1–§4) priced its eight golden
cases under CHAIN-based taint; S3b re-prices them under attribution semantics, and the
document never re-argues a single case. The collision is concrete: derivation case #5
(m0248, "abuse, harassment, or negativity toward **individuals**", chain third_party,
hypothetical P = {user}) is golden judgment (b) — factor d, and the clause "should not
outscore the user-chained material"; the derivation's own reason is "the act-noun
**generalizes** past the recorded patient … nothing in the text excludes the user." That
is exactly §4C's generic test — §4C defines generic as "comprehends all principals", and
"individuals" comprehends the user. Under §5.3 branch 2, a consistent attributor flags
m0248's atom generic ⇒ factor 1.0 ⇒ the clause OUTSCORES user-chained material: golden
judgment #5 inverted by the design's own definition. The design contains zero mentions of
m0248 or derivation cases #5/#6 (verified by grep). §2.1's remedy trigger ("if the
mechanism change breaks the d-plateau") is not operational here: the plateau was defined
over the S3 mechanism's flip sets, and under S3b case #5's factor depends on an
attribution judgement that does not exist until after D5/D1 — so "breaks" cannot be
evaluated without first re-adjudicating the golden cases under attribution semantics.
**Fix:** before OPEN, re-argue derivation cases #1–#8 under the attribution rule (blind,
document-side — the same seat pattern), and EITHER give a mechanical generic criterion
that separates m0018's "people" from m0248's "individuals" and pre-register it as
golden-testable, OR concede that §5.3 re-prices derivation cases and pre-register blind
re-derivation of d under the amended rule as the OPEN remedy — with the re-argued golden
table, not an inherited constant, as the licensing basis.

### S-4 — §7.5 STILL pre-registers no figure, no procedure, no denominator, and no trigger — while now asserting "The figure is pre-registered here" (prior M-4)

§7.5: "BEFORE OPEN, estimate — mechanically and blind to flip outcomes — how much of the
nominal 155-case `fp_promiscuous_atom` class STRICT document-grounded harm-bearer
attribution actually reaches … If the estimated STRICT reach is likewise small, that is
grounds to RE-SCOPE … The figure is pre-registered here and the MEASURE result is checked
against it." There is no figure anywhere in the document, no named blind procedure, no
denominator (155 census class? the D5 population? affected clauses?), and no threshold —
"likewise small" is not a trigger, contrast §7.2's hard automatic REVERT. The sentence
"The figure is pre-registered here" is false as written: what is pre-registered is the
OBLIGATION to estimate, which is precisely what the prior review condemned ("A
MEASURE-time comparison against nothing is still discovering at MEASURE"). The only
numbers present ("~1/155", "m0275/m0466 (+ m0018 per D4)") are historical S3 facts, not
an S3b estimate produced by a blind procedure. This also entangles §7.5 with D5 (the
enumeration §7.5 needs as its sampling frame is itself an open question — §8).
**Fix:** tie §7.5 to D5's enumeration as its frame, name the blind procedure (e.g.,
mechanical text/gloss scan for bearer-naming spans over a D5-derived sample, judged by a
fenced seat without flip knowledge), pre-register the number or interval and the
threshold under which the cycle re-scopes or does not open — or strike the claim that a
figure is pre-registered.

## MINOR

### S-5 — ruling (b) is honest, but the falsifiable core no longer contains a single protective-act recipient≠harm-bearer case, and the framing should say so

Finding (ii) of the S3 cycle — RECIPIENT ≠ HARM-BEARER on protective acts — had exactly
one confirmed case (m0239) plus the generic-noun variant (m0018). Ruling (b) demotes
m0239 and D4-conditions m0018, so the falsifiable core (m0275 + m0466) exercises finding
(i) — taint inheritance — and the harm-bearer mechanism only in the situation-atom shape.
No in-scope case tests "protective act UPON the user FOR others' benefit" — the defect
that gave the cycle its headline and this design its name ("beneficiary-aware"). The
shrinkage IS disclosed (§4B, §7.1, §7.5, §9) and scientifically defensible (the
alternative was a core prediction §5.1 cannot license); but §0's "fixes the PROVENANCE
defect that reverted S3" reads as the full claim. State plainly in §0/§7.1 which sub-
defect the core tests and that 4B-mechanism awaits the IMPLIED-EFFECTS layer.

### S-6 — stratified controls were never re-attached to the live corpus-wide rule (prior m-4 / coordinator N3)

N3's stratified-controls commitment governs only the WITHDRAWN A-structural rule ("if any
version is ever floated standalone"). The live rule — §5.3, which re-prices every
attributed clause for every declared query — keeps only the named restoration clauses
plus the two canonical controls. A corpus-wide mechanism change checked on four-to-five
named clauses is thin; the S2 golden-review pattern over a stratified sample of AFFECTED
clauses (behaviour × section × attribution-verdict strata, written before any dossier is
read) is the project's own precedent (prediction.json's FLIP BUDGET stratification shows
the pattern in the S3 record).

### S-7 — m0108's S3b pricing is left UNDEFINED in a foreseeable state, and no exploratory signature is pre-registered (prior m-5)

§7.1 keeps m0108 "NOT counted either way" — defensible. But under E-1's gap, m0108's
price under S3b is literally undefined for a foreseeable attribution state: its matched
atom is the patient-free situation `harmful_instructions` (gloss "user or developer
directions whose execution could cause harm" — a plausible `unclear`, since the gloss
names user AND developer bearers for a third-party query), and any resolved-disjoint
sibling fires taint into the undefined cap composition. Pre-register m0108's expected
pricing signature as an exploratory observation (which branch, which `why`) so its
silence or surprise teaches something; and resolving E-1 resolves this.

### S-8 — §5.3 branch 2 hardcodes one horn of open D4 without stating the dependence (prior m-3)

Branch 2 ("Generic: `a` is resolved and flagged `generic`") reads as settled mechanism
while D4 (flag vs patient-free convention) is explicitly open in §8. Under the patient-
free horn branch 2 is dead code and m0018's restoration moves to the annotation layer
(see S-1). State the rule's dependence on D4's outcome in §5.3 itself.

---

## What holds (verified, briefly — credit where due)

* **The dossier diagnosis remains exact.** m0275: matched patient-free situation
  `expressed_harmful_intent` (gloss "the user expresses an intention to harm another
  person"), sole patient-bearing sibling `should_provide_supportive_response` chain
  `[model, user]`, `clause_tainted: true`, factor 0.1 `why: clause_taint`, scores
  0.35147 → 0.13088 vs cut 0.23651. m0466: matched patient-free `user_requests_harmful_advice`,
  sibling `should_refuse_prohibited_help` `[model, user]`, same shape. m0276: matched
  patient-free `imminent_bodily_harm` (gloss "the user faces an immediate risk…"), three
  user-chained siblings, 0.35844 → 0.17814. m0239: matched PATIENT-BEARING act, `why:
  mismatched`, no third-party span anywhere. m0018: matched act atom chain `[model,
  third_party]`, `why: mismatched` against {user, developer}. Every number in §1, §3, §4
  checked against the dossier JSONs.
* **The mechanism genuinely separates m0275 from m0276** — via attribution, exactly as
  claimed: the bearer is legible from text/gloss for both ("another person" vs "the user
  faces an immediate risk"), and no chain-only rule can do it (§3's wall, re-verified
  against DISCOUNT_DERIVATION §3's (a)/(b) separator finding).
* **B-2's resolution is the scientifically honest move**, correctly grounded in
  backfill_author rule 3 + the m0236 precedent, with a coherent handoff
  (IMPLIED_EFFECTS_DESIGN names m0239 as first case and commits to count-first sizing).
* **The B-3 core insight is right**: "predicted but not attributed is FAIL, not PASS"
  kills the I1-manufactured trivial pass; the independent post-freeze check is
  pre-registered.
* **Invariants I1/I2/never-outprice are enforceable and testable**: I1 by the empty-
  attribution + declared-patients snapshot (dict-equality of the behaviours section,
  exactly the S3 review's I1 re-derivation pattern); I2 by per-clause raw monotonicity
  pins on a frozen pair; never-outprice by `priced_credit ≤ base_credit` per match. The
  opt-in seam pattern (pricing_version + declared patients in config identity, dossier
  dispatch ladder) is correctly inherited in intent (E-6 is the missing mechanics, not a
  wrong pattern).
* **The discipline holds**: D1–D5 are refused default resolutions; §7.4 restates the
  no-census/panel/judge/gold policy; the repair channel and own-cycle artifacts are now
  fenced; token scan honestly demoted to backstop.

## Recommendation

REVISE — a fourth pass, and it is a short one. Two blockers, both amendment-grade:
(1) E-1 — one rule sentence + one pinned test resolving the cap's composition with
branch-1/branch-2 atoms on tainted mixed clauses (and reconcile branch 1's "never as a
discount" prose with whichever horn is chosen); (2) S-1 + S-2 — restate the restoration
signature as a branch-keyed disjunction and pin its iteration set to the named clause
ids, so m0018 can PASS under whichever D4 horn is ruled. Fold in the four standing
majors while the document is open: keying (E-2) and value space (E-3) as two sentences
in §5.1 with validator checks; the golden re-argument or pre-registered re-derivation
trigger (S-3); a real figure-procedure-denominator-threshold in §7.5 or the claim struck
(S-4); the population-predicate definition/seat/fence (E-4); and the whitelist fence
statement (E-5). The minors can ride along. Then re-review: S-1's fix changes the
falsification bar's text, which deserves fresh eyes again.
