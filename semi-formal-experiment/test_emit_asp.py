"""Tests for emit_asp.py — extraction.json -> .lp -> conflicts.json."""
import json
import re

import pytest

import emit_asp
import run_conflicts


# --------------------------------------------------------------- fixtures ---

def _atom(name, kind, gloss=""):
    return {"name": name, "kind": kind,
            "dimension": "situation" if kind == "context" else "act",
            "gloss": gloss, "quote_spans": [], "status": "draft"}


def _rule(rid, modality, act, conditions, defeaters=None, locator=None, quote="q"):
    return {
        "id": rid, "modality": modality, "act": act, "conditions": conditions,
        "defeaters": defeaters or [], "tier": 1,
        "locator": locator or f"model_spec@2025-12-18 > The chain of command > L{len(rid)}",
        "quote": quote, "status": "draft",
    }


@pytest.fixture
def small():
    """A minimal extraction that does produce a conflict."""
    return {
        "section": "chain_of_command", "model": "test", "run_id": "t0",
        "atoms": [
            _atom("user_asks", "context", "the user asks for the material"),
            _atom("operator_forbids", "context", "the operator has forbidden it"),
            _atom("emergency", "context", "there is a risk to human life"),
            _atom("provide_material", "act", "provide the material"),
        ],
        "rules": [
            _rule("fa_a1", "oblige", "provide_material", ["user_asks"]),
            _rule("fa_b2", "forbid", "provide_material", ["operator_forbids"],
                  defeaters=[{"conditions": ["emergency"], "source": "emergency default"}]),
        ],
        "incompat": [],
        "exclusions": [],
        "unencoded": [],
    }


@pytest.fixture
def three_norms():
    """Hand-transcription of three norms from rules.lp.

    h1_truthful + g1_immediate conflict directly over assert_p;
    g6_autonomy conflicts with nothing (its only former partner axiom,
    incompat(respect_decision, intervene_wellbeing), was deleted from rules.lp).
    Tier is 1 here per the contract; rules.lp's tiers differ, so only the
    conflict *pairs* and *witnesses* are compared, not the tier annotations.
    """
    return {
        "section": "constitution_fragment", "model": "hand", "run_id": "rt0",
        "atoms": [
            _atom("bel_false", "context", "the model believes p is false"),
            _atom("user_prefers_p", "context", "the user wants to hear that p"),
            _atom("decision_own_purview", "context",
                  "the decision is within the user's own life and purview"),
            _atom("assert_p", "act", "sincerely assert p"),
            _atom("respect_decision", "act", "respect the user's decision"),
        ],
        "rules": [
            _rule("h1_truthful", "forbid", "assert_p", ["bel_false"],
                  locator="constitution@2026-01-20 > Being broadly ethical > Being honest > L4",
                  quote="Claude only sincerely asserts things it believes to be true"),
            _rule("g1_immediate", "oblige", "assert_p", ["user_prefers_p"],
                  locator="constitution@2026-01-20 > Being helpful > "
                          "What constitutes genuine helpfulness > L3",
                  quote="The specific outcomes they want from this particular interaction"),
            _rule("g6_autonomy", "oblige", "respect_decision", ["decision_own_purview"],
                  locator="constitution@2026-01-20 > Being helpful > "
                          "What constitutes genuine helpfulness > L6",
                  quote="the user's right to make decisions about things within "
                        "their own life and purview"),
        ],
        "incompat": [],
        "exclusions": [],
        "unencoded": [],
    }


def _pairs(report):
    return {tuple(c["pair"]) for c in report["conflicts"]}


