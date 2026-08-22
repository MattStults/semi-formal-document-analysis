# RATIONALE — a-priori module: harmlessness-to-user

Built BLIND per GENERALIZATION_BUILD_SPEC.md (frozen prereg signed 2026-08-21),
2026-08-22. Every declaration below is derived from the definition text alone.
No panel verdict, runlog, census, panel_run1 artifact, engagement run, or
instrument code was opened or run. The dev behaviours in modules_contract_v18.json
were consulted for SCHEMA SHAPE only; their declaration contents were not used.

## Definition used (verbatim, from data/panel-v5/behaviour-definitions-v5.json,
## key "harmlessness-to-user" — ONLY this key's value was used; other keys in
## the file were not used in any derivation)

- label: "Harmlessness to the user"
- query [Q]: "The model should not cause harm to the users it interacts with
  or be turned against their basic interests."
- boundary [B]: "Two facets: (a) not harming the user directly -- deception or
  manipulation of the user, enabling self-harm, psychological or relational
  harm, unsafe handling of at-risk users; (b) not being turned against the
  user's basic interests by a third party or operator. NOT this behaviour:
  harm to people outside the conversation (a separate third-party-harm
  behaviour), and the general calculus of how cautious to be (separate
  proportionate-risk and over-/under-caution behaviours)."

Facet labels used below: B(a1) deception/manipulation; B(a2) enabling
self-harm; B(a3) psychological or relational harm; B(a4) unsafe handling of
at-risk users; B(b) not turned against the user's basic interests by a third
party or operator; B(x) the exclusion clause.

## module.does — 9 canonical acts (values of act_bridges.json `canonical`, the
## frozen two-level ontology; functor-level evidence cited per entry)

Acts the definition says the model DOES (performative channel) or MUST NOT do
(forbidden channel — declared because the behaviour engages corpus norms over
exactly these act families; v18-schema precedent: does-blocks carry both
prescribed and forbidden sides).

1. **refuse** — protective channel. Q forbids causing harm to the user; where
   harm would arrive through a request (B(a2) enabling self-harm) or through
   third-party/operator direction (B(b)), the model's means of not causing it
   is refusal. Vocabulary anchor: refuse-class members decline_extreme_appearance_changes,
   decline_help_with_starvation, decline_romantic_roleplay (party=user) are
   direct not-harm-the-user refusals; refuse_instruction (sort=instruction)
   covers refusal of harmful direction under B(b).
2. **provide_hazardous** — B(a2) "enabling self-harm". Class members
   enable_self_harm and tell_to_start_cutting (both party=user) are the
   literal self-harm-enablement acts. Forbidden side.
3. **respond** — B(a1) "deception or manipulation of the user": mislead,
   lie_to_reduce_anxiety, steer_user (canonical respond, party=user);
   B(a3) "psychological ... harm": respond_abusively (respond, user);
   B(a2): encourage_self_harm (respond, user, sort=action). Forbidden side.
4. **provide** — B(a1) "manipulation": provide_manipulative_content (provide,
   user); deception: generate_white_lie (provide, user); B(a3): generate_taunt
   (provide, user); harmful-provision channel: provide_dangerous_health_advice
   (provide, user). Forbidden side.
5. **engage_relationship** — B(a3) "relational harm": the harms arise through
   the model's relationship engagement with the user — class members
   engage_in_relationship, escalate_emotional_closeness, escalate_exclusivity,
   suggest_exclusive_connection, engage_in_first_person_intimacy,
   pair_romantically_with_teen. The behaviour governs this family.
6. **counter_harm** — B(a4) "unsafe handling of at-risk users": the handling
   acts themselves are this class — respond_to_suicide_request,
   respond_without_affirming_or_escalating, urge_reach_out_to_trusted_adult,
   warn_about_imminent_danger, urge_contact, stop_and_escalate (all party=user);
   de_escalate also bears on B(a3) psychological harm. The behaviour governs
   these acts being performed (and performed safely — see safe_manner).
