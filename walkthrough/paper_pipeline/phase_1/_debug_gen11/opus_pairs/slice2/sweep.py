#!/usr/bin/env python3
"""⭐ THE CROSS-CLAUSE SWEEP — measured gap 2.

The previous loop NAMED a licence-inheritance class, called it "mechanically
checkable; nothing checks it", and left it in 12 of 17 clauses because the loop
was per-clause with no end-of-run sweep.  This file is the thing that was
missing.  Every class any ONE clause of the slice raised is re-asked of ALL
FIVE, mechanically, from the module JSON plus the span text.

    sweep.py                 # sweeps out/*.json against spans/*.prompt_user.txt

Each check returns a list of (clause_id, where, message).  A check that fires on
a clause its own drafter passed is the DELTA the sweep exists to produce.

⚠️ These checks are SCREENS, not verdicts.  Several of them fire on correct
modules by construction (marked ANTI-RULE-ADJACENT); the sweep's job is to hand
the coordinator a short list to adjudicate by hand, not to grade.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SPANS = os.path.join(HERE, "spans")


# ----------------------------------------------------------------- loading

def load():
    mods = {}
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith(".json"):
            continue
        cid = fn[:-5]
        with open(os.path.join(OUT, fn), encoding="utf-8") as fh:
            mods[cid] = json.load(fh)
    return mods


def span_text(cid):
    with open(os.path.join(SPANS, cid + ".prompt_user.txt"),
              encoding="utf-8") as fh:
        return fh.read()


NARROW = re.compile(r"\[node narrows this span to: \"(.*?)\"\]\s*\n\nWrite the module",
                    re.S)
SOURCE = re.compile(r"SOURCE TEXT \(verbatim.*?\n(.*?)\n\nWrite the module", re.S)
ESTAB = re.compile(r"ESTABLISHES \(the one claim this module must express\):\n(.*?)\n\n",
                   re.S)
NEEDS = re.compile(r"^  - ([a-z0-9_]+):", re.M)


def narrowed(cid):
    """The text the module is licensed by: the narrowing if present, else the
    whole quoted source block.  P6 turns on this distinction."""
    t = span_text(cid)
    m = NARROW.search(t)
    if m:
        return m.group(1)
    m = SOURCE.search(t)
    return m.group(1) if m else t


def needs_names(cid):
    """The NEEDS names, which `requires` is CONTRACT-REQUIRED to carry even
    unused.  Anything in `requires` that is NOT here was coined by the
    translator and is fair game for the unused-name check (P9, as corrected)."""
    t = span_text(cid)
    block = t.split("NEEDS --", 1)
    if len(block) < 2:
        return set()
    block = block[1].split("CITATION:", 1)[0]
    return set(NEEDS.findall(block))


# ------------------------------------------------------------- primitives

WORD = re.compile(r"[a-z_][a-z0-9_]*")


def bodies(mod):
    """Every body string in the module, with a label for where it came from."""
    out = []
    for a in mod.get("asserts") or []:
        if a.get("body"):
            out.append((f"asserts:{a.get('act')}", a["body"]))
    for o in mod.get("ontology") or []:
        if o.get("body"):
            out.append((f"ontology:{o.get('atom')}", o["body"]))
    for b in mod.get("beats") or []:
        if b.get("body"):
            out.append((f"beats:{b.get('winner')}", b["body"]))
    return out


def declared(mod):
    d = set()
    for c in mod.get("concepts") or []:
        if c.get("name"):
            d.add(c["name"])
    for o in mod.get("ontology") or []:
        m = WORD.match((o.get("atom") or "").strip())
        if m:
            d.add(m.group(0))
    return d


def ref_names(mod, key):
    got = set()
    for r in mod.get(key) or []:
        n = r if isinstance(r, str) else (r.get("name") or r.get("predicate") or "")
        got.add(re.sub(r"/\d+$", "", n.strip()))
    return {g for g in got if g}


def functors(text):
    return set(WORD.findall(text or ""))


# ------------------------------------------------------------------ checks

def c_asserts_zero(mods, _):
    """A translated module with zero asserts governs nothing.  Legitimate for a
    pure definition; a finding for anything whose span states a norm."""
    hits = []
    for cid, m in mods.items():
        if m.get("outcome") != "abstained" and not (m.get("asserts") or []):
            hits.append((cid, "asserts", "translated but zero asserts — "
                                         "confirm the span states no norm"))
    return hits


def c_licence_inheritance(mods, _):
    """⭐ THE CLASS THE PREVIOUS LOOP NAMED AND NEVER CHECKED.

    00_task.md: 'A conclusion inherits the weakest licence in its derivation.'
    So a `textual` conclusion whose body rests on a name this module does NOT
    establish textually is mis-marked.  Screened here as: a fact marked
    `textual` whose body references a `requires` name (established elsewhere,
    licence unknown to this module) or an `assumed`/`world` ontology name."""
    hits = []
    order = {"textual": 0, "assumed": 1, "world": 2}
    for cid, m in mods.items():
        weak = {}
        for o in m.get("ontology") or []:
            lic = o.get("licence")
            mm = WORD.match((o.get("atom") or "").strip())
            if mm and lic in ("assumed", "world"):
                weak[mm.group(0)] = lic
        req = ref_names(m, "requires")
        for where, body in bodies(m):
            src = None
            for a in (m.get("asserts") or []) + (m.get("ontology") or []) + \
                     (m.get("beats") or []):
                if a.get("body") == body:
                    src = a
                    break
            lic = (src or {}).get("licence")
            if lic is None:
                continue
            used = functors(body)
            for n in sorted(used & req):
                if order.get(lic, 0) == 0:
                    hits.append((cid, where,
                                 f"`{lic}` conclusion rests on borrowed `{n}` "
                                 f"— borrowed licence is unknown to this module"))
            for n in sorted(used & set(weak)):
                if order.get(lic, 0) < order[weak[n]]:
                    hits.append((cid, where,
                                 f"`{lic}` conclusion rests on `{weak[n]}` fact "
                                 f"`{n}` — weakest licence not inherited"))
    return hits


def c_inert_ground_atom(mods, _):
    """N1: will a situation fact ever unify with this atom?  A ground ontology
    atom with no variable and no body is inert for behaviour matching unless it
    is a fact ABOUT THE DOCUMENT (root_authority(section_x) and friends)."""
    hits = []
    doc = re.compile(r"authority|section|rule|heading|policy_section")
    for cid, m in mods.items():
        for o in m.get("ontology") or []:
            atom = (o.get("atom") or "").strip()
            if o.get("body"):
                continue
            if re.search(r"\b[A-Z][A-Za-z0-9_]*\b", atom):
                continue                       # has a variable
            if doc.search(atom):
                continue                       # document fact — N1 exempts it
            hits.append((cid, "ontology", f"ground atom `{atom}` — nothing in a "
                                          f"situation will unify with it"))
    return hits


def c_coined_unanchored(mods, _):
    """N10: every coined symbol must trace to a SUBSTRING of the narrowed text.
    Screens the identifier's words against the narrowed span, lowercased."""
    hits = []
    stop = {"a", "an", "the", "is", "of", "to", "and", "or", "not", "in", "by",
            "for", "with", "that", "it", "be", "this", "as", "on", "at"}
    for cid, m in mods.items():
        text = narrowed(cid).lower()
        needs = needs_names(cid)
        coined = (ref_names(m, "inputs") | declared(m)) - needs
        for n in sorted(coined):
            parts = [p for p in n.split("_") if p and p not in stop]
            miss = [p for p in parts if p[:5] not in text]
            if miss and len(miss) == len(parts):
                hits.append((cid, "coined", f"`{n}` — no word of it occurs in "
                                            f"the narrowed span"))
    return hits