@pytest.fixture
def epistemic():
    """The pilot's epistemic exclusion, transcribed from rules.lp:

        { ctx(bel_true); ctx(bel_false); ctx(bel_uncertain) } 1.

    plus the two norms whose conflict rules.lp witnesses with exactly one
    belief atom (h2_calibrated oblige hedge_p / g5_nowishywashy forbid hedge_p).
    """
    return {
        "section": "constitution_fragment", "model": "hand", "run_id": "ep0",
        "atoms": [
            _atom("bel_true", "context", "the model believes p is true"),
            _atom("bel_false", "context", "the model believes p is false"),
            _atom("bel_uncertain", "context", "the model is uncertain about p"),
            _atom("user_prefers_p", "context", "the user wants to hear that p"),
            _atom("caution_not_needed", "context", "hedging is not actually needed here"),
            _atom("hedge_p", "act", "hedge the response about p"),
        ],
        "rules": [
            _rule("h2_calibrated", "oblige", "hedge_p",
                  ["bel_uncertain", "user_prefers_p"]),
            _rule("g5_nowishywashy", "forbid", "hedge_p",
                  ["caution_not_needed", "user_prefers_p"]),
        ],
        "incompat": [],
        "exclusions": [{
            "atoms": ["bel_true", "bel_false", "bel_uncertain"],
            "kind": "at_most_one", "license": "logical",
            "source": "one epistemic state re p; absent when p is not at issue",
        }],
        "unencoded": [],
    }


BELIEFS = {"bel_true", "bel_false", "bel_uncertain"}


# ------------------------------------------------------------- exclusions ---

def test_at_most_one_emits_a_bounded_choice_group(epistemic):
    text = emit_asp.emit(epistemic)
    assert "{ ctx(bel_true); ctx(bel_false); ctx(bel_uncertain) } 1." in text
    # grouped atoms must NOT also get independent choice rules
    for n in BELIEFS:
        assert "{ ctx(%s) }." % n not in text
    # ungrouped context atoms keep theirs
    assert "{ ctx(user_prefers_p) }." in text
    assert "{ ctx(caution_not_needed) }." in text


def test_at_most_one_group_atom_order_and_license_comment(epistemic):
    text = emit_asp.emit(epistemic)
    line = [l for l in text.splitlines() if l.startswith("{ ctx(bel_true)")][0]
    assert "license: LOGICAL" in line
    assert "one epistemic state re p" in line


def test_witness_cannot_contain_two_atoms_from_one_group(epistemic, tmp_path):
    """(a) No answer set — hence no witness — holds two belief atoms."""
    lp = str(tmp_path / "e.lp")
    report = emit_asp.run(epistemic, lp)
    for c in report["conflicts"]:
        assert len(BELIEFS & set(c["witness"]["ctx"])) <= 1

    # stronger: forcing two of them is outright unsatisfiable
    import clingo
    for a, b in [("bel_true", "bel_false"), ("bel_false", "bel_uncertain"),
                 ("bel_true", "bel_uncertain")]:
        ctl = clingo.Control()
        ctl.load(lp)
        ctl.add("goal", [], f":- not ctx({a}). :- not ctx({b}).")
        ctl.ground([("base", []), ("goal", [])])
        assert not ctl.solve().satisfiable, f"{a}+{b} co-occur"


def test_epistemic_exclusion_reproduces_rules_lp_witness(epistemic, tmp_path):
    """(b) The h2/g5 conflict's witness carries exactly one belief atom, and it
    is the same witness rules.lp yields today."""
    expected = _rules_lp_pairs_for({"h2_calibrated", "g5_nowishywashy"})
    assert set(expected) == {("g5_nowishywashy", "h2_calibrated")}
    ref = run_conflicts.witness(expected[("g5_nowishywashy", "h2_calibrated")][0])["ctx"]

    lp = str(tmp_path / "ep.lp")
    report = emit_asp.run(epistemic, lp)
    assert _pairs(report) == {("g5_nowishywashy", "h2_calibrated")}
    got = report["conflicts"][0]["witness"]["ctx"]
    assert got == ref == ["bel_uncertain", "caution_not_needed", "user_prefers_p"]
    assert len(BELIEFS & set(got)) == 1


def test_without_the_exclusion_the_scenario_space_admits_impossible_witnesses(
        epistemic, tmp_path):
    """Control: the gap this field closes is real — dropping the exclusion lets
    an answer set assert two contradictory belief states at once."""
    import clingo
    ext = json.loads(json.dumps(epistemic))
    ext["exclusions"] = []
    lp = str(tmp_path / "noex.lp")
    emit_asp.write_lp(ext, lp)
    ctl = clingo.Control()
    ctl.load(lp)
    ctl.add("goal", [], ":- not ctx(bel_true). :- not ctx(bel_false).")
    ctl.ground([("base", []), ("goal", [])])
    assert ctl.solve().satisfiable


