# Worked examples — four good ones, then six bad

Your input is a **graph node**, not a bare clause: it arrives with `ESTABLISHES` (the one
claim), `PROVIDES` / `NEEDS` (assigned predicate names with their meanings), a `CITATION`
contract, and the verbatim `SOURCE TEXT`. The examples below are real nodes of this corpus.

Three contracts the node shape adds, before anything else:

1. **`cites` is always the node's id** — the string after `clause id:`. The `L0618-L0618`
   markers inside SOURCE TEXT locate text; they are not citable ids, and a module citing
   them is rejected.
2. **Every `NEEDS` name goes in `requires`, spelled exactly as given** (you choose the
   arity: `authority_levels_hierarchy` becomes `authority_levels_hierarchy/2`). Never
   define a NEEDS name in your `ontology` — another node owns it. Give it a `concepts`
   entry carrying the meaning the node text hands you.
3. **`inputs` is only for case-side facts you identify** — which messages exist, what an
   instruction says here. A name can never appear in both `requires` and `inputs`.

## The good one — a conditional node with borrowed vocabulary

Node `l527_796_n012`. ESTABLISHES: *"The implicit biases of 'Assume best intentions' are
subtle defaults that must never override explicit or implicit instructions from higher
levels of the chain of command."* NEEDS: `authority_levels_hierarchy`,
`best_intentions_bias`. PROVIDES: none. SOURCE TEXT (L0618): *"These implicit biases are
subtle and serve as defaults only --- they must never override explicit or implicit
instructions provided by higher levels of the chain of command."*

```json
{
  "outcome": "translated",
  "clause_id": "l527_796_n012",
  "abstain_reason": null,
  "claims": [
    "C1 the best-intentions defaults are defaults only",
    "C2 applying such a default is forbidden when it would override an explicit instruction from a higher level",
    "C3 the same prohibition holds for implicit instructions from a higher level"
  ],
  "acts": ["apply_default(D)"],
  "concepts": [
    { "name": "best_intentions_bias", "arity": 1,
      "gloss": "D is one of the implicit-bias defaults the 'Assume best intentions' section describes",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "name": "authority_levels_hierarchy", "arity": 2,
      "gloss": "which of two levels of the chain of command is the higher one",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "name": "higher_level_instruction", "arity": 1,
      "gloss": "I is an instruction from a level of the chain of command above the level at which the defaults operate",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "name": "defaults_level", "arity": 0,
      "gloss": "the level of the chain of command at which the best-intentions defaults themselves operate",
      "licence": "assumed", "cites": null,
      "inference": "'higher levels' only means something relative to the level the defaults hold; the text presupposes that level without naming it",
      "toggleable": false },
    { "name": "explicit_instruction", "arity": 1,
      "gloss": "I is an instruction stated outright in a message of this conversation",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "name": "implicit_instruction", "arity": 1,
      "gloss": "I is an instruction conveyed by a message of this conversation without being stated outright",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "name": "instruction_level", "arity": 2,
      "gloss": "instruction I was issued at level L of the chain of command",
      "licence": "assumed", "cites": null,
      "inference": "instructions 'provided by higher levels' must each carry a level for the comparison to range over",
      "toggleable": false },
    { "name": "overridden_if_applied", "arity": 2,
      "gloss": "applying default D in this situation would contradict what instruction I directs",
      "licence": "assumed", "cites": null,
      "inference": "'override' relates a default to a particular instruction it would displace; which pairs conflict is a fact about the case",
      "toggleable": false }
  ],
  "ontology": [
    { "atom": "higher_level_instruction(I)",
      "body": "explicit_instruction(I), instruction_level(I, L), authority_levels_hierarchy(L, defaults_level)",
      "gloss": "an explicit instruction from a level above the defaults",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false },
    { "atom": "higher_level_instruction(I)",
      "body": "implicit_instruction(I), instruction_level(I, L), authority_levels_hierarchy(L, defaults_level)",
      "gloss": "an implicit instruction from a level above the defaults",
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false }
  ],
  "asserts": [
    { "status": "forbid", "act": "apply_default(D)",
      "body": "best_intentions_bias(D), higher_level_instruction(I), overridden_if_applied(D, I)",
      "read_back": "applying default % is forbidden because it would override instruction % from a higher level of the chain of command",
      "read_back_slots": ["D", "I"],
      "licence": "textual", "cites": "l527_796_n012", "inference": null, "toggleable": false }
  ],
  "beats": [],
  "defines": [],
  "closure": [
    { "act_class": "apply_default", "closure": "cepa",
      "reason": "the clause bars a default only when it would override a higher-level instruction; a default that contradicts nothing is the section operating as intended, so silence permits" }
  ],
  "requires": ["authority_levels_hierarchy/2", "best_intentions_bias/1"],
  "inputs": ["explicit_instruction/1", "implicit_instruction/1", "instruction_level/2", "overridden_if_applied/2"],
  "forbid_body": [ { "head": "permit", "banned": "best_intentions_bias" } ]
}
```

