# The linkage experiment — can a borrowed symbol be discharged?

**PROPOSAL. Nothing built, nothing spent.** Written to the working method: what passes, what fails,
what evidence, what it costs. Supersedes the design-(b) proposal, which is parked — discriminating
spans for predicates that never enter the signature is polish on something inert.

---

## 1 · What the goal actually needs

The tool finds **which clauses bear on a behaviour**. A behaviour touches clause A; A borrows
`disallowed/1`; clause B defines it ⇒ **B bears on the behaviour too**. That chain is the product.
Without it the tool returns isolated clauses and silently misses everything one hop away.

⇒ **The goal-critical question is not what a borrowed symbol MEANS. It is whether it can be
DISCHARGED** — satisfied by an input, or linked to a definition. Everything in
`ITERATION_LOG.md` §1–7 answered the first question and returned 0.06, then 0.00.

`[RAN]` **Today, 0 of 12 orphan predicates find a provider anywhere in the corpus.** The chain does
not form even once. That is the number this experiment exists to move.

## 2 · Why it cannot be measured today, and what that implies

`[RAN]` **13 of 593 clauses (2.2%) are translated.** The clauses that would *define* the borrowed
symbols mostly do not exist yet, so 0/12 is a **corpus-size artifact**, not evidence about linkage.

⛔ **And random sampling would be the wrong draw.** Linking is a *neighbourhood* phenomenon — a
symbol and its definition co-occur in a region of the document. A random scatter of clauses across
78 sections produces a graph with no edges by construction, and would falsely confirm that linkage
fails. **Translate whole sections, so connected subgraphs exist to be found.**

## 3 · The two changes under test

**(i) A gloss on `requires`** — Q-23. Typed explicitly as an **expectation**, not a definition:
*"I need an X that means this"*, not *"X means this"*. ⚠️ The prompt must say this in those words, or
the borrower writes a competing definition and manufactures problem #9 — the objection Q-6 raises,
which is only correct if the field is mistyped.

**(ii) An unsatisfied `requires` becomes a REPORTED STATE** — Q-22. ⛔ **Not a validation error.**
Making it fatal would fail every module until its provider exists, which at 2.2% is all of them.
It must be a first-class outcome visible in the census — `satisfied` / `unsatisfied` / `input` —
so that "nothing defines this" stops being indistinguishable from "linked fine".

## 4 · ⭐ Stage 0 first — the cheap falsifier, before any corpus spend

**The premise of (i) is that glosses reproduce where names do not.** That is measured for *concept*
glosses — `[RAN]` 39 of 45 identical across repeat runs, all 6 differences pure paraphrase — but
**never for borrow glosses, which have never existed.**

⇒ **Re-translate only the existing 13 clauses, twice, with the new field.** Then ask the one
question that decides whether to go further:

> Do two independent translations of the same clause write **compatible expectations** for the same
> borrowed symbol?

| | outcome | what it means |
|---|---|---|
| ✅ | borrow-gloss agreement resembles concept-gloss agreement (~0.87, differences paraphrase) | premise holds — proceed to stage 1 |
| ⛔ | borrow-gloss agreement resembles borrow-NAME agreement (`[RAN]` **0.00**) | **STOP.** The join key is as noisy as the thing it replaces, and no amount of corpus buys a link |

**Cost: ~$0.07** (`[RAN]` ~$0.005/module — run `1719` $0.0284/5, run `1748` $0.0232/5), one guard
`--accept`, and a re-run of downstream artifacts. ⭐ **This is the whole point of doing it now:** the
same contract change after full translation costs ~$3.00 of a $8.50 ceiling with ~$2.15 already used.

## 5 · Stage 1 — translate neighbourhoods, and see whether links form

Sections chosen because `[RAN]` the 43 borrowed predicates cluster in them and the 12 orphans point
into them — not because they are convenient:

| section | clauses |
|---|---|
| `definitions` | 24 |
| `control_side_effects` | 23 |
| `levels_of_authority` | 22 |
| `follow_all_applicable_instructions` | 19 |
| `ignore_untrusted_data` | 17 |
| `scope_of_autonomy` | 16 |
| `letter_and_spirit` | 15 |
| `protect_privileged_information` | 15 |
| `transformation_exception` | 6 |
| `disallowed_content` | 5 |
| **total** | **162** of 593 |

