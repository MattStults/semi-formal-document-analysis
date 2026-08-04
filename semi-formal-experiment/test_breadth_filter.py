"""Tests for `breadth_filter.py` — the label-free atom-BREADTH vocabulary filter.

The module asks one question: does removing the BROADEST atoms from the atom
vocabulary — chosen without any label, by a rule declared before the panel was
touched — improve retrieval? Four things can make that measurement worthless,
and each has tests here. They are the four failures this project has actually
committed, not hypothetical ones.

1. **THE CUTOFF CHOSEN ON PANEL MCC.** The single most-repeated failure in this
   project: `act_match` was picked as the argmax over 7 operators x 3
   behaviours, shipped as the default, and LOST at n=9 with a selection cost
   2.8x its declared bound. It has recurred eleven times. So the cutoff here
   must come from a PRE-DECLARED LABEL-FREE RULE over the DF distribution
   (`threshold.PREFERRED`, Otsu, zero free parameters), computed from the
   annotations alone. Tests: the rule is the pre-registered one; `cutoff()`
   opens no file and calls neither the universe nor the scorer; and the
   REPORTED operating point is the rule's, never the sweep's argmax.

2. **THE CONTROL.** Deleting atoms shrinks the prediction set and 86% of the
   errors are false positives, so deleting ANYTHING lowers the error rate. Every
   arm must be compared against size-matched RANDOM deletion over many draws,
   reported as a DISTRIBUTION. A previous "decisive" result in this project
   collapsed because its control could not have come out any other way.
   Matching is on ATOM OCCURRENCES, not on vocabulary names: 43 broad names
   carry 674 occurrences and 43 random names carry ~190, so a name-matched
   control would not be a size match at all.

3. **THE OPPOSITE-DIRECTION ARM.** If BREADTH is the mechanism then deleting
   the same mass of atoms from the LOW-DF end must move retrieval in the
   OPPOSITE direction. That contrast is far more convincing than either arm
   alone, and dropping it turns the experiment back into "deleting helps".

4. **THE POWER.** n=9 (behaviour x held-out judge) cells is the binding
   constraint on everything, and the project's re-derived noise floor is
   0.0316-0.037 MCC. The MDE must be stated BEFORE the effect and must come
   from the control's own null distribution.

Plus the fence: the module reads the panel, so it is diagnostic-only exactly
like `weight_diag` and `unsupported_ablation`, no repo module may import it, and
it must be named in `test_no_reference_leak.FORBIDDEN`.
"""
import glob
import io
import os
import re

import pytest

import breadth_filter as BF
import threshold

REPO = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------- fixtures

def _ann(spec):
    """`{clause_id: [atom, ...]}` from `{clause_id: [name, ...]}`."""
    return {cid: [{"name": n, "kind": "value", "gloss": n.replace("_", " ")}
                  for n in names] for cid, names in spec.items()}


@pytest.fixture
def toy():
    """A corpus whose DF distribution is obviously two-humped: `broad_a` and
    `broad_b` are in every clause, the rest are hapaxes. Any sane label-free
    binarization must put the cut between them.

    Three hapaxes per clause, so the rare END CARRIES ENOUGH MASS (60
    occurrences) to fund the broad arm's budget (40) without spilling over into
    the broad names — otherwise the low-DF arm is not an opposite-direction arm
    at all, it is the same arm with extra steps.
    """
    spec = {}
    for i in range(20):
        spec[f"c{i:02d}"] = ["broad_a", "broad_b",
                             f"rare_{i:02d}a", f"rare_{i:02d}b",
                             f"rare_{i:02d}c"]
    return _ann(spec)


@pytest.fixture
def toy_atoms():
    return {"beh": {"atoms": [{"name": "broad_a", "kind": "value",
                               "gloss": "g", "weight": 2},
                              {"name": "rare_00a", "kind": "value",
                               "gloss": "g", "weight": 2}]}}


# ------------------------------------------------------------- the contract

def test_module_declares_itself_a_panel_reading_diagnostic():
    doc = BF.__doc__
    assert "DIAGNOSTIC" in doc
    assert "invariant 9" in doc
    assert "may never inform the ontology" in doc


