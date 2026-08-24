# THE ERROR CALCULUS — formal specification of the failure-response mechanism
(v0 draft, 2026-08-24, design tier. The mechanism this document specifies:
given a reported failure of the document/behaviour representation, route it
to a typed cause, execute a pre-defined move, validate mechanically, and
identify — in advance and provably — the exact points where frontier/human
judgment is required. Grounded throughout in artifacts already committed;
every class and edge case cites the campaign instance that exhibited it.)

## 1. Formal setting

- N: the node corpus (finite; canonical source node_corpus_all.json).
- For each node n, V(n) is its instrument-visible feature vector over the
  slot inventory S = (acts×sorts, governs, contexts, protects, actors,
  purposes, plumbing, refinements) with finite value vocabularies
  (satisfiability_census.SLOT_INVENTORY; vector() is the constructor).
- For each behaviour b, D(b) is its declaration set (module fields over S).
- f is the evaluation mechanism: a conjunction of gates plus OR-channels
  (relevance_by_act.relevance). Engagement E(n,b) = f(V(n), D(b)) is total,
  deterministic, and yields a DERIVATION (the reason path: functor→bridge→
  canonical act, admitting walls, or the purpose channel).
- T is the truth ledger: append-only rulings with provenance
  (seat-tier, brief-version); assembly with precedence = truth_all().
- I_k: the INVENTORY at version k = (slot set, value vocabularies,
  mechanism kinds in f). All quantities above are indexed by k.

A REPORTED FAILURE is a mismatch m = (n, b) with E(n,b) ≠ T(n,b), or a
reason-integrity flag (verdict correct, derivation degraded/substituted —
probe.py drift classes).

## 2. The Partition Theorem

THEOREM 1 (cause location). For any mismatch m, exactly one of:
  (C-V)  V(n) is unfaithful — the translation mis-states what the node
         claims (annotation/translation error);
  (C-D)  V faithful, but D(b) mis-scopes the behaviour (declaration error);
  (C-I)  V faithful and no D over inventory I_k can separate m from
         correctly-handled nodes (inventory insufficiency);
  (C-T)  V faithful, the instrument's reading defensible, and the ruling
         T(n,b) is itself wrong or non-binding (truth error / legitimate
         divergence — the DEFENSIBLE outcome).
ARGUMENT. E is a deterministic function of (V, D) under f. If V is faithful
and some D over I_k separates m without breaking correct nodes, the defect
is D's (C-D) — witnessed constructively by the census: SEPARABLE status IS
the certificate that such a D exists. If NO D over I_k separates m
(UNSAT certificate: a correctly-handled node with identical full vector
and opposite truth), the defect cannot be D's and is I_k's or upstream
(C-I), unless V is unfaithful (C-V) or T is wrong (C-T). The four cases
exhaust because V-faithfulness and T-correctness are the only exogenous
premises; everything between them is computed. ∎
(Every case has occurred: C-V = the F1 bespoke-does defect; C-D = the 9b
purpose deltas; C-I = the subtype colliders; C-T = the l427_460_n003
defensibility rescue.)

## 3. The Router (decidable; to be implemented as route.py)

Ordered tests; the first that fires assigns the class. Every step is a
computation or a pre-defined seat with a pinned brief.

R1 TRUTH SOLIDITY. Is T(n,b) at panel tier under the pinned lineage brief?
   If not: escalate the ruling (3-seat panel wave; port P1). If the panel
   overturns → C-T resolved, ledger superseded, done. (Cost: fractions of
   a wave seat. Instance: F5 escalation, 2026-08-24.)
R2 FAITHFULNESS AUDIT. Does the node's ESTABLISHES claim faithfully render
   its source span? Pinned audit brief (semantic-audit lane, 85% gate
   doctrine); port P2. Unfaithful → C-V; move = re-translate node +
   two-seat re-annotation; re-run router. (Instance: the only/exclusivity
   defect class from the semantic-audit protocol.)
