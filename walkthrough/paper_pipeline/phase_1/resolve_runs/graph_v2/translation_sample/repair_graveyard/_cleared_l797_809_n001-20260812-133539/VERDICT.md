# VERDICT: unrepaired after 5 attempts -- unbound-variable class

Status: unrepaired.

Evidence (this entry's own findings):
- `schema-breach`: ontology atom: 'stay_in_bounds_principles(P)' carries the variable 'P' but the body never mentions it, so nothing binds it. The solver refuses the WHOLE FILE for an unsafe variable — bind it in the body, or drop it from 

Diagnosis: an ontology atom carries a variable the body never
binds, so the solver refuses the whole module. This is a craft
slip the repair loop could not talk the model out of in 5
attempts -- a genuine unconverged translation, not a checker
defect. Disposition: cleared as DIAGNOSED-UNCONVERGED. If the
class recurs in the full-corpus run it becomes a tracked census
category with a prompt lever (name the binding requirement in
the ontology instruction), per the standing repair-census rule.
