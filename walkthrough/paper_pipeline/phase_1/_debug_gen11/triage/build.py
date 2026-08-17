"""TRIAGE — build the predictor/outcome table. Reads only; writes only triage/*.json.

Re-run:
  ../../../semi-formal-experiment/.venv/bin/python _debug_gen11/triage/build.py
from walkthrough/paper_pipeline/phase_1/.

Every predictor is defined in PREREG.md §3 and every outcome in PREREG.md §2.
Nothing here is fitted, thresholded or tuned.
"""
import sys, os, re, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(G11, "arms_review"))
import floor, measures                                              # noqa: E402

OUT = os.path.join(HERE, "table.json")

# ---------------------------------------------------------------- span parsing

NARROW_RE = re.compile(r"\[node narrows this span to:\s*(.*?)\]\s*$", re.S)
SRC_RE = re.compile(r"^SOURCE TEXT \(.*?\):\s*(.*)$", re.S | re.M)
NEEDS_RE = re.compile(r"^NEEDS --.*?:\s*\n(.*?)(?=\n[A-Z]{4,}[^\n]*:|\Z)", re.S | re.M)
NEEDS_ITEM_RE = re.compile(r"^\s+-\s+([A-Za-z_][A-Za-z0-9_]*):", re.M)
ESTAB_RE = re.compile(r"^ESTABLISHES \(.*?\):\s*\n(.*?)(?=\n\n)", re.S | re.M)


def span_parts(quote):
    """(narrowed_span_text, full_source_text, [needs names])."""
    m = SRC_RE.search(quote)
    src = m.group(1).strip() if m else ""
    n = NARROW_RE.search(src)
    narrowed = n.group(1).strip() if n else src
    if n:                                     # drop the narrowing note from src
        src = src[: n.start()].strip()
    nb = NEEDS_RE.search(quote)
    needs = NEEDS_ITEM_RE.findall(nb.group(1)) if nb else []
    if nb and "(none)" in nb.group(1):
        needs = []
    return narrowed, src, needs


# strip footnote markers and md links so the lexicons see prose
CLEAN = [(re.compile(r"\[\^[a-z0-9]+\]"), ""),
         (re.compile(r"\(see \[[^\]]*\]\([^)]*\)\)"), ""),
         (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
         (re.compile(r"\s+"), " ")]


def clean(t):
    for rx, rep in CLEAN:
        t = rx.sub(rep, t)
    return t.strip()


MODALS = ["should not", "should", "must not", "must", "may not", "may", "cannot",
          "can", "is expected to", "is required to", "needs to", "ought to",
          "shouldn't", "won't", "will not"]
CONJ = [", and ", ", or ", " and then ", "; and ", "; or "]
DISJ_RE = re.compile(r"\bor\b|\beither\b", re.I)
HEDGE = ["by default", "generally", "typically", "usually", "unless",
         "may want to", "should be willing", "in general", "normally", "tends to"]


def propload(t):
    t = clean(t).lower()
    n = 0
    scratch = t
    for m in MODALS:                    # longest-first, consume so "should not"
        c = scratch.count(m)            # is not also counted as "should"
        n += c
        scratch = scratch.replace(m, " ")
    n += sum(t.count(c) for c in CONJ)
    return n


def has_disj(t):
    return int(bool(DISJ_RE.search(clean(t))))


def has_hedge(t):
    t = clean(t).lower()
    return int(any(h in t for h in HEDGE))


# ------------------------------------------------------- licence inheritance

WEAK = {"assumed", "world"}
ATOM_HEAD = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)")
BODY_PRED = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")


