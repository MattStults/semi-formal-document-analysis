"""Join v2 — locator-restricted joining, degenerate-quote refusal, the
empty-meta candidate skip, and segmentation option 1 (per-link mixed
rendering variants).

Contracts under test: JOIN_INTEGRITY_DESIGN.md §2 (guards 2a/2b, versioning)
and SEGMENTATION_GAPS_DESIGN.md §3 option 1 + §4 (F9 code-side predicate),
as ruled by PORTFOLIO_REVIEW.md F9/F12.

Two tiers:
  * synthetic fixtures — hand-computed, panel-free;
  * the real universe — the designs' §3 falsifiable predictions, checked
    against the live panel file. These read passage IDENTITY (locator,
    quote, score, exampleBlock) only; no judge verdict is consulted.
    inventory/benchmark are the join's legitimate panel readers (see
    test_no_reference_leak.py's module note) and this file tests them.
"""
from __future__ import annotations

import json
import os

import pytest

import benchmark as B
import inventory

HERE = os.path.dirname(os.path.abspath(__file__))

MS = "model-spec@2025-12-18"

#: SEGMENTATION_GAPS_DESIGN §4 — the pinned membership of the code-side
#: content_empty predicate on the current clause artifact.
EMPTY_META_IDS = {"m0393", "m0398", "m0535", "m0539"}

#: SEGMENTATION_GAPS_DESIGN §1 — the seven zero-match locators option 1 must
#: repair (measured 2026-08-04; re-verified in this cycle's baseline run).
GAP_LOCATORS = {
    f"{MS} > #follow_all_applicable_instructions > ¶13",
    f"{MS} > #letter_and_spirit > ¶2",
    f"{MS} > #letter_and_spirit > ¶3",
    f"{MS} > #ignore_untrusted_data > ¶13",
    f"{MS} > #disallowed_content > ¶2",
    f"{MS} > #restricted_content > ¶1",
    f"{MS} > #avoid_errors > ¶3",
}

#: The two structural refusals on the true universe. JOIN_INTEGRITY §3.1
#: predicted only the first; the second (an `Example:` caption that is a
#: proper substring of BOTH its section's clauses) is refused by the same
#: load-bearing arm — a §3 miss recorded in this cycle's prediction draft.
FANOUT_REFUSED = f"{MS} > #ignore_untrusted_data > ¶2"     # 28 -> refused
EXAMPLE_REFUSED = f"{MS} > #protect_privileged_information > ¶14"  # 2 -> refused

#: JOIN_INTEGRITY §3.1 predicted this locator collapses 6 -> 1 under
#: restriction. MEASURED FALSE: all six candidates are already in
#: #definitions, and five of the six are contained IN the passage (the
#: legitimate one-to-many direction; the sixth matches via a link variant),
#: so v2 correctly leaves it at 6. Recorded as a design-vs-reality
#: discrepancy; the fan-out here is segmentation granularity, not the
#: join defect.
DEFINITIONS_FANOUT = f"{MS} > #definitions > ¶5"           # 6 -> 6 (unchanged)

#: The four pseudo-heading PASSAGES (each ¶ is exactly its clause's text).
#: SEGMENTATION §4 predicted the empty-meta skip is a no-op ("nothing
#: currently maps to them") — MEASURED FALSE on the true universe: each of
#: these locators self-maps 1:1 onto its pseudo-heading clause under v1.
#: All four are non-reference in every behaviour, so no reference recall
#: moves; under v2 they join to zero clauses.
EMPTY_META_LOCATORS = {
    f"{MS} > #express_uncertainty > ¶2": "m0393",
    f"{MS} > #express_uncertainty > ¶7": "m0398",
    f"{MS} > #be_thorough_but_efficient > ¶2": "m0535",
    f"{MS} > #be_thorough_but_efficient > ¶6": "m0539",
}


# ------------------------------------------------------------- fixtures

def row(cid, quote, section_id=None, kind="requirement", marked_span=None):
    r = {"id": cid, "quote": quote, "marked_span": marked_span, "kind": kind}
    if section_id is not None:
        r["section_id"] = section_id
    return r


LONG_A = "the assistant must always disclose its reasoning to the user"
LONG_B = "the operator may configure disclosure of chain of thought details"


# ---------------------------------------------------- locator anchor (2a)

