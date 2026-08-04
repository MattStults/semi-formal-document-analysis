"""Gate tests for the DECORATION-BLIND JOIN — pricing v1.2 (BACKFILL_DESIGN.md
§6 as amended by PORTFOLIO_REVIEW.md F1; the S1 spine cycle).

The join contract, pinned here:

  * MATCH KEY IS THE DECHAINED NAME — the atom channel keys on
    (polarity + stem, kind) with the principal chain stripped. Polarity is NOT
    stripped (`must_` vs `mustnot_` staying distinct is the whole point of the
    grammar, which is why `grammar.stem_of` is the wrong key). A chained QUERY
    atom matches a chain-free clause instance of the same dechained name, and
    vice versa.
  * IDF/DF OVER DECHAINED NAMES — a name's chained and chain-free instances
    share ONE df entry (their clause sets unioned), so decoration can no
    longer split a concept's document frequency.
  * LEX EXCLUDES CHAIN PRINCIPAL TOKENS — the decoration's principal tokens
    (`model`, `user`, ...) never enter the lexical documents or the query
    text; chains are pure pricing metadata, invisible to every v1-era channel.
  * ADD-CHAIN INVARIANCE (the §6 gate mutant) — decorating an atom with a
    principal chain leaves EVERY channel score bit-identical under the v1.2
    join. Verified RED against the 1.1 exact-name join, where the same mutant
    moves scores in both directions (broken match + split df).
  * CHAIN-FREE PARITY, BIT-IDENTICAL — on inputs carrying no chains the v1.2
    index reproduces the base class bit for bit (dechaining is the identity
    there), which is what keeps every existing overlay snapshot
    reconstructible through the current code.
  * LEGACY REACHABLE (amendment F9) — relevance.RelevanceIndex keeps the
    exact-name join untouched: absent pricing_version key ⇒ legacy, exactly
    the CYCLE5_DESIGN §1.5 dispatch ladder's bottom rung. The overlay-less
    snapshot/dossier path reconstructs every pre-1.2 snapshot through it.
  * UNPARSEABLE NAMES PASS THROUGH — a name grammar.parse_name errors on is
    never rewritten (the stem_of contract: rewriting the join key on a name
    we could not read is the invisible failure).
"""
from __future__ import annotations

import collections
import hashlib
import json
import os

import pytest

import containment
import grammar
import relevance
import snapshot

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ANN = os.path.join(HERE, "annotations_ext_v1_merged.json")
REAL_ATOMS = os.path.join(HERE, "behavior_atoms_audit_v1.json")

#: Wide stopword ceiling so tiny fixtures exercise idf pricing rather than
#: the stopword floor (test_containment.py's convention).
W = relevance.Weights(atom_stopword_frac=1.0)


def _clauses(n, sect="s"):
    return [{"id": f"c{i}", "quote": f"filler text number {i} entirely bland",
             "section_path": [sect], "locator": f"L{i}"}
            for i in range(1, n + 1)]


def _atom(name, kind="act"):
    # Deliberately a CONSTANT gloss: glosses are authored prose, not
    # decoration — a real add-chain edit (an atom_refactor rechain) rewrites
    # ONLY the name — so the fixtures must not smuggle the chained name (and
    # its principal tokens) into the lexical documents through the gloss.
    return {"name": name, "kind": kind, "gloss": "a bland gloss"}


def _beh(*names):
    return relevance.Behaviour(slug="q", name="query", definition="",
                               atoms=[_atom(n) for n in names])


# ------------------------------------------------------------- the version

def test_pricing_version_is_1_2():
    """v1.2 is a scoring-rule change under identical inputs; the module names
    its own pricing regime so a snapshot's config identity can name the cause
    of a diff (the F9 / CYCLE5_DESIGN §1.5 dispatch ladder: absent ⇒ legacy,
    ≤ 1.1 ⇒ exact-name pricing, 1.2 ⇒ decoration-blind join)."""
    assert containment.PRICING_VERSION == "1.2"