def lic_inherit(m):
    """O3: entries stamped `textual` whose body rests on a predicate this same
    module declares `assumed`/`world`. PREREG.md §2 O3. Four lines of Python,
    recomputed rather than taken on trust."""
    weak = {c["name"] for c in (m.get("concepts") or [])
            if c.get("licence") in WEAK}
    hits = []
    for field in ("ontology", "asserts"):
        for e in (m.get(field) or []):
            if e.get("licence") != "textual":
                continue
            body = e.get("body") or ""
            used = set(BODY_PRED.findall(body))
            bad = sorted(used & weak)
            if bad:
                hits.append({"field": field,
                             "atom": e.get("atom") or e.get("act") or "?",
                             "rests_on": bad})
    return hits


# ------------------------------------------------------------------ outcomes

NUMBERED = re.compile(r"^\s*(\d+)\.\s+(.*)$")


def frozen_count(path):
    """O1: numbered edit lines, excluding 'Leave ...' lines. PREREG.md §2."""
    n, kept = 0, []
    for line in open(path):
        m = NUMBERED.match(line)
        if not m:
            continue
        body = m.group(2).strip()
        if body.startswith("Leave "):
            continue
        n += 1
        kept.append(body[:90])
    return n, kept


# --------------------------------------------------------- cheap-critic diff

VERDICT = re.compile(r"^\s*(E\d+)\s*:\s*(PASS|FIX)", re.M | re.I)


def entry_verdicts(path, phase):
    d = json.load(open(path))
    for c in d["calls"]:
        if c["phase"] == phase:
            v = {k.upper(): w.upper() for k, w in VERDICT.findall(c["raw"])}
            if v:
                return v
    return {}


# --------------------------------------------------------------------- build

