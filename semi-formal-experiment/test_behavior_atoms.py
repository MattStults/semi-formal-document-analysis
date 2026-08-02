"""Tests for behavior_atoms.py — the QUERY side of the atom ontology.

The defect this module fixes: relevance.py scored every query with an EMPTY
behaviour-atom set, because the panel file has no `atoms` key. 0.6 of the
scoring weight was multiplied by zero on every query. So the tests below care
about two things above all:

  1. the artifact actually loads through relevance.load_behaviour_atoms and
     yields non-empty atoms (the channel is alive), and
  2. the names in it are names the CLAUSE side actually used (the channel
     matches). A behaviour atom that no clause carries is just as dead as no
     atom at all, only harder to see.
"""
import json
import os
import warnings

import pytest

import behavior_atoms as B
import relevance as R

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ fixtures

VOCAB = [
    {"name": "user_request_ambiguous", "kind": "situation",
     "gloss": "the user's request admits more than one reading", "n_clauses": 9},
    {"name": "clarifying_question", "kind": "act",
     "gloss": "the assistant asks the user what they meant", "n_clauses": 4},
    {"name": "refuse_request", "kind": "act",
     "gloss": "the assistant declines to do what was asked", "n_clauses": 21},
    {"name": "third_party_harm", "kind": "situation",
     "gloss": "someone outside the conversation is harmed", "n_clauses": 12},
    {"name": "helpfulness", "kind": "value",
     "gloss": "the good of actually helping the person in front of you",
     "n_clauses": 30},
    {"name": "operator", "kind": "entity",
     "gloss": "the business deploying the model", "n_clauses": 40},
]

BEHAVIOUR = {"slug": "helpfulness", "name": "Helpfulness",
             "definition": "The model should be genuinely and substantively "
                           "helpful, treating unhelpfulness as a real cost."}

AMBIG_BEHAVIOUR = {"slug": "ambiguity", "name": "Handling ambiguous requests",
                   "definition": "When a user's request is ambiguous the model "
                                 "should ask what was meant rather than guess."}


def reply(selected=(), new=()):
    return {"text": json.dumps({"selected": list(selected), "new": list(new)}),
            "finish_reason": "stop"}


class FakeClient:
    """Scripted responses. Counts calls, so 'one call per behaviour' is a
    measured claim rather than an intention."""

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


# --------------------------------------------------- no network in a dry run

def test_module_has_no_direct_http_usage():
    """Calls go through providers.py, which is the only thing that may touch
    the network and which defaults to a dry-run client."""
    src = open(os.path.join(HERE, "behavior_atoms.py")).read()
    for forbidden in ("urllib", "requests.post", "import requests",
                      "openai", "anthropic", "socket"):
        assert forbidden not in src, f"must not reference {forbidden} directly"


def test_dry_run_makes_no_network_call(tmp_path, monkeypatch):
    """The default path must be incapable of spending money. urlopen is
    poisoned; a dry run has to complete anyway."""
    import urllib.request

    def boom(*a, **k):
        raise AssertionError("dry run attempted a network call")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    out = tmp_path / "behavior_atoms.json"
    rc = B.main(["--out", str(out), "--annotations", str(tmp_path / "nope.json"),
                 "--prompt-log", str(tmp_path / "plog"),
                 "--log", str(tmp_path / "fail.jsonl")])
    assert rc == 0
    art = json.load(open(out))
    assert art["provenance"]["dry_run"] is True


def test_live_is_opt_in_and_dry_run_is_the_default():
    args = B.build_parser().parse_args([])
    assert args.live is False and args.dry_run is True


# ------------------------------------------------------- the closed taxonomy

def test_out_of_taxonomy_kind_is_rejected_and_counted(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": "refuse_request", "kind": "act", "weight": 3},
                        {"name": "helpfulness", "kind": "topic", "weight": 3}],
           "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail)
    assert [a["name"] for a in atoms] == ["refuse_request"]
    assert stats["rejections"]["bad_kind"] == 1
    assert stats["atoms_rejected"] == 1
    assert fail.count() >= 1


