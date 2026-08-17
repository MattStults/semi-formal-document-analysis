#!/usr/bin/env python3
"""⭐ THE CROSS-CLAUSE SWEEP — every class any slice-4 clause raised, run back
across ALL slice-4 clauses.

The gap this closes, measured on the previous cohort: the loop NAMED a
licence-inheritance class, called it "mechanically checkable; nothing checks
it", and left it in 12 of 17 clauses — because the loop was per-clause and had
no end-of-run sweep. A class found at clause 5 never reached clause 1.

Every check here is a few lines of Python over the module JSON. That is the
point: every high-value class this campaign has found was checkable in a few
lines that nobody had written.

Usage:  .venv/bin/python sweep.py            # all modules in out/
        .venv/bin/python sweep.py <id> ...
"""
import json, os, re, sys, glob, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CORPUS = os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")

_ROWS = json.load(open(CORPUS))["clauses"]
_BYID = {r["id"]: r for r in _ROWS}

WORD = re.compile(r"[a-z0-9_]+")
FUNCTOR = re.compile(r"([a-z][a-zA-Z0-9_]*)\s*\(")
BARE = re.compile(r"\b([a-z][a-zA-Z0-9_]*)\b")


# ---------------------------------------------------------------- span helpers

def narrowed_text(cid):
    """The text the module is actually licensed by.

    If the node carries `[node narrows this span to: "…"]`, THAT is the scope
    (REVIEW_LIST P6). If it does not, the whole printed SOURCE TEXT block is.
    """
    q = _BYID[cid]["quote"]
    m = re.search(r'\[node narrows this span to:\s*"(.*?)"\]\s*$', q, re.S)
    if m:
        return m.group(1), True
    m = re.search(r"SOURCE TEXT \(.*?\):\n(.*)$", q, re.S)
    return (m.group(1) if m else q), False


def establishes(cid):
    m = re.search(r"ESTABLISHES \(.*?\):\n(.*?)\n\n", _BYID[cid]["quote"], re.S)
    return m.group(1).strip() if m else ""


def needs_names(cid):
    m = re.search(r"^NEEDS .*?:\n(.*?)\n\nCITATION", _BYID[cid]["quote"],
                  re.S | re.M)
    if not m:
        return set()
    return set(re.findall(r"^\s+-\s+([a-z_][a-zA-Z0-9_]*):", m.group(1), re.M))


def provides_names(cid):
    m = re.search(r"^PROVIDES \(.*?\):\n(.*?)\n\nNEEDS", _BYID[cid]["quote"],
                  re.S | re.M)
    if not m:
        return set()
    return set(re.findall(r"^\s+-\s+([a-z_][a-zA-Z0-9_]*):", m.group(1), re.M))


# ---------------------------------------------------------------- module helpers

def bare(name):
    return name.split("/")[0].strip()


def declared(mod):
    """name -> licence, for everything the module declares a licence on."""
    out = {}
    for c in mod.get("concepts") or []:
        out.setdefault(bare(c.get("name", "")), c.get("licence"))
    for o in mod.get("ontology") or []:
        f = FUNCTOR.search(o.get("atom", "") or "")
        n = f.group(1) if f else bare(o.get("atom", "") or "")
        # an ontology entry ASSERTS; its licence is the stronger claim
        out[n] = o.get("licence")
    return out


def concept_licences(mod):
    return {bare(c.get("name", "")): c.get("licence")
            for c in (mod.get("concepts") or [])}


def split_conjuncts(text):
    """Split an ASP body on top-level commas. ⚠️ A naive `text.split(',')`
    shreds `f(a, b)` into two conjuncts and was the first version of this
    function; it made every constant ARGUMENT look like a predicate."""
    out, depth, cur = [], 0, ""
    for ch in text or "":
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [c.strip() for c in out if c.strip()]


