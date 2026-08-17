#!/usr/bin/env python3
"""JOB 1 — the self-report check: which `claims` entries have no formal counterpart?

⛔ NOTHING HERE MAKES A MODEL CALL. Pure deterministic re-analysis of bytes on disk.

    ../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/dropped_content/selfreport.py

WHY A MODULE CAN SELF-REPORT ITS OWN OMISSION
─────────────────────────────────────────────
Every module carries `claims`: the distinct claims the translator says it read out
of the span, written in prose, BEFORE and INDEPENDENTLY of the formal encoding. So
`claims` is a second, uncoerced witness to the span's content — the same structural
reason `checks.polarity_mismatches` works (`status` and `read_back` are written
independently, so disagreement is evidence). If a claim has no formal counterpart,
the translator has written down what it dropped.

⚠️ The same anti-rule that guards `read_back` guards this: if anything ever renders
`claims` FROM the encoding, this check dies silently and the omission becomes
invisible. Do not template `claims`.

THE THREE RULES, stated before scoring
──────────────────────────────────────
RULE A — SYMBOL COVERAGE (per claim, one threshold).
    Take the claim's content lemmas. Take the module's SYMBOL surface: every
    identifier appearing as an act, a concept name, an ontology atom or body
    predicate, an assert act or body predicate, or a forbid_body term, split on
    `_`. A claim whose lemma coverage falls at or below the threshold is flagged.
    Justification: the encoding must NAME what the claim is about. A claim about
    a grown-up mode with no `grown_up`/`mode`/`support` symbol anywhere has no
    counterpart, whatever the prose says.
    Failure mode: high overlap is cheap. A claim can share every noun with the
    encoding and still be dropped — `l1_170_n056` C1 "models should honor user
    requests" scores full coverage against an encoding that only FORBIDS honoring.
    Rule A is blind to modality by construction.

RULE B — MODALITY PRESENCE (per module, PARAMETER-FREE).
    Read each claim's deontic marker lexically (should/must -> oblige, must not/
    forbidden/may not -> forbid, may/is permitted -> permit, prefer/dispreferred/
    minimise -> prefer). If any claim carries marker T and the module has NO
    assert with `status == T`, flag the module.
    Justification: this is the one thing Rule A cannot see, and it needs no
    threshold, so it cannot be tuned onto a single-digit denominator.
    Failure mode: it is coarse. One `oblige` anywhere in the module discharges
    every obligation-claim in it, so a module that encodes obligation A and drops
    obligation B is invisible. It also inherits every ambiguity of "should".

RULE C = A or B.

⚠️ RULE A's threshold is the only tunable parameter in this file. It is reported
as a SWEEP over the whole range on both populations, and no value is selected as
"the" setting. Fitting a cut point to 7 positives would be measuring the fit.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
for _p in (os.path.join(GEN11, "fix_matrix"), PHASE1):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RUN = os.path.join(PHASE1, "resolve_runs", "graph_v2", "translation_sample",
                   "runs", "20260815-124836-together-deepseek-v4-flash")
REF_DIR = os.path.join(GEN11, "reference_set", "modules")
DIFFS = os.path.join(GEN11, "reference_set", "diffs.json")
GOLD_KEY = os.path.join(GEN11, "stage4_golden", "key.json")
ARM0 = os.path.join(GEN11, "stage4_golden", "arms", "arm0")

TARGET_CLASSES = {"dropped-content", "dropped-obligation"}

# ── lexicon ────────────────────────────────────────────────────────────────
#: Function words. Standard English closed class; not tuned to this corpus.
STOP = set("""a an the and or but if then than that this these those of to in on
at by for with about against between into through during before after above
below from up down out off over under again further once here there when where
why how all any both each few more most other some such no nor not only own same
so too very s t can will just don should now is are was were be been being have
has had do does did doing it its as which who whom whose what
""".split())

#: ⚠️ META-VOCABULARY. Words that describe the DOCUMENT or the TRANSLATION rather
#: than the content: a claim built only from these names nothing the encoding
#: could carry. Fixed before scoring; every entry is a word about the artefact,
#: not about any subject matter in the spec.
META = set("""clause section span example illustrates demonstrates states says
marked labelled labeled shown good bad assistant response responses model models
openai user users developer developers claim claims text passage sentence
""".split())

_WORD = re.compile(r"[a-z]+")


def lemma(w):
    """Crude suffix stripping. Deliberately NOT a real stemmer: a stemmer is a
    dependency this repo does not have, and every rule here must be readable."""
    for suf in ("ations", "ation", "ings", "ing", "ies", "ers", "er", "ed",
                "es", "s", "ly", "al"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def content_lemmas(text):
    ws = _WORD.findall(text.lower())
    out = set()
    for w in ws:
        if w in STOP or w in META or len(w) < 3:
            continue
        out.add(lemma(w))
    return out


def _preds(body):
    """Predicate names and constants out of an ASP-ish body string."""
    if not body:
        return []
    return re.findall(r"[a-z_][a-z0-9_]*", body)


def symbol_surface(m):
    """Every identifier the ENCODING commits to. Symbols only, never prose."""
    toks = []
    for a in m.get("acts") or []:
        toks += _preds(a)
    for c in m.get("concepts") or []:
        toks.append(c.get("name") or "")
    for o in m.get("ontology") or []:
        toks += _preds(o.get("atom")) + _preds(o.get("body"))
    for a in m.get("asserts") or []:
        toks += [a.get("status") or ""] + _preds(a.get("act")) + _preds(a.get("body"))
    for f in m.get("forbid_body") or []:
        toks += _preds(f.get("banned")) + _preds(f.get("head"))
    for d in m.get("defines") or []:
        toks += _preds(json.dumps(d))
    for b in m.get("beats") or []:
        toks += _preds(json.dumps(b))
    for r in (m.get("requires") or []) + (m.get("inputs") or []):
        toks += _preds(r)
    for c in m.get("closure") or []:
        toks += _preds(c.get("act_class"))
    out = set()
    for t in toks:
        for part in t.split("_"):
            if len(part) >= 3:
                out.add(lemma(part))
    return out


def prose_surface(m):
    """VARIANT: symbols PLUS the encoding's own prose (glosses, read-backs).
    Reported alongside because it is the generous reading and its cost in
    recall is the interesting number."""
    s = set(symbol_surface(m))
    for c in m.get("concepts") or []:
        s |= content_lemmas(c.get("gloss") or "")
    for o in m.get("ontology") or []:
        s |= content_lemmas(o.get("gloss") or "")
    for a in m.get("asserts") or []:
        s |= content_lemmas(a.get("read_back") or "")
    return s


# ── RULE A ─────────────────────────────────────────────────────────────────
def rule_a_scores(m, surface_fn=symbol_surface):
    """[(claim, coverage)] — fraction of the claim's content lemmas present."""
    surf = surface_fn(m)
    out = []
    for c in m.get("claims") or []:
        lem = content_lemmas(c)
        # strip the leading enumerator 'c1'/'c2' if it survived tokenisation
        lem = {x for x in lem if not re.fullmatch(r"c\d+", x)}
        if not lem:
            continue
        cov = len(lem & surf) / len(lem)
        out.append((c, cov, sorted(lem - surf)))
    return out


