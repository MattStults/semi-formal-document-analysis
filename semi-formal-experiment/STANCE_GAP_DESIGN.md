# STANCE_GAP_DESIGN — the SELECT normative-stance gap: scoping and decision (2026-08-04)

This is a scoping/decision document. It does NOT design a grammar
extension, and nothing in it authorizes building one.

## The gap, stated precisely

The behaviour definitions in `behaviours_query.json` carry WEIGHTING
claims — normative stances about how considerations trade off — that no
atom in the vocabulary expresses. The SELECT audit
(`select_audit/query_readback.json`) found one in each of the three DEV
behaviours, and they are not incidental phrasing; each is the definition's
load-bearing clause:

1. **helpfulness** — "treating unhelpfulness as a real cost rather than a
   safe default": a COST ASSIGNMENT. Atoms cover helping acts
   (`should_provide_*`) and outcomes; none says unhelpfulness carries
   weight.
2. **harm-avoidance-to-third-parties** — "weigh the potential harm": a
   DELIBERATIVE TRADE-OFF stance. Atoms cover preventing/avoiding/
   refusing; none expresses the evaluative act of weighing options.
3. **avoiding-over-and-under-caution** — "just as much as … errors in
   either direction carry real costs": a PARITY principle. Atoms cover
   both directions separately; none expresses that the two error classes
   are weighted symmetrically.

Structurally: the atom grammar (`grammar.py`) can name topics, acts,
entities and values, mark polarity, principals and condition/consequent
role — all properties OF one clause's content. A stance is a RELATION
over considerations (cost(X) > 0; weight(A) = weight(B)), and grammar.py
already ruled on relations for the authority lattice: "the grammar can
NAME the level; it still cannot express the ORDER, because that needs a
relation between atoms." Queries therefore capture what a behaviour is
ABOUT; they cannot capture how the behaviour says to WEIGH it. SELECT is
stance-blind by construction, not by oversight.

## The three candidate framings, with costs

### A. Grammar gap — a new atom kind (`stance`) or a weighting relation
Cost: highest. A fifth kind breaks the closed set every module pins; a
relation is the exact extension grammar.py declined for authority order;
either forces re-annotation (paid) and coins atoms that the clause
vocabulary does not attest — the coined-vs-selected mismatch is precisely
the dead-channel failure `warn_atom_channel_disabled` exists to catch.
Expected benefit: unestablished. The capacity bound (atom index already at
+0.972 attainable, supervised readout +0.591) says representation was
never the relevance ceiling; HANDOFF's standing instruction is "DO NOT BUY
ANNOTATION." Building A now would be paying for expressiveness with no
measured recall deficit to spend it on.

### B. Query-representation gap — per-behaviour weighting metadata
E.g. a `stances` field on each `behaviours_query.json` entry (machine-
readable cost/parity/weigh records), possibly used to bias retrieval
(parity ⇒ require both error-direction atom families represented in the
hit set). Cost: medium — cheap to write, but it has no clause-side
counterpart to match against, so any retrieval effect is a new scoring
mechanism whose knobs would be tuned by looking at results: invariant-9
pressure with no pre-registered target. As pure documentation-in-data it
collapses into option C with extra schema.

### C. Accepted limitation, documented at the product layer
SELECT retrieves passages about the behaviour's topics and acts; it does
not represent, match, or rank by the definition's weighting stance.
`query_readback.json` stated_gaps is the canonical record; the product
surface (and `NEW_DOCUMENT_RUNBOOK.md` / tool output where SELECT results
are presented) states the limitation in one sentence. Cost: near zero.
Risk: the limitation quietly becomes permanent without ever being priced —
which the upgrade triggers below exist to prevent.

## Decision

**Adopt C now.** Document SELECT as stance-blind; do not extend the
grammar; do not add query metadata. Revisit after the frozen-pipeline
generalization phase, which is the first setting that can PRICE the gap:
6 new behaviours, evaluated once, some of whose definitions will be
stance-dominant (mostly weighting language) and some topic-dominant.

Rationale, in one line: every measured signal says representation is not
the binding constraint, and the honest response to an unpriced gap is a
disclosure plus a pre-registered way to price it — not speculative
expressiveness.

Falsifiable commitment: if stance-blindness costs measurable recall, it
must show up as the stated_gap phrases' home passages being MISSED. That
is checkable, and until it is checked, options A and B are premature.

## Evidence that upgrades this gap's priority (pre-registered triggers)

1. **Generalization-phase contrast.** At the one-shot small-panel
   evaluation, behaviours with stance-dominant definitions systematically
   underperform topic-dominant ones (per-behaviour MCC/AUC, stated with
   the 0.037 noise floor and the score-1 caveat). Behaviour identity is
   confounded with everything at n=6, so this is a trigger for
   investigation, not a proof. [Amended per PORTFOLIO_REVIEW addendum
   ruling 3: the review confirmed this trigger is NON-VACUOUS —
   proportionate-risk-mitigation and how-to-approach-tradeoffs are
   stance-dominant on their face, so the contrast has members on both
   sides. BUT the stance/topic coding of ALL SIX generalization
   definitions must be PRE-REGISTERED in the G1 freeze artifact, before
   any evaluation contact; a coding assigned (or adjusted) after the
   per-behaviour numbers exist makes the contrast post-hoc and the
   trigger proves nothing.]
2. **Document-side miss concentration.** Flip adjudications or the
   salience eval (SALIENCE_EVAL_DESIGN.md) repeatedly land on missed or
   buried passages whose content is weighting prose — note that all four
   expert core anchors ARE deliberation/weighing passages ("probability
   that the action leads to harm", "figure out if Claude is being over
   cautious or over compliant"). This is a $0, label-free probe.
3. **The conflict tier forces a relation anyway.** Priority-2 conflict
   work is literally about weighing obligations; if it builds a weighting
   relation for its own reasons, SELECT should reuse that representation
   rather than motivate its own — at which point option A's cost is
   already sunk elsewhere and only the SELECT wiring remains.

Any one trigger firing reopens this decision as a written cycle (OPEN →
PREDICT → …), with the choice among A/B re-argued against the measured
cost. Absent a trigger, C stands and the gap stays a disclosed,
documented, priced-at-zero limitation.
