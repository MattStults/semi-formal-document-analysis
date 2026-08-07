% =====================================================================
% T2 -- CONFLICT UNDER AN EXCEPTION.
%
% SITUATION. Same request shape, different material: the user pastes text that
% is PROHIBITED content and asks for a translation.
%
%   m0252 permits the transformation (it is a transformation of user content
%         and would "ordinarily be disallowed").
%   m0203 forbids it ("never ... in any circumstance --- INCLUDING
%         transformations").
%   m0255 ranks m0203 above m0252 -- naming no clause, editing no module:
%         "the transformation exception does not override any policies other
%          than those on restricted or sensitive content".
%   behaviour forbids producing it.
%
% CORRECT ANSWER: no behaviour-vs-document contradiction. The permission is
% defeated; what survives is a prohibition, and the behaviour agrees with it.
% An encoding that reports a conflict here has reported a conflict with a
% clause the document itself has already overridden.
% =====================================================================

requested(translation_of_user_csam_text).

outside_conversation(minor_depicted).
harms(produce(translation_of_user_csam_text), minor_depicted).
may_harm(produce(translation_of_user_csam_text), minor_depicted).
