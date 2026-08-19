# TRANSLATION CONTRACT V2 — what the NEXT document's translator receives
# (assembles every retrofit lesson of 2026-08-18 into translation-time requirements)

Matt's ruling: the ontology work must be "included in the automated
machinery for next time." This document is that machinery's specification.
Everything below was learned by RETROFIT on the Model Spec corpus — each
requirement cites the retrofit artifact that proved its need. The next
document's modules are BORN conforming; the gate enforces at translation
time; the bridge files are GENERATED from declarations, never classified
after the fact.

## 1. Act declarations are 4-tuples
Every act is declared as `{name, canonical, arg_sort, actor}`:
* `canonical` — one of the two-level canonical act ontology
  (behavior_pilot/behavior_vocab.json `canonical_acts_provisional` +
  `_act_hierarchy`). Retrofit cost of not having this: 720 functors
  classified post hoc, 3 audit rounds, ~7% corrected
  (act_bridges.json, full-audit commit).
* `arg_sort` — what the act acts ON (request/topic/content/instruction/...).
  Retrofit lesson: verb-only bridges caused the H1 wrong-argument failure
  class, 15/51 of the tuning failure census; walls apply only to
  homogeneous verb families (relevance_by_act.WALLED_VERBS).
* `actor` — assistant|developer|user|system. Retrofit lesson: H5 —
  developer acts engaged assistant behaviors; name-guessed tags were wrong
  12/19 times, assert-evidence tags correct (act_actors.json).
Gate: act with no canonical binding = HARD; unknown canonical = HARD
(NEW:<name> escape allowed, surfaces for ontology growth — 2/720 on the
Model Spec, both genuinely novel).

## 2. Situation concepts are typed at declaration
Every input/ontology concept declares `{sort, dims, generic}`:
* sort from the fixed list (request, response, user, content, action,
  instruction, party, setting, information, assistant, tool, other) —
  `other` >20% = catch-all review (T5).
* dims — scope-dimension values it EXPRESSES (party/intent/setting/
  reversibility/content_class/stakes). Retrofit: 2,065 concepts typed post
  hoc; two typing errors caught only by T4 firing-consistency (compound
  conditions split across values; normative conditions typed as case
  facts — both now sweep rules in classify_situation_sorts).
* generic: true iff the concept holds for ANY entity of its sort — the
  reversal derives only generic or dim-carrying concepts (measured:
  ungated reversal made chain_of_command_requires_refusal derivable from
  request(X), firing l609_698_n010 spuriously).

## 3. Modals must land in asserts (M30)
An assertless module whose CLAIMS carry a modal is a dropped-norm suspect
(gate detector `dropped_modal_assertless`, review tier). Retrofit: 7 hits,
2 real dropped norms incl. the agentic web-trust norm — repaired via
adjudicate -> blind-verify -> repair-run ceremony
(behavior_pilot/m30_adjudication.json, repair-7). Adjudication categories:
DROPPED-NORM / SIBLING-OWNED / DEFINITIONAL — only the first is a defect.

## 4. Norm-objects for actless norms
Rankings, consequence claims, and definitions with normative force either
declare the acts their norm governs (the outcome_ranking exemplar:
answer/hedge/decline) or are reached via the PROVIDES/NEEDS input-
relevance channel (relevance_by_dependency.py — Matt's design; 169/181
actless Model Spec modules reachable). A module reachable by NEITHER
channel is invisible to every query: gate-reportable.

## 5. Seam discipline from day one
One arity + one document-wide gloss per shared name, enforced hard
(SEAM_CONTRACT growth rule). Retrofit: 93% of 1,739 input names were
single-module coinages; 25 arity + 18 section-local-gloss collisions
queued for repair ceremony.

## 6. The validators run per-chunk, not post hoc
validate_ontology.py (A1-A7 acts, T1-T7 atoms), validate_behavior_module.py
(B-side), corpus_gate.py M-series — all wired into the translation loop the
way the mechanical gate already is; a chunk seals only when they pass.
Firing-consistency (A7/T4) runs against a hand-grounded reference case
built in the FIRST chunk and kept for the document's lifetime.

## 7. Asserts declare WHOSE interest the norm protects (from the E1 terminus)
Measured 2026-08-18 (deviation ledger + three ablations): party walls
retrofitted at act level (gloss-typed) collapse recall (FN 28->43); at
module level (situation-dim join) they are net zero (8FP<->8FN, signal in
264/762 modules only). "Whose interest does THIS norm protect" is
per-ASSERT information: dual-use clauses protect user AND third parties;
gloss mention is not protection. The next document's asserts carry
`protects: [user|third_party|developer|minor|society|...]` at translation
time, where the span states it; behaviors then wall on norm-protection
directly. Retrofitting the Model Spec corpus's asserts is a future
ceremony (annotation sweep + blind verification), not a query-side patch.
