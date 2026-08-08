# Result — deleting the licence-emphasis line

Run 2026-08-07. 36 live calls, **$0.0482**. Prediction was frozen in `06d9d73` before any
call was made; this file was written after. Raw numbers in `RESULT_licence_emphasis.json`.

---

## ⛔ The licence question is NOT ANSWERED, and the line stays for now

`licence_modules_scored` came back at **1.33 of 6 clauses per repeat** (arm A `[2,1,1]`,
arm B `[1,1,2]`). Every licence rate in this report is therefore computed over **one or two
modules**.

The pre-registration named this in advance:

> If `licence_modules_scored` comes back low, **the honest reading is "not measured", not
> "no difference"**.

⇒ It came back low. Every licence metric reads `within noise`, and **that is the wrong
sentence to quote from this run**. The correct sentence is that the instrument could not
see. The line is not deleted, not because the deletion was shown to be harmful, but because
nothing was shown either way.

The cause is upstream: **78% of first attempts were unbuildable** in both arms. A module
that does not validate carries no licensed items, so a licence metric measured on this
corpus is measuring whatever the ~22% that survived happened to do.

**What has to happen before this question can be asked again:** the buildable rate has to
rise. That is the same work as the finding below, so there is one thing to fix, not two.

## Every metric, both arms

| metric | A mean (sd) | B mean (sd) | B − A | noise |
|---|---|---|---|---|
| first_attempt_clean_rate | 0.167 (0.000) | 0.111 (0.096) | −0.056 | 0.096 |
| unbuildable_rate | 0.778 (0.096) | 0.778 (0.096) | +0.000 | 0.193 |
| error_findings_per_clause | 2.944 (1.398) | 3.333 (1.202) | +0.389 | 2.600 |
| ⛔ licence_modules_scored | **1.333** (0.577) | **1.333** (0.577) | +0.000 | 1.155 |
| assumed_fact_rate | 0.061 (0.105) | 0.111 (0.192) | +0.051 | 0.297 |
| world_fact_rate | 0.000 (0.000) | 0.000 (0.000) | +0.000 | 0.000 |
| licensed_items_per_clause | 1.500 (0.289) | 2.500 (1.922) | +1.000 | 2.211 |

⚠️ Arm A's `first_attempt_clean_rate` has **sd exactly 0.000** across three repeats. At
temperature 0.2 that is luck on a 1-of-6 rate, not stability, and reading it as stability
would be the first mistake this harness exists to prevent.

⭐ **`world_fact_rate` is 0.000 in both arms, across 36 attempts.** That is the fourth
independent measurement of zero `world` facts — after the 18 hand-encoded clauses in
`REVIEW_QUEUE.md` §2.1. It is now the best-supported number here, and it is evidence for
option (b) in that open question: `world` may simply have no document-side instances. **Still
your call, but the evidence has stopped being ambiguous.**

## ⭐ The finding this run actually produced: a fix that did not generalise

The `read_back` slot-mismatch cause was the single biggest cluster before today's prompt
fixes, and after them it read as **eliminated**:

| | occurrences | per first attempt |
|---|---|---|
| the 8 **diagnosed** clauses, before the fix | 6 | 0.75 |
| the 8 **diagnosed** clauses, after the fix | **0** | 0.00 |
| ⛔ the 6 **held-out** clauses, after the fix | **18** | 0.50 |

⇒ On the clauses it was diagnosed from, the fix looks total. On six clauses never used for
diagnosis it is **partial at best** — roughly a third off, not gone.

⚠️ **This is a confounded comparison and I am not going to overstate it.** Different
clauses, different difficulty; the held-out set is harder on every metric. What it does
establish is that "the cause went to zero" was a statement about the diagnosis set and not
about the prompt, and only a held-out set could have shown that. This is the fitting failure
`PROPOSAL_graveyard.md` §2 predicted, caught on the first run of the thing built to catch it.

## The dominant cause, confirmed held-out

Pooled over both arms, 36 first attempts, 6 clauses never used for diagnosis:

| | | |
|---|---|---|
| **59×** | error | `ontology atom: ‹› is not a term. It must be a functor…` — **a whole rule written into a slot that holds one term** |
| 24× | error | `ontology atom ‹› carries the variable ‹› and there are no conditions to bind it` |
| 18× | error | `read_back has # ‹› slot(s) but # slot entr(ies)` |
| 18× | note | `‹› is head-less and declared in the concept table` |
| 16× | note | `‹› is head-less and declared as a situation input` |
| 13× | note | `‹› is declared in ‹› and no module in this link scope defines it` |

⭐ **Rule-in-a-term-slot is not an artefact of the eight clauses it was found on.** It is
the dominant defect on clauses selected before any outcome was known, at 1.6 occurrences per
first attempt — more than the next two causes combined. It is the one thing to fix next, and
now it can be fixed against a held-out measurement instead of against a reading.

## What this run cost, and what it bought

$0.0482 of the $8.50 cap. It bought: one open question moved toward closure (`world` facts,
now 4 independent zeros), one prompt fix demoted from "eliminated the cause" to "reduced it
on the clauses it was tuned on", and one target with a number attached.

⚠️ It did **not** buy an answer to the question it was built for. That is the correct outcome
for a pre-registered test whose instrument turned out to be underpowered, and it is only
visible as such because the underpowering was written down first.
