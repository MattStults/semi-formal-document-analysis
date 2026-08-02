"""Mechanical metrics over two `conflicts.json` sets (contract §5, Agent C).

Compares the solver path against the frontier baseline on the same question:
three buckets (`tool_only`, `baseline_only`, `both`), self-agreement within
each side's repeated runs, and --- given an `extraction.json` --- coverage
against the 42 conditional provisions.

Pairs compare as sets: §3 freezes `pair` as sorted, and everything here
normalizes to a sorted tuple anyway.

Usage:
    python delta.py --tool conflicts_tool_run*.json \\
                    --baseline conflicts_baseline_run*.json \\
                    --extraction extraction.json \\
                    --out delta_metrics.json --md delta_summary.md
"""
from __future__ import annotations

import argparse
import itertools
import json
import os

CONDITIONAL_PROVISIONS = 42       # contract §2, verified count for this section


# --------------------------------------------------------------------------
# loading / normalization
# --------------------------------------------------------------------------

def load_conflicts(path):
    with open(path) as f:
        return json.load(f)


def pair_key(pair):
    return tuple(sorted(str(p) for p in pair))


def pair_set(doc):
    """Conflict-pair set of one run (a conflicts.json dict or a path)."""
    if isinstance(doc, str):
        doc = load_conflicts(doc)
    return {pair_key(c["pair"]) for c in doc.get("conflicts", [])}


def union_pairs(docs):
    out = set()
    for d in docs:
        out |= pair_set(d)
    return out


def index_by_pair(docs):
    """pair -> list of the conflict records that assert it, across runs.
    Used by adjudicate.py to render a delta item's witness."""
    idx = {}
    for d in docs:
        if isinstance(d, str):
            d = load_conflicts(d)
        run_id = d.get("run_id", "")
        for c in d.get("conflicts", []):
            rec = dict(c)
            rec["run_id"] = run_id
            rec["source"] = d.get("source", "")
            idx.setdefault(pair_key(c["pair"]), []).append(rec)
    return idx


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def jaccard(a, b):
    """|A n B| / |A u B|. Two empty sets are treated as identical (1.0):
    perfect agreement on 'no conflicts', which is what it is."""
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _sets(runs):
    return [pair_set(r) if not isinstance(r, (set, frozenset)) else set(r)
            for r in runs]


def self_agreement(runs):
    """Mean pairwise Jaccard over k runs' conflict-pair sets.

    `None` (report as `n/a`) in two undefined cases, not 1.0:
      * k < 2 --- there is no pair to compare;
      * every run's set is empty --- k runs that all found nothing are no
        evidence of stability. `jaccard({}, {})` is 1.0 by its own definition
        (agreement on "no conflicts"), but averaging that into a *self*-
        agreement figure lets k truncated or failed model calls read as a
        perfectly reproducible comparator, which is the opposite of the truth.
        Real data makes this live: gpt-oss-20b truncates, and the tool side of
        the first real run is empty.
    """
    sets = _sets(runs)
    if len(sets) < 2:
        return None
    if not any(sets):
        return None
    vals = [jaccard(x, y) for x, y in itertools.combinations(sets, 2)]
    return sum(vals) / len(vals)


def n_empty_runs(runs):
    """How many runs on a side returned an empty conflict list. Reported
    alongside self-agreement so an empty side is visible rather than inferred."""
    return sum(1 for s in _sets(runs) if not s)


def buckets(tool_pairs, baseline_pairs):
    t, b = set(tool_pairs), set(baseline_pairs)
    srt = lambda s: sorted(list(p) for p in s)               # noqa: E731
    return {"tool_only": srt(t - b),
            "baseline_only": srt(b - t),
            "both": srt(t & b)}


def _load(extraction):
    if isinstance(extraction, str):
        with open(extraction) as f:
            return json.load(f)
    return extraction


def coverage(extraction, denom=CONDITIONAL_PROVISIONS, rejected_rule_ids=None):
    """rules emitted / 42, plus a tally of `unencoded` reasons (§5).

    `rejected_rule_ids` are rules the extraction claimed but that failed
    validation and never reached the solver. They are **not encoded**: counting
    them inflates coverage, and §6's coverage stop rule keys on this number.
    `coverage` is therefore the effective figure and `coverage_claimed` the
    extraction's own, with both reported so the gap stays visible.
    """
    extraction = _load(extraction)
    rules = extraction.get("rules", [])
    ids = {r.get("id") for r in rules if isinstance(r, dict) and r.get("id")}
    n_claimed = len(ids) if ids else len(rules)
    rejected = set(rejected_rule_ids or [])
    n_rejected = len(ids & rejected) if ids else len(rejected)
    n_rules = n_claimed - n_rejected
    unenc = extraction.get("unencoded", []) or []
    tally = {}
    for u in unenc:
        reason = (u or {}).get("reason", "") if isinstance(u, dict) else str(u)
        tally[reason] = tally.get(reason, 0) + 1
    return {"rules_claimed": n_claimed,
            "rules_rejected": n_rejected,
            "rules_emitted": n_rules,
            "rejected_rule_ids": sorted(ids & rejected) if ids else sorted(rejected),
            "denominator": denom,
            "coverage": (n_rules / denom) if denom else None,
            "coverage_claimed": (n_claimed / denom) if denom else None,
            "unencoded_count": len(unenc),
            "unencoded_reasons": dict(sorted(tally.items(),
                                             key=lambda kv: (-kv[1], kv[0])))}


