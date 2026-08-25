#!/usr/bin/env python3
"""qc_separability_census.py — Matt's separability test, committed before
the emergent annotations exist. Deterministic, $0.

Signatures at three strictness levels, per seat and on the two-seat
dimension-set intersection (conservative consensus):
  L1 dimension-set only (which handles are used)
  L2 dimension + exact-string value (lowercased/stripped; no fuzzy merge)
A COLLISION = two definitions with identical signatures. Collisions are
the insufficiency signal ONLY when the two definitions are genuinely
different behaviours — every collision is listed with both texts'
sources for that judgment, none is auto-excused."""
import json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def sig_dims(a):
    return tuple(sorted(a))


def sig_vals(a):
    return tuple(sorted((d, str(v).strip().lower()) for d, v in a.items()))


def census(anns, name, corpus):
    src = {e["id"]: e["source"] for e in corpus["entries"]}
    out = {}
    for level, fn in (("L1_dims", sig_dims), ("L2_dims+values", sig_vals)):
        groups = defaultdict(list)
        for i, a in anns.items():
            groups[fn(a)].append(i)
        coll = {str(k): v for k, v in groups.items() if len(v) > 1}
        out[level] = {
            "distinct_signatures": len(groups),
            "n": len(anns),
            "separability": round(len(groups) / len(anns), 3),
            "collision_groups": len(coll),
            "collisions": {k: [{"id": i, "source": src.get(i)} for i in v]
                           for k, v in coll.items()},
        }
    return {name: out}


def main():
    corpus = json.load(open(os.path.join(HERE, "query_class_corpus.json")))
    A = json.load(open(os.path.join(HERE, "qc_emergent_ann_A.json")))["annotations"]
    B = json.load(open(os.path.join(HERE, "qc_emergent_ann_B.json")))["annotations"]
    res = {}
    res.update(census(A, "seatA", corpus))
    res.update(census(B, "seatB", corpus))
    inter = {i: {d: A[i][d] for d in A[i] if d in B.get(i, {})}
             for i in A if i in B}
    inter = {i: a for i, a in inter.items() if a}
    res.update(census(inter, "consensus_dim_intersection", corpus))
    res["_"] = ("SEPARABILITY CENSUS over the emergent 24-dim schema. "
                "L2 exact-value collisions between different-source, "
                "different-construct definitions are the measured "
                "insufficiency; same-construct duplicates across sources "
                "are corpus redundancy, judged per collision, not "
                "auto-excused.")
    json.dump(res, open(os.path.join(HERE, "QC_SEPARABILITY_CENSUS.json"), "w"),
              indent=1)
    for k in ("seatA", "seatB", "consensus_dim_intersection"):
        for lvl in ("L1_dims", "L2_dims+values"):
            r = res[k][lvl]
            print(f"{k} {lvl}: {r['distinct_signatures']}/{r['n']} distinct "
                  f"({r['separability']}), {r['collision_groups']} collision groups")


if __name__ == "__main__":
    main()
