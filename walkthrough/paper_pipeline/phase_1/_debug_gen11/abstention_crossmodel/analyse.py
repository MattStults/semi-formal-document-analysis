#!/usr/bin/env python3
"""Cross-model replication analysis. Written BEFORE the first Sonnet draw.

Reads:  _debug_gen11/abstention_crossmodel/judgements/X###_d#.txt   (new, Sonnet)
        _debug_gen11/abstention_boundary/judgements/X###_d#.txt     (prior, Haiku)
        _debug_gen11/abstention_boundary/KEY_do_not_open_until_judged.json
Writes: _debug_gen11/abstention_crossmodel/{tally.json,joined.json,RESULTS.json}
Never writes anything under abstention_boundary/.
"""
import json, math, os, random, re, sys
from collections import Counter
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
PRIOR = os.path.join(os.path.dirname(HERE), "abstention_boundary")
OIDS = ["X%03d" % i for i in range(53)]


def read_draws(jdir, oid):
    out = []
    for d in range(1, 8):
        p = os.path.join(jdir, "%s_d%d.txt" % (oid, d))
        if not os.path.exists(p):
            continue
        txt = open(p).read()
        m = re.search(r"VERDICT:\s*(NON-NORMATIVE|NORMATIVE)", txt)
        if not m:
            raise SystemExit("unparseable verdict in %s" % p)
        out.append(m.group(1))
    return out


def verdict(draws):
    """Pre-registered rule: 3/3 -> that; 2-1 -> escalate to 5; 5-0/4-1 -> majority; 3-2 -> AMBIGUOUS."""
    c = Counter(draws)
    n = len(draws)
    if n == 3:
        if c["NORMATIVE"] == 3:
            return "NORMATIVE"
        if c["NON-NORMATIVE"] == 3:
            return "NON-NORMATIVE"
        return "ESCALATE"
    if n == 5:
        if c["NORMATIVE"] >= 4:
            return "NORMATIVE"
        if c["NON-NORMATIVE"] >= 4:
            return "NON-NORMATIVE"
        return "AMBIGUOUS"
    raise SystemExit("bad draw count %d" % n)


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def kappa(a, b, cats):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def boot_kappa(a, b, cats, seed=20260815, reps=10000):
    rng = random.Random(seed)
    n = len(a)
    vals = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        aa = [a[i] for i in idx]
        bb = [b[i] for i in idx]
        try:
            vals.append(kappa(aa, bb, cats))
        except ZeroDivisionError:
            pass
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))])