**Cost: ~$0.81** at the measured rate. ⚠️ **Hold back two sections as HELD-OUT** — `DEBUGGING_TIPS`
§3, never measure a fix on the clauses that motivated it. The orphans came from
`follow_all_applicable_instructions`, `scope_of_autonomy`, `transformation_exception`,
`letter_and_spirit`, `control_side_effects`; `ignore_untrusted_data` and
`protect_privileged_information` are named in no orphan and are the natural held-out pair.

## 6 · Worked example that PASSES

`m0079` declares `requires: conflicts_with_higher_authority/1` with a new expectation gloss —
something like *"an instruction that conflicts with one at a higher authority level"*. Translating
`levels_of_authority` produces a clause that **defines** a predicate for that idea, under whatever
name it coins, with its own concept gloss.

**The link is proposed on the GLOSSES, checked against the SPANS, and reported with both.** ⇒
`m0079`'s orphan count falls from 2 to 1; the census shows one `requires` moving `unsatisfied →
satisfied`; the chain *clause A → clause B* exists for the first time.

## 7 · Worked example that FAILS, and how it is told apart from a bug

Two clauses borrow `policy_class/2` and write **incompatible** expectations — one *"the policy
category governing a kind of material"*, the other *"the class of policy that applies to a
request"*. ⭐ **That is not a failure of the experiment. It is problem #9 detected**, in the only
medium where detection is possible, and it is the first time the pipeline could see it at all —
`[RAN]` 20% of reused names already carry conflicting definitions and nothing reports it.

⛔ **The genuine failure is different and must not be confused with it:** a link is proposed on
agreeing glosses, and the two predicates' **clause-blind spans do not overlap**. Then the gloss
agreed and the grounding did not, which means the gloss is agreeing on a paraphrase rather than a
concept — and the join key is decorative. `[RAN]` The span data exists and is **97%** stable, so this
check is free.

## 8 · Pre-registered predictions

| | prediction | |
|---|---|---|
| **L0** | borrow-gloss agreement across repeat translations ≫ borrow-name agreement (0.00) | ⛔ **STAGE-0 FALSIFIER** — fails ⇒ stop, do not spend |
| **L1** | `requires` entries finding a provider rises from `[RAN]` **0 of 12** | the headline |
| **L2** | where a provider is found, borrower expectation and owner definition agree | the join key working |
| **L3** | some pairs of borrowers disagree ⇒ problem #9 becomes **countable** | a success, not a failure |
| **L4** | orphan count falls from `[RAN]` 6 of 19 modules | mechanical, judgment-free |
| **L5** | L1–L4 hold on the two held-out sections | ⛔ **FALSIFIER** — held-out only; the rest is fitting by construction |

## 9 · What it does NOT do

- ⚠️ It does not resolve symbols the document never defines. `contradicts/2`, `overrides/2`,
  `makes_irrelevant/2` are the one thing 5 of 5 iterative runs agreed on, and they must end as
  **explicit open inputs** — route 3. Success here makes that set *smaller and visible*, not empty.
- It does not settle Invariant 1's A/B/C. It supplies the dictionary arm C needs, built from
  expectations rather than retrieval.
- It does not test the extensional-identity proposal, which stays available as the *checking* side
  (§7) rather than the proposing side.

## 10 · Total

**~$0.88** and two model-facing changes, of which **~$0.07 is spent before the falsifier can stop
it.** ⛔ Requires: Matt's ruling on Q-23, on Q-22's reported-state form, and a `guard.py --accept`.
Nothing here is decided.

---

# ⛔ REVISION, before spending — the free check says the design was wrong

Matt asked to validate the experiment before paying for it, and to consider what *other* experiments
might need, so data is collected once. The validation was runnable on data already on disk.

## What it found: the DISCHARGE ROUTE ITSELF is a coin flip

| clause · run | `requires` / `inputs` | signature | situations stage 3 enumerates |
|---|---|---|---|
| `m0150` 1719 | 0 / 4 | 4 | **16** |
| `m0150` 1748 | 2 / 0 | 1 | **2** |
| `m0105` 1719 | 0 / 2 | 2 | 4 |
| `m0105` 1748 | 5 / 0 | 1 | 2 |

`[RAN]` **Two of two repeat-translated clauses with borrows show a WHOLESALE flip** — one run puts
everything in `inputs`, the other everything in `requires`. Because `inputs` reaches the signature
and `requires` does not (Q-22), **the same clause is testable or inert depending on which field the
model happened to pick**, and the test space differs by 8×.

⚠️ n = 2 clauses, so the *rate* is not established. But the mechanism is not probabilistic: given
Q-22, this consequence follows with certainty whenever the flip occurs.

## ⭐ Why this is not a model failure, and what it means

`requires` means *"another clause defines it"*. **That is a GLOBAL property of the corpus, not a
local property of one clause.** A translator seeing one clause cannot know whether any of the other
592 defines `pasted_text/1` — so we have been asking it to guess, forcing a choice, and then routing
the whole test space on the guess.

⇒ **Route assignment belongs at LINK time, where the corpus is visible — not at translation time.**
The translator can say *what it borrows* and *what it needs that to mean*. It cannot say *who will
provide it*.

This also explains the rest of the log without new hypotheses: borrowed **names** are noise (0.00)
because nothing constrains them; **glosses** are stable (39/45) because meaning is a local property
the translator can see; **providers** are 0/12 because at 2.2% coverage there are none to find.

## The revised collection — one contract change, several experiments

⭐ Matt's economics are right and decide the shape: **the cost driver is the translation PASS, not
the field count** (`contract_hash` covers all of `schema.py`, so any field addition re-translates
everything). So take the union of what the candidate experiments need and collect it once.

| | experiment | needs |
|---|---|---|
| E1 | do borrows find providers (linkage) | borrow gloss · corpus size |
| E2 | problem #9 becomes countable | borrow gloss *(free rider on E1)* |
| E3 | ⭐ **is the route guess any good?** | the guess recorded as a **hint**, and not acted on |
| E4 | naming normalization (Matt's route A) | borrow gloss · corpus size *(free rider)* |
| E5 | test-driven naming (Matt's route B) | orphan count — **no new field** |
| E6 | extensional cross-check | expected section per borrow *(optional)* |

**Union: one `borrows` list replacing `requires`/`inputs`**, each entry carrying

- `name`, `arity` — as today
- `gloss` — ⭐ typed as an **expectation** (*"I need an X that means this"*), never a definition
- `expected_discharge` — `case-fact` · `another-clause` · **`unsure`**, recorded as a **HINT**
- `expected_section` — optional, for E6

⭐ **Two design points carry most of the value:**

1. **Recording the route guess without acting on it.** The signature is then computed from *all*
   borrows, so no module can be silently inert (Q-22 dissolves), while E3 measures whether the
   guess was ever worth trusting. Today the guess is invisible *and* load-bearing — the worst
   combination.
2. **Allowing `unsure`.** The model is currently forced to choose and therefore flips. An explicit
   `unsure` converts a silent coin flip into recorded uncertainty, which is measurable.

⚠️ **The honest cost of collecting wide.** A larger output schema is a harder generation task —
more malformed output, more repair turns, more abstention. `[RAN]` repair traffic is already visible
in the run costs (19 calls for 5 modules). **So the batch must be bounded, and stage 0 must measure
schema-size cost, not just gloss stability.** Adding a field is not free merely because the money is
already being spent.

## Revised stage 0 — still ~$0.07, now answering three things

Re-translate the existing 13 clauses **twice** under the new contract, and measure:

| | prediction | |
|---|---|---|
| **L0** | borrow-gloss agreement ≫ borrow-name agreement (`[RAN]` 0.00) | ⛔ falsifier — fails ⇒ stop |
| **L6** | ⭐ every borrow reaches the signature; no module enumerates 2^0 or loses a body predicate | Q-22 dissolved, mechanical |
| **L7** | ⚠️ abstention and repair rates do **not** rise materially against the current corpus | the cost of the wider schema, measured rather than assumed |

⛔ **L7 is new and it is a genuine falsifier too:** if collecting wide degrades translation quality,
the union is the wrong batch and must be cut back to the gloss alone.
