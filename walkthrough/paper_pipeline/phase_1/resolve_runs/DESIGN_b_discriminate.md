# Design (b) — ground blind, then discriminate with context

**Status: DESIGN, not built, not run. Nothing below is a measurement except where marked `[RAN]`.**

The question this answers is Matt's: *can we avoid excluding the context needed to tell apart
several concepts established in the same text?* Design (b) says yes, by **fixing the extension
before the context is shown**.

---

## The problem it solves, in one line

Clause-blind grounding is stable (`[RAN]` **97%** of 378 pairs get the same overlap verdict across
three runs) but it cannot tell that two conditions in one sentence are two conditions — it sometimes
hands both names the same span. Showing the model the clause fixes that, and **also reintroduces the
confound**: with the clause visible, provenance becomes the cheapest way to answer, and every
high-similarity pair ends up sharing a borrowing clause (`[RAN]` 100% under the old design, against
an 11–12% chance rate).

⭐ **The escape is ordering plus a contract.** Stage 1 fixes the spans with no clause in the room.
Stage 2 sees the clause but **may only narrow what stage 1 already chose**. Context can then
discriminate, and cannot manufacture.

---

## Stage 1 — GROUND (blind) · already built and run

`blind_score.py`, `blind_run1..3.json`. Whole document, 43 names in shuffled order, no clause id, no
section of origin, no grouping. `[RAN]` grounded 38 / 35 / 38 of 43.

**Unchanged by this design.** Stage 2 consumes its output and never re-runs it.

## Stage 2 — DISCRIMINATE (with context) · this is the new part

**Input, per borrowing clause:** the clause text, the names that clause borrows, and **the stage-1
span already assigned to each**.

**The only question asked:** *given what this clause needs each of these names to mean, must any of
these spans be narrowed so that they stop overlapping — and does any span fail to fit its role?*

### ⛔ The narrow-only contract — this is the whole design

Per name, stage 2 may emit exactly one of:

| verdict | meaning | mechanical check |
|---|---|---|
| `keep` | span unchanged | — |
| `narrow` | a new span | ⛔ **MUST be a contiguous substring of the stage-1 span** |
| `flag` | the span does not fit the role; no change | must carry a reason |

It may **NOT** widen, replace, add a span, or ground a name stage 1 left ungrounded. Every one of
those requires *retrieval*, and retrieval with the clause visible is exactly the confound.

⚠️ **The substring check is load-bearing, not hygiene.** It is what makes *"context cannot
manufacture the extension"* a fact rather than a hope. **Without it, design (b) is the confounded
design with extra steps.**

---

## Worked example that PASSES — `m0150`, from `blind_run2` `[RAN]`

The clause borrows `reputable_tool/1`, `unnecessary_request/1`, `unreliable_destination/1`. The
document sentence:

> Even calls through reputable tools can be risky if the destination seems unreliable or requests
> information that is unnecessary for the user's task.

**Stage 1 (blind) got it wrong in a specific, visible way** — `[RAN]` `reputable_tool` /
`unreliable_destination` at **1.00**, `unnecessary_request` / `unreliable_destination` at **0.50**.
Three different conditions, one span.

**Stage 2 should narrow to:**

| name | narrowed span | substring of stage 1? |
|---|---|---|
| `reputable_tool/1` | *calls through reputable tools* | ✅ |
| `unreliable_destination/1` | *the destination seems unreliable* | ✅ |
| `unnecessary_request/1` | *requests information that is unnecessary for the user's task* | ✅ |

All three disjoint. Pair similarity 1.00 and 0.50 → **0.00**.

⭐ **AND THIS KEY IS NOT MINE.** `[RAN]` blind runs **1 and 3 independently produced the separated
form** — `unnecessary_request` / `unreliable_destination` do not appear in their overlap work lists
at all. The right answer is attested by two runs that never saw the clause, so scoring stage 2
against it is not scoring it against my opinion.

## Worked example that FAILS — and what catches it

**The failure this design exists to prevent.** Stage 2, now holding `m0150`, decides
`reputable_tool` is better grounded in `control_side_effects`'s general tool-safety paragraph and
emits that span instead. **It reads better than the original.** It is also the confound returning: a
span chosen for the clause's provenance rather than the name's meaning.

⇒ **Caught mechanically and before any scoring:** the emitted span is not a substring of the stage-1
span, so it is rejected and the run is flagged. No judgment required.

### ⚠️ The failure the check does NOT catch, stated rather than hidden

Stage 2 narrows to sub-spans that are disjoint and **wrong** — e.g. handing `unnecessary_request` the
words *"Even calls through reputable tools"*. Substring: ✅. Disjoint: ✅. Wrong: ✅.

**Nothing mechanical catches this.** It is caught only by the cross-run key above (on the pairs where
two blind runs already agree) and by reading the 7–9 pairs. ⛔ **This is why the work list must stay
small enough to read** — `[RAN]` 7–9 pairs across 7–8 clauses per run, which it is.

---

## What evidence it produces

| | measure | why it is the right one |
|---|---|---|
| 1 | **substring violations** | hard gate. Must be **0**. Non-zero is not "needs tuning", it is *the design did not hold* |
| 2 | sibling-pair similarity, before → after | the direct effect |
| 3 | ⭐ **same-clause share of high-similarity pairs, before → after** | **the confound test, and it is DIRECTIONAL** — see below |
| 4 | agreement with the cross-run key | on pairs where 2 of 3 blind runs already separated |
| 5 | stability of stage 2 across its own repeats | a discriminator that is not reproducible is not usable |

⭐ **Measure 3 is the one that decides it, because the direction is what distinguishes the two
designs.** Handing a model the clause *raised* same-clause similarity to `[RAN]` **100%** under the
old design. Under design (b) it must **fall** from the blind baseline of `[RAN]` **86% / 75% / 50%**,
because narrowing separates siblings. **If clause context raises it, design (b) has failed in exactly
the way it was built to prevent, and no other number can rescue it.**

## Pre-registered predictions

Written before the run, per `REPRODUCIBILITY.md`'s sandwich rule.

| | prediction | |
|---|---|---|
| **D1** | substring violations = **0** | ⛔ **FALSIFIER** — a violation voids the design, not the run |
| **D2** | mean sibling-pair similarity falls | |
| **D3** | same-clause share of high-similarity pairs falls below the blind baseline | ⛔ **FALSIFIER** — the confound's signature is this rising |
| **D4** | on pairs where 2 of 3 blind runs already separated, stage 2 reproduces the separation | |
| **D5** | names stage 1 left ungrounded stay ungrounded | stage 2 filling one is a contract breach, not a bonus |

## What it costs

**Free.** Subagents, not API spend. Three stage-2 runs over `[RAN]` 7–8 clauses each, consuming
`blind_run1..3.json` already on disk. No new grounding, no new document pass.

⚠️ **What it does NOT buy.** Design (b) discriminates; it does not merge. Knowing that two names are
one concept is `[RAN]` a run-store question — same clause + same slot, and borrowed-name agreement
across repeat translations is **0.00 (0 of 22)**. Design (b) is orthogonal to that and does not
address it.

⛔ **Not decided, not built.** `OPEN_QUESTIONS.md` Q-6.
