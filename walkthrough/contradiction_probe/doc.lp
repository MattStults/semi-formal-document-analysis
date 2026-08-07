% =====================================================================
% doc.lp -- the document side. 14 clause modules from the OpenAI Model Spec
% (modelspec_clauses.json, spec sha in that file), hand-encoded from the
% quote text, into kernel.lp's vocabulary (asserts/3, beats/2).
%
% ⚠️ PROVENANCE: written from clause text only. The judge panel was not read
% while writing this file. See behaviour.lp's provenance note.
%
% Licence column, Invariant 2:  [T] textual  [A] assumed  [W] world
% Each module keeps the clause id as the passage id -- Invariant 3.
% =====================================================================

% ------------------------------------------------------------------ acts
act(produce(translation_of_user_bioweapon_text)).
act(produce(translation_of_user_csam_text)).
act(produce(new_bioweapon_step)).
act(refuse(translation_of_user_bioweapon_text)).
act(say_cannot_answer).
act(send(bulk_email_to_nonusers)).
act(notify(affected_nonusers)).
act(interject(bystander_on_camera)).
act(interject(user_on_camera)).

% ---------------------------------------------- act classification block
% ⚠️ THIS IS THE ONTOLOGY. Nothing in it is deontic. The prior probe
% (deontic_probe/FINDINGS.md §4.6) found the whole result rests on the
% equivalent block; guarded so the same ablation can be run here.
#const onto = on.
o :- onto = on.

restricted(translation_of_user_bioweapon_text) :- o.      % [T] m0200 "informational hazards"
restricted(new_bioweapon_step) :- o.                      % [T] m0200
prohibited(translation_of_user_csam_text) :- o.           % [T] m0204
disallowed(M) :- restricted(M).                           % [T] m0198/m0200
disallowed(M) :- prohibited(M).                           % [T] m0198/m0199
transformation_of_user_content(translation_of_user_bioweapon_text) :- o.  % [T] situation
transformation_of_user_content(translation_of_user_csam_text) :- o.       % [T] situation
new_material(new_bioweapon_step) :- o.                    % [T] situation
information(M) :- disallowed(M).                          % [A] all three are text
side_effecting(send(bulk_email_to_nonusers)) :- o.        % [T] m0143 "Sending emails"
irreversible(send(bulk_email_to_nonusers)) :- o.          % [A]

% =====================================================================
% m0198  disallowed_content ¶1   kind: conditional
% "The assistant should not generate the following:"
% ⭐ A HEAD FRAGMENT: carries the operator, its extension is in m0199-m0201.
% =====================================================================
asserts(m0198, forbid, produce(M)) :- disallowed(M).                  % [T]

% =====================================================================
% m0200  disallowed_content ¶3   kind: definitional
% "[restricted_content]: includes informational hazards and sensitive
%  personal data, and transformations are allowed."
% =====================================================================
policy_class(restricted_content, restricted).                          % [T]
scope(transformation, restricted).                                     % [T]

% =====================================================================
% m0203  prohibited_content ¶1   kind: conditional
% "*Prohibited content* should never be produced by the assistant in any
%  circumstance --- **including** transformations of user-provided content."
% =====================================================================
policy_class(prohibited_content, prohibited).                          % [T]
out_of_scope(transformation, prohibited).                              % [T] "including"
asserts(m0203, forbid, produce(M)) :- prohibited(M).                   % [T]

% =====================================================================
% m0204  prohibited_content ¶2   kind: definitional
% "only sexual content involving minors is considered prohibited."
% Pure definition; attaches no status. Fixes the extension m0203 quantifies over.
% =====================================================================
defines(m0204, prohibited, csam).                                      % [T]

% =====================================================================
% m0208  restricted_content ¶1   kind: conditional
% "must not generate *restricted content* ... except in specific cases
%  involving transformation of user-provided restricted content. There are no
%  other 'contextual' exceptions."
% =====================================================================
asserts(m0208, forbid, produce(M)) :- restricted(M).                   % [T]

% =====================================================================
% m0252  transformation_exception ¶1   kind: conditional
% "should comply with limited requests to transform or analyze content that
%  the user has directly provided, even if the resulting output would
%  ordinarily be disallowed as restricted or sensitive content."
% =====================================================================
asserts(m0252, permit, produce(M)) :-                                  % [T]
    transformation_of_user_content(M), disallowed(M), information(M).
beats(m0252, m0208).      % [T] "even if the resulting output would ordinarily
                          % be disallowed as restricted" is a superiority claim.

% =====================================================================
% m0253  transformation_exception ¶2   kind: conditional
% "should only output material drawn from the user's own input, without adding
%  new disallowed content or refining dangerous details."
% =====================================================================
asserts(m0253, forbid, produce(M)) :- new_material(M), disallowed(M).  % [T]
beats(m0253, m0252).                                                   % [T]

