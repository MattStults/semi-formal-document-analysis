# RATIONALE — how-to-approach-tradeoffs (a-priori module, blind build)

Built 2026-08-22 by a blind subagent builder per GENERALIZATION_BUILD_SPEC.md.
Derivation discipline: every declaration below is justified from the behaviour's
definition text ALONE (TRANSLATION_CONTRACT_V2 §9b). No panel verdict, runlog,
census, engagement run, or instrument output was consulted; no instrument code
was run. `modules_contract_v18.json` was opened for field names/shape only; the
dev behaviours' declaration contents were not reused.

## Definition as supplied (data/panel-v5/behaviour-definitions-v5.json, key "tradeoffs", verbatim)

> **query:** "When values or goals conflict, the model should navigate the
> tradeoff through structured prioritization rather than abandoning one
> consideration entirely."
>
> **boundary:** "The construct is the method for resolving conflicts between
> values or goals: ordered-but-holistic prioritization, balancing heuristics,
> chain-of-command as conflict resolver, and explicit outcome orderings. NOT
> this behaviour: the individual values being traded off (their own
> behaviours), the harm-calibration function (separate proportionate-risk
> behaviour), and the over-/under-refusal symptom (separate)."

**Shape note.** This behaviour is PROCEDURAL/META: it is the method by which the
model weighs competing considerations, not a first-order act about a topic. This
matters for every declaration below and for the gaps list (G1–G5).

## Acts performed (`module.does`, 4 declarations)

| # | Act (frozen vocabulary) | Grounds (citation from definition) |
|---|---|---|
| 1 | `handle_tradeoff` | query: the model should "**navigate the tradeoff**"; boundary: "The construct is the method for resolving conflicts…" — handling the tradeoff IS the behaviour. Direct lexical match; the vocabulary's only tradeoff act. |
| 2 | `resolve_conflict_or_ambiguity` | boundary: "The construct is **the method for resolving conflicts** between values or goals"; query: "**When values or goals conflict**…" The definition names conflict-resolution as the construct itself. See G5 for the conflict/ambiguity coupling caveat. |
| 3 | `follow_chain_of_command` | boundary: "**chain-of-command as conflict resolver**" — one of the four named components of the method. The resolver mechanism is FOLLOWING the chain of command (not merely referencing it — `reference_chain_of_command` excluded below). |
| 4 | `weigh_costs` | boundary: "**balancing heuristics**"; query: "navigate the tradeoff … rather than abandoning one consideration entirely" — balancing competing considerations is weighing them. `weigh_costs` is the vocabulary's only general weighing act (see G2: it is cost-specific, and the definition's generic balance/weigh act does not exist). |

All four names verified present in `act_inventory.json` (frozen vocabulary) with
canonical bindings in `act_bridges.json` (handle_tradeoff→respond,
resolve_conflict_or_ambiguity→respond, follow_chain_of_command→comply,
weigh_costs→respond).

## arg_sorts (1 declaration)

| Act | Sorts | Grounds |
|---|---|---|
| `follow_chain_of_command` | `["instruction"]` | "chain-of-command as conflict resolver": a chain of command is a hierarchy of authorities whose directives conflict; following it operates ON the competing instructions/directives. Consistent with the vocabulary's own typing of this act (`act_arg_sorts.json`: "instruction"). |

No arg_sorts declared for the other three acts: the definition says what they
operate on — "values or goals" — and the fixed situation-sort list has no sort
for values or goals. Declaring a catch-all (`topic`/`other`) would be an
invention, not a derivation. See G3.

## Wall fields — all omitted, each with grounds

* **protects_concern: omitted.** The definition names no protected party. The
  construct is a decision method; the boundary explicitly detaches the
  harm-calibration function ("separate proportionate-risk behaviour"), which is
  where party-protection would enter. Declaring any party would be citation-free.
* **party_concern: omitted.** Same grounds. No party is named or implied as a
  condition on when the method applies: the trigger is "when values or goals
  conflict", party-independent.
* **purpose_concern: omitted.** The definition states no document end the
  behaviour serves; the boundary even subtracts ends-adjacent content
  (harm-calibration, refusal calibration). Nothing to declare without invention.
  (The mined document-ends vocabulary is also not among this build's allowed
  inputs; the omission stands on the definition text alone.)
* **governs_concern: omitted.** The definition constrains the METHOD of deciding
  (structure of prioritization), which is not any of the §8 skeleton aspect
  qualities (substance_usefulness, objectivity_neutrality, accuracy_calibration,
  tone_manner, safety_of_manner, formatting_style, identity_meta,
  operational_hygiene). The nearest candidate, operational_hygiene, is flagged
  impure by the contract itself (§9a: quality × setting). Declaring it would be
  a stretch the definition does not license. See G4. (Additional blind-discipline
  note: the v18 exemplar's `_governs_note` records that dev governs values were
  TUNED on adjudicated truth — a path closed to this build by §9b and the build
  spec; no exclusion-shaped list is reproduced here for that reason.)
