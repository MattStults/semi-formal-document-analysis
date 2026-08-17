#!/usr/bin/env python3
"""Mechanical class checks — the cheap-Python instruments the slice-3 sweep runs
across ALL five modules, so a class found on clause 5 reaches clause 1.

Each check is a QUESTION a later reader can apply without judgment.
Run:  ../../../../../../semi-formal-experiment/.venv/bin/python mech.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IDS = ["l1001_1107_n003", "l1001_1107_n009", "l1108_1367_n001",
       "l1108_1367_n006", "l1108_1367_n011"]

_NAME = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")


def names_in(s):
    return set(_NAME.findall(s or ""))


def load(cid):
    p = os.path.join(OUT, f"{cid}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def entries(o, k):
    v = o.get(k)
    return v if isinstance(v, list) else []


def txt(e, *keys):
    if isinstance(e, str):
        return e
    return " ".join(str(e.get(k, "")) for k in keys)


def bodies(o):
    """Every body string in the module."""
    out = []
    for k in ("asserts", "ontology", "beats", "defines"):
        for e in entries(o, k):
            if isinstance(e, dict) and e.get("body"):
                out.append(e["body"])
    return out


def heads(o):
    out = []
    for e in entries(o, "asserts"):
        if isinstance(e, dict):
            out.append(str(e.get("act") or e.get("head") or ""))
    return out


def declared_names(o, key):
    s = set()
    for e in entries(o, key):
        if isinstance(e, str):
            s |= names_in(e) or {e.split("/")[0]}
        else:
            n = e.get("name") or e.get("predicate") or e.get("atom") or ""
            s |= (names_in(n) or {str(n).split("/")[0]})
    return {x for x in s if x}


# ---------------------------------------------------------------- checks
def c_needs_in_requires(cid, o, span):
    """M1. Is every NEEDS name from the span present in `requires`, spelled exactly?"""
    needs = re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", span, re.M)
    blk = span.split("NEEDS")[1].split("CITATION")[0] if "NEEDS" in span else ""
    needs = re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M)
    req = declared_names(o, "requires")
    return [f"NEEDS name absent from requires: {n}" for n in needs if n not in req]


def c_provides_defined(cid, o, span):
    """M2. Is every PROVIDES name actually defined here (ontology atom or concepts)?"""
    blk = span.split("PROVIDES")[1].split("NEEDS")[0] if "PROVIDES" in span else ""
    prov = re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M)
    onto = declared_names(o, "ontology")
    con = declared_names(o, "concepts")
    bad = []
    for n in prov:
        if n not in onto:
            bad.append(f"PROVIDES name not in ontology: {n}"
                       + ("" if n in con else "  (and not in concepts either)"))
    return bad


def c_requires_has_concept(cid, o, span):
    """M3. Does every `requires` entry have a `concepts` gloss? (10_output_format)"""
    req = declared_names(o, "requires")
    con = declared_names(o, "concepts")
    return [f"requires without a concepts gloss: {n}" for n in sorted(req - con)]


def c_undeclared_body_names(cid, o, span):
    """M4. Is every name used in a body declared in ontology/requires/inputs?"""
    dec = (declared_names(o, "ontology") | declared_names(o, "requires")
           | declared_names(o, "inputs") | declared_names(o, "concepts"))
    bad = []
    for b in bodies(o):
        for n in names_in(b) - dec:
            bad.append(f"body name never declared: {n}   in `{b}`")
    return sorted(set(bad))


def c_coined_unused(cid, o, span):
    """M5 (P9, narrowed). Does every name YOU COINED get used somewhere?
    NEEDS names in `requires` are contract-required and exempt."""
    blk = span.split("NEEDS")[1].split("CITATION")[0] if "NEEDS" in span else ""
    needs = set(re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M))
    coined = (declared_names(o, "ontology") | declared_names(o, "inputs")
              | (declared_names(o, "requires") - needs))
    used = set()
    for b in bodies(o):
        used |= names_in(b)
    for h in heads(o):
        used |= names_in(h)
    for e in entries(o, "ontology"):
        if isinstance(e, dict):
            used |= names_in(str(e.get("atom", "")))
    return [f"coined name declared and never used: {n}" for n in sorted(coined - used)]


def c_naf(cid, o, span):
    """M6 (N5). Does any body rely on ABSENCE of a fact (negation as failure)?"""
    bad = []
    for b in bodies(o):
        if re.search(r"(^|,|\s)not\s+[a-z_]", b):
            bad.append(f"negation-as-failure in body: `{b}`")
    return bad


def c_shared_body_obliges(cid, o, span):
    """M7 (P4). Do several obliges share ONE identical body? (disjunction as conjunction)"""
    seen = {}
    for e in entries(o, "asserts"):
        if isinstance(e, dict) and e.get("status") == "oblige":
            seen.setdefault(e.get("body") or "", []).append(e.get("act"))
    return [f"{len(v)} obliges share one body `{k}`: {v}"
            for k, v in seen.items() if len(v) > 1]


def c_tautology(cid, o, span):
    """M8 (P8). Does a rule's head functor appear in its own body?
    NOTE the anti-rule: `forbid X(R) :- X(R)` over a VARIABLE act is schema-forced."""
    bad = []
    for e in entries(o, "asserts"):
        if not isinstance(e, dict):
            continue
        act, body = str(e.get("act") or ""), str(e.get("body") or "")
        f = (_NAME.findall(act) or [None])[0]
        if f and f in names_in(body):
            flag = "SCHEMA-FORCED binder (act is a bare variable)" \
                if re.fullmatch(r"[A-Z][A-Za-z0-9_]*", act.strip()) else "REVIEW"
            bad.append(f"head functor `{f}` recurs in its own body [{flag}]: {act} :- {body}")
    return bad


def c_slots(cid, o, span):
    """M9. Do `read_back` %-count and `read_back_slots` length agree, everywhere?"""
    bad = []
    for k in ("asserts", "ontology", "concepts", "beats", "defines", "closure"):
        for e in entries(o, k):
            if not isinstance(e, dict) or "read_back" not in e:
                continue
            n = str(e["read_back"]).count("%")
            s = e.get("read_back_slots")
            s = len(s) if isinstance(s, list) else 0
            if n != s:
                bad.append(f"{k}: {n} '%' vs {s} slot(s): {e['read_back']!r}")
    return bad


def c_closure_coverage(cid, o, span):
    """M10. Does every distinct act functor in `asserts` have a `closure` entry?"""
    acts = set()
    for h in heads(o):
        acts |= (names_in(h) or set())
    cl = set()
    for e in entries(o, "closure"):
        n = e if isinstance(e, str) else (e.get("act") or e.get("name") or e.get("act_class") or "")
        cl |= (names_in(str(n)) or {str(n).split("/")[0]})
    return [f"act class governed with no closure declaration: {a}" for a in sorted(acts - cl) if a]


def c_citation(cid, o, span):
    """M11. Does every citation cite exactly this node id?"""
    bad = []
    blob = json.dumps(o)
    for m in set(re.findall(r"l\d+_\d+_n\d+", blob)):
        if m != cid:
            bad.append(f"citation to a foreign id: {m}")
    for m in set(re.findall(r"\bL\d+(?:-L?\d+)?\b", blob)):
        bad.append(f"line-number citation (never citable): {m}")
    return bad


def c_polarity(cid, o, span):
    """M12 (P1). Does any `prefer` name an act the span wants LESS of?
    Heuristic: act functor begins with avoid_/refrain/decline/not_ under `prefer`,
    or the read_back contains a negation while status is prefer."""
    bad = []
    for e in entries(o, "asserts"):
        if not isinstance(e, dict) or e.get("status") != "prefer":
            continue
        rb = str(e.get("read_back") or "").lower()
        if re.search(r"\b(not|never|avoid|should not|must not|refrain|without)\b", rb):
            bad.append(f"prefer whose read_back negates: {e.get('act')} — {e.get('read_back')!r}")
    return bad


def c_good_bad_poles(cid, o, span):
    """M13 (P10). If the span is a GOOD/BAD pair, do the two arms differ?"""
    if "GOOD" not in span or "BAD" not in span:
        return []
    rows = [(e.get("status"), e.get("act"), e.get("body"))
            for e in entries(o, "asserts") if isinstance(e, dict)]
    g = [r for r in rows if "good" in str(r[2]).lower()]
    b = [r for r in rows if "bad" in str(r[2]).lower()]
    out = []
    for x in g:
        for y in b:
            if x[0] == y[0] and x[1] == y[1]:
                out.append(f"GOOD and BAD arms carry the same status+act: {x[0]} {x[1]}")
    return out


def c_gloss_restates(cid, o, span):
    """M14. Does a `concepts` gloss just restate the predicate name?"""
    bad = []
    for e in entries(o, "concepts"):
        if not isinstance(e, dict):
            continue
        n = str(e.get("name") or "").split("/")[0]
        g = str(e.get("gloss") or "")
        words = [w for w in re.split(r"[^a-z]+", g.lower()) if w]
        nw = [w for w in n.split("_") if w]
        if nw and len(words) <= len(nw) + 2 and all(w in words for w in nw):
            bad.append(f"gloss may restate the name: {n} — {g!r}")
    return bad


def c_unanchored_constants(cid, o, span):
    """M15 (N10). Does every coined lowercase CONSTANT trace to a substring of
    the narrowed span (or of ESTABLISHES)? Reports candidates for human read."""
    m = re.search(r"\[node narrows this span to: \"(.*?)\"\]", span, re.S)
    hay = (m.group(1) if m else span).lower()
    est = span.split("ESTABLISHES")[1].split("PROVIDES")[0].lower() if "ESTABLISHES" in span else ""
    hay = hay + " " + est + " " + span.split("SOURCE TEXT")[-1].lower()
    consts = set()
    for e in entries(o, "ontology") + entries(o, "asserts"):
        if not isinstance(e, dict):
            continue
        for s in (str(e.get("atom", "")), str(e.get("act", "")), str(e.get("body", ""))):
            for arg in re.findall(r"\(([^()]*)\)", s):
                for a in arg.split(","):
                    a = a.strip()
                    if re.fullmatch(r"[a-z][a-z0-9_]*", a):
                        consts.add(a)
    bad = []
    for c in sorted(consts):
        toks = [t for t in c.split("_") if len(t) > 3]
        miss = [t for t in toks if t[:5] not in hay]
        if miss:
            bad.append(f"constant with token(s) absent from the span: {c} "
                       f"(missing {', '.join(miss)})")
    return bad



def c_naf_polarity(cid, o, span):
    """M16 (refines N5). WHICH DIRECTION does a negation-as-failure body run in?
    `not X` under a forbid/oblige head is CONSERVATIVE — silence makes the duty
    fire. `not X` under a permit/prefer head is the DANGEROUS one — silence
    LICENSES the act, which is what N5 was written about. N5 as written does not
    distinguish them, so it fires on the safe case and reads as a defect."""
    out = []
    for e in entries(o, "asserts"):
        if not isinstance(e, dict):
            continue
        b = str(e.get("body") or "")
        if not re.search(r"(^|,|\s)not\s+[a-z_]", b):
            continue
        st = e.get("status")
        if st in ("permit", "prefer"):
            out.append(f"DANGEROUS: `not` under `{st}` — silence licenses "
                       f"{e.get('act')}: {b}")
        else:
            out.append(f"conservative: `not` under `{st}` — silence makes the "
                       f"duty fire on {e.get('act')}: {b}  [REVIEW, not a defect]")
    return out


def c_inert_ontology(cid, o, span):
    """M17. Is any `ontology` predicate DEONTICALLY INERT — unreachable from any
    `asserts` body, even transitively? Content parked in `ontology` where no
    deontic rule ever fires on it is present to a reader and invisible to the
    solver. This is content deletion that the read-back cannot see."""
    # forward edges: ontology head functor -> functors its body needs
    heads_of = {}
    for e in entries(o, "ontology"):
        if not isinstance(e, dict):
            continue
        h = (_NAME.findall(str(e.get("atom", ""))) or [None])[0]
        if not h:
            continue
        heads_of.setdefault(h, set()).update(names_in(str(e.get("body") or "")))
    # seed: everything any assert body or act mentions
    reach = set()
    for e in entries(o, "asserts"):
        if isinstance(e, dict):
            reach |= names_in(str(e.get("body") or ""))
            reach |= names_in(str(e.get("act") or ""))
    for k in ("beats", "defines"):
        for e in entries(o, k):
            if isinstance(e, dict):
                reach |= names_in(str(e.get("body") or ""))
    changed = True
    while changed:
        changed = False
        for h, needs in heads_of.items():
            if h in reach and not needs <= reach:
                reach |= needs
                changed = True
    return [f"ontology head never reachable from any assert: {h}"
            for h in sorted(heads_of) if h not in reach]


def c_head_and_input(cid, o, span):
    """M18. Is a predicate BOTH derived here (an `ontology` head) and declared a
    situation `input`? Then a case can satisfy it without the ontology rule ever
    running, and the two legs can disagree. Sometimes deliberate — say so."""
    heads = set()
    for e in entries(o, "ontology"):
        if isinstance(e, dict):
            heads |= (_NAME.findall(str(e.get("atom", ""))) or set()) and \
                set(_NAME.findall(str(e.get("atom", ""))))
    inp = declared_names(o, "inputs")
    return [f"predicate is both an ontology head and a situation input: {n}"
            for n in sorted(heads & inp)]


def c_claims_uncovered(cid, o, span):
    """M19 (P3, made mechanical). Does every `claims` entry share a content word
    with SOME encoded rule? A claim whose vocabulary appears nowhere in any act,
    body, atom or read_back is the fingerprint of a dropped obligation.
    Crude on purpose — it directs attention, it does not adjudicate."""
    blob = " ".join(
        [str(e.get(k, "")) for k in ("act", "body", "read_back", "atom", "gloss")
         for grp in ("asserts", "ontology", "concepts")
         for e in entries(o, grp) if isinstance(e, dict)]).lower()
    stop = set("""the a an and or of to in is are be that this it its for with as
        not no any all every their they them there where when which who whom what
        from by on at into than then so such does do done has have had was were
        will would should must may can shall clause span module document assistant
        openai model rule rules content thing things one two three""".split())
    out = []
    for c in entries(o, "claims"):
        toks = [t for t in re.split(r"[^a-z]+", str(c).lower())
                if len(t) > 3 and t not in stop]
        miss = [t for t in toks if t[:5] not in blob]
        if toks and len(miss) == len(toks):
            out.append(f"claim shares no vocabulary with any encoded rule: {c}")
        elif toks and len(miss) > len(toks) * 0.7:
            out.append(f"claim mostly unencoded ({len(miss)}/{len(toks)} words "
                       f"absent): {c}   missing: {', '.join(miss[:6])}")
    return out


def c_requires_shadowed(cid, o, span):
    """M20. Does the module COIN a predicate that shadows a name it is required
    to BORROW? Borrowing `sensitive_content` and then coining
    `sensitive_content_appropriate_in` as an input is a duplication the link
    step cannot see, because the two names differ."""
    blk = span.split("NEEDS")[1].split("CITATION")[0] if "NEEDS" in span else ""
    needs = re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M)
    coined = declared_names(o, "ontology") | declared_names(o, "inputs")
    out = []
    for n in needs:
        for c in sorted(coined):
            if c != n and (c.startswith(n + "_") or n.startswith(c + "_")
                           or n in c):
                out.append(f"coined `{c}` shadows the NEEDS name `{n}`")
    return out



# ---- classes contributed by the CRITICS, swept back across all five clauses ----

def c_gloss_duplicated(cid, o, span):
    """M21 (critic n009, GLOSS-1). Is an `ontology` entry's gloss identical to the
    `concepts` gloss of the same predicate? An ontology gloss must describe the
    BODIED CASE ("X is hateful because it is a slur"), not re-state what the
    predicate means — otherwise the bodied rule's own content is unrecorded."""
    cg = {}
    for e in entries(o, "concepts"):
        if isinstance(e, dict):
            cg[str(e.get("name", "")).split("/")[0]] = " ".join(
                str(e.get("gloss", "")).lower().split())
    out = []
    for e in entries(o, "ontology"):
        if not isinstance(e, dict):
            continue
        h = (_NAME.findall(str(e.get("atom", ""))) or [None])[0]
        g = " ".join(str(e.get("gloss", "")).lower().split())
        if h and h in cg and g and g == cg[h]:
            out.append(f"ontology gloss is byte-identical to the concepts gloss "
                       f"for `{h}` — the bodied case is undescribed")
    return out


