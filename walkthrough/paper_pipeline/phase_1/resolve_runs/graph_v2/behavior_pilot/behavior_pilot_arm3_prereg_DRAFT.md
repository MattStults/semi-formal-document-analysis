# PRE-REGISTRATION DRAFT — arm 3: SYMBOLIC relevance (ASP corpus on the critical path)

Status: SIGN-READY, FROZEN 2026-08-18. Frozen state: modules_contract_v7 /
behaviors_canonical_v7 (census scaffold) / act_bridges.lp (actor-gated,
repair-7 acts) / relevance_by_act.py ARG_WALLS_ENABLED=False /
situation_types.json r2 / arm_ab.py / relevance_by_dependency.py (input
channel, own column); validation ledger attached
(ARM3_ROUND_LEDGER.md, frozen at r6). Test slice scored ONCE after Matt's
signature, by `arm_ab.py --slice test --canonical behaviors_canonical_v7.json
--modules modules_contract_v7.json` at the freeze commit, plus the
input-relevance channel reported as its own labeled column. Matt's rulings incorporated: Q1 both sub-arms (2026-08-18);
arm (b) redefined as MUTATION-BASED scope discrimination (Matt's design,
2026-08-18 — "changing the target to something the ontology defines as
clearly different and seeing if it still succeeds"); Q2 refinement to
plateau on a three-way split (Matt: "why not the 3 way split?").

## The claim
Relevance computed FROM the translated ASP corpus — no LLM anywhere in the
query path — reaches deviation-defensibility at least equal to the LLM-seat
instruments (cold-start arm 1, tuned arm 2) under the same Fable truth
tier, at $0 per query and with a stated, printable reason per verdict.

## Sub-arms (both registered; both reported)
(a) SYMBOLIC-ONLY: a module is relevant iff it asserts a deontic status on
    a canonical act the behavior performs (relevance_by_act.py through
    act_bridges.lp).
(b) +MUTATION: refine (a) by firing + scope mutation (arm_ab.py). Ground
    the behavior's canonical facts (sorts + scope-dimension values) through
    situation_bridges.lp; per act-engaged module: fires under original
    facts = scope_confirmed (kept); silent under original but fires under
    >=1 single-fact mutation to a canonically-distinct value =
    scope_mismatched (declined — the module positively engages a DIFFERENT
    scope); silent everywhere = undetermined (kept — act evidence stands;
    silence is not evidence). Three states, never collapsed. Fully
    symbolic; one clingo solve per (module x variant).
    Difference from (a), stated: (a) has no scope discrimination; (b) buys
    it with mutations, and can only DECLINE (a)'s engagements, never add.

## Ontology under test and refinement discipline (Q2 as ruled)
The generated ontologies (act: 11 canonical + r1 subtypes, two-level,
subtype-implies-parent; situation: typed hierarchy — sort + scope
dimensions, 3516 bridges) are refined in ROUNDS until plateau. Per round:
refinements may consult ONLY (i) tuning-half verdicts, (ii) validator
findings (validate_ontology.py), (iii) reference cases (S4). The
VALIDATION slice (arm3_split.json) is scored per round and watched for the
plateau; the TEST slice is scored ONCE at freeze and is never consulted
during refinement. Stopping rule (pre-stated): validation deviation-
defensibility gains < 0.02 on all behaviors for two consecutive rounds, or
4 rounds, whichever first. Behavior canonical instances
(behaviors_canonical.json) are query-side and iterate under the same
tuning-only discipline.

## Truth tier, split, metric — continuous with arms 1–2
Fable adjudicators, calibration rule (ESTABLISHES-anchored). Split:
arm3_split.json — tuning (seed 20260817, unchanged), validation/test 50/50
over all remaining adjudicated nodes (seed 20260818), test augmented with
12 blind-ruled balancing negatives per behavior (seed 20260819); FROZEN.
Test sizes: 61/60/53. Metrics: deviation defensibility (primary),
engagement/decline defensibility, recall. Reported beside arms 1 and 2 on
the same test slice, same truth.

## Pre-stated predictions and falsifiers
* Prediction: arm (a) >= tuned seat on >= 2 of 3 behaviors on the test
  slice; arm (b) >= arm (a) on precision without losing > 0.05 recall.
* Margin rule: with ~53–61 test nodes, one node is ~2 points; differences
  <= 2 nodes' worth are reported as "within resolution", not as wins.
* Falsifier: arm (a) < cold-start seat on any behavior, OR arm (b) <
  arm (a) on deviation-defensibility (the mutation stage would be dead
  weight), OR the act validator BLOCKED at freeze (A7 must pass; A1/A4
  clean), OR T4 firing-consistency failing at freeze. Any of these is
  reported as-is, no post-hoc rescue.
* Scoring is ONE run of arm_ab.py --slice test at the frozen commit; the
  numbers land in the report unedited.
