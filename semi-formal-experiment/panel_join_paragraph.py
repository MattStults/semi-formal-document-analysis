"""Paragraph-level join: pipeline-flagged constitution PARAGRAPHS vs the
frontier LLM panel's per-paragraph relevance scores.

Made possible by the locator/4 back-fill in rules.lp (see backfill_locators.py):
each norm now carries a verified ¶-level clause id, so

    behavior -> atoms_used -> norms -> PARAGRAPHS

can be compared against the panel's paragraph-level judgments.

Deliberately NOT reported: naive recall over all 616 paragraphs. Our 16 rules
trace to 14 distinct paragraphs, so any such number is dominated by text we
never attempted to encode. Instead:

  (a) precision-direction  : for each paragraph WE flag, what did the panel say?
  (b) restricted recall    : within the paragraphs our rulebase encodes, which
                             did the panel rate high-consensus and we missed?
  (c) small-model vs hand-authored delta on (a) and (b).

Usage:
  .venv/bin/python panel_join_paragraph.py results_smallmodel.json results_handauthored.json
"""
from __future__ import annotations

import json
import os
import re
import sys

from compare_to_panel import (HIGH_CONSENSUS, PANEL, conflict_pairs,
                              parse_rules_lp, relevant_norms)

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.lp")
CLAUSES = os.path.join(HERE, "constitution_clauses.json")


def parse_locators(path=RULES):
    """norm id -> (locator, clause id, clause kind) from locator/4 facts."""
    return {m[0]: (m[1], m[2], m[3]) for m in re.findall(
        r'^locator\((\w+),\s*"([^"]*)",\s*"(\w+)",\s*"(\w+)"\)\.', open(path).read(), re.M)}


def load_clauses():
    return {c["id"]: c for c in json.load(open(CLAUSES))["clauses"]}


def panel_index(beh, clauses):
    """clause id -> panel passage, joining panel passages to our clause ids.

    The panel's segmentation is NOT identical to constitution_clauses.json
    (paragraph numbering diverges inside some sections), so we join on the
    locator string first and fall back to unique verbatim quote containment.
    """
    passages = beh["coverage"]["anthropic"]["passages"]
    by_loc = {p["locator"]: p for p in passages}
    out, how = {}, {}
    for cid, c in clauses.items():
        if c["locator"] in by_loc:
            out[cid], how[cid] = by_loc[c["locator"]], "locator"
            continue
        probe = c["quote"][:80]
        hits = [p for p in passages if probe and probe in p["quote"]]
        if len(hits) == 1:
            out[cid], how[cid] = hits[0], "quote"
    return out, how


def flagged_paragraphs(atoms, norms, incompat, locators):
    """behavior atoms -> {clause id -> [norm ids]} via the norm layer."""
    _, closure = relevant_norms(atoms, norms, incompat)
    paras = {}
    for n in sorted(closure):
        if n in locators:
            paras.setdefault(locators[n][1], []).append(n)
    return closure, paras


def short(q, n=110):
    q = " ".join(q.split())
    return q if len(q) <= n else q[: n - 1] + "…"


def analyse(tag, res, norms, incompat, locators, pidx, clauses, encoded):
    closure, paras = flagged_paragraphs(res["atoms_used"], norms, incompat, locators)
    agree, disagree = [], []
    for cid, ns in sorted(paras.items()):
        p = pidx.get(cid)
        score = p["score"] if p else None
        (agree if (score is not None and score >= HIGH_CONSENSUS) else disagree).append(
            (cid, ns, score, clauses[cid]))
    # (b) restricted recall: encoded paragraphs the panel rated high, we missed
    missed = []
    for cid in sorted(encoded):
        p = pidx.get(cid)
        if p and p["score"] >= HIGH_CONSENSUS and cid not in paras:
            missed.append((cid, p["score"], clauses[cid]))
    return {"tag": tag, "status": res["status"], "norms": closure, "paras": paras,
            "agree": agree, "disagree": disagree, "missed": missed}


