# TRANSLATION_FIX_PLAN.md

Companion to **`TRANSLATION_REPAIR_CENSUS.md`**. Six fixes, ranked by cost saved per
unit of risk, each with the failing artifact, the instruction that permits it, the exact
diff, and what was validated offline.

**Zero API spend was incurred producing this.** Nothing under `runs/` or
`repair_graveyard/` was written to.

## The lever ordering, and why it is not negotiable here

```
(a) make it impossible in the grammar      — schema enum/const/shape + json_schema forcing
(b) fix it deterministically in code       — only where no content decision exists
(c) change the worked example
(d) change prose
```

The campaign's standing lesson is that a stated rule is not an enforced rule: an
authority convention sat in the prompt for three days and was violated 283 times until a
validator enforced it. This census reproduces the lesson twice over.

* **The prose already says all of it.** `10_output_format.md` contains
  *"The count must match: N slots, N arguments"*, *"a sentence with no substitution takes
  [] and no `%`"*, *"⚠️ An ontology entry with an unbound variable and NO body is
  neither"*, *"Declare each act once in `acts`"*, *"`closure` is required, not optional"*.
  Every one of those is a live top-five cost class.
* **And the worked example proves lever (c) works when it ENUMERATES.**
  `node_worked_example.md`'s notation table took the `not-a-term` /
  `forbid-body-not-bare-name` / `concept-name-carries-arity` family from 43 rounds to two
  (census §3.1). It succeeded because it is a *total function from slot to rendering*,
  not a warning.

⚠️ `prompt/00_task.md`, `prompt/10_output_format.md` and `prompt/20_worked_example.md`
are **GUARD-WATCHED**. Diffs against them below are proposals only and are **NOT
APPLIED**. `node_worked_example.md` is not watched.
⚠️ `schema.py` and `translate.py` are not on the do-not-touch list, but a batched corpus
run was in flight, and a schema change mid-run would invalidate `contract_hash` on every
entry already written. **Nothing was applied to either.** The only code written is two
new files plus their tests.

---

## Ranking

Measured by `translation_fix_sim.py` over the 84 schema-stage repair rounds of prompt
generation 11. "Kills" = rounds left with **nothing** to report; a fix that removes four
of a round's five findings saves nothing.

| rank | fix | lever | class(es) | kills alone | cumulative | risk |
|---|---|---|---|---|---|---|
| 1 | **D** ontology split: rules vs ground facts | (a) | `unsafe-variable` | **24 / 84 (29%)** | | medium |
| 2 | **E** acts carry their own closure | (a) | `act-not-in-acts`, `closure-missing`, `closure-ungoverned` | 8 / 84 (10%) | D+E → 30 (36%) | medium |
| 3 | **C** requires/inputs entries carry name+arity+gloss | (a) | `borrowed-without-gloss`, `inputs-entry-not-name-arity`, `requires-inputs-overlap` | 11 / 84 (13%) | +C → 43% | low |
| 4 | **A** deterministic autofix | (b) | `readback-slot-arity`, all IDFORM, `act-not-in-acts` | 2 / 84 (2%) | included above | **none — implemented & pinned** |
| 5 | **B** cites / clause_id as a per-request const | (a) | `citation-not-in-corpus`, `clause-id-mismatch` | 5 / 84 (6%) | **A+B+C+D+E → 49 / 84 (58%)** | **very low** |
| 6 | **F** body literals carry their origin | (a) | `undeclared-body-name` | 11 / 84 (13%) | +F → 76 / 84 (90%) | high |

**Highest value overall: D.** Largest single lever, one schema shape change, and it
removes the class the model is least able to repair itself (12 rounds persisted across a
repair, census §6.2).

**Highest value per unit of risk: A + B.** A is written, tested and applies today with
no schema change; B is four lines and cannot regress anything, because it narrows a
field to the single value the prompt already declares legal.

---

# Fix A — the deterministic autofix  *(lever b, IMPLEMENTED)*

**New file `translate_autofix.py`; pins in `test_translate_autofix.py` (34 passing).**
Pure functions over the raw module dict. No imports from any owned file.

## The line the file must not cross

A rule belongs there **only if the corrected value is fully determined by what the model
already wrote**, so applying it invents nothing and deletes nothing a reader could have
meant. Anything requiring a choice — which of ontology/requires/inputs a name belongs
in, what a borrowed predicate means, whether silence permits or prohibits, which variable
fills a `%` — stays with the model and costs a call. That is the correct price for a
decision. Five tests exist purely to pin the refusals (`test_undeclared_body_name_is_
never_autofixed`, `test_a_fabricated_citation_is_never_rewritten`, …).

## A1 · `readback-empty-slots` — the largest single sub-class in the census

**What the model did.** Verbatim from
`runs/20260810-225427…/l4572_4691_n011.transcript.json`, attempt 1:

```json
{"read_back": "for U18 users, the assistant cannot engage in immersive romantic roleplay",
 "read_back_slots": ["U"]}
```

and from `L1975-2125_n012`:

```json
{"read_back": "engaging the user in a relationship that undermines the user's capacity
               for meaningful human interactions is forbidden",
 "read_back_slots": ["U"]}
```

**61 of the 65 `read_back` findings are this exact shape: zero `%` in the sentence, a
non-empty slot list.**

**Why the instruction permits it.** `prompt/10_output_format.md` says the right thing
twice:

> ⭐ **`%` is the substitution marker. Put one `%` where each argument goes, in order.**
> …
> If the sentence needs no substitution, write it with **no `%` and no arguments** — that
> is a perfectly good read-back and is not an error
> …
> The count must match: N slots, N arguments.

and `schema.ReadBack`'s own field text says it a third time:

> "This is not the list of the rule's variables: a read-back with no substitution point
> is a good read-back and takes an empty list"

Three statements, 18 rounds under the live prompt. The reason is structural, not
comprehension: the field is *named* `read_back_slots` and sits beside `act` and `body`,
which are lists of the rule's variables. The model fills it as "this rule's variables"
because that is what the name and its neighbours suggest. **Prose cannot beat a field
name.**

**Why lever (b) and not (a).** The grammar cannot express "the number of `%` in string X
equals the length of array Y" — JSON Schema has no cross-field arithmetic, so
`json_schema_strict: true` (which these runs already use) cannot catch it. The durable
grammar fix is A1′ below. The autofix is available *today* at zero risk because the
rendered sentence is **byte-identical** before and after: there is no `%` for any entry
to fill, so the slot list is unreachable.

```python
# translate_autofix.py — applied
if isinstance(slots, list) and slots and rb.count("%") == 0:
    item["read_back_slots"] = []
```

The mirror case (more `%` than entries) is **not** fixed — choosing which variable fills
the extra `%` is content. Pinned: `test_more_percent_than_slots_is_NOT_autofixed`.

### A1′ — the durable grammar version, for when the renderer can be touched

Delete `read_back_slots` and make the marker carry its own name inline:

```diff
--- schema.py   (PROPOSED, NOT APPLIED)
 class ReadBack(Strict):
     read_back: str = Field(
-        description="the sentence a reviewer sees INSTEAD of the formal item. "
-                    "Put one `%` where each argument goes, in order")
-    read_back_slots: list[str] = Field(
-        description="the variables filling its `%` slots, in order …")
+        description="the sentence a reviewer sees INSTEAD of the formal item. "
+                    "Name each substitution INLINE in braces, using the "
+                    "variable itself: 'producing {M} is forbidden because {P} "
+                    "still binds'. A sentence needing no substitution simply "
+                    "has no braces — that is a good read-back.")
```

There is then no second list, so no count to mismatch, and the marker is
self-documenting. Cost: `render`/`%!trace_rule` interpolation and `readback.py` change
together. **Not proposed for this cycle** — it should ride with fix D's schema move.

## A2 · IDFORM — already extinct, kept as a regression floor

`concept-name-carries-arity`, `inputs-entry-not-name-arity`, `not-a-term`,
`forbid-body-not-bare-name`: the model writes a predicate in the wrong one of its three
renderings. Governed by `00_task.md` rule 10:

> ⚠️ The `/arity` notation never enters a value slot: a `concepts` entry's `name` is the
> bare name (its arity is the entry's own `arity` field), an `acts` entry is a term with
> its variable (`forbids(P, M)`), and `closure.act_class` / `forbid_body` slots take the
> bare functor name.

This family cost 52 rounds across generations 3–10 and **is now at 0–1 under gen 11**,
killed by the notation table in `node_worked_example.md`. The autofix rules stay as a
**floor**, not a fix: if the table is ever edited away the class returns silently, and
these rules make the return free instead of billable.

Determinism is guarded on both sides:

* `concept-name-arity` applies **only when the `/N` suffix agrees with the entry's own
  `arity` field** — the model said it twice and the fix asserts nothing new. A
  disagreement (`overrides/2` with `arity: 1`) is left for the model.
  Pinned: `test_a_disagreeing_arity_suffix_is_left_for_the_model`.
* `forbid-body-bare` extracts a functor, never invents one. Prose with no functor
  (`"out-of-scope action based on user's best interest"`) is refused.
  Pinned: `test_prose_in_forbid_body_is_NOT_guessed_at`.

## A3 · `ontology-rule-split` — `atom` holding a whole rule

**On disk:** `"atom": "system_rule(R) :- set_by_openai(R), transmittable_via_system_message(R)"`,
`"unclear_provenance(I) :- pasted_unread_text(I)"`, and nine more.

**The instruction is already exact** (`10_output_format.md`):

> ⚠️ `"atom": "system_rule(R) :- set_by_openai(R)"` is rejected — `atom` holds a single
> term, and the conditions belong in `body`.

The split point is `:-`, ASP's own rule separator — syntax, not judgement. Applied only
when `body` is empty; if the model filled both, reconciling them is content. This rule
also clears the *unsafe-variable* breach as a side effect: the variables were unbound
precisely because their binder was stranded inside `atom`.

## A4 · `declare-asserted-act` — and the honest finding about it

**On disk:** `"assertion names act 'produce(M)', which is not in `acts`"` — 26 findings
over 13 gen-11 clauses. The act term is copied verbatim off the assertion that already
names it; `acts` is a declaration list, not content.

⚠️ **Measured side effect, and it matters.** Declaring the act makes its closure due, so
this rule moves breaches from `act-not-in-acts` (17 rounds) into `closure-missing`
(12 → 24 on replay). It does **not** save the call. It is kept because it makes the
module *honest* — the alternative is a module asserting a status about an act it never
declared, with the closure question never asked — and because fix E turns the pair into
one structural requirement. Pinned: `test_declaring_the_act_does_not_invent_a_closure`.

## Offline validation of fix A

* `test_translate_autofix.py` — **34 tests, all passing.** RED-first: each fixture is a
  verbatim excerpt of an assistant turn from a stored transcript, the RED assertion is
  `schema.validate_all` firing the real message on it, the GREEN assertion is the same
  check passing after `autofix` with the content assertions unchanged.
* `test_base_module_is_clean` guards the whole file: the unperturbed fixture must pass,
  or every RED below it proves nothing.
* Non-mutation, idempotence and no-op-on-clean are pinned.
* Corpus replay: applied for real to all 244 stored failing modules. Rules fired
  61 × readback-empty-slots, 41 × concept-name-arity, 38 × forbid-body-bare,
  15 × act-class-functor, 9 × ontology-rule-split, 8 × reference-name-arity,
  1 × readback-trailing-slots, 116 × declare-asserted-act. Class presence after:
  `readback-slot-arity` 40 → 3, `act-not-in-acts` 30 → 0,
  `concept-name-carries-arity` 10 → 0, `inputs-entry-not-name-arity` 4 → 0.

**No live validation needed.** Fix A changes no prompt and makes no model call.

## Where fix A must be wired in

Not applied — the call site is inside `translate.py`'s repair loop and a corpus run is in
flight. The proposal:

```diff
--- translate.py   (PROPOSED, NOT APPLIED)
     obj = json.loads(raw)
+    # Deterministic notation repairs BEFORE validation. Two reasons:
+    #   1. they are free, and asking a model for them is not;
+    #   2. schema.Module._coherent is an `after` validator, so ANY sub-model
+    #      breach suppresses the whole coherence layer. Clearing the notational
+    #      breaches here is what lets round 1 report the real defects instead of
+    #      discovering them one round at a time (CENSUS §6.1).
+    obj, applied = translate_autofix.autofix(obj)
     mod, breaches = schema.validate_all(obj, clause_id=cid, known_clause_ids=ids)
```

`applied` must be recorded on the run artifact (a `*.autofix.json` beside
`*.raw.txt`), so that a deterministic edit is never invisible in the record.

---

# Fix B — `cites` and `clause_id` as a per-request const  *(lever a — do this first)*

**Kills 5 / 84 rounds alone (6%); very low risk; ~4 lines.**

**What the model did.** Fabricated provenance, 31 findings over 9 clauses:

```
cites 'L485-L486',   which is not a clause in this corpus
cites 'L1108-L1368', which is not a clause in this corpus
cites 'l1_170_n029', which is not a clause in this corpus   ← a NEIGHBOURING node
module says clause_id 'l1_170_n029' but it was asked to translate 'l1_170_n026'
```

Two shapes: line markers lifted out of the SOURCE TEXT block, and the id of an adjacent
graph node.

**Why the instruction permits it.** The contract is stated per request, in prose, inside
the user block (`node_corpus.py` adapter):

> CITATION: every ontology/asserts entry that cites a source must cite EXACTLY
> 'l1_170_n003' — the id of this node. Never cite line numbers, line ranges, or any
> other id.
>
> SOURCE TEXT (verbatim from the document; **the L-numbers locate text, they are not
> citable ids**):
> L0007-L0007: …

The prose is unambiguous and the L-numbers are disclaimed *in the same paragraph* — and
the model still cites them, because they are the only source-shaped identifiers actually
adjacent to the text it is reading. Meanwhile `schema.cites` is typed
`Optional[str] = Field(description="clause id — REQUIRED and non-empty when textual")`:
**the grammar permits any string.**

**Why lever (a), emphatically.** There is exactly ONE legal value, and it is known at
request time — the code already passes it as `clause_id` and `known_clause_ids`. And
this is the one class where the deterministic fix must be *refused*: `00_task.md` calls a
manufactured citation *"the single worst failure available here… it creates an invented
entity behind a passed check"*. An autofix that rewrites a bad citation into the legal
one would launder exactly that. Pinned as a refusal:
`test_a_fabricated_citation_is_never_rewritten`.

Format forcing is already on (`format_forcing: json_schema`, `json_schema_strict: true`,
confirmed in every gen-11 `run.json`), so a `const` is enforced by the provider's
constrained decoder at generation time — the token sequence is unreachable.

```diff
--- schema.py   (PROPOSED, NOT APPLIED)
-def json_schema():
+def json_schema(clause_id=None, cite_ids=None):
     """`Module.model_json_schema()`, flattened for structured-output mode.
+
+    ⭐ When the caller knows the identity of the clause being translated — which
+    it always does — that identity is written into the GRAMMAR rather than into
+    a sentence of the prompt. `cites` and `clause_id` then have exactly one
+    reachable value under constrained decoding, and a manufactured citation
+    stops being an error the repair loop pays to correct and becomes a token
+    sequence the decoder cannot emit. The prompt keeps saying it, for a reader.
     """
     raw = Module.model_json_schema()
     ...
+    if clause_id is not None:
+        raw["properties"]["clause_id"]["const"] = clause_id
+    if cite_ids:
+        for defn in _cited_defs(raw):          # Assertion, Superiority,
+            defn["properties"]["cites"] = {    # Definition, OntologyFact, Concepts
+                "anyOf": [{"enum": sorted(cite_ids)}, {"type": "null"}]}
     return raw

-def response_format(strict=True):
+def response_format(strict=True, clause_id=None, cite_ids=None):
     """together.ai's documented shape: {type, json_schema: {name, schema}}."""
-    js = {"name": "clause_module", "schema": json_schema()}
+    js = {"name": "clause_module",
+          "schema": json_schema(clause_id=clause_id, cite_ids=cite_ids)}
```

with the two call sites in `translate.py` (`_body()` and `response_format_payload()`)
passing the clause id and the legal cite set they already hold.

⚠️ **`cite_ids` must be the set the checker uses, not the whole corpus.** For a graph
node that set is `{node_id}` — one element — which is what makes this airtight. For the
flat-clause path it is the cross-referenced clauses actually shown, and passing the whole
593-clause corpus would be an enum wide enough to be useless. If the two sets can drift,
pass nothing rather than a wrong set.

**Offline validation.** The class is confirmed by replay: `citation-not-in-corpus` and
`clause-id-mismatch` are re-derived from the stored modules by
`schema.validate_all(..., known_clause_ids=…)` in all gen-11 rounds where the census
recorded them. Simulation: subtracting both classes kills 5 of 84 rounds ($0.0106).
**A `const` cannot be validated offline against a live decoder** — see §Live validation.

---

# Fix C — `requires` / `inputs` entries carry their own gloss  *(lever a)*

**Kills 11 / 84 (13%); low risk.**

**What the model did.** 36 findings over 15 gen-11 clauses:

```
`assistant_or_tool_message/1` is borrowed but has no gloss
`quoted_or_untrusted_text/1`  is borrowed but has no gloss
`multimodal_data/1`           is borrowed but has no gloss
`developer_instruction/1`     is borrowed but has no gloss
```

Cross-checking `l1_170_n028.json`: those three names **are** correctly listed in
`inputs`. The module simply has no `concepts` entry for them.

**Why the instruction permits it.** `10_output_format.md` states the requirement
prominently:

> ⭐ **And every `requires` entry must also have a `concepts` entry saying what you need
> it to MEAN.** Declaring the name says where it comes from; the `concepts` gloss says
> what you are assuming it is. Both are needed, for two different readers…

The instruction is right and the reasons given are good. It still fails 23 rounds,
because the requirement is **a join between two lists**. The model writes `inputs` at
the end, having already written `concepts`, and the second obligation is invisible from
where it is standing. This is a data-shape problem wearing a prose problem's clothes.

**Why lever (a).** Fold the meaning into the entry and the join disappears. Under
`json_schema_strict`, a required property of a required object is enforced by the
decoder: an entry without a gloss becomes unemittable.

```diff
--- schema.py   (PROPOSED, NOT APPLIED)
+class Borrowed(Strict):
+    """A predicate this module USES but does not define, with what it assumes
+    the predicate means.
+
+    ⭐ WHY THE GLOSS LIVES HERE AND NOT IN A PARALLEL `concepts` ENTRY.
+    It used to be a join: declare the name in `requires`/`inputs`, then declare
+    its meaning in `concepts`, and satisfy both. Measurement over every stored
+    translation run found the join unmet in 23 repair rounds across 15 clauses
+    under one prompt generation — always in the same direction, the name present
+    and the meaning absent. A cross-list obligation cannot be enforced by the
+    grammar; a required field of this object is enforced by the decoder itself.
+    """
+    name: str = Field(description="the predicate name, bare, e.g. request")
+    arity: int = Field(description="how many arguments it takes")
+    gloss: str = Field(
+        description="one sentence saying what THIS MODULE NEEDS it to mean. "
+                    "You are not defining the term — you are recording your "
+                    "assumption, so that a disagreement with the clause that "
+                    "does define it can be found. A gloss that restates the "
+                    "name is rejected")
+
-    requires: list[str] = Field(
-        description="predicates another clause must define, as name/arity")
-    inputs: list[str] = Field(
-        description="facts about the CASE, supplied at query time, name/arity")
+    requires: list[Borrowed] = Field(
+        description="predicates another clause must define, each with what "
+                    "this module needs it to mean")
+    inputs: list[Borrowed] = Field(
+        description="facts about the CASE, supplied at query time, each with "
+                    "what this module needs it to mean")
```

`name` + typed `arity` also makes `inputs-entry-not-name-arity` unrepresentable, and
`requires`/`inputs` disjointness becomes a comparison of `(name, arity)` pairs rather
than of formatted strings.

**Ripple, stated honestly.** `render()` writes `%% requires: {', '.join(mod.requires)}`
at `schema.py:1247-1248` and every consumer of `mod.requires` as `list[str]` needs a
`.sig` accessor. `Borrowed.sig` mirrors `Concept.sig` so the change is mechanical, but it
is not free, and it changes `contract_hash` — so it must land between corpus runs, never
during one.

**Offline validation.** Class confirmed by replay in all 23 gen-11 rounds. Simulation:
kills 11 / 84 ($0.0224). No offline proof is possible that the decoder will fill the
field well — only that it must fill it.

---

# Fix D — split `ontology` into rules and ground facts  *(lever a — the biggest lever)*

**Kills 24 / 84 (29%) alone; medium risk.**

**What the model did.** Every gen-11 `unsafe-variable` finding is an `ontology[i].atom`
carrying a variable nothing binds:

```
ontology atom: 'u18_user(U)'            carries the variable 'U' and there are no conditions to bind it
ontology atom: 'teen_user(U)'           carries the variable 'U' and there are no conditions to bind it
ontology atom: 'stay_in_bounds_principle(P)' … but the body never mentions it
ontology atom: 'limits_taxonomy(T)'     … but the body never mentions it
ontology atom: 'implicit_bias_default(D)' … no conditions to bind it
```

The model is saying *"this predicate exists"*. **74% of these atoms are already declared
in `concepts` with the same name and arity** — measured over the stored failing modules —
so the ontology entry is a duplicate that additionally makes clingo refuse the whole
file, taking every linked clause down with it.

**Why the instruction permits it.** `10_output_format.md` warns twice and correctly:

> ⚠️ An ontology entry with an unbound variable and NO body is neither: `restricted(M).`
> with nothing to bind `M` makes the solver reject the whole file. If you mean "the
> concept exists", declare it in `concepts` instead.

> ⭐ **Declaring a concept and asserting a fact are different, and both have their own
> list.**

and `node_worked_example.md` says it a third time —

> **Every variable in every atom is bound by its body.** … An atom with an unbound
> variable and no body makes the solver refuse the *whole file* — writing one is the
> single most expensive mistake in this format.

— and it is still the **most expensive class in the census**, with 12 of its rounds
persisting *across* a repair (the model was told and did not fix it). The reason is that
`OntologyFact` is one type doing two jobs:

```python
atom: str  = Field(description="e.g. restricted(new_bioweapon_step). NON-deontic")
body: Optional[str] = Field(description="ASP conditions, or null for a ground fact")
```

`body` is **optional**, so "unbound head with no body" is a *well-formed* value of the
type. The grammar says it is fine and only a validator says otherwise. That is the exact
configuration this campaign has learned not to trust.

**The fix: make the illegal state unrepresentable.**

```diff
--- schema.py   (PROPOSED, NOT APPLIED)
-class OntologyFact(Licensed):
-    atom: str = Field(description="e.g. restricted(new_bioweapon_step). NON-deontic")
-    gloss: str = Field(...)
-    body: Optional[str] = Field(
-        description="ASP conditions, or null for a ground fact")
+class OntologyRule(Licensed):
+    """A conditional classification: this thing is of that kind WHEN … .
+
+    ⭐ `body` is REQUIRED here, and that is the whole point of the split. It was
+    an Optional on a single combined type, which made "a head with an unbound
+    variable and no body" a well-formed value that only a validator rejected.
+    Measured over every stored run, that state was the single most expensive
+    repair class, and 12 of its rounds SURVIVED being pointed out. A state the
+    grammar permits will be produced; the fix is to stop permitting it.
+    """
+    atom: str = Field(
+        description="the classification, with its variables, e.g. system_rule(R)")
+    gloss: str = Field(...)
+    body: str = Field(
+        description="the ASP conditions that bind every variable in `atom`. "
+                    "Required — a rule with no conditions is a ground fact and "
+                    "belongs in `ontology_facts`")
+
+class OntologyGroundFact(Licensed):
+    """An unconditional classification about a NAMED thing: restricted(csam).
+
+    There is no `body` field at all, and `atom` may not carry a variable — so
+    the unsafe form cannot be written here either.
+    """
+    atom: str = Field(
+        description="a GROUND term — no variables, e.g. restricted(csam)")
+    gloss: str = Field(...)

-    ontology: list[OntologyFact] = Field(...)
+    ontology_rules: list[OntologyRule] = Field(
+        description="conditional classifications: X is of kind K when <body>")
+    ontology_facts: list[OntologyGroundFact] = Field(
+        description="unconditional classifications about NAMED things")
```

To write `u18_user(U)` the model must now be in `ontology_rules` and supply a body; to
write `u18_user(alice)` it must be in `ontology_facts` and use no variable. "The concept
exists" has nowhere to go **except `concepts`, which is where it belongs.** The choice
between the two lists is forced at the point the model picks the list, not discovered
afterwards by a validator.

Accompanying `node_worked_example.md` change (this file is **not** guard-watched and may
be edited):

```diff
--- resolve_runs/graph_v2/node_worked_example.md
-**Every variable in every atom is bound by its body.** `higher_level_instruction(I)`
-never appears bare: both entries carry a body that binds `I` (and `L`). An atom with an
-unbound variable and no body makes the solver refuse the *whole file* — writing one is
-the single most expensive mistake in this format.
+**Three lists, and which one a name goes in is decided before you write it.**
+
+| you want to say | list | shape |
+|---|---|---|
+| "the predicate `u18_user/1` exists and means …" | `concepts` | name + arity + gloss, asserts nothing |
+| "R is a system rule WHEN it is set by OpenAI"   | `ontology_rules` | `atom` + `body`, body binds every variable |
+| "csam is restricted"                             | `ontology_facts` | a GROUND atom, no variables, no body |
+
+`u18_user(U)` in `ontology_facts` is rejected — it carries a variable. `u18_user(U)`
+in `ontology_rules` with no body is not expressible: `body` is required. If what you
+meant is "this predicate exists", you wanted `concepts`, and you have probably already
+written it there.
```

**Offline validation.** Class confirmed by replay in all 22 gen-11 rounds. The
74%-already-in-`concepts` figure is measured over the stored failing modules and is
reproducible from `translation_repair_census.py`. Simulation: kills 24 / 84 ($0.0502).

**Rejected alternative, named.** An autofix rule
`ontology-drop-redundant-declaration` — drop an unbound, body-less ontology entry whose
name/arity is already in `concepts` — would clear 74% of the class deterministically and
was **rejected**: deleting a declared entry is a content edit, not a notation fix, and it
would put an automatic content deletion behind a green check. The grammar fix removes the
same failures without ever deleting anything the model wrote.

---

# Fix E — an act carries its own closure  *(lever a)*

**Kills 8 / 84 alone (10%); 30 / 84 (36%) with D; medium risk.**

**What the model did.** Three classes that are one defect — the act vocabulary does not
line up across three lists that must agree:

```
assertion names act 'produce(M)', which is not in `acts`
no default-closure declaration for act class(es) ['respond_as_plain_text', 'respond_via_function_call']
closure declared for act class(es) ['respond_with_plain_text_clarifying_question'] the module does not govern
```

The last is the tell: the model declared a closure for an act it named slightly
differently in `acts`. `closure-ungoverned` appears **for the first time in generation
11** — it was masked until `act-not-in-acts` started being reported.

**Why the instruction permits it.** The requirement is stated as strongly as prose can
state anything, in three places. `00_task.md` rule 12:

> **Declare the default closure for every act class you govern.** … This is required. An
> absent declaration is read as `cepa` silently, and that reading changes what the corpus
> concludes.

`10_output_format.md`:

> ### `closure` is required, not optional
> … It is forced, not optional. An absent declaration reads as `cepa` silently…

`schema.Closure`:

> ⚠️ Required for EVERY act class a module governs, because measurement shows the
> downstream verdict flips depending on the answer…

Everyone knows. It still costs 44 round-appearances, because **`acts`, `asserts[].act`
and `closure[].act_class` are three independent lists and consistency between them is a
validator's opinion.**

**The fix.** One list; the closure is a property of the act; assertions reference an act
by index.

```diff
--- schema.py   (PROPOSED, NOT APPLIED)
+class GovernedAct(Strict):
+    """One act this clause governs, WITH the meaning of the document's silence
+    about it.
+
+    ⭐ `acts` and `closure` used to be two lists that had to agree, plus a third
+    (`asserts[].act`) that had to name a member of the first by spelling it the
+    same way. Measured over every stored run, the three disagreed in 44 repair
+    round-appearances under one prompt generation, in all three directions.
+    Consistency between separate lists is a validator's opinion; a field of an
+    object is a fact.
+    """
+    term: str = Field(description="the act term with its variables, e.g. produce(M)")
+    closure: Literal["cepa", "cnpa", "unclear"] = Field(description=...)
+    reason: str = Field(description="one sentence from the clause …")
+
-    acts: list[str] = Field(...)
-    closure: list[Closure] = Field(...)
+    acts: list[GovernedAct] = Field(
+        description="every act this clause governs, each declared once, each "
+                    "carrying what the document's silence about it means")

 class Assertion(Licensed, ReadBack):
-    act: str = Field(description="the act term, e.g. produce(M)")
+    act: int = Field(
+        description="the 0-based index into `acts` of the act this status "
+                    "attaches to. You cannot attach a status to an act you "
+                    "have not declared")
```

`act-not-in-acts` becomes a type error rather than a spelling comparison;
`closure-missing` and `closure-ungoverned` become unrepresentable — there is no separate
list to under- or over-populate.

⚠️ **What this does NOT fix, deliberately.** The closure *value* (`cepa`/`cnpa`/
`unclear`) and its reason remain a real commitment about what the document's silence
means, and remain the model's decision. The fix removes the bookkeeping, not the
judgement — the `Literal` enum is already format-forced, so the value was never the
failure.

⚠️ An integer index is more brittle to a partial regeneration than a name. The
alternative — keep `act` a string and add a validator — is what exists now and is what
failed. If the index proves awkward in practice, the fallback is a string plus a
`json_schema` `enum` built per request from the acts the *adapter* already knows for
graph nodes — but that set is not known for free-form clauses, which is why the index is
proposed first.

**Offline validation.** All three classes confirmed by replay. Simulation: E alone kills
8 / 84 ($0.0161); D+E kills 30 / 84 ($0.0620).

---

# Fix F — body literals carry their origin  *(lever a; high risk; the residual)*

**Kills 11 / 84 alone; takes the plan from 58% to 90%.** Proposed, not recommended for
this cycle.

**What the model did.** 51 findings over 14 gen-11 clauses:

```
body references `teen`                      but nothing declares it
body references `request`                   but nothing declares it
body references `assistant`                 but nothing declares it
body references `first_person_roleplay`     but nothing declares it
body references `signs_of_delusion_or_mania` but nothing declares it
```

**Why the instruction permits it, and why it must keep costing a call today.**
`10_output_format.md`:

> ⭐ **Every predicate you reference must be declared.** Anything appearing in a body must
> be in your `ontology`, in `requires` (another clause defines it), or in `inputs` (a
> fact about the case). An undeclared name cannot be told apart from a typo.

That last clause is the reason **no autofix may touch this class**. In graph-node mode
`requires` is dictated by the NEEDS block, so an undeclared name could be routed to
`inputs` by elimination — and doing so would silently convert every typo into a declared
input, destroying the property the check exists for. Pinned as a refusal:
`test_undeclared_body_name_is_never_autofixed`.

**The grammar fix.** A body is a free-text ASP string, so nothing constrains the names
inside it. Replace the string with a list of literals, each tagged with where its
predicate comes from:

```diff
-    body: str = Field(description="the ASP conditions …")
+    body: list[BodyLiteral] = Field(
+        description="the conditions, one literal each. Every literal names its "
+                    "predicate and says where that predicate comes from — you "
+                    "cannot use a name without saying where it is declared")
+
+class BodyLiteral(Strict):
+    predicate: str
+    args: list[str]
+    negated: bool
+    origin: Literal["ontology", "requires", "inputs"]   # format-forced enum
```

`requires` and `inputs` then become **derivable** from the bodies rather than separately
maintained, which also removes the bookkeeping behind fix C. A typo still cannot be told
from a new name — but the model must now *assert* a home for it, which is a claim a
reviewer can check, rather than an omission nobody sees.

**Why not this cycle.** It rewrites every body in every module, the renderer, the link
checker, and the graveyard's stored artifacts. It should be designed on an orchestration
tier and reviewed on its own, not bundled with five smaller fixes.

**Intermediate, if F is wanted sooner:** keep `body` a string and add a required sibling
`body_names: list[{name, arity, origin}]`, cross-checked against the parsed body. That
converts a silent omission into a structural requirement without touching the renderer,
and lets an autofix rule *derive* `requires`/`inputs` from `body_names` deterministically
— because the model has then stated the origin itself and no bucket is being guessed.

---

# Offline validation — summary of evidence

| claim | how it was checked | result |
|---|---|---|
| the taxonomy is what the code says, not a reading of messages | every stored failing module replayed through `schema.validate_all` as it stands today | **84 / 84 gen-11 rounds reproduce their census classes — 100%** |
| the cost column is trustworthy | modelled cost of 435 visible calls vs 708 priced `usage.jsonl` rows | 1.11× — an upper bound, one-directional |
| fix A works and is safe | `test_translate_autofix.py`, RED-first on disk artifacts | **34 / 34 passing** |
| fix A does not cross the line | 5 refusal tests (undeclared name, borrowed gloss, fabricated citation, ungoverned closure, extra `%`) | all passing |
| fix A is safe to run twice / does not corrupt | idempotence, non-mutation, no-op-on-clean | passing |
| each fix's round-kill count | `translation_fix_sim.py`, autofix applied for real, grammar fixes simulated by class subtraction | table in §Ranking |

**Stated plainly: fixes B, C, D, E and F are grammar changes and CANNOT be validated
offline.** What the simulation shows is the *ceiling* — the rounds that would have had
nothing left to report if those classes could not occur. Whether a constrained decoder
produces *good* content in the newly-required fields is exactly the thing only a live run
can answer.

---

# Live validation — the cheapest experiment, costed. NOT RUN.

## The instrument already exists

`20260810-225427`, `20260810-234100` and `20260812-133317` translate the **identical
15-clause sample** under the identical system block, at 2.27 → 1.86 → 0.67 rounds per
clause. That is a calibrated, three-point baseline on a held-constant clause set. Reuse
it; do not invent a new sample.

The clause ids are in
`resolve_runs/graph_v2/translation_sample/runs/20260812-133317-together-deepseek-v4-flash/run.json`
under `config.select.clause_ids`:

```
l1_170_n026  l1_170_n028  l1108_1368_n004  l1611_1798_n006  l1799_1974_n009
l1975_2125_n012  l292_526_n027  l3384_3501_n007  l3995_4164_n001  l4251_4571_n029
l4572_4691_n011  l527_796_n012  l527_796_n022  l797_809_n001  l810_919_n014
```

Six of the fifteen carry the top-class defects directly under generation 11 (classes as
recorded, from `translation_repair_census.py`):

| clause | classes it drew under gen 11 |
|---|---|
| `l4572_4691_n011` | unsafe-variable, undeclared-body-name, borrowed-without-gloss, act-not-in-acts, closure-missing, closure-ungoverned, citation-not-in-corpus, clause-id-mismatch, empty-translation |
| `l1611_1798_n006` | unsafe-variable, undeclared-body-name, borrowed-without-gloss, act-not-in-acts, closure-missing, closure-ungoverned, readback-slot-arity, requires-inputs-overlap, not-a-term |
| `l3384_3501_n007` | undeclared-body-name, borrowed-without-gloss, act-not-in-acts, closure-missing, closure-ungoverned, readback-slot-arity, requires-inputs-overlap, clause-id-mismatch, toggleable-licence-mismatch |
| `l810_919_n014` | unsafe-variable, undeclared-body-name, borrowed-without-gloss, act-not-in-acts, closure-missing, closure-ungoverned, clause-id-mismatch, inputs-entry-not-name-arity |
| `l1_170_n026` | citation-not-in-corpus, clause-id-mismatch, readback-slot-arity, asp-body-unparseable, empty-body-not-null, unresolved-reference |
| `l527_796_n012` | unsafe-variable, readback-slot-arity |

Every class fixes A–E target is exercised by this sample, which is why it is the right
instrument and why a new one should not be drawn.

## Costs at measured rates

Baseline for this sample, from the census cost model (÷1.11 to remove the known
overestimate):

| arm | clauses | calls | cost |
|---|---|---|---|
| the observed baseline `20260812-133317` | 15 | 25 | **$0.043** |
| the observed worst case `20260810-225427` | 15 | 49 | $0.087 |

| # | arm | what it tests | calls (worst case: 5 attempts × 15) | cost | cumulative |
|---|---|---|---|---|---|
| 1 | **A only** — autofix wired in, prompt untouched | that the deterministic edits do not break a module the checks then accept, and that unmasking `_coherent` shortens chains | ≤75, expected ~22 | **$0.038** | $0.038 |
| 2 | **A + B** — plus the `cites`/`clause_id` const | that together.ai honours a `const`/`enum` inside `json_schema` strict mode, and that it does not degrade the rest of the object | ≤75, expected ~20 | **$0.035** | $0.073 |
| 3 | **A + B + C + D + E** — the full grammar plan | the headline: rounds per clause on the held-constant sample | ≤75, expected ~12 | **$0.021** | $0.094 |

**Total worst case: 225 calls, $0.39. Expected: ~54 calls, $0.094.**

Against the recorded budget in `spend.py` ($8.50 ceiling, ~$2.15 used) this is under 5%
of remaining headroom in the worst case, and it is the only way to answer the question.

## Read-out, pre-registered

* **Primary:** rounds per clause on the 15-clause sample. Baseline **0.67**. The
  simulation predicts **~0.28** for arm 3 (a 58% reduction in rounds).
* **Secondary:** repair-induced regression — the share of post-first rounds carrying a
  class no previous attempt had. Baseline **52%**. It should fall, because the grammar
  fixes remove the classes most often introduced by a repair.
* **Guard:** run `graveyard.py`'s `shrank` check on every convergence. A grammar change
  that makes modules pass by making them smaller is the failure mode this plan could
  produce, and the guard for it already exists.
* **Falsifier, stated in advance:** if arm 1 does not reduce rounds per clause at all,
  the masking hypothesis (§6.1 of the census) is wrong and fixes C–E should be re-costed
  before any of them is built.

## Order of operations

1. Land **A** (new file, already tested) — no schema change, no `contract_hash` change,
   can land during a corpus run.
2. Run **arm 1** between corpus runs.
3. Land **B** — smallest grammar change, cannot regress; run **arm 2**.
4. Design **D + E + C** together as one schema move with one `contract_hash` bump, get
   the independent adversarial review the cycle rules require, then run **arm 3**.
5. **F** is a separate design cycle on an orchestration tier.

⚠️ Fixes C, D and E change `contract_hash`. They must land **between** corpus runs, never
during one, or the graveyard entries already written stop being comparable.
