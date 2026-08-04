"""Tests for grammar.py — the notation's single source of truth.

`ladder.py` and `structural.py` each carry a hand-copied declaration of this
notation, pinned equal to each other by
`test_structural.test_the_notation_constants_agree_with_the_ladder_that_emits_them`.
Neither may import the other (`ladder` pulls in the provider layer, which
`structural` may not reference), so a third copy was going to appear the moment
a third consumer needed it — and the annotation surface IS that third consumer.
`grammar.py` is the declaration; this file pins the two existing copies to it.

The four properties everything downstream rests on, re-verified here over the
REAL vocabulary rather than a fixture:

  1. no shipped atom name begins with a reserved polarity prefix,
  2. no shipped atom name contains the principal separator,
  3. `stem_of` is therefore the IDENTITY on every shipped name — which is what
     makes every existing artifact keep working unchanged,
  4. `mustnot_` and `must_` do not shadow each other (longest-first).

(1)-(3) are backward compatibility. If any of them breaks, `annotations_b8.json`
starts decoding as though it carried a deontic force nobody wrote.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import grammar as G

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")


# --------------------------------------------------------------------------
# the declaration


def test_the_module_exports_the_notation_the_task_pinned():
    assert G.POLARITY_PREFIXES == ("must_", "mustnot_", "should_",
                                   "shouldnot_", "may_")
    assert G.PRINCIPAL_SEP == "__"
    assert G.PRINCIPALS == ("third_party", "developer", "operator", "system",
                            "model", "root", "user")


def test_platform_is_gone_and_root_replaced_it():
    """The Model Spec renamed its top level Platform -> Root AND split it from
    System, which the old vocabulary had defined as its equal. Leaving
    `platform` in would hand the extractor a token for a level the current
    document does not have; leaving `root` out cost m0040 its content."""
    assert "platform" not in G.PRINCIPALS
    assert "root" in G.PRINCIPALS
    assert "system" in G.PRINCIPALS, "root must not have absorbed system"


def test_renaming_platform_moved_no_join_key():
    """Why the rename was safe to do outright rather than by migration: no
    shipped atom name carries a principal chain, so `stem_of` is unchanged."""
    import json
    import pathlib
    here = pathlib.Path(__file__).parent
    names = set()

    def walk(o):
        if isinstance(o, dict):
            n = o.get("name")
            if isinstance(n, str):
                names.add(n)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for fn in ("annotations.json", "annotations_b8.json",
               "behavior_atoms_b8.json"):
        p = here / fn
        if p.exists():
            walk(json.loads(p.read_text()))
    assert names, "no shipped names loaded; this test would pass vacuously"
    carried = [n for n in names if G.PRINCIPAL_SEP in n]
    assert carried == [], f"principal chains exist and would need migrating: {carried[:5]}"
    assert all(G.stem_of(n) == n for n in names)


def test_principals_are_declared_longest_first():
    """`third_party` contains `_`, so a left-to-right split would tear it in
    half and a shorter principal matched first would swallow its prefix."""
    for i, p in enumerate(G.PRINCIPALS):
        for q in G.PRINCIPALS[i + 1:]:
            assert not q.startswith(p), (
                f"{q!r} comes after its own prefix {p!r}; the scan is "
                "longest-first and would never reach it")


def test_polarity_prefixes_are_declared_longest_first_where_they_nest():
    """`must_` is a prefix of nothing, but `mustnot_` shares its first four
    characters. A scan that tested `must_` against `mustnot_x` would not match
    (the underscore differs) — this asserts the property directly rather than
    trusting that coincidence."""
    assert G.parse_name("mustnot_x")["polarity"] == "mustnot"
    assert G.parse_name("must_x")["polarity"] == "must"
    assert G.parse_name("shouldnot_x")["polarity"] == "shouldnot"
    assert G.parse_name("should_x")["polarity"] == "should"


# --------------------------------------------------------------------------
# parse_name is TOTAL


@pytest.mark.parametrize("name", [
    "must_", "mustnot_", "a__b__c", "a__nobody", "x__", "__x",
    "", None, 3, "must___user",
])
def test_an_unparseable_name_yields_an_error_and_never_a_plausible_parse(name):
    """A convention that half-parses is worse than none: the render would then
    assert a deontic force nobody wrote."""
    p = G.parse_name(name)
    assert p["error"], f"{name!r} parsed without complaint"
    assert p["polarity"] is None
    assert not p["principals"]


def test_parse_name_returns_the_four_declared_keys_always():
    for name in ("plain", "must_x__model_user", "must_", None):
        assert set(G.parse_name(name)) == {"polarity", "stem", "principals",
                                           "error"}


def test_a_fully_decorated_name_parses_into_its_three_parts():
    p = G.parse_name("mustnot_disclose_reasoning__model_user")
    assert p["error"] is None
    assert p["polarity"] == "mustnot"
    assert p["stem"] == "disclose_reasoning"
    assert list(p["principals"]) == ["model", "user"]


def test_the_principal_chain_is_ORDERED_and_the_order_is_the_relation():
    a = G.parse_name("must_defer__model_operator")
    b = G.parse_name("must_defer__operator_model")
    assert list(a["principals"]) == ["model", "operator"]
    assert list(b["principals"]) == ["operator", "model"]
    assert a["principals"] != b["principals"], (
        "who acts and who is acted upon collapsed into one atom")


def test_third_party_is_not_torn_in_half_by_the_separator_scan():
    p = G.parse_name("mustnot_harm__model_third_party")
    assert p["error"] is None
    assert list(p["principals"]) == ["model", "third_party"]


def test_format_name_is_the_inverse_of_parse_name():
    for pol, stem, pri in (("must", "x", ("model", "user")),
                           (None, "x", ()),
                           ("may", "x", ()),
                           (None, "x", ("third_party",))):
        n = G.format_name(stem, pol, pri)
        p = G.parse_name(n)
        assert p["error"] is None
        assert (p["polarity"], p["stem"], tuple(p["principals"])) == (pol,
                                                                     stem, pri)


def test_stem_of_returns_the_name_itself_when_the_name_does_not_parse():
    """An unparseable name has no stem to strip to. Returning a guessed stem
    would silently rewrite an atom the join is keyed on."""
    assert G.stem_of("a__b__c") == "a__b__c"
    assert G.stem_of("must_") == "must_"


# --------------------------------------------------------------------------
# THE ROLE FIELD — condition / exception / consequent


def test_the_role_vocabulary_is_closed_and_small():
    assert G.ROLES == ("condition", "exception", "consequent", "topic")
    assert set(G.ROLE_ENGLISH) == set(G.ROLES)


def test_an_absent_role_is_not_an_error_and_is_not_invented():
    """Every shipped artifact predates this field. `role_of` must report
    'nothing recorded' rather than defaulting to a role the annotator did not
    write — a default would make every legacy atom assert a structure."""
    assert G.role_of({"name": "x"}) is None
    assert G.role_of({"name": "x", "role": None}) is None
    assert G.role_of({"name": "x", "role": ""}) is None


def test_an_unknown_role_is_rejected_rather_than_coerced():
    assert G.role_of({"name": "x", "role": "trigger"}) is None
    assert G.valid_role("trigger") is False
    assert G.valid_role("condition") is True


def test_role_is_normalised_for_case_and_whitespace_only():
    assert G.role_of({"name": "x", "role": " Condition "}) == "condition"


# --------------------------------------------------------------------------
# ENGLISH — the decode the read-back needs


def test_polarity_decodes_to_english_for_every_reserved_prefix():
    for p in G.POLARITY_PREFIXES:
        assert G.POLARITY_ENGLISH[p[:-1]]
    assert "not" in G.POLARITY_ENGLISH["mustnot"].lower() or \
        "forbid" in G.POLARITY_ENGLISH["mustnot"].lower()


def test_must_and_mustnot_do_not_decode_to_the_same_english():
    assert G.POLARITY_ENGLISH["must"] != G.POLARITY_ENGLISH["mustnot"]
    assert G.POLARITY_ENGLISH["should"] != G.POLARITY_ENGLISH["shouldnot"]


def test_describe_says_nothing_at_all_about_an_undecorated_atom():
    """The whole backward-compatibility story in one assertion: an atom in the
    shipped shape must produce NO decoration, so its render is byte-identical
    to what the read-back measured."""
    assert G.describe({"name": "clarify_user_intent", "kind": "act"}) == ""


def test_describe_names_the_force_the_actor_and_the_patient():
    txt = G.describe({"name": "mustnot_disclose__model_user", "kind": "act"})
    assert "model" in txt and "user" in txt
    assert "mustnot" not in txt, "the raw prefix leaked instead of English"
    assert G.POLARITY_ENGLISH["mustnot"].split()[0].lower() in txt.lower()


def test_describe_distinguishes_a_condition_from_a_consequent():
    cond = G.describe({"name": "x", "kind": "situation", "role": "condition"})
    cons = G.describe({"name": "x", "kind": "act", "role": "consequent"})
    exc = G.describe({"name": "x", "kind": "situation", "role": "exception"})
    assert cond != cons != exc and cond != exc


def test_carries_notation_is_false_for_the_shipped_atom_shape():
    assert G.carries_notation([{"name": "a"}, {"name": "b_c"}]) is False
    assert G.carries_notation([{"name": "must_a"}]) is True
    assert G.carries_notation([{"name": "a", "role": "condition"}]) is True
    assert G.carries_notation([{"name": "a", "role": "bogus"}]) is False


def test_records_reports_exactly_which_features_are_present():
    got = G.records([{"name": "must_a"}, {"name": "b__model_user"},
                     {"name": "c", "role": "condition"}])
    assert got["polarity"] and got["principals"] and got["condition"]
    assert not G.records([{"name": "a"}])["polarity"]


# --------------------------------------------------------------------------
# PINNED to the two hand-copied declarations already in the repo


def test_the_constants_agree_with_ladder():
    import ladder as L
    assert G.POLARITY_PREFIXES == L.POLARITY_PREFIXES
    assert G.PRINCIPAL_SEP == L.PRINCIPAL_SEP
    assert G.PRINCIPALS == L.PRINCIPALS


def test_the_constants_agree_with_structural():
    import structural as S
    assert G.POLARITY_PREFIXES == S.POLARITY_PREFIXES
    assert G.PRINCIPAL_SEP == S.PRINCIPAL_SEP
    assert G.PRINCIPALS == S.PRINCIPALS


@pytest.mark.parametrize("name", [
    "clarify_user_intent", "must_disclose__model_user", "may_x",
    "mustnot_y__third_party", "must_", "a__nobody", "a__b__c",
    "shouldnot_z__model_operator_third_party",
    "mustnot_harm__model_third_party",
])
def test_the_parse_agrees_with_both_hand_copies_case_for_case(name):
    """The two copies are pinned to each other elsewhere; this pins them to the
    declaration. A silent edit in any of the three is now caught twice."""
    import ladder as L
    import structural as S
    mine, lad, st = G.parse_name(name), L.parse_name(name), S.parse_atom_name(name)
    for other, who in ((lad, "ladder"), (st, "structural")):
        assert bool(mine["error"]) == bool(other["error"]), (name, who)
        if mine["error"]:
            continue          # see test_the_copies_leave_a_polarity_set_...
        assert mine["stem"] == other["stem"], (name, who)
        assert mine["polarity"] == other["polarity"], (name, who)
        assert list(mine["principals"]) == list(other["principals"]), (name, who)


def test_the_copies_leave_a_polarity_set_on_an_ERRORED_parse_and_this_one_does_not():
    """The one deliberate divergence, asserted so it cannot drift silently.

    `ladder.parse_name("must_")` sets `polarity="must"` and THEN discovers there
    is no stem, returning both the error and the field. Every caller checks
    `error` first, so nothing is broken today — but the task's requirement is
    that an unparseable name never yields a plausible parse, so `grammar` clears
    it. If a copy is ever fixed to match, this test fails and says so.
    """
    import ladder as L
    import structural as S
    assert L.parse_name("must_")["polarity"] == "must"
    assert S.parse_atom_name("must_")["polarity"] == "must"
    assert G.parse_name("must_")["polarity"] is None
    for mod, fn in ((L, "parse_name"), (S, "parse_atom_name")):
        assert getattr(mod, fn)("must_")["error"]


def test_stem_of_agrees_with_structurals_copy():
    import structural as S
    for name in ("clarify_user_intent", "must_disclose__model_user", "must_",
                 "a__b__c", "may_x"):
        assert G.stem_of(name) == S.stem_of(name), name


# --------------------------------------------------------------------------
# THE REAL VOCABULARY — the properties the whole design rests on


def _shipped_names():
    import json
    names = set()
    with open(ANNOTATIONS, encoding="utf-8") as f:
        data = json.load(f)
    for v in (data.get("vocabulary") or {}):
        names.add(v)
    for a in data.get("atoms", []):
        if a.get("name"):
            names.add(a["name"])
    with open(BEHAVIOUR_ATOMS, encoding="utf-8") as f:
        q = json.load(f)
    for rec in (q.get("behaviours") or q.get("queries") or {}).values():
        for a in (rec.get("atoms") if isinstance(rec, dict) else rec) or []:
            n = a.get("name") if isinstance(a, dict) else a
            if n:
                names.add(n)
    return names


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_the_real_vocabulary_loaded():
    assert len(_shipped_names()) >= 361


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_no_shipped_name_begins_with_a_reserved_polarity_prefix():
    bad = sorted(n for n in _shipped_names()
                 if any(n.startswith(p) for p in G.POLARITY_PREFIXES))
    assert bad == [], (
        f"{bad} would decode as a deontic force nobody wrote; the prefixes are "
        "no longer reserved and every existing artifact now lies")


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_no_shipped_name_contains_the_principal_separator():
    bad = sorted(n for n in _shipped_names() if G.PRINCIPAL_SEP in n)
    assert bad == []


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_stem_of_is_the_identity_on_every_shipped_name():
    """BACKWARD COMPATIBILITY, at the root: the stem-aware join asks for the
    same string twice on every existing artifact."""
    for n in sorted(_shipped_names()):
        assert G.stem_of(n) == n, n
        p = G.parse_name(n)
        assert p["error"] is None, n
        assert p["polarity"] is None and not p["principals"], n


@pytest.mark.skipif(not os.path.exists(ANNOTATIONS), reason="artifacts absent")
def test_no_shipped_atom_carries_a_role_and_none_is_invented_for_it():
    import json
    with open(ANNOTATIONS, encoding="utf-8") as f:
        data = json.load(f)
    for a in data.get("atoms", []):
        assert G.role_of(a) is None
    assert G.carries_notation(data.get("atoms", [])[:500]) is False


# --------------------------------------------------------------------------
# THE READ-BACK DECODE — readback.render must print English, not an opaque name
#
# These live here rather than in test_readback.py because what they test is the
# grammar's decode surface; test_readback.py owns the harness.


def _rb():
    import readback as rb
    return rb


def test_render_of_a_legacy_annotation_still_denies_holding_all_five_things():
    """The closing paragraph is only false where the annotation makes it false.
    On a shipped artifact nothing is decoded, so it must read exactly as the
    read-back measured it — otherwise rung 0's baseline stops applying."""
    rb = _rb()
    txt = rb.render([{"name": "clarify_user_intent", "kind": "act",
                      "gloss": "asks what the user meant", "span_id": "s1"}],
                    "conditional")
    assert ("no condition, no exception, no priority, no polarity, and nothing "
            "about who is addressed or what is required") in txt