def test_every_emitted_atom_carries_a_taxonomy_kind(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": a["name"], "kind": a["kind"], "weight": 2}
                        for a in VOCAB], "new": []}
    atoms, _ = B.verify_selection(obj, VOCAB, fail)
    assert atoms and all(a["kind"] in B.ATOM_KINDS for a in atoms)


# ------------------------------------------------- selection is constrained

def test_selection_mode_rejects_atoms_absent_from_the_vocabulary(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": "refuse_request", "kind": "act", "weight": 3},
                        {"name": "sycophantic_praise", "kind": "act",
                         "weight": 3}],
           "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail)
    assert [a["name"] for a in atoms] == ["refuse_request"]
    assert stats["rejections"]["unknown_atom"] == 1


def test_explicitly_new_atoms_survive_and_are_marked(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [], "new": [{"name": "unhelpfulness_cost", "kind": "value",
                                    "gloss": "the cost of not helping",
                                    "weight": 3}]}
    atoms, stats = B.verify_selection(obj, VOCAB, fail)
    assert [(a["name"], a["new"]) for a in atoms] == [("unhelpfulness_cost", True)]
    assert stats["atoms_new"] == 1


def test_new_atoms_are_capped_and_the_excess_counted(tmp_path):
    fail = fail_log(tmp_path)
    new = [{"name": f"coined_atom_{i}", "kind": "value", "gloss": "g",
            "weight": 1} for i in range(8)]
    atoms, stats = B.verify_selection({"selected": [], "new": new}, VOCAB, fail,
                                      max_new=3)
    assert len(atoms) == 3
    assert stats["rejections"]["excess_new"] == 5


def test_kind_disagreement_snaps_to_the_clause_side_kind(tmp_path):
    """Matching is on (name, kind) and the clause side's kind is the one in the
    index, so a behaviour filing `refuse_request` as a situation would miss
    every clause carrying it. Snap, and count."""
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": "refuse_request", "kind": "situation",
                         "weight": 3}], "new": []}
    atoms, stats = B.verify_selection(obj, VOCAB, fail)
    assert atoms[0]["kind"] == "act"
    assert stats["kind_snapped"] == 1


def test_weights_are_emitted_and_clamped(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": "refuse_request", "kind": "act", "weight": 9},
                        {"name": "operator", "kind": "entity", "weight": "x"}],
           "new": []}
    atoms, _ = B.verify_selection(obj, VOCAB, fail)
    by = {a["name"]: a["weight"] for a in atoms}
    assert by["refuse_request"] == B.MAX_WEIGHT
    assert by["operator"] == B.DEFAULT_WEIGHT


# ------------------------------------------------- THE alignment requirement

def test_vocabulary_is_shown_to_the_model_with_glosses():
    """An atom that is never shown can never be selected. The gloss is what the
    reuse decision is actually made on."""
    system, user = B.render_prompt(AMBIG_BEHAVIOUR, VOCAB)
    for a in VOCAB:
        assert a["name"] in user
        assert a["gloss"] in user


def test_behaviour_about_ambiguity_selects_the_existing_vocabulary_name(tmp_path):
    """The make-or-break property: a behaviour about ambiguous requests must end
    up carrying `user_request_ambiguous` — the name the CLAUSE side coined —
    not a private variant of it. Two defences are tested at once: the name is
    on the list the model is shown, and a variant coined anyway is resolved
    back onto the listed name by vocab_key."""
    system, user = B.render_prompt(AMBIG_BEHAVIOUR, VOCAB)
    assert "user_request_ambiguous" in user

    fail = fail_log(tmp_path)
    variant = {"selected": [],
               "new": [{"name": "ambiguous_user_query", "kind": "situation",
                        "gloss": "the query is unclear", "weight": 3}]}
    atoms, stats = B.verify_selection(variant, VOCAB, fail)
    assert [a["name"] for a in atoms] == ["user_request_ambiguous"]
    assert all(a["new"] is False for a in atoms)
    assert stats["atoms_aliased"] == 1


