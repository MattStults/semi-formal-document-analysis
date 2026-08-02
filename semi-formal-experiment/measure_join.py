"""How many panel passages join to a clause? The ceiling on every benchmark number.

A passage that matches no clause is neither a hit nor a miss — it is invisible
to the tool, so it caps recall regardless of how good the tool gets. This
reports that ceiling directly, overall and on the high-consensus subset that
the headline F1 is computed over.

    python3 measure_join.py
"""
from __future__ import annotations

import json
import os

import inventory

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
PANEL = os.path.join(
    HERE, "..", "data", "behaviours.json")


def clause_rows(path=CLAUSES):
    """Clause records in the shape match_passage expects. Clauses carry no
    marked_span (that is a focus-area artifact), so it is explicitly None
    rather than absent."""
    data = json.load(open(path))
    rows = data["clauses"] if isinstance(data, dict) else data
    return [dict(r, marked_span=None) for r in rows]


def panel_passages(path=PANEL, spec="openai"):
    """(behaviour, passage, score) triples from the panel's spec coverage.

    Walks the structure defensively: the panel file is an external artifact we
    do not control, and a silent shape change here would masquerade as a
    coverage regression rather than a parse failure.
    """
    data = json.load(open(path))
    out = []
    for b in data["behaviours"]:
        name = b.get("slug") or b.get("id")
        for p in ((b.get("coverage") or {}).get(spec) or {}).get("passages") or []:
            out.append({"behaviour": name,
                        "quote": p.get("quote") or "",
                        "score": p.get("score"),
                        "example_block": bool(p.get("exampleBlock"))})
    return out


def report():
    rows = clause_rows()
    passages = panel_passages()
    if not passages:
        raise SystemExit(
            "no passages parsed from the panel file — its shape changed; "
            "fix panel_passages() rather than trusting a 0% coverage number")

    strata = {}   # label -> [matched, total]

    def note(label, hit):
        s = strata.setdefault(label, [0, 0])
        s[0] += hit
        s[1] += 1

    unmatched = []
    for p in passages:
        hit = bool(inventory.match_passage(p["quote"], rows))
        note("all", hit)
        note(f"  {p['behaviour']}", hit)
        if (p["score"] or 0) >= 5:
            note("score >= 5", hit)
        if p["score"] == 6:
            note("score == 6", hit)
        if p["example_block"]:
            note("example blocks", hit)
        if not hit:
            unmatched.append(p)

    print(f"clauses: {len(rows)}   panel passages: {len(passages)}\n")
    print(f"{'stratum':34s} {'matched':>9s} {'total':>7s} {'pct':>7s}")
    for label, (m, t) in strata.items():
        print(f"{label:34s} {m:9d} {t:7d} {100*m/t:6.1f}%")

    print(f"\nunmatched ({len(unmatched)}):")
    for p in unmatched[:10]:
        print(f"  [{p['behaviour']} s={p['score']}] {p['quote'][:100]!r}")
    return {"strata": strata, "unmatched": len(unmatched)}


if __name__ == "__main__":
    report()
