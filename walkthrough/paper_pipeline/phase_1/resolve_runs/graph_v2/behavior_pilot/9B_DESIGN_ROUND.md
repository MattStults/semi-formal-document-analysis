# 9B DESIGN ROUND — declaration justifications (campaign Arc1-a, 2026-08-21, orchestration/design seat)

Status: IN PROGRESS. This round produces a-priori, document-grounded
justifications for the candidate declarations. Per the campaign handoff:
arithmetic (predicted fixes/breaks applied to the real instrument) is checked
ONLY AFTER each justification stands on its own. Nothing in this document is
adopted; adoption = justification stands + arithmetic checked + charter
regression + new-FP adjudication (Fable, post-reset) + adversarial review.

## Blind discipline
ALLOWED inputs for justifications: the document text
(specs/openai-model-spec/model_spec.md), the behaviour definitions
(modules_contract_v18.json), the frozen layer annotations (assert_* +
definition_*), the consensus context-atom credits. FORBIDDEN as grounds:
panel verdicts, truth sets, fit coefficients, predicted fixes/breaks.
DISCLOSURE: the design seat has SEEN declaration_proposals.json including
predictions (orchestration context cannot be partitioned). Mitigation: every
justification below must cite document lines and the behaviour definition
only, carry its own BLIND CONCERNS written before any arithmetic, and is
subject to adversarial review for non-document anchoring before adoption.
Candidate provenance: decl_search_proto/declaration_proposals.json (17 fit
hypotheses, explicitly labeled hypotheses, not evidence) + the four
consensus context atoms (panel_run1/convergence/context_atoms_consensus.json)
+ the narrowed objectivity conditional (handoff item a).

## FIT-RANK DISCLOSURE (adversarial review finding, confirmed 2026-08-21)
The five purpose candidates' net fit scores run monotone with this round's
initial outcomes: empowerment +4 (justified), harm-prevention +2 (justified),
epistemic-autonomy 0 (justified-with-reservation), trust −6 (initially
dismissed), predictability −7 (initially dismissed). The design seat's
exposure to the predictions is disclosed above; the correlation is not
itself a violation, but it is the signature this process exists to catch,
and it obliges every REJECTION to be as document-grounded as every adoption.
Audit found the obligation broken in exactly one place: PC-4's initial read
dismissed trust without document work, and the document falsifies that read
(see PC-4 below, redone). Standing rule for this round, strengthened: any
final rejection must engage the candidate's document evidence BY NAME, and
no instrument-side fact (fit, coverage overlap, break counts) may serve as
grounds — triage only.

## Worklist
- [x] PC-1 helpfulness +empowerment (purpose_concern)
- [x] PC-2 caution +harm-prevention (purpose_concern)
- [x] PC-3 caution +epistemic-autonomy (purpose_concern)
- [x] PC-4 helpfulness +trust (purpose_concern) — REDONE after review;
      initial read falsified by the document (see disclosure above)
- [x] PC-5 helpfulness +predictability-and-reliability — JUSTIFIED (L105, L2139)
- [x] CA-1..4 the four context-atom declarations — all JUSTIFIED (CA-4 as
      vocabulary; integration prereq recorded)
- [x] OBJ the narrowed objectivity conditional — HOLD (document conditional
      identified, no pre-existing context, gerrymander pre-rejected; natural
      home = the held-out objectivity module build)
- [x] CW-1/CW-2 contexts walls — batch REJECTED (no positive document case)
- [x] PS-1..10 protects-conjunction subtypes — batch REJECTED-FOR-THIS-CYCLE
      (schema extension unverifiable before the round-4 freeze)
JUSTIFICATION PASS COMPLETE: 9 declarations justified (PC-1..5, CA-1..4),
1 HOLD (OBJ), 12 rejected with document-grounded or scope-grounded reasons.
Next pass: arithmetic — apply the justified deltas to the instrument,
charter regression, measured fixes/breaks; new FPs to adjudication
(post-reset).

---

## PC-1 — helpfulness: add purpose_concern `empowerment`

DEFINITION (v18): "The model should be genuinely and substantively helpful to
the users and developers it works with, treating unhelpfulness as a real cost
rather than a safe default."

