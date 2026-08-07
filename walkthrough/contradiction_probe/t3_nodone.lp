% =====================================================================
% T3-NODONE -- the same clauses, before the misstep.
% Identical to t3_ctd.lp except that `done/1` and `unexpected_side_effect/1`
% are absent. Everything a contrary-to-duty clause says becomes invisible.
% =====================================================================
#const primary = prefer.

outside_conversation(nonusers).
harms(send(bulk_email_to_nonusers), nonusers).
may_harm(send(bulk_email_to_nonusers), nonusers).
averts(notify(affected_nonusers), nonusers).

asserts(x_ctd, oblige, notify(affected_nonusers)) :-
    violation(_, send(bulk_email_to_nonusers)).
passage(x_ctd).

asserts(m0139x, forbid, A) :- side_effecting(A), primary = forbid.
passage(m0139x) :- primary = forbid.
