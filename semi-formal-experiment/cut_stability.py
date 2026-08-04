"""CUT-STABILITY DIAGNOSTIC — how far does the label-free cut move, and who
lives in its blast radius?

WHY THIS EXISTS. In all three iteration cycles (ITERATION_LOOP.md cycle log),
clause m0422 was admitted by THRESHOLD DRIFT: its own score never moved, but
the Otsu cut settled a hair lower whenever any other scores moved, and m0422
sat just under the old cut. Three blinded adjudication runs called it a
regression each time, charged to the cut rule rather than the edges. The
standing escalation in cycle 3's decision file puts the Otsu rule formally
under suspicion and gates any overlay widening on this diagnostic: before
adding edges we must know whether m0422 is a rare edge case or one of a
standing population of near-cut bystanders that ANY score movement can flip.

WHAT IT MEASURES, per behaviour, over the frozen snapshots:

  1. CUT SENSITIVITY — perturb the recorded score distribution in controlled,
     label-free ways (bootstrap resampling of the clause scores; uniform
     jitter; deleting the k highest scores; deleting the k highest scores
     BELOW the cut, m0422's own neighbourhood) and report the distribution of
     the recomputed cut: its movement band and how many clauses' scores fall
     inside that band (the bystander population — the class m0422 belongs to).
  2. BYSTANDER CENSUS — the clauses within ±epsilon of the recorded cut, for
     several epsilons: counts in the printed summary, ids in the artifact.
  3. RULE COMPARISON — the same analysis under other label-free rules from
     threshold.py (isodata, triangle, kneedle), so the report says whether
     Otsu is unusually wobbly or every distribution-shape rule is.

WHY THIS MODULE IS NOT IN QUERY_MODULES (test_no_reference_leak.py). Same
posture as check_taxonomy.py: DIAGNOSTIC ONLY. It answers no relevance query
and produces no operating point that any query path consumes — it re-derives
numbers from an already-frozen artifact so a claim ("the cut is stable") is
checked rather than believed. Its only inputs are the frozen snapshot files
and the rules in threshold.py (itself a scanned query module); it never opens
a clause, annotation, or atom artifact, and it never touches the evaluation
reference — the same fence-clean discipline is pinned by test_cut_stability.py
with a static source scan and an open-spy over a full run().

DETERMINISM CONTRACT. Same snapshots in, byte-identical results file out.
The RNG is seeded with the fixed literal SEED below; no wall clock anywhere;
keys sorted on dump; floats rounded to snapshot.PRECISION-compatible places.

Usage:
    .venv/bin/python cut_stability.py
"""
from __future__ import annotations

import json
import math
import os
import random

import threshold as threshold_rules

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(HERE, "snapshots")

#: The frozen snapshots this diagnostic reads by default: the current baseline
#: and the shippable configuration (cycle 3's KEEP).
DEFAULT_TAGS = ("baseline-2026-08-03", "containment-v1.1-kindinherit")

OUT_PATH = os.path.join(HERE, "cut_stability_results.json")

#: Fixed literal seed — the whole determinism contract hangs on this being a
#: literal, which test_cut_stability.py pins statically.
SEED = 20260803

N_BOOTSTRAP = 200          #: bootstrap resamples of the clause-score vector
N_JITTER = 100             #: jitter trials
JITTER_DELTA = 0.01        #: uniform jitter half-width, in score units —
                           #: comparable to real observed flip movement (≥1e-3)
REMOVE_KS = (1, 2, 3, 5)   #: deletion sizes for the remove-top-k probes
EPSILONS = (0.005, 0.01, 0.02, 0.05)   #: census half-widths around the cut

#: Rules compared. First is threshold.PREFERRED (the rule under suspicion);
#: the others are parameter-free comparators from the same registered table,
#: so the comparison is like-for-like distribution-shape rules.
RULE_NAMES = ("otsu", "isodata", "triangle", "kneedle")

#: Same rounding places as snapshot.PRECISION, for the same reason: recorded
#: numbers must not differ across processes in the last ulp.
PRECISION = 10


def _r(x: float) -> float:
    return round(float(x), PRECISION) + 0.0


# ---------------------------------------------------------------- statistics

def _quantile(sorted_vals, q):
    """Nearest-rank quantile over an already-sorted list. Deterministic."""
    n = len(sorted_vals)
    if n == 0:
        return None
    idx = min(n - 1, max(0, int(math.ceil(q * n)) - 1))
    return sorted_vals[idx]


