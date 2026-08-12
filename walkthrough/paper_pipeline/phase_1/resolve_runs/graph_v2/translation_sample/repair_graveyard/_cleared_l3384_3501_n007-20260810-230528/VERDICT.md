# VERDICT: schema-breach craft-slip class (borrowed-name gloss / read_back slots / undeclared reference)

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: ['clarifying_question/1', 'developer_instruction/1'] appear in BOTH `requires` and `inputs`. `requires` means another clause must define it; `inputs` means it is supplied with the 
- `schema-breach`: assertion names act 'respond_with_plain_text_clarifying_question(R)', which is not in `acts`. Every act must be declared once so the closure declaration can be checked against it
- `schema-breach`: no default-closure declaration for act class(es) ['respond_as_plain_text', 'respond_via_function_call']. It is FORCED, not optional: an absent declaration reads as 'whatever is not
- `schema-breach`: closure declared for act class(es) ['respond_with_plain_text_clarifying_question'] the module does not govern — a commitment about acts this clause is not about

Diagnosis: the module referenced a borrowed name without a gloss, mismatched read_back slot counts, or left a body reference undeclared -- the classes the stage-2 inputs-gloss extension (schema.py, guard-accepted 2026-08-12) and the run-6..8 node worked-example/output-format fixes target. Run 8 measured 13/15 on the same sample. Disposition: cleared; the 2026-08-12 small-set rerun with the full fix stack is this class's regression test -- a recurrence re-opens as a NEW entry with fresh evidence.
