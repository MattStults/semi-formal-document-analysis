# Decisions waiting on Matt

Written 2026-08-05, kept current as things land. Each item is self-contained: what the
decision is, a concrete example, the options, what each costs, and what I'd recommend.
Answer any of them in any order — a sentence each is plenty, and I'll record the ruling with
its grounds in the repo.

**Nothing here blocks me from working.** The autonomous queue is deep and running. These are
the items where guessing wrong would waste real work or spend real money.

---

## A five-line glossary, so the rest reads plainly

* **Clause** — one numbered passage of the spec (e.g. m0276 is the self-harm paragraph).
* **Atom** — a short named fact tagged onto a clause, like `imminent_bodily_harm`. The tool
  matches a question against atoms to decide which clauses are relevant.
* **Flip** — a clause that changes status (relevant ↔ not relevant) when we change something.
  Flips are the unit of evidence: every one gets judged against the document.
* **Cycle** — the ceremony around a change: freeze a prediction, make the change, measure the
  flips, judge each one, then keep or revert. Six have run; five kept, one reverted.
* **The panel** — frontier models scoring the same question. It's the bar we're measured
  against, and it is itself imperfect.

---

## Decision 1 — The "overlay" cycle (S5) changes nothing measurable. Run it, fix it, or skip it?

**What it was supposed to do.** The tool knows a few concepts are special cases of others —
"psychological manipulation" and "targeted political manipulation" are both kinds of
"manipulation". That linkage was built, reviewed, and then switched **off** pending a cycle
to turn it on. S5 is that cycle, and every future linkage cycle waits behind it.

**What we found.** An independent reviewer built it and measured it: **turning it on changes
no clause's status at all.** Eight clauses get extra credit, but all eight were already
counted as relevant. The nearest clause that isn't relevant misses its threshold by 0.043 —
and even multiplying the credit by 2.5× doesn't move it.

**Why that matters more than "it does nothing".** The cycle's own rule is that we keep or
revert *based on the judged flips*. With zero flips there is nothing to judge, so the cycle
would pass its checks, close as a success, and have proven nothing — while unlocking every
later linkage cycle on the strength of that non-result.

**Options**

| | what happens | cost |
|---|---|---|
| **A. Skip S5 for now** | Leave the linkage off; revisit if a later cycle needs it | Free. Later linkage work stays blocked |
| **B. Run it as a deliberate no-op** | Close it honestly with "0 flips" pre-registered, disclosing that we measured before predicting | ~half a day of ceremony for no measured knowledge |
| **C. Fix the design first (recommended)** | Add a "can this even move anything?" screen before a linkage consumes a cycle, and have S5 pre-register the *mechanism* facts it can actually be wrong about | ~a day of design revision, then it's a cycle worth running |

**My recommendation: C, but at low priority.** The valuable part isn't S5 — it's the screen,
which stops future linkage cycles burning time on changes that cannot move anything. Note
one thing already spent: by measuring S5 before opening it, we used up its ability to be a
blind prediction. That can't be restored, and any S5 record must say so.

---

## Decision 2 — The vocabulary cycle (S6) has a safety gate that doesn't work. How far do we go?

**What it does.** For 26 clauses, the tool misses relevance because no atom describes the
concept. S6 adds atoms.

**The risk it was designed against.** Adding vocabulary is the most direct way to cheat: we
know which cases the panel says we're missing, so we could invent atoms until those cases
pass — which measures nothing except our ability to fit the answer key. The design's defence
is a split: only add atoms where the concept exists **nowhere**; where it exists but the
question can't reach it, fix the *question*, not the vocabulary.

**What the review found.** Two problems.

1. **Nothing enforces the split.** The seat proposing atoms is deliberately blind to which
   concepts the questions already use — so it *cannot* apply the rule, and no check computes
   it either. The only thing applying it is a paragraph of prose.
