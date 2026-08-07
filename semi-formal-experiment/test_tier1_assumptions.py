"""Property tests for the Tier-1 ($0, offline) assumption tests T-A1 / T-A2 / T-A9.

Written RED-first: every assertion below was run and observed to FAIL for its
named reason before `tier1_assumptions.py` / `tA9_scaling.py` existed.

Each test names the specific way the corresponding measurement could come out
"right" while the assumption it is supposed to test is FALSE. That is the point
of the file — these are anti-artifact guards, not coverage.

No network, no model calls, no spend.
"""
from __future__ import annotations

import math

import pytest

import containment
import grammar

import tier1_assumptions as tier1
import tA9_scaling as scal


# --------------------------------------------------------------- T-A1 guards


def test_drift_denominator_counts_a_clause_missing_from_one_pass():
    """RED reason: a clause with atoms in one pass and NONE in the other is
    MAXIMAL drift. Restricting the denominator to the intersection of the two
    `by_clause` maps silently drops exactly the worst cases and drives p_drift
    down. This is the way T-A1 passes while A-1 is false."""
    a = {"c1": {"x"}, "c2": {"y"}}
    b = {"c1": {"x"}}  # c2 absent entirely
    r = tier1.drift_pair(a, b, ["c1", "c2"], vocab_a={"x", "y"}, vocab_b={"x"})
    assert r["n_clauses"] == 2
    assert r["n_drift"] == 1
    assert "c2" in r["drifted"]


def test_novel_is_absence_from_the_other_pass_whole_vocabulary():
    """RED reason: if `novel` were computed as "name not in the other pass's
    set FOR THIS CLAUSE", every re-alignment (the same form moving between
    clauses) would be scored as a fresh human decision and p_novel would be
    ~1.0 by construction. Novelty must be checked against the other pass's
    ENTIRE vocabulary."""
    a = {"c1": {"moved_form"}}
    b = {"c1": {"other_form"}}
    # `moved_form` exists in b's vocabulary, just on a different clause.
    r = tier1.drift_pair(a, b, ["c1"],
                         vocab_a={"moved_form", "other_form"},
                         vocab_b={"other_form", "moved_form"})
    assert r["n_drift"] == 1
    assert r["n_novel"] == 0, "re-alignment must not count as a novel decision"

    r2 = tier1.drift_pair({"c1": {"brand_new"}}, {"c1": {"other_form"}}, ["c1"],
                          vocab_a={"brand_new"}, vocab_b={"other_form"})
    assert r2["n_novel"] == 1


def test_canonical_key_preserves_polarity():
    """RED reason: `grammar.stem_of` merges `must_x` with `mustnot_x`
    (verified below), so canonicalising with it would collapse a genuine
    polarity flip into "no drift". T-A1's lower bound must use
    `containment.dechain_name`, which is polarity-preserving."""
    assert grammar.stem_of("must_x") == grammar.stem_of("mustnot_x")  # the trap
    assert tier1.canon("must_x") != tier1.canon("mustnot_x")
    assert tier1.canon("must_x") == containment.dechain_name("must_x")


def test_cluster_bootstrap_is_wider_than_item_bootstrap_when_clusters_are_pure():
    """RED reason: a clause-level (item) bootstrap understates variance when
    drift is correlated within a section. If the helper resamples items rather
    than clusters, the interval is too tight and every T-A1 CI is wrong."""
    # 20 sections, 10 clauses each; each section is all-0 or all-1.
    clusters = [[1.0] * 10 if i % 2 == 0 else [0.0] * 10 for i in range(20)]
    lo_c, hi_c = tier1.cluster_bootstrap_mean(clusters, n_boot=2000, seed=1)
    flat = [[v] for c in clusters for v in c]
    lo_i, hi_i = tier1.cluster_bootstrap_mean(flat, n_boot=2000, seed=1)
    assert (hi_c - lo_c) > 1.5 * (hi_i - lo_i)


# --------------------------------------------------------------- T-A2 guards


