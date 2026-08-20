#!/usr/bin/env python3
"""SATISFIABILITY CENSUS (Matt's design, 2026-08-19) — deterministic, $0.

For each behavior, build every node's FEATURE VECTOR as the instrument sees it:
the set of (canonical act, status) pairs it can engage through, plus the union
of its asserts' governs / protects / contexts / actor values. Two nodes with
identical vectors CANNOT be separated by any wall or bridge configuration —
the instrument is a function of the vector. So:

  * a MISMATCH whose vector collides with a correctly-handled node of the
    OPPOSITE verdict is UNSAT at current granularity (fixing it must break
    the other node);
  * a mismatch with NO collision is SEPARABLE — some configuration handles it,
    and it should never be declared terminal.

This makes the terminal/fixable boundary a computation instead of a judgment.
Usage: .../.venv/bin/python satisfiability_census.py modules_contract_v17.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import relevance_by_act as RBA
import arm_ab as AB


def load_layers():
    sig = json.load(open(os.path.join(HERE, "assert_signature.json")))
    ap = json.load(open(os.path.join(HERE, "assert_protects.json")))
    pa = json.load(open(os.path.join(HERE, "assert_purpose_actor.json")))
    return sig, ap, pa


def vector(nid, corpus, br, sig, ap, pa):
    keys = sorted(k for k in sig if k.startswith(nid + "|"))
    acts = frozenset((br.get(f), s) for f, s in corpus.get(nid, []) if br.get(f))
    governs = frozenset(g for k in keys for g in sig[k]["governs"])
    contexts = frozenset(c for k in keys for c in sig[k].get("contexts", []))
    protects = frozenset(p for k in keys for p in ap.get(k, []))
    actors = frozenset(pa[k]["actor"] for k in keys if k in pa)
    purposes = frozenset(e for k in keys if k in pa for e in pa[k]["purpose"])
    return (acts, governs, contexts, protects, actors, purposes)


def truth_all(slug):
    t = dict(AB.truth_for(slug))
    fmap = {"helpfulness": [("fresh_draw", "HELP_RESULT"), ("fresh_draw2", "HELP_R2_RESULT"), ("fresh_draw3", "HELP_R3_RESULT")],
            "harm-avoidance-to-third-parties": [("fresh_draw2", "HARM_R2_RESULT")],
            "avoiding-over-and-under-caution": [("fresh_draw2", "CAUTION_R2_RESULT")]}
    for rd, f in fmap[slug]:
        p = os.path.join(HERE, "panel_run1", rd, f + ".json")
        if os.path.exists(p):
            t.update(json.load(open(p))["truth"])
    return t


def census(modules_file):
    mods = json.load(open(os.path.join(HERE, modules_file)))["modules"]
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    sig, ap, pa = load_layers()
    report = {}
    for slug in mods:
        _, rel = RBA.relevance(mods[slug], br, corpus)
        eng = set(rel)
        t = truth_all(slug)
        vecs = {}
        for n in t:
            vecs.setdefault(vector(n, corpus, br, sig, ap, pa), []).append(n)
        rows = {}
        for n, v in t.items():
            correct = (v == "relevant") == (n in eng)
            if correct:
                continue
            twins = [m for m in vecs[vector(n, corpus, br, sig, ap, pa)]
                     if m != n and ((t[m] == "relevant") == (m in eng)) and t[m] != v]
            rows[n] = {"verdict_needed": v, "status": "UNSAT" if twins else "SEPARABLE",
                       "colliding_correct_nodes": twins}
        report[slug] = rows
    return report


if __name__ == "__main__":
    mf = sys.argv[1] if len(sys.argv) > 1 else "modules_contract_v17.json"
    rep = census(mf)
    for slug, rows in rep.items():
        unsat = [n for n, r in rows.items() if r["status"] == "UNSAT"]
        sep = [n for n, r in rows.items() if r["status"] == "SEPARABLE"]
        print(f"== {slug}: {len(rows)} mismatches -> UNSAT {len(unsat)}, SEPARABLE {len(sep)}")
        for n in unsat:
            print(f"   UNSAT {n} collides with {rows[n]['colliding_correct_nodes'][:4]}")
    out = os.path.join(HERE, "panel_run1", "convergence", "satisfiability_census.json")
    json.dump({"_": __doc__.strip().splitlines()[0], "report": rep}, open(out, "w"), indent=1)
    print("wrote", out)
