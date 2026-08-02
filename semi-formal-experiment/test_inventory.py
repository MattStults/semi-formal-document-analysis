"""Tests for inventory.py — the focus-area -> row adapter."""
import json
import os
import re

import pytest

import inventory


@pytest.fixture(scope="module")
def rows():
    return inventory.load_section()


@pytest.fixture(scope="module")
def raw_section():
    return [
        r
        for r in inventory.load_raw()
        if r["top_level_section"] == "The chain of command"
    ]


def test_section_row_count(rows):
    assert len(rows) == 62


def test_conditional_count(rows):
    assert len(inventory.conditional(rows)) == 42


def test_no_rows_collapsed(rows, raw_section):
    """Every focus area survives, one row each, source_id join intact."""
    assert [r["source_id"] for r in rows] == [r["focus_id"] for r in raw_section]
    assert len({r["source_id"] for r in rows}) == 62


def test_all_ids_are_legal_asp_constants(rows):
    pat = re.compile(r"^[a-z][a-z0-9_]*$")
    bad = [r["id"] for r in rows if not pat.match(r["id"])]
    assert bad == []


def test_thirteen_source_ids_are_illegal_and_uniformly_prefixed(rows):
    pat = re.compile(r"^[a-z][a-z0-9_]*$")
    illegal = [r["source_id"] for r in rows if not pat.match(r["source_id"])]
    assert len(illegal) == 13, illegal
    assert all(i[0].isdigit() for i in illegal)
    # uniform rule: every id is prefixed, not just the illegal ones
    assert all(r["id"] == "fa_" + r["source_id"] for r in rows)


def test_verify_passes_for_all_rows(rows):
    assert inventory.verify(rows) is True


def test_quotes_are_verbatim(rows):
    text = inventory.spec_text()
    assert all(r["quote"] in text for r in rows)


def test_quote_is_the_text_field_verbatim(rows, raw_section):
    assert [r["quote"] for r in rows] == [r["text"] for r in raw_section]


def test_marked_span_preserved(rows, raw_section):
    assert [r["marked_span"] for r in rows] == [r["marked_span"] for r in raw_section]
    # sub-sentence anchors: at least some spans are strictly shorter than the
    # quote they were cut from, and none were dropped
    assert all(r["marked_span"] for r in rows)
    assert any(len(r["marked_span"]) < len(r["quote"]) for r in rows)


def test_locator_format(rows):
    pat = re.compile(
        r"^model_spec@2025-12-18 > The chain of command( > [^>]+)? > L\d+ "
        r"\[fa_[a-z0-9_]+\]$"
    )
    bad = [r["locator"] for r in rows if not pat.match(r["locator"])]
    assert bad == []


def test_locator_matches_section_path_line_and_id(rows, raw_section):
    for row, raw in zip(rows, raw_section):
        expected = ("model_spec@2025-12-18 > " + " > ".join(raw["section_path"])
                    + f" > L{raw['line']} [fa_{raw['focus_id']}]")
        assert row["locator"] == expected


def test_line_locators_alone_are_not_unique(rows):
    """The reason the id is in the locator at all: 62 provisions share only 34
    distinct line locators, and 7 of those collisions span different text."""
    from collections import Counter
    raw = inventory.load_raw()
    sec = [r for r in raw if r["top_level_section"] == "The chain of command"]
    bare = [inventory.make_locator(r["section_path"], r["line"]) for r in sec]
    counts = Counter(bare)
    assert len(counts) == 34
    collide = {k for k, n in counts.items() if n > 1}
    assert len(collide) == 11
    spanning_different_text = sum(
        1 for k in collide
        if len({r["text"] for r in sec
                if inventory.make_locator(r["section_path"], r["line"]) == k}) > 1
    )
    assert spanning_different_text == 7


def test_make_locator_without_an_id_keeps_the_old_form():
    assert inventory.make_locator(["The chain of command"], 173) == \
        "model_spec@2025-12-18 > The chain of command > L173"
    assert inventory.make_locator(["The chain of command"], 173, "8ep1") == \
        "model_spec@2025-12-18 > The chain of command > L173 [fa_8ep1]"


def test_locators_are_unique_in_the_section(rows):
    assert inventory.locator_is_unique(rows) is True
    assert len({r["locator"] for r in rows}) == 62


def test_locators_are_unique_across_all_259_focus_areas():
    all_rows = inventory.load_all()
    assert len(all_rows) == 259
    assert inventory.locator_is_unique(all_rows) is True
    assert len({r["locator"] for r in all_rows}) == 259


def test_locator_is_unique_reports_collisions():
    dupe = [
        {"locator": "x", "id": "a"}, {"locator": "x", "id": "b"},
        {"locator": "y", "id": "c"},
    ]
    with pytest.raises(AssertionError) as ei:
        inventory.locator_is_unique(dupe)
    assert "'x'" in str(ei.value)


# ---- quote-containment join ----

