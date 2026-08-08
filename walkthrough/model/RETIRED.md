# RETIRED — the formal model of the design, 2026-08-07

**If you are here because this directory looks half-empty: it is, on purpose. Read this
before re-inventing what was removed.**

## What was here

| file | what it did |
|---|---|
| `pipeline.lp` | ~12 KB of hand-authored ASP facts modelling `resources/03_pipeline.md` — its problems, stages, checks, seats, claims, and which check `catches` which problem |
| `rules.lp` | integrity constraints over those facts: `uncaught_problem`, `contamination`, `check_no_stage`, `claim_n_is_one`, `only_narrowed`, `silent_needs_determinism`, `specified_not_built`, `unaccounted_check`, `no_coverage_rule` |
| `check.py` | ran the two through clingo, parsed findings, classified them CONTRADICTION / GAP / DISCLOSURE, and mutation-tested that each rule fired on a model broken in its own way |
| `accepted.json` | waivers against those findings, each requiring date / who / why |
| the findings half of `guard.py` | ran `check.solve()` and blocked on any unwaived finding |

The design record it produced is kept: `REVIEW_FINDINGS.md` and `REVIEW_BRIEF.md` stay in
this directory. Retiring the machine does not retract what was learned by building it.

## Why it went

A clean review assessed it against one day of real failures, and the arithmetic was not
close:

- **Findings the model produced that day: 0.** Findings clean human/model reviewers
  produced over the same material: ~20.
- Of five conformance failures assessed, **two** were catchable only with rules that did
  not exist; **three** were structurally out of reach — they happened in *plans and
  prompts*, and the model described neither. It modelled the design document, and the
  design document was not where things went wrong.
- It **asserted one fact that contradicted the design** — `catches(normalise, p9)` —
  which suppressed a real disclosure until someone deleted it by hand. That is the
  decisive item. An unmaintained model is not merely unhelpful; it manufactures
  confidence, and this one already had.

The general form: the model had **no oracle**. `REVIEW_BRIEF.md` says so in its own last
paragraph — a sibling model elsewhere in this repo is differentially tested against
executing code, but this one described a document, and both were written by the same
person. Every fact in it was one unverified assertion. The review that was supposed to
catch that is expensive and ran twice.

## What was kept, and why it is the opposite case

**The staleness guard.** It compares a sha of watched files against a recorded review
point and reports ⛔ STALE when the design moves. On 2026-08-07 it was RIGHT and RED for
two hours while work proceeded from a stale reading of the design — the single most
expensive failure of that day — and nobody looked, because `hooks/pre-commit` had never
been installed.

The guard needs no oracle. It does not claim to know anything about the design; it claims
only that **nobody has asserted this file still matches, since the design changed**. That
claim is mechanically true or mechanically false, which is exactly what the assertions
were not.

⭐ The retirement came with a widening, and the widening is the actual finding: the watch
list now covers `paper_pipeline/phase_1/prompt/*.md` and `paper_pipeline/phase_1/schema.py`
— the files *transcribed* from the design, which is where the three out-of-reach failures
happened. It is data in `watch.json`, so widening it further is an edit to a list.

## ⇒ What would justify bringing it back

Not "we have time now". Specifically:

1. **An oracle.** Some way for a fact like `catches(link, p2)` to be checked against
   something other than the person who wrote it — mutation testing of the real check, a
   second independent transcription, or the design document carrying machine-readable
   markers that `pipeline.lp` is generated from rather than transcribed alongside.
   Without this, it is one person's assertions checked against the same person's
   assertions, and the `catches(normalise, p9)` failure recurs by construction.
2. **The failures being in scope.** If the pipeline's failures start landing in the
   *design document's* structure — a problem with no check, a seat reaching forbidden
   material — rather than in prompts, plans and transcriptions, the model's rules become
   relevant. Today they are not: 3 of 5 were out of reach.
3. **A named owner and a maintenance record.** The mechanism that killed it is that the
   model went stale while looking healthy. A revival that has no answer for "who updates
   this and how do we know they did" is the same artifact again.

⚠️ **Do not revive it by writing `pipeline.lp` back from memory.** If items 1–3 hold,
start from `REVIEW_FINDINGS.md` — it records what the model got wrong and how, which is
worth more than the model was.

## Salvage worth remembering, if you do rebuild

Three mechanisms in the retired code were good, independent of what they were checking,
and are worth copying rather than re-deriving:

- **The parse canary.** `check.py` raised rather than reporting clean when its output
  parser matched zero labels. It existed because a report-format change once made the
  guard report GREEN on ten open gaps. Any parser between a checker and its verdict needs
  one.
- **Delta-based mutation testing.** The self-test compared findings *introduced* by a
  mutation against a baseline, because two earlier cases had "passed" on findings that
  were already firing for unrelated reasons — the mutation changed nothing and the test
  proved nothing.
- **Waivers requiring date / who / why**, with a `review_by`, and an invalid waiver not
  waiving. The 2026-08-07 ruling behind it stands and generalises: *everything blocks; a
  waiver is the only route to non-blocking, because it is the only one that records who
  accepted it.* (Retired here only because there are no findings left to waive.)

The full waiver texts, which are substantive statements about what is and is not
mechanically checkable in this pipeline, are preserved in git history at
`walkthrough/model/accepted.json`.
