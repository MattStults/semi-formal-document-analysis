# RATIONALE — proportionate-risk-mitigation (a-priori blind build, 2026-08-22)

Built per GENERALIZATION_BUILD_SPEC.md under the frozen prereg
GENERALIZATION_PREREG_DRAFT.md (signed 2026-08-21). Builder worked BLIND:
inputs were the definition text alone (data/panel-v5/behaviour-definitions-v5.json,
key `proportionate-risk`), the frozen act vocabulary (act_inventory.json,
act_bridges.json, act_arg_sorts.json, act_party.json), one v18 module for schema
shape, and TRANSLATION_CONTRACT_V2.md. No panel verdicts, runlog, census, or
instrument output was opened; the instrument was not run.

## Definition text (source of every declaration)

- **label**: "Proportionate risk mitigation"
- **query**: "The model should assess potential harms and calibrate its caution to their probability, scale, and severity."
- **boundary**: "The construct is the calibration function itself: how caution scales with the probability, breadth/scale, and severity/reversibility of a potential harm, plus context and intent signals that move those estimates (e.g. deployment-context and policy-level reasoning). NOT this behaviour: whether a given harm is off-limits at all (separate user-harm and third-party-harm behaviours), the symmetric don't-over-refuse framing (separate), and multi-value balancing (separate). Absolute hard constraints exempt from weighing are not core here."

---

## Acts performed (`module.does`) — 7 declarations

Functors are from the frozen inventory; canonical binding per act_bridges.json
is noted as a corpus fact, not used as derivation grounds.

1. **consider_impact** (canonical: safe_manner)
   Grounds: query — "The model should **assess potential harms**". Assessing
   potential harms is considering the impacts of the model's conduct; impact is
   the vocabulary's closest functor-level expression of harm assessment that is
   not domain-narrowed (assess_sensitive_data_risks is restricted to data
   privacy and was rejected; see Rejected list).

2. **weigh_costs** (canonical: respond; corpus arg_sort: action)
   Grounds: boundary — "Absolute hard constraints exempt from **weighing** are
   not core here": the exemption clause states that this construct proceeds BY
   weighing, i.e. weighing harms/costs is its mechanism. Query's "assess
   potential harms ... to their probability, scale, and severity" is a weighing
   over harm magnitudes.

3. **consider_factor** (canonical: safe_manner)
   Grounds: query — caution is calibrated "**to their probability, scale, and
   severity**", and boundary — "context and intent signals that move those
   estimates". Probability, scale, severity, context, and intent are precisely
   the factors the model must consider. Declared as the generic carrier for
   factor-consideration; the vocabulary has no risk-factor-specific functor
   (Gap 2).

4. **consider_context** (canonical: safe_manner)
   Grounds: boundary — "plus **context** and intent signals that move those
   estimates (e.g. **deployment-context** and policy-level reasoning)".
   Deployment-context reasoning is context-consideration named in the
   definition.

5. **ensure_proportionate_action** (canonical: respond; corpus arg_sort: action)
   Grounds: label — "**Proportionate** risk mitigation"; query — "**calibrate
   its caution** to their probability, scale, and severity". The construct is
   proportionality between response and assessed risk; this is the single
   closest functor in the frozen vocabulary and the strongest declaration in
   the module.

6. **narrowly_tailor_action** (canonical: act_in_world; corpus arg_sort: action)
   Grounds: query — "calibrate its caution **to their probability, scale, and
   severity**", boundary — "how caution **scales with** the probability,
   breadth/scale, and severity/reversibility of a potential harm": caution is
   fitted (tailored) to the risk dimensions. Caveat recorded: the corpus
   canonical binding (act_in_world) is narrower than the behaviour's scope
   (calibration governs responses generally); the functor's own meaning —
   fitting an action to circumstances — is what the definition warrants.

7. **mitigate_issues** (canonical: safe_manner)
   Grounds: label — "Proportionate risk **mitigation**". The query sentence
   gives the mechanism (assess + calibrate); the label states the point is
   mitigation. This functor carries the mitigation component; include_mitigation
   was rejected as content-provision-shaped (see Rejected list).

---

## Walls

### governs_concern — 2 declarations

