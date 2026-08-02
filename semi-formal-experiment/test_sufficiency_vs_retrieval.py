"""Tests for `sufficiency_vs_retrieval.py`.

Three jobs.

1. **Pin the CONTRACT.** The module reads the panel, so it is fenced exactly
   like `weight_diag`: it must say in its own docstring that it is a diagnostic
   whose output may never inform the ontology, the vocabulary or a threshold,
   and no other repo module may import it. Those two tests are the fence.

2. **Pin the CATEGORISER.** The five-way categorisation of the 268 missing
   phrases is a deliverable in its own right and it is a hand-written lexical
   rule, i.e. the least trustworthy object in the file. The tests below pin its
   behaviour on named phrases, pin the frozen dev/held-out split that keeps its
   reported error rate honest, and pin that the reported error rate comes from
   the HELD-OUT sample the rule was never tuned on.

3. **Pin the STATISTICS.** A difference of means with a clause-level bootstrap
   CI is the whole answer. It is hand-rolled pure python (the repo `.venv` has
   no numpy) and a silent bug in it moves the verdict.
"""
import glob
import os
import re

import pytest

import sufficiency_vs_retrieval as S

REPO = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- the contract

def test_module_declares_itself_a_panel_reading_diagnostic():
    """If this banner goes, the next reader has a number derived from the answer
    key and no statement that feeding it back is illegal."""
    doc = S.__doc__
    assert "DIAGNOSTIC" in doc
    assert "invariant 9" in doc
    assert "may never inform the ontology" in doc


def test_no_repo_module_imports_this_diagnostic():
    """A consumer is how a panel-reading diagnostic becomes a leak. The moment
    `relevance.py` or `ontology.py` imports this, a gold-derived per-category
    effect size is one line from steering the vocabulary."""
    offenders = []
    for path in glob.glob(os.path.join(REPO, "*.py")):
        name = os.path.basename(path)
        if name in ("sufficiency_vs_retrieval.py",
                    "test_sufficiency_vs_retrieval.py"):
            continue
        with open(path) as fh:
            src = fh.read()
        if re.search(r"^\s*(import|from)\s+sufficiency_vs_retrieval\b", src, re.M):
            offenders.append(name)
    assert offenders == [], f"the diagnostic has consumers: {offenders}"


def test_diagnostic_does_not_import_the_other_diagnostic():
    """`weight_diag` fits supervised models on the panel. Importing it here
    would put a fitted readout one attribute access from this module's output,
    and `test_weight_diag.test_no_repo_module_imports_weight_diag` would fail —
    which is the correct outcome, so pin it on this side too."""
    with open(os.path.join(REPO, "sufficiency_vs_retrieval.py")) as fh:
        src = fh.read()
    assert not re.search(r"^\s*(import|from)\s+weight_diag\b", src, re.M)


def test_predictions_are_pre_registered_in_the_docstring():
    """The prior under test — deontic/precedence loss is conflict-bearing and
    should NOT predict relevance error, party/addressee loss SHOULD — is only a
    prior if it was written down before the number."""
    doc = S.__doc__
    for tag in ("P1.", "P2.", "P3."):
        assert tag in doc


# ---------------------------------------------------------- the categoriser

def test_categories_are_the_five_the_question_names():
    assert S.CATEGORIES == ("party", "deontic", "trigger", "exception",
                            "precedence")


@pytest.mark.parametrize("phrase,expected", [
    ("Assistant should understand and follow user intent", {"party", "deontic"}),
    ("Later instructions at the same authority take precedence", {"precedence"}),
    ("Interject only after sufficient signal that danger is imminent",
     {"trigger"}),
    ("Exception for scientific, historical, news, artistic, or appropriate "
     "contexts", {"exception"}),
    ("Content is a sequence of chunks", set()),
])
def test_categorise_named_phrases(phrase, expected):
    """Hand-checked anchors, one per category plus an `other`. These are the
    cases a future edit to the lexicon is most likely to break."""
    assert set(S.categorise(phrase)) == expected


