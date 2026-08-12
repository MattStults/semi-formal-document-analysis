# VERDICT (l1108_1368_n004-20260810-213258)

Diagnosed 2026-08-10, worked-example iteration loop (graph_v2/EXPERIMENTS.md, 'TRANSLATION SAMPLE RUN/RERUN' and 'RUNS 3-5').

## class: sample-scope-dangling
NOT a defect: `requires` names a provider node that exists in the full graph but is outside this 15-node sample, so the link-scope note fires. Verified against recurse/root/graph.json at diagnosis time (run-1 analysis, EXPERIMENTS.md 'TRANSLATION SAMPLE RUN').

**Fix:** None needed; disappears at full-graph scope. The note class (severity=note) never alone blocked a module.

## class: concept-declared-note
Note-severity: a head-less concept declared in the concept table -- informational in link scope, not a module defect.

**Fix:** None due.
