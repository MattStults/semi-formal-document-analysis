#!/usr/bin/env python3
"""The honest ceiling: of the reference set's 26 known edits, how many would
still be missed after every fix on the table?

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/fix_matrix/ceiling.py \
            --oracle _debug_gen11/fix_matrix/oracle_cache

Two coverage sources, and they are NOT the same kind of number:

  MEASURED   the offline check stack (F1 + F2-wx) run directly on the 25
             ORIGINAL modules. Every cell here is this harness firing on the
             actual bytes the translator produced.

  INFERRED   the four-seat pool. The seats have never been run on the
             reference set — only on the golden set — so seat coverage of a
             reference edit is a per-CLASS transfer from `score_golden.py`,
             not an observation. It is printed in its own column and never
             added to the measured one without the label.

⛔ WHY THE CEILING IS NOT "1 - RECALL". A class with recall 1.0 on 2 planted
items is not a solved class. The ceiling below counts an edit as COVERED only
if some instrument fires on the clause carrying it; it does not check that the
instrument named the right site or the right class. That makes this number an
UPPER BOUND on coverage — the true figure is lower — and it is reported as
such rather than as an achievement.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import detectors    # noqa: E402
import population   # noqa: E402

#: Per-class ANY-SEAT recall on the golden set, from
#: `score_golden.py --judge H2=_debug_gen11/seat_fix/out_h2`, the best seat arm
#: on disk. ⚠️ TRANSFERRED, NOT MEASURED on P-REF. Denominators are 1-3 items,
#: so a 1.0 here is one or two planted specimens and nothing more.
SEAT_RECALL_GOLD = {
    "disjunction-as-conjunction": (2, 2),
    "dropped-obligation":         (1, 2),
    "fact-as-deontic":            (1, 1),
    "invented-obligation":        (1, 1),
    "inverted-modality":          (2, 2),
    "prefer-polarity":            (2, 2),
    "scope-drift-narrow":         (2, 2),
    "scope-drift-widen":          (3, 3),
}

#: Classes in the reference set with NO golden specimen at all. Seat coverage
#: of these is UNKNOWN — not zero, not one. Printing them as 0 would understate
#: and as 1 would overstate; they get their own row.
NO_GOLDEN_SPECIMEN = {"dropped-content", "weakened-modality", "other"}

STACK = ["F1-regex", "F1-general", "F2-wx"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", default=None)
    args = ap.parse_args(argv)

    oracle = None
    if args.oracle:
        import oracle as om
        oracle = om.Oracle(args.oracle)

    diffs = json.load(open(os.path.join(GEN11, "reference_set", "diffs.json"),
                           encoding="utf-8"))
    edits = diffs["edits"]

    items = {i.clause_id: i for i in population.reference_population()
             if i.variant == "original"}

    fired = {}
    for cid, it in items.items():
        f = []
        for name in STACK:
            fn = detectors.FIXES[name][0]
            try:
                f += fn(it, oracle=oracle)
            except detectors.NeedsOracle:
                pass
        fired[cid] = bool(f)

    print("=" * 96)
    print("THE 26 KNOWN EDITS — covered by the offline stack (MEASURED) / by "
          "the seats (INFERRED)")
    print("=" * 96)
    print(f"{'clause':22s} {'class':28s} {'offline':>8s} {'seat(gold)':>12s}"
          f"  arguable")
    cov_off = cov_any = 0
    per_class = {}
    for e in edits:
        cid, cls = e["clause"], e["class"]
        off = fired.get(cid, False)
        if cls in NO_GOLDEN_SPECIMEN:
            seat = "unknown"
            seat_ok = None
        else:
            d, n = SEAT_RECALL_GOLD[cls]
            seat = f"{d}/{n}"
            seat_ok = d > 0
        arg = "ARGUABLE" if "ARGUABLE" in (e.get("confidence") or "") else ""
        cov_off += int(off)
        cov_any += int(off or bool(seat_ok))
        per_class.setdefault(cls, [0, 0, 0])
        per_class[cls][0] += 1
        per_class[cls][1] += int(off)
        per_class[cls][2] += int(off or bool(seat_ok))
        print(f"{cid:22s} {cls:28s} {'HIT' if off else '—':>8s} {seat:>12s}"
              f"  {arg}")

    n = len(edits)
    print("\n" + "-" * 96)
    print(f"MEASURED  offline stack ({' + '.join(STACK)}) reaches the clause "
          f"of {cov_off}/{n} edits = {cov_off / n:.0%}")
    print(f"          -> STILL MISSED, measured: {n - cov_off}/{n} = "
          f"{(n - cov_off) / n:.0%}")
    print(f"INFERRED  offline stack OR a seat of the same class reaches "
          f"{cov_any}/{n} = {cov_any / n:.0%}")
    print(f"          -> STILL MISSED, inferred ceiling: {n - cov_any}/{n} = "
          f"{(n - cov_any) / n:.0%}")

    print("\nper class")
    print(f"{'class':28s} {'n':>3s} {'offline':>8s} {'+seats':>8s}")
    for cls in sorted(per_class):
        t, o, a = per_class[cls]
        mark = "  ⚠️ no golden specimen" if cls in NO_GOLDEN_SPECIMEN else ""
        print(f"{cls:28s} {t:3d} {o:8d} {a:8d}{mark}")

    print("\n" + "=" * 96)
    print("WHAT THE CEILING NUMBER DOES NOT SAY")
    print("=" * 96)
    print("""\
* It is CLAUSE-level. An instrument that fires on the right clause for the
  wrong reason counts as covered. The true site-and-class-correct figure is
  strictly lower and this harness cannot produce it without a per-site
  adjudication of every seat reason, which is a separate exercise.
* The three classes with no golden specimen -- dropped-content (6 edits),
  other (4), weakened-modality (1) -- are 11 of the 26. NOTHING on the table
  targets them. dropped-content alone is the largest class in the reference
  set and no fix in this matrix, and no seat with a measured number, addresses
  it. That is the honest headline: the five fixes cover the classes they were
  designed for and leave the biggest class untouched.
* n = 26 edits over 25 clauses, and 15 unarguable planted mutants on the other
  population. Every recall in this file has a single-digit denominator.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
