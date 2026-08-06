# D5b — should patient-free ACT atoms join the attribution population?

**The question:** the candidate population is restricted to `kind == "situation"` for every
unchained atom. That restriction was never ruled — it was recorded as a sensitivity check.
It is now the single largest lever on the mechanism's coverage, larger than any choice
between the 368/427/439/746 lists.

**Status:** open ruling, drafted for decision. Nothing implemented. Written 2026-08-05.
Companion to `D5_WORKED_EXAMPLES.md` (which rules the *keyword band*; this rules the *kind
restriction*).

⛔ **Not seat material.**

---

## 1. Why this is open

`ATTRIBUTION_POPULATION_ENUMERATION.md` §2.2 defines the candidate band as *patient-free
**situation** atoms*, with this rationale: the design locates the patient-free
harm-describing class in the situation atoms, and *"patient-free act atoms are outside
§5.1's target (sensitivity check §3.3)."* Patient-free acts — **433 instances** — were
counted and set aside.

Two things have changed since:

1. **The measured cost of the restriction.** Of the 76 target cases no list can reach,
   **66 of the 80 resolved matched atoms are acts.** The kind restriction, not the keyword
   band, is what puts them out of reach.
2. **The semantics were renamed.** The field is now `affected_parties`, and the attribution
   procedure asks about *"harm, risk, protection, or benefit"*. Under a harm-only reading,
   excluding acts was natural — acts *do* things, situations *describe* states of the
   world. Under a beneficiary reading it is much less obvious: `provide_helpful_context`
   has a beneficiary, and one of the three named restorations (m0018, a pure-provision
   clause) is already an *act* atom whose attribution is the whole point of that control.

So the restriction may be a leftover from the narrower reading the project has now
explicitly moved away from.

---

## 2. What including acts could buy — MEASURED, and it is about 2 cases

⚠️ **This section originally reasoned from an unnamed count of "≤ 17". The count-first pass
(`D5B_COUNTS.md`, 2026-08-05) named its members, and the ceiling collapsed.** The pattern is
the same one that dissolved the 746 band in `D5_WORKED_EXAMPLES.md`: a count that looks like
a case for widening turns out, once its members are named, to be mostly false positives and
incidental matches.

The 17 shrinks **mechanically**, before any judgement is applied:

| step | remaining |
|---|---:|
| census cases unreachable under 439 whose clause text names a third-party-class noun | 17 |
| minus 1 duplicate (m0353 counted twice — same clause, same atom) | 16 |
| minus 3 whose atoms are `value`, outside this act proposal (m0019, m0050, m0482) | 13 |
| **minus every row whose atom the act keyword screen does not admit** | **3** (m0209, m0214, m0226) |

