# Spec citation convention

Every claim about what a spec says must carry a locator that resolves to an exact,
verbatim span of the spec text -- unambiguous start point, unambiguous end point.
This file defines the locator format. The resolver lives at `engine/spec-cite/cite.py`;
a locator is only valid if the tool resolves it to the intended text.

## Locator format

```
<spec>@<version> > <section-ref> > ¶<n>[ s<a>[-<b>]]
```

Examples:

```
model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1
constitution@2026-01-20 > Being broadly ethical > Being honest > ¶18 s1-4
constitution@2026-01-20 > Being helpful > What constitutes genuine helpfulness > ¶9 s1
model-spec@2025-12-18 > #letter_and_spirit > ¶12 s1-2
```

Reading order of the parts:

| Part | Meaning |
|---|---|
| `<spec>@<version>` | Which document and which release. `constitution@2026-01-20`, `model-spec@2025-12-18`. The version is mandatory in stored citations: a locator into an unpinned spec is meaningless after the next release. |
| `<section-ref>` | The smallest heading enclosing the text (see below). |
| `¶<n>` | Block number within that section, counting from 1. `p<n>` is an accepted ASCII spelling. |
| `s<a>[-<b>]` | Sentence or sentence range within the block. Omit to cite the whole block. A range spanning blocks is written `¶4 s2 - ¶5 s1`. |

`>` and `›` are interchangeable path separators.

## Section references

- **OpenAI Model Spec:** always use the stable anchor, e.g. `#avoid_sycophancy`.
  Anchors are defined in the markdown source (`{#anchor authority=...}`) and are the
  same IDs used by model-spec.openai.com, so one reference works for the mirror and
  the published page.
- **Claude constitution:** no anchors exist, so use the heading-title path from the
  top-level chapter down to the enclosing heading, e.g.
  `Being broadly ethical > Being honest`. Titles are quoted exactly as written
  (case-insensitive match). A trailing subset of the path is accepted when unique
  (`Being honest` alone resolves today), but stored citations should carry the full
  path so they never break if a duplicate title is later added.

Always cite into the *smallest* enclosing section: text under a `###` subsection is
cited via that subsection, never via its parent chapter. A section's block numbering
covers only its direct span (heading to next heading of any level), so subsection
content never shifts a parent's numbering.

## What counts as a block (¶)

Within a section's direct span, blocks are numbered 1..N in reading order. One block is:

- a prose paragraph (text separated by blank lines);
- **each top-level list item** (its nested sub-items and continuation lines belong to
  it) -- so the constitution's "Truthful / Calibrated / Transparent / ..." components
  are separately addressable blocks;
- an example unit in the Model Spec: the `**Example**: ...` caption plus its fenced
  `~~~xml` transcript count as **one** block, cited whole (no sentence numbers inside);
- any other fenced code block, blockquote, or table.

Headings are not blocks.

## What counts as a sentence (s)

Sentences are numbered from 1 within their block, split at `.` `!` `?` (plus any
closing quotes/brackets) followed by whitespace and an uppercase letter, digit, or
opening quote/bracket. Abbreviations ("e.g.", "i.e.", "etc.", "vs.", ...) do not end
sentences; colons and semicolons never do. A list item's bold label (`**Truthful**:`)
is part of its first sentence. The numbering the tool prints (`cite.py show`) is
definitive -- never count by hand.

## Verbatim text and normalization

Quoted excerpts are verbatim: original wording, casing, and punctuation, including
the originals' em dashes and ellipses. Exactly three mechanical normalizations are
applied (by `cite.py`, never by hand):

1. inline footnote markers (`[^sy73]`) are removed;
2. markdown links are reduced to their visible text, and Model Spec cross-references
   (`[?](#avoid_sycophancy)`) are rendered as the bare anchor (`#avoid_sycophancy`);
3. line wraps and list markers are dropped, whitespace collapsed to single spaces.

Nothing may be silently elided inside a quote. To skip material, end the excerpt and
start a new locator; a discontinuous quotation is two citations.

## Tooling

```
python3 engine/spec-cite/cite.py outline model-spec            # section tree + anchors
python3 engine/spec-cite/cite.py show "constitution > Being honest"   # numbered ¶/s
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find model-spec "some remembered phrase"   # text -> locator
```

Workflow for extracting an excerpt: `find` the passage, `show` the section to pick
the exact span, `resolve` the locator, and store the resolver's output as the quote.

## Where citations are used

- Notion DB **Spec Coverage by Behaviour**: each row's page body lists every excerpt
  as locator + verbatim quote.
- Sweep records (`research/sweeps/*.md`) and the "Behaviours to track" page.
- `data/coverage.json` (Phase 1): each coverage entry stores `locator` + `quote`, and
  CI re-resolves locators against `specs/` so a spec update that moves text fails
  loudly instead of silently.

New spec versions: add the mirrored file, register it in `SPECS` in `cite.py`, and
re-resolve stored locators; block numbers are stable only within a pinned version.
