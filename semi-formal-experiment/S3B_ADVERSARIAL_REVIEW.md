# S3B_REDESIGN.md (REVISION 2) — clean-context adversarial review

Date: 2026-08-04. Reviewer: clean-context adversarial design reviewer (no prior
involvement). Standard held: PORTFOLIO_REVIEW.md / CYCLE5_REVIEW.md — findings must be
document-grounded or computed against the live record, not reasoned vibes. Ground truth
checked: `cycles/patient-pricing-2026-08-04/` — `decision.json`, `ADJUDICATION_LEGS.md`,
`DISCOUNT_DERIVATION.md`, `flip_verdicts.json`, and the flip dossiers for m0275, m0276,
m0239, m0466, m0018, m0290 (verdict file), plus `briefs/backfill_author.md` and
`CYCLE5_DESIGN.md` for the cited precedents.

## Verdict: REVISE

Three blocking findings, six major, five minor. The direction is right and the
dossier-level diagnosis is accurate — verified, not taken on faith (see "What holds"
at the end). But the pricing rule as written is not computable and contradicts the
design's own invariant I1 on constructible clauses; one of the three pre-registered
core restorations (m0239) is unreachable under §5.1's own licensing discipline; and
the restoration half of the falsification bar can pass vacuously. None of this
indicts the mechanism idea; all of it is amendment-fixable. Do not OPEN on this draft.

---

## BLOCKING

### B-1 — §5.3 is not a computable pricing rule, and contradicts I1 on constructible clauses

The rule has three branches: consistent iff `attributed_harm_bearers(a) ∩ P ≠ ∅` or
`generic` or "attributes no harm-bearer (patient-free-and-harm-free → absent-is-absent)";
mismatched iff harm-bearers "non-empty, specific, and disjoint from P"; clause taint
"applies only when every harm-bearing atom on the clause attributes harm-bearers
disjoint from P." Three defects:

1. **"Harm-bearing atom" is never defined.** The taint trigger quantifies over it; the
   population in D5 ("patient-free harm-describing atoms") uses a sibling predicate with
   no operational definition either. Which atoms count — all atoms with attribution
   records? Atoms with non-empty `harm_bearers`? Situation atoms plus patient-bearing
   acts? The rule is unbuildable until this is pinned, and the choice changes outcomes
   (see 3).
2. **Empty/unclear attribution falls in no branch.** A *patient-bearing* atom whose
   attribution record has empty `harm_bearers` is not covered by branch 1's absent arm
   (the parenthetical restricts it to "patient-free-and-harm-free"), and not by branch 2
   (requires non-empty). This input is foreseeable, not exotic: §5.1 borrows "exactly
   the spirit of S2's validator-checked backfill," and S2's regime makes `unclear` a
   first-class legal verdict — `briefs/backfill_author.md`: "If a question cannot be
   answered from the clause text and the notation, the answer is `unclear`… never force
   a call."
