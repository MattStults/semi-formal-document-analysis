#!/usr/bin/env python3
"""translation_fix_sim.py -- replay every stored repair round through the LIVE
checks, and price each proposed fix by the rounds it would have removed.

NEW FILE. Read-only over runs/ and repair_graveyard/. No network, no spend.

Two things it does, in order:

1. FAITHFULNESS. For every repair round, take the module that failed (the
   assistant turn the round repairs), run it through `schema.validate_all` as it
   stands today, and check the classes the census assigned are reproduced. A
   taxonomy that cannot be re-derived from the artifact is a story, not a
   measurement.

2. SIMULATION. For each proposed fix, count the rounds that would have had
   NOTHING left to report. A round dies only when its LAST finding goes -- a
   fix that removes four of a round's five findings saves nothing, and this is
   the whole reason the plan is ranked by round-kills and not by finding-counts.

   `autofix` is applied for real. Grammar fixes (schema shape / enum) cannot be
   applied to a stored artifact, so they are simulated by SUBTRACTING the
   classes they make unrepresentable -- which is exactly what "impossible in the
   grammar" means, and is stated as an assumption rather than a measurement.

Usage:
    .venv/bin/python translation_fix_sim.py            # newest prompt generation
    .venv/bin/python translation_fix_sim.py --gen all  # every generation
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter

import schema
import translate_autofix as A
import translation_repair_census as C

HERE = os.path.dirname(os.path.abspath(__file__))

#: Findings raised by the LINK stage (clingo, cross-module resolution), which a
#: single stored module cannot reproduce on its own. Rounds involving one are
#: excluded from the simulation and counted separately.
LINK_ONLY = {"asp-syntax-refused", "requires-unprovided", "unresolved-reference"}

CORPORA = [
    "resolve_runs/graph_v2/node_corpus_all.json",
    "../../../semi-formal-experiment/modelspec_clauses.json",
]

# --------------------------------------------------------------------------
# The proposed fixes, as the set of census classes each one makes impossible.
# Named to match TRANSLATION_FIX_PLAN.md.
# --------------------------------------------------------------------------
FIX_A = ("A  autofix (implemented, translate_autofix.py)", set())
FIX_B = ("B  cites/clause_id as a per-request const",
         {"citation-not-in-corpus", "clause-id-mismatch"})
FIX_C = ("C  requires/inputs entries carry name+arity+gloss",
         {"borrowed-without-gloss", "inputs-entry-not-name-arity",
          "requires-inputs-overlap"})
FIX_D = ("D  ontology split into rules (body required) and ground facts",
         {"unsafe-variable"})
FIX_E = ("E  acts carry their own closure; asserts reference a declared act",
         {"closure-missing", "closure-ungoverned", "act-not-in-acts"})
FIX_F = ("F  body literals carry their origin (the residual class)",
         {"undeclared-body-name"})


def corpus_ids(root):
    ids = set()
    for p in CORPORA:
        try:
            d = json.load(open(os.path.join(root, p)))
        except Exception:
            continue
        recs = d.get("clauses") if isinstance(d, dict) else d
        ids |= {r["id"] for r in recs if isinstance(r, dict) and "id" in r}
    return ids


def load(root, gen):
    rounds, clauses, first = C.collect_rounds(root)
    gens, hashes = C.prompt_generations(root)
    out_cpt, _mc, cshare, _n = C.calibrate(C.usage_rows())
    for r in rounds:
        r["gen"] = gens.get(r["run"])
        r["cost"] = C.price_round(r, out_cpt, out_cpt, cshare)
    if gen != "all":
        g = max(hashes) if gen in (None, "newest") else int(gen)
        rounds = [r for r in rounds if r["gen"] == g]
        label = f"prompt generation {g} ({hashes[g]})"
    else:
        label = "all prompt generations"
    return rounds, label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--gen", default="newest",
                    help="'newest' (default), 'all', or a generation number")
    args = ap.parse_args()

    rounds, label = load(args.root, args.gen)
    ids = corpus_ids(args.root)

    link = [r for r in rounds if set(r["classes"]) & LINK_ONLY]
    rounds = [r for r in rounds if not (set(r["classes"]) & LINK_ONLY)]
    total, cost = len(rounds), sum(r["cost"] for r in rounds)

    print(f"=== {label} ===")
    print(f"schema-stage repair rounds: {total}  (${cost:.4f})")
    print(f"link-stage rounds excluded: {len(link)} "
          f"(a stored module cannot reproduce a cross-module finding)")
    print()

    # ---------------- 1. faithfulness -------------------------------------
    faithful = 0
    for r in rounds:
        obj = json.loads(r["failing_raw"])
        _m, br = schema.validate_all(obj, clause_id=r["clause"],
                                     known_clause_ids=ids | {r["clause"]})
        got = {C.classify("x", b.message) for b in br}
        if set(r["classes"]) <= got:
            faithful += 1
    print(f"FAITHFULNESS: the census classes are re-derived from the stored "
          f"module by the live checks in {faithful}/{total} rounds "
          f"({faithful/total:.0%})")
    print()

    # ---------------- 2. simulation ---------------------------------------
    def sim(impossible):
        killed, saved, residual = 0, 0.0, Counter()
        for r in rounds:
            obj = json.loads(r["failing_raw"])
            fixed, _fx = A.autofix(obj)
            _m, br = schema.validate_all(
                fixed, clause_id=r["clause"],
                known_clause_ids=ids | {r["clause"]})
            left = {C.classify("x", b.message) for b in br} - impossible
            for x in left:
                residual[x] += 1
            if not left:
                killed += 1
                saved += r["cost"]
        return killed, saved, residual

    ladder = [
        [FIX_A],
        [FIX_A, FIX_B],
        [FIX_A, FIX_B, FIX_C],
        [FIX_A, FIX_B, FIX_C, FIX_D],
        [FIX_A, FIX_B, FIX_C, FIX_D, FIX_E],
        [FIX_A, FIX_B, FIX_C, FIX_D, FIX_E, FIX_F],
    ]
    print(f"{'plan':56} {'rounds killed':>14} {'$ saved':>10}")
    print("-" * 82)
    last = None
    for step in ladder:
        imp = set().union(*[s for _n, s in step])
        k, s, res = sim(imp)
        name = " + ".join(n.split()[0] for n, _ in step)
        print(f"{name:56} {k:6}/{total} {k/total:5.0%} {s:9.4f} {s/cost:5.0%}")
        last = res
    print()
    print("each fix, alone, on top of the autofix:")
    for n, s in (FIX_B, FIX_C, FIX_D, FIX_E, FIX_F):
        k, sv, _ = sim(s)
        print(f"  {n:54} {k:4}/{total} {k/total:4.0%} ${sv:.4f}")
    print()
    print("residual classes with the whole plan applied except F:")
    imp = set().union(*[s for _n, s in ladder[-2]])
    _k, _s, res = sim(imp)
    for k2, v in res.most_common(15):
        print(f"  {v:4} {k2}")


if __name__ == "__main__":
    main()
