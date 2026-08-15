"""Q3: is the ontology route discoverable? Attempt-1 drafts only. READ-ONLY."""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "census.json")))
agree = json.load(open(os.path.join(HERE, "agreement.json")))
HARD = {"forbid", "permit", "oblige"}


def attempt1(path):
    """First assistant message of the transcript, parsed as the module JSON."""
    t = path[:-5] + ".transcript.json"
    if not os.path.exists(t):
        return None, 0
    msgs = json.load(open(t))
    n_assist = sum(1 for m in msgs if m.get("role") == "assistant")
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        c = m.get("content", "")
        c = re.sub(r"^```(?:json)?|```$", "", c.strip(), flags=re.M).strip()
        s, e = c.find("{"), c.rfind("}")
        if s < 0:
            return None, n_assist
        try:
            return json.loads(c[s:e + 1]), n_assist
        except Exception:
            return None, n_assist
    return None, n_assist


def route(d):
    if d is None:
        return "unparsed"
    if d.get("outcome") == "abstained":
        return "abstain"
    sts = {a.get("status") for a in d.get("asserts", []) if isinstance(a, dict)}
    if sts & HARD:
        return "deontic"
    if d.get("ontology"):
        return "ontology"
    if sts:
        return "prefer-only"
    return "empty"


glob_r = collections.Counter()
attempts = collections.Counter()
flip = collections.Counter()
per_id = {}
for r in rows:
    d1, na = attempt1(r["path"])
    rt = route(d1)
    glob_r[rt] += 1
    attempts[na] += 1
    per_id[r["clause_id"]] = rt
    final = "deontic" if r["deontic_hard"] else ("ontology" if r["n_ontology"] else
             ("prefer-only" if r["deontic_soft"] else "empty"))
    flip[(rt, final)] += 1

print("=== attempt-1 route, ALL 152 translated modules (MEASURED) ===")
tot = sum(glob_r.values())
for k, v in glob_r.most_common():
    print(f"  {k:12s} {v:4d}  {v/tot*100:5.1f}%")
print(f"\n  assistant turns per module (1 = no repair round): {dict(attempts)}")

print("\n=== attempt-1 -> final route transitions ===")
for (a, b), v in sorted(flip.items(), key=lambda x: -x[1]):
    mark = "" if a == b else "   <-- changed"
    print(f"  {a:12s} -> {b:12s} {v:4d}{mark}")

print("\n=== attempt-1 route for the DESCRIPTION-judged items (Q3 as pre-registered) ===")
for tag, ids in (("both tiers", agree["both"]), ("either tier", agree["either"])):
    c = collections.Counter(per_id[i] for i in ids)
    print(f"  {tag} (n={len(ids)}): {dict(c)}")
    for i in ids:
        print(f"      {i:20s} attempt-1 route = {per_id[i]}")
    n = sum(c[k] for k in ("ontology", "deontic", "abstain"))
    if n:
        print(f"      discoverability = ontology/(ont+deo+abs) = {c['ontology']}/{n} = {c['ontology']/n:.2f}")
