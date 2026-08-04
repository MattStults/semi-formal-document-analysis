"""Tests for containment.py — the licensed-subsumption overlay (Unit 4 v0).

What is being pinned, and why each pin exists:

  * EMPTY-OVERLAY EQUIVALENCE — with no edges, ContainmentIndex must reproduce
    RelevanceIndex on the real artifacts AT RECORDED PRECISION
    (snapshot.PRECISION-rounded scores, serialized canonically). The overlay
    is opt-in forever; "opt-in" is only true if opting in with nothing
    changes nothing.
  * EXACT MATCHES UNCHANGED — even with edges loaded, an exact name match must
    score exactly what the base class scores. Subsumption ADDS matches; it
    never re-prices existing ones.
  * THE MANIPULATION FAMILY — a query carrying `psychological_manipulation`
    must match a clause carrying `targeted_political_manipulation` through the
    licensed latent parent `manipulation`, in both directions, and when the
    query atom IS the parent. Pinned on a CONSTRUCTED fixture: pinning it on a
    real clause would be an outcome pin, which ITERATION_LOOP.md's case-bank
    rule forbids (a relevance label by another name).
  * SUBSUMER-IDF PRICING — a subsumption match is priced at the SUBSUMER's
    idf, strictly less than an exact match on a rarer child. The most-specific
    (rarest) common subsumer wins; a family match must never outbid the exact
    name it generalizes.
  * LICENSE REJECTIONS — every rejection class raises, naming the edge and the
    reason: polarity-prefixed child, principal in the modifier or chain,
    negation in the modifier, non-right-headed compound, cycle, wrong license
    string. Validation IS the license; a silently-accepted bad edge is an
    unreviewed vocabulary change.
  * LATENT-PARENT DF FORMULA — df(parent) = |union of the licensed children's
    clause sets| (overlapping clauses counted once), idf by the base formula.
  * ONE CREDIT PER CLAUSE ATOM (2026-08-03 review, finding 3, hole 1) — a
    clause-side atom's subsumption credit is awarded at most once per clause,
    its single best licensed match, never once per query sibling.
  * KIND DISCOUNT + THE INVARIANT (hole 2) — a real-atom subsumer's kind is
    checked as for exact matches; a latent subsumer with no checkable kind
    pays the mismatch discount, conservatively; and on identical evidence a
    subsumption match must NEVER outprice an exact match (credit capped at
    the matched clause atom's own exact price).
  * UNANIMOUS-CHILD KIND INHERITANCE (pricing v1.1) — a latent parent whose
    licensed children are ALL recorded under exactly one shared kind in the
    loaded clause vocabulary INHERITS that kind, and kind agreement is then
    checked against it exactly as for a real-vocabulary subsumer. A child
    with conflicting kinds, or any child with no recorded kind (absent from
    the clause vocabulary, or recorded kindless), blocks inheritance and the
    unconditional discount stays. Real-vocabulary subsumers never inherit.
  * EDGE BUDGET + FAMILY SUPPORT (hole 3) — the REQUIRED `budget`
    {max_edges, max_families} is enforced against the artifact's own edge
    list, and (when a vocabulary is supplied) every family needs >= 2
    children present in it: a one-child family is an alias.
  * V0 ARTIFACT — containment.json holds exactly the manipulation family, and
    that family is exactly the `_manipulation`-suffixed names present in the
    real b8 vocabulary (checked against the artifacts, not assumed); it
    declares budget {max_edges 4, max_families 2} and validates against the
    real b8 vocabulary.
"""
from __future__ import annotations

import json
import math
import os

import pytest

import containment
import relevance
import snapshot

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ANN = os.path.join(HERE, "annotations_b8.json")
REAL_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")

#: Wide stopword ceiling so tiny fixtures (where one atom easily covers >25%
#: of clauses) exercise idf pricing rather than the stopword floor.
W = relevance.Weights(atom_stopword_frac=1.0)

FAMILY_EDGES = (("psychological_manipulation", "manipulation"),
                ("targeted_political_manipulation", "manipulation"))


def _write_overlay(tmp_path, edges, name="ov.json", budget="fit"):
    """`budget="fit"` declares exactly the written edge/family counts;
    `budget=None` OMITS the (required) field; a dict is written verbatim."""
    for e in edges:
        e.setdefault("license", "shared_head")
        e.setdefault("note", "test")
    doc = {"artifact": "containment", "version": "v0",
           "edges": edges, "provenance": {"origin": "test"}}
    if budget == "fit":
        doc["budget"] = {"max_edges": len(edges),
                         "max_families": len({e["parent"] for e in edges})}
    elif budget is not None:
        doc["budget"] = budget
    path = str(tmp_path / name)
    with open(path, "w") as f:
        json.dump(doc, f)
    return path


