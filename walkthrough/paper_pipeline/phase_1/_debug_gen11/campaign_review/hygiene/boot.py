import json,os,sys,collections,random,statistics
sys.path.insert(0,"/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_golden")
import score_golden as S
B="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_baseline"
DEF=set(S.DEFECT_VERDICTS)
def counts(root,seat):
    c={}
    for f in sorted(os.listdir(root+"/raw")):
        cid,s=f[:-5].rsplit(".",1)
        if s!=seat: continue
        js,_=S.parse_reply(json.load(open(root+"/raw/"+f))["text"])
        if js is None: continue
        n=sum(1 for j in js if isinstance(j,dict) and j.get("verdict") in DEF)
        c[cid]=(n,len([j for j in js if isinstance(j,dict)]))
    return c
random.seed(7)
for seat in ("4b","4c"):
    A=counts(B+"/out",seat); C=counts(B+"/out_4dfixed",seat)
    cl=sorted(set(A)&set(C))
    delta={c:C[c][0]-A[c][0] for c in cl}
    size={c:A[c][1] for c in cl}
    print(f"\n=== seat {seat}: replication pair, {len(cl)} clauses, {sum(size.values())} items ===")
    nz=sorted(((abs(v),c,v) for c,v in delta.items() if v),reverse=True)[:8]
    print(f"  clauses with a nonzero swing: {sum(1 for v in delta.values() if v)}/{len(cl)}; "
          f"largest: {[(c,f'{v:+d}',f'n={size[c]}') for _,c,v in nz]}")
    # bootstrap an 86-item 'control column'
    sims=[]
    for _ in range(20000):
        tot=0; items=0
        while items<86:
            c=random.choice(cl); tot+=delta[c]; items+=size[c]
        sims.append(tot)
    sims.sort()
    lo,hi=sims[int(.025*len(sims))],sims[int(.975*len(sims))]
    print(f"  BOOTSTRAP: a pure-noise 86-item column difference has SD={statistics.pstdev(sims):.2f}, "
          f"95% interval [{lo:+d},{hi:+d}], 99% [{sims[int(.005*len(sims))]:+d},{sims[int(.995*len(sims))]:+d}]")
    print(f"  P(|diff| >= 3) = {sum(1 for s in sims if abs(s)>=3)/len(sims):.3f}; "
          f"P(|diff| >= 26) = {sum(1 for s in sims if abs(s)>=26)/len(sims):.4f}; "
          f"P(|diff| >= 14) = {sum(1 for s in sims if abs(s)>=14)/len(sims):.4f}; "
          f"P(|diff| >= 2) = {sum(1 for s in sims if abs(s)>=2)/len(sims):.3f}")
