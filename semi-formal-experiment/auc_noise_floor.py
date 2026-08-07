"""THE NOISE FLOOR FOR THE RANKING AXIS (passage AUC) — the missing twin of
`breadth_filter.NOISE_FLOOR = (0.0316, 0.037)`.

WHY THIS FILE EXISTS
--------------------
The project has a re-derived noise floor for the DECIDING axis (mean MCC over
the panel cells) and none at all for the RANKING axis. `combined.MEASURED`
records `auc_mean: {structural: 0.6475, section: 0.7427, combined: 0.7425}` and
calls the +0.0002 `combined - section` gap "no effect" — a verdict stated
against no instrument. Any new ranking lever measured on this panel produces a
mean-AUC delta, and without a null distribution that delta cannot be read.

WHAT THE NUMBER MEANS
---------------------
The floor is the 95% half-width of a mean-AUC delta that is KNOWN TO BE ZERO:
two independent, label-free random rankings of the SAME universe, scored
against the SAME golds, aggregated exactly the way a real ranking result is
aggregated (AUC per (behaviour, held-out judge) cell -> mean over that
behaviour's cells -> mean over behaviours), with the resampling unit set to the
BEHAVIOUR.

A mean-AUC delta smaller than the floor is not a result on this data, whatever
the point estimate says. This is the same protocol as `benchmark.noise_floor`
(the spread of a delta known to be zero, averaged over cells) with two changes,
both forced by `HANDOFF.md`:

  * the resampling unit is the BEHAVIOUR, not the passage. `HANDOFF.md:1184`
    measured between-behaviour SD of the `structural - bag` delta at 0.0596
    against between-draw SD 0.0172 — ~12x in variance — and concluded that
    passage-unit intervals "ignore it entirely". Behaviours are drawn with
    replacement here; passages are never resampled.
  * the zero delta comes from two independent RANKINGS rather than two
    independent passage resamples, because AUC is a property of a ranking.

TWO SETTINGS, deliberately (this is how the MCC floor got its range: two
independent derivations, 0.0316 at 1000 resamples and 0.0350-0.0357 at 2000,
published as the range 0.0316-0.037). Setting A is 1000 resamples at one seed,
setting B is 2000 at another. The floor is reported as the RANGE spanned by
them, never as a point.

WHAT IT IS NOT
--------------
1. It is an UNPAIRED null. The two rankings share nothing. A real lever is
   usually a PAIRED variant of its baseline (same scores, different tiebreak),
   and `HANDOFF.md:1175-1180` is explicit that an unpaired floor is 2.1x-6.5x
   the paired SE and "would reject a true, perfectly-measured effect of 0.03
   forever". The shipped MCC floor is unpaired anyway, so this one is derived
   the same way for comparability — but a lever that clears the floor is a
   result, and a lever that does NOT clear it is NOT thereby shown to be zero.
   The honest gate for a paired lever is: clear this floor for a REPORTABLE
   effect, AND show a behaviour-clustered paired CI excluding zero.
2. It carries no BETWEEN-BEHAVIOUR HETEROGENEITY of the effect. Random rankers
   are exchangeable across behaviours, so every behaviour's null delta has mean
   zero; the 0.0596 between-behaviour SD that dominated the MCC contrast came
   from two real predictors disagreeing systematically per behaviour, and no
   label-free null can manufacture it. So this floor bounds RANKING-DRAW noise
   plus behaviour-sampling noise, and is a LOWER bound on the dispersion a real
   pair of rankers would show. Read it as "below this is certainly noise", not
   "above this is certainly signal".
3. It is not a lever result. Nothing in this file scores any query module,
   reads any atom draw, or touches `combined`/`section`/`structural`.

SENSITIVITIES (printed, not folded into the floor)
--------------------------------------------------
Real rankers are coarse: they emit few distinct levels and leave much of the
universe at exactly 0.0. The primary null uses a fully continuous random
ranking; the grid re-derives the floor under coarser null rankers. MEASURED,
not assumed: heavy dead mass shrinks the floor (a quarter-scored ranker gives
0.0169) but MODERATE coarsening slightly WIDENS it (16 tied levels gives
0.0228, above the continuous 0.0221). So the continuous primary is NOT the
conservative end across ranker shapes, and the operative bar quoted at the
bottom of the report is the grid-inclusive one. That correction is kept in the
file rather than smoothed away, because the first draft of this docstring
asserted the opposite and the grid refuted it.

RUN
    .venv/bin/python auc_noise_floor.py

Deterministic: fixed seeds, no wall clock, no set iteration order, no network,
no model calls. Same inputs -> same bytes.
"""
from __future__ import annotations