def c_argorder_unpinned(cid, o, span):
    """M22 (critic n009, ORDER-1 — WIDENS N8 from borrowed to ALL arity>=2 names).
    For every concept of arity >= 2, does the gloss distinguish the argument
    positions — by naming the variables, or by an ordinal phrase? A silent
    inversion of a 2-place relation passes every other check there is."""
    out = []
    for e in entries(o, "concepts"):
        if not isinstance(e, dict):
            continue
        try:
            ar = int(e.get("arity") or 0)
        except (TypeError, ValueError):
            ar = 0
        if ar < 2:
            continue
        g = str(e.get("gloss") or "")
        gl = g.lower()
        ordinal = any(k in gl for k in
                      ("first argument", "second argument", "third argument",
                       "the first", "the second", "former", "latter"))
        # variables named in the gloss, e.g. "N is a phone number reaching P"
        varsy = re.findall(r"\b([A-Z][A-Za-z0-9_]{0,2})\b", g)
        varsy = [v for v in varsy if v not in ("A", "I", "R", "X") or True]
        if not ordinal and len(set(varsy)) < ar:
            out.append(f"arity-{ar} concept `{e.get('name')}` does not pin "
                       f"argument order in its gloss")
    return out


def c_open_list_closed(cid, o, span):
    """M23 (critic n006, C2). If the NARROWED span ends an enumeration with
    "etc." / "e.g." / "such as" / "or other", is there a route into that class
    besides the named ground constants? Closing an open list is a scope
    narrowing in the DANGEROUS direction and nothing else catches it."""
    m = re.search(r"\[node narrows this span to: \"(.*?)\"\]", span, re.S)
    hay = (m.group(1) if m else "").lower()
    if not hay:
        hay = span.split("SOURCE TEXT")[-1].lower()
    markers = [k for k in ("etc.", "e.g.", "such as", "or other", "and other",
                           "including", "among other") if k in hay]
    if not markers:
        return []
    # a route in = an ontology head with a BODY, or a bare input predicate
    open_routes = [e for e in entries(o, "ontology")
                   if isinstance(e, dict) and e.get("body")]
    inp = declared_names(o, "inputs")
    if open_routes or inp:
        return [f"span leaves a list OPEN ({', '.join(markers)}) — routes into "
                f"the class exist ({len(open_routes)} bodied ontology rule(s), "
                f"{len(inp)} input(s)) [REVIEW: is the RIGHT class left open?]"]
    return [f"span leaves a list OPEN ({', '.join(markers)}) but the module has "
            f"no bodied rule and no input — the class is CLOSED to the named "
            f"constants only. Scope narrowing, dangerous direction."]


