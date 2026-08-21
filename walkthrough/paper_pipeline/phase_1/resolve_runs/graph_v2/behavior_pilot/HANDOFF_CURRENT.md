# HANDOFF — convergence endgame + declaration-search results (2026-08-20, updated end-of-day)
Written for a frontier-capable agent resuming with zero context. Read top-down;
every claim has an artifact pointer. Repo root for this work: this directory
(behavior_pilot). Canonical campaign log: ../EXPERIMENTS.md. Contract:
TRANSLATION_CONTRACT_V2.md (§§8, 8-A1..A3, 9a-9g are binding).

## Instrument state (frozen, all-truth baseline)
- modules_contract_v18.json + behaviors_canonical_v13.json; engagement =
  relevance_by_act.py (act channel + walls + purpose channel SCOPED to assert
  lane — see "channel jurisdiction" comments in the file; definitional keys
  nid|c{i} never feed purpose_hit).
- Baseline (no definitional layers): caution TP102/FP12, harm TP73/FP11,
  help TP178/FP12 (truth = satisfiability_census.truth_all()).

## What just happened (all committed & pushed, d3-worked-example)
1. DEFINITIONAL LANE (panel_run1/convergence/definitional_lane_prereg.md — the
   single source of truth; read all its appended sections in order):
   179 norm-free nodes annotated by TWO independent Opus seats (parity-passed
   lane), consensus = per-field intersection, actor disagreement voids claim.
   Assembly: assemble_two_seat.py (encodes empty-governs fail-open,
   minor->third_party purity, EXAMPLE-NARRATION act-lift scope).
   Layers PARKED at panel_run1/convergence/candidate_definition_layers/
   (copy the 4 files into behavior_pilot/ to activate; mechanism inert without).
   Consensus arithmetic: +8 TP / +4 FP-instances on 3 unique nodes.
2. 3-NODE PRIORITY ESCALATION (decides lane adoption): are these act credits
   correct under the brief (definitional_ann_brief.md), stricter-reading test:
   l2821_3040_n006 (provide_information? claims describe consequences of user
   reliance), l1707_1973_n017 (act_in_world? information-flow enumeration),
   l699_796_n008 (comply? describes malicious tool instructions the user would
   NOT want followed). If credits removed -> lane is +8/0 -> ADOPT per gate.
   Seat must be BLIND (packet = claims+span only; never truth or this file).
3. ESCALATION QUEUE: definitional_escalation_queue.json (268 field-level seat
   disagreements). Most are engagement-inert; filter deterministically before
   spending judgment tokens (a value flips engagement only if it changes acts
   lifted, actor-admissibility, a governs hit vs declared concern, or protects
   vs protects_concern).
4. SPLIT MINING (class-2 UNSAT): split_mining_candidates.json + _report.md.
   ~5 atoms with blind annotation criteria. Adoption path: two-seat blind
   annotation of which ASSERTS carry each context atom -> regression ($0) ->
   any new FP adjudicated. Pre-adoption recall checks required for the 2
   medium-risk atoms (see report §3).
5. CONTRACT 8-A3: modulators (trigger/scope/defeater/manner-form/end) must be
   reified as atoms at translation time; census->mine->mint pipeline is the
   standing repair loop.

## Terminality language (READ THIS FIRST — 9g-addendum)
Every "TERMINAL" verdict in this repo is RELATIVE to a frozen mechanism inventory
and EXPIRES when vocabulary/declarations grow. The current terminality_verification.json
stamps its inventory and marks 13 nodes PENDING-VOCAB (reachable by the annotated,
not-yet-declared context atoms). Do not treat any node as unfixable-forever; treat
TERMINAL-* as "exhausted the named inventory". The context-atom declaration design
round (9b, design tier) is expected to convert PENDING-VOCAB nodes.

## What happened after the first version of this handoff (all committed/pushed)
- DEFINITIONAL LANE ADOPTED: +8 TP (104/74/183), sole FP adjudicated defensible.
  Escalations done: 3-node act ruling, 259/268 queue items proven inert, 9 ruled.