def main():
    loop = os.path.join(G11, "ds_opus_loop", "out")
    conv = floor.modules_for("ds_opus_loop")
    ids = sorted(conv)

    rows = {}
    for cid in ids:
        quote = floor.BYID[cid]["quote"]
        narrowed, src, needs = span_parts(quote)
        t1p = os.path.join(loop, cid + ".turn1.raw.json")
        t1 = json.load(open(t1p)) if os.path.exists(t1p) else None

        r = {"clause_id": cid}

        # ---- predictors (PREREG §3)
        r["BORROWED"] = len(needs)                                  # P2
        r["PROPLOAD"] = propload(narrowed)                          # P4
        r["DISJ"] = has_disj(narrowed)                              # P5
        r["HEDGE"] = has_hedge(narrowed)                            # P6
        r["span_chars"] = len(clean(narrowed))                      # length control
        r["needs_names"] = needs

        if t1:                                                      # P3
            f = floor.floor(t1, cid)
            r["FLOORDIRTY_T1"] = int(not (f["outcome"] == "translated"
                                          and not f["breaches"]
                                          and not f["errors"]))
            r["T1_ERRORS"] = len(f["errors"])
            r["T1_BREACHES"] = len(f["breaches"])
            r["T1_ASSERTS"] = len(t1.get("asserts") or [])          # length control
            r["T1_ENTRIES"] = sum(len(t1.get(k) or []) for k in
                                  ("concepts", "ontology", "asserts", "acts",
                                   "claims", "closure"))
            r["T1_SELFCITE"] = len(measures.selfcited(t1, cid))
            r["T1_LICINH"] = len(lic_inherit(t1))
        else:
            r["FLOORDIRTY_T1"] = None

        # ---- outcomes
        fbs = sorted(glob.glob(os.path.join(loop, cid + ".feedback_*.md")),
                     key=lambda p: int(re.search(r"feedback_(\d+)", p).group(1)))
        r["TURNS"] = len(fbs)                                       # O2
        r["FB_CHARS"] = sum(len(open(p).read()) for p in fbs)       # O1b (amendment A1)
        r["FB1_CHARS"] = len(open(fbs[0]).read()) if fbs else 0     # O1a
        if fbs:
            n, kept = frozen_count(fbs[0])
            txt = open(fbs[0]).read()
            # which of the three formats did the critic use? (amendment A1)
            r["FB1_FMT"] = (1 if n else
                            3 if "failed these checks" in txt else 2)
            r["FROZEN_FMT1"] = n if r["FB1_FMT"] == 1 else None     # format-restricted
            r["frozen_lines"] = kept
            r["FB1_ERRBLOCKS"] = txt.count("[error/")
        else:
            r["FB1_FMT"] = r["FROZEN_FMT1"] = None

        r["CONV_LICINH"] = len(lic_inherit(conv[cid]))              # O3
        r["CONV_LICINH_DETAIL"] = lic_inherit(conv[cid])
        r["CONV_SELFCITE"] = len(measures.selfcited(conv[cid], cid))  # O4
        fc = floor.floor(conv[cid], cid)
        r["FLOORDIRTY_CONV"] = int(not (fc["outcome"] == "translated"
                                        and not fc["breaches"]
                                        and not fc["errors"]))      # O5
        rows[cid] = r

    # ---- P1 DISAGREE, on the clauses both cheap arms completed
    dpaths = {os.path.basename(p).split(".")[0]: p
              for p in glob.glob(os.path.join(G11, "selfreview_arm", "out",
                                              "*.armd.json"))}
    epaths = {os.path.basename(p).split(".")[0]: p
              for p in glob.glob(os.path.join(G11, "ds_critic_arm", "out",
                                              "*.arme.json"))}
    both = sorted(set(dpaths) & set(epaths))
    for cid in ids:
        rows[cid]["DISAGREE"] = None
        rows[cid]["D_FIX"] = rows[cid]["E_FIX"] = None
    pair = {}
    for cid in both:
        d = entry_verdicts(dpaths[cid], "identify")
        e = entry_verdicts(epaths[cid], "critic")
        shared = sorted(set(d) & set(e), key=lambda k: int(k[1:]))
        if not shared:
            continue
        dis = [k for k in shared if d[k] != e[k]]
        pair[cid] = {"n_entries": len(shared), "disagree": len(dis),
                     "which": dis,
                     "d_fix": sum(v == "FIX" for v in d.values()),
                     "e_fix": sum(v == "FIX" for v in e.values())}
        if cid in rows:
            rows[cid]["DISAGREE"] = len(dis)
            rows[cid]["DISAGREE_FRAC"] = round(len(dis) / len(shared), 3)
            rows[cid]["D_FIX"] = pair[cid]["d_fix"]
            rows[cid]["E_FIX"] = pair[cid]["e_fix"]

    # ---- O6, Tier 2: independent review revised CONTENT verdict.
    # Transcribed verbatim from independent_review/01_verdicts.md, section
    # "REVISION after opening the critic's turns.md". ADJUDICATED, not measured.
    IREV = {
        "l1_170_n056": "CORRECT", "l1368_1541_n019": "CORRECT",
        "l1707_1973_n022": "CORRECT", "l171_426_n022": "CORRECT",
        "l2474_2554_n004": "CORRECT", "l3147_3238_n003": "CORRECT",
        "l3239_3382_n002": "CORRECT", "l3239_3382_n004": "CORRECT",
        "l4252_4482_n016": "CORRECT", "l699_796_n012": "CORRECT",
        "l1707_1973_n006": "DEFECTIVE", "l2821_3040_n017": "DEFECTIVE",
        "l4252_4482_n005": "DEFECTIVE",
        "l1001_1107_n005": "UNSURE", "l2126_2404_n016": "UNSURE",
        "l3596_3876_n009": "UNSURE", "l3877_3953_n014": "UNSURE",
    }
    for cid in ids:
        v = IREV.get(cid)
        rows[cid]["IREV"] = v
        rows[cid]["IREV_NOTCORRECT"] = None if v is None else int(v != "CORRECT")

    json.dump({"rows": rows, "pairs": pair, "both_arms": both},
              open(OUT, "w"), indent=1)
    print(f"wrote {OUT}: {len(rows)} clauses, {len(pair)} with DISAGREE")
    assert set(IREV) == set(ids), set(IREV) ^ set(ids)
    print("IREV keys match the loop's clause set: True")


if __name__ == "__main__":
    main()
