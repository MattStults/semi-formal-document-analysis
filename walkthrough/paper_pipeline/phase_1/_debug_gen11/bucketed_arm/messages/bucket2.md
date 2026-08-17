PROCEDURE 2 of 4 — IS THE LOGICAL FORM RIGHT?

**Step 1. The "or" ledger.**
Find every occurrence of the word "or" in the narrowed SOURCE TEXT. For each
one, write the verb that governs it. Then run the cheap test on each:
**does satisfying ONE disjunct satisfy the span?**

* YES → the disjunction belongs inside ONE act, over an `ontology`-derived
  disjunction. Several `oblige` entries on one identical body is usually
  wrong here: *"use a tool …, hedge …, **or** explain"* became three obliges on
  one body, so an assistant that hedged violated two of them.
* NO → the verb has negative scope. *"refuse to A or B"* and *"avoid A or B"*
  are De Morgan: they mean *refuse A **and** refuse B*. **Separate asserts are
  CORRECT.** Leave them separate. This reflex has pointed the wrong way twice
  on this corpus.

Then list every pair of `asserts` entries that share an IDENTICAL body, and
every pair of `ontology` heads that share an IDENTICAL body. Coextensive heads
let the module oblige and forbid the same act on every instance. Different
heads need different bodies.

**Step 2. The scope ledger.**
For each assert, write its body conditions as a list. Beside it, quote the
substring of the span that qualifies that duty. Then write the two mismatches:

* a body condition with no quoted substring behind it → the rule is NARROWER
  than the span. If the span states the prohibition unconditionally, drop the
  condition.
* a quoted qualifier with no body condition → the rule is WIDER than the span.
  Add the condition.

⚠️ The counter-intuitive half, and it has bitten: a body condition added to
encode *"regardless of context"* or *"by default"* **WEAKENS** the rule. It
makes the rule fire only where that condition is affirmatively supplied, so a
situation that simply does not mention it derives nothing. If the phrase you
are encoding means "always", it is not a body condition.

**Step 3. The unification ledger.**
List every `ontology` entry whose body is null, and every ground atom (arity 0,
or every argument a constant). Beside each, write ONE concrete situation fact
that would unify with it, or NONE.

* `side_effect_examples(sending_email)` asserts a constant and nothing in a real
  situation can ever match it — inert for behaviour matching, which is the whole
  point of this corpus. An arity-0 atom (`no_moral_ambiguity`) is a proposition,
  not a property of a case, and cannot discriminate between cases at all.
* Where the span names a KIND of thing, prefer the bodied rule over a coined
  constant, and give it the argument the act's variable can bind.
* Reserve ground atoms for facts about the DOCUMENT (`root_authority(section_x)`),
  where there is no situation to match. Those are correct as they stand.

⛔⛔ **THE BODY MUST DISCRIMINATE. Run this gate before you change any atom
under this step.** Write down one concrete case that your proposed new body is
FALSE of. If you cannot name that case — if the only body you can write is one
every case satisfies, `no_moral_ambiguity(S) :- scenario(S)`, `x(S) :-
situation(S)` — then this step would take a clause scoped to *some* cases and
make it govern *all* of them. That is a worse defect than the inert constant you
started with. **Leave the atom exactly as it is**, and record in `claims` that
the span names a kind the narrowed text gives you no test for. **Never widen
what the clause governs in order to satisfy this step.**

---

⛔ ANTI-RULE that applies to this procedure. Do NOT "fix" this; changing it is
itself an error. **`forbid X(R) :- X(R)` is SCHEMA-FORCED, not a defect.** An
unconditional prohibition over a variable act requires the tautological binder.
Do not "repair" it and do not let step 1's identical-body test or step 3's
discrimination test fire on it.

Where a step's remedy would violate one of the twelve rules in my first
message, **the rule wins** — say what you found in `claims` rather than
encoding a remedy the format cannot carry.

Return the complete module object and nothing else.
