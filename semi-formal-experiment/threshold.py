"""Label-free operating points: choosing a cut WITHOUT reading the answer key.

WHY THIS MODULE EXISTS
----------------------
The shipped scorer RANKS far better than it DECIDES. On the true 589-passage
universe, over 9 (behaviour x pair-gold) cells:

    shipped tool, held-out (LOBO) threshold        +0.206
    shipped tool, ORACLE threshold                 +0.387   <- unreachable
    supervised readout of the SAME offline features +0.591
    judges (mean / best per behaviour)             +0.555 / +0.654

The 0.18 gap between LOBO and oracle is PURE CALIBRATION: same scores, same
ranking, different cut. `relevance.DEFAULT_THRESHOLD = 0.18` closes it only by
being the in-sample argmax of a 51-point grid over the panel — which is fitting
to the measuring instrument, and a live violation of contract §5 invariant 9.

So the question this module answers is NOT "which threshold scores best on the
panel". It is: **is there a rule that picks an operating point from the SCORE
DISTRIBUTION and the corpus alone — never from labels — that recovers any of
that 0.18?** A rule of that shape may legitimately be MEASURED on the panel,
because the panel was never an input to it. That is measurement, not fitting.

THE HARD LINE THIS MODULE HOLDS
-------------------------------
Nothing here may read the reference. Concretely:

  * no import of the scorer, the panel loader, or the universe reconstruction;
  * no file is opened, at all — every function is pure arithmetic over a
    vector of scores that the caller supplies;
  * no constant in this file was chosen by looking at a panel number.

`test_threshold.py` asserts all three mechanically (a source scan plus a spy on
every read path), because "I did not peek" is not a testable claim.

============================================================================
PRE-REGISTRATION — written and committed BEFORE any rule was evaluated
============================================================================
Selecting the best-scoring rule ON THE PANEL is the same error as selecting the
best threshold on the panel, one level up. So the preferred rule is named here
first, on a-priori grounds only, and every rule tried is reported afterwards —
winners and losers, in one table.

**PRE-REGISTERED PREFERRED RULE: `otsu`, applied per behaviour.**

Grounds, all available before any measurement:

 1. **Zero free parameters.** Otsu maximises between-class variance over the
    score histogram; there is no q, no k, no c, no window to choose. A rule
    with a tunable knob is a threshold search wearing a disguise — whoever
    picks the knob can pick the answer. This is the only strong argument
    available a priori and it is why `otsu` is preferred over `kneedle`
    (sensitive to axis scaling), `largest_gap` (needs a search window) and
    `mean_plus_sd` (needs c).
 2. **Per behaviour by construction.** Each behaviour has its own score
    distribution, so the rule yields its own cut. A single constant cannot be
    right for three behaviours whose distributions differ.
 3. **It is the standard answer to exactly this question** — unsupervised
    binarization of a one-dimensional score — and predates this project by
    fifty years, so it cannot have been reverse-engineered from these data.

Everything else below is registered as a COMPARATOR, not a candidate for the
headline: `isodata`, `triangle`, `kneedle`, `largest_gap`, `mean_plus_sd`
(c = 0.0 / 0.5 / 1.0), `top_q` (q = 0.05 / 0.10 / 0.25), `stability`, and
`top_k` driven by a corpus statistic supplied by the caller.

**Honesty note about the strength of this pre-registration.** It is weaker
than it looks. The brief that commissioned this module disclosed the measured
per-behaviour optima (0.18 / 0.18 / 0.58), so the author was not blind to the
panel when choosing. The pre-registration therefore constrains WHICH RULE IS
QUOTED AS THE HEADLINE; it does not make the author blind. Read the full table,
not the headline row.

============================================================================

WHAT A RULE IS
--------------
`rule(scores) -> float`, where `scores` is a dict `{id: score}` or any iterable
of floats, and the return value is a cut used with `predict()`, whose semantics
mirror `relevance.RelevanceIndex.predict`: a clause needs a strictly positive
score AND a score at or above the cut.

DEGENERATE INPUT
----------------
A scorer carrying no information (every clause the same score) must not be
handed a flattering cut. Every rule here returns `DEGENERATE_CUT`, a value
above any possible score, so the prediction is EMPTY. That scores exactly 0.0
MCC — chance — which is the honest report for a scorer that discriminates
nothing. The mirror bug (a degenerate run reading as a good one) is one this
project has already hit once, via `jaccard({}, {}) == 1.0`; `jaccard` here
returns 0.0 for two empty sets for that reason.
"""
from __future__ import annotations

