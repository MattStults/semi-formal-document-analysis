STOP. Do not rewrite the module yet.

Re-read the SOURCE TEXT in my first message. Then check the module you just
returned against each of the eleven questions below.

Reply with EXACTLY eleven lines and nothing else, one per question, in this form:

E1: PASS
E2: FIX — <one sentence: the exact field, and the exact change to make>
E3: PASS

Rules for your reply:
* "FIX" means your module is wrong on that question. "PASS" means you checked
  the finished text and it is right.
* Never write "N/A", "unsure", or "partially". If the question does not apply to
  this clause, write PASS.
* A FIX line is an instruction to yourself. Name the field. Name the new value.
  One sentence. Do not explain.
* Check the object you are about to return, not your intentions.
* Do not output any JSON in this reply.

Every question below was measured on this corpus by a reviewer reading finished
modules against their spans, and they are ordered by how often each one actually
found something. Run the top of the list hardest.

---

**E1. Does a `gloss` restate its predicate's name instead of defining it?**

`safety_precaution_suggestion/1` glossed *"S is a suggestion that the user take
safety precautions"* is **the name, re-spaced**. Same for *"T is a transformation
task"*, *"S is an interactive setting"*, *"A is a straightforward answer"*.
A gloss is the **only** way another module's definition can ever be matched to
yours; one that restates the name passes zero information.

Ask, of every `concepts` and `ontology` gloss: does it say what makes the
predicate TRUE, in words that are not the name? For an arity ≥ 2 relation, does
it say which argument is which? Also ask: does any rule's head appear in its own
body?
⚠️ Do not *replace* a gloss to satisfy this — **add** to it. A gloss rewritten
to state argument order and nothing else is worse than the one it replaced.

**E2. An "unless" arm is a HOLE, not a rule — and a `cepa` closure re-asserts the silence you declined to break.**

*"should honor … **unless** it conflicts"* **WITHDRAWS** a requirement on the
excepted branch. It does not create a prohibition there. Adding `forbid` on that
branch asserts something the span never says.

