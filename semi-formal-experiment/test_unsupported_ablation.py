"""Tests for `unsupported_ablation.py` — the rung "-1" over-assertion ablation.

The module answers one question: if over-assertion is what costs retrieval, does
DELETING the over-asserting atoms buy retrieval back? Three things can make that
measurement worthless, and each has tests here.

1. **The control.** Deleting atoms shrinks the prediction set, which moves
   precision and recall mechanically. Without a same-size deletion control the
   experiment measures "fewer atoms", not "fewer UNSUPPORTED atoms". A previous
   "decisive" measurement in this project collapsed for exactly that reason. The
   control must be RANDOM, must delete the SAME NUMBER of atoms FROM THE SAME
   CLAUSES, and must be reported as a DISTRIBUTION over draws.

2. **The attribution.** Mapping a judge's free-text `unsupported` phrase onto a
   specific atom is a judgement call. It must be validated on a hand-checked
   sample and its error rate reported, or the treatment arm is deleting
   arbitrary atoms with a scientific-sounding name.

3. **The power.** 125 of 587 clauses carry read-back labels, so any effect is
   diluted ~5x. The MDE must be stated BEFORE the effect, and it must come from
   the control's own null distribution rather than an assumed variance.

Plus the fence: the module reads the panel, so it is diagnostic-only exactly
like `weight_diag` and `sufficiency_vs_retrieval`, and no repo module may
import it.
"""
import glob
import os
import re

import pytest

import unsupported_ablation as A

REPO = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- the contract

def test_module_declares_itself_a_panel_reading_diagnostic():
    doc = A.__doc__
    assert "DIAGNOSTIC" in doc
    assert "invariant 9" in doc
    assert "may never inform the ontology" in doc


def test_no_repo_module_imports_this_diagnostic():
    offenders = []
    for path in glob.glob(os.path.join(REPO, "*.py")):
        name = os.path.basename(path)
        if name in ("unsupported_ablation.py", "test_unsupported_ablation.py"):
            continue
        with open(path) as fh:
            src = fh.read()
        if re.search(r"^\s*(import|from)\s+unsupported_ablation\b", src, re.M):
            offenders.append(name)
    assert offenders == [], f"the diagnostic has consumers: {offenders}"


def test_the_module_is_named_in_the_anti_cheat_forbidden_list():
    """`test_no_reference_leak.FORBIDDEN` is what stops a QUERY module reaching
    the panel by importing a diagnostic that already read it. A new
    panel-reading module that is not on that list is a new laundering path."""
    import test_no_reference_leak as L
    assert "unsupported_ablation" in L.FORBIDDEN


def test_it_scores_the_true_589_passage_universe_not_the_graded_subset():
    """`load_panel` is the graded subset; `load_true_panel` is the evaluation
    universe. Scoring the subset inflates every rate and is the exact defect the
    task named."""
    U = A.universe()
    assert len(U.passages) == 589
    assert len(U.cells) == 9


def test_the_scored_modules_are_the_compliant_ones():
    """`relevance.py` VIOLATES invariant 10. It is reported as a SECONDARY
    comparison only; the primary verdict is `combined` V1@any_atom."""
    assert A.MODULES == ("combined", "structural", "relevance")
    assert A.PRIMARY_MODULE == "combined"
    assert A.SECONDARY_MODULES == ("relevance",)


# ------------------------------------------------------------- attribution

def test_attribution_returns_one_decision_per_unsupported_phrase():
    """95 unsupported phrases in, 95 decisions out. A phrase silently dropped
    shrinks the treatment arm without moving any printed n."""
    rows = A.unsupported_phrases()
    assert len(rows) == 95
    att = A.attribution()
    assert len(att) == len(rows)
    assert set(att) == set(range(len(rows)))


def test_attribution_only_ever_names_an_atom_of_that_phrase_s_own_clause():
    rows = A.unsupported_phrases()
    ann = A.annotations()
    for i, (cid, _p) in enumerate(rows):
        j = A.attribution()[i]
        if j is not None:
            assert 0 <= j < len(ann[cid]), (i, cid, j)


