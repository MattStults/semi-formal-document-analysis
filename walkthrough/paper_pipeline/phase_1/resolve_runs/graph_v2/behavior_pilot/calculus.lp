% ERROR CALCULUS single-mismatch machine — ASP encoding (v1 obligation A5).
% State: s(Census,V,Panel,Aud,Retr,Built,Mints,Defens,Deltas)
% Checked properties: no open state with 0 applicable rules (gap), none with
% 2+ (ambig), no cycle among open states (termination with budgets).
census(sep;reach;unsat). vv(unaud;faith;unfaith). bool(0;1).
mm(0;1;2). dd(0;1;2).
state(s(C,V,P,A,R,B,M,D,K)) :- census(C), vv(V), bool(P), bool(A), bool(R),
                               bool(B), mm(M), bool(D), dd(K).
% --- router: applicable(S,Rule) and trans(S,Rule,S') ---
app(s(C,V,0,A,R,B,M,D,K), r1) :- state(s(C,V,0,A,R,B,M,D,K)).
trans(s(C,V,0,A,R,B,M,D,K), r1, s(C,V,1,A,R,B,M,D,K)) :- state(s(C,V,0,A,R,B,M,D,K)).
term(s(C,V,0,A,R,B,M,D,K), r1, resolved_t) :- state(s(C,V,0,A,R,B,M,D,K)).
app(s(C,V,1,0,R,B,M,D,K), r2) :- state(s(C,V,1,0,R,B,M,D,K)).
trans(s(C,V,1,0,R,B,M,D,K), r2, s(C,faith,1,1,R,B,M,D,K))   :- state(s(C,V,1,0,R,B,M,D,K)).
trans(s(C,V,1,0,R,B,M,D,K), r2, s(C,unfaith,1,1,R,B,M,D,K)) :- state(s(C,V,1,0,R,B,M,D,K)).
app(s(C,unfaith,1,1,0,B,M,D,K), r2b) :- state(s(C,unfaith,1,1,0,B,M,D,K)).
trans(s(C,unfaith,1,1,0,B,M,D,K), r2b, s(C2,faith,1,1,1,B,M,D,K)) :- state(s(C,unfaith,1,1,0,B,M,D,K)), census(C2).
term(s(C,unfaith,1,1,0,B,M,D,K), r2b, resolved_v) :- state(s(C,unfaith,1,1,0,B,M,D,K)).
app(s(sep,faith,1,1,R,B,M,D,K), r3) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.
term(s(sep,faith,1,1,R,B,M,D,K), r3, resolved_d) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.
trans(s(sep,faith,1,1,R,B,M,D,K), r3, s(sep,faith,1,1,R,B,M,D,K+1)) :- state(s(sep,faith,1,1,R,B,M,D,K)), K < 2.
app(s(sep,faith,1,1,R,B,M,D,2), r3x) :- state(s(sep,faith,1,1,R,B,M,D,2)).
trans(s(sep,faith,1,1,R,B,M,D,2), r3x, s(C2,faith,1,1,R,B,M+1,D,0)) :- state(s(sep,faith,1,1,R,B,M,D,2)), M < 2, census(C2).
term(s(sep,faith,1,1,R,B,2,D,2), r3x, terminal_doc) :- state(s(sep,faith,1,1,R,B,2,D,2)).
term(s(sep,faith,1,1,R,B,2,0,2), r3x, defensible)   :- state(s(sep,faith,1,1,R,B,2,0,2)).
app(s(reach,faith,1,1,R,B,M,D,K), r4) :- state(s(reach,faith,1,1,R,B,M,D,K)).
trans(s(reach,faith,1,1,R,B,M,D,K), r4, s(sep,faith,1,1,R,1,M,D,K)) :- state(s(reach,faith,1,1,R,B,M,D,K)).
app(s(unsat,faith,1,1,R,B,M,D,K), r5) :- state(s(unsat,faith,1,1,R,B,M,D,K)), M < 2.
trans(s(unsat,faith,1,1,R,B,M,D,K), r5, s(C2,faith,1,1,R,B,M+1,D,0)) :- state(s(unsat,faith,1,1,R,B,M,D,K)), M < 2, census(C2).
app(s(unsat,faith,1,1,R,B,2,D,K), r5x) :- state(s(unsat,faith,1,1,R,B,2,D,K)).
term(s(unsat,faith,1,1,R,B,2,D,K), r5x, terminal_doc) :- state(s(unsat,faith,1,1,R,B,2,D,K)).
term(s(unsat,faith,1,1,R,B,2,0,K), r5x, defensible)   :- state(s(unsat,faith,1,1,R,B,2,0,K)).
% --- reachability from the three initial states ---
init(s(C,unaud,0,0,0,0,0,0,0)) :- census(C).
reach(S) :- init(S).
reach(T) :- reach(S), trans(S,_,T).
% --- properties ---
open(S) :- reach(S).
nApp(S,N) :- open(S), N = #count{ Ru : app(S,Ru) }.
gap(S)   :- nApp(S,0), not hasTerm(S).
hasTerm(S) :- term(S,_,_).
gapReal(S) :- nApp(S,0).
ambig(S) :- nApp(S,N), N >= 2.
% cycle among reachable open states
path(S,T) :- reach(S), trans(S,_,T).
path(S,T) :- path(S,U), trans(U,_,T).
cycle(S) :- path(S,S).
#show gapReal/1.
#show ambig/1.
#show cycle/1.