R3 CENSUS, CURRENT VIEW. SEPARABLE → C-D. Move: mechanical delta —
   candidates from decl-search/discriminator analysis; screened by
   probe.py (L0); validated per §5. FULLY MECHANICAL except the per-flip
   adjudication obligation (port P1, small).
R4 CENSUS, REACHABLE VIEW. CURRENT-UNSAT ∧ REACHABLE-SEPARABLE → C-I,
   subclasses I1/I2 (feature exists unconsumed / distinction typeable but
   unannotated). Moves: build the consumer (typed mechanism addition,
   §6) or run the annotation lane. Mechanical after a one-time build;
   annotation needs certified seats (port P2-adjacent).
R5 UNSAT BOTH VIEWS → C-I subclass I3 (mint new vocabulary; port P3) —
   census→mine→mint pipeline with blind criteria and M1–M4 gates — or,
   if minting attempts exhaust, I4 (document ambiguity; port P4 ruling:
   terminal-by-document, recorded, surfaced as instrument OUTPUT, not
   hidden). DEFENSIBLE remains available at every stage via the pinned
   defensibility brief (one pass, no iteration).

## 4. The Inventory Failure Surface (C-I, fully typed)

| class | detection (decidable certificate) | move | judgment port | historical instance |
|---|---|---|---|---|
| I1 feature unconsumed | REACHABLE-sep via a slot with no consuming gate | build consumer (typed gate; §6) | none (design review only) | refinement marks; purpose-as-wall need |
| I2 typeable, unannotated | value space contains the distinction; credits absent | annotation lane (2-seat + escalation) | seat certification (P2-adj) | context atoms |
| I3 distinction untyped | UNSAT-both + minable contrast in source | mint (blind criteria, M-gates) | P3: the intension choice | provide:forbid.form_equivalence; exhibit:illustrate |
| I4 document ambiguity | UNSAT-both persists after audited V, panel T, exhausted I1–I3 | record terminal-by-document; surface as output | P4: the exhaustion ruling | 2 terminal canary nodes |
| I5 bloat (dual) | feature essential nowhere (criticality census) ∧ zero charter cost to remove | prune via charter | none | (invariant measured 2026-08-24; none found yet) |

## 5. Validation obligations (every move, before adoption)

V1 CHARTER: fixes > breaks on the full assembled ledger, computed exactly
   (probe.py). Necessary, never sufficient (the radicalization revert is
   the standing reason).
V2 REASON PRESERVATION: per-node derivation diff on all verdict-unchanged
   nodes; DEGRADED = break regardless of verdict bit; SUBSTITUTED =
   design-tier review. (Criticality-weighted filtering is BLOCKED until
   the criticality brief is pinned and panel-stable — erratum 31f5da91;
   until then all drift escalates.)
V3 CLASS CARD + HELD-OUT TEST: the move names its class, states the
   general form grounded in document/schema, and predicts non-motivating
   members; L2 passes only if held-out members move. Kills
   gerrymanders-by-measurement structurally.
V4 PER-FLIP ADJUDICATION: every new FP/FN the move creates is blindly
   adjudicated (P1, pinned briefs, one pass).
V5 REALIZATION: registered prediction, then a fresh unscored confirmation
   draw; below-prediction ⇒ revert with record. (The statistical
   perimeter: V1–V4 are exact on the ledger; V5 is the only claim about
   unseen data, and it is a measurement, not a proof.)

## 6. The closure condition (the one engine requirement this calculus needs)

The move space is finitely enumerable iff f is constrained to a fixed gate
grammar: every gate = (slot-feature, semantics ∈ {restrictive, additive,
conditional}, no-information handling = explicit fail-open value that
exclusion cannot bind). Under this grammar, "new mechanism kind" (the open
end of C-I/I1) becomes a typed move like the others, and THEOREM 2 below
closes. The current engine approximates this grammar ad hoc; the
symmetric declaration algebra is the v3-engine commitment that makes it
exact. UNTIL THEN, I1 moves carry a design review (they extend f free-form).