def test_attribution_recovers_a_gloss_it_was_copied_from():
    """The read-back render prints `name [kind] -- gloss`, so an unsupported
    phrase is usually a paraphrase of one atom's gloss. If the scorer cannot
    match a phrase that IS a gloss, it cannot match a paraphrase of one."""
    atoms = [{"name": "tool_artifact",
              "gloss": "A program-generated artifact used to perform a task "
                       "for the assistant."},
             {"name": "program_generation",
              "gloss": "Generating an artifact through execution of a program."}]
    assert A.best_atom("Tool is a program-generated artifact", atoms)[0] == 0
    assert A.best_atom("Generating an artifact by executing a program",
                       atoms)[0] == 1


def test_attribution_declines_when_nothing_matches():
    """An unattributable phrase must come back as None, not as atom 0. Defaulting
    to the first atom would silently delete a well-supported atom in every clause
    the judge wrote something odd about."""
    atoms = [{"name": "tool_artifact", "gloss": "A program-generated artifact."}]
    idx, score = A.best_atom("Zebras migrate seasonally across grassland", atoms)
    assert idx is None
    assert score < A.MIN_ATTRIBUTION_SCORE


def test_hand_checked_attribution_sample_is_frozen_and_reproducible():
    """The sample the error rate is computed on must be the sample that was
    actually read, and it must be regenerable from a seed rather than a list
    someone could quietly extend after seeing the result."""
    assert set(A.HAND_ATTRIBUTION) == set(A.attribution_sample())
    assert len(A.HAND_ATTRIBUTION) == 30


def test_attribution_error_rate_is_measured_and_reported():
    """An unvalidated attribution is the mutant this test exists to catch: the
    module must publish how often the automatic attribution disagrees with the
    hand check, with an interval, and the report must print it."""
    v = A.validate_attribution()
    assert v["n"] == 30
    assert 0.0 <= v["accuracy"] <= 1.0
    assert v["lo"] <= v["accuracy"] <= v["hi"]
    txt = "\n".join(A.report_attribution())
    assert "attribution accuracy" in txt.lower()
    assert "hand-checked" in txt.lower()


def test_attribution_is_good_enough_to_carry_the_treatment_arm():
    """If this ever drops below ~0.8 the clause-level fallback is the honest
    analysis and the atom-level arm must be withdrawn."""
    v = A.validate_attribution()
    assert v["accuracy"] >= 0.8


# ------------------------------------------------------------ the drop sets

def test_treatment_drop_set_is_the_attributed_atoms():
    drop = A.drop_unsupported()
    att = A.attribution()
    rows = A.unsupported_phrases()
    want = {}
    for i, (cid, _p) in enumerate(rows):
        if att[i] is not None:
            want.setdefault(cid, set()).add(att[i])
    assert drop == want
    assert A.drop_size(drop) > 0


def test_random_control_deletes_the_same_count_from_the_same_clauses():
    """THE CONTROL. Same number of atoms, same clauses, chosen at random. A
    control that deletes a different number, or deletes from clauses the
    treatment never touched, is not a control for 'fewer atoms'."""
    t = A.drop_unsupported()
    for seed in (1, 2, 3):
        c = A.drop_random(t, seed=seed)
        assert set(c) == set(t)
        assert {k: len(v) for k, v in c.items()} == {k: len(v) for k, v in t.items()}
        assert A.drop_size(c) == A.drop_size(t)


def test_random_control_actually_varies_with_the_seed():
    """A 'random' control that returns the treatment set, or the same set every
    time, could not have come out any other way — the failure mode the task
    names explicitly."""
    t = A.drop_unsupported()
    draws = [A.drop_random(t, seed=s) for s in range(8)]
    assert any(d != t for d in draws)
    assert len({tuple(sorted((k, tuple(sorted(v))) for k, v in d.items()))
                for d in draws}) > 1


def test_random_control_only_picks_atoms_that_exist():
    t = A.drop_unsupported()
    ann = A.annotations()
    c = A.drop_random(t, seed=99)
    for cid, idxs in c.items():
        assert all(0 <= i < len(ann[cid]) for i in idxs)


