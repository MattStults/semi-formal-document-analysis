#!/usr/bin/env python3
"""H1 — the graph-side half of the `PROVIDES` join seat 4c never had.

⛔ FREE. No model call, no write outside this directory.

The join rule is `stage4_interpret/provides_split.py`'s, unchanged and stated
in one place so the two cannot drift:

    needs_of[node]      = {name: prose}  from the graph node's own NEEDS block
    providers_of[name]  = {nodes that PROVIDE it}

    a name is BORROWED-eligible for `node` iff
        (B1) it is in `node`'s NEEDS block, and
        (B2) some OTHER node provides it.

`provides_split.py` is a top-level script that reads a specific stored run on
import, so it cannot be imported for this; the twelve lines it shares with
this file are the join above and nothing else.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.dirname(os.path.dirname(HERE))
GRAPH = os.path.join(PHASE1, "resolve_runs", "graph_v2", "runs", "ds7",
                     "root_graph.production.json")


def norm_id(nid):
    return nid.replace("-", "_").lower()


def load(graph_path=None):
    """`(needs_of, providers_of)` off the production decomposition graph."""
    graph = json.load(open(graph_path or GRAPH, encoding="utf-8"))
    nodes = {norm_id(n["id"]): n for n in graph["nodes"]}
    needs_of = {k: {d["name"]: d.get("prose", "") for d in n.get("needs") or []}
                for k, n in nodes.items()}
    providers_of = {}
    for k, n in nodes.items():
        for d in n.get("provides") or []:
            providers_of.setdefault(d["name"], set()).add(k)
    return needs_of, providers_of


def borrowed_concepts(node_id, needs_of, providers_of):
    """`((name, prose), …)` for ONE node — B1 and B2, sorted by name.

    ⚠️ B2 is enforced. A name in NEEDS that NO other node provides is a
    dangling instruction, not an established concept, and telling 4c it is
    established elsewhere would be asserting something the graph does not say.
    """
    k = norm_id(node_id)
    needs = needs_of.get(k) or {}
    return tuple(sorted(
        (name, prose) for name, prose in needs.items()
        if (providers_of.get(name, set()) - {k})))