def c_needs_gloss_licence(cid, o, span):
    """M24 (critic n009, PF-1). Is a NEEDS name's `concepts` gloss stamped
    `licence: textual` citing THIS clause — when the meaning came from the
    node's NEEDS header and another node owns it? The worked example does
    exactly this, so it is a PROMPT finding, not a module defect. Counted, not
    condemned."""
    blk = span.split("NEEDS")[1].split("CITATION")[0] if "NEEDS" in span else ""
    needs = set(re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M))
    out = []
    for e in entries(o, "concepts"):
        if not isinstance(e, dict):
            continue
        n = str(e.get("name", "")).split("/")[0]
        if n in needs and e.get("licence") == "textual" and e.get("cites") == cid:
            out.append(f"borrowed NEEDS name `{n}` glossed `textual` citing this "
                       f"clause [PROMPT FINDING PF-1, not a module defect]")
    return out


def c_abstention_answered(cid, o, span):
    """M25 (critic n006, C7). Does the clause's written record answer the
    abstention question in words? Greps the notes and critic files for the
    trigger vocabulary. A SILENT answer counts as unasked — this is the
    instrument measured gap #1 was missing.
    ⚠️ Counting the WORD 'abstain' alone is a null-result detector: a
    translator told by `node_worked_example.md` that the trigger does not fire
    has nothing to write. So this checks the FOUR TRIGGERS by name."""
    blob = ""
    import glob as _g
    for p in ([os.path.join(OUT, cid + ".notes.md")]
              + sorted(_g.glob(os.path.join(OUT, cid + ".critic_t*.md")))):
        if os.path.exists(p):
            blob += open(p, encoding="utf-8").read().lower()
    if not blob:
        return ["no written record exists for this clause"]
    want = {"abstain": "abstain/abstention",
            "heading": "trigger: section heading",
            "goal": "trigger: goal rather than condition",
            "example": "trigger: it is an example",
            "expressible": "trigger: not expressible as rules"}
    return [f"abstention record never mentions {v}"
            for k, v in want.items() if k not in blob]