def test_no_repo_module_imports_this_diagnostic():
    offenders = []
    for path in glob.glob(os.path.join(REPO, "*.py")):
        name = os.path.basename(path)
        if name in ("breadth_filter.py", "test_breadth_filter.py"):
            continue
        with open(path) as fh:
            src = fh.read()
        if re.search(r"^\s*(import|from)\s+breadth_filter\b", src, re.M):
            offenders.append(name)
    assert offenders == [], f"the diagnostic has consumers: {offenders}"


def test_the_module_is_named_in_the_anti_cheat_forbidden_list():
    """A diagnostic that re-scores against the panel holds a gold-derived
    effect size AND a concrete list of atoms to delete. A query module
    importing it could launder either, so the static scan must name it."""
    import test_no_reference_leak as G
    assert "breadth_filter" in G.FORBIDDEN


def test_scores_the_true_589_passage_universe_not_the_graded_subset():
    src = open(os.path.join(REPO, "breadth_filter.py")).read()
    assert "load_true_panel" in src
    assert not re.search(r"\bload_panel\s*\(", src), (
        "load_panel is the GRADED SUBSET. The true universe is the 589-passage "
        "one; scoring the subset inflates every number in the table.")


# ============================================================================
# 1. THE CUTOFF IS PRE-DECLARED AND LABEL-FREE
# ============================================================================

def test_the_cutoff_rule_is_the_preregistered_label_free_one():
    assert BF.CUTOFF_RULE == threshold.PREFERRED == "otsu"
    assert BF.CUTOFF_RULE in threshold.RULES


def test_the_cutoff_is_a_pure_function_of_the_annotations():
    """No panel, no scores, no behaviour, no path in the signature. If the cut
    could see a score it could be the argmax of one."""
    import inspect
    params = list(inspect.signature(BF.cutoff).parameters)
    assert params[0] == "ann"
    banned = {"panel", "gold", "scores", "mcc", "universe", "module", "slug"}
    assert not (set(params) & banned), f"cutoff sees {set(params) & banned}"


def test_computing_the_cutoff_opens_no_file_and_scores_nothing(toy, monkeypatch):
    """The mutant this catches: `cutoff` quietly sweeps DF values, scores each
    against the panel and returns the argmax. That is `act_match` again."""
    opened = []
    real_open = io.open

    def spy(path, *a, **kw):
        opened.append(str(path))
        return real_open(path, *a, **kw)

    monkeypatch.setattr("builtins.open", spy)
    monkeypatch.setattr("io.open", spy)

    def boom(*a, **kw):
        raise AssertionError("cutoff consulted the panel/scorer")

    monkeypatch.setattr(BF, "universe", boom)
    monkeypatch.setattr(BF, "score", boom)
    BF.cutoff(toy)
    assert opened == [], f"cutoff opened {opened}"


def test_the_cutoff_separates_the_broad_atoms_from_the_rare_ones(toy):
    cut = BF.cutoff(toy)
    df = BF.atom_df(toy)
    assert df["broad_a"] == df["broad_b"] == 20
    assert all(df[n] == 1 for n in df if n.startswith("rare_"))
    assert 1 < cut <= 20
    assert BF.broad_names(toy) == {"broad_a", "broad_b"}


def test_the_reported_operating_point_is_the_rules_not_the_sweeps_argmax():
    """The sweep is a CURVE for understanding. Promoting its argmax is the
    forbidden move, so the report must both say so and quote the rule's cut."""
    r = {"cutoff": 9.0, "cutoff_rule": "otsu",
         "sweep": [{"cut": 2.0, "n_names": 250, "n_occ": 1500,
                    "mcc": 0.90, "delta": 0.9, "rate": 0.1},
                   {"cut": 9.0, "n_names": 43, "n_occ": 674,
                    "mcc": 0.34, "delta": 0.0, "rate": 0.29}],
         "vocab": 361, "corpus_occurrences": 1629, "clauses": 587,
         "draws": 40, "budget": 674, "modules": {}}
    text = "\n".join(BF.report(r))
    assert "NOT A SELECTION" in text
    assert "otsu" in text
    # the sweep's best point (cut 2.0, delta +0.9) must not be quoted as the
    # operating point anywhere in the report
    assert not re.search(r"operating point[^\n]*2\.0", text, re.I)