def test_dechain_name_strips_chain_keeps_polarity():
    dn = containment.dechain_name
    assert dn("should_ask_clarifying_questions__model_user") \
        == "should_ask_clarifying_questions"
    assert dn("mustnot_lie__model_user") == "mustnot_lie"
    assert dn("shouldnot_judge__model_user_developer") == "shouldnot_judge"
    # chain-free: the identity, polarity untouched
    assert dn("mustnot_lie") == "mustnot_lie"
    assert dn("interject") == "interject"
    # NOT stem_of: polarity survives (stem_of would key must_/mustnot_ alike)
    assert dn("mustnot_lie__model_user").startswith("mustnot_")
    assert grammar.parse_name("mustnot_lie__model_user")["stem"] == "lie"
    # unparseable names pass through unrewritten (the stem_of contract)
    assert dn("must_") == "must_"
    assert dn("bad__name__twice") == "bad__name__twice"
    assert dn("x__notaprincipal") == "x__notaprincipal"


# ------------------------------------------- the two match-key directions

def test_chained_query_atom_matches_chainfree_clause_instance():
    """Direction (a) of the two-sided coincidence (PORTFOLIO_REVIEW F1): a
    chained QUERY atom, dechained, matches a chain-free clause instance —
    priced at the dechained name's (merged-df) idf. RED under the 1.1
    exact-name join, where this match does not exist at all."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("should_ask_clarifying_questions")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    got = over._atom_score(
        {("should_ask_clarifying_questions__model_user", "act")}, "c1")
    idf = over.atom_idf["should_ask_clarifying_questions"]
    assert got == pytest.approx(idf / over._atom_norm)
    assert got > 0.0


def test_chained_clause_atom_matches_chainfree_query_atom():
    """Direction (b): a chained CLAUSE atom is matched by the chain-free
    query atom of the same dechained name. RED under 1.1."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("mustnot_lie__model_user")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    got = over._atom_score({("mustnot_lie", "act")}, "c1")
    assert got == pytest.approx(over.atom_idf["mustnot_lie"]
                                / over._atom_norm)
    assert got > 0.0


