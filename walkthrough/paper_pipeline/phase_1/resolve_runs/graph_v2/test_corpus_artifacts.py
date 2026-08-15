"""Pins for the FULL-CORPUS artifacts (pre-ds7-review gap: the one file a
paid run consumes was the one file with no pin -- flagged 2026-08-14).

The live corpus and the test fixture are deliberately DIFFERENT FILES
(node_corpus_all.json vs node_corpus.json): the same-file design let a
corpus regeneration break the sample pins three times.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    return json.load(open(os.path.join(HERE, name), encoding="utf-8"))


def test_the_corpus_the_paid_run_reads_matches_its_config():
    cfg = _load("config_corpus_all.json")
    assert cfg["corpus"]["path"] == "node_corpus_all.json"
    corpus = _load("node_corpus_all.json")
    ids = [c["id"] for c in corpus["clauses"]]
    assert len(ids) == len(set(ids)), "duplicate ids in the corpus"
    assert sorted(ids) == sorted(cfg["select"]["clause_ids"]), \
        "the config selects ids the corpus does not contain (or vice versa)"


def test_the_corpus_derives_from_the_CERTIFIED_graph():
    """Every corpus row must be a node of the certified production graph --
    not the golden, not a superseded build."""
    import node_corpus as NC
    corpus = _load("node_corpus_all.json")
    graph = json.load(open(os.path.join(
        HERE, "runs/ds7/root_graph.production.json"), encoding="utf-8"))
    nodes = {NC.asp_id(n["id"]) for n in graph["nodes"]}
    missing = [c["id"] for c in corpus["clauses"] if c["id"] not in nodes]
    assert not missing, f"corpus rows absent from the certified graph: {missing[:5]}"
    assert len(corpus["clauses"]) == len(graph["nodes"]), \
        "the corpus does not cover the whole certified graph"


def test_the_sample_fixture_is_not_the_live_corpus():
    """The split itself: regenerating one must never be regenerating the
    other (the 'never pin an exact count of a live artifact' hazard)."""
    sample, live = _load("node_corpus.json"), _load("node_corpus_all.json")
    assert len(sample["clauses"]) < len(live["clauses"])
    assert (json.load(open(os.path.join(HERE, "config_graph_nodes.json"),
                           encoding="utf-8"))["corpus"]["path"]
            == "node_corpus.json")
