#!/usr/bin/env python3
"""The fix matrix: every fix ALONE, then CUMULATIVELY, on BOTH populations.

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/fix_matrix/matrix.py [--oracle DIR]

⛔ EVERY NUMBER IS A PAIR. A row prints detections AND false positives on both
control strata or it does not print. A check that flags more is not a better
check: seat 4c reached 48/86 flags on believed-correct modules and 14/14 on
the borrowed-name controls precisely by being read as "sensitive".

⛔ THE UNADJUDICATED STRATUM IS NEVER SCORED. 36 of arm0's modules are raw
translator output nobody has read. Their flag rate is printed as YIELD, in its
own column, and never as specificity. The first version of this harness scored
them as clean and "discovered" 6 false positives for the polarity check — all
6 of which the reference set independently labels inverted-modality. They were
true positives on unvetted text. See `population.golden_population`.

⛔ ARGUABLE ITEMS ARE EXCLUDED FROM POOLED CELLS and printed on their own line,
following `key.json` and `diffs.json`, which both label their own.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import detectors    # noqa: E402
import population   # noqa: E402


class Cell:
    __slots__ = ("tp", "fn", "fp", "tn", "arg_tp", "arg_fn", "yield_hit",
                 "yield_n", "off_target", "hits", "misses", "fps",
                 "per_class")

    def __init__(self):
        self.tp = self.fn = self.fp = self.tn = 0
        self.arg_tp = self.arg_fn = 0
        self.yield_hit = self.yield_n = 0
        self.off_target = []      # (item, classes it carries but was not aimed at)
        self.hits, self.misses, self.fps = [], [], []
        #: class -> [detected, missed]. ⛔ Reported ALWAYS, because a pooled
        #: recall over classes with different reachability is a fiction: F1
        #: scores 2/2 on `prefer-polarity` and 0/2 on `inverted-modality`, and
        #: the pooled 2/4 = 0.500 describes neither.
        self.per_class = {}

    @property
    def recall(self):
        d = self.tp + self.fn
        return (self.tp / d) if d else None

    @property
    def specificity(self):
        d = self.fp + self.tn
        return (self.tn / d) if d else None

    @property
    def discrimination(self):
        """recall - (1 - specificity). Zero for a detector that fires at its
        own base rate; this is the pooled measure the project reports as
        +0.091 for the current four-seat pool."""
        if self.recall is None or self.specificity is None:
            return None
        return self.recall - (1.0 - self.specificity)


def run_one(fixes, items, oracle):
    """Run the UNION of `fixes` (a list of names) over `items`.

    Cumulative = union of findings, which is how these checks would actually
    compose in `checks.run_checks`: each appends Findings, none suppresses
    another. Target classes are the union of the fixes' targets.
    """
    fns = [detectors.FIXES[f][0] for f in fixes]
    target = set()
    for f in fixes:
        target |= detectors.FIXES[f][1]

    cell = Cell()
    for it in items:
        found = []
        for fn in fns:
            found += fn(it, oracle=oracle)
        fired = bool(found)

        if not population.is_scoreable(it):
            cell.yield_n += 1
            cell.yield_hit += int(fired)
            continue

        on_target, is_arg = it.carries(target)
        if on_target:
            for k in it.truth:
                if k in target:
                    cell.per_class.setdefault(k, [0, 0])[
                        0 if fired else 1] += 1
            if is_arg:
                cell.arg_tp += int(fired)
                cell.arg_fn += int(not fired)
            elif fired:
                cell.tp += 1
                cell.hits.append(it)
            else:
                cell.fn += 1
                cell.misses.append(it)
        else:
            # ⛔ DEFECT-TRADING CHECK. An item carrying a defect of some OTHER
            # class is still a legitimate flag if the detector fires on it --
            # but it is NOT a hit for the class we aimed at, and it is NOT a
            # clean control either. It is recorded separately and never
            # silently absorbed into either column.
            if it.truth:
                if fired:
                    cell.off_target.append((it, sorted(it.truth)))
                continue
            if fired:
                cell.fp += 1
                cell.fps.append(it)
            else:
                cell.tn += 1
    return cell


def fmt(x, w=6):
    return "  --  " if x is None else f"{x:{w}.3f}"


def print_cell(label, cell, indent="  "):
    r, s, d = cell.recall, cell.specificity, cell.discrimination
    print(f"{indent}{label:26s} "
          f"detect {cell.tp:2d}/{cell.tp + cell.fn:<2d} = {fmt(r)}   "
          f"FP {cell.fp:2d}/{cell.fp + cell.tn:<2d} spec {fmt(s)}   "
          f"discrim {fmt(d)}   "
          f"[arguable {cell.arg_tp}/{cell.arg_tp + cell.arg_fn}]  "
          f"[yield {cell.yield_hit}/{cell.yield_n}]")
    for k in sorted(cell.per_class):
        d, m = cell.per_class[k]
        print(f"{indent}    by class: {k:28s} {d}/{d + m}")
    if cell.off_target:
        print(f"{indent}    off-target flags (other real defects, not scored):"
              f" {len(cell.off_target)}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", default=None,
                    help="cache dir for the one-bit model judge; without it "
                         "the live variants are SKIPPED, never faked")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args(argv)

    oracle = None
    if args.oracle:
        import oracle as oracle_mod
        oracle = oracle_mod.Oracle(args.oracle)

    ref = population.reference_population()
    gold = population.golden_population()
    pops = [("P-REF  (real corrections, 25 clauses / 26 edits)", ref),
            ("P-GOLD (planted mutants, 17 / 11 believed-correct bases)", gold)]

    order = ["F1-regex", "F1-general", "F2", "F2-wx", "F2-live", "F4-reach"]
    print("=" * 100)
    print("ALONE — each fix on its own, on each population independently")
    print("=" * 100)
    alone = {}
    for pname, pop in pops:
        print(f"\n{pname}")
        for f in order:
            try:
                c = run_one([f], pop, oracle)
            except detectors.NeedsOracle as e:
                print(f"  {f:26s} SKIPPED — {e}")
                continue
            alone[(pname, f)] = c
            print_cell(f, c)

    print()
    print("=" * 100)
    print("CUMULATIVE — stacked in mechanistic order, increment per step")
    print("=" * 100)
    for pname, pop in pops:
        print(f"\n{pname}")
        prev = None
        for label, stack in detectors.CUMULATIVE:
            try:
                c = run_one(stack, pop, oracle)
            except detectors.NeedsOracle as e:
                # ⛔ SKIP THE STEP, KEEP GOING. An unavailable fix must not
                # abort the rest of the ladder -- later rungs are still
                # measurable, they are just increments over a shorter stack.
                print(f"  {label:26s} SKIPPED — {e}")
                continue
            f = label
            label = "+" + f
            print_cell(label, c)
            if prev is not None:
                dd = (None if c.discrimination is None
                      or prev.discrimination is None
                      else c.discrimination - prev.discrimination)
                print(f"      increment: detections {c.tp - prev.tp:+d}, "
                      f"false positives {c.fp - prev.fp:+d}, "
                      f"discrimination "
                      f"{'--' if dd is None else format(dd, '+.3f')}")
            prev = c

    print()
    print("=" * 100)
    print("DEFECT-TRADING CHECK — does a step raise anything it was not "
          "aimed at?")
    print("=" * 100)
    print("""\
