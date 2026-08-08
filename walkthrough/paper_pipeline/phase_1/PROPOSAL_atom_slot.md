# The dominant prompt defect — what it is, and one hypothesis I refuted myself

**For your review. NOTHING IMPLEMENTED: any fix here edits `prompt/10_output_format.md`, a
watched transcription.** Written 2026-08-07 from the held-out eval.

---

## The defect

**59 occurrences over 36 first attempts** on six clauses never used for diagnosis — more
than the next two causes combined. The model writes a whole rule into `atom`, a slot holding
one term:

> `ontology atom: 'conversation(C) :- valid_input(C)' is not a term. It must be a functor…`

## ⭐ It is CLAUSE-CONCENTRATED, not diffuse — the most useful thing here

Only **2 of the 6 clauses** produce it. Those two produce it on **every single attempt**,
all 12, in both arms:

| clause | attempts affected | rules per attempt | shape |
|---|---|---|---|
| m0055 · definitional | 6 of 6 | 4, every time | **conjunctive** |
| m0293 · definitional | 6 of 6 | 7–12 | mixed, incl. **disjunctive** |
| m0445, m0495, m0531, m0544 | ~0 | — | — |

⇒ This is not a prompt the model half-follows. It is a prompt that fails **totally and
reproducibly on a particular kind of clause** and barely at all on the rest. Both are
`definitional`; both are the only two `definitional` clauses in the eval set.

**That is the finding to act on**, and it points somewhere a re-wording will not reach: the
defect tracks the clause type, not the instruction's clarity.

## ⛔ The prompt already forbids this, in the exact rejected form

`10_output_format.md` carries a worked example of the correct split and this line:

> ⚠️ `"atom": "system_rule(R) :- set_by_openai(R)"` is rejected — `atom` holds a single term,
> and the conditions belong in `body`.

m0105's self-diagnosis quotes that sentence and says *"The instructions were clear on this
point… I simply misapplied that guidance."* ⇒ **Any fix that amounts to saying it again
louder is proposing to repeat an instruction the model can quote back.**

## The hypothesis I formed, and the check that refuted it

**Hypothesis:** the model reaches for *"P if A, or P if B"* — alternative sufficient
conditions — and the prompt shows only a **conjunctive** body, never says an atom may be
repeated with a second body, so writing the whole rule looks like the only route.

Two things supported it. m0105 states that intent in its own words (*"two alternative
sufficient conditions"*). And the route does exist but is undocumented — verified directly
against `schema.validate_all` and `render_lp`, two entries with the same atom and different
bodies are accepted and render correctly:

```
unclear_provenance(X) :- o, pasted_unread(X).        % [T] m0001
unclear_provenance(X) :- o, from_corrupt_page(X).    % [T] m0001
```

⛔ **Then I tested it within single attempts, and it does not hold as the cause.** Only **4
of 12** affected attempts repeat a head at all, and **all four are m0293**. m0055 writes four
rules into four atom slots every time, with four *different* heads and plainly **conjunctive**
bodies:

```
conversation(C)     :- valid_input(C)
message(M)          :- conversation(C), in_conversation(M, C)
message_role(M, R)  :- message(M), role_of(M, R)
message_content(M,C):- message(M), content_of(M, C)
```

That is **exactly the shape the worked example covers**. The route was documented, and the
model did not take it. ⇒ The disjunction gap is real and worth closing on its own merits, but
**it is not the cause**, and I would have shipped it as one had I not run the within-attempt
check. Recorded because the aggregate — "90% of distinct rules belong to a repeated head" —
read as strong support and was an artefact of pooling six attempts.

## Where that leaves it

The evidence supports one narrow change and does **not** yet identify the main cause.

**Worth doing on its own merits** — documents a capability the schema already has:

> ⭐ **A concept with two independent sufficient conditions gets TWO entries with the same
> `atom` and different bodies.** Repeating an atom is how you say "or"; there is no
> disjunction inside a body. `"body": "a(I) ; b(I)"` and
> `"atom": "p(I) :- a(I)"` are both rejected.

**Not yet identified:** why a clause that defines several concepts at once — m0055 defines
*conversation*, *message*, *role*, *content* in 154 characters — reliably produces rules in
atom slots when the same model handles conditional clauses correctly. ⚠️ **I have a guess and
no evidence: a multi-concept definitional clause may push the model toward "write the
ontology" rather than "fill in the fields."** Do not act on that until someone tests it.

**The cheapest next probe**, and it costs nothing: `self_diagnose.py` against m0055's
transcript, which is the case where the model had a documented route and did not take it.

## How to decide any of it

⛔ **Not on these six clauses.** They are now the diagnosis set. This run already showed the
cost: the `read_back` fix read as *eliminated* (6 → 0) on the clauses it was tuned on and
recurs 18 times held-out (`eval_arms/RESULT_licence_emphasis.md`).

⇒ Fresh draw — change the salt in `heldout.provenance.json` — pre-register the atom-slot
cluster count, run both arms, ~$0.05. **Pre-register the falsifier:** if the cluster does not
fall, the shape was not the cause and the text is one more paragraph for nothing.

## What I did not do, and why

I did not edit the prompt. It is a watched transcription; editing one without review is the
failure that cost the most in this project's history. And on the evidence above I would have
been fixing a real-but-secondary gap while reporting it as the cause.