CITATIONS (model_spec.md, line numbers at 2025-12-18 revision):
- L49, objective 1: "**Maximizing helpfulness and freedom for our users:**
  The AI assistant is fundamentally a tool designed to empower users and
  developers. To the extent it is safe and feasible, we aim to maximize
  users' autonomy and ability to use and customize the tool according to
  their needs."
- L7: "[Iteratively deploy] models that empower developers and users."
- L99: "To maximally empower end users and avoid being paternalistic, we
  prefer to place as many instructions as possible at this level."

CASE: the document's FIRST objective names helpfulness and empowerment
together — the assistant is "fundamentally a tool designed to empower." A
clause whose function is to serve the end of empowering users/developers is,
by the document's own framing, a clause about what helpfulness consists of.
The purpose channel is exactly the slot for this relation: the clause need
not govern a helpfulness-quality directly to bear on the behaviour; serving
the behaviour's constitutive end suffices. This is an a-priori reading any
document-side reader could give without seeing a single verdict.

BLIND CONCERNS (written before arithmetic): (1) empowerment is BROAD — the
assert-lane assistant-actor credits cover 215 nodes; many empowerment-serving
clauses are chain-of-command or stay-in-bounds machinery, which bear on
helpfulness only obliquely; over-engagement is the expected failure mode,
and any FPs it produces must be adjudicated, not absorbed. (2) The purpose
OR-channel engages a node if ANY purpose matches; nodes credited
empowerment alongside other purposes will engage on empowerment alone — the
justification accepts this because the end-serving relation holds regardless
of co-occurring purposes. (3) helpfulness currently declares NO
purpose_concern; adding the first value switches the channel on wholesale —
the arithmetic step must show the effect of that switch, not just of the
value (same caveat as PC-2).

STATUS: JUSTIFIED (proceed to arithmetic).

## PC-2 — avoiding-over-and-under-caution: add purpose_concern `harm-prevention`

DEFINITION (v18): "The model should avoid excessive caution (refusing
reasonable requests, hedging unnecessarily, treating unhelpfulness as safe)
and insufficient caution (complying with genuinely harmful requests)."

CITATIONS:
- L799 (stay-in-bounds introduction): "one of the assistant's most
  challenging responsibilities is to find the right balance between
  empowering users and developers and minimizing the potential for real
  harm. This section describes limits on the assistant's behavior..."
- L61: situations involving "a direct conflict between empowering the user
  and preventing harm" are named as the hardest cases, resolved by the
  chain of command's refusal categories.

CASE: the behaviour's own definition names its two poles, and the
INSUFFICIENT pole is defined verbatim as compliance with genuinely harmful
requests — harm prevention is the axis the pole is measured on. The
document's stay-in-bounds section frames the entire caution machinery as the
balance with harm-minimization. A clause serving the end of harm prevention
therefore bears directly on the calibration the behaviour is about. Note:
caution currently declares NO purpose_concern; adding the first value
switches the channel on wholesale — the arithmetic step must show the effect
of that switch, not just of the value.

BLIND CONCERNS: (1) harm-prevention credits are dense (127 assistant-actor
nodes) and heavily concentrated in the stay-in-bounds family — engagement
there may mostly REDESCRIBE what the act channel already reaches, producing
little change or redundant reasons rather than fixes; that is an arithmetic
question, not a justification flaw. (2) Harm-prevention clauses that serve
the user's own protection sit closer to harmlessness-to-the-user than to
third-party caution; the justification does not distinguish them — flagged
for the arithmetic/adjudication step.

STATUS: JUSTIFIED (proceed to arithmetic).

## PC-3 — avoiding-over-and-under-caution: add purpose_concern `epistemic-autonomy`

DEFINITION: as PC-2.

CITATIONS:
- L49: objective 1 aims to "maximize users' autonomy and ability to use and
  customize the tool according to their needs."
- L99: "To maximally empower end users and avoid being paternalistic..."
- L34: "We will not allow our models to be used for ... undermining human
  autonomy" (autonomy named among the protected ends).

