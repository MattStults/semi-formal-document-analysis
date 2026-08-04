"""Guards on the hand-authored reference translations.

WHAT THESE TESTS ARE FOR
------------------------
`golden_translations.json` is a STANDARD: 12 clauses of the Model Spec with the
atom set a careful reader should produce for each. Everything downstream that
claims "the extractor got this clause right" is measured against it, so three
things have to be mechanically true and none of them are checkable by reading:

  1. THE ARTIFACT IS FROZEN. A reference that can be edited to agree with
     whatever the extractor happened to emit is not a reference. The file
     carries its own sha256 and the loader refuses a file whose content and
     hash disagree.
  2. THE HELD-OUT HALF STAYS HELD OUT. Six of the twelve may be looked at while
     iterating on a prompt; six may not, ever. A dev accessor that leaks even
     one held-out entry destroys the only clean measurement in the artifact,
     and it does so invisibly.
  3. THE COMPARISON MEANS SOMETHING. `must_x` and `mustnot_x` are opposites and
     `__model_user` and `__user_model` are different relations. A scorer that
     calls either pair a match reports a number that is not about the document.

Each of those has a MUTANT test below — a test that fails if the guard is
removed — written and verified RED before the guard existed.
"""
import copy
import json
import os

import pytest

import golden
import grammar


HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACT = os.path.join(HERE, "golden_translations.json")


@pytest.fixture(scope="module")
def g():
    return golden.load()


# ==========================================================================
# 1. THE ARTIFACT: shape, budget, and conformance to the grammar
# ==========================================================================

def test_artifact_has_twelve_entries(g):
    assert len(g.entries) == 12
    assert len({e["clause_id"] for e in g.entries}) == 12


def test_every_entry_carries_the_fields_a_reference_needs(g):
    for e in g.entries:
        for k in ("clause_id", "locator", "kind", "quote", "split",
                  "structure", "atoms", "recoverable", "not_recoverable"):
            assert k in e, f"{e.get('clause_id')} missing {k}"
        assert e["recoverable"].strip(), e["clause_id"]
        assert e["not_recoverable"].strip(), e["clause_id"]


def test_every_atom_name_parses_under_the_grammar(g):
    for e in g.entries:
        for a in e["atoms"]:
            p = grammar.parse_name(a["name"])
            assert p["error"] is None, (e["clause_id"], a["name"], p["error"])


def test_every_atom_uses_the_closed_vocabularies(g):
    for e in g.entries:
        for a in e["atoms"]:
            assert a["kind"] in ("situation", "act", "entity", "value")
            if "role" in a:
                assert grammar.valid_role(a["role"]), (e["clause_id"], a)


def test_atom_names_match_the_identifier_pattern(g):
    import re
    pat = re.compile(r"^[a-z][a-z0-9_]*$")
    for e in g.entries:
        for a in e["atoms"]:
            assert pat.match(a["name"]), a["name"]


def test_the_encoding_budget_is_respected(g):
    """~2.8 atoms and ~200 gloss characters per clause. The budget is what
    makes the standard reachable; a reference that is correct only because it
    is enormous cannot be used to judge anything."""
    total = sum(len(e["atoms"]) for e in g.entries)
    assert total / len(g.entries) <= 2.8, total
    for e in g.entries:
        chars = sum(len(a["gloss"]) for a in e["atoms"])
        assert chars <= 240, (e["clause_id"], chars)


def test_every_span_id_resolves_against_the_real_clause(g):
    """Provenance is verified, not asserted: each cited span id must exist in
    the span table `extract_section.candidate_spans` derives from that clause's
    own quote, exactly as the pipeline derives it for the extractor."""
    import extract_section as ex
    clauses = {c["id"]: c for c in
               json.load(open(os.path.join(HERE, "modelspec_clauses.json"),
                              encoding="utf-8"))["clauses"]}
    for e in g.entries:
        row = dict(clauses[e["clause_id"]], marked_span=None)
        ids = {s["id"] for s in ex.candidate_spans(row)}
        for a in e["atoms"]:
            assert a["span_id"] in ids, (e["clause_id"], a["name"],
                                         a["span_id"], sorted(ids))


