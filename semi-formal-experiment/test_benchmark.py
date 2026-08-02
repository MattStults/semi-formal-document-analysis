"""Tests for benchmark.py. Hand-computed arithmetic on synthetic fixtures —
nothing here depends on a model, an API, or (except where marked) the real
panel file."""
from __future__ import annotations

import collections
import json

import pytest

import benchmark as B


def _p(name):
    import os
    return os.path.join(os.path.dirname(os.path.abspath(B.__file__)), name)


# ------------------------------------------------------------- fixtures

def mk_passage(pid, verdicts, quote, example_block=False):
    return {"id": pid, "locator": f"loc/{pid}", "quote": quote,
            "exampleBlock": example_block, "adjacent": False,
            "verdicts": dict(verdicts), "score": sum(verdicts.values())}


@pytest.fixture
def behaviour():
    """3 judges (a, b, c), 6 passages, scores hand-set to exercise both the
    >=5 cutoff and the ==6 strict cutoff."""
    ps = [
        mk_passage("p1", {"a": 2, "b": 2, "c": 2}, "alpha clause one"),      # 6
        mk_passage("p2", {"a": 2, "b": 2, "c": 1}, "beta clause two"),       # 5
        mk_passage("p3", {"a": 2, "b": 1, "c": 1}, "gamma clause three"),    # 4
        mk_passage("p4", {"a": 1, "b": 0, "c": 0}, "delta clause four"),     # 1
        mk_passage("p5", {"a": 2, "b": 2, "c": 2}, "in an example block",
                   example_block=True),                                       # 6
        mk_passage("p6", {"a": 2, "b": 2, "c": 2}, "not present anywhere"),   # 6
    ]
    return {"slug": "synthetic", "coverage": {"openai": {"passages": ps}}}


@pytest.fixture
def clauses():
    return [
        {"id": "c1", "quote": "alpha clause one", "marked_span": None},
        {"id": "c2", "quote": "beta clause two", "marked_span": None},
        {"id": "c3", "quote": "gamma clause three", "marked_span": None},
        {"id": "cx", "quote": "unrelated clause", "marked_span": None},
    ]


@pytest.fixture
def spec():
    # p6's quote is deliberately absent; p5's quote is present verbatim but
    # unsegmented (no clause covers it) AND flagged exampleBlock, so it must
    # land in example_block, which takes precedence.
    return ("alpha clause one\nbeta clause two\ngamma clause three\n"
            "delta clause four\nin an example block\nunrelated clause\n"
            "verbatim but nobody segmented this\n")


# ------------------------------------------------- reference sets (cap. 1)

def test_reference_threshold_is_a_parameter(behaviour):
    assert B.reference_ids(behaviour, 5) == {"p1", "p2", "p5", "p6"}
    assert B.reference_ids(behaviour, 4) == {"p1", "p2", "p3", "p5", "p6"}
    assert B.reference_ids(behaviour, 1) == {"p1", "p2", "p3", "p4", "p5", "p6"}


def test_strict_reference_is_unanimous_at_maximum(behaviour):
    assert B.max_score(behaviour) == 6
    assert {p["id"] for p in B.strict_reference(behaviour)} == {"p1", "p5", "p6"}


def test_judges_read_from_data_not_hardcoded(behaviour):
    assert B.judges(behaviour) == ["a", "b", "c"]
    odd = {"slug": "x", "coverage": {"openai": {"passages": [
        mk_passage("q1", {"opus": 2, "kimi-k2": 1}, "z")]}}}
    assert B.judges(odd) == ["kimi-k2", "opus"]
    assert B.max_score(odd) == 4


@pytest.mark.parametrize("thresh,expected", [(5, 4), (6, 3)])
def test_threshold_sensitivity_reported_for_same_input(behaviour, clauses, spec,
                                                       thresh, expected):
    m = B.map_reference(behaviour, clauses, thresh, spec)
    assert m["n_reference"] == expected


def test_report_prints_both_thresholds(behaviour, clauses, spec):
    md = B.report({"synthetic": behaviour}, clauses, spec=spec)
    assert ">=5" in md and ">=6" in md


# ------------------------------------------- precision / recall (cap. 3)

def test_prf_hand_computed():
    # ref = {1,2,3,4}; predicted = {1,2,5}  -> tp 2, fp 1, fn 2
    m = B.prf({1, 2, 5}, {1, 2, 3, 4})
    assert (m["tp"], m["fp"], m["fn"]) == (2, 1, 2)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["recall"] == pytest.approx(0.5)
    assert m["f1"] == pytest.approx(2 * (2 / 3) * 0.5 / ((2 / 3) + 0.5))


def test_perfect_predictor_scores_one(behaviour, clauses, spec):
    mp = B.map_reference(behaviour, clauses, 5, spec)
    r = B.score_tool(mp["clause_ids"], behaviour, clauses, 5, spec)
    assert r["matched"]["precision"] == 1.0
    assert r["matched"]["recall"] == 1.0
    assert r["matched"]["f1"] == 1.0
    # ...but NOT over the full reference set: p5/p6 are unreachable.
    assert r["full"]["recall"] < 1.0
    assert r["coverage_cost_recall"] > 0


def test_empty_predictor_is_zero_recall_no_zero_division(behaviour, clauses, spec):
    r = B.score_tool(set(), behaviour, clauses, 5, spec)
    assert r["matched"]["recall"] == 0.0
    assert r["matched"]["precision"] == 0.0
    assert r["matched"]["f1"] == 0.0
    assert r["full"]["recall"] == 0.0


def test_empty_reference_and_empty_prediction_do_not_divide_by_zero(behaviour,
                                                                   clauses, spec):
    r = B.score_tool(set(), behaviour, clauses, 99, spec)
    assert r["n_reference_passages"] == 0
    assert r["matched"]["recall"] == 0.0
    assert r["passage_level"]["recall_full"] == 0.0


def test_partial_predictor_hand_computed(behaviour, clauses, spec):
    # reference >=5 maps to clauses {c1, c2}. Predict {c1, cx}: tp 1, fp 1, fn 1.
    r = B.score_tool({"c1", "cx"}, behaviour, clauses, 5, spec)
    assert r["n_reference_clauses"] == 2
    assert (r["matched"]["tp"], r["matched"]["fp"], r["matched"]["fn"]) == (1, 1, 1)
    assert r["matched"]["precision"] == pytest.approx(0.5)
    assert r["matched"]["recall"] == pytest.approx(0.5)
    # full: 2 unmatched reference passages become extra false negatives
    assert r["full"]["fn"] == 3
    assert r["full"]["recall"] == pytest.approx(0.25)
    assert r["full"]["precision"] == pytest.approx(0.5)


def test_passage_level_recall(behaviour, clauses, spec):
    r = B.score_tool({"c1"}, behaviour, clauses, 5, spec)
    assert r["passage_level"]["hit"] == 1
    assert r["passage_level"]["recall_matched"] == pytest.approx(0.5)   # of 2
    assert r["passage_level"]["recall_full"] == pytest.approx(0.25)     # of 4


# ------------------------------------------- zero-match accounting (cap. 4)

def test_zero_match_strata_counted_and_never_dropped(behaviour, clauses, spec):
    m = B.map_reference(behaviour, clauses, 5, spec)
    assert m["n_reference"] == 4
    assert m["n_matched"] == 2
    assert sorted(m["unmatched"]) == ["p5", "p6"]
    assert m["strata"]["example_block"] == 1
    assert m["strata"]["not_verbatim_in_source"] == 1
    assert m["strata"]["verbatim_but_unsegmented"] == 0
    # the ledger must balance: every unmatched passage lands in exactly one bin
    assert sum(m["strata"].values()) == len(m["unmatched"])
    assert m["n_matched"] + len(m["unmatched"]) == m["n_reference"]


def test_verbatim_but_unsegmented_stratum(clauses, spec):
    p = mk_passage("pv", {"a": 2, "b": 2, "c": 2},
                   "verbatim but nobody segmented this")
    b = {"slug": "s", "coverage": {"openai": {"passages": [p]}}}
    m = B.map_reference(b, clauses, 5, spec)
    assert m["strata"]["verbatim_but_unsegmented"] == 1
    assert m["strata"]["not_verbatim_in_source"] == 0
    assert m["strata"]["example_block"] == 0


def test_unmatched_appear_in_report_and_in_full_denominator(behaviour, clauses, spec):
    md = B.report({"synthetic": behaviour}, clauses,
                  predictions={"synthetic": {"c1", "c2"}}, spec=spec)
    assert "Zero-match accounting" in md
    assert "verbatim_but_unsegmented" in md
    assert "| full |" in md


def test_normalization_footnotes_and_hardwrap(clauses):
    """Panel quotes lack the source's inline [^xxxx] markers and the source
    hard-wraps; the join must survive both."""
    rows = [{"id": "cf", "quote": "the assistant[^abc1] should\nnot lie",
             "marked_span": None}]
    hits = B.inventory.match_passage("the assistant should not lie", rows)
    assert [h["id"] for h in hits] == ["cf"]


# ------------------------------------------- panel agreement (cap. 2)

@pytest.fixture
def agreement_fixture():
    """Hand-built so leave-one-out is computable on paper.

    At threshold >=1:
      a = {p1,p2,p3,p4}   b = {p1,p2,p3}   c = {p1,p2}
    LOO for a: consensus(b,c) = {p1,p2}. tp 2, fp 2, fn 0
               -> P 0.5, R 1.0, F1 2/3, Jaccard 2/4 = 0.5
    LOO for c: consensus(a,b) = {p1,p2,p3}. tp 2, fp 0, fn 1
               -> P 1.0, R 2/3, F1 0.8, Jaccard 2/3
    Pairwise a|b = 3/4, a|c = 2/4, b|c = 2/3.
    """
    ps = [
        mk_passage("p1", {"a": 2, "b": 2, "c": 2}, "q1"),
        mk_passage("p2", {"a": 2, "b": 1, "c": 1}, "q2"),
        mk_passage("p3", {"a": 1, "b": 1, "c": 0}, "q3"),
        mk_passage("p4", {"a": 1, "b": 0, "c": 0}, "q4"),
    ]
    return {"slug": "agree", "coverage": {"openai": {"passages": ps}}}


def test_pairwise_jaccard_hand_computed(agreement_fixture):
    ag = B.panel_agreement(agreement_fixture)
    pw = ag["pairwise"][1]
    assert pw["a|b"] == pytest.approx(3 / 4)
    assert pw["a|c"] == pytest.approx(2 / 4)
    assert pw["b|c"] == pytest.approx(2 / 3)


def test_leave_one_out_hand_computed(agreement_fixture):
    loo = B.panel_agreement(agreement_fixture)["leave_one_out"][1]
    a = loo["a"]
    assert a["others"] == ["b", "c"]
    assert (a["tp"], a["fp"], a["fn"]) == (2, 2, 0)
    assert a["precision"] == pytest.approx(0.5)
    assert a["recall"] == pytest.approx(1.0)
    assert a["f1"] == pytest.approx(2 / 3)
    assert a["jaccard"] == pytest.approx(0.5)

    c = loo["c"]
    assert (c["tp"], c["fp"], c["fn"]) == (2, 0, 1)
    assert c["precision"] == pytest.approx(1.0)
    assert c["recall"] == pytest.approx(2 / 3)
    assert c["f1"] == pytest.approx(0.8)
    assert c["jaccard"] == pytest.approx(2 / 3)


