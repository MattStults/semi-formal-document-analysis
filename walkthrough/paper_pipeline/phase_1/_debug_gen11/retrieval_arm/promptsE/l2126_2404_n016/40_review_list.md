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

*(retrieved for this clause because: node narrows its span; PROVIDES empty -> every name is coined)*

### 3. Does every symbol you COINED trace to a substring of the narrowed text?
*(10 of 17)*

If the node prints `[node narrows this span to: "…"]`, the text around it is
context, not licence. The constant `tiananmen_example` was fluent, obviously
right to anyone who had read the section, and **unanchored** — the narrowed text
named no event. `answers_user_question` was coined for a span containing neither
*user* nor *question*.

**Ask, for each name you coin:** which substring of the NARROWED text does it
come from? If none, you are importing knowledge your citation cannot support.
⚠️ **Two known blind spots in this check, so run it on more than the name:**
(i) run it on the **gloss** too — a name can trace while its gloss imports
material from a neighbouring sentence; (ii) a **fused** name
(`exaggerated_or_stereotypical`) can be assembled from three separate legitimate
substrings and still weld a disjunction into one opaque symbol (see rule 5).

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
