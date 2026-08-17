import json,glob,os,re,collections
CORP=json.load(open('resolve_runs/graph_v2/node_corpus_all.json'))
by={c['id']:c for c in CORP['clauses']}
ids=sorted(os.path.basename(p)[:-5] for p in glob.glob('_debug_gen11/ds_opus_loop/out/*.json')
           if '.transcript' not in p and '.raw' not in p)

def needs(q):
    m=re.search(r'NEEDS.*?:\n(.*?)\n\nCITATION', q, re.S)
    if not m: return []
    out=[]
    for ln in m.group(1).split('\n'):
        ln=ln.strip()
        if ln.startswith('- '): out.append(ln[2:].split(':')[0].strip())
    return out
def provides(q):
    m=re.search(r'PROVIDES.*?\n(.*?)\n\nNEEDS', q, re.S)
    if not m: return []
    out=[]
    for ln in m.group(1).split('\n'):
        ln=ln.strip()
        if ln.startswith('- '): out.append(ln[2:].split(':')[0].strip())
    return out

A=collections.Counter(); rows=[]
for i in ids:
    M=json.load(open('_debug_gen11/ds_opus_loop/out/%s.json'%i))
    q=by[i]['quote']; N=set(needs(q)); P=set(provides(q))
    borrowed=N-P
    cmap={c['name']:c for c in M['concepts']}
    # C1 borrowed NEEDS self-cited
    selfcite=[n for n in sorted(borrowed) if n in cmap and cmap[n]['licence']=='textual' and cmap[n].get('cites')==i]
    ok    =[n for n in sorted(borrowed) if n in cmap and cmap[n]['licence']!='textual']
    # C2 licence inheritance: textual entry whose body cites an assumed/world concept
    weak={n for n,c in cmap.items() if c['licence'] in ('assumed','world')}
    inherit=[]
    for kind in ('ontology','asserts'):
        for e in M[kind]:
            b=e.get('body') or ''
            used={f for f in re.findall(r'([a-z_][A-Za-z0-9_]*)\s*\(', b)}
            bad=sorted(used & weak)
            if e['licence']=='textual' and bad:
                inherit.append((kind, e.get('atom') or e.get('act'), bad))
    # C3 dead requires (declared, never referenced in any body)
    allbodies=' '.join([(e.get('body') or '') for e in M['ontology']+M['asserts']])
    usedall={f for f in re.findall(r'([a-z_][A-Za-z0-9_]*)\s*\(', allbodies)}
    dead=[r for r in M['requires'] if r.split('/')[0] not in usedall]
    # C4 arity-0 concept used as a term argument somewhere
    zero={n for n,c in cmap.items() if c['arity']==0}
    text=json.dumps(M)
    z=[n for n in sorted(zero) if re.search(r'\([^)]*\b%s\b[^)]*\)'%re.escape(n), text)]
    rows.append((i,len(borrowed),selfcite,ok,inherit,dead,z))
    A['borrowed']+=len(borrowed); A['selfcite']+=len(selfcite)
    if selfcite: A['cl_selfcite']+=1
    if inherit: A['cl_inherit']+=1
    A['inherit']+=len(inherit)
    if dead: A['cl_dead']+=1
    A['dead']+=len(dead)
    if z: A['cl_zero']+=1

for r in rows:
    print('==',r[0],'borrowed_NEEDS=%d'%r[1])
    if r[2]: print('   SELF-CITED textual:',r[2])
    if r[3]: print('   correctly assumed/world:',r[3])
    for k,a,b in r[4]: print('   LICENCE-INHERIT: textual %s %r rests on assumed/world %s'%(k,a,b))
    if r[5]: print('   DEAD requires (never in any body):',r[5])
    if r[6]: print('   ARITY-0 concept used as a term:',r[6])
print()
print('TOTALS over %d modules:'%len(ids))
print(' borrowed NEEDS names total   :',A['borrowed'])
print(' self-cited as textual        :',A['selfcite'],'in',A['cl_selfcite'],'modules')
print(' licence-inheritance breaches :',A['inherit'],'in',A['cl_inherit'],'modules')
print(' dead requires entries        :',A['dead'],'in',A['cl_dead'],'modules')
print(' arity-0-used-as-term modules :',A['cl_zero'])
