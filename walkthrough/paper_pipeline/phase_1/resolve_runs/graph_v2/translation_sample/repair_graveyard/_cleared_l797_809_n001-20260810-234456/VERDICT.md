# VERDICT: schema-breach craft-slip class (borrowed-name gloss / read_back slots / undeclared reference)

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: ontology atom: 'stay_in_bounds_principle(P)' carries the variable 'P' but the body never mentions it, so nothing binds it. The solver refuses the WHOLE FILE for an unsafe variable 
- `schema-breach`: ontology atom: 'limits_taxonomy(T)' carries the variable 'T' but the body never mentions it, so nothing binds it. The solver refuses the WHOLE FILE for an unsafe variable — bind it

Diagnosis: the module referenced a borrowed name without a gloss, mismatched read_back slot counts, or left a body reference undeclared -- the classes the stage-2 inputs-gloss extension (schema.py, guard-accepted 2026-08-12) and the run-6..8 node worked-example/output-format fixes target. Run 8 measured 13/15 on the same sample. Disposition: cleared; the 2026-08-12 small-set rerun with the full fix stack is this class's regression test -- a recurrence re-opens as a NEW entry with fresh evidence.
