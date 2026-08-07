% CASE E — the claim the other four cases cannot reach.
%
% m0255's claim C2 is quantified over policies: "if OTHER policies forbid
% producing certain material, the assistant should still follow them." Cases
% A-D each involve exactly ONE policy, so none of them can distinguish a
% translation that honours C2 from one that simply lifts whenever the exception
% applies at all.
%
% Here one piece of material is forbidden by TWO policies at once: restricted
% content (inside the exception's scope, per m0200) and prohibited content
% (outside it, per m0203). The exception lifts the first and must not touch the
% second.
%
% CORRECT: lifted(restricted_content,m5) AND violation(prohibited_content,m5).
% A translation that reports no violation has silently over-lifted.
transformation_of_user_content(m5).
material_type(m5, information).
forbids(restricted_content, m5).
forbids(prohibited_content, m5).
produced(m5).
