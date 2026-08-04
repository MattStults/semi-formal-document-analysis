"""The QUERY side of the rung-1.5 notation: polarity + an ORDERED principal chain.

WHY THIS FILE EXISTS
--------------------
`structural.py` ships four notation-reading operators. Three of them
(`directive_atom`, `role_aligned`, `patient_aligned`) can read a clause-side
rung-1.5 pass; `polarity_consistent` cannot, "because an unpolarised query atom
contradicts nothing". That is a QUERY-side hole, and `behavior_atoms.py` is the
query side. These tests pin the extension that closes it.

THE THING MOST EASILY GOT WRONG. `behavior_atoms.py` is deliberately a
CONSTRAINED SELECTION over the clause vocabulary — the model picks identifiers
off a closed list and never authors the string that has to match. Adding
polarity must not turn that into free generation. So the tests below check, in
order of how much they matter:

  1. the STEM is still selected from the closed vocabulary, and the notated name
     is CONSTRUCTED by us from validated parts, never copied from the model;
  2. the principal chain is ORDERED and is never sorted, de-duplicated into a
     set, or otherwise flattened — a third party who acts is not a third party
     who is acted upon;
  3. `stem_of` remains the identity on every atom name in every SHIPPED
     artifact, so the join that already works keeps working. Tested against the
     real artifacts on disk, not fixtures.

`grammar.py` is a peer agent's file and may not exist yet. It is imported INSIDE
each test rather than at module scope so its absence is a red test rather than a
collection error that aborts the whole suite (see conftest.py's docstring).
"""
import json
import os

import pytest

import behavior_atoms as B

HERE = os.path.dirname(os.path.abspath(__file__))


def G():
    """The notation contract. A peer agent's file; RED until it lands."""
    import grammar
    return grammar


# ------------------------------------------------------------------ fixtures

VOCAB = [
    {"name": "user_request_ambiguous", "kind": "situation",
     "gloss": "the user's request admits more than one reading", "n_clauses": 9},
    {"name": "clarifying_question", "kind": "act",
     "gloss": "the assistant asks the user what they meant", "n_clauses": 4},
    {"name": "refuse_request", "kind": "act",
     "gloss": "the assistant declines to do what was asked", "n_clauses": 21},
    {"name": "cause_harm", "kind": "act",
     "gloss": "the assistant brings about a harm", "n_clauses": 12},
    {"name": "third_party", "kind": "entity",
     "gloss": "someone outside the conversation", "n_clauses": 40},
    {"name": "safety", "kind": "value",
     "gloss": "freedom from harm", "n_clauses": 30},
]

BEHAVIOUR = {"slug": "harm-avoidance-to-third-parties",
             "name": "Harm avoidance to third parties",
             "definition": "The model should weigh the potential harm to those "
                           "outside the conversation."}

#: Every behaviour-atom artifact this repo has ever shipped. Backward
#: compatibility is a claim about THESE files, so it is tested on THESE files.
SHIPPED = (["behavior_atoms_b8.json", "behavior_atoms.json"]
           + [f"behavior_atoms_draw{i}.json" for i in range(1, 5)]
           + [f"behavior_atoms_v2_draw{i}.json" for i in range(5)])


def shipped_paths():
    return [os.path.join(HERE, p) for p in SHIPPED
            if os.path.exists(os.path.join(HERE, p))]


def atom_names(path):
    with open(path, encoding="utf-8") as f:
        art = json.load(f)
    out = []
    for slug, entry in art.items():
        if slug.startswith("_") or slug == "provenance":
            continue
        for a in (entry.get("atoms") or []):
            if a.get("name"):
                out.append(a["name"])
    return out


def reply(selected=(), new=()):
    return {"text": json.dumps({"selected": list(selected), "new": list(new)}),
            "finish_reason": "stop"}


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = 0
        self.prompts = []

    def complete_envelope(self, system, user):
        self.prompts.append((system, user))
        r = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return r