def test_quotes_are_verbatim_from_the_corpus(g):
    clauses = {c["id"]: c for c in
               json.load(open(os.path.join(HERE, "modelspec_clauses.json"),
                              encoding="utf-8"))["clauses"]}
    for e in g.entries:
        assert e["quote"] == clauses[e["clause_id"]]["quote"], e["clause_id"]


def test_the_selection_spans_the_structures_the_grammar_exists_for(g):
    """The point of the twelve is COVERAGE. If a later edit collapsed them onto
    one structure the artifact would still load and still be frozen and would
    no longer test anything."""
    tags = {t for e in g.entries for t in e["structure"]}
    for needed in ("obligation", "prohibition", "permission", "defeater",
                   "explicit_parties", "control"):
        assert needed in tags, needed
    controls = [e for e in g.entries if "control" in e["structure"]]
    assert len(controls) == 2
    for e in controls:
        assert not grammar.carries_notation(e["atoms"]), (
            f"{e['clause_id']} is a CONTROL: it states no force, no parties "
            "and no trigger, so its reference translation must carry none of "
            "the three. Marking structure the clause does not state is the "
            "error the controls exist to catch.")


def test_polarity_and_principals_and_roles_are_all_exercised(g):
    used = grammar.records([a for e in g.entries for a in e["atoms"]])
    assert used == {"polarity": True, "principals": True, "condition": True}


def test_both_condition_and_exception_roles_appear(g):
    roles = {grammar.role_of(a) for e in g.entries for a in e["atoms"]}
    assert {"condition", "exception", "consequent"} <= roles


# ==========================================================================
# 2. THE FREEZE.  MUTANT: a loader that does not verify the hash.
# ==========================================================================

def test_the_recorded_hash_matches_the_content(g):
    assert g.sha256 == golden.compute_sha256(g.payload)


def test_a_tampered_artifact_is_REFUSED(tmp_path):
    """THE MUTANT. Edit one gloss, leave the recorded hash alone, and the
    loader must refuse the file. A loader that skips the check accepts this
    silently, which is exactly how a reference gets quietly retrofitted to
    whatever the extractor produced."""
    data = json.load(open(ARTIFACT, encoding="utf-8"))
    data["entries"][0]["atoms"][0]["gloss"] = "TAMPERED"
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(golden.GoldenHashError):
        golden.load(str(p))


def test_a_tampered_ATOM_NAME_is_refused(tmp_path):
    data = json.load(open(ARTIFACT, encoding="utf-8"))
    data["entries"][0]["atoms"][0]["name"] = "something_else"
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(golden.GoldenHashError):
        golden.load(str(p))


def test_moving_a_clause_between_dev_and_heldout_is_refused(tmp_path):
    """The split is inside the hash. Reclassifying a held-out clause as dev
    after seeing how the extractor did on it is the single most valuable
    tamper, so it must be the loudest failure."""
    data = json.load(open(ARTIFACT, encoding="utf-8"))
    moved = data["split"]["held_out"][0]
    data["split"]["held_out"].remove(moved)
    data["split"]["dev"].append(moved)
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(golden.GoldenHashError):
        golden.load(str(p))


def test_hash_is_insensitive_to_key_order_and_whitespace(tmp_path):
    """Re-serializing the same content must still verify — otherwise the freeze
    would break on a formatter and get switched off."""
    data = json.load(open(ARTIFACT, encoding="utf-8"))
    p = tmp_path / "t.json"
    p.write_text(json.dumps(data, indent=7, sort_keys=True), encoding="utf-8")
    assert golden.load(str(p)).sha256 == golden.load().sha256


# ==========================================================================
# 3. THE SPLIT.  MUTANT: held-out readable through the dev accessor.
# ==========================================================================

def test_split_is_six_and_six(g):
    assert len(g.dev_ids) == 6
    assert len(g.held_out_ids) == 6


def test_dev_and_held_out_are_disjoint_and_exhaustive(g):
    assert not (set(g.dev_ids) & set(g.held_out_ids))
    assert set(g.dev_ids) | set(g.held_out_ids) == {e["clause_id"]
                                                    for e in g.entries}


