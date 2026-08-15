# VERDICT: converged after repair (2 attempts); residue is expected incompleteness

Status: translated -- the module TRANSLATED; no finding at error severity.

Evidence (this entry's own findings):
- (no findings)

Diagnosis: `requires-unprovided` at this point in the FULL-CORPUS run is expected by construction -- at ~45 of 773 modules most providers are simply not translated yet, so a cross-module `requires` has nothing to resolve against. It is incompleteness, not a defect, and it resolves as the corpus fills. The entry exists because the graveyard records every non-first-attempt convergence, not only failures.

Disposition: cleared. RECHECK AT CORPUS COMPLETION: if `requires-unprovided` persists for these names once all 773 modules exist, it becomes a real under-export finding and a tracked census category.
