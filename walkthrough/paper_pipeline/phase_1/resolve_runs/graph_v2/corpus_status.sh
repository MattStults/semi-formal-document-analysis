#!/bin/bash
# Full-corpus translation status
D="$(cd "$(dirname "$0")" && pwd)"
P=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python
pgrep -f "translate_exec.py --config.*config_corpus_all" >/dev/null && echo "corpus run: RUNNING" || echo "corpus run: NOT RUNNING"
$P - <<EOF
import json, os, glob, sys
sys.path.insert(0, "$D/../..")
import graveyard as gy
done = set()
for d in glob.glob("$D/translation_sample/runs/*/"):
    for lp in glob.glob(d + "*.lp"):
        done.add(os.path.basename(lp)[:-3])
total = len(json.load(open("$D/node_corpus_all.json"))["clauses"])
print(f"translated: {len(done)}/{total}")
op = gy.open_entries("$D/translation_sample/repair_graveyard")
cap = json.load(open("$D/config_corpus_all.json"))["graveyard"]["cap"]
print(f"graveyard OPEN: {len(op)} / cap {cap}" + ("  <-- next slice will REFUSE until diagnosed" if len(op) >= cap else "  (gen-12 gate, not a mid-run stop)"))
t = sum((json.loads(l).get("cost_usd") or 0) for l in open("/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/usage.jsonl") if l.strip())
print(f"campaign spend: \${t:.2f} / \$20")
EOF
tail -3 "$D/runs/corpus_translation_log.txt" | cut -c1-150