def fail_log(tmp_path):
    import extract_section as ex
    return ex.FailureLog(str(tmp_path / "fail.jsonl"), run_id="t", model="m")


def act(name, polarity=None, principals=(), weight=3):
    a = {"name": name, "kind": "act", "weight": weight, "source": "definition"}
    if polarity is not None:
        a["polarity"] = polarity
    if principals:
        a["principals"] = list(principals)
    return a


# ------------------------------------------- the notation is not re-declared

def test_the_notation_is_imported_from_grammar_and_never_re_declared():
    """A second copy of the prefix list is how two modules quietly disagree.

    `structural.py` re-declares it deliberately and pins it with a test; the
    query side has no such excuse and the contract says import it.
    """
    import re
    src = open(os.path.join(HERE, "behavior_atoms.py"), encoding="utf-8").read()
    for const in ("POLARITY_PREFIXES", "PRINCIPALS", "PRINCIPAL_SEP"):
        assert not re.search(rf"^{const}\s*=", src, re.M), (
            f"behavior_atoms.py defines its own {const}; the notation must "
            "come from grammar.py")
    assert "import grammar" in src


def test_the_closed_enums_are_exactly_grammars():
    g = G()
    assert B.polarities() == tuple(p[:-1] for p in g.POLARITY_PREFIXES)
    assert B.principal_names() == tuple(g.PRINCIPALS)


def test_missing_grammar_is_an_explicit_refusal_not_a_silent_downgrade():
    """If the notation module is absent, the polarised path must REFUSE.

    Falling back to an unpolarised run would produce an artifact that looks
    right and carries none of the signal — the exact failure this module's
    docstring calls "the artifact looks full and matches nothing".
    """
    assert issubclass(B.NotationUnavailable, Exception)


# ---------------------------------------- selection stays selection

def test_a_decorated_name_keeps_the_selected_stem():
    g = G()
    name, err = B.decorate("cause_harm", "mustnot", ["model", "third_party"])
    assert err is None
    assert name == "mustnot_cause_harm__model_third_party"
    assert g.stem_of(name) == "cause_harm"
    p = g.parse_name(name)
    assert p["error"] is None
    assert p["polarity"] == "mustnot"
    assert tuple(p["principals"]) == ("model", "third_party")


def test_the_notated_name_is_constructed_by_us_not_copied_from_the_model(tmp_path):
    """FREE-GENERATION MUTANT. If the emitted name is whatever string the model
    wrote, a model that writes its own notation bypasses the closed vocabulary
    entirely and the query stops being a selection.
    """
    G()
    obj = {"selected": [act("mustnot_cause_harm__model_third_party")], "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail_log(tmp_path),
                                      notation=True)
    assert [a["name"] for a in atoms] == [], (
        "a pre-notated name is not a vocabulary selection and must not be "
        "accepted as one")
    assert stats["rejections"]["unknown_atom"] == 1


def test_decoration_rides_on_closed_enum_fields_not_on_the_name(tmp_path):
    G()
    obj = {"selected": [act("cause_harm", "mustnot", ["model", "third_party"])],
           "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail_log(tmp_path),
                                      notation=True)
    assert len(atoms) == 1
    a = atoms[0]
    assert a["stem"] == "cause_harm"
    assert a["name"] == "mustnot_cause_harm__model_third_party"
    assert a["polarity"] == "mustnot"
    assert a["principals"] == ["model", "third_party"]
    assert stats["notation"]["decorated"] == 1


def test_a_polarity_outside_the_reserved_set_is_refused_and_counted(tmp_path):
    G()
    obj = {"selected": [act("cause_harm", "ought", ["model", "third_party"])],
           "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail_log(tmp_path),
                                      notation=True)
    assert len(atoms) == 1, "the atom survives; only its decoration is refused"
    assert atoms[0]["polarity"] is None
    assert atoms[0]["name"] == "cause_harm__model_third_party"
    assert stats["notation"]["bad_polarity"] == 1


