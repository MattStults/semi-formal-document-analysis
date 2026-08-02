"""Tests for relevance.py — the offline behaviour -> clause query.

Nothing here calls a model or touches the network. The hand-written annotation
fixture (`relevance_fixture.json`) stands in for annotate.py's output, which is
being produced concurrently; every test that exercises the annotated path runs
against it or against an inline dict.
"""
from __future__ import annotations

import json
import os

import pytest

import relevance as R

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- fixtures

@pytest.fixture
def clauses():
    """Six clauses over two sections. `h*` are helpfulness-flavoured, `s*` are
    safety-flavoured, `n1` is neither."""
    return [
        {"id": "h1", "quote": "The assistant should be genuinely helpful to the "
                              "user and treat unhelpfulness as a real cost.",
         "section_path": ["Do the best work"], "kind": "conditional",
         "locator": "spec > Do the best work > 1"},
        {"id": "h2", "quote": "Refusing a benign request is itself a failure to "
                              "help the user.",
         "section_path": ["Do the best work"], "kind": "conditional",
         "locator": "spec > Do the best work > 2"},
        {"id": "h3", "quote": "Example: the assistant drafts the email.",
         "section_path": ["Do the best work"], "kind": "example",
         "locator": "spec > Do the best work > 3"},
        {"id": "s1", "quote": "The assistant must weigh potential harm to third "
                              "parties outside the conversation.",
         "section_path": ["Stay in bounds"], "kind": "conditional",
         "locator": "spec > Stay in bounds > 1"},
        {"id": "s2", "quote": "Do not produce content that harms society or the "
                              "world at large.",
         "section_path": ["Stay in bounds"], "kind": "conditional",
         "locator": "spec > Stay in bounds > 2"},
        {"id": "n1", "quote": "Dates are rendered in ISO 8601 format.",
         "section_path": ["Definitions"], "kind": "definitional",
         "locator": "spec > Definitions > 1"},
    ]


@pytest.fixture
def help_behaviour():
    return R.Behaviour(
        slug="helpfulness",
        name="Helpfulness",
        definition="The model should be genuinely and substantively helpful to "
                   "the users it works with, treating unhelpfulness as a real "
                   "cost rather than a safe default.",
        atoms=[{"name": "user_benefit", "kind": "value",
                "gloss": "the user is materially helped"},
               {"name": "refusal", "kind": "act",
                "gloss": "the assistant declines a request"}],
    )


@pytest.fixture
def harm_behaviour():
    return R.Behaviour(
        slug="harm-avoidance-to-third-parties",
        name="Harm avoidance to third parties",
        definition="The model should weigh potential harm to those outside the "
                   "conversation, avoiding actions or content that harm third "
                   "parties, society, or the world.",
        atoms=[{"name": "third_party_harm", "kind": "situation",
                "gloss": "someone outside the conversation is harmed"}],
    )


# ------------------------------------------------------- loader tolerance

def test_loader_tolerates_atom_with_only_a_name():
    """The ONLY required atom field is `name`. Everything else is optional and
    its absence must not raise — annotate.py is being built concurrently and we
    do not control which optional fields it ships."""
    ann = R.load_annotations({"clauses": [{"clause_id": "h1",
                                           "atoms": [{"name": "bare_atom"}]}]})
    assert [a["name"] for a in ann["h1"]] == ["bare_atom"]
    a = ann["h1"][0]
    assert a["kind"] == "" and a["gloss"] == "" and a["quote"] == ""


def test_loader_accepts_clause_major_atom_major_and_flat_shapes():
    clause_major = {"clauses": [{"clause_id": "c1",
                                 "atoms": [{"name": "x", "kind": "act",
                                            "gloss": "does x"}]}]}
    atom_major = {"atoms": [{"name": "x", "kind": "act", "gloss": "does x",
                             "quote_spans": [{"clause_id": "c1",
                                              "locator": "l", "quote": "q"}]}]}
    flat = [{"name": "x", "kind": "act", "gloss": "does x", "clause_id": "c1"}]
    for payload in (clause_major, atom_major, flat):
        ann = R.load_annotations(payload)
        assert list(ann) == ["c1"]
        assert ann["c1"][0]["name"] == "x"
        assert ann["c1"][0]["kind"] == "act"


