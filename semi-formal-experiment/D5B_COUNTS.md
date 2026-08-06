# D5b COUNTS — naming the act population and the 17

**Purpose:** the two deterministic counts `D5B_ACT_ATOMS.md` §5 says would decide the
patient-free-**act** ruling cheaply, run. (1) Apply the situations population predicates to
the 433 patient-free act instances. (2) Name the 17 unreachable census cases whose clause
text carries a third-party-class noun, and judge per case whether that noun plausibly names
the party bearing *that atom's* harm or protection.

**Status:** analysis for a ruling. **Nothing ruled, nothing implemented, no file changed, no
model call, zero spend.** Written 2026-08-05. Companion to `D5B_ACT_ATOMS.md` (the proposal)
and `D5_WORKED_EXAMPLES.md` (the measurement it rests on).

⛔ **NOT SEAT MATERIAL.** This document reads the census (`verdicts_merged.json` and its
dossiers) and names the clauses behind panel disagreements. It must never be handed to the
attribution seat, the adjudication seat, or any panel-blind pass. Task 2's judgements are a
**DESIGNER ESTIMATE**, not seat verdicts — the author was not fenced, read the census, and
the output is not attribution input under any circumstance.

**Headline:** the act population under the same keyword predicate is **41 instances, not
433** — D5b §4's "433 … even filtered by the same keyword predicate, this is a large
addition" is wrong by an order of magnitude; the filtered addition is 41, ~9% of the 439
population. And of the 17, my estimate is that **2 survive scrutiny** (both the same atom
name), with 3 more arguable and 12 incidental.

---

## 1. Task 1 — the patient-free ACT population

Predicates re-implemented from `ATTRIBUTION_POPULATION_ENUMERATION.md` §2.3–§2.5 (script in
the appendix; the situations-side numbers are reproduced as a pin before anything new is
computed).

**Pin check (reproduced, not taken on trust):** A = 368 · B-wide = 378 · B-core = 59 ·
B-ext = 77 · B-trim = 71. All four match §0. The act numbers below therefore come from the
same code path.

### 1.1 Survivors

| band | predicate | instances | distinct names | distinct clauses |
|---|---|---:|---:|---:|
| all patient-free acts | `len(principals) < 2 AND kind == "act"` | **433** | 243 | 302 |
| A-core | + CORE keyword on `name + " " + gloss` | **36** | 21 | 34 |
| A-core − FP_NAMES | | **36** | 21 | 34 |
| A-ext | + CORE∪EXT keyword | **41** | 26 | 38 |
| **A-trim** = A-ext − FP_NAMES | the act analogue of b-trim | **41** | **26** | **38** |

**The FP_NAMES exclusion removes nothing on the act side.** All four audited
false-positive names (`positive_user_intent`, `instructions_intended_low_risk`,
`scope_inadequate_for_task`, `user_prosocial_preferences`) are situation atoms; zero act
instances carry them. So the deduction that protects the situations band does **no work
here** — §1.3 below shows the act band needs its own audit, and needs it more.

This reproduces `ATTRIBUTION_POPULATION_ENUMERATION.md` §3.3's sensitivity line exactly
(*"41 instances, 26 names, 38 clauses"*). The EXT stems add 5 instances over CORE:
`may_discuss_minor_sexual_content` (sexual), `may_provide_general_drug_information` (drug),
`shouldnot_disclose_privileged_content` / `shouldnot_enable_privileged_access` /
`shouldnot_share_privileged_data` (private).

**Scale correction.** D5b §4's leading argument against widening is *"433 patient-free act
instances exist. Even filtered by the same keyword predicate, this is a large addition to a
backfill already at 439."* Filtered, it is **41** — a 9.3% addition (439 → 480), on 38
clauses of which **20 are new** to the population (275 → 295 clauses; 18 of the 38 already
carry a 439-population atom). That argument does not survive the count.
(The 433 figure is only reachable by an unfiltered widening, which is not the same
proposal: the situations band is keyword-filtered, so the act band must be too or the two
sides of the population are not built by the same rule.)

### 1.2 Query-side reach (panel-blind, join only)

Baseline: `ContainmentIndex.from_files(modelspec_clauses.json,
annotations_ext_v1_merged.json, overlay_empty.json)`, behaviours from
`behavior_atoms_audit_v1.json` × `behaviours_query.json`, cuts from
`thresholds_frozen.json`. Two reach senses are reported because they differ:
*predicted* = the clause is above that behaviour's frozen cut; *atom-matched* = one of these
act atoms carries an exact-name match in `explain(...)["matched_atoms"]` (dechained on both
sides). No panel value read.

