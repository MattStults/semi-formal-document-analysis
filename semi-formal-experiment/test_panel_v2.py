"""Tests for panel_v2 — the 9-behaviour, 2-spec, SMALL-MODEL panel.

Two things this module must not get wrong, and each has a test that fails if it
is got wrong:

  1. THE UNIVERSE IS TRUNCATED, WORSE THAN THE FIRST PANEL. The export keeps
     `score >= 2`. Score-0 rows are restorable as all-zero; score-1 rows are
     NOT — a real `tangentially related` judgement is gone. The reconstruction
     must restore the full 589/374 universe, the recovered rows must be
     all-zero, and the irrecoverability must be STATED and quantified.

  2. IT IS POWER, NOT A BAR. Its judges are small models. A report may not
     quote a bar off them without naming the roster and disclaiming the tier.

Assertions are against the REAL data wherever the point is that the real data
has a particular shape.
"""
from __future__ import annotations

import ast
import copy
import json

import pytest

import benchmark as B
import panel_v2 as V
import panel_universe as U

SLUGS = ("animal-welfare-impacts", "harmlessness-to-the-user", "helpfulness",
         "objectivity-on-contested-questions",
         "avoiding-over-and-under-caution", "proportionate-risk-mitigation",
         "harm-avoidance-to-third-parties", "how-to-approach-tradeoffs",
         "user-autonomy")

#: Published citation counts per cell, read once off the real export. These are
#: the numbers the reconstruction has to restore FROM.
PUBLISHED = {
    ("animal-welfare-impacts", "anthropic"): 229,
    ("animal-welfare-impacts", "openai"): 240,
    ("avoiding-over-and-under-caution", "anthropic"): 157,
    ("avoiding-over-and-under-caution", "openai"): 312,
    ("harm-avoidance-to-third-parties", "anthropic"): 197,
    ("harm-avoidance-to-third-parties", "openai"): 257,
    ("harmlessness-to-the-user", "anthropic"): 277,
    ("harmlessness-to-the-user", "openai"): 445,
    ("helpfulness", "anthropic"): 199,
    ("helpfulness", "openai"): 391,
    ("how-to-approach-tradeoffs", "anthropic"): 227,
    ("how-to-approach-tradeoffs", "openai"): 310,
    ("objectivity-on-contested-questions", "anthropic"): 122,
    ("objectivity-on-contested-questions", "openai"): 212,
    ("proportionate-risk-mitigation", "anthropic"): 153,
    ("proportionate-risk-mitigation", "openai"): 213,
    ("user-autonomy", "anthropic"): 121,
    ("user-autonomy", "openai"): 252,
}

UNIVERSE = {"openai": 589, "anthropic": 374}


@pytest.fixture(scope="module")
def raw():
    return V.load_raw()


@pytest.fixture(scope="module")
def loaded():
    return V.load_panel(with_provenance=True)


# ------------------------------------------------------------ verdict parsing

def test_parse_verdicts_accepts_the_python_repr_string():
    """The export has been seen in both shapes: a JSON object and a stringified
    Python dict repr. The string form must parse, or every verdict silently
    becomes unreadable."""
    assert V.parse_verdicts("{'gpt-mini': 2, 'haiku': 2, 'qwen-small': 1}") == {
        "gpt-mini": 2, "haiku": 2, "qwen-small": 1}


def test_parse_verdicts_accepts_a_real_mapping():
    assert V.parse_verdicts({"a": 0, "b": 1}) == {"a": 0, "b": 1}


def test_verdict_parsing_never_uses_eval():
    """`eval` on data written by another pipeline executes whatever it holds.
    The ban is checked by reading this module's own source rather than trusted:
    a future edit that reaches for `eval` fails here."""
    src = open(V.__file__).read()
    import re
    assert re.search(r"\beval\s*\(", src) is None, "panel_v2 must not call eval"
    assert "ast.literal_eval" in src


@pytest.mark.parametrize("bad", ["not a dict", "[1, 2]", "{}",
                                 "{'a': 3}", "{'a': -1}", "{'a': 'two'}",
                                 "{'a': True}"])
