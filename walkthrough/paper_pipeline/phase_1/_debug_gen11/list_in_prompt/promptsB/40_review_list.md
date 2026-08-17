# The review list — run this on YOUR OWN module before you return it

Everything below was **measured on this corpus**, by a reviewer reading finished
modules against their spans. Each entry is a **question to ask**, not a
description of a rule. They are ordered by how often each one actually found
something in 17 reviewed clauses — run the top of the list hardest.

**How to use it.** Write your module. Then write it out and run these questions
against **the object you are about to return**, not against your intentions. The
entries that found the most were the ones the reviewer could only answer by
looking at the finished text. An entry you did not check is worse than one that
found nothing.

⚠️ Two of these entries were measured to make things **worse** when obeyed
literally, and both say so where they stand. Where an entry's remedy would
violate one of the twelve rules above, **the rule wins** — say what you found in
`claims` rather than encoding a remedy the format cannot carry.

---

## THE FIVE THAT FOUND THE MOST

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

---

## THE MIDDLE

### 6. Is every entry in `claims` actually encoded — and can the rule that encodes it ever FIRE?
*(7 of 17)* A claim listed in `claims` and present in no assert is the
fingerprint of dropped content. ⚠️ **Two known holes:** the check passes when
`claims` and `asserts` **agree and are both wrong**, and it passes a claim
encoded by a rule whose body nothing can ever supply. So run it as *encoded AND
reachable*, and re-read `claims` against the SPAN, not against your asserts.
⚠️ And when a claim is out of scope, the fix is to **delete the claim**, not to
add an assert for it.

### 7. Does the span hedge — and if you cannot encode the hedge, did you SAY SO?
*(7 of 17)* `toggleable` is reserved for `world` facts, so *"by default"*,
*"generally"*, *"should"*, *"may want to"* have nowhere to live except a body
condition. **An unconditional `oblige` is byte-identical to one whose default was
dropped.**
**Ask:** does the span hedge? Encode the defeater as a body condition **if the
span names one**; if it names none, say so explicitly in `claims` and in the
read-back. ⛔ **Do not invent a defeater to satisfy this** — see entry 14.

### 8. Does each body widen past the span's qualifier, or NARROW a prohibition the span states unconditionally?
*(7 of 17)* Measured in both directions on one module: it forbade every
recipe (too wide) while permitting every overview *including ones with specific
ratios* (too narrow, in the dangerous direction).
⚠️ **The counter-intuitive half:** a body condition added to encode *"regardless
of context"* or *"by default"* **WEAKENS** the rule — it makes the rule fire only
where that condition is affirmatively supplied, so a situation that simply does
not mention it derives nothing.

### 9. For each relation of arity ≥ 2, is the argument order stated in its gloss?
*(4 of 17)* A total inversion — `authority_levels_hierarchy(higher, lower)` vs
`(lower, higher)` — **passes every deterministic check that exists**. Write your
reading into the gloss so a mismatch surfaces as a disagreement instead of a
silent inversion. Applies to names you coin as well as names you borrow.

### 10. Does every name YOU COINED appear in some body?
*(4 of 17)* Anything in `ontology` or `inputs`, and any `requires` entry that is
**not** a `NEEDS` name. A coined name with no use is the fingerprint of dropped
content.
⛔ **A `NEEDS` name in `requires` and used nowhere is CONTRACT-REQUIRED. Leave it
alone.** ⚠️ Also check the converse: a coined name that duplicates a borrowed one
(one idea, two names, inside one module) is a defect even though both are used.

### 11. How many finite verbs does the narrowed text contain, and how many propositions does `ESTABLISHES` demand?
*(3 of 17)* Run this **before drafting**. Asked to justify four propositions from
a text containing two, every redraft MOVES the unanchored content instead of
removing it. Participial adjuncts (*"clarifying…"*, *"avoiding…"*) are not
coordinate finite duties unless they carry their own condition.

### 12. Does a `prefer` name the act to AVOID?
*(3 of 17)* `status` has **no negative pole**. Faced with *"avoid X"* the natural
move is `prefer X` with a read-back that negates it — so the compiled rule states
the OPPOSITE of the document. **Name the avoidance as the act**
(`prefer minimize_redundant_phrases`), or use `forbid` where the span is that
strong and the thing is not a gradient. Never leave `status` and `read_back`
disagreeing.

### 13. Is the bearer of the main verb the assistant?
*(0 findings in 17 — reported so you can weight it)* If the subject is OpenAI,
the document, a message, or a section, it is a FACT, not a norm; route it to
`ontology`. And **strip the matrix verb first**: *"**We're exploring how to** let
developers generate X"* has matrix verb *exploring*, subject OpenAI, and its
object is a rule — the span is ABOUT a rule and does not state one.
⚠️ This entry passing tells you the *bearer* is right. **It says nothing about
whether the STRENGTH is right** — `permit` where the span obliges passes it
cleanly. Ask that separately.

---

## ⛔ THE TWO ENTRIES MEASURED TO CAUSE HARM

### 14. "without X" as a positive predicate — **polarity-dependent**
Under negation-as-failure, `not X` makes SILENCE license the act, so rule 4 asks
for `omits_ratios_and_techniques(C)` rather than `not includes_ratios(C)`.
⛔ **MEASURED: obeying this correctly CREATED a clause's decisive defect.** In a
**permission's** body, demanding positive establishment is safe — you must prove
the absence to earn the permission. In an **obligation's** body, or on anything
encoding a **default**, it is the dangerous direction: you must prove the
condition to incur the duty, and **silence exempts**.
**Ask before applying it:** is the body I am adding this to a permission or an
obligation? If an obligation, prefer entry 7's "say so explicitly" branch.
⚠️ And entry 7 and this entry, obeyed **together**, are what produced that
defect. If both fire on the same construct, encode neither and record both in
`claims`.

### 15. "or" in the span
Several `oblige` on one identical body is usually wrong: *"use a tool …, hedge
…, **or** explain"* became three obliges on one body, so an assistant that
hedged violated two.
⛔ **But the reflex points the WRONG WAY under a negative-scope verb, measured
twice.** *"refuse to A or B"* and *"avoid A or B"* are De Morgan: they mean
*refuse A **and** refuse B*, so **separate asserts are correct**. The cheap test:
does satisfying one disjunct satisfy the span? If yes, one act over an
`ontology`-derived disjunction. If no, separate asserts.
⚠️ Also check the mirror: several `ontology` heads sharing ONE identical body are
**coextensive**, so the module can oblige and forbid the same act on every
instance. Different heads need different bodies.

---

## THE LOW-YIELD TAIL — run them, but they found little in 17 clauses

* **A qualifier inside a list bounds ONE item.** *"…, its chemical components
  **(without specific ratios)**, and its dangers"* — the parenthetical binds the
  middle item. ⚠️ Propagating "to be safe" invents a restriction; dropping it
  permits the unqualified case. ⚠️ Measured to point the wrong way twice: where
  the phrase is a **shared complement** of coordinated verbs, propagation is
  correct.
* **"regardless of X" has a destination and it is `forbid_body`.** Body-absence
  alone stops THIS module conditioning on X; nothing stops a later module adding
  the exception the span forbids. *(0 findings in 17.)*
* **A GOOD/BAD example pair must have DISJOINT arms.** The same `prefer` on the
  same act for both `good_response(R)` and `bad_response(R)` makes the compiled
  program unable to tell the poles apart — the one thing the example exists to
  say. *(1 finding in 17.)*

---

## ⛔ ANTI-RULES — do NOT "fix" these

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
