# Expressibility sweep report

vocabulary: vocabulary_pilot.json (25 atoms, 7 axioms)

| status | count |
|---|---|
| PARTIAL | 3 |
| EXPRESSIBLE | 1 |
| INEXPRESSIBLE | 1 |

## helpfulness: EXPRESSIBLE
witness world: `act(disclose_i), ctx(user_wants_info)`

## avoiding-over-and-under-caution: PARTIAL
unmapped concepts (deterministic signal):
  - unnecessary_refusal
  - avoid_over_and_under_caution
errors: ['unmapped concept: unnecessary_refusal', 'unmapped concept: avoid_over_and_under_caution']
escalations proposed: [{'kind': 'atom', 'proposal': 'unnecessary_refusal', 'span': 'unnecessary refusals'}, {'kind': 'atom', 'proposal': 'avoid_over_and_under_caution', 'span': 'avoid excessive caution and unnecessary refusals'}]

## harm-avoidance-to-third-parties: INEXPRESSIBLE
unmapped concepts (deterministic signal):
  - potential_harm_to_third_parties
  - avoid_harmful_content
errors: ['unknown atom: harm_third_parties', 'unknown atom: avoid_harmful_content', 'unmapped concept: potential_harm_to_third_parties', 'unmapped concept: avoid_harmful_content']
escalations proposed: [{'kind': 'atom', 'proposal': 'harm_third_parties', 'span': 'harm to those outside the conversation'}, {'kind': 'atom', 'proposal': 'avoid_harmful_content', 'span': 'avoiding actions or content that harm third parties'}]

## sycophancy-avoidance: PARTIAL
unmapped concepts (deterministic signal):
  - bel_true_of_not_p
errors: ['unknown atom: bel_true_of_not_p', 'unmapped concept: bel_true_of_not_p']
escalations proposed: [{'kind': 'atom', 'proposal': 'bel_true_of_not_p', 'span': 'when it believes something different is true'}]

## transparency-about-limits: PARTIAL
unmapped concepts (deterministic signal):
  - model_cannot_help_with_i
errors: ['unknown atom: model_cannot_help_with_i', 'unmapped concept: model_cannot_help_with_i']
escalations proposed: [{'kind': 'atom', 'proposal': 'model_cannot_help_with_i', 'span': 'model cannot help with i'}]