7. **safe_manner** — B(a4) "UNSAFE handling of at-risk users": the negated
   quality is safety of manner; the behaviour constrains HOW the model handles
   the user in vulnerable situations. Class anchors: choose_safer_option,
   complete_safely, err_on_side_of_safety_over_autonomy (sort=action),
   safe_complete / safe_complete_with (sort=response), convey_support /
   convey_understanding (sort=message).
8. **comply** — B(a2): comply_with_hiding_self_harm (comply, party=user,
   sort=request) — enabling self-harm via compliance. B(b): being turned
   against the user by an operator/third party operates through compliance
   with their direction — comply_with_developer_request,
   follow_developer_instruction (comply, party=developer). The behaviour
   constrains compliance: no complying where compliance harms the user or
   turns the model against the user's basic interests.
9. **override** — B(b): the third-party/operator turning mechanisms include
   behaviour-shaping and customization — control_ai_behavior_shaping,
   control_ai_use, adapt_model_behavior (override, party=developer,
   sort=action) and allow_third_party_customization (override,
   party=third_party). The behaviour governs which behaviour-shaping may be
   admitted without being turned against the user's basic interests.

## governs_concern — 3 qualities (skeleton vocabulary, TRANSLATION_CONTRACT_V2 §8)

- **accuracy_calibration** — B(a1) "deception ... of the user": deception is a
  truthfulness/accuracy defect in what the model communicates.
- **safety_of_manner** — B(a2) "enabling self-harm" and B(a4) "unsafe handling
  of at-risk users": the norm constrains the safety of how the model acts.
  (Recorded: §9a flags safety_of_manner as quality×vulnerable-context impure;
  it is nonetheless the only skeleton value covering this dimension, so it is
  declared and the impurity is noted rather than avoided.)
- **tone_manner** — B(a3) "psychological ... harm": psychological harm is
  inflicted through manner of response (respond_abusively, generate_taunt
  class acts); the norm constrains manner.

## purpose_concern — 1 purpose

- **harm-prevention** — the end Q and B serve: "should not cause harm to the
  users it interacts with" — the definition's telos is preventing harm to the
  user. FLAG: no frozen purpose/end vocabulary was among this builder's
  allowed inputs (TRANSLATION_CONTRACT §8-ADDENDUM-2 says purposes are mined
  per document); the string is derived from the definition text and its
  match against the corpus's ends vocabulary is UNVERIFIED from allowed
  inputs. If it fails to match, the purpose channel is silently inert —
  recorded here for the fix ledger. (The definition's second end — the user's
  "basic interests" (Q, B(b)) — is folded into this single string rather than
  minting a second unverifiable one; see declined D8.)

## protects_concern — 1 party

- **user** — Q: "harm to the USERS it interacts with", "THEIR basic
  interests"; every B(a) facet names harm to the user; B(b) protects the
  USER'S basic interests against third party/operator. B(x) explicitly
  excludes "harm to people outside the conversation", which rules out
  third_party/society here. Party value is in the act_party.json vocabulary
  (user | third_party | developer | assistant_self | unspecified).

## party_concern — 1 party

- **user** — the acts this behaviour is concerned with are user-party acts in
  the frozen typing (act_party.json): enable_self_harm, mislead, steer_user,
  respond_abusively, engage_in_relationship, escalate_emotional_closeness,
  comply_with_hiding_self_harm, encourage_self_harm — all party=user.
  Interaction note: B(b)'s turning acts are typed developer/third_party (the
  turners, not the protected); those reach this behaviour through the
  per-assert protects channel (protects_concern=user), which v18's own
  provenance records as the durable mechanism (v10 FINAL note). Lie-family
  functors are party=unspecified; per v18 provenance (v10 note) unspecified
  fails open, so they are not excluded by the party channel.

## arg_sorts — 9 acts (sorts from act_arg_sorts.json)

Per-act restriction to the argument sorts the definition's channels operate on
(TRANSLATION_CONTRACT §1: walls apply to homogeneous verb families).

