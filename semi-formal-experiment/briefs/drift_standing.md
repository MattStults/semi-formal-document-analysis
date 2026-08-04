# Drift-standing adjudicator brief

You adjudicate the STANDING contents of the frozen label-free cut
(`thresholds_frozen.json` v1), one case at a time: clauses whose scores sit
near the cut, where nothing changed and nothing flipped — the cut simply
fell where it fell. Your verdicts become a disclosed error-mass accounting
line and document-side case law (DRIFT_STANDING_DESIGN.md §3, option (a)).
They change NO number, NO predicted set, NO threshold. You judge each case
AGAINST THE DOCUMENT, from the dossier alone — no repo exploration, no
external evidence, no outcome data of any kind.

Small-model seat (briefs/README.md standard). Two independent blinded legs
run this brief over the same dossiers; divergence above 10% of verdicts is a
defect in THIS brief, and the pass reruns — it does not average.

## Input and output

**Input:** exactly one stripped dossier (a JSON file from
`drift_standing/dossiers/`). It is self-contained by contract: the
behaviour's name, definition and query atoms with glosses; the clause's full
text, section path, locator and kind; the clause's atoms with glosses; the
deterministic read-back rendering; explain() under the pinned configuration
(channels, channel shares, matched atoms, top lexical terms); the frozen
cut, the clause's normalized score, and `distance_to_cut`. If something you
need is missing, that is a tooling bug — verdict `unclear`, and say what was
missing in `document_reason`.

**Output:** exactly one verdict record, appended to your leg's verdict file:

```json
{"dossier_id": "<copied verbatim from the dossier>",
 "verdict": "admit_defensible" | "admit_not_needed" | "unclear",
 "document_reason": "<document-side reason citing the clause text>",
 "confidence": "high" | "medium" | "low"}
```

- `dossier_id`, `verdict`, `document_reason` are REQUIRED; `confidence` is
  optional.
- `verdict` is a CLOSED set. Anything else is a schema violation, not a
  fourth opinion.
- `document_reason` must be non-empty and must cite document-side evidence:
  the clause's own words, its atoms and glosses. Never a score being big or
  small, never "it is close to the cut".

The file is checked mechanically by `drift_dossiers.py validate` — every
dossier adjudicated exactly once, no unknown ids, closed verdict set,
non-empty reasons. A run that does not validate clean is not adjudicated.

## The question (the flip adjudicator's cut-drift standard, verbatim)

This is the threshold question, not the clause-match question: the clause's
match is not on trial; the threshold placement is (briefs/
flip_adjudicator.md, "Cut-drift flips"). *Is this clause on the right side
of a defensible cut — would a careful auditor of this behaviour need it?*

> **Would a careful auditor of this behaviour need this clause?** On a plain
> reading of the clause text, does it concern this behaviour's subject
> matter, such that an auditor compiling everything the document says about
> the behaviour would have to include it?

- Auditor would NEED it → `admit_defensible` (its admission at the cut is
  defensible; if it sits below the cut, its exclusion is a real cost).
- Auditor would NOT need it → `admit_not_needed` (its admission is noise an
  auditor would not miss; if it sits below the cut, its exclusion is right).
- The document genuinely does not settle it → `unclear`, with the reason.

The verdict names the auditor-need judgment of the CLAUSE; it applies with
the same force whether `distance_to_cut` is positive (the clause is admitted
at the frozen cut) or negative (it sits just below). Do not re-litigate the
match; do not reward or punish the score.

Hold the standard tight: "an auditor would NEED it", never "an auditor
might find it vaguely related". The volume-ratchet warning applies with
full force — a loose reading here converts a measured standing cost into a
fake vindication, which is worse than the cost.

### Ruling: need is REDUNDANCY-AWARE (recalibration 1)

The question above admits two readings, and run 1 split on exactly that
seam. This brief now RULES on it. The standard is **redundancy-aware
need**:

> **Would a careful auditor of this behaviour need THIS clause, given that
> the rest of the corpus is also retrieved?** The auditor is not reading
> this clause in isolation; they hold the whole retrieved set. A clause
> earns `admit_defensible` only if its own text contributes something to
> the audit that the more direct rules on the same subject do not already
> supply — a distinct condition, a distinct boundary, a distinct
> obligation, a carve-in or carve-out stated nowhere more directly.

Two readings are considered and REJECTED by name, so no future seat has to
rediscover the ambiguity:

- **STANDALONE RELEVANCE — rejected.** "This clause supports the
  behaviour's principle, therefore an auditor could defend including it."
  Rejected: in a document this internally coherent, nearly every clause
  supports nearly every behaviour's principle at some remove. Standalone
  relevance collapses the standard to "vaguely related" and yields the
  ~100% defensible-rate failure mode. This is the same exclusion the
  flip_adjudicator precedent draws: "a careful auditor would not use it"
  excludes the merely-consistent.
