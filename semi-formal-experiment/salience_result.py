"""THE PRE-REGISTERED MEASUREMENT of the speech-act salience tier (R4).

Runs `PREREG_salience_ranking.md` exactly as frozen. Nothing here chooses a
configuration: the lever is `salience.Index` at its DEFAULT precedence and
DEFAULT tier order, the baseline is the same underlying ranker without the
tier (`section.SectionQuotient.rank`), and both are scored in THIS run against
the SAME panel and the SAME gold rule `auc_noise_floor.py` uses.

⛔ THE MEASUREMENT PROBLEM THIS FILE HAD TO SOLVE, STATED BEFORE THE NUMBERS
---------------------------------------------------------------------------
The lever is ORDER-ONLY: `salience.Index.rank` returns the baseline's
`(clause_id, score)` pairs PERMUTED, with no score touched (R4 guard 1). The
shipped AUC path is `benchmark.passage_scores(dict(ranked), joins)` — it takes
`dict(...)` of those pairs and therefore DISCARDS THE ORDER. Under the shipped
path the lever's AUC delta is exactly 0.0 by construction, for every panel,
every gold and every aggregation, before any data is read. That is a property
of the instrument, not a result about speech acts, and it is reported below as
arm SCORE-LIFT so it cannot be mistaken for one.

So the pre-registered AUC is computed under a POSITION LIFT: each arm's own
returned ORDER is turned into a strict descending score (best-ranked clause
scores highest), lifted to passages by the same MAX rule `passage_scores` uses,
and scored with the same `benchmark.auc`. Both arms get the identical
treatment; the ONLY difference between them is the order their ranker returned.
This is the only lift under which an order-only lever is visible at all.

AGGREGATION (fixed by the pre-registration + `auc_noise_floor.py`)
    AUC per (behaviour, atom draw, held-out judge) cell
      -> mean over that behaviour's cells
      -> mean over behaviours.
    RESAMPLING UNIT: the BEHAVIOUR, never the passage (`HANDOFF.md:1128-1138`).

GATE (frozen, both required)
    delta > 0.0228 (the grid-inclusive operative bar of `auc_noise_floor.py`)
    AND a behaviour-clustered paired CI excluding zero.
    Either alone is a NULL.

RUN
    .venv/bin/python salience_result.py

Deterministic: fixed seeds, no wall clock, no network, no model calls, $0.
"""
from __future__ import annotations

import json
import os
import random
import sys

import benchmark as B
import panel_v2
import relevance
import salience
import section as SEC
import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))

SPEC_KEY = "openai"
THRESHOLD = 1                      # `auc_noise_floor.THRESHOLD`
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
TOP_K = (1, 3, 5)
BOOT_RESAMPLES = 20000
BOOT_SEED = 20260806

#: The grid-inclusive operative bar printed by `auc_noise_floor.py`.
OPERATIVE_BAR = 0.0228
#: Transcribed, provenance-unverifiable — a SANITY REFERENCE ONLY, per the
#: pre-registration's amendment. Never the comparator.
TRANSCRIBED_SECTION_AUC = 0.7427


# ------------------------------------------------------------------ panel

def cells(panel: dict) -> dict:
    """`{slug: {"universe": [pid], "golds": [[pid]]}}` — the SAME panel and the
    SAME gold rule as `auc_noise_floor.cells`, carrying passage ids instead of
    indices because a real ranker has to score them."""
    out = {}
    for slug in sorted(panel):
        beh = panel[slug]
        ps = B.passages(beh, SPEC_KEY)
        if not ps:
            continue
        ids = sorted({p["id"] for p in ps})
        idset = set(ids)
        golds = []
        for _j, t in sorted(B.pair_targets(beh, THRESHOLD, SPEC_KEY).items()):
            g = sorted(set(t["gold"]) & idset)
            if g and len(g) < len(ids):     # AUC undefined otherwise
                golds.append(g)
        if golds:
            out[slug] = {"universe": ids, "golds": golds}
    return out


# ------------------------------------------------------------------- lift