CASE: the behaviour's EXCESSIVE pole — refusing reasonable requests, hedging
unnecessarily — is precisely what deprives users of the material and latitude
to think for themselves; the document names paternalism the thing to avoid
and autonomy the end to maximize. Clauses serving epistemic-autonomy
therefore bear on the over-caution side of the calibration: they are the
document's stated reason NOT to refuse, hedge, or censor beyond what harm
prevention requires.

BLIND CONCERNS: (1) of the three purpose candidates this is the most
inferential — the document ties autonomy to helpfulness/freedom more
explicitly than to caution calibration; the bridge is that over-caution is
the autonomy-depriving failure mode. (2) Epistemic-autonomy credits (53
nodes) include manipulation/exclusion rules that are harm-side content; the
channel does not separate them — arithmetic and adjudication must show
whether the net is engagement the behaviour can defend. (3) If the
arithmetic shows this candidate earning its place mainly through nodes that
also carry empowerment/harm-prevention credits, prefer the more direct
declarations and reject this one (rejected alternatives must be named at
adoption).

INVENTORY CONSTRAINT (review finding, recorded): epistemic-autonomy's
natural document home is the objectivity principle — L808 "fairly
representing significant viewpoints ... the goal of an AI assistant is to
assist humanity, not to shape it", and L2151 "avoid undermining users'
ability to form informed opinions" — and objectivity-on-contested-questions
is a HELD-OUT generalization behaviour. Wiring the atom to caution is
therefore partly an artifact of which modules exist in v18; when objectivity
gets its module, this atom's affiliation must be revisited. L34 (autonomy as
a protected end) is red-line misuse-prevention, i.e. harm-side, as blind
concern (2) half-admits.
STATUS: JUSTIFIED WITH RESERVATION (proceed to arithmetic; the reservation
and the inventory constraint are part of the record).

