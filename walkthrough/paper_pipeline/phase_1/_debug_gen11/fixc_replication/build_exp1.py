"""Build randomised Fix-C replication task files.

Design: 10 clauses (sole attempt-1 defect = borrowed-without-gloss in the 08-14
pair) x 2 arms x 3 independent draws = 60 tasks. ONE TASK PER SUBAGENT, so arm
is orthogonal to agent identity by construction -- the confound the original
experiment could not separate. Task ids are opaque and shuffled so the dispatch
order carries no arm information.
"""
import hashlib, json, os, random

HERE = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
RUN = os.path.join(HERE, "resolve_runs/graph_v2/translation_sample/runs",
                   "20260814-173322-together-deepseek-v4-flash")
RUN2 = os.path.join(HERE, "resolve_runs/graph_v2/translation_sample/runs",
                    "20260814-163457-together-deepseek-v4-flash")
SCRATCH = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRATCH, "exp1")
os.makedirs(OUT, exist_ok=True)

SEED = 20260815
DRAWS = 3

CLAUSES = ['l1_170_n036', 'l1_170_n046', 'l1_170_n049', 'l1_170_n051',
           'l1_170_n056', 'l1_170_n071', 'l1_170_n072', 'l1_170_n075',
           'l1_170_n082', 'l1_170_n087']

# RULE G -- the added block for arm B. One paragraph, local and COUNTED.
RULE_G = """

================================================================
RULE G — THE BORROWED-NAME GLOSS IS A COUNTED, LOCAL OBLIGATION
================================================================

Every name you write in `requires` or `inputs` is a BORROWED name: this module
uses it but does not define it. Every borrowed name MUST also appear as a
`concepts` entry giving its name, its arity, and a one-sentence gloss saying
what THIS MODULE NEEDS IT TO MEAN. There are no exceptions.

Do it like this, and count:

  1. Before you write `asserts`, list the borrowed names you are going to use.
  2. Write one `concepts` entry for EACH of them, with the same name and the
     same arity.
  3. Count them. If you declare N names across `requires` + `inputs`, you must
     have written at least N `concepts` entries covering exactly those N names.
     N in, N glossed. Check the count before you emit the object.

A gloss that merely restates the name is not a gloss. Say what the module is
assuming the predicate is true of, so that a disagreement with the clause that
actually defines it can be found.
"""


def read(p):
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()


def user_path(cid):
    for d in (RUN, RUN2):
        p = os.path.join(d, cid + ".prompt_user.txt")
        if os.path.exists(p):
            return p
    raise SystemExit("no user prompt for " + cid)


system_a = read(os.path.join(RUN, "prompt_system.txt"))
system_b = system_a + RULE_G

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
    t["task_id"] = "t%03d" % i
    up = user_path(t["clause"])
    t["user_sha"] = hashlib.sha256(read(up).encode()).hexdigest()[:16]
    d = os.path.join(OUT, t["task_id"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "system.txt"), "w") as fh:
        fh.write(system_a if t["arm"] == "A" else system_b)
    with open(os.path.join(d, "user.txt"), "w") as fh:
        fh.write(read(up))

with open(os.path.join(OUT, "manifest.json"), "w") as fh:
    json.dump({"seed": SEED, "draws": DRAWS, "clauses": CLAUSES,
               "system_a_sha": hashlib.sha256(system_a.encode()).hexdigest()[:16],
               "system_b_sha": hashlib.sha256(system_b.encode()).hexdigest()[:16],
               "tasks": tasks}, fh, indent=1)
print("tasks:", len(tasks), "dir:", OUT)
print("system A sha", hashlib.sha256(system_a.encode()).hexdigest()[:16],
      "len", len(system_a))
print("system B len", len(system_b))