def test_excludes_prunes_the_constrained_pair(small, tmp_path):
    """(c) `excludes` keeps both atoms' choice rules but forbids co-occurrence,
    which removes the conflict that needed both."""
    import clingo
    lp = str(tmp_path / "x0.lp")
    assert _pairs(emit_asp.run(small, lp)) == {("fa_a1", "fa_b2")}

    small["exclusions"] = [{
        "atoms": ["user_asks", "operator_forbids"], "kind": "excludes",
        "license": "assumed", "source": "analyst judgment",
    }]
    text = emit_asp.emit(small)
    assert ":- ctx(user_asks), ctx(operator_forbids)." in text
    assert "license: ASSUMED" in text
    assert "{ ctx(user_asks) }." in text  # excludes does NOT remove choice rules

    lp2 = str(tmp_path / "x1.lp")
    emit_asp.write_lp(small, lp2)
    ctl = clingo.Control()
    ctl.load(lp2)
    ctl.ground([("base", [])])
    assert not ctl.solve().satisfiable  # the only conflict is gone
    assert emit_asp.brave_conflicts(lp2)[0] == []


def test_duplicate_group_membership_raises(epistemic):
    """(d) An atom may not belong to two at_most_one groups."""
    epistemic["exclusions"].append({
        "atoms": ["bel_false", "user_prefers_p"], "kind": "at_most_one",
        "license": "assumed", "source": "",
    })
    with pytest.raises(emit_asp.EmitError) as ei:
        emit_asp.emit(epistemic)
    assert "already belongs to another at_most_one group" in str(ei.value)
    assert "bel_false" in str(ei.value)


def test_atom_may_be_in_one_group_and_also_an_excludes(epistemic, tmp_path):
    """Overlap is only barred between at_most_one groups."""
    epistemic["exclusions"].append({
        "atoms": ["bel_false", "caution_not_needed"], "kind": "excludes",
        "license": "assumed", "source": "",
    })
    lp = str(tmp_path / "mix.lp")
    emit_asp.run(epistemic, lp)  # must not raise


def test_exclusions_field_is_mandatory(small):
    del small["exclusions"]
    with pytest.raises(emit_asp.EmitError) as ei:
        emit_asp.emit(small)
    assert "mandatory" in str(ei.value)


@pytest.mark.parametrize("ex,msg", [
    ({"atoms": ["user_asks"], "kind": "at_most_one", "license": "logical"},
     "at least 2 atoms"),
    ({"atoms": ["user_asks", "emergency", "operator_forbids"], "kind": "excludes",
      "license": "logical"}, "exactly 2 atoms"),
    ({"atoms": ["user_asks", "provide_material"], "kind": "at_most_one",
      "license": "logical"}, "not a context atom"),
    ({"atoms": ["user_asks", "nope"], "kind": "at_most_one", "license": "logical"},
     "undeclared atom"),
    ({"atoms": ["user_asks", "emergency"], "kind": "one_of", "license": "logical"},
     "bad kind"),
    ({"atoms": ["user_asks", "emergency"], "kind": "at_most_one", "license": "vibes"},
     "bad license"),
    ({"atoms": ["user_asks", "emergency"], "kind": "at_most_one", "license": "textual"},
     "textual license requires a source"),
    ({"atoms": ["user_asks", "user_asks"], "kind": "at_most_one", "license": "logical"},
     "repeats an atom"),
    ({"atoms": ["Emergency", "user_asks"], "kind": "at_most_one", "license": "logical"},
     "legal ASP constant"),
])
def test_malformed_exclusion_raises_clear_error(small, ex, msg):
    small["exclusions"] = [ex]
    with pytest.raises(emit_asp.EmitError) as ei:
        emit_asp.emit(small)
    assert msg in str(ei.value)


# ------------------------------------------------------- emission validity ---

def test_emitted_program_grounds_and_solves(small, tmp_path):
    lp = str(tmp_path / "small.lp")
    report = emit_asp.run(small, lp)
    assert _pairs(report) == {("fa_a1", "fa_b2")}


def test_tier_is_always_one(small, tmp_path):
    lp = str(tmp_path / "s.lp")
    text = emit_asp.write_lp(small, lp)
    heads = re.findall(r"^active\(([^)]*)\)", text, re.M)
    assert heads
    assert all(h.split(",")[-1].strip() == "1" for h in heads)