def test_df_controls_are_count_matched_and_extreme():
    """The DF controls answer 'is this just deleting rare/common atoms?'. They
    must delete the same count per clause, and the low arm must have a strictly
    lower total document frequency than the high arm."""
    t = A.drop_unsupported()
    lo = A.drop_by_df(t, highest=False)
    hi = A.drop_by_df(t, highest=True)
    for c in (lo, hi):
        assert {k: len(v) for k, v in c.items()} == {k: len(v) for k, v in t.items()}
    df = A.atom_df()
    ann = A.annotations()

    def total(d):
        return sum(df[ann[cid][i]["name"]] for cid, idxs in d.items() for i in idxs)
    assert total(lo) < total(hi)


# ---------------------------------------------------------------- ablation

def test_ablation_removes_exactly_the_named_atoms_and_nothing_else():
    ann = A.annotations()
    drop = {"m0067": {0}}
    out = A.ablate(ann, drop)
    assert len(out["m0067"]) == len(ann["m0067"]) - 1
    assert ann["m0067"][0] not in out["m0067"]
    assert out["m0067"] == [a for i, a in enumerate(ann["m0067"]) if i != 0]
    for cid in ann:
        if cid != "m0067":
            assert out[cid] == ann[cid]


def test_ablation_does_not_mutate_the_shipped_annotations():
    ann = A.annotations()
    before = {c: len(v) for c, v in ann.items()}
    A.ablate(ann, A.drop_unsupported())
    assert {c: len(v) for c, v in A.annotations().items()} == before


def test_empty_ablation_reproduces_the_baseline_exactly():
    """The zero-deletion ablation must score identically to the baseline. If it
    does not, the scorer is not a function of the annotations alone and every
    delta below is contaminated."""
    U = A.universe()
    base = A.score(A.annotations(), A.PRIMARY_MODULE, U)
    same = A.score(A.ablate(A.annotations(), {}), A.PRIMARY_MODULE, U)
    assert base == same


def test_score_reports_fp_fn_and_the_readback_restricted_view():
    """Deletion can only act on the 125 read-back clauses, so the whole-universe
    number is ~5x diluted. Both must be reported or the dilution is invisible."""
    U = A.universe()
    s = A.score(A.annotations(), A.PRIMARY_MODULE, U)
    assert s["fp"] + s["fn"] == s["err"]
    assert s["trials"] == len(U.passages) * len(U.cells)
    assert s["rate"] == pytest.approx(s["err"] / s["trials"])
    assert 0 < s["readback_trials"] < s["trials"]
    assert s["readback_err"] <= s["err"]


# ------------------------------------------------------------------- power

def test_mde_comes_from_the_control_null_and_is_reported_first():
    """The honest MDE here is the spread of the CONTROL's own effect over draws.
    An assumed variance would be a guess; the null distribution is measured."""
    r = A.run(draws=6, modules=(A.PRIMARY_MODULE,))
    m = r["modules"][A.PRIMARY_MODULE]
    assert m["control"]["n_draws"] == 6
    assert "mde" in m and m["mde"] > 0
    # the SD of the control's own deltas, not an assumed variance
    assert m["mde"] == pytest.approx(2.8016 * m["control"]["sd"], rel=1e-3)
    lines = A.report(r)
    power = next(i for i, l in enumerate(lines) if l.startswith("POWER"))
    first_module = next(i for i, l in enumerate(lines) if l.startswith("MODULE:"))
    verdict = next(i for i, l in enumerate(lines) if "VERDICT" in l)
    assert power < first_module < verdict
    assert "READ BEFORE THE EFFECT" in lines[power]


def test_run_reports_the_control_as_a_distribution_not_a_point():
    r = A.run(draws=6, modules=(A.PRIMARY_MODULE,))
    c = r["modules"][A.PRIMARY_MODULE]["control"]
    assert len(c["deltas"]) == 6
    for k in ("mean", "sd", "lo", "hi"):
        assert k in c


def test_run_measures_the_treatment_against_the_control_not_against_baseline():
    """`delta` alone is 'fewer atoms'. The reported effect must be the treatment
    delta MINUS the control's mean delta, and the report must say so."""
    r = A.run(draws=6, modules=(A.PRIMARY_MODULE,))
    m = r["modules"][A.PRIMARY_MODULE]
    assert m["adjusted"] == pytest.approx(m["treatment"]["delta"]
                                          - m["control"]["mean"])
    # and `delta` must be the real change in the reported metric, not a constant
    assert m["treatment"]["delta"] == pytest.approx(m["treatment"][r["metric"]])
    assert m["treatment"]["delta"] != 0.0
    assert m["lowest_df"]["delta"] != m["highest_df"]["delta"]
    txt = "\n".join(A.report(r))
    assert "vs control" in txt.lower()


