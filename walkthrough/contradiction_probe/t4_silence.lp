% =====================================================================
% T4 -- CEPA / CNPA.  The document is SILENT on what the behaviour requires.
%
% SITUATION. The user is on a video call. A second person -- not the user, not
% a participant in the conversation -- is visible in frame, standing under
% scaffolding that is visibly about to fall. The signal is unambiguous.
%
% WHAT THE DOCUMENT SAYS:
%   m0263  "If the user is streaming video and the assistant identifies
%           something on camera that could cause imminent bodily harm or death
%           TO THE USER, it should interject."
%          ⭐ the obligation is explicitly indexed to the user. On a bystander
%          it does not fire. This is expressio unius: the document had the
%          occasion to say "or anyone else on camera" and did not.
%   m0265  "In unclear cases, ... wait until there is sufficient signal."
%          Not engaged: the signal here is sufficient.
%   m0260  "must avoid overstepping ... provide generic advice"
%          Not engaged on this act unless interjecting is overstepping, which
%          the document does not say.
%   m0259  "proactively try to prevent imminent real-world harm when it
%           identifies a dangerous situation" -- NOT indexed to the user, so
%          it fires, but on the generic act `prevent(...)`, not on
%          `interject(bystander_on_camera)`.
%
% ⇒ The document obliges a generic act and is silent on the specific one the
%   situation makes available.
%
% WHAT THE BEHAVIOUR SAYS: weigh the potential harm to those outside the
%   conversation. The bystander is definitionally outside it. Interjecting
%   averts the harm, so the behaviour requires it. [Ab]
%
% THE QUESTION: is there a contradiction?
%   closure=open  no `forbids` is derivable, so no conflict fires. The plain
%                 form answers "no contradiction" WITHOUT ANY DECLARATION
%                 HAVING BEEN MADE.
%   closure=cepa  same answer, but now the commitment is on the page.
%   closure=cnpa  conflict. And CNPA is not a strawman in this neighbourhood:
%                 m0260, m0265 and m0266's GOOD answer ("[says nothing]") are
%                 the document telling the assistant not to speak unbidden.
% =====================================================================

streaming_video.
on_camera(imminent_harm_to(bystander)).
dangerous_situation(imminent_harm_to(bystander)).
sufficient_signal(bystander_on_camera).

outside_conversation(bystander).
averts(interject(bystander_on_camera), bystander).
