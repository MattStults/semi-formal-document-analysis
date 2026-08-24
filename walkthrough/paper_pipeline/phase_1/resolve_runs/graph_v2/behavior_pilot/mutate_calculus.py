#!/usr/bin/env python3
"""Mutation testing for BOTH calculus checkers (the dead-slot-probe lesson:
a checker that has never caught a planted defect may be checking itself).
Each mutation plants one defect; the checker MUST report a violation.
"""
import subprocess, sys, re
PY = sys.executable
def run_clingo(prog):
    import clingo
    ctl = clingo.Control(['--warn=none']); ctl.add('base',[],prog); ctl.ground([('base',[])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out=[str(a) for a in m.symbols(shown=True)]
    return out
base = open("calculus.lp").read()
muts = [
 ("drop R4 (reach has no rule)", lambda s: s.replace(
    "app(s(reach,faith,1,1,R,B,M,D,K), r4) :- state(s(reach,faith,1,1,R,B,M,D,K)).","")),
 ("drop R5x guard (unsat exhausted, no rule)", lambda s: s.replace(
    "app(s(unsat,faith,1,1,R,B,2,D,K), r5x) :- state(s(unsat,faith,1,1,R,B,2,D,K)).","")),
 ("double-fire: r3 also at exhausted deltas", lambda s: s.replace(
    "app(s(sep,faith,1,1,R,B,M,D,K), r3) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.",
    "app(s(sep,faith,1,1,R,B,M,D,K), r3) :- state(s(sep,faith,1,1,R,B,M,D,K)).")),
 ("cycle: r3 stops consuming budget", lambda s: s.replace(
    "trans(s(sep,faith,1,1,R,B,M,D,K), r3, s(sep,faith,1,1,R,B,M,D,K+1)) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.",
    "trans(s(sep,faith,1,1,R,B,M,D,K), r3, s(sep,faith,1,1,R,B,M,D,K)) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.")),
 ("drop R2b (unfaithful dead-ends)", lambda s: s.replace(
    "app(s(C,unfaith,1,1,0,B,M,D,K), r2b) :- state(s(C,unfaith,1,1,0,B,M,D,K)).","")),
]
ok=0
for name, f in muts:
    mprog = f(base)
    assert mprog != base, f"mutation no-op: {name}"
    viol = run_clingo(mprog)
    caught = bool(viol)
    print(f"  {'CAUGHT' if caught else 'MISSED'}: {name}" + (f"  ({viol[:2]}...)" if caught else ""))
    ok += caught
print(f"clingo checker: {ok}/{len(muts)} planted defects caught")
sys.exit(0 if ok==len(muts) else 1)
