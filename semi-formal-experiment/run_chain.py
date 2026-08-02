"""Drive the whole comparison end to end on real artifacts.

    extraction.json  --filter-->  filtered  --emit_asp-->  conflicts (tool)
                                                              |
    baseline conflicts.json x k -------------------------------+--> delta.py
                                                              +--> adjudicate.py

Everything here is glue: no metric is computed in this file. It exists so the
table can be regenerated from the artifacts with one command, and so the
rejected-rule bookkeeping is carried into the metrics rather than lost between
steps.

    python run_chain.py --extraction smoke_live2/extraction_*.json \\
        --baseline "smoke_live2/conflicts_baseline_run*.json" \\
        --out-dir smoke_live2
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import adjudicate
import delta
import emit_asp
import filter_extraction


def run(extraction_path, baseline_globs, out_dir, inventory=None):
    os.makedirs(out_dir, exist_ok=True)
    p = lambda n: os.path.join(out_dir, n)                      # noqa: E731

    with open(extraction_path) as f:
        extraction = json.load(f)

    # ---- 1. filter (emit_asp is fail-fast; drop what cannot be emitted) ----
    filtered, report = filter_extraction.filter_extraction(extraction)
    with open(p("extraction_filtered.json"), "w") as f:
        json.dump(filtered, f, indent=1)
    with open(p("rejections.json"), "w") as f:
        json.dump(report, f, indent=1)

    cc = filter_extraction.cross_check(extraction)

    # ---- 2. tool side ----
    tool_doc = emit_asp.run(filtered, p("tool.lp"), p("conflicts_tool_run1.json"))

    # ---- 3. baseline side ----
    paths = []
    for g in baseline_globs:
        paths.extend(sorted(glob.glob(g)))
    baseline_docs = [delta.load_conflicts(x) for x in sorted(set(paths))]

    # ---- 4. metrics ----
    # Rejected rules never reach the solver, so they are discounted from
    # coverage: the §6 stop rule must key on what the program actually holds.
    m = delta.compute([tool_doc], baseline_docs, extraction=extraction,
                      rejected_rule_ids=[r["id"] for r in report["rejected"]
                                         if r["kind"] == "rule"])
    m["rule_filter"] = {k: v for k, v in report.items() if k != "rejected"}
    m["rule_filter"]["rejected"] = report["rejected"]
    m["rule_filter"]["cross_check_agrees_with_emit_asp"] = cc["agree"]
    with open(p("delta_metrics.json"), "w") as f:
        json.dump(m, f, indent=1)
    with open(p("delta_summary.md"), "w") as f:
        f.write(delta.to_markdown(m))

    # ---- 5. worksheet ----
    inv = adjudicate.load_inventory(inventory or adjudicate.FOCUS_AREAS)
    ws = adjudicate.render_worksheet(m, inv, [tool_doc], baseline_docs,
                                     extraction=extraction,
                                     rejected=report["rejected"])
    with open(p("adjudication_worksheet.md"), "w") as f:
        f.write(ws)

    return m, report, cc, len(baseline_docs)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extraction", required=True)
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--inventory", default=None)
    a = ap.parse_args(argv)
    m, report, cc, n_base = run(a.extraction, a.baseline, a.out_dir, a.inventory)
    print(delta.metrics_table(m))
    print()
    print(f"baseline runs found: {n_base}")
    print(f"rules kept {report['rules_emitted']}/{report['rules_in']}, "
          f"rejected {report['rules_rejected']}, "
          f"cascade drops {report['cascade_drops']}")
    print(f"filter cross-check vs emit_asp.validate(skip_invalid=True): "
          f"{'AGREE' if cc['agree'] else 'DISAGREE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
