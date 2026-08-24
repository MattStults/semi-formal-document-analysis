#!/usr/bin/env python3
"""Trace-legality checker: the auditable form of the §9 historical
validation. A TRACE is the recorded transition sequence for one historical
mismatch — each step (state, rule, next-or-terminal) carrying an evidence
pointer (artifact path + sha) in the full pipeline. This checker feeds the
trace to the SAME clingo machine that verified the calculus and asserts
every step is a legal transition — so validation is: (a) deterministic
replay generates the trace from committed artifacts; (b) clingo certifies
trace legality; (c) the predicted terminal matches the recorded resolution.
Demo: one legal trace, one tampered trace."""
import clingo, json
BASE = open("calculus.lp").read()
def check_trace(steps):
    facts = "".join(
        (f"tstep({i},{s},{r},{t}).\n" if t.startswith("s(") else f"tterm({i},{s},{r},{t}).\n")
        for i,(s,r,t) in enumerate(steps))
    prog = BASE + facts + """
badstep(I) :- tstep(I,S,R,T), not trans(S,R,T).
badstep(I) :- tterm(I,S,R,T), not term(S,R,T).
#show badstep/1.
"""
    ctl = clingo.Control(['--warn=none']); ctl.add('base',[],prog); ctl.ground([('base',[])])
    out=[]
    with ctl.solve(yield_=True) as h:
        for m in h: out=[str(a) for a in m.symbols(shown=True) if a.name=="badstep"]
    return out
legal = [
  ("s(sep,unaud,0,0,0,0,0,0,0)","r1","s(sep,unaud,1,0,0,0,0,0,0)"),
  ("s(sep,unaud,1,0,0,0,0,0,0)","r2","s(sep,faith,1,1,0,0,0,0,0)"),
  ("s(sep,faith,1,1,0,0,0,0,0)","r3","resolved_d"),
]
tampered = legal[:2] + [("s(sep,faith,1,1,0,0,0,0,0)","r5","terminal_doc")]  # illegal: r5 at SEP
print("legal trace violations:   ", check_trace(legal) or "NONE — certified")
print("tampered trace violations:", check_trace(tampered))
