"""Deterministic census of translated modules. READ-ONLY on runs/."""
import json, glob, os, re, random, collections, sys

RUNS = os.path.abspath(os.path.join(os.path.dirname(__file__),
    "../../resolve_runs/graph_v2/translation_sample/runs"))
LIVE = {"20260815-113545-together-deepseek-v4-flash",
        "20260815-124836-together-deepseek-v4-flash"}
OUT = os.path.dirname(os.path.abspath(__file__))

def load_all():
    by_id = {}
    for run in sorted(os.listdir(RUNS)):
        if run in LIVE:
            continue
        for f in sorted(glob.glob(os.path.join(RUNS, run, "*.json"))):
            if os.path.basename(f) == "concepts.json":
                continue
            try:
                d = json.load(open(f))
            except Exception:
                continue
            if not isinstance(d, dict) or "outcome" not in d:
                continue
            cid = d.get("clause_id") or os.path.basename(f)[:-5]
            # later runs sort later -> overwrite keeps most recent
            by_id[cid] = (run, f, d)
    return by_id

def status_of(a):
    if isinstance(a, dict):
        return a.get("status") or a.get("Status")
    return None

def main():
    by_id = load_all()
    tr = {k: v for k, v in by_id.items() if v[2]["outcome"] == "translated"}
    ab = {k: v for k, v in by_id.items() if v[2]["outcome"] == "abstained"}
    print(f"unique ids (excl live) = {len(by_id)}  translated = {len(tr)}  abstained = {len(ab)}")

    stat = collections.Counter()
    onto_atoms = []
    bodyless = 0
    rows = []
    for cid, (run, f, d) in sorted(tr.items()):
        sts = [status_of(a) for a in d.get("asserts", [])]
        sts = [s for s in sts if s]
        stat.update(sts)
        hard = any(s in ("forbid", "permit", "oblige") for s in sts)
        soft = (not hard) and any(s == "prefer" for s in sts)
        onto = d.get("ontology", []) or []
        for o in onto:
            atom = o.get("atom", "") if isinstance(o, dict) else str(o)
            onto_atoms.append((cid, atom, (o.get("licence") if isinstance(o, dict) else None)))
            if ":-" not in atom:
                bodyless += 1
        rows.append(dict(clause_id=cid, run=run, path=f,
                         n_asserts=len(sts), statuses=sts,
                         deontic_hard=hard, deontic_soft=soft,
                         n_ontology=len(onto),
                         ontology_only=(len(onto) > 0 and len(sts) == 0),
                         n_defines=len(d.get("defines", []) or []),
                         n_concepts=len(d.get("concepts", []) or [])))

    print("\n-- assert status distribution (whole population) --")
    for k, v in stat.most_common():
        print(f"  {k:10s} {v}")
    nh = sum(1 for r in rows if r["deontic_hard"])
    ns = sum(1 for r in rows if r["deontic_soft"])
    noa = sum(1 for r in rows if r["ontology_only"])
    nno = sum(1 for r in rows if r["n_asserts"] == 0)
    print(f"\nmodules with >=1 forbid/permit/oblige : {nh}/{len(rows)}")
    print(f"modules prefer-only                   : {ns}")
    print(f"modules with NO asserts at all        : {nno}")
    print(f"modules ontology-only (onto>0,asrt=0) : {noa}")
    print(f"\nontology facts total = {len(onto_atoms)}   body-less (no ':-') = {bodyless}")
    lic = collections.Counter(l for _, _, l in onto_atoms)
    print("ontology licences:", dict(lic))
    print("\nsample body-less ontology atoms:")
    for cid, a, l in onto_atoms[:15]:
        if ":-" not in a:
            print(f"   {cid}: {a}")

    json.dump(rows, open(os.path.join(OUT, "census.json"), "w"), indent=1)

    # pre-registered sample
    ids = sorted(tr)
    samp = random.Random(20260815).sample(ids, 40)
    payload = []
    for cid in sorted(samp):
        run, f, d = tr[cid]
        pu = f[:-5] + ".prompt_user.txt"
        payload.append(dict(clause_id=cid, run=run, prompt_user=pu))
    json.dump(payload, open(os.path.join(OUT, "sample.json"), "w"), indent=1)
    print(f"\nsample.json written: {len(payload)} items")

main()
