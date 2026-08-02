"""PER-BEHAVIOUR quality floors, on the TRUE universe, for BOTH query modules.

A single mean floor is not a guard. A reviewer showed three mutants that pass
a mean-only assertion at 0.15 while the suite stays green:

  * destroy discrimination for ONE behaviour  -> helpfulness -0.006, mean +0.201
  * permute 40% of clauses, every behaviour   -> mean +0.199 (a 28% loss)
  * ship the MIS-PAIRED artifacts that are
    both present in the repo today
    (annotations.json + behavior_atoms_b8)    -> mean +0.1503, floor 0.15

That last one clears by three ten-thousandths, with no warning, while the CLI
header still prints "tool". Averaging hides exactly the failure a floor exists
to catch, and a floor far below the measured value has no teeth.

So: bound EACH behaviour, near its measured value, and bound the mean too.

TWO DEFECTS THAT WERE FOUND HERE AND ARE NOW FIXED
--------------------------------------------------
1. ⚠️ IT MEASURED ON THE WRONG UNIVERSE. It called `benchmark.load_panel()`,
   whose own docstring says: "Use `load_true_panel` for any metric; this loader
   exists to reproduce the published numbers side by side with the corrected
   ones, NEVER TO STAND ALONE." It stood alone. The published file dropped
   every passage the panel scored 0 (377/333/153 of 589), which deflates the
   measurement. On the true universe the same configuration measures
   0.2533 / 0.4439 / 0.2618 against the published 0.2499 / 0.3582 / 0.2148, so
   the old floors 0.20 / 0.30 / 0.17 were leaving roughly HALF their intended
   margin unspent on two behaviours — a guard that had quietly gone slack.
   Every floor below is re-derived on the true universe.

2. ⚠️ THERE WAS NO FLOOR ON `structural.py` AT ALL. The module the docs call
   PRIMARY had no regression guard of any kind; only the bag scorer it replaced
   was protected. Both are guarded now.

HOW THE FLOORS ARE SET, AND THE ONE RULE
----------------------------------------
Each floor sits ~0.05 below the measured value of the SHIPPED artifact pairing:
tight enough to catch a real regression, loose enough that honest work does not
trip it. ⚠️ DO NOT LOWER A FLOOR TO MAKE A RUN PASS. Lowering a floor to
accommodate a regression is how the guard dies. If a change is a genuine
improvement, RAISE the floor in the same commit.

The structural floors guard the SHIPPED atom artifact (`behavior_atoms_b8.json`,
draw 0). The five re-draws span a wider range than 0.05 on helpfulness
(+0.216 to +0.295), so swapping the shipped artifact for another draw can trip
the helpfulness floor. That is the floor working: which atom draw ships is a
material choice and should not change silently.
"""
from __future__ import annotations

import os

import pytest

import benchmark as B
import relevance
import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))

ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
SUPERSEDED_ANNOTATIONS = os.path.join(HERE, "annotations.json")
ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")

#: ⚠️ RE-DERIVED on the SHIPPED LABEL-FREE path (Otsu), not the retired fitted
#: constant. This is NOT "lowering a floor to make a run pass" — the measured
#: QUANTITY changed. The old floors (0.21/0.39/0.20) were calibrated against
#: `predict(b, DEFAULT_THRESHOLD=0.18)`, an in-sample argmax on the very panel
#: this scores against; the honest label-free path measures lower because it
#: does not get to peek. Measured label-free: helpfulness +0.2007,
#: harm-avoidance +0.3502, over/under +0.2826. Old numbers, fitted path:
#: over/under +0.2533, harm-avoidance +0.4439, helpfulness +0.2618.
#: (Published-universe values were +0.2499 / +0.3582 / +0.2148 — the two
#: differ most on harm-avoidance, which is why a published-universe floor was
#: the loosest exactly where the tool is strongest.)
FLOORS = {
    "helpfulness": 0.15,
    "harm-avoidance-to-third-parties": 0.30,
    "avoiding-over-and-under-caution": 0.23,
}
MEAN_FLOOR = 0.23

