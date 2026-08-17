import json,os,sys,collections
sys.path.insert(0,"/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_golden")
import score_golden as S
G="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11"
DEF=set(S.DEFECT_VERDICTS)
def load(root):
    m={}
    for arm in sorted(os.listdir(root)):
        d=os.path.join(root,arm,'raw')
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            cid,seat=f[:-5].rsplit('.',1)
            js,_=S.parse_reply(json.load(open(os.path.join(d,f)))['text'])
            if js is None: continue
            for j in js:
                if isinstance(j,dict):
                    nm,_=S._norm_item(str(j.get('item','')))
                    m[(arm,cid,seat,nm)]=j.get('verdict')
    return m
A=load(G+'/seat_fix/out_h2'); B=load(G+'/seat_fix/out_h2b')
print("FULL H2 vs H2b (all golden arms, every item) — the only same-brief replicate in seat_fix")
for seat in ('4a','4b','4c','4d'):
    com=[k for k in set(A)&set(B) if k[2]==seat]
    ch=sum(1 for k in com if A[k]!=B[k])
    d=sum(1 for k in com if (A[k] in DEF)!=(B[k] in DEF))
    na=sum(1 for k in com if A[k] in DEF); nb=sum(1 for k in com if B[k] in DEF)
    per=collections.Counter()
    for k in com:
        if (A[k] in DEF)!=(B[k] in DEF): per[(k[0],k[1])]+=1
    top=per.most_common(5)
    print(f"  {seat}: n={len(com):4}  any-verdict change {ch:4} ({100*ch/max(len(com),1):5.1f}%)  "
          f"defect-flip {d:4} ({100*d/max(len(com),1):5.1f}%)  defects {na}->{nb} (net {nb-na:+d})  "
          f"largest clause swing {top[0][1] if top else 0} {top[:3]}")

import random,statistics
random.seed(11)
for seat in ('4b','4c'):
    keys=[k for k in set(A)&set(B) if k[2]==seat]
    per=collections.defaultdict(lambda:[0,0])
    for k in keys:
        u=(k[0],k[1]); per[u][1]+=1
        per[u][0]+= (1 if B[k] in DEF else 0)-(1 if A[k] in DEF else 0)
    units=list(per.values())
    sims=[]
    for _ in range(20000):
        t=0;n=0
        while n<86:
            d,s=random.choice(units); t+=d; n+=s
        sims.append(t)
    sims.sort()
    print(f"\nseat {seat}: clause-bootstrap of an 86-item column from the H2/H2b replicate ONLY")
    print(f"  SD={statistics.pstdev(sims):.2f}  95% [{sims[500]:+d},{sims[19499]:+d}]  "
          f"P(|d|>=3)={sum(1 for s in sims if abs(s)>=3)/20000:.3f}  "
          f"P(|d|>=26)={sum(1 for s in sims if abs(s)>=26)/20000:.4f}  "
          f"P(|d|>=14)={sum(1 for s in sims if abs(s)>=14)/20000:.4f}  "
          f"P(|d|>=2)={sum(1 for s in sims if abs(s)>=2)/20000:.3f}")
