# Worked examples — the good ones, then six bad

The good one is transcribed from `contradiction_probe/doc.lp`, which is 14 clauses hand-encoded in
this vocabulary and which runs.

## The good one

Clause `m0255`, section `transformation_exception`:

> "The transformation exception does not override any policies other than those on
> [restricted](#restricted_content) or [sensitive content](#sensitive_content); if other policies
> forbid producing certain material, the assistant should still follow them. There is no "good
> cause" exception for the restricted and sensitive content policies, and the assistant should not
> supply new disallowed material even for seemingly legitimate research or analysis purposes. The
> policy only applies to *information*, not actions; the assistant should not perform a prohibited
> action just because it's a "translation" of user-provided content."

This clause is the hardest case in the corpus: it ranks a **class** of other clauses above one
clause, while naming no individual clause and editing no module. That is what `beats` is for.

```json
{
  "outcome": "translated",
  "clause_id": "m0255",
  "abstain_reason": null,
  "claims": [
    "C1 the transformation exception's scope is exactly {restricted, sensitive}",
    "C2 policies outside that scope still bind",
    "C3 purpose ('good cause', research, analysis) never lifts a policy",
    "C4 the exception covers INFORMATION only, never ACTIONS"
  ],
  "acts": ["produce(M)"],
  "concepts": [
    { "name": "content_policy_rule", "arity": 1,
      "gloss": "a clause of this document that states one of its content policies",
      "licence": "assumed", "cites": null,
      "inference": "the clause speaks of 'other policies', which are the ones other clauses state",
      "toggleable": false },
    { "name": "asserts_policy", "arity": 2,
      "gloss": "the clause whose subject is the named policy",
      "licence": "assumed", "cites": null,
      "inference": "identifying which clause states which policy is what 'other policies' ranges over",
      "toggleable": false }
  ],
  "ontology": [
    { "atom": "content_policy_rule(m0203)", "body": null,
      "gloss": "a clause that states one of the document's content policies",
      "licence": "assumed", "cites": null,
      "inference": "m0203 states a policy on prohibited content, so it is one of the 'other policies' this clause defers to",
      "toggleable": false },
    { "atom": "content_policy_rule(m0208)", "body": null,
      "gloss": "a clause that states one of the document's content policies",
      "licence": "assumed", "cites": null,
      "inference": "m0208 states a policy on restricted content, so it is one of the 'other policies' this clause defers to",
      "toggleable": false },
    { "atom": "asserts_policy(m0203, prohibited_content)", "body": null,
      "gloss": "the clause whose subject is this named policy",
      "licence": "assumed", "cites": null,
      "inference": "m0203's subject is the prohibited-content policy",
      "toggleable": false },
    { "atom": "asserts_policy(m0208, restricted_content)", "body": null,
      "gloss": "the clause whose subject is this named policy",
      "licence": "assumed", "cites": null,
      "inference": "m0208's subject is the restricted-content policy",
      "toggleable": false }
  ],
  "asserts": [
    { "status": "forbid", "act": "produce(M)",
      "body": "new_material(M), disallowed(M)",
      "read_back": "purpose gives no exemption: producing % is new disallowed material",
      "read_back_slots": ["M"],
      "licence": "textual", "cites": "m0255",
      "inference": null, "toggleable": false }
  ],
  "beats": [
    { "sayer": "m0255", "winner": "R", "loser": "m0252",
      "body": "content_policy_rule(R), policy_class(P, K), out_of_scope(transformation, K), asserts_policy(R, P)",
      "read_back": "% outranks the transformation exception, because the exception does not reach its policy class",
      "read_back_slots": ["R"],
      "licence": "textual", "cites": "m0255",
      "inference": null, "toggleable": false }
  ],
  "defines": [],
  "closure": [
    { "act_class": "produce", "closure": "cepa",
      "reason": "the clause carves out from a prohibition rather than extending one; it says which policies still bind, so silence about a policy leaves the transformation permission standing" }
  ],
  "requires": ["policy_class/2", "scope/2", "out_of_scope/2", "disallowed/1"],
  "inputs": ["new_material/1"],
  "forbid_body": [ { "head": "permit", "banned": "purpose" } ]
}
```

Five things to notice.

**The act is indexed.** `produce(M)` — an act, never a material. `forbids(Policy, Material)` cannot
join anything on the query side; the join silently never fires and no conflict is ever derived.

**`beats` carries the sayer, and is quantified.** `beats(m0255, R, m0252)` with a body binding `R`
over a class of clauses. The sayer is what makes an override reachable at all: the clause *states*
the override, and nothing else records who said it.

**Concepts are declared, facts are asserted, and they are different things.**
`content_policy_rule/1` is *declared* in `concepts` with its meaning; the four
`content_policy_rule(m0203)`-style entries in `ontology` are the *instances*. A declaration asserts
nothing and never appears in the logic — it goes to the concept table.

**The ontology block is non-deontic.** It classifies; it attaches no status. Kept apart so it can be
ablated.

**Non-textual facts are marked, not deleted.** The four ontology facts are `assumed`, each with its
inference named. Deleting them, or citing m0255 for them, are both wrong.

**The closure is declared.** Silence about a policy has to mean something, and if you do not say
what, it silently means CEPA — whatever is not forbidden is permitted — and that flips downstream
verdicts with nothing recording that a commitment was made.

### A definitional clause, for contrast

Clause `m0204`: *"only sexual content involving minors is considered prohibited."* Pure definition;
attaches no status; fixes the extension another clause quantifies over.

```json
{ "outcome": "translated", "clause_id": "m0204", "abstain_reason": null,
  "claims": ["C1 the extension of `prohibited` is exactly csam"],
  "acts": [], "concepts": [], "ontology": [], "asserts": [], "beats": [],
  "defines": [ { "kind": "prohibited", "term": "csam",
                 "licence": "textual", "cites": "m0204",
                 "inference": null, "toggleable": false } ],
  "closure": [], "requires": [], "inputs": [], "forbid_body": [] }
```

No acts, so no closure declaration is due. That one is easy because the term has a fixed
extension. Most definitions do not.

### A definitional clause that needs RULES, which is the common case

Clause `m0088`: *"a candidate instruction is not applicable to the request if it is misaligned with
an applicable higher-level instruction, superseded by an instruction in a later message at the same
level, or suspected to be mistaken."*

This term has no fixed extension. It is defined by three conditions, any one of which is enough. So
it is not a `defines` entry — it is three `ontology` entries.

```json
{ "outcome": "translated", "clause_id": "m0088", "abstain_reason": null,
  "claims": ["C1 not applicable if misaligned with an applicable higher-level instruction",
             "C2 not applicable if a later message at the same level supersedes it",
             "C3 not applicable if it is suspected to be mistaken"],
  "acts": [], "asserts": [], "beats": [], "defines": [], "closure": [], "requires": [],
  "concepts": [
    { "name": "not_applicable", "arity": 2, "gloss": "candidate instruction I is not applicable to request R",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "candidate_instruction", "arity": 2, "gloss": "I is a candidate instruction for request R",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "misaligned_with_higher_level", "arity": 1, "gloss": "I is misaligned with an applicable higher-level instruction",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "supersedes", "arity": 2, "gloss": "J supersedes I",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "later_message", "arity": 2, "gloss": "J appears in a later message than I",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "same_level", "arity": 2, "gloss": "J and I carry the same authority level",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "name": "suspected_mistaken", "arity": 1, "gloss": "I is suspected to be mistaken",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false } ],
  "ontology": [
    { "atom": "not_applicable(I, R)",
      "body": "candidate_instruction(I, R), misaligned_with_higher_level(I)",
      "gloss": "not applicable because it is misaligned with an applicable higher-level instruction",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "atom": "not_applicable(I, R)",
      "body": "candidate_instruction(I, R), supersedes(J, I), later_message(J, I), same_level(J, I)",
      "gloss": "not applicable because a later message at the same level supersedes it",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false },
    { "atom": "not_applicable(I, R)",
      "body": "candidate_instruction(I, R), suspected_mistaken(I)",
      "gloss": "not applicable because it is suspected to be mistaken",
      "licence": "textual", "cites": "m0088", "inference": null, "toggleable": false } ],
  "inputs": ["candidate_instruction/2", "misaligned_with_higher_level/1", "supersedes/2",
             "later_message/2", "same_level/2", "suspected_mistaken/1"],
  "forbid_body": [] }
```

It renders as three rules that share a head:

```
not_applicable(I, R) :- o, candidate_instruction(I, R), misaligned_with_higher_level(I).
not_applicable(I, R) :- o, candidate_instruction(I, R), supersedes(J, I), later_message(J, I), same_level(J, I).
not_applicable(I, R) :- o, candidate_instruction(I, R), suspected_mistaken(I).
```

**A condition goes in `body`, never in `atom`.** `atom` holds one term — a functor and its
arguments. The rule arrow lives between the two fields, not inside either of them.

```json
{ "atom": "not_applicable(I, R) :- suspected_mistaken(I)" }
```
is rejected. So is `{ "atom": "not_applicable(I, R)", "body": null }` on its own — an atom with a
variable and no body is not a fact, and the solver refuses the whole file.

**Alternatives are written by repeating the atom.** Three sufficient conditions means three entries
with the same `atom` and different bodies. Conditions written side by side in one body are joined
with `and` — the second entry above needs all four of its conditions to hold at once.

⚠️ **`;` in a body does NOT mean "or".** This is the one place ASP is likely to mislead you. Writing

```json
{ "atom": "not_applicable(I, R)", "body": "misaligned_with_higher_level(I) ; suspected_mistaken(I)" }
```

is accepted, compiles, and means **and** — clingo reads `;` in a rule body exactly as it reads `,`.
The rule you get is strictly narrower than the clause you were given, it passes every check, and
nothing downstream can tell. If you mean "either one is enough", write two entries.

**Where `;` IS the right tool: pooling inside an argument, in brackets.**

```json
{ "atom": "privileged_information(X)",
  "body": "message_kind(X, (system;developer;hidden_cot))",
  "gloss": "X is a system, developer or hidden chain-of-thought message" }
```

That one does mean "or": `(a;b;c)` in an argument position expands into one rule per value, so it
is a real shorthand for three near-identical entries.

⚠️ **The brackets are load-bearing.** `message_kind(X, system;developer)` without them splits the
whole literal instead of the argument, and clingo rejects the file with *"'X' is unsafe"*. So:

| where the `;` is | what it means |
|---|---|
| between literals — `a(X) ; b(X)` | **and**. Almost never what you want |
| inside an argument, bracketed — `p(X, (a;b))` | **or**, expanded into separate rules |
| inside an argument, unbracketed — `p(X, a;b)` | a parse error further out; the file is refused |

**Every predicate a body names is declared.** All six appear in `inputs`, and each has a `concepts`
entry giving its gloss. A body predicate that is declared nowhere cannot be told from a typo.

## The six bad ones

Each has actually happened in this project.

**1 — invents an entity.** The clause says "policies other than restricted or sensitive"; it never
enumerates which policies exist.
```json
{ "atom": "content_policy_rule(deception_policy)", "licence": "textual", "cites": "m0255" }
```
There is no deception policy in the document. Everything downstream worked and was about a fiction —
and a clean reviewer, given the clause and this read-back, answered *"faithful, nothing
unsupported"*. If you need it and cannot cite it, mark it `assumed` and name the inference.

**2 — the act is a material, not an act.**
```json
{ "status": "forbid", "act": "restricted_content" }
```
`restricted_content` is a thing, not an act. The query side joins on acts; this one silently joins
nothing, derives zero conflicts, and reports no error. Write `produce(M)`.

**3 — reasons from an absence.**
```json
{ "status": "forbid", "act": "produce(M)", "body": "not permitted(M)",
  "read_back": "producing % is forbidden because the exception does not reach it" }
```
`not permitted` carries no account of *why*. The verdict is right and the stated reason is wrong,
and the read-back asserts a reason the program cannot support. Give the positive ground instead.

**4 — the superiority has no sayer, or invents one.**
```json
{ "sayer": "m0208", "winner": "m0208", "loser": "m0252" }
```
m0255 is the clause that states this override. Recording m0208 as the sayer claims m0208 said
something it does not say — and a module may only record superiority its own clause states.

**5 — turns a negative into a positive.** The clause says the exception does **not** override other
policies. This encodes what it *does* override:
```json
{ "status": "permit", "act": "produce(M)", "body": "not out_of_scope(transformation, K)" }
```
The document never licensed that step. Absence of an exclusion is not an inclusion.

**6 — imports a name without its content.** The clause is about acts of terrorism. This makes the
whole category one symbol whose gloss just says the name again:
```json
{ "name": "terrorism_act", "arity": 1, "gloss": "an act of terrorism" }
```
The gloss adds nothing a reader did not already supply. `terrorism_act(X)` now stands for whatever
the reader happens to think terrorism means, and the document's own content about it is not in the
module at all.

This is the hardest failure to see, because it **reads correctly in every explanation** — the
symbol echoes the document's words, so a read-back sounds faithful and a reviewer nods. Nothing
mechanical catches it: the name is well-formed, the gloss is present, the module compiles.

Write what the document says the term covers, and where you cannot, say so rather than absorbing
it into a name:
```json
{ "name": "terrorism_act", "arity": 1,
  "gloss": "X is an act intended to intimidate a population or coerce a government, which this clause groups with crimes against humanity and war crimes as a critical harm" }
```
If the content lives in another clause, `requires` it. If it comes from outside the document, mark
it `world` and make it toggleable. What you may not do is let a label stand in for content you
never wrote down.
