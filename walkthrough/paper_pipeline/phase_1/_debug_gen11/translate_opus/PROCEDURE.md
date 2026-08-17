# Translation pass — the procedure

Owner's ruling, 2026-08-16: **strictly sequential from wave 2 onward.** Wall-clock
is accepted so that every agent sees every prior agent's findings. Wave 1 (5
clauses, parallel, list v1) is grandfathered and runs to completion.

## The loop, per clause

1. **Dispatch ONE agent** for one clause. It reads `REVIEW_LIST.md` at its
   current version and the clause's own `spans/<id>.prompt_user.txt`.
2. Agent writes `out/<id>.json`, `out/<id>.notes.md`, `out/<id>.lessons.md`.
3. **The coordinator folds and dedupes** `lessons.md` into `REVIEW_LIST.md`,
   bumps the version, and records the fold in `LIST_LOG.md`.
4. **Only then** is the next agent dispatched.

⛔ No agent starts before the previous one's lessons are folded. That is the
whole point of the sequencing and it is the one step that must not be skipped
for speed.

## Fold-and-dedupe rules

The list is only worth its APPLICATION. An agent asked to check 40 entries
checks none of them properly, so the list is kept SHORT on purpose.

* **Merge on the QUESTION, not the wording.** Two entries asking the same
  discriminating question are one entry. Keep both clause provenances — the
  second occurrence is evidence the class is real, and that is worth more than
  a separate row.
* **Reject descriptions.** An entry must be a question a later reader can apply
  mechanically. "Watch out for scope drift" is not an entry; "does each body
  widen past the span's qualifier?" is.
* **A lesson that only restates the schema is not a lesson.** It belongs in the
  output-contract reading, not here.
* **SOFT CAP 20 ENTRIES.** At 20, the weakest-evidenced entry must be merged or
  retired before a new one is added, and the retirement is recorded. A list
  that grows without bound stops being read — that is the measured drift risk.
* **Anti-rules are never merged away.** They are the entries that prevent a
  reader from "fixing" something correct, and they carry the highest cost when
  lost.
* **Every entry carries its evidence.** Which clause taught it, and whether it
  was MEASURED on a real module or INFERRED.

## Versioning

`REVIEW_LIST.md` header carries `v<N>` and the clause count it has absorbed.
`LIST_LOG.md` records, per fold: clause, lessons proposed, lessons ADDED,
lessons MERGED (into which entry), lessons REJECTED (with the reason). A
rejected lesson is a real datum — it usually means the agent restated an
existing entry, which tells us the list is working.

## Provisional rulings

`PROVISIONAL.md` holds every ruling made in the absence of an owner decision —
currently the ESTABLISHES-vs-narrowing contract question. Each entry states the
ruling, its grounds, **every clause it decided**, and what would change if the
owner ruled the other way. These are never folded into `REVIEW_LIST.md`; they
stay separate so the owner can overturn the class in one decision.

## ⭐ TURN-BASED REVIEW — owner's ruling 2026-08-16

**Above 10 entries the list is presented in TURNS, not all at once.** An agent
handed twenty checks applies none of them properly; that is the measured drift
risk the old soft cap was a blunt answer to.

* **≤ 10 entries** — one pass, all entries, as now.
* **> 10 entries** — the agent drafts SPAN-FIRST as always, then revises across
  turns of **at most 5 entries each**.

**Turns are grouped by LENS, never split arbitrarily.** Five unrelated checks
in one turn is the same overload in miniature. The standing grouping, which
grows with the list:

| turn | lens | seed entries |
|---|---|---|
| 1 | **Is the right content here at all?** | P2 bearer · P3 claims-vs-asserts · P6 outside the narrowing |
| 2 | **Is the logical form right?** | P4 disjunction · P5 scope both ways · P8 tautology |
| 3 | **Is the force right?** | P1 polarity · P7 defeasibility · P10 GOOD/BAD poles |
| 4 | **Hygiene and anti-rules** | P9 unused declarations · the three anti-rules |

⛔ **A TURN THAT CHANGES NOTHING IS THE EXPECTED OUTCOME, NOT A FAILED TURN.**
State this to the agent in those words. An agent that believes each turn must
justify itself will edit a correct module until it is wrong — over-editing is
the specific risk turn-based review introduces, and it is worse than the
overload it cures because it degrades modules that were already right.

**Anchoring, stated so it is not discovered later:** later turns see the draft
as revised by earlier ones, so a defect introduced in turn 1 is less likely to
be caught in turn 3 — the turns are looking for different things. Mitigation:
the FINAL turn re-runs stage 2 in full and re-reads the span enumeration from
the draft phase against the finished module. Not a cure; a bound.

**Per turn the agent reports, per entry:** what it looked for, what it found,
and what it changed — including "nothing", which must be explicit rather than
an omission. A silent entry is treated as unchecked at the checkpoint.

## ⭐ THE CHECKPOINT — every 5 clauses, owner's ruling 2026-08-16

Not a status update. A gate, with measurements, that can HALT the pass. The
coordinator runs all of it and reports; the owner decides whether to continue.

### A. Are the translations good?

1. **Stage-2, re-derived by the coordinator, not taken from the agent.** Every
   module through `schema.validate_all` + `checks.run_checks`. Any module with
   an error-severity finding is a process failure, not a clause failure.
2. **Coordinator reads TWO of the five against their spans, personally.** Chosen
   as the one with the most asserts and the one with the fewest — the two ends
   are where over- and under-assertion live. This is the only step that is not
   an agent grading an agent.
3. **Overlap clauses**: for any clause with a known reference verdict, does the
   independent pass converge, diverge, or find MORE? Divergence is a finding
   about one of the two, and which one is not assumed.

### B. Is the review list actually getting better?

The list is worth its APPLICATION, not its length. Four measurements from
`LIST_LOG.md`:

* **Novelty rate** — lessons ADDED ÷ lessons PROPOSED. **Falling is the signal
  we want**: it means the list has absorbed the recurring classes. Rising after
  clause 10 means we have not converged and the cap will bite.
* **Rejection reasons** — a lesson rejected as "restates P3" is evidence the
  list is working. A lesson rejected as "not mechanical" is evidence the agents
  are drifting toward description.
* **Application coverage** — does each agent report a finding for EVERY entry,
  including "nothing"? An agent silently skipping entries is the first sign of
  the drift the cap exists to prevent.
* **Rubber-stamping** — if an agent reports "nothing" on every entry, that is
  not application, it is a null. Check at least one such "nothing" against the
  module by hand.

### C. Halt conditions — state them, do not soften them

* Any module ships with an error-severity finding.
* Two consecutive agents report "nothing" on every list entry.
* The list exceeds 20 entries without a retirement.
* An agent resolves a `PROVISIONAL` question differently from the recorded
  ruling without saying so.
* The coordinator's own read of a module disagrees with the agent's notes on a
  point of fact.

Any of these halts the pass and goes to the owner. **A halt is a success of the
gate, not a failure of the run.**

## What the coordinator does NOT do

Does not edit a module. Does not resolve an agent's UNSURE. Does not adjudicate
a clause against the reference set mid-pass — that comparison happens once, at
the end of a wave, and the agents stay fenced out of `reference_set/`,
`redraw_adjudication/` and `spotcheck_semantic/` throughout.
