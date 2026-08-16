"""Build arm-B configs, assemble both system prompts, diff them, emit the task manifest.
NO NETWORK. Writes only inside _debug_gen11/prompt_ab/."""
import os, sys, json, glob, hashlib, random, copy, difflib

P1 = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P1)
os.chdir(P1)
import translate

BASE_CFG = os.path.join(P1, "resolve_runs/graph_v2/config_corpus_all.json")
RUNS = os.path.join(P1, "resolve_runs/graph_v2/translation_sample/runs")
SEED = 20260815
DRAWS = 3

D1 = ["l1108_1367_n027", "l1707_1973_n006", "l1974_2125_n019", "l1_170_n053",
      "l2405_2473_n001", "l3954_4251_n010", "l4251_4571_n029"]
D2_TARGET = ["l1108_1368_n004", "l171_426_n016", "l171_426_n041", "l1_170_n005",
             "l1_170_n022", "l1_170_n032", "l1_170_n081", "l796_1000_n034"]
D2_CONTROL = ["l1611_1798_n006", "l171_426_n020", "l427_460_n010"]


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def arm_b_config(tag):
    cfg = json.load(open(BASE_CFG))
    cfg["corpus"]["path"] = os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")
    cfg["prompt"]["system_files"] = [
        f"promptsB_{tag}/00_task.md",
        f"promptsB_{tag}/10_output_format.md",
        f"promptsB_{tag}/node_worked_example.md",
        f"promptsB_{tag}/30_failure_modes.md",
    ]
    cfg["prompt"]["unused_files"] = []
    p = os.path.join(HERE, f"config_arm_b_{tag}.json")
    json.dump(cfg, open(p, "w"), indent=1)
    return p


def find_user(cid):
    c = sorted(glob.glob(os.path.join(RUNS, "*", cid + ".prompt_user.txt")))
    if not c:
        raise SystemExit("no user prompt on disk for " + cid)
    return c[-1]


cfg_a = translate.load_config(BASE_CFG)
sys_a = translate.build_system(cfg_a)

systems = {"A": sys_a}
for tag in ("d1", "d2"):
    p = arm_b_config(tag)
    systems["B_" + tag] = translate.build_system(translate.load_config(p))

for k, v in systems.items():
    open(os.path.join(HERE, f"system_{k}.txt"), "w").write(v)

report = {}
for tag in ("d1", "d2"):
    b = systems["B_" + tag]
    d = list(difflib.unified_diff(sys_a.splitlines(True), b.splitlines(True),
                                  "system_A", f"system_B_{tag}", n=3))
    open(os.path.join(HERE, f"system_diff_{tag}.txt"), "w").writelines(d)
    added = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    report[tag] = {"sha_A": sha(sys_a), "sha_B": sha(b),
                   "chars_A": len(sys_a), "chars_B": len(b),
                   "diff_hunks": sum(1 for l in d if l.startswith("@@")),
                   "lines_added": added, "lines_removed": removed}

# ---- tasks -------------------------------------------------------------
tasks = []
def add(exp, cohort, cids, tag):
    for arm in ("A", "B"):
        for cid in cids:
            for k in range(DRAWS):
                tasks.append({"exp": exp, "cohort": cohort, "clause": cid,
                              "arm": arm, "draw": k, "sys_key": "A" if arm == "A" else "B_" + tag})

add("D1", "target", D1, "d1")
add("D2", "target", D2_TARGET, "d2")
add("D2", "control", D2_CONTROL, "d2")

rng = random.Random(SEED)
rng.shuffle(tasks)
for i, t in enumerate(tasks):
    t["task_id"] = "t%03d" % i
    up = find_user(t["clause"])
    t["user_path"] = up
    t["user_sha"] = sha(open(up, encoding="utf-8").read())[:16]

json.dump({"seed": SEED, "draws": DRAWS, "systems": report,
           "cohorts": {"D1": D1, "D2_target": D2_TARGET, "D2_control": D2_CONTROL},
           "tasks": tasks},
          open(os.path.join(HERE, "manifest.json"), "w"), indent=1)

print(json.dumps(report, indent=1))
print("tasks:", len(tasks),
      " armA:", sum(1 for t in tasks if t["arm"] == "A"),
      " armB:", sum(1 for t in tasks if t["arm"] == "B"))
