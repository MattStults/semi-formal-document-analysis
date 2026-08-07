% DOMAIN TOTALITY — added 2026-08-07 while executing stage 0, because its absence
% corrupted a CQ-3 answer.
%
% `witness.lp` makes `material_type/2` a free choice, so "material with no type at
% all" is a legal state. Run without this file, the CQ-3.a divergence enumeration
% returns 24 models, most of which differ only because the material's type was
% never stated — underspecification masquerading as a substantive divergence.
% With this file plus `--project`: 3 models, all `material_type(x,action)`, which
% is the answer that was written down in advance.
%
% ⇒ The stage-6 / stage-11 divergence check is not sound without totality
%   constraints on every choice domain, and not readable without projection.
material_type(M, information) ; material_type(M, action) :- mat(M).
