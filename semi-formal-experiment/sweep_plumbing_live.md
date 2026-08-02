# Expressibility sweep report

vocabulary: vocabulary_pilot.json (25 atoms, 7 axioms)

| status | count |
|---|---|
| PARTIAL | 4 |
| INEXPRESSIBLE | 1 |

## helpfulness: PARTIAL
unmapped concepts (deterministic signal):
  - treating unhelpfulness as a real cost
  - safe default
errors: ['unmapped concept: treating unhelpfulness as a real cost', 'unmapped concept: safe default']
escalations proposed: [{'kind': 'atom', 'proposal': 'unhelpfulness_cost', 'span': 'treating unhelpfulness as a real cost rather than a safe default.'}, {'kind': 'atom', 'proposal': 'safe_default', 'span': 'treating unhelpfulness as a real cost rather than a safe default.'}]

## avoiding-over-and-under-caution: PARTIAL
unmapped concepts (deterministic signal):
  - avoid_unnecessary_refusals
  - avoid_harmful_compliance
  - errors_carry_real_costs
errors: ['unmapped concept: avoid_unnecessary_refusals', 'unmapped concept: avoid_harmful_compliance', 'unmapped concept: errors_carry_real_costs']
escalations proposed: [{'kind': 'atom', 'proposal': 'refuse_unnecessary', 'span': 'unnecessary refusals'}, {'kind': 'atom', 'proposal': 'harmful_compliance', 'span': 'harmful compliance'}, {'kind': 'atom', 'proposal': 'real_costs_of_errors', 'span': 'errors in either direction carry real costs'}]

## harm-avoidance-to-third-parties: INEXPRESSIBLE
unmapped concepts (deterministic signal):
  - harm_third_parties
  - weigh_harm
  - avoid_actions
  - avoid_content
errors: ['unmapped concept: harm_third_parties', 'unmapped concept: weigh_harm', 'unmapped concept: avoid_actions', 'unmapped concept: avoid_content']
escalations proposed: [{'kind': 'atom', 'proposal': 'harm_third_parties', 'span': 'The model should weigh the potential harm to those outside the conversation, avoiding actions or content that harm third parties, society, or the world.'}, {'kind': 'atom', 'proposal': 'weigh_harm', 'span': 'The model should weigh the potential harm to those outside the conversation, avoiding actions or content that harm third parties, society, or the world.'}, {'kind': 'atom', 'proposal': 'avoid_actions', 'span': 'The model should weigh the potential harm to those outside the conversation, avoiding actions or content that harm third parties, society, or the world.'}]

## sycophancy-avoidance: PARTIAL
unmapped concepts (deterministic signal):
  - belief_contradicts_user_preference
errors: ['unmapped concept: belief_contradicts_user_preference']
escalations proposed: [{'kind': 'atom', 'proposal': 'belief_contradicts_user_preference', 'span': 'model believes something different is true'}]

## transparency-about-limits: PARTIAL
unmapped concepts (deterministic signal):
  - degraded_answer_without_explanation
  - proactive
errors: ['unmapped concept: degraded_answer_without_explanation', 'unmapped concept: proactive']