def test_alignment_is_measured_against_the_clause_vocabulary(tmp_path):
    """The artifact has to report what fraction of its atoms exist on the clause
    side. A run where that is 0 has a live-looking artifact and a dead channel,
    and nothing else in the pipeline would notice."""
    client = FakeClient(reply(
        selected=[{"name": "helpfulness", "kind": "value", "weight": 3},
                  {"name": "refuse_request", "kind": "act", "weight": 2}],
        new=[{"name": "unhelpfulness_cost", "kind": "value", "gloss": "g",
              "weight": 2}]))
    art = B.run(client, [BEHAVIOUR], VOCAB, out=str(tmp_path / "b.json"),
                log_path=str(tmp_path / "f.jsonl"), model="m")
    entry = art["helpfulness"]
    assert entry["counts"]["atoms_in_clause_vocabulary"] == 2
    assert entry["counts"]["atoms_total"] == 3
    assert art["provenance"]["alignment"]["in_vocabulary_rate"] == pytest.approx(
        2 / 3, abs=1e-4)


def test_prefiltering_reports_the_unshown_fraction():
    """Any atom not shown is an invisible recall cap. It must be a number in the
    artifact, not a footnote."""
    shown, meta = B.prefilter_vocabulary(VOCAB, "ambiguous request clarify", 2)
    assert len(shown) == 2
    assert meta["vocabulary_total"] == len(VOCAB)
    assert meta["vocabulary_shown"] == 2
    assert meta["unshown_fraction"] == pytest.approx(1 - 2 / len(VOCAB), abs=1e-4)
    # the prefilter must be relevant, not arbitrary: the ambiguity atoms win
    assert "user_request_ambiguous" in {a["name"] for a in shown}


def test_no_prefiltering_when_the_vocabulary_fits():
    shown, meta = B.prefilter_vocabulary(VOCAB, "anything", 100)
    assert len(shown) == len(VOCAB) and meta["unshown_fraction"] == 0.0


# ------------------------------------------------------ relevance.py loading

def test_artifact_loads_through_relevance_loader(tmp_path):
    client = FakeClient(reply(
        selected=[{"name": "helpfulness", "kind": "value", "weight": 3},
                  {"name": "refuse_request", "kind": "act", "weight": 2}]))
    out = str(tmp_path / "behavior_atoms.json")
    B.run(client, [BEHAVIOUR], VOCAB, out=out, log_path=str(tmp_path / "f.jsonl"),
          model="m")
    loaded = R.load_behaviour_atoms(out)
    assert set(loaded) == {"helpfulness"}
    assert {a["name"] for a in loaded["helpfulness"]} == {"helpfulness",
                                                          "refuse_request"}
    assert all(a["kind"] in R.ATOM_KINDS for a in loaded["helpfulness"])
    assert all(a["gloss"] for a in loaded["helpfulness"])


def test_loaded_atoms_actually_drive_the_relevance_atom_channel(tmp_path):
    """End to end: the artifact must raise the score of a clause annotated with
    the same atom. This is the channel that was dead."""
    client = FakeClient(reply(
        selected=[{"name": "third_party_harm", "kind": "situation", "weight": 3}]))
    out = str(tmp_path / "behavior_atoms.json")
    B.run(client, [{"slug": "harm", "name": "Harm", "definition": "avoid harm"}],
          VOCAB, out=out, log_path=str(tmp_path / "f.jsonl"), model="m")

    clauses = [{"id": "c1", "quote": "a totally unrelated sentence about pears"},
               {"id": "c2", "quote": "another unrelated sentence about pears"}]
    ann = {"c1": [{"name": "third_party_harm", "kind": "situation",
                   "gloss": "someone outside is harmed"}]}
    panel = {"harm": {"slug": "harm", "name": "Harm", "definition": "avoid harm"}}
    behaviours = R.behaviours_from_panel(panel, out)
    idx = R.RelevanceIndex(clauses, ann)
    scores = dict(idx.rank(behaviours["harm"]))
    assert scores["c1"] > scores["c2"]