Read as: at each rung, FP on the believed-correct controls, plus the classes
the stack fires on that it was NOT aimed at. An off-target flag is not a bug --
those items really are defective -- but a rung that starts flagging a class it
does not target is flagging on something other than its criterion, and that is
the seat-4c failure in miniature.""")
    for pname, pop in pops:
        print(f"\n{pname}")
        prev = None
        for label, stack in detectors.CUMULATIVE:
            try:
                c = run_one(stack, pop, oracle)
            except detectors.NeedsOracle:
                continue
            off = {}
            for _i, cls in c.off_target:
                for k in cls:
                    off[k] = off.get(k, 0) + 1
            d = "" if prev is None else f"  (FP {c.fp - prev.fp:+d})"
            print(f"  {label:36s} FP {c.fp}/{c.fp + c.tn}{d}   "
                  f"unadjudicated yield {c.yield_hit}/{c.yield_n}")
            if off:
                print("       off-target classes: "
                      + ", ".join(f"{k}×{v}" for k, v in sorted(off.items())))
            else:
                print("       off-target classes: none")
            prev = c

    if args.detail:
        print()
        print("=" * 100)
        print("DETAIL — every miss and every false positive, named")
        print("=" * 100)
        for pname, pop in pops:
            for f in order:
                c = alone.get((pname, f))
                if not c:
                    continue
                if not (c.misses or c.fps or c.off_target):
                    continue
                print(f"\n{pname} :: {f}")
                for i in c.misses:
                    print(f"   MISS {i.key:46s} {i.note}")
                for i in c.fps:
                    print(f"   FP   {i.key:46s} {i.note}")
                for i, cl in c.off_target:
                    print(f"   OFF  {i.key:46s} carries {cl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
