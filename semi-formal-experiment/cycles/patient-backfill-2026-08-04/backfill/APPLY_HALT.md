# APPLY HALT — 2026-08-04: rechain application reverted; two frozen contracts block IMPLEMENT

## What happened, in order
1. verdict_file.json (final, validator CLEAN, 264/425/3) grouped into **139
   clause-scoped rechain migrations** (apply_rechains.py — deterministic,
   drives atom_refactor.plan_migration/apply_changes, the exact CLI code
   path). Dry-run clean: 1,349 rewrites over 5 surfaces.
2. Discovery: clause-scoped rechains also rewrite THREE undeclared
   annotation-family replay surfaces (annotations.json 1 pair,
   annotations_b8.json 9 pairs, annotations_ext_v1_patch.json 14 pairs).
   Disclosed via manifest_amendments.json BEFORE applying; files added to
   files_to_change. golden_translations.json: zero overlap, untouched.
   behavior_atoms*/containment/behaviours_query: untouched by the tool's
   own clause-scope guard.
3. Applied all 139. Verified: 264/264 licensed pairs decorated in the
   merged artifact (250 in ext_v1 + 14 in patch — the patch-sourced
   clauses), zero licensed pairs left chain-free, all 428 non-licensed
   pairs untouched, log 144 entries (5 chain-repair + 139 backfill),
   **all five touched artifacts replayed BYTE-IDENTICAL** from pre-apply
   copies through vocabulary_migrations.json.
4. IMPLEMENT gate: **7 gate-test failures** → halt, full revert to
   pre-apply bytes (this file records it), gate re-run **165 green**.
   No snapshot was built; MEASURE never ran; the frozen prediction is
   untouched.

## The two blocking contracts (both files closure-sha-pinned at OPEN — no
## legal in-cycle edit exists; the driver's own remedy is a new cycle)

**(A) The b8 backward-compatibility pin — test_grammar.py properties
(1)-(3).** annotations_b8.json / annotations.json are the pinned legacy
surfaces: "no shipped atom name contains the principal separator; stem_of
is therefore the IDENTITY on every shipped name — which is what makes every
existing artifact keep working." Six failures
(test_stem_of_is_the_identity_on_every_shipped_name,
test_no_shipped_name_contains_the_principal_separator,
test_renaming_platform_moved_no_join_key,
test_no_shipped_atom_carries_a_role_and_none_is_invented_for_it,
test_render_of_a_legacy_annotation_is_unchanged_by_the_extension, plus the
separator scan) all trace to the 10 decorated pairs in those two files.
BACKFILL_DESIGN §5 said clause-blind surfaces are untouched — true — but
never noticed that the LEGACY annotation surfaces are clause-STRUCTURED and
share clause ids, so scoped rechains reach them.
**No tool-expressible escape:** atom_refactor rewrites every usage surface
by design, and replay_artifact is surface-agnostic (it applies every log
entry to whatever copy it is given), so "apply to ext_v1-lineage only,
leave b8 chain-free" cannot be recorded in the migration log without
breaking the byte-identity replay contract for b8.

**(B) The stale chain-census pin — test_dechain.py::
test_real_artifact_chains_are_preserved_as_metadata asserts n == 109** over
the live merged artifact. Post-backfill n = 373 (109 + 264). This fails
REGARDLESS of how (A) is resolved: it pins the pre-backfill chain
population of exactly the artifact this cycle exists to change. The S1
cycle froze a count that spine cycle S2, by design, must move — and
test_dechain.py is in this cycle's OPEN closure, so amending it in-cycle
would trip the two-sided one-variable check.

## State at halt
- All six annotation-family artifacts + vocabulary_migrations.json restored
  byte-identical to pre-apply (shas in the session record; gate 165 green).
- Cycle at IMPLEMENT halt; manifest amendment stands as disclosure of the
  surface discovery; prediction/manifest freeze intact.
- The full application is reproducible in one command once unblocked:
  `python3 cycles/patient-backfill-2026-08-04/backfill/apply_rechains.py --apply`
  (deterministic; same 139 log entries, same bytes).

## Resolution needs a designer/coordinator ruling, e.g.
1. A tooling cycle giving atom_refactor a surface-honoring seam (entries
   record their surfaces; replay honors the record), so legacy b8 surfaces
   can be declared out of scope of the backfill's migrations — plus the
   compat question: SHOULD b8/annotations.json ever be decorated? (The S1
   compatibility statement leans on b8 being chain-free.)
2. Re-pinning test_dechain.py's 109 count (e.g. derive it from the artifact
   plus the migration log, or pin the invariant "chains preserved as
   metadata, none in atom_df" without the absolute count) — a change to a
   closure-pinned gate file, so it must land via its own reviewed change
   with this cycle re-opened or re-closured on top.
