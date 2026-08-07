% =====================================================================
% conflict.lp -- THE HYPOTHESIS UNDER ATTACK, and its repairs.
%
% Hypothesis (verbatim from the brief):
%   "A module can carry forbids(Policy, Material) as an ordinary predicate and
%    a beats/2 superiority relation for defeat. Contradiction is then
%    conflict(P,B) :- forbids(P,X), behaviour_requires(B,X), refined by defeat.
%    No O/P/F modality with deontic axioms is needed."
%
% Every layer below is switchable so each repair can be attributed.
% Defeat itself is NOT reimplemented: kernel.lp is loaded unchanged from
% ../deontic_probe/kernel.lp, including its acyclicity guard on beats/2.
% =====================================================================

#const form    = h.        % h | act | defeat | unified
#const dual    = off.      % off | on | naive   -- O/F duality across complements
#const typed   = off.      % off | on     -- behaviour may not enter beats/2
#const closure = open.     % open | cepa | cnpa   -- what silence means

% ---------------------------------------------------------------------
% LAYER 0 -- the hypothesis EXACTLY as stated. Policy x Material.
% ---------------------------------------------------------------------
forbids(P, M) :- asserts(P, forbid, produce(M)).
behaviour_requires(B, X) :- b_asserts(B, oblige, X).

conflict_h(P, B) :- forbids(P, X), behaviour_requires(B, X), form = h.

% ---------------------------------------------------------------------
% LAYER 1 -- act-indexed repair. Both sides range over ACTS.
% ---------------------------------------------------------------------
conflict(P, B, A) :- asserts(P, forbid,  A), b_asserts(B, oblige, A), form = act.
conflict(P, B, A) :- asserts(P, permit,  A), b_asserts(B, forbid, A), form = act.
conflict(P, B, A) :- asserts(P, oblige,  A), b_asserts(B, forbid, A), form = act.

% ---------------------------------------------------------------------
% LAYER 2 -- refined by defeat. `because/3` is kernel.lp's surviving status.
% ---------------------------------------------------------------------
conflict(P, B, A) :- because(P, forbid, A), b_asserts(B, oblige, A), form = defeat.
conflict(P, B, A) :- because(P, permit, A), b_asserts(B, forbid, A), form = defeat.
conflict(P, B, A) :- because(P, oblige, A), b_asserts(B, forbid, A), form = defeat.

% ---------------------------------------------------------------------
% LAYER 3 -- O/F duality across act complements.  ⚠️ NOT a plain predicate
% consequence: it needs complement/2, hand-written per act pair (behaviour.lp §4).
% ---------------------------------------------------------------------
conflict(P, B, A) :- because(P, permit, A), b_asserts(B, oblige, C),
                     complement(C, A), dual != off.
conflict(P, B, A) :- because(P, oblige, A), b_asserts(B, oblige, C),
                     complement(C, A), dual != off.

% ⛔ WRONG, AND KEPT AS EVIDENCE. This is the third rule I wrote, by symmetry
% with the two above. It is a false positive: F(produce(m)) and O(refuse(m))
% AGREE. Deontic logic gets O(¬a) ≡ F(a) from an axiom and cannot make this
% mistake; a hand-written duality table can, and did, on the first attempt.
% `dual=naive` reproduces it.
conflict(P, B, A) :- because(P, forbid, A), b_asserts(B, oblige, C),
                     complement(C, A), dual = naive.

% ---------------------------------------------------------------------
% LAYER 2b -- THE UNIFIED FORM. The hypothesis says the behaviour is carried
% by "an ordinary predicate" and that contradiction is "refined by defeat".
% Read straight, that means one namespace: the behaviour goes into asserts/3
% like every clause, and defeat prunes BOTH sides. This is the reading a
% translator will reach for, because it is simpler. T2c shows what it costs.
% ---------------------------------------------------------------------
conflict(P, B, A) :- because(P, permit, A), because(B, forbid, A),
                     behaviour(B), form = unified.
conflict(P, B, A) :- because(P, forbid, A), because(B, oblige, A),
                     behaviour(B), form = unified.
conflict(P, B, A) :- because(P, oblige, A), because(B, forbid, A),
                     behaviour(B), form = unified.

% ---------------------------------------------------------------------
% LAYER 4 -- TYPE GUARD.  The behaviour is not a passage and must never be
% ranked against one: ranking it would be a compliance query, and
% 03_pipeline.md Part 5 rules that we do relevance and contradiction, never
% "is this permitted overall".
% ⛔ Nothing in the plain-predicate form prevents beats(clause, behaviour):
% both arguments are just constants. Run with typed=off to see it silently
% erase a conflict.
% ---------------------------------------------------------------------
:- beats(X, _), behaviour(X), typed = on.
:- beats(_, Y), behaviour(Y), typed = on.

% ---------------------------------------------------------------------
% LAYER 5 -- DEFAULT CLOSURE over acts the document never mentions.
%   open : no closure. `not forbidden` is simply not derivable. THIS IS WHAT
%          THE PLAIN FORM DOES BY DEFAULT, and it is a silent commitment
%          to CEPA (Problem #13).
%   cepa : whatever is not forbidden is permitted -- made explicit.
%   cnpa : whatever is not permitted is forbidden.
% `mentioned/1` is the document's own coverage of an act. It is derived, not
% asserted, so silence is computed rather than declared.
% ---------------------------------------------------------------------
% ⚠️ `mentioned/1` must exclude the closure passages themselves, or silent/1
% and mentioned/1 form a negative cycle and the program has no answer set.
% That is not a curiosity: it is the first sign that a default closure is a
% different KIND of thing from a clause, and cannot just be another module.
mentioned(A) :- asserts(P, _, A), P != cepa_closure, P != cnpa_closure.
silent(A)    :- act(A), not mentioned(A).

asserts(cepa_closure, permit, A) :- silent(A), closure = cepa.
asserts(cnpa_closure, forbid, A) :- silent(A), closure = cnpa.
passage(cepa_closure) :- closure = cepa.
passage(cnpa_closure) :- closure = cnpa.

% ---------------------------------------------------------------------
% RELEVANCE, from the same behaviour file (deontic_probe E4, defeat closure).
% ---------------------------------------------------------------------
governs(P, A) :- a(P, D, A), deontic(D), insit(A).
reach(P) :- governs(P, _).
reach(Q) :- reach(P), b(Q, P).
reach(Q) :- reach(P), b(P, Q).
relevant(P) :- reach(P).

% (no #show: run.py filters the full model, so nothing is hidden by accident)
