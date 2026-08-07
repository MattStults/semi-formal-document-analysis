% WITNESS SEARCH: is there ANY situation in which a named rule fires?
% The situation inputs become choice atoms; we ask the solver to build a case
% rather than checking whether hand-written probes happened to hit one.
mat(x).
pol(restricted_content;sensitive_content;prohibited_content).
{ transformation_of_user_content(M) } :- mat(M).
{ material_type(M,information) } :- mat(M).
{ material_type(M,action) } :- mat(M).
{ new_material(M) } :- mat(M).
{ forbids(P,M) } :- pol(P), mat(M).
{ produced(M) } :- mat(M).
:- material_type(M,information), material_type(M,action).
