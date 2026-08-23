# CAMPAIGN REVIEW BRIEF — the 10-hour push (for Fable top-review)

You are the top-level adversarial reviewer for a research campaign. Attack;
do not confirm. This brief is your map: what the campaign did, what has
already been adversarially reviewed and how it held, what is under review
right now, and where to aim your own attack.

BASELINE: commit 5cc21627 (d3-worked-example). Everything described here is
commits 5cc21627..HEAD (currently ~46 commits; `git log --oneline
5cc21627..HEAD` is the ledger). Work directory:
walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/.
Campaign record: HANDOFF_CURRENT.md (campaign section, bottom),
../EXPERIMENTS.md (entries 9-13).

## 1. What the campaign is

Goal (Matt, 2026-08-21): inside one 10-hour human-attention window
straddling the Sun-2026-08-23 9pm-PT provider reset, produce (a) round-4
certification of the OpenAI Model Spec for the three dev behaviours, (b)
zero-adaptation generalization runs on SIX never-consulted behaviours, (c)
a blog series + living summary. The instrument: a label-free, query-time-
symbolic relevance engine (relevance_by_act.py) over a typed translation of
the document; truth is a ledger of blind adjudications; panel verdicts
(v3w/v5 frontier benches) are comparison material only, never truth.

Standing rules that bind everything below: never lower a floor to pass;
labels direct ATTENTION, never TRUTH; predictions frozen before measurement;
rulings recorded with rejected alternatives named; every new FP adjudicated;
machine-check every subagent exit claim; a positive adversarial finding
stops the lane until fixed.

## 2. What was done, by lane (with artifact locations)

### Arc1-e — census faithfulness (CLOSED, adversarial CLEAR after 4 rounds)
satisfiability_census.py's vector now mirrors the instrument under
addendum-3 semantics: CURRENT = frozen instrument per behaviour (dead slots
masked: contexts always; protects/purposes unless declared), REACHABLE =
design space (all declarable slots + consensus context atoms). Three
inert-feature false-SEPARABLE classes found and fixed across the rounds
(assert status; none/other sort sentinel; contexts slot); standing pinned
probe (SLOT_INVENTORY / DEAD_SLOTS_PINNED in test_satisfiability_census.py)
guards the class; 36 tests. Records: panel_run1/convergence/
CENSUS_VECTOR_FIX_PREREG.md (addenda 1-3), satisfiability_census_*
artifacts, LATENT_FIX_REGISTRY LF-3/LF-4 (repo root:
semi-formal-experiment/LATENT_FIX_REGISTRY.md).

### Arc1-b — subtype mint (CLOSED, CLEAR-WITH-NITS after 2 rounds)
Two act-refinement subtypes minted by two-seat blind annotation:
provide:forbid.form_equivalence (10-node consensus), exhibit:illustrate
(185 = 169 first-pass + 16 extension; extension seats ran in Matt's Claude
venue after provider input-inspection rejected every harness venue —
venue + sanitization rulings recorded). M1 (CURRENT bit-identical) held;
M2 held 3/3: all three former collider mismatches REACHABLE-separable +
addressable_by_declaration. Terminality fence extended to refinement marks;
45 PENDING-VOCAB re-stamps. Records: panel_run1/convergence/
SUBTYPE_MINT_PREREG.md (addenda 1-5), act_refinements_FINAL.json,
terminality_verification.json. Known caveat on record: extension agreement
1.0 came from two same-family sessions (non-diagnostic for shared
interpretive bias).