def test_loader_skips_unusable_records_without_crashing():
    ann = R.load_annotations({"clauses": [
        {"clause_id": "c1", "atoms": [{"name": "ok"}, {"gloss": "no name"}, {}]},
        {"atoms": [{"name": "orphan"}]},          # no clause_id
        "not a dict",
    ]})
    assert list(ann) == ["c1"]
    assert [a["name"] for a in ann["c1"]] == ["ok"]


def test_loader_reads_the_shipped_fixture_file():
    ann = R.load_annotations(os.path.join(HERE, R.FIXTURE))
    assert ann, "relevance_fixture.json must ship with the module"
    for cid, atoms in ann.items():
        assert isinstance(cid, str) and atoms
        for a in atoms:
            assert set(R.ATOM_FIELDS) <= set(a)


def test_loader_missing_file_is_empty_not_fatal(tmp_path):
    assert R.load_annotations(str(tmp_path / "absent.json")) == {}


# --------------------------------------------------------- basic ranking

def test_ranking_puts_the_on_topic_clause_first(clauses, help_behaviour):
    idx = R.RelevanceIndex(clauses)
    ranked = idx.rank(help_behaviour)
    assert ranked[0][0] == "h1"
    scores = dict(ranked)
    assert scores["h1"] > scores["n1"]
    assert scores["s1"] < scores["h1"]


def test_ranking_is_behaviour_specific(clauses, help_behaviour, harm_behaviour):
    idx = R.RelevanceIndex(clauses)
    assert idx.rank(help_behaviour)[0][0] == "h1"
    assert idx.rank(harm_behaviour)[0][0] in {"s1", "s2"}


def test_ranking_is_deterministic(clauses, help_behaviour):
    idx = R.RelevanceIndex(clauses)
    assert idx.rank(help_behaviour) == idx.rank(help_behaviour)
    assert R.RelevanceIndex(clauses).rank(help_behaviour) == idx.rank(help_behaviour)


def test_scores_are_normalized_to_unit_interval(clauses, help_behaviour):
    ranked = R.RelevanceIndex(clauses).rank(help_behaviour)
    assert all(0.0 <= s <= 1.0 for _, s in ranked)
    assert max(s for _, s in ranked) == pytest.approx(1.0)
    assert [s for _, s in ranked] == sorted((s for _, s in ranked), reverse=True)


def test_every_clause_is_ranked(clauses, help_behaviour):
    ranked = R.RelevanceIndex(clauses).rank(help_behaviour)
    assert {c for c, _ in ranked} == {c["id"] for c in clauses}


def test_no_model_is_called_at_query_time():
    """The entire value proposition is annotate-once / query-many-instantly.
    A query-time model call collapses this into the baseline we are beating."""
    src = open(os.path.join(HERE, "relevance.py")).read()
    for forbidden in ("import providers", "from providers", "requests",
                      "urllib", "http", "openai", "anthropic", "torch",
                      "transformers", "sentence_transformers"):
        assert forbidden not in src, f"query path must not reference {forbidden}"


# ------------------------------------------------- signals beyond exact names

def test_not_purely_exact_name_overlap(clauses, harm_behaviour):
    """No clause shares an atom NAME with the behaviour (there are no clause
    annotations at all here) and the query still ranks correctly — the lexical
    channel has to carry it."""
    idx = R.RelevanceIndex(clauses, annotations={})
    ranked = idx.rank(harm_behaviour)
    assert ranked[0][1] > 0
    assert ranked[0][0] in {"s1", "s2"}


def test_shared_atom_names_raise_the_score(clauses, harm_behaviour):
    ann = {"n1": [{"name": "third_party_harm", "kind": "situation",
                   "gloss": "someone outside the conversation is harmed"}]}
    plain = dict(R.RelevanceIndex(clauses, annotations={}).rank(harm_behaviour))
    boosted = dict(R.RelevanceIndex(clauses, annotations=ann).rank(harm_behaviour))
    assert boosted["n1"] > plain["n1"]


