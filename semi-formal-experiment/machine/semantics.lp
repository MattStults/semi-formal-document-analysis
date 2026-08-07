%% machine/semantics.lp — the allow/refuse fragment.
%%
%% This is the part of the model that PREDICTS what cycle.py will do, so
%% machine/check_model.py can put the two side by side on synthetic cycle
%% states (the DIFFERENTIAL CHECK). It reads only facts.lp plus a handful of
%% st_* state atoms the checker supplies per scenario:
%%
%%   st_phase(P)          the phase the cycle is sitting at
%%   st_override(O)       `--override O` was passed
%%   st_reason            `--reason` was non-empty
%%   st_flips(N)          MEASURE counted N flips
%%   st_plan(R)           flip_budget_plan.json exists with resolution R
%%   st_plan_rationale    that plan's rationale is non-empty
%%   st_decision(D)       decision.json carries decision=D
%%   st_exploratory       the cycle was demoted by a PREDICT override
%%   st_signed            signed_by is non-empty
%%   st_justified         justification is non-empty
%%   st_pred_fail         prediction_check.json contains a FAIL
%%   st_overridden        state.overrides is non-empty
%%
%% Every refusal below names the cycle.py line it mirrors.

% ------------------------------------------------------- the override path

% cycle.py:544 — an unexplained skipped gate is indistinguishable from a
% forgotten one.
refuse(override_needs_reason) :- st_override(_), not st_reason.
% cycle.py:548 — only the gate actually in front of you can be skipped.
refuse(override_wrong_phase)  :- st_override(O), st_phase(P), O != P.
% cycle.py:553 — the OVERRIDABLE tuple.
refuse(override_non_overridable) :- st_override(O), st_phase(O),
                                    not overridable(O).
% cycle.py:566 — a PREDICT override demotes rather than refuses.
demotes_to_exploratory :- st_override(predict), st_phase(predict),
                          st_reason, overridable(predict).

override_allowed :- st_override(_), not any_refusal.

% ---------------------------------------------------------- MEASURE budget

% cycle.py:981 — >FLIP_BUDGET flips with no plan halts.
halt(flip_budget) :- st_flips(N), constant_int(flip_budget,B), N > B,
                     not st_plan(_).
% cycle.py:986 — the plan's resolution is a CLOSED set.
refuse(plan_resolution) :- st_plan(R), not legal_resolution(R).
legal_resolution(split).
legal_resolution(stratified_sample).
% cycle.py:990 — an empty rationale is refused.
refuse(plan_rationale_empty) :- st_plan(_), not st_plan_rationale.
% cycle.py:992 — a SPLIT plan halts: adjudicate it as separate cycles.
halt(plan_says_split) :- st_plan(split), st_plan_rationale.

measure_proceeds :- st_flips(_), not any_halt, not any_refusal.

% ----------------------------------------------------------- DECIDE gates

% cycle.py:1368 — the closed decision vocabulary.
refuse(decision_value) :- st_decision(D), not decision_value(D).
% cycle.py:1371 — an exploratory cycle cannot record keep.
refuse(exploratory_keep) :- st_exploratory, st_decision(keep).
% cycle.py:1377 — an unsigned decision is not a decision.
refuse(unsigned) :- st_decision(_), not st_signed.
% cycle.py:1385 — a FAILed prediction or any override forces a justification.
refuse(justification_required) :- st_pred_fail, st_decision(_),
                                  not st_justified.
refuse(justification_required) :- st_overridden, st_decision(_),
                                  not st_justified.

decide_accepts :- st_decision(_), not any_refusal.

% --------------------------------------------------------------- rollup

any_refusal :- refuse(_).
any_halt    :- halt(_).

#show refuse/1.
#show halt/1.
#show override_allowed/0.
#show measure_proceeds/0.
#show decide_accepts/0.
#show demotes_to_exploratory/0.
