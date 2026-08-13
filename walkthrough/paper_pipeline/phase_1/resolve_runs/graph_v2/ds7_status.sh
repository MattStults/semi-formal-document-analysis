#!/bin/bash
# ds7 one-glance status
D="$(cd "$(dirname "$0")" && pwd)"
G="$D/runs/ds7"
if [ -f "$G/root_graph.json" ]; then
  echo "=== ds7 COMPLETE ==="
  grep -E "done:|resolution pass:|greedy descend:" "$D/runs/ds7_log.txt" | tail -4
  exit 0
fi
if kill -0 2216 2>/dev/null; then echo "ds7: RUNNING (pid 2216)"; else echo "ds7: PROCESS NOT RUNNING (stopped or crashed -- check $D/runs/ds7_log.txt)"; fi
echo "divisions: $(find "$G" -name division.json 2>/dev/null | wc -l | tr -d ' ')  subtree graphs: $(find "$G" -name graph.json 2>/dev/null | wc -l | tr -d ' ')  buried repairs: $(ls "$G/failed" 2>/dev/null | wc -l | tr -d ' ')"
for j in "$G"/inflight/job-*.json; do
  [ -e "$j" ] || continue
  echo "batch in flight: $(basename "$j")"
done
echo "log tail:"; tail -2 "$D/runs/ds7_log.txt" 2>/dev/null | cut -c1-140
