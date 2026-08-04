# The disagreement-autopsy seat: cause attribution over audit dossiers

Why this seat exists: two tool-vs-panel disagreements were debugged by hand
(DISAGREEMENT_REPORT.md, DISAGREEMENT_REPORT_ext_v1.md) and each yielded a
mechanical cause. ~294 disagreements exist under the current configuration.
This seat scales the same autopsy: one AUDIT DOSSIER per disagreement
(deterministically produced by `audit_disagreements.py dossiers`), one verdict
per dossier attributing a CAUSE from a closed taxonomy, all verdicts checked
mechanically by `audit_disagreements.py validate`.

## What this seat sees, and the fence

**THIS SEAT SEES PANEL VERDICTS BY DESIGN.** Unlike the flip adjudicator,
whose dossiers contain no label by construction, your dossier shows the
judges' per-judge verdicts and the panel score — you cannot attribute the
cause of a disagreement without knowing what the disagreement is. The fence
here is **DISCLOSURE, not blindness** (contract §5 invariant 9 bars fitting,
not measuring): the verdicts may inform your cause attribution and your side
judgment, but **nothing from this seat may edit a vocabulary, a query, a
weight or a threshold directly**. Your output is a measurement of failure
modes. Any fix must be independently motivated by document-side evidence and
must route through the iteration loop's own label-free instruments
(ITERATION_LOOP.md: labels direct ATTENTION, never TRUTH). "Fix these
dossiers" is never a change justification.

## Input and output

**Input:** exactly one dossier (one JSON file from
`audit_dossiers/<config-tag>/`, enumerated by `index.jsonl`). It is
self-contained: the passage (id, quote, panel score, per-judge verdicts), the
kind (FN = panel relevant / tool silent; FP = tool predicted / panel low),
all mapped clauses with raw and normalized scores, the behaviour's full query
atom list, and — for the max-scoring clause — its text, its atoms
(name/kind/gloss/role), the scorer's own explain() (channels, shares, matched
atoms, top lexical terms), plus the COMPUTED DISCRIMINATORS:

- `atom_channel_zero` — the ontology channel contributed exactly 0.0;
- `exact_name_intersection` — query atom names that literally matched;
- `stem_family_adjacency` — query atoms sharing a stem head with a
  differently-named clause atom (right-headed-compound heuristic,
  head_induction_probe.py's convention over `grammar.stem_of`): the
  "family present, names cannot meet" fingerprint;
- `join_fanout` — how many clauses the quote-containment join mapped this
  passage to; `degenerate: true` above 5, with the quote length that usually
  explains it;
- `distance_to_cut` — max normalized score minus this behaviour's derived
  (Otsu) cut: negative for an FN, small magnitude means a threshold story;
- `channel_shares` — which channel carried the max clause's score.

If something you need is missing from the dossier, that is a tooling bug —
say so in the note and escalate; do not reconstruct it from memory or from
the repo. No repo exploration: the dossier is your entire evidentiary basis.

**Output:** one record per dossier, appended to a JSON list:

```json
{"dossier_id": "<copied verbatim>",
 "cause": "<one taxonomy member>",
 "side": "tool" | "panel" | "both_defensible",
 "note": "<one or two sentences citing the dossier facts you used>",
 "sweep_core_evidence": ["<atom>", ...]   // optional, see fn_family_unselected
}
```

Every dossier in `index.jsonl` exactly once; closed vocabularies; the
validator refuses inconsistent files loudly.

## The cause taxonomy (closed — the same text ships as
`audit_disagreements.CAUSE_TAXONOMY`)

FN causes (panel relevant, tool silent):

- `fn_family_absent_from_vocabulary` — the concept has NO atom family in the
  clause-side vocabulary; no annotation could have carried the match.
  Signature: atom_channel_zero, empty intersection, empty adjacency (a
  nonempty adjacency refutes this cause — a family member exists).
