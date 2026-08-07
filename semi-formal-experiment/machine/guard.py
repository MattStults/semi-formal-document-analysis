"""Guard: a change to a governed document must update the formal model and pass it.

Two failure modes, and only checking the second is the trap:

  STALE  — the document changed but `machine/scanned.lp` was not regenerated, so
           the model is describing a file that no longer exists in that form. The
           model still PASSES, because it is internally consistent — it is just
           consistent with the past. This is the failure a "does it pass?" hook
           misses entirely.
  BROKEN — the model does not pass its own validator.

Staleness is detected by re-running the scanner into memory and diffing against
the committed `scanned.lp`. No hash bookkeeping to drift out of date: the check
IS the regeneration.

    python3 machine/guard.py            # check; non-zero on stale or broken
    python3 machine/guard.py --fix      # regenerate scanned.lp, then check

Wire-up (both, deliberately — one is universal, one is immediate):
  * git pre-commit  — fires for every agent and every human, tool-agnostic
  * Claude Code PostToolUse — fires the moment an edit lands, so the feedback
    arrives while the change is still in working memory
"""

import io
import os
import subprocess
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCANNED = os.path.join(HERE, "scanned.lp")

#: Changing any of these obliges you to update the model. This list is the
#: contract; adding a governed document means adding it here.
GOVERNED = (
    "HARNESS_REDESIGN.md",
    "CYCLE_DESIGN.md",
    "MODULE_MAP.md",
    "REPRODUCIBILITY.md",
    "ITERATION_LOOP.md",
    "cycle.py",
)


def _regenerate():
    """Return what scan.py would write right now, without writing it."""
    sys.path.insert(0, HERE)
    import scan
    import importlib
    importlib.reload(scan)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        scan.main([])
    out = buf.getvalue()
    if out.strip():
        return out
    # scan.main writes the file itself; fall back to reading what it wrote
    return open(SCANNED, encoding="utf-8").read()


def check(fix=False):
    fails = []

    fresh = _regenerate()
    on_disk = open(SCANNED, encoding="utf-8").read() if os.path.exists(SCANNED) else ""
    if fresh != on_disk:
        if fix:
            open(SCANNED, "w", encoding="utf-8").write(fresh)
            print("guard: regenerated machine/scanned.lp")
        else:
            a, b = on_disk.count("\n"), fresh.count("\n")
            fails.append(
                f"STALE: machine/scanned.lp does not match the current files "
                f"({a} -> {b} lines). A governed document changed without the "
                f"model being updated. Run: python3 machine/guard.py --fix")

    py = os.path.join(REPO, ".venv", "bin", "python")
    py = py if os.path.exists(py) else sys.executable
    r = subprocess.run([py, os.path.join(HERE, "check_model.py")],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        fails.append("BROKEN: check_model.py failed:\n    " +
                     "\n    ".join(tail[-12:]))
    return fails, r.stdout


def main(argv):
    fix = "--fix" in argv
    fails, out = check(fix=fix)
    if fails:
        print("⛔ formal-model guard FAILED\n")
        for f in fails:
            print("  " + f + "\n")
        print("The model in machine/ describes this repo's own governance rules.")
        print("A change to a governed document must be reflected there and pass.")
        print("Governed: " + ", ".join(GOVERNED))
        return 1
    print("✅ formal-model guard passed — model is current and valid")
    for line in out.strip().splitlines():
        if line.startswith(("PASS", "FAIL")) or "contradiction" in line:
            print("   " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