## 7. The Judgment-Port Theorem

THEOREM 2 (frontier necessity, relative to the grammar of §6). The
resolution of any reported failure is fully mechanical EXCEPT for at most
one invocation of one of exactly four ports:
  P1 truth rulings (T is exogenous to the formal system),
  P2 translation-faithfulness audits (V's fidelity is a reading),
  P3 intension choices when minting (an extension underdetermines its
     concept),
  P4 exhaustion rulings for document ambiguity (I4).
ARGUMENT. By Theorem 1 the cause is one of four classes; by §3–§4 every
class's move is computation plus at most the named port; by §6 the move
space itself is closed under typed extension. Nothing else in the pipeline
consumes a judgment: routing is decidable (census certificates), screening
is arithmetic (probe.py), validation V1–V3 are computations, V4–V5 invoke
only P1. ∎ — with the honest rider that P1–P4 seats are only as good as
their PINNED BRIEFS and measured stability (the judge is the instruction:
LINEAGE_SEAT_INSTRUCTION.md 20/20 vs 0.62–0.75 for unpinned variants).

## 8. Inventory versioning

The calculus is indexed by I_k. Terminality, separability, and Theorem 2
hold AT k; transitions k→k+1 occur only through I1–I3 moves with their
validations, and re-stamp obligations propagate (contract 9g-addendum:
"terminal" without an inventory qualifier is a review finding).

## 9. Historical validation plan (the acceptance test; deterministic, ~$0)

Build route.py implementing §3. Run it retrospectively over every resolved
mismatch in the campaign record: the ~640-node truth ledger's historical
flips, all cycle decision.json records, the 9b arithmetic sets, the
defensibility batches, today's 60+ canary/transfer misses. ACCEPTANCE:
(a) every case routes to exactly one class; (b) the prescribed move class
matches the move that actually resolved it (or the record shows why not,
as a calculus erratum); (c) the port invocations the router prescribes are
exactly the seats history actually needed. Failures of (a)–(c) are
calculus bugs, found for free.

## 10. Implementation map

EXISTS: census + certificates (satisfiability_census), L0 screening +
reason diff + hypothesis ledger (probe.py), charter arithmetic, derivation
explanations (explain_relevance), annotation lanes, mint pipeline + gates,
pinned relevance/defensibility briefs, wave-seat venue, supersession-lite
truth (fmap + overlay precedence).
TO BUILD (in order): (1) provenance-tiered ruling records + migration;
(2) route.py + historical validation (§9); (3) class-card tooling + the
driver glue chaining route→move→validate; (4) criticality brief pinning
(unblocks V2 filtering); (5) the §6 gate grammar (v3 engine, with the
next document).

## 11. AMENDMENTS FROM MODEL CHECKING (2026-08-24, calculus_model.py — the
## checker found two reachable-but-undefined outcomes; defined here)

A1 (R3 exhaustion — "separable but no principled delta"). R3 carries a
   DELTA BUDGET (2 attempts per mismatch; every attempt, pass or fail,
   appends to HYPOTHESIS_LEDGER.jsonl, and a ledger entry may never be
   retried). If the census says SEPARABLE but no candidate passes V1–V5
   within budget, the certificate and the failure together are EVIDENCE OF
   A MISSING INTENSION: the feature space distinguishes the nodes, but no
   principled (class-card-passing) declaration carries the distinction —
   the separation is gerrymander-only at the current concept vocabulary.
   ROUTE: R3x → I3 (mint the concept; port P3), or if minting exhausts,
   I4/DEFENSIBLE as in R5x. This closes outcome R3_NO_VALID_DELTA.
A2 (revert re-entry). A delta reverted at V5 re-enters the router AS THE
   SAME MISMATCH with its ledger entry recorded; by the no-retry rule the
   failed delta is excluded, and the R3 budget decrements. Exhaustion
   routes per A1. This closes outcome REVERTED_THEN and bounds the
   adopt→revert cycle structurally: each traversal consumes budget, and
   every terminal is a recorded outcome.
A3 (model limitations, recorded): the checker models retranslation as
   always yielding a faithful V (a still-unfaithful retranslation would
   re-enter R2b; the audit lane's 85% gate governs there — flagged for the
   v1 model), and treats census transitions on retranslation/minting as
   fully nondeterministic (conservative: properties hold on all branches).
   Checker: calculus_model.py; result after A1/A2: 0 gaps, 0 ambiguities,
   0 cycles, 0 undefined outcomes over all reachable states.
A4 (second checker pass — consumer builds are PER-FEATURE, not
   per-mismatch). A mint (I3) can produce a distinction that is annotated
   but unconsumed, returning the mismatch to REACHABLE with the prior
   consumer already built: R4 as first written had no rule there. AMENDED:
   R4 fires whenever census = REACHABLE, building the consumer for the
   feature that currently certifies separability; its budget is per
   FEATURE (finite because the inventory at any version is finite), and
   overall termination holds because every R4 firing consumes a fresh
   inventory feature and every R3/R5 firing consumes a mismatch-local
   budget. Exhaustion (no unconsumed certifying feature left) is
   impossible at census=REACHABLE by definition of the REACHABLE view —
   the certificate names the feature. Checker updated; final result:
   0 gaps, 0 ambiguities, 0 cycles, 0 undefined outcomes.
A5 (cost-ordering and batch semantics; calculus_cost_model.py,
   2026-08-24). (a) ORDERING THEOREM (verified in the cost model): the
   premise checks R1/R2 must precede any move whose cost exceeds theirs —
   deferring them past a consumer build or mint pays the expensive move on
   unverified premises and redoes it (measured in-model: worst case 48 vs
   43 wave-units from REACHABLE; lazy also destroys the cheap best case,
   48 vs 3). The R1->R5 order is therefore near-cost-optimal at measured
   seat costs (panel 3, audit 1 < build 5, mint 8); if seat economics ever
   invert, the rule generalizes to threshold form: premises before any
   move costing more than they do. Both policies provably reach identical
   terminal sets — the ordering question is pure cost, never soundness.
   (b) BATCH SEMANTICS (v0 gap, defined here): the per-mismatch machine is
   the projection of a coupled system sharing inventory state. Batch
   processing MUST: (i) sequence inventory-level moves (I1 builds, I3
   mints) BEFORE the per-mismatch deltas that depend on them — an
   inventory transition k->k+1 invalidates delta validations performed at
   k (redo cost), so the dependency order is topological, fundamental
   changes first; (ii) select moves by MEASURED COVERAGE, not per-mismatch
   routing: every candidate move's exact fix-set is computable (probe.py),
   so batch selection is weighted set-cover over (moves x mismatches) —
   a mint fixing 12 mismatches beats 12 deltas even at 8x unit cost.
   The v1 model obligation: a multi-token (Petri-style) checker verifying
   (i)-(ii) the way calculus_model.py verifies the single-mismatch
   machine, plus MUTATION TESTING of both checkers (the dead-slot-probe
   lesson: an unmutated checker may be checking itself) and an ASP
   encoding so the project's own solver verifies its own repair calculus.
A6 (verification stack COMPLETE + reuse corrections; 2026-08-24 second
   session of model work). (a) ASP ENCODING: calculus.lp encodes the
   machine declaratively; clingo independently confirms 0 gaps / 0
   ambiguities / 0 cycles. (b) MUTATION TESTING: mutate_calculus.py plants
   5 defect classes (dropped rule, dropped guard, double-fire, budget
   removal/cycle, dead-end); the clingo checker catches 5/5 — the
   dead-slot-probe tautology risk is retired for this checker. (c) TRACE
   LEGALITY (the auditable §9 mechanism, Matt's design): historical
   validation runs as (i) deterministic REPLAY — route.py derives each
   historical mismatch's route purely from committed artifacts (census
   recomputed at the historical contract version — demonstrated cheap by
   the v10–v19 scoring, seconds per version; truth tiers from ledger
   provenance; recorded audits/adjudications as port events); (ii) each
   case emits a TRACE (transition sequence, each step carrying its
   evidence pointer artifact+sha — the cycle.py typed-artifact
   discipline applied to routing); (iii) trace_check.py certifies every
   trace is a legal path of the SAME clingo machine (demonstrated: legal
   trace certified, tampered step caught); (iv) predicted terminal vs
   recorded resolution = the acceptance comparison. Cost: ~zero beyond
   building route.py — all replay, no seats.
   (d) REUSE CORRECTIONS (found by inventorying the repo's other
   semi-formal models): verify_terminal.py ALREADY implements exhaustive
   move-space enumeration proving terminality — route.py must call it,
   not re-implement R3/R4 exhaustion; mutation_scope.py already implements
   single-dimension sensitivity analysis; cycle.py is the standing typed-
   artifact state machine whose discipline traces inherit. The calculus's
   novelty is the PARTITION + PORTS + the verified router — not these
   components, which predate it and are cited as its implementation base.
A7 (mix->policy map; calculus_policy_map.py). The A5 ordering question
   parameterized over failure-mix and environment rates: at MEASURED seat
   costs EAGER (premises-first) wins at every tested mix and error rate —
   the ordering is insensitive to mix in the current cost regime because
   premises (4u) are cheap against builds/mints (5-8u). The map is the
   standing tool for detecting when that flips (e.g., panel costs 3x, or
   cheap certified premise seats).
A8 (CONVERGENCE DISCIPLINE — loops close on measured progress, not
   counters; Matt's question 2026-08-24; verified in calculus_model_v2.py).
   v0's budgets guaranteed termination crudely and conflated "proved no
   distinction exists" with "stopped looking". Replaced by three rules:
   (1) NO-REVISIT IS STRUCTURAL: the hypothesis ledger closes the delta
   space (finite per inventory version, attempts never repeat); coined
   criteria are recorded and novelty-checked. Budgets pace COST only.
   (2) PER-PASS PROGRESS OBLIGATION: every coining pass on a collided
   mismatch must STRICTLY SHRINK its collider set (computed exactly by the
   census); a no-progress pass closes the branch immediately. Collider
   count is a well-founded ranking ON THE PROBLEM — convergence in at most
   |initial colliders| productive passes, "productive" measured not hoped.
   The zero-collider case (separable but no principled delta validated,
   A1's missing-intension) has a DIFFERENT progress metric — growth of the
   delta candidate space — and gets exactly ONE coin per inventory
   version. (The v2 checker CAUGHT the cycle this distinction prevents:
   collider-ranking gives no room at X=0, and routing that case through
   the collided track looped SEP->coin->SEP infinitely. Second time a
   checker has corrected the calculus's author.)
   (3) TWO EXHAUSTION TERMINALS, never conflated: TERMINAL-BY-DOCUMENT
   requires the exhaustion CERTIFICATE (enumerable move space provably
   emptied — verify_terminal.py's existing mechanism — plus audited V and
   panel T); budget/ledger exhaustion WITHOUT a certificate yields
   SUSPENDED-OPEN at inventory k — re-enterable when the inventory grows,
   which is exactly the standing PENDING-VOCAB semantics (contract
   9g-addendum) generalized to the whole calculus.
   v2 checker results: 137 states, 0 gaps, 0 ambiguities, 0 cycles,
   0 progress-monotonicity violations; terminals now include
   SUSPENDED_OPEN and TERMINAL_DOC_CERTIFIED as distinct outcomes.
A9 (EXTENSIONAL IDENTITY — the outcome space at every node, mechanically;
   Matt's question 2026-08-24; measured by idea_space.py).
   PRINCIPLE: for this instrument an idea IS its extension. The engine
   consumes only feature vectors, so any two deltas, concepts, or
   distinctions inducing the same partition of the corpus are THE SAME
   ROUTE UNDER DIFFERENT NAMES — and identity is therefore a computation,
   not a judgment. Consequences, per node type:
   (a) CONFIG nodes (R3): the space is CLOSED and countable. Ledger
       entries are re-keyed by EXTENSIONAL FINGERPRINT (sha of the induced
       flip-set + reason-drift, which probe.py already computes) instead
       of delta syntax — syntactically novel proposals with a
       fingerprint already in the ledger are the same attempt and are
       refused mechanically. Single-field spaces are enumerated outright
       (verify_terminal.py); compound spaces are deduplicated to their
       extension classes.
   (b) MECHANISM nodes (R4): closed under the §6 gate grammar (kinds x
       features, finite).
   (c) COINING nodes (R5/R3x): the one place Matt's fallibility suspicion
       is CORRECT and irreducible. The extension lattice bounds the space
       above; mined candidates (split-mining over collider contrasts,
       decl-search interactions) give a FINITE MEASURED FRONTIER; and
       extensional dedup prevents re-coining an old concept under a new
       name. But GROUNDABILITY — whether an extension can be annotated
       consistently from source text — is a reading (port P3), so
       "exhausted" at a coining node always means exhausted RELATIVE TO
       THE MINED FRONTIER, recorded as such, EXCEPT where the
       BYTE-IDENTITY CERTIFICATE applies: same-vector twins whose source
       claims are byte-identical admit NO groundable distinction by any
       reading — the only absolute closure a coining node can have.
   MEASURED (2026-08-24, inventory v19-era, unmasked view): 762 nodes,
   614 distinct vectors -> the instrument can express at most 614 ideas
   over this corpus; 148 nodes sit in 45 provably-indistinguishable twin
   classes; ZERO classes carry the byte-identity certificate — meaning
   nothing in this corpus is currently provably terminal-by-document;
   every standing "terminal" is SUSPENDED-OPEN under A8's semantics, a
   distinction the calculus now enforces.
A10 (coining bounds + capability routing; Matt's questions 2026-08-24).
   (a) NO INTENSION-SIDE BOUND, STATED WHY: word-based bounds fail because
   readings are not compositional in word senses (scope ambiguity grows
   factorially; most sense-combinations are incoherent), distinctions are
   often structural/pragmatic rather than lexical (exhibit:illustrate is
   carried by document markup), and groundability is a property of the
   READER-TEXT PAIR — a pinned brief eliciting consistent annotation —
   not of the text alone (measured: 20/20 vs 15/24 on identical material
   under different briefs). The operative bound is EXTENSIONAL (A9): a
   coining node's outcome space is the set of cuts of its twin class,
   <= 2^(c-1) for class size c (single digits for our measured classes) —
   many names, few routes; the router traverses routes.
   (b) CAPABILITY ROUTING — five questions, asked in order, deciding what
   each decision node requires:
   Q1 output a function of committed artifacts?        -> DETERMINISTIC.
   Q2 judgment class has a pinned, stability-measured brief? if NOT ->
      DESIGN TIER pins it first (unpinned judgment is unstable at every
      tier; tier choice is meaningless before the instruction exists).
   Q3 parity certificate for tier T on THIS brief (measured on
      ledger-known cases, free)? -> CHEAPEST CERTIFIED TIER + seeded
      spot-check + escalation tripwire. Certificates live in the repo and
      re-measure when briefs change: the capability map is empirical and
      self-updating, never a standing opinion.
   Q4 decision GENERATIVE (naming a concept) rather than classificatory?
      -> FRONTIER + human ratification (P3: no answer key can certify it).
   Q5 decision binds future process (floor, prereg, exhaustion ruling)?
      -> HUMAN signature.
A11 (§9 HISTORICAL VALIDATION v0 — EXECUTED; Opus build, Fable-verified;
   ROUTE_VALIDATION_V0.json). 52 historical cases across all five recorded
   classes routed from committed artifacts: 49/52 (94.2%) match the
   recorded resolutions; 52/52 traces clingo-certified (independently
   re-checked on a sample). The three mismatches are FINDINGS FOR the
   calculus, not against it: two are the canary "terminal" nodes, which
   the router sends to I3-coining while the record stamped I4-terminal
   WITHOUT a logged mint exhaustion — i.e., history violated A8's
   certificate rule and A9 already showed those stamps overclaimed (zero
   byte-identity certificates exist); the record is what needs the
   erratum. The third is a node absent from the canonical corpus (P2
   port fires correctly on a real keying gap).
   STRUCTURAL FINDINGS (route-validate F-r1/F-r2, both actionable):
   F-r1: 20 of 644 assembled-ledger nodes key to a superseded chunking
   (l426_610_* vs l427_460_*) — a truth-ledger hygiene item.
   F-r2 (serious): verify_terminal.py — designated the move-space
   authority in A6(d) — enumerates only protects/governs moves; it has no
   purpose_concern move and stamps TERMINAL-STRUCT on 4 nodes the adopted
   9b purpose deltas demonstrably fixed; its truth assembly is also stale
   (no fresh_draw4, no defensibility overlay). Its terminality
   certificates are UNSOUND at the current inventory — the exact
   inventory-relative staleness contract 9g warned about, now caught by
   the calculus's own validation. Until verify_terminal is extended to
   the full declarable move set and current truth, NO exhaustion
   certificate may cite it; A8's certified-terminal path is effectively
   closed pending that fix, and every standing terminal is SUSPENDED-OPEN.
A12 (F-r2 STRUCTURAL FIX — data-driven move spaces; Matt's requirement:
   "a decision from a previous search must immediately reflect in the
   next one"). Implemented 2026-08-24:
   - RBA.DECLARABLE_MOVES is THE single-source registry of engine-
     consumable declaration channels; every enumerator derives from it.
   - verify_terminal.py now: enumerates purpose_concern moves (the F-r2
     omission); no longer forecloses act-unmatched nodes (the purpose
     channel is act-independent — a second latent staleness found during
     the fix); delegates truth to the maintained assembly (fresh_draw4 +
     defensibility overlay — confirmed live: the rescued node reads
     'relevant'); and every TERMINAL verdict now CARRIES ITS ENUMERATION
     SCOPE in the verdict string — a certificate names what it exhausted,
     so a subset enumeration can never again masquerade as an absolute
     claim (A8 honesty, enforced syntactically).
   - test_move_registry_handshake fails loud when the engine grows a
     channel the registry lacks, or when verify_terminal's ENUMERATED +
     KNOWN_UNENUMERATED stop covering the registry (the census
     SLOT_INVENTORY handshake pattern, generalized). KNOWN_UNENUMERATED
     (arg_sorts, party_concern, governs_conditional) are declared, so
     their existence structurally blocks absolute terminality claims
     until handlers exist.
A13 (HUMAN-DENSITY DESIGN — Matt's iteration concern). Humans appear
   slower-by-orders-of-magnitude ONLY if they sit inline. The calculus
   places them differently:
   (1) NEVER BLOCKING: no machine path waits on a human — anything
   needing ratification lands in SUSPENDED-OPEN and the loop continues
   on other tokens; human input is consumed ASYNCHRONOUSLY at batch
   boundaries. Iteration speed = machine speed; human latency bounds
   only how long suspensions sit, not throughput.
   (2) BATCHED RATIFICATION, not per-decision: the P3 human role is
   ratifying a BATCH of frontier-proposed intensions (the mint pipeline
   already works this way — blind criteria designed at frontier, one
   signature per prereg). Measured this campaign: ~4 human signatures
   across three weeks against hundreds of machine decisions.
   (3) MEASURED DELEGATION (design option, requires Matt's explicit
   ruling since it samples HIS oversight): the parity-certificate logic
   applies to the human port too — where frontier-vs-human agreement on
   a decision class is measured high over history, the human moves from
   gate to seeded auditor (spot-check with escalation tripwire), exactly
   as cheap tiers relate to frontier. Red shrinks by measurement, never
   by assumption.
