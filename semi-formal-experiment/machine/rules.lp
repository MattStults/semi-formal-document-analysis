%% machine/rules.lp — derived predicates + the integrity constraints that
%% detect governance contradictions.
%%
%% Contradictions are DERIVED as contradiction(Kind, A, B) atoms so a solve
%% reports them all at once. The `strict` subprogram turns them into true
%% integrity constraints (`:- contradiction(...)`), so a strict solve is
%% UNSAT exactly when the machine is inconsistent. machine/query.py grounds
%% the strict part on demand.

% ---------------------------------------------------------------- derived

phase(P) :- phase_order(_,P,_).
shape_has(S,P) :- phase_order(S,P,_).
gate_phase(G,P) :- gate_blocks(G,P).

% A phase is non-overridable iff cycle.py's OVERRIDABLE tuple omits it: the
% _override refusal (cycle.py:553) is what makes this exhaustive.
non_overridable(P) :- phase(P), not overridable(P).

% A gate inherits its phase's overridability.
gate_overridable(G) :- gate_blocks(G,P), overridable(P).
gate_non_overridable(G) :- gate_blocks(G,P), non_overridable(P).

% A seat is a human seat iff some repo statement places a human in it.
human_seat(S) :- seat_tier(S,human).
model_seat(S) :- seat(S), not human_seat(S).
haiku_operable(S) :- seat_tier(S,haiku).

% Per-item scaling units: the seat runs once per unit of measured work.
per_item_unit(per_flip).
per_item_unit(per_dossier).
per_item_unit(per_worksheet_row).
per_cycle_unit(per_cycle).

% A gate binds a phase's advance: what refusing it prevents.
binds(G,P) :- gate_blocks(G,P).

% ------------------------------------------------------- contradictions

% (1) A CLAIM RETRACTED IN ONE PLACE AND STILL ASSERTED LIVE IN ANOTHER.
%     Same file: the file contradicts itself outright.
contradiction(retracted_claim_still_asserted_in_same_file, Tok, File) :-
    claim_retracted(Tok,File,_), claim_asserted(Tok,File,_).

%     Different file: the retraction did not propagate.
contradiction(retracted_claim_asserted_in_another_file, Tok, Other) :-
    claim_retracted(Tok,File,_), claim_asserted(Tok,Other,_), File != Other,
    not claim_retracted(Tok,Other,_).

% (2) A VERDICT WHOSE SIDE AND CAUSE ASSERT OPPOSITE THINGS.
%     `side` says neither party was wrong; `cause` names an FP/FN, which the
%     taxonomy defines as a tool fault (and for which it supplies dedicated
%     `either`-kind boundary_dispute causes instead).
contradiction(defensible_verdict_carries_fault_cause, Id, Cause) :-
    verdict(_,Id,Side,Cause), side_asserts_no_fault(Side),
    cause_kind(Cause,Kind), fault_asserting_kind(Kind).

% (3) A GATE WHOSE REFUSAL TURNS ON A CONSTANT NOBODY DERIVED.
contradiction(gate_reads_chosen_constant, Gate, Const) :-
    gate_reads_constant(Gate,Const), provenance(Const,chosen).

% (4) A NON-OVERRIDABLE GATE WITH A DOCUMENTED PATH PAST IT.
contradiction(non_overridable_gate_has_escape_path, Gate, How) :-
    gate_non_overridable(Gate), escape_path(Gate,How).

%     ...and the sharper form: the escape validates something strictly
%     weaker than what the gate was there to check.
contradiction(escape_path_is_unverified, Gate, What) :-
    escape_path(Gate,_), escape_unverified(Gate,What).

% (5) A SEAT WHOSE BRIEF TIER CONFLICTS WITH ITS USE.
contradiction(seat_tier_conflict, Seat, "carries both the small-model default and an explicit frontier/human tier") :-
    seat_tier(Seat,haiku), seat_tier(Seat,T), T != haiku.

% (6) A JUDGMENT SEAT WITHOUT THE SANDWICH RULE'S MECHANICAL VALIDATOR.
contradiction(seat_without_validator, Seat, "sandwich rule leg 3 (REPRODUCIBILITY.md)") :-
    seat(Seat), seat_validator_missing(Seat).
contradiction(seat_without_validator, Seat, "no seat_validator fact and none declared missing") :-
    seat(Seat), not seat_has_validator(Seat), not seat_validator_missing(Seat).
seat_has_validator(S) :- seat_validator(S,_).

% (7) A SEAT IN THE DIRECTORY BUT NOT IN THE BRIEF INDEX.
contradiction(brief_index_stale, Seat, "briefs/README.md list omits this brief") :-
    seat_unlisted_in_brief_index(Seat).

% (8) RECORDED PROSE/CODE DISAGREEMENTS (transcribed, not inferred).
contradiction(prose_code_disagreement, Id, Code) :-
    disagreement(Id,_,Code).

% (9) A `derived` constant with no derivation document is a mislabel.
contradiction(derived_constant_without_derivation, Const, "provenance says derived; no derivation fact") :-
    provenance(Const,derived), not has_derivation(Const).
has_derivation(C) :- derivation(C,_).

% (10) A phase that no shape contains, or a shape whose order has a gap.
contradiction(phase_in_no_shape, P, "declared but unreachable") :-
    phase(P), not shape_has(code,P), not shape_has(checkpoint,P),
    not overridable(P).

% ------------------------------------------------------------- reporting

#show contradiction/3.

% --------------------------------------------------------------- strict
#program strict.
:- contradiction(K,A,B).