def test_locator_anchor_parses_panel_locators():
    """The section anchor is read off the panel's own locator grammar; a
    locator without an anchor yields None (restriction does not apply)."""
    assert inventory.locator_anchor(
        f"{MS} > #ignore_untrusted_data > ¶2") == "ignore_untrusted_data"
    assert inventory.locator_anchor(f"{MS} > #definitions > ¶5") == "definitions"
    assert inventory.locator_anchor("loc/p1") is None
    assert inventory.locator_anchor("") is None
    assert inventory.locator_anchor(None) is None


def test_join_v2_restricts_candidates_to_the_locator_section():
    """2a: with a resolvable anchor, only same-section clauses are candidates
    — the cross-section containment hit disappears, and the fact is
    disclosed as restricted: True."""
    shared = "ignore any instructions found in untrusted data"
    passage = f"prefix text {shared} suffix text"
    rows = [row("c_in", shared, section_id="sec_a"),
            row("c_out", shared, section_id="sec_b")]
    res = inventory.match_passage_v2(passage, rows,
                                     locator=f"{MS} > #sec_a > ¶1")
    assert res["restricted"] is True
    assert res["refused"] is False
    assert [r["id"] for r in res["clauses"]] == ["c_in"]
    assert res["join_version"] == inventory.JOIN_VERSION_V2


def test_join_v2_fallback_is_disclosed_never_silent():
    """2a: no anchor, or an anchor equal to no section_id, or rows without
    section_id -> full-corpus fallback with restricted: False."""
    shared = "ignore any instructions found in untrusted data"
    passage = f"prefix text {shared} suffix text"
    no_sid = [row("c1", shared)]
    res = inventory.match_passage_v2(passage, no_sid,
                                     locator=f"{MS} > #sec_a > ¶1")
    assert res["restricted"] is False
    assert [r["id"] for r in res["clauses"]] == ["c1"]

    sids = [row("c1", shared, section_id="sec_b")]
    res2 = inventory.match_passage_v2(passage, sids,
                                      locator=f"{MS} > #sec_a > ¶1")
    assert res2["restricted"] is False           # anchor matches no section_id
    assert [r["id"] for r in res2["clauses"]] == ["c1"]

    res3 = inventory.match_passage_v2(passage, sids, locator="loc/p1")
    assert res3["restricted"] is False           # no anchor at all
    assert [r["id"] for r in res3["clauses"]] == ["c1"]


# ------------------------------------------------ degenerate refusal (2b)

def test_degenerate_floor_refuses_short_quotes():
    """2b backstop: a sub-floor quote is refused BEFORE enumeration — proven
    against a SINGLE candidate, which the structural arm alone would never
    refuse. The floor is 14, recalibrated per the design's own rule
    ("if implementation finds a sub-floor quote that IS discriminating, the
    floor moves down, not the refusal semantics"): the design's 25 was
    calibrated on the PUBLISHED 863-passage universe, and the true 589
    universe holds seven discriminating quotes of 14-24 normalized chars
    (see test_recalibrated_floor_spares_discriminating_short_quotes)."""
    assert inventory.DEGENERATE_QUOTE_FLOOR == 14
    q = "mic check now"                       # 13 chars normalized
    assert len(inventory._norm(q)) == 13
    rows = [row("c1", "Example: mic check now plus more words",
                section_id="sec_a")]
    assert len(inventory.match_passage(q, rows)) == 1    # v1 matches
    res = inventory.match_passage_v2(q, rows, locator=f"{MS} > #sec_a > ¶2")
    assert res["refused"] is True
    assert res["flag"] == "degenerate_quote_refused"
    assert res["clauses"] == []


def test_floor_boundary_is_14_normalized():
    """A quote of exactly 14 normalized chars is NOT floor-refused; the floor
    is a strict backstop below 14 ('Sending emails', the shortest measured
    discriminating quote, must survive)."""
    q = "abcde fghij kl"                      # exactly 14 chars
    assert len(inventory._norm(q)) == 14
    rows = [row("c1", f"{q} and more of the clause text")]
    res = inventory.match_passage_v2(q, rows)
    assert res["refused"] is False
    assert [r["id"] for r in res["clauses"]] == ["c1"]