Things to notice, in order of how often their absence has failed a module:

**Every variable in every atom is bound by its body.** `higher_level_instruction(I)` never
appears bare: both entries carry a body that binds `I` (and `L`). An atom with an unbound
variable and no body makes the solver refuse the *whole file* — writing one is the single
most common failure on nodes. If you want to say "the concept exists", that is a `concepts`
entry, not an `ontology` entry.

**Alternatives are written by repeating the atom.** "explicit or implicit" is two entries
with the same atom and different bodies — never `;` between literals (which clingo reads
as AND), never a rule written into `atom`.

**The act is declared, then referred to.** `apply_default(D)` appears in `acts` once, and
the assert names it. An assert naming an act missing from `acts` is rejected.

**Three notations, and each has exactly one home.** Look at how `apply_default` is
written in each field of the module above — the same act, three spellings, none
interchangeable:

| field | notation | example above |
|---|---|---|
| `requires` / `inputs` | name/arity | `best_intentions_bias/1` |
| `acts`, and `act` inside an assert | term with its variable | `apply_default(D)` |
| `closure.act_class`, `forbid_body.head` | bare functor name | `apply_default` |

Writing `apply_default/1` in `closure`, or `apply_default(D)` in `forbid_body.head`, or
`apply_default/1` in `acts`, are each rejected.

**The NEEDS names went to `requires` verbatim, with the arity you chose.** And each also
has a `concepts` entry restating the meaning the node handed you — that prose, not the
name, is what links your module to the provider node.

**The case-side vocabulary went to `inputs`.** Which instructions exist, at what level,
and which pairs conflict are facts about the conversation being judged — not things any
node of the document defines.

**`forbid_body` is for "never", and its slots are BARE names.** "Must never override" is
also a claim about the rule set itself: no rule may derive a permission from a
best-intentions default. That is what `{ "head": "permit", "banned":
"best_intentions_bias" }` records — checked by inspecting the program, since no test case
can exhibit a derivation that never happens. Both slots are bare predicate names: never
`permit(A)` (a term), never `permit/1` (a reference). Most nodes leave this list empty;
reach for it only when the text forbids a *kind of rule*, not a kind of act.

## A heading-authority node — small is correct

Node `l3995_4164_n001` establishes only that the rules under a heading carry
guideline authority. The module is tiny, and that is right — a node that establishes
section metadata yields a classification, not obligations. Do not inflate it.

```json
{
  "outcome": "translated",
  "clause_id": "l3995_4164_n001",
  "abstain_reason": null,
  "claims": [
    "C1 all rules under the 'Don't make unprompted personal comments' heading carry guideline authority"
  ],
  "acts": [],
  "concepts": [
    { "name": "guideline_authority", "arity": 1,
      "gloss": "the rule carries guideline-level authority: guidance for assistant behavior rather than a strict requirement",
      "licence": "textual", "cites": "l3995_4164_n001", "inference": null, "toggleable": false },
    { "name": "rule_under_heading", "arity": 2,
      "gloss": "the rule is located under the named heading in the document",
      "licence": "assumed", "cites": null,
      "inference": "the node speaks of the rules under a heading, so a relation between a rule and a heading must exist",
      "toggleable": false },
    { "name": "unprompted_personal_comments_heading", "arity": 0,
      "gloss": "the document heading 'Don't make unprompted personal comments'",
      "licence": "textual", "cites": "l3995_4164_n001", "inference": null, "toggleable": false }
  ],
  "ontology": [
    { "atom": "guideline_authority(R)",
      "body": "rule_under_heading(R, unprompted_personal_comments_heading)",
      "gloss": "R is a rule under the 'Don't make unprompted personal comments' heading and therefore carries guideline authority",
      "licence": "textual", "cites": "l3995_4164_n001", "inference": null, "toggleable": false }
  ],
  "asserts": [], "beats": [], "defines": [], "closure": [],
  "requires": ["rule_under_heading/2"],
  "inputs": [],
  "forbid_body": []
}
```

No acts, so no closure entry is due.

## A worked-example node — translate the lesson, not the dialog

Node `l4251_4571_n029` is a document example (a good/bad response pair). Its lesson is a
preference, so `prefer` is the status — collapsing it into `forbid` would be a hollow stub.