def test_a_principal_outside_the_closed_list_is_refused_and_counted(tmp_path):
    G()
    obj = {"selected": [act("cause_harm", "mustnot", ["model", "bystander"])],
           "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail_log(tmp_path),
                                      notation=True)
    assert len(atoms) == 1
    assert atoms[0]["principals"] == []
    assert atoms[0]["name"] == "mustnot_cause_harm"
    assert stats["notation"]["bad_principal"] == 1


def test_a_chain_longer_than_the_declared_maximum_is_refused(tmp_path):
    G()
    chain = ["model", "user", "operator", "third_party"]
    assert len(chain) > B.MAX_PRINCIPALS
    obj = {"selected": [act("cause_harm", "mustnot", chain)], "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail_log(tmp_path),
                                      notation=True)
    assert atoms[0]["principals"] == []
    assert stats["notation"]["bad_principal"] == 1


def test_decoration_is_confined_to_the_act_slot(tmp_path):
    """Polarity is deontic force ON AN ACT and principals are the parties TO an
    act. A polarised `value` atom is a category error, and silently allowing it
    would put unparseable names in the query."""
    G()
    raw = {"name": "safety", "kind": "value", "weight": 3,
           "source": "definition", "polarity": "must",
           "principals": ["model", "third_party"]}
    atoms, stats = B.verify_selection({"selected": [raw], "new": []}, VOCAB,
                                      fail_log(tmp_path), notation=True)
    assert atoms[0]["name"] == "safety"
    assert atoms[0]["polarity"] is None
    assert atoms[0]["principals"] == []
    assert stats["notation"]["non_act_decoration"] == 1


def test_a_decoration_that_does_not_round_trip_falls_back_to_the_bare_stem():
    """The construction is only trusted because it is VERIFIED against the
    peer's parser. Anything that does not parse back to exactly what we put in
    degrades to the undecorated selection — never to a dropped atom, which
    would be a silent recall cap."""
    G()
    name, err = B.decorate("cause_harm", "must", ["model", "model"])
    assert err is not None
    assert name == "cause_harm"


def test_a_stem_that_collides_with_the_notation_is_caught_by_the_round_trip():
    """The round trip is the only thing standing between a legal-looking name
    and a name that means something else.

    Two collisions the field checks cannot see, both of which pass every
    enum test and then parse back to the wrong thing:
      * a vocabulary name that already begins with a reserved prefix — the
        prefixes are reserved against the 361 shipped names, but this module
        must not depend on a property of one artifact;
      * a vocabulary name containing the principal separator.
    Caught here, the atom degrades to its bare selected name. Uncaught, the
    join silently keys on a stem nobody selected.
    """
    g = G()
    name, err = B.decorate("may_refuse", None, [])
    assert g.parse_name("may_refuse")["stem"] == "refuse"
    assert err is not None, "a stem that re-parses as a different stem"
    assert name == "may_refuse"

    name, err = B.decorate("weird__stem", "must", ["model"])
    assert err is not None
    assert name == "weird__stem"


# ------------------------------------------------ ORDER carries the meaning

def test_the_principal_chain_is_ordered_and_never_sorted(tmp_path):
    """ORDER MUTANT. `model_third_party` is a third party who is HARMED;
    `third_party_model` is a third party who HARMS. Sorting, or de-duplicating
    the chain through a set, collapses those into one atom."""
    G()
    harmed, err1 = B.decorate("cause_harm", "mustnot", ["model", "third_party"])
    harming, err2 = B.decorate("cause_harm", "mustnot", ["third_party", "model"])
    assert err1 is None and err2 is None
    assert harmed != harming
    assert harmed == "mustnot_cause_harm__model_third_party"
    assert harming == "mustnot_cause_harm__third_party_model"


