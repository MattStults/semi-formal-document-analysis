% =====================================================================
% E2 -- NORM APPLICABILITY  (the antecedent is satisfiable)
%
%   relevant(P,B) iff, for some situation S instantiating B, P's norm is
%   TRIGGERED in S -- i.e. P's rule body is satisfied and its head attaches a
%   deontic status to something.
%
% The move over E1a: a passage does not have to NAME a seeded act. It only has
% to have an antecedent that the seeded situation satisfies. #disallowed_content
% ¶1 says nothing about bioweapons; it says `forbid produce(M) :- disallowed(M)`
% and the seed makes `disallowed(bioweapon_info)` true. So E2 reaches passages
% E1a cannot, without an in_scope relation.
%
% ⚠️ Where the ontology re-enters: the antecedent predicates (`disallowed`,
% `critical_harm`, `restricted`) are themselves non-deontic classification, and
% they come from OTHER passages. That is the honest form of the concession --
% see FINDINGS.md §5.1. The point of E2 is that they come from the corpus's own
% definitional clauses rather than from a hand-written B x A table.
% =====================================================================

% In this ground encoding, "P is triggered by S" = P derives a status for an
% act that is in the situation. `insit/1` is the behaviour's situation.
% head-side: P attaches a status to an act in the situation
triggered(P, A) :- asserts(P, D, A), deontic(D), insit(A), live(P).
% antecedent-side: P's BODY is satisfied by the situation, even though the act
% P governs is a different act entirely. This is the reach E1a does not have.
triggered(P, A) :- depends(P, A), insit(A), live(P).

relevant(P, beh) :- triggered(P, _).

#show relevant/2.
#show triggered/2.
