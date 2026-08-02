"""Enumerate distinct norm conflicts in rules.lp and print one minimal-ish
witness scenario per conflict, classified by tier resolution and
interpretation-dependence."""
import clingo
import os
from collections import defaultdict

RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.lp")


def brave_conflicts():
    """Union over all answer sets of the conflict/5 atoms (brave consequences)."""
    ctl = clingo.Control(["--enum-mode=brave"])
    ctl.load(RULES)
    ctl.ground([("base", [])])
    last = []

    def on_model(m):
        last.clear()
        last.extend(m.symbols(shown=True))

    ctl.solve(on_model=on_model)
    sources = {
        str(s.arguments[0]): str(s.arguments[1]).strip('"')
        for s in last
        if s.name == "source"
    }
    # paragraph-level provenance: norm -> (locator, clause id, clause kind)
    locators = {
        str(s.arguments[0]): tuple(str(a).strip('"') for a in s.arguments[1:])
        for s in last
        if s.name == "locator"
    }
    return sorted({str(s) for s in last if s.name == "conflict"}), sources, locators


def witness(conflict_atom, minimize=True):
    """One witness scenario for a given conflict, minimizing true ctx/interp atoms."""
    ctl = clingo.Control(["--opt-mode=optN", "1"])
    ctl.load(RULES)
    ctl.add("goal", [], f":- not {conflict_atom}.")
    if minimize:
        ctl.add("goal", [], "#minimize { 1,X : ctx(X) }.")
        ctl.add("goal", [], "#minimize { 1,X : interp(X) }.")
    ctl.ground([("base", []), ("goal", [])])
    found = {}

    def on_model(m):
        syms = m.symbols(shown=True)
        found["ctx"] = sorted(str(s.arguments[0]) for s in syms if s.name == "ctx")
        found["interp"] = sorted(str(s.arguments[0]) for s in syms if s.name == "interp")

    ctl.solve(on_model=on_model)
    return found if found else None


def holds_without_interps(conflict_atom):
    """Does the conflict have a witness with NO interp atoms set?"""
    ctl = clingo.Control()
    ctl.load(RULES)
    ctl.add("goal", [], f":- not {conflict_atom}.")
    ctl.add("goal", [], ":- interp(_).")
    ctl.ground([("base", []), ("goal", [])])
    return ctl.solve().satisfiable


def main():
    conflicts, sources, locators = brave_conflicts()
    # dedupe symmetric pairs: keep one representative per unordered norm pair
    seen_pairs = {}
    for c in conflicts:
        inner = c[len("conflict(") : -1]
        n1, n2, act, t1, t2 = [x.strip() for x in inner.split(",")]
        key = frozenset((n1, n2))
        if key not in seen_pairs:
            seen_pairs[key] = (c, n1, n2, act, int(t1), int(t2))

    groups = defaultdict(list)
    for c, n1, n2, act, t1, t2 in seen_pairs.values():
        w = witness(c)
        interp_free = holds_without_interps(c)
        kind = "SAME-TIER (unresolved by priority ordering)" if t1 == t2 else \
               f"CROSS-TIER (holistically resolved toward tier {min(t1, t2)})"
        cond = "" if interp_free else "  [ONLY under a contested interpretation]"
        groups[kind].append((n1, n2, act, t1, t2, w, cond))

    total = sum(len(v) for v in groups.values())
    print(f"{total} distinct norm-pair conflicts found\n" + "=" * 60)
    for kind in sorted(groups):
        print(f"\n### {kind}\n")
        for n1, n2, act, t1, t2, w, cond in sorted(groups[kind]):
            print(f"  {n1} (tier {t1})  vs  {n2} (tier {t2})  over act: {act}{cond}")
            print(f"      sources:  [{sources.get(n1, '?')}]  vs  [{sources.get(n2, '?')}]")
            for n in (n1, n2):
                loc = locators.get(n)
                if loc:
                    print(f"      ¶ {n:16s} {loc[0]}  [{loc[1]} {loc[2]}]")
                else:
                    print(f"      ¶ {n:16s} (no verified paragraph locator)")
            if w:
                print(f"      witness ctx:    {', '.join(w['ctx'])}")
                if w["interp"]:
                    print(f"      witness interp: {', '.join(w['interp'])}")
            print()


if __name__ == "__main__":
    main()
