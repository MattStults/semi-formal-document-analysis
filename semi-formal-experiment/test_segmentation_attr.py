"""Tests for `segmentation_attr` — Step 2 of LADDER_PLAN.md.

The module answers one question per missing phrase: is the content the
read-back judge says a reader would not know present in the clause's OWN
text, or only in an ADJACENT clause of the same section? The second case is
a SEGMENTATION loss, which no atom / vocabulary / grammar change can fix.

Everything here is offline and deterministic. No network, no API.
"""
import json
import os

import pytest

import segmentation_attr as sa

HERE = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------
# fixtures: tiny synthetic corpora, so the unit tests do not move when the
# real artifacts are re-run.

def _clause(cid, section, quote, kind="conditional"):
    return {"id": cid, "section_id": section, "kind": kind, "quote": quote,
            "locator": f"spec > {section} > {cid}", "section_path": [section]}


@pytest.fixture
def rows():
    return [
        _clause("c1", "sec_a", "The assistant must not reveal the password."),
        _clause("c2", "sec_a", "Unless the user is the account owner, in which "
                               "case disclosure is permitted."),
        _clause("c3", "sec_a", "Tools are called with a recipient field."),
        _clause("c4", "sec_b", "Colours should be described plainly."),
    ]


# --------------------------------------------------------------------------
# content keys / coverage


def test_content_keys_drops_stopwords_and_markdown():
    # `inventory._norm` strips emphasis and footnote markers; stopwords carry
    # no content, so "the assistant must not" is nothing but `assistant`.
    assert sa.content_keys("The assistant *must* not[^ab12]") == {"assistant"}


def test_content_keys_conflates_inflections():
    # Judge phrases are paraphrases: "instructions" vs "instruction" is not a
    # difference in content and must not cost coverage.
    assert sa.content_keys("instructions") == sa.content_keys("instruction")


def test_coverage_is_one_when_every_content_word_is_present():
    text = "The assistant must strive to follow all applicable instructions."
    assert sa.coverage("All applicable instructions must be followed", text) == 1.0


def test_coverage_is_zero_for_disjoint_content():
    assert sa.coverage("password disclosure", "colours described plainly") == 0.0


def test_coverage_of_an_empty_phrase_is_zero_not_a_crash():
    assert sa.coverage("the of and", "anything at all") == 0.0


def test_coverage_is_asymmetric_phrase_over_text():
    # A short phrase inside a long clause is fully covered; the long clause is
    # not covered by the short phrase. Direction is load-bearing.
    long = "the assistant must not reveal the password to third parties"
    assert sa.coverage("reveal password", long) == 1.0
    assert sa.coverage(long, "reveal password") < 1.0


# --------------------------------------------------------------------------
# neighbourhood


def test_neighbours_are_same_section_only(rows):
    got = [r["id"] for r in sa.neighbours(rows, "c3", window=2)]
    assert got == ["c1", "c2"]          # c4 is in sec_b


def test_neighbours_exclude_the_clause_itself(rows):
    assert "c2" not in [r["id"] for r in sa.neighbours(rows, "c2", window=2)]


def test_neighbours_respect_the_window(rows):
    assert [r["id"] for r in sa.neighbours(rows, "c3", window=1)] == ["c2"]


def test_neighbours_of_an_unknown_clause_is_empty(rows):
    assert sa.neighbours(rows, "nope", window=2) == []


# --------------------------------------------------------------------------
# the verdict


def test_phrase_present_in_own_text_is_attributed_to_the_clause(rows):
    rec = sa.attribute_phrase("The password must not be revealed", rows[0],
                              sa.neighbours(rows, "c1"))
    assert rec["verdict"] == "own"


def test_phrase_only_in_a_neighbour_is_a_segmentation_loss(rows):
    # "the account owner may have it disclosed" lives in c2, not c1.
    rec = sa.attribute_phrase("Disclosure is permitted for the account owner",
                              rows[0], sa.neighbours(rows, "c1"))
    assert rec["verdict"] == "segmentation"
    assert rec["best_neighbour"] == "c2"