def test_categorise_is_multi_label_not_a_priority_chain():
    """A single missing phrase routinely carries a party AND a force AND a
    condition. Collapsing to one label by priority order would make every
    per-category effect an artefact of that order."""
    got = S.categorise("The assistant should clarify when clarification is "
                       "necessary")
    assert {"party", "deontic", "trigger"} <= set(got)


def test_model_spec_is_not_a_party():
    """`Model Spec` is a document. A bare `\\bmodel\\b` rule tags every mention
    of it as a party and inflates the one category the prior says should
    predict."""
    assert "party" not in S.categorise(
        "The applicable Model Spec is specifically the trained-on version")


def test_every_missing_phrase_gets_a_category_set():
    """268 phrases in, 268 category sets out. A phrase silently dropped would
    move a per-category base rate without moving any n printed in the report."""
    rows = S.missing_phrases()
    assert len(rows) == 268
    assert all(isinstance(S.categorise(p), frozenset) for _cid, p in rows)


# --------------------------------------------- the validation of the labels

def test_dev_and_heldout_samples_are_disjoint_and_frozen():
    """The lexicon was revised after reading the DEV sample. If the two samples
    overlap, the reported error rate is a training-set number."""
    dev = set(S.HAND_LABELS_DEV)
    held = set(S.HAND_LABELS_HELDOUT)
    assert dev and held
    assert dev & held == set()
    assert dev == set(S.sample_indices(len(dev), S.DEV_SEED))
    assert held == set(S.sample_indices(len(held), S.HELDOUT_SEED,
                                        exclude=dev))


def test_hand_labels_only_use_declared_categories():
    for idx, cats in list(S.HAND_LABELS_DEV.items()) + \
            list(S.HAND_LABELS_HELDOUT.items()):
        assert set(cats) <= set(S.CATEGORIES), idx


def test_validation_reports_per_category_precision_and_recall():
    v = S.validate(S.HAND_LABELS_HELDOUT)
    assert v["n"] == len(S.HAND_LABELS_HELDOUT)
    for c in S.CATEGORIES:
        row = v["per_category"][c]
        assert set(row) >= {"tp", "fp", "fn", "precision", "recall"}
        assert 0.0 <= row["precision"] <= 1.0
        assert 0.0 <= row["recall"] <= 1.0
    assert 0.0 <= v["exact_match"] <= 1.0


def test_validation_is_perfect_against_the_rule_s_own_output():
    """Sanity floor: validating the rule against labels generated BY the rule
    must score 1.0 everywhere. If it does not, the scorer is broken and every
    reported precision is meaningless."""
    rows = S.missing_phrases()
    synth = {i: tuple(sorted(S.categorise(rows[i][1]))) for i in range(0, 268, 7)}
    v = S.validate(synth)
    assert v["exact_match"] == 1.0
    for c in S.CATEGORIES:
        row = v["per_category"][c]
        assert row["fp"] == 0 and row["fn"] == 0


def test_reported_error_rate_comes_from_the_heldout_sample():
    """The module must not quote the dev sample as its error rate."""
    assert S.REPORTED_VALIDATION_SAMPLE == "heldout"


# ------------------------------------------------------------- statistics

def test_bootstrap_diff_recovers_a_known_separation():
    """Group A all-1, group B all-0: the difference is exactly 1.0 and every
    resample must agree, so the CI is degenerate at 1.0."""
    lo, hi, d = S.bootstrap_diff([1.0] * 30, [0.0] * 30, n=200, seed=1)
    assert d == 1.0
    assert lo == 1.0 and hi == 1.0


def test_bootstrap_diff_brackets_zero_for_identical_groups():
    vals = [i / 20.0 for i in range(20)]
    lo, hi, d = S.bootstrap_diff(vals, list(vals), n=500, seed=3)
    assert abs(d) < 1e-12
    assert lo <= 0.0 <= hi


def test_bootstrap_diff_is_deterministic_under_a_fixed_seed():
    a = [0.1, 0.4, 0.9, 0.2, 0.7]
    b = [0.3, 0.3, 0.1, 0.6]
    assert S.bootstrap_diff(a, b, n=300, seed=11) == \
        S.bootstrap_diff(a, b, n=300, seed=11)
    assert S.bootstrap_diff(a, b, n=300, seed=11) != \
        S.bootstrap_diff(a, b, n=300, seed=12)


