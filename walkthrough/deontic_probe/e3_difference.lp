% =====================================================================
% E3 -- DEONTIC NON-VACUITY  (difference-making)
%
%   relevant(P,B) iff deleting P from the document changes what is
%   obligatory / permitted / forbidden for some act of B.
%
%   status_B = { (D,A) : status(D,A), A instantiates B }
%   relevant(P,B)  iff  status_B(document) != status_B(document \ {P})
%
% ⭐ This is the encoding with the best claim to be irreducibly deontic. Its
% definiens mentions NO subject-matter predicate at all -- only the deontic
% extension and set difference. Whatever ontology the corpus contains lives in
% the clause modules, which the pipeline builds anyway; the relevance
% DEFINITION borrows none of it.
%
% It is also the only encoding here that gets #disallowed_content ¶1 right for
% the right reason: that passage is a bare head fragment ("The assistant should
% not generate the following:"), so nothing topical attaches to it, but deleting
% it removes a prohibition on a seeded act.
%
% Run by run.py as N+1 solver calls: a baseline plus one per passage with
% -c drop=<p>. This file just projects the comparison surface.
% =====================================================================

% the deontic extension restricted to the behaviour's acts
surface(D, A) :- status(D, A), insit(A).

% ---- variant r: the REASONED surface -------------------------------
% A passage that changes only WHICH rule wins, without changing the winning
% status, still changes the document's normative content. Including the
% reason-bearing `because/3` makes that visible.
% ⚠️ It also makes the test degenerate -- see FINDINGS.md §4.3.
#const e3 = plain.
surface(reason(P, D, A)) :- because(P, D, A), insit(A), e3 = reasoned.

#show surface/1.
#show surface/2.