def test_render_of_a_legacy_annotation_is_unchanged_by_the_extension():
    """Byte-level backward compatibility on the REAL artifact, not a fixture."""
    import json
    rb = _rb()
    with open(ANNOTATIONS, encoding="utf-8") as f:
        by_clause = json.load(f)["by_clause"]
    for cid, atoms in list(by_clause.items())[:200]:
        txt = rb.render(atoms, "conditional")
        assert "FORCE:" not in txt and "ROLE:" not in txt and "WHO:" not in txt
        assert rb.LEGACY_CLOSING in txt


def test_a_polarity_prefixed_atom_renders_its_force_in_english():
    rb = _rb()
    txt = rb.render([{"name": "mustnot_disclose_reasoning__model_user",
                      "kind": "act", "gloss": "shows its own reasoning",
                      "span_id": "s1"}], "conditional")
    assert "FORBIDDEN" in txt
    assert "WHO:" in txt and "model" in txt and "user" in txt


def test_the_closing_stops_denying_polarity_once_polarity_is_recorded():
    rb = _rb()
    txt = rb.render([{"name": "mustnot_x__model_user", "kind": "act",
                      "gloss": "g", "span_id": "s1"}], "conditional")
    # the DENIAL LIST loses its polarity item. ("no polarity" still occurs
    # inside the convention note, which explains that a name WITHOUT a prefix
    # records none — that sentence is true and must survive.)
    assert "no priority, no polarity" not in txt
    assert "no condition, no exception, and no priority." in txt
    assert "nothing about who is addressed" not in txt