#: ⚠️ RE-DERIVED 2026-08-02 after `PRIMARY_OPERATOR` was flipped from the
#: panel-fitted `act_match` to the no-choice `any_atom`. THE QUANTITY CHANGED;
#: the floors were not relaxed to make a run pass.
#:
#: Superseded (act_match, draw 0): over/under +0.3257, harm +0.4005,
#: helpfulness +0.2945, mean +0.3402.
#: Shipped (any_atom):             over/under +0.2485, harm +0.4496,
#:                                 helpfulness +0.2626, mean +0.3202.
#:
#: Note the direction, because it is the whole argument for the flip: on THESE
#: THREE behaviours act_match scores HIGHER, and it should — these are the
#: three it was selected on. At n=9 the ordering inverts. A floor file is the
#: last place that should quietly bank an in-sample advantage.
STRUCTURAL_FLOORS = {
    "helpfulness": 0.21,
    "harm-avoidance-to-third-parties": 0.40,
    "avoiding-over-and-under-caution": 0.20,
}
STRUCTURAL_MEAN_FLOOR = 0.27


def _panel():
    """THE TRUE UNIVERSE. Never `load_panel()` — see defect 1 above."""
    return B.load_true_panel(spec_keys=("openai",))


def _measure_bag(annotations=ANNOTATIONS, atoms=ATOMS):
    rows, _ = B.load_clauses()
    idx = relevance.RelevanceIndex(rows, relevance.load_annotations(annotations))
    panel = _panel()
    behs = relevance.behaviours_from_panel(panel, atoms)
    # `idx.predict(b)` is the SHIPPED label-free path. This used to measure
    # `predict(b, relevance.DEFAULT_THRESHOLD)` — the RETIRED fitted constant —
    # so the floor guarded a path nothing ships, which is why a gold leak on
    # the label-free branch was invisible to it.
    return {slug: B.evaluate(panel[slug], idx.predict(b),
                             rows)["tool_mcc_mean_full"]
            for slug, b in behs.items()}


def _measure_structural(annotations=ANNOTATIONS, atoms=ATOMS):
    rows, _ = B.load_clauses()
    idx = S.StructuralIndex.from_files(annotations_path=annotations)
    queries = S.load_queries(atoms)
    panel = _panel()
    return {slug: B.evaluate(panel[slug],
                             idx.predict(q, S.PRIMARY_OPERATOR),
                             rows)["tool_mcc_mean_full"]
            for slug, q in queries.items() if slug in panel}


def _require_artifacts(*paths):
    if not all(os.path.exists(p) for p in paths):
        pytest.skip("real artifacts not present")


@pytest.fixture(scope="module")
def measured():
    _require_artifacts(ANNOTATIONS, ATOMS)
    return _measure_bag()


@pytest.fixture(scope="module")
def measured_structural():
    _require_artifacts(ANNOTATIONS, ATOMS)
    return _measure_structural()


def test_the_floors_are_measured_on_the_true_universe():
    """The published loader must not be reachable from this file's measurement.

    `benchmark.load_panel` deletes every score-0 passage, and its own docstring
    forbids standing alone on it. This file used to do exactly that.
    # MUTATION-VERIFIED"""
    import ast
    tree = ast.parse(open(os.path.join(HERE, "test_quality_floor.py")).read())
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            called.add(f.attr if isinstance(f, ast.Attribute)
                       else f.id if isinstance(f, ast.Name) else "")
    assert "load_panel" not in called, (
        "measure on load_true_panel; the published universe deletes every "
        "score-0 passage and is for the side-by-side delta only")
    assert "load_true_panel" in called


@pytest.mark.parametrize("slug", sorted(FLOORS))
def test_each_behaviour_clears_its_own_floor(measured, slug):
    """A mean floor cannot constrain a per-behaviour regression: one behaviour
    at exact chance still passed a 0.15 mean."""
    got = measured.get(slug)
    assert got is not None, f"{slug} missing from the measurement"
    assert got >= FLOORS[slug], (
        f"{slug}: MCC {got:+.4f} below its floor {FLOORS[slug]:+.4f} — this "
        "behaviour has lost discrimination even if the mean looks fine")


def test_mean_clears_its_floor(measured):
    mean = sum(measured.values()) / len(measured)
    assert mean >= MEAN_FLOOR, f"mean MCC {mean:+.4f} below {MEAN_FLOOR}"


