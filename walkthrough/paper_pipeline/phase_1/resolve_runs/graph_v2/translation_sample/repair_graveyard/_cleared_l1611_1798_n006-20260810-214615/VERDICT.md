# VERDICT: craft-slip class, addressed by the run-5..8 prompt/example fixes

Status: unrepaired (3 attempts, 2026-08-10 era).

Evidence (this entry's own findings):
- `clingo-error`: clingo refused this program, so nothing below was actually analysed: /var/folders/jh/ym8tv1sn29dbxk49v5wbp4s40000gn/T/stage2_checks_uzvuzxbq/l1611_1798_n006.lp:60:1-66: error: unsa

Diagnosis: single-instance ASP craft slips (unsafe variables / non-verbatim quotes) from the pre-run-8 prompt. The class fixes are the node worked example + output-format rules landed through run 8 (13/15) and the 2026-08-12 stage-2/stage-4 fix stack (EXPERIMENTS.md). Disposition: cleared; the 2026-08-12 small-set rerun is the regression test for this class.
