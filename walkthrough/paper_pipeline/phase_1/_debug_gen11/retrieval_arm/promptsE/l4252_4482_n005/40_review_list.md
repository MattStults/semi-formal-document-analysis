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

*(retrieved for this clause because: exemplifies a kind)*

### 5. Will a situation fact ever unify with this atom?
*(8 of 17)*

`side_effect_examples(E) :- sends_email(E)` classifies any real situation where
the assistant sends an email. `side_effect_examples(sending_email)` asserts a
constant, and **nothing in a real situation can ever match it** — inert for
behaviour matching, which is the whole point of this corpus. An arity-0 atom
(`no_moral_ambiguity`) is a proposition, not a property of a case, and cannot
discriminate between cases at all.

**Ask, of every `ontology` entry:** if the span names a KIND of thing, prefer the
bodied rule over a coined constant, and give it the argument the act's variable
can bind. Reserve ground atoms for facts about the **DOCUMENT**
(`root_authority(section_x)`), where there is no situation to match.

⛔ **STOP CONDITION — this entry was measured to MANUFACTURE a defect when the
"prefer a bodied rule" half was obeyed on the wrong kind of atom.** Giving an
atom a body over a universal type predicate does not make it discriminate; it
makes it **vacuous**, and vacuous is strictly worse than inert. `no_moral_ambiguity(S)
:- scenario(S)` says *every* scenario has no moral ambiguity, so a clause the
span scoped to "scenarios where there's no moral ambiguity" comes out governing
**ALL** scenarios. Inert wastes a symbol; vacuous rewrites the document.

**Two tests before you convert anything:**
1. **Is the atom a SCOPE CONDITION of this clause, or a KIND the clause talks
   about?** A scope condition (the "where there is no moral ambiguity" in
   *"in scenarios where there's no moral ambiguity, do X"*) belongs in the
   **body** of the rule it restricts, left undefined and declared in `inputs` or
   `requires`. It is **not** an `ontology` entry to be given a definition.
   Only convert a KIND the span names in its own right.
2. **Would the body be true of everything?** If the body you are about to write
   is a universal type predicate — `scenario(S)`, `situation(S)`, `case(S)`,
   `response(R)`, `act(A)` — with no further condition drawn from the span,
   **do not write the rule at all.** Leave the atom undefined and use it as a
   condition. An undefined condition is honest; a vacuous definition is a false
   claim about the document.

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
