"""Draw sample B (40 of the 73 deontic_hard) and write blind judge payloads."""
import json, os, re, random

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "census.json")))
hard = sorted([r for r in rows if r["deontic_hard"]], key=lambda r: r["clause_id"])
assert len(hard) == 73, len(hard)
samp = random.Random(20260815).sample(hard, 40)
samp.sort(key=lambda r: r["clause_id"])


def extract(pu_path):
    t = open(pu_path).read()
    est = re.search(r"ESTABLISHES.*?:\n(.*?)\n\n", t, re.S)
    src = re.search(r"SOURCE TEXT[^\n]*\n(.*?)(?:\n\nCROSS-REFERENCED|\Z)", t, re.S)
    est = est.group(1).strip() if est else ""
    src = src.group(1).strip() if src else ""
    if not est:  # non-graph clause format: fall back to the text: block
        m = re.search(r"\ntext:\n(.*?)(?:\n\nCROSS-REFERENCED|\Z)", t, re.S)
        est = (m.group(1).strip() if m else "")
    return est, src


out = []
for i, r in enumerate(samp):
    pu = r["path"][:-5] + ".prompt_user.txt"
    est, src = extract(pu) if os.path.exists(pu) else ("", "")
    out.append(dict(idx=i, clause_id=r["clause_id"], path=r["path"],
                    establishes=est, source=src))
json.dump(out, open(os.path.join(HERE, "sample.json"), "w"), indent=1)
print(len(out), "items;", sum(1 for o in out if not o["establishes"]), "missing establishes;",
      sum(1 for o in out if not o["source"]), "missing source")
for o in out[:3]:
    print("---", o["idx"], repr(o["establishes"])[:200], "|", repr(o["source"])[:200])