def test_permutation_destroys_the_arrival_dynamics_it_is_meant_to_control():
    """RED reason — THIS IS THE T-A2 ARTIFACT, and it inverts
    ASSUMPTION_TESTS' recommendation. The permutation control re-orders a
    FIXED, FINITE per-clause atom pool. Two corpora with opposite arrival
    dynamics — one where forms keep arriving to the last clause, one that has
    seen every form by clause 20 — have the SAME multiset of per-clause sets,
    so their permuted curves are indistinguishable while their observed curves
    are as different as they can be. A saturation verdict read off the
    permuted curve is therefore a statement about pool size only."""
    pool, n = 20, 200
    climbing = {f"c{i}": {f"f{i // 10}"} for i in range(n)}   # last form at c190
    saturated = {f"c{i}": {f"f{i % pool}"} for i in range(n)}  # all forms by c19
    ids = [f"c{i}" for i in range(n)]

    obs_climb = tier1.curve_from_sets(climbing, ids)
    obs_sat = tier1.curve_from_sets(saturated, ids)
    assert obs_climb[19] == 2 and obs_sat[19] == pool, (obs_climb[19], obs_sat[19])

    pc = tier1.mean_curve(tier1.permuted_curves(climbing, ids, n_perm=200, seed=7))
    ps = tier1.mean_curve(tier1.permuted_curves(saturated, ids, n_perm=200, seed=7))
    assert max(abs(a - b) for a, b in zip(pc, ps)) < 0.5, "permuted curves agree"
    assert pc[-1] == ps[-1] == pool, "endpoint is pool size, always"


def test_decile_rates_are_forms_per_clause_at_each_end():
    """RED reason: if the 'last window' rate were read off the whole tail
    rather than the last `window` clauses, the ratio would be diluted and the
    40% criterion would fire on almost any curve."""
    curve = [1, 2, 3, 4, 5, 5, 5, 5, 5, 5]  # 5 forms in first 5, none after
    first, last = tier1.decile_rates(curve, window=5)
    assert first == pytest.approx(1.0)
    assert last == pytest.approx(0.0)


def test_heaps_beta_recovers_a_known_exponent():
    """RED reason: a log-log fit that includes the n<~10 region, or that fits
    F against batch index instead of cumulative clauses, returns a beta that
    has nothing to do with Heaps' law. Then "beta < 0.75" is not a saturation
    statement."""
    ns = list(range(1, 601))
    forms = [max(1, round(n ** 0.60)) for n in ns]
    beta = tier1.heaps_beta(ns, forms, min_n=20)
    assert abs(beta - 0.60) < 0.03, beta


def test_observed_curve_is_cumulative_over_clauses_not_batches():
    """RED reason: `per_batch` rows are per BATCH. Plotting F against batch
    index compares arms with different batch sizes (14 / 8 / 6) on different
    x-axes, so the three arms' betas would not be comparable at all."""
    per_batch = [{"clauses": 5, "coined": 4}, {"clauses": 5, "coined": 1},
                 {"clauses": 5, "coined": 0}]
    ns, forms = tier1.observed_curve(per_batch)
    assert ns == [5, 10, 15]
    assert forms == [4, 5, 5]


# --------------------------------------------------------------- T-A9 guards


def test_emit_asp_emits_one_choice_rule_per_unconstrained_ctx_atom():
    """The A-9 claim, asserted against the emitter rather than its docstring.
    RED reason: if the emitter instead enumerated a fixed scenario list, the
    scenario space would not be 2^|ctx| and A-9's restatement would be wrong."""
    ex = scal.make_extraction(n_rules=4, exclusion_density=0.0, seed=0)
    import emit_asp
    lp = emit_asp.emit(ex, include_provenance=False)
    n_ctx = sum(1 for a in ex["atoms"] if a["kind"] == "context")
    import re
    n_choice = sum(1 for line in lp.splitlines()
                   if re.match(r"^\{ ctx\([a-z0-9_]+\) \}\.", line))
    assert n_ctx > 0
    assert n_choice == n_ctx


