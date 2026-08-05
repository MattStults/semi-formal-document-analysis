"""Per-locator diagnosis of every v1 -> v2_nomix mapped-set change.

For each changed locator: the v1/v2 sets, the anchor, each v1-mapped clause's
section_id, the quote, and which guard (empty-meta skip / restriction /
floor / structural refusal) accounts for the change — attributed by re-running
the join with each guard isolated.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, EXP)

import benchmark as B  # noqa: E402
import inventory as I  # noqa: E402


def main():
    rows, src = B.load_clauses()
    assert src == "modelspec_clauses.json"
    by_id = {r["id"]: r for r in rows}
    panel = B.load_true_panel()
    loc_quote, loc_scores = {}, {}
    for slug, b in panel.items():
        for p in B.passages(b):
            loc_quote[p["locator"]] = p["quote"]
            loc_scores.setdefault(p["locator"], {})[slug] = p.get("score", 0)

    report = []
    for loc in sorted(loc_quote):
        q = loc_quote[loc]
        v1 = sorted(r["id"] for r in I.match_passage(q, rows))
        res = I.match_passage_v2(q, rows, loc, mixed_variants=False)
        v2 = sorted(r["id"] for r in res["clauses"])
        if v1 == v2 and not res["refused"]:
            continue
        anchor = I.locator_anchor(loc)
        # guard attribution
        causes = []
        nq = I._norm(q)
        if len(nq) < I.DEGENERATE_QUOTE_FLOOR:
            causes.append("floor_backstop")
        v1_meta = [c for c in v1 if I.content_empty(by_id[c])]
        if v1_meta:
            causes.append(f"empty_meta_skip:{v1_meta}")
        out_of_section = [c for c in v1
                          if anchor and by_id[c].get("section_id") != anchor]
        if res["restricted"] and out_of_section:
            causes.append(f"restriction_removed:{out_of_section}")
        if res["refused"] and "floor_backstop" not in causes:
            causes.append("structural_refusal")
        report.append({
            "locator": loc, "anchor": anchor,
            "quote_norm_len": len(nq),
            "quote_head": nq[:90],
            "v1": v1,
            "v1_sections": {c: by_id[c].get("section_id") for c in v1},
            "v2": v2, "refused": res["refused"],
            "restricted": res["restricted"],
            "causes": causes,
            "scores": loc_scores[loc],
            "reference_grade": any(s >= 5 for s in loc_scores[loc].values()),
        })

    out = os.path.join(HERE, "delta_v1_v2nomix.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    print(f"{len(report)} locators change under v2_nomix\n")
    for r in report:
        print(f"- {r['locator']}")
        print(f"    anchor={r['anchor']} norm_len={r['quote_norm_len']} "
              f"refused={r['refused']} restricted={r['restricted']} "
              f"ref_grade={r['reference_grade']}")
        print(f"    v1={r['v1']} sections={r['v1_sections']}")
        print(f"    v2={r['v2']}")
        print(f"    causes={r['causes']}")
        print(f"    quote: {r['quote_head']!r}")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
