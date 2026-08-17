import json,math,sys,os
from math import comb, sqrt
sys.path.insert(0,"/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/_debug_gen11/stage4_golden")
import score_golden as S

def mcnemar_exact(n10,n01):
    n=n10+n01
    if n==0: return 1.0
    k=min(n10,n01)
    p=sum(comb(n,i) for i in range(0,k+1))/2**n
    return min(1.0,2*p)

def wilson(k,n,z=1.96):
    if n==0: return (0,1)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))

def pois_ci(k):
    # exact Poisson 95% CI via chi2 quantiles (Garwood)
    from statistics import NormalDist
    # use chi2 via gamma inverse: implement by bisection on regularized gamma
    def gammainc_lower_reg(s,x):
        # series
        if x<=0: return 0.0
        if x < s+1:
            t=1.0/s; sm=t; n=1
            while True:
                t*= x/(s+n); sm+=t; n+=1
                if t<1e-15*sm or n>10000: break
            return sm*math.exp(-x+s*math.log(x)-math.lgamma(s))
        # continued fraction for upper
        tiny=1e-300; b=x+1-s; c=1/tiny; d=1/b; h=d; i=1
        while i<10000:
            an=-i*(i-s); b+=2; d=an*d+b
            if abs(d)<tiny: d=tiny
            c=b+an/c
            if abs(c)<tiny: c=tiny
            d=1/d; de=d*c; h*=de; 
            if abs(de-1)<1e-15: break
            i+=1
        q=math.exp(-x+s*math.log(x)-math.lgamma(s))*h
        return 1-q
    def solve(target,k,lo,hi):
        for _ in range(200):
            mid=(lo+hi)/2
            # P(X<=k | mu=mid) = 1 - gammainc_lower_reg(k+1,mid)
            v=1-gammainc_lower_reg(k+1,mid)
            if v>target: lo=mid
            else: hi=mid
        return (lo+hi)/2
    lower = 0.0 if k==0 else solve(0.025,k-1,0,1000)  # P(X>=k)=0.025 -> P(X<=k-1)=0.975
    if k>0:
        # solve P(X<=k-1|mu)=0.025
        lo,hi=0,1000
        for _ in range(200):
            mid=(lo+hi)/2
            v=1-gammainc_lower_reg(k,mid)
            if v>0.025: lo=mid
            else: hi=mid
        lower=(lo+hi)/2
    lo,hi=0,1000
    for _ in range(200):
        mid=(lo+hi)/2
        v=1-gammainc_lower_reg(k+1,mid)
        if v>0.975: lo=mid
        else: hi=mid
    upper=(lo+hi)/2
    return lower,upper

print("== Q: one replicate pair, diff=3. 95% CI on sigma from a SINGLE normal observation ==")
# chi2_1 quantiles
q975=5.023886; q025=0.0009821
for d in (3,1,2):
    print(f"  |d|={d}: sigma in [{d/math.sqrt(q975):.2f}, {d/math.sqrt(q025):.1f}]")

print()
print("== Poisson CI on the discordant count, and implied SD of a control-column difference ==")
for seat,m,n in (('4c',5,86),('4b',1,86)):
    lo,hi=pois_ci(m)
    print(f"  seat {seat}: H2 vs H2b discordant items {m}/{n}; Poisson 95% CI on E[m] = [{lo:.2f},{hi:.2f}]")
    print(f"            SD(net diff)=sqrt(E[m]) in [{math.sqrt(lo):.2f},{math.sqrt(hi):.2f}]  ->  95% noise band +/-[{1.96*math.sqrt(lo):.1f},{1.96*math.sqrt(hi):.1f}]")
    print(f"            per-item discordance {m}/{n} Wilson 95% = [{wilson(m,n)[0]*100:.1f}%,{wilson(m,n)[1]*100:.1f}%]")

print()
print("== McNemar exact, paired per-item, control column ==")
for lab,n10,n01 in [("4c base->h1  (48->22)",32,6),
                    ("4c base->h2  (48->25)",29,6),
                    ("4c h2->h2b   (25->22) REPLICATE",4,1),
                    ("4c h2->h1r   (25->11)",14,0),
                    ("4b base->h2  (3->1)",3,1),
                    ("4b base->h1  (3->5)",0,2),
                    ("4b h2->h2b   (1->2) REPLICATE",0,1)]:
    print(f"  {lab:34} n10={n10:2} n01={n01:2}  exact p = {mcnemar_exact(n10,n01):.4g}")