def _clauses(n, sect="s"):
    return [{"id": f"c{i}", "quote": f"filler text number {i} entirely bland",
             "section_path": [sect], "locator": f"L{i}"}
            for i in range(1, n + 1)]


def _atom(name, kind="act"):
    return {"name": name, "kind": kind, "gloss": f"gloss of {name}"}


def _beh(*names):
    return relevance.Behaviour(slug="q", name="query", definition="",
                               atoms=[_atom(n) for n in names])


# --------------------------------------------------- empty-overlay equivalence

def _frozen_channels(idx, behaviours) -> bytes:
    """Canonical bytes of every behaviour's rounded channel decomposition —
    the same numbers a snapshot records, serialized the same way."""
    out = {}
    for slug in sorted(behaviours):
        ch = idx.channel_scores(behaviours[slug])
        out[slug] = {cid: {k: round(v, snapshot.PRECISION) + 0.0
                           for k, v in ch[cid].items()}
                     for cid in sorted(ch)}
    return json.dumps(out, sort_keys=True).encode()


def test_empty_overlay_reproduces_base_at_recorded_precision_on_real_artifacts():
    """With no edges, ContainmentIndex reproduces the base class's numbers AT
    RECORDED PRECISION (snapshot.PRECISION) — the intended contract, because
    that is the precision every snapshot freezes and every diff compares.

    Exact bit-identity is deliberately NOT claimed: the scorer's atom channel
    sums IDF terms in the iteration order of a set of strings, which varies
    with the per-process hash seed, so the last ulp of the sums is not stable
    even between two runs of the SAME class (see snapshot.py's PRECISION
    note). A sub-PRECISION perturbation (e.g. +1e-12) is therefore below this
    test's resolution BY DESIGN — anything at or above PRECISION fails."""
    if not (os.path.exists(REAL_ANN) and os.path.exists(REAL_ATOMS)):
        pytest.skip("real artifacts not present")
    base = relevance.RelevanceIndex.from_files(annotations_path=REAL_ANN)
    over = containment.ContainmentIndex.from_files(annotations_path=REAL_ANN,
                                                   edges=())
    behs = snapshot.load_behaviours(REAL_ATOMS)
    assert behs, "no behaviours with atoms — the comparison would be vacuous"
    assert base.atom_df == over.atom_df
    assert base.atom_idf == over.atom_idf
    assert _frozen_channels(base, behs) == _frozen_channels(over, behs)


def test_exact_matches_score_identically_even_with_edges_loaded():
    """Edges present, but the query atom has an exact clause match: the base
    class's number, to the last bit — subsumption never re-prices an exact hit."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation")],
           "c2": [_atom("pastry_recipe", "entity")]}
    base = relevance.RelevanceIndex(clauses, ann, W)
    over = containment.ContainmentIndex(clauses, ann, W,
                                        edges=FAMILY_EDGES)
    q = {("targeted_political_manipulation", "act")}
    assert over._atom_score(q, "c1") == base._atom_score(q, "c1")
    assert over._atom_score(q, "c2") == base._atom_score(q, "c2") == 0.0


# ------------------------------------------------- the manipulation family

def test_manipulation_family_match_child_to_sibling():
    """Query `psychological_manipulation`, clause `targeted_political_
    manipulation`: zero under the base matcher, positive under the overlay,
    priced at the latent parent's idf. Constructed fixture — never a pin on a
    real clause id."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation")],
           "c3": [_atom("pastry_recipe", "entity")]}
    beh = _beh("psychological_manipulation")
    base = relevance.RelevanceIndex(clauses, ann, W)
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAMILY_EDGES)

    assert base.channel_scores(beh)["c1"]["atom"] == 0.0
    got = over.channel_scores(beh)["c1"]["atom"]
    # `manipulation` is LATENT (no kinds defined), so the credit carries the
    # kind MISMATCH discount, conservatively (review hole 2)
    expected = (over.weights.atom
                * over.weights.kind_mismatch_discount
                * over.subsumer_idf["manipulation"] / over._atom_norm)
    assert got == pytest.approx(expected)
    assert got > 0.0
    # the unrelated clause gains nothing
    assert over.channel_scores(beh)["c3"]["atom"] == 0.0


