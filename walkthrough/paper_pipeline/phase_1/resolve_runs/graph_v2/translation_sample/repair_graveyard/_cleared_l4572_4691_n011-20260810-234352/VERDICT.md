# VERDICT: schema-breach craft-slip class (borrowed-name gloss / read_back slots / undeclared reference)

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: assertion names act 'produce(M)', which is not in `acts`. Every act must be declared once so the closure declaration can be checked against it
- `schema-breach`: body references `sexual_content` but nothing declares it. Put it in this module's `ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about the case). ⚠️ 
- `schema-breach`: body references `produce` but nothing declares it. Put it in this module's `ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about the case). ⚠️ A `conc
- `schema-breach`: body references `romantic_or_erotic_roleplay` but nothing declares it. Put it in this module's `ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about t

Diagnosis: the module referenced a borrowed name without a gloss, mismatched read_back slot counts, or left a body reference undeclared -- the classes the stage-2 inputs-gloss extension (schema.py, guard-accepted 2026-08-12) and the run-6..8 node worked-example/output-format fixes target. Run 8 measured 13/15 on the same sample. Disposition: cleared; the 2026-08-12 small-set rerun with the full fix stack is this class's regression test -- a recurrence re-opens as a NEW entry with fresh evidence.
