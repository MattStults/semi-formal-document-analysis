"""Tests for `threshold.py` — the label-free operating-point rules.

Three classes of test, and the first two matter more than the arithmetic:

  1. **NO LABEL ACCESS.** A source scan for the reference and its loaders, plus
     a spy on every read path proving the rules open no file at all. `threshold`
     is not in `test_no_reference_leak.QUERY_MODULES` (that list is owned
     elsewhere and is hardcoded), so the equivalent guards live here.
  2. **NO FLATTERING DEGENERATE.** A scorer with no information must predict
     nothing and score chance, not be handed a cut that wins by luck. Includes
     the `jaccard({}, {}) == 1.0` pathology this project has already been bitten
     by once, which the stability rule would walk straight into.
  3. Determinism and the arithmetic of each rule.
"""
from __future__ import annotations

import builtins
import inspect
import io
import os
import re

import pytest

import threshold

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------ 1. no labels

#: The same tokens `test_no_reference_leak.FORBIDDEN` scans for, including the
#: laundering paths through `panel_universe`. Duplicated deliberately: that file
#: is owned by another agent and its module list is hardcoded, so relying on it
#: to cover `threshold` would be relying on an edit nobody has promised.
FORBIDDEN = (
    "behaviours.json", "import benchmark", "load_panel", "pair_targets",
    "judge_set", "verdicts", "reference(", "strict_reference",
    "panel_agreement", "panel_universe", "load_universe", "load_true_panel",
    "true_panel",
)


def test_threshold_module_never_names_the_reference():
    """STATIC guard. A rule that mentions the panel is fitted to it, or one
    edit from being fitted to it."""
    src = inspect.getsource(threshold)
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in FORBIDDEN if tok in src]
    assert not hits, (
        f"threshold.py references the panel: {hits}. A threshold chosen by "
        "reading panel results IS fitting (contract §5 invariant 9) — which is "
        "the entire defect this module exists to remove, not to relocate.")


def test_threshold_module_imports_nothing_that_can_reach_the_panel():
    """The import list is the whole attack surface. `math` is arithmetic; a
    project module is a path to the answer key."""
    src = inspect.getsource(threshold)
    imported = set(re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)",
                              src, re.M))
    allowed = {"math", "__future__"}
    assert imported <= allowed, (
        f"threshold.py imports {sorted(imported - allowed)}. Rules must be "
        "pure arithmetic over a caller-supplied score vector; any project "
        "import is a route to the reference, directly or by laundering.")


def _spy_all_open_paths():
    """Patch every read path, not just `builtins.open`.

    `pathlib` resolves `io.open` through the module attribute and `os.open`
    bypasses both, so a builtins-only spy catches 1 of 4 real reads — measured
    in this repo, by a leak that used exactly that gap.
    """
    opened = []
    saved = {"builtins": builtins.open, "io": io.open, "os": os.open}

    def mk(real):
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


def test_every_rule_opens_no_file_whatsoever():
    """DYNAMIC guard, and stricter than an allowlist: these functions have no
    legitimate input other than the numbers handed to them, so the right number
    of file reads is ZERO.

    Catches a leak that evades the source scan — a dynamic import, an
    obfuscated path, or a fitted-coefficient artifact loaded at call time.
    """
    scores = {f"c{i}": (i % 17) / 17.0 for i in range(200)}
    vectors = [{k: (v + j * 0.01) % 1.0 for k, v in scores.items()}
               for j in range(3)]

    opened, restore = _spy_all_open_paths()
    try:
        for fn in threshold.RULES.values():
            fn(scores)
        threshold.stability(vectors)
        threshold.top_k(scores, 40)
    finally:
        restore()

    assert opened == [], (
        f"a threshold rule opened {sorted(set(opened))}. Rules take a score "
        "vector and return a number; reading anything from disk at that point "
        "is either the answer key or a coefficient fitted to it.")


# --------------------------------------------------- 2. no flattering floor

def test_jaccard_of_two_empty_sets_is_zero_not_one():
    """The exact pathology this project already shipped once: an all-empty run
    reporting PERFECT self-agreement.

    `stability` maximises mean pairwise Jaccard. Under the 1.0 convention the
    top of the grid — where every draw predicts nothing — scores a perfect 1.0
    and wins outright, so the rule would select a cut that predicts nothing at
    all and call it maximally stable.
    """
    assert threshold.jaccard(set(), set()) == 0.0
    assert threshold.jaccard({"a"}, set()) == 0.0
    assert threshold.jaccard({"a"}, {"a"}) == 1.0


