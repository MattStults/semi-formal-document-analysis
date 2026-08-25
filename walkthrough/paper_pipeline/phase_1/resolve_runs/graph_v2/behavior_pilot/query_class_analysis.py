#!/usr/bin/env python3
"""query_class_analysis.py — P5 of QUERY_CLASS_STUDY_SPEC.md (v2-vocabulary
edition: reads the v2 recode files after the v1 tripwire and vocabulary fix).
Deterministic, $0. Committed BEFORE any coding exists.

Consensus: a definition's pattern = the two seats' pattern when equal;
disagreements go to the Opus spot-check/calibration value when one
exists, else recorded UNRESOLVED (excluded from the curve, counted).
Curve: new-pattern accumulation over 200 seeded orderings (seed 20260860
+ i); Chao1 = S_obs + f1^2/(2*f2) (f2>0) else S_obs + f1*(f1-1)/2.
"""
import json, os, random, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def pat(rec):
    return "|".join(sorted(rec["places_constrained"])) + ">" + rec["query_verb"]


def main():
    corpus = json.load(open(os.path.join(HERE, "query_class_corpus.json")))
    ids = [e["id"] for e in corpus["entries"]]
    seats = {}
    for f in ("qc_calib_v2_opusA", "qc_calib_v2_opusB", "qc_bulk_v2_A",
              "qc_bulk_v2_B", "qc_spotcheck_v2_opus"):
        p = os.path.join(HERE, f + ".json")
        if os.path.exists(p):
            seats[f] = json.load(open(p))["codings"]
    opus_ref = {}
    for f in ("qc_calib_v2_opusA", "qc_calib_v2_opusB", "qc_spotcheck_v2_opus"):
        for i, r in seats.get(f, {}).items():
            opus_ref.setdefault(i, []).append(pat(r))
    cons, unresolved = {}, []
    for i in ids:
        cands = []
        for f in ("qc_calib_v2_opusA", "qc_calib_v2_opusB"):
            if i in seats.get(f, {}):
                cands.append(pat(seats[f][i]))
        if len(cands) == 2:
            if cands[0] == cands[1]:
                cons[i] = cands[0]
            else:
                unresolved.append(i)
            continue
        a = seats.get("qc_bulk_v2_A", {}).get(i)
        b = seats.get("qc_bulk_v2_B", {}).get(i)
        if a and b:
            pa_, pb_ = pat(a), pat(b)
            if pa_ == pb_:
                cons[i] = pa_
            elif i in opus_ref:
                cons[i] = opus_ref[i][0]
            else:
                unresolved.append(i)
    pats = list(cons.values())
    S_obs = len(set(pats))
    c = Counter(Counter(pats).values())
    f1, f2 = c.get(1, 0), c.get(2, 0)
    chao1 = S_obs + (f1 * f1 / (2 * f2) if f2 else f1 * (f1 - 1) / 2)
    curves = []
    for i in range(200):
        order = list(cons)
        random.Random(20260860 + i).shuffle(order)
        seen, curve = set(), []
        for n_, x in enumerate(order, 1):
            seen.add(cons[x])
            curve.append(len(seen))
        curves.append(curve)
    m = len(next(iter(curves)))
    mean_curve = [round(sum(c_[k] for c_ in curves) / len(curves), 2)
                  for k in range(m)]
    tail_new = mean_curve[-1] - mean_curve[max(0, m - 11)]
    out = {
        "_": ("QUERY-CLASS SATURATION ANALYSIS (deterministic; script "
              "committed pre-coding). Pattern = sorted places + verb."),
        "n_coded": len(cons), "n_unresolved": len(unresolved),
        "unresolved": unresolved,
        "S_observed_patterns": S_obs,
        "chao1_richness_estimate": round(chao1, 1),
        "singletons_f1": f1, "doubletons_f2": f2,
        "mean_accumulation_curve": mean_curve,
        "new_patterns_in_last_10": round(tail_new, 2),
        "saturation_verdict": ("SATURATING" if tail_new < 1.0 else
                               "NOT SATURATED at this corpus size"),
        "pattern_inventory": dict(Counter(pats).most_common()),
    }
    json.dump(out, open(os.path.join(HERE, "QUERY_CLASS_BOUND.json"), "w"),
              indent=1)
    print(json.dumps({k: out[k] for k in
                      ("n_coded", "S_observed_patterns",
                       "chao1_richness_estimate", "saturation_verdict")},
                     indent=1))


if __name__ == "__main__":
    main()
