# DRAFT — Post 1: What I'm trying to do, and why the goal changed

STATUS: campaign draft, not for publication. Numbers need artifact pointers
attached before publish; the "human panelist" comparison figure is NOT to be
used until sourced (campaign flag, 2026-08-21).

---

Model specs are the closest thing AI labs have to constitutions. They state
what a model should do when a user asks for something dangerous, how it
should weigh competing instructions, where it must refuse and where it must
not refuse too much. And then a very ordinary question arises in practice —
during an evaluation, a red-team, an incident review, a regulatory
conversation:

*Which passages of this document actually bear on behaviour X?*

Today that question is answered in one of two ways. Someone reads the
document carefully — slow, expert-hours, and their answer is an opinion
without a receipt. Or you ask a frontier model — fast, but the answer is
different next time, you cannot audit why it was given, and you have just
made the thing you are trying to evaluate into the judge of its own
governing document.

This project builds a third option. Read the document once, into a
semi-formal layer: clauses become typed objects — acts with deontic force
(the assistant *must refuse*, *may disclose*, *should prefer*), the
qualities those acts govern, the parties they protect, the conditions under
which they hold. Then the question "which passages bear on behaviour X?"
becomes a structural match between the behaviour's module and the
document's objects. No model is called at query time. The answer is
instant, runs offline, and every hit carries the span of source text that
licenses it.

That is the product. But the more important thing I learned is about the
goal.

## The goal I started with

The obvious way to know whether such a tool works is to compare it with a
panel of frontier models judging the same passages, and try to match them.
I built that comparison — a panel bench, behaviour definitions, a rubric,
blind adjudication — and ran the tool against it.

The honest numbers: the tool did not match the panel. In the project's
first era it reached a correlation of +0.31 against a frontier-panel bar of
+0.555, on the development behaviours, in the true passage universe — about
three times better than bag-of-words, and clearly short of the judges.

You can spend a long time trying to close a gap like that. What stopped me
was asking what closing it would actually mean.

## The restatement

The panel is not ground truth. It is three large models with their own
blind spots, and an independent expert review of the panel product found
that it over-flags and flattens salience. A tool that learns to match the
panel has not learned to read the document; it has learned the panel. And a
tool fitted to judges inherits exactly the thing you wanted to escape —
unauditable judgment, now laundered through a score.

So the goal was restated, and the restatement is the project's real thesis:

**The target is a logically consistent, auditable reading of the document —
not agreement with any judge.** Assumptions are explicit and toggleable.
Where the tool and the panel disagree, the disagreement is surfaced as
output, with both sides' reasons attached, because that disagreement is
information: either the tool misread the document, or the panel did, and a
reading you can audit lets you find out which.

Panel agreement did not disappear — it changed jobs. It is now a
calibration instrument: the thing that tells you where your reading and the
collective judgment diverge, so you can adjudicate the divergence against
the document itself, with neither side allowed to be truth by fiat.

## What the project became

Once the goal is "an auditable reading", the interesting engineering moves.
Every answer the tool gives has to be checkable, so the machinery around it
became the point:

- Pre-registered expectations before measurement, so a result cannot be
  fitted after the fact.
- Blind adjudication seats: judgments made against the document without
  knowing what the tool predicted.
- A separability census that distinguishes disagreements the instrument
  could in principle resolve from ones that are terminal at its current
  vocabulary — so effort goes where it can do something.
- Anti-cheat scans that have caught real planted leaks and real agent
  mistakes, because a measurement you can game is worse than none.

And the negative results stayed in the record, because they are the record.
An evaluation universe that was silently truncated. An error-rate "win"
that reversed under a different metric. A supervised score that proved
separability rather than semantics. Every headline in the first era was
overturned at least once — always by asking what an existing number
actually measures.

## What this post does not claim

It does not claim the tool beats frontier panels — on the old bar it does
not. It does not claim the current design is final — it is where the
defects have pushed it, and the defects are not done. It does not claim a
certified result yet: the current arc is running the certification and
generalization measurements as I write this, pre-registered, and the next
post will report whatever they find — which, if the process is honest,
might be a failure.

What it claims is smaller and, I think, more durable: that "which passages
of this document bear on this behaviour?" deserves an instrument-grade
answer — instant, offline, auditable — and that building one teaches you
more about what documents like these actually say than any single score
ever could.

---

END DRAFT.

Open items before publish:
1. Attach artifact pointers to every number (README.md results section;
   RELEVANCE_QUALITY_READ.md for the +0.108 control and the noise-floor
   caveat).
2. Decide how much of the "current arc" paragraph survives — depends on
   post 3's results.
3. Tone check with Matt: first-person voice, length (~1,050 words), and
   whether the goal-restatement framing lands the way the lived decision
   did.