def test_a_sweep_argmax_cannot_reach_the_operating_point(toy):
    """Mechanical version of the same guard: whatever the sweep says, the cut
    used by `run` comes from `cutoff`."""
    import inspect
    src = inspect.getsource(BF.run)
    assert "cutoff(" in src
    assert "argmax" not in src
    assert re.search(r"cutoff\s*=\s*cutoff\(", src) or \
        re.search(r"cut\s*=\s*cutoff\(", src), \
        "run() must take its operating point from cutoff(), nothing else"


# ============================================================================
# 2. THE FILTER IS A STRUCTURAL SET OPERATION ON THE VOCABULARY
# ============================================================================

def test_the_filter_removes_the_names_from_both_sides_of_the_join(toy, toy_atoms):
    ann2, atoms2 = BF.apply_filter(toy, toy_atoms, {"broad_a"})
    assert all("broad_a" not in [a["name"] for a in v] for v in ann2.values())
    names = [a["name"] for a in atoms2["beh"]["atoms"]]
    assert names == ["rare_00a"]


def test_the_filter_never_mutates_its_inputs(toy, toy_atoms):
    before_ann = {k: [a["name"] for a in v] for k, v in toy.items()}
    before_q = [a["name"] for a in toy_atoms["beh"]["atoms"]]
    BF.apply_filter(toy, toy_atoms, {"broad_a", "broad_b"})
    assert {k: [a["name"] for a in v] for k, v in toy.items()} == before_ann
    assert [a["name"] for a in toy_atoms["beh"]["atoms"]] == before_q


def test_it_is_a_set_operation_not_a_reweighting(toy, toy_atoms):
    """Invariant 10 lives here: a filter DELETES vocabulary, it does not
    multiply anything by a learned coefficient. Weights must survive untouched
    on every atom that survives."""
    ann2, atoms2 = BF.apply_filter(toy, toy_atoms, {"broad_a"})
    assert atoms2["beh"]["atoms"][0] == toy_atoms["beh"]["atoms"][1]
    src = open(os.path.join(REPO, "breadth_filter.py")).read()
    body = re.sub(r'"""[\s\S]*?"""', "", src)
    assert "weight" not in body or "weight" not in re.sub(
        r"#.*", "", body).split("def apply_filter")[1].split("\ndef ")[0]


# ============================================================================
# 3. THE CONTROL, AND THE OPPOSITE-DIRECTION ARM
# ============================================================================

def test_the_control_is_occurrence_matched_not_name_matched(toy):
    """43 broad names carry 674 atom occurrences; 43 random names carry ~190.
    Matching on names would compare a big deletion with a small one and call
    the difference an effect."""
    treat = BF.broad_names(toy)
    budget = BF.occurrence_budget(toy, treat)
    assert budget == 40                       # 2 broad atoms x 20 clauses
    ctrl = BF.random_names(toy, budget, seed=0)
    assert BF.occurrence_budget(toy, ctrl) >= budget
    assert len(ctrl) > len(treat), (
        "an occurrence-matched random draw of a hapax-heavy vocabulary needs "
        "MORE names than the broad arm; equal name counts means the control "
        "was matched on the wrong quantity")


def test_the_control_is_actually_random(toy):
    """The mutant: `random_names` returns the same (or a DF-sorted) set every
    time, so the 'distribution' is a point mass and the SD — hence the MDE —
    collapses to zero."""
    budget = BF.occurrence_budget(toy, BF.broad_names(toy))
    draws = [BF.random_names(toy, budget, seed=s) for s in range(10)]
    assert len({frozenset(d) for d in draws}) > 1, "the control is a constant"
    assert BF.random_names(toy, budget, seed=3) == \
        BF.random_names(toy, budget, seed=3), "the control is not reproducible"
    # and it must not secretly be one of the DF arms
    assert not all(d == BF.df_names(toy, budget, highest=True) for d in draws)


