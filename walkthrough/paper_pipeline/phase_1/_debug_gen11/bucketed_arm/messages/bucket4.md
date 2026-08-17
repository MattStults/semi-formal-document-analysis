PROCEDURE 4 of 4 — HYGIENE, THEN THE ANTI-RULES

**Step 1. The gloss-restates-name ledger.**
For every entry in `concepts` and in `ontology`, do this mechanically:

1. write the entry's NAME with the underscores replaced by spaces;
2. write its `gloss`;
3. if (2) is (1) with the variables inserted and nothing more, the gloss passes
   ZERO information.

`safety_precaution_suggestion/1` glossed *"S is a suggestion that the user take
safety precautions"* is the name, re-spaced. Same for *"T is a transformation
task"*, *"S is an interactive setting"*, *"A is a straightforward answer"*.
A gloss is the ONLY way another module's definition can ever be matched to
yours.

For each gloss that fails: say what makes the predicate TRUE, in words that are
not in the name.
⚠️ **ADD to the gloss; do not REPLACE it.** A gloss rewritten to state argument
order and nothing else is worse than the one it replaced. Keep the present
sentence and extend it.

**Step 2. The argument-order ledger.**
List every predicate in the module of arity ≥ 2, coined or borrowed. For each,
write which argument is which. Then check whether the gloss says so. If it does
not, add it to the gloss (keeping the present sentence).

A total inversion — `authority_levels_hierarchy(higher, lower)` vs
`(lower, higher)` — **passes every deterministic check that exists.** Writing
your reading into the gloss is what turns a silent inversion into a visible
disagreement.

**Step 3. The recursion ledger.**
List every rule whose head predicate appears in its own body. For each, apply
the test below before touching it:

* Is it `forbid X(R) :- X(R)`, or the same shape — an unconditional prohibition
  over a variable act? If YES it is **SCHEMA-FORCED and CORRECT. Leave it
  exactly as it is.**
* If NO, the recursion is a real defect. Fix it.

**Step 4. The anti-rule sweep. Run this last, over every change made in this
conversation.**

Re-read the three anti-rules below. Then go back over every edit you have made
across procedures 1, 2, 3 and 4, and **UNDO any edit that violates one of
them.** Restoring something you changed earlier in this conversation is an
expected outcome of this step.

* **`forbid X(R) :- X(R)` is SCHEMA-FORCED, not a defect.** An unconditional
  prohibition over a variable act requires the tautological binder. Do not
  "repair" it, and do not let step 1's head-in-its-own-body test fire on it.
* **A `requires` entry that no module here provides is CORRECT on a
  single-clause module.** Moving the predicate into `inputs` to silence that
  destroys the distinction rule 9 calls load-bearing. This is the single most
  common false alarm on this corpus. A `NEEDS` name in `requires` that is used
  nowhere is CONTRACT-REQUIRED — leave it alone.
* **Never make `status` and `read_back` agree by REWRITING THE READ-BACK.** The
  two are written independently and that redundancy is the only place a wrong
  status is visible. Fix the formal item, then update the prose's slots, and
  preserve its wording.

Where a step's remedy would violate one of the twelve rules in my first
message, **the rule wins** — say what you found in `claims` rather than
encoding a remedy the format cannot carry.

Return the complete module object and nothing else.