def logC(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact_2x2(a, b, c, d):
    """two-sided Fisher exact p."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)

    def logp(x):
        return logC(r1, x) + logC(n - r1, c1 - x) - logC(n, c1)

    p0 = logp(a)
    tot = 0.0
    for x in range(lo, hi + 1):
        lp = logp(x)
        if lp <= p0 + 1e-9:
            tot += math.exp(lp)
    return min(1.0, tot)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.exp(logC(n, i) - n * math.log(2)) for i in range(k + 1))
    return min(1.0, 2 * p)


def main():
    key = json.load(open(os.path.join(PRIOR, "KEY_do_not_open_until_judged.json")))
    newdir = os.path.join(HERE, "judgements")

    new_draws, old_draws, new_v, old_v = {}, {}, {}, {}
    for oid in OIDS:
        nd = read_draws(newdir, oid)
        od = read_draws(os.path.join(PRIOR, "judgements"), oid)
        if not nd:
            print("MISSING new draws for", oid)
            sys.exit(1)
        new_draws[oid], old_draws[oid] = nd, od
        new_v[oid], old_v[oid] = verdict(nd), verdict(od)

    esc = [o for o in OIDS if new_v[o] == "ESCALATE"]
    if esc:
        print("ESCALATION NEEDED (2-1 splits), dispatch d4,d5 for:")
        print(" ".join(esc))
        json.dump({o: dict(Counter(new_draws[o])) for o in OIDS},
                  open(os.path.join(HERE, "tally.json"), "w"), indent=1)
        sys.exit(0)

    R = {}
    # ---- C1 agreement / kappa ----
    A = [old_v[o] for o in OIDS]
    B = [new_v[o] for o in OIDS]
    cats3 = ["NORMATIVE", "NON-NORMATIVE", "AMBIGUOUS"]
    R["C1a_kappa3_all53"] = kappa(A, B, cats3)
    R["C1a_kappa3_ci"] = boot_kappa(A, B, cats3)
    sub = [o for o in OIDS if old_v[o] != "AMBIGUOUS" and new_v[o] != "AMBIGUOUS"]
    R["C1b_kappa2_n"] = len(sub)
    R["C1b_kappa2"] = kappa([old_v[o] for o in sub], [new_v[o] for o in sub],
                            ["NORMATIVE", "NON-NORMATIVE"])
    R["C1b_kappa2_ci"] = boot_kappa([old_v[o] for o in sub], [new_v[o] for o in sub],
                                    ["NORMATIVE", "NON-NORMATIVE"])
    R["C1c_agree_53"] = sum(1 for o in OIDS if old_v[o] == new_v[o]) / 53
    disp = [o for o in OIDS if key[o]["stratum"] != "ds_success"]
    R["dispute_n"] = len(disp)
    R["C1c_agree_dispute"] = sum(1 for o in disp if old_v[o] == new_v[o]) / len(disp)

    # ---- C2 three-way split on the dispute set ----
    def split(vmap):
        b = Counter()
        detail = {}
        for o in disp:
            v = vmap[o]
            k = key[o]
            hk = k.get("haiku") or {}
            some_model_abstained = hk.get("abstained", 0) > 0 or k.get("ds_outcome") == "abstained"
            # Bucket definitions reproduced from ABSTENTION_BOUNDARY.md §3, whose
            # published counts (19/2/2/6) are recovered exactly by these rules.
            if v == "AMBIGUOUS":
                lab = "GENUINELY AMBIGUOUS"
            elif v == "NON-NORMATIVE":
                lab = "ABSTAINER RIGHT"
            elif some_model_abstained:
                lab = "TRANSLATOR RIGHT"
            else:
                lab = "control: normative, no abstainer"
            b[lab] += 1
            detail[o] = lab
        return b, detail

    ob, odet = split(old_v)
    nb, ndet = split(new_v)
    R["C2_split_haiku"] = {k: [v, wilson(v, len(disp))] for k, v in ob.items()}
    R["C2_split_sonnet"] = {k: [v, wilson(v, len(disp))] for k, v in nb.items()}
    R["C2_bucket_detail"] = {o: [odet[o], ndet[o]] for o in disp}

    # ---- strata rates ----
    for lbl, vmap in (("haiku", old_v), ("sonnet", new_v)):
        for st in ("cohort17", "ds_abstain", "ds_success"):
            ids = [o for o in OIDS if key[o]["stratum"] == st]
            k_ = sum(1 for o in ids if vmap[o] == "NON-NORMATIVE")
            R["strat_%s_%s" % (lbl, st)] = [k_, len(ids), wilson(k_, len(ids))]

    # ---- C3 over-translation ----
    A_ids = [o for o in OIDS if key[o]["stratum"] == "cohort17" and key[o]["ds_outcome"] == "translated"]
    B_ids = [o for o in OIDS if key[o]["stratum"] == "ds_success"]
    for lbl, vmap in (("haiku", old_v), ("sonnet", new_v)):
        a_nn = sum(1 for o in A_ids if vmap[o] == "NON-NORMATIVE")
        a_amb = sum(1 for o in A_ids if vmap[o] == "AMBIGUOUS")
        b_nn = sum(1 for o in B_ids if vmap[o] == "NON-NORMATIVE")
        b_amb = sum(1 for o in B_ids if vmap[o] == "AMBIGUOUS")
        rest = 69 - len(A_ids)
        pB = b_nn / len(B_ids)
        lo, hi = wilson(b_nn, len(B_ids))
        pt = a_nn + rest * pB
        R["C3_%s" % lbl] = {
            "A_n": len(A_ids), "A_nonnorm": a_nn, "A_amb": a_amb,
            "B_n": len(B_ids), "B_nonnorm": b_nn, "B_amb": b_amb, "B_rate": pB,
            "point_modules": pt, "point_pct": pt / 69,
            "ci_modules": [a_nn + rest * lo, a_nn + rest * hi],
            "ci_pct": [(a_nn + rest * lo) / 69, (a_nn + rest * hi) / 69],
            "incl_amb_pct": (a_nn + a_amb + rest * ((b_nn + b_amb) / len(B_ids))) / 69,
        }

    # ---- C4 disagreement ----
    tab = Counter((old_v[o], new_v[o]) for o in OIDS)
    R["C4_crosstab"] = {"%s|%s" % k: v for k, v in tab.items()}
    b = tab[("NORMATIVE", "NON-NORMATIVE")]   # haiku N, sonnet NN => sonnet stricter
    c = tab[("NON-NORMATIVE", "NORMATIVE")]   # haiku NN, sonnet N => sonnet more permissive
    R["C4a_mcnemar_p"] = mcnemar_exact(b, c)
    R["C4a_haiku_N_sonnet_NN"] = b
    R["C4a_haiku_NN_sonnet_N"] = c
    for lbl, dmap, vmap in (("haiku", old_draws, old_v), ("sonnet", new_draws, new_v)):
        allc = Counter(x for o in OIDS for x in dmap[o])
        R["rate_%s_draws" % lbl] = dict(allc)
        R["rate_%s_draws_NN" % lbl] = allc["NON-NORMATIVE"] / sum(allc.values())
        R["rate_%s_items_NN" % lbl] = sum(1 for o in OIDS if vmap[o] == "NON-NORMATIVE") / 53
    dis = [o for o in OIDS if old_v[o] != new_v[o]]
    R["C4_disagree_ids"] = dis
    boundary = [o for o in dis
                if "AMBIGUOUS" in (old_v[o], new_v[o])
                or len(set(old_draws[o][:3])) > 1 or len(set(new_draws[o][:3])) > 1]
    R["C4c_boundary_disagreements"] = [len(boundary), len(dis), boundary]

    # ---- C5 falsifiers ----
    for lbl, vmap in (("haiku", old_v), ("sonnet", new_v)):
        ab = [o for o in OIDS if key[o]["stratum"] == "ds_abstain"]
        su = [o for o in OIDS if key[o]["stratum"] == "ds_success"]
        a1 = sum(1 for o in ab if vmap[o] == "NON-NORMATIVE"); a0 = len(ab) - a1
        s1 = sum(1 for o in su if vmap[o] == "NON-NORMATIVE"); s0 = len(su) - s1
        R["F1_%s" % lbl] = {"ds_abstain_NN": [a1, len(ab)], "ds_success_NN": [s1, len(su)],
                            "fisher_p": fisher_exact_2x2(a1, a0, s1, s0)}
    nd_all = Counter(x for o in OIDS for x in new_draws[o])
    R["F2_sonnet_max_share"] = max(nd_all.values()) / sum(nd_all.values())
    R["F3_sonnet_normative_rate"] = nd_all["NORMATIVE"] / sum(nd_all.values())

    R["verdicts"] = {o: {"haiku": old_v[o], "sonnet": new_v[o],
                         "clause": key[o]["clause"], "stratum": key[o]["stratum"],
                         "haiku_draws": new_draws[o] and old_draws[o],
                         "sonnet_draws": new_draws[o]} for o in OIDS}

    json.dump({o: dict(Counter(new_draws[o])) for o in OIDS},
              open(os.path.join(HERE, "tally.json"), "w"), indent=1)
    json.dump(R, open(os.path.join(HERE, "RESULTS.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != "verdicts"}, indent=1))


if __name__ == "__main__":
    main()
