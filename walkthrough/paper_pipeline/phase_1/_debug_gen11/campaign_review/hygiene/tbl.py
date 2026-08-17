import json, collections
d=json.load(open('seatfix_rescore.json'))
ARMS=['base','h1','h2','h2b','h1r']
print(json.dumps({k:list(v) for k,v in d.items()},indent=0)[:400])
for a in ARMS:
    v=d[a]
    print(a, {k:(len(x) if isinstance(x,list) else x) for k,x in v.items() if k!='root'})
