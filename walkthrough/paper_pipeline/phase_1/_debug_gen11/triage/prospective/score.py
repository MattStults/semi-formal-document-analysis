import os, sys, json, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
TRIAGE = os.path.dirname(HERE)
PAIRS = os.path.join(os.path.dirname(TRIAGE), "opus_pairs")
sys.path.insert(0, TRIAGE)
import build as B   # frozen predictor code -- imported, never retyped

rows = []
for i in range(1, 6):
    for p in sorted(glob.glob(os.path.join(PAIRS, "slice%d" % i, "spans", "*.prompt_user.txt"))):
        cid = os.path.basename(p)[: -len(".prompt_user.txt")]
        if cid.startswith("_"):
            continue
        quote = B.floor.BYID[cid]["quote"]
        narrowed, src, needs = B.span_parts(quote)
        rows.append({
            "slice": i, "clause_id": cid,
            "HEDGE": B.has_hedge(narrowed),
            "span_chars": len(B.clean(narrowed)),
            "region": re.match(r"(l\d+_\d+)", cid).group(1),
        })

hedged = [r["clause_id"] for r in rows if r["HEDGE"]]
out = {
    "n": len(rows),
    "n_hedged": len(hedged),
    "predicted_high_need": sorted(hedged),
    "rows": rows,
    "regions": {},
}
for r in rows:
    out["regions"][r["region"]] = out["regions"].get(r["region"], 0) + 1
json.dump(out, open(os.path.join(HERE, "prediction.json"), "w"), indent=1, sort_keys=True)
print(json.dumps({k: out[k] for k in ("n", "n_hedged", "regions", "predicted_high_need")}, indent=1))