def test_the_dev_accessor_NEVER_returns_a_held_out_entry(g):
    """THE MUTANT. `dev()` returning all twelve — or eleven, or seven — reads
    as a working accessor and quietly burns the held-out set the first time a
    prompt is tuned against its output."""
    got = [e["clause_id"] for e in g.dev()]
    assert got == sorted(g.dev_ids)
    for cid in g.held_out_ids:
        assert cid not in got, (
            f"{cid} is HELD OUT and was returned by the dev accessor")


def test_dev_entries_are_deep_copies(g):
    """Handing out the live dicts lets a caller edit the reference in memory
    and score against its own edit."""
    e = g.dev()[0]
    e["atoms"][0]["name"] = "mutated"
    assert g.dev()[0]["atoms"][0]["name"] != "mutated"


def test_held_out_requires_an_explicit_acknowledgement(g):
    with pytest.raises(golden.HeldOutAccessError):
        g.held_out()
    with pytest.raises(golden.HeldOutAccessError):
        g.held_out(final_evaluation=False)
    got = [e["clause_id"] for e in g.held_out(final_evaluation=True)]
    assert got == sorted(g.held_out_ids)


def test_lookup_by_id_also_gates_the_held_out_half(g):
    cid = g.held_out_ids[0]
    with pytest.raises(golden.HeldOutAccessError):
        g.entry(cid)
    assert g.entry(cid, final_evaluation=True)["clause_id"] == cid
    dev = g.dev_ids[0]
    assert g.entry(dev)["clause_id"] == dev


def test_the_split_is_reproducible_from_the_recorded_seed(g):
    """The split must be a seeded shuffle, not a choice. A hand-picked split
    can be picked to flatter."""
    dev, held = golden.seeded_split(sorted(e["clause_id"] for e in g.entries),
                                    g.payload["split"]["seed"])
    assert sorted(dev) == sorted(g.dev_ids)
    assert sorted(held) == sorted(g.held_out_ids)


def test_scoring_a_whole_set_refuses_held_out_ids_without_the_flag(g):
    cand = {cid: [] for cid in g.held_out_ids}
    with pytest.raises(golden.HeldOutAccessError):
        golden.score_all(cand, g)
    golden.score_all(cand, g, final_evaluation=True)


# ==========================================================================
# 4. THE COMPARISON.  MUTANTS: wrong polarity scored correct; principal order
#    ignored.
# ==========================================================================

A = dict(kind="act", gloss="", span_id="s1")


def atom(name, role=None, **kw):
    a = dict(A, name=name, **kw)
    if role:
        a["role"] = role
    return a


def test_identical_annotations_score_one():
    ref = [atom("mustnot_steer_user__model_user", "consequent"),
           atom("model_own_agenda", "topic", kind="situation")]
    r = golden.compare(copy.deepcopy(ref), ref, level="exact")
    assert r["precision"] == r["recall"] == r["f1"] == 1.0


def test_OPPOSITE_POLARITY_IS_NEVER_A_MATCH():
    """THE MUTANT. `must_disclose` against `mustnot_disclose` is the exact
    failure the notation was added to fix; a scorer that matches them on their
    shared stem reports that the extractor understood a clause whose meaning it
    inverted."""
    ref = [atom("must_disclose_reasoning")]
    cand = [atom("mustnot_disclose_reasoning")]
    for level in ("exact", "name", "deontic"):
        r = golden.compare(cand, ref, level=level)
        assert r["matched"] == 0, level
        assert r["f1"] == 0.0, level


def test_an_unmarked_name_does_not_match_a_forced_one():
    """"No force stated" is a real answer, not a wildcard. Letting a bare stem
    match `must_` makes the cheapest possible annotation score full marks."""
    r = golden.compare([atom("disclose_reasoning")],
                       [atom("must_disclose_reasoning")], level="deontic")
    assert r["matched"] == 0


def test_should_does_not_match_must():
    r = golden.compare([atom("should_disclose_reasoning")],
                       [atom("must_disclose_reasoning")], level="deontic")
    assert r["matched"] == 0


