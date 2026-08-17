"""Does the D1/D2 polarity-RECRUITED A/B cohort create the 33-flip set?  Zero spend."""
import os,sys,json,collections,math
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0,P1); sys.path.insert(0,os.path.join(P1,"_debug_gen11/d1_recruit"))
import census
V=json.load(open(os.path.join(P1,"_debug_gen11/flip_classify/verdicts.json")))
J=json.load(open(os.path.join(P1,"_debug_gen11/flip_classify/flips.json")))
recs={r["clause"]:r for r in J["records"]}
def shp(d):
    h=sum(1 for a in d["asserts"] if a["status"] in ("forbid","permit","oblige"))
    p=sum(1 for a in d["asserts"] if a["status"]=="prefer")
    return "mixed" if h and p else ("hard" if h else ("prefer" if p else "none"))
print(f"{'clause':22s} {'class':26s} {'n':>2s} {'nAB':>3s} {'base':>4s} still-multi still-flip")
n_lost=collections.Counter(); n_tot=collections.Counter()
for cid,r in sorted(recs.items()):
    k=V[cid]["cls"]; n_tot[k]+=1
    base=[d for d in r["draws"] if d["source"]=="graph_v2"]
    nab=len(r["draws"])-len(base)
    sm=len(base)>=2; sf=sm and len(set(shp(d) for d in base))>1
    if not sf: n_lost[k]+=1
    print(f"{cid:22s} {k:26s} {len(r['draws']):2d} {nab:3d} {len(base):4d}  {str(sm):5s}      {str(sf)}")
print("\nIf the D1/D2 polarity-recruited A/B draws are removed (they exist ONLY because")
print("those clauses tripped the polarity detector), flips that DISAPPEAR, per class:")
for k in n_tot: print(f"   {k:26s} lost {n_lost[k]}/{n_tot[k]}")

# base-only corpus census
draws=[census.measure(d) for d in census.collect_runs(census.RUNS_GLOB,"graph_v2")]
bc=collections.defaultdict(list)
for d in draws: bc[d["clause"]].append(d)
multi=[c for c,v in bc.items() if len([x for x in v if not x["unparsed"]])>=2]
print(f"\nBASE-ONLY (no A/B): draws={len(draws)} clauses={len(bc)} multi-draw={len(multi)}")
def wil(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return p*100,max(0,c-h)*100,min(1,c+h)*100
# honest headline recomputation
cnt=collections.Counter(v["cls"] for v in V.values())
n_gen=33-cnt["INSTRUMENT-ARTIFACT"]
print("\n=== HONEST-HEADLINE ARITHMETIC (denominator 112 multi-draw clauses) ===")
for lab,k in (("CONTRADICTION only",cnt["CONTRADICTION"]),
              ("CONTRADICTION + COVERAGE (>=1 draw demonstrably WRONG)",cnt["CONTRADICTION"]+cnt["COVERAGE"]),
              ("CONTRADICTION + COVERAGE + UNSURE",cnt["CONTRADICTION"]+cnt["COVERAGE"]+cnt["UNSURE"]),
              ("all genuine flips",n_gen),("all shape flips (published 29.5%)",33)):
    p,lo,hi=wil(k,112); print(f"  {lab:56s} {k:2d}/112 = {p:4.1f}% [{lo:4.1f},{hi:4.1f}]")
print("\n  n028 is described in the log as MIS-ROUTED but is counted GENUINE (STRENGTH).")
p,lo,hi=wil(cnt['CONTRADICTION'],28); print(f"  contradictions over a 28-clause genuine set: 7/28 = {p:.1f}% [{lo:.1f},{hi:.1f}]")
