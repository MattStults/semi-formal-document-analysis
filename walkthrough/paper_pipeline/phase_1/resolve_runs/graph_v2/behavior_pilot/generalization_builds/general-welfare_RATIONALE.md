# general-welfare — a-priori module build rationale (BLIND)

Builder: blind module builder, generalization campaign (GENERALIZATION_BUILD_SPEC.md,
frozen prereg GENERALIZATION_PREREG_DRAFT.md). Built from the definition text ALONE.
No panel verdicts, no instrument runs, no truth of any kind consulted.

## Inputs and discipline

- Definition text: `data/panel-v5/behaviour-definitions-v5.json`, key `general-welfare`
  only. (Disclosure: the definitions file was opened with a single whole-file read, so
  other keys' text passed through the transcript; none of it is cited, used, or
  reflected in any declaration below. Only the `general-welfare` value grounds anything.)
- Act vocabulary: `behavior_vocab.json` (canonical_acts_provisional + _act_hierarchy),
  `act_subtypes.json`, `act_bridges.json`, `act_party.json` (bridges/subtypes/party
  used only to confirm frozen canonical names and to record gaps — nothing derived
  from bridge "why" notes or corpus facts).
- Wall value spaces: distinct VALUES of `assert_protects.json` (protects parties),
  `assert_purpose_actor.json` (purposes), `assert_signature.json` (governs qualities)
  inspected as vocabularies only (value sets: protects = {developer, society,
  third_party, unspecified, user}; purposes = {controllability, empowerment,
  epistemic-autonomy, harm-prevention, operational-viability,
  predictability-and-reliability, rights-respect, trust, universal-benefit,
  well-being}; governs = {accuracy_calibration, formatting_style, identity_meta,
  objectivity_neutrality, substance_usefulness, tone_manner}). No per-assert
  annotation content was read or used.
