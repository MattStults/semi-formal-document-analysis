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

## v2 ADDENDA (2026-08-24, Matt's design review in session)

### A. SUPERSESSION ARCHITECTURE (Matt's reframe: make errors free to fix,
### rather than requiring cheap seats to be error-free)
The parity measurements (below) show no cheap tier reaches ruling-grade
parity even with the lineage brief and few-shot calibration. Instead of
gating cheap tiers OUT, the architecture makes their errors COSTLESS:
- TRUTH WITH PROVENANCE TIERS: every ruling is an append-only record
  (node, behavior, verdict, grounds, seat-tier, brief-version). Precedence:
  human > frontier panel > frontier single > cheap consensus > cheap
  single. A higher tier supersedes; nothing is overwritten.
- TOTAL RECOMPUTABILITY: everything downstream of truth (charter, cells,
  census, certification) is deterministic scripts over the assembled
  ledger. Flipping one verdict and recomputing the world costs seconds and
  $0. Disagreeing with a DeepSeek decision = one frontier wave seat on that
  node (cents) + rerun. THIS is why 0.75 does not hurt.
- CHEAP TIERS DIRECT ATTENTION, NEVER TRUTH — the campaign's founding
  doctrine applied to model tiers. Cheap seats prioritize where frontier
  looks (first-pass sweeps, disagreement surfacing, triage); certified
  CLAIMS are computed only over frontier-tier-or-better records, with the
  cheap layer reducing frontier VOLUME (rule only where cheap tiers
  disagree with the instrument, with each other, or with spot-checks).
- MEASURED CERTIFICATES (2026-08-24, 20 ledger-known nodes, Fable ref
  20/20): Haiku 0.85 plain / 0.80 few-shot (over-inclusive bias);
  DeepSeek-V4-Flash 0.75 (mixed 1/4); Sonnet 0.70 (strict 0/6). Opposite
  bias directions across tiers -> cross-tier disagreement is a stronger
  escalation trigger than same-tier duplication (their errors decorrelate).
  Artifacts: parity_cheap_tier_certificates.json, parity_*_rulings.json,
  parity_deepseek_raw.txt.

### B. REASON-PRESERVING VALIDATION (Matt: "changes must preserve not only
### the right call but the right reasons")
Verdict-preservation is insufficient: a delta can keep a node correctly
engaged while silently REPLACING the mechanism that engages it (e.g. the
semantically-right act path lost, a fail-open accident now carrying the
node). Right call, wrong reason = a latent break that the next delta
detonates. The instrument makes this checkable deterministically:
explain_relevance computes each engagement's full path (bespoke act ->
bridge -> canonical act -> walls admitted). VALIDATION STEP 3b (mandatory
for every delta): diff the per-node REASON SIGNATURE before/after for all
verdict-unchanged nodes; classify drift:
  - none: same path -> pass silently;
  - augmented: original path intact, new path added -> pass, logged;
  - SUBSTITUTED: original path lost, verdict carried by a different
    mechanism -> flagged for design-tier review before adoption (the
    right-call-wrong-reason class);
  - DEGRADED: verdict now carried by a fail-open (no-information) branch
    -> treated as a BREAK regardless of the verdict bit.
Truth-side analogue: seat grounds must quote the span (already enforced by
the brief); a mechanical quote-presence check runs on every ruling batch,
and superseding rulings record WHY the lower tier's grounds failed, so the
brief improves from its own error ledger.

### C. THE ITERATION FUNNEL (v3, 2026-08-24 — Matt: fast cheap hypothesis
### paths through an explosively large representation space)
The search space (declarations x vocabulary x mechanisms x exposures) is
far too large for adopt-and-measure iteration. The funnel makes hypothesis
COST proportional to hypothesis SURVIVAL — most die free:

L0  SECONDS, $0 — probe.py: any hypothesis expressible as a module delta
    gets its complete counterfactual vs the assembled ledger (~640 ruled
    nodes) with NO contract file touched: charter, affected nodes, and the
    reason-signature diff (augmented / SUBSTITUTED / DEGRADED). Candidate
    generation at this level is the L1 optimizer (decl-search) + the census
    discriminator analysis; screening is probe.py. Every probe appends to
    HYPOTHESIS_LEDGER.jsonl (append-only) so dead branches are never
    re-explored and rejected-by-name is automatic.
    VALIDATED 2026-08-24: probe.py reproduced the governs-narrowing
    arithmetic exactly (3/16) and additionally surfaced 15 DEGRADED nodes
    the hand check missed.
L1  MINUTES, CENTS — micro-probe on live judgment: hypotheses needing NEW
    information (an unannotated atom, a judge's reading of a proposed
    distinction) run on a seeded 10-30 node micro-sample; cheap seats
    first-pass, frontier only on the decisive nodes. (Today's 20-node
    parity probes and the 40-seat paired-format pilot were L1 runs.)
L2  TENS OF MINUTES, ~0.1pt — full validation: charter + reason-diff over
    the whole ledger, per-flip adjudication, ONE fresh confirmation wave
    (registered prediction first). Only here does a contract file change.
L3  HOURS, ~0.5-1pt — certification-grade: registered bands, fresh draws,
    falsifiers, defensibility (the round-4 machinery).
PROMOTION RULE: a hypothesis reaches level N only by passing N-1; a kill at
any level is a committed ledger record, not a discarded experiment. The
"one-off change to test before committing" is exactly an L0/L1 pass — the
contract is never mutated below L2, so exploration is free AND safe.