def test_phrase_found_nowhere_is_unlocated_not_silently_own(rows):
    # A paraphrase with no lexical anchor must NOT be scored as located; the
    # honest answer is that the lexical test cannot decide it.
    rec = sa.attribute_phrase("Cryptographic key rotation cadence", rows[0],
                              sa.neighbours(rows, "c1"))
    assert rec["verdict"] == "unlocated"


def test_unlocated_records_whether_a_neighbour_was_the_better_match(rows):
    rec = sa.attribute_phrase("owner", rows[0], sa.neighbours(rows, "c1"))
    assert rec["verdict"] in ("segmentation", "unlocated")
    assert "neighbour_better" in rec


def test_verdict_records_the_two_coverages_for_audit(rows):
    rec = sa.attribute_phrase("password", rows[0], sa.neighbours(rows, "c1"))
    assert rec["coverage_own"] == 1.0
    assert 0.0 <= rec["coverage_neighbour"] <= 1.0


def test_tau_is_a_parameter_so_sensitivity_can_be_reported(rows):
    phrase = "revealing the account password to an owner"
    strict = sa.attribute_phrase(phrase, rows[0], sa.neighbours(rows, "c1"),
                                 tau=1.0)
    loose = sa.attribute_phrase(phrase, rows[0], sa.neighbours(rows, "c1"),
                                tau=0.4)
    assert strict["verdict"] != loose["verdict"]


# --------------------------------------------------------------------------
# aggregation


def test_summarize_counts_verdicts_overall_and_per_kind():
    recs = [
        {"kind": "conditional", "verdict": "own", "neighbour_better": False},
        {"kind": "conditional", "verdict": "segmentation",
         "neighbour_better": True},
        {"kind": "meta", "verdict": "unlocated", "neighbour_better": False},
    ]
    s = sa.summarize(recs)
    assert s["total"] == 3
    assert s["counts"] == {"own": 1, "segmentation": 1, "unlocated": 1}
    assert s["per_kind"]["conditional"]["counts"]["segmentation"] == 1
    assert s["per_kind"]["meta"]["total"] == 1


def test_summarize_reports_a_band_not_a_point_estimate():
    # Lexical containment CANNOT resolve `unlocated`. Reporting only the
    # confirmed share would understate; reporting seg+unlocated would
    # overstate. Both bounds, always.
    recs = [{"kind": "meta", "verdict": "own", "neighbour_better": False},
            {"kind": "meta", "verdict": "segmentation",
             "neighbour_better": True},
            {"kind": "meta", "verdict": "unlocated", "neighbour_better": False},
            {"kind": "meta", "verdict": "unlocated", "neighbour_better": False}]
    s = sa.summarize(recs)
    assert s["segmentation_share_low"] == pytest.approx(0.25)
    assert s["segmentation_share_high"] == pytest.approx(0.75)
    assert s["segmentation_share_low"] < s["segmentation_share_high"]


# --------------------------------------------------------------------------
# structural segmentation defects (independent of the phrase test)


def test_orphan_item_detects_a_list_item_severed_from_its_lead_in():
    rows = [
        _clause("a1", "s", "It must not pursue any of the following:"),
        _clause("a2", "s", "revenue or upsell for providers."),
        _clause("a3", "s", "model-enhancing aims such as self-preservation."),
        _clause("a4", "s", "A new sentence that stands on its own."),
    ]
    flags = sa.structural_flags(rows)
    assert flags["a1"]["orphan_item"] is False
    assert flags["a2"]["orphan_item"] is True
    assert flags["a3"]["orphan_item"] is True   # chains past the first item
    assert flags["a4"]["orphan_item"] is False  # capitalised: chain broken


