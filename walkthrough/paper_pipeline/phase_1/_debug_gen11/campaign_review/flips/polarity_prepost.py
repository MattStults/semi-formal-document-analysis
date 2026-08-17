"""Re-run polarity detector at PRE-WIDENING vs POST-WIDENING definitions.
ZERO spend: pure re-analysis of flips.json + census draws on disk."""
import os, sys, json, re, collections, math
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, P1); sys.path.insert(0, os.path.join(P1, "_debug_gen11/d1_recruit"))
import checks, census

# verbatim from commit 10911de (2026-08-15), the PRE-WIDENING pattern
OLD = re.compile(r"\b(dispreferred|disprefer|not preferred|discouraged|"
                 r"should be avoided|is worse|undesirable)\b", re.I)
NEW = checks._DISFAVOURED   # post-widening, cee3d0e 2026-08-16

def trips(asserts, rx):
    hits = []
    for i, a in enumerate(asserts):
        if a.get("status") != "prefer": continue
        m = rx.search(str(a.get("read_back") or ""))
        if m: hits.append((a.get("act"), m.group(0)))
    return hits

V = json.load(open(os.path.join(P1, "_debug_gen11/flip_classify/verdicts.json")))
J = json.load(open(os.path.join(P1, "_debug_gen11/flip_classify/flips.json")))
recs = {r["clause"]: r for r in J["records"]}

print("=== A. THE 33 FLIP CLAUSES: pre- vs post-widening ===")
tab = {}
for name, rx in (("PRE", OLD), ("POST", NEW)):
    t = collections.defaultdict(lambda: [0,0])
    for cid, r in recs.items():
        k = V[cid]["cls"]
        hit = any(trips(d["asserts"], rx) for d in r["draws"])
        t[k][0] += int(hit); t[k][1] += 1
    tab[name] = t
for k in ("CONTRADICTION","STRENGTH-UNDERDETERMINED","COVERAGE","UNSURE","INSTRUMENT-ARTIFACT"):
    print(f"  {k:26s} PRE {tab['PRE'][k][0]}/{tab['PRE'][k][1]}   POST {tab['POST'][k][0]}/{tab['POST'][k][1]}")

print("\n=== B. per-clause, which CONTRADICTIONS trip and on WHICH PHRASE ===")
for cid in sorted(c for c in recs if V[c]["cls"]=="CONTRADICTION"):
    ph_old = sorted({p for d in recs[cid]["draws"] for _,p in trips(d["asserts"], OLD)})
    ph_new = sorted({p for d in recs[cid]["draws"] for _,p in trips(d["asserts"], NEW)})
    print(f"  {cid:20s} PRE={ph_old or '-'}  POST={ph_new or '-'}")

print("\n=== C. CORPUS-WIDE over all 421 draws ===")
draws = [census.measure(d) for d in census.collect_runs(census.RUNS_GLOB,"graph_v2")+census.collect_ab()]
for name, rx in (("PRE",OLD),("POST",NEW)):
    n_d = sum(1 for d in draws if trips([a for a in ((d["obj"] or {}).get("asserts") or []) if isinstance(a,dict)], rx))
    cl = {d["clause"] for d in draws if trips([a for a in ((d["obj"] or {}).get("asserts") or []) if isinstance(a,dict)], rx)}
    print(f"  {name:5s} draws tripping {n_d}/{len(draws)}   distinct clauses {len(cl)}  {sorted(cl)}")
