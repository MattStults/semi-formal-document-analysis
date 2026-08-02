# Adjudication worksheet --- conflict delta

Deltas only. Both-found items are skipped (§1: low information).

| metric | value |
|---|---|
| `|C_tool|` | 0 |
| `|C_baseline|` | 6 |
| tool_only | 0 |
| baseline_only | 6 |
| both | 0 |
| tool_self_agreement (k=1) | n/a (1/1 runs empty) |
| baseline_self_agreement (k=3) | 0.244 |
| coverage | 0.524 (22/42) |
| rules emitted vs rejected | 22 emitted, 2 rejected (of 24 extracted) |
| coverage_claimed (pre-rejection) | 0.571 (24/42) |
| unencoded | 18 |
| tool conflict channels open | NO (0 incompat, 0 acts both obliged and forbidden) |
| **degenerate** | yes — tool found no conflicts — every bucket is one-sided, `both` is vacuously empty, and no delta is a disagreement between two populated sets |

> **Degenerate comparison.** tool found no conflicts — every bucket is one-sided, `both` is vacuously empty, and no delta is a disagreement between two populated sets. Read the items below as *what the baseline asserted*, not as a disagreement between two populated conflict sets.

> **The tool's empty conflict set is not a solver finding.** The extraction declared 0 `incompat` pairs and no act that is both obliged and forbidden, and those are the only two ways the emitted program derives a conflict. Zero follows from the extraction before the solver runs.

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


**0 tool-only + 6 baseline-only = 6 items to adjudicate** (0 both-found skipped).

---

<!-- ITEM baseline_only fa_0prn fa_1ka0 -->
### 1. baseline_only --- `fa_0prn` + `fa_1ka0`

**`fa_0prn`** --- `model_spec@2025-12-18 > The chain of command > Respect the letter and spirit of instructions > L300` --- holistic

> The assistant should strive to detect conflicts and ambiguities --- even those not stated explicitly --- and resolve them by focusing on what the higher-level authority and overall purpose of the scenario imply[^0prn].

*anchor span:* “The assistant should strive to detect conflicts and ambiguities --- even those not stated explicitly --- and resolve them by focusing on what the higher-level authority and overall purpose of the scenario imply”

**`fa_1ka0`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L203` --- conditional

> The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior[^1ka0].

*anchor span:* “The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior”

**Encoding status.**
- `fa_0prn`: out of the encodable set --- not among the 42 conditional provisions (kind: holistic) — out of scope by design (§2), not an extraction gap
- `fa_1ka0`: unencoded --- not reported by the model; no rule was emitted for this provision (reason unstated)
- **Neither provision is encoded**: this pair lies entirely outside the encoding, so the tool could not have raised it whatever its logic. Default verdict OUT OF ENCODED SCOPE; this is a coverage cost, not a conflict-detection failure.

**Witness.** When a user instruction conflicts with a higher‑level instruction, the assistant must decide whether to engage in arguments or take directions about how to apply the higher‑level instruction, which [fa_0prn] requires resolving the conflict by focusing on higher‑level authority, while [fa_1ka0] forbids engaging in such arguments or directions.

**Note.** They collide because one requires engaging in conflict resolution, the other forbids it.

*asserted by:* baseline-together-cheap-20260801T093445-r1, baseline-together-cheap-20260801T093445-r2, baseline-together-cheap-20260801T093445-r3

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---

<!-- ITEM baseline_only fa_0prn fa_a9sh -->
### 2. baseline_only --- `fa_0prn` + `fa_a9sh`

**`fa_0prn`** --- `model_spec@2025-12-18 > The chain of command > Respect the letter and spirit of instructions > L300` --- holistic

> The assistant should strive to detect conflicts and ambiguities --- even those not stated explicitly --- and resolve them by focusing on what the higher-level authority and overall purpose of the scenario imply[^0prn].

*anchor span:* “The assistant should strive to detect conflicts and ambiguities --- even those not stated explicitly --- and resolve them by focusing on what the higher-level authority and overall purpose of the scenario imply”

**`fa_a9sh`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L199` --- holistic

> Sometimes it's difficult to tell if a user is asking a follow-up question or changing the subject; in these cases, the assistant should err on the side of assuming that the earlier context is still relevant when plausible, taking into account common sense cues including the amount of time between messages[^a9sh].

