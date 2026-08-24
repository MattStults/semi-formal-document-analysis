# Error-calculus router — static diagram

```mermaid
flowchart LR
  M([reported failure]) --> R1{"R1 panel (3u)\ntruth solid?"}
  R1 -- overturned --> T1([RESOLVED: truth error])
  R1 -- stands --> R2{"R2 audit (1u)\ntranslation faithful?"}
  R2 -- unfaithful --> R2b["R2b retranslate (2u)"]
  R2b -- resolves --> T2([RESOLVED: translation])
  R2b -- persists --> C
  R2 -- faithful --> C{census verdict}
  C -- SEPARABLE --> R3["R3 delta (1u)\nbudget 2, ledgered"]
  R3 -- validates --> T3([RESOLVED: declaration])
  R3 -- budget exhausted --> R3x["R3x: missing intension\n→ mint (8u)"]
  C -- REACHABLE --> R4["R4 build consumer (5u)\nper feature"] --> R3
  C -- UNSAT --> R5["R5 mint (8u)\nbudget 2"]
  R5 -- separates --> R3
  R5 -- needs consumer --> R4
  R3x --> R5x
  R5 -- exhausted --> R5x{"R5x exhaustion ruling"}
  R5x --> T4([TERMINAL by document])
  R5x --> T5([DEFENSIBLE])
```

Judgment ports (frontier/human): R1 rulings, R2 audits, the intension inside
R3x/R5 mints, and the R5x ruling. Everything else is computation.
Verified: calculus_model.py + calculus.lp (clingo) — 0 gaps / 0 ambiguities /
0 cycles; mutation-tested 5/5.