def position_scores(ranked_pairs, joins: dict) -> dict:
    """`{passage id: score}` from an ARM'S OWN ORDER.

    The order is turned into a strict descending score (rank 1 -> len(order)),
    then lifted to passages by MAX over the clauses joining to them — the same
    rule `benchmark.passage_scores` uses. A passage joining nothing scores 0.0
    and STAYS IN THE DENOMINATOR (also `passage_scores`' rule); 0.0 is below
    every positional score, which starts at 1.
    """
    n = len(ranked_pairs)
    pos = {cid: n - i for i, (cid, _s) in enumerate(ranked_pairs)}
    return {pid: max([pos.get(c, 0) for c in cids], default=0)
            for pid, cids in joins.items()}


def topk_precision(scores: dict, gold, universe, k: int) -> float:
    """|top-k ∩ gold| / k. Ties broken by passage id ascending — deterministic
    and identical for both arms, so no arm can win on tie-break luck."""
    u = sorted(universe)
    ranked = sorted(u, key=lambda x: (-scores.get(x, 0.0), x))
    g = set(gold)
    kk = min(k, len(ranked))
    return sum(1 for x in ranked[:kk] if x in g) / k


# ------------------------------------------------------------ measurement

def measure(panel: dict, clauses, ann: dict, draws: list) -> dict:
    """Per-behaviour AUC and top-k for BOTH arms, plus the R4 guard-1 check."""
    cs = cells(panel)
    slugs = sorted(cs)
    joins = {s: B.clause_joins(panel[s], clauses, SPEC_KEY) for s in slugs}

    sidx = S.StructuralIndex(clauses, ann)
    base_idx = SEC.SectionQuotient(sidx)
    lever = salience.Index(base_idx)

    per = {arm: {"auc": {s: [] for s in slugs},
                 "auc_score_lift": {s: [] for s in slugs},
                 **{f"p@{k}": {s: [] for s in slugs} for k in TOP_K}}
           for arm in ("baseline", "lever")}
    guard = {"checked": 0, "violations": []}
    moved = {"clauses": [], "passages": []}

    for draw in draws:
        queries = SEC.load_queries(draw)
        for s in slugs:
            q = queries.get(s)
            if q is None:
                continue
            base_pairs = base_idx.rank(q)
            lever_pairs = lever.rank(q, baseline=base_pairs)

            # ⭐ R4 guard 1, mechanically, on every behaviour x draw.
            guard["checked"] += 1
            if ({c for c, _ in base_pairs} != {c for c, _ in lever_pairs}
                    or len(base_pairs) != len(lever_pairs)
                    or dict(base_pairs) != dict(lever_pairs)):
                guard["violations"].append((os.path.basename(draw), s))

            u = cs[s]["universe"]
            arms = {"baseline": base_pairs, "lever": lever_pairs}
            # DID THE LEVER DO ANYTHING? A null against a lever that never
            # moved is a statement about the lever's reach, not about speech
            # acts, so the movement is measured rather than assumed.
            sb = position_scores(base_pairs, joins[s])
            sl = position_scores(lever_pairs, joins[s])
            ob = sorted(u, key=lambda x: (-sb.get(x, 0.0), x))
            ol = sorted(u, key=lambda x: (-sl.get(x, 0.0), x))
            moved["clauses"].append(
                sum(1 for i, (c, _v) in enumerate(base_pairs)
                    if lever_pairs[i][0] != c) / len(base_pairs))
            moved["passages"].append(
                sum(1 for i, x in enumerate(ob) if ol[i] != x) / len(u))
            for arm, pairs in arms.items():
                sc = position_scores(pairs, joins[s])
                sc_score = B.passage_scores(dict(pairs), joins[s])
                for gold in cs[s]["golds"]:
                    a = B.auc(sc, gold, u)
                    if a is not None:
                        per[arm]["auc"][s].append(a)
                    a2 = B.auc(sc_score, gold, u)
                    if a2 is not None:
                        per[arm]["auc_score_lift"][s].append(a2)
                    for k in TOP_K:
                        per[arm][f"p@{k}"][s].append(
                            topk_precision(sc, gold, u, k))
    return {"cells": cs, "slugs": slugs, "per": per, "guard": guard,
            "moved": moved, "sort_order": lever.sort_order()}


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def behaviour_means(per_arm: dict, metric: str, slugs) -> dict:
    return {s: _mean(per_arm[metric][s]) for s in slugs}


