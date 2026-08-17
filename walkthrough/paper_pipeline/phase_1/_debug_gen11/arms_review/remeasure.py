"""Common mechanical re-measure of every stored module across the 8 arms.
READ-ONLY on arm dirs. Writes nothing outside arms_review/."""
import json, os, sys, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, P1)
G11 = os.path.join(P1, "_debug_gen11")

def load(p):
    with open(p) as f: return json.load(f)

def modules_for(arm):
    """-> {clause_id: module dict}  (the arm's FINAL module for that clause)"""
    d = os.path.join(G11, arm, "out")
    out = {}
    if arm == "ds_opus_loop":
        for p in sorted(glob.glob(d+"/*.json")):
            b = os.path.basename(p)
            if ".raw." in b or ".transcript." in b or ".turn" in b: continue
            r = load(p); out[r.get("clause_id") or b[:-5]] = r.get("module")
    elif arm == "selfreview_arm":
        for p in sorted(glob.glob(d+"/*.repair.module.json")):
            cid = os.path.basename(p).split(".")[0]
            out[cid] = load(p)
    elif arm == "bucketed_arm":
        for cid in sorted({os.path.basename(p).split(".")[0]
                           for p in glob.glob(d+"/*.bucket*.module.json")}):
            bs = sorted(glob.glob(d+f"/{cid}.bucket*.module.json"))
            out[cid] = load(bs[-1])          # last bucket = final module
    elif arm == "decompose_arm":
        for p in sorted(glob.glob(d+"/*.final.json")):
            cid = os.path.basename(p).split(".")[0]
            r = load(p); out[cid] = r.get("module", r)
    else:
        for p in sorted(glob.glob(d+"/*.json")):
            b = os.path.basename(p)
            if ".raw." in b or ".adjudication" in b: continue
            r = load(p); out[r.get("clause_id") or b[:-5]] = r.get("module")
    return out

def stored_floor(arm):
    d = os.path.join(G11, arm, "out"); out = {}
    for p in sorted(glob.glob(d+"/*.json")):
        b = os.path.basename(p)
        if ".raw." in b or ".transcript." in b or ".turn" in b: continue
        try: r = load(p)
        except Exception: continue
        if isinstance(r, dict) and "floor" in r:
            out.setdefault(r.get("clause_id") or b.split(".")[0], []).append(r["floor"])
    return out

ARMS = ["ds_opus_loop","list_in_prompt","list_in_prompt_insample","examples_arm",
        "retrieval_arm","selfreview_arm","forced_verdict_arm","bucketed_arm",
        "decompose_arm"]

if __name__ == "__main__":
    import checks, schema, fixtures
    rows = None
    try:
        rows = fixtures.load_rows() if hasattr(fixtures,"load_rows") else None
    except Exception as e:
        print("fixtures:", e)
    for a in ARMS:
        m = modules_for(a)
        print(f"{a:26s} n_modules={len(m):3d}  none={sum(1 for v in m.values() if v is None)}")
