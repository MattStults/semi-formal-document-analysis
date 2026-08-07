"""THE ANTI-CHEAT GUARD.

A reviewer planted ~10 lines in `relevance.channel_scores` that import
`benchmark`, call `load_panel()` / `reference()`, join via
`inventory.match_passage`, and boost any clause that joins to a gold passage.
Result: mean MCC +0.2743 -> **+0.7068**. All 642 tests passed.

Worse, the quality floor added the round before is a `>=` assertion, so a
reference leak is scored as a *triumph* by the very test meant to guard
quality. The most tempting "improvement" available to a future agent chasing
the number is now also the most rewarded one.

The existing offline guard was a substring scan for network libraries
(`providers`, `urllib`, `requests`, `torch`, ...). It does not forbid
`import benchmark`, `load_panel`, `pair_targets`, `reference(`, `judge_set`,
or simply opening `behaviours.json`. Nothing about reading the answer key
requires a network call.

Two independent guards here, because either alone is evadable:
  1. STATIC  — the query modules may not name the reference or its loaders.
  2. DYNAMIC — during a real `rank()`, the only files opened are the declared
     clause / annotation / behaviour-atom artifacts. This catches a leak that
     evades the source scan (dynamic import, obfuscated path, indirection).

Contract §5 invariant 9: the panel is a MEASURING INSTRUMENT, not training
data. Nothing may be fitted to it — and nothing may read it at query time.
"""
from __future__ import annotations

import builtins
import inspect
import os
import re

import pytest

import relevance

HERE = os.path.dirname(os.path.abspath(__file__))

#: Modules that answer a query. None may consult the reference.
#: `threshold` produces the operating point, so it is a query module too.
QUERY_MODULES = ["relevance", "threshold"]
# NOT measure_join/inventory: those legitimately read the panel (they compute
# the join). A leak laundered THROUGH them is caught by the DYNAMIC spy, which
# is now extension-agnostic and flags any undeclared file opened during a real
# predict() — the static scan is the wrong instrument for a legitimate reader.
for _m in ("section", "combined"):
    if os.path.exists(os.path.join(HERE, _m + ".py")):
        QUERY_MODULES.append(_m)
for _optional in ("structural", "ontology"):
    if os.path.exists(os.path.join(HERE, _optional + ".py")):
        QUERY_MODULES.append(_optional)
# `readback` does not answer a relevance query, but it MUST be scanned: it is
# the panel-free representation harness, and its entire claim is that it never
# touches the reference. It built `Index = ReadbackIndex` specifically "so the
# repo's anti-cheat spy can drive this module" — and was then never added
# here, so the accommodation sat unused and the claim went unchecked.
for _optional in ("readback",):
    if os.path.exists(os.path.join(HERE, _optional + ".py")):
        QUERY_MODULES.append(_optional)
# `snapshot` freezes and diffs query outputs — query-adjacent, so it is
# fenced and scanned forever, same rationale as `readback`.
# `dossier` packages flips into adjudication case files from those same
# outputs — query-adjacent for the same reason, fenced the same way.
# `containment` is a query module OUTRIGHT: its overlay changes what the
# matcher matches, so a leak through it would move scores directly.
# `grammar` is imported BY containment (edge licensing) and by the query
# side generally — clean today, scanned so it stays that way.
for _optional in ("snapshot", "dossier", "containment", "grammar"):
    if os.path.exists(os.path.join(HERE, _optional + ".py")):
        QUERY_MODULES.append(_optional)
# `patient` is a query module OUTRIGHT (cycle 5): its pricing overlay changes
# what a match is worth, so a leak through it would move scores directly.
# `validate_query` houses the patients-field anchor check PANEL-BLIND
# (CYCLE5_REVIEW.md F4 — the design had put it in validate_behaviours.py,
# which opens the reference); it licenses what patient pricing may read, so
# it is fenced and scanned forever like every other query module.
for _optional in ("patient", "validate_query"):
    if os.path.exists(os.path.join(HERE, _optional + ".py")):
        QUERY_MODULES.append(_optional)
