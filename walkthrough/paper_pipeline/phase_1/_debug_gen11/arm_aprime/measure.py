#!/usr/bin/env python3
"""ARM A-PRIME — the mechanical measurement. NOTHING here reads a draft
span-first; the series' central weakness is eight agents applying eight
unstated defect predicates, and this arm adds no ninth.

Everything reuses `../arms_review/floor.py` and `measures.py` unmodified:
`floor.floor()` for `checks.run_checks` outcome / error-severity count /
`polarity_mismatches`, and `measures.selfcited()` / `measures.closures()` for
the borrowed-gloss and closure classes.

READ-ONLY except `_debug_gen11/arm_aprime/aprime_measures.json`.
"""
import collections
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.abspath(os.path.join(HERE, "..", "arms_review"))
sys.path.insert(0, REVIEW)
import floor                                                  # noqa: E402
import measures                                               # noqa: E402

G11 = floor.G11
N = 17


def wilson(k, n, z=1.96):
    """95% Wilson interval. One replicate gives a POINT estimate of the floor
    with real uncertainty; every F is reported with this attached."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3), round(min(1.0, c + h), 3))


def armA_turn1():
    return {os.path.basename(p).split(".")[0]:
            json.load(open(p, encoding="utf-8"))
            for p in glob.glob(G11 + "/ds_opus_loop/out/*.turn1.raw.json")}


def aprime():
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "out", "*.json"))):
        if p.endswith(".raw.json"):
            continue
        r = json.load(open(p, encoding="utf-8"))
        if r.get("module"):
            out[r["clause_id"]] = r["module"]
    return out


def canon(m):
    return json.dumps(m, sort_keys=True)


def signature(m):
    """The weaker structural identity pre-registered in PREREG.md."""
    return json.dumps({
        "concepts": sorted(f"{c.get('name')}/{c.get('arity')}"
                           for c in (m.get("concepts") or [])),
        "requires": sorted(m.get("requires") or []),
        "closure": sorted(measures.closures(m)),
    }, sort_keys=True)


def profile(m, cid):
    f = floor.floor(m, cid)
    return {
        "outcome": f["outcome"],
        "n_errors": len(f["errors"]),
        "n_breaches": len(f["breaches"]),
        "polarity": f["polarity"],
        "arity": f["arity"],
        "floor_clean": f["outcome"] == "translated" and not f["breaches"]
                       and not f["errors"],
        "selfcited": len(measures.selfcited(m, cid)),
        "requires": len(m.get("requires") or []),
        "closure": measures.closures(m),
        "n_asserts": len(m.get("asserts") or []),
        "n_ontology": len(m.get("ontology") or []),
        "n_concepts": len(m.get("concepts") or []),
        "canon": canon(m),
        "sig": signature(m),
    }


def main():
    A, P = armA_turn1(), aprime()
    shared = sorted(set(A) & set(P))
    pa = {c: profile(A[c], c) for c in shared}
    pp = {c: profile(P[c], c) for c in shared}

    # ---- per-measure noise floor: on how many of n clauses does A' != A? ----
    diffs = collections.OrderedDict()

    def F(name, key):
        ch = [c for c in shared if pa[c][key] != pp[c][key]]
        diffs[name] = {"F": len(ch), "n": len(shared),
                       "wilson95": wilson(len(ch), len(shared)),
                       "changed": ch}

    F("floor outcome", "outcome")
    F("error-severity count", "n_errors")
    F("floor_clean (outcome+breaches+errors)", "floor_clean")
    F("polarity_mismatches count", "polarity")
    F("arity_mismatches count", "arity")
    F("self-cited borrowed-gloss count", "selfcited")
    F("closure verdict list", "closure")
    F("asserts count", "n_asserts")
    F("ontology count", "n_ontology")
    F("concepts count", "n_concepts")
    F("exact module identity", "canon")
    F("structural signature identity", "sig")

    # the review's composite: outcome AND error count together
    comp = [c for c in shared
            if (pa[c]["outcome"], pa[c]["n_errors"])
            != (pp[c]["outcome"], pp[c]["n_errors"])]
    diffs["MECHANICAL FLOOR (outcome + error count)"] = {
        "F": len(comp), "n": len(shared),
        "wilson95": wilson(len(comp), len(shared)), "changed": comp}

    def agg(pr):
        cl = collections.Counter()
        for c in shared:
            cl.update(pr[c]["closure"])
        return {
            "floor_clean": sum(pr[c]["floor_clean"] for c in shared),
            "selfcited_glosses": sum(pr[c]["selfcited"] for c in shared),
            "requires_names": sum(pr[c]["requires"] for c in shared),
            "clauses_with_selfcite": sum(bool(pr[c]["selfcited"])
                                         for c in shared),
            "closure": dict(cl),
            "polarity_total": sum(pr[c]["polarity"] for c in shared),
            "asserts_total": sum(pr[c]["n_asserts"] for c in shared),
            "ontology_total": sum(pr[c]["n_ontology"] for c in shared),
        }

    res = {"n": len(shared), "clauses": shared,
           "armA_turn1": agg(pa), "armAprime": agg(pp),
           "noise_floor": diffs,
           "per_clause": {c: {"A": {k: v for k, v in pa[c].items()
                                    if k not in ("canon", "sig")},
                              "Aprime": {k: v for k, v in pp[c].items()
                                         if k not in ("canon", "sig")},
                              "identical_exact": pa[c]["canon"] == pp[c]["canon"],
                              "identical_sig": pa[c]["sig"] == pp[c]["sig"]}
                          for c in shared}}

    print(f"n = {len(shared)} paired clauses\n")
    print(f"{'':44s} {'armA_t1':>10s} {'armA-prime':>12s}")
    for k in ("floor_clean", "selfcited_glosses", "requires_names",
              "clauses_with_selfcite", "polarity_total", "asserts_total",
              "ontology_total"):
        print(f"{k:44s} {str(res['armA_turn1'][k]):>10s} "
              f"{str(res['armAprime'][k]):>12s}")
    print(f"{'closure':44s} {str(res['armA_turn1']['closure']):>10s}")
    print(f"{'':44s} {'':10s} {str(res['armAprime']['closure']):>12s}")
    print("\nPER-MEASURE NOISE FLOOR  (clauses of "
          f"{len(shared)} that changed under the EMPTY manipulation)")
    for k, v in diffs.items():
        lo, hi = v["wilson95"]
        print(f"  {k:44s} F = {v['F']:2d}/{v['n']}  "
              f"({100*v['F']/v['n']:4.0f}%, 95% CI {100*lo:.0f}-{100*hi:.0f}%)")

    json.dump(res, open(os.path.join(HERE, "aprime_measures.json"), "w"),
              indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
