#!/usr/bin/env python3
"""ARM E's SELECTOR — the experiment itself.

Maps one corpus row to a ranked subset of `REVIEW_LIST.md` entries, using ONLY
fields of the row.  It never reads an adjudication, a prior arm's output, or any
record of what this clause's defect turned out to be; doing so would be answer-
key leakage and would make the arm worthless.

Every trigger below is a lexical restatement of the ENTRY'S OWN stated trigger,
read off the entry text in `promptsE/entries/`.  The prior weights are the
`ORDERING.md` "distinct clauses on which this entry produced a finding" column —
an aggregate over 17 clauses, the SAME 20 numbers for every clause, so they
cannot encode which defect any particular clause had.

    selector.py --report      run over all 17 clauses, print the selection table
    selector.py --build       write promptsE/<cid>/40_review_list.md for each
"""
import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
CORPUS = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "node_corpus_all.json")
ENTRIES = os.path.join(HERE, "promptsE", "entries")

CLAUSES = [
    "l1_170_n056", "l3147_3238_n003", "l1707_1973_n006", "l3239_3382_n002",
    "l4252_4482_n016", "l171_426_n022", "l699_796_n012", "l1001_1107_n005",
    "l1368_1541_n019", "l1707_1973_n022", "l2126_2404_n016", "l2474_2554_n004",
    "l2821_3040_n017", "l3239_3382_n004", "l3596_3876_n009", "l3877_3953_n014",
    "l4252_4482_n005",
]

#: ORDERING.md, "total clauses with a finding".  E04 merges P6 (8) and N3 (4);
#: it takes P6's, since N3 "never fired alone".  E13 merges N2 (2) and P2 (0);
#: it takes 2.  These are the ONLY history this file sees, they are aggregate,
#: and they are identical for every clause.
PRIOR = {
    "E01": 12, "E02": 10, "E03": 10, "E04": 8, "E05": 8, "E06": 7, "E07": 7,
    "E08": 7, "E09": 4, "E10": 4, "E11": 3, "E12": 3, "E13": 2, "E14": 2,
    "E15": 1, "T1": 1, "T2": 0, "T3": 1,
}
ANTI = ["A1", "A2", "A3"]                       # fixed footer, never selected

_STOP = set("the a an of to and or in on for that this it is are be as by with "
            "not no if when where should must may can will would from at any "
            "their its they them we you your our".split())

_FINITE = re.compile(
    r"\b(is|are|was|were|be|been|being|has|have|had|do|does|did|should|shall|"
    r"must|may|might|can|could|will|would|need|needs|ought|honor|honors|"
    r"follow|follows|assume|assumes|apply|applies|prefer|prefers|avoid|avoids|"
    r"refuse|refuses|provide|provides|treat|treats|respond|responds|include|"
    r"includes|use|uses|make|makes|take|takes|give|gives|seek|seeks|ask|asks|"
    r"act|acts|aim|aims|allow|allows|comply|complies|defer|defers|assist|"
    r"assists|answer|answers|explain|explains|state|states|say|says)\b", re.I)


# ---------------------------------------------------------------- features


def parse_node(quote):
    """Pull the node header's blocks out of the corpus `quote` string.  The
    whole node record is one string; these are the only fields the selector is
    allowed to see."""
    def block(name, nxt):
        m = re.search(rf"(?ms)^{name}[^\n]*\n(.*?)(?=^(?:{nxt})\b|\Z)", quote)
        return (m.group(1).strip() if m else "")
    est = block("ESTABLISHES", "PROVIDES|NEEDS|CITATION|SOURCE TEXT")
    prov = block("PROVIDES", "NEEDS|CITATION|SOURCE TEXT")
    needs = block("NEEDS", "CITATION|SOURCE TEXT")
    src = block("SOURCE TEXT", "ZZZNEVER")
    m = re.search(r"\[node narrows this span to:\s*\"(.*?)\"\]\s*\Z",
                  quote, re.S)
    narrowed = m.group(1).strip() if m else re.sub(
        r"(?m)^L\d+-L\d+:\s*", "", src).strip()
    full = re.sub(r"(?m)^L\d+-L\d+:\s*", "", src)
    full = re.sub(r"\[node narrows.*?\]", "", full, flags=re.S).strip()
    return {"establishes": est,
            "provides": "" if "(none)" in prov else prov,
            "needs": "" if "(none)" in needs else needs,
            "source_full": full, "narrowed": narrowed,
            "narrows": bool(m) and narrowed != full}


