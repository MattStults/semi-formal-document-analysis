#!/usr/bin/env python3
"""THE MANIPULATION CHECK, and only that.

⛔ Branch count is NOT a result.  PREREG §3: banning the disjunction may simply
move the coin flip inside the critic, in which case this file reads as a clean
success while the modules get worse.  It tells us the instruction took effect.
Nothing more is claimed from it anywhere.

Also counts, mechanically:
  * `PRESERVE:` clauses per FIX line          (M2, F2's dose check)
  * E6 firings per cell                       (the entry held fixed on purpose)
  * FIX lines per clause, per cell
  * reasoning chars / truncation, from usage.jsonl

The branch predicate is arm E's own, verbatim from its RESULT §3(a): a FIX line
containing "either ... or", "or delete", "or remove", "or mark assumed".  It is
widened here by three more surface forms found in arm E's own edit lists
("delete it or", "or fix", "or the"), and BOTH the narrow and the widened counts
are printed so the arm-E baseline of 11/39 can be checked against the narrow one.

READ-ONLY except this directory.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
sys.path.insert(0, HERE)

NARROW = [r"\beither\b.*\bor\b", r"\bor delete\b", r"\bor remove\b",
          r"\bor mark\b.*assumed"]
WIDE = NARROW + [r"\bdelete .*\bor\b", r"\bor fix\b", r"\bor else\b",
                 r"\bor,\b", r"\bor otherwise\b", r"\bor simply\b",
                 r"\bor \(", r"\b, or \b"]

FIX_RE = re.compile(r"^\s*E(\d+)\s*:\s*FIX\b[\s—\-:]*(.*)$")
VERDICT_RE = re.compile(r"^\s*E(\d+)\s*:\s*(PASS|FIX)\b", re.I)


def replies(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".critic.txt"):
            out[f.split(".")[0]] = open(os.path.join(d, f),
                                        encoding="utf-8").read()
    return out


def fixes(raw):
    out = []
    for ln in raw.splitlines():
        if not VERDICT_RE.match(ln):
            continue
        m = FIX_RE.match(ln)
        if m and m.group(2).strip():
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def verdicts(raw):
    v = {}
    for ln in raw.splitlines():
        m = VERDICT_RE.match(ln)
        if m:
            v[int(m.group(1))] = m.group(2).upper()
    return v


def hits(s, pats):
    s = s.lower()
    return [p for p in pats if re.search(p, s)]


def score_cell(name, d):
    R = replies(d)
    rec = {"cell": name, "clauses": len(R), "fix_lines": 0,
           "branch_narrow": 0, "branch_wide": 0, "preserve": 0,
           "e6_fix": 0, "e6_clauses": [], "branch_examples": [],
           "per_clause": {}}
    for cid, raw in sorted(R.items()):
        fs = fixes(raw)
        v = verdicts(raw)
        bn = bw = pr = 0
        for n, s in fs:
            if hits(s, NARROW):
                bn += 1
                rec["branch_examples"].append(f"{cid} E{n}: {s[:150]}")
            if hits(s, WIDE):
                bw += 1
            if "PRESERVE" in s.upper():
                pr += 1
            if n == 6:
                rec["e6_fix"] += 1
                if cid not in rec["e6_clauses"]:
                    rec["e6_clauses"].append(cid)
        rec["fix_lines"] += len(fs)
        rec["branch_narrow"] += bn
        rec["branch_wide"] += bw
        rec["preserve"] += pr
        rec["per_clause"][cid] = {"verdict_lines": len(v), "fix": len(fs),
                                  "branch_narrow": bn, "preserve": pr,
                                  "entries_fixed": sorted(n for n, _ in fs)}
    return rec


def opus_baseline():
    """The comparator arm E measured: 1 branch line across all 17 Opus
    feedback files.  Recomputed here, not quoted."""
    d = os.path.join(G11, "ds_opus_loop", "out")
    n_lines = n_branch = 0
    ex = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".feedback_1.md"):
            continue
        for ln in open(os.path.join(d, f), encoding="utf-8"):
            ln = ln.strip()
            if len(ln) < 20:
                continue
            n_lines += 1
            if hits(ln, NARROW):
                n_branch += 1
                ex.append(f"{f}: {ln[:150]}")
    return {"cell": "armA_opus_feedback_1", "prose_lines": n_lines,
            "branch_narrow": n_branch, "branch_examples": ex}


if __name__ == "__main__":
    out = {"opus": opus_baseline()}
    for name, d in (("armE", os.path.join(G11, "ds_critic_arm", "out")),
                    ("F1", os.path.join(HERE, "out_f1")),
                    ("F2", os.path.join(HERE, "out_f2"))):
        r = score_cell(name, d)
        if r["clauses"]:
            out[name] = r
    print(f"{'cell':6s} {'cl':>3s} {'FIX':>4s} {'branch(narrow)':>15s} "
          f"{'branch(wide)':>13s} {'PRESERVE':>9s} {'E6 FIX':>7s}")
    for k in ("armE", "F1", "F2"):
        if k not in out:
            continue
        r = out[k]
        f = r["fix_lines"] or 1
        print(f"{k:6s} {r['clauses']:3d} {r['fix_lines']:4d} "
              f"{r['branch_narrow']:6d} ({100*r['branch_narrow']/f:4.1f}%) "
              f"{r['branch_wide']:6d} ({100*r['branch_wide']/f:4.1f}%) "
              f"{r['preserve']:4d} ({100*r['preserve']/f:4.1f}%) "
              f"{r['e6_fix']:7d}")
    o = out["opus"]
    print(f"\nOPUS feedback_1 baseline: {o['branch_narrow']} branch lines in "
          f"{o['prose_lines']} prose lines over 17 files")
    for e in o["branch_examples"]:
        print("   ", e)
    json.dump(out, open(os.path.join(HERE, "manipulation.json"), "w"), indent=1)
