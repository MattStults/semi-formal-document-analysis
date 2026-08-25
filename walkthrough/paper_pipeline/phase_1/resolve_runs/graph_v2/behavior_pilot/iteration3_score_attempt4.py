#!/usr/bin/env python3
"""iteration3_score_attempt4.py — STEP 4 scorer, committed BEFORE rulings.

Venue (ITERATION3_V5_PREDICTION.json): certified-Opus wave + 3 Opus panel
overrides + Opus probe; two Fable spot-checks with tripwires. Scores
attempt-4 against the registered P1-P4 and the P3 move gate over the 14
measured move-extension nodes (9 drawn gains + 5 probe).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FD4 = os.path.join(HERE, "panel_run1", "fresh_draw4")

DRAWN_GAINS = ['l1001_1107_n011', 'l1001_1107_n012', 'l1001_1107_n013',
               'l1108_1367_n018', 'l1707_1973_n037', 'l2474_2554_n009',
               'l3596_3876_n035', 'l3596_3876_n039', 'l3954_4251_n006']
PROBE = ['l1542_1706_n017', 'l3954_4251_n020', 'l3954_4251_n037',
         'l461_608_n008', 'l831_1000_n002']


def main():
    draw = json.load(open(os.path.join(
        HERE, "generalization_builds",
        "draw_how-to-approach-tradeoffs_seed20260826.json")))
    wave = json.load(open(os.path.join(
        FD4, "iter3_attempt4_wave_rulings.json")))["rulings"]
    panels = {L: json.load(open(os.path.join(
        FD4, f"iter3_attempt4_panel_{L}_rulings.json")))["rulings"]
        for L in "ABC"}
    probe = json.load(open(os.path.join(
        FD4, "iter3_probe_rulings.json")))["rulings"]
    eng, dec = draw["draw_engaged"], draw["draw_not_engaged"]
    assert set(wave) == set(eng) | set(dec)

    verdicts, prows, splits = {}, [], 0
    for n in wave:
        v = wave[n]["verdict"]
        if n in panels["A"]:
            vs = [panels[L][n]["verdict"] for L in "ABC"]
            maj = "relevant" if vs.count("relevant") >= 2 else "not_relevant"
            prows.append({"node": n, "wave": v, "seats": vs, "majority": maj,
                          "split": len(set(vs)) > 1})
            if len(set(vs)) > 1:
                splits += 1
            v = maj
        verdicts[n] = v

    tp = sum(1 for n in eng if verdicts[n] == "relevant")
    prec = tp / len(eng)
    tn = sum(1 for n in dec if verdicts[n] == "not_relevant")
    decl = tn / len(dec)

    # P3 move gate: 14 extension nodes
    ext = {}
    for n in DRAWN_GAINS:
        ext[n] = verdicts[n]
    for n in PROBE:
        ext[n] = probe[n]["verdict"]
    ext_rel = sum(1 for v in ext.values() if v == "relevant")
    p3 = ext_rel / len(ext)

    # spot-checks
    ws = json.load(open(os.path.join(
        FD4, "iter3_wave_spotcheck_fable_rulings.json")))["rulings"]
    ws_dis = [n for n in ws if ws[n]["verdict"] != verdicts.get(n)]
    ds = json.load(open(os.path.join(
        FD4, "iter3_dispute_spotcheck_fable_rulings.json")))["annotations"]
    marks = json.load(open(os.path.join(HERE, "arb_marks_final.json")))
    res = marks["dispute_resolutions"]
    ds_dis = [n for n in ds if ds[n]["mark"] != res.get(n)]

    checks = {
        "P1 (>=0.55)": ("PASS" if prec >= 0.55 else
                        "FAIL -> REVERT arbitrates_channel"),
        "P2 (0.65+/-0.12)": "WITHIN" if 0.53 <= prec <= 0.77 else "OUTSIDE",
        "P3 move gate (majority of 14 ext nodes relevant)":
            (f"PASS ({ext_rel}/14)" if p3 > 0.5 else
             f"FAIL ({ext_rel}/14) -> REVERT the channel regardless of P1"),
        "P4 (>=0.55)": "PASS" if decl >= 0.55 else "FAIL",
    }
    out = {
        "_": ("ITERATION 3 attempt-4 REALIZATION vs ITERATION3_V5_PREDICTION"
              ".json. Certified-Opus venue per A10 Q3 (final-run overlay "
              "rescinded, notes 0013). Measures THE REPAIR; attempt-1 "
              "transfer stays frozen."),
        "behaviour": "how-to-approach-tradeoffs",
        "engaged_precision": round(prec, 3),
        "decline_correctness": round(decl, 3),
        "panel": prows, "panel_split_rate": f"{splits}/{len(prows)}",
        "move_extension": {"verdicts": ext, "relevant": f"{ext_rel}/14"},
        "spot_checks": {
            "wave_vs_opus": (f"{len(ws_dis)}/8 disagreements "
                             f"({'TRIPWIRE FIRED' if len(ws_dis) >= 2 else 'ok'}): {ws_dis}"),
            "dispute_vs_panel": (f"{len(ds_dis)}/9 disagreements "
                                 f"({'TRIPWIRE FIRED' if len(ds_dis) >= 2 else 'ok'}): {ds_dis}")},
        "prediction_checks": checks,
        "misses": {
            "engaged_FP": sorted(n for n in eng if verdicts[n] == "not_relevant"),
            "not_engaged_FN": sorted(n for n in dec if verdicts[n] == "relevant")},
        "attempt_series": {"a1_transfer_frozen": 0.40, "a2_panel": 0.70,
                           "a3_panel": 0.55, "a4": round(prec, 3)},
        "verdicts": verdicts,
    }
    json.dump(out, open(os.path.join(HERE, "ITER3_ATTEMPT4_SCORED.json"), "w"),
              indent=1)
    print("engaged_precision:", round(prec, 3),
          " decline_correctness:", round(decl, 3))
    for k, v in checks.items():
        print(" ", k, "->", v)
    print("spot-checks:", out["spot_checks"])


if __name__ == "__main__":
    main()
