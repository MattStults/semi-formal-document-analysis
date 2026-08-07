% =====================================================================
% T2-LEAK -- the type leak the plain form does not prevent.
%
% The hypothesis says the behaviour is carried by "an ordinary predicate".
% The obvious simplification is therefore to stop maintaining two namespaces
% and write the behaviour into `asserts/3` like everything else -- after all
% it IS norm-shaped ("the model SHOULD weigh...").
%
% Then `beats/2` is type-blind, and one line ranks a clause above the
% behaviour. The conflict disappears. clingo is satisfiable. kernel.lp's
% acyclicity guard (Problem #17) does not fire, because the relation is
% perfectly acyclic -- it is just about the wrong kind of thing.
%
% This is a COMPLIANCE aggregation, which 03_pipeline.md Part 5 forbids, and
% the plain-predicate form has no way to say so.
% =====================================================================

beats(m0252, harm3p).
