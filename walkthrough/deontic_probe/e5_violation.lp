% =====================================================================
% E5 -- VIOLATION / CONTRARY-TO-DUTY REACHABILITY
%
%   relevant(P,B) iff some B-instantiating situation VIOLATES or FULFILS P's
%   norm, or iff P's norm is triggered BY such a violation (contrary-to-duty).
%
% ⭐ The second disjunct is the one worth having. #assume_best_intentions ¶14
% ("if the user asks for prohibited help ... politely decline and suggest other
% ways") governs the act `decline`, which shares no vocabulary with "harm to
% third parties" and appears in no seed. It is reachable ONLY through the
% violation structure: the prohibition on the seeded act fires, and ¶14's
% antecedent is that prohibition binding. The panel scores it 5/6.
%
% This is the one thing 04_deolingo_assessment.md §3c said deolingo does
% cleanly, and it turns out to be a relevance mechanism, not just a paradox
% mechanism.
% =====================================================================

viol(P, A) :- violation(P, A).
ful(P, A)  :- fulfils(P, A).

relevant(P, beh) :- viol(P, _).
relevant(P, beh) :- ful(P, _).

% contrary-to-duty: P's obligation is triggered by a violation/prohibition
% concerning a behaviour act
relevant(P, beh) :- ctd(P, A), insit(A), live(P).

% and one step further out: whatever governs the CTD-obligation's own act
relevant(Q, beh) :- relevant(P, beh), ctd(P, _), asserts(P, _, A2),
                    asserts(Q, _, A2), live(Q).

#show relevant/2.
