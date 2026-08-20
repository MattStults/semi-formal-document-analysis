# TRANSLATION CONTRACT V2 — what the NEXT document's translator receives
# (assembles every retrofit lesson of 2026-08-18 into translation-time requirements)

Matt's ruling: the ontology work must be "included in the automated
machinery for next time." This document is that machinery's specification.
Everything below was learned by RETROFIT on the Model Spec corpus — each
requirement cites the retrofit artifact that proved its need. The next
document's modules are BORN conforming; the gate enforces at translation
time; the bridge files are GENERATED from declarations, never classified
after the fact.

## 1. Act declarations are 4-tuples
Every act is declared as `{name, canonical, arg_sort, actor}`:
* `canonical` — one of the two-level canonical act ontology
  (behavior_pilot/behavior_vocab.json `canonical_acts_provisional` +
  `_act_hierarchy`). Retrofit cost of not having this: 720 functors
  classified post hoc, 3 audit rounds, ~7% corrected
  (act_bridges.json, full-audit commit).
* `arg_sort` — what the act acts ON (request/topic/content/instruction/...).
  Retrofit lesson: verb-only bridges caused the H1 wrong-argument failure
  class, 15/51 of the tuning failure census; walls apply only to
  homogeneous verb families (relevance_by_act.WALLED_VERBS).
* `actor` — assistant|developer|user|system. Retrofit lesson: H5 —
  developer acts engaged assistant behaviors; name-guessed tags were wrong
  12/19 times, assert-evidence tags correct (act_actors.json).
Gate: act with no canonical binding = HARD; unknown canonical = HARD
(NEW:<name> escape allowed, surfaces for ontology growth — 2/720 on the
Model Spec, both genuinely novel).

## 2. Situation concepts are typed at declaration
Every input/ontology concept declares `{sort, dims, generic}`:
* sort from the fixed list (request, response, user, content, action,
  instruction, party, setting, information, assistant, tool, other) —
  `other` >20% = catch-all review (T5).
* dims — scope-dimension values it EXPRESSES (party/intent/setting/
  reversibility/content_class/stakes). Retrofit: 2,065 concepts typed post
  hoc; two typing errors caught only by T4 firing-consistency (compound
  conditions split across values; normative conditions typed as case
  facts — both now sweep rules in classify_situation_sorts).
* generic: true iff the concept holds for ANY entity of its sort — the
  reversal derives only generic or dim-carrying concepts (measured:
  ungated reversal made chain_of_command_requires_refusal derivable from
  request(X), firing l609_698_n010 spuriously).

## 3. Modals must land in asserts (M30)
An assertless module whose CLAIMS carry a modal is a dropped-norm suspect
(gate detector `dropped_modal_assertless`, review tier). Retrofit: 7 hits,
2 real dropped norms incl. the agentic web-trust norm — repaired via
adjudicate -> blind-verify -> repair-run ceremony
(behavior_pilot/m30_adjudication.json, repair-7). Adjudication categories:
DROPPED-NORM / SIBLING-OWNED / DEFINITIONAL — only the first is a defect.

## 4. Norm-objects for actless norms
Rankings, consequence claims, and definitions with normative force either
declare the acts their norm governs (the outcome_ranking exemplar:
answer/hedge/decline) or are reached via the PROVIDES/NEEDS input-
relevance channel (relevance_by_dependency.py — Matt's design; 169/181
actless Model Spec modules reachable). A module reachable by NEITHER
channel is invisible to every query: gate-reportable.

## 5. Seam discipline from day one
One arity + one document-wide gloss per shared name, enforced hard
(SEAM_CONTRACT growth rule). Retrofit: 93% of 1,739 input names were
single-module coinages; 25 arity + 18 section-local-gloss collisions
queued for repair ceremony.

## 6. The validators run per-chunk, not post hoc
validate_ontology.py (A1-A7 acts, T1-T7 atoms), validate_behavior_module.py
(B-side), corpus_gate.py M-series — all wired into the translation loop the
way the mechanical gate already is; a chunk seals only when they pass.
Firing-consistency (A7/T4) runs against a hand-grounded reference case
built in the FIRST chunk and kept for the document's lifetime.

