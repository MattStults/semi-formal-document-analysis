# VERDICT (L3384-3501_n007-20260810-204357)

Diagnosed 2026-08-10 as part of the worked-example iteration loop (see graph_v2/EXPERIMENTS.md, sections 'TRANSLATION SAMPLE RUN/RERUN' and 'RUNS 3-5').

## class: asp-unsafe-id-or-syntax
Run-1/2 class: graph ids (L527-796_n012) are not valid ASP constants (uppercase = variable, hyphen = subtraction), so every module with an assert rendered an unparseable program; plus kindred clingo syntax errors from the same runs.

**Fix:** asp_id() aliasing in node_corpus.py (l527_796_n012); verified by the worked-example render gate. Extinct from run 3 on.
