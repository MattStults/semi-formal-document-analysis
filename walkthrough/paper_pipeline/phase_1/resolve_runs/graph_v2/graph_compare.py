#!/usr/bin/env python3
"""Graph-equivalence comparator (GRAPH_EQUIVALENCE.md, pre-registered
2026-08-10): measurements 1, 3, 4 and the seat queue of measurement 2
(class2_queue: every non-identical 1:1 pair and every split/join group,
ordered by the modal pre-filter — Matt's ruling 2026-08-11, see compare()).

Names are NEVER compared across graphs (the replay runs showed ~0% name
convergence on converged concepts): every cross-graph test lives in
line-space; each graph's needs are resolved against its OWN provides.

Output is DESCRIPTIVE ONLY — no pass/fail verdict. The protocol's verdict
is a judgment-backed zero over the adjudication queue, not a threshold;
this tool builds the queue and the statistics beside it.

Usage: python3 graph_compare.py --a <graph.json> --b <graph.json>
       [--doc <model_spec.md>] [--out compare_report.json]
"""
import argparse
import json
import os
import re
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from recurse_driver import load_doc, nm, write_json   # noqa: E402
from sweep_modals import profile                      # noqa: E402

DOC = os.path.join(HERE, "..", "..", "..", "..", "..", "specs",
                   "openai-model-spec", "model_spec.md")

JACCARD_MIN = 0.8      # 1:1 and split/join threshold (pre-registered)
GROUP_MAX = 3          # split/join covers a node with 2–3 of the other graph


# ---------------------------------------------------------------- geometry

def node_lines(node):
    s = set()
    for sp in node.get("spans", []):
        a, b = sp["lines"]
        s.update(range(a, b + 1))
    return frozenset(s)


def jaccard(x, y):
    u = len(x | y)
    return len(x & y) / u if u else 0.0


def est_tokens(text):
    """Normalized token set of an establishes string (for GC-1 tie-breaks)."""
    return frozenset(re.findall(r"[a-z0-9']+", text.lower()))


def runs(lineset):
    """Compact a line-set to [lo, hi] runs for the report."""
    out, prev = [], None
    for n in sorted(lineset):
        if prev is not None and n == prev + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
        prev = n
    return out


# ------------------------------------------------- measurement 1: alignment

