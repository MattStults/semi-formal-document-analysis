#!/usr/bin/env python3
"""REASON RENDERER for the symbolic relevance instrument — deterministic, LLM-free, $0.

The instrument (relevance_by_act.py) answers a yes/no: does this module engage
this behavior? A user's next question is always "why?". This module answers it
in ONE sentence, from templates, using only artifacts already on disk:

  * relevance_by_act.py            — the engagement decision itself (authoritative)
  * act_bridges.lp / act_actors    — bespoke functor -> canonical act
  * assert_protects.json           — which party each assert protects
  * assert_signature.json          — which quality each assert governs (+ plumbing)
  * assert_purpose_actor.json      — the actor of each assert, and the end it serves
  * ../node_corpus_all.json quotes — the node's ESTABLISHES claim
                                     (prompt_user.txt fallback for drifted ids,
                                     same fallback annotate_signature.py uses)

NO network, NO model call, NO new dependency. The engagement verdict is never
recomputed here by a second rule set: `relevance()` from the instrument decides,
and this module only NAMES the facts that produced its decision. The per-gate
diagnosis for a non-engaged node mirrors the instrument's gate order —
actor -> protects wall -> governs wall -> act match — and reports the FIRST gate
that failed, so the sentence says what would have to change.

Usage:
  .../.venv/bin/python explain_relevance.py modules_contract_v17.json helpfulness
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G2 = os.path.dirname(HERE)
for _p in (HERE, G2, os.path.join(G2, "..", "..")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import link_nodes                    # noqa: E402
import relevance_by_act as RBA       # noqa: E402

DEFAULT_MODULES = "modules_contract_v17.json"
QUOTE_CHARS = 120

_CACHE = {}


# ---------------------------------------------------------------- artifacts

def _json(name, default=None):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return {} if default is None else default
    return json.load(open(p, encoding="utf-8"))


def _load(modules_file=DEFAULT_MODULES):
    """Everything read from disk, once per modules file."""
    key = os.path.abspath(os.path.join(HERE, modules_file))
    if key in _CACHE:
        return _CACHE[key]
    sel = link_nodes.gather()
    st = {
        "modules": json.load(open(key, encoding="utf-8"))["modules"],
        "bridges": RBA.bridges(),
        "corpus": RBA.corpus_acts(),
        "selected": sel,
        "protects": _json("assert_protects.json"),
        "signature": _json("assert_signature.json"),
        "purpose_actor": _json("assert_purpose_actor.json"),
        "parents": RBA.parent_map(),
        "quotes": {c["id"]: c.get("quote") or ""
                   for c in _json2_clauses()},
        "rel": {},
    }
    _CACHE[key] = st
    return st


def _json2_clauses():
    p = os.path.join(G2, "node_corpus_all.json")
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8")).get("clauses", [])


def _relevance(st, slug):
    """Engagement map for one behavior, from the instrument itself (cached)."""
    if slug not in st["rel"]:
        mod = st["modules"][slug]
        acts, rel = RBA.relevance(mod, st["bridges"], st["corpus"])
        st["rel"][slug] = (acts, rel)
    return st["rel"][slug]


# ------------------------------------------------------------ node material

def establishes(st, cid):
    """The node's ESTABLISHES claim, truncated. Falls back to the run's
    prompt_user.txt when the corpus id has drifted (annotate_signature.span_for)."""
    nid = link_nodes.norm_id(cid)
    q = st["quotes"].get(nid) or st["quotes"].get(cid) or ""
    if not q:
        entry = st["selected"].get(nid)
        if entry:
            pu = os.path.join(os.path.dirname(entry[0]), f"{cid}.prompt_user.txt")
            if not os.path.exists(pu):
                pu = os.path.join(os.path.dirname(entry[0]), f"{nid}.prompt_user.txt")
            if os.path.exists(pu):
                q = open(pu, encoding="utf-8").read()
    if not q:
        return "(no source span on disk)"
    if "ESTABLISHES" in q:
        body = q[q.find("ESTABLISHES"):].split("PROVIDES")[0]
        # drop the bracketed header gloss on the ESTABLISHES line itself
        body = re.sub(r"^ESTABLISHES[^\n]*\n", "", body).strip()
    else:
        body = q.strip()
    body = " ".join(body.split())
    if len(body) > QUOTE_CHARS:
        body = body[:QUOTE_CHARS].rstrip() + "…"
    return body


def _keys(table, nid):
    return [k for k in table if k.startswith(nid + "|")]


# ------------------------------------------------------------------- gates
# Mirrors relevance_by_act.relevance's gate order. Each returns (ok, detail).

def _gate_actor(st, mod, nid):
    keys = _keys(st["purpose_actor"], nid)
    if not keys:
        return True, "unannotated (fail open)"
    actors = sorted({st["purpose_actor"][k]["actor"] for k in keys})
    if any(a == "assistant" for a in actors):
        return True, "assistant"
    return False, "/".join(actors) or "unknown"


def _gate_protects(st, mod, nid):
    decl = set(mod.get("protects_concern") or [])
    if not decl or not st["protects"]:
        return True, "no wall declared"
    keys = _keys(st["protects"], nid)
    if not keys:
        return True, "unannotated (fail open)"
    vals = {v for k in keys for v in st["protects"][k]}
    if "unspecified" in vals:
        return True, "unspecified (fail open)"
    hit = vals & decl
    if hit:
        return True, ", ".join(sorted(hit))
    return False, ", ".join(sorted(vals)) or "none"


def _gate_governs(st, mod, nid):
    sig = st["signature"]
    if not sig:
        return True, "no signature layer"
    keys = _keys(sig, nid)
    if not keys:
        return True, "unannotated (fail open)"
    if all(sig[k]["authority_plumbing"] for k in keys):
        return False, "authority_plumbing"
    decl = set(mod.get("governs_concern") or [])
    cond = mod.get("governs_conditional") or {}
    if not decl and not cond:
        return True, "no wall declared"
    hit = set()
    for k in keys:
        ctx = set(sig[k].get("contexts", []))
        for g in sig[k]["governs"]:
            if g in decl:
                hit.add(g)
            elif g in cond and ctx & set(cond[g]):
                hit.add(g)
    if hit:
        return True, ", ".join(sorted(hit))
    seen = sorted({g for k in keys for g in sig[k]["governs"]})
    return False, ", ".join(seen) or "none"


# ------------------------------------------------------------------ render

def explain(slug, node, modules_file=DEFAULT_MODULES):
    """One human-readable sentence saying why `node` does or does not engage `slug`."""
    st = _load(modules_file)
    if slug not in st["modules"]:
        return f"{node}: no behavior module named {slug!r} in {os.path.basename(modules_file)}."
    mod = st["modules"][slug]
    nid = link_nodes.norm_id(node)
    if nid not in st["corpus"]:
        return f"{node}: not in the linked corpus (no translated module on disk)."
    acts, rel = _relevance(st, slug)
    claim = establishes(st, nid)
    reasons = rel.get(nid)

    if reasons:
        ok_a, d_actor = _gate_actor(st, mod, nid)
        ok_p, d_prot = _gate_protects(st, mod, nid)
        ok_g, d_gov = _gate_governs(st, mod, nid)
        if len(reasons) == 1 and reasons[0][0] == "__purpose__":
            ends = sorted({e for k in _keys(st["purpose_actor"], nid)
                           if st["purpose_actor"][k]["actor"] == "assistant"
                           for e in st["purpose_actor"][k]["purpose"]
                           if e in set(mod.get("purpose_concern") or [])})
            lead = ("engages via the PURPOSE channel: an assistant-actor assert "
                    f"serves the declared end {' + '.join(ends) or '(declared end)'}")
        else:
            pairs = sorted({(f, ca, st_) for f, ca, st_ in reasons})
            shown = "; ".join(f"[{s}] {f} → {ca}" for f, ca, s in pairs[:3])
            more = f" (+{len(pairs) - 3} more)" if len(pairs) > 3 else ""
            matched = sorted({ca for _f, ca, _s in pairs})
            lead = (f"engages by ACT: its bespoke assert(s) {shown}{more} bridge to "
                    f"canonical act(s) {', '.join(matched)}, which {slug} performs")
        return (f"{nid} ENGAGES {slug} — {lead}; admitted by actor={d_actor}, "
                f"protects={d_prot}, governs={d_gov}. ESTABLISHES: “{claim}”")

    # not engaged: name the FIRST gate that failed, in the instrument's order
    ok, detail = _gate_actor(st, mod, nid)
    if not ok:
        why = (f"first gate failed = ACTOR: every assert is by a non-assistant "
               f"actor ({detail}), so no assistant act is governed")
        return f"{nid} does NOT engage {slug} — {why}. ESTABLISHES: “{claim}”"

    ok, detail = _gate_protects(st, mod, nid)
    if not ok:
        why = (f"first gate failed = PROTECTS wall: its asserts protect {detail}, "
               f"none of the roles {slug} declares "
               f"({', '.join(sorted(mod.get('protects_concern') or [])) or 'none'})")
        return f"{nid} does NOT engage {slug} — {why}. ESTABLISHES: “{claim}”"

    ok, detail = _gate_governs(st, mod, nid)
    if not ok:
        if detail == "authority_plumbing":
            why = ("first gate failed = GOVERNS wall: every assert is "
                   "authority_plumbing (document machinery, not an operative response norm)")
        else:
            why = (f"first gate failed = GOVERNS wall: its asserts govern {detail}, "
                   f"none of the qualities {slug} declares "
                   f"({', '.join(sorted(mod.get('governs_concern') or [])) or 'none'})")
        return f"{nid} does NOT engage {slug} — {why}. ESTABLISHES: “{claim}”"

    # walls all passed -> the act match (or the purpose channel) is what failed
    br = st["bridges"]
    canon = sorted({br[f] for f, _s in st["corpus"][nid] if br.get(f)})
    raw = sorted({f for f, _s in st["corpus"][nid]})
    if canon:
        seen = f"asserts on canonical act(s) {', '.join(canon)}"
    elif raw:
        seen = f"asserts on {', '.join(raw[:4])}, which bridge to no canonical act"
    else:
        seen = "asserts on no act at all"
    why = (f"first gate failed = NO ACT MATCH: it {seen}, while {slug} performs "
           f"{'/'.join(sorted(acts)) or '(no acts)'}"
           + ("" if not (mod.get("purpose_concern")) else
              "; no assistant-actor assert serves a declared end either"))
    return f"{nid} does NOT engage {slug} — {why}. ESTABLISHES: “{claim}”"




# ---------------------------------------------------------------- plain mode

_FRIENDLY_ACT = {
    "provide": "providing something to the user", "provide_information": "providing information",
    "provide_content": "producing content", "provide_resources": "pointing to resources",
    "disclose_data": "disclosing data", "provide_hazardous": "providing hazardous information",
    "respond": "responding", "answer_directly": "answering the question directly",
    "respond_in_manner": "the manner or style of a response", "acknowledge": "acknowledging something",
    "express_stance": "expressing a stance", "express_uncertainty": "expressing uncertainty",
    "express_calibrated_position": "taking a calibrated position", "uncertainty_phrasing": "how uncertainty is phrased",
    "protective_response": "responding protectively", "counter_harm": "countering a harm",
    "safe_manner": "handling something in a safe manner", "refuse": "refusing",
    "comply": "complying with a request", "ask": "asking a question",
    "act_in_world": "taking a real-world action", "deliberate": "deliberating",
    "monitor": "monitoring", "escalate": "escalating", "terminate": "ending the interaction",
}
_FRIENDLY_QUAL = {
    "substance_usefulness": "what is substantively provided or refused",
    "accuracy_calibration": "truthfulness and how uncertainty is expressed",
    "tone_manner": "tone and interpersonal manner",
    "formatting_style": "formatting and structure",
    "identity_meta": "what the assistant says about itself",
    "objectivity_neutrality": "balance and viewpoint fairness",
}
_FRIENDLY_ROLE = {
    "user": "the user in the conversation", "third_party": "people outside the conversation",
    "society": "the public at large", "developer": "the developer/operator",
    "minor": "minors", "unspecified": "no one in particular (fails open)",
}
_FRIENDLY_STATUS = {"forbid": "a prohibition on", "oblige": "a requirement to",
                    "permit": "a permission to", "prefer": "a preference for",
                    "example_good": "an endorsed example of", "example_bad": "a disfavored example of"}
_NL = "\n  "


def _words(name):
    return str(name).replace("_", " ")


def _f_act(a):
    return _FRIENDLY_ACT.get(a, _words(a))


def _f_list(vals, table):
    vals = [v for v in vals if v]
    return ", ".join(table.get(v, _words(v)) for v in vals) if vals else "(none)"


def explain_plain(slug, node, modules_file=DEFAULT_MODULES):
    """Multi-line, jargon-free account of the decision for `node` vs `slug`."""
    st = _load(modules_file)
    if slug not in st["modules"]:
        return f"{node}: no behavior module named {slug!r}."
    mod = st["modules"][slug]
    nid = link_nodes.norm_id(node)
    if nid not in st["corpus"]:
        return f"{node}: not in the linked corpus."
    acts, rel = _relevance(st, slug)
    claim = establishes(st, nid)
    reasons = rel.get(nid)
    b = _words(slug)
    L = [f'The clause says: "{claim}"']
    if reasons:
        L.insert(0, f"FLAGGED as bearing on {b}.")
        if len(reasons) == 1 and reasons[0][0] == "__purpose__":
            ends = sorted({e for k in _keys(st["purpose_actor"], nid)
                           if st["purpose_actor"][k]["actor"] == "assistant"
                           for e in st["purpose_actor"][k]["purpose"]
                           if e in set(mod.get("purpose_concern") or [])})
            L.append(f'Why: the clause exists to serve "{_f_list(ends, {})}" — one of the document goals this behavior tracks —')
            L.append("     so it was flagged even though its act wording does not match directly.")
        else:
            pairs = sorted({(f, ca, s) for f, ca, s in reasons})
            for f, ca, s in pairs[:3]:
                lead = _FRIENDLY_STATUS.get(str(s), f"a rule ({s}) about")
                if f == ca:
                    L.append(f"Why: it contains {lead} {_f_act(ca)} — something this behavior involves.")
                else:
                    L.append(f'Why: it contains {lead} "{_words(f)}", which the act ontology classifies as {_f_act(ca)} — something this behavior involves.')
            gv = sorted({g for k in _keys(st["signature"], nid) for g in st["signature"][k]["governs"]})
            pr = sorted({p for k in _keys(st["protects"], nid) for p in st["protects"][k]})
            checks = ["it is a rule about the assistant's own conduct"]
            if mod.get("protects_concern"):
                checks.append(f"it protects {_f_list(pr, _FRIENDLY_ROLE)} (this behavior tracks rules protecting {_f_list(sorted(mod['protects_concern']), _FRIENDLY_ROLE)})")
            if mod.get("governs_concern"):
                checks.append(f"it governs {_f_list(gv, _FRIENDLY_QUAL)} (this behavior tracks rules about {_f_list(sorted(mod['governs_concern']), _FRIENDLY_QUAL)})")
            L.append("Checks passed: " + "; ".join(checks) + ".")
        return _NL.join(L)
    L.insert(0, f"NOT FLAGGED for {b}.")
    ok, detail = _gate_actor(st, mod, nid)
    if not ok:
        who = {"organization": "the company (OpenAI) itself", "developer": "developers who build on the model",
               "document": "the document's own bookkeeping (what counts as an instruction, what overrides what)"}
        d = ", ".join(who.get(x.strip(), x.strip()) for x in str(detail).split(","))
        L.append(f"Why not: this clause is about {d} — not about how the assistant itself should respond,")
        L.append("     and behaviors only track rules for the assistant's own conduct.")
        return _NL.join(L)
    ok, detail = _gate_protects(st, mod, nid)
    if not ok:
        L.append(f"Why not: the tool's records say this rule exists to protect {_f_list(sorted(str(detail).split(', ')), _FRIENDLY_ROLE)},")
        L.append(f"     and this behavior only tracks rules protecting {_f_list(sorted(mod.get('protects_concern') or []), _FRIENDLY_ROLE)} —")
        L.append('     so it was filtered out at the "who does this rule protect?" check.')
        return _NL.join(L)
    ok, detail = _gate_governs(st, mod, nid)
    if not ok:
        if detail == "authority_plumbing":
            L.append("Why not: every rule here is the document's own machinery (which instructions count, what overrides what),")
            L.append("     not a rule about how the assistant should respond.")
        else:
            L.append(f"Why not: this rule is about {_f_list(sorted(str(detail).split(', ')), _FRIENDLY_QUAL)},")
            L.append(f"     and this behavior only tracks rules about {_f_list(sorted(mod.get('governs_concern') or []), _FRIENDLY_QUAL)} —")
            L.append('     so it was filtered out at the "which quality of responding does this rule govern?" check.')
        return _NL.join(L)
    br = st["bridges"]
    canon = sorted({br[f] for f, _s in st["corpus"][nid] if br.get(f)})
    raw = sorted({f for f, _s in st["corpus"][nid]})
    if canon:
        L.append(f"Why not: its rules are about {_f_list(canon, _FRIENDLY_ACT)},")
    elif raw:
        L.append(f'Why not: its rules are about "{", ".join(_words(r) for r in raw[:4])}", which the act ontology maps to no known act,')
    else:
        L.append("Why not: this clause states no rule about any act at all (it is definitional or commentary),")
    L.append(f"     while this behavior involves {_f_list(sorted(acts), _FRIENDLY_ACT)} —")
    L.append("     no overlap, so it never reached the later checks.")
    return _NL.join(L)


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip().splitlines()[-1])
        raise SystemExit(2)
    modules_file, slug = sys.argv[1], sys.argv[2]
    st = _load(modules_file)
    if slug not in st["modules"]:
        raise SystemExit(f"no such behavior: {slug}")
    acts, rel = _relevance(st, slug)
    print(f"# {slug} performs {sorted(acts)}; engaged modules {len(rel)} "
          f"of {len(st['corpus'])} (from {os.path.basename(modules_file)})")
    plain = "--plain" in sys.argv
    for cid in sorted(rel):
        print(explain_plain(slug, cid, modules_file) if plain else explain(slug, cid, modules_file))
    if "--with-declines" in sys.argv:
        for cid in sorted(c for c in st["corpus"] if c not in rel):
            print(explain(slug, cid, modules_file))


if __name__ == "__main__":
    main()
