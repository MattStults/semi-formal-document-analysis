#!/usr/bin/env python3
"""Round-4 scorer. Joins raw rulings (+ replacements) with the committed
draw, applies panel majorities, computes the registered cells and falsifier
checks F4/F5. Usage: round4_score.py <slug>."""
import json, sys, collections
slug = sys.argv[1]
pk = json.load(open(f"round4_{slug}_packets.json"))
rr = json.load(open(f"round4_{slug}_rulings_raw.json"))
rep = {}
try:
    rep = {(r["row"], r.get("instance")): r
           for r in json.load(open(f"round4_{slug}_replacements.json"))["rulings"]}
except FileNotFoundError:
    pass
rows = collections.defaultdict(dict)
for r in rr["rulings"]:
    rows[r["row"]][r.get("instance")] = r
for (row, inst), r in rep.items():
    rows[row][inst] = r          # replacement supersedes the malformed entry
panel = set(pk["panel_rows"])
side = {}
for i, p in enumerate(pk["packets"], 1):
    side[i] = p["side"]
node = {i: p["node"] for i, p in enumerate(pk["packets"], 1)}
verdict = {}
panel_splits = 0
overturns = 0
for i in range(1, len(pk["packets"]) + 1):
    if i in panel:
        vs = [rows[i][k]["verdict"] for k in ("a", "b", "c")]
        assert all(v in ("RELEVANT", "NOT_RELEVANT") for v in vs), (i, vs)
        maj = max(set(vs), key=vs.count)
        if len(set(vs)) > 1:
            panel_splits += 1
        if vs[0] != maj:
            overturns += 1       # instance-a as the single-equivalent
        verdict[i] = maj
    else:
        v = rows[i][None]["verdict"]
        assert v in ("RELEVANT", "NOT_RELEVANT"), (i, v)
        verdict[i] = v
cells = {}
eng = [i for i in verdict if side[i] == "E"]
noteng = [i for i in verdict if side[i] == "N"]
cells["engaged_precision_raw"] = sum(verdict[i] == "RELEVANT" for i in eng) / len(eng)
cells["decline_correctness_raw"] = sum(verdict[i] == "NOT_RELEVANT" for i in noteng) / len(noteng)
out = {"_": f"ROUND-4 {slug} scored cells (RAW; defensibility pass per amendment 1 runs on the misses next)",
       "n_engaged": len(eng), "n_not_engaged": len(noteng),
       "cells": cells,
       "misses": {"engaged_FP": sorted(node[i] for i in eng if verdict[i] == "NOT_RELEVANT"),
                  "not_engaged_FN": sorted(node[i] for i in noteng if verdict[i] == "RELEVANT")},
       "falsifiers": {"F4_panel_split_rate": panel_splits / len(panel),
                      "F5_overturn_rate": overturns / len(panel)},
       "verdicts_by_node": {node[i]: verdict[i] for i in verdict}}
json.dump(out, open(f"round4_{slug}_scored.json", "w"), indent=1)
slim = {k: v for k, v in out.items() if k != "verdicts_by_node"}
print(json.dumps(slim, indent=1))