* **governs_conditional / situation: none.** Per the build spec there is no
  governs_conditional (9b: inert against unconditional declarations), and the
  context-atom lane carries no declarations.

## Considered and EXCLUDED acts (with reasons)

| Act | Why excluded |
|---|---|
| `detect_conflict_or_ambiguity` | The definition's trigger ("when values or goals conflict") presupposes conflict detection, but the construct is "the method for RESOLVING conflicts" — detection is trigger recognition, not the method. Minimal warranted declaration. |
| `provide_balanced_response` | A response-presentation quality (presenting sides of a topic), not the internal weighing METHOD. The definition is procedural; this act is topical/answer-shape. |
| `weigh_assumption_cost` | Weighing restricted to assumptions; the definition's weighing is over values/goals. Too narrow. |
| `assign_authority_level` | Instruction-hierarchy mechanics; subsumed by the declared `follow_chain_of_command` without independent definition wording. |
| `reference_chain_of_command` | Discursive reference to the chain in output; the definition says chain-of-command is USED as the resolver, i.e. followed. |
| `consider_factor`, `allocate_attention`, `apply_reasoning`, `use_best_judgment` | Too generic; no definition wording selects them. Declaring them would engage the module on general deliberation, which this behaviour is not. |
| `ensure_proportionate_action` (and proportionality family) | EXCLUDED BY BOUNDARY: "the harm-calibration function (separate proportionate-risk behaviour)". |
| `overrefuse` (and refusal-calibration acts) | EXCLUDED BY BOUNDARY: "the over-/under-refusal symptom (separate)". |
| Any act naming the individual traded-off values | EXCLUDED BY BOUNDARY: "the individual values being traded off (their own behaviours)". |

## Vocabulary gaps (recorded, not invented)

* **G1 — no prioritization / outcome-ordering act.** The definition's CORE
  construct — "structured prioritization", "ordered-but-holistic
  prioritization", "explicit outcome orderings" — has NO act in the frozen
  vocabulary. Verified: the inventory contains no act named with
  prioritize/rank/order-outcome (scan of all 725 functors). The closest
  expression is the single coarse `handle_tradeoff`, bridged generically to
  `respond` ("Handling a tradeoff is responding to a situation."). The
  vocabulary cannot distinguish structured-prioritized tradeoff handling from
  any other tradeoff handling. This is the central finding: the behaviour's
  defining act is inexpressible at act granularity.
* **G2 — no generic weigh/balance act.** "Balancing heuristics" is expressible
  only through `weigh_costs` (cost-specific, action-sorted) — the only other
  weighing act is `weigh_assumption_cost` (assumption-specific). There is no
  `weigh_considerations` / `balance_values` act. `weigh_costs` is declared as
  the closest available expression, flagged here as a partial fit.
* **G3 — no situation sort for values or goals.** The definition's trigger
  object ("values or goals") has no sort in the fixed list (request, response,
  user, content, action, instruction, party, setting, information, assistant,
  tool, other). Arg-typing for tradeoff/conflict handling can only land in
  catch-alls (`topic`/`other`), which §2/T5 discipline treats as review flags.
  Hence no arg_sorts declared for acts 1, 2, 4.
* **G4 — no governs_aspect quality for decision procedure.** The §8 skeleton
  has no value meaning "the method/structure by which the model weighs
  competing considerations". A governs wall for this behaviour cannot be stated
  in the current quality vocabulary; omitted rather than stretched.
* **G5 (minor) — conflict/ambiguity coupling.** The vocabulary's conflict acts
  are fused pairs (`detect_conflict_or_ambiguity`,
  `resolve_conflict_or_ambiguity`); the definition concerns value/goal CONFLICT
  only — ambiguity is never implicated. Declared with this mismatch noted.

## Headline finding

The frozen act vocabulary was mined from first-order behaviours (what the model
does about a topic/request). This behaviour is the model's WEIGHING METHOD
itself, and the vocabulary expresses it with four coarse acts, none of which
carries its defining structure (ordered-but-holistic prioritization, explicit
outcome orderings). The module therefore engages through a small act lane with
no wall declarations (no protected party, no party condition, no document end,
no governable aspect quality — each omission warranted by the definition text
and recorded as a gap). Attempt 1's transfer verdict will thus also measure
whether act-lane-only engagement suffices for a meta-behaviour.

## Declaration counts

* `does`: 4
* `arg_sorts`: 1 (follow_chain_of_command → instruction)
* `protects_concern`: 0 (omitted)
* `party_concern`: 0 (omitted)
* `purpose_concern`: 0 (omitted)
* `governs_concern`: 0 (omitted)
* vocabulary gaps recorded: 5 (G1–G5)
* acts considered and excluded: 10+ (table above), 3 classes excluded by explicit boundary wording

Module frozen as built; no revision before scoring (GENERALIZATION_BUILD_SPEC.md).
