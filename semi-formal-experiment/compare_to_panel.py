"""Three-way comparison: small-model pipeline vs hand-authored pipeline vs
frontier LLM panel relevance judgments.

Question: when a cheap model does the ontology work (behavior -> derived
predicate over a fixed vocabulary), how does the resulting RELEVANCE answer
compare to (a) a careful human encoding of the same behavior and (b) simply
asking frontier models which passages are relevant?

Norms are parsed from rules.lp directly (no hand-mirrored table).

Usage:
  .venv/bin/python compare_to_panel.py results_smallmodel.json results_handauthored.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, "..", "data", "behaviours.json")
HIGH_CONSENSUS = 5

# panel section-path (first two levels) -> formalized family in rules.lp
FAMILY_MAP = {
    "Being broadly ethical > Being honest": "Being Honest",
    "Being helpful > What constitutes genuine helpfulness": "Genuine Helpfulness",
    "Being helpful > Why helpfulness is one of Claude’s most important traits": "Genuine Helpfulness",
    "Being helpful > Navigating helpfulness across principals": "Principal Hierarchy",
}


def parse_rules_lp(path):
    """Extract norms from rules.lp: id -> {act, ctx atoms, tier, family}."""
    text = open(path).read()
    sources = dict(re.findall(r'source\((\w+),\s*"([^"]+)"\)', text))
    norms = {}
    # active(id, modality, act, tier) :- body.   (body may span lines)
    for m in re.finditer(
            r"active\((\w+),\s*(\w+),\s*(\w+),\s*(\d+)\)\s*:-\s*(.*?)\.\s*$",
            text, re.M | re.S):
        nid, modality, act, tier, body = m.groups()
        ctx_atoms = set(re.findall(r"ctx\((\w+)\)", body))
        fam = sources.get(nid, "?").split(" / ")[0]
        norms[nid] = {"modality": modality, "act": act, "tier": int(tier),
                      "ctx": ctx_atoms, "family": fam,
                      "source": sources.get(nid, "?")}
    return norms


def conflict_pairs(path):
    """Norm pairs that share an incompatible-act relation or same act."""
    text = open(path).read()
    incompat = set()
    for a, b in re.findall(r"incompat\((\w+),\s*(\w+)\)", text):
        incompat.add(frozenset((a, b)))
    return incompat


def relevant_norms(atoms, norms, incompat):
    """Norms whose act or trigger atoms intersect the definition's atoms,
    plus one-step closure over incompatible acts."""
    atoms = set(atoms)
    base = {n for n, d in norms.items() if d["act"] in atoms or (d["ctx"] & atoms)}
    closure = set(base)
    for n, d in norms.items():
        for b in base:
            if frozenset((d["act"], norms[b]["act"])) in incompat:
                closure.add(n)
    return base, closure


def panel_rows(beh):
    out = []
    for p in beh["coverage"]["anthropic"]["passages"]:
        fam_key = " > ".join(p["locator"].split(" > ")[1:3])
        out.append((p, FAMILY_MAP.get(fam_key), fam_key, p["score"]))
    return out


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 1.0


def main():
    small = json.load(open(os.path.join(HERE, sys.argv[1])))
    hand = json.load(open(os.path.join(HERE, sys.argv[2])))
    panel = {b["slug"]: b for b in json.load(open(PANEL))["behaviours"]}
    norms = parse_rules_lp(os.path.join(HERE, "rules.lp"))
    incompat = conflict_pairs(os.path.join(HERE, "rules.lp"))

    smap = {r["name"]: r for r in small["results"]}
    hmap = {r["name"]: r for r in hand["results"]}

    print(f"norms parsed from rules.lp: {len(norms)}  "
          f"(families: {sorted({d['family'] for d in norms.values()})})")
    print(f"small-model source: {small['source']}   hand source: {hand['source']}")
    print("=" * 78)

    shared = [n for n in smap if n in hmap and n in panel]
    agreements = []
    for name in shared:
        s, h = smap[name], hmap[name]
        s_base, s_clo = relevant_norms(s["atoms_used"], norms, incompat)
        h_base, h_clo = relevant_norms(h["atoms_used"], norms, incompat)
        s_fams = {norms[n]["family"] for n in s_clo}
        h_fams = {norms[n]["family"] for n in h_clo}
        j = jaccard(s_clo, h_clo)
        agreements.append(j)

        rows = panel_rows(panel[name])
        hc = [r for r in rows if r[3] >= HIGH_CONSENSUS]
        hc_in = [r for r in hc if r[1]]
        hc_out = [r for r in hc if not r[1]]
        panel_fams = {r[1] for r in hc_in}

        print(f"\n### {name}")
        print(f"  verdict     small={s['status']:14s} hand={h['status']}")
        print(f"  atoms used  small={len(s['atoms_used']):2d}  hand={len(h['atoms_used']):2d}"
              f"   overlap={sorted(set(s['atoms_used']) & set(h['atoms_used']))}")
        print(f"  norms flagged  small={len(s_clo):2d}  hand={len(h_clo):2d}"
              f"   Jaccard={j:.2f}")
        print(f"    small-only: {sorted(s_clo - h_clo)}")
        print(f"    hand-only : {sorted(h_clo - s_clo)}")
        print(f"  families    small={sorted(s_fams)}")
        print(f"              hand ={sorted(h_fams)}")
        print(f"              panel={sorted(f for f in panel_fams if f)}  "
              f"(from {len(hc_in)} high-consensus in-scope passages)")
        print(f"  panel high-consensus OUT of formalized scope: {len(hc_out)}"
              f" / {len(hc)} total  ({100*len(hc_out)/max(1,len(hc)):.0f}%)")
        top_out = Counter(r[2] for r in hc_out).most_common(2)
        if top_out:
            print(f"    top out-of-scope homes: {top_out}")

    print("\n" + "=" * 78)
    if agreements:
        print(f"mean small-vs-hand norm-set Jaccard over {len(agreements)} shared "
              f"behaviors: {sum(agreements)/len(agreements):.2f}")
    # what the panel says about scope, aggregated
    tot_hc = tot_out = 0
    for name in shared:
        hc = [r for r in panel_rows(panel[name]) if r[3] >= HIGH_CONSENSUS]
        tot_hc += len(hc)
        tot_out += sum(1 for r in hc if not r[1])
    print(f"aggregate: {tot_out}/{tot_hc} high-consensus panel passages "
          f"({100*tot_out/max(1,tot_hc):.0f}%) lie outside the formalized fragment")


if __name__ == "__main__":
    main()
