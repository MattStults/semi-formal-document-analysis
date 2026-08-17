#!/usr/bin/env python3
"""THREE-WAY RELEVANCE REPORT — Matt's design (2026-08-17), one report per
panel behavior set: rows are (behavior, spec node) pairs where ANY of the three
instruments claimed relevance; columns are the TOOL (seat verdict + engaging
atom + grounds), the FRONTIER PANEL (consensus tier / any tier / cold), and the
FABLE ADJUDICATOR (blind ruling + quoted document grounds). Below the table,
every tool-vs-Fable disagreement carries a fix-locus tag and a one-line
difference note assembled from the two sets of grounds.

Fix-locus vocabulary (the column that answers "what do we do about it"):
  panel-strict      panel cold, seat engaged, Fable relevant  -> no fix; evidence FOR the tool
  scope-conflation  seat engaged on the wrong party/scope, Fable not_relevant -> behavior checklist + seat brief
  structural-node   seat engaged on a structure/glossary/commitment node, Fable not_relevant -> seat brief
  seat-miss         seat judged and declined, Fable relevant -> seat brief / atom reach
  retrieval-miss    never retrieved by ranking; probe verdict decides -> retrieval infrastructure
  panel-broad       panel hot, Fable not_relevant -> panel error; no fix
  unadjudicated     no Fable ruling yet

Scope: RELEVANCE matching only. Translation fidelity is measured in
semantic_audit.json; contradiction detection awaits the D4 concrete instances.
The report links, never blends.
"""
import json, os, glob, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "panel_run1")
GRAPH_V2 = os.path.dirname(HERE)


def load_match():
    parts = sorted(glob.glob(os.path.join(OUT, "match_partial_*.json")))
    m = None
    for p in parts:
        d = json.load(open(p))
        m = d if m is None else ({**m, "behaviors": {**m["behaviors"], **d["behaviors"]}})
    return m


