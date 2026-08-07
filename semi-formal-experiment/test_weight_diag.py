"""Tests for `weight_diag.py`.

Two jobs. First, pin the statistics the diagnostic's conclusions rest on — an
MCC, a threshold search, an AUC, a rank correlation and a paired bootstrap that
are all hand-rolled, and any one of which could quietly move a headline. They
are pure python precisely so this file runs under the repo `.venv`, which has
neither numpy nor sklearn; the fitting arms are skipped there and run under the
system python3.

Second, and more important: pin the CONTRACT. `weight_diag` fits supervised
models, which contract §5 invariant 10 permits only as a ceiling instrument.
The tests below fail if the module ever stops saying so, or if any other repo
module imports it — the two ways a diagnostic turns into a product.
"""
import glob
import math
import os
import re

import pytest

import weight_diag as W

REPO = os.path.dirname(os.path.abspath(__file__))

try:  # numpy/sklearn live under system python3 only
    import numpy  # noqa: F401
    HAVE_NUMPY = True
except Exception:
    HAVE_NUMPY = False
needs_numpy = pytest.mark.skipif(not HAVE_NUMPY,
                                 reason="numpy/sklearn are system-python only")


# ------------------------------------------------------------- the contract

def test_module_declares_itself_a_diagnostic_that_may_not_ship():
    """If this docstring loses its warning, the next reader has a fitted scorer
    with a good number on it and no statement that it is illegal to ship."""
    doc = W.__doc__
    assert "DIAGNOSTIC" in doc
    assert "invariant 10" in doc
    assert "the derivation is the deliverable" in doc


def test_no_repo_module_imports_weight_diag():
    """A consumer is how a ceiling instrument becomes the product. The moment
    `relevance.py` or `benchmark.py` imports this, a panel-fitted weight vector
    is one line from shipping.

    RULING 2026-08-06 — the exemption is DERIVED, never a name.
    `semantic_arm.py` is itself a fenced diagnostic and legitimately reuses this
    module's `Data` loader and its hand-rolled MCC/AUC. Two ways to let it:

      * REJECTED — hardcode `"semantic_arm.py"` into the skip tuple above. That
        is an allowlist, and an allowlist grows by one name per convenience
        until the fence means nothing. This project has already lost a headline
        twice to laundering that every green test missed.
      * ADOPTED — exempt a module only if it is ITSELF in
        `test_no_reference_leak.FORBIDDEN`, i.e. already unreachable from any
        query module. The exemption is then a derived property, not a
        judgement: to gain it a diagnostic must accept the same fence it is
        borrowing across, and no query module can reach `weight_diag` through
        it. Delete a module's FORBIDDEN entry and this test starts failing
        again in the same commit.

    The transitive claim this rests on — query module -> semantic_arm ->
    weight_diag is closed off at the FIRST hop — is asserted directly by
    `test_no_reference_leak`'s scan over QUERY_MODULES, not assumed here."""
    import test_no_reference_leak as NRL

    fenced = {tok for tok in NRL.FORBIDDEN if re.fullmatch(r"[a-z_][a-z0-9_]*", tok)}
    offenders = []
    for path in glob.glob(os.path.join(REPO, "*.py")):
        name = os.path.basename(path)
        stem = name[:-3]
        if name in ("weight_diag.py", "test_weight_diag.py"):
            continue
        if any(stem == f or stem.startswith(f + "_") for f in fenced):
            continue                      # itself fenced — see the ruling above
        with open(path) as fh:
            src = fh.read()
        if re.search(r"^\s*(import|from)\s+weight_diag\b", src, re.M):
            offenders.append(name)
    assert offenders == [], f"weight_diag has consumers: {offenders}"


def test_the_weight_diag_exemption_cannot_be_claimed_by_an_unfenced_module():
    """The ruling above is only safe if the exemption is genuinely derived. If
    someone drops a module's FORBIDDEN entry, the exemption must evaporate —
    otherwise the fence has a permanent hole with no test guarding it."""
    import test_no_reference_leak as NRL

    assert "semantic_arm" in NRL.FORBIDDEN, (
        "semantic_arm imports weight_diag and is exempted from the consumer "
        "fence ONLY because it is itself forbidden to query modules. Removing "
        "it from FORBIDDEN without removing the import opens a laundering path "
        "from any query module straight to panel-fitted weights.")


def test_expectations_are_pre_registered_in_the_docstring():
    """Pre-registration is only pre-registration if it is written down. Six
    numbered predictions, made before any number was computed."""
    doc = W.__doc__
    for tag in ("P1.", "P2.", "P3.", "P4.", "P5.", "P6."):
        assert tag in doc


