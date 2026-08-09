#!/usr/bin/env python3
"""EXTENSIONAL concept identity — is a concept's ID the TEXT it points at?

MATT'S PROPOSAL, 2026-08-08, and it inverts everything above it in this
directory. Every experiment so far tried to establish what a borrowed predicate
MEANS — a definition, a formal one, iterated to self-sufficiency. All of them
failed on the same rock: five runs produce five vocabularies with **0.00**
agreement, and consolidating five non-overlapping definitions yields nothing.

⭐ The proposal drops the definition entirely. A concept's identity becomes
**the region of the document it is grounded in**. Two names that point at the
same text ARE the same concept, whatever they are called; a name is then just a
label drawn from the set, and any member will do. Relations between concepts
fall out of set overlap: containment is specialisation, intersection is a shared
component, disjointness is independence.

WHY THE MEASUREMENTS FAVOUR IT over anything tried so far:

  what CONVERGES   section retrieval — 0.78 across five runs in round 1,
                   0.64 single-turn, 5 of 8 concepts unanimous
  what DOES NOT    predicate vocabulary — 0.06 single-shot, 0.00 iterated,
                   and 0 shared rule shapes for 6 of 8 concepts

⇒ The proposal builds identity out of the only signal that survived repetition,
and throws away the one that never did. It is also **statically checkable**,
which no definition ever was: a span either is in the document or it is not.

⛔ THE PLACE IT CAN BREAK, and this script exists to measure it rather than
argue about it. **Granularity.** `definitions` is ONE section holding roughly
ten unrelated term definitions. At section granularity every predicate grounded
anywhere in it collapses to one concept — which is RIGHT for `m0053`'s twins
`interactable_entity` and `interaction_entity` (two spellings, one idea, the
exact defect Q-6 names) and WRONG for `assistant` versus `conversation`, which
are simply different terms that share a home. So section granularity is
guaranteed to over-merge somewhere, and Matt's own sharper version — *"word
locations"* — is the one worth testing. This script measures both and reports
what each merges, because a merge that is correct and a merge that is wrong look
identical in a cluster count.

⚠️ WHAT THIS IS NOT. It is a probe over stored run data, not a pipeline module.
It reads `solver_v4.json` (43 real borrowed predicates, each with verbatim
excerpts) and asks only: how much collapsing does extensional identity buy, and
is the collapsing right? Nothing here is registered, fenced, or wired to a seat.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, "resolve_runs", "panel")

sys.path.insert(0, HERE)
from iter_score import normalise, load_document  # noqa: E402


def spans(run, secs):
    """predicate -> {section: [(start, end), ...]} in NORMALISED coordinates.

    ⚠️ Offsets are into the normalised section, not the raw file. That is fine
    for overlap comparisons — both sides go through the same normaliser — and
    it is the only way to locate an excerpt a model retyped with different
    whitespace. It would NOT be fine for anything that needs to cite the file.
    """
    out, missed = {}, 0
    for c in run.get("concepts", []):
        got = {}
        for ex in c.get("contributing") or []:
            sid, t = ex.get("section_id"), normalise(ex.get("excerpt", ""))
            if not t or sid not in secs:
                missed += 1
                continue
            i = secs[sid].find(t)
            if i < 0:
                missed += 1
                continue
            got.setdefault(sid, []).append((i, i + len(t)))
        if got:
            out[c["predicate"]] = got
    return out, missed


def overlaps(a, b):
    """Do two extensions share any TEXT (not merely a section)?

    ⛔ ANY-OVERLAP IS THE WRONG TEST and it produced a fake ontology on the
    first run. Excerpt LENGTH varies by an order of magnitude between
    predicates, so a name whose model quoted a 400-character passage overlaps
    almost everything and a name quoted in 20 characters overlaps almost
    nothing. Identity then tracks how much text a model chose to quote, not
    what the name means. Kept only as the baseline `B` reports; `chars`/`sim`
    below are the measure to use.
    """
    for sid, ra in a.items():
        for s1, e1 in ra:
            for s2, e2 in b.get(sid, ()):
                if s1 < e2 and s2 < e1:
                    return True
    return False


def chars(ext):
    """Extension as a set of (section, char) — length-aware, comparable."""
    out = set()
    for sid, rs in ext.items():
        for s, e in rs:
            out |= {(sid, i) for i in range(s, e)}
    return out


def sim(a, b):
    """Jaccard over covered characters. Symmetric, and length cannot inflate it."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster(preds, same):
    """Union-find over a symmetric `same` relation."""
    parent = {p: p for p in preds}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    names = list(preds)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if same(a, b):
                parent[find(a)] = find(b)
    groups = {}
    for p in names:
        groups.setdefault(find(p), []).append(p)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0]))