def test_actor_and_patient_are_recoverable_from_the_chain():
    G()
    a = {"name": "mustnot_cause_harm__model_third_party",
         "principals": ["model", "third_party"]}
    b = {"name": "mustnot_cause_harm__third_party_model",
         "principals": ["third_party", "model"]}
    assert B.actor_of(a) == "model"
    assert B.patients_of(a) == ("third_party",)
    assert B.actor_of(b) == "third_party"
    assert B.patients_of(b) == ("model",)


def test_swapping_actor_and_patient_changes_the_emitted_query(tmp_path):
    G()
    one = B.verify_selection(
        {"selected": [act("cause_harm", "mustnot", ["model", "third_party"])]},
        VOCAB, fail_log(tmp_path), notation=True)[0]
    two = B.verify_selection(
        {"selected": [act("cause_harm", "mustnot", ["third_party", "model"])]},
        VOCAB, fail_log(tmp_path), notation=True)[0]
    assert one[0]["name"] != two[0]["name"]
    assert B.patients_of(one[0]) != B.patients_of(two[0])


def test_the_role_signature_of_a_query_is_ordered(tmp_path):
    G()
    atoms = B.verify_selection(
        {"selected": [act("cause_harm", "mustnot", ["model", "third_party"]),
                      act("refuse_request", "may", ["model", "user"])]},
        VOCAB, fail_log(tmp_path), notation=True)[0]
    sig = B.role_signature(atoms)
    assert sig["actors"] == ("model",)
    assert sig["patients"] == ("third_party", "user")


# ------------------------------- backward compatibility, on the REAL artifacts

def test_stem_of_is_the_identity_on_every_shipped_query_atom_name():
    g = G()
    paths = shipped_paths()
    assert len(paths) >= 6, f"expected the shipped artifacts on disk, got {paths}"
    n = 0
    for p in paths:
        for name in atom_names(p):
            n += 1
            assert g.stem_of(name) == name, (
                f"{name!r} in {os.path.basename(p)} is not its own stem — the "
                "join that already works would stop working")
            assert g.parse_name(name)["error"] is None
    assert n > 300, f"only {n} shipped names checked"


def test_shipped_artifacts_still_load_and_still_join():
    """BACKWARD-COMPAT MUTANT. The artifacts on disk are unpolarised and every
    consumer of them must be unaffected."""
    import relevance as R
    for p in shipped_paths():
        loaded = R.load_behaviour_atoms(p)
        assert loaded, f"{p} no longer loads"
        names = [a["name"] for atoms in loaded.values() for a in atoms]
        assert names
        with open(p, encoding="utf-8") as f:
            prov = json.load(f).get("provenance") or {}
        recorded = (prov.get("alignment") or {}).get("in_vocabulary_rate")
        # Each artifact is measured against the vocabulary IT was built on;
        # `behavior_atoms.json` predates annotations_b8.json.
        voc = {a["name"] for a in B.load_vocabulary(
            prov.get("annotations") or "annotations_b8.json")}
        assert voc, p
        if recorded is None:
            continue
        hit = sum(1 for x in names if x in voc) / len(names)
        assert abs(hit - recorded) < 0.02, (
            f"{os.path.basename(p)}: join rate moved {recorded} -> {hit:.4f}")


def test_an_unnotated_run_emits_exactly_the_shipped_atom_shape(tmp_path):
    art = B.run(FakeClient(reply([act("refuse_request")])), [BEHAVIOUR], VOCAB,
                out_dir=str(tmp_path))
    a = art[BEHAVIOUR["slug"]]["atoms"][0]
    assert set(a) == {"name", "kind", "gloss", "weight", "source", "new"}, (
        "an unnotated run must produce byte-identical artifacts to the shipped "
        f"ones; got extra keys {sorted(set(a) - {'name', 'kind', 'gloss', 'weight', 'source', 'new'})}")
    assert art["provenance"].get("notation", {}).get("enabled") is False