def test_family_match_is_symmetric_and_covers_parent_as_query():
    clauses = _clauses(3)
    ann = {"c1": [_atom("psychological_manipulation")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAMILY_EDGES)
    # sibling direction reversed
    sib = over._atom_score({("targeted_political_manipulation", "act")}, "c1")
    # query atom IS the latent parent
    par = over._atom_score({("manipulation", "")}, "c1")
    assert sib > 0.0 and par > 0.0
    assert sib == pytest.approx(par)  # both priced at the same subsumer


# --------------------------------------------------- subsumer-idf pricing

def _pricing_fixture():
    """alpha_fam on 1 clause (rare), beta_fam on 3 (common); 6 clauses total.
    Parent union df = 4, so idf(parent) < idf(beta_fam) < idf(alpha_fam)."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("alpha_fam")],
           "c2": [_atom("beta_fam")], "c3": [_atom("beta_fam")],
           "c4": [_atom("beta_fam")],
           "c5": [_atom("other_thing", "entity")]}
    edges = (("alpha_fam", "fam"), ("beta_fam", "fam"))
    return clauses, ann, edges


def test_subsumption_priced_at_subsumer_idf_strictly_below_rarer_exact():
    clauses, ann, edges = _pricing_fixture()
    over = containment.ContainmentIndex(clauses, ann, W, edges=edges)
    q = {("alpha_fam", "act")}
    exact = over._atom_score(q, "c1")       # exact match on the rare child
    subsumed = over._atom_score(q, "c2")    # family match via the parent
    n = 6
    assert over.parent_df["fam"] == 4
    idf_parent = math.log(1.0 + n / (1.0 + 4))
    idf_alpha = math.log(1.0 + n / (1.0 + 1))
    # v1.1: both children are present and unanimously "act", so the latent
    # parent inherits the kind and the "act" query earns FULL kind credit
    assert subsumed == pytest.approx(idf_parent / over._atom_norm)
    assert exact == pytest.approx(idf_alpha / over._atom_norm)
    assert 0.0 < subsumed < exact


def test_non_latent_parent_is_priced_at_its_own_existing_idf():
    """A parent that IS a clause-vocabulary atom keeps the base index's price
    for it — the overlay invents idf only for parents the vocabulary lacks."""
    clauses = _clauses(5)
    ann = {"c1": [_atom("alpha_fam")], "c2": [_atom("fam")],
           "c3": [_atom("fam")]}
    over = containment.ContainmentIndex(clauses, ann, W,
                                        edges=(("alpha_fam", "fam"),))
    assert over.parent_df["fam"] == over.atom_df["fam"] == 2
    assert over.subsumer_idf["fam"] == over.atom_idf["fam"]


# ----------------------------------------------------------- explain override

def test_explain_names_the_subsumption_edge_behind_a_match():
    """The dossier behind a containment flip must be able to NAME the edge —
    query atom, clause atom, subsumer, subsumer idf — from the explain output
    alone (ITERATION_LOOP.md Unit 4.1). Exact matches stay in matched_atoms
    unchanged; subsumption matches get their own list."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation")],
           "c3": [_atom("pastry_recipe", "entity")]}
    beh = _beh("psychological_manipulation")
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAMILY_EDGES)
    base = relevance.RelevanceIndex(clauses, ann, W)

    ex = over.explain(beh, "c1")
    d = over.weights.kind_mismatch_discount
    assert ex["subsumption_matches"] == [{
        "query_atom": "psychological_manipulation",
        "clause_atom": "targeted_political_manipulation",
        "subsumer": "manipulation",
        "subsumer_idf": pytest.approx(over.subsumer_idf["manipulation"]),
        "kind_factor": pytest.approx(d),   # latent subsumer: discounted
        "credit": pytest.approx(d * over.subsumer_idf["manipulation"]),
    }]
    # exact-name matches are unchanged and stay where they were
    assert ex["matched_atoms"] == base.explain(beh, "c1")["matched_atoms"]
    # a clause with no family member reports no subsumption matches
    assert over.explain(beh, "c3")["subsumption_matches"] == []


