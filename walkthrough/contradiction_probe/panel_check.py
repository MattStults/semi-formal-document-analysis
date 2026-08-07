#!/usr/bin/env python3
"""AFTER-THE-FACT panel check. Run from semi-formal-experiment/.

  cd semi-formal-experiment && .venv/bin/python ../walkthrough/contradiction_probe/panel_check.py

⚠️ This script was written and run only AFTER doc.lp, behaviour.lp, conflict.lp
and every t*.lp were frozen. The prior probe (deontic_probe/FINDINGS.md §1)
leaked the panel into its encoding and had to discount its own successes.
Nothing here feeds back into the encoding.
"""
import json, re, sys, benchmark

ENCODED = ["m0198", "m0200", "m0203", "m0204", "m0208", "m0252", "m0253",
           "m0255", "m0270", "m0362", "m0139", "m0151", "m0440", "m0259",
           "m0260", "m0263", "m0265"]
# what conflict.lp's relevance query (T5) returned
PREDICTED = {"m0198", "m0203", "m0208", "m0252", "m0253"}

cs = {c["id"]: c for c in json.load(open("modelspec_clauses.json"))["clauses"]}
rows = (benchmark.load_true_panel(spec_keys=("openai",))
        ["harm-avoidance-to-third-parties"]["coverage"]["openai"]["passages"])
pan = {}
for r in rows:
    m = re.search(r"#(\w+) > ¶(\d+)", r["locator"])
    if m:
        pan[(m.group(1), int(m.group(2)))] = r

print(f"{'clause':7} {'section':35} {'kind':13} {'panel':6} T5")
for i in ENCODED:
    c = cs[i]
    n = int(re.search(r"¶(\d+)", c["locator"]).group(1))
    r = pan.get((c["section_id"], n))
    print(f"{i:7} {c['section_id']:35} {c['kind']:13} "
          f"{r['score'] if r else '??':<6} {'*' if i in PREDICTED else ''}")
