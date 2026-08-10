# Free pre-flight of the borrow-description change — 4 Haiku runs, $0.00

Matt: *"can you do a manual run against haiku to test this before we do real spend"*.

Method: build the **real** system and user prompts with `translate.build_system` /
`build_user`, hand them verbatim to subagents, write the JSON back, and put it through
`schema.validate`. Two clauses × two runs. No API spend.

⚠️ **Haiku is not the production translator** (`deepseek-v4-flash`), so rates here do not transfer.
What transfers is anything STRUCTURAL — a rule that cannot be followed, or a kind of disagreement
that no prompt wording could remove.

---

## 1 · ⛔ It found a defect before any spend: the rule was never stated

The change added a validator and updated the worked example — **and never wrote the instruction
down**. `10_output_format.md` states *"every predicate you reference must be declared"* and said
nothing about a description.

⇒ Every clause with a borrowed condition would have been **rejected for a rule it was never told**,
burning repair attempts, and it would have presented as *"the model cannot follow the format"*
rather than *"we forgot to say"*. Fixed before the runs.

## 2 · The format is followable and the rule bites

| | |
|---|---|
| validate first pass | **2 of 4** |
| the 2 failures | an act used but not declared in `acts`; both **unrelated** to the new rule — ordinary stage-2 repair |
| `requires` entries with a substantive gloss | **all of them** |
| hollow glosses (name restated) | **0** |

Both agents volunteered that the instruction was clear, one paraphrasing it correctly and
unprompted: *"the gloss must state what makes it true, not restate the name."*

## 3 · ⛔ THE FINDING: two runs carve the same sentence at different GRANULARITIES

`m0079`, same clause, same prompt:

| run A | run B |
|---|---|
| `higher_authority(J,I)` — *J has higher authority than I* | `conflicts_with_higher_authority(I)` — *I contradicts an instruction with higher authority* |
| `conflicts(I,J)` — *I and J cannot both be satisfied* | |
| `same_authority(I,J)` — *same authority level* | `superseded_by_later_same_level(I)` — *displaced by a later instruction at the same level* |

⭐ **These are not two names for one concept. They are two different carvings.** B's single condition
is approximately A's two conditions conjoined. And **the arities differ** — A uses only `/2`, B uses
`/1` and `/2` — so they cannot pair one-to-one even in principle, because arity is part of a
predicate's identity.

`[RAN]` **borrowed names shared between the two runs: 0 of 8 on `m0079`, 0 of 7 on `m0150`.**

⇒ **A layer of disagreement UNDERNEATH naming, which no gloss quality can remove.** Descriptions do
let a reader see that B's bundle equals A's conjunction — but that is a **many-to-one match across
different shapes**, not the one-to-one lookup the linking design assumes.

## 4 · ⚠️ CORRECTION — the one encouraging number from the paid run does not reproduce

The paid DeepSeek runs measured borrowed-name agreement rising from `[RAN]` **0.00 → 0.50**
(diagnosis set) and **0.69** (held-out) after the worked-example fix. It was reported with the
caveat *"NOT predicted… an observation at small n, not a confirmed hypothesis, and it should be
re-measured before anything is built on it."*

**Re-measured here: 0.00 and 0.00.**

Either Haiku varies more than DeepSeek, or the earlier figure was noise at 9–16 symbols. **Either
way it must not be relied on**, and no design should assume names got more stable.

## 5 · What this does and does not change

✅ **Keep the description change.** It is cheap, followable, produces substantive text, makes
borrowed conditions readable to a reviewer, and unblocks the two specs that Q-22's fix left blocked.
Its value does not depend on linking working.

⛔ **Do NOT yet spend on translating whole sections for linking.** The plan assumed matching one
borrowed condition to one definition. That is not the shape of the problem: matching would have to
handle one-condition-to-several and mismatched argument counts.

⚠️ **Open, not decided** — three ways this could go, none tested:
- constrain the carving in the prompt (*"prefer the finest-grained conditions the clause itself
  names"*) and re-measure whether granularity converges;
- accept many-to-one matching and design the matcher for it;
- match at the **clause** level rather than the predicate level — *"which clause bears on this?"* is
  the question the tool actually answers, and it may not need predicate identity at all.

⭐ The last one deserves weight: it is the only option that does not require the linking problem to
be solved first, and it is closer to what the product claims.