Of those 3, the designer estimate is **2 plausible** (m0209 and m0214 — both carrying
`shouldnot_facilitate_critical_harms`, both caution FPs where a `third_party` attribution is
disjoint from the query's `{user}`, so the clause is suppressed and the false positive is
fixed), and 1 split (m0226, whose atom appears on the count-pass's own false-positive list).

**Best estimate of the real ceiling: 2, plausible range 1–4** — and both survivors come from
a *single atom name*, which is a thin basis for a population change.

The remaining 11 rows are incidental mentions, exactly as the m0276 trap predicts: the
third-party noun is the topic of an example dialogue (×5), a capacity misattribution
(m0136's "third parties" are bound delegates, not victims), a scan artifact (`\bhuman\b`
inside "human rights" at m0327), and m0589 — the m0276 trap verbatim, where "teen" is the
conversation's own user per the §1.4 note (i).

One row deserves separate mention because it shows reach and yield are different things:
**m0019 is plausible but worth zero** — it is the one harm-avoidance row, where a
`third_party` attribution *overlaps* the query rather than being disjoint, so the atom keeps
full credit and the false positive survives untouched.

Coverage arithmetic, at the realistic ceiling: 81 of 155 target cases (52%) against 79
(51%) today — i.e. ≈27% of the census either way, unchanged to the nearest point.

---

## 3. The argument for including acts

- **The exclusion is unruled.** It sits in an enumeration document as a scoping choice,
  with no designer ruling and no adversarial review behind it. Everything else at this
  level of consequence in S3b has one.
- **It is now the dominant constraint.** 66 of 80 unreachable matched atoms. Every band
  argument is worth ≤ 3 cases; this is worth up to 17.
- **m0018 proves acts are attributable.** A chained act atom carrying a comprehensive
  generic is already a load-bearing control. Chained acts are in the population by
  construction; the line between them and *unchained* acts is about annotation history, not
  about whether the atom has a beneficiary.
- **The semantics moved.** `affected_parties` over "harm, risk, protection, or benefit" does
  not obviously exclude acts.

## 4. The argument against

- ~~**Scale and cost.** 433 patient-free act instances exist…~~ **WITHDRAWN — this argument
  was wrong.** Filtered by the same keyword predicate the situations got, the act population
  is **41 instances / 26 names / 38 clauses** (CORE-only: 36 / 21 / 34), of which 20 clauses
  would be newly reached. That is a *small* addition, not a large one. Do not use the 433
  figure — it is the unfiltered count. (`D5B_COUNTS.md` Task 1, which also reproduces the
  situations-side pins 368 / 378 / 59 / 77 / 71 exactly.)
- **THE REAL ARGUMENT: the keyword predicate does not transfer to acts.** Measured false-
  positive rate is **39–63% on acts versus 7.8% on situations**, and the four audited
  `FP_NAMES` exclusions remove **zero** act instances — every one of them is a situation
  name, so the audit that protects the situations band does no work here. The failures are
  the same negation shape that got `positive_user_intent` excluded: 16 of 41 instances match
  a harm keyword *inside a negation* — `should_provide_neutral_factual_information`
  ("without risk-amplifying" ×6), `should_follow_intended_instructions` ("low risk" ×5 — the
  act twin of the already-excluded situation `instructions_intended_low_risk`),
  `should_provide_public_information` ("unlikely to cause harm" ×2),
  `may_provide_political_content` ("not targeted for manipulative exploitation" ×2),
  `should_preserve_truthfulness` ("nondeceptive" ×1). Admitting acts on this predicate means
  admitting a population that is 2-in-5 noise into a mechanism whose dominant direction is
  suppression. A transferable predicate would have to be designed and audited first, which
  is a piece of work, not a scope tweak.
- **The suppression direction is the dangerous one.** Attributing `{user}` to helpfulness
  acts on clauses a third-party query currently reaches will *taint* those clauses and
  remove them. Every S3b regression to date was a wrongful removal. Widening the population
  in a direction that predominantly produces removals deserves controls before it is run,
  not after.
- **Acts may be systematically harder.** An act's beneficiary is often the party the act is
  addressed to — which is precisely the chain-shaped inference that caused the S3 revert.
  A seat asked "who benefits from this act?" is under more pull toward the grammatical
  recipient than one asked "who does this harm fall on?".
- **It reopens a settled scope.** S3b is at REVISION 9 with a long review chain. Widening
  the population changes the §7.5 denominator, the reach figure, the parity sample strata,
  and the golden-review boundary set. That is a revision, not an amendment.

---

## 5. What would decide it cheaply

Both steps are deterministic, local, and cost nothing:

1. **Count first.** Apply the existing keyword predicate to the 433 patient-free act
   instances: how many survive, on how many clauses, and how many of those clauses are
   reached by a declared query at all? The band decision had this number; this one does not.
2. **Blind scan the 17.** Run the pinned §1.4 noun-phrase table over just those clauses and
   record, per row, whether a third-party phrase is present *and* whether it plausibly names
   the bearer of that atom rather than an incidental mention. That converts "≤ 17" into a
   defensible estimate — and it is the same scan the design already specifies, on a
   different population.

Neither step attributes anything or spends a model call.

---

## 6. Recommendation

**Do not widen S3b now. Rule the exclusion explicitly, run the two counts, and carry the
extension as a named follow-up.**

Grounds (revised after the count-first pass — the direction is unchanged but the reasons
are different, and stronger):

- **The measured yield is ~2 cases, range 1–4**, both from a single atom name — not the ≤17
  this document first assumed. Against 79 already reachable, that moves census coverage from
  51% to 52%, which is ≈27% of all disagreements either way.
- **The keyword predicate does not transfer.** 39–63% false-positive rate on acts vs 7.8% on
  situations, with the existing `FP_NAMES` audit removing zero act instances. Widening on
  this predicate admits a 2-in-5-noise population into a mechanism whose dominant direction
  is *suppression* — the direction that produced every S3b regression so far. Fixing that
  means designing and auditing a new predicate for acts, which is its own piece of work.
- S3b is nine revisions deep with a settled population, a pinned denominator, pre-registered
  controls, and a parity sample designed around that population. Widening now restarts a
  review chain that has already found and fixed twelve blocking-or-major defects — to buy
  two cases.
- Nothing is lost by sequencing: the act population does not decay, and after S3b measures
  we will know how attribution actually performs where it *is* reachable. That is far better
  evidence for widening than an argument from clause text.

**Caveat carried from the count pass, unresolved:** the two survivors were assessed for
*reach* ("would the seat resolve `third_party` here?"), not for *flip* ("would the case
actually change?"). Under §5.3 the cap requires **every** resolved atom on the clause to be
disjoint from the query. Both survivors have single-name matched sets, so it is reachable —
but it was not simulated, and 2 is an estimate that has not been priced. If the ruling ever
turns on the difference between 2 and 0, simulate first.

What the ruling should say, concretely:

> The situations-only restriction is **RULED, not inherited**: S3b's attribution population
> excludes patient-free act atoms for this cycle. Grounds: bounded yield (≤ 17 of 155),
> predominantly suppression-direction, and a population change would invalidate the pinned
> §7.5 denominator, parity strata and golden boundary set at REVISION 9. The extension is
> registered as named follow-up work with a trigger: after S3b closes, if measured
> attribution accuracy on the situations population clears its floor, re-open D5b with the
> §5 counts in hand.

If you would rather widen now, the minimum I would want first is §5's two counts plus a
pre-registered control set for the suppression direction — specifically, named clauses that
a third-party query currently reaches through a helpfulness act and that **must not**
disappear.

---

## 7. Where this ruling lives when made

`S3B_REDESIGN.md` §8, alongside D1–D5, with the rejected option named. If the follow-up
form is chosen, the trigger also belongs in `LATENT_FIX_REGISTRY.md` — that registry exists
for exactly this shape: a real concern, a sketched response, and a named condition that
would promote it to active work.