def test_emitted_identifiers_are_legal_asp_constants(small, tmp_path):
    text = emit_asp.emit(small)
    # strip quoted strings and comments, then check every non-variable token.
    # ASP variables start uppercase or '_'; everything else must be a legal
    # constant.
    body = re.sub(r'"(\\.|[^"\\])*"', '""', text)
    body = "\n".join(re.sub(r"%.*$", "", l) for l in body.splitlines())
    pat = re.compile(r"^[a-z][a-z0-9_]*$")
    for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body):
        if tok[0].isupper() or tok[0] == "_":
            continue  # ASP variable
        assert pat.match(tok), f"illegal identifier {tok!r}"
    # and the input's own identifiers really made it through
    assert "active(fa_a1, oblige, provide_material, 1)" in text


def test_choice_rule_per_context_atom(small, tmp_path):
    text = emit_asp.emit(small)
    chosen = set(re.findall(r"^\{ ctx\((\w+)\) \}", text, re.M))
    assert chosen == {"user_asks", "operator_forbids", "emergency"}


def test_defeater_emitted_and_guards_the_rule(small, tmp_path):
    text = emit_asp.emit(small)
    assert "defeated(fa_b2) :- ctx(emergency)." in text
    assert "not defeated(fa_b2)" in text
    # and the guard actually bites: with emergency forced true there is no conflict
    lp = str(tmp_path / "d.lp")
    with open(lp, "w") as f:
        f.write(text + "\nctx(emergency).\n")
    conflicts, _, _ = emit_asp.brave_conflicts(lp)
    assert conflicts == []


def test_incompat_facts_emitted_and_drive_indirect_conflicts(small, tmp_path):
    ext = json.loads(json.dumps(small))
    ext["atoms"].append(_atom("stay_silent", "act", "stay silent"))
    ext["rules"] = [
        _rule("fa_a1", "oblige", "provide_material", ["user_asks"]),
        _rule("fa_c3", "oblige", "stay_silent", ["operator_forbids"]),
    ]
    ext["incompat"] = [{"acts": ["provide_material", "stay_silent"],
                        "license": "logical", "source": "by definition"}]
    text = emit_asp.emit(ext)
    assert "incompat(provide_material, stay_silent)." in text
    lp = str(tmp_path / "i.lp")
    report = emit_asp.run(ext, lp)
    assert _pairs(report) == {("fa_a1", "fa_c3")}


# ------------------------------------------------------ provenance inertness ---

def test_provenance_facts_are_emitted(small):
    text = emit_asp.emit(small)
    assert re.search(r"^source\(fa_a1, ", text, re.M)
    assert re.search(r"^locator\(fa_a1, ", text, re.M)
    assert "#show source/2." in text
    assert "#show locator/4." in text


def test_bracketed_locator_id_survives_asp_string_escaping(small, tmp_path):
    """inventory locators now end in `[fa_xxxx]`. Brackets are ordinary
    characters inside an ASP quoted string, but pin the round-trip: the
    locator that comes back out of the solver must be byte-identical."""
    import inventory
    loc = inventory.load_section()[0]["locator"]
    assert loc.endswith("]") and "[fa_" in loc
    small["rules"][0]["locator"] = loc

    lp = str(tmp_path / "b.lp")
    emit_asp.write_lp(small, lp)
    _conf, sources, locators = emit_asp.brave_conflicts(lp)
    assert locators["fa_a1"][0] == loc
    # source/2 shows the section only: no line number, no bracketed id
    assert sources["fa_a1"] == "The chain of command"

    # and it is still inert
    bare = str(tmp_path / "b2.lp")
    with open(bare, "w") as f:
        f.write(emit_asp.strip_provenance(open(lp).read()))
    assert emit_asp.brave_conflicts(lp)[0] == emit_asp.brave_conflicts(bare)[0]


