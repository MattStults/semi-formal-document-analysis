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

*(retrieved for this clause because: ESTABLISHES demands ~3 vs 2 finite verbs in span; participial adjunct)*

### 11. How many finite verbs does the narrowed text contain, and how many propositions does `ESTABLISHES` demand?
*(3 of 17)* Run this **before drafting**. Asked to justify four propositions from
a text containing two, every redraft MOVES the unanchored content instead of
removing it. Participial adjuncts (*"clarifying…"*, *"avoiding…"*) are not
coordinate finite duties unless they carry their own condition.

*(retrieved for this clause because: explicit hedge lexeme)*

### 7. Does the span hedge — and if you cannot encode the hedge, did you SAY SO?
*(7 of 17)* `toggleable` is reserved for `world` facts, so *"by default"*,
*"generally"*, *"should"*, *"may want to"* have nowhere to live except a body
condition. **An unconditional `oblige` is byte-identical to one whose default was
dropped.**
**Ask:** does the span hedge? Encode the defeater as a body condition **if the
span names one**; if it names none, say so explicitly in `claims` and in the
read-back. ⛔ **Do not invent a defeater to satisfy this** — see entry 14.

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
