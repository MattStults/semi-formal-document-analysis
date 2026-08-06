# Is this worth continuing to fund?

A decision memo for someone with no prior exposure to this project. Written 2026-08-05.
Every number here is measured and reproducible; sources are named at the end.

---

## The short version

We built a tool that answers "which passages of this policy document bear on behaviour X?"
without calling a model at query time. It works — it captures **about 45% of the useful signal**
between naive keyword matching and a panel of frontier models — and it produces something
frontier models don't: a citable source span for every answer, offline, instantly, reproducibly.

But **the last six engineering cycles improved its accuracy by an amount 100× smaller than the
measurement noise**, and a careful accounting says the entire remaining plan is worth at most a
further 15–28% of the gap under assumptions we've already disproved.

**Recommendation: stop funding accuracy work on the rule engine — but do not conclude from that
that the approach is dead.** The strongest version of this project is one we have not tried:
pay frontier prices **once per document** to produce a rich, explained, human-correctable map,
then answer unlimited behaviour questions against it cheaply. Our evidence favours that reading
— every wall we hit was the *representation* being too thin, never the matching being too dumb,
and the only real gain in the project's history came from improving an instrument rather than
the engine. See **Option D** in §6; it is the one worth funding, and it is testable for tens of
dollars.

If the goal is purely "high-quality results without much human work" **and** you are willing to
pay per behaviour, per iteration, forever: use frontier models today. The rule engine as built
will not overtake them.

---

## 1. The problem

Organizations publish normative documents — OpenAI's Model Spec, Anthropic's Constitution,
internal policy. A recurring, expensive question is: *given some behaviour a model exhibited,
which passages of the document actually bear on it?*

Today you answer that by asking a frontier model, passage by passage. That is slow, costs money
per query, gives a different answer each time, and produces no evidence — just an assertion.
For auditing, that last part is the real problem: you cannot show your work.

**The goal was a tool that answers as well as frontier models but instantly, offline, and with
an auditable reason for every answer** — and, if it worked on one document, that transferred to
another without re-tuning.

---

## 2. What we built

**Read the document once, expensively; query it many times, cheaply.** A cheap model reads each
passage and tags it with short named facts — "atoms" — like `imminent_bodily_harm` or
`should_provide_supportive_response`. A question is expressed in the same vocabulary, and
matching is structural: no model call at query time, and every hit traces back to the span of
text that licensed it.

**The process turned out to matter more than the mechanism.** Because the tool is scored against
frontier-model judgements, there is a constant temptation to tune it until it agrees with them —
which measures nothing except your ability to fit an answer key. So every change runs through a
ceremony:

1. **Freeze a prediction** before measuring anything.
2. **Make the change**, measure which passages changed status.
3. **Judge every changed passage against the document** — never against the answer key.
4. **Keep or revert** on that judgement, not on whether the score improved.

**This has already paid for itself once.** A change that clearly *improved* the aggregate score
was reverted because per-passage review found it had deleted the document's guidance on
de-escalating a user's radicalization. The metric said ship it. The process said no.

Supporting that: 2,194 automated tests, sha-frozen inputs so any past result can be rebuilt,
blind two-coder protocols, and scans that have caught both deliberately planted leaks and real
mistakes by agents working on the project.

---

## 3. Where the quality actually is

The metric is MCC, which runs from −1 to +1, where 0 is chance. Measured on three behaviours
over the full 589-passage universe:

| | score |
|---|---:|
| Frontier judge panel — the bar | **+0.556** |
| **Our tool** | **+0.309** |
| Bag-of-words keyword baseline | +0.108 |

**Read it this way:** between "dumb keyword matching" and "a panel of frontier models," the tool
captures **45% of the distance**. That is a real result — it is 2.9× the keyword baseline, and it
is free and instant at query time.

It is also, plainly, not frontier quality.

**The trajectory is the finding.** Here is what six months of the fix ladder looks like:

| | change in score |
|---|---:|
| Re-selecting which concepts the questions search with (an *instrument* change) | **+0.072** |
| **Six complete engineering cycles after that** | **+0.0003** |
| Measurement noise floor | **±0.032–0.037** |

The six cycles are, statistically, indistinguishable from doing nothing. The one genuine
improvement in the whole record came from fixing a *measuring instrument*, not the engine.