### Arc1-a / 9b — design round (justification pass + arithmetic)
9B_DESIGN_ROUND.md is the record. Justification pass: 9 declarations
justified from the document (PC-1..5 purpose candidates, CA-1..4 context
atoms), 1 HOLD (objectivity conditional — its natural home is the held-out
objectivity behaviour), 12 rejected with document- or scope-grounded
reasons. Fit-rank disclosure recorded (the five purpose candidates' fit
scores ran monotone with initial outcomes; PC-4's original dismissal was a
motivated-reasoning signature, caught by review, redone with document
work). Arithmetic: per-delta charter measured (help +empowerment 13/3 and
caution +harm-prevention 3/1 charter-positive; trust 7/9, predictability-
reliability 6/12, epistemic-autonomy 3/4 negative; all four governs_
conditional declarations INERT — unconditional governs_concern wins over
governs_conditional in signature_ok, recorded as mechanism insight). Exact
joint lattice enumerated (flip sets pairwise disjoint; the charter-positive
bundles carry parasitic negative-marginal deltas — adoption restricted to
positive-marginal deltas). v19_ADOPT_CANDIDATE.json = v18 + the two
charter-positive deltas; adoption FINAL only after the 29-node
defensibility batch (DEFENSIBILITY_BATCH_PROTOCOL.md) adjudicates the new
FPs post-reset.

### Generalization workstream (attempt-1 staged end-to-end)
- GENERALIZATION_PREREG_DRAFT.md — SIGNED by Matt 2026-08-21 (six
  behaviours, 3+3 sequential, FATAL stop rule, 40-node draws, S1 floor 0.70
  with the 71% anchor STRUCK, re-measurement protocol, four pre-declared v5
  comparison cuts, truth path closed to panel data; addenda 1-2:
  anchor-granularity strata operationalization + draw correction).