import math

#: Returned when the score vector carries no information. Strictly greater than
#: 1.0, the maximum a normalized score can take, so `predict` yields the empty
#: set rather than the whole corpus.
DEGENERATE_CUT = 2.0

#: The grid the stability rule searches. Same 51 points the project's threshold
#: sweeps use, so a stability-selected cut is directly comparable to a swept
#: one. Not fitted: it is a discretization of [0, 1], not a choice about data.
GRID = tuple(round(0.02 * i, 2) for i in range(51))

#: Histogram resolution for the histogram-based rules. 256 is the classical
#: choice for Otsu (one bin per 8-bit grey level) and is finer than the 51-point
#: grid the project sweeps, so it cannot be the binding constraint.
BINS = 256


# ------------------------------------------------------------------ helpers

def values(scores) -> list:
    """The score vector as a plain sorted-ascending list of floats.

    Accepts a mapping (values are taken) or any iterable of numbers, so a
    caller may pass `index.rank(...)` output, a dict, or a bare list without
    the call site having to know which.
    """
    if hasattr(scores, "values") and callable(scores.values):
        vals = list(scores.values())
    else:
        vals = [v for v in scores]
    if vals and isinstance(vals[0], (tuple, list)):    # [(id, score), ...]
        vals = [v[1] for v in vals]
    return sorted(float(v) for v in vals)


def is_degenerate(vals) -> bool:
    """True when no cut can separate the vector: fewer than two distinct scores.

    Checked by every rule before it computes anything. A rule that "works" on a
    constant vector is reporting an artifact of its own tie-breaking.
    """
    return len(set(vals)) < 2


def predict(scores, cut: float) -> set:
    """`{id}` above the cut — the same rule `relevance.predict` applies.

    Requires a STRICTLY POSITIVE score as well as one at or above the cut, so
    `cut=0.0` means "anything with any signal", never "everything", and an
    all-zero scorer predicts nothing.
    """
    if not (hasattr(scores, "items") and callable(scores.items)):
        raise TypeError("predict needs a mapping of id -> score")
    return {k for k, v in scores.items() if v > 0 and v >= cut}


def jaccard(a, b) -> float:
    """|a & b| / |a | b|, and **0.0 when both sets are empty**.

    The convention matters. Defining `jaccard({}, {}) == 1.0` made an all-empty
    run report PERFECT self-agreement elsewhere in this project — a metric that
    reads best when the system fails worst. The stability rule below maximises
    exactly this quantity, so under the 1.0 convention it would drive the cut
    to the top of the grid, where every draw predicts nothing and every pair
    "agrees" completely.
    """
    a, b = set(a), set(b)
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _histogram(vals, bins: int = BINS):
    """`(counts, edges)` over [min, max]. `vals` must be sorted ascending."""
    lo, hi = vals[0], vals[-1]
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        i = int((v - lo) / width) if width > 0 else 0
        counts[min(i, bins - 1)] += 1
    edges = [lo + width * (i + 1) for i in range(bins)]
    return counts, edges


# -------------------------------------------------------------------- rules
#
# Every rule below takes the score vector and returns a cut. None takes a
# label, an id, a behaviour, or a path.