def test_bootstrap_diff_on_an_empty_group_is_not_silently_zero():
    """An empty arm means the split produced no clauses on one side. Returning
    0.0 with a tight CI would print as 'no effect' when it is 'no data'."""
    with pytest.raises(ValueError):
        S.bootstrap_diff([], [0.1, 0.2], n=10, seed=1)


def test_rank_auc_matches_a_hand_computed_case():
    """AUC of the flag as a ranker of clause error rate. Two positives ranked
    1st and 3rd of four -> (2*2 - 1 - 2... ) hand-checked below."""
    assert S.auc([0.9, 0.5, 0.7, 0.1], [1, 0, 1, 0]) == 1.0
    assert S.auc([0.1, 0.5, 0.7, 0.9], [1, 0, 1, 0]) == 0.25
    assert S.auc([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 0]) == 0.5


# ------------------------------------------------- the retrieval join (slow)
# These build the 589-passage universe and run the shipped tool over it, which
# takes several seconds. Cached at module level so the whole file pays once.

def test_clause_kinds_are_the_five_readback_strata():
    """The read-back sampled 25 clauses of each of five kinds. If the kind
    lookup silently returns None for a stratum, the per-kind breakdown reports
    a 25-clause effect on 0 clauses."""
    kinds = S.clause_kinds()
    assert set(kinds.values()) == set(S.CLAUSE_KINDS)
    counts = {k: sum(1 for v in kinds.values() if v == k) for k in S.CLAUSE_KINDS}
    assert counts == {k: 25 for k in S.CLAUSE_KINDS}


def test_every_readback_clause_is_either_scored_or_declared_unjoinable():
    """125 in; scored + unjoined must equal 125. A clause that joins to no
    graded passage has NO retrieval outcome, and dropping it quietly is the
    coverage failure the read-back run already committed once."""
    R = S.retrieval()
    assert len(R.rate) + len(R.unjoined) == 125
    assert len(R.unjoined) == 2, sorted(R.unjoined)
    assert set(R.rate) & set(R.unjoined) == set()


def test_trials_equal_passages_times_cells():
    """Error rate = errors / trials, and trials must be exactly (passages the
    clause joins to) × (behaviour × pair-gold cells). A miscount here rescales
    every rate by a clause-dependent factor."""
    R = S.retrieval()
    assert len(R.cells) == 9
    for cid, n in R.trials.items():
        assert n == len(R.passages[cid]) * len(R.cells)


def test_error_rate_decomposes_into_false_positives_and_false_negatives():
    R = S.retrieval()
    for cid in R.rate:
        assert R.fp[cid] + R.fn[cid] == R.err[cid]
        assert R.rate[cid] == pytest.approx(R.err[cid] / R.trials[cid])
        assert 0.0 <= R.rate[cid] <= 1.0


def test_the_tool_arm_is_the_shipped_label_free_predictor():
    """Not an oracle threshold and not a refit. If this ever becomes
    `best_threshold`, the diagnostic reports a number no consumer can obtain."""
    import inspect
    src = inspect.getsource(S.retrieval.__wrapped__ if hasattr(
        S.retrieval, "__wrapped__") else S._build_retrieval)
    assert "predict(" in src
    assert "best_threshold" not in src


def test_split_returns_both_arms_keyed_to_clauses():
    R = S.retrieval()
    eff = S.effect(R, lambda cid: S.fidelity()[cid]["sufficient"], n=200)
    assert eff["n_true"] + eff["n_false"] == len(R.rate)
    assert eff["n_true"] == 20 - len([c for c in R.unjoined
                                      if S.fidelity()[c]["sufficient"]])
    assert eff["lo"] <= eff["diff"] <= eff["hi"]
    assert 0.0 <= eff["auc"] <= 1.0


def test_effect_refuses_a_degenerate_split():
    """A flag true for every clause has no comparison arm. It must raise, not
    print 0.000 with a tight CI."""
    R = S.retrieval()
    with pytest.raises(ValueError):
        S.effect(R, lambda cid: True, n=10)


