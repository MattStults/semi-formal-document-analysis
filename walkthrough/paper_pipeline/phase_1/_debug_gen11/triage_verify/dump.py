#!/usr/bin/env python3
"""Print a node for human reading: ESTABLISHES, licensed span text, missing
content words, and the surrounding document context."""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rederive as R


def show(nid, ctx=4):
    g = json.load(open(R.GRAPH))
    n = {x["id"]: x for x in g["nodes"]}[nid]
    cw = list(dict.fromkeys(R.words(n["establishes"])))
    lic = set(re.findall(r"[a-z]{4,}", R.licensed(n).lower()))
    miss = [w for w in cw if w not in lic]
    print("=" * 78)
    print(f"{nid}   missing {len(miss)}/{len(cw)} = {len(miss)/len(cw):.2f}")
    print(f"ESTABLISHES: {n['establishes']}")
    print(f"MISSING WORDS: {miss}")
    for sp in n["spans"]:
        a, b = sp["lines"]
        print(f"--- span L{a}-{b}  quote={'YES' if sp.get('quote') else 'no'}")
        if sp.get("quote"):
            print(f"    QUOTE: {sp['quote']}")
        print("    [doc context]")
        for i in range(max(1, a - ctx), min(len(R.DOCLINES), b + ctx) + 1):
            mark = ">" if a <= i <= b else " "
            print(f"    {mark}{i:5d}| {R.DOCLINES[i-1][:180]}")


if __name__ == "__main__":
    for nid in sys.argv[1:]:
        show(nid)
