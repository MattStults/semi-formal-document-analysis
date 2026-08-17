# SEAM CONTRACT — identity rulings for shared names (2026-08-16)

The borrowing seam had no identity contract: gloss, argument sort, and arity
were each independently guessable, every guess passed every check, and a
mismatch was indistinguishable from an unlinked provider (`root_authority`
split 0-vs-1 across 12+ modules; 14 shared names with arity disagreements on
the first corpus_gate run). Matt's original blocker — "we could interpret the
result as matching or not by choosing different definitions for things not
yet fully defined" — is this seam. Ruled before the full-corpus translation
run so 559 new modules are drafted under the contract instead of re-guessing.

**The data is `SEAM_CONTRACT.json`** (one arity + argument sorts + one
document-wide gloss per name). Enforcement is `corpus_gate.py`'s
`seam_contract` cross-check (hard tier). The translator sees the contract as
`node_seam_contract.md` in the corpus config's system block.

## Grounds for the authority-family ruling (the load-bearing one)

`X_authority/1` = "rule/instruction R carries authority level X":

1. **The demonstration governs.** `node_worked_example.md` L185–201 shows
   `guideline_authority(R) :- rule_under_heading(R, ...)` — the authority
   predicate takes a RULE, the heading appears only inside a separate
   relation. Demonstrations are what the model imitates (the licence-ruling
   episode re-proved this the same day).
2. **The corpus already conforms.** Measured on the concept index:
   `root_authority` is declared `/1` by ~28 modules and `/0` by 3; the other
   level names split the same way. The contract ratifies the dominant,
   demonstrated shape rather than migrating the corpus to a minority one.
3. Where a module needs a LEVEL as a term (orderings, `instruction_level/2`),
   it uses level constants (`defaults_level` is the demonstrated example) —
   distinct names from the `/1` predicates, so the same symbol never carries
   two sorts.

**Rejected by name:** reifying the five levels as constants with one shared
`assigned_authority/2` relation (`assigned_authority(R, root_authority)`).
Cleaner type theory, but it contradicts the worked example's demonstration,
orphans the ~28-module majority, and requires a corpus-wide migration for
zero query-side gain — `root_authority(R)` and
`assigned_authority(R, root_authority)` are interconvertible one-liners.

## Other pins, briefly

* `message_role_definition/2 (M, R)`: borrowers need the relation that binds
  a message to its role; the `/1` "concept about roles" variant gives the
  solver nothing to join on.
* `delegated_power/2 (P, L)`: the PROVIDES declaration wins over a borrower's
  `/1` coinage — providers own their names (contract 2).
* `information_hazards_prohibition/1`: the `/2` occurrence had duplicated the
  hierarchy's semantics into the wrong name — a mis-gloss, not a variant.
* `answers_question/2 (R, Q)`, `developer_instruction/1`,
  `user_instruction/1`, `higher_level_instruction/1`,
  `assistant_definition/1`, `model_spec/1`, `usage_policies/1`: dominant
  shape, argument order pinned in the gloss.

## Standing rules the contract adds

1. **A shared name's gloss is document-wide, never section-local.** "R is a
   rule in the #scope_of_autonomy section carrying root authority" is a false
   statement about the predicate the module actually receives once linked
   (slice-3's sweep finding, now `section_local_gloss` at hard tier for
   contract names).
2. **Provider declarations win.** A borrower who needs a different shape
   records the disagreement in its gloss; it does not fork the arity.
3. **New shared names enter the contract when their second borrower
   appears**, with the provider's declaration as the default pin.

## Consequences

Existing modules conflicting with the contract fail the gate's new hard check
and join the redraw queue with the bulk run. The panel-agreement and pilot
artifacts predate the contract; their numbers are unaffected (the seat reads
prose, not predicates).
