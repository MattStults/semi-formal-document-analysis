# Atom justification audit — rating protocol

## What you are doing

A research team built an *ontology* of a source document. The document is a published
specification of how an AI assistant should behave (the "constitution"). The ontology
consists of **atoms**: small named units, each with

- a `name` (an internal identifier),
- a `kind` and `dimension` (bookkeeping labels — `context` = a condition that may hold in a
  situation, `act` = something the assistant may do),
- a `gloss` — a one-line English statement of what the atom means, and
- one or more `quote_spans` — verbatim excerpts from the source document, each with a
  `locator` giving the section and paragraph it came from.

Every quote span in this sheet has already been machine-checked: each quote really is an
exact substring of the paragraph its locator points to. **Passing that check is not the
question.** The question is whether the *gloss* is actually justified by the *document*.

Some atoms in this sheet may be faithful. Some may name a distinction the source document
never draws, and merely carry quotes from nearby text. Some may state something stronger
than their quotes support. Your job is to say which, item by item.

You are rating an instrument, not the people who built it. There is no penalty for calling
something an invention and no reward for finding a target number of problems. Rate each
item on its own.

## Materials you may use

- `audit_sheet.json` — the 20 items to rate.
- `constitution_clauses.json` — the full source document, split into clauses with locators.
  This is the source of truth for what the document says. You may read any part of it.

## Materials you may NOT use

**Do not consult any other document from this project.** In particular do not read
`vocabulary_pilot.json`, `audit_key.json`, `adversarial_review_1.md`, any `litreview*.md`,
any `sweep_*.md`, or any source code in the directory. Do not ask the project team which
items are which. If you have already seen any of those files, say so before you start —
your ratings would not be usable.

Working only from the sheet and the source document is the whole point: the experiment
measures whether the sheet alone is enough to catch an unjustified atom.

## What to do for each item

Read the gloss. Read the spans. Then go find those spans in
`constitution_clauses.json` and **read the surrounding paragraph and the paragraphs around
it** — spans are often truncations, and the sentence a span was cut from may say something
importantly different from the span. Search the document for other passages on the same
topic; the licensing sentence, if there is one, may not be one of the spans provided.

Then answer two questions, **in this order**. Answer Q1 before you look for a licensing
span, and do not go back and revise Q1 after doing Q2 — the two answers are compared
against each other, so an independently-formed Q1 is what makes the comparison meaningful.

### Q1 — global: does the source document draw this distinction?

> Ignoring for a moment which spans were attached: does the source document actually draw
> the distinction this atom names? That is, is there something in the document that
> recognises this condition or this act as a thing, in roughly the sense the gloss gives?

Choose exactly one:

- `document_draws_it` — yes; the document recognises this distinction, somewhere.
- `model_invention` — no; this looks like a category the extractor introduced. The document
  may discuss the neighbourhood, but it never draws *this* line.
- `cannot_tell` — you genuinely cannot decide after a reasonable search. Use this sparingly
  and say what would have settled it.

Also record, in one or two sentences, **why** — and if you answered `document_draws_it`,
name the passage (locator or clause id) where the document draws it, which may or may not
be one of the spans on the sheet.

### Q2 — directed: which span licenses this gloss, and does the gloss overreach?

> Of the spans attached to this item, which one (if any) actually licenses the gloss? Paste
> its text. Then judge whether the gloss asserts more than that span establishes.

Record:

1. `licensing_span` — free text: paste the quote of the span you think comes closest to
   licensing the gloss. If none of them do, write `NONE`.
2. `verdict` — exactly one of:
   - `gloss_matches_span` — the span establishes what the gloss says, no more and no less.
   - `gloss_asserts_more` — the span is relevant and real, but the gloss claims something
     stronger, broader, or more specific than the span establishes.
   - `no_span_licenses_gloss` — none of the attached spans establish the gloss at all, even
     partially. (Use this when the spans are merely on the same topic.)
3. `q2_reason` — one or two sentences naming the gap, if any: what does the gloss assert
   that the span does not?

Q1 and Q2 can disagree, and that is fine and informative. An atom can name a real
distinction while carrying the wrong spans, and an atom can carry a perfectly good span
while overreaching in its gloss.

