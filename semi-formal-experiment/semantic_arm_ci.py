"""semantic_arm_ci.py — paired bootstrap CIs for the semantic arm's AUC deltas.

A +0.036 mean AUC difference is not a result without an interval. This resamples
PASSAGES (not cells) within each cell, recomputes both scorers' AUC on the same
resample, and reports the paired delta — the same shape as
`weight_diag.paired_bootstrap`, which bootstraps predictions rather than scores.

Diagnostic only. Pre-registration: SEMANTIC_ARM_PREREGISTRATION.md.
"""

from __future__ import annotations

import os
import random
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

import semantic_arm as SA
import weight_diag as W

N_BOOT = 2000
SEED = 20260806


def _auc(scores, y, idx):
    s = [scores[i] for i in idx]
    yy = [y[i] for i in idx]
    if not (0 < sum(yy) < len(yy)):
        return None
    return W.auc(s, yy)


def paired_auc_delta(D, score_a, score_b, n=N_BOOT, seed=SEED):
    """mean over cells of AUC(b) - AUC(a), with a passage-level paired CI."""
    rng = random.Random(seed)
    cells = D.cells()
    A = {c: score_a(c[0]) for c in cells}
    B = {c: score_b(c[0]) for c in cells}
    point = sum(W.auc(B[c], D.golds[c]) - W.auc(A[c], D.golds[c])
                for c in cells) / len(cells)

    N = D.N
    draws = []
    for _ in range(n):
        idx = [rng.randrange(N) for _ in range(N)]
        vals = []
        for c in cells:
            y = D.golds[c]
            a, b = _auc(A[c], y, idx), _auc(B[c], y, idx)
            if a is not None and b is not None:
                vals.append(b - a)
        if vals:
            draws.append(sum(vals) / len(vals))
    draws.sort()
    lo = draws[int(0.025 * len(draws))]
    hi = draws[int(0.975 * len(draws))]
    return point, lo, hi


def main():
    D = W.data()
    av_a, pv_a, bv_a = SA.arm_a_vectors(D, 200)     # best-AUC document-internal k
    av_b, pv_b, bv_b = SA.arm_b_vectors(D)

    exact = lambda s: SA.exact_scores(D, s)
    soft_a = lambda s: SA.soft_scores(D, s, av_a, use_idf=False)
    soft_b = lambda s: SA.soft_scores(D, s, av_b, use_idf=False)

    rows = [
        ("A(lsa-200) soft-match  vs  exact anchor", exact, soft_a),
        ("B(openai)  soft-match  vs  exact anchor", exact, soft_b),
        ("B(openai)  soft-match  vs  A(lsa-200)", soft_a, soft_b),
    ]
    print(f"\n{'contrast':<42} {'dAUC':>7}  {'95% CI':>18}  verdict")
    print("-" * 84)
    for label, fa, fb in rows:
        p, lo, hi = paired_auc_delta(D, fa, fb)
        v = "excludes zero" if (lo > 0 or hi < 0) else "SPANS ZERO"
        print(f"{label:<42} {p:>+7.3f}  [{lo:+.3f}, {hi:+.3f}]  {v}")


if __name__ == "__main__":
    main()