def otsu(scores, bins: int = BINS) -> float:
    """PRE-REGISTERED PREFERRED RULE. Otsu (1979), between-class variance.

    Splits the score histogram at the point maximising

        w0 * w1 * (mu0 - mu1)^2

    i.e. the cut under which the two induced groups are as far apart as the
    data allow. Fully unsupervised, no free parameter, and determined entirely
    by the shape of the score distribution.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    counts, edges = _histogram(vals, bins)
    n = len(vals)
    total = sum(c * (edges[i] - (edges[1] - edges[0]) / 2)
                for i, c in enumerate(counts))
    best, best_var, w0, sum0 = edges[0], -1.0, 0, 0.0
    for i, c in enumerate(counts):
        mid = edges[i] - (edges[1] - edges[0]) / 2
        w0 += c
        sum0 += c * mid
        w1 = n - w0
        if w0 == 0 or w1 == 0:
            continue
        mu0, mu1 = sum0 / w0, (total - sum0) / w1
        var = (w0 / n) * (w1 / n) * (mu0 - mu1) ** 2
        if var > best_var:
            best_var, best = var, edges[i]
    return best


def isodata(scores, max_iter: int = 100) -> float:
    """Ridler-Calvard iterative intermeans: the fixed point of

        t <- (mean of scores below t + mean of scores at or above t) / 2

    Also parameter-free, and a useful comparator for `otsu` because the two
    agree on clean bimodal data and diverge on skewed data — which tells the
    reader whether the score distribution is actually two-humped.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    t = sum(vals) / len(vals)
    for _ in range(max_iter):
        lo = [v for v in vals if v < t]
        hi = [v for v in vals if v >= t]
        if not lo or not hi:
            break
        new = (sum(lo) / len(lo) + sum(hi) / len(hi)) / 2
        if abs(new - t) < 1e-12:
            break
        t = new
    return t


