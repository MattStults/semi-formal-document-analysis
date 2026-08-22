# GENERALIZATION MODULE BUILD SPEC (frozen prereg GENERALIZATION_PREREG_DRAFT.md, signed 2026-08-21)

One a-priori module per held-out behaviour. Builders work BLIND.
ALLOWED INPUTS: the behaviour's definition text (data/panel-v5/
behaviour-definitions-v5.json — definitions only), the frozen act
vocabulary (act_inventory.json, act_bridges.json, act_arg_sorts.json,
act_party.json), the module schema (one v18 module in
modules_contract_v18.json as a SCHEMA exemplar only),
TRANSLATION_CONTRACT_V2.md.
FORBIDDEN INPUTS (do not open, do not grep): data/panel-v5/runlog-v5.jsonl,
data/behaviours.json, data/panel-coverage.json, everything under
panel_run1/ (truth, adjudications, census, arithmetic),
satisfiability_census*.json, and any engagement run on the behaviour being
built. Builders MUST NOT run the instrument.
SCHEMA (what relevance() consumes): top-level entry with "module": {"does":
[<canonical act names the behaviour PERFORMS, from the frozen vocabulary>],
"definition": <the behaviour definition>}, plus optional "governs_concern":
[qualities], "purpose_concern": [purposes], "protects_concern": [parties],
"arg_sorts": {act: [sorts]}, "party_concern": [parties].
DERIVATION RULES: acts performed from what the definition says the model
DOES; walls from what the definition says the model PROTECTS and the
purposes it SERVES; every declaration justified from the definition text
alone, cited in the rationale. No governs_conditional (9b found it inert
against unconditional declarations; the context-atom lane carries no
declarations).
OUTPUTS per behaviour: generalization_builds/<slug>.json (the module entry)
+ generalization_builds/<slug>_RATIONALE.md (per-declaration grounds from
the definition, and a list of vocabulary gaps found — acts the definition
implies that the frozen vocabulary lacks — recorded, not invented).
Modules freeze as built; no revision before scoring (attempt 1 carries the
transfer verdict).
