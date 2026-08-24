# Error-calculus router — static diagrams

Judge legend used in both diagrams below (and the widget):
**⚙ deterministic** — computed from committed artifacts, no model in the loop ·
**◇ cheap-certified** — any tier holding a measured parity certificate for the
pinned brief (plus seeded frontier spot-check) ·
**★ frontier** — measured frontier-only (cheap tiers failed parity on this brief) ·
**★+human** — generative naming or process-binding: frontier seat plus human ratification.

## 1. The router

```mermaid
flowchart LR
  M([reported failure]) --> R1{"R1 verify truth (3u) ★\n3-seat panel re-rules"}
  R1 -- overturned --> T1([RESOLVED: truth error])
  R1 -- stands --> R2{"R2 verify translation (1u) ★\naudit vs document"}
  R2 -- unfaithful --> R2b["R2b retranslate (2u) ◇\ncheap tier + mechanical checks"]
  R2b -- resolves --> T2([RESOLVED: translation])
  R2b -- persists --> C
  R2 -- faithful --> C{census verdict ⚙\ncomputed, free}
  C -- SEPARABLE --> R3["R3 config fix (1u) ⚙\noptimizer + exact arithmetic;\nnew flips adjudicated ★ (small)"]
  R3 -- validates --> T3([RESOLVED: declaration])
  R3 -- ledger exhausted --> R3x["R3x coin concept (8u) ★+human\nmissing intension"]
  C -- REACHABLE --> R4["R4 build consumer (5u) ⚙\ndesign review ★"] --> R3
  C -- UNSAT --> R5["R5 coin concept (8u) ★+human\nprogress: collider set must shrink"]
  R5 -- separates --> R3
  R5 -- needs consumer --> R4
  R3x --> R5x
  R5 -- no progress --> R5x{"R5x final ruling ★+human"}
  R5x -- exhaustion CERTIFICATE --> T4([TERMINAL by document])
  R5x -- no certificate --> T6([SUSPENDED-OPEN\nat inventory k])
  R5x --> T5([DEFENSIBLE])
  classDef det fill:#14532d22,stroke:#16a34a;
  classDef cheap fill:#1e3a8a22,stroke:#3b82f6;
  classDef front fill:#78350f22,stroke:#d97706;
  classDef human fill:#7f1d1d22,stroke:#dc2626;
  class C,R3,R4 det;
  class R2b cheap;
  class R1,R2 front;
  class R3x,R5,R5x human;
```

## 2. Preconditions — what must exist before the machine can run
(calculus A14; validated mechanically by `preflight.py` before every
iteration. The machine is a REPAIR calculus: a reported failure is
E(n,b) ≠ T(n,b), so E must be computable first — it cannot start from
zero nodes. Truth is the one cold-startable component.)

| # | precondition | why it is not arbitrary | mechanical check (preflight.py) | cold-startable? |
|---|---|---|---|---|
| P1 | Decomposition: canonical node corpus, stable ids, verbatim spans, source sha pinned | E's domain — without nodes there is nothing to engage | corpus parses; every node has id+quote; sha recorded | no — bootstrap pipeline |
| P2 | Translation liveness: nodes carry bridgeable acts; every module engages >0 nodes | E must be non-degenerate (the F1 silent-empty-lane class). Liveness only — QUALITY is what the machine improves | per-module engagement >0; bridge coverage >0 | no — bootstrap pipeline |
| P3 | Keying consistency: layers + truth ledger key to the canonical corpus | routing evidence must resolve; drift silently corrupts every downstream computation | zero layer-orphans; zero hard drift; canonical drift only within the FROZEN named set (F_R1_KNOWN_DRIFT.json — any NEW node fails) | no |
| P4 | Modules: definition text + declarations within DECLARABLE_MOVES | D must live in the registry every enumerator derives from (A12) | schema + registry membership | no |
| P5 | Pinned ruling brief with a MEASURED stability record (+ truth ledger, possibly empty) | the judge IS the instruction (measured 20/20 vs 0.62–0.75); an unpinned brief is an undefined judge at any tier | stability record present in the pinned brief file | **yes — truth only**: the machine manufactures rulings through the brief |
| P6 | Harness: census / probe / verify_terminal / trace / route importable; registry handshake holds | repair without verification is the metric-gaming failure the campaign was founded on | imports + handshake assertion | no |
| P7 | Governance: hypothesis + notes ledgers, runbook, stop conditions, budget registration | no-revisit (A9), learning-as-artifact, and halt-don't-improvise are load-bearing, not decoration | files exist; STOP CONDITIONS present | no |

```mermaid
flowchart LR
  DOC([document]) --> B["bootstrap pipeline ⚙
decompose → translate →
annotate → modules
(own validation: stage tests,
semantic-audit gate)"]
  B --> PF{"preflight.py ⚙
P1–P7"}
  PF -- any FAIL --> STOPB([blocked: fix the
precondition, not the machine])
  PF -- 7/7 --> RC["repair calculus
(diagram §1)"]
  T0["zero truth? fine —
pinned brief manufactures
rulings (P5, cold start)"] -.-> RC
  classDef det fill:#14532d22,stroke:#16a34a;
  class B,PF det;
```

## 3. The capability decision tree (calculus A10 — which judge does a
## decision node need?)

```mermaid
flowchart TD
  Q1{"Q1 — output a function of\ncommitted artifacts?"}
  Q1 -- yes --> D1["⚙ DETERMINISTIC\ncensus, arithmetic, fingerprints,\nrouting, trace checks"]
  Q1 -- no --> Q2{"Q2 — judgment class has a\nPINNED, stability-measured brief?"}
  Q2 -- no --> D2["★ DESIGN TIER pins the brief first\n(unpinned judgment is unstable\nat EVERY tier — measured 15/24\nfrontier test-retest)"]
  Q2 -- yes --> Q4{"Q4 — decision GENERATIVE\n(naming a concept)?"}
  Q4 -- yes --> D4["★+human — port P3\n(no answer key can certify it)"]
  Q4 -- no --> Q5{"Q5 — binds future process\n(floor / prereg / terminality)?"}
  Q5 -- yes --> D5["★+human signature"]
  Q5 -- no --> Q3{"Q3 — parity CERTIFICATE for\ntier T on this brief?\n(measured on ledger-known cases, free)"}
  Q3 -- yes --> D3["◇ CHEAPEST CERTIFIED TIER\n+ seeded ★ spot-check\n+ escalation tripwire"]
  Q3 -- no --> D3b["★ frontier\n(certificates re-measure when\nbriefs change — the capability\nmap is empirical, never opinion)"]
  classDef det fill:#14532d22,stroke:#16a34a;
  classDef cheap fill:#1e3a8a22,stroke:#3b82f6;
  classDef front fill:#78350f22,stroke:#d97706;
  classDef human fill:#7f1d1d22,stroke:#dc2626;
  class D1 det; class D3 cheap; class D2,D3b front; class D4,D5 human;
```

Verified: calculus_model.py + calculus_model_v2.py + calculus.lp (clingo,
mutation-tested 5/5); historical validation ROUTE_VALIDATION_V0.json
(52 cases, 49/52, all traces certified).
