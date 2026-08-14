#!/usr/bin/env python3
"""Pilot-behavior selection for the behavior-matching pilot (EXPERIMENTS.md
2026-08-13, "BEHAVIOR-PIPELINE PILOT PLAN").

Mines the semi-formal-experiment annotation corpus for behaviors whose
frontier-selected clauses CONCENTRATE in the translated 15-node sample's
document regions. Writes pilot_behaviors.json beside this script.

⛔ EVALUATION REFERENCE ONLY. The frontier annotations (gpt-5.6-luna) direct
ATTENTION — which behaviors are worth piloting where the translated sample
lives — never TRUTH. No matching decision anywhere in behavior_match.py reads
this file or the annotation corpus; disagreements at evaluation time are
adjudicated against the document, per the standing rule.

Method (pure re-analysis of artifacts already on disk; zero spend):
  * Behaviors: the 9 slugs of behavior_atoms_v2_draw{0..4}.json (gpt-5.6-luna,
    vocabulary-aligned to annotations_b8.json). An atom counts as STABLE for a
    behavior when it appears in >= 3 of the 5 independent draws — the draws
    are stochastic redraws, and stability is the free de-noiser.
  * Frontier-selected clauses for a behavior: union over its stable atoms of
    annotations_b8.json's vocabulary[name].clauses (the clauses the frontier
    annotator tagged with that atom).
  * Concentration: clause line numbers (modelspec_clauses.json, same
    source_sha256 as the graph doc) vs (a) the 15 nodes' NARROWED SPANS
    (node_corpus.json locators — what the translated modules actually encode)
    and (b) the nodes' REGION ranges (the l<a>_<b> prefix of the node id).
    Reported as share and as LIFT over the whole-document baseline share.
  * Selection: keep behaviors whose best span-level lift across the two
    weight cuts (atoms of weight >= 2 / weight >= 3) is >= 0.9 — i.e. at
    least near-baseline concentration inside the translated spans. The
    document-wide baseline is what a behavior with no regional affinity
    would score, so anything at or above it is signal at this tiny scale.

Usage:  python3 select_pilot_behaviors.py            # rewrites the JSON
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_V2 = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(GRAPH_V2, "..", "..", "..", "..", ".."))
EXP = os.path.join(REPO, "semi-formal-experiment")

NODE_CORPUS = os.path.join(GRAPH_V2, "node_corpus.json")
CLAUSES = os.path.join(EXP, "modelspec_clauses.json")
VOCAB_ANN = os.path.join(EXP, "annotations_b8.json")
DRAWS = [os.path.join(EXP, f"behavior_atoms_v2_draw{d}.json")
         for d in range(5)]
OUT = os.path.join(HERE, "pilot_behaviors.json")

STABLE_MIN_DRAWS = 3    # atom must appear in >= 3 of 5 draws
WEIGHT_CUTS = (2, 3)    # analyse atoms at weight>=2 and weight>=3
LIFT_FLOOR = 0.9        # keep behaviors with max span lift >= this
MAX_PILOT = 8


def _load(path):
    return json.load(open(path, encoding="utf-8"))


def node_geometry():
    """{node_id: {"spans": [(a,b)...], "region": (a,b)}} off node_corpus.json.
    Spans come from the locator's trailing L-list (the narrowed text the
    module encodes); the region is the graph section the node was cut from."""
    out = {}
    for c in _load(NODE_CORPUS)["clauses"]:
        loc = c["locator"].split(">")[-1]
        spans = [(int(m.group(1)), int(m.group(2)))
                 for m in re.finditer(r"L(\d+)-(\d+)", loc)]
        m = re.match(r"l(\d+)_(\d+)_n\d+", c["id"])
        out[c["id"]] = {"spans": spans,
                        "region": (int(m.group(1)), int(m.group(2)))}
    return out


def stable_atoms(draws, slug, weight_min):
    cnt = collections.Counter()
    weight = {}
    for d in draws:
        for a in d[slug]["atoms"]:
            if a.get("new"):
                continue                    # a coined atom has no clauses
            if a.get("weight", 1) < weight_min:
                continue
            cnt[a["name"]] += 1
            weight[a["name"]] = max(weight.get(a["name"], 0),
                                    a.get("weight", 1))
    return {n: weight[n] for n, k in cnt.items() if k >= STABLE_MIN_DRAWS}


def analyse():
    geo = node_geometry()
    clauses = _load(CLAUSES)["clauses"]
    line = {c["id"]: c["line"] for c in clauses}
    vocab = _load(VOCAB_ANN)["vocabulary"]
    draws = [_load(p) for p in DRAWS]
    slugs = [s for s in draws[0] if s not in ("provenance", "_warnings")]

    def span_nodes(ln):
        return sorted(n for n, g in geo.items()
                      if any(a <= ln <= b for a, b in g["spans"]))

    def region_nodes(ln):
        return sorted(n for n, g in geo.items()
                      if g["region"][0] <= ln <= g["region"][1])

    base_span = sum(1 for c in clauses if span_nodes(c["line"])) / len(clauses)
    base_region = sum(1 for c in clauses
                      if region_nodes(c["line"])) / len(clauses)

    rows = []
    for slug in slugs:
        row = {"slug": slug,
               "name": draws[0][slug].get("name", slug),
               "definition": draws[0][slug].get("definition", ""),
               "cuts": {}}
        for wmin in WEIGHT_CUTS:
            atoms = stable_atoms(draws, slug, wmin)
            cs = set()
            for n in atoms:
                v = vocab.get(n)
                if v:
                    cs.update(v["clauses"])
            in_span = {c: span_nodes(line[c]) for c in cs
                       if c in line and span_nodes(line[c])}
            in_region = {c: region_nodes(line[c]) for c in cs
                         if c in line and region_nodes(line[c])}
            span_share = len(in_span) / len(cs) if cs else 0.0
            region_share = len(in_region) / len(cs) if cs else 0.0
            hits = collections.Counter(
                n for ns in in_span.values() for n in ns)
            row["cuts"][f"weight>={wmin}"] = {
                "stable_atoms": sorted(atoms),
                "n_frontier_clauses": len(cs),
                "n_in_node_spans": len(in_span),
                "span_share": round(span_share, 4),
                "span_lift": round(span_share / base_span, 3),
                "clauses_in_node_spans": sorted(in_span),
                "span_hits_by_node": dict(hits.most_common()),
                "n_in_node_regions": len(in_region),
                "region_share": round(region_share, 4),
                "region_lift": round(region_share / base_region, 3),
            }
        row["max_span_lift"] = max(
            c["span_lift"] for c in row["cuts"].values())
        rows.append(row)

    rows.sort(key=lambda r: (-r["max_span_lift"], r["slug"]))
    selected = [r for r in rows if r["max_span_lift"] >= LIFT_FLOOR][:MAX_PILOT]
    return {
        "_purpose": "pilot behaviors for the behavior-matching pipeline "
                    "(EXPERIMENTS.md 2026-08-13 plan). EVALUATION REFERENCE "
                    "ONLY: frontier labels direct attention, never truth; no "
                    "matching code reads this file.",
        "_method": "stable (>=3/5 draws) behavior_atoms_v2 atoms -> "
                   "annotations_b8 vocabulary clauses -> clause line vs the "
                   "15 translated nodes' narrowed spans and regions; "
                   "selection = max span lift over weight cuts >= "
                   f"{LIFT_FLOOR}",
        "source_files": {
            "behavior_atoms": [os.path.basename(p) for p in DRAWS],
            "annotations": os.path.basename(VOCAB_ANN),
            "clauses": os.path.basename(CLAUSES),
            "node_corpus": os.path.basename(NODE_CORPUS)},
        "baseline": {
            "n_clauses": len(clauses),
            "share_in_node_spans": round(base_span, 4),
            "share_in_node_regions": round(base_region, 4)},
        "selected": [r["slug"] for r in selected],
        "behaviors": rows,
    }


def main():
    report = analyse()
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"baseline span share {report['baseline']['share_in_node_spans']}"
          f" over {report['baseline']['n_clauses']} clauses")
    for r in report["behaviors"]:
        mark = "*" if r["slug"] in report["selected"] else " "
        c2 = r["cuts"]["weight>=2"]
        print(f" {mark} {r['slug']:38s} max_lift={r['max_span_lift']:>5.2f} "
              f"clauses={c2['n_frontier_clauses']:3d} "
              f"in_span={c2['n_in_node_spans']:2d}")
    print(f"selected {len(report['selected'])}: "
          + ", ".join(report["selected"]))
    print(f"-> {os.path.relpath(OUT, os.getcwd())}")


if __name__ == "__main__":
    main()
