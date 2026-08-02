"""Tests for panel_universe — the TRUE judged universe loader.

The defect this module exists to fix: the panel graded EVERY passage of the
spec in one prompt (589 for the model spec, 374 for the constitution), but
`build_site_data.keeps_citation` dropped every passage whose summed score was
0 before publishing. The published file therefore holds 377/333/153 passages
for the three model-spec behaviours — 212/256/436 true negatives deleted.

These tests assert against the REAL data, not fixtures, wherever the point is
that the real data has a particular shape.
"""
from __future__ import annotations

import copy
import json

import pytest

import benchmark as B
import panel_universe as U

SLUGS = ("helpfulness", "harm-avoidance-to-third-parties",
         "avoiding-over-and-under-caution")
PUBLISHED_OPENAI = {"helpfulness": 377,
                    "harm-avoidance-to-third-parties": 333,
                    "avoiding-over-and-under-caution": 153}
PUBLISHED_ANTHROPIC = {"helpfulness": 197,
                       "harm-avoidance-to-third-parties": 199,
                       "avoiding-over-and-under-caution": 77}


# --------------------------------------------------------- the universe size

def test_model_spec_universe_is_589_passages():
    """The judges saw 589 passages, not the published 377/333/153."""
    ps = U.spec_passages("model-spec")
    assert len(ps) == 589


def test_constitution_universe_is_374_passages():
    assert len(U.spec_passages("constitution")) == 374


def test_every_behaviour_gets_the_whole_universe_not_the_published_subset():
    panel = U.load_universe()
    for slug in SLUGS:
        n = len(B.passages(panel[slug], "openai"))
        assert n == 589, f"{slug}: {n}"
        assert n != PUBLISHED_OPENAI[slug]


def test_recovered_zero_count_is_the_published_shortfall():
    prov = U.load_universe(with_provenance=True)[1]
    for slug in SLUGS:
        p = prov[(slug, "openai")]
        assert p["universe"] == 589
        assert p["published"] == PUBLISHED_OPENAI[slug]
        assert p["recovered_zero"] == 589 - PUBLISHED_OPENAI[slug]
    assert {prov[(s, "openai")]["recovered_zero"] for s in SLUGS} == {212, 256, 436}


# ------------------------------------------------------------------ the join

def test_every_published_passage_joins_to_a_universe_passage():
    _, prov = U.load_universe(with_provenance=True)
    for key, p in prov.items():
        assert p["join_rate"] == 1.0, f"{key}: {p['unjoined']}"
        assert p["unjoined"] == []


def test_an_unjoinable_published_passage_is_a_hard_error_not_a_silent_drop():
    pub = B.load_panel()
    b = copy.deepcopy(pub["helpfulness"])
    b["coverage"]["openai"]["passages"][0]["locator"] = "model-spec@nope > #x > ¶99"
    with pytest.raises(U.UnjoinablePassage) as e:
        U.recover_behaviour(b, "openai")
    assert "model-spec@nope" in str(e.value)


def test_universe_ids_are_locators_and_unique():
    panel = U.load_universe()
    ps = B.passages(panel["helpfulness"], "openai")
    ids = [p["id"] for p in ps]
    assert len(set(ids)) == len(ids) == 589
    assert all(p["id"] == p["locator"] for p in ps)


def test_published_verdicts_are_carried_through_unchanged():
    pub = B.load_panel()
    panel = U.load_universe()
    for slug in SLUGS:
        by_loc = {p["locator"]: p for p in B.passages(panel[slug], "openai")}
        for p in B.passages(pub[slug], "openai"):
            got = by_loc[p["locator"]]
            assert got["verdicts"] == p["verdicts"]
            assert got["score"] == p["score"]
            assert got["published_id"] == p["id"]


# ------------------------------------------------------- the recovered zeros

def test_recovered_passages_carry_verdict_zero_for_every_judge():
    panel = U.load_universe()
    for slug in SLUGS:
        js = B.judges(panel[slug], "openai")
        assert len(js) == 3
        rec = [p for p in B.passages(panel[slug], "openai") if p["recovered"]]
        assert rec
        for p in rec:
            assert set(p["verdicts"]) == set(js)
            assert set(p["verdicts"].values()) == {0}
            assert p["score"] == 0


def test_recovered_passages_are_gold_negative_under_every_pair_gold():
    panel = U.load_universe()
    for slug in SLUGS:
        rec = {p["id"] for p in B.passages(panel[slug], "openai") if p["recovered"]}
        for j, t in B.pair_targets(panel[slug], 1, "openai").items():
            assert not (t["gold"] & rec), f"{slug}/{j}"
            assert not (t["pred"] & rec), f"{slug}/{j}"


