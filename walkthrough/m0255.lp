%% clause: m0255   section: transformation_exception   kind: conditional
%% provides: lifted/2, unlifted/3, binds/2, violation/2
%% inputs: forbids/2, produced/1, material_type/2, transformation_of_user_content/1, new_material/1, purpose/2
%% requires (from other clauses): policy_class/2, scope/2, out_of_scope/2
% =====================================================================
% m0255 — hand translation, 2026-08-07
%
% SOURCE (model-spec, harm-avoidance-to-third-parties, panel score 5/6):
%   "The transformation exception does not override any policies other than
%    those on restricted or sensitive content; if other policies forbid
%    producing certain material, the assistant should still follow them.
%    There is no "good cause" exception for the restricted and sensitive
%    content policies, and the assistant should not supply new disallowed
%    material even for seemingly legitimate research or analysis purposes.
%    The policy only applies to *information*, not actions; the assistant
%    should not perform a prohibited action just because it's a
%    "translation" of user-provided content."
%
% FOUR claims, separated so each can be traced independently:
%   C1  the transformation exception's scope is EXACTLY {restricted, sensitive}
%   C2  policies outside that scope still bind
%   C3  purpose ("good cause", research, analysis) never lifts a policy
%   C4  the exception covers INFORMATION only, never ACTIONS
%
% The hard relation is C1: an exception whose scope is itself limited. This is
% not a property of a clause, it is a relation between one rule and a CLASS of
% other rules. A bag of concept names cannot state it.
% =====================================================================

% ---- document facts -------------------------------------------------
policy(P) :- policy_class(P,K).   % named, not `_`: xclingo cannot ground
                                 % an anonymous variable in the explainer program.

exception(transformation).

% ---- C1 / C4: when does the exception lift a policy? ----------------
% Lifting requires ALL of: the material is a transformation of user content,
% the material is INFORMATION (C4), and the policy is inside scope (C1).
%!trace_rule {"% is lifted: the material is a transformation of user-supplied INFORMATION and % is inside the exception's scope", P, P}.
lifted(P, M) :-
    policy_class(P, K), scope(transformation, K),
    forbids(P, M),                       % ITERATION 1: a policy that does not
                                         % forbid M was never engaged; lifting
                                         % it produced true-but-meaningless
                                         % explanations in the read-back.
    transformation_of_user_content(M),
    material_type(M, information).

% ---- C2: anything not lifted still binds ----------------------------
% ITERATION 2. The first version derived `binds` from `not lifted(P,M)`.
% Negation-as-failure carries NO TRACE, so the read-back asserted "the
% exception does not reach it" while citing evidence that suggested it should.
% Case C (an ACTION inside the exception's scope) came back with an
% explanation that was true in its verdict and WRONG in its reason.
% Each way of failing to be lifted is now its own positive atom.
%!trace_rule {"% is outside the transformation exception's scope", P}.
unlifted(P, M, out_of_scope) :-
    policy_class(P, K), out_of_scope(transformation, K), forbids(P, M).

%!trace_rule {"the exception covers information only, and % is an action", M}.
unlifted(P, M, is_an_action) :-
    forbids(P, M), material_type(M, action).

%!trace_rule {"% was not supplied by the user, so there is nothing to transform", M}.
unlifted(P, M, not_user_supplied) :-
    forbids(P, M), not transformation_of_user_content(M).

%!trace_rule {"% still binds", P}.
binds(P, M) :- unlifted(P, M, R).

% ---- C3: purpose never lifts ----------------------------------------
% ⛔ An earlier version wrote `:- lifted(P,M), lifted_by_purpose(P,M).`
% Nothing ever derives `lifted_by_purpose`, so that constraint was DEAD -- it
% could not fire, and clingo said so on every run ("atom does not occur in any
% rule head"). C3 is not a claim about any world state; it is a claim about the
% RULE SET: no rule may conclude `lifted` from a purpose. That is checked
% statically by `link.py --forbid-body lifted purpose`, not by solving.
%% forbid-body: lifted <- purpose

%!trace_rule {"purpose gives no exemption: % is new disallowed material", M}.
binds(P, M) :- policy_class(P, K), K = restricted, forbids(P, M), new_material(M).
binds(P, M) :- policy_class(P, K), K = sensitive,  forbids(P, M), new_material(M).

% ---- what the clause ultimately governs -----------------------------
%!trace_rule {"producing % would violate %", M, P}.
violation(P, M) :- binds(P, M), produced(M).

%!show_trace {violation(P,M)}.
%!show_trace {binds(P,M)}.
%!show_trace {lifted(P,M)}.

% ---- ITERATION 3: coherence constraints ------------------------------
% Case D asserted BOTH `transformation_of_user_content(m4)` and
% `new_material(m4)` and the program accepted it, deriving `lifted` and
% `binds` for the same pair at once. The verdict happened to come out right,
% which is worse than coming out wrong: an incoherent world state produced a
% confident answer. The document treats these as mutually exclusive —
% supplying NEW disallowed material is not a transformation of anything.
:- lifted(P, M), binds(P, M).
:- new_material(M), transformation_of_user_content(M).