def report(a):
    print(f"\n  -- {a['tag']} (definition status: {a['status']}) --")
    print(f"     norms flagged: {len(a['norms'])}  ->  paragraphs flagged: {len(a['paras'])}")
    print(f"     (a) precision-direction: {len(a['agree'])} agree with panel "
          f"high-consensus, {len(a['disagree'])} not")
    for cid, ns, score, c in a["agree"]:
        print(f"         AGREE   {cid} panel={score}  {c['locator'].split(' > ',1)[1]}")
        print(f"                 via {','.join(ns)}")
    for cid, ns, score, c in a["disagree"]:
        s = "not listed by panel" if score is None else f"panel={score}"
        print(f"         WE-FLAG/PANEL-DOESN'T  {cid} ({s})  {c['locator'].split(' > ',1)[1]}")
        print(f"                 via {','.join(ns)}")
        print(f"                 \"{short(c['quote'])}\"")
    print(f"     (b) restricted recall misses (encoded ¶, panel>=5, we didn't flag): "
          f"{len(a['missed'])}")
    for cid, score, c in a["missed"]:
        print(f"         MISS    {cid} panel={score}  {c['locator'].split(' > ',1)[1]}")
        print(f"                 \"{short(c['quote'])}\"")


def main():
    small = json.load(open(os.path.join(HERE, sys.argv[1])))
    hand = json.load(open(os.path.join(HERE, sys.argv[2])))
    panel = {b["slug"]: b for b in json.load(open(PANEL))["behaviours"]}
    norms = parse_rules_lp(RULES)
    incompat = conflict_pairs(RULES)
    locators = parse_locators()
    clauses = load_clauses()

    encoded = sorted({v[1] for v in locators.values()})
    print("PARAGRAPH-LEVEL JOIN: rulebase ¶s vs LLM-panel ¶ relevance judgments")
    print("=" * 78)
    print(f"norms with a verified ¶ locator: {len(locators)}/{len(norms)+1}  "
          f"-> {len(encoded)} distinct paragraphs of {len(clauses)} in the document "
          f"({100*len(encoded)/len(clauses):.1f}%)")
    print(f"encoded paragraph universe: {', '.join(encoded)}")
    print("\nCAVEAT ON DIRECTION: the panel is known to OVERSTATE relevance (it marks")
    print("a large share of the document relevant to every behaviour). So")
    print("  panel-flags / we-don't  = WEAK evidence against us (b, restricted recall);")
    print("  we-flag / panel-doesn't = the INTERESTING direction (a) — either a real")
    print("  relevance the panel overlooked, or an over-broad atom->norm closure.")

    norms_without = sorted(set(norms) - set(locators))
    if norms_without:
        print(f"\nnorms lacking a locator (excluded from the ¶ join): {norms_without}")

    summary = {}
    for name in sorted(panel):
        s = next((r for r in small["results"] if r["name"] == name), None)
        h = next((r for r in hand["results"] if r["name"] == name), None)
        if not (s and h):
            continue
        pidx, how = panel_index(panel[name], clauses)
        joined = sum(1 for cid in encoded if cid in pidx)
        hc_all = sum(1 for p in panel[name]["coverage"]["anthropic"]["passages"]
                     if p["score"] >= HIGH_CONSENSUS)
        print("\n" + "=" * 78)
        print(f"### {name}")
        print(f"    panel: {len(panel[name]['coverage']['anthropic']['passages'])} passages, "
              f"{hc_all} at high consensus (>={HIGH_CONSENSUS}); "
              f"{joined}/{len(encoded)} of our encoded ¶s appear in the panel list "
              f"({sum(1 for c in encoded if how.get(c)=='quote')} joined by quote, "
              f"segmentation differs)")
        a_s = analyse("small-model", s, norms, incompat, locators, pidx, clauses, encoded)
        a_h = analyse("hand-authored", h, norms, incompat, locators, pidx, clauses, encoded)
        report(a_s)
        report(a_h)
        ps, ph = set(a_s["paras"]), set(a_h["paras"])
        print(f"\n     (c) small vs hand: |small ¶|={len(ps)} |hand ¶|={len(ph)}  "
              f"hand-only={sorted(ph-ps)}  small-only={sorted(ps-ph)}")
        summary[name] = (a_s, a_h, ps, ph)

    print("\n" + "=" * 78)
    print("(c) AGGREGATE small-model vs hand-authored")
    for name, (a_s, a_h, ps, ph) in summary.items():
        print(f"  {name:34s} ¶ small={len(ps):2d} hand={len(ph):2d} | "
              f"agree small={len(a_s['agree'])} hand={len(a_h['agree'])} | "
              f"we-flag/panel-doesn't small={len(a_s['disagree'])} hand={len(a_h['disagree'])} | "
              f"restricted-recall misses small={len(a_s['missed'])} hand={len(a_h['missed'])}")


if __name__ == "__main__":
    main()
