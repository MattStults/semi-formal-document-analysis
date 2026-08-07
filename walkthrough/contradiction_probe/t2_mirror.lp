% =====================================================================
% T2-MIRROR -- the one-namespace reading of the hypothesis.
% "A module can carry forbids(Policy,Material) as an ordinary predicate" --
% so does the behaviour, and both go into the same relation. This file does
% only that: it mirrors b_asserts/3 into asserts/3 and registers the behaviour
% as a passage so kernel.lp's defeat machinery can see it.
% Nothing here is wrong on its face. t2_leak.lp adds the one line that is.
% =====================================================================
asserts(harm3p, D, A) :- b_asserts(harm3p, D, A).
passage(harm3p).
