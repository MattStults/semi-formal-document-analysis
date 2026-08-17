#!/usr/bin/env python3
"""MECHANICAL defect detectors, grouped BY LAYER.

Why mechanical.  Every prior arm on these 17 clauses was scored by one
adjudicator who had already read the historical defect table, and
`list_in_prompt_insample/RESULT.md` §10 records that the contamination runs
TOWARD the finding.  A per-layer comparison across three arms cannot rest on
that.  Every detector below reads only the emitted JSON and the node's own
user block, and is calibrated by reproducing the counts published in
`list_in_prompt_insample/RESULT.md` §11 before it is used on anything new.

The detectors are PROXIES and are named as such.  Each one is stated so a
reader can recompute it.  Where a proxy is known to be loose, the loose
direction is named in its docstring.

Layers (the brief's four):
  DEO   the deontic layer   — which act, which status, which condition
  ONT   the ontology layer  — what classes exist, bodied rule vs ground atom
  DECL  the declaration layer — requires/inputs/concepts, arity, licences
  CITE  citation discipline
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "config_corpus_all.json")

CLAUSES = [
    "l1_170_n056", "l3147_3238_n003", "l1707_1973_n006", "l3239_3382_n002",
    "l4252_4482_n016", "l171_426_n022", "l699_796_n012", "l1001_1107_n005",
    "l1368_1541_n019", "l1707_1973_n022", "l2126_2404_n016",
    "l2474_2554_n004", "l2821_3040_n017", "l3239_3382_n004",
    "l3596_3876_n009", "l3877_3953_n014", "l4252_4482_n005",
]

_VAR = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")
_ATOM = re.compile(r"([a-z][A-Za-z0-9_]*)\s*(\(([^()]*)\))?")


def needs_names(user_block):
    """The NEEDS names the node handed this module, read off the user block."""
    m = re.search(r"^NEEDS[^\n]*\n((?:  - .*\n)+)", user_block, re.M)
    if not m:
        return []
    return [ln.split(":", 1)[0].strip(" -")
            for ln in m.group(1).splitlines() if ln.strip().startswith("- ")]


def _split_body(body):
    """Body atoms, respecting one level of parens."""
    if not body:
        return []
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _vars(s):
    return _VAR.findall(s or "")


def _functor(term):
    m = re.match(r"\s*(?:not\s+)?([a-z][A-Za-z0-9_]*)", term or "")
    return m.group(1) if m else None


def _norm_body(body):
    return ", ".join(sorted(a.strip() for a in _split_body(body)))


# --------------------------------------------------------------- ONT layer
def ont_vacuous(obj):
    """ONT-1 VACUOUS BODY.  A bodied ontology rule whose body is nothing but
    type declarations over the head's own variables — `X(R) :- response(R)`,
    `no_moral_ambiguity(S) :- scenario(S)`.  Derives the head of every
    instance of the type, i.e. of every case.

    Test: every body atom is unary, its single argument is a variable, and
    that variable is a head variable.  LOOSE DIRECTION: a body that is
    genuinely one discriminating unary condition (`restricted(M)`) scores as
    vacuous.  Reported hits are listed so this is checkable."""
    hits = []
    for e in obj.get("ontology") or []:
        body = (e.get("body") or "").strip()
        if not body:
            continue
        hv = set(_vars(e.get("atom") or ""))
        atoms = _split_body(body)
        if not atoms:
            continue
        if all(re.fullmatch(r"[a-z][A-Za-z0-9_]*\(\s*[A-Z][A-Za-z0-9_]*\s*\)",
                            a.strip()) and set(_vars(a)) <= hv
               for a in atoms):
            hits.append(f"{e.get('atom')} :- {body}")
    return hits


def ont_unlinked(obj):
    """ONT-2 UNLINKED SINGLETON.  A variable occurring exactly once across a
    bodied ontology rule: it binds nothing and the condition does no work."""
    hits = []
    for e in obj.get("ontology") or []:
        body = (e.get("body") or "").strip()
        if not body:
            continue
        text = (e.get("atom") or "") + " " + body
        vs = _vars(text)
        singles = sorted({v for v in vs if vs.count(v) == 1})
        if singles:
            hits.append(f"{e.get('atom')} :- {body}  [singleton {','.join(singles)}]")
    return hits


def ont_coextensive(obj):
    """ONT-3 COEXTENSIVE HEADS.  Two or more ontology heads sharing ONE
    identical body: the classes they name have the same extension, so the
    distinction the span drew is gone."""
    seen = {}
    for e in obj.get("ontology") or []:
        b = _norm_body(e.get("body"))
        if not b:
            continue
        seen.setdefault(b, []).append(e.get("atom"))
    return [f"{' == '.join(v)}  :- {k}" for k, v in seen.items() if len(v) > 1]


# --------------------------------------------------------------- DEO layer
_NEG = re.compile(r"avoid|minimi[sz]|should not|must not|disfavo|refrain|"
                  r"discourag|not to |excessive|redundant|overstep|"
                  r"is to be reduced|is to be limited", re.I)
_AVOID_VERB = re.compile(r"avoid|minimi[sz]|refrain|reduce|limit|prevent|"
                         r"withhold|abstain|decline", re.I)


def deo_prefer_polarity(obj):
    """DEO-1 STATUS HAS NO NEGATIVE POLE.  `prefer A` where the read-back says
    A is the thing to AVOID — the compiled rule then states the opposite of
    the document.  Test: status == prefer, read-back matches a negative
    marker, and the ACT's own functor does NOT name the avoidance."""
    hits = []
    for a in obj.get("asserts") or []:
        if a.get("status") != "prefer":
            continue
        rb = a.get("read_back") or ""
        act = a.get("act") or ""
        if _NEG.search(rb) and not _AVOID_VERB.search(act):
            hits.append(f"prefer {act}  // {rb}")
    return hits


