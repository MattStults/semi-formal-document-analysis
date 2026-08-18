#!/usr/bin/env python3
"""SYMBOLIC relevance — relevance-by-act over the corpus, $0, deterministic.

Matt's ruling 2026-08-18: relevance must use the ASP corpus, not prose. A
module is RELEVANT-BY-ACT to a behavior iff it asserts a deontic status on a
canonical act the behavior performs (`does`), where the module's bespoke act
maps to the canonical act through act_bridges.lp. This is a STATIC read of
assert heads (no case facts needed): "does this clause govern an act the
behavior performs?" — the question a user asks first, answered with a stated
reason ("relevant because it forbids a kind of refusal"). The clingo FIRING
query (relevance_query) remains the stronger second stage once situation
facts are grounded.

Reports per behavior: relevant modules with the (bespoke act -> canonical
act, status) reason; per-branch coverage; and, when Fable truth exists,
the same defensibility metrics as the seat, on the same held-out halves —
so the two instruments sit side by side.

Usage: .../.venv/bin/python relevance_by_act.py modules_tuned_r2.json [--score]
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))
import link_nodes

_BR = re.compile(r"canonical_act\((\w+)\((?:X|unit)\)\)\s*:-\s*(\w+)")


def bridges():
    m = {}
    for ln in open(os.path.join(HERE, "act_bridges.lp")):
        mm = _BR.search(ln)
        if mm: m[mm.group(2)] = mm.group(1)
    return m


def corpus_acts():
    """cid -> [(bespoke_functor, status)] from assert heads."""
    out = {}
    for cid, (lp, obj, run) in link_nodes.gather().items():
        rows = []
        for a in obj.get("asserts") or []:
            f = re.match(r"([a-z_][A-Za-z0-9_]*)", str(a.get("act", "")))
            if f: rows.append((f.group(1), a.get("status")))
        out[link_nodes.norm_id(cid)] = rows
    return out


def behavior_acts(mod):
    """canonical acts a behavior PERFORMS: heads of `does` that are canonical, else act atoms bridged by name."""
    canon = set(json.load(open(os.path.join(HERE, "behavior_vocab.json")))["canonical_acts_provisional"])
    acts = set()
    for r in (mod.get("module") or {}).get("does", []):
        h = re.match(r"\s*(?:not\s+|-)?([a-z_][A-Za-z0-9_]*)", r)
        if h and h.group(1) in canon: acts.add(h.group(1))
    return acts, canon


def relevance(mod, br, corpus):
    acts, canon = behavior_acts(mod)
    per_atom_canon = {}                       # for per-branch coverage: atom -> canonical act via the atom's own performed act
    rel = {}
    for cid, rows in corpus.items():
        reasons = [(f, br.get(f), st) for f, st in rows if br.get(f) in acts]
        if reasons: rel[cid] = reasons
    return acts, rel


def main():
    path = sys.argv[1]; score = "--score" in sys.argv
    mods = json.load(open(path))["modules"]
    br = bridges(); corpus = corpus_acts()
    print(f"bridges {len(br)}; corpus modules {len(corpus)}")
    report = {}
    for slug, mod in mods.items():
        if "module" not in mod: continue
        acts, rel = relevance(mod, br, corpus)
        print(f"\n== {slug}: performs {sorted(acts)}; relevant-by-act modules {len(rel)}")
        report[slug] = {"performs": sorted(acts), "relevant": {c: [f"{f}->{ca}:{st}" for f, ca, st in v] for c, v in rel.items()}}
        if score:
            sp = json.load(open(os.path.join(HERE, "panel_run1", "arm2_split.json")))["split"][slug]
            held = set(sp["held_out"])
            f = {"helpfulness": "help", "harm-avoidance-to-third-parties": "harm", "avoiding-over-and-under-caution": "caution"}[slug]
            truth = {**json.load(open(os.path.join(HERE, "panel_run1", f"adjudication_run2_{f}.json")))["rulings"],
                     **json.load(open(os.path.join(HERE, "panel_run1", "agreed_negative_rulings.json")))["rulings"][slug]}
            import glob
            for p in glob.glob(os.path.join(HERE, "panel_run1", f"arm2_{f}_r*_fresh_rulings.json")):
                truth.update(json.load(open(p))["rulings"])
            U = [n for n in held if n in truth]; R = {n for n in U if truth[n] == "relevant"}
            e = [n for n in U if n in rel]; d = [n for n in U if n not in rel]
            ed = sum(truth[n] == "relevant" for n in e); dd = sum(truth[n] == "not_relevant" for n in d)
            dev = (ed + dd) / len(U) if U else 0
            print(f"   HELD-OUT {len(U)}: engaged {len(e)} def {ed}/{len(e) if e else 1}={ed/len(e) if e else 0:.2f} | declined {len(d)} def {dd}/{len(d) if d else 1}={dd/len(d) if d else 0:.2f} | recall {len(R & set(rel))}/{len(R)}={len(R & set(rel))/len(R) if R else 0:.2f} | DEVIATION-DEF {ed+dd}/{len(U)}={dev:.2f}")
            report[slug]["held_out"] = {"engaged": len(e), "engagement_def": f"{ed}/{len(e)}", "decline_def": f"{dd}/{len(d)}", "recall": f"{len(R & set(rel))}/{len(R)}", "deviation_def": round(dev, 3)}
    json.dump(report, open(os.path.join(HERE, "panel_run1", "relevance_by_act.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
