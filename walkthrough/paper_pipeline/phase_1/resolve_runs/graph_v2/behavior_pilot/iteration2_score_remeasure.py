#!/usr/bin/env python3
"""iteration2_score_remeasure.py — scorer for the void-ruling re-measurement
(ITER2_VOID_RULING_AND_REMEASURE_PREREG.md). Committed BEFORE any ruling
exists. Deterministic, $0.

Assembles: standing panel-tier truth (recomputed from committed artifacts,
never re-measured) + the 3 new certified-Opus panel majorities over the
62-node packet. Then:
  - MOVE GATE: panel-tier precision over the full 16-node extension
    (threshold 0.60; below -> revert executes).
  - attempt-2 / attempt-3 rescored at uniform panel tier, both sides;
    raw wave numbers reported alongside.
  - Fable spot-check vs Opus majorities; tripwire >=3/13 disagreements.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FD4 = os.path.join(HERE, "panel_run1", "fresh_draw4")

GAINS = ['l171_426_n014', 'l171_426_n016', 'l171_426_n019', 'l1_170_n026',
         'l1_170_n040', 'l1_170_n043', 'l1_170_n046', 'l1_170_n054',
         'l1_170_n057', 'l1_170_n059', 'l1_170_n060', 'l1_170_n091',
         'l3041_3146_n010', 'l3383_3501_n010', 'l4572_4692_n003',
         'l699_796_n010']


def standing_panel_tier():
    pt = {}
    e1 = json.load(open(os.path.join(FD4, "ITER1_TRADEOFFS_ESCALATION_RESULT.json")))
    for r in e1["panel"]:
        pt[r["node"]] = r["majority"]
    for r in e1["escalation2"]["panel"]:
        pt[r["node"]] = r["majority"]
    p1 = {L: json.load(open(os.path.join(
        FD4, f"gen_how-to-approach-tradeoffs_panel_{L}_rulings.json")))["rulings"]
        for L in "ABC"}
    for n in p1["A"]:
        vs = [p1[L][n]["verdict"] for L in "ABC"]
        pt[n] = "relevant" if vs.count("relevant") >= 2 else "not_relevant"
    a2s = json.load(open(os.path.join(HERE, "ITER1_ATTEMPT2_SCORED.json")))
    for r in a2s["panel"]:
        pt[r["node"]] = r["majority"]
    e2 = json.load(open(os.path.join(FD4, "ITER2_ESCALATION_RESULT.json")))
    pt.update(e2["truth"])
    a3s = json.load(open(os.path.join(HERE, "ITER2_ATTEMPT3_SCORED.json")))
    for r in a3s["panel"]:
        pt[r["node"]] = r["majority"]
    return pt


def main():
    pt = standing_panel_tier()
    pkt = [it["node"] for it in json.load(open(os.path.join(
        FD4, "iter2_remeasure_panel.json")))["items"]]
    seats = {L: json.load(open(os.path.join(
        FD4, f"iter2_remeasure_panel_{L}_rulings.json")))["rulings"]
        for L in "ABC"}
    for L in "ABC":
        assert set(seats[L]) == set(pkt), f"seat {L} node mismatch"
        for r in seats[L].values():
            assert r["verdict"] in ("relevant", "not_relevant") and r.get("grounds")
    new_maj, splits = {}, []
    for n in pkt:
        vs = [seats[L][n]["verdict"] for L in "ABC"]
        m = "relevant" if vs.count("relevant") >= 2 else "not_relevant"
        new_maj[n] = m
        if len(set(vs)) > 1:
            splits.append(n)
    truth = dict(pt)
    for n, v in new_maj.items():
        assert n not in pt, f"{n} had standing panel truth; packet must exclude it"
        truth[n] = v

    # spot-check
    spot_p = os.path.join(FD4, "iter2_remeasure_spotcheck_fable_rulings.json")
    spot = {}
    tripwire = "NOT RUN"
    if os.path.exists(spot_p):
        spot = json.load(open(spot_p))["rulings"]
        dis = [n for n in spot if spot[n]["verdict"] != new_maj.get(n)]
        tripwire = (f"FIRED ({len(dis)}/13 disagreements: {dis}) — HALT"
                    if len(dis) >= 3 else
                    f"not fired ({len(dis)}/13 disagreements: {dis})")

    # move gate: full 16-node extension
    ext = {n: truth[n] for n in GAINS}
    ext_prec = sum(1 for v in ext.values() if v == "relevant") / len(GAINS)
    gate = "MOVE STANDS" if ext_prec >= 0.60 else "REVERT EXECUTES"

    def rescore(draw_file, wave_file, panel_scored_key):
        d = json.load(open(os.path.join(HERE, "generalization_builds", draw_file)))
        wave = json.load(open(os.path.join(FD4, wave_file)))["rulings"]
        eng, dec = d["draw_engaged"], d["draw_not_engaged"]
        raw_tp = sum(1 for n in eng if wave[n]["verdict"] == "relevant")
        raw_tn = sum(1 for n in dec if wave[n]["verdict"] == "not_relevant")
        pt_tp = sum(1 for n in eng if truth[n] == "relevant")
        pt_tn = sum(1 for n in dec if truth[n] == "not_relevant")
        return {"raw_wave": {"engaged_precision": raw_tp / 20,
                             "decline_correctness": raw_tn / 20},
                "panel_tier": {"engaged_precision": pt_tp / 20,
                               "decline_correctness": pt_tn / 20},
                "panel_tier_misses": {
                    "engaged_FP": sorted(n for n in eng if truth[n] == "not_relevant"),
                    "not_engaged_FN": sorted(n for n in dec if truth[n] == "relevant")}}

    a2 = rescore("draw_how-to-approach-tradeoffs_seed20260824.json",
                 "iter1_tradeoffs_attempt2_wave_rulings.json", "a2")
    a3 = rescore("draw_how-to-approach-tradeoffs_seed20260825.json",
                 "iter2_attempt3_wave_rulings.json", "a3")

    out = {
        "_": ("RE-MEASUREMENT SCORED per ITER2_VOID_RULING_AND_REMEASURE_"
              "PREREG.md — uniform panel tier on the frozen draws, "
              "full-extension move gate, one shot, FINAL."),
        "move_gate": {"extension_precision": round(ext_prec, 3),
                      "threshold": 0.60, "outcome": gate,
                      "extension_verdicts": ext},
        "attempt2": a2, "attempt3": a3,
        "attempt1_transfer_frozen": 0.40,
        "new_panel_majorities": new_maj,
        "panel_splits": splits,
        "spot_check": {"tripwire": tripwire,
                       "rulings": {n: spot[n]["verdict"] for n in spot}},
    }
    json.dump(out, open(os.path.join(HERE, "ITER2_REMEASURE_SCORED.json"), "w"),
              indent=1)
    print("MOVE GATE:", gate, f"(extension precision {ext_prec:.3f})")
    for k, a in (("attempt2", a2), ("attempt3", a3)):
        print(f"{k}: raw {a['raw_wave']['engaged_precision']:.2f}/"
              f"{a['raw_wave']['decline_correctness']:.2f}  panel-tier "
              f"{a['panel_tier']['engaged_precision']:.2f}/"
              f"{a['panel_tier']['decline_correctness']:.2f}")
    print("spot-check:", tripwire)
    print("splits:", len(splits))


if __name__ == "__main__":
    main()
