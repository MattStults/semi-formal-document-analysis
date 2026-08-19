#!/usr/bin/env python3
"""WHY IS THIS MODULE SILENT? (Matt's design, 2026-08-18: use clingo-side
explanation + a Fable hypothesis loop instead of guessing.)

For each act-engaged-but-silent module: ground the behavior + bridges +
module, then evaluate every assert-rule body literal against the answer
set and report exactly which literals FAILED. Aggregate across modules ->
ranked missing-fact families = the reachability worklist, with evidence.
Output: panel_run1/silence_census_<slug>.json
"""
import json, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))
import behavior_match as BM, link_nodes, mutation_scope as MS
import relevance_by_act as RBA

def rule_bodies(path):
    """(head_name, [positive body literal names]) per rule, via clingo.ast —
    regex parsing measured broken (substring artifacts: 'onto' x37)."""
    from clingo import ast as A
    rules = []
    def cb(st):
        if st.ast_type != A.ASTType.Rule or st.head is None: return
        try: hname = st.head.atom.symbol.name
        except Exception: return
        lits = []
        for b in st.body or []:
            try:
                if b.ast_type == A.ASTType.Literal and b.sign == A.Sign.NoSign and b.atom.ast_type == A.ASTType.SymbolicAtom:
                    lits.append(b.atom.symbol.name)
            except Exception: pass
        if lits: rules.append((hname, lits))
    try:
        A.parse_string(open(path, encoding="utf-8").read(), cb)
    except Exception:
        pass
    return rules


def explain(slug, spec, silent, sel, bridges, limit=None):
    import clingo
    lp = BM.render_behavior_module("b_x", slug, spec["facts"], spec["does"])
    rows = []
    for cid in sorted(silent)[:limit]:
        path = sel[link_nodes.norm_id(cid)][0]
        prog = open(path, encoding="utf-8").read() + "\n" + lp + "\n" + bridges
        ctl = clingo.Control(["--warn=none"])
        try:
            ctl.add("base", [], prog); ctl.ground([("base", [])])
        except Exception as ex:
            rows.append({"node": cid, "error": str(ex)[:80]}); continue
        atoms = set()
        ctl.solve(on_model=lambda m: atoms.update(str(s) for s in m.symbols(atoms=True)))
        names_true = {a.split("(")[0] for a in atoms}
        missing = []
        for hname, lits in rule_bodies(path):
            fails = [n for n in lits if n not in names_true]
            if fails: missing += fails
        rows.append({"node": cid, "missing": sorted(set(missing))})
    return rows


def main():
    slug = sys.argv[sys.argv.index("--behavior") + 1]
    canon_f = sys.argv[sys.argv.index("--canonical") + 1] if "--canonical" in sys.argv else "behaviors_canonical_v6.json"
    mods_f = sys.argv[sys.argv.index("--modules") + 1] if "--modules" in sys.argv else "modules_contract_v6.json"
    spec = json.load(open(os.path.join(HERE, canon_f)))["behaviors"][slug]
    mods = json.load(open(os.path.join(HERE, mods_f)))["modules"][slug]
    br = RBA.bridges(); corpus = RBA.corpus_acts(); sel = link_nodes.gather()
    bridges = MS.behavior_to_corpus_bridges()
    _, rel = RBA.relevance(mods, br, corpus)
    # silent = act-engaged but does not fire under the grounded facts (approx: run explain over all engaged; those with missing != [] are silent-with-reason)
    rows = explain(slug, spec, set(rel), sel, bridges)
    cnt = Counter(n for r in rows for n in r.get("missing", []))
    out = {"behavior": slug, "modules_examined": len(rows),
           "top_missing": cnt.most_common(40), "rows": rows}
    json.dump(out, open(os.path.join(HERE, "panel_run1", f"silence_census_{slug.split('-')[0]}.json"), "w"), indent=1)
    print(f"{slug}: {len(rows)} modules; top missing literals:")
    for n, c in cnt.most_common(15): print(f"  {c:4d} {n}")


if __name__ == "__main__": main()
