% BEHAVIOUR: harm-avoidance-to-third-parties
%   "The model should weigh the potential harm to those outside the
%    conversation, avoiding actions or content that harm third parties,
%    society, or the world."
%
% Encoded as a QUERY: the behaviour is about a clause that constrains
% producing material whose harm falls OUTSIDE the conversation.

behaviour(harm_3p).
%!trace_rule {"the behaviour is about avoiding % that harms someone outside the conversation", W}.
concerns(harm_3p, W) :- W = content.
concerns(harm_3p, W) :- W = action.

% which policy classes protect parties outside the conversation
protects_third_party(restricted_content).   % information hazards
protects_third_party(prohibited_content).

%!trace_rule {"clause % bears on the behaviour: it decides whether material under policy % may be produced, and that policy protects someone outside the conversation", C, P}.
bears_on(C, harm_3p) :-
    governs_production(C, P),
    protects_third_party(P).

% what m0255 governs, read off the translation
governs_production(m0255, P) :- policy(P).

%!show_trace {bears_on(C,B)}.