- Six a-priori modules built BLIND (definitions + frozen vocabulary only;
  verdicts/truth/census forbidden): generalization_builds/*.json +
  _RATIONALE.md each. Systemic defect caught pre-scoring: bespoke does-names
  are silently discarded by behavior_acts() (three modules engaged nothing);
  repaired by reviewer-verified canonical translation, no new declarations;
  root causes recorded (ambiguous spec clause + stale docstring, corrected).
  Engagement spans 26-279/762 (tradeoffs broadest, disclosed as the
  attempt-1 property). Vocabulary-gap findings clustered in five families
  (meta/procedural, calibration/degree, prohibition, non-human parties,
  answer-quality acts) — recorded per module, fix-ledger will classify.
- draw_generalization.py: seeded stratified draws (20 engaged + 20 not,
  top-up rule; 50/50 panel-agree/panel-split v5 strata at anchor
  granularity; determinism tested). Six draws committed:
  generalization_builds/draw_*_seed20260822.json.
- ruling_packets/*.json: 240 generalization + 29 defensibility BLIND
  packets (span + definition + question only — no prediction, no draw side,
  no truth); ruling_packets.py regenerates them.
- modules_contract_GENERALIZATION.json: the six modules assembled on v18
  lineage.

### Round-4 + writeups
- ROUND4_PREREG_SCAFFOLD.md: protocol fixed (draws, rulings, canary +
  /usage checkpoints, cost, falsifiers F1-F5, success criterion, errata
  rule); freeze sections derive at instrument freeze (post-reset, after
  adoption finalizes). Lineage: rounds 1-3 (round-2: help PASSED, harm F1,
  caution F1-by-2, all fixed; round-3 signed 2026-08-19, SUPERSEDED UNRUN —
  froze v13, instrument moved to v18).
- blog_drafts/: 00-SERIES-OUTLINE.md, 01-what-and-why-DRAFT.md,
  02-technical-design-DRAFT.md.
- data/panel-v5/: collaborator frontier bench ingested (31,293 verdict
  rows, blob-verified at pinned commit ef08e676; PROVENANCE.md carries the
  comparison-only usage rule).

## 3. Adversarial review ledger (before your review)

| scope | rounds | verdict |
|---|---|---|
| Arc1-e census fix | 4 | CLEAR (mutation-tested probe; three defect classes fixed; reviewer-caught undercount disclosed) |
| Arc1-b mint lane + integration | 2 | CLEAR-WITH-NITS (all findings resolved; LF-4 registered) |
| Six module builds | 1-2 each, incl. post-repair re-verification | all CLEAR-WITH-NITS; corrections recorded append-only |
| 9b justifications + campaign pace | 1 | BLOCKED-on-PC-4 → fixed (PC-4 redo, fit-rank disclosure, instrument-side concerns demoted to triage) |
| Draw machinery + contract + arithmetic recompute | 2 | CLEAR-WITH-NITS: all fixes verified by two independent implementations (all six draws reproducible from raw inputs at the registered seed; full shas; correction record append-only); N5 formally withdrawn by the reviewer; residual nit (stale docstring) fixed. Cleared for attempt-1 rulings. |
| Ruling packets + defensibility protocol | 2 | round 2 BLOCKED (stale-vs-draw membership drift after the parallel draw fix; shuffle seed stored inside the file it protects) → resolved: all seven files regenerated against current draws with set-equality gating; seed moved to campaign-record material (base 20260823 + per-file index) with a written dispatch rule (seat receives only the prompt string); third verification requested |
| 9b design-round fixes re-verification | 1 | BLOCKED → resolved (b81afbfa): false disjointness lemma corrected (2-node E/P&R fix overlap, inclusion-exclusion on the triple); CA mechanism-facts self-contradiction corrected; PC-4/PC-5 asymmetry stated; citation swap + nits fixed; one MEDIUM refuted by arbitration (v19_ADOPT_CANDIDATE.json exists at 066fd263). Decisions unaffected. |

## 4. Current state + Sunday sequence

Now: all pre-reset work complete; tree clean; three gap reviews running.
Post-reset (Matt's venue executes Fable; orchestration cannot — Fable is
subscription-side, $0-API): (1) defensibility batch (29 blind rulings +
20% panels) → charter recomputed on rescued counts → final adoption of the
9b deltas; (2) instrument freeze → census re-run → round-4 prereg re-issue
→ Matt signs → round-4 run (~0.4M Fable; canary = helpfulness, /usage
checkpoints, falsifiers F1-F5); (3) six generalization ruling sets
(~0.5-0.6M) → attempt-1 transfer verdicts + fix ledger (EXPECTED /
ALARMING / FATAL classes; FATAL in block 1 fires the stop rule).

## 5. Where to aim your attack

Highest-value targets, in rough order:
1. The generalization attempt-1 design as a MEASUREMENT: do the six blind
   modules + 40-node draws + fix-ledger classes actually test "a new
   behaviour costs a fixed procedure, not another campaign"? Where could
   the verdict be an artifact of the build/repair history rather than
   transfer? (The F1 defect + repair happened AFTER builds froze as
   "no revision before scoring" — the repair was translation-only and
   reviewer-verified, but interrogate the seam.)
2. The truth doctrine under load: the defensibility batch adjudicates the
   SAME nodes whose labels the 9b arithmetic already used. Is the
   one-pass/no-iteration protocol actually sufficient against
   adjudicate-reject-adjudicate fitting?
3. The 9b adoption rule's interaction with the joint lattice: adoption was
   restricted to positive-marginal deltas — check that restriction is
   principled, not a post-hoc selection that happened to dodge parasitic
   bundles.
4. Strata operationalization (anchor granularity, max-over-paragraphs):
   could it systematically bias the panel-agree/split composition of the
   draws in a direction that flatters the instrument?
5. Anything in the record where a claim outruns its artifact (the
   campaign's own discipline demands claims be traced to artifacts —
   trace a sample).
6. The blog drafts' scope honesty (they are DRAFTS; post 3 is unwritten).

Also verify the ledger itself: pick any three claims from section 2 and
trace them to artifacts; pick any two "resolved" review findings and check
the resolution actually landed in the file it claims.

## 6. Output format requested

Findings by severity (FATAL / ALARMING / EXPECTED-nit) with evidence
(artifact paths, recomputations), disposition per finding, and a final
verdict: CLEAR / CLEAR-WITH-NITS / BLOCKED. Confirmed findings stop the
affected lane until fixed; uncertain findings go to arbitration against the
artifacts before acting (campaign doctrine — reviewer false-positives are
expected and have occurred).
