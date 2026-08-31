# ROSETTA — global behavior atoms bound per-document (design intent, 2026-08-18)

The project owner's framing: different documents may use one word with different meanings
and require different ontologies, so a single global atom vocabulary may be
unnecessarily hard or impossible — but worth trying, and the ATTEMPT should be
structured so the second document meets a schema, not a blank page. Until a
second document exists, the stone is trivially "the spec's own atoms"; this
note records the direction and the honest caveat.

## Three layers

1. **Global atoms** — document-independent, the user's vocabulary. Rule:
   phrased WITHOUT any one document's terms of art (BEHAVIOR_CHECKLIST.md
   rule 5, inverted). `atoms_frontier_frozen.json` and arm-2 tuner outputs are
   this layer's first drafts (spec-vocabulary leakage acknowledged).
2. **The rosetta stone** — per (atom, document): which of THIS document's
   nodes and predicates the atom binds to, with grounds. The seat's
   `(atom, node) -> engaged` verdicts ARE stone entries; today they are
   discarded per run. Fix: persist them (`rosetta/<document>.json`, keyed by
   atom id + node), extend to PREDICATE-level bindings (module inputs,
   seam-contract names), and make match READ the stone before spending. A
   binding survives an atom-gloss edit if the atom's identity is stable — that
   is what makes iteration cheap.
3. **The document's own ontology** — the translated corpus, seam contract,
   module vocabulary. Complete for the Model Spec as of 2026-08-17.

## What is testable with ONE document (do now)
* bindings-as-artifact: persist, re-match by lookup, measure spend -> ~$0.
* cross-behavior atom reuse: an atom shared by two behaviors must bind
  identically — a within-document check that the stone is about atoms.
* predicate-level binding + formal-layer relevance: bind atoms to module
  input predicates through the stone, run relevance as ONE clingo query over
  the whole corpus, and register it against the seat matcher on the same
  truth tier. This puts the translation on the critical path for relevance.

## What is NOT testable yet (deferred by ruling)
The generalization claim itself — global atoms binding meaningfully across
documents with different ontologies. Needs the second document (candidate:
the Anthropic constitution; `panel_v2.py`'s panel-coverage data already
scores 9 behaviours against both specs). **Gate (project owner, 2026-08-18): the tuned
instrument must first get close enough on the Model Spec to make the second
document worthwhile.** Honest expected outcome: some atoms will prove
spec-shaped and the stone's true form may be a per-document TRANSLATION of
each atom rather than a shared vocabulary; "no counterpart in document B" is
itself information.

## CORRECTION (project owner, 2026-08-18): the behavior is an ASP MODULE, not a bag of atoms

The intended pipeline is **Behavior → ASP module written in lingua-franca
(global-atom) predicates → the stone binds each global predicate to
document-specific predicates → the translated module queries the corpus.**
`DESIGN.md` §2 / `render_behavior_module` already define the module shape
(`behavior(b)`, situation facts, `does(b, act)`). The current implementation
uses a bare atom LIST as the whole behavior representation for relevance —
a shortcut that is nearly sufficient for relevance and insufficient for
firing/contradiction. Changes: (1) the arm-2 tuner emits a MODULE in global
predicates from round 2 on; the matching atoms are the module's vocabulary,
extracted, not a separate object; (2) stone bindings become PREDICATE-level
(global predicate → document predicate), so translation is mechanical;
(3) `render_behavior_module` consumes the translated module directly. The
lingua franca stays a glossed-concept layer above ASP; ASP enters where a
vocabulary exists to write it in — the document's, via the stone.
