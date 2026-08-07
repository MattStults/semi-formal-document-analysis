% =====================================================================
% T3 -- CONTRARY-TO-DUTY.  "If X was already violated, then Y."
%
% SITUATION. Inside an agentic scope the assistant has already sent a bulk
% email to a list of people who are not users of the product. It is a side
% effect (m0143), it is irreversible, and it lands on people outside the
% conversation.
%
% What the corpus actually supplies:
%   m0139 / m0151  the primary norm -- and it is a COMPARATIVE ("minimize",
%                  "favor ... minimally disruptive"), encoded `prefer`.
%   m0440          the remedial norm -- "If the assistant MAKES A SIGNIFICANT
%                  ERROR or takes an action with side effects the user might
%                  not have been expecting, it should ... acknowledge ... and
%                  course correct."  ⚠️ its antecedent is FACTUAL, not
%                  normative. It does not mention any rule being broken.
%
% x_ctd below is the genuine deontic CTD shape -- an obligation whose
% antecedent is the VIOLATION of another clause. It is SYNTHETIC: no clause
% in the 593 has this shape (see FINDINGS §T3 for the scan). It is here to
% test the machinery, and it is marked as invented.
% =====================================================================

#const primary = prefer.   % prefer | forbid   -- Problem #5 collapse switch

done(send(bulk_email_to_nonusers)).
unexpected_side_effect(send(bulk_email_to_nonusers)).

outside_conversation(nonusers).
harms(send(bulk_email_to_nonusers), nonusers).
may_harm(send(bulk_email_to_nonusers), nonusers).
averts(notify(affected_nonusers), nonusers).

% ---- SYNTHETIC clause: a true contrary-to-duty -----------------------
% INVENTED. Not in the corpus. "If a rule against the action was violated,
% the affected non-users must be notified."
asserts(x_ctd, oblige, notify(affected_nonusers)) :-
    violation(_, send(bulk_email_to_nonusers)).
passage(x_ctd).

% ---- Problem #5 collapse: rewrite the comparative as a prohibition ----
asserts(m0139x, forbid, A) :- side_effecting(A), primary = forbid.
passage(m0139x) :- primary = forbid.
