#!/usr/bin/env python3
"""Modal-fidelity experiment (Matt's #5 ruling, 2026-08-13): the sweep's
31 ds6 flags are MECHANICAL (modal-tier counting) -- adjudicate each one:
does the node's claim state the passage's obligations at the strength the
passage states them? Verdicts + grounds recorded; a sample gets frontier
review. Decides whether modal drift is real (prompt lever before ds7) or
sweep noise (flags stay telemetry)."""
import json, os, sys, subprocess, tempfile, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, "../../../../../semi-formal-experiment"))
import providers, recurse_driver as R

key = os.environ.get("TOGETHER_API_KEY") or providers._parse_shell_export(
    "~/.zshrc", "TOGETHER_API_KEY")
BRIEF = """You compare ONE claim against the passage it summarizes, on a
single dimension: OBLIGATION STRENGTH. The passage may use strong modals
(must, never, always, required), medium (should, generally), or weak
(may, can, might, encouraged). Judge whether the claim preserves the
strength of the obligations it restates: does anything the passage makes
mandatory become optional-sounding in the claim, or vice versa? Ignore
completeness and wording -- ONLY strength. When the claim simply omits a
differently-tiered clause of the passage without changing the strength of
what it DOES restate, that is preserved, not drifted.
Reply ONE JSON object: {"verdict": "preserved" | "drifted",
"grounds": "one sentence citing the decisive modal words"}"""
SCHEMA = {"type": "object", "properties": {
    "verdict": {"type": "string", "enum": ["preserved", "drifted"]},
    "grounds": {"type": "string"}}, "required": ["verdict", "grounds"]}

cachep = os.path.join(HERE, "modal_adj_cache.json")
cache = json.load(open(cachep)) if os.path.exists(cachep) else {}

def judge(prompt):
    k = hashlib.sha256(prompt.encode()).hexdigest()[:24]
    if k in cache:
        return cache[k]
    body = {"model": "deepseek-ai/DeepSeek-V4-Flash-0731", "max_tokens": 1024,
            "temperature": 0.0,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "verdict", "schema": SCHEMA, "strict": True}},
            "messages": [{"role": "system", "content": BRIEF},
                         {"role": "user", "content": prompt}]}
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
        v = json.loads(json.loads(p.stdout)["choices"][0]["message"]["content"])
    except Exception as exc:
        v = {"verdict": "error", "grounds": repr(exc)[:100]}
    cache[k] = v
    json.dump(cache, open(cachep, "w"))
    return v

def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "runs/ds6"
    lines = R.load_doc(os.path.join(
        HERE, "../../../../../specs/openai-model-spec/model_spec.md"))
    g = json.load(open(os.path.join(HERE, run, "root_graph.json")))
    by_id = {n["id"]: n for n in g["nodes"]}
    rep = json.load(open(os.path.join(HERE, run,
                                      "sweep_modals_report.json")))
    rows = rep[[k for k in rep if k not in ("total_nodes", "flagged")][0]]
    out = []
    for r in rows:
        n = by_id.get(r["id"])
        span = "\n---\n".join(
            "\n".join(lines[s["lines"][0]-1:s["lines"][1]])
            for s in (n or {}).get("spans", []))[:3000]
        prompt = (f"THE PASSAGE:\n{span}\n\nTHE CLAIM:\n"
                  f"{r['establishes']}\n\nDoes the claim preserve the "
                  f"passage's obligation strength? JSON only.")
        v = judge(prompt)
        out.append({"id": r["id"], "flags": r["flags"],
                    "verdict": v["verdict"], "grounds": v["grounds"],
                    "establishes": r["establishes"][:160]})
        print(f"{r['id']:20s} {r['flags'][0]['kind']:12s} -> {v['verdict']}")
    json.dump(out, open(os.path.join(HERE, run, "modal_adjudication.json"),
                        "w"), indent=1)   # run-local: risk_queue reads it
    d = sum(1 for x in out if x["verdict"] == "drifted")
    print(f"\n{d}/{len(out)} flags adjudicated as REAL drift")

if __name__ == "__main__":
    main()