def test_bare_condition_detects_an_antecedent_with_no_consequent():
    rows = [
        _clause("b1", "s", "The assistant should take special care when:"),
        _clause("b2", "s", "If an instruction seems misaligned with intent."),
        _clause("b3", "s", "If the user asks, the assistant must comply."),
    ]
    flags = sa.structural_flags(rows)
    assert flags["b2"]["bare_condition"] is True
    assert flags["b3"]["bare_condition"] is False   # has a modal consequent


def test_structural_flags_marks_lowercase_starts_as_fragments():
    rows = [_clause("x", "s", "model-enhancing aims such as self-preservation.")]
    assert sa.structural_flags(rows)["x"]["fragment_start"] is True


# --------------------------------------------------------------------------
# atom licensing spans (prior work: 1629/1629 inside their own clause)


def test_span_containment_flags_an_atom_licensed_by_a_neighbour(rows):
    ann = {
        "c1": [{"name": "pwd", "quote": "must not reveal the password"}],
        "c3": [{"name": "owner", "quote": "the account owner"}],   # from c2
    }
    rep = sa.span_containment(rows, ann)
    assert rep["atoms"] == 2
    assert rep["outside_own_clause"] == 1
    assert rep["offenders"][0]["clause_id"] == "c3"


def test_span_containment_is_normalized_not_byte_strict(rows):
    # Emphasis and footnote markers are source-encoding noise; a span that
    # differs from the clause only by them is INSIDE it.
    ann = {"c1": [{"name": "pwd", "quote": "must *not* reveal[^zz9] the password"}]}
    assert sa.span_containment(rows, ann)["outside_own_clause"] == 0


# --------------------------------------------------------------------------
# sampling for the hand-check (the error-rate estimate)


def test_sample_is_deterministic_under_a_seed():
    recs = [{"clause_id": f"c{i}", "phrase": f"p{i}", "verdict": "own",
             "kind": "meta"} for i in range(50)]
    assert sa.sample(recs, n=7, seed=11) == sa.sample(recs, n=7, seed=11)
    assert sa.sample(recs, n=7, seed=11) != sa.sample(recs, n=7, seed=12)


def test_sample_returns_n_records_and_never_more_than_available():
    recs = [{"clause_id": "c", "phrase": f"p{i}", "verdict": "own",
             "kind": "meta"} for i in range(5)]
    assert len(sa.sample(recs, n=3, seed=1)) == 3
    assert len(sa.sample(recs, n=99, seed=1)) == 5


# --------------------------------------------------------------------------
# the hand check itself: a committed label set, and the discrepancy it buys


def test_hand_check_labels_are_committed_and_legal():
    assert len(sa.HAND_CHECK) >= 40, "an error rate needs a real sample"
    assert set(sa.HAND_CHECK.values()) <= {"own", "segmentation", "unlocated"}


def test_hand_check_keys_all_resolve_to_real_missing_phrases():
    recs = sa.attribute_all()
    keys = {sa.phrase_key(r["clause_id"], r["phrase"]) for r in recs}
    assert set(sa.HAND_CHECK) <= keys, "a hand label with no phrase behind it"


def test_hand_check_report_quantifies_the_lexical_error_rate():
    rep = sa.hand_check_report()
    assert rep["n"] == len(sa.HAND_CHECK)
    assert 0.0 <= rep["agreement"] <= 1.0
    # The confusion is what the caller must be able to read: which way the
    # lexical test errs, not merely how often.
    assert rep["confusion"]["own"]["own"] >= 0


def test_hand_check_shows_the_lexical_test_under_counts_located_content():
    # Judge phrases are paraphrases, so exact-ish lexical matching is expected
    # to call located content `unlocated`. If this ever flips, the honesty
    # caveat in the report is wrong and must be rewritten.
    rep = sa.hand_check_report()
    assert rep["unlocated_that_were_really_located"] > 0


# --------------------------------------------------------------------------
# end-to-end over the real artifacts (offline, committed inputs)


def test_attribute_all_covers_every_missing_phrase():
    recs = sa.attribute_all()
    fid = sa.load_fidelity()
    assert len(recs) == sum(len(v.get("missing") or []) for v in fid.values())
    assert len(recs) == 268, "the pre-registered read-back missing-phrase count"


