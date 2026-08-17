#!/bin/bash
# Full-corpus completion run, 2026-08-16 (before Tuesday's DeepSeek x5 price
# change). 7 chunks of <=90 nodes so each run's worst-case estimate clears
# translate.py's $8 cost gate; batch execution per config (50% discount).
# Stops on rc>=2 (config error); rc=1 (some clause failed -> graveyard) is a
# per-clause outcome and the run continues. Log: bulk_run.log
set -u
D="$(cd "$(dirname "$0")" && pwd)"
P=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python
cd "$D"
for chunk in "$D"/bulk_chunk_*.txt; do
  ids=$(tr '\n' ' ' < "$chunk")
  echo "==== $(date) chunk $chunk ($(wc -l < "$chunk") ids)"
  $P translate_exec.py --config config_corpus_all.json \
     --clause $ids --live
  rc=$?
  echo "==== chunk rc=$rc"
  if [ "$rc" -ge 2 ]; then
    echo "==== ABORT: config-level error (rc=$rc)"; exit "$rc"
  fi
done
echo "==== $(date) all chunks done; running corpus gate"
cd "$D"
$P corpus_gate.py --quiet --json corpus_gate_report.json
