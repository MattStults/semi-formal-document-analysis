import glob, json, os, collections
P1="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
bad=[]; pats=collections.Counter(); marker=0
for pat in ("runs/*/run.json","resolve_runs/graph_v2/translation_sample/runs/*/run.json"):
    for rj in sorted(glob.glob(os.path.join(P1,pat))):
        root=os.path.dirname(rj); d=json.load(open(rj))
        for res in d.get("results",[]):
            tp=os.path.join(root,res["clause_id"]+".transcript.json")
            if not os.path.exists(tp): continue
            t=json.load(open(tp))
            roles="".join("U" if m["role"]=="user" else ("A" if m["role"]=="assistant" else "?") for m in t)
            pats[roles]+=1
            if any("DISCARDED" in (m.get("content") or "") for m in t): marker+=1
            exp="UA"*(res.get("attempts") or 0)
            if roles!=exp: bad.append((os.path.basename(root),res["clause_id"],roles,res.get("attempts"),res.get("status")))
print("role patterns:",dict(pats))
print("transcripts containing a restart marker:",marker)
print("roles != (UA)*attempts :",len(bad))
for b in bad[:20]: print("  ",b)