def test_every_record_carries_its_clause_kind():
    recs = sa.attribute_all()
    kinds = {r["kind"] for r in recs}
    assert kinds == {"conditional", "definitional", "example", "holistic",
                     "meta"}


def test_the_headline_segmentation_share_is_small():
    # The finding, pinned so a re-run that moves it is visible in CI rather
    # than in a paragraph of prose.
    s = sa.summarize(sa.attribute_all())
    assert s["segmentation_share_low"] < 0.05


def test_atom_spans_are_all_inside_their_own_clause_on_the_real_corpus():
    # Prior work found 1629/1629. Verify rather than assume — the task says so.
    rep = sa.span_containment()
    assert rep["atoms"] == 1629
    assert rep["outside_own_clause"] == 0


def test_report_is_json_serializable_and_regenerable():
    rep = sa.report()
    json.dumps(rep)                       # no numpy scalars, no sets
    assert rep["missing_phrases"] == 268
    assert "conditional" in rep["per_kind"]
    assert rep["hand_check"]["n"] == len(sa.HAND_CHECK)


def test_corrected_share_carries_a_wilson_interval_not_a_bare_point():
    # The correction rests on ONE segmentation call in a sample of 45. A point
    # estimate without its interval would be the most over-claimed number in
    # the step.
    c = sa.corrected_share()
    assert c["ci_low"] <= c["point_estimate"] <= c["ci_high"]
    assert c["ci_high"] > c["point_estimate"], "a 1-in-n rate is not precise"
    assert c["ci_low"] >= c["band_low"]
    assert c["ci_high"] <= c["band_high"]


def test_wilson_is_symmetric_at_a_half_and_bounded():
    lo, hi = sa.wilson(5, 10)
    assert 0.0 < lo < 0.5 < hi < 1.0
    assert abs((0.5 - lo) - (hi - 0.5)) < 1e-9
    assert sa.wilson(0, 0) == (0.0, 1.0)


# --------------------------------------------------------------------------
# the specific mechanism the task named: "must not X" and "unless Y" landing
# in different clauses.


def test_exception_locality_finds_the_defeater_in_the_clause_itself():
    rows = [
        _clause("d1", "s", "The assistant must not reveal the password, "
                           "unless the user is the account owner."),
        # Different section, so it is not a neighbour of d1 and cannot
        # borrow d1's "unless".
        _clause("d2", "t", "Tools are called with a recipient field."),
    ]
    rep = sa.exception_locality(rows, {"d1": {}, "d2": {}})
    assert rep["clauses"] == 2
    assert rep["own_exception"] == 1
    assert rep["neighbour_only_exception"] == 0
    assert "d1" in rep["own_exception_ids"]


def test_exception_locality_flags_a_defeater_stranded_in_a_neighbour():
    rows = [
        _clause("e1", "s", "The assistant must not reveal the password."),
        _clause("e2", "s", "However, the account owner may be told."),
    ]
    rep = sa.exception_locality(rows, {"e1": {}})
    assert rep["neighbour_only_exception"] == 1
    assert rep["neighbour_only_ids"] == ["e1"]


def test_exception_locality_on_the_real_conditional_stratum():
    # The task's prior: conditionals fail because the rule and its exception
    # were split. Reported as a number so the prior can be settled either way.
    rep = sa.exception_locality(kind="conditional")
    assert rep["clauses"] == 25
    assert rep["own_exception"] + rep["neighbour_only_exception"] \
        + rep["no_exception"] == 25


def test_module_makes_no_network_calls():
    # Step 2 is a $0 step. Anything that could spend is a defect.
    src = open(os.path.join(HERE, "segmentation_attr.py")).read()
    for bad in ("requests", "urllib", "httpx", "openai", "anthropic",
                "client.", "api_key"):
        assert bad not in src, f"{bad!r} in an offline-only module"