def test_provenance_key_is_not_read_as_a_behaviour(tmp_path):
    client = FakeClient(reply(selected=[{"name": "helpfulness", "kind": "value",
                                         "weight": 3}]))
    out = str(tmp_path / "b.json")
    B.run(client, [BEHAVIOUR], VOCAB, out=out, log_path=str(tmp_path / "f.jsonl"),
          model="m")
    assert set(R.load_behaviour_atoms(out)) == {"helpfulness"}


# --------------------------------------------------- degradation & failures

def test_missing_annotations_falls_back_and_warns_loudly(tmp_path):
    assert B.load_vocabulary(str(tmp_path / "absent.json")) == []
    client = FakeClient(reply(new=[{"name": "helpful_response", "kind": "act",
                                    "gloss": "the model helps", "weight": 3}]))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        art = B.run(client, [BEHAVIOUR], [], out=str(tmp_path / "b.json"),
                    log_path=str(tmp_path / "f.jsonl"), model="m")
    assert any("FREE GENERATION" in str(w.message).upper() for w in caught)
    assert any("alignment" in w.lower() for w in art["_warnings"])
    assert art["provenance"]["vocabulary_aligned"] is False
    # free generation must still produce atoms, and must not silently claim
    # they are aligned
    assert art["helpfulness"]["atoms"]
    assert art["provenance"]["alignment"]["in_vocabulary_rate"] == 0.0


def test_free_generation_does_not_cap_new_atoms(tmp_path):
    """With no vocabulary there is nothing to select from, so the new-atom cap
    would zero the run."""
    fail = fail_log(tmp_path)
    new = [{"name": f"a_{i}", "kind": "value", "gloss": "g"} for i in range(9)]
    atoms, _ = B.verify_selection({"selected": [], "new": new}, [], fail,
                                  max_new=3)
    assert len(atoms) == 9


def test_truncated_response_is_detected_not_parsed_as_empty(tmp_path):
    fail = fail_log(tmp_path)
    part = B.atoms_for_behaviour(
        {"text": '{"selected": [{"name": "refuse_request", "kind": "act"',
         "finish_reason": "length"},
        BEHAVIOUR, VOCAB, fail)
    assert part["truncated"] is True
    assert part["stats"]["truncated"] == 1
    assert any(r["stage"] == "truncated_output" for r in fail.records)


def test_unparseable_response_is_recorded_not_raised(tmp_path):
    fail = fail_log(tmp_path)
    part = B.atoms_for_behaviour({"text": "sorry, I cannot", "finish_reason": "stop"},
                                 BEHAVIOUR, VOCAB, fail)
    assert part["atoms"] == [] and part["parsed"] is False
    assert fail.count() >= 1


def test_dry_run_response_is_not_a_truncation(tmp_path):
    fail = fail_log(tmp_path)
    part = B.atoms_for_behaviour(None, BEHAVIOUR, VOCAB, fail)
    assert part["truncated"] is False and part["atoms"] == []


# ------------------------------------------------------------------ conduct

CONDUCT = ["Asked to summarise a contract, the model refuses because it is not "
           "a lawyer, though the user only wanted the gist."]


def test_conduct_reaches_the_prompt_and_is_distinguishable():
    system, user = B.render_prompt(BEHAVIOUR, VOCAB, conduct=CONDUCT)
    assert CONDUCT[0] in user
    assert "CONDUCT" in user
    _, plain = B.render_prompt(BEHAVIOUR, VOCAB)
    assert CONDUCT[0] not in plain


