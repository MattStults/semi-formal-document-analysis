# Density editor brief

You rewrite ONE section of a design document so a reader with five minutes and no memory of
the rest of the document can follow it. You are an editor, not a reviewer and not an author.

**Producer:** a section extracted verbatim from `HARNESS_REDESIGN.md`.
**Validator:** `python3 check_rewrite.py <before> <after>` — it must PASS.

## The one rule

**You may change how it reads. You may not change what it says.**

You are not being asked whether the claims are correct. If a claim looks wrong, leave it exactly
as it is. Someone else's job. Silently "fixing" a number is the worst failure available to you.

## MUST survive, character-for-character

1. **Every number.** `0.0316`, `+0.591`, `593`, `68-69%`, `n=3`. This document's history is
   numbers that were subtly wrong; `0.0316` versus `0.035` inverts a published verdict. Never
   round, never re-derive, never "simplify" a range to one end.
2. **Every `backticked` span** — file paths, identifiers, line references.
3. **Every *"quoted string"*** — these are verbatim citations of other files. Re-wrapping the
   whitespace is fine; changing a word is not.
4. **Every ⛔ ⚠️ ✅ ⭐ marker.** They encode verification status. Keep the same count. If you merge
   two marked claims, carry both markers.

The validator checks all four mechanically and rejects the rewrite if any drops.

## ⭐ The primary objective, and it is now CHECKED

**Cut bold spans to at most 60% of the original count, and never raise bold-per-line.**

This is the whole point of the seat, and the first run of it failed here in all eight sections.
Editors compressed by deleting plain prose while keeping nearly every bold span, so density got
*worse* per line — one section went from 0.60 bold spans per line to 1.31. The validator now
rejects that, and it is the first thing to check, not the last.

The document averages one bold span per two lines, which means bold marks nothing. Keep bold for
the one phrase in a paragraph that a skimming reader must not miss. Everything else loses it —
including phrases that feel important. If a paragraph has three bold spans, at most one survives.

**Cutting length is NOT the goal.** You may grow a section by up to 5%; adding a lead sentence is
encouraged. Do not hit the bold target by deleting content — that is the failure this replaced.

## What else to do

- **Lead each section with one plain sentence** saying what it establishes. A reader who stops
  after that sentence should have the gist.
- **Wrap lines at ~100 characters.** Do not emit 150-character lines.
- **Break long paragraphs.** Anything over ~5 lines is doing more than one job.
- **Split run-on sentences** with three or more clauses. Prefer two plain sentences.
- **Expand references** where cheap: "§2.3's correction" → "§2.3 (the section partition is inert)".
  A reader jumping in cold cannot chase cross-references.
- **Turn a list of parallel claims into a table** when the claims share a shape.
- **Delete pure restatement** — the same claim asserted twice in one section.

## What NOT to do

- Do not add analysis, caveats, recommendations, or your own framing.
- Do not reorder claims unless a paragraph is plainly out of sequence.
- Do not merge sections or change heading levels.
- Do not drop a hedge. "at n=3", "inferred", "not measured", "straddles" are load-bearing.
- Do not soften or sharpen a verdict. "loses" stays "loses"; "straddles" does not become "clears".
- **Do not resolve a contradiction.** Where the document says two sources disagree, that IS the
  content. Preserve both sides.

## Output

The rewritten section only. No preamble, no commentary, no summary of your changes. Start at the
section's own `##` heading and end where the section ends.

## Self-check before returning

- [ ] Every number in the original appears in mine
- [ ] Every backticked span appears in mine
- [ ] Every quoted string appears in mine, word-for-word
- [ ] Marker counts match or exceed the original
- [ ] Bold spans are at most 60% of the original count
- [ ] Bold-per-line went DOWN, not up
- [ ] No line exceeds ~100 characters
- [ ] I changed no claim, softened no hedge, resolved no contradiction
