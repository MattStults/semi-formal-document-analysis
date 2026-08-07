# Brief — reviewing the model against the design

**You are a clean reviewer.** You did not write the design or the model. This brief runs when the
guard reports the design document changed and the model has not been re-reviewed.

## The question

**Does `model/pipeline.lp` still faithfully describe `resources/03_pipeline.md`?**

Not "is the design good." Not "is the model elegant." Only: does the model say what the document
says, and does it say nothing the document does not.

## ⭐ You are encouraged to decline

If the design document is unclear, or the model's facts are hard to trace back to it, **say so and
stop.** The correct output is:

> *"I cannot confidently review this. Here is specifically what is unclear: …"*

That is a **wanted result**, not a failure. A confident review of writing you did not follow is
worse than no review — it certifies something nobody checked. If the writing is the problem, fixing
the writing is the work, and you have found it.

Do not guess at intent. Do not fill a gap with something plausible.

## What to check, in order

**1. Invented facts — the highest-value check.** For every `check/3`, `catches/2`, `narrows/3`,
`seat/2`, `sees/2`, `forbidden/2`, `problem/3` and `claim/3` in `pipeline.lp`: **find the sentence
in the design that licenses it.** Quote it. If you cannot find one, the fact is invented.

⚠️ This has already happened twice. `check(coverage, ...)` and `check(cycle_beats, ...)` were both
asserted while the design says in plain words that no such check exists — and one of them disabled
the model's flagship rule on its own flagship example.

**2. Omissions — invisible to every rule, so only you can find them.** What does the design say
that the model does not record? Work through the document's problem table, its stage diagram, its
seat table and its invariants. Anything absent is something no constraint can ever fire on.

**3. Accounting.** Every check must carry either `implementation(C, Path)` or `todo(C, Why)`.
Neither means it was invented. ⚠️ `todo/2` is scaffolding for this stage; it should shrink over
time, not grow.

**4. Contradictions between the design and itself.** The document has known internal inconsistencies
— stage numbers used differently in the diagram and in prose is a live example. Report them; do not
resolve them.

**5. Then run it.**

```
python3 check.py            # the findings
python3 check.py --self-test
python3 guard.py --self-test
python3 -m pytest test_model.py -q
```

Report what fails and whether the failures are the model's or the design's.

## What to produce

- **Invented facts** — each with the search you did to license it
- **Omissions** — ranked by how much a rule could have done with them
- **Whether you could review this confidently at all**, and if not, exactly what blocked you
- **The run output**

Do not edit anything. Do not propose rewrites. Report with `file:line`.

## Standing context

This directory is a prototype that is **allowed to contradict the wider repository** (see
`../README.md`); `03_pipeline.md` is its source of truth. Do not report a divergence from repo
practice as a defect unless the design claims to follow that practice.

⚠️ The model has **no oracle**. A sibling model elsewhere in this repo is differentially tested
against executing code; this one describes a document, and both were written by the same person.
Everything in it is one unverified assertion until you check it. That is why this review exists.
