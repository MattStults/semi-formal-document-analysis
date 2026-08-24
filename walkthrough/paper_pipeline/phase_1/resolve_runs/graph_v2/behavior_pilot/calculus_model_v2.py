#!/usr/bin/env python3
"""v2 checker: convergence by PROGRESS RANKING (collider count) instead of
arbitrary mint budgets (calculus A8). State adds X = |collider set| in
{0..3} (3 = 'many', abstracted). Rules: a mint/coin pass must strictly
reduce X or the branch closes immediately (no-progress -> SUSPENDED_OPEN,
re-enterable at a later inventory). TERMINAL_DOC is reachable ONLY via the
exhaustion certificate (X unchanged AND enumeration complete), modeled as
a distinct branch. Delta attempts remain ledger-closed (finite per
version; modeled with the budget standing in for ledger exhaustion).
Checks: coverage (exactly one rule per open state), no cycles, and the
NEW property: X never increases along any transition (progress monotone)."""
import collections
SEP,REACH,UNSAT="SEP","REACH","UNSAT"
def rules(s):
    census,v,panel,aud,retr,built,deltas,X,coined = s
    if not panel:
        return [("R1",["RESOLVED_T",(census,v,True,aud,retr,built,deltas,X,coined)])]
    if not aud:
        return [("R2",[(census,"FAITH",panel,True,retr,built,deltas,X,coined),
                       (census,"UNFAITH",panel,True,retr,built,deltas,X,coined)])]
    if v=="UNFAITH":
        if not retr:
            return [("R2b",[(c,"FAITH",panel,True,True,built,deltas,X,coined) for c in (SEP,REACH,UNSAT)]+["RESOLVED_V"])]
        return []
    if census==SEP:
        if deltas<2:  # ledger-closed finite delta space (budget = stand-in)
            return [("R3",["RESOLVED_D",(census,v,panel,aud,retr,built,deltas+1,X,coined)])]
        # A8: delta space exhausted. ONE intension-coin per inventory version
        # (progress metric here = delta-space growth, not collider count).
        if not coined:
            return [("R3x",[(SEP,v,panel,aud,retr,built,0,X,True),   # new concept -> fresh deltas
                            "SUSPENDED_OPEN"])]                       # coin failed
        return [("R3s",["SUSPENDED_OPEN","TERMINAL_DOC_CERTIFIED","DEFENSIBLE"])]
    if census==REACH:
        return [("R4",[(SEP,v,panel,aud,retr,True,deltas,X,coined)])]
    if census==UNSAT:
        if X>0:
            succ=[]
            # PROGRESS branch: the coined concept strictly reduces colliders
            for nx in range(0,X):        # any strict reduction
                succ.append((SEP,v,panel,aud,retr,built,0,nx,coined))
                succ.append((REACH,v,panel,aud,retr,built,0,nx,coined))
            # NO-PROGRESS branch: X unchanged -> immediate closure, typed:
            succ.append("SUSPENDED_OPEN")          # budgetless honest stop
            succ.append("TERMINAL_DOC_CERTIFIED")  # only via exhaustion certificate
            succ.append("DEFENSIBLE")
            return [("R5",succ)]
        # X==0: no colliders left -> separable by construction (keep deltas!)
        return [("R5done",[(SEP,v,panel,aud,retr,built,deltas,0,coined)])]
    return []
def check():
    init=[(c,"UNAUD",False,False,False,False,0,x,False) for c in (SEP,REACH,UNSAT) for x in (1,2,3)]
    seen=set(); gaps=[]; ambig=[]; edges=collections.defaultdict(set); bad_progress=[]
    front=list(init)
    while front:
        s=front.pop()
        if s in seen: continue
        seen.add(s)
        rs=rules(s)
        if not rs: gaps.append(s); continue
        if len(rs)>1: ambig.append(s)
        for rn,succs in rs:
            for t in succs:
                if isinstance(t,str): edges[s].add(t); continue
                if t[7]>s[7]: bad_progress.append((s,rn,t))   # X increased
                edges[s].add(t); front.append(t)
    color={}
    def dfs(u):
        color[u]=1
        for w in edges.get(u,()):
            if isinstance(w,str): continue
            if color.get(w)==1: return True
            if color.get(w) is None and dfs(w): return True
        color[u]=2; return False
    cyc=any(dfs(s) for s in list(seen) if color.get(s) is None)
    print(f"reachable open states: {len(seen)}")
    print(f"gaps: {len(gaps)}  ambiguities: {len(ambig)}  cycles: {'FOUND' if cyc else 'none'}")
    print(f"progress-monotonicity violations (collider count increased): {len(bad_progress)}")
    terms=set(t for ts in edges.values() for t in ts if isinstance(t,str))
    print("terminals:", sorted(terms))
check()
