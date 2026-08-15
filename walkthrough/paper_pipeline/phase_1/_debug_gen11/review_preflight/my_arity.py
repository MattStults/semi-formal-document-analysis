import glob, json, os, sys, collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0,P1)
import checks, schema
EXCL=("20260815-113545-together-deepseek-v4-flash",)
def scan(exclude):
    chains=[]
    for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
        for rj in sorted(glob.glob(os.path.join(P1,pat))):
            root=os.path.dirname(rj); run=os.path.basename(root)
            if run in exclude: continue
            d=json.load(open(rj))
            ids={r.get("clause_id") for r in d.get("results",[])}
            for res in d.get("results",[]):
                cid=res["clause_id"]
                tp=os.path.join(root,cid+".transcript.json")
                if not os.path.exists(tp): continue
                reps=[m["content"] for m in json.load(open(tp)) if m["role"]=="assistant"]
                if not reps: continue
                atts=[]
                for i,t in enumerate(reps,1):
                    try: obj=json.loads(t)
                    except Exception: obj=None
                    if not isinstance(obj,dict): atts.append((i,"unparseable",[],[])); continue
                    if obj.get("outcome")=="abstained": atts.append((i,"abstained",[],[])); continue
                    raw_mm=checks.arity_mismatches(obj)
                    mod,_=schema.validate_all(obj,clause_id=cid,known_clause_ids=ids)
                    mod_mm=checks.arity_mismatches(mod) if mod is not None else None
                    atts.append((i,"scored",raw_mm,mod_mm))
                chains.append(dict(run=run,clause=cid,status=res["status"],L=len(reps),atts=atts))
    return chains
ch=scan(EXCL)
print(f"chains {len(ch)}  attempt-modules {sum(len(c['atts']) for c in ch)}")
# A: raw-dict vs validated-Module disagreement
dis=[(c['run'][:13],c['clause'],a[0],a[2],a[3]) for c in ch for a in c['atts']
     if a[1]=="scored" and a[3] is not None and sorted(map(str,a[2]))!=sorted(map(str,a[3]))]
noneMod=[(c['clause'],a[0]) for c in ch for a in c['atts'] if a[1]=="scored" and a[3] is None]
print(f"raw-dict vs validated-Module DISAGREEMENTS: {len(dis)}   (validate_all returned None: {len(noneMod)})")
for d in dis[:10]: print("   ",d)
print()
def flagged(a): return a[1]=="scored" and bool(a[2])
# B: headline populations
acc_final=[c for c in ch if c['status']=='translated']
print(f"accepted final attempts n={len(acc_final)}  flagged={sum(1 for c in acc_final if flagged(c['atts'][-1]))}")
ft=[c for c in acc_final if c['L']==1]
print(f"first-try successes    n={len(ft)}       flagged={sum(1 for c in ft if flagged(c['atts'][0]))}")
a1=[c for c in ch if c['atts'] and flagged(c['atts'][0])]
print(f"ATTEMPT-1 drafts flagged: {len(a1)}")
print(f"  of which landed first-try (L==1 & translated): "
      f"{sum(1 for c in a1 if c['L']==1 and c['status']=='translated')}")
print(f"  status of the {len(a1)}: {dict(collections.Counter(c['status'] for c in a1))}")
print(f"  base rate unrepaired over ALL {len(ch)} chains: "
      f"{sum(1 for c in ch if c['status']=='unrepaired')}/{len(ch)} = "
      f"{100*sum(1 for c in ch if c['status']=='unrepaired')/len(ch):.0f}%")
print()
# C: "lethal" = arity mismatch present at EVERY scored attempt AND chain ended unrepaired
leth=[c for c in ch if c['status']=='unrepaired'
      and [a for a in c['atts'] if a[1]=='scored']
      and all(bool(a[2]) for a in c['atts'] if a[1]=='scored')]
print(f"chains carrying arity mismatch at EVERY scored attempt and ending unrepaired: {len(leth)}")
for c in leth: print(f"   {c['run'][:13]} {c['clause']:18s} L={c['L']}")
print(f"  -> distinct CLAUSE ids: {len({c['clause'] for c in leth})} "
      f"{sorted({c['clause'] for c in leth})}")
print()
# D: any-attempt flagged, per clause
anyf=collections.defaultdict(set)
for c in ch:
    if any(flagged(a) for a in c['atts']): anyf[c['clause']].add(c['status'])
print(f"distinct clauses flagged at >=1 attempt anywhere: {len(anyf)}")
for k,v in sorted(anyf.items()): print(f"   {k:18s} {sorted(v)}")
