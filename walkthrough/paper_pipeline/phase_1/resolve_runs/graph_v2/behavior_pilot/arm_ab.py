#!/usr/bin/env python3
"""ARM 3 instruments — both sub-arms, fully symbolic, $0.

(a) SYMBOLIC-ONLY : relevance-by-act (assert heads through act bridges).
(b) +MUTATION      : refine (a) by firing + scope mutation (Matt's design).
    For each act-engaged module, one clingo solve per (original + each
    mutation) with the behavior's canonical facts through the situation
    bridges:
      scope_confirmed  — fires under the original facts (kept)
      scope_mismatched — silent under the original but fires under >=1
                         mutant: the module POSITIVELY engages a different
                         scope (declined)
      undetermined     — silent everywhere: its body needs facts the
                         behavior does not state; the act evidence stands
                         (kept). Three states, never collapsed.
Scores any slice of arm3_split.json against the assembled Fable truth.

Usage: .../.venv/bin/python arm_ab.py [--slice validation|test|tuning] [--behavior S]
"""
import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))
import behavior_match as BM, link_nodes, mutation_scope as MS
import relevance_by_act as RBA

FKEY = {"helpfulness": "help", "harm-avoidance-to-third-parties": "harm", "avoiding-over-and-under-caution": "caution"}


def truth_for(slug):
    t = {**json.load(open(os.path.join(HERE, "panel_run1", f"adjudication_run2_{FKEY[slug]}.json")))["rulings"],
         **json.load(open(os.path.join(HERE, "panel_run1", "agreed_negative_rulings.json")))["rulings"][slug]}
    for p in glob.glob(os.path.join(HERE, "panel_run1", f"arm2_{FKEY[slug]}_r*_fresh_rulings.json")):
        t.update(json.load(open(p))["rulings"])
    nr = json.load(open(os.path.join(HERE, "panel_run1", "arm3_negative_rulings.json")))["rulings"].get(slug, {})
    t.update(nr)
    return t


def arm_b_states(slug, engaged_nodes, spec, sel, bridges):
    states = {}
    for i, cid in enumerate(sorted(engaged_nodes)):
        try:
            lp = BM.render_behavior_module("b3", slug, spec["facts"], spec["does"])
            base = BM.relevance_query([cid], lp + "\n" + bridges, selected=sel)
            fires = cid in (base.get("relevant_modules") or []) or bool(base.get("relevant_modules"))
        except Exception:
            states[cid] = "undetermined"; continue
        if fires:
            states[cid] = "scope_confirmed"; continue
        mut_fired = False
        for mname, (orig, mut) in spec["mutations"].items():
            f2 = [mut if f == orig else f for f in spec["facts"]]
            try:
                lp2 = BM.render_behavior_module("b3", slug, f2, spec["does"])
                q2 = BM.relevance_query([cid], lp2 + "\n" + bridges, selected=sel)
                if q2.get("relevant_modules"): mut_fired = True; break
            except Exception: pass
        states[cid] = "scope_mismatched" if mut_fired else "undetermined"
        if (i + 1) % 100 == 0: print(f"  {slug}: {i+1}/{len(engaged_nodes)} classified", flush=True)
    return states


def score(label, eng, slice_nodes, truth):
    U = [n for n in slice_nodes if n in truth]; R = {n for n in U if truth[n] == "relevant"}
    e = [n for n in U if n in eng]; d = [n for n in U if n not in eng]
    ed = sum(truth[n] == "relevant" for n in e); dd = sum(truth[n] == "not_relevant" for n in d)
    dev = (ed + dd) / len(U) if U else 0
    rec = len(R & set(eng)) / len(R) if R else 0
    print(f"   {label:22s} eng {len(e):3d} prec {ed}/{len(e) if e else 1}={ed/len(e) if e else 0:.2f} | dec {len(d):3d} def {dd}/{len(d) if d else 1}={dd/len(d) if d else 0:.2f} | recall {rec:.2f} | DEV-DEF {dev:.2f}")
    return {"engaged": len(e), "engagement_def": f"{ed}/{len(e)}", "decline_def": f"{dd}/{len(d)}", "recall": round(rec, 3), "deviation_def": round(dev, 3)}


def main():
    slice_name = sys.argv[sys.argv.index("--slice") + 1] if "--slice" in sys.argv else "validation"
    only = sys.argv[sys.argv.index("--behavior") + 1] if "--behavior" in sys.argv else None
    canon_f = sys.argv[sys.argv.index("--canonical") + 1] if "--canonical" in sys.argv else "behaviors_canonical.json"
    mods_f = sys.argv[sys.argv.index("--modules") + 1] if "--modules" in sys.argv else "modules_contract_v1.json"
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    spl = json.load(open(os.path.join(HERE, "panel_run1", "arm3_split.json")))["split"]
    beh = json.load(open(os.path.join(HERE, canon_f)))["behaviors"]
    mods = json.load(open(os.path.join(HERE, mods_f)))["modules"]
    br_map = RBA.bridges(); corpus = RBA.corpus_acts()
    sel = link_nodes.gather()
    sit_bridges = MS.behavior_to_corpus_bridges()
    out = {}
    for slug, spec in beh.items():
        if only and slug != only: continue
        truth = truth_for(slug); slc = spl[slug][slice_name]
        acts, rel_a = RBA.relevance(mods[slug], br_map, corpus)
        eng_a = set(rel_a)
        print(f"\n== {slug} [{slice_name}] act-engaged {len(eng_a)}")
        states = arm_b_states(slug, eng_a, spec, sel, sit_bridges)
        eng_b = {n for n, st in states.items() if st != "scope_mismatched"}
        from collections import Counter
        cnt = Counter(states.values())
        print(f"   states: {dict(cnt)}")
        sa = score("arm (a) act-only", eng_a, slc, truth)
        sb = score("arm (b) +mutation", eng_b, slc, truth)
        out[slug] = {"slice": slice_name, "act_engaged": len(eng_a), "states": dict(cnt), "arm_a": sa, "arm_b": sb,
                     "scope_mismatched": sorted(n for n, st in states.items() if st == "scope_mismatched")}
    json.dump(out, open(os.path.join(HERE, "panel_run1", f"arm_ab_{slice_name}{tag}.json"), "w"), indent=1)
    print(f"\nwrote panel_run1/arm_ab_{slice_name}{tag}.json")


if __name__ == "__main__":
    main()
