"""INDEPENDENT re-derivation. No import of translate.py. sha1 recomputed here."""
import glob, json, os, hashlib, collections, sys

P1 = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
GLOBS = ("runs/*/run.json",
         "resolve_runs/graph_v2/translation_sample/runs/*/run.json")

def h(t): return hashlib.sha1((t or "").encode("utf-8")).hexdigest()

def load(exclude_runs=()):
    rows = []
    for pat in GLOBS:
        for rj in sorted(glob.glob(os.path.join(P1, pat))):
            root = os.path.dirname(rj); run = os.path.basename(root)
            if run in exclude_runs: continue
            corpus = "sample" if "/translation_sample/" in rj else "runs"
            d = json.load(open(rj, encoding="utf-8"))
            for res in d.get("results", []):
                cid = res.get("clause_id")
                tp = os.path.join(root, cid + ".transcript.json")
                row = dict(run=run, corpus=corpus, clause=cid,
                           status=res.get("status"), attempts=res.get("attempts"),
                           per_attempt=res.get("per_attempt"),
                           cost=res.get("cost_usd"), tin=res.get("tokens_in"),
                           tout=res.get("tokens_out"), replies=None, roles=None)
                if os.path.exists(tp):
                    turns = json.load(open(tp, encoding="utf-8"))
                    row["replies"] = [m["content"] for m in turns if m.get("role")=="assistant"]
                    row["roles"] = [m.get("role") for m in turns]
                rows.append(row)
    return rows

def fire(replies):
    """First attempt index (1-based) whose reply repeats an earlier one."""
    if not replies: return None, []
    seen = {h(replies[0])}; fires = []
    for i, r in enumerate(replies[1:], start=2):
        k = h(r)
        if k in seen: fires.append(i)
        else: seen.add(k)
    return (fires[0] if fires else None), fires

def report(rows, label):
    usable = [r for r in rows if r["replies"] is not None]
    notr = [r for r in rows if r["replies"] is None]
    trunc = [r for r in usable if r["attempts"] and len(r["replies"]) < r["attempts"]]
    over = [r for r in usable if r["attempts"] and len(r["replies"]) > r["attempts"]]
    for r in usable:
        r["fire_at"], r["fires"] = fire(r["replies"])
        r["n"] = len(r["replies"])
    multi = [r for r in usable if r["n"] > 1]
    fired = [r for r in multi if r["fire_at"]]
    ok = lambda r: r["status"] == "translated"
    print(f"### {label}")
    print(f"  stored results {len(rows)}  with transcript {len(usable)}  none {len(notr)}")
    print(f"  truncated(replies<attempts) {len(trunc)}   replies>attempts {len(over)}")
    print(f"  multi-attempt {len(multi)}  fired {len(fired)} = {100*len(fired)/max(1,len(multi)):.1f}%"
          f"   of all usable {100*len(fired)/max(1,len(usable)):.1f}%")
    print(f"  fired & translated: {len([r for r in fired if ok(r)])} -> "
          f"{[ (r['clause'],r['run'][:13]) for r in fired if ok(r)]}")
    print(f"  predictor: fired n={len(fired)} translated {len([r for r in fired if ok(r)])}"
          f" ({100*len([r for r in fired if ok(r)])/max(1,len(fired)):.0f}%) |"
          f" distinct n={len(multi)-len(fired)} translated"
          f" {len([r for r in multi if not r['fire_at'] and ok(r)])}"
          f" ({100*len([r for r in multi if not r['fire_at'] and ok(r)])/max(1,len(multi)-len(fired)):.0f}%)")
    print(f"  refreeze proxy (>=2 fires): {len([r for r in fired if len(r['fires'])>1])}")
    print(f"  status hist multi: {dict(collections.Counter(r['status'] for r in multi))}")
    return usable, multi, fired

if __name__ == "__main__":
    rows = load()
    report(rows, "ALL RUNS ON DISK (2026-08-15 now)")
    print()
    rows2 = load(exclude_runs=("20260815-113545-together-deepseek-v4-flash",))
    report(rows2, "EXCLUDING the 11:35 run (post-dates the preflight at 11:25)")
