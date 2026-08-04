# S3 mechanism amendment — taint cap + derived constant (2026-08-04)

Loud amendment record (pre-PREDICT-freeze, so the manifest was edited
directly; this file is the old->new sha chain the freeze would otherwise
carry in manifest_amendments.json). Sanctioned path: the OPEN recomputation
(OPEN_RECOMPUTATION.md) broke the pre-registered d-plateau, firing
CYCLE5_DESIGN §1.4/Q6's pre-registered remedy — re-derivation from golden
patient-contrast cases. The designer adopted the frozen derivation's
recommendation in full (DISCOUNT_DERIVATION.md, sha
7e1979bc4505103eea58a138053e78a72ecdd7620a13f80cdc369a3d81df283e — also
pinned in test_patient.py).

## The amendment

1. **Taint semantics (the F-linearity fix):** under clause taint the
   surviving atom mass is capped at ONE discounted credit — tainted atom
   channel = d * max(base credits)/atom_norm, never d * sum. Deterministic
   survivor: highest base_credit, ties lexicographic on (clause_atom,
   query_atom, match); non-argmax credits are zeroed (factor 0.0, why
   "taint_capped", priced_credit 0.0), keeping explain sum-exact under the
   unchanged subtraction formula. Per-atom pricing on mixed clauses
   (taint defeated) unchanged: d per mismatched match. Invariants
   preserved and test-pinned: I2 monotone-downward on raw (capped mass <=
   the old d*sum), consistent-chain-defeats-taint, no-patients = bit-identity
   (I1), never-outprice.
2. **The constant:** PATIENT_MISMATCH_DISCOUNT = 0.10 (was 0.25 hand-set).
   Licensing basis: the derivation's golden-derived degenerate interval
   [0.10, 0.11] under the amended mechanism; tie-break as recorded there
   (equalize the binding (a) ceilings 0.114/0.119 against the (b) floor
   0.108; canonical one-decimal value). Docstring cites the derivation;
   the derivation sha is test-pinned so silent re-licensing is a loud
   test event.

## RED-first evidence

- `test_tainted_clause_mass_is_capped_not_linear_in_match_count` FAILED
  under d*sum (observed 0.45 = d*sum vs required 0.15 = d*max on the
  3-equal-idf dense fixture) and passes under d*max.
- `test_discount_constant_is_derived_0_10_pinned_to_the_derivation` FAILED
  at the old constant (0.25 != 0.10) and passes at 0.10 with the derivation
  sha intact.
- Guard pin added (already-green by design): `test_mixed_clause_per_atom_
  pricing_is_uncapped` — the cap is a taint rule only.
- Full patient/validate_query/no_reference_leak set: 73 passed post-amendment.

## sha chain

| file | old sha256 (pre-amendment) | new sha256 |
|---|---|---|
| patient.py | 1a8fb80bb65cacc9c3a3a0d5e030077e034f21a9fb1bdb6198e21210e1efe8ae | 4d2eda1046aae871ec82a5aadab87085645301852841eac30491cf2d3a0d450a |
| test_patient.py | 595e0b73fbf017ee2b9609fa15e573f2d4b7516bbcdda9e79386543f2f8fcdd7 | 779f69f713ddf8222e7dc04523ac53457253c180ddf54b28b9296e89a8ee190f |
| cycles/patient-pricing-2026-08-04/manifest.json | df5159a5014cd730e23c476de93906ee621c51cc284c02344ddd6342dbf0c438 | 8df0a1b477eebb7f804a4c7480b71bca114291a594638f05d690a140bf8b2084 |

NOTE (closure interaction): test_patient.py is a gate_test, so its OPEN
closure sha in state.json predates this amendment. The IMPLEMENT gate's
closure check would refuse the drift; this amendment record IS the loud
declaration of that change, made on the designer's ruling BEFORE the
freeze — state.json's closure pin for test_patient.py (and the open-shas
baseline for nothing else) is re-pinned to the new sha below, on the
record, as part of this amendment.
