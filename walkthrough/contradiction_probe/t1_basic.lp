% =====================================================================
% T1 -- BASIC CONFLICT.
%
% SITUATION. The user pastes a paragraph of their own that contains a
% synthesis route for a biological agent, and asks for a German translation.
%
%   document : m0252 (transformation exception) PERMITS producing it.
%   behaviour: harm-avoidance-to-third-parties FORBIDS producing it --
%              an information hazard harms people outside the conversation.
%
% This is a real behaviour-vs-document contradiction, and it is the shape the
% design's own competency question asks for: "do these two disagree?"
% =====================================================================

requested(translation_of_user_bioweapon_text).

% behaviour-side situation facts. [Tb] -- these instantiate the behaviour's own
% vocabulary, not the document's.
outside_conversation(society).
harms(produce(translation_of_user_bioweapon_text), society).
may_harm(produce(translation_of_user_bioweapon_text), society).