def test_leave_one_out_at_max_threshold(agreement_fixture):
    """At ==2 only p1 is unanimous; b and c each rate only p1 at 2, a rates
    p1,p2. LOO for a: consensus(b,c) = {p1}; tp 1, fp 1, fn 0."""
    loo = B.panel_agreement(agreement_fixture)["leave_one_out"][2]
    assert (loo["a"]["tp"], loo["a"]["fp"], loo["a"]["fn"]) == (1, 1, 0)
    assert loo["b"]["jaccard"] == pytest.approx(1.0)


def test_loo_mean(agreement_fixture):
    ag = B.panel_agreement(agreement_fixture)
    b_f1 = ag["leave_one_out"][1]["b"]["f1"]
    expected = (2 / 3 + b_f1 + 0.8) / 3
    assert B.loo_mean(ag, 1) == pytest.approx(expected)


def test_agreement_block_labels_loo_as_the_bar(agreement_fixture):
    md = B.report({"agree": agreement_fixture}, [], spec="")
    assert "Leave-one-out" in md
    assert "THE BAR" in md


# ------------------------------------------- clause loading (defensive)

def test_load_clauses_falls_back_when_file_absent(tmp_path):
    rows, src = B.load_clauses(str(tmp_path / "nope.json"))
    assert src == "modelspec_focus_areas.json"
    assert rows and all("id" in r and "quote" in r for r in rows)


def test_load_clauses_accepts_list_and_wrapped_shapes(tmp_path):
    for payload in (
        [{"id": "c1", "text": "hello"}],
        {"clauses": [{"clause_id": "c1", "clause_text": "hello"}]},
        {"rows": [{"focus_id": "c1", "quote": "hello"}]},
    ):
        p = tmp_path / "clauses.json"
        p.write_text(json.dumps(payload))
        rows, src = B.load_clauses(str(p))
        assert src == "clauses.json"
        assert rows[0]["id"] == "c1" and rows[0]["quote"] == "hello"
        assert rows[0]["marked_span"] is None


def test_load_clauses_skips_rows_without_id_or_text(tmp_path):
    p = tmp_path / "clauses.json"
    p.write_text(json.dumps([{"id": "c1", "quote": "ok"}, {"quote": "no id"},
                             {"id": "c2"}]))
    rows, _ = B.load_clauses(str(p))
    assert [r["id"] for r in rows] == ["c1"]


# ------------------------------------------- real data (integration)

def test_real_panel_loads_and_agrees_with_itself():
    panel = B.load_panel()
    assert set(panel) == {"helpfulness", "harm-avoidance-to-third-parties",
                          "avoiding-over-and-under-caution"}
    total = sum(len(B.passages(b)) for b in panel.values())
    assert total == 863
    assert sum(len(B.reference(b, 5)) for b in panel.values()) == 112
    for b in panel.values():
        ag = B.panel_agreement(b)
        assert len(ag["judges"]) == 3
        for t in B.THRESHOLDS:
            for m in ag["leave_one_out"][t].values():
                assert 0.0 <= m["f1"] <= 1.0


def test_real_zero_match_ledger_balances():
    panel = B.load_panel()
    clauses, _ = B.load_clauses()
    spec = B.spec_text()
    assert spec, "model_spec.md must be readable for strata classification"
    for b in panel.values():
        for t in (5, B.max_score(b)):
            m = B.map_reference(b, clauses, t, spec)
            assert sum(m["strata"].values()) == len(m["unmatched"])
            assert m["strata"]["unknown"] == 0
            assert m["n_matched"] + len(m["unmatched"]) == m["n_reference"]


# =====================================================================
#  Pair-gold protocol: the ONLY basis on which tool and judge are
#  comparable. Gold lives on passages, the tool predicts clauses, and
#  every number below is computed on the panel's own passage denominator.
# =====================================================================

def mk_role(score, entries):
    """`role` free text in the panel's format. `entries` is [(judge, label)]."""
    head = f"Model determined relevance (score {score}/6):"
    mark = {"core": "✓", "related": "~", "not relevant": "✗"}
    body = [f"{mark[lab]} {j} — {lab}" for j, lab in entries]
    return "\n".join([head] + body)


@pytest.fixture
def role_behaviour():
    """Judges named only in `role` free text, with all three label levels."""
    ps = []
    for pid, entries in [
        ("r1", [("GPT-5.6 Sol", "core"), ("Kimi-K3", "core"),
                ("Claude Fable 5", "core")]),                       # 6
        ("r2", [("GPT-5.6 Sol", "core"), ("Kimi-K3", "related"),
                ("Claude Fable 5", "not relevant")]),               # 3
        ("r3", [("GPT-5.6 Sol", "related"), ("Kimi-K3", "not relevant"),
                ("Claude Fable 5", "not relevant")]),               # 1
    ]:
        score = sum({"core": 2, "related": 1, "not relevant": 0}[l]
                    for _, l in entries)
        ps.append({"id": pid, "quote": f"quote {pid}", "exampleBlock": False,
                   "role": mk_role(score, entries), "score": score})
    return {"slug": "roles", "coverage": {"openai": {"passages": ps}}}


def test_judge_names_are_read_from_role_text(role_behaviour):
    assert B.panel_judge_names(role_behaviour) == [
        "Claude Fable 5", "GPT-5.6 Sol", "Kimi-K3"]


def test_role_labels_are_three_levels(role_behaviour):
    ps = B.passages(role_behaviour)
    names = B.panel_judge_names(role_behaviour)
    assert B.judge_labels(ps[1]["role"], names) == {
        "GPT-5.6 Sol": 2, "Kimi-K3": 1, "Claude Fable 5": 0}


def test_role_parse_reconstructs_published_score(role_behaviour):
    v = B.verify_role_parse(role_behaviour)
    assert v["total"] == 3 and v["reconstructed"] == 3 and v["mismatch"] == []


def test_role_parse_reconstructs_all_863_real_passages():
    """If this fails the parser is wrong, not the panel."""
    total = ok = 0
    for b in B.load_panel().values():
        v = B.verify_role_parse(b)
        total += v["total"]
        ok += v["reconstructed"]
        assert v["mismatch"] == [], v["mismatch"][:3]
    assert (ok, total) == (863, 863)


def test_real_panels_differ_per_behaviour():
    """Hardcoding one panel silently zeroes the other two behaviours."""
    names = {slug: B.panel_judge_names(b) for slug, b in B.load_panel().items()}
    assert all(len(v) == 3 for v in names.values())
    assert len(set(map(tuple, names.values()))) == 3
    assert "Claude Opus 4.8" in names["harm-avoidance-to-third-parties"]
    assert "Kimi-K2.6" in names["avoiding-over-and-under-caution"]


# ------------------------------------------------------- pair-gold targets

def test_pair_targets_gold_is_both_others_not_either(agreement_fixture):
    """a={p1..p4} b={p1,p2,p3} c={p1,p2} at >=1.
    gold for a = b AND c = {p1,p2}; gold for c = a AND b = {p1,p2,p3}."""
    t = B.pair_targets(agreement_fixture)
    assert t["a"]["gold"] == {"p1", "p2"}
    assert t["a"]["others"] == ["b", "c"]
    assert t["c"]["gold"] == {"p1", "p2", "p3"}


def test_judge_loo_matches_panel_agreement(agreement_fixture):
    loo = B.judge_loo(agreement_fixture)
    old = B.panel_agreement(agreement_fixture)["leave_one_out"][1]
    for j in loo:
        assert loo[j]["f1"] == pytest.approx(old[j]["f1"])


def test_real_bar_reproduces_the_quoted_numbers():
    """0.764 / 0.780 / 0.500 — best single judge, not the panel mean."""
    expected = {"helpfulness": (0.764, 0.636),
                "harm-avoidance-to-third-parties": (0.780, 0.697),
                "avoiding-over-and-under-caution": (0.500, 0.419)}
    for slug, b in B.load_panel().items():
        loo = B.judge_loo(b)
        best = max(m["f1"] for m in loo.values())
        mean = sum(m["f1"] for m in loo.values()) / len(loo)
        assert best == pytest.approx(expected[slug][0], abs=5e-4)
        assert mean == pytest.approx(expected[slug][1], abs=5e-4)


# ----------------------------------------------- clause -> passage lifting

def test_passage_is_predicted_if_any_joining_clause_is(behaviour, clauses):
    joins = B.clause_joins(behaviour, clauses)
    assert joins["p1"] == ["c1"]
    assert joins["p6"] == []          # not in the spec at all
    assert B.lift(set(), joins) == set()
    assert B.lift({"c1"}, joins) == {"p1"}
    assert B.lift({"c1", "c2", "cx"}, joins) == {"p1", "p2"}


def test_unjoinable_passages_can_never_be_predicted(behaviour, clauses):
    joins = B.clause_joins(behaviour, clauses)
    everything = {c["id"] for c in clauses}
    assert "p6" not in B.lift(everything, joins)
    assert B.joinable(joins) == {"p1", "p2", "p3"}


# ------------------------------------------------------------- evaluation

def test_evaluate_reports_matched_and_full_and_they_differ(behaviour, clauses):
    ev = B.evaluate(behaviour, {"c1", "c2"}, clauses)
    for j, row in ev["per_target"].items():
        assert "matched" in row and "full" in row
    assert ev["tool_mean_matched"] != ev["tool_mean_full"]
    assert ev["tool_mean_matched"] > ev["tool_mean_full"], \
        "unjoinable gold passages must cost recall on the full reference"


def test_empty_prediction_scores_zero_not_one(behaviour, clauses):
    """The jaccard({},{})==1.0 bug class: a metric must read WORST when the
    system fails worst."""
    ev = B.evaluate(behaviour, set(), clauses)
    assert ev["tool_mean_full"] == 0.0
    assert ev["tool_mean_matched"] == 0.0
    for row in ev["per_target"].values():
        assert row["full"]["f1"] == 0.0
        assert row["full"]["precision"] == 0.0
        assert row["full"]["recall"] == 0.0
    assert ev["tool_mean_full"] < ev["floor_mean"], \
        "predicting nothing must be worse than the degenerate floor"


def test_predict_everything_lands_on_the_floor_not_a_good_score(behaviour,
                                                                clauses):
    """The mirror bug: marking everything relevant must show precision at the
    base rate and an F1 exactly on the degenerate floor 2p/(1+p)."""
    ev = B.evaluate(behaviour, {c["id"] for c in clauses}, clauses)
    for j, row in ev["per_target"].items():
        base = row["gold_matched"] / row["n_matched"]
        assert row["matched"]["precision"] == pytest.approx(base)
        assert row["matched"]["recall"] == pytest.approx(1.0)
        assert row["matched"]["f1"] == pytest.approx(2 * base / (1 + base))
        assert row["floor_matched"] == pytest.approx(2 * base / (1 + base))


def test_floor_is_reported_for_every_target(behaviour, clauses):
    ev = B.evaluate(behaviour, {"c1"}, clauses)
    for row in ev["per_target"].values():
        assert 0.0 < row["floor_full"] <= 1.0
        assert 0.0 < row["floor_matched"] <= 1.0
    assert ev["floor_mean"] > 0


def test_evaluate_counts_join_losses(behaviour, clauses):
    ev = B.evaluate(behaviour, {"c1"}, clauses)
    j = ev["join"]
    assert j["n_passages"] == 6
    assert j["n_joinable"] == 3
    assert j["n_unjoinable"] == 3
    assert sum(j["strata"].values()) == 3


