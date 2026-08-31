# ARTIFACTS — routing table

Every star artifact, one line each. Paths are repo-relative; all verified at
publication. `BP/` abbreviates
`walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/`.

| Artifact | What it is | Path | Read this if you want |
|---|---|---|---|
| The ledger | Append-only research log, entries 0000–0043, errata included | `BP/ITERATION_NOTES.md` (root link: `LEDGER.md`) | the whole arc-2 story as it happened |
| Arc-2 handoff | Current state in one ⭐⭐ block (rest is archive) | `BP/HANDOFF_CURRENT.md` (root link: `ARC2_HANDOFF.md`) | where things stand |
| L1/L2 adversarial review | 36-finding review that killed the licensing experiments | `BP/L1L2_ADVERSARIAL_REVIEW.md` | what adversarial review looks like here |
| L1/L2 disposition | Per-finding verdicts with independent re-derivations | `BP/L1L2_REVIEW_DISPOSITION.md` | how findings get accepted or corrected |
| Census disposition | The withdrawal of the separability "pass" (0041) | `BP/RETRANS_REVIEW_DISPOSITION.md` | the random-partition-null rule's origin |
| Error calculus | The repair state machine (partition theorem, router, amendments) | `BP/ERROR_CALCULUS.md` | the formal repair framework |
| Calculus runbook | Execution-derived runbook, docs-tested | `BP/CALCULUS_RUNBOOK.md` | how the calculus actually runs |
| Behavior-pilot index | Which of the 348 files there are human-authored vs generated | `BP/README.md` | orientation in the arc-2 directory |
| Arc-2 engine | Relevance instrument + census over the translated corpus | `BP/relevance_by_act.py`, `BP/satisfiability_census.py` | the arc-2 code that runs |
| Campaign log | Graph-translation campaign: audits, repairs, convergence | `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/EXPERIMENTS.md` | arc-2 build history |
| The certified graph | 773 nodes, zero bad spans of 846 | `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.production.json` | the arc-2 substrate |
| Prune manifest | What was removed at publication, pinned by git object id | `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/PRUNED.md` | what was removed and how to restore it |
| Arc-1 handoff | Arc-1 state and corrected benchmark history (⭐⭐ block) | `semi-formal-experiment/HANDOFF.md` | arc-1 results with their corrections |
| Module map | What every arc-1 module is; §11 anti-rules | `semi-formal-experiment/MODULE_MAP.md` | how to run or change arc-1 code |
| Reproducibility rules | Sandwich rule, constant governance, determinism | `semi-formal-experiment/REPRODUCIBILITY.md` | the discipline in 138 lines |
| Cycle design | How a change cycle runs (ceremony, reviews, close) | `semi-formal-experiment/CYCLE_DESIGN.md` | the change process |
| The reverted cycle | Metric said ship; adjudication found deleted de-escalation guidance | `semi-formal-experiment/cycles/patient-pricing-2026-08-04/decision.json` | why per-flip adjudication exists |
| Governance model | Seats/tiers as a queryable ASP program | `semi-formal-experiment/machine/` (`query.py seats`) | the process as a logic program |
| Spec citation engine | Locator → verbatim text for both specs | `engine/spec-cite/cite.py` | the citation discipline |
| Citation convention | The locator format the whole repo uses | `specs/CITATION.md` | how citations are written |
| Panel roster | The three-behavior frontier-panel verdicts (arc-1 comparator) | `data/behaviours.json` | the calibration instrument |
| Panel v5 | 9 behaviors × 589 passages, externally authored (Apache-2.0) | `data/panel-v5/runlog-v5.jsonl` | the untouched replication tier |
| Agent brief | Canonical instructions for agents and new contributors | `AGENTS.md` | to work in this repo |
