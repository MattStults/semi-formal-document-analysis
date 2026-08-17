import json, collections
d=json.load(open('seatfix_rescore.json'))
ARMS=['base','h1','h2','h2b','h1r']
# per-item status per arm
st={a:{m['item_id']:(m['class'],m['arguable'],{s:m['seats'][s]['status'] for s in ('4a','4b','4c','4d')}) for m in d[a]['mutants']} for a in ARMS}
ids=sorted(st['base'])
print("ITEM-LEVEL MUTANT STATUS (unarguable only), seats 4b/4c/4d")
print(f"{'item':6} {'class':27} {'seat':4} " + " ".join(f"{a:>7}" for a in ARMS))
disc=collections.Counter()
for i in ids:
    cls,arg,_=st['base'][i]
    if arg: continue
    for seat in ('4b','4c','4d'):
        vals=[st[a][i][2][seat] for a in ARMS]
        if all(v in ('site-absent','not-run') for v in vals): continue
        mark=' *' if len(set(vals))>1 else ''
        print(f"{i:6} {cls:27} {seat:4} " + " ".join(f"{v[:7]:>7}" for v in vals)+mark)
# h2 vs h2b discordance on mutant sites
print()
for seat in ('4b','4c','4d'):
    tot=0;dd=0
    for i in ids:
        if st['base'][i][1]: continue
        a,b=st['h2'][i][2][seat],st['h2b'][i][2][seat]
        if a in ('site-absent','not-run') and b in ('site-absent','not-run'): continue
        tot+=1; dd+= (a!=b)
    print(f"H2 vs H2b mutant-site discordance seat {seat}: {dd}/{tot}")
# any-seat recall per arm
print()
for a in ARMS:
    det=sum(1 for i in ids if not st[a][i][1] and 'detected' in [st[a][i][2][s] for s in ('4b','4c','4d')])
    print(f"{a}: any-seat recall {det}/15")
