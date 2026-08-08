# Brief — reviewing a transcription against the design

⚠️ **AMENDED 2026-08-07.** This brief was written for `model/pipeline.lp`, an ASP model of the
design that has since been **retired** — see `RETIRED.md`. Its subject is now the file the guard
reported STALE: a **transcription** of the design (currently the stage-1 prompt files and
`schema.py`). Sections 1, 2 and 4 below transfer directly; section 3 and the `check.py` commands in
section 5 belonged to the retired model and are struck through where they no longer apply.

**You are a clean reviewer.** You did not write the design or the file under review. This brief runs
when the guard reports a watched file changed and has not been re-reviewed.

## The question

**Does the file under review still faithfully say what `resources/03_pipeline.md` says?**

Not "is the design good." Not "is the file elegant." Only: does it say what the document says, and
does it say nothing the document does not.

⭐ **The direction that matters most.** The guard fires when *either* side moved. If the DESIGN
moved, the transcription is now describing a design that no longer exists, and nobody edited it —
that is the failure this whole apparatus exists for, and it is invisible to every test the file has.

## ⭐ You are encouraged to decline

If the design document is unclear, or the model's facts are hard to trace back to it, **say so and
stop.** The correct output is:

> *"I cannot confidently review this. Here is specifically what is unclear: …"*

That is a **wanted result**, not a failure. A confident review of writing you did not follow is
worse than no review — it certifies something nobody checked. If the writing is the problem, fixing
the writing is the work, and you have found it.

Do not guess at intent. Do not fill a gap with something plausible.

## What to check, in order

**1. Invented claims — the highest-value check.** For every rule, failure mode, worked example,
required field and licence value the file states: **find the sentence in the design that licenses
it.** Quote it. If you cannot find one, it is invented.

⚠️ This has already happened twice. `check(coverage, ...)` and `check(cycle_beats, ...)` were both
asserted while the design says in plain words that no such check exists — and one of them disabled
the model's flagship rule on its own flagship example.

**2. Omissions — invisible to every test, so only you can find them.** What does the design say that
the file does not carry? Work through the document's problem table, its stage diagram, its seat
table and its invariants. A failure mode the design lists and the prompt omits is a failure nothing
will ever warn about.

**3.** ~~Accounting: every check must carry `implementation(C, Path)` or `todo(C, Why)`.~~ Retired
with `pipeline.lp`.

**4. Contradictions between the design and itself.** The document has known internal inconsistencies
— stage numbers used differently in the diagram and in prose is a live example. Report them; do not
resolve them.

**5. Then run it.**

```
python3 guard.py            # what is stale, and why each file is watched
python3 guard.py --self-test
python3 -m pytest test_model.py -q
```

Report what fails and whether the failures are the file's or the design's.

**6. Then, and only if you actually read it**, the person who commissioned the review accepts each
file by name: `python3 guard.py --accept <path>`. Accepting a file you skimmed is the failure this
guard exists to prevent, performed by hand.

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

⚠️ A transcription has **no oracle**. Nothing mechanical connects the prompt or the schema back to
the design; both sides were written by the same person, and the file passes all its own tests
whichever design it describes. Everything in it is one unverified assertion until you check it. That
is why this review exists — and it is the same argument that retired `pipeline.lp` (`RETIRED.md`),
which had the identical problem and, unlike a prompt, was not load-bearing for anything that runs.
