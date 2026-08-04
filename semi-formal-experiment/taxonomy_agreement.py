"""Do two independent open-coders carve the loss corpus the same way?

DIAGNOSTIC ONLY. No score, no query, no spend.

The coders chose their own category names, so name-matching is meaningless:
A's `enumerated_list_member` and B's `illustrative_instance` may or may not be
the same cut. What is comparable is the PARTITION each induced over the same
268 records. Adjusted Rand and normalised mutual information both measure
"do these two partitions group the same records together", are invariant to
relabelling, and are corrected for the agreement two random partitions would
show by chance -- which matters here because 16-21 categories over 268 records
gives raw overlap a large free head start.

Reported alongside: the cross-tab, so a high or low score can be read rather
than trusted, and a per-A-category purity so it is visible WHICH categories
are stable and which are one coder's framing.
"""
from __future__ import annotations

import collections
import itertools
import json
import math
import pathlib

HERE = pathlib.Path(__file__).parent


def _load(name):
    t = json.loads((HERE / name).read_text())
    return {k: v.get("primary") for k, v in (t.get("assignments") or {}).items()}


def adjusted_rand(a, b, keys):
    tab = collections.Counter((a[k], b[k]) for k in keys)
    rows = collections.Counter(a[k] for k in keys)
    cols = collections.Counter(b[k] for k in keys)
    c2 = lambda n: n * (n - 1) / 2
    idx = sum(c2(v) for v in tab.values())
    er = sum(c2(v) for v in rows.values())
    ec = sum(c2(v) for v in cols.values())
    n = c2(len(keys))
    exp = er * ec / n
    mx = (er + ec) / 2
    return (idx - exp) / (mx - exp) if mx != exp else 1.0


def nmi(a, b, keys):
    n = len(keys)
    tab = collections.Counter((a[k], b[k]) for k in keys)
    rows = collections.Counter(a[k] for k in keys)
    cols = collections.Counter(b[k] for k in keys)
    mi = sum((v / n) * math.log((v / n) / ((rows[x] / n) * (cols[y] / n)))
             for (x, y), v in tab.items() if v)
    h = lambda c: -sum((v / n) * math.log(v / n) for v in c.values() if v)
    ha, hb = h(rows), h(cols)
    return mi / math.sqrt(ha * hb) if ha and hb else 0.0


def main():
    import sys
    fa, fb = (sys.argv[1:3] if len(sys.argv) >= 3 else
              ("hole_taxonomy_coder_a.json", "hole_taxonomy_coder_b.json"))
    A, B = _load(fa), _load(fb)
    keys = sorted(set(A) & set(B))
    print(f"A assigned {len(A)}, B assigned {len(B)}, both {len(keys)}")
    print(f"A categories {len(set(A.values()))}, B categories {len(set(B.values()))}")
    print(f"adjusted Rand  {adjusted_rand(A, B, keys):+.3f}")
    print(f"NMI            {nmi(A, B, keys):.3f}")
    print()
    print("per-A-category: n, largest matching B category, purity")
    byA = collections.defaultdict(list)
    for k in keys:
        byA[A[k]].append(B[k])
    for cat, bs in sorted(byA.items(), key=lambda kv: -len(kv[1])):
        top, cnt = collections.Counter(bs).most_common(1)[0]
        print(f"  {len(bs):3d}  {cat:32s} -> {top:32s} {cnt/len(bs):.0%}")


if __name__ == "__main__":
    main()
