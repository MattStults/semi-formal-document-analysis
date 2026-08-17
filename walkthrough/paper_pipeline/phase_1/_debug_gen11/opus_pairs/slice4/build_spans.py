#!/usr/bin/env python3
"""Deterministic slice-4 selection + span prompt generation. No network."""
import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, P1)
import translate

CORPUS = os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")
CFG = os.path.join(P1, "resolve_runs/graph_v2/config_graph_nodes.json")

def eligible():
    rows = json.load(open(CORPUS))["clauses"]
    ids = [r["id"] for r in rows]
    a = set(os.path.basename(p).split(".")[0]
            for p in glob.glob(os.path.join(P1, "_debug_gen11/ds_opus_loop/out/*.json")))
    b = set(os.path.basename(p)[:-5]
            for p in glob.glob(os.path.join(P1, "_debug_gen11/reference_set/modules/*.json")))
    return rows, sorted(set(ids) - (a | b)), a, b

def main():
    rows, elig, a, b = eligible()
    stride = elig[3::5]                      # slice 4 of 5, start index 3
    idx = [round(i * (len(stride) - 1) / 4) for i in range(5)]
    picked = [stride[i] for i in idx]
    print("corpus", len(rows), "cohortA", len(a), "cohortB", len(b),
          "eligible", len(elig), "stride", len(stride))
    print("stride indices", idx)
    for cid in picked:
        print("  ", cid)
    cfg = json.load(open(CFG))
    cfg["corpus"]["path"] = "node_corpus_all.json"
    os.chdir(os.path.dirname(CFG))
    byid = {r["id"]: r for r in rows}
    for cid in picked:
        body, found, unres = translate.build_user(byid[cid], rows, cfg)
        out = os.path.join(HERE, "spans", cid + ".prompt_user.txt")
        open(out, "w", encoding="utf-8").write(body)
        print("wrote", out, len(body), "chars; xrefs", len(found), "unresolved", len(unres))
    json.dump({"eligible_size": len(elig), "stride_size": len(stride),
               "stride_indices": idx, "selected": picked},
              open(os.path.join(HERE, "selection.json"), "w"), indent=1)

main()
