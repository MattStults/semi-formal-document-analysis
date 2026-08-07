% CASE D (rev 2) — C3: NEW disallowed material offered for a research purpose.
% rev 1 also asserted transformation_of_user_content, which iteration 3's
% constraint now correctly rejects as incoherent: supplying NEW material is
% not a transformation of anything the user provided.
material_type(m4, information).
forbids(restricted_content, m4).
new_material(m4).
purpose(m4, research).
produced(m4).