def rule_a(m, thresh, surface_fn=symbol_surface):
    return [(c, cov, miss) for c, cov, miss in rule_a_scores(m, surface_fn)
            if cov <= thresh]


# ── RULE B ─────────────────────────────────────────────────────────────────
#: Longest-match-first: 'must not' must beat 'must', 'may not' must beat 'may'.
MODAL_MARKERS = [
    ("forbid", ["must not", "may not", "should not", "is forbidden",
                "are forbidden", "is prohibited", "shall not", "never",
                "no exception", "refuses", "must refuse", "is not permitted",
                "must avoid", "should avoid", "is barred"]),
    ("permit", ["may ", "is permitted", "are permitted", "is allowed",
                "are allowed", "can choose", "is free to"]),
    ("prefer", ["preferred", "dispreferred", "prefers", "should prefer",
                "minimi", "maximi", "favour", "favor", "better to",
                "as much as possible"]),
    ("oblige", ["must ", "should ", "is required", "are required",
                "is obliged", "needs to", "has to", "is expected to"]),
]


def claim_modality(claim):
    c = " " + claim.lower() + " "
    for status, pats in MODAL_MARKERS:
        for p in pats:
            if p in c:
                return status, p
    return None, None


def rule_b(m):
    have = {a.get("status") for a in (m.get("asserts") or [])}
    out = []
    for c in m.get("claims") or []:
        st, pat = claim_modality(c)
        if st and st not in have:
            out.append((c, st, pat))
    return out


# ── populations ────────────────────────────────────────────────────────────
def _load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def populations():
    d = _load(DIFFS)
    by_clause = {}
    for e in d["edits"]:
        by_clause.setdefault(e["clause"], []).append(e["class"])

    pos, neg = [], []
    # P-REF positives: originals of clauses carrying a dropped-* edit
    for cid, classes in sorted(by_clause.items()):
        if TARGET_CLASSES & set(classes):
            pos.append(("P-REF/pos", cid, "original",
                        _load(os.path.join(RUN, cid + ".json"))))
    # P-REF negatives (i): the corrected reference of those same clauses
    for cid, classes in sorted(by_clause.items()):
        if TARGET_CLASSES & set(classes):
            neg.append(("P-REF/neg-corrected", cid, "reference",
                        _load(os.path.join(REF_DIR, cid + ".json"))))
    # P-REF negatives (ii): the untouched-faithful clauses
    ref_ids = sorted(f[:-5] for f in os.listdir(REF_DIR) if f.endswith(".json"))
    untouched = [c for c in ref_ids if c not in by_clause]
    for cid in untouched:
        neg.append(("P-REF/neg-untouched", cid, "original",
                    _load(os.path.join(RUN, cid + ".json"))))
    # P-GOLD negatives: the 11 believed-correct bases
    bases = _load(GOLD_KEY)["bases"]
    for cid in sorted(bases):
        neg.append(("P-GOLD/neg-base", cid, "arm0",
                    _load(os.path.join(ARM0, cid + ".json"))))
    return pos, neg, by_clause, untouched, bases