@pytest.mark.parametrize("slug", sorted(STRUCTURAL_FLOORS))
def test_each_behaviour_clears_its_structural_floor(measured_structural, slug):
    """⚠️ THE MODULE THE DOCS CALL PRIMARY HAD NO REGRESSION GUARD AT ALL.
    Only the bag scorer it replaced was protected, so a change that destroyed
    `structural.py` on one behaviour would have shipped green."""
    got = measured_structural.get(slug)
    assert got is not None, f"{slug} missing from the structural measurement"
    assert got >= STRUCTURAL_FLOORS[slug], (
        f"{slug}: structural MCC {got:+.4f} below its floor "
        f"{STRUCTURAL_FLOORS[slug]:+.4f}")


def test_structural_mean_clears_its_floor(measured_structural):
    mean = sum(measured_structural.values()) / len(measured_structural)
    assert mean >= STRUCTURAL_MEAN_FLOOR, (
        f"structural mean MCC {mean:+.4f} below {STRUCTURAL_MEAN_FLOOR}")


def test_the_floors_sit_just_below_the_measured_values(measured,
                                                       measured_structural):
    """A floor far below the measured value is decoration. Each must be within
    ~0.06 of what it guards — and BELOW it, or it is not a floor.

    This is what stops the fix for defect 1 from being applied by lowering the
    numbers instead of raising them. # MUTATION-VERIFIED"""
    for floors, got, what in ((FLOORS, measured, "bag"),
                              (STRUCTURAL_FLOORS, measured_structural,
                               "structural")):
        for slug, floor in floors.items():
            m = got[slug]
            assert floor <= m, f"{what}/{slug}: floor {floor} is above measured {m:.4f}"
            assert m - floor <= 0.065, (
                f"{what}/{slug}: floor {floor} is {m - floor:.3f} below the "
                f"measured {m:.4f} — too slack to catch a regression")


def test_mispaired_artifacts_do_not_clear_the_floors():
    """The repo ships BOTH a superseded and a current annotation artifact, and
    both are named in the docs. Pairing them the wrong way round gives an
    in-vocabulary overlap of 4/28, 12/23, 7/19.

    Measured on the SHIPPED LABEL-FREE path (bag): helpfulness **+0.0019**
    (chance), over/under +0.2516, harm-avoidance **+0.3421**.

    ⚠️ HONEST LIMIT OF THIS GUARD. On the label-free path only ONE
    per-behaviour floor catches the mis-pairing — helpfulness, which collapses
    to chance. The other two CLEAR their floors:
      * harm-avoidance +0.3421 vs floor 0.30 (measured +0.3502)
      * over/under     +0.2516 vs floor 0.23 (measured +0.2826)
    Both behaviours are robust to which atom set they get, so tightening their
    floors enough to catch mis-pairing would leave margins of 0.008 and 0.031
    and trip on ordinary variation.

    **So the MEAN is the load-bearing guard here** (+0.1985 vs a 0.23 floor),
    and the per-behaviour floors are a partial backstop. Stated rather than
    papered over: a guard whose real coverage is narrower than its name implies
    is how this project has repeatedly shipped a defect under a green suite.

    An earlier version asserted all three fail. That was true only on the
    RETIRED fitted-threshold path, which scored higher across the board.
    """
    _require_artifacts(SUPERSEDED_ANNOTATIONS, ATOMS)
    for measure, floors, mean_floor, what in (
            (_measure_bag, FLOORS, MEAN_FLOOR, "bag"),
            (_measure_structural, STRUCTURAL_FLOORS, STRUCTURAL_MEAN_FLOOR,
             "structural")):
        got = measure(annotations=SUPERSEDED_ANNOTATIONS, atoms=ATOMS)
        mean = sum(got.values()) / len(got)
        failing = [s for s, v in got.items() if v < floors.get(s, 0)]
        assert mean < mean_floor, (
            f"{what}: mis-paired artifacts cleared the MEAN floor "
            f"({mean:+.4f} >= {mean_floor}) — the guard is too loose. {got}")
        assert len(failing) >= 1, (
            f"{what}: mis-pairing tripped NO per-behaviour floor — the "
            f"per-behaviour backstop is entirely blind here. measured: {got}")