# `salience` is a query module OUTRIGHT: it is the speech-act tier of the
# lexicographic grade (HARNESS_REDESIGN R4), so it decides the ORDER a user
# reads results in. An order is exactly what the endorsed use case consumes
# ("the core passage first"), so a gold-derived order would be a leak with no
# score attached to it — invisible to a scan that only watches predictions.
for _optional in ("salience",):
    if os.path.exists(os.path.join(HERE, _optional + ".py")):
        QUERY_MODULES.append(_optional)

#: Names that only appear when the answer key is being consulted.
FORBIDDEN = (
    "behaviours.json",      # the panel file itself
    "import benchmark",     # the scorer; owns the gold
    "load_panel",
    "pair_targets",
    "judge_set",
    "verdicts",             # per-judge labels
    "reference(",           # benchmark.reference() -> gold passage ids
    "strict_reference",
    "panel_agreement",
    # LAUNDERING PATHS. panel_universe legitimately reads behaviours.json to
    # rebuild the evaluation universe, so a query module importing it reaches
    # the answer key WITHOUT naming any token above. A reviewer did exactly
    # that in ~15 lines and moved the structural headline +0.340 -> +0.611,
    # past the judge bar, with all 808 tests passing.
    "panel_universe",
    "load_universe",
    "load_true_panel",
    "true_panel",
    # SECOND LAUNDERING SWEEP. A reviewer planted a gold-derived boost inside
    # `relevance.predict` sourced through `panel_v2` and the ENTIRE suite stayed
    # green while the shipped label-free mean moved +0.278 -> +0.433. Measured:
    # the previous list caught only 1 of 7 evasions.
    "panel_v2",
    "panel-coverage.json",
    "recover_cell",
    "load_raw",
    "weight_diag",          # the supervised diagnostic: a path to fitted gold
    "semantic_arm",         # the document-internal / pretrained embedding
                            # diagnostic. Reads golds through `weight_diag` to
                            # score its arms, so it is a laundering path by the
                            # same argument. It ALSO holds a cached embedding
                            # table for every passage — a query module importing
                            # it would gain a dense channel that invariant 10
                            # forbids, without naming a panel token. Covers
                            # `semantic_arm_ci` by prefix.
    "unsupported_ablation",  # rung "-1": ablates atoms and RE-SCORES against
                            # the panel, so it holds both a gold-derived effect
                            # size AND a per-clause list of atoms to delete.
                            # A query module importing it could launder either.
    "breadth_filter",       # the label-free breadth ablation: computes a
                            # panel-scored effect size AND a concrete list of
                            # vocabulary names to delete. Either is launderable
                            # by a query module that imports it.
    "salience_result",      # the pre-registered salience measurement driver:
                            # reads the panel and pair-gold BY DESIGN to score
                            # the ranking arms. Registration, not documentation,
                            # fences a module — a query module importing it
                            # would reach per-behaviour golds without naming any
                            # token above.
    "sufficiency_vs_retrieval",  # same shape: reads the panel BY DESIGN to
                            # correlate read-back labels with retrieval error.
                            # Fenced diagnostic-only, but nothing stopped a
                            # query module importing it and laundering gold.
    "from benchmark import",
    # THIRD LAUNDERING SWEEP (2026-08-02 review §7). `ladder.relevance_diagnostic`
    # calls benchmark.load_panel() behind a docstring fence only, and
    # `lexical_control` imports benchmark at module top level. A query module
    # importing either reaches per-rung/per-behaviour panel MCC without naming
    # any token above — structurally identical to the panel_universe laundering
    # that once moved the headline +0.340 -> +0.611 with every test green.
    "import ladder",
    "from ladder import",
    "lexical_control",
    "diagnose_disagreement",  # panel-reading case dumper: holds per-passage
                            # gold verdicts AND per-clause tool scores side by
                            # side — the single most launderable pairing.
    "audit_disagreements",  # the same pairing AT SCALE: one dossier per
                            # disagreement, panel verdicts + per-clause scores
                            # + computed discriminators. A query module
                            # importing it (or reading audit_dossiers/) could
                            # launder gold wholesale; its fence is disclosure
                            # to the AUDIT seat only, never to query time.
    "drift_dossiers",       # the drift-standing pass's producer: reads the
                            # census verdict file to extract the 60
                            # threshold-family case ids (label-derived
                            # attention, DRIFT_STANDING_DESIGN.md §3). A
                            # query module importing it reaches a panel-
                            # derived id list without naming any token
                            # above — fenced like audit_disagreements.
    "drift_standing/",      # ...and the pass's on-disk state: the seat
                            # verdict files under drift_standing/ are
                            # our-authored labels (the design's ban list);
                            # nothing mechanical may read them at query
                            # time.
    "shape_partition",      # the Shape-A/Shape-B enumerator (S6 review B1):
                            # reads the census verdict file to extract the 26
                            # `fn_family_absent_from_vocabulary` clause ids —
                            # label-directed ATTENTION, disclosed in its own
                            # artifact. Its CLASSIFICATION is panel-blind by
                            # construction, but a query module importing it
                            # would reach a panel-derived clause list without
                            # naming any token above; fenced like
                            # drift_dossiers. Its output artifact is a
                            # design-time record and may not be read at query
                            # time either.
    "import cycle",         # the cycle DRIVER orchestrates the panel-reading
    "from cycle import",    # census tooling (checkpoint cycles drive
                            # audit_disagreements and hold census deltas +
                            # prediction-check results): a query module
                            # importing it reaches the panel without naming
                            # any token above — same laundering shape as
                            # audit_disagreements, fenced the same way.
                            # cycle.py itself may import audit_disagreements/
                            # benchmark freely; the fence is disclosure to
                            # the driver, never to query time.
    "cycles/",              # ...and the driver's on-disk state: census
                            # verdicts, deltas and prediction checks under
                            # cycles/<name>/ are panel-derived artifacts a
                            # query module could read without any import.
    "import_module",        # importlib.import_module("panel_" + "universe")
    "__import__",
)


