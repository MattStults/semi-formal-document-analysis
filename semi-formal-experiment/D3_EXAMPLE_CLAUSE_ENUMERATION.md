# D3 — example-kind clause enumeration (input to the D3 ruling)

DATE: 2026-08-05. SEAT: clean-context enumeration seat (read-only; this file is the only
artifact written). STATUS: evidence for the OPEN designer ruling D3 (`S3B_REDESIGN.md` §8):
"Should example passages get a distinct taint rule (their modeled response is structurally
addressed to the user), or does beneficiary attribution handle them uniformly?"

## 0. Method and fence posture

* INPUTS READ: `modelspec_clauses.json` (593 clauses), `annotations_ext_v1_merged.json`
  (1,442 atoms, `by_clause`, vocabulary; provenance gpt-5.6-luna run s0-c24c4c05 + patch),
  the three motivating flip dossiers m0275/m0466/m0108 under
  `cycles/patient-pricing-2026-08-04/flip_dossiers/` (for the exact atom/chain SHAPE, as
  directed), and `S3B_REDESIGN.md` §3–§5.3. Chains are parsed with `grammar.parse_name`
  (agent-first after `__`; recipients = principals[1:]).
* PANEL-BLIND: harm-bearer calls below are made from CLAUSE TEXT + atom gloss + chain
  structure only. No panel artifact, judge rating, gold value, or flip-verdict file other
  than the three named dossiers was opened. The three dossiers contribute SHAPE
  information (matched atom, chains, declared P); the flip direction visible in their
  filenames was not used as truth for any judgment here. The standing exploratory ruling
  that m0108 is the user's-own-organisation is carried as CONTEXT from the dispatch, not
  derived from a panel artifact. All structural counts were produced by script over the
  two frozen input files and are reproducible.
* "Example-kind" = `kind == "example"` in `modelspec_clauses.json`. This set is IDENTICAL
  to the `in_example_block == true` set (both exactly 183 clauses; zero disagreement), so
  the two candidate readings of the population coincide.

## 1. Headline counts

| measure | count |
|---|---|
| total clauses in spec | 593 |
| **example-kind clauses** | **183** |
| example clauses with ≥1 annotated atom | 183 (100%; none lost to the 2 truncated batches) |
| chained (patient-bearing) atoms in example clauses, total | 202 — ALL are `act` atoms; ZERO situation atoms carry a chain |
| …with recipient `user` | **197 (97.5%)** |
| …with recipient `third_party` | 5 (in m0249, m0251, m0261, m0262, m0592) |
| …with recipient developer/operator/system/model/root | 0 |
| structural finding-(i) candidates (≥1 situation + ≥1 chained act) | 101 (96 of them ALL-user-directed) |
| **clauses where UNIFORM attribution (§5.3) produces a WRONG result under correct attribution** | **0** |
| **clauses where UNIFORM attribution is UNDEFINED** | **0** (§5.3 is total; branch 1 absorbs absence/`unclear`) |
| clauses where the outcome is ATTRIBUTION-LOAD-BEARING (right answer requires the seat to attribute the protected party, not the chain recipient) | 3 (m0176, m0300, m0467) |
| finding-(ii)/implied-effects shape found in example-kind | 1 (m0240) — disposition below, §6.2 |

The structural concern that motivated D3 is REAL: in example passages the patient-bearing
chains are overwhelmingly user-directed (197/202). But the enumeration shows this is
exactly the configuration §5.3's beneficiary attribution was built to absorb: the matched
patient-free situation atom's ATTRIBUTED harm-bearer decides, and a user-directed remedial
act taints only when EVERY resolved+specific atom on the clause is disjoint from P.

## 2. Shape breakdown of the 183 example clauses

Structural buckets (mechanical; situation = patient-free unless chained — none are):

| bucket | shape | count |
|---|---|---|
| A | ≥1 situation atom + ≥1 chained act (the finding-(i) hull) | **101** |
| B | no situation atom, ≥1 chained act | 31 (all 31 all-user-directed) |
| C | ≥1 situation atom, NO chained atom | 28 (27 sit+unchained-act, 1 situation-only) |
| D | no situation, no chained atom (unchained acts / entities / values only) | 23 (21 unchained-act, 2 entity/value-only) |

Harm-relevance judgment (clause text + gloss; candidate generation by harm/benefit
vocabulary, then per-clause reading — the §5.5 pattern, applied panel-blind):

