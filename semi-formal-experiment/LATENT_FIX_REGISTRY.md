# LATENT FIX REGISTRY — plans for issues with no current instance

Purpose: a registry of **latent/speculative fixes** — concerns that are real in principle
and have a sketched response, but for which an enumeration or audit found **zero current
instances**, so implementing them now would be building for a problem we do not have.
Each entry stays here, **not implemented**, until a real instance appears, with a named
TRIGGER that would justify implementation. This keeps us from shipping speculative
machinery while not losing the plan.

Origin (2026-08-05): coordinator ruling on D3 — the proposed example-kind taint rule was a
fix for a speculative issue the enumeration showed does not exist; Matt directed that such
plans be registered here rather than implemented.

Protocol:
* An entry belongs here when the concern is genuine but a current enumeration/audit found
  no instance. If there IS a current instance, it is not latent — it belongs in
  OUTSTANDING_WORK.md instead.
* Each entry names: ISSUE, EVIDENCE OF CURRENT ABSENCE, PLAN IF IT APPEARS, TRIGGER,
  STATUS.
* Entries are re-checked when the trigger fires or at a periodic review. If an entry's
  trigger fires, promote it to OUTSTANDING_WORK.md as active work.

---

## LF-1 — example-kind distinct taint rule (from designer ruling D3)

* **ISSUE.** Example passages' modeled response is structurally addressed to the user
  (the example shows the model speaking to the user), so it was hypothesized that
  example-kind clauses might need a DISTINCT taint rule rather than the uniform
  beneficiary-attribution rule (§5.3).
* **EVIDENCE OF CURRENT ABSENCE.** `D3_EXAMPLE_CLAUSE_ENUMERATION.md` (2026-08-05): over
  all 183 example-kind clauses, uniform attribution produces 0 wrong-result cases and 0
  undefined compositions. The motivating concern (user-directed remedial acts, 197/202
  chains) is real but is exactly what §5.3 absorbs. No special rule has work to do.
* **PLAN IF IT APPEARS.** Design an example-kind taint rule. NOTE: the §3 wall
  (m0275 vs m0276 structural identity) shows any ATTRIBUTION-FREE example rule would
  resurface user-harm clauses (m0291/m0264/m0290), so such a rule must itself be
  beneficiary-aware, and needs its own design + adversarial review — it is NOT sketched
  yet.
* **TRIGGER.** A future example-kind clause where uniform attribution produces a wrong
  result (wrong suppression or wrong surfacing), or a distribution shift in example
  clauses that the enumeration's shape buckets do not cover.
* **DETECTION (fail-loud tripwire — lands with the S3b build).** So the latent case fails
  LOUDLY and points here rather than silently mispricing:
  1. POPULATION PIN: a test asserts the example-kind population equals the enumeration's
     vetted set (the 183 ids). On any change (a new/re-annotated example clause), FAIL:
     "example-clause population changed since the D3 enumeration — re-run the enumeration
     before trusting example-clause pricing (see LATENT_FIX_REGISTRY.md LF-1)." This is
     the guard that catches a FUTURE instance the enumeration never vetted.
  2. LOAD-BEARING PIN: assert the attribution-load-bearing examples (m0176/m0300/m0467)
     surface for a third-party query via the attributed PROTECTED party (not the chain
     recipient); on failure, FAIL referencing LF-1.
  3. ADJUDICATION SHAPE-FLAG: any example-kind flip matching the finding-(i) shape is
     tagged in its dossier as an LF-1 candidate requiring explicit disposition
     (confirm-uniform, or promote LF-1 to active work) — never silently absorbed.
* **STATUS.** NOT IMPLEMENTED — S3b uses UNIFORM (D3 ruled 2026-08-05). Registered so the
  idea is not lost and not re-litigated from scratch if the trigger fires.
* **REVISIT (coordinator 2026-08-05).** Keep the DETECTION check MINIMAL for now (population
  pin + the 3 load-bearing clauses + shape-flag; NOT the full 183-clause pin). We do not yet
  know whether tripwires are useful or how many latent fixes will accumulate. Revisit the
  tripwire strategy if it costs more than it is worth, or if it is not catching enough —
  widen, narrow, or drop on that evidence.