*anchor span:* “Sometimes it's difficult to tell if a user is asking a follow-up question or changing the subject; in these cases, the assistant should err on the side of assuming that the earlier context is still relevant when plausible, taking into account common sense cues including the amount of time between messages”

**Encoding status.**
- `fa_0prn`: out of the encodable set --- not among the 42 conditional provisions (kind: holistic) — out of scope by design (§2), not an extraction gap
- `fa_a9sh`: out of the encodable set --- not among the 42 conditional provisions (kind: holistic) — out of scope by design (§2), not an extraction gap
- **Neither provision is encoded**: this pair lies entirely outside the encoding, so the tool could not have raised it whatever its logic. Default verdict OUT OF ENCODED SCOPE; this is a coverage cost, not a conflict-detection failure.

**Witness.** When a user instruction conflicts with a higher‑level instruction, the assistant must decide whether to assume earlier context is still relevant; [fa_0prn] says to resolve the conflict by focusing on higher‑level authority, overriding earlier context, whereas [fa_a9sh] says to err on the side of assuming earlier context is still relevant when plausible.

**Note.** They collide because one requires ignoring earlier context, the other requires keeping it.

*asserted by:* baseline-together-cheap-20260801T093445-r1

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---

<!-- ITEM baseline_only fa_0q9d fa_bn8b -->
### 3. baseline_only --- `fa_0q9d` + `fa_bn8b`

**`fa_0q9d`** --- `model_spec@2025-12-18 > The chain of command > Assume best intentions > L681` --- conditional

> If the user asks for prohibited help to accomplish a permissible goal, the assistant should politely decline to offer the prohibited help and suggest other ways it could help with the permissible goal[^0q9d].

*anchor span:* “If the user asks for prohibited help to accomplish a permissible goal, the assistant should politely decline to offer the prohibited help and suggest other ways it could help with the permissible goal”

**`fa_bn8b`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L201` --- conditional

> The **only** other reason an instruction should be ignored is if it is beyond the assistant's capabilities[^bn8b].

*anchor span:* “The **only** other reason an instruction should be ignored is if it is beyond the assistant's capabilities”

**Encoding status.**
- `fa_0q9d`: encoded --- oblige decline_prohibited_help_and_suggest_alternatives
- `fa_bn8b`: unencoded --- not reported by the model; no rule was emitted for this provision (reason unstated)
- **One provision is outside the encoding**: the pair is unreachable for the tool as encoded. Default verdict OUT OF ENCODED SCOPE, naming the missing side.

**Witness.** When a user explicitly requests prohibited help, the assistant must decline per [fa_0q9d], but [fa_bn8b] says the only reason to ignore a user instruction is if it is beyond the assistant’s capabilities, creating a conflict over whether the assistant can ignore the user’s instruction.

**Note.** [fa_0q9d] requires refusal for prohibited content, while [fa_bn8b] limits ignoring instructions to capability issues.

*asserted by:* baseline-together-cheap-20260801T093445-r3

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---

<!-- ITEM baseline_only fa_1ka0 fa_agh7 -->
### 4. baseline_only --- `fa_1ka0` + `fa_agh7`

**`fa_1ka0`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L203` --- conditional

> The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior[^1ka0].

*anchor span:* “The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior”

**`fa_agh7`** --- `model_spec@2025-12-18 > The chain of command > Ignore untrusted data by default > L723` --- conditional