- OBJECTIVITY AMENDMENTS REJECTED by name (instrument-wrong FPs 2/4 and 4/6);
  narrowed conditional left open (OBJECTIVITY_AMENDMENT_DECISION.md).
- 9f BREADTH REVIEWS + LABEL PANEL done: n007 gained 2 governs labels; n005
  proposal refuted; regression unchanged.
- CONTEXT-ATOM LAYER annotated corpus-wide (2 Opus seats, 81 consensus credits,
  20 disputes queued): 4 atoms, recall checks pass, DECLARATIONS NOT YET DESIGNED
  — the layer alone changes no engagement.
- DECLARATION-SEARCH PROTOTYPE (decl_search_proto/): durable Opus prompt +
  schema + validator; two runs complete, validator green both times. Read
  RUN1_ASSESSMENT.md (both runs' assessments). Headlines:
  * proposals are mergeable module deltas with charter arithmetic computed by
    mutating v18 and re-running the real instrument;
  * net-positive hypotheses: help purpose_concern +empowerment (+7/-3), caution
    +harm-prevention (+2/0), caution +epistemic-autonomy (+2/-2);
  * fail-open wall-flip failure class rediscovered from data (caution +society
    4/79) — trust the discrete-arithmetic step, never the soft fit;
  * CARVING QUESTION CLOSED: of 40 unresolved mismatches, only 3 are
    byte-identical to opposite-verdict colliders across all 543 columns
    (help::l797_830_n011, harm::l831_1000_n001, harm::l831_1000_n011) and they
    are EXACTLY the nodes behind the two deferred act-refinement atoms from
    split mining (provide:forbid.form_equivalence, exhibit:illustrate) — two
    blind-to-each-other methods agree on nodes and fix family. No open search
    remains; it is a closed work list.
- CRITERION STANDING (in-sample, all-truth): caution 0.941, harm 0.953, help
  0.960 under match-or-adjudicated-defensible; raw match 0.81-0.85; Matt's
  human-panelist baseline 71%. NOT yet certified — that is round-4's job.

## THE HIGHER-LEVEL GOAL and the path from here
Goal: a validated ASP-translated corpus whose relevance matching runs
symbolically (no LLM at query time) at frontier-panel-equivalent quality, with
everything generalized into the contract so the NEXT document (Anthropic
constitution) is right the first time. Two arcs remain:

ARC 1 — CERTIFY THIS DOCUMENT (order matters; a-c are one design round):
 a. 9b DESIGN ROUND (design tier — strongest model, NOT Opus): derive blind,
    document-grounded justifications for: the 4 context-atom declarations
    (which behavior consumes which atom), the 3 fitted purpose_concern
    proposals, and the narrowed objectivity conditional if justifiable. Inputs:
    context_atoms_consensus.json, declaration_proposals.json (deltas +
    blind_justification_stubs), document_ends.json. Truth values stay out of
    the room; the arithmetic is checked only AFTER a justification stands.
 b. MINT the two act-refinement subtypes via the standard pipeline: blind
    criteria already written in split_mining_candidates.json -> two-seat Opus
    annotation -> regression -> new-FP adjudication (Fable).
 c. Adjudicate the 5 predicted breaks from the purpose proposals (Fable, small).
 d. Re-run verify_terminal.py (inventory grows -> PENDING-VOCAB resolves; the
    remainder is terminal against the ENLARGED inventory — say it that way).
 e. MAINTENANCE before any census-based claim: satisfiability_census.vector()
    must merge definition_* lanes + context atoms (it predates both).
 f. ROUND-4 CERTIFICATION (~0.4M Fable, post reset): frozen instrument, fresh
    draws, 9e fresh-pool bands, prospective bucket assignment. This is what
    converts 0.94-0.96 in-sample into the certified claim.
    (⚠️ CORRECTED 2026-08-21: this line said "post Sat-9pm reset"; Matt confirmed
    the reset is SUNDAY 9pm PT / Aug 23 — the signed round-3 prereg record agrees.)
 g. Fold the 20 context-atom disputes + remaining panel_rerulings; final ledger.

ARC 2 — GENERALIZE AND GO TO THE NEXT DOCUMENT:
 h. The contract already carries the generalized lessons (8-A1..A3, 9a-9g incl.
    inventory-relative terminality). Before translating the constitution,
    walk TRANSLATION_CONTRACT_V2.md top to bottom as a checklist.
 i. OPERATIONALIZE THE HARNESS for the next document: the loop is now fully
    scripted piecewise (census -> split-mining -> two-seat lanes -> escalation
    -> charter regression -> verify_terminal; decl_search_proto as the
    declaration-search inner step). Wire a driver; Matt's approved division:
    Opus executes written specs, Fable only for adjudication/rulings/design.
 j. Constitution translation per the standing estimate (graph creation + doc
    translation, Opus-driven with Fable spot-audits; semantic-audit parity
    pre-test first, ~0.05M).

MODEL-TIER REMINDERS: 9b design round and any one-shot measurement design are
design-tier work — do NOT push onto Opus. Adjudication/flip rulings are
Fable-doctrine (Opus failed parity 0.38). Annotation lanes are Opus-proven.
## Hard rules that bite (do not relearn these)
- Never lower a floor to pass; labels direct ATTENTION never TRUTH; every new
  FP adjudicated or the config is inadmissible; prereg expectations frozen
  before measurement; rulings written into the repo with rejected alternatives
  named; machine-check every subagent exit claim (Opus has twice self-reported
  false completion); cd to behavior_pilot before running anything (imports).
- Judgment-tier doctrine: adjudication/rulings = Fable only; annotation = Opus
  OK; mechanical execution = any tier with written plan.

## CAMPAIGN START — the 10-hour push to certifiable, publishable data (2026-08-21, Matt-approved)
BASELINE COMMIT for review: 5cc216272042942d0ba51966070168fddeb53d25
(d3-worked-example, clean tree, in sync with origin). A reviewing Fable agent:
review FORWARD from this commit — everything after it is this campaign.

MANDATE (Matt, 2026-08-21): inside one 10-hour human-attention window
straddling the Sun-9pm-PT Fable reset (Aug 23), produce (1) round-4
certification of this document, (2) zero-adaptation generalization runs on
TWO held-out behaviours — harmlessness-to-the-user + objectivity-on-
contested-questions (chosen for diagnostic spread: adjacent-family protects-
wall flip + maximal-distance answer-quality shape; ai_character_index was
checked the same day: NO frontier truth exists beyond the 3 dev behaviours x
2 docs, so truth is fresh-draw blind adjudication; small-panel v2 verdicts
are attention pointers only; if the aci owner produces frontier verdicts
they enter ONLY as a pre-declared comparison layer, never truth), and (3) a
blog series (goals / design / results) + living summary document.

STANDING PROCESS RULES FOR THIS CAMPAIGN (Matt, 2026-08-21):
- Test-driven where possible; where automated tests are not realistic, the
  validation method is written BEFORE the work and then checked (manually,
  with Matt's help where asked).
- Every completed work item gets a clean-context ADVERSARIAL subagent review
  for engineering excellence and consistency with the higher-level goal
  before it counts; a positive finding stops the item until fixed.
- All of Phase 0 (arc-1 items a-e, round-4 prereg draft, generalization
  prereg, blog scaffolding) is autonomous; Matt's attention is spent on
  signatures, /usage checkpoints, falsifier readings, and writeup review.
- Round-3 prereg (signed, sha 69631bf3...) is SUPERSEDED unrun: it froze
  contract v13; the instrument has moved to v18. Round-4 needs a fresh
  prereg re-derived from v18 all-truth.
- The handoff's "Matt's human-panelist baseline 71%" currently has NO source
  artifact; it must be sourced or struck before it appears in any writeup.
