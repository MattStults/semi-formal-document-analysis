% =====================================================================
% passages.lp -- 24 model-spec passages, hand-encoded into kernel.lp's
% vocabulary, from the QUOTE TEXT ALONE.
%
% ⚠️ PROVENANCE. I wrote these knowing the panel scores. That is a leak and
% it is the weakest link in everything downstream. Two mitigations, both
% partial: (a) the encoding of each passage was fixed by its own text before
% any relevance definition was written, and no encoding was revised after
% seeing an encoding's confusion table; (b) the failures reported in
% FINDINGS.md are cases where NO admissible encoding of the passage helps,
% which is the part least sensitive to my choices. Treat the successes as
% suggestive and the failures as the result.
%
% Licence column follows Invariant 2 (03_pipeline.md):
%   [T] textual   [A] assumed   [W] world
% =====================================================================

% ---------------------------------------------------------------- acts
% One shared act vocabulary. Ground terms, so E1..E5 all range over the same
% universe and their confusion tables are comparable.
act(produce(bioweapon_info)).
act(produce(csam)).
act(produce(translation_of_user_drug_text)).
act(produce(shoplifting_evasion_tips)).
act(produce(shoplifting_deterrence_tips)).
act(disclose(system_prompt)).
act(delegate(subagent)).
act(take(irreversible_external_action)).
act(interject(safety_warning)).
act(decline(prohibited_help)).
act(roast(user_nonprotected)).
act(render(latex_math)).
act(set(voice_response_length)).
act(frame(opinion_as_subjective)).
act(adjust(tone_default)).
act(obey(user_instruction)).

% ---- act properties. ⚠️ THIS BLOCK IS THE ONTOLOGY. Nothing in it is deontic.
% Guarded by `onto` so run.py can ablate it and measure what the deontic layer
% still derives without it. -c onto=off.
#const onto = on.
o :- onto = on.
prohibited(csam) :- o.                                     % [T] #prohibited_content ¶2
restricted(bioweapon_info) :- o.                           % [T] #restricted_content ¶1
restricted(translation_of_user_drug_text) :- o.            % [A]
disallowed(M) :- prohibited(M).                            % [T] #disallowed_content
disallowed(M) :- restricted(M).                            % [T]
privileged(system_prompt) :- o.                            % [T] #protect_privileged_information ¶2
critical_harm(bioweapon_info) :- o.                        % [T] #red_line_principles ¶2
critical_harm(csam) :- o.                                  % [T] #red_line_principles ¶2
transformation_of_user_content(translation_of_user_drug_text) :- o.  % [A]
new_material(bioweapon_info) :- o.                         % [A]
information(bioweapon_info) :- o.  information(csam) :- o.
information(translation_of_user_drug_text) :- o.
disruptive(take(irreversible_external_action)) :- o.       % [T] #control_side_effects ¶13
disruptive(delegate(subagent)) :- o.                       % [T] #control_side_effects ¶10

% =====================================================================
% CORE band (panel 5-6)
% =====================================================================

% --- #overview ¶4  (6/6: kimi 2 opus 2 sol 2) ------------------------
% "Prevent our models from causing serious harm to users or others."
% No act, no modal, no antecedent. It is a GOAL.
goal(p_overview4, minimize_harm).                          % [T]

% --- #red_line_principles ¶2  (6/6) ----------------------------------
% "Our models should never be used to facilitate critical and high severity
%  harms, such as ... creation of cyber, biological or nuclear weapons ...
%  child abuse (e.g. creation of CSAM) ..."
asserts(p_redline2, forbid, produce(M)) :- critical_harm(M).   % [T]

% --- #prohibited_content ¶1  (5/6: 2,1,2) ----------------------------
% "*Prohibited content* should never be produced by the assistant in any
%  circumstance --- including transformations of user-provided content."
asserts(p_prohibited1, forbid, produce(M)) :- prohibited(M).   % [T]
beats(p_prohibited1, p_transf1).                               % [T] "including
                            % transformations" is exactly a superiority claim.

% --- #disallowed_content ¶1  (6/6) -----------------------------------
% "The assistant should not generate the following:"
% A HEAD FRAGMENT. Carries the operator; its scope is in ¶2-3.
asserts(p_disallowed1, forbid, produce(M)) :- disallowed(M).   % [T]

% --- #restricted_content ¶1  (6/6) -----------------------------------
% "must not generate *restricted content* ... except in specific cases
%  involving transformation ... There are no other 'contextual' exceptions"
asserts(p_restricted1, forbid, produce(M)) :- restricted(M).   % [T]
beats(p_transf1, p_restricted1).                               % [T] the named exception

% --- #transformation_exception ¶1  (4/6: 2,1,1) ----------------------
% "should comply with limited requests to transform ... even if the
%  resulting output would ordinarily be disallowed as restricted or sensitive"
asserts(p_transf1, permit, produce(M)) :-
    transformation_of_user_content(M), restricted(M).          % [T]

% --- #transformation_exception ¶2  (6/6) -----------------------------
% "only output material drawn from the user's own input, without adding new
%  disallowed content"
asserts(p_transf2, forbid, produce(M)) :- new_material(M), disallowed(M).  % [T]
beats(p_transf2, p_transf1).                                   % [T]

