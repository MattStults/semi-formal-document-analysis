# Proposal — the non-convergence graveyard

**For review. Not implemented. To be folded into `resources/03_pipeline.md` once the agent
currently editing that file releases it.**

---

## The problem this solves, with today's evidence

Two clauses failed in the first repair-enabled run. Both failed for **the same reason**: the model
wrote a whole rule into a slot that holds a single term. I found that by opening two transcripts and
reading them.

⇒ **That does not scale to 593 clauses**, and the signal it carries is not about those two clauses —
it is about the **prompt**. One shared cause, visible only by comparing failures against each other.

The design already says *"if repair does not converge under this split, the split is the first
suspect."* Nothing operationalises looking.

## The proposal

**When repair exhausts its budget, the whole transcript is written to a graveyard that must be
cleared by hand, and clearing requires a written diagnosis.**

    repair_graveyard/
      m0091-20260807-155327/
        transcript.json      every turn, including the final assistant answer
        findings.json        findings per attempt, so convergence is visible
        module.json          the last object it produced, valid or not
        VERDICT.md           ⛔ absent until an agent writes one. Blocks clearing.

⭐ **It fires on ANY failure to converge in the pipeline**, not only stage 2 — stages 3, 4 and the
stage-8 link step all have repair edges, and a prompt defect at any of them has the same shape.

### Why it must be manual and blocking

A report nobody reads is the failure this directory keeps re-learning: the `no %% provides:` warning
in `link.py` fired on every module until it became invisible. The staleness guard works precisely
because it is red and blocks. The graveyard should behave the same way — **a full graveyard halts a
run rather than overflowing**, because a hundred uninspected non-convergences is not a corpus, it is
an unexamined prompt defect repeated a hundred times.

## ⭐ Sampling successes, which I think is the stronger half of the idea

Waiting for outright failures throws away most of the signal — and today proves it.

**m0037 converged, was flagged `shrank`, and was garbage.** It cleared its finding by deleting the
offending entry; the module went to zero asserts, zero defines, zero ontology, and the run recorded
it as a success. A graveyard of failures only would never have contained it.

⇒ Sample, and **not uniformly**. The rate should track how much a case is likely to teach:

| what | rate | why |
|---|---|---|
| failed to converge | **100%** | the case the graveyard exists for |
| converged but **flagged** (`shrank`, `declaration-edit`) | **100%** | m0037. It succeeded and was wrong |
| converged on the **last available attempt** | **100%** | one more defect and it would have failed; the budget is hiding it |
| converged after any repair | a rate | the ordinary signal |
| ⭐ succeeded **first try, unflagged** | a LOW rate | see below |

⚠️ **The last row is the one to argue with, and I think it earns its place.** A graveyard containing
only trouble makes every diagnosis read as *"the prompt is broken."* A diagnosing agent needs cases
where the prompt WORKED to tell a real defect from an unlucky clause. A control group is cheap; its
absence is how a diagnosis becomes a rationalisation.

## ⛔ Four ways this goes wrong

**1. It fills up and gets bulk-cleared.** The single likeliest failure. ⇒ Clearing is per entry and
requires a `VERDICT.md`; there is no clear-all. A cap halts the pipeline rather than dropping
entries, because silently dropping the hundredth is how the first ninety-nine stop mattering.

