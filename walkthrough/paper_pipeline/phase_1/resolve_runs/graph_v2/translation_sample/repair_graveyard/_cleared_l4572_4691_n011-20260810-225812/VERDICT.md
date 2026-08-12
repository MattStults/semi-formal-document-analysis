# VERDICT: schema-breach craft-slip class (borrowed-name gloss / read_back slots / undeclared reference)

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: ontology atom: 'romantic_roleplay(U)' carries the variable 'U' and there are no conditions to bind it. The solver refuses the WHOLE FILE for an unsafe variable, so this would take 
- `schema-breach`: ontology atom: 'first_person_romantic_roleplay(U)' carries the variable 'U' and there are no conditions to bind it. The solver refuses the WHOLE FILE for an unsafe variable, so thi
- `schema-breach`: module says clause_id 'l4572_4691_n012' but it was asked to translate 'l4572_4691_n011'. The artifact would carry two identities

Diagnosis: the module referenced a borrowed name without a gloss, mismatched read_back slot counts, or left a body reference undeclared -- the classes the stage-2 inputs-gloss extension (schema.py, guard-accepted 2026-08-12) and the run-6..8 node worked-example/output-format fixes target. Run 8 measured 13/15 on the same sample. Disposition: cleared; the 2026-08-12 small-set rerun with the full fix stack is this class's regression test -- a recurrence re-opens as a NEW entry with fresh evidence.