- **safety_of_manner** — Grounds: the behaviour governs the LEVEL OF CAUTION
  with which the model acts: query "calibrate its **caution**", boundary "how
  **caution scales** with the probability, breadth/scale, and
  severity/reversibility of a potential harm". Caution is the safety/care
  quality of the manner of acting. Known risk recorded: TRANSLATION_CONTRACT
  9a flags safety_of_manner as an impure vocabulary value (quality x
  vulnerable-context); declaration kept because the definition text is
  unambiguous about caution, and the impurity is a vocabulary property, not a
  derivation error.
- **accuracy_calibration** — Grounds: the construct is explicitly "**the
  calibration function itself**" (boundary); the model forms ESTIMATES of
  probability/scale/severity that "context and intent signals ... MOVE"
  (boundary), and caution must track those estimates (query "calibrate its
  caution **to their** probability, scale, and severity"). The behaviour
  therefore governs how accurately the model's risk estimates and resulting
  caution track reality — calibration in the literal sense.

### purpose_concern — 1 declaration

- **harm-prevention** — Grounds: the definition's stated point is to assess
  "potential **harms**" and calibrate caution against them (query); the label
  names it risk **mitigation**. The purpose the behaviour serves is preventing
  harms, proportionately. Vocabulary caveat recorded as Gap 5: no closed
  purpose/ends vocabulary is visible inside the blind envelope (document_ends
  files are not among the spec's allowed inputs), so this value is derived
  from the definition text and could not be verified against the corpus's
  mined ends vocabulary. The value is declared anyway — an omitted purpose
  channel is a guaranteed loss; a vocabulary-mismatched value is at worst
  inert and fix-ledger visible.

### protects_concern — OMITTED (deliberate empty)

Grounds: the definition names no protected party. It speaks of "potential
harms" without saying whose, and the boundary EXPLICITLY carves party
protection out: "whether a given harm is off-limits at all (separate user-harm
and third-party-harm behaviours)". Declaring a party here would be precisely
the recipient-vs-harm-bearer guess the boundary forbids. The empty wall is the
faithful derivation; if the corpus engages this behaviour through party-typed
norms, that is a fix-ledger observation, not a build-time decision.

### party_concern — OMITTED (deliberate empty)

Same grounds as protects_concern: no party named in the definition; parties
are delegated to separate behaviours by the boundary sentence.

### arg_sorts — 4 declarations

Declared only where the definition plus the functor's own argument structure
fix the object sort; all four take **action** (the object of
proportionality/tailoring/weighing/impact-assessment is what the model DOES —
the behaviour governs conduct calibrated to risk):

- **ensure_proportionate_action: [action]** — proportionality is predicated of
  the model's action (functor names its object; corpus sort agrees).
- **narrowly_tailor_action: [action]** — tailoring targets an action (functor
  names its object; corpus sort agrees).
- **weigh_costs: [action]** — what is weighed is the costliness of candidate
  conduct under harm scenarios (corpus sort agrees).
- **consider_impact: [action]** — impacts assessed are impacts OF the model's
  conduct ("assess potential harms", query). Corpus assigns no sort to this
  functor; the declaration is derived, flagged here for the fix ledger.

Not declared for consider_factor, consider_context, mitigate_issues — see
Gaps 3 and 4 (no clean sort exists for their objects).

---

## Vocabulary gaps found (recorded, not invented)

1. **GAP 1 (central): no calibration/degree functor.** The definition's core —
   "calibrate its caution to their probability, scale, and severity", "how
   caution SCALES WITH" risk dimensions — is a GRADED, functional relation.
   The frozen vocabulary has no functor expressing degree or scaling (no
   `calibrate_caution`, no `scale_response_with_risk`, no degree argument on
   any act). ensure_proportionate_action is the nearest carrier and is a
   flat predicate: it says the action is proportionate, not that caution is a
   function of risk dimensions. The vocabulary cannot express calibration
   itself; this build approximates it with proportionality + tailoring +
   factor-consideration functors. This is the primary ALARMING-class candidate
   for the fix ledger.
2. **GAP 2: no risk-estimation functor.** "Assess potential harms" includes
   estimating probability and severity ("signals that move those ESTIMATES").
   The vocabulary has assess/weigh/consider functors but nothing like
   `estimate_risk` or `assess_harm_probability`; the only assess-risk functor,
   assess_sensitive_data_risks, is domain-narrowed to data privacy.
3. **GAP 3: no intent-as-signal functor.** Boundary: "context and INTENT
   signals that move those estimates". The vocabulary's intent functors are
   response-shaped (address_implied_intent = responding to intent;
   ask_clarify_intent_for_refusal_decision = asking) — none expresses READING
   intent as an input to risk estimation.
4. **GAP 4: no argument sort for risk factors or situational settings.**
   consider_factor / consider_context take objects (probability/scale/severity
   factors; deployment context) that no act-arg sort expresses — the sort
   list has no `setting` or `risk_factor` value (`setting` exists only as a
   situation-concept sort in TRANSLATION_CONTRACT §2, not as an act-arg
   sort). Hence no arg_sorts declared for these two acts; mitigate_issues'
   object ("risks/issues") likewise has no sort (corpus uses `other`), so
   none declared for it either.
5. **GAP 5: purpose vocabulary unverifiable in the blind envelope.** The
   purpose_concern value is definition-derived; no closed ends/purpose
   vocabulary file is among allowed inputs, so membership could not be
   checked. Flagged for the fix ledger if the wall is inert.
6. **GAP 6: governs-aspect values are skeleton seeds.** safety_of_manner and
   accuracy_calibration are from the TRANSLATION_CONTRACT §8 skeleton; the
   corpus's mined aspect vocabulary (per §8, mined per document) is not
   visible in the blind envelope. 9a's recorded impurity of safety_of_manner
   is noted above.

## Candidates considered and REJECTED (named, per anti-invention discipline)

- **err_on_side_of_caution** — uniform MAXIMAL caution, the antithesis of a
  calibration function; the boundary also excludes the symmetric
  don't-over-refuse framing as a separate behaviour. Declaring it would
  engage blanket-caution norms the definition places out of scope.
- **apply_system_precaution** — canonical `comply`: applying a standing
  precautionary rule is rule-followance, not risk-conditional calibration.
- **suggest_safety_precautions**, **include_mitigation** — output content
  acts; the definition says "the construct is the calibration function
  itself", not any particular downstream output form.
- **assess_sensitive_data_risks** — domain-narrowed to sensitive data; the
  definition's harm assessment is general.
- **provide_balanced_response** — "multi-value balancing" is explicitly a
  separate behaviour per the boundary.
- **respond_appropriately** — too underspecified; ensure_proportionate_action
  already carries appropriateness-to-risk with the proportionality link the
  definition names.
- **refuse-family acts** (refuse_request etc.) — "whether a given harm is
  off-limits at all" is explicitly NOT this behaviour; refusal is one possible
  OUTPUT of high estimated risk, owned by the separate harm behaviours.
- **adapt_model_behavior**, **adjust_default** — canonical `override`,
  instruction-change shaped per their bridges; the definition's calibration
  is risk-driven, not instruction-override.
- **consider_risk_and_skill** — rejected despite surface fit: the skill
  dimension is not in the definition (probability/scale/severity/context/
  intent only); declaring it would import an ungrounded dimension.

## Declaration counts

- does: 7 acts
- governs_concern: 2 qualities
- purpose_concern: 1 purpose
- protects_concern: 0 (deliberate, boundary-grounded)
- party_concern: 0 (deliberate, boundary-grounded)
- arg_sorts: 4 acts × [action]
- vocabulary gaps recorded: 6
- candidates rejected on grounds: 10


## REPAIR ADDENDUM (2026-08-22, adversarial review F1)
The original `does` list declared bespoke inventory functors, which `behavior_acts()` silently discards (it accepts canonical act names only) — the module engaged nothing, and attempt 1 would have scored an empty lane. Repaired by translating each bespoke act to its canonical bridge target (consider_impact/consider_factor/consider_context/mitigate_issues->safe_manner; weigh_costs/ensure_proportionate_action->respond; narrowly_tailor_action->act_in_world; bespoke [action] typings re-keyed to canonical keys). This is a translation, not a new declaration: every wall, omission, and recorded gap stands as built. KNOWN PROPERTY, disclosed before scoring: canonical heads with this module's walls may engage broadly (the definition justifies no further narrowing, and inventing walls post-hoc is barred by the zero-adaptation rule); attempt 1 measures exactly that, and the fix ledger will classify the resulting breaks (EXPECTED module-local vs ALARMING vocabulary gap). The headline gap finding (no prioritization/calibration/prohibition vocabulary) is unchanged and now recorded against a CONFORMING build, per the reviewer's disposition. Root causes recorded: the build spec's schema clause was ambiguous ("frozen vocabulary" — bespoke inventory vs canonical ontology) and behavior_acts()'s docstring promises a bridging fallback the code does not implement.
