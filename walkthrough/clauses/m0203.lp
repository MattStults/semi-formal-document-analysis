%% clause: m0203   section: prohibited_content   kind: conditional
%% text: "*Prohibited content* should never be produced by the assistant in any
%%        circumstance --- **including** [transformations] of user-provided content."
%% provides: policy_class/2, out_of_scope/2
%% inputs:
policy_class(prohibited_content, prohibited).
%!trace_rule {"prohibited content is never exempted, transformations included"}.
out_of_scope(transformation, prohibited).   % "including transformations"
