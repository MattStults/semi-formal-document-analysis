# SWEEP — slice 5, cross-clause, end of run

## What this file is, and why it exists

Gap 2 of the brief, measured on the previous cohort:

> **Classes found late never reach clauses done early.** The previous loop NAMED a
> licence-inheritance class, called it "mechanically checkable; nothing checks it", and left
> it in 12 of 17 clauses because the loop was per-clause with no end-of-run sweep.

So this slice ran the sweep. Every class any of the five clauses raised was folded into
`sweep_check.py` and re-run **across all five modules**, including the ones finished before
the class existed. The delta between what the per-clause pass caught and what the sweep
caught is the primary result, and it is in §3.

`sweep_check.py` is deliberately plain Python over the JSON modules and the span files —
no model call, no cost, re-runnable. Every check in it is a few lines. **That is the point:
every high-value class this campaign has found was checkable in a few lines that nobody had
written.**

Run it with:

```
semi-formal-experiment/.venv/bin/python _debug_gen11/opus_pairs/slice5/sweep_check.py
```

⚠️ **A check that fires is not automatically a defect.** Several classes on this corpus are
CONTRACTS (`REVIEW_LIST.md` ANTI-RULES). The output is a work list; the adjudication of every
firing is below.

---

## 1. The census

All five modules validate clean at the floor: **0 schema breaches, `repair_needed: False`,
zero error-severity findings**, re-derived by the coordinator with `schema.validate_all` +
`checks.run_checks` rather than taken from any agent's word. Every `note/link` finding is one
of the three classes the ANTI-RULES name as expected on a correct single-clause module
(`requires-unprovided`, `concept-declared`, `situation-input`); none was "fixed".

| clause | outcome | asserts | claims | ontology | concepts |
|---|---|---|---|---|---|
| `l1001_1107_n006` | translated | 2 | 4 | 3 | 8 |
| `l1001_1107_n011` | translated | 3 | 4 | 3 | 13 |
| `l1108_1367_n003` | translated | 3 | 4 | 1 | 7 |
| `l1108_1367_n008` | translated | 2 | 4 | 3 | 12 |
| `l1108_1367_n013` | translated | 0 | 2 | 2 | 5 |

**Zero abstentions across five clauses, two of which fire a literal `00_task.md` abstention
trigger.** That is a finding, not a pass — see `PROMPT_FINDINGS.md` PF-1.

### Asserts accounting (gap 3)

**No module lost an assert at any point.** Every drafter recorded `len(asserts)` at six
checkpoints (span-first draft, then each of five review turns) and the count was flat in every
case: 2/2/2/2/2/2, 3×6, 3×6, 2×6, 0×6. No reduction anywhere, so no reduction justification
was owed anywhere.