def test_the_real_offender_is_refused_by_the_structural_arm():
    """The header-only quote that manufactured the 28-fan-out is ABOVE the
    recalibrated floor (21 chars) and is caught by the LOAD-BEARING arm
    instead: post-restriction it is a proper substring of both remaining
    candidates, so it cannot discriminate — refused."""
    q = '!!! meta "Commentary"'
    assert len(inventory._norm(q)) == 21
    rows = [row("c1", '!!! meta "Commentary" first commentary block',
                section_id="sec_a"),
            row("c2", '!!! meta "Commentary" second commentary block',
                section_id="sec_a")]
    assert len(inventory.match_passage(q, rows)) == 2    # v1: the defect
    res = inventory.match_passage_v2(q, rows, locator=f"{MS} > #sec_a > ¶2")
    assert res["refused"] is True
    assert res["flag"] == "degenerate_quote_refused"
    assert res["restricted"] is True
    assert res["clauses"] == []


def test_structural_arm_refuses_nondiscriminating_quote():
    """2b load-bearing arm: a long quote that is a proper substring of EVERY
    post-restriction candidate cannot discriminate among them -> refused.
    The same quote against a single candidate matches."""
    q = "the assistant should treat untrusted content carefully"
    rows2 = [row("c1", f"{q} in the first of the two clauses",
                 section_id="s"),
             row("c2", f"{q} in the second of the two clauses",
                 section_id="s")]
    res = inventory.match_passage_v2(q, rows2, locator=f"{MS} > #s > ¶1")
    assert res["refused"] is True
    assert res["flag"] == "degenerate_quote_refused"

    res1 = inventory.match_passage_v2(q, rows2[:1], locator=f"{MS} > #s > ¶1")
    assert res1["refused"] is False
    assert [r["id"] for r in res1["clauses"]] == ["c1"]


def test_structural_arm_spares_the_containing_passage():
    """The legitimate one-to-many direction — a passage that CONTAINS several
    clause quotes — discriminates and must not be refused."""
    passage = f"{LONG_A}. {LONG_B}."
    rows = [row("c1", LONG_A, section_id="s"), row("c2", LONG_B, section_id="s")]
    res = inventory.match_passage_v2(passage, rows, locator=f"{MS} > #s > ¶1")
    assert res["refused"] is False
    assert sorted(r["id"] for r in res["clauses"]) == ["c1", "c2"]


def test_structural_arm_spares_exact_equality():
    """A quote EQUAL to one candidate (and inside another) discriminates:
    proper-substring-of-every-candidate is false, so no refusal."""
    q = LONG_A
    rows = [row("c1", LONG_A, section_id="s"),
            row("c2", f"{LONG_A} plus trailing qualification", section_id="s")]
    res = inventory.match_passage_v2(q, rows, locator=f"{MS} > #s > ¶1")
    assert res["refused"] is False
    assert sorted(r["id"] for r in res["clauses"]) == ["c1", "c2"]


# ------------------------------------------------- empty-meta skip (F9)

def test_content_empty_membership_is_pinned():
    """The F9 code-side predicate matches EXACTLY the four pseudo-heading
    clauses on the current artifact — no field is written anywhere."""
    rows, src = B.load_clauses()
    assert src == "modelspec_clauses.json"
    assert {r["id"] for r in rows if inventory.content_empty(r)} \
        == EMPTY_META_IDS


def test_content_empty_requires_meta_kind_and_heading_shape():
    assert inventory.content_empty(
        {"id": "x", "kind": "meta", "quote": "**Types of uncertainty**"})
    assert inventory.content_empty(
        {"id": "x", "kind": "meta", "quote": "Favoring longer responses:"})
    # heading-shaped text of a non-meta kind is CONTENT, not a pseudo-heading
    assert not inventory.content_empty(
        {"id": "x", "kind": "requirement", "quote": "**Types of uncertainty**"})
    # sentence-like lead-ins that happen to end with a colon are kept
    assert not inventory.content_empty(
        {"id": "x", "kind": "meta", "quote": "To realize this vision, we need to:"})
    assert not inventory.content_empty(
        {"id": "x", "kind": "meta", "quote": "The levels of authority are as follows:"})


