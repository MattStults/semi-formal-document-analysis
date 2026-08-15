# M2 — the borrowed name is declared in one list and glossed in another

**Mechanism, one sentence.** A predicate the module uses but does not define must be
named in `requires`/`inputs` *and* separately glossed in `concepts`; the two obligations
live in two lists, and for the 70% of cases where the name was handed to the model by the
graph's NEEDS block, the adapter's own wording (*"never in `ontology`, never defined
here"*) reads as an instruction **not** to write the second entry.

**29 repair rounds, $0.0435 (18% of repair spend), 24 clauses, 1 module lost.**

---

## How to recognise it

* Finding is `borrowed-no-gloss`. The named predicate is listed correctly in `requires`
  or `inputs`; the module simply has no `concepts` entry for it.
* Two triggers, and they matter separately:

  | trigger | findings | share |
  |---|---|---|
  | the name came from the node's own **graph NEEDS/PROVIDES block** | 35 | **70%** |
  | the name is one the model invented for itself | 15 | 30% |

  The graph-supplied set is a small, repeating vocabulary:
  `authority_levels_hierarchy/2` (9 findings), `user_authority/1` (5),
  `message_role_definition/1|2` (9), `chain_of_command_principle/1|2` (3),
  `conversation_definition/1` (2), `developer_definition/1` (2), `root_authority`,
  `tool_definition`, `assistant_definition`, `guideline_authority`.

---

## The exact finding text

```
<root>: `user_authority/1` is borrowed but has no gloss. Add a `concepts` entry saying
what this module needs it to MEAN — not what defines it, which stays in
`requires`/`inputs`. Without it a seat is shown a bare predicate name, and nothing can
match this to the clause that defines it
```

## The instruction that produces it

The adapter (`node_corpus.py`) writes this into every graph-node user block, verbatim:

> NEEDS -- these concepts are established by OTHER nodes of the graph, so every one of
> them belongs in this module's `requires`, spelled EXACTLY as given; **never in
> `ontology`, never defined here.** `inputs` is only for plain facts about the situation
> being judged (messages, roles, case data) that YOU identify -- a name can never appear
> in both requires and inputs:
>   - authority_levels_hierarchy: The ranking of instruction authority levels: root >
>     system > developer > user > guideline > no authority, used to determine which
>     instruction prevails in conflicts.

The paragraph hands the model **the exact gloss the checker is about to demand** and then
tells it the name is *not defined here*. The census diagnosed this class as a forgotten
join (`TRANSLATION_REPAIR_CENSUS.md` §5.4: *"the model writes `inputs` at the end, having
already written `concepts`, and the second obligation is invisible from where it is
standing"*). On graph-node prompts that diagnosis is incomplete: for 70% of instances the
prompt does not merely fail to remind — it supplies a plausible reason not to.

---

## Verbatim document excerpts, and the one lost module

**`l1_170_n056` — 5 attempts, no module, the same two findings on every round.**
Verbatim (L93):

> `Models should honor user requests unless they conflict with developer-, system-, or
> root-level instructions.`

Findings, rounds 1-5 identical:

```
<root>: `user_authority/1` is borrowed but has no gloss. …
<root>: `authority_levels_hierarchy/2` is borrowed but has no gloss. …
```

Both names were **given** to the module by its NEEDS block, with prose. This is a
genuinely normative clause — a chain-of-command rule — lost to a bookkeeping obligation
the prompt half-forbade.

**`l1_170_n049` — 2 attempts, recovered.** Verbatim (L79):

> `System: Rules set by OpenAI that can be transmitted or overridden through system
> messages, but cannot be overridden by developers or users.`

Round 1: `set_by_openai/1`, `transmittable_via_system_message/1`,
`overridable_by_developer_or_user/1` all borrowed without gloss — here the *invented*
trigger, not the graph one.

**`l1_170_n091` — 3 attempts.** Verbatim (L167):

> `The spec treats user and developer messages interchangeably, except that when both are
> present in a conversation, the developer messages have greater authority.`

Round 2 findings include `user_definition/1`, `developer_definition/1`,
`authority_levels_hierarchy/2` — all three straight out of its NEEDS block.

---

## Recovery — what changed when it did

23 of the 24 clauses recovered, almost always in one round: the model adds a `concepts`
entry whose gloss is a **paraphrase of the NEEDS prose it was already shown**. This is
the cheapest class to repair and the one where the repair adds the least information —
the content already existed in the prompt.

The one non-recovery, `l1_170_n056`, is also the class's only frozen chain: five
byte-identical modules (see `class_repair-fixed-point.md`). On the 08-15 retry under a
byte-identical prompt it **failed again, 5 attempts, unrepaired** — one of only four of
the 19 losses that reproduced (`n056`, `n058`, `n078`, `n084`). That makes `n056` the
strongest single artifact for this class: it is not sampling noise.

---

## The paid cost of the class

| | |
|---|---|
| repair rounds in which it appears | **29 of 130 (22%)** |
| findings | 50 |
| clauses touched | 24 |
| **attributed spend** | **$0.0435** (18% of repair spend) |
| **modules lost** | **1** (`l1_170_n056`) |

Ranked #2 by cost, #6 by modules lost. The gap between those two ranks is the point of
this file: it is expensive and almost never fatal, which is the opposite profile to M1.

---

## FALSIFIER

*The adapter's "never defined here" wording is a contributing cause.* Wrong if: re-running
the 35 graph-supplied instances with the NEEDS block reworded (or with the prose
pre-emitted as a `concepts` stub) leaves the `borrowed-no-gloss` rate unchanged. A
cleaner falsifier is available for free: **the 30% invented-name instances share no such
wording**, and if their per-clause rate matches the graph-supplied rate once normalised
by how many borrowed names each module has, the wording contributes nothing and the
census's plain forgotten-join diagnosis stands. That normalisation is not done in this
pass and should be the first measurement of the fix pass.

---

## Candidate solutions already on record

* **Fix C — `requires`/`inputs` entries carry name+arity+gloss as a `Borrowed` object.**
  Reviewed **SAFE TO LAND**, lowest blast radius of the three grammar fixes, *"the one I
  would land first"* (`TRANSLATION_CENSUS_REVIEW.md` §5). Two caveats the review attached
  and this run supports:
  * `requires-inputs-overlap` **must be removed from its credited classes** — carrying a
    gloss does not stop a name appearing in both lists. (In this run that class did not
    fire at all, so the correction costs C nothing here.)
  * *"the model can satisfy it with a junk gloss. This suppresses the check rather than
    removing the defect."* On this run that risk is visible in a neighbouring class:
    `gloss-restates-name` (M3) fired 12 times and killed 2 modules. Making the gloss
    required without making it informative moves M2 into M3.
* **Verdict on the defect: fatal to neither.** C's review findings are corrections to
  credit and framing, not to the mechanism. C is the one candidate on record that this
  run's evidence leaves intact.
* Not addressed by any candidate: that the **graph already holds the gloss**. Fix C makes
  the field required; it does not observe that `needs[].prose` could fill it.

---

## Graph-stage or translation-stage?

**Graph-stage-preventable, and unusually cheaply.** The information the checker demands
already exists at graph stage: every `needs` entry in `root_graph.production.json` is
`{"name": …, "prose": …}`, and `prose` is exactly a gloss. Nothing in the pipeline carries
it into the module; the adapter prints it as prose for the model to re-type. A graph-stage
decision — emit the borrowed name *with its prose already attached*, in whatever shape the
schema ends up wanting — removes the join without asking the model for anything.

The 30% invented-name half is genuinely translation-stage: the graph has never heard of
`set_by_openai/1`, and only the model knows what it needs it to mean.

One graph-stage defect this class exposes in passing: **the graph names concepts without
arity.** `message_role_definition` is borrowed at `/1` by `n071`, `n072`, `n073`, `n074`
and at `/2` by `n069`; `chain_of_command_principle` at `/1` and `/2`. Every module is
individually consistent and they cannot link. See `class_link-identity-drift.md`.

---

## Open question for the fix pass

If `needs[].prose` is emitted as a pre-filled gloss, the model is being handed a meaning
it did not commit to — and the whole reason the gloss exists (`schema.py`: *"you are
recording your assumption, so that a disagreement with the clause that does define it can
be found"*) is that the module's assumption must be **its own**, so a mismatch with the
defining clause is detectable. A pre-filled gloss makes every module agree by
construction and silently deletes that detector. **Is the disagreement-detection property
actually used downstream, and by what?** If nothing consumes it, pre-filling is free; if
something does, this class needs a different lever entirely.
