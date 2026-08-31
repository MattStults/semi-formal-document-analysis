# Semi-formal document analysis

A label-free tool that answers *which clauses of a model spec bear on a given
behavior?* mechanically: read the document once into a symbolic representation,
then answer deterministically, with a citable span and a stated reason for every
hit. Frontier-model panels were the calibration instrument — the tool should
match the panel, or give an answer a frontier model would accept as justifiable.

Six weeks; it did not reach that bar. This repo is the complete record of the
attempt: the machinery, the measurements, and the discipline that kept the
measurements honest — including the results that were withdrawn when adversarial
review showed they were noise. The full commit history is published unrewritten
so that every dated claim, pin, and withdrawal is externally checkable;
operational details (usage plumbing, working notes) were redacted in the
current files and remain in history by choice. The write-up is in two blog posts:
[the retrospective](#) and [where the work goes next](#) *(links added at
publication)*.

What held up and what didn't, in one paragraph: the symbolic engine (ASP/clingo
evaluation, conflict enumeration with witness scenarios, satisfiability checks)
worked — its failures were refusals, not wrong answers. Segmentation of both
specs into typed clause inventories worked after repair. Matching behaviors to
passages did not beat a single frontier judge; an ontology open-coded from 100
behavior definitions covered every sampled span but failed every separability
test once a matched random-partition null was run against it. The measurement
discipline — pre-registered predictions, blind adjudication seats, adversarial
review before every close, an append-only ledger with an erratum list — is the
part that transferred: it caught and withdrew three headline claims, and it is
the reason the numbers in this repo can be read at face value.

## Start here (5 minutes)

Everything below is deterministic re-analysis of committed data: no API keys, no
network, no model calls.

```bash
# 0. environment check (~3 s; full setup: bash setup_env.sh)
bash setup_env.sh --check

# 1. every claim about a spec resolves to verbatim text
python3 engine/spec-cite/cite.py outline model-spec
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"

# 2. the 773-node document graph, every span checked against the source
python3 walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/graph_check.py \
  walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.production.json

# 3. the measurement instrument, and its recall ceiling (98.4% join, misses printed by name)
cd semi-formal-experiment && .venv/bin/python measure_join.py

# 4. the arc-1 headline result, reproduced from disk (MCC by threshold, true vs published universe)
.venv/bin/python benchmark.py --tool --annotations annotations_b8.json --behaviour-atoms behavior_atoms_b8.json

# 5. the governance model as a queryable logic program (note the seat it reports as unvalidated)
.venv/bin/python machine/query.py seats
```

(`machine/check_model.py`, the companion source-check for step 5, also runs
clean — all four checks pass.)

## Two arcs

| Arc | Where | What |
|---|---|---|
| 1 (July–early Aug) | `semi-formal-experiment/` | Constitution pilot (616 clauses, 16-rule ASP fragment, conflict enumeration, expressibility triage) and the Model Spec relevance benchmark against a frontier-judge panel on the full 589-passage universe. |
| 2 (mid–late Aug) | `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/` | Document-graph translation (773 nodes), panel-adjudicated repair iterations, minted-dimension experiments, the query-class ontology study, and the adversarial reviews that ended the headline claims. |

The two share a corpus and nothing else. Different representation, different
failure modes, different evidence.

## Reading order

1. The blog retrospective *(link at publication)* — the narrative.
2. [`ITERATION_NOTES.md`](walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/ITERATION_NOTES.md)
   (also linked as `LEDGER.md` at root) — the append-only ledger, entries
   0000–0043: every step, every erratum, every withdrawal, written at the time.
   This is the primary artifact.
3. [`L1L2_ADVERSARIAL_REVIEW.md`](walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/L1L2_ADVERSARIAL_REVIEW.md)
   and [its disposition](walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/L1L2_REVIEW_DISPOSITION.md)
   — what a withdrawal looks like here: the review, the independent
   re-derivation of each decisive finding, the corrected verdicts.
4. [`semi-formal-experiment/REPRODUCIBILITY.md`](semi-formal-experiment/REPRODUCIBILITY.md)
   — the sandwich rule, constant governance, determinism requirements.