### Confidence

For each item also record `confidence`: `low` / `medium` / `high`, covering your Q1 answer.

## Output format

One JSON object per item, in the order the items appear on the sheet:

```json
{"item_id": "a01",
 "q1": "document_draws_it | model_invention | cannot_tell",
 "q1_reason": "...",
 "q1_locator": "clause id or locator, or null",
 "licensing_span": "pasted quote text, or NONE",
 "q2": "gloss_matches_span | gloss_asserts_more | no_span_licenses_gloss",
 "q2_reason": "...",
 "confidence": "low | medium | high"}
```

## Worked example

The item below is **not** in your sheet. It is here only to calibrate you on the two
questions. Three versions of the same atom are shown; only the first is faithful.

### Example A — a faithful atom

```json
{"item_id": "x01", "atom_name": "caution_not_needed", "kind": "context",
 "dimension": "situation",
 "gloss": "hedging/caveats not actually needed here",
 "quote_spans": [
   {"locator": "constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶3",
    "quote": "out of caution when it isn’t needed"},
   {"locator": "constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶6",
    "quote": "warnings, disclaimers, or caveats that aren’t necessary or useful"}]}
```

Looking these up, the source paragraphs read *"Gives an unhelpful, wishy-washy response out
of caution when it isn't needed."* and *"Adds excessive warnings, disclaimers, or caveats
that aren't necessary or useful."* Both are in a list of failure modes the document wants
avoided. The document therefore does treat "caution that isn't needed" as a real condition
it is tracking.

Rating: `q1 = document_draws_it`. `licensing_span` = the ¶3 quote;
`q2 = gloss_matches_span` — the gloss says exactly what the spans say, and no more.

### Example B — same spans, widened gloss

```json
{"gloss": "caveats and disclaimers are never appropriate and should be omitted", ...same spans...}
```

The distinction is still one the document draws (unnecessary caveats are a failure mode), so
`q1 = document_draws_it` again. But the spans establish that caveats are bad *when they
aren't needed / aren't necessary or useful* — a conditional. The gloss drops the condition
and asserts a blanket prohibition. Elsewhere the same document explicitly permits
"appropriate caveats", which the gloss would forbid.

Rating: `q1 = document_draws_it`, `q2 = gloss_asserts_more`, reason: "spans are conditional
on the caveat being unnecessary; the gloss is unconditional."

Note what this example shows: **Q1 can be `document_draws_it` and the atom can still be
defective.** That is exactly why both questions are asked.

### Example C — an invented distinction with real, adjacent spans

```json
{"atom_name": "caveat_length_limit", "kind": "context", "dimension": "situation",
 "gloss": "the caveat exceeds the one-sentence length above which it counts as excessive",
 "quote_spans": [
   {"locator": "constitution@2026-01-20 > Being helpful > Balancing helpfulness with other values > ¶6",
    "quote": "warnings, disclaimers, or caveats that aren’t necessary or useful"}]}
```

The span is real, verbatim, correctly located, and obviously about caveats. But the document
nowhere sets a length at which a caveat becomes excessive — it judges caveats by whether
they are necessary or useful, not by how long they are. A threshold has been imported from
outside the text.

Rating: `q1 = model_invention`, reason: "document judges caveats by necessity, never by
length; no passage sets any length threshold." `licensing_span = NONE`,
`q2 = no_span_licenses_gloss`.

Note what this example shows: **a real, verbatim, correctly-located span is not evidence
that the atom is justified.** Adjacency is cheap. Ask what the sentence actually
establishes.

## A few reminders

- Read the *whole* sentence a span was cut from. Truncation is the most common way a span
  ends up saying less than it appears to.
- A gloss that adds a threshold, a quantity, a scope extension ("or ...", "including ..."),
  or a new obligation is asserting more than a span that lacks it.
- If the document's own wording is permissive ("can", "may") and the gloss is obligatory
  ("must", "should", "is required"), that is an overreach.
- Do not use the atom `name` as evidence. Names were written by the extractor and can be
  more confident than the text supports.
- Take the items in the order given. Do not skim ahead for a pattern.
