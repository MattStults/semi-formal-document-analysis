# Pre-registration — does asking for PREDICATES instead of CONCEPTS close the gap?

**Frozen before the variant was run. 2026-08-08.**

## The result being explained

Run `20260808-080133` asked *"what concepts does this section need to make sense?"* Its answer
overlaps the predicates our translated modules actually borrow by **1 of 32 (3%)**.

Two readings:
1. **The probe asked the wrong question.** A reader's concept list is not a translator's predicate
   list. `conflicts_with_higher_authority` is a *relation a rule tests*; `authority_levels` is *the
   concept it tests against*. Both correct, neither the other.
2. **The granularities are irreconcilable**, and the map's role is to CHECK names (arm C), not to
   SUPPLY them (arm A).

This variant tests reading 1 and nothing else.

## The change, and it is one change

Same document, same section markers, same two-turn accumulating transcript, same model. Only the
question moves: from *"what concepts does this section need"* to *"what predicates will a rule
written from this section have to test, and which of them must come from elsewhere"*.

⛔ **The model is NOT shown our modules, our predicate names, or any translated output.** It is
shown the shape of the target (a rule with a body of conditions), which is our pipeline's own
design, not the answer. Showing it the 32 names would be fitting the probe to its own scoring set.

## The prediction ⭐ FROZEN

**Overlap with the 32 borrowed predicates rises materially above 3%.** If reading 1 is right, asking
for predicates should produce predicate-shaped names.

⛔ **FALSIFIER:** overlap stays at or near 3%. That supports reading 2 — the map is a resolution
target, not prompt context — and the pre-translation phase should be designed as arm C, a lookup the
translator never sees.

## What this cannot settle, stated in advance

1. **n = 7 translated modules, 32 borrowed predicates, 6 sections.** A small and non-random sample:
   these are the clauses that happened to be translated during harness development.
2. **Overlap is measured by NAME.** Two names for one predicate score as a miss, so this
   **understates** agreement. A high score is therefore strong evidence and a low score is weak —
   asymmetric, and the asymmetry favours the falsifier being wrong rather than right.
3. **It says nothing about whether supplying the map helps a translator.** Invariant 1's recorded
   objection to arm A is about supplying names increasing hallucination; neither run tests delivery.
4. One model, one temperature, one pass. No repeats, so run-to-run variance is unmeasured.

## Cost
Two turns, one accumulating transcript, ~$0.03 worst case. Run `20260808-080133` cost $0.0253.
