#!/usr/bin/env python3
"""Assemble the stage-4 baseline from the stored per-clause reports. FREE.

⛔ It makes no model call and reads only `--out`. Re-runnable, and re-running
it cannot change the measurement — every number here is a count over the JSON
the live run wrote.

⚠️ `unclear` IS ITS OWN ANSWER. Nothing below folds it into clean or defective
in either direction; the clean/defective split is on the four DEFECT verdicts
only, and the `unclear` volume is reported separately with its denominator.
"""

import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from stage4_driver import DEFECT_VERDICTS, SEVERITY   # noqa: E402


def load(out_dir):
    return [json.load(open(p, encoding="utf-8"))
            for p in sorted(glob.glob(os.path.join(out_dir, "reports",
                                                   "*.json")))]


def rendering_text(rep, item):
    for r in rep.get("renderings", ()):
        if r["item"] == item:
            return r["text"]
    return item


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args(argv)

    reports = load(a.out)
    plan = json.load(open(os.path.join(a.out, "plan.json"), encoding="utf-8"))
    spend = json.load(open(os.path.join(a.out, "spend.json"), encoding="utf-8"))

    seat_totals = collections.Counter()
    verdict_by_seat = collections.defaultdict(collections.Counter)
    seat_failures = collections.defaultdict(collections.Counter)
    defect_rows, clause_rows = [], []
    clean, defective = [], []
    instrument_defect_count = 0

    for rep in reports:
        cid = rep["clause_id"]
        drv = rep.get("_driver") or {}
        seatmap = dict(rep.get("seats") or {})
        seatmap["4a"] = (rep.get("advisory") or {}).get("4a", [])
        for seat, why in (drv.get("seat_failures") or {}).items():
            seat_failures[seat][why["error_class"]] += 1
        row_defects = []
        for seat, js in seatmap.items():
            for j in js:
                verdict_by_seat[seat][j["verdict"]] += 1
                seat_totals[seat] += 1
                if j["verdict"] in DEFECT_VERDICTS:
                    row_defects.append({
                        "clause_id": cid, "seat": seat, "verdict": j["verdict"],
                        "item": j["item"],
                        "text": rendering_text(rep, j["item"]),
                        "reason": j.get("reason", ""),
                        "evidential": j.get("evidential", True),
                        "stamps": j.get("stamps", [])})
        defect_rows.extend(row_defects)
        instrument_defect_count += len(rep.get("instrument_defects", []))
        pooled = (rep.get("unclear_rate") or {}).get("pooled") or {}
        # ⛔ 4a IS EXCLUDED FROM THE CLEAN/DEFECTIVE LINE, because `build_report`
        # excludes it from everything the pass line reads: it is the author
        # grading itself. Its verdicts are counted and printed, separately.
        evidential_defects = [d for d in row_defects if d["seat"] != "4a"]
        (defective if evidential_defects else clean).append(cid)
        clause_rows.append({
            "clause_id": cid,
            "status": drv.get("status"),
            "seats_adjudicated": drv.get("seats_adjudicated", []),
            "seats_refused": sorted((drv.get("seat_failures") or {})),
            "verdicts": {s: dict(collections.Counter(j["verdict"] for j in js))
                         for s, js in seatmap.items() if js},
            "unclear": pooled.get("unclear"),
            "denominator": pooled.get("denominator"),
            "defects": len(evidential_defects),
            "defects_4a_only": len(row_defects) - len(evidential_defects),
            "instrument_defects": len(rep.get("instrument_defects", [])),
            "readback_stamps": rep.get("readback_stamps", []),
            "echo": (rep.get("echo") or {}).get("clause_mean"),
        })

    defect_rows.sort(key=lambda d: (SEVERITY.get(d["verdict"], 9),
                                    d["clause_id"], d["seat"]))
    pooled_unclear = sum(r["unclear"] or 0 for r in clause_rows)
    pooled_denom = sum(r["denominator"] or 0 for r in clause_rows)

    summary = {
        "population": {
            "attempted_by_translation_run": 88,
            "modules_on_disk": plan["context"]["modules_on_disk"],
            "translated": plan["context"]["translated"],
            "reached_a_seat": plan["cost"]["clauses"],
            "did_not_reach_a_seat": [
                {"clause_id": s["clause_id"], "stage": s["stage"]}
                for s in plan["skipped"]],
            "reports_written": len(reports),
        },
        "headline": {
            "clean_at_stage_4": len(clean),
            "at_least_one_defect_verdict": len(defective),
            "denominator": len(clause_rows),
            "note": "clean = no unfaithful/unlicensed/not-conveyed/"
                    "not-as-meant from 4b/4c/4d. `unclear` is NOT counted as "
                    "either, and 4a (advisory, the author grading itself) is "
                    "not read by this line.",
        },
        "seat_verdicts": {s: dict(v) for s, v in verdict_by_seat.items()},
        "seat_denominators": dict(seat_totals),
        "seat_refusals": {s: dict(v) for s, v in seat_failures.items()},
        "unclear_pooled": {"unclear": pooled_unclear,
                           "denominator": pooled_denom,
                           "rate": (pooled_unclear / pooled_denom
                                    if pooled_denom else None)},
        "instrument_defects_4b_vs_4c": instrument_defect_count,
        "spend": spend,
        "polarity_findings": plan.get("polarity", {}),
        "clauses": clause_rows,
        "defect_rows": defect_rows,
    }
    json.dump(summary, open(os.path.join(a.out, "baseline.json"), "w",
                            encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("clauses", "defect_rows",
                                   "polarity_findings")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
