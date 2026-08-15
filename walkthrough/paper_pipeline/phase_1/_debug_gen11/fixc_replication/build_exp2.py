"""Build the randomised worked-example (DC-1 discoverability) experiment.

Cohort: the 17 clauses of the 08-14 pair whose attempt-1 repair message was
`undeclared-body-name` and nothing else.  17 clauses x 2 arms x 2 draws = 68
tasks, one isolated Haiku subagent each.

Arm A = the byte-identical stored gen-11 system prompt.
Arm B = the same prompt with the embedded `node_worked_example.md` text replaced
        by the EDITED version (the glossary / body-less-ground-atom example).
Nothing else differs -- the two prompts are identical outside that block.
"""
import hashlib, json, os, random

HERE = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
RUNS = [os.path.join(HERE, "resolve_runs/graph_v2/translation_sample/runs", d)
        for d in ("20260814-173322-together-deepseek-v4-flash",
                  "20260814-163457-together-deepseek-v4-flash")]
SCRATCH = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRATCH, "exp2")
os.makedirs(OUT, exist_ok=True)

SEED = 20260815 + 2
DRAWS = 2
CLAUSES = ['l171_426_n001', 'l1_170_n014', 'l1_170_n016', 'l1_170_n019',
           'l1_170_n023', 'l1_170_n032', 'l1_170_n045', 'l1_170_n050',
           'l1_170_n053', 'l1_170_n057', 'l1_170_n058', 'l1_170_n062',
           'l1_170_n065', 'l1_170_n067', 'l1_170_n078', 'l1_170_n084',
           'l1_170_n086']

OLD_WE = os.path.join(SCRATCH, "old_worked_example.md")
NEW_WE = os.path.join(SCRATCH, "new_worked_example.md")


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
old_we, new_we = read(OLD_WE), read(NEW_WE)
assert old_we in system_a, "stored system prompt does not embed the old worked example"
system_b = system_a.replace(old_we, new_we)
assert system_b != system_a

with open(os.path.join(OUT, "system_A.txt"), "w") as fh:
    fh.write(system_a)
with open(os.path.join(OUT, "system_B.txt"), "w") as fh:
    fh.write(system_b)

tasks = []
for arm in ("A", "B"):
    for cid in CLAUSES:
        for k in range(DRAWS):
            tasks.append({"arm": arm, "clause": cid, "draw": k})

rng = random.Random(SEED)
rng.shuffle(tasks)
for i, t in enumerate(tasks):
    t["task_id"] = "u%03d" % i
    d = os.path.join(OUT, t["task_id"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "system.txt"), "w") as fh:
        fh.write(system_a if t["arm"] == "A" else system_b)
    with open(os.path.join(d, "user.txt"), "w") as fh:
        fh.write(read(user_path(t["clause"])))

json.dump({"seed": SEED, "draws": DRAWS, "clauses": CLAUSES,
           "system_a_sha": hashlib.sha256(system_a.encode()).hexdigest()[:16],
           "system_b_sha": hashlib.sha256(system_b.encode()).hexdigest()[:16],
           "tasks": tasks},
          open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print("tasks:", len(tasks))
print("A len", len(system_a), "sha", hashlib.sha256(system_a.encode()).hexdigest()[:16])
print("B len", len(system_b), "sha", hashlib.sha256(system_b.encode()).hexdigest()[:16])