def words(t):
    return [w for w in re.findall(r"[a-zA-Z_]+", t.lower())]


def content(t):
    return {w for w in words(t) if w not in _STOP and len(w) > 2}


def features(row):
    q = row["quote"]
    n = parse_node(q)
    s = n["narrowed"]
    low = s.lower()
    f = dict(n)
    f["kind"] = row.get("kind", "")
    f["words"] = len(words(s))
    f["finite"] = len(_FINITE.findall(s))
    f["paren"] = bool(re.search(r"\([^)]{3,}\)", s))
    f["commas"] = s.count(",")
    f["needs_n"] = len(re.findall(r"(?m)^\s*-\s+\w", n["needs"]))
    f["prov_n"] = len(re.findall(r"(?m)^\s*-?\s*\w+:", n["provides"])) or \
        (1 if n["provides"] else 0)
    e, sp = content(n["establishes"]), content(s)
    f["est_extra"] = len(e - sp)          # ESTABLISHES says what span does not
    f["span_extra"] = len(sp - e)         # span says what ESTABLISHES drops
    f["est_props"] = 1 + len(re.findall(r"[;.]\s+\S|\band\b", n["establishes"]))
    f["low"] = low
    return f


def has(low, *pats):
    return any(re.search(p, low) for p in pats)


# ---------------------------------------------------------------- triggers
# Each returns (bonus, reason) or (0, "").  Bonus 0 => entry NOT eligible,
# except where the entry is unconditionally eligible by its own text.


