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

⭐ **And every `requires` entry must also have a `concepts` entry saying what you need it to MEAN.**
Declaring the name says where it comes from; the `concepts` gloss says what you are assuming it is.
Both are needed, for two different readers:

- a person is shown test cases built out of these predicates, and a bare name like `policy_class/2`
  tells them nothing they can check the clause against;
- and the only way another clause's definition can ever be matched to your need is by comparing what
  each one SAYS. The name you invent cannot do that job — two translations of one clause pick
  different names almost every time, while they describe the same idea in nearly the same words.

⚠️ **You are not defining the term.** You are recording what this clause has to assume about it. If
another clause turns out to mean something different by the same name, that disagreement is worth
finding, and it can only be found if you wrote your assumption down.

⛔ **A gloss that restates the name is rejected.** `pasted_text/1` glossed *"pasted text"*, or
`supersedes/2` glossed *"J supersedes I"*, passes no useful information to either reader. Say what
makes it true — *"text the user pasted in without reading it carefully"*.

## Fields

⭐ **Each field is described in the schema itself, on that field.** The schema is part of this
request; read the `description` on a field rather than looking for a second copy here. There is no
second copy on purpose — two descriptions of one field drift, and the drift is invisible.

What follows is only what **no single field can carry**: rules that hold *between* fields.

### `requires` and `inputs` must be disjoint

A predicate cannot both need another clause to define it and be a fact about the case being judged.
That distinction is what makes linking possible.

### Acts are indexed

`asserts` relates a status to an **act**, not to a thing. `produce(M)`, `refuse(R)`,
`interject(user)`, `say_cannot_answer`. Writing a material where an act belongs means the query side
joins nothing — silently, with no error and no conflict ever derived.

Declare each act once in `acts`, then refer to it.

### Every fact declares its licence, and the licence decides what else is required

`asserts`, `beats`, `defines`, `concepts` and every `ontology` entry carry `licence` together with
`cites`, `inference` and `toggleable`. **These four fields are one obligation, not four
independent ones:** the value you put in `licence` decides which of the other three you must fill
and which must be left empty. Each of those fields states its own condition in the schema; satisfy
all of them together, because they are checked together and a mismatch is rejected outright.

Marking a fact `assumed` or `world` is always available. Reach for it rather than for a citation
that merely looks plausible — an invented entity behind a passed check is the worse outcome.

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

### `closure` is required, not optional

For **every act class you govern** — every distinct functor appearing in `acts` — add one `closure`
entry, with a one-sentence reason drawn from the clause. Which of the three readings each value
stands for is on the `closure` field itself.

It is forced, not optional. An absent declaration reads as `cepa` silently, and that reading
changes downstream verdicts with nothing recording that a commitment was ever made.

A clause governing no acts — a pure definition — needs no closure entry.

### When abstaining

Set `outcome` to `"abstained"`, give `abstain_reason`, and leave every list empty. An abstention
with content in it is neither an abstention nor a translation, and is rejected.