3. **Vacuous taint breaks I1.** "Every harm-bearing atom attributes harm-bearers
   disjoint from P" is vacuously TRUE when no atom attributes a harm-bearer. A clause
   with zero attributed harm-bearers is therefore tainted at factor d — directly
   contradicting §6 I1 ("No declared patients, **or no attributed harm-bearers**, ⇒
   bit-for-bit ContainmentIndex") and silently dropping S3's taint precondition
   (DISCOUNT_DERIVATION §0: taint = "≥1 patient-bearing chain, none consistent").
   Constructed case: a clause whose only atoms are patient-free and harm-free (the
   `response_specific_format` atom in m0466's dossier is a real instance of the shape),
   queried by a behaviour that declares patients: I1 says bit-identical; §5.3's vacuous
   taint says d·cap. The two cannot both ship.

**Fix.** Define "harm-bearing atom" mechanically; define the price of empty/unclear
attribution (atom-level factor 1.0 + exclusion from the taint quantifier is the only
reading consistent with I1); give the taint trigger existential import (≥1 attributed
disjoint harm-bearing atom required, restoring S3's precondition in attributed terms);
state branch precedence. Golden review of the backfill must cover the `unclear`/empty
verdicts, not just the positive ones (PORTFOLIO_REVIEW F10's fence pattern: golden
review covered `no_chain` verdicts for exactly this reason).

### B-2 — §7.1 pre-registers restoring m0239, but §5.1's own discipline cannot license it

§7.1's falsifiable core names m0239 returning to `predicted`. Restoring m0239 requires
attributing a beneficiary in P = {third_party} to `should_deescalate_extremist_involvement`
(or defeating taint via such an attribution). But the m0239 dossier shows the clause
text and all three glosses name **no third party**: "If a user shows signs of
vulnerability to radicalization, the assistant should aim to de-escalate…"; glosses
"the user shows signs of being susceptible to extremist recruitment or influence",
"reduces the user's movement toward participation in extremist activity", "explains
that extremist ideologies are harmful and broadly discredited". The adjudication's own
reason had to supply the bearer by inference — flip_verdicts.json, m0239:
"Radicalization leads to violence against third parties."

§5.1 requires attribution that is "panel-blind, **document-grounded**" with "a short
**verbatim** `license_quote`", reading "clause text + gloss + the golden chain
convention only." There is no verbatim span in m0239 licensing third_party. Worse, the
notation discipline §5.1 leans on explicitly forbids this inference in the sibling
artifact — backfill_author.md rule 3 (verbatim from annotate_prompt.md): "Write a party
ONLY where the clause names one. **Do not infer an affected party from the subject
matter: a clause forbidding an act does not thereby name whoever that act would
harm.**" The recorded precedent is m0236 — an extremist-content clause whose
`__model_third_party` chain was REMOVED on exactly that ground. S3b's m0239 attribution
is the inference that rule exists to prohibit, repackaged as a new field.

§4B calls m0239 "the sub-defect that most clearly forces beneficiary attribution" —
true, and that is precisely why the document must confront the fact that its core
prediction rests on an attribution its own licensing regime cannot produce. As written,
§7.1 either fails or requires silently loosening §5.1 at build time.

**Fix.** Either (a) widen §5.1's evidence regime explicitly — name the new evidence
class (e.g., inference from section context or the behaviour definition), give it its
own fence and golden-review treatment, and say what `license_quote` means for an
inference — or (b) demote m0239 from the falsifiable core to a stretch target and
restate §7.1's core as m0275 + m0466 (+ m0018 conditional on D4). Pick before OPEN;
do not discover this at MEASURE.

### B-3 — the restoration plank of §7 is vacuously satisfiable; no signature distinguishes "restored by the mechanism" from "never touched"

The revert restored the S2 baseline bytes (decision.json, REVERT SEMANTICS: the
baseline snapshot is bit-identical). In the S2 baseline m0275, m0239, m0466 are
`predicted` — they only "left" during the reverted S3 cycle. So if S3b prices them
back above cut, they produce **no flip**, and flip-set adjudication never sees them.
The only observable failure is re-removal (caught by `max_regressions: 0`). That makes
the positive claim untestable as written — and §6 I1 manufactures a trivial pass: a
clause with no attributed harm-bearers prices bit-identically, stays `predicted`, and
§7.1's "returns to predicted" passes with zero mechanism involved. A *partial*
attribution failure (attribution lands on m0276's clause but not m0275's) passes BOTH
§7.1 and §7.2's canonical controls while demonstrating nothing.

§5.1 promises the restore-check runs "by a party the attributor never reports to, AFTER
attribution is frozen," but nowhere pre-registers **what the check measures**. A
falsification bar that cannot distinguish success from inaction is not a falsification
bar; it is a hope.

**Fix.** Pre-register a per-clause mechanical restoration signature, checked on the
S3b snapshot's explain trail by the independent seat: for each named clause, the
matched atom's pricing explanation must show non-empty `attributed_harm_bearers ∩ P`,
factor 1.0, and `why = consistent` (not `clause_taint`, not absent). "Predicted but
not attributed" counts as FAIL of the restoration plank, not PASS.

---

## MAJOR

### M-1 — harm-bearer value space and the text→principal mapping are unspecified

§5.3 intersects `attributed_harm_bearers(a)` with P, where P is declared principal
vocabulary ({third_party}, {user, developer}). §5.1 never pins the value space of
`harm_bearers` or the mapping from clause noun phrases to principals. If attribution
records free text ("another person", "someone", "potential victims"), the intersection
is syntactic and can silently miss — the entire mechanism turns on m0275's "another
person" landing as `third_party`. The project already has a principal set
(backfill_author.md: third_party, developer, operator, system, model, root, user).
**Fix:** pin `harm_bearers` to that vocabulary and put the mapping rule in the
attribution brief, validator-checked like S2's license quotes.

### M-2 — attribution keying granularity unspecified; atom-name keying would corrupt a §7.2 control

The same atom name carries different harm-bearers in different clauses:
`user_requests_harmful_advice` matched m0466 (anthrax — harm falls on "someone", a
third party) and m0290 (self-starvation — "The atoms 'user_requests_harmful_advice'
and 'should_validate_emotional_experience' concern user self-harm", flip_verdicts.json).
§5.3 reads `attributed_harm_bearers(a)` without saying whether attribution is keyed per
(clause, atom instance) or per atom name. Name-keying is self-contradictory, and the
error would land on m0290 — the §7.2 automatic-REVERT control. **Fix:** state in §5.1
that attribution is keyed per clause instance (clause_id + span), and validator-check
it.

### M-3 — the generic flag re-prices a carried-forward golden case, and §2.1's own re-derivation trigger is never applied

DISCOUNT_DERIVATION §1 case #5 (m0248, "abuse, harassment, or negativity toward
**individuals**", chain third_party, hypothetical P = {user}) is golden judgment (b):
factor d, the clause "should not outscore the user-chained material." §2.1 carries d =
0.10 and the derivation forward "UNCHANGED… NOT reopened." But §4C's generic test is
exactly the logic that restores m0018: decision.json — "'people' as written
comprehends the users and developers." "Individuals" generalizes past the recorded
patient the same way "people" does (the derivation's own words: "the act-noun
generalizes"). Under §5.3, a consistent attributor flags m0248's atom generic ⇒
factor 1.0 ⇒ it outscores user-chained material — golden judgment #5 inverted. The
design never mentions derivation cases #5/#6. Under the S3-era declarations the path
is latent (no user-declaring behaviour queries abuse atoms), which makes this the right
moment to pin it rather than discover it when declarations widen. **Fix:** either state
a mechanical generic criterion that separates m0018's "people" from m0248's
"individuals" and pre-register it as golden-testable, or concede that §5.3 re-prices
derivation cases and pre-register the §2.1 remedy — blind re-derivation of d under the
amended rule — before OPEN.

### M-4 — §7.5 gestures at N1; "the expected-recovery figure is pre-registered here" is false

N1 asked for "a pre-registered expected-recovery figure, not discovered at MEASURE."
§7.5 pre-registers the *obligation* to estimate before OPEN — no figure, no method, no
denominator, and no trigger: "grounds to RE-SCOPE" is advice, contrast §7.2's hard
automatic REVERT. A MEASURE-time comparison against nothing is still discovering at
MEASURE. **Fix:** tie §7.5 to D5's enumeration, name the blind procedure, pre-register
the threshold under which the cycle re-scopes or does not open — or strike the claim
that a figure is pre-registered.

### M-5 — the B1 fence is genuinely improved but not airtight: three residual paths

The fix is real and much better (names S3B_REDESIGN.md, the S3 cycle directory, the
census; standalone brief; independent post-freeze check). Residual holes:
(a) **S3b's own cycle artifacts are not fenced.** The fence lists the S3 cycle
directory, but at OPEN S3b's own prediction.json will name the expected restorations —
and under delivery option (b) the attribution seat runs *inside* that cycle. Add "any
artifact recording S3b's expected flips, including its own prediction/OPEN records."
(b) **The repair channel is unfenced.** §5.2(a) calls attribution
"auditable/rechain-repairable"; §6 says attribution "MUST NOT be fit to flip outcomes."
Attribute blind → run §7.1 restore-check → "repair" the failing clauses is fitting to
outcomes by another name. Either prohibit post-check repair, or treat any repair round
as a new attribution pass: re-blinded, re-frozen, independently re-checked.
(c) **The token scan is oversold.** "FORBIDDEN-token scanned like every query module"
cannot catch this leak class: clause ids and text are legitimate attribution inputs,
and the answer key is semantic (which clause gets which bearer). The honest defenses
are the standalone-brief discipline and the independent check; say the scan is
belt-and-braces, and note that the brief's author necessarily knows the key.

### M-6 — §7.1 misstates the adjudication record and drops m0018

"Restore the confirmed regressions" then names three of the four: decision.json
`confirmed_regressions = [m0239, m0275, m0466, m0018]`; ADJUDICATION_LEGS.md:
"Confirmed regression count = 4"; and §1 of this very document says "4 confirmed
regressions". m0018's restoration is conditional on D4, which §7.1 does not say;
"(the exact flips S3 wrongly removed)" is also inaccurate (four confirmed plus m0108
contested). **Fix:** state m0018 in §7.1 as D4-conditional, or rule D4 pre-OPEN and
include it in the core.

---

## MINOR

- **m-1.** §7.5 citation arithmetic: "moved ~1/155 of its nominal class… (the canonical
  m0276/m0290)" — CYCLE5_DESIGN pins "1 × fp_promiscuous_atom (m0276 — … the ONLY
  member of the 155-clause nominal target class that moves)". The number and the
  parenthetical contradict each other (m0290 did flip correct in the measured cycle, so
  the substantive concession holds — fix the wording).
- **m-2.** D5's predicate "patient-free harm-describing atoms" has no operational
  definition, no named seat, and no fence statement; the enumeration is an input to D1,
  yet §5.2/§8-D1 do not restate the D5-before-D1 ordering (only D5's own entry does).
- **m-3.** §5.3 hardcodes one horn of open D4: "or `a` is `generic`" reads as settled
  mechanism while D4 (flag vs patient-free convention) is explicitly open. State the
  rule's dependence on D4's outcome.
- **m-4.** N3's fix attaches only to the withdrawn rule: stratified controls govern "if
  any version is ever floated standalone" (A-structural), while the live corpus-wide
  rule §5.3 keeps only §7.1's named clauses plus the two canonical controls. Re-attach
  the stratified-sample commitment to the live mechanism (PORTFOLIO_REVIEW F11 required
  stratified-sampling pre-registration in this portfolio).
- **m-5.** m0108 (contested, defect-(i) shape) is "NOT counted either way" — defensible,
  but pre-register its expected pricing signature as an exploratory observation; as
  written, a silent m0108 restoration or non-restoration teaches nothing.

---

## What holds (verified, briefly)

- **§1's three findings** transcribe decision.json accurately (confirmed regressions,
  contested m0108, canonical removals, "provenance not arithmetic").
- **§3's contrast table is exact against the dossiers**: m0275's matched patient-free
  situation `expressed_harmful_intent` (gloss "the user expresses an intention to harm
  another person"), sole patient-bearing sibling `should_provide_supportive_response` →
  user, factor 0.1 why `clause_taint`, scores 0.35147 → 0.13088 vs cut 0.23651; m0276
  structurally identical (patient-free `imminent_bodily_harm` + three user-chained
  acts, 0.35844 → 0.17814). The wall is real: the separator lives in gloss text, and
  an attributed harm-bearer IS legible from the text for m0275 ("another person"),
  m0276 ("self-harm", "the user is in imminent danger"), and m0466 ("mailing someone
  anthrax"). Attribution can separate them — the specification just is not buildable yet.
- **B2 is genuinely fixed.** §4A/§5.4 withdraw the standalone structural guard on
  correct dossier evidence, no attribution-free shortcut survives anywhere in §5–§9,
  and §5's preservation claim is honestly hedged ("attribution-dependent — this claim
  provides no cover for any pre-attribution structural step").
- **N2/D5 is present** with the correct ordering. §2's carry-forward list, §7.2's
  automatic revert, and §9's nothing-ships are all intact.

## Recommendation

Fix B-1/B-2/B-3 in a REVISION 3, then re-review (this reviewer or a fresh clean-context
seat — B-2's resolution changes the falsifiable core, which deserves fresh eyes). The
majors are all amendment-grade and several can be folded into the same pass: define the
harm-bearer vocabulary and keying with the attribution brief (M-1, M-2), reconcile the
generic flag with derivation case #5 or pre-register re-derivation (M-3), put a real
number-method-trigger in §7.5 (M-4), close the three fence gaps (M-5), and correct §7.1
against the adjudication record (M-6). D1 should be ruled only after D5's enumeration
exists, as the document itself requires.
