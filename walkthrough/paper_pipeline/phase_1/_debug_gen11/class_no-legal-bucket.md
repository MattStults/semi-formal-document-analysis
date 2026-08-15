# M1 — the invented descriptive predicate has no legal declaration bucket

**Mechanism, one sentence.** To say anything at all about a span the model must invent a
descriptive predicate for the property the span describes, and for a span that is a
glossary entry, a statement about the document, or a commitment about OpenAI's products,
that predicate is a fact about neither the case being judged (`inputs`) nor another
node's claim (`requires`), so the model declares it in `concepts` — which the checker
explicitly refuses as a declaration — and there is no fourth list.

**This is the biggest class in the run by both rankings: 81 repair rounds, $0.1196 of
$0.2415 repair spend (50%), and 12 of the 19 lost modules (63%).**

---

> ⚠️ **Standing caveat on the 08-15 comparison.** `20260815-070038-together-deepseek-v4-flash`
> was **still in flight** while this analysis was written (its `run.json`, `health.jsonl`
> and `inflight/` are live, and graveyard entries were still appearing). Its outcomes are a
> **snapshot**, they will change, and **no count from it may be pinned into a test** — per
> `TRANSLATION_REPAIR_CENSUS.md` §9 and `AGENTS.md`. Nothing under `runs/` or
> `repair_graveyard/` was written to by this analysis. Its 08-14 numbers, by contrast, are
> from two completed runs and are stable.

## How to recognise it

* Finding is `undeclared-body-name` on a name that appears **nowhere in the graph**:
  measured, **201 of 206** `undeclared-body-name` findings name a predicate the graph
  never mentions (2% are graph-supplied). Compare M2, where 70% of the names *are*
  graph-supplied.
* The final module has an `ontology` rule whose `body` is made of those names and an
  **empty `inputs` list**. Measured over the 30 clauses that ever drew an
  `undeclared-body-name` finding:

  | | clauses | with EMPTY `inputs` in the final module |
  |---|---|---|
  | recovered (translated) | 17 | 3 |
  | never recovered (unrepaired) | 13 | **10** |

  The recovery move, when it happens, is one edit: **move the invented predicate into
  `inputs`**. Nothing else changes.
* The node's `establishes` is not an obligation. Hand-classified over the 19 unrepaired:
  **6 glossary/definitional, 6 about-the-document, 2 applicability/commitment, 1
  descriptive-capability, 4 genuinely normative.**

---

## The exact finding text

```
<root>: body references `sets_out_guidance` but nothing declares it. Put it in this
module's `ontology`, in `requires` (another clause defines it), or in `inputs` (a fact
about the case). ⚠️ A `concepts` entry alone does NOT declare it — concepts carry
meaning, not provenance; `sets_out_guidance/N` must ALSO appear in one of those three.
An undeclared name cannot be told apart from a typo
```