def test_polarity_is_never_stripped_from_the_key():
    """`must_x__model_user` must NOT match `mustnot_x` — polarity stays in
    the join key; only the chain is decoration."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("mustnot_lie__model_user")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    assert over._atom_score({("must_lie", "act")}, "c1") == 0.0
    assert over._atom_score({("lie", "act")}, "c1") == 0.0


# --------------------------------------------------------- df/idf merging

def test_df_merges_chained_and_chainfree_instances():
    """One concept, one df: chained and chain-free instances of the same
    dechained name share a single df entry whose value is the size of the
    UNION of their clause sets. RED under 1.1 (split keys, split df)."""
    clauses = _clauses(6)
    ann = {"c1": [_atom("should_ask_clarifying_questions")],
           "c2": [_atom("should_ask_clarifying_questions__model_user")],
           "c3": [_atom("should_ask_clarifying_questions")],
           # both variants on one clause: counted once
           "c4": [_atom("should_ask_clarifying_questions"),
                  _atom("should_ask_clarifying_questions__model_user")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    assert over.atom_df["should_ask_clarifying_questions"] == 4
    assert "should_ask_clarifying_questions__model_user" not in over.atom_df
    assert "should_ask_clarifying_questions__model_user" not in over.atom_idf


# ------------------------------------------------------ lexical exclusion

def test_lex_channel_excludes_chain_principal_tokens():
    """The decoration's principal tokens never enter the lexical documents:
    a clause whose ONLY mention of `model`/`user` is an atom name's chain
    must not lex-match a query for those tokens. RED under 1.1 (underscores
    split, so the chain injects `model` and `user` into the doc)."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("mustnot_lie__model_user")],
           "c2": [_atom("pastry_recipe", "entity")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    for tok in ("model", "user"):
        assert tok not in over.vectors["c1"], \
            f"chain principal token {tok!r} leaked into c1's lex document"
    # and the query side: a chained query atom contributes no chain tokens
    beh = _beh("mustnot_lie__model_user")
    q = over._query_vector(beh)
    for tok in ("model", "user"):
        assert tok not in q, \
            f"chain principal token {tok!r} leaked into the query vector"


# ------------------------------------- the §6 add-chain invariance mutant

def _all_channels(idx, beh):
    return {cid: dict(ch) for cid, ch in idx.channel_scores(beh).items()}


def test_add_chain_mutant_leaves_every_channel_score_bit_identical():
    """THE GATE (BACKFILL_DESIGN §6): decorating a clause atom with a
    principal chain — the exact edit the S2 patient backfill will make at
    population scale — leaves every channel score of every clause
    BIT-IDENTICAL. Verified RED against the 1.1 exact-name join, where the
    same planted mutant moves scores (breaks the exact match on the edited
    clause AND moves idf on untouched clauses via the split df)."""
    clauses = _clauses(6)
    plain = {"c1": [_atom("should_seek_confirmation")],
             "c2": [_atom("should_seek_confirmation")],
             "c3": [_atom("unrelated_topic", "entity")]}
    # the planted add-chain mutant: one instance decorated, nothing else moved
    mutant = {"c1": [_atom("should_seek_confirmation__model_user")],
              "c2": [_atom("should_seek_confirmation")],
              "c3": [_atom("unrelated_topic", "entity")]}
    beh = _beh("should_seek_confirmation")
    a = containment.ContainmentIndex(clauses, plain, W, edges=())
    b = containment.ContainmentIndex(clauses, mutant, W, edges=())
    assert _all_channels(a, beh) == _all_channels(b, beh)
    # and on the query side: chaining the QUERY atom is equally invisible
    beh_chained = _beh("should_seek_confirmation__model_user")
    assert _all_channels(a, beh) == _all_channels(a, beh_chained)


# --------------------------------------------------- chain-free parity pin

def test_chainfree_parity_is_bit_identical():
    """On inputs carrying no chains, dechaining is the identity and the v1.2
    index must reproduce the base class BIT FOR BIT — same df, same idf, same
    channel scores. This is what keeps every pre-1.2 overlay snapshot
    (all built over the chain-free b8 artifacts) reconstructible through the
    current code, and what makes the empty-overlay measure snapshot a
    one-variable change."""
    clauses = _clauses(5)
    ann = {"c1": [_atom("mustnot_lie"), _atom("pastry_recipe", "entity")],
           "c2": [_atom("should_seek_confirmation")],
           "c4": [_atom("mustnot_lie")]}
    base = relevance.RelevanceIndex(clauses, ann, W)
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    assert base.atom_df == over.atom_df
    assert base.atom_idf == over.atom_idf
    assert base.vectors == over.vectors
    for beh in (_beh("mustnot_lie"), _beh("should_seek_confirmation",
                                          "pastry_recipe")):
        assert base.channel_scores(beh) == over.channel_scores(beh)


def test_legacy_relevance_index_keeps_the_exact_name_join():
    """Amendment F9: the OLD behavior stays reachable — the plain
    RelevanceIndex (the absent-pricing_version reconstruction path) still
    keys on exact names: chained keys keep their own df and a chained query
    atom does NOT match a chain-free clause instance."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("should_ask_clarifying_questions")],
           "c2": [_atom("should_ask_clarifying_questions__model_user")]}
    legacy = relevance.RelevanceIndex(clauses, ann, W)
    assert legacy.atom_df["should_ask_clarifying_questions"] == 1
    assert legacy.atom_df["should_ask_clarifying_questions__model_user"] == 1
    assert legacy._atom_score(
        {("should_ask_clarifying_questions__model_user", "act")}, "c1") == 0.0


# -------------------------------------------------- explain transparency

def test_explain_reports_the_dechaining_it_priced():
    """A dossier must be able to name the join behind a flip from explain()
    alone (the Unit 4.1 contract): when a chain was stripped on either side,
    explain carries a `dechained` record naming the original -> dechained
    query names and the clause's preserved chains; on chain-free evidence the
    key is ABSENT, keeping pre-1.2 explain payloads unchanged."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("mustnot_lie__model_user")],
           "c2": [_atom("pastry_recipe", "entity")]}
    over = containment.ContainmentIndex(clauses, ann, W, edges=())
    out = over.explain(_beh("mustnot_lie__model_user"), "c1")
    assert out["dechained"]["query"] == {
        "mustnot_lie__model_user": "mustnot_lie"}
    assert out["dechained"]["clause_chains"] == {
        "mustnot_lie": [["model", "user"]]}
    # the dechained match is visible in matched_atoms under its priced key
    assert any(m["name"] == "mustnot_lie" for m in out["matched_atoms"])
    plain = over.explain(_beh("pastry_recipe"), "c2")
    assert "dechained" not in plain


