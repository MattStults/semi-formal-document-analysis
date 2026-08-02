# Adjudication worksheet --- conflict delta

Deltas only. Both-found items are skipped (§1: low information).

| metric | value |
|---|---|
| `|C_tool|` | 1 |
| `|C_baseline|` | 2 |
| tool_only | 0 |
| baseline_only | 1 |
| both | 1 |
| tool_self_agreement (k=1) | n/a |
| baseline_self_agreement (k=1) | n/a |
| coverage | 0.048 (2/42) |
| unencoded | 40 |

## Stop rules (contract §6 --- decided before results, read before you start)

- **Coverage < 70%** (fewer than 30 of 42 provisions encoded) --- stop; the
  loop would be measuring extraction gaps, not conflict quality.
- **`baseline_self_agreement` ~ 0** --- the comparator can't hold still.
  Report it and stop.
- **After 10 adjudications: ARTIFACT >= 6 and zero items marked REAL with
  "would not have found it"** --- noise without insight. Stop.
- **`attribution_rate` < 0.5** --- deltas don't localize; fixes are guesswork.
  Stop.
- **Fixes regress on most attempts** --- changes aren't local. Stop.

## How to adjudicate (§1)

The document is ground truth; the frontier model is a lead generator, never an
oracle. Ask **"which span licenses this, and does it assert more?"** --- never
"is this a real distinction?". The full clause is printed for exactly this
reason. A fix lands only when the source text says the tool was wrong.


**0 tool-only + 1 baseline-only = 1 items to adjudicate** (1 both-found skipped).

---

<!-- ITEM baseline_only fa_2bl7 fa_zyu5 -->
### 1. baseline_only --- `fa_2bl7` + `fa_zyu5`

**`fa_2bl7`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L197` --- conditional

> For example, Model Spec principles with user authority can be overridden by explicit developer[^zyu5] or user[^2bl7] instructions, and principles with guideline authority can be overridden by explicit[^3u2u] or *implicit*[^4q1u] developer or user instructions (see [?](#letter_and_spirit)).

*anchor span:* “or user”

**`fa_zyu5`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L197` --- conditional

> For example, Model Spec principles with user authority can be overridden by explicit developer[^zyu5] or user[^2bl7] instructions, and principles with guideline authority can be overridden by explicit[^3u2u] or *implicit*[^4q1u] developer or user instructions (see [?](#letter_and_spirit)).

*anchor span:* “For example, Model Spec principles with user authority can be overridden by explicit developer”

**Witness.** a baseline-only tension

**Note.** synthetic

*asserted by:* smoke-b

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---
