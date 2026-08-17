import json, os, sys, collections, math, itertools
SG="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_golden"
sys.path.insert(0, SG)
import score_golden as S
G11="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11"
ARMS={'base':SG+'/out_deepseek','h1':G11+'/seat_fix/out_h1','h2':G11+'/seat_fix/out_h2',
      'h2b':G11+'/seat_fix/out_h2b','h1r':G11+'/seat_fix/out_h1r'}
key=json.load(open(SG+'/key.json'))
ctl=[i for i in key['items'] if i['kind']=='control']
armof={i['item_id']:i['arm'] for i in key['items']}

def load(root):
    out={}
    for a in sorted(key['arms']):
        out[a],_=S.load_arm(os.path.join(root,a))
    return out

data={n:load(p) for n,p in ARMS.items()}

# per-item verdict map for control clauses
def ctl_items(d, item):
    got=d.get(f"arm{item['arm']}",{}).get(item['clause_id'],{})
    res={}
    for seat in ('4a','4b','4c','4d'):
        blob=got.get(seat)
        if blob is None or blob['judgements'] is None: continue
        for j in blob['judgements']:
            if not isinstance(j,dict): continue
            nm,_=S._norm_item(str(j.get('item','')))
            res[(seat,nm)]=j.get('verdict')
    return res

per={n:{} for n in ARMS}
for n,d in data.items():
    for it in ctl:
        for k,v in ctl_items(d,it).items():
            per[n][(it['clause_id'],)+k]=v

DEF=set(S.DEFECT_VERDICTS)
def fpset(n,seat):
    return {k for k,v in per[n].items() if k[1]==seat and v in DEF}
def universe(n,seat):
    return {k for k in per[n] if k[1]==seat}

print("=== CONTROL COLUMN: per-item paired discordance ===")
for seat in ('4b','4c'):
    print(f"\n-- seat {seat} --")
    for a,b in [('h2','h2b'),('base','h1'),('base','h2'),('h2','h1r'),('h1','h1r')]:
        ua,ub=universe(a,seat),universe(b,seat)
        common=ua&ub
        fa,fb=fpset(a,seat)&common, fpset(b,seat)&common
        n01=len(fb-fa); n10=len(fa-fb)
        print(f"  {a:5}->{b:5} n={len(common):3}  FP {len(fa):3}->{len(fb):3} "
              f"net {len(fb)-len(fa):+3}   flips: {a}only={n10} {b}only={n01} "
              f"discordant={n10+n01} ({100*(n10+n01)/max(len(common),1):.1f}%)")