- `fn_family_unselected` — the vocabulary HAS the family; the query's
  selection never reached for it (the ext_v1 FN: manipulation family on the
  clause side, none among the query's atoms). Signature: nonempty
  stem_family_adjacency, OR cite a select_audit score-3 in_scope_unselected
  finding in `sweep_core_evidence`.
- `fn_names_cannot_meet` — both sides hold atoms for the concept under
  different names (coined compound vs generic sibling); exact-name
  intersection cannot connect them (the b8 FN). Signature:
  atom_channel_zero, empty intersection, typically nonempty adjacency.
- `fn_kind_or_patient_discount` — names DO meet but the match under-scores
  (kind mismatch discount, stopworded/low-IDF atoms, missing patient
  structure). Signature: nonempty intersection, total still below the cut.
- `fn_threshold` — the match is real; the derived cut landed just above it.
  Signature: |distance_to_cut| <= 0.10.

FP causes (tool predicted, panel low):

- `fp_promiscuous_atom` — patient-free / stock atoms fired on a clause about
  a different party or subject (the b8 FP). Signature: nonempty
  intersection carrying the score.
- `fp_section_prior` — the score is mostly inherited section proximity.
  Signature: section is the dominant channel share.
- `fp_lexical_only` — no atom matched; shared vocabulary without shared
  concept. Signature: atom_channel_zero, lex share >= section share.
- `fp_join_artifact` — a degenerate quote mapped to many clauses and the
  passage inherited another clause's score (the ext_v1 FP: header-only quote
  -> 28 clauses). Signature: join_fanout > 5 (dossier flags it).
- `fp_threshold_drift` — a weak honest score the cut happened to admit.
  Signature: |distance_to_cut| <= 0.10.

Either kind:

- `boundary_dispute_tool_defensible` / `boundary_dispute_panel_defensible` —
  no mechanical defect; a genuine relevance-boundary judgment call, decided
  by the side question below. Side must match the cause name.
- `unexplained_escalate` — see the escalation rule.

## The escalation rule

If the dossier's facts fit no cause above, the verdict is
`unexplained_escalate` with a note describing what you observed. **Never
force-fit**: a wrong cause silently corrupts the failure-mode counts this
instrument exists to produce, while an escalation is a finding in its own
right (either a taxonomy gap or a tooling gap — both worth knowing).
Unmapped passages (join_fanout 0: the join found no clause at all — a
segmentation-coverage gap, deliberately outside this taxonomy) always
escalate; the validator enforces this.

## The side question (tight)

`side` answers: whose verdict would a careful auditor endorse on this
passage? Use the flip adjudicator's standard, held equally tight here
(briefs/flip_adjudicator.md — the volume-ratchet warning applies):

> **Would a careful auditor of this behaviour need this passage?** On a
> plain reading of the passage text, does it concern the behaviour's subject
> matter, such that an auditor compiling everything the document says about
> the behaviour would have to include it?

- Auditor needs it and the tool missed it (FN) → side `panel`.
- Auditor does not need it and the tool predicted it (FP) → side `panel`.
- The tool's call is the one the auditor-need reading supports → side
  `tool` (this happens: a panel judge can be generous or stray).
- The text genuinely supports both readings → `both_defensible`.

Hold it at "would NEED", never "might find vaguely related". Note that
`side` is about the passage-level verdict; `cause` is about the mechanism —
a tool that was wrong for a mechanical reason still gets its mechanical
cause, and a tool that was right can still carry a cause (e.g. a defensible
FP admitted by threshold drift).

## What this seat's output may cause

Counts by cause over the full dossier set are the deliverable: they say
which layer (vocabulary, selection, matcher, join, calibration) owns the
disagreement mass, which is what prioritizes the next loop iteration. What
the output may NOT do: justify editing any query-side artifact to flip
specific dossiers — that is fitting to the panel through a 294-sample
keyhole, differing from the two-sample version only in size.

Small-model standard applies (briefs/README.md): each attribution is an
atomic judgment over stated facts; small-vs-frontier divergence on the same
dossier is a defect in this brief or in the dossier, and the first check is
the blind validation against the hand-debugged cases in
DISAGREEMENT_REPORT.md / DISAGREEMENT_REPORT_ext_v1.md.
