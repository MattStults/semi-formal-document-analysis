# Output format

Return **one JSON object** matching the schema you have been given. No prose, no markdown, no code
fence — the response body is the object itself.

The `.lp` file is **rendered from this object**, not written by you. That is deliberate: the licence
on every fact survives into the record instead of being lost in a comment, and the shape is
identical for every clause.

## The vocabulary is fixed

You do not invent predicate names for the normative layer. Every clause in the corpus is written in
the same four relations, so that clauses written independently can be linked and queried together:

| relation | |
|---|---|
| `asserts(ClauseId, Status, Act)` | this clause attaches a deontic status to an act |
| `beats(Sayer, Winner, Loser)` | this clause says one clause outranks another |
| `defines(ClauseId, Kind, Term)` | this clause fixes the extension of a class |
| a separate **ontology** block | non-deontic classification, e.g. `restricted(x)` |

`Status` is exactly one of **`forbid`** · **`permit`** · **`oblige`** · **`prefer`**.
`prefer` is for comparatives — *"minimize side effects"*, *"favour approaches that…"* — and is not
one of forbid/permit/oblige. Collapsing a comparative into `forbid` is a hollow stub.

You DO invent names in the **ontology** block. That is where the clause's own subject matter lives.

⭐ **Declaring a concept and asserting a fact are different, and both have their own list.**

- `concepts` — *"the predicate `restricted/1` exists and means: the material falls under the
  restricted-content policy."* Name, arity, gloss. **Asserts nothing.** Use it for every predicate
  this clause introduces.
- `ontology` — *"this particular thing IS restricted."* A ground atom, or one with a body that
  binds its variables.

A concept declaration is where the written definition lives, and it is required, because the
read-back renders the **definition, not the label** — otherwise a clause pointing at the wrong
concept produces a paraphrase that reads correctly and nothing catches it.

⭐ **An ontology entry can be CONDITIONAL, and that is what `body` is for.** To say *"R is a system
rule if it is set by OpenAI and transmittable via a system message"*, split it across the two
fields — never write a whole rule into `atom`:

```json
{ "atom": "system_rule(R)",
  "body": "set_by_openai(R), transmittable_via_system_message(R)",
  "gloss": "R is a rule set by OpenAI that reaches the model through a system message", ... }
```

⚠️ `"atom": "system_rule(R) :- set_by_openai(R)"` is rejected — `atom` holds a single term, and the
conditions belong in `body`.

⚠️ An ontology entry with an unbound variable and NO body is neither: `restricted(M).` with nothing
to bind `M` makes the solver reject the whole file. If you mean "the concept exists", declare it in
`concepts` instead.

⚠️ **Declaring a concept is not the same as defining it.** A `concepts` entry says what a predicate
means; it does not tell the solver where any instance comes from. Every predicate a body references
must ALSO be in your `ontology`, your `requires`, or your `inputs` — otherwise the rule can never
fire.

⭐ **Every predicate you reference must be declared.** Anything appearing in a body must be in your
`ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about the case). An
undeclared name cannot be told apart from a typo.

## Fields

| field | |
|---|---|
| `outcome` | `"translated"` or `"abstained"` |
| `clause_id` | the id you were given, exactly |
| `abstain_reason` | one sentence when abstaining; `null` otherwise |
| `claims` | the clause's distinct claims, one string each |
| `acts` | every act term this clause governs, declared once: `["produce(M)"]` |
| `concepts` | predicates this clause INTRODUCES: name, arity, and what each MEANS |
| `ontology` | non-deontic classification facts |
| `asserts` | the deontic assertions. Each has a `body`: the conditions under which it holds, or **`null` when it holds unconditionally**. ⚠️ Not `""` — an empty string is rejected |
| `beats` | superiority claims **this clause states** |
| `defines` | extensions this clause fixes |
| `closure` | one per act class — see below, it is required |
| `requires` | predicates another clause must define, `name/arity` |
| `inputs` | facts about the case, supplied at query time, `name/arity` |
| `forbid_body` | claims about the rule set: `[{"head": "permit", "banned": "purpose"}]` |

`requires` and `inputs` must be **disjoint**. A predicate cannot both need another clause to define
it and be a fact about the case being judged. That distinction is what makes linking possible.

### Acts are indexed

`asserts` relates a status to an **act**, not to a thing. `produce(M)`, `refuse(R)`,
`interject(user)`, `say_cannot_answer`. Writing a material where an act belongs means the query side
joins nothing — silently, with no error and no conflict ever derived.

Declare each act once in `acts`, then refer to it.

### Every fact declares its licence

On `asserts`, `beats`, `defines` and every `ontology` entry:

- `licence` — `textual` · `assumed` · `world`
- `cites` — **required and non-empty when `textual`**, else `null`
- `inference` — **required and non-empty when `assumed`**: name the step in one sentence
- `toggleable` — **must be `true` when `world`**, else `false`

These are checked when your answer is read, and a violation is rejected outright.

### Read-backs

`asserts` and `beats` each carry `read_back` — the English sentence a reviewer sees **instead of**
the formal item — and `read_back_slots`, the variables filling its `%` slots in order.

Write it as the clause's own claim, not as a description of the code.

⭐ **`%` is the substitution marker. Put one `%` where each argument goes, in order.**

    read_back      : "producing % is forbidden because % still binds"
    read_back_slots : ["M", "P"]        two % signs, two arguments

**The same variable may appear more than once.** One entry per `%`, in order, repeating the
variable — this is legal and is often the natural sentence:

    read_back      : "producing % is forbidden because % is disallowed material"
    read_back_slots: ["M", "M"]        two % signs, two entries, same variable

If the sentence needs no substitution, write it with **no `%` and no arguments** — that is a
perfectly good read-back and is not an error:

    read_back      : "an instruction that is inapplicable should typically be ignored"
    read_back_slots : []

The count must match: N slots, N arguments. Because `%` is reserved for substitution you cannot use
it to mean *per cent* — write the words instead.

One line only: no quotes, braces, backslashes or newlines.

### `closure` is required, not optional

For **every act class you govern**, say what the document's silence about that act means:

- `cepa` — silence **permits** it (whatever is not forbidden is permitted)
- `cnpa` — silence **prohibits** it
- `unclear` — the clause does not settle it

with a one-sentence reason from the clause. This is forced because an absent declaration reads as
`cepa` silently, and that reading changes downstream verdicts with nothing recording that a
commitment was ever made.

A clause governing no acts — a pure definition — needs no closure entry.

### When abstaining

Set `outcome` to `"abstained"`, give `abstain_reason`, and leave every list empty. An abstention
with content in it is neither an abstention nor a translation, and is rejected.
