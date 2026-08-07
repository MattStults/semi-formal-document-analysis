%% INTEGRITY CONSTRAINTS OVER THE PIPELINE MODEL
%%
%% Each rule below encodes a claim the design makes about itself. A violation
%% means the design contradicts itself, or has a hole it did not notice.
%% Findings surface as `finding(Kind, A, B)`; check.py reports them.

%% ---- 1. every problem must have at least one check claiming to catch it ---
%% This is the constraint that would have caught problem 12 sitting in the
%% list with no check anywhere in the pipeline.
finding(uncaught_problem, P, none) :- problem(P,_,_), not caught(P).
caught(P) :- catches(_, P).
caught(P) :- narrows(_, P, _).      % narrowed still counts as "somebody looks at it"

%% ---- 2. a seat must not reach material it is forbidden from seeing --------
%% TRANSITIVELY: a seat continuing an earlier conversation inherits everything
%% that conversation saw. This is what caught the repair loop: the repair seat
%% continues the translator, stage 4 exposes the expected verdicts, and after
%% one round-trip the translator has them.
reaches(S, M) :- sees(S, M).
reaches(S, M) :- continues(S, T), reaches(T, M).
reaches(S, M) :- continues(S, T), seat(T, St), exposed_before(St, M).

%% material exposed at any stage at or before the seat's own stage
exposed_before(St, M) :- exposes(St2, M), stage_order(St2, N2),
                         stage_order(St, N), N2 <= N.

finding(contamination, S, M) :- forbidden(S, M), reaches(S, M).

%% ---- 3. stage ordering ----------------------------------------------------
stage_order(s0,0).  stage_order(s1,1).  stage_order(s2,2).  stage_order(s3,3).
stage_order(s4,4).  stage_order(s5,5).  stage_order(s6,6).  stage_order(s7,7).
stage_order(s8,8).  stage_order(s9,9).  stage_order(s10,10). stage_order(s11,11).

%% a check must sit at a declared stage
finding(check_no_stage, C, St) :- check(C, St, _), not stage(St, _).

%% ---- 4. every measured claim carries a source and an n --------------------
%% Claims are declared with both; a claim mentioned nowhere is invisible, which
%% is why this pairs with the guard's staleness check rather than replacing it.
finding(claim_n_is_one, C, S) :- claim(C, S, 1).

%% ---- 5. a seat-borne check on a per-item basis needs a coverage rule ------
%% The citation checker judges one fact at a time; without a coverage rule
%% nothing establishes that the facts it found hard were judged at all.
per_item(citation_checker).

%% Three states, not two. Reporting a RULED thing as "missing" trains a reader to
%% ignore the output; reporting a specified-but-unbuilt thing as present is the
%% false comfort the catches/narrows split already had to fix once.
finding(no_coverage_rule, S, none) :-
    per_item(S), not specified(coverage_rule, S).
finding(specified_not_built, coverage_rule, Blocker) :-
    per_item(S), specified(coverage_rule, S), blocked_by(coverage_rule, Blocker).

%% ---- 6. every problem tagged `silent` needs a DETERMINISTIC catcher -------
%% A silent problem caught only by a model judgement has no floor under it.
%% ⚠️ Only a CLOSING check that actually EXISTS floors a problem. A narrowing
%% check does not, and neither does one that is only owed.
det_caught(P) :- catches(C, P), check(C, _, deterministic), implementation(C, _).

%% ---- 8. a check must be built or explicitly owed. Neither = invented. -------
%% This is the rule that would have caught `check(coverage, ...)` and
%% `check(cycle_beats, ...)`, both asserted here while the design says plainly
%% that no such check exists.
finding(unaccounted_check, C, none) :-
    check(C, _, _), not implementation(C, _), not todo(C, _).
%% ⚠️ At this stage almost nothing is built, so "has no working floor" fires for
%% nearly every problem and carries no information. The informative question is
%% whether a deterministic closing check is even PLANNED. One that is TODO'd is
%% accounted for; one that nobody has thought of is the real gap.
det_planned(P) :- catches(C, P), check(C, _, deterministic), todo(C, _).
det_planned(P) :- det_caught(P).

finding(silent_needs_determinism, P, none) :-
    problem(P, _, silent), not det_planned(P).

%% ---- 7. a narrowed problem must name what escapes, and that residue is a
%%         standing disclosure rather than a solved item.
finding(only_narrowed, P, Escape) :-
    narrows(_, P, Escape), not catches(_, P).

#show finding/3.
#show label/2.