def test_parse_verdicts_refuses_anything_it_cannot_trust(bad):
    with pytest.raises(V.MalformedVerdicts):
        V.parse_verdicts(bad)


def test_every_verdict_in_the_real_export_parses(raw):
    n = 0
    for e in raw["coverage"]:
        for c in e["citations"]:
            v = V.parse_verdicts(c["verdicts"])
            assert set(v) == set(V.JUDGE_ROSTER)
            n += 1
    assert n == 4314


# --------------------------------------------------------------- the 18 cells

def test_the_export_is_nine_behaviours_by_two_specs(raw):
    cells = V.cells(raw)
    assert len(cells) == 18
    assert sorted({s for s, _ in cells}) == sorted(SLUGS)
    assert sorted({k for _, k in cells}) == ["anthropic", "openai"]


def test_the_score_distribution_has_no_zero_and_no_one(raw):
    """THE truncation evidence, computed rather than asserted in prose. If a
    future export restores score 1 this test fails and the irrecoverability
    caveat must be revisited — which is the point."""
    hist = V.score_histogram(raw)
    assert sorted(hist) == [2, 3, 4, 5, 6]
    assert 0 not in hist and 1 not in hist
    assert min(hist) == V.KEPT_MIN_SCORE


# ------------------------------------------------------------------ the join

def test_every_citation_joins_to_the_reconstructed_universe(loaded):
    _, prov = loaded
    for key, p in prov.items():
        assert p["join_rate"] == 1.0, f"{key}: {p['unjoined']}"
        assert p["unjoined"] == []


def test_join_is_2632_openai_and_1682_anthropic(loaded):
    _, prov = loaded
    for key, n in (("openai", 2632), ("anthropic", 1682)):
        assert sum(p["published"] for k, p in prov.items() if k[1] == key) == n


def test_an_unjoinable_locator_is_refused_not_dropped():
    """A citation joining to nothing is a JUDGED VERDICT about to be deleted.
    Silently dropping it is the defect panel_universe exists to prevent."""
    entry = {"behaviour_slug": "x", "lab_id": "openai",
             "citations": [{"locator": "no-such-locator", "quote": "q",
                            "verdicts": {"a": 2}, "adjacent": True}]}
    with pytest.raises(U.UnjoinablePassage):
        V.recover_cell(entry)


def test_a_duplicate_locator_is_refused():
    loc = U.spec_passages("model-spec")[0][0]
    cite = {"locator": loc, "quote": "q", "verdicts": {"a": 2}, "adjacent": True}
    entry = {"behaviour_slug": "x", "lab_id": "openai",
             "citations": [dict(cite), dict(cite, verdicts={"a": 0})]}
    with pytest.raises(U.UnjoinablePassage):
        V.recover_cell(entry)


def test_a_citation_missing_a_judge_is_refused():
    """A judge absent from one row would read as a fabricated 0."""
    locs = [p[0] for p in U.spec_passages("model-spec")[:2]]
    entry = {"behaviour_slug": "x", "lab_id": "openai", "citations": [
        {"locator": locs[0], "quote": "q", "verdicts": {"a": 2, "b": 2}},
        {"locator": locs[1], "quote": "q", "verdicts": {"a": 2}},
    ]}
    with pytest.raises(V.MalformedVerdicts):
        V.recover_cell(entry)


# ------------------------------------------------------- the restored universe

@pytest.mark.parametrize("slug", SLUGS)
def test_every_cell_gets_the_whole_universe(loaded, slug):
    panel, _ = loaded
    for key, n in UNIVERSE.items():
        got = len(B.passages(panel[slug], key))
        assert got == n, f"{slug}/{key}: {got}"
        assert got != PUBLISHED[(slug, key)]


def test_recovered_count_is_exactly_the_shortfall(loaded):
    _, prov = loaded
    for (slug, key), p in prov.items():
        assert p["published"] == PUBLISHED[(slug, key)]
        assert p["universe"] == UNIVERSE[key]
        assert p["recovered_zero"] == UNIVERSE[key] - PUBLISHED[(slug, key)]