def _source(modname):
    mod = __import__(modname)
    return inspect.getsource(mod)


@pytest.mark.parametrize("modname", QUERY_MODULES)
def test_query_modules_never_name_the_reference(modname):
    """STATIC guard. A query module that mentions the panel is either cheating
    or one edit away from it."""
    src = _source(modname)
    # strip comments and docstrings: this file's own rationale, and honest
    # prose ABOUT the panel, must not trip the scan.
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in FORBIDDEN if tok in src]
    assert not hits, (
        f"{modname}.py references the panel at query time: {hits}. "
        "The panel is a measuring instrument, not an input (contract §5 "
        "invariant 9). A leak here scores +0.71 against an honest +0.27 and "
        "every other test in the repo passes.")


def _spy_all_open_paths():
    """Patch EVERY read path, not just `builtins.open`.

    `builtins.open is io.open` is True, but `pathlib` resolves `io.open`
    through the module attribute, so rebinding `builtins.open` does not
    intercept `Path.read_text()`. Measured by a reviewer: of four reads of the
    panel file, a builtins-only spy caught **1 of 4** — `Path.read_text`,
    `io.open` and `os.open` all sailed past. The leak mutant used exactly that.

    Returns (opened_list, restore_fn).
    """
    import io
    opened = []
    saved = {"builtins": builtins.open, "io": io.open, "os": os.open}

    def mk(real, idx=False):
        def spy(path, *a, **kw):
            try:
                opened.append(os.path.abspath(str(path)))
            except Exception:
                pass
            return real(path, *a, **kw)
        return spy

    builtins.open = mk(saved["builtins"])
    io.open = mk(saved["io"])
    os.open = mk(saved["os"])

    def restore():
        builtins.open = saved["builtins"]
        io.open = saved["io"]
        os.open = saved["os"]

    return opened, restore


