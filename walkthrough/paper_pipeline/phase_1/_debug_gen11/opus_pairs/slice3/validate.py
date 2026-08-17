#!/usr/bin/env python3
"""Stage-2 validation for slice3 modules. Coordinator-run; agents may run it too.

    ../../../../../../semi-formal-experiment/.venv/bin/python validate.py <id> [...]
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, PHASE1)
import translate, schema, checks  # noqa: E402

CFG = os.path.join(PHASE1, "resolve_runs", "graph_v2", "config_corpus_all.json")


def main(ids):
    cfg = translate.load_config(CFG)
    rows = translate.load_corpus(cfg)
    idk = cfg["corpus"]["id_key"]
    by = {r[idk]: r for r in rows}
    corpus_ids = set(by)
    rc = 0
    for cid in ids:
        p = os.path.join(HERE, "out", f"{cid}.json")
        print("=" * 70)
        print(cid)
        if not os.path.exists(p):
            print("  MISSING", p); rc = 1; continue
        obj = json.load(open(p))
        mod, breaches = schema.validate_all(
            obj, clause_id=cid, known_clause_ids=corpus_ids)
        print(f"  schema.validate_all: {len(breaches)} breach(es)"
              f"{'  [MODULE DID NOT CONSTRUCT]' if mod is None else ''}")
        for e in breaches:
            print("   BREACH", e); rc = 1
        if mod is None:
            rc = 1
            continue
        row = by[cid]
        clause = {"id": cid, "section_id": row.get("section_id"),
                  "kind": row.get("kind"), "quote": row.get("quote")}
        res = checks.run_checks(obj, clause, corpus_ids)
        print(f"  checks.run_checks: repair_needed={res.repair_needed}"
              f"  errors={len(res.errors)}  notes={len(res.notes)}")
        for e in res.errors:
            print("   ERROR", e); rc = 1
        for n in res.notes:
            print("   note ", n)
        print(f"  asserts: {len(obj.get('asserts') or [])}"
              f"  ontology: {len(obj.get('ontology') or [])}"
              f"  requires: {len(obj.get('requires') or [])}"
              f"  inputs: {len(obj.get('inputs') or [])}"
              f"  claims: {len(obj.get('claims') or [])}"
              f"  verdict: {obj.get('verdict') or obj.get('status')}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or []))