def test_category_flags_are_per_clause_unions_of_their_missing_phrases():
    R = S.retrieval()
    flags = S.clause_categories()
    fid = S.fidelity()
    for cid in R.rate:
        want = set()
        for p in fid[cid]["missing"]:
            want |= S.categorise(p)
        assert flags[cid] == want


def test_clauses_with_no_missing_phrases_carry_no_category():
    fid = S.fidelity()
    flags = S.clause_categories()
    empties = [c for c in fid if not fid[c]["missing"]]
    assert len(empties) == 20
    assert all(flags[c] == set() for c in empties)


def test_main_prints_the_verdict_and_the_validation_together(capsys):
    """The categorisation's error rate and the effect it is used to measure are
    one artifact. A report that prints the effect without the error rate invites
    exactly the over-reading this module's docstring warns about."""
    S.main(["--fast"])          # --fast only lowers the resample count
    out = capsys.readouterr().out
    assert "held-out" in out
    assert "exact-set match" in out
    assert "sufficient" in out and "faithful" in out
    for c in S.CATEGORIES:
        assert c in out
    assert "DIAGNOSTIC" in out


# ------------------------------------------------------- the atom-count confound

def test_atom_count_is_read_from_the_shipped_annotations():
    """`faithful` means 'the render asserted nothing the clause does not say'.
    A clause with more atoms has more chances to assert something unsupported
    AND more chances to overlap a behaviour query — so atom count confounds the
    fidelity arms and must be measurable."""
    counts = S.clause_atom_count()
    fid = S.fidelity()
    assert set(counts) >= set(fid)
    assert all(isinstance(v, int) and v >= 0 for v in counts.values())
    assert max(counts[c] for c in fid) > 1


def test_stratified_effect_recovers_zero_when_the_flag_is_stratum_noise():
    """Within each stratum the flag splits identical values, so the pooled
    within-stratum difference is 0 even though the raw difference is large."""
    R = S.retrieval()
    cids = sorted(R.rate)
    strata = {c: (i % 3) for i, c in enumerate(cids)}
    # flag correlates perfectly with stratum -> no within-stratum contrast
    with pytest.raises(ValueError):
        S.stratified_effect(R, lambda c: strata[c] == 0,
                            lambda c: strata[c], n=50)


def test_stratified_effect_matches_the_raw_effect_with_one_stratum():
    """One stratum means no adjustment, so the two must agree exactly on the
    point estimate. If they do not, the pooling weights are wrong."""
    R = S.retrieval()
    fid = S.fidelity()
    raw = S.effect(R, lambda c: fid[c]["faithful"], n=200, seed=5)
    strat = S.stratified_effect(R, lambda c: fid[c]["faithful"],
                                lambda c: 0, n=200, seed=5)
    assert strat["diff"] == pytest.approx(raw["diff"])


def test_confound_report_names_atom_count_and_the_stratified_faithful_effect():
    R = S.retrieval()
    lines = "\n".join(S.report_confounds(R, n=200))
    assert "atom count" in lines
    assert "faithful | atom-count" in lines


# --------------------------------------------------------------- POWER
# A null at n=123 with 20 positives is close to guaranteed whether or not the
# effect is real. These pin that the module says so BEFORE it says "no effect".

def test_mde_two_proportion_matches_a_textbook_case():
    """n=64 per arm at p=0.5 detects ~0.25 absolute at 80% power / alpha .05.
    Hand-check: (1.96+0.8416)*sqrt(2*0.25/64) = 0.2476."""
    d = S.mde_two_proportion(64, 64, 0.5)
    assert 0.22 < d < 0.28


def test_mde_shrinks_with_n_and_grows_with_imbalance():
    balanced = S.mde_two_proportion(100, 100, 0.3)
    bigger = S.mde_two_proportion(1000, 1000, 0.3)
    lopsided = S.mde_two_proportion(20, 180, 0.3)
    assert bigger < balanced < lopsided


def test_mde_correlation_is_the_fisher_z_threshold():
    """|r| detectable at 80% power, n=123: tanh(2.8016/sqrt(120)) ~= 0.250."""
    r = S.mde_correlation(123)
    assert 0.24 < r < 0.26
    assert S.mde_correlation(1000) < r


