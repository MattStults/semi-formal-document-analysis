"""Run every reference module through the SAME gate translate.py:2557 runs.

    schema.validate_all  ->  checks.run_checks(obj, clause, corpus_ids)

Read-only against the corpus and the run directory. Writes nothing.

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/reference_set/validate_ref.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import checks            # noqa: E402
import schema            # noqa: E402

CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2", "node_corpus_all.json")
REF = os.path.join(HERE, "modules")


def main():
    corpus = json.load(open(CORPUS, encoding="utf-8"))["clauses"]
    by_id = {c["id"]: c for c in corpus}
    corpus_ids = set(by_id)

    names = sorted(f for f in os.listdir(REF) if f.endswith(".json"))
    bad = 0
    for name in names:
        cid = name[:-5]
        obj = json.load(open(os.path.join(REF, name), encoding="utf-8"))
        clause = by_id[cid]
        res = checks.run_checks(obj, clause, corpus_ids, attempt=1)
        errs = [f for f in res.findings if f.severity == "error"]
        warns = [f for f in res.findings if f.severity != "error"]
        flag = "OK  " if res.outcome == "translated" and not errs else "FAIL"
        if flag == "FAIL":
            bad += 1
        print(f"{flag} {cid:22s} outcome={res.outcome:10s} "
              f"errors={len(errs)} warnings={len(warns)}")
        for f in errs + warns:
            print(f"       [{f.severity}] {f.check_id} @ {f.where}: "
                  f"{f.message[:200]}")
    print(f"\n{len(names)} modules, {len(names) - bad} pass, {bad} fail")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
