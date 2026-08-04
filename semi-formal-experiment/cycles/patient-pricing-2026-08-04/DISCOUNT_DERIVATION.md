# DISCOUNT DERIVATION — re-arguing PATIENT_MISMATCH_DISCOUNT from golden patient-contrast cases

Seat: DISCOUNT-DERIVATION, patient-pricing-2026-08-04. Outcome-blind: this argument was
built from `patient.py`, `golden_translations.json`, `modelspec_clauses.json`,
`annotations_ext_v1_merged.json`, and `grammar.py` only. No cycle output, snapshot, diff,
census, panel, or flip-set file was opened. Nothing below rests on which clauses flip at
any d; corpus statistics (idf, cosine scales) were computed from the artifact directly.

## 0. The mechanics the derivation prices against (from patient.py + relevance.py formula
   as restated in patient.py's own contract)

* A credited atom match contributes, in raw-score units,
  `0.6 · f · factor`, where `f = idf(name)/atom_norm ∈ [0.62, 1.0]` on the merged
  artifact (N = 593; idf = log(1 + N/(1+df)); max df = 17, so nothing is stopworded and
  the per-match unit is nearly flat: **one atom match ≈ 0.37–0.60 raw**).
* `factor = d` iff (that clause atom's recorded patients are nonempty and disjoint from
  the declared set P) OR (the clause is tainted: ≥1 patient-bearing chain, none
  consistent). Single application, never d². One consistent chain defeats taint.
  Under taint, **patient-free atoms on the clause are discounted too**.
* The atom channel is a SUM of priced credits; local = 1.0·lex + 0.6·atom; section adds
  0.45·mean(top-3 local of section-mates) — a section-leading clause echoes ≈ +15% of its
  own local back. rank() normalizes by the corpus max raw; the default audit surface sits
  at normalized 0.18.
* Empirical lexical scales (computed from the clause vectors, 4000 random pairs):
  incidental overlap median 0.018, **p90 ≈ 0.06** ("noise line" ν), p99 0.155;
  genuinely-related clause pairs (m0276–m0291, m0276–m0278, m0356–m0364, m0242–m0244)
  sit at **0.14–0.19** ("signal line" λ). So: one consistent atom match outweighs a real
  lexical signal by ×2–4, and the question "does a discounted credit still mean anything"
  has a natural yardstick: above ν it is score-real; at or below ν it prices like a stray
  word overlap.

## 1. Contrast-case table