def test_PRINCIPAL_ORDER_IS_MEANING():
    """THE MUTANT. `cause_harm__model_third_party` is the model harming
    someone; `__third_party_model` is someone harming the model. A comparison
    that sorts or sets the chain scores the two as the same claim."""
    ref = [atom("cause_harm__model_third_party")]
    cand = [atom("cause_harm__third_party_model")]
    for level in ("exact", "name", "principal"):
        r = golden.compare(cand, ref, level=level)
        assert r["matched"] == 0, level


def test_a_shorter_chain_does_not_match_a_longer_one():
    r = golden.compare([atom("remind__model_user")],
                       [atom("remind__model_user_developer")],
                       level="principal")
    assert r["matched"] == 0


def test_stem_level_forgives_the_decorations_but_reports_them():
    """The graded levels are the whole design: an extractor that finds the
    right concept and the wrong force should score high on `stem` and zero on
    `deontic`, so the two failure modes stay visible separately."""
    ref = [atom("must_disclose_reasoning__model_user", "consequent")]
    cand = [atom("mustnot_disclose_reasoning__user_model", "condition")]
    r = golden.compare(cand, ref, level="stem")
    assert r["matched"] == 1
    assert r["agreement"]["polarity"] == 0.0
    assert r["agreement"]["principals"] == 0.0
    assert r["agreement"]["role"] == 0.0


def test_role_disagreement_is_reported_at_stem_level():
    ref = [atom("user_asked", "condition", kind="situation")]
    cand = [atom("user_asked", "exception", kind="situation")]
    r = golden.compare(cand, ref, level="stem")
    assert r["matched"] == 1
    assert r["agreement"]["role"] == 0.0
    assert golden.compare(cand, ref, level="role")["matched"] == 0
    assert golden.compare(cand, ref, level="exact")["matched"] == 0


def test_matching_is_one_to_one():
    """Two candidate atoms with the same stem must not both claim the one
    reference atom — otherwise emitting a name twice inflates recall."""
    ref = [atom("user_asked", kind="situation")]
    cand = [atom("user_asked", kind="situation"),
            atom("user_asked", kind="situation")]
    r = golden.compare(cand, ref, level="stem")
    assert r["matched"] == 1
    assert r["recall"] == 1.0
    assert r["precision"] == 0.5


def test_matching_is_maximal_not_first_come():
    """Greedy first-come pairing can consume the only atom a later candidate
    could have matched. The assignment must be a maximum matching."""
    ref = [atom("must_a"), atom("a")]
    cand = [atom("a"), atom("must_a")]
    r = golden.compare(cand, ref, level="name")
    assert r["matched"] == 2


def test_empty_candidate_scores_zero_without_dividing_by_zero():
    r = golden.compare([], [atom("must_a")], level="stem")
    assert r == pytest.approx({"matched": 0, "precision": 0.0, "recall": 0.0,
                               "f1": 0.0}, rel=0, abs=0) or r["f1"] == 0.0
    assert r["precision"] == 0.0


def test_empty_reference_and_empty_candidate_is_a_perfect_score():
    """A clause whose correct answer is "no atoms" is answered correctly by an
    empty list, and the scorer must not report 0.0 for it."""
    r = golden.compare([], [], level="exact")
    assert r["f1"] == 1.0


def test_unknown_level_is_refused():
    with pytest.raises(ValueError):
        golden.compare([], [], level="vibes")


def test_unparseable_candidate_names_do_not_crash_or_match():
    r = golden.compare([atom("must_")], [atom("must_a")], level="stem")
    assert r["matched"] == 0


def test_score_all_reports_per_clause_and_aggregate(g):
    cand = {e["clause_id"]: copy.deepcopy(e["atoms"]) for e in g.dev()}
    out = golden.score_all(cand, g)
    assert set(out["per_clause"]) == set(g.dev_ids)
    assert out["micro"]["f1"] == 1.0
    assert out["n_clauses"] == 6


