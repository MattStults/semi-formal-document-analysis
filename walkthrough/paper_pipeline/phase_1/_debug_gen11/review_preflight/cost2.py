import glob, json, os, hashlib, collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
def h(t): return hashlib.sha1((t or "").encode("utf-8")).hexdigest()
runs=[]
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
    for rj in sorted(glob.glob(os.path.join(P1,pat))):
        root=os.path.dirname(rj); d=json.load(open(rj))
        sp=(d.get("spend") or {})
        ma=int(((d.get("config") or {}).get("repair") or {}).get("max_attempts",1))
        ch=[]
        for res in d.get("results",[]):
            tp=os.path.join(root,res["clause_id"]+".transcript.json")
            if not os.path.exists(tp): continue
            reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
            if not reps: continue
            seen={h(reps[0])}; fires=[]
            for i,r in enumerate(reps[1:],2):
                if h(r) in seen: fires.append(i)
                else: seen.add(h(r))
            ch.append(dict(L=len(reps),F=(fires[0] if fires else None),ma=ma,
                           first=res.get("cost_usd") or 0.0,status=res.get("status")))
        if ch and sp.get("usd"): runs.append(dict(run=os.path.basename(root),ma=ma,ch=ch,
                                                 usd=sp["usd"],calls=sp.get("calls")))
# least squares for c_k = a + b*(k-1) over runs:  usd ~= a*N + b*S
N=[sum(c["L"] for c in r["ch"]) for r in runs]
S=[sum((c["L"]*(c["L"]-1))//2 for c in r["ch"]) for r in runs]
Y=[r["usd"] for r in runs]
import itertools
sNN=sum(n*n for n in N); sNS=sum(n*s for n,s in zip(N,S)); sSS=sum(s*s for s in S)
sNY=sum(n*y for n,y in zip(N,Y)); sSY=sum(s*y for s,y in zip(S,Y))
det=sNN*sSS-sNS*sNS
a=(sNY*sSS-sSY*sNS)/det; b=(sNN*sSY-sNS*sNY)/det
print(f"fitted per-call cost c_k = {a:.6f} + {b:.6f}*(k-1)   [k = 1-based attempt position]")
print(f"  c1={a:.6f} c2={a+b:.6f} c3={a+2*b:.6f} c4={a+3*b:.6f} c5={a+4*b:.6f}  (c5/c1={(a+4*b)/a:.2f})")
pred=[a*n+b*s for n,s in zip(N,S)]
print("  fit residuals (pred/actual):", [round(p/y,3) for p,y in zip(pred,Y)])
print()
def C(L): return sum(a+b*(k-1) for k in range(1,L+1))
allch=[c for r in runs for c in r["ch"]]
fired=[c for c in allch if c["F"]]
old=sum(C(c["L"]) for c in allch)
print(f"chains {len(allch)}  fired {len(fired)}  modelled baseline ${old:.4f} (actual total ${sum(r['usd'] for r in runs):.4f})")
print()
print("TOKEN-WEIGHTED multiplier over the WHOLE population:")
for name,R in (("redraw lands first try (R=1)",lambda c:1),
               ("redraw = corpus-typical 2 attempts",lambda c:2),
               ("redraw refreezes at 2 -> abandon (R=2)",lambda c:2),
               ("redraw runs full max_attempts",lambda c:c["ma"]),
               ("PESSIMAL: every redraw runs full max_attempts AND every chain refires",lambda c:c["ma"])):
    new=sum((C(c["L"]) if not c["F"] else C(c["F"])+C(R(c))) for c in allch)
    print(f"  {name:52s} {new/old:.3f}x")
# absolute pessimal: assume fire is only detected at the LAST stored attempt (no truncation benefit)
new=sum((C(c["L"]) if not c["F"] else C(c["L"])+C(c["ma"])) for c in allch)
print(f"  {'ADVERSARIAL: no truncation saving at all (F:=L)':52s} {new/old:.3f}x")
print()
print("same, restricted to fired chains:")
oldf=sum(C(c['L']) for c in fired)
for name,R in (("R=1",lambda c:1),("R=2",lambda c:2),("R=max_attempts",lambda c:c["ma"])):
    print(f"  {name:52s} {sum(C(c['F'])+C(R(c)) for c in fired)/oldf:.3f}x")
