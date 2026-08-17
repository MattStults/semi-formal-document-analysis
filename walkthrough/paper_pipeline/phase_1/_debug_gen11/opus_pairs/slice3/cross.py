#!/usr/bin/env python3
"""CROSS-MODULE sweep — the checks that CANNOT run on one module at a time.

Measured gap #2: "classes found late never reach clauses done early." The
per-clause loop is structurally blind to any defect whose evidence lives in two
modules at once. These are those checks.

Run: ../../../../../../semi-formal-experiment/.venv/bin/python cross.py
"""
import json, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IDS = ["l1001_1107_n003", "l1001_1107_n009", "l1108_1367_n001",
       "l1108_1367_n006", "l1108_1367_n011"]

_SORTS = ["rule", "instruction", "heading", "section", "message", "content",
          "response", "request", "person", "number", "context", "work", "group"]


def load():
    d = {}
    for c in IDS:
        p = os.path.join(OUT, f"{c}.json")
        if os.path.exists(p):
            d[c] = json.load(open(p))
    return d


def concept_index(mods):
    ix = defaultdict(list)
    for cid, o in mods.items():
        req = {str(r).split("/")[0] for r in (o.get("requires") or [])}
        onto = {(_h(e)) for e in (o.get("ontology") or []) if _h(e)}
        for e in (o.get("concepts") or []):
            n = str(e.get("name", "")).split("/")[0]
            role = "PROVIDES" if n in onto else ("borrows" if n in req else "coins")
            ix[n].append((cid, e.get("arity"), str(e.get("gloss") or ""), role))
    return ix


def _h(e):
    m = re.match(r"\s*([a-z_][A-Za-z0-9_]*)\s*\(", str(e.get("atom", "")))
    return m.group(1) if m else None


# ------------------------------------------------------------------ X1
def x_arity_disagreement(ix):
    """X1. Does a name shared by two modules carry two different arities?
    A link on a name whose arity differs never fires and never errors."""
    out = []
    for n, rows in sorted(ix.items()):
        ar = {r[1] for r in rows}
        if len(rows) > 1 and len(ar) > 1:
            out.append(f"`{n}` declared with arities {sorted(ar)} across "
                       + ", ".join(r[0] for r in rows))
    return out


# ------------------------------------------------------------------ X2
def x_sort_disagreement(ix):
    """X2. For a name shared by two modules, do the glosses name the SAME SORT
    of thing in argument 1? `rule` vs `instruction` vs `heading` are three
    different sorts and the link step compares names, not sorts."""
    out = []
    for n, rows in sorted(ix.items()):
        if len(rows) < 2:
            continue
        sorts = {}
        for cid, ar, g, role in rows:
            gl = g.lower()
            found = [s for s in _SORTS if re.search(rf"\b{s}s?\b", gl[:120])]
            sorts[cid] = (found[:2], role)
        heads = {tuple(v[0][:1]) for v in sorts.values() if v[0]}
        if len(heads) > 1:
            out.append(f"`{n}` glossed over DIFFERENT SORTS: "
                       + "; ".join(f"{c}={v[0]}({v[1]})" for c, v in sorts.items()))
    return out


# ------------------------------------------------------------------ X3  ⭐
def x_section_local_gloss(ix):
    """X3 ⭐ HIGHEST VALUE. Does a module gloss a SHARED, GLOBAL predicate as if
    it were LOCAL TO ITS OWN SECTION?

    `root_authority/1` is one global predicate. Three borrowers gloss it as "the
    rules stated in the RESPECT-CREATORS section", "the PRIVACY-PROTECTION
    section", "the #AVOID_HATEFUL_CONTENT section" — three mutually exclusive
    restrictions on one name. Once linked, an atom derived by ANY provider
    satisfies ALL of them, so each module's stated assumption is false of the
    predicate it actually gets.

    Invisible to every single-clause check, because within one module the gloss
    is perfectly accurate. This is the shape of the licence-inheritance class
    that sat unfixed in most of the previous cohort."""
    out = []
    pat = re.compile(r"(#[a-z_]+|\b[a-z]+[- ](?:creators?|protection|content)\b"
                     r"|\bthat section\b|\bthis section\b)", re.I)
    for n, rows in sorted(ix.items()):
        if len(rows) < 2:
            continue
        hits = []
        for cid, ar, g, role in rows:
            m = pat.findall(g)
            if m:
                hits.append((cid, role, sorted(set(x.strip() for x in m))))
        if len(hits) > 1 and len({tuple(h[2]) for h in hits}) > 1:
            out.append(f"`{n}` is glossed SECTION-LOCALLY by {len(hits)} modules, "
                       f"each naming a DIFFERENT section: "
                       + "; ".join(f"{c}({r})->{s}" for c, r, s in hits))
    return out


# ------------------------------------------------------------------ X4
def x_provider_borrower_gap(ix):
    """X4. For a name one module PROVIDES and others BORROW, does the provider's
    gloss cover everything the borrowers assume? Reports the pair so a human
    reads two sentences instead of five modules."""
    out = []
    for n, rows in sorted(ix.items()):
        prov = [r for r in rows if r[3] == "PROVIDES"]
        borr = [r for r in rows if r[3] == "borrows"]
        if prov and borr:
            out.append(f"`{n}`: PROVIDED by {prov[0][0]}, BORROWED by "
                       + ", ".join(b[0] for b in borr) + "  [READ THE GLOSSES]")
            out.append(f"    provider: {prov[0][2][:150]}")
            for b in borr:
                out.append(f"    {b[0]}: {b[2][:150]}")
    return out


# ------------------------------------------------------------------ X5
def x_orphan_borrow(ix, mods):
    """X5. Is a name BORROWED by some module and PROVIDED by none in this set?
    Expected for a 5-clause slice and NOT a defect — reported so the number is
    on the record rather than rediscovered as a surprise."""
    out = []
    for n, rows in sorted(ix.items()):
        if any(r[3] == "borrows" for r in rows) and not any(
                r[3] == "PROVIDES" for r in rows):
            out.append(f"`{n}` borrowed by "
                       + ", ".join(r[0] for r in rows if r[3] == "borrows")
                       + " — no provider in this slice [EXPECTED, not a defect]")
    return out


def main():
    mods = load()
    ix = concept_index(mods)
    print(f"modules loaded: {len(mods)}   distinct concept names: {len(ix)}")
    shared = {n: r for n, r in ix.items() if len(r) > 1}
    print(f"names appearing in more than one module: {len(shared)} "
          f"-> {sorted(shared)}")
    for fn in (x_arity_disagreement, x_sort_disagreement, x_section_local_gloss,
               x_provider_borrower_gap):
        print("=" * 72)
        print(fn.__name__[2:].upper())
        hits = fn(ix)
        print("\n".join("  * " + h for h in hits) if hits else "  clean")
    print("=" * 72)
    print("ORPHAN_BORROW")
    hits = x_orphan_borrow(ix, mods)
    print("\n".join("  * " + h for h in hits) if hits else "  clean")


if __name__ == "__main__":
    main()
