# Delta-from-golden investigation (ds7 vs recurse/root golden)

Standing directive: every delta gets a why. Investigation date: 2026-08-14, fully
offline. Inputs: `runs/ds7/compare_vs_golden.json`, `runs/ds7/edge_similarity.json`,
`runs/ds7/root_graph.json`, `recurse/root/graph.json`, `graph_compare.py`,
`GRAPH_EQUIVALENCE.md`, `authority_convention.md`, `specs/openai-model-spec/model_spec.md`.
Headline numbers under investigation: nodes a=593 / b=773, 1:1 = 486, misaligned 91/272,
edge recall 0.369 / precision 0.050, uncovered jaccard 0.4954.

## 1. Golden's 91 misaligned nodes

Mechanical pass over all 91 + manual classification of a seeded random sample of 15
(seed 7: L2821-3040_n003, L1369-1413_n001, L292-526_n015, L797-809_n002, L1-170_n027,
L1-170_n031, L3756-3994_n009, L1-170_n034, L292-526_n001, L527-796_n011, L1-170_n028,
L3502-3755_n015, L171-291_n002, L1-170_n008, L1-170_n033).

Mechanical census of the 91:

| class | n | meaning |
|---|---|---|
| factored_overflow | 26 | ds7 factors the golden node into >=2 nodes fully inside its lines, union jaccard >= 0.6 — clean k-way splits that overflow the comparator's 2–3-node split/join window |
| authority_convention | 20 | golden per-section heading-authority nodes (incl. both zero-overlap nodes, e.g. `L2474-2575_n003` "Rules in the 'Do not lie' section are user-level principles"); ds7 encodes the same fact as a `needs: system_authority/...` on the section's content nodes plus shared convention nodes |
| partial_other | 45 | partial overlaps — in the manual sample these are the same splits with boundary offsets (golden spans swallow commentary/example lines ds7 excludes by policy; golden has some giant spans, e.g. `L1-170_n028` owning L69–191) |
| genuine no-content-anywhere | 0 | — |

Manual classification of the 15: **granularity difference 9** (e.g. golden
`L2821-3040_n003` = ds7 n004+n005+n006, the uncertainty rule-of-thumb factored into
rule + degree + impact; golden `L292-526_n015` prohibited-goals list = ds7 n002/n003/n004
per-item; `L1-170_n031/n033/n034` authority-level definitions each split in 2–3),
**authority-convention difference 4** (`L1369-1413_n001`, `L797-809_n002`,
`L3756-3994_n009`, `L292-526_n001` — all "this heading's rules carry authority X"
nodes; verified content-preserved, e.g. `#comply_with_laws` system authority survives as
`needs: system_authority` on all of `L797-830_n001..n007`),
**comparator quirk 2** (`L171-291_n002` is jaccard **1.0** with ds7 `L171-426_n001` yet
classed misaligned; `L1-170_n008` at 0.5), **substantive disagreement: 0** — in no
sampled case do the two graphs make different claims about the same text.

ds7's 272 misaligned are the mirror image: the shards of the same factorizations.
Line-mass keeps this honest: misaligned mass is only 7.1% (a) / 4.7% (b); 1:1 mass ~80%
on both sides.

## 2. Edge precision 0.050 — decomposition of the 5,774-edge denominator

`graph_compare.build_edges` resolves every need by bare name against every provider of
that name — fan-out is |needers| x |providers| per name. Bucketing ds7's 5,774
comparator edges by need-name class:

| bucket | edges | share | what it is |
|---|---|---|---|
| authority plumbing (`*authority*` names) | 5,354 | 92.7% | `root_authority` 2,167 (197 needers x 11 providers), `guideline_authority` 1,638 (x13), `user_authority` 1,331 (x11), `system_authority` 68, etc. The ds7 authority convention (autofix-canonicalized, EXPERIMENTS 08-13) deliberately shares 5 level names document-wide; the comparator multiplies them out. F4 authority-collapse was never built (EXPERIMENTS: "raw recall/precision stays plumbing-dominated ... never implemented") |
| `assistant_definition` fan-out | 224 | 3.9% | one provider (`L1-170_n065`), 224 needers — a seed-vocabulary term cited by every third node |
| content edges | 196 | 3.4% | real concept dependencies |

Golden's 512 edges are 21.5% authority (110) because it mixes shared names with
per-section coinages (per `authority_convention.md`, the convention ds7 was built to fix).

**Re-measured with authority names excluded**: a=402, b=420, recall 0.177, precision
0.176. Excluding `assistant_definition` too: a=402, b=196, recall 0.177, **precision
0.378**. So precision 0.050 is ~95% measurement artifact. The honest residual finding
runs the OTHER way: ds7 carries only **196 content edges vs golden's 402**, because ds7
exports only **92 distinct provides names (773 nodes) vs golden's 230 (593 nodes)**.
Genuine over-linking: not observed; the 7 lowest-sim surviving edges (edge_similarity
<0.10 = 7/1011 = 0.7%) went to K3, which upheld 3 and rejected 2 (2 no_verdict).

