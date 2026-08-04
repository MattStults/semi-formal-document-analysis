# S3b REDESIGN — beneficiary-aware patient pricing (DRAFT for adversarial review)

Status: **DRAFT — design only, nothing implemented.** This document is the written,
reviewed design the S3 revert obliges before any re-attempt (HANDOFF 2026-08-04 LATE:
"It needs a written, reviewed design first — do not re-attempt by tuning constants").
It supersedes the S3 mechanism (`patient.py` as shipped at `091619c`, REVERTED).
Author: session coordinator (Qwen Code), 2026-08-04. Review seat: **not yet run** —
this draft must pass a clean-context adversarial review before OPEN.

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
   the remedy is the derivation's own §1.4/Q6: **re-derive blind** from golden
   patient-contrast cases — never re-tie-break after seeing which clause crosses
   (ruled explicitly at the m0355 knife-edge).
2. **The taint cap** (F-linearity fix): under clause taint the surviving atom mass is
   ONE discounted credit (`d · max(base credits)/atom_norm`), never `d · Σ`. Dense
   uniformly-wrong-patient clauses must not retain residual mass proportional to match
   count. The cap itself is not implicated in any of the four regressions.
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
* **A-structural (no re-annotation, partial).** Do not let clause taint discount a
  MATCHED patient-free atom whose kind is `situation` when every patient-bearing atom
  on the clause is an `act` whose agent is the model (a remedial/responsive act). I.e.
  a remedial act addressed to the user cannot taint the harm-situation it responds to.
  Cheap and mechanical. Risk: under-suppresses m0276-like cases where the user-directed
  atom genuinely bears the harm; needs the m0276/m0290 controls pinned to catch this.
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

**Candidate fixes.** A-structural does NOT cover this (the act atom IS patient-bearing
and genuinely mismatches `third_party`). Only **A-attribution** covers it: attribute the
protection's beneficiary (third parties) rather than the act's grammatical recipient
(the user). This is the sub-defect that most clearly forces beneficiary attribution.

### 4C. Generic-noun patients over-scope (m0018)

**Evidence.** m0018: "People should have easy access to trustworthy safety-critical
information…" is annotated `third_party` (the generic noun "People"), but a helpfulness
query declares `[user, developer]`. Adjudication (regression, high): "This is a core
statement of what helpfulness means." decision.json: "'people' as written comprehends
the users and developers the model works with rather than excluding them."

**The error.** A GENERIC-noun patient ("people", "everyone") is treated as excluding the
query's principals, when it in fact comprehends them.

**Candidate fixes.**
* **C-generic flag.** Attribute, per patient-bearing atom, whether its patient is GENERIC
  (comprehends all principals) or SPECIFIC. A generic patient never mismatches any
  declared P (it is consistent with every P). Mechanical once attributed.
* Alternatively, a CONVENTION ruling: generic-noun clauses are annotated patient-FREE
  (absence-is-absent), since they protect no one in particular. This is cheaper but loses
  the "People" signal and needs an annotation ruling.

---

## 5. The recommended mechanism: beneficiary-aware attribution

**Recommendation (to be confirmed or overturned by review): price on the attributed
HARM-BEARER / BENEFICIARY, not the chain's grammatical recipient.** Concretely:

1. **Attribution artifact.** For each patient-bearing atom (and each patient-free
   harm-describing atom, e.g. situation atoms), a **panel-blind, document-grounded**
   attribution records `harm_bearers` — the party/parties the harm or the protection
   ultimately falls on — plus a `generic` flag (§4C) and a short verbatim
   `license_quote`, exactly in the spirit of S2's validator-checked backfill. The
   attribution reads clause text + gloss + the golden chain convention only; it never
   opens a panel artifact, a judge rating, or a gold value (same fence as S3).
2. **Two delivery options (DECISION POINT D1 — needs a designer ruling):**
   * **(a) Annotation-side backfill.** Extend the chain convention so harm-bearer is a
     first-class annotated field, shipped as a targeted backfill cycle (validator-checked,
     license-quoted, golden-reviewed) — the proven S2 machinery. Pricing stays fully
     mechanical (reads attributed harm-bearers). Cost: an annotation cycle.
   * **(b) Index-side seat.** A panel-blind seat attributes harm-bearer at index-build
     time, stored as pricing metadata. Cheaper, but puts a judgment seat in the index
     path; needs its own brief (per `briefs/` convention) and a seat-parity check.
   * **Leaning (a)** for consistency with the project's discipline (mechanical pricing,
     auditable/rechain-repairable attribution), but (b) is legitimate if the team wants
     to avoid a backfill. A reviewer must choose; do not let this default silently.
