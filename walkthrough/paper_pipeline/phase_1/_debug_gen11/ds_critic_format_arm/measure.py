#!/usr/bin/env python3
"""⭐ TIER 1 — THE ADJUDICATION-FREE MEASURES, computed by the SAME code path as
every arm arm F is compared against.

⛔ No ninth defect predicate.  `arms_review/floor.py`, `arms_review/measures.py`
and `licence_control/measure.py` are IMPORTED, not reimplemented.  Nothing here
involves a judgment of mine, which is why it leads the report.

SETS SCORED
  armA_turn1              the byte-identical drafts every arm here reviews
  armA_turn2(OPUS)        the frontier critic's ONE round on those same drafts
  armA_final(OPUS gold)   the converged modules
  armE_post               arm E's post-critic repairs (unforced, no ban)
  F1_post                 ban only
  F2_post                 ban + preserve

⭐ Restricted to the INTERSECTION of clauses all measured post-sets completed,
so every column is over the same clauses.  The per-cell own-sample figures are
printed too, and both are reported.

PLUS the two mechanically checkable classes the blind independent review
enumerated (`independent_review/02_classes.md`), reimplemented here in the four
lines the reviewer said they take:
  class B  a `licence: textual` entry whose body rests on an `assumed`/`world`
           predicate -- the weakest-licence-inherits rule, unpropagated
  class C  a `requires` entry that appears in no rule body ("dead requires")
⚠️ ARTIFACT MISMATCH, stated wherever these are used: the independent review read
the CONVERGED modules, not the turn-1 drafts arm F starts from.  Its COUNTS are
not arm F's baseline; only its CHECKS are borrowed, and they are recomputed on
every set in the table so the comparison is internal to this file.

READ-ONLY except `_debug_gen11/ds_critic_format_arm/measure.json`.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(G11, "arms_review"))
sys.path.insert(0, os.path.join(G11, "licence_control"))

import measure as LC                                          # noqa: E402
import measures as M                                          # noqa: E402

LOOP_OUT = os.path.join(G11, "ds_opus_loop", "out")


def post_modules(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".repair.module.json"):
            out[f.split(".")[0]] = json.load(
                open(os.path.join(d, f), encoding="utf-8"))
    return out


def loop_turn(n):
    out = {}
    for f in sorted(os.listdir(LOOP_OUT)):
        if f.endswith(f".turn{n}.raw.json"):
            try:
                out[f.split(".")[0]] = json.loads(
                    open(os.path.join(LOOP_OUT, f), encoding="utf-8").read())
            except json.JSONDecodeError:
                pass
    return out


# --------------------------------------------------------------- extra classes
def _preds(body):
    return set(re.findall(r"([a-z_][a-z0-9_]*)\s*\(", body or ""))


def weak_licences(m):
    """class B: predicates the module itself declares assumed/world."""
    w = set()
    for c in (m.get("concepts") or []):
        if c.get("licence") in ("assumed", "world"):
            w.add(c.get("name"))
    for o in (m.get("ontology") or []):
        if o.get("licence") in ("assumed", "world"):
            w |= _preds(o.get("atom") or "")
    return w


def class_b(m):
    """`licence: textual` entries whose body rests on a weak predicate."""
    w = weak_licences(m)
    out = []
    for fld in ("ontology", "asserts"):
        for e in (m.get(fld) or []):
            if e.get("licence") == "textual" and (_preds(e.get("body")) & w):
                out.append(f"{fld}:{(e.get('atom') or e.get('act') or '?')}")
    return out


def class_c(m):
    """`requires` entries appearing in no rule body ("dead requires")."""
    used = set()
    for fld in ("ontology", "asserts"):
        for e in (m.get(fld) or []):
            used |= _preds(e.get("body"))
    return [r for r in (m.get("requires") or [])
            if r.split("/")[0] not in used]


def extras(mods, restrict=None):
    b = c = 0
    bm = cm = 0
    for cid, m in mods.items():
        if restrict is not None and cid not in restrict:
            continue
        B, C = class_b(m), class_c(m)
        b += len(B)
        c += len(C)
        bm += bool(B)
        cm += bool(C)
    return {"classB": b, "classB_modules": bm,
            "classC": c, "classC_modules": cm}


def main():
    sets = {
        "armA_turn1": loop_turn(1),
        "armA_turn2(OPUS 1 round)": loop_turn(2),
        "armA_final(OPUS gold)": M.sets()["armA_CONVERGED(gold)"],
        "armE_post(no ban)": post_modules(
            os.path.join(G11, "ds_critic_arm", "out")),
        "F1_post(ban)": post_modules(os.path.join(HERE, "out_f1")),
        "F2_post(ban+preserve)": post_modules(os.path.join(HERE, "out_f2")),
    }
    posts = [k for k in ("armE_post(no ban)", "F1_post(ban)",
                         "F2_post(ban+preserve)") if sets[k]]
    inter = set.intersection(*[set(sets[k]) for k in posts]) if posts else set()

    out = {"_intersection": sorted(inter), "_own_sample": {}, "_paired": {}}
    hdr = (f"{'set':26s} {'n':>3s} {'clean':>5s} {'selfcite':>9s} {'err':>4s} "
           f"{'pol':>4s} {'asrt':>5s} {'bodiless':>8s} {'B':>4s} {'C':>4s}  closure")

    for tag, restrict in (("_own_sample", None), ("_paired", inter)):
        print(f"\n=== {tag} ===")
        print(hdr)
        for name, mods in sets.items():
            if not mods:
                continue
            r = LC.score(name, mods, restrict=restrict)
            r.update(extras(mods, restrict))
            out[tag][name] = r
            print(f"{name:26s} {r['n']:3d} {r['floor_clean']:5d} "
                  f"{r['selfcited_glosses']:4d}/{r['requires_names']:<4d} "
                  f"{r['errors']:4d} {r['polarity']:4d} {r['asserts']:5d} "
                  f"{r['bodiless_asserts']:8d} {r['classB']:4d} {r['classC']:4d}"
                  f"  {r['closure']}")

    print("\nper-clause asserts, turn1 -> each post (paired set):")
    t1 = out["_paired"]["armA_turn1"]["per_clause"]
    print(f"  {'clause':22s} {'T1':>4s} " +
          " ".join(f"{k.split('_')[0]:>6s}" for k in posts))
    for cid in sorted(inter):
        row = f"  {cid:22s} {t1[cid]['asserts']:4d} "
        for k in posts:
            row += f"{out['_paired'][k]['per_clause'][cid]['asserts']:6d} "
        print(row)

    json.dump(out, open(os.path.join(HERE, "measure.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