2. **Recomputing it flips the answer for 15 of the 26 clauses.** Example: clause m0528 is a
   *harm* case, and the atoms it would need — `neutral_refusal`, `judgmental_refusal` — are
   already in the caution question's vocabulary. Adding them again is precisely the duplicate
   the design forbids. Meanwhile six clauses the design books as "already covered" carry no
   relevant atom anywhere, and are the real cases for new vocabulary.

There's a third finding worth knowing: the design accounts for how new atoms ripple through
the scoring, but **misses the largest channel** — atom names and their descriptions are part
of the text the tool searches, and that channel is the heaviest in the scorer. A seat writing
a free-text description is writing directly into it, unreviewed.

**Options**

| | what happens | cost |
|---|---|---|
| **A. Do the cheap half only** | Fix the *questions* for the ~14 clauses whose concepts already exist. No new vocabulary, no fitting risk | Small. Already in progress: I'm having the split computed mechanically now |
| **B. A then a reduced S6** | After A, add vocabulary only for whatever genuinely remains | Moderate; needs the design's four blocking findings fixed first |
| **C. Full S6 as designed** | — | Not advisable: its central safety gate provably doesn't work |
| **D. Drop vocabulary work entirely** | Accept these 26 as permanent misses | Free, and honest, if the strategic read says the ladder isn't worth finishing |

**My recommendation: A now, decide B later** — after you've seen the quality read (Decision
6). A is nearly free and is the negative control: if fixing the questions alone resolves most
of the 26, the vocabulary work was never needed.

---

## Decision 3 — The "implied effects" layer: four rulings, and it blocks the biggest cycle

**What it is.** Sometimes a clause protects someone it never names. The spec says the model
should de-escalate a user's radicalization — the people protected are *third parties*, but
the text never says so. Our rule is that the machine may never infer a party; a human
approves such a judgement once, it's logged with who approved it and when, and the tool then
reads it as a fact. This layer is that mechanism.

**Why it's urgent.** The largest pending cycle (S3b) cannot start until this layer passes
review, because S3b depends on it to hold that one case.

**The four decisions**, in plain terms — full options and recommendations in
`semi-formal-experiment/IMPLIED_EFFECTS_DECISIONS.md`:

1. **Where an approved judgement takes effect.** Two plausible wirings. They differ on one
   case that matters: under one of them, approving a judgement about the *radicalization*
   clause would also resurface the *self-harm* clause we deliberately suppress. Recommended
   option avoids that.
2. **How entries are keyed to the text**, so a later edit can't silently orphan them.
3. **Who is allowed to propose an entry.** Approval is already fenced against seeing the
   answer key; *proposal* is not, and that's where fitting actually happens. Complication we
   should be honest about: the flagship entry (the radicalization case) was itself found by
   looking at a result.
4. **What must never change.** Every approved entry has the power to bring back a suppressed
   clause. Recommended: pin the two must-stay-suppressed cases as tests, and switch off the
   "approve a whole class at once" shortcut, which analysis shows cannot distinguish the case
   we want from the case we must not touch.

**Scale, which the design never established:** roughly **5–15 entries**, from a candidate
pool of 41 clauses. That means one-at-a-time human approval is affordable and the risky
bulk-approval path isn't needed.

---

## Decision 4 — Money

**Where we are.** Hard ceiling $8.50, about $2.06 logged, plus a known gap where six runs
were billed but never recorded.

**What wants spending.** The S3b build needs a cheap model to read ~439 items, a frontier
model to check it on a sample, and a human-or-frontier review of that sample. Token cost is
small — my estimate is well under $1. **The real cost is your time**: roughly 80–100 rows to
review personally, plus every disagreement between the two models.

**The decision.** Two parts:

* **Am I authorized to spend at all, and up to what?** I've spent nothing and will spend
  nothing without this.
