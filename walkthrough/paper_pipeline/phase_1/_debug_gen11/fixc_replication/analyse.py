"""Pre-registered analysis for the randomised replication.

Primary endpoint: clean at attempt 1 (checks.run_checks outcome == "translated"),
arm A vs arm B, Fisher exact two-sided, over all draws.
Secondary: (a) the defect class the fix targets, (b) clause-stratified /
paired-by-clause view, (c) a permutation test that respects clause blocking,
so the estimate does not lean on independence between draws of one clause.
"""
import json, os, sys, math, random
from collections import defaultdict


def fisher(a, b, c, d):
    """two-sided Fisher exact on [[a,b],[c,d]]"""
    def logc(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    n = a + b + c + d
    r1, r2, c1 = a + b, c + d, a + c

    def p(x):
        return math.exp(logc(r1, x) + logc(r2, c1 - x) - logc(n, c1))
    obs = p(a)
    tot = 0.0
    lo, hi = max(0, c1 - r2), min(r1, c1)
    for x in range(lo, hi + 1):
        px = p(x)
        if px <= obs * (1 + 1e-9):
            tot += px
    return min(1.0, tot)


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963985
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def perm_test_blocked(rows, target="borrowed-without-gloss", n_iter=200000,
                      seed=7, key="ok"):
    """Permute the ARM LABEL within each clause block.

    This is the randomisation actually performed (arms are balanced within
    every clause), so the null distribution it generates is the correct one:
    it cannot borrow strength from between-clause differences.
    """
    by = defaultdict(list)
    for r in rows:
        by[r["clause"]].append(r)

    def stat(assign):
        na = nb = ka = kb = 0
        for cl, rs in by.items():
            for r, arm in zip(rs, assign[cl]):
                v = 1 if r[key] else 0
                if arm == "A":
                    na += 1; ka += v
                else:
                    nb += 1; kb += v
        return (kb / nb if nb else 0) - (ka / na if na else 0)

    obs_assign = {cl: [r["arm"] for r in rs] for cl, rs in by.items()}
    obs = stat(obs_assign)
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_iter):
        a = {}
        for cl, rs in by.items():
            lab = [r["arm"] for r in rs]
            rng.shuffle(lab)
            a[cl] = lab
        if abs(stat(a)) >= abs(obs) - 1e-12:
            ge += 1
    return obs, (ge + 1) / (n_iter + 1)


def report(expdir, target="borrowed-without-gloss", label="EXPERIMENT"):
    rows = json.load(open(os.path.join(expdir, "scored.json")))
    out = []
    P = out.append
    P("## %s  (n=%d observations)" % (label, len(rows)))
    for arm in ("A", "B"):
        rs = [r for r in rows if r["arm"] == arm]
        k = sum(1 for r in rs if r["ok"])
        lo, hi = wilson(k, len(rs))
        P("  arm %s: clean at attempt 1 = %d/%d = %.0f%%  [%.0f-%.0f]"
          % (arm, k, len(rs), 100 * k / len(rs), 100 * lo, 100 * hi))
    A = [r for r in rows if r["arm"] == "A"]
    B = [r for r in rows if r["arm"] == "B"]
    ka, kb = sum(r["ok"] for r in A), sum(r["ok"] for r in B)
    p = fisher(kb, len(B) - kb, ka, len(A) - ka)
    P("  Fisher exact (pooled, treats draws as independent): p = %.4f" % p)
    d, pp = perm_test_blocked(rows)
    P("  Clause-blocked permutation test: diff(B-A) = %+.3f, p = %.4f"
      % (d, pp))

    P("")
    P("  TARGETED DEFECT `%s` present at attempt 1:" % target)
    for arm in ("A", "B"):
        rs = [r for r in rows if r["arm"] == arm]
        k = sum(1 for r in rs if target in r["classes"])
        P("    arm %s: %d/%d = %.0f%%" % (arm, k, len(rs), 100 * k / len(rs)))
    ta = sum(1 for r in A if target in r["classes"])
    tb = sum(1 for r in B if target in r["classes"])
    P("    Fisher exact: p = %.4f"
      % fisher(ta, len(A) - ta, tb, len(B) - tb))

    P("")
    P("  Per clause (clean/draws):")
    P("  | clause | arm A | arm B |")
    P("  |---|---|---|")
    for cl in sorted({r["clause"] for r in rows}):
        a = [r for r in rows if r["clause"] == cl and r["arm"] == "A"]
        b = [r for r in rows if r["clause"] == cl and r["arm"] == "B"]
        P("  | %s | %d/%d | %d/%d |" % (cl, sum(r["ok"] for r in a), len(a),
                                        sum(r["ok"] for r in b), len(b)))

    P("")
    P("  Defect classes seen at attempt 1, by arm:")
    cnt = defaultdict(lambda: [0, 0])
    for r in rows:
        for c in r["classes"]:
            cnt[c][0 if r["arm"] == "A" else 1] += 1
    for c, (na, nb) in sorted(cnt.items(), key=lambda kv: -sum(kv[1])):
        P("    %-32s A=%d  B=%d" % (c, na, nb))
    return "\n".join(out)


if __name__ == "__main__":
    tgt = sys.argv[2] if len(sys.argv) > 2 else "borrowed-without-gloss"
    lab = sys.argv[3] if len(sys.argv) > 3 else "EXPERIMENT"
    print(report(sys.argv[1], tgt, lab))
