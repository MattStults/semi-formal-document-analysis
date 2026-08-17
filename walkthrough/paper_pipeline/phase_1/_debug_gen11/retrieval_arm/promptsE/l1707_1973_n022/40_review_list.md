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

*(retrieved for this clause because: explicit hedge lexeme)*

### 7. Does the span hedge — and if you cannot encode the hedge, did you SAY SO?
*(7 of 17)* `toggleable` is reserved for `world` facts, so *"by default"*,
*"generally"*, *"should"*, *"may want to"* have nowhere to live except a body
condition. **An unconditional `oblige` is byte-identical to one whose default was
dropped.**
**Ask:** does the span hedge? Encode the defeater as a body condition **if the
span names one**; if it names none, say so explicitly in `claims` and in the
read-back. ⛔ **Do not invent a defeater to satisfy this** — see entry 14.

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

*(retrieved for this clause because: avoidance/negative-pole verb)*

### 12. Does a `prefer` name the act to AVOID?
*(3 of 17)* `status` has **no negative pole**. Faced with *"avoid X"* the natural
move is `prefer X` with a read-back that negates it — so the compiled rule states
the OPPOSITE of the document. **Name the avoidance as the act**
(`prefer minimize_redundant_phrases`), or use `forbid` where the span is that
strong and the thing is not a gradient. Never leave `status` and `read_back`
disagreeing.

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