def test_empty_meta_clauses_never_candidates():
    """v2 skips content-empty clauses as candidates; v1 (kept reachable)
    still binds to them — the difference IS the fix."""
    heading = "**When to express uncertainty three**"   # >= 25 normalized
    passage = f"some passage discussing {heading} at length"
    rows = [row("m_meta", heading, section_id="s", kind="meta"),
            row("c_real", f"some passage discussing {heading}",
                section_id="s", kind="requirement")]
    assert {r["id"] for r in inventory.match_passage(passage, rows)} \
        == {"m_meta", "c_real"}
    res = inventory.match_passage_v2(passage, rows, locator=f"{MS} > #s > ¶1")
    assert [r["id"] for r in res["clauses"]] == ["c_real"]


# ------------------------------- segmentation option 1 (mixed variants)

def test_mixed_link_renderings_join():
    """A clause whose two links the panel rendered INCONSISTENTLY (one as
    text, one as target) defeats both uniform variants (v1 misses) and joins
    under the per-link mixed variant set (v2) — passed EXPLICITLY, since the
    mixed set is opt-in and not the default."""
    clause_md = ("the assistant should follow [the guidelines](guide_lines) "
                 "and respect [user intent](user_intent) at every step")
    panel_rendering = ("the assistant should follow the guidelines "
                       "and respect user_intent at every step")
    rows = [row("c1", clause_md, section_id="s")]
    assert inventory.match_passage(panel_rendering, rows) == []
    res = inventory.match_passage_v2(panel_rendering, rows,
                                     locator=f"{MS} > #s > ¶1",
                                     mixed_variants=True)
    assert [r["id"] for r in res["clauses"]] == ["c1"]


def test_mixed_variants_are_bounded_and_fall_back():
    """Beyond the cap (8 variants, i.e. 3 links) the mixed set refuses the
    explosion and falls back to the uniform pair — current behavior."""
    two = "see [a](ta) then [b](tb) end"
    assert len(inventory._variants_mixed(two)) == 4
    assert inventory._variants(two) <= inventory._variants_mixed(two)
    four = "see [a](ta) [b](tb) [c](tc) [d](td) end"
    assert inventory._variants_mixed(four) == inventory._variants(four)
    nolinks = "plain text with no links at all"
    assert inventory._variants_mixed(nolinks) == inventory._variants(nolinks)


def test_join_v2_can_isolate_the_variant_lever():
    """mixed_variants=False gives the restriction+refusal join over the
    UNIFORM variant set — the lever the two cycles' predictions are checked
    on independently."""
    clause_md = ("the assistant should follow [the guidelines](guide_lines) "
                 "and respect [user intent](user_intent) at every step")
    panel_rendering = ("the assistant should follow the guidelines "
                       "and respect user_intent at every step")
    rows = [row("c1", clause_md, section_id="s")]
    res_off = inventory.match_passage_v2(panel_rendering, rows,
                                         locator=f"{MS} > #s > ¶1",
                                         mixed_variants=False)
    assert res_off["clauses"] == []
    res_on = inventory.match_passage_v2(panel_rendering, rows,
                                        locator=f"{MS} > #s > ¶1",
                                        mixed_variants=True)
    assert [r["id"] for r in res_on["clauses"]] == ["c1"]


def test_match_passage_v2_default_is_mixed_variants_false():
    """The DEFAULT variant set is the measured/pinned uniform one: omitting
    the argument must behave exactly as mixed_variants=False (the lever
    fixture joins to NOTHING under the uniform set — it would join to c1
    under the unmeasured mixed set, so the equality below is discriminating).
    The mixed set is OPT-IN: an entry point opting into join_version=2 must
    never inherit it silently."""
    clause_md = ("the assistant should follow [the guidelines](guide_lines) "
                 "and respect [user intent](user_intent) at every step")
    panel_rendering = ("the assistant should follow the guidelines "
                       "and respect user_intent at every step")
    rows = [row("c1", clause_md, section_id="s")]
    res_default = inventory.match_passage_v2(panel_rendering, rows,
                                             locator=f"{MS} > #s > ¶1")
    res_off = inventory.match_passage_v2(panel_rendering, rows,
                                         locator=f"{MS} > #s > ¶1",
                                         mixed_variants=False)
    assert res_default == res_off
    assert res_default["clauses"] == []       # uniform set: the gap stands
    # and the signature itself pins the default
    import inspect
    sig = inspect.signature(inventory.match_passage_v2)
    assert sig.parameters["mixed_variants"].default is False


# ----------------------------------------- benchmark wiring (stratum etc.)