## 7. Asserts declare WHOSE interest the norm protects (from the E1 terminus)
Measured 2026-08-18 (deviation ledger + three ablations): party walls
retrofitted at act level (gloss-typed) collapse recall (FN 28->43); at
module level (situation-dim join) they are net zero (8FP<->8FN, signal in
264/762 modules only). "Whose interest does THIS norm protect" is
per-ASSERT information: dual-use clauses protect user AND third parties;
gloss mention is not protection. The next document's asserts carry
`protects: [user|third_party|developer|minor|society|...]` at translation
time, where the span states it; behaviors then wall on norm-protection
directly. Retrofitting the Model Spec corpus's asserts is a future
ceremony (annotation sweep + blind verification), not a query-side patch.

RETROFIT EXECUTED + TIER REQUIREMENT (2026-08-19, evidence:
panel_run1/PROTECTS_LAYER_RECORD.md): the Model Spec layer now exists
(assert_protects.json, frontier-labeled, audited keys locked in
protects_locked.json). MEASURED: small-tier seats plateau at ~0.60
exact-set on this judgment (DeepSeek 0.60, Haiku 0.62 on identical
inputs) — the deficit is stable normative doctrine on boundary cases
(unspecified<->user on epistemic norms; co-protection breadth), which
rubrics do not close. The next document annotates via
ESCALATION-BY-DISAGREEMENT: two cheap seats label every assert; agreement
keeps the label (measured 0.88 vs frontier, n=24 — REVALIDATE on >=100
asserts before relying), disagreement escalates to a frontier instance
(~40% volume, simulated hybrid 0.93). Inputs MUST include the verbatim
SOURCE TEXT (two rounds failed on paraphrase-only input) and every
node id must resolve to its span (15 drifted ids yielded empty spans
silently — check span non-empty per item, fail loud).

## 8. Every assert emits its full NORM SIGNATURE at translation time (closure ruling, 2026-08-19)

A norm is a typed tuple, and relevance failures are projections of it lost in
translation. The signature (A PRIORI — derived from deontic/frame structure plus
document mining, NOT from behavior failures; the 75-FP census is the CHECK that
confirmed closure, 74/75):

  (act, actor, protects, governs_aspect, scope, force, authority)

- act/actor/force: already required (§1, deontic statuses).
- protects: §7 (built for the Model Spec; 985 asserts, frontier-grade).
- governs_aspect — WHAT QUALITY of the act the norm constrains. Value vocabulary is
  MINED per document (the way the act ontology was mined), seeded with the skeleton:
  substance_usefulness | objectivity_neutrality | accuracy_calibration | tone_manner |
  safety_of_manner | formatting_style | identity_meta | operational_hygiene.
  This was the dominant census lever (40/58 + 17/17 fresh-draw FPs).
- scope: §2 typed situations, per-assert where the span narrows it.
- authority: instruction-level/precedence plumbing flag — a norm ABOUT the document's
  own machinery engages no behavior wall (7/58 census).

ANNOTATION PROTOCOL (measured, binding): bulk seat sweeps ride dispatch_core.py's
BATCH mode (graph_v2/dispatch_core.py: submit/poll/collect with resume-safety, spend
gate at submit, orphan sweep) — the 2026-08-19 retrofit sweeps ran on the live path
only because the author missed the existing plumbing; recorded so it isn't repeated.
Single pass per assert yields all fields;
dual cheap seats label everything, agreement keeps the label, disagreement escalates
to a frontier instance (solo small tiers measured ~0.60 exact-set). MEASURED UPDATE
(signature retrofit, n=100 pre-registered spot-check): agreed-cheap labels scored 0.78 —
BELOW floor; shared cheap-seat bias (safety_of_manner over-assignment) is invisible to
the disagreement trigger. BINDING: validate seats PER FIELD (the authority flag passed
at 0.97 while the aspect field failed), spot-check the agreed set at >=0.85 on >=100
items BEFORE trusting it, and budget full frontier for any field that fails — twice
measured (protects, governs), cheap tiers have not yet passed a judgment field's floor
on this document. Inputs carry verbatim SOURCE
TEXT; every node id must resolve to a non-empty span, checked loud. Calibration cases
with pre-registered expectations run before any sweep (incremental protocol).