def test_explain_exact_match_never_doubles_as_subsumption():
    """A query atom with an exact match on the clause is priced by the base
    class and must NOT also appear in subsumption_matches."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("targeted_political_manipulation")]}
    beh = _beh("targeted_political_manipulation")
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAMILY_EDGES)
    ex = over.explain(beh, "c1")
    assert ex["subsumption_matches"] == []
    assert [m["name"] for m in ex["matched_atoms"]] == \
        ["targeted_political_manipulation"]


def test_explain_subsumption_reports_the_priced_subsumer():
    """When several clause atoms share a subsumer with the query atom, the
    reported record is the one the scorer actually PRICED — the best (rarest)
    subsumer, matching _atom_score's credit exactly."""
    clauses, ann, edges = _pricing_fixture()
    over = containment.ContainmentIndex(clauses, ann, W, edges=edges)
    beh = _beh("alpha_fam")
    ex = over.explain(beh, "c2")   # beta_fam clause; match via latent "fam"
    assert len(ex["subsumption_matches"]) == 1
    m = ex["subsumption_matches"][0]
    assert m["query_atom"] == "alpha_fam"
    assert m["clause_atom"] == "beta_fam"
    assert m["subsumer"] == "fam"
    assert m["subsumer_idf"] == pytest.approx(over.subsumer_idf["fam"])
    # and the atom channel's credit is exactly this record's priced credit,
    # normalized — the same number _atom_score summed. v1.1: the pricing
    # fixture's children are unanimously "act", so the latent parent inherits
    # the kind and the "act" query pays no discount.
    assert m["kind_factor"] == pytest.approx(1.0)
    assert m["credit"] == pytest.approx(over.subsumer_idf["fam"])
    assert ex["channels"]["atom"] == pytest.approx(
        over.weights.atom * m["credit"] / over._atom_norm)


# ------------------------------- one credit per clause atom (review hole 1)

FAM5 = tuple((f"{m}_fam", "fam") for m in ("aa", "bb", "cc", "dd", "ee"))


def test_clause_atom_pays_at_most_one_query_sibling():
    """The reviewer's 4-sibling fixture: ONE clause-side family atom, FOUR
    query siblings. Before the fix every sibling was paid separately (score
    4.0 on this fixture); a clause atom's subsumption credit is awarded AT
    MOST ONCE per clause — its single best licensed match — never summed
    over query siblings."""
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam")], "c2": [_atom("other_thing", "entity")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAM5)
    q = {(f"{m}_fam", "act") for m in ("bb", "cc", "dd", "ee")}
    matches = over._subsumption_matches(q, "c1")
    assert len(matches) == 1, (
        "one clause-side family atom must earn exactly one subsumption "
        f"credit, got {len(matches)}")
    assert matches[0]["clause_atom"] == "aa_fam"
    # deterministic winner: ties break toward the sorted-first query sibling
    assert matches[0]["query_atom"] == "bb_fam"
    # and the score is exactly that single record's credit, normalized —
    # never a multiple of it
    assert over._atom_score(q, "c1") == pytest.approx(
        matches[0]["credit"] / over._atom_norm)


def test_distinct_clause_atoms_each_earn_at_most_one_credit():
    """Two clause-side family atoms, two query siblings with no exact match:
    each clause atom may be matched by at most one query sibling, so both
    credits survive — the per-clause-atom cap is a cap, not a collapse."""
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam"), _atom("bb_fam")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=FAM5)
    q = {("cc_fam", "act"), ("dd_fam", "act")}
    matches = over._subsumption_matches(q, "c1")
    assert len(matches) == 2
    assert [m["clause_atom"] for m in matches] == ["aa_fam", "bb_fam"]
    assert [m["query_atom"] for m in matches] == ["cc_fam", "dd_fam"]


# ----------------------------------- kind discount + invariant (review hole 2)

