## A glossary node — the list IS the content, and its members are `ontology` facts

Node `l1_170_n028`. ESTABLISHES: *"The authority hierarchy ranked from highest to lowest:
Root > System > Developer > User > Guideline, with a sixth tier below all of them — No
Authority: assistant and tool messages, and quoted/untrusted text and multimodal data in
other messages. Instructions at higher levels override those at lower levels in case of
conflict."* PROVIDES: `authority_levels_hierarchy`. NEEDS: none. SOURCE TEXT (L0069-L0101,
L0183, L0186-L0191): the document's own bulleted list of the six levels.

A glossary, a definition list, a taxonomy, a table of roles — a span whose content is a
**list of named things** — is the shape that most often ends with the checker saying *body
references `X` but nothing declares it*. The reason is a fork taken one step earlier:

| what the span hands you | where it goes | notation |
|---|---|---|
| a predicate you are introducing | `concepts` | name + arity + gloss |
| **a MEMBER of the list — one named thing the span says exists** | **`ontology`, as a GROUND atom with `body: null`** | `authority_level(root)` |
| a name another node owns | `requires` | `name/arity` |
| a fact about the case being judged | `inputs` | `name/arity` |

**Row two is the one that gets missed, and it is fully legal.** An `ontology` entry may be
a ground atom with **no body at all** — that is how a module says *"this particular thing
exists, and the document is where I got it."* `concepts` cannot do that job: it declares
that a predicate exists and what it means, and asserts **nothing**, so a body that tests
`authority_level(root)` against a `concepts`-only declaration can never fire, and the
checker reports the name as undeclared. The rule of thumb is short:

> **If you can point at the words in the span that name the thing, it is a ground
> `ontology` fact — count the members and write one entry each.** If you cannot, it is a
> `concepts` declaration or an `inputs` name.

The unbound-variable warning is about a *different* entry. `authority_level(L)` with no
body is illegal, because `L` is bound by nothing. `authority_level(root)` with no body is
correct, because `root` is a constant — there is nothing left to bind. **Body-less is not
the problem; unbound is.**

