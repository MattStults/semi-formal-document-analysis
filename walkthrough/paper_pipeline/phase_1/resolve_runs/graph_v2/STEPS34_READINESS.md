# Steps 3–4 readiness on graph-node modules (2026-08-11)

First cross-module LINK over node translations ran today (`link_nodes.py`,
14 translated modules of 593 graph nodes, `link_nodes_report.json`).

## Step 3 — link (`walkthrough/link.py`) — MECHANICAL (clingo subprocess)
Needs: the corpus's `.lp` paths + one merged concept table (`collect(paths,
concepts=rows)`). Node rows lack: real `section_id`s/anchors (all rows say
`graph_node`, `section_path=[]`), so link's L1 anchor-graph layer is inert on
node corpora — L2 (unresolved predicates) carries everything.
Measured on the real corpus: `#const onto = on.` is emitted into EVERY module
by `schema.render_lp`, and at corpus scope clingo refuses the redefinition and
analyses NOTHING. `link_nodes.py` dedupes it as a workaround; after dedup:
0 unresolved-reference errors, 1 closure-conflict error (`follow_instruction`
declared cepa in l527_796_n022 vs cnpa in l1_170_n026), 3 concept-multi-gloss
notes (same name, different written meanings: `overrides/2`,
`real_world_ties_principle/1`, `stay_in_bounds_principles/1`), requires
resolution 1/28 in-corpus — expected: most providers are simply untranslated.

## Step 4a — readback R1/R2 (`readback.py`) — MECHANICAL to render;
the four seats that JUDGE the artifact (`seats.py`) are model-bound and want
`dispatch_core` concurrency. Entry: `render_module(mod, extra_gloss=,
clause_quote=)` over a validated `schema.Module` — rebuild from the node
`.json` via `schema.validate_all(obj, cid, known_ids)`. Node-corpus gaps:
(a) `clause_quote` for RB4 echo — the node row's `quote` is the PACKED PROMPT
(scaffold + names + span text), not the source span, so RB4 measured against
it is distorted; feed span text only; (b) `requires` predicates are glossed in
the PROVIDER module's concept rows, so `extra_gloss` must come from the merged
corpus table (`readback.gloss_from_rows`) or every cross-node name is a
`readback-ungloss` error.

## Step 4b — readback R3 (`readback_r3.py`) — MECHANICAL (xclingo, in venv).
Entry: `render_r3(mod, situations, link_texts=)`; `situations` is
`probe.ProbeReport.covering` — a STAGE-3 artifact that does not exist for any
node module yet (no probe run over the node corpus). `link_texts` must be the
sibling providers of the module's `requires` — exactly the scope
`link_nodes.py` now computes — and the same `#const` dedup applies or xclingo
inherits the redefinition refusal. R3 refuses `_` anywhere in the link scope;
node modules pass `schema.py`'s ban, but any hand-written link glue must too.

## Integration gaps before a full-corpus run, ranked
1. **Shared preamble collision** — ✅ CLOSED 2026-08-11. The fix lives at
   corpus assembly, not emission: `link.SHARED_PREAMBLE` names the two lines
   `render_lp` emits into every ontology-bearing module (`#const onto = on.` /
   `o :- onto = on.`), and `link.collect` dedupes exactly those — nothing
   else — via `link.dedupe_shared_preamble` when linking >1 file. A genuine
   non-preamble `#const` redefinition still errors (pinned:
   `walkthrough/test_link.py` corpus-scope tests + `link.py --self-test`
   (k1)/(k2)). `render_lp` and the single-module path are byte-untouched;
   `link_nodes.py`'s local strip is deleted and its numbers reproduce
   (0 unresolved, 1 closure-conflict, requires 1/28). R3's `link_texts` can
   now reuse the same helper. ⚠️ Known residual: pyclingo caps diagnostics at
   20 messages, so WHICH declared head-less names surface as notes at corpus
   scope is truncated (verified via the clingo API with the cap lifted: 36
   unique head-less atoms, every one declared — the 0-unresolved result is
   real, not a cap artifact).
2. **Cross-node concept reconciliation** — same predicate, different glosses
   (3 cases in 14 modules) and one closure conflict; needs a corpus-level
   merge/rename policy before requires-resolution numbers mean anything, and
   before readback glosses can be borrowed across modules (gap 4a-b).
3. **Stage-3 situations for nodes** — R3 has NO input until probe runs over
   node modules with their provider link scope; wire probe to the
   `link_nodes.py` module set first, since scope is what probe solves over.
4. **RB4 quote source** — carry the raw span text in the corpus row (or read
   it back off `locator`) so echo is measured against the document, not the
   prompt scaffold.
5. **Anchors/section ids** — decide whether node rows should carry real
   section ids so link L1 and section-scoped selection work; today they are
   placeholders (`graph_node`).