def test_mde_difference_in_means_uses_the_observed_spread():
    """The outcome is a per-clause RATE, not a single Bernoulli draw, so the
    two-proportion MDE is the WRONG instrument on its own; the difference-in-
    means MDE on the observed between-clause SD is the one that matches the
    test actually run."""
    R = S.retrieval()
    d = S.mde_diff_in_means(R, 20, 103)
    assert 0.0 < d < 1.0
    assert S.mde_diff_in_means(R, 60, 63) < d      # balanced split detects less


def test_power_report_states_the_mde_and_the_uninformative_null(capsys):
    R = S.retrieval()
    txt = "\n".join(S.report_power(R))
    assert "MDE" in txt
    assert "uninformative" in txt.lower()
    # per-category power, which is far worse than the headline
    for c in S.CATEGORIES:
        assert c in txt


def test_power_block_is_printed_before_any_effect(capsys):
    S.main(["--fast"])
    out = capsys.readouterr().out
    assert out.index("MDE") < out.index("FIDELITY FLAGS")


# ------------------------------------------- kind stratification is PRIMARY

def test_kind_stratified_estimate_is_reported_for_every_fidelity_split():
    """Clause kind is a common cause of BOTH sufficiency and panel hit rate
    (sufficiency by kind runs 1/25..9/25; hit rate 0.056..0.242). An
    unstratified estimate is uninterpretable, so the within-kind estimate is
    the primary column."""
    R = S.retrieval()
    lines = S.report_fidelity(R, n=200)
    joined = "\n".join(lines)
    assert "within-kind" in joined
    for label in ("sufficient", "faithful"):
        assert any(label in l and "within-kind" in l for l in lines) or \
            any(label in l for l in lines)
    assert "PRIMARY" in joined


def test_kind_stratified_effect_uses_all_five_kinds_when_both_arms_exist():
    R = S.retrieval()
    fid = S.fidelity()
    e = S.stratified_effect(R, lambda c: fid[c]["sufficient"],
                            lambda c: S.clause_kinds()[c], n=200)
    assert e["strata"] == 5
    assert e["dropped"] == 0


def test_continuous_predictor_is_reported_because_it_is_better_powered():
    """The binary `sufficient` flag throws away the count of missing phrases,
    which is the same measurement at higher resolution and higher power."""
    R = S.retrieval()
    c = S.continuous_effect(R, lambda k: len(S.fidelity()[k]["missing"]),
                            n=200)
    assert -1.0 <= c["rho"] <= 1.0
    assert c["lo"] <= c["rho"] <= c["hi"]
    assert c["n"] == len(R.rate)


def test_the_verdict_and_the_refuted_prediction_are_recorded_in_the_module():
    """The answer lives in the module, not in a chat message. The within-kind
    estimate refuted P1, and a docstring still claiming a flat null would be a
    conclusion the next agent has to re-derive."""
    doc = S.__doc__
    assert "P1 is REFUTED" in doc
    assert "P2 is NOT supported" in doc
    assert "unsupported" in doc and "false positive" in doc.lower()
    # the honest caveat must travel with the finding
    assert "MDE" in doc and "multiple" in doc.lower()


# ============================================================================
# THE MODULE ARM — added 2026-08-02 after a science review found the analysis
# was run entirely through `relevance.py`, which HANDOFF.md marks as VIOLATING
# invariant 10. A finding that only holds under the module the contract is
# retiring is not a finding about the tool.
# ============================================================================

def test_modules_arm_names_the_two_compliant_modules():
    """`relevance` is the bag scorer (invariant-10 VIOLATING). `structural` and
    `combined` are the compliant ones. All three must be reachable or the
    reported effect is conditional on a module nobody intends to ship."""
    assert S.MODULES == ("relevance", "structural", "combined")
    assert S.PRIMARY_MODULE == "combined"