def test_atom_kind_agreement_is_a_signal(clauses, help_behaviour):
    same = {"n1": [{"name": "zzz", "kind": "act", "gloss": ""}]}
    other = {"n1": [{"name": "zzz", "kind": "entity", "gloss": ""}]}
    w = R.Weights(kind=0.5)
    s_same = dict(R.RelevanceIndex(clauses, annotations=same, weights=w)
                  .rank(help_behaviour))["n1"]
    s_other = dict(R.RelevanceIndex(clauses, annotations=other, weights=w)
                   .rank(help_behaviour))["n1"]
    assert s_same > s_other


def test_section_proximity_lifts_a_lexically_silent_clause(clauses, help_behaviour):
    """h3 ('Example: the assistant drafts the email') shares almost no
    vocabulary with the behaviour, but sits in the same section as h1/h2.
    Section smoothing must lift it above the unrelated Definitions clause."""
    off = R.RelevanceIndex(clauses, weights=R.Weights(section=0.0))
    on = R.RelevanceIndex(clauses, weights=R.Weights(section=0.6))
    assert on.raw_scores(help_behaviour)["h3"] > off.raw_scores(help_behaviour)["h3"]
    assert on.raw_scores(help_behaviour)["h3"] > on.raw_scores(help_behaviour)["n1"]


def test_query_expansion_can_be_disabled_and_changes_the_ranking(clauses,
                                                                 help_behaviour):
    a = R.RelevanceIndex(clauses, weights=R.Weights(expansion_terms=0)).rank(help_behaviour)
    b = R.RelevanceIndex(clauses, weights=R.Weights(expansion_terms=20)).rank(help_behaviour)
    assert dict(a) != dict(b)


def test_stemming_matches_morphological_variants():
    assert R.stem("refusals") == R.stem("refusal")
    assert R.stem("harming") == R.stem("harm")
    assert R.stem("helpfulness") == R.stem("helpful")
    assert R.stem("assistants") == R.stem("assistant")
    assert R.stem("harm") != R.stem("help")
    assert R.tokens("The assistant  should!") == {R.stem("assistant")}


# ------------------------------------------------------ threshold behaviour

def test_predict_is_binary_and_thresholded(clauses, help_behaviour):
    idx = R.RelevanceIndex(clauses)
    hi = idx.predict(help_behaviour, threshold=0.95)
    lo = idx.predict(help_behaviour, threshold=0.0)
    assert isinstance(hi, set) and isinstance(lo, set)
    assert 0 < len(hi) < len(lo)
    assert hi <= lo
    # threshold 0.0 means "anything with a positive signal", never "everything"
    assert lo == {c for c, s in idx.rank(help_behaviour) if s > 0}


def test_threshold_sweep_is_monotone(clauses, help_behaviour):
    idx = R.RelevanceIndex(clauses)
    sweep = idx.sweep(help_behaviour)
    ts = [t for t, _ in sweep]
    assert ts == sorted(ts)
    sizes = [len(s) for _, s in sweep]
    assert sizes == sorted(sizes, reverse=True), "higher threshold must predict less"
    for (_, a), (_, b) in zip(sweep, sweep[1:]):
        assert b <= a, "sweep sets must be nested"


def test_degenerate_corpus_predicts_nothing_rather_than_everything():
    """Zero lexical signal anywhere: the honest answer is the empty set, not a
    tie at the top that a threshold of 1.0 would silently accept."""
    dead = [{"id": f"d{i}", "quote": "zzz", "section_path": ["S"]}
            for i in range(4)]
    b = R.Behaviour(slug="x", name="", definition="qqq wwww", atoms=[])
    idx = R.RelevanceIndex(dead)
    assert all(s == 0.0 for _, s in idx.rank(b))
    assert idx.predict(b, threshold=0.5) == set()
    assert idx.predict(b, threshold=0.0) == set(), \
        "an all-zero score must not be promoted to relevant by a zero threshold"


def test_empty_clause_set_does_not_crash(help_behaviour):
    idx = R.RelevanceIndex([])
    assert idx.rank(help_behaviour) == []
    assert idx.predict(help_behaviour, 0.5) == set()
    assert idx.sweep(help_behaviour)


