import glob,json,os,hashlib,collections,math
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
def h(t): return hashlib.sha1((t or "").encode()).hexdigest()
CUR=("5ff9daf7","30ef9db2")
rows=[];runs=[]
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
  for rj in sorted(glob.glob(os.path.join(P1,pat))):
    root=os.path.dirname(rj); run=os.path.basename(root); d=json.load(open(rj))
    if (d.get("system_sha","")[:8],d.get("schema_sha","")[:8])!=CUR: continue
    ma=int(((d.get("config") or {}).get("repair") or {}).get("max_attempts",1))
    runs.append((run,d.get("spend",{}).get("usd"),d.get("spend",{}).get("calls")))
    for res in d.get("results",[]):
        tp=os.path.join(root,res["clause_id"]+".transcript.json")
        if not os.path.exists(tp): continue
        reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
        if not reps: continue
        seen={h(reps[0])};fires=[]
        for i,r in enumerate(reps[1:],2):
            if h(r) in seen: fires.append(i)
            else: seen.add(h(r))
        rows.append(dict(run=run,ma=ma,L=len(reps),F=fires[0] if fires else None,
                         nf=len(fires),status=res["status"]))
print("CURRENT GENERATION (system_sha 5ff9daf7, schema_sha 30ef9db2):")
print("  runs:",[r[0][:13] for r in runs])
multi=[r for r in rows if r["L"]>1]; fired=[r for r in multi if r["F"]]
ok=lambda r:r["status"]=="translated"
print(f"  chains {len(rows)}  multi {len(multi)}  fired {len(fired)} = {100*len(fired)/len(multi):.1f}%"
      f"   of all chains {100*len(fired)/len(rows):.1f}%   [POOLED headline: 24.5% / 14.9%]")
print(f"  predictor: fired {len([r for r in fired if ok(r)])}/{len(fired)} translated "
      f"({100*len([r for r in fired if ok(r)])/len(fired):.0f}%) | distinct "
      f"{len([r for r in multi if not r['F'] and ok(r)])}/{len(multi)-len(fired)} "
      f"({100*len([r for r in multi if not r['F'] and ok(r)])/(len(multi)-len(fired)):.0f}%)")
def wilson(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;hh=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return c-hh,c+hh
k=len([r for r in fired if ok(r)]);n=len(fired)
lo,hi=wilson(k,n); print(f"  restarts that would kill a success: {k}/{n} = {100*k/n:.1f}%  Wilson95 [{100*lo:.1f}%,{100*hi:.1f}%]")
lo,hi=wilson(len(fired),len(multi)); print(f"  blast radius CI: [{100*lo:.1f}%,{100*hi:.1f}%]")
# cost model, current gen only
a,b=0.001676,0.000101
def C(L): return sum(a+b*(k-1) for k in range(1,L+1))
old=sum(C(r["L"]) for r in rows)
for name,R in (("R=1",lambda r:1),("R=2",lambda r:2),("R=max_attempts",lambda r:r["ma"])):
    new=sum((C(r["L"]) if not r["F"] else C(r["F"])+C(R(r))) for r in rows)
    print(f"  cost multiplier ({name:14s}): {new/old:.3f}x")
new=sum((C(r["L"]) if not r["F"] else C(r["L"])+C(r["ma"])) for r in rows)
print(f"  cost multiplier (adversarial, no truncation saving): {new/old:.3f}x")
print(f"  fire_at hist {dict(collections.Counter(r['F'] for r in fired))}  L hist {dict(collections.Counter(r['L'] for r in fired))}")