CERTIFICATION (behavior-free, so the document is right FIRST TIME for unspecified
behaviors): per-dimension mutation probes — synthetic behavior pairs differing along
exactly one signature dimension; the instrument must discriminate every pair. Failures
localize the defective dimension before any real behavior is queried.

## 9. Generalized rules from the round-2 failure census (2026-08-19) — BINDING before any new document

9a. DIMENSIONAL PURITY of every slot vocabulary, validated BEFORE annotation begins.
Test: no two values in one slot may be simultaneously true of one beneficiary/norm
along different underlying dimensions. Attributes (age, vulnerability), contexts
(agentic setting, vulnerable interaction), and intents are SEPARATE FIELDS, never
values inside a role/quality vocabulary. Measured basis: the a priori purity audit's
flags coincided exactly with the empirically troubled values — protects.minor
(role x age; U18 false-engagement class, 36/71 minor-labels co-occur with user),
governs.safety_of_manner (quality x vulnerable-context; #1 seat-confusion pair AND
the spot-check failure locus), governs.operational_hygiene (quality x setting; #2
pair), acts.protective_response family (act x intent; the E5 reverts). Pure slots
(deontic force, authority flag) were also the tier-robust ones (0.97 at cheap tier):
purity predicts cheap-seat viability.

9b. BEHAVIOR DECLARATIONS ARE DERIVED A PRIORI, truth only validates. governs_concern,
protects_concern, and every wall declaration is derived from the behavior DEFINITION
by frontier judgment before any truth is consulted; adjudicated truth then validates
the derivation. Measured basis: harm's governs exclusion was left empty because
tuning-on-truth showed no gain on a precision-saturated adjudicated set — the FP mass
lived in the never-drawn pool and fired F1 (0.60 vs floor 0.81) in round 2. Tuning
declarations on available truth overfits walls to the sample.

9c. Seat-decomposition (per-aspect binaries, mechanical union) is REJECTED at small
tiers for the current impure vocabulary: pre-registered experiment (seed 20260821,
n=100 vs frontier layer) scored DeepSeek 0.29 / Haiku 0.20 exact with 66%/48%
cardinality anomalies (strict phrasing collapses to under-listing). May be re-tried
ONLY after 9a's purity fix, with a fresh pre-registration.

## 8-ADDENDUM (2026-08-19, from round-3 census): the ACTOR slot is REQUIRED in full
The §8 tuple's actor slot must be annotated as a complete typed field, not merely the
authority_plumbing boolean (the implementation shortfall that cost round-3 helpfulness
4 FPs and appeared as caution's census "other" class). Values (pending §9a mining +
purity check on each document): assistant | organization | developer | document
(authority_plumbing folds in as actor=document). Behavior walls engage ONLY
actor=assistant norms. Slot derived a priori (deontic agent position); value vocabulary
mined per document per §9a.

## 9d. All-truth regression table REQUIRED before any prereg (practice made law,
per Matt 2026-08-19): every instrument change is measured against the FULL accumulated
truth before a new registration is drafted; any regression on pre-judged cases requires
recorded grounds. As pools exhaust, certification converges to whole-population
validation (harm reached this at round 3: 70-node engaged population).

## 9e. Prediction bands come from FRESH-POOL evidence only (round-3 lesson): deriving
bands from all-truth measurements overstates fresh-pool performance because adjudicated
sets are engagement-favorable (measured: helpfulness all-truth precision 0.82 vs
fresh-pool 59/80=0.74; the inflated band fired F1 on an instrument performing at its
demonstrated level).

