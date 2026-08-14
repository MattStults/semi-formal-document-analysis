#!/bin/bash
set -e
cd "$(dirname "$0")"
P=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python
echo "=== STAGE 1: promise repair (opus_verdicts scope, \$0.40 gate) ==="
$P promise_repair.py runs/ds7 --yes
echo "=== STAGE 2: quality battery on the repaired graph ==="
$P graph_compare.py --a recurse/root/graph.json --b runs/ds7/root_graph.repaired.json \
   --doc ../../../../../specs/openai-model-spec/model_spec.md \
   --out runs/ds7/compare_repaired_vs_golden.json
$P - <<'EOF'
import json, sys
sys.path.insert(0, '.')
import risk_queue as RQ
for tag, path in (("ds7 original", "runs/ds7/root_graph.json"),
                  ("ds7 REPAIRED", "runs/ds7/root_graph.repaired.json")):
    g = json.load(open(path))
    provs, prose = set(), {}
    for n in g["nodes"]:
        for p in n.get("provides", []):
            nm = p.get("name") if isinstance(p, dict) else p
            provs.add(nm)
            if isinstance(p, dict): prose.setdefault(nm, p.get("prose",""))
    needs = [(n["id"], d) for n in g["nodes"] for d in n.get("needs", []) if isinstance(d, dict)]
    dang = [x for x in needs if x[1]["name"] not in provs]
    lo = sum(1 for _i, d in needs if d["name"] in provs
             and RQ.sim(d.get("prose",""), prose.get(d["name"],"")) < 0.1)
    print(f"{tag}: {len(g['nodes'])} nodes | {len(provs)} exported names | "
          f"{len(needs)} need-edges | {len(dang)} dangling | {lo} mismatched(<0.1)")
EOF
echo "=== REPAIR COMPLETE ==="
