import sys, os, io, contextlib, json
HERE="/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, HERE)
import translate as T
cfg = T.load_config(os.path.join(HERE,"resolve_runs/graph_v2/config_graph_nodes.json"))
try:
    T.cost_gate(1.9940, cfg)
    print("PASSED gate (unexpected)")
except T.CostGateError as e:
    print("CostGateError:", e)
# and what the 2T shim would have printed for graph_nodes
