# CLAIMS-SIGNATURE ANNOTATION BRIEF (definitional lane)

You annotate CLAIMS from modules translated from a spec regulating an AI assistant.
These modules assert no norms — they carry definitional/descriptive claims. For EACH
claim, judge from the claim text plus the source span (ESTABLISHES + SOURCE TEXT):

1. "acts": which canonical acts does the claim DESCRIBE or CHARACTERIZE the assistant
   performing (or performing badly)? A definition that characterizes a kind of act
   counts ("steering can take the form of refusal to engage" -> refuse). A claim about
   document structure, section layout, or terminology-bookkeeping describes NO
   assistant act -> []. Choose ONLY from this canonical vocabulary (0-3 per claim):
   acknowledge, act_in_world, act_with_care, answer_directly, ask, comply,
   counter_harm, deliberate, disclose_data, engage_relationship,
   express_calibrated_position, express_stance, express_uncertainty,
   judge_or_moralize, override, protective_response, provide, provide_content,
   provide_hazardous, provide_information, provide_resources, provide_steering,
   pursue_goal, refuse, respond, respond_addressing, respond_depth,
   respond_in_manner, safe_manner, uncertainty_phrasing
   Pick the MOST SPECIFIC act the claim supports; never invent names.

2. "actor": whose conduct/machinery is the claim about? assistant = characterizes
   assistant conduct or qualities of assistant responses; document = the document's own
   structure, instruction machinery, section layout, or drafting conventions;
   organization = the provider organization's policies/commitments as an organization;
   developer = developer/operator conduct.

3. "governs": WHAT QUALITY of assistant conduct does the claim bear on (0-2)?
   substance_usefulness = whether the response substantively helps;
   objectivity_neutrality = balance/viewpoint fairness; accuracy_calibration =
   truthfulness, honesty, uncertainty; tone_manner = interpersonal tone;
   formatting_style = layout/length/structure; identity_meta = what the assistant says
   about itself/provider. [] if none.

4. "contexts": [] or subset of: vulnerable_interaction (claim is specifically about
   protective handling of a vulnerable interaction), agentic_setting (agentic/tooling
   mechanics).

5. "protects": whose INTEREST is at stake in the claim (from the span, never inferred
   beyond it)? user, third_party, minor, society, developer, unspecified.

6. "purpose": which of the document's own ENDS does the claim serve (0-2)?
   empowerment, harm-prevention, operational-viability, universal-benefit,
   controllability, predictability-and-reliability, trust, epistemic-autonomy,
   well-being, rights-respect. [] if none evident in the span.

Judge each claim on its own text; the span provides context. Be conservative on
"acts": listing an act the claim does not actually describe is the costly error.

OUTPUT: JSON only, one object:
{"<node_id>": [{"acts": [...], "actor": "...", "governs": [...], "contexts": [...],
"protects": [...], "purpose": [...]}, ...one object per claim, in claim order...]}