def align(nodes_a, nodes_b):
    """Classify every node 1:1 / split_join / misaligned per the protocol.
    A split/join group pairs one coarse node with the 2–3 nodes of the other
    graph whose union reaches the same Jaccard bar; both sides of a group
    carry the split_join class."""
    la = {n["id"]: node_lines(n) for n in nodes_a}
    lb = {n["id"]: node_lines(n) for n in nodes_b}
    by_line_b = {}
    for bid, ls in lb.items():
        for line in ls:
            by_line_b.setdefault(line, []).append(bid)
    by_line_a = {}
    for aid, ls in la.items():
        for line in ls:
            by_line_a.setdefault(line, []).append(aid)

    cls_a = {n["id"]: None for n in nodes_a}
    cls_b = {n["id"]: None for n in nodes_b}
    pairs, groups = [], []

    def candidates(lines, by_line):
        seen = {}
        for line in lines:
            for other in by_line.get(line, []):
                seen[other] = seen.get(other, 0) + 1
        return sorted(seen, key=lambda o: (-seen[o], o))

    # pass 1: 1:1 as an injective matching over qualifying pairs.
    # Several nodes may own the SAME line-set (multiple claims on one span,
    # 28 such groups in the golden); a best-single-partner rule would leave
    # all but one of them unmatched even against an identical graph.
    # GC-1 FIX: Jaccard ties — in particular whole identical-line-set groups,
    # where every cross pairing scores 1.0 — are broken by establishes
    # similarity (normalized token overlap), never by node-id sort order, so
    # a content-identical graph pairs claim-to-claim, not id-to-id.
    ta = {n["id"]: est_tokens(n["establishes"]) for n in nodes_a}
    tb = {n["id"]: est_tokens(n["establishes"]) for n in nodes_b}
    qualifying = []
    for aid, ls in la.items():
        for bid in candidates(ls, by_line_b):
            j = jaccard(ls, lb[bid])
            if j >= JACCARD_MIN:
                qualifying.append((j, jaccard(ta[aid], tb[bid]), aid, bid))
    qualifying.sort(key=lambda t: (-t[0], -t[1], t[2], t[3]))
    match_a, match_b = {}, {}          # aid -> bid, bid -> aid
    jac = {}
    adjacency = {}                     # aid -> [bid ...] in preference order
    for j, s, aid, bid in qualifying:
        jac[(aid, bid)] = j
        adjacency.setdefault(aid, []).append(bid)
        if aid not in match_a and bid not in match_b:
            match_a[aid] = bid
            match_b[bid] = aid

    # GC-5 FIX: the greedy pass can "steal" a node's only qualifying partner
    # (misfiling a true 1:1 as split/join with a malformed concatenated
    # comparison downstream); augmenting-path passes grow the matching to
    # maximum cardinality over the qualifying subgraph.
    def augment(aid, visited):
        for bid in adjacency.get(aid, []):
            if bid in visited:
                continue
            visited.add(bid)
            prev = match_b.get(bid)
            if prev is None or augment(prev, visited):
                match_b[bid] = aid
                match_a[aid] = bid
                return True
        return False

    for aid in sorted(adjacency):
        if aid not in match_a:
            augment(aid, set())

    for aid in sorted(match_a):
        bid = match_a[aid]
        cls_a[aid] = cls_b[bid] = "one_to_one"
        pairs.append({"a": aid, "b": bid,
                      "jaccard": round(jac[(aid, bid)], 3)})

    # passes 2/3: a still-unclassified node covered by 2–3 of the other side.
    # GC-4 FIX: test every 2- and 3-subset of the top candidates (at most
    # C(5,2)+C(5,3)=20 union Jaccards) instead of only prefixes of the ranked
    # list — a high-overlap candidate that also sprawls elsewhere ("poison")
    # no longer blocks a perfect cover. Best union Jaccard wins; ties go to
    # the smaller group, then lexicographic ids, for determinism.
    def grouping(coarse_lines, other_lines, by_line, one_graph, many_graph,
                 cls_one, cls_many, coarse_id):
        cand = candidates(coarse_lines, by_line)[:GROUP_MAX + 2]
        best = None
        for k in range(2, GROUP_MAX + 1):
            for members in combinations(cand, k):
                union = frozenset().union(*(other_lines[m] for m in members))
                j = jaccard(coarse_lines, union)
                if j < JACCARD_MIN:
                    continue
                key = (-j, len(members), tuple(sorted(members)))
                if best is None or key < best[0]:
                    best = (key, list(members), j)
        if best is None:
            return False
        _, members, j = best
        cls_one[coarse_id] = "split_join"
        for m in members:
            if cls_many[m] is None:
                cls_many[m] = "split_join"
        groups.append({"one": {"graph": one_graph, "id": coarse_id},
                       "many": {"graph": many_graph, "ids": members},
                       "union_jaccard": round(j, 3)})
        return True

    for aid, ls in la.items():
        if cls_a[aid] is None:
            grouping(ls, lb, by_line_b, "a", "b", cls_a, cls_b, aid)
    for bid, ls in lb.items():
        if cls_b[bid] is None:
            grouping(ls, la, by_line_a, "b", "a", cls_b, cls_a, bid)

    for cls in (cls_a, cls_b):
        for k in cls:
            if cls[k] is None:
                cls[k] = "misaligned"
    return {"lines_a": la, "lines_b": lb, "cls_a": cls_a, "cls_b": cls_b,
            "pairs": pairs, "groups": groups}


RANK = {"one_to_one": 0, "split_join": 1, "misaligned": 2}


def line_mass(lines_by_id, cls, doc_len):
    """Per-line class = best class among that line's owners."""
    best = {}
    for nid, ls in lines_by_id.items():
        for line in ls:
            c = cls[nid]
            if line not in best or RANK[c] < RANK[best[line]]:
                best[line] = c
    mass = {"one_to_one": 0, "split_join": 0, "misaligned": 0}
    for c in best.values():
        mass[c] += 1
    out = {k: round(v / doc_len, 4) for k, v in mass.items()}
    out["unowned"] = round((doc_len - len(best)) / doc_len, 4)
    return out


# ----------------------------------------------------- measurement 3: edges

