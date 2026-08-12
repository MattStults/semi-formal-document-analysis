# Document-graph experiment — the key, written BEFORE the first run

**Matt's design.** Ask a model to segment the document into a **graph of nodes**, where each node
carries a prose description of what it establishes, what it **needs** from elsewhere, and what it
**provides**. No constraint on overlap or section boundaries; a node addresses text by **line
ranges**. Bias to simplicity — add nodes only when forced. Multi-turn: revise until every fact is
placed. Then: does it catch relationships we already know about?

⛔ **Written before any run**, per `REPRODUCIBILITY.md`'s sandwich rule. Everything below is
checkable mechanically against line numbers, except where marked as a reading.

---

## Why a graph at all — the finding that forced it `[RAN]`

The authority ranking is stated **nowhere in the document's sentences**:

```
L0183  Here is the ordering of authority levels...
L0186  **Root**: Model Spec "root" sections
L0187  **System**: Model Spec "system" sections and system messages
L0188  **Developer**: ...
L0189  **User**: ...
L0190  **Guideline**: ...
L0191  *No Authority*: assistant and tool messages; quoted/untrusted text...
```

`L0186` in full is *"**Root**: Model Spec 'root' sections"*. **There is no comparative in it.** Root
outranks System because it is printed first. So a pipeline that translates one clause at a time can
never recover the ranking — and `[RAN]` `higher_authority/2` was the single most-wanted predicate in
a 5-clause sample, borrowed independently by two clauses and provided by none.

⇒ The ordering is a property of the **arrangement**, and only a unit that spans the list can carry it.

## What the graph must catch — five pre-registered checks

| | check | mechanically testable? |
|---|---|---|
| **K1** | ⭐ **the ranking is ONE node** (or a parent node over item nodes) spanning **L0183–L0191**, and its `provides` mentions an **order / ranking / precedence** — not merely "authority levels exist" | line span: yes · wording: a reading |
| **K2** | the applicability conditions **L0195–L0199** (*not applicable if misaligned* / *if superseded* / *if mistaken*) form **one node**, not three unrelated ones | yes |
| **K3** | some node covering **L0181** (*"follow all applicable instructions"*) **needs** what K1's node provides — an actual edge between them | yes, once node ids are resolved |
| **K4** | the definitions run **L0114+** provides concepts that other nodes need — at least one **cross-section edge** | yes |
| **K5** | ⛔ **overlap or nesting is actually used somewhere** — if every node is a disjoint line range, the model has reproduced section segmentation and the freedom bought nothing | yes |

⚠️ **K5 is the one that decides whether this design differs from what we already have.** A graph of
disjoint ranges IS the current corpus with extra fields.

## What would count as a failure

- **K1 fails** ⇒ the central motivating case is not caught, and the design does not solve the problem
  it was invented for.
- **K5 fails** ⇒ no overlap anywhere ⇒ the graph adds descriptions but not structure.
- ⛔ **Line ranges that do not exist, or `needs` that no node `provides`, in numbers** ⇒ the graph is
  decorative. A dangling `needs` is *expected and fine* where the document genuinely does not supply
  it (that is a finding); dangling in the majority is not.

## Constraints the prompt must carry, each from a measured result

| constraint | why, `[RAN]` |
|---|---|
| ⛔ **PROSE only in `needs`/`provides` — never invented predicate names** | asking a model to predict the NAMES a translator will coin scored **1 of 32**, then **0 of 32**. Asking at the level of ideas scored **4 of 4** |
| line ranges, not quoted text | quoting is 89% verbatim at best; a line number is exact and checkable |
| bias to few nodes | untested here — Matt's judgement, recorded as such |
| iterate rather than one-shot | the iterative definition runs `[RAN]` **replaced** rather than resolved 62% of the time when nothing pinned the previous state; the audit turn must therefore ask what is UNPLACED, not "try again" |

## Then, and only if the above passes

1. repeat runs on one model → how much does the graph vary?
2. same prompt on a larger model → does the disagreement shrink, or change character?

⛔ **Nothing here is decided.** This is a test of whether the representation is reachable at all.
