# PRE-REGISTRATION DRAFT — arm 3: SYMBOLIC relevance (ASP corpus on the critical path)

Status: DRAFT, unhashed. Two open questions for Matt (asked 2026-08-18)
shape this document; it is hashed and signed only after they are answered.

## The claim
Relevance computed FROM the translated ASP corpus — a module is relevant to
a behavior iff it asserts a deontic status on a canonical act the behavior
performs (act ontology + bridges), optionally refined by a seat pass on the
scope/condition residue — reaches defensibility at least equal to the
LLM-seat instruments (cold-start arm 1, tuned arm 2) on the same held-out
halves under the same Fable truth tier, at $0 per query and with a stated
reason per hit.

## Sub-arms (Q1 — register both, or (a) only?)
(a) SYMBOLIC-ONLY: relevance_by_act.py, static read of assert heads through
    act_bridges.lp. No LLM in the relevance path.
(b) COMBINED: symbolic first; the seat (amended brief) adjudicates ONLY the
    residue — nodes symbolic engages whose relevance turns on scope/party/
    condition, i.e. where the behavior's guards do not hold. Reports seat
    calls used vs the seat-only arms.

## Ontology under test (Q2 — freeze as-is, or after one tuning-half-driven
refinement round?)
act_bridges.lp at commit <sha at freeze>, act ontology validator verdict
recorded (validate_ontology.py acts). If refined first: refinements may use
ONLY tuning-half verdicts (arm-2 discipline); the refined ontology's own
validator run is recorded; scoring on held-out only.

## Truth tier, halves, metric — IDENTICAL to arms 1–2
Fable adjudicators under the calibration rule (ESTABLISHES-anchored); the
same 50/50 split (seed 20260817); metric 0 defensibility (engagement,
decline, deviation) plus recall; per-branch coverage reported (the module
representation makes it available).

## Pre-stated predictions and falsifiers
* Prediction: symbolic-only >= tuned seat on >= 2 of 3 behaviors (prior:
  helpfulness 0.73 vs 0.65, caution 0.67 vs 0.67, harm 0.61 vs 0.78 on the
  provisional ontology, unregistered).
* Falsifier: symbolic-only < cold-start seat on any behavior, OR the
  combined arm does not beat symbolic-only while spending seat calls.
* Structural falsifier: act validator BLOCKED at freeze (A7 firing
  consistency must pass; A1/A4 must be clean).
