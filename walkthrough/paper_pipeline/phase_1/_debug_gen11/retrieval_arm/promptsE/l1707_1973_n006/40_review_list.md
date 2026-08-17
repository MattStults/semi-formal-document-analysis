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

*(retrieved for this clause because: ESTABLISHES adds 12 content words; span has 60 words ESTABLISHES drops)*

### 4. Is every asserted predicate supported by the NARROWED text?
*(8 of 17)*

Where `ESTABLISHES` and the narrowed `SOURCE TEXT` conflict, **the narrowed
`SOURCE TEXT` governs.** `ESTABLISHES` may direct *which* claim of the span you
express; it may not **add** content the span does not state, and it may not
**drop** a qualifier the span does state (measured: it restated a permission with
the span's own parenthetical deleted).

**Ask, in both directions:** what does `ESTABLISHES` say that the span does not,
and what does the span say that `ESTABLISHES` drops? Anything `ESTABLISHES`
adds is still expressible — as `assumed`, with the `inference` naming
`ESTABLISHES` as its source. **Nothing is lost, only marked.**
⚠️ Vocabulary that appears in the node's own `PROVIDES`/`NEEDS` glosses is not
thereby "outside the narrowing" — check the source text, not your memory of the
node header.

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

*(retrieved for this clause because: ESTABLISHES demands ~3 propositions; long span (multiple claims likely))*

### 6. Is every entry in `claims` actually encoded — and can the rule that encodes it ever FIRE?
*(7 of 17)* A claim listed in `claims` and present in no assert is the
fingerprint of dropped content. ⚠️ **Two known holes:** the check passes when
`claims` and `asserts` **agree and are both wrong**, and it passes a claim
encoded by a rule whose body nothing can ever supply. So run it as *encoded AND
reachable*, and re-read `claims` against the SPAN, not against your asserts.
⚠️ And when a claim is out of scope, the fix is to **delete the claim**, not to
add an assert for it.

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
