import json,sys,os
NEW='resolve_runs/graph_v2/translation_sample/runs/20260816-094505-together-deepseek-v4-flash'
REF='_debug_gen11/reference_set/modules'
def fmt(m):
    o=[]
    o.append('outcome=%s reason=%s'%(m.get('outcome'),m.get('abstain_reason')))
    o.append('claims: '+json.dumps(m.get('claims'),indent=1))
    o.append('acts: '+json.dumps(m.get('acts')))
    o.append('requires: '+json.dumps(m.get('requires'))+'  inputs: '+json.dumps(m.get('inputs')))
    o.append('concepts:')
    for c in m.get('concepts') or []:
        o.append('   %s/%s : %s'%(c.get('name'),c.get('arity'),c.get('gloss') or c.get('meaning')))
    o.append('ontology:')
    for f in m.get('ontology') or []:
        o.append('   %s  :- %s   // %s'%(f.get('atom'),f.get('body'),f.get('gloss')))
    o.append('asserts:')
    for a in m.get('asserts') or []:
        o.append('   status=%s act=%s body=%s'%(a.get('status'),a.get('act'),a.get('body')))
        o.append('      read_back: %s'%a.get('read_back'))
        for k in ('licence','citation','closure'):
            if a.get(k) is not None: o.append('      %s: %s'%(k,json.dumps(a.get(k))))
    o.append('forbid_body: '+json.dumps(m.get('forbid_body')))
    for k in ('beats','defines','closure'):
        if m.get(k): o.append(k+': '+json.dumps(m.get(k)))
    return '\n'.join(o)
for cid in sys.argv[1:]:
    print('='*80); print('CLAUSE',cid)
    print('---- REFERENCE (as it SHOULD be)')
    rp=os.path.join(REF,cid+'.json')
    print(fmt(json.load(open(rp))) if os.path.exists(rp) else 'NO REFERENCE FILE')
    print('---- NEW DRAW')
    np_=os.path.join(NEW,cid+'.json')
    print(fmt(json.load(open(np_))) if os.path.exists(np_) else 'NO MODULE FILE (unrepaired)')