# ------------------------------------------- real-artifact chain metadata

#: The S1-era chain census, frozen 2026-08-04 from the live pre-backfill
#: merged artifact and sha-pinned: 109 [clause_id, dechained_name, chain]
#: rows. The S2 patient backfill ADDS chains by design, so the pin is
#: subset-not-equality: losing any S1 chain (or chain metadata wholesale)
#: fails; gaining licensed chains does not.
CENSUS = os.path.join(HERE, "dechain_chain_census_s1.json")
CENSUS_SHA = ("5376cde396ed2e4190c979be7b422c7a4db81683"
              "f056a71023179be8528ddfab")


def test_real_artifact_chains_are_preserved_as_metadata():
    """Chains become pricing METADATA, not nothing: the index preserves every
    clause's stripped chains (for the 2.0 patient-pricing layer and for
    dossiers) and keys none of them into atom_df. Re-pinned for the S2
    backfill (designer ruling at the IMPLEMENT halt): (i) the frozen S1
    census of 109 chain instances must survive as a sub-multiset of the live
    chains — the exact n == 109 equality is dropped, because S2 exists to
    add chains; (ii) every live chain is well-formed: members from the
    principal vocabulary, decorated-name round-trip through the grammar
    (whose chains read agent-first), and length >= 2 for every chain NOT in
    the frozen census (the backfill validator's rule; five S1-era length-1
    chains are grandfathered inside the census itself)."""
    if not os.path.exists(REAL_ANN):
        pytest.skip("real artifact not present")
    with open(CENSUS, "rb") as f:
        raw = f.read()
    assert hashlib.sha256(raw).hexdigest() == CENSUS_SHA, (
        "the frozen S1 chain census fixture changed — it is a historical "
        "record and must never be regenerated")
    frozen = [(cid, name, tuple(ch))
              for cid, name, ch in json.loads(raw)["chains"]]
    assert len(frozen) == 109
    over = containment.ContainmentIndex.from_files(
        annotations_path=REAL_ANN, edges=())
    live = [(cid, name, tuple(ch))
            for cid, by_name in over.chains.items()
            for name, chains in by_name.items()
            for ch in chains]
    missing = collections.Counter(frozen) - collections.Counter(live)
    assert not missing, (
        f"S1-era chains lost from the live artifact: {sorted(missing)[:5]}")
    frozen_set = set(frozen)
    for cid, name, ch in live:
        assert ch, f"empty chain on {cid}/{name}"
        decorated = name + "".join(f"__{m}" if i == 0 else f"_{m}"
                                   for i, m in enumerate(ch))
        p = grammar.parse_name(decorated)
        assert not p["error"] and p["principals"] == list(ch), (
            f"live chain {ch} on {cid}/{name} is outside the principal "
            "vocabulary / grammar")
        if (cid, name, ch) not in frozen_set:
            assert len(ch) >= 2, (
                f"post-S1 chain {ch} on {cid}/{name} is length-1: a lone "
                "member cannot state who acts on whom")
    assert not any("__" in name for name in over.atom_df)
