# Adversarial design review of CYCLE5_DESIGN.md — verdict: DO NOT BUILD AS WRITTEN

2026-08-04. The reviewer implemented the design's pricing rule and executed it
against the live artifacts; findings below are computed, not reasoned.
CYCLE5_DESIGN.md must be amended per the MUST list before any build.

## MUST change before build

1. **Chain semantics inverted (F1).** grammar.py's chains are AGENT-FIRST; a
   length-1 chain records no patient (structural.py's shipped, test-pinned
   reading: patients = chain[1:]). The design read a sole member AS the
   patient — and the defining case depends on it: m0276's only chain is
   `must_advise_immediate_help__user`, which under the grammar parses as
   "the USER advises" — the annotation itself misused the convention.
   Fix: taint/patient reading from length-≥2 chains only; length-1 =
   patient-free; m0276 arrives via the backfill cycle re-chained
   `__model_user`.
2. **Flip prediction wrong >2× and mis-classed (F2).** Simulated at d=0.25
   under frozen cuts: 12 flips (not 1-5), 11 of them under-18 section
   clauses the census classed fp_section_prior — the cycle moves exactly
   1/155 of its nominal target class. §2 must carry the computed pin and §0
   the 1/155 scope truth.
3. **I2 unsound on normalized scores (F3).** The corpus-max normalizer moves
   when the argmax section is tainted (harm: every untouched clause's
   normalized score rises ~5%); monotonicity holds on RAW scores only, and
   normalizer-driven bystander flips would be mis-tagged match_change.
   Restate I2 on raw; demote zero-newly-predicted to a pinned computed fact;
   queue a normalizer_drift dossier annotation.
4. **Anchor check assigned to a panel-reading module (F4).**
   validate_behaviours.py opens data/behaviours.json (FORBIDDEN). House the
   patients-field license check panel-blind (patient.py or a new scanned
   validate_query.py).
5. **Definition-editing gameable inside the declared diff (F5).** Gate test:
   each behaviour's name+definition byte-equal to their cycle-4-closure
   values; the `patients` key is the only permitted delta.
6. **Cycle-4 dependency holes (F6).** Gate on cycle-4 CLOSED-with-KEEP (done:
   4f44c50); gate-assert every behaviour in both snapshots records
   threshold_source=frozen_artifact (fallback silently re-derives);
   explicit absent-pricing_version⇒legacy rule (baseline has no overlay, so
   no pricing_version key at all).

## Plausible / pre-register

- 11/12 flips ride the under-18 contested boundary (Q4 IS the cycle):
  pre-register that adjudication as the cycle's real question; regression ⇒
  revert loses m0276 too, by design.
- Taint marks m0221/m0222 (previously adjudicated correct) forever at ×0.25;
  REQUIRE golden review of any backfilled chain on ever-adjudicated-correct
  clauses.
- d=0.25 plateau: flip set identical for d ∈ {0.1, 0.25, 0.4} — pin the
  plateau at OPEN; the constant is defensible without a sweep.
- I1 (helpfulness equality) is current-artifact luck, not coverage; pin as
  such.

## Ladder change (accepted)

A cheap **CHAIN-AUDIT cycle precedes cycle 5**: golden-review the 109 chain
instances (at minimum the 16 length-1 chains and the 31 chained max-clauses),
fixing agent-first violations — annotation-shaped, settles §1.2 by evidence.
Then amended cycle 5, then the patient-backfill annotation cycle measured
through the adjudicated pricing mechanism.
