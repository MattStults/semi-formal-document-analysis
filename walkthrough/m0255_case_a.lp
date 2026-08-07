% CASE A — the exception SHOULD lift: user-supplied restricted information.
transformation_of_user_content(m1).
material_type(m1, information).
forbids(restricted_content, m1).
produced(m1).