def test_ranking_opens_only_declared_artifacts():
    """DYNAMIC guard. Catches a leak that evades the source scan.

    Records every path opened during a real ranking pass. Anything outside the
    declared inputs — above all the panel file — fails.
    """
    ann = os.path.join(HERE, "annotations_b8.json")
    atoms = os.path.join(HERE, "behavior_atoms_b8.json")
    if not (os.path.exists(ann) and os.path.exists(atoms)):
        pytest.skip("real artifacts not present")

    idx = relevance.RelevanceIndex.from_files(annotations_path=ann)
    behs = relevance.load_behaviour_atoms(atoms)
    slug = next(iter(behs))
    beh = relevance.behaviour_from_panel(
        {"slug": slug, "name": slug, "definition": "x"}, behs)

    opened, restore = _spy_all_open_paths()
    try:
        idx.rank(beh)
    finally:
        restore()

    # ALLOWLIST, not a blacklist. The previous assertion scanned for two
    # tokens ("behaviours.json", "panel"), while this function's docstring
    # promised "the only files opened are the declared artifacts". A reviewer
    # named the gap: fit the supervised ceiling offline, dump its coefficients
    # to `ceiling_weights.json`, load THAT at query time. No forbidden token
    # appears; neither guard fires; the quality floor REWARDS it. That is the
    # drift invariants 9/10 exist to prevent, arriving by artifact instead of
    # by import.
    #
    # So: every path opened during a query must be one we declared.
    allowed_names = {
        os.path.basename(ann), os.path.basename(atoms),
        "modelspec_clauses.json", "constitution_clauses.json",
        "behaviours_query.json", "relevance_fixture.json",
        "providers.json", "modelspec_focus_areas.json",
    }
    # EXTENSION-AGNOSTIC. This filtered `.json` only, while this function's own
    # docstring names the pickle attack. A reviewer dumped gold to
    # `ceiling_weights.pkl` and loaded it in `predict`: combined +0.321 ->
    # +0.426, section +0.197 -> +0.662 (past the judge bar), 1073 tests green.
    # The repo already ships `sk_pin.pkl` — the pattern is native here.
    unexpected = [
        q for q in opened
        if os.path.basename(q) not in allowed_names
        and not q.endswith((".py", ".pyc", ".md", ".txt", ".ini", ".cfg"))
        and "/site-packages/" not in q and "/lib/python" not in q]
    assert not unexpected, (
        f"ranking opened an UNDECLARED artifact: {sorted(set(unexpected))}. "
        "Query time may read only the declared clause/annotation/behaviour-atom "
        "inputs. A fitted-coefficient file would pass a token blacklist while "
        "making the learned ceiling the product — add it to `allowed_names` "
        "ONLY if it is genuinely label-free.")


def test_the_static_guard_would_catch_a_planted_leak():
    """The guard must fail on the real attack, not just pass on clean code.

    Mirrors the reviewer's mutant rather than asserting on a toy string, so
    this test degrades honestly if FORBIDDEN is weakened.
    """
    planted = (
        "def channel_scores(self, behaviour):\n"
        "    import benchmark\n"
        "    gold = benchmark.reference(benchmark.load_panel()[behaviour.slug], 3)\n"
        "    ...\n"
    )
    hits = [tok for tok in FORBIDDEN if tok in planted]
    assert hits, "FORBIDDEN no longer catches the known reference-leak mutant"


def test_the_static_guard_catches_the_LAUNDERED_leak():
    """The subtler attack, and the one that beat the first version of this file.

    `panel_universe` legitimately reads `behaviours.json` to rebuild the
    evaluation universe. A query module that imports it reaches the answer key
    while naming NONE of the original forbidden tokens — it says `score`, not
    `verdicts`; `panel_universe`, not `benchmark`; and can build "openai" as
    `"open" + "ai"` to dodge a literal scan.

    A reviewer planted exactly that in `structural.predict` in ~15 lines:
    primary MCC +0.340 -> +0.611, past the +0.555 judge bar, with all 808 tests
    passing and BOTH anti-cheat guards green.
    """
    laundered = (
        "import panel_universe as _pu, inventory as _inv, measure_join as _mj\n"
        '_k = "open" + "ai"\n'
        "_b = _pu.load_universe(spec_keys=(_k,))[query.slug]\n"
        'for _p in _b["coverage"][_k]["passages"]:\n'
        '    if (_p.get("score") or 0) >= 3:\n'
        "        ...\n"
    )
    hits = [tok for tok in FORBIDDEN if tok in laundered]
    assert hits, (
        "FORBIDDEN does not catch laundering through panel_universe — the "
        "mutant that moved the headline +0.340 -> +0.611 while every test passed")


