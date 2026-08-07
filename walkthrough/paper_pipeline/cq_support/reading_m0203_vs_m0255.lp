% TWO READINGS OF THE SAME PROHIBITION, for CQ-3.b — the control case.
%
% R1 — m0203 read on its own: "*Prohibited content* should never be produced by
%      the assistant in any circumstance --- **including** transformations of
%      user-provided content."
% R2 — the same prohibition as it survives m0255's exception machinery
%      (`binds/2`, reached via `out_of_scope(transformation, prohibited)`).
%
% Expected before running: EMPTY. The two readings are the same rule stated from
% two sides, so no situation should separate them, and the stage-6 rule says an
% empty differing set means the difference is immaterial. This instance exists so
% that CQ-3 has a negative case: a divergence check that can only ever report
% "they differ" is not a check.
forbidden_r1(P, M) :- policy_class(P, prohibited), forbids(P, M).
forbidden_r2(P, M) :- binds(P, M), policy_class(P, prohibited).

differ(P, M) :- forbidden_r1(P, M), not forbidden_r2(P, M).
differ(P, M) :- forbidden_r2(P, M), not forbidden_r1(P, M).

has_differ :- differ(P, M).
:- not has_differ.          % UNSATISFIABLE  <=>  the readings never diverge

#show differ/2.
