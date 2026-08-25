# ITERATION 2 — DECISION RECORD (how-to-approach-tradeoffs, 2026-08-24)

## Batch and routing
13 attempt-2 misses (ITER1_ATTEMPT2_SCORED.json). R1 escalation on the
certified Opus venue confirmed ALL 11 wave-single misses at panel tier
(0 overturns, 1 split — contrast attempt-1's 3/9 single-wave overturns).
Every mismatch is real. Truth: ITER2_TRADEOFFS_REPAIR_TRUTH.json (n=75).

## ADOPTED BATCH MOVE (pending V5)
1. `does += override` (module act-lane; C-D). The F1-era build rendered
   chain-of-command as `follow_chain_of_command->comply`; the corpus's
   actual conflict clauses head to canonical `override`
   (override_instruction, override_root_instruction, ignore_instruction).
   Fixes l699_796_n010; +2 unruled act-lane gains.
2. `machinery_concern: ["override"]` — NEW TYPED GATE (C-I(I1) consumer
   build, engine extension in relevance_by_act.relevance; registry +
   handshake test updated in the same commit per A12; 43 tests green;
   zero effect on any module not declaring it). Semantics: a node
   excluded by the STRUCTURAL walls (all-authority_plumbing or
   all-non-assistant-actor) engages iff it carries a functor bridging to
   a declared machinery act. Governs wall waived on this channel
   (machinery clauses' governs classification is itself structural);
   protects wall retained; additive; fail-inert when undeclared.
   GROUNDS: the definition names "chain-of-command as conflict resolver"
   as core subject matter; the panel ruled the spec's instruction-
   hierarchy DEFINITIONS (l1_170_n040 3-0, l1_170_n046 3-0) relevant; the
   global plumbing/actor exclusions — correct for every other behaviour —
   structurally forbid expressing "the machinery is the subject". This is
   the I1 row of the calculus's failure-surface table, the
   "purpose-as-wall" precedent class. Fixes n040, n046; +11 unruled
   machinery gains (the L1-170 instruction-hierarchy cluster).

## CLASS CARD (V3)
FAMILY: document conflict-arbitration machinery, override-class.
GENERAL FORM: clauses stating which instructions yield to which — the
document's own priority ordering — bear on the behaviour whose construct
is that ordering. PREDICTED MEMBERS (unruled, could not have motivated
the move): l1_170_n026/n043/n054/n057/n059/n060/n091, l171_426_n014/n016,
l3383_3501_n010, l4572_4692_n003 — the card predicts blind seats rule
drawn members of this family RELEVANT (realization-tested at V5).
Held-out mechanical check: all 13 unruled gains are structurally-excluded
override-headed nodes — zero gains outside the named family.

## VALIDATION
V1 charter (probe, n=75 ledger): fixes 3, breaks 0. V2: drift 0 degraded /
0 substituted / 1 augmented (allowed). V3: card above. V4: zero new ruled
flips (13 unruled gains carry no truth; they are the card's predictions).
V5: ITERATION2_V5_PREDICTION.json registered before any attempt-3 ruling.

## REJECTED ALTERNATIVES (by name)
- `does += provide` (would reach FNs n011/n013/n012): +151 corpus
  engagements (+139 even with an arg_sorts wall — sorts content/response
  dominate both sides). The attempt-1 transfer failure was exactly this
  broad-canonical-head shape; rejected as a precision bomb.
- `governs_concern += identity_meta` (to pass n040/n046 through the
  wall): re-engages 6 persona/identity presentation nodes the iteration-1
  card classed non-arbitration, and still requires the structural
  exemption anyway; the machinery gate reaches the target class without
  touching the persona class; rejected.
- Broad machinery exemption (respond/comply machinery acts included):
  34-node blast radius including voice-instruction and tool-mechanics
  clauses with no arbitration content; rejected — the act-typed
  declaration exists precisely to scope this.

## SUSPENDED-OPEN at this inventory (recorded, not hidden)
- FP side (5, all panel-tier): l2821_3040_n029, l3147_3238_n009,
  l3596_3876_n028, l3954_4251_n040, + standing l3954_4251_n038 — the
  single-consideration prescription family; no declarable separator
  exists without breaking panel-tier TPs (iteration-1 analysis extends:
  same governs/context/purpose signatures as kept TPs). Re-enterable via
  provide/act subtype mints or a purposes consumer IF a separating
  purpose profile is ever measured (current profiles overlap).
- FN side (5): n011/n013/n012 (provide-lane, see rejected alternatives);
  l1_170_n058 + l699_796_n008 (definitional-lane nodes with no act
  credits — the EXAMPLE-NARRATION act-lift scope ruling stands; C-V
  translation-repair lane is the named re-entry).

## Fix-ledger class (prereg vocabulary)
The FN reach defect is ALARMING-class (a distinction the instrument
lacked: machinery-as-subject-matter), resolved by a typed inventory
extension with design record — exactly the census->build pipeline the
contract prescribes. The does-lane fix is EXPECTED (module-local).