def test_latent_subsumer_without_unanimity_pays_the_kind_mismatch_discount():
    """A latent subsumer with no checkable kind — here, licensed child
    `bb_fam` is absent from the clause vocabulary, so v1.1's unanimity rule
    cannot fire — leaves kind AGREEMENT unverifiable; the credit
    conservatively carries the MISMATCH discount — for a matching kind, a
    foreign kind, and an empty kind alike. Before the v1 fix subsumption
    skipped the discount entirely: full 1.0 where a kind-mismatched exact
    match pays 0.4 (review hole 2)."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    d = over.weights.kind_mismatch_discount
    expected = d * over.subsumer_idf["fam"] / over._atom_norm
    for qkind in ("act", "value", ""):
        got = over._atom_score({("bb_fam", qkind)}, "c1")
        assert got == pytest.approx(expected), qkind


def test_real_subsumer_kind_agreement_checked_as_for_exact_matches():
    """When the subsumer IS a vocabulary atom its kinds are defined, so kind
    agreement is checked exactly as the base channel checks it for exact
    matches: full credit when the query kind is empty or among the subsumer's
    kinds, the mismatch discount otherwise."""
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam", "act")],
           "c2": [_atom("fam", "act")], "c3": [_atom("fam", "act")],
           "c4": [_atom("fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    d = over.weights.kind_mismatch_discount
    # real subsumer, priced at its own (base) idf: df(fam)=3 > df(aa_fam)=1,
    # so the clause-atom cap is inactive and the factor is isolated
    idf = over.subsumer_idf["fam"]
    assert idf == over.atom_idf["fam"]
    agree = over._atom_score({("bb_fam", "act")}, "c1")
    empty = over._atom_score({("bb_fam", "")}, "c1")
    clash = over._atom_score({("bb_fam", "value")}, "c1")
    assert agree == pytest.approx(idf / over._atom_norm)
    assert empty == pytest.approx(agree)
    assert clash == pytest.approx(d * idf / over._atom_norm)
    assert clash < agree


def test_subsumption_never_outprices_exact_on_identical_evidence():
    """THE INVARIANT (review hole 2): on identical evidence — the same clause
    annotation, the same query kind — a subsumption match must NEVER outprice
    an exact match. Latent case: the discount plus df(parent) >= df(child)
    keep it strictly below. Real-subsumer case: a subsumer atom RARER than the
    clause atom it matched through would outprice the exact match at its raw
    idf, so the credit is capped at the clause atom's own exact price."""
    # latent: strictly below the exact match on the same clause atom
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    exact = over._atom_score({("aa_fam", "act")}, "c1")
    sub = over._atom_score({("bb_fam", "act")}, "c1")
    assert 0.0 < sub < exact

    # real subsumer rarer than the clause atom: capped, never above
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("aa_fam", "act")],
           "c3": [_atom("aa_fam", "act")], "c4": [_atom("fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.subsumer_idf["fam"] > over.atom_idf["aa_fam"]  # rarer parent
    exact = over._atom_score({("aa_fam", "act")}, "c1")
    sub = over._atom_score({("bb_fam", "act")}, "c1")
    assert sub <= exact
    m = over._subsumption_matches({("bb_fam", "act")}, "c1")[0]
    assert m["credit"] == pytest.approx(over.atom_idf["aa_fam"])  # the cap


# ------------------- unanimous-child kind inheritance (pricing v1.1)

def test_pricing_version_is_exposed_and_bumped():
    """Every pricing regime change under identical inputs bumps the module's
    own version constant so a snapshot diff can name its cause. "1.2" = the
    decoration-blind join (decoration-blind-join-2026-08-04 cycle; the join
    semantics themselves are pinned in test_dechain.py)."""
    assert containment.PRICING_VERSION == "1.2"


def test_unanimous_act_kind_family_inherits_the_kind():
    """Both licensed children present in the clause vocabulary, both recorded
    under exactly "act": the latent parent inherits "act", and an "act" (or
    empty-kind) query atom earns FULL kind credit — the discount is lifted
    exactly where unanimity licenses it."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset({"act"})
    # cap inactive here: df(fam)=2 > df(bb_fam)=1, so idf(fam) < idf(bb_fam)
    idf = over.subsumer_idf["fam"]
    assert idf < over.atom_idf["bb_fam"]
    agree = over._atom_score({("aa_fam", "act")}, "c2")
    empty = over._atom_score({("aa_fam", "")}, "c2")
    assert agree == pytest.approx(idf / over._atom_norm)
    assert empty == pytest.approx(agree)
    # strictly above what the discount would have paid
    assert agree > over.weights.kind_mismatch_discount * idf / over._atom_norm


def test_inherited_kind_mismatch_with_query_still_pays_the_discount():
    """Inheritance makes the kind CHECKABLE, not free: a query atom whose
    kind clashes with the inherited kind pays the mismatch discount, exactly
    as it would against a real-vocabulary subsumer of that kind."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    d = over.weights.kind_mismatch_discount
    idf = over.subsumer_idf["fam"]
    clash = over._atom_score({("aa_fam", "value")}, "c2")
    agree = over._atom_score({("aa_fam", "act")}, "c2")
    assert clash == pytest.approx(d * idf / over._atom_norm)
    assert clash < agree


def test_conflicting_kind_family_does_not_inherit():
    """Children recorded under DIFFERENT kinds ("act" vs "value"): no
    unanimity, no inheritance — the latent parent keeps no kinds and the
    unconditional discount stays, for every query kind."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "value")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset()
    d = over.weights.kind_mismatch_discount
    idf = over.subsumer_idf["fam"]
    for qkind in ("act", "value", ""):
        got = over._atom_score({("aa_fam", qkind)}, "c2")
        assert got == pytest.approx(d * idf / over._atom_norm), qkind


def test_multi_kind_child_blocks_inheritance():
    """A child recorded under TWO kinds is not unanimous about either: no
    inheritance, the discount stays."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act"), _atom("aa_fam", "value")],
           "c2": [_atom("bb_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset()
    d = over.weights.kind_mismatch_discount
    got = over._atom_score({("bb_fam", "act")}, "c1")
    assert got == pytest.approx(
        d * min(over.subsumer_idf["fam"], over.atom_idf["aa_fam"])
        / over._atom_norm)


def test_missing_kind_child_blocks_inheritance():
    """Two blocking shapes of "no recorded kind": a licensed child ABSENT
    from the clause vocabulary, and a present child recorded KINDLESS. Either
    way the family's kind is not unanimously attested, so the latent parent
    inherits nothing and the discount stays."""
    d = W.kind_mismatch_discount
    # absent child: bb_fam is licensed but appears on no clause
    clauses = _clauses(6)
    ann = {"c1": [_atom("aa_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset()
    got = over._atom_score({("bb_fam", "act")}, "c1")
    assert got == pytest.approx(
        d * over.subsumer_idf["fam"] / over._atom_norm)

    # kindless child: bb_fam is present but recorded with an empty kind
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset()
    got = over._atom_score({("aa_fam", "act")}, "c2")
    assert got == pytest.approx(
        d * over.subsumer_idf["fam"] / over._atom_norm)


def test_real_vocabulary_subsumer_never_inherits_from_children():
    """Inheritance is for LATENT parents only. A subsumer that IS a
    vocabulary atom keeps its OWN recorded kinds even when its children are
    unanimous about a different kind — so an "act" query against a "value"
    real subsumer still pays the discount, exactly as before v1.1."""
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "act")],
           "c3": [_atom("fam", "value")], "c4": [_atom("fam", "value")],
           "c5": [_atom("fam", "value")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset({"value"})
    assert over.subsumer_idf["fam"] == over.atom_idf["fam"]
    d = over.weights.kind_mismatch_discount
    clash = over._atom_score({("aa_fam", "act")}, "c2")
    agree = over._atom_score({("aa_fam", "value")}, "c2")
    cap = min(over.subsumer_idf["fam"], over.atom_idf["bb_fam"])
    assert clash == pytest.approx(d * cap / over._atom_norm)
    assert agree == pytest.approx(cap / over._atom_norm)


def test_inherited_kind_credit_still_capped_by_the_clause_atom_price():
    """THE INVARIANT survives inheritance: full kind credit is still
    min(idf(subsumer), idf(clause_atom)), so an inherited-kind match never
    outprices the exact match on the same evidence. (A latent parent's union
    df is >= each child's df, so its idf is <= each child's — the min is the
    parent's idf and sub <= exact holds even at full kind credit; the
    rarer-REAL-subsumer cap case is pinned, unmodified, in
    test_subsumption_never_outprices_exact_on_identical_evidence.)"""
    clauses = _clauses(8)
    ann = {"c1": [_atom("aa_fam", "act")], "c2": [_atom("bb_fam", "act")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_kinds["fam"] == frozenset({"act"})  # inheritance ON
    exact = over._atom_score({("bb_fam", "act")}, "c2")
    sub = over._atom_score({("aa_fam", "act")}, "c2")
    assert 0.0 < sub <= exact
    m = over._subsumption_matches({("aa_fam", "act")}, "c2")[0]
    assert m["credit"] == pytest.approx(
        min(over.subsumer_idf["fam"], over.atom_idf["bb_fam"]))


# ------------------------------------------------ latent-parent df formula

def test_latent_parent_df_is_the_union_of_children_clause_sets():
    """A_fam on {c1,c2}, B_fam on {c2,c3}: union {c1,c2,c3}, df=3 — the shared
    clause is counted ONCE. Summing child dfs (4) would over-rarify nothing
    and over-common-ify the parent; the union is the set of clauses on which
    the parent concept is attested at all."""
    clauses = _clauses(5)
    ann = {"c1": [_atom("aa_fam")],
           "c2": [_atom("aa_fam"), _atom("bb_fam")],
           "c3": [_atom("bb_fam")]}
    over = containment.ContainmentIndex(
        clauses, ann, W, edges=(("aa_fam", "fam"), ("bb_fam", "fam")))
    assert over.parent_df["fam"] == 3
    assert over.subsumer_idf["fam"] == pytest.approx(
        math.log(1.0 + 5 / (1.0 + 3)))


# ------------------------------------------------------ license rejections

@pytest.mark.parametrize("edges,reason,named", [
    # a polarity prefix on the child is a deontic flip, not a specializer
    ([{"child": "mustnot_psychological_manipulation",
       "parent": "manipulation"}], "polarity",
     "mustnot_psychological_manipulation"),
    # a principal as the modifier changes WHO, not WHAT KIND
    ([{"child": "user_manipulation", "parent": "manipulation"}],
     "principal", "user_manipulation"),
    # a principal chain on the child is the same failure spelled differently
    ([{"child": "psychological_manipulation__user",
       "parent": "manipulation"}], "principal",
     "psychological_manipulation__user"),
    # a negation makes the child the parent's complement, not its subset
    ([{"child": "non_targeted_manipulation", "parent": "manipulation"}],
     "negation", "non_targeted_manipulation"),
    ([{"child": "no_manipulation_content", "parent": "content"}],
     "negation", "no_manipulation_content"),
    # v0 licenses ONLY right-headed compounds — mechanically checkable
    ([{"child": "manipulation_psychological", "parent": "manipulation"}],
     "right-headed", "manipulation_psychological"),
    ([{"child": "psychological_manipulation", "parent": "psychological"}],
     "right-headed", "psychological_manipulation"),
    # a cycle makes every member subsume itself
    ([{"child": "a_b", "parent": "b"}, {"child": "b", "parent": "a_b"}],
     "cycle", "a_b"),
    ([{"child": "x_x", "parent": "x_x"}], "cycle", "x_x"),
    # an unknown license string is an unreviewed licensing regime
    ([{"child": "psychological_manipulation", "parent": "manipulation",
       "license": "vibes"}], "license", "psychological_manipulation"),
])
def test_license_rejections_name_the_edge_and_the_reason(
        tmp_path, edges, reason, named):
    path = _write_overlay(tmp_path, edges)
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path)
    msg = str(ei.value)
    assert reason in msg
    assert named in msg


def test_valid_overlay_loads_and_empty_overlay_is_empty(tmp_path):
    good = _write_overlay(tmp_path, [
        {"child": "targeted_political_manipulation",
         "parent": "manipulation"},
        {"child": "psychological_manipulation", "parent": "manipulation"},
    ], name="good.json")
    assert containment.load_edges(good) == FAMILY_EDGES  # sorted, deduped
    empty = _write_overlay(tmp_path, [], name="empty.json")
    assert containment.load_edges(empty) == ()


# ---------------------------------- edge budget + family support (review hole 3)

TWO_EDGES = [{"child": "psychological_manipulation", "parent": "manipulation"},
             {"child": "targeted_political_manipulation",
              "parent": "manipulation"}]


def test_budget_is_required(tmp_path):
    """The schema's `budget` field is REQUIRED: an overlay that does not
    declare its own ceiling can grow without ever tripping a review."""
    path = _write_overlay(tmp_path, list(TWO_EDGES), budget=None)
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path)
    assert "budget" in str(ei.value)


@pytest.mark.parametrize("bad", [
    "vibes",                                        # not an object
    {"max_edges": 4},                               # max_families missing
    {"max_families": 2},                            # max_edges missing
    {"max_edges": "4", "max_families": 2},          # not an int
    {"max_edges": 4, "max_families": True},         # bool is not a count
    {"max_edges": -1, "max_families": 2},           # negative
])
def test_malformed_budget_is_rejected(tmp_path, bad):
    path = _write_overlay(tmp_path, list(TWO_EDGES), budget=bad)
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path)
    assert "budget" in str(ei.value)


def test_edge_list_exceeding_its_own_budget_is_rejected(tmp_path):
    path = _write_overlay(tmp_path, list(TWO_EDGES),
                          budget={"max_edges": 1, "max_families": 2})
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path)
    assert "max_edges" in str(ei.value) and "2" in str(ei.value)


def test_family_count_exceeding_its_own_budget_is_rejected(tmp_path):
    edges = [{"child": "aa_fam", "parent": "fam"},
             {"child": "bb_fam", "parent": "fam"},
             {"child": "aa_grp", "parent": "grp"},
             {"child": "bb_grp", "parent": "grp"}]
    path = _write_overlay(tmp_path, edges,
                          budget={"max_edges": 4, "max_families": 1})
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path)
    assert "max_families" in str(ei.value)


def test_one_child_family_is_rejected_against_the_vocabulary(tmp_path):
    """A one-child family is an ALIAS, not a generalization: with a single
    attested child the latent parent's df equals the child's df, so the
    'family' match re-prices the child under another name. `load_edges`
    rejects it loudly, naming the family, when given the vocabulary."""
    path = _write_overlay(tmp_path, [{"child": "aa_fam", "parent": "fam"}])
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path, vocabulary={"aa_fam", "other_thing"})
    msg = str(ei.value)
    assert "fam" in msg and "alias" in msg