def deo_shared_body(obj):
    """DEO-2 DISJUNCTION AS CONJUNCTION.  Two or more `oblige` assertions on
    ONE identical body: the span's "do A, B, OR C" compiles to "do all
    three", so satisfying one violates the other two."""
    seen = {}
    for a in obj.get("asserts") or []:
        if a.get("status") != "oblige":
            continue
        seen.setdefault(_norm_body(a.get("body")), []).append(a.get("act"))
    return [f"oblige {' & '.join(v)}  :- {k}"
            for k, v in seen.items() if len(v) > 1 and k]


def deo_bodiless_oblige(obj):
    """DEO-2b BODILESS `oblige`, two or more.  Split out of DEO-2 AFTER the
    scores were read, and the split is recorded rather than folded in: the
    original detector grouped on the normalised body string, so several
    assertions with NO body at all landed in one group and scored as the
    disjunction defect.  They are a different thing -- an unconditional duty,
    which may be right -- so they get their own row and the DEO-2 row is
    restricted to a shared NON-EMPTY body.  ⚠️ This change was made because
    arm G's DEO-2 hits were inspected and found to be all-bodiless; it
    therefore cannot be scored as a pre-registered prediction, and G-3 is
    reported against BOTH definitions."""
    n = sum(1 for a in obj.get("asserts") or []
            if a.get("status") == "oblige" and not (a.get("body") or "").strip())
    return [f"{n} `oblige` assertions with no body at all"] if n > 1 else []


# -------------------------------------------------------------- DECL layer
def decl_borrowed_gloss(obj, needs):
    """DECL-1 BORROWED-GLOSS LICENCE.  A concept the NODE established
    elsewhere, re-glossed here and stamped `licence: textual` — which, under
    this node's CITATION instruction, can only cite THIS node.  The module
    thereby cites itself for a definition it did not author.  The schema
    offers `assumed` + `inference` for exactly this, so the defect is
    reachable without any schema change."""
    hits = []
    byname = {c.get("name"): c for c in (obj.get("concepts") or [])}
    for n in needs:
        c = byname.get(n)
        if c is None:
            continue
        if c.get("licence") == "textual":
            hits.append(f"{n}: textual cites={c.get('cites')}")
    return hits