CHECKS = [v for k, v in sorted(globals().items()) if k.startswith("c_")]
ORDER = ["c_needs_in_requires", "c_provides_defined", "c_requires_has_concept",
         "c_undeclared_body_names", "c_coined_unused", "c_naf",
         "c_shared_body_obliges", "c_tautology", "c_slots",
         "c_closure_coverage", "c_citation", "c_polarity",
         "c_good_bad_poles", "c_gloss_restates", "c_unanchored_constants",
         "c_naf_polarity", "c_inert_ontology", "c_head_and_input",
         "c_claims_uncovered", "c_requires_shadowed",
         "c_gloss_duplicated", "c_argorder_unpinned", "c_open_list_closed",
         "c_needs_gloss_licence", "c_abstention_answered"]


def main():
    g = globals()
    total = 0
    for cid in IDS:
        o = load(cid)
        print("=" * 72)
        print(cid)
        if o is None:
            print("  (no module)"); continue
        if o.get("outcome") == "abstained":
            print(f"  ABSTAINED — {o.get('abstain_reason','')[:200]}")
        span = open(os.path.join(HERE, "spans", f"{cid}.prompt_user.txt")).read()
        for name in ORDER:
            fn = g[name]
            try:
                hits = fn(cid, o, span)
            except Exception as ex:                       # a check must never mask a module
                hits = [f"CHECK ERROR {ex!r}"]
            tag = f"  {name[2:]:24s}"
            if hits:
                total += len(hits)
                print(tag, f"{len(hits)} HIT")
                for h in hits:
                    print("      *", h)
            else:
                print(tag, "clean")
    print("=" * 72)
    print("total hits:", total)


if __name__ == "__main__":
    main()