- **KIND-CATEGORICAL EXCLUSION — rejected.** "It is an example /
  definitional / meta clause, therefore not needed; it is a conditional
  rule, therefore needed." Rejected: clause kind is evidence, never the
  verdict. An example that fixes a boundary no rule states (where exactly
  the document draws a line in a hard case) is non-redundant and
  defensible; a conditional rule that merely restates an obligation
  covered more directly elsewhere is redundant and not needed. Judge the
  CONTENT of this clause against what the rest of the corpus supplies, not
  the clause's type label.

Two further clarifications, binding: (i) redundancy is judged from the
dossier — the clause's text, atoms, kind, and section path tell you
whether its content is a distinct contribution or a restatement of the
more direct rules its own section structure points to; you do not open the
corpus to check. (ii) The `document_reason` requirement is strict:
machinery facts — "no matched atoms", channel shares, lexical terms — are
score-side evidence and are NOT acceptable reasons, exactly as a score
being big or small is not. The reason must engage the clause's words.

## Calibration anchors (worked exemplars)

Four cases from run 1 on which BOTH blinded legs independently concurred,
worked here under the redundancy-aware standard so you can calibrate
before your first verdict. They are anchors, not answers to copy: none of
run 1's disputed cases appears here, and matching an anchor's clause type
is not a verdict (see the kind-categorical rejection above).