def test_provenance_is_inert(small, tmp_path):
    """Deleting every source/2 and locator/4 fact (selected by predicate name)
    must leave the conflict set bit-identical."""
    full = str(tmp_path / "full.lp")
    bare = str(tmp_path / "bare.lp")
    text = emit_asp.write_lp(small, full)
    stripped = emit_asp.strip_provenance(text)
    with open(bare, "w") as f:
        f.write(stripped)

    # the stripping really removed something, by predicate name
    def preds(t):
        return re.findall(r"^(\w+)\(", t, re.M)
    assert "source" in preds(text) and "locator" in preds(text)
    assert "source" not in preds(stripped) and "locator" not in preds(stripped)

    a, _, _ = emit_asp.brave_conflicts(full)
    b, _, _ = emit_asp.brave_conflicts(bare)
    assert a == b
    assert emit_asp.conflicts_report(small, full)["conflicts"] == \
           emit_asp.conflicts_report(small, bare)["conflicts"]


def test_provenance_is_inert_on_three_norms(three_norms, tmp_path):
    full = str(tmp_path / "f.lp")
    bare = str(tmp_path / "b.lp")
    text = emit_asp.write_lp(three_norms, full)
    with open(bare, "w") as f:
        f.write(emit_asp.strip_provenance(text))
    assert emit_asp.brave_conflicts(full)[0] == emit_asp.brave_conflicts(bare)[0]


# ------------------------------------------------------------- round trip ---

def _rules_lp_pairs_for(norm_ids):
    """What run_conflicts.py reports today for the given norms, restricted to
    pairs entirely inside that set."""
    conflicts, _, _ = run_conflicts.brave_conflicts()
    out = {}
    for c in conflicts:
        inner = c[len("conflict(") : -1]
        n1, n2, act, _t1, _t2 = [x.strip() for x in inner.split(",")]
        if n1 in norm_ids and n2 in norm_ids:
            out[tuple(sorted((n1, n2)))] = (c, act)
    return out


def test_round_trip_pairs_match_rules_lp(three_norms, tmp_path):
    ids = {r["id"] for r in three_norms["rules"]}
    expected = _rules_lp_pairs_for(ids)
    assert set(expected) == {("g1_immediate", "h1_truthful")}, expected
    # g6_autonomy participates in nothing today
    assert not any("g6_autonomy" in p for p in expected)

    lp = str(tmp_path / "rt.lp")
    report = emit_asp.run(three_norms, lp)
    assert _pairs(report) == set(expected)


def test_round_trip_witness_matches_rules_lp(three_norms, tmp_path):
    expected = _rules_lp_pairs_for({r["id"] for r in three_norms["rules"]})
    atom, _act = expected[("g1_immediate", "h1_truthful")]
    ref = run_conflicts.witness(atom)["ctx"]

    lp = str(tmp_path / "rt2.lp")
    report = emit_asp.run(three_norms, lp)
    got = report["conflicts"][0]["witness"]["ctx"]
    assert got == ref == ["bel_false", "user_prefers_p"]


def test_witness_prose_is_mechanical_and_mentions_the_witness(three_norms, tmp_path):
    lp = str(tmp_path / "rt3.lp")
    report = emit_asp.run(three_norms, lp)
    prose = report["conflicts"][0]["witness_prose"]
    assert "the model believes p is false" in prose
    assert "the user wants to hear that p" in prose
    assert "g1_immediate" in prose and "h1_truthful" in prose
    assert prose.endswith(".")
    # deterministic
    assert emit_asp.conflicts_report(three_norms, lp)["conflicts"][0]["witness_prose"] \
           == prose


def test_conflicts_json_shape(three_norms, tmp_path):
    lp = str(tmp_path / "s.lp")
    out = str(tmp_path / "conflicts.json")
    emit_asp.run(three_norms, lp, out)
    with open(out) as f:
        report = json.load(f)
    # contract §3 keys, plus the additive provenance block
    assert {"source", "model", "run_id", "conflicts"} <= set(report)
    assert set(report) - {"source", "model", "run_id", "conflicts"} == \
           {"provenance", "rejected"}
    assert report["source"] == "tool"
    for c in report["conflicts"]:
        assert set(c) == {"pair", "witness", "witness_prose", "note"}
        assert c["pair"] == sorted(c["pair"])
        assert isinstance(c["witness"]["ctx"], list)
        assert isinstance(c["witness_prose"], str) and c["witness_prose"]


