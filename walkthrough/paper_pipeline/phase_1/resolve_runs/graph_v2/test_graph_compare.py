"""RED check for graph_compare.py (required by GRAPH_EQUIVALENCE.md before
first use): golden vs a four-way-mutated copy of itself must flag EXACTLY
the four planted defects — merged node, deleted needs-edge, strengthened
establishes, re-covered dangling — and golden vs itself must be clean.

Targets are chosen by scanning the live golden, never pinned by id or count
(a legitimately regrown golden must not fail this gate)."""
import copy
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import graph_compare as gc                                     # noqa: E402
from recurse_driver import load_doc, nm                        # noqa: E402

GRAPH = os.path.join(HERE, "recurse", "root", "graph.json")


@pytest.fixture(scope="module")
def golden():
    return json.load(open(GRAPH))


@pytest.fixture(scope="module")
def doc_len():
    return len(load_doc(gc.DOC))


# ------------------------------------------------------------------- GREEN

@pytest.fixture(scope="module")
def self_report(golden, doc_len):
    return gc.compare(golden, golden, doc_len)


def test_self_compare_is_clean(golden, self_report):
    r = self_report
    n = len(golden["nodes"])
    for side in ("a", "b"):
        c = r["alignment"]["counts"][side]
        assert c == {"one_to_one": n, "split_join": 0, "misaligned": 0}
        assert r["alignment"]["line_mass"][side]["split_join"] == 0
        assert r["alignment"]["line_mass"][side]["misaligned"] == 0
    # GC-1 pin: content-identical self-compare must pair every node to its
    # own copy — no cross pairings inside identical-line-set groups
    assert all(p["a"] == p["b"] for p in r["alignment"]["pairs_1to1"])
    assert r["edges"]["recall"] == 1.0
    assert r["edges"]["precision"] == 1.0
    assert r["edges"]["unmatched_a"] == []
    assert r["edges"]["unmatched_b"] == []
    assert r["edges"]["strict_recall"] == 1.0
    assert r["edges"]["strict_precision"] == 1.0
    assert r["edges"]["strict_unmatched_a"] == []
    assert r["edges"]["strict_unmatched_b"] == []
    assert r["uncovered"]["jaccard"] == 1.0
    assert r["uncovered"]["only_a"] == []
    assert r["uncovered"]["only_b"] == []
    assert r["dangling"]["prose_only_a"] == []
    assert r["dangling"]["prose_only_b"] == []
    assert r["modal_queue"] == []
    # GC-2 pin (Matt's ruling 2026-08-11): identical establishes auto-agree,
    # so a self-compare leaves the class-2 seat queue empty
    assert r["class2_queue"] == []
    assert r["class2_auto_agreed"] == len(golden["nodes"])
    assert r["adjudication_queue"] == []


# --------------------------------------------- synthetic pins (review 08-11)

def _node(nid, est, lines, needs=(), provides=()):
    return {"id": nid, "establishes": est,
            "needs": [{"name": n, "prose": n} for n in needs],
            "provides": [{"name": p, "prose": p} for p in provides],
            "spans": [{"lines": list(l)} for l in lines]}


def test_gc1_identical_line_set_group_pairs_by_content():
    """GC-1 pin: within a same-line-set tie group, pairing follows the
    establishes content, never node-id order — a content-identical graph
    with swapped ids produces zero modal-queue items and zero seat work."""
    a = {"nodes": [_node("a1", "The assistant must refuse.", [(10, 20)]),
                   _node("a2", "The assistant should apologize.", [(10, 20)])],
         "uncovered": []}
    b = {"nodes": [_node("b1", "The assistant should apologize.", [(10, 20)]),
                   _node("b2", "The assistant must refuse.", [(10, 20)])],
         "uncovered": []}
    r = gc.compare(a, b, 200)
    assert {(p["a"], p["b"]) for p in r["alignment"]["pairs_1to1"]} == \
        {("a1", "b2"), ("a2", "b1")}
    assert r["modal_queue"] == []
    assert r["class2_queue"] == []


