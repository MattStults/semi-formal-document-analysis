# RULING 01 — the cap is NOT raised, and the truncation is a RESULT

**Written mid-run, after cell F1's critic phase was observed and before any
repair call, any F2 call, and any scoring.** Recorded here rather than in the
transcript, per `REPRODUCIBILITY.md`.

## What was observed

F1's critic calls reason **far longer than arm E's**, and hit the 8,192-token
wall at a rate arm E never approached.

| | arm E (7,168, no ban) | **F1 (8,192, ban)** |
|---|---|---|
| reasoning chars, completed calls | 8,464 – 31,723 | **21,163 – 32,939 (first 12 rows)** |
| calls hitting the wall | 4 of 17 (24%) | **7 of the first 12 (58%)** |

⭐ **The ban is the most plausible cause and it is a finding, not an accident.**
A critic told *"decide which remedy is right for THIS span and write only that
one"* has been handed strictly more work than one allowed to write *"either add
X or delete Y"*. The disjunction was not only a defect in the output; it was a
**shortcut in the reasoning**, and removing it costs roughly 1.3× the thinking
per finding.

## The decision

⛔ **The cap is NOT raised, no clause is retried, and neither cell is re-run.**

## Grounds, with the tempting alternatives rejected by name

1. **`PREREG.md` §5 fixes `CRITIC_MAX_TOKENS = 8192`, uniform, no retries, and
   it was signed before the first call.** Raising it now would be tuning after
   seeing results — the exact thing `PREREG.md` §9.1 forbids.
2. **Rejected by name: *retry the truncated clauses at 12,288*.** The truncated
   set is selected BY THE BEHAVIOUR UNDER TEST — these are the clauses the ban
   made the critic work hardest on. A retry set so selected makes the sample
   heterogeneous in a way correlated with the outcome. This is arm D's stated
   reason for declining the same move and arm E's for declining it again.
3. **Rejected by name: *re-run all 17 in both cells at a higher cap*.** Uniform,
   so it escapes objection 2 — but it is still a design change chosen after
   seeing the outcome, it costs four more phases against a $0.25 cap that would
   not hold them, and it would leave two versions of each cell with no
   pre-registered rule for which is reported.
4. **Rejected by name: *drop the ban's wording to shorten the reasoning*.** That
   is changing the intervention to protect the sample. The intervention is what
   is being measured.

## What this costs, stated before the numbers exist

* ⛔ **The completed sample will be much smaller than arm E's 13 of 17, and the
  loss is NOT random: the lost clauses are the ones the critic worked hardest
  on.** Every rate arm F reports is therefore over a sample biased toward the
  clauses the critic found EASY, and the bias points the same way it did in arms
  D and E.
* **The paired intersection across arm E, F1 and F2 will be smaller still**, and
  is the only set on which the three are strictly comparable.
* ⚠️ If the completed sample falls below ~7 clauses per cell, **the cell cannot
  support a rate at all** and will be reported as a case series, not a
  measurement. That call is made on the count, not on which way the count
  points.

## What it buys

The truncation rate becomes a **measured cost of the intervention**, on the
record, at a fixed cap, with no selection: **F1 vs arm E at 8,192 vs 7,168 is
not like-for-like, but the reasoning-length distributions are, and they are
reported.**

— adjudicator, 2026-08-16, mid-run