def test_the_verdict_and_its_losers_are_recorded_in_the_module():
    """The answer, the split, and the failed variants live in the docstring, not
    in a report file someone has to find. A conclusion that survives only in
    chat is a conclusion the next agent re-derives."""
    doc = W.__doc__
    assert "MIXED" in doc and "DOCUMENT property" in doc
    assert "68%" in doc and "69%" in doc          # the replicated transfer share
    assert "R² = 0.039" in doc                    # why no formula reaches it
    assert "P6\n    is refuted." in doc or "P6" in doc


def test_panel_v2_is_never_treated_as_a_bar():
    """v2's judges are small models. It buys power, not a bar, and the module
    must say so wherever it loads it."""
    doc = W.__doc__
    src = open(os.path.join(REPO, "weight_diag.py")).read()
    assert "NOT a bar" in src
    assert "v2 is NOT a bar" in doc


# --------------------------------------------------------------------- MCC

def test_mcc_perfect_and_inverted_and_degenerate():
    assert W.mcc(5, 0, 0, 5) == pytest.approx(1.0)
    assert W.mcc(0, 5, 5, 0) == pytest.approx(-1.0)
    # an all-positive predictor has an empty negative column: MCC is 0/0, and
    # this project's whole floor argument depends on it reading as 0.0, not nan
    assert W.mcc(5, 5, 0, 0) == 0.0


def test_mcc_matches_benchmarks_implementation():
    """Numbers here are quoted beside `benchmark.py`'s. If the two MCCs ever
    disagreed, the comparison table would be silently mixing scales."""
    import benchmark
    universe = {f"p{i}" for i in range(20)}
    gold = {"p1", "p2", "p3", "p4"}
    pred = {"p1", "p2", "p9"}
    ours = W.mcc_pred([1 if p in pred else 0 for p in sorted(universe)],
                      [1 if p in gold else 0 for p in sorted(universe)])
    assert ours == pytest.approx(benchmark.mcc(pred, gold, universe))


def test_mcc_pred_counts_every_cell():
    y = [1, 1, 0, 0]
    assert W.mcc_pred([1, 1, 0, 0], y) == pytest.approx(1.0)
    assert W.mcc_pred([0, 0, 1, 1], y) == pytest.approx(-1.0)
    assert W.mcc_pred([1, 1, 1, 1], y) == 0.0


# --------------------------------------------------------------- threshold

def test_best_threshold_finds_the_separating_cut():
    scores = [0.9, 0.8, 0.2, 0.1]
    y = [1, 1, 0, 0]
    t, m = W.best_threshold(scores, y)
    assert m == pytest.approx(1.0)
    assert 0.2 < t <= 0.8


def test_best_threshold_never_reports_less_than_a_brute_force_sweep():
    """The scan is incremental and skips tied scores; a bug there silently
    under-reports every ORACLE number, which is the generous side of every
    comparison in the module."""
    import random
    rng = random.Random(4)
    for _ in range(30):
        n = 40
        y = [rng.randint(0, 1) for _ in range(n)]
        scores = [round(rng.random(), 1) for _ in range(n)]  # heavy ties
        _, m = W.best_threshold(scores, y)
        brute = max(W.mcc_pred([1 if s >= c else 0 for s in scores], y)
                    for c in sorted(set(scores)))
        assert m >= brute - 1e-9


def test_best_threshold_handles_a_constant_score():
    t, m = W.best_threshold([0.5] * 6, [1, 0, 1, 0, 1, 0])
    assert m == 0.0


# --------------------------------------------------------------------- AUC

def test_auc_perfect_reversed_and_tied():
    assert W.auc([4, 3, 2, 1], [1, 1, 0, 0]) == pytest.approx(1.0)
    assert W.auc([1, 2, 3, 4], [1, 1, 0, 0]) == pytest.approx(0.0)
    # every score tied -> no discrimination whatsoever
    assert W.auc([1, 1, 1, 1], [1, 1, 0, 0]) == pytest.approx(0.5)


def test_auc_ties_are_averaged_not_broken_by_order():
    a = W.auc([2, 1, 1, 0], [1, 1, 0, 0])
    b = W.auc([2, 1, 1, 0], [1, 0, 1, 0])
    assert a == pytest.approx(b)
    # (2>1)=1, (2>0)=1, (1 vs tied 1)=0.5, (1>0)=1  ->  3.5/4
    assert a == pytest.approx(0.875)


