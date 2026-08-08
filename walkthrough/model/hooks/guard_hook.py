"""Hook dispatcher: run the staleness guard when a watched file is edited.

Reads a Claude Code PostToolUse payload on stdin, or takes paths as argv.
Advisory by design — it reports, it does not block an edit. The blocking gate is
the git pre-commit hook in this directory.

⚠️ This file keeps NO copy of the watch list. It asks guard.py --watches. The
list lived in three places once, and they drifted.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.dirname(HERE)
GUARD = os.path.join(MODEL, "guard.py")


def watched(paths):
    """Ask the guard, one path at a time, so we can name the hits."""
    hits = []
    for p in paths:
        if not p:
            continue
        r = subprocess.run([sys.executable, GUARD, "--watches", p],
                           capture_output=True, text=True, cwd=MODEL)
        if r.returncode == 0:
            hits.append(p)
    return hits


def main():
    paths = sys.argv[1:]
    if not paths and not sys.stdin.isatty():
        try:
            payload = json.load(sys.stdin)
            fp = (payload.get("tool_input") or {}).get("file_path")
            paths = [fp] if fp else []
        except Exception:
            paths = []
    hits = watched(paths)
    if not hits:
        return 0

    r = subprocess.run([sys.executable, GUARD], capture_output=True, text=True,
                       cwd=MODEL)
    if r.returncode == 0:
        return 0
    print(f"\n⚠️  staleness guard: {', '.join(os.path.basename(h) for h in hits)} "
          f"changed.\n{r.stdout.strip()}\n"
          f"   Run: python3 walkthrough/model/guard.py   "
          f"(then --accept <path> once you have re-read it)",
          file=sys.stderr)
    return 0  # advisory: never block an edit


if __name__ == "__main__":
    raise SystemExit(main())