For depth after those: `semi-formal-experiment/MODULE_MAP.md` (§0 how to run
anything, §1b what each module is, §11 anti-rules — read before "fixing"
anything that looks wrong), `semi-formal-experiment/CYCLE_DESIGN.md` (how a
change cycle runs), and the two handoffs — `ARC2_HANDOFF.md` (root link) and
`semi-formal-experiment/HANDOFF.md`. **Read only the top starred block of each
handoff**: everything below is stacked historical state, self-marked and partly
superseded — an archive, not a read.

`ARTIFACTS.md` at root is the full routing table.

## Results, and what was withdrawn

Arc-1 benchmark (Model Spec, 589-passage universe, MCC): the tool reached
+0.32 in-sample (+0.278 label-free); the frontier judges' leave-one-out mean was
+0.555, and the judges beat the tool in all nine behavior-gold cells at the
judge's own false-positive rate. Arc-2 repair loop (engaged precision, one
behavior): 0.40 → 0.70 → 0.55 → 0.85 across four adjudicated attempts — with
the ledger's own honest headline being recall, not precision (23 of 40 declined
passages were panel-relevant).

**Withdrawn, by its own review process:**

- The separability census ("integration test passed") — withdrawn in
  `bf0d4978`: its pass condition was satisfiable by noise (random partition
  passed 299/300 trials); relevance prediction over the representation ran at
  base rate.
- The L1/L2 licensing experiments — withdrawn in `365d68b3`: DOES-NOT-LICENSE;
  one bar was already met by numbers indistinguishable from noise, the other
  had no null.
- The query-class saturation claim — bounded in `1143a921` (erratum #20): the
  "no new places" result was relative to the designer's own vocabulary, not the
  question space.

The binding rule that came out of these: a separability claim is only as strong
as its margin over a matched-granularity random-partition null, and a pass
condition that cannot fail is void.

## Running it

```bash
bash setup_env.sh            # creates semi-formal-experiment/.venv from requirements.txt
bash setup_env.sh --check    # verifies, ~3 s

cd semi-formal-experiment && .venv/bin/python -m pytest -q
# 2,270 passed, 1 skipped (4-10 min depending on machine; measured 2026-08-30)

cd ../walkthrough && ../semi-formal-experiment/.venv/bin/python -m pytest -q
# arc-2 suite; see CI for current counts
```

CI runs both suites plus the citation and graph checks from the demo path on
every push *(badge added at publication)*.

⚠️ **Two different files are named `behaviours.json` and they are NOT
interchangeable** — `data/behaviours.json` (the panel roster) and
`engine/panel/behaviours.json` (the vendored harness's own copy); the
experiment's query-side definitions are a differently named third file:
`semi-formal-experiment/behaviours_query.json`. Loading the wrong one produces
a silently de-behaviourised score.

## Layout

```
engine/            spec-cite (locator → verbatim text) and the vendored panel harness
specs/             the analyzed source documents, with their upstream licenses
data/              panel verdicts (roster + panel-v5) and coverage artifacts
semi-formal-experiment/   arc 1: DSL, checker, translator, benchmark, cycles, machine/
walkthrough/       arc 2: graph pipeline, runs, behavior_pilot/ (see its README)
ARTIFACTS.md       routing table for every star artifact
LEDGER.md          → the arc-2 append-only ledger (symlink)
ARC2_HANDOFF.md    → the arc-2 handoff (symlink)
```

Large superseded run artifacts were pruned for publication with a signed
manifest — see
[`PRUNED.md`](walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/PRUNED.md)
for what was removed and how to restore any of it from history.

## Third-party content

- `specs/openai-model-spec/` and `specs/claude-constitution/` are CC0 1.0
  public-domain documents, redistributed with their upstream licence statements and README
  files intact, for reproducibility of the clause inventories.
- `data/panel-v5/` redistributes data from
  [ai-character-index](https://github.com/AndresCotton/ai-character-index)
  (Andres Cotton), Apache-2.0 — see the LICENSE and NOTICE files in that
  directory.

Everything else: MIT (see `LICENSE`).

## For agents

`AGENTS.md` (symlinked as `CLAUDE.md`) is the canonical brief: read it before
acting in this repo.

## What this repo does not establish

That the approach is impossible. The withdrawn results are defects in
measurements, not proofs about the ontology. It establishes that the specific
demonstrations attempted here did not survive their own review process, and it
documents that process well enough to be reused. Claims are scoped throughout:
every separability claim requires its null; every "unresolved conflict" is a
claim about an encoding and a fragment, not about the document.