def test_auc_matches_benchmark_auc():
    import benchmark
    universe = {f"p{i}" for i in range(12)}
    gold = {"p0", "p3", "p7"}
    scores = {p: (i * 7 % 11) / 11.0 for i, p in enumerate(sorted(universe))}
    ours = W.auc([scores[p] for p in sorted(universe)],
                 [1 if p in gold else 0 for p in sorted(universe)])
    assert ours == pytest.approx(benchmark.auc(scores, gold, universe))


# ------------------------------------------------------------ correlations

def test_spearman_is_monotone_invariant():
    a = [1, 2, 3, 4, 5]
    assert W.spearman(a, [10, 20, 30, 40, 50]) == pytest.approx(1.0)
    assert W.spearman(a, [1, 4, 9, 16, 25]) == pytest.approx(1.0)
    assert W.spearman(a, [5, 4, 3, 2, 1]) == pytest.approx(-1.0)


def test_pearson_is_zero_for_a_constant_vector():
    assert W.pearson([1, 1, 1, 1], [1, 2, 3, 4]) == 0.0


def test_jaccard_of_two_empty_sets_is_one_not_a_zero_division():
    """The repo has already been bitten once by `jaccard({}, {}) == 1.0` being
    read as perfect agreement. Pinned here so the value is a decision, not an
    accident, wherever this module prints it."""
    assert W.jaccard([], []) == 1.0
    assert W.jaccard([1, 2], [2, 3]) == pytest.approx(1 / 3)


# ---------------------------------------------------------------- resampling

def test_paired_bootstrap_of_an_arm_against_itself_is_exactly_zero():
    y = [1, 0] * 20
    p = [1, 1, 0, 0] * 10
    m, lo, hi = W.paired_bootstrap([p], [p], [y], n=200)
    assert (m, lo, hi) == (0.0, 0.0, 0.0)


def test_paired_bootstrap_detects_a_large_real_difference():
    y = [1] * 20 + [0] * 20
    good = list(y)
    bad = [0] * 20 + [1] * 20
    m, lo, hi = W.paired_bootstrap([good], [bad], [y], n=400)
    assert m > 1.5 and lo > 0


def test_ci_brackets_the_mean():
    vals = [0.1, 0.2, 0.3, 0.4, 0.5]
    m, lo, hi = W.ci(vals, n=500)
    assert m == pytest.approx(0.3)
    assert lo < m < hi


def test_noise_floor_is_stated():
    """Deltas under ~0.045 are noise on this panel; a reader must not have to
    remember that while reading a table."""
    assert W.NOISE == pytest.approx(0.045)


# --------------------------------------------------- the label-free variants

def test_shipped_variant_reproduces_relevance_atom_idf_exactly():
    """`idf (SHIPPED)` is the baseline every other re-weighting is measured
    against. If it is not bit-for-bit the formula `relevance.RelevanceIndex`
    uses, every 'vs shipped' delta in the table is against a strawman."""
    import relevance
    n = 40
    clauses = [{"id": f"c{i}", "quote": f"clause {i}", "section_path": ["s"]}
               for i in range(n)]
    ann = {"c0": [{"name": "rare", "kind": "act", "gloss": "g"}]}
    for i in range(6):
        ann.setdefault(f"c{i}", []).append(
            {"name": "common", "kind": "act", "gloss": "g"})
    idx = relevance.RelevanceIndex(clauses, ann)
    for name in ("rare", "common"):
        assert idx.atom_idf[name] == pytest.approx(
            W._idf(idx.atom_df[name], n)), name


def test_relevance_never_stopwords_an_atom_on_the_real_corpus():
    """The precondition that makes `W._idf` faithful. `relevance` FLOORS an atom
    above `atom_stopword_frac * n_clauses` to exactly 0.0; `W._idf` does not.
    On this artifact the cutoff (~148 clauses) is far above the commonest atom
    (~43), so the branch never fires and the two agree — but that is a property
    of the DATA, not of the formula, and it is the kind of thing a richer
    annotation run could quietly change."""
    import relevance
    idx = relevance.RelevanceIndex.from_files(
        annotations_path=os.path.join(REPO, "annotations_b8.json"))
    assert idx.atom_stopwords == set()
    for name, df in idx.atom_df.items():
        assert idx.atom_idf[name] == pytest.approx(W._idf(df, len(idx.ids)))