def build_edges(nodes):
    """Resolve each need against THIS graph's provides, by name. Names never
    cross the graph boundary; the edge is its two line-regions."""
    providers = {}
    for n in nodes:
        for p in n.get("provides", []):
            providers.setdefault(nm(p), []).append(n["id"])
    lines = {n["id"]: node_lines(n) for n in nodes}
    edges, dangling = [], {}
    for n in nodes:
        for need in n.get("needs", []):
            name = nm(need)
            prose = need.get("prose", "") if isinstance(need, dict) else ""
            if name in providers:
                for pid in providers[name]:
                    edges.append({"needer": n["id"], "provider": pid,
                                  "need": name, "prose": prose,
                                  "needer_lines": lines[n["id"]],
                                  "provider_lines": lines[pid]})
            else:
                d = dangling.setdefault(name, {"name": name, "prose": prose,
                                               "needed_by": 0})
                d["needed_by"] += 1
    return edges, list(dangling.values())


def match_edges(edges_x, edges_y):
    """Edge of X matched in Y iff some Y-edge overlaps both regions."""
    out = []
    for e in edges_x:
        hit = any(not e["needer_lines"].isdisjoint(f["needer_lines"]) and
                  not e["provider_lines"].isdisjoint(f["provider_lines"])
                  for f in edges_y)
        out.append(hit)
    return out


def edge_public(e):
    return {"needer": e["needer"], "provider": e["provider"],
            "need": e["need"], "prose": e["prose"],
            "needer_lines": runs(e["needer_lines"]),
            "provider_lines": runs(e["provider_lines"])}


# ------------------------------------------- measurement 4: boundary objects

def uncovered_lines(graph):
    s = set()
    for u in graph.get("uncovered", []):
        a, b = u["lines"]
        s.update(range(a, b + 1))
    return s


def norm_prose(s):
    return re.sub(r"\s+", " ", s).strip().lower()


# ------------------------------------------------------------------ compare

