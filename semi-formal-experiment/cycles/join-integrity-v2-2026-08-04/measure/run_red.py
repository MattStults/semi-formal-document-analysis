"""Capture the RED transcript for test_join_v2.py into red_transcript.txt.

Run BEFORE the implementation lands; re-runnable for the record. Clears
__pycache__ first (HANDOFF: stale bytecode can lie about what ran).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1
                   else "red_transcript.txt")

for root in (EXP,):
    pc = os.path.join(root, "__pycache__")
    if os.path.isdir(pc):
        shutil.rmtree(pc)

r = subprocess.run(
    [sys.executable, "-m", "pytest",
     os.path.join(EXP, "test_join_v2.py"), "-v", "--tb=line",
     "-p", "no:cacheprovider"],
    capture_output=True, text=True)
with open(OUT, "w") as f:
    f.write(r.stdout + r.stderr)
print(OUT)
print(r.stdout.splitlines()[-1] if r.stdout else r.returncode)