def test_behaviour_with_no_text_predicts_nothing(clauses):
    empty = R.Behaviour(slug="e", name="", definition="", atoms=[])
    idx = R.RelevanceIndex(clauses)
    assert idx.predict(empty, threshold=0.5) == set()


# ------------------------------------------------------------ integration

def test_from_panel_builds_a_behaviour():
    b = R.behaviour_from_panel({"slug": "s", "name": "N", "definition": "D"})
    assert (b.slug, b.name, b.definition) == ("s", "N", "D")
    assert b.atoms == []


def test_runs_over_the_real_clause_file():
    idx = R.RelevanceIndex.from_files()
    assert len(idx.clauses) == 593
    b = R.behaviour_from_panel({
        "slug": "helpfulness", "name": "Helpfulness",
        "definition": "The model should be genuinely and substantively helpful "
                      "to the users and developers it works with."})
    ranked = idx.rank(b)
    assert len(ranked) == 593
    assert ranked[0][1] == pytest.approx(1.0)
    assert ranked[-1][1] < ranked[0][1]


# ============================================================
#  Atom IDF. Flagged by the annotate.py agent as the single most
#  likely way a good-looking artifact produces a bad F1: a clause
#  annotated only with generic atoms (`user`, `model`) is "covered"
#  and discriminates nothing.
# ============================================================

def _ann(mapping):
    return {cid: [dict(a) for a in atoms] for cid, atoms in mapping.items()}


@pytest.fixture
def generic_and_rare(clauses):
    """`user` is on every clause (a stopword atom); `refusal` on one."""
    ann = {c["id"]: [{"name": "user", "kind": "entity", "gloss": ""}]
           for c in clauses}
    ann["n1"].append({"name": "refusal", "kind": "act", "gloss": ""})
    return ann


def test_atom_appearing_everywhere_contributes_almost_nothing(clauses,
                                                              generic_and_rare):
    """An atom in 6 of 6 clauses is a stopword and must not move the ranking."""
    b_generic = R.Behaviour(slug="g", name="", definition="",
                            atoms=[{"name": "user", "kind": "entity"}])
    # isolate the atom channel: lexical/section/kind are separately tested
    idx = R.RelevanceIndex(clauses, annotations=generic_and_rare,
                           weights=R.Weights(lex=0.0, section=0.0, kind=0.0))
    assert "user" in idx.atom_stopwords
    assert idx.atom_idf["user"] == 0.0
    assert max(idx.raw_scores(b_generic).values()) == 0.0


def test_rare_atom_dominates_a_generic_one(clauses, generic_and_rare):
    b = R.Behaviour(slug="g", name="", definition="",
                    atoms=[{"name": "user", "kind": "entity"},
                           {"name": "refusal", "kind": "act"}])
    idx = R.RelevanceIndex(clauses, annotations=generic_and_rare,
                           weights=R.Weights(lex=0.0, section=0.0, kind=0.0))
    raw = idx.raw_scores(b)
    assert raw["n1"] > 0
    assert max(v for k, v in raw.items() if k != "n1") == 0.0, \
        "the generic atom must not lift the five clauses that carry only it"


def test_atom_vocabulary_is_reportable(clauses, generic_and_rare):
    idx = R.RelevanceIndex(clauses, annotations=generic_and_rare)
    vocab = idx.vocabulary()
    assert vocab[0] == ("user", 6)
    assert ("refusal", 1) in vocab


def test_kind_mismatch_is_discounted_not_dropped(clauses):
    """`refuse_request` (act) and `request_refused` (situation) are kept
    distinct by design, but the same NAME under a drifted kind is a known
    annotation instability — match it at a discount rather than missing it."""
    b = R.Behaviour(slug="g", name="", definition="",
                    atoms=[{"name": "refusal", "kind": "act"}])
    w = R.Weights(lex=0.0, section=0.0, kind=0.0)
    same = R.RelevanceIndex(
        clauses, annotations=_ann({"n1": [{"name": "refusal", "kind": "act"}]}),
        weights=w).raw_scores(b)["n1"]
    drift = R.RelevanceIndex(
        clauses, annotations=_ann({"n1": [{"name": "refusal",
                                           "kind": "situation"}]}),
        weights=w).raw_scores(b)["n1"]
    miss = R.RelevanceIndex(
        clauses, annotations=_ann({"n1": [{"name": "something_else",
                                           "kind": "act"}]}),
        weights=w).raw_scores(b)["n1"]
    assert same > drift > miss
    assert miss == 0.0