def conflict_channels(extraction, rejected_rule_ids=None):
    """Why the tool's conflict set is the size it is.

    The emitted program derives `conflict/5` exactly two ways (emit_asp's
    `_TAIL`): one act both obliged and forbidden, or two obligations over acts
    declared `incompat`. If neither is present, `|C_tool| == 0` is arithmetic
    about the extraction, **not** a solver finding about the section --- and
    the difference decides whether an empty tool side is a result or a
    non-result. Reported in the metrics so the zero is never left unattributed.
    """
    extraction = _load(extraction)
    rejected = set(rejected_rule_ids or [])
    obliged, forbidden = set(), set()
    for r in extraction.get("rules", []) or []:
        if not isinstance(r, dict) or r.get("id") in rejected:
            continue
        if r.get("modality") == "oblige":
            obliged.add(r.get("act"))
        elif r.get("modality") == "forbid":
            forbidden.add(r.get("act"))
    both = sorted(x for x in (obliged & forbidden) if x)
    incompat = extraction.get("incompat") or []
    # an incompat only opens a channel if both its acts are obliged somewhere
    live_incompat = [ax for ax in incompat
                     if isinstance(ax, dict)
                     and set(ax.get("acts") or []) <= obliged
                     and len(ax.get("acts") or []) == 2]
    return {"n_incompat": len(incompat),
            "n_incompat_between_obliged_acts": len(live_incompat),
            "acts_both_obliged_and_forbidden": both,
            "any_channel_open": bool(both or live_incompat)}


def compute(tool_docs, baseline_docs, extraction=None, rejected_rule_ids=None):
    """Full §5 metrics blob. `tool_docs`/`baseline_docs` are lists of
    conflicts.json dicts or paths (one entry per run)."""
    t = union_pairs(tool_docs)
    b = union_pairs(baseline_docs)
    bk = buckets(t, b)
    m = {
        "n_tool_runs": len(tool_docs),
        "n_baseline_runs": len(baseline_docs),
        "n_tool_empty_runs": n_empty_runs(tool_docs),
        "n_baseline_empty_runs": n_empty_runs(baseline_docs),
        "C_tool": len(t),
        "C_baseline": len(b),
        "tool_self_agreement": self_agreement(tool_docs),
        "baseline_self_agreement": self_agreement(baseline_docs),
        "bucket_sizes": {k: len(v) for k, v in bk.items()},
        "buckets": bk,
    }
    # A comparison in which one side is empty has no `both` bucket and no
    # disagreement to adjudicate --- every delta is one-sided by construction.
    # Say so in the blob, so `6 baseline_only` is never read as the two methods
    # disagreeing about six conflicts.
    reasons = []
    if not t:
        reasons.append("tool found no conflicts")
    if not b:
        reasons.append("baseline found no conflicts")
    m["degenerate"] = bool(reasons)
    m["degenerate_reason"] = (
        "; ".join(reasons) + " — every bucket is one-sided, `both` is "
        "vacuously empty, and no delta is a disagreement between two "
        "populated sets" if reasons else "")
    if extraction is not None:
        m["coverage"] = coverage(extraction, rejected_rule_ids=rejected_rule_ids)
        m["conflict_channels"] = conflict_channels(
            extraction, rejected_rule_ids=rejected_rule_ids)
    return m


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def _fmt(x):
    return "n/a" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def metrics_table(m):
    """The §5 numbers as a markdown table (shared with the worksheet header)."""
    L = ["| metric | value |", "|---|---|",
         f"| `|C_tool|` | {m['C_tool']} |",
         f"| `|C_baseline|` | {m['C_baseline']} |",
         f"| tool_only | {m['bucket_sizes']['tool_only']} |",
         f"| baseline_only | {m['bucket_sizes']['baseline_only']} |",
         f"| both | {m['bucket_sizes']['both']} |",
         f"| tool_self_agreement (k={m['n_tool_runs']}) | "
         f"{_fmt(m['tool_self_agreement'])}{_empty_note(m, 'tool')} |",
         f"| baseline_self_agreement (k={m['n_baseline_runs']}) | "
         f"{_fmt(m['baseline_self_agreement'])}{_empty_note(m, 'baseline')} |"]
    cov = m.get("coverage")
    if cov:
        L += [f"| coverage | {_fmt(cov['coverage'])} "
              f"({cov['rules_emitted']}/{cov['denominator']}) |"]
        if cov.get("rules_rejected"):
            L += [f"| rules emitted vs rejected | {cov['rules_emitted']} emitted, "
                  f"{cov['rules_rejected']} rejected "
                  f"(of {cov['rules_claimed']} extracted) |",
                  f"| coverage_claimed (pre-rejection) | "
                  f"{_fmt(cov['coverage_claimed'])} "
                  f"({cov['rules_claimed']}/{cov['denominator']}) |"]
        L += [f"| unencoded | {cov['unencoded_count']} |"]
    ch = m.get("conflict_channels")
    if ch:
        L += [f"| tool conflict channels open | "
              f"{'yes' if ch['any_channel_open'] else 'NO'} "
              f"({ch['n_incompat']} incompat, "
              f"{len(ch['acts_both_obliged_and_forbidden'])} acts both obliged "
              f"and forbidden) |"]
    if m.get("degenerate"):
        L += [f"| **degenerate** | yes — {m['degenerate_reason']} |"]
    return "\n".join(L)