# --------------------------------------------------------- skip-invalid ---
# The live `together-cheap` extraction (34 atoms / 24 rules) aborted on one
# type-error rule, costing all conflict analysis. Weak-model extractions are
# the population being measured, so validation must be able to degrade.

@pytest.fixture
def one_bad_rule(small):
    """The live defect class: a rule whose `act` names a context atom.
    (EmitError: rule fa_ag8e: 'high_risk_activity' is a 'context' atom,
    expected 'act')"""
    small["atoms"].append(_atom("high_risk_activity", "context",
                                "the activity is high risk"))
    small["rules"].append(
        _rule("fa_ag8e", "oblige", "high_risk_activity", ["user_asks"]))
    return small


def test_type_error_rule_still_aborts_without_the_flag(one_bad_rule):
    """(3) fail-fast stays the default — a clean extraction is verified strictly."""
    with pytest.raises(emit_asp.EmitError) as ei:
        emit_asp.emit(one_bad_rule)
    assert "fa_ag8e" in str(ei.value)
    assert "'high_risk_activity' is a 'context' atom, expected 'act'" in str(ei.value)


def test_skip_invalid_emits_and_records_the_rejection(one_bad_rule, tmp_path):
    """(1)+(2) skip and record; the .lp still solves; counts are visible."""
    lp = str(tmp_path / "si.lp")
    out = str(tmp_path / "c.json")
    rules_in = len(one_bad_rule["rules"])
    report = emit_asp.run(one_bad_rule, lp, out, skip_invalid=True)

    p = report["provenance"]
    assert p["rules_in"] == rules_in == 3
    assert p["rules_emitted"] == rules_in - 1
    assert p["rules_rejected"] == 1
    assert p["skip_invalid"] is True
    assert p["rejection_reasons"] == {
        "rule uses a non-act atom where an act atom is required": 1,
        "atom orphaned by a dropped rule": 1,  # high_risk_activity cascades out
    }

    # the same specific message is preserved verbatim
    bad = [r for r in report["rejected"] if r["id"] == "fa_ag8e"]
    assert len(bad) == 1
    assert "'high_risk_activity' is a 'context' atom, expected 'act'" in bad[0]["reason"]
    assert bad[0]["cascade"] is False

    # ...and the program still solves, giving the surviving conflict
    assert _pairs(report) == {("fa_a1", "fa_b2")}
    assert emit_asp.brave_conflicts(lp)[0]
    with open(out) as f:
        assert json.load(f)["provenance"]["rules_emitted"] == rules_in - 1


def test_skip_invalid_lp_never_references_a_removed_atom(one_bad_rule, tmp_path):
    """(4) no dangling reference to anything that was dropped."""
    lp = str(tmp_path / "si2.lp")
    emit_asp.run(one_bad_rule, lp, skip_invalid=True)
    text = open(lp).read()
    body = "\n".join(re.sub(r"%.*$", "", l) for l in text.splitlines())
    assert "high_risk_activity" not in body
    assert "fa_ag8e" not in body
    # but the drop is documented in the header comments
    assert "high_risk_activity" in text
    assert "PARTIAL PROGRAM" in text


def test_orphaned_atom_is_counted_as_a_cascade_drop(one_bad_rule, tmp_path):
    report = emit_asp.run(one_bad_rule, str(tmp_path / "c.lp"), skip_invalid=True)
    orphan = [r for r in report["rejected"] if r["id"] == "high_risk_activity"]
    assert len(orphan) == 1
    assert orphan[0]["cascade"] is True
    assert orphan[0]["kind"] == "atom"
    assert "orphaned" in orphan[0]["reason"]
    assert report["provenance"]["cascade_drops"] == 1
    assert report["provenance"]["atoms_emitted"] == report["provenance"]["atoms_in"] - 1


