%% machine/facts.lp — a HAND TRANSCRIPTION of this repo's governance machine.
%%
%% Nothing here is inferred, designed, or extrapolated. Every fact restates a
%% rule that is already written in a repo file, and every fact carries a
%% source(Fact, File, Line) companion plus a needle(Fact, Text) giving the
%% literal string that MUST appear at that line. machine/check_model.py
%% verifies both. Where a rule is stated nowhere, it is a GAP and is recorded
%% in machine/README.md, never invented here.
%%
%% AUTHORITY ORDER (CLAUDE.md read order + the task's own rule): cycle.py is
%% the ENFORCEMENT and wins over prose. Where prose and code disagree the
%% disagreement is itself recorded — see disagreement/3 at the bottom.

% ===========================================================================
% 1. CYCLE SHAPES AND PHASE ORDER
% ===========================================================================

shape(code).
source(shape(code),"cycle.py",98). needle(shape(code),"\"code\":").
shape(checkpoint).
source(shape(checkpoint),"cycle.py",100). needle(shape(checkpoint),"\"checkpoint\":").

% phase_order(Shape, Phase, Index) — the enforced order, PHASES_BY_SHAPE.
phase_order(code,open,1).
source(phase_order(code,open,1),"cycle.py",98). needle(phase_order(code,open,1),"\"OPEN\", \"PREDICT\"").
phase_order(code,predict,2).
source(phase_order(code,predict,2),"cycle.py",98). needle(phase_order(code,predict,2),"\"PREDICT\", \"IMPLEMENT\"").
phase_order(code,implement,3).
source(phase_order(code,implement,3),"cycle.py",98). needle(phase_order(code,implement,3),"\"IMPLEMENT\", \"MEASURE\"").
phase_order(code,measure,4).
source(phase_order(code,measure,4),"cycle.py",98). needle(phase_order(code,measure,4),"\"MEASURE\", \"ADJUDICATE\"").
phase_order(code,adjudicate,5).
source(phase_order(code,adjudicate,5),"cycle.py",98). needle(phase_order(code,adjudicate,5),"\"ADJUDICATE\"").
phase_order(code,decide,6).
source(phase_order(code,decide,6),"cycle.py",99). needle(phase_order(code,decide,6),"\"DECIDE\", \"CLOSE\"").
phase_order(code,close,7).
source(phase_order(code,close,7),"cycle.py",99). needle(phase_order(code,close,7),"\"CLOSE\"").

phase_order(checkpoint,open,1).
source(phase_order(checkpoint,open,1),"cycle.py",100). needle(phase_order(checkpoint,open,1),"\"OPEN\", \"PREDICT\"").
phase_order(checkpoint,predict,2).
source(phase_order(checkpoint,predict,2),"cycle.py",100). needle(phase_order(checkpoint,predict,2),"\"PREDICT\", \"IMPLEMENT\"").
phase_order(checkpoint,implement,3).
source(phase_order(checkpoint,implement,3),"cycle.py",100). needle(phase_order(checkpoint,implement,3),"\"IMPLEMENT\", \"MEASURE\"").
phase_order(checkpoint,measure,4).
source(phase_order(checkpoint,measure,4),"cycle.py",100). needle(phase_order(checkpoint,measure,4),"\"MEASURE\", \"ADJUDICATE\"").
phase_order(checkpoint,adjudicate,5).
source(phase_order(checkpoint,adjudicate,5),"cycle.py",100). needle(phase_order(checkpoint,adjudicate,5),"\"ADJUDICATE\"").
phase_order(checkpoint,census,6).
source(phase_order(checkpoint,census,6),"cycle.py",101). needle(phase_order(checkpoint,census,6),"\"CENSUS\", \"DECIDE\"").
phase_order(checkpoint,decide,7).
source(phase_order(checkpoint,decide,7),"cycle.py",101). needle(phase_order(checkpoint,decide,7),"\"DECIDE\", \"CLOSE\"").
phase_order(checkpoint,close,8).
source(phase_order(checkpoint,close,8),"cycle.py",101). needle(phase_order(checkpoint,close,8),"\"CLOSE\"").

% The default shape is "code": the census LEAVES the per-cycle path (F1).
default_shape(code).
source(default_shape(code),"cycle.py",16). needle(default_shape(code),"The DEFAULT shape is \"code\"").

% ---------------------------------------------------------------------------
% OVERRIDABILITY. cycle.py's OVERRIDABLE tuple is the enforcement; every
% other phase is non-overridable by the _override refusal at cycle.py:553.
% ---------------------------------------------------------------------------

overridable(predict).
source(overridable(predict),"cycle.py",109). needle(overridable(predict),"OVERRIDABLE = (\"PREDICT\"").
overridable(implement).
source(overridable(implement),"cycle.py",109). needle(overridable(implement),"\"IMPLEMENT\"").
overridable(census).
source(overridable(census),"cycle.py",109). needle(overridable(census),"\"CENSUS\"").

% The refusal that makes every other phase NON-overridable.
override_refusal_enforced.
source(override_refusal_enforced,"cycle.py",553). needle(override_refusal_enforced,"if override not in OVERRIDABLE:").

% Overriding PREDICT is legal but DEMOTES the cycle: CLOSE cannot record keep.
override_demotes(predict,exploratory).
source(override_demotes(predict,exploratory),"cycle.py",567). needle(override_demotes(predict,exploratory),"state[\"exploratory\"] = True").
exploratory_refuses_keep.
source(exploratory_refuses_keep,"cycle.py",1371). needle(exploratory_refuses_keep,"state.get(\"exploratory\") and d[\"decision\"] == \"keep\"").

% An override always requires a non-empty written reason.
override_requires_reason.
source(override_requires_reason,"cycle.py",545). needle(override_requires_reason,"--override requires a non-empty --reason").

% ===========================================================================
% 2. GATES — what each blocks, what it reads, what it refuses on
% ===========================================================================
% gate_blocks(Gate, Phase)      : the phase the gate stands in front of
% gate_reads(Gate, Input)       : the artifact/state it reads
% gate_reads_constant(Gate, C)  : a NAMED constant from section 4 it reads
% gate_refuses_on(Gate, Cond)   : the condition on which it refuses/halts
% escape_path(Gate, How)        : a documented way past the gate that is NOT
%                                 the --override mechanism

gate(g_manifest_schema).
source(gate(g_manifest_schema),"cycle.py",596). needle(gate(g_manifest_schema),"manifest.json invalid").
gate_blocks(g_manifest_schema,open).
source(gate_blocks(g_manifest_schema,open),"cycle.py",581). needle(gate_blocks(g_manifest_schema,open),"def _open(self, state)").
gate_reads(g_manifest_schema,"manifest.json").
source(gate_reads(g_manifest_schema,"manifest.json"),"cycle.py",592). needle(gate_reads(g_manifest_schema,"manifest.json"),"m = _read_json(mpath)").
gate_refuses_on(g_manifest_schema,"a REQUIRED_MANIFEST_KEYS key is missing").
source(gate_refuses_on(g_manifest_schema,"a REQUIRED_MANIFEST_KEYS key is missing"),"cycle.py",593). needle(gate_refuses_on(g_manifest_schema,"a REQUIRED_MANIFEST_KEYS key is missing"),"missing key").
gate_refuses_on(g_manifest_schema,"date is not YYYY-MM-DD (no wall clock)").
source(gate_refuses_on(g_manifest_schema,"date is not YYYY-MM-DD (no wall clock)"),"cycle.py",601). needle(gate_refuses_on(g_manifest_schema,"date is not YYYY-MM-DD (no wall clock)"),"is not YYYY-MM-DD").
gate_refuses_on(g_manifest_schema,"a declared path does not exist").
source(gate_refuses_on(g_manifest_schema,"a declared path does not exist"),"cycle.py",639). needle(gate_refuses_on(g_manifest_schema,"a declared path does not exist"),"path does not exist").
gate_refuses_on(g_manifest_schema,"code shape without compatibility.version_key/statement (F9)").
source(gate_refuses_on(g_manifest_schema,"code shape without compatibility.version_key/statement (F9)"),"cycle.py",626). needle(gate_refuses_on(g_manifest_schema,"code shape without compatibility.version_key/statement (F9)"),"compatibility.version_key").

gate(g_census_scope_pin).
source(gate(g_census_scope_pin),"cycle.py",608). needle(gate(g_census_scope_pin),"census_scope").
gate_blocks(g_census_scope_pin,open).
source(gate_blocks(g_census_scope_pin,open),"cycle.py",608). needle(gate_blocks(g_census_scope_pin,open),"if m.get(\"census_scope\") != \"dev\"").
gate_reads(g_census_scope_pin,"manifest.census_scope").
source(gate_reads(g_census_scope_pin,"manifest.census_scope"),"cycle.py",608). needle(gate_reads(g_census_scope_pin,"manifest.census_scope"),"m.get(\"census_scope\")").
gate_refuses_on(g_census_scope_pin,"census_scope is not 'dev'").
source(gate_refuses_on(g_census_scope_pin,"census_scope is not 'dev'"),"cycle.py",610). needle(gate_refuses_on(g_census_scope_pin,"census_scope is not 'dev'"),"census_scope must be 'dev'").

gate(g_predict_schema).
source(gate(g_predict_schema),"cycle.py",808). needle(gate(g_predict_schema),"prediction.json invalid").
gate_blocks(g_predict_schema,predict).
source(gate_blocks(g_predict_schema,predict),"cycle.py",732). needle(gate_blocks(g_predict_schema,predict),"def _predict(self, state)").
gate_reads(g_predict_schema,"prediction.json").
source(gate_reads(g_predict_schema,"prediction.json"),"cycle.py",767). needle(gate_reads(g_predict_schema,"prediction.json"),"pred = _read_json(ppath)").
gate_refuses_on(g_predict_schema,"expected_flip_count is not {min,max} with 0<=min<=max").
source(gate_refuses_on(g_predict_schema,"expected_flip_count is not {min,max} with 0<=min<=max"),"cycle.py",773). needle(gate_refuses_on(g_predict_schema,"expected_flip_count is not {min,max} with 0<=min<=max"),"expected_flip_count must be").
gate_refuses_on(g_predict_schema,"expected_directions empty unless the honest zero-flip prediction").
source(gate_refuses_on(g_predict_schema,"expected_directions empty unless the honest zero-flip prediction"),"cycle.py",784). needle(gate_refuses_on(g_predict_schema,"expected_directions empty unless the honest zero-flip prediction"),"expected_directions must be a non-empty list").
gate_reads_constant(g_predict_schema,directions).
source(gate_reads_constant(g_predict_schema,directions),"cycle.py",789). needle(gate_reads_constant(g_predict_schema,directions),"if d not in DIRECTIONS").

gate(g_predict_freeze).
source(gate(g_predict_freeze),"cycle.py",810). needle(gate(g_predict_freeze),"state[\"frozen_prediction_sha\"]").
gate_blocks(g_predict_freeze,predict).
source(gate_blocks(g_predict_freeze,predict),"cycle.py",811). needle(gate_blocks(g_predict_freeze,predict),"state[\"frozen_manifest_sha\"]").
gate_reads(g_predict_freeze,"sha256(prediction.json) and sha256(manifest.json)").
source(gate_reads(g_predict_freeze,"sha256(prediction.json) and sha256(manifest.json)"),"cycle.py",810). needle(gate_reads(g_predict_freeze,"sha256(prediction.json) and sha256(manifest.json)"),"sha256_file(ppath)").
gate_refuses_on(g_predict_freeze,"prediction.json changed after the freeze").
source(gate_refuses_on(g_predict_freeze,"prediction.json changed after the freeze"),"cycle.py",438). needle(gate_refuses_on(g_predict_freeze,"prediction.json changed after the freeze"),"prediction.json changed AFTER the freeze").
gate_refuses_on(g_predict_freeze,"prediction.json deleted after the freeze").
source(gate_refuses_on(g_predict_freeze,"prediction.json deleted after the freeze"),"cycle.py",432). needle(gate_refuses_on(g_predict_freeze,"prediction.json deleted after the freeze"),"was DELETED after the freeze").
gate_refuses_on(g_predict_freeze,"manifest.json changed after the freeze without an amendment").
source(gate_refuses_on(g_predict_freeze,"manifest.json changed after the freeze without an amendment"),"cycle.py",453). needle(gate_refuses_on(g_predict_freeze,"manifest.json changed after the freeze without an amendment"),"manifest.json changed AFTER the freeze without an").
escape_path(g_predict_freeze,"manifest_amendments.json chain: an entry whose old_sha chains from the frozen sha and carries a non-empty reason moves the expected sha").
source(escape_path(g_predict_freeze,"manifest_amendments.json chain: an entry whose old_sha chains from the frozen sha and carries a non-empty reason moves the expected sha"),"cycle.py",448). needle(escape_path(g_predict_freeze,"manifest_amendments.json chain: an entry whose old_sha chains from the frozen sha and carries a non-empty reason moves the expected sha"),"if amend.get(\"old_sha\") == expected").

gate(g_gate_tests).
source(gate(g_gate_tests),"cycle.py",825). needle(gate(g_gate_tests),"\"-m\", \"pytest\"").
gate_blocks(g_gate_tests,implement).
source(gate_blocks(g_gate_tests,implement),"cycle.py",820). needle(gate_blocks(g_gate_tests,implement),"def _implement(self, state)").
gate_reads(g_gate_tests,"manifest.gate_tests").
source(gate_reads(g_gate_tests,"manifest.gate_tests"),"cycle.py",823). needle(gate_reads(g_gate_tests,"manifest.gate_tests"),"if m[\"gate_tests\"]").
gate_refuses_on(g_gate_tests,"pytest exits nonzero (real exit code propagated, never swallowed)").
source(gate_refuses_on(g_gate_tests,"pytest exits nonzero (real exit code propagated, never swallowed)"),"cycle.py",191). needle(gate_refuses_on(g_gate_tests,"pytest exits nonzero (real exit code propagated, never swallowed)"),"raise ToolFailed").

gate(g_declared_files_changed).
source(gate(g_declared_files_changed),"cycle.py",828). needle(gate(g_declared_files_changed),"unchanged = [rel for rel, sha in sorted(state[\"open_shas\"].items())").
gate_blocks(g_declared_files_changed,implement).
source(gate_blocks(g_declared_files_changed,implement),"cycle.py",832). needle(gate_blocks(g_declared_files_changed,implement),"HALT (IMPLEMENT)").
gate_reads(g_declared_files_changed,"state.open_shas (captured at OPEN)").
source(gate_reads(g_declared_files_changed,"state.open_shas (captured at OPEN)"),"cycle.py",657). needle(gate_reads(g_declared_files_changed,"state.open_shas (captured at OPEN)"),"state[\"open_shas\"]").
gate_refuses_on(g_declared_files_changed,"a files_to_change entry is byte-identical to its OPEN sha").
source(gate_refuses_on(g_declared_files_changed,"a files_to_change entry is byte-identical to its OPEN sha"),"cycle.py",833). needle(gate_refuses_on(g_declared_files_changed,"a files_to_change entry is byte-identical to its OPEN sha"),"byte-identical to their OPEN shas").

gate(g_closure_unchanged).
source(gate(g_closure_unchanged),"cycle.py",838). needle(gate(g_closure_unchanged),"state.get(\"closure_shas\"").
gate_blocks(g_closure_unchanged,implement).
source(gate_blocks(g_closure_unchanged,implement),"cycle.py",843). needle(gate_blocks(g_closure_unchanged,implement),"raise CycleError").
gate_reads(g_closure_unchanged,"state.closure_shas (captured at OPEN)").
source(gate_reads(g_closure_unchanged,"state.closure_shas (captured at OPEN)"),"cycle.py",669). needle(gate_reads(g_closure_unchanged,"state.closure_shas (captured at OPEN)"),"state[\"closure_shas\"]").
gate_reads_constant(g_closure_unchanged,closure_defaults).
source(gate_reads_constant(g_closure_unchanged,closure_defaults),"cycle.py",665). needle(gate_reads_constant(g_closure_unchanged,closure_defaults),"for rel in CLOSURE_DEFAULTS").
gate_refuses_on(g_closure_unchanged,"an undeclared pinned input changed or disappeared since OPEN").
source(gate_refuses_on(g_closure_unchanged,"an undeclared pinned input changed or disappeared since OPEN"),"cycle.py",844). needle(gate_refuses_on(g_closure_unchanged,"an undeclared pinned input changed or disappeared since OPEN"),"UNDECLARED INPUTS CHANGED since OPEN").

gate(g_review_verdict).
source(gate(g_review_verdict),"cycle.py",852). needle(gate(g_review_verdict),"if m[\"review_required\"]").
gate_blocks(g_review_verdict,implement).
source(gate_blocks(g_review_verdict,implement),"cycle.py",867). needle(gate_blocks(g_review_verdict,implement),"HALT (IMPLEMENT): review_required").
gate_reads(g_review_verdict,"review_verdict.json").
source(gate_reads(g_review_verdict,"review_verdict.json"),"cycle.py",873). needle(gate_reads(g_review_verdict,"review_verdict.json"),"review = _read_json(rpath)").
gate_refuses_on(g_review_verdict,"verdict is not proceed|blocked").
source(gate_refuses_on(g_review_verdict,"verdict is not proceed|blocked"),"cycle.py",876). needle(gate_refuses_on(g_review_verdict,"verdict is not proceed|blocked"),"verdict must be proceed|blocked").
gate_refuses_on(g_review_verdict,"'by' is empty").
source(gate_refuses_on(g_review_verdict,"'by' is empty"),"cycle.py",879). needle(gate_refuses_on(g_review_verdict,"'by' is empty"),"'by' is empty").
gate_refuses_on(g_review_verdict,"verdict is blocked").
source(gate_refuses_on(g_review_verdict,"verdict is blocked"),"cycle.py",882). needle(gate_refuses_on(g_review_verdict,"verdict is blocked"),"review verdict is BLOCKED").

gate(g_baseline_snapshot).
source(gate(g_baseline_snapshot),"cycle.py",914). needle(gate(g_baseline_snapshot),"if not os.path.exists(base_path)").
gate_blocks(g_baseline_snapshot,measure).
source(gate_blocks(g_baseline_snapshot,measure),"cycle.py",910). needle(gate_blocks(g_baseline_snapshot,measure),"def _measure(self, state)").
gate_reads(g_baseline_snapshot,"snapshots/<baseline_snapshot_tag>.json").
source(gate_reads(g_baseline_snapshot,"snapshots/<baseline_snapshot_tag>.json"),"cycle.py",913). needle(gate_reads(g_baseline_snapshot,"snapshots/<baseline_snapshot_tag>.json"),"base_path = os.path.join(SNAPSHOT_DIR").
gate_refuses_on(g_baseline_snapshot,"the named baseline snapshot does not exist").
source(gate_refuses_on(g_baseline_snapshot,"the named baseline snapshot does not exist"),"cycle.py",916). needle(gate_refuses_on(g_baseline_snapshot,"the named baseline snapshot does not exist"),"baseline snapshot").

gate(g_tag_immutable).
source(gate(g_tag_immutable),"cycle.py",945). needle(gate(g_tag_immutable),"sha256_file(published) != sha256_file(built)").
gate_blocks(g_tag_immutable,measure).
source(gate_blocks(g_tag_immutable,measure),"cycle.py",946). needle(gate_blocks(g_tag_immutable,measure),"raise CycleError").
gate_reads(g_tag_immutable,"snapshots/<cycle>.json vs the cycle-local build").
source(gate_reads(g_tag_immutable,"snapshots/<cycle>.json vs the cycle-local build"),"cycle.py",943). needle(gate_reads(g_tag_immutable,"snapshots/<cycle>.json vs the cycle-local build"),"published = os.path.join(SNAPSHOT_DIR").
gate_refuses_on(g_tag_immutable,"a published snapshot tag exists with different content (F3)").
source(gate_refuses_on(g_tag_immutable,"a published snapshot tag exists with different content (F3)"),"cycle.py",949). needle(gate_refuses_on(g_tag_immutable,"a published snapshot tag exists with different content (F3)"),"tags are immutable").

gate(g_flip_budget).
source(gate(g_flip_budget),"cycle.py",981). needle(gate(g_flip_budget),"if len(flips) > FLIP_BUDGET").
gate_blocks(g_flip_budget,measure).
source(gate_blocks(g_flip_budget,measure),"cycle.py",982). needle(gate_blocks(g_flip_budget,measure),"return False, BUDGET_HALT.format").
gate_reads(g_flip_budget,"len(flips) from diff.json").
source(gate_reads(g_flip_budget,"len(flips) from diff.json"),"cycle.py",978). needle(gate_reads(g_flip_budget,"len(flips) from diff.json"),"flips = self._flip_list(diff)").
gate_reads_constant(g_flip_budget,flip_budget).
source(gate_reads_constant(g_flip_budget,flip_budget),"cycle.py",981). needle(gate_reads_constant(g_flip_budget,flip_budget),"FLIP_BUDGET").
gate_refuses_on(g_flip_budget,"more than FLIP_BUDGET flips and no flip_budget_plan.json").
source(gate_refuses_on(g_flip_budget,"more than FLIP_BUDGET flips and no flip_budget_plan.json"),"cycle.py",981). needle(gate_refuses_on(g_flip_budget,"more than FLIP_BUDGET flips and no flip_budget_plan.json"),"not os.path.exists(plan_path)").
% THE ESCAPE. A plan file with resolution=stratified_sample and a non-empty
% rationale lets MEASURE proceed. No code draws or verifies the sample.
escape_path(g_flip_budget,"flip_budget_plan.json with resolution=stratified_sample and a non-empty rationale").
source(escape_path(g_flip_budget,"flip_budget_plan.json with resolution=stratified_sample and a non-empty rationale"),"cycle.py",989). needle(escape_path(g_flip_budget,"flip_budget_plan.json with resolution=stratified_sample and a non-empty rationale"),"'stratified_sample'").
escape_validates_only(g_flip_budget,"resolution in {split,stratified_sample}").
source(escape_validates_only(g_flip_budget,"resolution in {split,stratified_sample}"),"cycle.py",986). needle(escape_validates_only(g_flip_budget,"resolution in {split,stratified_sample}"),"plan.get(\"resolution\") not in (\"split\", \"stratified_sample\")").
escape_validates_only(g_flip_budget,"rationale is a non-empty string").
source(escape_validates_only(g_flip_budget,"rationale is a non-empty string"),"cycle.py",991). needle(escape_validates_only(g_flip_budget,"rationale is a non-empty string"),"rationale is empty").
% ...and every flip is still dossiered; the seat is trusted to honour strata.
escape_unverified(g_flip_budget,"no code draws the strata, checks strata coverage, or verifies the sample against behaviour x direction x cause").
source(escape_unverified(g_flip_budget,"no code draws the strata, checks strata coverage, or verifies the sample against behaviour x direction x cause"),"cycle.py",999). needle(escape_unverified(g_flip_budget,"no code draws the strata, checks strata coverage, or verifies the sample against behaviour x direction x cause"),"\"dossiers\",").

gate(g_verdict_binding).
source(gate(g_verdict_binding),"cycle.py",1142). needle(gate(g_verdict_binding),"if raw[\"dossier_set_sha\"] != set_sha").
gate_blocks(g_verdict_binding,adjudicate).
source(gate_blocks(g_verdict_binding,adjudicate),"cycle.py",1119). needle(gate_blocks(g_verdict_binding,adjudicate),"def _adjudicate(self, state)").
gate_reads(g_verdict_binding,"flip_verdicts.json dossier_set_sha vs state.dossier_set_sha").
source(gate_reads(g_verdict_binding,"flip_verdicts.json dossier_set_sha vs state.dossier_set_sha"),"cycle.py",1120). needle(gate_reads(g_verdict_binding,"flip_verdicts.json dossier_set_sha vs state.dossier_set_sha"),"state.get(\"dossier_set_sha\"").
gate_refuses_on(g_verdict_binding,"flip_verdicts.json has no dossier_set_sha key").
source(gate_refuses_on(g_verdict_binding,"flip_verdicts.json has no dossier_set_sha key"),"cycle.py",1139). needle(gate_refuses_on(g_verdict_binding,"flip_verdicts.json has no dossier_set_sha key"),"dossier_set_sha key echoing the assignment").
gate_refuses_on(g_verdict_binding,"the echoed sha names a different dossier set").
source(gate_refuses_on(g_verdict_binding,"the echoed sha names a different dossier set"),"cycle.py",1146). needle(gate_refuses_on(g_verdict_binding,"the echoed sha names a different dossier set"),"the verdicts were made over DIFFERENT").

gate(g_flip_validator).
source(gate(g_flip_validator),"cycle.py",1150). needle(gate(g_flip_validator),"\"dossier.py\"").
gate_blocks(g_flip_validator,adjudicate).
source(gate_blocks(g_flip_validator,adjudicate),"cycle.py",1151). needle(gate_blocks(g_flip_validator,adjudicate),"\"--verdict-file\"").
gate_reads(g_flip_validator,"flip_dossiers/ and flip_verdicts.json").
source(gate_reads(g_flip_validator,"flip_dossiers/ and flip_verdicts.json"),"cycle.py",1151). needle(gate_reads(g_flip_validator,"flip_dossiers/ and flip_verdicts.json"),"self._p(\"flip_dossiers\")").
gate_refuses_on(g_flip_validator,"dossier.py validate exits nonzero").
source(gate_refuses_on(g_flip_validator,"dossier.py validate exits nonzero"),"cycle.py",1150). needle(gate_refuses_on(g_flip_validator,"dossier.py validate exits nonzero"),"_run([PYTHON").
% THE ESCAPE around a NON-OVERRIDABLE gate: the no-op short circuit at
% MEASURE marks ADJUDICATE (and CENSUS) completed without either running.
escape_path(g_flip_validator,"MEASURE no-op short-circuit appends ADJUDICATE to state.completed without any verdict file").
source(escape_path(g_flip_validator,"MEASURE no-op short-circuit appends ADJUDICATE to state.completed without any verdict file"),"cycle.py",968). needle(escape_path(g_flip_validator,"MEASURE no-op short-circuit appends ADJUDICATE to state.completed without any verdict file"),"state[\"completed\"].append(\"ADJUDICATE\")").
escape_validates_only(g_flip_validator,"diff.json carries noop: true").
source(escape_validates_only(g_flip_validator,"diff.json carries noop: true"),"cycle.py",959). needle(escape_validates_only(g_flip_validator,"diff.json carries noop: true"),"if diff.get(\"noop\")").

gate(g_census_baseline_named).
source(gate(g_census_baseline_named),"cycle.py",1172). needle(gate(g_census_baseline_named),"if not baseline_path or not os.path.exists(baseline_path)").
gate_blocks(g_census_baseline_named,census).
source(gate_blocks(g_census_baseline_named,census),"cycle.py",1165). needle(gate_blocks(g_census_baseline_named,census),"def _census(self, state)").
gate_reads(g_census_baseline_named,"manifest.baseline_census").
source(gate_reads(g_census_baseline_named,"manifest.baseline_census"),"cycle.py",729). needle(gate_reads(g_census_baseline_named,"manifest.baseline_census"),"baseline_census").
gate_refuses_on(g_census_baseline_named,"the NAMED baseline census artifact does not exist (F2)").
source(gate_refuses_on(g_census_baseline_named,"the NAMED baseline census artifact does not exist (F2)"),"cycle.py",1174). needle(gate_refuses_on(g_census_baseline_named,"the NAMED baseline census artifact does not exist (F2)"),"HALT (CENSUS)").

gate(g_census_identity_header).
source(gate(g_census_identity_header),"cycle.py",1228). needle(gate(g_census_identity_header),"index_records[0].get(\"record\") == \"config_identity\"").
gate_blocks(g_census_identity_header,census).
source(gate_blocks(g_census_identity_header,census),"cycle.py",1229). needle(gate_blocks(g_census_identity_header,census),"raise CycleError").
gate_reads(g_census_identity_header,"census/audit_dossiers/<tag>/index.jsonl first line").
source(gate_reads(g_census_identity_header,"census/audit_dossiers/<tag>/index.jsonl first line"),"cycle.py",1220). needle(gate_reads(g_census_identity_header,"census/audit_dossiers/<tag>/index.jsonl first line"),"index_records = [json.loads(line)").
gate_refuses_on(g_census_identity_header,"the census index has no config-identity header record").
source(gate_refuses_on(g_census_identity_header,"the census index has no config-identity header record"),"cycle.py",1230). needle(gate_refuses_on(g_census_identity_header,"the census index has no config-identity header record"),"no config-identity").

gate(g_held_out_cells).
source(gate(g_held_out_cells),"cycle.py",1237). needle(gate(g_held_out_cells),"held_out = [b for b in behaviours if b not in DEV_CENSUS_CELLS]").
gate_blocks(g_held_out_cells,census).
source(gate_blocks(g_held_out_cells,census),"cycle.py",1239). needle(gate_blocks(g_held_out_cells,census),"raise CycleError").
gate_reads(g_held_out_cells,"the behaviour slugs in the census index").
source(gate_reads(g_held_out_cells,"the behaviour slugs in the census index"),"cycle.py",1235). needle(gate_reads(g_held_out_cells,"the behaviour slugs in the census index"),"behaviours = sorted").
gate_reads_constant(g_held_out_cells,dev_census_cells).
source(gate_reads_constant(g_held_out_cells,dev_census_cells),"cycle.py",1237). needle(gate_reads_constant(g_held_out_cells,dev_census_cells),"DEV_CENSUS_CELLS").
gate_refuses_on(g_held_out_cells,"a behaviour outside DEV_CENSUS_CELLS appears; the refusal is declared non-overridable in its own message").
source(gate_refuses_on(g_held_out_cells,"a behaviour outside DEV_CENSUS_CELLS appears; the refusal is declared non-overridable in its own message"),"cycle.py",1245). needle(gate_refuses_on(g_held_out_cells,"a behaviour outside DEV_CENSUS_CELLS appears; the refusal is declared non-overridable in its own message"),"non-overridable").

gate(g_census_verdict_binding).
source(gate(g_census_verdict_binding),"cycle.py",1269). needle(gate(g_census_verdict_binding),"raw.get(\"dossier_set_sha\") != set_sha").
gate_blocks(g_census_verdict_binding,census).
source(gate_blocks(g_census_verdict_binding,census),"cycle.py",1270). needle(gate_blocks(g_census_verdict_binding,census),"raise CycleError").
gate_reads(g_census_verdict_binding,"census/verdicts_<behaviour>.json").
source(gate_reads(g_census_verdict_binding,"census/verdicts_<behaviour>.json"),"cycle.py",1267). needle(gate_reads(g_census_verdict_binding,"census/verdicts_<behaviour>.json"),"verdicts_{slug}.json").
gate_refuses_on(g_census_verdict_binding,"a per-behaviour census verdict file does not echo the dossier set sha (F3)").
source(gate_refuses_on(g_census_verdict_binding,"a per-behaviour census verdict file does not echo the dossier set sha (F3)"),"cycle.py",1274). needle(gate_refuses_on(g_census_verdict_binding,"a per-behaviour census verdict file does not echo the dossier set sha (F3)"),"unbound census verdicts").

gate(g_census_validator).
source(gate(g_census_validator),"cycle.py",1281). needle(gate(g_census_validator),"\"audit_disagreements.py\"").
gate_blocks(g_census_validator,census).
source(gate_blocks(g_census_validator,census),"cycle.py",1282). needle(gate_blocks(g_census_validator,census),"\"--verdicts\"").
gate_reads(g_census_validator,"census/verdicts_merged.json and the dossier dir").
source(gate_reads(g_census_validator,"census/verdicts_merged.json and the dossier dir"),"cycle.py",1278). needle(gate_reads(g_census_validator,"census/verdicts_merged.json and the dossier dir"),"verdicts_merged.json").
gate_refuses_on(g_census_validator,"audit_disagreements.py validate exits nonzero").
source(gate_refuses_on(g_census_validator,"audit_disagreements.py validate exits nonzero"),"cycle.py",1281). needle(gate_refuses_on(g_census_validator,"audit_disagreements.py validate exits nonzero"),"_run([PYTHON").

gate(g_decision_signature).
source(gate(g_decision_signature),"cycle.py",1377). needle(gate(g_decision_signature),"if not str(d.get(\"signed_by\", \"\")).strip()").
gate_blocks(g_decision_signature,decide).
source(gate_blocks(g_decision_signature,decide),"cycle.py",1355). needle(gate_blocks(g_decision_signature,decide),"def _decide(self, state)").
gate_reads(g_decision_signature,"decision.json").
source(gate_reads(g_decision_signature,"decision.json"),"cycle.py",1367). needle(gate_reads(g_decision_signature,"decision.json"),"d = _read_json(dpath)").
gate_reads_constant(g_decision_signature,decision_values).
source(gate_reads_constant(g_decision_signature,decision_values),"cycle.py",1368). needle(gate_reads_constant(g_decision_signature,decision_values),"DECISION_VALUES").
gate_refuses_on(g_decision_signature,"decision is not keep|revert").
source(gate_refuses_on(g_decision_signature,"decision is not keep|revert"),"cycle.py",1369). needle(gate_refuses_on(g_decision_signature,"decision is not keep|revert"),"decision must be one of").
gate_refuses_on(g_decision_signature,"signed_by is empty").
source(gate_refuses_on(g_decision_signature,"signed_by is empty"),"cycle.py",1378). needle(gate_refuses_on(g_decision_signature,"signed_by is empty"),"signed_by is empty").
gate_refuses_on(g_decision_signature,"an exploratory cycle records keep").
source(gate_refuses_on(g_decision_signature,"an exploratory cycle records keep"),"cycle.py",1373). needle(gate_refuses_on(g_decision_signature,"an exploratory cycle records keep"),"EXPLORATORY").

gate(g_justification_required).
source(gate(g_justification_required),"cycle.py",1385). needle(gate(g_justification_required),"if (any_fail or state[\"overrides\"])").
gate_blocks(g_justification_required,decide).
source(gate_blocks(g_justification_required,decide),"cycle.py",1387). needle(gate_blocks(g_justification_required,decide),"raise CycleError").
gate_reads(g_justification_required,"prediction_check.json and state.overrides").
source(gate_reads(g_justification_required,"prediction_check.json and state.overrides"),"cycle.py",1383). needle(gate_reads(g_justification_required,"prediction_check.json and state.overrides"),"any_fail = bool(check and any").
gate_refuses_on(g_justification_required,"a prediction FAILed or a gate was overridden and justification is empty").
source(gate_refuses_on(g_justification_required,"a prediction FAILed or a gate was overridden and justification is empty"),"cycle.py",1388). needle(gate_refuses_on(g_justification_required,"a prediction FAILed or a gate was overridden and justification is empty"),"a non-empty justification is required").

% ===========================================================================
% 3. SEATS
% ===========================================================================
% seat_tier(Seat, haiku|frontier|human): a seat may carry MORE THAN ONE tier
% fact when the repo states an either/or (e.g. "a human, or a frontier model").
% seat_scaling_unit(Seat, Unit): how many times the seat is exercised.

% --- the loop's document-side adjudication seat -----------------------------
seat(flip_adjudicator).
source(seat(flip_adjudicator),"briefs/README.md",21). needle(seat(flip_adjudicator),"flip_adjudicator.md").
seat_brief(flip_adjudicator,"briefs/flip_adjudicator.md").
source(seat_brief(flip_adjudicator,"briefs/flip_adjudicator.md"),"cycle.py",255). needle(seat_brief(flip_adjudicator,"briefs/flip_adjudicator.md"),"briefs/flip_adjudicator.md").
seat_tier(flip_adjudicator,haiku).
source(seat_tier(flip_adjudicator,haiku),"briefs/README.md",101). needle(seat_tier(flip_adjudicator,haiku),"operable by a Haiku-class model").
seat_tier_evidence(flip_adjudicator,"Haiku 4.5 vs Opus 5, blinded, 7/7 identical verdicts").
source(seat_tier_evidence(flip_adjudicator,"Haiku 4.5 vs Opus 5, blinded, 7/7 identical verdicts"),"briefs/README.md",114). needle(seat_tier_evidence(flip_adjudicator,"Haiku 4.5 vs Opus 5, blinded, 7/7 identical verdicts"),"7/7 identical verdicts").
seat_producer(flip_adjudicator,"dossier.py dossiers").
source(seat_producer(flip_adjudicator,"dossier.py dossiers"),"MODULE_MAP.md",275). needle(seat_producer(flip_adjudicator,"dossier.py dossiers"),"`dossier.py` → `dossier.py validate`").
seat_validator(flip_adjudicator,"dossier.py validate --dir <dir> --verdict-file <file>").
source(seat_validator(flip_adjudicator,"dossier.py validate --dir <dir> --verdict-file <file>"),"MODULE_MAP.md",291). needle(seat_validator(flip_adjudicator,"dossier.py validate --dir <dir> --verdict-file <file>"),"dossier.py validate --dir").
seat_scaling_unit(flip_adjudicator,per_flip).
source(seat_scaling_unit(flip_adjudicator,per_flip),"briefs/flip_adjudicator.md",3). needle(seat_scaling_unit(flip_adjudicator,per_flip),"You adjudicate ONE flip at a time").
seat_used_at(flip_adjudicator,adjudicate).
source(seat_used_at(flip_adjudicator,adjudicate),"cycle.py",1129). needle(seat_used_at(flip_adjudicator,adjudicate),"flip-adjudicator seat must produce").

% --- the IMPLEMENT-gate review seat ----------------------------------------
seat(change_reviewer).
source(seat(change_reviewer),"briefs/README.md",42). needle(seat(change_reviewer),"change_reviewer.md").
seat_brief(change_reviewer,"briefs/change_reviewer.md").
source(seat_brief(change_reviewer,"briefs/change_reviewer.md"),"cycle.py",286). needle(seat_brief(change_reviewer,"briefs/change_reviewer.md"),"briefs/change_reviewer.md").
seat_tier(change_reviewer,frontier).
source(seat_tier(change_reviewer,frontier),"briefs/change_reviewer.md",12). needle(seat_tier(change_reviewer,frontier),"FRONTIER/CAREFUL seat").
seat_tier(change_reviewer,human).
source(seat_tier(change_reviewer,human),"briefs/change_reviewer.md",12). needle(seat_tier(change_reviewer,human),"a human or frontier model").
seat_producer(change_reviewer,"cycle.py writes assignments/review.md").
source(seat_producer(change_reviewer,"cycle.py writes assignments/review.md"),"cycle.py",858). needle(seat_producer(change_reviewer,"cycle.py writes assignments/review.md"),"REVIEW_ASSIGNMENT.format").
seat_validator(change_reviewer,"cycle.py _implement: verdict in {proceed,blocked} and non-empty 'by'").
source(seat_validator(change_reviewer,"cycle.py _implement: verdict in {proceed,blocked} and non-empty 'by'"),"cycle.py",874). needle(seat_validator(change_reviewer,"cycle.py _implement: verdict in {proceed,blocked} and non-empty 'by'"),"review.get(\"verdict\") not in (\"proceed\", \"blocked\")").
seat_scaling_unit(change_reviewer,per_cycle).
source(seat_scaling_unit(change_reviewer,per_cycle),"briefs/change_reviewer.md",5). needle(seat_scaling_unit(change_reviewer,per_cycle),"cycle whose manifest says `review_required: true`").
seat_used_at(change_reviewer,implement).
source(seat_used_at(change_reviewer,implement),"briefs/change_reviewer.md",3). needle(seat_used_at(change_reviewer,implement),"IMPLEMENT gate").

% --- the DECIDE seat --------------------------------------------------------
seat(decision_signer).
source(seat(decision_signer),"briefs/README.md",48). needle(seat(decision_signer),"decision_signer.md").
seat_brief(decision_signer,"briefs/decision_signer.md").
source(seat_brief(decision_signer,"briefs/decision_signer.md"),"MODULE_MAP.md",282). needle(seat_brief(decision_signer,"briefs/decision_signer.md"),"decision_signer.md").
seat_tier(decision_signer,human).
source(seat_tier(decision_signer,human),"briefs/decision_signer.md",11). needle(seat_tier(decision_signer,human),"a human, or a frontier model").
seat_tier(decision_signer,frontier).
source(seat_tier(decision_signer,frontier),"briefs/decision_signer.md",11). needle(seat_tier(decision_signer,frontier),"frontier model acting under an").
seat_producer(decision_signer,"cycle.py drafts decision.draft.json").
source(seat_producer(decision_signer,"cycle.py drafts decision.draft.json"),"cycle.py",1353). needle(seat_producer(decision_signer,"cycle.py drafts decision.draft.json"),"decision.draft.json").
seat_validator(decision_signer,"cycle.py _decide: closed decision vocabulary, non-empty signed_by, forced justification").
source(seat_validator(decision_signer,"cycle.py _decide: closed decision vocabulary, non-empty signed_by, forced justification"),"cycle.py",1368). needle(seat_validator(decision_signer,"cycle.py _decide: closed decision vocabulary, non-empty signed_by, forced justification"),"d.get(\"decision\") not in DECISION_VALUES").
seat_scaling_unit(decision_signer,per_cycle).
source(seat_scaling_unit(decision_signer,per_cycle),"briefs/decision_signer.md",4). needle(seat_scaling_unit(decision_signer,per_cycle),"the accountable signature on one cycle's").
seat_used_at(decision_signer,decide).
source(seat_used_at(decision_signer,decide),"briefs/decision_signer.md",3). needle(seat_used_at(decision_signer,decide),"DECIDE seat of the cycle driver").

% --- the census cause-attribution seat -------------------------------------
seat(disagreement_autopsy).
source(seat(disagreement_autopsy),"briefs/README.md",32). needle(seat(disagreement_autopsy),"disagreement_autopsy.md").
seat_brief(disagreement_autopsy,"briefs/disagreement_autopsy.md").
source(seat_brief(disagreement_autopsy,"briefs/disagreement_autopsy.md"),"cycle.py",314). needle(seat_brief(disagreement_autopsy,"briefs/disagreement_autopsy.md"),"briefs/disagreement_autopsy.md").
seat_tier(disagreement_autopsy,haiku).
source(seat_tier(disagreement_autopsy,haiku),"briefs/disagreement_autopsy.md",157). needle(seat_tier(disagreement_autopsy,haiku),"Small-model standard applies").
seat_producer(disagreement_autopsy,"audit_disagreements.py dossiers").
source(seat_producer(disagreement_autopsy,"audit_disagreements.py dossiers"),"MODULE_MAP.md",276). needle(seat_producer(disagreement_autopsy,"audit_disagreements.py dossiers"),"audit_disagreements.py dossiers").
seat_validator(disagreement_autopsy,"audit_disagreements.py validate --verdicts <file> --dossier-dir <dir>").
source(seat_validator(disagreement_autopsy,"audit_disagreements.py validate --verdicts <file> --dossier-dir <dir>"),"MODULE_MAP.md",293). needle(seat_validator(disagreement_autopsy,"audit_disagreements.py validate --verdicts <file> --dossier-dir <dir>"),"audit_disagreements.py validate --verdicts").
seat_scaling_unit(disagreement_autopsy,per_dossier).
source(seat_scaling_unit(disagreement_autopsy,per_dossier),"MODULE_MAP.md",106). needle(seat_scaling_unit(disagreement_autopsy,per_dossier),"one dossier per tool-vs-panel disagreement").
seat_used_at(disagreement_autopsy,census).
source(seat_used_at(disagreement_autopsy,census),"cycle.py",1261). needle(seat_used_at(disagreement_autopsy,census),"HALT (CENSUS): judgment required").
seat_sees_panel(disagreement_autopsy).
source(seat_sees_panel(disagreement_autopsy),"briefs/README.md",34). needle(seat_sees_panel(disagreement_autopsy),"SEES").

% --- the drift-standing seat -----------------------------------------------
seat(drift_standing).
source(seat(drift_standing),"briefs/README.md",77). needle(seat(drift_standing),"drift_standing.md").
seat_brief(drift_standing,"briefs/drift_standing.md").
source(seat_brief(drift_standing,"briefs/drift_standing.md"),"MODULE_MAP.md",284). needle(seat_brief(drift_standing,"briefs/drift_standing.md"),"drift_standing.md").
seat_tier(drift_standing,haiku).
source(seat_tier(drift_standing,haiku),"briefs/README.md",81). needle(seat_tier(drift_standing,haiku),"Small-model seat").
seat_producer(drift_standing,"drift_dossiers.py dossiers").
source(seat_producer(drift_standing,"drift_dossiers.py dossiers"),"MODULE_MAP.md",284). needle(seat_producer(drift_standing,"drift_dossiers.py dossiers"),"drift_dossiers.py dossiers").
seat_validator(drift_standing,"drift_dossiers.py validate --verdicts <file> --dossier-dir <dir>").
source(seat_validator(drift_standing,"drift_dossiers.py validate --verdicts <file> --dossier-dir <dir>"),"MODULE_MAP.md",294). needle(seat_validator(drift_standing,"drift_dossiers.py validate --verdicts <file> --dossier-dir <dir>"),"drift_dossiers.py     validate --verdicts").
seat_scaling_unit(drift_standing,per_dossier).
source(seat_scaling_unit(drift_standing,per_dossier),"briefs/drift_standing.md",4). needle(seat_scaling_unit(drift_standing,per_dossier),"one case at a time").

% --- the SELECT-step seats --------------------------------------------------
seat(select_audit).
source(seat(select_audit),"briefs/README.md",30). needle(seat(select_audit),"select_audit.md").
seat_brief(select_audit,"briefs/select_audit.md").
source(seat_brief(select_audit,"briefs/select_audit.md"),"MODULE_MAP.md",277). needle(seat_brief(select_audit,"briefs/select_audit.md"),"select_audit.md").
seat_tier(select_audit,haiku).
source(seat_tier(select_audit,haiku),"briefs/README.md",101). needle(seat_tier(select_audit,haiku),"Every judgment seat is designed to be operable by a Haiku-class model").
seat_producer(select_audit,"select_audit.py").
source(seat_producer(select_audit,"select_audit.py"),"MODULE_MAP.md",277). needle(seat_producer(select_audit,"select_audit.py"),"select_audit.py").
seat_validator(select_audit,"select_audit.py validate").
source(seat_validator(select_audit,"select_audit.py validate"),"briefs/README.md",31). needle(seat_validator(select_audit,"select_audit.py validate"),"select_audit.py validate").
seat_scaling_unit(select_audit,per_behaviour).
source(seat_scaling_unit(select_audit,per_behaviour),"briefs/select_audit.md",3). needle(seat_scaling_unit(select_audit,per_behaviour),"a behaviour's query atoms are SELECTED").

% --- the two-coder taxonomy seat -------------------------------------------
seat(blind_coder).
source(seat(blind_coder),"briefs/README.md",23). needle(seat(blind_coder),"blind_coder.md").
seat_brief(blind_coder,"briefs/blind_coder.md").
source(seat_brief(blind_coder,"briefs/blind_coder.md"),"MODULE_MAP.md",278). needle(seat_brief(blind_coder,"briefs/blind_coder.md"),"blind_coder.md").
seat_tier(blind_coder,haiku).
source(seat_tier(blind_coder,haiku),"briefs/README.md",101). needle(seat_tier(blind_coder,haiku),"Every judgment seat is designed to be operable by a Haiku-class model").
seat_producer(blind_coder,"prep_hole_corpus.py").
source(seat_producer(blind_coder,"prep_hole_corpus.py"),"MODULE_MAP.md",278). needle(seat_producer(blind_coder,"prep_hole_corpus.py"),"prep_hole_corpus.py").
seat_validator(blind_coder,"check_taxonomy.py / taxonomy_agreement.py").
source(seat_validator(blind_coder,"check_taxonomy.py / taxonomy_agreement.py"),"MODULE_MAP.md",278). needle(seat_validator(blind_coder,"check_taxonomy.py / taxonomy_agreement.py"),"check_taxonomy.py`/`taxonomy_agreement.py").
seat_scaling_unit(blind_coder,per_corpus).
source(seat_scaling_unit(blind_coder,per_corpus),"briefs/blind_coder.md",4). needle(seat_scaling_unit(blind_coder,per_corpus),"corpus of read-back loss phrases").

% --- the golden-set seats ---------------------------------------------------
seat(golden_author).
source(seat(golden_author),"briefs/README.md",27). needle(seat(golden_author),"golden_author.md").
seat_brief(golden_author,"briefs/golden_author.md").
source(seat_brief(golden_author,"briefs/golden_author.md"),"MODULE_MAP.md",279). needle(seat_brief(golden_author,"briefs/golden_author.md"),"golden_author.md").
seat_tier(golden_author,haiku).
source(seat_tier(golden_author,haiku),"briefs/README.md",101). needle(seat_tier(golden_author,haiku),"Every judgment seat is designed to be operable by a Haiku-class model").
seat_validator(golden_author,"golden.load sha-freeze + test_golden.py").
source(seat_validator(golden_author,"golden.load sha-freeze + test_golden.py"),"MODULE_MAP.md",279). needle(seat_validator(golden_author,"golden.load sha-freeze + test_golden.py"),"golden.load` sha-freeze + `test_golden.py").
seat_scaling_unit(golden_author,per_document).
source(seat_scaling_unit(golden_author,per_document),"briefs/golden_author.md",4). needle(seat_scaling_unit(golden_author,per_document),"small set of clauses from the document").

seat(golden_review).
source(seat(golden_review),"briefs/README.md",37). needle(seat(golden_review),"golden_review.md").
seat_brief(golden_review,"briefs/golden_review.md").
source(seat_brief(golden_review,"briefs/golden_review.md"),"MODULE_MAP.md",280). needle(seat_brief(golden_review,"briefs/golden_review.md"),"golden_review.md").
seat_tier(golden_review,human).
source(seat_tier(golden_review,human),"briefs/golden_review.md",5). needle(seat_tier(golden_review,human),"for a HUMAN").
seat_tier(golden_review,frontier).
source(seat_tier(golden_review,frontier),"briefs/golden_review.md",6). needle(seat_tier(golden_review,frontier),"or a frontier model, explicitly").
seat_producer(golden_review,"the golden_author seat's golden_translations.json").
source(seat_producer(golden_review,"the golden_author seat's golden_translations.json"),"briefs/golden_review.md",3). needle(seat_producer(golden_review,"the golden_author seat's golden_translations.json"),"golden_translations.json").
seat_scaling_unit(golden_review,per_document).
source(seat_scaling_unit(golden_review,per_document),"briefs/golden_review.md",4). needle(seat_scaling_unit(golden_review,per_document),"audit every atom against its").

% --- the worksheet seats ----------------------------------------------------
seat(backfill_author).
source(seat(backfill_author),"briefs/README.md",54). needle(seat(backfill_author),"backfill_author.md").
seat_brief(backfill_author,"briefs/backfill_author.md").
source(seat_brief(backfill_author,"briefs/backfill_author.md"),"MODULE_MAP.md",283). needle(seat_brief(backfill_author,"briefs/backfill_author.md"),"backfill_author.md").
seat_tier(backfill_author,frontier).
source(seat_tier(backfill_author,frontier),"briefs/backfill_author.md",5). needle(seat_tier(backfill_author,frontier),"frontier/careful seat").
seat_producer(backfill_author,"backfill_worksheet.py build --dir <dir>").
source(seat_producer(backfill_author,"backfill_worksheet.py build --dir <dir>"),"MODULE_MAP.md",283). needle(seat_producer(backfill_author,"backfill_worksheet.py build --dir <dir>"),"backfill_worksheet.py build --dir").
seat_validator(backfill_author,"backfill_worksheet.py validate --dir <dir>").
source(seat_validator(backfill_author,"backfill_worksheet.py validate --dir <dir>"),"MODULE_MAP.md",295). needle(seat_validator(backfill_author,"backfill_worksheet.py validate --dir <dir>"),"backfill_worksheet.py validate --dir").
seat_scaling_unit(backfill_author,per_worksheet_row).
source(seat_scaling_unit(backfill_author,per_worksheet_row),"briefs/backfill_author.md",3). needle(seat_scaling_unit(backfill_author,per_worksheet_row),"for every row of a worksheet").

seat(attribution_author).
source(seat(attribution_author),"briefs/README.md",61). needle(seat(attribution_author),"attribution_author.md").
seat_brief(attribution_author,"briefs/attribution_author.md").
source(seat_brief(attribution_author,"briefs/attribution_author.md"),"briefs/README.md",61). needle(seat_brief(attribution_author,"briefs/attribution_author.md"),"attribution_author.md").
seat_tier(attribution_author,haiku).
source(seat_tier(attribution_author,haiku),"briefs/README.md",69). needle(seat_tier(attribution_author,haiku),"capable-but-cheap seat").
seat_scaling_unit(attribution_author,per_worksheet_row).
source(seat_scaling_unit(attribution_author,per_worksheet_row),"briefs/attribution_author.md",3). needle(seat_scaling_unit(attribution_author,per_worksheet_row),"for every row of a worksheet").
% The producer/validator DO NOT EXIST — recorded, not invented.
seat_validator_missing(attribution_author).
source(seat_validator_missing(attribution_author),"briefs/README.md",67). needle(seat_validator_missing(attribution_author),"Producer/validator NOT YET BUILT").

% --- the density-editor seat ------------------------------------------------
seat(density_editor).
source(seat(density_editor),"briefs/density_editor.md",1). needle(seat(density_editor),"Density editor brief").
seat_brief(density_editor,"briefs/density_editor.md").
source(seat_brief(density_editor,"briefs/density_editor.md"),"check_rewrite.py",5). needle(seat_brief(density_editor,"briefs/density_editor.md"),"briefs/density_editor.md").
seat_tier(density_editor,haiku).
source(seat_tier(density_editor,haiku),"briefs/README.md",101). needle(seat_tier(density_editor,haiku),"Every judgment seat is designed to be operable by a Haiku-class model").
seat_validator(density_editor,"check_rewrite.py <before> <after>").
source(seat_validator(density_editor,"check_rewrite.py <before> <after>"),"briefs/density_editor.md",7). needle(seat_validator(density_editor,"check_rewrite.py <before> <after>"),"check_rewrite.py").
seat_scaling_unit(density_editor,per_document).
source(seat_scaling_unit(density_editor,per_document),"briefs/density_editor.md",3). needle(seat_scaling_unit(density_editor,per_document),"ONE section of a design document").
% ...and it is MISSING from briefs/README.md's list, which claims 11 briefs.
seat_unlisted_in_brief_index(density_editor).
source(seat_unlisted_in_brief_index(density_editor),"briefs/README.md",18). needle(seat_unlisted_in_brief_index(density_editor),"**11** as of 2026-08-05").

% The small-model standard that supplies the default tier.
small_model_standard_default(haiku).
source(small_model_standard_default(haiku),"briefs/README.md",101). needle(small_model_standard_default(haiku),"Every judgment seat is designed to be operable by a Haiku-class model").
% ...and the standing rule that a small/frontier divergence is a SEAT defect.
divergence_is_seat_defect.
source(divergence_is_seat_defect,"briefs/README.md",104). needle(divergence_is_seat_defect,"the default diagnosis").

% ===========================================================================
% 4. CONSTANTS — name, value, source, PROVENANCE
% ===========================================================================
% provenance(C, derived) requires a derivation(C, Where) fact naming the
% document that shows the derivation. provenance(C, chosen) means: asserted,
% and no derivation exists anywhere in the repo (searched).

constant(flip_budget,"30").
source(constant(flip_budget,"30"),"cycle.py",113). needle(constant(flip_budget,"30"),"FLIP_BUDGET = 30").
provenance(flip_budget,chosen).
source(provenance(flip_budget,chosen),"ITERATION_LOOP.md",52). needle(provenance(flip_budget,chosen),"guideline: ~30").
% The only upstream statement is a GUIDELINE with no derivation: the policy
% says "more flips than can be exhaustively adjudicated (guideline: ~30)".

constant(dev_census_cells,"avoiding-over-and-under-caution, harm-avoidance-to-third-parties, helpfulness").
source(constant(dev_census_cells,"avoiding-over-and-under-caution, harm-avoidance-to-third-parties, helpfulness"),"cycle.py",92). needle(constant(dev_census_cells,"avoiding-over-and-under-caution, harm-avoidance-to-third-parties, helpfulness"),"DEV_CENSUS_CELLS = (\"avoiding-over-and-under-caution\"").
provenance(dev_census_cells,chosen).
source(provenance(dev_census_cells,chosen),"ITERATION_LOOP.md",55). needle(provenance(dev_census_cells,chosen),"DEV / TEST split").

constant(overridable_phases,"PREDICT, IMPLEMENT, CENSUS").
source(constant(overridable_phases,"PREDICT, IMPLEMENT, CENSUS"),"cycle.py",109). needle(constant(overridable_phases,"PREDICT, IMPLEMENT, CENSUS"),"OVERRIDABLE = (\"PREDICT\", \"IMPLEMENT\", \"CENSUS\")").
provenance(overridable_phases,chosen).
source(provenance(overridable_phases,chosen),"CYCLE_DESIGN.md",100). needle(provenance(overridable_phases,chosen),"NON-OVERRIDABLE").

constant(directions,"newly_predicted, no_longer_predicted").
source(constant(directions,"newly_predicted, no_longer_predicted"),"cycle.py",115). needle(constant(directions,"newly_predicted, no_longer_predicted"),"DIRECTIONS = (\"newly_predicted\", \"no_longer_predicted\")").
provenance(directions,chosen).
source(provenance(directions,chosen),"cycle.py",115). needle(provenance(directions,chosen),"DIRECTIONS").

constant(decision_values,"keep, revert").
source(constant(decision_values,"keep, revert"),"cycle.py",116). needle(constant(decision_values,"keep, revert"),"DECISION_VALUES = (\"keep\", \"revert\")").
provenance(decision_values,chosen).
source(provenance(decision_values,chosen),"cycle.py",116). needle(provenance(decision_values,chosen),"DECISION_VALUES").

constant(closure_defaults,"modelspec_clauses.json, constitution_clauses.json, behaviours_query.json").
source(constant(closure_defaults,"modelspec_clauses.json, constitution_clauses.json, behaviours_query.json"),"cycle.py",120). needle(constant(closure_defaults,"modelspec_clauses.json, constitution_clauses.json, behaviours_query.json"),"CLOSURE_DEFAULTS = (\"modelspec_clauses.json\"").
provenance(closure_defaults,chosen).
source(provenance(closure_defaults,chosen),"cycle.py",118). needle(provenance(closure_defaults,chosen),"Undeclared inputs whose sha-pinned closure is captured at OPEN").

constant(noise_floor,"(0.0316, 0.037)").
source(constant(noise_floor,"(0.0316, 0.037)"),"breadth_filter.py",190). needle(constant(noise_floor,"(0.0316, 0.037)"),"NOISE_FLOOR = (0.0316, 0.037)").
provenance(noise_floor,derived).
source(provenance(noise_floor,derived),"HANDOFF.md",1101). needle(provenance(noise_floor,derived),"re-derived noise floor").
derivation(noise_floor,"HANDOFF.md:1046-1047 — 0.0316 at 1000 resamples / 9 cells; 0.0350-0.0357 at 2000 resamples").
source(derivation(noise_floor,"HANDOFF.md:1046-1047 — 0.0316 at 1000 resamples / 9 cells; 0.0350-0.0357 at 2000 resamples"),"HANDOFF.md",1102). needle(derivation(noise_floor,"HANDOFF.md:1046-1047 — 0.0316 at 1000 resamples / 9 cells; 0.0350-0.0357 at 2000 resamples"),"9 cells and 0.0350–0.0357 at 2000 resamples").

constant(patient_mismatch_discount,"0.10").
source(constant(patient_mismatch_discount,"0.10"),"patient.py",157). needle(constant(patient_mismatch_discount,"0.10"),"PATIENT_MISMATCH_DISCOUNT = 0.10").
provenance(patient_mismatch_discount,derived).
source(provenance(patient_mismatch_discount,derived),"REPRODUCIBILITY.md",117). needle(provenance(patient_mismatch_discount,derived),"A **derived** constant").
derivation(patient_mismatch_discount,"cycles/patient-pricing-2026-08-04/DISCOUNT_DERIVATION.md (outcome-blind)").
source(derivation(patient_mismatch_discount,"cycles/patient-pricing-2026-08-04/DISCOUNT_DERIVATION.md (outcome-blind)"),"REPRODUCIBILITY.md",120). needle(derivation(patient_mismatch_discount,"cycles/patient-pricing-2026-08-04/DISCOUNT_DERIVATION.md (outcome-blind)"),"DISCOUNT_DERIVATION.md").

constant(containment_pricing_version,"1.2").
source(constant(containment_pricing_version,"1.2"),"containment.py",125). needle(constant(containment_pricing_version,"1.2"),"PRICING_VERSION = \"1.2\"").
provenance(containment_pricing_version,chosen).
source(provenance(containment_pricing_version,chosen),"MODULE_MAP.md",103). needle(provenance(containment_pricing_version,chosen),"this is what `containment.py` sets").

constant(fanout_degenerate,"5").
source(constant(fanout_degenerate,"5"),"audit_disagreements.py",55). needle(constant(fanout_degenerate,"5"),"FANOUT_DEGENERATE = 5").
provenance(fanout_degenerate,chosen).
source(provenance(fanout_degenerate,chosen),"audit_disagreements.py",52). needle(provenance(fanout_degenerate,chosen),"5 is the working line").

% ===========================================================================
% 5. ARTIFACTS each phase produces / consumes
% ===========================================================================

consumes(open,"manifest.json").
source(consumes(open,"manifest.json"),"cycle.py",592). needle(consumes(open,"manifest.json"),"m = _read_json(mpath)").
produces(open,"manifest.template.json").
source(produces(open,"manifest.template.json"),"cycle.py",586). needle(produces(open,"manifest.template.json"),"manifest_template(self.name)").
produces(open,"state.open_shas").
source(produces(open,"state.open_shas"),"cycle.py",657). needle(produces(open,"state.open_shas"),"state[\"open_shas\"]").
produces(open,"state.closure_shas").
source(produces(open,"state.closure_shas"),"cycle.py",669). needle(produces(open,"state.closure_shas"),"state[\"closure_shas\"]").

consumes(predict,"prediction.json").
source(consumes(predict,"prediction.json"),"cycle.py",767). needle(consumes(predict,"prediction.json"),"pred = _read_json(ppath)").
produces(predict,"prediction.template.json").
source(produces(predict,"prediction.template.json"),"cycle.py",756). needle(produces(predict,"prediction.template.json"),"_write_json(tpath, tpl)").
produces(predict,"state.frozen_prediction_sha").
source(produces(predict,"state.frozen_prediction_sha"),"cycle.py",810). needle(produces(predict,"state.frozen_prediction_sha"),"frozen_prediction_sha").
produces(predict,"state.frozen_manifest_sha").
source(produces(predict,"state.frozen_manifest_sha"),"cycle.py",811). needle(produces(predict,"state.frozen_manifest_sha"),"frozen_manifest_sha").

consumes(implement,"review_verdict.json").
source(consumes(implement,"review_verdict.json"),"cycle.py",873). needle(consumes(implement,"review_verdict.json"),"review = _read_json(rpath)").
produces(implement,"assignments/review.md").
source(produces(implement,"assignments/review.md"),"cycle.py",856). needle(produces(implement,"assignments/review.md"),"\"review.md\"").
produces(implement,"state.gate").
source(produces(implement,"state.gate"),"cycle.py",885). needle(produces(implement,"state.gate"),"state[\"gate\"]").

consumes(measure,"snapshots/<baseline_snapshot_tag>.json").
source(consumes(measure,"snapshots/<baseline_snapshot_tag>.json"),"cycle.py",913). needle(consumes(measure,"snapshots/<baseline_snapshot_tag>.json"),"base_path = os.path.join(SNAPSHOT_DIR").
consumes(measure,"flip_budget_plan.json").
source(consumes(measure,"flip_budget_plan.json"),"cycle.py",985). needle(consumes(measure,"flip_budget_plan.json"),"plan = _read_json(plan_path)").
produces(measure,"snapshots/<cycle>.json").
source(produces(measure,"snapshots/<cycle>.json"),"cycle.py",954). needle(produces(measure,"snapshots/<cycle>.json"),"shutil.copyfile(built, published)").
produces(measure,"diff.json").
source(produces(measure,"diff.json"),"cycle.py",957). needle(produces(measure,"diff.json"),"self._p(\"diff.json\")").
produces(measure,"flip_dossiers/").
source(produces(measure,"flip_dossiers/"),"cycle.py",1001). needle(produces(measure,"flip_dossiers/"),"\"--out-dir\", self._p(\"flip_dossiers\")").
produces(measure,"prediction_check.json").
source(produces(measure,"prediction_check.json"),"cycle.py",1115). needle(produces(measure,"prediction_check.json"),"prediction_check.json").

consumes(adjudicate,"flip_verdicts.json").
source(consumes(adjudicate,"flip_verdicts.json"),"cycle.py",1133). needle(consumes(adjudicate,"flip_verdicts.json"),"raw = _read_json(vpath)").
produces(adjudicate,"assignments/flips.md").
source(produces(adjudicate,"assignments/flips.md"),"cycle.py",1123). needle(produces(adjudicate,"assignments/flips.md"),"FLIPS_ASSIGNMENT.format").
produces(adjudicate,"state.flip_tallies").
source(produces(adjudicate,"state.flip_tallies"),"cycle.py",1154). needle(produces(adjudicate,"state.flip_tallies"),"state[\"flip_tallies\"]").

consumes(census,"census/verdicts_<behaviour>.json").
source(consumes(census,"census/verdicts_<behaviour>.json"),"cycle.py",1267). needle(consumes(census,"census/verdicts_<behaviour>.json"),"verdicts_{slug}.json").
produces(census,"assignments/census_<behaviour>.md").
source(produces(census,"assignments/census_<behaviour>.md"),"cycle.py",1252). needle(produces(census,"assignments/census_<behaviour>.md"),"census_{slug}.md").
produces(census,"census/verdicts_merged.json").
source(produces(census,"census/verdicts_merged.json"),"cycle.py",1278). needle(produces(census,"census/verdicts_merged.json"),"verdicts_merged.json").
produces(census,"census_delta.json").
source(produces(census,"census_delta.json"),"cycle.py",1289). needle(produces(census,"census_delta.json"),"census_delta.json").

consumes(decide,"decision.json").
source(consumes(decide,"decision.json"),"cycle.py",1367). needle(consumes(decide,"decision.json"),"d = _read_json(dpath)").
produces(decide,"decision.draft.json").
source(produces(decide,"decision.draft.json"),"cycle.py",1353). needle(produces(decide,"decision.draft.json"),"decision.draft.json").

produces(close,"cycles/CYCLE_LOG.jsonl line").
source(produces(close,"cycles/CYCLE_LOG.jsonl line"),"cycle.py",1426). needle(produces(close,"cycles/CYCLE_LOG.jsonl line"),"CYCLE_LOG.jsonl").
produces(close,"commit_message.txt").
source(produces(close,"commit_message.txt"),"cycle.py",1448). needle(produces(close,"commit_message.txt"),"commit_message.txt").
produces(close,"staging_list.txt").
source(produces(close,"staging_list.txt"),"cycle.py",1451). needle(produces(close,"staging_list.txt"),"staging_list.txt").
driver_never_runs_git.
source(driver_never_runs_git,"CYCLE_DESIGN.md",255). needle(driver_never_runs_git,"The driver NEVER runs git").

% ===========================================================================
% 6. SEMANTICS THE CONTRADICTION RULES NEED (all repo-stated)
% ===========================================================================

% What a `side` value asserts. Only both_defensible asserts NO fault.
side_asserts_no_fault("both_defensible").
source(side_asserts_no_fault("both_defensible"),"briefs/disagreement_autopsy.md",140). needle(side_asserts_no_fault("both_defensible"),"genuinely supports both readings").
% The taxonomy carries dedicated `either`-kind causes for exactly that case.
either_kind_cause_exists("boundary_dispute_tool_defensible").
source(either_kind_cause_exists("boundary_dispute_tool_defensible"),"audit_disagreements.py",161). needle(either_kind_cause_exists("boundary_dispute_tool_defensible"),"boundary_dispute_tool_defensible").
either_kind_cause_exists("boundary_dispute_panel_defensible").
source(either_kind_cause_exists("boundary_dispute_panel_defensible"),"audit_disagreements.py",168). needle(either_kind_cause_exists("boundary_dispute_panel_defensible"),"boundary_dispute_panel_defensible").
% An FP/FN-kind cause names a tool error: the validator itself pairs cause
% kind with the dossier's FP/FN kind.
fault_asserting_kind("FP").
source(fault_asserting_kind("FP"),"audit_disagreements.py",532). needle(fault_asserting_kind("FP"),"spec.get(\"kind\") in (\"FN\", \"FP\")").
fault_asserting_kind("FN").
source(fault_asserting_kind("FN"),"audit_disagreements.py",532). needle(fault_asserting_kind("FN"),"spec.get(\"kind\") in (\"FN\", \"FP\")").

% ===========================================================================
% 7. PROSE/CODE DISAGREEMENTS FOUND (recorded, not resolved)
% ===========================================================================
% disagreement(Id, "what prose says", "what code does")

disagreement(f5_stale_rationale,"CYCLE_DESIGN.md F5 marks the 'concurrent agents and no git' rationale STALE and corrected per PORTFOLIO_REVIEW F12","cycle.py's closure refusal message still prints that exact stale rationale to the operator").
source(disagreement(f5_stale_rationale,"CYCLE_DESIGN.md F5 marks the 'concurrent agents and no git' rationale STALE and corrected per PORTFOLIO_REVIEW F12","cycle.py's closure refusal message still prints that exact stale rationale to the operator"),"cycle.py",846). needle(disagreement(f5_stale_rationale,"CYCLE_DESIGN.md F5 marks the 'concurrent agents and no git' rationale STALE and corrected per PORTFOLIO_REVIEW F12","cycle.py's closure refusal message still prints that exact stale rationale to the operator"),"concurrent agents and no git").

disagreement(census_in_default_phases,"CYCLE_DESIGN.md's numbered Phases list still has CENSUS as phase 6 of the cycle","PHASES_BY_SHAPE puts CENSUS only in the checkpoint shape, per BINDING AMENDMENT F1").
source(disagreement(census_in_default_phases,"CYCLE_DESIGN.md's numbered Phases list still has CENSUS as phase 6 of the cycle","PHASES_BY_SHAPE puts CENSUS only in the checkpoint shape, per BINDING AMENDMENT F1"),"CYCLE_DESIGN.md",34). needle(disagreement(census_in_default_phases,"CYCLE_DESIGN.md's numbered Phases list still has CENSUS as phase 6 of the cycle","PHASES_BY_SHAPE puts CENSUS only in the checkpoint shape, per BINDING AMENDMENT F1"),"CENSUS").

disagreement(predict_targets,"CYCLE_DESIGN.md phase 2 says prediction.json holds expected_shrink / must_not_grow over the closed cause taxonomy","the driver requires mechanism-level targets and accepts census_classes only in the checkpoint shape (F1)").
source(disagreement(predict_targets,"CYCLE_DESIGN.md phase 2 says prediction.json holds expected_shrink / must_not_grow over the closed cause taxonomy","the driver requires mechanism-level targets and accepts census_classes only in the checkpoint shape (F1)"),"CYCLE_DESIGN.md",26). needle(disagreement(predict_targets,"CYCLE_DESIGN.md phase 2 says prediction.json holds expected_shrink / must_not_grow over the closed cause taxonomy","the driver requires mechanism-level targets and accepts census_classes only in the checkpoint shape (F1)"),"expected_shrink").

disagreement(brief_count,"briefs/README.md says the directory holds 11 briefs as of 2026-08-05","ls briefs/*.md returns 12 — density_editor.md is in the directory and absent from the list").
source(disagreement(brief_count,"briefs/README.md says the directory holds 11 briefs as of 2026-08-05","ls briefs/*.md returns 12 — density_editor.md is in the directory and absent from the list"),"briefs/README.md",18). needle(disagreement(brief_count,"briefs/README.md says the directory holds 11 briefs as of 2026-08-05","ls briefs/*.md returns 12 — density_editor.md is in the directory and absent from the list"),"**11** as of 2026-08-05").

disagreement(side_cause_independence,"the disagreement_autopsy brief states side and cause are independent, so a defensible call may still carry a mechanical cause","the CAUSE_TAXONOMY gives FP/FN kinds a fault-asserting meaning and supplies dedicated either-kind boundary_dispute causes for genuinely defensible cases").
source(disagreement(side_cause_independence,"the disagreement_autopsy brief states side and cause are independent, so a defensible call may still carry a mechanical cause","the CAUSE_TAXONOMY gives FP/FN kinds a fault-asserting meaning and supplies dedicated either-kind boundary_dispute causes for genuinely defensible cases"),"briefs/disagreement_autopsy.md",144). needle(disagreement(side_cause_independence,"the disagreement_autopsy brief states side and cause are independent, so a defensible call may still carry a mechanical cause","the CAUSE_TAXONOMY gives FP/FN kinds a fault-asserting meaning and supplies dedicated either-kind boundary_dispute causes for genuinely defensible cases"),"a tool that was wrong for a mechanical reason still gets its mechanical").

% ===========================================================================
% 8. MACHINE-READABLE CONSTANT VALUES (for machine/semantics.lp)
% ===========================================================================

constant_int(flip_budget,30).
source(constant_int(flip_budget,30),"cycle.py",113). needle(constant_int(flip_budget,30),"FLIP_BUDGET = 30").
decision_value(keep).
source(decision_value(keep),"cycle.py",116). needle(decision_value(keep),"\"keep\"").
decision_value(revert).
source(decision_value(revert),"cycle.py",116). needle(decision_value(revert),"\"revert\"").
direction_value(newly_predicted).
source(direction_value(newly_predicted),"cycle.py",115). needle(direction_value(newly_predicted),"\"newly_predicted\"").
direction_value(no_longer_predicted).
source(direction_value(no_longer_predicted),"cycle.py",115). needle(direction_value(no_longer_predicted),"\"no_longer_predicted\"").
dev_cell("avoiding-over-and-under-caution").
source(dev_cell("avoiding-over-and-under-caution"),"cycle.py",92). needle(dev_cell("avoiding-over-and-under-caution"),"avoiding-over-and-under-caution").
dev_cell("harm-avoidance-to-third-parties").
source(dev_cell("harm-avoidance-to-third-parties"),"cycle.py",93). needle(dev_cell("harm-avoidance-to-third-parties"),"harm-avoidance-to-third-parties").
dev_cell("helpfulness").
source(dev_cell("helpfulness"),"cycle.py",94). needle(dev_cell("helpfulness"),"helpfulness").
closure_default("modelspec_clauses.json").
source(closure_default("modelspec_clauses.json"),"cycle.py",120). needle(closure_default("modelspec_clauses.json"),"modelspec_clauses.json").
closure_default("constitution_clauses.json").
source(closure_default("constitution_clauses.json"),"cycle.py",120). needle(closure_default("constitution_clauses.json"),"constitution_clauses.json").
closure_default("behaviours_query.json").
source(closure_default("behaviours_query.json"),"cycle.py",121). needle(closure_default("behaviours_query.json"),"behaviours_query.json").
