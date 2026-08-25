#!/usr/bin/env python3
"""iteration1_score_attempt2.py — STEP 4 scorer (deterministic, $0).

Scores the attempt-2 confirmation wave for how-to-approach-tradeoffs
against ITERATION1_V5_PREDICTION.json. Venue-matched scoring, mirroring
attempt-1 (GEN_BLOCK1_SCORED.json): wave verdict per node; where a
3-seat panel ruled a node, the panel majority OVERRIDES the wave verdict
and the disagreement counts toward the split rate. If panel ruling files
are absent (budget-trimmed venue), scoring is wave-only and says so.

Outputs ITER1_ATTEMPT2_SCORED.json with:
  engaged_precision, decline_correctness, per-prediction PASS/FAIL,
  misses (engaged_FP / not_engaged_FN), and the P3 mechanism audit
  (governs signature of every fresh engaged-FP).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import satisfiability_census as SC

FD4 = os.path.join(HERE, "panel_run1", "fresh_draw4")
DRAW = os.path.join(HERE, "generalization_builds",
                    "draw_how-to-approach-tradeoffs_seed20260824.json")
PRED = os.path.join(HERE, "ITERATION1_V5_PREDICTION.json")
OUT = os.path.join(HERE, "ITER1_ATTEMPT2_SCORED.json")

GOV_DECL = {"substance_usefulness", "accuracy_calibration",
            "formatting_style", "objectivity_neutrality"}


def governs_profile(node):
    sig, ap, pa, ctx = SC.load_layers()
    ks = [k for k in sig if k.startswith(node + "|")]
    g = sorted({q for k in ks for q in sig[k]["governs"]})
    c = sorted({x for k in ks for x in sig[k].get("contexts", [])})
    return g, c


def main():
    draw = json.load(open(DRAW))
    engaged = list(draw["draw_engaged"])
    declined = list(draw["draw_not_engaged"])
    wave = json.load(open(os.path.join(
        FD4, "iter1_tradeoffs_attempt2_wave_rulings.json")))["rulings"]
    assert set(wave) == set(engaged) | set(declined), "wave node set mismatch"

    panels = {}
    for L in "ABC":
        p = os.path.join(FD4, f"iter1_tradeoffs_attempt2_panel_{L}_rulings.json")
        if os.path.exists(p):
            panels[L] = json.load(open(p))["rulings"]
    venue = "wave+panel" if len(panels) == 3 else "wave-only"

    verdicts, panel_rows, splits = {}, [], 0
    for n in wave:
        v = wave[n]["verdict"]
        if len(panels) == 3 and n in panels["A"]:
            vs = [panels[L][n]["verdict"] for L in "ABC"]
            maj = "relevant" if vs.count("relevant") >= 2 else "not_relevant"
            panel_rows.append({"node": n, "wave": v, "seats": vs,
                               "majority": maj, "split": len(set(vs)) > 1})
            if len(set(vs)) > 1:
                splits += 1
            v = maj
        verdicts[n] = v

    tp = [n for n in engaged if verdicts[n] == "relevant"]
    fp = [n for n in engaged if verdicts[n] == "not_relevant"]
    tn = [n for n in declined if verdicts[n] == "not_relevant"]
    fn = [n for n in declined if verdicts[n] == "relevant"]
    prec = len(tp) / len(engaged)
    decl = len(tn) / len(declined)

    p3_audit = []
    p3_violations = []
    for n in fp:
        g, c = governs_profile(n)
        only_tone_nonvuln = (set(g) == {"tone_manner"}
                             and "vulnerable_interaction" not in c)
        p3_audit.append({"node": n, "governs": g, "contexts": c,
                         "fixed_class_recurrence": only_tone_nonvuln})
        if only_tone_nonvuln:
            p3_violations.append(n)

    pred = json.load(open(PRED))
    checks = {
        "P1_primary (>=0.55)": ("PASS" if prec >= 0.55 else
                                "FAIL -> REVERT candidate B per V5"),
        "P2_point (0.65+/-0.10)": ("WITHIN" if 0.55 <= prec <= 0.75
                                   else "OUTSIDE"),
        "P3_mechanism (no fixed-class recurrence among engaged FPs)":
            ("PASS" if not p3_violations else f"FAIL: {p3_violations}"),
        "P4_decline (>=0.80)": "PASS" if decl >= 0.80 else "FAIL",
    }
    out = {
        "_": ("ITERATION 1 attempt-2 REALIZATION scored against the "
              "registered prediction (ITERATION1_V5_PREDICTION.json). "
              "Measures THE REPAIR, never transfer; attempt-1's 0.40 "
              "transfer verdict is frozen. Venue: " + venue + "."),
        "behaviour": "how-to-approach-tradeoffs",
        "venue": venue,
        "n": f"{len(engaged)}+{len(declined)}",
        "engaged_precision": round(prec, 3),
        "decline_correctness": round(decl, 3),
        "panel": panel_rows,
        "panel_split_rate": (f"{splits}/{len(panel_rows)}"
                             if panel_rows else "n/a"),
        "prediction_checks": checks,
        "misses": {"engaged_FP": sorted(fp), "not_engaged_FN": sorted(fn)},
        "p3_engaged_fp_audit": p3_audit,
        "attempt1_comparison": {
            "attempt1_engaged_precision_transfer_frozen": 0.40,
            "note": "comparison only; the two numbers answer different "
                    "questions (transfer vs repair)"},
        "verdicts": verdicts,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print("venue:", venue)
    print("engaged_precision:", round(prec, 3),
          " decline_correctness:", round(decl, 3))
    for k, v in checks.items():
        print(" ", k, "->", v)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
