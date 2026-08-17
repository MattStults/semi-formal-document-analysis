#!/usr/bin/env python3
"""Reconcile the LICENCE CONTROL's RECORDED spend against the ground-truth ledger.

`translate.Client._log_usage` runs BEFORE `_check_envelope`, so a truncated or
empty completion is billed and written to `usage.jsonl` while raising and leaving
no arm record.  This arm's `out/` totals therefore UNDER-count by construction and
must never be the spend figure of record.

⚠️ ATTRIBUTION IS NOT BY PROMPT SIZE.  `arm_aprime/reconcile.py` could separate
its rows from the concurrent decomposition arm by prompt tokens; this arm cannot,
because arm A-prime sends the same 39,959-char block to the same model and its
rows sit in the same size band.  So: the window is the ledger line count stamped
by `run_licence.py` immediately before the send, and rows inside it are matched to
this arm by their COST FIGURES.  Anything left over is reported as UNATTRIBUTED
and counted AGAINST this arm as the conservative bound, never silently assigned
elsewhere.

⚠️ MEASURED, and it is why the matcher is what it is: `Client.complete_messages`
returns `cost_usd` but NOT a usage dict — every arm record on disk carries
`"usage": null`, in this arm and in `arm_aprime/out/` alike.  The first matcher
written here keyed on `(prompt_tokens, completion_tokens, cost_usd)` and matched
0 of 16 rows for that reason.  The only field both sides hold is the cost, so the
match is a MULTISET match on `cost_usd` — weaker than an identity match, and
recorded as weaker.  It cannot distinguish this arm's row from another arm's row
that happened to cost the same to the 6th decimal; the residue figure is the
guard against that, not the match.

READ-ONLY except `_debug_gen11/licence_control/reconcile.json`.
Usage:  reconcile.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))
OUT = os.path.join(HERE, "out")
MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"
KEYS = ("prompt_tokens", "completion_tokens", "cost_usd")


def arm_records():
    recs = {}
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".json") and not f.endswith(".raw.json"):
            r = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
            if isinstance(r, dict) and "_lc_cost_usd" in r:
                recs[r["clause_id"]] = r
    return recs


def sig(u):
    return tuple(u.get(k) for k in KEYS)


def main():
    win = json.load(open(os.path.join(HERE, "ledger_window.json"),
                         encoding="utf-8"))
    first = win["first_new_line"]
    lines = open(LEDGER, encoding="utf-8").read().splitlines()
    new = []
    for ln in lines[first - 1:]:
        ln = ln.strip()
        if ln:
            try:
                new.append(json.loads(ln))
            except json.JSONDecodeError:
                pass

    recs = arm_records()
    recorded = sum(float(r["_lc_cost_usd"] or 0.0) for r in recs.values())

    want = {}
    for cid, r in recs.items():
        want.setdefault(round(float(r["_lc_cost_usd"] or 0.0), 9), []).append(cid)

    matched, residue = [], []
    pool = {k: list(v) for k, v in want.items()}
    for r in new:
        if r.get("model") != MODEL:
            residue.append(r)
            continue
        s = round(float(r.get("cost_usd") or 0.0), 9)
        if pool.get(s):
            pool[s].pop()
            matched.append(r)
        else:
            residue.append(r)

    unmatched_records = sorted(c for v in pool.values() for c in v)
    matched_usd = sum(float(r.get("cost_usd") or 0.0) for r in matched)
    residue_usd = sum(float(r.get("cost_usd") or 0.0) for r in residue)
    trunc = [r for r in new if r.get("truncated")]

    res = {"ledger_lines_total": len(lines), "first_new_line": first,
           "retry_windows": win.get("retry_windows", []),
           "rows_in_window": len(new),
           "arm_records_on_disk": len(recs),
           "arm_recorded_usd": round(recorded, 6),
           "ledger_rows_matched_to_arm_records": len(matched),
           "matched_usd": round(matched_usd, 6),
           "arm_records_with_no_ledger_row": unmatched_records,
           "UNATTRIBUTED_rows": len(residue),
           "UNATTRIBUTED_usd": round(residue_usd, 6),
           "truncated_rows_in_window": len(trunc),
           "spend_of_record_lower_bound_usd": round(matched_usd, 6),
           "spend_of_record_upper_bound_usd": round(matched_usd + residue_usd, 6)}
    print(json.dumps(res, indent=1))
    json.dump(res, open(os.path.join(HERE, "reconcile.json"), "w"), indent=1)
    print(f"\nSPEND OF RECORD (ledger): ${matched_usd:.5f} attributed, "
          f"+${residue_usd:.5f} UNATTRIBUTED in window -> conservative total "
          f"${matched_usd + residue_usd:.5f}.  out/ says ${recorded:.5f}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
