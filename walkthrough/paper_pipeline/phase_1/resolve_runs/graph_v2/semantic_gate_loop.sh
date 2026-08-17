#!/bin/bash
# Session-independent stage-4 loop (Matt's AFK directive, 2026-08-16):
# every 5 minutes, semantically gate any translated modules the two-pass
# DeepSeek gate has not yet seen (new bulk chunks land continuously).
# Exits when the bulk run has finished AND nothing remains ungated.
# Log: semantic_gate_loop.log
set -u
D="$(cd "$(dirname "$0")" && pwd)"
P=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python
cd "$D"
while true; do
  out=$($P semantic_gate.py --all-ungated --limit 120 2>&1)
  echo "==== $(date)"
  echo "$out" | tail -30
  if echo "$out" | grep -q "nothing ungated"; then
    if ! pgrep -f "bulk_run.sh" >/dev/null; then
      echo "==== bulk done and nothing ungated — loop exiting"
      break
    fi
  fi
  if echo "$out" | grep -q "THRESHOLD is None"; then
    echo "==== uncalibrated — loop exiting (set THRESHOLD first)"
    exit 2
  fi
  sleep 300
done
