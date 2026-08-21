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

VECTOR FAITHFULNESS (Arc1-e fix, 2026-08-21, prereg panel_run1/convergence/
CENSUS_VECTOR_FIX_PREREG.md): the vector mirrors relevance_by_act.relevance()
EXACTLY — assert layers merged with the definition_* lanes (keys nid|c{i}),
including the lane-scope jurisdiction ruling: purpose credits from
definitional keys never feed the purpose OR-channel (verdict-gated on the
assert lane only), while actor credits from definitional keys DO feed the
actor wall. Two views are reported: CURRENT (the instrument as frozen) and
REACHABLE (CURRENT plus consensus context-atom credits — annotated but
undeclared vocabulary, the 9b design round's input; inventory-relative
terminality per contract 9g).
Usage: .../.venv/bin/python satisfiability_census.py modules_contract_v18.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import relevance_by_act as RBA
import arm_ab as AB


def load_layers():
    def merged(assert_name, lane_name):
        p = os.path.join(HERE, assert_name)
        d = json.load(open(p)) if os.path.exists(p) else {}
        lp = os.path.join(HERE, lane_name)
        if os.path.exists(lp):
            d = {**d, **json.load(open(lp))}     # mirrors relevance(): {**assert, **definition}
        return d
    sig = merged("assert_signature.json", "definition_signature.json")
    ap = merged("assert_protects.json", "definition_protects.json")
    pa = merged("assert_purpose_actor.json", "definition_purpose_actor.json")
    cp = os.path.join(HERE, "panel_run1", "convergence", "context_atoms_consensus.json")
    ctx = json.load(open(cp))["credits"] if os.path.exists(cp) else {}
    return sig, ap, pa, ctx


def vector(nid, corpus, br, sig, ap, pa, ctx=None, asorts=None):
    # layer-independent key sets: relevance() looks each layer up by node
    # prefix on its own; a node annotated in one layer but not another must
    # still contribute the layers it has.
    skeys = sorted(k for k in sig if k.startswith(nid + "|"))
    pkeys = sorted(k for k in ap if k.startswith(nid + "|"))
    akeys = sorted(k for k in pa if k.startswith(nid + "|"))
    # (canonical act, status, functor arg-sort): all v18 behaviors declare
    # arg_sorts, so arg_ok() is live and the functor's raw sort is
    # instrument-visible (None = unspecified -> fail-open, as in arg_ok)
    acts = frozenset((br.get(f), s, (asorts or {}).get(f))
                     for f, s in corpus.get(nid, []) if br.get(f))
    governs = frozenset(g for k in skeys for g in sig[k]["governs"])
    contexts = frozenset(c for k in skeys for c in sig[k].get("contexts", []))
    protects = frozenset(p for k in pkeys for p in ap.get(k, []))
    actors = frozenset(pa[k]["actor"] for k in akeys)
    # lane-scope ruling (2026-08-20): definitional keys (|c{i}) never feed
    # the purpose OR-channel, so their purposes are not instrument-visible
    purposes = frozenset(e for k in akeys
                         if not k.split("|")[1].startswith("c")
                         for e in pa[k]["purpose"])
    # all-plumbing exclusion (signature_ok) is instrument-visible
    plumbing = frozenset(k.split("|")[1] for k in skeys
                         if sig[k].get("authority_plumbing"))
    cur = (acts, governs, contexts, protects, actors, purposes, plumbing)
    if ctx is None:
        return cur
    catoms = frozenset(a for vs in (ctx.get(nid) or {}).values() for a in vs)
    return (acts, governs, contexts | catoms, protects, actors, purposes, plumbing)


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
    for slug, m in mods.items():
        if m.get("party_concern"):
            raise NotImplementedError(
                f"{slug} declares party_concern: census vector() carries no "
                "act-party feature — extend vector() before running (Arc1-e addendum)")
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    sig, ap, pa, ctx = load_layers()
    asorts = RBA.arg_sorts()
    report = {}
    for slug in mods:
        _, rel = RBA.relevance(mods[slug], br, corpus)
        eng = set(rel)
        t = truth_all(slug)
        vecs, groups_cur, groups_rch = {}, {}, {}
        for n in t:
            vc = vector(n, corpus, br, sig, ap, pa, None, asorts)
            vr = vector(n, corpus, br, sig, ap, pa, ctx, asorts)
            vecs[n] = (vc, vr)
            groups_cur.setdefault(vc, []).append(n)
            groups_rch.setdefault(vr, []).append(n)

        def view(n, groups, idx):
            twins = [m for m in groups[vecs[n][idx]]
                     if m != n and ((t[m] == "relevant") == (m in eng)) and t[m] != t[n]]
            return ("UNSAT" if twins else "SEPARABLE"), twins

        rows = {}
        for n, v in t.items():
            correct = (v == "relevant") == (n in eng)
            if correct:
                continue
            sc, tc = view(n, groups_cur, 0)
            sr, tr = view(n, groups_rch, 1)
            rows[n] = {"verdict_needed": v, "status": sc, "colliding_correct_nodes": tc,
                       "status_reachable": sr, "colliding_correct_nodes_reachable": tr}
        report[slug] = rows
    return report


if __name__ == "__main__":
    mf = sys.argv[1] if len(sys.argv) > 1 else "modules_contract_v18.json"
    rep = census(mf)
    for slug, rows in rep.items():
        unsat = [n for n, r in rows.items() if r["status"] == "UNSAT"]
        sep = [n for n, r in rows.items() if r["status"] == "SEPARABLE"]
        runsat = [n for n, r in rows.items() if r["status_reachable"] == "UNSAT"]
        print(f"== {slug}: {len(rows)} mismatches -> CURRENT UNSAT {len(unsat)}, SEPARABLE {len(sep)}"
              f" | REACHABLE UNSAT {len(runsat)}, SEPARABLE {len(rows) - len(runsat)}")
        for n in unsat:
            print(f"   UNSAT {n} collides with {rows[n]['colliding_correct_nodes'][:4]}")
    # contract-stamped output name: earlier runs (v17-era, cited by
    # decl_search_proto) live in satisfiability_census.json and stay untouched
    stem = os.path.splitext(os.path.basename(mf))[0]
    out = os.path.join(HERE, "panel_run1", "convergence", f"satisfiability_census_{stem}.json")
    json.dump({"_": __doc__.strip().splitlines()[0], "contract": mf, "report": rep}, open(out, "w"), indent=1)
    print("wrote", out)
