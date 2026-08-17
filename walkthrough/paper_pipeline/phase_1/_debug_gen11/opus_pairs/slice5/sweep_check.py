#!/usr/bin/env python3
"""Slice-5 cross-clause sweep — the MECHANICAL half.

Gap 2 measured on the previous cohort: a class NAMED late never reaches the
clauses done early, because the loop is per-clause with no end-of-run sweep.
This file is the end-of-run sweep, and every check in it is deliberately a few
lines of Python — the point of the exercise is that every high-value class we
have found so far WAS checkable in a few lines that nobody had written.

Run:
  .../semi-formal-experiment/.venv/bin/python \
      _debug_gen11/opus_pairs/slice5/sweep_check.py

Each check returns a list of (clause_id, where, message). A check that fires is
NOT automatically a defect — several classes on this corpus are contracts (see
REVIEW_LIST.md ANTI-RULES). The output is a work list for the coordinator, and
SWEEP.md records the adjudication of every firing.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
SPANS = os.path.join(HERE, "spans")

WORD = re.compile(r"[a-z_][a-z0-9_]*", re.I)


def load():
    mods = {}
    for fn in sorted(os.listdir(OUT)):
        if fn.endswith(".json"):
            cid = fn[:-5]
            mods[cid] = json.load(open(os.path.join(OUT, fn)))
    return mods


def span_text(cid):
    p = os.path.join(SPANS, cid + ".prompt_user.txt")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def narrowed(cid):
    """The text the node NARROWS its span to, if it declares one; else the
    whole SOURCE TEXT block. P6/N10 are both about THIS string, not the
    printed context around it."""
    t = span_text(cid)
    m = re.search(r"\[node narrows this span to: \"(.*?)\"\]", t, re.S)
    if m:
        return m.group(1)
    m = re.search(r"SOURCE TEXT .*?:\n(.*?)(?:\n\nCROSS-REFERENCED|\n\nWrite the module)",
                  t, re.S)
    return m.group(1) if m else t


def establishes(cid):
    m = re.search(r"ESTABLISHES \(the one claim this module must express\):\n(.*?)\n\n",
                  span_text(cid), re.S)
    return m.group(1) if m else ""


def needs_names(cid):
    m = re.search(r"NEEDS --.*?\n(.*?)\n\nCITATION", span_text(cid), re.S)
    if not m:
        return set()
    return set(re.findall(r"^\s*-\s*([a-z_][a-z0-9_]*):", m.group(1), re.M))


def provides_names(cid):
    m = re.search(r"PROVIDES \(.*?\):\n(.*?)\n\nNEEDS", span_text(cid), re.S)
    if not m:
        return set()
    return set(re.findall(r"^\s*-\s*([a-z_][a-z0-9_]*):", m.group(1), re.M))


def bodies(mod):
    out = []
    for e in mod.get("ontology") or []:
        if e.get("body"):
            out.append(("ontology:" + e.get("atom", "?"), e["body"]))
    for e in mod.get("asserts") or []:
        if e.get("body"):
            out.append(("asserts:" + e.get("act", "?"), e["body"]))
    return out


def functors(s):
    return set(re.findall(r"([a-z_][a-z0-9_]*)\s*\(", s or "")) | \
           set(re.findall(r"\b([a-z_][a-z0-9_]*)\b(?!\s*\()", s or ""))


def head_functor(term):
    m = re.match(r"\s*([a-z_][a-z0-9_]*)", term or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------- checks

def c_asserts_census(mods):
    """Not a defect check — the census gap 3 exists to make visible."""
    return [(c, "-", "asserts=%d claims=%d ontology=%d concepts=%d outcome=%s"
             % (len(m.get("asserts") or []), len(m.get("claims") or []),
                len(m.get("ontology") or []), len(m.get("concepts") or []),
                m.get("outcome")))
            for c, m in mods.items()]


def c_claims_unencoded(mods):
    """P3 — a claim in `claims` encoded nowhere is the dropped-obligation
    fingerprint. Mechanical proxy: more claims than asserts+ontology entries."""
    hits = []
    for c, m in mods.items():
        if m.get("outcome") != "translated":
            continue
        nc = len(m.get("claims") or [])
        ne = len(m.get("asserts") or []) + len(m.get("ontology") or [])
        if nc > ne:
            hits.append((c, "claims", "%d claims vs %d encoded items — check each "
                                      "claim maps to something" % (nc, ne)))
    return hits


def c_naf(mods):
    """N5 / rule 4 / failure mode #4 — negation as failure in a body makes
    SILENCE license the act."""
    hits = []
    for c, m in mods.items():
        for where, b in bodies(m):
            if re.search(r"(^|,)\s*not\s+", b):
                hits.append((c, where, "negation-as-failure in body: %s" % b))
    return hits


def c_tautology(mods):
    """P8 — head functor appears in its own body. NOTE the ANTI-RULE:
    `forbid X(R) :- X(R)` on an assert is SCHEMA-FORCED, not a defect. Only the
    ontology case is reportable, and even there it may be a legitimate
    recursive-free alternative encoding — adjudicate, do not auto-fix."""
    hits = []
    for c, m in mods.items():
        for e in m.get("ontology") or []:
            h = head_functor(e.get("atom"))
            if h and re.search(r"\b%s\s*\(" % re.escape(h), e.get("body") or ""):
                hits.append((c, "ontology:" + e["atom"],
                             "head functor recurs in own body"))
    return hits


def c_gloss_restates_name(mods):
    """10_output_format.md: 'A gloss that restates the name is rejected.'
    Mechanical proxy: every alphabetic token of the name appears in the gloss
    and the gloss is short."""
    hits = []
    for c, m in mods.items():
        for e in m.get("concepts") or []:
            n, g = e.get("name", ""), (e.get("gloss") or "").lower()
            toks = [t for t in n.split("_") if len(t) > 3]
            if toks and all(t in g for t in toks) and len(g.split()) <= 8:
                hits.append((c, "concepts:" + n, "gloss may restate the name: %r" % e.get("gloss")))
    return hits


def c_borrowed_gloss_licence(mods):
    """⭐ THE LICENCE-INHERITANCE CLASS, named by the previous loop as
    'mechanically checkable; nothing checks it' and then left in 12 of 17
    clauses. A NEEDS name is OWNED BY ANOTHER NODE. A `concepts` entry for it
    marked `textual` + `cites: <this node>` asserts that THIS node's text
    defines it — which it does not; the node text merely QUOTES the other
    node's gloss.

    ⚠️ PROMPT FINDING, not necessarily a translator defect: the production
    worked example `node_worked_example.md` does exactly this for
    `authority_levels_hierarchy` on node l527_796_n012, and
    `10_output_format.md` (the 'every requires entry must also have a concepts
    entry' rule) requires the entry to exist. See PROMPT_FINDINGS.md."""
    hits = []
    for c, m in mods.items():
        needs = needs_names(c)
        for e in m.get("concepts") or []:
            if e.get("name") in needs and e.get("licence") == "textual":
                hits.append((c, "concepts:" + e["name"],
                             "NEEDS name (owned elsewhere) glossed licence=textual cites=%s"
                             % e.get("cites")))
    return hits


def c_needs_in_requires(mods):
    """Contract 2 of node_worked_example.md: EVERY NEEDS name must appear in
    `requires`, and must NEVER be defined in this module's `ontology`."""
    hits = []
    for c, m in mods.items():
        if m.get("outcome") != "translated":
            continue
        req = {r.split("/")[0] for r in (m.get("requires") or [])}
        onto = {head_functor(e.get("atom")) for e in (m.get("ontology") or [])}
        inp = {r.split("/")[0] for r in (m.get("inputs") or [])}
        for n in needs_names(c):
            if n not in req:
                hits.append((c, "requires", "NEEDS name %r missing from requires" % n))
            if n in onto:
                hits.append((c, "ontology", "NEEDS name %r defined here — owned by another node" % n))
            if n in inp:
                hits.append((c, "inputs", "NEEDS name %r also in inputs — must be disjoint" % n))
    return hits


def c_provides_delivered(mods):
    """The mirror of the above: a PROVIDES name is a promise to the rest of the
    graph. If this module defines it nowhere, other nodes `require` a name that
    nothing in the corpus supplies."""
    hits = []
    for c, m in mods.items():
        if m.get("outcome") != "translated":
            continue
        defined = {head_functor(e.get("atom")) for e in (m.get("ontology") or [])}
        defined |= {e.get("name") for e in (m.get("concepts") or [])}
        for n in provides_names(c):
            if n not in defined:
                hits.append((c, "PROVIDES", "promised name %r is defined nowhere in this module" % n))
    return hits


def c_coined_unused(mods):
    """P9 as CORRECTED: only names YOU COINED must be used. A NEEDS name in
    `requires` and unused is CONTRACT-REQUIRED and must be left alone.

    ⭐ SECOND EXEMPTION, added during this slice from `l1001_1107_n006`'s
    lessons C1 — and it is the sweep catching its own defect. P9 was corrected
    ONCE already because its original form fired on every correct node module.
    The CORRECTED form still fires on a correct module by a route the
    correction did not cover: a `PROVIDES` name is delivered as an `ontology`
    entry and is a document-side object OTHER nodes reference, not a condition
    this node tests, so it legitimately appears in no body. Exempting it is
    narrow — the exemption is 'the name is in this node's own PROVIDES block',
    not 'any unused ontology atom is fine', which would give back the
    dropped-content detector P9 exists to be."""
    hits = []
    for c, m in mods.items():
        needs = needs_names(c) | provides_names(c)
        used = set()
        for _, b in bodies(m):
            used |= functors(b)
        for e in m.get("asserts") or []:
            used |= functors(e.get("act"))
        for e in m.get("ontology") or []:
            used |= functors(e.get("atom"))
        coined = {e["name"] for e in (m.get("concepts") or []) if e.get("name") not in needs}
        coined |= {r.split("/")[0] for r in (m.get("inputs") or [])}
        for n in sorted(coined - used):
            hits.append((c, "unused", "coined name %r appears in no body/atom/act" % n))
    return hits


def c_coined_anchored(mods):
    """N10 — every coined symbol must trace to a SUBSTRING of the NARROWED
    text. Weak lexical proxy: at least one token of the name (len>3) occurs in
    the narrowed text OR in ESTABLISHES OR in a NEEDS gloss. Firing is a
    prompt to justify, not a defect."""
    hits = []
    for c, m in mods.items():
        hay = (narrowed(c) + " " + establishes(c) + " " + span_text(c)).lower()
        needs = needs_names(c)
        for e in m.get("concepts") or []:
            n = e.get("name", "")
            if n in needs:
                continue
            toks = [t for t in n.split("_") if len(t) > 3]
            if toks and not any(t[:5] in hay for t in toks):
                hits.append((c, "concepts:" + n, "no token of coined name occurs in span text"))
    return hits


def c_closure_declared(mods):
    """10_output_format.md: one `closure` entry for EVERY distinct functor in
    `acts`. An absent declaration reads as `cepa` SILENTLY."""
    hits = []
    for c, m in mods.items():
        acts = {head_functor(a) for a in (m.get("acts") or [])}
        acts.discard(None)
        decl = {e.get("act_class") for e in (m.get("closure") or [])}
        for a in sorted(acts - decl):
            hits.append((c, "closure", "act class %r governed with no closure declaration" % a))
        for a in sorted(decl - acts):
            hits.append((c, "closure", "closure declared for %r which is in no act" % a))
    return hits


def c_undeclared_body_names(mods):
    """10_output_format.md: every predicate a body references must be in
    ontology, requires or inputs — 'an undeclared name cannot be told apart
    from a typo'."""
    hits = []
    for c, m in mods.items():
        declared = {head_functor(e.get("atom")) for e in (m.get("ontology") or [])}
        declared |= {r.split("/")[0] for r in (m.get("requires") or [])}
        declared |= {r.split("/")[0] for r in (m.get("inputs") or [])}
        declared |= {e.get("name") for e in (m.get("concepts") or [])}
        declared.discard(None)
        for where, b in bodies(m):
            for f in re.findall(r"([a-z_][a-z0-9_]*)\s*\(", b):
                if f not in declared:
                    hits.append((c, where, "body name %r declared nowhere" % f))
    return hits


def c_readback_slots(mods):
    """N slots, N arguments — and the ANTI-RULE that read_back and status are
    written independently on purpose. This only checks the arithmetic."""
    hits = []
    for c, m in mods.items():
        for key in ("asserts", "beats"):
            for e in m.get(key) or []:
                rb = e.get("read_back") or ""
                ns = len(e.get("read_back_slots") or [])
                if rb.count("%") != ns:
                    hits.append((c, key, "%d %% markers vs %d slots: %r"
                                 % (rb.count("%"), ns, rb)))
    return hits


def c_polarity_smell(mods):
    """P1 — `status` has no negative pole, so 'avoid X' reliably becomes
    `prefer X` with a read-back that negates it. Mechanical proxy: a read_back
    containing a negation word on a `prefer`/`permit`/`oblige` assert."""
    NEG = re.compile(r"\b(not|never|avoid|refrain|must not|should not|no longer|without)\b", re.I)
    hits = []
    for c, m in mods.items():
        for e in m.get("asserts") or []:
            if e.get("status") in ("prefer", "permit", "oblige") and NEG.search(e.get("read_back") or ""):
                hits.append((c, "asserts:" + str(e.get("act")),
                             "status=%s but read_back is negative: %r"
                             % (e["status"], e.get("read_back"))))
    return hits


def c_good_bad_poles(mods):
    """P10 — if the span is a GOOD/BAD pair, the two arms must differ in
    `status` or in act. Fires only on spans that actually contain both."""
    hits = []
    for c, m in mods.items():
        t = span_text(c)
        if "<!-- GOOD" not in t and "GOOD -->" not in t:
            continue
        seen = {}
        for e in m.get("asserts") or []:
            k = (e.get("status"), e.get("act"))
            seen[k] = seen.get(k, 0) + 1
        dupes = [k for k, v in seen.items() if v > 1]
        hits.append((c, "GOOD/BAD span",
                     "span carries GOOD/BAD poles; assert (status,act) pairs=%s%s"
                     % (sorted(seen), " DUPLICATED:%s" % dupes if dupes else "")))
    return hits


def c_abstention_frame(mods):
    """⭐ GAP 1 — the frame is never audited. 00_task.md lists FOUR abstention
    triggers; a span headed `**Example**` or starting with a markdown heading
    fires two of them. This does not decide the question — it makes the
    question IMPOSSIBLE TO LEAVE UNASKED, which is the whole finding."""
    hits = []
    for c, m in mods.items():
        n = narrowed(c).strip()
        t = span_text(c)
        trig = []
        if re.match(r"#{1,6}\s", n):
            trig.append("it is a section heading")
        if "**Example**" in t or re.search(r"\bExample\b\s*:", t):
            trig.append("it is an example")
        if not trig:
            continue
        notes = os.path.join(OUT, c + ".notes.md")
        body = open(notes, encoding="utf-8").read().lower() if os.path.exists(notes) else ""
        answered = "abstain" in body
        hits.append((c, "abstention", "triggers present: %s | outcome=%s | "
                                      "notes mention abstention: %s"
                     % ("; ".join(trig), m.get("outcome"), answered)))
    return hits


def c_intra_slice_linkage(mods):
    """⭐ SLICE-5-SPECIFIC, and the reason this slice can measure something the
    per-clause loop structurally cannot. The deterministic selection happened to
    put TWO provider/consumer pairs inside one slice:

        l1108_1367_n013  PROVIDES user_authority   ->  l1108_1367_n008 NEEDS it
        l1001_1107_n006  PROVIDES privacy_protection_rule -> l1001_1107_n011 NEEDS it

    Failure mode #9 ('same name, different meanings — they link cleanly and are
    wrong') and review-list N8 ('a borrowed relation of arity >= 2 has an
    ARGUMENT ORDER the gloss does not fix') are both invisible to a per-clause
    reader and both visible here in four lines.

    Reports, per shared name: the arity each side chose, and each side's gloss.
    An ARITY MISMATCH is a hard defect — the consumer's rule can never fire.
    A gloss disagreement is the softer, more interesting half."""
    hits = []
    prov, cons = {}, {}
    for c, m in mods.items():
        gl = {e.get("name"): e for e in (m.get("concepts") or [])}
        for n in provides_names(c):
            prov.setdefault(n, []).append((c, gl.get(n)))
        for n in needs_names(c):
            cons.setdefault(n, []).append((c, gl.get(n)))
    for n in sorted(set(prov) & set(cons)):
        seen = []
        for side, rows in (("PROVIDES", prov[n]), ("NEEDS", cons[n])):
            for c, e in rows:
                ar = e.get("arity") if e else None
                seen.append((c, side, ar, (e or {}).get("gloss")))
        arities = {a for _, _, a, _ in seen if a is not None}
        for c, side, ar, g in seen:
            hits.append((c, "link:" + n, "%s arity=%s gloss=%r" % (side, ar, g)))
        if len(arities) > 1:
            hits.append(("<slice>", "link:" + n,
                         "⛔ ARITY MISMATCH across the slice: %s — the consumer's "
                         "rule can never fire" % sorted(arities)))
    return hits


def c_heading_attribute_block(mods):
    """From `l1108_1367_n013` lessons C1 — folded back across the slice, which
    is the point of the sweep. `00_task.md` names "it is a section heading" as
    the FIRST abstention trigger, and the reflex answer on a `####` line is
    abstain. What separates the two heading cases is NOT the heading: it is
    whether the line carries an inline attribute block `{#anchor key=value}`.
    A heading WITH one asserts a fact about the DOCUMENT and must be recorded
    in `ontology`; a bare title asserts nothing.

    Flags both arms:
      * attribute block present and outcome == abstained  -> content lost
      * bare `####` title, translated, and empty ontology  -> nothing recorded
    """
    hits = []
    for c, m in mods.items():
        n = narrowed(c).strip()
        if not re.match(r"#{1,6}\s", n):
            continue
        has_attr = bool(re.search(r"\{#\w+[^}]*=", n))
        if has_attr and m.get("outcome") == "abstained":
            hits.append((c, "heading", "attribute block present but abstained — "
                                       "the document fact it states is lost"))
        elif not has_attr and m.get("outcome") == "translated" and not (m.get("ontology") or []):
            hits.append((c, "heading", "bare title translated with empty ontology — "
                                       "records nothing"))
        else:
            hits.append((c, "heading", "attribute block=%s outcome=%s ontology=%d — consistent"
                         % (has_attr, m.get("outcome"), len(m.get("ontology") or []))))
    return hits


def c_provides_vs_abstain(mods):
    """From `l1108_1367_n013` lessons C2. Abstention is ALL-OR-NOTHING by
    schema (`10_output_format.md`: every list empty), so a node that abstains
    while its `PROVIDES` block is non-empty strands every consumer that carries
    the name in `requires` — a permanent dangling edge that looks downstream
    exactly like failure mode #15 (a rule waiting on an unlinked clause).
    Abstention stays available, but the stranding must be written into
    `abstain_reason` as an accepted cost."""
    hits = []
    for c, m in mods.items():
        p = provides_names(c)
        if p and m.get("outcome") == "abstained":
            named = (m.get("abstain_reason") or "")
            hits.append((c, "abstain/PROVIDES",
                         "abstained while promising %s; stranding %s in abstain_reason"
                         % (sorted(p), "NAMED" if any(n in named for n in p) else "NOT NAMED")))
    return hits


def c_bad_arm_sourcing(mods):
    """⭐ From `l1001_1107_n011` lessons L1 — folded back across the slice.

    A negatively-marked `<assistant>` arm is text the document QUOTES IN ORDER
    TO REJECT. Every existing review-list entry that reads span text — N6, P5,
    N10 — reads it without asking which arm it came from, and **N10 in
    particular would PASS a symbol anchored to a BAD-arm substring, because the
    substring is genuinely there.**

    The measured near-miss: this span's BAD arm contains *"even if they're
    public figures"*, which read as document text is a textbook N6 trigger
    (`forbid_body {permit, public_figure}`) and is the exact OPPOSITE of what
    the example teaches.

    Content words occurring in a BAD arm and NOWHERE ELSE in the span are the
    fingerprint. Flagging is a prompt to justify, not a verdict."""
    STOP = {"that", "this", "with", "from", "they", "them", "have", "been",
            "info", "information", "assistant", "user", "response", "even",
            "provide", "public", "private"}
    hits = []
    for c, m in mods.items():
        t = span_text(c)
        if "BAD" not in t:
            continue
        arms = re.split(r"<assistant>", t)
        bad = " ".join(a for a in arms[1:] if re.search(r"<!--\s*BAD", a)).lower()
        rest = (arms[0] + " ".join(a for a in arms[1:]
                                   if not re.search(r"<!--\s*BAD", a))).lower()
        if not bad.strip():
            continue
        names = {e.get("name") for e in (m.get("concepts") or [])}
        names |= {head_functor(e.get("atom")) for e in (m.get("ontology") or [])}
        names |= {f.get("banned") for f in (m.get("forbid_body") or [])}
        names.discard(None)
        for n in sorted(names):
            toks = [w for w in n.split("_") if len(w) > 3 and w not in STOP]
            only_bad = [w for w in toks if w in bad and w not in rest]
            if only_bad:
                hits.append((c, "BAD-arm:" + n,
                             "content word(s) %s occur ONLY in a BAD arm — "
                             "document text quoted to be REJECTED" % only_bad))
        if not any(h[0] == c for h in hits):
            hits.append((c, "BAD-arm", "BAD arm present; no coined name sources "
                                       "content exclusively from it — clean"))
    return hits


def c_truncated_narrowing(mods):
    """⭐ From `l1108_1367_n008` lessons C1 — folded back across the slice.

    The narrowing on that node ends at `…other principles (such as` because in
    the document the object is a bare markdown link with no visible label.
    `ESTABLISHES` completed it as "the avoid hateful content principle" with
    NOTHING marking the completion, and the NEEDS block independently handed
    over a name glossed to match — two mutually reinforcing pressures to encode
    a term the narrowed span does not contain.

    Nothing in the existing review list catches this: **N3 asks for the diff but
    assumes both texts are well-formed sentences, and P6 assumes the narrowing
    is a complete proposition.** This is a property of the document's markdown,
    so it recurs on every bare-link cross-reference in the corpus."""
    DANGLE = re.compile(r"(such as|including|e\.g\.|like|,\s*and|,\s*or|\(|\bof|\bto)\s*$", re.I)
    hits = []
    for c, m in mods.items():
        t = span_text(c)
        mm = re.search(r"\[node narrows this span to: \"(.*?)\"\]", t, re.S)
        if not mm:
            continue
        n = mm.group(1).rstrip()
        why = []
        if DANGLE.search(n):
            why.append("ends on a dangling function word")
        if n.count("(") != n.count(")"):
            why.append("unbalanced parenthesis")
        if why:
            hits.append((c, "truncation", "%s: …%r | ESTABLISHES completes it — check every "
                                          "coined name traces to the NARROWING, not the completion"
                         % ("; ".join(why), n[-46:])))
    return hits


def c_hedge_tier(mods):
    """From `l1108_1367_n008` lessons C4. `status` has no hedged pole: `forbid`
    from *should not* compiles BYTE-IDENTICALLY to `forbid` from *must not*.
    P7 covers defeasibility whose remedy is "push it into a body", but a modal
    TIER has no body to be pushed into and no `toggleable` slot — the only
    surviving trace is prose. Require that at least one `read_back` carries the
    span's own modal, and that the notes record the loss."""
    HEDGE = re.compile(r"\b(should|generally|typically|by default|ordinarily)\b", re.I)
    hits = []
    for c, m in mods.items():
        mm = HEDGE.search(narrowed(c))
        if not mm or not (m.get("asserts") or []):
            continue
        word = mm.group(1).lower()
        in_rb = any(word in (a.get("read_back") or "").lower() for a in m["asserts"])
        p = os.path.join(OUT, c + ".notes.md")
        body = open(p, encoding="utf-8").read().lower() if os.path.exists(p) else ""
        in_notes = bool(re.search(r"(should|hedg).{0,200}(must|not encodable|no hedged pole|byte-identical)",
                                  body, re.S))
        hits.append((c, "hedge:" + word,
                     "read_back carries the modal: %s | notes record the loss: %s"
                     % (in_rb, in_notes)))
    return hits


CHECKS = [
    ("census", c_asserts_census),
    ("⭐ truncated narrowing (from n008 C1)", c_truncated_narrowing),
    ("hedge tier recorded (from n008 C4)", c_hedge_tier),
    ("⭐ BAD-arm sourcing (from n011 L1)", c_bad_arm_sourcing),
    ("⭐ intra-slice linkage (n013->n008, n006->n011)", c_intra_slice_linkage),
    ("P3 claims-unencoded", c_claims_unencoded),
    ("N5 negation-as-failure", c_naf),
    ("P8 tautology (ontology only)", c_tautology),
    ("gloss restates name", c_gloss_restates_name),
    ("LICENCE-INHERITANCE on borrowed gloss", c_borrowed_gloss_licence),
    ("NEEDS contract", c_needs_in_requires),
    ("PROVIDES delivered", c_provides_delivered),
    ("P9 coined-and-unused", c_coined_unused),
    ("N10 coined-symbol anchoring", c_coined_anchored),
    ("closure completeness", c_closure_declared),
    ("undeclared body names", c_undeclared_body_names),
    ("read_back slot arithmetic", c_readback_slots),
    ("P1 polarity smell", c_polarity_smell),
    ("P10 GOOD/BAD poles", c_good_bad_poles),
    ("GAP-1 abstention frame", c_abstention_frame),
    ("heading attribute block (from n013 C1)", c_heading_attribute_block),
    ("PROVIDES vs abstain (from n013 C2)", c_provides_vs_abstain),
]


def main():
    mods = load()
    if not mods:
        sys.exit("no modules in %s" % OUT)
    print("modules:", ", ".join(sorted(mods)))
    for name, fn in CHECKS:
        hits = fn(mods)
        print("\n== %s — %d" % (name, len(hits)))
        for cid, where, msg in hits:
            print("   %-18s %-34s %s" % (cid, where, msg))


if __name__ == "__main__":
    main()
