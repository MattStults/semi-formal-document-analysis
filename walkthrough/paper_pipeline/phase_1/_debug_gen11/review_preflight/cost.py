import glob, json, os, hashlib, collections, statistics as st
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
def h(t): return hashlib.sha1((t or "").encode("utf-8")).hexdigest()
rows=[]
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
    for rj in sorted(glob.glob(os.path.join(P1,pat))):
        root=os.path.dirname(rj); d=json.load(open(rj))
        ma=int(((d.get("config") or {}).get("repair") or {}).get("max_attempts",1))
        for res in d.get("results",[]):
            tp=os.path.join(root,res["clause_id"]+".transcript.json")
            if not os.path.exists(tp): continue
            reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
            if not reps: continue
            seen={h(reps[0])}; fires=[]
            for i,r in enumerate(reps[1:],2):
                if h(r) in seen: fires.append(i)
                else: seen.add(h(r))
            rows.append(dict(run=os.path.basename(root),ma=ma,clause=res["clause_id"],
                L=len(reps),F=(fires[0] if fires else None),fires=fires,
                cost=res.get("cost_usd") or 0.0,status=res.get("status"),
                tin=res.get("tokens_in") or 0,tout=res.get("tokens_out") or 0))
print("max_attempts by run:",dict(collections.Counter((r["run"][:13],r["ma"]) for r in rows)))
print()
# empirical cost of a chain of length L
byL=collections.defaultdict(list)
for r in rows: byL[r["L"]].append(r["cost"])
print("empirical cost_usd by chain length L (n, mean, median):")
C={}
for L in sorted(byL):
    C[L]=st.mean(byL[L]); print(f"  L={L}  n={len(byL[L]):4d}  mean={C[L]:.5f}  median={st.median(byL[L]):.5f}")
print("  ratio C(L)/C(1):", {L: round(C[L]/C[1],2) for L in sorted(C)})
print()
fired=[r for r in rows if r["F"]]
print(f"fired chains: {len(fired)}; fire_at hist {dict(collections.Counter(r['F'] for r in fired))}")
print(f"  stored length L hist {dict(collections.Counter(r['L'] for r in fired))}")
print(f"  run max_attempts hist {dict(collections.Counter(r['ma'] for r in fired))}")
print()
tot_old=sum(r["cost"] for r in rows)
def sim(redraw_len):
    """redraw_len: callable(r)->expected length of the redrawn chain."""
    new=0.0
    for r in rows:
        if not r["F"]: new+=r["cost"]; continue
        R=redraw_len(r)
        new += C[min(r["F"],max(C))] + C[min(max(1,R),max(C))]
    return new/tot_old
print(f"TOTAL stored cost over all {len(rows)} chains: ${tot_old:.4f}")
scen = [
 ("BEST: redraw succeeds first try (R=1)", lambda r:1),
 ("redraw behaves like the corpus (R=mean chain len 1.83)", lambda r:2),
 ("redraw runs to the run's max_attempts", lambda r:r["ma"]),
 ("WORST: redraw refreezes at 2 then abandons -> R=2 ... same as above but capped", lambda r:min(2,r["ma"])),
 ("WORST-CASE CAP: redraw = full max_attempts, fire treated as F=L (no truncation)", None),
]
for name,f in scen:
    if f is None:
        new=sum((r["cost"] if not r["F"] else C[min(r['L'],max(C))]+C[min(r['ma'],max(C))]) for r in rows)
        print(f"  {name}: {new/tot_old:.3f}x")
    else:
        print(f"  {name}: {sim(f):.3f}x")
print()
print("--- restricted to FIRED chains only (denominator = their stored cost) ---")
old_f=sum(r["cost"] for r in fired)
for name,f in scen[:4]:
    new=sum(C[min(r["F"],max(C))]+C[min(max(1,f(r)),max(C))] for r in fired)
    print(f"  {name}: {new/old_f:.3f}x")
print()
print("--- call-count multiplier (ignores token growth) ---")
oldc=sum(r["L"] for r in rows)
for name,f in scen[:4]:
    print(f"  {name}: {sum((r['L'] if not r['F'] else r['F']+max(1,f(r))) for r in rows)/oldc:.3f}x")