def decl_needs_misfiled(obj, needs):
    """DECL-2 A NEEDS NAME IN THE WRONG FIELD.  The node says every NEEDS name
    belongs in `requires`, never in `ontology`, never in `inputs`."""
    req = {re.sub(r"/\d+$", "", r) for r in (obj.get("requires") or [])}
    inp = {re.sub(r"/\d+$", "", r) for r in (obj.get("inputs") or [])}
    onh = {_functor(e.get("atom")) for e in (obj.get("ontology") or [])}
    hits = []
    for n in needs:
        if n in inp:
            hits.append(f"{n} in inputs")
        if n in onh:
            hits.append(f"{n} defined in ontology")
        if n not in req and (n in inp or n in onh):
            pass
    return hits


def decl_needs_dropped(obj, needs):
    """DECL-3 A NEEDS NAME NOT DECLARED AT ALL.  Named by the node, absent
    from `requires`."""
    req = {re.sub(r"/\d+$", "", r) for r in (obj.get("requires") or [])}
    return [n for n in needs if n not in req]


def decl_undeclared_body_name(obj):
    """DECL-4 A BODY NAME NOTHING DECLARES.  Every predicate in an ontology or
    assert body must be in `ontology`, `requires` or `inputs`; otherwise the
    rule can never fire.  (`checks.py` covers part of this; it is recomputed
    here so the layer table is self-contained.)"""
    declared = set()
    for r in (obj.get("requires") or []) + (obj.get("inputs") or []):
        declared.add(re.sub(r"/\d+$", "", r))
    for e in obj.get("ontology") or []:
        f = _functor(e.get("atom"))
        if f:
            declared.add(f)
    for c in obj.get("concepts") or []:
        pass                       # a concepts entry declares MEANING, not a source
    hits = []
    for e in (obj.get("ontology") or []):
        for a in _split_body(e.get("body")):
            f = _functor(a)
            if f and f not in declared:
                hits.append(f"ontology body `{f}` undeclared")
    for a in (obj.get("asserts") or []):
        for at in _split_body(a.get("body")):
            f = _functor(at)
            if f and f not in declared:
                hits.append(f"assert body `{f}` undeclared")
    return sorted(set(hits))


# -------------------------------------------------------------- CITE layer
def cite_foreign(obj, cid):
    """CITE-1 A CITATION TO ANOTHER ID.  The node instructs that every cite be
    EXACTLY this node's id."""
    hits = []
    for fld in ("concepts", "ontology", "asserts", "beats", "defines"):
        for e in obj.get(fld) or []:
            c = (e.get("cites") or "").strip()
            if c and c != cid:
                hits.append(f"{fld}: cites {c}")
    return hits


DETECTORS = [
    ("ONT-1 vacuous body", "ONT", lambda o, n, c: ont_vacuous(o)),
    ("ONT-2 unlinked singleton", "ONT", lambda o, n, c: ont_unlinked(o)),
    ("ONT-3 coextensive heads", "ONT", lambda o, n, c: ont_coextensive(o)),
    ("DEO-1 prefer polarity", "DEO", lambda o, n, c: deo_prefer_polarity(o)),
    ("DEO-2 shared-body oblige", "DEO", lambda o, n, c: deo_shared_body(o)),
    ("DEO-2b bodiless oblige x2+", "DEO", lambda o, n, c: deo_bodiless_oblige(o)),
    ("DECL-1 borrowed-gloss licence", "DECL", lambda o, n, c: decl_borrowed_gloss(o, n)),
    ("DECL-2 NEEDS misfiled", "DECL", lambda o, n, c: decl_needs_misfiled(o, n)),
    ("DECL-3 NEEDS dropped", "DECL", lambda o, n, c: decl_needs_dropped(o, n)),
    ("DECL-4 undeclared body name", "DECL", lambda o, n, c: decl_undeclared_body_name(o)),
    ("CITE-1 foreign citation", "CITE", lambda o, n, c: cite_foreign(o, c)),
]


