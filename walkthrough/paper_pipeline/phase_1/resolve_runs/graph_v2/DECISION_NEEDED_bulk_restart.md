# DECISION NEEDED (Matt, Monday): restart chunks 2–6, and under what regime?

State when you left: bulk run launched, D1 rule countersigned (breach →
investigate → verify fix → restart). What happened overnight is the full
record in `semantic_audit.json`, `RUNTIME_WATCH.md`, and the commit log;
this file is only the decision.

## The facts

* Chunks 0–1 are DONE: 172/180 translated, 2 abstained, 6 graveyarded,
  ~$0.83. Chunks 2–6 (≈420 nodes) are HELD as `.hold` files.
* Chunk 0's blind audit breached the floor: **5/15 faithful (33%)** —
  the earlier 92% was cohort bias (simple structural nodes); complex
  conditional/agentic clauses are where DeepSeek breaks.
* The D1 fix loop ran TWO iterations. Verified fixed (prompt-level):
  modal downgrades, unless-negation, until-conditions, PROVIDES-definition,
  concepts-as-declaration freezes — iteration-1 cohort went 7/12 faithful.
  **Not fixable by prompting** (recurred through explicit failure-mode
  entries naming them): refusal-as-prefer inversion (three consecutive
  times on one clause), condition-voiding single-literal derivations,
  status flips under negated guards.
* Where instruction failed, DETECTION was added: three new hard-tier gate
  checks catch **10/23 known defects (43%) at ~83% precision** — every
  inversion instance flagged; read-required classes still need sampling.
* A frontier repair pass over all 8 known-defective latest artifacts is in
  flight (surgical field-level fixes per the auditors' findings, blind
  re-audit to follow). If it verifies, the KNOWN defect set goes to ~0;
  the open question is only the rate among unaudited modules.
* Spend ~$14.7 of $25. DeepSeek ×5 on Tuesday: finishing later multiplies
  the remaining ~$2 to ~$10.

## The options

**A. Restart under the amended prompt + detection net + repair pipeline.**
Chunks 2–6 (~$2 now), every module through the gate incl. the three new
checks, flagged modules frontier-repaired (the pass running now is the
prototype), random sampling continues as the miss-rate floor. Accepts a
residual UNDETECTED defect rate on hard clauses — best estimate 10–25% of
the read-required classes on conditional/agentic nodes, concentrated where
the audit found them. Full coverage removes the equivalence prereg's
structural ceiling.

**B. Panel-first partial restart.** Translate only the pilot/panel gap
regions (~150 nodes, ~$0.7), frontier-repair intensively there, leave the
long tail for a drafter-tier decision later (at 5× or with a better cheap
model). Value-dense: the deliverable needs those regions, not all 773.
The prereg then reports a larger stated coverage ceiling.

**C. Hold everything for your review.** Cleanest procedurally; the
remaining ~420 nodes cost ~$10 instead of ~$2 whenever translation resumes.

**My recommendation: A**, because the marginal $1.3 over B buys the
equivalence measurement its full denominator, the residual-defect risk is
bounded by detection + sampling + repair rather than assumed away, and the
per-flip philosophy holds (every kept module is either audited, gate-clean,
or repaired-and-re-audited — nothing is kept on the aggregate's say-so).
But the floor rule is countersigned and restarting below a verified floor
is your call, not mine — which is why the chunks are still `.hold` and this
file exists.

To restart on A: `for f in bulk_chunk_0*.hold; do mv "$f" "${f%.hold}"; done
&& nohup ./bulk_run.sh >> bulk_run.log 2>&1 &` (the loop now re-globs per
iteration; the $57.86 near-miss that motivated that fix is in the log).