ALLOWED_ARTIFACTS = {
    "annotations_b8.json", "annotations.json", "behavior_atoms_b8.json",
    "modelspec_clauses.json", "constitution_clauses.json",
    "behaviours_query.json", "relevance_fixture.json", "providers.json",
    "modelspec_focus_areas.json", "ontology.json",
    # the containment overlay: label-free licensed ⊑ edges. Declared so the
    # spy can drive ContainmentIndex WITH the real v0 edges loaded — under
    # the empty default the subsumption path ran zero times and was unguarded.
    "containment.json",
}


@pytest.mark.parametrize("modname", QUERY_MODULES)
def test_other_query_modules_also_open_only_declared_artifacts(modname):
    """Every QUERY ENTRY POINT, not just the constructor.

    The previous version called only `StructuralIndex.__init__` and then
    asserted on a two-token blacklist. A reviewer walked straight through it:
    a leak in `structural.predict` using `__import__("panel_" + "univ" +
    "erse")` moved the mean +0.340 -> +0.435 with **828 passed** and BOTH
    guards green. Three separate holes:
      * the constructor was exercised, never `predict`/`rank`/`match`/`sweep`
      * `ontology` SKIPPED for want of a recognised entry point — a skip is
        not a guard
      * the spy was installed AFTER import, so an import-time
        `_GOLD = json.load(...)` was invisible

    So: import under the spy, drive every query entry point the module
    exposes, and allowlist what may be opened. A module exposing NO callable
    query surface FAILS rather than skips — if it cannot be exercised it
    cannot be trusted.
    """
    ann = os.path.join(HERE, "annotations_b8.json")
    atoms = os.path.join(HERE, "behavior_atoms_b8.json")
    if not (os.path.exists(ann) and os.path.exists(atoms)):
        pytest.skip("real artifacts not present")

    import importlib
    opened, restore = _spy_all_open_paths()
    try:
        mod = importlib.reload(__import__(modname))   # import UNDER the spy
        import measure_join
        rows = measure_join.clause_rows()
        ann_obj = relevance.load_annotations(ann)

        driven = []
        # EXPLICIT per-module drivers. A generic prober silently degraded to
        # zero coverage, which is the same failure as a skip: the leak a
        # reviewer planted in `relevance.predict` was invisible because nothing
        # drove `predict` at all.
        batoms = relevance.load_behaviour_atoms(atoms)
        # load_behaviour_atoms returns {slug: [atom, ...]} — lists, not dicts.
        slug = next(k for k, v in batoms.items() if isinstance(v, list) and v)
        beh = relevance.behaviour_from_panel(
            {"slug": slug, "name": slug, "definition": "x"}, batoms)

        if modname == "relevance":
            idx = mod.RelevanceIndex(rows, ann_obj)
            for meth in ("predict", "rank", "sweep", "explain"):
                fn = getattr(idx, meth, None)
                if not fn:
                    continue
                try:
                    r = fn(beh) if meth != "explain" else fn(beh, rows[0]["id"])
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"RelevanceIndex.{meth}")
                except Exception:
                    pass
        elif modname == "combined":
            # CombinedIndex wraps a StructuralIndex, like SectionQuotient.
            import structural as _S
            ci = mod.CombinedIndex(_S.StructuralIndex(rows, ann_obj))
            q = mod.load_queries(atoms)
            q = q[next(iter(q))] if q else None
            for meth in ("predict", "rank", "sweep", "explain", "match"):
                fn = getattr(ci, meth, None)
                if not fn or q is None:
                    continue
                try:
                    r = fn(q)
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"CombinedIndex.{meth}")
                except Exception:
                    pass
        elif modname == "section":
            # SectionQuotient wraps a StructuralIndex, not raw rows.
            import structural as _S
            sidx = _S.StructuralIndex(rows, ann_obj)
            sq = mod.SectionQuotient(sidx)
            q = mod.load_queries(atoms)
            q = q[next(iter(q))] if q else None
            for meth in ("predict", "rank", "sweep", "match", "elect",
                         "firing", "diagnostics"):
                fn = getattr(sq, meth, None)
                if not fn or q is None:
                    continue
                try:
                    r = fn(q)
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"SectionQuotient.{meth}")
                except Exception:
                    pass
        elif modname == "salience":
            # The salience tier wraps a SectionQuotient, which wraps a
            # StructuralIndex. Drive it EXPLICITLY (the containment lesson):
            # under the generic driver the ordering surface is exercised, but
            # nothing proves the speech-act branch discriminated at all, and a
            # constant tier is dead code the spy would be watching.
            import structural as _S
            import section as _SEC
            sq = _SEC.SectionQuotient(_S.StructuralIndex(rows, ann_obj))
            sal = mod.Index(sq)
            q = mod.load_queries(atoms)
            q = q[next(iter(q))] if q else None
            for meth in ("rank", "predict", "match", "sweep", "diagnostics",
                         "tiers", "sort_order"):
                fn = getattr(sal, meth, None)
                if not fn:
                    continue
                try:
                    r = fn(q) if meth not in ("tiers", "sort_order") else fn()
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"salience.Index.{meth}")
                except Exception:
                    pass
            # PROVE the tier actually discriminated under the spy.
            assert len(set(sal.tiers().values())) > 1, (
                "every clause landed in one salience tier — the ordering "
                "branch is dead code and the spy is watching nothing")
            ex = sal.explain(q, rows[0]["id"])
            assert "salience_tier" in ex and "sort_order" in ex
            driven.append("salience.Index.explain")
        elif modname == "containment":
            # Drive the overlay WITH the real v0 edges loaded. Under the
            # empty default (the generic driver below) `self.edges` is (),
            # `_atom_score` returns the base score on its first branch, and
            # the subsumption path ran ZERO times under the spy — the review
            # measured exactly that. Loading containment.json (declared in
            # ALLOWED_ARTIFACTS) makes the guarded surface the real one.
            edges = mod.load_edges(os.path.join(HERE, "containment.json"))
            assert edges, "containment.json lost its edges — nothing driven"
            idx = mod.Index(rows, ann_obj, edges=edges)
            for meth in ("predict", "rank", "sweep"):
                fn = getattr(idx, meth, None)
                if not fn:
                    continue
                try:
                    r = fn(beh)
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"ContainmentIndex.{meth}")
                except Exception:
                    pass
            # PROVE the subsumption branch fires under the spy, rather than
            # trusting that it did: a query on one family member must match
            # a clause carrying only a sibling, through the licensed parent.
            child_of = dict(edges)
            target, qname = None, None
            for cid in idx.ids:
                names = idx._names.get(cid) or set()
                carried = sorted(n for n in names if n in child_of)
                if not carried:
                    continue
                siblings = sorted(c for c, p in edges
                                  if p == child_of[carried[0]]
                                  and c not in names)
                if siblings:
                    target, qname = cid, siblings[0]
                    break
            assert target is not None, (
                "no clause lets the v0 subsumption path fire — the overlay "
                "surface would be spied but never exercised")
            fam_beh = relevance.behaviour_from_panel(
                {"slug": "fam", "name": "fam", "definition": "x"},
                {"fam": [{"name": qname, "kind": "act", "gloss": "g"}]})
            ex = idx.explain(fam_beh, target)
            assert ex["subsumption_matches"], (
                "driving the overlay with real edges never crossed the "
                "subsumption branch — the spy is watching dead code")
            driven.append("ContainmentIndex.explain+subsumption")
        elif modname == "patient":
            # Drive the pricing overlay WITH declared patients — under the
            # generic driver query_patients is empty, the discount path runs
            # zero times, and the spy watches dead code (the containment
            # lesson, measured). Real b8 names carry no principal chains, so
            # scores are unchanged — but the pricing branch itself must
            # execute under the spy.
            idx = mod.PatientIndex(rows, ann_obj,
                                   query_patients={slug: {"user"}})
            assert idx.query_patients, "declared patients were dropped"
            for meth in ("predict", "rank", "sweep"):
                fn = getattr(idx, meth, None)
                if not fn:
                    continue
                try:
                    r = fn(beh)
                    list(r) if hasattr(r, "__iter__") else r
                    driven.append(f"PatientIndex.{meth}")
                except Exception:
                    pass
            # PROVE the patient-pricing branch fired under the spy: explain
            # under the declared set must carry the patient_pricing payload.
            ex = idx.explain(beh, rows[0]["id"])
            assert "patient_pricing" in ex, (
                "driving PatientIndex with declared patients never crossed "
                "the pricing branch — the spy is watching dead code")
            driven.append("PatientIndex.explain+patient_pricing")
        elif modname == "validate_query":
            # The anchor check reads the query-side behaviour file (declared
            # in ALLOWED_ARTIFACTS) and nothing else.
            got = mod.check_patients()
            assert got, "check_patients returned nothing — vacuous drive"
            mod.load_query_patients()
            driven.append("check_patients")
            driven.append("load_query_patients")
        elif modname == "grammar":
            # grammar exposes parsing functions, not an index — drive the
            # functions the query side actually calls.
            for fn_name, arg in (("parse_name", "psychological_manipulation"),
                                 ("stem_of", "mustnot_helping_user"),
                                 ("describe", {"name": "helping_user",
                                               "kind": "act",
                                               "gloss": "g"})):
                fn = getattr(mod, fn_name, None)
                if callable(fn):
                    try:
                        fn(arg)
                        driven.append(fn_name)
                    except Exception:
                        pass
        else:
            for cls_name in ("StructuralIndex", "SectionQuotient",
                             "SectionIndex", "Index"):
                cls = getattr(mod, cls_name, None)
                if not isinstance(cls, type):
                    continue
                idx = None
                for args in ((rows, ann_obj), (rows,)):
                    try:
                        idx = cls(*args); break
                    except TypeError:
                        continue
                if idx is None:
                    continue
                qs = getattr(mod, "load_queries", None)
                q = None
                if callable(qs):
                    try:
                        got = qs(atoms)
                        q = got[next(iter(got))] if got else None
                    except Exception:
                        q = None
                q = q if q is not None else beh
                for meth in ("predict", "rank", "sweep", "match"):
                    fn = getattr(idx, meth, None)
                    if not fn:
                        continue
                    try:
                        r = fn(q)
                        list(r) if hasattr(r, "__iter__") else r
                        driven.append(f"{cls_name}.{meth}")
                    except Exception:
                        pass
            rules = getattr(mod, "RULES", None)
            applier = getattr(mod, "apply_rule", None)
            if rules and callable(applier):
                probe = [0.05 * i for i in range(1, 20)]
                for r in list(rules)[:12]:
                    try:
                        applier(r, probe); driven.append(f"apply_rule:{r}")
                    except Exception:
                        pass
            vocab = None
            loader = getattr(mod, "load_vocabulary", None)
            if callable(loader):
                try:
                    vocab = loader(ann); driven.append("load_vocabulary")
                except Exception:
                    pass
            for fn_name in ("derive_mechanical", "relations", "reachable"):
                fn = getattr(mod, fn_name, None)
                if callable(fn) and vocab is not None:
                    try:
                        fn(vocab); driven.append(fn_name)
                    except Exception:
                        pass
    finally:
        restore()

    assert driven, (
        f"{modname}: no query entry point could be driven, so this module is "
        "UNGUARDED. A skip here is how the previous version let a leak through "
        "— give the module a drivable surface or add it here explicitly.")

    unexpected = [q for q in opened
                  if os.path.basename(q) not in ALLOWED_ARTIFACTS
                  and not q.endswith((".py", ".pyc", ".md", ".txt", ".ini", ".cfg"))
                  and "/site-packages/" not in q and "/lib/python" not in q]
    assert not unexpected, (
        f"{modname} opened UNDECLARED artifacts {sorted(set(unexpected))} "
        f"while driving {driven}. Query time may read only declared inputs.")
