# D5 — which atoms get an affected-party attribution? A decision document

**The question:** the S3b backfill will ask a model, per atom, *"which party does this
clause's harm or protection fall on?"* D5 decides **which atoms are on that list**. Three
candidate lists exist: 368, 427/439, or 746 atom-instances.

**Status:** analysis for a ruling. Nothing ruled, nothing implemented. Written 2026-08-05,
revised the same day after the five-case basis was challenged and replaced with a
corpus-wide measurement.

⛔ **Not seat material.** This reads S3's flip outcomes and the census. Never hand it to the
attribution seat or any adjudication seat.

> **Naming note (ruled 2026-08-05):** the field is being renamed `harm_bearers` →
> **`affected_parties`**. The mechanism was never harm-only — the attribution procedure
> asks about "harm, risk, **protection, or benefit**", the population predicate includes
> benefit keywords, and one of the three named restorations (m0018, *"People should have
> easy access to trustworthy safety-critical information"*) is a pure-provision clause with
> no harm in it at all and zero harm-keyword matches. The old name pulled against the
> definition in a document the seat reads.

---

## 1. The thirty-second version

- **368 breaks the mechanism**, provably (§4). Reject it on the record.
- **427 and 439 are tied** on every measurement available — same 79 cases reached. The 12
  instances separating them change nothing I can detect.
- **746** reaches 3 more of the 155 target cases, for ~307 extra model calls.
- **The finding that matters more than the band:** at its best, this mechanism reaches
  about **half its own target class** — 79 of 155. The other 76 are out of reach for every
  band on the table, because they are not all the same problem (§6).

The band choice is the small decision. §6 is the large one.

---

## 2. What you need to know to judge this

**1. A clause is scored through its atoms.** Each clause was annotated with short named
facts — `imminent_bodily_harm` (a *situation*), `should_provide_supportive_response__model_user`
(an *act*). A query matches against these names, and a clause's score comes from the atoms
that matched.

**2. Some atoms carry a "chain", most don't.** The `__model_user` suffix means "the model
does this *to* the user". Situation atoms almost never carry one. The 368-list is exactly
"atoms carrying a chain of length ≥ 2".

**3. S3 failed because a chain says the wrong thing.** The chain records who an act is
*addressed to*; S3 priced as if that were who the harm *falls on*. The spec's guidance on
de-escalating a user's radicalization is addressed to the user, but protects third parties.
S3 deleted it, and was reverted.

**4. What attribution does.** For each atom on the list, a model records `affected_parties`
— `{third_party}`, `{user}`, etc. Pricing compares that to the patients your query
declares: overlapping → full credit; disjoint → discounted, and if *every* resolved atom on
the clause is disjoint, the clause is tainted and its credit capped.

**5. The rule that decides this question:** *an atom not on the list gets no record, and an
atom with no record keeps full credit and is exempt from the cap.* Being off the list is
not cautious handling — it is **invisibility to the mechanism**. Any credit riding on that
atom passes through untouched.

---

## 3. The wall — the two clauses that define the problem

**m0275 — must be restored.** *Do not facilitate or encourage illicit behavior > ¶6.* An
example where the user says **"I want to shoot someone."**
- `expressed_harmful_intent` — situation, **no chain**. Gloss: *"the user expresses an
  intention to harm **another person**"* → harm falls on a **third party**.
- `should_provide_supportive_response__model_user` — act, chain `model → user`.

**m0276 — must stay suppressed.** *Do not encourage self-harm, delusions, or mania > ¶1.*
- `imminent_bodily_harm` — situation, **no chain**. Gloss: *"**the user** faces an immediate
  risk of serious physical injury or death"* → harm falls on the **user**.
- three acts, all `model → user`, including the *same*
  `should_provide_supportive_response__model_user` m0275 carries.

The chains are identical. The only discriminating information is on the **unchained
situation atom**. That is why attribution must reach unchained atoms.

---

## 4. Why 368 fails

Which atom actually carried the credited match, read from the S3 flip dossiers:

| clause | atom the score came through | chained? | on the 368-list? |
|---|---|---|---|
| **m0276** (must stay suppressed) | `imminent_bodily_harm` | no | **no** |
| **m0275** (must restore) | `expressed_harmful_intent` | no | **no** |
| **m0466** (must restore) | `user_requests_harmful_advice` | no | **no** |
| **m0108** (contested) | `harmful_instructions` | no | **no** |
| m0239 (→ implied-effects) | `should_deescalate_extremist_involvement` | yes | yes |

Apply fact 5. Under 368 those four atoms get no record, keep full credit, and are exempt
from the cap:

- **m0276 is not suppressed.** Its score runs entirely through an exempt atom, so nothing
  discounts it. The design makes m0276 resurfacing an **automatic revert**.
- **m0275 and m0466 restore for the wrong reason** — because nothing was attributed, not
  because a third-party bearer was licensed. The restoration check requires them back
  specifically as *"consistent"*, so they **fail the plank** too.

Two pre-registered checks failed in opposite directions. **368 is not conservative; it is
inert.**

---

## 5. Corpus-wide reach — the measurement that replaced the five-case argument

Five hand-picked clauses were too thin a basis. Recomputed over every clause the tool
predicts (panel-blind, no labels), and separately over all 155 target cases.

**Panel-blind — clauses the tool predicts, by behaviour:**

| behaviour | predicted | 368 | 427 | 439 | 746 |
|---|---:|---:|---:|---:|---:|
| avoiding-over-and-under-caution | 95 | 26 | 26 | 26 | **32** |
| harm-avoidance-to-third-parties | 73 | 17 | **40** | **40** | **40** |
| helpfulness | 146 | 78 | 78 | 78 | 78 |

**Census cross-check** — the 155 `fp_promiscuous_atom` cases (panel-derived, **attention
only**, never the ruling's primary ground):

| list | reaches | unreachable |
|---|---:|---:|
| 368 | 67 (43%) | 88 |
| 427 | **79 (51%)** | 76 |
| 439 | **79 (51%)** | 76 |
| 746 | 82 (53%) | 73 |

Three things follow:

1. **The band matters only for harm-avoidance** (17 → 40). For caution and helpfulness,
   368 = 427 = 439 exactly.
2. **427 and 439 are indistinguishable** — identical on all three behaviours and on the
   census. The EXT keywords buy nothing measurable in *reach*. (They may still improve the
   correctness of individual attributions; reach is what was measured.)
3. **746's apparent gain does not survive inspection.** The counting says +3 census cases
   and +6 caution clauses. Naming the atoms behind them says otherwise — the *entire*
   marginal gain, on both bases, comes from exactly **two atom names**:

   | atom | clauses it adds | gloss |
   |---|---|---|
   | `positive_user_intent` | m0164, m0170, m0171, m0174 | *"the user is presumed to have a constructive rather than **harmful** purpose"* |
   | `incomplete_user_context` | m0374, m0428 | *"the assistant lacks complete knowledge of the user's intent, values, or circumstances"* |

   `positive_user_intent` is **one of the four audited false positives** the b-trim
   predicate removes — the keyword match is on a *negation*. `incomplete_user_context` is a
   model knowledge-state, not a harm or a protection falling on any party. Under the
   attribution procedure's own step 1 — *"if the atom does not describe a
   harm/protection/benefit falling on any party, answer `unclear`"* — both return `unclear`,
   which prices at factor 1.0 and changes nothing.

   So 746's reach over 439 is **nominal, not effective**, and part of it is bought by
   re-admitting an atom a gloss audit already rejected. (Three answers were given on this
   question during analysis: "no gain" from five cases, "+3" from corpus-wide counting, and
   this one. Trust this one — it is the only one that names the atoms.)

---

## 6. The 76 unreachable cases are not one problem

Tested first: are they just *generic* atoms? **No.** Median document frequency is identical
across reachable and unreachable sets (3), mean identical (4.2). And 43 distinct atoms
produce the 76 cases — the top atom accounts for 9%, the top twelve for 50% — so no small
vocabulary fix clears them either.

What separates them is **subject matter**. Of the 82 matched-atom hits in the unreachable
set, 80 resolve to annotation instances: **all 80 are patient-free**, and by kind they are
**66 acts, 9 values, 2 entities, 3 situations**. The dominant names are helpfulness-domain:
`should_fill_information_gaps`, `should_provide_neutral_factual_information`,
`ask_clarifying_questions`, `provide_clear_answer`, `explain_reasoning`,
`deep_understanding`. These describe **answer quality**. There is no harm and no protection
in them, so "which party does this fall on?" has no answer — not a difficult one, none.

By clause text, the 76 split: **17** name a third-party-class noun, **29** name only
user/developer-class nouns, **30** name no party noun at all.

So `fp_promiscuous_atom` is a census label for a *symptom* — an atom matched, the panel
disagreed — not a mechanism. It decomposes:

| sub-cause | the feature that addresses it | cases |
|---|---|---:|
| Bearer named, and it isn't the query's patient | **S3b attribution** (this build) | **79** |
| Bearer nameable but the atom is an *act* — excluded because the population is situations-only | **population extension** — see `D5B_ACT_ATOMS.md` | ≤ **17** |
| Bearer implied, never named in the text | **implied-effects layer** — human-approved, per entry | part of the remaining 59 |
| No party at all — the clause is about answer quality | not an attribution problem; query-atom curation / structural role (S6, S6b) | ~30 |

Treat 17 as an **upper bound**. m0276 is the standing lesson: its text says "there are
**people** and resources who care", which scans as third-party, but the atom bears on the
user. A party appearing in the text is not the same as that party bearing *this atom's*
harm.

**Important correction on the third row.** An earlier draft treated "the clause names no
party" as terminal. It is not. The "never infer — write a party only where the clause names
one" rule binds the **attribution seat** (cheap, mechanical, panel-blind, must produce a
verbatim `license_quote`). When the bearer is implied rather than named, the seat returns
`unclear` — and `unclear` is the **queue for the implied-effects layer**, where a human
approves the judgement once, offline, logged with `approved_by`, `approved_date`, and a
revocable lifecycle. m0239 is that layer's first intended entry. So the residue is not
unreachable; it is **human-gated**.

That reframing comes with its own constraint, in the layer's own words (§1.5): it is *"the
highest-risk surface in the project for panel-fitting, because it is judgement."* Its
review is at REVISE with four blockers, two of them exactly here — the proposal *queue* is
unfenced (approval is fenced, but fitting happens at proposal time), and there are no
pre-registered negative controls, while every approved entry carries taint-defeating power:
the same power that would resurface m0276. The batch-approval path that would make dozens
of entries affordable is, per that review, *"provably unable to separate m0239 from
m0276"* as specified.

---

## 7. What this changes about the build's expected value

`BUILD_OVERVIEW.md` says S3b "attacks the census's largest error cause, 53%". That is the
size of the **class**, not of the fix. The class is 155 of 294 (53%); attribution reaches
79 of 155 (51%); so S3b as scoped addresses **79 of 294 ≈ 27% of all disagreements**. With
D5b at its optimistic ceiling, ~96 of 294 ≈ 33%.

Still the largest single lever on the board. Not the whole class, and the build should be
costed against 27%, not 53%.

---

## 8. Limits of this analysis

- The reach numbers are **structural**: they say whether the mechanism can *see* the atom
  carrying a clause's credit, not whether the attribution will be *correct*. A reached case
  can still be attributed wrongly.
- The expected bearers in §3–§4 are read from glosses; the seat has not run. If it
  disagrees on those specific cases, that is a seat defect with its own channel, not a
  reason to change the list.
- The residue characterization is tool-side only. To know *why* the panel rejected those 30
  matches I would have to read panel notes — attention-only, and reading them to shape the
  mechanism is how fitting starts. The clean way to characterize the residue is a blind
  pass: sample those clauses and have a seat say what each is about, with no labels present.
- The 368 finding rests on "no record ⇒ full credit, exempt from the cap" being read as
  written. It is stated four times in the design and is a fix from an earlier review, but
  it is the load-bearing premise.

---

## 9. Recommendation

1. **Reject 368 on the record**, for §4 — not by omission.
2. **Rule 439** for the situations population. 427 is equally defensible on the evidence;
   I prefer 439 only because its extra keywords came from a disclosed gloss audit and its
   six audited false positives are forced into the golden-review sample by design. If you
   would rather carry less judgment for identical measured reach, 427 is the honest choice
   and I will not argue.
3. **Reject 746 on the record too.** Its measured gain is two atom names — one an audited
   false positive whose keyword hit is a negation, one a model knowledge-state — both of
   which the seat would rule `unclear` at factor 1.0. It costs ~307 extra seat items and a
   larger human/frontier golden-review sample to buy nothing effective. The "removes the
   keyword judgment" argument cuts the other way: what it removes is the audit that
   *caught* `positive_user_intent`.
4. **Open D5b separately** (`D5B_ACT_ATOMS.md`): whether patient-free *act* atoms join the
   population. Bigger lever than any band delta.
5. **Correct `BUILD_OVERVIEW.md`** to state expected coverage as ~27% of the census rather
   than implying 53%.

The ruling belongs in `S3B_REDESIGN.md` §8 with its grounds and the rejected options named.
A ruling that lives only in a transcript is a review finding here.

---

## Appendix — reproduction

Deterministic, read-only, no API spend. List predicates re-implemented from
`ATTRIBUTION_POPULATION_ENUMERATION.md` §2.3–§2.5 rather than taken on trust:

```
368 (A)      := len(grammar.parse_name(name).principals) >= 2
746 (b-wide) := unchained AND kind == "situation"
427 (b-core) := 746-list AND CORE keyword in (name + " " + gloss) AND name not in FP_NAMES
439 (b-trim) := 746-list AND (CORE|EXT) keyword in (name + " " + gloss) AND name not in FP_NAMES
FP_NAMES      = {positive_user_intent, instructions_intended_low_risk,
                 scope_inadequate_for_task, user_prosocial_preferences}
```

⚠️ **The v1.2 decoration-blind join matches on DECHAINED names**, so a matched name
`should_deescalate_extremist_involvement` corresponds to the annotation instance
`should_deescalate_extremist_involvement__model_user`. Any lookup that skips dechaining
reports zero reach for the 368-list on every behaviour — an early version of this analysis
did exactly that.

Sources: `matched_atoms` from `idx.explain(behaviour, clause)` on the log-resolved baseline
(`join-integrity-v2-2026-08-04`, `ContainmentIndex` + `overlay_empty.json`, frozen
thresholds); census rows from `audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json`
joined to clauses via each dossier's `mapped_clauses` and `discriminators.exact_name_intersection`;
flip evidence from `cycles/patient-pricing-2026-08-04/flip_dossiers/`.
