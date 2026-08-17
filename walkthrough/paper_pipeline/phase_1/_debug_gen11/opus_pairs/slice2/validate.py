#!/usr/bin/env python3
"""Coordinator-run stage-2 floor for slice 2.  Never takes an agent's word.

    validate.py out/<id>.json [more.json ...]

Prints, per module: parse, schema breaches, checks outcome/repair_needed, every
finding, and the ASSERTS COUNT (gap 3 instrument -- content deletion is
invisible unless the count is recorded).
"""
import json
import os
import sys

P = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", ".."))
sys.path.insert(0, P)
os.chdir(P)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CFG = os.path.join(P, "resolve_runs", "graph_v2", "config_corpus_all.json")


def main(paths):
    cfg = translate.load_config(CFG)
    rows = translate.load_corpus(cfg)
    idk = cfg["corpus"]["id_key"]
    by = {r[idk]: r for r in rows}
    ids = set(by)
    worst = 0
    for path in paths:
        cid = os.path.basename(path).split(".")[0]
        print("=" * 70)
        print(cid, path)
        try:
            obj = json.load(open(path, encoding="utf-8"))
        except Exception as exc:                              # noqa: BLE001
            print("  NOT-JSON:", exc)
            worst = 2
            continue
        row = by[cid]
        mod, breaches = schema.validate_all(obj, cid, ids)
        print("  outcome_field :", obj.get("outcome"))
        print("  asserts       :", len(obj.get("asserts") or []))
        print("  ontology      :", len(obj.get("ontology") or []),
              " concepts:", len(obj.get("concepts") or []),
              " claims:", len(obj.get("claims") or []),
              " beats:", len(obj.get("beats") or []),
              " forbid_body:", len(obj.get("forbid_body") or []))
        print("  breaches      :", len(breaches))
        for b in breaches:
            print("     BREACH", b)
            worst = 2
        try:
            res = checks.run_checks(obj, row, ids)
        except Exception as exc:                              # noqa: BLE001
            print("  run_checks RAISED:", repr(exc))
            worst = 2
            continue
        print("  checks.outcome:", res.outcome,
              " repair_needed:", bool(res.repair_needed))
        for f in res.findings:
            print(f"     [{f.severity}/{f.origin}] {f.check_id} @ {f.where}: "
                  f"{f.message}")
            if f.severity == "error":
                worst = max(worst, 2)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