⭐ **The near-miss worth recording.** The `l1001_1107_n006` critic found that assert 2 is
*logically subsumed* by assert 1 (its body is assert 1's body plus one literal) and argued its
content's real destination is `forbid_body` — which the module already uses. It then **declined
to propose the deletion**, on the anti-over-edit rule. That is the gap-3 discipline working in
the direction it was built for: a critic with a plausible reason to delete an assert, holding.
The deletion would have taken the module from 2 to 1 with a read-back still reciting both.

---

## 2. What the per-clause pass caught on its own

For completeness, so the sweep's delta is not overstated. Working per clause, the five
drafters and four critics between them:

* answered the abstention question **explicitly, in words, all four triggers by name, on all
  five clauses** (gap 1 — see §4);
* kept the asserts count flat and reported it per turn (gap 3);
* found the truncated narrowing on `l1108_1367_n008` and encoded **nothing** from
  `ESTABLISHES`'s silent completion of it;
* found the BAD-arm trap on `l1001_1107_n011` (*"even if they're public figures"* sits inside
  the arm the document marks BAD; encoding it as `forbid_body {permit, public_figure}` would
  have written the rejected reasoning in as policy) and avoided it;
* kept the excluded *"However, it may provide critical, discouraging, or factual
  discussions…"* sentence entirely out of `l1108_1367_n003` — I verified this myself by
  grepping the module for that sentence's whole vocabulary: **zero hits**;
* applied `l171_426_n022` L6 correctly on `l1108_1367_n003`'s three-way `or` under a negative
  scope verb — three separate `forbid` asserts, not one conjunctive body.

That is a strong per-clause pass. The point of §3 is that it is still structurally blind to
one whole class of thing.

---

## 3. ⭐ WHAT ONLY THE SWEEP CAUGHT — the delta

### 3a. THE HEADLINE: an arity mismatch that makes a consumer's rule dead

The deterministic selection (`SELECTION.md` — nothing was hand-picked) happened to put **two
provider/consumer pairs inside one slice**:

```
l1108_1367_n013  PROVIDES user_authority          ->  l1108_1367_n008  NEEDS it
l1001_1107_n006  PROVIDES privacy_protection_rule ->  l1001_1107_n011  NEEDS it
```

Neither drafter could see its counterpart. Both flagged the risk in their own words and said
they could not resolve it:

> `l1108_1367_n013`: *"U2, the most likely undetected error: the arity of `user_authority`. …
> If a consumer node declares `user_authority/0` or `/2` in its `requires`, my module silently
> does not link. **I cannot see those nodes and did not look.**"*

> `l1001_1107_n006`: *"`root_authority/1` has two incompatible argument readings in the link
> set, and I could not resolve it without guessing another clause's content. … **This needs a
> coordinator decision; it will not resolve itself.**"*

The sweep resolves both, in four lines of Python, and — this is what makes it evidence rather
than noise — **it returns a different answer on each of the two structurally identical pairs**:

| link | provider | consumer | verdict |
|---|---|---|---|
| `user_authority` | `l1108_1367_n013`, **arity 1** over a rule | `l1108_1367_n008`, **arity 1** over a rule | ✅ **CONVERGES** |
| `privacy_protection_rule` | `l1001_1107_n006`, **arity 0** ground atom | `l1001_1107_n011`, **arity 1** | ⛔ **MISMATCH** |

**The mismatch is a real defect and it is silent.** `l1001_1107_n011` carries
`privacy_protection_rule/1` in `requires`; `l1001_1107_n006` delivers
`privacy_protection_rule` as a nullary ground atom. Nothing unifies. It is failure mode #3
("rules that can never fire") arriving through failure mode #9 ("same name, different
meanings; they link cleanly and are wrong"), and **both modules pass every deterministic check
we have, individually, with zero findings.**

Both choices are defensible in isolation, which is exactly why neither drafter caught it:
* `l1001_1107_n006` followed review-list **N1**, which reserves ground atoms for facts about
  the DOCUMENT — and a named rule of the document is precisely that;
* `l1001_1107_n011` read its NEEDS gloss (*"the rule that the assistant must not respond to…"*)
  as a predicate over a rule and gave it a variable.

⛔ **I have NOT edited either module.** The disagreement is the datum. Deciding it needs a
corpus-wide convention (are named document rules nullary constants or unary predicates?) and
that is an owner ruling, not a coordinator patch — patching one side here would hide the class
and leave the other 700-odd nodes to re-run into it.

**Note what the convergent case buys us.** `user_authority` matching is not a null result — it
is the control. The check discriminates rather than flagging everything, and the n013 critic
independently re-derived the same convergence by reading the NEEDS gloss, `authority_convention.md`
and the worked example's `guideline_authority/1`. **A mechanical check and a semantic reading,
run independently, agreeing.** That is the strongest form this evidence takes.

### 3b. THE LICENCE-INHERITANCE CLASS — reproduced at 4 of 4, up from 12 of 17

This is the class the brief names: *"NAMED a licence-inheritance class, called it 'mechanically
checkable; nothing checks it', and left it in 12 of 17 clauses."*

It now has a checker, and it fires on **every module in this slice that borrows a name — 6
firings across 4 of the 5 modules; the fifth borrows nothing at issue.**

| clause | borrowed name | licence | cites |
|---|---|---|---|
| `l1001_1107_n006` | `root_authority` | `textual` | itself |
| `l1001_1107_n011` | `root_authority` | `textual` | itself |
| `l1001_1107_n011` | `privacy_protection_rule` | `textual` | itself |
| `l1108_1367_n003` | `root_authority` | `textual` | itself |
| `l1108_1367_n008` | `user_authority` | `textual` | itself |
| `l1108_1367_n008` | `restricted_content_rule` | `textual` | itself |

Each is a `concepts` entry for a name **another node owns**, marked `textual` and citing *this*
node — asserting that this node's text says what the gloss says, when the gloss came from the
NEEDS block. `00_task.md` defines `textual` as *"the cited clause says this"* and warns that a
manufactured citation *"creates an invented entity behind a passed check"*.

⭐ **VERDICT: this is a PROMPT defect, not a translator defect, and it is filed as PF-2.** The
production worked example does exactly this twice, and `10_output_format.md` line 66 forces the
entry to exist. Two critics reached this independently and both routed it to prompt findings
rather than scoring the module clean — which is gap 4 working as designed.

⭐ **The one module that broke the pattern proves it is learnable:** `l1108_1367_n013` marked
its borrowed `authority_levels_hierarchy` gloss **`assumed`** with an inference naming where the
content actually comes from. Its critic's verdict: *"the module is more correct than the
instructions it was given."* One module out of five escaped a prompt-taught defect, on its own.

### 3c. Two classes folded back that the per-clause pass could not have applied

Both were discovered on one clause **after** others were finished. Under the per-clause loop
they would have died in one `lessons.md`. Re-run across all five:

* **BAD-arm sourcing** (from `l1001_1107_n011` L1) — flags any coined name whose content words
  occur inside a `<!-- BAD -->` arm and *nowhere else* in the span. N10 would **pass** such a
  name, because the substring is genuinely there. Re-run across the slice: one span has BAD
  arms, and it is clean.
* **Truncated narrowing** (from `l1108_1367_n008` C1) — flags a narrowing ending on a dangling
  function word or an unbalanced `(`. Re-run across the slice: fires on `l1108_1367_n008` only,
  correctly, and the module encodes nothing from the completion. **N3 asks for the
  ESTABLISHES/span diff but assumes both are well-formed sentences; P6 assumes the narrowing is
  a complete proposition. Neither would have caught this.** This is a property of the
  document's markdown (a bare `[?](#anchor)` link), so it recurs corpus-wide, not just here.

### 3d. A defect the sweep found in ITSELF

Worth recording because it is the same failure shape one level up. My first `P9
coined-and-unused` check exempted `NEEDS` names — the correction the review list already
carries — and **still fired on a correct module**, because a `PROVIDES` name is also delivered
as an unused `ontology` atom by contract. `l1001_1107_n006`'s lessons (C1) named the hole; I
fixed the checker. P9 has now been corrected **twice**, both times because it fired on
correct work. An entry that fires on correct work is how a previous seat reached 48/86 on
known-good modules.

---

## 4. Gap 1 — the frame audit, measured

**5 of 5 clauses have the abstention question answered explicitly, in words, with all four
`00_task.md` triggers checked by name.** Two of the five fire a literal trigger:

| clause | trigger fired | outcome | answered in writing |
|---|---|---|---|
| `l1001_1107_n011` | *"it is an example"* — span headed `**Example**`, node kind `meta` | translated | ✅ drafter and critic, at length |
| `l1108_1367_n013` | *"it is a section heading"* — span is a bare `####` line | translated | ✅ drafter and critic, at length |

Compare the previous cohort: an `**Example**`-headed span translated with **zero occurrences
of "abstain" in its entire transcript**.

⭐ **But the honest reading of this is not "the critics improved."** Forcing the question
revealed *why* it was never asked: **two production prompt files give contradictory abstention
tests, and the later, more specific one tells the translator that being an example or a heading
is not grounds to abstain.** Four separate agents found this independently, and I verified every
line reference myself. Full write-up in `PROMPT_FINDINGS.md` PF-1. The measured silence on the
previous cohort was the prompt's expected output, not a lazy reader.

The mechanical check now exists (`c_abstention_frame`): detect a trigger in the span, then
assert the notes contain the word. It is a presence check, not a verdict — but a silent answer
can no longer pass.

---

## 5. Firings adjudicated as NOT defects

* **`N10 coined-symbol anchoring`, 2 hits on `l1001_1107_n011`** (`asks_for`,
  `permissible_alternative_offer`). Both are structural relation names in a dialogue span whose
  content is carried by the turns, not by a quotable noun phrase. The lexical proxy is weak by
  construction. Not defects; recorded so the check's false-positive rate is visible.
* **`P10 GOOD/BAD poles`, 1 hit.** Reports the `(status, act)` pairs on the GOOD/BAD span. The
  three pairs are distinct — no duplicated pole, which is the failure P10 exists to catch.
* **`gloss restates name`, `P8 tautology`, `N5 negation-as-failure`, `P3 claims-unencoded`,
  `closure completeness`, `undeclared body names`, `read_back slot arithmetic`, `P1 polarity`,
  `NEEDS contract`, `PROVIDES delivered`: 0 hits each.** Notably `N5` at zero across five
  clauses including `l1108_1367_n008`, whose span is a `should not … unless` — the exact
  provocation for negation-as-failure. That module decomposed the defeater into two positive
  grounds instead and contains no `not` anywhere.

---

## 6. Unsettled, and left unsettled deliberately

1. **`privacy_protection_rule` arity.** §3a. Needs a corpus-wide convention; not patched.
2. **`root_authority` argument TYPE.** `l1001_1107_n006` reports that the sibling node
   `l1001_1107_n005` (outside this slice) emits `root_authority(protect_privacy)` — argument a
   **section** — while every consumer in this slice glosses it as taking a **rule**. This is
   `user_authority`'s question one arity down, and N8 does not reach it because N8 is scoped to
   arity ≥ 2. I could not test it: the provider is outside my slice and I did not edit anyone's
   gloss to match. **The worked example is evidence for the "rule" reading** —
   `guideline_authority(R) :- rule_under_heading(R, heading_const)` ranges over a rule — but
   that is my inference, not a ruling.
3. **`l1108_1367_n008` UNSURE-1**, whether `gratuitous` and `toward individuals` distribute over
   all three of *abuse, harassment, negativity* or bind one item each. The drafter took the
   distributive reading and flagged that it moves in the narrowing direction. Unresolved from
   the span alone.
4. **`l1001_1107_n011`'s `oblige`.** The span contains no deontic modal anywhere; the force is
   read off a `<!-- GOOD -->` / `<!-- BAD -->` marking. Drafter and critic both kept `oblige`
   and both named it as the call they would most want a second reader on.
5. **The hedge tier is unrecoverable at this schema.** `should not` compiles byte-identically to
   `must not`. `l1108_1367_n008` recorded it in four places because the schema offers no fifth.
   The sweep now checks that a hedged span carries its modal into at least one `read_back` and
   into the notes — it passes — but that is prose, not encoding.

---

## 7. The trap entry named in the brief

The brief warns that **entry `E6`** *"has now produced the identical harmful weakening under two
different critics on `l171_426_n022`"*.

⛔ **`E6` does not exist in `REVIEW_LIST.md` v2.** That file's entries are `P1`–`P10`, `N1`–`N10`
and three anti-rules. The only `E6` strings anywhere in the tree are element rows inside
per-clause `span_enumeration.md` tables, and `l171_426_n022`'s own enumeration has no `E6` row.
I could not instrument the entry by name and I am not going to pretend otherwise.

**What I did instead**, since the harm shape is what matters: treated any critic-driven change
that WEAKENS a rule as an E6-shaped firing — a reduction in `asserts`, or a new guard added to a
prohibition. **No such change occurred on any of the five clauses.** Total edits proposed by the
four returned critics: zero conclusion-changing, a handful of optional gloss nits. The one
critic with a plausible case for deleting an assert declined it (§1).

So: not reproduced here, but **not tested either** — this slice never reached the condition. If
the parent has the list version where `E6` lives, that check still needs running.
