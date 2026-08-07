#!/usr/bin/env python3
"""Does the corpus contain a contrary-to-duty clause at all?

  cd semi-formal-experiment && .venv/bin/python ../walkthrough/contradiction_probe/ctd_scan.py

A contrary-to-duty norm has the shape "if norm N was VIOLATED, then Y".
Three progressively weaker filters over all 593 clauses. No panel access.
"""
import json, re

cs = json.load(open("modelspec_clauses.json"))["clauses"]

# 1. an antecedent naming a violation of a rule
VIOL = re.compile(r"\b(if|when|after|once)\b[^.]{0,120}"
                  r"\b(violat|breach|broke\b|broken|non-?compliance)", re.I)
# 2. an antecedent naming a completed misstep by the assistant (factual)
MISSTEP = re.compile(r"\b(if|when|after|once)\b[^.]{0,120}"
                     r"\bthe assistant\b[^.]{0,60}"
                     r"\b(makes|made|takes|took|has|inadvertently|accidentally)\b", re.I)
# 3. anticipatory: antecedent names a norm being IN FORCE, not violated
ANTIC = re.compile(r"\b(if|when)\b[^.]{0,160}"
                   r"\b(would violate|is prohibited|prohibited help|cannot .{0,40}without"
                   r"|forbid|not allowed|disallowed)\b", re.I)

for name, pat in (("1. antecedent = a VIOLATION of a rule", VIOL),
                  ("2. antecedent = a completed misstep (factual)", MISSTEP),
                  ("3. antecedent = a prohibition IN FORCE (anticipatory)", ANTIC)):
    hits = [c for c in cs if c["kind"] in ("conditional", "holistic")
            and pat.search(c["quote"])]
    print(f"===== {name}: {len(hits)} of 593")
    for c in hits:
        print(f"  {c['id']}  {c['section_id']:34} {c['quote'][:120]!r}")
    print()
