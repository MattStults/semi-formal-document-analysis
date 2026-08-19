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
    """functor -> canonical, ASSISTANT-performed acts only (H5: a developer's
    or user's act must not engage an assistant behavior; act_actors.json)."""
    ap = os.path.join(HERE, "act_actors.json")
    actors = json.load(open(ap)) if os.path.exists(ap) else {}
    m = {}
    for ln in open(os.path.join(HERE, "act_bridges.lp")):
        mm = _BR.search(ln)
        if mm and actors.get(mm.group(2), "assistant") == "assistant":
            m[mm.group(2)] = mm.group(1)
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
    sp = os.path.join(HERE, "act_subtypes.json")
    if os.path.exists(sp): canon |= set(json.load(open(sp)).values())
    acts = set()
    for r in (mod.get("module") or {}).get("does", []):
        h = re.match(r"\s*(?:not\s+|-)?([a-z_][A-Za-z0-9_]*)", r)
        if h and h.group(1) in canon: acts.add(h.group(1))
    return acts, canon


def parent_map():
    """subtype -> parent for the two-level act ontology (act_subtypes.json).
    Relevance matches at PARENT level (a module about any kind of providing
    is relevant to a behavior about providing); FIRING stays subtype-strict."""
    p = os.path.join(HERE, "act_subtypes.json")
    if not os.path.exists(p): return {}
    subs = set(json.load(open(p)).values())
    return {s: ("provide" if s.startswith(("provide", "disclose")) else "respond")
            for s in subs if s not in ("provide", "respond")}


# argument-sort compatibility groups: sorts that are the same KIND of object
# for engagement purposes (a request and the instruction it carries; content
# and the information in it). Distinct kinds NEVER cross-match: topic vs
# request is the measured H1 failure. Unknown/none/other FAIL OPEN.
ARG_COMPAT = {
    "request": {"request", "instruction", "question", "message"},
    "instruction": {"request", "instruction", "message"},
    "content": {"content", "information", "data"},
    "information": {"content", "information", "data"},
    "data": {"content", "information", "data"},
    "question": {"question", "request"},
    "response": {"response"},
    "action": {"action", "tool"},
    "goal": {"goal"},
    "topic": {"topic"},
    "user": {"user", "party"},
    "party": {"user", "party"},
    "message": {"request", "instruction", "message"},
    "tool": {"action", "tool"},
}


def arg_sorts():
    p = os.path.join(HERE, "act_arg_sorts.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def behavior_arg_sorts(mod):
    """constant -> sort for the behavior's does-arguments, from the module's
    canonical facts naming convention (r*=request, c*=content, resp*=response,
    a*=action, i*=instruction/information, q*=question, s*=setting)."""
    import re as _re
    m = {}
    for r in (mod.get("module") or {}).get("does", []):
        h = _re.match(r"\s*([a-z_][A-Za-z0-9_]*)\(([a-z][a-z0-9]*)\)", r.split(":-")[0])
        if not h: continue
        const = h.group(2)
        sort = {"r": "request", "c": "content", "i": "information", "q": "question", "a": "action", "g": "goal", "u": "user", "w": "content", "t": "topic"}.get(const[0])
        if const.startswith("resp"): sort = "response"
        if sort: m[h.group(1)] = m.get(h.group(1), set()) | {sort}
    return m


# argument walls apply ONLY to verb families whose corpus arguments are
# homogeneous (measured 2026-08-18: respond-family args are heterogeneous —
# walls there cut real engagements, help recall 0.89->0.71 on tuning).
WALLED_VERBS = {"refuse", "comply", "provide", "ask", "act_in_world",
                "provide_information", "provide_content", "provide_resources",
                "disclose_data", "provide_hazardous"}


def relevance(mod, br, corpus):
    acts, canon = behavior_acts(mod)
    pm = parent_map()
    asorts = arg_sorts()
    bargs = behavior_arg_sorts(mod)
    def hits(c):
        if c is None: return False
        return c in acts or pm.get(c) in acts or c in {s for s, par in pm.items() if par in acts and c == s}
    def verb_hit(c):
        return c in acts or pm.get(c) in acts or any(pm.get(a2) == c for a2 in acts)

    def arg_ok(f, c):
        if c not in WALLED_VERBS and pm.get(c) not in WALLED_VERBS: return True
        fa = asorts.get(f)
        if fa in (None, "none", "other"): return True          # fail open
        # behavior arg sorts for the canonical verb (check verb + its parent/children)
        want = set()
        for a2 in acts:
            if a2 == c or pm.get(a2) == c or pm.get(c) == a2: want |= bargs.get(a2, set())
        if not want: return True                                # fail open
        return any(fa == w or fa in ARG_COMPAT.get(w, {w}) or w in ARG_COMPAT.get(fa, {fa}) for w in want)

    rel = {}
    for cid, rows in corpus.items():
        reasons = [(f, br.get(f), st) for f, st in rows
                   if br.get(f) is not None and verb_hit(br[f]) and arg_ok(f, br[f])]
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
