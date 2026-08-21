# EXTENSION ANNOTATION SEAT BRIEF — paste this whole file into a FRESH Claude session

Campaign: Arc1-b subtype mint (SUBTYPE_MINT_PREREG.md). You are ONE annotation
seat. The run needs TWO independent seats: run this brief twice, each time in
a fresh session with no shared state; the only difference is the SEAT number
you are given (first run: SEAT 1; second run: SEAT 2). Work blind: judge only
the document text against the two criteria. Do not read any repo file other
than the three packet files named below. Do not search for context.

## Input files (read all three, in order)
walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/
panel_run1/convergence/ctx_ext1.json, ctx_ext2.json, ctx_ext3.json
Each is a dict node_id -> {"span": ...}. In each span: everything after
"SOURCE TEXT (verbatim from the document..." is the document text you judge.
"ESTABLISHES" and "[node narrows this span to: ...]" are metadata — the
narrowing note tells you which sub-portion of the source text the node
covers; judge THAT portion. Ignore PROVIDES/NEEDS/CITATION instruction text.

## The two criteria (apply both to every node)
EXHIBIT (subtype exhibit:illustrate): "Annotate this act when the span is a
worked exhibit rather than a statement of the norm: it is headed 'Example'
(or equivalent) and/or contains a simulated exchange in speaker markup,
and/or carries GOOD/BAD/better-worse annotations on candidate responses. A
span that states a rule, condition, or rationale in the document's own voice
does not qualify, even when it gives illustrative parentheticals."

FORM-EQUIVALENCE (subtype provide:forbid.form_equivalence): "Annotate this
act subtype when the span states that changing the FORM of delivery does not
change how a rule applies -- that an encoded, obfuscated, indirect, partial,
translated, or different-modality rendering counts the same as the direct
one ('considered the same as', 'this includes depictions in text, audio, or
visual content', 'not merely a translation'). Do not annotate spans where a
change of form instead creates or expands a permission."

## Rules
- Judge FORM, not topic, for both criteria.
- A span mixing a stated rule with an embedded exhibit qualifies for EXHIBIT
  only if the node's covered portion is the exhibit part.
- When in genuine doubt, do NOT annotate (conservative).
- If a span's content is something you cannot process, do not stop and do not
  guess: put the node id in "refused" with a one-line reason and continue.

## Output (write BOTH files; SEAT = 1 or 2 as assigned)
panel_run1/convergence/mint_ext_seatSEAT_exhibit_illustrate.json:
{"seat": "extSEAT", "subtype": "exhibit:illustrate",
 "nodes_examined": <total nodes across the 3 files>,
 "annotated": {"<node_id>": "<quote max 25 words from the span showing why>", ...},
 "refused": {"<node_id>": "<reason>", ...}}
panel_run1/convergence/mint_ext_seatSEAT_form_equivalence.json — same shape,
"subtype": "provide:forbid.form_equivalence".
"annotated" is sparse: qualifying nodes only.

## Report when done
nodes_examined, annotated count + node ids, refused count + node ids, per
subtype. Nothing else.
