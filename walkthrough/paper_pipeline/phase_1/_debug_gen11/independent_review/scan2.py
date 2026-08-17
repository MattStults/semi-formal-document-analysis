import json,glob,os,re
ids=sorted(os.path.basename(p)[:-5] for p in glob.glob('_debug_gen11/ds_opus_loop/out/*.json')
           if '.transcript' not in p and '.raw' not in p)
HEDGE=re.compile(r'\b(generally|by default|default|typically|usually|may want to|should)\b',re.I)
n_h=0;n_slot=0;n_ov=0;n_undecl=0
for i in ids:
    M=json.load(open('_debug_gen11/ds_opus_loop/out/%s.json'%i))
    cn={c['name'] for c in M['concepts']}
    req={r.split('/')[0] for r in M['requires']}; inp={r.split('/')[0] for r in M['inputs']}
    ont={re.match(r'([a-z_][A-Za-z0-9_]*)',e['atom']).group(1) for e in M['ontology']}
    ov=req&inp
    if ov: print(i,'REQ/INPUT OVERLAP',sorted(ov)); n_ov+=1
    for e in M['asserts']+M['beats']:
        rb=e.get('read_back','') or ''
        if rb.count('%')!=len(e.get('read_back_slots',[])):
            print(i,'SLOT MISMATCH',repr(rb)); n_slot+=1
        if e.get('status') in ('forbid','oblige'):
            m=HEDGE.search(rb)
            if m and m.group(1).lower() in ('generally','by default','default','typically','usually'):
                print(i,'HEDGED READ-BACK on hard %s: %r'%(e['status'],rb)); n_h+=1
    # undeclared body predicates
    for kind in ('ontology','asserts'):
        for e in M[kind]:
            for f in re.findall(r'([a-z_][A-Za-z0-9_]*)\s*\(', e.get('body') or ''):
                if f not in (ont|req|inp):
                    print(i,'UNDECLARED body predicate',f,'in',e.get('atom') or e.get('act')); n_undecl+=1
print('\nhedged read-back on unqualified forbid/oblige:',n_h)
print('read_back slot mismatches:',n_slot)
print('requires/inputs overlaps:',n_ov)
print('undeclared body predicates:',n_undecl)
