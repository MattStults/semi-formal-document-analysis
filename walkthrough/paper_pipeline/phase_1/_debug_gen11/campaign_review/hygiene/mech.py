import json,os,sys,re,collections
G="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11"
sys.path.insert(0,G+"/stage4_golden"); sys.path.insert(0,G+"/seat_fix")
import score_golden as S, needs_join
N,P=needs_join.load()
def items(root,arm,cid,seat):
    p=os.path.join(root,arm,'raw',f'{cid}.{seat}.json')
    if not os.path.exists(p): return None,None
    blob=json.load(open(p)); js,_=S.parse_reply(blob['text'])
    if js is None: return None,None
    v={S._norm_item(str(j['item']))[0]: j['verdict'] for j in js if isinstance(j,dict)}
    # item text blocks from the prompt
    txt={}
    for b in re.split(r'\n(?=  item )', blob['prompt']):
        m=re.match(r'  item (\S+)',b)
        if m: txt[m.group(1)]=b
    return v,txt
key=json.load(open(G+"/stage4_golden/key.json"))
ctl=[(i['clause_id'],f"arm{i['arm']}") for i in key['items'] if i['kind']=='control']
tot=collections.Counter()
print(f"{'clause':22}{'arm':6}{'names':38}{'base':>5}{'h1':>5}  flipped-with-name / flipped-total")
for cid,arm in ctl:
    a,_=items(G+'/stage4_golden/out_deepseek',arm,cid,'4c')
    b,tx=items(G+'/seat_fix/out_h1',arm,cid,'4c')
    if a is None or b is None: continue
    names=[n for n,_ in needs_join.borrowed_concepts(cid,N,P)]
    flipped=[k for k in a if a.get(k)=='unlicensed' and b.get(k)!='unlicensed']
    withname=[k for k in flipped if any(n in tx.get(k,'') for n in names)]
    nm_items=[k for k in a if any(n in tx.get(k,'') for n in names)]
    tot['flip']+=len(flipped); tot['flip_named']+=len(withname); tot['named']+=len(nm_items)
    tot['named_flipped']+=len([k for k in nm_items if a.get(k)=='unlicensed' and b.get(k)!='unlicensed'])
    tot['named_fp_base']+=len([k for k in nm_items if a.get(k)=='unlicensed'])
    print(f"{cid:22}{arm:6}{','.join(names)[:36]:38}"
          f"{sum(1 for v in a.values() if v=='unlicensed'):>5}{sum(1 for v in b.values() if v=='unlicensed'):>5}"
          f"   {len(withname)}/{len(flipped)}   (items naming a borrowed concept: {len(nm_items)})")
print()
print(f"TOTAL 4c false positives cleared by H1: {tot['flip']}")
print(f"   of which the item actually mentions a name on the node's NEEDS list: {tot['flip_named']}")
print(f"   items that DO mention a NEEDS name and were FP at base: {tot['named_fp_base']}; of those cleared: {tot['named_flipped']}")