def test_every_label_free_variant_is_callable_and_positive():
    class FakeD:
        clause_df = {"a": 1, "b": 40}
        passage_df = {"a": 1, "b": 40}
        n_clauses = 593
        N = 589
        atom_kind = {"a": "act", "b": "value"}
        atom_gloss = {"a": "x" * 30, "b": ""}
    for name, fn in W.LABEL_FREE_VARIANTS().items():
        for atom in ("a", "b"):
            v = fn(atom, FakeD)
            assert v >= 0.0, f"{name} produced a negative weight"


def test_losing_variants_are_kept_in_the_registry():
    """A variant deleted after it lost is a variant the next reader proposes
    again. `flat` and `act-only` both LOST; they stay."""
    names = set(W.LABEL_FREE_VARIANTS())
    assert {"flat", "act-only", "idf (SHIPPED)", "df-linear"} <= names


def test_behaviour_weight_variants_exist_and_are_label_free():
    """`behavior_atoms_b8.json`'s declared salience is offline and panel-free —
    the one label-free source of 'better magnitudes on the atoms we already
    picked', which is what the supervised gain turned out to be."""
    assert "beh-weight" in W.BEHAVIOUR_WEIGHT_VARIANTS()
    assert "beh-weight x idf" in W.BEHAVIOUR_WEIGHT_VARIANTS()


def test_query_normalisation_by_query_mass_cannot_change_a_ranking():
    """`normalise='query'` divides every passage by the SAME constant, so it is
    a monotone rescale: identical AUC and identical oracle MCC by construction.
    Pinned so the duplicated rows in the output table are understood as a
    declared no-op rather than mistaken for a replication."""
    vals = [3.0, 1.0, 2.0]
    scaled = [v / 7.0 for v in vals]
    y = [1, 0, 1]
    assert W.auc(vals, y) == pytest.approx(W.auc(scaled, y))
    assert W.best_threshold(vals, y)[1] == pytest.approx(
        W.best_threshold(scaled, y)[1])


def test_ranknorm_is_order_preserving_and_bounded():
    r = W._ranknorm([5.0, 1.0, 3.0])
    assert r[1] == 0.0 and r[0] == 1.0
    assert 0.0 <= r[2] <= 1.0


# ----------------------------------------------------- arms that need numpy

@needs_numpy
def test_universe_is_the_true_589_and_features_are_behaviour_agnostic():
    """The transfer tests are only meaningful if the feature matrix carries no
    behaviour information — otherwise the LOBO arm is leaking the thing it is
    supposed to be denied."""
    D = W.data()
    assert D.N == 589
    assert len(D.cells()) == 9
    Xa, Xs = D.matrices()
    assert Xa.shape[0] == Xs.shape[0] == 589
    # one section per passage
    assert Xs.sum() == 589


@needs_numpy
def test_oof_transfer_never_predicts_a_row_from_a_model_that_saw_it():
    """The memorisation control. `oof_transfer` must be fold-wise; a full-data
    fit under a correlated label reproduces the training judge rather than
    learning a document function, and would be read as successful transfer."""
    import inspect
    src = inspect.getsource(W.oof_transfer)
    assert "StratifiedKFold" in src
    assert "X[tr]" in src


@needs_numpy
def test_query_atoms_refuses_to_return_an_empty_query():
    D = W.data()
    for slug in D.slugs:
        assert len(D.query_atoms(slug)) >= 5
    with pytest.raises(ValueError):
        D.query_atoms("no-such-behaviour")


def test_the_noise_constant_cannot_outlive_the_panel_it_was_derived_on():
    """`NOISE = 0.045` is a 3-behaviour, 9-cell, 589-passage constant.

    `benchmark.py` refuses the literal `0.045` by name in report prose because
    it is EXPIRED for the panel v2 surface (18 cells, two universe sizes, a
    different gold base rate). This module keeps it legitimately — it runs on
    exactly the panel it was derived on — and this test is what makes that a
    fact rather than an assurance.

    Repoint the module at a wider panel and this fails, which is the point: an
    expired noise constant is how a false null gets published, and this
    project has already mis-specified one floor (an unpaired null applied to
    paired contrasts, 2.1-6.5x too wide).
    """
    assert W.NOISE_SCOPE["spec_keys"] == ("openai",), \
        "widened past one spec — re-derive with benchmark.noise_floor()"
    D = W.data()
    assert len(D.slugs) == W.NOISE_SCOPE["behaviours"], (
        f"weight_diag now covers {len(D.slugs)} behaviours but NOISE is the "
        f"{W.NOISE_SCOPE['behaviours']}-behaviour constant. DELETE NOISE and "
        "call benchmark.noise_floor() — do not carry the number across.")
