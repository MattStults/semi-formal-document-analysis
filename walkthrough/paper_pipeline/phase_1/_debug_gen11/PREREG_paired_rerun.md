# PRE-REGISTRATION — paired re-run: is the gain the FIXES or the DATA?

Written and committed BEFORE the re-run is launched. Owner's question, verbatim:
*"we should translate one of the earlier slices next to see if the change is data or fixes"*.

## The observation to explain

| run | n | translated | first-try |
|---|---|---|---|
| `20260814-173322` (old contract) | 88 | **69%** | — |
| `20260815-070038` (old contract) | 69 | 84% | — |
| `20260815-124836` (current contract, NEW nodes) | 48 | **98%** | 69% |

98% vs 69% has two competing explanations and they are confounded in the data
we have, because the 48-node slice changed BOTH the contract AND the clauses:

* **H-FIXES** — the contract improved (prompt growth 28,091 → 37,891 chars, the
  restart policy, the arity check). The clauses were not easier.
* **H-DATA** — the 48 strided nodes were simply easier than the 88 in the
  earlier slice. The contract did little.

## Design: paired, same clauses, new contract

Re-run **the same 88 clause ids** processed by `20260814-173322`, under the
current contract. Clause set is held FIXED, contract is the only thing that
moves — so this isolates exactly the variable the confound hides.

## Pre-registered readings, fixed before any result is seen

Let `R` = translated rate on the re-run of those 88 clauses.

| result | reading |
|---|---|
| **R ≥ 92%** | **H-FIXES.** The contract carries the gain; the 48-node result was not a lucky draw. |
| **R ≤ 75%** | **H-DATA.** The gain was clause difficulty; the 98% does not generalise and the corpus-wide expectation stays ~70–85%. |
| **75% < R < 92%** | **BOTH.** Report the split, claim neither cleanly, and quote R as the corpus-wide expectation rather than 98%. |

Secondary, recorded now so they cannot be chosen afterwards:

1. **Per-clause pairing** is the real evidence, not the aggregate: report the
   2×2 of (old outcome × new outcome). The cell that matters is
   **old `unrepaired` → new `translated`**, which is the contract recovering a
   clause it previously lost. Its complement, **old `translated` → new
   `unrepaired`**, is a REGRESSION and is reported however small.
2. **Restart firing rate** on this population, against the review's live-stratum
   prediction of 32% [24, 42] of multi-attempt chains and the 13% seen on the
   48-node slice.
3. **Abstention count.** The 48-node slice returned 0 of 48. If this population
   also returns ~0, that is a property of the contract, not of the sample.
4. **Route mix** — how many modules are ontology-only vs hard-deontic — since
   the routing study measured 45% ontology at attempt 1 across 152 older
   modules and 19% on the new slice. A large shift is itself a finding.

## What this CANNOT settle

* It cannot tell us which of the several contract changes did the work; the
  contract moved as a bundle. Attribution to the restart policy specifically
  requires the per-clause restart data, not the aggregate.
* Re-running clauses the model has seen before is NOT a contamination risk here
  (no cross-call memory), but the modules produced will differ from the stored
  ones and **must not overwrite them** — this writes a new run directory.
* `20260814-173322` ran an OLDER prompt than `20260815-070038`. The 84% run is
  the nearer baseline; 69% is the further one. Chosen deliberately for the
  larger signal, and the 84% run remains available as a second pairing if the
  result is ambiguous.