# --------------------------------------------------------------- reporting

def test_headline_table_shows_tool_judge_and_floor(behaviour, clauses):
    md = B.headline_table({"synthetic": B.evaluate(behaviour, {"c1"}, clauses)})
    assert "FLOOR" in md
    assert "MCC" in md, "MCC is the primary metric and must lead the table"
    assert "mean LOO" in md, "the judge aggregate is the mean LOO, not the best"
    assert "matched" in md and "full" in md


def test_report_never_emits_matched_without_full(behaviour, clauses, spec):
    md = B.report({"synthetic": behaviour}, clauses,
                  predictions={"synthetic": {"c1"}}, spec=spec)
    assert B.check_report_pairing(md) is True
    # and the guard has teeth: strip the full-reference rows and it must fail
    stripped = "\n".join(l for l in md.split("\n") if "full" not in l.lower())
    with pytest.raises(AssertionError):
        B.check_report_pairing(stripped)


def test_report_carries_the_headline_table_when_a_prediction_is_given(
        behaviour, clauses, spec):
    md = B.report({"synthetic": behaviour}, clauses,
                  predictions={"synthetic": {"c1"}}, spec=spec)
    assert "FLOOR" in md
    assert "judged relevant" in md.lower() or "unjoinable" in md.lower()


def test_role_labels_agree_with_the_structured_verdicts_field():
    """Two independent renderings of the same judgements; if they disagree the
    bar is being computed off the wrong one."""
    for b in B.load_panel().values():
        alias = B.align_judges(b)
        assert len(alias) == 3
        names = B.panel_judge_names(b)
        for p in B.passages(b):
            lab = B.judge_labels(p.get("role"), names)
            for key, name in alias.items():
                assert (p.get("verdicts") or {}).get(key, 0) == lab.get(name, 0)


# ------------------------------------------- data integrity / spec swap

def test_verdicts_sum_to_the_published_score_everywhere():
    """1336 passages across both spec sides, 0 missing, 0 mismatched. If this
    fails the panel file changed and the benchmark must refuse to run rather
    than silently mis-score."""
    total = 0
    for b in B.load_panel().values():
        for key in B.spec_keys(b):
            v = B.verify_verdicts(b, key)
            assert v["mismatch"] == [], (key, v["mismatch"][:3])
            assert v["missing_verdicts"] == []
            total += v["total"]
    assert total == 1336


def test_openai_side_is_863():
    assert sum(len(B.passages(b)) for b in B.load_panel().values()) == 863


def test_spec_key_is_a_parameter_not_a_hardcode():
    """The Anthropic panel must stay reachable — the tool is required to be
    spec-swappable."""
    panel = B.load_panel()
    assert all("anthropic" in B.spec_keys(b) for b in panel.values())
    other = sum(len(B.passages(b, "anthropic")) for b in panel.values())
    assert other > 0 and other != 863
    b = panel["helpfulness"]
    assert B.judges(b, "anthropic")
    assert B.pair_targets(b, spec_key="anthropic")
    assert B.passages(b, "no-such-spec") == []


def test_judge_panels_differ_per_behaviour_in_verdicts_too():
    names = {slug: tuple(B.judges(b)) for slug, b in B.load_panel().items()}
    assert len(set(names.values())) == 3
    assert "opus" in names["harm-avoidance-to-third-parties"]
    assert "kimi-k2" in names["avoiding-over-and-under-caution"]


# ------------------------------------------- sweep / vocabulary / control

def test_sweep_report_prints_every_threshold_not_just_the_best(behaviour,
                                                               clauses, spec):
    sweeps = {"synthetic": [(0.0, {"c1", "c2", "c3", "cx"}),
                            (0.5, {"c1", "c2"}),
                            (0.9, {"c1"})]}
    md = B.sweep_report({"synthetic": behaviour}, clauses, sweeps, spec)
    assert md.count("| synthetic |") == 3
    assert "FLOOR" in md
    assert "F1 full" in md and "F1 matched" in md
    B.check_report_pairing(md)


def test_sweep_recall_is_monotone_non_increasing(behaviour, clauses, spec):
    joins = B.clause_joins(behaviour, clauses)
    rec = []
    for pred in ({"c1", "c2", "c3", "cx"}, {"c1", "c2"}, {"c1"}, set()):
        ev = B.evaluate(behaviour, pred, clauses, spec, joins=joins)
        rows = ev["per_target"].values()
        rec.append(sum(r["full"]["recall"] for r in rows) / len(rows))
    assert rec == sorted(rec, reverse=True)


def test_vocabulary_block_flags_stopword_atoms():
    import relevance as R
    cs = [{"id": f"c{i}", "quote": "x", "section_path": ["S"]} for i in range(8)]
    ann = {c["id"]: [{"name": "user"}] for c in cs}
    ann["c0"].append({"name": "rare_atom"})
    md = B.vocabulary_block(R.RelevanceIndex(cs, annotations=ann))
    assert "`user`" in md and "`rare_atom`" in md
    assert "yes" in md, "an atom on 8/8 clauses must be flagged stopworded"


def test_vocabulary_block_says_so_when_there_is_no_annotation():
    import relevance as R
    cs = [{"id": "c0", "quote": "x", "section_path": ["S"]}]
    md = B.vocabulary_block(R.RelevanceIndex(cs, annotations={}))
    assert "no annotation artifact" in md


def test_control_is_a_weight_setting_of_the_same_scorer():
    """The control must not be a second implementation — otherwise the
    control-vs-tool gap is an artifact of two divergent codebases rather than
    the ontology's contribution."""
    import lexical_control as L
    w = L.CONTROL_WEIGHTS
    assert (w.atom, w.kind, w.section) == (0.0, 0.0, 0.0)
    assert w.expansion_terms == 0 and w.expansion_docs == 0
    idx = L.control_index([{"id": "c1", "quote": "hello world",
                            "section_path": ["S"]}])
    assert idx.annotations == {}
    assert idx.atom_df == {}


def test_control_best_point_is_zero_for_a_dead_index():
    import lexical_control as L
    import relevance as R
    idx = L.control_index([{"id": "c1", "quote": "zzz", "section_path": ["S"]}])
    b = R.Behaviour(slug="x", name="", definition="qqq")
    got = L.best_point(idx, b, lambda pred: {"f1_full": 1.0})
    assert got["f1_full"] == 0.0, "an empty sweep must not report a perfect F1"


# =====================================================================
#  MCC as primary metric, refuse-to-headline, selection-effect exposure
# =====================================================================

def test_mcc_is_zero_for_both_degenerate_predictors():
    """The whole reason MCC replaces F1 as primary: an all-positive predictor
    scores 0.44-0.64 under F1 and exactly 0 under MCC."""
    u = set(range(100))
    gold = set(range(40))
    assert B.mcc(u, gold, u) == 0.0            # predict everything
    assert B.mcc(set(), gold, u) == 0.0        # predict nothing
    assert B.floor_mcc(gold, u) == 0.0
    assert B.floor_f1(gold, u) > 0.5           # ...whereas F1's floor is high
    assert B.mcc(gold, gold, u) == pytest.approx(1.0)
    assert B.mcc(u - gold, gold, u) == pytest.approx(-1.0)


def test_mcc_ranks_judges_the_same_way_f1_does():
    """Switching the primary metric must not silently reorder the panel."""
    for b in B.load_panel().values():
        ev = B.evaluate(b, set(), B.load_clauses()[0])
        by_f1 = sorted(ev["per_target"], key=lambda j: -ev["per_target"][j]["judge_full"]["f1"])
        by_mcc = sorted(ev["per_target"], key=lambda j: -ev["per_target"][j]["judge_mcc_full"])
        assert by_f1 == by_mcc


def test_sol_looks_degenerate_ONLY_because_its_true_negatives_were_deleted():
    """`sol` was called a chance-level judge throughout this project. It is
    not: it is a LOW-THRESHOLD judge, and the published universe had deleted
    exactly the passages it gets right (the ones nobody flagged). On the true
    589-passage universe its MCC on helpfulness goes -0.027 -> +0.308."""
    clauses, _ = B.load_clauses()
    pub = B.evaluate(B.load_panel()["helpfulness"], set(), clauses)
    true = B.evaluate(B.load_true_panel()["helpfulness"], set(), clauses)
    assert pub["per_target"]["sol"]["judge_mcc_full"] == pytest.approx(-0.027, abs=0.01)
    assert true["per_target"]["sol"]["judge_mcc_full"] == pytest.approx(+0.308, abs=0.01)


def test_the_exclusion_guard_stands_down_on_the_true_universe():
    """The `REFUSED / UNUSABLE FOR HEADLINE` machinery for over/under-caution
    was computed on the broken universe: the F1 floor there is 0.640 against a
    0.500 bar. On the true universe the base rate collapses and every one of
    the 9 cells has judge F1 > floor F1, so the refusal must NOT fire."""
    clauses, _ = B.load_clauses()
    pub = B.evaluate(B.load_panel()["avoiding-over-and-under-caution"], set(), clauses)
    assert pub["headline_usable"] is False           # the artifact, still reproducible
    assert "kimi-k2" in pub["unusable_targets"]

    true_panel = B.load_true_panel()
    for slug, b in true_panel.items():
        ev = B.evaluate(b, set(), clauses)
        assert ev["headline_usable"] is True, slug
        assert ev["unusable_targets"] == [], (slug, ev["unusable_targets"])
        for j, r in ev["per_target"].items():
            assert r["judge_full"]["f1"] > r["floor_full"], (slug, j)
    md = B.headline_table({s: B.evaluate(b, set(), clauses)
                           for s, b in true_panel.items()})
    assert "UNUSABLE FOR HEADLINE" not in md
    assert "REFUSED" not in md


def test_the_exclusion_guard_STILL_fires_when_a_cell_genuinely_fails():
    """The guard is re-derived, not deleted. A synthetic behaviour whose judge
    really is beaten by a constant must still be refused."""
    ps = [mk_passage(f"q{i}", {"a": 2, "b": 2, "c": 0}, f"clause {i}")
          for i in range(9)]
    ps += [mk_passage("q9", {"a": 0, "b": 0, "c": 2}, "clause 9")]
    b = {"slug": "rigged", "coverage": {"openai": {"passages": ps}}}
    ev = B.evaluate(b, set(), [{"id": "c1", "quote": "clause 0",
                                "marked_span": None}])
    r = ev["per_target"]["c"]
    assert r["floor_full"] > r["judge_full"]["f1"]
    assert ev["headline_usable"] is False
    assert "UNUSABLE FOR HEADLINE" in B.headline_table({"rigged": ev})


def test_kimi_k2_scale_difference_is_real_but_is_not_a_reason_to_exclude():
    """kimi-k2 never emits `related` — a genuine scale difference. But its MCC
    on the true universe is +0.552, so the cell is usable; the refusal it used
    to trigger was an artifact of the deleted true negatives."""
    clauses, _ = B.load_clauses()
    b = B.load_true_panel()["avoiding-over-and-under-caution"]
    used = collections.Counter((p.get("verdicts") or {}).get("kimi-k2")
                               for p in B.passages(b))
    assert used[1] == 0
    assert B.binary_scale_judges(b) == ["kimi-k2"]
    ev = B.evaluate(b, set(), clauses)
    assert ev["per_target"]["kimi-k2"]["judge_mcc_full"] == pytest.approx(0.552, abs=0.01)
    assert ev["headline_usable"] is True