def body_functors(text):
    """The predicates a body actually CALLS.

    ⛔ Only the functor of each top-level conjunct counts. A lowercase token
    sitting in an ARGUMENT slot — `instruction_level(I, developer)` — is a
    constant, not a predicate, and counting it produced a run of false
    UNFIREABLE hits on the previous cohort before this was fixed."""
    fs = set()
    for c in split_conjuncts(text):
        c = re.sub(r"^not\s+", "", c).strip()
        m = re.match(r"([a-z][a-zA-Z0-9_]*)\s*\(", c)
        if m:
            fs.add(m.group(1))
            continue
        m = re.fullmatch(r"([a-z][a-zA-Z0-9_]*)", c)
        if m:
            fs.add(m.group(1))
    return fs


def all_bodies(mod):
    """(where, body-text) for every body in the module."""
    for o in mod.get("ontology") or []:
        if o.get("body"):
            yield f"ontology:{o.get('atom')}", o["body"]
    for a in mod.get("asserts") or []:
        if a.get("body"):
            yield f"asserts:{a.get('status')}/{a.get('act')}", a["body"]
    for b in mod.get("beats") or []:
        if b.get("body"):
            yield f"beats:{b.get('winner')}", b["body"]


def n_asserts(mod):
    return len(mod.get("asserts") or [])


# ---------------------------------------------------------------- the checks

def C_LICINH(cid, mod):
    """⭐ LICENCE INHERITANCE. 00_task.md, in bold: 'A conclusion inherits the
    weakest licence in its derivation.' So a `textual` conclusion whose BODY
    rests on a name this module declares `assumed`/`world` is over-claiming its
    licence. MEASURED on the previous cohort: 32 instances, 12 of 17 modules,
    named as a class and fixed in none of them."""
    lic = concept_licences(mod)
    onto = {}
    for o in mod.get("ontology") or []:
        f = FUNCTOR.search(o.get("atom", "") or "")
        if f:
            onto[f.group(1)] = o.get("licence")
    table = {**lic, **{k: v for k, v in onto.items() if v}}
    out = []
    for where, body in all_bodies(mod):
        owner = None
        for o in mod.get("ontology") or []:
            if where == f"ontology:{o.get('atom')}":
                owner = o.get("licence")
        for a in mod.get("asserts") or []:
            if where.startswith("asserts:") and a.get("body") == body:
                owner = a.get("licence")
        if owner != "textual":
            continue
        weak = sorted({f for f in body_functors(body)
                       if table.get(f) in ("assumed", "world")})
        if weak:
            out.append(f"{where} is licence=textual but its body rests on "
                       f"{weak} declared assumed/world")
    return out


def C_CLAIMS_UNENCODED(cid, mod):
    """P3 — a claim listed in `claims` and encoded in no assert is the
    fingerprint of dropped content. Reported as ATTENTION, never as a fix:
    ⛔ the 'either add a body condition or delete the claim' remedy is a
    MEASURED defect generator (E6, two independent critics, same weakening)."""
    claims = mod.get("claims") or []
    if not claims:
        return []
    enc = " ".join(json.dumps(a) for a in (mod.get("asserts") or [])) + " " + \
          " ".join(json.dumps(o) for o in (mod.get("ontology") or []))
    enc_words = set(WORD.findall(enc.lower()))
    out = []
    for c in claims:
        head = c.split(":", 1)[-1]
        content = [w for w in WORD.findall(head.lower())
                   if len(w) > 4 and w not in ("should", "assistant", "clause",
                                               "document", "models", "model")]
        if content and not (set(content) & enc_words):
            out.append(f"claim {c[:70]!r} shares no content word with any "
                       f"assert/ontology entry")
    return out


def C_INERT_GROUND(cid, mod):
    """N1 — a ground constant nothing in a real situation can ever unify with.
    `side_effect_examples(sending_email)` is inert for behaviour matching, which
    is what this corpus exists to do. Flags ontology atoms that are fully ground
    (no variable) and are NOT document facts (no `_authority`/`_section` shape)."""
    out = []
    for o in mod.get("ontology") or []:
        atom = o.get("atom", "") or ""
        args = re.search(r"\((.*)\)\s*$", atom)
        if not args:
            continue
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\b", args.group(1)):
            continue                     # has a variable — fine
        if o.get("body"):
            continue
        f = FUNCTOR.search(atom)
        fn = f.group(1) if f else atom
        if "authority" in fn or "section" in fn or "root" in fn:
            continue                     # a fact ABOUT the document — legitimate
        out.append(f"ontology {atom!r} is fully ground with no body — will any "
                   f"situation fact ever unify with it?")
    return out


