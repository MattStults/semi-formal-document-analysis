"""T-A1 (re-extraction drift / novelty) and T-A2 (vocabulary saturation).

Deterministic re-analysis of artifacts already on disk. **No network, no model
calls, no spend.** Seeded everywhere a random number is used.

Run:  .venv/bin/python tier1_assumptions.py
Writes: tier1_results.json  (and prints the same numbers)

Design notes that are load-bearing:

* **Denominator is all 593 clause ids in `modelspec_clauses.json`**, not the
  intersection of the passes' `by_clause` maps. A clause with atoms in one
  pass and none in the other is MAXIMAL drift and must be counted.
* **Canonical key is `containment.dechain_name`**, not `grammar.stem_of` —
  the latter merges `must_x` with `mustnot_x` (§1.2).
* **Resampling unit is the SECTION** (`section_id` on every clause), because
  batches are section-aligned so drift is correlated within a section.
* **The T-A2 permutation control is a finite-pool NULL, not evidence.** It
  re-orders a fixed per-clause atom pool, so it cannot distinguish a corpus
  whose forms keep arriving from one that saturated at clause 20. See
  `test_tier1_assumptions.py::test_permutation_destroys_the_arrival_dynamics_it_is_meant_to_control`.
"""
from __future__ import annotations

import json
import math
import os
import random

import containment

HERE = os.path.dirname(os.path.abspath(__file__))

CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
PASSES = {
    "bs14": "annotations.json",
    "bs8": "annotations_b8.json",
    "ext_v1": "annotations_ext_v1.json",
}
#: Pre-registered bar from ASSUMPTION_TESTS A-1a §3: A-1a survives iff the
#: expected novel-decision count on the RAW (upper-bound) diff is <= 40.
NOVEL_DECISION_BAR = 40
#: A-2 saturation criteria (ASSUMPTION_TESTS A-2 §1/§3).
BETA_BAR = 0.75
DECILE_RATIO_BAR = 0.40


# --------------------------------------------------------------- keys / IO


def canon(name: str) -> str:
    """The polarity-preserving canonical key. Identity on unchained names."""
    return containment.dechain_name(name)


def load_clause_ids(path: str = CLAUSES):
    d = json.load(open(path))
    return [c["id"] for c in d["clauses"]], {c["id"]: c["section_id"]
                                             for c in d["clauses"]}, d["source_sha256"]


def load_pass(path: str):
    d = json.load(open(os.path.join(HERE, path)))
    names = {cid: {a["name"] for a in atoms}
             for cid, atoms in d["by_clause"].items()}
    return {
        "names": names,
        "vocab": set(d["vocabulary"]),
        "prov": d["provenance"],
    }


def apply_key(names: dict, key) -> dict:
    return {cid: {key(n) for n in s} for cid, s in names.items()}


# ------------------------------------------------------------------- T-A1


def drift_pair(a_names, b_names, clause_ids, vocab_a, vocab_b, key=None):
    """p_drift / p_novel over `clause_ids` (the FULL denominator).

    drift  = the clause's atom-name set differs between the passes
             (a clause absent from a pass has the empty set — maximal drift).
    novel  = at least one name in the symmetric difference is absent from the
             OTHER pass's whole vocabulary, i.e. it is a fresh form rather
             than a re-alignment of a form the other pass already knows.
    """
    if key is not None:
        a_names, b_names = apply_key(a_names, key), apply_key(b_names, key)
        vocab_a = {key(n) for n in vocab_a}
        vocab_b = {key(n) for n in vocab_b}
    drifted, novel, per_clause = [], [], {}
    for cid in clause_ids:
        sa, sb = a_names.get(cid, set()), b_names.get(cid, set())
        d = sa != sb
        is_novel = False
        if d:
            drifted.append(cid)
            only_a, only_b = sa - sb, sb - sa
            fresh = [n for n in only_a if n not in vocab_b]
            fresh += [n for n in only_b if n not in vocab_a]
            is_novel = bool(fresh)
            if is_novel:
                novel.append(cid)
        per_clause[cid] = (1.0 if d else 0.0, 1.0 if is_novel else 0.0)
    n = len(clause_ids)
    p_drift = len(drifted) / n
    p_novel = (len(novel) / len(drifted)) if drifted else 0.0
    return {
        "n_clauses": n,
        "n_drift": len(drifted),
        "p_drift": p_drift,
        "n_novel": len(novel),
        "p_novel": p_novel,
        "expected_novel_decisions": n * p_drift * p_novel,
        "drifted": drifted,
        "novel_clauses": novel,
        "per_clause": per_clause,
    }


