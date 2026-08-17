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

*(retrieved for this clause because: exception marker)*

### 2. An "unless" arm is a HOLE, not a rule — and a `cepa` closure re-asserts the silence you declined to break
*(10 of 17)*

*"should honor … **unless** it conflicts"* **WITHDRAWS** a requirement on the
excepted branch. It does not create a prohibition there. Adding `forbid` on that
branch asserts something the span never says.

The same reasoning governs `closure`. If the clause states a duty inside one
trigger and takes no position outside it, then reading its silence as blanket
permission (`cepa`) is a commitment the clause never made — **use `unclear`.**
Measured: `cepa` was the wrong value on four separate clauses, and its stated
reason was circular on a fifth (*"it does not forbid other answers, so silence
permits them"* is `cepa` justifying `cepa`).

**Ask:** does an "unless" arm carry its own assert? Does any `closure` value
decide something the span left open? Is the closure's `reason` drawn from the
span, or from the module?

*(retrieved for this clause because: a NEEDS/PROVIDES gloss describes a relation; span states an ordering/conflict between two things)*

### 9. For each relation of arity ≥ 2, is the argument order stated in its gloss?
*(4 of 17)* A total inversion — `authority_levels_hierarchy(higher, lower)` vs
`(lower, higher)` — **passes every deterministic check that exists**. Write your
reading into the gloss so a mismatch surfaces as a disagreement instead of a
silent inversion. Applies to names you coin as well as names you borrow.

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
