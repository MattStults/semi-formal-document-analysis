#!/usr/bin/env python3
"""⚠️ TIER 2 — THE ADJUDICATED MEASURES.  Every number this file prints rests on
a judgment of mine and is labelled as such wherever it is quoted.

It does no adjudicating itself.  It consumes `blind/verdicts.json` — written by
me from the BLIND pool, against criteria frozen in `key/frozen_key.json` before
any reply existed — unseals `blind/_sealed_map.json`, and tabulates.

⛔ `unseal` refuses while any pooled reply is unscored.  That is the whole point
of the file: the mapping from opaque id to cell cannot be consulted until every
verdict is written.

VERDICT VOCABULARY, fixed in `key/build_key.py`:
  identified        a FIX line names the field AND the change the item requires
  identified+wrong  names the right field, the WRONG change  -> a FALSE CHARGE,
                    counted against H5 and NOT counted as identification
  not_identified    no line matches
  repaired          the post module satisfies the item's `repair_if`
  unrepaired        identified and the post module does not satisfy `repair_if`

READ-ONLY except this directory.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLIND = os.path.join(HERE, "blind")


def load():
    v = json.load(open(os.path.join(BLIND, "verdicts.json"), encoding="utf-8"))
    pool = json.load(open(os.path.join(BLIND, "pool.json"), encoding="utf-8"))
    unscored = [r["reply"] for r in pool if r["reply"] not in v]
    if unscored:
        raise SystemExit(
            f"REFUSED to unseal: {len(unscored)} pooled replies are unscored "
            f"({', '.join(unscored[:5])}...). The mapping stays sealed.")
    m = json.load(open(os.path.join(BLIND, "_sealed_map.json"),
                       encoding="utf-8"))
    return v, pool, m


def main():
    verdicts, pool, seal = load()
    key = json.load(open(os.path.join(HERE, "key", "frozen_key.json"),
                         encoding="utf-8"))
    cells = {}
    for r in pool:
        oid = r["reply"]
        cell = seal[oid]["cell"]
        cid = seal[oid]["clause_id"]
        v = verdicts[oid]
        c = cells.setdefault(cell, {"clauses": [], "frozen": 0, "identified": 0,
                                    "repaired": 0, "false_charges": 0,
                                    "fix_lines": 0, "per_clause": {},
                                    "broken_blind": 0})
        c["clauses"].append(cid)
        c["broken_blind"] += bool(seal[oid]["broken_blind"])
        n_frozen = len(key[cid])
        ident = [k for k, s in v["items"].items() if s.get("identified")]
        rep = [k for k in ident if v["items"][k].get("repaired")]
        c["frozen"] += n_frozen
        c["identified"] += len(ident)
        c["repaired"] += len(rep)
        c["false_charges"] += len(v.get("false_charges", []))
        c["fix_lines"] += v.get("n_fix", 0)
        c["per_clause"][cid] = {"frozen": n_frozen, "identified": len(ident),
                                "repaired": len(rep),
                                "false_charges": len(v.get("false_charges", [])),
                                "fix": v.get("n_fix", 0),
                                "items_identified": sorted(ident),
                                "items_repaired": sorted(rep)}

    inter = set.intersection(*[set(c["clauses"]) for c in cells.values()])
    out = {"cells": cells, "intersection": sorted(inter), "paired": {}}
    for name, c in cells.items():
        f = i = r = 0
        for cid in inter:
            p = c["per_clause"][cid]
            f += p["frozen"]
            i += p["identified"]
            r += p["repaired"]
        out["paired"][name] = {"clauses": len(inter), "frozen": f,
                               "identified": i, "repaired": r,
                               "repair_given_id": (r / i) if i else None}

    # ⭐ THE ADJUDICATION-FREE IDENTIFICATION NUMBER (RULING_02).  Computed from
    # the anchor groups frozen and hashed before the first API call, on replies
    # the scorer cannot distinguish.  Coarse in both directions -- it counts a
    # line that names the right field with the WRONG change, and misses a
    # correct finding phrased around the anchors -- but no judgment of mine
    # enters it, and it cannot be bent toward a cell without editing a hashed
    # file.  Reported BESIDE the adjudicated rate for every cell.
    cand = json.load(open(os.path.join(BLIND, "candidates.json"),
                          encoding="utf-8"))
    pre = {}
    for oid, rec in cand.items():
        cell = seal[oid]["cell"]
        d = pre.setdefault(cell, {"frozen": 0, "hit": 0, "paired_frozen": 0,
                                  "paired_hit": 0})
        p = seal[oid]["clause_id"] in inter
        for it in rec["items"]:
            d["frozen"] += 1
            d["hit"] += bool(it["candidates"])
            if p:
                d["paired_frozen"] += 1
                d["paired_hit"] += bool(it["candidates"])
    out["prefilter_ADJUDICATION_FREE"] = pre
    print("⭐ PREFILTER — ADJUDICATION-FREE (frozen anchors, hashed pre-call)")
    for name, d in pre.items():
        print(f"{name:6s} own {d['hit']:3d}/{d['frozen']:3d} "
              f"({100*d['hit']/max(d['frozen'],1):4.1f}%)   paired "
              f"{d['paired_hit']:3d}/{d['paired_frozen']:3d} "
              f"({100*d['paired_hit']/max(d['paired_frozen'],1):4.1f}%)")

    print("\nOWN SAMPLE (⚠️ adjudicated)")
    print(f"{'cell':6s} {'cl':>3s} {'frozen':>7s} {'ident':>13s} "
          f"{'repaired':>13s} {'rep|ID':>8s} {'falseChg':>9s}")
    for name, c in cells.items():
        i, f, r = c["identified"], c["frozen"] or 1, c["repaired"]
        print(f"{name:6s} {len(c['clauses']):3d} {c['frozen']:7d} "
              f"{i:5d} ({100*i/f:4.1f}%) {r:5d} ({100*r/f:4.1f}%) "
              f"{(100*r/i if i else 0):7.1f}% {c['false_charges']:9d}")
    print(f"\nPAIRED on the {len(inter)} clauses ALL cells completed "
          f"(⚠️ adjudicated)")
    for name, p in out["paired"].items():
        f = p["frozen"] or 1
        print(f"{name:6s} frozen {p['frozen']:3d}  ident {p['identified']:3d} "
              f"({100*p['identified']/f:4.1f}%)  repaired {p['repaired']:3d} "
              f"({100*p['repaired']/f:4.1f}%)  rep|ID "
              f"{(100*p['repair_given_id'] if p['repair_given_id'] else 0):.0f}%")
    json.dump(out, open(os.path.join(HERE, "score.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
