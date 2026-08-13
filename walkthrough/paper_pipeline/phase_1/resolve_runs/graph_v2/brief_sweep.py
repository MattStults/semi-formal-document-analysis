#!/usr/bin/env python3
"""Hypothesis-driven seat-brief sweep (Matt 2026-08-13): variants come from
the FAILING cases' own grounds (all five borderline rejections state
'A is the rule, B is the level'), not from guesswork. Scores each brief on
a golden-derived labeled set; keeps nothing that raises false accepts."""
import json, os, sys, subprocess, tempfile, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, "../../../../../semi-formal-experiment"))
import providers, rename_seat as RS, recurse_driver as R

key = os.environ.get("TOGETHER_API_KEY") or providers._parse_shell_export(
    "~/.zshrc", "TOGETHER_API_KEY")
lines = R.load_doc(os.path.join(HERE, "../../../../../specs/openai-model-spec/model_spec.md"))

H1 = """

The document often describes ONE named concept from different facets: a
rule and the authority level it carries, a mechanism and its product, a
principle and the section that houses it. Descriptions capturing different
facets of the SAME referent are still the same concept. The test is not
"do these descriptions describe the same kind of entity?" but "do the two
passages engage the same named thing in the document -- the same tier of
the hierarchy, the same section's rule, the same defined object?\""""
H2 = """

The two descriptions were written independently by different annotators
who each saw only their own passage. Their WORDING will differ even when
the referent is identical -- weigh the passages' quoted text above the
description phrasing."""

BRIEFS = {"baseline": RS.BRIEF,
          "H1_referent": RS.BRIEF + H1,
          "H1H2_referent_text": RS.BRIEF + H1 + H2}

def judge(brief, prompt):
    body = {"model": "deepseek-ai/DeepSeek-V4-Flash-0731", "max_tokens": 1024,
            "temperature": 0.0,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "verdict", "schema": RS.SCHEMA[1], "strict": True}},
            "messages": [{"role": "system", "content": brief},
                         {"role": "user", "content": prompt}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(body, tf); name = tf.name
    p = subprocess.run(["curl", "-sS",
                        "https://api.together.xyz/v1/chat/completions",
                        "-H", "Authorization: Bearer " + key,
                        "-H", "Content-Type: application/json",
                        "--data-binary", "@" + name],
                       capture_output=True, text=True, timeout=300)
    os.unlink(name)
    try:
        return json.loads(json.loads(p.stdout)["choices"][0]["message"]
                          ["content"])["verdict"]
    except Exception:
        return "error"

def build_set():
    g = json.load(open(os.path.join(HERE, "recurse/root/graph.json")))
    by_id = {n["id"]: n for n in g["nodes"]}
    pnode, pprose = {}, {}
    for n in g["nodes"]:
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("prose"):
                pnode.setdefault(p["name"], n); pprose.setdefault(p["name"], p["prose"])
    pos, seen = [], set()
    for n in g["nodes"]:
        for d in n.get("needs", []):
            if (isinstance(d, dict) and d.get("prose") and d.get("name") in pprose
                    and d["name"] not in seen
                    and d["prose"].strip().lower() != pprose[d["name"]].strip().lower()):
                seen.add(d["name"])
                pos.append(("POS", d["prose"], n, pprose[d["name"]], pnode[d["name"]]))
    # hard negatives: DIFFERENT names, embedding-adjacent prose (reuse the
    # ds4 known-bads style: pair each need with a WRONG same-topic provider)
    neg = []
    names = sorted(pprose)
    for i, (lab, np_, nn, pp, pn) in enumerate(pos[:40]):
        # wrong candidate: the lexically-nearest OTHER name's provider
        def jac(a, b):
            ta = set(re.findall(r"[a-z]{4,}", a.lower())); tb = set(re.findall(r"[a-z]{4,}", b.lower()))
            return len(ta & tb) / max(len(ta | tb), 1)
        true_name = [k for k in pprose if pprose[k] == pp][0]
        alt = max((k for k in names if k != true_name),
                  key=lambda k: jac(np_, pprose[k]))
        neg.append(("NEG", np_, nn, pprose[alt], pnode[alt]))
    return pos[:40] + neg

def main():
    ds = build_set()
    print(f"labeled set: {sum(1 for x in ds if x[0]=='POS')} pos / "
          f"{sum(1 for x in ds if x[0]=='NEG')} neg")
    results = {}
    for bname, brief in BRIEFS.items():
        tp = fn = fp = tn = err = 0
        rows = []
        for lab, np_, nn, pp, pn in ds:
            v = judge(brief, RS.build_prompt(np_, nn, pp, pn, lines))
            if v == "error": err += 1
            elif lab == "POS":
                tp, fn = tp + (v == "same_concept"), fn + (v != "same_concept")
            else:
                fp, tn = fp + (v == "same_concept"), tn + (v != "same_concept")
            rows.append({"label": lab, "verdict": v, "need": np_[:60]})
        sens = tp / max(tp + fn, 1); fa = fp / max(fp + tn, 1)
        results[bname] = {"sensitivity": round(sens, 3),
                          "false_accept": round(fa, 3),
                          "tp": tp, "fn": fn, "fp": fp, "tn": tn,
                          "errors": err, "rows": rows}
        print(f"{bname:24s} sensitivity={sens:.2f}  false_accept={fa:.2f}  "
              f"(tp{tp} fn{fn} fp{fp} tn{tn} err{err})")
    json.dump(results, open(os.path.join(HERE, "brief_sweep_results.json"),
                            "w"), indent=1)

if __name__ == "__main__":
    main()