## 8-ADDENDUM-2 (2026-08-19): the PURPOSE/END slot is REQUIRED — measured basis
The factorization experiment (panel_run1/factorization_*) settled the telos question:
on the 18 hardest confusion pairs (9 residue FPs + 9 same-subtype TPs), rulings made
from BEHAVIOR-BLIND local descriptions alone (fields: constrains / purpose /
failure_mode, grounded in the span) matched panel truth 16/18 = 0.89 — panel
self-agreement level. Adequate local information EXISTS; fixed vocabularies were the
loss (the pre-registered subtype-granularity test failed its bar: 64% FP recovery at
27% TP cost — every finer subtype cell still contained both verdicts). REQUIRED for
the next document: (a) mine the document's OWN stated ends as the purpose vocabulary
(§9a purity check applies); (b) annotate purpose per-assert via the
purpose+failure_mode elicitation, BEHAVIOR-BLIND (blindness is what makes the slot a
document fact rather than cached relevance — the circularity objection dissolves only
under blindness, so it is binding); (c) behaviors declare which document-ends they
track; walls remain set-membership tests. Matt's method ruling encoded: naive a priori
description will not find every needed slot — the discrepancy census after each
certification round is the REPAIR loop that discovers missing slots (this one was
found by round-3's FP census; the actor slot by the same route).

## 9f. Label-breadth review before terminal claims (2026-08-19, from the caution-accuracy ablation)
Multi-label breadth noise (measured: exact-set 0.71 vs verdict-level ~0.9) has a consumer beyond walls:
ABLATION ANALYSES. A node engaging only through its weakest label looks irreducibly coupled when it is
merely under-labeled (measured case: l2126_2404_n017, whose caution-core moralizing forbids carried
objectivity-only labels). BINDING: no same-signature coupling may be declared terminal until the coupled
nodes' labels pass a breadth review; under-labeled asserts route to label panels first.

## 9g. Mechanical terminality verification (2026-08-19)
verify_terminal.py runs after every instrument change: FIXABLE moves are surfaced
automatically (it is also a fix-finder — it rediscovered the caution+objectivity
amendment independently); TERMINAL-DECL is proof-by-exhaustion over the finite
declaration space with inline receipts; TERMINAL-STRUCT fences the node to the
bridge/vocabulary space, where terminality is receipt-relative (PREMISE GAP
discipline). No terminal claim may appear in a report without its verifier verdict.

## 8-ADDENDUM-3 (2026-08-20): NO NORMATIVE MODULATION MAY LIVE ONLY IN PROSE —
## conditions, scopes, and defeaters are reified as atoms at translation time
Measured basis: the satisfiability census found 8 mismatch pairs vector-identical
to correct opposite-verdict nodes whose distinguishing feature was stated in the
span but never atomized ("if repeated at scale", "when they indicate illicit
intent", "no good-cause exception", provenance of the material, self-reference,
delivery-form equivalence). Mining recovered all 8 post hoc (split_mining_*.json)
— at the cost of a full census + mining + minting round the translator could have
avoided.
THE RULE (document-agnostic — no reference to any particular document's phrases):
whenever a clause MODULATES a norm — when it applies, to whom or what, under which
justification it is or is not defeated, in what form or manner, toward which end —
the modulator must be emitted as a structured atom in a declared dimension, never
left solely inside a read_back or gloss. The a priori modulator classes to check
each assert against (class-first, validate against known cases): TRIGGER (when),
SCOPE (to whom/what), DEFEATER (unless / notwithstanding claimed justification),
MANNER/FORM (how, incl. equivalence-of-form rules), END (toward what).
THE REPAIR LOOP (expected to be needed — the rule will be imperfectly applied):
the census -> split-mining -> blind-criterion minting -> two-seat annotation ->
charter regression pipeline built 2026-08-19/20 is the standing, document-agnostic
fixing mechanism for whatever the translator still leaves in prose. A missed
modulator is therefore a NORMAL, detectable, repairable event — not a design
failure; the design failure would be shipping without the census.
