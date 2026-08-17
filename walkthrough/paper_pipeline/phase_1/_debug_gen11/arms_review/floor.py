import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, P1)
G11 = os.path.join(P1, "_debug_gen11")
import translate, schema, checks

CFG = translate.load_config(os.path.join(G11,"examples_arm","config_armc.json"))
ROWS = translate.load_corpus(CFG)
IDK = CFG["corpus"]["id_key"]
IDS = {r[IDK] for r in ROWS}
BYID = {r[IDK]: r for r in ROWS}

def load(p):
    with open(p) as f: return json.load(f)

def modules_for(arm):
    d = os.path.join(G11, arm, "out"); out = {}
    if arm == "ds_opus_loop":
        for p in sorted(glob.glob(d+"/*.json")):
            b = os.path.basename(p)
            if any(k in b for k in (".raw.",".transcript.",".turn")): continue
            r = load(p); out[r["clause_id"]] = r
    elif arm == "selfreview_arm":
        for p in sorted(glob.glob(d+"/*.repair.module.json")):
            out[os.path.basename(p).split(".")[0]] = load(p)
    elif arm == "bucketed_arm":
        for cid in sorted({os.path.basename(p).split(".")[0]
                           for p in glob.glob(d+"/*.bucket*.module.json")}):
            bs = sorted(glob.glob(d+f"/{cid}.bucket*.module.json"),
                        key=lambda x: int(os.path.basename(x).split("bucket")[1].split(".")[0]))
            out[cid] = load(bs[-1])
    elif arm == "decompose_arm":
        for p in sorted(glob.glob(d+"/*.final.json")):
            r = load(p); out[os.path.basename(p).split(".")[0]] = r.get("module", r)
    else:
        for p in sorted(glob.glob(d+"/*.json")):
            b = os.path.basename(p)
            if ".raw." in b or ".adjudication" in b: continue
            r = load(p)
            if r.get("module"): out[r.get("clause_id") or b.split(".")[0]] = r["module"]
    return out

def floor(obj, cid):
    row = BYID[cid]
    res = {"breaches": [], "outcome": None, "repair": None, "errors": [], "notes": []}
    _m, br = schema.validate_all(obj, cid, IDS)
    res["breaches"] = [str(b) for b in br]
    r = checks.run_checks(obj, row, IDS)
    res["outcome"] = r.outcome
    res["repair"] = bool(r.repair_needed)
    for f in r.findings:
        (res["errors"] if f.severity=="error" else res["notes"]).append(
            f"{f.check_id}|{f.where}|{f.message}")
    res["polarity"] = len(checks.polarity_mismatches(obj))
    res["arity"] = len(checks.arity_mismatches(obj))
    return res