def test_the_stem_view_restores_an_unnotated_artifact(tmp_path):
    """The bridge for every consumer that predates the notation.

    `relevance.py` matches query atoms to clause atoms by EXACT name, with no
    stem fallback, so a polarised artifact handed to it would silently score a
    dead atom channel. `stem_view` is what makes that a non-event.
    """
    import relevance as R
    G()
    art = B.run(FakeClient(reply([act("cause_harm", "mustnot",
                                      ["model", "third_party"])])),
                [BEHAVIOUR], VOCAB, out_dir=str(tmp_path), notation=True)
    polarised = R.load_behaviour_atoms(art)
    names = [a["name"] for v in polarised.values() for a in v]
    assert names == ["mustnot_cause_harm__model_third_party"]

    view = B.stem_view(art)
    plain = R.load_behaviour_atoms(view)
    stems = [a["name"] for v in plain.values() for a in v]
    assert stems == ["cause_harm"]
    voc = {a["name"] for a in VOCAB}
    assert all(s in voc for s in stems)
    for v in view.values():
        if isinstance(v, dict) and isinstance(v.get("atoms"), list):
            for a in v["atoms"]:
                assert "polarity" not in a and "principals" not in a


def test_a_polarised_query_atom_carries_polarity_where_structural_reads_it(tmp_path):
    """The point of the whole exercise: `polarity_consistent` is inert because
    `parse_atom_name(query_atom)["polarity"]` is None for every query atom that
    exists today. After this pass it is not None."""
    structural = pytest.importorskip("structural")
    G()
    art = B.run(FakeClient(reply([act("cause_harm", "mustnot",
                                      ["model", "third_party"])])),
                [BEHAVIOUR], VOCAB, out_dir=str(tmp_path), notation=True)
    queries = structural.load_queries(art)
    q = queries[BEHAVIOUR["slug"]]
    polarities = [structural.parse_atom_name(a["name"])["polarity"]
                  for a in q.atoms]
    assert "mustnot" in polarities
    assert all(structural.parse_atom_name(a["name"])["error"] is None
               for a in q.atoms)


def test_shipped_query_atoms_are_unpolarised_which_is_why_the_operator_is_inert():
    """The premise of this whole file, asserted rather than assumed."""
    structural = pytest.importorskip("structural")
    for p in shipped_paths():
        for name in atom_names(p):
            assert structural.parse_atom_name(name)["polarity"] is None


# ---------------------------------------------------------------- the prompt

def test_the_notation_prompt_shows_both_closed_enums_and_the_vocabulary():
    G()
    system, user = B.render_prompt(BEHAVIOUR, VOCAB, notation=True)
    blob = system + user
    for p in B.polarities():
        assert p in blob
    for p in B.principal_names():
        assert p in blob
    assert "CLAUSE VOCABULARY" in blob, "selection must survive the extension"
    assert "refuse_request" in blob


def test_the_unnotated_prompt_is_unchanged_by_this_work():
    system, user = B.render_prompt(BEHAVIOUR, VOCAB)
    assert "polarity" not in (system + user).lower()
    assert "principal" not in (system + user).lower()


def test_the_notation_prompt_contains_no_labelled_example():
    """INVARIANT 9. Format demonstrations are allowed; behaviour->passage
    judgements are not, and a demonstration lifted from either spec is a
    channel from someone who has read the panel."""
    G()
    system, user = B.render_prompt(BEHAVIOUR, VOCAB, notation=True)
    blob = system + user
    for banned in ("relevant passage", "gold", "judge", "panel", "MCC",
                   "score >=", "labelled example"):
        assert banned.lower() not in blob.lower(), f"{banned!r} in the prompt"
    demos = B.notation_demonstrations()
    assert demos, "the notation prompt demonstrates nothing"
    for spec in ("modelspec_clauses.json", "constitution_clauses.json"):
        path = os.path.join(HERE, spec)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        for demo in demos:
            assert demo not in text, (
                f"demonstration {demo!r} is a string of {spec}")