import random
import sys

import benchmark as B
import panel_v2

#: The ranking axis was measured on the 9-behaviour panel (`combined.MEASURED
#: ["ranking"]["per_behaviour_delta_combined_minus_section"]` names those
#: slugs), model-spec side. Loaded, never enumerated: no count is pinned here.
SPEC_KEY = "openai"

#: Verdict >= this counts as a judge saying "relevant" when building pair-gold.
#: `benchmark.pair_targets`' own default; not a free parameter of this file.
THRESHOLD = 1

#: The two independent settings. (resamples, seed). The MCC floor's range came
#: from two derivations at 1000 and 2000 resamples; matched here so the two
#: floors are read the same way.
SETTINGS = (("A", 1000, 20260806), ("B", 2000, 4242))

#: Coarseness sensitivity: (number of distinct random levels, fraction of the
#: universe the ranker scores at all). `None` levels means fully continuous.
#: A grid, NOT a selection — no entry of it is promoted to the floor.
COARSENESS = ((None, 1.0), (64, 1.0), (16, 1.0), (4, 1.0), (2, 1.0),
              (None, 0.5), (None, 0.25))


# --------------------------------------------------------------- the panel

def cells(spec_key: str = SPEC_KEY) -> dict:
    """`{slug: {"n": universe size, "golds": [gold index sets]}}`.

    One gold per held-out judge, exactly the pair-gold `benchmark.roc_targets`
    scores AUC against. Passages are carried as INDICES into a fixed sorted id
    list, because the null only ever needs set membership under a ranking, and
    an index makes the rank arithmetic exact and order-stable.
    """
    panel = panel_v2.load_panel()
    out = {}
    for slug in sorted(panel):
        beh = panel[slug]
        ps = B.passages(beh, spec_key)
        if not ps:
            continue
        ids = sorted({p["id"] for p in ps})
        pos = {pid: i for i, pid in enumerate(ids)}
        golds = []
        for _judge, t in sorted(B.pair_targets(beh, THRESHOLD, spec_key).items()):
            g = {pos[x] for x in t["gold"] if x in pos}
            if g and len(g) < len(ids):      # AUC is undefined otherwise
                golds.append(sorted(g))
        if golds:
            out[slug] = {"n": len(ids), "golds": golds}
    return out


# ------------------------------------------------------ AUC of a ranking

def auc_from_ranking(rank_of: list, gold: list, n: int) -> float:
    """Mann-Whitney AUC for a STRICT ranking given as `rank_of[i] = rank`.

    No ties, so the rank-sum identity is exact and there is no bisect loop:
    AUC = (sum of positive ranks - npos(npos+1)/2) / (npos * nneg).
    """
    npos = len(gold)
    nneg = n - npos
    s = 0
    for i in gold:
        s += rank_of[i]
    return (s - npos * (npos + 1) / 2) / (npos * nneg)


def auc_from_levels(level_of: list, gold: list, n: int, levels: int) -> float:
    """Mann-Whitney AUC for a ranking with TIES, ties counted 0.5.

    `level_of[i]` is an integer bucket; higher is better. Counted by bucket in
    O(n + levels), which is the same statistic `benchmark.auc` computes with
    its bisect loop (asserted in `_selfcheck`).
    """
    pos = [0] * levels
    neg = [0] * levels
    g = set(gold)
    for i in range(n):
        (pos if i in g else neg)[level_of[i]] += 1
    npos, nneg = len(gold), n - len(gold)
    below = 0
    total = 0.0
    for L in range(levels):
        total += pos[L] * (below + 0.5 * neg[L])
        below += neg[L]
    return total / (npos * nneg)


