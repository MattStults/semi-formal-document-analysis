% A RIVAL READING, for CQ-3 (do two passages decide any situation differently?).
%
% R1 — m0200 read on its own: "[restricted content] ... and transformations are
%      allowed." Read alone, the permission is unqualified.
% R2 — m0200 as qualified by m0255: `lifted/2` from m0255.lp.
%
% This file does not assert either reading is right. It holds both and asks the
% solver to construct the situations in which they decide differently
% (03_pipeline.md, stage-6 divergence). Load with:
%   m0255.lp clauses/m0200.lp clauses/m0201.lp clauses/m0203.lp witness.lp
permits(r_m0200_alone, P, M) :-
    policy_class(P, K), scope(transformation, K),
    forbids(P, M), transformation_of_user_content(M).

permits(r_m0255_qualified, P, M) :- lifted(P, M).

differ(P, M) :- permits(r_m0200_alone, P, M), not permits(r_m0255_qualified, P, M).
differ(P, M) :- permits(r_m0255_qualified, P, M), not permits(r_m0200_alone, P, M).

has_differ :- differ(P, M).
:- not has_differ.          % enumerate ONLY the differing situations

#show differ/2.
#show material_type/2.
#show transformation_of_user_content/1.
