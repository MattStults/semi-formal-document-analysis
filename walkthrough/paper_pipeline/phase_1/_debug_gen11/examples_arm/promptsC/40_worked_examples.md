# Six corrections — what was returned, and what it should have been

Every pair below is **real**: the ⛔ fragment is what a module for this corpus actually
returned on its first attempt, and the ✅ fragment is what the same module looked like
after the defect was found and repaired against the node's own source text. The node ids
are the ids those modules carried; **cite the id in YOUR input, never one of these.**

Read the ✅ side as the shape to imitate. One line under each pair says what changed.

---

## 1. A gloss that re-spaces its own name

Node `l1368_1541_n019`, narrowed to: *"It should instead provide a disclaimer …, suggest
that the user take safety precautions, and provide generic advice …"*

⛔ returned, in `concepts`:

```json
{ "name": "safety_precaution_suggestion", "arity": 1,
  "gloss": "S is a suggestion that the user take safety precautions",
  "licence": "textual", "cites": "l1368_1541_n019", "inference": null, "toggleable": false }
```

✅ after repair:

```json
{ "name": "safety_precaution_suggestion", "arity": 1,
  "gloss": "P is advice to the user to take steps that reduce the risk of harm",
  "licence": "textual", "cites": "l1368_1541_n019", "inference": null, "toggleable": false }
```

**What changed:** the gloss stopped repeating the name and said what makes the predicate
true. A gloss is the only way another module's definition can ever be matched to yours;
the first one passes zero information to the reader who has to make that match.

---

## 2. A rule with its own head in its body, on a word outside the narrowing

Node `l3239_3382_n002`. SOURCE TEXT: *"The assistant should help the developer and user by
following explicit instructions and reasonably addressing implied intent (see …) **without
overstepping**."* — but `[node narrows this span to: "The assistant should help the
developer and user by following explicit instructions and reasonably addressing implied
intent"]`. The narrowing **stops before** *without overstepping*.

⛔ returned, in `ontology`:

```json
{ "atom": "overstepping(A)",
  "body": "avoid_overstepping(R), user_authority(R), overstepping(A)",
  "gloss": "A is an action that oversteps the assistant's bounds",
  "licence": "textual", "cites": "l3239_3382_n002", "inference": null, "toggleable": false }
```

✅ after repair — the rule is **gone**; `overstepping/1` is declared in `inputs`, and the
one assert that uses it carries the licence the narrowing forces:

```json
{ "read_back": "the assistant should not overstep by %", "read_back_slots": ["A"],
  "licence": "assumed", "cites": null,
  "inference": "the narrowed span stops before 'without overstepping'; the content comes from ESTABLISHES, not the narrowed text",
  "toggleable": false,
  "status": "forbid", "act": "overstep(A)",
  "body": "assistant_definition(S), overstepping(A)" }
```

**What changed:** two things. The rule that derived `overstepping(A)` from
`overstepping(A)` could never fire, so the module's only prohibition was dead — the
predicate is a fact about the case, so it belongs in `inputs`. And the content came from
`ESTABLISHES`, not from the narrowed text, so citing this node for it manufactures a
citation; `assumed` with the step named is the honest licence and loses nothing.

---

## 3. A `closure` that decides what the span left open

Node `l1368_1541_n019` again. The span says what to do **in a dangerous situation** and
takes no position outside that trigger.

⛔ returned:

```json
{ "act_class": "suggest_precautions", "closure": "cepa",
  "reason": "the clause obliges suggesting precautions in dangerous situations but does not forbid such suggestions elsewhere; silence permits them" }
```

✅ after repair:

```json
{ "act_class": "suggest_precautions", "closure": "unclear",
  "reason": "the clause says what to do in a dangerous situation and takes no position on this act otherwise" }
```

**What changed:** `closure` is conclusion-bearing — `cepa` commits the document to
permitting the act everywhere the trigger does not hold. The span made no such commitment.
Note the ⛔ `reason` is circular: *"it does not forbid … so silence permits"* is `cepa`
restating itself.

---

## 4. An "unless" arm is a HOLE, not a permission

Node `l1_170_n056`, narrowed to: *"Models should honor user requests **unless** they
conflict with developer-, system-, or root-level instructions."*

⛔ returned, in `asserts` — one unconditional duty plus three manufactured permissions:

```json
{ "status": "oblige", "act": "honor_request(R)", "body": "user_request(R)",
  "read_back": "honoring user request % is obliged", "read_back_slots": ["R"], "…": "…" }
{ "status": "permit", "act": "refuse_request(R)",
  "body": "user_request(R), developer_instruction(I), conflicts_with(R, I)",
  "read_back": "honoring user request % is not obliged because it conflicts with developer instruction %",
  "read_back_slots": ["R", "I"], "…": "…" }
```

*(plus the same `permit refuse_request(R)` again for `system_instruction` and for
`root_instruction`)*

✅ after repair — **one** assert, and the exception moved into its body via an
`ontology`-derived condition:

```json
{ "read_back": "honoring user request % is obliged unless it is overridden by a higher-level instruction",
  "read_back_slots": ["R"],
  "licence": "textual", "cites": "l1_170_n056", "inference": null, "toggleable": false,
  "status": "oblige", "act": "honor_request(R)",
  "body": "user_request(R), not overridden_by_higher_instruction(R)" }
```

```json
{ "atom": "overridden_by_higher_instruction(R)",
  "body": "user_request(R), developer_instruction(I), conflicts_with(R, I)",
  "gloss": "request R is overridden by a developer-level instruction",
  "licence": "textual", "cites": "l1_170_n056", "inference": null, "toggleable": false }
```

*(plus the same head again for `system_instruction` and for `root_instruction` — three
different bodies, one head, which is what a three-way disjunction looks like)*

**What changed:** the *"unless"* **withdraws** the duty on the excepted branch. It says
nothing about what is permitted there, so the three `permit refuse_request` entries
asserted a permission the document never gives. The excepted branch is now a hole in the
obligation's body, and the act class's `closure` records `unclear`, not `cepa`.

---

## 5. Where a condition about the CASE lives

Node `l2126_2404_n016`, narrowed to: *"**In scenarios where** there's no moral ambiguity or
valid opposing perspective, the assistant should provide straightforward, unambiguous
answers …"*

⛔ returned — an arity-0 constant, and an assert body that uses it:

```json
{ "name": "no_moral_ambiguity", "arity": 0, "gloss": "the scenario presents no moral ambiguity", "…": "…" }
```
```json
{ "status": "oblige", "act": "answer_with(A)",
  "body": "no_moral_ambiguity, no_valid_opposing_perspective, straightforward_answer(A)", "…": "…" }
```

⛔⛔ and the repair that looks right and is **worse** — giving it an argument by giving it
a body:

```json
{ "atom": "no_moral_ambiguity(S)", "body": "scenario(S)",
  "gloss": "scenario S has no moral ambiguity", "…": "…" }
```

✅ after repair — arity 1, declared in `inputs`, with the act's variable **linked** to the
scenario the condition is about:

```json
{ "name": "no_moral_ambiguity", "arity": 1, "gloss": "scenario S presents no moral ambiguity",
  "licence": "textual", "cites": "l2126_2404_n016", "inference": null, "toggleable": false }
```
```json
{ "status": "oblige", "act": "answer_with(A)",
  "body": "no_moral_ambiguity(S), no_valid_opposing_perspective(S), answer_in_scenario(A, S), straightforward_answer(A)",
  "read_back": "in a scenario with no moral ambiguity and no valid opposing perspective the assistant should answer with %, because % is a straightforward, unambiguous answer",
  "read_back_slots": ["A", "A"],
  "licence": "textual", "cites": "l2126_2404_n016", "inference": null, "toggleable": false }
```
with `"inputs": ["no_moral_ambiguity/1", "no_valid_opposing_perspective/1", "answer_in_scenario/2", …]`.

**What changed:** an arity-0 atom is a proposition, not a property of a case, so nothing a
real situation supplies can ever match it and the guard is inert — the module concludes
less than the span. **But a body of `:- scenario(S)` is not the fix**: it derives *no moral
ambiguity* of **every** scenario, so a clause scoped to one kind of scenario now governs
all of them — the module concludes **more** than the span, in the dangerous direction.
Give the predicate the argument, declare it in `inputs` as a fact the situation supplies,
and add the relation (`answer_in_scenario/2`) that ties the act's variable to it. Reserve
bodied `ontology` rules for conditions the span itself defines, and ground atoms for facts
about the **document** (`root_authority(protect_privacy)`).

---

## 6. A borrowed `NEEDS` gloss is not yours to cite

Node `l1707_1973_n022`. Its `NEEDS` block hands over
*`root_authority`: Rules in the protect_privileged_information section carry root
authority.* — that meaning is established by **another node**.

⛔ returned, in `concepts` — the gloss rewritten from memory and cited to **this** node:

```json
{ "name": "root_authority", "arity": 1,
  "gloss": "the rule carries root authority, the highest authority level in the document",
  "licence": "textual", "cites": "l1707_1973_n022", "inference": null, "toggleable": false }
```

✅ after repair:

```json
{ "name": "root_authority", "arity": 1,
  "gloss": "rules in the protect_privileged_information section carry root authority",
  "licence": "assumed", "cites": null,
  "inference": "the graph's NEEDS block states this, and another node establishes it",
  "toggleable": false }
```

**What changed:** the gloss is now the words the `NEEDS` block actually hands over, and the
licence says where they come from. This node's SOURCE TEXT never mentions authority levels,
so `"licence": "textual", "cites": "<this node>"` on that gloss is a citation to a sentence
that does not exist.

⚠️ This applies to **borrowed `NEEDS` names only**. A name in `PROVIDES`, and any name you
coin from the narrowed text, stays `textual` and cites this node — marking those `assumed`
would be the same error pointing the other way.
