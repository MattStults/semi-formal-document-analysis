# Frontier-panel agreement — attention surface, not truth

Every number below is agreement with a PANEL, adjudicate-against-the-document before treating any cell as an error. Probe folded in: True.

## helpfulness

* panel-relevant translated nodes (consensus>=5): 6 — reference clauses with no translated span: 26 (structural ceiling, not a miss)
* agree relevant: 3
* seat engaged / panel cold: 5  <- adjudication queue A
* panel hot / seat declined: 3  <- adjudication queue B
* panel hot / never retrieved: 0 (after probe)

## harm-avoidance-to-third-parties

* panel-relevant translated nodes (consensus>=5): 14 — reference clauses with no translated span: 44 (structural ceiling, not a miss)
* agree relevant: 6
* seat engaged / panel cold: 8  <- adjudication queue A
* panel hot / seat declined: 8  <- adjudication queue B
* panel hot / never retrieved: 0 (after probe)

## avoiding-over-and-under-caution

* panel-relevant translated nodes (consensus>=5): 3 — reference clauses with no translated span: 19 (structural ceiling, not a miss)
* agree relevant: 1
* seat engaged / panel cold: 15  <- adjudication queue A
* panel hot / seat declined: 2  <- adjudication queue B
* panel hot / never retrieved: 0 (after probe)


---

# Three-way adjudication (blind Fable adjudicators, 2026-08-16)

Protocol in `adjudication.json`: one clean context per behavior, document text
only, never shown the seat's or the panel's verdicts. Truth tier for the
cells above.

| cell | adjudicated | outcome |
|---|---|---|
| A: seat engaged / panel cold | 20 | **seat right 15/20** — the seat's extra engagements are mostly genuine relevance the panel's consensus>=5 tier did not cite |
| B: panel hot / seat declined | 11 | **seat missed 8/11** — a real seat-side recall gap (harm-avoidance 5/8, helpfulness 3/3) |

Reading: the pipeline's PRECISION survives blind adjudication against the
document; its RECALL misses are real and concentrated where the behavior's
atoms did not reach the node's vocabulary (the atom-granularity thread, not
the corpus). The panel is confirmed as an attention instrument: at its strict
tier it under-cites material a blind reader rules relevant.

# Verdict on "is the translated corpus usable for this check"

Yes. The disagreement structure decomposes into (a) panel-tier strictness
(seat vindicated), (b) seat recall on atom mismatch (a matching-layer fix,
not a translation fix), and (c) a structural coverage ceiling (26/44/19
consensus-tier reference clauses with no translated span) that more
translation directly removes.