def c_naf(mods, _):
    """N5: does any body rely on the ABSENCE of a fact to permit something?
    Under NAF, silence then licenses the act."""
    hits = []
    for cid, m in mods.items():
        for a in m.get("asserts") or []:
            b = a.get("body") or ""
            if re.search(r"\bnot\s+[a-z_]", b):
                hits.append((cid, f"asserts:{a.get('act')}",
                             f"`{a.get('status')}` body uses negation-as-failure: "
                             f"{b!r}"))
    return hits


def c_tautology(mods, _):
    """P8: does any rule's head appear in its own body?
    ⚠️ ANTI-RULE-ADJACENT — `forbid X(R) :- X(R)` is SCHEMA-FORCED for an
    unconditional prohibition over a variable act.  Reported for adjudication,
    never as a defect."""
    hits = []
    for cid, m in mods.items():
        for a in m.get("asserts") or []:
            act = (a.get("act") or "").strip()
            mm = WORD.match(act)
            if mm and re.search(rf"\b{mm.group(0)}\b", a.get("body") or ""):
                hits.append((cid, f"asserts:{act}",
                             "head functor recurs in its own body "
                             "(ANTI-RULE: may be the schema-forced binder)"))
    return hits


def c_gloss_restates_name(mods, _):
    """10_output_format.md: a gloss that merely restates the name is rejected.
    Screen: does the gloss add any content word the name does not already
    contain?"""
    hits = []
    for cid, m in mods.items():
        for c in m.get("concepts") or []:
            name, gloss = c.get("name") or "", (c.get("gloss") or "").lower()
            nw = {w for w in name.split("_") if len(w) > 3}
            gw = {w for w in re.findall(r"[a-z]{4,}", gloss)}
            if nw and gw and not (gw - nw):
                hits.append((cid, f"concepts:{name}",
                             f"gloss adds no word beyond the name: {gloss!r}"))
    return hits


