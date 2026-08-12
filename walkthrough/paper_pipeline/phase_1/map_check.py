#!/usr/bin/env python3
"""Can a clause's BORROWED condition be satisfied by another clause's DEFINITION?

⭐ THE QUESTION THE WHOLE `resolve_runs/` LINE HAS BEEN CIRCLING, and it has never
actually been asked, because it cannot be asked without both halves on the table.
`[RAN]` 13 of 593 clauses are translated and **0 of 12 borrowed conditions find a
provider anywhere** — not because matching fails, but because the clauses that would
define them have never been translated.

⛔ AND AN EARLIER FRAMING OF THIS WAS WRONG, recorded so it is not repeated. Two runs
of ONE clause were compared, found to carve the clause differently, and that was
reported as evidence about linking. It is not: two runs of one clause are
ALTERNATIVES — one is kept and the other discarded — so they never need to link to
each other. That comparison measures REPRODUCIBILITY. Linking is a different pairing
entirely: **one clause's borrow against a DIFFERENT clause's head.**

⚠️ ONE-TO-ONE WAS NEVER THE REQUIREMENT EITHER. Matt's design says a section defines
several things and needs several things, so a need may be met by a combination of
what is on offer. This script therefore reports FOUR outcomes per borrow, not two:

    exact        a provider head has the same name AND arity — links today
    shape        same idea, different arity or decomposition — needs a BRIDGING
                 RULE (`p(I) :- q(I,J), r(J,I).`), which is a design decision and
                 not an impossibility
    described    no head matches, but a provider CONCEPT describes the same idea —
                 the definition exists in the corpus without being derivable
    absent       nothing on offer resembles it

⭐ `shape` IS THE INTERESTING COLUMN. `exact` means the naive lookup works; `absent`
means the corpus is still too small; `shape` is the case that decides whether the
linking design needs a bridge-builder, and how often.

⚠️ THE DESCRIPTION COMPARISON IS A JUDGEMENT, NOT A STRING TEST. `[RAN]` two glosses
that plainly mean the same thing scored 0.44 by text similarity, so this script does
NOT decide `described` mechanically — it prints the candidate pairs for a reader and
counts only what a reader confirms. A string threshold here would manufacture a
number nobody could defend.
"""

import argparse
import glob
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import link                                                    # noqa: E402
import schema                                                  # noqa: E402


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def heads_of(mod):
    """(name/arity) a module DERIVES — its ontology atoms with or without a body.

    ⛔ NOT its `concepts`. A concept says what a name means; it does not say that
    anything produces it. `schema.py` keeps that distinction and so does this: a
    borrow satisfied only by someone's concept entry is `described`, never `exact`.
    """
    out = set()
    for o in mod.get("ontology") or []:
        atom = (o.get("atom") or "").strip()
        name, _, rest = atom.partition("(")
        if not name:
            continue
        args = [a for a in rest.rstrip(")").split(",") if a.strip()] if rest else []
        out.add(f"{name.strip()}/{len(args)}")
    return out


def concepts_of(mod):
    return {f"{c.get('name')}/{c.get('arity')}": (c.get("gloss") or "")
            for c in (mod.get("concepts") or [])}


def borrows_of(mod):
    g = concepts_of(mod)
    return {p: g.get(p, "") for p in (mod.get("requires") or [])}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--needs", nargs="+", required=True,
                   help="module json files whose `requires` we try to satisfy")
    p.add_argument("--providers", nargs="+", required=True,
                   help="module json files that might define them")
    a = p.parse_args(argv)

    provs = []
    for f in a.providers:
        m = load(f)
        provs.append((os.path.basename(f), m, heads_of(m), concepts_of(m)))

    print(f"{'='*78}\nPROVIDERS — what has been put on offer\n{'='*78}")
    for name, m, hs, cs in provs:
        print(f"  {name}  clause={m.get('clause_id')}")
        print(f"     derives : {sorted(hs) or '— nothing —'}")
        for sig, gl in cs.items():
            print(f"     concept : {sig:38} {gl[:70]}")

    all_heads = set().union(*[h for _, _, h, _ in provs]) if provs else set()
    all_con = {}
    for _, _, _, cs in provs:
        all_con.update(cs)

    print(f"\n{'='*78}\nNEEDS — and whether anything on offer meets them\n{'='*78}")
    tally = {"exact": 0, "shape": 0, "described": 0, "absent": 0}
    for f in a.needs:
        m = load(f)
        print(f"\n  {os.path.basename(f)}  clause={m.get('clause_id')}")
        for sig, gl in borrows_of(m).items():
            name, _, ar = sig.partition("/")
            if sig in all_heads:
                verdict, note = "exact", "a provider derives this name/arity"
            elif any(h.split("/")[0] == name for h in all_heads):
                other = [h for h in all_heads if h.split("/")[0] == name]
                verdict, note = "shape", f"same name, different arity: {other}"
            elif sig in all_con or any(c.split("/")[0] == name for c in all_con):
                verdict, note = "described", "a provider CONCEPT names it, but nothing derives it"
            else:
                verdict, note = "candidate?", "no name match — read the glosses below"
            tally[verdict if verdict in tally else "absent"] += 1
            print(f"     [{verdict:10}] {sig:36} {note}")
            print(f"                  needs: {gl[:80]}")
            if verdict == "candidate?":
                for sig2, gl2 in sorted(all_con.items()):
                    print(f"                    ? {sig2:30} {gl2[:64]}")

    print(f"\n{'='*78}")
    print("  " + " · ".join(f"{k} {v}" for k, v in tally.items()))
    print("\n  ⚠️ `candidate?` rows are for a READER. A string comparison of two "
          "glosses\n     scored 0.44 on a pair that plainly matched, so nothing here "
          "guesses.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