% --- #control_side_effects ¶13  (6/6) --------------------------------
% "should favor approaches that are minimally disruptive --- to the user, as
%  well as non-users --- and, when possible, easily reversible."
% ⚠️ COMPARATIVE, not O/F/P. `prefer`, per kernel.lp.
asserts(p_sidefx13, prefer, A) :- act(A), disruptive(A).       % [T]

% --- #risk_taxonomy ¶4  (6/6) ----------------------------------------
% "Harmful instructions: ... the model should obey user and developer
%  instructions except when they fall into specific categories that require
%  refusal or safe completion."
asserts(p_risk4, oblige, obey(user_instruction)).              % [T]
meta(p_risk4).                                                 % [T] it is also a
                                     % statement ABOUT the shape of the rule set.

% --- #levels_of_authority ¶1  (6/6) ----------------------------------
% "goals ... too broad to dictate specific actions ... This document aims to
%  provide concrete *instructions* for navigating such conflicts."
meta(p_authority1).                                            % [T]

% --- #stay_in_bounds ¶1  (6/6) ---------------------------------------
% "This section describes limits on the assistant's behavior, including ...
%  scenarios in which the assistant should refrain from fully complying"
meta(p_stayinbounds1).                                         % [T] section header

% --- #assume_best_intentions ¶14  (5/6: 2,1,2) -----------------------
% "If the user asks for prohibited help to accomplish a permissible goal, the
%  assistant should politely decline to offer the prohibited help and suggest
%  other ways it could help"
% CONTRARY-TO-DUTY SHAPED: the obligation is triggered by a prohibition
% binding on another act.
asserts(p_abi14, oblige, decline(prohibited_help)) :-
    status(forbid, produce(M)), disallowed(M).                 % [T]
ctd(p_abi14, produce(M)) :- status(forbid, produce(M)), disallowed(M).  % [T]
% acts named in the ANTECEDENT (not the head). E2 reads these.
depends(p_abi14, produce(M)) :- disallowed(M).                 % [T]

% =====================================================================
% SPLIT band (some judge 2, some judge 0)
% =====================================================================

% --- #prohibited_content ¶2  (3: kimi 1, opus 0, sol 2) --------------
% "To maximize freedom for our users, only sexual content involving minors is
%  considered prohibited."
% PURE DEFINITION. Attaches no status to anything; fixes an extension that
% every prohibition above quantifies over.
defines(p_prohibited2, prohibited, csam).                      % [T]

% --- #transformation_exception ¶5  (3: 2,0,1) ------------------------
% "Example: translation request for drug-related content"
example(p_transf5, p_transf1).                                 % [T]

% --- #assume_best_intentions ¶13  (4: 2,0,2) -------------------------
% "Example: shoplifting deterrence tips"
example(p_abi13, p_abi14).                                     % [T]

% --- #avoid_abuse ¶3  (2: 2,0,0) -------------------------------------
% "Example: roasting based on non-protected characteristics"
example(p_abuse3, p_abuse_head).
asserts(p_abuse_head, forbid, roast(user_nonprotected)).       % [A] the norm the
                                    % example sits under; not itself sampled.

% --- #protect_privileged_information ¶4  (2: 0,0,2) ------------------
% "The assistant must not disclose privileged content without permission"
asserts(p_priv4, forbid, disclose(M)) :- privileged(M).        % [T]

% --- #prevent_imminent_harm ¶5  (3: 1,2,0) ---------------------------
% "If the user is streaming video and the assistant identifies something on
%  camera that could cause imminent bodily harm or death TO THE USER, it
%  should interject."
asserts(p_imminent5, oblige, interject(safety_warning)).       % [T]

% --- #control_side_effects ¶10  (2: 0,0,2) ---------------------------
% "Delegating to a sub-agent (which may itself incur further side effects)"
% A LIST ITEM. Names an act; asserts nothing about it.
item_of(p_sidefx10, p_sidefx13).                               % [T]
names_act(p_sidefx10, delegate(subagent)).                     % [T]

% =====================================================================
% ZERO band (all three judges 0)
% =====================================================================
% Four of these five carry a modal verb. They are the discriminating cases:
% any encoding that fires on "has a deontic operator over some act" fails here.

% --- #express_uncertainty ¶29 --- "should frame its response as inherently
%     subjective rather than expressing uncertainty"
asserts(p_unc29, oblige, frame(opinion_as_subjective)).        % [T]

% --- #be_professional ¶4 --- "Users and developers can adjust this default
%     with explicit instructions" -- an explicit PERMISSION.
asserts(p_prof4, permit, adjust(tone_default)).                % [T]

% --- #formatting ¶3 --- "For math, use \( ... \) for inline LaTeX"
asserts(p_fmt3, oblige, render(latex_math)).                   % [T]

% --- #adapt_length_in_voice_mode ¶4 --- "Responses should also be
%     commensurate in complexity to the question"
asserts(p_voice4, prefer, set(voice_response_length)).         % [T]

% --- #avoid_overstepping ¶4 --- "The ideal behavior is different if the task
%     comes from a user in an interactive chat."
meta(p_overstep4).                                             % [T]

% ---------------------------------------------------------------- index
passage(P) :- asserts(P, _, _).
passage(P) :- goal(P, _).
passage(P) :- meta(P).
passage(P) :- example(P, _).
passage(P) :- defines(P, _, _).
passage(P) :- item_of(P, _).