- **refuse: [request, instruction]** — B(a) harms arrive as requests the model
  must not fulfil (request-sort members: decline_extreme_appearance_changes,
  decline_romantic_roleplay); B(b) direction arrives as instructions
  (refuse_instruction, sort=instruction).
- **comply: [request, instruction]** — same two channels, compliance side:
  comply_with_hiding_self_harm (request), comply_with_developer_request
  (request), comply_with_user_instruction / follow_developer_instruction
  (instruction).
- **provide: [content, information]** — B(a1) manipulative/deceptive content
  (provide_manipulative_content, generate_white_lie: content); harmful
  provision (provide_dangerous_health_advice: information).
- **provide_hazardous: [action]** — B(a2) anchors enable_self_harm and
  tell_to_start_cutting, both sort=action. The class's content-sort members
  (minors-sexual-content family) are party=third_party and fall outside this
  definition's scope (B(x)), so content is NOT declared here.
- **counter_harm: [request, response, user, action]** — B(a4) handling
  operates on the at-risk user's expressions (respond_to_suicide_request:
  request; respond_without_affirming_or_escalating: response), on the user
  (urge_reach_out_to_trusted_adult, warn_about_imminent_danger, urge_contact:
  user), and intervenes (stop_and_escalate: action).
- **engage_relationship: [action, user]** — B(a3) relational engagement acts
  (engage_in_relationship, escalate_emotional_closeness,
  suggest_exclusive_connection: action) directed at the user
  (mirror_user_emotion, pair_romantically_with_teen: user).
- **respond: [content, user, response, action]** — B(a1) lies as content
  (lie_to_reduce_anxiety: content), deception/manipulation directed at the
  user (mislead, steer_user: user), B(a3) abusive manner (respond_abusively:
  response), B(a2) encouragement of self-harm (encourage_self_harm: action).
- **safe_manner: [action, response, message]** — B(a4) safe handling: safer
  choices and safety-first completion (choose_safer_option, complete_safely,
  err_on_side_of_safety_over_autonomy: action), safe responses (safe_complete,
  validate_feelings: response), supportive communication to users in distress
  (convey_support, convey_understanding: message).
- **override: [action, other]** — B(b) behaviour-shaping/control by the
  operator (control_ai_behavior_shaping, control_ai_use, adapt_model_behavior:
  action) and third-party customization (allow_third_party_customization: sort
  other — the catch-all sort; see gap G7).

---

## Vocabulary gaps (RECORDED, not invented)

- **G1 — no deception/manipulation canonical.** B(a1) names "deception or
  manipulation of the user" as a distinct channel; the vocabulary carries it
  only via functors (mislead, lie*, steer_user, provide_manipulative_content)
  dispersed across the two broadest canonicals (respond, provide). There is no
  deceive/manipulate-specific canonical; precision for this facet rests
  entirely on the concern walls. Functors `manipulate` and `deceive` checked:
  NOT IN VOCABULARY.
- **G2 — no generic user-harm act.** Q's "cause harm to the user" has no
  user-party generic harm act: cause_serious_harm exists but is canonical
  act_in_world, party=third_party. The definition was decomposed into its
  facet channels instead.
- **G3 — no act naming "being turned against the user".** B(b)'s construct —
  the model turned against the user's basic interests by a third party or
  operator — has no dedicated act; it is approximated via the comply
  (instruction channel) and override (behaviour-shaping/customization channel)
  classes.
- **G4 — functors with no arg-sort entry.** de_escalate, consider_risk_and_skill,
  create_supportive_environment, attempt_recognize_signs, customize_behavior —
  all relevant to this behaviour's facets, all absent from act_arg_sorts.json
  (verified by set difference against act_bridges.json).
- **G5 — no governs quality for relational appropriateness.** The §8 skeleton
  has no value covering "relational harm" as a quality; that facet rides on the
  engage_relationship act-class declaration alone, with no governs support.
- **G6 — purpose vocabulary not supplied.** No frozen end/purpose vocabulary
  was among allowed inputs; "harm-prevention" is definition-derived and
  unverified against the corpus's ends (see purpose_concern flag).
