#!/usr/bin/env python3
"""Matt's question 2026-08-12: is SEMANTIC embedding cosine sufficient to
put the true provider in the top-N candidates for each need? Ground truth:
the graph's own resolved edges (need prose -> provider prose under one
name). Reports recall@1/3/5/10 vs the lexical-Jaccard baseline."""
import json, os, sys, urllib.request, math, re

def _key():
    if os.environ.get("TOGETHER_API_KEY"):
        return os.environ["TOGETHER_API_KEY"]
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "..", "..", "..", "semi-formal-experiment"))
    import providers
    return providers._parse_shell_export("~/.zshrc", "TOGETHER_API_KEY")

MODEL = "intfloat/multilingual-e5-large-instruct"
def embed(texts):
    out = []
    for i in range(0, len(texts), 64):
        body = json.dumps({"model": MODEL, "input": texts[i:i+64]}).encode()
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile("wb", suffix=".json",
                                         delete=False) as tf:
            tf.write(body)
        p = subprocess.run(
            ["curl", "-sS", "https://api.together.xyz/v1/embeddings",
             "-H", "Authorization: Bearer " + _key(),
             "-H", "Content-Type: application/json",
             "--data-binary", "@" + tf.name], capture_output=True, text=True,
            timeout=180)
        os.unlink(tf.name)
        r = json.loads(p.stdout)
        if "data" not in r:
            raise RuntimeError(str(r)[:300])
        out += [d["embedding"] for d in r["data"]]
    return out

def cos(a, b):
    d = sum(x*y for x, y in zip(a, b))
    return d / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(x*x for x in b)) + 1e-9)

def jac(a, b):
    ta = set(re.findall(r"[a-z]{4,}", a.lower())); tb = set(re.findall(r"[a-z]{4,}", b.lower()))
    return len(ta & tb) / max(len(ta | tb), 1)

def run(path):
    g = json.load(open(path))
    prov = {}
    for n in g["nodes"]:
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("prose"):
                prov.setdefault(p["name"], p["prose"])
    cands = sorted(prov)
    queries = []
    for n in g["nodes"]:
        for d in n.get("needs", []):
            if (isinstance(d, dict) and d.get("prose") and d.get("name") in prov
                    and d["prose"].strip().lower() != prov[d["name"]].strip().lower()):
                queries.append((d["prose"], d["name"]))
    # dedupe identical (prose, answer) pairs
    queries = sorted(set(queries))
    texts = [prov[c] for c in cands] + [q for q, _ in queries]
    vecs = embed(texts)
    cvecs, qvecs = vecs[:len(cands)], vecs[len(cands):]
    def recall(rank_fn):
        hits = {1: 0, 3: 0, 5: 0, 10: 0}
        for (qp, ans), qv in zip(queries, qvecs):
            ranked = rank_fn(qp, qv)
            pos = ranked.index(ans) if ans in ranked else 10**9
            for k in hits:
                hits[k] += pos < k
        return {k: f"{v}/{len(queries)}" for k, v in hits.items()}
    emb = recall(lambda qp, qv: [c for _, c in sorted(
        ((-cos(qv, cv), c) for cv, c in zip(cvecs, cands)))])
    lex = recall(lambda qp, qv: [c for _, c in sorted(
        ((-jac(qp, prov[c]), c) for c in cands))])
    print(f"{path}: {len(queries)} unique (need-prose -> true provider) pairs, {len(cands)} candidates")
    print(f"  embedding cosine recall@N: {emb}")
    print(f"  lexical Jaccard  recall@N: {lex}")

for p in sys.argv[1:] or ["recurse/root/graph.json", "runs/ds5/root_graph.json"]:
    run(p)
