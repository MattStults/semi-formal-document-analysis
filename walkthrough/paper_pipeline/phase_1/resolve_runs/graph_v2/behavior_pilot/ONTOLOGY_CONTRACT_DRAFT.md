# ONTOLOGY CONTRACT — situation concepts + ACTS — draft for the project owner's ruling (2026-08-18)

The project owner's observation: the "act seam contract" and the behavior atoms' act
vocabulary are ONE thing — an ontology of acts. SEAM_CONTRACT.json is the
situation-concept half (root_authority/1, authority_levels_hierarchy/2 …);
this file is the act half. Together they are the document's shared
vocabulary. Behavior modules are written directly in it (`does(b,
refuse(r1))`, situation facts in seam names / declared inputs); each corpus
module reaches it through bridge rules from its bespoke act names. For ONE
document the rosetta stone IS this bridge layer; a second document adds its
own bridges to the same canonical acts. One ruling, not two: accept an act
ontology with bridge rules that keep the bespoke names?

## The act half (formerly ACT_SEAM_CONTRACT_DRAFT.md)

## The measured problem
`act_inventory.json`: **762 modules, 725 distinct act functors, 866 act
declarations** — effectively one act name per module. `respond_with` (53)
and `refuse_request` (9) are the only names shared beyond a handful. A
behavior module's `does(b, act)` can only fire against acts modules SHARE,
so corpus-wide contradiction queries are impossible today; the S4 result
worked only because it was hand-grounded to 10 modules' bespoke names.
Behavior-translation failure B8; the direct twin of the authority-name seam
SEAM_CONTRACT.json already fixed for relevance.

## What the corpus does RIGHT that a naive fix would destroy
Bespoke act names carry the clause's exact distinction
(`refuse_in_judgmental_tone` vs `refuse_cleanly`; `refuse_exhaustive_list`;
`provide_crisis_resources` vs `provide_definitive_advice`). Collapsing 725 →
~12 loses that. The worked example already shows the right pattern for a
similar case: a canonical act (`apply_default(D)`) with the specific class
carried by a body predicate (`best_intentions_bias(D)`).

## Proposed shape: a canonical act LAYER, not a replacement
Each module keeps its bespoke act, and ADDITIONALLY declares which canonical
act it instantiates, via one ontology bridge rule per bespoke act:
```
canonical_act(refuse(R))  :- refuse_in_judgmental_tone(R).     % bridge
```
so `asserts(C, forbid, refuse_in_judgmental_tone(R))` stays exact, and a
behavior `does(b, refuse(r1))` fires through the bridge. Queries can ask at
either grain. Bridges are mechanical (one line per bespoke act), gate-
checked (every act must bridge to exactly one canonical act, arity pinned),
and re-runnable as a batch pass over the 762 modules — no redraws.

## Candidate canonical acts (from the inventory's families; RULE ON THESE)
| canonical | arity/args | covers (examples) | count |
|---|---|---|---|
| `respond(R)` | response | respond_with, respond_to_request, answer_directly, produce_response, give_*_answer | ~120 |
| `refuse(R)` | request | refuse_*, decline_*, overrefuse, refuse_to_help | ~35 |
| `comply(R)` | request | comply_with_*, follow_instruction, follow_*_instruction, obey_instruction | ~25 |
| `provide(I)` | information/content | provide_*, share_*, disclose_*, generate_content, produce_* | ~70 |
| `ask(Q)` | question | ask_*, seek_clarification, clarify_*, seek_confirmation, confirm_with_user | ~25 |
| `act_in_world(A)` | agentic action | perform_action, execute_*, send_*, delete_*, use_tool, act_autonomously | ~20 |
| `override(I)` | instruction/rule | override_*, ignore_instruction | ~12 |
| `express_uncertainty(R)` | response | hedge_*, qualify_*, add_disclaimer, express_uncertainty | ~10 |
| `pursue_goal(G)` | goal | pursue_goal, adopt_goal, optimize_for_goal, directly_pursue_goal | ~8 |
| `judge_or_moralize(R)` | request | be_judgmental, be_prescriptive, lecture_*, respond_non_moralizing(neg) | ~8 |
| `engage_relationship(U)` | user | engage_in_relationship, pair_romantically_*, engage_in_first_person_intimacy | ~6 |
| (long tail) | — | ~350 functors used once, mostly further specialisations of the above | — |
Long-tail functors bridge to the nearest canonical act; genuinely novel acts
(a real gap) get a new canonical entry by the same rule as the seam contract
(enters when a second module needs it).

## Alternatives, rejected by name
* **Rename bespoke acts to canonical ones (725 → 12):** destroys the clause-
  level distinctions the corpus encodes and would need 762 redraws.
* **Leave acts bespoke and ground behaviors per matched subset (status quo):**
  works for a demo, cannot scale past hand-grounding; no corpus-wide
  contradiction query is ever possible.

## What the ruling unblocks
Behavior modules written in canonical acts fire corpus-wide; the behavior
translator's contract becomes "canonical acts + declared inputs" (B5 fixed);
predicate-level rosetta bindings become the canonical-act layer itself for
this document; the second document later supplies its own bridges to the
same canonical acts — which is exactly the rosetta stone.

## The situation half — MEASURED SHAPE (2026-08-18)

Running the act procedure over the 2065 situation concepts (inventory →
discover → merge) produced 1959 proposals and merge collapsed only 6. That
is not a merge failure: the corpus's situation vocabulary is genuinely
SPECIFIC — `response_acknowledges_censorship` and
`response_includes_disclaimer` are different facts, and forcing them under
"a few hundred canonicals" would erase distinctions the document makes.
Acts collapse to ~11 verbs; situation concepts do not collapse.

Ruling proposed: the situation ontology is a TYPED HIERARCHY, not a flat
canonical list —
  * a SORT per concept from a fixed small set (request, response, user,
    content, action, instruction, party, setting, information, assistant,
    tool, other) — what its first argument is;
  * a small set of shared SCOPE DIMENSIONS with canonically-distinct values
    (party: user|third_party|developer|minor|society; intent:
    benign|ambiguous|illicit; setting: interactive|programmatic|agentic;
    reversibility; content_class; stakes), assigned to concepts that
    EXPRESS a value — these are the axes the mutation test (arm b) moves
    along, and the axes behaviors need to state scope;
  * near-duplicate merge only (`same_as`).
Bridges: `canonical_concept(<sort>(X)) :- <bespoke>(X)` and
`scope(<dim>,<value>,X) :- <bespoke>(X)`. Behavior modules state facts as
sorts + scope values (`request(r1). scope(intent,ambiguous,r1).`) and reach
every bespoke predicate that expresses them. `classify_situation_sorts.py`
builds it; `validate_ontology.py atoms` scores it.