def triggers(f):
    low, t = f["low"], {}

    # E01 gloss restates its name — purely local/syntactic, applies to any
    # module that writes a gloss, i.e. all of them.  Unconditionally eligible.
    t["E01"] = (2 + (1 if f["prov_n"] or f["needs_n"] else 0),
                "always (module writes glosses)"
                + ("; PROVIDES/NEEDS present" if f["prov_n"] or f["needs_n"]
                   else ""))

    # E02 "unless" arm is a hole / cepa closure
    b, r = 0, []
    if has(low, r"\bunless\b", r"\bexcept\b", r"\bother than\b",
           r"\bdoes not apply\b", r"\bdoesn't apply\b"):
        b += 4; r.append("exception marker")
    if has(low, r"\bonly (if|when)\b", r"\bin cases where\b"):
        b += 1; r.append("restrictive scope")
    t["E02"] = (b, "; ".join(r))

    # E03 every coined symbol traces to a substring of the NARROWED text
    b, r = 0, []
    if f["narrows"]:
        b += 3; r.append("node narrows its span")
    if not f["prov_n"]:
        b += 1; r.append("PROVIDES empty -> every name is coined")
    t["E03"] = (b, "; ".join(r))

    # E04 ESTABLISHES vs narrowed span, both directions
    b, r = 0, []
    if f["est_extra"] >= 2:
        b += 2; r.append(f"ESTABLISHES adds {f['est_extra']} content words")
    if f["span_extra"] >= 4:
        b += 2; r.append(f"span has {f['span_extra']} words ESTABLISHES drops")
    if f["paren"]:
        b += 1; r.append("parenthetical in span (droppable qualifier)")
    t["E04"] = (b, "; ".join(r))

    # E05 will a situation fact ever unify with this atom?
    b, r = 0, []
    if has(low, r"\bscenario", r"\bsituation", r"\bcase[s]?\b",
           r"\bwhere there'?s\b", r"\bin which\b"):
        b += 3; r.append("names a scope/situation kind")
    if has(low, r"\bsuch as\b", r"\bfor example\b", r"\be\.g\.", r"\bkind of\b",
           r"\btype[s]? of\b"):
        b += 2; r.append("exemplifies a kind")
    if f["prov_n"]:
        b += 1; r.append("PROVIDES names to define")
    t["E05"] = (b, "; ".join(r))

    # E06 is every claim encoded, and can the rule FIRE?
    b, r = 0, []
    if f["est_props"] >= 2:
        b += 2; r.append(f"ESTABLISHES demands ~{f['est_props']} propositions")
    if f["words"] >= 35:
        b += 1; r.append("long span (multiple claims likely)")
    t["E06"] = (b, "; ".join(r))

    # E07 does the span hedge, and did you SAY SO?
    b, r = 0, []
    if has(low, r"\bby default\b", r"\bgenerally\b", r"\btypically\b",
           r"\busually\b", r"\bin general\b", r"\bordinarily\b",
           r"\bwhere possible\b", r"\bwhen possible\b", r"\btry to\b",
           r"\baim to\b", r"\bmay want\b", r"\bmight\b", r"\bsometimes\b",
           r"\boften\b", r"\bin most\b"):
        b += 4; r.append("explicit hedge lexeme")
    elif has(low, r"\bshould\b", r"\bmay\b"):
        b += 2; r.append("weak modal (should/may)")
    t["E07"] = (b, "; ".join(r))

    # E08 body widens past a qualifier / narrows an unconditional prohibition
    b, r = 0, []
    if has(low, r"\bonly\b", r"\bregardless\b", r"\bin cases where\b",
           r"\bwhen\b", r"\bif\b", r"\bunless\b", r"\bwithout\b"):
        b += 3; r.append("scope qualifier present")
    if has(low, r"\bnever\b", r"\balways\b", r"\bany\b", r"\ball\b"):
        b += 1; r.append("universal quantifier")
    t["E08"] = (b, "; ".join(r))

    # E09 argument order of an arity >= 2 relation
    b, r = 0, []
    gl = (f["needs"] + " " + f["provides"]).lower()
    if has(gl, r"\bbetween\b", r"\branking\b", r"\bhierarch", r"\brelation",
           r"\bwhich .* prevail", r"\bover\b", r"\bprecedence\b", r"\border\b"):
        b += 3; r.append("a NEEDS/PROVIDES gloss describes a relation")
    if has(low, r"\bmore than\b", r"\bprevail", r"\btakes precedence\b",
           r"\bhigher\b", r"\boutrank", r"\bover the\b", r"\bconflict"):
        b += 2; r.append("span states an ordering/conflict between two things")
    t["E09"] = (b, "; ".join(r))

    # E10 does every name you coined appear in some body?
    b, r = 0, []
    if f["prov_n"] and f["needs_n"]:
        b += 2; r.append("both PROVIDES and NEEDS present")
    if f["words"] >= 40:
        b += 1; r.append("long span -> many coinages")
    t["E10"] = (b, "; ".join(r))

    # E11 finite verbs vs propositions demanded — run BEFORE drafting
    b, r = 0, []
    if f["est_props"] > max(f["finite"], 1):
        b += 4
        r.append(f"ESTABLISHES demands ~{f['est_props']} vs "
                 f"{f['finite']} finite verbs in span")
    if has(low, r"\w+ing\b.*,", r",\s*\w+ing\b"):
        b += 1; r.append("participial adjunct")
    t["E11"] = (b, "; ".join(r))

    # E12 does a `prefer` name the act to AVOID?
    b, r = 0, []
    if has(low, r"\bavoid\b", r"\brefrain\b", r"\bnever\b", r"\bminimi[sz]e\b",
           r"\bshould not\b", r"\bshouldn't\b", r"\bdo not\b", r"\bdon't\b",
           r"\brather than\b", r"\binstead of\b", r"\bwithout\b",
           r"\bnot\b.*\b(assume|treat|provide|give|state)\b"):
        b += 4; r.append("avoidance/negative-pole verb")
    t["E12"] = (b, "; ".join(r))

    # E13 is the bearer of the main verb the assistant? strip the matrix verb
    b, r = 0, []
    if re.match(r"\s*(we|openai|this (document|section|spec)|the (spec|"
                r"document|section)|developers?|users?)\b", low):
        b += 4; r.append("subject is not the assistant/model")
    if has(low, r"\bwe'?re \w+ing\b", r"\bwe (plan|intend|believe|expect)\b",
           r"\bis intended to\b", r"\bthis section\b"):
        b += 2; r.append("matrix verb over a rule")
    t["E13"] = (b, "; ".join(r))

    # E14 "without X" — HARM entry, POLARITY-GATED.  Only eligible where its
    # measured-safe branch applies: a PERMISSION's body.  Never shipped on an
    # obligation or a default, which is where obeying it created a defect.
    b, r = 0, []
    if has(low, r"\bwithout\b", r"\bin the absence of\b", r"\bunless\b"):
        if has(low, r"\bmay\b", r"\bcan\b", r"\bis allowed\b", r"\bpermitted\b",
               r"\bis free to\b") and not has(low, r"\bmust\b", r"\bshould\b",
                                              r"\bby default\b"):
            b += 3; r.append("absence-phrase inside a PERMISSION (safe branch)")
        else:
            r.append("absence-phrase but NOT a permission -> WITHHELD "
                     "(measured-harm branch)")
    t["E14"] = (b, "; ".join(r))

    # E15 "or" in the span
    b, r = 0, []
    if re.search(r"\bor\b", low):
        b += 3; r.append("disjunction in span")
    if has(low, r"\b(refuse|avoid|decline|not)\b[^.]{0,60}\bor\b"):
        b += 1; r.append("negative-scope `or` (De Morgan case)")
    t["E15"] = (b, "; ".join(r))

    # T1 a qualifier inside a list bounds ONE item
    b, r = 0, []
    if f["paren"] and f["commas"] >= 2:
        b += 3; r.append("parenthetical inside a comma list")
    t["T1"] = (b, "; ".join(r))

    # T2 "regardless of X" -> forbid_body.  0 findings in 17: literal only.
    b, r = 0, []
    if has(low, r"\bregardless\b", r"\bno matter\b", r"\birrespective\b"):
        b += 4; r.append("literal `regardless` trigger")
    t["T2"] = (b, "; ".join(r))

    # T3 GOOD/BAD example pair.  1 finding in 17, in-sample: literal only.
    b, r = 0, []
    if re.search(r"good response|bad response|✅|❌|\bgood\b.*\bbad\b",
                 low):
        b += 5; r.append("GOOD/BAD marker present")
    t["T3"] = (b, "; ".join(r))

    return t