| population | clauses | predicted by any behaviour | atom-matched by any |
|---|---:|---:|---:|
| **A-trim (41 inst)** | 38 | **27** | **20** |
| A-core−FP (36 inst) | 34 | 26 | 19 |

Per behaviour, A-trim:

| behaviour | predicted | atom-matched |
|---|---:|---:|
| helpfulness | 13 | 8 |
| harm-avoidance-to-third-parties | 15 | 10 |
| avoiding-over-and-under-caution | 15 | 13 |

So ~71% of the act band's clauses are reached by at least one declared behaviour, and ~53%
are reached *through one of these atoms*. That is a live population, not an inert one — which
also means the suppression risk D5b §4 names is real on those 20 clauses, not hypothetical.

### 1.3 False-positive audit of the surviving names (the `positive_user_intent` pattern)

Same audit the situations band got in §2.5: which surviving instances match a keyword but
whose **gloss does not describe a harm/risk/protection/benefit falling on a party**. On the
act side this is not a trim — it is most of the band.

**Class 1 — the canonical pattern: the keyword hit is on a NEGATION (16 of 41 instances,
5 names).** These are `positive_user_intent`'s exact shape.

| name | inst | clauses | gloss (verbatim) | why it is a hit on a negation |
|---|---:|---|---|---|
| `should_provide_neutral_factual_information` | 6 | m0210, m0213, m0235, m0237, m0240, m0312 | *"gives objective information without risk-amplifying operational detail"* (m0312: *"…without unfairly amplifying risk"*) | "risk" appears only inside *"without risk-amplifying"*; the atom is answer neutrality |
| `should_follow_intended_instructions` | 5 | m0182, m0191, m0347, m0445, m0446 | *"follows instructions that are clearly intended and low risk"* | "risk" appears only in *"low risk"* — the same negation the already-excluded situation name `instructions_intended_low_risk` was excluded for. The act twin of an audited FP was never excluded |
| `should_provide_public_information` | 2 | m0226, m0227 | *"provides public information unlikely to cause harm through disclosure"* | "harm" appears only in *"unlikely to cause harm"* |
| `may_provide_political_content` | 2 | m0217, m0219 | *"provides political material when it is not targeted for manipulative exploitation"* | both stems ("manipulat", "exploit") sit inside *"not targeted for"* |
| `should_preserve_truthfulness` | 1 | m0452 | *"keeps creative responses accurate and nondeceptive"* | "decept" appears only inside *"nondeceptive"* |

**Class 2 — word-sense / no-party hits (10 instances, 10 names).** The keyword is present
affirmatively but denotes no harm falling on a party — a topic word, a rule violation, a
model-side assessment, or confidentiality of *material* rather than a person's privacy.

| name | clause | gloss | defect |
|---|---|---|---|
| `monitor_policy_violations` | m0120 | *"…detect possible violations of usage rules"* | "violat" = breach of rules, not a party's rights |
| `assess_risk_and_skill` | m0267 | *"evaluates the danger and the knowledge or skill needed to reduce it"* | a model-side assessment; **also a substring artifact — the stem `kill` matches inside "skill"** |
| `risk_mitigation` | m0026 | *"actions intended to reduce or address risks"* | contentless; names no party |
| `creative_risk_taking` | m0451 | *"considers less predictable options when creativity benefits from risk"* | "risk"/"benefit" both describe the creative process |
| `may_provide_general_drug_information` | m0211 | *"gives high-level information about a drug without operational synthesis details"* | "drug" is a topic word; permission-shaped |
| `may_discuss_minor_sexual_content` | m0206 | *"discusses sexual content involving minors in permitted non-graphic contexts"* | "sexual" is a topic word; permission-shaped |
| `should_weigh_assumption_costs` | m0380 | *"balances the harm of incorrect assumptions against the inconvenience of asking"* | "harm of incorrect assumptions" = answer-quality cost |
| `shouldnot_disclose_privileged_content` | m0294 | *"keeps underlying manuals, prompts, or other privileged material private by default"* | "private" = confidentiality of material, not a person's privacy |
| `shouldnot_enable_privileged_access` | m0292 | *"avoids creating new access to private or privileged information"* | same |
| `shouldnot_share_privileged_data` | m0292 | *"avoids transmitting private or privileged information without authorization"* | same |

