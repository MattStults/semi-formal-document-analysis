# Shared-name signatures (the seam contract)

Some predicate names are SHARED across the whole corpus: many nodes borrow
them, and a link between modules only fires when everyone writes the same
signature. For the names below, the signature is FIXED. Use it exactly —
the arity, the argument order, and the document-wide meaning. Do not
re-gloss one of these names in terms of your own node's section: your module
receives the document-wide predicate once linked, so a section-local gloss
would be a false statement about it. If your node genuinely needs a
different shape, keep the contract signature in `requires` and record the
disagreement in your `concepts` gloss — do not fork the arity.

| name | signature | meaning |
|---|---|---|
| `root_authority/1` | `root_authority(R)` | rule/instruction R carries the root level of instruction authority (highest; not overridable by system, developer or user instructions) |
| `system_authority/1` | `system_authority(R)` | R carries the system level of instruction authority |
| `developer_authority/1` | `developer_authority(R)` | R carries the developer level of instruction authority |
| `user_authority/1` | `user_authority(R)` | R carries the user level of instruction authority |
| `guideline_authority/1` | `guideline_authority(R)` | R carries the guideline level: guidance rather than strict requirement |
| `authority_levels_hierarchy/2` | `authority_levels_hierarchy(H, L)` | level H (first argument) outranks level L (second) in root > system > developer > user > guideline |
| `assistant_definition/1` | `assistant_definition(A)` | A is the assistant as the Model Spec defines it |
| `model_spec/1` | `model_spec(D)` | D is the Model Spec document |
| `usage_policies/1` | `usage_policies(P)` | P is OpenAI's usage-policies document |
| `message_role_definition/2` | `message_role_definition(M, R)` | message M (first argument) has role R (second): system, developer, user, assistant or tool |
| `developer_instruction/1` | `developer_instruction(I)` | I is an instruction issued at the developer authority level |
| `user_instruction/1` | `user_instruction(I)` | I is an instruction issued at the user authority level |
| `higher_level_instruction/1` | `higher_level_instruction(I)` | I is an instruction from a level that outranks the instruction under evaluation |
| `answers_question/2` | `answers_question(R, Q)` | response R (first argument) answers question Q (second) |
| `delegated_power/2` | `delegated_power(P, L)` | power P (first argument) is delegated by the Model Spec to authority level L (second) |
| `information_hazards_prohibition/1` | `information_hazards_prohibition(R)` | R is the rule prohibiting detailed actionable steps for information hazards |

When you need an authority LEVEL as a term (for orderings or
`instruction_level/2`-style relations), use a distinct level constant (the
worked example's `defaults_level` is the demonstrated pattern) — never the
`/1` predicate name in a constant position.