def triangle(scores, bins: int = BINS) -> float:
    """Zack's triangle method: the histogram bin furthest from the line joining
    the histogram peak to the far end of the distribution.

    Designed for exactly the shape a relevance scorer produces — one dominant
    low-score mode with a long thin tail of hits, where Otsu's symmetric
    variance criterion can sit too low. Parameter-free.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    counts, edges = _histogram(vals, bins)
    peak = max(range(bins), key=lambda i: counts[i])
    # walk toward the high-score end
    end = bins - 1
    while end > peak and counts[end] == 0:
        end -= 1
    if end <= peak:
        return DEGENERATE_CUT
    x0, y0, x1, y1 = peak, counts[peak], end, counts[end]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1.0
    best, best_d = edges[peak], -1.0
    for i in range(peak, end + 1):
        d = abs(dy * (i - x0) - dx * (counts[i] - y0)) / norm
        if d > best_d:
            best_d, best = d, edges[i]
    return best


def kneedle(scores) -> float:
    """The knee of the sorted-descending score curve (Satopaa et al.).

    The knee is the rank furthest, perpendicularly, from the chord joining the
    highest and lowest scores. The knee is the first rank on the LOW side of
    the elbow, so the cut returned is the score of the rank before it —
    otherwise the knee's own (low) score would be admitted and the rule would
    predict the whole corpus on a clean hinge.

    Registered as a comparator rather than the preferred rule because it is NOT
    scale-invariant: the answer moves when the score axis is rescaled relative
    to the rank axis, and this project's scores are already normalized by an
    arbitrary corpus maximum.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    desc = vals[::-1]
    n = len(desc)
    x0, y0, x1, y1 = 0.0, desc[0], float(n - 1), desc[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1.0
    knee, best_d = 0, -1.0
    for i, v in enumerate(desc):
        d = abs(dy * (i - x0) - dx * (v - y0)) / norm
        if d > best_d:
            best_d, knee = d, i
    return desc[max(knee - 1, 0)]


def largest_gap(scores, lo_frac: float = 0.01, hi_frac: float = 0.50) -> float:
    """The cut at the widest gap between consecutive distinct scores, searched
    over the rank window `[lo_frac, hi_frac]` of the corpus.

    The window is a free parameter and is why this is a comparator, not the
    preferred rule: without one the widest gap is almost always between the
    single top score and the rest, which predicts a set of size one.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    desc = vals[::-1]
    n = len(desc)
    lo, hi = max(1, int(lo_frac * n)), max(2, int(hi_frac * n))
    best, best_gap = desc[0], -1.0
    for i in range(lo, min(hi, n)):
        gap = desc[i - 1] - desc[i]
        if gap > best_gap:
            best_gap, best = gap, desc[i - 1]
    return best


def mean_plus_sd(scores, c: float = 1.0) -> float:
    """`mean + c * sd` of the score vector. `c` is a free parameter."""
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    mu = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / len(vals))
    return mu + c * sd


def top_k(scores, k: int) -> float:
    """The score at rank `k` — a PREDICTION BUDGET, not a score criterion.

    `k` must come from the caller and must itself be label-free: a corpus
    statistic (e.g. how many clauses share any atom with the query) is
    legitimate; a number read off a panel curve is not. This function cannot
    check that, so the call site is where the invariant lives.
    """
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    k = max(1, min(int(k), len(vals)))
    return vals[::-1][k - 1]


def top_q(scores, q: float) -> float:
    """The score at the top-`q` quantile — `top_k` with k = q * n."""
    vals = values(scores)
    if not vals or is_degenerate(vals):
        return DEGENERATE_CUT
    return top_k(scores, max(1, int(round(q * len(vals)))))


def stability(score_vectors, grid=GRID) -> float:
    """The cut at which the PREDICTED SET is most stable across independent
    draws of the query — no labels anywhere.

    `score_vectors` is a list of `{id: score}` mappings, one per draw (this
    project has five independent draws of the behaviour atoms). For each cut on
    the grid the mean pairwise Jaccard of the predicted sets is computed, and
    the cut maximising it is returned.

    The reasoning: a cut that lands in a dense part of the score distribution
    puts many borderline clauses near the boundary, so resampling the query
    flips them; a cut in a sparse part is robust. That is a property of the
    scores alone.

    VACUOUS AGREEMENT IS EXCLUDED AT BOTH ENDS, and this is the whole
    difficulty with the rule. At the top of the grid every draw predicts
    NOTHING and every pair agrees; at the bottom every draw predicts
    EVERYTHING and every pair agrees. Neither is a decision. `jaccard` returns
    0.0 for two empty sets, which handles the top; the `full` check below
    handles the bottom. Without it the rule selects "predict every scored
    clause" — the all-positive predictor, whose MCC is 0 by construction — and
    on this project's real scores it did exactly that on all three behaviours.

    Ties are broken toward the LOWER cut, deterministically. If every cut on
    the grid is vacuous the rule reports `DEGENERATE_CUT` rather than picking
    one.
    """
    vecs = [v for v in score_vectors if v]
    if len(vecs) < 2:
        return DEGENERATE_CUT
    # Every draw scoring everything the same agrees perfectly at every cut.
    # That is no information, not maximal stability — and it is the exact shape
    # of the "metric reads best when the system fails worst" bug this project
    # has already shipped once.
    if all(is_degenerate(values(v)) for v in vecs):
        return DEGENERATE_CUT
    full = [{k for k, x in v.items() if x > 0} for v in vecs]
    best, best_s = DEGENERATE_CUT, -1.0
    for t in sorted(grid):
        preds = [predict(v, t) for v in vecs]
        if all(p == f for p, f in zip(preds, full)):
            continue                      # vacuous: "predict everything"
        pairs = [jaccard(preds[i], preds[j])
                 for i in range(len(preds)) for j in range(i + 1, len(preds))]
        s = sum(pairs) / len(pairs) if pairs else 0.0
        if s > best_s + 1e-12:
            best_s, best = s, t
    return best


#: Every rule this module offers, by the name the reports use. The preferred
#: rule is marked so a report cannot silently promote a comparator.
RULES = {
    "otsu": otsu,
    "isodata": isodata,
    "triangle": triangle,
    "kneedle": kneedle,
    "largest_gap": largest_gap,
    "mean+0.0sd": lambda s: mean_plus_sd(s, 0.0),
    "mean+0.5sd": lambda s: mean_plus_sd(s, 0.5),
    "mean+1.0sd": lambda s: mean_plus_sd(s, 1.0),
    "top_q=0.05": lambda s: top_q(s, 0.05),
    "top_q=0.10": lambda s: top_q(s, 0.10),
    "top_q=0.25": lambda s: top_q(s, 0.25),
}

#: The name of the pre-registered rule. Reports read this rather than hardcode
#: a string, so changing the headline requires changing the pre-registration.
PREFERRED = "otsu"

#: Rules that need more than one score vector, so they cannot live in `RULES`.
MULTI_VECTOR_RULES = {"stability": stability}


def apply_rule(name: str, scores) -> float:
    """`RULES[name](scores)`, with a clear error for an unknown name."""
    if name not in RULES:
        raise KeyError(f"unknown rule {name!r}; have {sorted(RULES)}")
    return RULES[name](scores)