---

## 4. How much more we think we can get

We costed every remaining planned fix against the catalogued errors. Assuming each lands
**perfectly with zero side effects** — which has never once happened — the whole remaining plan
closes **42%** of the gap, reaching about +0.41. The honest estimate is **15–28%**, reaching
+0.35 to +0.38.

Even that generous number rests on assumptions already disproved by measurement:

- One planned fix **changes nothing at all** — we built it and measured zero effect.
- Another supplies 65% of the optimistic gain, and its own independent review disqualifies
  **14 of its 26 targets**. Priced with realistic side effects it delivers *less than nothing*.
- The largest fix reaches **half** of the error class it targets — about 27% of all catalogued
  disagreements.
- **20% of the catalogued errors cannot be fixed at all without cheating** — they are threshold
  calibration, and "fixing" them means tuning until we agree with the answer key.

And the deepest problem: **43% of the errors being measured were never catalogued.** Our
error census covers 256 of 447 actual disagreements. Every planned fix aims at the 57% we
enumerated.

---

## 5. Why rules don't cover it — the actual limitation

This is the part worth reading, because the naive expectation is that rules should eventually
cover everything. They don't, and the reason is specific.

**Every rule we add either needs a new layer of judgement, or trades one error for another.**
Four concrete walls:

**(a) The formal representation loses the deciding information.** Two passages — one about a
user threatening another person, one about a user at risk of self-harm — have *structurally
identical* representations. Both are "the model should respond supportively to the user." One
must be returned for a question about harm to third parties; the other must not. The
distinguishing fact is who the harm falls on, and it exists only in prose. To fix it you must
add a new annotation layer recording who is affected — which is itself a model judgement needing
its own validation and review. The rule didn't eliminate the judgement; it *relocated* it.

**(b) Some questions the document does not answer.** A passage covers a user whose company
accounts get compromised. Is the user's own employer a "third party"? Two independent competent
reviewers split on it, and the document genuinely doesn't settle it. No rule can decide what the
text leaves open — someone has to rule, and those rulings accumulate, one per ambiguity.

**(c) Some passages protect people they never mention.** Guidance on de-escalating radicalization
protects third parties; the text never says so. A rule that never infers can't reach it. A rule
that infers is unsafe — the same inference resurfaces passages we correctly suppressed. The only
safe path is a human approving each such case individually.

**(d) Widening coverage adds errors roughly as fast as it removes them.** Adding vocabulary to
catch missed passages also makes the tool fire on passages it shouldn't. At three false
positives per true one — modest, given the tool already runs at 23–65% precision — the largest
remaining fix nets to zero.

**The unifying finding: the long tail is not made of missing rules. It is made of judgement.**
Roughly a third of the remaining error is cases where "which passages are relevant" is a
question about meaning, context, or a boundary the document leaves open — not a question a
structural matcher can answer at any level of sophistication. A significant chunk is not even
about parties or concepts; it is passages about *answer quality*, where the relevance question
has a different shape entirely.

That is why returns diminish. You are not compressing knowledge into rules. You are moving
judgement out of a model's head and into artifacts — and each artifact needs its own review,
its own validation, and its own defence against being tuned to the answer key.

---

## 6. The three options

### A. Keep funding the rule engine toward frontier parity

**No.** Six cycles delivered nothing measurable; the remaining plan's honest ceiling is +0.38
against a +0.556 bar; and the mechanisms that would deliver most of it are the ones our own
reviews just disqualified. The next planned step also spends real money on model calls whose
best possible effect is a third of the noise floor — an unfalsifiable purchase.

### B. Use frontier models instead

**If the only goal is quality with little human effort: yes, today.** Frontier models score
+0.556 where we score +0.309. Nothing in our plan closes that.

But be clear about what you give up, because it is not nothing: per-query cost and latency,
offline operation, reproducibility (frontier answers drift between runs and between model
versions), and — most importantly for auditing — **evidence**. Our tool cites the span that
licensed each answer. A frontier model asserts.

And frontier is not a ceiling on quality either. The one human expert who reviewed the panel's
output found the *judges* over-flag and flatten importance — treating many related passages as
equally relevant and failing to identify *the* core one. Their verdict on our tool was
**"missing nuance and specificity, but very useful and efficient to find relevant parts and
compare"** — and they endorsed a use case we have never measured: **ranked first-pass auditing**.

