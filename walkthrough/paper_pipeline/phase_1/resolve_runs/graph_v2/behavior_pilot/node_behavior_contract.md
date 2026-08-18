# Behavior translator contract — the corpus vocabulary a behavior module MUST be written in

Matt's ruling 2026-08-18: with one document, behaviors are translated INTO the document's vocabulary directly, following the spec pipeline's own contract discipline (NEEDS/PROVIDES + seam contract + validation). Every predicate in a behavior module is one of the names below, or an explicit `borrow` naming which module declares it. Anything else is a validation BREACH (behavior-translation failure B5), exactly as an undeclared name is a breach in a spec module.

## Canonical ACTS (PROVISIONAL — ONTOLOGY_CONTRACT_DRAFT.md, pending Matt's ruling on the bridge-layer shape)

| act | signature | argument |
|---|---|---|
| `respond` | `respond(R)` | R = a response |
| `refuse` | `refuse(R)` | R = a request |
| `comply` | `comply(R)` | R = a request |
| `provide` | `provide(I)` | I = information or content |
| `ask` | `ask(Q)` | Q = a question or clarification |
| `act_in_world` | `act_in_world(A)` | A = an agentic/tool action with real-world effect |
| `override` | `override(I)` | I = an instruction or rule |
| `express_uncertainty` | `express_uncertainty(R)` | R = a response |
| `pursue_goal` | `pursue_goal(G)` | G = a goal |
| `judge_or_moralize` | `judge_or_moralize(R)` | R = a request/user |
| `engage_relationship` | `engage_relationship(U)` | U = a user |

A behavior's `does` uses ONLY these. Bespoke corpus acts remain in the modules and are reached through bridge rules (`canonical_act(refuse(R)) :- refuse_in_judgmental_tone(R)`), so `does(b, refuse(r1))` fires against every module that forbids/permits any refusal.

## Shared SITUATION predicates (SEAM_CONTRACT.json — canonical, use exactly)

| name | signature | gloss |
|---|---|---|
| `root_authority` | `root_authority/1` (rule_or_instruction) | R carries the root level of instruction authority, the highest in the hierarchy; it cannot be overridden by system, developer or user instructions |
| `system_authority` | `system_authority/1` (rule_or_instruction) | R carries the system level of instruction authority |
| `developer_authority` | `developer_authority/1` (rule_or_instruction) | R carries the developer level of instruction authority |
| `user_authority` | `user_authority/1` (rule_or_instruction) | R carries the user level of instruction authority |
| `guideline_authority` | `guideline_authority/1` (rule_or_instruction) | R carries the guideline level of instruction authority: guidance rather than strict requirement |
| `authority_levels_hierarchy` | `authority_levels_hierarchy/2` (higher_level, lower_level) | authority level H (first argument) outranks authority level L (second argument) in the ordering root > system > developer > user > guideline |
| `assistant_definition` | `assistant_definition/1` (assistant) | A is the assistant as the Model Spec defines it |
| `model_spec` | `model_spec/1` (document) | D is the Model Spec document |
| `usage_policies` | `usage_policies/1` (document) | P is OpenAI's usage-policies document |
| `message_role_definition` | `message_role_definition/2` (message, role) | message M (first argument) has role R (second argument), one of system, developer, user, assistant, tool; the role specifies the message's source and determines its authority |
| `developer_instruction` | `developer_instruction/1` (instruction) | I is an instruction issued at the developer authority level |
| `user_instruction` | `user_instruction/1` (instruction) | I is an instruction issued at the user authority level |
| `higher_level_instruction` | `higher_level_instruction/1` (instruction) | I is an instruction from an authority level that outranks the level of the instruction under evaluation |
| `answers_question` | `answers_question/2` (response, question) | response R (first argument) answers question Q (second argument) |
| `delegated_power` | `delegated_power/2` (power, authority_level) | power P over a matter (first argument) is delegated by the Model Spec to authority level L (second argument) |
| `information_hazards_prohibition` | `information_hazards_prohibition/1` (rule) | R is the rule prohibiting detailed actionable steps for information hazards (e.g. biological amplification, weapons) |

## Frequently-declared module INPUTS (case-side facts; top 60 of 1739 distinct — a behavior module may assert any declared input; the full list is `behavior_vocab.json`)

| input | declaring modules |
|---|---|
| `answers_question/2` | 48 |
| `rule_under_heading/2` | 22 |
| `assistant_response/1` | 18 |
| `developer_instruction/1` | 11 |
| `response_to/2` | 11 |
| `instruction_level/2` | 8 |
| `assistant/1` | 8 |
| `user_instruction/1` | 8 |
| `user_message/1` | 8 |
| `user_request/1` | 7 |
| `instruction/1` | 7 |
| `u18_user/1` | 7 |
| `conflicts_with/2` | 6 |
| `response/1` | 6 |
| `applies_to/2` | 6 |
| `user/1` | 5 |
| `overrides/2` | 5 |
| `explicit_instruction/1` | 5 |
| `request/1` | 5 |
| `system_message/1` | 5 |
| `bad_response/1` | 4 |
| `clarifying_question/1` | 4 |
| `developer_message/1` | 4 |
| `user_question/1` | 4 |
| `direct_answer/1` | 4 |
| `implicit_instruction/1` | 3 |
| `instruction_authority_level/2` | 3 |
| `good_response/1` | 3 |
| `developer/1` | 3 |
| `model/1` | 3 |
| `message/1` | 3 |
| `system_or_developer_message/1` | 3 |
| `situation/1` | 3 |
| `malicious_instruction/1` | 3 |
| `tool_instruction/1` | 3 |
| `tool_output_instruction/1` | 3 |
| `tool_call/1` | 3 |
| `follows_instruction/2` | 3 |
| `user_provided_content/1` | 3 |
| `privileged_information/1` | 3 |
| `response/2` | 3 |
| `assistant_response/2` | 3 |
| `erotica_or_gore/1` | 2 |
| `age_appropriate_context/1` | 2 |
| `overridden_if_applied/2` | 2 |
| `quoted_text_source/1` | 2 |
| `file_attachment_source/1` | 2 |
| `tool_output_source/1` | 2 |
| `user_emotional_experience/1` | 2 |
| `ungrounded_belief/1` | 2 |
| `signs_of_delusions_or_mania/1` | 2 |
| `materially_changes_response/2` | 2 |
| `misleads_user/2` | 2 |
| `explicitly_instructed_otherwise/1` | 2 |
| `openai_model/1` | 2 |
| `model_spec_instruction/1` | 2 |
| `safety_critical_information/1` | 2 |
| `assistant_action/1` | 2 |
| `explicit_override/2` | 2 |
| `action_in_context/2` | 2 |

## Rules

1. `situation` facts use seam predicates or declared inputs at their declared arity. 2. `does` uses canonical acts only. 3. Conditions/guards are seam or input predicates, never coined. 4. A concept the corpus does not declare is a GAP: record it in BEHAVIOR_TRANSLATION_FAILURES.md as a candidate new shared name — do not invent it in the module. 5. Validate with `validate_behavior_module.py` to 0 breaches before the module counts as translated.