def cluster_bootstrap_mean(clusters, n_boot=2000, seed=0, alpha=0.05):
    """Percentile CI for the pooled mean, resampling CLUSTERS with replacement.

    `clusters` is a list of lists of values. Resampling clusters (not items)
    is what makes the interval honest when values inside a cluster are
    correlated.
    """
    clusters = [c for c in clusters if c]
    if not clusters:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    k = len(clusters)
    means = []
    for _ in range(n_boot):
        tot = cnt = 0.0
        for _ in range(k):
            c = clusters[rng.randrange(k)]
            tot += sum(c)
            cnt += len(c)
        means.append(tot / cnt)
    means.sort()
    lo = means[int(alpha / 2 * n_boot)]
    hi = means[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return (lo, hi)


def _clusters_of(per_clause, section_of, index):
    by_sec = {}
    for cid, vals in per_clause.items():
        by_sec.setdefault(section_of[cid], []).append(vals[index])
    return list(by_sec.values())


# ------------------------------------------------------------------- T-A2


def observed_curve(per_batch):
    """(cumulative clauses, cumulative COINED forms) from `vocabulary.per_batch`.

    x is cumulative CLAUSES, never batch index — the arms have batch sizes
    14 / 8 / 6 and would otherwise be on different axes.
    """
    ns, forms, n, f = [], [], 0, 0
    for row in per_batch:
        n += row["clauses"]
        f += row["coined"]
        ns.append(n)
        forms.append(f)
    return ns, forms


def curve_from_sets(by_clause, order):
    """F(n) = |union of atom names over the first n clauses of `order`|."""
    seen, out = set(), []
    for cid in order:
        seen |= by_clause.get(cid, set())
        out.append(len(seen))
    return out


def permuted_curves(by_clause, clause_ids, n_perm=200, seed=20260806):
    rng = random.Random(seed)
    ids = list(clause_ids)
    out = []
    for _ in range(n_perm):
        rng.shuffle(ids)
        out.append(curve_from_sets(by_clause, ids))
    return out


def mean_curve(curves):
    k = len(curves)
    return [sum(c[i] for c in curves) / k for i in range(len(curves[0]))]


def decile_rates(curve, window=100):
    """(forms per clause over the first `window`, over the last `window`)."""
    w = min(window, len(curve))
    first = curve[w - 1] / w
    last = (curve[-1] - curve[-1 - w]) / w if len(curve) > w else first
    return first, last


def heaps_beta(ns, forms, min_n=20):
    """OLS slope of log F on log n, over points with n >= min_n and F > 0."""
    xs = [math.log(n) for n, f in zip(ns, forms) if n >= min_n and f > 0]
    ys = [math.log(f) for n, f in zip(ns, forms) if n >= min_n and f > 0]
    k = len(xs)
    if k < 3:
        return float("nan")
    mx, my = sum(xs) / k, sum(ys) / k
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else float("nan")


# ------------------------------------------------------------------ report


def _fmt(x, p=4):
    return "nan" if x != x else f"{x:.{p}f}"


def main():
    clause_ids, section_of, doc_sha = load_clause_ids()
    passes = {k: load_pass(v) for k, v in PASSES.items()}

    out = {"doc_sha256": doc_sha, "n_clauses": len(clause_ids),
           "n_sections": len(set(section_of.values()))}
    print("=" * 78)
    print("T-A1 / T-A2  —  deterministic re-analysis, $0, seeded")
    print("=" * 78)

    # ---- precondition: same document bytes, and what else differs
    print("\n[precondition] source_sha256 per artifact")
    shas = {}
    for k, p in passes.items():
        pr = p["prov"]
        shas[k] = pr["source_sha256"]
        print(f"  {k:7s} {PASSES[k]:28s} sha={pr['source_sha256'][:16]}… "
              f"model={pr['model']} seed={pr['seed']} bs={pr['batch_size']} "
              f"nb={pr['n_batches']} docfacts={'docfacts' in pr} "
              f"evicted={pr['carried_atoms_evicted']}")
    print(f"  clauses artifact sha={doc_sha[:16]}…")
    same = len(set(shas.values()) | {doc_sha}) == 1
    print(f"  ALL THREE SHARE source_sha256 WITH THE CLAUSES ARTIFACT: {same}")
    out["source_sha256_agrees"] = same
    # arm detection: extended-prompt fields present on atoms?
    for k, p in passes.items():
        extra = set()
        for atoms in json.load(open(os.path.join(HERE, PASSES[k])))["by_clause"].values():
            for a in atoms:
                extra |= set(a) - {"name", "kind", "gloss", "span_id", "quote",
                                   "clause_id", "locator"}
        print(f"  {k:7s} extra per-atom fields: {sorted(extra) or '(none)'}")
        out.setdefault("arm_fields", {})[k] = sorted(extra)

    # ---------------------------------------------------------------- T-A1
    print("\n" + "-" * 78)
    print("T-A1  drift and novelty   (denominator = all %d clauses)" % len(clause_ids))
    print("-" * 78)
    pairs = [("bs14", "bs8"), ("bs14", "ext_v1"), ("bs8", "ext_v1")]
    out["T_A1"] = {"bar_expected_novel_decisions": NOVEL_DECISION_BAR, "pairs": {}}
    for a, b in pairs:
        row = {}
        for label, key in (("raw", None), ("dechained", canon)):
            r = drift_pair(passes[a]["names"], passes[b]["names"], clause_ids,
                           passes[a]["vocab"], passes[b]["vocab"], key=key)
            dcl = _clusters_of(r["per_clause"], section_of, 0)
            lo, hi = cluster_bootstrap_mean(dcl, n_boot=2000, seed=20260806)
            row[label] = {
                "p_drift": r["p_drift"], "n_drift": r["n_drift"],
                "p_drift_ci95_section_cluster": [lo, hi],
                "p_novel": r["p_novel"], "n_novel": r["n_novel"],
                "expected_novel_decisions": r["expected_novel_decisions"],
                "verdict_vs_bar": ("PASS" if r["expected_novel_decisions"]
                                   <= NOVEL_DECISION_BAR else "FAIL"),
            }
            print(f"  {a:6s} vs {b:6s} [{label:9s}]  "
                  f"p_drift={_fmt(r['p_drift'])} (n={r['n_drift']}) "
                  f"CI95[sec]=({_fmt(lo)},{_fmt(hi)})  "
                  f"p_novel={_fmt(r['p_novel'])} (n={r['n_novel']})  "
                  f"E[novel decisions]={r['expected_novel_decisions']:.1f} "
                  f"-> {row[label]['verdict_vs_bar']} vs bar {NOVEL_DECISION_BAR}")
        out["T_A1"]["pairs"][f"{a}|{b}"] = row

    # pooled over all three
    pooled_drift = pooled_novel = 0
    per_clause = {}
    for cid in clause_ids:
        sets = {k: passes[k]["names"].get(cid, set()) for k in PASSES}
        vals = list(sets.values())
        d = any(v != vals[0] for v in vals[1:])
        nv = False
        if d:
            pooled_drift += 1
            for k in PASSES:
                others = set().union(*[passes[o]["vocab"] for o in PASSES if o != k])
                if any(n not in others for n in sets[k]):
                    nv = True
            if nv:
                pooled_novel += 1
        per_clause[cid] = (1.0 if d else 0.0, 1.0 if nv else 0.0)
    pd = pooled_drift / len(clause_ids)
    pn = pooled_novel / pooled_drift if pooled_drift else 0.0
    lo, hi = cluster_bootstrap_mean(_clusters_of(per_clause, section_of, 0),
                                    n_boot=2000, seed=20260806)
    print(f"  POOLED (3 passes, raw)              p_drift={_fmt(pd)} "
          f"(n={pooled_drift}) CI95[sec]=({_fmt(lo)},{_fmt(hi)})  "
          f"p_novel={_fmt(pn)} (n={pooled_novel})  "
          f"E[novel decisions]={len(clause_ids) * pd * pn:.1f}")
    out["T_A1"]["pooled_raw"] = {
        "p_drift": pd, "n_drift": pooled_drift,
        "p_drift_ci95_section_cluster": [lo, hi],
        "p_novel": pn, "n_novel": pooled_novel,
        "expected_novel_decisions": len(clause_ids) * pd * pn,
    }

    # ---------------------------------------------------------------- T-A2
    print("\n" + "-" * 78)
    print("T-A2  vocabulary saturation")
    print("-" * 78)
    out["T_A2"] = {}
    for k, p in passes.items():
        pb = p["prov"]["vocabulary"]["per_batch"]
        bns, bforms = observed_curve(pb)  # recorded, at BATCH resolution
        # per-CLAUSE curve, rebuilt in document (== processing) order, so that
        # the observed and permuted curves are the same function of the same
        # data and the 100-clause windows mean the same thing on both.
        obs = curve_from_sets(p["names"], clause_ids)
        ns = list(range(1, len(obs) + 1))
        forms = obs
        # cross-check the rebuild against the recorded per-batch coined counts
        chk = [obs[n - 1] for n in bns]
        agree = all(a == b for a, b in zip(chk, bforms))
        print(f"\n  [check] {k}: rebuilt per-clause curve matches recorded "
              f"cumulative `coined` at all {len(bns)} batch boundaries: {agree}"
              f"  (final rebuilt={obs[-1]} recorded_coined={bforms[-1]})")
        beta_o = heaps_beta(ns, forms, min_n=20)
        f_o, l_o = decile_rates(forms, window=100)
        v = p["prov"]["vocabulary"]
        curves = permuted_curves(p["names"], clause_ids, n_perm=200, seed=20260806)
        mc = mean_curve(curves)
        beta_p = heaps_beta(list(range(1, len(mc) + 1)), mc, min_n=20)
        f_p, l_p = decile_rates(mc, window=100)
        sat_o = (beta_o < BETA_BAR) and (l_o < DECILE_RATIO_BAR * f_o)
        sat_p = (beta_p < BETA_BAR) and (l_p < DECILE_RATIO_BAR * f_p)
        print(f"  arm {k}  ({PASSES[k]})")
        print(f"    recorded reuse_rate={v['reuse_rate']}  coined={v['coined']} "
              f"reused={v['reused']}  distinct={v['distinct_names']}")
        print(f"    OBSERVED  n_max={ns[-1]}  F(n_max)={forms[-1]}  "
              f"beta={_fmt(beta_o, 3)}  first100={_fmt(f_o, 3)}/clause  "
              f"last100={_fmt(l_o, 3)}/clause  ratio={_fmt(l_o / f_o, 3)}  "
              f"-> saturates={sat_o}")
        print(f"    PERMUTED  n_max={len(mc)} F(n_max)={mc[-1]:.0f}  "
              f"beta={_fmt(beta_p, 3)}  first100={_fmt(f_p, 3)}/clause  "
              f"last100={_fmt(l_p, 3)}/clause  ratio={_fmt(l_p / f_p, 3)}  "
              f"-> saturates={sat_p}   [FINITE-POOL NULL — not evidence]")
        # last-quarter observed coining, the honest "still climbing?" read
        q = len(forms) // 4
        tail = (forms[-1] - forms[-1 - q]) / (ns[-1] - ns[-1 - q])
        head = forms[q] / ns[q]
        print(f"    observed coining rate  first quarter={_fmt(head, 3)}/clause  "
              f"last quarter={_fmt(tail, 3)}/clause")
        out["T_A2"][k] = {
            "reuse_rate": v["reuse_rate"], "coined": v["coined"],
            "reused": v["reused"], "distinct_names": v["distinct_names"],
            "batch_resolution_recorded_coined": bforms[-1],
            "rebuild_matches_recorded": agree,
            "observed": {"n_max": ns[-1], "F_max": forms[-1], "beta": beta_o,
                         "first100_per_clause": f_o, "last100_per_clause": l_o,
                         "ratio": l_o / f_o, "saturates": sat_o,
                         "first_quarter_rate": head, "last_quarter_rate": tail},
            "permuted_null": {"beta": beta_p, "first100_per_clause": f_p,
                              "last100_per_clause": l_p, "ratio": l_p / f_p,
                              "saturates": sat_p},
        }
    arms_sat = sum(1 for k in out["T_A2"] if out["T_A2"][k]["observed"]["saturates"])
    print(f"\n  OBSERVED curves meeting BOTH criteria: {arms_sat} of 3 "
          f"(decision rule wanted >= 2 of 3)")
    out["T_A2"]["arms_saturating_observed"] = arms_sat

    with open(os.path.join(HERE, "tier1_results.json"), "w") as f:
        json.dump(out, f, indent=1, default=list)
    print("\nwrote tier1_results.json")


if __name__ == "__main__":
    main()