def test_score_still_equals_sum_of_verdicts_everywhere():
    panel = U.load_universe()
    for slug in SLUGS:
        v = B.verify_verdicts(panel[slug], "openai")
        assert v["mismatch"] == [] and v["missing_verdicts"] == []
        assert v["total"] == 589


def test_judge_names_still_parse_from_role_text_on_the_true_universe():
    """`panel_judge_names` reads the `role` free text; recovered rows must
    supply one or the cross-check silently loses judges."""
    panel = U.load_universe()
    for slug in SLUGS:
        names = B.panel_judge_names(panel[slug], "openai")
        assert len(names) == 3
        vr = B.verify_role_parse(panel[slug], "openai")
        assert vr["mismatch"] == []


# ------------------------------------------------------------- quote fidelity

def test_local_citation_quote_matches_the_mvp_builder_on_every_passage():
    """`panel_universe` re-implements build_site_data's quote rule so it has no
    import-time dependency on the mvp repo's config. If the copy ever drifts,
    recovered quotes stop matching the clause join and the numbers move."""
    bsd = U._mvp_build_site_data()
    for loc, sec, text in U.spec_passages("model-spec"):
        assert U.citation_quote(text) == bsd.citation_quote(text), loc


def test_recovered_quotes_equal_the_published_quotes_where_they_overlap():
    pub = B.load_panel()
    panel = U.load_universe()
    by_loc = {p["locator"]: p for p in B.passages(panel["helpfulness"], "openai")}
    for p in B.passages(pub["helpfulness"], "openai"):
        assert by_loc[p["locator"]]["quote"] == p["quote"]
        assert by_loc[p["locator"]]["exampleBlock"] == p["exampleBlock"]


# ------------------------------------------------------- spec swappability

def test_anthropic_side_loads_through_the_same_code_path():
    panel, prov = U.load_universe(with_provenance=True)
    for slug in SLUGS:
        assert len(B.passages(panel[slug], "anthropic")) == 374
        p = prov[(slug, "anthropic")]
        assert p["spec"] == "constitution"
        assert p["published"] == PUBLISHED_ANTHROPIC[slug]
        assert p["recovered_zero"] == 374 - PUBLISHED_ANTHROPIC[slug]
        assert p["join_rate"] == 1.0


def test_spec_key_selects_which_side_is_recovered():
    panel = U.load_universe(spec_keys=("openai",))
    pub = B.load_panel()
    assert len(B.passages(panel["helpfulness"], "openai")) == 589
    # untouched side stays exactly as published
    assert (len(B.passages(panel["helpfulness"], "anthropic"))
            == len(B.passages(pub["helpfulness"], "anthropic")) == 197)


def test_unknown_spec_key_is_an_error_not_a_silent_passthrough():
    with pytest.raises(KeyError):
        U.spec_for_key("gemini")


# ------------------------------------------------------------- provenance

def test_provenance_block_states_universe_published_recovered_and_join_rate():
    _, prov = U.load_universe(with_provenance=True)
    md = U.provenance_block(prov)
    assert "589" in md and "377" in md and "212" in md
    assert "join" in md.lower()
    assert "374" in md            # the constitution side is in the same block
    for line in md.splitlines():
        assert "%" not in line or "join" in line.lower() or "|" in line


def test_provenance_is_json_serializable():
    _, prov = U.load_universe(with_provenance=True)
    json.dumps({f"{k[0]}/{k[1]}": v for k, v in prov.items()})


# ------------------------------------------------- the point of the exercise

def test_the_true_universe_restores_true_negatives_the_published_one_deleted():
    """The recovered rows are exactly the ones every judge called irrelevant:
    deleting them deletes true-negative credit the judges earned."""
    pub, panel = B.load_panel(), U.load_universe()
    for slug in SLUGS:
        loc = {p["id"]: p["locator"] for p in B.passages(pub[slug], "openai")}
        for j, t in B.pair_targets(panel[slug], 1, "openai").items():
            pub_t = B.pair_targets(pub[slug], 1, "openai")[j]
            # golds and predictions are unchanged (ids are re-keyed to locators)
            assert t["gold"] == {loc[i] for i in pub_t["gold"]}
            assert t["pred"] == {loc[i] for i in pub_t["pred"]}
        # ...only the universe grew, which is where the true negatives live.
        assert len(B.passages(panel[slug], "openai")) > len(B.passages(pub[slug], "openai"))
