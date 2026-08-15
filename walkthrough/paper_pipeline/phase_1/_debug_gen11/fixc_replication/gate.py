"""STEP 1 gate computation + the within-clause route/outcome confound test."""
import json, os, sys, math, random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse import wilson, fisher  # noqa: E402

TARGET = "undeclared-body-name"


def blocked_perm(rows, indicator, outcome="ok", n_iter=200000, seed=11):
    """Permute `indicator` WITHIN each clause. Tests association with
    `outcome` holding clause difficulty fixed."""
    by = defaultdict(list)
    for r in rows:
        by[r["clause"]].append(r)

    def stat(assign):
        n1 = n0 = k1 = k0 = 0
        for cl, rs in by.items():
            for r, ind in zip(rs, assign[cl]):
                v = 1 if r[outcome] else 0
                if ind:
                    n1 += 1; k1 += v
                else:
                    n0 += 1; k0 += v
        if not n1 or not n0:
            return None
        return k1 / n1 - k0 / n0

    obs = stat({cl: [indicator(r) for r in rs] for cl, rs in by.items()})
    if obs is None:
        return None, None, None
    rng = random.Random(seed)
    ge = eff = 0
    for _ in range(n_iter):
        a = {}
        for cl, rs in by.items():
            lab = [indicator(r) for r in rs]
            rng.shuffle(lab)
            a[cl] = lab
        s = stat(a)
        if s is None:
            continue
        eff += 1
        if abs(s) >= abs(obs) - 1e-12:
            ge += 1
    return obs, (ge + 1) / (eff + 1), eff


def main(expdir):
    rows = json.load(open(os.path.join(expdir, "scored.json")))
    n = len(rows)
    print("## STEP 1 INSTRUMENT CHECK  (n=%d stock draws)" % n)
    k = sum(1 for r in rows if TARGET in r["classes"])
    lo, hi = wilson(k, n)
    print("  `%s` at attempt 1: %d/%d = %.1f%%  Wilson95 [%.1f, %.1f]"
          % (TARGET, k, n, 100 * k / n, 100 * lo, 100 * hi))
    ok = sum(1 for r in rows if r["ok"])
    clo, chi = wilson(ok, n)
    print("  clean at attempt 1: %d/%d = %.1f%%  [%.1f, %.1f]"
          % (ok, n, 100 * ok / n, 100 * clo, 100 * chi))
    gate = (k / n >= 0.15) and (lo >= 0.08)
    print("  GATE (pre-registered: rate>=15%% AND Wilson-lo>=8%%): %s"
          % ("PASS" if gate else "FAIL"))

    print("\n  clauses on which the class EVER fired (of 17):")
    byc = defaultdict(list)
    for r in rows:
        byc[r["clause"]].append(r)
    ever = 0
    for cl in sorted(byc):
        rs = byc[cl]
        t = sum(1 for r in rs if TARGET in r["classes"])
        ever += t > 0
        print("    %-14s target %d/%d   clean %d/%d   body-less-ont draws %d/%d"
              % (cl, t, len(rs), sum(r["ok"] for r in rs), len(rs),
                 sum(1 for r in rs if r["n_ontology_bodyless"] > 0), len(rs)))
    print("    -> class fired on %d of %d clauses" % (ever, len(byc)))

    print("\n  Baseline route uptake (>=1 body-less ground ontology atom):")
    u = sum(1 for r in rows if r["n_ontology_bodyless"] > 0)
    ulo, uhi = wilson(u, n)
    print("    %d/%d = %.1f%%  [%.1f, %.1f]"
          % (u, n, 100 * u / n, 100 * ulo, 100 * uhi))

    print("\n  Defect classes at attempt 1 (stock):")
    cnt = defaultdict(int)
    for r in rows:
        for c in r["classes"]:
            cnt[c] += 1
    for c, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print("    %-32s %d" % (c, v))

    print("\n## THE 60-vs-38 CONFOUND: route choice vs outcome, CLAUSE HELD FIXED")
    ru = [r for r in rows if r["n_ontology_bodyless"] > 0]
    rn = [r for r in rows if r["n_ontology_bodyless"] == 0]
    print("  marginal: route-users %d/%d = %.0f%%  non-users %d/%d = %.0f%%"
          % (sum(r["ok"] for r in ru), len(ru),
             100 * sum(r["ok"] for r in ru) / max(1, len(ru)),
             sum(r["ok"] for r in rn), len(rn),
             100 * sum(r["ok"] for r in rn) / max(1, len(rn))))
    print("  Fisher (marginal, ignores clause): p = %.4f"
          % fisher(sum(r["ok"] for r in ru), len(ru) - sum(r["ok"] for r in ru),
                   sum(r["ok"] for r in rn), len(rn) - sum(r["ok"] for r in rn)))
    d, p, eff = blocked_perm(rows, lambda r: r["n_ontology_bodyless"] > 0)
    if d is None:
        print("  clause-blocked test: NOT COMPUTABLE (no clause has both)")
    else:
        print("  clause-blocked permutation: diff = %+.3f, p = %.4f "
              "(%d informative permutations)" % (d, p, eff))
        disc = [cl for cl, rs in byc.items()
                if 0 < sum(1 for r in rs if r["n_ontology_bodyless"] > 0) < len(rs)]
        print("  clauses discordant on route choice (the only ones that "
              "inform the blocked test): %d of %d" % (len(disc), len(byc)))


if __name__ == "__main__":
    main(sys.argv[1])