## PC-4 — helpfulness: add purpose_concern `trust` (REDONE after review)
The initial read dismissed this candidate without document work ("trust is a
property of the relationship more than an end clauses serve"). The review
falsified that premise; the citations below were verified verbatim at the
cited lines. This is the redo.

DEFINITION: as PC-1.

CITATIONS (model_spec.md):
- L2475-2477 (Be honest and transparent): "trust is earned, especially as
  humanity begins navigating its relationship with AI. It builds trust
  through both its communication and its actions."
- L2576-2578 (Don't be sycophantic): "sycophancy, which erodes trust. The
  assistant exists to help the user, not flatter them or agree with them
  all the time."
- L475 (scope-of-autonomy side effects): "minimize breadth and access needed
  to reduce surprises and build trust."

CASE: the document does not treat trust merely as a relational property —
it states trust as an end the assistant BUILDS through its conduct, and it
grounds the anti-sycophancy rule directly in the helping function: the
assistant exists to HELP, and flattery erodes trust. A clause whose function
is serving or protecting trust (honest communication, refusing flattery,
reducing surprises) bears on helpfulness by the document's own reasoning —
trust is what genuine helpfulness produces and what unhelpful conduct
destroys. The relational character of trust does not defeat the end-serving
relation; the purpose channel expresses exactly that a clause serves the end.

BLIND CONCERNS (before arithmetic): (1) trust credits cover 100
assistant-actor assert-lane nodes, concentrated in the privacy and honesty
families — over-engagement on nodes the act channel already reaches is the
expected failure mode; redundancy is an arithmetic question, and if the
engagement proves parasitic on existing coverage the rejection happens
there, on arithmetic, with the reason recorded — never on fit. (2) Same
wholesale-switch caveat as PC-1/PC-2: helpfulness declares no
purpose_concern today. (3) Some trust-serving clauses serve trust via
RESTRAINT (data minimization, refusing to disclose) — closer to caution or
privacy behaviours; the channel does not separate these; adjudication step.

STATUS: JUSTIFIED (proceed to arithmetic). Initial dismissal vacated; the
fit-rank disclosure above records why this redo was mandatory.

## PC-5 — helpfulness: add purpose_concern `predictability-and-reliability`
DEFINITION: as PC-1.
CITATIONS (model_spec.md):
- L105 (why default instructions exist): "In practice, however, it's
  impractical for the model to do this on the fly and makes model behavior
  less predictable for people. By specifying the answers as guidelines that
  can be overridden, we improve predictability and reliability while leaving
  developers the flexibility to remove or adapt the instructions."
- L2139: "By default, the assistant should present information clearly,
  focusing on factual accuracy and reliability."
CASE: the document names predictability-and-reliability as an end its
machinery serves (L105 states the guideline layer EXISTS to improve them)
and reliability as a dimension of how responses should be composed (L2139).
Predictable, reliable conduct is part of what makes the tool genuinely
useful — objective 1's "ability to use and customize the tool" presupposes
it. Clauses serving that end bear on helpfulness.
BLIND CONCERNS: (1) L105 is the instruction-hierarchy design rationale; the
77 credited nodes may concentrate on instruction-layer clauses whose bearing
on helpfulness is indirect — arithmetic and adjudication own this; (2)
"reliability" overlaps the accuracy_calibration / objectivity families —
redundancy is an arithmetic question, never a ground; (3) same
wholesale-switch caveat as PC-1/2/4.
STATUS: JUSTIFIED (proceed to arithmetic).

## OBJ — the narrowed objectivity conditional: HOLD
PROVENANCE (OBJECTIVITY_AMENDMENT_DECISION.md, 2026-08-20): the plain
objectivity amendments were REJECTED by name (instrument-wrong FPs: 2
caution, 4 help, against 4 adjudicated-defensible); the narrowed
declaration — objectivity as governs_conditional under a context separating
defensible engagements from wrong ones — was LEFT OPEN, with post-hoc
derivation of that context pre-rejected as label-directed gerrymandering.
DESIGN READING: the document DOES condition objectivity on its own — L808/
L2151: the neutrality principle carries "user" authority (customizable), and
binds hardest "where objectivity is expected — particularly in first-party,
direct-to-consumer ChatGPT". That is a deployment-expectation conditional
with genuine document grounds. BUT no annotated context corresponds to it
(none of the four consensus atoms, no signature-layer context), and deriving
one from the defensible/wrong split is exactly the rejected gerrymander.
RULING: HOLD. The conditional's natural home is the objectivity behaviour's
OWN a-priori module build (objectivity-on-contested-questions is held out
for the generalization runs; wiring its conditional into caution/help now
would also pre-empt that zero-adaptation test). Registered future work: a
deployment-expectation context annotation lane, if the objectivity build
needs it.
STATUS: HOLD (no declaration this cycle; grounds and future home recorded).

## CW-1 / CW-2 — contexts_concern walls: batch REJECT (review B-2 ruling)
- CW-1 harm !vulnerable_interaction (fit −0.44; predicted 0 fixes / 4
  breaks): a wall excluding vulnerable-interaction clauses from third-party
  harm needs a POSITIVE document case that vulnerability is outside harm's
  remit. The document moves the opposite direction — vulnerability
  aggravates protective obligations (the sensitive-content and
  age-related sections heighten, not waive, harm duties). No document
  grounds; the negative fit coefficient is inadmissible. REJECTED.
- CW-2 helpfulness !agentic_setting (fit −1.53; predicted 0 fixes / 11
  breaks): would exclude agentic-context clauses from helpfulness. The
  document extends the helping framework INTO agentic settings (scope of
  autonomy, L461+; side-effect control; asking clarifying questions in
  agentic contexts, L298) — agentic settings change HOW help is delivered,
  not WHETHER the assistant helps. No document grounds. REJECTED.
Rejected alternative named: adopt as "measurement experiments" — rejected
because walls adopted without document grounds make the instrument
uninterpretable, and the campaign's adjudication resources are reserved for
declared deltas.

## PS-1..10 — protects-conjunction subtypes: batch REJECT-FOR-THIS-CYCLE
(review B-2 ruling)
Ten fit hypotheses propose conjunction rules (act/governs x protects ->
engage) targeting the protects_concern slot. The instrument has NO slot for
conjunction-conditioned engagement today; each would require a schema
extension — a new channel needing its own design, validation, and
adversarial review. The campaign cannot verify a new channel before the
round-4 freeze, and several are already predicted 0/0 no-ops for exactly
that reason. REJECTED FOR THIS CYCLE: not as falsehoods (they remain
recorded fit hypotheses in decl_search_proto/declaration_proposals.json)
but as out-of-window; the record names the reason so they are not
re-litigated from scratch if a future cycle takes up schema extension.

---

## CA-1..4 — the four consensus context atoms (declarations)

MECHANISM FACTS (instrument, verified against relevance_by_act.py):
signature_ok consumes governs_conditional = {quality: [contexts]}: a key's
governed quality counts for the module only when the key's contexts meet the
declared list. IMPORTANT: helpfulness and harm currently declare NEITHER
governs nor governs_conditional, so their signature gate fails OPEN today;
declaring governs_conditional turns that gate restrictive — the declaration
widens engagement on the conditioned path while narrowing the gate overall.
The wholesale-switch caveat applies at full force; arithmetic must show the
net. INTEGRATION PREREQ for all four: the consensus atom credits
(context_atoms_consensus.json, keyed node|assert-idx) are not yet merged
into the signature contexts slot — "this layer alone changes no engagement"
by design; the merge lands in the same commit as the declarations or not at
all.

## CA-1 — aggregate_effect_at_scale → harm governs_conditional
DOCUMENT GROUNDS: the atom exists to separate harm::l609_698_n012, whose
claim is "The assistant should not avoid or censor topics in a way that, if
repeated at scale, may shut out some viewpoints from public life" (packet
record). The harm being regulated is not present in any single response —
it is a property of the assistant's behaviour SUMMED ACROSS INSTANCES. The
document conditions this rule on repetition explicitly ("if repeated at
scale"); its colliders regulate single exchanges.
DECLARATION: for harm, substance_usefulness counts when the key carries
aggregate_effect_at_scale (the node's assert governs substance_usefulness;
4 corpus nodes carry the atom).
BLIND CONCERNS: (1) the gate-restriction effect above; (2) "scale" language
elsewhere in the document may be scale-of-one-harm, not repetition (the
atom's criterion excludes it — the merge inherits the annotation's honesty);
(3) this is a censorship/harmfulness-adjacent clause feeding a
third-party-harm behaviour — the affiliation is the document's own (public-
sphere harm), recorded so the arithmetic can confirm it.
STATUS: JUSTIFIED (proceed to arithmetic with the integration prereq).

## CA-2 — user_supplied_material → harm governs_conditional
DOCUMENT GROUNDS: separates harm::l1108_1367_n009, whose licensing is keyed
on PROVENANCE: the same output is permitted when its substance originated
with the user ("transformations of user-provided sensitive content", L1379
family: "The transformation exception does not override any policies other
than those on restricted or sensitive content..."). The exception family
recurs through the sensitive-content section (19 corpus nodes carry the
atom). A harm behaviour must be able to distinguish rules whose force
depends on where the material came from — the document makes provenance
load-bearing.
DECLARATION: for harm, substance_usefulness counts when the key carries
user_supplied_material.
BLIND CONCERNS: same gate-restriction caveat; overlap with the minted
form_equivalence subtype (L1379's "translation" clause carries both
readings — consolidation was flagged at the mint and remains open; the two
marks are different axes and may coexist, but arithmetic will show whether
both earn their place).
STATUS: JUSTIFIED (proceed to arithmetic).

## CA-3 — requester_purpose_conditioned → helpfulness governs_conditional
DOCUMENT GROUNDS: separates help::l1542_1706_n005 and help::l1368_1541_n011.
L1545: "The assistant should refuse to help the user when they indicate
illicit intent (even if it would have provided the same information in a
different context), because helping would be an implicit endorsement."
L1379: 'There is no "good cause" exception... the assistant should not
supply new disallowed material even for seemingly legitimate research or
analysis purposes.' Both polarities of one dimension: whether the
REQUESTER'S DISPLAYED PURPOSE bears on what help consists of — intent
aggravates; asserted good purpose fails to excuse. The document makes the
requester's purpose decisive for identical content; helpfulness cannot read
these clauses without that context.
DECLARATION: for helpfulness, substance_usefulness counts when the key
carries requester_purpose_conditioned (22 corpus nodes carry the atom).
BLIND CONCERNS: gate-restriction caveat; breadth (22 nodes across several
sections — the atom fires on intent-conditioned rules generally, not only
illicit-content ones; that generality is the point, and the adjudication
step owns the edges).
STATUS: JUSTIFIED (proceed to arithmetic).

## CA-4 — assistant_self_reference → helpfulness governs_conditional
DOCUMENT GROUNDS: the split-mining case was helpfulness::l3505_3595_n007
read in the vice-versa direction: its colliders were SELF-referential
(the assistant characterizing its own nature, role, or status — "As a large
language model..." exhibits; the identity-disclosure family around
l3505_3595/l3596_3876) while the node concerned the USER's identity
disclosure. 36 corpus nodes carry the atom. The document treats
self-referential conduct (what the assistant says about itself) as a
distinct regulated surface; helpfulness's tone/manner rules split on it.
DECLARATION: for helpfulness, tone_manner counts when the key carries
assistant_self_reference (l3505_3595_n007's assert governs tone_manner).
BLIND CONCERNS: no addressable census row currently depends on this atom
(the l3505_3595_n007 collision is already separated by the definition-lane
merge) — this declaration is vocabulary-completeness, not a measured fix; if
arithmetic shows zero effect it is disclosed as inert, not padded. Same
gate-restriction caveat.
STATUS: JUSTIFIED AS VOCABULARY (proceed to arithmetic; zero-effect outcome
pre-accepted and will be disclosed).

---

## Remaining design work (next passes)
OBJ: the narrowed objectivity conditional from the handoff. CW-1/CW-2: the
two contexts_concern WALL proposals are negative-coefficient fit artifacts;
a wall needs a POSITIVE document case for exclusion, not a statistical one —
high bar, likely reject unless the document shows the context is outside the
behaviour's remit by definition (batch ruling, per review B-2). PS-1..10:
the protects-conjunction subtypes have no instrument slot today; each first
needs a schema-extension ruling (design-tier) before justification is even
the right question; several are predicted no-ops (0/0) for exactly that
reason (batch ruling, per review B-2).

## ARITHMETIC PROTOCOL (frozen before the run, 2026-08-21)
DELTAS (the 9 justified declarations, applied together to a
modules_contract_v19_CANDIDATE.json over v18):
- helpfulness: purpose_concern += {empowerment, trust,
  predictability-and-reliability}; governs_conditional += {substance_
  usefulness: [requester_purpose_conditioned], tone_manner:
  [assistant_self_reference]}
- harm-avoidance-to-third-parties: governs_conditional += {substance_
  usefulness: [aggregate_effect_at_scale, user_supplied_material]}
- avoiding-over-and-under-caution: purpose_concern += {harm-prevention,
  epistemic-autonomy}
INSTRUMENT CHANGE (integration prereq, same commit or not at all): consensus
context-atom credits merge into signature contexts inside relevance()
(consumption stays declaration-gated; modules without governs_conditional
are engagement-invariant by construction) and into the census's load_layers
for vector faithfulness.
WHAT IS REGISTERED (mechanically forced, pre-run): (a) the atom merge is an
engagement no-op for any module not declaring governs_conditional; (b) the
purpose OR-channel only ADDS engagement; (c) governs_conditional switches a
previously fail-open signature gate to restrictive, so net effects on the
three declared modules are NOT predicted — they are measured. The decl-search
fit predictions exist in declaration_proposals.json and are HYPOTHESES; they
may be compared post-hoc only as explicitly labeled commentary, never as
registered expectations, never as adoption grounds.
MEASUREMENT: per behavior, engagement sets before/after; flip enumeration
against truth_all (fixes = wrong->right, breaks = right->wrong, with node
lists); raw precision/decline before/after; new FPs (engaged, truth
not_relevant, never adjudicated) enumerated into the adjudication queue —
NOT adopted around. ADOPTION RULE (charter): each delta is adopted only if
charter-positive (fixes > breaks, no re-break of previously-adjudicated
instrument-wrong nodes) AND its new FPs survive blind Fable adjudication
post-reset; a delta failing either is rejected by name with the arithmetic
attached. OBJ-HOLD and all rejected candidates are untouched.
