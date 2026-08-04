# cycle.py — design contract (2026-08-04, under construction)

One fix cycle as a state machine over typed artifacts. The driver runs
mechanical phases itself and halts with a named, templated blank wherever
judgment is required. The operator (LLM or human) is only ever filling typed
blanks — the seats' dossier-in/verdict-out contract lifted to workflow level.
Motivation: across this project every recorded operator error was
orchestration (a missing --tool flag scoring an empty prediction set; a
`| tail` swallowing a failing gate's exit code before a paid run), and zero
were judgment errors at certified seats.

## State and interaction

- All state under `cycles/<name>/` + derived `state.json`; NO wall clock
  (dates caller-supplied); deterministic artifacts; subprocess exit codes
  propagated.
- `status` reports phase, why, and the exact artifact needed next.
  `next` runs the next mechanical phase, or halts and emits a template.
- `--override PHASE --reason` skips a gate LOUDLY: recorded in state, echoed
  by every later `status`, and surfaced in the close log and decision draft.

## Phases

1. OPEN — `manifest.json`: fix description, DOCUMENT-SIDE rationale, files to
   change, gate tests, review_required, baseline snapshot tag, config.
2. PREDICT — `prediction.json`: expected_shrink / must_not_grow over the
   closed cause taxonomy; sha-FROZEN on validation, tamper = hard error.
3. IMPLEMENT GATE — refuses until gate tests pass, declared files actually
   changed, and (if required) a review verdict artifact says "proceed".
4. MEASURE — snapshot, diff vs baseline, flip dossiers. No-op → short-circuit
   to DECIDE with a drafted no-effect decision.
5. ADJUDICATE — emits the flip-seat assignment; waits for a verdict file that
   VALIDATES (document-side adjudication per briefs/flip_adjudicator.md).
6. CENSUS — regenerates audit dossiers, emits autopsy-seat assignments,
   merges + validates verdicts, computes census-to-census deltas, checks the
   frozen predictions → `prediction_check.json`.
7. DECIDE — drafts `decision.draft.json` with every computed field filled and
   `decision`/`signed_by` blank; halts for a signed `decision.json`.
8. CLOSE — one line appended to `cycles/CYCLE_LOG.jsonl`.

## The decision rule (policy-critical — see tension below)

Keep/revert is grounded in the DOCUMENT-SIDE evidence: the flip
adjudications (phase 5). The census deltas and prediction check (phase 6) are
MEASUREMENT, reported in the draft so the decision is informed, and gating
only in the refusal direction: a FAILED prediction or an override obliges a
written justification; it never auto-decides. Nothing in the driver keeps a
change because a panel-derived count moved the right way.

## Known tension for review

The prediction artifact quantifies targets over CENSUS CAUSE CLASSES, which
are panel-derived (the census pairs tool output with panel verdicts). Policy:
labels direct attention, never truth. The design's position: predictions are
falsifiable statements about label-derived MEASUREMENTS, checked mechanically
and disclosed — not fit criteria, because the keep decision cites the
document-side adjudications and a prediction failure forces justification
rather than reversal. Whether that line is drawn correctly — or whether
per-cycle prediction-checking on panel-derived counts is de-facto fitting
with extra steps — is exactly what an adversarial review should attack.

## Scope

v1 supports one cycle shape: a code/matching fix. Extension points marked for
annotation-cycle and selection-cycle variants. cycle.py joins FORBIDDEN (it
orchestrates panel-reading census tooling).

## ⚠️ BINDING AMENDMENTS (2026-08-04 adversarial design review — supersede
anything above that conflicts)

1. **CENSUS LEAVES THE PER-CYCLE PATH (F1).** The review confirmed the flagged
   tension as a contradiction: the census is the rate-limited outer loop, and
   running it per cycle makes fix selection/stopping coordinate descent on
   panel-derived counts even when every keep is document-justified. The
   DEFAULT cycle is: OPEN → PREDICT → IMPLEMENT GATE → MEASURE → ADJUDICATE →
   DECIDE → CLOSE, with `census: deferred_to_checkpoint` recorded. A separate
   CHECKPOINT cycle-shape (pre-registered, every N closed cycles or
   explicitly declared) runs the census, checks any census-class predictions,
   stamps every census-derived number DEV, and logs `census_consulted: true`.
   PREDICT's REQUIRED targets are document-side, mechanism-level: expected
   flip count/direction/specific clauses and adjudication expectations —
   checkable at MEASURE/ADJUDICATE with zero panel contact.
2. **Census identity (F2).** Census output is cycle-scoped
   (`cycles/<name>/census/` or a tag-qualified dir) with the FULL config
   identity (input shas, overlay sha, pricing_version, threshold rule) in its
   index header; deltas are computed against a NAMED prior census artifact,
   never "the directory". Never regenerate into a baseline's directory.
3. **Verdict binding + tag immutability (F3).** Dossier generation records a
   `dossier_set_sha` (over sorted per-dossier shas) in the assignment; the
   wait-state requires the verdict artifact to echo it. The driver REFUSES
   `snapshot --tag T` when snapshots/T.json exists with different content.
   Verdict REUSE is legal only as an explicit `reused_from` record when the
   dossier bytes are identical — never presented as fresh adjudication.
4. **Flip budget (F4b).** MEASURE counts flips; >30 halts with the policy §4
   template: split the change, or emit a pre-registered stratified-sample
   assignment (behaviour × direction × cause). The first customer measured 34.
5. **Freeze integrity (F5).** The MANIFEST's sha freezes at PREDICT alongside
   the prediction; both re-verified at every later phase; manifest changes
   only via a loud amendment artifact. PREDICT-freeze, ADJUDICATE-validation
   and the DECIDE signature are NON-OVERRIDABLE; overriding PREDICT demotes
   the cycle to `exploratory`, whose CLOSE cannot record KEEP. The
   one-variable check is TWO-SIDED: declared files changed AND a sha-pinned
   closure of undeclared inputs (captured at OPEN) unchanged — this workspace
   has concurrent agents and no git.
6. **Census scope pin (F7).** Manifest declares `census_scope: dev`; the
   driver hard-pins the behaviour list to the recorded DEV cells; touching a
   held-out cell outside a pre-registered checkpoint is a non-overridable
   refusal.
7. **Reconstruction compatibility (F9).** A code fix is cycle-compatible ONLY
   if the old behavior remains reachable via a version recorded in snapshot
   config (the PRICING_VERSION pattern) so the baseline side reconstructs.
   The driver must hardcode the two validators' differing flag spellings
   (`--verdict-file` vs `--verdicts`) — do not "harmonize" them.
8. v1.1 queue (non-blocking): state.json-is-a-cache invariant + tmp/rename
   atomicity + single-open-cycle lock + pricing_version in the noop identity
   (F6); briefs for the DECIDE signer and review-verdict seats (F9).

First customer (versioned cut): safe on the tooling axis, and on the policy
axis ONLY in this amended form — rule chosen label-free via the cut_stability
route and pre-registered BEFORE any census consultation; predictions at
mechanism level ("m0422 stops drifting; flips are threshold_drift only");
its 34 flips handled under the §4 budget path.
