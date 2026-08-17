#!/usr/bin/env python3
"""The two independent anchored populations, assembled once, labelled once.

⛔ NOTHING HERE MAKES A MODEL CALL. Everything is deterministic re-analysis of
bytes already on disk.

Two populations, deliberately NOT pooled:

  P-REF  the reference set (`_debug_gen11/reference_set/`). 25 clauses; 26
         classified edits between the ORIGINAL module (as the translator wrote
         it, in the read-only run dir) and the REFERENCE module (as a careful
         human reader corrected it). A detector aimed at class K is scored:
           positives = the ORIGINALS of clauses carrying a class-K edit
           negatives = (i) the REFERENCES of those same clauses (the defect is
                           gone; a detector still firing is a false positive)
                       (ii) the ORIGINALS of the 9 clauses with no edit at all
                           (untouched-faithful control)
         Population is REAL CORRECTIONS on real translator output.

  P-GOLD the golden set (`_debug_gen11/stage4_golden/`). 11 believed-correct
         bases; arms/arm1..3 carry ONE planted mutant each over an otherwise
         identical corpus; arm0 is the same 11 modules untouched. A detector
         aimed at class K is scored:
           positives = the mutated module at each arm/site with class K
           negatives = arm0's 11 controls, plus every NON-mutated module in
                       arms 1-3 (they are byte-identical to the source run)
         Population is PLANTED DEFECTS, mechanically applied and reversible.

The two populations share 8 clause ids but not a construction method: P-REF is
"a human found this wrong", P-GOLD is "we broke this on purpose". A detector
tuned on one is checked on the other. That is the whole point of carrying both
and it is the only overfitting control available at n=15 unarguable mutants.

⚠️ P-REF's 2 ARGUABLE edits (`diffs.json` confidence containing 'ARGUABLE') and
P-GOLD's 2 arguable mutants (`key.json` arguable=true) are carried but EXCLUDED
from every pooled cell, and reported on their own line, exactly as the two
source sets do it.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
if PHASE1 not in sys.path:
    sys.path.insert(0, PHASE1)

import schema  # noqa: E402

RUN = os.path.join(
    PHASE1, "resolve_runs", "graph_v2", "translation_sample", "runs",
    "20260815-124836-together-deepseek-v4-flash")
REF_DIR = os.path.join(GEN11, "reference_set", "modules")
DIFFS = os.path.join(GEN11, "reference_set", "diffs.json")
GOLD_KEY = os.path.join(GEN11, "stage4_golden", "key.json")
ARMS = os.path.join(GEN11, "stage4_golden", "arms")
CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "node_corpus_all.json")

#: A defect class is ARGUABLE when the source set says so. Never inferred here.
_ARGUABLE_MARK = "ARGUABLE"


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def corpus_by_id():
    return {c["id"]: c for c in _load(CORPUS)["clauses"]}


def span_of(clause_id):
    """The translator's own prompt for this clause — ESTABLISHES + SOURCE TEXT.

    This is what the module was written FROM, so it is the only honest place a
    document-grounded detector may read. Returns '' if absent.
    """
    p = os.path.join(RUN, clause_id + ".prompt_user.txt")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class Item:
    """One (module, label) pair a detector is run against.

    `truth` is the set of defect classes this module actually carries at the
    site level; `polarity` of the item for a given detector D is
    `D.klass in truth`.
    """

    __slots__ = ("pop", "clause_id", "variant", "obj", "truth", "note")

    def __init__(self, pop, clause_id, variant, obj, truth, arguable, note=""):
        self.pop = pop
        self.clause_id = clause_id
        self.variant = variant
        self.obj = obj
        #: ⚠️ PER-CLASS, not per-item. `truth` maps class -> is-this-one-
        #: arguable. An item-level arguable flag is too coarse and hides a
        #: confident defect behind an arguable one that happens to share a
        #: clause: l1108_1367_n014 carries a CONFIDENT invented-obligation and
        #: an ARGUABLE fact-as-deontic, and an item-level flag excluded the
        #: confident one from every pooled cell.
        self.truth = dict(truth)
        self.note = note

    @property
    def arguable(self):
        return bool(self.truth) and all(self.truth.values())

    def carries(self, classes):
        """(on_target, arguable) for a detector aimed at `classes`."""
        hit = {k: v for k, v in self.truth.items() if k in classes}
        return bool(hit), (bool(hit) and all(hit.values()))

    @property
    def key(self):
        return f"{self.pop}:{self.clause_id}:{self.variant}"

    def module(self):
        """Parsed `schema.Module`, or None if this artifact will not validate.

        A detector that needs the typed object gets None and must abstain; a
        detector reading raw JSON is unaffected. Both are legitimate — but a
        detector must not silently score an abstention as a negative, so
        `matrix.py` counts them in their own column.
        """
        try:
            return schema.validate(self.obj, clause_id=self.clause_id)
        except Exception:
            return None


def reference_population():
    """P-REF. Returns (items, class_counts).

    MEASURED, not inferred: the class labels are `diffs.json`'s own, and the
    'unchanged' negatives are the 9 clauses `diffs.json` reports as untouched.
    """
    d = _load(DIFFS)
    edits = d["edits"]
    by_clause = {}
    for e in edits:
        by_clause.setdefault(e["clause"], []).append(e)

    ref_names = sorted(f[:-5] for f in os.listdir(REF_DIR)
                       if f.endswith(".json"))
    items = []
    for cid in ref_names:
        my = by_clause.get(cid, [])
        classes = {}
        for e in my:
            arg = _ARGUABLE_MARK in (e.get("confidence") or "")
            # a class is arguable only if EVERY edit of that class is
            classes[e["class"]] = classes.get(e["class"], True) and arg
        arguable = bool(classes) and all(classes.values())
        orig_p = os.path.join(RUN, cid + ".json")
        orig = _load(orig_p)
        ref = _load(os.path.join(REF_DIR, cid + ".json"))
        if my:
            # positive: the original carries every class in `classes`
            items.append(Item("REF", cid, "original", orig, classes, arguable,
                              note="; ".join(sorted(classes))))
            # negative: the corrected module carries none of them
            items.append(Item("REF", cid, "reference", ref, {}, arguable,
                              note="corrected"))
        else:
            # untouched-faithful control, both copies identical by construction
            items.append(Item("REF", cid, "original", orig, {}, False,
                              note="untouched-faithful"))
    return items


def golden_population():
    """P-GOLD. Returns items over arm0 (controls) and arms 1-3 (mutants).

    Every module in an arm is included: the mutated one as a positive for its
    planted class, and every other module in the same arm as a negative. Arm
    non-mutant modules are byte-identical across arms, so they are emitted ONCE
    (from arm0) rather than four times — counting the same bytes four times
    would inflate specificity by 4x and that is exactly the kind of number this
    project has been burned by.
    """
    key = _load(GOLD_KEY)
    items = []
    mutated = {}          # (arm, clause_id) -> item record
    for it in key["items"]:
        if it["kind"] != "mutant":
            continue
        mutated[(it["arm"], it["clause_id"])] = it

    # positives
    for (arm, cid), it in sorted(mutated.items()):
        p = os.path.join(ARMS, f"arm{arm}", cid + ".json")
        items.append(Item("GOLD", cid, f"arm{arm}/{it['item_id']}", _load(p),
                          {it["class"]: bool(it.get("arguable"))}, False,
                          note=it["item_id"]))

    # ⛔ NEGATIVES ARE THE 11 BASES ONLY, NOT ALL 47 MODULES IN arm0.
    # arm0 is a full copy of the real run, and the other 36 modules in it are
    # UNVETTED translator output — the raw corpus, which demonstrably contains
    # real defects. Counting a detector's hit on one of those as a false
    # positive is not conservative, it is wrong: caught by this harness on its
    # first run, where `checks.polarity_mismatches` "false-positived" on
    # l1108_1367_n027, l1707_1973_n006, l1974_2125_n019, l2405_2473_n001 and
    # l4252_4482_n016 — all five of which the reference set independently
    # labels inverted-modality. Those are TRUE positives on unvetted text.
    # Only `key.json:bases` were read and marked FAITHFUL by a human.
    arm0 = os.path.join(ARMS, "arm0")
    for cid in sorted(key["bases"]):
        items.append(Item("GOLD", cid, "arm0",
                          _load(os.path.join(arm0, cid + ".json")),
                          {}, False, note="believed-correct control"))

    # The remaining arm0 modules are carried as an UNADJUDICATED stratum. A
    # detector's hits here are reported as a rate and NEVER scored, because no
    # one has established a right answer for them. They are the yield estimate,
    # not the specificity estimate.
    for f in sorted(os.listdir(arm0)):
        if not f.endswith(".json") or f in ("concepts.json", "run.json"):
            continue
        cid = f[:-5]
        if "." in cid or cid in set(key["bases"]):
            continue
        items.append(Item("GOLD", cid, "arm0-unvetted",
                          _load(os.path.join(arm0, f)), {}, False,
                          note="UNADJUDICATED"))
    return items


def is_scoreable(item):
    """False for the unadjudicated stratum — carried, reported, never scored."""
    return item.variant != "arm0-unvetted"


def all_items():
    return reference_population() + golden_population()


def main():
    ref = reference_population()
    gold = golden_population()
    for name, pop in (("P-REF", ref), ("P-GOLD", gold)):
        pos = [i for i in pop if i.truth]
        neg = [i for i in pop if not i.truth]
        print(f"{name}: {len(pop)} items  "
              f"({len(pos)} carrying a labelled defect, {len(neg)} clean)")
        cc = {}
        for i in pos:
            for k in i.truth:
                cc[k] = cc.get(k, 0) + 1
        for k in sorted(cc):
            arg = sum(1 for i in pos if i.truth.get(k))
            print(f"    {k:28s} {cc[k]:3d}"
                  + (f"  ({arg} arguable)" if arg else ""))
    bad = [i for i in ref + gold if i.module() is None]
    print(f"\nartifacts that do not validate: {len(bad)}")
    for i in bad:
        print("   ", i.key)


if __name__ == "__main__":
    main()
