# The golden-graph protocol
> **Provenance (G1, review 2026-08-11):** The existing golden was produced by
> the SUBAGENT build of 2026-08-10 (interactive Haiku dispatches), not by
> recurse_driver.py; the driver's autofixes, dedupe and health bands were
> built AFTER and validated against that golden. A new document following
> this procedure runs the driver path; the golden itself did not.


How to produce a **golden decomposition** of a NEW document. Distilled from the
2026-08-10/11 build (EXPERIMENTS.md); instruments and worked artifacts referenced below
live in this directory. Standing rules apply throughout: **labels direct attention,
never truth** — a flag or a verdict motivates a look, but every keep/repair is grounded
in the document itself; **design docs, keys, and prior verdicts never reach a seat**
(this file included); **every instrument is RED-verified before first use** (shown to
catch a planted or historical defect); **every repair is mechanically verified after
application** — false completion reports are a confirmed recurring failure mode.

## 1. Generation — recursive protocol, cheap model

Run `recurse_driver.py` with `RECURSE_PROMPT.md`: recursive division (2–3 children per
cut, enforced in the response-format grammar, not just prose), leaf extraction, then
unwinds that resolve cross-child links via inherited seed names. Small model (Haiku /
DeepSeek tier); schema-forced replies; multi-round accumulating repair; safe autofixes
only (e.g. `dedupe_nodes` — exact duplicates cannot lose information). Resumable at
every tree node.
- Catches: coarsening, dropped coverage, dangling links — each unwind is scored
  in-flight; cross-links are seeded downward so linking is mechanical, not clairvoyant.
- Never: let the dispatch pre-answer a leaf's judgment without flagging it (that turns a
  recognition test into a mechanism test); let a seat see build transcripts; delete a
  dangling to make counts clean — genuine externals MUST survive (a zero-dangling root
  is over-resolution).
- Leaves: the run directory tree (per-node dispatches, replies, repairs), the merged
  `graph.json`, `health.jsonl`.

## 2. Health bands during generation (golden-free, from the 2026-08-11 postmortem)

Absolute early-warning signals that need no reference graph, emitted per artifact into
`health.jsonl` with immediate warnings: **density** over `LEAF_DENSITY_MAX` (0.7
nodes/line, ~2x healthy top), **exact-duplicate content** under distinct ids (a decoding
loop — 969 copies once passed every id-based validator), **zero needs in a large span**
(linkage failed to transfer on that draw). `smoke_granularity.py` replays the two known
failure dispatches against any candidate model before committing to it.
- Never: trust id-based validators alone; treat token-cap truncation as a one-off (the
  runaway draws were the same loop hitting the cap).

## 3. Mechanical checks — `graph_check.py`

On the finished graph (and automatically post-build): span resolution, quote
verbatim-rate, size distribution, overlap/nesting, name-link resolution + dangling list,
coverage identity, unaccounted lines. Plus `merge_check.py` (content loss across merges;
RED on the historical tier-loss case) and the id-diff across unwinds (caught the one
deletion violation). ⚠️ G4 (review): the sampling script and the id-diff are
per-document one-liners that MUST be committed alongside the audit key --
the golden's own `audit_sample.py` was never packaged, so its sampling is
pinned only by the stored sample_*.json files.
- Catches: everything countable — before any judgment is spent.
- Never: apply an instrument that has not failed RED on a known defect; assume the
  checker is wrong when it disagrees with a reader — verify ground truth first (the
  line-count dispute: `graph_check` was right, the blind auditor was wrong).
- Leaves: check reports in the run dir; a mechanically-clean graph.

## 4. Stratified audit — frontier model, pre-registered key

Write the key BEFORE any auditor runs (pattern: `AUDIT_KEY.md`). Four strata, sampled
deterministically by script: **A** node fidelity (faithful/overreach/incomplete/wrong),
**B** edge validity (valid/mention-only/mismatch/partial — mention-only is the
self-satisfaction defect in disguise), **C** blind re-adjudication of every recorded
judgment call, phrased as questions never answers, **D** coverage honesty on uncovered
ranges. Thresholds pre-registered per stratum (A ≥90% translation-grade, 80–90% repair
pass, <80% iterate; B ≥90%; any D silently-dropped is a finding). Auditors get ONLY the
raw document, the line-numbered copy, a stripped graph (judgment_calls and
cross_link_report removed), and their own sample.
- Catches: judgment errors mechanics cannot see; whether recorded decisions survive
  blind re-derivation.
- Never: let the orchestrator write verdicts; hand a stratum another stratum's
  questions; aggregate the four rates into one score — they have different consumers.
- Leaves: the key, per-stratum rates with denominators, a findings list
  (`audit/AUDIT_RESULTS.md`), verified repairs (string-check each application).

## 5. Systematic sweeps — every audit-discovered class, full graph

The audit samples ~5% of nodes; every defect CLASS it finds is swept over ALL nodes with
a purpose-built, RED-verified (`--self-test`) instrument. This build: `sweep_modals.py`
(establishes vs span-text modal profile: strengthened/weakened/flattened) and
`sweep_headings.py` (heading-only nodes asserting section content). Expect a new
document's audit to surface its own classes; build the sweep, RED it, run it.
- Catches: the unsampled instances (~6 expected here; 76 candidates found).
- Never: repair from a flag without adjudication — sweeps are lexical heuristics and
  false-positive-rich by design (36/76 here).
- Leaves: `sweep_*_report.json` per class.

## 6. Seat adjudication + mechanical verification of every repair

Sweep candidates go to parallel frontier-tier seats, blind to provenance beyond the flag
kind, with any known legitimate carve-outs stated in the brief (here: imperative mood
renders as "must"). Verdict per candidate: repair (with proposed text) or
false-positive (with grounds). BEFORE applying any repair: re-sweep the proposed text
and run `merge_check` against the original (content-drop check) — a proposal that
re-flags is hand-inspected; only demonstrated instrument artifacts pass (2/40 here). Back
up the graph, apply, record everything in `adjudication/DISPOSITION.json`.
- Catches: false positives; garbled repairs (a prior repair corrupted a sentence —
  hence verbatim verification is non-negotiable).
- Never: apply an unverified proposal; discard false-positive grounds — the accepted
  flags are the closed loop's expected residue.
- Leaves: seat verdicts (`adjudication/verdicts_*.json`), `DISPOSITION.json`, the
  pre-sweep backup.

## 7. The closed loop

Re-run every sweep on the repaired graph. **Pass = the flag set equals the
adjudicated-keep set (accepted false positives PLUS recorded instrument
artifacts) exactly** -- zero
unexpected flags, zero lost content; `graph_check` fully clean; danglings unchanged and
each survivor individually legitimate (external reference or structural
self-reference). Any deviation reopens step 6.
- Leaves: **the golden candidate**, its residual-flag record, and (optional capstone)
  one more independent audit round on this exact artifact.

A second graph of the same document is compared against the golden via
`GRAPH_EQUIVALENCE.md` — pre-registered, name-free, judgment-backed-zero verdict rule —
never by similarity score.