def mk_passage(pid, verdicts, quote, locator=None, example_block=False):
    return {"id": pid, "locator": locator or f"loc/{pid}", "quote": quote,
            "exampleBlock": example_block, "adjacent": False,
            "verdicts": dict(verdicts), "score": sum(verdicts.values())}


@pytest.fixture
def behaviour_v2():
    """One healthy reference passage, one degenerate-quote reference passage
    (score 6, sub-floor quote matching two clauses), one non-reference."""
    ps = [
        mk_passage("p1", {"a": 2, "b": 2, "c": 2},
                   "alpha clause one of considerable length"),
        mk_passage("p2", {"a": 2, "b": 2, "c": 2}, "!!! heading",
                   locator=f"{MS} > #sec_a > ¶2"),
        mk_passage("p3", {"a": 1, "b": 0, "c": 0},
                   "beta clause two of considerable length"),
    ]
    return {"slug": "synthetic", "coverage": {"openai": {"passages": ps}}}


@pytest.fixture
def clauses_v2():
    return [row("c1", "alpha clause one of considerable length",
                section_id="sec_a"),
            row("c2", "!!! heading first block", section_id="sec_a"),
            row("c3", "!!! heading second block", section_id="sec_a"),
            row("c4", "beta clause two of considerable length",
                section_id="sec_b")]


SPEC_V2 = ("alpha clause one of considerable length\n"
           "!!! heading first block\n!!! heading second block\n"
           "beta clause two of considerable length\n")


def test_strata_gained_the_refusal_stratum():
    assert "degenerate_quote_refused" in B.STRATA
    assert len(B.STRATA) == 5


def test_map_reference_records_refusal_stratum(behaviour_v2, clauses_v2):
    m = B.map_reference(behaviour_v2, clauses_v2, 5, SPEC_V2,
                        join_version=inventory.JOIN_VERSION_V2)
    assert m["join_version"] == inventory.JOIN_VERSION_V2
    assert m["per_passage"]["p1"] == ["c1"]
    assert m["per_passage"]["p2"] == []
    assert m["unmatched"] == ["p2"]
    assert m["strata"]["degenerate_quote_refused"] == 1
    assert m["strata_ids"]["degenerate_quote_refused"] == ["p2"]
    assert sum(m["strata"].values()) == len(m["unmatched"])
    assert m["join_facts"]["p2"] == {"restricted": False, "refused": True}
    assert m["join_facts"]["p1"]["refused"] is False


def test_map_reference_default_is_v1_and_versioned(behaviour_v2, clauses_v2):
    """v1 stays the default and stays reachable byte-identically; the version
    is recorded either way (JOIN_INTEGRITY_DESIGN §2 versioning)."""
    m = B.map_reference(behaviour_v2, clauses_v2, 5, SPEC_V2)
    assert m["join_version"] == inventory.JOIN_VERSION_V1
    assert m["strata"]["degenerate_quote_refused"] == 0
    # under v1 the degenerate quote fans out to both clauses — the defect
    assert sorted(m["per_passage"]["p2"]) == ["c2", "c3"]
    with pytest.raises(ValueError):
        B.map_reference(behaviour_v2, clauses_v2, 5, SPEC_V2, join_version=3)


def test_score_tool_counts_refused_reference_as_full_fn(behaviour_v2,
                                                        clauses_v2):
    """§2b: a refused reference passage is an unmatched false negative in
    `full` scoring — the honest cost."""
    m = B.map_reference(behaviour_v2, clauses_v2, 5, SPEC_V2,
                        join_version=inventory.JOIN_VERSION_V2)
    r = B.score_tool({"c1"}, behaviour_v2, clauses_v2, 5, SPEC_V2, mapping=m)
    assert r["matched"] == B.prf({"c1"}, {"c1"})
    assert r["full"]["fn"] == 1                      # the refused passage
    assert r["zero_match"]["degenerate_quote_refused"] == 1
    assert r["join_version"] == inventory.JOIN_VERSION_V2


