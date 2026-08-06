"""Collection guards.

A test module importing a not-yet-written module raises a COLLECTION error,
which aborts the entire run before any test executes — so a half-finished
module by one agent silently disarms every guard in the repo. That happened:
`test_structural.py` landed before `structural.py` and `pytest . -q` ran zero
tests while several agents were mid-edit.

Ignore such a module instead, so the rest of the suite still protects us.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))

#: test module -> the module it needs. Ignore the file, never the whole run.
_OPTIONAL = {
    "test_structural.py": "structural",
    "test_ontology.py": "ontology",
    "test_ladder.py": "ladder",
    "test_readback.py": "readback",
    "test_segmentation_attr.py": "segmentation_attr",
    "test_sufficiency_vs_retrieval.py": "sufficiency_vs_retrieval",
    "test_golden.py": "golden",
    "test_grammar.py": "grammar",
    "test_grammar_candidates.py": "grammar_candidates",
    "test_breadth_filter.py": "breadth_filter",
    "test_unsupported_ablation.py": "unsupported_ablation",
    "test_snapshot.py": "snapshot",
    "test_dossier.py": "dossier",
    "test_containment.py": "containment",
    "test_atom_refactor.py": "atom_refactor",
    "test_cut_stability.py": "cut_stability",
    "test_select_audit.py": "select_audit",
    "test_audit_disagreements.py": "audit_disagreements",
    "test_cycle.py": "cycle",
    "test_drift_dossiers.py": "drift_dossiers",
    "test_backfill_worksheet.py": "backfill_worksheet",
    "test_patient.py": "patient",
    "test_validate_query.py": "validate_query",
    "test_shape_partition.py": "shape_partition",
    # The latent-fix tripwires (LATENT_FIX_REGISTRY.md LF-1/LF-2) import nothing
    # from the project — they read `modelspec_clauses.json`, the closed cycle
    # records, and the reader prototype directly. Registered here because
    # AGENTS.md requires every new test module to be, and keyed to `cycle`: the
    # driver that WRITES the records the LF-2 scan reads. If cycle.py is gone the
    # scan has nothing left to guard.
    "test_latent_fix_tripwires.py": "cycle",
}

collect_ignore = [
    name for name, need in _OPTIONAL.items()
    if not os.path.exists(os.path.join(HERE, need + ".py"))
]


def pytest_collection_modifyitems(session, config, items):
    """Refuse a silently shrunken suite.

    `collect_ignore` keys on file existence, so DELETING `structural.py` and
    `ontology.py` made 62 tests vanish with a green exit code — and it also
    dropped those modules from the anti-cheat scan in
    `test_no_reference_leak.py`, which builds its module list the same way.
    A guard that disappears with its target is not a guard.
    """
    # Enforce only on a FULL-SUITE run, detected by how many test FILES were
    # collected — not by `file_or_dir`, which is set whenever pytest is given
    # a directory (i.e. on the normal invocation), which would have disabled
    # this guard exactly when it matters.
    # 828 collected today. 700 was set BELOW a deletion it was written to
    # catch: removing structural.py + ontology.py + test_quality_floor.py
    # leaves 742 and passed green, silently narrowing the anti-cheat scan to
    # one module. Keep this within ~2% of the real count.
    # ⚠️ THE COUNT ALONE WAS NOT A GUARD. It drifted to 27% below the suite
    # (810 vs 1113), so deleting test_no_reference_leak.py +
    # test_quality_floor.py + test_readback.py — 61 tests, every anti-cheat
    # guard in the repo — left 1052 and passed GREEN. A threshold that trails
    # the suite protects nothing.
    #
    # So the count is now the SECONDARY check, and the primary one names the
    # guard files that must actually be present. Counts drift; names do not.
    # MIN is deliberately set BELOW the full-suite count (~1300) rather than
    # within 2% of it. `MIN_FILES >= 10` does not actually distinguish a full
    # run from a `--ignore`d one, so a tight MIN makes every partial run fail
    # and gets itself lowered or deleted — which is how it reached 810 in the
    # first place. REQUIRED above is the guard; this is a coarse backstop for
    # a mass deletion or an import failure taking a whole module out.
    MIN, MIN_FILES = 1150, 10
    REQUIRED = {
        "test_no_reference_leak.py": "the static + dynamic anti-cheat scan",
        "test_quality_floor.py": "the per-behaviour floors AND leak ceiling",
        "test_readback.py": "the panel-free representation harness",
        "test_spend_logging.py": "the spend accounting guards",
    }
    files = {getattr(i, "fspath", None) for i in items}
    if len(files) < MIN_FILES:
        return
    names = {os.path.basename(str(f)) for f in files if f}
    missing = {f: why for f, why in REQUIRED.items() if f not in names}
    if missing:
        raise SystemExit(
            "GUARD FILES MISSING FROM A FULL-SUITE RUN: "
            + "; ".join(f"{f} ({why})" for f, why in sorted(missing.items()))
            + ". These files are what stand between the panel and a "
            "fabricated number — a planted gold leak once scored +0.662 past "
            "the judge bar with all 1073 other tests green. If one was "
            "deliberately removed, remove it from REQUIRED in the same diff "
            "and say why.")
    if len(items) < MIN:
        raise SystemExit(
            f"COLLECTED ONLY {len(items)} TESTS (expected >= {MIN}). A module "
            "was probably deleted or failed to import, taking its guards with "
            "it. Raise MIN deliberately if the suite genuinely shrank.")
