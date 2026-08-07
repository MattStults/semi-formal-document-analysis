"""Hook dispatcher: run the pipeline-model guard when a watched file is edited.

Reads a Claude Code PostToolUse payload on stdin, or takes paths as argv.
Advisory by design — it reports, it does not block an edit. The blocking gate is
the git pre-commit hook in this directory.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.dirname(HERE)
WALK = os.path.dirname(MODEL)

WATCHED = ("resources/03_pipeline.md", "model/pipeline.lp", "model/rules.lp")


def watched(paths):
    return [p for p in paths
            if any(p.replace("\\", "/").endswith(w) for w in WATCHED)]


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

    r = subprocess.run([sys.executable, os.path.join(MODEL, "guard.py")],
                       capture_output=True, text=True, cwd=MODEL)
    if r.returncode == 0:
        return 0
    print(f"\n⚠️  pipeline-model guard: {', '.join(os.path.basename(h) for h in hits)} "
          f"changed.\n{r.stdout.strip()}\n"
          f"   Run: python3 walkthrough/model/guard.py   (then --accept when reviewed)",
          file=sys.stderr)
    return 0  # advisory: never block an edit


if __name__ == "__main__":
    raise SystemExit(main())