def C_COINED_UNUSED(cid, mod):
    """P9, in its CORRECTED form. ⛔ A NEEDS name sitting unused in `requires`
    is CONTRACT-REQUIRED (prompt contract 2) and must NOT be flagged — the
    original form of this entry fired on every correct node module. Only names
    the translator COINED count: `ontology`, `inputs`, and any `requires` entry
    that is not a NEEDS name."""
    needs = needs_names(cid)
    used = set()
    for _, body in all_bodies(mod):
        used |= body_functors(body)
    for a in mod.get("asserts") or []:
        used |= body_functors(a.get("act", ""))
    for o in mod.get("ontology") or []:
        used |= body_functors(o.get("atom", ""))
    coined = set()
    for r in mod.get("requires") or []:
        n = bare(r if isinstance(r, str) else r.get("name", ""))
        if n and n not in needs:
            coined.add(("requires", n))
    for i in mod.get("inputs") or []:
        n = bare(i if isinstance(i, str) else i.get("name", ""))
        if n:
            coined.add(("inputs", n))
    return [f"{k} {n!r} is a name YOU COINED and appears in no body/act/atom"
            for k, n in sorted(coined) if n not in used]


def C_UNTRACED_SYMBOL(cid, mod):
    """N10 — every coined symbol must trace to a SUBSTRING of the narrowed text.
    Caught a live near-miss (`tiananmen_example`, fluent and unanchored)."""
    text, narrowed = narrowed_text(cid)
    est = establishes(cid)
    hay = set(WORD.findall((text + " " + est).lower()))
    needs = needs_names(cid) | provides_names(cid)
    out = []
    for c in mod.get("concepts") or []:
        n = bare(c.get("name", ""))
        if n in needs:
            continue
        toks = [t for t in n.split("_") if len(t) > 3]
        if toks and not any(t in hay or any(t in h or h in t for h in hay)
                            for t in toks):
            out.append(f"concept {n!r}: no token traces to the "
                       f"{'narrowed' if narrowed else 'printed'} text")
    return out


def C_TAUTOLOGICAL_GLOSS(cid, mod):
    """P8 / 10_output_format.md: 'A gloss that restates the name is rejected.'"""
    out = []
    for c in mod.get("concepts") or []:
        n = bare(c.get("name", ""))
        g = (c.get("gloss") or "").lower()
        gw = set(WORD.findall(g))
        nw = set(t for t in n.split("_") if len(t) > 2)
        if nw and nw <= gw and len(gw - nw) <= 3:
            out.append(f"concept {n!r} gloss {c.get('gloss')!r} restates the name")
    return out


def C_SELFCITE(cid, mod):
    """Citation contract: a `textual` entry must cite EXACTLY this node id."""
    out = []
    for kind in ("ontology", "asserts", "beats", "defines", "concepts"):
        for e in mod.get(kind) or []:
            if e.get("licence") == "textual" and e.get("cites") != cid:
                out.append(f"{kind} entry cites {e.get('cites')!r}, not {cid!r}")
            if e.get("licence") != "textual" and e.get("cites"):
                out.append(f"{kind} entry licence={e.get('licence')} but carries "
                           f"cites={e.get('cites')!r}")
    return out


def C_UNFIREABLE(cid, mod):
    """⛔ THE E6 TRAP, MADE MECHANICAL. A rule whose body references a predicate
    that NOTHING in this module or its declared surface can ever supply is dead.
    This is the exact shape the 'add a body condition' repair branch produces,
    and it is invisible to every other check: the module still validates, still
    reads back correctly, and never fires."""
    supplied = set()
    for o in mod.get("ontology") or []:
        f = FUNCTOR.search(o.get("atom", "") or "")
        if f:
            supplied.add(f.group(1))
    for r in mod.get("requires") or []:
        supplied.add(bare(r if isinstance(r, str) else r.get("name", "")))
    for i in mod.get("inputs") or []:
        supplied.add(bare(i if isinstance(i, str) else i.get("name", "")))
    out = []
    for where, body in all_bodies(mod):
        dead = sorted(f for f in body_functors(body) if f not in supplied)
        dead = [d for d in dead if len(d) > 2]
        if dead:
            out.append(f"{where}: body references {dead}, supplied by nothing "
                       f"in ontology/requires/inputs — the rule cannot fire")
    return out


