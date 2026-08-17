#!/usr/bin/env python3
"""Every arm's difference from arm A turn 1, on the SAME measures, against the
null's floor. Turn-1 vs turn-1 throughout: arm A' is a turn-1 draw, so the only
like-for-like comparator is arm A's turn-1 draft, not its converged module.

READ-ONLY except `_debug_gen11/arm_aprime/vs_arms.json`.
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "arms_review")))
sys.path.insert(0, HERE)
import floor                                                  # noqa: E402
import measures                                               # noqa: E402
import measure as M                                           # noqa: E402

ARMS = ["list_in_prompt", "list_in_prompt_insample", "examples_arm",
        "retrieval_arm", "forced_verdict_arm", "selfreview_arm",
        "bucketed_arm", "decompose_arm"]


def main():
    A = M.armA_turn1()
    sets = {"arm A-PRIME (NULL)": M.aprime()}
    for a in ARMS:
        sets[a] = floor.modules_for(a)

    rows = {}
    for name, S in sets.items():
        shared = sorted(set(A) & set(S))
        pa = {c: M.profile(A[c], c) for c in shared}
        pp = {}
        for c in shared:
            try:
                pp[c] = M.profile(S[c], c)
            except Exception:                                 # noqa: BLE001
                pp[c] = None
        shared = [c for c in shared if pp[c]]
        n = len(shared)

        def F(key):
            return sum(pa[c][key] != pp[c][key] for c in shared)

        mech = sum((pa[c]["outcome"], pa[c]["n_errors"])
                   != (pp[c]["outcome"], pp[c]["n_errors"]) for c in shared)
        cl = collections.Counter()
        for c in shared:
            cl.update(pp[c]["closure"])
        rows[name] = {
            "n": n,
            "mech_floor_diff": mech,
            "mech_pct": round(100 * mech / n, 1) if n else None,
            "outcome_diff": F("outcome"),
            "selfcite_count_diff": F("selfcited"),
            "closure_diff": F("closure"),
            "clauses_with_selfcite": sum(bool(pp[c]["selfcited"])
                                         for c in shared),
            "unclear": cl.get("unclear", 0),
            "closure_mix": dict(cl),
            "exact_identical_to_A": sum(pa[c]["canon"] == pp[c]["canon"]
                                        for c in shared),
            "sig_identical_to_A": sum(pa[c]["sig"] == pp[c]["sig"]
                                      for c in shared),
        }

    null = rows["arm A-PRIME (NULL)"]
    hdr = (f"{'arm':26s} {'n':>3s} {'mech-floor diff':>16s} {'selfcite cl':>12s} "
           f"{'unclear':>8s} {'exact==A':>9s} {'sig==A':>7s}")
    print(hdr)
    print("-" * len(hdr))
    for name, r in rows.items():
        mark = ""
        if r["n"] == 0:
            print(f"{name:26s}   0   NO OVERLAP with the 17 (out-of-sample arm)")
            continue
        if name != "arm A-PRIME (NULL)":
            mark = "  <= FLOOR" if r["mech_pct"] <= null["mech_pct"] else "  > floor"
        print(f"{name:26s} {r['n']:3d} {r['mech_floor_diff']:6d} "
              f"({r['mech_pct']:5.1f}%) {r['clauses_with_selfcite']:12d} "
              f"{r['unclear']:8d} {r['exact_identical_to_A']:9d} "
              f"{r['sig_identical_to_A']:7d}{mark}")
    json.dump(rows, open(os.path.join(HERE, "vs_arms.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
