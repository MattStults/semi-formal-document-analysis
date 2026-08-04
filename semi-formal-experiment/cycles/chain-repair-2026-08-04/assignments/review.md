# Change review assignment — cycle chain-repair-2026-08-04

Seat brief: briefs/change_reviewer.md — read it first; it is the seat's
entire instruction. This is a frontier/careful seat: it exists to catch the
implementer's mistakes, so the small-model standard does not apply.

Change under review (from the manifest):

- fix_description: Apply the 12 chain-audit corrections (chain_audit/verdicts.json) as five atom_refactor rechain migrations: four whole-artifact principal-chain repairs __user -> __model_user (must_disclose_response_changes, must_preserve_user_agency, must_advise_immediate_help, should_support_world_connection; 11 agent_missing verdicts) plus one clause-scoped fold shouldnot_judge__model_user_developer -> shouldnot_judge__model_user --clause m0271 (unlicensed developer patient; m0170's verdict-correct instance of the same name is untouched). All applied with --apply --date 2026-08-04, reasons citing chain_audit/verdicts.json, logged and replayable in vocabulary_migrations.json.
- document_side_rationale: chain_audit verdicts - grammar-convention repairs, document-side, label-free. Each corrected atom's clause names the assistant as the acting party and the user as patient; the sole-member __user chains misread the patient as agent under the grammar's agent-first convention (grammar.py: order is the relation). m0271's clause licenses only the user patient. No panel outcome informs any rename. NOTES: (1) baseline_snapshot_tag versioned-cut-2026-08-04 was built WITHOUT --thresholds on the old code path; its cuts equal thresholds_frozen.json's values by construction (that closed cycle froze them from the same config), so it is a valid baseline for this cycle's --thresholds measured snapshot; any cut difference would surface as flips and falsify the zero-flip prediction. (2) annotations_ext_v1_patch.json is an atom_refactor scan surface but carries ZERO usages of the five affected names (verified by grep and by its absence from all five dry-run change sets), so it is deliberately omitted from files_to_change. (3) vocabulary_migrations.json did not exist before this cycle; it was initialized pre-OPEN as the tool's own canonical empty log ({artifact, version, migrations: []} via atom_refactor.load_log/_dumps) so its sha is pinned at OPEN and the five appended migration entries satisfy the changed-file gate.
- files_to_change: annotations_ext_v1.json, annotations_ext_v1_merged.json, behavior_atoms_audit_v1.json, vocabulary_migrations.json
- gate_tests: test_atom_refactor.py, test_grammar.py, test_no_reference_leak.py

Required output: review_verdict.json in this cycle's directory:

    {"verdict": "proceed" | "blocked",
      "by": "<who reviewed — never the implementer>",
      "notes": "<what was verified, or why blocked>"}

All three keys are REQUIRED; verdict is a CLOSED set. The driver re-checks
the frozen manifest/prediction shas, the two-sided one-variable check and
the gate tests mechanically; your seat verifies what the machine cannot
(see the brief: freeze shas, declared-diff-only, tests bind — at least one
mutant — and the fence scan). A "blocked" verdict halts the cycle until
resolved and re-reviewed.