def test_every_recovered_passage_is_all_zero_from_every_judge(loaded):
    """The restoration must not invent a verdict. A recovered row is a passage
    the export dropped because NO judge scored it >= 2 — all-zero is the only
    reading available, and it is what makes the restoration a restoration of
    true-negative credit rather than an invention."""
    panel, _ = loaded
    seen = 0
    for slug in SLUGS:
        for key in UNIVERSE:
            for p in B.passages(panel[slug], key):
                if p["recovered"]:
                    assert set(p["verdicts"]) == set(V.JUDGE_ROSTER)
                    assert set(p["verdicts"].values()) == {0}
                    assert p["score"] == 0
                    seen += 1
    assert seen == sum(UNIVERSE[k] - PUBLISHED[(s, k)]
                       for s in SLUGS for k in UNIVERSE)


def test_published_rows_keep_their_verdicts(loaded, raw):
    panel, _ = loaded
    for e in raw["coverage"]:
        rows = {p["id"]: p for p in
                B.passages(panel[e["behaviour_slug"]], e["lab_id"])}
        for c in e["citations"]:
            row = rows[c["locator"]]
            assert row["recovered"] is False
            assert row["verdicts"] == V.parse_verdicts(c["verdicts"])
            assert row["score"] == sum(row["verdicts"].values())


def test_score_equals_sum_of_verdicts_on_every_row(loaded):
    """`benchmark.verify_verdicts` is a hard gate in main(); it must pass."""
    panel, _ = loaded
    for slug in SLUGS:
        for key in UNIVERSE:
            v = B.verify_verdicts(panel[slug], key)
            assert v["mismatch"] == [] and v["missing_verdicts"] == []
            assert v["total"] == UNIVERSE[key]


def test_the_role_text_reconstructs_the_score(loaded):
    """The export's `role` is literally None on all 4,314 rows. It is rebuilt
    so `verify_role_parse` stays a real cross-check instead of a vacuous one."""
    panel, _ = loaded
    r = B.verify_role_parse(panel["helpfulness"], "openai")
    assert r["mismatch"] == []
    assert r["reconstructed"] == UNIVERSE["openai"]
    assert sorted(r["judges"]) == sorted(V.JUDGE_ROSTER)


def test_quotes_are_re_derived_for_published_rows_too(loaded, raw):
    """Published rows carry the RAW passage text; recovered rows would carry the
    publisher's cleaned quote. Mixing them biases the clause join ALONG THE GOLD
    AXIS, because 'published' means 'some judge saw relevance'. Every row's
    quote is therefore re-derived from the universe text."""
    panel, _ = loaded
    text = {loc: t for loc, _s, t in U.spec_passages("model-spec")}
    differing = 0
    for p in B.passages(panel["helpfulness"], "openai"):
        want, is_ex = U.citation_quote(text[p["locator"]])
        assert p["quote"] == want
        assert p["exampleBlock"] == is_ex
        if p["raw_quote"] is not None and p["raw_quote"] != want:
            differing += 1
    assert differing > 0, ("if no published quote differs from the derived one "
                           "this guard is no longer testing anything")


# ---------------------------------------- score-1 irrecoverability, quantified

def test_the_module_states_that_score_1_is_irrecoverable():
    doc = V.__doc__.lower()
    assert "irrecoverable" in doc
    assert "score 1" in doc or "score-1" in doc
    assert V.IRRECOVERABLE_SCORES == (1,)


def test_provenance_marks_score_1_as_irrecoverable_on_every_cell(loaded):
    _, prov = loaded
    for key, p in prov.items():
        assert p["score_1_present"] is False, key
        assert p["score_1_irrecoverable"] is True, key
        assert p["min_published_score"] == V.KEPT_MIN_SCORE


