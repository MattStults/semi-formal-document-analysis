#!/usr/bin/env python3
"""MECHANICAL measurement for the LICENCE CONTROL arm, and for every arm it is
compared against, computed by ONE code path.

Nothing here reads a span or applies a defect predicate of its own.  The target
class and the floor come from `arms_review/floor.py` and `arms_review/
measures.py` — imported, not reimplemented, so the denominator is the one the
cross-arm review already published.  The four extra columns the brief asks for
(error-severity findings, polarity mismatches, asserts/ontology counts, bodiless
asserts) are computed off `checks`/`floor` outputs, applied identically to every
arm in the table.

READ-ONLY except `_debug_gen11/licence_control/measure.json`.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
REVIEW = os.path.join(G11, "arms_review")
sys.path.insert(0, REVIEW)

import floor as F                                             # noqa: E402
import measures as M                                          # noqa: E402


def modules_licence_control():
    """This arm writes `run_aprime.py`'s record shape: {clause_id, module}."""
    d = os.path.join(HERE, "out")
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json") or f.endswith(".raw.json"):
            continue
        r = json.load(open(os.path.join(d, f), encoding="utf-8"))
        if isinstance(r, dict) and r.get("module"):
            out[r["clause_id"]] = r["module"]
    return out


def modules_aprime():
    d = os.path.join(G11, "arm_aprime", "out")
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json") or f.endswith(".raw.json"):
            continue
        r = json.load(open(os.path.join(d, f), encoding="utf-8"))
        if isinstance(r, dict) and r.get("module"):
            out[r["clause_id"]] = r["module"]
    return out


def asserts_of(m):
    return list(m.get("asserts") or [])


def bodiless_asserts(m):
    """An `asserts` entry with no body at all — the shape that collapsed the
    decomposition arm's floor (13 of 31 there, 0 of 25 unaided)."""
    return [a for a in asserts_of(m) if not (a.get("body") or "").strip()]


def score(name, mods, restrict=None):
    rec = {"n": 0, "clauses": [], "floor_clean": 0, "outcomes": collections.Counter(),
           "selfcited_glosses": 0, "requires_names": 0, "clauses_with_selfcite": 0,
           "errors": 0, "notes": 0, "breaches": 0, "polarity": 0, "arity": 0,
           "asserts": 0, "bodiless_asserts": 0, "clauses_with_bodiless": 0,
           "ontology": 0, "inputs": 0, "concepts": 0,
           "closure": collections.Counter(), "per_clause": {}}
    for cid in sorted(mods):
        if restrict is not None and cid not in restrict:
            continue
        m = mods[cid]
        rec["n"] += 1
        rec["clauses"].append(cid)
        try:
            f = F.floor(m, cid)
            clean = (f["outcome"] == "translated" and not f["breaches"]
                     and not f["errors"])
        except Exception as exc:                              # noqa: BLE001
            f, clean = {"outcome": f"EXC {exc!r}", "breaches": [], "errors": [],
                        "notes": [], "polarity": 0, "arity": 0}, False
        sc = M.selfcited(m, cid)
        bl = bodiless_asserts(m)
        rec["floor_clean"] += clean
        rec["outcomes"][f["outcome"]] += 1
        rec["selfcited_glosses"] += len(sc)
        rec["clauses_with_selfcite"] += bool(sc)
        rec["requires_names"] += len(m.get("requires") or [])
        rec["errors"] += len(f["errors"])
        rec["notes"] += len(f["notes"])
        rec["breaches"] += len(f["breaches"])
        rec["polarity"] += f.get("polarity", 0)
        rec["arity"] += f.get("arity", 0)
        rec["asserts"] += len(asserts_of(m))
        rec["bodiless_asserts"] += len(bl)
        rec["clauses_with_bodiless"] += bool(bl)
        rec["ontology"] += len(m.get("ontology") or [])
        rec["inputs"] += len(m.get("inputs") or [])
        rec["concepts"] += len(m.get("concepts") or [])
        rec["closure"].update(M.closures(m))
        rec["per_clause"][cid] = {
            "floor_clean": clean, "outcome": f["outcome"],
            "selfcited": len(sc), "requires": len(m.get("requires") or []),
            "errors": len(f["errors"]), "breaches": len(f["breaches"]),
            "polarity": f.get("polarity", 0),
            "asserts": len(asserts_of(m)), "bodiless": len(bl),
            "ontology": len(m.get("ontology") or []),
            "inputs": len(m.get("inputs") or []),
            "closure": M.closures(m), "errors_detail": f["errors"]}
    rec["closure"] = dict(rec["closure"])
    rec["outcomes"] = dict(rec["outcomes"])
    return rec


def all_sets():
    s = dict(M.sets())
    s["arm_aprime(null)"] = modules_aprime()
    s["licence_control"] = modules_licence_control()
    return s


if __name__ == "__main__":
    sets = all_sets()
    out = {}
    for name, mods in sets.items():
        if not mods:
            continue
        out[name] = score(name, mods)
    # the paired view: only clauses the licence control actually produced
    lc = set(sets["licence_control"]) if sets.get("licence_control") else set()
    if lc:
        out["_paired"] = {name: score(name, mods, restrict=lc)
                          for name, mods in sets.items() if mods}
    hdr = (f"{'arm':26s} {'n':>3s} {'clean':>5s} {'selfcite':>9s} "
           f"{'err':>4s} {'pol':>4s} {'asrt':>5s} {'bodiless':>8s} "
           f"{'ont':>4s} {'inp':>4s}")
    print(hdr)
    for name, r in out.items():
        if name.startswith("_"):
            continue
        print(f"{name:26s} {r['n']:3d} {r['floor_clean']:5d} "
              f"{r['selfcited_glosses']:4d}/{r['requires_names']:<4d} "
              f"{r['errors']:4d} {r['polarity']:4d} {r['asserts']:5d} "
              f"{r['bodiless_asserts']:8d} {r['ontology']:4d} {r['inputs']:4d}")
    json.dump(out, open(os.path.join(HERE, "measure.json"), "w"), indent=1)