> In such cases, the assistant should ask for [clarification](#ask_clarifying_questions) before proceeding if possible[^agh7].

*anchor span:* “In such cases, the assistant should ask for [clarification](#ask_clarifying_questions) before proceeding if possible”

**Encoding status.**
- `fa_1ka0`: unencoded --- not reported by the model; no rule was emitted for this provision (reason unstated)
- `fa_agh7`: encoded --- oblige ask_for_clarification_before_proceeding_if_possible
- **One provision is outside the encoding**: the pair is unreachable for the tool as encoded. Default verdict OUT OF ENCODED SCOPE, naming the missing side.

**Witness.** When a user instruction conflicts with a higher‑level instruction, the assistant must decide whether to ask for clarification; [fa_agh7] requires asking for clarification before proceeding, whereas [fa_1ka0] forbids engaging in arguments or taking directions about how higher‑level instructions should be applied.

**Note.** They collide because one requires asking for clarification, the other forbids such engagement.

*asserted by:* baseline-together-cheap-20260801T093445-r1

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---

<!-- ITEM baseline_only fa_1ka0 fa_m12p -->
### 5. baseline_only --- `fa_1ka0` + `fa_m12p`

**`fa_1ka0`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L203` --- conditional

> The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior[^1ka0].

*anchor span:* “The assistant should generally refuse to engage in arguments or take directions about how higher-level instructions should be applied to its current behavior”

**`fa_m12p`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L181` --- conditional

> This includes all system, developer and user instructions except for those that conflict with a higher-authority instruction[^m12p] or a later instruction at the same authority[^d32l].

*anchor span:* “This includes all system, developer and user instructions except for those that conflict with a higher-authority instruction”

**Encoding status.**
- `fa_1ka0`: unencoded --- not reported by the model; no rule was emitted for this provision (reason unstated)
- `fa_m12p`: unencoded --- not reported by the model; no rule was emitted for this provision (reason unstated)
- **Neither provision is encoded**: this pair lies entirely outside the encoding, so the tool could not have raised it whatever its logic. Default verdict OUT OF ENCODED SCOPE; this is a coverage cost, not a conflict-detection failure.

**Witness.** When a user instructs the assistant to explain how higher‑level instructions should be applied, [fa_m12p] says the assistant must follow all system, developer, and user instructions unless they conflict with higher authority, so it should comply; however, [fa_1ka0] says the assistant must refuse to engage in arguments or take directions about how higher‑level instructions should be applied.

**Note.** The two provisions conflict over whether the assistant should comply with the user’s request.

*asserted by:* baseline-together-cheap-20260801T093445-r2

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---

<!-- ITEM baseline_only fa_a9sh fa_agh7 -->
### 6. baseline_only --- `fa_a9sh` + `fa_agh7`

**`fa_a9sh`** --- `model_spec@2025-12-18 > The chain of command > Follow all applicable instructions > L199` --- holistic

> Sometimes it's difficult to tell if a user is asking a follow-up question or changing the subject; in these cases, the assistant should err on the side of assuming that the earlier context is still relevant when plausible, taking into account common sense cues including the amount of time between messages[^a9sh].

*anchor span:* “Sometimes it's difficult to tell if a user is asking a follow-up question or changing the subject; in these cases, the assistant should err on the side of assuming that the earlier context is still relevant when plausible, taking into account common sense cues including the amount of time between messages”

**`fa_agh7`** --- `model_spec@2025-12-18 > The chain of command > Ignore untrusted data by default > L723` --- conditional

> In such cases, the assistant should ask for [clarification](#ask_clarifying_questions) before proceeding if possible[^agh7].

*anchor span:* “In such cases, the assistant should ask for [clarification](#ask_clarifying_questions) before proceeding if possible”

**Encoding status.**
- `fa_a9sh`: out of the encodable set --- not among the 42 conditional provisions (kind: holistic) — out of scope by design (§2), not an extraction gap
- `fa_agh7`: encoded --- oblige ask_for_clarification_before_proceeding_if_possible
- **One provision is outside the encoding**: the pair is unreachable for the tool as encoded. Default verdict OUT OF ENCODED SCOPE, naming the missing side.

**Witness.** When a long user message contains embedded instructions, the assistant must decide whether to assume earlier context is still relevant or to ask for clarification; [fa_a9sh] says to assume earlier context is still relevant when plausible, while [fa_agh7] says to ask for clarification before proceeding if possible.

**Note.** They collide because one requires assuming earlier context, the other requires asking for clarification.

*asserted by:* baseline-together-cheap-20260801T093445-r1

Verdict --- check exactly one:

- [ ] REAL
- [ ] ARTIFACT --- responsible atom or rule: ____
- [ ] RESOLVED ELSEWHERE --- clause id: ____
- [ ] OUT OF ENCODED SCOPE --- missing atom: ____

Would I have found this by reading the section carefully?  Y / N  ->  answer: __

---
