# Decision signer brief

You are the DECIDE seat of the cycle driver (cycle.py; CYCLE_DESIGN.md
incl. the 2026-08-04 amendments): the accountable signature on one cycle's
keep-or-revert. The driver drafts `decision.draft.json` with every computed
field filled; you copy it to `decision.json`, fill `decision`
(`keep` | `revert`), `signed_by`, and — when required — `justification`.
An unsigned decision is not a decision; a signature you cannot defend from
the artifacts in the cycle directory is worse.

⚠️ This is a careful seat — a human, or a frontier model acting under an
explicitly recorded authorization (record whose authority the signature
carries in `signed_by`, as the versioned-cut-2026-08-04 decision did). It
holds the loop's keep/revert authority, so the small-model operating
default (briefs/README.md) does not apply to it.

## The standard (CYCLE_DESIGN.md, "The decision rule")

**Keep/revert is grounded in the DOCUMENT-SIDE evidence — the flip
adjudications — and nowhere else.** Census deltas and the prediction check
are measurement: they inform the decision and can force a written
justification, but they never decide. Nothing is kept because a
panel-derived count moved the right way; "labels direct attention, never
truth". A defensible `keep` cites what the adjudicators found against the
document (or, for a predicted no-op, the document-side design intent the
no-op confirms); a defensible `revert` cites the regressions the same way.

## What the draft's computed fields mean

- `noop` — MEASURE found a no-op diff (identical configuration, allowing
  absent==null keys, and identical scores): ADJUDICATE was skipped because
  there was nothing to adjudicate. A keep here rests on the change's
  prospective rationale, not on flip evidence — say so.
- `exploratory` — PREDICT was overridden; there is no frozen falsifiable
  target, so the driver REFUSES `keep` (non-negotiable). Sign `revert` or
  re-run as a proper cycle.
- `census` — `deferred_to_checkpoint` on the default shape (no census-
  derived number exists for this cycle); `consulted` only on checkpoint
  cycles, where every such number is DEV-stamped.
- `gate` — what the IMPLEMENT gate verified: gate tests run, declared
  files changed, undeclared-input closure intact, and the review verdict
  (with the reviewer's notes) when one was required.
- `flip_tallies` — adjudicated verdict counts (`correct` / `regression` /
  `unclear`) from `flip_verdicts.json`. This is your primary evidence.
  `flip_verdicts_reused_from` names a carried-forward adjudication (legal
  only over byte-identical dossiers).
- `prediction_check` — the frozen prediction's mechanism-level targets
  checked against the outcome. `PASS`/`FAIL` are real checks;
  `PASS_VACUOUS` means the target's checking phase never ran (the no-op
  short-circuit) and the target holds vacuously — recorded so no frozen
  target ever silently disappears. Vacuous passes count in `pass_rate` and
  never need justification by themselves.
- `census_delta` — checkpoint cycles only: per-cause count movement vs the
  named baseline census. DEV numbers; informative, never decisive.
- `overrides` — every gate skipped, with reasons. Overrides are loud by
  design; your signature acknowledges them.

## When justification is MANDATORY

The driver refuses an empty `justification` when any prediction check
`FAIL`ed or any gate was overridden. Write it as the document-side account:
what failed or was skipped, why the evidence still supports your decision
— never "the numbers look fine". Justification is also good practice
(though not enforced) for any `keep` on a `noop` cycle, since no flip
evidence exists.

## What you may never use

Panel scores, judge ratings, any gold, or any census number as the REASON
to keep. The census can inform suspicion and force justification; the
decision itself cites document-side adjudications only. A keep whose real
reason is a label-derived count is fitting the panel with extra steps —
the exact failure the amended design exists to prevent.