def main():
    match = load_match()
    ag = json.load(open(os.path.join(OUT, "agreement.json")))
    probe_p = os.path.join(OUT, "probe.json")
    probe = json.load(open(probe_p))["behaviors"] if os.path.exists(probe_p) else {}
    fable = {}
    for p in glob.glob(os.path.join(OUT, "adjudication_run2_*.json")):
        d = json.load(open(p)); fable[d["behavior"]] = d["rulings"]
    grounds_f = {}
    # keep the adjudicators' grounds if present in adjudication.json shape (run1) — run2 stored verdict-only; note it
    corpus = {c["id"]: c for c in json.load(open(os.path.join(GRAPH_V2, "node_corpus_all.json")))["clauses"]}

    def establishes(cid):
        q = corpus.get(cid, {}).get("quote", "")
        m = re.search(r"ESTABLISHES \(the one claim this module must express\):\s*(.*?)\n\s*\n", q, re.S)
        return (m.group(1).strip() if m else "")[:140]

    lines = ["# Three-way relevance report — frontier panel behaviors, full corpus (run 2)", "",
             "Rows: (behavior, spec node) where the TOOL engaged, the PANEL cited (consensus>=5), or FABLE ruled relevant. "
             "Tool = embed-rank + blind small-model seat over node prose (frozen frontier atoms, TOP_K 12). "
             "Panel = the frontier judges' summed CITATION score over passages: `cited>=5` (consensus tier), `cited 2-4` (some judges), `uncited` (below 2 or absent from the export — NOT an affirmative irrelevance verdict). Fable = blind adjudicator, document text only. Tool verdicts marked `*` came from the probe (label-selected node, blind per-pair judgment).",
             "",
             "**Scope: relevance matching only.** Translation fidelity: `../semantic_audit.json` (all six bulk cohorts sealed). "
             "Contradiction detection: awaits `CONCRETE_INSTANCES.md` adjudication. Fix-locus tags are the coordinator's, from the grounds; overrule freely.",
             ""]
    totals = Counter()
    for slug, b in match["behaviors"].items():
        t = ag["behaviors"][slug]["consensus_ge5"]
        t2 = ag["behaviors"][slug]["any_ge2"]
        panel_hot = set(t["agree_relevant"]) | set(t["panel_hot_seat_declined"]) | set(t["panel_hot_never_retrieved"])
        panel_warm = (set(t2["agree_relevant"]) | set(t2["panel_hot_seat_declined"]) | set(t2["panel_hot_never_retrieved"])) - panel_hot
        seat = {}     # node -> (verdict, atom, grounds)
        for row in b["atoms"]:
            for v in row["verdicts"]:
                cur = seat.get(v["node"])
                if v["verdict"] == "engaged" and (cur is None or cur[0] != "engaged"):
                    seat[v["node"]] = ("engaged", row["atom"], v["grounds"])
                elif cur is None:
                    seat[v["node"]] = ("declined", row["atom"], v["grounds"])
        for v in probe.get(slug, []):
            cur = seat.get(v["node"])
            if v["verdict"] == "engaged" and (cur is None or cur[0] != "engaged"):
                seat[v["node"]] = ("engaged*", v["atom"], v["grounds"])
            elif cur is None:
                seat[v["node"]] = ("declined*", v["atom"], v["grounds"])
        fr = fable.get(slug, {})
        rows = sorted(set(seat) | panel_hot | set(fr))
        rows = [n for n in rows if seat.get(n, ("",))[0].startswith("engaged") or n in panel_hot or fr.get(n) == "relevant"]
        lines += [f"## {slug}", "", f"| node | establishes | tool | panel | fable | tag |", "|---|---|---|---|---|---|"]
        tags = Counter(); disagreements = []
        for n in rows:
            sv = seat.get(n, ("not-retrieved", "", ""))
            tool = sv[0]
            panel = "cited>=5" if n in panel_hot else ("cited 2-4" if n in panel_warm else "uncited")
            fv = fr.get(n, "—")
            # tag
            if fv == "—":
                tag = "unadjudicated"
            elif tool.startswith("engaged") and fv == "relevant" and panel != "cited>=5": tag = "panel-strict"
            elif tool.startswith("engaged") and fv == "not_relevant":
                tag = "structural-node" if re.search(r"glossary|definition|commit|structure|section", (establishes(n)+sv[2]).lower()) else "scope-conflation"
            elif tool.startswith("declined") and fv == "relevant": tag = "seat-miss"
            elif tool == "not-retrieved" and panel == "cited>=5": tag = "retrieval-miss"
            elif panel == "cited>=5" and fv == "not_relevant": tag = "panel-broad"
            elif tool.startswith("engaged") and fv == "relevant" and panel == "cited>=5": tag = "agree"
            else: tag = "other"
            tags[tag] += 1; totals[tag] += 1
            lines.append(f"| `{n}` | {establishes(n)} | {tool}{(' ('+sv[1]+')') if sv[1] else ''} | {panel} | {fv} | {tag} |")
            if tag not in ("agree", "unadjudicated", "panel-strict") and (fv != "—"):
                disagreements.append((n, tag, sv, fv))
        lines += ["", "**Tag counts:** " + ", ".join(f"{k} {v}" for k, v in sorted(tags.items())), ""]
        if disagreements:
            lines += ["### Tool-vs-Fable disagreements, with fix locus", ""]
            for n, tag, sv, fv in disagreements:
                lines.append(f"* `{n}` — **{tag}** — tool {sv[0]} via `{sv[1]}` (\"{sv[2][:120]}…\"); Fable: {fv}. "
                             + {"scope-conflation": "Fix at the behavior checklist + seat brief: the party/scope qualifier is not being tested.",
                                "structural-node": "Fix at the seat brief: structure/glossary/commitment nodes establish no norm to bear on the behavior.",
                                "seat-miss": "Fix at the seat brief / atom reach: the node was retrieved and judged not_engaged against a Fable-relevant clause.",
                                "retrieval-miss": "Fix at retrieval infrastructure: the node never reached the seat.",
                                "panel-broad": "No tool fix: the panel cited a node a blind reader rules irrelevant."}.get(tag, ""))
            lines.append("")
    lines += ["## Totals across behaviors", "", ", ".join(f"{k} {v}" for k, v in sorted(totals.items())), "",
              "## Honesty notes", "",
              "* Fable adjudicators are the truth TIER, not truth: no cell carries Matt's countersignature yet (spot-check column to be added on his pass).",
              "* Inter-adjudicator breadth differed: the helpfulness adjudicator read persona/character nodes as relevant more inclusively than the harm-avoidance adjudicator did for its behavior. Not smoothed.",
              "* Retrieval-miss rows carry the probe's verdict when present (`engaged*`/`declined*`); unprobed rows say not-retrieved.",
              "* Agreed-irrelevant sample (over-firing control) not yet drawn; add before any headline number is quoted."]
    open(os.path.join(OUT, "THREEWAY_REPORT.md"), "w").write("\n".join(lines) + "\n")
    print("wrote panel_run1/THREEWAY_REPORT.md;", dict(totals))


if __name__ == "__main__":
    main()