Judgments are FROM THE DOCUMENT: clause text + the golden chain convention
("a chain is written ONLY where the clause names both an actor and a party the act falls
on" — golden_translations.json, principal_chain_convention).

| # | clause_id | chain patient(s) (merged artifact) | hypothetical query patient P | judgment | clause-text reason |
|---|-----------|-----------------------------------|------------------------------|----------|--------------------|
| 1 | m0276 | user (×3: `mustnot_enable_self_harm`, `should_provide_supportive_response`, `must_advise_immediate_help`; plus patient-free `imminent_bodily_harm`) | {third_party} | **(a)** full suppression | Every harm-bearing noun is the user: "must not encourage or enable **self**-harm", "convey that **the user** is not alone", "if **the user** is in imminent danger". Self-harm is definitionally harm to the speaker; nothing in the clause generalizes to harming others. The document gives an auditor of a harm-to-third-parties behaviour no reason to surface this clause. (Canonical case.) |
| 2 | m0242 | third_party (`mustnot_generate_disallowed_content`) | {user} | **(a)** full suppression | Operative test is group-targeting in every phrase: "targeting **protected groups** (race, religion, …)", "slurs, insults, … demeans or dehumanizes" scoped by that target. User-directed abuse is the province of m0248 ("toward individuals"), and this very section's example clauses (m0244–m0246) carry `__model_user` chains (`must_refuse_request__model_user`), so a user-patient query is served by section-mates, not by this clause's atom credit. (Reverse canonical.) |
| 3 | m0356 | third_party (×2: `shouldnot_lie_by_commission`, `may_lie_by_omission`; plus patient-free `express_uncertainty`) | {user} | **(a)** full suppression | The clause opens with its own patient scoping: "**When interacting with third parties** on behalf of the user…". The user appears only as beneficiary and as the party who may instruct — never as the party lied to. Lying **to the user** lives in section-mates of "Do not lie" (14 peers, incl. m0364 `mustnot_lie__model_user`). The document itself draws the patient boundary this query falls outside. |
| 4 | m0364 | user (`mustnot_lie`) | {third_party} | **(a)** full suppression | The example is wholly user-directed: the user asks "Are you allowed to use the word 'delve'?" and the BAD answer is the model lying **to the user**. Deceiving third parties is exactly m0356's territory (same section). |
| 5 | m0248 | third_party (`shouldnot_engage_abuse`) | {user} | **(b)** subordinate but real | The act-noun generalizes past the recorded patient: "abuse, harassment, or negativity toward **individuals**" — the interlocutor is an individual; nothing in the text excludes the user. The chain (golden-sanctioned: golden m0248 also writes `__model_third_party`, gloss "toward a person") is a narrower reading than the text supports. An auditor of a model-abuses-the-user behaviour should still meet this clause in the trail; it just should not outscore the user-chained material. |
| 6 | m0592 | mixed: `shouldnot_provide_harmful_advice` → user, `involve_trusted_adults` → third_party | {user} | **(b)** on the mismatched atom; clause itself survives | "I can't give guidance on … challenges — they can cause [harm to the asking teen] … A parent … might have good advice." Harmful advice falls on the user (consistent, factor 1.0, taint defeated — the m0248 guard); involving trusted adults is an act toward third parties on the user's behalf, still auditor-relevant context for a user-harm behaviour, so its credit should survive subordinately, not vanish. |
| 7 | m0276 | user (as in #1) | {user} | **(c)** untouched (control) | Same clause, right patient: a self-harm behaviour declaring the user is exactly whom every chain names. Factor must be 1.0 — and mechanically is (`consistent`, bit-identical). |
| 8 | m0242 | third_party (as in #2) | {third_party} | **(c)** untouched (control) | Hateful-content behaviour declaring third parties: chain consistent, factor 1.0, taint defeated. |

Six patient-contrast cases (#1–#6) spanning full suppression (×4), partial relevance
(×2, one generalizing-act, one mixed-patient/guard), plus two no-discount controls.

## 2. Arithmetic per case

Notation: matched mismatched idf mass F = Σf over the atoms a compatible-stem query can
credit on the clause; discounted atom raw = 0.6·F·d; ν = 0.06 (incidental-overlap p90),
λ ≈ 0.19 (related-pair signal). Taint applies in #1–#5 (all patient-bearing chains
mismatched); in #6 the guard defeats taint and only the one atom is discounted.

* **#1 m0276 (a).** f = .929, .688, .929, plus tainted patient-free .879 → worst-case
  F = 3.43, base atom raw = 2.06. "Match must not survive" ⇒ 2.06·d ≤ ν ⇒ **d ≤ 0.029**.
  (Laxer, rank-based reading: with self-section echo ×1.15 and a one-consistent-atom
  competitor normalizer M ≈ 0.85, `1.15·2.06·d/M ≤ 0.18` ⇒ d ≤ 0.065; a realistic
  two-atom match F ≈ 1.6 gives d ≤ 0.06–0.11. Every reading lands at or below ≈ 0.1,
  and the strict one at ≈ 0.03.)
* **#2 m0242 (a).** Single atom f = .879 → 0.527·d ≤ ν ⇒ **d ≤ 0.114**.
* **#3 m0356 (a).** Worst case F = 1.0 + 1.0 + .662 (tainted patient-free) = 2.66 →
  1.60·d ≤ ν ⇒ **d ≤ 0.038**; a single-stem query (F = 1.0) gives d ≤ 0.10.
* **#4 m0364 (a).** Single atom f = .840 → 0.504·d ≤ ν ⇒ **d ≤ 0.119**.
* **#5 m0248 (b).** Single atom f = .929, credit 0.557·d. Score-real (above stray-word
  level): 0.557·d ≥ ν ⇒ **d ≥ 0.108**. Not score-driving (below a genuine signal):
  0.557·d ≤ λ ⇒ d ≤ 0.34.
* **#6 m0592 (b, guarded).** Consistent atom (.929) full credit carries the clause;
  mismatched `involve_trusted_adults` (.879) credit 0.527·d. Subordination is automatic
  for any d < 1; score-real visibility gives the same soft floor form, d ≥ ν/0.527 ≈ 0.11.
* **#7, #8 (c).** Factor is 1.0 by the consistent branch; no constraint on d. They
  constrain the MECHANISM (consistency and the taint guard must price bit-identically),
  which patient.py already guarantees.

## 3. Derived interval

Ceilings (a): 0.029 (#1), 0.038 (#3), 0.114 (#2), 0.119 (#4).
Floors (b): 0.108 (#5), ≈0.11 soft (#6). Upper bound from (b)-subordination: 0.34.
Independent relational bound from the pricing mechanics' own comparator: a recorded wrong
patient is stronger counter-evidence than an unstable kind ⇒ d < kind_mismatch_discount
= 0.4 (consistent with everything above; never binding).

**Intersection: [0.108, 0.029] — EMPTY.** The conflict is #1/#3 against #5/#6.

Two findings, both about the mechanism rather than the constant:

* **F-linearity of taint.** Taint applies d per credited match, so a uniformly
  mismatched clause's residual atom mass is 0.6·F·d — linear in how much of it the query
  matches. The clauses the document most wants suppressed (densely decorated, every
  chain wrong: m0276, m0356) are precisely the ones that retain the most absolute mass.
  Suppressing them below noise needs d ≤ ν/(0.6F) ≈ 0.03–0.04, while keeping a
  single-chain generalizing clause score-real needs d ≥ ν/(0.6f) ≈ 0.11. Jointly
  satisfiable only when F ≈ f, i.e. never for dense clauses. A single multiplicative
  per-match d cannot express the golden judgments. This is also why the provisional
  plateau assumption failed: the golden constraints do not carve out an interval, they
  pinch to a knife-edge near 0.1 and cross.
* **The (a)/(b) separator is textual and invisible to the layer.** #4 (m0364, user
  chain, f = .84) and #5 (m0248, third-party chain, f = .93) are mechanically almost
  identical — one mismatched chain, tainted, similar idf — yet golden judgment demands
  suppression for one and survival for the other. What separates them is whether the
  clause's patient-nouns saturate the text ("the user is not alone") or the act-noun
  generalizes ("toward individuals"). That information lives in the clause TEXT (and
  leaks into the lexical channel), not in the chain metadata the pricing reads. No value
  of d can strictly separate them; d ≈ 0.1 prices both AT the noise line, which is the
  best a single constant can do.

## 4. Recommendation

**Mechanism amendment (primary): under clause taint, cap the clause's surviving atom
mass at ONE discounted credit** — tainted atom channel = d · max(base credits)/atom_norm
instead of d · Σ (per-atom mismatch on untainted/mixed clauses stays per-match; the
guard, single-application, and never-outprice invariants are untouched, since the capped
sum is ≤ the current d·Σ, all factors remain ≤ 1, and I1 is unaffected because the path
is only entered with nonempty P). Rationale: uniform mismatch attestation is the
strongest patient evidence a clause can carry; more mismatched chains should mean MORE
suppression, not linearly more residual. Under the amendment the (a) ceilings become
d ≤ ν/(0.6·f_max) ≈ 0.10–0.12 for all four (a) cases and the constraint set collapses to
the degenerate interval **d ≈ 0.10–0.11** against the (b) floor 0.108.

**The constant: d = 0.10.** Tie-break rule, stated: the interval is degenerate (amended)
or empty (unamended), so choose the value that equalizes the two binding golden
pressures — the largest (a)-single-atom ceiling family (0.114/0.119) and the (b) floor
(0.108) meet at ≈ 0.11; the canonical one-decimal value at that point is 0.1. At d = 0.1
a wrong-patient match prices at ≈ the incidental-overlap line: gone as a score driver,
present in the explain trail with an exact priced_credit.

If the mechanism is NOT amended, the honest single-constant compromise is the log-midpoint
of the conflict (√(0.029·0.108) ≈ 0.056 → 0.05), which suppresses the canonical dense
case fully but extinguishes judgment (b); 0.1 instead honors (b) and the single-atom (a)
cases while leaving dense tainted clauses (#1, #3) a residual of ≈ 0.21 raw — above noise,
below one honest atom match. I recommend 0.1 over 0.05 because (b) is a golden judgment
of equal standing and the dense-case residual is the amendment's job to fix, not the
constant's.

**Against the incumbent 0.25, on golden grounds alone:** at d = 0.25 the canonical case's
residual is 0.6·3.43·0.25 ≈ 0.51 raw — within the range of a single fully consistent
rare-atom match (0.37–0.60). A clause whose every recorded chain says "wrong patient"
would price like a right-patient single-match clause. That contradicts golden judgment
(a) on the canonical case directly; 0.25 is not in any interval this derivation can
produce, independent of operationalization choices.

— frozen artifact; derivation inputs and arithmetic as above.
