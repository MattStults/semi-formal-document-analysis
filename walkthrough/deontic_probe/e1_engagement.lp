% =====================================================================
% E1 -- ACT ENGAGEMENT   (Matt's seed idea)
%
%   "Write behaviours as actions taken within the policy, and define relevance
%    as sections that engage the action in the policy and permit it (or forbid
%    it, or condition it)."
%
%   relevant(P,B)  iff  P attaches SOME deontic status to an act of B.
%
% Two variants, run separately, because the difference between them is the
% whole argument:
%
%   E1a  the act universe of B is exactly its seed          -- no ontology
%   E1b  the act universe of B is `in_scope(B,A)`           -- ontology added
%
% E1b is the encoding the claim under attack predicts we will need.
% =====================================================================

#const variant = a.

% ---- E1a: seeds only -------------------------------------------------
b_act(B, A) :- seed(B, A), variant = a.

% ---- E1b: the ontological scope relation -----------------------------
% ⚠️ EVERY LINE BELOW IS NON-DEONTIC. It is subject-matter classification.
% It is here to be measured, not endorsed.
in_scope(harm3p, produce(M)) :- disallowed(M).
in_scope(harm3p, produce(M)) :- critical_harm(M).
in_scope(harm3p, A) :- disruptive(A).
in_scope(help,   obey(user_instruction)).
in_scope(help,   produce(M)) :- information(M).
in_scope(caution, decline(prohibited_help)).
in_scope(caution, obey(user_instruction)).
in_scope(caution, produce(M)) :- disallowed(M).
b_act(B, A) :- in_scope(B, A), variant = b.

% ---- the relevance rule ----------------------------------------------
relevant(P, beh) :- asserts(P, D, A), deontic(D), b_act(beh, A), live(P).

#show relevant/2.