def test_gc4_poison_candidate_does_not_block_true_cover():
    """GC-4 pin: a high-overlap candidate that also sprawls elsewhere must
    not block the true 2-cover — subsets of the candidate list are searched,
    not only prefixes of it."""
    a = {"nodes": [_node("a1", "Claim.", [(1, 20)])], "uncovered": []}
    b = {"nodes": [_node("b_c1", "Part one.", [(1, 12)]),
                   _node("b_c2", "Part two.", [(13, 20)]),
                   _node("b_p", "Poison.", [(5, 14), (100, 150)])],
         "uncovered": []}
    r = gc.compare(a, b, 200)
    groups = r["alignment"]["split_join_groups"]
    assert len(groups) == 1
    assert groups[0]["one"] == {"graph": "a", "id": "a1"}
    assert sorted(groups[0]["many"]["ids"]) == ["b_c1", "b_c2"]
    assert groups[0]["union_jaccard"] == 1.0
    assert r["alignment"]["misaligned"]["a"] == []
    assert r["alignment"]["misaligned"]["b"] == ["b_p"]


def test_gc5_maximum_matching_rescues_stolen_partner():
    """GC-5 pin: greedy must not steal a node's only qualifying partner —
    the augmenting pass recovers the all-1:1 maximum matching instead of
    misfiling a true 1:1 as split/join."""
    a = {"nodes": [_node("a1", "One.", [(1, 10)]),
                   _node("a2", "Two.", [(1, 9)])], "uncovered": []}
    b = {"nodes": [_node("b1", "One.", [(1, 10)]),
                   _node("b2", "Two.", [(2, 11)])], "uncovered": []}
    r = gc.compare(a, b, 200)
    for side in ("a", "b"):
        assert r["alignment"]["counts"][side] == \
            {"one_to_one": 2, "split_join": 0, "misaligned": 0}
    assert r["alignment"]["split_join_groups"] == []
    assert {(p["a"], p["b"]) for p in r["alignment"]["pairs_1to1"]} == \
        {("a1", "b2"), ("a2", "b1")}


def test_gc6_uncovered_mismatch_reaches_adjudication_queue():
    """GC-6 pin: class-4 line disagreements are queue items, not just a
    printed diff."""
    a = {"nodes": [_node("a1", "Claim.", [(1, 10)])],
         "uncovered": [{"lines": [11, 12]}]}
    b = {"nodes": [_node("b1", "Claim.", [(1, 10)])], "uncovered": []}
    r = gc.compare(a, b, 200)
    assert {"kind": "uncovered_mismatch", "graph": "a", "lines": [11, 12]} \
        in r["adjudication_queue"]
    assert r["uncovered"]["only_a"] == [[11, 12]]


def test_gc3_shadowed_edges_disclosed_and_strict_metric_covers(
        golden, doc_len, self_report):
    """GC-3 pin: every edge deletion must be visible to the permissive
    metric, or to the strict exact-aligned-pair metric, or the edge must be
    LISTED in the report's shadowed_edges disclosure — never silent. One
    live shadowed deletion is executed to prove the strict metric fires
    where the permissive one is blind."""
    edges, _ = gc.build_edges(golden["nodes"])
    sh = self_report["edges"]["shadowed_edges"]
    assert sh["a"]["count"] == sh["b"]["count"] > 0
    listed = {(e["needer"], e["provider"], e["need"])
              for e in sh["a"]["edges"]}

    probe = None
    for e in edges:
        key = (e["needer"], e["provider"], e["need"])
        shadowed = any(
            f is not e and
            not f["needer_lines"].isdisjoint(e["needer_lines"]) and
            not f["provider_lines"].isdisjoint(e["provider_lines"])
            for f in edges)
        if not shadowed:
            # permissive metric detects this deletion (RED gate exercises it)
            continue
        # deleting the need removes every (needer, need) edge; the strict
        # metric misses the deletion only if a sibling edge keeps the exact
        # aligned endpoint pair alive
        strict_blind = any(f["need"] != e["need"] and
                           f["needer"] == e["needer"] and
                           f["provider"] == e["provider"] for f in edges)
        if strict_blind:
            # undetectable by BOTH metrics -> must be disclosed by name
            assert key in listed
            continue
        assert key in listed  # disclosure covers all shadowed edges
        if (probe is None and
                sum(1 for nd in next(n for n in golden["nodes"]
                                     if n["id"] == e["needer"])["needs"]
                    if nm(nd) == e["need"]) == 1 and
                sum(1 for f in edges if f["need"] == e["need"]) == 1):
            probe = e
    assert probe is not None

    b = copy.deepcopy(golden)
    nb = next(n for n in b["nodes"] if n["id"] == probe["needer"])
    nb["needs"] = [nd for nd in nb["needs"] if nm(nd) != probe["need"]]
    r = gc.compare(golden, b, doc_len)
    assert r["edges"]["recall"] == 1.0        # permissive metric is blind
    assert r["edges"]["strict_recall"] < 1.0  # strict metric detects it
    assert [(e["needer"], e["provider"], e["need"])
            for e in r["edges"]["strict_unmatched_a"]] == \
        [(probe["needer"], probe["provider"], probe["need"])]


