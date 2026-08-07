"""Deontic-shape vs topical-shape as predictors of panel relevance.

Two crude one-bit features, scored against the SAME frozen panel:
  DEO   -- does the passage contain a deontic operator (modal verb)?
  TOPIC -- does the passage share a content word with the behaviour's gloss?
and DEO&TOPIC / TOPIC-only, to see which bit carries the signal.
No model call.
"""
import os, re, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "semi-formal-experiment")))
import panel_universe as pu

MODAL = re.compile(r"\b(should|shall|must|may|never|cannot|can't|ought|"
                   r"is not allowed|are not allowed|prohibited|required|permitted|"
                   r"forbidden|disallowed|refuse|decline|avoid)\b", re.I)

# behaviour gloss -> topical content words (hand-written from the behaviour name only)
TOPIC = {
 "helpfulness": r"\b(help|helpful|useful|assist|user'?s? goal|task|answer|comply|"
                r"complies|solve|serve|benefit|empower)\w*",
 "harm-avoidance-to-third-parties":
                r"\b(harm|harmful|danger|dangerous|injur|violen|weapon|abuse|"
                r"third part|non-?user|others|society|world|bystander|外)\w*",
 "avoiding-over-and-under-caution":
                r"\b(caution|cautious|overly|refus|declin|hedg|disclaim|"
                r"unnecessar|conservat|risk|safe|safety|comply|compliance)\w*",
}

def mcc(tp, fp, fn, tn):
    d = math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))
    return (tp*tn - fp*fn)/d if d else 0.0

u = pu.load_universe(spec_keys=("openai",))
print(f"{'behaviour':34s} {'feature':14s} {'TP':>5s} {'FP':>5s} {'FN':>5s} {'TN':>5s} {'prec':>6s} {'rec':>6s} {'MCC':>7s}")
for b in u:
    ps = u[b]["coverage"]["openai"]["passages"]
    top = re.compile(TOPIC[b], re.I)
    for name, pred in (
        ("DEO",        lambda q: bool(MODAL.search(q))),
        ("TOPIC",      lambda q: bool(top.search(q))),
        ("DEO and TOPIC", lambda q: bool(MODAL.search(q)) and bool(top.search(q))),
    ):
        tp=fp=fn=tn=0
        for p in ps:
            gold = p["score"] >= 3          # majority-ish relevant
            got = pred(p["quote"])
            if got and gold: tp+=1
            elif got: fp+=1
            elif gold: fn+=1
            else: tn+=1
        prec = tp/max(tp+fp,1); rec = tp/max(tp+fn,1)
        print(f"{b:34s} {name:14s} {tp:5d} {fp:5d} {fn:5d} {tn:5d} {prec:6.3f} {rec:6.3f} {mcc(tp,fp,fn,tn):7.3f}")
    print()