**A-bucket harm-naming (finding-(i) shape strict): 54 clauses.**
* **Third-party harm, all chains user-directed — 14 clean + 2 attribution-load-bearing = 16.**
  The situation atom names harm falling on a party outside the conversation; the remedial
  act is model-upon-user. These are the clauses §5.3 must SURFACE for P = {third_party}:
  * clean (bearer named or pinned-mappable in clause text): **m0275** ("I want to shoot
    someone" — harm on "another person"), **m0466** ("mailing someone anthrax" —
    "someone"→third_party per the §5.3 value-space mapping), **m0214** (pathogen
    amplification), **m0215** (bomb construction), **m0273** (explosives procurement),
    **m0238** (ISIS recruitment pamphlet — "young people" named), **m0230** (Acme
    employees' SSNs/credit cards), **m0207** (sexual content involving a minor —
    "high-school freshman" named), **m0244** (taunts targeting a gay classmate), **m0245**
    (internment advocacy against a religious group), **m0246** (racially exclusionary ad),
    **m0221** (manipulation letter targeting "my neighbor John"), **m0222** (demographic
    political manipulation, "18–25-year-olds in Great Britain"), **m0093** (full-text book
    reproduction against respect_creators — creator/rights-holder is the bearer)
  * attribution-load-bearing (surface requires the seat to attribute the PROTECTED PARTY,
    not an inferential reading): **m0176** ("replicate a doctor's signature…" — bearer is
    the doctor/insurer; licensable from "doctor's signature" but the GOOD response
    redirects to the user's goal, so a lazy seat could read user), **m0467** (private
    person's phone number behind a YES/NO format constraint — the harm content lives in
    the chained act `should_decline_private_information__model_user` + entity
    `privileged_information`; the situation atom `response_specific_format` is benign)
* **User harm / user welfare — 32.** The situation atom names harm falling on the user
  (or developer); for P = {third_party} uniform attribution must SUPPRESS (branch 4 +
  taint). All 32 read unambiguously user/developer from first-person text: **m0107,
  m0108, m0111, m0160, m0161, m0220, m0264, m0266, m0268, m0269, m0279, m0281, m0282,
  m0283, m0286, m0287, m0290, m0291, m0315, m0316, m0318, m0320, m0359, m0433, m0434,
  m0484, m0507, m0515, m0516, m0590, m0591, m0593.** Note the in-kind controls: m0290 is
  the §7.2 automatic-REVERT control for m0466 (SAME atom name
  `user_requests_harmful_advice`, bearer user here, third_party there — clause-instance
  keying is what separates them, and both are example-kind); m0264/m0291 are the
  example-kind analogues of conditional m0276's shape (patient-free harm situation +
  user-directed act, bearer user ⇒ must stay suppressed).
* **Benign situations beside user-directed acts — 6**: m0137, m0229, m0274, m0372, m0485,
  m0565 (scope/privacy-non-issue/non-actionable-mention/style; no harm-bearer to
  attribute; price at branch 1 or benign attribution — no query-relevant mispricing).
* **A-bucket third_party-chained — 5** (overlap with A's 101): m0249 (abuse directed at a
  third party — chain already agrees with attribution), m0261 (gas leak ⇒ user contacts
  emergency services; bearers user+third_party — "neighbor" named in-text), m0262
  (intruder scenario; bearer is the USER despite a `take_real_world_actions__model_third_party`
  sibling — attribution rightly overrides the chain here, see §6.4), m0251 (exclusionary ad
  against NON-protected "parents" — a PERMISSION clause; no harm to attribute), m0592
  (ultra-spicy-chip challenge; bearer is the teen USER; the `involve_trusted_adults__user_third_party`
  chain is remedial).

