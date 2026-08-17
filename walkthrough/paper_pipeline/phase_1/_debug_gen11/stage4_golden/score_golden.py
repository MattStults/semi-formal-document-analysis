#!/usr/bin/env python3
"""Score one or more judges against the golden set — the per-class DETECTION
PROFILE, and the per-judge precision that goes with it.

    ../../../../semi-formal-experiment/.venv/bin/python \
        _debug_gen11/stage4_golden/score_golden.py \
            --judge deepseek=out_deepseek --judge sonnet=out_sonnet

⛔ ZERO SPEND. It reads stored replies off disk and has no client seam.

⭐ IT SCORES THE RAW REPLIES, NOT THE REPORTS, AND THAT IS THE WHOLE POINT.
`seats.judge` does a bare `json.loads` on the reply. A parity run found ALL 20
`claude-sonnet-4-5` replies wrapped in a ```json markdown fence, so `judge`
refused every one of them — a judge that reads perfectly well would score 0%
detection and 0% false positives, and would look like a judge that said
nothing rather than one the instrument could not hear. Scoring the reports
alone can therefore only ever measure DeepSeek.

So this file re-adjudicates from `raw/<clause>.<seat>.json`, through ONE
normalisation applied IDENTICALLY TO EVERY JUDGE — it is a no-op on DeepSeek —
so that no judge is advantaged or penalised for an output habit rather than
for its judgement. Every normalisation that fires is COUNTED and printed, so
the reader can see how much of a judge's score depended on it.

⛔ `seats.py` IS NOT TOUCHED AND REMAINS UNFIXED. Another change is pending
there and it needs its own reviewed cycle. The normalisation lives here, in
the scoring layer, and the fact that the production seam still cannot hear a
fenced reply is a live finding, not something this file has repaired.

⛔ THE FAILURE MODE THIS FILE IS DESIGNED AGAINST is `mutate_seats.py`'s: an
instrument that once reported *`83 mutants applied, 0 survivor(s)`, exit 0,
against a RED test suite* because it could not tell **killed** from **never
ran**. The counterpart lie here would be scoring a judge that refused, errored
or answered `unclear` as though it had passed or failed. Every item lands in
exactly ONE of six statuses and NONE is folded into another:

    detected            a DEFECT verdict at the planted site
    missed              a PASS verdict at the planted site
    unclear-at-site     the seat answered `unclear` there. NOT a detection and
                        NOT a miss — it is its own answer
    seat-refused        the reply could not be adjudicated even after
                        normalisation, or the seat is missing
    site-absent         the site is not in that seat's denominator; the seat
                        was never asked
    not-run             no stored reply for this clause and seat

A rate is printed only as `detected / (detected + missed + unclear-at-site)`,
with the other three counts beside it, every time.

THREE STRATA, SCORED SEPARATELY:

  MUTANTS          one planted defect each. Recall, per class, per seat.
  CONTROLS         the same 11 modules unmutated. Any defect verdict is a
                   false positive against the only independent read we have.
  BORROW CONTROLS  unmutated items that correctly use a concept the node's
                   own NEEDS block told the translator to borrow. Seat 4c is
                   never shown `PROVIDES`, so it flags these BY DESIGN — this
                   stratum turns that design blindness into a precision
                   number instead of an argument.

⚠️ 4a IS ADVISORY (the author grading itself) and never enters a headline.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
KEY = os.path.join(HERE, "key.json")

#: `stage4_driver.DEFECT_VERDICTS`, restated rather than imported so this
#: scorer does not drag the driver's import chain in. `_check_contract()`
#: FAILS if the two ever diverge — two copies drift and it is always the copy.
DEFECT_VERDICTS = ("unfaithful", "unlicensed", "not-conveyed", "not-as-meant")
PASS_VERDICTS = ("faithful", "licensed", "covered", "as-meant")
SEATS = ("4a", "4b", "4c", "4d")
ADVISORY = "4a"
STATUSES = ("detected", "missed", "unclear-at-site", "seat-refused",
            "site-absent", "not-run")


class ScoreError(RuntimeError):
    pass


def _check_contract():
    path = os.path.join(PHASE1, "_debug_gen11", "stage4_baseline",
                        "stage4_driver.py")
    if not os.path.isfile(path):
        return
    src = open(path, encoding="utf-8").read()
    missing = [v for v in DEFECT_VERDICTS if f'"{v}"' not in src]
    if missing:
        raise ScoreError(
            f"⛔ {missing} are no longer defect verdicts in stage4_driver.py. "
            f"This scorer's copy has drifted from the driver's and every "
            f"count below would be wrong.")


# ==========================================================================
#  ⭐ THE NORMALISATION. Applied to every judge identically.
# ==========================================================================

_FENCE = re.compile(r"^\s*```(?:json|JSON)?\s*\n(.*?)\n?\s*```\s*$", re.S)


def parse_reply(text):
    """`(judgements, notes)` — or `(None, notes)` if it truly cannot be read.

    Each tolerance below is here because a REAL model reply needed it, and
    each one is RECORDED in `notes` so a reader can see how much of a judge's
    score rests on the scorer's charity rather than on the judge.

      fence     ```json … ``` — all 20 claude-sonnet-4-5 replies in the
                parity run. `seats.judge` refuses these outright.
      object    `{"judgements": [...]}` vs a bare list. Both are seen.
      trailing  prose after the JSON, which some models append.

    ⛔ NOT tolerated: inventing a judgement, dropping one, or retrying. A
    reply that cannot be parsed is a REFUSAL and is reported as one. A
    refusal rate tuned to zero by retrying is not a measurement.
    """
    notes = []
    if not text or not text.strip():
        return None, ["empty reply"]
    s = text.strip()
    m = _FENCE.match(s)
    if m:
        notes.append("fence-stripped")
        s = m.group(1).strip()
    obj = None
    try:
        obj = json.loads(s)
    except Exception:                                        # noqa: BLE001
        # The JSON is there but something surrounds it. ⛔ THE LIST BRACKETS
        # ARE TRIED FIRST AND THAT ORDER IS LOAD-BEARING: a judgement list's
        # FIRST `{` and LAST `}` also parse — as a single judgement object —
        # so brace-first silently turned a valid reply into "not a list" and
        # scored an answering seat as REFUSED. Caught by `--selftest`.
        cands = []
        for opener, closer in (("[", "]"), ("{", "}")):
            i, j = s.find(opener), s.rfind(closer)
            if i >= 0 and j > i:
                try:
                    cands.append(json.loads(s[i:j + 1]))
                except Exception:                            # noqa: BLE001
                    continue
        for cand in cands:
            if isinstance(cand, list) or (isinstance(cand, dict)
                                          and any(isinstance(cand.get(k), list)
                                                  for k in ("judgements",
                                                            "judgments",
                                                            "items",
                                                            "results"))):
                obj = cand
                notes.append("trailing-text-trimmed")
                break
    if obj is None:
        return None, notes + ["unparseable"]
    if isinstance(obj, dict):
        for k in ("judgements", "judgments", "items", "results"):
            if isinstance(obj.get(k), list):
                if k != "judgements":
                    notes.append(f"envelope-key:{k}")
                obj = obj[k]
                break
    if not isinstance(obj, list):
        return None, notes + ["not a list of judgements"]
    return obj, notes


def _norm_item(s):
    """Item matching, in the same three steps `seats._reply_item` uses plus
    the one it does not.

    ⛔ THE ONE IT DOES NOT is the `C1 ` claim label. Dropping it caused ALL 57
    seat-4d refusals in the first stage-4 baseline (17.6% of every call made),
    and the replies were otherwise competent — right count, right order, real
    reasons. Tolerated here, and every use is counted, because a 4d column
    that is 70% empty cannot support a per-class profile of dropped content —
    which is the one class 4d exists to catch.
    """
    s = " ".join((s or "").split())
    m = re.match(r"^C\d+\s*:?\s+(.*)$", s)
    return (m.group(1).strip() if m else s), bool(m)


# ==========================================================================
#  loading a judge's stored run
# ==========================================================================

def load_arm(arm_dir):
    """`{clause: {seat: {...}}}` rebuilt from the RAW replies, plus the plan's
    denominators. Falls back to nothing rather than to a guess."""
    plan_path = os.path.join(arm_dir, "plan.json")
    denom = {}
    if os.path.isfile(plan_path):
        plan = json.load(open(plan_path, encoding="utf-8"))
        for p in plan.get("planned", []):
            denom[p["clause_id"]] = p.get("ids", {})
    raw_dir = os.path.join(arm_dir, "raw")
    out = {}
    if os.path.isdir(raw_dir):
        for f in sorted(os.listdir(raw_dir)):
            m = re.match(r"^(.*)\.(4[abcd])\.json$", f)
            if not m:
                continue
            cid, seat = m.group(1), m.group(2)
            blob = json.load(open(os.path.join(raw_dir, f), encoding="utf-8"))
            js, notes = parse_reply(blob.get("text"))
            out.setdefault(cid, {})[seat] = {
                "judgements": js, "notes": notes,
                "denominator": (denom.get(cid) or {}).get(seat)}
    return out, denom


def verdict_at(seat_blob, wanted):
    """The judgement(s) the judge returned at one site, or why there are none.

    `wanted` is a list of item strings. Matching is exact first, then
    whitespace-normalised, then claim-label-tolerant — and which one fired is
    recorded, never silently absorbed.
    """
    if seat_blob is None:
        return {"status": "not-run"}
    js = seat_blob["judgements"]
    if js is None:
        return {"status": "seat-refused", "why": "; ".join(seat_blob["notes"])}
    want = {}
    for w in wanted:
        n, _ = _norm_item(w)
        want[n] = w
    hits, relabelled = [], False
    for j in js:
        if not isinstance(j, dict):
            continue
        n, was = _norm_item(str(j.get("item", "")))
        if n in want:
            hits.append(j)
            relabelled = relabelled or was
    if not hits:
        denom = seat_blob.get("denominator")
        in_denom = denom is not None and any(
            _norm_item(d)[0] in want for d in denom)
        return {"status": "seat-refused" if in_denom else "site-absent",
                "why": ("the site was in the seat's denominator but the reply "
                        "carries no judgement for it"
                        if in_denom else
                        "the site is not in this seat's denominator")}
    vs = [h.get("verdict") for h in hits]
    if any(v in DEFECT_VERDICTS for v in vs):
        h = next(h for h in hits if h.get("verdict") in DEFECT_VERDICTS)
        st = "detected"
    elif any(v == "unclear" for v in vs):
        h = next(h for h in hits if h.get("verdict") == "unclear")
        st = "unclear-at-site"
    elif any(v in PASS_VERDICTS for v in vs):
        h = next(h for h in hits if h.get("verdict") in PASS_VERDICTS)
        st = "missed"
    else:
        return {"status": "seat-refused",
                "why": f"unrecognised verdict(s) {vs}"}
    return {"status": st, "verdict": h.get("verdict"),
            "reason": str(h.get("reason", ""))[:500],
            "claim_label_tolerated": relabelled}


def clause_defects(seat_blob):
    """Every defect verdict in one seat's reply, for the LOOSE measure and for
    the control false-positive count. Returns None if the seat did not
    adjudicate — which is NOT zero defects."""
    if seat_blob is None or seat_blob["judgements"] is None:
        return None
    n_def = sum(1 for j in seat_blob["judgements"]
                if isinstance(j, dict)
                and j.get("verdict") in DEFECT_VERDICTS)
    return n_def, len([j for j in seat_blob["judgements"]
                       if isinstance(j, dict)])


# ==========================================================================
#  scoring
# ==========================================================================

def score(key, root):
    arms = {}
    for arm in sorted(key["arms"]):
        arms[arm], _ = load_arm(os.path.join(root, arm))
    out = {"root": root, "mutants": [], "controls": [], "borrows": [],
           "normalisation": {}}
    notes_tally = {}
    for arm in arms.values():
        for seats_ in arm.values():
            for blob in seats_.values():
                for n in blob["notes"]:
                    notes_tally[n] = notes_tally.get(n, 0) + 1
    out["normalisation"] = notes_tally

    for item in key["items"]:
        got = arms.get(f"arm{item['arm']}", {}).get(item["clause_id"])
        if item["kind"] == "mutant":
            rows = {}
            for seat in SEATS:
                wanted = ([item["claim"]] if seat == "4d" and item.get("claim")
                          else ([] if seat == "4d" else item.get("site") or []))
                if not wanted:
                    rows[seat] = {"status": "site-absent",
                                  "why": "no site for this seat"}
                    continue
                rows[seat] = verdict_at((got or {}).get(seat), wanted)
            out["mutants"].append({
                **{k: item[k] for k in ("item_id", "clause_id", "arm",
                                        "class", "subtype", "arguable",
                                        "site", "claim",
                                        "mechanical_detector")},
                "seats": rows,
                "loose": _loose(got)})
        elif item["kind"] == "borrow-control":
            rows = {seat: verdict_at((got or {}).get(seat), item["site"])
                    for seat in SEATS}
            out["borrows"].append({
                **{k: item[k] for k in ("item_id", "clause_id", "class",
                                        "site")},
                "seats": rows})
        else:
            fp, judged, refused = {}, {}, []
            for seat in SEATS:
                cd = clause_defects((got or {}).get(seat))
                if cd is None:
                    fp[seat], judged[seat] = None, None
                    refused.append(seat)
                else:
                    fp[seat], judged[seat] = cd
            out["controls"].append({
                "item_id": item["item_id"], "clause_id": item["clause_id"],
                "false_positives": fp, "judged": judged,
                "refused_seats": refused, "loose": _loose(got)})
    return out


def _loose(got):
    """Any defect verdict anywhere in the clause, 4a excluded. `None` when no
    non-advisory seat adjudicated — absence of a flag from a seat that never
    spoke is not a clean bill."""
    if not got:
        return None
    seen = False
    for seat, blob in got.items():
        if seat == ADVISORY:
            continue
        cd = clause_defects(blob)
        if cd is None:
            continue
        seen = True
        if cd[0]:
            return True
    return False if seen else None


# ==========================================================================
#  rendering
# ==========================================================================

def _cell():
    return {s: 0 for s in STATUSES}


def render_judge(name, sc):
    L = [f"╔══ JUDGE: {name}   ({sc['root']})"]
    if sc["normalisation"]:
        L.append("║  normalisation applied (identical for every judge; a "
                 "no-op on a judge")
        L.append("║  that already speaks the contract):")
        for k, v in sorted(sc["normalisation"].items()):
            L.append(f"║     {k:26} {v}")
    else:
        L.append("║  normalisation applied: none")
    L.append("╚" + "═" * 60)
    L.append("")

    muts = sc["mutants"]
    solid = [m for m in muts if not m["arguable"]]
    arg = [m for m in muts if m["arguable"]]

    L.append("PER-CLASS DETECTION PROFILE — STRICT (defect verdict AT the "
             "planted site)")
    hdr = (f"  {'class':28} {'seat':4} {'det':>4} {'miss':>5} {'uncl':>5} "
           f"{'refu':>5} {'n/a':>4}  {'det/answered':>13}")
    L.append(hdr)
    L.append("  " + "-" * (len(hdr) - 2))
    by = {}
    for m in solid:
        for seat in SEATS:
            by.setdefault((m["class"], seat), _cell())[
                m["seats"][seat]["status"]] += 1
    for cls, seat in sorted(by):
        c = by[(cls, seat)]
        ans = c["detected"] + c["missed"] + c["unclear-at-site"]
        rate = f"{c['detected']}/{ans}" if ans else "— (0 answered)"
        L.append(f"  {cls:28} {seat:4} {c['detected']:4} {c['missed']:5} "
                 f"{c['unclear-at-site']:5} {c['seat-refused']:5} "
                 f"{c['site-absent'] + c['not-run']:4}  {rate:>13}"
                 + ("  (advisory)" if seat == ADVISORY else ""))
    L.append("")
    L.append(f"  denominator: {len(solid)} unarguable mutants; {len(arg)} "
             f"ARGUABLE excluded from every cell above.")
    L.append("")

    L.append("ANY-SEAT RECALL — the item is detected if ANY non-advisory seat "
             "flags its site")
    byc = {}
    for m in solid:
        st = [m["seats"][s]["status"] for s in SEATS if s != ADVISORY]
        d = byc.setdefault(m["class"], [0, 0, 0])
        if "detected" in st:
            d[0] += 1
        elif "missed" in st or "unclear-at-site" in st:
            d[1] += 1
        else:
            d[2] += 1
    for cls in sorted(byc):
        d, miss, silent = byc[cls]
        L.append(f"  {cls:28} {d}/{d + miss} detected"
                 + (f"   ({silent} item(s) NO SEAT ANSWERED — not a miss)"
                    if silent else ""))
    L.append("")

    if arg:
        L.append("ARGUABLE ITEMS — reported, never pooled")
        for m in arg:
            st = {s: m["seats"][s]["status"] for s in SEATS}
            L.append(f"  {m['item_id']}  {m['class']:26} "
                     f"{m['clause_id']:20} {st}")
        L.append("")

    # ---- borrowed-name controls ------------------------------------------
    L.append("⭐ BORROWED-NAME CONTROLS — unmutated, correct by the "
             "pipeline's own instruction.")
    L.append("   A defect verdict here is a FALSE POSITIVE. 4c is never shown "
             "`PROVIDES`,")
    L.append("   so this stratum measures a KNOWN design blindness rather "
             "than arguing about it.")
    bb = {}
    for b in sc["borrows"]:
        for seat in SEATS:
            bb.setdefault((b["class"], seat), _cell())[
                b["seats"][seat]["status"]] += 1
    L.append(f"  {'stratum':20} {'seat':4} {'FLAGGED':>8} {'clean':>6} "
             f"{'uncl':>5} {'refu':>5} {'n/a':>4}  {'FP rate':>9}")
    for cls, seat in sorted(bb):
        c = bb[(cls, seat)]
        ans = c["detected"] + c["missed"] + c["unclear-at-site"]
        rate = f"{c['detected']}/{ans}" if ans else "—"
        L.append(f"  {cls:20} {seat:4} {c['detected']:8} {c['missed']:6} "
                 f"{c['unclear-at-site']:5} {c['seat-refused']:5} "
                 f"{c['site-absent'] + c['not-run']:4}  {rate:>9}"
                 + ("  (advisory)" if seat == ADVISORY else ""))
    L.append("")

    # ---- whole-clause controls -------------------------------------------
    L.append("CONTROLS — per-seat false positives on the 11 modules a reader "
             "called FAITHFUL")
    L.append(f"  {'clause':22} {'4a':>9} {'4b':>9} {'4c':>9} {'4d':>9}")
    tot = {s: [0, 0] for s in SEATS}
    for c in sc["controls"]:
        cells = []
        for s in SEATS:
            f, j = c["false_positives"][s], c["judged"][s]
            if f is None:
                cells.append("refused".rjust(9))
            else:
                tot[s][0] += f
                tot[s][1] += j
                cells.append(f"{f}/{j}".rjust(9))
        L.append(f"  {c['clause_id']:22} " + " ".join(cells))
    L.append(f"  {'TOTAL':22} " + " ".join(
        f"{tot[s][0]}/{tot[s][1]}".rjust(9) for s in SEATS))
    L.append("")

    fm = sum(1 for m in muts if m["loose"])
    nm = sum(1 for m in muts if m["loose"] is not None)
    fc = sum(1 for c in sc["controls"] if c["loose"])
    nc = sum(1 for c in sc["controls"] if c["loose"] is not None)
    L.append("⚠️ LOOSE — any defect verdict ANYWHERE in the clause. The shape "
             "the `66 of 81`")
    L.append("   headline counts. The CONTROL row is what makes it readable "
             "at all.")
    L.append(f"   mutants  flagged : {fm}/{nm}")
    L.append(f"   CONTROLS flagged : {fc}/{nc}")
    if nm and nc:
        L.append(f"   discrimination   : {fm / nm - fc / nc:+.3f}   "
                 f"(0.000 = the loose measure separates nothing)")
    return "\n".join(L)


def render_compare(scores):
    """Per-judge recall and precision, per class, side by side."""
    L = ["", "=" * 72,
         "JUDGE COMPARISON — VALIDITY, not agreement",
         "=" * 72, "",
         "  RECALL is any-seat, over unarguable mutants only.",
         "  PRECISION is 1 - (flagged borrow controls / answered borrow "
         "controls);",
         "  it is the number the borrowed-name stratum exists to produce.",
         ""]
    names = list(scores)
    classes = sorted({m["class"] for sc in scores.values()
                      for m in sc["mutants"] if not m["arguable"]})
    L.append(f"  {'class':28} " + " ".join(f"{n:>14}" for n in names))
    for cls in classes:
        cells = []
        for n in names:
            solid = [m for m in scores[n]["mutants"]
                     if not m["arguable"] and m["class"] == cls]
            d = sum(1 for m in solid if any(
                m["seats"][s]["status"] == "detected"
                for s in SEATS if s != ADVISORY))
            a = sum(1 for m in solid if any(
                m["seats"][s]["status"] in ("detected", "missed",
                                            "unclear-at-site")
                for s in SEATS if s != ADVISORY))
            cells.append((f"{d}/{a}" if a else "—").rjust(14))
        L.append(f"  {cls:28} " + " ".join(cells))
    L.append("")
    for label, key_ in (("borrow FP (all)", None),
                        ("borrow FP (resolved only)", "borrow-resolved")):
        cells = []
        for n in names:
            bs = [b for b in scores[n]["borrows"]
                  if key_ is None or b["class"] == key_]
            f = sum(1 for b in bs if any(
                b["seats"][s]["status"] == "detected"
                for s in SEATS if s != ADVISORY))
            a = sum(1 for b in bs if any(
                b["seats"][s]["status"] in ("detected", "missed",
                                            "unclear-at-site")
                for s in SEATS if s != ADVISORY))
            cells.append((f"{f}/{a}" if a else "—").rjust(14))
        L.append(f"  {label:28} " + " ".join(cells))
    cells = []
    for n in names:
        tot = [0, 0]
        for c in scores[n]["controls"]:
            for s in SEATS:
                if s == ADVISORY or c["false_positives"][s] is None:
                    continue
                tot[0] += c["false_positives"][s]
                tot[1] += c["judged"][s]
        cells.append((f"{tot[0]}/{tot[1]}" if tot[1] else "—").rjust(14))
    L.append(f"  {'control FP (all items)':28} " + " ".join(cells))
    cells = []
    for n in names:
        r = scores[n]["normalisation"]
        cells.append(f"{sum(r.values())}".rjust(14))
    L.append(f"  {'normalisations applied':28} " + " ".join(cells))
    L.append("")
    L.append("  ⚠️ A judge with high recall AND high borrow-FP has not found "
             "defects; it")
    L.append("     has a prior. Read the two rows together or neither.")
    return "\n".join(L)


# ==========================================================================
#  ⛔ THE SELF-TEST. The instrument proves it can tell the statuses APART
#     before it is allowed to report any of them.
# ==========================================================================

_CASES = [
    ("plain list, defect at site", "detected",
     '[{"item":"asserts[0]","verdict":"unlicensed","reason":"r"}]', []),
    ("plain list, pass at site", "missed",
     '[{"item":"asserts[0]","verdict":"licensed","reason":"r"}]', []),
    ("unclear at site", "unclear-at-site",
     '[{"item":"asserts[0]","verdict":"unclear","reason":"r"}]', []),
    # ⭐ the claude-sonnet-4-5 shape. `seats.judge` refuses this outright.
    ("```json fenced", "detected",
     '```json\n[{"item":"asserts[0]","verdict":"unfaithful","reason":"r"}]\n```',
     ["fence-stripped"]),
    ("envelope object", "detected",
     '{"judgements":[{"item":"asserts[0]","verdict":"unfaithful",'
     '"reason":"r"}]}', []),
    ("prose after the JSON", "missed",
     '[{"item":"asserts[0]","verdict":"faithful","reason":"r"}]\nHope this '
     'helps!', ["trailing-text-trimmed"]),
    ("empty reply is a REFUSAL, not a pass", "seat-refused", "", ["empty reply"]),
    ("unparseable is a REFUSAL, not a pass", "seat-refused",
     "I cannot judge this.", ["unparseable"]),
    ("answered, but not about this site", "seat-refused",
     '[{"item":"concepts[0]","verdict":"licensed","reason":"r"}]', []),
]


def selftest():
    """⛔ `mutate_seats.py` once reported `0 survivors` against a RED suite
    because it could not tell *killed* from *never ran*. These cases exist so
    this scorer cannot make the same mistake unnoticed: a refusal, an empty
    reply and an unparseable reply must each land on `seat-refused` and NEVER
    on `missed` or `detected`."""
    bad = []
    for name, want, text, want_notes in _CASES:
        js, notes = parse_reply(text)
        blob = {"judgements": js, "notes": notes,
                "denominator": ["asserts[0]", "concepts[0]"]}
        got = verdict_at(blob, ["asserts[0]"])["status"]
        ok = got == want and all(n in notes for n in want_notes)
        bad.append((ok, name, want, got, notes))
    # a site genuinely outside the denominator is `site-absent`, not a refusal
    js, notes = parse_reply(
        '[{"item":"concepts[0]","verdict":"licensed","reason":"r"}]')
    got = verdict_at({"judgements": js, "notes": notes,
                      "denominator": ["concepts[0]"]}, ["asserts[9]"])["status"]
    bad.append((got == "site-absent", "site outside the denominator",
                "site-absent", got, []))
    # no stored reply at all is `not-run`, which is not a zero
    got = verdict_at(None, ["asserts[0]"])["status"]
    bad.append((got == "not-run", "no stored reply", "not-run", got, []))

    for ok, name, want, got, notes in bad:
        print(f"  {'ok ' if ok else '⛔ '} {name:42} want={want:16} "
              f"got={got:16} {notes}")
    fails = [b for b in bad if not b[0]]
    print(f"\n  {len(bad) - len(fails)}/{len(bad)} cases pass")
    return 1 if fails else 0


def verify_sites(key, root):
    """⛔ RUN THIS BEFORE SPENDING. A planted site that is in NO seat's
    denominator is never shown to any judge, so every judge "misses" it and
    the set reports a false negative forever. Reads the `plan.json` a `--dry`
    run writes, so it costs nothing and needs no reply."""
    bad, rows = [], []
    for arm in sorted(key["arms"]):
        p = os.path.join(root, arm, "plan.json")
        if not os.path.isfile(p):
            bad.append((arm, "no plan.json — run the driver with --dry first"))
            continue
        plan = {x["clause_id"]: x.get("ids", {})
                for x in json.load(open(p, encoding="utf-8"))["planned"]}
        for it in key["items"]:
            if f"arm{it['arm']}" != arm or it["kind"] == "control":
                continue
            ids = plan.get(it["clause_id"])
            if ids is None:
                bad.append((it["item_id"], "clause is not in the plan"))
                continue
            targets = it["site"] or ([it["claim"]] if it.get("claim") else [])
            seats = sorted(s for s, v in ids.items()
                           if any(t in v for t in targets))
            rows.append((it["item_id"], it["class"], targets[:1], seats))
            if not seats:
                bad.append((it["item_id"],
                            f"site {targets} is in NO seat's denominator"))
    for iid, cls, tgt, seats in rows:
        print(f"  {iid:44} {cls:26} {str(tgt[0])[:38]:40} {seats}")
    print()
    if bad:
        for b in bad:
            print(f"  ⛔ {b[0]}: {b[1]}")
        print(f"\n  {len(bad)} unscoreable item(s). REFUSING — do not spend "
              f"against this set until they are fixed.")
        return 1
    print(f"  ok — all {len(rows)} planted sites reach at least one seat's "
          f"denominator.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", action="append", default=[], metavar="NAME=DIR",
                    help="a judge's output root (holding arm0/ arm1/ …). "
                         "Repeat for a comparison.")
    ap.add_argument("--key", default=KEY)
    ap.add_argument("--json", default=None)
    ap.add_argument("--selftest", action="store_true",
                    help="prove the six statuses are distinguishable. Free.")
    ap.add_argument("--verify-sites", metavar="DIR", default=None,
                    help="⛔ run before spending: check every planted site is "
                         "in a seat's denominator, off a --dry run's "
                         "plan.json. Free.")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.verify_sites:
        key = json.load(open(a.key, encoding="utf-8"))
        root = (a.verify_sites if os.path.isabs(a.verify_sites)
                else os.path.join(HERE, a.verify_sites))
        return verify_sites(key, root)
    if not a.judge:
        ap.error("pass at least one --judge NAME=DIR (or --selftest)")
    _check_contract()
    key = json.load(open(a.key, encoding="utf-8"))
    scores = {}
    for spec in a.judge:
        name, _, path = spec.partition("=")
        if not path:
            ap.error(f"--judge {spec!r} is not NAME=DIR")
        root = path if os.path.isabs(path) else os.path.join(HERE, path)
        if not os.path.isdir(root):
            raise ScoreError(
                f"⛔ {root} does not exist. A judge with no stored run scores "
                f"`not-run` on every item, which is NOT a zero — refusing "
                f"rather than printing a table of zeros.")
        scores[name] = score(key, root)
    for name, sc in scores.items():
        print(render_judge(name, sc))
        print()
    if len(scores) > 1:
        print(render_compare(scores))
    if a.json:
        json.dump(scores, open(a.json, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print(f"\n  rows written to {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
