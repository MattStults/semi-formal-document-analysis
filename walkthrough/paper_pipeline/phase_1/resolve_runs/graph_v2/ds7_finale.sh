#!/bin/bash
set -e
cd /Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2
echo "=== STAGE 1: frontier review (K3, batched, parity-gated) ==="
/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python frontier_review.py runs/ds7 --yes
echo "=== STAGE 2: fixup round ==="
/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python fixup.py runs/ds7
echo "=== STAGE 3: quality battery vs golden ==="
/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python -c "
import sys; sys.path.insert(0, '.')
import recurse_driver as R
R.post_build_checks('runs/ds7', golden='recurse/root/graph.json',
                    doc_path='../../../../../specs/openai-model-spec/model_spec.md')
"
echo "=== FINALE COMPLETE ==="