* **When?** My recommendation: **not until the design is final.** If the backfill runs and
  then the design changes, we pay twice — and the expensive half is your review time, not
  tokens. Concretely, that means after Decision 3 and after S3b's own review.

---

## Decision 5 — A defect that lets S3b pass its test without working

Found while preparing Decision 3, and it needs a ruling from whoever owns S3b.

S3b's proof that it works is: three specific clauses must come back, *for the right reason*.
But an approved implied-effects entry on those same clauses would produce **exactly the same
signature** — so the test could pass with the actual mechanism doing nothing.

**Fix, recommended:** make the two cases mechanically distinguishable — a separate marker for
"restored because a human approved an implied effect" versus "restored because the mechanism
worked" — and require the mechanism's own artifact to be present for the test to count.

Cheap to fix now, expensive later: if it's not fixed, a green result on S3b will not mean
what the record says it means.

---

## Decision 6 — Fund, pivot, or hand it to frontier models

**Still open — but it is now a decision with a memo attached rather than a question needing
research.** Read **`PROJECT_ASSESSMENT.md`** (repo root): written for a reader with no
background, it lays out the problem, the approach, where quality actually is, how much more is
available, *why* rules run out, and a recommendation across all three options.

**The one-line version:** stop funding accuracy work on the rule engine; fund the auditability
machinery (model-agnostic — it works wrapped around a frontier model) and the ranked-audit axis
a human expert endorsed; run two cheap decisive experiments first. If the only goal is quality
with little human effort, frontier models are better today and nothing in our plan closes that.

**The two cheap experiments, neither of which needs your decision to be worth running:** the
recalibrated "who was wrong" pass (the only thing that could legitimately move the bar), and
the transfer test on held-out behaviours. ⚠️ The related salience check is *not* free — its
only usable anchor sits on a held-out behaviour, so running it spends a one-shot resource.

The supporting measurement is below and in `semi-formal-experiment/RELEVANCE_QUALITY_READ.md`.

### Where the tool stands

**+0.309** against a frontier-panel bar of **+0.556**. (The scale runs −1 to +1; 0 is
chance. So the tool is real, and it is not close to the panel.)

### The finding that decides it

**The last six completed cycles moved that number by +0.0003 in total.** The project's own
measured noise floor is 0.032–0.037 — about **100× larger than everything six cycles
achieved**. Statistically, the executed fix ladder has produced *nothing*.

The one genuine gain in the whole record, **+0.072**, came from re-selecting which
question-side concepts the tool searches with — an *instrument* change, made before the
ladder started. Not a mechanism fix.

### What the remaining ladder can deliver, being generous

Assuming every remaining cycle lands **perfectly** with zero side effects — which never
happens — the whole remaining ladder closes **42%** of the gap, reaching about +0.41. The
honest estimate is **15–28%**, reaching +0.35 to +0.38.

And the generous number rests on assumptions we have already refuted:

* **S5 measures literally zero effect** (Decision 1).
* **S6 supplies 65% of that optimistic gain**, and its own review disqualifies 14–15 of its
  26 targets. Priced with even modest side effects — three new false positives per case
  recovered — S6 delivers *less than nothing*.
* **S3b** reaches 79 of its 155 cases; oracle best case **+0.010**, a third of the noise
  floor.
* **The threshold class — 20% of all disagreements — has no owner by design**, correctly:
  consuming those would be fitting to the answer key, which the whole method forbids.

### Two structural findings that outrank the arithmetic

1. **43% of the errors being measured were never catalogued.** The disagreement census covers
   256 of 447 actual disagreement cases. Every planned fix aims at the 57% that is catalogued.
   Even a perfect ladder leaves the largest uncatalogued block untouched.
2. **We cannot currently say how much of the gap is the panel's fault.** The census has a
   field marking "the tool is wrong" vs "the panel is arguably wrong" — and it turns out to be
   perfectly segregated by *which run produced it* (one behaviour: 129 cases all "tool wrong";
   another: 41 all "panel wrong"). Zero mixing across 294 judgments is a per-run stance, not
   per-case judgment. Taken at face value it would say **more than half the gap is panel
   error** — but it cannot be taken at face value.

