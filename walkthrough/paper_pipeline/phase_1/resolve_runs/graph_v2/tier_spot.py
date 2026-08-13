#!/usr/bin/env python3
"""Seat-tier spot check (Matt 2026-08-13): K3 vs cheaper Kimi vs
DeepSeek-Pro vs the Flash baseline, same adopted brief, same golden-
labeled pairs -- so next campaign's frontier-tier choice is a measurement.
Serial with disk cache (resumable); ~$1.2 total."""
import json, os, sys, subprocess, tempfile, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, "../../../../../semi-formal-experiment"))
import providers, rename_seat as RS
import brief_sweep as B

key = os.environ.get("TOGETHER_API_KEY") or providers._parse_shell_export(
    "~/.zshrc", "TOGETHER_API_KEY")
MODELS = ["moonshotai/Kimi-K3", "moonshotai/Kimi-K2.5-fp4",
          "deepseek-ai/DeepSeek-V4-Pro",
          "deepseek-ai/DeepSeek-V4-Flash-0731"]
BRIEF = B.BRIEFS["H1H2_referent_text"]         # the adopted brief
cachep = os.path.join(HERE, "tier_spot_cache.json")
cache = json.load(open(cachep)) if os.path.exists(cachep) else {}

def judge(model, prompt):
    k = hashlib.sha256((model + "\x00" + prompt).encode()).hexdigest()[:24]
    if k in cache:
        return cache[k]
    body = {"model": model, "max_tokens": 2048, "temperature": 0.0,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "verdict", "schema": RS.SCHEMA[1], "strict": True}},
            "messages": [{"role": "system", "content": BRIEF},
                         {"role": "user", "content": prompt}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json",
                                     delete=False) as tf:
        json.dump(body, tf); name = tf.name
    try:
        p = subprocess.run(
            ["curl", "-sS", "https://api.together.xyz/v1/chat/completions",
             "-H", "Authorization: Bearer " + key,
             "-H", "Content-Type: application/json",
             "--data-binary", "@" + name],
            capture_output=True, text=True, timeout=300)
    finally:
        os.unlink(name)
    try:
        r = json.loads(p.stdout)
        v = json.loads(r["choices"][0]["message"]["content"])["verdict"]
        u = r.get("usage", {})
        out = {"verdict": v, "pt": u.get("prompt_tokens"),
               "ct": u.get("completion_tokens")}
    except Exception as exc:
        out = {"verdict": "error", "err": repr(exc)[:80],
               "raw": p.stdout[:120]}
    cache[k] = out
    json.dump(cache, open(cachep, "w"))
    return out

def main():
    ds = B.build_set()
    pos = [x for x in ds if x[0] == "POS"][:20]
    neg = [x for x in ds if x[0] == "NEG"][:20]
    sample = pos + neg
    import recurse_driver as R
    lines = R.load_doc(os.path.join(
        HERE, "../../../../../specs/openai-model-spec/model_spec.md"))
    results = {}
    for model in MODELS:
        tp = fn = fp = tn = err = 0
        toks = 0
        for lab, np_, nn, pp, pn in sample:
            v = judge(model, RS.build_prompt(np_, nn, pp, pn, lines))
            toks += (v.get("ct") or 0)
            if v["verdict"] == "error":
                err += 1
            elif lab == "POS":
                tp, fn = tp + (v["verdict"] == "same_concept"), \
                         fn + (v["verdict"] != "same_concept")
            else:
                fp, tn = fp + (v["verdict"] == "same_concept"), \
                         tn + (v["verdict"] != "same_concept")
        sens = tp / max(tp + fn, 1); fa = fp / max(fp + tn, 1)
        results[model] = {"sensitivity": round(sens, 3),
                          "false_accept": round(fa, 3),
                          "tp": tp, "fn": fn, "fp": fp, "tn": tn,
                          "errors": err, "out_tokens": toks}
        print(f"{model:38s} sens={sens:.2f} FA={fa:.2f} "
              f"(tp{tp} fn{fn} fp{fp} tn{tn} err{err}) out_toks={toks}")
    json.dump(results, open(os.path.join(HERE, "tier_spot_results.json"),
                            "w"), indent=1)

if __name__ == "__main__":
    main()
