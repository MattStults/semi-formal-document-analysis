# Expressibility sweep report

vocabulary: vocabulary_pilot.json (25 atoms, 7 axioms)

| status | count |
|---|---|
| EXPRESSIBLE | 3 |
| INEXPRESSIBLE | 1 |
| PARTIAL | 1 |

## helpfulness: EXPRESSIBLE
witness world: `act(disclose_i), act(hedge_p), ctx(user_wants_info)`

## avoiding-over-and-under-caution: EXPRESSIBLE

## harm-avoidance-to-third-parties: INEXPRESSIBLE
unmapped concepts (deterministic signal):
  - potential_harm_to_third_parties
  - avoid_harm_to_third_parties
errors: ['unknown atom: potential_harm_to_third_parties', 'unknown atom: avoid_harm_to_third_parties', 'unmapped concept: potential_harm_to_third_parties', 'unmapped concept: avoid_harm_to_third_parties']
escalations proposed: [{'kind': 'atom', 'proposal': 'potential_harm_to_third_parties', 'span': 'potential harm to those outside the conversation'}, {'kind': 'atom', 'proposal': 'avoid_harm_to_third_parties', 'span': 'avoiding actions or content that harm third parties'}]

## sycophancy-avoidance: EXPRESSIBLE

## transparency-about-limits: PARTIAL
unmapped concepts (deterministic signal):
  - model_cannot_help
errors: ['unknown atom: model_cannot_help', 'unmapped concept: model_cannot_help']
escalations proposed: [{'kind': 'atom', 'proposal': 'model_cannot_help', 'span': 'The model should proactively tell users what it cannot help with in the current context'}]