**Class 3 — flagged borderline, KEPT** (mirrors §2.5's borderline-kept convention):
`mustnot_autonomously_pursue_goals` (m0115, *"does not independently pursue engagement
metrics that do not benefit the user"* — the keyword hit is a negation, but the protection
does run to the user), `should_wait_for_danger_signal` (m0265), `should_state_violation_wrong`
(m0327, *"…fundamental human rights violation…"* — real, but the atom is a speech act),
`mustnot_perform_high_risk_activities` (m0136).

**Clean survivors (11 names / 15 instances = 7 harm-describing core names + the 4 class-3
borderlines):**
`shouldnot_facilitate_critical_harms` ×3 (m0014, m0209, m0214), `prevent_serious_harm` ×2
(m0004, m0029), `should_provide_preventive_information` ×2 (m0172, m0174),
`should_prevent_imminent_harm` (m0259), `shouldnot_provide_harmful_advice` (m0259),
`psychological_manipulation` (m0322), `may_refer_law_enforcement` (m0120), plus the class-3
borderlines.

**Audited band, with reach:**

| band | instances | names | clauses | predicted by any | atom-matched by any |
|---|---:|---:|---:|---:|---:|
| A-trim (mechanical) | 41 | 26 | 38 | 27 | 20 |
| − class 1 (negations) | **25** | 21 | 22 | 16 | 12 |
| − class 1 and 2 | **15** | 11 | 14 | 12 | 10 |

**Comparison that matters:** the situations band's audit removed 6 of 77 instances (7.8%).
The act band's equivalent audit removes 16 of 41 (39%), or 26 of 41 (63%) with word-sense
hits. The keyword screen is substantially **less reliable on acts than on situations**,
because act glosses routinely name a harm in order to say the act avoids, permits, or
weighs it. That is a mechanical fact about the predicate, independent of any view on
whether acts have bearers — and it means a widening would import a population whose
majority the seat should rule `unclear`.

---

## 2. Task 2 — naming the 17

### 2.1 Reproduction of the census figures

All of `D5_WORKED_EXAMPLES.md` §5–§6's figures reproduce exactly from the stated method:

| quantity | reproduced | doc |
|---|---:|---:|
| `fp_promiscuous_atom` census rows | 155 | 155 |
| rows with a mapped clause | 155 | — |
| resolved matched-atom instances | 173 | — |
| reachable under the 439 predicate | **79** | 79 |
| unreachable | **76** | 76 |
| unreachable matched instances by kind | act 66 · value 9 · situation 3 · entity 2 | same |
| all unreachable matched instances patient-free | yes | yes |
| clause text: third_party / user-dev only / none | **17 / 29 / 30** | 17 / 29 / 30 |

### 2.2 What the 17 are before any judgement

Three structural facts, all mechanical, all reducing the ceiling before a single judgement
call is made:

1. **The 17 are 16 distinct targets.** m0353 appears twice — once under `helpfulness`, once
   under `avoiding-over-and-under-caution` — same clause, same atom instance
   (`explain_reasoning`). One attribution serves both rows.
2. **3 of 17 carry a `value` atom, not an act** (m0019 `human_safety_rights`, m0050
   `user_developer_empowerment`, m0482 `deep_understanding`). D5b proposes admitting
   patient-free **acts**. Those three are outside the proposal entirely — reaching them
   needs a *different* widening (values), which nobody has proposed and which has no count.
3. **Only 3 of 17 would be admitted by the act keyword screen at all** — m0209 and m0214
   (`shouldnot_facilitate_critical_harms`) and m0226 (`should_provide_public_information`).
   The other 14 carry atoms with no CORE/EXT keyword in that **instance's** name+gloss
   (the predicate is per instance, so `should_provide_neutral_factual_information` is
   admitted in m0210 but not in m0327, whose gloss reads *"gives objective context without
   taking a position"*)
   (`provide_clear_answer`, `explain_reasoning`, `should_explain_reasoning`,
   `must_pause_for_approval`, `shouldnot_generate_disallowed_content`, …). Under the
   *same predicate the situations band uses*, the 17 is already a **3** before anyone judges
   a noun phrase. To reach the other 14 you must widen to *all 433* patient-free acts — a
   different, much larger, and separately unaudited proposal.

That last point is the single most consequential number in this document, and it is
purely mechanical.

### 2.3 Per-case table — ⚠️ DESIGNER ESTIMATE, NOT SEAT VERDICTS

Ordered by clause id. "adm?" = admitted by the act keyword screen (§1.1 A-trim).
Locators are `model_spec@2025-12-18 > …`; the leading document token is dropped for width.

| # | clause | locator | behaviour row | matched atom (kind, adm?) | third-party phrase(s), verbatim | designer judgement |
|---|---|---|---|---|---|---|
| 1 | **m0019** | Overview > Red-line principles > ¶7 | harm-avoidance | `human_safety_rights` (value, no) | "**People** should have transparency…", "…implicate **people's** fundamental **human** rights" | **PLAUSIBLE bearer, ZERO yield.** The atom's gloss is *"protecting people from harm and respecting their fundamental rights"* and the clause names people at large — an m0018-shaped comprehensive generic. But (a) it is a `value` atom, outside D5b's act proposal, and (b) the row's query is **harm-avoidance-to-third-parties**, which declares patient `third_party`: a third-party attribution here *overlaps* the query, giving full credit and **leaving the FP exactly where it is**. Naming the bearer correctly does not fix this case. |
| 2 | **m0050** | Overview > Instructions and levels of authority > ¶21 | helpfulness | `user_developer_empowerment` (value, no) | "…makes model behavior less predictable for **people**" | **INCIDENTAL.** The gloss names the bearers explicitly — *"what users and developers can accomplish"*. "people" is the audience of predictability in an aside about why defaults exist. Also a value atom. |
| 3 | **m0136** | The chain of command > Act within an agreed-upon scope of autonomy > ¶14 | caution | `must_pause_for_approval` (act, no) | "…all sub-agents and **third parties** (and their sub-agents in turn) operate under the same scope" | **INCIDENTAL — capacity misattribution**, the failure §1.3 step 2 names by that phrase. The third parties here are *delegates bound by* the scope — actors, not the party a harm falls on. The atom is a shutdown-timer duty. A verbatim "third parties" span exists, which is exactly why the scan counts it and the seat must not. |
| 4 | **m0205** | Stay in bounds > … > Never generate sexual content involving minors > ¶1 | caution | `shouldnot_generate_disallowed_content` (act, no) | "Sexual content involving **minors** is prohibited…" | **BORDERLINE, likely `unclear`.** The clause's protection unmistakably runs to minors. But this atom's gloss — *"avoids producing content that the specification prohibits"* — describes a compliance duty, not a harm falling on a party, so procedure step 1 (*"if the atom … does not describe a harm/protection/benefit falling on any party, answer `unclear`"*) plausibly fires first. Not keyword-admitted, so out of scope regardless. |
| 5 | **m0209** | Stay in bounds > … > Don't provide information hazards > ¶1 | caution | `shouldnot_facilitate_critical_harms` (act, **yes**) | "…activities that are illicit, could **harm people** or property, or lead to critical or large-scale harm" | **PLAUSIBLE — the strongest of the 17.** The noun phrase is the direct object of the harm verb in the clause's own sentence, and the atom's gloss is *"does not support or enable severe harmful activities through model use"*. The people harmed by CBRN facilitation are third parties on any reading. Verbatim `license_quote` available. Query is caution ({user}) ⇒ third-party attribution is disjoint ⇒ suppression ⇒ **fixes the FP**. |
| 6 | **m0214** | Stay in bounds > … > Don't provide information hazards > ¶6 | caution | `shouldnot_facilitate_critical_harms` (act, **yes**) | "…too little to reliably infect a **person**" | **PLAUSIBLE but weaker than m0209.** Same atom, an example clause (*"refusing to facilitate amplification of a biological threat"*). The only third-party span sits inside the `<user>` turn's hypothetical and grammatically describes an *inoculum quantity*, not the clause's protected party. Defensible: the person infected is precisely who the amplified agent harms, and it is the clause's only person noun. But a seat could reasonably rule this a topic mention and return `unclear`. Same fix direction as m0209. |
| 7 | **m0226** | Stay in bounds > … > Protect people's privacy > ¶1 | helpfulness | `should_provide_public_information` (act, **yes**) | "…requests for private or sensitive information about **people**" | **SPLIT — do not count.** The clause protects the people whose information it is (third parties), but this atom is the *permissive carve-out* and its gloss is one of §1.3's negations: *"provides public information **unlikely to cause harm** through disclosure"*. It is on this document's own class-1 FP list (§1.3). If the FP audit is applied, the atom leaves the population; if it is not, the seat's step 1 should still rule it `unclear`. Counting it would be counting the same defect twice. |
| 8 | **m0247** | Stay in bounds > … > Avoid hateful content directed at protected groups > ¶6 | caution | `may_provide_critical_factual_discussion` (act, no) | "…\"conversion therapy\" for gay and trans **people**" | **INCIDENTAL.** The phrase is the *topic of the user's request* inside an example. The atom permits objective critical discussion; the effect of that permission does not fall on gay and trans people as this atom's bearers — the clause's point is that critiquing a *practice* is allowed. |
| 9 | **m0327** | Seek the truth together > Don't have an agenda > Assume an objective POV > ¶4 | helpfulness | `should_provide_neutral_factual_information` (act, no) | "…fundamental **human** rights violations" | **INCIDENTAL — and a scan artifact.** `\bhuman\b` matched the *modifier* in "human rights", not a person noun phrase. The atom is answer neutrality (*"gives objective context without taking a position"*) and its sibling name `should_state_violation_wrong` is where the rights content lives. Also a class-1 FP name in §1.3. |
| 10 | **m0338** | Seek the truth together > … > Assume an objective POV > ¶15 | helpfulness | `provide_clear_answer` (act, no) | "Should tall **people** be allowed to play sports?" | **INCIDENTAL, plainly.** Answer-directness atom; the phrase is the subject of a deliberately trivial example question. |
| 11 | **m0339** | Seek the truth together > … > Assume an objective POV > ¶16 | helpfulness | `provide_clear_answer` (act, no) | "misgendering one **person**", "misgender **people**" | **INCIDENTAL.** The persons are the content of a trolley-problem prompt used to illustrate answering directly. The atom bears on answer form. |
| 12 | **m0353** | Seek the truth together > Be honest and transparent > ¶1 | helpfulness | `explain_reasoning` (act, no) | "…as **humanity** begins navigating its relationship with AI", "…operating with **people's** best interests at heart" | **INCIDENTAL to WEAK.** The clause does state a benefit running to people at large, but it belongs to the *integrity* sentence, not to `explain_reasoning` (*"makes the basis for a response or decision clear"*), whose beneficiary is the interlocutor. §1.3 step 5's "never borrow a bearer from a sibling" applies within a clause too. Likely `unclear`. |
| 13 | **m0353** | *(same clause, same atom)* | caution | `explain_reasoning` (act, no) | *(same)* | **DUPLICATE of #12.** Two census rows, one attribution target. The 17 is 16 distinct targets. |
| 14 | **m0482** | Use appropriate style > Be responsible > ¶2 | helpfulness | `deep_understanding` (value, no) | "its place in **society**", "relationship with **people**", "first-hand **human** experience" | **INCIDENTAL.** An answer-quality value about the model's self-situating; the nouns describe the model's context, not a party bearing a harm. Also a value atom, outside the proposal. |
| 15 | **m0498** | Use appropriate style > Be clear and direct > ¶8 | helpfulness | `should_explain_reasoning` (act, no) | "the population of Chicago is around 3 million **people**" | **INCIDENTAL — the clearest false hit in the set.** A Fermi estimate of piano tuners. No harm, no protection, no party. |
| 16 | **m0563** | Use appropriate style > Adapt to the user's modality > Adapt length and structure > ¶3 | helpfulness | `should_provide_clear_answer` (act, no) | "**Humans** and chimpanzees share about 98-99% of their DNA", "**human** brain size" | **INCIDENTAL.** Topic of a voice-mode length example. |
| 17 | **m0589** | Under-18 Principles > Prioritize safety for teens > ¶13 | caution | `should_prioritize_safety` (act, no) | "…must decline **teen** requests" | **INCIDENTAL — the m0276 trap, exactly.** "teen" maps `third_party` by the pinned §1.4 table *by default*, but note (i) says: *"where the clause contextually identifies them as the conversation's user, the seat maps `user`"*. This clause does exactly that, twice: *"acknowledge the **user's** concern"* and *"If the **user** appears to be in immediate danger"*. The teen **is** the user; the safety protection runs to the user. A scan reads third_party; the bearer is the user. |

### 2.4 Tally

| judgement | rows | distinct targets |
|---|---:|---:|
| plausible AND act AND keyword-admitted AND fix-direction | **2** (m0209, m0214) | 2 |
| plausible but zero/negative yield (wrong query direction, or wrong atom kind) | 1 (m0019) | 1 |
| borderline, likely `unclear`; not keyword-admitted | 1 (m0205) | 1 |
| split — plausible clause, but the atom is a class-1 FP | 1 (m0226) | 1 |
| incidental mention (topic, capacity, sibling-borrowed, or scan artifact) | 11 | 10 (m0353 ×2) |
| duplicate row | 1 | — |
| **total** | **17** | **16** |

Twelve of the seventeen — 71% — are the m0276 shape or worse: a party noun present in the
text with no relationship to the atom's bearer. Six are the *topic of an example dialogue*
(m0214 partly, m0247, m0338, m0339, m0498, m0563), which is a systematic hazard the design's
scan has no defense against: example clauses quote user prompts, and user prompts are about
people.

---

## 3. What this means for the ≤ 17 ceiling

**Best estimate of the real yield: 2 census cases, range 1–4.**

The 17 shrinks in four independent mechanical steps before judgement even starts —
duplicate (−1), value atoms outside the proposal (−3), atoms the shared keyword predicate
does not admit (−11 of the remainder) — leaving **3**; and of those 3, m0226's atom is on
this document's own false-positive list, leaving **2**: m0209 and m0214, both
`shouldnot_facilitate_critical_harms`, both `avoiding-over-and-under-caution` FPs where a
`third_party` attribution is disjoint from the query's declared `{user}` and therefore
suppresses.

**Uncertainty, and its direction:**

- **Upward, to ~4:** if a seat licenses m0226 anyway (its clause text names people plainly)
  and rules m0205 resolved rather than `unclear`. Both require the seat to answer step 1
  "yes" on an atom whose gloss negates the harm.
- **Upward, to ~14, only under a different proposal:** admitting *all 433* patient-free acts
  without the keyword screen. That is not "the same keyword predicate" D5b §5 asks to
  apply, it has never been audited, and §1.3 shows the audit would be heavy (39–63% FP rate
  on the *filtered* subset, which is the easy end).
- **Downward, to 0–1:** m0214's only third-party span is inside a `<user>` turn describing
  an inoculum quantity; a strict seat rules it a topic mention. And **suppression is not
  guaranteed by attribution** — §5.3's cap fires only when *every* resolved atom on the
  clause is disjoint, and I have not simulated pricing. Both m0209 and m0214 have a
  single-name matched set, so the condition is reachable, but "the seat resolves
  third_party" and "the census case flips" are different events. **A reviewer should check
  this one** before treating 2 as banked.
- **One name carries everything.** Both surviving cases are the same atom name. This is
  structurally the same finding as `D5_WORKED_EXAMPLES.md` §5's 746 analysis: a count that
  looked like a population-level gain resolves, once named, into one or two atom names.

**What this does to D5b's arguments** (offered as input to the ruling, not as the ruling):

- §4's *scale* argument is **wrong and should not be used**: the filtered addition is 41
  instances / 38 clauses, not 433.
- §3's *"worth up to 17"* argument is **not supported**: worth ~2 under the same predicate
  the situations band uses, ~4 optimistically.
- §4's *suppression-direction* argument is **strengthened**: 20 of the act band's 38 clauses
  are currently atom-matched by a declared behaviour, so a widening acts on live clauses;
  and 16–26 of the 41 instances are keyword false positives that a seat must catch, on a
  predicate measurably less reliable for acts than for situations.
- The recommendation D5b §6 already makes — **rule the exclusion explicitly, carry the
  extension as named follow-up** — survives these counts intact and is better supported by
  them than by the ≤ 17 ceiling it was written against. The honest ground has changed from
  "bounded at 17" to "**about 2, and one atom name**".

**Not decided here.** Whether the ruling should be "situations-only for this cycle" or
something else is the designer's call; this document supplies the two counts §5 asked for
and nothing more.

---

## Appendix A — reproduction

Deterministic, read-only, panel-blind on Task 1, census-reading on Task 2, zero API spend.
Run from `semi-formal-experiment/` with `.venv/bin/python`.

**Predicates, exactly as used** (re-implemented from
`ATTRIBUTION_POPULATION_ENUMERATION.md` §2.3–§2.5, not taken from the document's numbers —
the situations-side pin `A=368, B-wide=378, B-core=59, B-ext=77, B-trim=71` is asserted
before the act numbers are computed):

```
CORE / EXT / FP_NAMES   as ATTRIBUTION_POPULATION_ENUMERATION.md §2.4–§2.5
patient_free(a)        := len(grammar.parse_name(a.name).principals) < 2
keyword(a, S)          := any(stem in (a.name + " " + a.gloss).lower() for stem in S)

A-core(a)  := patient_free(a) AND a.kind == "act" AND keyword(a, CORE)
A-ext(a)   := patient_free(a) AND a.kind == "act" AND keyword(a, CORE|EXT)
A-trim(a)  := A-ext(a) AND a.name not in FP_NAMES

in439(a)   := len(principals) >= 2
              OR (patient_free(a) AND a.kind == "situation"
                  AND keyword(a, CORE|EXT) AND a.name not in FP_NAMES)
```

⚠️ **Dechaining.** The v1.2 join matches on DECHAINED names: a matched name
`should_deescalate_extremist_involvement` is the annotation instance
`should_deescalate_extremist_involvement__model_user`. Every lookup below splits on
`grammar.PRINCIPAL_SEP` on **both** sides. An analysis that skips this reports zero reach
for the chained population.

### A.1 Task 1 — act population and reach

```python
import json, os, sys
from collections import Counter, defaultdict
os.chdir("semi-formal-experiment"); sys.path.insert(0, ".")
import grammar, containment, snapshot

atoms = json.load(open("annotations_ext_v1_merged.json"))["atoms"]
CORE = ["harm","hurt","injur","suffer","kill","death","violence","violent","abuse",
        "weapon","terror","radicaliz","extremis","victim","risk","danger","threat",
        "unsafe","exploit","manipulat","coerci","intimidat","harass","fraud","decei",
        "decept","discriminat","violat","disempower","oppress","benefit","wellbeing",
        "well-being","welfare","flourish"]
EXT = CORE + ["distress","sexual","illicit","private","mania","manic","drug",
              "dissatisfaction","misrepresent"]
FP_NAMES = {"positive_user_intent","instructions_intended_low_risk",
            "scope_inadequate_for_task","user_prosocial_preferences"}

def chain(a):
    p = grammar.parse_name(a["name"]); assert not p["error"], p
    return p["principals"]
def hit(a, stems):
    t = (a["name"] + " " + a["gloss"]).lower()
    return sorted({k for k in stems if k in t})

pf = [a for a in atoms if len(chain(a)) < 2]
pf_sit = [a for a in pf if a["kind"] == "situation"]
assert (len([a for a in atoms if len(chain(a)) >= 2]), len(pf_sit)) == (368, 378)
assert len([a for a in pf_sit if hit(a, CORE)]) == 59
assert len([a for a in pf_sit if hit(a, EXT)]) == 77
assert len([a for a in pf_sit if hit(a, EXT) and a["name"] not in FP_NAMES]) == 71

pf_act        = [a for a in pf if a["kind"] == "act"]                       # 433
act_core      = [a for a in pf_act if hit(a, CORE)]                         # 36
act_ext       = [a for a in pf_act if hit(a, EXT)]                          # 41
act_core_trim = [a for a in act_core if a["name"] not in FP_NAMES]          # 36
act_trim      = [a for a in act_ext  if a["name"] not in FP_NAMES]          # 41
for label, xs in [("pf acts", pf_act), ("A-core", act_core),
                  ("A-core-FP", act_core_trim), ("A-ext", act_ext),
                  ("A-trim", act_trim)]:
    print("%-12s inst=%4d names=%3d clauses=%3d" % (
        label, len(xs), len({a["name"] for a in xs}),
        len({a["clause_id"] for a in xs})))

idx = containment.ContainmentIndex.from_files(
    clauses_path="modelspec_clauses.json",
    annotations_path="annotations_ext_v1_merged.json",
    edges=containment.load_edges("overlay_empty.json"))
behs = snapshot.load_behaviours("behavior_atoms_audit_v1.json", "behaviours_query.json")
cuts = snapshot.load_frozen_thresholds("thresholds_frozen.json")
SEP  = grammar.PRINCIPAL_SEP
pred = {s: idx.predict(b, cuts[s]) for s, b in behs.items()}

def reach(label, pop):
    cl, pa, ma = {a["clause_id"] for a in pop}, set(), set()
    for s, b in behs.items():
        p = pred[s] & cl; pa |= p; m = set()
        for cid in cl:
            names = {x["name"].split(SEP)[0]
                     for x in (idx.explain(b, cid).get("matched_atoms") or [])}
            if {a["name"].split(SEP)[0] for a in pop
                if a["clause_id"] == cid} & names:
                m.add(cid)
        ma |= m
        print("   %-34s predicted=%3d atom-matched=%3d" % (s, len(p), len(m)))
    print("%s: clauses=%d predicted_any=%d matched_any=%d"
          % (label, len(cl), len(pa), len(ma)))

reach("A-trim", act_trim)          # 38 / 27 / 20
reach("A-core-FP", act_core_trim)  # 34 / 26 / 19
```

The §1.3 audit bands are the same call with the class-1 / class-2 name sets removed:

```python
NEG = {"should_follow_intended_instructions",
       "should_provide_neutral_factual_information",
       "should_provide_public_information", "may_provide_political_content",
       "should_preserve_truthfulness"}                                   # 16 instances
WORDSENSE = {"assess_risk_and_skill", "risk_mitigation", "monitor_policy_violations",
             "may_provide_general_drug_information", "creative_risk_taking",
             "should_weigh_assumption_costs", "may_discuss_minor_sexual_content",
             "shouldnot_disclose_privileged_content",
             "shouldnot_enable_privileged_access",
             "shouldnot_share_privileged_data"}                          # 10 instances
reach("minus NEG",      [a for a in act_trim if a["name"] not in NEG])
reach("minus NEG+WS",   [a for a in act_trim
                         if a["name"] not in NEG | WORDSENSE])
# -> 25 inst / 22 clauses / 16 / 12   and   15 inst / 14 clauses / 12 / 10
```

The class assignments themselves are a **judgement over the verbatim glosses printed by**:

```python
for a in sorted(act_trim, key=lambda a: (a["name"], a["clause_id"])):
    print("%-8s %-46s [%s] :: %s" % (a["clause_id"], a["name"],
                                     ",".join(hit(a, EXT)), a["gloss"]))
```

### A.2 Task 2 — the 17

```python
import json, os, re, sys
from collections import Counter, defaultdict
os.chdir("semi-formal-experiment"); sys.path.insert(0, ".")
import grammar
# ... CORE / EXT / FP_NAMES / chain() / hit() as in A.1 ...

atoms   = json.load(open("annotations_ext_v1_merged.json"))["atoms"]
clauses = {c["id"]: c for c in
           json.load(open("modelspec_clauses.json"))["clauses"]}
SEP = grammar.PRINCIPAL_SEP

def in439(a):
    return (len(chain(a)) >= 2 or
            (a["kind"] == "situation" and hit(a, EXT)
             and a["name"] not in FP_NAMES))
def act_candidate(a):                      # the D5b extension predicate
    return (len(chain(a)) < 2 and a["kind"] == "act"
            and hit(a, EXT) and a["name"] not in FP_NAMES)

bykey = defaultdict(list)                  # DECHAINED key — see the warning above
for a in atoms:
    bykey[(a["clause_id"], a["name"].split(SEP)[0])].append(a)

DOSS = "audit_dossiers/ext_v1_merged__audit_v1"
census = [r for r in json.load(open(f"{DOSS}/verdicts_merged.json"))
          if r.get("cause") == "fp_promiscuous_atom"]          # 155
rows = []
for r in census:
    d   = json.load(open(f"{DOSS}/{r['dossier_id']}.json"))
    cid = d["mapped_clauses"][0]["clause_id"]                  # highest scoring
    names = d.get("discriminators", {}).get("exact_name_intersection") or []
    insts = [a for n in names
             for a in bykey.get((cid, n.split(SEP)[0]), [])]
    rows.append((r, cid, names, insts))

unreach = [x for x in rows if not any(in439(a) for a in x[3])]  # 76
print(Counter(a["kind"] for x in unreach for a in x[3]))
# Counter({'act': 66, 'value': 9, 'situation': 3, 'entity': 2})

NP_TABLE = [ ... exactly S3B_ATTRIBUTION_TASK_DESIGN.md Appendix A's pinned table ... ]
TABLE = [(re.compile(rx, re.I), pr) for rx, pr in NP_TABLE]
def np_hits(text):
    found = defaultdict(list)
    for rx, pr in TABLE:
        for m in rx.finditer(text):
            found[pr].append(m.group(0))
    return found

tp = [(x, np_hits(clauses[x[1]]["quote"])) for x in unreach]
tp = [(x, h) for x, h in tp if h.get("third_party")]            # 17
for x, h in sorted(tp, key=lambda t: t[0][1]):
    r, cid, names, insts = x
    print(cid, clauses[cid].get("locator"), r["dossier_id"], names,
          sorted(set(h["third_party"])),
          [(a["kind"], act_candidate(a), a["gloss"]) for a in insts])
```

Yields `third_party=17 · user/developer-only=29 · none=30` over the 76, matching
`D5_WORKED_EXAMPLES.md` §6, and `act_candidate` is True for exactly 3 of the 17 (m0209,
m0214, m0226).

**Sources:** `annotations_ext_v1_merged.json`, `modelspec_clauses.json`, `grammar.py`,
`containment.py` + `overlay_empty.json`, `behavior_atoms_audit_v1.json`,
`behaviours_query.json`, `thresholds_frozen.json`,
`audit_dossiers/ext_v1_merged__audit_v1/` (census — attention only, never a ruling's
primary ground), pinned NP table from `S3B_ATTRIBUTION_TASK_DESIGN.md` §1.4.

— End. No attribution performed; no ruling made; nothing implemented.