def test_score_all_counts_a_missing_clause_as_a_miss(g):
    cand = {e["clause_id"]: copy.deepcopy(e["atoms"]) for e in g.dev()}
    dropped = sorted(cand)[0]
    del cand[dropped]
    out = golden.score_all(cand, g)
    assert out["per_clause"][dropped]["recall"] == 0.0
    assert out["micro"]["f1"] < 1.0


def test_score_all_ignores_clause_ids_that_are_not_in_the_reference(g):
    cand = {e["clause_id"]: copy.deepcopy(e["atoms"]) for e in g.dev()}
    cand["m9999"] = [atom("noise")]
    out = golden.score_all(cand, g)
    assert "m9999" not in out["per_clause"]
    assert out["micro"]["f1"] == 1.0


def test_the_reference_scores_itself_perfectly_at_every_level(g):
    """A sanity check on the artifact and the scorer at once: if the reference
    does not match itself, one of the two is wrong."""
    for e in g.entries_unsafe():
        for level in golden.LEVELS:
            r = golden.compare(copy.deepcopy(e["atoms"]), e["atoms"],
                               level=level)
            assert r["f1"] == 1.0, (e["clause_id"], level)


# ==========================================================================
# 5. THE SPAN-ANCHORED LEVELS.  Two authors agreed on stem NAMES at 0.29,
#    on SPANS at 0.79, and on decoration over span-matched pairs at 10/11 —
#    so "span" scores WHERE the content is, ignoring what it was called, and
#    "span_deco" adds WHAT structure it carries. Naming stays its own axis.
# ==========================================================================

def satom(name, quote, kind="act", role=None):
    a = dict(name=name, quote=quote, kind=kind, gloss="", span_id="s1")
    if role:
        a["role"] = role
    return a


Q = "The assistant must strive to follow all applicable instructions."


def test_span_matches_on_containment_candidate_inside_reference():
    r = golden.compare([satom("anything_at_all", "must strive to follow")],
                       [satom("something_else", Q)], level="span")
    assert r["matched"] == 1, "candidate quote contained in reference quote"


def test_span_matches_on_containment_reference_inside_candidate():
    r = golden.compare([satom("a", Q)],
                       [satom("b", "follow all applicable instructions")],
                       level="span")
    assert r["matched"] == 1, "reference quote contained in candidate quote"


def test_span_normalizes_whitespace_before_containment():
    r = golden.compare([satom("a", "must   strive\n to  follow")],
                       [satom("b", Q)], level="span")
    assert r["matched"] == 1, "whitespace differences must not break containment"


def test_span_without_overlap_is_no_match():
    r = golden.compare([satom("a", "an entirely different sentence")],
                       [satom("b", Q)], level="span")
    assert r["matched"] == 0
    assert r["f1"] == 0.0


def test_span_empty_quote_never_matches():
    """"" is a substring of everything; an atom that cites nothing must not
    match everywhere for free."""
    r = golden.compare([satom("a", "")], [satom("b", Q)], level="span")
    assert r["matched"] == 0
    r = golden.compare([satom("a", "   ")], [satom("b", Q)], level="span")
    assert r["matched"] == 0
    r = golden.compare([satom("a", "")], [satom("b", "")], level="span")
    assert r["matched"] == 0


def test_span_default_is_pure_location_kind_is_ignored():
    """The headline number. A calibration author produced out-of-vocabulary
    kinds; a kind typo must degrade a kind-strict score, not zero the level."""
    r = golden.compare([satom("a", Q, kind="behavior")],
                       [satom("b", Q, kind="act")], level="span")
    assert r["matched"] == 1, "default span is location-only; kind ignored"


def test_span_kind_strict_requires_the_same_kind():
    cand = [satom("a", Q, kind="behavior")]
    ref = [satom("b", Q, kind="act")]
    r = golden.compare(cand, ref, level="span", kind_strict=True)
    assert r["matched"] == 0, "kind_strict=True must require the kind"
    r = golden.compare([satom("a", Q, kind="act")], ref, level="span",
                       kind_strict=True)
    assert r["matched"] == 1