# ---------------------------------------------------------- target picking

def _lines(node):
    return gc.node_lines(node)


def _pick_targets(golden):
    """Scan the golden for four mutually non-interfering mutation targets.
    Order of selection fixes ties deterministically."""
    nodes = golden["nodes"]
    by_id = {n["id"]: n for n in nodes}
    edges, danglings = gc.build_edges(nodes)
    dang_names = {d["name"] for d in danglings}
    line_counts = {}
    for n in nodes:
        for ln in _lines(n):
            line_counts[ln] = line_counts.get(ln, 0) + 1

    # deleted edge: unique need name on its needer, single provider, and no
    # OTHER edge whose two regions both overlap it (else region-matching
    # would still find a witness and the deletion would be invisible)
    del_edge = None
    for e in edges:
        needer = by_id[e["needer"]]
        if sum(1 for nd in needer["needs"] if nm(nd) == e["need"]) != 1:
            continue
        if sum(1 for f in edges if f["need"] == e["need"]) != 1:
            continue
        shadowed = any(
            f is not e and
            not f["needer_lines"].isdisjoint(e["needer_lines"]) and
            not f["provider_lines"].isdisjoint(e["provider_lines"])
            for f in edges)
        if not shadowed:
            del_edge = e
            break
    assert del_edge is not None
    edge_ids = {del_edge["needer"], del_edge["provider"]}

    # merge pair: adjacent in document order, exclusively-owned disjoint
    # spans, no edge in either direction between them, balanced enough that
    # neither half reaches Jaccard 0.8 against the merged node, and clear of
    # the deleted edge's endpoints
    ordered = sorted(nodes, key=lambda n: min(_lines(n)))
    merge_pair = None
    for x, y in zip(ordered, ordered[1:]):
        lx, ly = _lines(x), _lines(y)
        if x["id"] in edge_ids or y["id"] in edge_ids:
            continue
        if not lx.isdisjoint(ly):
            continue
        if any(line_counts[ln] > 1 for ln in lx | ly):
            continue
        union = len(lx | ly)
        if max(len(lx), len(ly)) / union >= gc.JACCARD_MIN:
            continue
        names_x = {nm(p) for p in x["provides"]}
        names_y = {nm(p) for p in y["provides"]}
        if ({nm(nd) for nd in x["needs"]} & names_y or
                {nm(nd) for nd in y["needs"]} & names_x):
            continue
        merge_pair = (x, y)
        break
    assert merge_pair is not None
    used = edge_ids | {merge_pair[0]["id"], merge_pair[1]["id"]}

    # strengthen: a 'should' in establishes, on a node not already used
    strengthen = next(n for n in nodes
                      if n["id"] not in used and
                      re.search(r"\bshould\b", n["establishes"], re.I))
    used.add(strengthen["id"])

    # cover a dangling: host any unused node; the fake provider must not sit
    # on lines where an A-edge whose needer overlaps a needer of the
    # dangling already lands, or a planted B-edge would be matched and
    # invisible in precision. GC-8 FIX: the guard is line-based (matching is
    # by line overlap — an id-based guard misses same-lines siblings), and
    # the dangling's needers must be clear of the other mutations so the
    # planted-edge count is exactly `needed_by`.
    dangle = host = None
    for d in danglings:
        if d["needed_by"] < 1:
            continue
        needer_ids = {n["id"] for n in nodes
                      if any(nm(nd) == d["name"] for nd in n["needs"])}
        if needer_ids & used:
            continue
        needer_ls = [_lines(by_id[i]) for i in needer_ids]
        host = next(
            (n for n in nodes
             if n["id"] not in used and n["id"] not in needer_ids and
             not any(not e["provider_lines"].isdisjoint(_lines(n)) and
                     any(not e["needer_lines"].isdisjoint(ls)
                         for ls in needer_ls)
                     for e in edges)), None)
        if host is not None:
            dangle = d
            break
    assert dangle is not None and host is not None
    return del_edge, merge_pair, strengthen, dangle, host, dang_names


