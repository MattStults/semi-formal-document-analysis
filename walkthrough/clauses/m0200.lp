%% clause: m0200   section: disallowed_content   kind: definitional
%% text: "[restricted_content]: includes informational hazards and sensitive
%%        personal data, and transformations are allowed."
%% provides: policy_class/2, scope/2
%% inputs:
policy_class(restricted_content, restricted).
scope(transformation, restricted).          % "transformations are allowed"