def test_conduct_atoms_are_kept_distinguishable_in_the_artifact(tmp_path):
    client = FakeClient(reply(selected=[
        {"name": "helpfulness", "kind": "value", "weight": 3,
         "source": "definition"},
        {"name": "refuse_request", "kind": "act", "weight": 3,
         "source": "conduct"}]))
    art = B.run(client, [BEHAVIOUR], VOCAB, conduct={"helpfulness": CONDUCT},
                out=str(tmp_path / "b.json"), log_path=str(tmp_path / "f.jsonl"),
                model="m")
    entry = art["helpfulness"]
    assert entry["conduct"] == CONDUCT
    assert entry["source"] == "definition+conduct"
    src = {a["name"]: a["source"] for a in entry["atoms"]}
    assert src == {"helpfulness": "definition", "refuse_request": "conduct"}
    assert entry["counts"]["atoms_from_conduct"] == 1


def test_source_defaults_to_definition_when_no_conduct_was_given(tmp_path):
    fail = fail_log(tmp_path)
    obj = {"selected": [{"name": "refuse_request", "kind": "act", "weight": 3,
                         "source": "conduct"}], "new": []}
    atoms, _ = B.verify_selection(obj, VOCAB, fail, has_conduct=False)
    assert atoms[0]["source"] == "definition"


# ----------------------------------------------------- the cache invariant

def test_exactly_one_call_per_behaviour(tmp_path):
    client = FakeClient(reply(selected=[{"name": "helpfulness", "kind": "value",
                                         "weight": 3}]))
    behaviours = [BEHAVIOUR, dict(AMBIG_BEHAVIOUR),
                  {"slug": "third", "name": "Third", "definition": "x"}]
    B.run(client, behaviours, VOCAB, out=str(tmp_path / "b.json"),
          log_path=str(tmp_path / "f.jsonl"), model="m")
    assert client.calls == 3


def test_a_relevance_query_never_calls_this_module():
    """relevance.py must not import behavior_atoms: query time is offline, the
    artifact is read from disk."""
    src = open(os.path.join(HERE, "relevance.py")).read()
    assert "import behavior_atoms" not in src


def test_prompt_carries_only_one_behaviour():
    """One behaviour per call keeps the artifact incrementally rebuildable and
    keeps a truncation from costing every behaviour at once."""
    _, user = B.render_prompt(BEHAVIOUR, VOCAB)
    assert BEHAVIOUR["definition"] in user
    assert AMBIG_BEHAVIOUR["definition"] not in user


# ------------------------------------------------------------------ loading

def test_load_vocabulary_reads_the_annotate_artifact(tmp_path):
    art = {"vocabulary": {"refuse_request": {"kind": "act", "gloss": "declines",
                                             "n_clauses": 3, "clauses": ["c1"]}},
           "atoms": [], "provenance": {}}
    p = tmp_path / "annotations.json"
    p.write_text(json.dumps(art))
    vocab = B.load_vocabulary(str(p))
    assert vocab == [{"name": "refuse_request", "kind": "act",
                      "gloss": "declines", "n_clauses": 3}]


def test_load_vocabulary_falls_back_to_the_atom_list(tmp_path):
    """Some artifacts carry atoms without the vocabulary index."""
    art = {"atoms": [{"name": "refuse_request", "kind": "act", "gloss": "declines",
                      "clause_id": "c1"},
                     {"name": "refuse_request", "kind": "act", "gloss": "declines",
                      "clause_id": "c2"}]}
    p = tmp_path / "a.json"
    p.write_text(json.dumps(art))
    vocab = B.load_vocabulary(str(p))
    assert len(vocab) == 1 and vocab[0]["n_clauses"] == 2


def test_load_behaviours_reads_the_panel_file():
    rows = B.load_behaviours()
    assert {r["slug"] for r in rows} >= {"helpfulness"}
    assert all(r.get("definition") for r in rows)


def test_load_conduct_accepts_a_string_or_a_list(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"helpfulness": "one sentence",
                             "other": ["a", "b"]}))
    got = B.load_conduct(str(p))
    assert got == {"helpfulness": ["one sentence"], "other": ["a", "b"]}
