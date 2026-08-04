# Flip adjudication assignment — cycle patient-pricing-2026-08-04

Seat brief: briefs/flip_adjudicator.md — read it first; it is the seat's
entire instruction. Judge each flip AGAINST THE DOCUMENT, from the dossier
alone.

Dossiers: flip_dossiers/ under this cycle's directory. Enumerate the work via
flip_dossiers/index.jsonl — one JSON dossier file per flip.

Dossier set sha256: 726492bf72fe5e9809ca8f6b402bec3161ca8ca4ff916ab05f7a05060e59b78b

Required output: flip_verdicts.json in this cycle's directory:

    {"dossier_set_sha": "726492bf72fe5e9809ca8f6b402bec3161ca8ca4ff916ab05f7a05060e59b78b",
      "records": [
        {"flip_id": "<copied verbatim from the dossier>",
          "verdict": "correct" | "regression" | "unclear",
          "document_reason": "<document-side reason, citing the clause>",
          "confidence": "high" | "medium" | "low"},
        ...]}

The dossier_set_sha above MUST be echoed verbatim — it binds your verdicts
to exactly this dossier set. flip_id, verdict, document_reason are REQUIRED
per record; confidence optional. Every flip in index.jsonl exactly once.
Reusing a previous adjudication is legal ONLY when the dossier bytes are
identical (same set sha) and declared via a "reused_from" key naming the
source file — never presented as fresh adjudication. The file is checked by
`dossier.py validate` before the cycle advances.

## Cycle-specific pre-registered notes (operator addendum — FROZEN facts
## only, from prediction.json sha c99260f0…; nothing here overrides the brief)

- Per-flip adjudication, document-side, from the dossier alone. 18 flips.
- MECHANISM, as each dossier records it:
  * The 6 harm newly_predicted flips (m0015, m0215, m0265, m0266, m0268,
    m0269) carry a `normalizer_drift` record ({raw_a, raw_b}): their RAW
    score did not rise (m0015/m0215 unchanged; the others fell) — the
    normalized crossing is the corpus-max normalizer falling (the harm
    argmax clause was taint-discounted), a threshold-class mechanism per
    the frozen prediction (S1 m0207 precedent). Adjudicate them per-flip
    like any other; the mechanism context is in the dossier, and each
    dossier's explain_b carries the full patient_pricing payload.
  * The 12 no_longer_predicted flips are match_change: the patient
    mismatch/taint discount moved the clause's own raw score through the
    frozen cut. The discounting chains and factors are itemized in
    explain_b.patient_pricing.
  * m0355 (harm, no_longer_predicted) was PRE-REGISTERED
    undetermined-at-freeze: its capped residual passes within ±0.005 of
    the frozen harm cut (normalized 0.2350 vs cut 0.2365; margin record in
    the frozen prediction notes). Per the designer ruling it is adjudicated
    like every other flip, with threshold-proximity named as its mechanism
    context; its verdict extends the P3 drift-standing family line.
- The frozen expectation of record (context, not instruction): m0276's
  removal was pre-registered expected `correct` (the design's hand
  autopsy); max_regressions = 0 is the frozen falsifiable bound — a
  `regression` verdict, particularly on a taint-set removal, is a REAL
  finding against the taint rule and must be recorded as your judgment,
  never suppressed to fit the prediction.
