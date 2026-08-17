# The review list for THIS clause — run it on your own module before you return it

Everything below was **measured on this corpus**, by a reviewer reading finished
modules against their spans. Each entry is a **question to ask**, not a
description of a rule.

⚠️ **This is a SELECTION, not the whole list.** The full list has eighteen
entries. The ones below were picked because a feature of *this clause's own
text* matches what they test — the reason is printed under each one. Entries not
shown were judged not to apply here; do not go looking for them. **Run the ones
below hard**, on the object you are about to return, not on your intentions.

⚠️ Where an entry's remedy would violate one of the twelve rules above, **the
rule wins** — say what you found in `claims` rather than encoding a remedy the
format cannot carry.

---

*(retrieved for this clause because: a NEEDS/PROVIDES gloss describes a relation; span states an ordering/conflict between two things)*

### 9. For each relation of arity ≥ 2, is the argument order stated in its gloss?
*(4 of 17)* A total inversion — `authority_levels_hierarchy(higher, lower)` vs
`(lower, higher)` — **passes every deterministic check that exists**. Write your
reading into the gloss so a mismatch surfaces as a disagreement instead of a
silent inversion. Applies to names you coin as well as names you borrow.

*(retrieved for this clause because: explicit hedge lexeme)*

### 7. Does the span hedge — and if you cannot encode the hedge, did you SAY SO?
*(7 of 17)* `toggleable` is reserved for `world` facts, so *"by default"*,
*"generally"*, *"should"*, *"may want to"* have nowhere to live except a body
condition. **An unconditional `oblige` is byte-identical to one whose default was
dropped.**
**Ask:** does the span hedge? Encode the defeater as a body condition **if the
span names one**; if it names none, say so explicitly in `claims` and in the
read-back. ⛔ **Do not invent a defeater to satisfy this** — see entry 14.

*(retrieved for this clause because: scope qualifier present; universal quantifier)*

### 8. Does each body widen past the span's qualifier, or NARROW a prohibition the span states unconditionally?
*(7 of 17)* Measured in both directions on one module: it forbade every
recipe (too wide) while permitting every overview *including ones with specific
ratios* (too narrow, in the dangerous direction).
⚠️ **The counter-intuitive half:** a body condition added to encode *"regardless
of context"* or *"by default"* **WEAKENS** the rule — it makes the rule fire only
where that condition is affirmatively supplied, so a situation that simply does
not mention it derives nothing.

*(retrieved for this clause because: always (module writes glosses); PROVIDES/NEEDS present)*

### 1. Does a `gloss` restate its predicate's name instead of defining it?
*(found something on 12 of 17 clauses — the highest-yield entry in this file, and
the cheapest to run)*

`safety_precaution_suggestion/1` glossed *"S is a suggestion that the user take
safety precautions"* is **the name, re-spaced**. Same for *"T is a transformation
task"*, *"S is an interactive setting"*, *"A is a straightforward answer"*.
A gloss is the **only** way another module's definition can ever be matched to
yours; one that restates the name passes zero information.

**Ask, of every `concepts` and `ontology` gloss:** does it say what makes the
predicate TRUE, in words that are not the name? For an arity ≥ 2 relation, does
it say which argument is which?
Also ask P8's first half: **does any rule's head appear in its own body?**
⚠️ Do not *replace* a gloss to satisfy this — **add** to it. A gloss rewritten
to state argument order and nothing else is worse than the one it replaced.

---

## ⛔ ANTI-RULES — these apply on EVERY clause. Do NOT "fix" these.

* **`forbid X(R) :- X(R)` is SCHEMA-FORCED, not a defect.** An unconditional
  prohibition over a variable act requires the tautological binder. Do not
  "repair" it, and do not let entry 1's head-in-its-own-body test fire on it.

* **A `requires` entry that no module here provides is CORRECT on a
  single-clause module.** Moving the predicate into `inputs` to silence that
  destroys the distinction rule 9 calls load-bearing. This is the single most
  common false alarm on this corpus.

* **Never make `status` and `read_back` agree by REWRITING THE READ-BACK.** The
  two are written independently and that redundancy is the only place a wrong
  status is visible. **Fix the formal item.** ⚠️ The mechanism generalises: where
  any two independently written fields disagree — body vs read-back, gloss vs
  body, `claims` vs assert — the honest prose is usually the evidence and the
  formal item is usually the defect. Repair the formal item first, then update
  the prose's slots, and preserve its wording.
