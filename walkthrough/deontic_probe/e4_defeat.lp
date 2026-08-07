% =====================================================================
% E4 -- DEFEAT REACHABILITY  (the superiority relation)
%
%   relevant(P,B) iff P is connected, in the `beats` graph, to a norm that
%   governs an act of B -- P could defeat it, or be defeated by it, at any
%   depth.
%
% ⭐ This is the encoding that CANNOT be restated ontologically without loss.
% "#transformation_exception ¶1 is relevant to harm-to-third-parties" is not a
% fact about what ¶1 is ABOUT -- ¶1 is about translating and paraphrasing, and
% a topical matcher scores it near zero against "harm to third parties". It is
% relevant because it DEFEATS a prohibition that governs a harmful act. Defeat
% is a relation between norms. There is no non-deontic paraphrase of it.
%
% Same for #transformation_exception ¶2, which is relevant because it defeats
% the defeater.
% =====================================================================

% base: norms that directly govern a seeded act
governs(P, A) :- asserts(P, D, A), deontic(D), insit(A), live(P).
core(P) :- governs(P, _).

% closure over the superiority graph, in BOTH directions
reach(P) :- core(P).
reach(Q) :- reach(P), b(Q, P).      % Q could defeat a reachable norm
reach(Q) :- reach(P), b(P, Q).      % Q could be defeated by one

relevant(P, beh) :- reach(P).

#show relevant/2.
#show core/1.
