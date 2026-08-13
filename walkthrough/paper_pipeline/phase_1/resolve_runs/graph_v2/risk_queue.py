#!/usr/bin/env python3
"""Risk queue (Matt's design, 2026-08-13): rank every judgment-bearing
decision in a finished graph by deterministic risk signals so frontier
review is dispatched down a SHORT list instead of over the whole graph.
Offline, no spend. Usage: risk_queue.py runs/ds7 -> runs/ds7/risk_queue.json
"""
import json
import os
import re
import sys


def sim(a, b):
    ta = set(re.findall(r"[a-z]{4,}", (a or "").lower()))
    tb = set(re.findall(r"[a-z]{4,}", (b or "").lower()))
    return len(ta & tb) / max(len(ta | tb), 1)


def build(run_dir):
    g = json.load(open(os.path.join(run_dir, "root_graph.json")))
    nodes = g["nodes"]
    prov_prose, fanout = {}, {}
    for n in nodes:
        for p in n.get("provides", []):
            if isinstance(p, dict):
                prov_prose.setdefault(p["name"], p.get("prose", ""))
    for n in nodes:
        for d in n.get("needs", []):
            name = d.get("name") if isinstance(d, dict) else d
            fanout[name] = fanout.get(name, 0) + 1
    items = []
    # 1. applied renames -- from the ROOT graph AND every interior unwind
    # artifact (pre-ds7 review finding 5: interior verdicts never
    # propagate to root; the queue walks the run tree instead)
    import glob
    verdicts = list(g.get("rename_seat_verdicts", []))
    for p in glob.glob(os.path.join(run_dir, "**", "graph.json"),
                       recursive=True):
        try:
            verdicts += json.load(open(p)).get("rename_seat_verdicts", [])
        except Exception:
            pass
    for v in verdicts:
        if v.get("verdict") != "same_concept":
            continue
        p = v.get("proposal", {})
        name = p.get("rename_to") or p.get("name")
        items.append({
            "kind": "seat_accepted_rename", "detail": p,
            "grounds": v.get("grounds", ""), "where": v.get("where", ""),
            "risk": round(1.0 + 0.1 * fanout.get(name, 0), 2)})
    # 2. every surviving edge with near-zero name-prose similarity
    for n in nodes:
        for d in n.get("needs", []):
            if not isinstance(d, dict):
                continue
            pp = prov_prose.get(d.get("name"))
            if pp is None:
                continue
            s = sim(d.get("prose", ""), pp)
            if s < 0.1:
                items.append({
                    "kind": "low_sim_edge",
                    "detail": {"needer": n["id"], "name": d["name"],
                               "prose": d.get("prose", "")[:120]},
                    "risk": round(0.8 + 0.1 * fanout.get(d["name"], 0)
                                  - s, 2)})
    # 3. dropped merges (redundant pairs kept -- verify no real loss)
    for m in g.get("dropped_merges", []):
        items.append({"kind": "dropped_merge", "detail": m, "risk": 0.6})
    # 4. descend near-misses (highest-sim unaccepted candidates)
    for nm_ in g.get("descend_near_misses", []):
        top = (nm_.get("candidates") or [{}])[0]
        items.append({"kind": "dangling_near_miss", "detail": nm_,
                      "risk": round(0.4 + (top.get("sim") or 0), 2)})
    # 5. modal drift verdicts (run-local file; produced by running
    # modal_adjudicate.py against THIS run -- ds6's verdicts name ds6
    # node ids and do not transfer)
    path = os.path.join(run_dir, "modal_adjudication.json")
    if os.path.exists(path):
        for x in json.load(open(path)):
            if x.get("verdict") == "drifted":
                items.append({"kind": "modal_drift",
                              "detail": {"id": x.get("id"),
                                         "grounds": x.get("grounds", "")},
                              "risk": 0.9})
    # 6. broken promises from health
    hp = os.path.join(run_dir, "health.jsonl")
    if os.path.exists(hp):
        for line in open(hp):
            row = json.loads(line)
            for name in row.get("broken_promises", []) or []:
                items.append({"kind": "broken_promise",
                              "detail": {"unwind": row.get("artifact"),
                                         "name": name},
                              "risk": round(0.7 + 0.1 * fanout.get(name, 0),
                                            2)})
    items.sort(key=lambda x: -x["risk"])
    out = {"run": run_dir, "items": items,
           "counts": {}, "total": len(items)}
    for x in items:
        out["counts"][x["kind"]] = out["counts"].get(x["kind"], 0) + 1
    path = os.path.join(run_dir, "risk_queue.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"{len(items)} risk items -> {path}; by kind: {out['counts']}")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "runs/ds6")