def test_family_children_must_be_present_in_the_vocabulary(tmp_path):
    """Two children on paper, one in the vocabulary = a one-child family in
    every df that will ever be computed. Presence, not edge count, is what
    the check counts."""
    path = _write_overlay(tmp_path, [{"child": "aa_fam", "parent": "fam"},
                                     {"child": "bb_fam", "parent": "fam"}])
    with pytest.raises(ValueError) as ei:
        containment.load_edges(path, vocabulary={"aa_fam", "other_thing"})
    assert "alias" in str(ei.value) and "fam" in str(ei.value)
    # with both children present the same file loads
    got = containment.load_edges(path, vocabulary={"aa_fam", "bb_fam"})
    assert got == (("aa_fam", "fam"), ("bb_fam", "fam"))


def test_without_a_vocabulary_load_edges_skips_the_family_check(tmp_path):
    """snapshot.py / dossier.py reconstruct a RECORDED (sha-verified) overlay
    with `load_edges(path)` and no vocabulary in hand; reconstruction of an
    already-frozen artifact must not be blocked by the artifact-review check.
    The check runs wherever a vocabulary IS supplied — the artifact pin below
    runs it against the real b8 names."""
    path = _write_overlay(tmp_path, [{"child": "aa_fam", "parent": "fam"}])
    assert containment.load_edges(path) == (("aa_fam", "fam"),)


