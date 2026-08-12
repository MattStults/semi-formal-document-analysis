#!/usr/bin/env python3
"""Repair census: the graph-construction analogue of the translation
pipeline's error tracking (Matt's process ruling, 2026-08-12).

Every buried failure in a run's failed/ dir is a PROBLEM INSTANCE, not just
noise on the way to a passing build: ds5's $0.92-vs-$0.15 overrun was repair
rounds and their re-paid prompts. This tool mines failed/ + health.jsonl
into a per-run taxonomy so that each category with repeat offenders gets a
tracked underlying-cause fix (prompt, example, or format forcing) TESTED
before the next paid run, and successive runs can be compared
category-by-category to show the error count actually falling.

Usage:  repair_census.py runs/ds5 [runs/ds4 ...]     (offline, no spend)
Writes: <run>/repair_census.json and prints the comparison table.
"""
import collections
import glob
import json
import os
import re
import sys

#: error-string -> category. Order matters: first match wins. Each category
#: is a candidate UNDERLYING CAUSE bucket; the fix lever is named beside it.
TAXONOMY = [
    ("quote-not-verbatim",   r"quote not verbatim",       "prompt/example"),
    ("uncovered-content",    r"uncovered content line",   "prompt/example"),
    ("coverage-identity",    r"coverage identity",        "prompt/example"),
    ("cross-link-provider",  r"cross-link .*does not contain",
     "autofix/validator"),
    ("merge-loses-content",  r"merge .*loses content",    "prompt"),
    ("rename-unprovided",    r"rename.*not provided|is not provided by",
     "format-forcing (enum)"),
    ("oversize-dup-loop",    r"oversize first draw|looks truncated",
     "prompt/format"),
    ("parse-failure",        r"failed to parse",          "format-forcing"),
    ("dropped-seed",         r"dropped",                  "autofix"),
    ("repair-exhausted",     r"call failed after",        "(terminal symptom)"),
]


def classify(errs):
    text = " ; ".join(str(e) for e in errs)
    for name, pat, lever in TAXONOMY:
        if re.search(pat, text):
            return name
    return "other"


def census(run_dir):
    rows = []
    for f in sorted(glob.glob(os.path.join(run_dir, "failed", "*.json"))):
        d = json.load(open(f))
        errs = d.get("errors") or []
        # root dispatches name as _L__r0 (empty key -> double underscore);
        # serial-path Driver._bury files carry only a millisecond stamp and
        # legitimately classify as phase "?" (review finding 6)
        m = re.search(r"_([DLU])_((?:c\d+_?)*)_?r(\d+)", os.path.basename(f))
        rows.append({
            "file": os.path.basename(f),
            "phase": m.group(1) if m else "?",
            "dispatch": (m.group(2).rstrip("_") or "root") if m else "?",
            "round": int(m.group(3)) if m else -1,
            "category": classify(errs),
            "first_error": str(errs[0])[:140] if errs else "",
            "reply_chars": len(d.get("reply") or ""),
        })
    by_cat = collections.Counter(r["category"] for r in rows)
    by_dispatch = collections.Counter(
        (r["dispatch"], r["category"]) for r in rows)
    repeat = sorted((k for k, v in by_dispatch.items() if v > 1),
                    key=lambda k: -by_dispatch[k])
    out = {
        "run": run_dir,
        "buried_failures": len(rows),
        "by_category": dict(by_cat.most_common()),
        "repeat_offenders": [
            {"dispatch": d, "category": c, "rounds": by_dispatch[(d, c)]}
            for d, c in repeat],
        "levers": {name: lever for name, _p, lever in TAXONOMY},
        "rows": rows,
    }
    path = os.path.join(run_dir, "repair_census.json")
    json.dump(out, open(path, "w"), indent=1)
    return out


def main():
    runs = sys.argv[1:] or ["runs/ds5"]
    results = [census(r) for r in runs]
    cats = sorted({c for r in results for c in r["by_category"]})
    w = max(len(c) for c in cats) + 2
    print("category".ljust(w) + "".join(f"{os.path.basename(r['run']):>10}"
                                        for r in results) + "   fix lever")
    levers = results[0]["levers"]
    for c in cats:
        line = c.ljust(w)
        for r in results:
            line += f"{r['by_category'].get(c, 0):>10}"
        print(line + f"   {levers.get(c, '')}")
    print("total".ljust(w) + "".join(f"{r['buried_failures']:>10}"
                                     for r in results))
    for r in results:
        if r["repeat_offenders"]:
            print(f"\n{r['run']} repeat offenders (same dispatch, same "
                  f"category, >1 round -- the repair transcript is not "
                  f"fixing these):")
            for o in r["repeat_offenders"][:8]:
                print(f"  {o['dispatch']:<24} {o['category']:<22} "
                      f"x{o['rounds']}")


if __name__ == "__main__":
    main()