def test_every_cell_clears_mcc_0_30_on_the_true_universe():
    """All 9 (behaviour, pair-gold) cells: judge mean +0.555, min +0.308."""
    clauses, _ = B.load_clauses()
    vals = []
    for b in B.load_true_panel().values():
        ev = B.evaluate(b, set(), clauses)
        vals += [r["judge_mcc_full"] for r in ev["per_target"].values()]
    assert len(vals) == 9
    assert min(vals) >= 0.30
    assert sum(vals) / 9 == pytest.approx(0.555, abs=0.01)
    assert min(vals) == pytest.approx(0.308, abs=0.01)


def test_published_universe_judge_mcc_is_the_understated_number():
    clauses, _ = B.load_clauses()
    vals = []
    for b in B.load_panel().values():
        ev = B.evaluate(b, set(), clauses)
        vals += [r["judge_mcc_full"] for r in ev["per_target"].values()]
    assert sum(vals) / 9 == pytest.approx(0.394, abs=0.01)
    assert min(vals) < 0.0            # sol on helpfulness, the artifact


def test_kimi_k2_never_emits_related():
    """The documented cause of the refusal — asserted, not just asserted-in-prose."""
    b = B.load_panel()["avoiding-over-and-under-caution"]
    used = collections.Counter((p.get("verdicts") or {}).get("kimi-k2")
                               for p in B.passages(b))
    assert used[1] == 0, "kimi-k2 is expected to run a binary 0/2 scale"
    assert used[0] and used[2]
    other = collections.Counter((p.get("verdicts") or {}).get("sol")
                                for p in B.passages(b))
    assert other[1] > 0, "the comparator judges do use the middle level"


def test_healthy_behaviours_still_carry_a_headline():
    panel = B.load_panel()
    clauses, _ = B.load_clauses()
    for slug in ("helpfulness", "harm-avoidance-to-third-parties"):
        assert B.evaluate(panel[slug], set(), clauses)["headline_usable"] is True


# ==================================================================
#  THE TRUE UNIVERSE  (589 judged passages, not the published 377)
# ==================================================================

def test_load_true_panel_is_the_589_universe_and_load_panel_is_not():
    true, pub = B.load_true_panel(), B.load_panel()
    for slug in pub:
        assert len(B.passages(true[slug])) == 589
        assert len(B.passages(pub[slug])) < 589


def test_tool_gains_less_than_the_judges_when_the_universe_is_restored():
    """The whole point. Restoring the deleted true negatives is worth +0.046
    to the tool and +0.161 to the judges: the gap widens 0.120 -> 0.235."""
    clauses, _ = B.load_clauses()
    import relevance as R
    idx = R.RelevanceIndex.from_files(annotations_path=_p("annotations_b8.json"))
    behs = R.behaviours_from_panel(B.load_panel(),
                                   atoms_source=_p("behavior_atoms_b8.json"))
    got = {}
    for name, panel in (("published", B.load_panel()), ("true", B.load_true_panel())):
        t, j = [], []
        for slug, b in panel.items():
            pred = idx.predict(behs[slug], 0.18)
            ev = B.evaluate(b, pred, clauses)
            t.append(ev["tool_mcc_mean_full"])
            j.append(ev["judge_mcc_mean_full"])
        got[name] = (sum(t) / 3, sum(j) / 3)
    assert got["published"][0] == pytest.approx(0.274, abs=0.01)
    assert got["true"][0] == pytest.approx(0.320, abs=0.01)
    assert got["published"][1] == pytest.approx(0.394, abs=0.01)
    assert got["true"][1] == pytest.approx(0.555, abs=0.01)
    assert (got["true"][1] - got["true"][0]) > (got["published"][1] - got["published"][0])


def test_report_emits_both_universes_and_the_delta_never_one_alone():
    clauses, _ = B.load_clauses()
    md = B.dual_report(predictions={s: set() for s in B.load_panel()},
                       clauses=clauses)
    assert "589" in md and "377" in md
    assert "TRUE universe" in md and "published universe" in md
    assert "delta" in md.lower()
    assert B.check_universe_pairing(md) is True


def test_universe_pairing_guard_rejects_a_true_only_headline():
    md = ("## Headline — tool vs the panel\n"
          "| behaviour | tool MCC |\n| --- | ---: |\n| x | +0.320 |\n")
    with pytest.raises(AssertionError):
        B.check_universe_pairing(md)


def test_delta_table_states_both_numbers_and_their_difference(behaviour, clauses):
    pub = {"synthetic": B.evaluate(behaviour, {"c1"}, clauses)}
    md = B.delta_table(pub, pub)
    assert "delta" in md.lower()
    assert "+0.000" in md            # identical inputs -> zero delta, stated


# ---------------------------------------------------- threshold-free ROC/AUC