**m0203 — `admit_defensible`** (avoiding-over-and-under-caution;
"*Prohibited content* should never be produced by the assistant in any
circumstance — including transformations of user-provided content"). This
clause states the absolute floor of the caution scale: "never", "in any
circumstance", and the explicit carve-in of transformations — an exception
other clauses otherwise grant. An auditor of over-/under-caution needs the
hard limit that bounds the tradeoff, and no more direct rule in the
retrieved set supplies the "even transformations" boundary. Non-redundant
content → defensible.

**m0370 — `admit_defensible`** (avoiding-over-and-under-caution; for
subjective questions, articulate interpretation and assumptions with a
thoughtful rationale; be "a firm sounding board … rather than a sponge
that doles out praise"). This is a specific middle-path directive for a
specific situation (subjective questions): neither hedging into vagueness
nor complying into empty praise. The sounding-board/sponge boundary is
stated nowhere more directly; an auditor compiling what the document says
about calibrated caution needs this clause itself, not a paraphrase from
elsewhere. Distinct obligation in a distinct condition → defensible.

**m0183 — `admit_defensible`** (helpfulness; "seek clarification when
instructions might be intended but could cause serious side effects").
The document has general clarifying-question rules — so a lazy redundancy
reading might discard this. But the clause attaches the obligation to a
distinct trigger: possibly-intended instructions from untrusted data whose
execution carries serious side effects. That condition is not restated by
the general rules; an auditor of helpfulness under uncertainty needs this
specific trigger. Distinct condition → defensible. (This is the anchor
against over-applying the redundancy ruling: redundancy means the CONTENT
is supplied elsewhere, not that the TOPIC appears elsewhere.)

**m0379 — `admit_not_needed`** (helpfulness; the fragment "suggesting how
the response could improve with more information"). A definitional sliver
of a paragraph whose substantive clarifying-question obligations are
carried by fuller, more direct clauses in the same retrieved corpus. Read
on its own it gestures at the behaviour; given the rest of the corpus is
also retrieved, it contributes no condition, boundary, or obligation the
auditor does not already hold. Merely-consistent restatement → not
needed. Note that BOTH readings of run 1's split converged here — even
standalone relevance found nothing standalone in it.

## Expectation note (calibration failure signals)

This population is near-cut marginal BY SELECTION — every dossier sits
within 0.10 of the frozen cut; these are the borderline cases, chosen
because they are borderline. A genuinely calibrated seat should therefore
land somewhere in the interior: a defensible-rate anywhere near 100% or
near 0% is not a finding, it is a calibration failure signal — the seat
has collapsed into one of the two rejected readings. (Run 1's legs landed
at 59/60 defensible and 20/60 defensible respectively; at least one was
mis-calibrated by construction.) When you are genuinely torn under the
redundancy-aware standard, `unclear` is the correct verdict, with the
tension stated in `document_reason` — run 1 produced 0 `unclear` across
120 verdicts on a by-selection-marginal population, which is itself
suspicious for forced binary choices. Uniform `high` confidence across a
marginal population is the same smell.

## What you may never see or use

**Label values — panel scores, judge ratings, any gold — are never
available to you, and never usable.** The stripped dossier schema contains
none by construction (a banned-key check enforces it); if one somehow
appears anywhere in your materials, stop and report the contamination
instead of adjudicating. Blindness list — none of the following may be
opened, quoted, or remembered into a verdict:

- any panel file (`behaviours.json`, panel coverage/universe artifacts, any
  per-judge verdict file);
- `audit_dossiers/` in its entirety — the census dossiers carry panel
  scores and per-judge verdicts BY DESIGN and are contaminated for this
  seat;
- `DISAGREEMENT_REPORT.md`, `DISAGREEMENT_REPORT_ext_v1.md`, and any
  disagreement/census report;
- the design docs for this pass and its neighbours
  (`DRIFT_STANDING_DESIGN.md`, `PORTFOLIO_REVIEW.md`, `HANDOFF.md`,
  `CYCLE*_DESIGN.md`, cycle decision files under `cycles/`);
- the OTHER leg: its assignment file, its verdict file, its operator notes;
- run 1's outputs in their entirety: `drift_standing/verdicts_leg_a.json`
  and `drift_standing/verdicts_leg_b.json` as they existed before the
  rerun, and any comparison or diagnosis of them — rerun seats adjudicate
  under the recalibrated standard, blind to how any case was previously
  called. (The four anchor cases quoted in this brief are the sole,
  deliberate exception, disclosed above.)

"The panel agrees", "the census said panel-side", and "this class is mostly
noise" are not reasons; neither is any memory of how a case was scored
elsewhere. Your entire evidentiary basis is the document text in the
dossier. (Labels directed ATTENTION to these 60 cases — that provenance is
recorded in the assignment artifact and legitimate; it has no bearing on
any verdict. ITERATION_LOOP.md: labels direct ATTENTION, never TRUTH.)

## The two-blinded-legs protocol

Two legs, A and B, each a fresh context running this same brief over the
same 60 dossiers, each writing its own verdict file
(`drift_standing/verdicts_leg_a.json` / `verdicts_leg_b.json`). A leg never
sees the other leg's verdicts, notes, or existence beyond this paragraph.
After both legs validate clean, a separate (non-seat) comparison counts
agreement: **the pre-registered expectation is >= 90% verdict agreement**
(the flip seat's precedent: 7/7 and 3/3); below that the brief is defective
and the pass RERUNS after the brief is fixed — disagreements are never
averaged, split, or negotiated.

## What the output is — and the ban list (verbatim from the design)

The verdicts are DISCLOSURE-ONLY: (1) the error-mass accounting line quoted
wherever the frozen cut's performance is quoted, and (2) document-side case
law for a possible future, checkpoint-gated re-cut cycle's post-hoc check.
The predicted set, weights, and cut are bit-identical before and after this
pass. From DRIFT_STANDING_DESIGN.md §3, "What may never flow from it":

> No per-clause cut nudging: no exclusion list, no per-id override, no
> post-filter dropping `admit_not_needed` clauses from the predicted set,
> no weight or rule edit citing these verdicts, no outcome pin ("m0XXX must
> not be predicted"). Each of those is the same move: converting 59
> our-authored relevance judgments into training signal — **fitting with
> extra steps**, and on this class it is *literally* the relapse pattern of
> §0 (choosing what the cut admits by looking at judgments of what it
> should admit). The seat's verdicts are labels the moment anything
> mechanical consumes them.

And the casebank consultation rule (§3, use 2, amended per PORTFOLIO_REVIEW
F10):

> **ONE casebank consultation per candidate rule FAMILY, consumed and
> recorded** — the consultation is logged (which family, which cycle, date)
> in the casebank's own ledger, and a rule family that has spent its
> consultation cannot iterate against the casebank; a second look for the
> same family is the coordinate-descent move the F10 fence exists to block.

## Recalibration history

**Run 1 (failed, superseded).** Two blinded legs, 60 dossiers each,
validated clean — and agreed on 20/60 verdicts (33%), far below the
pre-registered ≥90%. The divergence was ONE-DIRECTIONAL in all 40
disagreements: leg A said `admit_not_needed` where leg B said
`admit_defensible`, never the reverse. Diagnosis (by the non-seat
comparison, not by either leg): the brief's question was unruled on
redundancy. Leg A applied a redundancy-aware reading (content captured by
more direct rules elsewhere is not needed), operationalized largely as
kind-categorical exclusion; leg B applied standalone relevance (supports
the behaviour's principle → defensible). Both were defensible readings of
the then-ambiguous question; the 33% is a defect of THIS brief, per its
own protocol. Neither leg produced a single `unclear` (0/120), and leg B
marked every verdict `high` confidence — both flagged above as calibration
failure signals.

**This amendment (recalibration 1, 2026-08-04).** Following the
select_audit v2 precedent (the binary self-calibrated seat failed at
32-47% in-scope; the fix moved calibration into the instrument), this
brief now: rules on redundancy (redundancy-aware need; standalone
relevance and kind-categorical exclusion rejected by name), adds four
calibration anchors drawn only from run 1's 20 agreed cases (the 40
disputed cases are deliberately NOT anchored — they must be resolved by
the recalibrated standard, not by fiat), adds the expectation note, and
extends the blindness list to run 1's verdict files.

**Rerun (required).** The pass reruns in full: two FRESH legs, blind to
run 1's outputs per the amended blindness list, over the same 60 pinned
dossiers, same ≥90% agreement bar. Run 1's verdicts are void for both of
the pass's declared uses; nothing is carried over or averaged.
