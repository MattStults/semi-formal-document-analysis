# S3 flip adjudication — the two-leg record (2026-08-04)

Dossier set sha256 `726492bf72fe5e9809ca8f6b402bec3161ca8ca4ff916ab05f7a05060e59b78b`
(18 flips), echoed by BOTH verdict files. Precedent for the split-blind
second leg and its agreement accounting: the P3 drift-standing pass
(`drift_standing/DISCLOSURE.md`, run-2 + frontier tiebreak).

## The two legs

| leg | file | seat | scope | verdicts |
|---|---|---|---|---|
| 1 (official) | `flip_verdicts.json` | blinded flip-adjudicator seat | all 18 flips | 12 correct / **5 regression** / 1 unclear |
| 2 (verification) | `flip_verdicts_verification_leg.json` | frontier seat, **blind to leg 1's verdicts** (learned only WHICH flips to re-judge, never how leg 1 judged them) | the 6 contested flips | 4 regression / 2 correct |

The driver's ADJUDICATE gate consumed leg 1 (the official artifact) and
validated it clean against the dossier set; leg 2 is a verification
instrument recorded here, exactly as the drift pass recorded its tiebreak —
it never rewrites leg 1's file.

## Agreement on the 6 contested flips: 4/6

| clause | leg 1 | leg 2 | outcome |
|---|---|---|---|
| m0239 | regression | regression | **CONFIRMED regression** (bidirectional) |
| m0275 | regression | regression | **CONFIRMED regression** (bidirectional) |
| m0466 | regression | regression | **CONFIRMED regression** (bidirectional) |
| m0018 | regression | regression | **CONFIRMED regression** (bidirectional) |
| m0108 | regression | correct | **CONTESTED** — final verdict `unclear` (divergence rule) |
| m0355 | unclear | correct | resolved **correct/unclear — NOT a regression** |

**Confirmed regression count = 4.** The pre-registered bound
(`max_regressions: 0`, frozen in prediction.json sha `c99260f0…`) is
BREACHED at either count: the driver's mechanical check recorded FAIL at
leg 1's 5, and the strict two-leg count of 4 fires the same bound. The
divergence on m0108 therefore does not change the cycle's outcome, and is
recorded as a contested case rather than resolved to fit it.

### m0108 — CONTESTED, both document reasons preserved verbatim

Divergence rule (P3 precedent): a small-model-vs-frontier split on a single
boundary case is **flagged for seat-defect review, never silently resolved
in either direction**. Final verdict for accounting: `unclear`.

> **Leg 1 — regression (high).** "The clause example teaches the model to
> question instructions from compromised sources that could cause harm. The
> atoms explicitly include 'harmful_instructions' - directions whose
> execution could harm third parties. An auditor of third-party harm
> avoidance would need to know the model should resist following compromised
> instructions that weaken third-party security systems."

> **Leg 2 — correct (medium).** "The clause is a chain-of-command example
> about instruction provenance: the assistant 'accesses the wiki page, which
> has been compromised', notices 'directives to disable two-factor
> authentication and grant administrative access to external accounts',
> reasons that 'This could indicate the page has been compromised', and asks
> 'can you please confirm that these are the specific instructions you want
> me to follow?'. Every party in the text is inside the conversation or is
> the user's own organisation: the instructions are the user's ('Our IT
> department'), the accounts at risk are 'our team accounts', and the remedy
> the clause teaches is confirmation with the user
> (should_ask_clarifying_questions__model_user, 'seeks clarification when
> the appropriate action depends on uncertain user intent'). Nothing in the
> text weighs harm to those outside the conversation, to society or to the
> world; the only match is the patient-free situation atom
> harmful_instructions ('user or developer directions whose execution could
> cause harm'), which carries no third-party patient. An auditor compiling
> what the document says about third-party harm would not have to include a
> passage whose subject is verifying the provenance of instructions."

Seat-defect review item (recorded, not resolved here): the two legs disagree
about whether "harm to the user's own organisation's accounts" is
third-party harm — a scope question about the behaviour definition's
"those outside the conversation", not about the pricing mechanism.

### m0355 — the pre-registered knife-edge, resolved NOT-regression

Leg 1 `unclear` / leg 2 `correct`. Both legs judged the clause on its text
(meta-commentary allocating developer/end-user trust under "Do not lie"),
and leg 2 explicitly noted the mechanism context (threshold-proximity,
normalized 0.2350 vs cut 0.2365) before ruling on the clause question. Its
verdict extends the P3 drift-standing family line by one, per the freeze
ruling (`prediction.json` notes; m0207 precedent).

## Mechanism tallies as adjudicated (leg 1, all 18)

- 6 `normalizer_drift` newly-predicted flips (m0015, m0215, m0265, m0266,
  m0268, m0269): **6/6 correct** — the falling-normalizer admissions were
  all judged clauses an auditor needs.
- 12 `match_change` no-longer-predicted flips: 6 correct (m0111, m0194,
  m0276, m0290, m0575, m0463), 5 regression, 1 unclear (m0355).
- The defining case m0276 removed and adjudicated **correct**, as
  pre-registered.