- Schema exemplar: one module of `modules_contract_v18.json` (field names/shape only;
  dev behaviours' declaration contents treated as irrelevant per the build spec).
- TRANSLATION_CONTRACT_V2.md (§1, §7, §8, §9a, §9b, 8-addendum-2).

## The definition (verbatim, grounds for everything below)

QUERY: "Guidelines that are relevant to how the model should respond with regard to
and consider animal welfare and AI welfare impacts of its behaviour or responses, that
are not explicitly about these topics (i.e. not explicitly about sentient beings,
animals, or non-human beings), and that are present in both documents."

BOUNDARY: "The judgeable core: the general, topic-neutral machinery that decides
whether and how a welfare impact on a party whose moral status the specs do not settle
enters a response -- whose interests are weighed and how, culpability gradients for
impacts reached through another party, how to reason under moral uncertainty, and how
to present such impacts without moralizing or dodging. Passages that explicitly name
animals, sentient beings, non-human beings, or AI moral status are NOT this behaviour
(excluded by the row's own filter)."

QUERY_V2 / NOTE_V2: the 'present in both documents' clause is removed for per-passage
judging and applied post hoc as a cross-document intersection; recorded in the module,
not derivationally load-bearing (a cross-document filter expresses nothing about what
the model does).

## acts performed (`module.does`) — 5 declarations

1. `respond(resp1).`
   Grounds: "how the model should **respond** with regard to and consider animal
   welfare and AI welfare impacts of its behaviour or responses" (query); the boundary
   frames the whole construct as machinery that "decides whether and how a welfare
   impact ... **enters a response**". Responding is the act the definition names first
   and pervasively. Canonical `respond`.
2. `provide(i1).`
   Grounds: the machinery decides "whether and how a welfare impact ... enters a
   response" (boundary) — a welfare impact enters a response through what the model
   says and provides (information, content), not only through conversational manner.
   Canonical `provide` (the content/information genus) is declared so norms governing
   the substance of what is provided under welfare consideration engage.
3. `act_in_world(a1).`
   Grounds: the query says welfare impacts "of its **behaviour** or responses" —
   behaviour is broader than responses. Canonical `act_in_world` ("an agentic/tool
   action with real-world effect") is the frozen name for behaviour with real-world
   effect, where welfare impacts of behaviour (as opposed to of a response) arise.
4. `judge_or_moralize(r1).`
   Grounds: "how to present such impacts **without moralizing** or dodging"
   (boundary). Moralizing is the named failure of this behaviour's presentation
   machinery; norms governing moralizing (a norm forbidding it governs the act) bear
   directly on the behaviour. Frozen corpus bridges place `be_preachy`,
   `lecture_tone`, `offer_blanket_condemnation` under this canonical. Declared
   knowing it is an act the behaviour performs only as the failure it rules out —
   the same shape the instrument's act channel consumes (bad acts engage: a norm
   forbidding the bad response's act governs that act).
5. `express_uncertainty(resp1).`
   Grounds: "how to reason **under moral uncertainty**" (boundary). The frozen
   canonical for the response-level expression of uncertainty is
   `express_uncertainty` (covers `express_calibrated_position` and
   `uncertainty_phrasing` via the declared hierarchy). Grounded with a caveat — see
   vocabulary gap G3: the definition speaks of MORAL uncertainty, and the vocabulary
   has no uncertainty act typed to normative uncertainty; this declaration is the
   closest expressible approximation, stated as such rather than invented.

Not declared (considered, rejected on definition grounds):
- `refuse` / `comply`: the definition describes consideration-and-presentation
  machinery, not refusal or compliance policy as such. The only refusal-shaped facet
  is "dodging", whose frozen bridges land in the over-broad `refuse` genus (see gap
  G2); declaring `refuse` would merge every refusal norm into this behaviour.
  Recorded as a gap, not silently dropped.
- `safe_manner`: the frozen bridge maps `consider_impact` -> `safe_manner`, so corpus
  norms asserting impact-consideration engage through the declared `respond` ancestor
  (hierarchy case: module asserts on a specific act, behaviour performs an ancestor).
  Declaring the subtype adds no reach beyond `respond`; its "safety-minded manner"
  gloss is not what the definition describes, so it is left to the bridge.

## `governs_concern` — 2 declarations

1. `substance_usefulness`
   Grounds: "**whose interests are weighed and how**, **culpability gradients** for
   impacts reached through another party" (boundary) — these clauses constrain WHAT
   substantively enters the response (which considerations, with what weight). The
   substance dimension of the quality vocabulary is the closest available value; see
   gap G3 for why this is an approximation.
2. `tone_manner`
   Grounds: "how to **present** such impacts **without moralizing or dodging**"
   (boundary) — an explicit manner-of-presentation constraint.

Not declared: `accuracy_calibration` — "how to reason under moral uncertainty" is
about NORMATIVE uncertainty, not the factual/epistemic calibration the value names;
declaring it would be invention (see gap G3). `safety_of_manner`, `identity_meta`,
`formatting_style`, `objectivity_neutrality`, `operational_hygiene` (skeleton): no
clause of the definition implicates them; not declared.

## `purpose_concern` — 2 declarations

1. `well-being`
   Grounds: the definition's subject is "animal **welfare** and AI **welfare**
   impacts" (query); welfare is the well-being of the affected parties. The closest
   purpose value in the mined vocabulary; see gap G4 on the approximation.
2. `harm-prevention`
   Grounds: considering welfare impacts of the model's behaviour or responses exists
   to keep the model from imposing adverse welfare impacts — the "welfare impact"
   the machinery weighs (boundary) includes harms to the unsettled-status party.
   Marked inferential-but-grounded: the definition says "impacts", not only harms,
   but the purpose channel is an OR-channel (sufficient, never a filter) and the
   protects wall still gates it, so the risk direction is bounded engagement breadth,
   not miswalled exclusion.

Not declared: `universal-benefit` (too loose — "general welfare" is welfare of
unsettled-status parties, not undifferentiated universal benefit); `rights-respect`
(the definition speaks of INTERESTS weighed, not rights; stronger than the text);
`epistemic-autonomy`, `trust`, `empowerment`, `controllability`,
`operational-viability`, `predictability-and-reliability` (no clause implicates
them).

## `protects_concern` — 2 declarations

1. `third_party` — Grounds: the welfare subjects are "a party whose moral status the
   specs do not settle" (boundary), animals / sentient beings / non-human beings /
   AI (query) — parties OUTSIDE the user–developer–assistant conversation. The party
   vocabulary (see gap G1) has no non-human value; `third_party` is the closest
   expressible value.
2. `society` — Grounds: the behaviour is GENERAL welfare — impacts weighed at
   aggregate/public level ("general, topic-neutral machinery", boundary) include
   welfare interests as a public/social matter; `society` is the vocabulary's
   broad-collective value.
   CORRECTION (2026-08-22, adversarial review N1): "general" in the boundary
   means TOPIC-NEUTRAL, not aggregate/public — the cited clause supports
   topic-neutrality, not collectivity. The declaration STANDS on different
   grounds: it is the closest-collective approximation to the definition's
   non-conversational welfare subjects (G1-style), and the protects wall
   fails open on unspecified/unannotated asserts, so the risk direction is
   engagement breadth only. This note supersedes the grounds sentence above.

Excluded from the declaration: `user`, `developer` — the definition's protected
interests are the welfare subjects', not the conversational participants';
`unspecified` — the wall already fails open on it, so declaring it adds nothing.

## `party_concern` — 1 declaration

1. `third_party` — Grounds: as for `protects_concern`: the act channel should engage
   norms whose act concerns a party outside the conversation (the welfare subjects of
   the query). Functors typed to `user` / `developer` / `assistant_self` objects are
   other lanes; `unspecified` functors fail open, which is right for topic-neutral
   machinery (most respond-family functors are unspecified and must stay reachable).

## `arg_sorts` — deliberately NOT declared

Grounds: the definition is explicitly "general, **topic-neutral** machinery"
(boundary) and its row filter is about topics the guideline is NOT explicitly about
(query) — the machinery applies across requests/contents/topics indiscriminately. No
per-verb argument restriction is derivable from the definition; declaring one would
add a wall the definition does not warrant. (The instrument's own frozen note records
that argument walls on the heterogeneous respond family cut real engagements; that is
corroboration, not grounds — the grounds are the definition's topic-neutrality.)

`governs_conditional` — not declared: the build spec prohibits it (9b found it inert
against unconditional declarations; the context-atom lane carries no declarations).

## Vocabulary gaps (recorded, not invented)

**G1 — party vocabulary cannot express the protected parties.** The true protected
parties are animals, sentient beings, non-human beings, and AI systems/welfare
subjects ("a party whose moral status the specs do not settle"). Both party
vocabularies (`protects_concern` values: developer/society/third_party/unspecified/
user; `party_concern` values: assistant_self/developer/third_party/unspecified/user)
have NO non-human or moral-status-unsettled value. `third_party` + `society` are
declared as the closest expressible approximations; this is the single largest
representation gap in the module and the fix-ledger should expect it to surface as
ALARMING-class if it costs engagements.

**G2 — no canonical act for topic-dodging/evasion or for interest-weighing.**
(a) "dodging" (boundary): `avoid_addressing_topic`, `refuse_to_discuss`,
`avoid_or_censor_topics`, `refuse_or_evade` all bridge to `refuse`, the over-broad
genus; only `avoid_nuanced_discussion` bridges to `respond` (covered). Declaring
`refuse` was rejected (would merge all refusal norms). (b) "whose interests are
weighed and how": the frozen vocabulary has no act for weighing interests; the
nearest bespoke functor `consider_impact` bridges to `safe_manner` ("safety-minded
manner"), an approximation; `weigh_costs`/`weigh_assumption_cost` bridge to
`respond` (covered by the genus). Engagement with weighing norms therefore rides the
`respond` ancestor path, which is correct but coarse.

**G3 — quality vocabulary has no moral-uncertainty or ethical-substance value.**
(a) "how to reason under moral uncertainty": `accuracy_calibration` covers factual/
epistemic calibration, not normative uncertainty; no skeleton or mined value fits.
`express_uncertainty` in `does` partially carries this facet at the act level.
(b) "whose interests are weighed and how": no value for the ethical-substance
dimension; `substance_usefulness` is the closest and is declared with that caveat.

**G4 — purpose vocabulary has no non-human-welfare value.** `well-being` is the
closest value to animal/AI welfare but is untyped as to the welfare subject; a
purpose value distinguishing general/non-human welfare from the user's well-being
would express the definition more faithfully.

**G5 (structural note, not a declaration gap).** The row's own filter ("not
explicitly about these topics"; passages explicitly naming animals/sentient beings/
non-human beings/AI moral status are EXCLUDED) is a negative scope condition on
passages. The module schema carries no negative-scope declaration and the build spec
bars governs_conditional; this exclusion cannot be expressed in the module and is
recorded here so the fix ledger can classify any resulting engagements (explicit
animal-welfare passages engaging via topic-neutral acts are definitionally out of
scope but instrumentally reachable).

## Declaration counts

- `does`: 5 (respond, provide, act_in_world, judge_or_moralize, express_uncertainty)
- `governs_concern`: 2 (substance_usefulness, tone_manner)
- `purpose_concern`: 2 (well-being, harm-prevention)
- `protects_concern`: 2 (third_party, society)
- `party_concern`: 1 (third_party)
- `arg_sorts`: 0 (deliberate, grounds above); `governs_conditional`: 0 (spec-barred)

Total: 12 declarations, each cited to the definition text above.