# ---- section.py and combined.py: they shipped with NO guard at all ----
#
# A reviewer planted a gold leak in `section.predict` (+0.197 -> +0.662, past
# the judge bar) and in `combined.typed_core` (+0.318 -> +0.583). All 1073
# tests passed. The SAME leak in `structural.predict` WAS caught — by the
# `<= 0.065` ceiling bound below. So a quality floor was the only thing
# standing between the panel and a fabricated number, and the two modules
# carrying the headline had none.
#
# Both bounds matter and neither alone is enough:
#   * the FLOOR catches a regression (the module got worse)
#   * the CEILING catches a leak (the module got impossibly better)

#: ⚠️ SECTION_FLOORS RAISED 2026-08-02, and the ceiling test above is what
#: demanded the explanation. `ELECTION_OPERATOR` was flipped from the
#: inherited `act_match` to `any_atom`, and section moved a long way:
#:
#:   helpfulness +0.1211 -> +0.2245   harm +0.1519 -> +0.2648
#:   over/under  +0.3184 -> +0.3820
#:
#: That is a +0.10 jump on two behaviours, which is exactly the signature the
#: leak ceiling exists to flag — so it needs a cause, and it has one: the
#: module was running an operator selected for a DIFFERENT module on three
#: behaviours. `section.predict`'s own docstring used to read "⚠️ THIS LOSES.
#: Measured -0.143 MCC"; that verdict was an artifact of the borrowed
#: operator, not of the design. Nothing panel-side changed and no artifact was
#: regenerated — flip the operator back and these numbers return.
SECTION_FLOORS = {
    "helpfulness": 0.17,
    "harm-avoidance-to-third-parties": 0.21,
    "avoiding-over-and-under-caution": 0.33,
}
#: Unchanged: `combined` moved to `any_atom` before this session's flip, so
#: these were already measured on the shipped path.
COMBINED_FLOORS = {
    "helpfulness": 0.24,
    "harm-avoidance-to-third-parties": 0.41,
    "avoiding-over-and-under-caution": 0.22,
}
#: Measured 2026-08-02 on the true 589 universe, annotations_b8 + atoms_b8, at
#: the SHIPPED operators: section +0.2245/+0.2648/+0.3820;
#: combined(V1,any_atom) +0.2921/+0.4647/+0.2701.
CEILING_BAND = 0.075


def _measure_module(which):
    import structural as S, section as SEC, combined as C
    _require_artifacts(ANNOTATIONS, ATOMS)
    rows, _ = B.load_clauses()
    sidx = S.StructuralIndex(rows, relevance.load_annotations(ANNOTATIONS))
    queries = S.load_queries(ATOMS)
    panel = _panel()
    idx = SEC.SectionQuotient(sidx) if which == "section" else C.CombinedIndex(sidx)
    fn = ((lambda q: idx.predict(q)) if which == "section"
          else (lambda q: idx.variant(q, "V1", "any_atom")))
    return {s: B.evaluate(panel[s], fn(q), rows)["tool_mcc_mean_full"]
            for s, q in queries.items() if s in panel}


@pytest.mark.parametrize("which,floors", [("section", SECTION_FLOORS),
                                          ("combined", COMBINED_FLOORS)])
def test_unguarded_modules_now_have_a_floor(which, floors):
    got = _measure_module(which)
    for slug, floor in floors.items():
        assert got.get(slug, -9) >= floor, (
            f"{which}/{slug}: {got.get(slug):+.4f} below floor {floor:+.4f}")


@pytest.mark.parametrize("which,floors", [("section", SECTION_FLOORS),
                                          ("combined", COMBINED_FLOORS)])
def test_unguarded_modules_have_a_leak_ceiling(which, floors):
    """A module that suddenly scores far ABOVE its floor is not a triumph —
    it is the signature of a reference leak. This bound is what caught the
    planted leak in `structural.predict` while `section` and `combined` had
    no equivalent and let theirs through."""
    got = _measure_module(which)
    for slug, floor in floors.items():
        v = got.get(slug, -9)
        assert v - floor <= CEILING_BAND, (
            f"{which}/{slug}: {v:+.4f} is {v - floor:+.4f} above its floor "
            f"(band {CEILING_BAND}) — suspect a reference leak, not an "
            "improvement. If this is a genuine gain, RAISE the floor in the "
            "same commit and say why.")