def behaviour_auc(cell: dict, rng: random.Random,
                  levels: int | None, active: float) -> float:
    """Mean AUC over one behaviour's golds, under ONE random ranking.

    The SAME random ranking scores all of that behaviour's golds, because a
    real ranker produces one ranking per behaviour and its cells are correlated
    through it. Drawing a fresh ranking per gold would understate the spread.

    `levels=None, active=1.0` is the primary: a uniformly random strict order
    over the whole universe. `active<1.0` leaves the rest of the universe tied
    at the bottom, the way a real ranker leaves everything it cannot reach at
    0.0. `levels` coarsens the scored part into that many tied buckets.
    """
    n = cell["n"]
    if levels is None and active >= 1.0:
        order = list(range(n))
        rng.shuffle(order)
        rank_of = [0] * n
        for r, i in enumerate(order, start=1):
            rank_of[i] = r
        return sum(auc_from_ranking(rank_of, g, n)
                   for g in cell["golds"]) / len(cell["golds"])

    k = max(1, min(n - 1, int(round(active * n))))
    order = list(range(n))
    rng.shuffle(order)
    scored, dead = order[:k], order[k:]
    nlev = (levels or k) + 1          # +1 for the dead bucket at the bottom
    level_of = [0] * n
    for i in dead:
        level_of[i] = 0
    if levels is None:
        for r, i in enumerate(scored, start=1):
            level_of[i] = r
    else:
        for i in scored:
            level_of[i] = 1 + rng.randrange(levels)
    return sum(auc_from_levels(level_of, g, n, nlev)
               for g in cell["golds"]) / len(cell["golds"])


# ------------------------------------------------------- the null itself

def null_deltas(cs: dict, resamples: int, seed: int,
                levels: int | None = None, active: float = 1.0,
                cluster: bool = True) -> list:
    """The sampling distribution of a mean-AUC delta that is exactly zero.

    One draw:
      1. resample the behaviour set WITH REPLACEMENT (the clustering step —
         `cluster=False` freezes the behaviour set and isolates the pure
         ranking-draw component, so the two can be reported separately the way
         `HANDOFF.md:1184` reports behaviour SD against draw SD for MCC);
      2. for each behaviour slot, draw TWO independent random rankings and take
         each one's mean AUC over that behaviour's golds;
      3. delta = mean over slots of (A - B).

    Both rankings see the identical universe and the identical golds, so the
    delta's expectation is zero by construction, with no appeal to any model.
    """
    rng = random.Random(seed)
    slugs = sorted(cs)
    out = []
    for _ in range(resamples):
        picked = ([slugs[rng.randrange(len(slugs))] for _ in slugs]
                  if cluster else slugs)
        d = 0.0
        for s in picked:
            a = behaviour_auc(cs[s], rng, levels, active)
            b = behaviour_auc(cs[s], rng, levels, active)
            d += a - b
        out.append(d / len(picked))
    out.sort()
    return out


def interval(deltas: list) -> dict:
    lo = deltas[int(0.025 * len(deltas))]
    hi = deltas[int(0.975 * len(deltas)) - 1]
    mean = sum(deltas) / len(deltas)
    var = sum((d - mean) ** 2 for d in deltas) / max(1, len(deltas) - 1)
    return {"n": len(deltas), "lo": lo, "hi": hi, "half_width": (hi - lo) / 2,
            "mean": mean, "sd": var ** 0.5}


# ---------------------------------------------------------------- checks

def _selfcheck(cs: dict) -> list:
    """Prove the fast AUC paths equal `benchmark.auc` before quoting them."""
    rng = random.Random(1)
    slug = sorted(cs)[0]
    cell = cs[slug]
    n, gold = cell["n"], cell["golds"][0]
    lines = []

    order = list(range(n))
    rng.shuffle(order)
    rank_of = [0] * n
    for r, i in enumerate(order, start=1):
        rank_of[i] = r
    mine = auc_from_ranking(rank_of, gold, n)
    theirs = B.auc({i: rank_of[i] for i in range(n)}, set(gold), set(range(n)))
    assert abs(mine - theirs) < 1e-12, (mine, theirs)
    lines.append(f"  strict-ranking AUC == benchmark.auc  ({mine:.6f})")

    level_of = [rng.randrange(5) for _ in range(n)]
    mine = auc_from_levels(level_of, gold, n, 5)
    theirs = B.auc({i: level_of[i] for i in range(n)}, set(gold), set(range(n)))
    assert abs(mine - theirs) < 1e-12, (mine, theirs)
    lines.append(f"  tied-levels AUC   == benchmark.auc  ({mine:.6f})")
    return lines