def _empty_note(m, side):
    n = m.get(f"n_{side}_empty_runs", 0)
    k = m.get(f"n_{side}_runs", 0)
    if not n:
        return ""
    return f" ({n}/{k} runs empty)"


def to_markdown(m):
    cov = m.get("coverage")
    L = ["# Conflict delta --- mechanical metrics", "", metrics_table(m)]
    if m.get("degenerate"):
        L += ["", f"> **Degenerate comparison.** {m['degenerate_reason']}."]
    ch = m.get("conflict_channels")
    if ch and not ch["any_channel_open"]:
        L += ["", "> **The tool's empty conflict set is not a solver finding.** "
              "The emitted program can derive a conflict only from an act that "
              "is both obliged and forbidden, or from two obligations over an "
              f"`incompat` pair. This extraction has {ch['n_incompat']} "
              "`incompat` facts and no act in both modalities, so zero "
              "conflicts follows from the extraction before the solver runs. "
              "Read it as an extraction result, not as evidence about the "
              "section or the method."]
    L += ["", "## Deltas", "",
          f"**tool_only ({m['bucket_sizes']['tool_only']})** --- a real "
          "conflict the model missed, or an encoding artifact.", ""]
    L += [f"- `{p[0]}` + `{p[1]}`" for p in m["buckets"]["tool_only"]] or ["- (none)"]
    L += ["",
          f"**baseline_only ({m['bucket_sizes']['baseline_only']})** --- a "
          "tool miss (name the atom), or a confabulation.", ""]
    L += [f"- `{p[0]}` + `{p[1]}`" for p in m["buckets"]["baseline_only"]] or ["- (none)"]
    if cov and cov["unencoded_reasons"]:
        L += ["", "## Unencoded reasons", ""]
        L += [f"- {n} x {r}" for r, n in cov["unencoded_reasons"].items()]
    L += ["", "Both-found items are low information and are not listed; "
          "`adjudicate.py` skips them.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tool", nargs="*", default=[],
                    help="conflicts.json from the solver path (one per run)")
    ap.add_argument("--baseline", nargs="*", default=[],
                    help="conflicts.json from the frontier baseline (per run)")
    ap.add_argument("--extraction", default=None,
                    help="extraction.json, for coverage")
    ap.add_argument("--rejections", default=None,
                    help="filter_extraction.py's report; rejected rules are "
                         "discounted from coverage (they never reach the solver)")
    ap.add_argument("--out", default=None, help="write the metrics JSON here")
    ap.add_argument("--md", default=None, help="write the markdown summary here")
    a = ap.parse_args(argv)

    rejected = None
    if a.rejections:
        with open(a.rejections) as f:
            rejected = [r["id"] for r in json.load(f).get("rejected", [])
                        if r.get("kind") == "rule"]
    m = compute([load_conflicts(p) for p in a.tool],
                [load_conflicts(p) for p in a.baseline],
                extraction=a.extraction, rejected_rule_ids=rejected)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(m, f, indent=1)
        print(f"metrics -> {a.out}")
    md = to_markdown(m)
    if a.md:
        with open(a.md, "w") as f:
            f.write(md)
        print(f"summary -> {a.md}")
    if not a.out and not a.md:
        print(json.dumps(m, indent=1))
        print()
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