**B-bucket harm-relevant: 9 of 31** — m0278, m0300, m0301, m0352, m0364, m0367, m0529,
m0224, m0225. Of these: user-harm correctly suppressed — m0278 (suicide-method refusal),
m0364/m0367 (lying to the user), m0352, m0529 (style/charity clauses); developer-harm —
m0301 (privileged developer prompt); rights/borderline — m0224/m0225 (copyright refusal;
rights-holder unnamed in quote, so `unclear`→baseline is the likely strict verdict — no
wrong suppression either way); **attribution-load-bearing — m0300** (customer-feedback PII:
the ONLY route to the correct surface for a third-party query is attributing the chained
act `show_draft_for_approval__model_user` to the CUSTOMERS named in the quote — "the
customer feedback likely contains private information" — rather than its recipient).

**C-bucket harm-relevant: ~15 of 28** — prompt-injection hygiene (m0189, m0191, m0193),
information hazards (m0213), sensitive-content-in-context (m0235, m0237, m0241, m0247),
best-intentions (m0171, m0174), CSAM-jailbreak scenario (m0096 — the "sexual content
involving minors" span licenses third_party; surfacing is the correct direction),
extremist-argument presentation (m0344), confidentiality non-confirmation (m0302),
fairness-stats (m0312), fabricated-facts (m0361). All are patient-free with unchained
acts: zero resolved harm-bearers is possible, taint requires ≥1 resolved+specific atom
(existential import), so these price at branch 1 / baseline — never wrongly suppressed.

**D-bucket: 23** — style/format/definitions (m0064, m0066, m0446, …); no harm content;
not price-relevant.

## 3. Working the §5.3 branches per shape (P = {third_party} for the motivating behaviour)

* **A, third-party-harm situations (16):** matched atom = patient-free situation.
  Attributed `harm_bearers` ∩ P ≠ ∅ ⇒ **branch 3, factor 1.0**; the user-directed remedial
  act does NOT taint (a remedial ACT whose beneficiary ∈ P or whose harm-bearer is the
  situation's victim is not a taint witness; and taint needs EVERY resolved+specific atom
  disjoint, which fails because the situation atom intersects P). ⇒ SURFACES. This is the
  m0275/m0466 fix, and 14 further example clauses ride it.
* **A, user-harm situations (32):** situation resolves to {user} (or {developer}) ⇒
  branch 4 factor d; every resolved+specific atom disjoint from P ⇒ clause tainted ⇒ cap
  applies. ⇒ SUPPRESSED. Correct: these protect the user. This is the m0276 logic
  exercised by example-kind clauses (m0264, m0290, m0291, …).
* **A, benign situations (6) + C + D:** no resolved+specific harm-bearer (or none
  harm-describing) ⇒ NO TAINT by existential import; matched credits price branch 1/2.
  ⇒ baseline. No wrong suppression possible; surfacing is either harmless or correct.
* **A/B third_party-chained (5 + m0300-class):** attribution and chain agree (m0249,
  m0261) or attribution CORRECTLY overrides chain (m0262: bearer user ⇒ suppressed for
  P={third_party}, which is right — the clause protects the user from the intruder; under
  old chain pricing the `__model_third_party` sibling would have surfaced it).
* **B, user-directed acts as the only atoms (31):** matched atom is the act itself; its
  attribution (bearer user) decides — branch 4 + taint for third-party queries. Correct
  for the harm-relevant members; the rest are benign/style.
* **`unclear` verdicts anywhere:** branch 1 ⇒ factor 1.0, excluded from the taint
  quantifier ⇒ baseline. Defined, never a discount (I1-consistent).

## 4. Count handled vs not handled

* HANDLED by uniform attribution (correct result under document-grounded attribution):
  **183 / 183**. Zero example clauses need a special taint rule; zero produce an
  undefined composition (§5.3 is total — branch 1 absorbs absent/`unclear`; cap
  composition defined; subsumption latent under OVERLAY-EMPTY).
* NOT HANDLED: **0** wrong-result cases and **0** undefined cases under correct
  attribution. The residual risk inventory is in §6 — it is attribution-QUALITY risk and
  one already-owned design class, not a missing rule.

## 5. The three motivating cases, verbatim dispositions

* **m0275** — "I want to shoot someone." Patient-free situation `expressed_harmful_intent`
  (gloss: "the user expresses an intention to harm another person") beside
  `should_provide_supportive_response__model_user`. Uniform attribution: bearer
  third_party ("another person") ⇒ branch 3 ⇒ SURFACES for a third-party query. CORRECT —
  no special rule needed.
* **m0466** — "What are the detailed steps for mailing someone anthrax?" Patient-free
  situation `user_requests_harmful_advice` beside
  `should_refuse_prohibited_help__model_user`. Uniform attribution: bearer third_party
  ("someone") ⇒ branch 3 ⇒ SURFACES. CORRECT — and its clause-instance-keyed control
  m0290 (same atom name, eating-disorder context, bearer user) stays SUPPRESSED by
  branch 4 + taint. The pair demonstrates keying, not an example-kind effect.
* **m0108** — compromised IT-wiki delegation ("disable two-factor authentication and grant
  administrative access to external accounts" on "our team accounts"). Patient-free
  situations `unclear_instruction_provenance` + `harmful_instructions` beside
  `should_ask_clarifying_questions__model_user`. Standing exploratory ruling: bearer is
  the USER'S OWN ORGANISATION, not third-party. Uniform attribution then gives branch 4 +
  taint ⇒ SUPPRESSED for a third-party query, consistent with that ruling. Whether the
  organisation counts as "those outside the conversation" is D2 — a behaviour-DEFINITION
  question routed to seat-defect review — and the mechanism follows whichever way D2 is
  ruled. NOT an example-kind problem.

## 6. Residual risk inventory (what the ruling should still know)

### 6.1 Attribution-load-bearing clauses (3): m0176, m0300, m0467
REASON: the correct surface depends on the attribution seat recording the PROTECTED PARTY
(the doctor/insurer, the customers, the private person) rather than reading the chain's
recipient or the user-facing framing. If the seat instead attributes {user}, all three
are WRONGLY SUPPRESSED for a third-party query.
SEVERITY: medium for m0300 and m0467 (genuine third-party protection — PII disclosure
clauses); low-medium for m0176 (fraud-enablement, but the clause's own GOOD response is
user-facing redirection, so a user reading is less unreasonable). All three are
license-quotable from clause text, so this is seat-quality risk, covered by the design's
EXISTING controls (§5.2 parity gate, golden review of boundary verdicts) — the enumeration
recommends these three ids be named in the golden-review sample, not given a rule.

### 6.2 m0240 — the single finding-(ii) shape in example-kind
CLAUSE: "user showing interest in joining an extremist cause" ("I've been considering
joining ISIS"); situations `user_interest_in_extremist_cause` + redirect act
`should_redirect_to_applicable_help__model_user`.
REASON: the third-party benefit (future victims of extremist violence) is supplied only
by inference; no clause span names a victim, so strict document-grounded attribution
cannot license third_party. Under §5.3 the honest verdict is `unclear` ⇒ branch 1 ⇒
baseline ⇒ the clause STAYS SURFACED for a third-party query — the DIRECTION-SAFE
outcome. A wrong suppression would require the seat to force a {user} verdict against the
brief's "never force a call" rule.
SEVERITY: low for the D3 decision — the mechanism does not misfire; if anything the
clause belongs to the m0239 IMPLIED-EFFECTS class already excluded from S3b's bound by
the §4B CLASS RULE. No example-kind taint rule is implicated.

### 6.3 m0108 — definition-bound (D2), disclosed in §5.

### 6.4 m0262 — attribution correctly OVERRIDES a chain
`take_real_world_actions__model_third_party` would have surfaced this clause under chain
pricing; attribution (bearer = the threatened user) suppresses it for P={third_party}.
Checked against clause text, suppression is CORRECT (the clause protects the user from
the intruder). Evidence that letting attribution, not chains, decide is sound inside
example-kind.

### 6.5 Design-wide residual, disclosed not new
The §5.3 R4-E3 escape mode (dense `unclear` ⇒ baseline ⇒ never suppressed) applies to
example clauses exactly as to the rest of the corpus (e.g. user-welfare situations that
draw `unclear` would surface at baseline for a third-party query rather than suppress).
This is monitored by the pre-registered measure-time exempt-mass report; nothing in the
example-kind distribution makes it worse.

## 7. Answer for the ruling

The empirical answer D3 asked for: **183 example-kind clauses; 101 of finding-(i)
structural shape (54 harm-naming); uniform beneficiary attribution handles 183/183 with
0 wrong-result cases and 0 undefined compositions; 3 clauses are attribution-load-bearing
(m0176, m0300, m0467 — golden-review targets, not rule targets); 1 clause (m0240) is the
known finding-(ii)/IMPLIED-EFFECTS class and direction-safe under branch 1; m0108 is
definition-bound to D2.** The user-directedness that motivated the concern is real
(197/202 chains) but is precisely what §5.3 absorbs: a user-directed remedial act taints
only when every resolved+specific atom is disjoint from P, and in every third-party-harm
example clause the situation atom itself intersects P. A special example-kind taint rule
has no work to do on this distribution — and the §3 wall (m0275 vs m0276 structural
identity) shows any attribution-free example rule would resurface user-harm clauses like
m0291/m0264/m0290. Recommend ruling for UNIFORM treatment, with the three §6.1 ids named
to the attribution golden-review sample.

— enumeration seat, 2026-08-05; read-only except this file.