# ── report ─────────────────────────────────────────────────────────────────
def main():
    pos, neg, by_clause, untouched, bases = populations()

    print("=" * 78)
    print("POPULATION OVERLAP — checked before any score is quoted")
    print("=" * 78)
    ov = sorted(set(bases) & set(untouched))
    extra = sorted(set(bases) - set(untouched))
    print(f"P-REF untouched-faithful : {len(untouched)}  {untouched}")
    print(f"P-GOLD believed-correct  : {len(bases)}")
    print(f"  shared with P-REF      : {len(ov)}  {ov}")
    print(f"  unique to P-GOLD       : {len(extra)}  {extra}")
    for cid in extra:
        print(f"     !! {cid} is labelled DEFECTIVE by P-REF: "
              f"{sorted(set(by_clause.get(cid, [])))}")

    for label, surface_fn in (("SYMBOLS ONLY", symbol_surface),
                              ("SYMBOLS + GLOSS/READ-BACK", prose_surface)):
        print()
        print("=" * 78)
        print(f"RULE A — symbol coverage sweep   [{label}]")
        print("=" * 78)
        print(f"{'thresh':>7} | {'REF pos':>8} | {'REF corr':>9} | "
              f"{'REF untch':>10} | {'GOLD base':>10}")
        for th in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80):
            row = []
            for group in ("P-REF/pos", "P-REF/neg-corrected",
                          "P-REF/neg-untouched", "P-GOLD/neg-base"):
                src = pos if group == "P-REF/pos" else neg
                items = [x for x in src if x[0] == group]
                n = sum(1 for _, _, _, m in items
                        if rule_a(m, th, surface_fn))
                row.append(f"{n}/{len(items)}")
            print(f"{th:>7.2f} | {row[0]:>8} | {row[1]:>9} | "
                  f"{row[2]:>10} | {row[3]:>10}")

    print()
    print("=" * 78)
    print("RULE A — per-claim detail on the 7 positives (SYMBOLS ONLY)")
    print("=" * 78)
    for group, cid, var, m in pos:
        print(f"\n-- {cid}  ({', '.join(sorted(set(by_clause[cid])))})")
        for c, cov, miss in sorted(rule_a_scores(m), key=lambda x: x[1]):
            print(f"   cov={cov:.2f}  {c[:88]}")
            if cov < 0.7:
                print(f"            missing: {miss}")

    print()
    print("=" * 78)
    print("RULE B — modality presence (parameter-free)")
    print("=" * 78)
    for name, src in (("POSITIVES", pos), ("NEGATIVES", neg)):
        print(f"\n{name}")
        for group, cid, var, m in src:
            hits = rule_b(m)
            mark = "FIRE" if hits else "    "
            print(f"  {mark} {group:22s} {cid:20s} "
                  f"statuses={sorted({a.get('status') for a in (m.get('asserts') or [])})}")
            for c, st, pat in hits:
                print(f"        no `{st}` assert, but claim says '{pat.strip()}': "
                      f"{c[:70]}")

    print()
    print("=" * 78)
    print("SUMMARY — recall / false-positive PAIRS (denominators are single-digit)")
    print("=" * 78)
    groups = [("P-REF/pos", pos)] + [(g, [x for x in neg if x[0] == g])
                                     for g in ("P-REF/neg-corrected",
                                               "P-REF/neg-untouched",
                                               "P-GOLD/neg-base")]
    for th in (0.30, 0.50):
        for surf_name, surf in (("sym", symbol_surface),
                                ("sym+prose", prose_surface)):
            cells = []
            for g, items in groups:
                n = sum(1 for _, _, _, m in items if rule_a(m, th, surf))
                cells.append(f"{g.split('/')[-1]}={n}/{len(items)}")
            print(f"RULE A  th<={th:.2f} [{surf_name:9s}]  " + "  ".join(cells))
    cells = []
    for g, items in groups:
        n = sum(1 for _, _, _, m in items if rule_b(m))
        cells.append(f"{g.split('/')[-1]}={n}/{len(items)}")
    print("RULE B  (no threshold)          " + "  ".join(cells))
    for th in (0.30, 0.50):
        cells = []
        for g, items in groups:
            n = sum(1 for _, _, _, m in items
                    if rule_a(m, th, symbol_surface) or rule_b(m))
            cells.append(f"{g.split('/')[-1]}={n}/{len(items)}")
        print(f"RULE C  A(th<={th:.2f},sym) or B  " + "  ".join(cells))


if __name__ == "__main__":
    main()