**2. ⭐ Fitting the prompt to the graveyard.** If the prompt is tuned until non-convergence stops,
the prompt has been optimised against our own measurement — which is precisely the shape this
project has a standing ruling against (open question 3, *"a search whose objective is a model
judgement"*). ⇒ **A held-out clause set, never used for diagnosis**, and a prompt change is accepted
only if it holds there. Without this the graveyard becomes a fitting loop with extra steps.

**3. It becomes a permanent store of answer keys.** Today's transcripts carry only stage-2 findings
and are safe. Stage 3's findings carry must-forbid / must-permit labels; stage 4's can name an
expected answer. ⇒ **The graveyard inherits the `origin` filter**, or a diagnosing agent reads
verdicts out of it and writes them back into the prompt — the leak the filter exists to prevent,
taking the long way round.

**4. The prompt is a watched transcription of the design.** An agent that edits it must go through
the staleness guard, or we get prompt drift with no review — the failure that cost the most today.

## ⭐ Who diagnoses — the model that failed, as a PROPOSER

The expensive reading of this proposal is that every entry needs a strong agent. It does not, for
most entries.

**The failing model is already holding the whole context** — the clause, its own attempts, and the
findings against them. Asking it *"what change to your instructions would have prevented this?"*
costs one cheap call and is the natural continuation of the transcript.

⚠️ **It is unreliable as a source of truth about its own failure, and we have two recorded cases:**

- `m0217` wrote `political_topic(C, _)` and annotated it *"The anonymous variable is avoided by
  using a named variable in a helper rule."* It self-reported compliance while violating.
- Earlier, a model found the concepts correctly by reading and then stated a rule that could not
  possibly have produced its own examples.

⇒ **So it is a proposer, never a diagnosis.** That is this project's existing rule — *"a model is a
proposer, never the source of a deterministic step, and anything it returns must be verified
mechanically against clauses it did not see."* A wrong hypothesis costs one held-out run; a right
one costs nothing extra.

### The loop

1. On entry, ask the failing model for a **prompt-change hypothesis**. Cheap, same transcript.
2. **Aggregate across entries.** One agent reading twenty hypotheses finds the shared cause that
   twenty agents reading one each cannot. Today's two failures had one cause between them.
3. Each surviving cluster becomes **one testable hypothesis**: change the prompt, run **held-out
   clauses**, measure.
4. Keep what survives. Clear those entries automatically, with the evidence attached.

⇒ **For a shared, validated cause, clearing is part of the pipeline.** The expensive path is only
for the residue.

### ⛔ This is a search over prompt space, and it must be visible

Generating hypotheses from the graveyard, testing them, and keeping the winners **is coordinate
descent on our own measurement** — the shape a standing ruling already forbids (open question 3).
Held-out clauses are not sufficient on their own, because you can keep searching until something
clears the held-out set too.

⇒ **Log every hypothesis tried, not only the ones kept**, each with its held-out result. A prompt
change found on the first attempt and one found on the thirtieth are different claims, and only the
count distinguishes them. The log is the artifact that makes the search arguable instead of
invisible.

## Clearing: pipeline for the common case, a skill for the residue

| | |
|---|---|
| shared cause, hypothesis validated held-out | ⭐ **pipeline** — automatic, logged, cheap |
| no hypothesis survives, or causes do not cluster | **a skill**, invoked by an agent |
| the graveyard reaches its cap | ⭐ **blocks the pipeline** — see below |

⭐ **The skill's FIRST step is to read `DEBUGGING_TIPS.md`, before forming any hypothesis.** That
file is the accumulated record of what has already been worked out the hard way, and its first
entry is the one that would otherwise be missed every time: *check whether the failing shape is
DEMONSTRATED by a worked example, not merely stated in prose.* The dominant stage-2 failure —
59 occurrences in 36 first attempts — was a rule the prompt forbade explicitly and never once
showed the right form of. Adding one worked example took it to zero on held-out clauses. An
agent that starts from "how do I word this rule better" will not find that.

⭐ **And the skill MAINTAINS that file.** Any entry whose diagnosis took real work adds a tip
before it adds a fix — including the false path taken first, which is the expensive part and
the part a conclusion-only note throws away. A cleared entry whose diagnosis was hard and left
no tip is an incomplete clearing.

**The rest of the tripwires**, because they are what a diagnosing agent will otherwise miss. It
must check, every time:

- **Is this fitting?** How many hypotheses were tried for this cluster; what the held-out result was.
- **Does the fix touch a WATCHED transcription?** The prompt files are transcriptions of the design;
  editing one without re-review is the failure that cost the most in this project's history.
- **Would it disclose an answer key?** A stage-3 or stage-4 finding carries expected verdicts. It
  must not reach the prompt through a diagnosis.
- **Is the cause the model, the prompt, the schema, or the design?** Four different owners. The
  commonest error is fixing the prompt for a schema defect, because the prompt is easiest to edit.

⭐ **Auto-triggering: make it BLOCK, not notify.** The staleness guard works because it is red and
stops a commit. The `no %% provides:` warning failed because it printed on every run and became
invisible. A graveyard at its cap should halt the pipeline — a hundred uninspected non-convergences
is not a corpus, it is one prompt defect repeated a hundred times.

## What clearing requires

A `VERDICT.md` naming:

1. **The cause**, and whether it is shared with other entries — the shared cause is the finding, not
   the individual failure.
2. **Where the fix belongs**: prompt, schema, design, or "the model cannot do this".
3. **The held-out result** — the change tried against clauses not in the graveyard.
4. ⭐ **What would have caught this earlier**, which is how the checks improve rather than the prompt
   only.

## Cost

Writing entries: free. Diagnosis: one agent per batch, and the batching is the point — one agent
reading twenty transcripts finds a shared cause that twenty agents reading one each cannot.

⚠️ **Sampling successes costs disk and attention, not money** — the calls were already made. The
real cost is that a graveyard nobody empties is worse than none, so the sample rate has to be set
against how fast entries can actually be diagnosed, not against how much data would be nice.

## What I am least sure of

Whether **"failed to converge"** is the right trigger. Today's two failures were both caught by
stage 2 — cheap, deterministic, and the transcript is short. A stage-4 non-convergence would carry
four review seats' worth of material and be far more expensive to diagnose. It may be that the
graveyard wants a per-stage budget rather than one global rule, but I have no evidence either way
and would rather ship the simple version and measure.
