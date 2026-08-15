import glob,json,os,hashlib,collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
def h(t): return hashlib.sha1((t or "").encode()).hexdigest()
by=collections.defaultdict(lambda: dict(multi=0,fire=0,succ_fire=0,n=0))
missing=[]
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
  for rj in sorted(glob.glob(os.path.join(P1,pat))):
    root=os.path.dirname(rj); run=os.path.basename(root); d=json.load(open(rj))
    key=(d.get("system_sha","?")[:8], d.get("schema_sha","?")[:8])
    for res in d.get("results",[]):
        cid=res["clause_id"]; tp=os.path.join(root,cid+".transcript.json")
        if not os.path.exists(tp):
            missing.append((run[:13],cid,res.get("status"),res.get("attempts"))); continue
        reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
        if not reps: continue
        seen={h(reps[0])}; f=None
        for i,r in enumerate(reps[1:],2):
            if h(r) in seen:
                f=f or i
            else: seen.add(h(r))
        b=by[key]; b["n"]+=1
        if len(reps)>1:
            b["multi"]+=1
            if f: b["fire"]+=1; b["succ_fire"]+= (res["status"]=="translated")
        b.setdefault("runs",set()).add(run[:13])
print("fire rate stratified by (system_sha, schema_sha) — the prompt/schema generation:")
for k,v in sorted(by.items(), key=lambda kv:-kv[1]["multi"]):
    r=100*v["fire"]/v["multi"] if v["multi"] else 0
    print(f"  sys={k[0]} schema={k[1]}  chains={v['n']:4d} multi={v['multi']:4d} "
          f"fire={v['fire']:3d} ({r:5.1f}%)  fired&translated={v['succ_fire']}  runs={sorted(v['runs'])}")
print()
print(f"results with NO transcript ({len(missing)}):")
for m in missing: print("   ",m)
