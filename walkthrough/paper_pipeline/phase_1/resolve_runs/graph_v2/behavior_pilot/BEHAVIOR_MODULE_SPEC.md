# Behavior module — the primary behavior artifact (spec for the arm-2 tuner, round 2+)

The project owner's ruling 2026-08-18: the behavior is an ASP MODULE in lingua-franca
predicates, not a bag of atoms; structure carries relevance information a
bag loses (a clause defining excessive caution alone is relevant to ONE
branch of "avoid over- AND under-caution"), and per-branch coverage is what
a user needs to interpret the result. Whether structure is NECESSARY for
binary relevance is an open empirical question — scored later by comparing
bag-of-vocabulary vs structure-aware relevance from the SAME module.

## Shape

```json
{
 "behavior": "<slug>",
 "definition": "<verbatim>",
 "structure": {                       // nested AND/OR over branch ids
   "op": "and", "branches": [
     {"id": "over_caution", "op": "or", "atoms": ["refuses_reasonable_request", "hedges_unnecessarily", "treats_unhelpfulness_as_safe"]},
     {"id": "under_caution", "op": "or", "atoms": ["complies_with_genuinely_harmful_request"]}
   ]},
 "atoms": [ {"id": "refuses_reasonable_request", "kind": "act|condition|consideration",
             "gloss": "...document-neutral, party named, vocabulary-reach test passed..."} ],
 "conditions": [ {"id": "...", "gloss": "..."} ],       // 'unless'/'when' guards, kept OUT of atoms
 "module": {                                             // ASP in global predicates (DESIGN.md §2 shape)
   "situation": ["<global_pred>(b, ...)"], "does": ["<global_act>(b, ...)"] }
}
```

Rules: (1) every atom carries a stable `id` (the stone keys on it); (2) branch
structure mirrors the definition's own logic — conjunctions of disjunctions,
with negations/conditions as explicit guards, never folded into an atom's
gloss; (3) the atom list is DERIVED from the module's vocabulary, not authored
separately; (4) glosses obey BEHAVIOR_CHECKLIST.md.

## What the report gains
Per behavior: a per-branch coverage row (which branches have >=1 relevant
clause) beside the flat relevance number, so "relevant to one branch only"
is visible rather than flattened.

## What is deferred
Predicate-level stone bindings and `render_behavior_module` consuming the
translated module (ROSETTA.md items 2–3) — built after the tuned relevance
number lands, since they are the firing/contradiction path.
