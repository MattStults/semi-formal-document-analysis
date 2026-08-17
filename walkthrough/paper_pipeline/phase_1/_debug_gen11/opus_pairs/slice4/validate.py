#!/usr/bin/env python3
"""Coordinator-run stage 2: schema.validate_all + checks.run_checks per module.

Usage: validate.py [<id> ...]     (default: every out/*.json)
Never takes an agent's word for a module's status.
"""
import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, P1)
import schema, checks

CORPUS = os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")
rows = json.load(open(CORPUS))["clauses"]
byid = {r["id"]: r for r in rows}
corpus_ids = set(byid)

def n_asserts(obj):
    return len(obj.get("asserts") or [])

def one(cid):
    path = os.path.join(HERE, "out", cid + ".json")
    obj = json.load(open(path))
    mod, breaches = schema.validate_all(obj, clause_id=cid, known_clause_ids=corpus_ids)
    findings, outcome = [], None
    if mod is not None:
        # ⚠️ run_checks returns a CheckResult, NOT a list. Iterating the result
        # object raises TypeError; the findings live on `.findings` and the
        # stage-2 verdict on `.outcome`.
        res = checks.run_checks(obj, byid[cid], corpus_ids)
        findings, outcome = list(res.findings), res.outcome
    return obj, mod, breaches, findings, outcome

def sev(f):
    return getattr(f, "severity", "?")

def main():
    ids = sys.argv[1:] or sorted(os.path.basename(p)[:-5]
                                 for p in glob.glob(os.path.join(HERE, "out", "*.json"))
                                 if not os.path.basename(p).endswith(".notes.json"))
    bad = 0
    for cid in ids:
        obj, mod, breaches, findings, outcome = one(cid)
        errs = [f for f in findings if sev(f) == "error"]
        print(f"=== {cid}  declared={obj.get('outcome')} stage2={outcome} "
              f"asserts={n_asserts(obj)} "
              f"module={'OK' if mod else 'NOT CONSTRUCTED'} "
              f"breaches={len(breaches)} findings={len(findings)} errors={len(errs)}")
        for b in breaches:
            print("   BREACH:", b)
            bad += 1
        for f in findings:
            print(f"   [{sev(f)}]", f)
        bad += len(errs)
    print("\nTOTAL error-severity/breach count:", bad)
    return 1 if bad else 0

sys.exit(main())
