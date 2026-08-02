"""Which clause KINDS carry the panel's relevance signal?

The extraction pipeline encodes only `conditional` clauses. If the passages the
panel rates relevant live mostly in other kinds, a conditional-only tool has a
hard recall cap that no amount of model quality can lift — so this has to be
measured before spending on extraction, not after.

    python3 measure_kinds.py
"""
from __future__ import annotations

import collections

import inventory
import measure_join


def report():
    rows = measure_join.clause_rows()
    passages = measure_join.panel_passages()

    # kind mix of the corpus, as the baseline to compare against
    corpus = collections.Counter(r["kind"] for r in rows)

    # kind mix of clauses the panel actually points at, by consensus stratum
    strata = {"all": lambda p: True,
              "score >= 5": lambda p: (p["score"] or 0) >= 5,
              "score == 6": lambda p: p["score"] == 6}
    hits = {k: collections.Counter() for k in strata}
    seen = {k: set() for k in strata}

    for p in passages:
        matched = inventory.match_passage(p["quote"], rows)
        for label, pred in strata.items():
            if pred(p):
                for r in matched:
                    hits[label][r["kind"]] += 1
                    seen[label].add(r["id"])

    kinds = sorted(corpus, key=lambda k: -corpus[k])
    cols = ["corpus"] + list(strata)
    print(f"{'kind':14s}" + "".join(f"{c:>18s}" for c in cols))
    for k in kinds:
        cells = [f"{corpus[k]:6d} {100*corpus[k]/sum(corpus.values()):5.1f}%"]
        for label in strata:
            tot = sum(hits[label].values()) or 1
            cells.append(f"{hits[label][k]:6d} {100*hits[label][k]/tot:5.1f}%")
        print(f"{k:14s}" + "".join(f"{c:>18s}" for c in cells))

    print()
    for label in strata:
        tot = sum(hits[label].values()) or 1
        enc = hits[label]["conditional"]
        print(f"{label:12s} conditional-only ceiling: "
              f"{enc}/{tot} = {100*enc/tot:.1f}% of relevance-weighted hits; "
              f"{len(seen[label])} distinct clauses cited")
    return hits


if __name__ == "__main__":
    report()
