#!/usr/bin/env python3
"""Arm G's spend, from its OWN stage records first, with `usage.jsonl` as a
cross-check.  Several agents append to that ledger concurrently, so its rows are
not this arm's rows; the reconciliation matches on the token shapes only arm G
produces (a prose stage's small prompt, or a stage-4 send) inside this arm's
wall-clock window.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_armg                                               # noqa: E402

LEDGER = os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))


def main():
    per, calls, trunc, retries = {}, 0, 0, 0
    for f in sorted(glob.glob(os.path.join(HERE, "out", "*.stages.json"))):
        d = json.load(open(f, encoding="utf-8"))
        c = sum(s["cost_usd"] for s in d["stages"])
        per[d["clause_id"]] = (len(d["stages"]), c,
                               (d.get("floor") or {}).get("outcome"),
                               len((d.get("floor") or {}).get("breaches") or []))
        calls += len(d["stages"])
        trunc += sum(1 for s in d["stages"] if s.get("truncated"))
        retries += sum((s.get("attempts") or 1) - 1 for s in d["stages"])
    recorded = sum(v[1] for v in per.values())
    print(f"{'clause':22} {'stages':>6} {'cost':>9} {'outcome':>10} {'breaches':>8}")
    for k, v in per.items():
        print(f"{k:22} {v[0]:6} {v[1]:9.5f} {str(v[2]):>10} {v[3]:8}")
    print(f"\nRECORDED  {calls} calls, ${recorded:.5f}")
    w = run_armg.ledger_waste()
    print(f"WASTED    calls that produced no record: ${w:.5f}  "
          f"({100 * w / (recorded + w):.0f}% of spend)")
    print(f"ARM TOTAL ${recorded + w:.5f}  cap ${run_armg.CAP_USD:.3f}  "
          f"brief ceiling $0.120")
    print(f"truncated prose stages KEPT: {trunc};  in-process retries: {retries}")

    rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8")]
    # WASTE, computed rather than hand-maintained.  Arm G is the only arm in
    # this window that sends a prompt under 8,000 tokens (its prose stages); the
    # other live arms send the 40 KB production block, ~10.5k tokens, every
    # time.  So: every prose-shaped row in the window, minus the ones this arm
    # has a stage record for, is a call arm G paid for and got nothing from.
    START_TS = 1786925100
    prose = [r for r in rows if r["ts"] > START_TS and r["prompt_tokens"] < 8000]
    # Matched on `content_chars`, which the ledger records and which equals
    # len(raw) on the stage record exactly.  (`_check_envelope`'s return value
    # carries no `usage`, so the stage records' `usage` field is always null --
    # true of `ds_opus_loop/loop.py` as well, and worth knowing.)
    pool = []
    for f in sorted(glob.glob(os.path.join(HERE, "out", "*.stages.json"))):
        for st in json.load(open(f, encoding="utf-8"))["stages"]:
            if st["stage"] != 4:
                pool.append(len(st["raw"]))
    waste = []
    for r in prose:
        if r["content_chars"] in pool:
            pool.remove(r["content_chars"])
        else:
            waste.append(r)
    print(f"\nWASTE from the ledger: {len(waste)} prose-shaped calls with no "
          f"stage record, ${sum(r['cost_usd'] for r in waste):.5f}")
    for r in waste:
        print(f"   ts {r['ts']:.0f}  prompt {r['prompt_tokens']:5}  "
              f"completion {r['completion_tokens']:5}  content_chars "
              f"{r['content_chars']:5}  {r['finish_reason']}  "
              f"${r['cost_usd']:.5f}")
    # arm G's stage-4 sends are the only ones in this window whose prompt is
    # >12k tokens (production block + a 3-stage transcript); prose stages are the
    # only ones under 8k.  Other arms' single-shot calls sit at ~10.5k.
    lo = min(r["ts"] for r in rows[-400:]) if rows else 0
    print(f"\nusage.jsonl cross-check (whole tail, {len(rows)} rows, "
          f"other arms' rows included):")
    for lab, pred in (("prose-shaped (<8k prompt)", lambda r: r["prompt_tokens"] < 8000),
                      ("armG stage-4-shaped (>12k prompt)",
                       lambda r: r["prompt_tokens"] > 12000)):
        sel = [r for r in rows if pred(r) and r["ts"] > 1786925000]
        print(f"  {lab}: {len(sel)} rows, ${sum(r['cost_usd'] for r in sel):.5f}")
    print(f"  (arm G is {calls} recorded + "
          f"{'the truncated/empty sends listed in run_armg.WASTED_USD'})")


if __name__ == "__main__":
    main()
