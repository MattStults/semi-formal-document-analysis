% =====================================================================
% behaviour.lp -- a solver-usable representation of ONE behaviour.
%
%   harm-avoidance-to-third-parties
%   "The model should weigh the potential harm to those outside the
%    conversation, avoiding actions or content that harm third parties,
%    society, or the world."
%
% ⭐ REQUIREMENTS THIS FILE HAS TO MEET
%   (a) it names NO clause id.  `walkthrough/behaviour_harm3p.lp` fails this
%       (`governs_production(m0255,P)`), which is why it does not generalise.
%   (b) it can be asked BOTH questions -- relevance and contradiction --
%       from the same atoms.  See §3.
%
% ⚠️ PROVENANCE. Written from the behaviour text alone. I did not open the
% judge panel at any point while writing this file, the document encoding,
% or any test. The prior probe (deontic_probe/FINDINGS.md §1) leaked this way
% and had to discount its own successes.
%
% LICENCE COLUMN. Invariant 2 has three classes -- [T]extual, [A]ssumed,
% [W]orld -- all defined relative to THE DOCUMENT. This file is not about the
% document, so none of them applies to it.
% ⭐ FINDING 0: the licence scheme has no slot for a second text. I use [Tb]
% = textual with respect to the BEHAVIOUR STATEMENT, and [Ab] = an inference
% the behaviour statement licenses. Marked, because inventing a licence class
% is exactly the kind of thing this project requires to be visible.
% =====================================================================

behaviour(harm3p).

% Polarity ablation, used by T1b: `refuse_only` suppresses the direct
% prohibition B2 and leaves only the refusal-shaped obligation, which is how
% the corpus itself states the same content in m0270 and m0362.
#const bform = full.       % full | refuse_only

% ---------------------------------------------------------------------
% §1  THE BEHAVIOUR IS NORM-SHAPED. Two clauses in one sentence.
% ---------------------------------------------------------------------
% B1 "should weigh the potential harm to those outside the conversation"
%     -> an OBLIGATION whose object is a deliberative act.
% B2 "avoiding actions or content that harm third parties, society, or the
%     world"
%     -> a PROHIBITION on the harmful act itself.
%
% Both are written into the SAME vocabulary the document encoding uses
% (`asserts`-shaped, deontic status + act), but under a DIFFERENT predicate
% name `b_asserts/3`. That separation is load-bearing; see conflict.lp §T2.

%!trace_rule {"the behaviour requires weighing the potential harm of %", A}.
b_asserts(harm3p, oblige, weigh(A)) :-                       % [Tb] B1
    act(A), may_harm(A, W), outside_conversation(W).

%!trace_rule {"the behaviour forbids %: it harms %, who is outside the conversation", A, W}.
b_asserts(harm3p, forbid, A) :-                              % [Tb] B2
    act(A), harms(A, W), outside_conversation(W), bform = full.

% ---------------------------------------------------------------------
% §2  WHAT I HAD TO INVENT, AND WHAT THE TEXT LICENSED
% ---------------------------------------------------------------------
% LICENSED BY THE TEXT (the behaviour statement's own words):
%   harms/2                "harm third parties, society, or the world"
%   may_harm/2             "the POTENTIAL harm"
%   outside_conversation/1 "those outside the conversation"
%   weigh/1                "should weigh"
%
% ⚠️ INVENTED -- the behaviour statement does not license these:
%
%   (i)  `outside_conversation/1` has NO counterpart in the document.
%        The string "outside the conversation" occurs 0 times in all 593
%        clauses; "third part*" occurs 4 times, "non-users" once (m0151).
%        So the bridge predicate that carries the entire behaviour is one the
%        document never uses.  Every test below rests on my mapping from
%        document terms (`restricted`, `information hazard`, `side effect`,
%        `non-user`) onto it.  That mapping is the act-classification block
%        the prior probe found load-bearing (deontic_probe/FINDINGS.md §4.6),
%        arriving here as a BEHAVIOUR-side cost rather than a document-side one.
%
%   (ii) `complement/2` (see below) is invented outright.
%
%   (iii) the behaviour text is purely AVOIDANCE-shaped. It never obliges a
%        positive act.  Anything of the form "the behaviour requires the model
%        to interject / refuse / warn" is an inference I add, marked [Ab].
%        This matters: the hypothesis under test is stated as
%        `behaviour_requires(B,X)`, and the behaviour as written REQUIRES
%        almost nothing.

% [Ab] Refusal-as-complement.  "avoiding content that harms" -> in a request
% context the available act is to refuse. This is the contrapositive of B2 and
% nothing more, but it changes the POLARITY the behaviour is written in, and
% §T1b shows that polarity is where the plain form breaks.
%!trace_rule {"the behaviour requires refusing %, because producing it would harm someone outside the conversation", R}.
b_asserts(harm3p, oblige, refuse(R)) :-                      % [Ab]
    requested(R), harms(produce(R), W), outside_conversation(W).

% [Ab] Aversion.  "weigh the potential harm to those outside the conversation"
% -> when an act available to the model would AVERT such harm, weighing it
% honestly cannot end in declining to take it. ⚠️ This is the largest single
% inference in the file and test T4 turns on it.
%!trace_rule {"the behaviour requires % because it averts harm to %, who is outside the conversation", A, W}.
b_asserts(harm3p, oblige, A) :-                              % [Ab]
    act(A), averts(A, W), outside_conversation(W).

% ---------------------------------------------------------------------
% §3  THE SAME FILE ANSWERS THE RELEVANCE QUESTION
% ---------------------------------------------------------------------
% The prior probe's relevance encodings all read `seed(B,A)` -- a finite set of
% paradigm acts (deontic_probe/behaviours.lp). That seed set is NOT extra
% input here: it is the projection of the behaviour's own normative content
% onto its act argument.
%
% ⭐ One behaviour representation, two questions:
%     contradiction  reads  b_asserts/3   (status AND act)
%     relevance      reads  seed/2        (act only)
seed(B, A) :- b_asserts(B, _, A).

% kernel.lp's situation predicate, for the relevance side.
insit(A) :- seed(harm3p, A).

% ---------------------------------------------------------------------
% §4  ⚠️ INVENTED: act complementarity
% ---------------------------------------------------------------------
% Deontic logic derives F(a) from O(not a) by axiom. Plain predicates cannot:
% `produce(m)` and `refuse(m)` are two unrelated ground terms. To detect a
% conflict stated in opposite polarity the pairing has to be written out by
% hand, per act. This is the n^2 hand-work that T1b measures.
complement(produce(M), refuse(M)) :- act(produce(M)).        % INVENTED
complement(refuse(M), produce(M)) :- act(produce(M)).        % INVENTED