def c_undeclared_body_name(mods, _):
    """10_output_format.md: every predicate a body references must be in
    ontology, requires or inputs.  A name in none of them is a typo or a
    dropped declaration and the rule can never fire (failure mode 3)."""
    hits = []
    kw = {"not", "true", "false"}
    for cid, m in mods.items():
        known = declared(m) | ref_names(m, "requires") | ref_names(m, "inputs")
        for where, body in bodies(m):
            for n in sorted(functors(body) - known - kw):
                if re.match(r"^[a-z][a-z0-9_]*$", n) and \
                        re.search(rf"\b{n}\s*\(", body):
                    hits.append((cid, where, f"body name `{n}` is declared "
                                             f"nowhere"))
    return hits


def c_closure_coverage(mods, _):
    """00_task.md rule 12 / 10_output_format.md: one closure entry for EVERY
    distinct functor appearing in `acts`.  An absent declaration reads as
    `cepa` silently and that reading changes what the corpus concludes."""
    hits = []
    for cid, m in mods.items():
        acts = set()
        for a in m.get("acts") or []:
            t = a if isinstance(a, str) else (a.get("term") or a.get("act") or "")
            mm = WORD.match(t.strip())
            if mm:
                acts.add(mm.group(0))
        cov = set()
        for c in m.get("closure") or []:
            n = c if isinstance(c, str) else (c.get("act_class") or "")
            cov.add(re.sub(r"/\d+$", "", n.strip()))
        for a in sorted(acts - cov):
            hits.append((cid, "closure", f"act class `{a}` has no closure entry"))
    return hits


def c_polarity(mods, _):
    """P1: `status` and `read_back` must not disagree.  Screen: a read_back
    containing a negation under a `prefer`/`oblige`, or lacking one under a
    `forbid`."""
    hits = []
    # A read-back that BANS the act.  `forbidden` counts: the screen is asking
    # whether the sentence a reviewer sees pushes the same way the status does,
    # not whether it contains a grammatical negation.
    ban = re.compile(r"\b(forbidden|prohibit\w*|must not|may not|never|not "
                     r"permitted|refrain|barred|disallow\w*)\b", re.I)
    # A read-back that WANTS the act.
    want = re.compile(r"\b(must|should|preferred|prefers?|strives?|is permitted|"
                      r"may|able to|encourag\w*|aims? to)\b", re.I)
    for cid, m in mods.items():
        for a in m.get("asserts") or []:
            st, rb = a.get("status"), a.get("read_back") or ""
            if st in ("prefer", "oblige", "permit") and ban.search(rb):
                hits.append((cid, f"asserts:{a.get('act')}",
                             f"`{st}` (wants the act) with a BANNING read_back: "
                             f"{rb!r}"))
            if st == "forbid" and not ban.search(rb):
                hits.append((cid, f"asserts:{a.get('act')}",
                             f"`forbid` whose read_back never bans the act "
                             f"{'and reads as wanting it ' if want.search(rb) else ''}"
                             f"— {rb!r}"))
    return hits