```json
{
  "outcome": "translated",
  "clause_id": "l4251_4571_n029",
  "abstain_reason": null,
  "claims": [
    "C1 for an open-ended question, a brief overview with an offer to elaborate is preferred over overwhelming detail"
  ],
  "acts": ["respond_with(R)"],
  "concepts": [
    { "name": "brief_overview", "arity": 1,
      "gloss": "a response that gives a short overview and offers to elaborate, rather than listing all details at once",
      "licence": "assumed", "cites": null,
      "inference": "the example contrasts a brief response with an overloaded one; the contrast needs this class",
      "toggleable": false },
    { "name": "open_question", "arity": 1,
      "gloss": "a user question that is open-ended and admits many possible answers",
      "licence": "assumed", "cites": null,
      "inference": "the example turns on the question being broad enough that dumping every detail overwhelms",
      "toggleable": false },
    { "name": "answers_question", "arity": 2,
      "gloss": "response R answers question Q",
      "licence": "assumed", "cites": null,
      "inference": "the preference relates a response to the question it answers",
      "toggleable": false }
  ],
  "ontology": [],
  "asserts": [
    { "status": "prefer", "act": "respond_with(R)",
      "body": "brief_overview(R), open_question(Q), answers_question(R, Q)",
      "read_back": "responding with % is preferred: a brief overview with an offer to elaborate suits an open-ended question",
      "read_back_slots": ["R"],
      "licence": "textual", "cites": "l4251_4571_n029", "inference": null, "toggleable": false }
  ],
  "beats": [], "defines": [],
  "closure": [
    { "act_class": "respond_with", "closure": "cepa",
      "reason": "the example states a preference between two permitted responses; it forbids nothing, so silence leaves responses permitted" }
  ],
  "requires": [],
  "inputs": ["brief_overview/1", "open_question/1", "answers_question/2"],
  "forbid_body": []
}
```

## A commentary node — abstaining is a real answer

Node `l1799_1974_n009` is a definitional analogy. It imposes nothing; encoding it would
mean inventing a normative force the text does not state. Abstain, say why, and leave
**every** list empty — an abstention with content in it is neither an abstention nor a
translation, and is rejected.

```json
{
  "outcome": "abstained",
  "clause_id": "l1799_1974_n009",
  "abstain_reason": "This clause is a definitional analogy, not a normative statement. It does not itself impose an obligation, permission, or prohibition on any act; it only describes the relationship between the assistant and its underlying prompts. Encoding it as a rule would require inventing a normative force the text does not state.",
  "claims": [], "acts": [], "concepts": [], "ontology": [], "asserts": [],
  "beats": [], "defines": [], "closure": [], "requires": [], "inputs": [],
  "forbid_body": []
}
```

Many graph nodes are commentary, headings, or document examples. A hollow-but-honest
module (like the heading node above) or a clean abstention (like this one) are both
better than an invented obligation.

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

## The six bad ones

Each of these happened on nodes of this corpus, in this pipeline, this week.

**0 — the right name in the wrong notation.**
```json
{ "acts": ["refrain_from_full_compliance/1"],
  "closure": [ { "act_class": "apply_default/1", "closure": "cepa" } ] }
```
Both rejected. `name/arity` lives only in `requires`/`inputs`. An `acts` entry is a term
(`refrain_from_full_compliance(R)`); a `closure.act_class` is the bare functor
(`apply_default`). See the three-notations table above.

**1 — an unbound variable with no body.** From a sycophancy node:
```json
{ "atom": "ungrounded_belief(B)", "body": null }
```
`B` is bound by nothing, and the solver refuses the whole file — taking every linked
module down with it. If the intent was "this concept exists", that is a `concepts` entry.
If the intent was a classification, write the body that binds `B`.

**2 — a rule written into `atom`.** From the authority-ordering node:
```json
{ "atom": "overrides(A, B) :- higher_authority(A, B)" }
```
`atom` holds one term. The conditions go in `body`; the arrow lives between the two
fields, not inside either.

**3 — an act referred to but never declared.** From a hard-refusal example node:
```json
{ "asserts": [ { "status": "forbid", "act": "provide_steps", "body": "..." } ], "acts": [] }
```
Every act is declared once in `acts` so the closure declaration can be checked against
it. (And `provide_steps` without an argument cannot join the query side — index it:
`provide_steps(M)`.)

**4 — an abstention that keeps its content.**
```json
{ "outcome": "abstained", "claims": ["C1 ..."], "asserts": [ { "status": "forbid" } ] }
```
Neither an abstention nor a translation. Pick: if the node establishes an obligation,
translate it; if it establishes none, abstain with every list empty.

**5 — citing the line markers instead of the node.**
```json
{ "name": "scope_record", "licence": "textual", "cites": "L0618-L0618" }
```
The `L`-numbers inside SOURCE TEXT locate text; the only citable id is the node's own
(`clause id:` at the top of the input). A textual licence citing anything else is
rejected, and on a graph node there is never a reason to cite anything but the node.
