"""TRIAGE — statistics and the reference-set transfer check.

Re-run (from walkthrough/paper_pipeline/phase_1/):
  ../../../semi-formal-experiment/.venv/bin/python _debug_gen11/triage/analyse.py

Univariate rank statistics and top-k capture only. No multivariate fit, no tuned
threshold, no predictor combination — see PREREG.md §6.
Reads only; writes only triage/stats.json.
"""
import sys, os, json, glob, itertools, random

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
P1 = os.path.dirname(G11)
sys.path.insert(0, os.path.join(G11, "arms_review"))
sys.path.insert(0, HERE)
import floor, measures                                              # noqa: E402
import build as B                                                   # noqa: E402

PRED = ["DISAGREE", "BORROWED", "FLOORDIRTY_T1", "PROPLOAD", "DISJ", "HEDGE"]
CTRL = ["span_chars", "T1_ENTRIES"]


# ------------------------------------------------------------ rank statistics

def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(x, y):
    n = len(x)
    if n < 3:
        return None
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** .5
    dy = sum((b - my) ** 2 for b in ry) ** .5
    return None if dx == 0 or dy == 0 else round(num / (dx * dy), 3)


def perm_p(x, y, iters=20000, seed=11):
    """Two-sided permutation p for Spearman. Exact-ish, no scipy."""
    obs = spearman(x, y)
    if obs is None:
        return None
    rng = random.Random(seed)
    y2, hits = list(y), 0
    for _ in range(iters):
        rng.shuffle(y2)
        s = spearman(x, y2)
        if s is not None and abs(s) >= abs(obs) - 1e-12:
            hits += 1
    return round((hits + 1) / (iters + 1), 4)


def topk_capture(score, weight, k):
    """Fraction of total `weight` sitting in the top-k by `score`.
    Ties broken pessimistically AND optimistically; both reported, because at
    n=17 with integer predictors ties decide the answer."""
    idx = list(range(len(score)))
    tot = sum(weight)
    hi = sorted(idx, key=lambda i: (-score[i], -weight[i]))[:k]
    lo = sorted(idx, key=lambda i: (-score[i], weight[i]))[:k]
    return (round(sum(weight[i] for i in hi) / tot, 3),
            round(sum(weight[i] for i in lo) / tot, 3))


# ------------------------------------------------- reference cohort predictors

def reference_cohort():
    run = os.path.join(P1, "resolve_runs", "graph_v2", "translation_sample",
                       "runs", "20260815-124836-together-deepseek-v4-flash")
    dj = json.load(open(os.path.join(G11, "reference_set", "diffs.json")))
    ids = sorted(os.path.basename(p)[:-5] for p in
                 glob.glob(os.path.join(G11, "reference_set", "modules", "*.json")))
    edited = {e["clause"] for e in dj["edits"]}
    nedits = {}
    for e in dj["edits"]:
        nedits[e["clause"]] = nedits.get(e["clause"], 0) + 1

    rows = {}
    for cid in ids:
        if cid not in floor.BYID:
            continue
        narrowed, _src, needs = B.span_parts(floor.BYID[cid]["quote"])
        r = {"clause_id": cid,
             "BORROWED": len(needs),
             "PROPLOAD": B.propload(narrowed),
             "DISJ": B.has_disj(narrowed),
             "HEDGE": B.has_hedge(narrowed),
             "span_chars": len(B.clean(narrowed)),
             "REF_EDITED": int(cid in edited),
             "REF_NEDITS": nedits.get(cid, 0)}
        dp = os.path.join(run, cid + ".json")
        if os.path.exists(dp):
            draft = json.load(open(dp))
            m = draft.get("module", draft)
            try:
                f = floor.floor(m, cid)
                r["FLOORDIRTY_T1"] = int(not (f["outcome"] == "translated"
                                              and not f["breaches"]
                                              and not f["errors"]))
            except Exception:                                       # noqa: BLE001
                r["FLOORDIRTY_T1"] = None
            r["T1_ENTRIES"] = sum(len(m.get(k) or []) for k in
                                  ("concepts", "ontology", "asserts", "acts",
                                   "claims", "closure"))
        else:
            r["FLOORDIRTY_T1"] = r["T1_ENTRIES"] = None
        rows[cid] = r
    return rows, dj