def test_truncation_cost_is_measured_on_the_overlapping_behaviours():
    """The cost is not asserted, it is MEASURED: the same `score >= 2` rule is
    applied to the FRONTIER panel, where score-1 rows survive, and the judges'
    own numbers are recomputed. Score-1 rows can never be in a pair-gold (that
    needs two judges at >= 1), so the gold is untouched and the whole effect is
    on the JUDGES' predicted sets: their lone `related` calls vanish, their
    false positives with them, and their agreement is flattered."""
    cost = V.truncation_cost()
    assert len(cost) == 6                      # 3 behaviours x 2 specs
    for key, r in cost.items():
        assert r["n_score_1"] > 0, key
        assert r["class_changed"] == r["n_score_1"]
        assert r["gold_changed"] == 0, key
        assert r["judge_mcc_delta"] > 0, key    # truncation INFLATES the judges
    mean = sum(r["judge_mcc_delta"] for r in cost.values()) / len(cost)
    assert mean > 0.05, mean


def test_truncation_block_states_the_limitation_and_shows_numbers():
    md = V.truncation_block(V.truncation_cost())
    low = md.lower()
    assert "irrecoverable" in low
    assert "score-1" in low or "score 1" in low
    assert md.count("\n|") >= 7          # header + rule + 6 cells


def test_apply_v2_truncation_zeroes_only_below_the_kept_minimum():
    ps = [{"id": "p1", "verdicts": {"a": 1, "b": 0, "c": 0}, "score": 1},
          {"id": "p2", "verdicts": {"a": 2, "b": 0, "c": 0}, "score": 2},
          {"id": "p3", "verdicts": {"a": 0, "b": 0, "c": 0}, "score": 0}]
    b = {"slug": "x", "coverage": {"openai": {"passages": ps}}}
    out = V.apply_v2_truncation(b, "openai")
    got = {p["id"]: p["score"] for p in B.passages(out, "openai")}
    assert got == {"p1": 0, "p2": 2, "p3": 0}
    assert B.passages(b, "openai")[0]["score"] == 1   # input not mutated


# --------------------------------------------- spec-key parameterisation

def test_both_spec_keys_load_through_the_identical_code_path(loaded):
    panel, prov = loaded
    for slug in SLUGS:
        assert sorted(panel[slug]["coverage"]) == ["anthropic", "openai"]
    assert {p["spec"] for p in prov.values()} == {"model-spec", "constitution"}


def test_one_spec_key_can_be_loaded_alone():
    """Spec-swappability is the claim; a caller must be able to hold one side."""
    panel = V.load_panel(spec_keys=("anthropic",))
    for b in panel.values():
        assert sorted(b["coverage"]) == ["anthropic"]
        assert len(B.passages(b, "anthropic")) == 374


def test_behaviour_metadata_is_required_not_defaulted():
    """A behaviour with no definition hands `relevance` an empty query and
    scores like a broken tool rather than like a missing input."""
    with pytest.raises(V.MissingBehaviourMetadata):
        V.load_panel(meta_path=_empty_meta())


def _empty_meta():
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump({"behaviours": []}, f)
    return path


def test_every_behaviour_gets_a_name_and_a_definition(loaded):
    panel, _ = loaded
    for slug, b in panel.items():
        assert b["name"], slug
        assert len(b["definition"]) > 20, slug


# -------------------------------------------------------- power, not a bar

def test_every_behaviour_carries_the_small_model_tier(loaded):
    panel, _ = loaded
    for slug, b in panel.items():
        assert B.panel_tier(b) == "small", slug
        assert B.panel_roster(b) == list(V.JUDGE_ROSTER), slug


def test_the_frontier_panel_is_not_labelled_small():
    """Defaulting the other way would silently demote the real bar."""
    for b in B.load_panel().values():
        assert B.panel_tier(b) == "frontier"


def test_provenance_block_names_the_roster_and_disclaims_the_bar(loaded):
    _, prov = loaded
    md = V.provenance_block(prov).lower()
    for m in V.JUDGE_ROSTER:
        assert m in md
    assert "not the frontier bar" in md
    assert "small-model panel" in md


def test_published_panel_keeps_only_the_export_rows(loaded):
    panel, _ = loaded
    pub = V.published_panel(panel)
    for slug in SLUGS:
        for key in UNIVERSE:
            assert len(B.passages(pub[slug], key)) == PUBLISHED[(slug, key)]
            assert all(not p["recovered"] for p in B.passages(pub[slug], key))
            # the input is untouched
            assert len(B.passages(panel[slug], key)) == UNIVERSE[key]
