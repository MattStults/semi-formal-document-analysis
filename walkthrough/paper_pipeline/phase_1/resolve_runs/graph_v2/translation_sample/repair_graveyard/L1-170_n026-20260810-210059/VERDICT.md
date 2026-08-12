# VERDICT (L1-170_n026-20260810-210059)

Diagnosed 2026-08-10, worked-example iteration loop (graph_v2/EXPERIMENTS.md, 'TRANSLATION SAMPLE RUN/RERUN' and 'RUNS 3-5').

## class: identity-mismatch
One-off: the model wrote a fabricated clause_id ('L61') instead of the asked id -- an early symptom of the run-1/2 citation-and-id confusion on pre-asp_id corpora.

**Fix:** CITATION contract + asp_id() aliasing; the class did not recur after run 3.