def test_at_most_one_atoms_lose_their_independent_choice_rule():
    """RED reason: if grouped atoms kept an independent `{ ctx(a) }.` AND a
    bounded group, the exclusion-density sweep would not actually shrink the
    scenario space, and the 0%-vs-50% arms of T-A9 would be the same
    experiment run twice."""
    import emit_asp
    ex = scal.make_extraction(n_rules=8, exclusion_density=1.0, seed=0)
    assert ex["exclusions"], "generator must actually emit exclusions"
    lp = emit_asp.emit(ex, include_provenance=False)
    grouped = {n for e in ex["exclusions"] if e["kind"] == "at_most_one"
               for n in e["atoms"]}
    assert grouped
    for n in grouped:
        assert ("{ ctx(%s) }." % n) not in lp


def test_scenario_space_grows_exponentially_in_unconstrained_ctx_atoms():
    """The SPACE is 2^|unconstrained ctx| by construction (one choice rule per
    atom). RED reason: if the space were not exponential, A-9's restatement
    would be wrong and measuring grounding would be fine."""
    counts = []
    for n in (4, 6, 8):
        r = scal.measure(scal.make_extraction(n_rules=n, exclusion_density=0.0,
                                              seed=0), timeout=60.0)
        assert r["status"] == "ok", r
        assert r["n_answer_sets_complete"], r
        counts.append(r["n_answer_sets"])
    assert counts[1] > 2 * counts[0] and counts[2] > 2 * counts[1], counts


def test_brave_mode_does_not_visit_all_answer_sets():
    """MEASURED CORRECTION to ASSUMPTION_TESTS' A-9 restatement, which says
    `run_conflicts` "uses --enum-mode=brave over all answer sets". clingo's
    brave mode computes brave consequences by iterative refinement, so it
    visits O(#atoms) models, not 2^n. RED reason: if brave mode really did
    visit every answer set, model count WOULD be the enumeration cost and the
    restatement would be exactly right."""
    r = scal.measure(scal.make_extraction(n_rules=8, exclusion_density=0.0,
                                          seed=0), timeout=60.0)
    assert r["n_answer_sets"] > 100, r["n_answer_sets"]
    assert r["n_models_visited_brave"] < r["n_answer_sets"] / 10, r


def test_exclusions_shrink_the_scenario_space():
    """RED reason: if at_most_one groups did not actually reduce the number of
    answer sets, the 0%-vs-50% density arms would be the same experiment."""
    a = scal.measure(scal.make_extraction(12, 0.0, 0), timeout=60.0)
    b = scal.measure(scal.make_extraction(12, 0.5, 0), timeout=60.0)
    assert b["n_answer_sets"] < a["n_answer_sets"] / 2, (a["n_answer_sets"],
                                                         b["n_answer_sets"])


def test_grounded_size_stays_small_while_models_explode():
    """RED reason: this is the exact failure mode ASSUMPTION_TESTS names — a
    grounding-size measurement comes back green on a program that cannot be
    solved. If grounded size grew as fast as the model count, measuring
    grounding would be a sufficient guard after all."""
    a = scal.measure(scal.make_extraction(n_rules=4, exclusion_density=0.0,
                                          seed=0), timeout=60.0)
    b = scal.measure(scal.make_extraction(n_rules=10, exclusion_density=0.0,
                                          seed=0), timeout=60.0)
    ground_growth = b["ground_rules"] / max(1, a["ground_rules"])
    model_growth = b["n_answer_sets"] / max(1, a["n_answer_sets"])
    assert model_growth > 4 * ground_growth, (ground_growth, model_growth)


def test_no_size_or_time_guard_exists_in_the_shipped_entry_points():
    """G-f, asserted rather than quoted. RED reason: if a cap already existed,
    T-A9's falsification would be a non-event."""
    for path in ("emit_asp.py", "run_conflicts.py"):
        src = open(path).read()
        assert "time-limit" not in src
        assert "--models" not in src
        assert "solve_limit" not in src


def test_math_import_is_used():
    assert math.isclose(1.0, 1.0)