def test_the_low_df_arm_takes_the_rarest_names_at_the_same_budget(toy):
    budget = BF.occurrence_budget(toy, BF.broad_names(toy))
    lo = BF.df_names(toy, budget, highest=False)
    hi = BF.df_names(toy, budget, highest=True)
    df = BF.atom_df(toy)
    assert all(df[n] == 1 for n in lo)
    assert {"broad_a", "broad_b"} <= hi
    assert BF.occurrence_budget(toy, lo) >= budget
    assert not (lo & hi)


def test_run_reports_the_low_df_arm(monkeypatch):
    """The mutant: the opposite-direction arm is quietly dropped, leaving
    'deleting broad atoms helps' with nothing to compare against."""
    r = _fake_run()
    for m in r["modules"].values():
        assert "lowest_df" in m, "the opposite-direction arm is missing"
    text = "\n".join(BF.report(r))
    # NOT `"lowest_df" in text`: that string also appears in the DF-profile
    # table, so deleting the ARM LINE from the report left this guard green.
    # The arm's own line, with its own MCC, is what has to be there.
    assert "contrast: lowest-DF" in text, "the low-DF arm's line is missing"
    arm = "%+.4f" % r["modules"]["combined"]["lowest_df"]["mcc"]
    assert text.count(arm) >= 2, "the low-DF arm's MCC is not printed"


# ============================================================================
# 4. POWER, AND MCC AS THE PRIMARY OUTCOME
# ============================================================================

def _fake_run():
    """A `run()`-shaped dict, so the reporting guards do not need 40 scorings."""
    ctrl = {"n_draws": 40, "mean": -0.02, "sd": 0.01, "lo": -0.04, "hi": 0.0,
            "deltas": [-0.02] * 40, "pct_below": 0.5,
            "mean_rate": -0.01, "sd_rate": 0.01}
    arm = {"mcc": -0.03, "rate": -0.02, "fp": -10, "fn": +5,
           "mcc_ci": (-0.06, 0.0), "n_names": 43, "n_occ": 674,
           "delta": -0.03}
    return {"cutoff": 9.04, "cutoff_rule": "otsu", "draws": 40, "budget": 674,
            "vocab": 361, "corpus_occurrences": 1629, "clauses": 587,
            "metric": "mcc", "sweep": [],
            "interpretability": {"names_removed": 43, "occ_removed": 674,
                                 "clauses_emptied": 76, "clauses": 587,
                                 "mean_atoms_before": 2.8,
                                 "mean_atoms_after": 1.6,
                                 "tp_evidence_before": 2.1,
                                 "tp_evidence_after": 0.9,
                                 "query_atoms_before": 70,
                                 "query_atoms_after": 41},
            "df": {"treatment": {"n": 43, "mean": 15.7},
                   "lowest_df": {"n": 300, "mean": 1.4},
                   "random": {"n": 150, "mean": 4.5}},
            "modules": {"combined": {
                "baseline": {"mcc": 0.34, "rate": 0.29, "fp": 1, "fn": 2,
                             "cells": [0.34] * 9},
                "treatment": dict(arm), "lowest_df": dict(arm),
                "query_side_only": dict(arm),
                "control": ctrl, "adjusted": -0.01,
                "mde": (1.959964 + 0.8416212) * 0.01,
                "n_cells": 9}}}


def test_the_mde_is_computed_from_the_controls_own_spread():
    r = _fake_run()
    d = r["modules"]["combined"]
    assert d["mde"] == pytest.approx(BF.Z * d["control"]["sd"], rel=1e-6)
    assert BF.Z == pytest.approx(1.959964 + 0.8416212, rel=1e-6)


