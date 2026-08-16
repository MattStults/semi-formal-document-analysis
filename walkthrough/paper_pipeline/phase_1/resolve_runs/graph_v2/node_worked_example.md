# Worked examples — four good ones, then six bad

Your input is a **graph node**, not a bare clause: it arrives with `ESTABLISHES` (the one
claim), `PROVIDES` / `NEEDS` (assigned predicate names with their meanings), a `CITATION`
contract, and the verbatim `SOURCE TEXT`. The examples below are real nodes — real
`ESTABLISHES` / `NEEDS` / `PROVIDES` contracts, verbatim source text from this document. Their
**ids are the ids of the node sample this file was written against; the segmentation has moved
since, so they may not be ids you are handed** — cite the id in your own input, never one of
these (contract 1).

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

## A heading-authority node — a structural fact is translatable

Node `l3995_4164_n001` establishes only that the rules under a heading carry
guideline authority. NEEDS: none. PROVIDES: `guideline_authority`.

**This node obliges nobody, and it is still a translation, not an abstention.** There are three
routes: a node stating a norm goes to `asserts`; a node stating a **structural fact**
about the document — which authority a section carries, what class a thing falls in — goes to
`ontology` with `asserts` empty; only a node that establishes *neither* is an abstention. An empty
`asserts` list is not an empty module.

Here the third route is not available anyway: the node's `PROVIDES` names
`guideline_authority`, so other nodes are waiting on this module to make that predicate
derivable, and abstaining would strand every one of them. The module is tiny, and that is right.
Do not inflate it — but do deliver what `PROVIDES` promises.

`rule_under_heading` is in **`inputs`, not `requires`**, and the node's own contract is what
decides that: `requires` is for the names in the `NEEDS` block, and this node's `NEEDS` is
*(none)* — so no other node owns `rule_under_heading`. It is a fact about the material being
judged, which the module identifies itself. Had it been declared in `requires`, the rule's body
would wait forever on a definition no node ever supplies, and the head would derive nothing while
looking like it enforced something.

⚠️ **This is not a licence to move a borrowed name into `inputs` to make a module look clean.** The
discriminator is the `NEEDS` block, never "no provider turned up" — a genuine `NEEDS` name whose
provider is missing stays in `requires`, and the missing link is the finding.

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
  "requires": [],
  "inputs": ["rule_under_heading/2"],
  "forbid_body": []
}
```

No acts, so no closure entry is due. And `asserts` is empty because the node states no norm —
`outcome` is still `translated`, because the `ontology` entry says something the document says.

## A worked-example node — translate the lesson, not the dialog

Node `l4251_4571_n029` is a document example (a good/bad response pair). Its lesson is a
preference, so `prefer` is the status — collapsing it into `forbid` would be a hollow stub.
NEEDS: `voice_turn_taking_rule` (*"voice responses must align with iterative, turn-taking
conversation structure and adapt to conversational shifts"*). PROVIDES: none.

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
    { "name": "voice_turn_taking_rule", "arity": 1,
      "gloss": "R is subject to the requirement that a voice response fit an iterative, turn-taking exchange and adapt as the conversation shifts",
      "licence": "textual", "cites": "l4251_4571_n029", "inference": null, "toggleable": false },
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
  "requires": ["voice_turn_taking_rule/1"],
  "inputs": ["brief_overview/1", "open_question/1", "answers_question/2"],
  "forbid_body": []
}
```

**The NEEDS name went to `requires` even though the module never uses it.** Nothing in this
birthday example turns on voice turn-taking; the graph linked the node to that concept anyway.
Contract 2 is not conditional on your judgment of relevance — record the name, with the gloss the
node handed you, and let the link be inspected. Dropping it is the one outcome that cannot be
inspected: the module then looks complete and the missing cross-reference is invisible.

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

Many graph nodes are commentary, headings, or document examples. The two honest answers are a
small module that records only what the node actually establishes (like the heading node above,
which states a structural fact and asserts nothing) and a clean abstention (like this one, where
the node establishes nothing at all). Both are better than an invented obligation. What decides
between them is whether the node establishes anything the document says — not what KIND of
passage it is.

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
Neither an abstention nor a translation. Pick, on the three-way route: a norm the node states
goes to `asserts`; a structural fact it states goes to `ontology` with `asserts` empty; a node
that establishes neither is an abstention with **every** list empty. "It states no obligation" is
not on its own grounds to abstain — the heading node above states none and is translated.

**5 — citing the line markers instead of the node.**
```json
{ "name": "scope_record", "licence": "textual", "cites": "L0618-L0618" }
```
The `L`-numbers inside SOURCE TEXT locate text; the only citable id is the node's own
(`clause id:` at the top of the input). A textual licence citing anything else is
rejected, and on a graph node there is never a reason to cite anything but the node.
