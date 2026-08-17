import json,os,sys,collections,math
sys.path.insert(0,"/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_golden")
import score_golden as S
B="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_baseline"
def load(root):
    m={}
    for f in sorted(os.listdir(root+"/raw")):
        cid,seat=f[:-5].rsplit(".",1)
        js,notes=S.parse_reply(json.load(open(root+"/raw/"+f))["text"])
        if js is None: continue
        for j in js:
            if isinstance(j,dict):
                nm,_=S._norm_item(str(j.get("item","")))
                m[(cid,seat,nm)]=j.get("verdict")
    return m
A=load(B+"/out"); C=load(B+"/out_4dfixed")
DEF=set(S.DEFECT_VERDICTS)
print("REPLICATION PAIR: stage4_baseline/out  vs  out_4dfixed  (prompts byte-identical, 324 calls each)")
for seat in ("4a","4b","4c","4d"):
    ka={k for k in A if k[1]==seat}; kb={k for k in C if k[1]==seat}
    com=ka&kb
    verdict_flip=sum(1 for k in com if A[k]!=C[k])
    da={k for k in com if A[k] in DEF}; db={k for k in com if C[k] in DEF}
    n10=len(da-db); n01=len(db-da)
    clauses=collections.Counter()
    for k in com:
        if (A[k] in DEF)!=(C[k] in DEF): clauses[k[0]]+=1
    print(f"\n seat {seat}: matched items n={len(com)} (arm A only {len(ka-com)}, B only {len(kb-com)})")
    print(f"   any-verdict change      : {verdict_flip}/{len(com)} = {100*verdict_flip/max(len(com),1):.1f}%")
    print(f"   DEFECT-vs-not flips     : A-only={n10} B-only={n01} discordant={n10+n01} "
          f"({100*(n10+n01)/max(len(com),1):.1f}%)  net={n01-n10:+d}")
    print(f"   defect totals           : {len(da)} -> {len(db)}")
    if clauses:
        top=clauses.most_common(6)
        print(f"   clustering: {len(clauses)} clauses carry the flips; largest single-clause swing {top[0][1]} items -> {top}")
