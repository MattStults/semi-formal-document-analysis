#!/bin/bash
# Full-corpus completion run — chunked so each run's worst-case estimate
# clears translate.py's $8 cost gate; batch execution per config.
#
# ⚠️ RE-GLOBS EVERY ITERATION (2026-08-17): the first version expanded
# bulk_chunk_*.txt once at loop start, so renaming a chunk file under a
# running loop handed translate_exec an EMPTY --clause list — whole-corpus
# selection — and only the cost gate ($57.86 vs $8, nothing sent) stopped
# it. Holding a chunk = rename to .hold; the next iteration re-globs and
# simply does not see it. A missing/empty chunk file now aborts loudly.
# Stops on rc>=2 (config error); rc=1 (per-clause failures -> graveyard)
# continues. Log: bulk_run.log
set -u
D="$(cd "$(dirname "$0")" && pwd)"
P=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/semi-formal-experiment/.venv/bin/python
cd "$D"
while true; do
  chunk=$(ls "$D"/bulk_chunk_*.txt 2>/dev/null | head -1)
  if [ -z "$chunk" ]; then
    echo "==== $(date) no runnable chunks; done"
    break
  fi
  if [ ! -s "$chunk" ]; then
    echo "==== ABORT: chunk file $chunk is missing or empty"; exit 3
  fi
  ids=$(tr '\n' ' ' < "$chunk")
  echo "==== $(date) chunk $chunk ($(wc -l < "$chunk") ids)"
  $P translate_exec.py --config config_corpus_all.json --clause $ids --live
  rc=$?
  echo "==== chunk rc=$rc"
  if [ "$rc" -ge 2 ]; then
    echo "==== ABORT: config-level error (rc=$rc)"; exit "$rc"
  fi
  mv "$chunk" "$chunk.done"
done
echo "==== $(date) all chunks done; running corpus gate"
$P corpus_gate.py --quiet --json corpus_gate_report.json
