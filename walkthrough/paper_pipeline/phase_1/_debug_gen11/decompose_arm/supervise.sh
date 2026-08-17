#!/bin/bash
# Relaunch the four workers until every clause has a final module, or 12 rounds.
# Grounds: this provider returned HTTP 503 and multi-minute stalls throughout the
# arm's window, and a worker that exhausts its in-process retries exits leaving its
# clause part-done.  `run_armg.py` is resumable by construction -- it refuses any
# stage but the next one -- so relaunching is safe and never re-sends a paid stage.
cd "$(dirname "$0")"
PY=../../../../../semi-formal-experiment/.venv/bin/python
for round in $(seq 1 12); do
  n=$(ls out/*.final.json 2>/dev/null | wc -l)
  [ "$n" -ge 17 ] && { echo "ROUND $round: all 17 done"; break; }
  echo "ROUND $round: $n finals"
  for grp in "l3147_3238_n003,l1707_1973_n006,l3239_3382_n002,l4252_4482_n016" \
             "l171_426_n022,l699_796_n012,l1001_1107_n005,l1368_1541_n019" \
             "l1707_1973_n022,l2474_2554_n004,l2821_3040_n017,l3239_3382_n004" \
             "l3596_3876_n009,l3877_3953_n014,l4252_4482_n005"; do
    PHASE1_HTTP_TIMEOUT=240 $PY -u run_armg.py --live --all --only "$grp" \
      >> "worker_${grp:0:12}.log" 2>&1 &
  done
  wait
done
echo "SUPERVISOR DONE: $(ls out/*.final.json 2>/dev/null | wc -l) finals"
