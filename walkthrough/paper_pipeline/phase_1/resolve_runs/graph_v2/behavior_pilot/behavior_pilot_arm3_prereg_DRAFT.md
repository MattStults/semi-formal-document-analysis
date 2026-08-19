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
* Prediction, PER BEHAVIOR (validation-informed, stated before test):
  helpfulness — arm (a) BEATS both seat arms (expect ~0.75-0.85), arm (b)
  >= arm (a); caution — arm (a) comparable to tuned seat (within the
  margin rule) at higher recall, arm (b) expected slightly BELOW arm (a)
  (validation showed -0.03; if test confirms, (b) is reported as
  behavior-dependent, valuable on helpfulness only); harm — arm (a) above
  cold-start but BELOW tuned seat (defect 1), expect ~0.45-0.60.
  The equivalence claim is: arm (a) >= tuned seat on >= 2 of 3 behaviors.
* Margin rule: with ~53–61 test nodes, one node is ~2 points; differences
  <= 2 nodes' worth are reported as "within resolution", not as wins.
* Falsifier: arm (a) < cold-start seat on ANY behavior, OR arm (a) <
  tuned seat on ALL THREE, OR arm (b) < arm (a) on HELPFULNESS (the one
  behavior where validation predicts (b) helps — if it fails there, the
  mutation stage is dead weight), OR the act validator BLOCKED at freeze
  (A7 must pass; A1/A4 clean), OR T4 firing-consistency failing at freeze.
  Any of these is reported as-is, no post-hoc rescue.
* Scoring is ONE run of arm_ab.py --slice test at the frozen commit; the
  numbers land in the report unedited.

## Known defects AT registration (disclosed pre-signature; none is grounds for post-hoc rescue)
1. H1 wrong-argument engagements unfixed (walls off by tuning evidence;
   per-behavior argument declarations are future work). Harm expected well
   below the tuned seat.
2. Arm (b) grounds ~10% of engaged modules; decline-only; measured value
   mixed (helps helpfulness, costs caution). n-ary/constant reversal unbuilt.
3. ~5% residual bridge error (fresh blind sample 60/63).
4. T2 arity collisions unrepaired (35 drafts HELD post-test) — some
   firings/silences are corpus defects, not instrument verdicts.
5. 12/181 actless modules unreachable by any channel; input-relevance is
   one-hop, lightly validated, reported as its own column.
6. Truth tier single-model (arm-1 second-frontier control failed at 77%);
   all numbers mean "defensible under Fable-tier reading".
7. Decline denominators are small on help/caution — margin rule governs.
8. Validation slice consulted ~8 times across rounds (ledger discloses);
   its curve is advisory only.
9. Behavior modules hand-authored under the contract; behavior-translation
   automation is NOT the registered claim.

---

**SIGNED — Matt Stults, 2026-08-18.** Content sha256 at signing:
`a05adfcc50186b05fb4b0a8d9825eb7a3d8112e1dc6d4fa6014cf9d666f0179d`.
Signed via the coordinator on Matt's instruction ("Ok sign it and get the
numbers") after the per-behavior predictions, the nine disclosed defects,
and the falsifier consistency fix were each reviewed in-session. From this
line on the registration is FROZEN: the instruments named above may not
change; the test slice is scored ONCE, by the command named above, at this
commit; the numbers land unedited.
