#!/usr/bin/env python3
"""The mix->policy map (Matt's expectation, calculus A5 follow-on): given a
failure-mix and environment probabilities, WHICH ordering is cheapest?

Parameterizes the calculus transition system with:
  mix = (fSEP, fREACH, fUNSAT)   fractions of incoming failures by census
  p_o = P(panel overturns a single-tier ruling)   [truth error rate]
  p_u = P(audit finds the translation unfaithful) [translation error rate]
  p_d = P(a delta attempt validates)              [delta hit rate]
  p_m = P(a mint separates)                       [mint hit rate]
and computes EXPECTED cost per policy analytically over the same transition
system as calculus_cost_model.py. Policies: EAGER (premises first, current
order) vs LAZY (route free, premises only at adoption/terminal). Costs in
wave-units: panel 3, audit 1, retranslate 2, delta 1, build 5, mint 8.
Illustrative simplification (documented): retranslation redistributes the
census uniformly and resolves outright half the time.
"""
C = dict(panel=3, audit=1, retr=2, delta=1, build=5, mint=8)

def E(census, lazy, p, prem=(False,False), mints=0, deltas=0):
    p_o,p_u,p_d,p_m = p
    panel,aud = prem
    def premises_cost():
        # expected cost of running R1+R2 now (returns cost, P(resolved there))
        c=0.0; pr=0.0
        if not panel: c+=C["panel"]; pr=p_o
        if not aud:
            c+=(1-pr)*C["audit"]
            # unfaithful -> retranslate: half resolve, half uniform census
            c+=(1-pr)*p_u*(C["retr"])
        return c, pr
    if not lazy and not (panel and aud):
        c,pr=premises_cost()
        cont=(1-pr)
        # after premises: with prob p_u we retranslated: 0.5 resolved, 0.5 uniform census
        resolved_v=cont*p_u*0.5
        go=cont-resolved_v
        avg=(E("SEP",lazy,p,(True,True),mints,deltas)+E("REACH",lazy,p,(True,True),mints,deltas)+E("UNSAT",lazy,p,(True,True),mints,deltas))/3
        stay=E(census,lazy,p,(True,True),mints,deltas)
        return c + go*( (p_u and (cont>0)) and ((cont*p_u*0.5/max(go,1e-9))*avg + (cont*(1-p_u)/max(go,1e-9))*stay) or stay)
    if census=="SEP":
        if deltas<2:
            need = lazy and not (panel and aud)
            c=0.0; pr=0.0
            if need:
                c,pr=premises_cost()
            cont=1-pr
            return c+cont*(C["delta"] + (1-p_d)*E("SEP",lazy,p,(True,True) if need else prem,mints,deltas+1))
        if mints<2:
            return C["mint"] + p_m*E("SEP",lazy,p,prem,mints+1,0) + (1-p_m)*E("UNSAT",lazy,p,prem,mints+1,0)
        return 0.0
    if census=="REACH":
        return C["build"] + E("SEP",lazy,p,prem,mints,deltas)
    if census=="UNSAT":
        if mints<2:
            return C["mint"] + p_m*E("SEP",lazy,p,prem,mints+1,0) + (1-p_m)*E("UNSAT",lazy,p,prem,mints+1,0)
        need = lazy and not (panel and aud)
        c,pr=premises_cost() if need else (0.0,0.0)
        return c
    return 0.0

def emix(mix,lazy,p):
    return sum(f*E(c,lazy,p) for f,c in zip(mix,("SEP","REACH","UNSAT")))

print(f"{'mix (SEP/REACH/UNSAT)':24s} {'p_o':>4s} {'p_u':>4s} | {'EAGER':>7s} {'LAZY':>7s}  winner")
for mix,label in (((0.7,0.2,0.1),"SEP-heavy 70/20/10"),((0.2,0.2,0.6),"UNSAT-heavy 20/20/60"),((0.34,0.33,0.33),"uniform")):
    for p_o,p_u in ((0.02,0.02),(0.10,0.10),(0.25,0.25)):
        p=(p_o,p_u,0.6,0.5)
        e1=emix(mix,False,p); e2=emix(mix,True,p)
        print(f"{label:24s} {p_o:>4.2f} {p_u:>4.2f} | {e1:7.2f} {e2:7.2f}  {'LAZY' if e2<e1 else 'EAGER'}")