def test_match_passage_finds_provisions_inside_a_paragraph(rows):
    row = rows[0]
    passage = "Preamble noise. " + row["quote"] + " Trailing noise."
    got = inventory.match_passage(passage, rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_is_whitespace_insensitive(rows):
    """The source hard-wraps; byte-strict comparison fails on multi-line
    clauses, which is exactly the case that must work."""
    row = max(rows, key=lambda r: len(r["quote"]))
    hardwrapped = row["quote"].replace(" ", "\n   ", 3)
    assert hardwrapped != row["quote"]
    got = inventory.match_passage(hardwrapped, rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_matches_a_fragment_of_a_longer_clause(rows):
    """The panel sometimes cites less than the full sentence."""
    row = max(rows, key=lambda r: len(r["quote"]))
    fragment = row["quote"][10:-10]
    got = inventory.match_passage(fragment, rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_matches_on_marked_span(rows):
    sub = [r for r in rows if len(r["marked_span"]) < len(r["quote"])]
    assert sub, "expected some sub-sentence anchors"
    row = max(sub, key=lambda r: len(r["marked_span"]))
    got = inventory.match_passage("Context. " + row["marked_span"] + " More.", rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_returns_all_matches_not_an_arbitrary_pick(rows):
    """A paragraph holds several provisions; the relation is one-to-many and
    callers must see that."""
    multi = [
        rows[i]["quote"] + " " + rows[i + 1]["quote"]
        for i in range(len(rows) - 1)
        if rows[i]["locator"].rsplit(" > L", 1)[0]
        == rows[i + 1]["locator"].rsplit(" > L", 1)[0]
    ]
    assert multi
    got = inventory.match_passage(multi[0], rows)
    assert len(got) >= 2


def test_every_focus_quote_carries_a_footnote_marker(rows):
    """Why _norm strips them: the stored quotes all carry an inline `[^xxxx]`
    marker that the panel's quotes do not, so byte containment fails on text
    that is otherwise character-for-character identical."""
    marker = re.compile(r"\[\^[a-z0-9]+\]")
    assert all(marker.search(r["quote"]) for r in rows)
    all_rows = inventory.load_all()
    assert all(marker.search(r["quote"]) for r in all_rows)
    # and for some the marker is mid-sentence, where marked_span cannot rescue it
    assert sum(1 for r in all_rows
               if marker.search(r["quote"]) and not marker.search(r["quote"][-12:])) == 25


def test_match_passage_ignores_footnote_markers(rows):
    marker = re.compile(r"\[\^[a-z0-9]+\]")
    row = next(r for r in rows if marker.search(r["quote"]))
    panel_style = marker.sub("", row["quote"])  # how the panel stores it
    assert panel_style != row["quote"]
    got = inventory.match_passage(panel_style, rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_handles_a_midsentence_marker(rows):
    """The case `marked_span` cannot rescue."""
    marker = re.compile(r"\[\^[a-z0-9]+\]")
    mid = [r for r in inventory.load_all()
           if marker.search(r["quote"]) and not marker.search(r["quote"][-12:])]
    assert mid
    row = mid[0]
    all_rows = inventory.load_all()
    got = inventory.match_passage(marker.sub("", row["quote"]), all_rows)
    assert row["id"] in {r["id"] for r in got}


def test_match_passage_returns_empty_for_unrelated_text(rows):
    assert inventory.match_passage("The mitochondrion is the powerhouse.", rows) == []
    assert inventory.match_passage("", rows) == []
    assert inventory.match_passage("   \n  ", rows) == []


def test_verify_rejects_a_tampered_quote(rows):
    tampered = dict(rows[0], quote=rows[0]["quote"] + " ZZZ-not-in-spec")
    with pytest.raises(AssertionError):
        inventory.verify([tampered])


def test_row_shape(rows):
    expected = {
        "id", "source_id", "locator", "quote", "marked_span",
        "kind", "modality", "has_defeater",
    }
    assert all(set(r) == expected for r in rows)


def test_rows_are_json_serializable(rows):
    json.dumps(rows)


def test_summary_matches_contract_facts(rows):
    s = inventory.summarize(rows)
    assert s["rows"] == 62
    assert s["conditional"] == 42
    assert s["conditional_with_defeater"] == 18
    assert s["illegal_source_ids"] == 13
    assert s["modality_on_conditional"] == {
        "must": 10, "should": 17, "should not": 5, "must not": 4, "may": 2,
    }


# ---- join normalization ----
#
# Each case below is a real mismatch class observed against the panel file, not
# a hypothetical. Together they are what moves the join from 377/863 to 849/863,
# so a regression here silently caps every benchmark number downstream.


def test_norm_strips_emphasis_so_example_captions_match():
    """Every example caption is `**Example**:` in source and `Example:` in the
    panel — without this, no example-block passage can ever match (313 of 863)."""
    assert inventory._norm("**Example**: a thing") == "Example: a thing"
    assert inventory._norm("*soft* and `code`") == "soft and code"


def test_norm_strips_footnote_markers_mid_sentence():
    assert inventory._norm("do this[^ab12] always") == "do this always"


def test_variants_yields_both_link_renderings():
    """The panel's renderer emitted link text sometimes and the link target
    other times, so the join has to accept either."""
    assert inventory._variants("see [the rules](#chain_of_command) here") == {
        "see the rules here", "see #chain_of_command here"}


def test_variants_collapses_to_one_when_no_link():
    assert inventory._variants("plain text") == {"plain text"}


def test_match_passage_finds_clause_across_link_rendering():
    rows = [{"quote": "As mentioned in [the letter](#letter_and_spirit), users may.",
             "marked_span": None}]
    for rendered in ("As mentioned in the letter, users may.",
                     "As mentioned in #letter_and_spirit, users may."):
        assert inventory.match_passage(rendered, rows) == rows, rendered


def test_match_passage_tolerates_null_marked_span():
    """Clause rows carry no marked_span; a None must not crash the join."""
    rows = [{"quote": "Always be willing to tell users.", "marked_span": None}]
    assert inventory.match_passage("Always be willing to tell users.", rows)


def test_match_passage_empty_quote_matches_nothing():
    rows = [{"quote": "anything at all", "marked_span": None}]
    assert inventory.match_passage("", rows) == []
    assert inventory.match_passage("   ", rows) == []


def test_spec_md_resolves_to_the_canonical_specs_tree():
    """One source of truth: the specs/ tree, not a per-experiment clone."""
    assert os.path.exists(inventory.SPEC_MD)
    assert "specs/openai-model-spec" in inventory.SPEC_MD
