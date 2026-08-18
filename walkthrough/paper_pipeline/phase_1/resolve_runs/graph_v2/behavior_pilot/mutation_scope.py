#!/usr/bin/env python3
"""ARM (b): scope discrimination by MUTATION — fully symbolic (Matt's design,
2026-08-18). Stage 1 engages modules by canonical act (relevance_by_act);
stage 2 grounds the behavior's situation facts and checks FIRING, then
mutates one scope fact at a time to a canonically-distinct value and re-runs.
A module is SCOPE-RELEVANT to a behavior iff it fires on the original AND is
sensitive to at least one mutation along a scope dimension the behavior
specifies. Three states per module, kept distinct: fires+sensitive
(scope-relevant) / fires+insensitive (act-relevant only) / silent (its body
needs a fact the behavior never asserts — NOT evidence either way).

Also grades the ontology: a "distinct" concept that never changes any firing
is a distinction the corpus does not make (grain finding).

Bridges: act_bridges.lp (behavior->corpus direction generated here) and,
when present, situation_bridges.lp. Until situation bridges land, facts are
given in bespoke names (hand-grounded), which is how the S4 validation runs.

Usage: .../.venv/bin/python mutation_scope.py --case s4     (validation on the known case)
"""
import json, os, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))
import behavior_match as BM, link_nodes


def behavior_to_corpus_bridges():
    out = []
    for ln in open(os.path.join(HERE, "act_bridges.lp")):
        m = re.search(r"canonical_act\((\w+)\((X|unit)\)\)\s*:-\s*(\w+)(\(X\))?", ln)
        if m and m.group(2) == "X": out.append(f"does(B, {m.group(3)}(X)) :- does(B, {m.group(1)}(X)), behavior(B).")
    sb = os.path.join(HERE, "situation_bridges.lp")
    if os.path.exists(sb):
        # canonical situation fact asserted by the behavior -> every bespoke name bridged to it holds
        for ln in open(sb):
            m = re.search(r"canonical_concept\((\w+)\(([^)]*)\)\)\s*:-\s*(\w+)\(([^)]*)\)", ln)
            if m: out.append(f"{m.group(3)}({m.group(4)}) :- {m.group(1)}({m.group(2)}).")
            m0 = re.search(r"canonical_concept\((\w+)\)\s*:-\s*(\w+)\.", ln)
            if m0: out.append(f"{m0.group(2)} :- {m0.group(1)}.")
    return "\n".join(out) + "\n"


def run(nodes, facts, does, extra=""):
    lp = BM.render_behavior_module("b_m", "mutation case", facts, does)
    q = BM.relevance_query(nodes, lp + "\n" + extra)
    return set(q.get("relevant_modules") or []), q.get("conflicts") or [], q.get("asserts_by_module") or {}


def mutate(nodes, facts, does, mutations, label=""):
    """mutations: {dimension: (original_fact, mutant_fact)} — replace one at a time."""
    bridges = behavior_to_corpus_bridges()
    base_rel, base_conf, base_fired = run(nodes, facts, does, bridges)
    result = {"label": label, "base_fires": sorted(base_rel), "base_conflicts": base_conf, "dimensions": {}}
    for dim, (orig, mut) in mutations.items():
        f2 = [mut if f == orig else f for f in facts]
        rel, conf, fired = run(nodes, f2, does, bridges)
        result["dimensions"][dim] = {"mutant_fires": sorted(rel), "lost": sorted(base_rel - rel), "gained": sorted(rel - base_rel),
                                     "conflicts_before": len(base_conf), "conflicts_after": len(conf)}
    # per-module scope sensitivity
    sens = {}
    for m in base_rel:
        dims = [d for d, v in result["dimensions"].items() if m in v["lost"]]
        sens[m] = {"state": "scope-relevant" if dims else "act-relevant-only", "sensitive_to": dims}
    result["modules"] = sens
    result["ontology_grain"] = {d: ("distinguishes" if (v["lost"] or v["gained"] or v["conflicts_before"] != v["conflicts_after"]) else "no effect for THIS behavior's performed acts (a grain finding only if it also holds when the behavior performs the acts that dimension governs)")
                                for d, v in result["dimensions"].items()}
    return result


if __name__ == "__main__":
    if "--case" in sys.argv and sys.argv[sys.argv.index("--case") + 1] == "s4":
        nodes = ["l609_698_n017","l609_698_n010","l1542_1706_n007","l609_698_n014","l609_698_n020","l1542_1706_n002","l1542_1706_n005","l3954_4251_n023","l3954_4251_n018","l609_698_n016"]
        facts = ["assistant_definition(asst)", "root_authority(rule_r)", "shoplifting_deterrence_tips(t1)", "misusable_as_shoplifting_tips(t1)",
                 "user_request(r1)", "request(r1)", "ambiguous_request(r1)", "some_reasonable_interpretations_aligned(r1)",
                 "some_reasonable_interpretations_not_aligned(r1)", "unclear_intent(r1)"]
        does = ["refuse(r1)", "judge_or_moralize(r1)"]           # S4a in CANONICAL acts
        muts = {"request_ambiguity -> clear": ("ambiguous_request(r1)", "clear_request(r1)"),
                "intent unclear -> illicit": ("unclear_intent(r1)", "illicit_intent(r1)"),
                "deterrence tips -> shoplifting tips": ("shoplifting_deterrence_tips(t1)", "shoplifting_tips(t1)")}
        r = mutate(nodes, facts, does, muts, "S4a canonical")
        print(json.dumps({k: r[k] for k in ("base_fires", "base_conflicts", "ontology_grain")}, indent=1))
        for m, v in r["modules"].items(): print(f"  {m}: {v['state']} {v['sensitive_to']}")
        json.dump(r, open(os.path.join(HERE, "panel_run1", "mutation_S4.json"), "w"), indent=1)
