# CHEAP-TIER FIX + CERTIFICATION DRIVER — design (2026-08-24, Matt's directive)

GOAL (Matt): a mechanical batch process that (1) takes a batch of found
issues, fixes and validates them using cheap models (Haiku / DeepSeek-class)
wherever possible, and (2) certifies mechanically, cheap-first, engaging
frontier models only where necessary plus spot checks — with the blog-grade
demonstration: "we found issues, ran mechanical fixes, and the predicted
gains were realized on fresh unscored data."

## SAFETY ARCHITECTURE (the rules that make cheap tiers admissible)
S-A PARITY CERTIFICATES, PER SEAT-BRIEF: no cheap model performs a role
    without a measured agreement certificate on LEDGER-KNOWN nodes for the
    EXACT brief it will run (doctrine: divergence from frontier on the same
    brief is a seat defect — a brief that cheap tiers fail is either
    improved with context until they pass, or the role stays frontier).
    Certificates are free: the ledger is the answer key.
S-B CORRELATED-ERROR GUARD: cheap-cheap agreement alone never suffices —
    the 2026-08-24 parity failure showed cheap tiers agreeing on WRONG
    answers. Every cheap-ruled batch carries a seeded FRONTIER SPOT-CHECK
    (rate >=15%) with a pre-registered overturn tripwire (F5 pattern:
    overturn rate >10% -> the whole batch escalates to frontier). The
    spot-check seed is registered before the batch runs.
S-C DETERMINISTIC CORE UNTOUCHED: delta search (decl-search/L1), charter
    arithmetic, census triage, draws, scoring, falsifier checks are
    model-free and stay so. Models enter ONLY at: annotation lanes,
    relevance rulings, defensibility adjudication.
S-D THE RADICALIZATION GUARDRAIL STAYS: every adopted delta's flips are
    individually adjudicated; charter (fixes>breaks) is necessary, never
    sufficient. Adjudication runs at the cheapest tier holding a parity
    certificate FOR ADJUDICATION specifically; absent one, frontier.
S-E FLOORS NEVER MOVE DOWN; every fix is validated twice: on the ledger
    (in-sample charter) AND on a fresh unscored confirmation draw
    (out-of-sample realization) before any claim is made.
S-F ESCALATION IS PRE-ROUTED, NOT DISCRETIONARY: census triage routes each
    issue BEFORE work starts — (i) separable-in-consumable-features ->
    mechanical delta; (ii) needs annotation -> two cheap seats + frontier
    on disagreement + spot-check; (iii) needs new mechanism/vocabulary ->
    design tier (frontier), by name; (iv) UNSAT-terminal -> frontier/human
    ruling only. The router's output is committed with the batch.

## THE LOOP (one command per phase; all artifacts committed)
1. TRIAGE (free): census + discriminator analysis over the batch ->
   routed queue.
2. FIX (cheap): mechanical deltas emitted by decl-search; annotation lanes
   on certified cheap seats (two-seat consensus, frontier escalation);
   module repairs (attempt-2 semantics per the generalization prereg's
   re-measurement protocol — transfer verdicts stay attempt-1, repairs are
   attempt-2, never mixed).
3. VALIDATE (free + small): charter arithmetic vs full ledger; per-flip
   adjudication at certified-cheapest tier; REGISTER predicted fresh-draw
   movement before step 4.
4. REALIZE (cheap seats + frontier spot-check): fresh confirmation draw
   from unscored pool, ruled blind, scored against the registered
   prediction. Above-band -> leak check; below -> the fix did not
   generalize, delta reverts (recorded).
5. CERTIFY: the round-4 machinery (draws/bands/falsifiers/defensibility)
   with rulings at the certified-cheapest tier + frontier spot-checks.

## COST MODEL (measured basis)
Wave seat rules 40 nodes/call. Haiku wave ~= 1/30 the weekly-bar weight of
a Fable wave; a full behavior certification ~5 waves. If Haiku holds a
parity certificate, per-behavior certification cost approaches noise, with
frontier spend concentrated in the >=15% spot-check.

## STATUS
- Parity test 1 (gating): Haiku + Sonnet on the lineage brief over the
  20-node ledger-known replication packet (Fable reference: 20/20).
  Dispatched 2026-08-24; certificate thresholds: >=0.90 -> certified for
  ruling waves with S-B spot-checks; 0.80-0.90 -> retry with enhanced
  context (few-shot ledger examples appended to the brief; re-test); <0.80
  -> role stays frontier (which is already cheap in wave form).
- First batch queued for the loop: tradeoffs' 12 FPs (attempt-2 repair),
  helpfulness's 9 separable FPs (pending mechanism), harm's 8 FNs
  (party-wall family), caution's 13 FPs.