The parenthetical is the whole mechanism. The three offered homes are `ontology` (which
needs its own body, so the regress just moves), `requires` (which the graph adapter
reserves: *"these concepts are established by OTHER nodes of the graph, so every one of
them belongs in this module's `requires`, spelled EXACTLY as given"*), and `inputs`,
which the same adapter paragraph restricts: *"`inputs` is only for plain facts about the
situation being judged (messages, roles, case data) that YOU identify"*.

`interacted_with_by_end_user_or_developer(A)` is not a message, a role or case data. By
the prompt's own definition **there is no bucket for it**, and the model complies with
the prompt rather than with the checker.

---

## The controlled pair that proves it is the bucket, not the text

Three glossary spans of the same shape succeeded on attempt 1; two failed five times.
The only difference is where the invented predicate was declared.

**SUCCEEDS — `l1_170_n055`, 1 attempt.** Verbatim document text:

> `User: Instructions from end users.`

```json
"ontology": [{"atom": "instruction_level(I, user_level)", "body": "user_instruction(I)"}],
"inputs":   ["user_instruction/1"],
"requires": ["authority_levels_hierarchy/2"]
```

**SUCCEEDS — `l1_170_n070`, 1 attempt.** Verbatim:

> `` `developer`: from the application developer (possibly also OpenAI) ``

```json
"ontology": [{"atom": "developer_role(M)", "body": "from_application_developer(M)"}, …],
"inputs":   ["from_application_developer/1", "from_openai/1"]
```

**FAILS — `l1_170_n069`, 5 attempts, no module.** Verbatim:

> `` `system`: messages added by OpenAI ``

```json
"ontology": [{"atom": "system_message(M)",
              "body": "message_role(M, system), added_by_openai(M)"}],
"concepts": ["system_message", "message_role", "added_by_openai", "message_role_definition"],
"inputs":   []
```

**FAILS — `l1_170_n065`, 5 attempts, no module.** Verbatim:

> `Assistant: the entity that the end user or developer interacts with. (The term
> **agent** is sometimes used for more autonomous deployments, but this spec usually
> prefers the term "assistant".)`

```json
"ontology": [{"atom": "assistant_definition(A)",
              "body": "interacted_with_by_end_user_or_developer(A)"}],
"concepts": ["assistant_definition", "autonomous_deployment"],
"inputs":   []
```

Identical module shape. `user_instruction/1` reads as a fact about the situation being
judged, so the model was willing to call it an input. `interacted_with_by_end_user_or_developer/1`
does not, so it was not. **The failure tracks whether the invented predicate sounds like
case data, not whether the span is translatable.**

---

## Two more verbatim excerpts, from the two most expensive members

**`l1_170_n062` — 5 attempts, frozen byte-identical all five, 9 findings every round.**
Verbatim (L105):

> `Why include default instructions at all? Consider a request to write code: without
> additional style guidance or context, should the assistant provide a detailed,
> explanatory response or simply deliver runnable code? … In theory, the assistant can
> derive some of these answers from higher level principles in the spec. In practice,
> however, it's impractical…`

Findings, every round, unchanged: `default_instruction` ×4, `overridable_guideline` ×4,
`derived_on_the_fly` ×1 — all `undeclared-body-name`. This is a paragraph of *rationale
about why the document has defaults*. It contains no obligation.

**`l1_170_n015` — 5 attempts, 6 findings every round.** Verbatim (L23):

> `The rest of the document consists of direct instructions to the model, beginning with
> some foundational definitions that are used throughout the document. These are followed
> by a description of the chain of command… The remaining sections cover specific
> principles that guide the model's behavior.`

Invented: `rest_of_document_section` (20 findings), `document_order` (10). The model is
being asked to formalise a **table of contents**.

---

## Recovery — what changed when it did

18 of the 30 clauses in this class recovered. Two distinct routes, both visible in the
transcripts:

1. **Move to `inputs`** — `l1_170_n073`, attempt 1 → 2, the only change in the module:
   ```
   att 1  inputs: []              ontology body: "message_role(M, tool)"
   att 2  inputs: ["message_role/2"]   ontology body: "message_role(M, tool)"   ← passes
   ```
   Same for `l1_170_n067` (attempt 2 adds `has_role/2, has_content/2, consists_of/2,
   list_of_messages/1` to `inputs`; bodies untouched).
2. **Give the invented predicate its own ontology head** — `l1_170_n086`, attempt 3 adds
   two `token_definition(T)` entries so `atomic_unit` / `measures_length` acquire heads.
   `inputs` stays empty. This route inflates the module rather than declaring provenance.

**And the decisive recovery evidence: a fresh sample.** Run `20260815-070038` re-ran 18
of the 19 unrepaired clauses under a **byte-identical prompt** (same `user_sha`, same
`system_sha 5ff9daf7fe58845f`, same params). Of the 12 modules this class lost, **9
translated on the retry** (`n014` 2 att, `n023` 2, `n037` 1, `n052` 1, `n062` 1, `n065`
3, `n069` 1, `n087` 2, `n088` 3); 3 remained unrepaired (`n058`, `n078`, `n084`) and
`n015` abstained. The whole 19-clause retry cost 45 calls against the 95 calls the
08-14 repair loop spent to produce nothing.

**So the span is not untranslatable. The model has a legal move and finds it about half
the time; the repair loop does not help it find it** (see `class_repair-fixed-point.md`:
50 of the 76 repair rounds on unrepaired clauses returned byte-identical modules).

---

## The paid cost of the class

Priced from the 230 transcript turns matched 1:1 to `semi-formal-experiment/usage.jsonl`
on `content_chars` (0 unmatched). A round's cost is split evenly across the distinct
mechanisms in the finding set that caused it.

| | |
|---|---|
| repair rounds in which this class appears | **81 of 130 (62%)** |
| findings | 206 of 341 (60%) |
| clauses touched | 30 of 100 |
| **attributed spend** | **$0.1196** of $0.2415 repair spend (**50%**) |
| **modules lost** | **12 of 19** |
| measured per-call rate on these runs | $0.001761 mean, $0.001636 median |

Projected onto the 773-node corpus at this run's rate, this one class is ~$0.92 of
repair and ~93 lost modules — the lost modules being the number that matters.

---

## FALSIFIER

The hypothesis is *the bucket is missing, and the span type predicts which spans hit it*.
It is wrong if either of these is true:

1. **Re-run the 12 lost clauses with `inputs` pre-populated** (or with the adapter's
   `inputs` sentence widened to admit definitional properties) and the
   `undeclared-body-name` findings do **not** fall. If they persist, the bucket is not
   the constraint and the model simply cannot decide provenance.
2. **The span-type story fails on the succeeding population.** It already nearly does:
   about 20 of the 36 first-pass successes are also non-normative (`n001` "The Model Spec
   outlines the intended behavior…", `n013` "dedicated to the public domain", `n017`
   "Human safety and human rights are paramount", `n061` "The levels of authority are
   further explored in a later section"). **Span type alone does not predict failure** —
   this is the single most important caveat in this file, and it is why the coordinating
   instance's hand-classification of the 19 unrepaired, while confirmed in shape (16/19
   non-normative), cannot carry the conclusion on its own. If a fix routes on span type
   alone it will divert ~20 spans that were translating fine at $0.0015 each.

---

## Candidate solutions already on record

* **Fix F — "body literals carry their origin"** (`TRANSLATION_FIX_PLAN.md`) is the only
  candidate that targets this class. Reviewed **REJECT / not ready**
  (`TRANSLATION_CENSUS_REVIEW.md` §8): *"Making the origin a required field does not make
  the choice; it relocates the same decision into a field the model must still fill, and
  converts a good message ('nothing declares it') into a worse one ('origin says ontology
  but it is not there')."* The review also refuses its 27 marginal kills as the least
  defensible subtraction in the plan.
* **Is that defect fatal to the idea, or only to the diff?** On this run's evidence,
  **fatal to F as scoped, and for a reason the review did not have.** F assumes the model
  is failing to *state* an origin it knows. The controlled pair above shows the model's
  problem is that **the origin it needs does not exist as a legal value**: for
  `interacted_with_by_end_user_or_developer/1`, all three of F's `Literal["ontology",
  "requires", "inputs"]` options are wrong by the prompt's own definitions. A required
  enum with no correct member forces a false declaration — the coordinating instance's
  reading (*F converts hard failures into plausible fabrications*) is **confirmed**, and
  the mechanism is now named: it is not that the model is lazy about origin, it is that
  the enum is not total over the predicates the corpus needs.
* **Fix A explicitly refuses to touch this class** and is right to
  (`test_undeclared_body_name_is_never_autofixed`). Preserve that refusal.
* Nothing else on record addresses it. The bucket question — *what list holds a
  descriptive property of a defined term* — has **no candidate design at all**. That is
  phase B's largest greenfield item.

---

## Graph-stage or translation-stage?

**Both, and the split is clean — which is why treating it as one problem has been
expensive.**

* **Graph-stage-preventable (the routing half).** The graph already knows enough to
  classify each node's span: it holds `establishes`, `spans[].quote`, `provides` and
  `needs`, and it *already* assigns a `kind` (this run's corpus marks `l1_170_n065`
  "Assistant: the entity…" as `definitional` and `l1_170_n015` "The rest of the document
  consists of…" as `conditional` — the latter is plainly wrong and no model call is
  needed to see it). A graph-stage speech-act decision (normative / definitional /
  meta-about-document / applicability / example) would let the pipeline stop sending
  meta-about-document spans to a translator whose only output shape is a rule. **The
  cheapest evidence that this is the right stage: all 12 abstentions in this run are
  non-normative spans, they cost one call each, and the pipeline already treats abstention
  as a legitimate outcome.** The graph could have made that decision once, for free,
  instead of buying it 19 times at five calls each.
* **Not graph-stage (the bucket half).** Four of the 19 unrepaired are *genuinely
  normative* — `l171_426_n005` ("The assistant must strive to follow all applicable
  instructions"), `l1_170_n047` ("When two root-level principles conflict, the model
  should default to inaction"), `l1_170_n052` ("Models should obey developer instructions
  unless overridden"), `l1_170_n056`. `n052` is a pure M1 loss on a pure obligation: its
  five identical attempts all fail on `body references \`developer_instruction\``. No
  span classification saves it. The missing bucket is a **schema/adapter-stage** defect
  and would survive perfect graph-stage routing.

---

## Open question for the fix pass

The graph's `needs` entries already carry a `prose` field, and the adapter already prints
it. Nothing in the pipeline distinguishes *"a predicate that describes a defined term"*
from *"a predicate that describes the case"* — but the module's own `concepts` list holds
exactly the former and is forbidden from counting as a declaration. **Is the checker's
rule (`a concepts entry alone does NOT declare it`) load-bearing, or is it defending
against a typo risk that a fourth list — or a per-entry `declares: bool` on `concepts` —
would defend against more cheaply?** Answering that requires knowing what
`schema.py:865`'s declaration set is protecting; do not touch it before that is written
down, since `TRANSLATION_CENSUS_REVIEW.md` D-3 flags the same line as the one Fix D would
silently break.
