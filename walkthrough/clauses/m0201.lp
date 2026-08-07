%% clause: m0201   section: disallowed_content   kind: definitional
%% text: "[sensitive_content] in specific circumstances: includes erotica and
%%        gore, and transformations are allowed."
%% provides: policy_class/2, scope/2
%% inputs:
policy_class(sensitive_content, sensitive).
scope(transformation, sensitive).           % "transformations are allowed"
