"""STEP 1 instrument check: 17 clauses x 3 stock draws = 51 isolated tasks."""
import hashlib, json, os, random

HERE = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
RUNS = [os.path.join(HERE, "resolve_runs/graph_v2/translation_sample/runs", d)
        for d in ("20260814-173322-together-deepseek-v4-flash",
                  "20260814-163457-together-deepseek-v4-flash")]
SCRATCH = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRATCH, "instr")
os.makedirs(OUT, exist_ok=True)

SEED = 20260815 + 7
DRAWS = 3
CLAUSES = ['l171_426_n001', 'l1_170_n014', 'l1_170_n016', 'l1_170_n019',
           'l1_170_n023', 'l1_170_n032', 'l1_170_n045', 'l1_170_n050',
           'l1_170_n053', 'l1_170_n057', 'l1_170_n058', 'l1_170_n062',
           'l1_170_n065', 'l1_170_n067', 'l1_170_n078', 'l1_170_n084',
           'l1_170_n086']


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def user_path(cid):
    for d in RUNS:
        p = os.path.join(d, cid + ".prompt_user.txt")
        if os.path.exists(p):
            return p
    raise SystemExit("no user prompt for " + cid)


system_a = read(os.path.join(RUNS[0], "prompt_system.txt"))
sha = hashlib.sha256(system_a.encode()).hexdigest()[:16]
assert sha == "5ff9daf7fe58845f", sha

tasks = [{"arm": "A", "clause": c, "draw": k}
         for c in CLAUSES for k in range(DRAWS)]
random.Random(SEED).shuffle(tasks)
for i, t in enumerate(tasks):
    t["task_id"] = "i%03d" % i
    d = os.path.join(OUT, t["task_id"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "system.txt"), "w") as fh:
        fh.write(system_a)
    with open(os.path.join(d, "user.txt"), "w") as fh:
        fh.write(read(user_path(t["clause"])))

json.dump({"seed": SEED, "draws": DRAWS, "clauses": CLAUSES,
           "system_a_sha": sha, "tasks": tasks},
          open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print("tasks:", len(tasks), "system sha", sha, "len", len(system_a))