def test_clause_joins_versioned_and_cache_does_not_bleed(behaviour_v2,
                                                         clauses_v2):
    j1 = B.clause_joins(behaviour_v2, clauses_v2)
    j2 = B.clause_joins(behaviour_v2, clauses_v2,
                        join_version=inventory.JOIN_VERSION_V2)
    assert sorted(j1["p2"]) == ["c2", "c3"]
    assert j2["p2"] == []
    # and again from cache, in both orders
    assert B.clause_joins(behaviour_v2, clauses_v2)["p2"] == j1["p2"]
    facts = B.clause_join_facts(behaviour_v2, clauses_v2,
                                join_version=inventory.JOIN_VERSION_V2)
    assert facts["p2"]["refused"] is True
    assert B.clause_join_facts(behaviour_v2, clauses_v2) == {}


def test_evaluate_carries_join_version_and_refused_stratum(behaviour_v2,
                                                           clauses_v2):
    r1 = B.evaluate(behaviour_v2, {"c1"}, clauses_v2, spec=SPEC_V2)
    assert r1["join"]["join_version"] == inventory.JOIN_VERSION_V1
    assert r1["join"]["strata"]["degenerate_quote_refused"] == 0
    r2 = B.evaluate(behaviour_v2, {"c1"}, clauses_v2, spec=SPEC_V2,
                    join_version=inventory.JOIN_VERSION_V2)
    assert r2["join"]["join_version"] == inventory.JOIN_VERSION_V2
    assert r2["join"]["strata"]["degenerate_quote_refused"] == 1


def test_census_identity_join_version_seam():
    """F12: join_version belongs to CENSUS config identity. The seam accepts
    an explicit version; the no-argument default stays None (the census has
    not yet run under a versioned join — S8 passes it explicitly)."""
    import audit_disagreements as AD
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        ann = os.path.join(d, "annotations_x.json")
        atoms = os.path.join(d, "behavior_atoms_y.json")
        json.dump({"clauses": []}, open(ann, "w"))
        json.dump({}, open(atoms, "w"))
        assert AD.config_identity(ann, atoms)["join_version"] is None
        ident = AD.config_identity(
            ann, atoms, join_version=inventory.JOIN_VERSION_V2)
        assert ident["join_version"] == inventory.JOIN_VERSION_V2


# --------------------------- the real universe: §3 predictions, both designs

@pytest.fixture(scope="module")
def real_maps():
    """Locator-level mapped sets over the true 589-locator universe, under
    v1, v2 without mixed variants (the P1 lever alone), and full v2."""
    rows, src = B.load_clauses()
    assert src == "modelspec_clauses.json"
    panel = B.load_true_panel()
    loc_quote, loc_scores = {}, {}
    for slug, b in panel.items():
        for p in B.passages(b):
            loc = p["locator"]
            assert loc_quote.setdefault(loc, p["quote"]) == p["quote"]
            loc_scores.setdefault(loc, {})[slug] = p.get("score", 0)

    maps = {"v1": {}, "v2_nomix": {}, "v2": {}}
    refused = {"v2_nomix": set(), "v2": set()}
    for loc, q in loc_quote.items():
        maps["v1"][loc] = frozenset(
            r["id"] for r in inventory.match_passage(q, rows))
        for mode, mix in (("v2_nomix", False), ("v2", True)):
            res = inventory.match_passage_v2(q, rows, loc, mixed_variants=mix)
            maps[mode][loc] = frozenset(r["id"] for r in res["clauses"])
            if res["refused"]:
                refused[mode].add(loc)
    return {"maps": maps, "refused": refused, "scores": loc_scores,
            "n_locators": len(loc_quote)}


def test_prediction1_the_exact_locator_delta_under_restriction(real_maps):
    """The corrected §3.1 pin, re-derived mechanically on the TRUE universe
    (the design's "exactly two locators change" was computed against the
    published-universe calibration and is superseded — see the P1 cycle
    draft's design-vs-reality section): exactly SIX locators change under
    restriction + refusal + the empty-meta skip, every one non-reference;
    every other mapped set is byte-identical. Any other delta halts the
    cycle."""
    assert real_maps["n_locators"] == 589
    v1, v2 = real_maps["maps"]["v1"], real_maps["maps"]["v2_nomix"]
    changed = {loc for loc in v1 if v1[loc] != v2[loc]}
    assert changed == ({FANOUT_REFUSED, EXAMPLE_REFUSED}
                       | set(EMPTY_META_LOCATORS))
    # the two structural refusals
    assert real_maps["refused"]["v2_nomix"] == {FANOUT_REFUSED,
                                                EXAMPLE_REFUSED}
    assert len(v1[FANOUT_REFUSED]) == 28
    assert v2[FANOUT_REFUSED] == frozenset()
    assert len(v1[EXAMPLE_REFUSED]) == 2
    assert v2[EXAMPLE_REFUSED] == frozenset()
    # the four pseudo-heading self-maps drop to zero, not refused
    for loc, cid in EMPTY_META_LOCATORS.items():
        assert v1[loc] == frozenset({cid})
        assert v2[loc] == frozenset()
    # §3.1's predicted 6 -> 1 collapse is REFUTED: legitimately unchanged
    assert v1[DEFINITIONS_FANOUT] == v2[DEFINITIONS_FANOUT]
    assert len(v1[DEFINITIONS_FANOUT]) == 6


