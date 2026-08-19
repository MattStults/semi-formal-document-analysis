#!/usr/bin/env python3
"""INPUT-RELEVANCE channel (Matt's design, 2026-08-18): a module with no
acts is relevant to a behavior when it PROVIDES a name that an
act-relevant module CONSUMES — the ranking/definition is an input to a
norm that engages. Symbolic, $0, reason printable: 'provides <name>,
consumed by <module> which asserts on <act>'. One hop by default (a
provider of a provider is attention-diluting; measured before widening).
Reported as a distinct state ("input_relevant"), never merged silently
into act engagement."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))
import link_nodes

_BODY = re.compile(r":-(.*?)\.", re.S); _ATOM = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")


def indexes():
    sel = link_nodes.gather()
    provides, consumes = {}, {}
    for cid, (lp, o, r) in sel.items():
        names = set()
        for key in ("defines", "provides"):
            for d in o.get(key) or []:
                n = d.get("name") if isinstance(d, dict) else str(d).split("/")[0].split("(")[0]
                if n: names.add(n.strip())
        for d in o.get("ontology") or []:
            m = re.match(r"([a-z_][A-Za-z0-9_]*)", str(d.get("atom", "")))
            if m: names.add(m.group(1))
        for n in names: provides.setdefault(n, set()).add(cid)
        used = set()
        for s in o.get("requires") or []: used.add(str(s).split("/")[0].split("(")[0].strip())
        txt = open(lp, encoding="utf-8").read()
        for b in _BODY.findall(txt): used |= set(_ATOM.findall(b))
        consumes[cid] = used
    return provides, consumes


def input_relevant(act_engaged, provides, consumes, exclude=None, max_providers=2, min_consumers=2):
    """provider cid -> reasons, one hop, SPECIFICITY-WEIGHTED (2026-08-18,
    Matt's gate backlog item 4). Measured over-fire: providers of widely-
    shared names (scaffolding) engage everywhere. A name counts only if
    (a) few modules provide it (<= max_providers — it is THIS provider's
    concept, not corpus scaffolding), and (b) the provider is consumed by
    >= min_consumers act-engaged modules OR provides a name consumed by an
    engaged module at >= 2 distinct names (multi-thread dependence)."""
    seam = set()
    sp = os.path.join(G2, "SEAM_CONTRACT.json")
    if os.path.exists(sp): seam = set(json.load(open(sp))["names"])
    raw = {}
    for consumer in act_engaged:
        for n in consumes.get(consumer, ()):
            if n in seam: continue                       # scaffolding by definition
            provs = provides.get(n, ())
            if len(provs) > max_providers: continue      # shared scaffolding
            for provider in provs:
                if provider == consumer or provider in act_engaged: continue
                if exclude and provider in exclude: continue
                raw.setdefault(provider, []).append((n, consumer))
    return {p: v for p, v in raw.items()
            if len({c for _, c in v}) >= min_consumers or len({n for n, _ in v}) >= 2}


if __name__ == "__main__":
    import relevance_by_act as RBA, arm_ab
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    provides, consumes = indexes()
    mods = json.load(open(os.path.join(HERE, sys.argv[sys.argv.index("--modules") + 1] if "--modules" in sys.argv else "modules_contract_v4.json")))["modules"]
    spl = json.load(open(os.path.join(HERE, "panel_run1", "arm3_split.json")))["split"]
    slice_name = sys.argv[sys.argv.index("--slice") + 1] if "--slice" in sys.argv else "tuning"
    report = {}
    for slug, mod in mods.items():
        truth = arm_ab.truth_for(slug)
        _, rel = RBA.relevance(mod, br, corpus)
        eng_a = set(rel)
        dep = input_relevant(eng_a, provides, consumes)
        slc = [n for n in spl[slug][slice_name] if n in truth]
        # score: act-only vs act+dependency
        for label, eng in (("act-only", eng_a), ("act+input", eng_a | set(dep))):
            e = [n for n in slc if n in eng]; d = [n for n in slc if n not in eng]
            ed = sum(truth[n] == "relevant" for n in e); dd = sum(truth[n] == "not_relevant" for n in d)
            R = {n for n in slc if truth[n] == "relevant"}
            print(f"{slug[:28]:28s} {label:10s} eng {len(e):3d} prec {ed/len(e) if e else 0:.2f} recall {len(R & set(eng))}/{len(R)}={len(R & set(eng))/len(R) if R else 0:.2f} DEV-DEF {(ed+dd)/len(slc):.2f}")
        report[slug] = {"input_relevant_count": len(dep),
                        "sample_reasons": {p: [f"provides {n} <- {c}" for n, c in v[:2]] for p, v in list(dep.items())[:6]}}
    json.dump(report, open(os.path.join(HERE, "panel_run1", f"input_relevance_{slice_name}.json"), "w"), indent=1)
