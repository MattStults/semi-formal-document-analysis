#!/usr/bin/env python3
"""Re-measure pilot-behavior coverage against the CURRENTLY TRANSLATED corpus.

`pilot_behaviors.json` was selected against the pinned 15-node sample
(node_corpus.json); its own honest finding was that only one behavior
concentrated >2x there. The corpus has since grown (translation_sample/runs).
This script recomputes the same span/region concentration numbers over the
nodes that are actually translated today — the newest artifact per node, as
`corpus_gate.py` gathers them — so the pilot subset is frozen against reality
rather than against the stale sample.

Same evaluation-reference caveat as select_pilot_behaviors.py: frontier labels
direct ATTENTION (which regions the pilot needs), never truth. No matching
code reads this output. Deterministic, zero spend.

Usage:  ../../../../../../semi-formal-experiment/.venv/bin/python \
            coverage_translated.py [--json coverage_translated.json]
"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import select_pilot_behaviors as spb           # noqa: E402
import corpus_gate                             # noqa: E402

NODE_CORPUS_ALL = os.path.join(os.path.dirname(HERE), "node_corpus_all.json")


def translated_geometry():
    """Geometry (narrowed spans + region) for translated, non-abstained nodes."""
    geo_all = {}
    for c in spb._load(NODE_CORPUS_ALL)["clauses"]:
        loc = c["locator"].split(">")[-1]
        spans = [(int(m.group(1)), int(m.group(2)))
                 for m in re.finditer(r"L(\d+)-(\d+)", loc)]
        m = re.match(r"l(\d+)_(\d+)_n\d+", c["id"])
        geo_all[c["id"]] = {"spans": spans,
                            "region": (int(m.group(1)), int(m.group(2)))}
    translated, abstained = {}, []
    for cid, (o, _span, _run) in corpus_gate.gather().items():
        if o.get("outcome") == "abstained":
            abstained.append(cid)
        elif cid in geo_all:
            translated[cid] = geo_all[cid]
    return translated, abstained, geo_all


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    geo, abstained, geo_all = translated_geometry()
    clauses = spb._load(spb.CLAUSES)["clauses"]
    line = {c["id"]: c["line"] for c in clauses}
    vocab = spb._load(spb.VOCAB_ANN)["vocabulary"]
    draws = [spb._load(p) for p in spb.DRAWS]
    slugs = [s for s in draws[0] if s not in ("provenance", "_warnings")]

    def span_nodes(ln, g=geo):
        return sorted(n for n, v in g.items()
                      if any(a <= ln <= b for a, b in v["spans"]))

    base_span = sum(1 for c in clauses if span_nodes(c["line"])) / len(clauses)

    print(f"translated nodes with geometry: {len(geo)} "
          f"(+{len(abstained)} abstained, excluded)")
    print(f"baseline: {base_span:.1%} of {len(clauses)} clause lines fall in "
          f"a translated node's narrowed span")
    report = {"translated_nodes": len(geo), "baseline_span_share": base_span,
              "behaviors": {}}
    for slug in slugs:
        row = {}
        for wmin in spb.WEIGHT_CUTS:
            atoms = spb.stable_atoms(draws, slug, wmin)
            cs = set()
            for n in atoms:
                v = vocab.get(n)
                if v:
                    cs.update(v["clauses"])
            in_span = {c: span_nodes(line[c]) for c in cs
                       if c in line and span_nodes(line[c])}
            share = len(in_span) / len(cs) if cs else 0.0
            uncovered = sorted(c for c in cs
                               if c in line and not span_nodes(line[c]))
            # which UNTRANSLATED regions would close the gap
            gap = collections.Counter()
            for c in uncovered:
                for n, v in geo_all.items():
                    if n in geo:
                        continue
                    if any(a <= line[c] <= b for a, b in v["spans"]):
                        gap[f"l{v['region'][0]}_{v['region'][1]}"] += 1
                        break
            row[f"weight>={wmin}"] = {
                "n_frontier_clauses": len(cs),
                "n_in_translated_spans": len(in_span),
                "span_share": round(share, 4),
                "span_lift": round(share / base_span, 3) if base_span else 0,
                "covering_nodes": sorted({n for ns in in_span.values() for n in ns}),
                "gap_regions": dict(gap.most_common(6)),
            }
        report["behaviors"][slug] = row
        c2 = row["weight>=2"]
        print(f"  {slug:38s} lift={max(v['span_lift'] for v in row.values()):>5.2f}"
              f"  covered={c2['n_in_translated_spans']:3d}/{c2['n_frontier_clauses']:3d}"
              f"  gap-> {', '.join(list(c2['gap_regions'])[:3]) or '-'}")
    if args.json:
        with open(os.path.join(HERE, args.json), "w") as f:
            json.dump(report, f, indent=1, sort_keys=True)
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
