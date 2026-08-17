# Stage-4 semantic audit — the go/no-go for the bulk run (2026-08-16)

Matt's challenge, verbatim in spirit: the panel-agreement adjudication
validated node RELEVANCE (prose), not ASP fidelity — so what is the semantic
confidence in the translations the bulk run is mass-producing? This audit is
the answer, run while chunk 0 sat in the batch queue, with the pre-declared
rule: **new-prompt cohort ≥85% faithful with no dropped obligations in the
faithful set → bulk continues; below → pause and wait for the owner.**
**COUNTERSIGNED (Matt, 2026-08-16), with one amendment: a breach does not
end in a parked pause. The standing rule is investigate → verify a fix on
the failing sample → restart.** A pause is the state while the fix is being
verified, not the destination; only a fix that cannot be verified leaves the
run stopped for the owner.

Protocol: blind Fable-tier auditors, one per cohort, never shown gate
results or each other's work. Per module: read the module JSON and its span
(`prompt_user.txt`), report DROPPED / INVENTED / WRONG-POLARITY / HOLLOW
normative content with the decisive words quoted. Strict on content, lenient
on style. Raw verdicts: `semantic_audit.json`.

## Results

| cohort | faithful | defective | rate |
|---|---|---|---|
| **new-prompt redraws** (run 20260816-221213 — what the bulk run replicates) | 12 | 1 | **92.3%** |
| old-prompt sample (pre-ruling drafts) | 5 | 2 | 71% |

**Verdict: CONTINUE.** 92.3% clears the 85% floor; the corrected prompt
cohort beats the old baseline; the bulk run was not paused.

## The defects, by name

* `l4252_4482_n003` (new): **dropped exclusivity** — "instructions that
  discuss the nuances of audio or video … are ONLY relevant to Advanced
  voice" encodes the inclusion and omits the exclusion; a world where those
  instructions also bind standard voice satisfies the module.
* `l1_170_n046` (old): **converse inversion** — "'Root' instructions ONLY
  come from the Model Spec" encoded as "every Model Spec instruction is
  root", overgeneralizing root authority; the document's own lower-level
  designations contradict the encoded rule.
* `l2653_2820_n004` (old): **dropped directive** — the cost-of-incorrect-
  assumptions weighing is claim C1 and encoded nowhere.

⭐ **Two of three defects are the same mechanism: an "only"/exclusivity
clause encoded as its inclusion with the exclusion dropped or inverted.**
This is now a named candidate class for the review-list fold and for a
mechanical check (a span containing "only"/"solely"/"exclusively" whose
module has no forbid, no cnpa closure, and no forbid_body is a cheap
attention flag — untested, follow the graveyard discipline before trusting
it). The battery's prediction that consistent deletion evades the mechanical
gate is confirmed on real traffic: all three defects passed every check.

## Standing consequence

Per-chunk sampling continues through the bulk run: each completed chunk gets
a fresh blind audit of ~6 sampled modules under the same rule. A chunk
falling below the floor stops the run (`pkill -f bulk_run.sh`) while the
failure is diagnosed; a fix verified on the failing sample restarts the
remaining chunks (Matt's D1 amendment); an unverifiable fix leaves the run
stopped for the owner. Audit records append to `semantic_audit.json`.
