#!/usr/bin/env python3
"""Reconcile arm E's RECORDED spend against the ground-truth ledger.

⚠️ THE MEASURED HOLE.  `translate.Client._log_usage` runs BEFORE
`_check_envelope`, so a truncated completion is BILLED and then RAISES, leaving
no turn record.  It hid 36% of arm D's spend.  `out/` totals therefore UNDER-count
by construction and must never be the spend figure of record.

Attribution is by prompt shape, not by row count: arm E sends a 39,959-char
system block on every call, which prices to >=10k prompt tokens.  Any concurrent
arm's rows are reported as UNATTRIBUTED rather than silently assigned.

READ-ONLY except `_debug_gen11/ds_critic_arm/reconcile.json`.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))
MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
MIN_PROMPT_TOKENS = 9000


def main():
    start = json.load(open(os.path.join(HERE, "out", "_ledger_start.json"))
                      )["first_new_line"]
    rows = [json.loads(l) for i, l in enumerate(open(LEDGER, encoding="utf-8"), 1)
            if i >= start and l.strip()]
    mine = [r for r in rows if r.get("model") == MODEL
            and (r.get("prompt_tokens") or 0) >= MIN_PROMPT_TOKENS]
    other = [r for r in rows if r not in mine]
    rec = sum(float(c.get("cost_usd") or 0.0)
              for p in glob.glob(os.path.join(HERE, "out", "*.arme.json"))
              for c in json.load(open(p, encoding="utf-8"))["calls"])
    billed = sum(float(r.get("cost_usd") or 0.0) for r in mine)
    trunc = [r for r in mine if r.get("truncated")]
    unf = [r for r in mine if (r.get("reasoning_chars") or 0) > 0]
    forced = [r for r in mine if (r.get("reasoning_chars") or 0) == 0]
    res = {"first_new_line": start, "new_rows": len(rows),
           "arme_rows_by_prompt_size": len(mine),
           "arme_billed_usd": round(billed, 6),
           "arm_recorded_usd": round(rec, 6),
           "unrecorded_usd_THE_HOLE": round(billed - rec, 6),
           "truncated_billed_rows": len(trunc),
           "truncated_billed_usd": round(
               sum(float(r["cost_usd"]) for r in trunc), 6),
           "unattributed_rows": len(other),
           "unattributed_usd": round(
               sum(float(r.get("cost_usd") or 0.0) for r in other), 6),
           "unforced_calls": len(unf),
           "unforced_reasoning_chars_min_max": [
               min((r["reasoning_chars"] for r in unf), default=0),
               max((r["reasoning_chars"] for r in unf), default=0)],
           "forced_calls": len(forced),
           "forced_reasoning_chars_distinct": sorted(
               {r["reasoning_chars"] for r in forced})}
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(HERE, "reconcile.json"), "w"), indent=1)
    print(f"\nSPEND OF RECORD for arm E: ${billed:.5f} (ledger), "
          f"not ${rec:.5f} (out/).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
