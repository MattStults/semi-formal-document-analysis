#!/usr/bin/env bash
# Create the venv and install everything. Idempotent — safe to re-run.
#
#     bash setup_env.sh            # install
#     bash setup_env.sh --check    # verify only, install nothing
#
# The venv lives at semi-formal-experiment/.venv because several commands take
# relative paths and expect to run from that directory.
#
# NOTE FOR AGENTS: call binaries by path — `semi-formal-experiment/.venv/bin/python`.
# Do not `source` the activate script; it cannot be statically vetted and will
# stall on an approval prompt.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/semi-formal-experiment/.venv"
PY="$VENV/bin/python"
CHECK_ONLY="${1:-}"

if [ "$CHECK_ONLY" != "--check" ]; then
    [ -x "$PY" ] || { echo "creating $VENV"; python3 -m venv "$VENV"; }
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet -r "$ROOT/requirements.txt"
fi

[ -x "$PY" ] || { echo "no venv at $VENV — run without --check first"; exit 1; }

echo "--- imports ---"
fail=0
while read -r mod why; do
    if "$PY" -c "import $mod" 2>/dev/null; then
        ver="$("$PY" -c "import $mod,sys; print(getattr($mod,'__version__',getattr($mod,'VERSION','?')))" 2>/dev/null || echo '?')"
        printf '  ok      %-12s %-10s %s\n' "$mod" "$ver" "$why"
    else
        printf '  MISSING %-12s %-10s %s\n' "$mod" "" "$why"
        fail=1
    fi
done <<'MODS'
pytest the test suite
clingo the solver; absent = ASP tests show as collection errors
pydantic phase_1 schema and format forcing
MODS

echo "--- self-tests that need no network and cost nothing ---"
run() {
    if out="$("$PY" "$1" --self-test 2>&1)"; then
        printf '  ok      %s — %s\n' "$(basename "$(dirname "$1")")/$(basename "$1")" \
            "$(echo "$out" | tail -1)"
    else
        printf '  FAILED  %s\n%s\n' "$1" "$(echo "$out" | tail -3)"
        fail=1
    fi
}
run "$ROOT/walkthrough/paper_pipeline/phase_1/translate.py"
run "$ROOT/walkthrough/link.py"

echo
if [ "$fail" -eq 0 ]; then
    echo "environment OK."
    echo
    echo "  $PY -m pytest -q                 # from semi-formal-experiment/, ~4 min"
    echo "  $PY walkthrough/paper_pipeline/phase_1/translate.py --clause m0255"
    echo "                                   # DRY RUN, sends nothing"
else
    echo "environment INCOMPLETE — see MISSING/FAILED above."
    exit 1
fi
