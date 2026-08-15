import json, os, re, sys, glob, hashlib
HERE = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, HERE)
from translation_repair_census import classify, FINDING, REPAIR_HEAD

RUNS = ["20260814-163457-together-deepseek-v4-flash",
        "20260814-173322-together-deepseek-v4-flash"]
BASE = os.path.join(HERE, "resolve_runs/graph_v2/translation_sample/runs")

def attempt1_classes(tpath):
    t = json.load(open(tpath))
    # find first repair message
    for m in t:
        if m["role"] != "user":
            continue
        c = m["content"]
        mt = REPAIR_HEAD.match(c)
        if mt and mt.group(1) == "1":
            cls = []
            for line in c.splitlines():
                fm = FINDING.match(line)
                if fm:
                    cls.append(classify(fm.group(1), fm.group(3)))
            return cls, c
    return None, None

rows = []
for r in RUNS:
    d = os.path.join(BASE, r)
    for tp in sorted(glob.glob(d + "/*.transcript.json")):
        cid = os.path.basename(tp).replace(".transcript.json", "")
        cls, msg = attempt1_classes(tp)
        up = os.path.join(d, cid + ".prompt_user.txt")
        rows.append(dict(run=r, clause=cid, classes=cls,
                         has_user=os.path.exists(up), msg=msg))

sole_gloss = [x for x in rows if x["classes"] and set(x["classes"]) == {"borrowed-without-gloss"}]
sole_udbn = [x for x in rows if x["classes"] and set(x["classes"]) == {"undeclared-body-name"}]
any_udbn = [x for x in rows if x["classes"] and "undeclared-body-name" in x["classes"]]
print("total transcripts:", len(rows))
print("with attempt-1 repair:", len([x for x in rows if x['classes']]))
print("SOLE borrowed-without-gloss:", len(sole_gloss), [x["clause"] for x in sole_gloss])
print("SOLE undeclared-body-name:", len(sole_udbn), [x["clause"] for x in sole_udbn])
print("ANY undeclared-body-name:", len(any_udbn), [x["clause"] for x in any_udbn])
json.dump({"sole_gloss": [{k: v for k, v in x.items() if k != 'msg'} for x in sole_gloss],
           "sole_udbn": [{k: v for k, v in x.items() if k != 'msg'} for x in sole_udbn],
           "any_udbn": [{k: v for k, v in x.items() if k != 'msg'} for x in any_udbn]},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cohorts.json"), "w"), indent=1)
