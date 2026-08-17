#!/usr/bin/env python3
"""MECHANICAL measurement for ARM E, computed by the SAME code path as every
arm it is compared against.

⛔ No ninth defect predicate.  `arms_review/floor.py`, `arms_review/measures.py`
and `licence_control/measure.py` are IMPORTED, not reimplemented, so arm E lands
in the published cross-arm table with the published denominators.

Sets scored, all restricted to the 13 clauses whose critic call completed, so
every column is over the SAME clauses:
  armA_turn1     the byte-identical drafts every arm here reviews
  armA_turn2     the OPUS critic's one-round result on those same drafts
  armA_final     the Opus loop's converged modules (the gold)
  armE_post      this arm's post-critic repair modules
plus arm D (selfreview) over its own 9, for reference.

READ-ONLY except `_debug_gen11/ds_critic_arm/measure.json`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(G11, "arms_review"))
sys.path.insert(0, os.path.join(G11, "licence_control"))

import measure as LC                                          # noqa: E402
import measures as M                                          # noqa: E402

LOOP_OUT = os.path.join(G11, "ds_opus_loop", "out")


def arme_post():
    out = {}
    for f in sorted(os.listdir(os.path.join(HERE, "out"))):
        if f.endswith(".repair.module.json"):
            out[f.split(".")[0]] = json.load(
                open(os.path.join(HERE, "out", f), encoding="utf-8"))
    return out


def loop_turn(n):
    out = {}
    for f in sorted(os.listdir(LOOP_OUT)):
        if f.endswith(f".turn{n}.raw.json"):
            cid = f.split(".")[0]
            try:
                out[cid] = json.loads(
                    open(os.path.join(LOOP_OUT, f), encoding="utf-8").read())
            except json.JSONDecodeError:
                pass
    return out


if __name__ == "__main__":
    post = arme_post()
    keep = set(post)
    sets = {
        "armA_turn1": loop_turn(1),
        "armA_turn2(OPUS 1 round)": loop_turn(2),
        "armA_final(OPUS gold)": M.sets()["armA_CONVERGED(gold)"],
        "armE_post(DS critic)": post,
    }
    out = {}
    for name, mods in sets.items():
        rec = LC.score(name, mods, restrict=keep)
        out[name] = rec
        print(f"{name:26s} n={rec['n']:3d} clean={rec['floor_clean']:3d} "
              f"selfcite={rec['selfcited_glosses']:3d}/{rec['requires_names']:3d} "
              f"err={rec['errors']:3d} pol={rec['polarity']:3d} "
              f"asrt={rec['asserts']:3d} bodiless={rec['bodiless_asserts']:3d} "
              f"closure={rec['closure']}")
    # arm D, over its own completed 9, for reference only
    d = M.sets()["selfreview_arm"]
    rec = LC.score("selfreview_arm", d)
    out["selfreview_arm(D, own 9)"] = rec
    print(f"{'selfreview_arm(D)':26s} n={rec['n']:3d} clean={rec['floor_clean']:3d} "
          f"selfcite={rec['selfcited_glosses']:3d}/{rec['requires_names']:3d} "
          f"err={rec['errors']:3d} pol={rec['polarity']:3d} "
          f"asrt={rec['asserts']:3d} bodiless={rec['bodiless_asserts']:3d} "
          f"closure={rec['closure']}")
    json.dump(out, open(os.path.join(HERE, "measure.json"), "w"), indent=1)
    print("\nper-clause floor_clean turn1 -> post:")
    t1 = out["armA_turn1"]["per_clause"]
    pp = out["armE_post(DS critic)"]["per_clause"]
    for cid in sorted(keep):
        print(f"  {cid:20s} {t1[cid]['outcome']:12s} -> {pp[cid]['outcome']:12s} "
              f"clean {int(t1[cid]['floor_clean'])}->{int(pp[cid]['floor_clean'])} "
              f"err {t1[cid]['errors']}->{pp[cid]['errors']} "
              f"selfcite {t1[cid]['selfcited']}->{pp[cid]['selfcited']} "
              f"pol {t1[cid]['polarity']}->{pp[cid]['polarity']} "
              f"bodiless {t1[cid]['bodiless']}->{pp[cid]['bodiless']}")