def test_kind_strict_is_refused_outside_the_span_levels():
    """The flag exists for the span levels only; on the name-anchored ladder it
    would silently do nothing, which reads as doing something."""
    with pytest.raises(ValueError):
        golden.compare([], [], level="stem", kind_strict=True)
    with pytest.raises(ValueError):
        golden.compare([], [], level="exact", kind_strict=True)


def test_span_deco_rejects_a_polarity_mismatch_that_span_accepts():
    cand = [satom("must_follow_instructions", Q, role="consequent")]
    ref = [satom("mustnot_follow_instructions", Q, role="consequent")]
    assert golden.compare(cand, ref, level="span")["matched"] == 1
    assert golden.compare(cand, ref, level="span_deco")["matched"] == 0


def test_span_deco_rejects_a_principal_mismatch_that_span_accepts():
    cand = [satom("must_follow__model_user", Q, role="consequent")]
    ref = [satom("must_follow__user_model", Q, role="consequent")]
    assert golden.compare(cand, ref, level="span")["matched"] == 1
    assert golden.compare(cand, ref, level="span_deco")["matched"] == 0


def test_span_deco_rejects_a_role_mismatch_that_span_accepts():
    cand = [satom("must_follow", Q, role="condition")]
    ref = [satom("must_follow", Q, role="consequent")]
    assert golden.compare(cand, ref, level="span")["matched"] == 1
    assert golden.compare(cand, ref, level="span_deco")["matched"] == 0


def test_span_deco_matches_when_decoration_is_absent_on_both():
    """Absent equals absent: two bare atoms on the same span carry the same
    (empty) structure. Different STEMS, deliberately — span levels must not
    smuggle the name back in."""
    cand = [satom("one_naming", Q)]
    ref = [satom("another_naming", Q)]
    assert golden.compare(cand, ref, level="span_deco")["matched"] == 1


def test_span_deco_matches_identical_decoration_under_different_stems():
    cand = [satom("must_one_naming__model_user", Q, role="consequent")]
    ref = [satom("must_other_naming__model_user", Q, role="consequent")]
    assert golden.compare(cand, ref, level="span_deco")["matched"] == 1


def test_existing_levels_are_byte_unchanged_by_the_span_levels():
    """THE REGRESSION PIN. A fixture where span WOULD match (same quote) but
    the stems differ, plus a stem match with the wrong force: if the span logic
    leaked into the name-anchored ladder in either direction, at least one of
    these exact numbers moves."""
    ref = [satom("must_follow_instructions", Q, role="consequent"),
           satom("user_asked", "when the user asks", kind="situation",
                 role="condition")]
    cand = [satom("mustnot_follow_instructions", Q, role="consequent"),
            satom("differently_named_concept", "when the user asks",
                  kind="situation", role="condition")]
    stem = golden.compare(cand, ref, level="stem")
    assert stem["matched"] == 1          # shared stem only; quotes don't count
    assert stem["precision"] == 0.5
    assert stem["recall"] == 0.5
    exact = golden.compare(cand, ref, level="exact")
    assert exact["matched"] == 0         # polarity flipped on the stem match
    assert exact["f1"] == 0.0
    deo = golden.compare(cand, ref, level="deontic")
    assert deo["matched"] == 0


def test_score_all_supports_the_span_levels(g):
    cand = {e["clause_id"]: copy.deepcopy(e["atoms"]) for e in g.dev()}
    for level in ("span", "span_deco"):
        out = golden.score_all(cand, g, level=level)
        assert out["micro"]["f1"] == 1.0, level
        assert out["level"] == level


def test_held_out_guard_fires_for_the_span_levels_too(g):
    cand = {cid: [] for cid in g.held_out_ids}
    for level in ("span", "span_deco"):
        with pytest.raises(golden.HeldOutAccessError):
            golden.score_all(cand, g, level=level)


def test_score_all_passes_kind_strict_through(g):
    cand = {e["clause_id"]: copy.deepcopy(e["atoms"]) for e in g.dev()}
    out = golden.score_all(cand, g, level="span", kind_strict=True)
    assert out["micro"]["f1"] == 1.0
    with pytest.raises(ValueError):
        golden.score_all(cand, g, level="stem", kind_strict=True)