```json
{
  "outcome": "translated",
  "clause_id": "l1_170_n028",
  "abstain_reason": null,
  "claims": [
    "C1 there are six levels of authority: root, system, developer, user, guideline, and no authority",
    "C2 they are ranked in that order, each level immediately above the next",
    "C3 assistant and tool messages, and quoted/untrusted text and multimodal data in other messages, carry no authority",
    "C4 an instruction at a higher level overrides a conflicting instruction at a lower level"
  ],
  "acts": ["follow_instruction(I)"],
  "concepts": [
    { "name": "authority_level", "arity": 1,
      "gloss": "L is one of the six levels of authority this section ranks",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "authority_levels_hierarchy", "arity": 2,
      "gloss": "level H sits immediately above level L in the ranking of authority levels",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "no_authority_source", "arity": 1,
      "gloss": "S is a part of the input that carries no authority: an assistant or tool message, or quoted/untrusted text or multimodal data inside another message",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "root", "arity": 0,
      "gloss": "the root level: fundamental rules that no system message, developer or user can override",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "system", "arity": 0,
      "gloss": "the system level: rules set by OpenAI, transmittable or overridable through system messages",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "developer", "arity": 0,
      "gloss": "the developer level: instructions given by developers using the API",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "user", "arity": 0,
      "gloss": "the user level: instructions from end users",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "guideline", "arity": 0,
      "gloss": "the guideline level: instructions that can be overridden implicitly",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "no_authority", "arity": 0,
      "gloss": "the sixth tier, below all the others, carrying no authority at all",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "assistant_or_tool_message", "arity": 0,
      "gloss": "the class of assistant and tool messages, named here so it can be listed as a no-authority source",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "quoted_or_untrusted_text", "arity": 0,
      "gloss": "the class of quoted or untrusted text appearing inside another message",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "multimodal_data", "arity": 0,
      "gloss": "the class of multimodal data appearing inside another message",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "outranks", "arity": 2,
      "gloss": "level H is somewhere above level L in the ranking, not merely immediately above it",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "name": "instruction_level", "arity": 2,
      "gloss": "instruction I was issued at level L of the authority hierarchy",
      "licence": "assumed", "cites": null,
      "inference": "the ranking can only decide a conflict if each instruction carries a level; the text presupposes that assignment",
      "toggleable": false },
    { "name": "conflicts_with", "arity": 2,
      "gloss": "instructions I and J direct incompatible things in this situation",
      "licence": "assumed", "cites": null,
      "inference": "'in case of conflict' relates two particular instructions; which pairs conflict is a fact about the case",
      "toggleable": false }
  ],
  "ontology": [
    { "atom": "authority_level(root)", "body": null,
      "gloss": "root is a level of authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_level(system)", "body": null,
      "gloss": "system is a level of authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_level(developer)", "body": null,
      "gloss": "developer is a level of authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_level(user)", "body": null,
      "gloss": "user is a level of authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_level(guideline)", "body": null,
      "gloss": "guideline is a level of authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_level(no_authority)", "body": null,
      "gloss": "no authority is the sixth tier, below all the others",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_levels_hierarchy(root, system)", "body": null,
      "gloss": "root sits immediately above system",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_levels_hierarchy(system, developer)", "body": null,
      "gloss": "system sits immediately above developer",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_levels_hierarchy(developer, user)", "body": null,
      "gloss": "developer sits immediately above user",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_levels_hierarchy(user, guideline)", "body": null,
      "gloss": "user sits immediately above guideline",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "authority_levels_hierarchy(guideline, no_authority)", "body": null,
      "gloss": "guideline sits immediately above the no-authority tier",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "no_authority_source(assistant_or_tool_message)", "body": null,
      "gloss": "assistant and tool messages carry no authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "no_authority_source(quoted_or_untrusted_text)", "body": null,
      "gloss": "quoted or untrusted text inside another message carries no authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "no_authority_source(multimodal_data)", "body": null,
      "gloss": "multimodal data inside another message carries no authority",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "outranks(H, L)",
      "body": "authority_levels_hierarchy(H, L)",
      "gloss": "a level immediately above another outranks it",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false },
    { "atom": "outranks(H, L)",
      "body": "authority_levels_hierarchy(H, M), outranks(M, L)",
      "gloss": "outranking carries down the chain, so root outranks every level below it",
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false }
  ],
  "asserts": [
    { "status": "forbid", "act": "follow_instruction(I)",
      "body": "instruction_level(I, LI), instruction_level(J, LJ), conflicts_with(I, J), outranks(LJ, LI)",
      "read_back": "following instruction % is forbidden because it conflicts with instruction % issued at a higher level of authority",
      "read_back_slots": ["I", "J"],
      "licence": "textual", "cites": "l1_170_n028", "inference": null, "toggleable": false }
  ],
  "beats": [],
  "defines": [],
  "closure": [
    { "act_class": "follow_instruction", "closure": "cepa",
      "reason": "the section bars following an instruction only when a higher-level instruction conflicts with it; an instruction nothing contradicts is followed as normal, so silence permits" }
  ],
  "requires": [],
  "inputs": ["instruction_level/2", "conflicts_with/2"],
  "forbid_body": []
}
```

Count what the enumeration produced: **six** levels, **five** ranking pairs, **three**
no-authority sources — **fourteen body-less ground atoms**, one per named thing in the
span, each with `body: null` and each citing the node. Not one of them could have been
written as a `concepts` entry instead: `concepts` says a predicate exists, `ontology` says
a thing *is* one.

Two more things this node shows:

**A constant gets a `concepts` entry too, at arity 0.** `root`, `system`, `no_authority`
and the three no-authority sources are names the module invents to stand for the things
the list names, so each is declared — `{"name": "root", "arity": 0, …}`. Declaring the
container (`authority_level/1`) is not declaring its members.

**Only the two rules carry a body, and both bind their variables.** `outranks(H, L)` is
written twice — the base case and the transitive step — the same repeat-the-atom pattern
as the node above. Everything that is a *fact* is ground and body-less; everything that is
a *rule* has a body. That split is the whole of the `ontology` block.

