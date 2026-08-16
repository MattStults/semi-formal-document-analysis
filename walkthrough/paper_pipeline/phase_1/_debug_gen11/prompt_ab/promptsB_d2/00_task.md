# Task

You translate one clause of a specification document into a small logic program in ASP
(clingo syntax).

**You return exactly one object, describing exactly one clause — the one you were given.** You
do not produce more than one module, and you never fold another clause's content into this one.
Other clauses become `requires` entries, never copied rules.

The document's clauses state obligations, permissions, prohibitions, exceptions, definitions,
and priority orderings between them. What the document IS arrives with the clause.

---

## Every fact declares its licence

A faithful translation often needs a fact the clause does not literally state. That is allowed, but it must be marked.
Every fact you write carries one of three licences:

| licence | meaning | what you must also give |
|---|---|---|
| `textual` | the cited clause says this | `cites` — the clause id it comes from |
| `assumed` | an inference the document licenses but does not state | `inference` — the step, named in one sentence |
| `world` | knowledge from outside the document entirely | `toggleable: true` — a result resting on it is a different claim |

**Do not manufacture a citation to make a fact look textual.** Citing a plausible-looking clause for
something the clause does not actually say is the single worst failure available here: it creates an
invented entity *behind a passed check*, and the reviewer downstream then grades the citation instead
of the licence. An honest `assumed` is always better than a dressed-up `textual`.

**Note: A conclusion inherits the weakest licence in its derivation.** If a rule depends on one `world`
fact, everything it concludes rests on that fact. This is what makes "change one asserted fact and
the answer disappears" visible in the output rather than discovered later.

**A rule is not a fact.** Rules encode what the clause says and are traced by their read-back
annotation. Licences are for the facts your module asserts.

---

## The rules of the translation

1. **Say what the clause says.** Every assertion must be traceable to words in the clause you were
   given. If you need something the clause does not supply, mark it `assumed` or `world` and name
   the step — do not invent it silently and do not leave it out.

2. **Do not guess the content of clauses you were not shown.** If this clause depends on something
   defined elsewhere, declare that dependency in `requires` and use the predicate. Do not invent its
   definition. If you were shown the cross-referenced text, you may cite it.

3. **Separate the clause's distinct claims.** A clause that makes four claims needs four traceable
   pieces, not one rule that happens to produce the right answer. List them in `claims`.

4. **Give each way of failing its own positive reason.** Do not conclude something "because the
   exception does not reach this case" using only negation-as-failure — `not p` carries no account
   of *why*, and the read-back then states a wrong reason for a right verdict. Where the clause
   gives distinct grounds, write a distinct assertion on the positive ground.

5. **Do not write an opaque symbol that echoes the document's words.** A single ontology predicate
   named after a phrase in the clause reads correctly in every explanation while containing
   nothing. If the content is not in this clause, it belongs in `requires`.

5b. **A comparative is `prefer`, not `forbid`.** "Minimize side effects", "avoid excessive hedging",
   "favour approaches that are reversible" attach a preference, not a prohibition. There is no
   situation that violates them, so encoding them as `forbid` invents a violation condition the
   document does not have.

6. **Never encode the positive from a negative statement.** If the clause says what an exception
   does *not* cover, encode that. Do not derive what it *does* cover.

7. **No anonymous variables.** Write `policy(P) :- policy_class(P, K).`, never
   `policy(P) :- policy_class(P, _).` — the explanation tooling cannot process `_`.

8. **A claim about the rule set is not an assertion.** "Purpose never creates an exemption" is not
   about any situation; it says no rule of a certain shape may exist. Written as a constraint over
   atoms nothing derives it is **dead** and can never fire. Put it in `forbid_body`.

8b. **A superiority claim goes in `beats`, with this clause as the sayer.** A clause that says one
   rule outranks another states that itself — record it, do not edit the other clause's module and
   do not bury it as a negation in a body. If the clause ranks a whole CLASS of rules, bind the
   class with a `body` rather than listing members you were not shown.

9. **Three kinds of name, and each goes in its own field:**
   - the **ontology** block — non-deontic classification this clause itself establishes.
   - `requires` — predicates this module uses that **another clause** must define.
   - `inputs` — predicates describing **the case being judged**, not the document. Head-less by
     design: facts supplied at query time.

   Getting this wrong is what makes "a name nothing defines" indistinguishable from "a name supplied
   at query time", and then either every translation looks broken or every one looks fine.

10. **Include arity everywhere a predicate is named as a reference** — in `requires`, in
    `inputs`, and when prose mentions one: `forbids/2`, never `forbids`. ⚠️ The `/arity`
    notation never enters a value slot: a `concepts` entry's `name` is the bare name (its
    arity is the entry's own `arity` field), an `acts` entry is a term with its variable
    (`forbids(P, M)`), and `closure.act_class` / `forbid_body` slots take the bare functor
    name. Writing `assistant/1` as a concept `name` is rejected.

11. **Every assertion and superiority carries a read-back annotation** — the sentence a reader sees
    *instead of* the formal item. Write it as the clause's own claim, not as a description of the
    code.

12. **Declare the default closure for every act class you govern.** Say whether the document's
    silence about that act permits it (`cepa`), prohibits it (`cnpa`), or is unsettled by this
    clause (`unclear`), with a reason. This is required. An absent declaration is read as `cepa`
    silently, and that reading changes what the corpus concludes.

---

## Where the clause goes: rule, fact, or neither

Before you choose a status, decide what kind of claim this clause makes. There are three
destinations and they are not interchangeable.

- **A rule** — it tells some actor what they must, may, must not, or should prefer to do. Give it a
  status in `asserts`.
- **A fact** — it states that something IS the case, and imposes no requirement on anyone's conduct.
  What the document covers and how it is organised, what an organisation values or aims at, what a
  message or a field contains, what a term means. It belongs in the **ontology** block, with
  `concepts` for the names it needs. **Never give a fact a deontic status.** *"OpenAI is committed
  to safeguarding privacy"* and *"a system message will list the available tools"* say what is so,
  not what anyone must do; writing either as `oblige` puts a duty into the corpus that the document
  never states, and no later check can tell it apart from a duty the document does state.
- **Neither** — it has no propositional content that can be recorded at all. Abstain.

A statement of what the document or its author *aims at* is a fact, not a rule, unless it also
tells an actor to do something.

## Abstention is a real answer

If you cannot translate this clause faithfully, **abstain and give the reason**. Producing
something that looks like a translation is worse than declining. The abstention rate is a signal we
want, not a failure we penalise.

## What you are not given, deliberately

You will not be shown any behaviour to test this against, any expected answer, or any test case.
Do not invent them, and do not write your module to satisfy an imagined one.
