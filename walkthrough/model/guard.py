"""Guard: a change to the design document must be reflected in the model.

    python3 guard.py            # check — non-zero if stale or if the model finds something
    python3 guard.py --accept   # record the current design as reviewed

TWO FAILURE MODES, and only checking the second is the trap:

  STALE   — `resources/03_pipeline.md` changed and nobody re-checked whether the
            model still describes it. The model still passes, because it is
            internally consistent — with the *previous* design. This is the
            failure a "does it pass?" hook misses entirely, and it is the
            common one.
  FINDING — the model reports a contradiction or a hole.

Staleness is detected by hashing the design document and comparing against the
hash recorded at the last review. Accepting is a deliberate act: you are
asserting you have read the diff and either updated `pipeline.lp` or decided it
needed no change.

⚠️ WHAT THIS CANNOT DO. It cannot tell whether a `catches` claim is true, and it
cannot notice a problem nobody wrote down. It checks that the design is
self-consistent and that the model matches the document — not that either is
right.

Wire-up: a pre-commit hook, or a PostToolUse hook on edits to the design doc.
"""

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WALK = os.path.dirname(HERE)
DESIGN = os.path.join(WALK, "resources", "03_pipeline.md")
STAMP = os.path.join(HERE, "reviewed.json")
ACCEPTED = os.path.join(HERE, "accepted.json")
REQUIRED = ("finding", "subject", "date", "who", "why")
PY = os.path.join(WALK, "..", "semi-formal-experiment", ".venv", "bin", "python")
PY = PY if os.path.exists(PY) else sys.executable

#: Also guarded — a change to any of these can invalidate the model.
WATCHED = [DESIGN, os.path.join(HERE, "pipeline.lp"), os.path.join(HERE, "rules.lp")]


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def current():
    return {os.path.relpath(p, WALK): digest(p) for p in WATCHED if os.path.exists(p)}


def recorded():
    if not os.path.exists(STAMP):
        return {}
    return json.load(open(STAMP)).get("digests", {})


def waivers():
    """Return (valid, invalid). A waiver missing any required field does NOT waive."""
    if not os.path.exists(ACCEPTED):
        return {}, []
    raw = json.load(open(ACCEPTED)).get("waivers", [])
    valid, invalid = {}, []
    for w in raw:
        missing = [f for f in REQUIRED if not str(w.get(f, "")).strip()]
        if missing:
            invalid.append((w, missing))
            continue
        valid[(w["finding"], w["subject"])] = w
    return valid, invalid


#: ⛔ An earlier version scraped check.py's printed output with a regex. When
#: check.py's report format changed, the regex stopped matching, guard.py saw
#: zero findings, and reported GREEN on a design with ten open gaps. Import the
#: function instead — a format change can no longer silently disable the guard.
sys.path.insert(0, HERE)
import check as _check


def check():
    now, then = current(), recorded()
    stale_files = [k for k in now if then.get(k) != now[k]]
    missing = [k for k in now if k not in then]

    found, labels = _check.solve()
    ok_waivers, bad_waivers = waivers()

    waived = {f for f in found if f in ok_waivers}
    blocking = found - waived
    stale_waivers = set(ok_waivers) - found
    today = datetime.date.today().isoformat()

    print(f"MODEL — {len(found)} finding(s); run `python3 check.py` for detail\n")

    if waived:
        print(f"WAIVED — reported, not blocking ({len(waived)}):")
        for k, subj in sorted(waived):
            w = ok_waivers[(k, subj)]
            flag = ""
            if w.get("review_by") and w["review_by"] < today:
                flag = f"  ⚠️ review_by {w['review_by']} has passed"
            print(f"  {k}/{subj} — {w['who']}, {w['date']}{flag}")
            print(f"      {w['why'][:150]}")
        print()

    if bad_waivers:
        print(f"⛔ {len(bad_waivers)} INVALID waiver(s) — missing required fields, "
              f"so they do NOT waive:")
        for w, missing in bad_waivers:
            print(f"  {w.get('finding','?')}/{w.get('subject','?')} — "
                  f"missing: {', '.join(missing)}")
        print()

    if stale_waivers:
        print(f"⚠️ {len(stale_waivers)} waiver(s) for findings that no longer occur — "
              f"remove them so the list stays honest:")
        for k, subj in sorted(stale_waivers):
            print(f"  {k}/{subj}")
        print()

    has_findings = bool(blocking)

    if not then:
        print("⛔ never reviewed — no baseline recorded.")
        print("   Read the design, confirm pipeline.lp describes it, then:")
        print("   python3 guard.py --accept")
        return 1

    if stale_files:
        print(f"⛔ STALE — {len(stale_files)} watched file(s) changed since the model was "
              f"last reviewed against the design:")
        for k in stale_files:
            print(f"      {k}  {then.get(k, '(new)')} -> {now[k]}")
        print()
        print("   The model still passes its own checks — against the PREVIOUS design.")
        print()
        print("   ⭐ PROCESS: do not update the model yourself. Dispatch a CLEAN reviewer")
        print("      with model/REVIEW_BRIEF.md. It checks the model against the design,")
        print("      runs everything, and reports. It is explicitly allowed to answer")
        print("      'I cannot confidently review this' — that is a wanted outcome and")
        print("      means the writing needs fixing, not the model.")
        print()
        print("   Then: python3 guard.py --accept")
        return 1

    if has_findings:
        print(f"⛔ {len(blocking)} finding(s) not waived:")
        for k, subj in sorted(blocking):
            print(f"      {k}/{subj}")
        print()
        print("   Fix them, or add a waiver to accepted.json with date, who and why.")
        return 1

    print("✅ model is current with the design; "
          f"{len(waived)} finding(s) waived, none blocking")
    return 0


def accept():
    d = current()
    json.dump({"digests": d,
               "note": "Recorded by a human asserting they read the design diff "
                       "and confirmed model/pipeline.lp still describes it."},
              open(STAMP, "w"), indent=1)
    print("recorded as reviewed:")
    for k, v in d.items():
        print(f"   {k}  {v}")
    return 0


def watches(paths):
    """Exit 0 if any given path is one this guard watches. The shell hook asks
    here rather than keeping its own copy of the list — an earlier version had
    the list in three places, which is how they drift apart."""
    names = {os.path.basename(w) for w in WATCHED}
    return 0 if any(os.path.basename(p) in names for p in paths) else 1


def self_test():
    """The guard must SEE what check.py sees. An earlier version scraped text and
    silently saw nothing when the format changed, reporting green on ten gaps."""
    direct, _ = _check.solve()
    ok = len(direct) > 0
    print(f"  [{'PASS' if ok else 'FAIL'}] guard sees findings at all "
          f"({len(direct)} via direct import)")

    # a waiver must reduce the blocking set, and only for its own subject
    valid, _bad = waivers()
    overlap = {f for f in direct if f in valid}
    ok2 = len(overlap) == len(valid) or not valid
    print(f"  [{'PASS' if ok2 else 'FAIL'}] every recorded waiver matches a live "
          f"finding ({len(overlap)}/{len(valid)})")
    if not ok2:
        for f in sorted(set(valid) - direct):
            print(f"          stale waiver: {f[0]}/{f[1]}")
    return 0 if (ok and ok2) else 1


if __name__ == "__main__":
    if "--watches" in sys.argv:
        i = sys.argv.index("--watches")
        raise SystemExit(watches(sys.argv[i + 1:]))
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    raise SystemExit(accept() if "--accept" in sys.argv else check())
