"""How much of what the panel calls CORE has any deontic content to encode?

Joins `modelspec_clauses.json`'s own `kind` label (conditional / definitional /
example / meta / holistic) to the frozen panel verdicts, over all 589 passages
x 3 behaviours. The `kind` labels are the repo's, not mine.

Reading: `conditional` is the only kind that reliably carries an O/F/P over an
act. Everything else is either ontology (definitional), illustration (example),
statement about the rule set (meta), or a value/goal (holistic).
No model call.
"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.abspath(os.path.join(HERE, "..", "..", "semi-formal-experiment"))
sys.path.insert(0, MVP)
import panel_universe as pu

clauses = json.load(open(os.path.join(MVP, "modelspec_clauses.json")))["clauses"]

def key(loc):
    """section_id + paragraph number, the one thing both locator formats share."""
    m = re.search(r"¶(\d+)\s*$", loc)
    par = m.group(1) if m else "?"
    parts = [p.strip() for p in loc.split(">")]
    sec = parts[-2] if len(parts) >= 2 else "?"
    return (sec.lstrip("#").lower().replace(" ", "_").replace("-", "_"), par)

by_key = {}
for c in clauses:
    by_key.setdefault((c["section_id"].lower(), key(c["locator"])[1]), []).append(c)

u = pu.load_universe(spec_keys=("openai",))
tab = collections.defaultdict(collections.Counter)
unjoined = 0
for b in u:
    for p in u[b]["coverage"]["openai"]["passages"]:
        hit = by_key.get(key(p["locator"]))
        if not hit:
            unjoined += 1
            continue
        kind = hit[0]["kind"]
        s = p["score"]
        band = "core(5-6)" if s >= 5 else ("mid(1-4)" if s >= 1 else "zero(0)")
        tab[b][(kind, band)] += 1

kinds = sorted({k for b in tab for k, _ in tab[b]})
print(f"unjoined passage-rows (excluded): {unjoined} of {589*3}\n")
for b in tab:
    print(b)
    print(f"  {'kind':14s} {'core':>6s} {'%core':>7s} {'mid':>6s} {'zero':>6s}")
    tot_core = sum(tab[b][(k, "core(5-6)")] for k in kinds)
    for k in kinds:
        c = tab[b][(k, "core(5-6)")]
        print(f"  {k:14s} {c:6d} {100*c/max(tot_core,1):6.1f}% "
              f"{tab[b][(k,'mid(1-4)')]:6d} {tab[b][(k,'zero(0)')]:6d}")
    nd = sum(tab[b][(k, "core(5-6)")] for k in kinds if k != "conditional")
    print(f"  -> core passages that are NOT `conditional`: {nd}/{tot_core} "
          f"({100*nd/max(tot_core,1):.0f}%)\n")