def _mutate(golden, del_edge, merge_pair, strengthen, dangle, host):
    b = copy.deepcopy(golden)
    by_id = {n["id"]: n for n in b["nodes"]}

    x, y = by_id[merge_pair[0]["id"]], by_id[merge_pair[1]["id"]]
    merged = {"id": x["id"] + "+" + y["id"],
              "establishes": x["establishes"] + "\n" + y["establishes"],
              "needs": x["needs"] + y["needs"],
              "provides": x["provides"] + y["provides"],
              "spans": x["spans"] + y["spans"]}
    b["nodes"] = [n for n in b["nodes"] if n["id"] not in (x["id"], y["id"])]
    b["nodes"].append(merged)

    needer = by_id[del_edge["needer"]]
    needer["needs"] = [nd for nd in needer["needs"]
                       if nm(nd) != del_edge["need"]]

    s = by_id[strengthen["id"]]
    s["establishes"] = re.sub(r"\bshould\b", "must", s["establishes"],
                              count=1, flags=re.I)

    by_id[host["id"]]["provides"].append(
        {"name": dangle["name"], "prose": dangle["prose"]})
    return b, merged["id"]


# --------------------------------------------------------------------- RED

def test_mutated_compare_flags_exactly_the_four(golden, doc_len):
    del_edge, merge_pair, strengthen, dangle, host, dang_names = \
        _pick_targets(golden)
    mutated, merged_id = _mutate(golden, del_edge, merge_pair, strengthen,
                                 dangle, host)
    r = gc.compare(golden, mutated, doc_len)
    merge_ids = {merge_pair[0]["id"], merge_pair[1]["id"]}

    # 1. merge -> split/join (or misaligned), and nothing else leaves 1:1
    flagged_a = set(r["alignment"]["misaligned"]["a"])
    flagged_b = set(r["alignment"]["misaligned"]["b"])
    for g in r["alignment"]["split_join_groups"]:
        side = {"a": flagged_a, "b": flagged_b}
        side[g["one"]["graph"]].add(g["one"]["id"])
        side[g["many"]["graph"]].update(g["many"]["ids"])
    assert flagged_a == merge_ids
    assert flagged_b == {merged_id}

    # 2. deleted edge -> recall < 1 with exactly that edge unmatched
    assert r["edges"]["recall"] < 1.0
    assert [(e["needer"], e["provider"], e["need"])
            for e in r["edges"]["unmatched_a"]] == \
        [(del_edge["needer"], del_edge["provider"], del_edge["need"])]
    # planted provider -> precision flags one edge per needer occurrence.
    # GC-8 FIX: the expected count comes from the PLANTED mutation
    # (dangle["needed_by"]), never from the observed output, so a dead
    # precision signal fails here instead of passing vacuously.
    planted = dangle["needed_by"]
    assert len(r["edges"]["unmatched_b"]) == planted
    assert all(e["need"] == dangle["name"] and e["provider"] == host["id"]
               for e in r["edges"]["unmatched_b"])

    # 3. modal change -> exactly that pair in the seat queue
    assert [(q["a"], q["b"]) for q in r["modal_queue"]] == \
        [([strengthen["id"]], [strengthen["id"]])]
    # GC-2 (Matt's ruling 2026-08-11): seat work = the changed pair plus the
    # merge group; every untouched pair auto-agrees; mismatches sort first
    assert len(r["class2_queue"]) == 2
    assert r["class2_queue"][0]["kind"] == "pair"
    assert r["class2_queue"][0]["a"] == [strengthen["id"]]
    assert r["class2_queue"][0]["modal_mismatch"] is True
    assert r["class2_queue"][1]["kind"] == "group"
    assert set(r["class2_queue"][1]["a"]) == merge_ids
    assert r["class2_queue"][1]["b"] == [merged_id]
    assert r["class2_queue"][1]["modal_mismatch"] is False

    # 4. re-covered dangling -> dangling-set difference, exactly one concept
    assert [d["name"] for d in r["dangling"]["prose_only_a"]] == \
        [dangle["name"]]
    assert r["dangling"]["prose_only_b"] == []
    assert {d["name"] for d in r["dangling"]["b"]} == \
        dang_names - {dangle["name"]}

    # nothing outside the four planted defects reaches adjudication.
    # GC-8 FIX: the expected list is built from the planted mutations, not
    # read off the observed report.
    kinds = sorted(q["kind"] for q in r["adjudication_queue"])
    expected = ["dangling_mismatch"] + ["unmatched_edge"] * (1 + planted)
    assert kinds == sorted(expected)

    # boundary sanity: mutations never touched coverage
    assert r["uncovered"]["jaccard"] == 1.0