## 3. Uncovered-set difference (jaccard 0.4954)

only_b (uncovered in ds7, covered in golden) = 311 lines, classified by ds7's own
recorded uncover reasons: **256 blank lines, 20 admonition markers, 17 headings, 10
example markup, 3 fences** — golden swallowed these inside spans; ds7 excludes them by
explicit policy — and **4 unclaimed-content lines** (e.g. L716, autofixed after repair
non-convergence) + 1 judgment-call line. only_a = 125 lines golden left uncovered that
ds7 covers (commentary, xml examples, definition lines). Verified the scary-looking
case: heading L801 `#comply_with_laws authority=system` is "uncovered" in ds7 but its
authority semantics are fully captured (§1). **Net: ~98% coverage-policy difference, ~5
lines of real ds7 gap.**

## 4. Top 3 causes by mass

| # | cause | mass | classification |
|---|---|---|---|
| 1 | **Comparator authority/name fan-out**: shared authority-level names (5,354 edges, 92.7% of the precision denominator) + `assistant_definition` (224) multiplied into every needer x provider pair; plus ~20 of golden's 91 misaligned nodes being per-section authority nodes ds7 encodes as needs-links by mandated convention | ~5,578 of 5,774 edges; ~20/91 misaligned | **MEASUREMENT artifact** (the F4 authority-collapse the comparator never got) on the edge metric; the convention itself is BENIGN-BY-PROTOCOL (Matt-approved restructure, EXPERIMENTS 08-13) |
| 2 | **Granularity: ds7 factors finer** (773 vs 593 nodes; 26 clean factored-overflow + most of the 45 partials of golden's misaligned; ds7's 272 misaligned are the shards) | ~70/91 golden misaligned, ~250/272 ds7 misaligned, yet only 4.7–7.1% line mass | **BENIGN-BY-PROTOCOL** (GRAPH_EQUIVALENCE split/join rule; the comparator's 2–3-node window under-groups k-way splits, so part is also MEASUREMENT). 0 substantive disagreements found in the 15-sample |
| 3 | **ds7 provides under-export**: 92 exported concept names vs golden's 230 → content-edge recall 0.177 (196 vs 402 content edges) and ~50 of the 64 "honest danglings" reference real content that exists as ds7 nodes with empty `provides` (e.g. `L1542-1706_n013` self-harm rule, `L3383-3501_n001..4` interactive-vs-programmatic) | ~206 missing content edges; ~50/64 danglings | **ds7 DEFECT** (the one real one). Not content loss — the claims are all present as nodes — but the cross-link vocabulary is too sparse, which is exactly what a steps-1-4 consumer traverses |

(Cause 4, below threshold: golden's own quirks — swallowed blank/markup lines, giant
spans like L69–191, per-section authority coinages — **GOLDEN defects**; the golden is
Haiku-built and not sacred. They inflate only_a/misaligned counts marginally.)

## 5. Recommendation (per rulings #3/#4)

Ruling #3: the graph as close to correct as we can make it via a repeatable recorded
process. Ruling #4: production = highest-quality DeepSeek graph + frontier-level fixes.

**Nothing in the node/coverage/edge deltas blocks ds7+fixups as the production graph** —
causes 1 and 2 are measurement artifacts and protocol-sanctioned conventions, and the
alignment evidence (486 1:1, ~80% line mass, 0 substantive disagreements in sample,
edge-sim <0.10 only 0.7%) supports acceptance. **Two items DO belong in the fix round
before the "production" stamp, both already in-scope under ruling #4:**

1. **The provides under-export (cause 3).** The 52-item fixup queue (esp. the 40
   frontier-confirmed broken promises) plus the ~50 dangling needs naming unexported
   content are one defect class: concepts present as nodes but absent from the
   resolution vocabulary. A bounded, recorded frontier-seat pass that adds `provides`
   exports / resolves danglings against named existing nodes is exactly ruling #4's
   "frontier-level fixes". Without it the graph's cross-link layer is materially
   thinner than the golden's (196 vs 402 content edges).
2. **Measurement hygiene, not graph change:** build the F4 authority-collapse (or adopt
   the authority-excluded numbers above: recall 0.177 / precision 0.378) so the recorded
   quality numbers for the production package aren't dominated by plumbing; and note the
   1.0-jaccard-yet-misaligned comparator quirk (`L171-291_n002`) as a known
   graph_compare classing artifact.

Everything else observed is benign-by-protocol or golden-side, with the why recorded
above.
