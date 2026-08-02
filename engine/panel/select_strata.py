#!/usr/bin/env python3
"""Pick a stratified smoke sample for prompt validation, using cheap-panel scores.

Strata per behaviour (cheap-panel 0..6 score = sum of ternary verdicts):
  likely-relevant (score >= 5), in-between (2..4), likely-not (0..1).
Deterministic pick (hash-ordered) of `per_stratum` from each band -> one locators file
per behaviour. The pinned smoke-*.txt samples are the record of the validation
runs; the run logs behind them live on the experiment branch.

  python3 select_strata.py --runlog=<cheap runlog> [--rubric=v2] [--per=5]
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "panel-config.json").read_text())
SITE2BEH = {"helpfulness": "helpfulness", "harm-avoidance-to-third-parties": "third-party-harm",
            "avoiding-over-and-under-caution": "over-under-caution"}


def main():
    runlog, rubric, per = None, "v2", 5
    for a in sys.argv[1:]:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--rubric="):
            rubric = a.split("=", 1)[1]
        elif a.startswith("--per="):
            per = int(a.split("=", 1)[1])
    if not runlog:
        sys.exit("need --runlog= (the cheap-panel runlog to stratify from)")
    cheap = set(CONFIG["panels"]["cheap"])
    votes = collections.defaultdict(dict)
    for line in runlog.read_text().splitlines():
        d = json.loads(line)
        if d.get("rubric", "v1") == rubric and d.get("parsed", True) and d["model"] in cheap:
            votes[(d["behaviour"], d["locator"])][d["model"]] = d.get("verdict", 0)
    behs = [SITE2BEH[s] for s in CONFIG["display"]["behaviours"]]
    for beh in behs:
        strata = {"likely-relevant": [], "in-between": [], "likely-not": []}
        for (b, loc), mv in votes.items():
            if b != beh or len(mv) < 3:
                continue
            score = sum(mv.values())
            band = "likely-relevant" if score >= 5 else "in-between" if score >= 2 else "likely-not"
            strata[band].append(loc)
        pick = []
        for band, locs in strata.items():
            locs.sort(key=lambda l: hashlib.md5((beh + l).encode()).hexdigest())
            pick += locs[:per]
            print(f"{beh:20} {band:15} pool {len(locs):4} -> picked {min(per, len(locs))}")
        out = HERE / f"smoke-{beh}.txt"
        out.write_text("\n".join(sorted(pick)) + "\n")
        print(f"  -> {out.name} ({len(pick)} locators)\n")


if __name__ == "__main__":
    main()