def C_BORROWED_GATE(cid, mod):
    """⭐ RAISED BY `l3954_4251_n030`, SWEPT BACK ACROSS THE SLICE.

    Every assert body is gated on a borrowed `NEEDS` predicate, so **no rule in
    the module fires on situation facts alone** — the module is inert until some
    other node's module is linked in and supplies the borrowed fact.

    This is the SAME SHAPE as the measured E6 harm (*"add a body condition
    referencing lower_level_content to both asserts"* → both prohibitions stop
    firing in any situation that does not affirmatively supply an authority
    fact), reached without any repair step: the drafter simply wrote it that way
    from the start. That is why it is worth a mechanical check — the E6
    discussion frames the defect as something a CRITIC introduces, and it can be
    present in a first draft.

    ⚠️ NOT automatically a defect. Where the span really is conditioned on
    another node's concept, the gate is the correct encoding. The check forces
    the question: *is the gate in the span, or is it an unforced narrowing?*"""
    needs = needs_names(cid)
    asserts = mod.get("asserts") or []
    if not asserts or not needs:
        return []
    gated = []
    for a in asserts:
        used = body_functors(a.get("body", ""))
        hit = sorted(used & needs)
        if hit:
            gated.append((a.get("status"), a.get("act"), hit))
    if len(gated) != len(asserts):
        return [f"assert {s}/{act} is gated on borrowed {hit}"
                for s, act, hit in gated]
    return [f"ALL {len(asserts)} asserts are gated on a borrowed NEEDS "
            f"predicate {sorted({h for _, _, hs in gated for h in hs})} — the "
            f"module fires on NO situation until another node supplies it. Is "
            f"that gate stated in the span?"]


def C_POLE_COLLAPSE(cid, mod):
    """P10 — both poles of a GOOD/BAD example must differ. The compiled program
    must be able to tell them apart; that is the one thing the example says."""
    seen = {}
    out = []
    for a in mod.get("asserts") or []:
        key = (a.get("status"), a.get("act"))
        b = a.get("body") or ""
        if key in seen and seen[key] == b:
            out.append(f"two asserts identical in status+act+body: {key}")
        seen[key] = b
    q = _BYID[cid]["quote"]
    if "<!-- GOOD" in q and "BAD" in q:
        acts = {(a.get("status"), a.get("act")) for a in mod.get("asserts") or []}
        if len(acts) < 2 and acts:
            out.append("span is a GOOD/BAD comparison but the module emits "
                       "fewer than two distinct status+act pairs")
    return out


def C_NAF(cid, mod):
    """N5 — under NAF, `not X` makes SILENCE license the act."""
    out = []
    for where, body in all_bodies(mod):
        if re.search(r"\bnot\s+[a-z]", body):
            out.append(f"{where}: body uses negation-as-failure {body!r} — does "
                       f"absence of a fact permit something?")
    return out


def C_ARGORDER(cid, mod):
    """N8 — a borrowed relation of arity >= 2 has an ARGUMENT ORDER the gloss
    does not fix. A total inversion passes every deterministic check we have,
    so the only defence is that the reading is WRITTEN DOWN."""
    needs = needs_names(cid)
    out = []
    for c in mod.get("concepts") or []:
        n = bare(c.get("name", ""))
        if n in needs and (c.get("arity") or 0) >= 2:
            g = c.get("gloss") or ""
            if not re.search(r"\b[A-Z]\d?\b", g):
                out.append(f"borrowed relation {n}/{c.get('arity')}: gloss names "
                           f"no argument variables, so its argument ORDER is "
                           f"unrecorded and an inversion is undetectable")
    return out