# ------------------------------------------------------------ the v0 artifact

def _b8_vocabulary():
    """Every atom name appearing in the real b8 artifacts (clause + query)."""
    names = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("name"), str):
                names.add(o["name"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for p in (REAL_ANN, REAL_ATOMS):
        with open(p) as f:
            walk(json.load(f))
    return names


def test_v0_artifact_is_exactly_the_manipulation_family():
    path = os.path.join(HERE, "containment.json")
    assert os.path.exists(path), "containment.json (the v0 artifact) missing"
    assert containment.load_edges(path) == FAMILY_EDGES


def test_v0_artifact_declares_a_tight_budget():
    """v0 declares max_edges 4 / max_families 2 — headroom for exactly one
    more two-child family, no more. The budget lives in the file, so it
    participates in the overlay sha every snapshot records: raising it is a
    visible config change, never a drift."""
    path = os.path.join(HERE, "containment.json")
    with open(path) as f:
        doc = json.load(f)
    assert doc["budget"] == {"max_edges": 4, "max_families": 2}


def test_v0_artifact_validates_against_the_real_vocabulary():
    """The family-support check, run for real: both manipulation children are
    present in the b8 vocabulary, so the artifact loads under it."""
    if not (os.path.exists(REAL_ANN) and os.path.exists(REAL_ATOMS)):
        pytest.skip("real artifacts not present")
    got = containment.load_edges(os.path.join(HERE, "containment.json"),
                                 vocabulary=_b8_vocabulary())
    assert got == FAMILY_EDGES


def test_v0_family_membership_matches_the_real_vocabulary():
    """The artifact's children must be EXACTLY the `_manipulation`-suffixed
    names in the b8 vocabulary — verified against the artifacts, not assumed,
    so vocabulary drift surfaces here instead of silently orphaning an edge."""
    if not (os.path.exists(REAL_ANN) and os.path.exists(REAL_ATOMS)):
        pytest.skip("real artifacts not present")
    family = {n for n in _b8_vocabulary() if n.endswith("_manipulation")}
    children = {c for c, _ in
                containment.load_edges(os.path.join(HERE, "containment.json"))}
    assert children == family


# ------------------------------------------------------------ opt-in forever

def test_constructor_default_is_empty_edges_and_never_reads_a_file(tmp_path):
    """No edges argument → no edges, base scoring — there is no default-on
    path, and nothing implicitly loads containment.json."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("psychological_manipulation")]}
    base = relevance.RelevanceIndex(clauses, ann, W)
    over = containment.ContainmentIndex(clauses, ann, W)
    assert over.edges == ()
    q = {("targeted_political_manipulation", "act")}
    assert over._atom_score(q, "c1") == base._atom_score(q, "c1") == 0.0
