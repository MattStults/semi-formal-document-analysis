# PRE-REGISTRATION — re-draw the 25 reference clauses under the REPAIRED prompt

Written and committed BEFORE the run. The campaign review's finding that
prompted it:

> **Not one module has been drawn under the repaired prompt.** The reference
> set, the golden set, the 65% ceiling and every seat-fix arm describe a prompt
> that no longer exists.

## What changed in the prompt

`node_worked_example.md`, commit `cee3d0e` (attested `mattstults`). It now
teaches the **three-way route** (norm → `asserts`; structural fact → `ontology`
with `asserts` empty; neither → abstain), states that an empty `asserts` list is
not an empty module, records the `NEEDS`→`requires` contract in a demonstration
that previously violated it, and corrects the exemplar-id claim.

Assembled system prompt: **39,968 chars** (was 36,605). All prior runs used the
36,605-char version, sha `5ff9daf7…`.

## The measurement

Re-draw all **25** reference clauses. Compare each new module against the
**reference module** (`_debug_gen11/reference_set/modules/<id>.json`) and against
the **26 classified edits** (`diffs.json`), which name exactly what was wrong
with the original draw.

Edit classes at stake: dropped-content 6 · inverted-modality 5 ·
scope-drift-widen 5 · other 4 · fact-as-deontic 2 · invented-obligation 1 ·
disjunction-as-conjunction 1 · dropped-obligation 1 · weakened-modality 1.
**16 of the 25 clauses carried at least one edit; 9 were clean.**

## Pre-registered readings — fixed before any result is seen

Let `R` = of the 26 known edits, how many the new draw no longer needs.

| result | reading |
|---|---|
| **R ≥ 13 (50%)** | The prompt repair carries real corpus benefit. The fix matrix's 58% ceiling estimate is broadly supported by direct measurement. |
| **4 ≤ R < 13** | Partial. Report per class — the composition matters more than the total, since the repair targeted ROUTING and should not be expected to touch polarity or dropped content. |
| **R < 4** | The prompt repair does not move the corpus. Every instrument-side fix should then be re-justified on its own, because the ceiling was estimated against a prompt whose repair does nothing. |

**The honest prior, recorded now so it cannot be claimed afterwards:** the
repair targets the abstain-vs-translate ROUTE. It should plausibly move
`fact-as-deontic` (2) and `invented-obligation` (1), possibly some of `other`
(4). It has **no mechanism** to reach `inverted-modality` (5) or
`dropped-content` (6) — those trace to the missing negative pole and to
span-first blindness respectively. **So a "good" result here is R ≈ 3–7, not
13.** A result of R ≥ 13 would be surprising and should be treated as suspect
rather than celebrated.

## Secondary, recorded now

1. **REGRESSIONS.** Of the 9 clauses the reader called FAITHFUL, how many now
   carry a defect they did not have? Any regression is reported however small —
   the repaired prompt is guard-attested and shipping.
2. **Abstention rate.** The repair explicitly tells the model an empty `asserts`
   list is not an empty module. If abstentions *rise*, the repair is being read
   as licence to abstain, which is the opposite of the ruling.
3. **Route mix** — ontology-only vs hard-deontic, against 19% on the fresh slice
   and 57% on the paired re-run.
4. **`checks.polarity_mismatches`** on the new draws, against 4 known
   inversions in this cohort.

## What this CANNOT settle

* Whether the reference set is right. It is one reader, 25 clauses, and the
  campaign review found only **1 of 16 clauses is an independent discovery**.
  This measures agreement with that anchor, not correctness.
* Anything about generalization — same document, same decomposer.
* n = 25 clauses / 26 edits. Every per-class cell is single-digit.