def band_stats(cuts) -> dict:
    """Summary of a cut distribution. Degenerate sentinel cuts (a resample
    with fewer than two distinct scores) are counted, then excluded — a
    sentinel of 2.0 is not a cut position and would swamp every band."""
    real = sorted(c for c in cuts if c < threshold_rules.DEGENERATE_CUT)
    n = len(real)
    out = {"n": n, "n_degenerate": len(cuts) - n}
    if n == 0:
        out.update({"min": None, "max": None, "mean": None, "sd": None,
                    "q05": None, "q50": None, "q95": None, "band_width": None})
        return out
    mu = sum(real) / n
    sd = math.sqrt(sum((c - mu) ** 2 for c in real) / n)
    q05, q50, q95 = (_quantile(real, q) for q in (0.05, 0.50, 0.95))
    out.update({"min": _r(real[0]), "max": _r(real[-1]), "mean": _r(mu),
                "sd": _r(sd), "q05": _r(q05), "q50": _r(q50), "q95": _r(q95),
                "band_width": _r(q95 - q05)})
    return out


# ------------------------------------------------------------- bystanders

def band_bystanders(scores: dict, lo: float, hi: float) -> list:
    """Sorted ids whose score lies in [lo, hi] — with the same strictly-
    positive requirement threshold.predict applies, so a zero-score clause is
    never counted as a bystander at any band."""
    return sorted(cid for cid, s in scores.items() if s > 0 and lo <= s <= hi)


def bystander_census(scores: dict, cut: float, epsilons=EPSILONS) -> dict:
    """{str(eps): {count, ids}} for clauses within ±eps of the cut."""
    out = {}
    for eps in epsilons:
        ids = band_bystanders(scores, cut - eps, cut + eps)
        out[str(eps)] = {"count": len(ids), "ids": ids}
    return out


# ------------------------------------------------------------ perturbations

def _cut(rule_name: str, vals) -> float:
    return threshold_rules.apply_rule(rule_name, list(vals))


def bootstrap_cuts(rule_name, vals, n, rng) -> list:
    """Cuts over n with-replacement resamples of the positive score vector."""
    out = []
    for _ in range(n):
        sample = rng.choices(vals, k=len(vals))
        out.append(_cut(rule_name, sample))
    return out


def jitter_cuts(rule_name, vals, n, delta, rng) -> list:
    """Cuts after adding uniform(-delta, +delta) noise to every score,
    floored at a tiny positive so a jittered clause stays in the positive
    population rather than silently leaving it."""
    out = []
    for _ in range(n):
        jittered = [max(1e-9, v + rng.uniform(-delta, delta)) for v in vals]
        out.append(_cut(rule_name, jittered))
    return out


def remove_top_k_cut(rule_name, vals, k) -> float:
    """Cut after deleting the k highest scores — does the top of the
    distribution anchor the cut?"""
    kept = sorted(vals)[:-k] if k < len(vals) else []
    return _cut(rule_name, kept) if len(kept) >= 2 else \
        threshold_rules.DEGENERATE_CUT


def remove_top_k_below_cut(rule_name, vals, cut, k) -> float:
    """Cut after deleting the k highest scores STRICTLY BELOW the current cut
    — the near-cut sub-threshold mass, exactly m0422's neighbourhood. If the
    cut chases the deleted mass downward, drift-admission is structural."""
    below = sorted(v for v in vals if v < cut)
    above = [v for v in vals if v >= cut]
    kept = below[:-k] if k < len(below) else []
    kept = kept + above
    return _cut(rule_name, kept) if len(kept) >= 2 else \
        threshold_rules.DEGENERATE_CUT


# ------------------------------------------------------------------ engine

