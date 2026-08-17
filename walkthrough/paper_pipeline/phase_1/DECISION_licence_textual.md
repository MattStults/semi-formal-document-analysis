# DECISION — `licence: "textual"` means "the source text says this" (2026-08-16)

**Owner ruling (Matt Stults, 2026-08-16), resolving the open question stated by the
slice-5 critic and recorded in `_debug_gen11/SERIES_HANDOFF.md` §7:**

> Does `licence: "textual"` mean **"the source text says this"** or **"this node's
> contract says this"**?

**Ruling: the first. `textual` is a claim about the cited clause's source text and
nothing else.** A meaning that reaches the translator any other way — a `NEEDS`
contract, an assigned predicate name's description, a reading of what the section must
intend — is `assumed`, with the `inference` naming where it came from.

## The rejected alternative, by name

**"`textual` covers what this node's contract says" — rejected.** Under that reading a
borrowed `NEEDS` gloss is `textual` against the borrowing node, which is what the prompt's
own worked example demonstrated until today. Three independent critics (opus_pairs slices
2, 3, 5) traced module defects to that demonstration; slice 2's citation audit found
`root_authority`'s entire gloss had zero support in the lines it cited. The reading makes
a citation into a claim about the *graph* while every reviewer grades it as a claim about
the *document* — the manufactured-citation failure `00_task.md` already names as the worst
one available. It also destroys the diagnostic value of `assumed`: the licence field stops
distinguishing "the document states this" from "the pipeline handed me this".

## What was edited to implement it

All three files are guard-watched; accepted by name after these edits.

1. **`prompt/00_task.md`** — licence table row for `textual` sharpened; a paragraph added
   stating the source-text test. Same commit: the abstention triggers ("it is a section
   heading", "it is an example") were replaced by the establishes-test, retiring the
   contradiction with `node_worked_example.md` found independently by slices 2 and 3
   (the worked example demonstrates a heading node and an example node translated, and
   says what decides is whether the node establishes anything — not the kind of passage).
2. **`prompt/10_output_format.md`** — the `requires`-gloss rule (the line the Opus critic
   cited twice when it declined the borrowed-gloss fix) now states the licence
   consequence: a borrowed name's `concepts` gloss is `assumed` naming its origin, unless
   the clause's own text states the meaning.
3. **`resolve_runs/graph_v2/node_worked_example.md`** — contract 2 now states the licence
   rule, and the demonstrations conform: `best_intentions_bias`,
   `authority_levels_hierarchy` (example 1) and `voice_turn_taking_rule` (example 3)
   are `assumed` with inferences naming the NEEDS contract. These were the manufactured
   citations slice 2 found (SERIES_HANDOFF §7, "THE PROMPT'S OWN GOOD WORKED EXAMPLE
   MANUFACTURES CITATIONS").

## Consequences downstream

* The borrowed-gloss class (20/23 in the gen-11 sample), the manufactured-citation
  findings, and the `assumed`-vs-`textual` disagreement in SERIES_HANDOFF §0 all resolve
  in the same direction: the modules that marked borrowed glosses `assumed` were right.
* Existing translated modules that mark borrowed `NEEDS` glosses `textual` are now
  formally defective on this point. The corpus-level sweep (`needs_gloss_licence` check)
  counts them; whether a module is redrawn for this alone is a per-region call in the
  pilot-subset work, not an automatic invalidation — the defect is mechanical and
  auditable, and the fix is licence-field-only.
* Review-list entries that fought the old demonstration (the E6-signature weakenings)
  lose their prompt cover; the list fold that follows the opus_pairs series should be
  done against this ruling.
