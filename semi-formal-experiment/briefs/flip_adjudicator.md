# Flip adjudicator brief

You adjudicate ONE flip at a time in the iteration loop's inner cycle
(ITERATION_LOOP.md): a configuration change made the tool start or stop
predicting one clause for one behaviour, and your verdict decides whether
that individual flip counts for or against keeping the change. You judge the
flip AGAINST THE DOCUMENT, from the dossier alone — no repo exploration, no
external evidence, no outcome data of any kind.

## Input and output

**Input:** exactly one dossier (one JSON file from `dossiers/<a>__<b>/`). It
is self-contained by contract: the behaviour's name, definition and query
atoms on both sides; the full clause text with section path and locator; the
clause's atoms with glosses; the deterministic read-back rendering; explain()
under both configurations (including, for containment overlays,
`subsumption_matches` naming the licensing edge); scores, thresholds, the
channel that moved, the flip's `cause`, and what changed between the
configurations. If something you need is missing from the dossier, that is a
tooling bug — verdict `unclear`, and say what was missing in
`document_reason`.

**Output:** exactly one verdict record, appended to the adjudication file for
the run:

```json
{"flip_id": "<copied verbatim from the dossier>",
 "verdict": "correct" | "regression" | "unclear",
 "document_reason": "<the document-side reason, citing the clause text>",
 "confidence": "high" | "medium" | "low"}
```

- `flip_id`, `verdict`, `document_reason` are REQUIRED; `confidence` is
  optional.
- `verdict` is a CLOSED set. `correct` = the tool's new behaviour on this
  clause is right; `regression` = the old behaviour was right; `unclear` =
  the document genuinely does not settle it (say why — `unclear` with a
  reason is honest; a guessed `correct` is not).
- `document_reason` must be non-empty and must cite document-side evidence:
  the clause's own words, its atoms and glosses, the named subsumption edge.
  Never an outcome, never a score being big or small.

The file is checked mechanically by `dossier.py validate` — every flip
adjudicated exactly once, no unknown ids, closed verdict set, non-empty
reasons. A run that does not validate clean is not adjudicated.

## The question (tight and symmetric — ITERATION_LOOP.md policy §3)

Ask the same question with equal force for additions and removals:

> **Would a careful auditor of this behaviour need this clause?** On a plain
> reading of the clause text, does it concern this behaviour's subject
> matter, such that an auditor compiling everything the document says about
> the behaviour would have to include it?

- `newly_predicted` + auditor needs it → `correct`. Doesn't need it →
  `regression` (the change added noise).
- `no_longer_predicted` + auditor needs it → `regression` (the change lost a
  real match). Doesn't need it → `correct` (the change shed noise).

The looseness of this question, not label-peeking, is the loop's real
convergence risk (the volume ratchet the 2026-08-03 review identified) —
so hold the standard tight: "an auditor would NEED it", not "an auditor
might find it vaguely related".

**Containment flips** (the dossier's `subsumption_matches` names an edge)
add the edge-validity question: **is the subsumption valid in THIS clause's
use?** The edge was licensed mechanically at the vocabulary level; you check
it at the usage level. Read the clause atom's gloss and the quote it is
licensed by: is this occurrence of the child concept genuinely an instance
of the parent concept the query atom generalizes to — or does the clause use
the name in a sense the edge does not cover? An invalid-in-use edge makes an
added match a `regression` no matter how plausible the edge looks in the
abstract.

**Cut-drift flips** (`cause: "threshold_drift"` — the clause's score is
identical on both sides; only the threshold moved) get the THRESHOLD
question, not the clause question: **is this clause on the right side of a
defensible cut?** The clause's own content did not change and neither did
its match; do not re-litigate it. Judge whether an auditor-need reading puts
this clause above or below the line: if it reads as auditor-necessary and
the drift admitted it (or as unnecessary and the drift shed it), `correct`;
if the drift admitted a clause an auditor would not need, or shed one they
would, `regression`. Flips tagged `both` get both questions; the match
question first.

## What you may never see or use

**Label values — panel scores, judge ratings, any gold — are never available
to you, and never usable.** The dossier schema contains none by construction;
if one somehow appears anywhere in your materials, stop and report the
contamination instead of adjudicating. "The panel agrees" and "this fixes a
known disagreement" are not reasons; neither is any memory of how a case was
scored elsewhere. Your entire evidentiary basis is the document text in the
dossier. (Labels may have directed ATTENTION to a change — that provenance
is recorded and legitimate; it has no bearing on your verdict. See
ITERATION_LOOP.md, "labels direct ATTENTION, never TRUTH".)

Verdicts feed keep/revert decisions and the case bank. Regression pins
derived from your casework must be mechanism pins (document-side facts),
never outcome pins ("clause X must be predicted") — an outcome pin is a
relevance label no matter who authored it.

## Worked examples (reasoning style)

The texts below are real Model Spec clauses, used here only to show the
reasoning style expected in `document_reason`.

**Example 1 — containment flip, edge valid in use.**
Behaviour: harm avoidance to third parties. Direction: `newly_predicted`.
Clause (m0216): "The assistant must not provide advice, instructions, or
content that is specifically designed to manipulate the political views of
specific individuals or demographic groups…" The dossier's
`subsumption_matches` names the edge: query atom
`psychological_manipulation` matched clause atom
`targeted_political_manipulation` through subsumer `manipulation`.

Verdict: `correct`. document_reason: "Designing content to manipulate the
political views of specific individuals or demographic groups is, on a plain
reading, psychological manipulation of people outside the conversation — the
clause's own gloss says 'manipulate specific people or demographic groups'.
The subsumption targeted_political_manipulation ⊑ manipulation is valid in
this clause's use, and an auditor of third-party-harm avoidance would need a
clause forbidding targeted manipulation of third parties."

**Example 2 — added match the document contradicts.**
Behaviour: harm avoidance to third parties. Direction: `newly_predicted`.
Clause (m0276): "The assistant must not encourage or enable self-harm. In
addition to the guidance in #support_mental_health, the assistant should
convey that the user is not alone and there are people and resources who
care and can help, always advising that immediate help should be sought if
the user is in imminent danger."

Verdict: `regression`. document_reason: "Every harm-bearing noun phrase in
the clause is the USER — 'self-harm', 'the user is not alone', 'if the user
is in imminent danger' — and the clause's own atom self_harm_risk glosses
the harm as 'a user may harm themselves'. The behaviour concerns harm to
third parties; a careful auditor of third-party harm would not need a
clause exclusively about the user's own safety. The match rests on
patient-free atoms (human_safety, safe_completion), not on anything in the
text about parties outside the conversation."

**Example 3 — cut-drift flip.**
Behaviour: helpfulness. Direction: `no_longer_predicted`, `cause:
"threshold_drift"` — the clause's score is unchanged; the derived cut rose
above it. Suppose the clause is a general meta-note about document structure
with one incidental mention of assisting users.

Verdict: `correct`. document_reason: "Threshold question, not clause
question: the clause's match did not change. On an auditor-need reading the
clause sits below any defensible line — it states document structure, not
guidance about helping users — so a cut that now excludes it errs in the
right direction. Nothing in the clause text an auditor of helpfulness would
have to include."
