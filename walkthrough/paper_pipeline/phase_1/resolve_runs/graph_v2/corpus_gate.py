#!/usr/bin/env python3
"""CORPUS GATE — the single operational definition of "defect" for translated
node modules, promoted from `_debug_gen11/opus_pairs/slice3/{mech,cross}.py`
(the end-of-run sweep that SERIES_HANDOFF §7 records as the strongest result of
the critic-loop series). This file is the ONE code path every arm and every
salvage decision scores through; the per-arm predicates it replaces are the
"overlapping predicates" problem SERIES_HANDOFF §8 names.

Every check is a QUESTION a later reader can apply without judgment. Checks are
tiered by what a hit MEANS, and the tier is data, not prose:

  hard    — the module is mechanically defective on its own terms (a name that
            cannot link, a citation that lies, a licence that misstates its
            source under DECISION_licence_textual.md). Salvage requires an edit.
  review  — the pattern has produced defects before and directs attention;
            a hit is not itself a defect (labels direct ATTENTION, never TRUTH).
  info    — on the record so the number is never rediscovered as a surprise
            (orphan borrows in a partial corpus, schema-forced binders).

Scope: the NEWEST translated artifact per node across translation_sample/runs/*
— the same "newest wins" rule as link_nodes.gather(). Abstained modules are
counted and exempt (an abstention has no content to check).

Run:   ../../../../../semi-formal-experiment/.venv/bin/python corpus_gate.py
       [--json corpus_gate_report.json] [--ids id1 id2 ...]

Provenance: per-module checks M1–M24 are slice-3 `mech.py` verbatim except
where noted; cross-module checks X1–X5 are slice-3 `cross.py`. M25
(abstention_answered) is NOT promoted — it reads slice-local notes/critic files
that production runs do not produce; its production replacement is the
establishes-test now stated in 00_task.md itself. M6 (bare naf) is subsumed by
M16 (naf_polarity), which distinguishes the dangerous direction from the
conservative one — running both would double-count every hit.
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "translation_sample", "runs")

_NAME = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")

# ---------------------------------------------------------------- gather

def gather():
    """cid -> (module dict, span text, run dir name). Newest run wins."""
    out = {}
    for run in sorted(os.listdir(RUNS)):
        rd = os.path.join(RUNS, run)
        if not os.path.isdir(rd):
            continue
        for jp in glob.glob(os.path.join(rd, "l*_n*.json")):
            base = os.path.basename(jp)
            if base.endswith((".transcript.json", ".version.json", ".raw.json")):
                continue
            cid = base[:-5]
            sp = os.path.join(rd, cid + ".prompt_user.txt")
            span = open(sp, encoding="utf-8").read() if os.path.exists(sp) else ""
            try:
                out[cid] = (json.load(open(jp)), span, run)
            except (json.JSONDecodeError, UnicodeDecodeError) as ex:
                out[cid] = ({"_unreadable": repr(ex)}, span, run)
    return out


def region_of(cid):
    m = re.match(r"(l\d+_\d+)_", cid)
    return m.group(1) if m else cid

# ---------------------------------------------------------------- helpers
# (slice-3 mech.py verbatim)

def names_in(s):
    return set(_NAME.findall(s or ""))


def entries(o, k):
    v = o.get(k)
    return v if isinstance(v, list) else []


def bodies(o):
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


def needs_names(span):
    blk = span.split("NEEDS")[1].split("CITATION")[0] if "NEEDS" in span else ""
    return re.findall(r"^  - ([a-z_][A-Za-z0-9_]*):", blk, re.M)

# ---------------------------------------------------------------- per-module
# signature: fn(cid, o, span) -> [hit, ...]

def c_needs_in_requires(cid, o, span):
    """M1 hard. Every NEEDS name present in `requires`, spelled exactly."""
    req = declared_names(o, "requires")
    return [f"NEEDS name absent from requires: {n}"
            for n in needs_names(span) if n not in req]


def c_provides_defined(cid, o, span):
    """M2 hard. Every PROVIDES name actually defined here."""
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
    """M3 hard. Every `requires` entry has a `concepts` gloss."""
    req = declared_names(o, "requires")
    con = declared_names(o, "concepts")
    return [f"requires without a concepts gloss: {n}" for n in sorted(req - con)]


def c_undeclared_body_names(cid, o, span):
    """M4 hard. Every name used in a body is declared somewhere."""
    dec = (declared_names(o, "ontology") | declared_names(o, "requires")
           | declared_names(o, "inputs") | declared_names(o, "concepts"))
    bad = []
    for b in bodies(o):
        for n in names_in(b) - dec:
            bad.append(f"body name never declared: {n}   in `{b}`")
    return sorted(set(bad))


def c_coined_unused(cid, o, span):
    """M5 review (P9 narrowed). Every name YOU COINED gets used somewhere."""
    needs = set(needs_names(span))
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


def c_shared_body_obliges(cid, o, span):
    """M7 review (P4). Several obliges sharing ONE identical body."""
    seen = {}
    for e in entries(o, "asserts"):
        if isinstance(e, dict) and e.get("status") == "oblige":
            seen.setdefault(e.get("body") or "", []).append(e.get("act"))
    return [f"{len(v)} obliges share one body `{k}`: {v}"
            for k, v in seen.items() if len(v) > 1]


def c_tautology(cid, o, span):
    """M8 review/info (P8). Head functor recurring in its own body.
    The anti-rule stands: over a bare-variable act this is schema-forced (info)."""
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
    """M9 hard. `read_back` %-count and `read_back_slots` length agree."""
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
    """M10 hard. Every distinct act functor in `asserts` has a closure entry."""
    acts = set()
    for h in heads(o):
        acts |= (names_in(h) or set())
    cl = set()
    for e in entries(o, "closure"):
        n = e if isinstance(e, str) else (e.get("act") or e.get("name") or e.get("act_class") or "")
        cl |= (names_in(str(n)) or {str(n).split("/")[0]})
    return [f"act class governed with no closure declaration: {a}"
            for a in sorted(acts - cl) if a]


def c_citation(cid, o, span):
    """M11 hard. Every citation cites exactly this node id.
    DIVERGES from slice-3 mech.py deliberately: that version grepped the whole
    JSON blob for L-markers, which false-positives on ASP variables named L1/L2
    inside glosses (3 modules on the first corpus run). Only `cites` values are
    citations."""
    bad = []
    cites = []

    def walk(v):
        if isinstance(v, dict):
            c = v.get("cites")
            if isinstance(c, str) and c:
                cites.append(c)
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(o)
    for c in set(cites):
        if re.fullmatch(r"L\d+(?:-L?\d+)?", c):
            bad.append(f"line-number citation (never citable): {c}")
        elif c != cid:
            bad.append(f"citation to a foreign id: {c}")
    return bad


def c_polarity(cid, o, span):
    """M12 review (P1). A `prefer` whose read_back negates."""
    bad = []
    for e in entries(o, "asserts"):
        if not isinstance(e, dict) or e.get("status") != "prefer":
            continue
        rb = str(e.get("read_back") or "").lower()
        if re.search(r"\b(not|never|avoid|should not|must not|refrain|without)\b", rb):
            bad.append(f"prefer whose read_back negates: {e.get('act')} — {e.get('read_back')!r}")
    return bad


def c_good_bad_poles(cid, o, span):
    """M13 review (P10). GOOD/BAD pair whose two arms do not differ."""
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
    """M14 review. A `concepts` gloss that just restates the predicate name."""
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
    """M15 review (N10). Coined lowercase constants that trace to no substring
    of the narrowed span."""
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
    """M16 (subsumes M6/N5). `not X` under permit/prefer is hard — silence
    licenses the act. Under forbid/oblige it is conservative (info)."""
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
    """M17 review. Ontology predicate unreachable from any assert, even
    transitively — content a reader sees and the solver never uses."""
    heads_of = {}
    for e in entries(o, "ontology"):
        if not isinstance(e, dict):
            continue
        h = (_NAME.findall(str(e.get("atom", ""))) or [None])[0]
        if not h:
            continue
        heads_of.setdefault(h, set()).update(names_in(str(e.get("body") or "")))
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
    """M18 review. Predicate both derived here and declared a situation input."""
    hs = set()
    for e in entries(o, "ontology"):
        if isinstance(e, dict):
            hs |= set(_NAME.findall(str(e.get("atom", ""))))
    inp = declared_names(o, "inputs")
    return [f"predicate is both an ontology head and a situation input: {n}"
            for n in sorted(hs & inp)]


def c_claims_uncovered(cid, o, span):
    """M19 review (P3 made mechanical). A claim sharing no vocabulary with any
    encoded rule is the fingerprint of a dropped obligation. Directs attention,
    does not adjudicate."""
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
    """M20 review. A coined predicate shadowing a name the module must borrow."""
    coined = declared_names(o, "ontology") | declared_names(o, "inputs")
    out = []
    for n in needs_names(span):
        for c in sorted(coined):
            if c != n and (c.startswith(n + "_") or n.startswith(c + "_")
                           or n in c):
                out.append(f"coined `{c}` shadows the NEEDS name `{n}`")
    return out


def c_gloss_duplicated(cid, o, span):
    """M21 review (GLOSS-1). Ontology gloss byte-identical to the concepts gloss
    of the same predicate — the bodied case is undescribed."""
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
    """M22 review (ORDER-1, widens N8). Arity>=2 concept whose gloss does not
    pin argument order."""
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
        varsy = re.findall(r"\b([A-Z][A-Za-z0-9_]{0,2})\b", g)
        if not ordinal and len(set(varsy)) < ar:
            out.append(f"arity-{ar} concept `{e.get('name')}` does not pin "
                       f"argument order in its gloss")
    return out


def c_open_list_closed(cid, o, span):
    """M23 review (C2). Narrowed span ends an enumeration open; is there a route
    into the class besides named ground constants?"""
    m = re.search(r"\[node narrows this span to: \"(.*?)\"\]", span, re.S)
    hay = (m.group(1) if m else "").lower()
    if not hay:
        hay = span.split("SOURCE TEXT")[-1].lower()
    markers = [k for k in ("etc.", "e.g.", "such as", "or other", "and other",
                           "including", "among other") if k in hay]
    if not markers:
        return []
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
    """M24 hard SINCE THE RULING. A borrowed NEEDS name's gloss stamped
    `licence: textual` citing this clause. Before DECISION_licence_textual.md
    (2026-08-16) the prompt's own worked example demonstrated this, so it was a
    prompt finding; the ruling makes it a module defect — the fix is
    licence-field-only, so it never requires a redraw on its own."""
    needs = set(needs_names(span))
    out = []
    for e in entries(o, "concepts"):
        if not isinstance(e, dict):
            continue
        n = str(e.get("name", "")).split("/")[0]
        if n in needs and e.get("licence") == "textual" and e.get("cites") == cid:
            out.append(f"borrowed NEEDS name `{n}` glossed `textual` citing this "
                       f"clause [manufactured citation under the 2026-08-16 ruling]")
    return out


# check registry: (name, fn, tier). Tier is the DEFAULT for the check; two
# checks re-tier individual hits by content (tautology, naf_polarity) below.
PER_MODULE = [
    ("needs_in_requires", c_needs_in_requires, "hard"),
    ("provides_defined", c_provides_defined, "hard"),
    ("requires_has_concept", c_requires_has_concept, "hard"),
    ("undeclared_body_names", c_undeclared_body_names, "hard"),
    ("coined_unused", c_coined_unused, "review"),
    ("shared_body_obliges", c_shared_body_obliges, "review"),
    ("tautology", c_tautology, "review"),
    ("slots", c_slots, "hard"),
    ("closure_coverage", c_closure_coverage, "hard"),
    ("citation", c_citation, "hard"),
    ("polarity", c_polarity, "review"),
    ("good_bad_poles", c_good_bad_poles, "review"),
    ("gloss_restates", c_gloss_restates, "review"),
    ("unanchored_constants", c_unanchored_constants, "review"),
    ("naf_polarity", c_naf_polarity, "hard"),
    ("inert_ontology", c_inert_ontology, "review"),
    ("head_and_input", c_head_and_input, "review"),
    ("claims_uncovered", c_claims_uncovered, "review"),
    ("requires_shadowed", c_requires_shadowed, "review"),
    ("gloss_duplicated", c_gloss_duplicated, "review"),
    ("argorder_unpinned", c_argorder_unpinned, "review"),
    ("open_list_closed", c_open_list_closed, "review"),
    ("needs_gloss_licence", c_needs_gloss_licence, "hard"),
]


def tier_of(check, hit, default):
    if check == "tautology":
        return "info" if "SCHEMA-FORCED" in hit else "review"
    if check == "naf_polarity":
        return "hard" if hit.startswith("DANGEROUS") else "info"
    return default

# ---------------------------------------------------------------- cross-module
# (slice-3 cross.py, over the whole gathered set)

_SORTS = ["rule", "instruction", "heading", "section", "message", "content",
          "response", "request", "person", "number", "context", "work", "group"]


def _h(e):
    m = re.match(r"\s*([a-z_][A-Za-z0-9_]*)\s*\(", str(e.get("atom", "")))
    return m.group(1) if m else None


def concept_index(mods):
    ix = defaultdict(list)
    for cid, o in mods.items():
        req = {str(r).split("/")[0] for r in (o.get("requires") or [])}
        onto = {(_h(e)) for e in (o.get("ontology") or []) if isinstance(e, dict) and _h(e)}
        for e in (o.get("concepts") or []):
            if not isinstance(e, dict):
                continue
            n = str(e.get("name", "")).split("/")[0]
            role = "PROVIDES" if n in onto else ("borrows" if n in req else "coins")
            ix[n].append((cid, e.get("arity"), str(e.get("gloss") or ""), role))
    return ix


def x_arity_disagreement(ix, mods):
    """X1 hard. One shared name, two arities — the link never fires, never errors."""
    out = []
    for n, rows in sorted(ix.items()):
        ar = {r[1] for r in rows}
        if len(rows) > 1 and len(ar) > 1:
            out.append(f"`{n}` declared with arities {sorted(map(str, ar))} across "
                       + ", ".join(r[0] for r in rows))
    return out


def x_sort_disagreement(ix, mods):
    """X2 review. Shared name whose glosses put a different SORT in argument 1."""
    out = []
    for n, rows in sorted(ix.items()):
        if len(rows) < 2:
            continue
        sorts = {}
        for cid, ar, g, role in rows:
            gl = g.lower()
            found = [s for s in _SORTS if re.search(rf"\b{s}s?\b", gl[:120])]
            sorts[cid] = (found[:2], role)
        hs = {tuple(v[0][:1]) for v in sorts.values() if v[0]}
        if len(hs) > 1:
            out.append(f"`{n}` glossed over DIFFERENT SORTS: "
                       + "; ".join(f"{c}={v[0]}({v[1]})" for c, v in sorts.items()))
    return out


def x_section_local_gloss(ix, mods):
    """X3 hard ⭐. A shared global predicate glossed section-locally by several
    borrowers, each naming a DIFFERENT section — the root_authority shape:
    once linked, any provider's atom satisfies all of them, so every module's
    stated assumption is false of the predicate it actually gets."""
    out = []
    pat = re.compile(r"(#[a-z_]+|\b[a-z]+[- ](?:creators?|protection|content)\b"
                     r"|\bthat section\b|\bthis section\b)", re.I)
    for n, rows in sorted(ix.items()):
        if len(rows) < 2:
            continue
        hits = []
        for cid, ar, g, role in rows:
            m = pat.findall(g)
            if m:
                hits.append((cid, role, sorted(set(x.strip() for x in m))))
        if len(hits) > 1 and len({tuple(h[2]) for h in hits}) > 1:
            out.append(f"`{n}` is glossed SECTION-LOCALLY by {len(hits)} modules, "
                       f"each naming a DIFFERENT section: "
                       + "; ".join(f"{c}({r})->{s}" for c, r, s in hits))
    return out


def x_provider_borrower_gap(ix, mods):
    """X4 info. Provider/borrower pairs listed so a human reads two sentences
    instead of five modules. Volume is high at corpus scale; summarized."""
    out = []
    for n, rows in sorted(ix.items()):
        prov = [r for r in rows if r[3] == "PROVIDES"]
        borr = [r for r in rows if r[3] == "borrows"]
        if prov and borr:
            out.append(f"`{n}`: provided by {prov[0][0]}, borrowed by {len(borr)} module(s)")
    return out


def x_orphan_borrow(ix, mods):
    """X5 info. Borrowed by some module, provided by none translated yet.
    EXPECTED in a partial corpus — on the record, not a defect."""
    out = []
    for n, rows in sorted(ix.items()):
        if any(r[3] == "borrows" for r in rows) and not any(
                r[3] == "PROVIDES" for r in rows):
            out.append(f"`{n}` borrowed by {sum(1 for r in rows if r[3] == 'borrows')} "
                       f"module(s), no provider translated yet")
    return out


def x_seam_contract(ix, mods):
    """X6 hard. A module declares a SEAM_CONTRACT.json name at a different
    arity than the contract pins (SEAM_CONTRACT.md, 2026-08-16). Unlike X1,
    this fires even when only ONE module carries the name — the contract is
    the other party."""
    path = os.path.join(HERE, "SEAM_CONTRACT.json")
    if not os.path.exists(path):
        return []
    contract = json.load(open(path))["names"]
    out = []
    for n, spec in sorted(contract.items()):
        for cid, ar, g, role in ix.get(n, []):
            try:
                ok = int(ar) == int(spec["arity"])
            except (TypeError, ValueError):
                ok = False
            if not ok:
                out.append(f"`{n}` declared /{ar} by {cid} ({role}); contract "
                           f"pins /{spec['arity']} ({', '.join(spec['args'])})")
    return out


CROSS = [
    ("seam_contract", x_seam_contract, "hard"),
    ("arity_disagreement", x_arity_disagreement, "hard"),
    ("sort_disagreement", x_sort_disagreement, "review"),
    ("section_local_gloss", x_section_local_gloss, "hard"),
    ("provider_borrower_gap", x_provider_borrower_gap, "info"),
    ("orphan_borrow", x_orphan_borrow, "info"),
]

# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="write the full report here")
    ap.add_argument("--ids", nargs="*", default=None,
                    help="restrict to these clause ids")
    ap.add_argument("--quiet", action="store_true",
                    help="summary only, no per-hit lines")
    args = ap.parse_args(argv)

    raw = gather()
    if args.ids:
        raw = {c: v for c, v in raw.items() if c in set(args.ids)}
    report = {"modules": {}, "cross": {}, "summary": {}}
    abstained, unreadable = [], []
    mods = {}
    for cid, (o, span, run) in sorted(raw.items()):
        if "_unreadable" in o:
            unreadable.append(cid)
            continue
        if o.get("outcome") == "abstained":
            abstained.append(cid)
            continue
        mods[cid] = o
        row = {"run": run, "region": region_of(cid),
               "hits": {"hard": [], "review": [], "info": []}}
        for name, fn, default in PER_MODULE:
            try:
                hits = fn(cid, o, span)
            except Exception as ex:      # a check must never mask a module
                hits = [f"CHECK ERROR {ex!r}"]
                default = "hard"
            for h in hits:
                row["hits"][tier_of(name, h, default)].append(f"{name}: {h}")
        report["modules"][cid] = row

    ix = concept_index(mods)
    for name, fn, tier in CROSS:
        hits = fn(ix, mods)
        report["cross"][name] = {"tier": tier, "hits": hits}

    # ---- summary
    per_region = defaultdict(lambda: {"n": 0, "clean": 0, "hard": 0, "review": 0})
    n_clean = 0
    for cid, row in report["modules"].items():
        r = per_region[row["region"]]
        r["n"] += 1
        r["hard"] += len(row["hits"]["hard"])
        r["review"] += len(row["hits"]["review"])
        if not row["hits"]["hard"]:
            r["clean"] += 1
            n_clean += 1
    report["summary"] = {
        "modules_translated": len(report["modules"]),
        "abstained": len(abstained),
        "unreadable": unreadable,
        "hard_clean_modules": n_clean,
        "cross_hard_hits": sum(len(v["hits"]) for k, v in report["cross"].items()
                               if v["tier"] == "hard"),
        "per_region": {k: dict(v) for k, v in sorted(per_region.items())},
    }

    # ---- print
    s = report["summary"]
    print(f"corpus gate over {s['modules_translated']} translated modules "
          f"(+{s['abstained']} abstained, {len(unreadable)} unreadable)")
    print(f"hard-clean modules: {s['hard_clean_modules']}/{s['modules_translated']}")
    print(f"{'region':14s} {'n':>4s} {'hard-clean':>10s} {'hard hits':>10s} {'review':>8s}")
    for reg, v in sorted(per_region.items(),
                         key=lambda kv: int(kv[0][1:].split("_")[0])):
        print(f"{reg:14s} {v['n']:4d} {v['clean']:10d} {v['hard']:10d} {v['review']:8d}")
    print("=" * 60)
    counts = defaultdict(int)
    for row in report["modules"].values():
        for tier in ("hard", "review"):
            for h in row["hits"][tier]:
                counts[(tier, h.split(":")[0])] += 1
    for (tier, name), c in sorted(counts.items()):
        print(f"  {tier:7s} {name:24s} {c}")
    print("=" * 60)
    for name, v in report["cross"].items():
        print(f"cross {name} [{v['tier']}]: {len(v['hits'])} hit(s)")
        if not args.quiet and v["tier"] != "info":
            for h in v["hits"][:20]:
                print("   *", h)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=1, sort_keys=True)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