def compare(graph_a, graph_b, doc_len, path_a="a", path_b="b"):
    nodes_a, nodes_b = graph_a["nodes"], graph_b["nodes"]
    est_a = {n["id"]: n["establishes"] for n in nodes_a}
    est_b = {n["id"]: n["establishes"] for n in nodes_b}

    al = align(nodes_a, nodes_b)
    adjq = []
    for graph, cls, lines, est in (("a", al["cls_a"], al["lines_a"], est_a),
                                   ("b", al["cls_b"], al["lines_b"], est_b)):
        for nid, c in cls.items():
            if c == "misaligned":
                adjq.append({"kind": "misaligned_node", "graph": graph,
                             "id": nid, "lines": runs(lines[nid]),
                             "establishes": est[nid]})

    # measurement-2 queue. GC-2 RULING (Matt's ruling 2026-08-11 via the
    # session record): aligned 1:1 pairs whose NORMALIZED establishes are
    # IDENTICAL auto-agree with no seat; ALL other 1:1 pairs and every
    # split/join group are seat work and go to class2_queue. The modal
    # pre-filter ORDERS that queue (mismatches first) but no longer GATES
    # it — equal modal profiles over different conditions ("must refuse ...
    # weapons" vs "must refuse ... self-harm") is exactly the
    # false-equivalence-by-omission this closes. The review's alternative
    # (b) — a ruling restricting measurement 2 to the modal pre-filter's
    # routes — is rejected by name. modal_queue remains as the pre-filter's
    # own listing (a subset of class2_queue).
    modal_queue, class2_queue = [], []
    class2_auto_agreed = 0
    for p in al["pairs"]:
        ea, eb = est_a[p["a"]], est_b[p["b"]]
        if norm_prose(ea) == norm_prose(eb):
            class2_auto_agreed += 1
            continue
        pa, pb = profile(ea), profile(eb)
        class2_queue.append({"kind": "pair", "a": [p["a"]], "b": [p["b"]],
                             "modal_mismatch": pa != pb,
                             "profile_a": pa, "profile_b": pb,
                             "establishes_a": ea, "establishes_b": eb})
        if pa != pb:
            modal_queue.append({"a": [p["a"]], "b": [p["b"]],
                                "profile_a": pa, "profile_b": pb})
    for g in al["groups"]:
        one, many = g["one"], g["many"]
        est_one = {"a": est_a, "b": est_b}[one["graph"]]
        est_many = {"a": est_a, "b": est_b}[many["graph"]]
        lines_many = {"a": al["lines_a"], "b": al["lines_b"]}[many["graph"]]
        ordered = sorted(many["ids"], key=lambda i: min(lines_many[i]))
        eo = est_one[one["id"]]
        em = "\n".join(est_many[i] for i in ordered)
        po, pm = profile(eo), profile(em)
        ids_a = [one["id"]] if one["graph"] == "a" else ordered
        ids_b = ordered if one["graph"] == "a" else [one["id"]]
        prof_a, prof_b = (po, pm) if one["graph"] == "a" else (pm, po)
        ea, eb = (eo, em) if one["graph"] == "a" else (em, eo)
        class2_queue.append({"kind": "group", "a": ids_a, "b": ids_b,
                             "modal_mismatch": po != pm,
                             "profile_a": prof_a, "profile_b": prof_b,
                             "establishes_a": ea, "establishes_b": eb})
        if po != pm:
            modal_queue.append({"a": ids_a, "b": ids_b,
                                "profile_a": prof_a, "profile_b": prof_b})
    # stable sort: modal mismatches first, otherwise original order
    class2_queue.sort(key=lambda q: 0 if q["modal_mismatch"] else 1)

    edges_a, dang_a = build_edges(nodes_a)
    edges_b, dang_b = build_edges(nodes_b)
    hit_a = match_edges(edges_a, edges_b)
    hit_b = match_edges(edges_b, edges_a)
    unmatched_a = [edge_public(e) for e, h in zip(edges_a, hit_a) if not h]
    unmatched_b = [edge_public(e) for e, h in zip(edges_b, hit_b) if not h]
    for graph, lst in (("a", unmatched_a), ("b", unmatched_b)):
        for e in lst:
            adjq.append({"kind": "unmatched_edge", "graph": graph, **e})

    # GC-3 FIX: any-overlap matching cannot see the deletion of a "shadowed"
    # edge (both its regions overlapped by some other edge of its own graph —
    # 76/512 = 14.8% on the golden). Two disclosures: (1) a STRICT secondary
    # metric — an edge is strictly matched only when the other graph connects
    # the exact 1:1-aligned partner nodes — reported alongside the permissive
    # pre-registered one (which keeps driving the adjudication queue); (2) the
    # shadowed edges themselves, counted and listed per graph, so the verdict
    # memo carries the instrument's known resolution limit.
    a2b = {p["a"]: p["b"] for p in al["pairs"]}
    b2a = {p["b"]: p["a"] for p in al["pairs"]}
    keys_a = {(e["needer"], e["provider"]) for e in edges_a}
    keys_b = {(e["needer"], e["provider"]) for e in edges_b}

    def strict_match(edges_x, x2y, keys_y):
        return [(x2y.get(e["needer"]), x2y.get(e["provider"])) in keys_y
                for e in edges_x]

    strict_a = strict_match(edges_a, a2b, keys_b)
    strict_b = strict_match(edges_b, b2a, keys_a)

    def shadowed(edges_x):
        return [edge_public(e) for e in edges_x if any(
            f is not e and
            not f["needer_lines"].isdisjoint(e["needer_lines"]) and
            not f["provider_lines"].isdisjoint(e["provider_lines"])
            for f in edges_x)]

    shadow_a, shadow_b = shadowed(edges_a), shadowed(edges_b)

    unc_a, unc_b = uncovered_lines(graph_a), uncovered_lines(graph_b)
    only_a_runs, only_b_runs = runs(unc_a - unc_b), runs(unc_b - unc_a)
    # GC-6 FIX: class-4 line disagreements are part of "every adjudicated
    # disagreement from classes 1–4" — a verdict process that works the queue
    # must see them, not only the printed diff.
    for graph, rr in (("a", only_a_runs), ("b", only_b_runs)):
        for lo, hi in rr:
            adjq.append({"kind": "uncovered_mismatch", "graph": graph,
                         "lines": [lo, hi]})

    # danglings: exact-prose matches agree mechanically; the rest is a
    # concept-level question and goes to adjudication
    pa = {norm_prose(d["prose"]): d for d in dang_a}
    pb = {norm_prose(d["prose"]): d for d in dang_b}
    prose_only_a = [pa[k] for k in sorted(set(pa) - set(pb))]
    prose_only_b = [pb[k] for k in sorted(set(pb) - set(pa))]
    for graph, lst in (("a", prose_only_a), ("b", prose_only_b)):
        for d in lst:
            adjq.append({"kind": "dangling_mismatch", "graph": graph, **d})

    def counts(cls):
        c = {"one_to_one": 0, "split_join": 0, "misaligned": 0}
        for v in cls.values():
            c[v] += 1
        return c

    return {
        "protocol": "GRAPH_EQUIVALENCE.md 2026-08-10",
        "a": path_a, "b": path_b, "doc_lines": doc_len,
        "alignment": {
            "counts": {"a": counts(al["cls_a"]), "b": counts(al["cls_b"])},
            "pairs_1to1": al["pairs"],
            "split_join_groups": al["groups"],
            "misaligned": {
                "a": sorted(i for i, c in al["cls_a"].items()
                            if c == "misaligned"),
                "b": sorted(i for i, c in al["cls_b"].items()
                            if c == "misaligned")},
            "line_mass": {
                "a": line_mass(al["lines_a"], al["cls_a"], doc_len),
                "b": line_mass(al["lines_b"], al["cls_b"], doc_len)},
        },
        "edges": {
            "a_total": len(edges_a), "b_total": len(edges_b),
            "recall": round(sum(hit_a) / len(edges_a), 4) if edges_a else 1.0,
            "precision": (round(sum(hit_b) / len(edges_b), 4)
                          if edges_b else 1.0),
            "unmatched_a": unmatched_a, "unmatched_b": unmatched_b,
            # GC-3: strict secondary metric (exact 1:1-aligned-pair match)
            "strict_recall": (round(sum(strict_a) / len(edges_a), 4)
                              if edges_a else 1.0),
            "strict_precision": (round(sum(strict_b) / len(edges_b), 4)
                                 if edges_b else 1.0),
            "strict_unmatched_a": [edge_public(e) for e, h
                                   in zip(edges_a, strict_a) if not h],
            "strict_unmatched_b": [edge_public(e) for e, h
                                   in zip(edges_b, strict_b) if not h],
            # GC-3: known resolution limit of the permissive metric
            "shadowed_edges": {
                "a": {"count": len(shadow_a), "edges": shadow_a},
                "b": {"count": len(shadow_b), "edges": shadow_b}},
        },
        "uncovered": {
            "jaccard": round(jaccard(frozenset(unc_a), frozenset(unc_b)), 4),
            "only_a": only_a_runs, "only_b": only_b_runs,
        },
        "dangling": {
            "a": dang_a, "b": dang_b,
            "prose_only_a": prose_only_a, "prose_only_b": prose_only_b,
        },
        "modal_queue": modal_queue,
        "class2_queue": class2_queue,
        "class2_auto_agreed": class2_auto_agreed,
        "adjudication_queue": adjq,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--doc", default=DOC)
    ap.add_argument("--out", default=os.path.join(HERE,
                                                  "compare_report.json"))
    args = ap.parse_args()
    doc_len = len(load_doc(args.doc))
    report = compare(json.load(open(args.a)), json.load(open(args.b)),
                     doc_len, args.a, args.b)
    write_json(args.out, report)
    c = report["alignment"]["counts"]
    print(f"nodes a={sum(c['a'].values())} b={sum(c['b'].values())}  "
          f"1:1 a/b={c['a']['one_to_one']}/{c['b']['one_to_one']}  "
          f"misaligned a/b={c['a']['misaligned']}/{c['b']['misaligned']}")
    print(f"edge recall={report['edges']['recall']} "
          f"precision={report['edges']['precision']}  "
          f"strict recall={report['edges']['strict_recall']} "
          f"precision={report['edges']['strict_precision']}  "
          f"uncovered jaccard={report['uncovered']['jaccard']}")
    sh = report["edges"]["shadowed_edges"]
    print(f"shadowed edges a/b={sh['a']['count']}/{sh['b']['count']}")
    print(f"modal queue={len(report['modal_queue'])}  "
          f"class2 queue={len(report['class2_queue'])} "
          f"(auto-agreed {report['class2_auto_agreed']})  "
          f"adjudication queue={len(report['adjudication_queue'])}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