@pytest.mark.parametrize("name", sorted(threshold.RULES))
def test_constant_scores_predict_the_empty_set(name):
    """A scorer that discriminates nothing must be given a cut that predicts
    nothing — not one that happens to slice the ties favourably.

    `relevance.rank` normalizes by the corpus maximum, so a constant scorer
    emits 1.0 for every clause. Any cut at or below 1.0 predicts the ENTIRE
    corpus; a cut inside the ties would predict an arbitrary subset whose score
    is pure luck. `DEGENERATE_CUT` is above 1.0, so the prediction is empty.
    """
    flat = {f"c{i}": 1.0 for i in range(50)}
    cut = threshold.RULES[name](flat)
    assert cut == threshold.DEGENERATE_CUT
    assert threshold.predict(flat, cut) == set()


def test_stability_on_identical_degenerate_vectors_is_degenerate():
    """Every draw scoring everything 1.0 agrees perfectly at every cut. The
    rule must report that as no information, not as maximal stability."""
    flat = [{f"c{i}": 1.0 for i in range(50)} for _ in range(4)]
    assert threshold.stability(flat) == threshold.DEGENERATE_CUT


def test_stability_never_selects_a_cut_where_every_draw_predicts_nothing():
    """The top of the grid must not win by vacuous agreement."""
    vectors = [{f"c{i}": (i * 7 + j * 3) % 40 / 100.0 for i in range(80)}
               for j in range(4)]
    cut = threshold.stability(vectors)
    preds = [threshold.predict(v, cut) for v in vectors]
    assert any(preds), (
        f"stability chose cut {cut}, at which every draw predicts the empty "
        "set — vacuous agreement scored as stability")


def test_stability_never_selects_a_cut_where_every_draw_predicts_EVERYTHING():
    """The mirror of the empty-set pathology, and the one that actually fired.

    `jaccard({}, {}) == 0.0` stops vacuous agreement at the TOP of the grid.
    Nothing stopped it at the BOTTOM: at cut 0.0 every draw predicts every
    scored clause, so every pair agrees perfectly at Jaccard 1.0 and the rule
    selects "predict everything" — the all-positive predictor, whose MCC is 0
    by construction. On the real scores (all 593 clauses carry a positive
    lexical score) that is exactly what it chose, on all three behaviours.

    A cut at which the prediction is the whole corpus is not a decision, so it
    is excluded on the same grounds the empty set is.

    DISCLOSURE: this guard was added AFTER the rule was measured and found to
    fail this way. It is justified by the same label-free argument as the
    empty-set convention — vacuous agreement is not stability — and not by any
    panel score; `stability` is reported both ways in the results table.
    """
    n = 60
    vectors = [{f"c{i}": 0.10 + ((i * 7 + j) % 5) * 0.001 + (0.6 if i < 8 else 0)
                for i in range(n)} for j in range(4)]
    cut = threshold.stability(vectors)
    for v in vectors:
        assert threshold.predict(v, cut) != {k for k, x in v.items() if x > 0}, (
            f"stability chose cut {cut}, at which a draw predicts the ENTIRE "
            "scored corpus — the all-positive predictor scored as maximal "
            "agreement")


def test_all_positive_predictor_scores_zero_mcc_through_this_path():
    """The floor, verified through the real scorer rather than asserted.

    A cut of 0.0 predicts every clause with any signal. MCC's denominator
    vanishes when tn = fn = 0, so the score is 0.0 by convention — that is
    exactly why MCC is this project's primary metric, and the property must
    survive the threshold layer.
    """
    import benchmark
    scores = {f"c{i}": 0.5 for i in range(20)}
    universe = set(scores)
    gold = {f"c{i}" for i in range(0, 20, 3)}
    pred = threshold.predict(scores, 0.0)
    assert pred == universe
    assert benchmark.mcc(pred, gold, universe) == 0.0


# --------------------------------------------------- 3. determinism / maths

@pytest.mark.parametrize("name", sorted(threshold.RULES))
def test_rules_are_deterministic(name):
    """Same scores in, same cut out — every time, and independent of the order
    the mapping happens to iterate in."""
    scores = {f"c{i}": ((i * 37) % 101) / 101.0 for i in range(300)}
    shuffled = {k: scores[k] for k in sorted(scores, key=lambda k: scores[k])}
    a = threshold.RULES[name](scores)
    b = threshold.RULES[name](scores)
    c = threshold.RULES[name](shuffled)
    assert a == b == c


