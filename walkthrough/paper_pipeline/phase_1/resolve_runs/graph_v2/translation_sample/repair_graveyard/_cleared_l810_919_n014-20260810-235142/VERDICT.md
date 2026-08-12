# VERDICT: schema-breach craft-slip class (borrowed-name gloss / read_back slots / undeclared reference)

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: no default-closure declaration for act class(es) ['refuse_request']. It is FORCED, not optional: an absent declaration reads as 'whatever is not forbidden is permitted', silently. 
- `schema-breach`: closure declared for act class(es) ['refuse_help'] the module does not govern — a commitment about acts this clause is not about
- `schema-breach`: `request/1` is borrowed but has no gloss. Add a `concepts` entry saying what this module needs it to MEAN — not what defines it, which stays in `requires`/`inputs`. Without it a se
- `schema-breach`: module says clause_id 'l810_4571_n014' but it was asked to translate 'l810_919_n014'. The artifact would carry two identities

Diagnosis: the module referenced a borrowed name without a gloss, mismatched read_back slot counts, or left a body reference undeclared -- the classes the stage-2 inputs-gloss extension (schema.py, guard-accepted 2026-08-12) and the run-6..8 node worked-example/output-format fixes target. Run 8 measured 13/15 on the same sample. Disposition: cleared; the 2026-08-12 small-set rerun with the full fix stack is this class's regression test -- a recurrence re-opens as a NEW entry with fresh evidence.
