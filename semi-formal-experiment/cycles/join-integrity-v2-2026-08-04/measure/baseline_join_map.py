"""Baseline (join v1) locator-level join map — the BEFORE side of the P1/P2
before/after comparison, plus verification of every measured fact the two
designs (JOIN_INTEGRITY_DESIGN.md, SEGMENTATION_GAPS_DESIGN.md) rest on.

Reads passage IDENTITY only (locator, quote, score, exampleBlock) — no judge
verdict is consulted. Run from anywhere:

    python3 .../measure/baseline_join_map.py [--out out.json] [--tag v1]

Output: {locator: {"quote_sha": ..., "clauses": [...ids...]}} per spec side,
fan-out distribution, zero-match locators with strata, reference-grade
(score>=5) per-behaviour mapped sets, and the empty-meta candidate scan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, EXP)

import benchmark  # noqa: E402
import inventory  # noqa: E402


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def clause_rows():
    rows, src = benchmark.load_clauses()
    assert src == "modelspec_clauses.json", src
    return rows


def join_fn(mode: str):
    """mode: v1 | v2_nomix | v2. Returns locator-join callable
    (quote, rows, locator) -> {"clauses": [ids], "refused": bool,
    "restricted": bool}."""
    if mode == "v1":
        def f(quote, rows, locator):
            return {"clauses": [r["id"] for r in
                                inventory.match_passage(quote, rows)],
                    "refused": False, "restricted": None}
        return f

    def f(quote, rows, locator, _mix=(mode == "v2")):
        res = inventory.match_passage_v2(quote, rows, locator,
                                         mixed_variants=_mix)
        return {"clauses": [r["id"] for r in res["clauses"]],
                "refused": res["refused"], "restricted": res["restricted"]}
    return f


def build(mode: str) -> dict:
    rows = clause_rows()
    panel = benchmark.load_true_panel()
    jf = join_fn(mode)
    spec = benchmark.spec_text()
    norm_spec = inventory._norm(spec)
    out = {"mode": mode, "locators": {}, "reference_grade": {},
           "fanout_hist": {}, "zero_match": []}

    # locator -> quote consistency check, then one join per locator
    loc_quote, loc_meta = {}, {}
    for slug, b in panel.items():
        for p in benchmark.passages(b):
            loc = p.get("locator") or p["id"]
            q = p.get("quote", "")
            if loc in loc_quote:
                assert loc_quote[loc] == q, f"quote mismatch at {loc}"
            loc_quote[loc] = q
            m = loc_meta.setdefault(loc, {"example_block": False,
                                          "scores": {}})
            m["example_block"] = m["example_block"] or bool(
                p.get("exampleBlock"))
            m["scores"][slug] = p.get("score", 0)

    for loc in sorted(loc_quote):
        q = loc_quote[loc]
        res = jf(q, rows, loc)
        cids = sorted(res["clauses"])
        rec = {"quote_sha": sha(q), "n": len(cids), "clauses": cids,
               "refused": res["refused"], "restricted": res["restricted"]}
        out["locators"][loc] = rec
        out["fanout_hist"][str(len(cids))] = \
            out["fanout_hist"].get(str(len(cids)), 0) + 1
        if not cids and not res["refused"]:
            meta = loc_meta[loc]
            if meta["example_block"]:
                stratum = "example_block"
            elif inventory._norm(q) not in norm_spec:
                stratum = "not_verbatim_in_source"
            else:
                stratum = "verbatim_but_unsegmented"
            out["zero_match"].append(
                {"locator": loc, "stratum": stratum, "quote_len": len(q),
                 "scores": meta["scores"]})

    # reference-grade mapped sets, per behaviour (prediction 2 evidence)
    for slug, b in panel.items():
        ref = {}
        for p in benchmark.reference(b):
            loc = p.get("locator") or p["id"]
            ref[loc] = out["locators"][loc]["clauses"]
        out["reference_grade"][slug] = ref
    return out


def empty_meta_scan() -> list:
    """Meta clauses whose text is heading-shaped — computed by the same
    predicate the v2 join will use once it exists; before implementation this
    reports raw candidates by shape for calibration."""
    rows = clause_rows()
    if hasattr(inventory, "content_empty"):
        return sorted(r["id"] for r in rows if inventory.content_empty(r))
    import re
    pat = re.compile(r"^(\*\*[^*\n]+\*\*|[^.!?\n]{1,60}:)$")
    return sorted(r["id"] for r in rows
                  if r.get("kind") == "meta"
                  and pat.fullmatch((r.get("quote") or "").strip()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="v1", choices=["v1", "v2_nomix", "v2"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = build(args.mode)
    res["empty_meta_candidates"] = empty_meta_scan()
    out = args.out or os.path.join(HERE, f"join_map_{args.mode}.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    n = len(res["locators"])
    print(f"mode={args.mode} locators={n}")
    print("fanout_hist:", dict(sorted(res["fanout_hist"].items(),
                                      key=lambda kv: int(kv[0]))))
    print("zero_match:", len(res["zero_match"]))
    for z in res["zero_match"]:
        print("  ", z["locator"], z["stratum"], z["quote_len"], z["scores"])
    big = [(loc, r["n"]) for loc, r in res["locators"].items() if r["n"] > 1]
    print("fanout>1 locators:")
    for loc, k in sorted(big, key=lambda t: -t[1])[:10]:
        print("  ", k, loc)
    print("empty_meta_candidates:", res["empty_meta_candidates"])
    print("wrote", out)


if __name__ == "__main__":
    main()
