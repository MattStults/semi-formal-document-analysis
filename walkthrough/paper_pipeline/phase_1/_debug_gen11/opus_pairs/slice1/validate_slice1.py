"""Coordinator-side re-derivation of stage 2 for slice 1. Never takes an agent's word.

Run from phase_1/:
    ../../../semi-formal-experiment/.venv/bin/python _debug_gen11/opus_pairs/slice1/validate_slice1.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, PHASE1)

import schema, checks  # noqa: E402

CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2", "node_corpus_all.json")
IDS = ["l1001_1107_n001", "l1001_1107_n007", "l1001_1107_n012",
       "l1108_1367_n004", "l1108_1367_n009"]


def main():
    rows = json.load(open(CORPUS))["clauses"]
    byid = {r["id"]: r for r in rows}
    corpus_ids = set(byid)
    worst = 0
    for cid in IDS:
        p = os.path.join(HERE, "out", cid + ".json")
        if not os.path.exists(p):
            print(f"--- {cid}: MODULE MISSING")
            worst = max(worst, 2)
            continue
        obj = json.load(open(p))
        mod, breaches = schema.validate_all(obj, cid, corpus_ids)
        res = checks.run_checks(obj, byid[cid], corpus_ids)
        print(f"--- {cid}  outcome={obj.get('outcome')!r} "
              f"asserts={len(obj.get('asserts') or [])} "
              f"ontology={len(obj.get('ontology') or [])} "
              f"claims={len(obj.get('claims') or [])} "
              f"beats={len(obj.get('beats') or [])} "
              f"closure={len(obj.get('closure') or [])} "
              f"requires={len(obj.get('requires') or [])} "
              f"inputs={len(obj.get('inputs') or [])}")
        print(f"    schema: constructed={mod is not None} breaches={len(breaches)}")
        for b in breaches:
            print("      BREACH:", getattr(b, "where", ""), getattr(b, "message", b))
            worst = max(worst, 2)
        print(f"    checks: result={res.outcome} findings={len(res.findings)}")
        for f in res.findings:
            print(f"      [{f.severity}] {getattr(f, 'check_id', '')} "
                  f"{getattr(f, 'where', '')}: {getattr(f, 'message', '')}")
            if f.severity == "error":
                worst = max(worst, 2)
    print(f"\nWORST = {worst}  (0 = clean, 2 = at least one error-severity)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