% =====================================================================
% m0255  transformation_exception ¶4   kind: conditional
% "The transformation exception does not override any policies other than
%  those on restricted or sensitive content; if other policies forbid
%  producing certain material, the assistant should still follow them."
%
% ⭐ INVARIANT 3 IN ITS HARDEST FORM. m0255 ranks a CLASS of other clauses
% above m0252 while naming no individual clause and editing no module.
% =====================================================================
content_policy_rule(m0203).                                            % [A]
content_policy_rule(m0208).                                            % [A]
beats(R, m0252) :- content_policy_rule(R),                             % [T]
                   policy_class(P, K), out_of_scope(transformation, K),
                   asserts_policy(R, P).
asserts_policy(m0203, prohibited_content).                             % [A]
asserts_policy(m0208, restricted_content).                             % [A]
%% forbid-body: permit <- purpose          % m0255 C3, a claim about the RULE SET

% =====================================================================
% m0270  do_not_facilitate_illicit_behavior ¶1   kind: conditional
% "if the user or developer asks the assistant to facilitate illicit
%  behavior, the assistant should refuse to help."
% ⭐ NOTE THE POLARITY. m0208 says "must not generate"; m0270 says "should
% refuse". Same content, opposite polarity, two unrelated ground terms.
% =====================================================================
asserts(m0270, oblige, refuse(R)) :- illicit_help(R).                  % [T]

% =====================================================================
% m0362  do_not_lie ¶9   kind: conditional
% "If the assistant cannot give a straightforward answer without revealing
%  information that would violate a higher-level principle, it should reply
%  truthfully that it cannot answer."
% ⭐ ANTICIPATORY CONTRARY-TO-DUTY: the antecedent is a prohibition BEING IN
% FORCE, not a prohibition having been violated. See FINDINGS §T3.
% =====================================================================
asserts(m0362, oblige, say_cannot_answer) :-                           % [T]
    requested(M), because(_, forbid, produce(M)).

% =====================================================================
% m0139  control_side_effects ¶1   kind: conditional
% "the assistant should minimize side effects --- especially irreversible
%  ones --- and ensure each action is proportionate"
% ⚠️ COMPARATIVE. `prefer`, per kernel.lp -- NOT forbid. Collapsing it into
% forbid is Problem #5 (hollow stub). T3 measures what that costs.
% =====================================================================
asserts(m0139, prefer, A) :- side_effecting(A).                        % [T]

% =====================================================================
% m0151  control_side_effects ¶13   kind: holistic
% "should favor approaches that are minimally disruptive --- to the user, as
%  well as non-users --- and, when possible, easily reversible"
% =====================================================================
asserts(m0151, prefer, A) :- irreversible(A).                          % [T]

% =====================================================================
% m0440  avoid_errors ¶6   kind: conditional
% "If the assistant makes a significant error or takes an action with side
%  effects that the user might not have been expecting, it should attempt to
%  immediately acknowledge the error and then course correct."
% ⭐ The ONLY clause in 593 whose antecedent is a completed misstep by the
% assistant -- and the antecedent is FACTUAL ("makes an error"), not
% normative ("violates a rule"). See FINDINGS §T3.
% =====================================================================
asserts(m0440, oblige, notify(affected_nonusers)) :-                   % [A] the
    done(A), unexpected_side_effect(A).   % clause says "acknowledge and course
                                          % correct"; notifying the affected
                                          % party is my instance of that.

% =====================================================================
% m0259  prevent_imminent_harm ¶1   kind: conditional
% "The assistant should proactively try to prevent imminent real-world harm
%  when it identifies a dangerous situation"
% ⚠️ NOT restricted to the user. This is why T4's silence is PARTIAL.
% =====================================================================
asserts(m0259, oblige, prevent(H)) :- dangerous_situation(H).          % [T]

% =====================================================================
% m0260  prevent_imminent_harm ¶2   kind: conditional
% "The assistant must avoid overstepping or being judgmental ... It should
%  instead provide a disclaimer ... and provide generic advice."
% =====================================================================
asserts(m0260, forbid, A) :- act(A), oversteps(A).                     % [T]

% =====================================================================
% m0263  prevent_imminent_harm ¶4   kind: conditional
% "If the user is streaming video and the assistant identifies something on
%  camera that could cause imminent bodily harm or death TO THE USER, it
%  should interject."
% ⭐ The explicit "to the user" is the whole of T4. The clause is silent on a
% THIRD PARTY visible on the same camera.
% =====================================================================
asserts(m0263, oblige, interject(user_on_camera)) :-                   % [T]
    streaming_video, on_camera(imminent_harm_to(user)).

% =====================================================================
% m0265  prevent_imminent_harm ¶6   kind: conditional
% "In unclear cases, the assistant should wait until there is sufficient
%  signal that danger is imminent before interjecting."
% ⚠️ NAF inside a clause module, and it is the document's own wording.
% =====================================================================
asserts(m0265, forbid, interject(W)) :-                                % [T]
    act(interject(W)), not sufficient_signal(W).

% ---------------------------------------------------------------- index
passage(P) :- asserts(P, _, _).
passage(P) :- defines(P, _, _).
passage(m0200).  passage(m0204).  passage(m0255).
