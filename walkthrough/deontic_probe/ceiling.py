"""Structural ceiling on ANY encoding whose relevance predicate needs a deontic
operator in the passage. No model call; pure re-analysis of the frozen panel."""
import os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.abspath(os.path.join(HERE, "..", "..", "semi-formal-experiment"))
sys.path.insert(0, MVP)
import panel_universe as pu

MODAL = re.compile(r"\b(should|shall|must|may|never|cannot|can't|"
                   r"is not allowed|are not allowed|is prohibited|are prohibited|"
                   r"is required|are required|ought|permitted|forbidden|"
                   r"disallowed|refuse|decline|avoid)\b", re.I)
EXAMPLE = re.compile(r"^\s*Example:", re.I)

u = pu.load_universe(spec_keys=("openai",))
rows = []
for b in u:
    ps = u[b]["coverage"]["openai"]["passages"]
    tab = collections.Counter()
    for p in ps:
        q = p["quote"]
        deo = bool(MODAL.search(q))
        ex = bool(EXAMPLE.match(q)) or bool(p.get("exampleBlock"))
        s = p["score"]
        band = "core(5-6)" if s >= 5 else ("mid(1-4)" if s >= 1 else "zero(0)")
        tab[(band, deo)] += 1
        tab[(band, "ex" if ex else "prose")] += 1
    rows.append((b, tab, len(ps)))

print(f"{'behaviour':38s} {'band':11s} {'n':>5s} {'modal':>7s} {'%':>6s} {'example':>8s} {'%':>6s}")
for b, tab, n in rows:
    for band in ("core(5-6)", "mid(1-4)", "zero(0)"):
        tot = tab[(band, True)] + tab[(band, False)]
        m = tab[(band, True)]
        e = tab[(band, "ex")]
        print(f"{b:38s} {band:11s} {tot:5d} {m:7d} {100*m/max(tot,1):5.1f}% {e:8d} {100*e/max(tot,1):5.1f}%")
    print()
