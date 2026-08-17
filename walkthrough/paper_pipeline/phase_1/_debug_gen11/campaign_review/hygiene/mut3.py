import json,math
from math import comb
d=json.load(open('seatfix_rescore.json'))
ARMS=['base','h1','h2','h2b','h1r']
st={a:{m['item_id']:(m['arguable'],{s:m['seats'][s]['status'] for s in ('4a','4b','4c','4d')}) for m in d[a]['mutants']} for a in ARMS}
ids=[i for i in sorted(st['base']) if not st['base'][i][0]]
def mc(n10,n01):
    n=n10+n01
    if n==0: return 1.0
    k=min(n10,n01); return min(1,2*sum(comb(n,i) for i in range(k+1))/2**n)
def det(a,i,s): return st[a][i][1][s]=='detected'
def sites(s): return [i for i in ids if st['base'][i][1][s] not in ('site-absent','not-run')]
print("== per-item DETECTION change sets (mutant sites) ==")
for s in ('4b','4c','4d'):
    S=sites(s)
    for a,b in [('base','h1'),('base','h2'),('base','h2b'),('h2','h2b'),('h2','h1r'),('h1','h1r')]:
        gain=[i for i in S if not det(a,i,s) and det(b,i,s)]
        loss=[i for i in S if det(a,i,s) and not det(b,i,s)]
        print(f"  {s} {a:5}->{b:5} n={len(S):2} gain={len(gain)}{gain} loss={len(loss)}{loss} McNemar p={mc(len(loss),len(gain)):.4f}")
    print()
# control clause detail for H1 mechanism
print("== control FP per clause per arm (4c) ==")
cl={a:{c['clause_id']:c['false_positives'] for c in d[a]['controls']} for a in ARMS}
jd={c['clause_id']:c['judged'] for c in d['base']['controls']}
print(f"{'clause':22}"+"".join(f"{a:>8}" for a in ARMS)+"   judged")
for c in sorted(cl['base']):
    print(f"{c:22}"+"".join(f"{cl[a][c]['4c']:>8}" for a in ARMS)+f"   {jd[c]['4c']}")
print(f"{'TOTAL':22}"+"".join(f"{sum(cl[a][c]['4c'] for c in cl[a]):>8}" for a in ARMS))
print()
print(f"{'clause(4b)':22}"+"".join(f"{a:>8}" for a in ARMS))
for c in sorted(cl['base']):
    print(f"{c:22}"+"".join(f"{cl[a][c]['4b']:>8}" for a in ARMS))
print(f"{'TOTAL':22}"+"".join(f"{sum(cl[a][c]['4b'] for c in cl[a]):>8}" for a in ARMS))
print()
print("== borrow-control FP (4c / 4b) ==")
for a in ARMS:
    b=d[a]['borrows']
    f4c=sum(1 for x in b if x['seats']['4c']['status']=='detected')
    f4b=sum(1 for x in b if x['seats']['4b']['status']=='detected')
    print(f"  {a:5} 4c {f4c}/14   4b {f4b}/14")
