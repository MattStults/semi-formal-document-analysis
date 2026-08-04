"""Probe: how much subsumption structure is latent in the existing atom names?

DIAGNOSTIC ONLY, LABEL-FREE. Reads atom NAMES from the annotation artifacts and
nothing else — no panel, no scores, no behaviour gold. English compounds are
mostly right-headed ("targeted_political_manipulation" is a kind of
manipulation), so the last token is a candidate hypernym and shared last tokens
are candidate siblings. This measures how far that one convention would go;
it does not claim every induced edge is semantically valid — counter-examples
are exactly what the printout is for.
"""
from __future__ import annotations

import collections
import json
import pathlib

HERE = pathlib.Path(__file__).parent


def _names(path, keys=("atoms",)):
    d = json.loads((HERE / path).read_text())
    out = set()

    def walk(o):
        if isinstance(o, dict):
            n = o.get("name")
            if isinstance(n, str):
                out.add(n)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(d)
    return out


def _singular(tok):
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def head(name):
    return _singular(name.rsplit("_", 1)[-1])


def main():
    clause_names = _names("annotations_b8.json")
    query_names = _names("behavior_atoms_b8.json")
    print(f"clause vocabulary {len(clause_names)}, query vocabulary "
          f"{len(query_names)}, exact overlap "
          f"{len(clause_names & query_names)}")

    heads = collections.defaultdict(set)
    for n in clause_names | query_names:
        heads[head(n)].add(n)
    multi = {h: ns for h, ns in heads.items() if len(ns) > 1}
    print(f"distinct heads {len(heads)}; heads with >1 member {len(multi)}; "
          f"names living in a >1 family "
          f"{sum(len(v) for v in multi.values())}")

    # query atoms that currently match nothing by exact name, but would gain
    # clause-side siblings through the shared head
    unmatched_q = query_names - clause_names
    gained = {}
    for q in sorted(unmatched_q):
        sibs = (heads[head(q)] & clause_names) - {q}
        if sibs:
            gained[q] = sorted(sibs)
    print(f"\nquery atoms with NO exact clause match: {len(unmatched_q)}; "
          f"of those, gaining siblings via head: {len(gained)}")
    for q, sibs in gained.items():
        print(f"  {q}  ->  {', '.join(sibs[:6])}"
              + (" …" if len(sibs) > 6 else ""))

    print("\nlargest head families (subsumption candidates AND its risks):")
    for h, ns in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:12]:
        print(f"  {h:16s} ({len(ns):2d}) {', '.join(sorted(ns)[:7])}"
              + (" …" if len(ns) > 7 else ""))


if __name__ == "__main__":
    main()