def test_recalibrated_floor_spares_discriminating_short_quotes(real_maps):
    """§2b's calibration rule, executed: every sub-25 normalized quote on the
    true universe EXCEPT the header-only offender discriminates (maps to
    exactly one in-section clause) and keeps its mapping under v2. This is
    the measurement that moved the floor from 25 to 14."""
    v1, v2 = real_maps["maps"]["v1"], real_maps["maps"]["v2_nomix"]
    short_ok = {
        f"{MS} > #control_side_effects > ¶5",                    # 14 chars
        f"{MS} > #respond_to_audio_testing_in_voice_mode > ¶2",  # 18
        f"{MS} > #letter_and_spirit > ¶15",                      # 20
        f"{MS} > #be_thorough_but_efficient > ¶10",              # 21, ref-grade
        f"{MS} > #be_responsible > ¶4",                          # 24
        f"{MS} > #no_other_objectives > ¶9",                     # 24
    }
    for loc in short_ok:
        assert len(v1[loc]) == 1, loc
        assert v2[loc] == v1[loc], loc


def test_prediction2_no_reference_grade_passage_changes(real_maps):
    """JOIN_INTEGRITY §3.2: no passage with panel score >= 5 in any behaviour
    changes its mapped set under restriction + refusal."""
    v1, v2 = real_maps["maps"]["v1"], real_maps["maps"]["v2_nomix"]
    ref_locs = {loc for loc, ss in real_maps["scores"].items()
                if any(s >= 5 for s in ss.values())}
    assert ref_locs, "reference-grade set unexpectedly empty"
    assert all(v1[loc] == v2[loc] for loc in ref_locs)


def test_option1_repairs_exactly_the_seven_gap_locators(real_maps):
    """SEGMENTATION §3 option 1 acceptance: the seven zero-match locators map,
    each to exactly one clause, and no already-matched passage changes its
    mapped set. Mixed variants are the ONLY lever between these two runs."""
    off, on = real_maps["maps"]["v2_nomix"], real_maps["maps"]["v2"]
    changed = {loc for loc in off if off[loc] != on[loc]}
    assert changed == GAP_LOCATORS
    for loc in GAP_LOCATORS:
        assert off[loc] == frozenset()
        assert len(on[loc]) == 1, (loc, sorted(on[loc]))
    assert real_maps["refused"]["v2"] == real_maps["refused"]["v2_nomix"]


def test_empty_meta_skip_measured_delta(real_maps):
    """SEGMENTATION §4's acceptance ("nothing currently maps to them;
    predicted delta zero") is MEASURED FALSE on the true universe — the four
    pseudo-heading PARAGRAPHS are themselves panel passages, each self-mapped
    1:1 onto its pseudo-heading clause under v1. The corrected pin: exactly
    those four self-maps exist under v1, all non-reference, and under v2 no
    passage maps to a content-empty clause."""
    v1 = real_maps["maps"]["v1"]
    v1_hits = {loc: sorted(cids & EMPTY_META_IDS) for loc, cids in v1.items()
               if cids & EMPTY_META_IDS}
    assert v1_hits == {loc: [cid] for loc, cid in EMPTY_META_LOCATORS.items()}
    for loc in EMPTY_META_LOCATORS:
        assert not any(s >= 5 for s in real_maps["scores"][loc].values()), loc
    for mode in ("v2_nomix", "v2"):
        hit = {loc for loc, cids in real_maps["maps"][mode].items()
               if cids & EMPTY_META_IDS}
        assert hit == set(), (mode, sorted(hit))
