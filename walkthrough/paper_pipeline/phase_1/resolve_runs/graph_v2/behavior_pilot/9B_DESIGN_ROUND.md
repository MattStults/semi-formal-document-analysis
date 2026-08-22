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
- [ ] PC-5 helpfulness +predictability-and-reliability — needs document work
- [ ] CA-1..4 the four context-atom declarations (aggregate_effect_at_scale,
      assistant_self_reference, requester_purpose_conditioned,
      user_supplied_material)
- [ ] OBJ the narrowed objectivity conditional
- [ ] CW-1 harm !vulnerable_interaction wall; CW-2 helpfulness !agentic_setting wall
- [ ] PS-1..10 protects-conjunction subtypes (most carry no instrument slot
      today; each needs a schema-extension ruling or rejection before a
      justification is even relevant)

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

## PC-5 — helpfulness: add purpose_concern `predictability-and-reliability` (pending document work)
Standard (document-anchored, survives review): justify only if the document
shows predictability-and-reliability as an INDEPENDENT end clauses serve.
Instrument-side concern (overlap with the act channel's existing coverage)
is triage only — inadmissible as grounds for either justification or
rejection, per the strengthened rule above. 77 assistant-actor assert-lane
nodes carry the credit; document work outstanding.

---

## Remaining design work (next passes)
CA-1..4: for each consensus context atom, decide WHICH behaviour's
governs_conditional (or other context-consuming declaration) it feeds, with
document grounding; the atoms are annotated corpus-wide (81 consensus
credits) but "this layer alone changes no engagement" until a declaration
consumes it. OBJ: the narrowed objectivity conditional from the handoff.
CW-1/CW-2: the two contexts_concern WALL proposals are negative-coefficient
fit artifacts; a wall needs a POSITIVE document case for exclusion, not a
statistical one — high bar, likely reject unless the document shows the
context is outside the behaviour's remit by definition. PS-1..10: the
protects-conjunction subtypes have no instrument slot today; each first
needs a schema-extension ruling (design-tier) before justification is even
the right question; several are predicted no-ops (0/0) for exactly that
reason.