def paired_ci(base: dict, lever: dict, slugs, resamples=BOOT_RESAMPLES,
              seed=BOOT_SEED) -> dict:
    """Behaviour-clustered paired bootstrap of the mean delta.

    The BEHAVIOUR is the resampling unit. Passages are never resampled; the two
    arms always see the identical resample, so the interval is paired.
    """
    d = {s: lever[s] - base[s] for s in slugs}
    point = _mean(d[s] for s in slugs)
    rng = random.Random(seed)
    out = []
    n = len(slugs)
    for _ in range(resamples):
        out.append(_mean(d[slugs[rng.randrange(n)]] for _ in range(n)))
    out.sort()
    lo = out[int(0.025 * len(out))]
    hi = out[int(0.975 * len(out)) - 1]
    return {"delta": point, "lo": lo, "hi": hi,
            "excludes_zero": bool(lo > 0 or hi < 0),
            "per_behaviour": d}


# ---------------------------------------------------------- anchor probe

def _norm(s: str) -> str:
    """Lowercase, letters and digits only. The expert's quotes were relayed as
    prose and do not match the panel byte-for-byte ('over cautious' against the
    document's 'overcautious'), so an exact-prefix matcher silently drops
    anchors. Normalising is a matching fix, never a scoring one."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _lcp(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


#: The normalised window used to LOCATE near-miss candidates when the expert's
#: relayed quote does not appear verbatim. Short, because the relayed quotes
#: diverge early ('if Claude is being over cautious' against the document's
#: 'whether Claude is being overcautious').
ANCHOR_PROBE_WINDOW = 16


def _near_misses(ps, start: str, limit: int = 3) -> list:
    """`[(passage id, normalised overlap)]` — DIAGNOSTIC ONLY.

    ⛔ Never used to select an anchor. Fuzzy matching an n=1 expert quote onto a
    passage would be a judgment call made by this script, on the only
    human-expert gold the project has; when the quote is not verbatim the
    anchor is reported UNMATCHED and the near misses are printed so a human can
    resolve it under a protocol.
    """
    ns = _norm(start)
    scored = []
    for p in ps:
        nq = _norm(p.get("quote") or "")
        i = nq.find(ns[:ANCHOR_PROBE_WINDOW])
        if i >= 0:
            scored.append((p["id"], _lcp(ns, nq[i:])))
    scored.sort(key=lambda kv: (-kv[1], kv[0]))
    return scored[:limit]


def _find_passage(beh, spec_key, anchor):
    """The panel passage the expert named — VERBATIM matches only.

    Returns `(passage, how, near_misses)`.
    """
    ps = B.passages(beh, spec_key)
    start = (anchor.get("expert_core_passage_starts") or "").strip()
    contains = (anchor.get("expert_core_passage_contains") or "").strip()
    for p in ps:
        if start and (p.get("quote") or "").strip().startswith(start):
            return p, "exact prefix", []
    for p in ps:
        if start and start in (p.get("quote") or ""):
            return p, "exact substring", []
    for p in ps:
        if contains and contains in (p.get("quote") or ""):
            return p, "contains-field substring", []
    return None, "no verbatim match", _near_misses(ps, start) if start else []


def anchor_probe(panel: dict, draws: list) -> dict:
    """⛔ R4's own falsification probe. n=3 usable anchors spanning 2
    behaviours, n=1 expert, secondhand, no protocol. QUALITATIVE, NEVER a
    decision rule (`PREREG_salience_ranking.md`, amended limits)."""
    with open(os.path.join(HERE, "expert_salience.json")) as f:
        art = json.load(f)
    rows = []
    for a in art["anchors"]:
        slug, spec_key = a["behaviour"], a["spec"]
        row = {"behaviour": slug, "spec": spec_key,
               "starts": a.get("expert_core_passage_starts")}
        if not a.get("expert_core_passage_starts"):
            row["status"] = "UNUSABLE — expert_core_passage_starts is null"
            rows.append(row)
            continue
        beh = panel.get(slug)
        if beh is None or not B.passages(beh, spec_key):
            row["status"] = "no panel coverage for this (behaviour, spec)"
            rows.append(row)
            continue
        target, how, near = _find_passage(beh, spec_key, a)
        if target is None:
            row["status"] = ("UNMATCHED — the relayed quote is not verbatim in "
                             "the panel; not resolved here (see _near_misses)")
            row["near_misses"] = near
            rows.append(row)
            continue
        row["passage_id"] = target["id"]
        row["matched_by"] = how

        clauses, _src = B.clauses_for_spec(spec_key)
        ann = B.annotations_for_spec(
            relevance.load_annotations(ANNOTATIONS), spec_key)
        row["n_annotations"] = len(ann)
        sidx = S.StructuralIndex(clauses, ann)
        base_idx = SEC.SectionQuotient(sidx)
        lever = salience.Index(base_idx)
        joins = B.clause_joins(beh, clauses, spec_key)
        u = sorted({p["id"] for p in B.passages(beh, spec_key)})

        base_pos, lever_pos, hits_n = [], [], []
        for draw in draws:
            q = SEC.load_queries(draw).get(slug)
            if q is None:
                continue
            base_pairs = base_idx.rank(q)
            lever_pairs = lever.rank(q, baseline=base_pairs)
            # HITS = the module's own predicted set, lifted to passages. If it
            # predicts nothing, the whole universe is used and that is said.
            # DEGENERACY: with no clause annotations for this spec the ranker
            # fires on nothing and every clause carries one score, so any
            # "rank" it reports is an artifact of the tie-break, not a result.
            row["distinct_base_scores"] = len({v for _c, v in base_pairs})
            pred = base_idx.predict(q)
            hits = sorted({pid for pid, cids in joins.items()
                           if set(cids) & pred}) or u
            hits_n.append(len(hits))
            for name, pairs, acc in (("b", base_pairs, base_pos),
                                     ("l", lever_pairs, lever_pos)):
                sc = position_scores(pairs, joins)
                order = sorted(hits, key=lambda x: (-sc.get(x, 0.0), x))
                acc.append(order.index(target["id"]) + 1
                           if target["id"] in order else None)
        row.update({
            "hits_per_draw": hits_n,
            "baseline_rank_of_core": base_pos,
            "lever_rank_of_core": lever_pos,
            "lever_first_in_all_draws": bool(
                lever_pos and all(p == 1 for p in lever_pos)),
            "status": "run",
        })
        rows.append(row)
    return {"usage_rules": art["usage_rules"], "rows": rows}


# ---------------------------------------------------------------- report

def report() -> str:
    panel = panel_v2.load_panel()
    clauses, src = B.clauses_for_spec(SPEC_KEY)
    ann = B.annotations_for_spec(relevance.load_annotations(ANNOTATIONS),
                                 SPEC_KEY)
    draws = B.resolve_atom_draws()
    if not draws:
        raise SystemExit("no behaviour-atom draw on disk — refusing to score")

    m = measure(panel, clauses, ann, draws)
    slugs, per = m["slugs"], m["per"]
    o = ["=" * 76,
         "PRE-REGISTERED MEASUREMENT — speech-act salience on the ranking axis",
         "=" * 76, "",
         f"panel: panel_v2 / {SPEC_KEY} — {len(slugs)} behaviours; clauses "
         f"{os.path.basename(src)} ({len(clauses)}); annotations "
         f"{os.path.basename(ANNOTATIONS)} ({len(ann)})",
         f"atom draws: {[os.path.basename(d) for d in draws]}",
         "gold: pair-gold (both held-out judges at >= "
         f"{THRESHOLD}), per benchmark.pair_targets — the SAME rule as "
         "auc_noise_floor.py",
         f"cells: AUC per (behaviour, draw, held-out judge); "
         f"{sum(len(v['auc'][s]) for s in slugs for v in [per['baseline']])} "
         "cells total",
         "resampling unit: the BEHAVIOUR (HANDOFF.md:1128-1138)", "",
         "SORT ORDER (R4 guard 2 — a result whose order is not named is not "
         "reportable):"]
    for k, v in sorted(m["sort_order"].items()):
        o.append(f"    {k}: {v}")

    o += ["", "-" * 76,
          "R4 GUARD 1 — the lever's returned SET vs the baseline's",
          "-" * 76,
          f"  (behaviour x draw) pairs checked: {m['guard']['checked']}",
          f"  set/score violations: {len(m['guard']['violations'])}"]
    if m["guard"]["violations"]:
        o += ["  ⛔ BLOCKING DEFECT — the sort changed the set. "
              "No headline number may be read.",
              f"  offenders: {m['guard']['violations'][:10]}"]
        return "\n".join(o)
    o.append("  ✅ identical set and identical scores on every behaviour x "
             "draw — ordering only.")
    o += ["", "  DID THE LEVER MOVE ANYTHING? (a null against an inert lever "
          "would be a different claim)",
          f"    clauses whose position changed:  "
          f"{_mean(m['moved']['clauses']):.1%} (mean over behaviour x draw)",
          f"    passages whose rank changed:     "
          f"{_mean(m['moved']['passages']):.1%}"]

    # ---------------------------------------------------- the headline
    base_auc = behaviour_means(per["baseline"], "auc", slugs)
    lev_auc = behaviour_means(per["lever"], "auc", slugs)
    ci = paired_ci(base_auc, lev_auc, slugs)
    clears_bar = ci["delta"] > OPERATIVE_BAR
    verdict = ("MOVES" if (clears_bar and ci["excludes_zero"]) else
               "REGRESSES" if ci["delta"] < -OPERATIVE_BAR and ci["excludes_zero"]
               else "NULL")

    o += ["", "=" * 76,
          "1. AUC, behaviour-clustered — THE PRE-REGISTERED HEADLINE",
          "=" * 76,
          f"  baseline (section.SectionQuotient.rank)  mean AUC = "
          f"{_mean(base_auc.values()):.4f}",
          f"  lever    (salience.Index @ DEFAULT)      mean AUC = "
          f"{_mean(lev_auc.values()):.4f}",
          f"  delta (lever - baseline)                 = {ci['delta']:+.4f}",
          f"  behaviour-clustered paired 95% CI        = "
          f"[{ci['lo']:+.4f}, {ci['hi']:+.4f}]  "
          f"({BOOT_RESAMPLES} resamples, seed {BOOT_SEED})",
          "",
          "  GATE ARITHMETIC (both required, either alone is a NULL):",
          f"    (a) delta {ci['delta']:+.4f} > {OPERATIVE_BAR:.4f} ?  "
          f"{'YES' if clears_bar else 'NO'}",
          f"    (b) paired CI excludes zero ?           "
          f"{'YES' if ci['excludes_zero'] else 'NO'}",
          f"  ==> VERDICT: {verdict}", "",
          "  per behaviour (baseline -> lever, delta):"]
    for s in slugs:
        o.append(f"    {s:<38}{base_auc[s]:.4f} -> {lev_auc[s]:.4f}  "
                 f"{lev_auc[s] - base_auc[s]:+.4f}")

    # ---------------------------------------------------- top-k
    o += ["", "=" * 76,
          "2. TOP-K PRECISION — the axis the endorsed use case cares about",
          "=" * 76,
          "  (reported WITH the AUC above; either alone is a protocol "
          "violation)", "",
          "     k   baseline    lever      delta      95% CI (behaviour-"
          "clustered)   gate"]
    topk = {}
    for k in TOP_K:
        b = behaviour_means(per["baseline"], f"p@{k}", slugs)
        l = behaviour_means(per["lever"], f"p@{k}", slugs)
        c = paired_ci(b, l, slugs)
        topk[k] = {"baseline": _mean(b.values()), "lever": _mean(l.values()),
                   **c}
        gate = ("MOVES" if (c["delta"] > OPERATIVE_BAR and c["excludes_zero"])
                else "NULL")
        o.append(f"     {k}   {_mean(b.values()):.4f}     "
                 f"{_mean(l.values()):.4f}   {c['delta']:+.4f}   "
                 f"[{c['lo']:+.4f}, {c['hi']:+.4f}]              {gate}")

    # ------------------------------------------- score-lift / instrument
    b_sl = behaviour_means(per["baseline"], "auc_score_lift", slugs)
    l_sl = behaviour_means(per["lever"], "auc_score_lift", slugs)
    sl_delta = _mean(l_sl.values()) - _mean(b_sl.values())
    o += ["", "=" * 76,
          "3. THE SHIPPED SCORE LIFT — an instrument fact, not a result",
          "=" * 76,
          f"  baseline mean AUC (benchmark.passage_scores) = "
          f"{_mean(b_sl.values()):.4f}",
          f"  lever    mean AUC (benchmark.passage_scores) = "
          f"{_mean(l_sl.values()):.4f}",
          f"  delta = {sl_delta:+.6f}",
          "  The shipped path takes dict(ranked) and DISCARDS the order, so an "
          "order-only",
          "  lever is invisible to it BY CONSTRUCTION — this 0 is arithmetic, "
          "not evidence.", ""]

    # ------------------------------------------- fresh vs transcribed
    o += ["=" * 76,
          "4. FRESH BASELINE vs THE TRANSCRIBED 0.7427 (prereg amendment)",
          "=" * 76,
          f"  transcribed `combined.MEASURED['ranking']['auc_mean']['section']`"
          f" = {TRANSCRIBED_SECTION_AUC:.4f}  (hand-transcribed, no generator)",
          f"  fresh baseline, score lift (the shipped path)   = "
          f"{_mean(b_sl.values()):.4f}   "
          f"(delta {_mean(b_sl.values()) - TRANSCRIBED_SECTION_AUC:+.4f})",
          f"  fresh baseline, position lift (this run's arm)  = "
          f"{_mean(base_auc.values()):.4f}   "
          f"(delta {_mean(base_auc.values()) - TRANSCRIBED_SECTION_AUC:+.4f})",
          "  The comparator for the gate is the FRESH baseline above, never "
          "the transcribed",
          "  constant (PREREG amendment 2026-08-06).", ""]

    # ------------------------------------------- anchors
    ap = anchor_probe(panel, draws)
    o += ["=" * 76,
          "5. SECONDARY — R4's own anchor falsification probe",
          "=" * 76,
          "  ⛔ n=3 usable anchors spanning 2 behaviours, n=1 expert, "
          "secondhand, no protocol.",
          "  QUALITATIVE ONLY. This is NOT a decision rule and no gate reads "
          "it.", ""]
    for r in ap["rows"]:
        o.append(f"  - {r['behaviour']} / {r['spec']}: {r['status']}")
        for pid, ov in r.get("near_misses", []):
            o.append(f"      near miss ({ov} normalised chars): {pid}")
        if r["status"] == "run":
            o.append(f"      passage {r['passage_id']}")
            o.append(f"      matched by: {r.get('matched_by')}; hits per draw "
                     f"{r['hits_per_draw']}; clause annotations for this spec: "
                     f"{r['n_annotations']}; distinct baseline scores: "
                     f"{r.get('distinct_base_scores')}")
            if r.get("distinct_base_scores", 0) < 2 or not r["n_annotations"]:
                o.append("      ⛔ DEGENERATE — the ranker has no annotations "
                         "for this spec; its order is a tie-break artifact.")
            o.append(f"      rank of the expert core passage — baseline "
                     f"{r['baseline_rank_of_core']}, lever "
                     f"{r['lever_rank_of_core']}")
            o.append(f"      lever puts it FIRST in every draw: "
                     f"{r['lever_first_in_all_draws']}")
    o.append("")

    o += ["=" * 76, f"HEADLINE: {verdict}", "=" * 76]
    return "\n".join(o)


def main(argv=None) -> int:
    sys.stdout.write(report() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