### D. The option this memo originally missed: pay frontier prices ONCE, per document

*Added 2026-08-05 after the framing above was challenged, correctly.*

The comparison in A–C is between "our cheap tool" and "a frontier model per query." That
skipped the option that actually matches the economics: **the expensive pass is a one-time cost
per document; the cheap thing is per behaviour, per iteration.**

Reframed: *is there a frontier "mapping layer" — run once over the document, producing explicit
decisions with written explanations, auditable and human-correctable after the fact — such that
arbitrary behaviour questions can then be answered cheaply against it?*

**Our evidence bears on this more favourably than on the rule ladder, for four reasons:**

1. **The only real gain in the project's history came from improving the representation, not
   the engine.** +0.072 from re-selecting which concepts the questions search with; +0.0003 from
   six cycles of matching improvements. That is direct evidence that representation quality is
   the lever.
2. **Every wall we hit was representation loss, not matching failure.** The two structurally
   identical passages are identical *because the annotation dropped who the harm falls on*. The
   fix we designed for it — a per-passage record of the affected party, with a verbatim
   supporting quote — is a small instance of exactly what you're describing.
3. **The cost is genuinely small and we can price it.** 589 passages, one frontier call each,
   a few thousand tokens in and out: **order $20–60, once**, versus 589 × behaviours ×
   iterations for the per-query approach. Our existing design already has the cheaper variant —
   a cheap model does the pass, a frontier model validates a stratified sample — measured at
   well under $1.
4. **The correction machinery is already designed** (`INTERPRETATION_LAYER_DESIGN.md`): entries
   carry who approved them, when, and why; they are individually revocable; and the tool reads
   them as fact rather than re-deriving them. That is precisely "human-correctable after the
   fact", and it is *better* than a frontier model per query, which gives a different answer
   each run and leaves no record to correct.

**The long tail may be much shorter in dimension-space than in rule-space.** This is the key
reframing, and it is the thing the earlier §5 got half right. We hit four walls, and each maps
to a *missing annotation dimension*, not to a missing rule:

| wall we hit | the dimension it implies |
|---|---|
| Two identical-looking passages, different answers | **who the harm or benefit falls on** |
| A passage protects people it never names | **what it implies but does not say** |
| The document doesn't settle a boundary | **the scope decision, with its reasoning** |
| ~30 cases about answer quality, not parties | **what kind of obligation this passage is** |

Four dimensions, discovered empirically by failing four times. That is a very different
prospect from an unbounded tail of rules. If the true dimension count is ~5–15, a single
well-designed frontier pass can carry all of them, and the tail closes.

**What is genuinely unproven — and it is one thing, and it is cheap to test:** *does an
annotation made without knowing the behaviours generalize to behaviours nobody had in mind?*
Every dimension above was discovered by looking at failures on three known behaviours. An
annotation schema fitted to those is not evidence about arbitrary future ones. This is exactly
what the six held-out behaviours exist to answer, and it is answerable in one experiment.

**The risk to name honestly:** schema completeness is decided in advance. Miss a dimension and
a whole class of questions becomes unanswerable — and you find out only by failing at it, which
is how we found all four. The bet is that the number is small and discoverable. Our data is
consistent with that, and does not prove it.

**How I would test it, in order:**

1. **Blind annotation pass** on a subset — frontier, rich schema covering the four known
   dimensions plus an open "what else is salient here" slot, with a written explanation and a
   verbatim quote per decision. **The schema must be written without looking at the held-out
   behaviours.**
2. **Score it on the six held-out behaviours.** If a behaviour-blind annotation answers
   behaviours it never saw, the architecture is validated and the tail is bounded. If it only
   works on the three it was designed against, the tail is not bounded and Option B is correct.
3. **Only then** build the cheap-model-plus-parity-validation version, which is where the
   economics actually live.

That sequence spends tens of dollars and one one-shot resource to answer the question the whole
project has been circling. It is a far better use of a held-out test than confirming that the
rule ladder plateaued.

### C. Pivot — the auditability machinery

Two things, both cheap, both building on what already works.

