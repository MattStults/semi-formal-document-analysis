# Post 3 — How it's working (DRAFT, 2026-08-24; written after the runs, per the series rule)

Scope-honesty note, up front: every number in this post has a committed
artifact behind it (pointers inline, repo paths relative to
`walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/`).
The runs this post reports happened on 2026-08-24, under a signed
pre-registration whose errata are appended, never rewritten. Where a
falsifier fired, that is reported in the same table as the passes.

## What was run

A label-free symbolic instrument (no model calls at query time, no panel
labels anywhere in its inputs) answers "which passages of the OpenAI Model
Spec bear on behaviour X?" Truth is produced by blind frontier adjudication
under a PINNED ruling instruction, with three-seat panels on a seeded
fraction and pre-registered falsifiers. Three development behaviours were
measured on fresh, never-before-ruled draws; six never-consulted behaviours
were then run with zero adaptation.

## The development-behaviour table (fresh draws, ROUND4_DEV_TABLE.json)

| behaviour | raw precision | headline (match-or-defensible) | registered band | raw / headline decline-correctness |
|---|---|---|---|---|
| helpfulness | 0.625 — F1 fired | 0.725 — in band | 0.71–0.87 | 0.875 / 0.975 |
| harm-avoidance (3rd party) | 0.824 — in band | 0.882 | 0.81–0.97 | 0.800 / 1.000 |
| over/under-caution | 0.675 — F1 by one node | 0.750 — in band | 0.69–0.85 | 0.875 / 0.950 |

Both numbers always publish: "raw" scores the instrument against strict
panel majorities; "headline" additionally credits misses that a separate
blind one-pass adjudication ruled DEFENSIBLE (a reasonable index could
include/omit the passage), under a seat instructed to default against
defensibility. Harm's engaged cell is a POPULATION figure — every remaining
unruled engaged node was ruled, so there is no sampling error behind it.
Two raw cells missed their floors and the falsifiers fired; that is what
falsifiers are for, and the diagnosis below is why we trust the numbers
more, not less, for it.

## The result I did not expect: the improvement curve is real, and honest

Because every historical version of the instrument is committed, all ten
were scored against the SAME fresh 80-node truth (R4_VERSION_CURVE.json):
accuracy climbs monotonically v10 0.637 → v13 0.700 → v15 0.750 → v19
0.750. Three weeks of fixes generalized to data none of them ever saw —
this is not overfitting — and the curve also shows honestly where the most
recent week's work polished the already-ruled pool without moving the
frontier. The apparent collapse from earlier rounds (a 0.78 pass) is pool
hardening, quantified: the same v12 instrument scores 0.78 on the earlier
draw's population and 0.519 on today's residue — the unruled remainder of
the document is ~26 points harder, and today's instrument scores 0.625 on
it, the best any version does.

## Zero-adaptation transfer: two cold passes and one predicted failure

Six behaviours the campaign never consulted were built blind from their
definitions, and block 1 ran with zero adaptation (GEN_BLOCK1_SCORED.json):

| held-out behaviour | engaged precision | S1 floor 0.70 |
|---|---|---|
| harmlessness-to-user | 0.800 | PASS |
| objectivity-on-contested-questions | 0.800 | PASS |
| how-to-approach-tradeoffs | 0.400 | FAIL — F2, stop rule fired |

Two never-tuned behaviours pass cold at the same level as the certified
development behaviour. And the failure was PREDICTED IN WRITING before any
ruling existed (GENERALIZATION_FAMILY_PREDICTIONS.md, committed first):
tradeoffs was named as the likeliest failure, at exactly this falsifier,
for exactly the mechanism the blind module-builder had documented — the
vocabulary has no prioritization acts, so the module engages a third of the
corpus with no walls. The stop rule then halted block 2, per the signed
prereg. A failure you can predict from definitions before measuring is a
failure you understand; that is the strongest evidence in this post that
the remaining work is bounded and locatable.

## Where the misses live (and the day the judge itself was debugged)

Every engagement is a computed derivation, so every miss was traced
(R4_HELP_FAILURE_HYPOTHESES.md): the dominant classes are over-broad
act-bridges and quality-scope breadth in the behaviour modules — NOT
document errors and NOT translation errors. The census proves 10 of the 12
indefensible helpfulness misses are separable with existing or declarable
features; two are terminal at the current vocabulary, identified as such by
computation, not by giving up.

The most instructive failure of the day was in the measurement itself: the
first canary run diverged wildly, and the diagnosis recovered a
methodological law this project now treats as central — THE JUDGE IS THE
INSTRUCTION. An uncommitted ruling prompt produced a stricter judge than
the one that built the truth ledger; recovering the original instruction
verbatim from session transcripts and re-running reproduced the ledger
20/20 (LINEAGE_SEAT_INSTRUCTION.md). The same lesson recurred in
miniature within hours on a different judgment class (a criticality census
whose two frontier seats agreed only 15/24 under different briefs). Every
judgment class needs its instruction pinned and its stability measured
before its outputs are consumed; the ones here now are.

## What frontier judgment actually costs now

The entire day — some 400 blind rulings, panels, defensibility
adjudications, parity tests, and every diagnostic — consumed a few percent
of one subscription week (measured via cache-priced batch seats that rule
40 passages per call). Cheap-tier substitution was measured and REJECTED:
Haiku/Sonnet/DeepSeek score 0.70–0.85 against the ledger on the pinned
brief with decorrelated biases (parity_cheap_tier_certificates.json), and
one cheap census produced confident, uniform, wrong labels that a seeded
frontier spot-check caught in eight nodes. The honest economic finding is
the opposite of the one we went looking for: frontier judgment became
cheap enough that the cheap-model layer is mostly unnecessary.

## The failures worth their weight (carried from the whole campaign)

The reverted "improvement" that deleted the spec's guidance on
de-escalating a user's radicalization while the aggregate metric said ship
it — the founding reason every fix here is adjudicated per-flip, not
per-score. The false-separable census classes that took four adversarial
review rounds to kill. The annotation lanes no provider seat could read,
and the venue rulings that got them ruled anyway. And today's additions:
a voided seat whose passage the orchestrator had reconstructed from memory
instead of the committed packet (caught immediately, disclosed), and the
overclaimed "criticality rules" corrected by erratum within the hour.

## What this establishes — and does not

Establishes: on this document, a symbolic reading achieves 0.72–0.88
headline agreement with pinned-brief frontier truth on fresh draws across
three tuned behaviours; two of three untuned behaviours transfer at 0.80
with zero adaptation; failures are mechanically traceable to typed causes;
and the improvement curve on held-out truth is monotone across the entire
campaign. Does NOT establish: certification (two raw floors fired
honestly); anything beyond this one document; block-2 transfer (halted by
the stop rule, by design); or that the remaining misses are fixed — they
are located and typed, which is different.

## The path this points at, and the ask

The day's diagnostics converge on a specific next object: because
engagement is a computed function over finite vocabularies, every mismatch
provably locates in one of four places (node translation, module
declaration, mechanism inventory, or the truth ruling itself), the
inventory failure surface itself types into five classes with
pre-defined moves, and the conditions requiring expensive judgment reduce
to three identifiable ports (truth, translation faithfulness, and naming
new distinctions). Writing that ERROR CALCULUS down, building its
mechanical router, and validating it against every resolved mismatch in
the campaign's history is a session of design work with almost no model
cost — and it converts this project's claim from "we measured well" to
"we can prove which errors are mechanically fixable and identify, in
advance, exactly where judgment is required." That, plus a second document
(a constitution-class text) to test the calculus off its home turf, is
what continued funding buys.
