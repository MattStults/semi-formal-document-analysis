# graph_v2 — document-decomposition experiment artifacts (2026-08-10)

Everything produced by the decomposition-step experiments in one place. Committed and
published; superseded run artifacts were pruned with a manifest (see `PRUNED.md`).

## What is here

- `EXPERIMENTS.md` — the running experiment log: decisions with grounds, run log,
  pre-registered keys, Matt's rulings, test deviations. ⚠️ ~2,900 lines,
  chronological, and late entries RETRACT earlier ones (search "CORRECTION to
  this log") — reading it front-to-back as current state will mislead you.
  **Read the last six entries** (2026-08-14, from "ds7 PRODUCTION GRAPH --
  CERTIFIED" to the end) plus the named reports below, and treat everything
  earlier as history:
  - `production_certification.md` — the independent certification pass over
    `runs/ds7/root_graph.production.json` (offline, $0) and its numbered
    conditions.
  - `opus_recheck_report.md` — Opus recheck of the 61 quarantined ds7 verdicts
    under evidence prompts (zero API spend).
  - For the translation campaign that runs against this graph, the operating
    runbook is `../../TRANSLATION_RUNBOOK.md` (phase_1).
- `GRAPH_PROMPT_v2A..D.md` — single-agent prompt variants (v2D = final single-agent form).
- `RECURSE_PROMPT.md` — the shared brief for the recursive divide/leaf/unwind design
  (Matt's architecture). This is the current best prompt.
- `graph_check.py` — mechanical checks on any graph.json
  (`graph_check.py <graph> [span_hi] [span_lo]`). `division_check.py` — same for
  division.json (`division_check.py <division> <lo> <hi>`).
- `run1..run3/` — Haiku full-document single-agent runs (v2A/B/C). `run4/` — Haiku on
  slice L1-800 (v2D). `run5/` — Sonnet full document (v2D). `run2/graph_r2.json` — the
  pinned refinement-turn result; `run2/audit_1.md` its pinned work list.
- `recurse/` — the full recursion tree, one directory per tree node
  (`root`, `c1`, `c2`, `c21`, `c211`, ... ). Dividers hold `division.json`
  (children, seed_vocabulary, expected_cross_links, judgment_calls); every node that
  finished holds `graph.json` (nodes, uncovered, judgment_calls, cross_link_report at
  unwind levels). Node ids are span-prefixed (`L171-291_n008`) and stable across levels.

## Regenerating the line-numbered document

Line numbers everywhere refer to the RAW file
`specs/openai-model-spec/model_spec.md` (4691 lines), numbered consecutively:

```bash
python3 - <<'EOF'
src='specs/openai-model-spec/model_spec.md'
with open(src) as f, open('model_spec_numbered.txt','w') as g:
    for i,line in enumerate(f,1): g.write(f'L{i:04d}  {line}')
EOF
```

## State at final sync (complete)

The full tree is built and unwound. `recurse/root/graph.json` is the whole-document
graph: **593 nodes** (coincidentally the original clause-corpus count), 224 provided
names, 482 needs edges, 17 dangling entries over **13 final unresolved names**
(`final_dangling` in the file, each with grounds; `usage_policies` is the one true
external URL; the rest are section-anchor concepts no node explicitly provides —
contestable, recorded). The authority ordering is ONE multi-span node
(`L1-170_n028`, spans [69-101]+[183]+[186-191]) with 31 consumers; `chain_of_command`
is a root-added structure node (`L1-4691_n001_structure`). All mechanical checks:
0 bad line ranges (611 spans), 1 non-verbatim quote of 302 (L4251-4571_n026, known),
58/59 authority headings in nodes, 2 unaccounted lines of 3722. Scored against the
pre-registered root key in EXPERIMENTS.md (R1-R6): R1, R2, R5, R6 pass; R3 partially
(5 renames adjudicated, 7 kept dangling on name-level grounds — the residue is the
golden protocol's adjudication surface); R4 resolved via the structure node.

## Deployment note: prompt-cache structure (for DeepSeek / repeat runs)

The prompt content needs no change; the ORDER does. Every agent call must be:
  system prompt (or first user bytes) := RECURSE_PROMPT.md verbatim, byte-identical
  then the per-agent dispatch block (phase, span, workdir, seed source) LAST,
  then document text enters via tool results after that.
This makes the brief a shared cacheable prefix across all ~35 calls of a tree build.
The 2026-08-10 build did the reverse (dispatch first, brief via file read) and got no
cross-agent cache sharing. On DeepSeek, verify via prompt_cache_hit_tokens per response.

## Running the build on DeepSeek (phase_1 harness)

`recurse_driver.py` runs the RECURSE_PROMPT.md protocol as plain API calls on
the phase_1 provider harness (same DeepSeek-V4-Flash endpoint, key, prices,
and spend ledger as translate.py). Phase U's mechanical half is code; the
model only returns decisions, which are applied and re-verified (merge-loss
check included, RED-pinned in test_recurse_driver.py — 12 tests, suite-green).

```bash
VENV=../../../../../semi-formal-experiment/.venv/bin/python
$VENV recurse_driver.py --mock --doc toy_doc.md --out runs/mock --leaf-max 15  # free
$VENV recurse_driver.py --dry-run                    # plan + worst-case cost
TOGETHER_API_KEY=... $VENV recurse_driver.py --yes --out runs/ds1   # live
$VENV recurse_driver.py --yes --out runs/ds1         # resumes from artifacts
```

Worst-case estimate for the full model spec: ~$0.13/run (no cache credit
claimed). The system prompt is the brief verbatim on every call, so the
provider prefix-cache covers it; the run report prints the measured cache hit
rate from response usage. For a stability comparison against the 2026-08-10
Haiku tree, paste that build's root seed_vocabulary into driver_config.json's
root_seeds and diff the resulting trees.

## Translation sample (graph nodes -> ASP via translate.py)

`node_corpus.py` adapts graph nodes into a translate.py corpus without touching
any watched prompt file: each row's text carries the node's establishes, its
ASSIGNED provides/needs names (with prose), and the verbatim span text. The
emitted `config_graph_nodes.json` repoints only corpus/select/output dirs;
prompts, model, cost gates, and the spend ledger are phase_1's own.

Sample: 15 nodes, seed 42, stratified — the merged ordering node, an Under-18
delta, a heading-authority node, a section-lead provider, a usage_policies
needer, plus 10 random. Regenerate/resize: `python3 node_corpus.py [--n N|--ids ...]`.

```bash
cd ../..   # phase_1
VENV=../../../semi-formal-experiment/.venv/bin/python
$VENV translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --show-prompt 1  # free
TOGETHER_API_KEY=... $VENV translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --live
```

Scoring the sample (the coupling question): classify each failure as LOCAL
(schema/groundability/readback — leaf-time validation would have caught it)
vs LINK-level (requires/provides resolution — only visible post-unwind).