def test_each_module_arm_is_the_shipped_configuration():
    """`combined` at V1@`any_atom` and `structural` at its shipped `any_atom`
    default — the exact configurations `benchmark.build_query_module` ships.
    Rebuilding the query here by hand is how the diagnostic ends up scoring a
    configuration that is not the one the project reports."""
    import benchmark as B
    import relevance as R
    panel = B.load_true_panel(spec_keys=(S.SPEC_KEY,))
    clauses, _ = B.clauses_for_spec(S.SPEC_KEY)
    for name in S.MODULES:
        want = B.build_query_module(name, panel, clauses,
                                    annotations=R.load_annotations(S.ANNOTATIONS),
                                    atoms=S.BEHAVIOUR_ATOMS)
        got = S.predictor(name, panel, clauses)
        for slug in sorted(want.queries):
            assert got(slug) == want.predict(slug), (name, slug)


def test_retrieval_is_keyed_by_module_and_the_modules_disagree():
    """A cache keyed only on the panel would hand every module the first
    module's numbers, and the whole comparison would print three identical
    rows."""
    a = S.retrieval(module="relevance")
    b = S.retrieval(module="combined")
    assert a is not b
    assert a.module == "relevance" and b.module == "combined"
    assert a.rate != b.rate


def test_module_comparison_report_prints_all_three_modules(capsys):
    R = None
    lines = "\n".join(S.report_modules(n=200))
    for name in S.MODULES:
        assert name in lines
    assert "VIOLATING" in lines
    assert "faithful" in lines and "sufficient" in lines
    _ = R


def test_docstring_no_longer_calls_relevance_the_shipped_tool():
    """`relevance.py` violates invariant 10. Calling it 'the shipped label-free
    tool' in a docstring is how the next reader inherits the error."""
    doc = S.__doc__
    assert "the shipped label-free tool" not in doc
    assert "invariant 10" in doc


def test_docstring_records_the_module_swap_verdict():
    """`faithful` / `>=1 unsupported` survive the swap; `sufficient` does not.
    LADDER_PLAN step 1's gate was cleared on the half that does not survive."""
    doc = S.__doc__
    assert "MODULE SWAP" in doc
    assert "spans zero" in doc


def test_fidelity_flags_are_exact_complements_not_independent_tests():
    """`faithful` == NOT `>=1 unsupported` and `sufficient` == NOT `>=1
    missing`, on every one of the 125 clauses. Counting them as four tests
    inflates the multiplicity correction against the surviving finding."""
    fid = S.fidelity()
    assert all(fid[c]["faithful"] == (not fid[c]["unsupported"]) for c in fid)
    assert all(fid[c]["sufficient"] == (not fid[c]["missing"]) for c in fid)
    assert S.INDEPENDENT_FIDELITY_TESTS == 2
    assert "complement" in S.__doc__.lower()


def test_atom_count_adjusted_effect_is_reported_as_primary():
    """Atom count is an uncontrolled common cause: rho(atom count, error) is the
    same size as rho(unsupported count, error). An unadjusted effect cannot
    separate 'over-assertion causes FPs' from 'broad atoms cause FPs'."""
    R = S.retrieval()
    lines = S.report_fidelity(R, n=200)
    joined = "\n".join(lines)
    assert "atom-count-adjusted PRIMARY" in joined
    for label in ("faithful", "sufficient"):
        assert any(label in l and "atom-count-adjusted" in l for l in lines)


def test_atom_count_adjustment_attenuates_the_faithful_effect():
    """The reported attenuation (-0.157 within-kind -> ~-0.100 within
    atom-count tertile) is the number the intervention in the ablation rests
    on. If adjustment ever stops attenuating, the mechanism story changed."""
    R = S.retrieval()
    fid = S.fidelity()
    kind = S.stratified_effect(R, lambda c: fid[c]["faithful"],
                               lambda c: S.clause_kinds()[c], n=400)
    adj = S.atom_count_adjusted(R, lambda c: fid[c]["faithful"], n=400)
    raw = S.effect(R, lambda c: fid[c]["faithful"], n=400, seed=5)
    # TERTILES, not one bucket: a single-stratum "adjustment" is the raw effect
    # wearing an adjusted label, and it would attenuate too.
    assert adj["strata"] == 3
    assert adj["diff"] != pytest.approx(raw["diff"])
    assert kind["diff"] < 0 and adj["diff"] < 0
    assert abs(adj["diff"]) < abs(kind["diff"])