def test_auc_hand_computed():
    sc = {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
    u, gold = set(sc), {"a", "c"}
    # pos {.9,.7} vs neg {.8,.6}: 3 of 4 pairs ordered correctly
    assert B.auc(sc, gold, u) == pytest.approx(0.75)
    assert B.auc(sc, {"a", "b"}, u) == pytest.approx(1.0)
    assert B.auc(sc, {"c", "d"}, u) == pytest.approx(0.0)


def test_auc_counts_ties_as_half():
    sc = {"a": 0.5, "b": 0.5, "c": 0.5, "d": 0.5}
    assert B.auc(sc, {"a", "b"}, set(sc)) == pytest.approx(0.5)
    sc2 = {"a": 1.0, "b": 1.0, "c": 0.0, "d": 1.0}
    # pos {a=1,c=0} neg {b=1,d=1}: (0.5+0.5+0+0)/4
    assert B.auc(sc2, {"a", "c"}, set(sc2)) == pytest.approx(0.25)


def test_auc_is_undefined_without_both_classes():
    sc = {"a": 1.0, "b": 0.0}
    assert B.auc(sc, set(), set(sc)) is None
    assert B.auc(sc, set(sc), set(sc)) is None


def test_missing_score_is_zero_not_dropped():
    """A passage joining to no clause can never be predicted; it scores 0 and
    stays in the denominator. Dropping it would inflate the tool's AUC."""
    sc = {"a": 0.9}
    u, gold = {"a", "b", "c", "d"}, {"a", "b"}
    assert B.auc(sc, gold, u) == pytest.approx(0.75)   # b ties c and d at 0


def test_tpr_at_fpr_hand_computed():
    sc = {"a": 0.9, "b": 0.8, "c": 0.7, "d": 0.6}
    u, gold = set(sc), {"a", "c"}
    assert B.tpr_at_fpr(sc, gold, u, 0.0) == pytest.approx(0.5)
    assert B.tpr_at_fpr(sc, gold, u, 0.5) == pytest.approx(1.0)
    assert B.tpr_at_fpr(sc, gold, u, 1.0) == pytest.approx(1.0)


def test_operating_point_of_a_binary_predictor():
    u, gold = {"a", "b", "c", "d"}, {"a", "c"}
    assert B.operating_point({"a", "b"}, gold, u) == pytest.approx((0.5, 0.5))
    assert B.operating_point(gold, gold, u) == pytest.approx((0.0, 1.0))


def test_roc_block_compares_the_tool_at_each_judges_own_operating_point():
    """A judge is one (FPR,TPR) point; the tool is a curve. The only
    threshold-free apples-to-apples comparison is the tool's TPR at the
    judge's own FPR — and on the true universe the judge wins 9/9."""
    clauses, _ = B.load_clauses()
    import relevance as R
    idx = R.RelevanceIndex.from_files(annotations_path=_p("annotations_b8.json"))
    behs = R.behaviours_from_panel(B.load_panel(),
                                   atoms_source=_p("behavior_atoms_b8.json"))
    rows, wins = [], 0
    for slug, b in B.load_true_panel().items():
        joins = B.clause_joins(b, clauses)
        sc = B.passage_scores(dict(idx.rank(behs[slug])), joins)
        r = B.roc_targets(b, sc)
        for j, cell in r.items():
            rows.append((slug, j, cell))
            wins += cell["judge_wins"]
    assert len(rows) == 9
    assert wins == 9, "the judge beats the tool at its own FPR on every cell"
    by_slug = {s: c["auc"] for s, j, c in rows}
    assert by_slug["helpfulness"] == pytest.approx(0.64, abs=0.03)
    assert by_slug["harm-avoidance-to-third-parties"] == pytest.approx(0.78, abs=0.03)
    assert by_slug["avoiding-over-and-under-caution"] == pytest.approx(0.90, abs=0.03)
    hel = [c for s, j, c in rows if s == "helpfulness" and j in ("fable", "kimi")]
    for c in hel:
        assert 0.75 <= c["judge_tpr"] <= 0.79
        assert c["judge_fpr"] == pytest.approx(0.06, abs=0.01)
        assert c["tool_tpr_at_judge_fpr"] == pytest.approx(0.128, abs=0.02)
    md = B.roc_block({s: {"per_target": {j: {"roc": c}}} for s, j, c in rows})
    assert "AUC" in md and "TPR" in md and "FPR" in md


def test_auc_is_reported_per_behaviour_and_pair_gold(behaviour, clauses):
    joins = B.clause_joins(behaviour, clauses)
    sc = B.passage_scores({"c1": 1.0, "c2": 0.5, "c3": 0.1}, joins)
    ev = B.evaluate(behaviour, {"c1"}, clauses, scores=sc)
    for j, r in ev["per_target"].items():
        assert "roc" in r
        assert set(r["roc"]) >= {"auc", "judge_fpr", "judge_tpr",
                                 "tool_tpr_at_judge_fpr", "judge_wins"}


# ------------------------------------------------------------- the MCC band

def test_mcc_band_reports_min_median_max_not_a_point():
    band = B.mcc_band([(0.10, 0.20), (0.20, 0.30), (0.30, 0.10), (0.50, 0.40)],
                      lo=0.10, hi=0.30)
    assert band["min"] == pytest.approx(0.10)
    assert band["max"] == pytest.approx(0.30)
    assert band["median"] == pytest.approx(0.20)
    assert band["n"] == 3
    assert band["lo"] == 0.10 and band["hi"] == 0.30


def test_mcc_band_block_prints_the_whole_curve_and_the_ci_caveat():
    curve = [(round(0.02 * i, 2), 0.2 + 0.001 * i) for i in range(51)]
    md = B.mcc_band_block({"synthetic": curve})
    assert md.count("| synthetic |") >= 51, "every threshold, not just the best"
    assert "band" in md.lower()
    assert "LOBO" in md and "contains zero" in md
    assert "point estimate" in md.lower()


def test_mcc_curve_is_computed_over_the_whole_sweep(behaviour, clauses):
    idx_scores = {"c1": 1.0, "c2": 0.6, "c3": 0.2, "cx": 0.9}
    curve = B.mcc_curve(behaviour, idx_scores, clauses)
    assert len(curve) == 51
    assert all(0.0 <= t <= 1.0 for t, _ in curve)
    assert curve == sorted(curve)


def test_headline_never_prints_f1_without_its_floor(behaviour, clauses):
    md = B.headline_table({"synthetic": B.evaluate(behaviour, {"c1"}, clauses)})
    header = [l for l in md.split("\n") if l.startswith("| behaviour |")][0]
    assert "FLOOR" in header
    assert "MCC" in header
    i_f1, i_floor = header.index("tool F1"), header.index("F1 FLOOR")
    assert i_f1 < i_floor, "the floor must sit beside the F1 it qualifies"


def test_head_to_head_is_one_row_per_gold_not_a_mean(behaviour, clauses):
    """The old headline compared a mean-of-three to a max-of-one."""
    ev = B.evaluate(behaviour, {"c1"}, clauses)
    md = B.head_to_head_table({"synthetic": ev})
    assert md.count("| synthetic |") == len(ev["per_target"]) == 3
    for j in ev["per_target"]:
        assert f"| {j} |" in md


def test_judge_mean_is_promoted_over_judge_best(behaviour, clauses):
    md = B.headline_table({"synthetic": B.evaluate(behaviour, {"c1"}, clauses)})
    assert "mean LOO" in md
    assert "best judge" not in md.lower()


def test_selection_effect_counts_are_surfaced(behaviour, clauses):
    ev = B.evaluate(behaviour, {"c1", "cx"}, clauses)
    assert ev["n_predicted_clauses"] == 2
    assert ev["n_predicted_unliftable"] == 1        # cx joins to no passage
    assert ev["unliftable_frac"] == pytest.approx(0.5)
    md = B.headline_table({"synthetic": ev})
    assert "unscored" in md
    assert "Selection effect" in md


def test_control_is_capped_at_the_tool_budget():
    """Unbudgeted, the control collapses to predict-everything and 'wins'."""
    import lexical_control as L
    import relevance as R
    cs = [{"id": f"c{i}",
           "quote": "helpful user" if i < 3 else f"unrelated topic{i}",
           "section_path": ["S"]} for i in range(20)]
    idx = L.control_index(cs)
    b = R.Behaviour(slug="x", name="", definition="helpful user")
    seen = []
    L.best_point(idx, b, lambda pred: (seen.append(len(pred)) or {"mcc": 0.0}),
                 budget=5)
    assert seen and max(seen) <= 5


def test_control_best_point_ranks_on_mcc_by_default():
    import lexical_control as L
    import relevance as R
    cs = [{"id": f"c{i}", "quote": f"clause {i} helpful", "section_path": ["S"]}
          for i in range(10)]
    idx = L.control_index(cs)
    b = R.Behaviour(slug="x", name="", definition="helpful")
    got = L.best_point(idx, b, lambda pred: {"mcc": len(pred), "f1_full": -1.0})
    assert got["mcc"] == got["n"]


# ---- regression: the real loader must preserve section structure ----
#
# `_clause_rows` rebuilt each row from a fixed key list and dropped
# `section_path`. RelevanceIndex then saw ONE section holding all 593 clauses,
# so the section channel (0.45 of the scoring weight) became a constant added
# to every clause. That pinned the minimum normalized score at ~0.30 — exactly
# DEFAULT_THRESHOLD — so the tool predicted 592/593 clauses and reported
# MCC ~= 0, which was read as "the method learned nothing".
#
# 631 tests passed with the channel dead, because EVERY fixture in this file
# and in test_relevance.py hand-builds clause dicts that already contain
# `section_path`. The gap was that nothing exercised the REAL loader. These
# tests do, and they are deliberately written against the real data file.

def test_real_clause_rows_preserve_section_path():
    """Bound the SHAPE, not just >1. A mutant collapsing 593 clauses into
    (592 + 1) sections passed the original `len(sections) > 1` assertion while
    fully reinstating the bug: the tool still predicted 593/593 at MCC -0.036."""
    rows, _ = B.load_clauses()
    assert rows, "no clauses loaded"
    sections = {}
    for r in rows:
        sections.setdefault(tuple(r.get("section_path") or ()), []).append(r)
    assert len(sections) >= 70, (
        f"only {len(sections)} distinct sections; the real spec has 78")
    biggest = max(len(v) for v in sections.values())
    assert biggest < 0.10 * len(rows), (
        f"largest section holds {biggest}/{len(rows)} clauses — the section "
        "channel is effectively a constant")


def test_real_clause_rows_keep_fields_the_scorer_reads():
    """Every row, not rows[0]. Enumerating keys is how section_path was lost."""
    rows, _ = B.load_clauses()
    for key in ("id", "quote", "section_path", "kind"):
        missing = [r.get("id") for r in rows if key not in r]
        assert not missing, f"{key!r} missing on {len(missing)} row(s)"


def test_index_built_from_real_rows_sees_many_sections():
    import relevance
    rows, _ = B.load_clauses()
    idx = relevance.RelevanceIndex(rows, {})
    assert len(getattr(idx, "_members", {})) >= 70


def test_prediction_at_the_default_threshold_is_not_degenerate():
    """THE SYMPTOM TEST — the one that was missing.

    Both prior defects (section_path dropped; threshold selected on F1) showed
    up the same way: predict almost everything, MCC ~ 0. Asserting on the
    structure of the index is indirect; this asserts the observable failure.
    """
    import relevance
    rows, _ = B.load_clauses()
    ann = relevance.load_annotations(_p("annotations_b8.json"))
    if not ann:
        pytest.skip("annotations_b8.json not present")
    panel = B.load_panel()
    behs = relevance.behaviours_from_panel(panel, _p("behavior_atoms_b8.json"))
    idx = relevance.RelevanceIndex(rows, ann)
    for slug, b in behs.items():
        pred = idx.predict(b, relevance.DEFAULT_THRESHOLD)
        assert len(pred) < 0.60 * len(rows), (
            f"{slug}: predicts {len(pred)}/{len(rows)} clauses at the default "
            "threshold — degenerate, as in both prior defects")
        assert pred, f"{slug}: predicts nothing at the default threshold"


def test_tool_mcc_over_the_real_panel_clears_a_floor():
    """THE QUALITY GUARD. Every other test here bounds STRUCTURE (section
    counts, field presence, prediction counts). A scorer with ZERO
    discrimination passes all of them: permuting the per-clause channel scores
    leaves the score DISTRIBUTION — and therefore the prediction count —
    identical, while MCC collapses from +0.274 to +0.048 / -0.057.

    Both prior defects were ultimately visible here and nowhere else. This is
    also the guard that keeps meaning when the additive combiner is replaced:
    a count-based symptom test stops constraining anything the moment the
    score distribution changes shape.

    Measured +0.2743 at the time of writing; the floor is set well below so
    ordinary tuning does not trip it, but no degenerate or permuted variant
    can pass.
    """
    import relevance
    rows, _ = B.load_clauses()
    ann = relevance.load_annotations(_p("annotations_b8.json"))
    if not ann:
        pytest.skip("annotations_b8.json not present")
    panel = B.load_panel()
    behs = relevance.behaviours_from_panel(panel, _p("behavior_atoms_b8.json"))
    idx = relevance.RelevanceIndex(rows, ann)

    mccs = []
    for slug, b in behs.items():
        pred = idx.predict(b, relevance.DEFAULT_THRESHOLD)
        ev = B.evaluate(panel[slug], pred, rows)
        mccs.append(ev["tool_mcc_mean_full"])
    mean = sum(mccs) / len(mccs)
    assert mean >= 0.15, (
        f"mean tool MCC {mean:+.4f} over the real panel is below the floor — "
        "the scorer has lost its discrimination (measured +0.2743)")


# ------------------------------------------------- label-free operating point
#
# The single largest gap in this project: the tool's RANKING is far better than
# its thresholded DECISION (LOBO +0.206 vs oracle +0.387). `threshold.py` picks
# an operating point from the score distribution alone. These tests guard the
# reporting path, whose job is to make the calibration gap impossible to hide.

@pytest.fixture
def op_scores():
    """`{slug: {clause id: score}}` for the synthetic behaviour."""
    return {"synthetic": {"c1": 0.90, "c2": 0.80, "c3": 0.20, "cx": 0.05}}


def test_mean_mcc_at_agrees_with_the_curve_at_a_grid_point(behaviour, clauses,
                                                           op_scores):
    """The new arbitrary-cut evaluator and the existing grid sweep must be the
    same function. If they drift, every rule is scored on a different protocol
    from the LOBO/oracle rows it is compared against."""
    joins = B.clause_joins(behaviour, clauses)
    curve = dict(B.mcc_curve(behaviour, op_scores["synthetic"], clauses,
                             joins=joins))
    for t in (0.10, 0.20, 0.50, 0.90):
        assert B.mean_mcc_at(behaviour, op_scores["synthetic"], joins,
                             t) == pytest.approx(curve[t])


def test_lobo_cuts_never_use_the_behaviours_own_curve():
    """LOBO is only honest if the held-out behaviour is genuinely held out."""
    # `a` peaks so hard at 0.1 that including its own curve would drag every
    # behaviour's held-out choice to 0.1. Held out properly, `a` must be
    # decided by b+c (both peak at 0.5), and `b` by a+c (a's 5.0 dominates).
    curves = {"a": [(0.1, 5.0), (0.5, 0.0)],
              "b": [(0.1, 0.0), (0.5, 1.0)],
              "c": [(0.1, 0.0), (0.5, 1.0)]}
    cuts = B.lobo_cuts(curves)
    assert cuts["a"] == 0.5, (
        "LOBO used the held-out behaviour's OWN curve — the cut is no longer "
        "held out and every number derived from it is in-sample")
    assert cuts["b"] == 0.1
    assert cuts["c"] == 0.1
    assert B.oracle_cuts(curves)["a"] == 0.1      # oracle DOES use its own


def test_label_free_cuts_are_computed_without_opening_anything(op_scores):
    """DYNAMIC guard on the wiring, not just on `threshold.py`.

    The rule may be clean while the call site launders the answer key in — the
    exact attack that beat the first version of the anti-cheat guard elsewhere
    in this repo. During cut selection the right number of file reads is zero.
    """
    import builtins
    import io
    import os as _os
    opened = []
    saved = (builtins.open, io.open, _os.open)

    def mk(real):
        def spy(path, *a, **kw):
            opened.append(str(path))
            return real(path, *a, **kw)
        return spy

    builtins.open, io.open, _os.open = mk(saved[0]), mk(saved[1]), mk(saved[2])
    try:
        cuts = B.label_free_cuts("otsu", op_scores)
    finally:
        builtins.open, io.open, _os.open = saved
    assert set(cuts) == {"synthetic"}
    assert opened == [], f"cut selection opened {opened}"


def test_operating_point_block_never_states_a_number_without_lobo_and_floors(
        behaviour, clauses, op_scores):
    """THE reporting invariant. The reported operating point exists to close a
    CALIBRATION gap, so the gap must stay visible beside it: the held-out LOBO
    number it improves on, the oracle it cannot reach, and both floors."""
    joins = {"synthetic": B.clause_joins(behaviour, clauses)}
    md = B.operating_point_block({"synthetic": behaviour}, op_scores, joins,
                                 clauses, resamples=0)
    low = md.lower()
    for token in ("lobo", "oracle", "floor a", "floor b"):
        assert token in low, f"operating-point block omits {token!r}"
    assert B.check_operating_point_pairing(md)


def test_check_operating_point_pairing_rejects_a_lone_number():
    """Mutation-proof the guard: it must FAIL on the bad document."""
    lone = "## Operating point\n\nlabel-free rule `otsu`: mean MCC +0.278\n"
    with pytest.raises(AssertionError):
        B.check_operating_point_pairing(lone)


def test_operating_point_block_reports_every_rule_including_losers(
        behaviour, clauses, op_scores):
    """Selecting the best rule ON THE PANEL is the same error as selecting the
    best threshold on it. The defence is that every rule tried is printed."""
    import threshold as T
    joins = {"synthetic": B.clause_joins(behaviour, clauses)}
    md = B.operating_point_block({"synthetic": behaviour}, op_scores, joins,
                                 clauses, resamples=0)
    for name in T.RULES:
        assert name in md, f"rule {name!r} was tried but is not in the table"
    assert "PRE-REGISTERED" in md.upper()
    assert T.PREFERRED in md


def test_operating_point_block_marks_the_preregistered_rule_not_the_winner(
        behaviour, clauses, op_scores):
    """The headline row must be the pre-registered rule even when a comparator
    scores higher — that is the whole point of pre-registering."""
    import threshold as T
    joins = {"synthetic": B.clause_joins(behaviour, clauses)}
    md = B.operating_point_block({"synthetic": behaviour}, op_scores, joins,
                                 clauses, resamples=0)
    marked = [l for l in md.split("\n") if "PREFERRED" in l and l.startswith("|")]
    assert len(marked) == 1, f"expected exactly one preferred row, got {marked}"
    assert T.PREFERRED in marked[0]


def test_an_all_positive_cut_lands_exactly_on_the_floor(behaviour, clauses,
                                                        op_scores):
    """Both floors survive the new layer, and they are DIFFERENT numbers.

    Cut 0.0 predicts every clause with any signal, which lifts to every
    REACHABLE passage — that is floor B, not floor A. Floor A (predict the
    literal universe, including passages that join to no clause) is MCC's
    definitional zero. Conflating the two is how a coverage cost gets absorbed
    into a headline, so the test pins that cut 0.0 hits floor B exactly and
    that floor A is still 0.
    """
    joins = B.clause_joins(behaviour, clauses)
    universe = set(joins)
    golds = [t["gold"] for t in B.pair_targets(behaviour).values()]

    floor_a = sum(B.mcc(universe, g, universe) for g in golds) / len(golds)
    assert floor_a == 0.0

    floor_b = sum(B.mcc(B.joinable(joins), g, universe)
                  for g in golds) / len(golds)
    assert B.mean_mcc_at(behaviour, op_scores["synthetic"], joins,
                         0.0) == pytest.approx(floor_b)


def test_a_degenerate_scorer_gets_no_flattering_operating_point(behaviour,
                                                                clauses):
    """A constant scorer must be cut to the empty prediction, scoring 0.0 —
    not sliced through its ties into a lucky subset."""
    import threshold as T
    flat = {"synthetic": {c["id"]: 1.0 for c in clauses}}
    joins = B.clause_joins(behaviour, clauses)
    cuts = B.label_free_cuts(T.PREFERRED, flat)
    assert cuts["synthetic"] == T.DEGENERATE_CUT
    assert B.mean_mcc_at(behaviour, flat["synthetic"], joins,
                         cuts["synthetic"]) == 0.0


# ================================================================
#  PANEL v2 — 18 cells, small-model judges. POWER, NOT A BAR.
# ================================================================

def _small(slug="synthetic", ps=None, key="openai"):
    """A behaviour tagged as small-model panel, in the shape panel_v2 emits."""
    ps = ps or [mk_passage("p1", {"a": 2, "b": 2, "c": 2}, "alpha clause one"),
                mk_passage("p4", {"a": 1, "b": 0, "c": 0}, "delta clause four")]
    return {"slug": slug, "coverage": {key: {"passages": ps}},
            "panel": {"id": "small-model-panel-v2", "tier": "small",
                      "models": ["gpt-mini", "haiku", "qwen-small"],
                      "label": "small-model panel"}}


def test_a_behaviour_without_a_panel_block_is_the_frontier_panel():
    """Defaulting the other way would relabel the real bar 'small' and make the
    guard fire on the frontier tables, which would train everyone to ignore it."""
    assert B.panel_tier({"slug": "x"}) == "frontier"
    assert B.panel_roster({"slug": "x"}) == []


def test_panel_tier_and_roster_are_read_off_the_behaviour():
    b = _small()
    assert B.panel_tier(b) == "small"
    assert B.panel_roster(b) == ["gpt-mini", "haiku", "qwen-small"]


def test_a_bar_quoted_off_small_judges_must_name_the_tier():
    """THE structural guard. The small-model panel's judge column is exactly
    the number someone will lift and quote as 'the bar' — six times the
    frontier panel's evidence, and the wrong standard entirely."""
    md = "| behaviour | judge MCC |\n| x | +0.525 |"
    with pytest.raises(AssertionError, match="small-model panel"):
        B.check_bar_provenance(md, {"synthetic": _small()})


def test_a_bar_quoted_off_small_judges_must_name_the_roster():
    md = ("judge MCC is reported below. This is the small-model panel and it "
          "is NOT the frontier bar. judges: gpt-mini, haiku.")
    with pytest.raises(AssertionError, match="qwen-small"):
        B.check_bar_provenance(md, {"synthetic": _small()})


def test_the_bar_guard_passes_when_the_tier_and_roster_are_named():
    md = B.bar_provenance_block({"synthetic": _small()}) + "\n| judge MCC |\n"
    assert B.check_bar_provenance(md, {"synthetic": _small()}) is True


def test_the_bar_guard_does_not_fire_on_the_frontier_panel():
    md = "| behaviour | judge MCC |\n| x | +0.525 |"
    assert B.check_bar_provenance(md, {"x": {"slug": "x"}}) is True


def test_the_bar_guard_does_not_fire_on_a_document_with_no_bar():
    assert B.check_bar_provenance("no numbers here", {"s": _small()}) is True


def test_bar_provenance_block_describes_both_tiers():
    md = B.bar_provenance_block({"a": _small(), "b": {"slug": "b"}}).lower()
    assert "small-model panel" in md and "not the frontier bar" in md
    assert "frontier panel" in md and "the bar" in md


def test_bar_provenance_derives_an_undeclared_roster_from_the_verdicts(behaviour):
    """An unnamed bar is the thing this block exists to prevent, so a panel
    that predates the `panel` field has its roster read off the data."""
    md = B.bar_provenance_block([behaviour])
    for j in B.judges(behaviour, "openai"):
        assert f"`{j}`" in md
    assert "(unnamed)" not in md


def test_the_two_panels_share_three_slugs_so_they_must_not_be_dict_merged(
        behaviour, clauses):
    """helpfulness / harm-avoidance-to-third-parties /
    avoiding-over-and-under-caution are in BOTH panels. Merging the two
    behaviour maps by slug silently deletes three small-model behaviours; the
    report must count both panels in full."""
    small = _small(slug="helpfulness", ps=B.passages(behaviour, "openai"))
    front = dict(behaviour, slug="helpfulness")
    ev = B.cell_evaluate(small, set(), "openai", clauses=clauses, spec="alpha")
    fev = B.cell_evaluate(front, set(), "openai", clauses=clauses, spec="alpha")
    md = B.panel_v2_report({"helpfulness": small},
                           {("helpfulness", "openai"): ev},
                           {("helpfulness", "openai"): ev}, "control",
                           frontier_results={("helpfulness", "openai"): fev},
                           frontier_behaviours={"helpfulness": front})
    assert "small-model panel** (`small-model-panel-v2`, 1 behaviours)" in md
    assert "frontier panel** (`frontier-panel`, 1 behaviours)" in md
    assert "FRONTIER panel" in md and "never merged" in md


# ------------------------------------------------------------ floors A and B

def test_floor_b_is_the_joinable_predictor_and_floor_a_is_zero(behaviour,
                                                               clauses):
    joins = B.clause_joins(behaviour, clauses)
    universe, matched = set(joins), B.joinable(joins)
    gold = B.pair_targets(behaviour)["a"]["gold"]
    assert B.mcc(universe, gold, universe) == 0.0                 # floor A
    assert B.floor_b_mcc(gold, universe, matched) == pytest.approx(
        B.mcc(matched, gold, universe))


def test_cell_evaluate_reports_both_floors_on_every_target(behaviour, clauses):
    ev = B.cell_evaluate(behaviour, set(), "openai", clauses=clauses,
                         spec="alpha clause one beta clause two")
    for row in ev["per_target"].values():
        assert row["floor_a_mcc"] == 0.0
        assert "floor_b_mcc" in row
    assert ev["floor_a_mcc"] == 0.0
    assert ev["spec_key"] == "openai"


# ------------------------------------------------- per-spec clause namespaces

def test_each_spec_key_has_its_own_clause_inventory_and_markdown():
    """Scoring the constitution against the model spec's clauses would leave
    every miss diagnosed as a segmentation bug on the wrong document."""
    assert set(B.SPEC_CLAUSES) == {"openai", "anthropic"}
    assert B.SPEC_CLAUSES["openai"] != B.SPEC_CLAUSES["anthropic"]
    ms, _ = B.clauses_for_spec("openai")
    cn, _ = B.clauses_for_spec("anthropic")
    assert {str(c["id"])[0] for c in ms} == {"m"}
    assert {str(c["id"])[0] for c in cn} == {"c"}


def test_an_unknown_spec_key_raises_rather_than_defaulting():
    with pytest.raises(KeyError):
        B.clauses_for_spec("deepmind")


def test_annotations_are_filtered_to_the_specs_clause_namespace():
    """An annotation file keyed m0001... says nothing about c001...; handing it
    to the constitution index leaves every clause unannotated while the run
    reports 'annotations: ok'."""
    ann = {"m0001": 1, "m0002": 2, "c001": 3}
    assert B.annotations_for_spec(ann, "openai") == {"m0001": 1, "m0002": 2}
    assert B.annotations_for_spec(ann, "anthropic") == {"c001": 3}
    assert B.annotations_for_spec({}, "openai") == {}


# ------------------------------------------------ bootstrap and noise floor

def _vecs(n, k=3, seed=0):
    import random
    rng = random.Random(seed)
    return [[(rng.random() < 0.4, rng.random() < 0.4) for _ in range(n)]
            for _ in range(k)]


def test_a_predictor_against_itself_has_a_zero_paired_delta():
    """Pairing is the whole point: the same resample on both sides must cancel
    exactly, not merely approximately."""
    a = {("s", "openai"): _vecs(80)}
    mean, lo, hi = B.paired_bootstrap_cells(a, a, resamples=100)
    assert (mean, lo, hi) == (0.0, 0.0, 0.0)


def test_the_noise_floor_is_positive_and_shrinks_with_more_passages():
    """It is a sampling-variability quantity: a bigger universe must lower it,
    or it is not measuring what it claims to."""
    small = B.noise_floor({("s", "openai"): _vecs(60, seed=1)}, resamples=200)
    big = B.noise_floor({("s", "openai"): _vecs(600, seed=1)}, resamples=200)
    assert small["half_width"] > 0
    assert big["half_width"] < small["half_width"]


def test_the_noise_floor_is_re_derived_never_imported():
    """Importing the 3-behaviour panel's 0.045 onto an 18-cell panel with two
    universe sizes is exactly how this project published a false null."""
    nf = B.noise_floor({("s", "openai"): _vecs(400, seed=2)}, resamples=200)
    assert nf["half_width"] != B.OPERATING_POINT_NOISE
    assert "not reused" in B.noise_floor_block(nf).lower()
    assert str(B.OPERATING_POINT_NOISE) in B.noise_floor_block(nf)


def test_a_delta_inside_the_noise_floor_is_reported_as_not_distinguishable():
    nf = {"half_width": 0.05}
    assert "NOT distinguishable" in B.bootstrap_block((0.01, -0.02, 0.04),
                                                      "a", "b", nf)
    assert "NOT distinguishable" in B.bootstrap_block((0.20, -0.01, 0.41),
                                                      "a", "b", nf)
    assert "**distinguishable**" in B.bootstrap_block((0.20, 0.11, 0.29),
                                                      "a", "b", nf)


def test_cell_vectors_are_passage_aligned_to_the_gold(behaviour):
    vecs = B.cell_vectors(behaviour, {"p1", "p2"}, "openai")
    ps = sorted(p["id"] for p in B.passages(behaviour, "openai"))
    assert len(vecs) == len(B.judges(behaviour, "openai"))
    for v in vecs:
        assert len(v) == len(ps)
    targets = B.pair_targets(behaviour, 1, "openai")
    for (j, t), v in zip(sorted(targets.items()), vecs):
        assert [g for _, g in v] == [p in t["gold"] for p in ps]


# --------------------------------------------------------- the 18-cell table

def test_cell_table_prints_one_row_per_cell_and_labels_the_tier(behaviour,
                                                                clauses):
    b = dict(_small(), coverage=behaviour["coverage"])
    ev = B.cell_evaluate(b, set(), "openai", clauses=clauses, spec="alpha")
    md = B.cell_table({("synthetic", "openai"): ev}, "control")
    assert "| synthetic | openai | small |" in md
    assert "FLOOR A" in md and "FLOOR B" in md
    assert "mean of 1 cells" in md
    assert "least informative row" in md


def test_cell_results_is_keyed_by_cell_not_by_slug(behaviour, clauses):
    """A slug-keyed prediction map would score the constitution with the model
    spec's clause ids — a different namespace, silently predicting nothing."""
    b = _small(ps=B.passages(behaviour, "openai"))
    out = B.cell_results({"synthetic": b}, {("synthetic", "openai"): set()},
                         spec_keys=("openai",),
                         clauses={"openai": clauses}, specs={"openai": "alpha"})
    assert list(out) == [("synthetic", "openai")]
    assert B.cell_results({"synthetic": b}, {"synthetic": set()},
                          spec_keys=("openai",), clauses={"openai": clauses},
                          specs={"openai": "alpha"}) == {}


def test_panel_v2_report_runs_all_three_guards(behaviour, clauses):
    b = _small(ps=B.passages(behaviour, "openai"))
    ev = B.cell_evaluate(b, set(), "openai", clauses=clauses, spec="alpha")
    res = {("synthetic", "openai"): ev}
    md = B.panel_v2_report({"synthetic": b}, res, res, "control")
    low = md.lower()
    assert "true universe" in low and "published universe" in low
    assert "delta" in low
    assert "small-model panel" in low and "not the frontier bar" in low
    for m in ("gpt-mini", "haiku", "qwen-small"):
        assert m in low


def test_panel_v2_report_refuses_an_unlabelled_small_model_bar(monkeypatch,
                                                               behaviour,
                                                               clauses):
    """MUTATION CHECK, standing: if the tier disclaimer is ever dropped from
    `bar_provenance_block`, the report must fail rather than print."""
    b = _small(ps=B.passages(behaviour, "openai"))
    ev = B.cell_evaluate(b, set(), "openai", clauses=clauses, spec="alpha")
    monkeypatch.setattr(B, "bar_provenance_block", lambda _bs: "judges: some\n")
    with pytest.raises(AssertionError):
        B.panel_v2_report({"synthetic": b},
                          {("synthetic", "openai"): ev},
                          {("synthetic", "openai"): ev}, "control")


# ================================================================
#  check_bar_provenance — THE THREE EVASIONS, AND `python -O`
# ================================================================
#
# The guard was SELF-SATISFYING: its only call site emitted
# `bar_provenance_block(...)` two lines earlier, and that block contains the
# exact strings the guard looks for, so no report the function produced could
# ever fail it. A reviewer defeated it three ways, and `python -O` deleted it
# outright because it was built out of bare `assert`s.
#
# Each evasion below is a test. All four were RED before the guard was rebuilt.

_DISCLAIM = ("This is the small-model panel (gpt-mini, haiku, qwen-small) and "
             "it is NOT the frontier bar.")


def test_bar_provenance_rejects_a_disclaimer_hidden_in_an_html_comment():
    """EVASION 1. `<!-- ... -->` renders as nothing. A disclosure a reader
    cannot see has not been made, and a substring scan cannot tell the
    difference. # MUTATION-VERIFIED: deleting the comment strip turns this
    green."""
    # The table below is otherwise IMPECCABLE — it carries its own `panel`
    # tier column — so the ONLY thing this test can fail on is the comment.
    md = (f"<!-- {_DISCLAIM} -->\n\n"
          "## Results\n\n| behaviour | panel | judge MCC |\n"
          "| x | small | +0.525 |\n")
    with pytest.raises(B.BarProvenanceError, match="small-model panel"):
        B.check_bar_provenance(md, {"synthetic": _small()})


def test_bar_provenance_rejects_a_disclaimer_attached_to_a_different_table():
    """EVASION 2. The disclaimer is present, in visible prose, with the full
    roster — but it is attached to a DIFFERENT section, and the section that
    actually quotes the bar carries no tier at all. A whole-document substring
    scan passes it; a reader of the bar table never sees it."""
    md = ("## Coverage\n\n" + _DISCLAIM + "\n\n"
          "| behaviour | passages |\n| x | 589 |\n\n"
          "## Results\n\n| behaviour | judge MCC |\n| x | +0.525 |\n")
    with pytest.raises(B.BarProvenanceError, match="section"):
        B.check_bar_provenance(md, {"synthetic": _small()})


def test_bar_provenance_rejects_a_disclaimer_that_arrives_after_the_number():
    """The same attachment defect in its temporal form: the reader meets the
    number first and the caveat afterwards, if at all."""
    md = ("## Results\n\n| behaviour | judge MCC | panel |\n"
          "| x | +0.525 | small |\n\n"
          "## Notes\n\n" + _DISCLAIM + "\n")
    with pytest.raises(B.BarProvenanceError, match="(?i)before"):
        B.check_bar_provenance(md, {"synthetic": _small()})


def test_bar_provenance_catches_judge_agreement_phrasing():
    """EVASION 3. `judge agreement 0.83` hits NONE of the old markers
    (`judge mcc` / `judge f1` / `the bar` / `judge (mean loo)`), so the guard
    returned True and the small-model bar was quoted unlabelled."""
    md = "## Results\n\nOn these behaviours judge agreement 0.83.\n"
    with pytest.raises(B.BarProvenanceError, match="small-model panel"):
        B.check_bar_provenance(md, {"synthetic": _small()})
    # ... and the same for the other paraphrases that mean the same thing.
    for phrasing in ("panel self-agreement was 0.83",
                     "inter-judge agreement 0.83",
                     "the judges agree 83% of the time",
                     "| x | 0.83 |  <- judge column"):
        with pytest.raises(B.BarProvenanceError):
            B.check_bar_provenance(f"## Results\n\n{phrasing}\n",
                                   {"synthetic": _small()})


def test_bar_provenance_is_not_a_bare_assert_and_survives_python_dash_O():
    """`assert` is COMPILED OUT under `python -O`, so the guard evaporated in
    exactly the deployment where nobody is watching. Run it for real in a `-O`
    subprocess rather than reading the source."""
    import os
    import subprocess
    import sys
    prog = (
        "import benchmark as B\n"
        "b = {'slug': 's', 'coverage': {'openai': {'passages': []}},\n"
        "     'panel': {'id': 'p', 'tier': 'small',\n"
        "               'models': ['gpt-mini'], 'label': 'l'}}\n"
        "try:\n"
        "    B.check_bar_provenance('| behaviour | judge MCC |', {'s': b})\n"
        "except AssertionError:\n"
        "    print('GUARD FIRED')\n"
        "else:\n"
        "    print('GUARD EVAPORATED')\n")
    out = subprocess.run(
        [sys.executable, "-O", "-c", prog],
        cwd=os.path.dirname(os.path.abspath(B.__file__)),
        capture_output=True, text=True)
    assert "GUARD FIRED" in out.stdout, (
        f"the bar guard does not survive `python -O`: {out.stdout!r} "
        f"{out.stderr[-400:]!r}")


def test_bar_provenance_still_passes_a_report_that_labels_its_bar_properly():
    """The guard has to be satisfiable HONESTLY, or it will simply be deleted."""
    md = (B.bar_provenance_block({"synthetic": _small()})
          + "\n## Results\n\n| behaviour | panel | judge MCC |\n"
            "| x | small | +0.525 |\n")
    assert B.check_bar_provenance(md, {"synthetic": _small()}) is True


def test_the_bar_guard_is_not_satisfied_by_its_own_block_alone(behaviour,
                                                               clauses):
    """THE SELF-SATISFACTION TEST. `panel_v2_report` emits
    `bar_provenance_block` and then checks for that block's own strings — so
    the guard could not fail for any report it produced. It must still fail
    when the *tables* it wraps lose their tier labels, which the block cannot
    supply. # MUTATION-VERIFIED"""
    b = _small(ps=B.passages(behaviour, "openai"))
    ev = B.cell_evaluate(b, set(), "openai", clauses=clauses, spec="alpha")
    honest = B.cell_table({("synthetic", "openai"): ev}, "tool")
    # strip the tier column values — the table now quotes `judge MCC` with no
    # indication of whose judgement it is.
    stripped = honest.replace("| small |", "|  |")
    md = B.bar_provenance_block({"synthetic": b}) + "\n" + stripped
    assert B.check_bar_provenance(
        B.bar_provenance_block({"synthetic": b}) + "\n" + honest,
        {"synthetic": b}) is True
    with pytest.raises(B.BarProvenanceError, match="section"):
        B.check_bar_provenance(md, {"synthetic": b})


# ================================================================
#  QUERY MODULES — relevance vs structural vs section, one gold
# ================================================================
#
# For three cycles `benchmark.py` routed EVERY mode through
# `relevance.RelevanceIndex`, so the two modules the contract calls compliant
# could not produce a headline number at all and every number the project
# reported came from the module the contract says violates invariant 10.
# These tests pin the property that fixes it: any query module, the SAME gold.

import os as _os

_REAL_ANN = _p("annotations_b8.json")
_REAL_ATOMS = _p("behavior_atoms_b8.json")


def _has_real_artifacts():
    return _os.path.exists(_REAL_ANN) and _os.path.exists(_REAL_ATOMS)


@pytest.fixture(scope="module")
def real_query_inputs():
    if not _has_real_artifacts():
        pytest.skip("real artifacts not present")
    import relevance
    rows, _ = B.load_clauses()
    return rows, relevance.load_annotations(_REAL_ANN), _REAL_ATOMS


def test_every_declared_query_module_can_be_built_and_predicts(
        real_query_inputs):
    """THE DEFECT. `structural.py` and `section.py` could not produce a
    headline number at all: nothing in this file could turn either into a
    `{slug: [clause_id]}` prediction. Each must now do so."""
    rows, ann, atoms = real_query_inputs
    panel = B.load_true_panel(spec_keys=("openai",))
    for name in B.QUERY_MODULES:
        qm = B.build_query_module(name, panel, rows, annotations=ann,
                                  atoms=atoms)
        assert qm.slugs, f"{name}: no behaviour could be queried"
        for slug in qm.slugs:
            pred = qm.predict(slug)
            assert isinstance(pred, set)
            assert pred, f"{name}/{slug}: predicts nothing at all"
            assert len(pred) < 0.9 * len(rows), (
                f"{name}/{slug}: predicts {len(pred)}/{len(rows)} — degenerate")


def test_the_selector_rejects_a_module_it_does_not_know(real_query_inputs):
    rows, ann, atoms = real_query_inputs
    with pytest.raises(ValueError, match="unknown query module"):
        B.build_query_module("bag_of_wishes", {}, rows, annotations=ann,
                             atoms=atoms)


def test_all_modules_score_through_the_identical_gold_universe_and_join(
        real_query_inputs):
    """THE POINT OF THE EXERCISE. Side-by-side is only meaningful if the gold,
    the universe and the clause->passage join are byte-identical across
    modules; otherwise the comparison measures the harness.

    # MUTATION-VERIFIED: building one module over a truncated clause list — the
    # failure mode where a module reaches for its OWN `CLAUSES` default instead
    # of the corpus it was handed — turns this red on `clause_ids`."""
    rows, ann, atoms = real_query_inputs
    panel = B.load_true_panel(spec_keys=("openai",))
    slug = sorted(panel)[0]
    joins = {(slug, "openai"): B.clause_joins(panel[slug], rows, "openai")}
    evs, corpora = {}, {}
    for name in B.QUERY_MODULES:
        qm = B.build_query_module(name, panel, rows, annotations=ann,
                                  atoms=atoms)
        corpora[name] = qm.clause_ids
        if slug not in qm.slugs:
            continue
        evs[name] = B.cell_results({slug: panel[slug]},
                                   qm.predictions("openai", slugs=[slug]),
                                   spec_keys=("openai",), joins=joins,
                                   clauses={"openai": rows})[(slug, "openai")]
    assert len(evs) == len(B.QUERY_MODULES)
    # SAME CORPUS. Every module must have indexed the clause list it was
    # handed, not one of its own module-level defaults.
    want = [str(c["id"]) for c in rows]
    for name, got in corpora.items():
        assert got == want, (
            f"{name} indexed {len(got)} clauses, not the {len(want)} it was "
            f"given — it is scoring a different corpus from its rivals")
    ref = evs["relevance"]
    for name, ev in evs.items():
        assert ev["n_passages"] == ref["n_passages"], f"{name}: other universe"
        assert ev["floor_b_mcc_mean"] == ref["floor_b_mcc_mean"], (
            f"{name}: other join — FLOOR B is a property of the join alone")
        assert ev["judge_mcc_mean_full"] == ref["judge_mcc_mean_full"], (
            f"{name}: other gold — the judges' own number must not move")
        for j, row in ev["per_target"].items():
            assert row["gold_full"] == ref["per_target"][j]["gold_full"], (
                f"{name}/{j}: a different gold set")


def test_the_relevance_module_stays_label_free(real_query_inputs):
    """⚠️ `relevance.DEFAULT_THRESHOLD = 0.18` is an IN-SAMPLE ARGMAX over the
    very panel this scores against and was only just retired from this file.
    The module wrapper must call `predict(b)` (Otsu, from the query's own score
    distribution) and must not silently reacquire the fitted constant."""
    import relevance
    rows, ann, atoms = real_query_inputs
    panel = B.load_true_panel(spec_keys=("openai",))
    qm = B.build_query_module("relevance", panel, rows, annotations=ann,
                              atoms=atoms)
    idx = relevance.RelevanceIndex(rows, ann)
    batoms = relevance.load_behaviour_atoms(atoms)
    differs = 0
    for slug in qm.slugs:
        q = relevance.behaviour_from_panel(panel[slug], batoms)
        assert qm.predict(slug) == idx.predict(q), (
            f"{slug}: the module wrapper is not the label-free path")
        if idx.predict(q) != idx.predict(q, relevance.DEFAULT_THRESHOLD):
            differs += 1
    assert differs, (
        "the label-free cut and the fitted constant agree everywhere, so this "
        "test cannot tell them apart — it is not guarding anything")


def test_benchmark_never_names_the_fitted_threshold_in_live_code():
    """The retirement must not be cosmetic a second time. Reintroducing
    `relevance.DEFAULT_THRESHOLD` anywhere in this module's EXECUTABLE source
    (comments and docstrings explaining the retirement are fine) puts every
    reported number back on the in-sample argmax. # MUTATION-VERIFIED"""
    import ast
    src = open(_p("benchmark.py")).read()
    tree = ast.parse(src)
    named = [n for n in ast.walk(tree)
             if isinstance(n, ast.Attribute) and n.attr == "DEFAULT_THRESHOLD"]
    assert not named, (
        f"benchmark.py reads relevance.DEFAULT_THRESHOLD at "
        f"line(s) {[n.lineno for n in named]} — that constant is the in-sample "
        "argmax of a 51-point grid on THIS panel (worth a spurious +0.042 mean "
        "MCC). The default must stay label-free.")


# ---------------------------------------------------- the comparison table

def _fake_comparison():
    """A hand-built comparison result, so the renderer and its guard are
    testable without the 589-passage panel."""
    slugs = ["alpha", "beta"]
    draws = ["d0", "d1"]
    mcc = {}
    for i, m in enumerate(("relevance", "structural", "section", "control")):
        for d in draws:
            for j, s in enumerate(slugs):
                mcc[(m, d, s)] = 0.30 - 0.05 * i + 0.01 * j
    return {
        "spec_key": "openai", "slugs": slugs, "draws": draws,
        "modules": ("relevance", "structural", "section", "control"),
        "mcc": mcc,
        "judge": {s: 0.51 for s in slugs},
        "floor_a": {s: 0.0 for s in slugs},
        "floor_b": {s: -0.03 for s in slugs},
        "n_passages": {s: 589 for s in slugs},
        "tier": {s: "small" for s in slugs},
        "roster": ["gpt-mini", "haiku", "qwen-small"],
        "noise_floor": {"resamples": 10, "cells": 2, "lo": -0.03, "hi": 0.03,
                        "half_width": 0.0295, "mean": 0.0},
        "deltas": {("structural", "relevance"): (-0.038, -0.060, -0.017),
                   ("section", "relevance"): (-0.086, -0.111, -0.061),
                   ("structural", "control"): (0.061, 0.032, 0.090)},
        "missing": {},
    }


def test_the_comparison_table_has_one_row_per_module_and_one_column_per_cell():
    md = B.module_comparison_table(_fake_comparison())
    for name in ("relevance", "structural", "section"):
        assert f"`{name}.py`" in md, f"{name} is not a row of the table"
    assert "lexical control" in md
    assert "| alpha |" in md or "alpha" in md
    # the mean must not be the only number
    assert md.count("\n|") > 6


def test_the_comparison_table_cannot_omit_the_floors():
    """FLOOR A (0.000) and FLOOR B (chance under the coverage gap) go beside
    every number, and the lexical control is a row, not a footnote. A table
    without them lets a module that has learned nothing read as a result."""
    md = B.module_comparison_table(_fake_comparison())
    assert B.check_module_comparison(md) is True
    for missing in ("FLOOR A", "FLOOR B", "lexical control"):
        broken = md.replace(missing, "xxx")
        with pytest.raises(B.ModuleComparisonError, match="(?i)floor|control"):
            B.check_module_comparison(broken)


def test_the_comparison_guard_demands_more_than_one_atom_draw():
    """A single draw quoted as a constant is an error this project has made
    twice. The table has to show every draw."""
    md = B.module_comparison_table(_fake_comparison())
    assert "5 draws" in md or "2 draws" in md
    with pytest.raises(B.ModuleComparisonError, match="(?i)draw"):
        B.check_module_comparison(md.replace("draws", "draw"))


def test_the_comparison_guard_refuses_a_single_draw():
    """`--behaviour-atoms one.json` would otherwise produce a perfectly
    well-formed table off ONE draw. The between-draw sd (0.014 on
    `structural`) is a third of the difference between the modules."""
    cmp = _fake_comparison()
    cmp["draws"] = ["d0"]
    cmp["mcc"] = {k: v for k, v in cmp["mcc"].items() if k[1] == "d0"}
    with pytest.raises(B.ModuleComparisonError, match="(?i)1 atom draw"):
        B.check_module_comparison(B.module_comparison_table(cmp))


def test_the_comparison_guard_demands_a_paired_bootstrap_interval():
    cmp = _fake_comparison()
    md = B.module_comparison_table(cmp) + B.module_bootstrap_block(cmp)
    assert B.check_module_comparison(md) is True
    with pytest.raises(B.ModuleComparisonError, match="(?i)noise floor"):
        B.check_module_comparison(md.replace("noise floor", "xxx"))


def test_the_bootstrap_block_states_every_pairwise_difference_with_its_ci():
    md = B.module_bootstrap_block(_fake_comparison())
    assert "structural" in md and "relevance" in md
    assert "-0.0380" in md or "-0.038" in md
    assert "95% CI" in md
    assert "0.0295" in md, "the RE-DERIVED noise floor must be printed"
    assert "0.045" not in md, "the expired 3-behaviour noise constant is refused"


def test_the_per_draw_table_prints_all_draws_never_the_mean_alone():
    md = B.module_draw_table(_fake_comparison())
    for d in ("d0", "d1"):
        assert d in md
    assert "sd" in md.lower()


def test_the_comparison_report_labels_the_small_model_bar(real_query_inputs):
    """The comparison quotes the judges' own column, so it is subject to the
    same bar-provenance rule as everything else — and it runs the rebuilt
    guard on its own output."""
    cmp = _fake_comparison()
    md = B.module_comparison_report(cmp)
    assert "small-model panel" in md.lower()
    assert "not the frontier bar" in md.lower()
    for m in ("gpt-mini", "haiku", "qwen-small"):
        assert m in md.lower()


def test_the_comparison_report_refuses_to_drop_the_tier_disclaimer(monkeypatch):
    cmp = _fake_comparison()
    monkeypatch.setattr(B, "comparison_bar_block", lambda _c: "judges: some\n")
    with pytest.raises(AssertionError):
        B.module_comparison_report(cmp)


# ------------------------------------------------------------------ the CLI

def test_the_cli_accepts_a_query_module_with_tool_and_panel_v2():
    for mode in ("--tool", "--panel-v2"):
        opts = B._parse_args([mode, "--query-module", "structural"])
        assert opts["query_module"] == "structural"
    assert B._parse_args(["--tool"])["query_module"] == "relevance"


def test_the_cli_rejects_an_unknown_query_module():
    with pytest.raises(SystemExit, match="(?i)query-module"):
        B._parse_args(["--tool", "--query-module", "nope"])


def test_the_cli_has_a_compare_modules_mode():
    assert B._parse_args(["--compare-modules"])["mode"] == "compare-modules"


def test_modes_that_are_relevance_only_refuse_another_module():
    """`--ablate` / `--sweep` / `--operating-point` read channel weights and
    threshold sweeps that only the bag scorer has. Refusing is honest;
    silently running relevance under another module's name is not."""
    for mode in ("--ablate", "--sweep", "--operating-point"):
        with pytest.raises(SystemExit, match="(?i)only .*relevance"):
            B._parse_args([mode, "--query-module", "structural"])
