"""END-OF-RUN SWEEP — every class any slice-1 clause raised, run back across all 5.

The measured gap this exists to close: a class NAMED on clause 4 never reaches clause 1,
because the loop is per-clause with no end-of-run pass. Each check below is a QUESTION a
later reader can apply mechanically, which is the point — every high-value class we have
found was checkable in a few lines of Python that nobody had written.

Run from phase_1/:
    ../../../semi-formal-experiment/.venv/bin/python _debug_gen11/opus_pairs/slice1/sweep.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2", "node_corpus_all.json")
IDS = ["l1001_1107_n001", "l1001_1107_n007", "l1001_1107_n012",
       "l1108_1367_n004", "l1108_1367_n009"]

ANCHOR = re.compile(r"\]\(#([a-zA-Z0-9_-]+)\)")
NAME = re.compile(r"^\s+- (\w+):\s*(.*)$", re.M)


def blocks(quote):
    prov = re.search(r"PROVIDES.*?\n(.*?)\nNEEDS", quote, re.S)
    need = re.search(r"NEEDS.*?:\n(.*?)\nCITATION", quote, re.S)
    P = dict(NAME.findall(prov.group(1))) if prov else {}
    N = dict(NAME.findall(need.group(1))) if need else {}
    return P, N


def narrowed(quote):
    m = re.search(r"\[node narrows this span to: \"(.*?)\"\]", quote, re.S)
    if m:
        return m.group(1)
    src = quote.split("SOURCE TEXT", 1)[-1]
    return src


def functor(term):
    return term.split("(")[0].strip()


def body_functors(body):
    if not body:
        return set()
    return {functor(x) for x in re.findall(r"[a-z_][a-zA-Z0-9_]*\s*\(", body)}


def main():
    rows = {r["id"]: r for r in json.load(open(CORPUS))["clauses"]}
    mods = {}
    for cid in IDS:
        mods[cid] = json.load(open(os.path.join(HERE, "out", cid + ".json")))

    print("=" * 78)
    print("S1  BORROWED-GLOSS LICENCE SPLIT")
    print("    Q: for each NEEDS name, is its `concepts` licence `textual` or `assumed`?")
    print("    A split ACROSS clauses means one of them is wrong, and neither pass saw it.")
    print("=" * 78)
    lic = {}
    for cid in IDS:
        P, N = blocks(rows[cid]["quote"])
        for c in mods[cid].get("concepts") or []:
            if c["name"] in N:
                lic.setdefault(c["name"], []).append((cid, c["licence"]))
                print(f"  {cid:18s} NEEDS {c['name']:28s} licence={c['licence']}")
    for name, seen in lic.items():
        if len({l for _, l in seen}) > 1:
            print(f"  ⛔ SPLIT on `{name}`: {seen}")

    print()
    print("=" * 78)
    print("S2  PROVIDES n NEEDS SELF-LOOP")
    print("    Q: does the node NEED a name it also PROVIDES? Then contract 2 "
          "('never in ontology') and PROVIDES ('the predicates this module defines') "
          "cannot both be obeyed.")
    print("=" * 78)
    for cid in IDS:
        P, N = blocks(rows[cid]["quote"])
        both = sorted(set(P) & set(N))
        if both:
            m = mods[cid]
            onto_heads = {functor(o["atom"]) for o in (m.get("ontology") or [])}
            req = {r.split("/")[0] for r in (m.get("requires") or [])}
            for b in both:
                print(f"  ⛔ {cid}: `{b}` in BOTH. resolved as: "
                      f"ontology={b in onto_heads} requires={b in req}")
    print("  (corpus-wide count of the same shape is reported in SWEEP.md)")

    print()
    print("=" * 78)
    print("S4  HEAD-ONLY PREDICATE — derived and consumed by nothing")
    print("    Q: is any predicate an ontology HEAD that appears in no assert body and "
          "no other ontology body? Then nothing it classifies can change a verdict.")
    print("=" * 78)
    for cid in IDS:
        m = mods[cid]
        heads = {functor(o["atom"]) for o in (m.get("ontology") or [])}
        used = set()
        for o in (m.get("ontology") or []):
            used |= body_functors(o.get("body"))
        for a in (m.get("asserts") or []):
            used |= body_functors(a.get("body"))
        for f in (m.get("forbid_body") or []):
            used.add(f.get("banned"))
        inert = sorted(heads - used)
        n_asserts = len(m.get("asserts") or [])
        print(f"  {cid:18s} asserts={n_asserts} ontology_heads={sorted(heads)}")
        if inert:
            print(f"      -> INERT (head-only, consumed nowhere): {inert}")

    print()
    print("=" * 78)
    print("S5  DOCUMENT ANCHOR DROPPED BY THE NODE CONTRACT")
    print("    Q: does the SOURCE TEXT carry a markdown anchor that the NEEDS block "
          "never mentions? Then the document's own cross-reference is invisible to the "
          "translator and to `requires`.")
    print("=" * 78)
    for cid in IDS:
        q = rows[cid]["quote"]
        P, N = blocks(q)
        anchors = sorted(set(ANCHOR.findall(q.split("SOURCE TEXT", 1)[-1])))
        joined = " ".join(list(N) + list(N.values()) + list(P))
        missed = [a for a in anchors if a not in joined]
        print(f"  {cid:18s} anchors={anchors or '-'} not-in-NEEDS={missed or '-'} "
              f"requires={mods[cid].get('requires')}")

    print()
    print("=" * 78)
    print("S6  `claims` OVERLOADED — how many claims are encoded in no assert/ontology?")
    print("    Q: P3 says an unencoded claim is the fingerprint of a dropped obligation. "
          "But 30_failure_modes row 11 TELLS you to put impossibility notes in `claims`. "
          "Count both, do not assume the first.")
    print("=" * 78)
    for cid in IDS:
        m = mods[cid]
        n_claims = len(m.get("claims") or [])
        meta = [c for c in (m.get("claims") or [])
                if re.match(r"^C\d+\s+META", c) or " META" in c[:12]]
        print(f"  {cid:18s} claims={n_claims} explicitly-META={len(meta)} "
              f"asserts={len(m.get('asserts') or [])} "
              f"ontology={len(m.get('ontology') or [])}")

    print()
    print("=" * 78)
    print("S7  OPEN CLASS CLOSED IN CODE")
    print("    Q: does the narrowed span carry an open-list marker (`such as`, `e.g.`, "
          "`like`, `including`)? If so, is the class it opens derivable ONLY from the "
          "named members?")
    print("=" * 78)
    for cid in IDS:
        txt = narrowed(rows[cid]["quote"])
        marks = [w for w in ("such as", "e.g.", "contexts like", " like ", "including")
                 if w in txt]
        m = mods[cid]
        heads = {}
        for o in (m.get("ontology") or []):
            heads.setdefault(functor(o["atom"]), []).append(o.get("body"))
        closed = {h: len(b) for h, b in heads.items()
                  if all(x for x in b) and h not in
                  {i.split("/")[0] for i in (m.get("inputs") or [])}
                  and h not in {r.split("/")[0] for r in (m.get("requires") or [])}}
        print(f"  {cid:18s} open-markers={marks or '-'}")
        if marks and closed:
            print(f"      -> classes derivable ONLY from named members: {closed}")

    print()
    print("=" * 78)
    print("S8  CARVE-OUT WITH NO LANDING FIELD")
    print("    Q: does the span carry an exception connective (`However`, `unless`, "
          "`only`, a BAD[#anchor] tag) whose counterpart clause id was never supplied? "
          "Then rule 8b's `beats` has no id to take and the relation is unrecordable.")
    print("=" * 78)
    for cid in IDS:
        txt = narrowed(rows[cid]["quote"])
        full = rows[cid]["quote"].split("SOURCE TEXT", 1)[-1]
        conn = [w for w in ("However", "unless", "may only", "BAD[#", "except")
                if w in txt or w in full]
        print(f"  {cid:18s} connectives={conn or '-'} beats={len(mods[cid].get('beats') or [])}")

    print()
    print("SWEEP COMPLETE.")


if __name__ == "__main__":
    main()