def test_verdict_is_stated_against_the_mde_and_can_say_it_cannot_resolve():
    """'This design cannot resolve the effect' is a legitimate answer and the
    module must be able to print it."""
    r = A.run(draws=6, modules=(A.PRIMARY_MODULE,))
    txt = "\n".join(A.report(r))
    assert "VERDICT" in txt
    assert re.search(r"CANNOT RESOLVE|IMPROVES|WORSENS", txt)


def test_main_runs_offline_and_prints_the_fence(capsys):
    A.main(["--fast"])
    out = capsys.readouterr().out
    assert "DIAGNOSTIC" in out
    assert "VERDICT" in out
    assert "attribution accuracy" in out.lower()


# --------------------------------------------- the attribution cannot self-validate

def test_validation_reads_the_hand_labels_not_the_automatic_output():
    """The mutant this catches: `validate_attribution` scoring the automatic
    attribution against ITSELF, which reports 1.000 forever. Flip one hand label
    to a value the rule cannot have produced and the accuracy must drop."""
    real = dict(A.HAND_ATTRIBUTION)
    i = sorted(real)[0]
    bad = -99 if real[i] != -99 else -98
    A.HAND_ATTRIBUTION[i] = bad
    try:
        v = A.validate_attribution()
        assert v["accuracy"] < 1.0
        assert i in v["misses"]
    finally:
        A.HAND_ATTRIBUTION.clear()
        A.HAND_ATTRIBUTION.update(real)


def test_hand_labels_are_not_a_copy_of_the_automatic_attribution():
    """A hand check that agrees with the rule on every single case is either a
    perfect rule or a transcription of the rule's output. At least one
    disagreement is what shows a human actually read them."""
    att = A.attribution()
    assert any(A.HAND_ATTRIBUTION[i] != att[i] for i in A.HAND_ATTRIBUTION)


# ------------------------------------------------- the document-frequency profile

def test_every_arm_reports_the_document_frequency_of_what_it_deleted():
    """The decisive comparison is not treatment-vs-baseline, it is what the
    treatment deletes vs what the DF arms delete. If deleting the commonest
    atoms beats deleting the unsupported ones, the mechanism is atom BREADTH,
    not over-assertion, and the report must make that visible."""
    t = A.drop_unsupported()
    p = A.df_profile(t)
    assert p["n"] == A.drop_size(t)
    assert p["mean"] > 0
    lo = A.df_profile(A.drop_by_df(t, highest=False))
    hi = A.df_profile(A.drop_by_df(t, highest=True))
    assert lo["mean"] < p["mean"] < hi["mean"]
    r = A.run(draws=4, modules=(A.PRIMARY_MODULE,))
    txt = "\n".join(A.report(r))
    assert "mean DF" in txt


def test_the_verdict_is_recorded_in_the_module_not_in_a_chat_message():
    """The repo convention: the answer lives in the module a reviewer can run.
    A docstring that still promises a measurement is a conclusion the next agent
    has to re-derive."""
    doc = A.__doc__
    assert "THE ANSWER IS NO" in doc
    assert "indistinguishable from" in doc
    assert "WHAT THIS DOES AND DOES NOT ESTABLISH" in doc


def test_the_recorded_verdict_still_matches_what_the_module_computes():
    """The docstring says the treatment lands inside the random control's noise
    under the PRIMARY module. If that ever stops being true the docstring is a
    stale constant, which is the failure mode LADDER_PLAN names last."""
    r = A.run(draws=12, modules=(A.PRIMARY_MODULE,))
    m = r["modules"][A.PRIMARY_MODULE]
    assert abs(m["adjusted"]) < m["mde"]
    # and the DF arm beats the flagged arm — the mechanism claim in the docstring
    assert m["highest_df"]["delta"] < m["treatment"]["delta"]
    assert m["lowest_df"]["delta"] > m["treatment"]["delta"]