# ---------------------------------------------------------------- report

def report() -> str:
    cs = cells()
    n_beh = len(cs)
    n_cells = sum(len(c["golds"]) for c in cs.values())
    out = ["=" * 74,
           "NOISE FLOOR FOR THE RANKING AXIS (mean passage AUC)",
           "=" * 74, "",
           f"panel: panel_v2 / {SPEC_KEY} — {n_beh} behaviours, {n_cells} "
           f"(behaviour, held-out judge) AUC cells",
           f"universe sizes: {sorted({c['n'] for c in cs.values()})}",
           "gold: pair-gold (both held-out judges at >= "
           f"{THRESHOLD}), per benchmark.pair_targets", "",
           "self-check:"]
    out += _selfcheck(cs)
    out += ["",
            "NULL: two independent label-free random rankings of the same "
            "universe,",
            "      scored against the same golds; behaviours resampled with "
            "replacement.", ""]

    floors = []
    primary = {}
    for name, resamples, seed in SETTINGS:
        d = interval(null_deltas(cs, resamples, seed))
        primary[name] = d
        floors.append(d["half_width"])
        out.append(f"setting {name}: {resamples} resamples, seed {seed}")
        out.append(f"    null delta 95% interval [{d['lo']:+.4f}, "
                   f"{d['hi']:+.4f}]  (mean {d['mean']:+.5f}, sd {d['sd']:.4f})")
        out.append(f"    ** floor (half-width): {d['half_width']:.4f} **")
    lo, hi = min(floors), max(floors)
    out += ["",
            f"==> AUC NOISE FLOOR = {lo:.4f}-{hi:.4f} "
            "(mean AUC over behaviours)",
            "    State no ranking verdict that fails at "
            f"{hi:.4f}.", ""]

    out += ["variance decomposition (the HANDOFF.md:1184 read, for AUC):"]
    for name, resamples, seed in SETTINGS:
        drawonly = interval(null_deltas(cs, resamples, seed, cluster=False))
        full = primary[name]
        ratio = (full["sd"] / drawonly["sd"]) ** 2 if drawonly["sd"] else 0.0
        out.append(f"    setting {name}: ranking-draw SD {drawonly['sd']:.4f} "
                   f"-> behaviour-clustered SD {full['sd']:.4f} "
                   f"({ratio:.2f}x in variance)")
    out += ["    Unlike MCC, behaviour clustering barely widens this null: a "
            "random ranker is",
            "    exchangeable across behaviours, so the null carries no "
            "between-behaviour",
            "    heterogeneity of the effect. See limitation 2 in the "
            "docstring.", ""]

    out += ["coarseness sensitivity (2000 resamples, seed 4242) — a GRID, not "
            "a selection:",
            "    levels  active  floor"]
    grid = []
    for levels, active in COARSENESS:
        d = interval(null_deltas(cs, 2000, 4242, levels=levels, active=active))
        grid.append(d["half_width"])
        out.append(f"    {str(levels or 'cont'):>6}  {active:>6.2f}  "
                   f"{d['half_width']:.4f}")
    bar = max(grid + floors)
    out += ["    Heavy dead mass shrinks the null (ties drag AUC to 0.5); "
            "moderate coarsening",
            "    slightly WIDENS it. The continuous primary is therefore not "
            "the widest shape,",
            f"    and the operative bar below is the grid-inclusive "
            f"{bar:.4f}.", ""]

    out += ["HOW TO USE IT",
            f"  * a mean-AUC delta below {lo:.4f} is indistinguishable from "
            "ranking noise;",
            f"  * between {lo:.4f} and {bar:.4f} it straddles the floor — say "
            "so, do not round;",
            f"  * above {bar:.4f} it is reportable AS A MAGNITUDE, and still "
            "needs a",
            "    behaviour-clustered paired CI excluding zero before it is a "
            "WIN.",
            "  * the recorded combined-minus-section ranking gap (+0.0002, "
            "combined.MEASURED)",
            "    is two orders of magnitude under the floor: that null was "
            "never at risk.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    sys.stdout.write(report() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
