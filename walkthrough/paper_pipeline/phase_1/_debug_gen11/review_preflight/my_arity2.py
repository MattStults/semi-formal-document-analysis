import glob, json, os, sys, collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0,P1); import checks, schema
EXCL=("20260815-113545-together-deepseek-v4-flash",)
rows=[]
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
    for rj in sorted(glob.glob(os.path.join(P1,pat))):
        root=os.path.dirname(rj); run=os.path.basename(root)
        if run in EXCL: continue
        d=json.load(open(rj)); ids={r["clause_id"] for r in d.get("results",[])}
        for res in d.get("results",[]):
            cid=res["clause_id"]; tp=os.path.join(root,cid+".transcript.json")
            if not os.path.exists(tp): continue
            reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
            for i,t in enumerate(reps,1):
                try: obj=json.loads(t)
                except Exception: continue
                if not isinstance(obj,dict) or obj.get("outcome")=="abstained": continue
                mm=checks.arity_mismatches(obj)
                mod,br=schema.validate_all(obj,clause_id=cid,known_clause_ids=ids)
                rows.append(dict(run=run,clause=cid,att=i,L=len(reps),status=res["status"],
                                 flagged=bool(mm),live=(mod is not None),nbreach=len(br)))
f=[r for r in rows if r["flagged"]]
print(f"attempt-modules scored by the replay: {len(rows)}   flagged by replay: {len(f)}")
print(f"  of those, the LIVE loop would actually emit the arity finding "
      f"(validate_all returned a Module): {sum(1 for r in f if r['live'])}")
print(f"  suppressed live by the mod-is-None short circuit: {sum(1 for r in f if not r['live'])}")
print()
a1=[r for r in f if r["att"]==1]
print(f"attempt-1 flagged: {len(a1)}; live-emitting: {sum(1 for r in a1 if r['live'])}")
for r in a1: print(f"   {r['run'][:13]} {r['clause']:18s} L={r['L']} status={r['status']:10s} live={r['live']} schema_breaches={r['nbreach']}")
print()
# how many flagged attempt-modules were OTHERWISE clean (would be a NEW repair round)?
newround=[r for r in f if r["live"] and r["nbreach"]==0]
print(f"flagged attempts with ZERO schema breaches (arity alone could add a round): {len(newround)}")
for r in newround: print(f"   {r['run'][:13]} {r['clause']:18s} att {r['att']}/{r['L']} status={r['status']}")
