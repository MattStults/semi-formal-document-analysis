# Model Spec clause segmentation summary

Source: `external/model_spec/model_spec.md`, `model_spec@2025-12-18`
(sha256 `8c95f02085548b145468ea45b4c9d99ab6f915e097854fa919dd35b34fd077c0`, 271,474 chars).
Inventory: `modelspec_clauses.json`. Producer: `segment_modelspec.py` +
`modelspec_kinds.py` (hand-assigned kinds).

**Total clauses: 593** — 410 prose clauses + 183 example blocks.

## Headline: character coverage

| | chars | % of source |
|---|---|---|
| **inside a clause `quote`** | **264,280** | **97.35%** |
| heading lines (text preserved in `section_path` / `section_id`) | 5,704 | 2.10% |
| blank lines | 603 | 0.22% |
| line separators between units | 592 | 0.22% |
| list bullet markers + block indentation | 295 | 0.11% |
| **unaccounted** | **0** | **0.00%** |

Every character is either inside a clause quote or is one of four structural
tokens, asserted in `segment_modelspec.accounting()`. No body text is dropped.

For contrast, the 259 focus-area markers reach 50,855 chars (18.7%) and zero
example-block characters. Example blocks alone are **150,079 chars — 55.3% of
the document** and were previously unaddressable.

## By kind

| kind | count | % |
|---|---|---|
| conditional | 188 | 31.7% |
| example | 183 | 30.9% |
| definitional | 84 | 14.2% |
| meta | 72 | 12.1% |
| holistic | 66 | 11.1% |

Excluding example blocks (the prose-only pool comparable to the constitution's
616 clauses): conditional 45.9%, definitional 20.5%, meta 17.6%, holistic 16.1%.
The Model Spec is markedly more rule-shaped than the constitution (31.7%
conditional over its whole corpus) — expected, since it is written as direct
instructions to a model rather than as a values document.

Kinds were hand-assigned clause by clause after reading (`modelspec_kinds.py`
is the record). One systematic rule: all 28 `!!! meta "Commentary"` blocks are
`meta`, on the spec's own definition of them ("commentary that is not directly
instructing the model").

## By top-level section

| section | clauses | conditional | holistic | definitional | meta | example | with focus markers | quote chars |
|---|---|---|---|---|---|---|---|---|
| Overview | 51 | 7 | 10 | 11 | 23 | 0 | 0 | 12,638 |
| Definitions | 24 | 0 | 0 | 20 | 2 | 2 | 0 | 6,760 |
| The chain of command | 118 | 39 | 18 | 26 | 14 | 21 | 34 | 39,663 |
| Stay in bounds | 127 | 46 | 5 | 6 | 12 | 58 | 39 | 69,714 |
| Seek the truth together | 114 | 34 | 14 | 14 | 10 | 42 | 31 | 57,249 |
| Do the best work | 33 | 15 | 5 | 1 | 1 | 11 | 18 | 15,746 |
| Use appropriate style | 107 | 36 | 14 | 5 | 7 | 45 | 36 | 53,014 |
| Under-18 Principles | 19 | 11 | 0 | 1 | 3 | 4 | 0 | 9,496 |
| **total** | **593** | **188** | **66** | **84** | **72** | **183** | **158** | **264,280** |

## Focus markers

* 259 `[^xxxx]` markers in the source, 259 distinct, **259 assigned to a clause**
  (0 orphans). Every `focus_id` in `modelspec_focus_areas.json` appears in some
  clause's `focus_ids`.
* **158 clauses (26.6%) carry at least one marker; 435 (73.4%) carry none.**
  The privileged focus-area subset is therefore recoverable exactly
  (`[c for c in clauses if c["focus_ids"]]`) while no longer being the only way
  in. Markers are retained inside `quote` verbatim.

## Example blocks: one clause per block

183 `~~~xml` blocks, each **one clause**, `kind: "example"`,
`in_example_block: true`, quote spanning the `**Example**: <caption>` line
through the closing `~~~` fence (blank line between included, so the quote is a
single contiguous source substring).

Why not one clause per message turn:

1. **The benchmark only ever cites captions.** All 313 example-block passages in
   the 863-passage panel set quote the caption line ("Example: ambiguous message
   from user, ..."), never a `<user>`/`<assistant>` turn body. Splitting per turn
   would create 630 turn clauses that no panel passage can hit, while the
   caption would sit alone in a clause stripped of the behaviour it illustrates.
2. **The panel numbers blocks as single paragraphs.** Its locators
   (`#ask_clarifying_questions > ¶12`) count each block as one `¶`; our numbering
   reproduces this (see below).
3. **`<comparison>` blocks are only meaningful whole.** A GOOD/BAD pair read
   apart from its sibling inverts its meaning.

Cost: blocks are large (mean 820 chars, max 3,036), so an example clause is a
coarser retrieval unit than a prose clause. If a later stage needs turn-level
addressing, split *within* the clause rather than renumbering `¶`.

## Verification (all assertions run in `segment_modelspec.main()`)

| check | result |
|---|---|
| `quote` is an exact substring of the source | **593 / 593 (100%)** |
| locator uniqueness | 0 duplicates |
| focus markers landing in a clause | 259 / 259 |
| clauses with a hand-assigned kind | 593 / 593 |
| characters unaccounted for | 0 |

## Cross-check against the LLM panel (863 Model Spec passages)

Joining on quote containment after normalizing footnote markers, whitespace,
markdown emphasis, and markdown links:

| | matched | notes |
|---|---|---|
| all panel passages | **849 / 863 (98.4%)** | 847 matched exactly one clause |
| example-block passages | **313 / 313 (100%)** | previously 0% reachable |
| high-consensus passages | 110 / 112 | |
| high-consensus example-block | **43 / 43** | |

`¶` numbering independently reproduces the panel's for 730 of 863 passages,
i.e. the unit boundaries agree, not just the text.

The 14 misses are all panel transcription artifacts, not segmentation gaps: the
panel's renderer inconsistently rewrote `[text](url)` sometimes to `text`,
sometimes to `url`, occasionally differently within one passage.

### Required change to the join normalizer (not in files I own)

`inventory._norm` today strips only footnote markers and whitespace. Against
this segmentation that yields **377 / 863**. Markdown emphasis (`**`, `*`,
`` ` ``) and links must also be normalized to reach 849. Notably, *no*
example-block passage can match without emphasis stripping, because every
caption is `**Example**: ...` in the source and `Example: ...` in the panel.
Recommended normalizer, matching on either link rendering:

```python
FOOTNOTE = re.compile(r"\[\^[a-z0-9]+\]")
LINK     = re.compile(r"\[([^]]*)\]\(([^)]*)\)")
EMPH     = re.compile(r"\*\*|\*|`")
def variants(s):
    s = FOOTNOTE.sub("", s or "")
    return {" ".join(EMPH.sub("", LINK.sub(lambda m: m.group(k), s)).split())
            for k in (1, 2)}   # link -> text, and link -> target
```

## Structure that resisted clean segmentation

* **Lazy list continuations.** Red-line principles line 34 continues the bullet
  on line 33 with no bullet and no indent; several other lists do the same.
  Handled by absorbing unblanked non-bullet lines into the preceding item, so
  the two lines form one clause rather than a bullet plus an orphan paragraph.
* **`!!! meta "Commentary"` blocks.** Their 4-space-indented bodies sometimes run
  to several paragraphs. Kept as one clause including the `!!!` marker line,
  because the panel quotes and numbers them that way
  (`#refusal_style > ¶4` == `!!! meta "Commentary" We have updated ...`). This
  makes commentary a coarser unit than surrounding prose.
* **Bold pseudo-headings.** `**When to express uncertainty**` and
  `**Favoring longer responses:**` are structural headings written as body
  paragraphs. They are emitted as `meta` clauses and consume a `¶`, but they
  carry no content and never anchor anything.
* **Indentation under authority-level bullets.** Under `- **Root**: ...` the
  spec places three indented explanatory paragraphs. These become separate
  clauses; the alternative (folding them into the bullet) would produce a
  1.5k-char clause whose first sentence is a definition.
* **`¶` numbering drift.** Our numbering matches the panel's in 730/863 cases;
  the residual drift traces to commentary blocks and to a handful of
  parenthetical cross-reference lines (`(see also [?](#letter_and_spirit) ...)`)
  which the panel appears to have folded into a neighbour. Because the join is
  on quote containment, this is cosmetic — but do not treat panel `¶` numbers as
  authoritative keys.
* **Ten ``` fenced code blocks** all sit inside `~~~xml` example blocks and
  needed no separate handling; the `~~~` scan reaches the true closing fence
  because backtick fences never close a tilde fence.