def select(row):
    f = features(row)
    t = triggers(f)
    k = min(4, max(2, 2 + (f["words"] >= 25) + (f["words"] >= 45)))
    scored = []
    for e, (b, r) in t.items():
        if b <= 0:
            continue
        scored.append((b + PRIOR[e] * 2.0 / 12.0, b, e, r))
    scored.sort(key=lambda x: (-x[0], -PRIOR[x[2]], x[2]))
    chosen = scored[:k]
    return f, t, k, chosen


# ---------------------------------------------------------------- assembly

PREAMBLE = """# The review list for THIS clause — run it on your own module \
before you return it

Everything below was **measured on this corpus**, by a reviewer reading finished
modules against their spans. Each entry is a **question to ask**, not a
description of a rule.

⚠️ **This is a SELECTION, not the whole list.** The full list has eighteen
entries. The ones below were picked because a feature of *this clause's own
text* matches what they test — the reason is printed under each one. Entries not
shown were judged not to apply here; do not go looking for them. **Run the ones
below hard**, on the object you are about to return, not on your intentions.

⚠️ Where an entry's remedy would violate one of the twelve rules above, **the
rule wins** — say what you found in `claims` rather than encoding a remedy the
format cannot carry.
"""

FOOTER_HEAD = """---

## ⛔ ANTI-RULES — these apply on EVERY clause. Do NOT "fix" these.
"""


def build_list(row):
    f, t, k, chosen = select(row)
    out = [PREAMBLE, "---\n"]
    for score, b, e, r in chosen:
        body = open(os.path.join(ENTRIES, f"{e}.md"), encoding="utf-8").read()
        body = body.rstrip().rstrip("-").rstrip()
        out.append(f"*(retrieved for this clause because: {r})*\n\n{body}\n")
    out.append(FOOTER_HEAD)
    for a in ANTI:
        out.append(open(os.path.join(ENTRIES, f"{a}.md"),
                        encoding="utf-8").read().rstrip() + "\n")
    return "\n".join(out).rstrip() + "\n", f, t, k, chosen


def rows():
    d = json.load(open(CORPUS, encoding="utf-8"))
    by = {r["id"]: r for r in d["clauses"]}
    return [by[c] for c in CLAUSES]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args(argv)
    table = {}
    for row in rows():
        txt, f, t, k, chosen = build_list(row)
        cid = row["id"]
        table[cid] = {
            "k": k, "words": f["words"], "finite": f["finite"],
            "narrows": f["narrows"], "prov_n": f["prov_n"],
            "needs_n": f["needs_n"], "est_props": f["est_props"],
            "selected": [e for _, _, e, _ in chosen],
            "reasons": {e: r for _, _, e, r in chosen},
            "all_triggers": {e: b for e, (b, _) in t.items() if b > 0},
            "withheld_note": {e: r for e, (b, r) in t.items() if b == 0 and r},
            "list_chars": len(txt),
            "list_sha256": hashlib.sha256(txt.encode()).hexdigest(),
        }
        if a.build:
            d = os.path.join(HERE, "promptsE", cid)
            os.makedirs(d, exist_ok=True)
            dest = os.path.join(d, "40_review_list.md")
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(txt)
    if a.report or not a.build:
        print(json.dumps(table, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