def analyze_behaviour(beh: dict, rng) -> dict:
    """The full diagnostic for one behaviour's recorded scores."""
    scores = beh["scores"]
    recorded_cut = float(beh.get("threshold", 0.0))
    positives = sorted(s for s in scores.values() if s > 0)

    rules = {}
    for rule_name in RULE_NAMES:
        cut = _r(_cut(rule_name, positives))
        boot = bootstrap_cuts(rule_name, positives, N_BOOTSTRAP, rng)
        jit = jitter_cuts(rule_name, positives, N_JITTER, JITTER_DELTA, rng)
        bstats = band_stats(boot)
        jstats = band_stats(jit)
        boot_band = (band_bystanders(scores, bstats["q05"], bstats["q95"])
                     if bstats["q05"] is not None else [])
        jit_band = (band_bystanders(scores, jstats["q05"], jstats["q95"])
                    if jstats["q05"] is not None else [])
        rules[rule_name] = {
            "cut": cut,
            "bootstrap": {"stats": bstats,
                          "band_bystanders": {"count": len(boot_band),
                                              "ids": boot_band}},
            "jitter": {"delta": JITTER_DELTA, "stats": jstats,
                       "band_bystanders": {"count": len(jit_band),
                                           "ids": jit_band}},
            "remove_top_k": {
                str(k): _r(remove_top_k_cut(rule_name, positives, k))
                for k in REMOVE_KS},
            "remove_top_k_below_cut": {
                str(k): _r(remove_top_k_below_cut(rule_name, positives,
                                                  cut, k))
                for k in REMOVE_KS},
        }

    preferred = threshold_rules.PREFERRED
    return {
        "recorded_cut": _r(recorded_cut),
        "recomputed_preferred_cut": rules[preferred]["cut"],
        "recomputed_matches_recorded":
            rules[preferred]["cut"] == _r(recorded_cut),
        "n_scores": len(scores),
        "n_positive": len(positives),
        "census": bystander_census(scores, recorded_cut, EPSILONS),
        "rules": rules,
    }


def run(snapshot_dir: str = SNAPSHOT_DIR, tags=DEFAULT_TAGS,
        out_path: str = OUT_PATH) -> dict:
    """Load the frozen snapshots, run the diagnostic, write the artifact.

    The RNG is re-seeded here with the literal SEED and consumed in a fixed
    iteration order (given tag order, sorted slugs, fixed rule order), so the
    artifact is byte-identical across runs and machines.
    """
    rng = random.Random(SEED)
    snapshots = {}
    for tag in tags:
        with open(os.path.join(snapshot_dir, f"{tag}.json")) as f:
            snap = json.load(f)
        snapshots[tag] = {
            slug: analyze_behaviour(snap["behaviours"][slug], rng)
            for slug in sorted(snap["behaviours"])}

    results = {
        "seed": SEED,
        "params": {"n_bootstrap": N_BOOTSTRAP, "n_jitter": N_JITTER,
                   "jitter_delta": JITTER_DELTA,
                   "remove_ks": list(REMOVE_KS),
                   "epsilons": [str(e) for e in EPSILONS],
                   "rules": list(RULE_NAMES),
                   "preferred_rule": threshold_rules.PREFERRED},
        "snapshots": snapshots,
    }
    with open(out_path, "wb") as f:
        f.write((json.dumps(results, sort_keys=True, indent=1,
                            ensure_ascii=False) + "\n").encode("utf-8"))
    print(format_summary(results))
    print(f"wrote {out_path}")
    return results


# ----------------------------------------------------------------- report

def format_summary(results: dict) -> str:
    """Counts and bands only — ids live in the artifact."""
    lines = ["# cut-stability diagnostic"]
    for tag, behaviours in sorted(results["snapshots"].items()):
        lines.append(f"\n## snapshot {tag}")
        for slug, b in sorted(behaviours.items()):
            lines.append(
                f"\n### {slug}  (recorded cut {b['recorded_cut']:.4f}, "
                f"{b['n_positive']} positive scores"
                + ("" if b["recomputed_matches_recorded"]
                   else "; NOTE recomputed preferred cut "
                        f"{b['recomputed_preferred_cut']:.4f} != recorded")
                + ")")
            for eps, c in sorted(b["census"].items(), key=lambda kv:
                                 float(kv[0])):
                lines.append(f"  census ±{eps}: {c['count']} clauses")
            for rule, r in ((n, b["rules"][n]) for n in
                            results["params"]["rules"]):
                bs, js = r["bootstrap"]["stats"], r["jitter"]["stats"]
                lines.append(
                    f"  {rule:<9} cut {r['cut']:.4f}  "
                    f"boot band [{bs['q05']:.4f},{bs['q95']:.4f}] "
                    f"w={bs['band_width']:.4f} "
                    f"bystanders={r['bootstrap']['band_bystanders']['count']}"
                    f"  jitter w={js['band_width']:.4f} "
                    f"bystanders={r['jitter']['band_bystanders']['count']}")
                drops = ", ".join(
                    f"k={k}:{v:.4f}" for k, v in
                    sorted(r["remove_top_k_below_cut"].items(),
                           key=lambda kv: int(kv[0])))
                lines.append(f"            remove-top-k-below-cut → {drops}")
    return "\n".join(lines)


if __name__ == "__main__":
    run()