def report(title, groups, note=""):
    merged = [g for g in groups if len(g) > 1]
    print(f"\n{title}")
    print(f"  {sum(len(g) for g in groups)} predicates -> {len(groups)} concepts"
          f"   ({len(merged)} clusters hold more than one name)")
    if note:
        print(f"  {note}")
    for g in merged:
        print(f"     [{len(g)}] " + ", ".join(sorted(g)))
    return groups


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", default=os.path.join(PANEL, "solver_v4.json"))
    p.add_argument("--document", default=os.path.join(PANEL, "DOCUMENT.txt"))
    a = p.parse_args(argv)
    if not os.path.exists(a.run):
        print(f"⛔ {a.run} missing — nothing measured", file=sys.stderr)
        return 2
    secs, _ = load_document(a.document)
    with open(a.run, encoding="utf-8") as fh:
        run = json.load(fh)
    ext, missed = spans(run, secs)

    print(f"{'='*74}\nEXTENSIONAL IDENTITY over {len(ext)} predicates"
          f"   ({missed} excerpts could not be located and are dropped)\n{'='*74}")

    # -- coarse: same SECTION SET ------------------------------------------
    secset = {p: frozenset(v) for p, v in ext.items()}
    report("A · SECTION-SET identity  (two names with the same section set "
           "are one concept)",
           cluster(ext, lambda x, y: secset[x] == secset[y]))

    # -- fine: overlapping TEXT --------------------------------------------
    report("B · ⭐ SPAN-OVERLAP identity  (Matt's 'word locations' — two names "
           "that\n     quote overlapping TEXT are one concept)",
           cluster(ext, lambda x, y: overlaps(ext[x], ext[y])))

    # -- what the coarse version merges that the fine one does not ---------
    fine = {}
    for g in cluster(ext, lambda x, y: overlaps(ext[x], ext[y])):
        for m in g:
            fine[m] = g[0]
    print("\nC · ⛔ WHAT SECTION GRANULARITY MERGES THAT SPANS KEEP APART")
    print("     these are the over-merges — same home, different text")
    n = 0
    for g in cluster(ext, lambda x, y: secset[x] == secset[y]):
        sub = {}
        for m in g:
            sub.setdefault(fine[m], []).append(m)
        if len(sub) > 1:
            n += 1
            home = ", ".join(sorted(secset[g[0]]))
            print(f"     in <{home}>: " +
                  "  |  ".join("/".join(sorted(v)) for v in sub.values()))
    if not n:
        print("     none — the two granularities agree on this run")

    # -- ontology: containment and intersection ----------------------------
    # -- D. length-aware similarity, and NO transitive chaining ------------
    # ⛔ TWO DEFECTS IN B AND THEY COMPOUND. Union-find takes the TRANSITIVE
    # CLOSURE of "overlaps", so A-overlaps-B and B-overlaps-C puts A and C in
    # one concept even when they share no text at all. Combined with the
    # length bias above, one predicate quoted at length chains the whole
    # section into a single blob — which is exactly the 8-name cluster B
    # reports, and exactly why the first containment table had 15 of its 16
    # pairs pointing at the same right-hand side.
    #
    # So: score every PAIR by character-Jaccard, report the distribution, and
    # do not close the relation transitively.
    ch = {p: chars(v) for p, v in ext.items()}
    names = sorted(ch)
    scored = []
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            s = sim(ch[x], ch[y])
            if s > 0:
                scored.append((s, x, y))
    scored.sort(reverse=True)
    total = len(names) * (len(names) - 1) // 2
    print("\nD · ⭐ LENGTH-AWARE SIMILARITY (character Jaccard), NO chaining")
    print(f"     {len(scored)} of {total} pairs share any text at all")
    for lo, hi in ((0.8, 1.01), (0.5, 0.8), (0.2, 0.5), (0.0, 0.2)):
        band = [t for t in scored if lo <= t[0] < hi]
        print(f"     {lo:.1f}–{hi if hi <= 1 else 1.0:.1f}: {len(band):>4} pairs")
    print("\n     strongest pairs — these are the candidate SYNONYMS:")
    for s, x, y in scored[:12]:
        print(f"       {s:.2f}  {x:42} {y}")

    print("\nE · CONTAINMENT (one extension inside another) — the ontology edge")
    print("     reported only where the smaller is >=0.9 covered AND the")
    print("     larger is <=0.5 covered, so 'everything ⊂ the long quote' cannot")
    print("     masquerade as a hierarchy")
    n = 0
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            a, b = ch[x], ch[y]
            if not a or not b or not (a & b):
                continue
            for lo_n, hi_n, lo_s, hi_s in ((x, y, a, b), (y, x, b, a)):
                if len(lo_s & hi_s) / len(lo_s) >= 0.9 and \
                        len(lo_s & hi_s) / len(hi_s) <= 0.5:
                    n += 1
                    if n <= 15:
                        print(f"       {lo_n:42} ⊂ {hi_n}")
    print(f"     {n} containment pairs of {total} possible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
