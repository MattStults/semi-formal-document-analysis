#!/usr/bin/env python3
"""⛔ WRITE-ONCE LEDGER FOR CRITIC ARTIFACTS.

Why this file exists (coordinator ruling, mid-run): in a sibling slice a
`critic_1.md` was **rewritten in place between two readers**. Two agents read
materially different documents under the same filename — one reporting two
prompt findings, the revised one reporting none — and neither could tell. That
makes "the critic confirmed it" unfalsifiable, which is the one thing this run
exists to establish.

The defect is invisible to `validate.py`, which does not read prose. It is
trivially visible to four lines of sha256, which is what this is.

Contract:
  * A critic artifact is named `<clause>.critic_<turn>.md` and is WRITE-ONCE.
    A revised pass is a NEW file at the next turn number, never an edit.
  * `record` freezes the hash of every critic artifact present.
  * `verify` re-hashes and REFUSES if any recorded file changed, and reports any
    file that appeared without being recorded.
  * Any claim of the form "the critic found X" must cite the file and the hash
    printed here. A claim that cannot name its source file and hash is not a
    finding and must be marked MINE ALONE, NOT CORROBORATED.

Usage:
    critic_ledger.py record     # freeze what is on disk now
    critic_ledger.py verify     # exit 1 if anything moved
"""
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
LEDGER = os.path.join(HERE, "CRITIC_LEDGER.json")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def scan():
    rows = {}
    for p in sorted(glob.glob(os.path.join(OUT, "*.critic_*.md"))):
        name = os.path.basename(p)
        rows[name] = {"sha256": sha(p), "bytes": os.path.getsize(p)}
    return rows


def load():
    if not os.path.exists(LEDGER):
        return {}
    return json.load(open(LEDGER))


def record():
    old, cur = load(), scan()
    # ⛔ Recording must never quietly overwrite a differing prior hash — that
    # would be the very laundering this file exists to prevent.
    changed = [n for n in old if n in cur and old[n]["sha256"] != cur[n]["sha256"]]
    if changed:
        print("⛔ REFUSING TO RECORD — these artifacts CHANGED after being frozen:")
        for n in changed:
            print(f"   {n}: {old[n]['sha256'][:16]} -> {cur[n]['sha256'][:16]}")
        print("This is a finding about the run, not a mess to tidy away.")
        return 1
    new = sorted(set(cur) - set(old))
    merged = {**old, **cur}
    json.dump(merged, open(LEDGER, "w"), indent=1, sort_keys=True)
    for n in sorted(merged):
        print(f"{merged[n]['sha256'][:16]}  {merged[n]['bytes']:7d}  {n}"
              + ("   [NEW]" if n in new else ""))
    print(f"\n{len(merged)} critic artifact(s) frozen; {len(new)} new this pass.")
    return 0


def verify():
    old, cur = load(), scan()
    bad = 0
    for n, row in sorted(old.items()):
        if n not in cur:
            print(f"⛔ MISSING: {n} was recorded and is now gone")
            bad += 1
        elif cur[n]["sha256"] != row["sha256"]:
            print(f"⛔ OVERWRITTEN: {n}")
            print(f"   recorded {row['sha256']}")
            print(f"   on disk  {cur[n]['sha256']}")
            bad += 1
    for n in sorted(set(cur) - set(old)):
        print(f"⚠️ UNRECORDED: {n} appeared after the last `record`")
        bad += 1
    print("OK — every recorded critic artifact is byte-identical." if not bad
          else f"\n{bad} problem(s).")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    sys.exit(record() if cmd == "record" else verify())