3. **Pricing rule, amended.** For a query with declared patients P, on each clause:
   * a credited match through atom `a` is **consistent** (factor 1.0) iff
     `attributed_harm_bearers(a) ∩ P ≠ ∅`, or `a` is `generic`, or `a` attributes no
     harm-bearer (patient-free-and-harm-free → absent-is-absent, factor 1.0);
   * **mismatched** (factor d) iff the attributed harm-bearers are non-empty, specific,
     and disjoint from P;
   * **clause taint** (with the existing cap) applies only when every harm-bearing atom
     on the clause attributes harm-bearers disjoint from P. A remedial ACT atom whose
     attributed beneficiary ∈ P, or whose attributed harm-bearer is the situation's
     victim, does NOT taint a sibling harm-situation atom. **This is the single rule
     change that fixes 4A and 4B together.**
4. **No cross-sibling taint in example passages (belt-and-braces).** Even before
   attribution lands, the structural guard of §4A-A-structural should be added so a
   matched patient-free situation atom is never discounted solely because a sibling
   model-act atom is user-directed. This is independently justified by m0275/m0466/m0108
   and does not depend on D1.

**What this preserves:** m0276 and m0290 stay suppressed (their harm-bearing atoms
attribute the USER as harm-bearer, disjoint from a third-party P); d = 0.10 and the cap
are untouched; the opt-in/bit-identity invariants hold (no attribution ⇒ no declared
harm-bearers ⇒ bit-identical).

---

## 6. Invariants pre-registered for S3b

* **I1 bit-identity.** No declared patients, or no attributed harm-bearers, ⇒ bit-for-bit
  ContainmentIndex. Pinned by test, as in S3.
* **I2 monotone-downward on RAW scores.** All factors ≤ 1. Normalized-score bystander
  movement is `normalizer_drift` in the dossier, never `match_change` (S3/F3 convention).
* **No constant re-tuning.** `d` stays 0.10 unless the mechanism change breaks the
  d-plateau, in which case re-derive blind (derivation §1.4/Q6), never re-tie-break
  post-hoc. The attribution MUST NOT be fit to flip outcomes (contract invariant 9;
  labels direct ATTENTION, never TRUTH).
* **Panel-blind.** Attribution and any index-side seat are panel-blind, scanned by
  `test_no_reference_leak.py`; declarations licensed by the behaviour's own prose only.
* **Never-outprice.** Any new factor path keeps every credit ≤ the un-discounted credit.

---

## 7. Falsification bar (pre-registered prediction skeleton)

The redesign's cycle must pre-register, at OPEN, a prediction whose falsifiable core is:

1. **Restore the confirmed regressions.** m0275, m0239, m0466 return to `predicted` for
   their behaviours (the exact flips S3 wrongly removed). m0108 stays `unclear`/contested
   pending its named seat-defect review (see §8) — it is NOT counted either way.
2. **Keep the canonical removals.** m0276 and m0290 remain `no_longer_predicted` for
   harm-avoidance-to-third-parties. If either re-surfaces, REVERT regardless of all else.
3. **`max_regressions: 0`** under the same two-leg split-blind adjudication S3 used
   (leg 1 official + frontier verification leg blind to leg 1; divergence → `unclear`,
   never silently resolved; P3/`ADJUDICATION_LEGS.md` precedent).
4. **No census/panel/judge/gold consultation** informs the decision; flip adjudications
   only (S3 policy, restated).

---

## 8. Open questions for the designer ruling / seat-defect review (NOT resolved here)

* **D1 (load-bearing).** Attribution delivery: annotation-side backfill (§5.2a) vs
  index-side seat (§5.2b). Needs a ruling before any build; do not let it default.
* **D2 — the m0108 scope question** (carried verbatim from S3, `ADJUDICATION_LEGS.md`):
  is "harm to the user's own organisation's accounts" harm to "those outside the
  conversation"? This is a question about the behaviour DEFINITION, not the pricing
  mechanism; it goes to seat-defect review and is NOT resolved by S3b.
* **D3 — example-kind clauses.** Should example passages get a distinct taint rule
  (their modeled response is structurally addressed to the user), or does beneficiary
  attribution handle them uniformly? The m0275/m0466/m0108 evidence is all example-kind.
* **D4 — generic-noun convention.** Attribute `generic` and keep the patient (§4C), or
  rule generic-noun clauses patient-free? Needs an annotation-convention ruling.
* **D5 — attribution population size.** S2 adjudicated 109 chain instances + backfilled
  264. S3b attribution targets harm-bearing atoms; its population must be enumerated and
  licensed the same way (verbatim quote, golden review) before pricing reads it.

---

## 9. What this document deliberately does NOT do

* It does not implement or patch `patient.py`. Nothing ships with it.
* It does not tune `d` or any weight.
* It does not open a cycle. OPEN happens only after a clean-context adversarial review
  returns non-blocking and D1–D5 have rulings.
* It does not resolve m0108, m0355-family threshold cases, or any census question; those
  stay deferred to their named venues (seat-defect review, S8 checkpoint).

— DRAFT; awaiting adversarial review.