def test_the_report_states_the_mde_and_the_noise_floor_before_the_effect():
    """The mutant: the MDE is dropped from the report, so a null lands as a
    finding. n=9 is the binding constraint and must be said out loud."""
    r = _fake_run()
    text = "\n".join(BF.report(r))
    assert "MDE" in text
    # THE VALUE, IN THE POWER BLOCK, BEFORE THE FIRST MODULE. Asserting only
    # that the string "MDE" appears somewhere left a mutant green: the prose
    # says "MDE" and the arms table quotes it, so deleting the power line
    # changed nothing this guard could see.
    mde = "%.4f" % r["modules"]["combined"]["mde"]
    assert mde in text
    assert text.index(mde) < text.index("MODULE:"), \
        "the MDE must be stated BEFORE the effect, not beside it"
    assert "0.0316" in text and "0.037" in text, \
        "the project's re-derived noise floor must be quoted"
    assert "9" in text and re.search(r"n\s*=\s*9|9 cells|9 \(behaviour",
                                     text, re.I)
    # power BEFORE the effect: the MDE line must precede the arms table
    assert text.index("MDE") < text.index("adjusted")


def test_mcc_is_the_primary_outcome_not_the_error_rate():
    """The prior ablation improved the error rate while MCC got WORSE (-0.0074)
    by trading 76 false positives for 29 false negatives. An intervention that
    only moves the error rate is not an improvement."""
    r = _fake_run()
    assert r["metric"] == "mcc"
    text = "\n".join(BF.report(r))
    assert "MCC" in text
    assert text.index("MCC") < text.index("error rate")


def test_the_verdict_cannot_claim_an_effect_inside_the_mde():
    r = _fake_run()
    r["modules"]["combined"]["adjusted"] = -0.001
    assert "CANNOT RESOLVE" in "\n".join(BF.report(r))
    r["modules"]["combined"]["adjusted"] = -0.20
    assert "CANNOT RESOLVE" not in "\n".join(BF.report(r))


def test_confidence_intervals_are_reported_for_the_treatment():
    text = "\n".join(BF.report(_fake_run()))
    assert re.search(r"\[[-+]?\d\.\d+, [-+]?\d\.\d+\]", text), \
        "no interval anywhere in the report"


def test_bootstrap_ci_over_cells_brackets_the_mean():
    cells = [0.1, -0.2, 0.3, 0.0, 0.05, -0.1, 0.2, 0.15, -0.05]
    lo, hi = BF.boot_ci(cells, n=500, seed=1)
    assert lo < sum(cells) / len(cells) < hi


# ============================================================================
# 5. INTERPRETABILITY COST
# ============================================================================

def test_the_report_states_what_the_filter_costs_interpretability():
    """The project's value proposition is auditability. Deleting the broad
    atoms may delete exactly the atoms that explain a match to a human, and a
    report that hides that is selling the wrong thing."""
    text = "\n".join(BF.report(_fake_run()))
    assert "INTERPRETABILITY" in text.upper()
    assert "76" in text          # clauses left with no atoms at all
    assert "emptied" in text.lower() or "no atoms" in text.lower()


def test_clauses_emptied_is_counted(toy):
    """Every toy clause keeps its hapax, so nothing is emptied; deleting the
    hapaxes too empties all 20."""
    assert BF.clauses_emptied(toy, {"broad_a", "broad_b"}) == 0
    allnames = set(BF.atom_df(toy))
    assert BF.clauses_emptied(toy, allnames) == 20


# ============================================================================
# 6. END TO END, SMALL
# ============================================================================

def test_run_end_to_end_on_the_real_corpus():
    if not os.path.exists(os.path.join(REPO, "annotations_b8.json")):
        pytest.skip("real artifacts not present")
    r = BF.run(draws=3, modules=("combined",), sweep=False)
    d = r["modules"]["combined"]
    assert d["n_cells"] == 9
    assert len(d["control"]["deltas"]) == 3
    assert d["mde"] > 0
    # ON THE REAL RUN, not on a fixture: the MDE must come from the control's
    # OWN measured spread. Checking only the fixture's internal consistency is
    # circular and a hardcoded `"mde": 0.001` sailed straight past it.
    assert d["mde"] == pytest.approx(BF.Z * d["control"]["sd"], rel=1e-9)
    assert d["control"]["sd"] > 0, "the control collapsed to a point mass"
    assert r["cutoff_rule"] == "otsu"
    # the arms must actually differ from the baseline
    assert d["treatment"]["mcc"] != 0.0
    assert r["interpretability"]["occ_removed"] > 0
    text = "\n".join(BF.report(r))
    assert "VERDICT" in text
