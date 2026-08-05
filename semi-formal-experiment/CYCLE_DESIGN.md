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
   closure of undeclared inputs (captured at OPEN) unchanged. [Corrected per
   PORTFOLIO_REVIEW F12: the original "this workspace has concurrent agents
   and no git" rationale is STALE — the repo IS git-tracked (which is what
   validates the git-primary A-side reconstruction, tooling item 0b). The
   two-sided closure check stands on its own merits: concurrent agents, and
   sha-pinned closure being the check the ceremony can verify mechanically.]
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

---

## ⚠️ PRE-BUILT CYCLES (added 2026-08-04 after P1 hit this undocumented)

The driver assumes OPEN precedes implementation: `_open` captures each
`files_to_change` sha, and the IMPLEMENT gate refuses when those files are
byte-identical to their OPEN shas ("the fix has not been implemented"). Every
cycle through S3 happened to follow that order, so this was never written down.

**It does not always hold.** Work built in an isolated worktree and parked for a
later gate window (P1 join-integrity is the first case) arrives *finished and
already measured* before its cycle can open. The coordinator creates these
deliberately — parallel work needs isolation — so the pattern is expected, not an
accident, and it needs a documented handling.

### What the freeze can and cannot give you here

Separate two things the ceremony provides:

* **The temporal guarantee** (predictions made before results are known). For a
  pre-built cycle this is **already gone and no procedure restores it**. Do not
  construct a ritual that appears to restore it.
* **The mechanical gate coverage** (declared files changed; gate tests green;
  closure of undeclared inputs unchanged; review verdict present). These remain
  fully meaningful regardless of when the code was written, and are worth keeping.

### The ruling (coordinator, 2026-08-04) — restore-then-reapply

1. Record the hashes of the finished files, then restore them to their **pre-change
   bytes in the CURRENT tree** — not to the worktree's fork point. A parked branch
   may have zero unique commits (P1's did); checking out the fork point silently
   reverts unrelated later work. Verify the restored files differ from the finished
   ones **only** in this cycle's hunks before proceeding.
2. Move any test file that exists solely to gate this change into `gate_tests`
   (closure-pinned), not `files_to_change`.
3. OPEN (captures the pre-change shas), then PREDICT from the drafts.
4. Re-apply the saved files as the IMPLEMENT step and **verify byte-identity to the
   reviewed bytes**. That check is what makes the shuffle legitimate rather than a
   re-implementation: the gate then genuinely exercises declared-files-changed,
   tests, and closure.
5. Regenerate any measurement artifacts produced in the worktree — they were built
   against a different tree and are misleading as-is (P1's `measure/` files date from
   a superseded constant).

**Rejected alternatives, with reasons:** `--override IMPLEMENT` records the truth but
discards all three mechanical checks to avoid a file-shuffle — a bad trade, and it
leaves a permanent override banner on a cycle that doesn't need one. Ratifying by
review + no-op proof alone (no cycle) loses the record for a change that does alter the
measurement plumbing the census runs on; "score-inert" is a claim that deserves a cycle,
and the no-op proof is evidence *for* it, not a substitute.

### The disclosure is MANDATORY

The cycle record must state plainly, in the prediction notes **and** repeated in the
decision justification, that the change was built and measured before OPEN. Without
that line, restore-then-reapply is the one structure that could quietly *overstate*
our discipline — a passing prediction reads as a blind prediction to any later reader.
P1's draft prediction already carries the right form of words ("all numbers below are
measured, not hoped"); keep them through to the decision.

---

## ⚠️ CYCLE CEREMONY MECHANICS (added 2026-08-04 — previously precedent-only)

These were learned by doing and lived only inside cycle directories. The gate-pin rule
alone cost two halts and two re-closures in a single cycle.

### The amendment channel

`cycles/<name>/manifest_amendments.json` is the LOUD record for anything that changes a
frozen or pinned artifact mid-cycle. Each entry chains: `old_sha` must equal the previous
entry's `new_sha` (the first equals `state.json`'s `frozen_manifest_sha`), so the chain is
verifiable end-to-end and `cycle.py status` echoes every amendment forever. An amendment
that changes no manifest bytes still gets an entry with `old_sha == new_sha` — use this to
record a test-delta or a disposition. **Never edit a frozen artifact silently; never
"fix up" a sha in place.**

### Gate pins vs declared changes — the trap

A file is either **closure-pinned** (captured at OPEN, must NOT change: the gate refuses
if it does) or a **declared change** (`files_to_change`: the gate refuses if it does NOT
change). Putting a file in the wrong class produces a gate failure that looks like a code
bug and is not. Two real cases:

* A gate test whose assertions pin the *pre-change* state is closure-pinned by default,
  but the cycle's own change necessarily turns it red. The fix is a **re-closure**: move
  it to `files_to_change`, rewriting its pins to the declared state (a *stronger* pin),
  recorded as an amendment.
* A test that pins a **live-artifact census count** (`n == 109`, `692 candidates`) will go
  stale the moment a cycle legitimately changes that artifact. Pin the frozen *input*
  (a sha-pinned fixture or the frozen worksheet) plus a subset/coherence check — never an
  exact count of a growing artifact. This failed twice in one cycle, in both S1's test and
  the operator's own.

**A re-closure made without prior designer sign-off must be FLAGGED FOR THE REVIEW SEAT to
countersign or block.** Do not let the operator's convenience silently become policy.

### Seat conventions

* Every judgment seat gets a written `briefs/` file, a closed output schema, and a
  mechanical validator. The brief states what the seat may never see.
* **A cycle's own design document is never seat material** — nor is `PORTFOLIO_REVIEW.md`,
  prior cycles' `flip_verdicts*.json`, or the census. Design docs pre-register expected
  outcomes, so handing one to a seat "for context" destroys the judgment it was dispatched
  to make.
* The coordinator MAY append an **operator addendum** to a driver-written assignment,
  containing FROZEN FACTS ONLY (mechanism maps, pre-registered expectations already on
  record). It never overrides the brief and never adds new judgment instructions.
* **Contested verdicts are recorded as contested.** When two legs of a seat diverge, both
  document reasons are preserved verbatim, the verdict is `unclear`, and the divergence is
  flagged for seat-defect review — never resolved by fiat, never averaged, and never
  re-run at a bigger model to break the tie.
* A bound-breaching or otherwise decision-critical verdict from a small-model seat gets an
  independent split-blind verification leg before any decision cites it (the leg learns
  WHICH items are contested, never which way the first leg ruled).

### Designer rulings

A ruling is a coordinator decision that resolves something a design left open or that a
halt surfaced. It must be **written into the cycle record** (a named `*.md` in the cycle
dir, or the decision justification), stating the grounds and — where a tempting
alternative was rejected — **rejecting it by name with the reason**. A ruling that exists
only in a dispatch message is transcript-only procedure, which `REPRODUCIBILITY.md`
classes as a review finding.

### Commit at CLOSE

The driver NEVER runs git. CLOSE drafts `commit_message.txt` and `staging_list.txt`
(= `files_to_change` ∪ the cycle dir); the coordinator stages, verifies, and commits.
Staging often needs MORE than the list: newly created modules/tests, `conftest.py`
registrations, new fixtures, the published snapshot, and `cycles/CYCLE_LOG.jsonl` — whose
line may lag the previous cycle's commit and ride the next one. Check `git status` against
the list rather than trusting either alone.