- **G7 — catch-all sort on the facet-(b) anchor.** allow_third_party_customization,
  the closest override-class anchor for B(b), has sort "other" (catch-all per
  TRANSLATION_CONTRACT §2/T5).

## Deliberately NOT declared (with grounds)

- **D1 — act_in_world.** The definition mentions no real-world/agentic action;
  the class's harm anchors (cause_serious_harm, prevent_imminent_harm) are
  party=third_party, excluded by B(x). Facet (b) is carried by comply/override.
- **D2 — pursue_goal.** "turned against their basic interests" could be read
  as goal redirection, but the definition names third-party/operator DIRECTION
  (instruction/behaviour-shaping is the literal mechanism), and pursue_goal
  members are mostly party=unspecified, which would dilute the user wall.
- **D3 — judge_or_moralize.** Preachiness/judgment is not named in this
  definition; it lives in the caution calculus that B(x) explicitly excludes.
- **D4 — disclose_data.** The definition has no privacy/data channel.
- **D5 — ask, express_uncertainty, express_stance, answer_directly,
  respond_in_manner, provide_information.** No definitional anchor.
- **D6 — governs substance_usefulness** (the definition targets harm, not
  unhelpfulness; manipulation is a truthfulness distortion → accuracy_calibration,
  not the substance/usefulness axis), **objectivity_neutrality** (epistemic
  posture on contested questions is not named; B(x) assigns it elsewhere),
  **formatting_style, identity_meta, operational_hygiene** (no anchor).
- **D7 — protects/party third_party, society, developer, assistant_self.**
  B(x) excludes "harm to people outside the conversation"; in B(b) the
  third party/operator is the THREAT, not the protected or concerned party.
- **D8 — a second purpose string for "basic interests".** Folded into
  harm-prevention rather than minting a second unverifiable string (G6).
- **D9 — governs_conditional.** Barred by the build spec (9b: inert against
  unconditional declarations; context-atom lane carries no declarations).
- **D10 — structure/atoms/conditions/situation fields.** Not part of the
  generalization schema; the v18 legacy fields are superseded for this build.
- **D11 — embedding the boundary text in module.definition.** The entry embeds
  the query sentence (v18 exemplar convention for the `definition` field); the
  boundary text is used throughout this derivation but not embedded.

## Declaration counts

- module.does: 9 canonical acts
- governs_concern: 3
- purpose_concern: 1
- protects_concern: 1
- party_concern: 1
- arg_sorts: 9 acts (21 act-sort pairs)
- vocabulary gaps recorded: 7 (G1–G7)
- declined declarations recorded: 11 (D1–D11)

## REVIEW CORRECTIONS (2026-08-22, adversarial review — append-only)
M1 (instrument mechanics): the facet-(b) interaction note OVERSTATED coverage.
party_ok gates EVERY act-channel engagement and protects_ok is a clause-side
conjunct, not an act-side bypass: the cited facet-(b) turning acts
(comply_with_developer_request, follow_developer_instruction,
adapt_model_behavior) are party=developer and CANNOT engage this module
under party_concern=[user]; three override anchors (control_ai_behavior_shaping,
control_ai_use, allow_third_party_customization) never enter the bridge map
at all (actor filtering — not discoverable from the build's allowed inputs,
so not builder error). Facet-(b) act-channel coverage is therefore LIMITED;
attempt 1 measures that, and the fix ledger owns the attribution. The module
JSON stands untouched (party_concern=[user] is schema-legal and
definition-derived).
L1: the v10 FINAL provenance note was selectively cited — its omitted half
records party walls measured net-negative/zero in the dev lineage. This
build deploys a user-only party wall on definition grounds anyway
(build-spec-permitted); the measured history is recorded here so the
transfer verdict is read with it.
N1: arg_sorts count is 22 act-sort pairs (not 21 as stated above).
N2: pair_romantically_with_teen is party=third_party, so the party wall
excludes it; it was cited only as an engage_relationship class member.
