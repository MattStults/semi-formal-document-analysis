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
    # canonical acts are their own bridge (example-act lifting emits canonical
    # names directly; identity mapping, no semantic change for bespoke functors)
    canon = set(json.load(open(os.path.join(HERE, "behavior_vocab.json")))["canonical_acts_provisional"])
    sp = os.path.join(HERE, "act_subtypes.json")
    if os.path.exists(sp): canon |= set(json.load(open(sp)).values())
    hier = json.load(open(os.path.join(HERE, "behavior_vocab.json"))).get("_act_hierarchy", {})
    canon |= set(hier) | set(hier.values())
    for c in canon: m.setdefault(c, c)
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
    # EXAMPLE-ACT LIFTING (contract mechanism, convergence phase-2): worked-example
    # modules assert no acts because the norm lives in what the example's responses
    # DO. example_acts.json (Opus-annotated, span-quoted) supplies the demonstrated
    # canonical acts; good_acts and bad_acts both engage (a norm forbidding the BAD
    # response's act governs that act). Acts are already canonical — bridged 1:1.
    ep = os.path.join(HERE, "example_acts.json")
    if os.path.exists(ep):
        ex = json.load(open(ep))["acts"]
        for node, d in ex.items():
            if node in out and not out[node]:
                out[node] = [(a, "example_good") for a in d.get("good_acts", [])] + \
                            [(a, "example_bad") for a in d.get("bad_acts", [])]
    # DEFINITION-ACT LIFTING (definitional lane, prereg panel_run1/convergence/
    # definitional_lane_prereg.md): norm-free definitional modules whose CLAIMS
    # describe/characterize assistant acts (Opus-annotated, parity-passed lane)
    # gain those canonical acts with status "described". Sibling of example-act
    # lifting; walls apply via the definition_* layer merges in relevance().
    dp = os.path.join(HERE, "definition_acts.json")
    if os.path.exists(dp):
        for node, alist in json.load(open(dp))["acts"].items():
            if node in out and not out[node]:
                out[node] = [(a, "described") for a in alist]
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
    """subtype -> ANCESTORS for the act ontology, read from the DECLARED
    hierarchy (behavior_vocab.json _act_hierarchy) with transitive closure.
    (2026-08-18: name-prefix guessing broke silently when the hierarchy
    became three-level — counter_harm -> protective_response -> respond;
    caution lost every protective engagement, 72%->59%. Declared, closed,
    never guessed.) Returns {name: set(of all ancestors)}."""
    p = os.path.join(HERE, "behavior_vocab.json")
    h = json.load(open(p)).get("_act_hierarchy", {}) if os.path.exists(p) else {}
    # legacy default for subtypes not in the declared map
    sp = os.path.join(HERE, "act_subtypes.json")
    if os.path.exists(sp):
        for s2 in set(json.load(open(sp)).values()):
            if s2 not in h and s2 not in ("provide", "respond"):
                h[s2] = "provide" if s2.startswith(("provide", "disclose")) else "respond"
    h.setdefault("protective_response", "respond")
    out = {}
    for k in h:
        anc, cur = set(), k
        while cur in h and h[cur] not in anc:
            anc.add(h[cur]); cur = h[cur]
        out[k] = anc
    return out


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


def act_party():
    """functor -> party its object/beneficiary/victim concerns (the E1
    structural fix, Matt's decision 2, 2026-08-18). unspecified fails open."""
    p = os.path.join(HERE, "act_party.json")
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
# FROZEN CONFIG 2026-08-18: walls DISABLED. Tuning-half evidence: walls in
# their verb-family form cost every behavior (0.75/0.54/0.78 vs
# 0.75/0.57/0.81 without); the H1 fix needs per-behavior argument
# declarations (future work, census-motivated). Machinery + act_arg_sorts
# retained; flip ARG_WALLS_ENABLED to re-enable for experiments.
ARG_WALLS_ENABLED = False
WALLED_VERBS = {"refuse", "comply", "provide", "ask", "act_in_world",
                "provide_information", "provide_content", "provide_resources",
                "disclose_data", "provide_hazardous"} if ARG_WALLS_ENABLED else set()


