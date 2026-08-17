#!/usr/bin/env python3
"""Reconcile arm A-prime's RECORDED spend against the ground-truth ledger.

`translate.Client._log_usage` runs BEFORE `_check_envelope`, so a truncated or
empty completion is billed and written to `usage.jsonl` while raising and
leaving no arm record.  This arm's `out/` totals therefore UNDER-count by
construction and must never be the spend figure of record.

`../decompose_arm/` is running concurrently on the SAME provider and model, so
the window is not this arm's alone.  Attribution is by `prompt_tokens`: arm A'
sends a fixed 39,959-char system block plus one user block, which prices to
~10.1k prompt tokens; the concurrent arm's calls sit far below that.  Rows are
matched to the arm's own recorded usage dicts where those exist, and the
residue is reported as UNATTRIBUTED rather than silently assigned.

READ-ONLY except for `_debug_gen11/arm_aprime/reconcile.json`.
Usage:  reconcile.py <first_new_line_number>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))
OUT = os.path.join(HERE, "out")
MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
#: arm A' prompt is 39,959c system + ~2-8kc user -> >=9,000 prompt tokens.
#: Every concurrent-arm call in this window is well under this.
APRIME_MIN_PROMPT_TOKENS = 9000


def arm_records():
    recs = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".json") and not f.endswith(".raw.json"):
            r = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
            if isinstance(r, dict) and "_aprime_cost_usd" in r:
                recs[r["clause_id"]] = r
    return recs


def main(first_new):
    lines = open(LEDGER, encoding="utf-8").read().splitlines()
    new = []
    for ln in lines[first_new - 1:]:
        ln = ln.strip()
        if ln:
            try:
                new.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    recs = arm_records()
    recorded = sum(float(r["_aprime_cost_usd"] or 0.0) for r in recs.values())

    mine = [r for r in new if r.get("model") == MODEL
            and (r.get("prompt_tokens") or 0) >= APRIME_MIN_PROMPT_TOKENS]
    other = [r for r in new if r not in mine]
    billed = sum(float(r.get("cost_usd") or 0.0) for r in mine)
    trunc = [r for r in mine if r.get("truncated")]

    res = {"ledger_lines_total": len(lines), "first_new_line": first_new,
           "new_rows": len(new),
           "aprime_rows_by_prompt_size": len(mine),
           "aprime_billed_usd": round(billed, 6),
           "arm_records_on_disk": len(recs),
           "arm_recorded_usd": round(recorded, 6),
           "unrecorded_usd": round(billed - recorded, 6),
           "truncated_billed_rows": len(trunc),
           "concurrent_other_rows": len(other),
           "concurrent_other_usd": round(
               sum(float(r.get("cost_usd") or 0.0) for r in other), 6)}
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(HERE, "reconcile.json"), "w"), indent=1)
    print(f"\nSPEND OF RECORD for arm A-prime: ${billed:.5f} "
          f"(ledger), not ${recorded:.5f} (out/).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1])))