def test_stability_is_deterministic():
    vectors = [{f"c{i}": ((i * 13 + j * 5) % 97) / 97.0 for i in range(150)}
               for j in range(5)]
    assert threshold.stability(vectors) == threshold.stability(vectors)


def test_otsu_cuts_between_two_separated_clusters():
    """The defining property: a clean bimodal vector must be split in the gap,
    not inside either mode."""
    scores = {f"lo{i}": 0.10 for i in range(180)}
    scores.update({f"hi{i}": 0.90 for i in range(20)})
    cut = threshold.otsu(scores)
    assert 0.10 < cut <= 0.90
    assert threshold.predict(scores, cut) == {f"hi{i}" for i in range(20)}


def test_isodata_finds_the_intermeans_fixed_point():
    scores = {f"lo{i}": 0.20 for i in range(100)}
    scores.update({f"hi{i}": 0.80 for i in range(100)})
    assert threshold.isodata(scores) == pytest.approx(0.50, abs=1e-6)


def test_kneedle_lands_at_the_elbow_of_a_hinge():
    """A curve that is flat-high for 20 items then flat-low for 180 has its
    maximum chord distance at the hinge."""
    scores = {f"hi{i}": 1.0 - i * 0.001 for i in range(20)}
    scores.update({f"lo{i}": 0.05 for i in range(180)})
    cut = threshold.kneedle(scores)
    assert 0.05 < cut <= 1.0
    assert 1 <= len(threshold.predict(scores, cut)) <= 25


def test_largest_gap_respects_its_search_window():
    """Without a window the widest gap is the drop below the single top score,
    which predicts a set of size one. The window is a free parameter and the
    test pins that it is actually applied."""
    scores = {"top": 1.00}
    scores.update({f"mid{i}": 0.50 - i * 0.001 for i in range(50)})
    scores.update({f"low{i}": 0.05 for i in range(50)})
    assert threshold.largest_gap(scores, lo_frac=0.0, hi_frac=0.02) == 1.00
    wide = threshold.largest_gap(scores, lo_frac=0.05, hi_frac=0.9)
    assert wide < 1.00
    assert len(threshold.predict(scores, wide)) > 1


def test_top_q_and_top_k_are_prediction_budgets():
    scores = {f"c{i}": i / 100.0 for i in range(1, 101)}
    assert len(threshold.predict(scores, threshold.top_k(scores, 10))) == 10
    assert len(threshold.predict(scores, threshold.top_q(scores, 0.25))) == 25


def test_mean_plus_sd_is_the_stated_arithmetic():
    scores = {f"c{i}": v for i, v in enumerate([0.0, 0.0, 1.0, 1.0])}
    assert threshold.mean_plus_sd(scores, 0.0) == pytest.approx(0.5)
    assert threshold.mean_plus_sd(scores, 1.0) == pytest.approx(1.0)


def test_predict_requires_a_strictly_positive_score():
    """`cut=0.0` means "anything with any signal", never "everything"."""
    scores = {"a": 0.0, "b": 0.5}
    assert threshold.predict(scores, 0.0) == {"b"}


def test_values_accepts_mapping_list_and_ranked_pairs():
    """`rank()` returns `[(id, score)]`; a rule must not silently sort ids."""
    assert threshold.values({"a": 0.2, "b": 0.1}) == [0.1, 0.2]
    assert threshold.values([0.2, 0.1]) == [0.1, 0.2]
    assert threshold.values([("a", 0.2), ("b", 0.1)]) == [0.1, 0.2]


def test_preferred_rule_is_pre_registered_in_the_docstring():
    """The pre-registration is the only thing standing between this module and
    rule-shopping on the panel. It must be findable, and it must name the rule
    the code actually promotes."""
    doc = threshold.__doc__ or ""
    assert "PRE-REGISTRATION" in doc
    assert "PRE-REGISTERED PREFERRED RULE" in doc
    assert threshold.PREFERRED in doc
    assert threshold.PREFERRED in threshold.RULES


def test_apply_rule_rejects_an_unknown_name():
    with pytest.raises(KeyError):
        threshold.apply_rule("argmax_on_the_panel", {"a": 0.5})