def relevance(mod, br, corpus):
    acts, canon = behavior_acts(mod)
    pm = parent_map()
    asorts = arg_sorts()
    bargs = behavior_arg_sorts(mod)
    party = act_party()
    # per-behavior party declaration: {"party_concern": ["third_party", ...]} on the module —
    # engagement requires the functor's party be declared-compatible or unspecified (fail open).
    p_decl = set(mod.get("party_concern") or [])
    def hits(c):
        if c is None: return False
        return c in acts or bool(pm.get(c, set()) & acts)
    def verb_hit(c):
        # BOTH hierarchy directions are norm-relevant (restored 2026-08-18
        # after dropping the second silently cost caution 27 engagements):
        # (i) module asserts on a SPECIFIC act, behavior performs an ancestor
        #     — the specific norm is about a kind of act the behavior does;
        # (ii) module asserts on a GENERAL act, behavior performs a
        #     descendant — a norm on the genus governs the species
        #     (a norm about all responses governs a protective response).
        if c in acts: return True
        if pm.get(c, set()) & acts: return True                    # (i)
        return any(c in pm.get(a2, set()) for a2 in acts)          # (ii)

    # per-behavior argument declarations (H1 fix, opt-in): a behavior module
    # may declare {"arg_sorts": {"refuse": ["request","topic"], ...}} — walls
    # then apply ONLY to verbs that behavior explicitly declares, replacing
    # the global verb-family walls (measured to cost every behavior).
    declared = mod.get("arg_sorts") or {}

    def arg_ok(f, c):
        decl = declared.get(c) or next((declared[a] for a in pm.get(c, set()) if a in declared), None)
        if decl:
            fa = asorts.get(f)
            if fa in (None, "none", "other"): return True       # fail open
            return any(fa == w or fa in ARG_COMPAT.get(w, {w}) or w in ARG_COMPAT.get(fa, {fa}) for w in decl)
        if c not in WALLED_VERBS and not (pm.get(c, set()) & WALLED_VERBS): return True
        fa = asorts.get(f)
        if fa in (None, "none", "other"): return True          # fail open
        # behavior arg sorts for the canonical verb (check verb + its parent/children)
        want = set()
        for a2 in acts:
            if a2 == c or pm.get(a2) == c or pm.get(c) == a2: want |= bargs.get(a2, set())
        if not want: return True                                # fail open
        return any(fa == w or fa in ARG_COMPAT.get(w, {w}) or w in ARG_COMPAT.get(fa, {fa}) for w in want)

    def party_ok(f):
        if not p_decl: return True
        pv = party.get(f, "unspecified")
        return pv == "unspecified" or pv in p_decl

    # PER-ASSERT protects wall (the E1 fix, calibrated 2026-08-18): a module
    # engages only if SOME assert protects a declared party, or is
    # unspecified/unannotated (fail open). Declared via module "protects_concern".
    ap_path = os.path.join(HERE, "assert_protects.json")
    ap = json.load(open(ap_path)) if os.path.exists(ap_path) else {}
    _d = os.path.join(HERE, "definition_protects.json")
    if os.path.exists(_d): ap = {**ap, **json.load(open(_d))}  # definitional lane, keys nid|c{i}
    prot_decl = set(mod.get("protects_concern") or [])

    def protects_ok(cid):
        if not prot_decl or not ap: return True
        keys = [k for k in ap if k.startswith(cid + "|")]
        if not keys: return True                       # unannotated: fail open
        vals = {v for k in keys for v in ap[k]}
        return "unspecified" in vals or bool(vals & prot_decl)

    # NORM-SIGNATURE walls (contract §8, layer frontier-labeled 2026-08-19,
    # panel_run1/PROTECTS_LAYER_RECORD.md): (a) a module whose asserts are ALL
    # authority_plumbing is document machinery — excluded from every behavior's
    # relevance (7/58 census FPs); (b) a module engages only if SOME assert
    # governs a quality the behavior declares via "governs_concern" (40/58 +
    # 17/17 fresh-draw census FPs). Both fail OPEN on unannotated asserts.
    sig_path = os.path.join(HERE, "assert_signature.json")
    sig = json.load(open(sig_path)) if os.path.exists(sig_path) else {}
    _d = os.path.join(HERE, "definition_signature.json")
    if os.path.exists(_d): sig = {**sig, **json.load(open(_d))}  # definitional lane, keys nid|c{i}
    # CONTEXT-ATOM LANE (8-A3 consensus credits; 9b integration 2026-08-21):
    # annotated-but-undeclared context atoms merge into signature contexts.
    # Consumption stays declaration-gated (governs_conditional below), so any
    # module not declaring governs_conditional is engagement-invariant.
    _ca = os.path.join(HERE, "panel_run1", "convergence", "context_atoms_consensus.json")
    if os.path.exists(_ca):
        for _nid, _idxs in json.load(open(_ca)).get("credits", {}).items():
            for _i, _atoms in _idxs.items():
                _k = f"{_nid}|{_i}"
                if _k in sig and _atoms:
                    sig[_k] = {**sig[_k], "contexts":
                               sorted(set(sig[_k].get("contexts", [])) | set(_atoms))}
    gov_decl = set(mod.get("governs_concern") or [])

    # governs_conditional (contract 9a purity migration, 2026-08-19): a quality may be
    # declared as bearing on the behavior ONLY in certain contexts, e.g. caution cares
    # about tone_manner only in vulnerable_interaction contexts. {quality: [contexts]}.
    gov_cond = mod.get("governs_conditional") or {}

    def signature_ok(cid):
        if not sig: return True
        keys = [k for k in sig if k.startswith(cid + "|")]
        if not keys: return True                       # unannotated: fail open
        if all(sig[k]["authority_plumbing"] for k in keys): return False
        if not gov_decl and not gov_cond: return True
        for k in keys:
            ctx = set(sig[k].get("contexts", []))
            for g in sig[k]["governs"]:
                if g in gov_decl: return True
                if g in gov_cond and ctx & set(gov_cond[g]): return True
        return False

    # ACTOR slot (contract 8-addendum, spot-check 0.99): a module whose asserts are ALL
    # by a non-assistant actor (organization/developer/document) is excluded from every
    # behavior's relevance. Folds authority_plumbing (actor=document). Fail open.
    pa_path = os.path.join(HERE, "assert_purpose_actor.json")
    pa = json.load(open(pa_path)) if os.path.exists(pa_path) else {}
    _d = os.path.join(HERE, "definition_purpose_actor.json")
    if os.path.exists(_d): pa = {**pa, **json.load(open(_d))}  # definitional lane, keys nid|c{i}
    purp_decl = set(mod.get("purpose_concern") or [])

    def actor_ok(cid):
        keys = [k for k in pa if k.startswith(cid + "|")]
        if not keys: return True
        return any(pa[k]["actor"] == "assistant" for k in keys)

    def purpose_hit(cid):
        # PURPOSE OR-CHANNEL (contract 8-addendum-2, verdict-gate 0.91/0.94/0.86):
        # a module engages if SOME assistant-actor assert serves a declared end —
        # an additional sufficient channel, never a filter (calibration ruling:
        # filters on purpose kill core TPs like l171_426_n005).
        if not purp_decl: return False
        # LANE SCOPE (definitional-lane FP analysis, 2026-08-20): the purpose
        # OR-channel was verdict-gated on the ASSERT lane (0.91/0.94/0.86) and
        # never validated for definitional claims; its one definitional firing
        # was the lane's only FP (harm::l1_170_n031, actor-ambiguous meta claim)
        # while all 10 lane fixes engage by ACT. Definitional keys (nid|c{i})
        # therefore do not feed this channel.
        for k in [k for k in pa if k.startswith(cid + "|") and not k.split("|")[1].startswith("c")]:
            if pa[k]["actor"] == "assistant" and set(pa[k]["purpose"]) & purp_decl:
                return True
        return False

    rel = {}
    for cid, rows in corpus.items():
        if not actor_ok(cid): continue
        act_reasons = []
        if protects_ok(cid) and signature_ok(cid):
            act_reasons = [(f, br.get(f), st) for f, st in rows
                           if br.get(f) is not None and verb_hit(br[f]) and arg_ok(f, br[f]) and party_ok(f)]
        if act_reasons:
            rel[cid] = act_reasons
        elif purpose_hit(cid) and protects_ok(cid):
            # purpose channel is act-independent but the beneficiary wall still
            # applies to every channel (9d: unwalled purpose flooded harm, prec
            # 0.88->0.66; the walled variant is what gets measured/adopted)
            rel[cid] = [("__purpose__", "purpose_channel", "end")]
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
