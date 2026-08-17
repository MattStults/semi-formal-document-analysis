"""Stage-2 validation for the fix_pass_1 modules. ZERO API SPEND.

Replays exactly the call `translate.py:2557` (`repair_loop`'s `look`) makes:
    checks.run_checks(obj, clause, corpus_ids, concepts=concepts, attempt=n)
with `concepts=None` so `run_checks` derives the module's own rows (its
documented default), and `corpus_ids` = every id in the node corpus.

Usage:
    validate.py                    # every module in modules/, plus the originals
    validate.py <clause_id> ...    # only these
    validate.py --orig <id> ...    # the ORIGINAL run module, for a before/after
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import checks  # noqa: E402

RUN = os.path.join(
    PHASE1, "resolve_runs", "graph_v2", "translation_sample", "runs",
    "20260815-124836-together-deepseek-v4-flash")
CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "node_corpus_all.json")
FIXED = os.path.join(HERE, "modules")

_rows = json.load(open(CORPUS, encoding="utf-8"))["clauses"]
CLAUSES = {r["id"]: r for r in _rows}
CORPUS_IDS = set(CLAUSES)


def check(cid, path):
    obj = json.load(open(path, encoding="utf-8"))
    res = checks.run_checks(obj, CLAUSES[cid], CORPUS_IDS,
                            concepts=None, attempt=1)
    return res


def report(cid, path, label):
    res = check(cid, path)
    fs = list(res.findings)
    errs = [f for f in fs if f.severity == "error"]
    print(f"[{label}] {cid}: outcome={res.outcome}  "
          f"findings={len(fs)} (errors={len(errs)})")
    for f in fs:
        print(f"    {f.severity:7s} {f.check_id:24s} {f.where}: {f.message}")
    return fs


def main(argv):
    orig = "--orig" in argv
    argv = [a for a in argv if a != "--orig"]
    if argv:
        ids = argv
    else:
        ids = sorted(f[:-5] for f in os.listdir(FIXED) if f.endswith(".json"))
    bad = 0
    for cid in ids:
        p = (os.path.join(RUN, cid + ".json") if orig
             else os.path.join(FIXED, cid + ".json"))
        if not os.path.exists(p):
            print(f"[MISSING] {p}")
            bad += 1
            continue
        fs = report(cid, p, "orig" if orig else "fixed")
        if any(f.severity == "error" for f in fs):
            bad += 1
    print(f"\n{len(ids)} module(s); {bad} with error-severity findings.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
