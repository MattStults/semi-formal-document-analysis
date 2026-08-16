"""Score the draws against the PREREG endpoints. Deterministic, no model calls."""
import os, sys, json, glob, re, math, collections
P1 = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P1)
import checks

HARD = {"forbid", "permit", "oblige"}


def parse(text):
    if not text:
        return None
    c = text.strip()
    c = re.sub(r"^```(?:json)?", "", c).strip()
    c = re.sub(r"```$", "", c).strip()
    s, e = c.find("{"), c.rfind("}")
    if s < 0 or e < s:
        return None
    try:
        return json.loads(c[s:e + 1])
    except Exception:
        return None


def score_one(rec):
    d = parse(rec.get("text")) if rec.get("ok") else None
    o = {"task_id": rec["task_id"], "exp": rec["exp"], "cohort": rec["cohort"],
         "clause": rec["clause"], "arm": rec["arm"], "draw": rec["draw"],
         "unparsed": d is None, "abstained": False,
         "polarity_mismatch": False, "n_prefer": 0, "prefer_acts": [],
         "hard_statuses": [], "deontic_hard": False, "n_ontology": 0,
         "routed_ontology": False}
    if d is None:
        return o
    o["abstained"] = (d.get("outcome") == "abstained")
    asr = [a for a in (d.get("asserts") or []) if isinstance(a, dict)]
    sts = [a.get("status") for a in asr]
    o["n_prefer"] = sum(1 for s in sts if s == "prefer")
    o["prefer_acts"] = [a.get("act") for a in asr if a.get("status") == "prefer"]
    o["hard_statuses"] = sorted({s for s in sts if s in HARD})
    o["deontic_hard"] = bool(o["hard_statuses"])
    o["n_ontology"] = len(d.get("ontology") or [])
    o["routed_ontology"] = (not o["deontic_hard"]) and o["n_ontology"] > 0
    hits = []
    for i, a in enumerate(asr):
        if a.get("status") != "prefer":
            continue
        m = checks._DISFAVOURED.search(str(a.get("read_back") or ""))
        if m:
            hits.append({"i": i, "act": a.get("act"), "phrase": m.group(0),
                         "read_back": a.get("read_back")})
    o["polarity_mismatch"] = bool(hits)
    o["polarity_hits"] = hits
    o["nonprefer_acts"] = [(a.get("status"), a.get("act")) for a in asr
                           if a.get("status") in HARD]
    return o


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def _lc(n):
    r = 0.0
    for i in range(2, n + 1):
        r += math.log(i)
    return r


def fisher(a, b, c, d):
    """two-sided Fisher exact on [[a,b],[c,d]]"""
    n = a + b + c + d
    def p(x):
        y = a + b - x
        u = a + c - x
        v = d - (a - x)
        if min(x, y, u, v) < 0:
            return 0.0
        return math.exp(_lc(a + b) + _lc(c + d) + _lc(a + c) + _lc(b + d)
                        - _lc(n) - _lc(x) - _lc(y) - _lc(u) - _lc(v))
    p0 = p(a)
    tot = 0.0
    for x in range(0, min(a + b, a + c) + 1):
        px = p(x)
        if px <= p0 * (1 + 1e-9):
            tot += px
    return min(1.0, tot)


def load():
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, "draws", "*.json"))):
        rows.append(score_one(json.load(open(f))))
    return rows


def rate(rows, key):
    k = sum(1 for r in rows if r[key])
    return k, len(rows), wilson(k, len(rows))


def report(rows, sel, key, label, invert=False):
    A = [r for r in rows if sel(r) and r["arm"] == "A"]
    B = [r for r in rows if sel(r) and r["arm"] == "B"]
    ka, na, wa = rate(A, key)
    kb, nb, wb = rate(B, key)
    line = f"  {label:28s} A {ka:3d}/{na:<3d} = {wa[0]*100:5.1f}% [{wa[1]*100:4.1f},{wa[2]*100:5.1f}]"
    if nb:
        pv = fisher(ka, na - ka, kb, nb - kb)
        line += f"   B {kb:3d}/{nb:<3d} = {wb[0]*100:5.1f}% [{wb[1]*100:4.1f},{wb[2]*100:5.1f}]   Fisher p={pv:.4f}"
    print(line)
    return (ka, na, kb, nb)


if __name__ == "__main__":
    rows = load()
    json.dump(rows, open(os.path.join(HERE, "scored.json"), "w"), indent=1)
    print(f"draws scored: {len(rows)}  "
          f"(A={sum(1 for r in rows if r['arm']=='A')}, B={sum(1 for r in rows if r['arm']=='B')})")

    print("\n=== EXPERIMENT 1 — prefer polarity (D1 cohort, 7 clauses) ===")
    d1 = lambda r: r["exp"] == "D1"
    report(rows, d1, "polarity_mismatch", "PRIMARY polarity_mismatch")
    report(rows, d1, "abstained", "trade1 abstained")
    report(rows, d1, "unparsed", "trade2 unparsed")
    report(rows, lambda r: d1(r) and not r["unparsed"], "no_prefer", "trade3 prefer-erasure") \
        if any("no_prefer" in r for r in rows) else None
    # trade3/4 computed inline below
    for arm in ("A", "B"):
        s = [r for r in rows if d1(r) and r["arm"] == arm and not r["unparsed"]]
        if not s:
            continue
        er = sum(1 for r in s if r["n_prefer"] == 0)
        cc = sum(1 for r in s if r["n_prefer"] == 0 and r["deontic_hard"])
        print(f"  trade3 prefer-erasure  arm {arm}: {er}/{len(s)} = {er/len(s)*100:5.1f}%"
              f"   trade4 comparative-collapse: {cc}/{len(s)} = {cc/len(s)*100:5.1f}%")
    print("\n  per-clause polarity_mismatch (hits/draws):")
    for cid in sorted({r["clause"] for r in rows if d1(r)}):
        cells = []
        for arm in ("A", "B"):
            s = [r for r in rows if d1(r) and r["clause"] == cid and r["arm"] == arm]
            if s:
                cells.append(f"{arm}={sum(1 for r in s if r['polarity_mismatch'])}/{len(s)}")
        print(f"    {cid:20s} " + "  ".join(cells))

    print("\n=== EXPERIMENT 2 — fact routed to a deontic status ===")
    tgt = lambda r: r["exp"] == "D2" and r["cohort"] == "target"
    ctl = lambda r: r["exp"] == "D2" and r["cohort"] == "control"
    print(" TARGET cohort (8 DESCRIPTION-judged clauses):")
    report(rows, tgt, "deontic_hard", "PRIMARY deontic_hard")
    report(rows, tgt, "routed_ontology", "routed_ontology")
    report(rows, tgt, "abstained", "trade1 abstained")
    report(rows, tgt, "unparsed", "trade3 unparsed")
    print(" CONTROL cohort (3 NORM-judged clauses, SHOULD stay deontic):")
    report(rows, ctl, "deontic_hard", "control deontic_hard")
    report(rows, ctl, "abstained", "control abstained")
    print("\n  per-clause deontic_hard (hits/draws):")
    for coh, sel in (("target", tgt), ("control", ctl)):
        for cid in sorted({r["clause"] for r in rows if sel(r)}):
            cells = []
            for arm in ("A", "B"):
                s = [r for r in rows if sel(r) and r["clause"] == cid and r["arm"] == arm]
                if s:
                    cells.append(f"{arm}={sum(1 for r in s if r['deontic_hard'])}/{len(s)}")
            print(f"    [{coh:7s}] {cid:20s} " + "  ".join(cells))
