# VERDICT: repair converged (3 attempt(s)); residue is note-severity

Status: translated.

Evidence (this entry's own findings):
- `requires-unprovided`: `age_under_18/1` is declared in `%% requires:` and no module in this link scope defines it
- `requires-unprovided`: `assistant/1` is declared in `%% requires:` and no module in this link scope defines it
- `requires-unprovided`: `real_world_ties_principle/1` is declared in `%% requires:` and no module in this link scope defines it

Diagnosis: the module translated after repair; nothing at error
severity remains. Entries like this exist because the graveyard
records every non-first-attempt convergence, not only failures.
Disposition: cleared. The 2026-08-14 full-corpus run is the
regression surface -- a recurrence opens a NEW entry with fresh
evidence and its own diagnosis.