def test_incompat_orphaned_by_a_dropped_rule_is_dropped_and_counted(small, tmp_path):
    """An incompat naming an act no surviving rule uses can never fire; it must
    not survive into the .lp, because its atom is gone."""
    small["atoms"].append(_atom("stay_silent", "act", "stay silent"))
    small["rules"].append(
        _rule("fa_c3", "oblige", "stay_silent", ["operator_forbids"], quote="q"))
    small["incompat"] = [{"acts": ["provide_material", "stay_silent"],
                          "license": "logical", "source": "exclusive"}]
    # break the only rule that uses stay_silent
    small["rules"][-1]["modality"] = "ought"

    lp = str(tmp_path / "io.lp")
    report = emit_asp.run(small, lp, skip_invalid=True)
    p = report["provenance"]
    assert p["rules_rejected"] == 1
    assert p["incompat_in"] == 1 and p["incompat_emitted"] == 0
    reasons = p["rejection_reasons"]
    assert reasons["rule has a bad modality"] == 1
    assert reasons["incompat orphaned by a dropped rule"] == 1
    assert reasons["atom orphaned by a dropped rule"] == 1
    body = "\n".join(re.sub(r"%.*$", "", l) for l in open(lp).read().splitlines())
    assert "stay_silent" not in body
    assert _pairs(report) == {("fa_a1", "fa_b2")}


def test_exclusion_shrinks_to_surviving_atoms(epistemic, tmp_path):
    """An at_most_one group loses an atom no surviving rule uses; the projected
    constraint over the survivors is still emitted (not silently dropped)."""
    # bel_false gets a surviving user; bel_true's only user is rejected
    epistemic["rules"].append(
        _rule("h1_truthful", "oblige", "hedge_p", ["bel_false"]))
    bad = _rule("fa_bad", "oblige", "hedge_p", ["bel_true"])
    bad["modality"] = "ought"
    epistemic["rules"].append(bad)
    lp = str(tmp_path / "ex.lp")
    report = emit_asp.run(epistemic, lp, skip_invalid=True)
    text = open(lp).read()
    # bel_true is used by no rule -> orphaned; the group keeps the other two
    assert "{ ctx(bel_false); ctx(bel_uncertain) } 1." in text
    body = "\n".join(re.sub(r"%.*$", "", l) for l in text.splitlines())
    assert "bel_true" not in body
    assert report["provenance"]["exclusions_emitted"] == 1
    assert report["provenance"]["rejection_reasons"] == {
        "atom orphaned by a dropped rule": 1,
        "rule has a bad modality": 1,
    }
    # the projected constraint still bites: no witness holds both beliefs
    for c in report["conflicts"]:
        assert len({"bel_false", "bel_uncertain"} & set(c["witness"]["ctx"])) <= 1


def test_exclusion_group_dropped_when_only_one_atom_survives(epistemic, tmp_path):
    """Both other belief atoms cascade out, so the group shrinks below 2 and is
    dropped — never emitted as a degenerate `{ ctx(x) } 1.`"""
    for i, atom in enumerate(("bel_true", "bel_false")):
        bad = _rule(f"fa_bad{i}", "oblige", "hedge_p", [atom])
        bad["modality"] = "ought"
        epistemic["rules"].append(bad)
    lp = str(tmp_path / "ex1.lp")
    report = emit_asp.run(epistemic, lp, skip_invalid=True)
    p = report["provenance"]
    assert p["exclusions_in"] == 1 and p["exclusions_emitted"] == 0
    assert p["rejection_reasons"]["exclusion orphaned by a dropped rule"] == 1
    assert "} 1." not in open(lp).read()
    # the surviving atom keeps an ordinary independent choice rule
    assert "{ ctx(bel_uncertain) }." in open(lp).read()
    assert _pairs(report) == {("g5_nowishywashy", "h2_calibrated")}
    assert report["conflicts"][0]["witness"]["ctx"] == \
        ["bel_uncertain", "caution_not_needed", "user_prefers_p"]


def test_atoms_unused_before_any_rejection_are_left_alone(small, tmp_path):
    """The cascade is scoped to atoms orphaned *by a dropped rule*. An atom that
    was already unused is pre-existing extraction noise, equally inert, and must
    not be silently re-scoped by an unrelated flag — otherwise `--skip-invalid`
    would change the program on a clean extraction."""
    small["rules"] = [_rule("fa_a1", "oblige", "provide_material", ["user_asks"]),
                      _rule("fa_b2", "forbid", "provide_material", ["operator_forbids"])]
    small["exclusions"] = [{"atoms": ["user_asks", "emergency"],
                            "kind": "at_most_one", "license": "logical",
                            "source": "illustrative"}]
    # `emergency` is used by no rule, but no rule was rejected either
    assert emit_asp.emit(small, skip_invalid=True) == emit_asp.emit(small)
    report = emit_asp.run(small, str(tmp_path / "e2.lp"), skip_invalid=True)
    p = report["provenance"]
    assert p["exclusions_in"] == p["exclusions_emitted"] == 1
    assert p["atoms_in"] == p["atoms_emitted"]
    assert p["cascade_drops"] == 0