### The recommendation

**Stop treating +0.556 as the objective.** Concretely:

* **Don't spend the S3b budget.** Best case is a third of the noise floor. Costed honestly it
  cannot be falsified.
* **Run one cheap thing first:** a recalibrated, cross-behaviour pass over that segregated
  field. It is the only thing that could legitimately move the bar, and it costs a seat run.
  ⚠️ The related "salience" check is **not** free: its only usable anchor sits on one of the
  six held-out behaviours, so running it spends part of a resource that can be used once.
  That's your call, not a free follow-up.
* **Go to the checkpoint and the generalization test sooner.** "Does the error pattern
  transfer to six never-consulted behaviours" is answerable now on a frozen pipeline, is the
  question you were actually asking, and is not improved by first spending three cycles to
  move the score by 0.04.
* **Rewrite the headline claim.** "+0.31 against +0.556" invites the wrong comparison. The
  defensible claim: an offline, auditable, label-free tool at **2.9× the bag-of-words
  baseline**, with a citable source span for every answer, on a use case a human expert
  endorsed — first-pass auditing — *whose own quality axis has never been measured*.

**Correction in the tool's favour:** the published baseline comparison (+0.19) is wrong. It's
a 9-behaviour number sitting in a 3-behaviour table. The real baseline is +0.108, so the lift
is **2.9×, not 1.6×**.

### What I need from you

Not a full pivot decision — just direction: **keep grinding the ladder, or stop and write up
what we have while running the two cheap high-information checks?** My recommendation is the
latter. The honest finding here looks like it's about the method and the instruments, not the
score — and that is a more interesting result than a scorer that got to +0.38.

---

## Decision 8 — Two version-threading gaps that affect the checkpoint census

Found while fixing a reported bug (which is fixed: the join's refusal/restriction facts were
conditioned on *who computed the joins* rather than on which join version was declared, so a
caller that precomputes them — exactly the checkpoint census's shape — silently lost them).

Two adjacent items need a ruling rather than a unilateral widening of that fix:

1. **`cell_evaluate` cannot select the new join at all** — it has no version parameter and
   hard-defaults to the old one. Any checkpoint caller routing through it would silently
   measure and *report* the old join. Same class of defect, different function.
2. **The restriction fact never reaches the caller.** The design calls it "a fact the caller
   must see"; today it is available only by calling a second function directly.

**Impact if unfixed:** the checkpoint census could record a configuration it did not actually
run. **Cost to fix:** small, but (1) widens a diff and (2) changes an output shape, so both
want a decision rather than an agent's judgement.

**Recommendation:** fix (1) before any checkpoint run — it is a correctness issue in the
measurement's own self-description. Defer (2) unless the checkpoint needs per-passage
restriction, in which case do both together.

---

## Already decided — recorded, not waiting

* **How much autonomy I have (was Decision 7), answered 2026-08-05.** Free to open and run
  cycles **up to the measurement step**, subject to three standing constraints: don't go
  through one-way doors; don't make decisions that are expensive to recover from, especially
  ones that could subtly contaminate data; don't make decisions that can't easily be validated
  after the fact. I still spend nothing, sign no keep/revert decision, and merge no
  scoring-path code until its review passes.

* **Which atoms get an affected-party label** — the 439-item list. Two alternatives rejected
  by name with grounds.
* **Not extending it to a further class of atoms** — measured yield was ~2 cases.
* **Run S4 before S3b.**
* **Retire the one un-replayable historical snapshot** rather than pretend it reproduces.
* **Rename the field** to `affected_parties`, because the mechanism was never harm-only.
* **Build the shared version-dispatch machinery first**, so future changes are a registry
  entry rather than another hand-written branch.
