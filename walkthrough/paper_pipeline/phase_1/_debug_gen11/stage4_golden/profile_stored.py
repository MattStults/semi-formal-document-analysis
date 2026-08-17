#!/usr/bin/env python3
"""What stage 4 ALREADY DID on defects we can anchor without a model — read
off the stored replies of the two runs already on disk.

    ../../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/stage4_golden/profile_stored.py

⛔ ZERO SPEND. Every number below is deterministic re-analysis of replies
already paid for. There is no client seam in this file.

⭐ THE RULE THAT DECIDES WHAT MAY APPEAR HERE. A cell of the detection profile
can be filled from stored replies ONLY if the defect was identified by
something OTHER than the instrument being measured. Two such sources exist on
disk:

  MECHANICAL   `checks.polarity_findings` — a deterministic check, re-run here
               over the modules rather than quoted from any document. No model
               is involved at any point, so a seat's verdict at that site is a
               genuine hit or a genuine miss.
  PIPELINE     a node's own `NEEDS` block, which TELLS the translator to put a
               name in `requires`. A module that did so is correct by the
               pipeline's own instruction, so a 4c `unlicensed` on it is a
               false positive — again with no model in the loop.

⛔ WHAT MAY NOT APPEAR HERE, AND WHY THE TABLE IS MOSTLY EMPTY. `BASELINE.md`
§5 names real specimens of inverted modality (`l1_170_n088`), invented
obligation (`l1_170_n075`) and dropped content (`l1_170_n056`) — but every one
of them was FOUND BY STAGE 4 ITSELF. Scoring recall against defects the
instrument selected measures nothing: the denominator is "defects it caught",
so the answer is 100% by construction. Those cells are therefore reported as
UNFILLABLE OFFLINE, and filling them is exactly what the golden set is for.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GRAPH_V2 = os.path.join(PHASE1, "resolve_runs", "graph_v2")
WALK = os.path.abspath(os.path.join(PHASE1, "..", ".."))
for _p in (PHASE1, GRAPH_V2, WALK):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks                       # noqa: E402
import schema                       # noqa: E402

sys.path.insert(0, HERE)
import score_golden as SG           # noqa: E402

RUNS = os.path.join(GRAPH_V2, "translation_sample", "runs")

#: (label, stored stage-4 output, the translation run it judged)
STORED = [
    ("baseline", os.path.join(PHASE1, "_debug_gen11", "stage4_baseline",
                              "out"),
     os.path.join(RUNS, "20260815-130831-together-deepseek-v4-flash")),
    ("polarity", os.path.join(PHASE1, "_debug_gen11", "stage4_polarity",
                              "out_a"),
     os.path.join(RUNS, "20260815-124836-together-deepseek-v4-flash")),
]

#: Every class the golden set plants. A class with no MECHANICAL or PIPELINE
#: anchor on disk cannot be scored offline at all, and saying so is the point.
CLASSES = ["prefer-polarity", "inverted-modality", "invented-obligation",
           "fact-as-deontic", "dropped-obligation", "scope-drift-widen",
           "scope-drift-narrow", "disjunction-as-conjunction"]

UNFILLABLE = {
    "inverted-modality":
        "specimens exist (`l1_170_n088` asserts[3],[4]; `l1_170_n052`) but "
        "STAGE 4 FOUND THEM, so the denominator is 'defects it caught' and "
        "recall is 100% by construction",
    "invented-obligation":
        "same — `l1_170_n075` asserts[0] was named BY 4b",
    "dropped-obligation":
        "`l1_170_n056` was called defective by a human reader, but on a "
        "DIFFERENT translation of the node (run 124836) than the one stage 4 "
        "judged (run 130831). Different bytes; not a join",
    "fact-as-deontic": "no anchored specimen among the judged clauses",
    "scope-drift-widen": "no anchored specimen among the judged clauses",
    "scope-drift-narrow": "no anchored specimen among the judged clauses",
    "disjunction-as-conjunction":
        "the human read names `l3147_3238_n003`, which no stage-4 run has "
        "judged",
}


def load_modules(run_dir):
    out = {}
    for f in sorted(os.listdir(run_dir)):
        if not f.endswith(".json") or f.endswith((".version.json",
                                                  ".transcript.json")):
            continue
        if f in ("run.json", "concepts.json"):
            continue
        obj = json.load(open(os.path.join(run_dir, f), encoding="utf-8"))
        if obj.get("outcome") == "translated":
            out[obj["clause_id"]] = obj
    return out


# ==========================================================================
#  1. the MECHANICAL anchor: `prefer` polarity
# ==========================================================================

def polarity_rows(label, out_dir, run_dir):
    mods = load_modules(run_dir)
    got, _ = SG.load_arm(out_dir)
    rows = []
    for cid, obj in sorted(mods.items()):
        try:
            mod = schema.validate(obj)
        except Exception:                                    # noqa: BLE001
            continue
        for f in checks.polarity_findings(mod):
            if cid not in got:
                rows.append({"run": label, "clause": cid, "site": f.where,
                             "judged": False, "seats": {},
                             "message": f.message})
                continue
            seats = {}
            for seat in SG.SEATS:
                seats[seat] = SG.verdict_at(got[cid].get(seat), [f.where])
            rows.append({"run": label, "clause": cid, "site": f.where,
                         "judged": True, "seats": seats,
                         "message": f.message})
    return rows


# ==========================================================================
#  2. the PIPELINE anchor: names the node TOLD the module to borrow
# ==========================================================================

_NEEDS = ("NEEDS -- these concepts are established by OTHER nodes of the "
          "graph, so every one of them belongs in this module's `requires`")


def borrow_rows(label, out_dir, run_dir, corpus):
    mods = load_modules(run_dir)
    got, _ = SG.load_arm(out_dir)
    rows = []
    for cid, obj in sorted(mods.items()):
        row = corpus.get(cid)
        if not row or _NEEDS not in row.get("quote", ""):
            continue
        try:
            mod = schema.validate(obj)
        except Exception:                                    # noqa: BLE001
            continue
        req = set(mod.requires)
        for i, c in enumerate(mod.concepts):
            if c.sig not in req:
                continue
            site = f"concepts[{i}]"
            seats = {}
            for seat in SG.SEATS:
                seats[seat] = SG.verdict_at((got.get(cid) or {}).get(seat),
                                            [site])
            rows.append({"run": label, "clause": cid, "site": site,
                         "name": c.name, "seats": seats})
    return rows


# ==========================================================================
#  3. ⭐ THE NULL. A detection rate is meaningless without the rate at which
#     the same seat returns the same verdict on ITEMS OF THE SAME KIND when
#     nothing is planted.
# ==========================================================================

def base_rates(label, out_dir):
    """Per seat, per item KIND: how often does a defect verdict come back at
    all? `4c unlicensed on 5 of 6 polarity sites` reads as a detection only if
    4c does NOT return `unlicensed` on most `asserts[…]` items anyway."""
    got, _ = SG.load_arm(out_dir)
    tally = {}
    for cid, seats_ in got.items():
        for seat, blob in seats_.items():
            if blob["judgements"] is None:
                continue
            for j in blob["judgements"]:
                if not isinstance(j, dict):
                    continue
                item = str(j.get("item", ""))
                kind = item.split("[")[0] if "[" in item else "claims"
                c = tally.setdefault((label, seat, kind),
                                     {"defect": 0, "unclear": 0, "pass": 0})
                v = j.get("verdict")
                c["defect" if v in SG.DEFECT_VERDICTS else
                  "unclear" if v == "unclear" else "pass"] += 1
    return tally


# ==========================================================================
#  rendering
# ==========================================================================

def render(pol, bor, base):
    L = []
    L.append("=" * 74)
    L.append("PER-CLASS DETECTION PROFILE FROM STORED REPLIES — what we can "
             "and cannot")
    L.append("fill without spending anything")
    L.append("=" * 74)
    L.append("")

    # --- polarity ---------------------------------------------------------
    judged = [r for r in pol if r["judged"]]
    L.append(f"CLASS `prefer-polarity`   ANCHOR: mechanical "
             f"(`checks.polarity_findings`, re-run here)")
    L.append(f"  findings on disk: {len(pol)}   of which stage 4 judged the "
             f"clause: {len(judged)}")
    L.append("")
    L.append(f"  {'run':9} {'clause':20} {'site':12} "
             + " ".join(f"{s:>16}" for s in SG.SEATS))
    for r in judged:
        L.append(f"  {r['run']:9} {r['clause']:20} {r['site']:12} "
                 + " ".join(
                     f"{_short(r['seats'][s]):>16}" for s in SG.SEATS))
    tot = {s: {"detected": 0, "missed": 0, "unclear-at-site": 0,
               "other": 0} for s in SG.SEATS}
    for r in judged:
        for s in SG.SEATS:
            st = r["seats"][s]["status"]
            tot[s][st if st in tot[s] else "other"] += 1
    L.append("")
    L.append(f"  {'seat':6} {'detected':>9} {'missed':>7} {'unclear':>8} "
             f"{'refused/na':>11}   detected/answered")
    for s in SG.SEATS:
        t = tot[s]
        ans = t["detected"] + t["missed"] + t["unclear-at-site"]
        L.append(f"  {s:6} {t['detected']:9} {t['missed']:7} "
                 f"{t['unclear-at-site']:8} {t['other']:11}   "
                 + (f"{t['detected']}/{ans}" if ans else "— (0 answered)")
                 + ("   (advisory)" if s == SG.ADVISORY else ""))
    anyd = sum(1 for r in judged if any(
        r["seats"][s]["status"] == "detected"
        for s in SG.SEATS if s != SG.ADVISORY))
    anya = sum(1 for r in judged if any(
        r["seats"][s]["status"] in ("detected", "missed", "unclear-at-site")
        for s in SG.SEATS if s != SG.ADVISORY))
    L.append("")
    L.append(f"  ⭐ ANY NON-ADVISORY SEAT: {anyd}/{anya} detected.")
    L.append("")
    L.append("  ⛔ THE SAME ROW, MINUS THE SEAT'S OWN BASE RATE ON `asserts[…]"
             "` ITEMS IN THE")
    L.append("     SAME RUN. A seat that flags every assertion it sees has "
             "not detected the")
    L.append("     planted one. `lift` is detection-rate minus base-rate; at "
             "or below 0 the")
    L.append("     seat's verdict at the site carries NO information about "
             "the defect.")
    L.append("")
    L.append(f"  {'run':9} {'seat':5} {'at site':>9} {'base rate on asserts':>22}"
             f" {'lift':>8}")
    for run in sorted({r["run"] for r in judged}):
        rs = [r for r in judged if r["run"] == run]
        for s in SG.SEATS:
            d = sum(1 for r in rs if r["seats"][s]["status"] == "detected")
            a = sum(1 for r in rs if r["seats"][s]["status"]
                    in ("detected", "missed", "unclear-at-site"))
            b = base.get((run, s, "asserts"))
            if not a or not b:
                continue
            bn = b["defect"] + b["unclear"] + b["pass"]
            br = b["defect"] / bn
            at = f"{d}/{a}={d / a:.2f}"
            nul = f"{b['defect']}/{bn}={br:.2f}"
            L.append(f"  {run:9} {s:5} {at:>9} {nul:>22} "
                     f"{d / a - br:>+8.2f}"
                     + ("   (advisory)" if s == SG.ADVISORY else ""))
    L.append("")
    L.append("  The seats' own words at the missed sites — read them, because "
             "several")
    L.append("  RESTATE THE CORRECT OPPOSITE MEANING and then pass the item "
             "anyway:")
    shown = 0
    for r in judged:
        for s in SG.SEATS:
            v = r["seats"][s]
            if v["status"] == "missed" and shown < 8:
                L.append(f"    {r['clause']}.{r['site']} [{s} "
                         f"{v.get('verdict')}] {v.get('reason', '')[:190]}")
                shown += 1
    L.append("")

    # --- borrowing --------------------------------------------------------
    L.append("PRECISION CELL `licensed borrowing`   ANCHOR: pipeline (the "
             "node's own NEEDS block)")
    L.append("  Every item below is a concept the node INSTRUCTED the "
             "translator to place in")
    L.append("  `requires`. The module did. A defect verdict on it is a FALSE "
             "POSITIVE.")
    L.append("")
    per = {}
    for r in bor:
        for s in SG.SEATS:
            c = per.setdefault((r["run"], s), {"flag": 0, "clean": 0,
                                               "unclear": 0, "other": 0})
            st = r["seats"][s]["status"]
            c["flag" if st == "detected" else
              "clean" if st == "missed" else
              "unclear" if st == "unclear-at-site" else "other"] += 1
    L.append(f"  {'run':9} {'seat':5} {'FLAGGED':>8} {'clean':>6} "
             f"{'unclear':>8} {'refused/na':>11}   FP rate")
    for run, s in sorted(per):
        c = per[(run, s)]
        ans = c["flag"] + c["clean"] + c["unclear"]
        L.append(f"  {run:9} {s:5} {c['flag']:8} {c['clean']:6} "
                 f"{c['unclear']:8} {c['other']:11}   "
                 + (f"{c['flag']}/{ans} = {c['flag'] / ans:.2f}"
                    if ans else "—")
                 + ("   (advisory)" if s == SG.ADVISORY else ""))
    L.append("")
    L.append(f"  borrowed items found across both stored runs: {len(bor)}")
    L.append("")

    # --- the null ---------------------------------------------------------
    L.append("⭐ THE NULL — how often each seat returns a DEFECT verdict when "
             "nothing is")
    L.append("   planted, by item kind. Every detection rate above must be "
             "read against")
    L.append("   the matching cell here, or it is not a measurement of "
             "anything.")
    L.append("")
    L.append(f"  {'run':9} {'seat':5} {'kind':10} {'defect':>7} "
             f"{'unclear':>8} {'pass':>6}   defect rate")
    for k in sorted(base):
        run, seat, kind = k
        c = base[k]
        n = c["defect"] + c["unclear"] + c["pass"]
        L.append(f"  {run:9} {seat:5} {kind:10} {c['defect']:7} "
                 f"{c['unclear']:8} {c['pass']:6}   "
                 f"{c['defect'] / n:.2f}  (n={n})"
                 + ("   (advisory)" if seat == SG.ADVISORY else ""))
    L.append("")

    # --- what cannot be filled -------------------------------------------
    L.append("⛔ CELLS THAT CANNOT BE FILLED FROM STORED REPLIES AT ANY PRICE")
    L.append("   — this is the hole the golden set exists to close.")
    for c in CLASSES:
        if c in UNFILLABLE:
            L.append(f"   {c:28} {UNFILLABLE[c]}")
    return "\n".join(L)


def _short(v):
    st = v["status"]
    if st == "detected":
        return f"DETECT:{v.get('verdict', '')}"
    if st == "missed":
        return f"miss:{v.get('verdict', '')}"
    return st


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    corpus = {r["id"]: r for r in json.load(
        open(os.path.join(GRAPH_V2, "node_corpus_all.json"),
             encoding="utf-8"))["clauses"]}
    pol, bor, base = [], [], {}
    for label, out_dir, run_dir in STORED:
        if not os.path.isdir(out_dir) or not os.path.isdir(run_dir):
            print(f"  ⚠️ {label}: missing {out_dir} or {run_dir}; skipped")
            continue
        pol += polarity_rows(label, out_dir, run_dir)
        bor += borrow_rows(label, out_dir, run_dir, corpus)
        base.update(base_rates(label, out_dir))
    print(render(pol, bor, base))
    if a.json:
        json.dump({"polarity": pol, "borrow": bor,
                   "base_rates": {"|".join(k): v for k, v in base.items()}},
                  open(a.json, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print(f"\n  rows written to {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
