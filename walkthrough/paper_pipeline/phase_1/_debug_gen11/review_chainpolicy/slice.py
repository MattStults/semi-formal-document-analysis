import sys, os, io, re, contextlib, json
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, P1)
import translate as T
class A:
    clause=section=kinds=provider=model=max_tokens=None
    limit=None; live=False; show_prompt=0; only_stale=False
d=os.path.join(P1,"resolve_runs/graph_v2")
def price(limit, double=True):
    a=A(); a.limit=limit
    buf=io.StringIO(); cwd=os.getcwd()
    try:
        os.chdir(d)
        with contextlib.redirect_stdout(buf):
            T.run(T.load_config("config_corpus_all.json"), a)
    finally: os.chdir(cwd)
    return float(re.search(r"cost \(worst\) : \$([0-9.]+)", buf.getvalue()).group(1))
lo,hi=1,773
while lo<hi:
    mid=(lo+hi+1)//2
    if price(mid)<=8.0: lo=mid
    else: hi=mid-1
print("max gate-passing corpus_all slice under 2x doubling:", lo, "->", price(lo))
print("at", lo+1, "->", price(lo+1))
