#!/usr/bin/env python3
"""Matt's canonicalization probe (2026-08-13): rewrite every concept
description into a fixed referent card, embed the CARDS, and measure
recall@N on golden ground truth against the 82%@10 raw-prose baseline.
Rewrites are cached to disk (canon_cache.json) -- resumable, rerun-free."""
import json, os, sys, subprocess, tempfile, math, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, "../../../../../semi-formal-experiment"))
import providers

key = os.environ.get("TOGETHER_API_KEY") or providers._parse_shell_export(
    "~/.zshrc", "TOGETHER_API_KEY")

CARD_SCHEMA = {"type": "object", "properties": {
    "referent": {"type": "string"},
    "kind": {"type": "string", "enum": [
        "rule", "authority_level", "category", "mechanism", "principle",
        "section", "process", "entity", "property", "other"]},
    "governs": {"type": "string"}},
    "required": ["referent", "kind", "governs"]}

CANON_BRIEF = """You normalize one concept description from a policy
document into a referent card. REFERENT: the named thing itself, in 3-8
words, stripped of facet framing (if the description is 'the authority
level of user sections', the referent is 'user-level instructions/authority
tier'; if it is 'an instruction from end users...', the referent is the
same tier). KIND: what facet the description takes. GOVERNS: what the
referent applies to, 3-10 words. Reply with the JSON object only."""

_cache = {}
CPATH = os.path.join(HERE, "canon_cache.json")
if os.path.exists(CPATH):
    _cache = json.load(open(CPATH))

def canon(text):
    k = hashlib.sha256(text.encode()).hexdigest()[:24]
    if k in _cache:
        return _cache[k]
    body = {"model": "deepseek-ai/DeepSeek-V4-Flash-0731", "max_tokens": 512,
            "temperature": 0.0,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "card", "schema": CARD_SCHEMA, "strict": True}},
            "messages": [{"role": "system", "content": CANON_BRIEF},
                         {"role": "user", "content": text}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(body, tf); name = tf.name
    p = subprocess.run(["curl", "-sS",
                        "https://api.together.xyz/v1/chat/completions",
                        "-H", "Authorization: Bearer " + key,
                        "-H", "Content-Type: application/json",
                        "--data-binary", "@" + name],
                       capture_output=True, text=True, timeout=180)
    os.unlink(name)
    try:
        c = json.loads(json.loads(p.stdout)["choices"][0]["message"]["content"])
        card = f"REFERENT: {c['referent']} | KIND: {c['kind']} | GOVERNS: {c['governs']}"
    except Exception:
        card = text          # fail-open to raw text, recorded
    _cache[k] = card
    json.dump(_cache, open(CPATH, "w"))
    return card

def embed(texts):
    out = []
    for i in range(0, len(texts), 64):
        body = json.dumps({"model": "intfloat/multilingual-e5-large-instruct",
                           "input": texts[i:i+64]}).encode()
        with tempfile.NamedTemporaryFile("wb", suffix=".json",
                                         delete=False) as tf:
            tf.write(body); name = tf.name
        p = subprocess.run(["curl", "-sS",
                            "https://api.together.xyz/v1/embeddings",
                            "-H", "Authorization: Bearer " + key,
                            "-H", "Content-Type: application/json",
                            "--data-binary", "@" + name],
                           capture_output=True, text=True, timeout=180)
        os.unlink(name)
        r = json.loads(p.stdout)
        out += [d["embedding"] for d in r["data"]]
    return out

def cos(a, b):
    d = sum(x*y for x, y in zip(a, b))
    return d / (math.sqrt(sum(x*x for x in a)) *
                math.sqrt(sum(x*x for x in b)) + 1e-9)

def main():
    g = json.load(open(os.path.join(HERE, "recurse/root/graph.json")))
    prov = {}
    for n in g["nodes"]:
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("prose"):
                prov.setdefault(p["name"], p["prose"] + " || "
                                + n.get("establishes", ""))
    cands = sorted(prov)
    queries = []
    for n in g["nodes"]:
        for d in n.get("needs", []):
            if (isinstance(d, dict) and d.get("prose") and d.get("name") in prov
                    and d["prose"].strip().lower()
                    not in prov[d["name"]].strip().lower()):
                queries.append((d["prose"] + " || " + n.get("establishes", ""),
                                d["name"]))
    queries = sorted(set(queries))
    print(f"{len(queries)} queries, {len(cands)} candidates; canonicalizing "
          f"{len(cands) + len(queries)} texts...")
    ccards = [canon(prov[c]) for c in cands]
    qcards = [canon(q) for q, _ in queries]
    cvecs, qvecs = embed(ccards), embed(qcards)
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    for (qt, ans), qv in zip(queries, qvecs):
        ranked = [c for _, c in sorted(
            ((-cos(qv, cv), c) for cv, c in zip(cvecs, cands)))]
        pos = ranked.index(ans)
        for k in hits:
            hits[k] += pos < k
    print("CANONICAL-CARD embedding recall@N:",
          {k: f"{v}/{len(queries)}" for k, v in hits.items()})
    print("(raw enriched-prose baseline was @1 55, @3 90, @5 99, @10 114 "
          "of 139)")

if __name__ == "__main__":
    main()