def floor(obj, row, cfg, rows):
    idk = cfg["corpus"]["id_key"]
    ids = {r[idk] for r in rows}
    _, breaches = schema.validate_all(obj, row[idk], ids)
    out = {"breaches": len(breaches), "outcome": None, "repair_needed": None}
    try:
        res = checks.run_checks(obj, row, ids)
        out["outcome"] = res.outcome
        out["repair_needed"] = bool(res.repair_needed)
    except Exception as exc:                                   # noqa: BLE001
        out["outcome"] = f"raised:{exc!r}"
    return out


def score_file(path, cid, ctx):
    cfg, rows, by, users = ctx
    with open(path, encoding="utf-8") as fh:
        obj = json.load(fh)
    # arm B stores the module inside a record envelope; arms A and G store it bare
    if "module" in obj and "outcome" not in obj:
        obj = obj["module"]
    needs = needs_names(users[cid])
    rec = {"clause": cid, "needs": needs, "hits": {}, "n_needs": len(needs)}
    for name, layer, fn in DETECTORS:
        h = fn(obj, needs, cid)
        if h:
            rec["hits"][name] = h
    rec["floor"] = floor(obj, by[cid], cfg, rows)
    return rec


def context():
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    idk = cfg["corpus"]["id_key"]
    by = {r[idk]: r for r in rows}
    users = {c: translate.build_user(by[c], rows, cfg)[0] for c in CLAUSES}
    return cfg, rows, by, users


def score_arm(pathfn, ctx):
    recs = []
    for cid in CLAUSES:
        p = pathfn(cid)
        if not os.path.exists(p):
            recs.append({"clause": cid, "missing": True, "hits": {}})
            continue
        try:
            recs.append(score_file(p, cid, ctx))
        except json.JSONDecodeError as exc:
            recs.append({"clause": cid, "unparsed": str(exc), "hits": {}})
    return recs


def summarise(recs):
    tab = {}
    for name, layer, _ in DETECTORS:
        n = sum(1 for r in recs if r["hits"].get(name))
        k = sum(len(r["hits"].get(name, [])) for r in recs)
        tab[name] = (layer, n, k)
    return tab


def main():
    ctx = context()
    arms = {
        "A unaided (loop turn 1)":
            lambda c: os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop",
                                   "out", f"{c}.turn1.raw.json"),
        "B list-in-prompt (in-sample)":
            lambda c: os.path.join(PHASE1, "_debug_gen11",
                                   "list_in_prompt_insample", "out",
                                   f"{c}.json"),
        "G decomposed":
            lambda c: os.path.join(HERE, "out", f"{c}.final.json"),
    }
    if len(sys.argv) > 1:
        arms = {k: v for k, v in arms.items() if k.startswith(sys.argv[1])}
    allrecs = {}
    for arm, fn in arms.items():
        recs = score_arm(fn, ctx)
        allrecs[arm] = recs
        print(f"\n===== {arm} =====")
        have = [r for r in recs if not r.get("missing")]
        print(f"scored {len(have)}/{len(CLAUSES)}")
        if not have:
            continue
        for name, (layer, n, k) in summarise(have).items():
            print(f"  [{layer:4}] {name:32} {n:2}/{len(have)} clauses, {k:3} hits")
        inv = sum(1 for r in have if r.get("floor", {}).get("outcome")
                  != "translated")
        print(f"  floor: {inv}/{len(have)} not `translated`")
    with open(os.path.join(HERE, "layer_scores.json"), "w",
              encoding="utf-8") as fh:
        json.dump(allrecs, fh, indent=1)
    print("\nwrote layer_scores.json")


if __name__ == "__main__":
    main()