# -------------------------------------------------------- dry run and cost

def test_dry_run_makes_no_call_in_notation_mode(tmp_path, monkeypatch):
    G()
    import annotate
    monkeypatch.setattr(annotate, "provider_config",
                        lambda *a, **k: annotate.provider_config("luna"))
    art = B.run(FakeClient({"text": None, "finish_reason": None}), [BEHAVIOUR],
                VOCAB, out_dir=str(tmp_path), notation=True)
    assert art["provenance"]["dry_run"] is True


def test_the_token_count_is_measured_from_this_repos_own_calls():
    """MEASURED, not chars/4. This project has mis-priced the same operation
    three times and always toward spending."""
    cal = B.calibrate_chars_per_token()
    assert cal["chars_per_token"] is not None
    assert 3.5 < cal["chars_per_token"] < 7.0, cal
    assert cal["n_calls"] >= 9, cal
    assert "usage" in cal["source"]


def test_an_unmeasurable_cost_is_reported_as_unmeasured_not_as_a_constant(tmp_path):
    """The failure mode this project has hit three times is a guess wearing the
    word "measured". With no usable log there is no number, and the dry run
    must say so rather than fall back to chars/4."""
    cal = B.calibrate_chars_per_token(usage_path=str(tmp_path / "nothing.jsonl"))
    assert cal["chars_per_token"] is None
    assert "UNAVAILABLE" in cal["method"]
    est = B.dry_run_cost([BEHAVIOUR], VOCAB, model="gpt-5.6-luna",
                         calibration=cal)
    assert est["measured"] is False
    assert est["usd_likely"] is None and est["usd_ceiling"] is None


def test_the_cost_estimate_goes_through_spend_cost_of(monkeypatch):
    import spend
    seen = []
    real = spend.cost_of
    monkeypatch.setattr(spend, "cost_of",
                        lambda r, px: (seen.append(r), real(r, px))[1])
    est = B.dry_run_cost([BEHAVIOUR], VOCAB, model="gpt-5.6-luna")
    assert seen, "cost must be computed by spend.cost_of, not re-implemented"
    assert est["usd_ceiling"] >= est["usd_likely"] > 0
    assert est["input_tokens"] > 0 and est["measured"] is True


def test_the_notation_block_is_priced_not_assumed():
    plain = B.dry_run_cost([BEHAVIOUR], VOCAB, model="gpt-5.6-luna")
    G()
    notated = B.dry_run_cost([BEHAVIOUR], VOCAB, model="gpt-5.6-luna",
                             notation=True)
    assert notated["input_tokens"] > plain["input_tokens"]


# ------------------------------------------------------------ seeded draws

def test_draws_are_seeded_and_written_to_separate_files(tmp_path):
    client = FakeClient(reply([act("refuse_request")]))
    paths = B.run_draws(client, [BEHAVIOUR], VOCAB, draws=3,
                        out_dir=str(tmp_path))
    assert len(paths) == 3
    assert len({os.path.basename(p) for p in paths}) == 3
    seeds = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            seeds.append(json.load(f)["provenance"]["seed"])
    assert seeds == [0, 1, 2]
    assert client.calls == 3


def test_spread_is_reported_across_the_real_five_draws():
    """A single draw is not a result. The spread is a number or it is nothing."""
    paths = [os.path.join(HERE, f"behavior_atoms_v2_draw{i}.json")
             for i in range(5)]
    if not all(os.path.exists(p) for p in paths):
        pytest.skip("v2 draws absent")
    s = B.spread(paths)
    assert s["n_draws"] == 5
    assert len(s["behaviours"]) == 9
    for slug, row in s["behaviours"].items():
        assert 0.0 <= row["mean_jaccard"] <= 1.0
        assert row["atoms_mean"] > 0
    assert 0.0 <= s["mean_jaccard"] <= 1.0