**C1. Ship the auditability machinery, not the scorer.** The genuinely novel assets here are the
process and the instruments: judgements made explicit, versioned, revocable and individually
reviewable; a change ceremony that catches metric-improving regressions; an error census method
that classifies *why* a system disagrees rather than just how often. That machinery is
**model-agnostic**. Point it at a frontier model's output and you get frontier quality *plus*
provenance, reproducibility, and regression control — which is the actual unmet need. The tool
becomes the audit layer, not the answer engine.

**C2. Measure the axis the expert actually endorsed.** We have spent the entire project on
binary relevance, and the one human signal says the useful question is *ranking* — surface the
core passage first. We have never measured that. It is plausible the tool is far better at it
than +0.309 suggests, because ranking rewards precision at the top rather than total recall.

**Before committing to either, two experiments that cost almost nothing:**

1. **Re-run the "who was wrong" classification.** Our census records, per disagreement, whether
   the tool or the panel was at fault. Taken at face value it says **more than half the gap is
   panel error** — but the field turns out to be confounded with which batch produced it, so it
   cannot be trusted as it stands. One recalibrated pass either legitimises a large correction
   to the bar or kills the hypothesis. This is the single highest-value cheap check available.
2. **Run the transfer test.** The tool has never been evaluated on the six behaviours held back
   from all development, or on a second document. That is the question "does this approach
   generalize" — and it is answerable now, on a frozen pipeline, without any further fixes.

---

## 7. What to tell a funder

> The rule-based approach reached 45% of the way from keyword matching to frontier-model
> quality, then stopped improving — six full engineering cycles moved it by 1% of the
> measurement noise. We understand why: the remaining errors are not missing rules. Every wall
> was the same shape — the once-per-document representation was too thin to carry the deciding
> fact, so the judgement had to happen at query time, where it is expensive and unauditable.
>
> That diagnosis points somewhere specific. The economics that matter are **high one-time cost
> per document, low cost per behaviour and per iteration** — and we never tested the version
> built for those economics: a frontier pass over the document that makes each decision
> explicitly, in writing, with a citation, once, and is human-correctable afterwards. Our four
> failures map to four missing annotation *dimensions*, not to an unbounded tail of rules; if
> the true count is small, that architecture closes the gap and the per-query cost stays near
> zero.
>
> One experiment decides it, for tens of dollars: annotate blind, then score on behaviours the
> annotation never saw. If a behaviour-blind map answers behaviours nobody had in mind, fund it.
> If it only works on the behaviours it was designed against, the tail is unbounded and the
> right answer is to use frontier models per query and keep only our audit machinery.
>
> Either way the durable asset is the same: the machinery for making model judgements explicit,
> revocable, and regression-tested. That works wrapped around any engine, and it addresses the
> need frontier models genuinely do not meet.

**A closing note on epistemic hygiene, which is itself a result.** Every negative finding in this
memo was produced by the project's own instruments, pre-registered and adversarially reviewed
before anyone knew what the answer would be. The zero-effect fix was measured before it shipped.
The disqualified mechanism was caught by a review of our own design. The published baseline
number in our README was wrong in *our favour* and we corrected it. A project that reliably
tells you its own approach has stalled is doing something right, and that capability is worth
more than the 0.04 the remaining ladder might have bought.

---

## Sources

All in this repository, all reproducible without network access:

- `semi-formal-experiment/RELEVANCE_QUALITY_READ.md` — the measurement: current scores, the
  full trajectory across every snapshot, the gap decomposition, the census-coverage finding, and
  the confound in the "who was wrong" field.
- `semi-formal-experiment/S5_ADVERSARIAL_REVIEW.md` — the zero-effect measurement.
- `semi-formal-experiment/S6_ADVERSARIAL_REVIEW.md` — 14 of 26 targets disqualified.
- `semi-formal-experiment/D5_WORKED_EXAMPLES.md` — why the largest fix reaches half its class,
  and the two structurally identical passages that must be answered differently.
- `semi-formal-experiment/cycles/patient-pricing-2026-08-04/decision.json` — the revert: a
  metric-improving change that deleted needed safety guidance.
- `semi-formal-experiment/cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md` — the
  ambiguity two competent reviewers split on.
- `semi-formal-experiment/INTERPRETATION_LAYER_DESIGN.md` — the proposed shape of C1.
- `README.md` — current headline numbers, with the corrected baseline.
