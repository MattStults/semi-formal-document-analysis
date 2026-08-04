"""Independent verification of a hole-taxonomy coder's output.

DIAGNOSTIC ONLY. The coders self-report that they covered every record; this
re-derives it from the corpus so the claim is checked rather than believed.
Also re-counts every category from `assignments`, because a hand-written
`count` field and the actual assignments are two different artifacts and only
one of them is the data.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent


def check(path):
    corpus = json.loads((HERE / "hole_corpus.json").read_text())
    t = json.loads(pathlib.Path(path).read_text())
    # a coder artifact declares which corpus channel it coded; default is the
    # original missing-channel exercise so earlier artifacts keep verifying.
    channel = t.get("channel", "missing")
    ids = [r["id"] for r in corpus[channel]]

    asg = t.get("assignments") or {}
    unc = list(t.get("unclassified") or [])
    declared = {c["name"]: c.get("count") for c in t.get("categories") or []}

    seen = list(asg) + unc
    dupes = [k for k, v in collections.Counter(seen).items() if v > 1]
    missing = [i for i in ids if i not in set(seen)]
    extra = [i for i in seen if i not in set(ids)]

    actual = collections.Counter(v.get("primary") for v in asg.values())
    unknown = sorted(set(actual) - set(declared))
    mismatch = {k: (declared[k], actual.get(k, 0))
                for k in declared if declared[k] != actual.get(k, 0)}
    sec = collections.Counter(v.get("secondary") for v in asg.values()
                              if v.get("secondary"))

    print(f"--- {pathlib.Path(path).name}")
    print(f"corpus records      {len(ids)}")
    print(f"assigned            {len(asg)}")
    print(f"unclassified        {len(unc)}")
    print(f"duplicated ids      {len(dupes)} {dupes[:5]}")
    print(f"never assigned      {len(missing)} {missing[:5]}")
    print(f"not in corpus       {len(extra)} {extra[:5]}")
    print(f"categories declared {len(declared)}  used {len(actual)}")
    print(f"undeclared used     {unknown}")
    print(f"count field wrong   {mismatch or 'none'}")
    print(f"records w/ secondary{sum(sec.values())}")
    ok = not (dupes or missing or extra or unknown or mismatch)
    print(f"VERDICT             {'clean' if ok else 'DISCREPANCIES ABOVE'}")
    return ok, actual, sec


if __name__ == "__main__":
    for p in sys.argv[1:]:
        check(p)
        print()
