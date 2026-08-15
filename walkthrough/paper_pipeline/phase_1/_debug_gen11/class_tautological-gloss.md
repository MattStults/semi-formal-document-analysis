# M3 — the tautological predicate: the gloss can only restate the name

**Mechanism, one sentence.** When the model names a predicate after the exact phrase the
span uses, the span contains no further information to gloss it with, so every gloss it
can honestly write is a restatement of the name — and the checker rejects restatements.

**11 repair rounds, $0.0159 (7% of repair spend), 5 clauses, 2 modules lost.**

---

## How to recognise it

* Finding is `gloss-restates-name`, quoting the offending gloss.
* The predicate name is a transliteration of a noun phrase in the span, and the span says
  nothing else about it.
* The chain is characteristically **short-then-stuck**: the model fixes everything else
  and then spends its remaining attempts on this one finding, unchanged.

## The exact finding text

```
<root>: the gloss for `user_of_product/2` restates its own name ('U is a user of product
  P'). A gloss has to say something the name does not, or it carries no information for a
  reader or a matcher

<root>: the gloss for `system_developer_user_instruction/1` restates its own name
  ('instruction I is a system, developer, or user instruction'). A gloss has to say
  something the name does not…

<root>: the gloss for `persecution/1` restates its own name ('H is persecution'). …
```

---

## The two lost modules

**`l1_170_n028` — 5 attempts, this finding on every one, module lost.** Verbatim (L43):

> `Users can always access a transparent experience via our direct-to-consumer products.`

The predicate is `user_of_product(U, P)`. The clause tells you that users can access a
transparent experience via OpenAI's D2C products. It does **not** tell you what makes
someone a user of a product. There is no non-tautological gloss available from this text.
Five attempts, byte-identical modules, no module.

**`l171_426_n005` — 5 attempts, module lost.** Verbatim (L181):

> `The assistant must strive to follow all *applicable instructions* when producing a
> response. This includes all system, developer and user instructions except for those
> that conflict with a higher-authority instruction or a later instruction at the same
> authority.`

The predicate is `system_developer_user_instruction/1`, glossed *"instruction I is a
system, developer, or user instruction"*. The clause's list — "system, developer and user
instructions" — is precisely and only what the name says. Rounds 3, 4 and 5 report this
single finding and nothing else: **the module was otherwise correct and was lost to one
gloss.** This is a genuinely normative clause and the run's most exasperating loss.

**`l1_170_n019` — 3 attempts, recovered.** Verbatim (L32):

> `Our models should never be used to facilitate critical and high severity harms, such as
> acts of violence …, creation of cyber, biological or nuclear weapons …, terrorism,
> child abuse (e.g., creation of CSAM), persecution or mass surveillance.`

Round 2 draws `gloss-restates-name` on `persecution/1` and `mass_surveillance/1`. The
document gives parenthetical examples for *violence* and *weapons* and *child abuse* but
**none for persecution or mass surveillance** — and those are exactly the two that drew
the finding. The class is a direct function of how much the document elaborates a term.

---

## Recovery — what changed when it did

Three of five recovered, always by importing world knowledge the span does not contain:
`l1_170_n019` attempt 3 glosses `persecution/1` as systematic mistreatment of a group;
`l1_170_n050` and `l1_170_n067` similarly. **That is the uncomfortable part of this
class: the check is satisfied by the model adding information the document does not
license**, and `schema.py` calls an unnamed inference *"an unmarked invention"* (see
`class_honest-invention-penalised.md`, where the model marks it and is penalised anyway).
The two clauses that refused to invent are the two that were lost.

On the 08-15 retry both losses translated — `l1_170_n028` on attempt 1,
`l171_426_n005` on attempt 4.

---

## The paid cost of the class

| | |
|---|---|
| repair rounds in which it appears | **11 of 130 (8%)** |
| findings | 12 |
| clauses touched | 5 |
| **attributed spend** | **$0.0159** (7%) |
| **modules lost** | **2 of 19** |

Cost rank #5, modules-lost rank **#3**. The gap is the sharpest in the run: 5 clauses,
2 losses — a 40% kill rate, the highest of any class (M1's is 12/30 = 40% too, but on six
times the volume; M2's is 1/24 = 4%).

---

## FALSIFIER

*The gloss is impossible because the span is exhausted by the name.* Wrong if a competent
reader can write a non-tautological, document-grounded gloss for `user_of_product/2` from
`l1_170_n028`'s span alone. **This is a cheap human test and it should be run before any
fix**: if a reader can do it, the class is a model-capability problem and belongs with
prose/worked-example levers, not with the check.

A second falsifier: if the recoveries' glosses turn out to be **document-grounded** rather
than imported world knowledge, then the check is doing its job and the two losses are
outliers. Read the three recovered glosses against their spans and say which.

---

## Candidate solutions already on record

* **No candidate on record targets this class.** `gloss-restates-name` does not appear in
  `translation_repair_census.py:TAXONOMY` at all — it would classify as `OTHER:schema-breach`
  — so it is absent from the census, from `TRANSLATION_FIX_PLAN.md` and from the review.
  It is one of four classes this run surfaces that the earlier work never saw
  (`PRIOR_WORK_MAP.md`).
* **Fix C interacts with it and makes it worse.** C makes a gloss a *required* field of
  every `requires`/`inputs` entry. The review already anticipated the shape of the problem
  — *"the model can satisfy it with a junk gloss. This suppresses the check rather than
  removing the defect"* — but this run shows the other direction: when the model does not
  write a junk gloss, `gloss-restates-name` fires and can kill the module. **C should be
  re-costed with M3 in the picture**: it converts M2 rounds (cheap, 4% kill rate) into
  either junk glosses or M3 rounds (7% of spend, 40% kill rate). That is a re-ranking the
  review could not have made and phase B must.

---

## Graph-stage or translation-stage?

**Genuinely translation-stage, and arguably check-stage rather than either.**

The graph cannot prevent this. It could avoid *handing over* a name that is a bare
transliteration — but in all five instances the offending predicate was **invented by the
model**, not supplied by the graph (`user_of_product`, `system_developer_user_instruction`,
`persecution`, `mass_surveillance`, `openai_supplied_instruction`, `list_of_messages`). A
span-type decision does not help either: `l171_426_n005` and `l1_170_n019` are ordinary
obligations.

The live question is whether the **check** is well-posed. Its stated ground is that a
restating gloss *"carries no information for a reader or a matcher"*. That is true, and it
is also true that for a span whose entire content is the term, no other gloss is
available without inventing. The check as written has no escape hatch for that case, and
the two clauses that declined to invent are the two that died.

---

## Open question for the fix pass

`schema.py` offers a licence vocabulary precisely for information that is not read off
the text (`textual` / `assumed` + named inference / `world`). **Is a gloss that restates
its name acceptable when the concept is `licence: textual` and the span genuinely
contains nothing more — i.e. should the check be conditional on licence?** Deciding that
requires knowing what consumes glosses downstream (the seat brief, the matcher, or both),
and that consumer list is not written down anywhere this analysis could find.