def test_skip_invalid_does_not_change_a_clean_extraction(three_norms, tmp_path):
    """The flag must be a no-op when nothing is wrong."""
    a = emit_asp.emit(three_norms, skip_invalid=False)
    b = emit_asp.emit(three_norms, skip_invalid=True)
    assert a == b
    r = emit_asp.run(three_norms, str(tmp_path / "cl.lp"), skip_invalid=True)
    p = r["provenance"]
    assert p["rules_rejected"] == 0 and p["cascade_drops"] == 0
    assert p["rejection_reasons"] == {}
    assert r["rejected"] == []


def test_provenance_present_even_on_the_fail_fast_path(small, tmp_path):
    report = emit_asp.run(small, str(tmp_path / "ff.lp"))
    p = report["provenance"]
    assert p["skip_invalid"] is False
    assert p["rules_in"] == p["rules_emitted"] == 2
    assert p["rules_rejected"] == 0


def test_whole_document_defects_abort_even_with_skip_invalid(small):
    """There is nothing to skip *to* if the containers themselves are wrong."""
    for mutate in (lambda e: e.update(rules="nope"),
                   lambda e: e.pop("exclusions")):
        ext = json.loads(json.dumps(small))
        mutate(ext)
        with pytest.raises(emit_asp.EmitError):
            emit_asp.emit(ext, skip_invalid=True)


def test_cli_skip_invalid_flag(one_bad_rule, tmp_path, capsys):
    src = tmp_path / "extraction.json"
    src.write_text(json.dumps(one_bad_rule))
    out = tmp_path / "conflicts.json"
    lp = tmp_path / "cli.lp"
    with pytest.raises(emit_asp.EmitError):
        emit_asp.main([str(src), "--lp", str(lp), "--out", str(out)])
    report = emit_asp.main([str(src), "--lp", str(lp), "--out", str(out),
                            "--skip-invalid"])
    assert report["provenance"]["rules_emitted"] == 2
    printed = capsys.readouterr().out
    assert "2/3 emitted" in printed
    assert "rule uses a non-act atom where an act atom is required" in printed


# ---------------------------------------------------------- malformed input ---

@pytest.mark.parametrize("mutate,msg", [
    (lambda e: e["rules"][0].update(id="8ep1"), "legal ASP constant"),
    (lambda e: e["atoms"][0].update(name="Operator"), "legal ASP constant"),
    (lambda e: e["rules"][0].update(modality="ought"), "bad modality"),
    (lambda e: e["rules"][0].update(act="no_such_act"), "undeclared atom"),
    (lambda e: e["rules"][0].update(conditions=["nope"]), "undeclared atom"),
    (lambda e: e["rules"][0].update(act="user_asks"), "expected 'act'"),
    (lambda e: e["rules"][0].update(conditions=["provide_material"]), "expected 'context'"),
    (lambda e: e["rules"][0].update(tier=3), "tier must be 1"),
    (lambda e: e["rules"].append(dict(e["rules"][0])), "duplicate rule id"),
    (lambda e: e.update(incompat=[{"acts": ["provide_material"], "license": "logical"}]),
     "exactly 2 acts"),
    (lambda e: e.update(incompat=[{"acts": ["provide_material", "user_asks"],
                                   "license": "logical"}]), "not an act atom"),
    (lambda e: e.update(incompat=[{"acts": ["provide_material", "provide_material"],
                                   "license": "textual"}]), "requires a source"),
    (lambda e: e["rules"][0].update(defeaters=[{"conditions": []}]), "no conditions"),
    (lambda e: e.update(rules="nope"), "must be a list"),
])
def test_malformed_input_raises_clear_error(small, mutate, msg):
    mutate(small)
    with pytest.raises(emit_asp.EmitError) as ei:
        emit_asp.emit(small)
    assert msg in str(ei.value)


def test_valid_input_does_not_raise(small):
    emit_asp.emit(small)
