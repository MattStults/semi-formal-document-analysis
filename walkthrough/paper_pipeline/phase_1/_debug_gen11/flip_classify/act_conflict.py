"""Mechanical pre-screen: does any clause carry an act that one draw FORBIDS and
another PERMITS/OBLIGES?  That is the only fully mechanical contradiction test.
Matches on the act functor name (arity/variable-insensitive), so it over-reports
rather than under-reports.

    ../../../../semi-formal-experiment/.venv/bin/python _debug_gen11/flip_classify/act_conflict.py
"""
import os, json, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(HERE, "flips.json")))

def functor(a):
    if not a: return None
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", str(a))
    return m.group(1) if m else str(a)

POS = {"permit", "oblige", "prefer"}
for r in j["records"]:
    seen = collections.defaultdict(set)          # functor -> statuses
    where = collections.defaultdict(set)
    for d in r["draws"]:
        for a in d["asserts"]:
            f = functor(a["act"])
            seen[f].add(a["status"]); where[f].add(d["run"])
    for f, ss in sorted(seen.items()):
        if "forbid" in ss and (ss & POS):
            print(f"HARD CONFLICT {r['clause']:22s} {f:45s} {sorted(ss)}")
        elif len(ss) > 1:
            print(f"  soft-diff    {r['clause']:22s} {f:45s} {sorted(ss)}")
