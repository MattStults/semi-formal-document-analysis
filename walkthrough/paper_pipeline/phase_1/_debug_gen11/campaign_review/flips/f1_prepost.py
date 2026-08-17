"""F1-regex PRE- vs POST-widening on the fix_matrix anchored populations. Zero spend."""
import os,sys,re,collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0,P1); sys.path.insert(0,os.path.join(P1,"_debug_gen11/fix_matrix"))
import checks, population, detectors
OLD=re.compile(r"\b(dispreferred|disprefer|not preferred|discouraged|"
               r"should be avoided|is worse|undesirable)\b", re.I)
NEW=checks._DISFAVOURED
def fire(mod,rx):
    if mod is None: return []
    out=[]
    for i,a in enumerate(getattr(mod,"asserts",None) or []):
        if getattr(a,"status",None)!="prefer": continue
        m=rx.search(str(getattr(a,"read_back","") or ""))
        if m: out.append((i,getattr(a,"act","?"),m.group(0)))
    return out
items=[i for i in population.all_items() if population.is_scoreable(i)]
print(f"scoreable items: {len(items)}")
for name,rx in (("PRE",OLD),("POST",NEW)):
    tp=fp=pos=neg=0; tphits=[]; fphits=[]
    for it in items:
        mod=it.module()
        isF1 = bool(it.truth) and any(k in detectors.F1_CLASSES for k in it.truth)
        hit=fire(mod,rx)
        if isF1:
            pos+=1
            if hit: tp+=1; tphits.append((it.key,hit[0][2]))
        else:
            neg+=1
            if hit: fp+=1; fphits.append((it.key,hit[0][2]))
    print(f"  {name:5s} recall {tp}/{pos}   FP {fp}/{neg}")
    for k,p in tphits: print(f"        TP {k}  <- '{p}'")
    for k,p in fphits: print(f"        FP {k}  <- '{p}'")