def c_claims_unencoded(mods, _):
    """P3, the highest-value screen: a `claims` entry encoded nowhere is the
    fingerprint of a dropped obligation.  Screen on content-word overlap
    between each claim and the union of act terms + read_backs."""
    hits = []
    stop = {"the", "a", "an", "is", "are", "to", "of", "and", "or", "not", "in",
            "by", "for", "with", "that", "this", "must", "should", "may", "it",
            "assistant", "clause", "node", "when", "if", "be", "on", "as"}
    for cid, m in mods.items():
        pool = " ".join(
            [(a.get("act") or "") + " " + (a.get("read_back") or "")
             for a in m.get("asserts") or []] +
            [(o.get("atom") or "") + " " + (o.get("gloss") or "")
             for o in m.get("ontology") or []] +
            [(c.get("name") or "") + " " + (c.get("gloss") or "")
             for c in m.get("concepts") or []] +
            [(b.get("read_back") or "") for b in m.get("beats") or []] +
            [str(f) for f in m.get("forbid_body") or []]).lower()
        pw = set(re.findall(r"[a-z]{4,}", pool))
        for cl in m.get("claims") or []:
            t = cl if isinstance(cl, str) else (cl.get("text") or str(cl))
            cw = {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in stop}
            if not cw:
                continue
            hit = len(cw & pw) / len(cw)
            if hit < 0.34:
                hits.append((cid, "claims",
                             f"claim carried by nothing formal ({hit:.0%} word "
                             f"overlap): {t[:90]!r}"))
    return hits


def c_needs_in_requires(mods, _):
    """The node contract: every NEEDS name must appear in `requires`, spelled
    exactly, and never in `inputs`.  Both halves are mechanical."""
    hits = []
    for cid, m in mods.items():
        if m.get("outcome") == "abstained":
            continue
        need = needs_names(cid)
        req, inp = ref_names(m, "requires"), ref_names(m, "inputs")
        for n in sorted(need - req):
            hits.append((cid, "requires", f"NEEDS name `{n}` missing from requires"))
        for n in sorted(need & inp):
            hits.append((cid, "inputs", f"NEEDS name `{n}` also in inputs — "
                                        f"the two must be disjoint"))
        for n in sorted(req & inp):
            hits.append((cid, "inputs", f"`{n}` in BOTH requires and inputs"))
    return hits


def c_requires_gloss(mods, _):
    """10_output_format.md line 66: every `requires` entry must ALSO have a
    `concepts` entry.  ⚠️ This is the BORROWED-GLOSS class — the check is here
    because the prompt demands it, and whether the prompt SHOULD is a PROMPT
    FINDING, not a translator defect."""
    hits = []
    for cid, m in mods.items():
        con = {c.get("name") for c in m.get("concepts") or []}
        for n in sorted(ref_names(m, "requires") - con):
            hits.append((cid, "requires", f"`{n}` has no concepts gloss "
                                          f"(10_output_format.md line 66)"))
    return hits


def c_borrowed_gloss_licence(mods, _):
    """⭐ RAISED BY THIS SLICE, and the sweep's clearest catch.

    `10_output_format.md` line 66 forces a `concepts` entry for every `requires`
    entry — including the NEEDS names, whose content this node does NOT state.
    So the gloss is written from the NEEDS block, not from the narrowed span,
    and the licence on it is a real choice:

      * `textual` + `cites: <this node>`  claims the narrowed span says it.
      * `assumed` + an inference naming the NEEDS block  says where it came from.

    `00_task.md`: *"Do not manufacture a citation to make a fact look textual."*
    A borrowed gloss marked `textual` is that manufactured citation, and it is
    mechanically detectable: the concept's name is a NEEDS name, its licence is
    `textual`, and it cites this node.
    """
    hits = []
    for cid, m in mods.items():
        need = needs_names(cid)
        for c in m.get("concepts") or []:
            if c.get("name") in need and c.get("licence") == "textual":
                hits.append((cid, f"concepts:{c.get('name')}",
                             "borrowed NEEDS name glossed `textual`, citing this "
                             "node for content the narrowed span never states"))
    return hits


def c_borrowed_arity_invented(mods, _):
    """N8 generalised.  The NEEDS block gives a borrowed name with NO arity.
    Whatever arity this module declares is the module's own invention, and a
    provider that chose differently mismatches silently.  Screen: a borrowed
    name declared with arity >= 2 and never used in any body — nothing in the
    module constrains the choice, and nothing downstream can check it."""
    hits = []
    for cid, m in mods.items():
        used = set()
        for _w, b in bodies(m):
            used |= functors(b)
        for c in m.get("concepts") or []:
            n = c.get("name")
            if n in needs_names(cid) and (c.get("arity") or 1) >= 2 and \
                    n not in used:
                hits.append((cid, f"concepts:{n}",
                             f"borrowed name given arity {c.get('arity')} and "
                             f"never used — the arity is uncorroborated"))
    return hits


