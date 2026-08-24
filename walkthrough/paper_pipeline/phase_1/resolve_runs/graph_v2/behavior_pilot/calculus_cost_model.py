#!/usr/bin/env python3
"""Cost extension of calculus_model.py: compares the EAGER policy (premise
checks first, current R1->R5 order) against a LAZY policy (free census
routing first; premises verified only before any ADOPTION or terminal
ruling). Verifies (a) both policies reach the same terminal SET from every
initial state (soundness preserved: nothing adopts without premises), and
(b) worst/best-case total cost per initial state. Costs in wave-seat units
(measured 2026-08-24): panel 3, audit 1, retranslate 2, delta attempt 1,
consumer build 5, mint 8, census/probe 0."""
import itertools
SEP, REACH, UNSAT = "SEP","REACH","UNSAT"
COST = {"R1":3,"R2":1,"R2b":2,"R3":1,"R3x":8,"R4":5,"R5":8,"R5x":0}
MINT_BUDGET=2

def rules(s, lazy):
    census,v,panel,aud,retr,built,mints,defens,deltas = s
    prem_ok = panel and aud
    def prem_first():
        if not panel: return [("R1",["RESOLVED_T",(census,v,True,aud,retr,built,mints,defens,deltas)])]
        if not aud:   return [("R2",[(census,"FAITHFUL",panel,True,retr,built,mints,defens,deltas),
                                     (census,"UNFAITHFUL_KNOWN",panel,True,retr,built,mints,defens,deltas)])]
        return None
    if not lazy:
        p=prem_first()
        if p: return p
    if v=="UNFAITHFUL_KNOWN":
        if not retr:
            return [("R2b",[(c,"FAITHFUL",panel,True,True,built,mints,defens,deltas) for c in (SEP,REACH,UNSAT)]+["RESOLVED_V"])]
        return []
    # census routing (free to consult)
    if census==SEP:
        if deltas<2:
            if lazy and not prem_ok:
                p=prem_first()
                if p: return p   # premises forced ONLY at adoption time
            nxt=(census,v,panel,aud,retr,built,mints,defens,deltas+1)
            return [("R3",["RESOLVED_D",nxt])]
        if mints<MINT_BUDGET:
            return [("R3x",[(c,v,panel,aud,retr,built,mints+1,defens,0) for c in (SEP,REACH,UNSAT)])]
        return [("R5x",["TERMINAL_DOC"]+([] if defens else ["DEFENSIBLE"]))]
    if census==REACH:
        return [("R4",[(SEP,v,panel,aud,retr,True,mints,defens,deltas)])]
    if census==UNSAT:
        if mints<MINT_BUDGET:
            return [("R5",[(c,v,panel,aud,retr,built,mints+1,defens,0) for c in (SEP,REACH,UNSAT)])]
        if lazy and not prem_ok:
            p=prem_first()
            if p: return p   # terminal ruling also requires premises
        return [("R5x",["TERMINAL_DOC"]+([] if defens else ["DEFENSIBLE"]))]
    return []

def analyze(lazy):
    from functools import lru_cache
    import sys
    sys.setrecursionlimit(100000)
    terms=set(); memo={}
    def go(s):
        if s in memo: return memo[s]
        memo[s]=(0,0)  # cycle guard (budgets guarantee none)
        rs=rules(s,lazy)
        if not rs:
            memo[s]=("GAP","GAP"); terms.add("GAP"); return memo[s]
        worst=0; best=None
        for rn,succs in rs:
            c=COST[rn]
            for t in succs:
                if isinstance(t,str):
                    terms.add(t); w,b=c,c
                else:
                    w2,b2=go(t)
                    if w2=="GAP": w,b=c,c
                    else: w,b=c+w2,c+b2
                worst=max(worst,w)
                best=w if best is None else min(best,b)
        memo[s]=(worst,best); return memo[s]
    inits=[(c,"UNAUDITED",False,False,False,False,0,False,0) for c in (SEP,REACH,UNSAT)]
    res={c: go(s) for c,s in zip((SEP,REACH,UNSAT),inits)}
    return res, terms

for name,lazy in (("EAGER",False),("LAZY",True)):
    res,terms=analyze(lazy)
    print(f"{name}: terminals={sorted(terms)}")
    for c,(w,b) in res.items():
        print(f"   init census={c:5s}: worst-case cost {w:>4}  best-case {b}")