def C_CLOSURE(cid, mod):
    """00_task.md rule 12 — one closure per distinct act functor. An absent
    declaration reads as `cepa` SILENTLY and changes what the corpus concludes."""
    functors = set()
    for a in mod.get("acts") or []:
        f = FUNCTOR.search(a if isinstance(a, str) else a.get("act", ""))
        functors.add(f.group(1) if f else bare(a if isinstance(a, str) else ""))
    functors.discard("")
    have = set()
    for c in mod.get("closure") or []:
        have.add(bare(c.get("act_class", "") if isinstance(c, dict) else c))
    missing = sorted(functors - have)
    return [f"act class {m!r} has no closure entry — silently read as cepa"
            for m in missing]


def C_ABSTAIN_FRAME(cid, mod):
    """⭐ THE FRAME CHECK, MADE MECHANICAL — the gap this run exists to close.
    A span headed `**Example**:`, or whose narrowing IS that heading, meets an
    abstention trigger named in 00_task.md ('it is an example'). This does not
    decide the clause; it forces the question to be ASKED, which is exactly what
    did not happen on the previous cohort (zero occurrences of 'abstain' in the
    whole transcript of an Example-headed clause)."""
    text, narrowed = narrowed_text(cid)
    q = _BYID[cid]["quote"]
    trig = []
    if re.search(r"\*\*Example\*\*\s*:", text):
        trig.append("'it is an example' — the text is/contains an `**Example**:` heading")
    if narrowed and re.fullmatch(r"\*\*Example\*\*\s*:.*", text.strip()):
        trig.append("the NARROWING is the example heading ALONE — nothing else "
                    "is in scope")
    if re.search(r"\bwe aim to\b|\baims? to\b|\bis dedicated to\b|"
                 r"\bwe are exploring\b|\bwe hope\b", text, re.I):
        trig.append("'states a goal rather than a condition' — the matrix verb "
                    "is an aim, not a norm")
    if re.match(r"^#+ ", text.strip()):
        trig.append("'it is a section heading'")
    if not trig:
        return []
    verdict = mod.get("outcome")
    return [f"ABSTENTION TRIGGER PRESENT: {t}  [module outcome = {verdict!r}]"
            for t in trig]


CHECKS = [
    ("FRAME/abstain",      C_ABSTAIN_FRAME),
    ("LICINH",             C_LICINH),
    ("UNFIREABLE",         C_UNFIREABLE),
    ("BORROWED-GATE",      C_BORROWED_GATE),
    ("CLAIMS-UNENCODED",   C_CLAIMS_UNENCODED),
    ("INERT-GROUND",       C_INERT_GROUND),
    ("COINED-UNUSED",      C_COINED_UNUSED),
    ("UNTRACED-SYMBOL",    C_UNTRACED_SYMBOL),
    ("TAUTOLOGICAL-GLOSS", C_TAUTOLOGICAL_GLOSS),
    ("SELFCITE",           C_SELFCITE),
    ("POLE-COLLAPSE",      C_POLE_COLLAPSE),
    ("NAF",                C_NAF),
    ("ARGORDER",           C_ARGORDER),
    ("CLOSURE",            C_CLOSURE),
]


def main():
    ids = sys.argv[1:] or sorted(
        os.path.basename(p)[:-5]
        for p in glob.glob(os.path.join(HERE, "out", "*.json")))
    mods = {}
    for cid in ids:
        p = os.path.join(HERE, "out", cid + ".json")
        if os.path.exists(p):
            mods[cid] = json.load(open(p))
    total = 0
    for cid, mod in mods.items():
        print(f"\n===== {cid}   outcome={mod.get('outcome')!r}  "
              f"asserts={n_asserts(mod)}")
        for name, fn in CHECKS:
            try:
                hits = fn(cid, mod)
            except Exception as e:                      # a check must never
                hits = [f"CHECK CRASHED: {e!r}"]        # silently pass
            for h in hits:
                print(f"  [{name}] {h}")
            total += len(hits)
    print(f"\nTOTAL sweep hits across {len(mods)} modules: {total}")
    print("⚠️ A hit is ATTENTION, not a verdict. Adjudicate against the span.")


if __name__ == "__main__":
    main()