# ------------------------------------------------------------------------ main

def main():
    T = json.load(open(os.path.join(HERE, "table.json")))
    R = T["rows"]
    ids = sorted(R)
    out = {"n_clauses": len(ids)}

    # ---------- recompute validation: does my instrument reproduce the review?
    out["validation"] = {
        "CONV_LICINH_total": sum(R[c]["CONV_LICINH"] for c in ids),
        "CONV_LICINH_modules": sum(R[c]["CONV_LICINH"] > 0 for c in ids),
        "CONV_SELFCITE_total": sum(R[c]["CONV_SELFCITE"] for c in ids),
        "CONV_SELFCITE_modules": sum(R[c]["CONV_SELFCITE"] > 0 for c in ids),
        "independent_review_claimed": "licence-inheritance 32 in 12/17; "
                                      "self-cite 20 of 23 in 12/17",
    }

    # ---------- primary: predictors vs Tier-1 frontier-yield columns, n=17
    prim = {}
    for oc in ("FB_CHARS", "TURNS", "CONV_LICINH", "FLOORDIRTY_CONV"):
        y_all = [R[c][oc] for c in ids]
        col = {}
        for p in PRED + CTRL:
            keep = [c for c in ids if R[c].get(p) is not None]
            x = [R[c][p] for c in keep]
            y = [R[c][oc] for c in keep]
            col[p] = {"n": len(keep), "rho": spearman(x, y),
                      "p_perm": perm_p(x, y) if len(keep) >= 6 else None}
        # top-k capture of the yield weight
        k = 6                                                # ceil(17/3)
        base = round(k / len(ids), 3)
        if oc == "FB_CHARS":
            cap = {}
            w = [R[c]["FB_CHARS"] for c in ids]
            for p in PRED + CTRL:
                if any(R[c].get(p) is None for c in ids):
                    cap[p] = "n/a (incomplete coverage)"
                    continue
                s = [R[c][p] for c in ids]
                cap[p] = topk_capture(s, w, k)
            cap["_random_baseline"] = base
            cap["_oracle"] = topk_capture(w, w, k)
            col["_topk_capture_of_FB_CHARS"] = cap
        prim[oc] = col
    out["primary_tier1"] = prim

    # ---------- Tier 2
    y6 = [R[c]["IREV_NOTCORRECT"] for c in ids]
    t2 = {}
    for p in PRED + CTRL:
        keep = [c for c in ids if R[c].get(p) is not None]
        x = [R[c][p] for c in keep]
        y = [R[c]["IREV_NOTCORRECT"] for c in keep]
        t2[p] = {"n": len(keep), "rho": spearman(x, y),
                 "p_perm": perm_p(x, y) if len(keep) >= 6 else None,
                 "mean_if_notcorrect": (round(sum(a for a, b in zip(x, y) if b)
                                              / max(1, sum(y)), 2)),
                 "mean_if_correct": (round(sum(a for a, b in zip(x, y) if not b)
                                           / max(1, len(y) - sum(y)), 2))}
    out["tier2_IREV"] = {"n_notcorrect": sum(y6), "n_correct": len(y6) - sum(y6),
                         "by_predictor": t2}

    # ---------- the DISAGREE cell, in full, because n=6 means show every point
    dis = [c for c in ids if R[c].get("DISAGREE") is not None]
    out["disagree_cell"] = {
        "n": len(dis),
        "clauses": {c: {"DISAGREE": R[c]["DISAGREE"],
                        "D_FIX": R[c]["D_FIX"], "E_FIX": R[c]["E_FIX"],
                        "which": T["pairs"][c]["which"],
                        "FB_CHARS": R[c]["FB_CHARS"], "TURNS": R[c]["TURNS"],
                        "CONV_LICINH": R[c]["CONV_LICINH"],
                        "IREV": R[c]["IREV"]} for c in dis},
        "note": "every point is printed because n=6 supports nothing else",
    }

    # ---------- transfer
    ref, dj = reference_cohort()
    rids = sorted(ref)
    overlap = sorted(set(rids) & set(ids))
    tr = {"n": len(rids), "n_edited": sum(ref[c]["REF_EDITED"] for c in rids),
          "diffs_json_says": {"n_clauses": dj["n_clauses"],
                              "n_edited": dj["n_edited"],
                              "n_unchanged": dj["n_unchanged"]},
          "overlap_with_the_17": overlap,
          "by_predictor": {}, "by_predictor_disjoint": {}}
    for subset, key in ((rids, "by_predictor"),
                        ([c for c in rids if c not in set(ids)],
                         "by_predictor_disjoint")):
        for p in ["BORROWED", "FLOORDIRTY_T1", "PROPLOAD", "DISJ", "HEDGE",
                  "span_chars", "T1_ENTRIES"]:
            keep = [c for c in subset if ref[c].get(p) is not None]
            x = [ref[c][p] for c in keep]
            for oc in ("REF_EDITED", "REF_NEDITS"):
                y = [ref[c][oc] for c in keep]
                tr[key].setdefault(p, {})[oc] = {
                    "n": len(keep), "rho": spearman(x, y),
                    "p_perm": perm_p(x, y) if len(keep) >= 6 else None}
    tr["rows"] = ref
    out["transfer_reference_set"] = tr

    # ---------- sign agreement: in-sample (17) vs transfer (25)
    sign = {}
    for p in ["BORROWED", "FLOORDIRTY_T1", "PROPLOAD", "DISJ", "HEDGE"]:
        a = prim["FB_CHARS"][p]["rho"]
        b = tr["by_predictor"][p]["REF_EDITED"]["rho"]
        c = tr["by_predictor_disjoint"][p]["REF_EDITED"]["rho"]
        sign[p] = {"rho_17_vs_FB_CHARS": a, "rho_25_vs_REF_EDITED": b,
                   "rho_20disjoint_vs_REF_EDITED": c,
                   "prereg_direction": "+",
                   "holds_sign_in_sample": None if a is None else a > 0,
                   "holds_sign_on_transfer": None if b is None else b > 0}
    out["sign_agreement"] = sign

    json.dump(out, open(os.path.join(HERE, "stats.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("transfer_reference_set",)}, indent=1))
    print("\n--- TRANSFER ---")
    print(json.dumps({k: v for k, v in tr.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()


# =====================================================================
# POST-HOC, EXPLORATORY, NOT PRE-REGISTERED. Everything below this line
# was computed AFTER the pre-registered joins were read. It is recorded
# so the record is complete, and it is labelled so it cannot be mistaken
# for a result. Nothing here is permitted to carry a conclusion.
# =====================================================================

def posthoc():
    T = json.load(open(os.path.join(HERE, "table.json")))
    R, P = T["rows"], T["pairs"]
    ids = sorted(R)
    o = {}

    # (a) Do the Tier-1 outcome columns even agree with each other?
    #     If "frontier yield" is not one thing, no single predictor can track it.
    oc = ["FB_CHARS", "TURNS", "CONV_LICINH", "CONV_SELFCITE", "FB1_CHARS"]
    o["outcome_intercorrelation"] = {
        f"{a}~{b}": spearman([R[c][a] for c in ids], [R[c][b] for c in ids])
        for a, b in itertools.combinations(oc, 2)}

    # (b) HEDGE as a FILTER rather than a ranker (it is binary; ties dominate)
    for name, sub in (("the_17", ids),):
        h = [c for c in sub if R[c]["HEDGE"]]
        n = [c for c in sub if not R[c]["HEDGE"]]
        o.setdefault("hedge_as_filter", {})[name] = {
            "n_hedged": len(h), "n_plain": len(n),
            "mean_FB_CHARS_hedged": round(sum(R[c]["FB_CHARS"] for c in h) / len(h)),
            "mean_FB_CHARS_plain": round(sum(R[c]["FB_CHARS"] for c in n) / len(n)),
            "share_of_total_FB_CHARS_in_hedged":
                round(sum(R[c]["FB_CHARS"] for c in h)
                      / sum(R[c]["FB_CHARS"] for c in ids), 3),
            "share_of_clauses_hedged": round(len(h) / len(sub), 3)}

    # (c) the union/volume variant of the cheap-critic signal, n=6
    x_dis = [R[c]["DISAGREE"] for c in sorted(P)]
    x_vol = [P[c]["d_fix"] + P[c]["e_fix"] for c in sorted(P)]
    x_max = [max(P[c]["d_fix"], P[c]["e_fix"]) for c in sorted(P)]
    x_e = [P[c]["e_fix"] for c in sorted(P)]
    for nm, xs in (("DISAGREE", x_dis), ("D_FIX+E_FIX", x_vol),
                   ("max(D,E)", x_max), ("E_FIX alone", x_e)):
        o.setdefault("cheap_critic_variants_n6", {})[nm] = {
            oc2: spearman(xs, [R[c][oc2] for c in sorted(P)])
            for oc2 in ("FB_CHARS", "TURNS", "CONV_LICINH")}

    # (d) hypergeometric one-sided p for the reference-set HEDGE cell
    ref, _ = reference_cohort()
    rid = sorted(ref)
    N, K = len(rid), sum(ref[c]["REF_EDITED"] for c in rid)
    nn = sum(ref[c]["HEDGE"] for c in rid)
    kk = sum(ref[c]["HEDGE"] and ref[c]["REF_EDITED"] for c in rid)

    def C(a, b):
        return 0 if b < 0 or b > a else __import__("math").comb(a, b)
    p = sum(C(K, i) * C(N - K, nn - i) for i in range(kk, min(nn, K) + 1)) / C(N, nn)
    o["reference_hedge_cell"] = {
        "N": N, "n_edited": K, "n_hedged": nn, "n_hedged_and_edited": kk,
        "base_rate_edited": round(K / N, 3),
        "hedged_edit_rate": round(kk / nn, 3),
        "one_sided_hypergeometric_p": round(p, 4)}

    # (e) why FLOORDIRTY did not transfer
    o["floordirty_transfer"] = {
        "reference_cohort_dirty": sum(bool(ref[c]["FLOORDIRTY_T1"]) for c in rid),
        "reference_cohort_n": len(rid),
        "the_17_dirty": sum(R[c]["FLOORDIRTY_T1"] for c in ids),
        "note": "zero variance on the reference cohort: the predictor is a "
                "property of the pipeline generation, not of the clause"}

    # (f) is the Tier-2 outcome confounded with span type?
    o["tier2_confound"] = {
        c: {"IREV": R[c]["IREV"], "T1_ENTRIES": R[c]["T1_ENTRIES"],
            "span_chars": R[c]["span_chars"], "BORROWED": R[c]["BORROWED"]}
        for c in sorted(ids, key=lambda c: R[c]["T1_ENTRIES"])}

    s = json.load(open(os.path.join(HERE, "stats.json")))
    s["POSTHOC_EXPLORATORY_not_preregistered"] = o
    json.dump(s, open(os.path.join(HERE, "stats.json"), "w"), indent=1)
    print(json.dumps(o, indent=1))


if os.environ.get("TRIAGE_POSTHOC"):
    posthoc()