def test_the_closing_stops_denying_conditions_once_a_role_is_recorded():
    rb = _rb()
    txt = rb.render([{"name": "x", "kind": "situation", "gloss": "g",
                      "span_id": "s1", "role": "condition"}], "conditional")
    assert "no condition" not in txt
    assert "no polarity" in txt        # still true: no polarity was recorded


def test_the_closing_stops_denying_exceptions_once_an_exception_is_recorded():
    rb = _rb()
    txt = rb.render([{"name": "x", "kind": "situation", "gloss": "g",
                      "span_id": "s1", "role": "exception"}], "conditional")
    assert "no exception" not in txt


def test_if_X_then_Y_and_Y_unless_X_no_longer_render_identically():
    """THE DEFECT, in one test. Conditionals are 1/25 sufficient because these
    two clauses currently produce the same unordered set {X, Y}."""
    rb = _rb()
    x = {"name": "user_request_ambiguous", "kind": "situation",
         "gloss": "the request admits two readings", "span_id": "s1"}
    y = {"name": "ask_clarifying_question", "kind": "act",
         "gloss": "asks the user which was meant", "span_id": "s1"}
    if_then = rb.render([dict(x, role="condition"), dict(y, role="consequent")],
                        "conditional")
    unless = rb.render([dict(x, role="exception"), dict(y, role="consequent")],
                       "conditional")
    plain = rb.render([x, y], "conditional")
    assert if_then != unless
    assert if_then != plain and unless != plain


def test_never_Y_is_distinguishable_from_Y(): 
    rb = _rb()
    y = {"name": "ask_clarifying_question", "kind": "act", "gloss": "g",
         "span_id": "s1"}
    assert (rb.render([dict(y, name="mustnot_ask_clarifying_question")],
                      "conditional")
            != rb.render([y], "conditional"))


def test_an_unrecognised_role_is_not_rendered_as_a_role():
    """A typo must not become an assertion about conditional structure."""
    rb = _rb()
    txt = rb.render([{"name": "x", "kind": "situation", "gloss": "g",
                      "span_id": "s1", "role": "trigger"}], "conditional")
    assert "ROLE:" not in txt
    assert "no condition" in txt


def test_an_unparseable_name_is_printed_but_not_decoded():
    rb = _rb()
    txt = rb.render([{"name": "a__b__c", "kind": "act", "gloss": "g",
                      "span_id": "s1"}], "conditional")
    assert "a__b__c" in txt
    assert "FORCE:" not in txt and "WHO:" not in txt
    assert "no polarity" in txt