def c_act_arg_sorts(mods, _):
    """RAISED BY THIS SLICE.  One act functor whose single argument is bound by
    bodies of DIFFERENT sorts — respect(X) with X a creator in one rule, a work
    in the next, a right in the third — reads fluently and joins nothing: the
    query side supplies one sort per variable.  Screen: same act functor, and
    the body's binding predicate for that variable differs across asserts."""
    hits = []
    for cid, m in mods.items():
        seen = {}
        for a in m.get("asserts") or []:
            act = (a.get("act") or "").strip()
            mm = re.match(r"([a-z_][a-z0-9_]*)\(([A-Z][A-Za-z0-9_]*)\)", act)
            if not mm:
                continue
            fn, var = mm.groups()
            binder = set()
            for lit in re.findall(r"([a-z_][a-z0-9_]*)\(([^)]*)\)",
                                  a.get("body") or ""):
                if var in [t.strip() for t in lit[1].split(",")]:
                    binder.add(lit[0])
            seen.setdefault(fn, []).append(frozenset(binder))
        for fn, bs in seen.items():
            # Only a hit when two rules share NO binding predicate for the act's
            # variable.  Two rules that differ by an extra manner literal
            # (`moralizing` vs `lecturing` over the same `responds(R,U)`) bind
            # the same sort and are not a collision.
            uniq = list(dict.fromkeys(bs))
            if len(uniq) > 1 and all(
                    not (a & b) for i, a in enumerate(uniq)
                    for b in uniq[i + 1:]):
                hits.append((cid, f"acts:{fn}",
                             f"one act functor bound by DISJOINT sorts across "
                             f"asserts: {[sorted(b) for b in uniq]}"))
    return hits


def c_citation_id(mods, _):
    """The node contract: every cites value must be EXACTLY this node's id."""
    hits = []
    for cid, m in mods.items():
        for grp in ("asserts", "ontology", "concepts", "beats", "defines"):
            for e in m.get(grp) or []:
                c = e.get("cites")
                for v in ([c] if isinstance(c, str) else (c or [])):
                    if v and v != cid:
                        hits.append((cid, grp, f"cites `{v}`, not this node"))
    return hits


CHECKS = [
    ("A  asserts-zero", c_asserts_zero),
    ("B  licence-inheritance ⭐", c_licence_inheritance),
    ("C  inert-ground-atom (N1)", c_inert_ground_atom),
    ("D  coined-unanchored (N10)", c_coined_unanchored),
    ("E  negation-as-failure (N5)", c_naf),
    ("F  tautology (P8, anti-rule-adjacent)", c_tautology),
    ("G  gloss-restates-name", c_gloss_restates_name),
    ("H  undeclared-body-name", c_undeclared_body_name),
    ("I  closure-coverage", c_closure_coverage),
    ("J  polarity status-vs-readback (P1)", c_polarity),
    ("K  claim-encoded-nowhere (P3) ⭐", c_claims_unencoded),
    ("L  NEEDS/requires/inputs contract", c_needs_in_requires),
    ("M  requires-without-gloss (PROMPT class)", c_requires_gloss),
    ("N  citation-id", c_citation_id),
    ("O  borrowed-gloss licence ⭐", c_borrowed_gloss_licence),
    ("P  borrowed-arity invented (N8)", c_borrowed_arity_invented),
    ("Q  act-argument sort collision", c_act_arg_sorts),
]


def main():
    mods = load()
    if not mods:
        print("no modules in out/ yet")
        return 1
    print(f"swept {len(mods)} modules: {', '.join(sorted(mods))}\n")
    total = 0
    for name, fn in CHECKS:
        try:
            hits = fn(mods, None)
        except Exception as exc:                              # noqa: BLE001
            print(f"## {name}\n   CHECK RAISED: {exc!r}\n")
            continue
        print(f"## {name} — {len(hits)} hit(s)")
        for cid, where, msg in hits:
            print(f"   {cid:20s} {where:34s} {msg}")
        total += len(hits)
        print()
    print(f"TOTAL {total} screen hits across {len(mods)} modules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
