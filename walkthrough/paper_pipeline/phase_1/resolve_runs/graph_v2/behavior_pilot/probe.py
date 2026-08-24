#!/usr/bin/env python3
"""HYPOTHESIS PROBE — funnel level 0 (CHEAP_TIER_DRIVER_DESIGN.md v3).

One command, seconds, $0: takes a candidate module delta and reports its
complete counterfactual against the assembled truth ledger WITHOUT touching
any contract file — charter (fixes/breaks), the affected-node lists, and
the REASON-SIGNATURE diff over verdict-unchanged nodes (v2 addendum B:
'substituted' and 'degraded' paths surface even when the verdict bit holds;
degraded = the node's engagement is now carried ONLY by the purpose channel
or survives with a strictly smaller act-reason set).

Usage:
  probe.py <slug> '<json delta>'          # delta = partial module dict,
                                          # e.g. '{"governs_concern": [...]}'
  probe.py <slug> --file delta.json
  probe.py <slug> <delta...> --contract <file> --truth <file>
      # iteration-1 extension (2026-08-24): probe a slug that lives in a
      # different contract file and/or whose truth is not in truth_all's
      # fmap (the generalization venue). --truth points at a committed
      # {node: verdict} artifact; defaults unchanged.
Appends one record to HYPOTHESIS_LEDGER.jsonl (append-only: hypothesis,
charter, drift counts, verdict) so dead branches are never re-explored.
"""
import json, sys, os, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import relevance_by_act as RBA
import satisfiability_census as SC

def reasons(rel):
    return {n: frozenset(map(tuple, v)) for n, v in rel.items()}

def main():
    argv = list(sys.argv[1:])
    contract, truth_file = "modules_contract_v19.json", None
    if "--contract" in argv:
        i = argv.index("--contract"); contract = argv[i + 1]; del argv[i:i + 2]
    if "--truth" in argv:
        i = argv.index("--truth"); truth_file = argv[i + 1]; del argv[i:i + 2]
    slug = argv[0]
    raw = open(argv[2]).read() if argv[1] == "--file" else argv[1]
    delta = json.loads(raw)
    mods = json.load(open(os.path.join(HERE, contract)))["modules"]
    truth = (json.load(open(os.path.join(HERE, truth_file)))["truth"]
             if truth_file else SC.truth_all(slug))
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    _, rel0 = RBA.relevance(mods[slug], br, corpus)
    m = copy.deepcopy(mods[slug]); m.update(delta)
    _, rel1 = RBA.relevance(m, br, corpus)
    e0, e1 = set(rel0), set(rel1)
    lost, gained = e0 - e1, e1 - e0
    fx = sorted([n for n in lost if truth.get(n) == "not_relevant"]
                + [n for n in gained if truth.get(n) == "relevant"])
    bk = sorted([n for n in lost if truth.get(n) == "relevant"]
                + [n for n in gained if truth.get(n) == "not_relevant"])
    r0, r1 = reasons(rel0), reasons(rel1)
    drift = {"augmented": [], "substituted": [], "degraded": []}
    P = ("__purpose__", "purpose_channel", "end")
    for n in e0 & e1:
        if r0[n] == r1[n]:
            continue
        if r1[n] > r0[n]:
            drift["augmented"].append(n)
        elif (P,) == tuple(r1[n]) and P not in r0[n] or (r1[n] < r0[n]):
            drift["degraded"].append(n)
        else:
            drift["substituted"].append(n)
    rec = {"slug": slug, "delta": delta,
           "charter": {"fixes": len(fx), "breaks": len(bk)},
           "fixed_nodes": fx, "broken_nodes": bk,
           "lost": len(lost), "gained": len(gained),
           "unruled_lost": sum(1 for n in lost if n not in truth),
           "unruled_gained": sum(1 for n in gained if n not in truth),
           "reason_drift": {k: len(v) for k, v in drift.items()},
           "drift_nodes": drift,
           "verdict": ("KILL (charter-negative)" if len(bk) >= len(fx) and (fx or bk)
                       else "KILL (inert)" if not (fx or bk or any(drift.values()))
                       else "DEGRADED-BREAKS" if drift["degraded"]
                       else "ADVANCE to level 1/2")}
    with open(os.path.join(HERE, "HYPOTHESIS_LEDGER.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")
    slim = {k: v for k, v in rec.items()
            if k not in ("fixed_nodes", "broken_nodes", "drift_nodes")}
    print(json.dumps(slim, indent=1))

if __name__ == "__main__":
    main()
