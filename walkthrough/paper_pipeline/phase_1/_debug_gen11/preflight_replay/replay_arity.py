"""CHECK 2 — the arity-aware declaration check, replayed over every stored module.

ZERO API SPEND. Reads stored `<clause>.json` module files under `runs/` and
`resolve_runs/graph_v2/translation_sample/runs/`, plus the graveyard copies,
and applies `checks.arity_mismatches` (the shipping function, imported, not
copied) to each.

The question that matters: how many modules that the loop ACCEPTED — i.e. the
ones sitting in the production corpus with status `translated` — would now be
flagged? Each such module is a NEW error-severity finding injected into a loop
that previously converged: added repair rounds, and a changed outcome on work
we already have.

`checks.run_checks` adds `arity_findings` AFTER the abstention return, so
abstained modules are excluded here too.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import checks  # noqa: E402

RUN_GLOBS = ("runs/*/run.json",
             "resolve_runs/graph_v2/translation_sample/runs/*/run.json")
GY_GLOBS = ("repair_graveyard/*/module.json",
            "resolve_runs/graph_v2/translation_sample/repair_graveyard/*/module.json")


def modules():
    for pattern in RUN_GLOBS:
        for rj in sorted(glob.glob(os.path.join(PHASE1, pattern))):
            root = os.path.dirname(rj)
            data = json.load(open(rj, encoding="utf-8"))
            for res in data.get("results", []):
                cid = res.get("clause_id")
                mp = os.path.join(root, cid + ".json")
                if not os.path.exists(mp):
                    continue
                obj = json.load(open(mp, encoding="utf-8"))
                yield dict(src="run", run=os.path.basename(root), clause=cid,
                           status=res.get("status"),
                           attempts=res.get("attempts"),
                           corpus=("runs" if "/translation_sample/" not in rj
                                   else "sample"),
                           path=os.path.relpath(mp, PHASE1), obj=obj)
    for pattern in GY_GLOBS:
        for mp in sorted(glob.glob(os.path.join(PHASE1, pattern))):
            obj = json.load(open(mp, encoding="utf-8"))
            entry = os.path.join(os.path.dirname(mp), "entry.json")
            e = json.load(open(entry, encoding="utf-8")) \
                if os.path.exists(entry) else {}
            yield dict(src="graveyard", run=os.path.basename(os.path.dirname(mp)),
                       clause=e.get("clause_id") or obj.get("clause_id"),
                       status="graveyard:" + str(e.get("status")),
                       attempts=e.get("attempts"),
                       corpus="graveyard",
                       path=os.path.relpath(mp, PHASE1), obj=obj)


def main():
    rows = []
    for m in modules():
        obj = m.pop("obj")
        if (obj.get("outcome") == "abstained"):
            m["skipped"] = "abstained"
            m["mismatches"] = []
        else:
            m["skipped"] = None
            m["mismatches"] = checks.arity_mismatches(obj)
        rows.append(m)

    print("=" * 78)
    print("CHECK 2 — arity_mismatches over every stored module")
    print("=" * 78)
    print(f"module files read: {len(rows)}  "
          f"(abstained, skipped as run_checks does: "
          f"{sum(1 for r in rows if r['skipped'])})")
    scored = [r for r in rows if not r["skipped"]]
    flagged = [r for r in scored if r["mismatches"]]
    print(f"scored: {len(scored)}   flagged by the new check: {len(flagged)}")
    print()

    for status_pred, label in (
            (lambda s: s == "translated", "ACCEPTED (status=translated)"),
            (lambda s: s == "unrepaired", "unrepaired"),
            (lambda s: s == "invalid_module", "invalid_module"),
            (lambda s: str(s).startswith("graveyard"), "graveyard copies"),
            (lambda s: s in ("abstained_under_repair", "error"), "other")):
        pop = [r for r in scored if status_pred(r["status"])]
        f = [r for r in pop if r["mismatches"]]
        print(f"{label:32s} n={len(pop):4d}  flagged {len(f):4d}"
              f"  ({100.0 * len(f) / max(1, len(pop)):.1f}%)")
    print()

    acc = [r for r in scored if r["status"] == "translated" and r["mismatches"]]
    print("--- ACCEPTED MODULES THAT WOULD NOW BE FLAGGED ---")
    print(f"count: {len(acc)}")
    for r in acc:
        print(f"  * {r['path']}  ({r['clause']}, attempts={r['attempts']})")
        for where, name, known, arity in r["mismatches"]:
            print(f"      {where}: {name} declared at {known}, used at {arity}")
    print()

    print("--- flagged failures (the upside population) ---")
    for r in scored:
        if r["mismatches"] and r["status"] != "translated":
            names = ", ".join(f"{n}/{a} (decl {k})"
                              for _, n, k, a in r["mismatches"])
            print(f"  {r['status']:22s} {r['run'][:24]:24s} {r['clause']:18s} {names}")

    out = os.path.join(HERE, "arity.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, default=str)
    print(f"\nper-module table -> {out}")


if __name__ == "__main__":
    main()
