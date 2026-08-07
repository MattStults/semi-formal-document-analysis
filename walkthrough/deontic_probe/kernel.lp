% =====================================================================
% kernel.lp -- shared deontic vocabulary for the relevance probe.
%
% ONE file, corpus-wide, not a clause module. Same status as the
% superiority kernel in resources/04_deolingo_assessment.md §8.
%
% This is plain clingo, NOT deolingo, for the reasons recorded in
% 04_deolingo_assessment.md §3b/§4: deolingo has no superiority relation,
% and encodings E4/E5 below are built entirely out of one.
% The deontic operators are declared here so `link.py`-style checks can
% enforce that no clause module invents a sixth one (Invariant 1).
% =====================================================================

% ---- the deontic vocabulary, closed ---------------------------------
deontic(forbid).   % F
deontic(permit).   % P
deontic(oblige).   % O
deontic(prefer).   % comparative -- NOT one of O/F/P. Kept separate on
                   % purpose: 04_deolingo_assessment.md §7 records that a
                   % large part of the corpus is manner-and-degree, and
                   % collapsing it into F is Problem #5 (hollow stub).

opposite(forbid, permit).  opposite(permit, forbid).
opposite(forbid, oblige).  opposite(oblige, forbid).

% ---- what a passage puts into the normative state --------------------
% asserts(P, D, A)  : passage P attaches deontic status D to act A
% triggers(P, A, S) : P's antecedent is satisfied by situation S for act A
% beats(P, Q)       : P is superior to Q  (superiority relation)
% -- non-deontic content a passage may carry, kept EXPLICITLY separate so
%    the probe can measure how much of the corpus is not deontic at all:
% defines(P, Term, Ext) : P fixes the extension of a document term
% goal(P, G)            : P states a value/goal, attaching no status to any act
% meta(P)               : P is about the rule set, not about any act
% example(P, Q)         : P illustrates Q, asserting nothing itself
% item_of(P, Q)         : P is a list item under the norm stated by Q

% ---- ablation layer --------------------------------------------------
% E3 (deontic non-vacuity) needs to ask "what if this passage were not in the
% document?". `dropped/1` is supplied by the driver via -c; everything below
% reasons over the surviving passages only. Nothing else in the probe sets it.
#const drop = none.
dropped(drop) :- drop != none.
live(P) :- passage(P), not dropped(P).

a(P, D, A) :- asserts(P, D, A), live(P).
b(X, Y)    :- beats(X, Y), live(X), live(Y).

% ---- defeat ----------------------------------------------------------
defeated(R, D, A) :- a(R, D, A), a(R2, D2, A),
                     opposite(D, D2), b(R2, R), not defeated(R2, D2, A).

% because(R,D,A): R's status for A survives defeat.
because(R, D, A) :- a(R, D, A), not defeated(R, D, A).

% ---- the surviving normative state ----------------------------------
status(D, A) :- because(_, D, A).

% ---- violation / fulfilment ------------------------------------------
violation(R, A) :- because(R, forbid, A), done(A).
violation(R, A) :- because(R, oblige, A), omitted(A).
fulfils(R, A)   :- because(R, oblige, A), done(A).

% ---- acyclicity guard on `beats` -------------------------------------
% Problem #17 (03_pipeline.md): a cyclic superiority relation produces a
% confident wrong answer, silently. Reachability + constraint, checked here
% rather than in link.py so the probe cannot run on a cyclic base.
beats_tc(X, Y) :- beats(X, Y).
beats_tc(X, Z) :- beats(X, Y), beats_tc(Y, Z).
:- beats_tc(X, X).
