import json
d=json.load(open('seatfix_rescore.json'))
ARMS=['base','h1','h2','h2b','h1r']
st={a:{m['item_id']:(m['arguable'],{s:m['seats'][s]['status'] for s in ('4a','4b','4c','4d')}) for m in d[a]['mutants']} for a in ARMS}
ids=[i for i in sorted(st['base']) if not st['base'][i][0]]
for label,seats in (('excl 4a',('4b','4c','4d')),('incl 4a',('4a','4b','4c','4d'))):
    row=[]
    for a in ARMS:
        row.append(sum(1 for i in ids if 'detected' in [st[a][i][1][s] for s in seats]))
    print(f"any-seat recall ({label}):", dict(zip(ARMS,[f'{r}/15' for r in row])))
# 4c denominator
for a in ARMS:
    c={}
    for i in ids:
        s=st[a][i][1]['4c']
        c[s]=c.get(s,0)+1
    print(a,'4c site statuses',c)