The same reasoning governs `closure`. If the clause states a duty inside one
trigger and takes no position outside it, then reading its silence as blanket
permission (`cepa`) is a commitment the clause never made — **use `unclear`.**
Measured: `cepa` was the wrong value on four separate clauses, and its stated
reason was circular on a fifth (*"it does not forbid other answers, so silence
permits them"* is `cepa` justifying `cepa`).

Ask: does an "unless" arm carry its own assert? Does any `closure` value decide
something the span left open? Is the closure's `reason` drawn from the span, or
from the module?

**E3. Does every symbol you COINED trace to a substring of the narrowed text?**

If the node prints `[node narrows this span to: "…"]`, the text around it is
context, not licence. The constant `tiananmen_example` was fluent, obviously
right to anyone who had read the section, and **unanchored** — the narrowed text
named no event. `answers_user_question` was coined for a span containing neither
*user* nor *question*.

Ask, for each name you coin: which substring of the NARROWED text does it come
from? If none, you are importing knowledge your citation cannot support.
⚠️ Two known blind spots, so run it on more than the name: (i) run it on the
**gloss** too — a name can trace while its gloss imports material from a
neighbouring sentence; (ii) a **fused** name (`exaggerated_or_stereotypical`) can
be assembled from three separate legitimate substrings and still weld a
disjunction into one opaque symbol.

**E4. Is every asserted predicate supported by the NARROWED text?**

Where `ESTABLISHES` and the narrowed `SOURCE TEXT` conflict, **the narrowed
`SOURCE TEXT` governs.** `ESTABLISHES` may direct *which* claim of the span you
express; it may not **add** content the span does not state, and it may not
**drop** a qualifier the span does state.

Ask, in both directions: what does `ESTABLISHES` say that the span does not, and
what does the span say that `ESTABLISHES` drops? Anything `ESTABLISHES` adds is
still expressible — as `assumed`, with the `inference` naming `ESTABLISHES` as
its source. **Nothing is lost, only marked.**
⚠️ Vocabulary that appears in the node's own `PROVIDES`/`NEEDS` glosses is not
thereby "outside the narrowing" — check the source text, not your memory of the
node header.

**E5. Will a situation fact ever unify with this atom?**

`side_effect_examples(E) :- sends_email(E)` classifies any real situation where
the assistant sends an email. `side_effect_examples(sending_email)` asserts a
constant, and **nothing in a real situation can ever match it** — inert for
behaviour matching, which is the whole point of this corpus. An arity-0 atom
(`no_moral_ambiguity`) is a proposition, not a property of a case, and cannot
discriminate between cases at all.

Ask, of every `ontology` entry: if the span names a KIND of thing, prefer the
bodied rule over a coined constant, and give it the argument the act's variable
can bind. Reserve ground atoms for facts about the **DOCUMENT**
(`root_authority(section_x)`), where there is no situation to match.

⛔⛔ **THE BODY MUST DISCRIMINATE. This entry has one measured failure mode and it
is severe.** If the only body you can write is one that every case satisfies —
`no_moral_ambiguity(S) :- scenario(S)`, `x(S) :- situation(S)` — then obeying
this entry has taken a clause scoped to *some* cases and made it govern *all* of
them. That is a worse defect than the inert constant you started with. **Before
you change anything here, ask: is there a case this body is FALSE of?** If there
is not, **leave the atom exactly as it is** and record in `claims` that the span
names a kind the narrowed text gives you no test for. **Never widen what the
clause governs in order to satisfy E5.**

**E6. Is every entry in `claims` actually encoded — and can the rule that encodes it ever FIRE?**

A claim listed in `claims` and present in no assert is the fingerprint of dropped
content. ⚠️ Two known holes: the check passes when `claims` and `asserts` **agree
and are both wrong**, and it passes a claim encoded by a rule whose body nothing
can ever supply. So run it as *encoded AND reachable*, and re-read `claims`
against the SPAN, not against your asserts.
⚠️ And when a claim is out of scope, the fix is to **delete the claim**, not to
add an assert for it.

**E7. Does the span hedge — and if you cannot encode the hedge, did you SAY SO?**

`toggleable` is reserved for `world` facts, so *"by default"*, *"generally"*,
*"should"*, *"may want to"* have nowhere to live except a body condition. **An
unconditional `oblige` is byte-identical to one whose default was dropped.**
Ask: does the span hedge? Encode the defeater as a body condition **if the span
names one**; if it names none, say so explicitly in `claims` and in the
read-back. ⛔ **Do not invent a defeater to satisfy this.**

**E8. Does each body widen past the span's qualifier, or NARROW a prohibition the span states unconditionally?**

Measured in both directions on one module: it forbade every recipe (too wide)
while permitting every overview *including ones with specific ratios* (too
narrow, in the dangerous direction).
⚠️ The counter-intuitive half: a body condition added to encode *"regardless of
context"* or *"by default"* **WEAKENS** the rule — it makes the rule fire only
where that condition is affirmatively supplied, so a situation that simply does
not mention it derives nothing.

**E9. For each relation of arity ≥ 2, is the argument order stated in its gloss?**

A total inversion — `authority_levels_hierarchy(higher, lower)` vs
`(lower, higher)` — **passes every deterministic check that exists**. Write your
reading into the gloss so a mismatch surfaces as a disagreement instead of a
silent inversion. Applies to names you coin as well as names you borrow.

**E10. Does a `prefer` name the act to AVOID?**

`status` has **no negative pole**. Faced with *"avoid X"* the natural move is
`prefer X` with a read-back that negates it — so the compiled rule states the
OPPOSITE of the document. **Name the avoidance as the act**
(`prefer minimize_redundant_phrases`), or use `forbid` where the span is that
strong and the thing is not a gradient. Never leave `status` and `read_back`
disagreeing.

**E11. "or" in the span.**

Several `oblige` on one identical body is usually wrong: *"use a tool …, hedge
…, **or** explain"* became three obliges on one body, so an assistant that
hedged violated two.
⛔ But the reflex points the WRONG WAY under a negative-scope verb, measured
twice. *"refuse to A or B"* and *"avoid A or B"* are De Morgan: they mean
*refuse A **and** refuse B*, so **separate asserts are correct**. The cheap test:
does satisfying one disjunct satisfy the span? If yes, one act over an
`ontology`-derived disjunction. If no, separate asserts.
⚠️ Also check the mirror: several `ontology` heads sharing ONE identical body are
**coextensive**, so the module can oblige and forbid the same act on every
instance. Different heads need different bodies.

---

## ⛔ ANTI-RULES — do NOT "fix" these. Marking any of them FIX is itself an error.

* **`forbid X(R) :- X(R)` is SCHEMA-FORCED, not a defect.** An unconditional
  prohibition over a variable act requires the tautological binder. Do not
  "repair" it, and do not let E1's head-in-its-own-body test fire on it.
* **A `requires` entry that no module here provides is CORRECT on a
  single-clause module.** Moving the predicate into `inputs` to silence that
  destroys the distinction rule 9 calls load-bearing. This is the single most
  common false alarm on this corpus. A `NEEDS` name in `requires` that is used
  nowhere is CONTRACT-REQUIRED — leave it alone.
* **Never make `status` and `read_back` agree by REWRITING THE READ-BACK.** The
  two are written independently and that redundancy is the only place a wrong
  status is visible. **Fix the formal item.** ⚠️ The mechanism generalises: where
  any two independently written fields disagree — body vs read-back, gloss vs
  body, `claims` vs assert — the honest prose is usually the evidence and the
  formal item is usually the defect. Repair the formal item first, then update
  the prose's slots, and preserve its wording.

Where an entry's remedy would violate one of the twelve rules in my first
message, **the rule wins** — say what you found in `claims` rather than encoding
a remedy the format cannot carry.

Eleven lines. Nothing else.