def test_atom_kinds_are_the_closed_set():
    assert R.ATOM_KINDS == ("situation", "act", "entity", "value")


# ---- explain(): auditability is half the stated value proposition ----
#
# explain() existed for hours with ZERO callers and ZERO tests, and the only
# CLI entry point ran the degraded lexical baseline while calling itself the
# tool. An unreachable method is a claim, not a feature.

import subprocess
import sys as _sys

import relevance as _R

_HERE = os.path.dirname(os.path.abspath(_R.__file__))


def _real_index():
    ann = os.path.join(_HERE, "annotations_b8.json")
    if not os.path.exists(ann):
        pytest.skip("annotations_b8.json not present")
    return _R.RelevanceIndex.from_files(annotations_path=ann)


def _real_behaviour(slug="helpfulness"):
    atoms = os.path.join(_HERE, "behavior_atoms_b8.json")
    panel = os.path.join(_HERE, "..", "data", "behaviours.json")
    if not (os.path.exists(atoms) and os.path.exists(panel)):
        pytest.skip("real artifacts not present")
    raw = next(b for b in json.load(open(panel))["behaviours"]
               if b["slug"] == slug)
    return _R.behaviour_from_panel(raw, _R.load_behaviour_atoms(atoms))


def test_explain_channels_sum_to_the_raw_score():
    """The decomposition must actually account for the score, or it is
    decoration rather than an audit trail."""
    idx, beh = _real_index(), _real_behaviour()
    cid = idx.rank(beh)[0][0]
    info = idx.explain(beh, cid)
    assert sum(info["channels"].values()) == pytest.approx(info["raw"], rel=1e-6)


def test_explain_returns_the_span_that_licensed_each_matched_atom():
    """behaviour -> atom -> span -> clause -> locator. Without the span the
    chain bottoms out in an assertion."""
    idx, beh = _real_index(), _real_behaviour()
    for cid, _ in idx.rank(beh)[:15]:
        info = idx.explain(beh, cid)
        if info["matched_atoms"]:
            a = info["matched_atoms"][0]
            assert a["quote"] and a["locator"]
            assert a["quote"] in idx.by_id[cid]["quote"], "span not from this clause"
            return
    pytest.skip("no matched atoms in the top 15")


def test_explain_names_the_behaviour_and_clause_kind_of_each_match():
    """Matching is on (name, kind); an audit that hides the kinds cannot show
    why a near-match was discounted."""
    idx, beh = _real_index(), _real_behaviour()
    for cid, _ in idx.rank(beh)[:15]:
        for a in idx.explain(beh, cid)["matched_atoms"]:
            assert "behaviour_kind" in a and "clause_kind" in a
            assert "kind_agrees" in a
            return
    pytest.skip("no matched atoms in the top 15")


def test_cli_runs_the_tool_not_the_degraded_baseline():
    """Regression: main() called from_files() with no annotations and
    behaviour_from_panel with no atoms, so the shipped CLI silently ran the
    lexical baseline and warned about it."""
    r = subprocess.run([_sys.executable, "relevance.py", "helpfulness", "--top", "3"],
                       cwd=_HERE, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "ATOM CHANNEL DISABLED" not in r.stderr, \
        "the default CLI path is still running without behaviour atoms"
    assert "LEXICAL BASELINE" not in r.stdout


def test_cli_baseline_mode_is_explicit_and_labelled():
    r = subprocess.run([_sys.executable, "relevance.py", "helpfulness",
                        "--baseline", "--top", "3"],
                       cwd=_HERE, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "LEXICAL BASELINE" in r.stdout


def test_cli_explain_is_reachable():
    idx, beh = _real_index(), _real_behaviour()
    cid = idx.rank(beh)[0][0]
    r = subprocess.run([_sys.executable, "relevance.py", "helpfulness",
                        "--explain", cid], cwd=_HERE,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "matched_atoms" in r.stdout and "channel_share" in r.stdout
